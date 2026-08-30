#!/usr/bin/env bash
# 서버 세션 복구 — 서버 재시작마다 1회 실행
# 사용: cd /workspace/training/humanoid && bash _bootstrap/restore.sh
set -u
ROOT=/workspace/training/humanoid
EXPECT_CKPT=2775a61e5294f37ec99a1454cdf200b2b0d9cd233022f68c6f293715690e9abc
cd "$ROOT" || { echo "[FAIL] $ROOT 없음"; exit 1; }
[ -d _bootstrap ] || { echo "[FAIL] _bootstrap 폴더가 없습니다 — zip 업로드/해제를 먼저 하세요"; exit 1; }
mkdir -p exported reports
cp -f _bootstrap/exported/model_best.pt exported/model_best.pt
cp -f _bootstrap/exported/env.yaml       exported/env.yaml
cp -f _bootstrap/humanoid_rewards.py     humanoid_rewards.py
FAIL=0
GOT=$(sha256sum exported/model_best.pt | cut -d" " -f1)
if [ "$GOT" = "$EXPECT_CKPT" ]; then
  echo "[OK]   model_best.pt = Run 05"
else
  echo "[FAIL] model_best.pt 해시 불일치"; echo "       기대 $EXPECT_CKPT"; echo "       실제 $GOT"; FAIL=1
fi
check() {
  V=$(sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\(-\{0,1\}[0-9.]\{1,\}\).*/\1/p" humanoid_rewards.py | head -1)
  if [ "$V" = "$2" ]; then echo "[OK]   $1 = $V"; else echo "[FAIL] $1 = ${V:-없음} (기대 $2)"; FAIL=1; fi
}
check track_lin_vel_xy_exp 1.0
check track_ang_vel_z_exp 1.0
check feet_air_time 0.2
check termination_penalty -50.0
check flat_orientation_l2 -1.5
check ang_vel_xy_l2 -0.05
check joint_deviation_hip -0.2
check joint_deviation_torso -0.1
check action_rate_l2 -0.0005
echo "----------------------------------------"
if [ "$FAIL" = "0" ]; then
  echo "[DONE] 복구 완료 — Run 05 상태. play 실행 가능."
else
  echo "[BLOCKED] 복구 실패 — FAIL 항목 해결 전에는 실행하지 마세요."; exit 1
fi
