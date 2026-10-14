"""Over-correction vs under-correction vs gait rhythm in Go2 body yaw-rate (read-only).

Per case, from steps.csv (50 Hz, cmd_wz = 0 cases only):
  * event-triggered response: local |wz| peaks above the case p95 (>=0.5 s apart),
    sign-normalised, averaged over the next 1.5 s.  Overshoot = -min / peak.
    Large overshoot with a fast zero crossing = under-damped loop (over-correction
    candidate); slow monotone decay without overshoot = under-correction.
  * spectrum of wz vs spectrum of root_z (gait rhythm reference).
  * autocorrelation first zero crossing and negative lobe depth.
  * event-aligned tilt (proj_grav_z) and height change before the peak: was the
    peak preceded by an external-looking disturbance?
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

DT = 0.02
SEEDS = ("101", "202", "303")
CASES = ["forward_nominal", "forward_slow", "backward", "left", "rough_forward", "rough_lateral",
         "slope_plus_20", "slope_minus_20", "stairs_10_up", "stairs_10_down", "stairs_15_up",
         "stairs_15_down", "push_pos_x", "push_pos_y", "dr_seed_101"]
POST, PRE = 75, 25  # 1.5 s after, 0.5 s before


def series(root: Path, case: str):
    out = []
    for s in SEEDS:
        p = root / f"seed_{s}" / case / "steps.csv"
        if not p.exists():
            continue
        a = pd.read_csv(p, usecols=["step", "env_id", "actual_wz", "proj_grav_z", "root_z", "upright"])
        for _, g in a[a.step > 50].groupby("env_id"):
            g = g.sort_values("step")
            if len(g) > 300 and g.upright.all():
                out.append((g.actual_wz.to_numpy(), g.proj_grav_z.to_numpy(), g.root_z.to_numpy()))
    return out


def analyse(envs) -> dict:
    allw = np.concatenate([w for w, _, _ in envs])
    thr = np.percentile(np.abs(allw), 95)
    resp, tilt, dz = [], [], []
    for w, gz, z in envs:
        aw = np.abs(w)
        last = -999
        for i in range(PRE, len(w) - POST):
            if aw[i] >= thr and aw[i] == aw[i - 2:i + 3].max() and i - last >= 25:
                sg = np.sign(w[i])
                resp.append(sg * w[i - PRE:i + POST] / aw[i])
                tilt.append(gz[i - PRE:i + POST] - gz[i - PRE])
                dz.append(z[i - PRE:i + POST] - z[i - PRE])
                last = i
    r = np.mean(resp, axis=0)
    after = r[PRE:]
    zc = np.where(after <= 0)[0]
    first_zero_s = float(zc[0] * DT) if len(zc) else None
    overshoot = float(-after.min())
    t_min = float(np.argmin(after) * DT)
    half = np.where(after <= 0.5)[0]
    # spectra
    def spec(xs):
        n = min(len(x) for x in xs)
        n = 2 ** int(np.log2(n))
        f = np.fft.rfftfreq(n, DT)
        P = np.mean([np.abs(np.fft.rfft((x[:n] - x[:n].mean()) * np.hanning(n))) ** 2 for x in xs], axis=0)
        return f, P
    f, Pw = spec([w for w, _, _ in envs])
    _, Pz = spec([z for _, _, z in envs])
    band = lambda P, lo, hi: float(P[(f >= lo) & (f < hi)].sum() / P[f > 0.05].sum())
    fz = float(f[1:][np.argmax(Pz[1:] * (f[1:] > 0.8))])
    fw = float(f[1:][np.argmax(Pw[1:])])
    # autocorrelation
    ac = []
    for w, _, _ in envs:
        x = w - w.mean()
        c = np.correlate(x, x, "full")[len(x) - 1:len(x) + 100]
        ac.append(c / c[0])
    ac = np.mean(ac, axis=0)
    acz = np.where(ac <= 0)[0]
    return {
        "envs": len(envs), "events": len(resp), "peak_threshold_rad_s": float(thr),
        "wz_std": float(allw.std()),
        "resp_first_zero_s": first_zero_s, "resp_overshoot_ratio": overshoot, "resp_min_at_s": t_min,
        "resp_half_decay_s": float(half[0] * DT) if len(half) else None,
        "resp_at": {f"{k*DT:.2f}s": float(after[k]) for k in (5, 10, 15, 25, 40, 60)},
        "resp_before_peak_0.2s": float(r[PRE - 10]),
        "tilt_change_before_peak": float(np.mean(tilt, axis=0)[PRE] ),
        "height_change_before_peak_m": float(np.mean(dz, axis=0)[PRE]),
        "wz_dominant_hz": fw, "gait_hz_from_root_z": fz,
        "wz_power_lt1hz": band(Pw, 0.05, 1.0), "wz_power_1_4hz": band(Pw, 1.0, 4.0), "wz_power_gt4hz": band(Pw, 4.0, 25.1),
        "ac_first_zero_s": float(acz[0] * DT) if len(acz) else None, "ac_min": float(ac.min()), "ac_min_at_s": float(np.argmin(ac) * DT),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    res = {str(r): {c: analyse(series(r, c)) for c in CASES} for r in a.root}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
