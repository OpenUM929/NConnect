#!/usr/bin/env bash
# One upload -> one command -> one result ZIP: Default-01 training + paired G1-G7 eval.
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-/workspace/go2_default_vs_pilot_v1}
DEFAULT_ROOT="$PACKAGE_ROOT/default"
PILOT_ROOT="$PACKAGE_ROOT/pilot"
REGISTRY="$PACKAGE_ROOT/go2_self_eval_registry.json"
KEEP=/workspace/_keep/go2_default_vs_pilot_v1
RESULT_ZIP=/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip
TMUX_NAME=go2_default_vs_pilot_v1
SEEDS=(101 202 303)
EVAL_STEPS=${GO2_EVAL_STEPS:-1000}
VIDEO_STEPS=${GO2_VIDEO_STEPS:-500}
RESUME=${GO2_RESUME:-0}

package_result() {
  local label=$1
  mkdir -p "$KEEP"
  printf 'RESULT_STATE=%s\nPACKAGED_AT=%s\n' "$label" "$(date -Is)" >"$KEEP/RESULT_STATUS.txt"
  (
    cd "$KEEP"
    find . -type f ! -name SHA256SUMS.txt ! -name SHA256SUMS.txt.tmp -print0 \
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
  [[ -d "$DEFAULT_ROOT" && -d "$PILOT_ROOT" && -s "$REGISTRY" ]] || {
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
    "cd '$PACKAGE_ROOT' && PACKAGE_ROOT='$PACKAGE_ROOT' GO2_RESUME='$RESUME' bash server_run_go2_default_vs_pilot_v1.sh --inner"
  echo "[STARTED] $TMUX_NAME resume=$RESUME"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] [DONE] GO2_DEFAULT_VS_PILOT_RESULT_READY"
  exit 0
fi

mkdir -p "$KEEP/logs" "$KEEP/training" "$KEEP/evaluation" "$KEEP/reports" "$KEEP/meta"
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

echo '[PHASE 1/4] Default-01 from-scratch training: seed=42 envs=4096 iterations=1000'
cd "$DEFAULT_ROOT"
if [[ "$RESUME" == 1 && -s "$KEEP/training/model_best.pt" && -s "$KEEP/training/env.yaml" ]] && \
   grep -qx 'TRAIN_RC=0' "$KEEP/training/DEFAULT_TRAIN_STATUS.txt"; then
  echo '[SKIP] verified Default-01 training artifact already present'
else
  rm -rf -- logs exported
  mkdir -p exported
  set +e
  NO_AUTO_SUBMIT=1 /workspace/IsaacLab/isaaclab.sh -p train.py \
    --task Quadruped-v0 --num_envs 4096 --max_iterations 1000 --seed 42 --headless \
    2>&1 | tee "$KEEP/logs/default_training.log"
  TRAIN_RC=${PIPESTATUS[0]}
  set -e
  printf 'TRAIN_RC=%s\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS=1000\n' "$TRAIN_RC" >"$KEEP/training/DEFAULT_TRAIN_STATUS.txt"
  [[ "$TRAIN_RC" == 0 && -s exported/model_best.pt && -s exported/env.yaml ]] || {
    echo '[FAIL] Default-01 training or finalize failed'; exit 3;
  }
  cp -a exported/model_best.pt exported/env.yaml "$KEEP/training/"
fi
mkdir -p "$KEEP/training/source"
cp -a train.py play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
  go2_policy_lineage.py go2_task "$KEEP/training/source/"
find logs -type f \( -name 'events.out.tfevents*' -o -name 'model_*.pt' -o -path '*/params/*' \) \
  -exec cp --parents -a '{}' "$KEEP/training/" \;
sha256sum quadruped_rewards.py train.py play.py go2_task/*.py >"$KEEP/training/default_source.sha256"
diff -u "$PILOT_ROOT/quadruped_rewards.py" "$DEFAULT_ROOT/quadruped_rewards.py" >"$KEEP/training/reward_only.diff" || true

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
  local policy=$1 root=$2 seed=$3 scenario=$4 case_id=$5
  set_case "$case_id"
  local out="$KEEP/evaluation/$policy/cases/seed_${seed}/$case_id"
  mkdir -p "$out" "$KEEP/logs/$policy"
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
    echo "[SKIP] eval $policy $scenario/$case_id seed=$seed"
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
    "${push_env[@]}" "${cmd[@]}" 2>&1 | tee "$KEEP/logs/$policy/seed_${seed}_${case_id}.log"
  local rc=${PIPESTATUS[0]}
  set -e
  [[ "$rc" == 0 && -s "$out/summary.json" ]] && grep -qx 'EVAL_RC=0' "$out/STATUS.txt" || {
    echo "[FAIL] eval $policy $scenario/$case_id seed=$seed rc=$rc"; exit 5;
  }
  printf '%s\n' "$fingerprint" >"$out/case_identity.sha256"
}

run_policy() {
  local policy=$1 root=$2 model=$3 env=$4 expected_sha=$5
  echo "[PHASE 2/4] policy=$policy telemetry"
  cd "$root"
  rm -rf -- exported
  mkdir -p exported "$KEEP/evaluation/$policy"
  cp -a "$model" exported/model_best.pt
  cp -a "$env" exported/env.yaml
  mkdir -p "$KEEP/evaluation/$policy/source"
  cp -a play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
    go2_policy_lineage.py go2_task "$KEEP/evaluation/$policy/source/"
  echo "$expected_sha  exported/model_best.pt" | sha256sum -c -
  ACTIVE_MODEL_SHA=$expected_sha
  cat >"$KEEP/evaluation/$policy/identity.json" <<EOF
{"policy":"$policy","model_sha256":"$expected_sha","env_sha256":"$(sha256sum "$env" | awk '{print $1}')","registry_sha256":"$(sha256sum "$REGISTRY" | awk '{print $1}')"}
EOF
  for seed in "${SEEDS[@]}"; do
    run_eval_case "$policy" "$root" "$seed" G1 forward_slow
    run_eval_case "$policy" "$root" "$seed" G1 forward_nominal
    run_eval_case "$policy" "$root" "$seed" G1 forward_fast
    for case_id in backward left right diagonal_left diagonal_right combined_yaw_left combined_yaw_right; do
      run_eval_case "$policy" "$root" "$seed" G2 "$case_id"
    done
    run_eval_case "$policy" "$root" "$seed" G3 rough_forward
    run_eval_case "$policy" "$root" "$seed" G3 rough_lateral
    run_eval_case "$policy" "$root" "$seed" G4 slope_plus_20
    run_eval_case "$policy" "$root" "$seed" G4 slope_minus_20
    for case_id in stairs_10_up stairs_10_down stairs_15_up stairs_15_down; do
      run_eval_case "$policy" "$root" "$seed" G5 "$case_id"
    done
    for case_id in push_pos_x push_neg_x push_pos_y push_neg_y; do
      run_eval_case "$policy" "$root" "$seed" G6 "$case_id"
    done
    run_eval_case "$policy" "$root" "$seed" G7 "dr_seed_${seed}"
  done
  [[ "$(find "$KEEP/evaluation/$policy/cases" -name summary.json | wc -l)" == 69 ]] || {
    echo "[FAIL] policy=$policy telemetry count is not 69"; exit 6;
  }
  if [[ -s exported/policy.pt ]]; then
    cp -a exported/policy.pt "$KEEP/evaluation/$policy/policy.pt"
  fi
  [[ -s "$KEEP/evaluation/$policy/policy.pt" ]] || { echo "[FAIL] policy export missing for $policy"; exit 6; }
  /workspace/IsaacLab/isaaclab.sh -p go2_policy_lineage.py \
    "$model" "$KEEP/evaluation/$policy/policy.pt" "$KEEP/evaluation/$policy/POLICY_LINEAGE.json"
}

DEFAULT_MODEL="$KEEP/training/model_best.pt"
DEFAULT_ENV="$KEEP/training/env.yaml"
DEFAULT_SHA=$(sha256sum "$DEFAULT_MODEL" | awk '{print $1}')
PILOT_MODEL="$KEEP/training/pilot_model_best.pt"
PILOT_ENV="$KEEP/training/pilot_env.yaml"
if [[ ! -s "$PILOT_MODEL" || ! -s "$PILOT_ENV" ]]; then
  cp -a "$PILOT_ROOT/exported/model_best.pt" "$PILOT_MODEL"
  cp -a "$PILOT_ROOT/exported/env.yaml" "$PILOT_ENV"
fi
PILOT_SHA=$(sha256sum "$PILOT_MODEL" | awk '{print $1}')
[[ "$PILOT_SHA" == c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d ]] || {
  echo '[FAIL] frozen Pilot-01 SHA mismatch'; exit 7;
}

run_policy default "$DEFAULT_ROOT" "$DEFAULT_MODEL" "$DEFAULT_ENV" "$DEFAULT_SHA"
run_policy pilot "$PILOT_ROOT" "$PILOT_MODEL" "$PILOT_ENV" "$PILOT_SHA"

echo '[PHASE 3/4] reports and worst-case videos'
/workspace/IsaacLab/isaaclab.sh -p "$PACKAGE_ROOT/go2_fixed_eval_report.py" \
  --registry "$REGISTRY" --default-root "$KEEP/evaluation/default" \
  --pilot-root "$KEEP/evaluation/pilot" --out "$KEEP/reports"

run_video() {
  local policy=$1 root=$2 model=$3 env=$4 scenario=$5 case_id=$6 seed=$7
  set_case "$case_id"
  local video="$KEEP/evaluation/$policy/videos/${scenario}_${case_id}_seed_${seed}.mp4"
  if [[ "$RESUME" == 1 && -s "$video" ]]; then
    echo "[SKIP] video $policy $scenario/$case_id seed=$seed"
    return 0
  fi
  cd "$root"
  rm -rf -- exported
  mkdir -p exported "$KEEP/evaluation/$policy/videos"
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
    2>&1 | tee "$KEEP/logs/$policy/video_${scenario}_${case_id}_seed_${seed}.log"
  [[ -s exported/play_video.mp4 ]] || { echo "[FAIL] video missing: $policy $scenario"; exit 8; }
  cp -a exported/play_video.mp4 "$video"
}

for policy in default pilot; do
  if [[ "$policy" == default ]]; then root=$DEFAULT_ROOT; model=$DEFAULT_MODEL; env=$DEFAULT_ENV; else root=$PILOT_ROOT; model=$PILOT_MODEL; env=$PILOT_ENV; fi
  while IFS=$'\t' read -r scenario case_id seed; do
    [[ "$scenario" == scenario ]] && continue
    run_video "$policy" "$root" "$model" "$env" "$scenario" "$case_id" "$seed"
  done <"$KEEP/evaluation/$policy/WORST_CASES.tsv"
  [[ "$(find "$KEEP/evaluation/$policy/videos" -name '*.mp4' | wc -l)" == 7 ]] || {
    echo "[FAIL] expected 7 worst-case videos for $policy"; exit 8;
  }
done

echo '[PHASE 4/4] one-file result packaging'
printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nDEFAULT_MODEL_SHA=%s\nPILOT_MODEL_SHA=%s\nTELEMETRY_PER_POLICY=69\nVIDEOS_PER_POLICY=7\nVIDEO_STATUS=VIDEO_UNKNOWN\n' \
  "$(date -Is)" "$DEFAULT_SHA" "$PILOT_SHA" >"$KEEP/RUNNER_STATUS.txt"
package_result FULL
trap - EXIT
echo '[DONE] GO2_DEFAULT_VS_PILOT_RESULT_READY'
