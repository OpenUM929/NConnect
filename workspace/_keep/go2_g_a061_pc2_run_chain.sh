#!/usr/bin/env bash
set -uo pipefail
mount -o binary,noacl,posix=0,user C:/workspace /workspace 2>&1
export ISAACLAB_SH=/workspace/bin/isaaclab.sh
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONUNBUFFERED=1
export PATH="/c/workspace/bin/pyshim:$PATH"

echo "[CHAIN START] $(date -Is)"
unzip -oq /workspace/GO2_G_A061_PC2_TREE_n3_dof_torques_l2_m1e_4_v1.zip -d /workspace
bash /workspace/go2_g_a061_pc2/run_point.sh --inner n3_dof_torques_l2_m1e_4
rc=$?
echo "[n3_dof_torques_l2_m1e_4 exit] $rc $(date -Is)"
echo "[CHAIN END] $(date -Is)"
exit "$rc"
