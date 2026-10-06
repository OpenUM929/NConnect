# PC2 탐색트리 판독 — s11_ang_vel_xy_l2_m0p02

- 노드: `workspace\_keep\go2_g_a063_pc2_s11_ang_vel_xy_l2_m0p02`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'ang_vel_xy_l2': -0.02}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G5_stairs15_ge2', 'T_G5_stairs15_nonstall_after_ge2', 'T_G5_stairs15_survival']
  - common_losses: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'S_yaw_right_yaw_rmse', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse']
  - partial_seed_losses: {'T_G5_stairs15_ge1': ['202', '303'], 'T_G5_stairs15_progress_ratio': ['303'], 'S_push_pos_y_falls': ['202'], 'S_push_pos_y_survival': ['202'], 'S_push_neg_y_falls': ['202'], 'S_push_neg_y_survival': ['202']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 13→23; 202: 16→23; 303: 12→26 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.13555333808000072, 'rmse': 0.21747515728236083}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.16670801459299825, 'rmse': 0.23507065192832582}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.1349434370506081, 'rmse': 0.22115701836559296} |
| T_G5_stairs15_ge1 | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 14→18; 202: 18→13; 303: 20→10 |
| T_G5_stairs15_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 1→6; 202: 1→4; 303: 1→3 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 1→4; 202: 1→3; 303: 1→2 |
| T_G5_stairs15_progress_ratio | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'worse'} | 101: 0.15926055355870625→0.16557897133339416; 202: 0.15526276969988256→0.15872928224703364; 303: 0.15797493859095257→0.15561217357303392 |
| T_G5_stairs15_survival | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.03125→0.40625; 202: 0.03125→0.15625; 303: 0.03125→0.09375 |
| S_stairs10_ge2 | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 26→31; 202: 30→31; 303: 29→30 |
| S_stairs10_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.53125→0.9375; 202: 0.59375→0.875; 303: 0.5→0.84375 |
| S_stairs10_progress_ratio | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.30537512402492606→0.8401317390556219; 202: 0.36892067344704993→0.8147378275621453; 303: 0.44727566097403154→0.7873410031865353 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13984381110366453→0.1577135019445845; 202: 0.1412283080457853→0.1557897434926055; 303: 0.14554375353750243→0.15897760578982373 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13197176738398128→0.12398018930358655; 202: 0.13163769258758068→0.12438388532025987; 303: 0.13360666624676226→0.12696444712437813 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.0853723014245051; 202: 0.07055512599999088→0.08795572405504934; 303: 0.06940222790799686→0.08338318867468847 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.08933496496089288; 202: 0.0698239791466322→0.08547324834774814; 303: 0.0695564418189401→0.08131528119578339 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0→0; 202: 0→1; 303: 0→0 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→0.96875; 303: 1.0→1.0 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.08460623213041202; 202: 0.06901107798414484→0.09047954488338356; 303: 0.0687554101390921→0.08662412683103039 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0→0; 202: 0→1; 303: 0→0 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→0.96875; 303: 1.0→1.0 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.08637553927761489; 202: 0.068929399843416→0.08892073177021052; 303: 0.06832387620766188→0.08513781084230926 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 4→1; 202: 2→0; 303: 0→0 |
| S_rough_forward_motion | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.11074309205499977, 'rmse': 0.18624411838789787}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.09331334951563469, 'rmse': 0.15800877832144186}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.100428104037396, 'rmse': 0.16204177208372408} |
| S_forward_nominal_cmd_error | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06584699518880566→0.02470940272862976; 202: 0.06588044092647338→0.023140519196657716; 303: 0.06613569222880822→0.026550162180669967 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1362061008257787→0.12098611822299542; 202: 0.13378358180109215→0.11928670569600452; 303: 0.13953023417442037→0.12424820812265094 |
| S_G7_dr_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.9375→0.96875; 202: 0.90625→1.0; 303: 0.90625→0.96875 |
| S_G7_dr_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.23962127644247008→0.19996175901366797; 202: 0.21095762200504264→0.16705141096917558; 303: 0.2317696478391446→0.21811147823991586 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 4, 'reached_ge2': 6, 'stalled_after_reach': 2, 'conditional_stall_rate': 0.3333333333333333}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 3, 'reached_ge2': 4, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.25}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 2, 'reached_ge2': 3, 'stalled_after_reach': 1, 'conditional_stall_rate': 0.3333333333333333}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
