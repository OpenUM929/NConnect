#!/usr/bin/env python3
"""G-A062 PC2 일괄 실행 Q 계열(Q0·Q1·Q2) 분석 자료 (2026-10-04).

G-A060 분석 도구(tools/go2_g_a060_pc2_analysis.py)의 계산식을 그대로 쓰고 비교 대상만 바꾼다:
P0 = PC2 B1(G-A060 a048_seed42), Q0 = P0 + lin_vel_z -1.5(A043 보상), Q1·Q2 = Q0 + 한 항.
판정(분류)은 tools/go2_pc2_tree_readout.py 가 하고, 이 도구는 넘어짐 경로·상태표·proxy 자료만 만든다.

    python -B tools/go2_g_a062_q_analysis.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a062_q_analysis_20261004/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_g_a060_pc2_analysis as base  # noqa: E402

P0 = "workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42"
Q0 = "workspace/_keep/go2_g_a062_pc2_q0_lin_vel_z_l2_m1p5"
Q1 = "workspace/_keep/go2_g_a062_pc2_q1_track_ang_vel_z_exp_p1p0"
Q2 = "workspace/_keep/go2_g_a062_pc2_q2_ang_vel_xy_l2_m0p06"
base.SRC = ROOT  # 회수본이 다른 작업 폴더에 있으므로 저장소 루트 기준 상대경로로 준다
base.OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a062_q_analysis_20261004"
base.ARMS = (
    ("PC2_B1", "A048 그대로 (P0)", P0),
    ("PC2_Q0", "lin_vel_z_l2 -1.25->-1.5 (A043 보상)", Q0),
    ("PC2_Q1", "Q0 + track_ang_vel_z_exp 0.75->1.0", Q1),
    ("PC2_Q2", "Q0 + ang_vel_xy_l2 -0.05->-0.06", Q2),
)
_state = base.state_tables


def state_tables() -> dict:
    import go2_state_outcome as so
    orig = so.run

    def run():
        so.PAIRS = [("PC2_B1", "PC2_Q0", "lin_vel_z_l2 -1.25->-1.5 (P0 base, PC2)"),
                    ("PC2_Q0", "PC2_Q1", "track_ang_vel_z_exp 0.75->1.0 (Q0 base, PC2)"),
                    ("PC2_Q0", "PC2_Q2", "ang_vel_xy_l2 -0.05->-0.06 (Q0 base, PC2)")]
        return orig()
    so.run = run
    try:
        return _state()
    finally:
        so.run = orig


base.state_tables = state_tables

if __name__ == "__main__":
    raise SystemExit(base.main())
