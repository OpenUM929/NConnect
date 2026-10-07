# PC2 탐색트리 판독 — s07_feet_air_time_p0p35

- 노드: `workspace\_keep\go2_g_a063_pc2_s07_feet_air_time_p0p35`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'feet_air_time': 0.35}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G3_rough_lateral_falls']
  - common_losses: ['T_G5_stairs15_ge1', 'T_G5_stairs15_progress_ratio', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse']
  - partial_seed_losses: {'T_G3_rough_lateral_motion': ['202', '303'], 'T_G5_stairs15_ge2': ['101'], 'T_G5_stairs15_nonstall_after_ge2': ['101'], 'T_G5_stairs15_survival': ['101'], 'S_stairs10_progress_ratio': ['303'], 'S_push_pos_x_falls': ['101', '202'], 'S_push_pos_x_survival': ['101', '202'], 'S_push_pos_x_recovery_upright': ['101', '202'], 'S_push_neg_x_falls': ['101', '202'], 'S_push_neg_x_survival': ['101', '202'], 'S_push_neg_x_recovery_upright': ['101', '202'], 'S_rough_forward_falls': ['303'], 'S_rough_forward_motion': ['202']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 13→3; 202: 16→5; 303: 12→8 |
| T_G3_rough_lateral_motion | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.14039722322317585, 'rmse': 0.19510230847836174}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.1627081054053983, 'rmse': 0.21967638388985145}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.16984056842603062, 'rmse': 0.21559204447541716} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→13; 202: 18→7; 303: 20→12 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'same'} | 101: 1→0; 202: 1→2; 303: 1→1 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 1→0; 202: 1→1; 303: 1→1 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.14745918322674703; 202: 0.15526276969988256→0.15286497493990464; 303: 0.15797493859095257→0.14337488934914297 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'better'} | 101: 0.03125→0.0; 202: 0.03125→0.0625; 303: 0.03125→0.1875 |
| S_stairs10_ge2 | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'better'} | 101: 26→30; 202: 30→30; 303: 29→31 |
| S_stairs10_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.53125→0.875; 202: 0.59375→0.84375; 303: 0.5→0.75 |
| S_stairs10_progress_ratio | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'worse'} | 101: 0.30537512402492606→0.4083756859167772; 202: 0.36892067344704993→0.5211638469014357; 303: 0.44727566097403154→0.3786358565602714 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13984381110366453→0.11891220280490894; 202: 0.1412283080457853→0.12086704864376427; 303: 0.14554375353750243→0.11991639788568106 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13197176738398128→0.0871629178308252; 202: 0.13163769258758068→0.09151623937316376; 303: 0.13360666624676226→0.09443598463247216 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 0→1; 202: 0→2; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→0.9375; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.08736975726492062; 202: 0.07055512599999088→0.08609528177584123; 303: 0.06940222790799686→0.08010200443102393 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→0.9453125; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 0→1; 202: 0→2; 303: 0→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→0.9375; 303: 1.0→1.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.08378573706241087; 202: 0.0698239791466322→0.08935629885422403; 303: 0.0695564418189401→0.08331589218547793 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 1.0→0.9765625; 202: 1.0→0.953125; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.08344106693599032; 202: 0.06901107798414484→0.08259399741654232; 303: 0.0687554101390921→0.08212561464307105 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.0825792335103558; 202: 0.068929399843416→0.08385918230551727; 303: 0.06832387620766188→0.0849169228411315 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'worse'} | 101: 4→1; 202: 2→2; 303: 0→2 |
| S_rough_forward_motion | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.06542251308634556, 'rmse': 0.1757237524495671}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.09185409532217476, 'rmse': 0.21215743404631837}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.08347512502121213, 'rmse': 0.19940232218900505} |
| S_forward_nominal_cmd_error | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06584699518880566→0.0006094765486686082; 202: 0.06588044092647338→0.0035127792115273726; 303: 0.06613569222880822→0.0005496084180317551 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1362061008257787→0.10804496873629212; 202: 0.13378358180109215→0.10867725425914258; 303: 0.13953023417442037→0.1122489756650261 |
| S_G7_dr_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.9375→1.0; 202: 0.90625→0.96875; 303: 0.90625→0.9375 |
| S_G7_dr_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.23962127644247008→0.16111067480247954; 202: 0.21095762200504264→0.14717089901500344; 303: 0.2317696478391446→0.17983685984932218 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 2, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.5}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
