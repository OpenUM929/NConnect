<!-- PC2_HANDOFF
WORK_ID: G-A076
STATUS: CANCELLED
START_AFTER: G-A075
START_MARKER: /workspace/_keep/go2_g_a075_report_policy/RUNNER_STATUS.txt exists and G-A075 has a terminal DONE or FAILED ledger row
PACKAGE: workspace/training/quadruped/upload/G-A076/current/GO2_G_A076_REPORT_POLICY_v1.zip
PACKAGE_SHA256: 0aec4d943e51bffab313673abec0980cbcd03507d45da287968d664c1c29f2c0
-->

# G-A076 PC2 execution retry

## 2026-10-09 사용자 정정 — 재학습 발행 취소
G-A074의 3,000 iteration 학습은 TRAIN_RC=0으로 완료됐으므로 이 문서의 재학습 명령을 새로 실행하거나 재시작하지 않는다. 이미 실행 중인 G-A076은 상태·로그·artifact를 보존하고 현재 종료 상태를 보고한다. 원격 시작 기록만으로 현재 학습 진행을 확정하지 않는다. 다음 작업은 HANDOFF_G_A074_EVAL_PC2.md에 따른 기존 G-A074 checkpoint 평가 재개다. 실행 중 프로세스 강제 종료는 이 문서에서 지시하지 않는다.

## 0. 한눈에
- 목적: G-A075와 같은 report-policy 단일변수 실험을 Isaac Lab 인터프리터 우선 선택으로 재실행한다.
- 단일 변경: `flat_orientation_l2 -0.20 -> -0.25`; reward, seed 42, 4096 env, 3000 iterations, checkpoint 2400, evaluator와 69-case 수집 조건은 그대로다.
- 시작 조건: G-A075가 `RUNNER_RC=0`과 `FULL_69_COMPLETE`로 끝나면 G-A076을 실행하지 않고 중복 회차로 종료한다. G-A075가 Python 환경 선택 문제로 실패하고 학습·평가가 완결되지 않았을 때만 실행한다.
- 수집: 원 학습 `exported/report.html`, model/env/checkpoint identity, full 69-case telemetry, configured videos, 결과 ZIP/SHA.
- 판정: PC2는 실행·회수만 한다. 성능 판독과 채택/폐기는 작성 PC가 한다.

## 1. 준비 확인
1. `git pull` 후 ZIP SHA를 확인한다.
   ```bash
   cd workspace/training/quadruped/upload/G-A076/current
   sha256sum -c GO2_G_A076_REPORT_POLICY_v1.zip.sha256
   ```
2. G-A075의 `RUNNER_STATUS.txt`와 PC2 ledger를 확인한다. G-A075가 완결됐으면 G-A076은 `SKIPPED_DUPLICATE`로 기록하고 실행하지 않는다.
3. G-A075가 미완결 실패했으며 다른 `train.py`/`play.py`가 실행 중이지 않을 때만 시작한다.
4. 시작 전에 `workspace/_keep/pc2_handoff_ledger.tsv`에 다음을 append하고 commit/push한다.
   ```text
   G-A076	STARTED	<ISO-8601>	G-A075 interpreter retry; flat_orientation -0.25; Isaac Lab python preferred; seed42; 3000 iter
   ```

## 2. 실행
```bash
unzip -oq /workspace/GO2_G_A076_REPORT_POLICY_v1.zip -d /workspace && nohup bash /workspace/go2_g_a076_report_policy/run_all.sh > /workspace/_keep/go2_g_a076_pc2_console.log 2>&1 &
```

진행 중 `/workspace/_keep/go2_g_a076_report_policy/point.log`와 GPU 상태를 확인한다. 시작 뒤 reward·runner·학습·평가 파일은 수정하지 않는다.

## 3. 실패 처리
- rc 20–25 또는 30–34이면 같은 패키지를 자동 재시작하지 않는다.
- 로그, `RUNNER_STATUS.txt`, interrupted training artifact와 부분 결과 ZIP/SHA를 보존한다.
- 상태와 rc를 ledger에 `FAILED`로 기록하고 즉시 commit/push한다.

## 4. 회수
- `/workspace/_keep/go2_g_a076_report_policy/` 전체
- `/workspace/_keep/GO2_G_A076_REPORT_POLICY_RESULT.zip` 및 `.sha256`
- 이번 run의 `exported/report.html`, model/env/checkpoint identity, telemetry, 영상과 로그
- 100MB 초과 archive는 95MB parts로 나누고 원본 SHA를 유지한다.
- SHA 확인 뒤 ledger에 `DONE` 또는 `FAILED<TAB>rc`를 기록하고 commit/push한다.

## 5. 보고
실행/건너뜀 상태, rc, 시작·종료 시각, 회수 경로와 SHA만 보고한다. 성능과 다음 reward 값은 판독하지 않는다.
