# Go2 열린 결정 원장 (2026-09-18)

> **생성 문서 — 손으로 고치지 않는다.** `python -B tools/go2_open_decisions.py` 가 만든다.
> 증거 `reports/evidence/go2_open_decisions_20260918/DECISIONS.csv`, 관문 `tools/test_go2_open_decisions_contract.py`.

여기 적힌 것은 **우리가 스스로 내렸지만 사용자가 승인하지 않은 해석**이다. 산문에 붙인 `[모름]` 은 파일을 건너가지 못한다 — 그래서 결정마다 번호를 주고, 그 해석에 기대는 산출물마다 번호를 글자로 박아 둔다.

`WIDENS` 는 우리 권한을 **넓히는** 해석이다. 이쪽은 엄격히 본다 — 규칙 밖을 막는 대신 규칙을 넓혀 통과시키는 것이 보존 사례 C02 의 모양이기 때문이다.

## U1-R6-ENV-REWARD-20260918  ·  OPEN  ·  WIDENS

- **질문**: 배포 `REWARD_WEIGHTS` 6개 목록 **밖**의 env RewTerm 가중치를 바꾸는 회차가 R-6 안인가?
- **우리가 임시로 택한 해석**: R-6 안으로 판단하고 `change_class: env_reward_weight` 를 신설했으며, 관문 상수 `R6_CHANGE_CLASSES` 에 그 값을 추가해 추천을 통과시켰다.
- **이 해석이 허용하는 `change_class`**: `env_reward_weight`
- **이 해석이 사용자 결정임을 적어 둔 원문**: `workspace/training/quadruped/reports/GO2_REWARD_MECHANISM_FORECAST.md` — "R-6 해석은 사용자 결정이다"
- **이 해석에 기대는 산출물**:
  - `tools/test_go2_detectability_gate.py`
  - `tools/build_go2_a033_reward_package.py`
  - `.claude/agents/go2-planner.md`
  - `.claude/agents/go2-analyst.md`
  - `.claude/agents/go2-auditor.md`
  - `.codex/agents/go2-campaign-manager.md`
  - `.codex/agents/go2-evaluation-auditor.md`
  - `.codex/agents/go2-report-writer.md`
  - `.codex/agents/go2-test-planner.md`
  - `workspace/training/quadruped/config/experiments/G_A039_a033_dof_acc_m125e7.json`
  - `GO2_NOW.md`
- **왜 중요한가**: 규칙 밖 추천을 막는 대신 규칙 쪽을 넓혀 통과시킨 것이다(보존 사례 C02와 같은 모양). 2026-09-18 정정: 이 칸은 '기각되면 6개 목록 안에 남은 레버가 없다'고 적고 있었다 — 원장 GO2_REWARD_EVIDENCE_MASTER.md §1-a 가 lin_vel_z_l2 양방향·ang_vel_xy_l2 완화·action_rate_l2 강화·flat_orientation_l2 를 '미탐색'으로 적고 있어 그 전제는 거짓이다(분석가 판독 GO2_TUNING_POLICY_READOUT_20260918.md §2). 기각돼도 목록 안에 갈 곳은 남는다 — 다만 넷 다 걷는 기준선 유효 시도 0건이라 기울기를 잴 수 없다(OUT_OF_RANGE). 반대 행도 더 강하다: dof_acc_l2 는 배포 판정기 go2_task/_finalize.py 의 _REP_BASELINE·_REP_INTENT·_REP_ADV 어디에도 없어 extras 에조차 들어가지 않는다 — 배포 판정기에게 그 변경은 존재하지 않는다. 반면 목록 안 주석 3항(track_ang_vel_z_exp·undesired_contacts·termination_penalty)은 _REP_INTENT 에 등재돼 있다.

## U2-SEED-REPLICATE-20260918  ·  OPEN  ·  WIDENS

- **질문**: 같은 설정·다른 학습 seed 로 다시 돌리는 재현 회차가 R-6 안인가?
- **우리가 임시로 택한 해석**: **차단 조건에는 걸리지 않는다**고 읽고 정보 회차로 실행한다 — R-6 이 막는 것은 배포 학습 코드의 수정인데 seed 는 배포 `train.py` 가 해석하지 않고 상류 Isaac Lab `rsl_rl/train.py` 로 그대로 넘기는 CLI 인자이고(배포 `go2_task/` 에는 seed 가 없다), 지금까지의 전 회차도 같은 경로로 `--seed 42` 를 넘겼다. 동시에 **보상 변경이 아니므로 승급은 금지**한다: `change_class: training_seed` 를 신설하고, 이 분류의 사양은 `promotion` 을 `forbidden_not_a_reward_change` 로 적어야만 관문을 지난다. 2026-09-18 판단(밖으로 보고 후보로 올리지 않는다)의 결론은 유지되고, 달라진 것은 **실행까지 막지는 않는다**는 것뿐이다.
- **이 해석이 허용하는 `change_class`**: `training_seed`
- **이 해석이 사용자 결정임을 적어 둔 원문**: `workspace/training/quadruped/reports/GO2_SEED_SENSITIVITY.md` — "seed 반복 회차가 R-6(보상 가중치만) 안인지는 사용자 결정 대기다"
- **이 해석에 기대는 산출물**:
  - `tools/test_go2_detectability_gate.py`
  - `tools/build_go2_seed_pair_package.py`
  - `workspace/training/quadruped/server_run_go2_full69_campaign.sh`
  - `workspace/training/quadruped/config/experiments/G_A045_seed43_a033_rewards.json`
  - `workspace/training/quadruped/config/experiments/G_A046_seed43_lin_vel_z_m15.json`
  - `workspace/training/quadruped/upload/plan/GO2_A045_SEED_PAIR_PLAN_20260924.md`
  - `GO2_NOW.md`
- **왜 중요한가**: 학습은 seed 42 하나뿐이라 한 회차의 차이가 레버인지 seed 운인지 가를 수 없다. 열리지 않으면 어떤 회차도 레버 효과를 확정하지 못하고 사슬을 지지/반증만 한다. 2026-09-24 추가: 이 공백이 이제 판정 자체를 흔든다 — 같은 다이얼 세 점에서 계단 계수기는 단조인데 낙상 계수기는 가운데 값에서만 솟았고(`reports/evidence/go2_seed_pair_20260924/MONOTONICITY.csv`), 회차 간 총점 차이(-3.63·+2.10)가 승급 문턱(2.53)과 같은 자리에 있다. **이 결정이 닫히지 않으면 우리는 자를 잴 수 없고, 자를 모르면 지금까지의 FAIL 도 읽을 수 없다.** 반대로 사용자가 '밖이다, 실행도 하지 말라'로 닫으면 G-A045·G-A046 은 폐기하고 단일 seed 판정의 한계를 문서로만 적는다.

## 승인되면 / 기각되면

사용자가 승인하면 `status` 를 `APPROVED` 로 바꾸고 결정 번호(`G-D-...`)를 함께 적는다. 기각되면 `REJECTED` 로 바꾸고, 그 해석에 기대던 산출물을 모두 되돌린다 — 위 목록이 되돌릴 대상의 전부다.
