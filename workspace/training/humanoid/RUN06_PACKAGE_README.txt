Run 06 server package
=====================

Purpose
- H1 standing tuning is already complete.
- This run keeps all Run 05 reward weights unchanged and tests long-run convergence.

Server
1) Upload run06_server_package.zip to /workspace/training/humanoid/
2) unzip -o run06_server_package.zip
3) MAX_ITERS=10000 bash server_run06_long.sh
   Use 15000 only when at least 3h20m of server time remains.

Download after completion
- /workspace/_keep/train_260831-06_run05cfg_<iter>_DOWNLOAD.tar.gz

Do not submit policy.pt from this run yet.
train.py does not regenerate policy.pt; the final selected checkpoint is exported and evaluated later.
