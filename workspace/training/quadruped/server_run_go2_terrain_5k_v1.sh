#!/usr/bin/env bash
# One upload -> one command -> one result ZIP.
#
# G-A011 "terrain curriculum": the single controlled variable against the frozen
# Pilot-01 baseline is TRAINING LENGTH.  Reward weights are byte-identical to
# Pilot-01, so anything that moves is attributable to iterations alone.
#
# Phases
#   1  train Pilot rewards from scratch, seed 42, 4096 envs, 5000 iterations
#      (a background snapshotter preserves model_1000/2000/3000/4000.pt, which
#       the trainer's finalizer would otherwise prune)
#   2  tier-1 ladder: 7 representative cases at each preserved checkpoint,
#      giving an iterations -> score curve at no extra training cost
#   3  full 69-case G1-G7 suite on the final policy, seeds 101/202/303
#   4  full 69-case suite on frozen Pilot-01 under the SAME v2 evaluator --
#      this is the v2 baseline the campaign currently does not have
#   5  worst-case videos
#   6  one-file packaging
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-/workspace/go2_terrain_5k_v1}
TRAIN_ROOT="$PACKAGE_ROOT/candidate"
PILOT_ROOT="$PACKAGE_ROOT/pilot"
REGISTRY="$PACKAGE_ROOT/go2_self_eval_registry.json"
KEEP=/workspace/_keep/go2_terrain_5k_v1
RESULT_ZIP=/workspace/_keep/GO2_TERRAIN_5K_RESULT.zip
TMUX_NAME=go2_terrain_5k_v1
SEEDS=(101 202 303)
LADDER=(1000 2000 3000 4000)
MAX_ITERATIONS=${GO2_MAX_ITERATIONS:-5000}
EVAL_STEPS=${GO2_EVAL_STEPS:-1000}
VIDEO_STEPS=${GO2_VIDEO_STEPS:-500}
RESUME=${GO2_RESUME:-0}
PILOT_EXPECTED_SHA=c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d

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
  [[ -d "$TRAIN_ROOT" && -d "$PILOT_ROOT" && -s "$REGISTRY" ]] || {
    echo "[FAIL] package must be extracted at $PACKAGE_ROOT"; exit 2;
  }
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
  tmux new-session -d -s "$TMUX_NAME" \
    "cd '$PACKAGE_ROOT' && PACKAGE_ROOT='$PACKAGE_ROOT' GO2_RESUME='$RESUME' GO2_MAX_ITERATIONS='$MAX_ITERATIONS' bash server_run_go2_terrain_5k_v1.sh --inner"
  echo "[STARTED] $TMUX_NAME resume=$RESUME iterations=$MAX_ITERATIONS"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[ESTIMATE] training ~5h20m + evaluation ~1h20m at the measured 3.86 s/iter"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] [DONE] GO2_TERRAIN_5K_RESULT_READY"
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
sha256sum "$TRAIN_ROOT/go2_eval_telemetry.py" >"$KEEP/meta/evaluator.sha256"

echo "[PHASE 1/6] from-scratch training: Pilot rewards, seed=42, envs=4096, iterations=$MAX_ITERATIONS"
cd "$TRAIN_ROOT"
if [[ "$RESUME" == 1 && -s "$KEEP/training/model_best.pt" && -s "$KEEP/training/env.yaml" ]] && \
   grep -qx 'TRAIN_RC=0' "$KEEP/training/TRAIN_STATUS.txt" 2>/dev/null; then
  echo '[SKIP] verified training artifact already present'
else
  rm -rf -- logs exported
  mkdir -p exported
  # The trainer's finalizer prunes intermediate .pt files once training ends, so
  # the ladder checkpoints must be copied out while training is still running.
  ( while sleep 60; do
      for iter in "${LADDER[@]}"; do
        [[ -s "$KEEP/training/checkpoints/model_${iter}.pt" ]] && continue
        src=$(find logs -type f -name "model_${iter}.pt" 2>/dev/null | head -1)
        [[ -n "$src" ]] || continue
        cp -a "$src" "$KEEP/training/checkpoints/model_${iter}.pt.tmp" 2>/dev/null || continue
        mv "$KEEP/training/checkpoints/model_${iter}.pt.tmp" \
           "$KEEP/training/checkpoints/model_${iter}.pt"
        echo "[SNAPSHOT] model_${iter}.pt preserved"
      done
    done ) &
  SNAPSHOT_PID=$!
  set +e
  NO_AUTO_SUBMIT=1 /workspace/IsaacLab/isaaclab.sh -p train.py \
    --task Quadruped-v0 --num_envs 4096 --max_iterations "$MAX_ITERATIONS" --seed 42 --headless \
    2>&1 | tee "$KEEP/logs/candidate_training.log"
  TRAIN_RC=${PIPESTATUS[0]}
  set -e
  kill "$SNAPSHOT_PID" 2>/dev/null || true
  wait "$SNAPSHOT_PID" 2>/dev/null || true
  printf 'TRAIN_RC=%s\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS=%s\n' \
    "$TRAIN_RC" "$MAX_ITERATIONS" >"$KEEP/training/TRAIN_STATUS.txt"
  [[ "$TRAIN_RC" == 0 && -s exported/model_best.pt && -s exported/env.yaml ]] || {
    echo '[FAIL] training or finalize failed'; exit 3;
  }
  cp -a exported/model_best.pt exported/env.yaml "$KEEP/training/"
fi
mkdir -p "$KEEP/training/source"
cp -a train.py play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
  go2_policy_lineage.py go2_task "$KEEP/training/source/"
find logs -type f \( -name 'events.out.tfevents*' -o -name 'model_*.pt' -o -path '*/params/*' \) \
  -exec cp --parents -a '{}' "$KEEP/training/" \;
sha256sum quadruped_rewards.py train.py play.py go2_task/*.py >"$KEEP/training/candidate_source.sha256"
# Reward parity with Pilot-01 is the whole premise of this run: prove it, do not assert it.
if ! diff -u "$PILOT_ROOT/quadruped_rewards.py" "$TRAIN_ROOT/quadruped_rewards.py" \
     >"$KEEP/training/reward_parity.diff"; then
  echo '[FAIL] candidate rewards differ from Pilot-01; training length is no longer the only variable'
  exit 3
fi
echo 'REWARD_PARITY=IDENTICAL_TO_PILOT_01' >"$KEEP/training/REWARD_PARITY.txt"

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
  VX=0 VY=0 WZ=0 PUSH_X= PUSH_Y= TERRAIN_LABEL=plane
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
    rough_forward|rough_lateral|dr_seed_*)
      [[ "$case_id" == rough_lateral ]] && VY=0.30 || VX=0.50
      TERRAIN_LABEL=rough
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
  local fingerprint
  fingerprint=$(
    { printf '%s\0%s\0%s\0%s\0' "$ACTIVE_MODEL_SHA" "$scenario" "$case_id" "$seed"; printf '%s\0' "${cmd[@]}"; } \
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
  local -a push_env=(env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y)
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
  # silently fell back to the termination-only metric.
  grep -q 'posture_gate_v2' "$out/summary.json" || {
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
}

TIER1=(G1:forward_fast G2:diagonal_left G3:rough_forward G4:slope_plus_20 G5:stairs_15_up G6:push_pos_x G7:dr_seed_101)

echo '[PHASE 2/6] tier-1 ladder over preserved checkpoints (iterations -> score curve)'
CAND_ENV="$KEEP/training/env.yaml"
for iter in "${LADDER[@]}"; do
  ckpt="$KEEP/training/checkpoints/model_${iter}.pt"
  if [[ ! -s "$ckpt" ]]; then
    echo "[WARN] checkpoint model_${iter}.pt was not preserved; ladder point skipped"
    continue
  fi
  stage_policy "$TRAIN_ROOT" "$ckpt" "$CAND_ENV"
  out="$KEEP/ladder/iter_${iter}"
  mkdir -p "$out"
  printf '{"iteration":%s,"model_sha256":"%s"}\n' "$iter" "$ACTIVE_MODEL_SHA" >"$out/identity.json"
  for entry in "${TIER1[@]}"; do
    run_eval_case "ladder_${iter}" "$TRAIN_ROOT" 101 "${entry%%:*}" "${entry##*:}" "$out"
  done
done

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

echo '[PHASE 3/6] full 69-case suite on the 5k policy'
run_full_suite terrain5k "$TRAIN_ROOT" "$KEEP/training/model_best.pt" "$CAND_ENV" ""

echo '[PHASE 4/6] full 69-case suite on frozen Pilot-01 under the same v2 evaluator'
PILOT_MODEL="$KEEP/training/pilot_model_best.pt"
PILOT_ENV="$KEEP/training/pilot_env.yaml"
if [[ ! -s "$PILOT_MODEL" || ! -s "$PILOT_ENV" ]]; then
  cp -a "$PILOT_ROOT/exported/model_best.pt" "$PILOT_MODEL"
  cp -a "$PILOT_ROOT/exported/env.yaml" "$PILOT_ENV"
fi
run_full_suite pilot_v2 "$PILOT_ROOT" "$PILOT_MODEL" "$PILOT_ENV" "$PILOT_EXPECTED_SHA"

echo '[PHASE 5/6] worst-case videos'
run_video() {
  local label=$1 root=$2 model=$3 env=$4 scenario=$5 case_id=$6 seed=$7
  set_case "$case_id"
  local video="$KEEP/evaluation/$label/videos/${scenario}_${case_id}_seed_${seed}.mp4"
  if [[ "$RESUME" == 1 && -s "$video" ]]; then
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
  local -a push_env=(env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y)
  [[ -n "$PUSH_X" ]] && push_env+=("NCRC_PLAY_PUSH_X=$PUSH_X")
  [[ -n "$PUSH_Y" ]] && push_env+=("NCRC_PLAY_PUSH_Y=$PUSH_Y")
  "${push_env[@]}" "${cmd[@]}" \
    2>&1 | tee "$KEEP/logs/$label/video_${scenario}_${case_id}_seed_${seed}.log"
  [[ -s exported/play_video.mp4 ]] || { echo "[FAIL] video missing: $label $scenario"; exit 8; }
  cp -a exported/play_video.mp4 "$video"
}

# One video per scenario on the new policy: the terrain scenarios are the ones
# this run is trying to move, and they are exactly the ones a number alone
# cannot adjudicate (a policy parked on a stair top platform scores as alive).
for entry in "${TIER1[@]}"; do
  run_video terrain5k "$TRAIN_ROOT" "$KEEP/training/model_best.pt" "$CAND_ENV" \
    "${entry%%:*}" "${entry##*:}" 101
done
[[ "$(find "$KEEP/evaluation/terrain5k/videos" -name '*.mp4' | wc -l)" == 7 ]] || {
  echo '[FAIL] expected 7 videos for terrain5k'; exit 8;
}

echo '[PHASE 6/6] one-file result packaging'
CAND_SHA=$(sha256sum "$KEEP/training/model_best.pt" | awk '{print $1}')
LADDER_POINTS=$(find "$KEEP/ladder" -name summary.json | wc -l)
printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nWORK_ID=G-A011\nRUN_ID=train_260903-Go2_terrain_5k\nMAX_ITERATIONS=%s\nCANDIDATE_MODEL_SHA=%s\nPILOT_MODEL_SHA=%s\nTELEMETRY_CANDIDATE=69\nTELEMETRY_PILOT_V2=69\nLADDER_CASES=%s\nVIDEOS_CANDIDATE=7\nEVALUATOR=posture_gate_v2\nVIDEO_STATUS=VIDEO_UNKNOWN\nOFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED\n' \
  "$(date -Is)" "$MAX_ITERATIONS" "$CAND_SHA" "$PILOT_EXPECTED_SHA" "$LADDER_POINTS" >"$KEEP/RUNNER_STATUS.txt"
package_result FULL
trap - EXIT
echo '[DONE] GO2_TERRAIN_5K_RESULT_READY'
