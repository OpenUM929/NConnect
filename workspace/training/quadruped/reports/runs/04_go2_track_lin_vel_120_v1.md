# 04. go2_track_lin_vel_120_v1

- 시각: `2026-09-02_09-27-11` (학습 로그 내장값)
- 산출물: `workspace/_keep/go2_track_lin_vel_120_v1`
- 학습: 1000/1000 iter, 로그 `workspace/_keep/go2_track_lin_vel_120_v1/logs/candidate_training.log`
- 4족 판별 근거: `go2_representative_registry.json` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

| reward 항 | 가중치 |
|---|---|
| `track_lin_vel_xy_exp` | 1.2 |
| `track_ang_vel_z_exp` | 0.75 |
| `feet_air_time` | 0.01 |
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
| 200 | 0.2349 | 0.3207 | 948.94 | 0.0615 | 0.9385 | 10.67 | 0.49 | 8.0809 |
| 300 | 0.36 | 0.3254 | 967.67 | 0.0439 | 0.9561 | 12.24 | 0.47 | 7.4911 |
| 500 | 0.6711 | 0.4584 | 938.57 | 0.0883 | 0.9117 | 13.63 | 0.48 | 7.6516 |
| 999 | 0.9724 | 0.4926 | 993.3 | 0.0652 | 0.9348 | 15.51 | 0.49 | 7.9883 |

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `baseline_tier1` | 0.00000 | 17.53712 | 7 | `no_fall_detection` | POLICY_DOES_NOT_LOCOMOTE |
| `candidate` | 0.00000 | 20.62741 | 7 | `no_fall_detection` | POLICY_DOES_NOT_LOCOMOTE |

> `baseline_tier1` · `candidate`: 69 case 전수가 아니다. 빠진 시나리오는 0점으로 합산되므로 **그 arm의 70점은 전수 평가본과 같은 축에 놓을 수 없다.** 같은 부분 평가끼리만 비교한다.

## 계측 한계

- `no_fall_detection` — 낙상을 세지 않는다. 생존 proxy가 종료 수만 본다 → 점수가 위로 치우친다.

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
