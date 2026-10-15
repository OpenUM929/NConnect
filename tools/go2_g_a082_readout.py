"""G-A082 readout: preregistered heading-change test + protection axes (read-only).

Arms come from the G-A082 result: evaluation/candidate (track_ang_vel_z_exp 0.75)
and evaluation/g_a077_pc2 (matched PC2 G-A077 control, same seed and iter 2400).

Primary metric (preregistered, same code as the G-A077 weakness analysis §4):
  per robot, |sum((actual_wz - cmd_wz) * 0.02)| in degrees over steps > 50, n = 3 seeds x 32.
Preregistered baseline numbers are the server G-A077 medians written in experiment.json;
the matched PC2 control is reported beside them.
Protection axes follow experiment.json "protection".  Score = H1 official-fit formula
(tools/go2_weakness_breakdown.py), a sensitivity model, not an official Go2 score.
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
import go2_climb_count as climb  # noqa: E402
import go2_weakness_breakdown as wb  # noqa: E402

SEEDS = ("101", "202", "303")
HEADING_CASES = ("forward_nominal", "rough_forward", "rough_lateral", "slope_plus_20", "slope_minus_20",
                 "stairs_10_up", "stairs_10_down", "stairs_15_up", "stairs_15_down", "push_pos_x")
PRIMARY = ("slope_plus_20", "stairs_10_down", "stairs_15_down")
TERRAIN = ("G3", "G4", "G5")


def heading(cases: Path, case: str) -> dict:
    hs, slow, tot = [], [], []
    for s in SEEDS:
        a = pd.read_csv(cases / f"seed_{s}" / case / "steps.csv", usecols=["step", "env_id", "actual_wz", "cmd_wz"])
        for _, g in a[a.step > 50].groupby("env_id"):
            w = (g.actual_wz - g.cmd_wz).to_numpy()
            hs.append(abs(np.sum(w) * 0.02) * 180 / np.pi)
            sm = np.convolve(w, np.ones(100) / 100, "same")
            slow.append((sm ** 2).sum())
            tot.append((w ** 2).sum())
    hs = np.array(hs)
    return {"med": float(np.median(hs)), "p90": float(np.percentile(hs, 90)),
            "slow_share": float(sum(slow) / sum(tot)), "gt45": int((hs > 45).sum()), "n": int(len(hs))}


def stairs(cases: Path) -> dict:
    out = {}
    for case, h in climb.STAIR_HEIGHTS.items():
        for s in SEEDS:
            got = climb.count(cases / f"seed_{s}" / case / "steps.csv", h)
            if got is not None:
                out[f"{case}|{s}"] = {k: got[k] for k in ("direction", "robots", "ge1", "ge2", "full")}
    return out


def arm(cases: Path) -> dict:
    df = wb.run(cases)
    sc = df.groupby("scenario").case_score.mean()
    terr = df[df.scenario.isin(TERRAIN)]
    g2 = df[df.case.str.startswith("combined_yaw")]
    yaw_rmse = {}
    for _, r in g2.iterrows():
        s = json.loads((cases / f"seed_{r.seed}" / r.case / "summary.json").read_text(encoding="utf-8"))
        yaw_rmse[f"{r.case}|{r.seed}"] = s["tracking_yaw_rmse"]
    return {
        "heading": {c: heading(cases, c) for c in HEADING_CASES},
        "stairs": stairs(cases),
        "scenario_score": {k: float(v) for k, v in sc.items()},
        "total_70": float(sum(70 * wb.W[k] * v for k, v in sc.items())),
        "loss_survival": float(df.loss_survival.sum()), "loss_tracking": float(df.loss_tracking.sum()),
        "loss_tracking_yaw_part": float(df.loss_tracking_yaw_part.sum()),
        "G3_survival_sum": float(df[df.scenario == "G3"].survival.sum()),
        "G3_cases": int((df.scenario == "G3").sum()),
        "terrain_along_speed_mean": float(terr.along_speed.mean()),
        "G2_combined_yaw_survival": {f"{r.case}|{r.seed}": float(r.survival) for _, r in g2.iterrows()},
        "G2_combined_yaw_rmse": yaw_rmse,
        "cases": df.to_dict("records"),
    }


def verdict(cand: dict, base_vals: dict) -> str:
    ratios = [cand[c]["med"] / base_vals[c] for c in PRIMARY]
    if all(r < 0.5 for r in ratios):
        return "SUPPORTED"
    if not any(r < 0.8 for r in ratios):
        return "REFUTED"
    return "INCONCLUSIVE"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, default=ROOT / "workspace/_keep/go2_g_a082_track_ang_vel_z_p0p75")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    exp = json.loads((a.result / "meta/experiment.json").read_text(encoding="utf-8"))
    prereg = exp["preregistered_predictions"]["primary"]["cases"]
    res = {"candidate": arm(a.result / "evaluation/candidate/cases"),
           "g_a077_pc2": arm(a.result / "evaluation/g_a077_pc2/cases")}
    pc2 = {c: res["g_a077_pc2"]["heading"][c]["med"] for c in PRIMARY}
    res["primary"] = {
        "prereg_baseline_server_g_a077": prereg,
        "matched_pc2_g_a077": pc2,
        "candidate": {c: res["candidate"]["heading"][c]["med"] for c in PRIMARY},
        "verdict_vs_prereg_numbers": verdict(res["candidate"]["heading"], prereg),
        "verdict_vs_matched_pc2": verdict(res["candidate"]["heading"], pc2),
    }
    a.out.mkdir(parents=True, exist_ok=True)
    for k in ("candidate", "g_a077_pc2"):
        pd.DataFrame(res[k].pop("cases")).to_csv(a.out / f"{k}_cases.csv", index=False, encoding="utf-8")
    (a.out / "readout.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res["primary"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
