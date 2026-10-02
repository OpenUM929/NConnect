"""Go2 G-A033 sentinel cross-device check (2026-10-02).

Every iter-pinned run also evaluates the same frozen G-A033 sentinel policy on 5 cases.
Comparing those summaries across runs separates the evaluation layer (same policy, same
case) from the training layer. Server runs are compared with each other (same device)
and with the PC runs (different device). No thresholds; observed values only.

Usage: python -B tools/go2_sentinel_cross_device.py [--check]
"""
import csv
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = os.path.join(ROOT, "workspace", "_keep")
OUT_DIR = os.path.join(ROOT, "workspace", "training", "quadruped", "reports", "evidence",
                       "go2_sentinel_cross_device_20261002")
REFERENCE = "go2_g_a048_a033_lin_vel_z_m125"  # server run used as the reference row
PC_RUNS = {"go2_g_a057_track_lin_vel_xy_exp_p1p2", "go2_g_a058_a043_seed43", "go2_g_a058_a048_seed42"}
METRICS = ["posture_fall_env_count_pessimistic", "terminated_env_count", "survival_proxy",
           "speed_xy_mean", "tracking_xy_rmse", "height_rel_median", "wall_seconds"]


def sentinel_runs():
    runs = []
    for d in sorted(glob.glob(os.path.join(KEEP, "go2_g_a0*"))):
        if glob.glob(os.path.join(d, "evaluation", "g_a033_sentinel", "cases", "*", "*", "summary.json")):
            runs.append(os.path.basename(d))
    return runs


def load(run):
    base = os.path.join(KEEP, run, "evaluation", "g_a033_sentinel", "cases")
    out = {}
    for f in glob.glob(os.path.join(base, "*", "*", "summary.json")):
        seed, case = os.path.relpath(f, base).replace("\\", "/").split("/")[:2]
        with open(f, encoding="utf-8") as fh:
            out[(seed, case)] = json.load(fh)
    return out


def rows():
    ref = load(REFERENCE)
    result = []
    for run in sentinel_runs():
        data = load(run)
        for key in sorted(ref):
            if key not in data:
                continue
            row = {"run": run, "device": "PC1" if run in PC_RUNS else "server",
                   "seed": key[0], "case": key[1]}
            for m in METRICS:
                row[m] = data[key].get(m)
                r = ref[key].get(m)
                v = data[key].get(m)
                row["d_" + m] = (v - r) if isinstance(v, (int, float)) and isinstance(r, (int, float)) else None
            result.append(row)
    return result


def main():
    table = rows()
    if not table:
        print("no sentinel runs found")
        return 1
    fields = ["run", "device", "seed", "case"] + METRICS + ["d_" + m for m in METRICS]
    if "--check" in sys.argv:
        path = os.path.join(OUT_DIR, "SENTINEL_CROSS_DEVICE.csv")
        with open(path, encoding="utf-8", newline="") as fh:
            old = list(csv.DictReader(fh))
        same = len(old) == len(table) and all(
            str(o["run"]) == str(n["run"]) and str(o["case"]) == str(n["case"]) for o, n in zip(old, table))
        print("CHECK_OK" if same else "CHECK_MISMATCH")
        return 0 if same else 1
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "SENTINEL_CROSS_DEVICE.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(table)
    # range of posture falls per case, split by device
    summary = {}
    for r in table:
        summary.setdefault((r["case"], r["device"]), []).append(r["posture_fall_env_count_pessimistic"])
    for (case, dev), vals in sorted(summary.items()):
        vals = [v for v in vals if v is not None]
        print(f"{case:16s} {dev:6s} n={len(vals):2d} posture_falls min={min(vals)} max={max(vals)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
