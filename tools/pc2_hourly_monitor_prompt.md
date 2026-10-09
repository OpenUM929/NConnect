# NConnect PC2 hourly HANDOFF monitor

Run one PC2 monitoring cycle. Do not ask questions or wait for approval.

1. Run `git pull --ff-only` in `C:\dev\NConnect`.
2. Read the root `AGENTS.md` PC2 handoff contract, every `HANDOFF_*_PC2.md`
   header, `workspace/_keep/pc2_handoff_ledger.tsv`, and
   `workspace/_keep/author_pc_ledger.tsv`.
3. Check active `train.py`/`play.py` processes and every active batch log. If
   training is active, do not start another training run.
4. Recover each completed point exactly as its HANDOFF section 4 requires.
   Verify SHA, `FULL_69_COMPLETE`, the run's `report.html`, and required
   videos before calling recovery complete. Split archives over 100 MB into
   95 MB parts; never commit the original ZIP. Commit and push recovered
   artifacts immediately.
5. When a batch ends, append `DONE` or `FAILED<TAB>rc` to the PC2 ledger,
   commit and push, then immediately run another HANDOFF scan.
6. If no training is active, select the lowest-numbered HANDOFF with a
   `PC2_HANDOFF` header, `STATUS: READY`, a satisfied start marker, and no
   PC2 ledger row. Verify its package SHA and R-6 compliance, append and
   push its `STARTED` ledger row, then run the HANDOFF's existing command.
7. Do not select reward values, analyze performance, alter deployment source,
   or create a new training runner. PC2 only uses the supplied package,
   builder, and runner.
8. Windows Task Scheduler invokes this monitor every 30 minutes. Publish
   observed completed-case counts and video/recovery status; do not estimate
   percentages from elapsed time. Do not overlap active evaluation processes.

9. Durable user instruction (2026-10-09): after G-A074-EVAL recovery is
   verified and committed/pushed, do not end at recovery or wait for another
   user instruction. Explicitly leave the execution-only PC2 lane and take
   the author lane for this bounded follow-up. This is the user-authorized
   exception to step 7's reward-selection restriction, not permission for
   the execution lane to pick arbitrary values. Read GO2_NOW.md,
   GO2_TUNING_ANALYSIS_BRIEF.md, applicable quadruped AGENTS.md,
   GO2_REWARD_EVIDENCE_MASTER.md dial history, and its required base-data,
   lecture, mechanism-forecast, and reward-trial references before selecting.
   Read the matched original training report and evaluate recovered G1-G7
   telemetry/videos. Separate observed facts, failure-path hypotheses,
   lecture-based predictions, and prior counterexamples. Reuse the recorded
   stairs failure analysis; do not repeat completed diagnostics/training.
   Update canonical evidence/state records and commit/push the readout.
   Then choose the next justified single-variable experiment, reserve the
   next unused ID, and use existing builders/runners to publish its numbered
   execution package under upload/<ID>/current/. Verify single-variable diff,
   LF, bash syntax, archive CRC/SHA, report recovery and server shutdown gates.
   Publish its execution line, result path, and standard READY PC2 handoff;
   commit/push and verify the remote commit. Never publish review-only files
   as a substitute. Follow existing budget/execution authority; do not start
   a new server session or alter deployment code to force completion.
   Stop this follow-up only once the next valid tuning package/handoff is
   published, or report a concrete blocking validation/regulation/budget/
   access/destructive-operation issue. No routine reapproval question.
   Use the author ledger to record follow-up progress and prevent duplicate
   selection/publication on later cycles. If a validated next package already
   exists, continue its existing handoff instead of creating another one.

Current priority: inspect the current ledger and every active batch; H-A001 may be active. Its Windows `C:\workspace` and Git Bash `/workspace` paths are the same junction. Do not claim a status without observed evidence.
