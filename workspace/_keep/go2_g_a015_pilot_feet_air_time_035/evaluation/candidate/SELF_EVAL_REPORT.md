# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 16.369/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 0.0312 | 0.5561 | 0.0174 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 1.0000 | 0.9122 | 0.9122 | diagonal_left@101 | INTERNAL_SCENARIO_PASS |
| G3 | 0.0000 | 0.4312 | 0.0000 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.0000 | 0.4577 | 0.0000 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.0000 | 0.1888 | 0.0000 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.9375 | 0.9481 | 0.8888 | push_pos_x@101 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.1250 | 0.4427 | 0.0553 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
