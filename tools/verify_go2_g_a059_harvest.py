"""G-A059 A043 계단 진단 재생 회수 검증 (2026-10-01).  성능·원인을 판정하지 않는다.

G-A056 검증기(tools/verify_go2_a043_diag_replay_harvest.py)의 판정 규칙(zip·artifact·channels·video, 종료코드
0/3/1)을 그대로 쓰고, 회수 폴더 이름·seed·case·영상 목록만 G-A059 것으로 바꾼다. 정책·평가기 식별자는 같다(G-A043 iter 900).

    python -B tools/verify_go2_g_a059_harvest.py <GO2_G_A059_RESULT.zip | 압축 푼 폴더> [--out <dir>]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_go2_g_a059_a043_stairs_diag_package as pkg  # noqa: E402
import verify_go2_a043_diag_replay_harvest as base  # noqa: E402

base.KEEP_DIR_NAME = pkg.KEEP_DIR_NAME
base.SEED = pkg.SEED
base.CASES = pkg.CASES
base.RUNS = tuple((label, pkg.SEED, c) for c in pkg.CASES for label in ("plain", "diag"))
base.VIDEOS = pkg.VIDEOS
base.DEFAULT_OUT = base.ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a059_diag_20261001"

KEEP_DIR_NAME, SEED, CASES, RUNS, VIDEOS = base.KEEP_DIR_NAME, base.SEED, base.CASES, base.RUNS, base.VIDEOS
run_dir, video_dir, main = base.run_dir, base.video_dir, base.main

if __name__ == "__main__":
    raise SystemExit(main())
