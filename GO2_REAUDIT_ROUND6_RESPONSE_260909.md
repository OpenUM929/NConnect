# Go2 6차 독립 재감사 회신 — 수집과 점수 채택의 경계
작성일: 2026-09-09 · 대상: `GO2_REAUDIT_ROUND6_PROMOTION_260909.md`
범위: 로컬 코드·합성 반례·수치 재계산 계약. 서버 실행·학습·공식 심사는 수행하지 않았다.
아래 `Q/`는 `workspace/training/quadruped/`의 경로 약칭이다. 요청서의 설명은 감사 대상이지 사실의 증명이 아니다.

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 프록시의 신뢰성, 설계 의도·리포트의 증거 정확성.
- [현재 단계] 단계 0/6 — 증거·artifact 정합성.
- [확보] 5차 반례 차단 재현, 6차 고정 해시 18개 일치, 독립 추가 반례 스크립트.
- [미확보] 추가로 발견한 시간·높이 파생·환경 identity 검증 공백의 해소. 실제 G-A027 전량 평가 결과는 이 감사에서 검증하지 않았다.
- [이번 테스트] 정상 자료를 수용하면서 잘못된 자료를 점수로 채택하지 않는지 확인한다. reward 만족도·G1~G7 행동은 직접 측정하지 않는다.
- [흐름] 5차 수리 → **6차 소비 측 검증** → 해소 시 회수물 점수 채택 심사 → 미해소 시 채택 보류·원본 보존 → 제출 별도 심사.
- [지금 할 일] 이 회신과 독립 재현 스크립트를 Opus에 전달한다.
- [보장하지 않음] 코드 계약 검증은 실제 측정 유효성, 후보 승급, 공식 점수·제출 자격을 보장하지 않는다.

## 1. 요약 및 최종 판단
1. **[증거·높음] 기존 수리는 실질적이다.** 중복 격자, upright 문자열, 요약 수치 위조, metadata 불일치, RC 부분 일치, G6 비유한 수치, NaN floor 반례가 거절되는 것을 재실행했다. 정상 합성 자료도 수용된다. 근거: `GO2_REAUDIT_ROUND6_PROBE_260909.py:80-181`, `tools/test_go2_scoring_repair_contract.py`.
2. **[증거·높음] 시간축 검사가 빠져 낙상 판정까지 바꿀 수 있다.** 동일한 7개 비기립 행의 시각만 0으로 바꾸고 요약을 맞추면 survival 0.5가 1.0으로 바뀌는데, 검증기는 양쪽 모두 faults=[]를 낸다. 근거: `GO2_REAUDIT_ROUND6_CODEX_PROBE_260909.py`의 FALL_CONTROL/FALL_HIDDEN_BY_FALSE_TIME 및 §3.1.
3. **[증거·높음] 자세 재계산은 한 단계 덜 내려갔다.** upright와 height_rel은 대조하지만 height_rel이 root_z−terrain_z에서 나왔는지는 대조하지 않는다. 지면 높이 100 또는 banana도 수용됐다. 근거: `tools/verify_go2_a027_harvest.py:390-403`, `Q/go2_eval_telemetry.py:285-316`.
4. **[증거·높음] 승인된 환경 hash 대조는 구현되지 않았다.** env_sha256=banana가 수용된다. 실행계획의 실제 대조 목록은 evaluator/registry/model 세 항목이다. 근거: `tools/verify_go2_a027_harvest.py:774-792`.
5. **[판단] 고정 ZIP의 조건부 수집 동의는 유지하되, 이 검증기만을 근거로 한 점수 채택·자동 승급 보류는 해제하지 않는다.** 위 세 공백은 로컬 소비 경로에 있으며, 이번 반례가 서버 계측기에도 존재한다고 입증한 것은 아니다. 기존 실행 조건은 `SERVER_SESSION_RUNBOOK.md:186-209`에 남아 있다.

이는 “6차 수리가 무효”라는 뜻이 아니다. **해소된 결함과 남은 결함을 분리**한 판정이다. 실제 정책이 잘못 승급됐다는 주장도 하지 않는다.

## 2. 재실행 범위와 증거
### 2.1 확인한 것
- 요청서 SHA256: `907a9b5cecc2e3b3b55d37baf6768f066bbb494df3116194dff7d15c232a6eb0`. 요청서 sidecar와 일치.
- 요청서 고정 파일 18개: 실제 디스크 SHA256과 전부 일치. 런타임 재개 후 다시 대조했다.
- `python -B GO2_REAUDIT_ROUND6_PROBE_260909.py`: 정상 대조군 수용, 기존 반례 거절, pin 18개 일치 출력 확인.
- `python -B tools/test_go2_scoring_repair_contract.py`: 최신 재실행 종료 코드 0.
- `python -B tools/test_go2_harvest_verifier_contract.py`: 재개 후 전 구간 재실행 종료 코드 0. 기존 계약 성공과 §3의 새 반례 수용이 동시에 성립함을 확인했다.
- `python -B tools/test_go2_a017_full_suite_contract.py`: 종료 코드 0. 패키지 payload·manifest·CRC·LF·bash -n 및 고정 아카이브 일치 확인. ZIP을 다시 쓰는 빌더 명령은 실행하지 않았다.
- 독립 추가 probe: `python -B GO2_REAUDIT_ROUND6_CODEX_PROBE_260909.py`, 종료 코드 0. **진단 출력 스크립트이지 결함 없음에 대한 회귀검사 성공 표식이 아니다.**

추가 probe는 계약 검사에서 fixture 정의만 AST로 읽고 임시 디렉터리에 합성 자료를 만든다. 실제 회수물·정책·ZIP을 변조하지 않는다. 이 감사는 “Go2 테스트 10종 전부 성공”을 독립 재확인했다고 주장하지 않는다.

### 2.2 기존 수리를 인정하는 범위
| 수리 | 직접 근거 | 판정 범위 |
|---|---|---|
| 격자 중복·누락 검사 | `tools/verify_go2_a027_harvest.py:443-459` | 기존 중복 행 반례 차단. 시간 정합성까지 보장하지 않음 |
| upright 값 영역·파생 오차 대조 | 같은 파일 `:383-416` | banana 및 cmd/actual 대비 error 위조 차단 |
| summary 재계산 | 같은 파일 `:484-552,675-684` | RMSE·생존·회복·진행량·커버리지 재계산 경로 존재 |
| G5/G6 소비 필드 | 같은 파일 `:119-180`; `Q/go2_fixed_eval_report.py:28-60` | 계단 진행량, 밀침 후 RMSE·기립 회복 필수화 |
| floor 타입·유한성·범위 | `Q/go2_tuning_eval_report.py:223-255,288-309` | NaN/Infinity/bool/문자열/범위 밖 값을 측정 무효로 분리 |
| 최저 인자 추적 | `Q/go2_tuning_eval_report.py:330-344`; `Q/go2_fixed_eval_report.py`의 survival_floor_case/tracking_floor_case | 시나리오 미달 수치 및 floor를 만든 case를 보고하는 방향 수용 |

## 3. 독립 추가 반례 — 아직 닫히지 않은 경계
### 3.1 R6-C1: time_s는 숫자 파싱만 하고 시간으로 검증하지 않는다
**원문:** 계측기는 `sim_time = (self.step + 1) * self.step_dt`를 만들고 소수 6자리로 CSV에 쓴다(`Q/go2_eval_telemetry.py:258,267`).
받는 쪽은 time_s를 float로 읽지만 비유한 검사는 아홉 kinematics 열에만 적용한다(`tools/verify_go2_a027_harvest.py:363-381`). time_s를 `step * step_dt`에 대조하지 않고 낙상 grace 및 회복 창에 사용한다(`:235-293,422-436`).

직접 출력:
```text
ONE_TIME_NAN INTERNAL_GATE_PASS [] []
ALL_TIME_999 INTERNAL_GATE_PASS [] []
FALL_CONTROL survival 0.5 faults []
FALL_HIDDEN_BY_FALSE_TIME survival 1.0 faults []
```

마지막 두 사례는 2 env×50 step, dt=0.1의 동일 fixture에서 env 0의 step 6~12를 비기립으로 만든다. 대조군은 survival=0.5다. 그 7행의 time_s만 0.0으로 바꾸면 grace_s=0.5 이전으로 해석되어 낙상이 사라진다. 위조된 survival=1.0을 summary에 적으면 재계산과 일치하므로 거절되지 않는다. **상태 행·높이 행·격자·step_dt가 같아도 잘못된 시각이 생존 판정을 바꾼다는 수치 증명**이다. 공식 점수 차이가 아니라 합성 내부 생존값의 변화다.

**요구:** time_s 유한성, 승인된 양의 dt, step별 소수 6자리 출력 계약, env별 시간 순서를 검증한 뒤 재생한다. 손상된 시각을 조용히 새 값으로 덮어써 수용하지 않는다. 위조 행 순서도 거절하거나, 검증된 인덱스로 명시적으로 정렬한 뒤 replay하는 정책을 고정한다.

**영향:** 점수 채택 경계의 높은 우선순위 결함. 현재 고정 collector가 잘못된 시각을 생성했다는 증거는 아니다.

### 3.2 R6-C2: height_rel의 원천 대조가 빠졌다
계측기 원문은 root_z에서 terrain_z를 빼고, 비유한 결과를 None으로 기록한다(`Q/go2_eval_telemetry.py:285-294`).
검증기는 height_rel과 proj_grav_z만 읽어 upright를 판정한다(`tools/verify_go2_a027_harvest.py:390-403`). terrain_z는 필수 헤더에 있지만 이 산식을 확인하지 않는다(`:89-95`).

직접 출력:
```text
HEIGHT_TERRAIN_CONTRADICTION INTERNAL_GATE_PASS [] []
TERRAIN_BANANA INTERNAL_GATE_PASS [] []
```

root_z=0.32, height_rel=0.32를 둔 채 terrain_z를 0에서 100으로 바꾸거나 banana로 바꿔도 통과했다. 전자는 산식상 높이가 −99.68이어야 하므로 명백한 모순이다.

**요구:** 계측기와 같은 결측·비유한 처리로 root_z−terrain_z를 재계산하고 height_rel과 대조한 다음 upright를 검사한다. 이는 **모든 ray hit의 비유한 값을 금지하라**는 요구가 아니다. 정상적인 지면 결측→height_rel 공백→upright 공백 경로는 보존해야 한다.

**영향:** 점수 채택 경계 결함. 정상 collector가 이 모순을 실제로 썼다는 주장은 미확인.

### 3.3 R6-C3: env identity는 승인값 대조가 아니라 존재 검사다
`read_run_plan`은 model/계측기/registry hash와 env 수·step 수를 읽는다(`tools/verify_go2_a027_harvest.py:688-747`).
`verify_arm`은 env_sha256의 존재만 요구하며 실제 expected 대조에는 넣지 않는다(`:774-792`). 두 arm의 env hash가 같아야 한다는 뜻도 아니다. 정책마다 **자기 승인 env**에 맞아야 한다.

직접 출력:
```text
ENV_HASH_BANANA INTERNAL_GATE_PASS [] []
```

따라서 “모델·env·계측기·registry 해시를 승인 계획과 대조한다”는 런북 설명(`SERVER_SESSION_RUNBOOK.md:229-231`)은 env에 관해서는 과장이다. 원래 러너는 실제 env hash를 기록한다(`Q/server_run_go2_a017_full_suite.sh:313-335`). 기록하는 것과 받는 쪽이 승인된 원본 파일과 대조하는 것은 다르다.

**요구:** 동결 패키지/manifest의 각 정책 env.yaml에서 기대 SHA를 도출하고 arm별 대조한다. SHA 문자열 모양 검사만으로 끝내지 않는다. 기대값을 회수물 자신의 identity에서 가져오면 순환 검증이다. 원본을 확보하지 못하면 INCONCLUSIVE로 남긴다.

**영향:** 평가 조건 식별 및 점수 채택 경계 결함. 수집 ZIP 교체 요구는 아니다.

## 4. 요청서 §10 Q1~Q5 회신
### Q1. 재계산 정의·허용오차
**부분동의.** 낙상 타이머의 결측 freeze·optimistic/pessimistic 구조는 원문과 대응한다(`Q/go2_eval_telemetry.py:317-334` ↔ 검증기 `:235-260`). 종료된 env의 progress는 종료 행까지 더한 뒤 멈추며 양쪽이 대응한다(collector `:341-351` ↔ 검증기 `:515-533`). 회복 peak/quiet/upright/break도 대응한다(collector `:358-405` ↔ 검증기 `:263-293`).

다만 **산식이 같아도 입력 시간축을 검증하지 않으면 같은 결과가 신뢰 가능한 결과라는 뜻은 아니다.** R6-C1이 실제 반례다.

`_agree`는 순수 상대 오차가 아니라 `1e-6 * max(1, abs(claimed))`의 절대·상대 혼합 허용치다(`tools/verify_go2_a027_harvest.py:198-204`). RMSE 등의 현재 허용치를 더 넓혀야 한다는 근거는 이 감사에서 확보하지 않았다. 반면 time_s는 collector가 6자리로 반올림한다는 별도 직렬화 계약을 반영해야 한다. 요약 오차 허용치 확대만으로 시간 창/낙상 분기 불일치를 해결해서는 안 된다.

### Q2. 계획 미확인의 INCONCLUSIVE
**동의.** 자료가 내부적으로 모순된 FAIL과 승인 계획을 모르는 INCONCLUSIVE는 다르다. 현재 main은 INCONCLUSIVE에도 종료 코드 1을 내므로 자동 채택을 막는 방향이 맞다(`tools/verify_go2_a027_harvest.py:934-942,977-982`). 진단 자체를 막을 필요는 없다. 다만 실제 점수 채택에서는 승인 계획 대조를 필수로 유지한다.

### Q3. case 지문을 재계산하지 않은 결정
**조건부 동의.** 이번 수집 직전에 복잡한 shell 환경을 Python으로 중복 구현하라고 요구하지 않는다. 하지만 현재 검사는 “64자리 hex이며 case 간 중복이 없다”까지만 보장한다(`tools/verify_go2_a027_harvest.py:637-645,825-834`). **유일한 지문은 올바른 지문의 증명이 아니다.** 지문이 유일하다는 이유만으로 시나리오의 명령·지형·DR이 승인 조건과 같았다고 확정하면 안 된다.

이번 회수에서는 동결 소스·원시 명령·metadata·실행 로그·모델/env identity를 함께 대조한다(`SERVER_SESSION_RUNBOOK.md:201-205`). 다음 패키지 개선은 지문 입력을 구조화된 manifest로 함께 보존하여 재현을 쉽게 만드는 것이다. 현재 ZIP을 이 목적만으로 재빌드할 필요는 없다.

### Q4. case별 소비 필드
**핵심 목록 배치에 동의.** combined_yaw의 yaw RMSE를 공통 목록에 두는 것은 현재 collector가 모든 행에서 계산하므로 타당하다(`Q/go2_eval_telemetry.py:263-264`; `Q/go2_fixed_eval_report.py:30-34`). 계단의 duration/progress와 밀침의 post-push RMSE/upright recovery도 현재 목록에 들어갔다(`tools/verify_go2_a027_harvest.py:119-180`).

이번에 남은 핵심은 새 summary 필드의 누락보다 **그 필드가 의존하는 시간과 상대 높이, 실행 identity**다. 소비 목록만 완성됐다고 원자료 검증 완료로 승격하지 않는다.

### Q5. G-A027 수집 및 점수 채택
- **조건부 수집 동의 유지:** 고정 ZIP `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea`, 잔여 GPU 실측, 첫 10분 계측 확인, 2시간 재판정, 전량 회수·원본 보존 조건(`SERVER_SESSION_RUNBOOK.md:186-206`).
- **점수 채택·자동 승급 보류 유지:** R6-C1~C3를 로컬에서 닫고 회수물 전체에 적용하기 전에는 현 검증기 출력 하나로 해제하지 않는다.
- **수집을 지금 막는 새 collector 결함은 이번 감사에서 입증하지 않았다.** 로컬 검사 수리를 서버 수집과 분리할 수 있다.
- **조건 충족 실측 여부는 별도:** 잔여 GPU·서버 실행 상태는 이번 감사에서 미측정이다. 이 문서는 서버를 실제로 시작했다거나 실행 조건을 모두 충족했다는 확인서가 아니다.

## 5. 개선안 — 한 번에 경계를 닫는 작은 수리
아래는 감사자의 제안이며 구현 완료·GPU 실행 승인이 아니다. 시간은 로컬 작업 timebox다.

| 우선순위·등급 | 작업·시간 박스 | 사전 판정·실패 시 대안 |
|---|---|---|
| P1 · 개선(점수 채택 전 필수) | 시간축 검증 30~45분 | NaN/Inf/상수시각/역순/step-dt 불일치 및 낙상 숨김 반례 거절. 정상 반올림 시각 수용. 실패 시 점수 채택 보류, 원본 보존 |
| P1 · 개선(점수 채택 전 필수) | 상대 높이 파생 대조 20~30분 | 산식 모순·문자열 거절. 정상 결측은 기존 coverage/ambiguity 계약대로 처리. 비유한 ray 일괄 금지 금물 |
| P1 · 개선(점수 채택 전 필수) | arm별 env 승인 hash 30~45분 | 동결 패키지의 실제 env로 기대값 고정. 바른 64자리이지만 다른 hash도 거절. 기대 원본 없으면 INCONCLUSIVE |
| P1 · 개선 | 정상 collector 출력으로 소비 검사 대조 30~45분 | 수제 summary만 쓰지 말고 collector가 만든 CSV/summary를 검사. dt=0.02·종료·결측·회복 경계 포함 |
| P2 · 개선 | 테스트 계층 분리 20~30분 | 작은 단일-case 단위 반례 + 138-case 완전성 통합 + CLI 계획 대조로 분리. 반복 전체 디렉터리 복사 비용을 줄이되 통합 검사 삭제 금지 |
| P2 · 개선 | 다음 패키지에서 지문 입력 manifest | 현재 동결 ZIP은 유지. 구조화 입력과 hash의 대응을 다음 버전에서 고정 |

근거: P1 첫 세 행은 §3 직접 반례, 정상 대조군 개선은 `tools/test_go2_harvest_verifier_contract.py:94-155`의 수제 fixture 구조, 테스트 비용 개선은 같은 파일 `:195-203`의 반복 전체 copytree 구조, 지문 manifest 제안은 검증기 `:637-645`의 확인 한계다.

**종료 조건:** 기존 반례 차단을 유지하고 위 세 경계의 반례를 거절하며 정상 collector 출력이 수용되면 코드 경계 감사를 닫는다. 그 뒤 실제 회수물 검사·영상·내부 성능 심사는 별도로 한다. 로컬 수리 실패를 곧바로 GPU 재학습이나 전량 재수집 명령으로 바꾸지 않는다.

## 6. 한계·미확인
- G-A027 실제 138-case 수집 완료, 영상 7건의 행동, 잔여 GPU, 공식 점수·자격: 이 감사에서 미측정.
- 위 합성 손상이 실제 서버 결과에 발생했는지, 과거 후보 승급을 바꿨는지: 미확인.
- SHA 일치는 파일 동일성 증거다. 실행 내용의 진실성이나 로봇 성능을 보증하지 않는다.
- env·case 식별을 모든 외부 조작에 견디는 인증 체계로 만들었다는 보장은 없다. 이번 목적은 승인 입력과 회수 증거의 로컬 대조다.
- 0바이트 사고 전 파일과 재빌드본의 바이트 동일성은 이 감사에서 새로 확인하지 않았다. “손실 없음”으로 승격하지 않는다.
- 제품 소스·원장·ZIP은 수정하지 않았다. 새 산출물은 본 회신, sidecar, 독립 반례 스크립트다. 커밋·서버 실행 없음.

**Opus에 요청하는 다음 답변:** “검사 전부 성공”보다 R6-C1~C3 각각의 수정 위치, 동일 반례 거절 출력, 정상 collector 대조 출력, 남은 한계만 제시해 달라. 이미 확인한 수집/채택 경계는 근거 없이 합치지 말아 달라.
