# G-A093 기술 개선 리포트 초안 — 문장별 근거 (2026-10-18)

⟨⟩ 칸은 G-A093 서버 결과(report.html, TRAIN_STATUS, 69 case 판독)로 채운다. 채우기 전에는 제출본이 아니다. 예시 값으로 채웠을 때 497자이므로, 실측값이 길면 문장을 줄인다.

| 문장 | 근거 |
|---|---|
| 배포 보상 제자리(전진 0.035m/s) | Default-01, GO2_TUNING_BASE_DATA.md |
| 배포값: 속도 1, 흔들림 -0.08, 동작 -0.01, 수평 0(비활성), 회전 0.75(주석의 유효값) | tools/build_go2_default_vs_pilot_package.py DEFAULT_REWARDS, 배포 quadruped_rewards.py L82 |
| 회전 손실 51%(7.02/13.78), 0.3→0.75: 7.02→5.53, 55.29→56.85 | reports/GO2_G_A082_READOUT_20261015.md L51-52 |
| std 1.03, 동작 -0.005→-0.01: std 0.80(0.798), 15cm 생존 0.875→0.974, 57.59 | reports/GO2_G_A083_READOUT_20261015.md §2·§3 |
| 강좌 '약하게: 민첩하지만 다리 떨림' | 배포 quadruped_rewards.py action_rate 주석 |
| 수평 -0.22/-0.23: 55.39/56.56 | GO2_G_A089_READOUT §5, GO2_G_A087_READOUT |
| 회전 0.85: 56.72 | GO2_G_A090_READOUT_20261017.md |
| 발 들기 0.05: 54.66, 이동 추종 손실 6.92→10.03 | GO2_G_A092_READOUT_20261018.md |
| 5000회 = 강좌 13강 "5000(본격 학습)" | GO2_LECTURE_REWARD_REFERENCE.md §9 |
| ⟨⟩ 서버 학습 종료 iter·발산·평가 iter·지형·낙상률·내부점수 | G-A093 결과 ZIP: training/TRAIN_STATUS.txt, EVAL_CHECKPOINT_OVERRIDE.txt, exported/report.html, 69 case 판독 |

- 내부점수는 우리 역산 수식(/70)이고 공식 점수가 아니다. 리포트에는 "내부"로만 적는다.
- 57.59 이하 점수들은 PC2 학습 seed 42 하나에서 iter 2400으로 평가한 값이다. 서버 결과와 기계가 다르다.

## v2 (TECH_REPORT_DRAFT_v2.txt, 2026-10-18) 추가 근거
- 회전 항 기여 10%: G-A077 PC2 학습 로그 iter 2301~2400 평균 Episode_Reward/track_ang_vel_z_exp 0.1563 ÷ track_lin_vel_xy_exp 1.5781 = 9.9%. G-A082 0.4550/1.4240 = 32%.
- 상하 흔들림 벌점 3.5배: Episode_Reward/lin_vel_z_l2 −0.0595(G-A077) → −0.2089(G-A082). G-A083에서는 −0.1047.
- 사전등록 예측 std≤0.80·15cm 계단 생존≥0.92 → 실측 0.798·0.974 (GO2_G_A083_READOUT §2·§3).
- 주의: 기여 비율은 결과를 보고 나서 계산한 값이다. 회전 추종을 0.75로 정한 이유로 쓰지 않는다. 리포트에는 관측으로만 적었다. 결정 근거는 손실 몫 51%와 배포값 복귀다.
