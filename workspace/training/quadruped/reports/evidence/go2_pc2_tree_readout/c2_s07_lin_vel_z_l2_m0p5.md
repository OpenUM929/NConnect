# PC2 탐색트리 판독 — c2_s07_lin_vel_z_l2_m0p5

- 노드: `workspace\_keep\go2_g_a064_pc2_c2_s07_lin_vel_z_l2_m0p5`
- 비교 부모(s07_feet_air_time_p0p35): `workspace\_keep\go2_g_a063_pc2_s07_feet_air_time_p0p35`
- 비교 부모 대비 변경: {'lin_vel_z_l2': -0.5}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G3_rough_lateral_motion', 'T_G5_stairs15_ge1', 'T_G5_stairs15_ge2', 'T_G5_stairs15_nonstall_after_ge2']
  - common_losses: ['S_yaw_right_yaw_rmse', 'S_yaw_right_xy_rmse', 'S_rough_forward_motion', 'S_forward_nominal_cmd_error', 'S_G4_slope_plus_20_xy_rmse', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'T_G3_rough_lateral_falls': ['202'], 'T_G5_stairs15_progress_ratio': ['202'], 'T_G5_stairs15_survival': ['303'], 'S_stairs10_ge2': ['303'], 'S_stairs10_survival': ['202'], 'S_push_pos_x_falls': ['202'], 'S_push_pos_x_survival': ['202'], 'S_push_pos_x_post_push_rmse': ['202', '303'], 'S_push_neg_x_falls': ['303'], 'S_push_neg_x_survival': ['303'], 'S_push_neg_x_post_push_rmse': ['202', '303'], 'S_push_pos_y_falls': ['101', '202'], 'S_push_pos_y_survival': ['101', '202'], 'S_push_pos_y_post_push_rmse': ['101', '202'], 'S_push_neg_y_falls': ['101', '303'], 'S_push_neg_y_survival': ['101', '303'], 'S_push_neg_y_post_push_rmse': ['101', '303'], 'S_rough_forward_falls': ['303'], 'S_G7_dr_survival': ['101', '202']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'same'} | 101: 3→2; 202: 5→10; 303: 8→8 |
| T_G3_rough_lateral_motion | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: {'abs_error': 0.14039722322317585, 'rmse': 0.19510230847836174}→{'abs_error': 0.08796880766892523, 'rmse': 0.16349286437440966}; 202: {'abs_error': 0.1627081054053983, 'rmse': 0.21967638388985145}→{'abs_error': 0.08964798566336801, 'rmse': 0.1723059561121286}; 303: {'abs_error': 0.16984056842603062, 'rmse': 0.21559204447541716}→{'abs_error': 0.09725933361549599, 'rmse': 0.17351027409481024} |
| T_G5_stairs15_ge1 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 13→14; 202: 7→15; 303: 12→14 |
| T_G5_stairs15_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0→4; 202: 2→4; 303: 1→5 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0→3; 202: 1→3; 303: 1→4 |
| T_G5_stairs15_progress_ratio | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: 0.14745918322674703→0.15535301127772247; 202: 0.15286497493990464→0.14460677572240094; 303: 0.14337488934914297→0.1466969992720987 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'worse'} | 101: 0.0→0.09375; 202: 0.0625→0.0625; 303: 0.1875→0.0625 |
| S_stairs10_ge2 | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'worse'} | 101: 30→32; 202: 30→30; 303: 31→29 |
| S_stairs10_survival | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: 0.875→0.9375; 202: 0.84375→0.8125; 303: 0.75→0.90625 |
| S_stairs10_progress_ratio | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.4083756859167772→0.8307196717056936; 202: 0.5211638469014357→0.8517923776428219; 303: 0.3786358565602714→0.8055997300231829 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.11891220280490894→0.1764378604391245; 202: 0.12086704864376427→0.17405121425316736; 303: 0.11991639788568106→0.18692784220259384 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0871629178308252→0.10739189201589258; 202: 0.09151623937316376→0.10748870616860406; 303: 0.09443598463247216→0.11177968070053937 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1→1; 202: 2→4; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0.96875→0.96875; 202: 0.9375→0.875; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.08736975726492062→0.08306107829067717; 202: 0.08609528177584123→0.09424210244152573; 303: 0.08010200443102393→0.08499447362349602 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.96875→1.0; 202: 0.9453125→0.9921875; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'worse'} | 101: 1→0; 202: 2→2; 303: 0→2 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'worse'} | 101: 0.96875→1.0; 202: 0.9375→0.9375; 303: 1.0→0.9375 |
| S_push_neg_x_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.08378573706241087→0.08063541605188912; 202: 0.08935629885422403→0.09255214885974604; 303: 0.08331589218547793→0.08749254560898655 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.9765625→1.0; 202: 0.953125→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 0→2; 202: 0→1; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 1.0→0.9375; 202: 1.0→0.96875; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 0.08344106693599032→0.08986310996900793; 202: 0.08259399741654232→0.08486894845538022; 303: 0.08212561464307105→0.08009890419369292 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 0→3; 202: 0→0; 303: 0→1 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 1.0→0.90625; 202: 1.0→1.0; 303: 1.0→0.96875 |
| S_push_neg_y_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 0.0825792335103558→0.09235864433608794; 202: 0.08385918230551727→0.0825429816030925; 303: 0.0849169228411315→0.0859321019761262 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'worse'} | 101: 1→0; 202: 2→2; 303: 2→4 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.06542251308634556, 'rmse': 0.1757237524495671}→{'abs_error': 0.07031931784380602, 'rmse': 0.18476491266102188}; 202: {'abs_error': 0.09185409532217476, 'rmse': 0.21215743404631837}→{'abs_error': 0.08738398308685263, 'rmse': 0.21767893947196448}; 303: {'abs_error': 0.08347512502121213, 'rmse': 0.19940232218900505}→{'abs_error': 0.13351225389894972, 'rmse': 0.2566416675883074} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0006094765486686082→0.012676115375208186; 202: 0.0035127792115273726→0.0144001277281266; 303: 0.0005496084180317551→0.012913005114778109 |
| S_G4_slope_plus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_plus_20_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.1107149260131976→0.12114363220929616; 202: 0.11299388872750336→0.12113877042253758; 303: 0.11278422658967056→0.12343901520340857 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 1.0→0.78125; 202: 0.96875→0.90625; 303: 0.9375→0.9375 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.16111067480247954→0.2855725533282734; 202: 0.14717089901500344→0.22909776550313915; 303: 0.17983685984932218→0.22894469838287393 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 3, 'reached_ge2': 4, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.25}
- seed 202: 부모 {'value': 1, 'reached_ge2': 2, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.5} / 노드 {'value': 3, 'reached_ge2': 4, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.25}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 4, 'reached_ge2': 5, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.2}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
