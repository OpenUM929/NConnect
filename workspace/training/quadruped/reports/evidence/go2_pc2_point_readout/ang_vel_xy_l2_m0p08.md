# PC2 점 판독 — ang_vel_xy_l2_m0p08

- 점: `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_ang_vel_xy_l2_m0p08`
- 직접 대조군(B1): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 점 자료 상태: COMPLETE (보상 snapshot OK, GPU 모델 NVIDIA GeForce RTX 5070)
- B1 자료 상태: COMPLETE (A048 대조 OK)
- 유지 조건·GPU 모델 비교: OK [] (GPU 모델이 같다는 확인이지 같은 PC·환경의 증명이 아니다(§18-3 WATCH).)
- sentinel: EVAL_LAYER_DIFFERS ['202/dr_seed_202']
- 정지 판정: MOVING
- 표적(험지 옆걸음 자세 낙상): TARGET_WORSENED 
  - seed 101: B1 13 → 점 16 (차 3)
  - seed 202: B1 16 → 점 23 (차 7)
  - seed 303: B1 12 → 점 20 (차 8)
- 이동·추종(rough_lateral): ALL_SEEDS_WORSE, 나빠진 seed ['101', '202', '303'], 과속 seed []
- 보호 stairs_10_ge2: COMMON_LOSS_OBSERVED (나빠진 seed ['101', '202', '303']; 101: 26→1, 202: 30→0, 303: 29→0)
  - seed 101 ≥2단 도달 뒤: B1 {'reached_ge2': 26, 'stalled_after_reach': 8, 'post_channel_terminated': 0, 'post_channel_height_only': 6, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 20, 'run_channel_terminated': 0, 'run_channel_height_only': 11, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 15} / 점 {'reached_ge2': 1, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 1, 'run_channel_terminated': 0, 'run_channel_height_only': 1, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0}
  - seed 202 ≥2단 도달 뒤: B1 {'reached_ge2': 30, 'stalled_after_reach': 11, 'post_channel_terminated': 0, 'post_channel_height_only': 7, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 23, 'run_channel_terminated': 0, 'run_channel_height_only': 11, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 19} / 점 {'reached_ge2': 0, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 0, 'run_channel_terminated': 0, 'run_channel_height_only': 0, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0}
  - seed 303 ≥2단 도달 뒤: B1 {'reached_ge2': 29, 'stalled_after_reach': 8, 'post_channel_terminated': 0, 'post_channel_height_only': 9, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 20, 'run_channel_terminated': 0, 'run_channel_height_only': 14, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 15} / 점 {'reached_ge2': 0, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 0, 'run_channel_terminated': 0, 'run_channel_height_only': 0, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0}
- 보호 stairs_15_ge2: COMMON_LOSS_OBSERVED (나빠진 seed ['101', '202', '303']; 101: 1→0, 202: 1→0, 303: 1→0)
  - seed 101 ≥2단 도달 뒤: B1 {'reached_ge2': 1, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 1, 'run_channel_terminated': 0, 'run_channel_height_only': 1, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0} / 점 {'reached_ge2': 0, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 0, 'run_channel_terminated': 0, 'run_channel_height_only': 0, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0}
  - seed 202 ≥2단 도달 뒤: B1 {'reached_ge2': 1, 'stalled_after_reach': 0, 'post_channel_terminated': 1, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 0, 'run_channel_terminated': 1, 'run_channel_height_only': 0, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0} / 점 {'reached_ge2': 0, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 0, 'run_channel_terminated': 0, 'run_channel_height_only': 0, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0}
  - seed 303 ≥2단 도달 뒤: B1 {'reached_ge2': 1, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 1, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 0, 'run_channel_terminated': 0, 'run_channel_height_only': 1, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0} / 점 {'reached_ge2': 0, 'stalled_after_reach': 0, 'post_channel_terminated': 0, 'post_channel_height_only': 0, 'post_channel_tilt_or_both': 0, 'post_channel_union_only': 0, 'post_channel_none': 0, 'run_channel_terminated': 0, 'run_channel_height_only': 0, 'run_channel_tilt_or_both': 0, 'run_channel_union_only': 0, 'run_channel_none': 0}
- 보호 yaw_right_falls: COMMON_LOSS_NOT_OBSERVED (나빠진 seed []; 101: 0→0, 202: 0→0, 303: 0→0)
- 보호 push_pos_x_falls: COMMON_LOSS_NOT_OBSERVED (나빠진 seed []; 101: 0→0, 202: 0→0, 303: 0→0)
- 보호 push_neg_x_falls: COMMON_LOSS_NOT_OBSERVED (나빠진 seed ['202']; 101: 0→0, 202: 0→1, 303: 0→0)
- 보호 push_pos_y_falls: COMMON_LOSS_NOT_OBSERVED (나빠진 seed ['303']; 101: 0→0, 202: 0→0, 303: 0→1)
- 보호 push_neg_y_falls: COMMON_LOSS_NOT_OBSERVED (나빠진 seed ['202']; 101: 0→0, 202: 0→1, 303: 0→0)
- 보호 rough_forward_falls: COMMON_LOSS_NOT_OBSERVED (나빠진 seed ['202', '303']; 101: 4→1, 202: 2→3, 303: 0→1)
- 보호 rough_forward_cmd_error: COMMON_LOSS_OBSERVED (나빠진 seed ['101', '202', '303']; 101: 0.14389231611321246→0.30272805373391054, 202: 0.10030702088473559→0.27857406183519606, 303: 0.12981202803889502→0.29977909257576213)
- 보호 forward_nominal_cmd_error: COMMON_LOSS_NOT_OBSERVED (나빠진 seed []; 101: 0.06584699518880566→0.011430885480030573, 202: 0.06588044092647338→0.006486895232412415, 303: 0.06613569222880822→0.01499028480954856)

**조합 분류: TARGET_WORSENED** — 그 방향의 바깥 점은 열지 않는다(영구 기각 아님).
- 결측 부분: []
- 세 seed 공통 손실 항목: ['stairs_10_ge2', 'stairs_15_ge2', 'rough_forward_cmd_error']
- 일부 seed 손실 항목: ['push_neg_x_falls', 'push_pos_y_falls', 'push_neg_y_falls', 'rough_forward_falls']
- 다음 점: 자동 선택 없음 — 표적·보호 결과와 남은 비용으로 Codex 가 정한다.
