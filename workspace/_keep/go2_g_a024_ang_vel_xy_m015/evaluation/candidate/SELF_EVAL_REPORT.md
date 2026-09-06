# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- telemetry: 7/7
- simulation proxy: 0.000/70 (not official)

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 0.0000 | 0.0037 | 0.0000 | forward_fast@101 | INTERNAL_SCENARIO_FAIL |
| G2 | 0.0000 | 0.2675 | 0.0000 | diagonal_left@101 | INTERNAL_SCENARIO_FAIL |
| G3 | 0.0000 | 0.3717 | 0.0000 | rough_forward@101 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.0000 | 0.3795 | 0.0000 | slope_plus_20@101 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.0000 | 0.0325 | 0.0000 | stairs_15_up@101 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.0000 | 0.9786 | 0.0000 | push_pos_x@101 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.0000 | 0.3690 | 0.0000 | dr_seed_101@101 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1.
