"""15cm 계단 오르기: 모서리 창 최대 수직 속도 시각 ±0.2초의 전진 속도 (2026-09-30).

`GO2_STAIRS_SIX_EDGE_COMPARE_20260930.md` §4의 동시성 수치를 재현한다.
정의는 `go2_stairs_six_edge_compare.py`와 같다: 모서리 = 로봇 아래 지형이 출발(1초 행)보다
단 높이 절반 이상 높아진 첫 행, 창 = 모서리 −0.5~+1.5초, 수직 속도 = root_z 차분(세계 좌표).
오른 단 수는 `go2_climb_count.gained_steps`.
"""
import csv, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_climb_count import alive_rows, gained_steps

K = Path(__file__).resolve().parents[1] / "workspace" / "_keep"
RUNS = {"A043": "go2_g_a043_a033_lin_vel_z_m15", "A048": "go2_g_a048_a033_lin_vel_z_m125",
        "A044": "go2_g_a044_a033_lin_vel_z_m175"}
OUT = Path(__file__).resolve().parents[1] / "workspace/training/quadruped/reports/evidence/go2_stairs_six_edge_compare_20260930"
H, DT = 0.15, 0.02

def main() -> None:
    rows = []
    for arm, d in RUNS.items():
        for seed in (101, 202, 303):
            p = K / d / f"evaluation/candidate/cases/seed_{seed}/stairs_15_down/steps.csv"
            for env, rs in alive_rows(p).items():
                n = len(rs)
                z = np.array([float(r["root_z"]) for r in rs]); tz = np.array([float(r["terrain_z"]) for r in rs])
                vx = np.array([float(r["actual_vx"]) for r in rs]); vz = np.gradient(z, DT)
                tz0 = tz[min(50, n - 1)]
                e = next((i for i in range(50, n) if tz[i] - tz0 > 0.5 * H), None)
                if e is None:
                    continue
                w0, w1 = max(0, e - 25), min(n, e + 75)
                k = w0 + int(vz[w0:w1].argmax())
                rows.append(dict(arm=arm, seed=seed, env=env, steps=gained_steps(rs, "climb", H),
                                 t_vzmax_minus_edge=(k - e) * DT, vz_max=vz[k],
                                 vx_at_vzmax=vx[max(0, k - 10):k + 11].mean()))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "PUSH_FORWARD_SIMULTANEITY.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for arm in RUNS:
        for ok in (True, False):
            g = [r for r in rows if r["arm"] == arm and (r["steps"] >= 2) == ok]
            if not g:
                continue
            q = lambda k: np.percentile([r[k] for r in g], [25, 50, 75])
            print(f"{arm} {'ok' if ok else 'fail'} n={len(g)} " + " ".join(
                f"{k}=p25/50/75 {a:.3f}/{b:.3f}/{c:.3f}" for k in ("t_vzmax_minus_edge", "vz_max", "vx_at_vzmax") for a, b, c in [q(k)]))

if __name__ == "__main__":
    main()
