"""G-A086 fall-cause check against G-A083 (read-only, evaluation steps.csv only).

Question: why did G-A086 fall more in evaluation (12 -> 16), with stairs_15_down 2 -> 6,
rough_lateral 1 -> 5, DR 1 -> 4, while push falls went 4 -> 0?
1. Stair climb (stairs_15_down / stairs_10_down = climbing up): first-step edge window, reusing
   tools/go2_g_a084_failure_cause.py edge_rows/summarize unchanged.
2. Per fallen robot in every case: the 1 s before the posture-gate fall step (upright == 0 after
   step 25): mean along-command speed, body height above terrain, tilt (1 + proj_grav_z), and the
   fall kind at the fall step (same rule as go2_weakness_breakdown: tilt if proj_grav_z > -0.5,
   low if height_rel < 0.18).
3. Per case, all robots after step 50: median height_rel, median tilt, robots that ever went
   below height_rel 0.18.
Roll and pitch are not separable in steps.csv (only proj_grav_z).  Run from the repository root.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_g_a084_failure_cause as fc  # noqa: E402

ARMS = {"g_a083": ROOT / "workspace/_keep/go2_g_a083_action_rate_m0p01/evaluation/candidate/cases",
        "g_a086": ROOT / "workspace/_keep/go2_g_a086_action_rate_m0p0125_flat_m0p23/evaluation/candidate/cases"}
CASES = ("rough_forward", "rough_lateral", "stairs_10_down", "stairs_15_down", "stairs_15_up",
         "slope_plus_20", "forward_nominal", "forward_slow", "push_neg_x", "push_pos_x",
         "push_neg_y", "push_pos_y", "dr_seed_101", "dr_seed_202", "dr_seed_303")
COLS = ["step", "env_id", "cmd_vx", "cmd_vy", "actual_vx", "actual_vy", "proj_grav_z",
        "height_rel", "upright"]


def seeds_for(case: str) -> tuple[str, ...]:
    return (case.rsplit("_", 1)[1],) if case.startswith("dr_seed_") else fc.SEEDS


def case_rows(cases: Path, case: str) -> tuple[dict, list[dict]]:
    h, t, ever, n, falls = [], [], 0, 0, []
    for s in seeds_for(case):
        a = pd.read_csv(cases / f"seed_{s}" / case / "steps.csv", usecols=COLS)
        m = a[a.step > 50]
        h.append(float(m.height_rel.median()))
        t.append(float((1 + m.proj_grav_z).median()))
        mn = m.groupby("env_id").height_rel.min()
        ever += int((mn < 0.18).sum())
        n += len(mn)
        for env, g in a.groupby("env_id"):
            g = g.sort_values("step")
            bad = g[(g.step > 25) & (g.upright == 0)]
            if not len(bad):
                continue
            r = bad.iloc[0]
            f = int(r.step)
            kind = "tilt" if r.proj_grav_z > -0.5 else ("low" if r.height_rel < 0.18 else "other")
            if r.proj_grav_z > -0.5 and r.height_rel < 0.18:
                kind = "tilt+low"
            w = g[(g.step >= f - 50) & (g.step < f)]
            cn = np.hypot(w.cmd_vx, w.cmd_vy)
            along = np.where(cn > 1e-6, (w.actual_vx * w.cmd_vx + w.actual_vy * w.cmd_vy) / np.where(cn > 1e-6, cn, 1), np.nan)
            falls.append({"case": case, "seed": s, "env": int(env), "fall_step": f, "kind": kind,
                          "along_1s_before": float(np.nanmean(along)) if np.isfinite(along).any() else None,
                          "height_1s_before": float(w.height_rel.mean()) if len(w) else None,
                          "tilt_1s_before_max": float((1 + w.proj_grav_z).max()) if len(w) else None})
    return ({"height_med": float(np.mean(h)), "tilt_med": float(np.mean(t)),
             "robots_ever_below_0.18": ever, "robots": n}, falls)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    res = {"stairs_15_climb": {}, "stairs_10_climb": {}, "posture": {}, "falls_by_kind": {}}
    for arm, cases in ARMS.items():
        for key, case, h in (("stairs_15_climb", "stairs_15_down", 0.15), ("stairs_10_climb", "stairs_10_down", 0.10)):
            df = pd.DataFrame(fc.edge_rows(cases, case, h))
            df.to_csv(a.out / f"{arm}_{case}_edge.csv", index=False, encoding="utf-8")
            res[key][arm] = fc.summarize(df)
        allf, post = [], {}
        for c in CASES:
            post[c], f = case_rows(cases, c)
            allf += f
        res["posture"][arm] = post
        fdf = pd.DataFrame(allf)
        fdf.to_csv(a.out / f"{arm}_falls.csv", index=False, encoding="utf-8")
        res["falls_by_kind"][arm] = fdf.groupby(["case", "kind"]).size().to_dict() if len(fdf) else {}
        res["falls_by_kind"][arm] = {f"{k[0]}|{k[1]}": int(v) for k, v in res["falls_by_kind"][arm].items()}
    (a.out / "fall_cause.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
