# go2_tuning_engine_v1_3.zip — 로컬 검증 기록 (260903)

## 1. 산출물 신원

| 항목 | 값 |
|---|---|
| 아카이브 | `workspace/training/quadruped/go2_tuning_engine_v1_3.zip` |
| SHA-256 | `dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a` |
| 크기 | 12,781,997 B |
| 멤버 수 | 50 |
| 내부 manifest | `PACKAGE_SHA256SUMS.txt` 49/49 OK |
| 실험 사양 | `G_A015_pilot_feet_air_time_035.json`, SHA-256 `f2ac4d7fb68da95ec982c708f95664a31ec46af8d38d7a9721dbc29c8c8ca693`, 2,579 B |
| `engine_version` | `1.2.0` |

## 2. v1.2 → v1.3 변경 3건과 근거

### 2-1. tier-1 게이트를 가중 총점 기준으로 교체

`go2_tuning_eval_report.tier1_decision`의 조기 종료 판정에서 시나리오 고정 절을 제거하고
`gates.min_total_points_delta`로 대체했다. `target_scenario`는 선택 항목이 되어
`target_scenario_observation` 키에 관측값으로만 남는다(판정 `schema_version` 2 → 3).

근거는 측정된 4건 전부에서 고정 시나리오 절과 가중 총점의 부호가 반대였다는 사실이다.

| 실험 | 단일 변수 | 총점 Δ/70 | 허용 초과 생존 후퇴 | v1.1 판정 사유 |
|---|---|---:|---|---|
| G-A011 | `track_lin_vel_xy_exp` 1.0→1.2 | **+3.0903** | 없음 | `target_G1_improvement_below_0.05` |
| G-A010 | `lin_vel_z_l2` −3.0→−2.0 | **+2.2572** | 없음 (G7 −0.031) | `target_G1_improvement_below_0.05` |
| G-A013 | `flat_orientation_l2` 0.0→−1.0 | **−1.4278** | G2·G4·G5·G6 | 총점·생존 후퇴 |

대회 규정이 채점하는 값은 `Σ(weight × 시나리오 점수)`이므로 게이트도 같은 값을 본다.
생존 가드(`max_survival_regression`)는 그대로 유지해, 총점만 올리고 생존을 무너뜨리는
후보(G-A013 형태)는 계속 차단한다.

### 2-2. 동결 기준선을 선택 가능하게 (Default-01 | Pilot-01)

`FROZEN_BASELINES` 레지스트리를 추가하고, `baseline.name`이 지정한 기준선의 reward 집합과
model/env SHA-256을 검증한다. 엔진 ZIP은 `baseline/default/`와 `baseline/pilot/` 아래
두 정책의 checkpoint·env.yaml·검증된 seed 101 tier-1 case 증거를 모두 싣는다.

근거: 같은 69-case `posture_gate_v2` 스위트에서 Default-01은 `17.90697/70`, 동결 Pilot-01은
`33.79311/70`이다(G-F70). Default-01 기준 단일 변수 스크리닝은 제출할 일이 없는 정책을
최적화한다.

### 2-3. 아카이브 이름 v1_3

`go2_tuning_engine_v1_1.zip`·`v1_2.zip`은 `SUPERSEDED_DO_NOT_REUSE`다. 잘못 올려도
`engine_version` 불일치로 validate 단계에서 거부되며 학습은 시작되지 않는다.

## 3. 검증 결과

| 검사 | 결과 |
|---|---|
| ZIP CRC | `testzip()` 무결 |
| 내부 manifest | 49/49 OK |
| 실험 사양 내장 여부 | 없음 (엔진은 실험을 포함하지 않는다) |
| `.sh` CRLF | 0 |
| 추출본 `validate` | `VALID` · `work_id=G-A015` · `baseline=Pilot-01` |
| 추출본 `materialize` (Pilot-01) | candidate `feet_air_time 0.35` / baseline `0.2`, 나머지 5개 동일 |
| 기준선 checkpoint SHA | `c4d78adf…5f89af8d` (Pilot-01, G-A012 검증본과 동일) |
| 기준선 env SHA | `f5550641…5b26975d` |
| 캐시된 tier-1 case | 7/7 (`VERIFIED_G_A012`) — 기준선 재평가 불필요 |
| Default-01 경로 회귀 | 같은 엔진에서 여전히 materialize 됨 (`99ceeaa1…`) |
| 계약 테스트 | `python -m unittest discover -s tools` 47/47 OK |

## 4. 증거 경계

- `feet_air_time 0.35`가 `0.20`보다 낫다는 것은 **가설**이다. 측정된 것은 0.01 → 0.20 구간이
  같은 스위트에서 `+3.8656/70`이었다는 사실뿐이며, 곡선이 0.20~0.35 사이에서 꺾일 수 있다.
  그 경우 tier-1이 조기 종료하고 사전등록된 후속은 `0.20 → 0.28`이다.
- tier-1은 seed 101 7-case 스크리닝이다. 승격 판단은 69-case 재평가에서만 확정한다.
- `INTERNAL_*`은 내부 게이트이며 공식 결과가 아니다(`OFFICIAL_RESULT_UNMEASURED`).
- G7은 독립 증거가 아니다(G-F75: `dr_seed_*`의 `steps.csv`가 같은 seed `rough_forward`와 동일).
