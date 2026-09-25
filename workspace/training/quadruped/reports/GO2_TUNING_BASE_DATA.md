# Go2 튜닝 기반 데이터

> **생성 문서 — 손으로 고치지 않는다.** `python tools/go2_tuning_base_data.py`가 증거 CSV에서 만든다.
> 원본: `reports/evidence/go2_stairs_behavior_20260916/` (`WEIGHT_OUTCOME.csv` · `LATERAL_BEHAVIOR.csv` · `CLIMB_REWARD.csv`, 생성기 `tools/go2_stairs_behavior.py`).
> 변수별 한 항 변경 쌍의 조건 대조·영향 표: `reports/GO2_VARIABLE_INFLUENCE.md`(생성기 `tools/go2_variable_influence.py`).
> 관문: `tools/test_go2_tuning_base_data_contract.py`. 분석 서술은 `reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md` §8·§9.

## 0. 사용 규칙 (2026-09-16 사용자 지시)

1. 튜닝값은 이 문서의 표와 특이점에서 도출한다. 보상 산수·항 크기·외부 기준값은 보조 근거이고 단독 근거가 아니다.
2. 튜닝을 제안하거나 판독할 때 답에 **해당 표의 행(원자료)을 먼저 보여주고**, 그 다음 특이점, 그 다음 값을 말한다.
3. 바꾸는 가중치마다 걷는 회차에서 관측된 값 대비 위치를 적는다: `OBSERVED` · `BETWEEN_OBSERVED` · `OUT_OF_RANGE`.
   새 reward 사양은 `base_data` 필드에 이 계산을 그대로 적고, `OUT_OF_RANGE`면 `out_of_range_reason`을 적는다(관문이 검사).
4. 도출 원리가 표의 다른 회차와 반대로 나오면 그 원리로 값을 정하지 않는다(§5 S5가 그 예).
5. 학습 seed는 전 회차 42 하나다. 회차 간 차이는 seed 운과 가를 수 없다 — 특이점은 **방향 후보**이지 인과가 아니다.

걷는 회차 정의: `rough_forward_speed >= 0.2` (표의 걷는 회차와 멈춘 회차 사이가 비어 있어 경계 위치에 결과가 흔들리지 않는다).

## 0-1. 보상 항의 역할 — Isaac Lab v2.3.1 원문 (2026-09-17 사용자 지시)

> "기준 문서에서 변수가 어떤 역할을 하는지 설명 없이 우리 결과로만 판단하지 마라." 각 항을 먼저 원문 식으로 읽고, 우리 결과는 그 역할과 맞는지 대조한다.
> 원문: `reports/evidence/go2_reward_term_roles_20260917/` (`SOURCES.csv`에 URL·SHA256). 식 칸은 그 파일의 함수 본문을 생성기가 그대로 뽑은 것이다(타입 힌트용 대입 제외).
> 가중치·파라미터는 현재 기준선 G-A033 학습 `env.yaml`(`_keep/go2_g_a033_a017_track_lin_vel_xy_150/training/env.yaml`)에서 읽는다. 로그 칸은 `TRAINING_TERMS.csv` 마지막 10 iter 평균이다.

| 항 | 원문 설명 | 원문 식 (파일:줄) | 풀이 | 걸리는 영역 [추정] | G-A033 가중치 | 로그(초당) | 로그÷가중치 | 우리 한 항 변경 쌍 등급 |
|---|---|---|---|---|---|---|---|---|
| `track_lin_vel_xy_exp` | Reward tracking of linear velocity commands (xy axes) using exponential kernel. | `lin_vel_error = torch.sum( torch.square(env.command_manager.get_command(command_name)[:, :2] - asset.data.root_lin_vel_b[:, :2]), dim=1, ) ; return torch.exp(-lin_vel_error / std**2)` (isaaclab_envs_mdp_rewards.py:297) | 몸통 좌표의 앞뒤·좌우 속도가 명령과 가까울수록 커지는 보상(최대 1). 오차²/std²의 지수 감소 | 전 영역(G1~G7 추종) | `1.5` (std `0.5`) | `0.950` | `0.633` | A 2 · C 2 |
| `track_ang_vel_z_exp` | Reward tracking of angular velocity commands (yaw) using exponential kernel. | `ang_vel_error = torch.square(env.command_manager.get_command(command_name)[:, 2] - asset.data.root_ang_vel_b[:, 2]) ; return torch.exp(-ang_vel_error / std**2)` (isaaclab_envs_mdp_rewards.py:311) | 몸통 좌표의 회전(yaw) 속도가 명령과 가까울수록 커지는 보상(최대 1) | G2 회전·전 영역 방향 유지 | `0.75` (std `0.5`) | `0.503` | `0.671` | **없음** |
| `lin_vel_z_l2` | Penalize z-axis base linear velocity using L2 squared kernel. | `return torch.square(asset.data.root_lin_vel_b[:, 2])` (isaaclab_envs_mdp_rewards.py:76) | 몸통 좌표의 위아래 속도² 벌점 — 튀기·떨어지기·**올라서기** 모두 같은 벌점 | G5 계단·G4 경사·G3 험지 | `-2.0` | `-0.062` | `0.031` | A 1 · C 2 |
| `ang_vel_xy_l2` | Penalize xy-axis base angular velocity using L2 squared kernel. | `return torch.sum(torch.square(asset.data.root_ang_vel_b[:, :2]), dim=1)` (isaaclab_envs_mdp_rewards.py:83) | 몸통의 좌우 구르기(roll)·앞뒤 끄덕임(pitch) **속도²** 벌점 — 기울어진 자세 자체가 아니라 기우는 빠르기 | G3 옆 뒤집힘·G6 밀침·G5 턱 넘기 | `-0.05` | `-0.151` | `3.020` | A 2 · B 2 · C 1 |
| `dof_torques_l2` | Penalize joint torques applied on the articulation using L2 squared kernel. | `return torch.sum(torch.square(asset.data.applied_torque[:, asset_cfg.joint_ids]), dim=1)` (isaaclab_envs_mdp_rewards.py:136) | 관절 토크² 합 벌점 — 힘을 덜 쓰게 한다 | G5 오르기(큰 토크 필요) | `-0.0002` | `-0.102` | `510.000` | **없음** |
| `dof_acc_l2` | Penalize joint accelerations on the articulation using L2 squared kernel. | `return torch.sum(torch.square(asset.data.joint_acc[:, asset_cfg.joint_ids]), dim=1)` (isaaclab_envs_mdp_rewards.py:163) | 관절 가속도² 합 벌점 — 관절 움직임을 부드럽게 한다 | G5·G6 빠른 발 동작 | `-2.5e-07` | `-0.228` | `912000.000` | **없음** |
| `action_rate_l2` | Penalize the rate of change of the actions using L2 squared kernel. | `return torch.sum(torch.square(env.action_manager.action - env.action_manager.prev_action), dim=1)` (isaaclab_envs_mdp_rewards.py:245) | 이번 행동과 직전 행동의 차이² 합 벌점 — 행동을 매끄럽게 한다 | G6 밀침 대응·G5 발 올리기 | `-0.01` | `-0.129` | `12.900` | C 1 |
| `feet_air_time` | Reward long steps taken by the feet using L2-kernel. | `first_contact = contact_sensor.compute_first_contact(env.step_dt)[:, sensor_cfg.body_ids] ; last_air_time = contact_sensor.data.last_air_time[:, sensor_cfg.body_ids] ; reward = torch.sum((last_air_time - threshold) * first_contact, dim=1) ; reward *= torch.norm(env.command_manager.get_command(command_name)[:, :2], dim=1) > 0.1 ; return reward` (isaaclab_tasks_locomotion_velocity_mdp_rewards.py:26) | 발이 땅에 닿는 순간 `(체공 시간 − threshold)`를 더한다. 명령 속도가 `0.1` 이하면 0. 체공이 threshold보다 짧으면 **음수(짧은 걸음 벌점)** | 걸음 형태 → G5 발 올리기·G4 | `0.2` (threshold `0.5`) | `-0.026` | `-0.130` | A 1 · B 1 · C 3 |
| `flat_orientation_l2` | Penalize non-flat base orientation using L2 squared kernel. | `return torch.sum(torch.square(asset.data.projected_gravity_b[:, :2]), dim=1)` (isaaclab_envs_mdp_rewards.py:90) | 몸통 좌표에서 본 중력 방향의 xy 성분² 벌점 — **기울어진 자세 자체**(roll·pitch 각) | G3 옆 뒤집힘 · 단 G4 경사·G5 계단에서도 상시 부과 | `0.0` | `0.000` | `—` | C 1 · D 1 |
| `dof_pos_limits` | Penalize joint positions if they cross the soft limits. | `out_of_limits = -( asset.data.joint_pos[:, asset_cfg.joint_ids] - asset.data.soft_joint_pos_limits[:, asset_cfg.joint_ids, 0] ).clip(max=0.0) ; out_of_limits += ( asset.data.joint_pos[:, asset_cfg.joint_ids] - asset.data.soft_joint_pos_limits[:, asset_cfg.joint_ids, 1] ).clip(min=0.0) ; return torch.sum(out_of_limits, dim=1)` (isaaclab_envs_mdp_rewards.py:182) | 관절 각도가 soft limit 밖으로 나간 양의 합 벌점 | 관절 한계 근처 동작 | `0.0` | `—` | `—` | **없음** |

로그 기록 방식(원문 `isaaclab_managers_reward_manager.py`): 매 step `식 × 가중치 × dt`를 에피소드 동안 더하고, `Episode_Reward/항` = 그 합의 평균 ÷ `max_episode_length_s`다. 그래서 로그 칸은 **항끼리 같은 단위(초당 보상)**로 비교된다. 로그가 소수 3자리라 로그÷가중치는 반올림 오차를 포함한다.

**원문에서 바로 읽히는 사실**

- **멈춰도 추종 보상이 남는다.** 제자리 로봇의 추종 항 = exp(−v²/std²), std `0.5`: 명령 `0.5` m/s면 `0.368`, `1.0` m/s면 `0.018`(가중치 곱 전). 그래서 G-A033 15cm 오르기 앞에서 멈춘 로봇도 추종 보상률 `0.679`(§3, 가중치 곱 후)를 받는다. 평가 추종 proxy도 같은 std를 쓴다(registry `tracking_proxy_std`).
- **`lin_vel_z_l2`는 올라서는 동작 자체를 벌한다.** 식에 방향 구분이 없다. G-A033 10cm 오른 로봇의 수직 벌점률 `-0.124` 대 15cm 정지 로봇 `-0.021`(§3). 단 벌점 몫과 15cm 오르기는 회차 사이에서 맞지 않았다(§5 S5).
- **`ang_vel_xy_l2`와 `flat_orientation_l2`는 다른 것을 본다.** 앞은 기우는 **속도**, 뒤는 기운 **각도**다. G-A033의 구르기·끄덕임 속도² 평균은 로그÷가중치 `3.020` (rms 약 `1.74` rad/s)이다. 20 s보다 일찍 끝난 에피소드도 20 s로 나누므로 실제보다 작게 잡힌 값이다.
- **`flat_orientation_l2`는 경사·계단에서도 벌점을 낸다.** 몸통이 20° 기울면 식 값은 sin²(20°) = `0.117`다. Isaac Lab은 이 항을 Go2 **평지** 설정에서만 `-2.5`로 켜고 험지 설정에서는 `0`으로 둔다(MASTER §1-b 표). 험지에서 끈 이유는 원문에 적혀 있지 않다 [모름].
- **`feet_air_time`은 threshold `0.5` s보다 짧은 체공을 벌한다.** 걷는 회차 로그가 모두 음수다(§6-1). 발 높이가 아니라 체공 시간을 본다.
- **G-A033에서 가장 큰 벌점 순서(로그):** `dof_acc_l2` `-0.228` · `ang_vel_xy_l2` `-0.151` · `action_rate_l2` `-0.129` · `dof_torques_l2` `-0.102` · `lin_vel_z_l2` `-0.062` · `feet_air_time` `-0.026`. 양수 항 합 `1.453`. 가장 큰 벌점 `dof_acc_l2`은 **한 번도 바꾼 적이 없다**.
- **한 항 변경 쌍이 하나도 없는 항:** `track_ang_vel_z_exp`, `dof_torques_l2`, `dof_acc_l2`, `dof_pos_limits`. 이 항들은 역할(원문)만 있고 우리 측정은 없다.
- **`undesired_contacts`**: Isaac Lab 기본은 허벅지 접촉 벌점(`-1.0`, 원문 `isaaclab_tasks_locomotion_velocity_env_cfg.py`)이고, Go2 험지 설정이 `None`으로 지운다(원문 `isaaclab_tasks_go2_rough_env_cfg.py`). 우리 env도 `null`이다.
- **종료 조건 `base_contact`**: Terminate when the contact force on the sensor exceeds the force threshold. 식 `net_contact_forces = contact_sensor.data.net_forces_w_history ; return torch.any( torch.max(torch.norm(net_contact_forces[:, :, sensor_cfg.body_ids], dim=-1), dim=1)[0] > threshold, dim=1 )` (isaaclab_envs_mdp_terminations.py:153). 우리 env는 몸통(`base`) 접촉력 > `1.0` N이면 끝난다 — G3 험지 옆걸음의 '종료'가 이것이다.

걷는 회차 학습 로그의 항 범위(`TRAINING_TERMS.csv`, A017, A031, A032, G-A033, Pilot-01):

| 항 | 최소 | 최대 |
|---|---|---|
| `track_lin_vel_xy_exp` | `0.796` | `0.950` |
| `track_ang_vel_z_exp` | `0.503` | `0.554` |
| `lin_vel_z_l2` | `-0.067` | `-0.054` |
| `ang_vel_xy_l2` | `-0.151` | `-0.108` |
| `dof_torques_l2` | `-0.102` | `-0.085` |
| `dof_acc_l2` | `-0.228` | `-0.168` |
| `action_rate_l2` | `-0.129` | `-0.086` |
| `feet_air_time` | `-0.026` | `-0.001` |
| `flat_orientation_l2` | `0.000` | `0.000` |

## 1. 회차별 가중치와 결과 (`WEIGHT_OUTCOME.csv`)

| 회차 | track | lin_vel_z | ang_vel_xy | action_rate | feet_air | flat_orient | 험지 전진 속도 | 경사 전진 m | 10cm 2단 이상 | 15cm 1단 이상 | 걷기 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Default-01 | 1 | -3 | -0.08 | -0.01 | 0.01 | 0 | 0.035 | 1.476 | 0 | 0 | 정지 |
| feet_air_time_020_v1 | 1 | -3 | -0.08 | -0.01 | 0.2 | 0 | 0.032 | 1.104 | 0 | 0 | 정지 |
| A010 | 1 | -2 | -0.08 | -0.01 | 0.01 | 0 | 0.031 | 0.008 | — | — | 정지 |
| A013 | 1 | -3 | -0.08 | -0.01 | 0.01 | -1 | 0.030 | 0.094 | — | — | 정지 |
| A024 | 1 | -3 | -0.15 | -0.01 | 0.01 | 0 | 0.031 | 0.307 | — | — | 정지 |
| track_120_v1 | 1.2 | -3 | -0.08 | -0.01 | 0.01 | 0 | 0.031 | 0.323 | — | — | 정지 |
| chain01 | 1.2 | -3 | -0.08 | -0.01 | 0.01 | 0 | 0.032 | 0.321 | 0 | 0 | 정지 |
| A020 | 1.2 | -2 | -0.08 | -0.01 | 0.01 | 0 | 0.036 | 0.323 | — | — | 정지 |
| A021 | 1.2 | -3 | -0.05 | -0.01 | 0.01 | 0 | 0.037 | 0.336 | — | — | 정지 |
| A022 | 1.2 | -3 | -0.08 | -0.01 | 0.2 | 0 | 0.034 | 0.293 | — | — | 정지 |
| Pilot-01 | 1.2 | -2 | -0.05 | -0.01 | 0.2 | 0 | 0.261 | 2.140 | 19 | 12 | 걷기 |
| A015 | 1.2 | -2 | -0.05 | -0.01 | 0.35 | 0 | 0.110 | 1.649 | — | — | 정지 |
| A016 | 1.2 | -2 | -0.15 | -0.01 | 0.2 | 0 | 0.031 | 0.285 | — | — | 정지 |
| A018 | 1.2 | -2 | -0.05 | -0.008 | 0.2 | 0 | 0.052 | 0.521 | — | — | 정지 |
| A017 | 1.4 | -2 | -0.05 | -0.01 | 0.2 | 0 | 0.270 | 5.867 | 2 | 0 | 걷기 |
| A031 | 1.4 | -2 | -0.05 | -0.01 | 0.01 | 0 | 0.299 | 1.993 | — | — | 걷기 |
| A032 | 1.4 | -2 | -0.05 | -0.01 | 0.1 | 0 | 0.242 | 5.626 | — | — | 걷기 |
| G-A033 | 1.5 | -2 | -0.05 | -0.01 | 0.2 | 0 | 0.366 | 8.840 | 43 | 4 | 걷기 |
| A043 | 1.5 | -1.5 | -0.05 | -0.01 | 0.2 | 0 | 0.419 | 9.268 | 94 | 88 | 걷기 |

빈칸(—)은 오르기를 재지 않은 회차다.

## 2. 험지 옆걸음 (`LATERAL_BEHAVIOR.csv`, 로봇 96대)

| 회차 | track | 종료 | 무거운 로봇 종료 | 가벼운 로봇 종료 | 질량 AUC | \|wz\| | 종료 전 기울기 cos | 처음 2초 \|wz\| AUC | 방향 이탈 rad (종료 / 생존) |
|---|---|---|---|---|---|---|---|---|---|
| Default-01 | 1 | 21 | 11/34 | 4/28 | 0.613 | 0.168 | — | 0.798 | 0.302 / 0.242 |
| feet_air_time_020_v1 | 1 | 4 | 2/34 | 1/28 | 0.538 | 0.080 | — | 0.546 | 0.280 / 0.222 |
| chain01 | 1.2 | 21 | 9/34 | 5/28 | 0.622 | 0.179 | -0.915 | 0.656 | 0.393 / 0.686 |
| Pilot-01 | 1.2 | 31 | 10/34 | 8/28 | 0.530 | 0.154 | -0.422 | 0.640 | 0.146 / 0.352 |
| A017 | 1.4 | 48 | 17/34 | 12/28 | 0.525 | 0.168 | -0.830 | 0.553 | 0.310 / 0.442 |
| G-A033 | 1.5 | 58 | 30/34 | 10/28 | 0.784 | 0.269 | -0.973 | 0.600 | 0.460 / 0.750 |

무거운 로봇 = 몸통 질량 `>= 8.5 kg`, 가벼운 로봇 = `< 7 kg`. 기울기 cos가 음수면 뒤집힌 채 끝났다. 옛 로그는 기울기가 없다(—).
옆걸음 명령의 회전은 0이다(`steps.csv` `cmd_wz`). 그래서 \|wz\|는 회전 추종 오차이고, 방향 이탈은 끝날 때까지 누적 회전의 크기다. AUC는 종료 로봇의 값이 생존 로봇보다 클 확률이다(`0.5` = 무관).

| 회차 | case | 옆 명령 vy | 실제 vy | 종료 | 무거운 로봇 종료 | 가벼운 로봇 종료 | 질량 AUC | 처음 2초 vy AUC |
|---|---|---|---|---|---|---|---|---|
| Pilot-01 | rough_lateral | `0.30` | 0.134 | 31 | 10/34 | 8/28 | 0.530 | 0.589 |
| Pilot-01 | left | `0.35` | 0.304 | 0 | 0/34 | 0/28 | — | — |
| Pilot-01 | right | `-0.35` | -0.258 | 0 | 0/34 | 0/28 | — | — |
| Pilot-01 | diagonal_left | `0.30` | 0.284 | 0 | 0/34 | 0/28 | — | — |
| Pilot-01 | diagonal_right | `-0.30` | -0.173 | 0 | 0/34 | 0/28 | — | — |
| Pilot-01 | rough_forward | `0.00` | 0.019 | 3 | 1/34 | 0/28 | 0.667 | 0.699 |
| A017 | rough_lateral | `0.30` | 0.103 | 48 | 17/34 | 12/28 | 0.525 | 0.593 |
| A017 | left | `0.35` | 0.353 | 0 | 0/34 | 0/28 | — | — |
| A017 | right | `-0.35` | -0.296 | 0 | 0/34 | 0/28 | — | — |
| A017 | diagonal_left | `0.30` | 0.340 | 0 | 0/34 | 0/28 | — | — |
| A017 | diagonal_right | `-0.30` | -0.252 | 0 | 0/34 | 0/28 | — | — |
| A017 | rough_forward | `0.00` | -0.013 | 0 | 0/34 | 0/28 | — | — |
| G-A033 | rough_lateral | `0.30` | 0.112 | 58 | 30/34 | 10/28 | 0.784 | 0.505 |
| G-A033 | left | `0.35` | 0.294 | 4 | 4/34 | 0/28 | 0.845 | 0.867 |
| G-A033 | right | `-0.35` | -0.310 | 0 | 0/34 | 0/28 | — | — |
| G-A033 | diagonal_left | `0.30` | 0.228 | 0 | 0/34 | 0/28 | — | — |
| G-A033 | diagonal_right | `-0.30` | -0.290 | 0 | 0/34 | 0/28 | — | — |
| G-A033 | rough_forward | `0.00` | -0.002 | 3 | 1/34 | 1/28 | 0.394 | 0.491 |

실제 vy = 종료 전 구간(처음 정착 구간 제외) 평균. 평지 옆걸음(left·right·diagonal)은 `0.30`~`0.35` 명령, 험지 옆걸음은 `0.30` 명령이다. vy AUC는 종료 로봇이 명령 방향으로 더 빨리 움직였을 확률이다.

### 2-1. 옆걸음 기록이 있는 한 항 변경 쌍 (종료 수는 `CASE_BEHAVIOR.csv` seed 101/202/303)

| 쌍 | 바뀐 가중치 | env.yaml 차이(`log_dir` 제외) | 체크포인트 같음 | 둘 다 걷기 | seed별 종료 | 종료 합 | 옆 속도 vy | 무거운 로봇 종료 | 종료 전 기울기 cos |
|---|---|---|---|---|---|---|---|---|---|
| Default-01 → feet_air_time_020_v1 | feet_air | `882: weight: 0.01 → weight: 0.2` | 예 | 아니오 | 8/7/6 → 0/1/3 | 21 → 4 | 0.010 → 0.006 | 11 → 2 | — → — |
| Default-01 → chain01 | track | `827: weight: 1.0 → weight: 1.2` | 아니오 (800 대 900) | 아니오 | 8/7/6 → 5/11/5 | 21 → 21 | 0.010 → 0.044 | 11 → 9 | — → -0.915 |
| Pilot-01 → A017 | track | `827: weight: 1.2 → weight: 1.4` | 아니오 (999 대 900) | 예 | 6/11/14 → 17/14/17 | 31 → 48 | 0.134 → 0.103 | 10 → 17 | -0.422 → -0.830 |
| A017 → G-A033 | track | `827: weight: 1.4 → weight: 1.5` | 예 | 예 | 17/14/17 → 19/20/19 | 48 → 58 | 0.103 → 0.112 | 17 → 30 | -0.830 → -0.973 |

- 종료 수는 계측 세대와 무관하다: 같은 Pilot-01 체크포인트를 낙상 미검출 세대(`go2_default_vs_pilot_v1`)와 검출 세대(`go2_a017_full_suite`)로 잰 seed별 종료가 같다(CSV 두 행).
- **A017 → G-A033(track 한 항, 체크포인트 같음): 험지 옆걸음 종료가 seed 셋 모두에서 늘었다(`True`).** 평지 옆걸음 종료는 left 0 → 4 · right 0 → 0 · diagonal_left 0 → 0 · diagonal_right 0 → 0, 실제 vy는 left 0.353 → 0.294 · right -0.296 → -0.310 · diagonal_left 0.340 → 0.228 · diagonal_right -0.252 → -0.290 — 왼쪽 옆 속도가 줄었다.
- Default-01 → `feet_air_time_020_v1`(feet_air 한 항, 체크포인트 같음)은 종료 21 → 4이지만 두 정책 모두 걷지 않는다(험지 옆 vy 0.010 → 0.006). 옆으로 가지 않아서 덜 넘어진 것과 가를 수 없다 — 걷는 기준으로 옮기지 않는다.
- 로봇별로 처음 2초 옆 속도는 험지 옆걸음 종료를 설명하지 않는다: vy AUC 0.589 · 0.593 · 0.505. 로봇별로 가장 강한 것은 G-A033의 몸통 질량(AUC 0.784)이고, 질량은 보상 항이 아니다.
- 옆걸음 기록이 없는 가중치 변경: `ang_vel_xy_l2` — A016(`-0.15`, Pilot 위)·A021(`-0.05`, chain01 위)·A024(`-0.15`, Default 위) — 셋 다 7 case 평가라 험지 옆걸음 기록이 없다 · `flat_orientation_l2` — A013(`-1`, Default 위) 하나, 7 case 평가라 옆걸음 기록이 없다. 걷는 회차는 전부 `0` · `lin_vel_z_l2 · action_rate_l2` — A010·A020·A018 모두 7 case 평가라 옆걸음 기록이 없다.
  이 회차들의 7 case에 평지 `diagonal_left`(옆 명령 `0.30`)가 있지만, 후보 실제 vy가 전부 `0.01` 미만이다(`True`, seed 101 `steps.csv` 전 행 평균). 옆으로 가지 않은 정책이라 옆 넘어짐 정보가 없다. 기울기 벌점 두 항은 G-A033 종료 로봇이 뒤집혀 끝난다는 점(기울기 cos)에서 물리적으로 가깝지만, 값을 정할 데이터가 없다.

## 3. 오르기 구간 보상률 (`CLIMB_REWARD.csv`, G-A033 가중치로 계산)

| arm | case | 구간 | 로봇 | 추종 보상률 | 수직 벌점률 | 합 |
|---|---|---|---|---|---|---|
| pilot | forward_nominal | walk | 96 | 1.430 | -0.053 | 1.377 |
| pilot | stairs_10_down | stall | 31 | 0.690 | -0.028 | 0.662 |
| pilot | stairs_10_down | climb | 19 | 0.840 | -0.102 | 0.739 |
| pilot | stairs_15_down | stall | 84 | 0.679 | -0.019 | 0.661 |
| a017 | forward_nominal | walk | 96 | 1.380 | -0.031 | 1.349 |
| a017 | stairs_10_down | stall | 68 | 0.711 | -0.016 | 0.695 |
| a017 | stairs_10_down | climb | 2 | 0.906 | -0.058 | 0.848 |
| a017 | stairs_15_down | stall | 96 | 0.672 | -0.007 | 0.665 |
| candidate | forward_nominal | walk | 96 | 1.471 | -0.063 | 1.408 |
| candidate | stairs_10_down | climb | 43 | 0.985 | -0.124 | 0.861 |
| candidate | stairs_10_down | stall | 6 | 0.714 | -0.072 | 0.642 |
| candidate | stairs_15_down | stall | 92 | 0.679 | -0.021 | 0.658 |

case 이름은 지형과 반대다: `stairs_*_down` = 오르기(역피라미드).

## 4. 가중치별 관측 범위 (걷는 회차)

| 가중치 | 전 회차 관측값 | 걷는 회차 관측값 |
|---|---|---|
| `track_lin_vel_xy_exp` | 1, 1.2, 1.4, 1.5 | 1.2, 1.4, 1.5 |
| `lin_vel_z_l2` | -3, -2, -1.5 | -2, -1.5 |
| `ang_vel_xy_l2` | -0.15, -0.08, -0.05 | -0.05 |
| `action_rate_l2` | -0.01, -0.008 | -0.01 |
| `feet_air_time` | 0.01, 0.1, 0.2, 0.35 | 0.01, 0.1, 0.2 |
| `flat_orientation_l2` | -1, 0 | 0 |

걷는 회차에서 값이 하나뿐인 가중치는 기울기를 잴 수 없다. 그 가중치를 움직이는 값은 전부 `OUT_OF_RANGE`다.

## 5. 특이점 (표에서 계산)

- **S1 걷기 조건 — 반례가 나왔다.** 걷는 회차 6개 중 5개가 `lin_vel_z -2` · `ang_vel_xy -0.05`를 함께 가진다. **예외: A043(`lin_vel_z -1.5` · `ang_vel_xy -0.05`)** — '이 쌍이 아니면 멈춘다'는 옛 읽기는 이 행으로 반증됐다. 둘 중 하나만 같은 회차: A010, A020, A021, A016 — 전부 정지. 같은 쌍인데 정지한 회차: A015(feet_air 0.35), A018(action_rate -0.008) — 걷는 회차에 없는 값이 하나씩 있다.
- **S2 track 선 (feet_air 0.2, 걷는 회차).** Pilot-01 track 1.2: 경사 2.140 m · 10cm 19 · 15cm 12 → A017 track 1.4: 경사 5.867 m · 10cm 2 · 15cm 0 → G-A033 track 1.5: 경사 8.840 m · 10cm 43 · 15cm 4.
  같은 선의 옆걸음: Pilot-01 종료 31 (무거운 10 · 가벼운 8, AUC 0.530) → A017 종료 48 (무거운 17 · 가벼운 12, AUC 0.525) → G-A033 종료 58 (무거운 30 · 가벼운 10, AUC 0.784). 무게 민감(AUC)은 마지막 값에서만 나타난다.
- **S3 15cm 오르기는 track과 한 방향으로 움직이지 않는다** (단조: `False`). 10cm도 19 → 2 → 43로 튄다 — 줄어든 Pilot-01→A017 쌍은 평가 체크포인트도 달라(§5-2) track 한 항의 비교가 아니다.
- **S4 feet_air 선 (track 1.4, 걷는 회차).** A031 0.01: 경사 1.993 m · 험지 속도 0.299 → A032 0.1: 경사 5.626 m · 험지 속도 0.242 → A017 0.2: 경사 5.867 m · 험지 속도 0.270. 걷는 회차 밖 값: A015 feet_air 0.35는 정지.
- **S5 오르기 수직 벌점 몫 대 15cm 오르기.** 몫 = (15cm 정지 수직 벌점률 − 10cm 오름 수직 벌점률) / (10cm 오름 추종률 − 15cm 정지 추종률). Pilot-01 `52%` (오른 로봇 19대) · 15cm 12 · A017 `22%` (오른 로봇 2대) · 15cm 0 · G-A033 `34%` (오른 로봇 43대) · 15cm 4. '몫이 작을수록 15cm를 더 오른다'가 성립하는가: `False`.

## 5-1. track 기준 비율 (벌점 ÷ track)

근거: 학습기 rsl_rl(설치본 `>= 4.0`, `launcher.log`)은 `normalize_advantage_per_mini_batch: false`(학습 `agent.yaml`)일 때 배치 전체의 advantage를 평균 0·표준편차 1로 바꾼 뒤 정책을 갱신한다 (rsl_rl main `algorithms/ppo.py`: `advantages = (advantages - mean) / (std + 1e-8)`, 2026-09-16 원문 확인). 그래서 보상 전체에 같은 배수를 곱해도 정책 갱신 크기는 같고, 항 사이의 비율이 방향을 정한다. 단 가치 함수 손실은 정규화하지 않으므로 완전히 무관하지는 않다. track은 양수 항이라 올리면 모든 벌점의 비율이 함께 줄어든다.

| 회차 | track | lin_vel_z ÷ track | ang_vel_xy ÷ track | feet_air ÷ track | 회전 추종(`0.75`) ÷ track | 걷기 | 10cm 2단 이상 | 학습 지형 레벨 |
|---|---|---|---|---|---|---|---|---|
| Default-01 | `1` | `-3.000` | `-0.0800` | `0.0100` | `0.750` | 정지 | 0 | 0.000 |
| feet_air_time_020_v1 | `1` | `-3.000` | `-0.0800` | `0.2000` | `0.750` | 정지 | 0 | 0.547 |
| A010 | `1` | `-2.000` | `-0.0800` | `0.0100` | `0.750` | 정지 | — | — |
| A013 | `1` | `-3.000` | `-0.0800` | `0.0100` | `0.750` | 정지 | — | — |
| A024 | `1` | `-3.000` | `-0.1500` | `0.0100` | `0.750` | 정지 | — | — |
| track_120_v1 | `1.2` | `-2.500` | `-0.0667` | `0.0083` | `0.625` | 정지 | — | 0.975 |
| chain01 | `1.2` | `-2.500` | `-0.0667` | `0.0083` | `0.625` | 정지 | 0 | — |
| A020 | `1.2` | `-1.667` | `-0.0667` | `0.0083` | `0.625` | 정지 | — | — |
| A021 | `1.2` | `-2.500` | `-0.0417` | `0.0083` | `0.625` | 정지 | — | — |
| A022 | `1.2` | `-2.500` | `-0.0667` | `0.1667` | `0.625` | 정지 | — | 0.916 |
| Pilot-01 | `1.2` | `-1.667` | `-0.0417` | `0.1667` | `0.625` | 걷기 | 19 | 3.902 |
| A015 | `1.2` | `-1.667` | `-0.0417` | `0.2917` | `0.625` | 정지 | — | 1.771 |
| A016 | `1.2` | `-1.667` | `-0.1250` | `0.1667` | `0.625` | 정지 | — | 0.000 |
| A018 | `1.2` | `-1.667` | `-0.0417` | `0.1667` | `0.625` | 정지 | — | 1.166 |
| A017 | `1.4` | `-1.429` | `-0.0357` | `0.1429` | `0.536` | 걷기 | 2 | 4.216 |
| A031 | `1.4` | `-1.429` | `-0.0357` | `0.0071` | `0.536` | 걷기 | — | 4.783 |
| A032 | `1.4` | `-1.429` | `-0.0357` | `0.0714` | `0.536` | 걷기 | — | 4.575 |
| G-A033 | `1.5` | `-1.333` | `-0.0333` | `0.1333` | `0.500` | 걷기 | 43 | 4.710 |
| A043 | `1.5` | `-1.000` | `-0.0333` | `0.1333` | `0.500` | 걷기 | 94 | — |

- 걷는 기준에서 track을 올린 두 단계(Pilot→A017 `-14%`, A017→G-A033 `-7%`)는 벌점 비율을 한 방향으로 줄였다. 10cm 오르기는 19 → 2 → 43로 줄었다가 늘었다(S3). 줄어든 쌍은 평가 체크포인트가 달라, 체크포인트가 같은 A017→G-A033만 보면 비율이 줄 때 오르기가 늘었다(§5-2).
- 회전 추종 비율도 track과 함께 줄었고 옆걸음 평균 \|wz\|는 0.154 → 0.168 → 0.269로 늘었다(§2). **그러나 로봇별로는 회전이 종료를 설명하지 않는다:** 처음 2초 \|wz\| AUC는 걷는 세 회차에서 `0.553`~`0.640`로 약하고(질량 AUC G-A033 `0.784`보다 낮다), 방향 이탈이 생존 로봇에서 더 큰가: `True`(§2 마지막 열). 회전 추종 가중치를 올리는 후보는 이 표로 뒷받침되지 않는다.

## 5-2. track 한 항만 다른 쌍 — case별 이동 거리 (`CASE_BEHAVIOR.csv` `projected_progress_m`, seed 3개 평균)

- 학습 env.yaml 대조 Pilot-01→A017: `log_dir` 외 다른 줄 = `827: weight: 1.2 → weight: 1.4`.
- 학습 env.yaml 대조 A017→G-A033: `log_dir` 외 다른 줄 = `827: weight: 1.4 → weight: 1.5`.
- 평가 체크포인트: Default-01 iter `800` (`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 294행: Default-01 iter 800, SHA `99ceeaa1…`) · feet_air_time_020_v1 iter `800` (`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 295행: step 829 → `model_800`, SHA `0dc8815f…`) · chain01 iter `900` (`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 297행: step 900 → `model_900`, SHA `143871e3…`) · Pilot-01 iter `999` (`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 294행: best iter 972 → `model_999`, SHA `c4d78adf…`) · A017 iter `900` (`GO2_REWARD_EVIDENCE_MASTER.md` 640행: `model_900.pt`, SHA `0563deff…`) · G-A033 iter `900` (`_keep/go2_g_a033_a017_track_lin_vel_xy_150/training/CHECKPOINT_PIN.txt` `EVAL_CHECKPOINT_ITER`).
- 학습 `agent.yaml` 세 회차 동일: `True` (Pilot-01은 G-A001 원본 회수본 `params/agent.yaml`). 학습 seed는 셋 다 `42`, 반복 `1000`이다. Pilot-01의 학습 소스 코드는 보관되지 않아 대조하지 못했다.

| case | 실제 동작 | Pilot-01 (track `1.2`, iter `999`) | A017 (`1.4`, iter `900`) | G-A033 (`1.5`, iter `900`) |
|---|---|---|---|---|
| forward_nominal | 평지 전진 | `14.841` | `12.555` | `14.719` |
| rough_forward | 험지 전진 | `4.779` | `5.289` | `7.503` |
| rough_lateral | 험지 옆걸음 | `1.345` | `1.181` | `1.993` |
| slope_plus_20 | 오르막 20° | `2.140` | `5.867` | `8.840` |
| slope_minus_20 | 내리막 20° | `8.564` | `7.545` | `7.909` |
| stairs_10_down | 10cm 계단 오르기 | `1.776` | `1.683` | `2.186` |
| stairs_15_down | 15cm 계단 오르기 | `1.363` | `1.274` | `1.425` |
| stairs_10_up | 10cm 계단 내려가기 | `7.830` | `6.933` | `7.032` |
| stairs_15_up | 15cm 계단 내려가기 | `5.733` | `6.790` | `7.030` |

- **A017→G-A033 (학습 설정 차이 = track 한 줄, 체크포인트 같음): 이동 거리가 늘어난 case `9`/`9`.** 계단 오르기 로봇 수(§1 10cm 2단 이상)도 2 → 43로 늘었다. 같은 설정·같은 seed 학습과 평가는 결정론적이므로(`GO2_NOW.md` §0 [회차 실측]) 이 차이는 track 변경의 결과다 [확인].
- Pilot-01→A017: 늘어난 case `3`/`9`. 학습 env.yaml·agent.yaml은 track 한 줄만 다르지만 평가 체크포인트가 iter `999` 대 `900`으로 다르다. 이 쌍의 감소를 track 효과로만 읽지 않는다. S3의 '줄었다가 늘었다'는 이 쌍에서 나온다.
- 남는 한계: 학습 seed가 `42` 하나라 다른 seed에서도 같은 방향인지는 모른다 [모름]. 정지 계열(Default-01 track `1` → track_120_v1 `1.2`)은 §1에서 경사 전진이 줄었지만 체크포인트가 `800` 대 `900`이다(`GO2_VARIABLE_INFLUENCE.md` G-A009) — 걷는 기준에서의 결과를 정지 기준으로 옮기지 않는다.

## 6. 발 들기(`feet_air_time`)와 계단

### 6-1. 학습 로그의 발 들기 항 (`TRAINING_TERMS.csv`, 마지막 10 iter 평균)

| 회차 | 가중치 | 걷기 | 학습 로그 항 | 항 ÷ 가중치 | 학습 지형 레벨 | 몸통 접촉 종료 |
|---|---|---|---|---|---|---|
| A031 | `0.01` | 걷기 | -0.001 | `-0.10` | 4.783 | 0.118 |
| Default-01 | `0.01` | 정지 | -0.001 | `-0.10` | 0.000 | 0.068 |
| track_120_v1 | `0.01` | 정지 | -0.001 | `-0.10` | 0.975 | 0.066 |
| A032 | `0.1` | 걷기 | -0.014 | `-0.14` | 4.575 | 0.143 |
| A016 | `0.2` | 정지 | -0.010 | `-0.05` | 0.000 | 0.021 |
| A017 | `0.2` | 걷기 | -0.025 | `-0.12` | 4.216 | 0.103 |
| A018 | `0.2` | 정지 | -0.025 | `-0.12` | 1.166 | 0.204 |
| A022 | `0.2` | 정지 | -0.025 | `-0.12` | 0.916 | 0.062 |
| G-A033 | `0.2` | 걷기 | -0.026 | `-0.13` | 4.710 | 0.173 |
| Pilot-01 | `0.2` | 걷기 | -0.025 | `-0.12` | 3.902 | 0.138 |
| feet_air_time_020_v1 | `0.2` | 정지 | -0.020 | `-0.10` | 0.547 | 0.028 |
| A015 | `0.35` | 정지 | -0.039 | `-0.11` | 1.771 | 0.103 |

- 표의 모든 회차에서 항이 음수다(`True`). 로봇의 평균 체공이 `0.5 s`보다 짧아서, 이 항은 실제로는 **짧은 걸음 벌점**으로 작동한다.
- 걷는 회차의 항 ÷ 가중치는 `-0.14` ~ `-0.10`로, 가중치가 `0.01`에서 `0.35`까지 변해도 크게 움직이지 않는다. 가중치는 체공 시간 자체보다 벌점 크기를 바꾼다 [추정: 로그가 가중치 × 원값이라는 IL 기록 방식 가정]. 가중치 `0.01` 행은 로그가 소수 3자리라 비율의 오차가 크다.

### 6-2. 계단 기록이 있는 발 들기 값

| 회차 | 가중치 | 걷기 | 계단 case | seed 수 | 속도 | 종료 로봇 | 생존 proxy |
|---|---|---|---|---|---|---|---|
| A031 | `0.01` | 걷기 | 원격 측정 없음 | 0 | — | — | — |
| Default-01 | `0.01` | 정지 | stairs_10_down (오르기) | 3 | 0.029 / 0.028 / 0.029 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| Default-01 | `0.01` | 정지 | stairs_10_up (내려가기) | 3 | 0.028 / 0.027 / 0.028 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| Default-01 | `0.01` | 정지 | stairs_15_down (오르기) | 3 | 0.029 / 0.028 / 0.029 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| Default-01 | `0.01` | 정지 | stairs_15_up (내려가기) | 3 | 0.028 / 0.028 / 0.028 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| chain01 | `0.01` | 정지 | stairs_10_down (오르기) | 3 | 0.026 / 0.026 / 0.026 | 0 / 0 / 0 | 0.000 / 0.000 / 0.000 |
| chain01 | `0.01` | 정지 | stairs_10_up (내려가기) | 3 | 0.026 / 0.025 / 0.025 | 0 / 0 / 0 | 0.000 / 0.000 / 0.000 |
| chain01 | `0.01` | 정지 | stairs_15_down (오르기) | 3 | 0.026 / 0.026 / 0.026 | 0 / 0 / 0 | 0.000 / 0.000 / 0.000 |
| chain01 | `0.01` | 정지 | stairs_15_up (내려가기) | 3 | 0.025 / 0.025 / 0.025 | 0 / 0 / 0 | 0.000 / 0.000 / 0.000 |
| A032 | `0.1` | 걷기 | 원격 측정 없음 | 0 | — | — | — |
| A017 | `0.2` | 걷기 | stairs_10_down (오르기) | 3 | 0.118 / 0.107 / 0.116 | 0 / 0 / 0 | 0.031 / 0.000 / 0.219 |
| A017 | `0.2` | 걷기 | stairs_10_up (내려가기) | 3 | 0.347 / 0.341 / 0.342 | 0 / 0 / 0 | 0.781 / 0.750 / 0.750 |
| A017 | `0.2` | 걷기 | stairs_15_down (오르기) | 3 | 0.084 / 0.088 / 0.081 | 0 / 2 / 1 | 0.000 / 0.000 / 0.000 |
| A017 | `0.2` | 걷기 | stairs_15_up (내려가기) | 3 | 0.349 / 0.336 / 0.341 | 0 / 1 / 1 | 0.719 / 0.562 / 0.719 |
| A022 | `0.2` | 정지 | stairs_15_up (내려가기) | 1 | 0.030 | 0 | 0.000 |
| G-A033 | `0.2` | 걷기 | stairs_10_down (오르기) | 3 | 0.199 / 0.180 / 0.192 | 1 / 2 / 3 | 0.875 / 0.531 / 0.531 |
| G-A033 | `0.2` | 걷기 | stairs_10_up (내려가기) | 3 | 0.369 / 0.367 / 0.367 | 0 / 0 / 0 | 1.000 / 0.969 / 1.000 |
| G-A033 | `0.2` | 걷기 | stairs_15_down (오르기) | 3 | 0.100 / 0.098 / 0.103 | 1 / 0 / 0 | 0.125 / 0.031 / 0.031 |
| G-A033 | `0.2` | 걷기 | stairs_15_up (내려가기) | 3 | 0.370 / 0.363 / 0.361 | 3 / 2 / 2 | 0.844 / 0.781 / 0.844 |
| Pilot-01 | `0.2` | 걷기 | stairs_10_down (오르기) | 3 | 0.138 / 0.131 / 0.130 | 2 / 2 / 1 | 0.125 / 0.125 / 0.094 |
| Pilot-01 | `0.2` | 걷기 | stairs_10_up (내려가기) | 3 | 0.383 / 0.382 / 0.389 | 0 / 0 / 0 | 0.750 / 0.750 / 0.875 |
| Pilot-01 | `0.2` | 걷기 | stairs_15_down (오르기) | 3 | 0.103 / 0.103 / 0.106 | 1 / 4 / 3 | 0.031 / 0.000 / 0.000 |
| Pilot-01 | `0.2` | 걷기 | stairs_15_up (내려가기) | 3 | 0.320 / 0.324 / 0.321 | 2 / 2 / 4 | 0.719 / 0.781 / 0.812 |
| feet_air_time_020_v1 | `0.2` | 정지 | stairs_10_down (오르기) | 3 | 0.029 / 0.030 / 0.029 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| feet_air_time_020_v1 | `0.2` | 정지 | stairs_10_up (내려가기) | 3 | 0.028 / 0.029 / 0.028 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| feet_air_time_020_v1 | `0.2` | 정지 | stairs_15_down (오르기) | 3 | 0.029 / 0.030 / 0.028 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| feet_air_time_020_v1 | `0.2` | 정지 | stairs_15_up (내려가기) | 3 | 0.028 / 0.029 / 0.028 | 0 / 0 / 0 | 1.000 / 1.000 / 1.000 |
| A015 | `0.35` | 정지 | stairs_15_up (내려가기) | 1 | 0.364 | 31 | 0.000 |
| A015 기준(Pilot 재평가) | `0.2` | 걷기 | stairs_15_up (내려가기) | 1 | 0.320 | 2 | 0.719 |

- **걷는 기준에서 오르기를 잰 발 들기 값은 `0.2` 하나뿐이다.** 발 들기 값에 따른 오르기 변화는 데이터가 없다.
- 걷는 기준에서 다른 값으로 계단을 잰 것은 A015(`0.35`) 내려가기 seed 1개뿐이다. 같은 날 잰 Pilot 기준보다 빨라졌지만 대부분 종료됐다.
- 정지 기준(Default-01 대 `feet_air_time_020_v1`, chain01 대 A022)에서는 두 값 모두 계단에서 움직이지 않아 비교 정보가 없다.
- A032는 체크포인트 iter 700으로 평가됐고 A017은 iter 900이다. 두 행은 같은 시점 비교가 아니다 (`GO2_REWARD_EVIDENCE_MASTER.md` 241행).
- A031·A032 결과 묶음(`_keep/go2_basic_motion_pair_a031_a032`)의 계단 기록은 내려가기 case 영상 1개뿐이고 원격 측정이 없다.
- 평가 기록에 발 위치·발 높이·접지 열이 없다(`steps.csv` 접촉 열은 몸통 접촉 `term_base_contact` 하나). 발이 계단 모서리에 걸리는지는 기록으로 볼 수 없다.
- 생존 proxy는 계측 세대가 다르다. Default-01·`feet_air_time_020_v1`은 낙상을 세지 않던 계측이라 멈춰 있어도 `1.000`이고, chain01·A022는 낙상 검출 계측이라 몸을 낮춘 정지가 `0.000`이다. 두 세대의 생존 값을 서로 비교하지 않는다 (`GO2_NOW.md` §0 [확보]).
- IL v2.3.1 `feet_air_time` 식은 `Σ(체공 시간 − 0.5 s) × 첫 접지`이고 명령 속도가 작으면 0이다. 발 높이가 아니라 **체공 시간**을 본다.

## 7. 기존 사양 대조

| 사양 | 바꾼 가중치 | 값 | 걷는 회차 관측값 | 위치 | 비고 |
|---|---|---|---|---|---|
| G-A037 | `lin_vel_z_l2` | `-1.0` | `-2.0`, `-1.5` | `OUT_OF_RANGE` | 도출 원리가 S5와 반대, 업로드 보류 · HOLD_CONTRADICTED |
| G-A038 | `ang_vel_xy_l2` | `-0.08` | `-0.05` | `OUT_OF_RANGE` | 실행(판정 없음, `reports/GO2_G_A038_READOUT.md`): 험지 옆걸음 종료 감소, 10cm 오르기 붕괴 — 승급 후보 아님 |
| G-A040 | `flat_orientation_l2` | `-0.5` | `0.0` | `OUT_OF_RANGE` | HOLD_UNSUPPORTED |
| G-A041 | `ang_vel_xy_l2` | `-0.04` | `-0.05` | `OUT_OF_RANGE` | INFORMATION_RUN |
| G-A042 | `track_lin_vel_xy_exp` | `1.6` | `1.2`, `1.4`, `1.5` | `OUT_OF_RANGE` | INFORMATION_RUN |
| G-A043 | `lin_vel_z_l2` | `-1.5` | `-2.0`, `-1.5` | `OBSERVED` | 도출 원리가 S5와 반대, 업로드 보류 · INFORMATION_RUN |
| G-A044 | `lin_vel_z_l2` | `-1.75` | `-2.0`, `-1.5` | `BETWEEN_OBSERVED` | 도출 원리가 S5와 반대, 업로드 보류 · INFORMATION_RUN |
