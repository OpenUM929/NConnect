#!/usr/bin/env python3
"""G-A063 PC2 계단 범위 스윕 분석 자료 (2026-10-05). s01~s03(lin_vel_z 강화), s04(lin_vel_z 완화), s05~s07(feet_air_time 0.01/0.1/0.35).

G-A060 분석 도구(tools/go2_g_a060_pc2_analysis.py)의 계산식을 그대로 쓰고 비교 대상만 바꾼다:
P0 = PC2 B1(G-A060 a048_seed42, lin_vel_z -1.25). 각 점 = P0 + 한 항(아래 ARMS). 점이 회수될 때마다 ARMS·PAIRS에 한 줄씩 더한다.
판정(분류)은 tools/go2_pc2_tree_readout.py 가 하고, 이 도구는 넘어짐 경로·상태표·proxy 자료만 만든다.

    python -B tools/go2_g_a063_s_analysis.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a063_s_analysis_20261005/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_g_a060_pc2_analysis as base  # noqa: E402

P0 = "workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42"
S01 = "workspace/_keep/go2_g_a063_pc2_s01_lin_vel_z_l2_m5"
S02 = "workspace/_keep/go2_g_a063_pc2_s02_lin_vel_z_l2_m3"
S03 = "workspace/_keep/go2_g_a063_pc2_s03_lin_vel_z_l2_m2"
S04 = "workspace/_keep/go2_g_a063_pc2_s04_lin_vel_z_l2_m0p5"
S05 = "workspace/_keep/go2_g_a063_pc2_s05_feet_air_time_p0p01"
S06 = "workspace/_keep/go2_g_a063_pc2_s06_feet_air_time_p0p1"
S07 = "workspace/_keep/go2_g_a063_pc2_s07_feet_air_time_p0p35"
base.SRC = ROOT  # 회수본이 다른 작업 폴더에 있으므로 저장소 루트 기준 상대경로로 준다
base.OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a063_s_analysis_20261005"
base.ARMS = (
    ("PC2_B1", "A048 그대로 (P0, lin_vel_z -1.25)", P0),
    ("PC2_S01", "lin_vel_z_l2 -1.25->-5.0", S01),
    ("PC2_S02", "lin_vel_z_l2 -1.25->-3.0", S02),
    ("PC2_S03", "lin_vel_z_l2 -1.25->-2.0", S03),
    ("PC2_S04", "lin_vel_z_l2 -1.25->-0.5", S04),
    ("PC2_S05", "feet_air_time 0.2->0.01", S05),
    ("PC2_S06", "feet_air_time 0.2->0.1", S06),
    ("PC2_S07", "feet_air_time 0.2->0.35", S07),
)
_state = base.state_tables


def state_tables() -> dict:
    import go2_state_outcome as so
    orig = so.run

    def run():
        so.PAIRS = [("PC2_B1", "PC2_S01", "lin_vel_z_l2 -1.25->-5.0 (P0 base, PC2)"),
                    ("PC2_B1", "PC2_S02", "lin_vel_z_l2 -1.25->-3.0 (P0 base, PC2)"),
                    ("PC2_B1", "PC2_S03", "lin_vel_z_l2 -1.25->-2.0 (P0 base, PC2)"),
                    ("PC2_B1", "PC2_S04", "lin_vel_z_l2 -1.25->-0.5 (P0 base, PC2)"),
                    ("PC2_B1", "PC2_S05", "feet_air_time 0.2->0.01 (P0 base, PC2)"),
                    ("PC2_B1", "PC2_S06", "feet_air_time 0.2->0.1 (P0 base, PC2)"),
                    ("PC2_B1", "PC2_S07", "feet_air_time 0.2->0.35 (P0 base, PC2)")]
        return orig()
    so.run = run
    try:
        return _state()
    finally:
        so.run = orig


base.state_tables = state_tables

if __name__ == "__main__":
    raise SystemExit(base.main())
