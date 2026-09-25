#!/usr/bin/env bash
# One upload -> one command -> one result ZIP.  Every arm runs the FULL 69 cases; there is no gate.
#
# Sibling of server_run_go2_campaign.sh (byte-shared helpers; the differences are named in
# tools/test_go2_g_a045_package_contract.py).  That script exists to spend GPU time carefully:
# it runs a cheap target stage first and only pays for the remaining cases when go2_target_gate.py
# says the arm is worth it.  This one is for the rounds where that saving is the wrong trade --
# G-A043's decisive loss sat outside its 23-case stage 1 and only appeared after the full 69 ran
# (defect C-11), and a round that measures the ruler itself has no winner to select at all.
#
#   1  each arm's full stage, through the arm's own iteration-pinned runner (--inner):
#      training, catastrophe gate, all 69 cases, the sentinel, the videos, that arm's result ZIP
#   2  one result ZIP: every arm result ZIP and CAMPAIGN_STATUS.txt
# No arm gates another: an arm that fails is packaged with what it collected and the next one runs.
# Nothing here decides performance.  The local verifier reads every harvest again after recovery
# and its verdict is the one of record.  All GPU work goes through the arm runner; this script
# never calls train.py or play.py itself.
#
# First used by G-A045 + G-A046, a training-seed pair.  A seed is not a reward weight, so no
# policy this script trains may be promoted: the arm specs carry
# promotion: forbidden_not_a_reward_change and the R-6 reading is the open decision
# U2-SEED-REPLICATE-20260918, which is the user's to close.
set -euo pipefail

SELF=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
CAMPAIGN_ROOT=${CAMPAIGN_ROOT:-$(dirname "$SELF")}
[[ -s "$CAMPAIGN_ROOT/CAMPAIGN_SHA256SUMS.txt" && -s "$CAMPAIGN_ROOT/campaign_config.env" ]] || {
  echo "[FAIL] campaign package must be extracted at $CAMPAIGN_ROOT"; exit 2;
}
(cd "$CAMPAIGN_ROOT" && sha256sum -c --quiet CAMPAIGN_SHA256SUMS.txt) || {
  echo '[FAIL] campaign package checksum mismatch'; exit 2;
}
# shellcheck source=/dev/null
source "$CAMPAIGN_ROOT/campaign_config.env"

WORKSPACE=/workspace
CAMPAIGN_KEEP="$WORKSPACE/_keep/$CAMPAIGN_KEEP_NAME"
CAMPAIGN_RESULT="$WORKSPACE/_keep/$CAMPAIGN_RESULT_ZIP"
# The arm runner is named by campaign_config.env (G-A033 v2: the iteration-pinned runner).
case "${ARM_RUNNER:-}" in
  server_run_go2_candidate_staged.sh|server_run_go2_candidate_iter_pinned.sh) ;;
  *) echo "[FAIL] campaign_config.env names no known ARM_RUNNER: '${ARM_RUNNER:-}'"; exit 2 ;;
esac
RESUME=${GO2_RESUME:-0}
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}

# One value from an arm's run_config.env, read in a subshell so the arms never mix.
arm_var() { ( source "$1/run_config.env"; printf '%s' "${!2}" ); }
arm_keep() { printf '%s/_keep/%s' "$WORKSPACE" "$(arm_var "$1" KEEP_DIR_NAME)"; }
arm_result() { printf '%s/_keep/%s' "$WORKSPACE" "$(arm_var "$1" RESULT_ZIP_NAME)"; }
status_of() {
  [[ -f "$1/RUNNER_STATUS.txt" ]] || return 0
  sed -n "s/^$2=//p" "$1/RUNNER_STATUS.txt" | tail -n 1
}
full_complete() {
  # Defect C-28: RUNNER_RC/STAGE/DECISION say the runner reached the end, not that the
  # 69 cases are on disk, and RUNNER_STATUS.txt is written before the ZIP is built.  A
  # skip needs both: the collection named complete, and a downloadable result that
  # verifies.  Anything less is resumed, not skipped.
  local keep=$1 result=$2
  [[ "$(status_of "$keep" RUNNER_RC)" == 0 && "$(status_of "$keep" STAGE)" == full &&
     "$(status_of "$keep" DECISION)" == SUITE_COMPLETE &&
     "$(status_of "$keep" COLLECTION_STATUS)" == FULL_69_COMPLETE ]] || return 1
  [[ -s "$result" && -s "${result}.sha256" ]] || return 1
  ( cd "$(dirname "$result")" && sha256sum -c --quiet "$(basename "$result").sha256" ) >/dev/null 2>&1
}

# The arm runner's own preflight, for every arm before anything starts, because
# the campaign calls each arm runner with --inner, which skips it.
preflight_arm() (
  root=$1 work=$2
  source "$root/run_config.env"
  [[ "$WORK_ID" == "$work" ]] || { echo "[FAIL] $root holds $WORK_ID, expected $work"; exit 2; }
  [[ ${#TARGET_CASES[@]} -gt 0 ]] || { echo "[FAIL] $WORK_ID run_config.env has no TARGET_CASES"; exit 2; }
  for name in "$ARM_RUNNER" posture_contract_check.py candidate_suite_checks.py package_go2_result.py \
      go2_self_eval_registry.json expected_rewards.json experiment.json; do
    [[ -s "$root/$name" ]] || { echo "[FAIL] $WORK_ID package is missing $name"; exit 2; }
  done
  [[ -d "$root/candidate" && -d "$root/baseline" ]] || { echo "[FAIL] $WORK_ID package is incomplete"; exit 2; }
  [[ "$(sha256sum "$root/candidate/go2_eval_telemetry.py" | awk '{print $1}')" == "$EXPECTED_EVALUATOR_SHA" ]] || {
    echo "[FAIL] $WORK_ID evaluator is not the baseline arm's $EXPECTED_EVALUATOR_SHA"; exit 2;
  }
  [[ "$(sha256sum "$root/go2_self_eval_registry.json" | awk '{print $1}')" == "$EXPECTED_REGISTRY_SHA" ]] || {
    echo "[FAIL] $WORK_ID registry is not the baseline arm's $EXPECTED_REGISTRY_SHA"; exit 2;
  }
  [[ "$(sha256sum "$root/baseline/exported/model_best.pt" | awk '{print $1}')" == "$BASELINE_MODEL_SHA" &&
     "$(sha256sum "$root/baseline/exported/env.yaml" | awk '{print $1}')" == "$BASELINE_ENV_SHA" ]] || {
    echo "[FAIL] $WORK_ID baseline $BASELINE_NAME artifacts do not match their frozen SHA"; exit 2;
  }
)
previous_results() {
  local root path
  for path in "$CAMPAIGN_KEEP" "$CAMPAIGN_RESULT"; do
    [[ ! -e "$path" ]] || echo "$path"
  done
  for root in "${ARM_ROOT[@]}"; do
    for path in "$(arm_keep "$root")" "$(arm_result "$root")"; do
      [[ ! -e "$path" ]] || echo "$path"
    done
  done
}

if [[ "${1:-}" != "--inner" ]]; then
  [[ "$RESUME" == 0 || "$RESUME" == 1 ]] || { echo '[FAIL] GO2_RESUME must be 0 or 1'; exit 2; }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  command -v unzip >/dev/null 2>&1 || { echo '[FAIL] unzip is missing'; exit 2; }
  [[ -x "$ISAACLAB_SH" ]] || { echo "[FAIL] missing $ISAACLAB_SH"; exit 2; }
  pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py' && {
    echo '[BLOCKED] training/play process is already running'; exit 2;
  } || true
  # The arm packages ship inside this one and are verified before they are used.
  for i in "${!ARM_WORK[@]}"; do
    zip="$CAMPAIGN_ROOT/arms/${ARM_ZIP[$i]}"
    [[ "$(sha256sum "$zip" | awk '{print $1}')" == "${ARM_ZIP_SHA[$i]}" ]] || {
      echo "[FAIL] ${ARM_WORK[$i]} package ${ARM_ZIP[$i]} is not the one this campaign was built with"; exit 2;
    }
    unzip -oq "$zip" -d "$WORKSPACE"
    (cd "${ARM_ROOT[$i]}" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) || {
      echo "[FAIL] ${ARM_WORK[$i]} package checksum mismatch after extraction"; exit 2;
    }
    preflight_arm "${ARM_ROOT[$i]}" "${ARM_WORK[$i]}" || exit 2
  done
  for name in "$CAMPAIGN_TMUX" $(for root in "${ARM_ROOT[@]}"; do arm_var "$root" TMUX_NAME; echo; done); do
    tmux has-session -t "$name" 2>/dev/null && { echo "[BLOCKED] tmux session already exists: $name"; exit 2; }
  done
  # A default rerun must not destroy results that have not been downloaded yet.
  mapfile -t previous < <(previous_results)
  if [[ "$RESUME" == 0 && ${#previous[@]} -gt 0 ]]; then
    if [[ "${GO2_DISCARD_PREVIOUS:-0}" != 1 ]]; then
      echo '[BLOCKED] results from a previous run are present:'
      printf '  %s\n' "${previous[@]}"
      echo '  download them first, then either GO2_RESUME=1 to continue that run'
      echo '  or GO2_DISCARD_PREVIOUS=1 to discard them deliberately'
      exit 2
    fi
    echo '[WARN] GO2_DISCARD_PREVIOUS=1 — deleting the previous run'
    for path in "${previous[@]}"; do rm -rf -- "$path" "${path}.sha256"; done
  fi
  [[ -f "$SELF" ]] || { echo "[FAIL] cannot find myself to re-enter: $SELF"; exit 2; }
  printf -v INNER_COMMAND "cd %q && CAMPAIGN_ROOT=%q GO2_RESUME=%q ISAACLAB_SH=%q bash %q --inner" \
    "$CAMPAIGN_ROOT" "$CAMPAIGN_ROOT" "$RESUME" "$ISAACLAB_SH" "$SELF"
  tmux new-session -d -s "$CAMPAIGN_TMUX" "$INNER_COMMAND"
  echo "[STARTED] $CAMPAIGN_TMUX campaign=$CAMPAIGN_ID arms=${ARM_WORK[*]} resume=$RESUME"
  echo "[MONITOR] tmux attach -t $CAMPAIGN_TMUX"
  # An estimate from prior wall time, not a cap: nothing here stops the run.
  echo "[ESTIMATE] ~95m per arm (${#ARM_WORK[@]} arm(s)): training ~59m, then all 69 cases, the sentinel and the videos"
  echo "           measured on G-A044, which took 94m end to end for one arm.  A plan figure, not a cap"
  echo "[NO_DEADLINE] the script does not enforce a time limit; watch the clock yourself"
  echo "[DOWNLOAD_WHEN_DONE] $CAMPAIGN_RESULT"
  echo "[DONE_MARKER] $CAMPAIGN_DONE_MARKER"
  exit 0
fi

mkdir -p "$CAMPAIGN_KEEP/arm_results"
LOG="$CAMPAIGN_KEEP/CAMPAIGN_LOG.txt"
log() { printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }
declare -A STATE=()

sha_or_none() {
  if [[ -s "$1" ]]; then sha256sum "$1" | awk '{print $1}'; else echo NONE; fi
}
write_campaign_status() {
  local rc=$1 state=$2 root work key keep
  {
    printf 'CAMPAIGN_RC=%s\nRESULT_STATE=%s\nWRITTEN_AT=%s\nCAMPAIGN_ID=%s\nRELEASE_ID=%s\n' \
      "$rc" "$state" "$(date -Is)" "$CAMPAIGN_ID" "$CAMPAIGN_RELEASE_ID"
    for root in "${ARM_ROOT[@]}"; do
      work=$(arm_var "$root" WORK_ID)
      key=${work//-/_}
      keep=$(arm_keep "$root")
      printf '%s_STATE=%s\n%s_COLLECTION=%s\n%s_STAGE=%s\n%s_DECISION=%s\n%s_RESULT_SHA=%s\n' \
        "$key" "${STATE[$work]:-NOT_RUN}" "$key" "$(status_of "$keep" COLLECTION_STATUS)" \
        "$key" "$(status_of "$keep" STAGE)" "$key" "$(status_of "$keep" DECISION)" \
        "$key" "$(sha_or_none "$(arm_result "$root")")"
    done
    printf 'GATE_ROLE=none_every_arm_runs_the_full_69_and_this_script_schedules_nothing\n'
    printf 'OFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED\n'
  } >"$CAMPAIGN_KEEP/CAMPAIGN_STATUS.txt"
}
package_campaign() {
  local state=$1 rc=$2 root result
  for root in "${ARM_ROOT[@]}"; do
    result=$(arm_result "$root")
    [[ ! -s "$result" ]] || cp -a "$result" "$CAMPAIGN_KEEP/arm_results/"
    [[ ! -s "${result}.sha256" ]] || cp -a "${result}.sha256" "$CAMPAIGN_KEEP/arm_results/"
  done
  write_campaign_status "$rc" "$state"
  (
    cd "$CAMPAIGN_KEEP"
    find . -type f ! -name SHA256SUMS.txt ! -name SHA256SUMS.txt.tmp -print0 \
      | sort -z | xargs -0 sha256sum >SHA256SUMS.txt.tmp
    mv SHA256SUMS.txt.tmp SHA256SUMS.txt
  )
  "$ISAACLAB_SH" -p "${ARM_ROOT[0]}/package_go2_result.py" "$CAMPAIGN_KEEP" "$CAMPAIGN_RESULT"
  sha256sum "$CAMPAIGN_RESULT" >"${CAMPAIGN_RESULT}.sha256"
  echo "[DOWNLOAD] $CAMPAIGN_RESULT"
  echo "[DOWNLOAD] ${CAMPAIGN_RESULT}.sha256"
}
on_exit() {
  local rc=$?
  trap - EXIT
  if [[ "$rc" != 0 ]]; then
    log "[FAIL] campaign runner rc=$rc; packaging what exists"
    package_campaign PARTIAL "$rc" || true
  fi
}
trap on_exit EXIT

run_stage() {
  local root=$1 stage=$2 resume=$3 remeasure=$4
  log "[ARM] $(arm_var "$root" WORK_ID) stage=$stage resume=$resume remeasure_baseline=$remeasure"
  (cd "$root" && PACKAGE_ROOT="$root" GO2_RESUME="$resume" GO2_REMEASURE_BASELINE="$remeasure" \
    GO2_STAGE="$stage" ISAACLAB_SH="$ISAACLAB_SH" bash "$ARM_RUNNER" --inner)
}
arm_phase() {
  local root=$1 work keep resume=0
  work=$(arm_var "$root" WORK_ID)
  keep=$(arm_keep "$root")
  if full_complete "$keep" "$(arm_result "$root")"; then
    STATE[$work]=FULL_DONE
    log "[SKIP] $work already collected the full 69"
    return 0
  fi
  # A half-finished harvest is continued, never started over: the arm runner's own resume
  # is what keeps a dropped connection from costing the training again.
  if [[ -d "$keep" ]]; then resume=1; fi
  if run_stage "$root" full "$resume" 0 && full_complete "$keep" "$(arm_result "$root")"; then
    STATE[$work]=FULL_DONE
  else
    STATE[$work]=FULL_RUNNER_FAILED
    log "[ARM FAILED] $work full stage; what it collected is kept and the next arm goes on"
  fi
}
log "[START] campaign $CAMPAIGN_ID ($CAMPAIGN_RELEASE_ID) resume=$RESUME"
(cd "$CAMPAIGN_ROOT" && sha256sum -c --quiet CAMPAIGN_SHA256SUMS.txt)
log "[PHASE 1/2] full 69-case collection, arm by arm: ${ARM_WORK[*]}"
for root in "${ARM_ROOT[@]}"; do
  arm_phase "$root"
done
log '[PHASE 2/2] one-file campaign result'
for root in "${ARM_ROOT[@]}"; do
  work=$(arm_var "$root" WORK_ID)
  log "[RESULT] $work state=${STATE[$work]:-NOT_RUN} collection=$(status_of "$(arm_keep "$root")" COLLECTION_STATUS)"
done
package_campaign CAMPAIGN_COMPLETE 0
trap - EXIT
echo "$CAMPAIGN_DONE_MARKER"
