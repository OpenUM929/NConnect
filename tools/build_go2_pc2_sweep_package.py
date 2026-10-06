#!/usr/bin/env python3
"""PC2 계단 집중 범위 스윕 패키지 빌더 — track 1.5 고정, P0 위 한 항씩 배포 추천 범위 끝에서 끝까지 (G-A063, 2026-10-04).

사용자 지시(2026-10-04): "모든 값을 고정하고 하나의 변수만 강좌와 배포를 기준으로 최소 최대 안에서 변경",
"track 1.5를 기준으로 계단에 집중한 테스트", 충돌 항(lin_vel_z 고정 해제, feet_air_time 기각 해제) "둘 다 포함".
설계: workspace/training/quadruped/upload/plan/GO2_PC2_STAIRS_RANGE_SWEEP_20261004.md

G-A062 일괄 실행 빌더(tools/build_go2_pc2_batch_package.py)의 점 생성·run_all·run_point 를 그대로 쓰고 점 목록만 바꾼다.
모든 점의 부모는 P0(PC2 A048 = G-A060 B1, track 1.5)다. 다른 기준선에서 잰 같은 값은 이 기준에서 다시 잰다(이력 예외 사유에 적는다).

    python -B tools/build_go2_pc2_sweep_package.py --check
    python -B tools/build_go2_pc2_sweep_package.py --publish --work-id G-A063
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_pc2_batch_package as batch  # noqa: E402

DESIGN = "workspace/training/quadruped/upload/plan/GO2_PC2_STAIRS_RANGE_SWEEP_20261004.md"
SWEEP = "P0 기준 범위 스윕 재측정(사용자 지시 2026-10-04: 기준 고정·한 항씩 배포 최소~최대)"
# (key, 바꿀 항, 값, 메모) — 실행 순서. 배포 추천 범위: lin_vel_z −5.0~−0.5, feet 0.01~0.5, ang −0.3~−0.02, action −0.02~−0.005.
GRID = (
    ("s01_lin_vel_z_l2_m5", "lin_vel_z_l2", -5.0, "배포 범위 최강. 배포 ③ '강하게: 몸을 낮게 깔고 안정 (험지/계단 유리, 대신 굼뜸)'."),
    ("s02_lin_vel_z_l2_m3", "lin_vel_z_l2", -3.0, "배포 시작값·강좌 예시 강한 쪽."),
    ("s03_lin_vel_z_l2_m2", "lin_vel_z_l2", -2.0, "서버 A033 값을 P0 기준으로 재측정."),
    ("s04_lin_vel_z_l2_m0p5", "lin_vel_z_l2", -0.5, "배포 범위 최약. 배포 ③ '약하게: 통통 튀며 역동 (착지 불안정)'."),
    ("s05_feet_air_time_p0p01", "feet_air_time", 0.01, "배포 범위 최소·배포 시작값. '↓ 발을 거의 안 들고 끌듯이'."),
    ("s06_feet_air_time_p0p1", "feet_air_time", 0.1, "범위 내 하단."),
    ("s07_feet_air_time_p0p35", "feet_air_time", 0.35, "범위 내 상단. 배포 ② '↑ 발을 높이 들어 험지 돌파 유리', 생성기 '발 높이 ↑ 등반 유리'."),
    ("s08_feet_air_time_p0p5", "feet_air_time", 0.5, "배포 범위 최대. '0.5+ 면 바운딩 가능성'."),
    ("s09_ang_vel_xy_l2_m0p3", "ang_vel_xy_l2", -0.3, "배포 범위 최강. 배포 ④ '강하게: 덜 휘청'."),
    ("s10_ang_vel_xy_l2_m0p15", "ang_vel_xy_l2", -0.15, "범위 중간."),
    ("s11_ang_vel_xy_l2_m0p02", "ang_vel_xy_l2", -0.02, "배포 범위 최약. 배포 ④ '약하게: 흔들림 허용 (험지 적응 여지)'."),
    ("s12_action_rate_l2_m0p02", "action_rate_l2", -0.02, "배포 범위 최강. 배포 ⑤ '강하게: 부드럽지만 굼뜬 반응'."),
    ("s13_action_rate_l2_m0p005", "action_rate_l2", -0.005, "배포 범위 최약. 배포 ⑤ '약하게: 민첩하지만 다리 떨림'."),
    ("s14_p0_repeat", "lin_vel_z_l2", -1.25, "P0 그대로 재학습. 같은 PC·같은 seed 학습 흔들림 측정(스윕 차이 해석 기준)."),
)


def points() -> tuple:
    out = []
    for key, var, value, note in GRID:
        exemption = ("REPEAT: P0 재학습(학습 흔들림 측정)" if key.endswith("p0_repeat")
                     else SWEEP)
        out.append((key, {}, var, value, exemption, note))
    return tuple(out)


def names(work_id: str) -> dict[str, str]:
    n = batch.pkg.names(work_id)
    n["release"] = f"GO2_{n['up']}_PC2_STAIRS_SWEEP_v1"
    return n


_ORIG_GUIDE = batch.guide


def guide(n: dict, zip_sha: str | None) -> str:
    text = _ORIG_GUIDE(n, zip_sha)
    return (text.replace("60점 목표 전략", "계단 집중 범위 스윕(track 1.5 고정)")
                .replace("P0 = PC2 A048(G-A060 B1), Q0 = P0 + lin_vel_z -1.5(A043 보상, 1번 점):",
                         "모든 점의 부모 P0 = PC2 A048(G-A060 B1, track 1.5). s14 는 P0 그대로 재학습:")
                .replace("--hours 18", "--hours 40"))


@contextlib.contextmanager
def configured():
    """일괄 실행 빌더의 점 목록·이름·안내문을 이 스윕으로 잠시 바꾼다(끝나면 되돌린다 — 같은 프로세스의 G-A062 빌드에 새지 않게)."""
    keys = ("POINTS", "DESIGN", "PROVISIONAL_WORK_ID", "names", "guide")
    saved = {k: getattr(batch, k) for k in keys}
    batch.POINTS, batch.DESIGN, batch.PROVISIONAL_WORK_ID = points(), DESIGN, "G-A063"
    batch.names, batch.guide = names, guide
    try:
        yield batch
    finally:
        for k, v in saved.items():
            setattr(batch, k, v)


def build(work_id: str = "G-A063") -> tuple[bytes, dict]:
    with configured():
        return batch.build(work_id)


def main(argv: list[str] | None = None) -> int:
    with configured():
        return batch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
