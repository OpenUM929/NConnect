# 03. go2_feet_air_time_020_v1

- 시각: `2026-09-01_19-18-17` (학습 로그 내장값)
- 산출물: `workspace/_keep/go2_feet_air_time_020_v1`
- 학습: 1000/1000 iter, 로그 `workspace/_keep/go2_feet_air_time_020_v1/logs/candidate_training.log`
- 4족 판별 근거: `GO2_FEET_AIR_TIME_020_SCREENING_PRD.md` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

| reward 항 | 가중치 |
|---|---|
| `track_lin_vel_xy_exp` | 1 |
| `track_ang_vel_z_exp` | 0.75 |
| `feet_air_time` | 0.2 |
| `lin_vel_z_l2` | -3 |
| `ang_vel_xy_l2` | -0.08 |
| `action_rate_l2` | -0.01 |
| `flat_orientation_l2` | 0 |
| `dof_torques_l2` | -0.0002 |
| `dof_pos_limits` | 0 |

## 학습 곡선

`terrain`은 `terrain_levels_vel` 커리큘럼 도달 레벨(만점 10)이다. 이 커리큘럼은 **이동 거리로 승급**한다.

| iter | terrain | track_lin_vel | episode_length | base_contact | time_out | reward | action_std | entropy_loss |
|---|---|---|---|---|---|---|---|---|
| 200 | 0.1492 | 0.2283 | 944.68 | 0.1078 | 0.8922 | 8.53 | 0.48 | 7.755 |
| 300 | 0.0037 | 0.2176 | 986.5 | 0.0398 | 0.9602 | 11.24 | 0.44 | 6.6861 |
| 500 | 0.2621 | 0.3036 | 982.81 | 0.039 | 0.961 | 13.31 | 0.4 | 5.7134 |
| 999 | 0.5508 | 0.4158 | 984.94 | 0.0287 | 0.9713 | 14.8 | 0.42 | 6.3138 |

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `candidate` | 21.77258 | 21.77258 | 69 | `no_fall_detection` | POLICY_DOES_NOT_LOCOMOTE |

`candidate` 시나리오별 배점:

| G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|
| 0.04 | 2.83 | 4.96 | 3.91 | 1.04 | 6.52 | 2.48 |

## 계측 한계

- `no_fall_detection` — 낙상을 세지 않는다. 생존 proxy가 종료 수만 본다 → 점수가 위로 치우친다.

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
