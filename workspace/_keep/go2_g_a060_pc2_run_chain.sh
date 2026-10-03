#!/usr/bin/env bash
set -uo pipefail
mount -o binary,noacl,posix=0,user C:/workspace /workspace 2>&1
export ISAACLAB_SH=/workspace/bin/isaaclab.sh
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONUNBUFFERED=1
export PATH="/c/workspace/bin/pyshim:$PATH"
R=/workspace/go2_g_a060_pc2/run_point.sh
run_point() {
  local key=$1
  echo "[POINT CALL] $key $(date -Is)"
  # A full point takes hours. Never use log silence or a 10-minute wall limit
  # to kill it. The frozen runner verifies full collection before returning 0.
  bash "$R" --inner "$key"
  local rc=$?
  echo "[POINT RETURN] $key rc=$rc $(date -Is)"
  return "$rc"
}

echo "[CHAIN START] $(date -Is)"
run_point a048_seed42
rc1=$?
echo "[a048_seed42 exit] $rc1"
if [ "$rc1" -eq 0 ]; then
  run_point ang_vel_xy_l2_m0p08
  rc2=$?
  echo "[ang_vel_xy_l2_m0p08 exit] $rc2"
  # HANDOFF_G_A060_PC2.md: point 3 runs even if point 2 failed.
  run_point track_lin_vel_xy_exp_p1p4
  rc3=$?
  echo "[track_lin_vel_xy_exp_p1p4 exit] $rc3"
else
  echo "[SKIP] B1(a048_seed42) failed rc=$rc1 — per HANDOFF_G_A060_PC2.md this blocks points 2 and 3"
fi
echo "[CHAIN END] $(date -Is)"
if [ "$rc1" -ne 0 ]; then exit "$rc1"; fi
if [ "$rc2" -ne 0 ]; then exit "$rc2"; fi
exit "$rc3"
