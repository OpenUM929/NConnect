"""Per-case weakness breakdown of a Go2 69-case evaluation (read-only).

Score model: H1 official-fit formula (tools/h1_official_formula_fit.py, rank 1):
  tracking = mean_t exp(-sqrt(e_xy^2 + e_yaw^2) / 0.70), first 50 steps excluded
  case = survival_proxy (posture_gate_v2) * tracking; scenario = mean over cases/seeds
Point loss is split into survival loss 70w(1-s) and tracking loss 70w*s*(1-t);
tracking loss is further split into the part removed if yaw error were zero.
This is a sensitivity model, not an official Go2 score.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

SCALE, SKIP = 0.70, 50
W = {"G1": .15, "G2": .15, "G3": .20, "G4": .15, "G5": .15, "G6": .10, "G7": .10}
SEEDS = ("101", "202", "303")
COLS = ["step", "env_id", "cmd_vx", "cmd_vy", "cmd_wz", "actual_vx", "actual_vy", "actual_wz",
        "error_xy", "error_yaw", "proj_grav_z", "height_rel", "upright", "terminated"]


def case_row(d: Path, scen: str, case: str, seed: str) -> dict:
    s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    a = pd.read_csv(d / "steps.csv", usecols=COLS)
    m = a[a.step > SKIP]
    exy, eyaw = m.error_xy.to_numpy(), m.error_yaw.to_numpy()
    t = float(np.mean(np.exp(-np.sqrt(exy ** 2 + eyaw ** 2) / SCALE)))
    t_noyaw = float(np.mean(np.exp(-exy / SCALE)))
    cvx, cvy = m.cmd_vx.to_numpy(), m.cmd_vy.to_numpy()
    cn = np.hypot(cvx, cvy)
    along = np.where(cn > 1e-6, (m.actual_vx * cvx + m.actual_vy * cvy) / np.where(cn > 1e-6, cn, 1), np.nan)
    perp = np.where(cn > 1e-6, (m.actual_vy * cvx - m.actual_vx * cvy) / np.where(cn > 1e-6, cn, 1), m.actual_vy)
    falls = []
    for env, g in a.groupby("env_id"):
        bad = g[(g.step > 25) & (g.upright == 0)]
        if len(bad):
            r = bad.iloc[0]
            kind = "tilt" if r.proj_grav_z > -0.5 else ("low" if r.height_rel < 0.18 else "other")
            if r.proj_grav_z > -0.5 and r.height_rel < 0.18:
                kind = "tilt+low"
            falls.append((int(r.step), kind))
    surv = float(s["survival_proxy"])
    return {
        "scenario": scen, "case": case, "seed": seed, "survival": surv, "tracking": t,
        "case_score": surv * t, "tracking_if_no_yaw": t_noyaw,
        "cmd_speed": float(np.nanmean(cn)), "cmd_wz": float(m.cmd_wz.mean()),
        "along_speed": float(np.nanmean(along)) if np.isfinite(along).any() else None,
        "lateral_drift": float(np.mean(perp)), "actual_wz": float(m.actual_wz.mean()),
        "exy_mean": float(exy.mean()), "eyaw_mean": float(eyaw.mean()),
        "fallen_envs": int(s.get("fallen_env_count", 0)), "terminated_envs": int(s.get("terminated_env_count", 0)),
        "fall_kinds": ",".join(sorted({k for _, k in falls})) if falls else "",
        "fall_tilt": sum(1 for _, k in falls if "tilt" in k), "fall_low_only": sum(1 for _, k in falls if k == "low"),
        "fall_step_median": float(np.median([f for f, _ in falls])) if falls else None,
        "height_rel_p10": s.get("height_rel_p10"), "progress_m": s.get("projected_progress_m"),
        "recovery_upright": (s.get("recovery") or {}).get("recovery_rate_upright"),
    }


def run(root: Path) -> pd.DataFrame:
    reg = json.loads(Path("workspace/training/quadruped/config/go2_self_eval_registry.json").read_text(encoding="utf-8"))
    rows = []
    for sc in reg["scenarios"]:
        for case in sc["internal_cases"]:
            for seed in SEEDS:
                if sc["id"] == "G7" and case != f"dr_seed_{seed}":
                    continue
                rows.append(case_row(root / f"seed_{seed}" / case, sc["id"], case, seed))
    df = pd.DataFrame(rows)
    df["w"] = df.scenario.map(W)
    n = df.groupby("scenario").case.transform("size")
    df["loss_survival"] = 70 * df.w * (1 - df.survival) / n
    df["loss_tracking"] = 70 * df.w * df.survival * (1 - df.tracking) / n
    df["loss_tracking_yaw_part"] = 70 * df.w * df.survival * (df.tracking_if_no_yaw - df.tracking) / n
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    df = run(a.root)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
