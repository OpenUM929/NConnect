# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 15.704/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.0032 | 0.0032 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 0.8125 | 0.2615 | 0.2125 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.9062 | 0.3740 | 0.3390 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.6875 | 0.3735 | 0.2568 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.6875 | 0.0097 | 0.0066 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.5312 | 0.9577 | 0.5088 | push_pos_x@101 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.9062 | 0.3730 | 0.3380 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
