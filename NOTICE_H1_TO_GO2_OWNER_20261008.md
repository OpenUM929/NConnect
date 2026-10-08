#  H1 세션 → Go2 튜닝 정책 담당에게 전달 두 가지 (H1 세션 Claude, 2026-10-08, 사용자 지시)

이 절은 H1(2족) 세션이 쓴다. Go2 판독·값 선택은 하지 않는다. 사용자 지시 두 가지를 전한다.

**1. 학습 횟수가 지정 최소치(1,500회)에 못 미친다.**
- 사용자 원문: "4족 보행 튜닝 정책을 담당하는 이에게 현재 지정된 튜닝 횟수(최소 1500회)를 만족하지 않고 있다고 전달하자."
- 확인한 사실:
  - G-A072 4점은 `MAX_ITERATIONS=1000`, 평가 checkpoint는 iter 900이다(`GO2_G_A072_PC2_SEED43_REPRO_v1.zip`의 `point_config.env`).
  - G-A063·G-A064·G-A069 계열도 같은 1,000회 / 평가 900 구조다(`GO2_REWARD_EVIDENCE_MASTER.md:251` "스크리닝 1000").
  - Isaac Lab 공식 Go2 rough 설정은 `max_iterations=1500`이다(`reports/evidence/go2_curriculum_source_20260918/isaaclab_tasks_go2_agents_rsl_rl_ppo_cfg.py`).
  - 학습 길이만 바꾸는 G-A035(1000→1500, 보상 무변경)는 계획만 있고 실행하지 않았다(`GO2_REWARD_EVIDENCE_MASTER.md:144`).
- 그래서 지금까지의 Go2 판독(계단 이득의 seed 재현 실패 포함)은 지정 최소치 미만의 학습에서 나온 것이다. 이 사실을 다음 회차 설계에 반영해 달라. 값·순서 판단은 Go2 담당이 한다.

**2. PC2 순서: G-A072 다음은 H1 H-A001이다.**
- `HANDOFF_H_A001_PC2.md`(STATUS READY, `START_AFTER: G-A072`)를 git에 올렸다.
- 내용은 H1 Run06·Run05 속도 격자 재생이다. 학습은 없고, GPU 약 1~2시간 [추정].
- 사용자 지시는 "4족 보행 튜닝 작업이 끝나면 우리 작업을 진행"이다. §68의 checkpoint 재생 등 다음 Go2 작업은 `START_AFTER: H-A001`(START_MARKER: `/workspace/_keep/h1_ha001_console.log`에 `[DONE] H-A001`)로 잡아 달라.

원본: 작성 PC 로컬 `GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md` §69(git 판은 §19까지라 이 파일로 따로 올린다).
