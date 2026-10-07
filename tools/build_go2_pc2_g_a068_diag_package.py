#!/usr/bin/env python3
"""PC2 G-A068 진단 재생 패키지 빌더 (2026-10-07). 학습 없음 · 보상 변경 없음.

합의: workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md §14-2·§16(Codex 찬성: c2·c3),
§17(c6가 유일하게 R1 충족 — 같은 재생에 넣는다), Codex 직접 협의 1/3: 순서 c6 → c3 → c2. G-A066 빌더(tools/build_go2_pc2_g_a065_diag_package.py)를 그대로 쓰고
정책 목록과 보상 파일 출처만 바꾼다. 판독은 G-A067 판독기(tools/go2_g_a067_behavior_analysis.py)로 한다.

    python -B tools/build_go2_pc2_g_a068_diag_package.py --check
    python -B tools/build_go2_pc2_g_a068_diag_package.py --publish
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_pc2_g_a065_diag_package as b  # noqa: E402

G_A064_ZIP = b.GO2 / "upload/G-A064/current/GO2_G_A064_PC2_S07_COMBO_v4.zip"
G_A064_ZIP_SHA = "8c0e711568e09b41b50102ec24c9d6c18a0a4f419447c0095b613f90f4260f0b"

b.WORK_ID, b.SLUG, b.UP = "G-A068", "g_a068", "G_A068"
b.EDITION = "v1"
b.RELEASE = f"GO2_{b.UP}_PC2_DIAG_REPLAY_{b.EDITION}"
b.PREFIX = f"go2_{b.SLUG}_pc2/"
b.STATUS_DIR = f"go2_{b.SLUG}_pc2_points"
b.DESIGN = "workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md"
b.POLICIES = (
    ("c6", "workspace/_keep/go2_g_a064_pc2_c6_s07_ang_vel_xy_l2_m0p035", "s07 + ang_vel_xy_l2 -0.05->-0.035 (G-A064 c6)"),
    ("c3", "workspace/_keep/go2_g_a064_pc2_c3_s07_action_rate_l2_m0p0075", "s07 + action_rate_l2 -0.01->-0.0075 (G-A064 c3)"),
    ("c2", "workspace/_keep/go2_g_a064_pc2_c2_s07_lin_vel_z_l2_m0p5", "s07 + lin_vel_z_l2 -1.25->-0.5 (G-A064 c2)"),
)
b.REWARD_RUNS = {"c2": "c2_s07_lin_vel_z_l2_m0p5", "c3": "c3_s07_action_rate_l2_m0p0075",
                 "c6": "c6_s07_ang_vel_xy_l2_m0p035"}
_orig_source = b.pc2_source


def pc2_source() -> dict[str, bytes]:
    """평가 소스는 G-A063 shared/candidate(같은 evaluator 바이트), 보상 파일은 G-A064 각 점의 candidate."""
    saved = b.REWARD_RUNS
    b.REWARD_RUNS = {}
    try:
        out = _orig_source()
    finally:
        b.REWARD_RUNS = saved
    outer = G_A064_ZIP.read_bytes()
    b.need(b.sha(outer) == G_A064_ZIP_SHA, "G-A064 release ZIP SHA changed")
    with zipfile.ZipFile(io.BytesIO(outer)) as z:
        for key, run in b.REWARD_RUNS.items():
            out[f"_rewards_{key}"] = z.read(f"go2_g_a064_pc2/runs/{run}/candidate/quadruped_rewards.py")
    return out


b.pc2_source = pc2_source

if __name__ == "__main__":
    raise SystemExit(b.main())
