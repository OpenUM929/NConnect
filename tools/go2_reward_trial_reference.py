#!/usr/bin/env python3
"""Go2 보상 변수 시험 이력 참고표 — `lin_vel_z_l2` 여섯 점 (2026-09-28).

왜 따로 있는가.  네 점 표(`go2_g_a048_readout_20260926/DIAL_FOUR_POINTS.csv`)는 발행 사양이 인용하므로 고치지 않는다.
이 도구는 같은 계수기(`tools/go2_lin_vel_z_dial_points.py`의 `row()`)로 여섯 점을 회수물에서 다시 센다.
G-A049·G-A050의 검증 판정은 `_keep`이 아니라 `workspace/server_returns/<ID>_REVIEW_20260927/`에 있다.
참고 문서 `workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md`의 표는 이 CSV에서 옮겼다.

    python -B tools/go2_reward_trial_reference.py           # CSV를 만든다
    python -B tools/go2_reward_trial_reference.py --check   # 저장된 CSV와 재계산이 같은지만 본다
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_lin_vel_z_dial_points as dial  # noqa: E402

OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_reward_trial_reference_20260928"
CSV_PATH = OUT / "LIN_VEL_Z_SIX_POINTS.csv"
REVIEW = {
    "go2_g_a050_a033_lin_vel_z_m1375": ROOT / "workspace/server_returns/G-A050_REVIEW_20260927/harvest_verification.json",
    "go2_g_a049_a033_lin_vel_z_m1": ROOT / "workspace/server_returns/G-A049_REVIEW_20260927/harvest_verification.json",
}
EXTRA = (("G-A050", "go2_g_a050_a033_lin_vel_z_m1375", "-1.375"),
         ("G-A049", "go2_g_a049_a033_lin_vel_z_m1", "-1.0"))


def table() -> list[dict[str, str]]:
    original = dial.judgement

    def judgement(run: str) -> dict:
        if run in REVIEW:
            return json.loads(REVIEW[run].read_text(encoding="utf-8"))["judgement"]
        return original(run)

    dial.judgement = judgement
    try:
        rows = [dial.row(*p) for p in list(dial.POINTS) + list(EXTRA)]
    finally:
        dial.judgement = original
    return sorted(rows, key=lambda r: -float(r["lin_vel_z_l2"]))


# A033 위 한 항 변경 회차 전부. 1단계에서 멈춘 회차(A038·A041·A042)는 일부 case만 평가했으므로
# 세 평가 seed 모두에 있는 case의 계수기만 세고, 나머지 칸과 총점은 비운다(0으로 채우지 않는다).
A033_TRIALS = (
    ("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150", "기준선"),
    ("G-A042", "go2_g_a042_a033_track_lin_vel_xy_160", "track_lin_vel_xy_exp 1.5→1.6"),
    ("G-A038", "go2_g_a038_a033_ang_vel_xy_m008", "ang_vel_xy_l2 -0.05→-0.08"),
    ("G-A041", "go2_g_a041_a033_ang_vel_xy_m004", "ang_vel_xy_l2 -0.05→-0.04"),
    ("G-A047", "go2_g_a047_a033_flat_orientation_m05", "flat_orientation_l2 0.0→-0.5"),
    ("G-A044", "go2_g_a044_a033_lin_vel_z_m175", "lin_vel_z_l2 -2.0→-1.75"),
    ("G-A043", "go2_g_a043_a033_lin_vel_z_m15", "lin_vel_z_l2 -2.0→-1.5"),
    ("G-A050", "go2_g_a050_a033_lin_vel_z_m1375", "lin_vel_z_l2 -2.0→-1.375"),
    ("G-A048", "go2_g_a048_a033_lin_vel_z_m125", "lin_vel_z_l2 -2.0→-1.25"),
    ("G-A049", "go2_g_a049_a033_lin_vel_z_m1", "lin_vel_z_l2 -2.0→-1.0"),
)
TRIALS_CSV = OUT / "A033_BASE_TRIALS.csv"
TRIAL_COLUMNS = (["work_id", "change", "cases_all_seeds", "total_70"] + [c[0] for c in dial.CLIMBS]
                 + [f[0] for f in dial.FALLS])
SCORES = ROOT / "workspace/training/quadruped/reports/runs/SCENARIO_SCORES.csv"


def full_total(work_id: str, run: str, n_cases: int, six: dict[str, str]) -> str:
    # 전수 69 = 23 case × 3 seed. DR case 이름에 seed가 들어가(dr_seed_101 등) 세 seed 공통 case는 22개다.
    if n_cases != 22:
        return ""
    if work_id in six:
        return six[work_id]
    with SCORES.open(encoding="utf-8", newline="") as handle:
        for r in csv.DictReader(handle):
            if r["run"] == run and r["arm"] == "candidate":
                return f"{float(r['total_70']):.5f}"
    return ""


def trial_row(work_id: str, run: str, change: str, six: dict[str, str]) -> dict[str, str]:
    base = dial.cases(run)
    present = set.intersection(*({p.name for p in (base / s).iterdir()} for s in dial.SEEDS))
    out = {"work_id": work_id, "change": change, "cases_all_seeds": str(len(present))}
    out["total_70"] = full_total(work_id, run, len(present), six)
    for name, case_id, height, key in dial.CLIMBS:
        if case_id not in present:
            out[name] = ""
            continue
        total = 0
        for seed in dial.SEEDS:
            result = dial.climb.count(base / seed / case_id / "steps.csv", height)
            if result is None or int(result["robots"]) != 32:
                total = None
                break
            total += int(result[key])
        out[name] = "" if total is None else str(total)
    for name, case_ids in dial.FALLS:
        if not all(c in present for c in case_ids):
            out[name] = ""
            continue
        total = 0
        for case_id in case_ids:
            for seed in dial.SEEDS:
                s = json.loads((base / seed / case_id / "summary.json").read_text(encoding="utf-8"))
                total += int(s["posture_fall_env_count_pessimistic"])
        out[name] = str(total)
    return out


def write(path: Path, columns, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rows = table()
    six = {r["work_id"]: r["total_70"] for r in rows}
    trials = [trial_row(*t, six) for t in A033_TRIALS]
    if args.check:
        bad = [p.name for p, r in ((CSV_PATH, rows), (TRIALS_CSV, trials)) if read(p) != r]
        if bad:
            print("MISMATCH:", ", ".join(bad))
            return 1
        print("OK")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    write(CSV_PATH, dial.COLUMNS, rows)
    write(TRIALS_CSV, TRIAL_COLUMNS, trials)
    print(CSV_PATH)
    print(TRIALS_CSV)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
