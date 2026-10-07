# PC2 탐색트리 판독 — s02_lin_vel_z_l2_m3

- 노드: `workspace\_keep\go2_g_a063_pc2_s02_lin_vel_z_l2_m3`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'lin_vel_z_l2': -3.0}
- 정지 판정: MOVING
- **분류: WORSENED**
  - common_losses: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'T_G5_stairs15_ge1', 'T_G5_stairs15_ge2', 'T_G5_stairs15_nonstall_after_ge2', 'T_G5_stairs15_progress_ratio', 'T_G5_stairs15_survival', 'S_stairs10_ge2', 'S_stairs10_survival', 'S_stairs10_progress_ratio', 'S_yaw_right_yaw_rmse', 'S_yaw_right_xy_rmse', 'S_push_pos_x_falls', 'S_push_pos_x_survival', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_falls', 'S_push_neg_x_survival', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_falls', 'S_push_pos_y_survival', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_falls', 'S_push_neg_y_survival', 'S_push_neg_y_post_push_rmse', 'S_rough_forward_motion', 'S_G4_slope_minus_20_xy_rmse', 'S_G7_dr_survival', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'S_yaw_right_falls': ['303'], 'S_yaw_right_survival': ['303'], 'S_rough_forward_falls': ['202', '303'], 'S_G4_slope_minus_20_survival': ['202']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 13→26; 202: 16→26; 303: 12→26 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.16684587851093188, 'rmse': 0.23595061257632177}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.18415644724483027, 'rmse': 0.2400766421217363}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.18153892520308296, 'rmse': 0.2391366869252474} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→0; 202: 18→0; 303: 20→1 |
| T_G5_stairs15_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.12731323438457917; 202: 0.15526276969988256→0.11733653959246301; 303: 0.15797493859095257→0.12639089910645276 |
| T_G5_stairs15_survival | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.03125→0.0; 202: 0.03125→0.0; 303: 0.03125→0.0 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 26→0; 202: 30→1; 303: 29→0 |
| S_stairs10_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.53125→0.125; 202: 0.59375→0.125; 303: 0.5→0.125 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.30537512402492606→0.1448934375630924; 202: 0.36892067344704993→0.13818193493831515; 303: 0.44727566097403154→0.14589781604549343 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 0→0; 202: 0→0; 303: 0→1 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→0.96875 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13984381110366453→0.1639641448428391; 202: 0.1412283080457853→0.15980744215152293; 303: 0.14554375353750243→0.1716403227564753 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13197176738398128→0.14667435389157857; 202: 0.13163769258758068→0.13941176182011447; 303: 0.13360666624676226→0.15111195818054 |
| S_push_pos_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→7; 202: 0→13; 303: 0→8 |
| S_push_pos_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.78125; 202: 1.0→0.59375; 303: 1.0→0.75 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.11487074314187835; 202: 0.07055512599999088→0.12870501711475132; 303: 0.06940222790799686→0.11885617460783998 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→9; 202: 0→16; 303: 0→13 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.71875; 202: 1.0→0.5; 303: 1.0→0.59375 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.12108310382911724; 202: 0.0698239791466322→0.13158566997149487; 303: 0.0695564418189401→0.1279886053059449 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→15; 202: 0→10; 303: 0→5 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.53125; 202: 1.0→0.6875; 303: 1.0→0.84375 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.12557016490675138; 202: 0.06901107798414484→0.12799015720140636; 303: 0.0687554101390921→0.10389957042030362 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→7; 202: 0→8; 303: 0→8 |
| S_push_neg_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.78125; 202: 1.0→0.75; 303: 1.0→0.75 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.11188310082556457; 202: 0.068929399843416→0.12245018181183061; 303: 0.06832387620766188→0.11498157868513174 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 4→3; 202: 2→4; 303: 0→2 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.2330960131007923, 'rmse': 0.3279965267057376}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.2064884038228335, 'rmse': 0.3085889902707244}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.24723382858574017, 'rmse': 0.33790049578887915} |
| S_forward_nominal_cmd_error | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06584699518880566→0.03651612607174015; 202: 0.06588044092647338→0.03177868226543068; 303: 0.06613569222880822→0.042252635298002716 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→0.9375; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.1362061008257787→0.13880486597028607; 202: 0.13378358180109215→0.15392942000333207; 303: 0.13953023417442037→0.14855397292799427 |
| S_G7_dr_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.9375→0.8125; 202: 0.90625→0.6875; 303: 0.90625→0.875 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.23962127644247008→0.3156862803478331; 202: 0.21095762200504264→0.35052682348325553; 303: 0.2317696478391446→0.3326112821841756 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
