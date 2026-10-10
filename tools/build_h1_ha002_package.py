#!/usr/bin/env python3
"""Build H-A002: matched 1,000-iteration action-rate control/candidate study."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H1 = ROOT / "workspace/training/humanoid"
OUT = H1 / "upload/H-A002/current"
NAME = "H_A002_ACTION_RATE_M0P002_v2.zip"
PREFIX = "h1_ha002/"
FIXED_TIME = (2026, 10, 10, 0, 0, 0)
BASE = -0.0005
CANDIDATE = -0.002
RUN06_MODEL = H1 / "_eval_run06/model_best.pt"
RUN06_SHA = "8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636"
ORIGINAL_COMMIT = "e288246"
ORIGINALS = (
    "train.py", "play.py", "h1_task/__init__.py", "h1_task/_finalize.py",
    "h1_task/agent_cfg.py", "h1_task/env_cfg.py",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def git_bytes(relative: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{ORIGINAL_COMMIT}:workspace/training/humanoid/{relative}"],
        cwd=ROOT,
    )


def reward_source(value: float) -> bytes:
    source = lf(H1 / "_bootstrap/humanoid_rewards.py").decode("utf-8")
    old = '"action_rate_l2":      -0.0005,'
    new = f'"action_rate_l2":      {value},'
    if source.count(old) != 1:
        raise ValueError("action_rate_l2 baseline line changed")
    return source.replace(old, new).encode("utf-8")


RUNNER = r'''#!/usr/bin/env bash
set -euo pipefail
ROOT=${H1_ROOT:-/workspace/training/humanoid}
ISAACLAB=${ISAACLAB_SH:-/workspace/IsaacLab/isaaclab.sh}
PKG="$ROOT/h1_ha002"
KEEP=/workspace/_keep/H_A002_ACTION_RATE_M0P002
RESULT=/workspace/_keep/H_A002_ACTION_RATE_M0P002_RESULT.zip
NO_TMUX=${NO_TMUX:-0}
TMUX_NAME=h1_ha002_action_rate
SEEDS=(101 202 303)
ARMS=(control candidate)

py_cmd() {
  [[ -x /workspace/isaaclab_venv/bin/python ]] && { echo /workspace/isaaclab_venv/bin/python; return; }
  [[ -x /workspace/isaaclab_venv/Scripts/python.exe ]] && { echo /workspace/isaaclab_venv/Scripts/python.exe; return; }
  command -v python3 >/dev/null 2>&1 && { echo python3; return; }
  command -v python >/dev/null 2>&1 && { echo python; return; }
  echo '[FAIL] Python is required for identity and result packaging.' >&2; return 1
}

cleanup_runtime() {
  local rc=0 reward_want reward_got
  set +e
  restore_originals || rc=1
  cp -f "$PKG/rewards/control/humanoid_rewards.py" "$ROOT/humanoid_rewards.py" || rc=1
  reward_want=$(sha256sum "$PKG/rewards/control/humanoid_rewards.py" | awk '{print $1}')
  reward_got=$(sha256sum "$ROOT/humanoid_rewards.py" | awk '{print $1}')
  [[ "$reward_got" == "$reward_want" ]] || rc=1
  set -e
  return "$rc"
}

snapshot_exported() {
  mkdir -p "$KEEP/pre_run_exported"
  : >"$KEEP/pre_run_exported/state.tsv"
  local rel
  for rel in model_best.pt env.yaml policy.pt play_video.mp4 report.html; do
    if [[ -f "$ROOT/exported/$rel" ]]; then
      cp -a "$ROOT/exported/$rel" "$KEEP/pre_run_exported/$rel"
      printf '%s\tpresent\n' "$rel" >>"$KEEP/pre_run_exported/state.tsv"
    else
      printf '%s\tabsent\n' "$rel" >>"$KEEP/pre_run_exported/state.tsv"
    fi
  done
  (cd "$KEEP/pre_run_exported" && find . -maxdepth 1 -type f ! -name state.tsv ! -name snapshot.sha256 -print0 | sort -z | xargs -0 -r sha256sum >snapshot.sha256)
}

restore_exported() {
  local state="$KEEP/pre_run_exported/state.tsv"
  [[ -s "$state" ]] || return 0
  local rel presence
  while IFS=$'\t' read -r rel presence; do
    if [[ "$presence" == present ]]; then
      mkdir -p "$ROOT/exported"
      cp -a "$KEEP/pre_run_exported/$rel" "$ROOT/exported/$rel"
      [[ "$(sha256sum "$ROOT/exported/$rel" | awk '{print $1}')" == "$(sha256sum "$KEEP/pre_run_exported/$rel" | awk '{print $1}')" ]] || return 1
    else
      rm -f -- "$ROOT/exported/$rel"
      [[ ! -e "$ROOT/exported/$rel" ]] || return 1
    fi
  done <"$state"
  [[ ! -s "$KEEP/pre_run_exported/snapshot.sha256" ]] || (cd "$KEEP/pre_run_exported" && sha256sum -c snapshot.sha256)
}

package_result() {
  local label=$1
  mkdir -p "$KEEP"
  (cd "$KEEP" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum >SHA256SUMS.txt)
  rm -f -- "$RESULT.tmp"
  local py; py=$(py_cmd)
  "$py" - "$KEEP" "$RESULT.tmp" <<'PY'
import pathlib, sys, zipfile
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
    for p in sorted(root.rglob('*')):
        if p.is_file(): z.write(p, pathlib.Path(root.name)/p.relative_to(root))
PY
  mv "$RESULT.tmp" "$RESULT"
  sha256sum "$RESULT" >"$RESULT.sha256"
  echo "[PACKAGE_$label] $RESULT"
}

restore_originals() {
  local rel rc=0
  while read -r digest rel; do
    mkdir -p "$ROOT/$(dirname "$rel")" || rc=1
    cp -f "$PKG/original/$rel" "$ROOT/$rel" || rc=1
    echo "$digest  $ROOT/$rel" | sha256sum -c - || rc=1
  done <"$PKG/ORIGINAL_SHA256SUMS.txt"
  return "$rc"
}

preflight() {
  [[ -x "$ISAACLAB" ]] || { echo "[FAIL] IsaacLab launcher missing: $ISAACLAB"; exit 2; }
  command -v nvidia-smi >/dev/null 2>&1 || { echo '[FAIL] nvidia-smi missing'; exit 2; }
  pgrep -af 'train.py|play.py' >/dev/null && { echo '[BLOCKED] existing train/play process'; exit 2; } || true
  restore_originals
  cp -f "$PKG/rewards/control/humanoid_rewards.py" "$ROOT/humanoid_rewards.py"
  echo '8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636  '"$PKG/model_run06.pt" | sha256sum -c -
  mkdir -p "$KEEP/preflight"; local marker="$KEEP/preflight.marker"; touch "$marker"
  NCRC_EVAL_OUT="$KEEP/preflight" NCRC_EVAL_STEPS=2 "$ISAACLAB" -p "$PKG/h1_eval_entry.py" \
    --task Humanoid-v0 --num_envs 1 --headless --checkpoint "$PKG/model_run06.pt" \
    agent.seed=42 env.scene.terrain.terrain_type=plane env.curriculum.terrain_levels=null \
    env.commands.base_velocity.heading_command=false env.commands.base_velocity.rel_standing_envs=0.0 \
    env.commands.base_velocity.resampling_time_range='[1000.0,1000.0]' \
    env.commands.base_velocity.ranges.lin_vel_x='[0.0,0.0]' \
    env.commands.base_velocity.ranges.lin_vel_y='[0.0,0.0]' \
    env.commands.base_velocity.ranges.ang_vel_z='[0.0,0.0]'
  validate_eval "$KEEP/preflight" 2 1 "$marker" || { echo '[FAIL] H1 asset/config preflight incomplete'; exit 3; }
}

validate_eval() {
  local out=$1 steps=$2 envs=$3 marker=$4 py; py=$(py_cmd)
  [[ -s "$out/summary.json" && -s "$out/steps.csv" && -s "$out/STATUS.txt" ]] || return 1
  [[ "$out/summary.json" -nt "$marker" && "$out/steps.csv" -nt "$marker" && "$out/STATUS.txt" -nt "$marker" ]] || return 1
  grep -qx 'EVAL_RC=0' "$out/STATUS.txt" || return 1
  "$py" - "$out/summary.json" "$steps" "$envs" <<'PY'
import json, sys
s=json.load(open(sys.argv[1], encoding='utf-8')); steps=int(sys.argv[2]); envs=int(sys.argv[3])
if s.get('completed') is not True or s.get('steps') != steps or s.get('rows') != steps * envs:
    raise SystemExit(1)
PY
}

validate_fresh_training_outputs() {
  local root=$1 marker=$2 run_dir=$3 reward=$4 py model_sha env_reward
  [[ -s "$root/exported/model_best.pt" && -s "$root/exported/env.yaml" && -s "$root/exported/report.html" ]] || return 1
  [[ "$root/exported/model_best.pt" -nt "$marker" && "$root/exported/env.yaml" -nt "$marker" && "$root/exported/report.html" -nt "$marker" ]] || return 1
  model_sha=$(sha256sum "$root/exported/model_best.pt" | awk '{print $1}')
  VALID_SELECTED_MODEL=$(find "$run_dir" -maxdepth 1 -type f -name 'model_[0-9]*.pt' -print0 | xargs -0 -r sha256sum | awk -v want="$model_sha" '$1 == want {print $2; exit}')
  [[ -n "$VALID_SELECTED_MODEL" ]] || return 1
  VALID_SELECTED_ITER=$(basename "$VALID_SELECTED_MODEL"); VALID_SELECTED_ITER=${VALID_SELECTED_ITER#model_}; VALID_SELECTED_ITER=${VALID_SELECTED_ITER%.pt}
  VALID_MODEL_SHA=$model_sha
  py=$(py_cmd)
  env_reward=$("$py" - "$root/exported/env.yaml" <<'PY'
import sys, yaml
data=yaml.unsafe_load(open(sys.argv[1], encoding='utf-8'))
terms=data['rewards'] if 'rewards' in data else data['env']['rewards']
node=terms['action_rate_l2']
print(node['weight'] if isinstance(node, dict) else node.weight)
PY
  ) || return 1
  "$py" - "$env_reward" "$reward" <<'PY'
import math, sys
raise SystemExit(0 if math.isclose(float(sys.argv[1]), float(sys.argv[2]), rel_tol=0, abs_tol=1e-12) else 1)
PY
}

train_arm() {
  local arm=$1 reward=$2
  local marker="$KEEP/$arm/session_start.marker"
  mkdir -p "$KEEP/$arm/training" "$KEEP/$arm/exported" "$KEEP/$arm/logs"
  cp -f "$PKG/rewards/$arm/humanoid_rewards.py" "$ROOT/humanoid_rewards.py"
  grep -Fq '"action_rate_l2":      '"$reward"',' "$ROOT/humanoid_rewards.py" || { echo "[FAIL] $arm reward staging"; exit 4; }
  touch "$marker"
  set +e
  NO_AUTO_SUBMIT=1 PYTHONUTF8=1 PYTHONIOENCODING=utf-8 "$ISAACLAB" -p "$ROOT/train.py" \
    --task Humanoid-v0 --num_envs 4096 --max_iterations 1000 --headless agent.seed=42 \
    2>&1 | tee "$KEEP/$arm/train.log"
  local rc=${PIPESTATUS[0]}
  set -e
  [[ "$rc" == 0 ]] || { echo "[FAIL] $arm training rc=$rc"; exit 5; }
  local run_dir
  run_dir=$(find "$ROOT/logs/rsl_rl/humanoid" -mindepth 1 -maxdepth 1 -type d -newer "$marker" -print | sort | tail -n 1)
  [[ -n "$run_dir" ]] || { echo "[FAIL] $arm fresh run_dir missing"; exit 6; }
  validate_fresh_training_outputs "$ROOT" "$marker" "$run_dir" "$reward" || { echo "[FAIL] $arm stale/mismatched training outputs"; exit 6; }
  local selected_model=$VALID_SELECTED_MODEL selected_iter=$VALID_SELECTED_ITER model_sha=$VALID_MODEL_SHA py
  py=$(py_cmd)
  cp -a "$ROOT/exported/model_best.pt" "$KEEP/$arm/training/model_best.pt"
  cp -a "$ROOT/exported/env.yaml" "$KEEP/$arm/training/env.yaml"
  cp -a "$ROOT/humanoid_rewards.py" "$KEEP/$arm/training/humanoid_rewards.py"
  cp -a "$run_dir"/. "$KEEP/$arm/logs/"
  [[ -s "$ROOT/exported/report.html" && "$ROOT/exported/report.html" -nt "$marker" ]] || { echo "[FAIL] $arm REPORT_REQUIRED_NOT_ACQUIRED"; exit 7; }
  cp -a "$ROOT/exported/report.html" "$KEEP/$arm/exported/report.html"
  sha256sum "$KEEP/$arm/training/model_best.pt" "$KEEP/$arm/training/env.yaml" "$KEEP/$arm/training/humanoid_rewards.py" "$KEEP/$arm/exported/report.html" >"$KEEP/$arm/identity.sha256"
  "$py" - "$KEEP/$arm/identity.json" "$arm" "$reward" "$run_dir" "$selected_iter" \
    "$KEEP/$arm/training/model_best.pt" "$KEEP/$arm/training/env.yaml" "$KEEP/$arm/training/humanoid_rewards.py" "$PKG/eval_telemetry.py" <<'PY'
import hashlib, json, pathlib, sys
out, arm, reward, run_dir, selected_iter, model, env, reward_file, evaluator = sys.argv[1:]
def digest(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
pathlib.Path(out).write_text(json.dumps({
  'arm': arm, 'action_rate_l2': float(reward), 'fresh_run_dir': run_dir,
  'selected_iter': int(selected_iter), 'model_sha256': digest(model),
  'env_sha256': digest(env), 'reward_sha256': digest(reward_file),
  'evaluator_sha256': digest(evaluator),
}, indent=2) + '\n', encoding='utf-8')
PY
  printf 'ARM=%s\nACTION_RATE_L2=%s\nTRAIN_RC=0\nRUN_DIR=%s\nSELECTED_ITER=%s\nMODEL_SHA=%s\nREPORT_STATUS=REPORT_ACQUIRED\n' "$arm" "$reward" "$run_dir" "$selected_iter" "$model_sha" >"$KEEP/$arm/TRAIN_STATUS.txt"
}

terrain_args() {
  case "$1" in
    plane) printf '%s\n' env.scene.terrain.terrain_type=plane env.curriculum.terrain_levels=null ;;
    rough) printf '%s\n' env.scene.terrain.terrain_type=generator env.curriculum.terrain_levels=null env.scene.terrain.terrain_generator.curriculum=false env.scene.terrain.terrain_generator.num_rows=1 env.scene.terrain.terrain_generator.num_cols=4 env.scene.terrain.terrain_generator.difficulty_range='[1.0,1.0]' env.scene.terrain.max_init_terrain_level=0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.boxes.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0 env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range='[0.02,0.10]' env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0 ;;
    slope_up) printf '%s\n' env.scene.terrain.terrain_type=generator env.curriculum.terrain_levels=null env.scene.terrain.terrain_generator.curriculum=false env.scene.terrain.terrain_generator.num_rows=1 env.scene.terrain.terrain_generator.num_cols=4 env.scene.terrain.terrain_generator.difficulty_range='[1.0,1.0]' env.scene.terrain.max_init_terrain_level=0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.boxes.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=1.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.slope_range='[0.17632698,0.17632698]' ;;
    slope_down) printf '%s\n' env.scene.terrain.terrain_type=generator env.curriculum.terrain_levels=null env.scene.terrain.terrain_generator.curriculum=false env.scene.terrain.terrain_generator.num_rows=1 env.scene.terrain.terrain_generator.num_cols=4 env.scene.terrain.terrain_generator.difficulty_range='[1.0,1.0]' env.scene.terrain.max_init_terrain_level=0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.boxes.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=1.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.slope_range='[0.17632698,0.17632698]' env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0 ;;
  esac
}

run_eval() {
  local arm=$1 seed=$2 name=$3 vx=$4 vy=$5 wz=$6 terrain=$7 push=$8
  local out="$KEEP/$arm/evaluation/seed_$seed/$name"
  local marker="$KEEP/$arm/evaluation/seed_${seed}/${name}.marker"
  mkdir -p "$out"; touch "$marker"
  mapfile -t targs < <(terrain_args "$terrain")
  local -a cmd=("$ISAACLAB" -p "$PKG/h1_eval_entry.py" --task Humanoid-v0 --num_envs 32 --headless --checkpoint "$KEEP/$arm/training/model_best.pt" "agent.seed=$seed" env.commands.base_velocity.heading_command=false env.commands.base_velocity.rel_standing_envs=0.0 env.commands.base_velocity.resampling_time_range='[1000.0,1000.0]' "env.commands.base_velocity.ranges.lin_vel_x=[$vx,$vx]" "env.commands.base_velocity.ranges.lin_vel_y=[$vy,$vy]" "env.commands.base_velocity.ranges.ang_vel_z=[$wz,$wz]" "${targs[@]}")
  [[ "$push" == 0 ]] || cmd+=(--push "$push")
  NCRC_EVAL_OUT="$out" NCRC_EVAL_STEPS=1000 "${cmd[@]}" >"$out/play.log" 2>&1
  validate_eval "$out" 1000 32 "$marker" || { echo "[FAIL] incomplete eval $arm $seed $name"; exit 8; }
  local py; py=$(py_cmd)
  "$py" - "$KEEP/$arm/identity.json" "$out/identity.json" "$seed" "$name" <<'PY'
import json, pathlib, sys
identity=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
identity.update({'evaluation_seed': int(sys.argv[3]), 'evaluation_case': sys.argv[4], 'evaluation_steps': 1000})
pathlib.Path(sys.argv[2]).write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8')
PY
}

evaluate_arm() {
  local arm=$1 reward=$2 seed
  cp -f "$PKG/rewards/$arm/humanoid_rewards.py" "$ROOT/humanoid_rewards.py"
  for seed in "${SEEDS[@]}"; do
    run_eval "$arm" "$seed" plane_vx0p75 0.75 0 0 plane 0; run_eval "$arm" "$seed" plane_vx1p00 1 0 0 plane 0; run_eval "$arm" "$seed" plane_vx1p25 1.25 0 0 plane 0
    run_eval "$arm" "$seed" rough_vx0p75 0.75 0 0 rough 0; run_eval "$arm" "$seed" rough_vx1p00 1 0 0 rough 0
    run_eval "$arm" "$seed" turn_vx0p50_L 0.5 0 0.5 plane 0; run_eval "$arm" "$seed" turn_vx0p50_R 0.5 0 -0.5 plane 0; run_eval "$arm" "$seed" turn_vx1p00_L 1 0 0.5 plane 0; run_eval "$arm" "$seed" turn_vx1p00_R 1 0 -0.5 plane 0
    run_eval "$arm" "$seed" H1_stand 0 0 0 plane 0; run_eval "$arm" "$seed" H2_forward 0.75 0 0 plane 0; run_eval "$arm" "$seed" H3_left 0 0.3 0 plane 0; run_eval "$arm" "$seed" H3_right 0 -0.3 0 plane 0
    run_eval "$arm" "$seed" H4_left 0.5 0.15 0.5 plane 0; run_eval "$arm" "$seed" H4_right 0.5 -0.15 -0.5 plane 0; run_eval "$arm" "$seed" H5_rough 0.5 0 0 rough 0; run_eval "$arm" "$seed" H6_plus10 0.5 0 0 slope_up 0; run_eval "$arm" "$seed" H6_minus10 0.5 0 0 slope_down 0; run_eval "$arm" "$seed" H7_push 0 0 0 plane 0.5
  done
  [[ "$(find "$KEEP/$arm/evaluation" -name summary.json | wc -l)" == 57 ]] || { echo "[FAIL] $arm expected 57 telemetry cases"; exit 9; }
  local py; py=$(py_cmd)
  "$py" - "$KEEP/$arm/identity.json" "$KEEP/$arm/evaluation/identity.json" <<'PY'
import json, pathlib, sys
identity=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
identity.update({'evaluation_case_count': 57, 'evaluation_seeds': [101, 202, 303], 'evaluation_steps': 1000})
pathlib.Path(sys.argv[2]).write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8')
PY
}

video_case() {
  local arm=$1 name=$2 vx=$3 vy=$4 wz=$5 terrain=$6 push=$7
  mapfile -t targs < <(terrain_args "$terrain")
  local -a cmd=("$ISAACLAB" -p "$ROOT/play.py" --task Humanoid-v0 --num_envs 4 --headless --video --video_length 1000 --enable_cameras agent.seed=101 env.commands.base_velocity.heading_command=false env.commands.base_velocity.rel_standing_envs=0.0 env.commands.base_velocity.resampling_time_range='[1000.0,1000.0]' "env.commands.base_velocity.ranges.lin_vel_x=[$vx,$vx]" "env.commands.base_velocity.ranges.lin_vel_y=[$vy,$vy]" "env.commands.base_velocity.ranges.ang_vel_z=[$wz,$wz]" "${targs[@]}")
  [[ "$push" == 0 ]] || cmd+=(--push "$push")
  rm -f "$ROOT/exported/play_video.mp4" "$ROOT/exported/policy.pt"
  "${cmd[@]}" >"$KEEP/$arm/videos/${name}.log" 2>&1
  [[ -s "$ROOT/exported/play_video.mp4" ]] || { echo "[FAIL] video $arm $name"; exit 10; }
  cp -a "$ROOT/exported/play_video.mp4" "$KEEP/$arm/videos/${name}.mp4"
  local model_sha; model_sha=$(sha256sum "$KEEP/$arm/training/model_best.pt" | awk '{print $1}')
  printf '{"arm":"%s","video_case":"%s","video_seed":101,"checkpoint_sha256":"%s"}\n' "$arm" "$name" "$model_sha" >"$KEEP/$arm/videos/${name}.identity.json"
}

videos_arm() {
  local arm=$1; mkdir -p "$KEEP/$arm/videos"
  cp -f "$KEEP/$arm/training/model_best.pt" "$ROOT/exported/model_best.pt"; cp -f "$KEEP/$arm/training/env.yaml" "$ROOT/exported/env.yaml"; cp -f "$PKG/rewards/$arm/humanoid_rewards.py" "$ROOT/humanoid_rewards.py"
  video_case "$arm" H1_stand 0 0 0 plane 0; video_case "$arm" H2_forward 0.75 0 0 plane 0; video_case "$arm" H3_left 0 0.3 0 plane 0; video_case "$arm" H3_right 0 -0.3 0 plane 0
  video_case "$arm" H4_left 0.5 0.15 0.5 plane 0; video_case "$arm" H4_right 0.5 -0.15 -0.5 plane 0; video_case "$arm" H5_rough 0.5 0 0 rough 0; video_case "$arm" H6_plus10 0.5 0 0 slope_up 0; video_case "$arm" H6_minus10 0.5 0 0 slope_down 0; video_case "$arm" H7_push 0 0 0 plane 0.5
  [[ "$(find "$KEEP/$arm/videos" -name '*.mp4' | wc -l)" == 10 ]] || { echo "[FAIL] $arm video count"; exit 10; }
  local py; py=$(py_cmd)
  "$py" - "$KEEP/$arm/identity.json" "$KEEP/$arm/videos/identity.json" <<'PY'
import json, pathlib, sys
identity=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
identity.update({'video_seed': 101, 'video_count': 10, 'video_checkpoint_sha256': identity['model_sha256']})
pathlib.Path(sys.argv[2]).write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8')
PY
}

if [[ "${1:-}" != --inner ]]; then
  [[ "$NO_TMUX" == 1 ]] && exec bash "$PKG/server_run_h1_ha002.sh" --inner
  command -v tmux >/dev/null 2>&1 || { echo '[FAIL] tmux missing; use NO_TMUX=1'; exit 2; }
  tmux new-session -d -s "$TMUX_NAME" "cd '$ROOT' && bash '$PKG/server_run_h1_ha002.sh' --inner"
  echo "[STARTED] $TMUX_NAME"; echo "[RESULT] $RESULT"; exit 0
fi

[[ ! -e "$KEEP" ]] || { echo "[BLOCKED] nonempty or stale H-A002 KEEP already exists: $KEEP"; exit 2; }
mkdir -p "$KEEP/meta"; exec > >(tee -a "$KEEP/launcher.log") 2>&1
cp -f "$PKG/experiment.json" "$PKG/PACKAGE_SHA256SUMS.txt" "$PKG/eval_telemetry.py" "$PKG/h1_eval_entry.py" "$KEEP/meta/"
sha256sum "$KEEP/meta/experiment.json" "$KEEP/meta/PACKAGE_SHA256SUMS.txt" "$KEEP/meta/eval_telemetry.py" "$KEEP/meta/h1_eval_entry.py" >"$KEEP/meta/audit.sha256"
trap 'rc=$?; trap - EXIT; er=0; cr=0; restore_exported || er=$?; cleanup_runtime || cr=$?; printf "RUNNER_RC=%s\nEXPORTED_RESTORE_RC=%s\nCLEANUP_RC=%s\nFAILED_AT=%s\n" "$rc" "$er" "$cr" "$(date -Is)" >"$KEEP/RUNNER_STATUS.txt"; package_result PARTIAL || true; exit "$rc"' EXIT
snapshot_exported
preflight
train_arm control -0.0005
train_arm candidate -0.002
evaluate_arm control -0.0005; evaluate_arm candidate -0.002
videos_arm control; videos_arm candidate
restore_exported
cleanup_runtime
printf 'RUNNER_RC=0\nTRAIN_ARMS=2/2\nEVAL_CASES=114/114\nVIDEOS=20/20\nREPORTS=2/2\nCOMPLETED_AT=%s\n' "$(date -Is)" >"$KEEP/RUNNER_STATUS.txt"
package_result FULL
trap - EXIT
echo '[DONE] H-A002 matched 1000-iteration control/candidate collection complete.'
'''


def experiment() -> dict:
    return {
        "schema": "h1_ha002_action_rate_matched_v1",
        "work_id": "H-A002",
        "classification": "exploratory_mechanism_test_not_adoption",
        "single_change": {"name": "action_rate_l2", "control": BASE, "candidate": CANDIDATE},
        "value_basis": "preplanned interior value at the lower quarter of the documented -0.008..-0.0005 range; not an optimum or safety claim",
        "observed_trigger": "P0 mean vx ratios were near 1 with zero falls, while selected high-command yaw RMSE exceeded its within-policy +5% reference threshold by about 6.15%..8.44%.",
        "causal_limit": "No action/joint channel was recorded, so command jitter versus contact-driven disturbance remains unresolved.",
        "hypothesis": "A fourfold action-change penalty may reduce yaw variation.",
        "competing": "It may make motion sluggish or fail if the variation is contact-driven.",
        "alternatives": {"-0.001": "weaker contrast, not proven safer", "-0.008": "range endpoint with stronger sluggishness risk", "track_lin_vel_xy_exp=1.5": "targets an axis not deficient in P0", "track_ang_vel_z_exp_up": "could force oscillation; prior cross-reward history is adverse"},
        "training": {"arms": ["control", "candidate"], "from_scratch": True, "seed": 42, "iterations_each": 1000, "num_envs": 4096},
        "evaluation": {"seeds": [101, 202, 303], "p0_cases_each_arm": 27, "h1_h7_cases_each_arm": 30, "telemetry_total": 114, "videos_each_arm": 10},
        "decision": "Compare only matched 1000-iteration arms; retain Run06. No automatic 3000/10000 promotion.",
    }


def entries() -> dict[str, bytes]:
    model = RUN06_MODEL.read_bytes()
    if sha(model) != RUN06_SHA:
        raise ValueError("Run06 preflight model SHA mismatch")
    originals = {rel: git_bytes(rel) for rel in ORIGINALS}
    sums = "".join(f"{sha(originals[rel])}  {rel}\n" for rel in ORIGINALS).encode()
    files = {
        "server_run_h1_ha002.sh": RUNNER.encode(),
        "h1_eval_entry.py": lf(H1 / "h1_ha001/h1_eval_entry.py"),
        "eval_telemetry.py": lf(H1 / "eval_telemetry.py"),
        "rewards/control/humanoid_rewards.py": reward_source(BASE),
        "rewards/candidate/humanoid_rewards.py": reward_source(CANDIDATE),
        "model_run06.pt": model,
        "ORIGINAL_SHA256SUMS.txt": sums,
        "experiment.json": (json.dumps(experiment(), ensure_ascii=False, indent=2) + "\n").encode(),
        "README.txt": (
            "H-A002 v2 runs matched from-scratch 1000-iteration control (-0.0005) and candidate (-0.002) arms.\n"
            "Run: cd /workspace/training/humanoid && unzip -o H_A002_ACTION_RATE_M0P002_v2.zip && "
            "NO_TMUX=1 H1_ROOT=/workspace/training/humanoid ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh "
            "bash h1_ha002/server_run_h1_ha002.sh\nResult: /workspace/_keep/H_A002_ACTION_RATE_M0P002_RESULT.zip (+ .sha256).\n"
        ).encode(),
    }
    files.update({f"original/{rel}": data for rel, data in originals.items()})
    manifest = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items())).encode()
    files["PACKAGE_SHA256SUMS.txt"] = manifest
    return files


def build(out: Path = OUT) -> Path:
    files = entries()
    out.mkdir(parents=True, exist_ok=True)
    target = out / NAME
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(PREFIX + name, FIXED_TIME)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    (out / f"{NAME}.sha256").write_bytes(f"{sha(target.read_bytes())}  {NAME}\n".encode())
    return target


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    result = build(destination)
    print(result)
    print(sha(result.read_bytes()))
