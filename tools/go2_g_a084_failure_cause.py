"""G-A084 failure-cause check against G-A083 (read-only, evaluation steps.csv only).

1. 15 cm climb (case stairs_15_down = climbing up): per robot, the first-step edge time T is
   the first step where terrain_z under the body rises by more than half the step height
   above its start.  In the window T-0.5 s .. T+1.5 s (the window of
   reports/GO2_STAIRS_CAUSE_TO_LECTURE_20260928.md section 1-1) report body height change,
   peak root_z rise speed and peak tilt (1 + proj_grav_z; roll and pitch are not separable
   in steps.csv).  Robots are split by the posture-gate fall verdict (upright == 0 after step 25).
2. Flat heading drift: per robot mean actual_wz at cmd_wz == 0 on the flat cases, and the
   share of robots turning to the same side.
   max_tilt_rate is the peak |d(1 + proj_grav_z)/dt| in the edge window, a proxy for the
   roll/pitch rate that ang_vel_xy_l2 penalizes (only its tilting component is visible).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARMS = {"g_a083": ROOT / "workspace/_keep/go2_g_a083_action_rate_m0p01/evaluation/candidate/cases",
        "g_a084": ROOT / "workspace/_keep/go2_g_a084_ang_vel_xy_m0p065/evaluation/candidate/cases"}
SEEDS = ("101", "202", "303")
FLAT = ("forward_slow", "forward_nominal", "forward_fast", "backward", "left", "right",
        "diagonal_left", "diagonal_right")
COLS = ["step", "env_id", "root_z", "terrain_z", "proj_grav_z", "height_rel", "upright", "actual_vx"]


def edge_rows(cases: Path, case: str, height: float) -> list[dict]:
    out = []
    for s in SEEDS:
        a = pd.read_csv(cases / f"seed_{s}" / case / "steps.csv", usecols=COLS)
        for env, g in a.groupby("env_id"):
            g = g.sort_values("step")
            bad = g[(g.step > 25) & (g.upright == 0)]
            fall_step = int(bad.step.iloc[0]) if len(bad) else None
            rise = g.terrain_z - g.terrain_z.iloc[0]
            hit = g[rise > height / 2]
            row = {"seed": s, "env": int(env), "fell": fall_step is not None, "fall_step": fall_step,
                   "reached_edge": len(hit) > 0}
            if len(hit):
                t = int(hit.step.iloc[0])
                row["edge_step"] = t
                row["fell_before_edge"] = fall_step is not None and fall_step < t
                w = g[(g.step >= t - 25) & (g.step <= t + 75)]
                if fall_step is not None:
                    w = w[w.step <= fall_step]
                if len(w) > 2:
                    vz = np.diff(w.root_z.to_numpy()) / 0.02
                    row.update({
                        "dz_body_m": float(w.root_z.iloc[-1] - w.root_z.iloc[0]),
                        "max_rise_mps": float(vz.max()),
                        "max_tilt": float((1 + w.proj_grav_z).max()),
                        "max_tilt_rate": float(np.abs(np.diff((1 + w.proj_grav_z).to_numpy())).max() / 0.02),
                        "min_height_rel": float(w.height_rel.min()),
                        "vx_before_edge": float(g[(g.step >= t - 25) & (g.step < t)].actual_vx.mean()),
                    })
            out.append(row)
    return out


def drift(cases: Path) -> dict:
    res = {}
    for c in FLAT:
        wz = []
        for s in SEEDS:
            a = pd.read_csv(cases / f"seed_{s}" / c / "steps.csv", usecols=["step", "env_id", "actual_wz", "cmd_wz"])
            m = a[(a.step > 50) & (a.cmd_wz.abs() < 1e-9)]
            wz += m.groupby("env_id").actual_wz.mean().tolist()
        wz = np.array(wz)
        res[c] = {"mean_wz": float(wz.mean()), "share_left": float((wz > 0).mean()),
                  "median_abs_wz": float(np.median(np.abs(wz))), "n": int(len(wz))}
    return res


def summarize(df: pd.DataFrame) -> dict:
    out = {"robots": int(len(df)), "fell": int(df.fell.sum()), "reached_edge": int(df.reached_edge.sum()),
           "fell_before_edge": int(df.get("fell_before_edge", pd.Series(dtype=bool)).fillna(False).sum())}
    for grp, sub in (("survived", df[~df.fell & df.reached_edge]), ("fell_after_edge", df[df.fell & df.reached_edge & ~df.fell_before_edge.fillna(False)])):
        out[grp] = {"n": int(len(sub))}
        for k in ("dz_body_m", "max_rise_mps", "max_tilt", "max_tilt_rate", "min_height_rel", "vx_before_edge"):
            if k in sub and len(sub):
                out[grp][k] = float(sub[k].median())
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    res = {"stairs_15_climb": {}, "stairs_10_climb": {}, "flat_drift": {}}
    for arm, cases in ARMS.items():
        for key, case, h in (("stairs_15_climb", "stairs_15_down", 0.15), ("stairs_10_climb", "stairs_10_down", 0.10)):
            df = pd.DataFrame(edge_rows(cases, case, h))
            df.to_csv(a.out / f"{arm}_{case}_edge.csv", index=False, encoding="utf-8")
            res[key][arm] = summarize(df)
        res["flat_drift"][arm] = drift(cases)
    (a.out / "failure_cause.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
