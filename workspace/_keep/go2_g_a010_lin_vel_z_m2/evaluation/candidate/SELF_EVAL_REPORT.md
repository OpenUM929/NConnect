# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 19.794/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.0031 | 0.0031 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 1.0000 | 0.2662 | 0.2662 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.8438 | 0.3697 | 0.3120 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 1.0000 | 0.3671 | 0.3671 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 1.0000 | 0.0000 | 0.0000 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 1.0000 | 0.9610 | 0.9610 | push_pos_x@101 | INTERNAL_SCENARIO_PASS |
| G7 | 0.7812 | 0.3691 | 0.2884 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
