"""G-A086 readout: preregistered tracking-loss test, push/DR/15cm secondary, protection (read-only).

Arms: evaluation/candidate (action_rate_l2 -0.0125 + flat_orientation_l2 -0.23 on G-A083) and the
G-A083 PC2 evaluation (reused without rerun).  The reused baseline is read from the local G-A083
result (evaluation/candidate); the copy inside the G-A086 result was hash-compared file by file at
fetch time instead of extracted (380/380 identical).  Thresholds are copied from
meta/experiment.json "preregistered_predictions".  The two value changes are judged together;
this tool does not split their effects.  Score = H1 official-fit formula
(tools/go2_weakness_breakdown.py) and the legacy /70 proxy (go2_fixed_eval_report); neither is an
official Go2 score.  Run from the repository root.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "workspace/training/quadruped"))
import go2_g_a082_readout as r82  # noqa: E402
import go2_g_a083_readout as r83  # noqa: E402
import go2_g_a084_readout as r84  # noqa: E402
import go2_fixed_eval_report as fr  # noqa: E402

A083 = ROOT / "workspace/_keep/go2_g_a083_action_rate_m0p01"
REG = ROOT / "workspace/training/quadruped/config/go2_self_eval_registry.json"


def prereg(arm: dict) -> dict:
    df = pd.DataFrame(arm["cases"])
    g6, g7 = df[df.scenario == "G6"], df[df.scenario == "G7"]
    s15d = df[df.case == "stairs_15_down"]
    return {"loss_tracking_sum": float(df.loss_tracking.sum()), "rows": int(len(df)),
            "push_falls_G6": int(g6.fallen_envs.sum()), "g6_rows": int(len(g6)),
            "dr_survival_loss_G7": float(g7.loss_survival.sum()), "g7_rows": int(len(g7)),
            "stairs_15_down_falls": int(s15d.fallen_envs.sum()), "s15d_rows": int(len(s15d)),
            "loss_tracking_by_scenario": df.groupby("scenario").loss_tracking.sum().to_dict(),
            "loss_survival_by_scenario": df.groupby("scenario").loss_survival.sum().to_dict()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, default=ROOT / "workspace/_keep/go2_g_a086_action_rate_m0p0125_flat_m0p23")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    roots = {"candidate": a.result / "evaluation/candidate", "g_a083_pc2": A083 / "evaluation/candidate"}
    arms = {k: r82.arm(v / "cases") for k, v in roots.items()}
    std = {"candidate": r83.std_window(a.result), "g_a083_pc2": r83.std_window(A083)}
    ex = {k: r84.extra(v) for k, v in arms.items()}
    pr = {k: prereg(v) for k, v in arms.items()}
    prot = {}
    for k, v in arms.items():
        head = {c: v["heading"][c]["med"] for c in r82.PRIMARY}
        checks = {
            "stairs_10_down_full_ge_85": ex[k]["stairs_full"]["stairs_10_down"] >= 85,
            "stairs_15_down_full_ge_85": ex[k]["stairs_full"]["stairs_15_down"] >= 85,
            "stairs15_survival_ge_0.92": ex[k]["stairs15_survival_mean"] >= 0.92,
            "heading_each_le_40": all(h <= 40 for h in head.values()),
            "G3_survival_sum_ge_5.75": v["G3_survival_sum"] >= 5.75,
            "terrain_speed_ge_0.425": v["terrain_along_speed_mean"] >= 0.425,
            "G2_combined_yaw_all_1": all(s == 1.0 for s in v["G2_combined_yaw_survival"].values()),
            "policy_std_le_0.98": std[k]["mean_std_2380_2420"] <= 0.98,
        }
        prot[k] = {"heading_median": head, "stairs_full": ex[k]["stairs_full"],
                   "stairs15_survival_mean": ex[k]["stairs15_survival_mean"],
                   "G3_survival_sum": v["G3_survival_sum"],
                   "terrain_along_speed_mean": v["terrain_along_speed_mean"],
                   "policy_std_2380_2420": std[k]["mean_std_2380_2420"],
                   "checks": checks, "all_held": all(checks.values())}
    c = pr["candidate"]
    lt = c["loss_tracking_sum"]
    out = {
        "primary": {"loss_tracking_sum": {k: p["loss_tracking_sum"] for k, p in pr.items()},
                    "verdict": "SUPPORTED" if lt <= 11.0 else "REFUTED" if lt >= 11.59 else "INCONCLUSIVE"},
        "secondary": {
            "push_falls_G6": {k: p["push_falls_G6"] for k, p in pr.items()},
            "push_verdict": "SUPPORTED" if c["push_falls_G6"] <= 2 else "NOT_SUPPORTED",
            "dr_survival_loss_G7": {k: p["dr_survival_loss_G7"] for k, p in pr.items()},
            "dr_verdict": "SUPPORTED" if c["dr_survival_loss_G7"] <= 0.10 else "NOT_SUPPORTED",
            "stairs_15_down_falls": {k: p["stairs_15_down_falls"] for k, p in pr.items()},
            "stairs15_verdict": "SUPPORTED" if c["stairs_15_down_falls"] <= 2 else "NOT_SUPPORTED",
            "training_base_contact_2380_2420": {k: s["base_contact_2380_2420"] for k, s in std.items()},
        },
        "protection": prot,
        "prereg_detail": pr,
        "std": std,
        "extra": ex,
        "score": {k: {"formula_total_70": v["total_70"], "scenario_score": v["scenario_score"],
                      "loss_survival": v["loss_survival"], "loss_tracking": v["loss_tracking"],
                      "legacy_proxy_70": fr.build_policy(roots[k], REG)["simulation_points_70"]}
                  for k, v in arms.items()},
    }
    a.out.mkdir(parents=True, exist_ok=True)
    for k, v in arms.items():
        pd.DataFrame(v.pop("cases")).to_csv(a.out / f"{k}_cases.csv", index=False, encoding="utf-8")
    (a.out / "arms.json").write_text(json.dumps(arms, ensure_ascii=False, indent=1), encoding="utf-8")
    (a.out / "readout.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("primary", "secondary", "protection", "score")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
