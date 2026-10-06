#!/usr/bin/env python3
"""G-A061 N3(dof_torques_l2 -2e-4 -> -1e-4) 분석 자료 (2026-10-04).

G-A060 분석 도구(tools/go2_g_a060_pc2_analysis.py)의 계산식을 그대로 쓰고 비교 대상만 바꾼다:
부모 P0 = PC2 B1(G-A060 a048_seed42), 노드 = G-A061 N3. 같은 PC2·같은 학습 seed 42.
판정(분류)은 tools/go2_pc2_tree_readout.py 가 하고, 이 도구는 넘어짐 경로·상태표·proxy 자료만 만든다.

    python -B tools/go2_g_a061_n3_analysis.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a061_n3_analysis_20261004/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_g_a060_pc2_analysis as base  # noqa: E402

P0 = "workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42"
N3 = "workspace/server_returns/G-A061/extracted/go2_g_a061_pc2_n3_dof_torques_l2_m1e_4"
base.SRC = ROOT  # 두 회수본이 다른 작업 폴더에 있으므로 저장소 루트 기준 상대경로로 준다
base.OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a061_n3_analysis_20261004"
base.ARMS = (
    ("PC2_B1", "A048 그대로 (부모 P0)", P0),
    ("PC2_N3", "dof_torques_l2 -2e-4->-1e-4", N3),
)
_state = base.state_tables


def state_tables() -> dict:
    import go2_state_outcome as so
    orig = so.run

    def run():
        so.PAIRS = [("PC2_B1", "PC2_N3", "dof_torques_l2 -2e-4->-1e-4 (P0 base, PC2)")]
        return orig()
    so.run = run
    try:
        return _state()
    finally:
        so.run = orig


base.state_tables = state_tables

if __name__ == "__main__":
    raise SystemExit(base.main())
