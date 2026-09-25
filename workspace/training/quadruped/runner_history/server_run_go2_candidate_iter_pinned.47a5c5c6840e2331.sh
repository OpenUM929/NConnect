#!/usr/bin/env bash
# One upload -> one command -> one result ZIP.
#
# Staged candidate runner with a pinned evaluation checkpoint (first used by G-A033 v2).
#
# server_run_go2_candidate_staged.sh (G-A031/G-A032, run as released) evaluates the
# model train.py's finalize picks: the saved checkpoint nearest the highest mean
# reward.  That iteration moves with the reward curve, so candidate and baseline
# can be measured at different points of training: A017 was evaluated at iter 900,
# G-A032 at iter 700 (read from the checkpoints themselves).  This runner evaluates
# the candidate at the baseline's iteration instead (EVAL_CHECKPOINT_ITER in
# run_config.env).  finalize deletes every other model_*.pt when training ends, so
# the checkpoint is copied while training runs.  Training itself is untouched (R-6):
# the copy only reads logs/.  In the harvest, training/model_best.pt is the pinned
# checkpoint that was evaluated, training/model_best_by_reward.pt is finalize's
# pick, and training/CHECKPOINT_PIN.txt records both.  Everything outside the
# CHECKPOINT PIN blocks is the staged runner unchanged (asserted by the contract test).
#
# The staged runner's own header follows.
#
# Staged candidate runner (first used by G-A031/G-A032, basic-motion plan).
#
# A copy of server_run_go2_candidate_suite.sh (G-A030), which stays byte for
# byte as G-A030 shipped it.  set_case, run_eval_case, run_video, stage_policy,
# write_identity, run_full_suite, the training phase and the report recovery
# are that runner's code unchanged (asserted by the contract test).  What is new:
#   - two stages, GO2_STAGE=target (default) and GO2_STAGE=full.
#     target: training, catastrophe gate, the plan's target cases only, the
#       sentinel, the listed videos, one result ZIP.  The plan's criterion 1 is
#       decided on the target cases alone, so a target-stage failure is final.
#     full: with GO2_RESUME=1, the remaining cases of the 69; everything the
#       target stage measured is kept through the case fingerprints.
#   - PACKAGE_ROOT defaults to this script's own folder, not to G-A030's.
#   - no baseline videos when the stored arm already holds the counterparts.
#
# Phases
#   1  single-variable training; report.html preserved before any evaluation
#   2  catastrophe gate
#   3  candidate target cases (target stage) or 69-case suite (full stage)
#   4  baseline arm: sentinel cases, or the same cases with GO2_REMEASURE_BASELINE=1
#   5  videos
#   6  one-file packaging
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
[[ -s "$PACKAGE_ROOT/PACKAGE_SHA256SUMS.txt" && -s "$PACKAGE_ROOT/run_config.env" ]] || {
  echo "[FAIL] package must be extracted at $PACKAGE_ROOT"; exit 2;
}
# The run identity is read from a file, so the file is verified before use.
(cd "$PACKAGE_ROOT" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) || {
  echo '[FAIL] package checksum mismatch'; exit 2;
}
# shellcheck source=/dev/null
source "$PACKAGE_ROOT/run_config.env"
# BEGIN CHECKPOINT PIN: config
# Checked here, not in the outer preflight: the campaign runner calls --inner.
[[ "${EVAL_CHECKPOINT_ITER:-}" =~ ^[0-9]+$ ]] || {
  echo '[FAIL] run_config.env has no numeric EVAL_CHECKPOINT_ITER'; exit 2;
}
# END CHECKPOINT PIN: config

CANDIDATE_ROOT="$PACKAGE_ROOT/candidate"
BASELINE_ROOT="$PACKAGE_ROOT/baseline"
REGISTRY="$PACKAGE_ROOT/go2_self_eval_registry.json"
EXPECTED_REWARDS="$PACKAGE_ROOT/expected_rewards.json"
KEEP="/workspace/_keep/$KEEP_DIR_NAME"
RESULT_ZIP="/workspace/_keep/$RESULT_ZIP_NAME"
SEEDS=(101 202 303)
EVAL_STEPS=${GO2_EVAL_STEPS:-1000}
VIDEO_STEPS=${GO2_VIDEO_STEPS:-500}
RESUME=${GO2_RESUME:-0}
REMEASURE=${GO2_REMEASURE_BASELINE:-0}
STAGE=${GO2_STAGE:-target}

# The server has no system python3 (260909).  Resolve an interpreter from what
# is already there, exactly as the G-A027 runner does.
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
POSTURE_CHECK="$PACKAGE_ROOT/posture_contract_check.py"
CHECKS="$PACKAGE_ROOT/candidate_suite_checks.py"
PY=()
if command -v python3 >/dev/null 2>&1; then
  PY=(python3)
elif command -v python >/dev/null 2>&1; then
  PY=(python)
elif [[ -x "$ISAACLAB_SH" ]]; then
  PY=("$ISAACLAB_SH" -p)
fi
# Both roles ship a byte-identical evaluator (asserted by the package contract
# test), so one hash identifies the ruler every case was measured with.
EVALUATOR_SHA=$(sha256sum "$CANDIDATE_ROOT/go2_eval_telemetry.py" | awk '{print $1}')
REGISTRY_SHA=$(sha256sum "$REGISTRY" | awk '{print $1}')

# BEGIN GO2_REPORT_RECOVERY
recover_training_report() {
  local source="$CANDIDATE_ROOT/exported/report.html"
  mkdir -p "$KEEP/exported"
  if [[ ! -s "$source" || ! -f "$TRAIN_START_MARKER" || ! "$source" -nt "$TRAIN_START_MARKER" ]]; then
    # Preserve rejected server evidence without presenting it as the current report.
    [[ ! -f "$source" ]] || cp -a "$source" "$KEEP/exported/report.rejected.html"
    printf 'REPORT_STATUS=REPORT_REQUIRED_NOT_ACQUIRED\nREASON=missing_empty_or_stale\n' >"$KEEP/exported/REPORT_STATUS.txt"
    echo '[FAIL] REPORT_REQUIRED_NOT_ACQUIRED: current training report missing/empty/stale'
    return 4
  fi
  cp -a "$source" "$KEEP/exported/report.html" || return 4
  (cd "$KEEP/exported" && sha256sum report.html >report.html.sha256) || return 4
  printf 'REPORT_STATUS=REPORT_ACQUIRED\nSOURCE=%s\nIDENTITY=see_training_model_env_and_logs\n' "$source" >"$KEEP/exported/REPORT_STATUS.txt"
}
# END GO2_REPORT_RECOVERY

package_result() {
  local label=$1
  mkdir -p "$KEEP"
  printf 'RESULT_STATE=%s\nPACKAGED_AT=%s\n' "$label" "$(date -Is)" >"$KEEP/RESULT_STATUS.txt"
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
  [[ "$RESUME" == 0 || "$RESUME" == 1 ]] || { echo '[FAIL] GO2_RESUME must be 0 or 1'; exit 2; }
  [[ "$REMEASURE" == 0 || "$REMEASURE" == 1 ]] || { echo '[FAIL] GO2_REMEASURE_BASELINE must be 0 or 1'; exit 2; }
  [[ "$STAGE" == target || "$STAGE" == full ]] || { echo '[FAIL] GO2_STAGE must be target or full'; exit 2; }
  [[ ${#TARGET_CASES[@]} -gt 0 ]] || { echo '[FAIL] run_config.env has no TARGET_CASES'; exit 2; }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  [[ -x "$ISAACLAB_SH" ]] || { echo "[FAIL] missing $ISAACLAB_SH"; exit 2; }
  [[ ${#PY[@]} -gt 0 ]] || {
    echo '[FAIL] no python interpreter for the posture check: tried python3, python,'
    echo "       and $ISAACLAB_SH -p"; exit 2;
  }
  [[ -s "$POSTURE_CHECK" && -s "$CHECKS" ]] || { echo "[FAIL] missing check scripts in $PACKAGE_ROOT"; exit 2; }
  [[ -d "$CANDIDATE_ROOT" && -d "$BASELINE_ROOT" && -s "$REGISTRY" && -s "$EXPECTED_REWARDS" ]] || {
    echo "[FAIL] package must be extracted at $PACKAGE_ROOT"; exit 2;
  }
  # The stored baseline arm is comparable only through the ruler that measured
  # it.  The package ships that ruler; refuse to start on any other.
  [[ "$EVALUATOR_SHA" == "$EXPECTED_EVALUATOR_SHA" ]] || {
    echo "[FAIL] evaluator $EVALUATOR_SHA is not the baseline arm's $EXPECTED_EVALUATOR_SHA"; exit 2;
  }
  [[ "$REGISTRY_SHA" == "$EXPECTED_REGISTRY_SHA" ]] || {
    echo "[FAIL] registry $REGISTRY_SHA is not the baseline arm's $EXPECTED_REGISTRY_SHA"; exit 2;
  }
  [[ "$(sha256sum "$BASELINE_ROOT/exported/model_best.pt" | awk '{print $1}')" == "$BASELINE_MODEL_SHA" &&
     "$(sha256sum "$BASELINE_ROOT/exported/env.yaml" | awk '{print $1}')" == "$BASELINE_ENV_SHA" ]] || {
    echo "[FAIL] baseline $BASELINE_NAME artifacts do not match their frozen SHA"; exit 2;
  }
  pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py' && {
    echo '[BLOCKED] training/play process is already running'; exit 2;
  } || true
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
    echo "[BLOCKED] tmux session already exists: $TMUX_NAME"; exit 2;
  }
  # A default rerun must not destroy results that have not been downloaded yet.
  if [[ "$RESUME" == 0 && ( -d "$KEEP" || -e "$RESULT_ZIP" ) ]]; then
    if [[ "${GO2_DISCARD_PREVIOUS:-0}" != 1 ]]; then
      echo "[BLOCKED] results from a previous run are present:"
      [[ ! -d "$KEEP" ]] || echo "  $KEEP"
      [[ ! -e "$RESULT_ZIP" ]] || echo "  $RESULT_ZIP"
      echo '  download them first, then either GO2_RESUME=1 to continue that run'
      echo '  or GO2_DISCARD_PREVIOUS=1 to discard them deliberately'
      exit 2
    fi
    echo '[WARN] GO2_DISCARD_PREVIOUS=1 — deleting the previous run'
    rm -rf -- "$KEEP" "$RESULT_ZIP" "${RESULT_ZIP}.sha256"
  fi
  printf -v INNER_COMMAND "cd %q && PACKAGE_ROOT=%q GO2_RESUME=%q GO2_REMEASURE_BASELINE=%q GO2_STAGE=%q ISAACLAB_SH=%q bash server_run_go2_candidate_staged.sh --inner" \
    "$PACKAGE_ROOT" "$PACKAGE_ROOT" "$RESUME" "$REMEASURE" "$STAGE" "$ISAACLAB_SH"
  tmux new-session -d -s "$TMUX_NAME" "$INNER_COMMAND"
  echo "[STARTED] $TMUX_NAME work=$WORK_ID stage=$STAGE resume=$RESUME remeasure_baseline=$REMEASURE"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  # An estimate from prior wall time, not a cap: nothing here stops the run.
  if [[ "$STAGE" == target ]]; then
    echo "[ESTIMATE] target stage: training ~57m + $(( ${#TARGET_CASES[@]} + 1 )) candidate cases ~8m + ${#SENTINEL_CASES[@]} sentinel cases ~4m"
    echo "           + $(( ${#CANDIDATE_VIDEOS[@]} + ${#BASELINE_VIDEOS[@]} )) videos ~4m + packaging ~10m ~= 1h25m (1h40m with 20% margin)"
    echo "           read the result locally first; GO2_STAGE=full GO2_RESUME=1 then adds the other cases (~55m)"
  else
    echo "[ESTIMATE] full stage: training ~57m unless resumed + the candidate cases not yet measured (~45m after a target stage)"
    echo "           + packaging ~10m"
  fi
  echo "           GO2_REMEASURE_BASELINE=1 measures the baseline on the same cases instead of the sentinel"
  echo "[NO_DEADLINE] the script does not enforce a time limit; watch the clock yourself"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] $DONE_MARKER"
  exit 0
fi

mkdir -p "$KEEP/logs" "$KEEP/training" "$KEEP/evaluation" "$KEEP/reports" "$KEEP/meta" "$KEEP/exported"
exec > >(tee -a "$KEEP/launcher.log") 2>&1
on_exit() {
  local rc=$?
  if [[ "$rc" != 0 ]]; then
    trap - EXIT
    printf 'RUNNER_RC=%s\nFAILED_AT=%s\n' "$rc" "$(date -Is)" >"$KEEP/RUNNER_STATUS.txt"
    package_result PARTIAL || true
  fi
}
trap on_exit EXIT

echo "[START] $WORK_ID $RUN_ID resume=$RESUME remeasure_baseline=$REMEASURE at $(date -Is)"
(cd "$PACKAGE_ROOT" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt)
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$KEEP/meta/gpu.csv" || true
cp -a "$REGISTRY" "$EXPECTED_REWARDS" "$PACKAGE_ROOT/run_config.env" "$PACKAGE_ROOT/experiment.json" \
  "$PACKAGE_ROOT/PACKAGE_SHA256SUMS.txt" "$KEEP/meta/"
sha256sum "$REGISTRY" >"$KEEP/meta/registry.sha256"
sha256sum "$CANDIDATE_ROOT/go2_eval_telemetry.py" >"$KEEP/meta/evaluator.sha256"

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

set_case() {
  local case_id=$1
  VX=0 VY=0 WZ=0 PUSH_X= PUSH_Y= DR_MODE=0 TERRAIN_LABEL=plane
  TERRAIN_ARGS=("${PLANE[@]}")
  case "$case_id" in
    forward_slow) VX=0.30 ;;
    forward_nominal) VX=0.75 ;;
    forward_fast) VX=1.20 ;;
    backward) VX=-0.50 ;;
    left) VY=0.35 ;;
    right) VY=-0.35 ;;
    diagonal_left) VX=0.50; VY=0.30 ;;
    diagonal_right) VX=0.50; VY=-0.30 ;;
    combined_yaw_left) VX=0.50; VY=0.15; WZ=0.50 ;;
    combined_yaw_right) VX=0.50; VY=-0.15; WZ=-0.50 ;;
    rough_forward|rough_lateral)
      [[ "$case_id" == rough_lateral ]] && VY=0.30 || VX=0.50
      TERRAIN_LABEL=rough
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]')
      ;;
    # G7 shared this branch with G3 and never set NCRC_EVAL_DR, so every dr_seed_*
    # case ran the identical configuration to rough_forward and its steps.csv came
    # out byte-identical.  G7 carries weight 0.10 and was rescoring G3.
    dr_seed_*)
      VX=0.50; DR_MODE=1
      TERRAIN_LABEL=rough_dr
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]')
      ;;
    slope_plus_20|slope_minus_20)
      VX=0.50; TERRAIN_LABEL="$case_id"
      local key=hf_pyramid_slope_inv
      [[ "$case_id" == slope_minus_20 ]] && key=hf_pyramid_slope
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.proportion=1.0"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.slope_range=[0.36397023,0.36397023]")
      ;;
    stairs_10_up|stairs_10_down|stairs_15_up|stairs_15_down)
      VX=0.50; TERRAIN_LABEL="$case_id"; local key=pyramid_stairs height=0.10
      [[ "$case_id" == *_down ]] && key=pyramid_stairs_inv
      [[ "$case_id" == stairs_15_* ]] && height=0.15
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.proportion=1.0"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.step_height_range=[$height,$height]")
      ;;
    push_pos_x) PUSH_X=0.50 ;;
    push_neg_x) PUSH_X=-0.50 ;;
    push_pos_y) PUSH_Y=0.50 ;;
    push_neg_y) PUSH_Y=-0.50 ;;
    *) echo "[FAIL] unknown case: $case_id"; exit 4 ;;
  esac
}

posture_ok() {
  "${PY[@]}" "$POSTURE_CHECK" "$1"
}
run_eval_case() {
  local label=$1 root=$2 seed=$3 scenario=$4 case_id=$5 outroot=$6
  set_case "$case_id"
  local out="$outroot/cases/seed_${seed}/$case_id"
  mkdir -p "$out" "$KEEP/logs/$label"
  local -a cmd=(
    /workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 32 --headless
    "agent.seed=$seed"
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$VX,$VX]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$VY,$VY]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$WZ,$WZ]"
    "${TERRAIN_ARGS[@]}"
  )
  # Everything that can change a summary is in the fingerprint, or a resume
  # banks a case measured under different conditions (G-A027 runner, R3).
  local fingerprint
  fingerprint=$(
    { printf '%s\0%s\0%s\0%s\0%s\0%s\0%s\0' "$ACTIVE_MODEL_SHA" "$ACTIVE_ENV_SHA" \
        "$scenario" "$case_id" "$seed" "$EVAL_STEPS" "$EVALUATOR_SHA"
      printf '%s\0%s\0%s\0' "${DR_MODE:-0}" "${PUSH_X:-}" "${PUSH_Y:-}"
      printf '%s\0%s\0%s\0%s\0' "${NCRC_EVAL_FALL_TILT_COS:-}" \
        "${NCRC_EVAL_FALL_HEIGHT:-}" "${NCRC_EVAL_FALL_HOLD_S:-}" \
        "${NCRC_EVAL_FALL_GRACE_S:-}"
      printf '%s\0' "${cmd[@]}"; } \
      | sha256sum | awk '{print $1}'
  )
  if [[ "$RESUME" == 1 && -s "$out/summary.json" && -s "$out/STATUS.txt" && -s "$out/case_identity.sha256" ]] && \
     grep -qx 'EVAL_RC=0' "$out/STATUS.txt" && grep -qx "$fingerprint" "$out/case_identity.sha256"; then
    echo "[SKIP] eval $label $scenario/$case_id seed=$seed"
    return 0
  fi
  rm -rf -- "$out"
  mkdir -p "$out"
  printf 'COMMAND: '; printf '%q ' "${cmd[@]}"; printf '\n'
  local -a push_env=(env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y -u NCRC_EVAL_DR)
  [[ "${DR_MODE:-0}" == 1 ]] && push_env+=("NCRC_EVAL_DR=1")
  [[ -n "$PUSH_X" ]] && push_env+=("NCRC_PLAY_PUSH_X=$PUSH_X")
  [[ -n "$PUSH_Y" ]] && push_env+=("NCRC_PLAY_PUSH_Y=$PUSH_Y")
  set +e
  NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$EVAL_STEPS" NCRC_EVAL_CASE="$case_id" \
  NCRC_EVAL_SCENARIO="$scenario" NCRC_EVAL_SEED="$seed" \
    "${push_env[@]}" "${cmd[@]}" 2>&1 | tee "$KEEP/logs/$label/seed_${seed}_${case_id}.log"
  local rc=${PIPESTATUS[0]}
  set -e
  [[ "$rc" == 0 && -s "$out/summary.json" ]] && grep -qx 'EVAL_RC=0' "$out/STATUS.txt" || {
    echo "[FAIL] eval $label $scenario/$case_id seed=$seed rc=$rc"; exit 5;
  }
  posture_ok "$out/summary.json" || {
    echo "[FAIL] posture evidence missing for $label $case_id seed=$seed"; exit 5;
  }
  printf '%s\n' "$fingerprint" >"$out/case_identity.sha256"
}

stage_policy() {
  local root=$1 model=$2 env=$3
  cd "$root"
  rm -rf -- exported
  mkdir -p exported
  cp -a "$model" exported/model_best.pt
  cp -a "$env" exported/env.yaml
  ACTIVE_MODEL_SHA=$(sha256sum exported/model_best.pt | awk '{print $1}')
  ACTIVE_ENV_SHA=$(sha256sum exported/env.yaml | awk '{print $1}')
}
write_identity() {
  local label=$1 root=$2 model=$3 env=$4 out=$5
  mkdir -p "$out"
  cat >"$out/identity.json" <<IDEOF
{"policy":"$label","model_sha256":"$(sha256sum "$model" | awk '{print $1}')","env_sha256":"$(sha256sum "$env" | awk '{print $1}')","registry_sha256":"$REGISTRY_SHA","evaluator_sha256":"$(sha256sum "$root/go2_eval_telemetry.py" | awk '{print $1}')"}
IDEOF
}
run_full_suite() {
  local label=$1 root=$2 model=$3 env=$4 expected_sha=$5
  local out="$KEEP/evaluation/$label"
  echo "[SUITE] $label full 69-case G1-G7 over seeds ${SEEDS[*]}"
  stage_policy "$root" "$model" "$env"
  [[ -z "$expected_sha" || "$ACTIVE_MODEL_SHA" == "$expected_sha" ]] || {
    echo "[FAIL] $label model SHA mismatch: $ACTIVE_MODEL_SHA"; exit 7;
  }
  mkdir -p "$out/source"
  cp -a play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
    go2_policy_lineage.py go2_task "$out/source/"
  write_identity "$label" "$root" "$model" "$env" "$out"
  for seed in "${SEEDS[@]}"; do
    for case_id in forward_slow forward_nominal forward_fast; do
      run_eval_case "$label" "$root" "$seed" G1 "$case_id" "$out"
    done
    for case_id in backward left right diagonal_left diagonal_right combined_yaw_left combined_yaw_right; do
      run_eval_case "$label" "$root" "$seed" G2 "$case_id" "$out"
    done
    for case_id in rough_forward rough_lateral; do
      run_eval_case "$label" "$root" "$seed" G3 "$case_id" "$out"
    done
    for case_id in slope_plus_20 slope_minus_20; do
      run_eval_case "$label" "$root" "$seed" G4 "$case_id" "$out"
    done
    for case_id in stairs_10_up stairs_10_down stairs_15_up stairs_15_down; do
      run_eval_case "$label" "$root" "$seed" G5 "$case_id" "$out"
    done
    for case_id in push_pos_x push_neg_x push_pos_y push_neg_y; do
      run_eval_case "$label" "$root" "$seed" G6 "$case_id" "$out"
    done
    run_eval_case "$label" "$root" "$seed" G7 "dr_seed_${seed}" "$out"
  done
  [[ "$(find "$out/cases" -name summary.json | wc -l)" == 69 ]] || {
    echo "[FAIL] $label telemetry count is not 69"; exit 6;
  }
  [[ ! -s exported/policy.pt ]] || cp -a exported/policy.pt "$out/policy.pt"
}
run_video() {
  local label=$1 root=$2 model=$3 env=$4 scenario=$5 case_id=$6 seed=$7
  set_case "$case_id"
  local video="$KEEP/evaluation/$label/videos/${scenario}_${case_id}_seed_${seed}.mp4"
  local vfp="${video%.mp4}.identity.sha256"
  local vfingerprint
  local vmodel_sha venv_sha
  vmodel_sha=$(sha256sum "$model" | awk '{print $1}')
  venv_sha=$(sha256sum "$env" | awk '{print $1}')
  vfingerprint=$(printf '%s\0%s\0%s\0%s\0%s\0%s\0%s\0%s\0%s\0%s\0' \
    "$vmodel_sha" "$venv_sha" "$scenario" "$case_id" "$seed" "$VIDEO_STEPS" \
    "$EVALUATOR_SHA" "${DR_MODE:-0}" "${PUSH_X:-}" "${PUSH_Y:-}" \
    | sha256sum | awk '{print $1}')
  if [[ "$RESUME" == 1 && -s "$video" && -s "$vfp" ]] && grep -qx "$vfingerprint" "$vfp"; then
    echo "[SKIP] video $label $scenario/$case_id seed=$seed"
    return 0
  fi
  cd "$root"
  rm -rf -- exported
  mkdir -p exported "$KEEP/evaluation/$label/videos"
  cp -a "$model" exported/model_best.pt
  cp -a "$env" exported/env.yaml
  local -a cmd=(
    /workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 4
    --headless --video --video_length "$VIDEO_STEPS" --enable_cameras
    "agent.seed=$seed" 'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$VX,$VX]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$VY,$VY]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$WZ,$WZ]" "${TERRAIN_ARGS[@]}"
  )
  local -a push_env=(env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y -u NCRC_EVAL_DR)
  [[ "${DR_MODE:-0}" == 1 ]] && push_env+=("NCRC_EVAL_DR=1")
  [[ -n "$PUSH_X" ]] && push_env+=("NCRC_PLAY_PUSH_X=$PUSH_X")
  [[ -n "$PUSH_Y" ]] && push_env+=("NCRC_PLAY_PUSH_Y=$PUSH_Y")
  "${push_env[@]}" "${cmd[@]}" \
    2>&1 | tee "$KEEP/logs/$label/video_${scenario}_${case_id}_seed_${seed}.log"
  [[ -s exported/play_video.mp4 ]] || { echo "[FAIL] video missing: $label $scenario"; exit 8; }
  cp -a exported/play_video.mp4 "$video"
  printf '%s\n' "$vfingerprint" >"$vfp"
}
run_video_list() {
  local label=$1 root=$2 model=$3 env=$4
  shift 4
  local entry scenario case_id seed
  for entry in "$@"; do
    IFS=: read -r scenario case_id seed <<<"$entry"
    run_video "$label" "$root" "$model" "$env" "$scenario" "$case_id" "$seed"
  done
  [[ "$(find "$KEEP/evaluation/$label/videos" -name '*.mp4' | wc -l)" == "$#" ]] || {
    echo "[FAIL] expected $# videos for $label"; exit 8;
  }
}
count_files() {
  [[ -d "$1" ]] || { echo 0; return 0; }
  find "$1" -name "$2" | wc -l
}
finish() {
  local decision=$1 baseline_arm=$2
  local report_status
  report_status=$(sed -n 's/^REPORT_STATUS=//p' "$KEEP/exported/REPORT_STATUS.txt" 2>/dev/null || true)
  printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nWORK_ID=%s\nRUN_ID=%s\nDECISION=%s\nSINGLE_CHANGE=%s:%s->%s\nTRAIN_SEED=%s\nCANDIDATE_MODEL_SHA=%s\nCANDIDATE_ENV_SHA=%s\nBASELINE_NAME=%s\nBASELINE_MODEL_SHA=%s\nBASELINE_ARM=%s\nTELEMETRY_CANDIDATE=%s\nTELEMETRY_BASELINE=%s\nTELEMETRY_BASELINE_SENTINEL=%s\nVIDEOS_CANDIDATE=%s\nVIDEOS_BASELINE=%s\nREPORT_STATUS=%s\nEVALUATOR=posture_gate_v2\nEVALUATOR_SHA=%s\nREGISTRY_SHA=%s\nTELEMETRY_SCHEMA=6\nVIDEO_STATUS=VIDEO_UNKNOWN\nOFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED\n' \
    "$(date -Is)" "$WORK_ID" "$RUN_ID" "$decision" \
    "$SINGLE_CHANGE_NAME" "$SINGLE_CHANGE_FROM" "$SINGLE_CHANGE_TO" "$TRAIN_SEED" \
    "$CANDIDATE_SHA" "$(sha256sum "$CANDIDATE_ENV" | awk '{print $1}')" \
    "$BASELINE_NAME" "$BASELINE_MODEL_SHA" "$baseline_arm" \
    "$(count_files "$KEEP/evaluation/candidate/cases" summary.json)" \
    "$(count_files "$KEEP/evaluation/$BASELINE_LABEL/cases" summary.json)" \
    "$(count_files "$KEEP/evaluation/${BASELINE_LABEL}_sentinel/cases" summary.json)" \
    "$(count_files "$KEEP/evaluation/candidate/videos" '*.mp4')" \
    "$(count_files "$KEEP/evaluation/${BASELINE_LABEL}_videos/videos" '*.mp4')" \
    "${report_status:-UNKNOWN}" "$EVALUATOR_SHA" "$REGISTRY_SHA" >"$KEEP/RUNNER_STATUS.txt"
  printf 'STAGE=%s\n' "$STAGE" >>"$KEEP/RUNNER_STATUS.txt"
  # BEGIN CHECKPOINT PIN: status
  printf 'CANDIDATE_EVAL_ITER=%s\nREWARD_BEST_MODEL_ITER=%s\n' \
    "$(sed -n 's/^EVAL_CHECKPOINT_ITER=//p' "$KEEP/training/CHECKPOINT_PIN.txt")" \
    "$(sed -n 's/^REWARD_BEST_MODEL_ITER=//p' "$KEEP/training/CHECKPOINT_PIN.txt")" >>"$KEEP/RUNNER_STATUS.txt"
  # END CHECKPOINT PIN: status
  package_result FULL
  trap - EXIT
  echo "$DONE_MARKER"
  exit 0
}

# BEGIN CHECKPOINT PIN: functions
PIN_MODEL="$KEEP/training/model_iter${EVAL_CHECKPOINT_ITER}.pt"
PIN_RECORD="$KEEP/training/CHECKPOINT_PIN.txt"
# Copy logs/**/model_<iter>.pt once its size holds still for two looks.  Runs in
# the background during training; finalize removes the file when training ends.
snapshot_checkpoint() {
  local want="model_${EVAL_CHECKPOINT_ITER}.pt" found size prev=-1 still=0
  while :; do
    # `|| true`: logs/ does not exist yet when training starts, and under errexit and
    # pipefail a failing find would end this background loop without a word.
    found=$(find "$CANDIDATE_ROOT/logs" -type f -name "$want" 2>/dev/null | head -n 1) || true
    if [[ -n "$found" ]]; then
      size=$(stat -c %s "$found" 2>/dev/null || echo 0)
      if [[ "$size" -gt 0 && "$size" == "$prev" ]]; then still=$((still + 1)); else still=0; fi
      prev=$size
      if [[ "$still" -ge 2 ]] && cp "$found" "$PIN_MODEL.tmp" && mv "$PIN_MODEL.tmp" "$PIN_MODEL"; then
        echo "[CHECKPOINT PIN] copied $found ($size bytes)"
        return 0
      fi
    fi
    sleep "${GO2_PIN_POLL_S:-5}"
  done
}
# Right after training, before any failure gate can exit: stop the copier and take
# the file if finalize kept it (it does when the reward pick is this iteration).
stop_checkpoint_copier() {
  local found
  kill "$SNAPSHOT_PID" 2>/dev/null || true
  wait "$SNAPSHOT_PID" 2>/dev/null || true
  rm -f -- "$PIN_MODEL.tmp"
  if [[ ! -s "$PIN_MODEL" ]]; then
    found=$(find "$CANDIDATE_ROOT/logs" -type f -name "model_${EVAL_CHECKPOINT_ITER}.pt" 2>/dev/null | head -n 1) || true
    [[ -z "$found" ]] || cp -a "$found" "$PIN_MODEL"
  fi
}
# After the training gates: make the pinned checkpoint the evaluated candidate and record both picks.
settle_checkpoint_pin() {
  local best
  [[ -s "$PIN_MODEL" ]] || {
    echo "[FAIL] checkpoint model_${EVAL_CHECKPOINT_ITER}.pt was not captured during training"; return 3;
  }
  best=$(find "$CANDIDATE_ROOT/logs" -type f -name 'model_*.pt' 2>/dev/null \
    | sed -n 's/.*model_\([0-9][0-9]*\)\.pt$/\1/p' | head -n 1) || true
  mv "$KEEP/training/model_best.pt" "$KEEP/training/model_best_by_reward.pt"
  cp -a "$PIN_MODEL" "$KEEP/training/model_best.pt"
  printf 'EVAL_CHECKPOINT_ITER=%s\nEVAL_CHECKPOINT_SHA=%s\nREWARD_BEST_MODEL_ITER=%s\nREWARD_BEST_MODEL_SHA=%s\nRULE=the candidate is evaluated at the baseline checkpoint iteration; training/model_best.pt is that checkpoint, training/model_best_by_reward.pt is the finalize pick\n' \
    "$EVAL_CHECKPOINT_ITER" "$(sha256sum "$PIN_MODEL" | awk '{print $1}')" "${best:-UNKNOWN}" \
    "$(sha256sum "$KEEP/training/model_best_by_reward.pt" | awk '{print $1}')" >"$PIN_RECORD"
  cat "$PIN_RECORD"
}
# END CHECKPOINT PIN: functions
echo "[PHASE 1/6] $WORK_ID single-variable training: $SINGLE_CHANGE_NAME $SINGLE_CHANGE_FROM->$SINGLE_CHANGE_TO seed=$TRAIN_SEED envs=$NUM_ENVS iterations=$MAX_ITERATIONS"
cd "$CANDIDATE_ROOT"
TRAIN_START_MARKER="$KEEP/training/TRAIN_STARTED.marker"
if [[ "$RESUME" == 1 && -s "$KEEP/training/model_best.pt" && -s "$KEEP/training/env.yaml" ]] && \
  grep -qx 'TRAIN_RC=0' "$KEEP/training/TRAIN_STATUS.txt"; then
  # BEGIN CHECKPOINT PIN: resume
  grep -qx "EVAL_CHECKPOINT_ITER=$EVAL_CHECKPOINT_ITER" "$PIN_RECORD" 2>/dev/null &&
    grep -qx "EVAL_CHECKPOINT_SHA=$(sha256sum "$KEEP/training/model_best.pt" | awk '{print $1}')" "$PIN_RECORD" || {
    echo "[FAIL] preserved candidate model is not the pinned iter-$EVAL_CHECKPOINT_ITER checkpoint; refusing to resume"
    exit 4
  }
  # END CHECKPOINT PIN: resume
  if [[ ! -s "$KEEP/exported/report.html" ]] ||
     ! grep -qx 'REPORT_STATUS=REPORT_ACQUIRED' "$KEEP/exported/REPORT_STATUS.txt" ||
     ! (cd "$KEEP/exported" && sha256sum -c report.html.sha256); then
    echo 'REPORT_STATUS=REPORT_REQUIRED_NOT_ACQUIRED' >"$KEEP/training/REPORT_RESUME_STATUS.txt"
    echo '[FAIL] preserved training report missing or checksum mismatch; refusing to retrain/claim complete'
    exit 4
  fi
  echo '[SKIP] candidate training artifact already present'
else
  rm -rf -- logs exported
  mkdir -p exported
  touch "$TRAIN_START_MARKER"
  # BEGIN CHECKPOINT PIN: start copier
  rm -f -- "$PIN_MODEL" "$PIN_MODEL.tmp" "$PIN_RECORD"
  snapshot_checkpoint &
  SNAPSHOT_PID=$!
  # END CHECKPOINT PIN: start copier
  set +e
  # Rule 14: the operator's training-history backup stays on unless the caller
  # opted out explicitly (same handling as server_run_go2_tuning_engine_v1.sh).
  declare -a train_env=(env)
  if [[ -n "${NO_AUTO_SUBMIT:-}" ]]; then
    train_env+=("NO_AUTO_SUBMIT=$NO_AUTO_SUBMIT")
    echo "[WARN] NO_AUTO_SUBMIT=$NO_AUTO_SUBMIT — operator training-history backup is OFF for this run"
  else
    train_env+=(-u NO_AUTO_SUBMIT)
  fi
  "${train_env[@]}" "$ISAACLAB_SH" -p train.py \
    --task Quadruped-v0 --num_envs "$NUM_ENVS" --max_iterations "$MAX_ITERATIONS" --seed "$TRAIN_SEED" --headless \
    2>&1 | tee "$KEEP/logs/candidate_training.log"
  TRAIN_RC=${PIPESTATUS[0]}
  set -e
  # BEGIN CHECKPOINT PIN: stop copier
  stop_checkpoint_copier
  # END CHECKPOINT PIN: stop copier
  printf 'TRAIN_RC=%s\nSEED=%s\nNUM_ENVS=%s\nMAX_ITERATIONS=%s\nSINGLE_CHANGE=%s:%s->%s\n' \
    "$TRAIN_RC" "$TRAIN_SEED" "$NUM_ENVS" "$MAX_ITERATIONS" \
    "$SINGLE_CHANGE_NAME" "$SINGLE_CHANGE_FROM" "$SINGLE_CHANGE_TO" >"$KEEP/training/TRAIN_STATUS.txt"
  # Preserve available artifacts before any failure gate invokes PARTIAL packaging.
  for artifact in model_best.pt env.yaml policy.pt; do
    [[ ! -s "exported/$artifact" ]] || cp -a "exported/$artifact" "$KEEP/training/"
  done
  [[ ! -d logs ]] || cp -a logs "$KEEP/training/"
  recover_training_report || exit 4
  [[ "$TRAIN_RC" == 0 && -s exported/model_best.pt && -s exported/env.yaml ]] || {
    echo '[FAIL] candidate training or finalize failed'; exit 3;
  }
  cp -a exported/model_best.pt exported/env.yaml "$KEEP/training/"
  # BEGIN CHECKPOINT PIN: settle
  settle_checkpoint_pin || exit 3
  # END CHECKPOINT PIN: settle
fi
mkdir -p "$KEEP/training/source"
cp -a train.py play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
  go2_policy_lineage.py go2_task "$KEEP/training/source/"
sha256sum quadruped_rewards.py train.py play.py go2_task/*.py >"$KEEP/training/candidate_source.sha256"
diff -u "$PACKAGE_ROOT/reference/baseline_quadruped_rewards.py" quadruped_rewards.py \
  >"$KEEP/training/reward_only.diff" || true
# The reward file ignores unknown names with only a warning, so a trained
# env.yaml is the evidence of which weights were in force, not the source file.
if ! "${PY[@]}" "$CHECKS" env-rewards "$KEEP/training/env.yaml" "$EXPECTED_REWARDS" candidate \
    >"$KEEP/training/ENV_REWARD_CHECK.txt" 2>&1; then
  cat "$KEEP/training/ENV_REWARD_CHECK.txt"
  echo '[FAIL] the trained env.yaml does not carry the intended reward weights'; exit 3
fi
cat "$KEEP/training/ENV_REWARD_CHECK.txt"

CANDIDATE_MODEL="$KEEP/training/model_best.pt"
CANDIDATE_ENV="$KEEP/training/env.yaml"
CANDIDATE_SHA=$(sha256sum "$CANDIDATE_MODEL" | awk '{print $1}')
CAND_OUT="$KEEP/evaluation/candidate"
write_identity candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CAND_OUT"

echo "[PHASE 2/6] catastrophe gate: training loss finite, candidate moves on $CATASTROPHE_CASE"
DECISION=SUITE_COMPLETE
if grep -Eiq 'loss:[[:space:]]*-?(nan|inf)' "$KEEP/logs/candidate_training.log" 2>/dev/null; then
  DECISION=CATASTROPHE_TRAINING_NONFINITE
else
  IFS=: read -r GATE_SCENARIO GATE_CASE GATE_SEED <<<"$CATASTROPHE_CASE"
  stage_policy "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV"
  run_eval_case candidate "$CANDIDATE_ROOT" "$GATE_SEED" "$GATE_SCENARIO" "$GATE_CASE" "$CAND_OUT"
  set +e
  "${PY[@]}" "$CHECKS" moving "$CAND_OUT/cases/seed_${GATE_SEED}/$GATE_CASE/summary.json"
  GATE_RC=$?
  set -e
  case "$GATE_RC" in
    0) ;;
    1) DECISION=CATASTROPHE_STATIONARY ;;
    *) echo '[FAIL] catastrophe gate could not read its case summary'; exit 5 ;;
  esac
fi
if [[ "$DECISION" != SUITE_COMPLETE ]]; then
  echo "[EARLY STOP] $DECISION — the suite is skipped; one witness video is recorded"
  IFS=: read -r GATE_SCENARIO GATE_CASE GATE_SEED <<<"$CATASTROPHE_CASE"
  run_video_list candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CATASTROPHE_CASE"
  finish "$DECISION" NOT_MEASURED
fi

# The target stage measures a named list with the same run_eval_case, so a
# later full stage (GO2_RESUME=1) keeps these cases through their fingerprints.
run_case_list() {
  local label=$1 root=$2 model=$3 env=$4 expected_sha=$5 out=$6
  shift 6
  stage_policy "$root" "$model" "$env"
  [[ -z "$expected_sha" || "$ACTIVE_MODEL_SHA" == "$expected_sha" ]] || {
    echo "[FAIL] $label model SHA mismatch: $ACTIVE_MODEL_SHA"; exit 7;
  }
  mkdir -p "$out/source"
  cp -a play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
    go2_policy_lineage.py go2_task "$out/source/"
  write_identity "$label" "$root" "$model" "$env" "$out"
  local entry scenario case_id seed
  for entry in "$@"; do
    IFS=: read -r scenario case_id seed <<<"$entry"
    run_eval_case "$label" "$root" "$seed" "$scenario" "$case_id" "$out"
  done
}

if [[ "$STAGE" == target ]]; then
  echo "[PHASE 3/6] candidate target stage: ${#TARGET_CASES[@]} basic-motion cases (plan 6-1 item 1)"
  run_case_list candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$CAND_OUT" \
    "${TARGET_CASES[@]}"
  # The catastrophe case is measured too (phase 2) and is not one of the targets.
  [[ "$(find "$CAND_OUT/cases" -name summary.json | wc -l)" == "$(( ${#TARGET_CASES[@]} + 1 ))" ]] || {
    echo '[FAIL] candidate target-stage telemetry count mismatch'; exit 6;
  }
  STAGE_DECISION=TARGET_STAGE_COMPLETE
else
  echo '[PHASE 3/6] candidate full 69-case suite (cases already measured are kept on resume)'
  run_full_suite candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA"
  STAGE_DECISION=SUITE_COMPLETE
fi

BASELINE_MODEL="$KEEP/policy/baseline_model_best.pt"
BASELINE_ENV="$KEEP/policy/baseline_env.yaml"
mkdir -p "$KEEP/policy"
if [[ ! -s "$BASELINE_MODEL" || ! -s "$BASELINE_ENV" ]]; then
  cp -a "$BASELINE_ROOT/exported/model_best.pt" "$BASELINE_MODEL"
  cp -a "$BASELINE_ROOT/exported/env.yaml" "$BASELINE_ENV"
fi
if [[ "$REMEASURE" == 1 && "$STAGE" == target ]]; then
  echo "[PHASE 4/6] baseline $BASELINE_NAME remeasured on the target-stage cases on the candidate's evaluator"
  run_case_list "$BASELINE_LABEL" "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV" "$BASELINE_MODEL_SHA" \
    "$KEEP/evaluation/$BASELINE_LABEL" "$CATASTROPHE_CASE" "${TARGET_CASES[@]}"
  BASELINE_ARM=REMEASURED_SAME_RUN
elif [[ "$REMEASURE" == 1 ]]; then
  echo "[PHASE 4/6] baseline $BASELINE_NAME remeasured in full on the candidate's evaluator"
  run_full_suite "$BASELINE_LABEL" "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV" "$BASELINE_MODEL_SHA"
  BASELINE_ARM=REMEASURED_SAME_RUN
else
  echo "[PHASE 4/6] baseline $BASELINE_NAME sentinel: ${#SENTINEL_CASES[@]} cases re-measured against the stored arm"
  SENT_OUT="$KEEP/evaluation/${BASELINE_LABEL}_sentinel"
  stage_policy "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV"
  [[ "$ACTIVE_MODEL_SHA" == "$BASELINE_MODEL_SHA" ]] || {
    echo "[FAIL] baseline model SHA mismatch: $ACTIVE_MODEL_SHA"; exit 7;
  }
  write_identity "${BASELINE_LABEL}_sentinel" "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV" "$SENT_OUT"
  for entry in "${SENTINEL_CASES[@]}"; do
    IFS=: read -r scenario case_id seed <<<"$entry"
    run_eval_case "${BASELINE_LABEL}_sentinel" "$BASELINE_ROOT" "$seed" "$scenario" "$case_id" "$SENT_OUT"
  done
  [[ "$(find "$SENT_OUT/cases" -name summary.json | wc -l)" == "${#SENTINEL_CASES[@]}" ]] || {
    echo '[FAIL] sentinel telemetry count mismatch'; exit 6;
  }
  BASELINE_ARM=REUSED_STORED_WITH_SENTINEL
fi

echo '[PHASE 5/6] videos (the listed relevant cases only; a full-stage resume keeps them)'
# A stair or slope score cannot be adjudicated by a number alone: a policy
# parked on a stair-top platform reads as alive and on-command.
run_video_list candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "${CANDIDATE_VIDEOS[@]}"
if [[ ${#BASELINE_VIDEOS[@]} -gt 0 ]]; then
  run_video_list "${BASELINE_LABEL}_videos" "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV" "${BASELINE_VIDEOS[@]}"
fi

echo "[PHASE 6/6] one-file result packaging (stage=$STAGE)"
finish "$STAGE_DECISION" "$BASELINE_ARM"
