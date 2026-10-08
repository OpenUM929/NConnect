"""Run06 H4 steps.csv: split velocity tracking error into bias, gait band, high-frequency jitter.

Read-only. Usage: python -I tools/h1_run06_jitter_analysis.py [cases_dir]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT = Path("workspace/server_returns/train_260831-06_run05cfg_10000/fixed_eval/original/"
               "train_260831-06_run05cfg_10000_fixed_eval/cases")
DT = 0.02          # policy step (sim dt 0.005 x decimation 4)
WARMUP_S = 2.0     # drop spawn transient


def analyse(steps: Path) -> list[dict]:
    d = pd.read_csv(steps)
    d = d[d.time_s >= WARMUP_S]
    rows = []
    for ax in ("vx", "vy", "wz"):
        err = d[f"actual_{ax}"] - d[f"cmd_{ax}"]
        hi = gait = tot = 0.0
        for _, s in d.groupby("env_id"):
            x = s[f"actual_{ax}"].to_numpy()
            x = x - x.mean()
            f = np.fft.rfftfreq(len(x), DT)
            p = np.abs(np.fft.rfft(x)) ** 2
            hi += p[f >= 8].sum()
            gait += p[(f > 0) & (f < 4)].sum()
            tot += p[f > 0].sum()
        rows.append({
            "case": steps.parent.name, "axis": ax, "cmd": float(d[f"cmd_{ax}"].iloc[0]),
            "mean_actual": float(d[f"actual_{ax}"].mean()), "bias": float(err.mean()),
            "rmse": float(np.sqrt((err ** 2).mean())),
            "share_ge8hz": hi / tot, "share_lt4hz": gait / tot,
        })
    return rows


def main() -> None:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    rows = [r for p in sorted(base.glob("*/steps.csv")) for r in analyse(p)]
    print(pd.DataFrame(rows).round(4).to_csv(index=False), end="")


if __name__ == "__main__":
    main()
