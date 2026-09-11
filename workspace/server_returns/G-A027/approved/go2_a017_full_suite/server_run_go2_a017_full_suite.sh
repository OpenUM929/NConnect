#!/usr/bin/env bash
# One upload -> one command -> one result ZIP.  NO TRAINING.
#
# G-A027 "G-A017 full-suite measurement".  NO TRAINING, NO REWARD CHANGE.
#
# Rule 8 scores every scenario as survival x tracking, and rule 7 puts 0.60 of
# the Go2 weight on terrain (G3 0.20, G4 0.15, G5 0.15, G7 0.10).  Under the
# repaired engine, G-A017 (Pilot-01 with track_lin_vel_xy_exp 1.2 -> 1.4, one
# dial, nothing else) is the only stored tuning run that both arms measured on
# one ruler, on a baseline that walks, with no scenario product regression past
# the allowed limit -- +3.707916/70 at tier-1.  G6's product did move against
# it, by -0.006756; the verdict holds at any limit from 0.007 up, so it does
# not rest on the substituted 0.1.  It was killed by the old survival-only clause and so
# never received seeds 202/303 or the 69-case suite; it has a tier-1 absolute
# score (50.199157/70 against Pilot-01's 46.491241/70 on that same 7-case scale)
# but no score on the 69-case worst-case scale that Pilot-01's 33.793106/70
# comes from.  Those two scales must not be compared with each other.
#
# Both policies are frozen and already trained.  This run replays them.
#
# Phases
#   1  full 69-case G1-G7 suite on frozen G-A017, seeds 101/202/303
#   2  full 69-case G1-G7 suite on frozen Pilot-01, same evaluator, same day
#   3  one video per scenario (G1-G7) so the numbers have a witness
#   4  one-file packaging
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-/workspace/go2_a017_full_suite}
TRAIN_ROOT="$PACKAGE_ROOT/candidate"
A017_ROOT="$PACKAGE_ROOT/a017"
PILOT_ROOT="$PACKAGE_ROOT/pilot"
REGISTRY="$PACKAGE_ROOT/go2_self_eval_registry.json"
KEEP=/workspace/_keep/go2_a017_full_suite
RESULT_ZIP=/workspace/_keep/GO2_A017_FULL_SUITE_RESULT.zip
TMUX_NAME=go2_a017_full_suite
SEEDS=(101 202 303)
EVAL_STEPS=${GO2_EVAL_STEPS:-1000}
VIDEO_STEPS=${GO2_VIDEO_STEPS:-500}
RESUME=${GO2_RESUME:-0}

# Every other runner in this campaign reaches Python only through
# /workspace/IsaacLab/isaaclab.sh -p, and this file does the same for play.py
# and for packaging.  The per-case posture check was the one place that called a
# bare python3, and this server has none on PATH, so the run stopped at
# preflight.  Installing one would be a change to the competition environment.
# Resolve an interpreter from what is already here instead -- a system python if
# the machine has one, otherwise the Isaac Lab python that the rest of this
# script already runs through.  Resolved above the --inner branch so both
# invocations of this file agree on it.
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
POSTURE_CHECK="$PACKAGE_ROOT/posture_contract_check.py"
PY=()
if command -v python3 >/dev/null 2>&1; then
  PY=(python3)
elif command -v python >/dev/null 2>&1; then
  PY=(python)
elif [[ -x "$ISAACLAB_SH" ]]; then
  PY=("$ISAACLAB_SH" -p)
fi
A017_EXPECTED_SHA=0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4
PILOT_EXPECTED_SHA=c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d
# All three roles ship a byte-identical evaluator (asserted by the package
# contract test), so one hash identifies the ruler every case was measured with.
EVALUATOR_SHA=$([[ -s "$PACKAGE_ROOT/candidate/go2_eval_telemetry.py" ]] && sha256sum "$PACKAGE_ROOT/candidate/go2_eval_telemetry.py" | awk '{print $1}' || echo UNSET)

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
  /workspace/IsaacLab/isaaclab.sh -p "$PACKAGE_ROOT/package_go2_result.py" "$KEEP" "$RESULT_ZIP"
  sha256sum "$RESULT_ZIP" >"${RESULT_ZIP}.sha256"
  echo "[DOWNLOAD] $RESULT_ZIP"
  echo "[DOWNLOAD] ${RESULT_ZIP}.sha256"
}

if [[ "${1:-}" != "--inner" ]]; then
  [[ "$RESUME" == 0 || "$RESUME" == 1 ]] || { echo '[FAIL] GO2_RESUME must be 0 or 1'; exit 2; }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  [[ ${#PY[@]} -gt 0 ]] || {
    echo '[FAIL] no python interpreter for the posture check: tried python3, python,'
    echo "       and $ISAACLAB_SH -p"; exit 2;
  }
  [[ -s "$POSTURE_CHECK" ]] || { echo "[FAIL] missing $POSTURE_CHECK"; exit 2; }
  [[ -d "$TRAIN_ROOT" && -d "$A017_ROOT" && -d "$PILOT_ROOT" && -s "$REGISTRY" ]] || {
    echo "[FAIL] package must be extracted at $PACKAGE_ROOT"; exit 2;
  }
  (cd "$PACKAGE_ROOT" && sha256sum -c PACKAGE_SHA256SUMS.txt)
  pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py' && {
    echo '[BLOCKED] training/play process is already running'; exit 2;
  } || true
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
    echo "[BLOCKED] tmux session already exists: $TMUX_NAME"; exit 2;
  }
  # A default rerun used to delete the previous run's KEEP tree and result ZIP
  # before doing anything else, so an accidental second launch destroyed results
  # that had not been downloaded yet.  Stop instead, and say what to do.
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
  tmux new-session -d -s "$TMUX_NAME" \
    "cd '$PACKAGE_ROOT' && PACKAGE_ROOT='$PACKAGE_ROOT' GO2_RESUME='$RESUME' bash server_run_go2_a017_full_suite.sh --inner"
  echo "[STARTED] $TMUX_NAME resume=$RESUME"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  # 23 cases x 3 seeds = 69 runs per policy, two policies, plus 7 videos.
  # This is an estimate from prior wall time, not a cap: nothing in this script
  # stops the run when it is exceeded.
  echo "[ESTIMATE] no training; 2 x 69 case-runs + 7 videos ~= 1h45m at the measured 28 s/case"
  echo "[NO_DEADLINE] the script does not enforce a time limit; watch the clock yourself"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] [DONE] GO2_A017_FULL_SUITE_RESULT_READY"
  exit 0
fi

mkdir -p "$KEEP/logs" "$KEEP/training" "$KEEP/training/checkpoints" \
         "$KEEP/evaluation" "$KEEP/ladder" "$KEEP/reports" "$KEEP/meta"
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

(cd "$PACKAGE_ROOT" && sha256sum -c PACKAGE_SHA256SUMS.txt)
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$KEEP/meta/gpu.csv" || true
cp -a "$REGISTRY" "$KEEP/meta/"
sha256sum "$REGISTRY" >"$KEEP/meta/registry.sha256"
# The evaluator is the thing that changed since the last campaign run; pin it.
sha256sum "$A017_ROOT/go2_eval_telemetry.py" >"$KEEP/meta/evaluator.sha256"
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

# A substring test is not a value test.  measurement_contract carries the literal
# string "posture_gate_v2" on every summary, including one whose survival number
# is null because the posture channels were never read -- so the old
# `grep -q posture_gate_v2` passed on exactly the file it existed to reject.
# Check the decided fields, check that the coverage behind them is real, and
# check that the rows that were not observed could not have changed who fell, and
# check that the physics produced finite numbers at all: inf passes every
# threshold test in the gate, so an exploded step read as a perfectly upright robot.
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
  # The fingerprint has to cover everything that can change a summary, or a resume
  # silently banks a case measured under different conditions.  argv alone is not
  # that: set_case also installs DR_MODE, PUSH_X and PUSH_Y, which reach play.py
  # as environment variables and never appear in cmd, and the posture thresholds
  # are env-overridable too.  Two runs differing only in those hashed identically.
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
  # The posture gate is the reason this run exists; refuse to bank a case that
  # silently fell back to the termination-only metric or watched only some envs.
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
  cat >"$out/identity.json" <<IDEOF
{"policy":"$label","model_sha256":"$ACTIVE_MODEL_SHA","env_sha256":"$(sha256sum "$env" | awk '{print $1}')","registry_sha256":"$(sha256sum "$REGISTRY" | awk '{print $1}')","evaluator_sha256":"$(sha256sum go2_eval_telemetry.py | awk '{print $1}')"}
IDEOF
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
  # Existence is not evidence.  A video recorded before the G7 fix shows the same
  # filename and a different run, and the old fingerprint omitted the policy
  # itself -- two different robots hashed the same.
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

SCENARIO_CASE=(G1:forward_fast G2:diagonal_left G3:rough_forward G4:slope_plus_20 G5:stairs_15_up G6:push_pos_x G7:dr_seed_101)

echo '[PHASE 1/4] full 69-case suite on frozen G-A017 candidate under the posture-gated evaluator'
A017_MODEL="$KEEP/policy/a017_model_best.pt"
A017_ENV="$KEEP/policy/a017_env.yaml"
mkdir -p "$KEEP/policy"
if [[ ! -s "$A017_MODEL" || ! -s "$A017_ENV" ]]; then
  cp -a "$A017_ROOT/exported/model_best.pt" "$A017_MODEL"
  cp -a "$A017_ROOT/exported/env.yaml" "$A017_ENV"
fi
run_full_suite a017 "$A017_ROOT" "$A017_MODEL" "$A017_ENV" "$A017_EXPECTED_SHA"

# Pilot-01 is remeasured in full, not refreshed case by case.
#
# The earlier draft of this runner refreshed only G7, on the argument that G7 was
# the one scenario whose definition changed and Pilot-01's other 66 stored cases
# were therefore reusable. That argument is checkable and it does hold for this
# data -- every stored Pilot case carries a live height channel, so requiring both
# posture channels changes none of them, and NCRC_EVAL_DR was provably never set
# in the old environment. But it stays an argument about data measured on another
# day by another engine build, and this campaign has already lost weeks to a
# comparison that rested on an argument instead of a measurement. Remeasuring all
# 69 costs about half an hour and makes both arms same-day, same-engine and
# same-evaluator-SHA, which no reader has to take on trust.
echo '[PHASE 2/4] Pilot-01 full 69-case remeasurement on the same evaluator as the candidate'
PILOT_MODEL="$KEEP/policy/pilot_model_best.pt"
PILOT_ENV="$KEEP/policy/pilot_env.yaml"
mkdir -p "$KEEP/policy"
if [[ ! -s "$PILOT_MODEL" || ! -s "$PILOT_ENV" ]]; then
  cp -a "$PILOT_ROOT/exported/model_best.pt" "$PILOT_MODEL"
  cp -a "$PILOT_ROOT/exported/env.yaml" "$PILOT_ENV"
fi
run_full_suite pilot "$PILOT_ROOT" "$PILOT_MODEL" "$PILOT_ENV" "$PILOT_EXPECTED_SHA"

echo '[PHASE 3/4] one video per scenario'
# A stair or slope score cannot be adjudicated by a number alone: a policy
# parked on a stair-top platform reads as alive and on-command.  Rule 8 asks
# whether the robot finished without falling, so each scenario gets a witness.
for entry in "${SCENARIO_CASE[@]}"; do
  run_video a017 "$A017_ROOT" "$A017_MODEL" "$A017_ENV" \
    "${entry%%:*}" "${entry##*:}" 101
done
[[ "$(find "$KEEP/evaluation/a017/videos" -name '*.mp4' | wc -l)" == 7 ]] || {
  echo '[FAIL] expected 7 videos for a017'; exit 8;
}

echo '[PHASE 4/4] one-file result packaging'
printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nWORK_ID=G-A027\nRUN_ID=eval_260908-Go2_a017_full_suite\nTRAINING=none\nA017_MODEL_SHA=%s\nPILOT_MODEL_SHA=%s\nTELEMETRY_A017=69\nTELEMETRY_PILOT=69\nVIDEOS_A017=7\nEVALUATOR=posture_gate_v2\nEVALUATOR_SHA=%s\nTELEMETRY_SCHEMA=6\nENGINE_VERSION=1.5.4\nVIDEO_STATUS=VIDEO_UNKNOWN\nOFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED\n' \
  "$(date -Is)" "$A017_EXPECTED_SHA" "$PILOT_EXPECTED_SHA" "$EVALUATOR_SHA" >"$KEEP/RUNNER_STATUS.txt"
package_result FULL
trap - EXIT
echo '[DONE] GO2_A017_FULL_SUITE_RESULT_READY'
