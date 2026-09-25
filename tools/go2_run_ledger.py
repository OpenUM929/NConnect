"""Go2 회차 원장 — `workspace/_keep` 산출물만 읽어서 회차 기록을 복원한다.

이 모듈은 사람이 적은 숫자를 하나도 쓰지 않는다. 학습 로그·env.yaml·case summary만
읽는다. 그래서 원장과 산출물이 어긋날 수 없다. 어긋나면 그건 산출물이 바뀐 것이다.

세 가지를 산출물에서만 뽑는다.
  1. 학습:   시각(로그 내장) · reward 가중치(env.yaml) · 커리큘럼 곡선(로그)
  2. 평가:   **하나의 정본 registry로 다시 채점한** 70점 · case 수 · 계측 세대
  3. 동일성: 학습 지표 줄을 해시해서 같은 학습의 재탕을 찾아낸다

계측 세대(`instrument`)가 다른 두 회차의 70점은 비교할 수 없다. 낙상 검출이
09-01에는 아예 없었고 09-03에 생겼기 때문이다. 같은 정책이 41.98과 33.79로 나온다.
"""
from __future__ import annotations

import glob
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
KEEP = ROOT / "workspace/_keep"
REGISTRY = QUAD / "config/go2_self_eval_registry.json"

sys.path.insert(0, str(QUAD))
sys.path.insert(0, str(ROOT / "tools"))
import go2_fixed_eval_report as fixed_eval  # noqa: E402
import tfcurve  # noqa: E402

# 텍스트 학습 로그가 없는 원본 회수본은 학습기가 쓴 텐서보드 기록에서 같은 곡선을 읽는다.
TF_TAGS = {
    "terrain": "Curriculum/terrain_levels",
    "reward": "Train/mean_reward",
    "episode_length": "Train/mean_episode_length",
    "track_lin_vel": "Episode_Reward/track_lin_vel_xy_exp",
    "base_contact": "Episode_Termination/base_contact",
    "time_out": "Episode_Termination/time_out",
    "action_std": "Policy/mean_std",
    "entropy_loss": "Loss/entropy",
}

REWARD_KEYS = (
    "track_lin_vel_xy_exp", "track_ang_vel_z_exp", "feet_air_time", "lin_vel_z_l2",
    "ang_vel_xy_l2", "action_rate_l2", "flat_orientation_l2", "dof_torques_l2",
    "dof_acc_l2", "undesired_contacts", "dof_pos_limits",
)
CURVE_ITERS = (200, 300, 500, 999)
# 학습 로그에서 이 줄들만 뽑아 해시한다. 시각·처리량 줄은 매번 달라지므로 뺀다.
METRIC_LINE = re.compile(
    r"(Curriculum/terrain_levels:|Mean reward:|Mean episode length:"
    r"|Episode_Reward/|Episode_Termination/|Mean action std:)"
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def terrain_at(log: Path, iteration: int) -> float | None:
    """그 iteration의 커리큘럼 도달 레벨.  체크포인트와 짝지을 때는 반드시 같은 iteration을 쓴다.

    한 곳에만 둔다.  2026-09-16 전에는 재평가 빌더가 자기 사본을 두고, 기준점은 iter 999 값을
    "iter900"이라는 주석과 함께 손으로 적어 넣었다(4.2503·4.7087 — 실제 @900은 3.4268·4.4937).
    """
    blocks = re.split(r"Learning iteration (\d+)/", _text(log))
    for i in range(1, len(blocks), 2):
        if int(blocks[i]) != iteration:
            continue
        hit = re.search(r"Curriculum/terrain_levels:\s*([\d.\-eE]+)", blocks[i + 1])
        return float(hit.group(1)) if hit else None
    return None


# 체크포인트가 저장되는 핀.  재평가·기준선 비교가 쓰는 iteration은 전부 여기 있다.
PIN_ITERATIONS = (700, 800, 900, 999)


def reward_weights(env_yaml: Path) -> dict[str, float]:
    """env.yaml의 reward 블록에서 weight만 읽는다 (yaml 의존성 없이)."""
    text = _text(env_yaml)
    out: dict[str, float] = {}
    for key in REWARD_KEYS:
        head = re.search(r"^(\s*)" + key + r":\s*$", text, re.M)
        if not head:
            continue
        indent = len(head.group(1))
        tail = text[head.end():]
        end = re.search(r"^\s{0,%d}\S" % indent, tail, re.M)
        block = tail[: end.start()] if end else tail
        weight = re.search(r"^\s*weight:\s*(-?[\d.eE+]+)\s*$", block, re.M)
        if weight:
            out[key] = float(weight.group(1))
    return out


def training_curve(log: Path) -> dict[str, Any]:
    """학습 로그에서 시각·반복수·커리큘럼 곡선·지표 지문을 뽑는다."""
    text = _text(log)
    stamp = re.search(r"Exact experiment name requested from command line: (\S+)", text)
    metrics = [ln for ln in text.splitlines() if METRIC_LINE.search(ln)]
    blocks = re.split(r"Learning iteration (\d+)/(\d+)", text)
    curve: dict[int, dict[str, float | None]] = {}
    total = None
    for i in range(1, len(blocks), 3):
        iteration, total = int(blocks[i]), int(blocks[i + 1])
        body = blocks[i + 2]

        def value(pattern: str) -> float | None:
            hit = re.search(pattern, body)
            return float(hit.group(1)) if hit else None

        curve[iteration] = {
            "terrain": value(r"Curriculum/terrain_levels:\s*([\d.\-eE]+)"),
            "reward": value(r"Mean reward:\s*([\d.\-eE]+)"),
            "episode_length": value(r"Mean episode length:\s*([\d.\-eE]+)"),
            "track_lin_vel": value(r"Episode_Reward/track_lin_vel_xy_exp:\s*([\d.\-eE]+)"),
            "base_contact": value(r"Episode_Termination/base_contact:\s*([\d.\-eE]+)"),
            "time_out": value(r"Episode_Termination/time_out:\s*([\d.\-eE]+)"),
            "action_std": value(r"Mean action std:\s*([\d.\-eE]+)"),
            "entropy_loss": value(r"Mean entropy loss:\s*([\d.\-eE]+)"),
        }
    return {
        "started": stamp.group(1) if stamp else None,
        "iterations_logged": len(curve),
        "max_iterations": total,
        "metric_fingerprint": hashlib.sha256("\n".join(metrics).encode()).hexdigest(),
        "metric_line_count": len(metrics),
        "curve": {str(i): curve[i] for i in CURVE_ITERS if i in curve},
    }


def tfevents_curve(path: Path) -> dict[str, Any]:
    """텐서보드 기록의 커리큘럼 곡선.  기록 순서 = 반복 순서(tfcurve.load와 같은 규칙)."""
    series: dict[str, list[float]] = {}
    for tag, value in tfcurve.scalars(str(path)):
        series.setdefault(tag, []).append(float(value))
    length = len(series.get(TF_TAGS["terrain"], []))
    curve = {}
    for it in CURVE_ITERS:
        if it < length:
            curve[str(it)] = {key: (series[tag][it] if len(series.get(tag, [])) > it else None)
                              for key, tag in TF_TAGS.items()}
    return {"source": path.relative_to(ROOT).as_posix(), "iterations_logged": length, "curve": curve}


def instrument_generation(summary: dict[str, Any]) -> str:
    """case summary가 어느 계측 세대에서 나왔는지 — 낙상을 어떻게 셌는가로 가린다."""
    if "measurement_contract" in summary:
        return "posture_gate_v2"
    if "posture_measured" in summary or "fallen_env_count" in summary:
        return "posture_gate_v1"
    return "no_fall_detection"


def rescore(arm_root: Path, registry: Path = REGISTRY) -> dict[str, Any]:
    """정본 registry 하나로 다시 채점한다. 회차가 당시 쓰던 registry는 쓰지 않는다."""
    policy = fixed_eval.build_policy(arm_root, registry)
    fractions = {sid: body.get("weighted_fraction", 0.0) for sid, body in policy["scenarios"].items()}
    scenarios = {sid: round(value * 70, 5) for sid, value in fractions.items()}
    cases = sorted(glob.glob(str(arm_root / "cases/seed_*/*/summary.json")))
    generation = instrument_generation(json.loads(Path(cases[0]).read_text(encoding="utf-8"))) if cases else None

    # 당시 판정이 실제로 쓴 숫자. 그 회차가 보관한 보고서에서 그대로 읽는다.
    recorded = arm_root / "SELF_EVAL_REPORT.json"
    as_recorded = None
    if recorded.is_file():
        stored = json.loads(recorded.read_text(encoding="utf-8"))
        as_recorded = round(
            sum(b.get("weighted_fraction", 0.0) for b in stored["scenarios"].values()) * 70, 5)

    # 추종 rmse 평균. 계측 세대가 바뀌어도 이 값은 움직이지 않아야 한다 — 바뀐 것이
    # 생존 측정뿐인지 확인하는 대조군이다(종합 §4). 그래서 원장이 같이 들고 나온다.
    rmses = []
    for case in cases:
        value = json.loads(Path(case).read_text(encoding="utf-8")).get("tracking_xy_rmse")
        if value is not None:
            rmses.append(float(value))

    return {
        "total_70": round(sum(fractions.values()) * 70, 5),
        "as_recorded_70": as_recorded,
        "tracking_xy_rmse_mean": round(sum(rmses) / len(rmses), 5) if rmses else None,
        "scenarios_70": scenarios,
        "observed_cases": policy.get("observed_telemetry_count"),
        "locomotion": policy.get("locomotion", {}).get("verdict"),
        "instrument": generation,
    }


def robot_evidence(run_dir: Path) -> dict[str, list[str]]:
    """회차가 어느 로봇인지 산출물로 가린다 — 디렉터리 이름으로 가리지 않는다.

    이름으로 걸렀더니 Pilot-01의 원본 학습 `train_260831-Go2_5var_1000`이 `go2_` 접두사가
    없다는 이유로 통째로 빠졌다. 이름은 사람이 붙이고 경로·상태파일은 학습기가 쓴다.
    """
    found: dict[str, list[str]] = {"quadruped": [], "humanoid": []}
    for path in run_dir.rglob("*"):
        posix = path.as_posix()
        if "rsl_rl/quadruped" in posix:
            found["quadruped"].append(posix)
        elif "rsl_rl/humanoid" in posix or "/humanoid/" in posix:
            found["humanoid"].append(posix)
        elif path.is_file() and path.name.lower().startswith("go2"):
            found["quadruped"].append(posix)
    for marker in ("STATUS.txt", "launcher.log"):
        note = run_dir / marker
        if not note.is_file():
            continue
        text = _text(note)
        for robot, needle in (("quadruped", "rsl_rl/quadruped"), ("humanoid", "rsl_rl/humanoid")):
            if needle in text:
                found[robot].append(f"{marker}:{needle}")
    return {robot: hits[:3] for robot, hits in found.items() if hits}


def is_quadruped(run_dir: Path) -> bool:
    evidence = robot_evidence(run_dir)
    return "quadruped" in evidence and "humanoid" not in evidence


def occurred(record: dict[str, Any]) -> str | None:
    """회차가 언제 일어났는가 — 학습 로그 · 평가 로그 · 학습기가 만든 run 폴더 이름 순."""
    return (record.get("training", {}).get("started")
            or record.get("evaluated")
            or record.get("trained_at_from_run_dir"))


def training_env_index(keep: Path = KEEP) -> dict[str, Path]:
    """학습 env.yaml의 sha256 → 경로. 평가 arm의 identity.json이 가리키는 학습을 찾는 데 쓴다."""
    index: dict[str, Path] = {}
    for path in sorted(keep.glob("**/env.yaml")):
        if path.parent.name == "training" or path.parent.name == "params":
            index.setdefault(hashlib.sha256(path.read_bytes()).hexdigest(), path)
    return index


def arm_rewards(arm_root: Path, record: dict[str, Any],
                env_index: dict[str, Path]) -> tuple[dict[str, float], str]:
    """그 arm 정책을 학습한 reward. 회차의 env.yaml을 모든 arm에 붙이지 않는다.

    2026-09-16 이전에는 회차 env.yaml 하나를 모든 arm 행에 적었다. 그래서 LEDGER의
    Pilot arm이 Default 가중치로, 각 baseline arm이 후보 가중치로 적혀 있었다.
    """
    identity = arm_root / "identity.json"
    if identity.is_file():
        env_sha = json.loads(identity.read_text(encoding="utf-8")).get("env_sha256")
        if env_sha in env_index:
            return reward_weights(env_index[env_sha]), "identity_env_sha256"
    if arm_root.name == "candidate" and record.get("training") and record.get("rewards"):
        return record["rewards"], "trained_in_this_run"
    return {}, "unknown"


def harvest(keep: Path = KEEP) -> list[dict[str, Any]]:
    """`_keep`의 Go2 회차를 학습 시각 순으로 돌려준다."""
    env_index = training_env_index(keep)
    records: list[dict[str, Any]] = []
    for run_dir in sorted(p for p in keep.iterdir() if p.is_dir() and is_quadruped(p)):
        record: dict[str, Any] = {
            "run": run_dir.name,
            "path": run_dir.relative_to(ROOT).as_posix(),
            "robot_evidence": robot_evidence(run_dir)["quadruped"],
        }

        # 최근 회차는 `training/env.yaml`로 묶여 오고, 08-31 원본 회수본은 학습기가 쓴
        # `<run>/params/env.yaml`만 있다. 둘 다 받는다.
        env_yaml = sorted(run_dir.glob("**/training/env.yaml")) or sorted(run_dir.glob("**/params/env.yaml"))
        if env_yaml:
            record["rewards"] = reward_weights(env_yaml[0])
            record["env_yaml"] = env_yaml[0].relative_to(ROOT).as_posix()

        log = sorted(run_dir.glob("**/candidate_training.log"))
        if log:
            record["training"] = training_curve(log[0])
            record["training"]["log"] = log[0].relative_to(ROOT).as_posix()

        case_logs = sorted(run_dir.glob("logs/*/seed_*.log"))
        if case_logs:
            stamp = re.search(r"20\d\d-\d\d-\d\d_\d\d-\d\d-\d\d", _text(case_logs[0]))
            record["evaluated"] = stamp.group(0) if stamp else None
        if not record.get("training"):
            # 텍스트 학습 로그가 없는 원본 회수본. 학습기가 만든 run 폴더와 체크포인트는 남아 있다.
            checkpoints = sorted(p for p in run_dir.rglob("model_*.pt"))
            stamps = [p.name for p in run_dir.rglob("*")
                      if p.is_dir() and re.fullmatch(r"20\d\d-\d\d-\d\d_\d\d-\d\d-\d\d", p.name)]
            if checkpoints and stamps:
                record["trained_at_from_run_dir"] = min(stamps)
                events = sorted(run_dir.rglob("events.out.tfevents.*"))
                record["training_log_missing"] = {
                    "checkpoints": [p.name for p in checkpoints],
                    # 2026-09-17 정정: 이전 문구 "곡선·종료 사유를 볼 수 없다"는 틀렸다. 텍스트 로그만 찾았다.
                    "note": ("텍스트 학습 로그 미회수 — 곡선은 텐서보드 기록에서 읽었다" if events
                             else "학습 로그 미회수 — 텍스트 로그도 텐서보드 기록도 없다"),
                }
                if events:
                    record["training_tfevents"] = tfevents_curve(events[0])

        arms: dict[str, Any] = {}
        for summary in run_dir.glob("**/cases/seed_*/*/summary.json"):
            arms.setdefault(summary.parents[3], None)
        for arm_root in sorted(arms):
            arms[arm_root] = rescore(arm_root)
            arms[arm_root]["rewards"], arms[arm_root]["rewards_source"] = arm_rewards(
                arm_root, record, env_index)
        record["arms"] = {root.name: body for root, body in arms.items()}
        generations = {body["instrument"] for body in record["arms"].values()}
        if len(record["arms"]) > 1:
            # 두 arm을 다른 계측으로 재면 그 비교는 정책 차이가 아니라 계측 차이를 읽는다.
            record["instrument_symmetric"] = len(generations) == 1

        records.append(record)

    records.sort(key=lambda r: (occurred(r) or "9999", r["run"]))
    _mark_replicates(records)
    return records


def _mark_replicates(records: list[dict[str, Any]]) -> None:
    """지표 지문이 같은 회차는 같은 학습이다 — 재탕인지 재현인지 표시한다."""
    seen: dict[str, str] = {}
    for record in records:
        fingerprint = record.get("training", {}).get("metric_fingerprint")
        if not fingerprint:
            continue
        if fingerprint in seen:
            record["replicate_of"] = seen[fingerprint]
        else:
            seen[fingerprint] = record["run"]


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    records = harvest()
    blob = json.dumps(records, indent=1, ensure_ascii=False)
    if out:
        out.write_text(blob + "\n", encoding="utf-8")
        print(f"{len(records)} runs -> {out}")
    else:
        print(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
