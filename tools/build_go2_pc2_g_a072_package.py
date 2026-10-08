#!/usr/bin/env python3
"""PC2 G-A072 패키지 빌더 — G-A063 s04(P0 + lin_vel_z −1.25→−0.5)를 학습 seed 43으로 다시 학습한다 (2026-10-08).

합의: workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md §62~§65.
- G-A069에서 c6의 계단 이득(seed 42: 높이 유지 45)이 seed 43에서 사라졌다(1/96 도달). PC2 계단 판독이 모두 학습 seed 42 하나였으므로
  기존 계단 이득 점이 다른 학습에서도 쓸 만한 행동을 내는지 먼저 확인한다(§62-4·§64-2).
- Codex §65는 s04 한 점으로 좁혔으나, 사용자 지시(2026-10-08 "협의는 길었는데 테스트 점이 없네")로 s04 → P0 seed 43 대조 → s13 → s11 4점을
  한 일괄 실행으로 낸다. 뒤 점은 STOP 파일로 끊을 수 있다.
- 탐색 기준(§64-2·§65): 15cm ≥2단 ≥12/96 이고 P0 seed 42 값(3)보다 큼. 이것만으로 재현·부모 채택을 판정하지 않고
  계단 접근→높이 획득→진행·유지/손실, 험지 지지 상실·전복, 밀침 회복을 함께 읽는다.
- 예측(§64-3 Claude): s04 seed 43 ≥12. 보상은 G-A063 s04와 같고 학습 seed만 다르다. checkpoint 이어 학습 아님.
G-A062 일괄 실행 빌더(tools/build_go2_pc2_batch_package.py)의 점 생성·run_all·run_point 를 그대로 쓴다.

    python -B tools/build_go2_pc2_g_a072_package.py --check
    python -B tools/build_go2_pc2_g_a072_package.py --publish --work-id G-A072
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_pc2_batch_package as batch  # noqa: E402

DESIGN = "workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md"
TRAIN_SEED = "43"
SEED_REPEAT = "학습 seed 재현: G-A063 {k}(같은 부모 P0·같은 값 {v}, 학습 seed 42)를 seed 43으로 다시 학습한다"
REPEAT = "REPEAT: P0(PC2 A048 보상) 학습 seed 43 대조 — 같은 seed에서 P0 대비 변경 효과를 가르기 위한 기준(§65가 지적한 공백)"
# (key, 바꿀 항, 값, 이력 예외, 메모) — 실행 순서. 사용자 지시(2026-10-08 "테스트 점이 없네"): s04 하나에서 4점으로 넓힌다.
GRID = (
    ("s04s43_lin_vel_z_l2_m0p5", "lin_vel_z_l2", -0.5, SEED_REPEAT.format(k="s04", v="lin_vel_z_l2 −0.5"),
     "s04 seed 42: 15cm ≥2단 3→23·10cm 낙상 44→2, 험지 옆걸음 낙상 41→63·밀침 0→40. 탐색 기준 ≥12 이고 >3(§64-2·§65). Claude 예측 ≥12."),
    ("p0s43_lin_vel_z_l2_m1p25", "lin_vel_z_l2", -1.25, REPEAT,
     "P0 seed 43. s04·s13·s11 seed 43을 같은 seed의 부모와 비교한다. P0 seed 42: 15cm ≥2단 3."),
    ("s13s43_action_rate_l2_m0p005", "action_rate_l2", -0.005, SEED_REPEAT.format(k="s13", v="action_rate_l2 −0.005"),
     "s13 seed 42: 15cm ≥2단 3→19. 탐색 기준 ≥10. Claude 예측 <10, Codex CX72-S13 ≥10."),
    ("s11s43_ang_vel_xy_l2_m0p02", "ang_vel_xy_l2", -0.02, SEED_REPEAT.format(k="s11", v="ang_vel_xy_l2 −0.02"),
     "s11 seed 42: 15cm ≥2단 3→13·밀침 2. 탐색 기준 ≥7. Claude 예측 <7(같은 항 c6가 seed 의존을 보임)."),
)
POINTS = tuple((key, {}, var, value, exemption, note) for key, var, value, exemption, note in GRID)


def names(work_id: str) -> dict[str, str]:
    n = batch.pkg.names(work_id)
    n["release"] = f"GO2_{n['up']}_PC2_SEED43_REPRO_v1"
    return n


_ORIG_GUIDE = batch.guide


def guide(n: dict, zip_sha: str | None) -> str:
    return (_ORIG_GUIDE(n, zip_sha)
            .replace("60점 목표 전략 ", "학습 seed 43 재현 ")
            .replace("점마다 학습 seed 42", "점마다 학습 seed 43")
            .replace("P0 = PC2 A048(G-A060 B1), Q0 = P0 + lin_vel_z -1.5(A043 보상, 1번 점):",
                     "부모 P0 = PC2 A048(G-A060 B1). 학습 seed 43:")
            .replace("--hours 18", "--hours 12"))


@contextlib.contextmanager
def configured():
    keys = ("POINTS", "DESIGN", "PROVISIONAL_WORK_ID", "names", "guide", "TRAIN_SEED")
    saved = {k: getattr(batch, k) for k in keys}
    batch.POINTS, batch.DESIGN, batch.PROVISIONAL_WORK_ID = POINTS, DESIGN, "G-A072"
    batch.names, batch.guide, batch.TRAIN_SEED = names, guide, TRAIN_SEED
    try:
        yield batch
    finally:
        for k, v in saved.items():
            setattr(batch, k, v)


def build(work_id: str = "G-A072") -> tuple[bytes, dict]:
    with configured():
        return batch.build(work_id)


def main(argv: list[str] | None = None) -> int:
    with configured():
        return batch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
