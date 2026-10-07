<!-- PC2_HANDOFF
WORK_ID: G-A068
STATUS: READY
START_AFTER: NONE
START_MARKER: NONE
PACKAGE: workspace/training/quadruped/upload/G-A068/current/GO2_G_A068_PC2_DIAG_REPLAY_v1.zip
PACKAGE_SHA256: 51ba29f00f30317fc253d4a7d00b1a0e4a4c8499d4c39db519b035dc6e5dc40a
-->
# G-A068 인계 — PC2(RTX 5070) 진단 재생 3정책 c6·c3·c2 + 행동 판독 (학습 없음, PC2 Claude 세션용, 2026-10-07)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 루트 `AGENTS.md`(R-1~R-7, 「PC2 작업 인계」 절)를 따른다. 진행 방식은 G-A066과 같다(`HANDOFF_G_A066_PC2.md`). 다른 점만 적는다.

## 0. 한눈에
- **설계·합의:** `workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md` §14-2·§16·§17, Codex 직접 협의(순서 c6 → c3 → c2).
- **무엇을 하나:** 학습하지 않는다. G-A064의 c6(ang −0.035)·c3(action −0.0075)·c2(lin −0.5) 정책을 G-A066과 같은 평가기·진단 채널로 다시 재생한다. 정책마다 stairs_15_down·rough_lateral × 평가 seed 202·101·303 × plain·diag = 12회, 합계 36회.
- **시간 [추정]:** G-A066 PC2 실측(정책당 529~543초)으로 약 27분 + 초기화.
- **시작 조건:** 없음. 다른 train.py·play.py가 돌고 있으면 시작하지 않는다.
- **그 다음:** 끝나면 G-A069(c6 학습 seed 43, START_AFTER G-A068)가 이어서 시작된다.

## 1. 준비 확인
1. `git pull` 뒤 SHA 확인: `cd workspace/training/quadruped/upload/G-A068/current && sha256sum -c GO2_G_A068_PC2_DIAG_REPLAY_v1.zip.sha256`
2. 원장에 `G-A068<TAB>STARTED<TAB>시각`을 적고 커밋·푸시한다.
3. `cp workspace/training/quadruped/upload/G-A068/current/GO2_G_A068_PC2_DIAG_REPLAY_v1.zip /workspace/`

## 2. 실행 (Git Bash)
1. 환경 변수는 G-A066 인계 §2와 같다.
2. 재생 한 줄:
   ```bash
   unzip -oq /workspace/GO2_G_A068_PC2_DIAG_REPLAY_v1.zip -d /workspace && nohup bash /workspace/go2_g_a068_pc2/run_all.sh > /workspace/_keep/go2_g_a068_batch_console.log 2>&1 &
   ```
3. 진행 확인: `tail -n 5 /workspace/_keep/go2_g_a068_pc2_points/BATCH_RUN.log` — `[BATCH END]`가 찍히면 끝이다.
4. **재생이 끝나고 §4 회수(저장소 `workspace/_keep/`로 복사)를 마친 뒤**, 저장소 루트에서 행동 판독을 돌린다(GPU 없음, 약 1~2분):
   ```bash
   PYTHONIOENCODING=utf-8 PYTHONUTF8=1 nice -n 10 python -B tools/go2_g_a067_behavior_analysis.py --prefix go2_g_a068_pc2_ --policies p0,s07,c6,c3,c2 --out workspace/_keep/go2_g_a068_analysis
   ```
   p0·s07은 G-A066 폴더에서 읽는 기준 비교다. `workspace/_keep/go2_g_a068_analysis/STATUS.txt`에 `G_A067_ANALYSIS=COMPLETE`가 있어야 한다.

## 3. 실패 처리
- 재생 rc는 G-A066 인계 §3과 같다(rc 2 패키지·SHA 불일치, rc 21 다른 프로세스, rc 33 이전 결과, rc 5 재생 실패).
- 판독 스크립트 오류는 RUN.log를 회수하고 `FAILED<TAB>analysis`로 적는다. 스크립트를 고치지 않는다.

## 4. 회수
- 정책마다 `/workspace/_keep/go2_g_a068_pc2_<key>/` 폴더 전체와 `GO2_G_A068_PC2_<KEY>_RESULT.zip`·`.sha256`, 그리고 `/workspace/_keep/go2_g_a068_pc2_points/`, 콘솔 로그를 저장소 `workspace/_keep/`로 복사한다. 100MB 초과 ZIP은 95MB parts로 나눈다.
- 판독 결과 `workspace/_keep/go2_g_a068_analysis/`도 함께 커밋·푸시한다.
- 원장에 `G-A068<TAB>DONE<TAB>시각`을 추가한다.

## 5. 보고 (판독은 하지 않는다)
- 정책마다 RUNS_DONE, `meta/REPRO_STATUS.txt`의 IDENTICAL 수(6이어야 한다), 판독 STATUS만 적는다.
