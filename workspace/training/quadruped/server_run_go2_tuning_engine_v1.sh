#!/usr/bin/env bash
# Fixed engine: validated experiment JSON -> training -> gated evaluation -> one result ZIP.
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-/workspace/go2_tuning_engine_v1_3}
if [[ "${1:-}" == "--inner" ]]; then
  EXPERIMENT_PATH=${EXPERIMENT_PATH:-/workspace/experiment.json}
else
  EXPERIMENT_PATH=${1:-/workspace/experiment.json}
fi
ISAACLAB=${ISAACLAB:-/workspace/IsaacLab/isaaclab.sh}
ENGINE_ZIP_PATH=${GO2_ENGINE_ZIP_PATH:-/workspace/go2_tuning_engine_v1_3.zip}
RESUME=${GO2_RESUME:-0}
[[ -x "$ISAACLAB" && -s "$PACKAGE_ROOT/go2_tuning_config.py" && -s "$EXPERIMENT_PATH" ]] || {
  echo "[FAIL] missing engine config or experiment: $PACKAGE_ROOT $EXPERIMENT_PATH"; exit 2;
}
ENV_FILE=$(mktemp /tmp/go2_tuning_env.XXXXXX)
"$ISAACLAB" -p "$PACKAGE_ROOT/go2_tuning_config.py" shell-env \
  --experiment "$EXPERIMENT_PATH" --out "$ENV_FILE"
source "$ENV_FILE"
rm -f -- "$ENV_FILE"
KEEP="/workspace/_keep/$KEEP_DIR_NAME"
RESULT_ZIP="/workspace/_keep/$RESULT_ZIP_NAME"
RUNTIME_ROOT="/workspace/_go2_tuning_runtime/$EXPERIMENT_SLUG"
CANDIDATE_ROOT="$RUNTIME_ROOT/candidate"
DEFAULT_ROOT="$RUNTIME_ROOT/default"
TIER1_REGISTRY="$RUNTIME_ROOT/tier1_registry.json"
REP_REGISTRY="$RUNTIME_ROOT/representative_registry.json"

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
  [[ -d "$PACKAGE_ROOT/source_template" && -d "$PACKAGE_ROOT/baseline" && -s "$PACKAGE_ROOT/config/go2_tuning_experiment_schema.json" ]] || {
    echo "[FAIL] engine must be extracted at $PACKAGE_ROOT"; exit 2;
  }
  "$ISAACLAB" -p "$PACKAGE_ROOT/go2_tuning_config.py" validate --experiment "$EXPERIMENT_PATH"
  (cd "$PACKAGE_ROOT" && sha256sum -c PACKAGE_SHA256SUMS.txt)
  pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py' && {
    echo '[BLOCKED] training/play process is already running'; exit 2;
  } || true
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
    echo "[BLOCKED] tmux session already exists: $TMUX_NAME"; exit 2;
  }
  if [[ "$RESUME" == 0 ]]; then
    rm -rf -- "$KEEP" "$RESULT_ZIP" "${RESULT_ZIP}.sha256"
  fi
  printf -v INNER_COMMAND "cd %q && PACKAGE_ROOT=%q EXPERIMENT_PATH=%q GO2_RESUME=%q ISAACLAB=%q GO2_ENGINE_ZIP_PATH=%q bash server_run_go2_tuning_engine_v1.sh --inner" \
    "$PACKAGE_ROOT" "$PACKAGE_ROOT" "$EXPERIMENT_PATH" "$RESUME" "$ISAACLAB" "$ENGINE_ZIP_PATH"
  tmux new-session -d -s "$TMUX_NAME" "$INNER_COMMAND"
  echo "[STARTED] $TMUX_NAME resume=$RESUME"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] $DONE_MARKER"
  exit 0
fi

mkdir -p "$KEEP/logs" "$KEEP/training" "$KEEP/evaluation" "$KEEP/reports" "$KEEP/meta"
exec > >(tee -a "$KEEP/launcher.log") 2>&1
"$ISAACLAB" -p "$PACKAGE_ROOT/go2_tuning_config.py" materialize \
  --engine-root "$PACKAGE_ROOT" --experiment "$EXPERIMENT_PATH" --runtime-root "$RUNTIME_ROOT"
ENGINE_ARCHIVE_SHA256=UNAVAILABLE
[[ -s "$ENGINE_ZIP_PATH" ]] && ENGINE_ARCHIVE_SHA256=$(sha256sum "$ENGINE_ZIP_PATH" | awk '{print $1}')
ENGINE_MANIFEST_SHA256=$(sha256sum "$PACKAGE_ROOT/PACKAGE_SHA256SUMS.txt" | awk '{print $1}')
cp -a "$EXPERIMENT_PATH" "$PACKAGE_ROOT/config/go2_tuning_experiment_schema.json" "$PACKAGE_ROOT/ENGINE_METADATA.json" "$KEEP/meta/"
printf 'ENGINE_VERSION=%s\nENGINE_ARCHIVE_SHA256=%s\nENGINE_MANIFEST_SHA256=%s\nEXPERIMENT_SHA256=%s\n' \
  "$ENGINE_VERSION" "$ENGINE_ARCHIVE_SHA256" "$ENGINE_MANIFEST_SHA256" "$EXPERIMENT_SHA256" >"$KEEP/meta/ENGINE_EXPERIMENT_IDENTITY.txt"
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
cp -a "$TIER1_REGISTRY" "$REP_REGISTRY" "$KEEP/meta/"

echo "[PHASE 1/4] $WORK_ID single-variable training: $SINGLE_CHANGE_NAME $SINGLE_CHANGE_FROM->$SINGLE_CHANGE_TO seed=$TRAIN_SEED envs=$NUM_ENVS iterations=$MAX_ITERATIONS"
cd "$CANDIDATE_ROOT"
if [[ "$RESUME" == 1 && -s "$KEEP/training/model_best.pt" && -s "$KEEP/training/env.yaml" ]] && \
   grep -qx 'TRAIN_RC=0' "$KEEP/training/TRAIN_STATUS.txt"; then
  echo '[SKIP] candidate training artifact already present'
else
  rm -rf -- logs exported
  mkdir -p exported
  set +e
  NO_AUTO_SUBMIT=1 /workspace/IsaacLab/isaaclab.sh -p train.py \
    --task Quadruped-v0 --num_envs "$NUM_ENVS" --max_iterations "$MAX_ITERATIONS" --seed "$TRAIN_SEED" --headless \
    2>&1 | tee "$KEEP/logs/candidate_training.log"
  TRAIN_RC=${PIPESTATUS[0]}
  set -e
  printf 'TRAIN_RC=%s
SEED=%s
NUM_ENVS=%s
MAX_ITERATIONS=%s
SINGLE_CHANGE=%s:%s->%s
EXPERIMENT_SHA256=%s
' \
    "$TRAIN_RC" "$TRAIN_SEED" "$NUM_ENVS" "$MAX_ITERATIONS" "$SINGLE_CHANGE_NAME" "$SINGLE_CHANGE_FROM" "$SINGLE_CHANGE_TO" "$EXPERIMENT_SHA256" >"$KEEP/training/TRAIN_STATUS.txt"
  [[ "$TRAIN_RC" == 0 && -s exported/model_best.pt && -s exported/env.yaml ]] || {
    echo '[FAIL] candidate training or finalize failed'; exit 3;
  }
  cp -a exported/model_best.pt exported/env.yaml "$KEEP/training/"
fi
mkdir -p "$KEEP/training/source"
cp -a train.py play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
  go2_policy_lineage.py go2_task "$KEEP/training/source/"
if [[ -d logs ]]; then
  find logs -type f \( -name 'events.out.tfevents*' -o -name 'model_*.pt' -o -path '*/params/*' \) \
    -exec cp --parents -a '{}' "$KEEP/training/" \;
fi
sha256sum quadruped_rewards.py train.py play.py go2_task/*.py >"$KEEP/training/candidate_source.sha256"
diff -u "$DEFAULT_ROOT/quadruped_rewards.py" quadruped_rewards.py >"$KEEP/training/reward_only.diff" || true

CANDIDATE_MODEL="$KEEP/training/model_best.pt"
CANDIDATE_ENV="$KEEP/training/env.yaml"
CANDIDATE_SHA=$(sha256sum "$CANDIDATE_MODEL" | awk '{print $1}')
DEFAULT_MODEL="$DEFAULT_ROOT/model_best.pt"
DEFAULT_ENV="$DEFAULT_ROOT/env.yaml"
DEFAULT_SHA=$(sha256sum "$DEFAULT_MODEL" | awk '{print $1}')

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
  VX=0 VY=0 WZ=0 PUSH_X= PUSH_Y= DR_MODE=0
  TERRAIN_ARGS=("${PLANE[@]}")
  case "$case_id" in
    forward_fast) VX=1.20 ;;
    diagonal_left) VX=0.50; VY=0.30 ;;
    rough_forward)
      VX=0.50
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]')
      ;;
    slope_plus_20)
      VX=0.50
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.slope_range=[0.36397023,0.36397023]')
      ;;
    stairs_15_up)
      VX=0.50
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.step_height_range=[0.15,0.15]')
      ;;
    push_pos_x) PUSH_X=0.50 ;;
    dr_seed_*)
      VX=0.50; DR_MODE=1
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]')
      ;;
    *) echo "[FAIL] unknown representative case: $case_id"; exit 4 ;;
  esac
}

run_eval_case() {
  local label=$1 root=$2 model=$3 env_yaml=$4 policy_sha=$5 out_root=$6 seed=$7 scenario=$8 case_id=$9
  set_case "$case_id"
  local out="$out_root/cases/seed_${seed}/$case_id"
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
  local fingerprint
  fingerprint=$(
    { printf '%s\0%s\0%s\0%s\0%s\0' "$policy_sha" "$scenario" "$case_id" "$seed" "$DR_MODE"; printf '%s\0' "${cmd[@]}"; } \
      | sha256sum | awk '{print $1}'
  )
  if [[ "$RESUME" == 1 && -s "$out/summary.json" && -s "$out/STATUS.txt" && -s "$out/case_identity.sha256" ]] && \
     grep -qx 'EVAL_RC=0' "$out/STATUS.txt" && grep -qx "$fingerprint" "$out/case_identity.sha256"; then
    echo "[SKIP] eval $label $scenario/$case_id seed=$seed"
    return 0
  fi
  local -a run_env=(env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y -u NCRC_EVAL_DR)
  [[ -n "$PUSH_X" ]] && run_env+=("NCRC_PLAY_PUSH_X=$PUSH_X")
  [[ -n "$PUSH_Y" ]] && run_env+=("NCRC_PLAY_PUSH_Y=$PUSH_Y")
  [[ "$DR_MODE" == 1 ]] && run_env+=("NCRC_EVAL_DR=1")
  local attempt rc log
  for ((attempt=1; attempt<=CASE_ATTEMPTS; attempt++)); do
    rm -rf -- "$out" "$root/exported"
    mkdir -p "$out" "$root/exported"
    cp -a "$model" "$root/exported/model_best.pt"
    cp -a "$env_yaml" "$root/exported/env.yaml"
    log="$KEEP/logs/$label/seed_${seed}_${case_id}.attempt_${attempt}.log"
    set +e
    (cd "$root" && NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$EVAL_STEPS" \
      NCRC_EVAL_CASE="$case_id" NCRC_EVAL_SCENARIO="$scenario" NCRC_EVAL_SEED="$seed" \
      "${run_env[@]}" "${cmd[@]}") 2>&1 | tee "$log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ "$rc" == 0 && -s "$out/summary.json" && -s "$out/STATUS.txt" ]] && grep -qx 'EVAL_RC=0' "$out/STATUS.txt"; then
      cp -a "$log" "$KEEP/logs/$label/seed_${seed}_${case_id}.log"
      printf '%s\n' "$fingerprint" >"$out/case_identity.sha256"
      return 0
    fi
    echo "[RETRY] eval $label $scenario/$case_id seed=$seed rc=$rc attempt=$attempt/$CASE_ATTEMPTS"
    [[ "$attempt" == "$CASE_ATTEMPTS" ]] || sleep $((CASE_RETRY_DELAY * attempt))
  done
  echo "[FAIL] eval $label $scenario/$case_id seed=$seed after $CASE_ATTEMPTS attempts"
  return 5
}

run_candidate_representatives() {
  local seed=$1
  run_eval_case candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$KEEP/evaluation/candidate" "$seed" G1 forward_fast
  run_eval_case candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$KEEP/evaluation/candidate" "$seed" G2 diagonal_left
  run_eval_case candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$KEEP/evaluation/candidate" "$seed" G3 rough_forward
  run_eval_case candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$KEEP/evaluation/candidate" "$seed" G4 slope_plus_20
  run_eval_case candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$KEEP/evaluation/candidate" "$seed" G5 stairs_15_up
  run_eval_case candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$KEEP/evaluation/candidate" "$seed" G6 push_pos_x
  run_eval_case candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "$CANDIDATE_SHA" "$KEEP/evaluation/candidate" "$seed" G7 "dr_seed_${seed}"
}

run_target_video() {
  local video="$KEEP/evaluation/candidate/videos/G1_forward_fast_seed_101.mp4"
  [[ "$RESUME" == 1 && -s "$video" ]] && { echo '[SKIP] target video'; return 0; }
  set_case forward_fast
  mkdir -p "$KEEP/evaluation/candidate/videos"
  local -a cmd=(
    /workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs "$VIDEO_NUM_ENVS"
    --headless --video --video_length "$VIDEO_STEPS" --enable_cameras
    "agent.seed=${VIDEO_SEED}" 'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$VX,$VX]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$VY,$VY]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$WZ,$WZ]" "${TERRAIN_ARGS[@]}"
  )
  local attempt rc
  for ((attempt=1; attempt<=CASE_ATTEMPTS; attempt++)); do
    rm -rf -- "$CANDIDATE_ROOT/exported"
    mkdir -p "$CANDIDATE_ROOT/exported"
    cp -a "$CANDIDATE_MODEL" "$CANDIDATE_ROOT/exported/model_best.pt"
    cp -a "$CANDIDATE_ENV" "$CANDIDATE_ROOT/exported/env.yaml"
    set +e
    (cd "$CANDIDATE_ROOT" && "${cmd[@]}") 2>&1 | tee "$KEEP/logs/candidate/video_G1_forward_fast_seed_101.attempt_${attempt}.log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ "$rc" == 0 && -s "$CANDIDATE_ROOT/exported/play_video.mp4" ]]; then
      cp -a "$CANDIDATE_ROOT/exported/play_video.mp4" "$video"
      return 0
    fi
    [[ "$attempt" == "$CASE_ATTEMPTS" ]] || sleep $((CASE_RETRY_DELAY * attempt))
  done
  return 8
}

finish_full() {
  local decision=$1 candidate_cases=$2
  mkdir -p "$KEEP/evaluation/candidate/source"
  cp -a "$CANDIDATE_ROOT"/play.py "$CANDIDATE_ROOT"/quadruped_rewards.py "$CANDIDATE_ROOT"/pyproject.toml \
    "$CANDIDATE_ROOT"/go2_eval_telemetry.py "$CANDIDATE_ROOT"/go2_policy_lineage.py "$CANDIDATE_ROOT"/go2_task \
    "$KEEP/evaluation/candidate/source/"
  if [[ -s "$CANDIDATE_ROOT/exported/policy.pt" ]]; then
    cp -a "$CANDIDATE_ROOT/exported/policy.pt" "$KEEP/evaluation/candidate/policy.pt"
  fi
  [[ -s "$KEEP/evaluation/candidate/policy.pt" ]] || { echo '[FAIL] candidate policy export missing'; exit 6; }
  /workspace/IsaacLab/isaaclab.sh -p "$CANDIDATE_ROOT/go2_policy_lineage.py" \
    "$CANDIDATE_MODEL" "$KEEP/evaluation/candidate/policy.pt" "$KEEP/evaluation/candidate/POLICY_LINEAGE.json"
  printf 'RUNNER_RC=0
COMPLETED_AT=%s
WORK_ID=%s
RUN_ID=%s
DECISION=%s
CANDIDATE_MODEL_SHA=%s
TELEMETRY_CANDIDATE=%s
TELEMETRY_BASELINE=7
VIDEOS_CANDIDATE=1
VIDEO_STATUS=VIDEO_UNKNOWN
ENGINE_VERSION=%s
ENGINE_ARCHIVE_SHA256=%s
EXPERIMENT_SHA256=%s
OFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED
' \
    "$(date -Is)" "$WORK_ID" "$RUN_ID" "$decision" "$CANDIDATE_SHA" "$candidate_cases" "$ENGINE_VERSION" "$ENGINE_ARCHIVE_SHA256" "$EXPERIMENT_SHA256" >"$KEEP/RUNNER_STATUS.txt"
  package_result FULL
  trap - EXIT
  echo "$DONE_MARKER"
  exit 0
}

echo '[PHASE 2/4] tier-1 early kill: 7 candidate cases + 1 repaired-DR baseline case'
mkdir -p "$KEEP/evaluation/baseline_tier1" "$KEEP/evaluation/candidate"
cp -a "$RUNTIME_ROOT/baseline_seed/." "$KEEP/evaluation/baseline_tier1/"
cat >"$KEEP/evaluation/baseline_tier1/identity.json" <<EOF
{"policy":"default","model_sha256":"$DEFAULT_SHA","training_seed":$TRAIN_SEED,"evaluator":"repaired_v2"}
EOF
cat >"$KEEP/evaluation/candidate/identity.json" <<EOF
{"policy":"$EXPERIMENT_SLUG","model_sha256":"$CANDIDATE_SHA","env_sha256":"$(sha256sum "$CANDIDATE_ENV" | awk '{print $1}')","training_seed":$TRAIN_SEED,"evaluator":"repaired_v2"}
EOF
run_candidate_representatives 101
run_eval_case baseline "$DEFAULT_ROOT" "$DEFAULT_MODEL" "$DEFAULT_ENV" "$DEFAULT_SHA" \
  "$KEEP/evaluation/baseline_tier1" 101 G7 dr_seed_101
run_target_video
/workspace/IsaacLab/isaaclab.sh -p "$PACKAGE_ROOT/go2_tuning_eval_report.py" \
  --mode tier1 --experiment "$EXPERIMENT_PATH" --registry "$TIER1_REGISTRY" \
  --baseline-root "$KEEP/evaluation/baseline_tier1" \
  --candidate-root "$KEEP/evaluation/candidate" --out "$KEEP/reports"
TIER1_STATUS=$(sed -n 's/^[[:space:]]*"status": "\([^"]*\)".*/\1/p' \
  "$KEEP/reports/TIER1_DECISION.json" | head -n 1)
if [[ "$TIER1_STATUS" != INTERNAL_EARLY_KILL_PASS ]]; then
  echo "[EARLY STOP] $TIER1_STATUS"
  finish_full "$TIER1_STATUS" 7
fi

echo '[PHASE 3/4] representative evaluation: add seeds 202 and 303 (21 candidate cases total)'
run_candidate_representatives 202
run_candidate_representatives 303
/workspace/IsaacLab/isaaclab.sh -p "$PACKAGE_ROOT/go2_tuning_eval_report.py" \
  --mode representative --experiment "$EXPERIMENT_PATH" --registry "$REP_REGISTRY" \
  --candidate-root "$KEEP/evaluation/candidate" --out "$KEEP/reports"
REP_STATUS=$(sed -n 's/^[[:space:]]*"status": "\([^"]*\)".*/\1/p' \
  "$KEEP/reports/REPRESENTATIVE_DECISION.json" | head -n 1)

echo '[PHASE 4/4] result packaging'
finish_full "$REP_STATUS" 21
