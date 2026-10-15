"""G-A084 readout: preregistered G6 xy test, tilt-falls / training-fall secondary, protection (read-only).

Arms: evaluation/candidate (ang_vel_xy_l2 -0.065 on G-A083) and the G-A083 PC2 evaluation
(reused without rerun).  The reused baseline is read from the local G-A083 result
(evaluation/candidate); the copy inside the G-A084 result was hash-compared file by file
at fetch time instead of extracted (370/370 data files identical, videos not compared).
Thresholds are copied from meta/experiment.json "preregistered_predictions"; the one
correction (tilt_falls_G3_G6 reference 9, not 7; GO2_G_A084_PLAN §4) changes only the
reference shown, not the threshold.  Score = H1 official-fit formula
(tools/go2_weakness_breakdown.py) and the legacy /70 proxy (go2_fixed_eval_report);
neither is an official Go2 score.  Run from the repository root.
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
import go2_fixed_eval_report as fr  # noqa: E402

A083 = ROOT / "workspace/_keep/go2_g_a083_action_rate_m0p01"
REG = ROOT / "workspace/training/quadruped/config/go2_self_eval_registry.json"


def extra(arm: dict) -> dict:
    df = pd.DataFrame(arm["cases"])
    g6 = df[df.scenario == "G6"]
    g36 = df[df.scenario.isin(("G3", "G6"))]
    s15 = df[df.case.isin(("stairs_15_up", "stairs_15_down"))]
    full = {c: int(sum(v["full"] for k, v in arm["stairs"].items() if k.startswith(c + "|")))
            for c in ("stairs_10_down", "stairs_15_down")}
    return {
        "g6_exy_mean": float(g6.exy_mean.mean()), "g6_rows": int(len(g6)),
        "g6_exy_by_case": g6.groupby("case").exy_mean.mean().to_dict(),
        "tilt_falls_G3_G6": int(g36.fall_tilt.sum()), "g3_g6_rows": int(len(g36)),
        "tilt_falls_by_case": {k: int(v) for k, v in g36.groupby("case").fall_tilt.sum().items() if v},
        "stairs_full": full,
        "stairs15_survival_mean": float(s15.survival.mean()),
        "fallen_envs_total": int(df.fallen_envs.sum()),
        "fallen_by_case": {f"{r.case}|{r.seed}": int(r.fallen_envs) for _, r in df.iterrows() if r.fallen_envs},
        "survival_by_case": df.groupby("case").survival.mean().to_dict(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, default=ROOT / "workspace/_keep/go2_g_a084_ang_vel_xy_m0p065")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    roots = {"candidate": a.result / "evaluation/candidate", "g_a083_pc2": A083 / "evaluation/candidate"}
    arms = {k: r82.arm(v / "cases") for k, v in roots.items()}
    std = {"candidate": r83.std_window(a.result), "g_a083_pc2": r83.std_window(A083)}
    ex = {k: extra(v) for k, v in arms.items()}
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
        prot[k] = {"heading_median": head, "G3_survival_sum": v["G3_survival_sum"],
                   "terrain_along_speed_mean": v["terrain_along_speed_mean"],
                   "checks": checks, "all_held": all(checks.values())}
    c = ex["candidate"]
    bc = std["candidate"]["base_contact_2380_2420"]
    out = {
        "primary": {"g6_exy_mean": {k: e["g6_exy_mean"] for k, e in ex.items()},
                    "verdict": "SUPPORTED" if c["g6_exy_mean"] <= 0.065
                    else "REFUTED" if c["g6_exy_mean"] >= 0.075 else "INCONCLUSIVE"},
        "secondary": {
            "tilt_falls_G3_G6": {k: e["tilt_falls_G3_G6"] for k, e in ex.items()},
            "tilt_verdict": "SUPPORTED" if c["tilt_falls_G3_G6"] <= 3 else "NOT_SUPPORTED",
            "tilt_reference_note": "prereg wrote G-A083=7; corrected reference is 9 (all 18 G3/G6 rows, recovered robots included)",
            "training_base_contact_2380_2420": {k: s["base_contact_2380_2420"] for k, s in std.items()},
            "base_contact_verdict": "SUPPORTED" if bc is not None and bc <= 0.17 else "NOT_SUPPORTED",
        },
        "protection": prot,
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
