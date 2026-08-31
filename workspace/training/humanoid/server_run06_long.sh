#!/usr/bin/env bash
# Run 06: Run 05 reward configuration 그대로 장기 수렴 확인.
# 외부 실행: MAX_ITERS=10000 bash server_run06_long.sh
# 완료 bundle: /workspace/_keep/<RUN_ID>_DOWNLOAD.tar.gz
set -euo pipefail

ROOT=/workspace/training/humanoid
MAX_ITERS=${MAX_ITERS:-10000}
RUN_ID=${RUN_ID:-train_260831-06_run05cfg_${MAX_ITERS}}
TMUX_NAME=${TMUX_NAME:-run06_${MAX_ITERS}}
KEEP=/workspace/_keep/${RUN_ID}
MARKER=${KEEP}/session_start.marker

if [[ "${1:-}" == "--inner" ]]; then
  mkdir -p "$KEEP/ckpt" "$KEEP/final" "$KEEP/run"
  touch "$MARKER"

  find_run_dir() {
    [[ -d "$ROOT/logs/rsl_rl/humanoid" ]] || return 0
    find "$ROOT/logs/rsl_rl/humanoid" -mindepth 1 -maxdepth 1 -type d \
      -newer "$MARKER" -print 2>/dev/null | sort | tail -n 1
  }

  copy_milestone() {
    local run_dir=$1 target=$2 threshold=$3 marker="$KEEP/ckpt/.saved_${target}"
    [[ -e "$marker" ]] && return 0
    local newest iter
    newest=$(find "$run_dir" -maxdepth 1 -type f -name 'model_[0-9]*.pt' -printf '%f\n' \
      | sort -t_ -k2,2n | tail -n 1 || true)
    [[ -n "$newest" ]] || return 0
    iter=${newest#model_}; iter=${iter%.pt}
    if (( iter >= threshold )); then
      cp -f "$run_dir/$newest" "$KEEP/ckpt/${target}_${newest}"
      printf '%s\t%s\n' "$target" "$newest" >>"$KEEP/ckpt/milestones.tsv"
      touch "$marker"
    fi
  }

  watcher() {
    while :; do
      local run_dir
      run_dir=$(find_run_dir)
      if [[ -n "$run_dir" ]]; then
        printf '%s\n' "$run_dir" >"$KEEP/run_dir.txt"
        copy_milestone "$run_dir" 3000 2900
        copy_milestone "$run_dir" 5000 4900
        copy_milestone "$run_dir" 10000 9900
        copy_milestone "$run_dir" 15000 14900
      fi
      sleep 2
    done
  }

  watcher &
  WATCH_PID=$!
  trap 'kill "$WATCH_PID" 2>/dev/null || true' EXIT

  set +e
  NO_AUTO_SUBMIT=1 /workspace/IsaacLab/isaaclab.sh -p train.py \
    --task Humanoid-v0 --num_envs 4096 --max_iterations "$MAX_ITERS" --headless \
    2>&1 | tee "$KEEP/train.log"
  TRAIN_RC=${PIPESTATUS[0]}
  set -e

  kill "$WATCH_PID" 2>/dev/null || true
  wait "$WATCH_PID" 2>/dev/null || true
  trap - EXIT

  RUN_DIR=$(cat "$KEEP/run_dir.txt" 2>/dev/null || true)
  [[ -n "$RUN_DIR" ]] || RUN_DIR=$(find_run_dir)
  [[ -z "$RUN_DIR" || ! -d "$RUN_DIR" ]] || cp -a "$RUN_DIR"/. "$KEEP/run"/
  [[ ! -f "$ROOT/reports/experiment_history.csv" ]] || \
    cp -a "$ROOT/reports/experiment_history.csv" "$KEEP/"
  # train.py는 policy.pt를 갱신하지 않는다. 이전 run의 stale policy 혼입을 막기 위해 제외한다.
  for f in model_best.pt env.yaml report.html; do
    [[ -f "$ROOT/exported/$f" ]] && cp -a "$ROOT/exported/$f" "$KEEP/final/"
  done

  {
    echo "RUN_ID=$RUN_ID"
    echo "MAX_ITERS=$MAX_ITERS"
    echo "TRAIN_RC=$TRAIN_RC"
    echo "RUN_DIR=${RUN_DIR:-NOT_FOUND}"
    date -Is
  } | tee "$KEEP/STATUS.txt"
  find "$KEEP" -type f ! -name SHA256SUMS.txt -print0 \
    | sort -z | xargs -0 sha256sum >"$KEEP/SHA256SUMS.txt"
  tar -C /workspace/_keep -czf "/workspace/_keep/${RUN_ID}_DOWNLOAD.tar.gz" "$RUN_ID"
  sha256sum "/workspace/_keep/${RUN_ID}_DOWNLOAD.tar.gz" | tee "$KEEP/DOWNLOAD_SHA256.txt"
  echo "[DONE] DOWNLOAD=/workspace/_keep/${RUN_ID}_DOWNLOAD.tar.gz"
  exit "$TRAIN_RC"
fi

cd "$ROOT"
[[ "$MAX_ITERS" == "10000" || "$MAX_ITERS" == "15000" ]] || {
  echo "[FAIL] MAX_ITERS는 10000 또는 15000만 허용합니다."; exit 2;
}
[[ -f _bootstrap/restore.sh ]] || {
  echo "[FAIL] 패키지를 현재 폴더에 먼저 압축 해제하세요."; exit 2;
}
command -v tmux >/dev/null 2>&1 || { echo "[FAIL] tmux 없음"; exit 2; }
pgrep -af 'train.py|isaaclab.sh' && { echo "[BLOCKED] 기존 학습 프로세스가 있습니다."; exit 2; } || true
tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
  echo "[BLOCKED] tmux $TMUX_NAME 이미 존재"; exit 2;
}

mkdir -p "$KEEP/pre_restore"
for f in humanoid_rewards.py exported/model_best.pt exported/env.yaml exported/policy.pt; do
  [[ -f "$f" ]] && cp -a "$f" "$KEEP/pre_restore/"
done
find "$KEEP/pre_restore" -type f -maxdepth 1 -print0 2>/dev/null \
  | sort -z | xargs -0 -r sha256sum >"$KEEP/pre_restore/SHA256SUMS.txt"

bash _bootstrap/restore.sh | tee "$KEEP/restore.log"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader \
  | tee "$KEEP/gpu.csv"
sha256sum train.py play.py humanoid_rewards.py h1_task/*.py _bootstrap/restore.sh \
  reports/experiment_history.csv \
  >"$KEEP/source_before.sha256"

tmux new-session -d -s "$TMUX_NAME" \
  "cd '$ROOT' && MAX_ITERS='$MAX_ITERS' RUN_ID='$RUN_ID' TMUX_NAME='$TMUX_NAME' bash server_run06_long.sh --inner 2>&1 | tee '$KEEP/launcher.log'"

echo "[STARTED] $RUN_ID"
echo "[PURPOSE] 서기 재튜닝이 아니라 Run 05 보상 고정 상태의 장기 수렴 확인"
echo "[MONITOR] tmux attach -t $TMUX_NAME"
echo "[STATUS]  tail -n 40 $KEEP/train.log"
echo "[RESULT]  /workspace/_keep/${RUN_ID}_DOWNLOAD.tar.gz"
