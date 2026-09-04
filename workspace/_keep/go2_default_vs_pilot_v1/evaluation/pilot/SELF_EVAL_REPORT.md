# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 69/69
- simulation proxy: 41.980/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.8925 | 0.8925 | forward_fast@303 | INTERNAL_SCENARIO_PASS |
| G2 | 1.0000 | 0.7521 | 0.7521 | combined_yaw_left@303 | INTERNAL_SCENARIO_PASS |
| G3 | 0.5625 | 0.5904 | 0.4403 | rough_lateral@303 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.9688 | 0.5288 | 0.5288 | slope_plus_20@303 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.8750 | 0.2595 | 0.2270 | stairs_15_down@202 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.9688 | 0.9661 | 0.9378 | push_pos_y@202 | INTERNAL_SCENARIO_PASS |
| G7 | 0.9375 | 0.5904 | 0.5781 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
