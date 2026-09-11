# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- reasons: scenario_or_weighted_total_gate_failed
- telemetry: 69/69
- locomotion: POLICY_LOCOMOTES (0/69 stationary cases)
- survival definition: posture_gate_v2
- tracking std: 0.5
- simulation proxy: 33.671/70 (not official)

survival and tracking below are the worst-product case's own factors, so proxy = survival x tracking exactly.

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.8925 | 0.8925 | forward_fast@303 | INTERNAL_SCENARIO_PASS |
| G2 | 1.0000 | 0.7521 | 0.7521 | combined_yaw_left@303 | INTERNAL_SCENARIO_PASS |
| G3 | 0.0938 | 0.7828 | 0.0734 | rough_lateral@303 | INTERNAL_SCENARIO_FAIL |
| G4 | 1.0000 | 0.5288 | 0.5288 | slope_plus_20@303 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.0000 | 0.1347 | 0.0000 | stairs_15_down@202 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.9688 | 0.9661 | 0.9359 | push_neg_x@101 | INTERNAL_SCENARIO_PASS |
| G7 | 0.8438 | 0.5540 | 0.4674 | dr_seed_202@202 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v2.
