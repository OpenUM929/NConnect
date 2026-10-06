#!/usr/bin/env bash
# PC2 진단 재생 러너 (G-A065/G-A066, 2026-10-06).  학습 없음 · 보상 변경 없음.
# server_run_go2_a043_diag_replay.sh(G-A056)에서 다음만 바꿨다:
#   - 실행 목록: stairs_15_down·rough_lateral × 평가 seed 202·101·303 × plain·diag = 12회 (영상 없음)
#   - set_case: 두 case 의 분기를 PC2 평가 러너(server_run_go2_candidate_iter_pinned.sh)와 같은 문자열로 둔다
#   - 정책 식별 문구는 run_config.env 의 POLICY_LABEL 을 쓴다
#   - tmux 를 쓰지 않는다: --inner 없이 부르면 사전 검사 뒤 같은 프로세스에서 --inner 를 실행한다(PC2 Git Bash)
#   - 재현 검사: 모든 seed·case 에서 plain 과 diag 의 steps.csv 를 비교한다
# PC2 결과는 행동 경로 진단 자료이며 성능 판정이나 제출 근거가 아니다.
set -euo pipefail

PACKAGE_ROOT=${PACKAGE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
SELF=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
DRY_RUN=${GO2_DIAG_DRY_RUN:-0}
[[ -s "$PACKAGE_ROOT/PACKAGE_SHA256SUMS.txt" && -s "$PACKAGE_ROOT/run_config.env" ]] || {
  echo "[FAIL] package must be extracted at $PACKAGE_ROOT"; exit 2;
}
if [[ "$DRY_RUN" != 1 ]]; then
  (cd "$PACKAGE_ROOT" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) || { echo '[FAIL] package checksum mismatch'; exit 2; }
fi
# shellcheck source=/dev/null
source "$PACKAGE_ROOT/run_config.env"

PLAIN_ROOT="$PACKAGE_ROOT/plain"
DIAG_ROOT="$PACKAGE_ROOT/diag"
POLICY_DIR="$PACKAGE_ROOT/policy"
KEEP_BASE=${GO2_DIAG_KEEP_BASE:-/workspace/_keep}  # 시험용으로만 바꾼다(계약 테스트)
KEEP="$KEEP_BASE/$KEEP_DIR_NAME"
RESULT_ZIP="$KEEP_BASE/$RESULT_ZIP_NAME"
EVAL_STEPS=1000
VIDEO_STEPS=1000
ISAACLAB_SH=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
RUNS=(
  "plain 202 G5 stairs_15_down"
  "diag 202 G5 stairs_15_down"
  "plain 202 G3 rough_lateral"
  "diag 202 G3 rough_lateral"
  "plain 101 G5 stairs_15_down"
  "diag 101 G5 stairs_15_down"
  "plain 101 G3 rough_lateral"
  "diag 101 G3 rough_lateral"
  "plain 303 G5 stairs_15_down"
  "diag 303 G5 stairs_15_down"
  "plain 303 G3 rough_lateral"
  "diag 303 G3 rough_lateral"
)
VIDEOS=()

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

# PC2 평가 러너(server_run_go2_candidate_iter_pinned.sh)의 set_case 에서 이 두 case 의 분기를 같은 문자열로 옮겼다.
set_case() {
  local case_id=$1
  VX=0 VY=0 WZ=0
  TERRAIN_ARGS=("${PLANE[@]}")
  case "$case_id" in
    rough_forward|rough_lateral)
      [[ "$case_id" == rough_lateral ]] && VY=0.30 || VX=0.50
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]')
      ;;
    stairs_10_up|stairs_10_down|stairs_15_up|stairs_15_down)
      VX=0.50; local key=pyramid_stairs height=0.10
      [[ "$case_id" == *_down ]] && key=pyramid_stairs_inv
      [[ "$case_id" == stairs_15_* ]] && height=0.15
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.proportion=1.0"
        "env.scene.terrain.terrain_generator.sub_terrains.${key}.step_height_range=[$height,$height]")
      ;;
    *) echo "[FAIL] unknown case: $case_id"; exit 4 ;;
  esac
}

case_command() {
  local seed=$1
  CMD=(
    "$ISAACLAB_SH" -p play.py --task Quadruped-v0 --num_envs 32 --headless
    "agent.seed=$seed"
    'env.commands.base_velocity.heading_command=false'
    'env.commands.base_velocity.rel_standing_envs=0.0'
    'env.commands.base_velocity.resampling_time_range=[1000.0,1000.0]'
    "env.commands.base_velocity.ranges.lin_vel_x=[$VX,$VX]"
    "env.commands.base_velocity.ranges.lin_vel_y=[$VY,$VY]"
    "env.commands.base_velocity.ranges.ang_vel_z=[$WZ,$WZ]"
    "${TERRAIN_ARGS[@]}"
  )
}

if [[ "$DRY_RUN" == 1 ]]; then
  ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh
  for run in "${RUNS[@]}"; do
    read -r label seed scenario case_id <<<"$run"
    set_case "$case_id"; case_command "$seed"
    printf 'RUN %s %s %s COMMAND: ' "$label" "$seed" "$case_id"; printf '%q ' "${CMD[@]}"; printf '\n'
  done
  exit 0
fi

package_result() {
  local collection=$1
  mkdir -p "$KEEP"
  printf 'RESULT_STATE=PACKAGED\nCOLLECTION_STATUS=%s\nVIDEOS_WITH_FILE=%s\nVIDEOS_PLANNED=%s\nPACKAGED_AT=%s\n' \
    "$collection" "${videos_with_file:-0}" "${#VIDEOS[@]}" "$(date -Is)" >"$KEEP/RESULT_STATUS.txt"
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
  [[ -x "$ISAACLAB_SH" ]] || { echo "[FAIL] missing $ISAACLAB_SH (ISAACLAB_SH 로 알려 준다)"; exit 2; }
  for root in "$PLAIN_ROOT" "$DIAG_ROOT"; do
    [[ -s "$root/play.py" && -s "$root/go2_eval_telemetry.py" && -s "$root/quadruped_rewards.py" && -d "$root/go2_task" ]] || {
      echo "[FAIL] incomplete source root $root"; exit 2; }
  done
  [[ "$(sha256sum "$PLAIN_ROOT/go2_eval_telemetry.py" | awk '{print $1}')" == "$EXPECTED_EVALUATOR_SHA" &&
     "$(sha256sum "$DIAG_ROOT/go2_eval_telemetry_v6.py" | awk '{print $1}')" == "$EXPECTED_EVALUATOR_SHA" ]] || {
    echo "[FAIL] evaluator bytes are not the PC2 evaluation ruler ($EXPECTED_EVALUATOR_SHA)"; exit 2; }
  [[ "$(sha256sum "$POLICY_DIR/model_best.pt" | awk '{print $1}')" == "$MODEL_SHA" &&
     "$(sha256sum "$POLICY_DIR/env.yaml" | awk '{print $1}')" == "$ENV_SHA" ]] || {
    echo "[FAIL] policy is not $POLICY_LABEL ($MODEL_SHA)"; exit 2; }
  pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py' && {
    echo '[BLOCKED] training/play process is already running'; exit 21; } || true
  if [[ -d "$KEEP" || -e "$RESULT_ZIP" ]]; then
    if [[ "${GO2_DISCARD_PREVIOUS:-0}" != 1 ]]; then
      echo "[BLOCKED] results from a previous run are present: $KEEP $RESULT_ZIP"
      echo '  download them first, or GO2_DISCARD_PREVIOUS=1 to discard them deliberately'
      exit 33
    fi
    echo '[WARN] GO2_DISCARD_PREVIOUS=1 - deleting the previous run'
    rm -rf -- "$KEEP" "$RESULT_ZIP" "${RESULT_ZIP}.sha256"
  fi
  echo "[START] $WORK_ID $POLICY_LABEL runs=${#RUNS[@]} (no training, no video)"
  PACKAGE_ROOT="$PACKAGE_ROOT" ISAACLAB_SH="$ISAACLAB_SH" exec bash "$SELF" --inner
fi

mkdir -p "$KEEP/logs" "$KEEP/meta"
exec > >(tee -a "$KEEP/launcher.log") 2>&1
videos_with_file=0
on_exit() {
  local rc=$?
  if [[ "$rc" != 0 ]]; then
    trap - EXIT
    printf 'RUNNER_RC=%s\nFAILED_AT=%s\n' "$rc" "$(date -Is)" >"$KEEP/RUNNER_STATUS.txt"
    printf 'RUNNER_END=%s\n' "$(date -Is)" >>"$KEEP/meta/RUN_TIMES.txt"
    package_result INCOMPLETE_CRASH || true
  fi
}
trap on_exit EXIT

echo "[START] $WORK_ID at $(date -Is)"
printf 'RUNNER_START=%s\n' "$(date -Is)" >"$KEEP/meta/RUN_TIMES.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >"$KEEP/meta/gpu.csv" || true
cp -a "$PACKAGE_ROOT/run_config.env" "$PACKAGE_ROOT/PACKAGE_SHA256SUMS.txt" "$PACKAGE_ROOT/experiment.json" "$KEEP/meta/"

stage_root() {
  rm -rf -- "$1/exported"
  mkdir -p "$1/exported"
  cp -a "$POLICY_DIR/model_best.pt" "$1/exported/model_best.pt"
  cp -a "$POLICY_DIR/env.yaml" "$1/exported/env.yaml"
}
for root in "$PLAIN_ROOT" "$DIAG_ROOT"; do stage_root "$root"; done
cat >"$KEEP/meta/identity.json" <<IDEOF
{"work_id":"$WORK_ID","policy":"$POLICY_LABEL","model_sha256":"$MODEL_SHA","env_sha256":"$ENV_SHA","evaluator_sha256":"$EXPECTED_EVALUATOR_SHA","diag_module_sha256":"$(sha256sum "$DIAG_ROOT/go2_eval_diag_v2.py" | awk '{print $1}')","diag_wrapper_sha256":"$(sha256sum "$DIAG_ROOT/go2_eval_telemetry.py" | awk '{print $1}')"}
IDEOF

done_runs=0
for run in "${RUNS[@]}"; do
  read -r label seed scenario case_id <<<"$run"
  root=$PLAIN_ROOT
  [[ "$label" == diag ]] && root=$DIAG_ROOT
  set_case "$case_id"; case_command "$seed"
  out="$KEEP/$label/cases/seed_${seed}/$case_id"
  mkdir -p "$out"
  printf 'COMMAND: '; printf '%q ' "${CMD[@]}"; printf '\n'
  started=$(date +%s)
  set +e
  (cd "$root" && env -u NCRC_PLAY_PUSH_X -u NCRC_PLAY_PUSH_Y -u NCRC_EVAL_DR \
    NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS="$EVAL_STEPS" NCRC_EVAL_CASE="$case_id" \
    NCRC_EVAL_SCENARIO="$scenario" NCRC_EVAL_SEED="$seed" \
    "${CMD[@]}") 2>&1 | tee "$KEEP/logs/${label}_seed_${seed}_${case_id}.log"
  rc=${PIPESTATUS[0]}
  set -e
  printf '%s %s %s rc=%s wall_s=%s\n' "$label" "$seed" "$case_id" "$rc" "$(( $(date +%s) - started ))" >>"$KEEP/meta/RUN_TIMES.txt"
  [[ "$rc" == 0 && -s "$out/summary.json" ]] && grep -qx 'EVAL_RC=0' "$out/STATUS.txt" || {
    echo "[FAIL] $label $case_id seed=$seed rc=$rc"; exit 5; }
  if [[ "$label" == diag ]]; then
    [[ -s "$out/diag.csv.gz" && -s "$out/DIAG_STATUS.txt" ]] || { echo "[FAIL] no diag output for $case_id"; exit 5; }
    cat "$out/DIAG_STATUS.txt"
  fi
  done_runs=$((done_runs + 1))
done

# Early read on interference only; the stored-run comparison is done locally.
: >"$KEEP/meta/REPRO_STATUS.txt"
for seed in 202 101 303; do
  for case_id in stairs_15_down rough_lateral; do
    a="$KEEP/plain/cases/seed_${seed}/$case_id/steps.csv"
    b="$KEEP/diag/cases/seed_${seed}/$case_id/steps.csv"
    cmp -s "$a" "$b" && r=IDENTICAL || r=DIFFERENT
    echo "PLAIN_VS_DIAG_seed_${seed}_${case_id}=$r" >>"$KEEP/meta/REPRO_STATUS.txt"
  done
done
cat "$KEEP/meta/REPRO_STATUS.txt"
printf 'RUNS_DONE=%s\nRUNS_PLANNED=%s\nVIDEOS_WITH_FILE=%s\nVIDEOS_PLANNED=%s\n' \
  "$done_runs" "${#RUNS[@]}" "$videos_with_file" "${#VIDEOS[@]}" >"$KEEP/RUNNER_STATUS.txt"
printf 'RUNNER_END=%s\n' "$(date -Is)" >>"$KEEP/meta/RUN_TIMES.txt"
package_result COMPLETE_12_OF_12
trap - EXIT
echo "$DONE_MARKER"
