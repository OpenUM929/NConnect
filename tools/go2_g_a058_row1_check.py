#!/usr/bin/env python3
"""G-A058 행 1(이 PC A048 seed 42) 대 서버 A048(seed 42) 대 이 PC track 1.2 — 같은 저장소 계산식으로 재계산 (2026-10-01).

실행 PC가 보낸 READOUT.md 를 받아쓰지 않고 tools/go2_g_a057_sweep_compare 의 axis_scores·case_metrics 로 다시 잰다.
기록만 한다: 한 쌍의 관측이라 환경 영향과 학습 변동을 분리하지 않는다(Codex 합의 2026-09-30).

    python -B tools/go2_g_a058_row1_check.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a058_row1_check_20261001/ROW1_CHECK.csv
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_axis_bottleneck as axis  # noqa: E402
import go2_g_a057_sweep_compare as cmp  # noqa: E402

ARMS = {
    "server_A048_seed42": "go2_g_a048_a033_lin_vel_z_m125",
    "local_A048_seed42": "go2_g_a058_a048_seed42",
    "local_A057_track_1p2": "go2_g_a057_track_lin_vel_xy_exp_p1p2",
}
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a058_row1_check_20261001/ROW1_CHECK.csv"


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
    keys = [k for k in cols["server_A048_seed42"] if k not in ("variable", "value", "status")]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", *ARMS])
        for k in keys:
            w.writerow([k, *(cols[a].get(k, "") for a in ARMS)])
    for k in keys:
        print(k, *(cols[a].get(k, "") for a in ARMS), sep="\t")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
