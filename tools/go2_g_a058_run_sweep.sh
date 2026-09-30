#!/usr/bin/env bash
# G-A058 reward-unchanged replicate launcher, derived from tools/go2_g_a057_run_sweep.sh by renaming only
# (source: tools/go2_g_a058_run_sweep.sh; packaged as go2_g_a058/run_sweep.sh).
#
# One command runs every remaining arm of the sweep, one after another.  Each arm is the
# audited G-A055 runner (server_run_go2_candidate_iter_pinned.sh, bytes unchanged) started
# in --inner mode on its own materialised package root, so training, the iter-900 pin, the
# 69-case suite, the G-A033 sentinel, the videos and the one-file result ZIP are exactly the
# per-arm contract used on the competition server.  This file only sequences arms.
#
#   bash run_sweep.sh            print the plan + estimate, preflight, start inside tmux
#   bash run_sweep.sh --list     print the plan and exit
#   bash run_sweep.sh --inner    the sequential loop itself (what tmux runs)
#
# Re-running the same command resumes: an arm whose result is verified complete is skipped,
# an arm with a partial result continues with GO2_RESUME=1, and nothing already written is
# deleted or overwritten by this launcher.
#
# Exit codes of --inner: 0 loop finished (individual arm failures are recorded, not fatal)
#   20 free disk below GO2_SWEEP_MIN_FREE_GB     21 another train/play process is running
#   22 Isaac Lab / GPU missing                   23 an arm failed before training started (common environment)
#   24 two consecutive arms failed in training   25 sweep package checksum mismatch
#
# Status words in SWEEP_STATUS.tsv keep three things apart (Codex work order 3, 2026-09-29):
#   run safety stop     ABORT_* (whole sweep, exit codes above) and SAFETY_STOP_NONFINITE (one arm: training
#                       loss went non-finite, the runner refuses to evaluate a policy that is not executable)
#   execution failure   RUN_ERROR (runner rc != 0), COLLECTION_FAILED (rc 0 but the 69-case harvest is not
#                       complete), RUN_ERROR_MATERIALIZE, BLOCKED_EXISTING_RESULT
#   complete            DONE / SKIP_DONE — the harvest is FULL_69_COMPLETE, whatever the policy did
# Neither this launcher nor the runner stops, skips or reruns an arm because its evaluation looks bad.  A
# stationary policy is still measured on all 69 cases (COLLECT_REQUIRED_ON_STATIONARY=1).  Excluding a
# candidate after evaluation is the readout's job (upload/plan/GO2_OTHER_PC_SEQUENCE_PROPOSAL_20260930.md §3), not a run state.
set -euo pipefail

SWEEP_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SELF="$SWEEP_ROOT/$(basename "${BASH_SOURCE[0]}")"
RUNNER_NAME=server_run_go2_candidate_iter_pinned.sh
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
WORK_BASE=${GO2_SWEEP_WORK:-/workspace/go2_g_a058_work}
MIN_FREE_GB=${GO2_SWEEP_MIN_FREE_GB:-20}
TMUX_NAME=go2_g_a058
TEST_MODE=${GO2_SWEEP_TEST_MODE:-0}
# The per-arm runner always writes /workspace/_keep.  KEEP_BASE may differ only in the
# GPU-free contract test, whose fake runner honours GO2_SWEEP_KEEP_BASE.
if [[ "$TEST_MODE" == 1 ]]; then
  KEEP_BASE=${GO2_SWEEP_KEEP_BASE:?test mode needs GO2_SWEEP_KEEP_BASE}
  RUNNER_OVERRIDE=${GO2_SWEEP_TEST_RUNNER:?test mode needs GO2_SWEEP_TEST_RUNNER}
else
  KEEP_BASE=/workspace/_keep
  RUNNER_OVERRIDE=
fi
STATUS_DIR="$KEEP_BASE/go2_g_a058_sweep"
STATUS_TSV="$STATUS_DIR/SWEEP_STATUS.tsv"
ORDER="$SWEEP_ROOT/sweep_order.txt"
# Measured on the competition server (RTX 5080 16 GB): one full69 arm = 94 min, training 58 min
# (G-A044).  Another GPU is slower or faster; this is a planning figure, not a cap.
ARM_MINUTES=95

log_status() {  # key status rc collection resume started ended note
  mkdir -p "$STATUS_DIR"
  [[ -s "$STATUS_TSV" ]] || printf 'key\tstatus\trc\tcollection\tresume\tstarted\tended\tnote\n' >"$STATUS_TSV"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >>"$STATUS_TSV"
  echo "[SWEEP] $1 $2 rc=$3 collection=$4 resume=$5 $8"
}

verified_done() {  # keep result_zip
  local keep=$1 zip=$2
  [[ -s "$keep/RESULT_STATUS.txt" && -s "$zip" && -s "$zip.sha256" ]] || return 1
  grep -qx 'RESULT_STATE=FULL' "$keep/RESULT_STATUS.txt" || return 1
  grep -qx 'COLLECTION_STATUS=FULL_69_COMPLETE' "$keep/RESULT_STATUS.txt" || return 1
  [[ "$(awk '{print $1}' "$zip.sha256")" == "$(sha256sum "$zip" | awk '{print $1}')" ]]
}

runner_decision() {  # keep
  # A failed arm may not have written the file; never let a missing file end the sweep (set -e + pipefail).
  { sed -n 's/^DECISION=//p' "$1/RUNNER_STATUS.txt" 2>/dev/null || true; } | tail -1
}

safety_stopped() {  # keep result_zip — a finished non-finite-training stop, packaged and checksummed
  local keep=$1 zip=$2
  [[ "$(runner_decision "$keep")" == CATASTROPHE_TRAINING_NONFINITE && -s "$zip" && -s "$zip.sha256" ]] || return 1
  [[ "$(awk '{print $1}' "$zip.sha256")" == "$(sha256sum "$zip" | awk '{print $1}')" ]]
}

free_gb() {
  if [[ -n "${GO2_SWEEP_TEST_FREE_GB:-}" && "$TEST_MODE" == 1 ]]; then echo "$GO2_SWEEP_TEST_FREE_GB"; return; fi
  mkdir -p "$KEEP_BASE"
  df -Pk "$KEEP_BASE" | awk 'NR==2 {print int($4/1048576)}'
}

print_plan() {
  local n_new=0 key keep zip
  echo "=== G-A058 보상 무변경 재학습(A048 seed 42, A043 seed 43·44) — 실행 목록 ==="
  echo "보상은 바꾸지 않는다. A048 보상 seed 42, A043 보상 seed 43·44 · 4096 env · 1000 iter · 평가 checkpoint 900 · 69 case."
  echo "보상 무변경 재학습 세 행이다. 목적과 판독 기준은 SWEEP_PLAN.md."
  while read -r key keep zip; do
    [[ -n "$key" ]] || continue
    n_new=$((n_new + 1))
    local change
    change=$(grep -E '^SINGLE_CHANGE_(NAME|FROM|TO)=' "$SWEEP_ROOT/runs/$key/run_config.env" | cut -d= -f2 | paste -sd' ')
    if verified_done "$KEEP_BASE/$keep" "$KEEP_BASE/$zip" 2>/dev/null; then
      printf '  %-34s %-40s [완료·검증됨 — 건너뜀]\n' "$key" "$change"
    elif [[ -d "$KEEP_BASE/$keep" ]]; then
      printf '  %-34s %-40s [부분 결과 — GO2_RESUME=1 로 이어서]\n' "$key" "$change"
    else
      printf '  %-34s %-40s [새로 실행]\n' "$key" "$change"
    fi
  done <"$ORDER"
  echo "새 학습 실행 ${n_new}개. 예상: 서버 RTX 5080 기준 한 실행 약 ${ARM_MINUTES}분 → 약 $(( n_new * ARM_MINUTES / 60 ))시간 $(( n_new * ARM_MINUTES % 60 ))분."
  echo "다른 GPU에서는 달라진다(보장 아님). 결과: $KEEP_BASE/go2_g_a058_<key>/ 와 $KEEP_BASE/GO2_G_A058_<KEY>_RESULT.zip"
}

if [[ "${1:-}" == "--list" ]]; then
  print_plan
  exit 0
fi

(cd "$SWEEP_ROOT" && sha256sum -c --quiet SWEEP_SHA256SUMS.txt) || { echo '[FAIL] sweep package checksum mismatch'; exit 25; }

if [[ "${1:-}" != "--inner" ]]; then
  print_plan
  [[ -x "$ISAACLAB_SH" ]] || { echo "[FAIL] missing $ISAACLAB_SH (Isaac Lab 위치를 ISAACLAB_SH 로 알려 주거나 /workspace/IsaacLab 에 둔다)"; exit 22; }
  command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1 || { echo '[FAIL] nvidia-smi 가 GPU 를 찾지 못한다'; exit 22; }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && { echo "[BLOCKED] tmux session already exists: $TMUX_NAME (tmux attach -t $TMUX_NAME)"; exit 2; }
  printf -v INNER "cd %q && ISAACLAB_SH=%q GO2_SWEEP_WORK=%q GO2_SWEEP_MIN_FREE_GB=%q bash %q --inner" \
    "$SWEEP_ROOT" "$ISAACLAB_SH" "$WORK_BASE" "$MIN_FREE_GB" "$SELF"
  tmux new-session -d -s "$TMUX_NAME" "$INNER"
  echo "[STARTED] $TMUX_NAME — 진행 보기: tmux attach -t $TMUX_NAME   상태 표: $STATUS_TSV"
  echo "[RESUME] 끊기면 같은 명령을 다시 친다: bash $SELF"
  exit 0
fi

mkdir -p "$STATUS_DIR/logs"
exec > >(tee -a "$STATUS_DIR/sweep.log") 2>&1
echo "[SWEEP START] $(date -Is)"
# Record how this PC differs from the competition server; a difference in results is not
# read as a reward effect alone (Codex work order section 4).
{
  echo "RECORDED_AT=$(date -Is)"
  echo "SERVER_REFERENCE_GPU=NVIDIA GeForce RTX 5080, 580.126.09, 16303 MiB (meta/gpu.csv of the reused arms)"
  echo "THIS_GPU=$( (nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || echo unknown) | paste -sd';')"
  echo "UNAME=$(uname -a 2>/dev/null || echo unknown)"
  echo "ISAACLAB_SH=$ISAACLAB_SH"
  echo "ISAACLAB_GIT=$( (git -C "$(dirname "$ISAACLAB_SH")" describe --tags --always 2>/dev/null) || echo unknown)"
} >"$STATUS_DIR/ENVIRONMENT_$(date +%Y%m%d-%H%M%S).txt"

train_failures=0
while read -r key keep_name zip_name; do
  [[ -n "$key" ]] || continue
  keep="$KEEP_BASE/$keep_name"
  result="$KEEP_BASE/$zip_name"
  if verified_done "$keep" "$result"; then
    log_status "$key" SKIP_DONE 0 FULL_69_COMPLETE - - - "verified result already present"
    continue
  fi
  if safety_stopped "$keep" "$result"; then
    log_status "$key" SKIP_SAFETY_STOPPED 0 INCOMPLETE_EARLY_STOP - - - "run safety stop already recorded (non-finite training); not an evaluation verdict"
    continue
  fi
  free=$(free_gb)
  if (( free < MIN_FREE_GB )); then
    log_status "$key" ABORT_DISK 20 - - "$(date -Is)" - "free ${free} GB < ${MIN_FREE_GB} GB"
    exit 20
  fi
  if [[ "$TEST_MODE" != 1 ]]; then
    if pgrep -af 'train.py|play.py' >/dev/null 2>&1; then
      log_status "$key" ABORT_BUSY 21 - - "$(date -Is)" - "another train/play process is running"
      exit 21
    fi
    [[ -x "$ISAACLAB_SH" ]] || { log_status "$key" ABORT_ENV 22 - - "$(date -Is)" - "missing $ISAACLAB_SH"; exit 22; }
  fi
  resume=0
  [[ -d "$keep" ]] && resume=1
  if [[ "$resume" == 0 && -e "$result" ]]; then
    log_status "$key" BLOCKED_EXISTING_RESULT - - 0 "$(date -Is)" - "result ZIP exists without its folder; not overwritten — move it away to rerun"
    continue
  fi
  work="$WORK_BASE/$key"
  if [[ ! -d "$work" ]]; then
    mkdir -p "$work"
    cp -a "$SWEEP_ROOT/shared/." "$work/"
    cp -a "$SWEEP_ROOT/runs/$key/." "$work/"
  fi
  if ! (cd "$work" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) 2>/dev/null; then
    # The runner stages baseline/exported by deleting and re-copying it; an interruption in
    # between leaves a listed file missing.  Restore only package files (same bytes), never results.
    cp -a "$SWEEP_ROOT/shared/." "$work/"
    cp -a "$SWEEP_ROOT/runs/$key/." "$work/"
  fi
  if ! (cd "$work" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt); then
    log_status "$key" RUN_ERROR_MATERIALIZE - - "$resume" "$(date -Is)" - "work dir $work does not match its PACKAGE_SHA256SUMS"
    continue
  fi
  started=$(date -Is)
  runner="$work/$RUNNER_NAME"
  [[ -z "$RUNNER_OVERRIDE" ]] || runner="$RUNNER_OVERRIDE"
  set +e
  PACKAGE_ROOT="$work" GO2_RESUME="$resume" GO2_STAGE=full GO2_REMEASURE_BASELINE=0 ISAACLAB_SH="$ISAACLAB_SH" \
    bash "$runner" --inner </dev/null >"$STATUS_DIR/logs/${key}_$(date +%Y%m%d-%H%M%S).log" 2>&1
  rc=$?
  set -e
  collection=$({ sed -n 's/^COLLECTION_STATUS=//p' "$keep/RESULT_STATUS.txt" 2>/dev/null || true; } | tail -1)
  collection=${collection:--}
  if [[ "$rc" == 0 ]] && verified_done "$keep" "$result"; then
    log_status "$key" DONE "$rc" "$collection" "$resume" "$started" "$(date -Is)" "-"
    train_failures=0
    continue
  fi
  decision=$(runner_decision "$keep")
  if [[ "$rc" == 0 && "$decision" == CATASTROPHE_TRAINING_NONFINITE ]]; then
    # Run safety stop: the policy is not executable, so nothing was evaluated.  Not a performance verdict.
    log_status "$key" SAFETY_STOP_NONFINITE "$rc" "$collection" "$resume" "$started" "$(date -Is)" "training loss non-finite; runner evaluated nothing (run safety stop, not an evaluation verdict)"
    train_failures=0
    continue
  fi
  if [[ "$rc" == 0 ]]; then
    log_status "$key" COLLECTION_FAILED "$rc" "$collection" "$resume" "$started" "$(date -Is)" "runner finished but the harvest is not FULL_69_COMPLETE (decision=${decision:-?}); rerun resumes it"
    train_failures=0
    continue
  fi
  # Failed before any training output on a fresh arm: nothing arm-specific ran yet, so the
  # cause is the shared environment (Isaac Lab, GPU, package).  Stop instead of burning the list.
  if [[ "$resume" == 0 && ! -f "$keep/training/TRAIN_STARTED.marker" && ! -s "$keep/logs/candidate_training.log" ]]; then
    log_status "$key" ABORT_ENV_EARLY 23 "$collection" "$resume" "$started" "$(date -Is)" "runner rc=$rc before training started"
    exit 23
  fi
  if [[ -s "$keep/training/TRAIN_STATUS.txt" ]] && ! grep -qx 'TRAIN_RC=0' "$keep/training/TRAIN_STATUS.txt"; then
    train_failures=$((train_failures + 1))
  else
    train_failures=0
  fi
  log_status "$key" RUN_ERROR "$rc" "$collection" "$resume" "$started" "$(date -Is)" "see $STATUS_DIR/logs and $keep/RUNNER_STATUS.txt"
  if (( train_failures >= 2 )); then
    log_status "$key" ABORT_REPEATED_TRAIN_FAILURE 24 "$collection" "$resume" "$started" "$(date -Is)" "two consecutive arms failed in training"
    exit 24
  fi
done <"$ORDER"
echo "[SWEEP END] $(date -Is) — 상태 표 $STATUS_TSV"
exit 0
