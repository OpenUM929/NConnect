#!/bin/bash
# Go2 1000iter 가벼운 pilot — 서버 결과 패키징 러너
# 업로드 후: bash server_pack_Go2_1000.sh
# 결과: /workspace/_keep/<RUN_ID>_DOWNLOAD.tar.gz + .sha256 + STATUS.txt
set -e

RUN_ID="train_260831-Go2_5var_1000"
KEEP="/workspace/_keep/${RUN_ID}"
SRC="/workspace/training/quadruped"

echo "=== PACK Go2 1000 ==="
echo "RUN_ID=${RUN_ID}"
echo "KEEP=${KEEP}"
mkdir -p "${KEEP}"

# 1. 최신 run 폴더 탐색 (logs/rsl_rl/quadruped/<run>)
LATEST_RUN=$(ls -t "${SRC}/logs/rsl_rl/quadruped" 2>/dev/null | head -n1 || true)
echo "LATEST_RUN=${LATEST_RUN}"

# 2. STATUS 기록
{
  echo "RUN_ID=${RUN_ID}"
  echo "PACK_TIME=$(date -Is)"
  echo "LATEST_RUN=${LATEST_RUN}"
  echo "REWARD_WEIGHTS:"
  grep -E "track_lin|feet_air|lin_vel_z|ang_vel_xy|action_rate" "${SRC}/quadruped_rewards.py" || true
  echo "--- exported ---"
  ls -lh "${SRC}/exported/" 2>&1 || true
  echo "--- logs ---"
  ls -lh "${SRC}/logs/rsl_rl/quadruped/${LATEST_RUN}/" 2>&1 | head -n 30 || true
} | tee "${KEEP}/STATUS.txt"

# 3. tar 생성 — 필수 bundle만 (보험 snapshot과 분리)
#    exported + 해당 run의 logs/params + rewards.py
TARBALL="${KEEP}/${RUN_ID}_DOWNLOAD.tar.gz"
echo "Creating ${TARBALL} ..."

# tar에 넣을 파일 목록 확인
tar -czf "${TARBALL}" \
  -C /workspace/training \
  quadruped/quadruped_rewards.py \
  quadruped/exported \
  quadruped/go2_task \
  2>&1 | tee -a "${KEEP}/STATUS.txt" || true

# 최신 run이 있으면 추가
if [ -n "${LATEST_RUN}" ] && [ -d "${SRC}/logs/rsl_rl/quadruped/${LATEST_RUN}" ]; then
  echo "Appending logs for ${LATEST_RUN} ..."
  tar -rf "${TARBALL%.gz}" -C /workspace/training "quadruped/logs/rsl_rl/quadruped/${LATEST_RUN}" 2>&1 | tee -a "${KEEP}/STATUS.txt" || true
  # rf는 비압축 tar에 append, 다시 gzip
  gzip -f "${TARBALL%.gz}" 2>&1 | tee -a "${KEEP}/STATUS.txt" || true
fi

# 4. SHA256
sha256sum "${TARBALL}" | tee "${KEEP}/DOWNLOAD_SHA256.txt" | tee -a "${KEEP}/STATUS.txt"
ls -lh "${TARBALL}" | tee -a "${KEEP}/STATUS.txt"

echo ""
echo "[DONE] DOWNLOAD=${TARBALL}"
echo "[DONE] SHA256=$(cat ${KEEP}/DOWNLOAD_SHA256.txt)"
echo "다운로드할 파일 2개:"
echo "  ${TARBALL}"
echo "  ${KEEP}/DOWNLOAD_SHA256.txt"
echo "로컬 저장 위치: workspace/server_returns/${RUN_ID}/original/"
