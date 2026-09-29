# G-A057 사전등록 (자동 생성: tools/go2_g_a057_preregistration.py)

- 기준 정책 go2_g_a048_a033_lin_vel_z_m125. 학습 seed 42 한 번. 모든 행이 학습 seed 42 한 번이다. 학습 seed 흔들림은 미측정(U2)이므로 지지는 '이 1회에서 예측과 일치'일 뿐이다.
- 판정 규칙:
  - SUPPORTED: 지지 — 표적 지표가 사전등록 문턱을 넘었다. 이 학습 1회(seed 42)에서 예측과 일치했다는 뜻이며 효과 확정이 아니다.
  - NOT_SUPPORTED: 미지지 — 표적 지표가 A048 수준 이하(예측 방향의 변화 없음) 또는 세 seed 모두 반대 방향.
  - INSUFFICIENT: 중간 — 경계 안. '반증을 피한 것은 지지가 아니다'. '줄었으나 목표 미달'처럼 수를 그대로 보고한다.
  - MISSING: 판독 불가(지표) — 그 지표의 case·seed 기록이 없거나 로봇 수가 32 가 아니다. 다른 지표의 판정은 지우지 않는다.
  - UNREADABLE_RUN: 판독 불가(실행) — RESULT_STATUS 가 FULL/FULL_69_COMPLETE 가 아니거나 실행이 안전 중단·오류로 끝났다. 모든 지표를 판정하지 않는다.
  - cost_indicators: 이름이 _cost·_risk 로 끝나는 지표는 원문이 경고한 손실의 확인 지표다. 지지 = 손실이 나타남.
  - exclusion_after_evaluation: 평가 후 후보 제외(다음 선택 목록에서 뺀다): ① 정지 정책(moving_gate STATIONARY) ② 개선 표적 지표가 모두 NOT_SUPPORTED. 보호 항목의 3 seed 일치 악화는 제외 사유로 자동 적용하지 않고 옆에 적는다 — 다음 선택은 Codex 가 한다.
  - run_safety_stop: 실행 중 안전 중단(평가 결과와 무관): 학습 loss 비유한(CATASTROPHE_TRAINING_NONFINITE), 디스크 부족, 다른 학습 프로세스, 환경 없음, 학습 시작 전 실패, 두 실행 연속 학습 실패, 패키지 체크섬 불일치. 러너·일괄 러너는 성능이 나쁘다는 이유로 중단하지 않는다.
  - no_winner: 총 내부 proxy 는 함께 비교하되 총점만으로 승자를 정하지 않고, 한 seed 의 결과를 최적값으로 확정하지 않는다.

## track_lin_vel_xy_exp_p1p2

- 변경: track_lin_vel_xy_exp 1.5 → 1.2. 유지: feet_air_time 0.2, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(LECTURE_DIRECT): 강좌 14 §3: track 1.0→2.0 '더 빠릿하게 이동해요. 대신 장애물 앞에서 과속해 균형을 잃기 쉬워요'. 배포 ①: '↑ 빠릿하게 멀리 이동 / ↓ 천천히·안정적 / ⚠️ 너무 높이면 험지/장애물서 자세 무너짐'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §3·§6]
- 예측 방향: 속도↓ · 안정↑(천천히·안정적), 1.4 보다 큰 변경
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: A033 위 1.5→1.6(A042) 10cm ≥2단 43→0, 10cm 낙상 34→85, 험지 전진 낙상 4→20, 험지 전진 속도 0.37→0.24(1단계). Pilot→A017→A033(1.2→1.4→1.5) 험지 전진 속도 0.26→0.27→0.37, 같은 두 인상에서 험지 옆걸음 종료 48→58.
- 표적 지표:
  - rough_lateral_falls_down: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. '천천히·안정적'의 험지 옆걸음 자세 낙상 감소.
  - rough_forward_speed_down_cost: rough_forward speed_xy_mean down (3 seed 방향). '천천히'의 확인 지표. 지지 = 예측된 감속이 나타남(비용).

## track_lin_vel_xy_exp_p1p4

- 변경: track_lin_vel_xy_exp 1.5 → 1.4. 유지: feet_air_time 0.2, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(LECTURE_DIRECT): 강좌 14 §3: track 1.0→2.0 '더 빠릿하게 이동해요. 대신 장애물 앞에서 과속해 균형을 잃기 쉬워요'. 배포 ①: '↑ 빠릿하게 멀리 이동 / ↓ 천천히·안정적 / ⚠️ 너무 높이면 험지/장애물서 자세 무너짐'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §3·§6]
- 예측 방향: 속도↓ · 안정↑(천천히·안정적)
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: A033 위 1.5→1.6(A042) 10cm ≥2단 43→0, 10cm 낙상 34→85, 험지 전진 낙상 4→20, 험지 전진 속도 0.37→0.24(1단계). Pilot→A017→A033(1.2→1.4→1.5) 험지 전진 속도 0.26→0.27→0.37, 같은 두 인상에서 험지 옆걸음 종료 48→58.
- 표적 지표:
  - rough_lateral_falls_down: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. '천천히·안정적'의 험지 옆걸음 자세 낙상 감소.
  - rough_forward_speed_down_cost: rough_forward speed_xy_mean down (3 seed 방향). '천천히'의 확인 지표. 지지 = 예측된 감속이 나타남(비용).

## track_lin_vel_xy_exp_p1p6

- 변경: track_lin_vel_xy_exp 1.5 → 1.6. 유지: feet_air_time 0.2, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(LECTURE_DIRECT): 강좌 14 §3: track 1.0→2.0 '더 빠릿하게 이동해요. 대신 장애물 앞에서 과속해 균형을 잃기 쉬워요'. 배포 ①: '↑ 빠릿하게 멀리 이동 / ↓ 천천히·안정적 / ⚠️ 너무 높이면 험지/장애물서 자세 무너짐'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §3·§6]
- 예측 방향: 속도↑(빠릿하게) / 험지·장애물 앞 자세 무너짐 위험
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: A033 위 1.5→1.6(A042) 10cm ≥2단 43→0, 10cm 낙상 34→85, 험지 전진 낙상 4→20, 험지 전진 속도 0.37→0.24(1단계). Pilot→A017→A033(1.2→1.4→1.5) 험지 전진 속도 0.26→0.27→0.37, 같은 두 인상에서 험지 옆걸음 종료 48→58.
- 표적 지표:
  - rough_forward_speed_up: rough_forward speed_xy_mean up (3 seed 방향). 험지 전진에서 '빠릿하게' — 명령 추종 강조로 속도가 오르는가.
  - stairs_10_ge2_down_risk: stairs_10_down climb_ge2_pooled A048 90 → 지지 ≤45, 미지지 ≥90. 강좌 경고 '장애물 앞 과속해 균형을 잃기 쉬움'의 확인 지표. 지지 = 경고가 A048 에서도 나타남(손실).

## ang_vel_xy_l2_m0p04

- 변경: ang_vel_xy_l2 -0.05 → -0.04. 유지: track_lin_vel_xy_exp 1.5, feet_air_time 0.2, lin_vel_z_l2 -1.25, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표: ang_vel_xy_l2 '몸통을 기울이지 마라'(−). 배포 ④: '강하게: 덜 휘청 (안정) / 약하게: 흔들림 허용 (험지 적응 여지)'. 생성기: 내림(강화) '흔들림 억제 ↑ 안정'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6·§6-b]
- 예측 방향: 완화: 흔들림 허용(험지 적응 여지)
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: A033 위(A041, 1단계) 험지 옆걸음 낙상 59→52, 험지 전진 낙상 4→8, 10cm ≥2단 43→8, 10cm 낙상 34→93.
- 표적 지표:
  - rough_lateral_falls_down: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. '험지 적응 여지'를 험지 옆걸음 자세 낙상 감소로 읽는다. 원문은 방향만 말하고 어느 관측이 좋아지는지 특정하지 않는다.
  - rough_forward_speed_up: rough_forward speed_xy_mean up (3 seed 방향). '험지 적응 여지'의 두 번째 읽기: 험지 전진 속도.

## ang_vel_xy_l2_m0p08

- 변경: ang_vel_xy_l2 -0.05 → -0.08. 유지: track_lin_vel_xy_exp 1.5, feet_air_time 0.2, lin_vel_z_l2 -1.25, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표: ang_vel_xy_l2 '몸통을 기울이지 마라'(−). 배포 ④: '강하게: 덜 휘청 (안정) / 약하게: 흔들림 허용 (험지 적응 여지)'. 생성기: 내림(강화) '흔들림 억제 ↑ 안정'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6·§6-b]
- 예측 방향: 강화: 덜 휘청(안정)
- 기존 관측·반례: A048 위 관측 없음. 다른 기준에서 방향이 뒤집혔다: A033 위(A038) 험지 옆걸음 낙상 59→18, A043 위(A055) 24→50. 두 기준 모두 10cm ≥2단 붕괴(43→0, 94→2). A043 위 우회전 낙상 29→0.
- 표적 지표:
  - rough_lateral_falls_down: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. '덜 휘청'의 험지 옆걸음 자세 낙상 감소.

## feet_air_time_p0p01

- 변경: feet_air_time 0.2 → 0.01. 유지: track_lin_vel_xy_exp 1.5, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표: feet_air_time '발을 적당히 들었다 놓으라'(+). 배포 ②: '↑ 발을 높이 들어 험지 돌파 유리 (0.5+ 면 바운딩 가능성) / ↓ 발을 거의 안 들고 끌듯이 걸음 (너무 낮으면 못 걷고 제자리 가능성)'. 생성기: 올림 '발 높이 ↑ 등반 유리', 내림 '발 낮게 ↓ 평지안정·등반약'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6·§6-b]
- 예측 방향: 내림: 발 낮게 · 평지 안정 · 등반 약(너무 낮으면 제자리)
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: Pilot-01 위 0.2→0.35(A015) 몸 높이 6/7 case 하락, 험지 낙상 6→32/32, 경사 +20° 0→32. A017 위 0.2→0.01(A031) 표적 proxy −0.022, 0.2→0.1(A032) 표적 proxy −0.437·험지 전진 종료 0→2.33·경사 +20° 낙상 71(1단계). 0.1 이 세 값 중 가장 나빴다(값 순서와 결과가 한 방향이 아님).
- 기전 가설(원문 아님): 기전 가설(원문 아님): 식은 착지 때 (체공 − 0.5초)를 더한다. A048 착지의 97.5~99.7%에서 이 항이 음수다(workspace/training/quadruped/reports/GO2_A048_AIR_TIME_CHECK_20260929.md §3). 발 높이는 평가기가 재지 않는다 — '발을 높이 든다'는 이 탐색에서 미측정이다. 내리면 짧은 착지 비용이 줄어 재착지가 덜 억제될 수 있다는 설명은 기전 가설이며 계단 개선 우선 근거가 아니다(Codex 정정 2026-09-29). 0.01 은 Isaac Lab Go2 rough 값이지만 계단 성능 근거가 아니다.
- 직접 예측 없음: 배포 '평지 안정'은 A048 평지 생존이 이미 1.0 이라 개선을 관측할 여지가 없다 — 판정 지표로 두지 않는다.
- 표적 지표:
  - stairs_15_ge2_down_cost: stairs_15_down climb_ge2_pooled A048 24 → 지지 ≤12, 미지지 ≥24. 배포 '등반약'의 확인 지표. 지지 = 예측된 손실이 나타남.
  - rough_lateral_falls_down_mech: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. 기전 가설(재착지 덜 억제)의 험지 옆걸음 낙상 감소.

## feet_air_time_p0p1

- 변경: feet_air_time 0.2 → 0.1. 유지: track_lin_vel_xy_exp 1.5, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표: feet_air_time '발을 적당히 들었다 놓으라'(+). 배포 ②: '↑ 발을 높이 들어 험지 돌파 유리 (0.5+ 면 바운딩 가능성) / ↓ 발을 거의 안 들고 끌듯이 걸음 (너무 낮으면 못 걷고 제자리 가능성)'. 생성기: 올림 '발 높이 ↑ 등반 유리', 내림 '발 낮게 ↓ 평지안정·등반약'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6·§6-b]
- 예측 방향: 내림: 발 낮게 · 평지 안정 · 등반 약
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: Pilot-01 위 0.2→0.35(A015) 몸 높이 6/7 case 하락, 험지 낙상 6→32/32, 경사 +20° 0→32. A017 위 0.2→0.01(A031) 표적 proxy −0.022, 0.2→0.1(A032) 표적 proxy −0.437·험지 전진 종료 0→2.33·경사 +20° 낙상 71(1단계). 0.1 이 세 값 중 가장 나빴다(값 순서와 결과가 한 방향이 아님).
- 기전 가설(원문 아님): 기전 가설(원문 아님): 식은 착지 때 (체공 − 0.5초)를 더한다. A048 착지의 97.5~99.7%에서 이 항이 음수다(workspace/training/quadruped/reports/GO2_A048_AIR_TIME_CHECK_20260929.md §3). 발 높이는 평가기가 재지 않는다 — '발을 높이 든다'는 이 탐색에서 미측정이다. 내리면 짧은 착지 비용이 줄어 재착지가 덜 억제될 수 있다는 설명은 기전 가설이며 계단 개선 우선 근거가 아니다(Codex 정정 2026-09-29).
- 직접 예측 없음: 배포 '평지 안정'은 A048 평지 생존이 이미 1.0 이라 개선을 관측할 여지가 없다 — 판정 지표로 두지 않는다.
- 표적 지표:
  - stairs_15_ge2_down_cost: stairs_15_down climb_ge2_pooled A048 24 → 지지 ≤12, 미지지 ≥24. 배포 '등반약'의 확인 지표. 지지 = 예측된 손실이 나타남.
  - rough_lateral_falls_down_mech: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. 기전 가설(재착지 덜 억제)의 험지 옆걸음 낙상 감소.

## feet_air_time_p0p35

- 변경: feet_air_time 0.2 → 0.35. 유지: track_lin_vel_xy_exp 1.5, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01, flat_orientation_l2 0
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표: feet_air_time '발을 적당히 들었다 놓으라'(+). 배포 ②: '↑ 발을 높이 들어 험지 돌파 유리 (0.5+ 면 바운딩 가능성) / ↓ 발을 거의 안 들고 끌듯이 걸음 (너무 낮으면 못 걷고 제자리 가능성)'. 생성기: 올림 '발 높이 ↑ 등반 유리', 내림 '발 낮게 ↓ 평지안정·등반약'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6·§6-b]
- 예측 방향: 올림: 발 높이↑ · 험지 돌파·등반 유리(0.5+ 바운딩 경고)
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: Pilot-01 위 0.2→0.35(A015) 몸 높이 6/7 case 하락, 험지 낙상 6→32/32, 경사 +20° 0→32. A017 위 0.2→0.01(A031) 표적 proxy −0.022, 0.2→0.1(A032) 표적 proxy −0.437·험지 전진 종료 0→2.33·경사 +20° 낙상 71(1단계). 0.1 이 세 값 중 가장 나빴다(값 순서와 결과가 한 방향이 아님).
- 기전 가설(원문 아님): 기전 가설(원문 아님): 식은 착지 때 (체공 − 0.5초)를 더한다. A048 착지의 97.5~99.7%에서 이 항이 음수다(workspace/training/quadruped/reports/GO2_A048_AIR_TIME_CHECK_20260929.md §3). 발 높이는 평가기가 재지 않는다 — '발을 높이 든다'는 이 탐색에서 미측정이다. 올리면 짧은 착지 비용이 커져 착지 감소·몸 낮춤(A015 경로)이 경쟁 예측이다.
- 표적 지표:
  - stairs_15_ge2_up: stairs_15_down climb_ge2_pooled A048 24 → 지지 ≥60, 미지지 ≤24. 배포 '등반 유리'의 15cm 오르기.
  - rough_forward_speed_up: rough_forward speed_xy_mean up (3 seed 방향). 배포 '험지 돌파 유리'.
  - rough_height_down_competing: rough_forward height_rel_median down (3 seed 방향). 경쟁 예측(기전 가설, A015 경로): 몸 낮춤. 지지 = 경쟁 예측이 나타남.

## action_rate_l2_m0p008

- 변경: action_rate_l2 -0.01 → -0.008. 유지: track_lin_vel_xy_exp 1.5, feet_air_time 0.2, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, flat_orientation_l2 0
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표: action_rate_l2 '명령을 급격히 바꾸지 마라 (부드러움)'. 배포 ⑤: '강하게: 부드럽지만 굼뜬 반응 / 약하게: 민첩하지만 다리 떨림'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§4·§6]
- 예측 방향: 완화: 민첩 · 다리 떨림
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: Pilot-01 위 −0.01→−0.008(A018) 7 case 전부 거의 정지, 평지 고속 속도 1.17→0.03. 강화(−0.012) 방향은 어느 기준에서도 측정한 적 없음.
- 직접 예측 없음: '다리 떨림'은 평가기에 채널이 없어 미측정이다.
- 표적 지표:
  - yaw_right_tracking_yaw_down: combined_yaw_right tracking_yaw_rmse down (3 seed 방향). '민첩'을 복합 우회전의 회전 추종 오차 감소로 읽는다.

## action_rate_l2_m0p012

- 변경: action_rate_l2 -0.01 → -0.012. 유지: track_lin_vel_xy_exp 1.5, feet_air_time 0.2, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, flat_orientation_l2 0
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표: action_rate_l2 '명령을 급격히 바꾸지 마라 (부드러움)'. 배포 ⑤: '강하게: 부드럽지만 굼뜬 반응'. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6]
- 예측 방향: 강화: 부드러움 · 굼뜸
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: Pilot-01 위 −0.01→−0.008(A018) 7 case 전부 거의 정지, 평지 고속 속도 1.17→0.03. 강화(−0.012) 방향은 어느 기준에서도 측정한 적 없음.
- 직접 예측 없음: 개선 쪽 예측('부드러움')은 평가기에 채널이 없어 직접 예측 없음 — 표적 개선 지표를 두지 않는다.
- 표적 지표:
  - yaw_right_tracking_yaw_up_cost: combined_yaw_right tracking_yaw_rmse up (3 seed 방향). '굼뜬 반응'의 확인 지표. 지지 = 예측된 비용이 나타남.

## flat_orientation_l2_m0p25

- 변경: flat_orientation_l2 0 → -0.25. 유지: track_lin_vel_xy_exp 1.5, feet_air_time 0.2, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표에 없다(H1 표에만 '몸통을 똑바로 유지'). 배포 원본 주석: '몸통 수평 유지. ↑(강) 안정 / ↓(약) 험지 적응'. 생성기: 내림(강화) '자세 ↑ 꼿꼿·안정·소극'. 로컬 '계단에서 덜 넘어짐' 주석은 우리가 덧붙인 것이라 출처로 쓰지 않는다. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6 ⑥·§6-b]
- 예측 방향: 강화: 안정 · 꼿꼿 · 소극(험지 적응 ↓)
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: A033 위 0→−0.5(A047) 험지 옆걸음 낙상 59→60(감소 없음), 험지 전진 속도 0.366→0.192, 10cm ≥2단 43→0, 15cm 낙상 90→8(오르지 않아서), DR 낙상 1→13.
- 표적 지표:
  - rough_lateral_falls_down: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. '안정'의 험지 옆걸음 자세 낙상 감소.
  - rough_forward_speed_down_cost: rough_forward speed_xy_mean down (3 seed 방향). '소극'의 확인 지표. 지지 = 예측된 감속.

## flat_orientation_l2_m0p5

- 변경: flat_orientation_l2 0 → -0.5. 유지: track_lin_vel_xy_exp 1.5, feet_air_time 0.2, lin_vel_z_l2 -1.25, ang_vel_xy_l2 -0.05, action_rate_l2 -0.01
- 출처(DEPLOY_DIRECT): 강좌 14 Go2 표에 없다(H1 표에만 '몸통을 똑바로 유지'). 배포 원본 주석: '몸통 수평 유지. ↑(강) 안정 / ↓(약) 험지 적응'. 생성기: 내림(강화) '자세 ↑ 꼿꼿·안정·소극'. 로컬 '계단에서 덜 넘어짐' 주석은 우리가 덧붙인 것이라 출처로 쓰지 않는다. [workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md §1·§6 ⑥·§6-b]
- 예측 방향: 강화: 안정 · 꼿꼿 · 소극(험지 적응 ↓), −0.25 보다 큰 변경
- 기존 관측·반례: A048 위 관측 없음. 다른 기준: A033 위 0→−0.5(A047) 험지 옆걸음 낙상 59→60(감소 없음), 험지 전진 속도 0.366→0.192, 10cm ≥2단 43→0, 15cm 낙상 90→8(오르지 않아서), DR 낙상 1→13.
- 표적 지표:
  - rough_lateral_falls_down: rough_lateral posture_falls_pooled A048 16 → 지지 ≤8, 미지지 ≥16. '안정'의 험지 옆걸음 자세 낙상 감소.
  - rough_forward_speed_down_cost: rough_forward speed_xy_mean down (3 seed 방향). '소극'의 확인 지표. 지지 = 예측된 감속.

## 공통 보호 항목 (기록, 3 seed 일치 악화만 표시)

- moving_gate: forward_nominal 러너의 정지 판정(candidate_suite_checks.py moving)과 같은 규칙. 정지면 평가 후 후보 제외 사유다(실행 중 중단 아님 — 러너는 69 case 를 끝까지 수집한다).
- forward_speed: forward_nominal 평지 전진 감속
- rough_forward_speed: rough_forward 험지 전진 감속
- yaw_right_speed: combined_yaw_right 복합 우회전 감속
- rough_lateral_falls: rough_lateral 험지 옆걸음 낙상 증가
- rough_forward_falls: rough_forward 험지 전진 낙상 증가
- yaw_right_falls: combined_yaw_right 복합 우회전 낙상 증가
- slope_plus_20_falls: slope_plus_20 경사 +20° 낙상 증가
- push_neg_y_falls: push_neg_y 밀침(−y) 낙상 증가 — A048 밀침 낙상 1건이 난 방향
- stairs_10_ge2: stairs_10_down 10cm ≥2단 감소
- stairs_15_ge2: stairs_15_down 15cm ≥2단 감소
- axis_scores:  G1~G7 점수·총 내부 proxy 는 tools/go2_g_a057_sweep_compare.py 가 낸다. 총점만으로 승자를 정하지 않는다.
- stairs_stall:  계단 정체 로봇 수는 비교 도구의 stairs_*_stall 열.
