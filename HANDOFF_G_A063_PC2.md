# G-A063 인계 — PC2(RTX 5070) 계단 집중 범위 스윕 14점 (PC2 Claude 세션용, 2026-10-05)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 루트 `AGENTS.md`(R-1~R-7)와 `GO2_NOW.md` 맨 위 줄을 함께 따른다.
PC2 환경 우회(마운트, isaaclab.sh shim, pyshim, D3D12 영상 런처)는 G-A060·G-A061·G-A062 때와 같다(`HANDOFF_PC2_CONTINUOUS_MONITOR_20261003.md`, `workspace/_keep/go2_g_a060_pc2_run_chain.sh`).

## 0. 한눈에
- **설계:** `workspace/training/quadruped/upload/plan/GO2_PC2_STAIRS_RANGE_SWEEP_20261004.md`
- **시작 조건:** G-A062 일괄 실행(P6·P4)이 끝난 뒤 시작한다. 두 학습을 동시에 돌리지 않는다.
- **무엇을 하나:** 모든 점의 부모는 P0(PC2 A048, track 1.5)다. 점마다 보상 한 항만 배포 추천 범위 안에서 바꾼다.
- **실행 방식:** 14점을 명령 한 줄로 순서대로 돈다. 점당 약 2시간 25분, 합계 약 34시간 [추정]이다.
  1. `s01_lin_vel_z_l2_m5` — lin_vel_z −1.25 → −5.0
  2. `s02_lin_vel_z_l2_m3` — lin_vel_z → −3.0
  3. `s03_lin_vel_z_l2_m2` — lin_vel_z → −2.0
  4. `s04_lin_vel_z_l2_m0p5` — lin_vel_z → −0.5
  5. `s05_feet_air_time_p0p01` — feet_air_time 0.2 → 0.01
  6. `s06_feet_air_time_p0p1` — feet_air_time → 0.1
  7. `s07_feet_air_time_p0p35` — feet_air_time → 0.35
  8. `s08_feet_air_time_p0p5` — feet_air_time → 0.5
  9. `s09_ang_vel_xy_l2_m0p3` — ang_vel_xy −0.05 → −0.3
  10. `s10_ang_vel_xy_l2_m0p15` — ang_vel_xy → −0.15
  11. `s11_ang_vel_xy_l2_m0p02` — ang_vel_xy → −0.02
  12. `s12_action_rate_l2_m0p02` — action_rate −0.01 → −0.02
  13. `s13_action_rate_l2_m0p005` — action_rate → −0.005
  14. `s14_p0_repeat` — P0 그대로 재학습(학습 흔들림 측정). RUN_GUIDE에는 `lin_vel_z_l2 -> -1.25`로 보이지만 값은 P0와 같다.
- **결과의 용도:** PC2 결과는 탐색 근거이고 제출 정책이 아니다.

## 1. 준비 확인
1. `git pull`한 뒤 패키지를 확인한다.
   - 경로: `workspace/training/quadruped/upload/G-A063/current/GO2_G_A063_PC2_STAIRS_SWEEP_v1.zip`
   - SHA256: `e02e5eae1f226dd4efee4413b4aed37d571f936e546add69ae5b19005c46cccd`
   - 확인: `cd workspace/training/quadruped/upload/G-A063/current && sha256sum -c GO2_G_A063_PC2_STAIRS_SWEEP_v1.zip.sha256`
2. G-A062가 끝났는지 확인한다: `/workspace/_keep/go2_g_a062_pc2_points/BATCH_RUN.log`에 `[BATCH END]` 줄이 있어야 한다.
3. 다른 학습(train.py·play.py)이 돌고 있지 않은지 확인한다. 돌고 있으면 첫 점이 rc 21로 거부되고 일괄 실행이 멈춘다.
4. ZIP을 `/workspace/`에 복사한다: `cp workspace/training/quadruped/upload/G-A063/current/GO2_G_A063_PC2_STAIRS_SWEEP_v1.zip /workspace/`

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
   unzip -oq /workspace/GO2_G_A063_PC2_STAIRS_SWEEP_v1.zip -d /workspace && nohup bash /workspace/go2_g_a063_pc2/run_all.sh > /workspace/_keep/go2_g_a063_batch_console.log 2>&1 &
   ```
3. GPU 감시(별도 셸, 같은 환경 변수 뒤):
   ```bash
   bash tools/go2_gpu_watch.sh --hours 40 --pattern 'go2_g_a063_pc2_*'
   ```
   - **`--pattern`을 반드시 준다.** 빠뜨리면 지난 회차를 감시한다.
   - 감시는 기록만 하고 프로세스를 끄지 않는다.
4. 진행 확인:
   ```bash
   tail -n 5 /workspace/_keep/go2_g_a063_pc2_points/BATCH_RUN.log
   cat /workspace/_keep/go2_g_a063_pc2_points/POINT_STATUS.tsv
   ```

## 3. 실패 처리
- **rc 20~25 (환경·패키지):** run_all이 남은 점을 멈춘다. 고친 뒤 §2의 같은 한 줄을 다시 실행한다. 끝난 점은 SKIP_DONE으로 넘어간다.
- **rc 30·31 (학습 뒤 평가·회수 실패):** run_all이 다음 점으로 간다. 전체가 끝난 뒤 `bash /workspace/go2_g_a063_pc2/run_point.sh --only <key>`로 그 점만 재개한다. 재학습은 없다.
- **학습 도중 실패(iter 900 checkpoint 없음):** 자동 재학습하지 않는다. 보고한다.
- **영상 Vulkan 실패:** G-A060의 D3D12 영상 런처 우회를 쓴다. 배포 코드는 수정하지 않는다.

## 4. 회수 (끝난 점부터 바로)
- 점마다 다음을 저장소 `workspace/_keep/`에 같은 이름으로 복사한다.
  - `/workspace/_keep/go2_g_a063_pc2_<key>/` 폴더 전체
  - `GO2_G_A063_PC2_<KEY>_RESULT.zip`과 `.sha256`
- 함께 복사할 것: `/workspace/_keep/go2_g_a063_pc2_points/`, GPU 감시 기록, 콘솔 로그.
- 100MB 초과 ZIP은 95MB parts로 나누고 원본 ZIP은 `.gitignore`에 넣는다(`ARTIFACT_MANAGEMENT.md` §6-a). 예:
  ```bash
  cd workspace/_keep && split -b 95000000 -d -a 3 GO2_G_A063_PC2_<KEY>_RESULT.zip GO2_G_A063_PC2_<KEY>_RESULT.zip.
  ```
  `workspace/_keep/reconstruct_zips.sh` 목록에도 이름을 추가한다.
- 점마다 report.html(`exported/report.html`)과 영상 10편이 있어야 한다. 없으면 그 점은 회수 완료가 아니다.
- **끝난 점부터 한 점씩 커밋·푸시한다.** 작성 PC가 받는 대로 판독한다. 커밋 메시지 예: `chore: publish G-A063 PC2 <key> result as 95MB parts`

## 5. 보고 (판독은 하지 않는다)
- 사용자 보고는 `## 0. 예선 기준 현재 위치`로 시작한다.
- 점마다 상태(DONE/FAILED), rc, 실측 시간을 적는다.
- 성능 판독은 작성 PC가 한다: 점마다 `tools/go2_pc2_tree_readout.py read --node <key> --change <term>=<value> --point workspace/_keep/go2_g_a063_pc2_<key> --parent workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42`, s14는 `--change` 대신 `--repeat`.
