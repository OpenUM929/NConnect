<!-- PC2_HANDOFF
WORK_ID: G-A065
STATUS: READY
START_AFTER: G-A063
START_MARKER: /workspace/_keep/go2_g_a063_pc2_points/BATCH_RUN.log 에 [BATCH END]
PACKAGE: workspace/training/quadruped/upload/G-A065/current/GO2_G_A065_PC2_DIAG_REPLAY_v1.zip
PACKAGE_SHA256: 56d5fd2f24d0654977f3b7714421b999fa4f1e6bf65ed21ce88dddc0c74fad36
-->
# G-A065 인계 — PC2(RTX 5070) 진단 재생 5정책 (학습 없음, PC2 Claude 세션용, 2026-10-06)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 루트 `AGENTS.md`(R-1~R-7, 「PC2 작업 인계」 절)와 `GO2_NOW.md` 맨 위 줄을 함께 따른다.
PC2 환경 우회(마운트, isaaclab.sh shim, pyshim)는 G-A060~G-A063 때와 같다. 이번 실행은 영상을 만들지 않으므로 D3D12 영상 우회는 필요 없다.

## 0. 한눈에
- **설계·합의:** `workspace/training/quadruped/upload/plan/GO2_G_A063_SWEEP_CODEX_CONSULT_20261006.md` §25·§26 (Codex 3/3 APPROVE, 사용자 승인 "진단 먼저")
- **무엇을 하나:** 학습하지 않는다. 보상을 바꾸지 않는다. 이미 학습된 PC2 정책 5개를 같은 평가기로 다시 재생한다. 재생에는 읽기 전용 진단 채널(몸통 roll·pitch 속도, 발 위치·접촉력, 관절 위치·속도·토크)이 붙는다.
- **정책(실행 순서, 모두 PC2 학습 iter 900):**
  1. `p0` — P0 (G-A060 B1, A048 보상)
  2. `s04` — P0 + lin_vel_z −0.5
  3. `s11` — P0 + ang_vel_xy −0.02
  4. `s13` — P0 + action_rate −0.005
  5. `s07` — P0 + feet_air_time 0.35 (G-A064 부모)
- **정책마다:** `stairs_15_down`·`rough_lateral` × 평가 seed 202·101·303 × plain·diag = 12회. 합계 60회.
- **시간 [추정]:** 서버 실측은 회당 21~33초였다. 합계 약 30~40분과 초기화 시간이다. PC2에서는 잰 적이 없다.
- **시작 조건:** G-A063이 끝난 뒤(`[BATCH END]`, s14 회수까지 완료 확인됨). G-A064보다 먼저 한다(G-A064는 `START_AFTER: G-A065`).
- **결과의 용도:** 행동 경로 진단 자료다. 성능 판정·제출 근거가 아니다.

## 1. 준비 확인
1. `git pull`한 뒤 패키지를 확인한다.
   - 경로: `workspace/training/quadruped/upload/G-A065/current/GO2_G_A065_PC2_DIAG_REPLAY_v1.zip`
   - SHA256: `56d5fd2f24d0654977f3b7714421b999fa4f1e6bf65ed21ce88dddc0c74fad36`
   - 확인: `cd workspace/training/quadruped/upload/G-A065/current && sha256sum -c GO2_G_A065_PC2_DIAG_REPLAY_v1.zip.sha256`
2. G-A063이 끝났는지 확인한다: `/workspace/_keep/go2_g_a063_pc2_points/BATCH_RUN.log`에 `[BATCH END]`가 있어야 한다.
3. 다른 train.py·play.py가 돌고 있지 않은지 확인한다. 돌고 있으면 러너가 rc 21로 거부한다.
4. `workspace/_keep/pc2_handoff_ledger.tsv`에 `G-A065<TAB>STARTED<TAB>시각`을 적고 커밋·푸시한다.
5. ZIP을 `/workspace/`에 복사한다: `cp workspace/training/quadruped/upload/G-A065/current/GO2_G_A065_PC2_DIAG_REPLAY_v1.zip /workspace/`

## 2. 실행 (Git Bash)
1. 환경 변수(매 셸마다 한 번, G-A063 인계 §2와 같다):
   ```bash
   mount -o binary,noacl,posix=0,user C:/workspace /workspace
   export ISAACLAB_SH=/workspace/bin/isaaclab.sh
   export PYTHONIOENCODING=utf-8
   export PYTHONUTF8=1
   export KMP_DUPLICATE_LIB_OK=TRUE
   export PYTHONUNBUFFERED=1
   export PATH="/c/workspace/bin/pyshim:$PATH"
   ```
2. 실행 한 줄:
   ```bash
   unzip -oq /workspace/GO2_G_A065_PC2_DIAG_REPLAY_v1.zip -d /workspace && nohup bash /workspace/go2_g_a065_pc2/run_all.sh > /workspace/_keep/go2_g_a065_batch_console.log 2>&1 &
   ```
3. 진행 확인: `tail -n 5 /workspace/_keep/go2_g_a065_pc2_points/BATCH_RUN.log`
4. GPU 감시는 이번에는 선택이다(학습 없음, 약 40분). 돌릴 경우 `--pattern 'go2_g_a065_pc2_*'`를 반드시 준다.

## 3. 실패 처리
- 러너가 0이 아닌 코드로 끝나면 `run_all`이 남은 정책을 멈춘다. 고친 뒤 §2의 같은 한 줄을 다시 실행한다. 끝난 정책은 `SKIP_DONE`으로 넘어간다.
  - rc 2: 패키지·평가기·정책 SHA·소스 불일치
  - rc 21: 다른 학습·재생이 돌고 있음
  - rc 33: 이전 결과가 남아 있음
  - rc 5: 재생 하나가 실패함(`/workspace/_keep/go2_g_a065_pc2_<key>/logs/`)
- 같은 정책을 일부러 처음부터 다시 돌릴 때만 `GO2_DISCARD_PREVIOUS=1`을 앞에 붙인다. 내려받기 전에는 쓰지 않는다.
- 배포 코드(train.py·play.py·task)는 수정하지 않는다.

## 4. 회수
- 정책마다 저장소 `workspace/_keep/`에 같은 이름으로 복사한다.
  - `/workspace/_keep/go2_g_a065_pc2_<key>/` 폴더 전체
  - `GO2_G_A065_PC2_<KEY>_RESULT.zip`과 `.sha256`
- 함께 복사할 것: `/workspace/_keep/go2_g_a065_pc2_points/`, 콘솔 로그.
- 100MB 초과 ZIP은 95MB parts로 나눈다(`ARTIFACT_MANAGEMENT.md` §6-a). 예: `split -b 95000000 -d -a 3 <ZIP> <ZIP>.`
- **정책 5개가 다 끝나면 한 번에 커밋·푸시한다.** 커밋 메시지 예: `chore: publish G-A065 PC2 diag replay results`
- 원장에 `G-A065<TAB>DONE<TAB>시각`(실패 시 `FAILED<TAB>rc`)을 추가한다.

## 5. 보고 (판독은 하지 않는다)
- 사용자 보고는 `## 0. 예선 기준 현재 위치`로 시작한다.
- 정책마다 다음을 적는다: RUNS_DONE, `meta/REPRO_STATUS.txt`의 IDENTICAL 수(6이어야 한다), `meta/RUN_TIMES.txt`의 wall_s 합.
- 판독(roll 선행 대 지지 실패 선행, 분기 A~F)과 G-A064 순서 결정은 작성 PC가 한다.
