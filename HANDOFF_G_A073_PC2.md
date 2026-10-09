<!-- PC2_HANDOFF
WORK_ID: G-A073
STATUS: READY
START_AFTER: G-A072
START_MARKER: /workspace/_keep/go2_g_a072_pc2_points/BATCH_RUN.log 에 [BATCH END]
PACKAGE: workspace/training/quadruped/upload/G-A073/current/GO2_G_A073_REPORT_POLICY_v1.zip
PACKAGE_SHA256: 2a9aa2573a636084e46663526cf89db3780e891b4baf414978e14343fe147a1a
-->

# G-A073 PC2 인계 — report 정책 재학습 + 단일 안정성 변경

## 0. 한눈에
- **목적:** `report.html`에서 읽은 7개 보상값을 그대로 재현하고, `flat_orientation_l2`만 `-0.20 → -0.25`로 바꾼 정책을 재학습한다.
- **정책 기준:** `track_lin_vel_xy_exp=2.0`, `feet_air_time=0.01`, `lin_vel_z_l2=-3.0`, `ang_vel_xy_l2=-0.05`, `action_rate_l2=-0.005`, `track_ang_vel_z_exp=0.30`, `flat_orientation_l2=-0.20`.
- **단일 변경:** `flat_orientation_l2=-0.25`.
- **학습:** seed 42, 4096 env, 3000 iterations, from scratch; 평가 checkpoint iter 2400.
- **수집:** full 69-case telemetry, configured videos, 원 학습 `exported/report.html`, 결과 ZIP/SHA.
- **예상 시간:** 기존 1000 iter보다 길다. 고정 TTL을 가정하지 말고 GPU·로그를 감시한다.
- **판정:** PC2는 실행·회수만 한다. 채택/폐기와 원인 판독은 작성 PC가 한다.

## 1. 준비 확인
1. `git pull` 후 ZIP SHA를 확인한다.
   ```bash
   cd workspace/training/quadruped/upload/G-A073/current
   sha256sum -c GO2_G_A073_REPORT_POLICY_v1.zip.sha256
   ```
2. 선행 표식 확인: `/workspace/_keep/go2_g_a072_pc2_points/BATCH_RUN.log`에 `[BATCH END]`가 있어야 한다.
3. 다른 `train.py`/`play.py`가 실행 중이면 시작하지 않는다.
4. SHA 확인 후 `workspace/_keep/pc2_handoff_ledger.tsv`에 다음을 append하고 commit/push한다.
   ```text
   G-A073	STARTED	<ISO-8601>	report policy flat_orientation -0.25; seed42; 3000 iter
   ```

## 2. 실행
1. ZIP을 `/workspace/`로 복사한다.
2. 다음 한 줄로 실행한다.
   ```bash
   unzip -oq /workspace/GO2_G_A073_REPORT_POLICY_v1.zip -d /workspace && nohup bash /workspace/go2_g_a073_report_policy/run_all.sh > /workspace/_keep/go2_g_a073_pc2_console.log 2>&1 &
   ```
3. 진행 확인:
   ```bash
   tail -n 20 /workspace/_keep/go2_g_a073_report_policy/point.log
   nvidia-smi
   ```
4. 학습 중 reward 파일·runner·평가 코드를 수정하지 않는다.

## 3. 실패 처리
- 환경/패키지 오류(rc 20–25): 학습을 임의 재시작하지 말고 로그와 `RUNNER_STATUS.txt`를 회수한다.
- 학습 오류(rc 30–34): 실행 중 생성된 `training/interrupted_*`와 로그를 보존한다. 프로세스를 강제 종료하지 않는다.
- 디스크 부족: 남은 실행을 중지하려면 상태 폴더에 `STOP`을 만들고 이미 실행 중인 프로세스는 끄지 않는다.

## 4. 회수
- `/workspace/_keep/go2_g_a073_report_policy/` 전체
- `/workspace/_keep/GO2_G_A073_REPORT_POLICY_RESULT.zip` 및 `.sha256`
- `exported/report.html`이 이번 run의 report인지 확인되는 원본
- `training/model_best.pt`, `training/env.yaml`, checkpoint/policy identity, telemetry, 영상, 로그
- `workspace/_keep/pc2_handoff_ledger.tsv`에 `DONE` 또는 `FAILED<TAB>rc`를 append하고 commit/push한다.

## 5. 보고
실행 상태, rc, 시작/종료 시각, 회수 경로와 SHA만 보고한다. 성능 판독, 원인 해석, 다음 reward 값 선택은 하지 않는다.
