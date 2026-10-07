# PC2 탐색트리 판독 — c1_s07_ang_vel_xy_l2_m0p02

- 노드: `workspace\_keep\go2_g_a064_pc2_c1_s07_ang_vel_xy_l2_m0p02`
- 비교 부모(s07_feet_air_time_p0p35): `workspace\_keep\go2_g_a063_pc2_s07_feet_air_time_p0p35`
- 비교 부모 대비 변경: {'ang_vel_xy_l2': -0.02}
- 정지 판정: MOVING
- **분류: WORSENED**
  - common_losses: ['T_G3_rough_lateral_motion', 'T_G5_stairs15_ge1', 'S_stairs10_ge2', 'S_stairs10_survival', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse', 'S_forward_nominal_cmd_error']
  - partial_seed_losses: {'T_G3_rough_lateral_falls': ['101', '202'], 'T_G5_stairs15_ge2': ['202'], 'T_G5_stairs15_nonstall_after_ge2': ['202'], 'T_G5_stairs15_progress_ratio': ['202', '303'], 'T_G5_stairs15_survival': ['202', '303'], 'S_yaw_right_xy_rmse': ['101', '202'], 'S_push_pos_y_falls': ['101'], 'S_push_pos_y_survival': ['101'], 'S_push_neg_y_falls': ['101', '303'], 'S_push_neg_y_survival': ['101', '303'], 'S_G7_dr_survival': ['101', '202'], 'S_G7_dr_xy_rmse': ['202']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 3→9; 202: 5→11; 303: 8→8 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14039722322317585, 'rmse': 0.19510230847836174}→{'abs_error': 0.1827272297710389, 'rmse': 0.21911989204218157}; 202: {'abs_error': 0.1627081054053983, 'rmse': 0.21967638388985145}→{'abs_error': 0.18806373262952591, 'rmse': 0.21702498038034868}; 303: {'abs_error': 0.16984056842603062, 'rmse': 0.21559204447541716}→{'abs_error': 0.17639707960150763, 'rmse': 0.20643145204881308} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 13→3; 202: 7→1; 303: 12→2 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0→0; 202: 2→0; 303: 1→1 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0→0; 202: 1→0; 303: 1→1 |
| T_G5_stairs15_progress_ratio | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.14745918322674703→0.15153163548136933; 202: 0.15286497493990464→0.13763230453058714; 303: 0.14337488934914297→0.14267640846603896 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.0→0.09375; 202: 0.0625→0.03125; 303: 0.1875→0.03125 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 30→23; 202: 30→25; 303: 31→24 |
| S_stairs10_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.875→0.53125; 202: 0.84375→0.53125; 303: 0.75→0.65625 |
| S_stairs10_progress_ratio | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.4083756859167772→0.8376808498380705; 202: 0.5211638469014357→0.6147945248417089; 303: 0.3786358565602714→0.9152793132551006 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.11891220280490894→0.10404202147290802; 202: 0.12086704864376427→0.10454323231339516; 303: 0.11991639788568106→0.10519351870677318 |
| S_yaw_right_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 0.0871629178308252→0.0907027390520198; 202: 0.09151623937316376→0.09253212108476193; 303: 0.09443598463247216→0.0904800041792861 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 1→0; 202: 2→1; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.96875→1.0; 202: 0.9375→0.96875; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08736975726492062→0.15400468868048955; 202: 0.08609528177584123→0.17852510120839266; 303: 0.08010200443102393→0.15935142121795592 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.96875→1.0; 202: 0.9453125→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'same'} | 101: 1→0; 202: 2→2; 303: 0→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'same'} | 101: 0.96875→1.0; 202: 0.9375→0.9375; 303: 1.0→1.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08378573706241087→0.16138433875622374; 202: 0.08935629885422403→0.167822157296049; 303: 0.08331589218547793→0.16336864312229005 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.9765625→1.0; 202: 0.953125→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 0→1; 202: 0→0; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08344106693599032→0.17210284638630396; 202: 0.08259399741654232→0.1609478838274378; 303: 0.08212561464307105→0.151200351339935 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 0→1; 202: 0→0; 303: 0→1 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 1.0→0.96875; 202: 1.0→1.0; 303: 1.0→0.96875 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0825792335103558→0.1516380067242422; 202: 0.08385918230551727→0.17688426637398083; 303: 0.0849169228411315→0.1655762866313631 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 1→0; 202: 2→0; 303: 2→1 |
| S_rough_forward_motion | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: {'abs_error': 0.06542251308634556, 'rmse': 0.1757237524495671}→{'abs_error': 0.02438767258088964, 'rmse': 0.14712331236551845}; 202: {'abs_error': 0.09185409532217476, 'rmse': 0.21215743404631837}→{'abs_error': 0.004274677163247309, 'rmse': 0.12207814953365743}; 303: {'abs_error': 0.08347512502121213, 'rmse': 0.19940232218900505}→{'abs_error': 0.01860052744675461, 'rmse': 0.13223983716506907} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0006094765486686082→0.03722036931467687; 202: 0.0035127792115273726→0.03937012170098331; 303: 0.0005496084180317551→0.03661636034909044 |
| S_G4_slope_plus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_plus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1107149260131976→0.10652497535148243; 202: 0.11299388872750336→0.11114828953461983; 303: 0.11278422658967056→0.10816378744608357 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 1.0→0.96875; 202: 0.96875→0.90625; 303: 0.9375→1.0 |
| S_G7_dr_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: 0.16111067480247954→0.1308633718498105; 202: 0.14717089901500344→0.16476651107148477; 303: 0.17983685984932218→0.13062008000095754 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 2, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.5} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
