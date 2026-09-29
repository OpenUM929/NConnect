# 외부 사례 조사 — Isaac Lab·legged_gym 사족 보행 튜닝 (2026-09-29, 사용자 요청)

## 0. 예선 기준 현재 위치
- [예선 목표] G5 계단·G3 험지·G6 밀침. 우리 문제(15cm 오르기 실패, 험지 옆걸음 재착지 실패, feet_air_time 작용)에 닿는 외부 사례만 모았다.
- [현재 단계] 2/6, 보상 선정 전(기준 A048).
- [보장하지 않음] 외부 사례는 로봇·보상 항·학습 길이·지형이 우리와 다르다. 방향 참고이며 우리 결과의 예측이 아니다. R-6상 우리는 env에 있는 10개 항의 가중치만 바꿀 수 있다.

## 1. 출처별 사실
1. Rudin et al., CoRL 2021 "Learning to Walk in Minutes" (legged_gym 원형, ANYmal) — https://arxiv.org/abs/2109.11978
   - 보상 가중치(Table 2, dt 곱): 선속도 추종 1, 각속도 추종 0.5, z 속도 −4, roll·pitch 각속도 −0.05, 관절 가속·속도 −0.001, 토크 −0.00002, action rate −0.25, 충돌 −0.001, **feet air time 2**. feet air time이 선속도 추종의 2배다.
   - 계단은 커리큘럼으로 5→20 cm, 20 cm까지 거의 100% 성공. 학습 1500 iter. (높이 관측·커리큘럼과 함께 쓴 결과다. iter 수만 떼어 적용하지 않는다 — 2026-09-29 정정)
   - "dragging leg" 같은 행동 결함은 보상 가중치 조정이 필요했다고 적었다(구체값 없음).
2. Isaac Lab 공식 Go2 설정 — https://github.com/isaac-sim/IsaacLab (`config/go2/agents/rsl_rl_ppo_cfg.py`)
   - rough runner `max_iterations = 1500`, flat 300. feet_air_time 가중치는 rough 0.01, flat 0.25(우리 원장 `GO2_REWARD_EVIDENCE_MASTER.md` 표 A).
3. Isaac Lab Discussion #1977 / Issue #1955 "How to tune feet_air_time weight" — https://github.com/isaac-sim/IsaacLab/discussions/1977
   - Go2 사용자: "feet air time 보상을 넣으면 정책이 아예 발을 떼지 않는다." threshold를 낮추거나 가중치를 올려도 해결되지 않았다. 해결책은 공유되지 않았다.
4. Margolis & Agrawal, CoRL 2022 "Walk These Ways" (Go1) — https://proceedings.mlr.press/v205/margolis23a/margolis23a.pdf
   - "낮은 걸음 빈도와 높은 발 스윙 높이가 계단 통과에 필요하다."
   - 몸을 낮게 붙이는 "crouch" 걸음은 계단을 못 넘고, 몸을 높이 들고 발을 높이 드는 "stomp" 걸음은 턱·계단을 넘는다.
   - "넓은 스탠스"는 밀침에 강하지만 다른 과제(빠른 달리기)에는 불리하다. 일반 정책은 발을 엉덩이 아래에 두도록 유도되는 경우가 많다.
   - 발 스윙 높이 추적 보상(−0.6), 몸 높이 추적(−0.2) 같은 별도 항을 썼다. 시각 없는 기존 정책은 "먼저 걸려 넘어질 뻔한 뒤 발을 드는 반사(foot-trapping reflex)"를 학습했다고 적었다.
5. 단계 학습 사례 — gpai-robotics go2-lab-rough-terrain-locomotion (https://github.com/gpai-robotics/go2-lab-rough-terrain-locomotion): 평지 → 험지·경사 → 계단 미세조정 3단계. 가중치 공개 없음.
6. StairMaster (arXiv 2606.25765, Go2): 계단 모서리 벌점·발 위치 항 등 **맞춤 보상 항**으로 가파른 계단을 해결. 우리 env에는 없는 항이다.

## 2. 우리 문제와의 대응 [판단]
- **계단 대 험지·밀침의 상충은 외부에서도 보고된다.** Walk These Ways의 crouch/stomp·넓은 스탠스 설명은 우리 A048(몸 낮음 0.243 m, 발 넓게 → 험지·밀침 강함, 15cm ≥2단 24)과 A043(몸 높음 0.341 m → 15cm 77, 험지·우회전 약함) 관측과 같은 방향이다. 한 정책이 한 걸음 성격만 가지면 둘을 동시에 얻기 어렵다는 설명이다(인과 확정 아님).
- **계단에 필요한 걸음 = 낮은 빈도·높은 발 스윙.** feet_air_time(threshold 0.5초)은 걸음 빈도를 낮추는 쪽의 항이다. A048은 걸음 97.5~99.7%가 0.5초보다 짧다(`GO2_A048_AIR_TIME_CHECK_20260929.md`). 다만 우리 자료에서 긴 체공이 높은 발 들림과 비례하지 않았고, 발 스윙 높이를 직접 보상하는 항은 우리 env에 없다.
- **feet_air_time의 상대 비중.** 원형(Rudin)은 선속도 추종의 2배, Isaac Lab Go2 rough는 0.01(추종 1.5의 1/150), 우리는 0.2(추종의 약 1/7). 외부 공식 값끼리도 20배 이상 차이 난다. 어느 값이 계단에 맞는지 외부 사례로 정해지지 않는다.
- **"보상을 넣으면 발을 떼지 않는다"(Isaac Lab #1977)는 우리 추정(짧은 착지마다 음수 → 착지 횟수 감소로 비용 회피)과 같은 방향의 사용자 보고다.** 원인 설명은 그 토론에 없다.
- **학습 길이.** 원형·Isaac Lab Go2 rough 모두 1500 iter, 우리는 1000 iter. 배포 설명도 "걸음 성격은 3000~5000 iter". G-A035(1000→1500) 보류 중.
- **외부에서 계단을 푼 방법 대부분은 우리가 못 쓰는 것이다**: 발 스윙 높이·몸 높이 추적 항, 계단 모서리 벌점, 교사-학생 학습, 계단 전용 미세조정 단계. R-6상 가중치만 바꿀 수 있다. 지형 높이 관측(`height_scan`)과 terrain_levels 커리큘럼은 우리 env에도 이미 있다(A048 `training/env.yaml`의 `scene.height_scanner`·`observations.policy.height_scan`·`curriculum.terrain_levels`). 그러므로 "그것이 없어서 계단에서 실패한다"는 설명은 틀리다(2026-09-29 정정).
