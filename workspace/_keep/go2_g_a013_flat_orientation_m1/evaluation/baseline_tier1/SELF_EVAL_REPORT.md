# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 17.132/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.0036 | 0.0036 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 1.0000 | 0.2653 | 0.2653 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.7500 | 0.3709 | 0.2782 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 1.0000 | 0.3835 | 0.3835 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 1.0000 | 0.0336 | 0.0336 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.6562 | 0.9434 | 0.6191 | push_pos_x@101 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.6562 | 0.3703 | 0.2430 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
