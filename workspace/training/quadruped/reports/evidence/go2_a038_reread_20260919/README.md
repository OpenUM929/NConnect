# go2_a038_reread_20260919 — 증거

판독문: `workspace/training/quadruped/reports/GO2_A038_REREAD_20260919.md`
생성기: `tools/go2_a038_reread.py`

```
PYTHONIOENCODING=utf-8 python -B tools/go2_a038_reread.py
```

한 번 돌리면 아래 CSV 전부가 다시 만들어진다. 손으로 입력한 값은 없다 — 모두
`workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/` 과
`workspace/_keep/go2_g_a038_a033_ang_vel_xy_m008/` 의 `summary.json` · `steps.csv`,
그리고 `workspace/training/quadruped/config/go2_self_eval_registry.json` 에서 읽거나
그 행으로 계산한 것이다.

| 파일 | 내용 | 원자료 |
|---|---|---|
| `CASE_SUMMARY.csv` | 두 arm × seed 101/202/303 × case 5종의 `summary.json` 전 필드, 채점 4변형 재구성 | `evaluation/candidate/cases/seed_*/<case>/summary.json` |
| `AXIS_RECON.csv` | G3·G5(`stairs_10_down`) 축 재구성, 채점 가능 여부, A038−A033 차이 | 위 |
| `CLIMB_COUNT.csv` | `stairs_10_down` 오른 로봇 수 — `tools/go2_climb_count.py` 를 그대로 호출(자세 게이트 미사용) | `steps.csv` `root_z` |
| `STAIRS10_PER_ENV.csv` · `STAIRS10_ROLLUP.csv` | 개체(env) 32대별 자세·높이·속도·이동·지형, seed별 집계 | `steps.csv` |
| `STAIRS10_TIME_PROFILE.csv` | 100 step 구간별 높이 중앙값·속도·기울기·서 있는 비율 | `steps.csv` |
| `ROUGH_LATERAL_PER_ENV.csv` · `ROUGH_LATERAL_ROLLUP.csv` | 같은 항목의 `rough_lateral` 판 | `steps.csv` |
| `FALL_CHANNEL_PER_ENV.csv` · `FALL_CHANNEL_ROLLUP.csv` | 낙상 판정을 높이 채널(`height_rel < 0.18`)과 기울기 채널(`proj_grav_z > -0.5`)로 분해 — `go2_eval_telemetry.py:295-330` 재생 | `steps.csv` |

성격 분류(분석가 규칙): 전부 **측정**이다. 예측·이득구간 값은 이 폴더에 없다
(이득구간은 `reports/runs/BASELINE_MARGIN.csv`, 계단 하한은
`reports/evidence/go2_fact_rules_20260917/CLIMB_GUARD.csv` 를 인용한다).

재생 검증: `FALL_CHANNEL_*` 의 `fall_by_either` 개체 수는 `summary.json` 의
`fallen_env_count` 와 A-038 3 seed 전부, A-033 3 seed 전부에서 일치한다
(`posture_fall_env_count_optimistic` 과는 A-033 seed 202·303 에서 1대 차 — 미관측 행 처리).
