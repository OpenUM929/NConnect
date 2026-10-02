#!/usr/bin/env bash
# PC2 single-point launcher (2026-10-02, design: upload/plan/GO2_PC2_DENSE_SWEEP_PROPOSAL_20261002.md §13-3·§14).
# Source: tools/go2_pc2_run_point.sh; packaged as <package>/run_point.sh.
#
# Runs exactly ONE named point of the PC2 point list and stops.  Which point runs next is a separate,
# human decision taken after the readout of the previous point (§13-1); this file never chains points.
# Each point is the audited G-A055 runner (server_run_go2_candidate_iter_pinned.sh, bytes unchanged)
# started in --inner mode on its own materialised package root, exactly as in G-A057/G-A058.
#
#   bash run_point.sh                  help only (no run)
#   bash run_point.sh --list           list the points and their state
#   bash run_point.sh --only <key>     preflight, then run that one point inside tmux and stop
#   bash run_point.sh --inner <key>    the single run itself (what tmux runs)
#
# Any other argument, a missing key, a key not in points.txt or a key that looks like a path is
# refused before any folder is created or training starts (exit 64).
#
# Exit codes of --inner: 0 DONE or SKIP_DONE
#   20 free disk below GO2_POINT_MIN_FREE_GB     21 another train/play process is running
#   22 Isaac Lab / GPU missing                   23 failed before training started (environment)
#   25 package checksum mismatch                 30 RUN_ERROR (runner rc != 0)
#   31 COLLECTION_FAILED (rc 0, harvest not FULL_69_COMPLETE)   32 SAFETY_STOP_NONFINITE
#   33 BLOCKED_EXISTING_RESULT                   34 RUN_ERROR_MATERIALIZE
# Nothing here judges performance.  A stationary policy is still collected on all 69 cases.
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SELF="$ROOT_DIR/$(basename "${BASH_SOURCE[0]}")"
RUNNER_NAME=server_run_go2_candidate_iter_pinned.sh
POINTS="$ROOT_DIR/points.txt"
# point_config.env carries only names (work id, status dir, work dir, tmux session); it is in the checksum list.
# shellcheck disable=SC1091
source "$ROOT_DIR/point_config.env"
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
WORK_BASE=${GO2_POINT_WORK:-$POINT_WORK_DIR}
MIN_FREE_GB=${GO2_POINT_MIN_FREE_GB:-20}
TEST_MODE=${GO2_POINT_TEST_MODE:-0}
if [[ "$TEST_MODE" == 1 ]]; then
  KEEP_BASE=${GO2_POINT_KEEP_BASE:?test mode needs GO2_POINT_KEEP_BASE}
  RUNNER_OVERRIDE=${GO2_POINT_TEST_RUNNER:?test mode needs GO2_POINT_TEST_RUNNER}
else
  KEEP_BASE=/workspace/_keep
  RUNNER_OVERRIDE=
fi
STATUS_DIR="$KEEP_BASE/$POINT_STATUS_DIR_NAME"
STATUS_TSV="$STATUS_DIR/POINT_STATUS.tsv"

usage() {
  cat <<EOF
PC2 단일 점 실행기 ($POINT_WORK_ID) — 한 번에 한 점만 돌고 멈춘다.
  bash $SELF --list          점 목록과 상태
  bash $SELF --only <key>    그 점 하나만 실행(tmux $POINT_TMUX_NAME), 끝나면 멈춘다
다음 점은 앞 점 판독 뒤 따로 정한다(자동 연결 없음).
EOF
}

refuse() { echo "[REFUSED] $1"; usage; exit 64; }

check_key() {  # key — reject before any folder exists
  local k=${1:-}
  [[ -n "$k" ]] || refuse "key 가 없다"
  [[ "$k" =~ ^[a-z0-9_]+$ ]] || refuse "key 형식이 아니다(경로·공백 불가): $k"
  awk -v k="$k" '$1==k {f=1} END {exit !f}' "$POINTS" || refuse "목록에 없는 key: $k"
}

point_line() { awk -v k="$1" '$1==k {print $2, $3}' "$POINTS"; }

log_status() {  # key status rc collection resume started ended note
  mkdir -p "$STATUS_DIR"
  [[ -s "$STATUS_TSV" ]] || printf 'key\tstatus\trc\tcollection\tresume\tstarted\tended\tnote\n' >"$STATUS_TSV"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >>"$STATUS_TSV"
  echo "[POINT] $1 $2 rc=$3 collection=$4 resume=$5 $8"
}

verified_done() {  # keep result_zip
  local keep=$1 zip=$2
  [[ -s "$keep/RESULT_STATUS.txt" && -s "$zip" && -s "$zip.sha256" ]] || return 1
  grep -qx 'RESULT_STATE=FULL' "$keep/RESULT_STATUS.txt" || return 1
  grep -qx 'COLLECTION_STATUS=FULL_69_COMPLETE' "$keep/RESULT_STATUS.txt" || return 1
  [[ "$(awk '{print $1}' "$zip.sha256")" == "$(sha256sum "$zip" | awk '{print $1}')" ]]
}

runner_decision() { { sed -n 's/^DECISION=//p' "$1/RUNNER_STATUS.txt" 2>/dev/null || true; } | tail -1; }

free_gb() {
  if [[ -n "${GO2_POINT_TEST_FREE_GB:-}" && "$TEST_MODE" == 1 ]]; then echo "$GO2_POINT_TEST_FREE_GB"; return; fi
  mkdir -p "$KEEP_BASE"
  df -Pk "$KEEP_BASE" | awk 'NR==2 {print int($4/1048576)}'
}

print_list() {
  local key keep zip change
  echo "=== $POINT_WORK_ID PC2 점 목록 (최대 목록 — 실행 여부는 점마다 따로 정한다) ==="
  while read -r key keep zip; do
    [[ -n "$key" ]] || continue
    change=$(grep -E '^SINGLE_CHANGE_(NAME|FROM|TO)=' "$ROOT_DIR/runs/$key/run_config.env" | cut -d= -f2 | paste -sd' ')
    if verified_done "$KEEP_BASE/$keep" "$KEEP_BASE/$zip" 2>/dev/null; then
      printf '  %-34s %-40s [완료·검증됨]\n' "$key" "$change"
    elif [[ -d "$KEEP_BASE/$keep" ]]; then
      printf '  %-34s %-40s [부분 결과 — 같은 --only 로 이어서]\n' "$key" "$change"
    else
      printf '  %-34s %-40s [미실행]\n' "$key" "$change"
    fi
  done <"$POINTS"
}

# ---- argument parsing: nothing below runs for a refused call ----
MODE=help
KEY=
case "$#" in
  0) MODE=help ;;
  1) case "$1" in
       --help|-h) MODE=help ;;
       --list) MODE=list ;;
       --only|--inner) refuse "$1 에 key 가 없다" ;;
       *) refuse "알 수 없는 인수: $1" ;;
     esac ;;
  2) case "$1" in
       --only) MODE=only; KEY=$2 ;;
       --inner) MODE=inner; KEY=$2 ;;
       *) refuse "알 수 없는 인수: $1" ;;
     esac ;;
  *) refuse "인수가 너무 많다: $*" ;;
esac

case "$MODE" in
  help) usage; exit 0 ;;
  list) print_list; exit 0 ;;
esac

check_key "$KEY"
(cd "$ROOT_DIR" && sha256sum -c --quiet SHA256SUMS.txt) || { echo '[FAIL] package checksum mismatch'; exit 25; }

if [[ "$MODE" == only ]]; then
  print_list
  printf -v INNER "cd %q && ISAACLAB_SH=%q GO2_POINT_WORK=%q GO2_POINT_MIN_FREE_GB=%q bash %q --inner %q" \
    "$ROOT_DIR" "$ISAACLAB_SH" "$WORK_BASE" "$MIN_FREE_GB" "$SELF" "$KEY"
  if [[ "$TEST_MODE" == 1 ]]; then
    # GPU-free contract test: same command string, run in the foreground instead of tmux.
    bash -c "$INNER"
    exit $?
  fi
  [[ -x "$ISAACLAB_SH" ]] || { echo "[FAIL] missing $ISAACLAB_SH (ISAACLAB_SH 로 위치를 알려 준다)"; exit 22; }
  command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1 || { echo '[FAIL] nvidia-smi 가 GPU 를 찾지 못한다'; exit 22; }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 22; }
  tmux has-session -t "$POINT_TMUX_NAME" 2>/dev/null && { echo "[BLOCKED] tmux session already exists: $POINT_TMUX_NAME"; exit 21; }
  tmux new-session -d -s "$POINT_TMUX_NAME" "$INNER"
  echo "[STARTED] $KEY in tmux $POINT_TMUX_NAME — 진행: tmux attach -t $POINT_TMUX_NAME  상태: $STATUS_TSV"
  echo "[NOTE] 이 점이 끝나면 멈춘다. 다음 점은 판독 뒤 따로 정한다."
  exit 0
fi

# ---- --inner: exactly one point ----
read -r keep_name zip_name <<<"$(point_line "$KEY")"
keep="$KEEP_BASE/$keep_name"
result="$KEEP_BASE/$zip_name"
mkdir -p "$STATUS_DIR/logs"
exec > >(tee -a "$STATUS_DIR/point.log") 2>&1
echo "[POINT START] $KEY $(date -Is)"
{
  echo "RECORDED_AT=$(date -Is)"
  echo "POINT_KEY=$KEY"
  echo "THIS_GPU=$( (nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || echo unknown) | paste -sd';')"
  echo "UNAME=$(uname -a 2>/dev/null || echo unknown)"
  echo "ISAACLAB_SH=$ISAACLAB_SH"
  echo "ISAACLAB_GIT=$( (git -C "$(dirname "$ISAACLAB_SH")" describe --tags --always 2>/dev/null) || echo unknown)"
} >"$STATUS_DIR/ENVIRONMENT_${KEY}_$(date +%Y%m%d-%H%M%S).txt"

if verified_done "$keep" "$result"; then
  log_status "$KEY" SKIP_DONE 0 FULL_69_COMPLETE - - - "verified result already present; nothing rerun"
  exit 0
fi
free=$(free_gb)
if (( free < MIN_FREE_GB )); then
  log_status "$KEY" ABORT_DISK 20 - - "$(date -Is)" - "free ${free} GB < ${MIN_FREE_GB} GB"
  exit 20
fi
if [[ "$TEST_MODE" != 1 ]]; then
  if pgrep -af 'train.py|play.py' >/dev/null 2>&1; then
    log_status "$KEY" ABORT_BUSY 21 - - "$(date -Is)" - "another train/play process is running"
    exit 21
  fi
  [[ -x "$ISAACLAB_SH" ]] || { log_status "$KEY" ABORT_ENV 22 - - "$(date -Is)" - "missing $ISAACLAB_SH"; exit 22; }
fi
resume=0
[[ -d "$keep" ]] && resume=1
if [[ "$resume" == 0 && -e "$result" ]]; then
  log_status "$KEY" BLOCKED_EXISTING_RESULT 33 - 0 "$(date -Is)" - "result ZIP exists without its folder; not overwritten"
  exit 33
fi
work="$WORK_BASE/$KEY"
if [[ ! -d "$work" ]]; then
  mkdir -p "$work"
  cp -a "$ROOT_DIR/shared/." "$work/"
  cp -a "$ROOT_DIR/runs/$KEY/." "$work/"
fi
if ! (cd "$work" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) 2>/dev/null; then
  # Restore only package files (same bytes); results live in $keep, never in $work.
  cp -a "$ROOT_DIR/shared/." "$work/"
  cp -a "$ROOT_DIR/runs/$KEY/." "$work/"
fi
if ! (cd "$work" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt); then
  log_status "$KEY" RUN_ERROR_MATERIALIZE 34 - "$resume" "$(date -Is)" - "work dir $work does not match its PACKAGE_SHA256SUMS"
  exit 34
fi
started=$(date -Is)
runner="$work/$RUNNER_NAME"
[[ -z "$RUNNER_OVERRIDE" ]] || runner="$RUNNER_OVERRIDE"
set +e
PACKAGE_ROOT="$work" GO2_RESUME="$resume" GO2_STAGE=full GO2_REMEASURE_BASELINE=0 ISAACLAB_SH="$ISAACLAB_SH" \
  bash "$runner" --inner </dev/null >"$STATUS_DIR/logs/${KEY}_$(date +%Y%m%d-%H%M%S).log" 2>&1
rc=$?
set -e
collection=$({ sed -n 's/^COLLECTION_STATUS=//p' "$keep/RESULT_STATUS.txt" 2>/dev/null || true; } | tail -1)
collection=${collection:--}
if [[ "$rc" == 0 ]] && verified_done "$keep" "$result"; then
  log_status "$KEY" DONE "$rc" "$collection" "$resume" "$started" "$(date -Is)" "-"
  echo "[POINT END] $KEY DONE — 다음 점은 판독 뒤 따로 정한다."
  exit 0
fi
decision=$(runner_decision "$keep")
if [[ "$rc" == 0 && "$decision" == CATASTROPHE_TRAINING_NONFINITE ]]; then
  log_status "$KEY" SAFETY_STOP_NONFINITE 32 "$collection" "$resume" "$started" "$(date -Is)" "training loss non-finite; nothing evaluated (run safety stop, not an evaluation verdict)"
  exit 32
fi
if [[ "$rc" == 0 ]]; then
  log_status "$KEY" COLLECTION_FAILED 31 "$collection" "$resume" "$started" "$(date -Is)" "harvest not FULL_69_COMPLETE (decision=${decision:-?}); the same --only resumes it"
  exit 31
fi
if [[ "$resume" == 0 && ! -f "$keep/training/TRAIN_STARTED.marker" && ! -s "$keep/logs/candidate_training.log" ]]; then
  log_status "$KEY" ABORT_ENV_EARLY 23 "$collection" "$resume" "$started" "$(date -Is)" "runner rc=$rc before training started"
  exit 23
fi
log_status "$KEY" RUN_ERROR 30 "$collection" "$resume" "$started" "$(date -Is)" "runner rc=$rc; see $STATUS_DIR/logs and $keep/RUNNER_STATUS.txt"
exit 30
