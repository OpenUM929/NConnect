"""action_rate_l2 three-point saturation estimate on one baseline (read-only).

Points (same rewards except action_rate_l2; P0 = A048 rewards, train seed 42, PC2):
  -0.005  G-A063 s13      -0.01  P0 (a048_seed42, parent of both)      -0.02  G-A063 s12
Values are the stored readouts reports/evidence/go2_pc2_tree_readout/{s13,s12}_*.json
(counts summed over eval seeds 101/202/303, rates averaged) and the legacy /70 proxy from
reports/evidence/go2_g_a063_s_analysis_20261005 and the s12/s13 readouts.
A quadratic through three points has no error estimate; a vertex outside [-0.02, -0.005]
or a monotonic series means no interior saturation point.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "workspace/training/quadruped/reports/evidence/go2_pc2_tree_readout"
X = np.array([-0.005, -0.01, -0.02])
PROXY = {"legacy_proxy_70": [44.47, 46.77, 31.28]}  # s13 / P0 / s12 readouts (GO2_G_A063_S1{3,2}_READOUT)


def agg(v: dict) -> float:
    vals = [v[s]["rmse"] if isinstance(v[s], dict) else v[s] for s in ("101", "202", "303")]
    return float(np.sum(vals)) if all(isinstance(t, int) for t in vals) else float(np.mean(vals))


def fit(y: list[float]) -> dict:
    y = np.asarray(y, float)
    c = np.polyfit(X, y, 2)
    mono = bool(np.all(np.diff(y) >= 0) or np.all(np.diff(y) <= 0))
    xv = float(-c[1] / (2 * c[0])) if c[0] != 0 else None
    inside = xv is not None and -0.02 <= xv <= -0.005 and not mono
    return {"y": y.tolist(), "vertex": xv if inside else None, "kind": "min" if c[0] > 0 else "max",
            "vertex_value": float(np.polyval(c, xv)) if inside else None,
            "monotonic": mono,
            "pred": {str(v): float(np.polyval(c, v)) for v in (-0.0075, -0.0125, -0.015)}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    s13 = json.loads((EV / "s13_action_rate_l2_m0p005.json").read_text(encoding="utf-8"))["values"]
    s12 = json.loads((EV / "s12_action_rate_l2_m0p02.json").read_text(encoding="utf-8"))["values"]
    res = {}
    for k in s13:
        try:
            p, p2 = agg(s13[k]["parent"]), agg(s12[k]["parent"])
        except (KeyError, TypeError):
            continue
        assert abs(p - p2) < 1e-9, k  # both points share the same parent
        y = [agg(s13[k]["point"]), p, agg(s12[k]["point"])]
        if np.ptp(y) == 0:
            continue
        res[k] = fit(y)
    for k, y in PROXY.items():
        res[k] = fit(y)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "action_rate_saturation.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, r in res.items():
        v = f"{r['vertex']:+.4f} {r['kind']}" if r["vertex"] is not None else ("monotonic" if r["monotonic"] else "outside")
        print(f"{k:38s} {r['y'][0]:8.3f} {r['y'][1]:8.3f} {r['y'][2]:8.3f}  vertex {v}")


if __name__ == "__main__":
    main()
