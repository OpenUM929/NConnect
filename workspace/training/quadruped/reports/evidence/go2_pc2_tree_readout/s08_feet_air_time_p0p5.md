# PC2 탐색트리 판독 — s08_feet_air_time_p0p5

- 노드: `workspace\_keep\go2_g_a063_pc2_s08_feet_air_time_p0p5`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'feet_air_time': 0.5}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G3_rough_lateral_falls']
  - common_losses: ['T_G5_stairs15_ge1', 'T_G5_stairs15_nonstall_after_ge2', 'T_G5_stairs15_progress_ratio', 'T_G5_stairs15_survival', 'S_stairs10_ge2', 'S_stairs10_progress_ratio', 'S_push_pos_x_falls', 'S_push_pos_x_survival', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_falls', 'S_push_neg_x_survival', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_falls', 'S_push_pos_y_survival', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_falls', 'S_push_neg_y_survival', 'S_push_neg_y_post_push_rmse', 'S_forward_nominal_cmd_error', 'S_G7_dr_xy_rmse']
  - partial_seed_losses: {'T_G3_rough_lateral_motion': ['202'], 'T_G5_stairs15_ge2': ['202', '303'], 'S_stairs10_survival': ['202', '303'], 'S_rough_forward_motion': ['202', '303']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 13→6; 202: 16→9; 303: 12→4 |
| T_G3_rough_lateral_motion | target | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.11518242605871026, 'rmse': 0.18858389155010166}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.138913102114028, 'rmse': 0.20991992772637796}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.09727838433631683, 'rmse': 0.17102202090205448} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→1; 202: 18→0; 303: 20→0 |
| T_G5_stairs15_ge2 | target | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 1→1; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.1370854056661775; 202: 0.15526276969988256→0.12717672393083923; 303: 0.15797493859095257→0.12864845287853308 |
| T_G5_stairs15_survival | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.03125→0.0; 202: 0.03125→0.0; 303: 0.03125→0.0 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 26→14; 202: 30→12; 303: 29→14 |
| S_stairs10_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'worse'} | 101: 0.53125→0.53125; 202: 0.59375→0.53125; 303: 0.5→0.46875 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.30537512402492606→0.19435652223604846; 202: 0.36892067344704993→0.206477733867039; 303: 0.44727566097403154→0.20867366081161887 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13984381110366453→0.10552553410861709; 202: 0.1412283080457853→0.1062351647303858; 303: 0.14554375353750243→0.10536153361185942 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13197176738398128→0.08809229497256989; 202: 0.13163769258758068→0.08855035336733331; 303: 0.13360666624676226→0.08809783056505495 |
| S_push_pos_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→4; 202: 0→3; 303: 0→5 |
| S_push_pos_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.875; 202: 1.0→0.90625; 303: 1.0→0.84375 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.10672655464660676; 202: 0.07055512599999088→0.0994706710215182; 303: 0.06940222790799686→0.10829215395007913 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→4; 202: 0→3; 303: 0→4 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.875; 202: 1.0→0.90625; 303: 1.0→0.875 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.1046485357910374; 202: 0.0698239791466322→0.10290775369472341; 303: 0.0695564418189401→0.10199874067407315 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→1; 202: 0→2; 303: 0→4 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.96875; 202: 1.0→0.9375; 303: 1.0→0.875 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.09403519711480046; 202: 0.06901107798414484→0.10583887185958088; 303: 0.0687554101390921→0.10465484933714285 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→2; 202: 0→3; 303: 0→2 |
| S_push_neg_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.9375; 202: 1.0→0.90625; 303: 1.0→0.9375 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.10013502492504515; 202: 0.068929399843416→0.10256493410959192; 303: 0.06832387620766188→0.09353631272361808 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'better', '303': 'same'} | 101: 4→3; 202: 2→0; 303: 0→0 |
| S_rough_forward_motion | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.030649027239420146, 'rmse': 0.19116654998743438}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.0931195734395035, 'rmse': 0.25573105824009823}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.052957281063420514, 'rmse': 0.21393581153973285} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06584699518880566→0.07752753219910358; 202: 0.06588044092647338→0.07963454547093107; 303: 0.06613569222880822→0.07777404709474034 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1362061008257787→0.08676390354625545; 202: 0.13378358180109215→0.09132974300206771; 303: 0.13953023417442037→0.09085283699912362 |
| S_G7_dr_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.9375→1.0; 202: 0.90625→0.96875; 303: 0.90625→0.96875 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.23962127644247008→0.24069934545053642; 202: 0.21095762200504264→0.2751078748531017; 303: 0.2317696478391446→0.29288802546684095 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 1, 'stalled_after_reach': 1, 'conditional_stall_rate': 1.0}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
