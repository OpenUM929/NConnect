#!/usr/bin/env python3
"""G-A062 PC2 일괄 실행 P 계열(P5·P6·P4) 분석 자료 (2026-10-04).

G-A060 분석 도구(tools/go2_g_a060_pc2_analysis.py)의 계산식을 그대로 쓰고 비교 대상만 바꾼다:
P0 = PC2 B1(G-A060 a048_seed42), P 점 = P0 + 한 항. 회수된 점만 넣는다(없는 폴더는 건너뛴다).
판정(분류)은 tools/go2_pc2_tree_readout.py 가 하고, 이 도구는 넘어짐 경로·상태표·proxy 자료만 만든다.

    python -B tools/go2_g_a062_p_analysis.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a062_p_analysis_20261004/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_g_a060_pc2_analysis as base  # noqa: E402

P0 = "workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42"
POINTS = (  # (짧은 이름, 변경, 회수 폴더)
    ("PC2_P5", "dof_acc_l2 -2.5e-7->-1.25e-7", "workspace/_keep/go2_g_a062_pc2_p5_dof_acc_l2_m1p25e_7"),
    ("PC2_P6", "dof_acc_l2 -2.5e-7->-6.25e-8", "workspace/_keep/go2_g_a062_pc2_p6_dof_acc_l2_m6p25e_8"),
    ("PC2_P4", "dof_torques_l2 -2e-4->-5e-5", "workspace/_keep/go2_g_a062_pc2_p4_dof_torques_l2_m5e_5"),
)
PRESENT = tuple(p for p in POINTS if (ROOT / p[2] / "RESULT_STATUS.txt").is_file())
base.SRC = ROOT  # 회수본이 다른 작업 폴더에 있으므로 저장소 루트 기준 상대경로로 준다
base.OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a062_p_analysis_20261004"
base.ARMS = (("PC2_B1", "A048 그대로 (P0)", P0),) + PRESENT
_state = base.state_tables


def state_tables() -> dict:
    import go2_state_outcome as so
    orig = so.run

    def run():
        so.PAIRS = [("PC2_B1", name, f"{change} (P0 base, PC2)") for name, change, _ in PRESENT]
        return orig()
    so.run = run
    try:
        return _state()
    finally:
        so.run = orig


base.state_tables = state_tables

if __name__ == "__main__":
    raise SystemExit(base.main())
