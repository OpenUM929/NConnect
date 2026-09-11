# H1 공식 결과 기반 내부 proxy 교정 검토 — 2026-09-10

## 0. 예선 기준 현재 위치
- [예선 목표] H1 시뮬레이션 70점 축의 내부 점수 예측 오차를 실측하고, 이후 H1·Go2 결과 해석의 과신을 줄인다.
- [현재 단계] 단계 0/6 — 공식 결과와 제출 policy의 artifact 대응이 아직 확인되지 않았다.
- [확보] 사용자 전사 `OFFICIAL_RESULT` 57.45/70과 Run06 독립 3-seed의 역사적 `INTERNAL_GATE_PASS` 표기 65.7316/70을 각각 보존했다(`workspace/calibration/h1_official_20260910/OFFICIAL_RESULT_TRANSCRIPTION.json`의 `total`; `workspace/submission_candidates/h1_run06_model9900/INDEPENDENT_EVAL_REPORT.json`의 `independent_validation.simulation_points_70`). 현행 자세 기준에서는 H5·H6가 `POSTURE_UNMEASURED`다(`H1_REWARD_EVIDENCE_MASTER.md:329-331`).
- [미확보] 공식 평가에 사용된 제출 round·policy/checkpoint/hash가 없어 Run06과 동일 정책인지 미확인이다(공식 전사 JSON의 `submission_identity.match_status=UNCONFIRMED`).
- [이번 테스트] 기존 내부 proxy와 실제 H1 시나리오 점수의 오차·순위 불일치를 계산하고, 과적합 없는 보정 사용 경계를 고정한다.
- [흐름] Run06 내부 평가·공식 결과 확보 → **정책 대응 미확인 상태의 조건부 교정** → identity 확인 시 직접 비교 → 추가 공식 표본으로 외부검증 → 최종 제출 판단.
- [지금 할 일] 서버 작업은 없다. 다음 H1 공식 결과 회수 때 제출 round와 업로드한 `policy.pt` 식별자를 함께 보존한다.
- [보장하지 않음] 한 제출 결과를 자기 자신에 맞춘 계수는 다음 H1 점수, Go2 점수, 공식 evaluator의 생존·추종 변환식을 보장하지 않는다.

## 1. 입력과 비교 가능성

| 입력 | 증거 계층 | 식별자 / 범위 | 판정 |
|---|---|---|---|
| 사용자 제공 H1 7개 공식 점수 | `OFFICIAL_RESULT_USER_TRANSCRIPTION` | `OFFICIAL_RESULT_TRANSCRIPTION.json`의 `source.type`, `scenarios`, `total` | 합계 57.45/70 산술 일치. 화면 원본·round·policy ID는 미보존 |
| Run06 내부 독립평가 | 역사적 `INTERNAL_GATE_PASS`; 현행 자세 검증은 부분 | `INDEPENDENT_EVAL_REPORT.json`의 `independent_validation`; seed 101·202·303, 최악 seed/시나리오 | raw 65.7316335945/70. H5·H6 `POSTURE_UNMEASURED` |
| 조건부 비교 후보 | `ARTIFACT_VERIFIED`였던 로컬 후보 | `model_best_iter9900.pt` SHA-256 `8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636` | 로컬 후보 식별은 확정, 공식 제출본과의 대응은 미확인 |

기존 원장도 Run06을 위 SHA로 동결하고(`H1_REWARD_EVIDENCE_MASTER.md:266-270`), 당시 실제 제출 여부를 미측정으로 남겼다(`H1_REWARD_EVIDENCE_MASTER.md:371-372`). 이번 공식 결과는 **H1 제출물이 실제 평가됐다는 사용자 제공 증거**지만, 점수만으로 그 제출물이 Run06인지 역추론할 수 없다. 따라서 아래 비교 상태는 `CONDITIONAL_ONLY_IDENTITY_UNCONFIRMED`다(`H1_OFFICIAL_CALIBRATION.json`의 `comparison_eligibility`).

## 2. 우리 채점 결과와 공식 결과 비교

내부 점수는 기존과 동일하게 `최악 seed의 scenario_proxy × 공식 배점`으로 환산했다. 원값은 수정하지 않았다(`H1_OFFICIAL_CALIBRATION.json`의 `calibration_review.original_proxy_changed=false`).

| 시나리오 | 내부 원 proxy | 기존 내부 / 배점 | 전역계수 보정참고 / 배점 | 실제 공식 / 배점 | 내부−공식 |
|---|---:|---:|---:|---:|---:|
| H1 제자리 | 0.9269 | 9.732 / 10.5 | 8.506 / 10.5 | 8.73 / 10.5 | +1.002 |
| H2 전진 | 0.9630 | 13.482 / 14 | 11.783 / 14 | 11.54 / 14 | **+1.942** |
| H3 좌우 | 0.9810 | 6.867 / 7 | 6.002 / 7 | 5.81 / 7 | +1.057 |
| H4 회전복합 | 0.9062 | 6.343 / 7 | 5.544 / 7 | 5.78 / 7 | +0.563 |
| H5 약한 요철 | 0.9584 | 10.063 / 10.5 | 8.795 / 10.5 | 8.29 / 10.5 | +1.773 |
| H6 ±10° 경사 | 0.9735 | 10.222 / 10.5 | 8.934 / 10.5 | 8.64 / 10.5 | +1.582 |
| H7 밀침 | 0.8594 | 9.023 / 10.5 | 7.887 / 10.5 | 8.66 / 10.5 | +0.363 |
| **합계** | **0.9390 가중** | **65.732 / 70** | **57.45 / 70** | **57.45 / 70** | **+8.282** |

표의 재현 가능한 원수치는 `H1_OFFICIAL_CALIBRATION.json`의 `scenarios.H1`~`scenarios.H7`, `totals`에 있다. 보정참고는 모든 시나리오에 **하나의 전역계수 0.8740084**만 곱했으며(`adjusted_reference_points_global_ratio`), 실제 공식 시나리오별 값에 맞춘 계수는 쓰지 않았다. 합계가 57.45와 같은 것은 이 동일 표본의 총점 비율로 계수를 만들었기 때문이며 예측 검증이 아니다.

### 정밀도 진단

- [조건부 계산] 공식 제출본이 Run06이라는 가정에서 내부가 공식보다 **8.2816/70점 높다**(`totals.internal_minus_official_points`). identity 확인 전에는 확정 예측오차가 아니다.
- [조건부 계산] 같은 가정에서 시나리오 정규화 점수의 평균 편향/MAE는 모두 **0.11709**, RMSE는 **0.12536**이다(`observed_precision_diagnostics`). 일곱 차이는 모두 내부 쪽이 높은 방향이다.
- [관찰] 내부의 최대 약점은 H7이지만 공식 득점률의 최대 약점은 H5다. 약점 순위가 일치하지 않는다(`observed_precision_diagnostics.internal_weakest_to_strongest`, `official_weakest_to_strongest`, `weakest_scenario_agrees=false`).
- [추론] 현재 proxy는 이 표본의 **총 성능을 낙관적으로 보는 방향**이며, 특히 요철·경사에서 공식 조건과 내부 근사 조건의 괴리가 클 가능성이 있다. 단, 공식 생존율과 tracking 점수가 분리 제공되지 않아 그 원인을 특정할 수 없다.

## 3. 채점 기준 변경 검토와 업데이트

### 유지 — 내부 원 proxy와 gate

기존 `survival × exp(-(RMSE/0.5)^2)`와 내부 gate는 정책 간 같은 자 비교 및 안전성 검사로 유지한다. 공식 evaluator의 미공개 변환식을 한 표본으로 대체하면 오히려 과적합된다. 기존 내부 평가가 공식 점수가 아니라는 선언도 유지한다(`INDEPENDENT_EVAL_REPORT.json`의 `limitations[0]`, `independent_validation.official_score=false`).

### 추가 — 예측 보고 v2

앞으로 결과표에는 다음을 병기한다(`H1_OFFICIAL_CALIBRATION.json`의 `calibration_review.recommended_reporting_policy`).

1. **Raw internal proxy** — 기존 판정·후보 비교용 정본. 변경 없음.
2. **H1 official-calibration sensitivity** — raw 총점에 관측 전역계수 **0.8740084**를 곱한 비결정 참고열. `NON_VALIDATED_SENSITIVITY`로만 표기.
3. **관측 오차** — raw와 sensitivity를 모두 제시하고, 공식 결과가 있는 정책은 실제 공식 점수를 별도 열에 둔다.
4. **시나리오별 계수** — 이번 동일 표본을 정확히 재현하므로 진단용으로만 보존하고 튜닝 우선순위에는 사용하지 않는다.

계수는 현재 `coefficients_enabled_for_prediction=false`, `validated_prediction=false`, 공식 제출 표본 1개, 외부검증 0개다. 즉 **채점식을 교체한 것이 아니라 오차 모델을 추가한 것**이다(`calibration_review`).

### Go2 적용 경계

H1 전역계수 0.8740084를 Go2 raw proxy에 곱하는 것은 사용자가 요청한 보수적 민감도 확인에는 쓸 수 있다. 그러나 기체·G1~G7·지형·명령·평가기 구현이 다르므로 `cross_robot_transfer.apply_h1_coefficients_to_go2=false`, 기본 비활성이다. 결과 이름은 반드시 `H1_RATIO_STRESS_SENSITIVITY`로 하고 **Go2 공식 예상점수나 후보 승급 근거로 쓰지 않는다**(`H1_OFFICIAL_CALIBRATION.json`의 `cross_robot_transfer`).

## 4. 재현 명령과 검증

```powershell
python tools/build_h1_official_calibration.py `
  --internal workspace/submission_candidates/h1_run06_model9900/INDEPENDENT_EVAL_REPORT.json `
  --official workspace/calibration/h1_official_20260910/OFFICIAL_RESULT_TRANSCRIPTION.json `
  --out workspace/calibration/h1_official_20260910/H1_OFFICIAL_CALIBRATION.json
python -m unittest tools/test_build_h1_official_calibration.py
python -m py_compile tools/build_h1_official_calibration.py tools/test_build_h1_official_calibration.py
```

- 빌드: 종료 코드 0, 내부 65.7316335945 / 공식 57.45 / 관측계수 0.8740084014.
- 단위 테스트: 3건, 종료 코드 0. 입력 배점 불일치 거부, identity에 따른 비교 가능성 분리, 단일표본 계수 기본 비활성·Go2 이전 금지를 검증한다.
- 문법 검사: 종료 코드 0.
- 검증하지 않은 범위: 공식 화면 원본, 제출 round, 제출 policy tensor/해시, 공식 evaluator의 생존·tracking 분해, 두 번째 공식 제출에 대한 외부검증.

## 5. 종료 판정

**공식 제출본이 Run06과 동일하다는 조건에서** raw proxy와 공식 결과는 8.28점 차이가 나고 약점 순위도 다르다. 제출 identity가 미확인이고 H5·H6 자세가 현행 기준에서 미측정이며 공식 표본도 하나뿐이므로 H1 보정계수는 `NON_VALIDATED_SENSITIVITY`, Go2 이전은 `DISABLED`가 올바른 종료 상태다. 다음 공식 표본에서 identity를 고정해 계수를 사전 예측으로 적용한 뒤 오차를 측정해야 비로소 예측 정밀도를 검증할 수 있다.

### 2026-09-11 제출 안내본 역추적 — H1-CAL-20260910
- [관찰] PROJECT_STATE.md:1207-1208이 사용자에게 제출하도록 지시한 위치는 `workspace/submission_candidates/h1_run06_model9900/UPLOAD_READY/`다. 따라서 **우리 제출 안내본은 Run06 iter9900으로 확인**됐다. 단순히 후보가 불명이라고 표현하지 않는다.
- [ARTIFACT_VERIFIED] 해당 폴더 policy.pt/env.yaml/TECHNICAL_REPORT.md의 기존 manifest 3/3 및 회수 final/model_best.pt·env.yaml의 승인 기대 SHA 2/2가 일치했다. 검증 명령 종료 코드 0. 원자료: `workspace/calibration/h1_official_20260910/SUBMISSION_INSTRUCTION_TRACE_20260911.json:checks`.
- [관찰] 대응 학습 bundle report: `workspace/server_returns/train_260831-06_run05cfg_10000/extracted/train_260831-06_run05cfg_10000/final/report.html`, SHA c4c8054106c53227ed1272dc9eecdfb55567dce321c2724cc53cc390f40c190c. `training/humanoid/exported/report.html`은 승급 이전 파일이라는 RUN06_SUBMISSION_NOTICE.txt:7 경고와 구별한다.
- [경계] 제출 지시본 확인과 외부 업로드 확인은 다르다. 공식57.45의 정책 identity는 외부 증거가 없어 여전히 UNCONFIRMED_EXTERNAL이나, 제출 안내 이력은 Run06을 가리킨다. 기존 raw/보정 점수는 변경하지 않는다. 대시보드 업로드본 또는 제출 완료 당시 파일 식별자로 외부 대응을 닫는다.
