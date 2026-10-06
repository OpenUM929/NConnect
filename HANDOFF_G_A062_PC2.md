# G-A062 인계 — PC2(RTX 5070) 60점 목표 일괄 실행 6점 (PC2 Claude 세션용, 2026-10-04)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 루트 `AGENTS.md`(R-1~R-7)와 `GO2_NOW.md` 맨 아래 줄을 함께 따른다.
PC2 환경 우회(마운트, isaaclab.sh shim, pyshim, D3D12 영상 런처)는 G-A060·G-A061 때와 같다(`HANDOFF_PC2_CONTINUOUS_MONITOR_20261003.md`, `workspace/_keep/go2_g_a060_pc2_run_chain.sh`).

## 0. 한눈에
- **설계:** `workspace/training/quadruped/upload/plan/GO2_PC2_BATCH_60_STRATEGY_20261004.md`
- **실행 방식:** 6점을 명령 한 줄로 순서대로 돈다. 점당 약 2시간 25분, 합계 약 15시간 [추정]이다.
  1. `q0_lin_vel_z_l2_m1p5` (A043 보상 재현, Q 계열 부모)
  2. `q1_track_ang_vel_z_exp_p1p0`
  3. `q2_ang_vel_xy_l2_m0p06`
  4. `p5_dof_acc_l2_m1p25e_7`
  5. `p6_dof_acc_l2_m6p25e_8`
  6. `p4_dof_torques_l2_m5e_5`
- **G-A061 N5 단독 ZIP과의 관계:** N5 단독 ZIP은 **돌리지 않는다.** 4번 점과 보상이 같다.
- **결과의 용도:** PC2 결과는 탐색 근거이고 제출 정책이 아니다.

## 1. 준비 확인
1. `git pull`한 뒤 패키지를 확인한다.
   - 경로: `workspace/training/quadruped/upload/G-A062/current/GO2_G_A062_PC2_BATCH60_v1.zip`
   - SHA256: `33a629abf15dbc44b027718ac3b7ec9c050a8ebfd1a2c71e2889ca8294f56f7e`
   - 확인 명령: `sha256sum -c`
2. ZIP을 `/workspace/`에 복사한다.
3. 다른 학습(train.py·play.py)이 돌고 있지 않은지 확인한다. 돌고 있으면 첫 점이 rc 21로 거부되고 일괄 실행이 멈춘다.

## 2. 실행
- **환경 변수:** `go2_g_a060_pc2_run_chain.sh` 머리의 mount·export 줄을 먼저 실행한다.
- **실행 한 줄:** `unzip -oq /workspace/GO2_G_A062_PC2_BATCH60_v1.zip -d /workspace && bash /workspace/go2_g_a062_pc2/run_all.sh`
  - Windows에서는 `nohup … > /workspace/_keep/go2_g_a062_batch_console.log 2>&1 &`로 띄운다.
- **GPU 감시:** `tools/go2_gpu_watch.sh --hours 18 --pattern 'go2_g_a062_pc2_*'`
  - **`--pattern`을 반드시 준다.** 기본값이 G-A060이라 빠뜨리면 지난 회차를 감시한다.
  - 감시는 기록만 하고 프로세스를 끄지 않는다.
- **진행 확인:** `/workspace/_keep/go2_g_a062_pc2_points/BATCH_RUN.log`, `POINT_STATUS.tsv`

## 3. 실패 처리
| 상황 | 처리 |
|---|---|
| rc 20~25 (환경·패키지) | run_all이 남은 점을 멈춘다. 고친 뒤 같은 한 줄을 다시 실행한다. 끝난 점은 SKIP_DONE으로 넘어간다 |
| rc 30·31 (학습 뒤 평가·회수 실패) | run_all이 다음 점으로 간다. 전체가 끝난 뒤 `bash /workspace/go2_g_a062_pc2/run_point.sh --only <key>`로 그 점만 재개한다. 재학습은 없다 |
| 학습 도중 실패(iter 900 checkpoint 없음) | 자동 재학습하지 않는다. 보고한다 |
| 영상 Vulkan 실패 | G-A060의 D3D12 영상 런처 우회를 쓴다. 배포 코드는 수정하지 않는다 |

## 4. 회수
- 점마다 다음을 저장소 `workspace/_keep/`에 같은 이름으로 복사한다.
  - `/workspace/_keep/go2_g_a062_pc2_<key>/` 폴더 전체
  - `GO2_G_A062_PC2_<KEY>_RESULT.zip`과 `.sha256`
- 함께 복사할 것: `/workspace/_keep/go2_g_a062_pc2_points/`, GPU 감시 기록, 콘솔 로그.
- 100MB 초과 ZIP은 95MB parts로 나누고, `workspace/_keep/reconstruct_zips.sh` 목록에 이름을 추가한다.
- 점마다 report.html과 영상 10편이 있어야 한다. 없으면 그 점은 회수 완료가 아니다.
- **일부 점만 끝났어도 끝난 점부터 회수·푸시해도 된다.** 작성 PC가 끝난 점부터 판독한다.

## 5. 보고 (판독은 하지 않는다)
- 사용자 보고는 `## 0. 예선 기준 현재 위치`로 시작한다.
- 점마다 상태(DONE/FAILED), rc, 실측 시간을 적는다.
- 성능 판독과 다음 일괄 실행은 작성 PC가 `tools/go2_pc2_tree_readout.py read --change`로 한다.
