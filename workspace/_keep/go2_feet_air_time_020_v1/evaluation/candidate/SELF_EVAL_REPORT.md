# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 69/69
- simulation proxy: 21.773/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.0036 | 0.0036 | forward_fast@202 | INTERNAL_SCENARIO_FAIL |
| G2 | 1.0000 | 0.2694 | 0.2694 | diagonal_left@202 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.9062 | 0.3778 | 0.3544 | rough_forward@303 | INTERNAL_SCENARIO_FAIL |
| G4 | 1.0000 | 0.3720 | 0.3720 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 1.0000 | 0.0990 | 0.0990 | stairs_15_up@303 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.9688 | 0.9613 | 0.9313 | push_pos_x@101 | INTERNAL_SCENARIO_PASS |
| G7 | 0.9375 | 0.3778 | 0.3544 | dr_seed_303@303 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
