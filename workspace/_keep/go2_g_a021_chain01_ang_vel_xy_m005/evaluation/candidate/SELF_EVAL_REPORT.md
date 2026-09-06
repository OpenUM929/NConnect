# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 12.003/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.0032 | 0.0032 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 0.2500 | 0.2684 | 0.0671 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.4688 | 0.3823 | 0.1792 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.4062 | 0.3825 | 0.1554 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.4062 | 0.0335 | 0.0136 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.8438 | 0.9706 | 0.8189 | push_pos_x@101 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.4688 | 0.3808 | 0.1785 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
