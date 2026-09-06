# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 50.199/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.9031 | 0.9031 | forward_fast@101 | INTERNAL_SCENARIO_PASS |
| G2 | 1.0000 | 0.9659 | 0.9659 | diagonal_left@101 | INTERNAL_SCENARIO_PASS |
| G3 | 0.9062 | 0.6282 | 0.5693 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.7812 | 0.7286 | 0.5692 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.7188 | 0.7217 | 0.5187 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.9688 | 0.9642 | 0.9341 | push_pos_x@101 | INTERNAL_SCENARIO_PASS |
| G7 | 1.0000 | 0.6632 | 0.6632 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
