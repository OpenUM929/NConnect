# PC2 탐색트리 판독 — s12_action_rate_l2_m0p02

- 노드: `workspace\_keep\go2_g_a063_pc2_s12_action_rate_l2_m0p02`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'action_rate_l2': -0.02}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G5_stairs15_survival']
  - common_losses: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'T_G5_stairs15_ge2', 'T_G5_stairs15_nonstall_after_ge2', 'S_stairs10_ge2', 'S_stairs10_progress_ratio', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse', 'S_rough_forward_motion', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'T_G5_stairs15_ge1': ['202', '303'], 'T_G5_stairs15_progress_ratio': ['202', '303'], 'S_push_pos_x_falls': ['101', '202'], 'S_push_pos_x_survival': ['101', '202'], 'S_push_pos_x_recovery_upright': ['202'], 'S_push_neg_x_falls': ['202'], 'S_push_neg_x_survival': ['202'], 'S_push_pos_y_falls': ['202', '303'], 'S_push_pos_y_survival': ['202', '303'], 'S_push_neg_y_falls': ['303'], 'S_push_neg_y_survival': ['303'], 'S_push_neg_y_recovery_upright': ['303'], 'S_rough_forward_falls': ['303'], 'S_G7_dr_survival': ['101']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 13→32; 202: 16→31; 303: 12→30 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.24233040295548397, 'rmse': 0.2862753392085197}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.24740357557508677, 'rmse': 0.2917730899759513}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.2590045061571197, 'rmse': 0.2925356668878622} |
| T_G5_stairs15_ge1 | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 14→15; 202: 18→7; 303: 20→11 |
| T_G5_stairs15_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.16475442330446088; 202: 0.15526276969988256→0.14974158168444412; 303: 0.15797493859095257→0.1420327486430615 |
| T_G5_stairs15_survival | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.03125→0.15625; 202: 0.03125→0.09375; 303: 0.03125→0.21875 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 26→10; 202: 30→11; 303: 29→13 |
| S_stairs10_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.53125→0.75; 202: 0.59375→0.625; 303: 0.5→0.59375 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.30537512402492606→0.19005063006500156; 202: 0.36892067344704993→0.19211986481948423; 303: 0.44727566097403154→0.18468650459457395 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13984381110366453→0.10179788320408868; 202: 0.1412283080457853→0.09975638313386591; 303: 0.14554375353750243→0.10235774077653688 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13197176738398128→0.09412670790836994; 202: 0.13163769258758068→0.09080728899485772; 303: 0.13360666624676226→0.09603920462608258 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 0→1; 202: 0→2; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'worse', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→0.9375; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.09724321104254736; 202: 0.07055512599999088→0.10147860103909068; 303: 0.06940222790799686→0.0945616382969438 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→0.96875; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0→0; 202: 0→2; 303: 0→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→0.9375; 303: 1.0→1.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.09144721339101493; 202: 0.0698239791466322→0.09960675118853221; 303: 0.0695564418189401→0.09454295080712635 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 0→0; 202: 0→1; 303: 0→1 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→0.96875; 303: 1.0→0.96875 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.09776233543009871; 202: 0.06901107798414484→0.09130158309098087; 303: 0.0687554101390921→0.0942005080016131 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 0→0; 202: 0→0; 303: 0→2 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→0.9375 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.09653081192510801; 202: 0.068929399843416→0.09407285672413927; 303: 0.06832387620766188→0.09993369727611122 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→0.9921875 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'better', '303': 'worse'} | 101: 4→4; 202: 2→0; 303: 0→2 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.16046066904381096, 'rmse': 0.2477111357426806}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.14767366730884723, 'rmse': 0.2367867922498207}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.15522838093298402, 'rmse': 0.23808606624830092} |
| S_forward_nominal_cmd_error | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06584699518880566→0.026731145152528057; 202: 0.06588044092647338→0.025196320836089137; 303: 0.06613569222880822→0.027730807663970847 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1362061008257787→0.11997204790403543; 202: 0.13378358180109215→0.11582435549163062; 303: 0.13953023417442037→0.12392715166525826 |
| S_G7_dr_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'better', '303': 'better'} | 101: 0.9375→0.78125; 202: 0.90625→0.9375; 303: 0.90625→0.9375 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.23962127644247008→0.26665110156315835; 202: 0.21095762200504264→0.24072031296031116; 303: 0.2317696478391446→0.28515680255485665 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
