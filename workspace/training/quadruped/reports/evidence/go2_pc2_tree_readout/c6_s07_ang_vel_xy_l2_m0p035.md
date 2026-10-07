# PC2 탐색트리 판독 — c6_s07_ang_vel_xy_l2_m0p035

- 노드: `workspace\_keep\go2_g_a064_pc2_c6_s07_ang_vel_xy_l2_m0p035`
- 비교 부모(s07_feet_air_time_p0p35): `workspace\_keep\go2_g_a063_pc2_s07_feet_air_time_p0p35`
- 비교 부모 대비 변경: {'ang_vel_xy_l2': -0.035}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G5_stairs15_ge1', 'T_G5_stairs15_ge2', 'T_G5_stairs15_nonstall_after_ge2', 'T_G5_stairs15_progress_ratio', 'T_G5_stairs15_survival']
  - common_losses: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'S_push_pos_x_falls', 'S_push_pos_x_survival', 'S_push_neg_x_falls', 'S_push_neg_x_survival', 'S_push_pos_y_falls', 'S_push_pos_y_survival', 'S_push_pos_y_post_push_rmse', 'S_push_pos_y_recovery_upright', 'S_push_neg_y_falls', 'S_push_neg_y_survival', 'S_push_neg_y_post_push_rmse', 'S_push_neg_y_recovery_upright', 'S_forward_nominal_cmd_error', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'S_stairs10_ge2': ['303'], 'S_stairs10_survival': ['101', '202'], 'S_stairs10_progress_ratio': ['202'], 'S_push_pos_x_post_push_rmse': ['202', '303'], 'S_push_pos_x_recovery_upright': ['202'], 'S_push_neg_x_post_push_rmse': ['101', '202'], 'S_push_neg_x_recovery_upright': ['101', '303'], 'S_rough_forward_motion': ['101'], 'S_G7_dr_survival': ['101']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 3→9; 202: 5→13; 303: 8→11 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14039722322317585, 'rmse': 0.19510230847836174}→{'abs_error': 0.21255430699446715, 'rmse': 0.24316164142289923}; 202: {'abs_error': 0.1627081054053983, 'rmse': 0.21967638388985145}→{'abs_error': 0.22593953934896763, 'rmse': 0.24831523656282303}; 303: {'abs_error': 0.16984056842603062, 'rmse': 0.21559204447541716}→{'abs_error': 0.22902893301256605, 'rmse': 0.2531489028994944} |
| T_G5_stairs15_ge1 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 13→28; 202: 7→22; 303: 12→23 |
| T_G5_stairs15_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0→17; 202: 2→17; 303: 1→13 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0→10; 202: 1→12; 303: 1→11 |
| T_G5_stairs15_progress_ratio | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.14745918322674703→0.20370184385144938; 202: 0.15286497493990464→0.18456719267694283; 303: 0.14337488934914297→0.1768316226491588 |
| T_G5_stairs15_survival | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.0→0.375; 202: 0.0625→0.3125; 303: 0.1875→0.28125 |
| S_stairs10_ge2 | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'worse'} | 101: 30→32; 202: 30→31; 303: 31→30 |
| S_stairs10_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 0.875→0.8125; 202: 0.84375→0.8125; 303: 0.75→0.90625 |
| S_stairs10_progress_ratio | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: 0.4083756859167772→0.6890823259502653; 202: 0.5211638469014357→0.46451098090411647; 303: 0.3786358565602714→0.44263615854218363 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.11891220280490894→0.10447262929660632; 202: 0.12086704864376427→0.10514787202135861; 303: 0.11991639788568106→0.10360535281317294 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.0871629178308252→0.08484266243523571; 202: 0.09151623937316376→0.08410034736980021; 303: 0.09443598463247216→0.08581890900925146 |
| S_push_pos_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→3; 202: 2→8; 303: 0→4 |
| S_push_pos_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.96875→0.90625; 202: 0.9375→0.75; 303: 1.0→0.875 |
| S_push_pos_x_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.08736975726492062→0.0859325724191672; 202: 0.08609528177584123→0.10366111360209594; 303: 0.08010200443102393→0.09419269750757513 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'same'} | 101: 0.96875→0.9765625; 202: 0.9453125→0.9140625; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→4; 202: 2→3; 303: 0→2 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.96875→0.875; 202: 0.9375→0.90625; 303: 1.0→0.9375 |
| S_push_neg_x_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 0.08378573706241087→0.0932639032405755; 202: 0.08935629885422403→0.09449252747269174; 303: 0.08331589218547793→0.08322505938896041 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 0.9765625→0.9609375; 202: 0.953125→1.0; 303: 1.0→0.9765625 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→3; 202: 0→4; 303: 0→2 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.90625; 202: 1.0→0.875; 303: 1.0→0.9375 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08344106693599032→0.0890377348774599; 202: 0.08259399741654232→0.09193654459961377; 303: 0.08212561464307105→0.08979973583217372 |
| S_push_pos_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.984375; 202: 1.0→0.9921875; 303: 1.0→0.9765625 |
| S_push_neg_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→2; 202: 0→4; 303: 0→4 |
| S_push_neg_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.9375; 202: 1.0→0.875; 303: 1.0→0.875 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0825792335103558→0.08958851691536955; 202: 0.08385918230551727→0.09797661871948372; 303: 0.0849169228411315→0.09143666854125566 |
| S_push_neg_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.9921875; 202: 1.0→0.9765625; 303: 1.0→0.9609375 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'better', '303': 'better'} | 101: 1→1; 202: 2→0; 303: 2→0 |
| S_rough_forward_motion | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'better'} | 101: {'abs_error': 0.06542251308634556, 'rmse': 0.1757237524495671}→{'abs_error': 0.08104050628519249, 'rmse': 0.17762949578431247}; 202: {'abs_error': 0.09185409532217476, 'rmse': 0.21215743404631837}→{'abs_error': 0.06621904743545443, 'rmse': 0.15864800828210154}; 303: {'abs_error': 0.08347512502121213, 'rmse': 0.19940232218900505}→{'abs_error': 0.07606177961022265, 'rmse': 0.16290282443995263} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0006094765486686082→0.00850138741986528; 202: 0.0035127792115273726→0.0059294783480857705; 303: 0.0005496084180317551→0.009895235231440314 |
| S_G4_slope_plus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_plus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1107149260131976→0.10188208487082573; 202: 0.11299388872750336→0.10425868205153754; 303: 0.11278422658967056→0.10395278080206839 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'better'} | 101: 1.0→0.9375; 202: 0.96875→0.96875; 303: 0.9375→0.96875 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.16111067480247954→0.16477458550142987; 202: 0.14717089901500344→0.1745342183079888; 303: 0.17983685984932218→0.23638271686531695 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 10, 'reached_ge2': 17, 'stalled_after_reach': 7, 'conditional_stall_rate': 0.4117647058823529}
- seed 202: 부모 {'value': 1, 'reached_ge2': 2, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.5} / 노드 {'value': 12, 'reached_ge2': 17, 'stalled_after_reach': 5, 'conditional_stall_rate': 0.29411764705882354}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 11, 'reached_ge2': 13, 'stalled_after_reach': 2, 'conditional_stall_rate': 0.15384615384615385}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
