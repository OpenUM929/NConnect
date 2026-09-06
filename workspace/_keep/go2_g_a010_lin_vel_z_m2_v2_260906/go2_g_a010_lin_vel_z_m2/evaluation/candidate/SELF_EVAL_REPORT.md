# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 9.500/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 0.5938 | 0.0031 | 0.0018 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 0.3438 | 0.2662 | 0.0915 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.5000 | 0.3697 | 0.1849 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.3438 | 0.3671 | 0.1262 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.3125 | 0.0000 | 0.0000 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.4688 | 0.9610 | 0.4505 | push_pos_x@101 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.5625 | 0.3691 | 0.2076 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
