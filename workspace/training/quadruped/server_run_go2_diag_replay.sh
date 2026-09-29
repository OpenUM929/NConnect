#!/usr/bin/env bash
# One upload -> one command -> one result ZIP.   G-A052 diagnostic replay (2026-09-28).
#
# No training.  No reward change.  Replays the stored G-A048 policy (iter 900) on three
# cases it already failed on, with the evaluator that measured it, and adds read-only
# diagnostic channels (go2_eval_diag.py) to the same rollout.
#
#   1 plain  rough_lateral  seed 202   evaluator only - reproduction check
#   2 diag   rough_lateral  seed 202   evaluator + diag channels
#   3 diag   stairs_10_down seed 101   (the name says down; the case climbs)
#   4 diag   stairs_15_down seed 101
#
# The play.py command for each case is the one G-A048's runner issued (set_case and
# run_eval_case of server_run_go2_candidate_iter_pinned.sh, asserted by the contract
# test against G-A048's launcher.log).  plain/ holds G-A048's evaluated source bytes;
# diag/ holds the same bytes plus the wrapper, which play.py imports under the
# evaluator's name, and the unchanged evaluator renamed go2_eval_telemetry_v6.py.
#
# Env var GO2_DIAG_DRY_RUN=1 prints the four commands and exits (local contract test).
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
SELF=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
DRY_RUN=${GO2_DIAG_DRY_RUN:-0}
[[ -s "$PACKAGE_ROOT/PACKAGE_SHA256SUMS.txt" && -s "$PACKAGE_ROOT/run_config.env" ]] || {
  echo "[FAIL] package must be extracted at $PACKAGE_ROOT"; exit 2;
}
if [[ "$DRY_RUN" != 1 ]]; then
  (cd "$PACKAGE_ROOT" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) || { echo '[FAIL] package checksum mismatch'; exit 2; }
fi
# shellcheck source=/dev/null
source "$PACKAGE_ROOT/run_config.env"

PLAIN_ROOT="$PACKAGE_ROOT/plain"
DIAG_ROOT="$PACKAGE_ROOT/diag"
POLICY_DIR="$PACKAGE_ROOT/policy"
KEEP="/workspace/_keep/$KEEP_DIR_NAME"
RESULT_ZIP="/workspace/_keep/$RESULT_ZIP_NAME"
EVAL_STEPS=1000
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
RUNS=(
  "plain 202 G3 rough_lateral"
  "diag 202 G3 rough_lateral"
  "diag 101 G5 stairs_10_down"
  "diag 101 G5 stairs_15_down"
)

PLANE=(
  'env.scene.terrain.terrain_type=plane'
  'env.curriculum.terrain_levels=null'
)
GEN_BASE=(
  'env.scene.terrain.terrain_type=generator'
  'env.curriculum.terrain_levels=null'
  'env.scene.terrain.terrain_generator.curriculum=false'
  'env.scene.terrain.terrain_generator.num_rows=1'
  'env.scene.terrain.terrain_generator.num_cols=4'
  'env.scene.terrain.terrain_generator.difficulty_range=[1.0,1.0]'
  'env.scene.terrain.max_init_terrain_level=0'
)
ZERO_TERRAINS=(
  'env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.boxes.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0'
)

# The two branches of G-A048's set_case these cases use, unchanged.
set_case() {
  local case_id=$1
  VX=0 VY=0 WZ=0
  TERRAIN_ARGS=("${PLANE[@]}")
  case "$case_id" in
    rough_forward|rough_lateral)
      [[ "$case_id" == rough_lateral ]] && VY=0.30 || VX=0.50
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]')
      ;;
    stairs_10_up|stairs_10_down|stairs_15_up|stairs_15_down)
      VX=0.50; local key=pyramid_stairs height=0.10
      [[ "$case_id" == *_down ]] && key=pyramid_stairs_inv
      [[ "$case_id" == stairs_15_* ]] && height=0.15
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.proportion=1.0"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.step_height_range=[$height,$height]")
      ;;
    *) echo "[FAIL] unknown case: $case_id"; exit 4 ;;
  esac
}

case_command() {
  local seed=$1
  CMD=(
    "$ISAACLAB_SH" -p play.py --task Quadruped-v0 --num_envs 32 --headless
    "agent.seed=$seed"
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$VX,$VX]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$VY,$VY]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$WZ,$WZ]"
    "${TERRAIN_ARGS[@]}"
  )
}

if [[ "$DRY_RUN" == 1 ]]; then
  ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh
  for run in "${RUNS[@]}"; do
    read -r label seed scenario case_id <<<"$run"
    set_case "$case_id"; case_command "$seed"
    printf 'RUN %s %s %s COMMAND: ' "$label" "$seed" "$case_id"; printf '%q ' "${CMD[@]}"; printf '\n'
  done
  exit 0
fi

package_result() {
  local collection=$1
  mkdir -p "$KEEP"
  printf 'RESULT_STATE=PACKAGED\nCOLLECTION_STATUS=%s\nPACKAGED_AT=%s\n' "$collection" "$(date -Is)" >"$KEEP/RESULT_STATUS.txt"
  [[ ! -f "$KEEP/launcher.log" ]] || cp -a "$KEEP/launcher.log" "$KEEP/launcher.snapshot.log"
  (
    cd "$KEEP"
    find . -type f ! -name launcher.log ! -name SHA256SUMS.txt ! -name SHA256SUMS.txt.tmp -print0 \
      | sort -z | xargs -0 sha256sum >SHA256SUMS.txt.tmp
    mv SHA256SUMS.txt.tmp SHA256SUMS.txt
  )
  "$ISAACLAB_SH" -p "$PACKAGE_ROOT/package_go2_result.py" "$KEEP" "$RESULT_ZIP"
  sha256sum "$RESULT_ZIP" >"${RESULT_ZIP}.sha256"
  echo "[DOWNLOAD] $RESULT_ZIP"
  echo "[DOWNLOAD] ${RESULT_ZIP}.sha256"
}

if [[ "${1:-}" != "--inner" ]]; then
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  [[ -x "$ISAACLAB_SH" ]] || { echo "[FAIL] missing $ISAACLAB_SH"; exit 2; }
  for root in "$PLAIN_ROOT" "$DIAG_ROOT"; do
    [[ -s "$root/play.py" && -s "$root/go2_eval_telemetry.py" && -d "$root/go2_task" ]] || {
      echo "[FAIL] incomplete source root $root"; exit 2; }
  done
  [[ "$(sha256sum "$PLAIN_ROOT/go2_eval_telemetry.py" | awk '{print $1}')" == "$EXPECTED_EVALUATOR_SHA" &&
     "$(sha256sum "$DIAG_ROOT/go2_eval_telemetry_v6.py" | awk '{print $1}')" == "$EXPECTED_EVALUATOR_SHA" ]] || {
    echo "[FAIL] evaluator bytes are not G-A048's ($EXPECTED_EVALUATOR_SHA)"; exit 2; }
  [[ "$(sha256sum "$POLICY_DIR/model_best.pt" | awk '{print $1}')" == "$MODEL_SHA" &&
     "$(sha256sum "$POLICY_DIR/env.yaml" | awk '{print $1}')" == "$ENV_SHA" ]] || {
    echo "[FAIL] policy is not G-A048 iter 900 ($MODEL_SHA)"; exit 2; }
  pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py' && {
    echo '[BLOCKED] training/play process is already running'; exit 2; } || true
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && { echo "[BLOCKED] tmux session already exists: $TMUX_NAME"; exit 2; }
  if [[ -d "$KEEP" || -e "$RESULT_ZIP" ]]; then
    if [[ "${GO2_DISCARD_PREVIOUS:-0}" != 1 ]]; then
      echo "[BLOCKED] results from a previous run are present: $KEEP $RESULT_ZIP"
      echo '  download them first, or GO2_DISCARD_PREVIOUS=1 to discard them deliberately'
      exit 2
    fi
    echo '[WARN] GO2_DISCARD_PREVIOUS=1 - deleting the previous run'
    rm -rf -- "$KEEP" "$RESULT_ZIP" "${RESULT_ZIP}.sha256"
  fi
  printf -v INNER_COMMAND "cd %q && PACKAGE_ROOT=%q ISAACLAB_SH=%q bash %q --inner" \
    "$PACKAGE_ROOT" "$PACKAGE_ROOT" "$ISAACLAB_SH" "$SELF"
  tmux new-session -d -s "$TMUX_NAME" "$INNER_COMMAND"
  echo "[STARTED] $TMUX_NAME work=$WORK_ID runs=${#RUNS[@]} (no training)"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[ESTIMATE] 4 play.py runs; G-A048's suite took ~0.5 min per case including Isaac start-up;"
  echo "           allow 15 min including packaging (diag CSV adds write time, not measured before)"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] $DONE_MARKER"
  exit 0
fi

mkdir -p "$KEEP/logs" "$KEEP/meta"
exec > >(tee -a "$KEEP/launcher.log") 2>&1
on_exit() {
  local rc=$?
  if [[ "$rc" != 0 ]]; then
    trap - EXIT
    printf 'RUNNER_RC=%s\nFAILED_AT=%s\n' "$rc" "$(date -Is)" >"$KEEP/RUNNER_STATUS.txt"
    package_result INCOMPLETE_CRASH || true
  fi
}
trap on_exit EXIT

echo "[START] $WORK_ID at $(date -Is)"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$KEEP/meta/gpu.csv" || true
cp -a "$PACKAGE_ROOT/run_config.env" "$PACKAGE_ROOT/PACKAGE_SHA256SUMS.txt" "$PACKAGE_ROOT/experiment.json" "$KEEP/meta/"

for root in "$PLAIN_ROOT" "$DIAG_ROOT"; do
  rm -rf -- "$root/exported"
  mkdir -p "$root/exported"
  cp -a "$POLICY_DIR/model_best.pt" "$root/exported/model_best.pt"
  cp -a "$POLICY_DIR/env.yaml" "$root/exported/env.yaml"
done
cat >"$KEEP/meta/identity.json" <<IDEOF
{"work_id":"$WORK_ID","policy":"G-A048 iter 900","model_sha256":"$MODEL_SHA","env_sha256":"$ENV_SHA","evaluator_sha256":"$EXPECTED_EVALUATOR_SHA","diag_module_sha256":"$(sha256sum "$DIAG_ROOT/go2_eval_diag.py" | awk '{print $1}')","diag_wrapper_sha256":"$(sha256sum "$DIAG_ROOT/go2_eval_telemetry.py" | awk '{print $1}')"}
IDEOF

done_runs=0
for run in "${RUNS[@]}"; do
  read -r label seed scenario case_id <<<"$run"
  root=$PLAIN_ROOT
  [[ "$label" == diag ]] && root=$DIAG_ROOT
  set_case "$case_id"; case_command "$seed"
  out="$KEEP/$label/cases/seed_${seed}/$case_id"
  mkdir -p "$out"
  printf 'COMMAND: '; printf '%q ' "${CMD[@]}"; printf '\n'
  started=$(date +%s)
  set +e
  (cd "$root" && env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y -u NCRC_EVAL_DR \
    NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$EVAL_STEPS" NCRC_EVAL_CASE="$case_id" \
    NCRC_EVAL_SCENARIO="$scenario" NCRC_EVAL_SEED="$seed" \
    "${CMD[@]}") 2>&1 | tee "$KEEP/logs/${label}_seed_${seed}_${case_id}.log"
  rc=${PIPESTATUS[0]}
  set -e
  printf '%s %s %s rc=%s wall_s=%s\n' "$label" "$seed" "$case_id" "$rc" "$(( $(date +%s) - started ))" >>"$KEEP/meta/RUN_TIMES.txt"
  [[ "$rc" == 0 && -s "$out/summary.json" ]] && grep -qx 'EVAL_RC=0' "$out/STATUS.txt" || {
    echo "[FAIL] $label $case_id seed=$seed rc=$rc"; exit 5; }
  if [[ "$label" == diag ]]; then
    [[ -s "$out/diag.csv.gz" && -s "$out/DIAG_STATUS.txt" ]] || { echo "[FAIL] no diag output for $case_id"; exit 5; }
    cat "$out/DIAG_STATUS.txt"
  fi
  done_runs=$((done_runs + 1))
done

# Early read on interference only; the stored-run comparison is done locally.
a="$KEEP/plain/cases/seed_202/rough_lateral/steps.csv"
b="$KEEP/diag/cases/seed_202/rough_lateral/steps.csv"
if cmp -s "$a" "$b"; then echo 'PLAIN_VS_DIAG=IDENTICAL' >"$KEEP/meta/REPRO_STATUS.txt"
else echo 'PLAIN_VS_DIAG=DIFFERENT' >"$KEEP/meta/REPRO_STATUS.txt"; fi
cat "$KEEP/meta/REPRO_STATUS.txt"
printf 'RUNS_DONE=%s\nRUNS_PLANNED=%s\n' "$done_runs" "${#RUNS[@]}" >"$KEEP/RUNNER_STATUS.txt"
package_result COMPLETE_4_OF_4
trap - EXIT
echo "$DONE_MARKER"
