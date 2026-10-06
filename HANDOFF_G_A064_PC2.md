<!-- PC2_HANDOFF
WORK_ID: G-A064
STATUS: HOLD
START_AFTER: G-A065
START_MARKER: /workspace/_keep/go2_g_a065_pc2_points/BATCH_RUN.log 에 [BATCH END]
PACKAGE: workspace/training/quadruped/upload/G-A064/current/GO2_G_A064_PC2_S07_COMBO_v2.zip
PACKAGE_SHA256: 7f7c66f7c0dbc50f29cf272eec9135151b8b6141e79d148a6cfad0435e112ef4
-->
# G-A064 인계 — PC2(RTX 5070) s07 부모 위 계단 레버 조합·중간값 5점 (v2) (PC2 Claude 세션용, 2026-10-06)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 루트 `AGENTS.md`(R-1~R-7, 「PC2 작업 인계」 절)와 `GO2_NOW.md` 맨 위 줄을 함께 따른다.
PC2 환경 우회(마운트, isaaclab.sh shim, pyshim, D3D12 영상 런처)는 G-A060~G-A063 때와 같다(`HANDOFF_PC2_CONTINUOUS_MONITOR_20261003.md`, `workspace/_keep/go2_g_a060_pc2_run_chain.sh`).

**머리말 `STATUS: HOLD`인 동안은 시작하지 않는다.** 작성 PC가 `READY`로 바꾼 커밋을 받은 뒤에만 시작한다.

## 0. 한눈에
- **설계·합의:** `workspace/training/quadruped/upload/plan/GO2_G_A063_SWEEP_CODEX_CONSULT_20261006.md` §12~§15, §25·§26(v2: c4 제외, 순서 변경)
- **시작 조건:** G-A065 진단 재생이 끝난 뒤(`[BATCH END]`)에 시작한다. 두 작업을 동시에 돌리지 않는다.
- **v2 순서는 진단 전 기본 순서다.** G-A065 결과로 순서가 바뀌면 작성 PC가 v3로 다시 내고 이 문서를 고친다.
- **무엇을 하나:** 모든 점의 부모는 S07 = P0(PC2 A048, track 1.5) + feet_air_time 0.35(G-A063 s07)다. 점마다 보상 한 항만 바꾼다.
- **실행 방식:** 5점을 명령 한 줄로 순서대로 돈다. 점당 약 2시간 25분, 합계 약 12시간 [추정].
  1. `c1_s07_ang_vel_xy_l2_m0p02` — ang_vel_xy −0.05 → −0.02
  2. `c2_s07_lin_vel_z_l2_m0p5` — lin_vel_z −1.25 → −0.5
  3. `c3_s07_action_rate_l2_m0p0075` — action_rate −0.01 → −0.0075
  4. `c6_s07_ang_vel_xy_l2_m0p035` — ang_vel_xy −0.05 → −0.035
  5. `c5_s07_lin_vel_z_l2_m0p875` — lin_vel_z −1.25 → −0.875
- **결과의 용도:** PC2 결과는 탐색 근거이고 제출 정책이 아니다.

## 1. 준비 확인
1. `git pull`한 뒤 패키지를 확인한다.
   - 경로: `workspace/training/quadruped/upload/G-A064/current/GO2_G_A064_PC2_S07_COMBO_v2.zip`
   - SHA256: `7f7c66f7c0dbc50f29cf272eec9135151b8b6141e79d148a6cfad0435e112ef4`
   - 확인: `cd workspace/training/quadruped/upload/G-A064/current && sha256sum -c GO2_G_A064_PC2_S07_COMBO_v2.zip.sha256`
2. G-A065가 끝났는지 확인한다: `/workspace/_keep/go2_g_a065_pc2_points/BATCH_RUN.log`에 `[BATCH END]` 줄이 있어야 한다.
3. 다른 학습(train.py·play.py)이 돌고 있지 않은지 확인한다. 돌고 있으면 첫 점이 rc 21로 거부되고 일괄 실행이 멈춘다.
4. `workspace/_keep/pc2_handoff_ledger.tsv`에 `G-A064<TAB>STARTED<TAB>시각`을 적고 커밋·푸시한다(AGENTS.md 「PC2 작업 인계」 PC2 3항).
5. ZIP을 `/workspace/`에 복사한다: `cp workspace/training/quadruped/upload/G-A064/current/GO2_G_A064_PC2_S07_COMBO_v2.zip /workspace/`

## 2. 실행 (Git Bash)
1. 환경 변수(매 셸마다 한 번):
   ```bash
   mount -o binary,noacl,posix=0,user C:/workspace /workspace
   export ISAACLAB_SH=/workspace/bin/isaaclab.sh
   export PYTHONIOENCODING=utf-8
   export PYTHONUTF8=1
   export KMP_DUPLICATE_LIB_OK=TRUE
   export PYTHONUNBUFFERED=1
   export PATH="/c/workspace/bin/pyshim:$PATH"
   ```
2. 실행 한 줄(백그라운드):
   ```bash
   unzip -oq /workspace/GO2_G_A064_PC2_S07_COMBO_v2.zip -d /workspace && nohup bash /workspace/go2_g_a064_pc2/run_all.sh > /workspace/_keep/go2_g_a064_batch_console.log 2>&1 &
   ```
3. GPU 감시(별도 셸, 같은 환경 변수 뒤):
   ```bash
   bash tools/go2_gpu_watch.sh --hours 16 --pattern 'go2_g_a064_pc2_*'
   ```
   - **`--pattern`을 반드시 준다.** 빠뜨리면 지난 회차를 감시한다. 감시는 기록만 하고 프로세스를 끄지 않는다.
4. 진행 확인:
   ```bash
   tail -n 5 /workspace/_keep/go2_g_a064_pc2_points/BATCH_RUN.log
   cat /workspace/_keep/go2_g_a064_pc2_points/POINT_STATUS.tsv
   ```

## 3. 실패 처리
- **rc 20~25 (환경·패키지):** run_all이 남은 점을 멈춘다. 고친 뒤 §2의 같은 한 줄을 다시 실행한다. 끝난 점은 SKIP_DONE으로 넘어간다.
- **rc 30·31 (학습 뒤 평가·회수 실패):** run_all이 다음 점으로 간다. 전체가 끝난 뒤 `bash /workspace/go2_g_a064_pc2/run_point.sh --only <key>`로 그 점만 재개한다. 재학습은 없다.
- **학습 도중 실패(iter 900 checkpoint 없음):** 자동 재학습하지 않는다. 보고한다.
- **영상 Vulkan 실패:** G-A060의 D3D12 영상 런처 우회를 쓴다. 배포 코드는 수정하지 않는다.

## 4. 회수 (끝난 점부터 바로)
- 점마다 다음을 저장소 `workspace/_keep/`에 같은 이름으로 복사한다.
  - `/workspace/_keep/go2_g_a064_pc2_<key>/` 폴더 전체
  - `GO2_G_A064_PC2_<KEY>_RESULT.zip`과 `.sha256`
- 함께 복사할 것: `/workspace/_keep/go2_g_a064_pc2_points/`, GPU 감시 기록, 콘솔 로그.
- 100MB 초과 ZIP은 95MB parts로 나누고 원본 ZIP은 `.gitignore`에 넣는다(`ARTIFACT_MANAGEMENT.md` §6-a):
  ```bash
  cd workspace/_keep && split -b 95000000 -d -a 3 GO2_G_A064_PC2_<KEY>_RESULT.zip GO2_G_A064_PC2_<KEY>_RESULT.zip.
  ```
  `workspace/_keep/reconstruct_zips.sh` 목록에도 이름을 추가한다.
- 점마다 report.html(`exported/report.html`)과 영상 10편이 있어야 한다. 없으면 그 점은 회수 완료가 아니다.
- **끝난 점부터 한 점씩 커밋·푸시한다.** 커밋 메시지 예: `chore: publish G-A064 PC2 <key> result as 95MB parts`
- 5점이 모두 끝나면 원장에 `G-A064<TAB>DONE<TAB>시각`(실패 시 `FAILED<TAB>rc`)을 추가하고 커밋·푸시한다.

## 5. 보고 (판독은 하지 않는다)
- 사용자 보고는 `## 0. 예선 기준 현재 위치`로 시작한다.
- 점마다 상태(DONE/FAILED), rc, 실측 시간을 적는다.
- 성능 판독은 작성 PC가 한다. 비교 부모는 s07 회수본이다. 점마다 다음 명령을 쓴다.
  ```bash
  tools/go2_pc2_tree_readout.py read --node <key> --change <term>=<value> --point workspace/_keep/go2_g_a064_pc2_<key> --parent workspace/_keep/go2_g_a063_pc2_s07_feet_air_time_p0p35
  ```
