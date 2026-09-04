# Run06 independent multi-seed validation

- status: INDEPENDENT_VALIDATION_PASS
- simulation proxy: 93.90/100
- simulation points proxy: 65.73/70
- predeclared seeds: 101, 202, 303
- missing seeds: none
- failed seeds: none

| scenario | worst survival | worst tracking | worst proxy | gate |
|---|---:|---:|---:|---|
| H1 | 1.0000 | 0.9269 | 0.9269 | INDEPENDENT_SCENARIO_PASS |
| H2 | 1.0000 | 0.9630 | 0.9630 | INDEPENDENT_SCENARIO_PASS |
| H3 | 1.0000 | 0.9810 | 0.9810 | INDEPENDENT_SCENARIO_PASS |
| H4 | 1.0000 | 0.9062 | 0.9062 | INDEPENDENT_SCENARIO_PASS |
| H5 | 1.0000 | 0.9584 | 0.9584 | INDEPENDENT_SCENARIO_PASS |
| H6 | 1.0000 | 0.9735 | 0.9735 | INDEPENDENT_SCENARIO_PASS |
| H7 | 1.0000 | 0.8594 | 0.8594 | INDEPENDENT_SCENARIO_PASS |

## Limitations
- This remains an internal proxy, not an official competition score.
- Three seeds reduce but do not eliminate simulation generalization uncertainty.
- The scenario definitions approximate the disclosed competition descriptions.
- The policy, proxy formula and thresholds are frozen before these seeds are run.
