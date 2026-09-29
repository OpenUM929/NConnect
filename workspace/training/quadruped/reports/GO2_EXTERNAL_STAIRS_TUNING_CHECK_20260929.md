# Codex 계단 전략의 외부 근거 재검토 (2026-09-29)

작성: Claude(메인 루프). 사용자 요청: "외부 정보를 활용해서 ISAAC 튜닝 방향이 codex가 말한 게 맞는지 검토해봐".
표기: [확인] 원문 확인, [추정] 해석, [모름] 근거 없음. 새 실험·값 제안은 없다.

## 1. 읽은 원문
- Isaac Lab v2.3.1 `velocity_env_cfg.py`: 공통 RewardsCfg, height_scan, CurriculumCfg
- Isaac Lab v2.3.1 `config/go2/rough_env_cfg.py`: Go2 덮어쓰기
- Isaac Lab v2.3.1 `mdp/rewards.py`: `feet_air_time` 식
- Rudin et al. 2021, arXiv 2109.11978 (NVIDIA·ETH, legged_gym), 그리고 legged_gym `legged_robot_config.py`·`legged_robot.py`
- Margolis & Agrawal 2022 (Walk These Ways), arXiv 2212.03238
- 우리 A048 `workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/training/env.yaml` (커밋 b18a9b2)

## 2. Codex 주장별 판정
1. **"Rudin은 20cm 계단에서 거의 100% 성공, 높이 관측·커리큘럼과 함께"** — [확인]. 논문 원문: "steps up to 0.2 m … nearly 100% success rate". 높이 관측은 108점, 게임식 지형 커리큘럼을 썼다. "1500 policy updates"라는 숫자만 떼어 쓰면 안 된다는 지적도 맞다.
2. **"우리 env에 높이 관측·커리큘럼이 이미 있다"** — [확인]. A048 env.yaml에 `scene.height_scanner`, `observations.policy.height_scan`, `curriculum.terrain_levels`(`terrain_levels_vel`)가 있다. 학습 지형의 40%가 계단이고(pyramid_stairs 0.2 + inv 0.2), 계단 높이는 `step_height_range` 0.05~0.23 m다. G5의 10~15cm는 이 범위 안에 있다.
3. **"feet_air_time은 발 높이가 아니라 착지 시 체공시간을 평가한다"** — [확인]. 식은 `sum((last_air_time − threshold) × first_contact)`이고, 명령 크기 0.1 초과일 때만 켜진다. 다만 원문 docstring은 이 항의 목적을 "helps ensure that the robot lifts its feet off the ground and takes steps"라고 적는다.
4. **"Walk These Ways는 계단에 낮은 보행 빈도·높은 발 스윙을 쓴다"** — [확인]. 원문: "a low frequency and high footswing height are necessary for stair traversal". 그런데 이 정책은 고유감각만 쓰고(높이 관측 없음), 발 스윙 높이·접촉 일정·몸 높이 추적 같은 전용 보상 항이 있다. 우리 R-6 범위(가중치만 변경)에는 이런 항이 없다. "feet_air_time 상향 = 계단"의 증거가 아니라는 Codex 판단은 맞다.
5. **"0.01은 Isaac Lab Go2 설정의 비교점"** — [확인]. Go2 rough 설정이 `feet_air_time.weight = 0.01`이다. 공통 설정 값은 0.125다.
   - 한계: Isaac Lab은 Go2 설정의 계단 성공률을 발표하지 않는다. 0.01은 "Isaac Lab이 Go2에 쓴 값"일 뿐 "계단에 유리한 값"이라는 근거가 없다. [확인]

## 3. Codex가 다루지 않은 외부 사실 — 하향 방향과 충돌한다
- 외부에서 계단 성공을 수치로 보고한 기준은 Rudin/legged_gym 하나다. 그 설정은 같은 체공 식(threshold 0.5)을 쓰고, **`feet_air_time` 1.0 · `lin_vel_z` −2.0 · `ang_vel_xy` −0.05 · `action_rate` −0.01**이다. [확인]
- dt는 모든 항에 똑같이 곱해지므로 항끼리의 비율은 비교할 수 있다. `feet_air_time` ÷ |`lin_vel_z`| 비율은 다음과 같다. [확인한 값으로 계산]
  - legged_gym(계단 성공 보고): 1.0/2.0 = 0.5
  - Isaac Lab 공통: 0.125/2.0 = 0.0625
  - 우리 A048: 0.2/1.25 = 0.16
  - Codex 시험(A048 + 0.01): 0.01/1.25 = 0.008
  - Isaac Lab Go2: 0.01/2.0 = 0.005
- 계단 성공이 보고된 설정은 **짧은 착지를 음수로 만드는 똑같은 식을 우리보다 상대적으로 더 강하게** 썼다. 따라서 "짧은 재접지를 음수로 만드는 것이 계단을 막는다"는 Codex의 기전 가설은 외부 기준과 맞지 않는다. [추정: 로봇(ANYmal)과 크기가 다르고, legged_gym은 `only_positive_rewards=True`로 음수 총보상을 0으로 자른다는 차이가 있다]
- Rudin 논문은 이 항을 "visually appealing behavior"를 위한 것이라고만 적고, 계단에 대한 효과는 분석하지 않았다. 따라서 이 비율 자료는 올리라는 근거도 아니다. [확인]

## 4. 결론
- Codex가 인용한 외부 사실은 대부분 정확하다(§2의 1~5).
- 그러나 결론 방향 "계단을 위해 feet_air_time을 0.01로 낮춘다"는 외부 근거로 지지되지 않는다.
  - 계단 성공을 보고한 유일한 기준은 체공 항을 상대적으로 강하게 썼다.
  - 0.01은 계단 성능이 발표되지 않은 Isaac Lab Go2 기본값이다.
  - 강좌·배포 설명도 하향이 "등반약"이라고 한다(`GO2_LECTURE_REWARD_REFERENCE.md` §6-b).
- 이것은 2026-09-29 Codex 최종 지시(0.01은 일반 탐색 행으로만 유지, 계단 우선 2×2 철회)와 같은 방향이다.
- 외부 연구에서 계단에 직접 쓰인 도구(발 스윙 높이·보행 빈도 명령, 모서리 벌점, 교사-학생 학습)는 모두 보상 항 추가나 코드 변경이 필요하다. R-6상 쓸 수 없다. [확인]
- [모름] 가중치만으로 G5를 올리는 레버가 외부 문헌에 있는지는 이번 원문들로 답할 수 없다.
