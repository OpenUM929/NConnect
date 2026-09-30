# 외부 4족 보행 연구·공식 설정은 보상 값을 어떻게 정했나 (2026-09-30)

작성: Claude(메인 루프). 사용자 요청: "4족 보행에서 외부에서는 보상 값을 어떻게 선정했는지 찾아봐".
표기: [확인] 원문 직접 확인(아래 URL), [모름] 원문에 설명 없음. 새 값 제안은 없다.

## 1. 출처별 선정 방법
1. **Rudin et al. 2021 (legged_gym, ANYmal)** — https://arxiv.org/html/2109.11978
   - [확인] 선정 방법 설명이 없다. 원문: "After tuning of the reward weights, we can obtain a policy that respects all our constraints and can be transferred to the physical robot." 수동 조정이다.
   - [확인] 모든 지형에 같은 보상 한 벌을 쓴다("a single policy with the same rewards for all terrains").
   - [확인] feet_air_time은 "longer steps … more visually appealing behavior"를 위해 넣었다. 계단용 항이 아니다.
   - [확인] 계단은 보상이 아니라 지형 커리큘럼으로 풀었다(단 높이 5 → 20 cm). 학습 1500 iter.
   - legged_gym 기본값 [확인, `legged_robot_config.py`]: tracking_lin_vel 1.0, tracking_ang_vel 0.5, lin_vel_z −2.0, ang_vel_xy −0.05, orientation 0, torques −0.00001, dof_acc −2.5e−7, feet_air_time 1.0, action_rate −0.01, collision −1, only_positive_rewards=True, tracking_sigma 0.25.
2. **Hwangbo et al. 2019 (ANYmal, Science Robotics)** — https://arxiv.org/abs/1901.08652
   - [확인] 원문에 적힌 유일한 체계적 방법: **벌점 계수 커리큘럼**. 목표 항(속도 추종) 외의 모든 벌점에 k_c를 곱하고, k_c를 k0=0.3에서 시작해 매 iter k_c ← k_c^0.997로 1에 가깝게 올린다.
   - [확인] 이유: "a behavior is already a good local minimum when there is high penalty associated with motion"(움직임 벌점이 크면 서 있기가 국소 최적이 된다). 먼저 목표를 배우고 나중에 제약을 다듬는다.
   - [확인] k0는 "should be chosen to prevent the initial tendency to stand still. It can be easily tuned by observing the first one hundred iterations". 각 벌점의 기본 계수 자체의 선정 이유는 없다 [모름].
   - [확인] 발 들기는 체공시간이 아니라 **발 높이 목표 벌점**(foot clearance cost, 목표 0.07 m)으로 줬다.
3. **Margolis & Agrawal 2022 (Walk These Ways, Go1)** — https://arxiv.org/html/2212.03238
   - [확인] 계수 선정 방법 설명이 없다(Table 1에 값만 있음).
   - [확인] 계단은 명령으로 조절하는 발 스윙 높이 보상(−0.6)과 낮은 보행 빈도로 넘었다("a low frequency and high footswing height are necessary for stair traversal").
4. **Unitree 공식 unitree_rl_gym Go2** — https://github.com/unitreerobotics/unitree_rl_gym/blob/main/legged_gym/envs/go2/go2_config.py
   - [확인] legged_gym 기본값을 물려받고 torques −0.0002, dof_pos_limits −10.0, base_height_target 0.25만 바꾼다. 바꾼 이유 설명은 없다 [모름].
5. **Isaac Lab v2.3.1 Go2 rough** — https://github.com/isaac-sim/IsaacLab/blob/v2.3.1/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/go2/rough_env_cfg.py
   - [확인] 공통 설정을 물려받고 feet_air_time 0.01, dof_torques −0.0002, track_lin_vel_xy 1.5, track_ang_vel_z 0.75, dof_acc −2.5e−7, undesired_contacts None만 바꾼다. 이유 설명이 없고, 계단 성능도 발표하지 않았다 [모름].
6. **서베이** — https://arxiv.org/html/2406.01152v2 등: 보상 항 가중치는 엔지니어가 시행착오로 손으로 조정하는 것이 표준이며, 가중치에 민감해 결과가 일관되지 않을 수 있다고 정리한다 [확인, 검색 요약 수준].

## 2. 정리
- 외부의 공통 관행: **이미 있는 기본값(legged_gym)을 물려받고 로봇에 맞춰 몇 항만 바꾸며, 바꾼 값의 근거는 대개 적지 않는다.** 이론으로 값을 도출한 사례는 찾지 못했다.
- 원문에 방법이 적힌 것은 Hwangbo의 **벌점 계수 커리큘럼** 하나다. 동기("움직임 벌점이 크면 서 있기가 국소 최적")는 우리 계단 정지·가라앉음 양상과 같은 방향의 설명이다. 그러나 학습 중 계수를 바꾸려면 학습 코드 수정이 필요해 R-6상 쓸 수 없다.
- 계단 성공은 외부에서 **가중치 선택이 아니라** 지형 커리큘럼·학습 길이(Rudin) 또는 전용 보상 항(Hwangbo 발 높이 목표, Walk These Ways 발 스윙 높이)으로 얻었다.
- 한계: 로봇(ANYmal·Go1)과 보상 식·추종 폭이 우리와 다르다. 이 문서는 선정 방법의 조사이며 우리 값의 예측이 아니다.
