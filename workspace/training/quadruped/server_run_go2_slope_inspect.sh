#!/usr/bin/env bash
# One upload -> one command -> one result ZIP.  NO TRAINING, NO REWARD CHANGE.
#
# G-A034 "A017 uphill stall witness".
#
# In the stored A017 suite (G-A027) the posture gate marks 7 of 32 robots on
# slope_plus_20, seed 101, as fallen: envs 4 18 20 22 24 27 31.  Their telemetry
# is level (projected gravity z about -1.0), below the 0.18 m height-above-terrain
# line and nearly stopped -- but numbers cannot say whether the robot is
# crouched, slipping, stepping in place, or standing normally while the height
# reading (the mean of the height-scanner grid) runs low.  The stored G4 video
# follows env 0, which walked, so no stalled robot has ever been seen.
#
# This run replays that exact case -- frozen A017, seed 101, 32 envs, the same
# overrides as the suite -- once per target robot, with the camera following
# that robot, and records the telemetry again each time so the result shows
# whether the replay reproduced the stored falls.
#
#   default targets   22 24 4 (stored falls) and 0 (walked; control)
#   GO2_INSPECT_ENVS="22 31"                choose other robots (0-31)
#   GO2_INSPECT_EYE / GO2_INSPECT_LOOKAT    camera offset from the followed robot
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-/workspace/go2_slope_inspect}
ROOT="$PACKAGE_ROOT/a017"
KEEP=/workspace/_keep/go2_slope_inspect
RESULT_ZIP=/workspace/_keep/GO2_SLOPE_INSPECT_RESULT.zip
TMUX_NAME=go2_slope_inspect
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
A017_EXPECTED_SHA=0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4
SEED=101
STEPS=1000
STORED_FALLS="4 18 20 22 24 27 31"
INSPECT_ENVS=${GO2_INSPECT_ENVS:-22 24 4 0}
EYE=${GO2_INSPECT_EYE:-[-2.5,-2.5,1.2]}
LOOKAT=${GO2_INSPECT_LOOKAT:-[0.0,0.0,0.2]}
read -r -a TARGETS <<<"$INSPECT_ENVS"

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
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  [[ -x "$ISAACLAB_SH" ]] || { echo "[FAIL] missing $ISAACLAB_SH"; exit 2; }
  [[ ${#TARGETS[@]} -gt 0 ]] || { echo '[FAIL] GO2_INSPECT_ENVS is empty'; exit 2; }
  for e in "${TARGETS[@]}"; do
    [[ "$e" =~ ^[0-9]+$ && "$e" -le 31 ]] || { echo "[FAIL] robot index must be 0-31: $e"; exit 2; }
  done
  [[ -d "$ROOT" && -s "$PACKAGE_ROOT/go2_slope_stuck_check.py" ]] || {
    echo "[FAIL] package must be extracted at $PACKAGE_ROOT"; exit 2;
  }
  (cd "$PACKAGE_ROOT" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) || {
    echo '[FAIL] package checksum mismatch'; exit 2;
  }
  pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py' && {
    echo '[BLOCKED] training/play process is already running'; exit 2;
  } || true
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
    echo "[BLOCKED] tmux session already exists: $TMUX_NAME"; exit 2;
  }
  if [[ -d "$KEEP" || -e "$RESULT_ZIP" ]]; then
    if [[ "${GO2_DISCARD_PREVIOUS:-0}" != 1 ]]; then
      echo '[BLOCKED] results from a previous run are present:'
      [[ ! -d "$KEEP" ]] || echo "  $KEEP"
      [[ ! -e "$RESULT_ZIP" ]] || echo "  $RESULT_ZIP"
      echo '  download them first, then rerun with GO2_DISCARD_PREVIOUS=1'
      exit 2
    fi
    echo '[WARN] GO2_DISCARD_PREVIOUS=1 -- deleting the previous run'
    rm -rf -- "$KEEP" "$RESULT_ZIP" "${RESULT_ZIP}.sha256"
  fi
  tmux new-session -d -s "$TMUX_NAME" \
    "cd '$PACKAGE_ROOT' && PACKAGE_ROOT='$PACKAGE_ROOT' GO2_INSPECT_ENVS='$INSPECT_ENVS' GO2_INSPECT_EYE='$EYE' GO2_INSPECT_LOOKAT='$LOOKAT' bash server_run_go2_slope_inspect.sh --inner"
  echo "[STARTED] $TMUX_NAME robots=${TARGETS[*]} seed=$SEED case=slope_plus_20"
  echo "[MONITOR] tmux attach -t $TMUX_NAME   (detach: Ctrl+b then d)"
  echo "[ESTIMATE] ${#TARGETS[@]} replays of 1000 steps with video; not measured on this server yet"
  echo "[DOWNLOAD_WHEN_DONE] $RESULT_ZIP"
  echo "[DONE_MARKER] [DONE] GO2_SLOPE_INSPECT_RESULT_READY"
  exit 0
fi

mkdir -p "$KEEP/logs" "$KEEP/videos" "$KEEP/telemetry" "$KEEP/policy" "$KEEP/meta"
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

(cd "$PACKAGE_ROOT" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt)
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$KEEP/meta/gpu.csv" || true
cp -a "$ROOT/exported/model_best.pt" "$KEEP/policy/a017_model_best.pt"
cp -a "$ROOT/exported/env.yaml" "$KEEP/policy/a017_env.yaml"
MODEL_SHA=$(sha256sum "$KEEP/policy/a017_model_best.pt" | awk '{print $1}')
[[ "$MODEL_SHA" == "$A017_EXPECTED_SHA" ]] || { echo "[FAIL] A017 model SHA mismatch: $MODEL_SHA"; exit 7; }

# Identical to set_case slope_plus_20 in server_run_go2_a017_full_suite.sh, the
# runner that produced the stored falls.  Any drift here and the replay is a
# different case, which the reproduction check below would report.
SLOPE_ARGS=(
  'env.scene.terrain.terrain_type=generator'
  'env.curriculum.terrain_levels=null'
  'env.scene.terrain.terrain_generator.curriculum=false'
  'env.scene.terrain.terrain_generator.num_rows=1'
  'env.scene.terrain.terrain_generator.num_cols=4'
  'env.scene.terrain.terrain_generator.difficulty_range=[1.0,1.0]'
  'env.scene.terrain.max_init_terrain_level=0'
  'env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.boxes.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=1.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.slope_range=[0.36397023,0.36397023]'
)

run_target() {
  local e=$1
  local out="$KEEP/telemetry/env_$e"
  local video="$KEEP/videos/slope_plus_20_seed${SEED}_robot${e}.mp4"
  echo "[REPLAY] robot $e: slope_plus_20 seed=$SEED num_envs=32 steps=$STEPS camera follows robot $e"
  cd "$ROOT"
  rm -rf -- exported "$out"
  mkdir -p exported "$out"
  cp -a "$KEEP/policy/a017_model_best.pt" exported/model_best.pt
  cp -a "$KEEP/policy/a017_env.yaml" exported/env.yaml
  local -a cmd=(
    "$ISAACLAB_SH" -p play.py --task Quadruped-v0 --num_envs 32 --headless
    --video --video_length "$STEPS" --enable_cameras
    "agent.seed=$SEED"
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    'env.commands.base_velocity.ranges.lin_vel_x=[0.50,0.50]'
    'env.commands.base_velocity.ranges.lin_vel_y=[0,0]'
    'env.commands.base_velocity.ranges.ang_vel_z=[0,0]'
    "${SLOPE_ARGS[@]}"
    'env.viewer.origin_type=asset_root'
    'env.viewer.asset_name=robot'
    "env.viewer.env_index=$e"
    "env.viewer.eye=$EYE"
    "env.viewer.lookat=$LOOKAT"
  )
  printf 'COMMAND: '; printf '%q ' "${cmd[@]}"; printf '\n'
  set +e
  env -u NCRC_PLAY_PUSH -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y -u NCRC_EVAL_DR \
    NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$STEPS" NCRC_EVAL_CASE=slope_plus_20 \
    NCRC_EVAL_SCENARIO=G4 NCRC_EVAL_SEED="$SEED" \
    "${cmd[@]}" 2>&1 | tee "$KEEP/logs/robot_${e}.log"
  local rc=${PIPESTATUS[0]}
  set -e
  [[ -s exported/play_video.mp4 ]] || { echo "[FAIL] robot $e: no video (play rc=$rc)"; exit 8; }
  [[ -s "$out/summary.json" && -s "$out/steps.csv" ]] || {
    echo "[FAIL] robot $e: no telemetry (play rc=$rc)"; exit 5;
  }
  cp -a exported/play_video.mp4 "$video"
  echo "[VIDEO] $video"
}

started=$(date +%s)
for e in "${TARGETS[@]}"; do
  run_target "$e"
done

# The check prints its own verdict line; the wrapper's exit status is not
# trusted (isaaclab.sh -p reports failure for any nonzero child status).
"$ISAACLAB_SH" -p "$PACKAGE_ROOT/go2_slope_stuck_check.py" "$KEEP/telemetry" \
  --stored "$STORED_FALLS" --out "$KEEP/STUCK_CHECK.txt" || true
[[ -s "$KEEP/STUCK_CHECK.txt" ]] || { echo '[FAIL] stuck check wrote nothing'; exit 6; }
overall=$(sed -n 's/^OVERALL=//p' "$KEEP/STUCK_CHECK.txt" | head -n 1)

printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nWORK_ID=G-A034\nTRAINING=none\nA017_MODEL_SHA=%s\nCASE=slope_plus_20\nSEED=%s\nROBOTS=%s\nCAMERA_EYE=%s\nCAMERA_LOOKAT=%s\nREPLAY=%s\nWALL_SECONDS=%s\n' \
  "$(date -Is)" "$MODEL_SHA" "$SEED" "${TARGETS[*]}" "$EYE" "$LOOKAT" "${overall:-UNKNOWN}" \
  "$(( $(date +%s) - started ))" >"$KEEP/RUNNER_STATUS.txt"
package_result FULL
trap - EXIT
echo "[RESULT] replay=${overall:-UNKNOWN} videos=$(find "$KEEP/videos" -name '*.mp4' | wc -l)"
echo '[DONE] GO2_SLOPE_INSPECT_RESULT_READY'
