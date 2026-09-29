# 13. go2_g_a021_chain01_ang_vel_xy_m005

- 시각: `2026-09-05_11-00-08` (학습 로그 내장값)
- 산출물: `workspace/_keep/go2_g_a021_chain01_ang_vel_xy_m005`
- 학습: 1000/1000 iter, 로그 `workspace/_keep/go2_g_a021_chain01_ang_vel_xy_m005/logs/candidate_training.log`
- 4족 판별 근거: `go2_tuning_experiment_schema.json` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

| reward 항 | 가중치 |
|---|---|
| `track_lin_vel_xy_exp` | 1.2 |
| `track_ang_vel_z_exp` | 0.75 |
| `feet_air_time` | 0.01 |
| `lin_vel_z_l2` | -3 |
| `ang_vel_xy_l2` | -0.05 |
| `action_rate_l2` | -0.01 |
| `flat_orientation_l2` | 0 |
| `dof_torques_l2` | -0.0002 |
| `dof_pos_limits` | 0 |

## 학습 곡선

`terrain`은 `terrain_levels_vel` 커리큘럼 도달 레벨(만점 10)이다. 이 커리큘럼은 **이동 거리로 승급**한다.

| iter | terrain | track_lin_vel | episode_length | base_contact | time_out | reward | action_std | entropy_loss |
|---|---|---|---|---|---|---|---|---|
| 200 | 0.3587 | 0.4201 | 964.4 | 0.05 | 0.95 | 12.9 | 0.49 | 8.1747 |
| 300 | 0.5111 | 0.4189 | 968.5 | 0.0313 | 0.969 | 13.63 | 0.48 | 8.0223 |
| 500 | 0.6991 | 0.3635 | 897.43 | 0.1857 | 0.8143 | 12.64 | 0.5 | 8.4642 |
| 999 | 1.0124 | 0.5734 | 979.47 | 0.0895 | 0.9107 | 15.78 | 0.52 | 8.8539 |

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `baseline_tier1` | 0.00000 | 18.61056 | 7 | `no_fall_detection` | POLICY_DOES_NOT_LOCOMOTE |
| `candidate` | 0.00000 | 12.00263 | 7 | `posture_gate_v1` | POLICY_DOES_NOT_LOCOMOTE |

> `baseline_tier1` · `candidate`: 69 case 전수가 아니다. 빠진 시나리오는 0점으로 합산되므로 **그 arm의 70점은 전수 평가본과 같은 축에 놓을 수 없다.** 같은 부분 평가끼리만 비교한다.

> **계측 비대칭.** 이 묶음의 두 arm이 서로 다른 계측 세대로 측정됐다. 둘의 차이는 정책 차이와 계측 차이가 섞인 값이라 **단일 변수 비교로 쓸 수 없다.**

## 계측 한계

- `no_fall_detection` — 낙상을 세지 않는다. 생존 proxy가 종료 수만 본다 → 점수가 위로 치우친다.
- `posture_gate_v1` — 자세 기반 낙상 검출 도입. 측정 계약 필드는 아직 없다.

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
