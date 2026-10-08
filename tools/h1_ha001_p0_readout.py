"""H-A001 P0 readout: verified highest test command and branch, per §12 of
workspace/training/humanoid/upload/plan/H1_STABLE_SPEED_TUNING_DEBATE_20261008.md.

Read-only. Usage: python -I tools/h1_ha001_p0_readout.py <KEEP dir H_A001_P0_SPEED_GRID> [--out DIR]
Window: t >= 2 s, rows up to and including the first termination row per env are excluded after it.
Fall = terminated row (base_contact) or root_z < 0.55 m for >= 25 consecutive steps (0.5 s).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEEDS = (101, 202, 303)
POLICIES = ("run06", "run05")
WINDOW_S = 2.0
FALL_Z, FALL_STEPS = 0.55, 25
RATIO_LO, RATIO_HI, RMSE_TOL, STRONG = 0.95, 1.05, 1.05, 1.20
FAMILIES = {  # family -> (reference case, ordered higher cases); turn families need L and R
    "plane": ("plane_vx0p75", ["plane_vx1p00", "plane_vx1p25"]),
    "rough": ("rough_vx0p75", ["rough_vx1p00"]),
    "turn": ("turn_vx0p50", ["turn_vx1p00"]),
}
CMD_VX = {"plane_vx0p75": .75, "plane_vx1p00": 1.0, "plane_vx1p25": 1.25, "rough_vx0p75": .75,
          "rough_vx1p00": 1.0, "turn_vx0p50": .5, "turn_vx1p00": 1.0}


def case_metrics(steps_csv: Path) -> dict:
    d = pd.read_csv(steps_csv)
    falls = 0
    keep = []
    for _, s in d.groupby("env_id", sort=True):
        s = s.sort_values("step")
        term = s.index[(s["terminated"] == 1) | (s["truncated"] == 1)]
        end = s.index.get_loc(term[0]) if len(term) else len(s)
        died = bool(len(term)) and int(s.loc[term[0], "terminated"]) == 1
        low = (s["root_z"].to_numpy()[:end] < FALL_Z).astype(int)
        run = best = 0
        for v in low:
            run = run + 1 if v else 0
            best = max(best, run)
        falls += int(died or best >= FALL_STEPS)
        keep.append(s.iloc[:end])
    w = pd.concat(keep)
    w = w[w["time_s"] >= WINDOW_S]
    cmd_vx = float(w["cmd_vx"].iloc[0])
    return {
        "envs": int(d["env_id"].nunique()), "falls": falls,
        "vx_ratio": float(w["actual_vx"].mean() / cmd_vx) if cmd_vx else None,
        "xy_rmse": float(np.sqrt((w["error_xy"] ** 2).mean())),
        "yaw_rmse": float(np.sqrt((w["error_yaw"] ** 2).mean())),
    }


def load(keep: Path) -> dict:
    out = {}
    for p in POLICIES:
        for seed in SEEDS:
            for f in sorted((keep / "cases" / p / f"seed_{seed}").glob("*/steps.csv")):
                out[(p, seed, f.parent.name)] = case_metrics(f)
    return out


def _sides(family: str, case: str) -> list[str]:
    return [f"{case}_L", f"{case}_R"] if family == "turn" else [case]


def judge(m: dict, policy: str) -> dict:
    res = {}
    for fam, (ref, highers) in FAMILIES.items():
        rows, verified, branch_hint = [], None, None
        ref_ok = all(m[(policy, s, c)]["falls"] == 0 and RATIO_LO <= m[(policy, s, c)]["vx_ratio"] <= RATIO_HI
                     for s in SEEDS for c in _sides(fam, ref))
        if ref_ok:
            verified = CMD_VX[ref]
        for case in highers:
            per = []
            for s in SEEDS:
                for side_ref, side in zip(_sides(fam, ref), _sides(fam, case)):
                    r, h = m[(policy, s, side_ref)], m[(policy, s, side)]
                    per.append({
                        "seed": s, "case": side, "falls": h["falls"], "vx_ratio": h["vx_ratio"],
                        "xy_rel": h["xy_rmse"] / r["xy_rmse"], "yaw_rel": h["yaw_rmse"] / r["yaw_rmse"],
                    })
            ratio_ok = all(RATIO_LO <= x["vx_ratio"] <= RATIO_HI for x in per)
            falls0 = all(x["falls"] == 0 for x in per)
            xy_ok = all(x["xy_rel"] <= RMSE_TOL for x in per)
            yaw_ok = all(x["yaw_rel"] <= RMSE_TOL for x in per)
            passed = ratio_ok and falls0 and xy_ok and yaw_ok
            rows.append({"case": case, "pass": passed, "ratio_ok": ratio_ok, "falls0": falls0,
                         "xy_ok": xy_ok, "yaw_ok": yaw_ok,
                         "strong_worsening": any(max(x["xy_rel"], x["yaw_rel"]) > STRONG for x in per),
                         "per_seed": per})
            if passed and verified == CMD_VX[ref if case == highers[0] else highers[highers.index(case) - 1]]:
                verified = CMD_VX[case]
            elif not passed and branch_hint is None:
                slow = any(x["vx_ratio"] < RATIO_LO for x in per)
                if not falls0:
                    branch_hint = "iv_REJUDGE" if slow else "FALLS"
                elif slow and yaw_ok:
                    branch_hint = "i_A_lin_vel"
                elif ratio_ok and not yaw_ok:
                    branch_hint = "ii_B_action_rate"
                else:
                    branch_hint = "REJUDGE"
        res[fam] = {"reference_ok": ref_ok, "verified_highest_vx": verified,
                    "first_failure_branch": branch_hint, "cases": rows}
    hints = {v["first_failure_branch"] for v in res.values() if v["first_failure_branch"]}
    if not hints and all(v["reference_ok"] for v in res.values()):
        branch = "iii_KEEP_RUN06_UPPER_UNKNOWN"
    elif len(hints) == 1 and hints <= {"i_A_lin_vel", "ii_B_action_rate"}:
        branch = hints.pop()
    else:
        branch = "iv_REJUDGE"
    return {"branch": branch, "families": res}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("keep", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    m = load(a.keep)
    out = a.out or a.keep / "readout"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"policy": p, "seed": s, "case": c, **v} for (p, s, c), v in sorted(m.items())]) \
        .to_csv(out / "P0_CASES.csv", index=False)
    summary = {p: judge(m, p) for p in POLICIES}
    summary["branch_decision_policy"] = "run06"
    summary["branch"] = summary["run06"]["branch"]
    (out / "P0_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for p in POLICIES:
        print(p, summary[p]["branch"],
              {f: v["verified_highest_vx"] for f, v in summary[p]["families"].items()})


if __name__ == "__main__":
    main()
