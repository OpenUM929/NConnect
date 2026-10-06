# PC2 탐색트리 판독 — q2_ang_vel_xy_l2_m0p06

- 노드: `workspace\_keep\go2_g_a062_pc2_q2_ang_vel_xy_l2_m0p06`
- 비교 부모(q0_lin_vel_z_l2_m1p5): `workspace\_keep\go2_g_a062_pc2_q0_lin_vel_z_l2_m1p5`
- 비교 부모 대비 변경: {'ang_vel_xy_l2': -0.06}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'T_G5_stairs15_ge1']
  - common_losses: ['S_stairs10_survival', 'S_yaw_right_xy_rmse', 'S_forward_nominal_cmd_error', 'S_G7_dr_survival']
  - partial_seed_losses: {'T_G5_stairs15_progress_ratio': ['202', '303'], 'S_stairs10_progress_ratio': ['303'], 'S_push_neg_y_falls': ['101', '303'], 'S_push_neg_y_survival': ['101', '303'], 'S_push_neg_y_recovery_upright': ['101', '303'], 'S_rough_forward_motion': ['202', '303'], 'S_G4_slope_plus_20_survival': ['202', '303'], 'S_G7_dr_xy_rmse': ['101', '303']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 22→12; 202: 28→16; 303: 26→13 |
| T_G3_rough_lateral_motion | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: {'abs_error': 0.22769287979936148, 'rmse': 0.2550146949677173}→{'abs_error': 0.162828295621974, 'rmse': 0.22211180199294264}; 202: {'abs_error': 0.22529975394061957, 'rmse': 0.2578220644725718}→{'abs_error': 0.17327482790650137, 'rmse': 0.22278210154528302}; 303: {'abs_error': 0.22051778723335363, 'rmse': 0.2620872835357513}→{'abs_error': 0.14849736052928408, 'rmse': 0.20466471864102923} |
| T_G5_stairs15_ge1 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0→2; 202: 0→3; 303: 0→5 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| T_G5_stairs15_progress_ratio | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.15541971636597016→0.15958359235810327; 202: 0.14303445603232837→0.14059167173175952; 303: 0.14242761529444392→0.14183689985884143 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'better', '303': 'same'} | 101: 0.0→0.0; 202: 0.0→0.03125; 303: 0.0→0.0 |
| S_stairs10_ge2 | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 10→14; 202: 10→17; 303: 10→12 |
| S_stairs10_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.5→0.34375; 202: 0.625→0.40625; 303: 0.4375→0.25 |
| S_stairs10_progress_ratio | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'worse'} | 101: 0.19715209687437166→0.2219198294662053; 202: 0.19963763798453169→0.21681499862895715; 303: 0.18768355708979662→0.18207148282683927 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1578533065838916→0.12937813881758997; 202: 0.155896481903809→0.12796253395259943; 303: 0.15929572096748684→0.12999427708016187 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08241003856055727→0.09130370104617824; 202: 0.08225879966896964→0.09055218205700086; 303: 0.08318119530829639→0.09128577003421524 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'better', '303': 'same'} | 101: 0→0; 202: 1→0; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'better', '303': 'same'} | 101: 1.0→1.0; 202: 0.96875→1.0; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09881454270256791→0.0837676977075055; 202: 0.09999638073158008→0.0858981766303729; 303: 0.09485108181626041→0.08266744066339833 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'better', '303': 'better'} | 101: 0→0; 202: 1→0; 303: 1→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'better', '303': 'better'} | 101: 1.0→1.0; 202: 0.96875→1.0; 303: 0.96875→1.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09700456835313767→0.08131045907618001; 202: 0.10087653402086463→0.08638130750962232; 303: 0.09820890244706314→0.0836286193939346 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09810522121453173→0.08527900097160046; 202: 0.09518145861490816→0.08270413831338583; 303: 0.09197216556397649→0.08202637516767464 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 0→1; 202: 1→0; 303: 0→1 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 1.0→0.96875; 202: 0.96875→1.0; 303: 1.0→0.96875 |
| S_push_neg_y_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.09339924728272127→0.08634464273612162; 202: 0.0992218749147261→0.08466989062583695; 303: 0.09708420807088516→0.08570302892741523 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 1.0→0.9921875; 202: 1.0→1.0; 303: 1.0→0.984375 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 3→3; 202: 2→2; 303: 3→3 |
| S_rough_forward_motion | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.1934537293079232, 'rmse': 0.299538143941292}→{'abs_error': 0.1538493783354949, 'rmse': 0.26976343361386135}; 202: {'abs_error': 0.16004909291077557, 'rmse': 0.2672241344637713}→{'abs_error': 0.1822250179184886, 'rmse': 0.29590568727793887}; 303: {'abs_error': 0.16686083529333973, 'rmse': 0.2723031288173912}→{'abs_error': 0.19600693280567993, 'rmse': 0.30404357211995464} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.016257441871260325→0.01666942778680669; 202: 0.018666657095676942→0.0190382662425308; 303: 0.014738288237468145→0.016504815156130448 |
| S_G4_slope_plus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→0.9375; 303: 1.0→0.9375 |
| S_G4_slope_plus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.243029336491582→0.11459695733338464; 202: 0.21327468071554134→0.16063576877179833; 303: 0.2818254828091102→0.17451588241395374 |
| S_G7_dr_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.96875→0.90625; 202: 0.90625→0.84375; 303: 0.96875→0.78125 |
| S_G7_dr_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 0.302088946222019→0.3163638039077807; 202: 0.3072689991696239→0.2844534942097651; 303: 0.2755554002667832→0.32783315600306506 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
