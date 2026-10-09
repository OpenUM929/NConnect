<!-- PC2_HANDOFF
WORK_ID: G-A074
STATUS: READY
START_AFTER: G-A076 terminal DONE or FAILED; do not stop it
START_MARKER: /workspace/_keep/go2_g_a076_report_policy/RUNNER_STATUS.txt
PACKAGE: workspace/training/quadruped/upload/G-A074/recovery/current/GO2_G_A074_EVAL_RECOVERY_v1.zip
PACKAGE_SHA256: cfee0ebfc432ce0dcfd2cfeb4ac7ee65a1464236928f777160b3886068f1e457
-->

# G-A074 completed-checkpoint evaluation recovery

## 0. 한눈에
- 목적: 이미 완료된 G-A074 학습의 iter-2400 checkpoint로 69-case telemetry와 영상을 이어서 수집한다.
- 학습: 새 학습 없음. 복구 러너에는 `train.py` 실행 명령이 없으며 `TRAIN_RC=0`과 checkpoint SHA가 다르면 rc 40으로 종료한다.
- 시작 조건: 현재 G-A076 프로세스를 중단하지 않는다. G-A076이 terminal 상태가 된 뒤 결과를 보존하고, G-A074 평가가 미완료일 때만 시작한다.
- 고정 checkpoint: `d39b88e9a6b06fd08498c90bbba334a3aaaca1cc8e540102c7d0e284bac72211`.
- 예상 시간: 69-case와 영상 수집 시간만 필요하며 새 3,000-iteration 학습 시간은 들지 않는다.

## 1. 준비 확인
1. `git pull` 후 패키지 SHA를 검사한다.
   ```bash
   REPO_ROOT=$(git rev-parse --show-toplevel)
   cd "$REPO_ROOT/workspace/training/quadruped/upload/G-A074/recovery/current"
   sha256sum -c GO2_G_A074_EVAL_RECOVERY_v1.zip.sha256
   ```
2. G-A076의 ledger가 terminal이어도 `pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py'`로 실제 프로세스가 없는지 함께 확인한다. 프로세스가 있으면 stale marker로 보고 기다리며 종료시키지 않는다.
3. `/workspace/_keep/go2_g_a074_report_policy/training/TRAIN_STATUS.txt`가 `TRAIN_RC=0`이고 `model_best.pt` SHA가 위 고정값인지 확인한다.
4. keep 경로가 사라졌다면 저장소의 `workspace/_keep/GO2_G_A074_REPORT_POLICY_RESULT.zip`을 임시 위치에 풀어 위 검사를 통과한 뒤에만 원래 keep 경로로 복원한다. 기존 keep을 덮어쓰지 않는다.
5. 이미 `evaluation/candidate/cases`에 69개 `summary.json`과 필수 영상이 모두 있으면 실행하지 않고 `SKIPPED_ALREADY_COMPLETE`로 기록한다.

## 2. 실행
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
cp "$REPO_ROOT/workspace/training/quadruped/upload/G-A074/recovery/current/GO2_G_A074_EVAL_RECOVERY_v1.zip" /workspace/
unzip -oq /workspace/GO2_G_A074_EVAL_RECOVERY_v1.zip -d /workspace
nohup bash /workspace/go2_g_a074_eval_recovery/run_eval_only.sh > /workspace/_keep/go2_g_a074_eval_recovery.console.log 2>&1 &
```

`run_eval_only.sh`가 패키지 manifest, G-A074 완료 artifact, report SHA, checkpoint pin을 먼저 검사한다. 기존 결과 ZIP은 timestamp가 붙은 `g_a074_pre_eval_archives/` 사본과 SHA로 보존한 뒤 기존 runner를 `GO2_RESUME=1`, `GO2_STAGE=full`, `--inner`로 호출한다.

## 3. 실패 처리
- rc 40: 완료된 G-A074 artifact의 누락 또는 SHA 불일치다. 재학습하지 않고 현재 keep, ZIP, 로그를 보존한다.
- evaluator 또는 USD asset 오류: 같은 checkpoint와 부분 결과를 보존하고 자동 재시작하지 않는다.
- 어떤 실패에서도 G-A075/G-A076 학습 패키지를 다시 실행하지 않는다.

## 4. 회수
- `/workspace/_keep/go2_g_a074_report_policy/`
- `/workspace/_keep/GO2_G_A074_REPORT_POLICY_RESULT.zip`와 `.sha256`
- `/workspace/_keep/g_a074_pre_eval_archives/`의 평가 전 원본 ZIP과 SHA
- 69-case telemetry, configured videos, `RUNNER_STATUS.txt`, `RESULT_STATUS.txt`, 평가 로그를 함께 회수한다.
- 100MB 초과 archive는 저장소 규칙에 따라 95MB parts로 나눈다.

## 5. 보고
PC2는 시작·종료 시각, rc, checkpoint SHA, telemetry 수, 영상 수, 결과 ZIP SHA만 ledger에 기록하고 commit/push한다. 성능 판독과 다음 보상 선택은 작성 PC가 한다.
