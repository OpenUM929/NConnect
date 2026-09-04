#!/usr/bin/env bash
# One upload -> one command -> one result ZIP: feet_air_time=0.20-only training and G1-G7 screening.
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-/workspace/go2_feet_air_time_020_v1}
CANDIDATE_ROOT="$PACKAGE_ROOT/candidate"
REGISTRY="$PACKAGE_ROOT/go2_self_eval_registry.json"
BASELINE_REPORT="$PACKAGE_ROOT/baseline_DEFAULT_SELF_EVAL_REPORT.json"
KEEP=/workspace/_keep/go2_feet_air_time_020_v1
RESULT_ZIP=/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip
TMUX_NAME=go2_feet_air_time_020_v1
BASELINE_MODEL_SHA=99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676
EXPECTED_CANDIDATE_SHA=0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5
SEEDS=(101 202 303)
EVAL_STEPS=${GO2_EVAL_STEPS:-1000}
VIDEO_STEPS=${GO2_VIDEO_STEPS:-500}
RESUME=${GO2_RESUME:-0}
RECOVERY_ONLY=${GO2_RECOVERY_ONLY:-0}
RECOVERY_SEED="$PACKAGE_ROOT/recovery_seed"
CASE_ATTEMPTS=${GO2_CASE_ATTEMPTS:-3}
CASE_RETRY_DELAY=${GO2_CASE_RETRY_DELAY:-10}

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
  [[ "$RECOVERY_ONLY" == 0 || "$RECOVERY_ONLY" == 1 ]] || { echo '[FAIL] GO2_RECOVERY_ONLY must be 0 or 1'; exit 2; }
  [[ "$RECOVERY_ONLY" == 0 || "$RESUME" == 1 ]] || { echo '[FAIL] recovery-only mode requires GO2_RESUME=1'; exit 2; }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  [[ -d "$CANDIDATE_ROOT" && -s "$REGISTRY" && -s "$BASELINE_REPORT" ]] || {
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
    "cd '$PACKAGE_ROOT' && PACKAGE_ROOT='$PACKAGE_ROOT' GO2_RESUME='$RESUME' bash server_run_go2_feet_air_time_020_v1.sh --inner"
  echo "[STARTED] $TMUX_NAME resume=$RESUME"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] [DONE] GO2_FEET_AIR_TIME_020_RESULT_READY"
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
cp -a "$REGISTRY" "$PACKAGE_ROOT/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md" "$KEEP/meta/"
cp -a "$BASELINE_REPORT" "$KEEP/meta/"
sha256sum "$REGISTRY" "$BASELINE_REPORT" >"$KEEP/meta/frozen_inputs.sha256"

if [[ "$RECOVERY_ONLY" == 1 ]]; then
  [[ -s "$RECOVERY_SEED/training/model_best.pt" && -s "$RECOVERY_SEED/training/env.yaml" ]] || {
    echo '[FAIL] recovery seed is missing candidate model/env'; exit 2;
  }
  cp -an "$RECOVERY_SEED/." "$KEEP/"
  RECOVERED_SHA=$(sha256sum "$KEEP/training/model_best.pt" | awk '{print $1}')
  [[ "$RECOVERED_SHA" == "$EXPECTED_CANDIDATE_SHA" ]] || {
    echo "[FAIL] recovery candidate mismatch: $RECOVERED_SHA"; exit 2;
  }
  echo "[RECOVERY] candidate=$RECOVERED_SHA completed_cases=$(find "$KEEP/evaluation/candidate/cases" -name case_identity.sha256 2>/dev/null | wc -l)"
fi

echo '[PHASE 1/4] feet_air_time=0.20-only from-scratch training: seed=42 envs=4096 iterations=1000'
cd "$CANDIDATE_ROOT"
if [[ "$RESUME" == 1 && -s "$KEEP/training/model_best.pt" && -s "$KEEP/training/env.yaml" ]] && \
   grep -qx 'TRAIN_RC=0' "$KEEP/training/TRAIN_STATUS.txt"; then
  echo '[SKIP] candidate training artifact already present'
else
  [[ "$RECOVERY_ONLY" == 0 ]] || { echo '[FAIL] recovery-only mode refuses retraining'; exit 3; }
  rm -rf -- logs exported
  mkdir -p exported
  set +e
  NO_AUTO_SUBMIT=1 /workspace/IsaacLab/isaaclab.sh -p train.py \
    --task Quadruped-v0 --num_envs 4096 --max_iterations 1000 --seed 42 --headless \
    2>&1 | tee "$KEEP/logs/candidate_training.log"
  TRAIN_RC=${PIPESTATUS[0]}
  set -e
  printf 'TRAIN_RC=%s\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS=1000\nSINGLE_CHANGE=feet_air_time:0.01->0.20\n' \
    "$TRAIN_RC" >"$KEEP/training/TRAIN_STATUS.txt"
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
diff -u "$PACKAGE_ROOT/default_quadruped_rewards.py" quadruped_rewards.py >"$KEEP/training/reward_only.diff" || true

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
  local seed=$1 scenario=$2 case_id=$3
  set_case "$case_id"
  local out="$KEEP/evaluation/candidate/cases/seed_${seed}/$case_id"
  mkdir -p "$out" "$KEEP/logs/candidate"
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
    { printf '%s\0%s\0%s\0%s\0' "$CANDIDATE_SHA" "$scenario" "$case_id" "$seed"; printf '%s\0' "${cmd[@]}"; } \
      | sha256sum | awk '{print $1}'
  )
  if [[ "$RESUME" == 1 && -s "$out/summary.json" && -s "$out/STATUS.txt" && -s "$out/case_identity.sha256" ]] && \
     grep -qx 'EVAL_RC=0' "$out/STATUS.txt" && grep -qx "$fingerprint" "$out/case_identity.sha256"; then
    echo "[SKIP] eval candidate $scenario/$case_id seed=$seed"
    return 0
  fi
  local -a push_env=(env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y)
  [[ -n "$PUSH_X" ]] && push_env+=("NCRC_PLAY_PUSH_X=$PUSH_X")
  [[ -n "$PUSH_Y" ]] && push_env+=("NCRC_PLAY_PUSH_Y=$PUSH_Y")
  local attempt rc log
  for ((attempt=1; attempt<=CASE_ATTEMPTS; attempt++)); do
    rm -rf -- "$out"
    mkdir -p "$out"
    log="$KEEP/logs/candidate/seed_${seed}_${case_id}.attempt_${attempt}.log"
    printf '[CASE] scenario=%s case=%s seed=%s attempt=%s/%s\n' \
      "$scenario" "$case_id" "$seed" "$attempt" "$CASE_ATTEMPTS"
    printf 'COMMAND: '; printf '%q ' "${cmd[@]}"; printf '\n'
    set +e
    NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$EVAL_STEPS" NCRC_EVAL_CASE="$case_id" \
    NCRC_EVAL_SCENARIO="$scenario" NCRC_EVAL_SEED="$seed" \
      "${push_env[@]}" "${cmd[@]}" 2>&1 | tee "$log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ "$rc" == 0 && -s "$out/summary.json" && -s "$out/STATUS.txt" ]] && \
       grep -qx 'EVAL_RC=0' "$out/STATUS.txt"; then
      cp -a "$log" "$KEEP/logs/candidate/seed_${seed}_${case_id}.log"
      printf '%s\n' "$fingerprint" >"$out/case_identity.sha256"
      return 0
    fi
    echo "[RETRY] eval candidate $scenario/$case_id seed=$seed rc=$rc attempt=$attempt/$CASE_ATTEMPTS"
    [[ "$attempt" == "$CASE_ATTEMPTS" ]] || sleep $((CASE_RETRY_DELAY * attempt))
  done
  echo "[FAIL] eval candidate $scenario/$case_id seed=$seed after $CASE_ATTEMPTS attempts"
  return 5
}

CANDIDATE_MODEL="$KEEP/training/model_best.pt"
CANDIDATE_ENV="$KEEP/training/env.yaml"
CANDIDATE_SHA=$(sha256sum "$CANDIDATE_MODEL" | awk '{print $1}')

echo '[PHASE 2/4] candidate G1-G7 telemetry: 69 cases'
cd "$CANDIDATE_ROOT"
rm -rf -- exported
mkdir -p exported "$KEEP/evaluation/candidate/source"
cp -a "$CANDIDATE_MODEL" exported/model_best.pt
cp -a "$CANDIDATE_ENV" exported/env.yaml
cp -a play.py quadruped_rewards.py pyproject.toml go2_eval_telemetry.py \
  go2_policy_lineage.py go2_task "$KEEP/evaluation/candidate/source/"
cat >"$KEEP/evaluation/candidate/identity.json" <<EOF
{"policy":"feet_air_time_020","model_sha256":"$CANDIDATE_SHA","env_sha256":"$(sha256sum "$CANDIDATE_ENV" | awk '{print $1}')","registry_sha256":"$(sha256sum "$REGISTRY" | awk '{print $1}')","training_seed":42}
EOF
for seed in "${SEEDS[@]}"; do
  run_eval_case "$seed" G1 forward_slow
  run_eval_case "$seed" G1 forward_nominal
  run_eval_case "$seed" G1 forward_fast
  for case_id in backward left right diagonal_left diagonal_right combined_yaw_left combined_yaw_right; do
    run_eval_case "$seed" G2 "$case_id"
  done
  run_eval_case "$seed" G3 rough_forward
  run_eval_case "$seed" G3 rough_lateral
  run_eval_case "$seed" G4 slope_plus_20
  run_eval_case "$seed" G4 slope_minus_20
  for case_id in stairs_10_up stairs_10_down stairs_15_up stairs_15_down; do
    run_eval_case "$seed" G5 "$case_id"
  done
  for case_id in push_pos_x push_neg_x push_pos_y push_neg_y; do
    run_eval_case "$seed" G6 "$case_id"
  done
  run_eval_case "$seed" G7 "dr_seed_${seed}"
done
[[ "$(find "$KEEP/evaluation/candidate/cases" -name summary.json | wc -l)" == 69 ]] || {
  echo '[FAIL] candidate telemetry count is not 69'; exit 6;
}
if [[ -s exported/policy.pt ]]; then
  cp -a exported/policy.pt "$KEEP/evaluation/candidate/policy.pt"
fi
[[ -s "$KEEP/evaluation/candidate/policy.pt" ]] || { echo '[FAIL] candidate policy export missing'; exit 6; }
/workspace/IsaacLab/isaaclab.sh -p go2_policy_lineage.py \
  "$CANDIDATE_MODEL" "$KEEP/evaluation/candidate/policy.pt" "$KEEP/evaluation/candidate/POLICY_LINEAGE.json"

echo '[PHASE 3/4] pre-registered report and candidate worst-case videos'
/workspace/IsaacLab/isaaclab.sh -p "$PACKAGE_ROOT/go2_single_variable_report.py" \
  --registry "$REGISTRY" --baseline-report "$BASELINE_REPORT" \
  --candidate-root "$KEEP/evaluation/candidate" --out "$KEEP/reports"

run_video() {
  local scenario=$1 case_id=$2 seed=$3
  set_case "$case_id"
  local video="$KEEP/evaluation/candidate/videos/${scenario}_${case_id}_seed_${seed}.mp4"
  if [[ "$RESUME" == 1 && -s "$video" ]]; then
    echo "[SKIP] video candidate $scenario/$case_id seed=$seed"
    return 0
  fi
  cd "$CANDIDATE_ROOT"
  mkdir -p "$KEEP/evaluation/candidate/videos"
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
  local attempt rc log
  for ((attempt=1; attempt<=CASE_ATTEMPTS; attempt++)); do
    rm -rf -- exported
    mkdir -p exported
    cp -a "$CANDIDATE_MODEL" exported/model_best.pt
    cp -a "$CANDIDATE_ENV" exported/env.yaml
    log="$KEEP/logs/candidate/video_${scenario}_${case_id}_seed_${seed}.attempt_${attempt}.log"
    set +e
    "${push_env[@]}" "${cmd[@]}" 2>&1 | tee "$log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ "$rc" == 0 && -s exported/play_video.mp4 ]]; then
      cp -a "$log" "$KEEP/logs/candidate/video_${scenario}_${case_id}_seed_${seed}.log"
      cp -a exported/play_video.mp4 "$video"
      return 0
    fi
    echo "[RETRY] video candidate $scenario/$case_id seed=$seed rc=$rc attempt=$attempt/$CASE_ATTEMPTS"
    [[ "$attempt" == "$CASE_ATTEMPTS" ]] || sleep $((CASE_RETRY_DELAY * attempt))
  done
  echo "[FAIL] video missing after $CASE_ATTEMPTS attempts: candidate $scenario"
  return 8
}

while IFS=$'\t' read -r scenario case_id seed; do
  [[ "$scenario" == scenario ]] && continue
  run_video "$scenario" "$case_id" "$seed"
done <"$KEEP/evaluation/candidate/WORST_CASES.tsv"
[[ "$(find "$KEEP/evaluation/candidate/videos" -name '*.mp4' | wc -l)" == 7 ]] || {
  echo '[FAIL] expected 7 worst-case videos for candidate'; exit 8;
}

echo '[PHASE 4/4] one-file result packaging'
printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nBASELINE_MODEL_SHA=%s\nCANDIDATE_MODEL_SHA=%s\nTELEMETRY_CANDIDATE=69\nVIDEOS_CANDIDATE=7\nEVALUATOR_TERMINATION=GRACEFUL\nCASE_ATTEMPTS=%s\nVIDEO_STATUS=VIDEO_UNKNOWN\nOFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED\n' \
  "$(date -Is)" "$BASELINE_MODEL_SHA" "$CANDIDATE_SHA" "$CASE_ATTEMPTS" >"$KEEP/RUNNER_STATUS.txt"
package_result FULL
trap - EXIT
echo '[DONE] GO2_FEET_AIR_TIME_020_RESULT_READY'
