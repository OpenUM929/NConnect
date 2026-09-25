"""계단 앞 **정체**와 **첫 단 도달시간** — 평가 `steps.csv`에서만 읽는다 (표준 라이브러리만).

왜 있는가 (2026-09-21).  계획 `upload/plan/GO2_FORWARD_STAIRS_POLICY_20260921.md` §4는 계단 개선을
점수가 아니라 **행동**으로 재라고 요구한다: ②명령 방향으로 거의 움직이지 않는 시간의 비율, ③처음
한 단을 오른 시각.  기존 지표로는 둘 다 읽히지 않는다 — `speed_xy_mean`은 종료 뒤 행까지 섞인 전체
평균이고(G-A041 판독 §원시 채널), 오른 로봇 수(`tools/go2_climb_count.py`)는 **언제** 올랐는지를
말하지 않는다.

정의 (계획 §4 item 2·3 그대로. 문턱은 설계값이며 측정값이 아니다):
  정체시간비율   명령 전진이 양수인 case에서, 첫 종료 전 구간의 행만 본다.  처음 `0.5초`는 빼고,
                 terminal 행과 그 이후도 뺀다(`go2_climb_count.alive_rows`와 같은 절단).
                 명령 방향 투영속도가 `0.05 m/s` 미만인 상태가 **연속 1초 이상** 이어진 구간의
                 시간을 더해 유효시간으로 나눈다.  유효시간이 0이면 값은 `None`이고 이유를 적는다.
  첫 단 도달시각 `go2_climb_count.gained_steps`가 1을 넘는 첫 행의 `time_s`.  못 오른 로봇은
                 `None` + `censored=True`다.  도달자만 평균내 전체 개선으로 적지 않는다 —
                 `arrival_rate`를 반드시 함께 낸다.

    python -B tools/go2_stall_diagnostics.py --candidate workspace/_keep/<회차>/evaluation/candidate
    python -B tools/go2_stall_diagnostics.py --candidate <...> --baseline <...> --out <폴더>
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import go2_climb_count as climb  # noqa: E402

SCHEMA_VERSION = "go2_stall_diagnostics_v2"
GENERATOR_VERSION = "2.0.0"
STALL_SPEED = 0.05      # m/s, 계획 §4 item 2 의 설계값
MIN_RUN_S = 1.0         # 연속 이 시간 이상이어야 '정체'로 센다
GRACE_S = 0.5           # 시작 흔들림 제외 (평가기 posture_gate 의 grace 와 같은 값)
EXPECTED_ROBOTS = 32
SEEDS = ("101", "202", "303")
CASES = ("stairs_10_down", "stairs_15_down")
BASELINE = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
OUT = QUAD / "reports/evidence/go2_stall_diagnostics_20260921"


FIELDS = (
    "arm", "case", "seed", "robots", "expected_robots", "valid_robots", "missing_robots",
    "coverage_complete", "direction", "valid_seconds", "stall_seconds", "stall_share",
    "stall_share_median", "arrivals", "arrival_rate", "first_step_time_median_s", "censored", "reason",
)
ENV_FIELDS = (
    "arm", "case", "seed", "env_id", "observed", "valid_seconds", "stall_seconds", "stall_share",
    "first_step_time_s", "censored", "reason",
)


def specification() -> dict:
    """Machine-readable measurement contract; values are definitions, not inferred run facts."""
    return {
        "units": {
            "projected_speed": "m/s", "valid_seconds": "s", "stall_seconds": "s",
            "stall_share": "fraction", "first_step_time": "s", "arrival_rate": "fraction",
        },
        "coordinate_frame": "body frame",
        "coordinate_source": "go2_eval_telemetry.py robot.data.root_lin_vel_b[:, :2]",
        "projection": "actual body-frame xy velocity projected onto command body-frame xy direction",
        "window": {
            "initial_grace_s": GRACE_S,
            "end": "exclusive of the first terminated/truncated row and all later rows",
            "stall_threshold_m_s": STALL_SPEED,
            "minimum_contiguous_stall_s": MIN_RUN_S,
        },
        "first_step_rule": "first time_s where go2_climb_count gained-step rule reaches >=1",
        "coverage_rule": "all expected environments must be present and stall-valid; censored arrivals remain valid",
        "exclusions": ["initial grace window", "terminal row", "rows after first terminal row"],
    }


def projected_speed(row: dict[str, str]) -> float | None:
    """명령 방향으로의 투영속도.  명령이 0이면 방향이 없으므로 None."""
    cx, cy = float(row["cmd_vx"]), float(row["cmd_vy"])
    norm = (cx * cx + cy * cy) ** 0.5
    if norm <= 0.0:
        return None
    return (float(row["actual_vx"]) * cx + float(row["actual_vy"]) * cy) / norm


def env_stall(env_rows: list[dict[str, str]]) -> tuple[float, float] | None:
    """(유효시간, 정체시간).  명령 방향이 없거나 유효 행이 없으면 None."""
    dt = None
    if len(env_rows) >= 2:
        dt = float(env_rows[1]["time_s"]) - float(env_rows[0]["time_s"])
    if not dt or dt <= 0:
        return None
    grace = int(round(GRACE_S / dt))
    rows = env_rows[grace:]
    speeds = [projected_speed(row) for row in rows]
    speeds = [s for s in speeds if s is not None]
    if len(speeds) != len(rows) or not speeds:
        return None
    need = int(round(MIN_RUN_S / dt))
    stalled, run = 0, 0
    for speed in [*speeds, None]:            # 마지막에 None 을 넣어 진행 중인 구간을 닫는다
        if speed is not None and speed < STALL_SPEED:
            run += 1
            continue
        if run >= need:
            stalled += run
        run = 0
    return len(speeds) * dt, stalled * dt


def env_reading(env_id: str, env_rows: list[dict[str, str]], direction: str, height: float) -> dict:
    """Retain one environment's valid/null/censored result instead of dropping it in aggregation."""
    measured = env_stall(env_rows)
    first_step = env_first_step(env_rows, direction, height)
    if measured is None:
        valid = stalled = share = None
        reason = "no valid command-directed time after the grace window"
    else:
        valid, stalled = measured
        share = stalled / valid if valid > 0 else None
        reason = "" if valid > 0 else "no valid time after the grace window"
    return {
        "env_id": str(env_id),
        "observed": True,
        "valid_seconds": round(valid, 3) if valid is not None else None,
        "stall_seconds": round(stalled, 3) if stalled is not None else None,
        "stall_share": round(share, 6) if share is not None else None,
        "first_step_time_s": round(first_step, 3) if first_step is not None else None,
        "censored": first_step is None,
        "reason": reason,
    }


def env_first_step(env_rows: list[dict[str, str]], direction: str, height: float) -> float | None:
    """`gained_steps`가 1이 되는 첫 행의 시각.  못 오르면 None (censored)."""
    if not env_rows:
        return None
    base = env_rows[min(climb.SETTLE_ROW, len(env_rows) - 1)]
    z0 = float(base["root_z"])
    x0, y0 = float(env_rows[0]["root_x"]), float(env_rows[0]["root_y"])
    best = None
    for row in env_rows:
        if not climb.travelled(row, x0, y0):
            continue
        z = float(row["root_z"])
        best = z if best is None else (max(best, z) if direction == "climb" else min(best, z))
        rise = (best - z0) if direction == "climb" else (z0 - best)
        if int((rise + climb.STEP_TOLERANCE * height) // height) >= 1:
            return float(row["time_s"])
    return None


def case_reading(steps: Path, case_id: str) -> dict:
    """한 case·seed 의 정체·도달 판독.  원자료가 없으면 reason 만 남는다."""
    height = climb.STAIR_HEIGHTS[case_id]
    # 없는 기록은 0 이 아니다.  모든 칸을 None 으로 두고 이유를 적는다 (계획 §4 item 4).
    empty = {key: None for key in FIELDS if key not in ("arm", "case", "seed")}
    expected = EXPECTED_ROBOTS
    metadata_path = steps.parent / "metadata.json"
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            expected = int(metadata["num_envs"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    expected_ids = {str(index) for index in range(expected)}

    def absent(reason: str) -> dict:
        environment_readings = [
            {
                "env_id": env_id, "observed": False, "valid_seconds": None, "stall_seconds": None,
                "stall_share": None, "first_step_time_s": None, "censored": None,
                "reason": "environment absent from steps.csv",
            }
            for env_id in sorted(expected_ids, key=int)
        ]
        return {
            **empty, "robots": 0, "expected_robots": expected, "valid_robots": 0,
            "missing_robots": expected, "coverage_complete": False, "reason": reason,
            "environment_readings": environment_readings,
        }

    if not steps.is_file():
        return absent("steps.csv absent")
    by = climb.alive_rows(steps)
    if not by:
        return absent("no rows before the first termination")
    counted = climb.count(steps, height)
    direction = counted["direction"]
    environment_readings = [env_reading(env_id, env_rows, direction, height) for env_id, env_rows in by.items()]
    observed_ids = set(by)
    missing_ids = expected_ids - observed_ids
    for env_id in sorted(missing_ids, key=int):
        environment_readings.append({
            "env_id": env_id, "observed": False, "valid_seconds": None, "stall_seconds": None,
            "stall_share": None, "first_step_time_s": None, "censored": None,
            "reason": "environment absent from steps.csv",
        })
    environment_readings.sort(
        key=lambda item: (0, int(item["env_id"])) if item["env_id"].isdigit() else (1, item["env_id"])
    )
    valid_envs = [item for item in environment_readings if item["observed"] and item["valid_seconds"] is not None]
    valid_total = sum(item["valid_seconds"] for item in valid_envs)
    stall_total = sum(item["stall_seconds"] for item in valid_envs)
    shares = [item["stall_share"] for item in valid_envs if item["stall_share"] is not None]
    reached = [item["first_step_time_s"] for item in environment_readings
               if item["observed"] and item["first_step_time_s"] is not None]
    unexpected_ids = observed_ids - expected_ids
    coverage_complete = not missing_ids and not unexpected_ids and len(valid_envs) == expected
    coverage_reasons = []
    if len(by) != expected:
        coverage_reasons.append(f"expected {expected} environments, observed {len(by)}")
    invalid_count = len(by) - len(valid_envs)
    if invalid_count:
        coverage_reasons.append(f"{invalid_count} observed environments lack valid stall time")
    if unexpected_ids:
        coverage_reasons.append("unexpected environment ids: " + ",".join(sorted(unexpected_ids)))
    return {
        "robots": len(by),
        "expected_robots": expected,
        "valid_robots": len(valid_envs),
        # A present env with a null denominator is also missing from screening coverage.
        "missing_robots": max(expected - len(valid_envs), 0),
        "coverage_complete": coverage_complete,
        "direction": direction,
        "valid_seconds": round(valid_total, 3),
        "stall_seconds": round(stall_total, 3),
        # 풀링 비율은 시간으로 가중한 값이고, 중앙값은 로봇 단위다.  둘은 다른 수다.
        "stall_share": round(stall_total / valid_total, 6) if valid_total > 0 else None,
        "stall_share_median": round(statistics.median(shares), 6) if shares else None,
        "arrivals": len(reached),
        "arrival_rate": round(len(reached) / len(by), 6),
        "first_step_time_median_s": round(statistics.median(reached), 3) if reached else None,
        "censored": len(by) - len(reached),
        "reason": "; ".join(coverage_reasons),
        "environment_readings": environment_readings,
    }


def arm_reading(arm: Path, cases: tuple[str, ...] = CASES, seeds: tuple[str, ...] = SEEDS) -> list[dict]:
    rows = []
    for case_id in cases:
        for seed in seeds:
            steps = arm / "cases" / f"seed_{seed}" / case_id / "steps.csv"
            rows.append({"arm": arm.parent.parent.name, "case": case_id, "seed": seed,
                         **case_reading(steps, case_id)})
    return rows


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_status(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    return dict(line.split("=", 1) for line in lines if "=" in line)


def _run_root(arm: Path) -> Path:
    """Return the nearest ancestor carrying actual run identity/pin files."""
    for parent in (arm, *arm.parents):
        if (parent / "RUNNER_STATUS.txt").is_file() or (parent / "meta" / "experiment.json").is_file():
            return parent
    return arm


def arm_provenance(arm: Path, evaluation_seeds: tuple[str, ...] = SEEDS) -> dict:
    """Read provenance from identity/status/experiment files; missing facts remain null."""
    identity = _read_json(arm / "identity.json")
    root = _run_root(arm)
    status = _read_status(root / "RUNNER_STATUS.txt")
    experiment = _read_json(root / "meta" / "experiment.json")
    training = experiment.get("training") if isinstance(experiment.get("training"), dict) else {}
    evaluation = experiment.get("evaluation") if isinstance(experiment.get("evaluation"), dict) else {}
    arm_prefix = arm.name.upper()

    checkpoint = status.get(f"{arm_prefix}_EVAL_ITER") or status.get("EVAL_CHECKPOINT_ITER")
    if checkpoint is None:
        checkpoint = evaluation.get("checkpoint_iter")
    try:
        checkpoint = int(checkpoint) if checkpoint is not None else None
    except (TypeError, ValueError):
        checkpoint = None

    training_seed = status.get("TRAIN_SEED")
    if training_seed is None:
        training_seed = training.get("seed")
    try:
        training_seed = int(training_seed) if training_seed is not None else None
    except (TypeError, ValueError):
        training_seed = None

    recorded_evaluation_seeds = sorted({
        str(metadata["evaluation_seed"])
        for path in (arm / "cases").glob("seed_*/*/metadata.json")
        for metadata in [_read_json(path)]
        if metadata.get("evaluation_seed") is not None
    })
    requested_evaluation_seeds = [str(seed) for seed in evaluation_seeds]
    values = {
        "arm": arm.name,
        "arm_path": str(arm),
        "run_id": status.get("RUN_ID") or experiment.get("run_id"),
        "model_sha256": identity.get("model_sha256"),
        "checkpoint_iter": checkpoint,
        "evaluator": status.get("EVALUATOR"),
        "evaluator_sha256": identity.get("evaluator_sha256") or status.get("EVALUATOR_SHA"),
        "registry_sha256": identity.get("registry_sha256") or status.get("REGISTRY_SHA"),
        "training_seed": training_seed,
        "evaluation_seeds": recorded_evaluation_seeds or None,
        "requested_evaluation_seeds": requested_evaluation_seeds,
        "sources": {
            "identity": str(arm / "identity.json"),
            "runner_status": str(root / "RUNNER_STATUS.txt"),
            "experiment": str(root / "meta" / "experiment.json"),
        },
    }
    required = (
        "run_id", "model_sha256", "checkpoint_iter", "evaluator", "evaluator_sha256",
        "registry_sha256", "training_seed",
    )
    missing = [key for key in required if values[key] in (None, "")]
    if values["evaluation_seeds"] is None:
        missing.append("evaluation_seeds")
    elif set(values["evaluation_seeds"]) != set(requested_evaluation_seeds):
        missing.append("evaluation_seeds_mismatch")
    values["provenance_complete"] = not missing
    values["reason"] = "" if not missing else "missing provenance: " + ", ".join(missing)
    return values


def provenance_sidecar(arms: tuple[Path, ...], evaluation_seeds: tuple[str, ...] = SEEDS) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generator": {"path": "tools/go2_stall_diagnostics.py", "version": GENERATOR_VERSION},
        "specification": specification(),
        "arms": [arm_provenance(arm, evaluation_seeds) for arm in arms],
    }


def write_env_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ENV_FIELDS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            common = {"arm": row.get("arm"), "case": row.get("case"), "seed": row.get("seed")}
            for environment in row.get("environment_readings", []):
                item = {**common, **environment}
                writer.writerow({key: ("" if item.get(key) is None else item.get(key, "")) for key in ENV_FIELDS})


def write_outputs(rows: list[dict], out: Path, provenance: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    write_csv(rows, out / "STALL_DIAGNOSTICS.csv")
    write_env_csv(rows, out / "STALL_DIAGNOSTICS_ENV.csv")
    sidecar = {
        **provenance,
        "schema_version": provenance.get("schema_version", SCHEMA_VERSION),
        "generator": provenance.get(
            "generator", {"path": "tools/go2_stall_diagnostics.py", "version": GENERATOR_VERSION}
        ),
        "specification": provenance.get("specification", specification()),
    }
    (out / "STALL_DIAGNOSTICS_PROVENANCE.json").write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )




def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: ("" if row.get(key) is None else row.get(key, "")) for key in FIELDS})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path, help="evaluation/candidate of the run")
    parser.add_argument("--baseline", type=Path, default=BASELINE, help="the arm it is read against")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--json", action="store_true", help="print the rows instead of writing the CSV")
    args = parser.parse_args(argv)
    rows = [*arm_reading(args.baseline), *arm_reading(args.candidate)]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    write_outputs(rows, args.out, provenance_sidecar((args.baseline, args.candidate)))
    path = args.out / "STALL_DIAGNOSTICS.csv"
    print(f"wrote {path} ({len(rows)} rows) and per-environment/provenance sidecars")
    for row in rows:
        print("  %-38s %-16s %s  stall_share=%s  first_step=%s  arrival_rate=%s" % (
            row["arm"], row["case"], row["seed"], row["stall_share"],
            row["first_step_time_median_s"], row["arrival_rate"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
