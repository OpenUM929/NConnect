#!/usr/bin/env python3
"""PC2 G-A069 패키지 빌더 — G-A064 c6(s07 + ang_vel_xy −0.035)를 학습 seed 43으로 다시 학습한다 (2026-10-07).

합의: workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md §17-4·§17-6과
Codex 직접 협의(1/3, 사용자 지시 "전체를 공유하면서 이야기"): G-A068 진단 다음에 c6 하나만 독립 학습 seed로 확인한다.
c6는 다섯 점 중 유일하게 R1을 충족했지만(계단 높이 유지 3→45) 같은 항의 양 끝(−0.05, −0.02)과 정반대라
학습 흔들림과 값에 따른 비선형 변화를 아직 분리하지 못했다. 보상은 G-A064 c6와 같고 학습 seed만 다르다.
G-A064 빌더(→ G-A062 일괄 실행 빌더)의 점 생성·run_all·run_point 를 그대로 쓴다.

    python -B tools/build_go2_pc2_g_a069_package.py --check
    python -B tools/build_go2_pc2_g_a069_package.py --publish --work-id G-A069
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_pc2_g_a064_package as g64  # noqa: E402

batch = g64.batch
TRAIN_SEED = "43"
SEED_REPEAT = "학습 seed 재현: G-A064 c6(같은 부모 s07·같은 값 ang_vel_xy_l2 −0.035, 학습 seed 42)를 seed 43으로 다시 학습한다"
NOTE = ("c6 seed 42는 계단 높이 유지 3→45·R1 충족, 험지 뒤집힘 7→31·밀침 6→43. 같은 항 −0.05/−0.02와 정반대라 "
        "학습 흔들림인지 확인한다. 예측(문서 §17-6·Codex): 유지 ≥25, 2/3 seed에서 s07보다 높음; 험지 뒤집힘 ≥15.")
POINTS = (("c6s43_s07_ang_vel_xy_l2_m0p035", dict(g64.S07), "ang_vel_xy_l2", -0.035, SEED_REPEAT, NOTE),)


def names(work_id: str) -> dict[str, str]:
    n = batch.pkg.names(work_id)
    n["release"] = f"GO2_{n['up']}_PC2_C6_SEED43_v1"
    return n


def guide(n: dict, zip_sha: str | None) -> str:
    return (g64.guide(n, zip_sha).replace("s07 부모 조합·action_rate 사이값", "c6 학습 seed 43 재현")
            .replace("--hours 16", "--hours 4"))


@contextlib.contextmanager
def configured():
    with g64.configured():
        saved = (batch.POINTS, batch.PROVISIONAL_WORK_ID, batch.names, batch.guide, batch.TRAIN_SEED)
        batch.POINTS, batch.PROVISIONAL_WORK_ID = POINTS, "G-A069"
        batch.names, batch.guide, batch.TRAIN_SEED = names, guide, TRAIN_SEED
        try:
            yield batch
        finally:
            batch.POINTS, batch.PROVISIONAL_WORK_ID, batch.names, batch.guide, batch.TRAIN_SEED = saved


def build(work_id: str = "G-A069") -> tuple[bytes, dict]:
    with configured():
        return batch.build(work_id)


def main(argv: list[str] | None = None) -> int:
    with configured():
        return batch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
