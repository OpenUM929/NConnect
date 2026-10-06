# PC2 탐색트리 판독 — s05_feet_air_time_p0p01

- 노드: `workspace\_keep\go2_g_a063_pc2_s05_feet_air_time_p0p01`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'feet_air_time': 0.01}
- 정지 판정: MOVING
- **분류: WORSENED**
  - common_losses: ['T_G3_rough_lateral_motion', 'T_G5_stairs15_ge1', 'T_G5_stairs15_ge2', 'T_G5_stairs15_nonstall_after_ge2', 'T_G5_stairs15_progress_ratio', 'S_stairs10_ge2', 'S_stairs10_progress_ratio', 'S_yaw_right_yaw_rmse', 'S_yaw_right_xy_rmse', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_falls', 'S_push_neg_x_survival', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_falls', 'S_push_pos_y_survival', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse', 'S_rough_forward_motion', 'S_forward_nominal_cmd_error', 'S_G4_slope_minus_20_xy_rmse', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'T_G3_rough_lateral_falls': ['101', '303'], 'T_G5_stairs15_survival': ['101', '303'], 'S_stairs10_survival': ['101', '202'], 'S_push_pos_x_falls': ['303'], 'S_push_pos_x_survival': ['303'], 'S_push_neg_x_recovery_upright': ['202', '303'], 'S_push_pos_y_recovery_upright': ['202'], 'S_rough_forward_falls': ['202', '303'], 'S_G7_dr_survival': ['101', '202']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 13→19; 202: 16→16; 303: 12→16 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.17155861589078797, 'rmse': 0.22011163141949275}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.19684364634514168, 'rmse': 0.23425631429241708}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.19068506071739955, 'rmse': 0.23007941974618712} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→2; 202: 18→3; 303: 20→3 |
| T_G5_stairs15_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.14832499051012538; 202: 0.15526276969988256→0.14308995689099904; 303: 0.15797493859095257→0.14235855876060674 |
| T_G5_stairs15_survival | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 0.03125→0.0; 202: 0.03125→0.03125; 303: 0.03125→0.0 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 26→17; 202: 30→10; 303: 29→16 |
| S_stairs10_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'better'} | 101: 0.53125→0.3125; 202: 0.59375→0.40625; 303: 0.5→0.5625 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.30537512402492606→0.24140868606249577; 202: 0.36892067344704993→0.18869846500875426; 303: 0.44727566097403154→0.20844321892308634 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13984381110366453→0.2827038695492655; 202: 0.1412283080457853→0.2798062202648758; 303: 0.14554375353750243→0.28027246264067596 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13197176738398128→0.2594498659432013; 202: 0.13163769258758068→0.2550870514525594; 303: 0.13360666624676226→0.26209582852314517 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 0→0; 202: 0→0; 303: 0→1 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→0.96875 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.09218191212139522; 202: 0.07055512599999088→0.09240813818919608; 303: 0.06940222790799686→0.08780120059468688 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→1; 202: 0→2; 303: 0→1 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.96875; 202: 1.0→0.9375; 303: 1.0→0.96875 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.09688386700764348; 202: 0.0698239791466322→0.09183716731677513; 303: 0.0695564418189401→0.09328827902074012 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→0.984375; 303: 1.0→0.9921875 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→1; 202: 0→2; 303: 0→2 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.96875; 202: 1.0→0.9375; 303: 1.0→0.9375 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.08885520537947954; 202: 0.06901107798414484→0.08996587783371711; 303: 0.0687554101390921→0.09699858819991454 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→0.9921875; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.08993102770411526; 202: 0.068929399843416→0.09360308947853149; 303: 0.06832387620766188→0.09083313420813231 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 4→3; 202: 2→6; 303: 0→3 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.28458876564767444, 'rmse': 0.3662199118415368}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.22858981906711057, 'rmse': 0.32394871540947023}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.2601248177095286, 'rmse': 0.34728417830798103} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06584699518880566→0.09588305337697656; 202: 0.06588044092647338→0.08725949447405967; 303: 0.06613569222880822→0.10285860326239149 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.1362061008257787→0.20384473198981873; 202: 0.13378358180109215→0.1985735609054983; 303: 0.13953023417442037→0.20262198574434548 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 0.9375→0.875; 202: 0.90625→0.8125; 303: 0.90625→0.90625 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.23962127644247008→0.3509336437159083; 202: 0.21095762200504264→0.3942016482129472; 303: 0.2317696478391446→0.36215323325811355 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
