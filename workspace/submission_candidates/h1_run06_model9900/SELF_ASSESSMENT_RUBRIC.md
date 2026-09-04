# Run06 제출 전 자체 채점표 v1

> 이 채점표는 운영진 점수가 아니다. 공개된 70/20/10 구조에 맞춰 제출 전 중단·승급을
> 결정하는 내부 기준이며, 공식 evaluator의 비공개 tracking 변환을 대체하지 못한다.

## 1. 시뮬레이션 proxy — 70점

### 고정 계산식

- 시나리오 점수: `survival_proxy × tracking_proxy`
- tracking proxy: `exp(-(RMSE/0.5)^2)`
- 방향 쌍 H3·H4·H6: 두 방향 중 최악값
- H7: 추종 proxy와 `recovered / expected pushes` 중 작은 값
- 시나리오 gate: survival ≥ 0.95 그리고 tracking ≥ 0.70
- 전체 gate: H1~H7 전부 측정·통과 그리고 가중 simulation proxy ≥ 0.70

### 검증 계층

| 계층 | 조건 | 현재 상태 |
|---|---|---|
| 교정 평가 | seed 42, 32 env, 10 case, 1,000 step | `CALIBRATION_PASS`, 66.04/70 |
| 독립 평가 | 사전등록 seed 101·202·303, 동일 10 case | `INDEPENDENT_VALIDATION_PASS`, 65.73/70 |
| 공식 평가 | 운영진 evaluator | `OFFICIAL_RESULT_UNMEASURED` |

`CALIBRATION_PASS`는 threshold를 부분 seed 42 자료를 본 뒤 고정했으므로 독립 성능 검증이 아니다.
이후 동결한 정책·식·threshold로 독립 평가를 수행했고, 각 시나리오에 대해 세 seed 중 최악
survival·tracking·scenario proxy를 사용해 전부 내부 gate를 통과했다.

## 2. 설계 의도 자체감사 — 18/20

| 항목 | 배점 | 자체점수 | 근거 |
|---|---:|---:|---|
| 실제 `env.yaml` reward 값과 리포트 일치 | 6 | 6 | 리포트 §4와 후보 `env.yaml` 대조 |
| Run04→05→06 변경·비교 추적성 | 4 | 4 | 리포트 §3, run·iter·SHA 식별 |
| survival·tracking 교환관계와 한계 설명 | 4 | 4 | 리포트 §2·§5·§6 |
| H1~H7 설계 연결 | 3 | 3 | 리포트 §5 시나리오 표 |
| 운영진 의도와 동일한지에 대한 불확실성 선언 | 3 | 1 | 자체검증만 완료; 공식 의도분석 미측정 |

## 3. 리포트 완성도 자체감사 — 9/10

| 항목 | 배점 | 자체점수 | 근거 |
|---|---:|---:|---|
| 정책·환경·리포트 식별 | 2 | 2 | 리포트 §1 |
| 변경 이유와 결과의 수치 제시 | 2 | 2 | 리포트 §3 |
| 시나리오별 증거와 한계 분리 | 2 | 2 | 리포트 §5 |
| 과장·공식 점수 오인 방지 | 2 | 2 | 리포트 §6 |
| 외부 심사자의 가독성·설득력 | 2 | 1 | 자체검토만 완료 |

## 4. 제출 승급 규칙

- 문서 자체감사: 27/30
- 최소 총점: simulation proxy + 27 ≥ 70/100
- 운영 목표: 75/100 이상
- 필수 조건: `INDEPENDENT_VALIDATION_PASS`
- 현재 내부 산술값: 65.73 + 27 = **92.73/100**
- 현재 상태: `INDEPENDENT_VALIDATION_PASS`로 내부 성능 제출 승급 완료
- 제한: 내부 proxy이므로 운영진 공식 점수·예선 합격을 보장하지 않음
