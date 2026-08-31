#!/usr/bin/env bash
# Go2 4족 1,000 iter pilot 고정 명령 영상 스위트 — H1 server_run06_videos.sh 벤치마킹
# Outer: VIDEO_SUITE=full bash server_run_Go2_videos.sh
# Output: /workspace/_keep/train_260831-Go2_5var_1000_videos_*.tar.gz
# 벤치마킹 원본: workspace/training/humanoid/server_run06_videos.sh (SHA 793ca054...)
#   - 동일 구조: tmux, CORE(4종)→FULL(10종) 2단 패키징, fingerprint, VIDEO_STATUS.tsv, preflight
#   - 변경점: Humanoid-v0 → Quadruped-v0, 12관절, RUN_ID/MODEL_SHA/TMUX_NAME/G시나리오
set -euo pipefail

ROOT=/workspace/training/quadruped
RUN_ID=train_260831-Go2_5var_1000
MODEL_SHA=C4D78ADF3FBD90311E70D2B165370DDDED3D5F913E8F128621FA1BE45F89AF8D
SUITE=${VIDEO_SUITE:-full}
RESUME=${VIDEO_RESUME:-0}
TMUX_NAME=run_Go2_videos
KEEP=/workspace/_keep/${RUN_ID}_videos

package_now() {
  local label=$1
  (
    cd "$KEEP"
    find . -type f ! -name SHA256SUMS.txt ! -name SHA256SUMS.txt.tmp -print0 \
      | sort -z | xargs -0 sha256sum >SHA256SUMS.txt.tmp
    mv SHA256SUMS.txt.tmp SHA256SUMS.txt
  )
  local tarball="/workspace/_keep/${RUN_ID}_VIDEOS_${label}.tar.gz"
  local tmp="${tarball}.tmp"
  tar -C /workspace/_keep -czf "$tmp" "${RUN_ID}_videos"
  tar -tzf "$tmp" >/dev/null
  mv "$tmp" "$tarball"
  sha256sum "$tarball" >"${tarball}.sha256.tmp"
  mv "${tarball}.sha256.tmp" "${tarball}.sha256"
  cat "${tarball}.sha256"
  echo "[PACKAGE] $tarball"
}

if [[ "${1:-}" != "--inner" ]]; then
  [[ "$SUITE" == "core" || "$SUITE" == "full" ]] || {
    echo '[FAIL] VIDEO_SUITE must be core or full'; exit 2;
  }
  [[ "$RESUME" == "0" || "$RESUME" == "1" ]] || {
    echo '[FAIL] VIDEO_RESUME must be 0 or 1'; exit 2;
  }
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux 없음'; exit 2; }
  pgrep -af 'train.py|isaaclab.sh.*train.py' && {
    echo '[BLOCKED] 학습 프로세스가 아직 실행 중입니다.'; exit 2;
  } || true
  tmux has-session -t "$TMUX_NAME" 2>/dev/null && {
    echo "[BLOCKED] tmux $TMUX_NAME already exists"; exit 2;
  }
  mkdir -p "$KEEP"
  tmux new-session -d -s "$TMUX_NAME" \
    "cd '$ROOT' && VIDEO_SUITE='$SUITE' VIDEO_RESUME='$RESUME' bash server_run_Go2_videos.sh --inner"
  echo "[STARTED] $TMUX_NAME suite=$SUITE resume=$RESUME"
  echo "[MONITOR] tmux attach -t $TMUX_NAME"
  echo "[CORE] /workspace/_keep/${RUN_ID}_VIDEOS_CORE.tar.gz"
  echo "[FULL] /workspace/_keep/${RUN_ID}_VIDEOS_FULL.tar.gz"
  exit 0
fi

cd "$ROOT"
mkdir -p "$KEEP/videos" "$KEEP/logs" "$KEEP/policies" "$KEEP/meta"
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

echo "$MODEL_SHA  exported/model_best.pt" | sha256sum -c -
cp -a exported/model_best.pt exported/env.yaml "$KEEP/meta/"
sha256sum play.py quadruped_rewards.py go2_task/*.py >"$KEEP/meta/source.sha256"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader \
  >"$KEEP/meta/gpu.csv" || true
if [[ "$RESUME" != "1" || ! -s "$KEEP/VIDEO_STATUS.tsv" ]]; then
  printf 'scenario\tvx\tvy\twz\tpush_mps\tterrain\tplay_rc\tmp4_bytes\tpolicy_bytes\n' \
    >"$KEEP/VIDEO_STATUS.tsv"
fi

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

preflight_config() {
  local scenario=$1 vx=$2 vy=$3 wz=$4 terrain=$5
  shift 5
  local -a terrain_args=("$@")
  local -a cmd=(
    /workspace/IsaacLab/isaaclab.sh -p play.py
    --task Quadruped-v0 --num_envs 1
    --headless --video --video_length 2 --enable_cameras
    'agent.seed=42'
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$vx,$vx]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$vy,$vy]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$wz,$wz]"
    "${terrain_args[@]}"
  )

  rm -f exported/play_video.mp4 exported/policy.pt
  {
    echo "===== PREFLIGHT $scenario terrain=$terrain ====="
    printf 'COMMAND: '; printf '%q ' "${cmd[@]}"; printf '\n'
  } | tee "$KEEP/logs/preflight_${scenario}.command.txt"

  set +e
  "${cmd[@]}" 2>&1 | tee "$KEEP/logs/preflight_${scenario}.log"
  local rc=${PIPESTATUS[0]}
  set -e
  if [[ "$rc" != 0 || ! -s exported/play_video.mp4 || ! -s exported/policy.pt ]]; then
    echo "[PREFLIGHT_FAIL] $scenario rc=$rc or artifact missing"
    exit 4
  fi
  rm -f exported/play_video.mp4 exported/policy.pt
  echo "[PREFLIGHT_OK] $scenario"
}

run_case() {
  local scenario=$1 vx=$2 vy=$3 wz=$4 push=$5 terrain=$6
  shift 6
  local -a terrain_args=("$@")
  local -a cmd=(
    /workspace/IsaacLab/isaaclab.sh -p play.py
    --task Quadruped-v0 --num_envs 4
    --headless --video --video_length 1000 --enable_cameras
    'agent.seed=42'
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$vx,$vx]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$vy,$vy]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$wz,$wz]"
    "${terrain_args[@]}"
  )
  [[ "$push" == "0" ]] || cmd+=(--push "$push")

  local fingerprint
  fingerprint=$(
    {
      printf '%s\0' "$MODEL_SHA"
      cat "$KEEP/meta/source.sha256"
      printf '%s\0' "${cmd[@]}"
    } | sha256sum | awk '{print $1}'
  )
  if [[ "$RESUME" == "1" && -s "$KEEP/videos/${scenario}.mp4" && -s "$KEEP/policies/${scenario}.pt" ]] &&
     [[ -s "$KEEP/logs/${scenario}.fingerprint.sha256" ]] &&
     grep -qx "$fingerprint" "$KEEP/logs/${scenario}.fingerprint.sha256" &&
     (cd "$KEEP" && sha256sum -c "logs/${scenario}.artifacts.sha256" >/dev/null) &&
     awk -F '\t' -v scenario="$scenario" '$1 == scenario && $7 == 0 && $8 > 0 && $9 > 0 { found=1 } END { exit !found }' "$KEEP/VIDEO_STATUS.tsv"; then
    echo "[SKIP] $scenario already complete and fingerprint matches"
    return 0
  fi

  awk -F '\t' -v scenario="$scenario" 'NR == 1 || $1 != scenario' \
    "$KEEP/VIDEO_STATUS.tsv" >"$KEEP/VIDEO_STATUS.tsv.tmp"
  mv "$KEEP/VIDEO_STATUS.tsv.tmp" "$KEEP/VIDEO_STATUS.tsv"

  rm -f exported/play_video.mp4 exported/policy.pt
  {
    echo "===== $scenario vx=$vx vy=$vy wz=$wz push=$push terrain=$terrain ====="
    printf 'COMMAND: '; printf '%q ' "${cmd[@]}"; printf '\n'
  } | tee "$KEEP/logs/${scenario}.command.txt"

  set +e
  "${cmd[@]}" 2>&1 | tee "$KEEP/logs/${scenario}.log"
  local rc=${PIPESTATUS[0]}
  set -e
  if [[ "$rc" != 0 || ! -s exported/play_video.mp4 || ! -s exported/policy.pt ]]; then
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t0\t0\n' \
      "$scenario" "$vx" "$vy" "$wz" "$push" "$terrain" "$rc" \
      >>"$KEEP/VIDEO_STATUS.tsv"
    echo "[FAIL] $scenario rc=$rc or artifact missing"
    exit 3
  fi
  cp -a exported/play_video.mp4 "$KEEP/videos/${scenario}.mp4"
  cp -a exported/policy.pt "$KEEP/policies/${scenario}.pt"
  printf '%s\n' "$fingerprint" >"$KEEP/logs/${scenario}.fingerprint.sha256"
  (
    cd "$KEEP"
    sha256sum "videos/${scenario}.mp4" "policies/${scenario}.pt" \
      >"logs/${scenario}.artifacts.sha256"
  )
  printf '%s\t%s\t%s\t%s\t%s\t%s\t0\t%s\t%s\n' \
    "$scenario" "$vx" "$vy" "$wz" "$push" "$terrain" \
    "$(stat -c %s "$KEEP/videos/${scenario}.mp4")" \
    "$(stat -c %s "$KEEP/policies/${scenario}.pt")" \
    >>"$KEEP/VIDEO_STATUS.tsv"
}

write_status() {
  local suite=$1
  echo "VIDEO_SUITE=$suite" >"$KEEP/STATUS.txt"
  echo "VIDEO_COUNT=$(find "$KEEP/videos" -type f -name '*.mp4' | wc -l)" >>"$KEEP/STATUS.txt"
  echo "POLICY_COUNT=$(find "$KEEP/policies" -type f -name '*.pt' | wc -l)" >>"$KEEP/STATUS.txt"
  echo "MODEL_SHA=$MODEL_SHA" >>"$KEEP/STATUS.txt"
  date -Is >>"$KEEP/STATUS.txt"
}

validate_full() {
  local -a expected=(G1_stand G2_forward G3_left G3_right G4_complex G4_complex_right G5_rough G6_plus10_approx G6_minus10_approx G7_push)
  [[ "$(find "$KEEP/videos" -type f -name '*.mp4' | wc -l)" == 10 ]]
  [[ "$(find "$KEEP/policies" -type f -name '*.pt' | wc -l)" == 10 ]]
  local scenario
  for scenario in "${expected[@]}"; do
    [[ -s "$KEEP/videos/${scenario}.mp4" && -s "$KEEP/policies/${scenario}.pt" ]]
    awk -F '\t' -v scenario="$scenario" '$1 == scenario && $7 == 0 && $8 > 0 && $9 > 0 { found=1 } END { exit !found }' "$KEEP/VIDEO_STATUS.tsv"
    (cd "$KEEP" && sha256sum -c "logs/${scenario}.artifacts.sha256" >/dev/null)
  done
}

# Core: stage-1 regression gate.
if [[ "$SUITE" == "full" ]]; then
  preflight_config G5_rough 0.50 0.00 0.00 rough "${ROUGH[@]}"
  preflight_config G6_plus10_approx 0.50 0.00 0.00 slope_inv "${SLOPE_UP[@]}"
  preflight_config G6_minus10_approx 0.50 0.00 0.00 slope "${SLOPE_DOWN[@]}"
fi

run_case G1_stand 0.00 0.00 0.00 0 plane "${PLANE[@]}"
run_case G2_forward 0.75 0.00 0.00 0 plane "${PLANE[@]}"
run_case G4_complex 0.50 0.15 0.50 0 plane "${PLANE[@]}"
run_case G7_push 0.00 0.00 0.00 0.5 plane "${PLANE[@]}"

if [[ "$SUITE" == "full" ]]; then
  write_status core
  package_now CORE
  run_case G3_left 0.00 0.30 0.00 0 plane "${PLANE[@]}"
  run_case G3_right 0.00 -0.30 0.00 0 plane "${PLANE[@]}"
  run_case G4_complex_right 0.50 -0.15 -0.50 0 plane "${PLANE[@]}"
  run_case G5_rough 0.50 0.00 0.00 0 rough "${ROUGH[@]}"
  run_case G6_plus10_approx 0.50 0.00 0.00 0 slope_inv "${SLOPE_UP[@]}"
  run_case G6_minus10_approx 0.50 0.00 0.00 0 slope "${SLOPE_DOWN[@]}"
  validate_full
  write_status full
  package_now FULL
else
  write_status core
  package_now CORE
fi

printf 'RUNNER_RC=0\nCOMPLETED_AT=%s\n' "$(date -Is)" >"$KEEP/RUNNER_STATUS.txt"
echo "[DONE] Go2 video suite=$SUITE"
