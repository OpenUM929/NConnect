# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 2.093/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 0.0000 | 0.0038 | 0.0000 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 0.0000 | 0.2732 | 0.0000 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.0312 | 0.3917 | 0.0122 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.0000 | 0.3925 | 0.0000 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.0000 | 0.0503 | 0.0000 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.2500 | 0.9508 | 0.2377 | push_pos_x@101 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.0938 | 0.3922 | 0.0368 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
