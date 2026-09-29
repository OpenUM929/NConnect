#!/usr/bin/env python3
"""G-A057 보상 변수 일괄 탐색 — 실행 목록 확정 (재사용 / 새 학습 / 평가만 필요) (2026-09-29, Codex 작업 지시).

출발 설정은 A048 보상(G-A048 학습 env.yaml)이다.  실행마다 아래 여섯 항 중 **한 항만** 바꾼다.
완료 회차의 재사용은 **변수 이름·값이 같다는 것으로 정하지 않는다.**  다음이 모두 대응해야 재사용이다.

  1. 학습된 env.yaml 의 보상 항 **전체**(여섯 다이얼 + dof_torques·dof_acc·track_ang_vel_z·dof_pos_limits 등)가
     A048 env.yaml 에서 그 한 항만 바꾼 값과 같다.
  2. 학습 조건: TRAIN_SEED 42, NUM_ENVS 4096, MAX_ITERATIONS 1000, EVAL_CHECKPOINT_ITER 900 (meta/run_config.env).
  3. 학습 코드: training/candidate_source.sha256 의 train.py·play.py·go2_task/*.py 해시가 이 패키지가 싣는 파일과 같다.
  4. 평가: meta/evaluator.sha256·registry.sha256 이 이 패키지의 평가기·registry 와 같고, 69 case summary 가 모두 있다.
1~3 이 맞고 4 가 모자라면 EVAL_ONLY(보존 checkpoint 로 평가만), 1~3 중 하나라도 다르면 NEW_TRAIN 이다.
기준 정책이 다른 회차(A018·A038·A041 등)는 1 에서 걸러진다 — 참고자료이지 대체가 아니다.  미실행 패키지는
학습 산출물이 없으므로 후보에 오르지 않는다.

    python -B tools/go2_g_a057_sweep_plan.py            # 목록 출력 + 증거 파일 작성
출력: workspace/training/quadruped/reports/evidence/go2_g_a057_sweep_plan/SWEEP_PLAN.json, SWEEP_PLAN.md
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
KEEP = ROOT / "workspace/_keep"
sys.path.insert(0, str(GO2))
from candidate_suite_checks import reward_weights  # noqa: E402

WORK_ID = "G-A057"
BASE_ARM = "go2_g_a048_a033_lin_vel_z_m125"
BASE_LABEL = "A048"
SOURCE_PACKAGE = GO2 / "upload/G-A055/current/GO2_G_A055_a043_ang_vel_xy_m008_full69_v2.zip"
SOURCE_PREFIX = "go2_g_a055/"
CONDITIONS = {"TRAIN_SEED": "42", "NUM_ENVS": "4096", "MAX_ITERATIONS": "1000", "EVAL_CHECKPOINT_ITER": "900"}
CODE_FILES = ("train.py", "play.py", "go2_task/__init__.py", "go2_task/_finalize.py", "go2_task/agent_cfg.py",
              "go2_task/env_cfg.py")
CASE_COUNT = 69
# Codex 작업 지시 §2 의 표 그대로.  A048 값(기준)은 각 변수 목록에 들어 있고 한 번만 센다.
GRID = {
    "track_lin_vel_xy_exp": (1.2, 1.4, 1.5, 1.6),
    "lin_vel_z_l2": (-2.0, -1.75, -1.5, -1.375, -1.25, -1.0),
    "ang_vel_xy_l2": (-0.04, -0.05, -0.08),
    "feet_air_time": (0.01, 0.1, 0.2, 0.35),
    "action_rate_l2": (-0.008, -0.01, -0.012),
    "flat_orientation_l2": (0.0, -0.25, -0.5),
}
OUT = GO2 / "reports/evidence/go2_g_a057_sweep_plan"
TOL = 1e-12


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_key(name: str, value: float) -> str:
    """파일·폴더 이름에 쓰는 실행 키.  예: ang_vel_xy_l2 -0.08 -> ang_vel_xy_l2_m0p08"""
    text = f"{abs(value):g}".replace(".", "p")
    return f"{name}_{'m' if value < 0 else 'p'}{text}"


def base_weights() -> dict[str, float | None]:
    return reward_weights((KEEP / BASE_ARM / "training/env.yaml").read_text(encoding="utf-8"))


def same_weights(a: dict, b: dict) -> bool:
    if set(a) != set(b):
        return False
    for k in a:
        if (a[k] is None) != (b[k] is None):
            return False
        if a[k] is not None and abs(float(a[k]) - float(b[k])) > TOL:
            return False
    return True


def package_hashes() -> dict[str, str]:
    """이 패키지(G-A055 v2 payload 재사용)가 싣는 학습 코드·평가기·registry 해시."""
    import zipfile
    z = zipfile.ZipFile(SOURCE_PACKAGE)
    out = {f: sha(z.read(SOURCE_PREFIX + "candidate/" + f)) for f in CODE_FILES}
    out["evaluator"] = sha(z.read(SOURCE_PREFIX + "candidate/go2_eval_telemetry.py"))
    out["registry"] = sha(z.read(SOURCE_PREFIX + "go2_self_eval_registry.json"))
    return out


def run_config(arm: Path) -> dict[str, str]:
    out = {}
    p = arm / "meta/run_config.env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^([A-Z_]+)=(.*)$", line)
            if m:
                out[m.group(1)] = m.group(2).strip().strip("'\"")
    return out


def first_hash(path: Path) -> str | None:
    return path.read_text(encoding="utf-8").split()[0] if path.is_file() else None


def source_hashes(arm: Path) -> dict[str, str]:
    out = {}
    p = arm / "training/candidate_source.sha256"
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2:
                out[parts[1].lstrip("*")] = parts[0]
    return out


def candidate_arms() -> list[Path]:
    return sorted(d for d in KEEP.iterdir() if (d / "training/env.yaml").is_file() and (d / "meta/run_config.env").is_file())


def classify(arm: Path, want: dict, pkg: dict) -> tuple[str, list[str]]:
    """(REUSE|EVAL_ONLY|NO_MATCH, 이유 목록)."""
    why = []
    got = reward_weights((arm / "training/env.yaml").read_text(encoding="utf-8"))
    if not same_weights(got, want):
        return "NO_MATCH", ["보상 항 전체가 다름"]
    cfg = run_config(arm)
    for k, v in CONDITIONS.items():
        if cfg.get(k) != v:
            why.append(f"{k}={cfg.get(k)} (필요 {v})")
    src = source_hashes(arm)
    for f in CODE_FILES:
        if src.get(f) != pkg[f]:
            why.append(f"학습 코드 {f} 해시 불일치")
    if why:
        return "NO_MATCH", why
    ev = []
    if first_hash(arm / "meta/evaluator.sha256") != pkg["evaluator"]:
        ev.append("평가기 해시 불일치")
    if first_hash(arm / "meta/registry.sha256") != pkg["registry"]:
        ev.append("registry 해시 불일치")
    n = len(list((arm / "evaluation/candidate/cases").glob("seed_*/*/summary.json")))
    if n != CASE_COUNT:
        ev.append(f"평가 summary {n}/{CASE_COUNT}")
    return ("EVAL_ONLY", ev) if ev else ("REUSE", ["보상 전체·학습 조건·학습 코드·평가기·registry·69 case 일치"])


def plan() -> dict:
    base = base_weights()
    pkg = package_hashes()
    arms = candidate_arms()
    runs = []
    seen_base = False
    for name, values in GRID.items():
        for value in values:
            is_base = abs(float(base[name]) - value) <= TOL
            if is_base and seen_base:
                runs.append({"variable": name, "value": value, "key": run_key(name, value), "status": "BASE_SHARED",
                             "evidence": f"{BASE_LABEL} 기준값 — 첫 변수 행의 {BASE_LABEL} 결과를 공유, 반복 실행 안 함"})
                continue
            want = dict(base)
            want[name] = value
            matches = [(arm, *classify(arm, want, pkg)) for arm in arms]
            reuse = [m for m in matches if m[1] == "REUSE"]
            evalonly = [m for m in matches if m[1] == "EVAL_ONLY"]
            row = {"variable": name, "value": value, "key": run_key(name, value), "is_base": is_base,
                   "rewards": {k: want[k] for k in ("track_lin_vel_xy_exp", "feet_air_time", "lin_vel_z_l2",
                                                    "ang_vel_xy_l2", "action_rate_l2", "flat_orientation_l2")}}
            if reuse:
                row.update(status="REUSE", arm=reuse[0][0].name, evidence="; ".join(reuse[0][2]),
                           other_matches=[m[0].name for m in reuse[1:]])
            elif evalonly:
                row.update(status="EVAL_ONLY", arm=evalonly[0][0].name, evidence="; ".join(evalonly[0][2]))
            else:
                row.update(status="NEW_TRAIN", arm=None,
                           evidence="보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음")
            if is_base:
                seen_base = True
            runs.append(row)
    return {"work_id": WORK_ID, "base_arm": BASE_ARM, "base_label": BASE_LABEL, "base_env_rewards": base,
            "conditions": CONDITIONS, "package_hashes": pkg, "grid": {k: list(v) for k, v in GRID.items()},
            "searched_arms": [a.name for a in arms], "runs": runs}


def markdown(p: dict) -> str:
    lines = [f"# {WORK_ID} 실행 목록 (자동 생성: tools/go2_g_a057_sweep_plan.py)", "",
             f"출발 설정 {p['base_label']}(`{p['base_arm']}` 학습 env.yaml). 한 실행에 한 항만 바꾼다. "
             f"학습 seed {CONDITIONS['TRAIN_SEED']}, env {CONDITIONS['NUM_ENVS']}, {CONDITIONS['MAX_ITERATIONS']} iter, "
             f"평가 checkpoint {CONDITIONS['EVAL_CHECKPOINT_ITER']}, 69 case.", "",
             "| 변수 | 값 | 상태 | 근거 회차 | 근거 |", "|---|---:|---|---|---|"]
    for r in p["runs"]:
        lines.append(f"| {r['variable']} | {r['value']} | {r['status']} | {r.get('arm') or '—'} | {r['evidence']} |")
    counts = {}
    for r in p["runs"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines += ["", "집계: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), "",
              f"대조한 완료 회차 {len(p['searched_arms'])}개(workspace/_keep 에서 training/env.yaml 과 meta/run_config.env 가 있는 폴더).",
              "기준 정책이 다른 회차는 보상 항 전체가 달라 재사용하지 않는다. 미실행 패키지는 학습 산출물이 없어 후보가 아니다."]
    return "\n".join(lines) + "\n"


def main() -> int:
    p = plan()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SWEEP_PLAN.json").write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    (OUT / "SWEEP_PLAN.md").write_text(markdown(p), encoding="utf-8", newline="\n")
    for r in p["runs"]:
        print(f"{r['status']:12s} {r['variable']:22s} {r['value']:>8}  {r.get('arm') or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
