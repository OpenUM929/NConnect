#!/usr/bin/env python3
"""G-A058 행 2(이 PC A043 seed 43) 판독 — 같은 저장소 계산식으로 재계산 (2026-10-02).

비교 열: 서버 A043 s42, 서버 A048 s42, 이 PC A048 s42(행 1), 이 PC A043 s43(행 2).
지표 계산은 tools/go2_g_a057_sweep_compare 의 axis_scores·case_metrics, 계단 모서리 동작은
tools/go2_stairs_six_edge_compare.py 와 같은 정의(모서리 = 지형이 1초 행보다 단 높이 절반 이상
높아진 첫 행, 접근 창 1~3초, 모서리 창 −0.5~+1.5초)를 쓴다. 기록만 하며 판정 문턱을 만들지 않는다.

    python -B tools/go2_g_a058_row2_check.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a058_row2_check_20261002/
"""
import csv
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_axis_bottleneck as axis  # noqa: E402
import go2_g_a057_sweep_compare as cmp  # noqa: E402
from go2_climb_count import alive_rows, gained_steps  # noqa: E402

ARMS = {
    "server_A043_s42": "go2_g_a043_a033_lin_vel_z_m15",
    "server_A048_s42": "go2_g_a048_a033_lin_vel_z_m125",
    "local_A048_s42": "go2_g_a058_a048_seed42",
    "local_A043_s43": "go2_g_a058_a043_seed43",
}
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a058_row2_check_20261002"
DT = 0.02
EDGE_METRICS = ("ap_hrel", "ap_tilt", "ap_speed", "ap_vz_rms", "pre_speed", "ed_rise", "ed_vz_max",
                "ed_tilt_max", "ed_speed_min", "ed_vx_mean", "alive_s")


def edge_rows(arm: str, d: str):
    out = []
    for seed in (101, 202, 303):
        for case, h in (("stairs_10_down", .10), ("stairs_15_down", .15)):
            p = cmp.KEEP / d / f"evaluation/candidate/cases/seed_{seed}/{case}/steps.csv"
            for env, rows in alive_rows(p).items():
                n = len(rows)
                A = lambda k: np.array([float(r[k]) for r in rows])  # noqa: E731
                z, tz, hr, pg, sp, vx = A("root_z"), A("terrain_z"), A("height_rel"), A("proj_grav_z"), A("speed_xy"), A("actual_vx")
                tilt = np.degrees(np.arccos(np.clip(-pg, -1, 1)))
                vz = np.gradient(z, DT)
                rec = dict(arm=arm, seed=seed, case=case, env=env, steps=gained_steps(rows, "climb", h), alive_s=n * DT)
                a0, a1 = 50, min(150, n)
                if a1 - a0 > 50:
                    rec.update(ap_hrel=hr[a0:a1].mean(), ap_tilt=tilt[a0:a1].mean(), ap_speed=sp[a0:a1].mean(),
                               ap_vz_rms=math.sqrt((vz[a0:a1] ** 2).mean()))
                tz0 = tz[min(50, n - 1)]
                e = next((i for i in range(50, n) if tz[i] - tz0 > 0.5 * h), None)
                rec["reached_edge"] = e is not None
                if e is not None:
                    w0, w1 = max(0, e - 25), min(n, e + 75)
                    rec.update(ed_rise=(z[w0:w1] - z[w0]).max(), ed_vz_max=vz[w0:w1].max(), ed_tilt_max=tilt[w0:w1].max(),
                               ed_speed_min=sp[e:w1].min() if w1 > e else float("nan"),
                               ed_vx_mean=vx[e:w1].mean() if w1 > e else float("nan"),
                               pre_speed=sp[max(0, e - 25):e].mean() if e > 0 else float("nan"))
                out.append(rec)
    return out


def med(rows, k):
    v = [r[k] for r in rows if k in r and not (isinstance(r[k], float) and math.isnan(r[k]))]
    return st.median(v) if v else float("nan")


def main() -> int:
    std = float(axis.registry()["score"]["tracking_proxy_std"])
    cols = {}
    for label, name in ARMS.items():
        arm = cmp.KEEP / name
        rec = {"present": True, "axes": cmp.axis_scores(arm), "gpu": cmp.gpu(arm),
               "variable": "-", "value": "-", "status": "-", "arm": name}
        for c in (*cmp.FALL_CASES, *cmp.STAIRS):
            rec[c] = cmp.case_metrics(arm, c, std)
        cols[label] = cmp.flat(rec)
    keys = [k for k in cols["server_A043_s42"] if k not in ("variable", "value", "status")]
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "ROW2_CHECK.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", *ARMS])
        for k in keys:
            w.writerow([k, *(cols[a].get(k, "") for a in ARMS)])
    for k in keys:
        print(k, *(cols[a].get(k, "") for a in ARMS), sep="\t")

    rows = [r for label, d in ARMS.items() for r in edge_rows(label, d)]
    fields = sorted({k for r in rows for k in r})
    with open(OUT / "STAIRS_EDGE_ROWS.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    summary = []
    for case in ("stairs_10_down", "stairs_15_down"):
        for grp, cond in (("ALL", lambda r: True), ("climb>=2", lambda r: r["steps"] >= 2), ("climb<2", lambda r: r["steps"] < 2)):
            for label in ARMS:
                rs = [r for r in rows if r["arm"] == label and r["case"] == case and cond(r)]
                s = dict(case=case, group=grp, arm=label, n=len(rs), reached_edge=sum(r["reached_edge"] for r in rs))
                s.update({m: round(med(rs, m), 4) for m in EDGE_METRICS})
                summary.append(s)
    with open(OUT / "STAIRS_EDGE_MEDIANS.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    print()
    for s in summary:
        print(*s.values(), sep="\t")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
