# PC2 탐색트리 판독 — c3_s07_action_rate_l2_m0p0075

- 노드: `workspace\_keep\go2_g_a064_pc2_c3_s07_action_rate_l2_m0p0075`
- 비교 부모(s07_feet_air_time_p0p35): `workspace\_keep\go2_g_a063_pc2_s07_feet_air_time_p0p35`
- 비교 부모 대비 변경: {'action_rate_l2': -0.0075}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G3_rough_lateral_falls']
  - common_losses: ['T_G5_stairs15_progress_ratio', 'S_stairs10_ge2', 'S_stairs10_survival', 'S_stairs10_progress_ratio', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse', 'S_rough_forward_motion', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'T_G3_rough_lateral_motion': ['101'], 'T_G5_stairs15_ge1': ['101', '303'], 'T_G5_stairs15_ge2': ['202', '303'], 'T_G5_stairs15_nonstall_after_ge2': ['202', '303'], 'T_G5_stairs15_survival': ['202', '303'], 'S_yaw_right_yaw_rmse': ['101', '303'], 'S_push_neg_x_falls': ['303'], 'S_push_neg_x_survival': ['303'], 'S_push_neg_y_falls': ['101'], 'S_push_neg_y_survival': ['101'], 'S_forward_nominal_cmd_error': ['101'], 'S_G4_slope_plus_20_survival': ['101'], 'S_G4_slope_plus_20_xy_rmse': ['101', '202'], 'S_G7_dr_survival': ['101', '303']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 3→2; 202: 5→3; 303: 8→2 |
| T_G3_rough_lateral_motion | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'better'} | 101: {'abs_error': 0.14039722322317585, 'rmse': 0.19510230847836174}→{'abs_error': 0.14564701398831337, 'rmse': 0.19896331853055704}; 202: {'abs_error': 0.1627081054053983, 'rmse': 0.21967638388985145}→{'abs_error': 0.1325610430152334, 'rmse': 0.18838570945537192}; 303: {'abs_error': 0.16984056842603062, 'rmse': 0.21559204447541716}→{'abs_error': 0.12534855742691856, 'rmse': 0.18419715351057422} |
| T_G5_stairs15_ge1 | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 13→6; 202: 7→8; 303: 12→3 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 0→0; 202: 2→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 0→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.14745918322674703→0.14512766168793298; 202: 0.15286497493990464→0.14202798128017466; 303: 0.14337488934914297→0.14157751757759257 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.0→0.03125; 202: 0.0625→0.03125; 303: 0.1875→0.03125 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 30→13; 202: 30→13; 303: 31→9 |
| S_stairs10_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.875→0.5625; 202: 0.84375→0.59375; 303: 0.75→0.375 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.4083756859167772→0.21458530264877487; 202: 0.5211638469014357→0.19575234514160572; 303: 0.3786358565602714→0.18971138513833297 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 0.11891220280490894→0.11994705084330179; 202: 0.12086704864376427→0.12042620875105163; 303: 0.11991639788568106→0.12070538405246299 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.0871629178308252→0.08060677946956674; 202: 0.09151623937316376→0.08028627261403809; 303: 0.09443598463247216→0.08191443883992532 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 1→0; 202: 2→0; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.96875→1.0; 202: 0.9375→1.0; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08736975726492062→0.09988962863116095; 202: 0.08609528177584123→0.10188280923206446; 303: 0.08010200443102393→0.10000388579724509 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.96875→1.0; 202: 0.9453125→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'worse'} | 101: 1→0; 202: 2→0; 303: 0→1 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'worse'} | 101: 0.96875→1.0; 202: 0.9375→1.0; 303: 1.0→0.96875 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08378573706241087→0.10007277408267642; 202: 0.08935629885422403→0.1026848534854311; 303: 0.08331589218547793→0.1024276051015582 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.9765625→1.0; 202: 0.953125→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08344106693599032→0.10209369645803405; 202: 0.08259399741654232→0.10049583520456601; 303: 0.08212561464307105→0.10197917536858511 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 0→1; 202: 0→0; 303: 0→0 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0825792335103558→0.10165786420312203; 202: 0.08385918230551727→0.10059724013719658; 303: 0.0849169228411315→0.10219512867571803 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 1→0; 202: 2→0; 303: 2→1 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.06542251308634556, 'rmse': 0.1757237524495671}→{'abs_error': 0.1416049698059561, 'rmse': 0.2558703902692024}; 202: {'abs_error': 0.09185409532217476, 'rmse': 0.21215743404631837}→{'abs_error': 0.12762541988462783, 'rmse': 0.2455745633941435}; 303: {'abs_error': 0.08347512502121213, 'rmse': 0.19940232218900505}→{'abs_error': 0.12207974240679481, 'rmse': 0.23243912151667928} |
| S_forward_nominal_cmd_error | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'better'} | 101: 0.0006094765486686082→0.0007561702849833152; 202: 0.0035127792115273726→0.001219448397230205; 303: 0.0005496084180317551→0.0001576329669670251 |
| S_G4_slope_plus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_plus_20_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 0.1107149260131976→0.12905569150894047; 202: 0.11299388872750336→0.121840059566743; 303: 0.11278422658967056→0.10261086814363662 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 1.0→0.90625; 202: 0.96875→0.96875; 303: 0.9375→0.90625 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.16111067480247954→0.3047735229790528; 202: 0.14717089901500344→0.2813370222751834; 303: 0.17983685984932218→0.3153628326828585 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 2, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.5} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
