# PC2 탐색트리 판독 — q1_track_ang_vel_z_exp_p1p0

- 노드: `workspace\_keep\go2_g_a062_pc2_q1_track_ang_vel_z_exp_p1p0`
- 비교 부모(q0_lin_vel_z_l2_m1p5): `workspace\_keep\go2_g_a062_pc2_q0_lin_vel_z_l2_m1p5`
- 비교 부모 대비 변경: {'track_ang_vel_z_exp': 1.0}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G3_rough_lateral_motion']
  - common_losses: ['T_G5_stairs15_progress_ratio', 'S_stairs10_ge2', 'S_stairs10_survival', 'S_stairs10_progress_ratio', 'S_yaw_right_falls', 'S_yaw_right_survival', 'S_yaw_right_yaw_rmse', 'S_yaw_right_xy_rmse', 'S_push_pos_x_falls', 'S_push_pos_x_survival', 'S_push_pos_x_recovery_upright', 'S_push_neg_x_falls', 'S_push_neg_x_survival', 'S_push_neg_x_recovery_upright', 'S_push_pos_y_falls', 'S_push_pos_y_survival', 'S_push_pos_y_recovery_upright', 'S_push_neg_y_falls', 'S_push_neg_y_survival', 'S_push_neg_y_recovery_upright', 'S_rough_forward_falls', 'S_rough_forward_motion', 'S_forward_nominal_cmd_error', 'S_G4_slope_plus_20_survival', 'S_G4_slope_plus_20_xy_rmse', 'S_G7_dr_survival', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'T_G3_rough_lateral_falls': ['101']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'better'} | 101: 22→26; 202: 28→20; 303: 26→21 |
| T_G3_rough_lateral_motion | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: {'abs_error': 0.22769287979936148, 'rmse': 0.2550146949677173}→{'abs_error': 0.1982139455752679, 'rmse': 0.24869582592652922}; 202: {'abs_error': 0.22529975394061957, 'rmse': 0.2578220644725718}→{'abs_error': 0.21124675546699087, 'rmse': 0.25405730971617735}; 303: {'abs_error': 0.22051778723335363, 'rmse': 0.2620872835357513}→{'abs_error': 0.19660265882158182, 'rmse': 0.2544509327829815} |
| T_G5_stairs15_ge1 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15541971636597016→0.1048129672227589; 202: 0.14303445603232837→0.0925744891162759; 303: 0.14242761529444392→0.09316200389905141 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.0→0.0; 202: 0.0→0.0; 303: 0.0→0.0 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 10→0; 202: 10→0; 303: 10→0 |
| S_stairs10_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.5→0.0; 202: 0.625→0.0; 303: 0.4375→0.0 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.19715209687437166→0.12060847985940559; 202: 0.19963763798453169→0.10737897394328852; 303: 0.18768355708979662→0.11196913795688652 |
| S_yaw_right_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→32; 202: 0→32; 303: 0→32 |
| S_yaw_right_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.1578533065838916→0.2084659461275394; 202: 0.155896481903809→0.2043587059873799; 303: 0.15929572096748684→0.21164127910298794 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08241003856055727→0.2049945988709408; 202: 0.08225879966896964→0.2063544694874944; 303: 0.08318119530829639→0.20050811957968362 |
| S_push_pos_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→17; 202: 1→15; 303: 0→12 |
| S_push_pos_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.46875; 202: 0.96875→0.53125; 303: 1.0→0.625 |
| S_push_pos_x_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09881454270256791→0.07673065688427055; 202: 0.09999638073158008→0.07424028213057965; 303: 0.09485108181626041→0.07497354631680046 |
| S_push_pos_x_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.8671875; 202: 1.0→0.8828125; 303: 1.0→0.8984375 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→13; 202: 1→17; 303: 1→14 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.59375; 202: 0.96875→0.46875; 303: 0.96875→0.5625 |
| S_push_neg_x_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09700456835313767→0.07573523201741718; 202: 0.10087653402086463→0.07649752896262856; 303: 0.09820890244706314→0.076300180516984 |
| S_push_neg_x_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.9296875; 202: 1.0→0.8203125; 303: 1.0→0.96875 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→15; 202: 0→22; 303: 0→8 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.53125; 202: 1.0→0.3125; 303: 1.0→0.75 |
| S_push_pos_y_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09810522121453173→0.07902495515345119; 202: 0.09518145861490816→0.0766405344762591; 303: 0.09197216556397649→0.07375920169336914 |
| S_push_pos_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.875; 202: 1.0→0.828125; 303: 1.0→0.890625 |
| S_push_neg_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→12; 202: 1→19; 303: 0→12 |
| S_push_neg_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.625; 202: 0.96875→0.40625; 303: 1.0→0.625 |
| S_push_neg_y_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09339924728272127→0.07494725845978092; 202: 0.0992218749147261→0.07608008785248979; 303: 0.09708420807088516→0.07621971870731009 |
| S_push_neg_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.890625; 202: 1.0→0.859375; 303: 1.0→0.921875 |
| S_rough_forward_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 3→32; 202: 2→32; 303: 3→32 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.1934537293079232, 'rmse': 0.299538143941292}→{'abs_error': 0.46248554527507485, 'rmse': 0.47068699720196344}; 202: {'abs_error': 0.16004909291077557, 'rmse': 0.2672241344637713}→{'abs_error': 0.4512607156833088, 'rmse': 0.4639955443836718}; 303: {'abs_error': 0.16686083529333973, 'rmse': 0.2723031288173912}→{'abs_error': 0.4545309574433487, 'rmse': 0.46669636509304246} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.016257441871260325→0.12083638134485997; 202: 0.018666657095676942→0.1184195035061183; 303: 0.014738288237468145→0.11991396516828423 |
| S_G4_slope_plus_20_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_G4_slope_plus_20_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.243029336491582→0.4524536867509792; 202: 0.21327468071554134→0.44846302450149805; 303: 0.2818254828091102→0.45123635806630763 |
| S_G7_dr_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.96875→0.0; 202: 0.90625→0.0; 303: 0.96875→0.0 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.302088946222019→0.47035405874576225; 202: 0.3072689991696239→0.46746654262408033; 303: 0.2755554002667832→0.4735172992454919 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
