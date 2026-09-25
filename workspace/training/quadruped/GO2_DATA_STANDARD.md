# Go2 데이터 의미 명세 v1

## 목적과 범위
목적은 **처음 읽는 사람이 숨은 정의를 추측하지 않고 해석하는 것**이다. 숫자 오류와 의미 오류를 구분한다.
이번 조사에서는 집계 CSV의 숫자가 손상됐다는 증거보다, 생성 단계에서 **대리 지표에 원 보상 항 이름을 붙이고 집단·좌표계·창을 생략한 문제**를 확인했다.
적용 완료 범위는 TILT, SITUATIONS, PROBE_SITUATIONS, FALL_CHANNEL_ROLLUP, CLIMB_REWARD의 5개 집계표다. 전체 원자료의 재검증/이관 완료가 아니다.

## 1. 확인한 원천 원인
| 생성 위치 | 생략/과장된 의미 | 잘못 시작하게 만든 해석 | 표준 표현 |
|---|---|---|---|
| `tools/go2_reward_mechanism.py::tilt_case` | `terminated`는 base-contact 집단; `survivors`는 그 밖의 집단 | 전체 종료/자세 생존 집단으로 오독 | `base_contact_env_count`, `non_base_contact_*` |
| 같은 함수 | 접촉 전 1.0~0.5초 창 vs 비접촉 개체 전체 episode; 유효 창 표본 수 없음 | 같은 시간창의 두 집단 비교, 19×13을 모든 행의 분모로 일반화 | 창별 명세, 유효 분모 UNKNOWN; AUC를 효과량/인과로 해석 금지 |
| `window_values` | `lin_vel_z_l2`에 월드 높이 차분² | 몸통 좌표 원 보상식 실측으로 오독 | `world_height_difference_velocity_squared_mean`, SURROGATE |
| `window_values` | `ang_vel_xy_l2`에 기울기 크기의 차분² | roll/pitch 각속도 제곱합과 동일시 | `inclination_magnitude_difference_rate_squared_mean`, SURROGATE |
| `situation_groups` | seeds 합침; 10cm 오른 집단과 15cm 정지 집단; upright는 비접촉 라벨 | 동일 조건 인과 대조, 실제 자세 생존으로 오독 | 지형·선택 조건·시간창·seed pooling을 명세 |
| `probe_situations` | delta는 고정 행동에서 가중치만 바꾼 부분 산술 | 재학습 후 개선량/점수 예측으로 오독 | `fixed_behavior_*_partial_margin_delta`, COUNTERFACTUAL |
| `tools/go2_stairs_behavior.py::climb_reward_rows` | 모든 정책에 A033 가중치, 2항만 계산 | 그 run 학습 보상/총 보상으로 오독 | `a033_*`, `two_term_partial` 명시 |
| `tools/go2_a038_reread.py::channel_rollup` | tilt-only와 both 구별; union은 별도 연속 타이머 | tilt-only=0을 tilt 채널 전체=0으로 오독 | only/both/union 명칭 보존; 합산 등식 임의 가정 금지 |

기존 주석에 일부 한계가 있었지만 **표와 함께 전달되지 않았다**. 각 역할의 기억·원문 재발견에 의존한 것이 구조적 원인이다.

## 2. 단일 명세와 파일 관계
- 기계 판독 정본: `config/go2_evidence_data_dictionary.json` — 각 표의 원 경로, 고유키, 생성 함수, 집단, 창, 집계, 한계와 **모든 수치 열**의 뜻/단위/계산식/근거 종류를 정의한다.
- 사람용 이 문서는 원칙과 진단이다. 수치 열 정의를 다른 문서에 별도 정본으로 복제하지 않는다.
- 표준 생성기: `tools/go2_standardize_evidence.py`.
- 소비용 출력: `reports/evidence/go2_standardized_v1/standardized.json`. 명세와 값이 함께 들어 있고 원 CSV/생성 코드/명세/변환기의 SHA를 보존한다. 해시는 무결성이며 정책 동일성이나 수치 타당성 증명이 아니다.
- 원 CSV/steps/log/checkpoint/승인 ZIP은 수정하지 않는다. 기존 이름은 `legacy_column`으로만 보존한다. 이것은 **의미 명세를 붙인 무손실 뷰**이며 누락 채널을 복원하거나 surrogate를 실제 reward로 바꾸지 않는다.
- 명령: `python -B tools/go2_standardize_evidence.py`; 검증: `python -B -m unittest tools.test_go2_data_standard_contract -q`.

## 3. 신규 집계 데이터 필수 계약
1. 식별자: run, checkpoint iter/model SHA, evaluator/registry 버전, 학습 seed와 평가 seed를 구별한다. 집계표만으로 회수 못하면 UNKNOWN과 원 manifest 회수 경로를 남긴다. 폴더명으로 추정하지 않는다.
2. 행의 단위: env-step / env-window / case-seed / seed-pool을 명시한다. 합친 seed의 불확실성을 독립 학습 반복으로 바꾸지 않는다.
3. 열: 고유한 이름, 단위, 좌표계, 원 채널, 정확한 계산식, 유효 표본 수/분모, 시간창, 제외/절단 처리, 집계 가중법을 함께 저장한다. 분모가 기존 집계에 없으면 UNKNOWN, 다음 생성기부터 반드시 출력한다.
4. 종류: MEASURED / DERIVED / SURROGATE / COUNTERFACTUAL / HYPOTHESIS를 구별한다. 대리값은 원 reward와 같은 이름을 쓰지 않는다.
5. 누락: JSON null + reason. 0은 실제 계산된 0이다. 빈 CSV는 0으로 채우지 않는다. NaN/Infinity는 오류로 거부한다.
6. 변경: schema_version·생성 코드·원 입력 SHA·변환 사유를 기록한다. 열 삭제/이름 변경/창·분모 변경 시 새 버전으로 내고 과거 자료를 덮어쓰지 않는다. 명세 밖 열/중복키는 조용히 수용하지 않는다.
7. 비교: 정책·계측뿐 아니라 집단/좌표계/창/지형/단위를 대조한다. 불일치는 비교 불가 또는 부분 가능으로 명시한다. 두 평균을 빼는 산술 가능성이 인과 비교 가능성을 뜻하지 않는다.

## 4. 강좌와 수식을 정책 판단에 쓰는 절차
강좌 14(보상 함수 설계와 조정)의 항목 역할/보상 해킹 사례, 강좌 15(학습 관찰과 진단)의 로그와 행동 관찰 원칙을 로컬 HTML에서 직접 확인했다. 강좌의 쉬운 설명을 정확한 물리량 정의로 대체하지 않는다. 예를 들어 '몸통을 기울이지 마라'라는 설명만으로 각도와 각속도를 같다고 볼 수 없다.

정확한 원식: 보관 Isaac Lab v2.3.1 `reports/evidence/go2_reward_term_roles_20260917/isaaclab_envs_mdp_rewards.py`의 `lin_vel_z_l2`, `ang_vel_xy_l2`, `flat_orientation_l2`; `isaaclab_tasks_locomotion_velocity_mdp_rewards.py::feet_air_time`. 버전/출처 SHA는 같은 폴더 `SOURCES.csv`를 사용한다.

| 판단 대상 | 원식으로 확인할 것 | 데이터에서 확인할 것 | 허용되지 않는 결론 |
|---|---|---|---|
| 계단 수직 움직임 | 몸통 좌표 vz²: 위/아래 부호를 구별하지 않음 | 월드 높이 차분은 대리값, 전진거리·자세 생존·실제 지형을 별도 측정 | 벌점 감소만으로 계단 완주 개선 확정 |
| 흔들림 속도 | omega_body_x²+omega_body_y² | scalar tilt 변화율은 각속도 전체가 아님; 원 채널 없으면 SURROGATE | 대리 지표 감소를 원 보상 감소로 단정 |
| 기울어진 자세 | gx²+gy² | 1-gz²는 unit norm 조건부, 뒤집힌 자세에서도 0 가능 | 자세 벌점=생존 게이트 또는 낙상 인과 |
| 발 들기 | 접촉 순간 (air_time-threshold), 명령 크기 조건 | 체공시간과 발 높이/계단 여유 높이는 별도 | 체공 증가=발 높이 증가=계단 개선 |

판단 제출 형식: **강좌 원리 → 정확한 원식/버전 → 실제 사용 채널과 차이 → 현재 관측 → 경쟁 가설 → 단일변수 실험의 반증 기준**.
reward 산술은 목적함수의 유인을 설명한다. 계단/흔들림이 실제 보정됐는지는 동일 평가 조건의 전진·추종·자세 생존·영상으로 확인한다. 지금 자료만으로 이미 보정됐다고 하지 않는다.
공식 채점식과 학습 보상식은 별개다. 강좌는 공식 점수 근거가 아니다.

## 5. 적용 현황과 남은 공백
- 5개 표 129행을 원 숫자 문자열까지 보존해 표준 뷰로 변환한다. 기존 생성기의 산술을 몰래 바꾸지 않는다.
- 명세/열/고유키/유한수/누락 및 surrogate 분류는 테스트한다. 원 raw telemetry 전체 재계산, 기존 정책 지문 전수 연결, 미저장 분모 복원은 수행하지 않았다.
- 기존 보고서/실험 사양이 legacy 숫자를 인용할 때도 이 명세를 함께 대조한다. 기존 산문 전체가 자동 정정됐다고 주장하지 않는다.
- 향후 신규 생성기는 명세 계약을 생성 시점부터 만족해야 한다. 현재 변환기는 이미 잃어버린 의미를 추정하여 채우지 않는 점진 이관이다.

## 2026-09-20 명세 누락 재발 시험 및 수정 결과
- 기존 49 tests 성공 후 필수 의미 필드 누락/빈 문자열/공백, 미등록 증거 종류, 차원 중복/지표 충돌을 주입했다. 추가 2 tests에서 수정 전 35 failures + 1 error를 확인했다(오류는 canonical_name 누락의 KeyError; 나머지는 거부되지 않은 입력).
- go2_standardize_evidence.validate_spec를 추가하여 표준 뷰 생성 전에 명세를 검증한다. 정상 5개 표 129행의 원문 값과 입력 SHA 보존, 현행 게시 결과 재현을 포함하여 관련 51 tests 성공.
- 이것은 구조적 계약 검사다. 그럴듯하지만 틀린 수식/설명, 누락된 원 표본 수/정책 identity, 모든 기존 생산자의 표준 출력 전환, 원자료 재계산과 독립 역할 재감사는 미완료다. 튜닝 효과를 입증하지 않는다.
