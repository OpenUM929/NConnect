RUN06 FIXED EVALUATION PACKAGE
==============================

Purpose
-------
Measure the already-trained Run06 model_9900 policy across all H1-H7 cases.
This package does NOT train and does NOT change reward weights.  It produces
an internal seven-scenario scorecard (simulation proxy /70); it is not an
official competition score.

Run on the temporary server
---------------------------
1. Upload run06_fixed_eval_package.zip into /workspace/training/humanoid
2. cd /workspace/training/humanoid && unzip -o run06_fixed_eval_package.zip
3. Run exactly one command:

   cd /workspace/training/humanoid && sed -i 's/\r$//' server_run06_fixed_eval.sh && bash server_run06_fixed_eval.sh

Monitor only if needed
----------------------
tmux attach -t run06_fixed_eval

Download after [DONE]
---------------------
/workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz
/workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz.sha256

The FULL archive contains raw per-environment CSV telemetry, command logs,
summaries, source hashes, model/env evidence, and a compact report.  A partial
or missing H1-H7 case is SELF_ASSESSMENT_INCOMPLETE and contributes no PASS.
