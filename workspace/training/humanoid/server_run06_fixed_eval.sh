#!/usr/bin/env bash
# Run06 model_9900 fixed-policy telemetry suite. No training is performed.
# User command: bash server_run06_fixed_eval.sh
set -euo pipefail

ROOT=/workspace/training/humanoid
RUN_ID=train_260831-06_run05cfg_10000
MODEL_SHA=8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636
MODEL_SOURCE="$ROOT/_eval_run06/model_best.pt"
ENV_SOURCE="$ROOT/_eval_run06/env.yaml"
KEEP="/workspace/_keep/${RUN_ID}_fixed_eval"
TMUX_NAME=run06_fixed_eval
RESUME=${EVAL_RESUME:-0}

package_now() {
  local label=$1
  mkdir -p "$KEEP"
  (
    cd "$KEEP"
    find . -type f ! -name SHA256SUMS.txt ! -name SHA256SUMS.txt.tmp -print0 \
      | sort -z | xargs -0 sha256sum >SHA256SUMS.txt.tmp
    mv SHA256SUMS.txt.tmp SHA256SUMS.txt
  )
  local tarball="/workspace/_keep/${RUN_ID}_FIXED_EVAL_${label}.tar.gz"
  local tmp="${tarball}.tmp"
  tar -C /workspace/_keep -czf "$tmp" "${RUN_ID}_fixed_eval"
  tar -tzf "$tmp" >/dev/null
  mv "$tmp" "$tarball"
  sha256sum "$tarball" >"${tarball}.sha256"
  echo "[PACKAGE] $tarball"
  cat "${tarball}.sha256"
}

if [[ "${1:-}" != "--inner" ]]; then
  [[ "$RESUME" == 0 || "$RESUME" == 1 ]] || { echo '[FAIL] EVAL_RESUME must be 0 or 1'; exit 2; }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing'; exit 2; }
  pgrep -af 'train.py|isaaclab.sh.*train.py' && {
    echo '[BLOCKED] A training process is still running.'; exit 2;
  } || true
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
    echo "[BLOCKED] tmux session already exists: $TMUX_NAME"; exit 2;
  }
  [[ -s "$MODEL_SOURCE" ]] || { echo "[FAIL] missing $MODEL_SOURCE"; exit 2; }
  echo "$MODEL_SHA  $MODEL_SOURCE" | sha256sum -c -
  tmux new-session -d -s "$TMUX_NAME" \
    "cd '$ROOT' && EVAL_RESUME='$RESUME' bash server_run06_fixed_eval.sh --inner"
  echo "[STARTED] $TMUX_NAME"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[RESULT] /workspace/_keep/${RUN_ID}_FIXED_EVAL_FULL.tar.gz"
  exit 0
fi

cd "$ROOT"
if [[ "$RESUME" == 0 ]]; then
  rm -rf -- "$KEEP"
fi
mkdir -p "$KEEP/cases" "$KEEP/logs" "$KEEP/meta" exported
exec > >(tee -a "$KEEP/launcher.log") 2>&1

on_exit() {
  local rc=$?
  if [[ "$rc" != 0 ]]; then
    trap - EXIT
    printf 'RUNNER_RC=%s\nFAILED_AT=%s\n' "$rc" "$(date -Is)" >"$KEEP/RUNNER_STATUS.txt"
    package_now PARTIAL || true
  fi
}
trap on_exit EXIT

echo "$MODEL_SHA  $MODEL_SOURCE" | sha256sum -c -
cp -a "$MODEL_SOURCE" exported/model_best.pt
cp -a "$ENV_SOURCE" exported/env.yaml
sha256sum play.py eval_telemetry.py fixed_eval_report.py humanoid_rewards.py h1_task/*.py \
  >"$KEEP/meta/source.sha256"
cp -a "$MODEL_SOURCE" "$ENV_SOURCE" "$KEEP/meta/"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$KEEP/meta/gpu.csv"
printf 'scenario\tvx\tvy\twz\tpush_mps\tterrain\tsteps\tplay_rc\n' >"$KEEP/EVAL_STATUS.tsv"

PLANE=(
  'env.scene.terrain.terrain_type=plane'
  'env.curriculum.terrain_levels=null'
)

SLOPE_UP=(
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
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=1.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.slope_range=[0.17632698,0.17632698]'
)

SLOPE_DOWN=(
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
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=1.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.slope_range=[0.17632698,0.17632698]'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0'
)

ROUGH=(
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
  'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
  'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0'
  'env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0'
)

run_case() {
  local scenario=$1 vx=$2 vy=$3 wz=$4 push=$5 terrain=$6 steps=$7
  shift 7
  local -a terrain_args=("$@")
  local out="$KEEP/cases/$scenario"
  if [[ "$RESUME" == 1 && -s "$out/STATUS.txt" ]] && grep -qx 'EVAL_RC=0' "$out/STATUS.txt"; then
    echo "[SKIP] $scenario already complete"
    return 0
  fi
  rm -rf -- "$out"
  mkdir -p "$out"
  local -a cmd=(
    /workspace/IsaacLab/isaaclab.sh -p play.py
    --task Humanoid-v0 --num_envs 32 --headless
    'agent.seed=42'
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$vx,$vx]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$vy,$vy]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$wz,$wz]"
    "${terrain_args[@]}"
  )
  [[ "$push" == 0 ]] || cmd+=(--push "$push")
  {
    echo "scenario=$scenario terrain=$terrain steps=$steps"
    printf 'COMMAND: '; printf '%q ' "${cmd[@]}"; printf '\n'
  } | tee "$KEEP/logs/${scenario}.command.txt"
  set +e
  NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$steps" "${cmd[@]}" \
    2>&1 | tee "$KEEP/logs/${scenario}.log"
  local rc=${PIPESTATUS[0]}
  set -e
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$scenario" "$vx" "$vy" "$wz" "$push" "$terrain" "$steps" "$rc" \
    >>"$KEEP/EVAL_STATUS.tsv"
  if [[ "$rc" != 0 || ! -s "$out/summary.json" || ! -s "$out/steps.csv" ]] || \
     ! grep -qx 'EVAL_RC=0' "$out/STATUS.txt"; then
    echo "[FAIL] $scenario rc=$rc or telemetry missing"
    exit 3
  fi
  echo "[OK] $scenario"
}

# Every case runs one full 20 s episode so survival is measurable.  Paired
# directions are scored by their worse result in fixed_eval_report.py.
run_case H1_stand   0.00  0.00  0.00 0 plane 1000 "${PLANE[@]}"
run_case H2_forward 0.75  0.00  0.00 0 plane 1000 "${PLANE[@]}"
run_case H3_left    0.00  0.30  0.00 0 plane 1000 "${PLANE[@]}"
run_case H3_right   0.00 -0.30  0.00 0 plane 1000 "${PLANE[@]}"
run_case H4_left    0.50  0.15  0.50 0 plane 1000 "${PLANE[@]}"
run_case H4_right   0.50 -0.15 -0.50 0 plane 1000 "${PLANE[@]}"
run_case H5_rough   0.50  0.00  0.00 0 rough 1000 "${ROUGH[@]}"
run_case H6_plus10  0.50 0.00 0.00 0 slope_inv 1000 "${SLOPE_UP[@]}"
run_case H6_minus10 0.50 0.00 0.00 0 slope 1000 "${SLOPE_DOWN[@]}"
run_case H7_push 0.00 0.00 0.00 0.5 plane 1000 "${PLANE[@]}"

/workspace/IsaacLab/isaaclab.sh -p fixed_eval_report.py "$KEEP"
printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nMODEL_SHA=%s\n' \
  "$(date -Is)" "$MODEL_SHA" >"$KEEP/RUNNER_STATUS.txt"
package_now FULL
trap - EXIT
echo '[DONE] Run06 fixed-policy evaluation complete'
