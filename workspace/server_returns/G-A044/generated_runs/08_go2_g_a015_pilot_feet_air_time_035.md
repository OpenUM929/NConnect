# 08. go2_g_a015_pilot_feet_air_time_035

- 시각: `2026-09-04_08-03-40` (학습 로그 내장값)
- 산출물: `workspace/_keep/go2_g_a015_pilot_feet_air_time_035`
- 학습: 1000/1000 iter, 로그 `workspace/_keep/go2_g_a015_pilot_feet_air_time_035/logs/candidate_training.log`
- 4족 판별 근거: `go2_tuning_experiment_schema.json` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

| reward 항 | 가중치 |
|---|---|
| `track_lin_vel_xy_exp` | 1.2 |
| `track_ang_vel_z_exp` | 0.75 |
| `feet_air_time` | 0.35 |
| `lin_vel_z_l2` | -2 |
| `ang_vel_xy_l2` | -0.05 |
| `action_rate_l2` | -0.01 |
| `flat_orientation_l2` | 0 |
| `dof_torques_l2` | -0.0002 |
| `dof_pos_limits` | 0 |

## 학습 곡선

`terrain`은 `terrain_levels_vel` 커리큘럼 도달 레벨(만점 10)이다. 이 커리큘럼은 **이동 거리로 승급**한다.

| iter | terrain | track_lin_vel | episode_length | base_contact | time_out | reward | action_std | entropy_loss |
|---|---|---|---|---|---|---|---|---|
| 200 | 0.2393 | 0.3989 | 989.13 | 0.0173 | 0.9827 | 12.68 | 0.47 | 7.6177 |
| 300 | 0.4394 | 0.3676 | 971.86 | 0.0292 | 0.9708 | 12.86 | 0.47 | 7.6355 |
| 500 | 0.7183 | 0.4403 | 962.53 | 0.0503 | 0.9497 | 14.54 | 0.48 | 7.8045 |
| 999 | 1.8052 | 0.6451 | 934.44 | 0.1049 | 0.8951 | 14.9 | 0.5 | 8.3473 |

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `baseline_tier1` | 0.00000 | 46.49124 | 7 | `posture_gate_v1` | POLICY_LOCOMOTES |
| `candidate` | 0.00000 | 16.36931 | 7 | `posture_gate_v1` | POLICY_LOCOMOTES |

> `baseline_tier1` · `candidate`: 69 case 전수가 아니다. 빠진 시나리오는 0점으로 합산되므로 **그 arm의 70점은 전수 평가본과 같은 축에 놓을 수 없다.** 같은 부분 평가끼리만 비교한다.

## 계측 한계

- `posture_gate_v1` — 자세 기반 낙상 검출 도입. 측정 계약 필드는 아직 없다.

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
