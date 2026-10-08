#!/usr/bin/env bash
# H-A001 P0: frozen Run06 / Run05 speed-grid measurement. No training, no reward change.
# Distributed files (play.py, train.py, h1_task/, humanoid_rewards.py, exported/) are not touched.
set -euo pipefail

ROOT=${H1_ROOT:-/workspace/training/humanoid}
ISAACLAB=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
NO_TMUX=${NO_TMUX:-0}   # PC2 (Git Bash): NO_TMUX=1 and run under nohup
PKG="$ROOT/h1_ha001"
WORK_ID=H_A001_P0_SPEED_GRID
KEEP="/workspace/_keep/$WORK_ID"
TMUX_NAME=h1_ha001_p0
RESUME=${EVAL_RESUME:-0}
SEEDS=(101 202 303)
PLAY_ORIGINAL_SHA=bba3c5acbdd37281430875b87175716a23e91bf830da64794f809d60383d8bdb
declare -A MODEL_SHA=(
  [run06]=8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636
  [run05]=2775a61e5294f37ec99a1454cdf200b2b0d9cd233022f68c6f293715690e9abc
)
declare -A MODEL_PATH=(
  [run06]="$PKG/models/run06/model_9900.pt"
  [run05]="$PKG/models/run05/model_2700.pt"
)
POLICIES=(run06 run05)

package_now() {
  local label=$1
  mkdir -p "$KEEP"
  (
    cd "$KEEP"
    find . -type f ! -name SHA256SUMS.txt ! -name SHA256SUMS.txt.tmp -print0 \
      | sort -z | xargs -0 sha256sum >SHA256SUMS.txt.tmp
    mv SHA256SUMS.txt.tmp SHA256SUMS.txt
  )
  local tarball="/workspace/_keep/${WORK_ID}_${label}.tar.gz"
  tar -C /workspace/_keep -czf "${tarball}.tmp" "$WORK_ID"
  tar -tzf "${tarball}.tmp" >/dev/null
  mv "${tarball}.tmp" "$tarball"
  sha256sum "$tarball" >"${tarball}.sha256"
  echo "[PACKAGE] $tarball"
  cat "${tarball}.sha256"
}

preflight() {
  echo "$PLAY_ORIGINAL_SHA  $ROOT/play.py" | sha256sum -c - || {
    echo '[BLOCKED] play.py is not the distributed original (R-6). Restore it first.'; exit 2;
  }
  local p
  for p in "${POLICIES[@]}"; do
    echo "${MODEL_SHA[$p]}  ${MODEL_PATH[$p]}" | sha256sum -c -
  done
}

if [[ "${1:-}" != "--inner" ]]; then
  [[ "$RESUME" == 0 || "$RESUME" == 1 ]] || { echo '[FAIL] EVAL_RESUME must be 0 or 1'; exit 2; }
  if command -v pgrep >/dev/null 2>&1 && pgrep -af 'train.py|play.py' >/dev/null; then
    echo '[BLOCKED] train.py or play.py is still running.'; exit 2
  fi
  preflight
  if [[ "$NO_TMUX" == 1 ]]; then
    cd "$ROOT" && EVAL_RESUME="$RESUME" exec bash "$PKG/server_run_h1_ha001_p0.sh" --inner
  fi
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux is missing (set NO_TMUX=1 to run in the foreground)'; exit 2; }
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
    echo "[BLOCKED] tmux session already exists: $TMUX_NAME"; exit 2;
  }
  tmux new-session -d -s "$TMUX_NAME" \
    "cd '$ROOT' && EVAL_RESUME='$RESUME' bash '$PKG/server_run_h1_ha001_p0.sh' --inner"
  echo "[STARTED] $TMUX_NAME"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[RESULT] /workspace/_keep/${WORK_ID}_FULL.tar.gz"
  exit 0
fi

cd "$ROOT"
[[ "$RESUME" == 0 ]] && rm -rf -- "$KEEP"
mkdir -p "$KEEP/cases" "$KEEP/logs" "$KEEP/meta"
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

preflight
sha256sum play.py h1_task/*.py humanoid_rewards.py "$PKG"/*.py "$PKG"/*.sh \
  "${MODEL_PATH[@]}" >"$KEEP/meta/source.sha256"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$KEEP/meta/gpu.csv" || true
printf 'policy\tseed\tcase\tvx\tvy\twz\tterrain\tsteps\tplay_rc\n' >"$KEEP/EVAL_STATUS.tsv"

PLANE=(
  'env.scene.terrain.terrain_type=plane'
  'env.curriculum.terrain_levels=null'
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
  local policy=$1 seed=$2 name=$3 vx=$4 vy=$5 wz=$6 terrain=$7 steps=$8
  shift 8
  local -a terrain_args=("$@")
  local out="$KEEP/cases/$policy/seed_$seed/$name"
  if [[ "$RESUME" == 1 && -s "$out/STATUS.txt" ]] && grep -qx 'EVAL_RC=0' "$out/STATUS.txt"; then
    echo "[SKIP] $policy seed=$seed $name"; return 0
  fi
  rm -rf -- "$out"; mkdir -p "$out"
  local -a cmd=(
    "$ISAACLAB" -p "$PKG/h1_eval_entry.py"
    --task Humanoid-v0 --num_envs 32 --headless
    --checkpoint "${MODEL_PATH[$policy]}"
    "agent.seed=$seed"
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$vx,$vx]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$vy,$vy]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$wz,$wz]"
    "${terrain_args[@]}"
  )
  local log="$KEEP/logs/${policy}_seed${seed}_${name}"
  { printf 'COMMAND: '; printf '%q ' "${cmd[@]}"; printf '\n'; } | tee "$log.command.txt"
  set +e
  NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$steps" "${cmd[@]}" 2>&1 | tee "$log.log"
  local rc=${PIPESTATUS[0]}
  set -e
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$policy" "$seed" "$name" "$vx" "$vy" "$wz" "$terrain" "$steps" "$rc" >>"$KEEP/EVAL_STATUS.tsv"
  if [[ "$rc" != 0 || ! -s "$out/summary.json" || ! -s "$out/steps.csv" ]] || \
     ! grep -qx 'EVAL_RC=0' "$out/STATUS.txt"; then
    echo "[FAIL] $policy seed=$seed $name rc=$rc or telemetry missing"; exit 3
  fi
  echo "[OK] $policy seed=$seed $name"
}

for policy in "${POLICIES[@]}"; do
  for seed in "${SEEDS[@]}"; do
    run_case "$policy" "$seed" plane_vx0p75   0.75 0.0  0.0 plane 1000 "${PLANE[@]}"
    run_case "$policy" "$seed" plane_vx1p00   1.00 0.0  0.0 plane 1000 "${PLANE[@]}"
    run_case "$policy" "$seed" plane_vx1p25   1.25 0.0  0.0 plane 1000 "${PLANE[@]}"
    run_case "$policy" "$seed" rough_vx0p75   0.75 0.0  0.0 rough 1000 "${ROUGH[@]}"
    run_case "$policy" "$seed" rough_vx1p00   1.00 0.0  0.0 rough 1000 "${ROUGH[@]}"
    run_case "$policy" "$seed" turn_vx0p50_L  0.50 0.0  0.5 plane 1000 "${PLANE[@]}"
    run_case "$policy" "$seed" turn_vx0p50_R  0.50 0.0 -0.5 plane 1000 "${PLANE[@]}"
    run_case "$policy" "$seed" turn_vx1p00_L  1.00 0.0  0.5 plane 1000 "${PLANE[@]}"
    run_case "$policy" "$seed" turn_vx1p00_R  1.00 0.0 -0.5 plane 1000 "${PLANE[@]}"
  done
done

printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\nSEEDS=%s\nPOLICIES=%s\n' \
  "$(date -Is)" "${SEEDS[*]}" "${POLICIES[*]}" >"$KEEP/RUNNER_STATUS.txt"
package_now FULL
trap - EXIT
echo '[DONE] H-A001 P0 speed grid complete. Download the FULL tar.gz and .sha256, then the server may be shut down.'
