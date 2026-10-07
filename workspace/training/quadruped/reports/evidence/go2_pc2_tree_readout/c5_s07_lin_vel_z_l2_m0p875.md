# PC2 탐색트리 판독 — c5_s07_lin_vel_z_l2_m0p875

- 노드: `workspace\_keep\go2_g_a064_pc2_c5_s07_lin_vel_z_l2_m0p875`
- 비교 부모(s07_feet_air_time_p0p35): `workspace\_keep\go2_g_a063_pc2_s07_feet_air_time_p0p35`
- 비교 부모 대비 변경: {'lin_vel_z_l2': -0.875}
- 정지 판정: MOVING
- **분류: WORSENED**
  - common_losses: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'T_G5_stairs15_progress_ratio', 'S_stairs10_ge2', 'S_stairs10_progress_ratio', 'S_yaw_right_yaw_rmse', 'S_yaw_right_xy_rmse', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_falls', 'S_push_neg_x_survival', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_falls', 'S_push_pos_y_survival', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_falls', 'S_push_neg_y_survival', 'S_push_neg_y_post_push_rmse', 'S_rough_forward_motion', 'S_forward_nominal_cmd_error', 'S_G4_slope_plus_20_xy_rmse', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'T_G5_stairs15_ge1': ['101', '303'], 'T_G5_stairs15_ge2': ['202', '303'], 'T_G5_stairs15_nonstall_after_ge2': ['202', '303'], 'S_stairs10_survival': ['101', '202'], 'S_push_pos_x_falls': ['202', '303'], 'S_push_pos_x_survival': ['202', '303'], 'S_rough_forward_falls': ['202'], 'S_G4_slope_plus_20_survival': ['303'], 'S_G7_dr_survival': ['202', '303']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 3→25; 202: 5→22; 303: 8→23 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14039722322317585, 'rmse': 0.19510230847836174}→{'abs_error': 0.2210913164435016, 'rmse': 0.2544502752555353}; 202: {'abs_error': 0.1627081054053983, 'rmse': 0.21967638388985145}→{'abs_error': 0.2294072489156443, 'rmse': 0.26294386899569505}; 303: {'abs_error': 0.16984056842603062, 'rmse': 0.21559204447541716}→{'abs_error': 0.2417046171340438, 'rmse': 0.2670884326223308} |
| T_G5_stairs15_ge1 | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'worse'} | 101: 13→9; 202: 7→8; 303: 12→7 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 0→0; 202: 2→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 0→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.14745918322674703→0.14581602309364822; 202: 0.15286497493990464→0.14340801916795284; 303: 0.14337488934914297→0.13664489882311326 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'same', '303': 'better'} | 101: 0.0→0.09375; 202: 0.0625→0.0625; 303: 0.1875→0.21875 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 30→12; 202: 30→11; 303: 31→12 |
| S_stairs10_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 0.875→0.6875; 202: 0.84375→0.59375; 303: 0.75→0.8125 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.4083756859167772→0.17806052172719503; 202: 0.5211638469014357→0.16989677091821806; 303: 0.3786358565602714→0.16525697796139865 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.11891220280490894→0.1474019639108601; 202: 0.12086704864376427→0.14525408018218183; 303: 0.11991639788568106→0.15099563271790634 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0871629178308252→0.15503053898995783; 202: 0.09151623937316376→0.15025352587783963; 303: 0.09443598463247216→0.1620475524149995 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 2→4; 303: 0→2 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.96875→1.0; 202: 0.9375→0.875; 303: 1.0→0.9375 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08736975726492062→0.11049706238570099; 202: 0.08609528177584123→0.12060633484204147; 303: 0.08010200443102393→0.11362125256167349 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.96875→1.0; 202: 0.9453125→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→6; 202: 2→3; 303: 0→2 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.96875→0.8125; 202: 0.9375→0.90625; 303: 1.0→0.9375 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08378573706241087→0.1206227315465169; 202: 0.08935629885422403→0.12312572049176496; 303: 0.08331589218547793→0.11268256643352899 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 0.9765625→1.0; 202: 0.953125→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→6; 202: 0→2; 303: 0→3 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.8125; 202: 1.0→0.9375; 303: 1.0→0.90625 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.08344106693599032→0.12545134507110572; 202: 0.08259399741654232→0.11473650661688566; 303: 0.08212561464307105→0.10685368480826553 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→8; 202: 0→2; 303: 0→4 |
| S_push_neg_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.75; 202: 1.0→0.9375; 303: 1.0→0.875 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0825792335103558→0.12710548628290125; 202: 0.08385918230551727→0.11957793909498483; 303: 0.0849169228411315→0.12148558698470871 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: 1→0; 202: 2→6; 303: 2→1 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.06542251308634556, 'rmse': 0.1757237524495671}→{'abs_error': 0.24461924109471916, 'rmse': 0.33507583368733357}; 202: {'abs_error': 0.09185409532217476, 'rmse': 0.21215743404631837}→{'abs_error': 0.19189692985394996, 'rmse': 0.2931690382590688}; 303: {'abs_error': 0.08347512502121213, 'rmse': 0.19940232218900505}→{'abs_error': 0.2507953400053662, 'rmse': 0.3377574335227472} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.0006094765486686082→0.030182849711885562; 202: 0.0035127792115273726→0.023317978262509143; 303: 0.0005496084180317551→0.03397480925937235 |
| S_G4_slope_plus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→0.96875 |
| S_G4_slope_plus_20_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.1107149260131976→0.22162705454572915; 202: 0.11299388872750336→0.19673041560516363; 303: 0.11278422658967056→0.23922086185740424 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 1.0→1.0; 202: 0.96875→0.9375; 303: 0.9375→0.90625 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.16111067480247954→0.35798485891234466; 202: 0.14717089901500344→0.31790606933048016; 303: 0.17983685984932218→0.32535051020537786 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 2, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.5} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
