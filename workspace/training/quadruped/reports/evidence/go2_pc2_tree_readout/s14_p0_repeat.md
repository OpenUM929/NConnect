# PC2 탐색트리 판독 — s14_p0_repeat

- 노드: `workspace\_keep\go2_g_a063_pc2_s14_p0_repeat`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {}
- 정지 판정: MOVING
- **분류: NO_CONSISTENT_CHANGE**
  - note: 동등성·무효과 증명이 아니다. 세 seed 방향이 엇갈린 혼합도 여기에 든다.

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 13→13; 202: 16→16; 303: 12→12 |
| T_G3_rough_lateral_motion | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173} |
| T_G5_stairs15_ge1 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 14→14; 202: 18→18; 303: 20→20 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1→1; 202: 1→1; 303: 1→1 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1→1; 202: 1→1; 303: 1→1 |
| T_G5_stairs15_progress_ratio | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.15926055355870625→0.15926055355870625; 202: 0.15526276969988256→0.15526276969988256; 303: 0.15797493859095257→0.15797493859095257 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.03125→0.03125; 202: 0.03125→0.03125; 303: 0.03125→0.03125 |
| S_stairs10_ge2 | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 26→26; 202: 30→30; 303: 29→29 |
| S_stairs10_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.53125→0.53125; 202: 0.59375→0.59375; 303: 0.5→0.5 |
| S_stairs10_progress_ratio | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.30537512402492606→0.30537512402492606; 202: 0.36892067344704993→0.36892067344704993; 303: 0.44727566097403154→0.44727566097403154 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.13984381110366453→0.13984381110366453; 202: 0.1412283080457853→0.1412283080457853; 303: 0.14554375353750243→0.14554375353750243 |
| S_yaw_right_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.13197176738398128→0.13197176738398128; 202: 0.13163769258758068→0.13163769258758068; 303: 0.13360666624676226→0.13360666624676226 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.069380060215967→0.069380060215967; 202: 0.07055512599999088→0.07055512599999088; 303: 0.06940222790799686→0.06940222790799686 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.06868000597159794→0.06868000597159794; 202: 0.0698239791466322→0.0698239791466322; 303: 0.0695564418189401→0.0695564418189401 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.06935616071552589→0.06935616071552589; 202: 0.06901107798414484→0.06901107798414484; 303: 0.0687554101390921→0.0687554101390921 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_post_push_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.07028925895448256→0.07028925895448256; 202: 0.068929399843416→0.068929399843416; 303: 0.06832387620766188→0.06832387620766188 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 4→4; 202: 2→2; 303: 0→0 |
| S_rough_forward_motion | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845} |
| S_forward_nominal_cmd_error | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.06584699518880566→0.06584699518880566; 202: 0.06588044092647338→0.06588044092647338; 303: 0.06613569222880822→0.06613569222880822 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.1362061008257787→0.1362061008257787; 202: 0.13378358180109215→0.13378358180109215; 303: 0.13953023417442037→0.13953023417442037 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.9375→0.9375; 202: 0.90625→0.90625; 303: 0.90625→0.90625 |
| S_G7_dr_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0.23962127644247008→0.23962127644247008; 202: 0.21095762200504264→0.21095762200504264; 303: 0.2317696478391446→0.2317696478391446 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
