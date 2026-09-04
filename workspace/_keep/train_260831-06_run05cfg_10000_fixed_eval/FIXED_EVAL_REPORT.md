# Run06 fixed-policy evaluation

This report contains measurements only; final PASS/FAIL is decided after local review.

| case | xy MAE | yaw MAE | early terminations | timeouts |
|---|---:|---:|---:|---:|
| H1_stand | 0.055861123817127385 | 0.1111637241438416 | 0 | 32 |
| H2_forward | 0.06310838516123013 | 0.12147282264639307 | 0 | 32 |
| H3_left | 0.0591664845454481 | 0.11551584671547334 | 0 | 32 |
| H3_right | 0.060434671701575356 | 0.11261887498029227 | 0 | 32 |
| H4_left | 0.05645664626136165 | 0.1230133025986288 | 0 | 32 |
| H4_right | 0.0634153451099536 | 0.12534940090340388 | 0 | 32 |
| H5_rough | 0.07977234089219636 | 0.14586890675895825 | 0 | 32 |
| H6_minus10 | 0.06376332609754459 | 0.12115283765865296 | 0 | 32 |
| H6_plus10 | 0.06429866516103058 | 0.1196926823560375 | 0 | 32 |
| H7_push | 0.06517696226699758 | 0.11191103291976924 | 0 | 32 |

## H7 recovery proxy
- observed disturbances: 114
- recovered events: 114
- median recovery seconds: 0.1800000000000006

## Internal seven-scenario scorecard
- status: SELF_ASSESSMENT_PASS
- simulation proxy: 94.34/100
- simulation points proxy: 66.04/70
- missing scenarios: none
- failed scenarios: none

| scenario | survival proxy | tracking proxy | scenario proxy | gate |
|---|---:|---:|---:|---|
| H1 | 1.0000 | 0.9268 | 0.9268 | INTERNAL_SCENARIO_PASS |
| H2 | 1.0000 | 0.9631 | 0.9631 | INTERNAL_SCENARIO_PASS |
| H3 | 1.0000 | 0.9812 | 0.9812 | INTERNAL_SCENARIO_PASS |
| H4 | 1.0000 | 0.9051 | 0.9051 | INTERNAL_SCENARIO_PASS |
| H5 | 1.0000 | 0.9568 | 0.9568 | INTERNAL_SCENARIO_PASS |
| H6 | 1.0000 | 0.9738 | 0.9738 | INTERNAL_SCENARIO_PASS |
| H7 | 1.0000 | 0.8906 | 0.8906 | INTERNAL_SCENARIO_PASS |

## Limitations
- The exact official tracking-score transform is not disclosed; self_assessment is internal proxy v1.
- Proxy-v1 thresholds were frozen after viewing partial H4/H6/H7 telemetry; those cases are calibration, not independent validation.
- One checkpoint and one fixed seed do not establish generalization.
- The H7 recovery calculation is an internal proxy, not an official score definition.
- A completed run is evidence collection, not an automatic PASS decision.
