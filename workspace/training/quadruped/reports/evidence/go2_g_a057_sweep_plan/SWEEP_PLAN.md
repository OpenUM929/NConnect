# G-A057 실행 목록 (자동 생성: tools/go2_g_a057_sweep_plan.py)

출발 설정 A048(`go2_g_a048_a033_lin_vel_z_m125` 학습 env.yaml). 한 실행에 한 항만 바꾼다. 학습 seed 42, env 4096, 1000 iter, 평가 checkpoint 900, 69 case.

| 변수 | 값 | 상태 | 근거 회차 | 근거 |
|---|---:|---|---|---|
| track_lin_vel_xy_exp | 1.2 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| track_lin_vel_xy_exp | 1.4 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| track_lin_vel_xy_exp | 1.5 | REUSE | go2_g_a048_a033_lin_vel_z_m125 | 보상 전체·학습 조건·학습 코드·평가기·registry·69 case 일치 |
| track_lin_vel_xy_exp | 1.6 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| lin_vel_z_l2 | -2.0 | REUSE | go2_g_a033_a017_track_lin_vel_xy_150 | 보상 전체·학습 조건·학습 코드·평가기·registry·69 case 일치 |
| lin_vel_z_l2 | -1.75 | REUSE | go2_g_a044_a033_lin_vel_z_m175 | 보상 전체·학습 조건·학습 코드·평가기·registry·69 case 일치 |
| lin_vel_z_l2 | -1.5 | REUSE | go2_g_a043_a033_lin_vel_z_m15 | 보상 전체·학습 조건·학습 코드·평가기·registry·69 case 일치 |
| lin_vel_z_l2 | -1.375 | REUSE | go2_g_a050_a033_lin_vel_z_m1375 | 보상 전체·학습 조건·학습 코드·평가기·registry·69 case 일치 |
| lin_vel_z_l2 | -1.25 | BASE_SHARED | — | A048 기준값 — 첫 변수 행의 A048 결과를 공유, 반복 실행 안 함 |
| lin_vel_z_l2 | -1.0 | REUSE | go2_g_a049_a033_lin_vel_z_m1 | 보상 전체·학습 조건·학습 코드·평가기·registry·69 case 일치 |
| ang_vel_xy_l2 | -0.04 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| ang_vel_xy_l2 | -0.05 | BASE_SHARED | — | A048 기준값 — 첫 변수 행의 A048 결과를 공유, 반복 실행 안 함 |
| ang_vel_xy_l2 | -0.08 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| feet_air_time | 0.01 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| feet_air_time | 0.1 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| feet_air_time | 0.2 | BASE_SHARED | — | A048 기준값 — 첫 변수 행의 A048 결과를 공유, 반복 실행 안 함 |
| feet_air_time | 0.35 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| action_rate_l2 | -0.008 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| action_rate_l2 | -0.01 | BASE_SHARED | — | A048 기준값 — 첫 변수 행의 A048 결과를 공유, 반복 실행 안 함 |
| action_rate_l2 | -0.012 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| flat_orientation_l2 | 0.0 | BASE_SHARED | — | A048 기준값 — 첫 변수 행의 A048 결과를 공유, 반복 실행 안 함 |
| flat_orientation_l2 | -0.25 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |
| flat_orientation_l2 | -0.5 | NEW_TRAIN | — | 보상 전체·학습 조건·학습 코드가 대응하는 완료 회차 없음 |

집계: BASE_SHARED 5, NEW_TRAIN 12, REUSE 6

대조한 완료 회차 13개(workspace/_keep 에서 training/env.yaml 과 meta/run_config.env 가 있는 폴더).
기준 정책이 다른 회차는 보상 항 전체가 달라 재사용하지 않는다. 미실행 패키지는 학습 산출물이 없어 후보가 아니다.
