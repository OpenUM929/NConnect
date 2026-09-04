"""Re-score H1 survival on the flat scenarios with the posture gate.

The archived ``steps.csv`` carries ``root_z`` but no orientation and no terrain
height, so only the flat scenarios (H1-H4, H7 = weight 0.70 of the official
total) can be re-scored.  H5 (rough) and H6 (slope) move the ground under the
base, which makes a world-frame height test meaningless there.
"""
from __future__ import annotations

import csv
import glob
import os
import statistics
import sys

# H1 pelvis stands at ~0.91 m and spawns at 1.05 m.  A humanoid that has gone
# down is at roughly a third of that; 0.55 m is deliberately generous so a deep
# crouch is not miscounted as a fall.
FALL_HEIGHT_M = float(os.environ.get("NCRC_H1_FALL_HEIGHT", 0.55))
FALL_HOLD_S = 0.5
FALL_GRACE_S = 0.5

FLAT = {"H1_stand", "H2_forward", "H3_left", "H3_right", "H4_left", "H4_right", "H7_push"}
WEIGHT = {"H1": 0.15, "H2": 0.20, "H3": 0.10, "H4": 0.10, "H5": 0.15, "H6": 0.15, "H7": 0.15}


def score_case(path: str) -> dict:
    per_env: dict[int, list[tuple[float, float, int]]] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            per_env.setdefault(int(row["env_id"]), []).append(
                (float(row["time_s"]), float(row["root_z"]), int(row["terminated"]))
            )
    fallen = 0
    terminated = 0
    zmin = float("inf")
    for env_id, rows in per_env.items():
        rows.sort()
        run = 0.0
        prev_t = rows[0][0]
        down = False
        for t, z, term in rows:
            zmin = min(zmin, z)
            dt = max(t - prev_t, 0.0)
            prev_t = t
            if term:
                terminated += 1
            if t < FALL_GRACE_S:
                continue
            run = run + dt if z < FALL_HEIGHT_M else 0.0
            if run >= FALL_HOLD_S:
                down = True
        if down:
            fallen += 1
    n = len(per_env)
    return {
        "envs": n,
        "v1": 1.0 - terminated / n if n else None,
        "v2": 1.0 - fallen / n if n else None,
        "fallen": fallen,
        "root_z_min": zmin,
    }


def main() -> int:
    root = "workspace/_keep/train_260831-06_run05cfg_10000_independent_eval/seeds"
    worst: dict[str, dict] = {}
    print(f"{'case':12s} {'seed':6s} {'envs':>5s} {'surv_v1':>8s} {'surv_v2':>8s} {'fallen':>6s} {'root_z_min':>10s}")
    for seed_dir in sorted(glob.glob(f"{root}/seed_*")):
        seed = os.path.basename(seed_dir)
        for csv_path in sorted(glob.glob(f"{seed_dir}/cases/*/steps.csv")):
            case = os.path.basename(os.path.dirname(csv_path))
            if case not in FLAT:
                continue
            r = score_case(csv_path)
            print(f"{case:12s} {seed:6s} {r['envs']:5d} {r['v1']:8.4f} {r['v2']:8.4f} "
                  f"{r['fallen']:6d} {r['root_z_min']:10.4f}")
            cur = worst.get(case)
            if cur is None or r["v2"] < cur["v2"]:
                worst[case] = r
    print()
    print("worst-case across seeds (official weight 0.70 covered):")
    delta_total = 0.0
    for case in sorted(worst):
        r = worst[case]
        scen = case.split("_")[0]
        w = WEIGHT[scen] / (2 if scen in ("H3", "H4") else 1)
        d = (r["v1"] - r["v2"]) * w * 70
        delta_total += d
        print(f"  {case:12s} v1={r['v1']:.4f} -> v2={r['v2']:.4f}  "
              f"weight={w:.3f}  point_delta={-d:+.3f}")
    print(f"\nTOTAL simulation point change on flat scenarios: {-delta_total:+.3f} / 70")
    print(f"threshold: root_z < {FALL_HEIGHT_M} m held {FALL_HOLD_S}s after {FALL_GRACE_S}s grace")
    print("NOT_RESCORABLE (terrain height moves under the base): H5_rough, H6_plus10, H6_minus10")
    return 0


if __name__ == "__main__":
    sys.exit(main())
