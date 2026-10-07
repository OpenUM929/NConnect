# PC2 탐색트리 판독 — s13_action_rate_l2_m0p005

- 노드: `workspace\_keep\go2_g_a063_pc2_s13_action_rate_l2_m0p005`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'action_rate_l2': -0.005}
- 정지 판정: MOVING
- **분류: TRADEOFF**
  - target_improvements: ['T_G5_stairs15_ge2', 'T_G5_stairs15_nonstall_after_ge2', 'T_G5_stairs15_progress_ratio', 'T_G5_stairs15_survival']
  - common_losses: ['T_G3_rough_lateral_falls', 'T_G3_rough_lateral_motion', 'T_G5_stairs15_ge1', 'S_push_pos_x_post_push_rmse', 'S_push_neg_x_post_push_rmse', 'S_push_pos_y_post_push_rmse', 'S_push_neg_y_post_push_rmse', 'S_G7_dr_survival']
  - partial_seed_losses: {'S_push_pos_x_falls': ['101'], 'S_push_pos_x_survival': ['101'], 'S_push_neg_x_falls': ['202'], 'S_push_neg_x_survival': ['202'], 'S_push_pos_y_falls': ['101', '303'], 'S_push_pos_y_survival': ['101', '303'], 'S_push_neg_y_falls': ['303'], 'S_push_neg_y_survival': ['303'], 'S_rough_forward_falls': ['202', '303'], 'S_rough_forward_motion': ['202'], 'S_G7_dr_xy_rmse': ['202']}

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 13→21; 202: 16→18; 303: 12→21 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.19298743982084604, 'rmse': 0.2320435076414777}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.1947168202015424, 'rmse': 0.2315515238888889}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.19725573183502257, 'rmse': 0.2286454388147022} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→13; 202: 18→11; 303: 20→16 |
| T_G5_stairs15_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 1→6; 202: 1→7; 303: 1→6 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 1→4; 202: 1→4; 303: 1→4 |
| T_G5_stairs15_progress_ratio | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.15926055355870625→0.18109933059592725; 202: 0.15526276969988256→0.16909083398833913; 303: 0.15797493859095257→0.17222516909154356 |
| T_G5_stairs15_survival | target | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.03125→0.09375; 202: 0.03125→0.21875; 303: 0.03125→0.125 |
| S_stairs10_ge2 | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 26→31; 202: 30→31; 303: 29→31 |
| S_stairs10_survival | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.53125→0.625; 202: 0.59375→0.625; 303: 0.5→0.6875 |
| S_stairs10_progress_ratio | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.30537512402492606→0.7969621968537104; 202: 0.36892067344704993→0.8675384777961301; 303: 0.44727566097403154→0.8889459269459467 |
| S_yaw_right_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 0→0; 202: 0→0; 303: 0→0 |
| S_yaw_right_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13984381110366453→0.11889040241949991; 202: 0.1412283080457853→0.11847284982776059; 303: 0.14554375353750243→0.11902533770288426 |
| S_yaw_right_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.13197176738398128→0.09673899904984908; 202: 0.13163769258758068→0.0967450971515475; 303: 0.13360666624676226→0.09756716660368905 |
| S_push_pos_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 0→1; 202: 0→0; 303: 0→0 |
| S_push_pos_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'same'} | 101: 1.0→0.96875; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.10379961521521182; 202: 0.07055512599999088→0.10032838699546526; 303: 0.06940222790799686→0.09985688272151078 |
| S_push_pos_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_x_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 0→0; 202: 0→1; 303: 0→0 |
| S_push_neg_x_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'worse', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→0.96875; 303: 1.0→1.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.09777480412808193; 202: 0.0698239791466322→0.1012764486159454; 303: 0.0695564418189401→0.09975891446468446 |
| S_push_neg_x_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_pos_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 0→1; 202: 0→0; 303: 0→1 |
| S_push_pos_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 1.0→0.96875; 202: 1.0→1.0; 303: 1.0→0.96875 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.10163764884635454; 202: 0.06901107798414484→0.09706443529087973; 303: 0.0687554101390921→0.10030937120339618 |
| S_push_pos_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_push_neg_y_falls | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 0→0; 202: 0→0; 303: 0→1 |
| S_push_neg_y_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'worse'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→0.96875 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.09724506818419572; 202: 0.068929399843416→0.098299625208804; 303: 0.06832387620766188→0.10280431353115456 |
| S_push_neg_y_recovery_upright | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_rough_forward_falls | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'worse'} | 101: 4→3; 202: 2→4; 303: 0→3 |
| S_rough_forward_motion | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.035838460991052645, 'rmse': 0.17560640783968104}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.03876295707880978, 'rmse': 0.1813568772279158}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.03499188844503659, 'rmse': 0.17618410092158554} |
| S_forward_nominal_cmd_error | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06584699518880566→0.05482690649597266; 202: 0.06588044092647338→0.0526374756074266; 303: 0.06613569222880822→0.05660795193949808 |
| S_G4_slope_minus_20_survival | protect | NO_COMMON_DIRECTION | {'101': 'same', '202': 'same', '303': 'same'} | 101: 1.0→1.0; 202: 1.0→1.0; 303: 1.0→1.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.1362061008257787→0.11285371755820142; 202: 0.13378358180109215→0.1122175307978585; 303: 0.13953023417442037→0.11711995386211445 |
| S_G7_dr_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.9375→0.78125; 202: 0.90625→0.78125; 303: 0.90625→0.84375 |
| S_G7_dr_xy_rmse | protect | NO_COMMON_DIRECTION | {'101': 'better', '202': 'worse', '303': 'better'} | 101: 0.23962127644247008→0.22739000928944694; 202: 0.21095762200504264→0.23641617551981672; 303: 0.2317696478391446→0.21338461993469293 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 4, 'reached_ge2': 6, 'stalled_after_reach': 2, 'conditional_stall_rate': 0.3333333333333333}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 4, 'reached_ge2': 7, 'stalled_after_reach': 3, 'conditional_stall_rate': 0.42857142857142855}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 4, 'reached_ge2': 6, 'stalled_after_reach': 2, 'conditional_stall_rate': 0.3333333333333333}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
