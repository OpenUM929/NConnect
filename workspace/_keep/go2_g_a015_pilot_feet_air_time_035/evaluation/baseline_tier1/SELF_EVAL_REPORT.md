# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 46.491/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.8932 | 0.8932 | forward_fast@101 | INTERNAL_SCENARIO_PASS |
| G2 | 1.0000 | 0.9247 | 0.9247 | diagonal_left@101 | INTERNAL_SCENARIO_PASS |
| G3 | 0.8125 | 0.5967 | 0.4848 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 1.0000 | 0.5533 | 0.5533 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.7188 | 0.5696 | 0.4094 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.9688 | 0.9712 | 0.9408 | push_pos_x@101 | INTERNAL_SCENARIO_PASS |
| G7 | 0.9375 | 0.5975 | 0.5601 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
