# G-A060 인계 — PC2(RTX 5070)에서 오늘 밤 세 점 학습 (PC2 Claude 세션용, 2026-10-03)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 사용자에게 같은 설명을 다시 요구하지 않는다.
루트 `AGENTS.md`(R-1~R-7), `GO2_NOW.md` 맨 아래 줄들을 함께 따른다.

## 0. 한눈에
- **목적:** 험지 옆걸음(G3)을 개선하면서 계단·우회전·밀침을 지킬 보상을 찾는 탐색이다. PC2 결과는 탐색 근거이고 제출 정책이 아니다(R-6·제14조).
- **오늘 밤 돌릴 것(사용자 결정, 계획의 시작 세 점):** 모두 A048 보상 위에서 한 항만 바꾸고, 학습 seed 42, 4096 env, 1000 iter, 평가 iter 900, 69 case, 영상 10편이다.
  1. `a048_seed42` — 기준선 B1(A048 그대로). PC2의 모든 비교 대조군이다.
  2. `ang_vel_xy_l2_m0p08` — ang_vel_xy −0.05→−0.08
  3. `track_lin_vel_xy_exp_p1p4` — track 1.5→1.4
- **순서 규칙:** B1이 정상 완료(exit 0)일 때만 2·3을 돈다. 2가 실패해도 3은 돈다. 네 번째 점은 이 세 결과를 보고 정하므로 오늘은 돌지 않는다.
- **예상 시간 [추정]:** 한 점 약 2시간, 세 점 약 6시간이다(서버 RTX 5080 실측 95분 기준 환산). PC2에서 실측해 다시 적는다.
- **설계 근거:** `workspace/training/quadruped/upload/plan/GO2_PC2_DENSE_SWEEP_PROPOSAL_20261002.md` §13·§14·§20.

## 1. 준비 확인
1. `git pull` 후 패키지가 있는지 확인한다: `workspace/training/quadruped/upload/G-A060/current/GO2_G_A060_PC2_a048_points_v1.zip`, SHA256 `a969c96a9f74d29664953e1a9c43655a328070eab176e1553257fdde722d47fd`.
2. OS를 확인한다. Windows면 PC1과 같은 방식을 쓴다: Git Bash, `/workspace` 마운트, `isaaclab.sh` 래퍼(`HANDOFF_G_A057_OTHER_PC.md` §5-b).
3. ZIP을 `/workspace/`에 복사한다. 원본은 저장소에 그대로 둔다.

## 2. 환경 기록 (학습 전, PC1과 같다고 가정하지 않는다)
- 다음을 기록한다: OS, GPU·드라이버·VRAM(`nvidia-smi`), CUDA, Isaac Sim 세부 버전, Isaac Lab 태그·커밋, torch·rsl-rl-lib 버전, Python, 디스크 여유.
- 기록 파일은 두 곳에 둔다.
  - `/workspace/_keep/go2_g_a060_pc2_points/PC2_ENV_RECORD.txt`
  - 저장소 `workspace/training/quadruped/reports/GO2_PC2_ENV_20261003.md`(서버·PC1과의 차이 표시)
- 평지 에셋 `Environments/Grid/default_environment.usd`가 있는지 확인한다. PC1에서는 이 파일이 없어 평가 case 하나가 실패한 적이 있다.
- 배포 학습 코드는 수정하지 않는다. 로봇 수(4096)도 줄이지 않는다.

## 3. 실행
- 패키지의 `run_point.sh`는 지정한 한 점만 돌고 멈춘다. 세 점은 아래처럼 이어서 실행한다.
- Isaac Lab이 `/workspace/IsaacLab`에 없으면 `export ISAACLAB_SH=<경로>/isaaclab.sh`를 먼저 한다.
- 실행 명령(`R=/workspace/go2_g_a060_pc2/run_point.sh`):
  - 먼저 `unzip -oq /workspace/GO2_G_A060_PC2_a048_points_v1.zip -d /workspace`
  - 그다음 `bash $R --inner a048_seed42 && { bash $R --inner ang_vel_xy_l2_m0p08; bash $R --inner track_lin_vel_xy_exp_p1p4; }`를 tmux 세션(Linux)이나 `nohup ... &`(Windows) 안에서 실행한다.
- 감시: `/workspace/_keep/go2_g_a060_pc2_points/POINT_STATUS.tsv`와 `point.log`를 본다. 짧은 간격의 폴링 루프는 띄우지 않는다.
  - 학습이 시작되면 iteration당 시간을 한 번 재서 남은 시간을 이 문서 §0에 적는다.
- 종료 코드:
  - 22: Isaac Lab·GPU를 못 찾음
  - 23: 학습 시작 전 실패(환경)
  - 21: 다른 학습이 돌고 있음
  - 20: 디스크 20 GB 미만
  - 30: 학습·평가 오류
  - 31: 수집 미완
  - 32: 학습 loss 비유한
- 시작 단계에서 실패하면(20~23) 원인을 기록하고 사용자에게 보고한 뒤 멈춘다. 4096 env가 메모리 부족이어도 로봇 수를 줄이지 않고 보고한다.
- 중간에 끊기면 같은 `--inner <key>`를 다시 실행한다. 부분 결과는 이어서 돌고, 완료된 점은 SKIP_DONE으로 건너뛴다.

## 4. 회수
- 점마다 다음 두 가지를 저장소 `workspace/_keep/`에 같은 이름으로 복사한다. 원본은 지우지 않는다.
  - `/workspace/_keep/go2_g_a060_pc2_<key>/` 폴더 전체(report.html 포함)
  - `GO2_G_A060_PC2_<KEY>_RESULT.zip`과 `.sha256`
- `/workspace/_keep/go2_g_a060_pc2_points/`(상태 표, 로그, 환경 기록)도 함께 복사한다.
- ZIP은 `sha256sum -c`로 확인한다. 100 MB를 넘으면 95 MB parts로 등재한다(루트 AGENTS 대용량 규칙, `workspace/_keep/reconstruct_zips.sh`).
- 다음 경우는 회수 완료로 보고하지 않는다.
  - report.html 누락 → `REPORT_REQUIRED_NOT_ACQUIRED`
  - 영상 10편 미달
- 커밋·푸시는 사용자가 요청할 때 한다.

## 5. 보고 (판독은 하지 않는다)
- 사용자 보고는 `## 0. 예선 기준 현재 위치`로 시작한다. 점마다 상태(DONE/FAILED)와 실측 시간만 적는다.
- 성능 판독은 하지 않는다. 판독 도구(`tools/go2_pc2_point_readout.py`)가 Codex 재검토(§19) 대기 중이라, 판독은 작성 PC에서 승인 뒤에 한다.
- 장비가 다르므로 PC2 결과를 PC1·서버 결과와 한 표에서 효과로 비교하지 않는다. PC2 점은 PC2 B1과만 비교한다.
- 다음 점(네 번째부터)은 정하지 않는다. 세 점의 판독 뒤 Codex가 정한다.
