# G-A074 — G-A073 execution-only retry

- Parent: G-A073 (`flat_orientation_l2 -0.20 -> -0.25`, report-policy baseline, seed 42, 4096 env, 3000 iterations).
- G-A073 did not start child training: Windows `cp1252` raised `UnicodeEncodeError` while the supplied `train.py` printed Korean launcher text.
- G-A074 changes no reward, model, seed, environment count, iteration count, checkpoint, evaluator, or collection condition. It supplies `PYTHONIOENCODING=utf-8` only to the outer package runner so stdout encoding cannot abort before child training.
- The supplied training/evaluation files are not edited. The candidate remains a one-variable reward change from the recorded report policy.
- Required recovery: report.html, full 69-case telemetry, configured videos, result ZIP + SHA; performance readout is separate from PC2 execution.
