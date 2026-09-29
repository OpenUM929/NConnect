#!/usr/bin/env python3
"""`lin_vel_z_l2` 다이얼 네 점 표 — G-A048(−1.25) 회수 뒤 (2026-09-26).

왜 따로 있는가.  세 점 표 `reports/evidence/go2_seed_pair_20260924/DIAL_THREE_POINTS.csv` 는 발행된 G-A048 사양이
셀 그대로 인용하므로 고치지 않는다.  이 도구는 같은 계수기를 네 번째 점까지 **회수물에서 직접** 다시 센다
(정본 표 `reports/runs/SCENARIO_SCORES.csv`·`STAIRS_CLIMB.csv` 에 G-A048 이 아직 없기 때문이다).
세 점은 세 점 표와 글자 그대로 같아야 한다 — `--check` 가 그것을 확인한다.

셈:
  total_70          검증기 `harvest_verification.json` judgement.points_70 (G-A033 은 기준선 칸)
  climb_*           tools/go2_climb_count.py `count()` — 세 점 표·가설 판독기와 같은 함수
  falls_*           평가기 summary.json `posture_fall_env_count_pessimistic`, seed 101·202·303 합
  G1..G7_delta      judgement.scenarios[*].delta (G-A033 대비 시나리오 proxy 변화, G-A033 은 0)

한계.  네 점 모두 학습 seed 42 하나다.  점 사이의 차이에 학습 경로 흔들림이 얼마나 섞였는지는 측정 0건이다
(U2-SEED-REPLICATE-20260918 미결).  이 표는 판정이 아니라 관측이다.

    python -B tools/go2_lin_vel_z_dial_points.py           # 표를 만든다
    python -B tools/go2_lin_vel_z_dial_points.py --check   # 세 점이 세 점 표와 같은지만 본다
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
KEEP = ROOT / "workspace/_keep"
sys.path.insert(0, str(ROOT / "tools"))
import go2_climb_count as climb  # noqa: E402

OUT = QUAD / "reports/evidence/go2_g_a048_readout_20260926"
THREE = QUAD / "reports/evidence/go2_seed_pair_20260924/DIAL_THREE_POINTS.csv"

POINTS = (
    ("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150", "-2.0"),
    ("G-A044", "go2_g_a044_a033_lin_vel_z_m175", "-1.75"),
    ("G-A043", "go2_g_a043_a033_lin_vel_z_m15", "-1.5"),
    ("G-A048", "go2_g_a048_a033_lin_vel_z_m125", "-1.25"),
)
# 기준선 판정이 들어 있는 회수물(G-A033 자신에는 대조 판정이 없다).
BASELINE_SOURCE = "go2_g_a043_a033_lin_vel_z_m15"
SEEDS = ("seed_101", "seed_202", "seed_303")
PUSH = ("push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y")
CLIMBS = (("climb_10_down_ge2", "stairs_10_down", 0.10, "ge2"),
          ("climb_15_down_ge1", "stairs_15_down", 0.15, "ge1"),
          ("climb_15_down_ge2", "stairs_15_down", 0.15, "ge2"))
FALLS = (("falls_stairs_10_down", ("stairs_10_down",)),
         ("falls_stairs_15_down", ("stairs_15_down",)),
         ("falls_rough_lateral", ("rough_lateral",)),
         ("falls_rough_forward", ("rough_forward",)),
         ("falls_push_4dir", PUSH),
         ("falls_combined_yaw_right", ("combined_yaw_right",)))
SCENARIOS = ("G1", "G2", "G3", "G4", "G5", "G6", "G7")
COLUMNS = (["work_id", "lin_vel_z_l2", "train_seed", "total_70"] + [c[0] for c in CLIMBS]
           + [f[0] for f in FALLS] + [f"{g}_delta" for g in SCENARIOS])
# 세 점 표와 대조할 열(그 표에 있는 것만).
SHARED = ["total_70"] + [c[0] for c in CLIMBS] + [f[0] for f in FALLS]


def cases(run: str) -> Path:
    return KEEP / run / "evaluation" / "candidate" / "cases"


def judgement(run: str) -> dict:
    data = json.loads((KEEP / run / "harvest_verification.json").read_text(encoding="utf-8"))
    return data["judgement"]


def train_seed(run: str) -> str:
    for line in (KEEP / run / "training" / "TRAIN_STATUS.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("SEED="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"{run}: TRAIN_STATUS.txt has no SEED line")


def row(work_id: str, run: str, value: str) -> dict[str, str]:
    out = {"work_id": work_id, "lin_vel_z_l2": value, "train_seed": train_seed(run)}
    if work_id == "G-A033":
        out["total_70"] = f"{judgement(BASELINE_SOURCE)['points_70']['baseline']:.5f}"
        deltas = {g: 0.0 for g in SCENARIOS}
    else:
        j = judgement(run)
        out["total_70"] = f"{j['points_70']['candidate']:.5f}"
        deltas = {g: j["scenarios"][g]["delta"] for g in SCENARIOS}
    for name, case_id, height, key in CLIMBS:
        total = 0
        for seed in SEEDS:
            result = climb.count(cases(run) / seed / case_id / "steps.csv", height)
            if result is None or int(result["robots"]) != 32:
                raise RuntimeError(f"{run} {seed} {case_id}: climb record incomplete")
            total += int(result[key])
        out[name] = str(total)
    for name, case_ids in FALLS:
        total = 0
        for case_id in case_ids:
            for seed in SEEDS:
                s = json.loads((cases(run) / seed / case_id / "summary.json").read_text(encoding="utf-8"))
                total += int(s["posture_fall_env_count_pessimistic"])
        out[name] = str(total)
    for g in SCENARIOS:
        out[f"{g}_delta"] = f"{deltas[g]:+.5f}"
    return out


def monotonicity(table: list[dict[str, str]]) -> list[list[str]]:
    """−2.0 → −1.75 → −1.5 → −1.25 순으로 한 방향인가.  한 방향이 아니면 다이얼 크기만으로 설명되지 않는다."""
    out = [["counter", "at_m2_0", "at_m1_75", "at_m1_5", "at_m1_25", "monotone"]]
    for name in ["total_70"] + [c[0] for c in CLIMBS] + [f[0] for f in FALLS]:
        values = [float(r[name]) for r in table]
        up = all(a <= b for a, b in zip(values, values[1:]))
        down = all(a >= b for a, b in zip(values, values[1:]))
        out.append([name, *(f"{v:g}" for v in values), str(up or down)])
    return out


def check(table: list[dict[str, str]]) -> list[str]:
    with THREE.open(encoding="utf-8", newline="") as handle:
        stored = {r["work_id"]: r for r in csv.DictReader(handle)}
    faults = []
    for r in table:
        if r["work_id"] not in stored:
            continue
        for col in SHARED:
            if float(stored[r["work_id"]][col]) != float(r[col]):
                faults.append(f"{r['work_id']} {col}: three-point table {stored[r['work_id']][col]}, recount {r[col]}")
    return faults


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    table = [row(*p) for p in POINTS]
    faults = check(table)
    for fault in faults:
        print("MISMATCH", fault)
    if args.check:
        return 1 if faults else 0
    if faults:
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "DIAL_FOUR_POINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(table)
    with (OUT / "MONOTONICITY_FOUR.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(monotonicity(table))
    print(f"{len(table)} points -> {OUT.relative_to(ROOT)} (three points match {THREE.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
