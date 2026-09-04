# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 69/69
- simulation proxy: 17.907/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.0036 | 0.0036 | forward_fast@202 | INTERNAL_SCENARIO_FAIL |
| G2 | 1.0000 | 0.2653 | 0.2653 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.7188 | 0.3677 | 0.2655 | rough_forward@303 | INTERNAL_SCENARIO_FAIL |
| G4 | 1.0000 | 0.3835 | 0.3835 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 1.0000 | 0.1318 | 0.1318 | stairs_10_down@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.6250 | 0.9352 | 0.5854 | push_neg_x@303 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.7188 | 0.3677 | 0.2655 | dr_seed_303@303 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
