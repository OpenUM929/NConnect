#!/usr/bin/env python3
"""G-A057 12개 새 학습 행의 실행 전 사전등록 (2026-09-29, Codex 작업 지시 2).

행마다 다음을 **결과 전에** 고정한다.
  change            변경값과 나머지 유지값(SWEEP_PLAN 의 보상 전체)
  source            강좌·배포 원문 출처와 예측 방향.  prediction_type 으로 구분한다:
                      LECTURE_DIRECT   강좌 14 Go2 표·예시에 직접 있는 설명
                      DEPLOY_DIRECT    배포 quadruped_rewards.py 주석·_finalize.py 설명(강좌 Go2 표 밖)
                      MECHANISM_HYPOTHESIS  우리가 식·관측으로 확장한 설명(강좌·배포 원문이 아님)
                      NO_DIRECT_PREDICTION  원문에 이 관측에 대한 직접 예측이 없음
  prior             해당 기준(A048)에서의 관측과 다른 기준의 기존 반례.  A048 위 관측은 12개 모두 없다.
  targets           표적 시나리오와 개선을 판단할 관측(판정 지표)
  protection        감속·정지·다른 시나리오 손실을 확인할 공통 보호 항목(기록, 판정 이름 없음)
  verdict_rules     지지·미지지·판독 불가 기준

문턱은 여기서 한 번 계산해 JSON 에 적고, 판독기(tools/go2_g_a057_prereg_readout.py)는 JSON 만 읽는다.
수치 문턱의 원칙은 기존 탐색 회차와 같다(G-A051·G-A055 사양 `hypothesis.indicators`):
  줄어야 하는 계수  지지 ≤ 기준의 절반(내림), 미지지 ≥ 기준.  그 사이는 INSUFFICIENT('줄었으나 목표 미달').
  늘어야 하는 계수  지지 ≥ 기준과 96 의 중간(올림), 미지지 ≤ 기준.
  연속값(속도·RMSE·높이)  크기 문턱을 두지 않는다.  세 평가 seed 모두 A048 같은 seed 대비 예측 방향이면 지지,
                    모두 반대(또는 같음)면 미지지, 나머지는 INSUFFICIENT.  학습 seed 흔들림은 미측정(U2)이라
                    크기로 판정하지 않는다.
이 문턱은 통계·공식 기준이 아니며 채택 문턱을 바꾸지 않는다.  G-A057 은 채택·승급 대상이 아니다.

    python -B tools/go2_g_a057_preregistration.py          # JSON·MD 작성
    python -B tools/go2_g_a057_preregistration.py --check  # 쓰지 않고 저장본과 같은지 확인
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
import go2_dial_hypothesis as dial  # noqa: E402
import go2_g_a057_sweep_plan as planmod  # noqa: E402

OUT_JSON = QUAD / "config/experiments/G_A057_preregistration.json"
OUT_MD = QUAD / "reports/evidence/go2_g_a057_sweep_plan/PREREGISTRATION.md"
BASE = ROOT / "workspace/_keep" / planmod.BASE_ARM
SEEDS = [101, 202, 303]
ROBOTS = 96
LECT = "workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md"
TRIAL = "workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md"
AIR = "workspace/training/quadruped/reports/GO2_A048_AIR_TIME_CHECK_20260929.md"

STEP = {"stairs_10_down": 0.10, "stairs_15_down": 0.15}


def base_seed_values(kind: str, case: str, field: str | None = None) -> dict[str, float | int]:
    """A048 회수물에서 한 지표의 seed 별 값."""
    if kind == "count":
        metric = "climb_ge2_pooled" if case in STEP else "posture_falls_pooled"
        ind = {"metric": metric, "case": case, "seeds": SEEDS, "robots": ROBOTS, "step_height_m": STEP.get(case)}
        vals = dial.per_seed(BASE, ind)
    else:
        vals = {}
        for s in SEEDS:
            p = dial.cases_dir(BASE) / f"seed_{s}" / case / "summary.json"
            vals[str(s)] = json.loads(p.read_text(encoding="utf-8")).get(field) if p.is_file() else None
    if any(v is None for v in vals.values()):
        raise SystemExit(f"A048 {case} {field or kind} 기록이 없다 — 사전등록 문턱을 계산할 수 없다")
    return vals


def count_ind(case: str, direction: str, note: str) -> dict:
    per = base_seed_values("count", case)
    base = sum(per.values())
    ind = {"kind": "count", "metric": "climb_ge2_pooled" if case in STEP else "posture_falls_pooled", "case": case,
           "seeds": SEEDS, "robots": ROBOTS, "direction": direction, "a048_per_seed": per, "a048_pooled": base,
           "note": note}
    if case in STEP:
        ind["step_height_m"] = STEP[case]
    if direction == "down":
        ind.update(supported_if_at_most=base // 2, not_supported_if_at_least=base,
                   basis=f"A048 {base}/96. 지지 ≤ 절반({base // 2}), 미지지 ≥ A048({base}) — G-A051·G-A055 와 같은 운영 규칙.")
    else:
        up = base + math.ceil((ROBOTS - base) / 2)
        ind.update(supported_if_at_least=up, not_supported_if_at_most=base,
                   basis=f"A048 {base}/96. 지지 ≥ A048 과 96 의 중간({up}), 미지지 ≤ A048({base}).")
    if base == 0 and direction == "down":
        ind["note"] += " A048 이 이미 0 이라 '감소' 지지는 관측될 수 없다 — 판정은 미지지(늘어남 없음=0 은 지지 경계와 같다)로만 읽지 않고 기록으로 본다."
    return ind


def dir_ind(case: str, field: str, direction: str, note: str) -> dict:
    return {"kind": "seed_direction", "case": case, "field": field, "seeds": SEEDS, "direction": direction,
            "a048_per_seed": base_seed_values("field", case, field), "note": note,
            "basis": "세 평가 seed 모두 A048 같은 seed 대비 예측 방향이면 지지, 모두 반대 또는 같음이면 미지지, 나머지 INSUFFICIENT. 크기 문턱 없음."}


# ---- 행별 내용 (원문 인용은 LECT/TRIAL 참고본의 절 번호) -------------------------------------------------
def rows_spec() -> dict[str, dict]:
    track_src = {"prediction_type": "LECTURE_DIRECT",
                 "text": "강좌 14 §3: track 1.0→2.0 '더 빠릿하게 이동해요. 대신 장애물 앞에서 과속해 균형을 잃기 쉬워요'. "
                         "배포 ①: '↑ 빠릿하게 멀리 이동 / ↓ 천천히·안정적 / ⚠️ 너무 높이면 험지/장애물서 자세 무너짐'.",
                 "cite": f"{LECT} §3·§6"}
    track_prior = ("A048 위 관측 없음. 다른 기준: A033 위 1.5→1.6(A042) 10cm ≥2단 43→0, 10cm 낙상 34→85, 험지 전진 낙상 4→20, "
                   "험지 전진 속도 0.37→0.24(1단계). Pilot→A017→A033(1.2→1.4→1.5) 험지 전진 속도 0.26→0.27→0.37, "
                   "같은 두 인상에서 험지 옆걸음 종료 48→58.")
    ang_src_strong = {"prediction_type": "DEPLOY_DIRECT",
                      "text": "강좌 14 Go2 표: ang_vel_xy_l2 '몸통을 기울이지 마라'(−). 배포 ④: '강하게: 덜 휘청 (안정) / 약하게: 흔들림 허용 (험지 적응 여지)'. "
                              "생성기: 내림(강화) '흔들림 억제 ↑ 안정'.",
                      "cite": f"{LECT} §1·§6·§6-b"}
    feet_src = {"prediction_type": "DEPLOY_DIRECT",
                "text": "강좌 14 Go2 표: feet_air_time '발을 적당히 들었다 놓으라'(+). 배포 ②: '↑ 발을 높이 들어 험지 돌파 유리 (0.5+ 면 바운딩 가능성) / "
                        "↓ 발을 거의 안 들고 끌듯이 걸음 (너무 낮으면 못 걷고 제자리 가능성)'. 생성기: 올림 '발 높이 ↑ 등반 유리', 내림 '발 낮게 ↓ 평지안정·등반약'.",
                "cite": f"{LECT} §1·§6·§6-b"}
    feet_mech = ("기전 가설(원문 아님): 식은 착지 때 (체공 − 0.5초)를 더한다. A048 착지의 97.5~99.7%에서 이 항이 음수다"
                 f"({AIR} §3). 발 높이는 평가기가 재지 않는다 — '발을 높이 든다'는 이 탐색에서 미측정이다.")
    feet_prior = ("A048 위 관측 없음. 다른 기준: Pilot-01 위 0.2→0.35(A015) 몸 높이 6/7 case 하락, 험지 낙상 6→32/32, 경사 +20° 0→32. "
                  "A017 위 0.2→0.01(A031) 표적 proxy −0.022, 0.2→0.1(A032) 표적 proxy −0.437·험지 전진 종료 0→2.33·경사 +20° 낙상 71(1단계). "
                  "0.1 이 세 값 중 가장 나빴다(값 순서와 결과가 한 방향이 아님).")
    act_prior = "A048 위 관측 없음. 다른 기준: Pilot-01 위 −0.01→−0.008(A018) 7 case 전부 거의 정지, 평지 고속 속도 1.17→0.03. 강화(−0.012) 방향은 어느 기준에서도 측정한 적 없음."
    flat_src = {"prediction_type": "DEPLOY_DIRECT",
                "text": "강좌 14 Go2 표에 없다(H1 표에만 '몸통을 똑바로 유지'). 배포 원본 주석: '몸통 수평 유지. ↑(강) 안정 / ↓(약) 험지 적응'. "
                        "생성기: 내림(강화) '자세 ↑ 꼿꼿·안정·소극'. 로컬 '계단에서 덜 넘어짐' 주석은 우리가 덧붙인 것이라 출처로 쓰지 않는다.",
                "cite": f"{LECT} §1·§6 ⑥·§6-b"}
    flat_prior = ("A048 위 관측 없음. 다른 기준: A033 위 0→−0.5(A047) 험지 옆걸음 낙상 59→60(감소 없음), 험지 전진 속도 0.366→0.192, "
                  "10cm ≥2단 43→0, 15cm 낙상 90→8(오르지 않아서), DR 낙상 1→13.")
    return {
        "track_lin_vel_xy_exp_p1p6": {
            "source": {**track_src, "direction": "속도↑(빠릿하게) / 험지·장애물 앞 자세 무너짐 위험"},
            "prior": track_prior,
            "targets": {"rough_forward_speed_up": dir_ind("rough_forward", "speed_xy_mean", "up",
                                                          "험지 전진에서 '빠릿하게' — 명령 추종 강조로 속도가 오르는가."),
                        "stairs_10_ge2_down_risk": count_ind("stairs_10_down", "down",
                                                              "강좌 경고 '장애물 앞 과속해 균형을 잃기 쉬움'의 확인 지표. 지지 = 경고가 A048 에서도 나타남(손실).")},
        },
        "track_lin_vel_xy_exp_p1p4": {
            "source": {**track_src, "direction": "속도↓ · 안정↑(천천히·안정적)"},
            "prior": track_prior,
            "targets": {"rough_lateral_falls_down": count_ind("rough_lateral", "down", "'천천히·안정적'의 험지 옆걸음 자세 낙상 감소."),
                        "rough_forward_speed_down_cost": dir_ind("rough_forward", "speed_xy_mean", "down",
                                                                  "'천천히'의 확인 지표. 지지 = 예측된 감속이 나타남(비용).")},
        },
        "track_lin_vel_xy_exp_p1p2": {
            "source": {**track_src, "direction": "속도↓ · 안정↑(천천히·안정적), 1.4 보다 큰 변경"},
            "prior": track_prior,
            "targets": {"rough_lateral_falls_down": count_ind("rough_lateral", "down", "'천천히·안정적'의 험지 옆걸음 자세 낙상 감소."),
                        "rough_forward_speed_down_cost": dir_ind("rough_forward", "speed_xy_mean", "down",
                                                                  "'천천히'의 확인 지표. 지지 = 예측된 감속이 나타남(비용).")},
        },
        "ang_vel_xy_l2_m0p08": {
            "source": {**ang_src_strong, "direction": "강화: 덜 휘청(안정)"},
            "prior": ("A048 위 관측 없음. 다른 기준에서 방향이 뒤집혔다: A033 위(A038) 험지 옆걸음 낙상 59→18, A043 위(A055) 24→50. "
                      "두 기준 모두 10cm ≥2단 붕괴(43→0, 94→2). A043 위 우회전 낙상 29→0."),
            "targets": {"rough_lateral_falls_down": count_ind("rough_lateral", "down", "'덜 휘청'의 험지 옆걸음 자세 낙상 감소.")},
        },
        "ang_vel_xy_l2_m0p04": {
            "source": {**ang_src_strong, "direction": "완화: 흔들림 허용(험지 적응 여지)"},
            "prior": "A048 위 관측 없음. 다른 기준: A033 위(A041, 1단계) 험지 옆걸음 낙상 59→52, 험지 전진 낙상 4→8, 10cm ≥2단 43→8, 10cm 낙상 34→93.",
            "targets": {"rough_lateral_falls_down": count_ind("rough_lateral", "down",
                                                               "'험지 적응 여지'를 험지 옆걸음 자세 낙상 감소로 읽는다. 원문은 방향만 말하고 어느 관측이 좋아지는지 특정하지 않는다."),
                        "rough_forward_speed_up": dir_ind("rough_forward", "speed_xy_mean", "up", "'험지 적응 여지'의 두 번째 읽기: 험지 전진 속도.")},
        },
        "feet_air_time_p0p35": {
            "source": {**feet_src, "direction": "올림: 발 높이↑ · 험지 돌파·등반 유리(0.5+ 바운딩 경고)"},
            "prior": feet_prior,
            "mechanism_hypothesis": feet_mech + " 올리면 짧은 착지 비용이 커져 착지 감소·몸 낮춤(A015 경로)이 경쟁 예측이다.",
            "targets": {"stairs_15_ge2_up": count_ind("stairs_15_down", "up", "배포 '등반 유리'의 15cm 오르기."),
                        "rough_forward_speed_up": dir_ind("rough_forward", "speed_xy_mean", "up", "배포 '험지 돌파 유리'."),
                        "rough_height_down_competing": dir_ind("rough_forward", "height_rel_median", "down",
                                                                "경쟁 예측(기전 가설, A015 경로): 몸 낮춤. 지지 = 경쟁 예측이 나타남.")},
        },
        "feet_air_time_p0p1": {
            "source": {**feet_src, "direction": "내림: 발 낮게 · 평지 안정 · 등반 약"},
            "prior": feet_prior,
            "mechanism_hypothesis": feet_mech + " 내리면 짧은 착지 비용이 줄어 재착지가 덜 억제될 수 있다는 설명은 기전 가설이며 계단 개선 우선 근거가 아니다(Codex 정정 2026-09-29).",
            "targets": {"stairs_15_ge2_down_cost": count_ind("stairs_15_down", "down", "배포 '등반약'의 확인 지표. 지지 = 예측된 손실이 나타남."),
                        "rough_lateral_falls_down_mech": count_ind("rough_lateral", "down", "기전 가설(재착지 덜 억제)의 험지 옆걸음 낙상 감소.")},
            "no_direct_prediction": "배포 '평지 안정'은 A048 평지 생존이 이미 1.0 이라 개선을 관측할 여지가 없다 — 판정 지표로 두지 않는다.",
        },
        "feet_air_time_p0p01": {
            "source": {**feet_src, "direction": "내림: 발 낮게 · 평지 안정 · 등반 약(너무 낮으면 제자리)"},
            "prior": feet_prior,
            "mechanism_hypothesis": feet_mech + " 내리면 짧은 착지 비용이 줄어 재착지가 덜 억제될 수 있다는 설명은 기전 가설이며 계단 개선 우선 근거가 아니다(Codex 정정 2026-09-29). 0.01 은 Isaac Lab Go2 rough 값이지만 계단 성능 근거가 아니다.",
            "targets": {"stairs_15_ge2_down_cost": count_ind("stairs_15_down", "down", "배포 '등반약'의 확인 지표. 지지 = 예측된 손실이 나타남."),
                        "rough_lateral_falls_down_mech": count_ind("rough_lateral", "down", "기전 가설(재착지 덜 억제)의 험지 옆걸음 낙상 감소.")},
            "no_direct_prediction": "배포 '평지 안정'은 A048 평지 생존이 이미 1.0 이라 개선을 관측할 여지가 없다 — 판정 지표로 두지 않는다.",
        },
        "action_rate_l2_m0p008": {
            "source": {"prediction_type": "DEPLOY_DIRECT",
                       "text": "강좌 14 Go2 표: action_rate_l2 '명령을 급격히 바꾸지 마라 (부드러움)'. 배포 ⑤: '강하게: 부드럽지만 굼뜬 반응 / 약하게: 민첩하지만 다리 떨림'.",
                       "cite": f"{LECT} §1·§4·§6", "direction": "완화: 민첩 · 다리 떨림"},
            "prior": act_prior,
            "targets": {"yaw_right_tracking_yaw_down": dir_ind("combined_yaw_right", "tracking_yaw_rmse", "down",
                                                               "'민첩'을 복합 우회전의 회전 추종 오차 감소로 읽는다.")},
            "no_direct_prediction": "'다리 떨림'은 평가기에 채널이 없어 미측정이다.",
        },
        "action_rate_l2_m0p012": {
            "source": {"prediction_type": "DEPLOY_DIRECT",
                       "text": "강좌 14 Go2 표: action_rate_l2 '명령을 급격히 바꾸지 마라 (부드러움)'. 배포 ⑤: '강하게: 부드럽지만 굼뜬 반응'.",
                       "cite": f"{LECT} §1·§6", "direction": "강화: 부드러움 · 굼뜸"},
            "prior": act_prior,
            "targets": {"yaw_right_tracking_yaw_up_cost": dir_ind("combined_yaw_right", "tracking_yaw_rmse", "up",
                                                                   "'굼뜬 반응'의 확인 지표. 지지 = 예측된 비용이 나타남.")},
            "no_direct_prediction": "개선 쪽 예측('부드러움')은 평가기에 채널이 없어 직접 예측 없음 — 표적 개선 지표를 두지 않는다.",
        },
        "flat_orientation_l2_m0p25": {
            "source": {**flat_src, "direction": "강화: 안정 · 꼿꼿 · 소극(험지 적응 ↓)"},
            "prior": flat_prior,
            "targets": {"rough_lateral_falls_down": count_ind("rough_lateral", "down", "'안정'의 험지 옆걸음 자세 낙상 감소."),
                        "rough_forward_speed_down_cost": dir_ind("rough_forward", "speed_xy_mean", "down", "'소극'의 확인 지표. 지지 = 예측된 감속.")},
        },
        "flat_orientation_l2_m0p5": {
            "source": {**flat_src, "direction": "강화: 안정 · 꼿꼿 · 소극(험지 적응 ↓), −0.25 보다 큰 변경"},
            "prior": flat_prior,
            "targets": {"rough_lateral_falls_down": count_ind("rough_lateral", "down", "'안정'의 험지 옆걸음 자세 낙상 감소."),
                        "rough_forward_speed_down_cost": dir_ind("rough_forward", "speed_xy_mean", "down", "'소극'의 확인 지표. 지지 = 예측된 감속.")},
        },
    }


def protection() -> dict:
    """모든 행 공통 보호 항목: 기록만 하고 판정 이름을 붙이지 않는다.  3 seed 일치 악화만 표시한다."""
    return {
        "moving_gate": {"kind": "moving", "case": "forward_nominal", "seed": 101,
                        "note": "러너의 정지 판정(candidate_suite_checks.py moving)과 같은 규칙. 정지면 평가 후 후보 제외 사유다(실행 중 중단 아님 — 러너는 69 case 를 끝까지 수집한다)."},
        "forward_speed": dir_ind("forward_nominal", "speed_xy_mean", "down", "평지 전진 감속"),
        "rough_forward_speed": dir_ind("rough_forward", "speed_xy_mean", "down", "험지 전진 감속"),
        "yaw_right_speed": dir_ind("combined_yaw_right", "speed_xy_mean", "down", "복합 우회전 감속"),
        "rough_lateral_falls": count_ind("rough_lateral", "up", "험지 옆걸음 낙상 증가"),
        "rough_forward_falls": count_ind("rough_forward", "up", "험지 전진 낙상 증가"),
        "yaw_right_falls": count_ind("combined_yaw_right", "up", "복합 우회전 낙상 증가"),
        "slope_plus_20_falls": count_ind("slope_plus_20", "up", "경사 +20° 낙상 증가"),
        "push_neg_y_falls": count_ind("push_neg_y", "up", "밀침(−y) 낙상 증가 — A048 밀침 낙상 1건이 난 방향"),
        "stairs_10_ge2": count_ind("stairs_10_down", "down", "10cm ≥2단 감소"),
        "stairs_15_ge2": count_ind("stairs_15_down", "down", "15cm ≥2단 감소"),
        "axis_scores": {"kind": "axis_scores", "note": "G1~G7 점수·총 내부 proxy 는 tools/go2_g_a057_sweep_compare.py 가 낸다. 총점만으로 승자를 정하지 않는다."},
        "stairs_stall": {"kind": "compare_tool", "note": "계단 정체 로봇 수는 비교 도구의 stairs_*_stall 열."},
    }


VERDICT_RULES = {
    "SUPPORTED": "지지 — 표적 지표가 사전등록 문턱을 넘었다. 이 학습 1회(seed 42)에서 예측과 일치했다는 뜻이며 효과 확정이 아니다.",
    "NOT_SUPPORTED": "미지지 — 표적 지표가 A048 수준 이하(예측 방향의 변화 없음) 또는 세 seed 모두 반대 방향.",
    "INSUFFICIENT": "중간 — 경계 안. '반증을 피한 것은 지지가 아니다'. '줄었으나 목표 미달'처럼 수를 그대로 보고한다.",
    "MISSING": "판독 불가(지표) — 그 지표의 case·seed 기록이 없거나 로봇 수가 32 가 아니다. 다른 지표의 판정은 지우지 않는다.",
    "UNREADABLE_RUN": "판독 불가(실행) — RESULT_STATUS 가 FULL/FULL_69_COMPLETE 가 아니거나 실행이 안전 중단·오류로 끝났다. 모든 지표를 판정하지 않는다.",
    "cost_indicators": "이름이 _cost·_risk 로 끝나는 지표는 원문이 경고한 손실의 확인 지표다. 지지 = 손실이 나타남.",
    "exclusion_after_evaluation": "평가 후 후보 제외(다음 선택 목록에서 뺀다): ① 정지 정책(moving_gate STATIONARY) ② 개선 표적 지표가 모두 NOT_SUPPORTED. 보호 항목의 3 seed 일치 악화는 제외 사유로 자동 적용하지 않고 옆에 적는다 — 다음 선택은 Codex 가 한다.",
    "run_safety_stop": "실행 중 안전 중단(평가 결과와 무관): 학습 loss 비유한(CATASTROPHE_TRAINING_NONFINITE), 디스크 부족, 다른 학습 프로세스, 환경 없음, 학습 시작 전 실패, 두 실행 연속 학습 실패, 패키지 체크섬 불일치. 러너·일괄 러너는 성능이 나쁘다는 이유로 중단하지 않는다.",
    "no_winner": "총 내부 proxy 는 함께 비교하되 총점만으로 승자를 정하지 않고, 한 seed 의 결과를 최적값으로 확정하지 않는다.",
}


def build() -> dict:
    plan = planmod.plan()
    new = {r["key"]: r for r in plan["runs"] if r["status"] == "NEW_TRAIN"}
    spec = rows_spec()
    if set(spec) != set(new):
        raise SystemExit(f"사전등록 행 {sorted(spec)} != SWEEP_PLAN NEW_TRAIN {sorted(new)}")
    base6 = {k: plan["base_env_rewards"][k] for k in planmod.GRID}
    rows = {}
    for key, row in new.items():
        s = spec[key]
        held = {k: v for k, v in row["rewards"].items() if k != row["variable"]}
        rows[key] = {"change": {"name": row["variable"], "from": base6[row["variable"]], "to": row["value"], "held": held},
                     **s}
    return {"work_id": "G-A057", "schema": "go2_g_a057_prereg_v1", "base_arm": planmod.BASE_ARM,
            "reader": "tools/go2_g_a057_prereg_readout.py", "promotion": "forbidden_sweep_data_only",
            "training_seed": 42, "evaluation_seeds": SEEDS,
            "limits": "모든 행이 학습 seed 42 한 번이다. 학습 seed 흔들림은 미측정(U2)이므로 지지는 '이 1회에서 예측과 일치'일 뿐이다.",
            "verdict_rules": VERDICT_RULES, "protection": protection(), "rows": rows}


def markdown(pre: dict) -> str:
    L = ["# G-A057 사전등록 (자동 생성: tools/go2_g_a057_preregistration.py)", "",
         f"- 기준 정책 {pre['base_arm']}. 학습 seed 42 한 번. {pre['limits']}",
         "- 판정 규칙:"] + [f"  - {k}: {v}" for k, v in pre["verdict_rules"].items()] + [""]
    for key, r in pre["rows"].items():
        c = r["change"]
        L += [f"## {key}", "",
              f"- 변경: {c['name']} {c['from']:g} → {c['to']:g}. 유지: " + ", ".join(f"{k} {v:g}" for k, v in c["held"].items() if v is not None),
              f"- 출처({r['source']['prediction_type']}): {r['source']['text']} [{r['source']['cite']}]",
              f"- 예측 방향: {r['source']['direction']}",
              f"- 기존 관측·반례: {r['prior']}"]
        if r.get("mechanism_hypothesis"):
            L.append(f"- 기전 가설(원문 아님): {r['mechanism_hypothesis']}")
        if r.get("no_direct_prediction"):
            L.append(f"- 직접 예측 없음: {r['no_direct_prediction']}")
        L.append("- 표적 지표:")
        for name, t in r["targets"].items():
            if t["kind"] == "count":
                thr = (f"지지 ≤{t['supported_if_at_most']}, 미지지 ≥{t['not_supported_if_at_least']}" if t["direction"] == "down"
                       else f"지지 ≥{t['supported_if_at_least']}, 미지지 ≤{t['not_supported_if_at_most']}")
                L.append(f"  - {name}: {t['case']} {t['metric']} A048 {t['a048_pooled']} → {thr}. {t['note']}")
            else:
                L.append(f"  - {name}: {t['case']} {t['field']} {t['direction']} (3 seed 방향). {t['note']}")
        L.append("")
    L += ["## 공통 보호 항목 (기록, 3 seed 일치 악화만 표시)", ""]
    for name, p in pre["protection"].items():
        L.append(f"- {name}: {p.get('case', '')} {p.get('note', '')}")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    pre = build()
    text = json.dumps(pre, ensure_ascii=False, indent=1) + "\n"
    if a.check:
        same = OUT_JSON.is_file() and OUT_JSON.read_text(encoding="utf-8") == text
        print("PREREG_UP_TO_DATE" if same else "PREREG_STALE")
        return 0 if same else 1
    OUT_JSON.write_text(text, encoding="utf-8", newline="\n")
    OUT_MD.write_text(markdown(pre), encoding="utf-8", newline="\n")
    print(json.dumps({"rows": len(pre["rows"]), "json": str(OUT_JSON), "md": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
