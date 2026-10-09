# G-A076 — G-A075 conditional execution retry

- Parent: G-A075 (`flat_orientation_l2 -0.20 -> -0.25`, report-policy baseline, seed 42, 4096 env, 3000 iterations).
- G-A075 is running as of 2026-10-09 20:48 KST. G-A076 must not duplicate it when G-A075 reaches `RUNNER_RC=0` and `FULL_69_COMPLETE`.
- If G-A075 fails because the host `python3` is selected instead of Isaac Lab's interpreter, G-A076 retries with `$ISAACLAB_SH -p` preferred. Reward values, training/evaluation settings and collection scope are unchanged.
- Package text payloads are normalized to LF. This is packaging hygiene, not a scientific variable.
- Decision: a complete G-A075 makes G-A076 `SKIPPED_DUPLICATE`; an incomplete interpreter-selection failure permits one G-A076 run; any other failure returns to author-PC diagnosis without automatic retry.
- Evidence required before any performance claim: matching report/model/env/checkpoint identity, full 69-case telemetry, configured videos, result ZIP and SHA.
