# Go2 internal self evaluation

- status: INTERNAL_GATE_FAIL
- reasons: scenario_or_weighted_total_gate_failed
- telemetry: 69/69
- locomotion: POLICY_LOCOMOTES (3/69 stationary cases)
- survival definition: posture_gate_v2
- tracking std: 0.5
- simulation proxy: 39.765/70 (not official)

survival and tracking below are the worst-product case's own factors, so proxy = survival x tracking exactly.

| G | survival | tracking | proxy | worst case | gate |
|---|---:|---:|---:|---|---|
| G1 | 1.0000 | 0.8944 | 0.8944 | forward_nominal@303 | INTERNAL_SCENARIO_PASS |
| G2 | 1.0000 | 0.8921 | 0.8921 | combined_yaw_right@303 | INTERNAL_SCENARIO_PASS |
| G3 | 0.4688 | 0.7574 | 0.3550 | rough_lateral@303 | INTERNAL_SCENARIO_FAIL |
| G4 | 0.7500 | 0.6810 | 0.5108 | slope_plus_20@202 | INTERNAL_SCENARIO_FAIL |
| G5 | 0.0000 | 0.1614 | 0.0000 | stairs_10_down@202 | INTERNAL_SCENARIO_FAIL |
| G6 | 0.9062 | 0.9616 | 0.8715 | push_neg_y@202 | INTERNAL_SCENARIO_FAIL |
| G7 | 0.9062 | 0.7209 | 0.6533 | dr_seed_303@303 | INTERNAL_SCENARIO_FAIL |

Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v2.
