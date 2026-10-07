# PC2 탐색트리 판독 — s09_ang_vel_xy_l2_m0p3

- 노드: `workspace\_keep\go2_g_a063_pc2_s09_ang_vel_xy_l2_m0p3`
- 비교 부모(a048_seed42): `workspace\server_returns\G-A060\extracted\go2_g_a060_pc2_a048_seed42`
- 비교 부모 대비 변경: {'ang_vel_xy_l2': -0.3}
- 정지 판정: STATIONARY
- **분류: WORSENED**
  - why: ['moving gate STATIONARY(표적 개선보다 우선)']

| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |
|---|---|---|---|---|
| T_G3_rough_lateral_falls | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 13→32; 202: 16→32; 303: 12→32 |
| T_G3_rough_lateral_motion | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14933934216601233, 'rmse': 0.20522460467308345}→{'abs_error': 0.30109973387176064, 'rmse': 0.31153399020627365}; 202: {'abs_error': 0.1491048393115072, 'rmse': 0.20229972387228073}→{'abs_error': 0.3013446553469678, 'rmse': 0.31279059738857573}; 303: {'abs_error': 0.14634944355083798, 'rmse': 0.2003756974848173}→{'abs_error': 0.3009293883089763, 'rmse': 0.31320739819081395} |
| T_G5_stairs15_ge1 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 14→0; 202: 18→0; 303: 20→0 |
| T_G5_stairs15_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_nonstall_after_ge2 | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1→0; 202: 1→0; 303: 1→0 |
| T_G5_stairs15_progress_ratio | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.15926055355870625→0.024312721103270662; 202: 0.15526276969988256→0.024277651021839104; 303: 0.15797493859095257→0.024533080316876302 |
| T_G5_stairs15_survival | target | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.03125→0.0; 202: 0.03125→0.0; 303: 0.03125→0.0 |
| S_stairs10_ge2 | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 26→0; 202: 30→0; 303: 29→0 |
| S_stairs10_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.53125→0.0; 202: 0.59375→0.0; 303: 0.5→0.0 |
| S_stairs10_progress_ratio | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.30537512402492606→0.02447849937427965; 202: 0.36892067344704993→0.02404990455316876; 303: 0.44727566097403154→0.024418036146569636 |
| S_yaw_right_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→32; 202: 0→32; 303: 0→32 |
| S_yaw_right_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_yaw_right_yaw_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13984381110366453→0.2113831161867631; 202: 0.1412283080457853→0.20993160776409994; 303: 0.14554375353750243→0.20898730591490797 |
| S_yaw_right_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.13197176738398128→0.5710466768946628; 202: 0.13163769258758068→0.5707232755927846; 303: 0.13360666624676226→0.5715055787542616 |
| S_push_pos_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→32; 202: 0→32; 303: 0→32 |
| S_push_pos_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_push_pos_x_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.069380060215967→0.05118227813338099; 202: 0.07055512599999088→0.051314793793843315; 303: 0.06940222790799686→0.05120437734066584 |
| S_push_pos_x_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_push_neg_x_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→32; 202: 0→32; 303: 0→32 |
| S_push_neg_x_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_push_neg_x_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06868000597159794→0.05118398814619639; 202: 0.0698239791466322→0.05106444637296486; 303: 0.0695564418189401→0.05115501485102802 |
| S_push_neg_x_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_push_pos_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→32; 202: 0→32; 303: 0→32 |
| S_push_pos_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_push_pos_y_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.06935616071552589→0.051069776548393515; 202: 0.06901107798414484→0.051309312100431374; 303: 0.0687554101390921→0.051493514657772924 |
| S_push_pos_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_push_neg_y_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0→32; 202: 0→32; 303: 0→32 |
| S_push_neg_y_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_push_neg_y_post_push_rmse | protect | COMMON_IMPROVEMENT | {'101': 'better', '202': 'better', '303': 'better'} | 101: 0.07028925895448256→0.05126336938363536; 202: 0.068929399843416→0.051544053543215555; 303: 0.06832387620766188→0.051177972308200974 |
| S_push_neg_y_recovery_upright | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_rough_forward_falls | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 4→32; 202: 2→32; 303: 0→32 |
| S_rough_forward_motion | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: {'abs_error': 0.14389231611321246, 'rmse': 0.23163547322585054}→{'abs_error': 0.4974378910435064, 'rmse': 0.492366277589876}; 202: {'abs_error': 0.10030702088473559, 'rmse': 0.16845034274818782}→{'abs_error': 0.4971879388876588, 'rmse': 0.49155906962503054}; 303: {'abs_error': 0.12981202803889502, 'rmse': 0.20663266128640845}→{'abs_error': 0.49758556288984657, 'rmse': 0.4916879023237451} |
| S_forward_nominal_cmd_error | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.06584699518880566→0.7487370670440698; 202: 0.06588044092647338→0.7491162859834519; 303: 0.06613569222880822→0.7487029617515032 |
| S_G4_slope_minus_20_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 1.0→0.0; 202: 1.0→0.0; 303: 1.0→0.0 |
| S_G4_slope_minus_20_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.1362061008257787→0.4928045770511809; 202: 0.13378358180109215→0.4930797885240535; 303: 0.13953023417442037→0.49279308403406497 |
| S_G7_dr_survival | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.9375→0.0; 202: 0.90625→0.0; 303: 0.90625→0.0 |
| S_G7_dr_xy_rmse | protect | COMMON_LOSS | {'101': 'worse', '202': 'worse', '303': 'worse'} | 101: 0.23962127644247008→0.4924088525529949; 202: 0.21095762200504264→0.4933766174906962; 303: 0.2317696478391446→0.4925167783439921 |

도달 후 정체(기술 지표, 투표 안 함):
- seed 101: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 202: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}
- seed 303: 부모 {'value': 1, 'reached_ge2': 1, 'stalled_after_reach': 0, 'conditional_stall_rate': 0.0} / 노드 {'value': 0, 'reached_ge2': 0, 'stalled_after_reach': 0, 'conditional_stall_rate': 'NOT_APPLICABLE'}

평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2).
