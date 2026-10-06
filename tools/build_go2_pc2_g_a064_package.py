#!/usr/bin/env python3
"""PC2 G-A064 패키지 빌더 — s07(P0 + feet_air_time 0.35) 위 계단 레버 조합 2점 + action_rate 사이값 2점 (2026-10-06).

합의: workspace/training/quadruped/upload/plan/GO2_G_A063_SWEEP_CODEX_CONSULT_20261006.md §12(점1·점2·판정·분기), §13(동률 규칙), §14(사용자 지시
"action_rate는 사이 값 테스트가 필요할 것 같아" → −0.0075·−0.015, s13 판독을 기다리지 않고 둘 다 넣어 선택 단계를 없앤다),
§15(사용자 승인: 계단 레버 중간값 lin_vel_z −0.875·ang_vel_xy −0.035 추가, 6점).
v2(§26, 사용자 승인 2026-10-06): c4(action_rate −0.015) 제외 — s12(−0.02) 붕괴, c4 이득을 지지하는 관측 없음(Codex 3/3).
진단 전 기본 순서 c1 → c2 → c3 → c6 → c5. G-A065 진단 결과로 순서가 바뀌면 v3로 다시 낸다.
G-A062 일괄 실행 빌더(tools/build_go2_pc2_batch_package.py)의 점 생성·run_all·run_point 를 그대로 쓰고 점 목록·부모만 바꾼다.

    python -B tools/build_go2_pc2_g_a064_package.py --check
    python -B tools/build_go2_pc2_g_a064_package.py --publish --work-id G-A064
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_pc2_batch_package as batch  # noqa: E402

DESIGN = "workspace/training/quadruped/upload/plan/GO2_G_A063_SWEEP_CODEX_CONSULT_20261006.md"
S07 = {"feet_air_time": 0.35}
S07_HARVEST = "workspace/_keep/go2_g_a063_pc2_s07_feet_air_time_p0p35"
COMBO = "조합 시험: G-A063에서 P0 위로 잰 값을 s07(feet 0.35) 부모 위에서 다시 잰다(합의 §12, 부모가 다름)"
# (key, 바꿀 항, 값, 메모) — 실행 순서
GRID = (
    ("c1_s07_ang_vel_xy_l2_m0p02", "ang_vel_xy_l2", -0.02,
     "계단 원인(모서리에서 앞을 들지 못함) → 강좌 '몸통을 기울이지 마라' 벌점 완화 → G-A063 s11 15cm ≥2단 3→13·밀침 2. 험지 이득 보존 여부."),
    ("c2_s07_lin_vel_z_l2_m0p5", "lin_vel_z_l2", -0.5,
     "같은 원인 → '위아래 흔들림 억제' 벌점 완화 → G-A063 s04 15cm ≥2단 3→23. 경쟁 설명: 진입 몸높이 상승. 밀침 0→40 부작용."),
    ("c3_s07_action_rate_l2_m0p0075", "action_rate_l2", -0.0075,
     "험지 원인 2-1(가는 쪽 발을 다시 딛지 못함) → 배포 ⑤ '약하게: 민첩' → 재착지 유리 예측. P0 −0.01과 범위 끝 −0.005 사이."),
    ("c6_s07_ang_vel_xy_l2_m0p035", "ang_vel_xy_l2", -0.035,
     "P0 −0.05와 −0.02의 가운데. −0.02에서 계단 3→13·G3 5.94→2.16. 같은 구조(사용자 지시 2026-10-06)."),
    ("c5_s07_lin_vel_z_l2_m0p875", "lin_vel_z_l2", -0.875,
     "P0 −1.25와 −0.5의 가운데. 양 끝에서 계단 이득(3→23)과 험지 손실(G3 5.94→2.93)이 함께 나왔고 강좌 설명도 둘로 갈린다(완화→들어올리기 / 너무 약하면 험지 붕괴). 그 사이의 모양을 본다(사용자 지시 2026-10-06)."),
)


def points() -> tuple:
    out = []
    for key, var, value, note in GRID:
        # 같은 항·같은 값의 P0 위 이력(G-A063 s04·s11)은 부모가 다르므로 예외로 적는다. 사이값은 이력 없음이 정상이다.
        exemption = COMBO if (var, value) in (("ang_vel_xy_l2", -0.02), ("lin_vel_z_l2", -0.5)) else None
        out.append((key, dict(S07), var, value, exemption, note))
    return tuple(out)


def names(work_id: str) -> dict[str, str]:
    n = batch.pkg.names(work_id)
    n["release"] = f"GO2_{n['up']}_PC2_S07_COMBO_v2"
    return n


_ORIG_GUIDE = batch.guide


def guide(n: dict, zip_sha: str | None) -> str:
    text = _ORIG_GUIDE(n, zip_sha)
    return (text.replace("60점 목표 전략", "s07 부모 조합·action_rate 사이값")
                .replace("P0 = PC2 A048(G-A060 B1), Q0 = P0 + lin_vel_z -1.5(A043 보상, 1번 점):",
                         "모든 점의 부모 S07 = P0(PC2 A048, track 1.5) + feet_air_time 0.35(G-A063 s07):")
                .replace("부모 Q0", "부모 S07")
                .replace("--hours 18", "--hours 16"))  # 5점 약 12시간 + 여유


@contextlib.contextmanager
def configured():
    """일괄 실행 빌더의 점 목록·부모·이름·안내문을 G-A064로 잠시 바꾼다(끝나면 되돌린다)."""
    keys = ("POINTS", "DESIGN", "PROVISIONAL_WORK_ID", "PARENT_LABEL", "PARENT_HARVEST", "names", "guide")
    saved = {k: getattr(batch, k) for k in keys}
    batch.POINTS, batch.DESIGN, batch.PROVISIONAL_WORK_ID = points(), DESIGN, "G-A064"
    batch.PARENT_LABEL, batch.PARENT_HARVEST = "S07", S07_HARVEST
    batch.names, batch.guide = names, guide
    try:
        yield batch
    finally:
        for k, v in saved.items():
            setattr(batch, k, v)


def build(work_id: str = "G-A064") -> tuple[bytes, dict]:
    with configured():
        return batch.build(work_id)


def main(argv: list[str] | None = None) -> int:
    with configured():
        return batch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
