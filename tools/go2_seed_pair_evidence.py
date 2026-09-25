"""같은 다이얼 세 점을 한 표에 놓고, 어느 계수기가 단조인지 센다 — 생성 도구.

왜 필요한가.  `lin_vel_z_l2` 는 이제 걷는 기준선 위에서 세 값이 측정됐다: -2.0(G-A033),
-1.75(G-A044), -1.5(G-A043).  총점만 보면 가운데 값이 양 끝보다 **낮다**(38.89 < 42.53 < 44.62)
— 보간이 깨졌다는 뜻으로 읽힌다.  그런데 계단에 오른 로봇 수는 세 점에서 단조로 늘고,
자세 낙상 수는 가운데 점에서만 치솟는다.  한 표에 놓지 않으면 이 어긋남이 보이지 않는다.

이 도구는 판정하지 않는다.  세 회차의 산출물에서 같은 자를 대고 숫자를 옮길 뿐이다:

    python -B tools/go2_seed_pair_evidence.py

출력 `reports/evidence/go2_seed_pair_20260924/`:
  DIAL_THREE_POINTS.csv  회차마다 한 행 — 다이얼 값, 학습 seed, 총점, 계단 계수기, 낙상 계수기
  MONOTONICITY.csv       계수기마다 한 행 — 세 점이 다이얼 방향으로 단조인가

낙상 수는 평가 3 seed x 32 env = 96 개체를 합한 것이고, `posture_gate_v2` 의
`posture_fall_env_count_pessimistic` 이다.  계단 수는 `go2_stairs_behavior.py` 가 만든
STAIRS_CLIMB.csv 의 같은 96 개체 합이다.  총점은 `reports/runs/SCENARIO_SCORES.csv` 의 행이다.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
KEEP = ROOT / "workspace" / "_keep"
OUT = QUAD / "reports" / "evidence" / "go2_seed_pair_20260924"
STAIRS = QUAD / "reports" / "evidence" / "go2_stairs_behavior_20260916" / "STAIRS_CLIMB.csv"
SCORES = QUAD / "reports" / "runs" / "SCENARIO_SCORES.csv"

# 세 점 — 같은 기준선(G-A033 보상표) 위에서 이 다이얼만 움직인 회차들.  전부 학습 seed 42 다.
POINTS = (
    {"work_id": "G-A033", "run": "go2_g_a033_a017_track_lin_vel_xy_150", "lin_vel_z_l2": "-2.0",
     "role": "frozen baseline"},
    {"work_id": "G-A044", "run": "go2_g_a044_a033_lin_vel_z_m175", "lin_vel_z_l2": "-1.75",
     "role": "midpoint"},
    {"work_id": "G-A043", "run": "go2_g_a043_a033_lin_vel_z_m15", "lin_vel_z_l2": "-1.5",
     "role": "relaxed end"},
)
SEEDS = ("seed_101", "seed_202", "seed_303")
PUSH = ("push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y")
# (열 이름, case, 이 계수기가 커지면 좋은가)
FALL_COUNTERS = (
    ("falls_stairs_10_down", ("stairs_10_down",), False),
    ("falls_stairs_15_down", ("stairs_15_down",), False),
    ("falls_rough_lateral", ("rough_lateral",), False),
    ("falls_rough_forward", ("rough_forward",), False),
    ("falls_push_4dir", PUSH, False),
    ("falls_combined_yaw_right", ("combined_yaw_right",), False),
)
CLIMB_COUNTERS = (
    ("climb_10_down_ge2", "stairs_10_down", "body_rise_ge2", True),
    ("climb_15_down_ge1", "stairs_15_down", "body_rise_ge1", True),
    ("climb_15_down_ge2", "stairs_15_down", "body_rise_ge2", True),
)
COLUMNS = (["work_id", "run", "lin_vel_z_l2", "train_seed", "role", "total_70"]
           + [name for name, _c, _col, _g in CLIMB_COUNTERS]
           + [name for name, _c, _g in FALL_COUNTERS])


def cases_dir(run: str) -> Path:
    return KEEP / run / "evaluation" / "candidate" / "cases"


def falls(run: str, case_ids: tuple[str, ...]) -> int:
    total = 0
    for case_id in case_ids:
        for seed in SEEDS:
            path = cases_dir(run) / seed / case_id / "summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            total += int(summary["posture_fall_env_count_pessimistic"])
    return total


def climbs(run: str, case_id: str, column: str) -> int:
    total = 0
    with STAIRS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["run"] == run and row["arm"] == "candidate" and row["case"] == case_id:
                total += int(row[column])
    return total


def total_70(run: str) -> str:
    with SCORES.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["run"] == run and row["arm"] == "candidate":
                return row["total_70"]
    raise RuntimeError(f"{run} not in {SCORES.name} — run tools/build_go2_run_reports.py first")


def train_seed(run: str) -> str:
    """회수물이 적어 둔 학습 seed.  회차 사이의 유일한 통제 변수라서 표에 같이 둔다."""
    status = KEEP / run / "training" / "TRAIN_STATUS.txt"
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("SEED="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"{run}: TRAIN_STATUS.txt has no SEED line")


def rows() -> list[dict[str, str]]:
    table = []
    for point in POINTS:
        run = point["run"]
        row = {"work_id": point["work_id"], "run": run, "lin_vel_z_l2": point["lin_vel_z_l2"],
               "train_seed": train_seed(run), "role": point["role"], "total_70": total_70(run)}
        for name, case_id, column, _good in CLIMB_COUNTERS:
            row[name] = str(climbs(run, case_id, column))
        for name, case_ids, _good in FALL_COUNTERS:
            row[name] = str(falls(run, case_ids))
        table.append(row)
    return table


def monotonicity(table: list[dict[str, str]]) -> list[list[str]]:
    """다이얼을 -2.0 -> -1.75 -> -1.5 순으로 놓았을 때 계수기가 한 방향인가."""
    order = sorted(table, key=lambda row: float(row["lin_vel_z_l2"]))  # -2.0, -1.75, -1.5
    out = [["counter", "at_m2_0", "at_m1_75", "at_m1_5", "monotone", "reads"]]
    counters = [(name, "climb") for name, _c, _col, _g in CLIMB_COUNTERS]
    counters += [(name, "fall") for name, _c, _g in FALL_COUNTERS]
    counters.insert(0, ("total_70", "score"))
    for name, kind in counters:
        values = [float(row[name]) for row in order]
        rising = values[0] <= values[1] <= values[2]
        falling = values[0] >= values[1] >= values[2]
        monotone = rising or falling
        if kind == "climb":
            reads = ("다이얼을 풀수록 오른 로봇이 는다" if rising else
                     "가운데 값이 양 끝의 순서를 깬다" if not monotone else "다이얼을 풀수록 준다")
        elif kind == "fall":
            reads = ("가운데 값에서만 낙상이 솟는다 — 다이얼 크기로 설명되지 않는다"
                     if not monotone else "다이얼 방향과 같은 방향으로 움직인다")
        else:
            reads = ("가운데 값이 양 끝보다 낮다 — 보간이 성립하지 않는다"
                     if not monotone else "다이얼 방향과 같은 방향으로 움직인다")
        out.append([name, *(f"{value:g}" for value in values), str(monotone), reads])
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    table = rows()
    with (OUT / "DIAL_THREE_POINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(COLUMNS))
        writer.writeheader()
        writer.writerows(table)
    with (OUT / "MONOTONICITY.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(monotonicity(table))
    print(f"{len(table)} points -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
