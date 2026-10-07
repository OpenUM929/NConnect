<!-- PC2_HANDOFF
WORK_ID: G-A069
STATUS: READY
START_AFTER: G-A068
START_MARKER: /workspace/_keep/go2_g_a068_pc2_points/BATCH_RUN.log 에 [BATCH END]
PACKAGE: workspace/training/quadruped/upload/G-A069/current/GO2_G_A069_PC2_C6_SEED43_v1.zip
PACKAGE_SHA256: 84744be6b02156de7e2abe178622950b98f95bc3f439b8731ed57e67918feacc
-->
# G-A069 인계 — PC2(RTX 5070) c6 학습 seed 43 재현 1점 (PC2 Claude 세션용, 2026-10-07)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 실행·회수 방식은 G-A064와 같다(`HANDOFF_G_A064_PC2.md` §2~§4). 다른 점만 적는다.

## 0. 한눈에
- **설계·합의:** `workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md` §17, Codex 직접 협의(독립 seed 확인은 c6 하나).
- **무엇을 하나:** G-A064 c6와 **같은 보상**(s07 + ang_vel_xy −0.035)을 **학습 seed 43**으로 다시 학습하고 같은 평가 69 case를 돈다. 점 하나다.
  - 점 key: `c6s43_s07_ang_vel_xy_l2_m0p035`
- **왜:** c6는 계단 높이 유지 3→45로 다섯 점 중 유일하게 R1을 충족했지만, 같은 항의 양 끝 값과 정반대라 학습 흔들림인지 확인한다.
- **시간 [추정]:** 약 2시간 15분(G-A064 실측).
- **시작 조건:** G-A068 재생이 끝난 뒤(`/workspace/_keep/go2_g_a068_pc2_points/BATCH_RUN.log`에 `[BATCH END]`). G-A068의 판독 스크립트(CPU)는 겹쳐도 된다.

## 1. 준비 확인
1. `git pull` 뒤 SHA 확인: `cd workspace/training/quadruped/upload/G-A069/current && sha256sum -c GO2_G_A069_PC2_C6_SEED43_v1.zip.sha256`
2. 다른 train.py·play.py가 없는지 확인한다.
3. 원장에 `G-A069<TAB>STARTED<TAB>시각`을 적고 커밋·푸시한다.
4. `cp workspace/training/quadruped/upload/G-A069/current/GO2_G_A069_PC2_C6_SEED43_v1.zip /workspace/`

## 2. 실행 (Git Bash)
1. 환경 변수는 G-A064 인계 §2와 같다.
2. 실행 한 줄:
   ```bash
   unzip -oq /workspace/GO2_G_A069_PC2_C6_SEED43_v1.zip -d /workspace && nohup bash /workspace/go2_g_a069_pc2/run_all.sh > /workspace/_keep/go2_g_a069_batch_console.log 2>&1 &
   ```
3. GPU 감시: `bash tools/go2_gpu_watch.sh --hours 4 --pattern 'go2_g_a069_pc2_*'`
4. 진행 확인: `tail -n 5 /workspace/_keep/go2_g_a069_pc2_points/BATCH_RUN.log`

## 3. 실패 처리
- G-A064 인계 §3과 같다.

## 4. 회수
- `/workspace/_keep/go2_g_a069_pc2_c6s43_s07_ang_vel_xy_l2_m0p035/` 폴더 전체, `GO2_G_A069_PC2_C6S43_S07_ANG_VEL_XY_L2_M0P035_RESULT.zip`·`.sha256`(100MB 초과면 95MB parts), `/workspace/_keep/go2_g_a069_pc2_points/`, GPU 감시 기록, 콘솔 로그를 저장소 `workspace/_keep/`로 복사해 커밋·푸시한다.
- report.html(`exported/report.html`)과 영상 10편이 있어야 회수 완료다.
- 원장에 `G-A069<TAB>DONE<TAB>시각`을 추가한다.

## 5. 보고 (판독은 하지 않는다)
- 상태(DONE/FAILED), rc, 실측 시간만 적는다. 판독은 작성 PC가 G-A064 c6(seed 42)와 비교해서 한다.
