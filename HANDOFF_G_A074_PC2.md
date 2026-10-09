<!-- PC2_HANDOFF
WORK_ID: G-A074
STATUS: READY
START_AFTER: G-A072
START_MARKER: /workspace/_keep/go2_g_a072_pc2_points/BATCH_RUN.log contains [BATCH END]
PACKAGE: workspace/training/quadruped/upload/G-A074/current/GO2_G_A074_REPORT_POLICY_v1.zip
PACKAGE_SHA256: cd6bb2d039de823a4efb79281b24ccde400b569e0d0f63d2c171a0ef9f84c19d
-->

# G-A074 PC2 handoff — G-A073 execution-only retry

## 0. Summary
- Purpose: execute the same single reward change as G-A073: report-policy flat_orientation_l2 -0.20 -> -0.25.
- G-A073 failed before child training because Windows cp1252 could not print Korean launcher text.
- G-A074 changes only the package launch environment: PYTHONIOENCODING=utf-8; reward values, seed 42, 4096 envs, 3000 iterations, checkpoint 2400, evaluator, and collection all remain fixed.
- Required collection: source-training exported/report.html, model/env identity, full 69-case telemetry, configured videos, result ZIP and SHA.

## 1. Preparation
1. Verify ZIP SHA and G-A072 [BATCH END] marker.
2. Do not start if any train.py or play.py process is active.
3. Append and push before launch:
   G-A074<TAB>STARTED<TAB><ISO-8601><TAB>G-A073 execution-only retry; flat_orientation -0.25; UTF-8 launcher environment; seed42; 3000 iter

## 2. Run
`ash
unzip -oq /workspace/GO2_G_A074_REPORT_POLICY_v1.zip -d /workspace && nohup bash /workspace/go2_g_a074_report_policy/run_all.sh > /workspace/_keep/go2_g_a074_pc2_console.log 2>&1 &
`
Monitor /workspace/_keep/go2_g_a074_report_policy/point.log and GPU state. Do not edit reward, runner, training, or evaluation files once started.

## 3. Failure
For rc 20-25 or 30-34, do not restart this package. Preserve logs, RUNNER_STATUS.txt, and any interrupted training artifacts; append FAILED with rc, commit, and push.

## 4. Recovery
Recover /workspace/_keep/go2_g_a074_report_policy/, /workspace/_keep/GO2_G_A074_REPORT_POLICY_RESULT.zip and sidecar, console log, report.html, model/env/checkpoint identity, telemetry, and videos. Verify SHA. Split archives over 100 MB into 95 MB parts. Append DONE or FAILED and commit/push immediately.

## 5. Reporting
Report only execution status, rc, timestamps, recovery path, and SHA. Performance readout and the next reward decision remain with the author PC.
