"""G-A083 readout: preregistered std test, G6/15cm secondary, G-A082 protection axes (read-only).

Arms: evaluation/candidate (action_rate_l2 -0.01 on G-A082) and evaluation/g_a082_pc2
(stored G-A082 evaluation, reused without rerun).  Thresholds are copied from
meta/experiment.json "preregistered_predictions"; they are not tuned here.
Score = H1 official-fit formula (tools/go2_weakness_breakdown.py), a sensitivity model,
not an official Go2 score.
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
import go2_g_a082_readout as r82  # noqa: E402
import go2_tfevents_scalars as tfe  # noqa: E402

A082 = ROOT / "workspace/_keep/go2_g_a082_track_ang_vel_z_p0p75"


def std_window(result: Path, lo: int = 2380, hi: int = 2420) -> dict:
    ev = sorted((result / "training/logs").rglob("events.out.tfevents.*"))[-1]
    s = tfe.scalars(str(ev))
    std = s["Policy/mean_std"]
    win = [v for k, v in std.items() if lo <= k <= hi]
    fall = s.get("Episode_Termination/base_contact", {})
    fwin = [v for k, v in fall.items() if lo <= k <= hi]
    return {"mean_std_2380_2420": float(np.mean(win)), "n": len(win),
            "mean_std_last": float(std[max(std)]), "last_iter": int(max(std)),
            "mean_std_iter1000": float(std.get(1000, np.nan)),
            "base_contact_2380_2420": float(np.mean(fwin)) if fwin else None}


def secondary(arm: dict) -> dict:
    df = pd.DataFrame(arm["cases"])
    g6 = df[df.scenario == "G6"]
    s15 = df[df.case.isin(("stairs_15_up", "stairs_15_down"))]
    return {"g6_exy_mean": float(g6.exy_mean.mean()), "g6_rows": int(len(g6)),
            "stairs15_survival_mean": float(s15.survival.mean()), "stairs15_rows": int(len(s15)),
            "stairs15_survival_by_case": s15.groupby("case").survival.mean().to_dict()}


def protection(arm: dict) -> dict:
    full = sum(v["full"] for k, v in arm["stairs"].items() if k.startswith("stairs_15_down|"))
    head = {c: arm["heading"][c]["med"] for c in r82.PRIMARY}
    checks = {
        "heading_each_le_40": all(v <= 40 for v in head.values()),
        "stairs_15_down_full_ge_51": full >= 51,
        "G3_survival_sum_ge_5.75": arm["G3_survival_sum"] >= 5.75,
        "terrain_speed_ge_0.425": arm["terrain_along_speed_mean"] >= 0.425,
        "G2_combined_yaw_all_1": all(v == 1.0 for v in arm["G2_combined_yaw_survival"].values()),
    }
    return {"heading_median": head, "stairs_15_down_full": int(full), "G3_survival_sum": arm["G3_survival_sum"],
            "terrain_along_speed_mean": arm["terrain_along_speed_mean"],
            "G2_combined_yaw_survival": arm["G2_combined_yaw_survival"], "checks": checks,
            "all_held": all(checks.values())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, default=ROOT / "workspace/_keep/go2_g_a083_action_rate_m0p01")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    arms = {"candidate": r82.arm(a.result / "evaluation/candidate/cases"),
            "g_a082_pc2": r82.arm(a.result / "evaluation/g_a082_pc2/cases")}
    std = {"candidate": std_window(a.result), "g_a082_pc2": std_window(A082)}
    m = std["candidate"]["mean_std_2380_2420"]
    out = {
        "primary": {"std": std, "verdict": "SUPPORTED" if m <= 0.80 else "REFUTED" if m >= 0.98 else "INCONCLUSIVE"},
        "secondary": {k: secondary(v) for k, v in arms.items()},
        "protection": {k: protection(v) for k, v in arms.items()},
        "score": {k: {"total_70": v["total_70"], "scenario_score": v["scenario_score"],
                      "loss_survival": v["loss_survival"], "loss_tracking": v["loss_tracking"]}
                  for k, v in arms.items()},
    }
    c = out["secondary"]["candidate"]
    out["secondary"]["verdict"] = {"g6": "SUPPORTED" if c["g6_exy_mean"] <= 0.065 else "NOT_SUPPORTED",
                                   "stairs15": "SUPPORTED" if c["stairs15_survival_mean"] >= 0.92 else "NOT_SUPPORTED"}
    a.out.mkdir(parents=True, exist_ok=True)
    for k, v in arms.items():
        pd.DataFrame(v.pop("cases")).to_csv(a.out / f"{k}_cases.csv", index=False, encoding="utf-8")
    (a.out / "arms.json").write_text(json.dumps(arms, ensure_ascii=False, indent=1), encoding="utf-8")
    (a.out / "readout.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
