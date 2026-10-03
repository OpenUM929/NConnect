#!/usr/bin/env bash
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
  VX=0 VY=0 WZ=0 PUSH_X= PUSH_Y= DR_MODE=0 TERRAIN_LABEL=plane
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
    rough_forward|rough_lateral)
      [[ "$case_id" == rough_lateral ]] && VY=0.30 || VX=0.50
      TERRAIN_LABEL=rough
      TERRAIN_ARGS=("${GEN_BASE[@]}" "${ZERO_TERRAINS[@]}"
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=1.0'
        'env.scene.terrain.terrain_generator.sub_terrains.random_rough.noise_range=[0.02,0.10]')
      ;;
    # G7 shared this branch with G3 and never set NCRC_EVAL_DR, so every dr_seed_*
    # case ran the identical configuration to rough_forward and its steps.csv came
    # out byte-identical.  G7 carries weight 0.10 and was rescoring G3.
    dr_seed_*)
      VX=0.50; DR_MODE=1
      TERRAIN_LABEL=rough_dr
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

# A substring test is not a value test.  measurement_contract carries the literal
# string "posture_gate_v2" on every summary, including one whose survival number
# is null because the posture channels were never read -- so the old
# `grep -q posture_gate_v2` passed on exactly the file it existed to reject.
# Check the decided fields, check that the coverage behind them is real, and
# check that the rows that were not observed could not have changed who fell, and
# check that the physics produced finite numbers at all: inf passes every
# threshold test in the gate, so an exploded step read as a perfectly upright robot.
