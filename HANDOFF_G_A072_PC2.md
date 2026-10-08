<!-- PC2_HANDOFF
WORK_ID: G-A072
STATUS: READY
START_AFTER: G-A069
START_MARKER: /workspace/_keep/go2_g_a069_pc2_points/BATCH_RUN.log 에 [BATCH END]
PACKAGE: workspace/training/quadruped/upload/G-A072/current/GO2_G_A072_PC2_SEED43_REPRO_v1.zip
PACKAGE_SHA256: 59d3e2f67dc81a9f59e14aed0c72b1f2db1504fc23fb22986395e5278a90e580
-->
# G-A072 인계 — PC2(RTX 5070) 학습 seed 43 재현 4점 (PC2 Claude 세션용, 2026-10-08)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 실행·회수 방식은 G-A064·G-A069와 같다(`HANDOFF_G_A064_PC2.md` §2~§4). 다른 점만 적는다.

## 0. 한눈에
- **설계·합의:** `workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md` §62~§66.
- **무엇을 하나:** G-A063의 계단 이득 점들과 그 부모 P0를 **학습 seed 43**으로 다시 학습하고, 같은 평가 69 case를 돈다. 점은 넷이고 아래 순서로 실행한다.
  1. `s04s43_lin_vel_z_l2_m0p5`: P0 + lin_vel_z −1.25→−0.5
  2. `p0s43_lin_vel_z_l2_m1p25`: P0 그대로, seed 43 대조
  3. `s13s43_action_rate_l2_m0p005`: P0 + action_rate −0.01→−0.005
  4. `s11s43_ang_vel_xy_l2_m0p02`: P0 + ang_vel_xy −0.05→−0.02
- **왜:** G-A069에서 c6의 계단 이득이 seed 43에서 사라졌다. 그래서 기존 계단 이득 점이 다른 학습에서도 나오는지 확인한다.
- **시간 [추정]:** 점당 약 2시간 15분, 합계 약 9시간이다.
- **시작 조건:** G-A069가 끝났으면 바로 시작한다(`/workspace/_keep/go2_g_a069_pc2_points/BATCH_RUN.log`에 `[BATCH END]`).

## 1. 준비 확인
1. `git pull` 뒤 SHA를 확인한다: `cd workspace/training/quadruped/upload/G-A072/current && sha256sum -c GO2_G_A072_PC2_SEED43_REPRO_v1.zip.sha256`
2. 다른 train.py·play.py가 돌고 있지 않은지 확인한다.
3. 원장에 `G-A072<TAB>STARTED<TAB>시각`을 적고 커밋·푸시한다.
4. `cp workspace/training/quadruped/upload/G-A072/current/GO2_G_A072_PC2_SEED43_REPRO_v1.zip /workspace/`

## 2. 실행 (Git Bash)
1. 환경 변수는 G-A064 인계 §2와 같다.
2. 실행 한 줄:
   ```bash
   unzip -oq /workspace/GO2_G_A072_PC2_SEED43_REPRO_v1.zip -d /workspace && nohup bash /workspace/go2_g_a072_pc2/run_all.sh > /workspace/_keep/go2_g_a072_batch_console.log 2>&1 &
   ```
3. GPU 감시: `bash tools/go2_gpu_watch.sh --hours 12 --pattern 'go2_g_a072_pc2_*'`
4. 진행 확인: `tail -n 5 /workspace/_keep/go2_g_a072_pc2_points/BATCH_RUN.log`

## 3. 실패 처리
- G-A064 인계 §3과 같다. 남은 점을 멈춰야 하면 `touch /workspace/_keep/go2_g_a072_pc2_points/STOP`만 한다.

## 4. 회수
- **점이 하나 끝날 때마다 바로 회수한다.** 다음 점을 기다리지 않는다. 회수할 것은 다음과 같다.
  - `/workspace/_keep/go2_g_a072_pc2_<key>/` 폴더 전체
  - `GO2_G_A072_PC2_<KEY>_RESULT.zip`·`.sha256` (100MB 초과면 95MB parts)
  - 이것들을 저장소 `workspace/_keep/`로 복사해 커밋·푸시한다.
- 모든 점이 끝나면 `/workspace/_keep/go2_g_a072_pc2_points/`, GPU 감시 기록, 콘솔 로그도 회수한다.
- 점마다 report.html(`exported/report.html`)과 영상 10편이 있어야 회수 완료다.
- 원장에 `G-A072<TAB>DONE<TAB>시각`을 추가한다.

## 5. 보고 (판독은 하지 않는다)
- 점마다 상태(DONE/FAILED), rc, 실측 시간만 적는다. 판독은 작성 PC가 G-A063 seed 42 결과와 비교해서 한다.
