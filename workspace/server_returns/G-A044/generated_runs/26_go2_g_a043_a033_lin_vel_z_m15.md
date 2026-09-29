# 26. go2_g_a043_a033_lin_vel_z_m15

- 시각: `2026-09-22_12-22-54` (학습 로그 내장값)
- 산출물: `workspace/_keep/go2_g_a043_a033_lin_vel_z_m15`
- 학습: 1000/1000 iter, 로그 `workspace/_keep/go2_g_a043_a033_lin_vel_z_m15/logs/candidate_training.log`
- 4족 판별 근거: `go2_self_eval_registry.json` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

| reward 항 | 가중치 |
|---|---|
| `track_lin_vel_xy_exp` | 1.5 |
| `track_ang_vel_z_exp` | 0.75 |
| `feet_air_time` | 0.2 |
| `lin_vel_z_l2` | -1.5 |
| `ang_vel_xy_l2` | -0.05 |
| `action_rate_l2` | -0.01 |
| `flat_orientation_l2` | 0 |
| `dof_torques_l2` | -0.0002 |
| `dof_pos_limits` | 0 |

## 학습 곡선

`terrain`은 `terrain_levels_vel` 커리큘럼 도달 레벨(만점 10)이다. 이 커리큘럼은 **이동 거리로 승급**한다.

| iter | terrain | track_lin_vel | episode_length | base_contact | time_out | reward | action_std | entropy_loss |
|---|---|---|---|---|---|---|---|---|
| 200 | 0.5524 | 0.5735 | 978.13 | 0.0675 | 0.9325 | 13.89 | 0.56 | 9.6836 |
| 300 | 0.7094 | 0.5957 | 993.69 | 0.0378 | 0.9622 | 16.16 | 0.54 | 9.3836 |
| 500 | 1.531 | 0.7595 | 950.75 | 0.0837 | 0.9163 | 15.77 | 0.55 | 9.5732 |
| 999 | 5.2393 | 1.0681 | 911.49 | 0.1809 | 0.8194 | 17.95 | 0.64 | 11.4162 |

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `candidate` | 44.62454 | 보고서 없음 | 69 | `posture_gate_v2` | POLICY_LOCOMOTES |
| `g_a033_sentinel` | 0.00000 | 보고서 없음 | 5 | `posture_gate_v2` | POLICY_LOCOMOTES |

> 이 arm은 표준 평가 보고서(`SELF_EVAL_REPORT.json`)가 생성되지 않았다. 당시 판정이 쓴 숫자를 산출물에서 확인할 수 없고, 위 재채점값만 근거로 남는다.

> `g_a033_sentinel`: 69 case 전수가 아니다. 빠진 시나리오는 0점으로 합산되므로 **그 arm의 70점은 전수 평가본과 같은 축에 놓을 수 없다.** 같은 부분 평가끼리만 비교한다.

`candidate` 시나리오별 배점:

| G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|
| 9.67 | 4.58 | 7.41 | 9.74 | 1.62 | 6.28 | 5.33 |

## 계측 한계

- `posture_gate_v2` — 낙상 검출 + 측정 계약 고정(양 채널 필수·v1 대체 금지·커버리지 0.99).

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
