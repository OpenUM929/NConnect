RUN06 INDEPENDENT MULTI-SEED EVALUATION
=======================================

Purpose
-------
Challenge the high calibration score without changing or retraining Run06.
The frozen model_9900 policy is evaluated on predeclared unseen seeds
101, 202 and 303 across all ten H1-H7 cases.  Every seed must pass and the
worst seed per scenario is used.  This is still an internal proxy, not an
official competition score.

Expected server time
--------------------
Approximately 15-25 minutes.  No training is performed.

Run
---
1. Upload run06_independent_eval_package.zip to /workspace/training/humanoid
2. Run exactly:

   cd /workspace/training/humanoid && unzip -o run06_independent_eval_package.zip && sed -i 's/\r$//' server_run06_independent_eval.sh && bash server_run06_independent_eval.sh

Monitor
-------
tmux attach -t run06_independent_eval

Download only after [DONE]
--------------------------
/workspace/_keep/train_260831-06_run05cfg_10000_INDEPENDENT_EVAL_FULL.tar.gz
/workspace/_keep/train_260831-06_run05cfg_10000_INDEPENDENT_EVAL_FULL.tar.gz.sha256

Do not accept PARTIAL as complete.  Keep the server on until both FULL files
are downloaded and verified locally.
