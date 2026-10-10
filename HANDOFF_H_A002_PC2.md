<!-- PC2_HANDOFF
WORK_ID: H-A002
STATUS: READY
START_AFTER: G-A077
START_MARKER: /workspace/_keep/go2_g_a077_flat_orientation_m0p225/RUNNER_STATUS.txt
PACKAGE: workspace/training/humanoid/upload/H-A002/current/H_A002_ACTION_RATE_M0P002_v1.zip
PACKAGE_SHA256: d6cbdf8a6705dc28fe250297098140d507bf4d70a08603f6abfcaf6c54cd00ba
-->

# H-A002 — H1 기존 P0 판독 후 대응 1000iter 탐색

## 0. 한눈에

- 설계: 대조 action_rate_l2 -.0005 / 후보 -.002만 다르게, 각 from-scratch1000iter·seed42·4096env. 동일 best-reward checkpoint 규칙. 원인/최적값 증명이나 Run06 채택 비교가 아니다.
- 시작 조건: G-A077 회수·판독 commit/push 완료, 이 문서 READY·SHA 검증, 기존 PC2의 GPU 작업 없음. G-A077 원본 collection rc31은 baseline 영상 기대0/실제10 집계 오류이며 별도 감사로69/69·10/10 양팔 회수 검증 완료. 원본 표식을 수정하거나 A077을 다시 실행하지 않는다.
- 점: control1000 → candidate1000 → 각57 telemetry·10영상 → 회수·판독. H-A001 완료54/54는 재실행하지 않는다. 추가 Go2 없음.
- 예상 시간: 이 PC2의 H1 1000iter 실측이 없어 완료 시간을 확정하지 않는다. 30분마다 실제 iter/1000, cases/114, videos/20을 보고한다.
- 계획: workspace/training/humanoid/upload/plan/H1_H_A002_ACTION_RATE_PLAN_20261010.md. 3000/10000iter 자동 승급 없음.

## 1. 준비 확인

1. ZIP와 sidecar SHA 및 내부 PACKAGE_SHA256SUMS.txt를 대조한다. READY가 아니면 실행 금지.
2. G-A077 원장 terminal·회수 감사·판독의 원격 commit을 확인한다. 프로세스 목록과 nvidia-smi에서 train/play 없음, 여유20GB 이상, 기존 IsaacLab/venv를 확인한다. 새 서버 세션을 열지 않는다.
3. 기존 H1 배포 train/play/task는 e288246 정본 SHA를 사용한다. runtime logic 수정 금지. 기존 Run06 exported 파일은 사전 snapshot 후 성공/실패 모두 복구하며, 기존 H-A002 KEEP가 있으면 자동 재실행하지 않는다.
4. 원본 Run06을 쓰는2-step asset preflight가 완료된 뒤에만 새 학습을 시작한다. 이것은 완료 P0 격자 반복이 아니다.

## 2. 실행

Git Bash에서 ZIP를 /workspace/training/humanoid/로 복사하고 SHA 검증 후:

```bash
cd /workspace/training/humanoid && unzip -o H_A002_ACTION_RATE_M0P002_v1.zip && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH NO_TMUX=1 H1_ROOT=/workspace/training/humanoid ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh bash h1_ha002/server_run_h1_ha002.sh
```

기존 launcher/배포 train/play/evaluator를 사용한다. 각 팔 train.log의 실제 iter와 nvidia-smi를 확인한다. 단일 GPU에서 중복 실행하지 않는다. tools/watch_h1_pc2_progress.ps1은 파일 기반 진행률만 기록하고, tools/pc2_hourly_monitor_prompt.md의 예약 Codex가 이 대화에 한국어로 보고·후속 판독한다.

## 3. 실패 처리

- rc2/3: 선행 프로세스·기존 KEEP·Isaac/GPU·asset/preflight 차단. 진행 중 프로세스 종료·자동 재시도 금지.
- rc4~7: reward/source·학습·fresh checkpoint/env·report 실패. 완료한 팔을 재학습하지 않고 원 로그·부분 결과를 보존한다.
- rc8~10: telemetry/영상 수집 실패. checkpoint를 보존하고 평가 복구만 판단한다. completed=false나 EVAL_RC 비정상은 완료 case로 세지 않는다.
- 실패 시 원본 source와 Run06 canonical exported를 복구하고 PARTIAL ZIP/SHA 및 원 rc를 보존한다. 원본 표식을 FULL로 바꾸지 않는다.

## 4. 회수

- /workspace/_keep/H_A002_ACTION_RATE_M0P002/
- /workspace/_keep/H_A002_ACTION_RATE_M0P002_RESULT.zip 및 .sha256
- 각 팔 model/env/reward/report/log/tfevents, evaluator·experiment·manifest·선택iter/identity, telemetry57개·영상10개를 검증한다. 영상은 fixed seed101.
- ZIP CRC·내부 manifest·외부 SHA를 대조한 뒤95MiB parts로 나눠 git에 등재(100MB 초과 시). 원본은 ignore하며 LFS를 쓰지 않는다. 회수·원장 commit/push 후 원격 SHA를 확인한다.
- 필수 bundle·영상·telemetry·SHA의 로컬 검증 전 종료 가능 판정 금지. 기존 PC2 실행은 휘발 서버 종료와 구분한다.

## 5. 보고

실행 담당은 실제 iter/case/video/회수·차단만 보고한다. 작성 담당이 대응1000iter 비교를 판독하고 VIDEO/INTERNAL_GATE/OFFICIAL_RESULT를 분리한다. 전체 평가·영상·회수 전 학습 정상 종료를 성능 완료로 보고하지 않는다. 사용자 일반 승인을 다시 묻지 않고 안전한 기존 후속을 진행한다.
