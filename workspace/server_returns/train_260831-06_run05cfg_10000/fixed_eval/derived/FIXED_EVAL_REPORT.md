# Run06 fixed-policy evaluation

This report contains measurements only; final PASS/FAIL is decided after local review.

| case | xy MAE | yaw MAE | early terminations | timeouts |
|---|---:|---:|---:|---:|
| H4_left | 0.058811506299803445 | 0.12414169252990784 | 0 | 0 |
| H4_right | 0.06570976918667785 | 0.12629217177139557 | 0 | 0 |
| H6_minus10 | 0.06376332609754459 | 0.12115283765865296 | 0 | 32 |
| H6_plus10 | 0.06429866516103058 | 0.1196926823560375 | 0 | 32 |
| H7_push | 0.06517696226699758 | 0.11191103291976924 | 0 | 32 |

## H7 recovery proxy
- observed disturbances: 114
- recovered events: 114
- median recovery seconds: 0.1800000000000006

## Limitations
- One checkpoint and one fixed seed do not establish generalization.
- The H7 recovery calculation is an internal proxy, not an official score definition.
- A completed run is evidence collection, not an automatic PASS decision.
