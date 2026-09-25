# 02. go2_default_vs_pilot_v1

- 시각: `2026-09-01_16-52-25` (평가 로그 내장값)
- 산출물: `workspace/_keep/go2_default_vs_pilot_v1`
- 학습 산출물: 체크포인트 model_800.pt, model_best.pt — **텍스트 학습 로그 미회수 — 곡선은 텐서보드 기록에서 읽었다**
- 텐서보드 기록: `workspace/_keep/go2_default_vs_pilot_v1/training/logs/rsl_rl/quadruped/2026-09-01_15-46-28/events.out.tfevents.1788245199.da-perfect52.9768.0` (1000 iter)
- 4족 판별 근거: `go2_self_eval_registry.json` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

| reward 항 | 가중치 |
|---|---|
| `track_lin_vel_xy_exp` | 1 |
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

텍스트 로그가 없어 텐서보드 기록에서 같은 태그를 읽었다.

| iter | terrain | track_lin_vel | episode_length | base_contact | time_out | reward | action_std | entropy_loss |
|---|---|---|---|---|---|---|---|---|
| 200 | 0.1745 | 0.2329 | 987.92 | 0.0467 | 0.9533 | 10.821 | 0.4648 | 7.3606 |
| 300 | 0.0005 | 0.2171 | 987.1 | 0.0257 | 0.9743 | 12.1279 | 0.4409 | 6.7142 |
| 500 | 0 | 0.1665 | 977.83 | 0.0486 | 0.9514 | 12.3809 | 0.417 | 6.0542 |
| 999 | 0 | 0.2119 | 975.33 | 0.0655 | 0.9345 | 13.0452 | 0.4432 | 6.8991 |

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `default` | 17.90699 | 17.90699 | 69 | `no_fall_detection` | POLICY_DOES_NOT_LOCOMOTE |
| `pilot` | 41.97990 | 41.97990 | 69 | `no_fall_detection` | POLICY_LOCOMOTES |

`default` 시나리오별 배점:

| G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|
| 0.04 | 2.79 | 3.72 | 4.03 | 1.38 | 4.10 | 1.86 |

`pilot` 시나리오별 배점:

| G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|
| 9.37 | 7.90 | 6.16 | 5.55 | 2.38 | 6.56 | 4.05 |

## 계측 한계

- `no_fall_detection` — 낙상을 세지 않는다. 생존 proxy가 종료 수만 본다 → 점수가 위로 치우친다.

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
