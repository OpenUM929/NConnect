"""Search tracking-score formulas that reproduce the H1 official per-scenario scores.

Input: Run06 independent-eval per-step telemetry (3 seeds x 10 cases) and the
user-transcribed official H1 detail table (57.45/70).  Each formula family has ONE
global scale shared by all scenarios -- no per-scenario coefficient, no global ratio.
Validation is leave-one-scenario-out: fit on 6, predict the 7th.

Optional --go2 <eval_root>: apply the selected formula to a Go2 69-case evaluation
(survival_proxy from each case summary, tracking from steps.csv).  The result is a
sensitivity number, not an official Go2 score.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

H1_ROOT = Path("workspace/_keep/train_260831-06_run05cfg_10000_independent_eval/seeds")
SEEDS = ("101", "202", "303")
W = {"H1": .15, "H2": .20, "H3": .10, "H4": .10, "H5": .15, "H6": .15, "H7": .15}
OFFICIAL = {"H1": 8.73, "H2": 11.54, "H3": 5.81, "H4": 5.78, "H5": 8.29, "H6": 8.64, "H7": 8.66}
H1_CASES = {"H1": ["H1_stand"], "H2": ["H2_forward"], "H3": ["H3_left", "H3_right"],
            "H4": ["H4_left", "H4_right"], "H5": ["H5_rough"], "H6": ["H6_minus10", "H6_plus10"],
            "H7": ["H7_push"]}
GO2_W = {"G1": .15, "G2": .15, "G3": .20, "G4": .15, "G5": .15, "G6": .10, "G7": .10}
GRID = np.concatenate([np.linspace(0.01, 0.1, 91), np.linspace(0.1, 3, 291)])
SKIPS = (0, 50)  # 50 steps = first 1 s (start-up transient from standstill)


def load_errors(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = np.genfromtxt(path, delimiter=",", names=True)
    return a["step"], a["error_xy"], a["error_yaw"]


def stat(name: str, s: float, step, exy, eyaw, skip: int) -> float:
    m = step > skip
    exy, eyaw = exy[m], eyaw[m]
    comb = np.sqrt(exy ** 2 + eyaw ** 2)
    e = {"xy": exy, "yaw": eyaw, "comb": comb}
    kind, form = name.split(":")
    if form == "step_exp1":
        return float(np.mean(np.exp(-e[kind] / s)))
    if form == "step_exp2":
        return float(np.mean(np.exp(-(e[kind] / s) ** 2)))
    if form == "mae_exp1":
        return math.exp(-e[kind].mean() / s)
    if form == "rms_exp2":
        return math.exp(-(math.sqrt((e[kind] ** 2).mean()) / s) ** 2)
    if form == "mae_linear":
        return max(0.0, 1 - e[kind].mean() / s)
    if form == "prod_step_exp1":
        return float(np.mean(np.exp(-exy / s)) * np.mean(np.exp(-eyaw / s)))
    if form == "avg_step_exp1":
        return float(0.5 * np.mean(np.exp(-exy / s)) + 0.5 * np.mean(np.exp(-eyaw / s)))
    raise ValueError(name)


FORMULAS = [f"{k}:{f}" for k in ("xy", "yaw", "comb")
            for f in ("step_exp1", "step_exp2", "mae_exp1", "rms_exp2", "mae_linear")]
FORMULAS += ["xy:prod_step_exp1", "xy:avg_step_exp1"]


def h1_scores(data, name, s, skip):
    return {sc: float(np.mean([np.mean([stat(name, s, *data[(sd, c)], skip) for sd in SEEDS])
                               for c in cases])) for sc, cases in H1_CASES.items()}


def loss(r, keys):
    return math.sqrt(np.mean([(70 * W[k] * (r[k] - OFFICIAL[k] / (70 * W[k]))) ** 2 for k in keys]))


def fit_all(data):
    rows = []
    for name in FORMULAS:
        for skip in SKIPS:
            table = {round(float(s), 4): h1_scores(data, name, s, skip) for s in GRID}
            best = min(table, key=lambda s: loss(table[s], W))
            loo = []
            for out in W:
                keys = [k for k in W if k != out]
                s = min(table, key=lambda x: loss(table[x], keys))
                loo.append(70 * W[out] * (table[s][out] - OFFICIAL[out] / (70 * W[out])))
            r = table[best]
            rows.append({"formula": name, "skip_steps": skip, "scale": best,
                         "fit_rmse_points": loss(r, W),
                         "loo_rmse_points": math.sqrt(np.mean(np.square(loo))),
                         "loo_max_abs_points": max(map(abs, loo)),
                         "loo_errors_points": dict(zip(W, loo)),
                         "points": {k: 70 * W[k] * r[k] for k in W},
                         "total": sum(70 * W[k] * r[k] for k in W)})
    rows.sort(key=lambda x: x["loo_rmse_points"])
    loo = []
    for out in W:
        keys = [k for k in W if k != out]
        c = sum(OFFICIAL[k] for k in keys) / sum(70 * W[k] for k in keys)
        loo.append(70 * W[out] * (c - OFFICIAL[out] / (70 * W[out])))
    baseline = {"formula": "single global ratio (rejected method)",
                "loo_rmse_points": math.sqrt(np.mean(np.square(loo))),
                "loo_max_abs_points": max(map(abs, loo))}
    return rows, baseline


def go2_apply(root: Path, name: str, s: float, skip: int) -> dict:
    reg = json.loads(Path("workspace/training/quadruped/config/go2_self_eval_registry.json").read_text(encoding="utf-8"))
    out = {}
    for sc in reg["scenarios"]:
        vals = []
        for case in sc["internal_cases"]:
            for sd in SEEDS:
                cid = f"dr_seed_{sd}" if sc["id"] == "G7" else case
                if sc["id"] == "G7" and case != f"dr_seed_{sd}":
                    continue
                d = root / f"seed_{sd}" / cid
                surv = json.loads((d / "summary.json").read_text(encoding="utf-8"))["survival_proxy"]
                vals.append(surv * stat(name, s, *load_errors(d / "steps.csv"), skip))
        out[sc["id"]] = 70 * GO2_W[sc["id"]] * float(np.mean(vals))
    out["total"] = sum(out[k] for k in GO2_W)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--go2", type=Path, nargs="*", default=[])
    args = ap.parse_args()
    data = {(sd, c): load_errors(H1_ROOT / f"seed_{sd}" / "cases" / c / "steps.csv")
            for sd in SEEDS for cs in H1_CASES.values() for c in cs}
    rows, baseline = fit_all(data)
    result = {"official_h1": OFFICIAL, "identity": "Run06 assumed (UNCONFIRMED_EXTERNAL)",
              "baseline": baseline, "ranked": rows, "go2": {}}
    top = rows[0]
    for root in args.go2:
        result["go2"][str(root)] = go2_apply(root, top["formula"], top["scale"], top["skip_steps"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
