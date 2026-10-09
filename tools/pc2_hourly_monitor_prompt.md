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
8. End after this cycle; Windows Task Scheduler invokes the next cycle hourly.

Current priority: G-A072. Its Windows `C:\workspace` and Git Bash
`/workspace` paths are the same junction. Do not claim a status without
observed evidence.
