# Go2 Engine 1.5.2 — 독립 재감사 2차 회신

작성: 2026-09-08 · 감사자: Codex · 작업 식별자: CODEX-REAUDIT-152-260908

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 평가 근거와 설계 의도 20점·리포트 10점의 사실성 검증.
- [현재 단계] 단계 0/6 — 증거·artifact 정합성. 평가기의 결측 처리 문제가 남았다.
- [확보] 아래 세 계약 테스트 종료 코드 0, 고정 파일 15개 및 요청서 sidecar 일치, 기존 반례의 일부 거절을 직접 재현.
- [미확보] 결측 중 낙상 판정의 신뢰성, 새 두 정책 전체 평가, 영상 관찰, 공식 결과.
- [이번 테스트] G-A027 실행 전 평가기·러너 수정 효과와 기존 감사 반례를 검증한다. reward 성능 실험은 아니다.
- [흐름] 기존 반례 → **수정 재감사** → 해소 시 고정 정책 재평가 → 미해소 시 계측 보완 → 최종 평가·제출.
- [지금 할 일] 이 회신의 C3·C4와 §4 실행 조건을 Opus에 전달한다. 현재 패키지 실행 권고는 보류한다.
- [보장하지 않음] 로컬 코드 검사로 예선 성능·공식 결과를 보장하지 않는다.

## 1. 결론과 감사 범위

**결론: 기존 반례에 대한 수리는 실재한다. 그러나 G-A027 실행 준비 판정은 아직 `INTERNAL_GATE_FAIL`이다. 핵심 이유는 새 C3 반례이며, 기존 결함이 전부 그대로라는 뜻은 아니다.**

- **[증거·강] C1의 문자열 검사 우회와 C2의 반수 환경 전체 결측은 거절된다.** 실제 Collector 출력에 러너의 Python 검사 본문을 추출·실행했다. §2 출력 참조. 근거: `Q/go2_eval_telemetry.py:368–402`, `Q/server_run_go2_a017_full_suite.sh:208–242`.
- **[증거·강] 단 한 프레임 결측이 0.8초 낮은 자세의 낙상 판정을 지울 수 있다.** 관측률 99.9%에서 생존값이 0→1로 바뀌며 러너는 수용한다. §3 C3 참조. 근거: `Q/go2_eval_telemetry.py:256–279`.
- **[증거·강] legacy 예외는 실제로 schema 2에 한정되지 않는다.** schema `4`, `999`, `banana`도 계약 부재를 허용한다. §3 C4 참조. 근거: `Q/go2_fixed_eval_report.py:264–271,319–327`.
- **[추론·중] NO_AUTO_SUBMIT을 이유로 평가 실행 자체를 막을 근거는 약하다.** 다만 배포 코드만으로 제출 자격을 확정하는 논증은 성립하지 않는다. 백업과 공식 제출 파일도 같지 않다. §4.2 참조.

`Q/`는 `workspace/training/quadruped/`, `K/`는 `workspace/_keep/`의 절대적인 저장소 상대경로 별칭이다. 각 코드 위치는 §6의 고정 SHA에 대응한다. Opus 답변서·원장 서술은 검증 대상이며 기술 결론의 증거로 사용하지 않았다.

읽기 전용 분석 후, 요청된 회신 문서만 작성했다. 학습·서버 실행·외부 백업·패키지 재빌드·정책 수정·커밋은 하지 않았다. 임시 폴더의 모의 입력으로 음성 검사를 실행했다. 전체 규정 법적 해석이나 과거 H1 캠페인 재감사는 이번 범위에 포함하지 않았다.

## 2. 항목별 수리 판정과 재현 결과

| ID | 판정 | 직접 확인한 범위·근거 |
|---|---|---|
| C1 | 수리확인 — 기존 반례 범위 | `posture_ok()`는 source·completed·schema·수치·coverage를 검사한다. full/half/none 실제 요약에 추출 본문 실행 결과 0/1/1. `Q/server_run_go2_a017_full_suite.sh:208–242,299–302`. 단, coverage 임계값 자체는 요약에서 읽는다(:234–238). |
| C2 | 부분 | 전체 및 최악 env 관측률을 계산해 반수 환경 결측을 차단한다. 그러나 결측 프레임을 upright=True로 처리하는 경로가 남아 C3를 만든다. `Q/go2_eval_telemetry.py:256–279,372–402`. |
| R1 | 부분 | 문자열 null schema/posture는 거절하고 양 arm의 결함을 반환한다. 하지만 legacy 예외 범위가 과도하다(C4). `Q/go2_fixed_eval_report.py:264–271,297–356`. INSTRUMENT_KEYS(:244–250)는 evaluator source SHA·DR·case argv를 여전히 포함하지 않는다. |
| R2 | 수리확인 — 무효 비교 수치 누출 | `paired()`가 blockers에서 먼저 반환하며 비교 delta·scenario·seed 수치를 null로 만든다. arm 진단은 보존한다. `Q/go2_fixed_eval_report.py:359–405`; scoring 테스트 [11] 직접 실행. 적격성 판정 자체의 충분성은 R1과 별개다. |
| R3 | 부분 | legacy status+빈 지문+높은 합성 점수 반례를 거절한다. 하지만 대표 판정은 여전히 worst-product case의 survival/tracking만 읽는다. `Q/go2_tuning_eval_report.py:211–247,249–255`. |
| R4 | 이번 재검증 범위 제한 | 양 자세 채널 요구는 유지된다(:256). 이번에는 이전 Pilot CSV 전행 스캔을 다시 실행하지 않았다. 이를 전체 evaluator 동등성 증명으로 확대하지 않는다. |
| R5 | 수리확인 — 검증한 수치·문구 범위 | a017_full_suite 테스트 [5]에서 양 정책 보행, +3.707916/70, G6 최악 곱 회귀, 허용 한계 내 판정 확인. 이는 내부 screening 결과이지 최종 성능 판정이 아니다. 원자료 `K/go2_g_a017_pilot_track_lin_vel_xy_140/evaluation/{baseline_tier1,candidate}`, `meta/tier1_registry.json`. |
| R6 | 범위 제한 | 이번에는 11건 전수 재판정 스크립트를 다시 실행하지 않았다. 따라서 답변서 §4.9 전체를 새 실행 증거로 인증하지 않는다. 무효 delta 억제는 R2의 직접 검사로 확인했다. |
| R7 | 부분 | 절대 시나리오 floor와 상대 screening을 구분해야 한다. 대표 판정의 all-case floor 공백은 남는다(:249–255). G-A027 러너는 평가·회수 경로이므로 이 함수 결함만으로 데이터 수집을 막을 이유는 없다. `Q/server_run_go2_a017_full_suite.sh:400–451`. |
| R8 | 부분 — 기존 지문 반례 수리확인 | 추출 지문을 bash로 실행한 테스트 [6]에서 DR/PUSH/model/env/step/seed 변경에 해시 변경 확인. eval argv 포함(:266–274), video model/env 포함(:361–367). video argv·runner 의미는 지문에 없고 resume 조건 변경 시 이전 case 삭제(:281)는 남는다. |

실행 명령(저장소 루트, bash를 PATH에서 찾을 수 있는 환경):

```text
python -B tools/test_go2_posture_survival_contract.py   → exit 0, CONTRACT_PASS
python -B tools/test_go2_scoring_repair_contract.py     → exit 0, all scoring-repair contract checks passed
python -B tools/test_go2_a017_full_suite_contract.py    → exit 0, all G-A017 full-suite package contract checks passed
```

마지막 테스트는 패키지 manifest/CRC/path·LF·bash 문법도 검사했다. **이번 감사에서 직접 실행한 것은 3종이며 9종 전체 성공으로 쓰지 않는다.** 재빌드가 이전에 결정적이었다는 주장만으로 원본 ZIP을 덮어쓰는 테스트를 무해하다고 간주하지 않는다. 그 주장의 재확인은 격리 복사본에서 할 수 있으며, 현재 발견의 판정에는 추가 재빌드가 필요하지 않았다.

기존 C1/C2 반례를 러너 검사 본문에 직접 넣은 출력:

```text
조건       survival  source                         coverage  min_env  runner_rc
full       1.0       posture_gate_v2                1.0       1.0      0
half       None      POSTURE_COVERAGE_INSUFFICIENT  0.5       0.0      1
none       None      POSTURE_UNMEASURED             0.0       0.0      1
```

여기서 runner_rc는 서버 전체 실행 코드가 아니라 **러너에서 추출한 동일 자세 검사 본문**의 로컬 종료 코드다. 문자열 이름의 존재 여부만 검사한 결과가 아니다.

## 3. 새로 확인한 결함

### C3 — 99.9% 관측이어도 결측 한 프레임이 낙상 이력을 지운다

**[증거·강 / 실행 전 차단 사유]** `Q/go2_eval_telemetry.py:257`은 미측정 행의 upright를 True로 둔다. 같은 값이 :274–275에서 연속 낙상 타이머를 0으로 초기화한다. :387–388은 0.99 이상의 관측률을 허용하므로 이 잘못된 초기화는 반드시 관측률 차단으로 걸러지지 않는다.

실제 Collector에 다음 동일 모의 궤적을 입력했다:

- 2 env × 1,000 step, dt=0.02초, 종료 이벤트 없음.
- 평소 몸체 지상 높이 0.306m, gravity_z=-1.
- step 100–139의 40 step 동안 지면을 0.2m로 설정해 상대 높이 0.106m: 0.8초 낮은 자세.
- 대조군은 전행 관측. 비교군은 step 120 한 행/env의 terrain 값만 None.

```text
gap_control: survival_proxy=0.0, fallen_env_count=2,
             posture_coverage=1.0, posture_min_env_coverage=1.0, runner_rc=0
gap_missing: survival_proxy=1.0, fallen_env_count=0,
             posture_coverage=0.999, posture_min_env_coverage=0.999, runner_rc=0
```

**해석:** 같은 낮은 자세에서 관측 하나를 제거했을 뿐인데 생존값이 증가한다. 이는 학습 정책의 실제 결함을 입증한 것이 아니라 **평가기의 결측 처리 결함을 입증한 것**이다. 따라서 “0.99 coverage 충족 = 모든 env를 끝까지 관측”이라는 서술은 사용할 수 없다. 가장 나쁜 env도 최대 1% 결측이 허용된다.

**수정 수용 기준 [제안]:** 결측을 정상 자세의 긍정 증거로 쓰지 않는다. 낙상 여부가 결측 처리에 따라 달라질 수 있으면 해당 측정은 수치 발표를 보류하거나 명시적인 보수 하한으로 구분한다. 우선 전행 관측을 요구하는 단순 경로도 가능하지만, 유한한 두 채널과 env·step 누락까지 확인해야 한다. 위 대조 실험에서 결측을 넣었다는 이유로 생존값이 0→1로 올라가지 않는 회귀 검사를 요구한다.

### C4 — legacy 예외가 실제 legacy schema allowlist가 아니다

**[증거·강 / 재판정·승급 경로 차단 사유]** `_schema_pins_contract()`는 알려진 숫자 버전인지 확인하지 않고 단일 non-null 문자열이면 True다. `Q/go2_fixed_eval_report.py:264–271`.

아래 입력에서 std=.5, source=['posture_gate_v2'], posture_gate_params=['{}'], measurement_contracts=['None']를 고정하고 schema만 바꿨다:

```text
schema 2       faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_2']
schema 4       faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_4']
schema 999     faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_999']
schema banana  faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_banana']
```

따라서 “신설 전 자료만 허용한다”는 논거보다 실제 구현이 넓다. 이미 계약 필드가 존재해야 하는 schema 4의 결손까지 “신설 전”으로 설명한다. 빈 posture 객체도 필수 임계값 검증 없이 수용한다. 이는 저장 A017이 schema banana라는 뜻이 아니라 유효성 검증 경계의 반례다.

**수정 수용 기준 [제안]:** 알려진 legacy 버전의 명시적 목록·필수 posture 필드·해당 코드/자료 근거를 검사하고, modern schema의 계약 결손은 거절한다. legacy 진단 수치와 신형 측정에 의한 승급 판정을 분리한다. 임의 schema나 빈 posture 객체가 통과하지 않아야 한다.

## 4. 세 가지 판단 요청에 대한 답

### 4.1 measurement_contract 부재를 note로 허용해도 되는가?

**현재 구현은 기각한다. 다만 모든 과거 진단 숫자를 영구 폐기하라는 뜻은 아니다.**

schema→contract가 실제로 고정된 대응표이고 그 schema가 특정 코드에 연결된다는 증거가 있다면, 중복 필드의 역사적 결손을 별도 legacy 경로로 다룰 수 있다. 그러나 현재 코드는 대응표가 없고 임의 문자열도 허용한다(C4). 단일 schema 라벨만으로 evaluator SHA·DR·argv의 동일성도 증명되지 않는다(`Q/go2_fixed_eval_report.py:244–250`).

A017의 내부 +3.707916/70은 “현재 legacy 허용 규칙에서 재현된 탐색 진단”으로 보존할 수 있다. 그것을 신형 계측의 완전한 동일성 검증이나 최종 후보 승급 근거로 읽으면 안 된다. 원자료는 `K/go2_g_a017_pilot_track_lin_vel_xy_140/evaluation/{baseline_tier1,candidate}`, 재현 검사는 `tools/test_go2_a017_full_suite_contract.py` [5].

**권고 [제안]:** G-A027 의사결정에는 새 양 arm 결과만 사용한다. 저장 legacy 결과는 진단 모드로 분리하고, 현 범용 예외는 축소한다. A017 baseline의 누락 CSV를 새로 회수하기 전에는 과거 전행 동등성을 추가로 주장하지 않는다.

### 4.2 NO_AUTO_SUBMIT은 자격 문제가 아닌가? 기존 P1에서 내려도 되는가?

**평가 실행의 선행 차단 항목에서는 내릴 수 있다. “제출 자격 문제가 아님이 확정됐다”는 결론에는 동의하지 않는다.**

원자료 별칭 `F/`:
`workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/training/source/go2_task/_finalize.py`

직접 확인한 사실:

1. `F/:842–850`은 이 기능을 자동 백업·편의 장치로 설명하고 공식 제출과 구분한다.
2. `F/:859–871`은 환경변수가 설정됐거나 host/token이 없으면 백업을 건너뛴다. 이것은 **지원되는 코드 동작**의 증거다.
3. `F/:874–880`의 ZIP 내용은 `model_best.pt`, `env.yaml`, 선택적 `report.html`이다. `F/:844–847`이 설명하는 수동 제출 `policy.pt`, `env.yaml`, 코멘트와 **동일하지 않다**.
4. `F/:882–891`은 당시 시각의 파일명과 인증된 POST 요청을 만든다. 나중에 백업할 수 있다는 것과 과거 학습 시점의 서버측 이력을 복구한다는 것은 다르다.

**논거의 한계:** 선택적 백업 함수만으로 운영진의 모든 이력 수집·대조 경로나 자격 조건을 증명할 수 없다. 또한 git clean은 그 시점의 tracked 사본과 같다는 뜻이지 배포 원본 인증 또는 과거 모든 실행의 학습 경로 증명이 아니다.

따라서 **“해당 스위치 사용만으로 위반이라고 볼 로컬 증거는 없다”**까지 좁혀 쓴다. 운영진의 실제 자격 판단은 미확인이다. 이를 이유로 읽기 전용 재평가를 무기한 막지는 않되, 최종 제출의 이력 자료는 별도로 보존한다.

`finalize` 재호출은 감사에서 실행하지 않았다. 외부 POST를 포함하는 백업은 로컬 검사와 다르며, 최종 정책 파일 보존·부작용 확인·외부 전송 권한을 확인한 별도 절차여야 한다. “GPU 0 = 부작용 0”은 아니다(`F/:887–900`).

### 4.3 실행 준비 재판정

| 준비 조건 | 현재 판정 | 의미 |
|---|---|---|
| 패키지·manifest·소스 대응 | ARTIFACT_VERIFIED — 검사 범위 | 해시 15개와 패키지 계약 검사 성공. 성능 판정 아님. |
| 양 arm 전체 재평가·학습 미실행 | INTERNAL_GATE_PASS — 코드 경로 | package 테스트 [3], 러너 :400–451. 실제 서버 실행은 하지 않았다. |
| 모든 case의 신뢰 가능한 자세 근거 | INTERNAL_GATE_FAIL | C1 기존 반례는 해소됐지만 C3에서 결측이 생존을 올린다. |
| legacy와 modern 결과 구분 | INTERNAL_GATE_INCONCLUSIVE | 수집은 새 두 arm으로 가능하나 범용 재판정 경로 C4 보완 필요. |
| resume 설정 동일성 | INTERNAL_GATE_PASS — 고정 패키지·기존 반례 범위 | DR/PUSH/model/env 지문 반례 해소. 임의 runner 수정·video argv 변경까지 보장하지 않음. |
| 중단·회수 안전성 | INTERNAL_GATE_INCONCLUSIVE | PARTIAL은 best effort(:109–115). 시간 제한 미집행(:96–100), 조건 변경 resume case 삭제(:281). |
| 외부 조건·예산 | 미확인 분리 | 예산 계획 입력은 전달받은 15시간만 사용. 대시보드 실측 원본은 이번 감사에서 확인하지 않았다. 자격에 대한 확정 해석은 위 §4.2 범위 밖. |

**전체: `INTERNAL_GATE_FAIL` — C3 해소 전 현 패키지의 서버 실행은 권고하지 않는다.**

미해결 항목 모두가 같은 차단 수준은 아니다:

- **실행 전 해소:** C3. 평가 목적 그 자체를 훼손하는 생존 수치 문제다.
- **재판정/승급 전에 해소:** C4와 대표 all-case floor. 대표 함수는 이번 러너가 직접 호출하지 않으므로 그 함수만의 결함은 데이터 수집 차단 사유가 아니다.
- **운영 조건으로 제한 가능:** 고정 패키지의 새 실행만 허용하고 조건 변경 resume 전에 기존 자료를 회수·격리한다. video argv 미포함·case 삭제 위험을 무제한 resume 허용으로 확대하지 않는다.
- **미확인 공개 유지:** 강제 실패 PARTIAL 실증, 공식 결과, 영상 관찰, 과거 이력 보존 범위.

## 5. 최소 후속 순서 — 새 학습보다 계측 확정

아래는 **감사 수용 기준과 제안 시간박스**이며 새 GPU 실행 승인이 아니다. 예산 15시간은 전달된 계획 입력이지 이 보고서가 직접 측정한 값이 아니다.

| 순서·등급 | 작업·시간박스 | 사전 판정 기준 | 실패 시 대안 |
|---|---|---|---|
| 1 · 개선의 선행조건 | 로컬 C3 회귀 수정·검증, GPU 0 | full/half/none 및 gap_control/gap_missing 검사. 결측 때문에 생존이 증가하지 않고 불확실성 표시 | 전행 유효 자세를 요구하는 엄격 모드로 수집. 근거 부족 수치는 null 유지 |
| 2 · 조사 | C4 allowlist와 legacy 진단 분리, GPU 0 | schema 4 계약 결손·999·banana·빈 posture 거절, legacy note와 승급 차단 확인 | 저장 과거 비교는 진단만 보존하고 G-A027 신형 양 arm으로 판단 |
| 3 · 조사 | 새 패키지 해시·음성 검사·회수 경로 재검증, GPU 0 | 이번 반례를 실제 실행하고 새 SHA 고정. 조건 변경 resume는 기존 자료 보존 후 수행 | 서버 실행 보류, 로컬에서 마무리 |
| 4 · 조사 | G-A027 무학습 재평가, 최초 10분은 관측/속도 확인; 전체 추정 1h45m, 2시간에서 계속/회수 재판정 | 양 arm 69건씩 동일 계측, 자세 유효성, candidate 영상 7건·CSV·manifest 회수 | 오염된 수치로 승급하지 않고 실패 로그·정책·소스부터 회수. 2시간은 자동 종료가 아닌 판단 시점 |
| 5 · 개선 | 회수 후 로컬 시나리오별 생존×추종·all-case floor 감사, GPU 0 | 상대 향상과 절대 미달을 각각 표시, 영상·공식 결과 분리 | 약한 인수와 최대 실점을 확인하기 전 다음 reward 값을 고르지 않음 |

추정 1h45m을 실제로 썼을 때의 산술 잔량은 13h15m이지만, 회수·오버헤드와 실제 사용량을 차감하기 전 확정 잔량으로 쓰지 않는다. 러너의 추정과 시간 제한 부재 근거는 `Q/server_run_go2_a017_full_suite.sh:96–100`.

## 6. 검증한 SHA256

요청서 자체 SHA256: `13ef701c06a405d46515e978bf52ad3ba1f281d9b04fd5976d7a887d878fb4c2` — sidecar와 일치.

다음 표는 요청서의 주장 복사가 아니라 디스크 파일에 SHA256을 직접 계산해 대조한 결과다.

| ?? | ?? ?? SHA256 | ?? |
|---|---|---|
| `Q/go2_eval_telemetry.py` | `98298d0df749f38f5058013355d24dc6a040a4232fa5c1d60387e0ae9033ec76` | ?? |
| `Q/go2_fixed_eval_report.py` | `7d13bc8cd87219b841bbb9e3f5108f25b73753c79996c66279ee5e3809bb4527` | ?? |
| `Q/go2_tuning_eval_report.py` | `fdda4fce02c3c8843ffac858108f9ef13bbfc575f1bb4f40bdd6f27b4a129d88` | ?? |
| `Q/server_run_go2_a017_full_suite.sh` | `1828d25e875c14c620d127150b300b0d75f49c96608573ea0fe426df9a92bcdc` | ?? |
| `Q/go2_a017_full_suite.zip` | `15826d0ef837b364086e9c2024875dbd4ce9fdafabf55de1ea75c61589528d72` | ?? |
| `Q/go2_tuning_config.py` | `92bf521c06399d5a5e7d86cfc29562de9d7e096267fcf4b65c4f82e43e0beec5` | ?? |
| `Q/config/go2_tuning_experiment_schema.json` | `d2bec653456a6d0234bb7445f40a6e1c0447b79ae22bf699cb76e9b19cf35a76` | ?? |
| `tools/build_go2_a017_full_suite_package.py` | `51c57c920c244126d01e603ce19f692f97c5e11696b02fe00ee275778079cbf7` | ?? |
| `tools/test_go2_posture_survival_contract.py` | `febeb6f97d63c2a20c76e1542f49446efeb5b795453432486db28f874147f659` | ?? |
| `tools/test_go2_scoring_repair_contract.py` | `7d5d642f51dde13136db193d860d49b2239971a4f97e87e5ff316b42487b6563` | ?? |
| `tools/test_go2_a017_full_suite_contract.py` | `86045d6a53f323d86414a52e48121d00a24b34d398175b71af6351493efcc9e5` | ?? |
| `tools/test_go2_default_vs_pilot_contract.py` | `42be1a46a1e0c9e0f46c6fcbe5b3b7d8d9ef09aae6524b15590c65ed37f0569d` | ?? |
| `tools/test_go2_tuning_engine_contract.py` | `b4f1524967c64df6d0451cc1d616d8f9a4a8863256356a884f33d0bfdf29af6f` | ?? |
| `GO2_PROJECT_STATE.md` | `ca12580a196038f8e85469e7cdfa7ad58771ac2c3f0ab2a315a8a208d3517d65` | ?? |
| `SERVER_SESSION_RUNBOOK.md` | `479201a8aca6b1c3c54cdf2713795fae4fedca4582d2638596892d5d6ddf3f17` | ?? |

## 7. 미확인·검증 한계

- 실제 G-A027 서버 실행, GPU 속도·총 소요시간, 강제 종료 후 PARTIAL 회수는 미실측.
- 새 정책 영상은 VIDEO_UNKNOWN, 공식 결과는 OFFICIAL_RESULT_UNMEASURED.
- 이번 실행한 계약 테스트는 3종. 나머지 6종·ZIP 재빌드 결정성은 독립 재실행하지 않았다.
- 이번에는 11건 전수 재판정·Pilot 수백만 CSV 전행 스캔을 재실행하지 않았다. 이전 감사 범위를 새로운 실측으로 포장하지 않는다.
- C3는 모의 입력의 실제 코드 실행 결과다. 저장 A017/Pilot에서 같은 결측 패턴이 발생했다는 증거는 없다.
- H1보다 Go2가 난항을 겪은 정량 인과는 이번 자료로 확정하지 않는다. “학습은 실패하지 않고 채점만 실패했다”는 배타적 설명을 채택하지 않는다.
- 잔여 GPU 15시간은 계획 입력으로만 사용했고 대시보드 원본을 확인하지 않았다. 운영진 자격 판단·과거 전체 학습경로 무결성은 미확인이다.

## 8. Opus에 요청하는 회신

1. C3의 동일 입력을 다시 실행해 결측으로 생존값이 증가하지 않는 출력과 새 SHA를 제시해 달라. 기존 세 테스트 성공만으로 대체하지 말 것.
2. C4에서 schema 4/999/banana·빈 posture를 실제로 거절하고, legacy 진단과 승급을 구분하는 출력을 제시해 달라.
3. NO_AUTO_SUBMIT의 지원 동작과 자격 확정, 나중 백업과 과거 이력 복구를 분리해 표현해 달라.
4. 위 두 코드 경계가 정리되면 전면 새 감사가 아니라 해당 음성 검사·패키지 정합·고정 실행 조건만 재확인해 G-A027으로 진행할 수 있다. 이 보고서는 새로운 reward 탐색을 추가로 요구하지 않는다.

### 부록 A. C3·C1/C2 로컬 재현 코드

저장소 루트에서 실행한다. 원본 소스·정책·패키지는 수정하지 않고 임시 디렉터리에 요약을 만든다. 테스트 파일의 클래스·함수·import 정의만 로드하며 테스트 본문을 재실행하지 않는다.

```python
import ast, json, subprocess, sys, tempfile
from pathlib import Path

q = Path('workspace/training/quadruped')
sys.path.insert(0, str(q))
p = Path('tools/test_go2_posture_survival_contract.py')
m = ast.parse(p.read_text(encoding='utf-8'))
m.body = [x for x in m.body if isinstance(
    x, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))]
ns = {'__file__': str(p.resolve())}
exec(compile(m, str(p), 'exec'), ns)
runner = (q / 'server_run_go2_a017_full_suite.sh').read_text(encoding='utf-8')
check = runner.split("python3 - \"$1\" <<'PYEOF'", 1)[1].split('\nPYEOF', 1)[0]

for kind in ['full', 'half', 'none', 'gap_control', 'gap_missing']:
    steps = 1000 if kind.startswith('gap') else 100
    env = ns['StubEnv'](num_envs=2, height=.306, grav_z=-1., speed=1.)
    with tempfile.TemporaryDirectory() as td:
        c = ns['tel'].Collector(Path(td), steps)
        c.attach(env)
        def posture(*args):
            if kind == 'half': return [-1., -1.], [0., None]
            if kind == 'none': return [-1., -1.], [None, None]
            if kind.startswith('gap'):
                if kind == 'gap_missing' and c.step == 120:
                    return [-1., -1.], [None, None]
                return [-1., -1.], ([.2, .2] if 100 <= c.step < 140 else [0., 0.])
            return [-1., -1.], [0., 0.]
        c._posture = posture
        zero = ns['FakeTensor'](ns['np'].zeros(2))
        result = (None, None, zero, zero, {})
        for _ in range(steps): c.record(env, result)
        if not c.closed: c.close(True)
        path = Path(td) / 'summary.json'
        s = json.loads(path.read_text(encoding='utf-8'))
        r = subprocess.run([sys.executable, '-c', check, str(path)],
                           capture_output=True, text=True)
        print(kind, {k: s[k] for k in ['survival_proxy', 'fallen_env_count',
              'posture_coverage', 'posture_min_env_coverage']}, 'runner_rc', r.returncode)
```
