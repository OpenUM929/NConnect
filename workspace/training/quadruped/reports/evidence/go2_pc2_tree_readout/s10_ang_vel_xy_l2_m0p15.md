# PC2 탐색트리 판독 — s10_ang_vel_xy_l2_m0p15

- 노드: `workspace\_keep\go2_g_a063_pc2_s10_ang_vel_xy_l2_m0p15`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'ang_vel_xy_l2': -0.15}
- 정지 판정: STATIONARY
- **분류: WORSENED**
  - why: ['moving gate STATIONARY(표적 개선보다 우선)']

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | NO_COMMON_DIRECTION | {'101': 'worse', '202': 'same', '303': 'worse'} | 101: 13→14; 202: 16→16; 303: 12→16 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.2530385479755956, 'rmse': 0.275026082686971}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.26048727786219583, 'rmse': 0.2782677418163177}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.2601976160380933, 'rmse': 0.2793513892033102} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→0; 202: 18→0; 303: 20→0 |
| T_G5_stairs15_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.02784512261601051; 202: 0.15526276969988256→0.028313405080349165; 303: 0.15797493859095257→0.02784874062469314 |
| T_G5_stairs15_survival | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.03125→0.0; 202: 0.03125→0.0; 303: 0.03125→0.0 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 26→0; 202: 30→0; 303: 29→0 |
| S_stairs10_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.53125→0.0; 202: 0.59375→0.0; 303: 0.5→0.0 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.30537512402492606→0.028064925148217325; 202: 0.36892067344704993→0.027946473005868028; 303: 0.44727566097403154→0.02771135276280618 |
| S_yaw_right_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→32; 202: 0→32; 303: 0→32 |
| S_yaw_right_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13984381110366453→0.15984483204827765; 202: 0.1412283080457853→0.16116353486939392; 303: 0.14554375353750243→0.161055653846474 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13197176738398128→0.5229781544146381; 202: 0.13163769258758068→0.524131727077136; 303: 0.13360666624676226→0.5211980340445014 |
| S_push_pos_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→10; 202: 0→17; 303: 0→14 |
| S_push_pos_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.6875; 202: 1.0→0.46875; 303: 1.0→0.5625 |
| S_push_pos_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.069380060215967→0.0911399451984514; 202: 0.07055512599999088→0.09503675922201521; 303: 0.06940222790799686→0.09412198001090871 |
| S_push_pos_x_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.8203125; 202: 1.0→0.6640625; 303: 1.0→0.7734375 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→14; 202: 0→13; 303: 0→9 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.5625; 202: 1.0→0.59375; 303: 1.0→0.71875 |
| S_push_neg_x_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06868000597159794→0.08998572901090217; 202: 0.0698239791466322→0.09274284135466583; 303: 0.0695564418189401→0.09354875586826827 |
| S_push_neg_x_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.7265625; 202: 1.0→0.7890625; 303: 1.0→0.84375 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→15; 202: 0→14; 303: 0→12 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.53125; 202: 1.0→0.5625; 303: 1.0→0.625 |
| S_push_pos_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06935616071552589→0.09788423345922437; 202: 0.06901107798414484→0.09777765178301044; 303: 0.0687554101390921→0.09207853305296004 |
| S_push_pos_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.7890625; 202: 1.0→0.7890625; 303: 1.0→0.8515625 |
| S_push_neg_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→13; 202: 0→11; 303: 0→11 |
| S_push_neg_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.59375; 202: 1.0→0.65625; 303: 1.0→0.65625 |
| S_push_neg_y_post_push_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.07028925895448256→0.09138339425472151; 202: 0.068929399843416→0.09063484415006647; 303: 0.06832387620766188→0.09408421962115858 |
| S_push_neg_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.734375; 202: 1.0→0.765625; 303: 1.0→0.8046875 |
| S_rough_forward_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 4→32; 202: 2→32; 303: 0→32 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.4955503884824324, 'rmse': 0.4916337224806761}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.4953269173199907, 'rmse': 0.49078065510167834}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.4952377725567636, 'rmse': 0.48967077799327097} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06584699518880566→0.7504011642964719; 202: 0.06588044092647338→0.7504419511348182; 303: 0.06613569222880822→0.7506405435667093 |
| S_G4_slope_minus_20_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.1362061008257787→0.4924162913882401; 202: 0.13378358180109215→0.4923269984729393; 303: 0.13953023417442037→0.4925153204210458 |
| S_G7_dr_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.9375→0.03125; 202: 0.90625→0.03125; 303: 0.90625→0.03125 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.23962127644247008→0.4925275339499229; 202: 0.21095762200504264→0.4905131735523843; 303: 0.2317696478391446→0.4890973416180383 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
