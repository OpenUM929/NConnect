# PC2 탐색트리 판독 — s03_lin_vel_z_l2_m2

- 노드: `workspace\_keep\go2_g_a063_pc2_s03_lin_vel_z_l2_m2`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'lin_vel_z_l2': -2.0}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G5_stairs15_survival']
  - common_losses: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'T_G5_stairs15_ge1', 'T_G5_stairs15_progress_ratio', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse']
  - partial_seed_losses: {'T_G5_stairs15_ge2': ['101'], 'T_G5_stairs15_nonstall_after_ge2': ['101'], 'S_stairs10_ge2': ['202', '303'], 'S_stairs10_progress_ratio': ['202', '303'], 'S_rough_forward_falls': ['303'], 'S_rough_forward_motion': ['202'], 'S_G7_dr_survival': ['202'], 'S_G7_dr_xy_rmse': ['202', '303']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 13→19; 202: 16→28; 303: 12→20 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.21279607169206777, 'rmse': 0.25332112048752287}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.22381273966465665, 'rmse': 0.2598989170091526}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.23007653534230763, 'rmse': 0.26131835982474333} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→9; 202: 18→16; 303: 20→18 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'better'} | 101: 1→0; 202: 1→1; 303: 1→3 |
| T_G5_stairs15_nonstall_after_ge2 | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 1→0; 202: 1→1; 303: 1→1 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.13601410103692618; 202: 0.15526276969988256→0.13689960758714018; 303: 0.15797493859095257→0.14480039425251023 |
| T_G5_stairs15_survival | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.03125→0.09375; 202: 0.03125→0.25; 303: 0.03125→0.28125 |
| S_stairs10_ge2 | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 26→28; 202: 30→28; 303: 29→27 |
| S_stairs10_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.53125→0.84375; 202: 0.59375→0.78125; 303: 0.5→0.78125 |
| S_stairs10_progress_ratio | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.30537512402492606→0.3353061683770937; 202: 0.36892067344704993→0.3497830995808763; 303: 0.44727566097403154→0.3593085735744099 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13984381110366453→0.13233648187118122; 202: 0.1412283080457853→0.13507967768025708; 303: 0.14554375353750243→0.13810839679336118 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13197176738398128→0.10695530296688197; 202: 0.13163769258758068→0.10749094529994604; 303: 0.13360666624676226→0.11018991340942492 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.09068256622950249; 202: 0.07055512599999088→0.09230420022215945; 303: 0.06940222790799686→0.08807901431719223 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.08949143131667797; 202: 0.0698239791466322→0.09019233695471206; 303: 0.0695564418189401→0.09016685702869011 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.08668285360183667; 202: 0.06901107798414484→0.08682195290857735; 303: 0.0687554101390921→0.08670177792543861 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.08818922420545805; 202: 0.068929399843416→0.09024822499169789; 303: 0.06832387620766188→0.0912611657128433 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 4→4; 202: 2→2; 303: 0→2 |
| S_rough_forward_motion | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.10570816332329636, 'rmse': 0.22489638704710888}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.09285032281695144, 'rmse': 0.21312429026518634}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.08526308743628269, 'rmse': 0.19668303058747458} |
| S_forward_nominal_cmd_error | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06584699518880566→0.02133750415162039; 202: 0.06588044092647338→0.018551542113878217; 303: 0.06613569222880822→0.023197139247663756 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1362061008257787→0.11439600781564681; 202: 0.13378358180109215→0.11085171062630157; 303: 0.13953023417442037→0.10896202030832318 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0.9375→0.9375; 202: 0.90625→0.78125; 303: 0.90625→0.90625 |
| S_G7_dr_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.23962127644247008→0.20890330194567897; 202: 0.21095762200504264→0.2833402561528203; 303: 0.2317696478391446→0.24456944369609884 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 1, 'reached_ge2': 3, 'stalled_after_reach': 2, 'conditional_stall_rate': 0.6666666666666666}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
