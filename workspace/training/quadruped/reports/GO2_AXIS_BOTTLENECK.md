# Go2 축 병목 판독 — 무엇이 점수를 묶는가 (2026-09-19)

대상 arm: `G-A033 evaluation/candidate`. 생성 `tools/go2_axis_bottleneck.py`,
증거 `reports/evidence/go2_axis_bottleneck_20260919/AXIS_BOTTLENECK.csv`, 관문 `tools/test_go2_axis_bottleneck_contract.py`.

채점식은 `workspace/training/quadruped/go2_fixed_eval_report.py:29-60` 이다. 축 점수는
**case 별 proxy 의 최솟값**이고, 계단 case 는 `completion`(전진거리/기대거리)으로 한 번 더 깎인다.
`body_rise_ge1` 같은 오르기 수는 **채점식에 들어가지 않는다** — 2026-09-18~19 에 판독·기획·감사가
모두 그 지표로 G5 를 이야기했고, 그것이 이 문서를 만든 이유다.

| 축 | 최솟값 case | 생존 | tracking | 축 점수 | 만점 | 묶는 인수 | 생존 1.0 반사실 |
|---|---|---:|---:|---:|---:|---|---:|
| G1 | `forward_fast`@101 | 1.0 | 0.87853 | **9.22452** | 10.5 | `tracking_xy` | 9.22452 |
| G2 | `combined_yaw_right`@303 | 1.0 | 0.87742 | **9.21294** | 10.5 | `tracking_xy` | 9.21294 |
| G3 | `rough_lateral`@202 | 0.375 | 0.80519 | **4.22726** | 14.0 | `survival` | 10.71746 |
| G4 | `slope_plus_20`@202 | 1.0 | 0.85883 | **9.01774** | 10.5 | `tracking_xy` | 9.01774 |
| G5 | `stairs_15_down`@202 | 0.03125 | 0.13632 | **0.04473** | 10.5 | `survival` | 1.43139 |
| G6 | `push_pos_x`@101 | 0.84375 | 0.96389 | **5.69295** | 7.0 | `survival` | 6.73997 |
| G7 | `dr_seed_101`@101 | 1.0 | 0.72978 | **5.10847** | 7.0 | `tracking_xy` | 5.10847 |

`생존 1.0 반사실` 은 **측정이 아니라 반사실 계산**이다 — 자세 게이트를 완벽히 고쳤을 때의 상한이고,
그 차이가 이득구간 밖인지는 이 표가 말하지 않는다(`reports/runs/BASELINE_MARGIN.csv` 의
`delta_resample_sd` 는 **같은 계측으로 잰 두 arm 의 차이**에 대한 값이라 계측 자체를 바꾸는
반사실에 그대로 적용할 수 없다 — 2026-09-19 감사 D4).
