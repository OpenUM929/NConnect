# Go2 예선 캠페인 지침

## 증거 관리자 인계 (2026-09-20 적용)

데이터 정리·집계표 인용·튜닝 정책 판단 전 `GO2_DATA_STANDARD.md`와 `config/go2_evidence_data_dictionary.json`을 확인한다.
표준화된 5개 표는 원 숫자와 함께 정의·집단·창·단위·좌표계·원식/대리식 구분을 전달한다. 새 집계에도 같은 명세 계약을 적용하며 기존 데이터 이관 완료로 일반화하지 않는다.

공통 계약: `workspace/training/quadruped/GO2_EVIDENCE_HANDOFF.md`.
순서: INPUT_REVIEW → 분석가 → OUTPUT_REVIEW → 기획자 → OUTPUT_REVIEW → 독립 감사자 → PM 초안 → PM_REVIEW → PM 확정. 감사자의 새 주장도 OUTPUT_REVIEW 대상이며 감사 독립성을 유지한다.
PM이 전달마다 공통 계약의 검토 기록과 버전을 확인하고 관리자를 명시 호출한다(MANUAL_PM_DISPATCH). 변경 없는 자료·주장만 REUSE_UNCHANGED로 재사용한다. 자동 런타임 가로채기는 없으며 누락 검토는 UNREVIEWED로 표시한다.
증거 카드의 원자료와 학습 문서 수식·적용 범위를 직접 확인한다. 카드는 원문 열람을 대체하지 않는다.
사실 → 문서 기반 해석 → 경쟁 가설 → 반증 조건 → 선택을 구분한다. 결론 고정이 아니라 근거 있는 수정이 목적이다.
PM은 `.codex/agents/go2-evidence-manager.md`를 읽힌 담당자를 배치한다. 자료 공백은 한계로 보고하며 새 승인 게이트로 만들지 않는다.

이 파일은 저장소 루트 `AGENTS.md`를 대체하지 않는다. `workspace/training/quadruped/`에서
Go2 학습·평가·보고를 수행할 때 적용하는 최소 차이 지침이다.

## 1. 캠페인 정본과 범위

- H1 캠페인과 원장·점수·artifact를 섞지 않는다.
- **필독은 두 개다(2026-09-14 사용자 승인, 캠페인 감사 P3).**
  1. 루트 `GO2_NOW.md` — 현재 위치·동결 기준선·처리량·NEXT
  2. `GO2_REWARD_EVIDENCE_MASTER.md` §1-a·§1-b — 다이얼 시도 이력(새 후보는 해당 행 인용 필수)·외부 기준(Isaac Lab 공식 Go2 설정·문헌, G-D-EXTREF-20260915)
- **튜닝값을 도출·제안·판독할 때는 `reports/GO2_TUNING_BASE_DATA.md`(튜닝 기반 데이터, §0-1 항 역할)와 `reports/GO2_REWARD_MECHANISM_FORECAST.md`(기전·예측·튜닝 정책)를 추가로 필독한다(2026-09-16·09-17 사용자 지시).** §4 규칙 9.
- 아래 문서는 **조회용**이다. 필요한 절만 찾아 읽는다. 현재 상태가 `GO2_NOW.md`와 다르면 `GO2_NOW.md`가 이긴다.
  `GO2_PROJECT_STATE.md`(결정·사실 이력), `GO2_CAMPAIGN_SCHEDULE.md`, `GO2_REWARD_EVIDENCE_MASTER.md` 나머지 절,
  `config/go2_self_eval_registry.json`(G1~G7 정본), `upload/plan/`의 PRD·계획·brief.
  서버 실행·회수 작업에서는 루트 규칙대로 `ARTIFACT_MANAGEMENT.md`를 먼저 읽는다.
- 동결 기준선 식별자는 이 파일에 고정하지 않는다. `GO2_NOW.md` §1을 본다.
  260901 판의 "보존 비교군 Pilot-01(`c4d78adf…`) / 향후 기준선 Default-01"은 `SUPERSEDED`다.
  Default-01은 보행하지 않는다(G-D113). 기준선은 A017(G-D184)을 거쳐 2026-09-16부터 G-A033이다(G-D-BASELINE-A033-20260916).

### 1-a. Default Baseline PRD는 살아있는 정본

> 2026-09-14 정정: 이 PRD는 G-D94(260905)로 v1 범위(Default-01 vs Pilot-01)에서 종료됐다. 현재 위치의 living 정본은
> `GO2_NOW.md`, 결정 이력은 `GO2_PROJECT_STATE.md`다. 아래 PRD 동기화 의무는 이 두 파일 갱신으로 이행한다.

- `upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md`는 단발 계획서가 아니다. Go2 기획자는 매 기획 턴 시작과
  종료에 이 문서를 읽고, 최신 사용자 결정·artifact·구현 확정값·평가 결과·다음 분기를 반영한다.
- `go2-campaign-manager`는 목표·순서·분기·완료조건, `go2-test-planner`는 통제변수·metric·허용오차·
  산출물·후속 실험을 같은 턴에 갱신한다.
- 실제 artifact가 PRD보다 최신이면 artifact를 우선 판정하고 즉시 PRD를 갱신한다.
- PRD 변경 시 `GO2_PROJECT_STATE.md`, `GO2_CAMPAIGN_SCHEDULE.md`, `GO2_REWARD_EVIDENCE_MASTER.md`,
  `ARTIFACT_MANAGEMENT.md`, 상세계획·planner brief 중 영향받는 문서를 함께 동기화한다.
- PRD와 원장이 불일치하면 같은 턴에 동기화하고 진행한다. 불일치를 이유로 사용자가 요청한 튜닝 패키지 발행을
  멈추지 않는다(2026-09-14 개정). 동기화 완료는 장기 학습 승급의 조건으로만 쓴다.

## 2. Go2 G1~G7 정본

시나리오명·가중치·필수 측정은 반드시 `config/go2_self_eval_registry.json`에서 읽는다.

| ID | 시나리오 | 가중치 |
|---|---|---:|
| G1 | 전진 속도 추종 | 0.15 |
| G2 | 전방위 속도 추종 | 0.15 |
| G3 | 거친 지형 | 0.20 |
| G4 | 경사 ±20° | 0.15 |
| G5 | 계단 10~15cm | 0.15 |
| G6 | 밀침 회복 | 0.10 |
| G7 | 도메인 랜덤화 | 0.10 |

`server_run_Go2_videos.sh`는 G1 제자리·G2 전진·G3 좌우·G4 복합·G5 rough·G6 ±10°·G7 push로
구성된 H1형 복사본이다. 이 파일은 **`LEGACY_INVALID_MAPPING`**이며 Go2 G1~G7 커버리지,
자체 점수, 제출 승급의 근거로 사용하지 않는다. 역사적 파일을 조용히 덮어쓰지 말고 새 evaluator를 만든다.

## 3. 현재 단계와 다음 행동

- **이 절에는 고정된 next-action을 적지 않는다.** 현재 단계·다음 행동은 `GO2_PROJECT_STATE.md`의 최신 행과
  `upload/README.md`의 `Current experiment`에서 읽는다. (260914 이전 판의 "G-A007 `feet_air_time` only 허용"은
  `SUPERSEDED`이며 튜닝 제한 근거로 인용하지 않는다.)
- 사용자가 튜닝을 요청하면 루트 `AGENTS.md`의 **「튜닝 요청 산출물 계약」**이 이 파일의 모든 HOLD 규칙보다 우선한다.
  산출물은 `upload/<ID>/current/` 실행 패키지이며 review 자료로 대신하지 않는다.
- 긴 10,000~15,000 iter 학습은 1,000~5,000 iter 단일변수 승자, survival·tracking 비열등,
  독립 평가 seed 결과가 있어야 승급한다. 이 조건은 **장기 학습 승급** 조건이지 1,000 iter 단일변수 패키지의 발행 조건이 아니다.

## 4. 튜닝 규칙

1. 강좌 14강의 기본 원칙대로 한 번에 reward 하나만 바꾼다.
2. `기본값`, `권장 범위 중간`, `몇 배`는 값 선정 근거가 아니다.
   단 Isaac Lab 공식 Go2 설정은 모든 후보가 **대조해야 하는** 외부 기준이다(MASTER §1-b). 대조는 의무이고, 그 값 자체가 최적의 증거는 아니다.
3. 변경 전 목적함수, 직접 영향 G 시나리오, 예상 부작용, 성공·실패·INCONCLUSIVE,
   seed, iteration, 중단점, 영상·telemetry·bundle을 사전등록한다.
4. 점수는 `survival_proxy × tracking_proxy`로 분리한다. 평균 reward, terrain level,
   학습 `base_contact`만으로 자체 시나리오 점수를 만들지 않는다.
5. 같은 evaluator 지문으로 잰 쌍이 아니면 특정 reward를 `만족` 또는 `개선 원인`으로 쓰지 않는다.
   (260901 판의 "Pilot-01과 Default-01 비교 전" 조건은 G-D94로 끝났다. 한 항 변경 쌍은 `reports/GO2_VARIABLE_INFLUENCE.md` 등급 A만 변수 효과로 인용한다.)
6. 정책 간 성능 비교에 reward 계수가 다른 `Train/mean_reward` 절대값을 사용하지 않는다.
7. 단일 seed는 `exploratory`다. 장기 승급 전 최소 평가 seed 101·202·303을 적용한다.
   학습 seed는 전 회차 42 하나라, 한 회차의 결과는 **가설의 지지·반박**이지 레버 효과 확정이 아니다(`reports/GO2_SEED_SENSITIVITY.md`, 2026-09-17).
8. **외부 기준 대조(2026-09-15 사용자 결정 G-D-EXTREF-20260915).** 분석·후보 비교·결과 판독에 MASTER §1-b를 넣는다.
   - 항별 대조: Isaac Lab Go2 rough 값·배포 시작값·기준선 값·이탈 여부(`tools/go2_external_reference_diff.py`)
   - 관련 문헌 원리와 R-6 적용 가능 여부
   - Isaac Lab 값에서 멀어지는 후보는 이탈 근거를 적는다. 새 후보 사양(G-A031~)은 `external_reference` 필드를 가진다.
9. **기반 데이터에서 값을 도출한다(2026-09-16 사용자 지시: "데이터를 기반으로 특이점을 찾고 이를 기반으로 튜닝 값을 잡는다").**
   - 정본 `reports/GO2_TUNING_BASE_DATA.md` — 증거 CSV에서 `tools/go2_tuning_base_data.py`가 생성한다. 손으로 고치지 않는다.
   - 답과 문서는 **원자료 행 → 특이점 → 값** 순서로 쓴다. 결론만 말하고 데이터를 생략하지 않는다.
   - 보상 산수·항 크기·외부 기준값은 보조 근거다. 도출 원리가 표의 다른 회차와 반대로 나오면 그 원리로 값을 정하지 않는다.
   - 바꾸는 가중치마다 걷는 회차 관측값 대비 위치(`OBSERVED`·`BETWEEN_OBSERVED`·`OUT_OF_RANGE`)를 사양 `base_data`에 적는다. `OUT_OF_RANGE`는 `out_of_range_reason` 필수.
   - 새 학습 회수 후에는 `tools/go2_stairs_behavior.py` → `tools/go2_tuning_base_data.py` 순서로 재생성한다.
   - 관문: `tools/test_go2_tuning_base_data_contract.py`.
   - **변수 영향은 `reports/GO2_VARIABLE_INFLUENCE.md`에서 읽는다(2026-09-17 사용자 지시: 모든 변수를 track처럼 검수).** 한 항 변경 쌍마다 env 차이·체크포인트·기준 캐시·걷기 여부를 대조한 등급(A~E)이 붙어 있다. 등급 A가 아닌 쌍의 결과를 걷는 기준의 변수 효과로 인용하지 않는다. 생성 `tools/go2_variable_influence.py`, 관문 `tools/test_go2_variable_influence_contract.py`. 새 한 항 변경 회차를 회수하면 `PAIRS`에 추가하고 재생성한다.
   - **변수를 말할 때는 먼저 역할을 적는다(2026-09-17 사용자 지시: 기준 문서의 역할 설명 없이 우리 결과로만 판단하지 않는다).** 역할은 기반 데이터 §0-1(Isaac Lab v2.3.1 원문 식, `reports/evidence/go2_reward_term_roles_20260917/`)에서 읽는다. 답의 순서는 원문 역할 → 우리 원자료 행 → 둘이 맞는지 → 값이다. 새 사양의 `base_data.terms.<항>.role`에 원문 설명이 들어가야 관문을 통과한다.
   - **현재 상황과 변수 변경 결과는 `reports/GO2_REWARD_MECHANISM_FORECAST.md`로 예측한다(2026-09-17 사용자 지시: 원문 역할에 기반한 사실 추론).** 생성 `tools/go2_reward_mechanism.py`, 관문 `tools/test_go2_reward_mechanism_contract.py`.
     - 후보마다 **네 구간**을 계산해 사양 `base_data.walk_margin`에 적는다(2026-09-17 사용자 지시: "걷기로만 하지 말고 계단과 흔들림도 염두에 둔다").
       - 걷기: 학습 로그 margin
       - 계단·흔들림·밀침: 평가 기록 부분 margin(`situations`)
       - 걷기 구간이 아니거나 `worse`가 비어 있지 않으면 `reason` 필수다(관문 검사).
       - 세 정책에서 부호가 엇갈리는 항(보고서 §5-1 †)은 예측 근거로 쓰지 않는다.
     - 튜닝 정책은 그 문서 §8에서 읽는다. **정책 내용을 이 파일에 옮겨 적지 않는다**(2026-09-17: 옮겨 적은 사본이 G-A038 반박 뒤에도 남아 있었다. 관문 `tools/test_go2_policy_text_contract.py`).
     - 새 학습 회차를 회수하면 재생성한다. 예측 구간과 실제 결과가 어긋나면 정책부터 고친다.
   - **판정 규칙은 `fact_rules_v1`이다(2026-09-17, G-D-FACT-RULES-20260917).** 목표 축 G3·G5, 보호 축 G1·G2·G4·G6·G7. 표적 묶음마다 하한, 계단은 **오른 로봇 수**로 잰다(G5 점수는 case 최솟값이라 계단 붕괴를 보지 못한다). 코드 `tools/go2_fact_rules.py`, 한도 생성 `tools/go2_fact_rules_spec.py`, 관문 `tools/test_go2_fact_rules_contract.py`.
   - **후보는 사실 근거 추론 사슬로 고른다(같은 결정).** 사양 `inference` 블록: 원문 역할 → 원자료 행(반대 행 포함) → 특이점 → 네 구간 방향 → 반증 조건 → 위험 축. 이득 수치는 요구하지 않는다. 관문 `tools/test_go2_detectability_gate.py`.
   - **위험 축은 기준선 최약 case로 지킨다(2026-09-22, 결함 C-11).** `원자료 행 → 특이점 → 값`은 **값에만** 적용되는 순서가 아니다. 무엇을 재고 무엇을 지킬지도 원자료에서 고른다. `inference.risk_axes`에 적은 축은 1단계 목록에 그 축의 **저장된 기준선 최약 case**(생존×추종 최소)가 들어가야 한다.
     - 실증: G-A043은 위험 축에 G2를 적고 1단계 23 case에는 G2의 lateral(`left`·`right`)만 넣었다. 실제로 깨진 것은 G2 최약 case `combined_yaw_right`(평가 seed 3개 전부)였고, 1단계는 TARGET_PASS를 냈다. 결정적 손실은 전수 69를 다 돌린 뒤에야 보였다.
     - 이유: 1단계 목록은 **표적 축**에서 만들어진다. 그래서 표적 축 악화는 조기에 멎지만(G-A042가 실제로 1단계에서 멎었다) 보호 축 악화는 멎지 않는다. 시나리오 점수가 case 최솟값이라는 성질(위 `fact_rules_v1` 항의 G5 설명과 같은 성질)이 G2에서도 그대로 작동한다 — 한 case가 시나리오 전체를 끌어내린다.
     - 최약 case는 회차 **전에** 저장된 기준선 69 case에서 계산된다: `tools/go2_stage1_blind_spot.py`(0.1초). 관문 `tools/test_go2_detectability_gate.py::test_17`. 한계 — 최약 case는 '가장 먼저 무너질 자리'의 **대용**이지 증명이 아니다. 전수 69를 걷는 회차는 못 보는 자리가 없어 면제되지만, 그 면제는 **사양이 전수 수집을 선언했을 때만** 적용된다(`collection.mode = "full_69_single_stage"`, 빌더가 `run_config.env`에 `GO2_STAGE=full`을 쓴다). 선언 없이 1단계 목록만 비우면 관문이 막는다 — 그것은 C-11을 고친 것이 아니라 감춘 것이다(2026-09-22, G-A044).

## 5. 증거 계층

다음 용어만 사용한다.

- `ARTIFACT_VERIFIED`
- `VIDEO_OBSERVED` / `VIDEO_UNKNOWN`
- `INTERNAL_GATE_PASS` / `INTERNAL_GATE_FAIL` / `INTERNAL_GATE_INCONCLUSIVE`
- `SELF_ASSESSMENT_PASS` / `SELF_ASSESSMENT_INCOMPLETE`
- `OFFICIAL_RESULT_UNMEASURED` / 실제 공식 결과

bare `PASS`, `합격`, `통과 확정`을 쓰지 않는다. 영상, telemetry, 내부 proxy, 공식 결과는 서로 승격하지 않는다.

## 6. 자체평가 규칙

- 내부 v1은 후보 `env.yaml`에서 tracking `std`를 읽어
  `tracking_proxy=exp(-(RMSE/std)^2)`로 계산한다. 공식 변환식이라고 부르지 않는다.
- 시나리오 내부 게이트: survival ≥0.95, tracking ≥0.70. 양방향·다중 조건은 최악값을 쓴다.
- G1~G7 중 하나라도 survival/tracking이 빠지면 `SELF_ASSESSMENT_INCOMPLETE`이며 보수적으로 0점 처리한다.
- 전 시나리오 측정, 각 게이트 통과, 가중 simulation proxy ≥0.70이 자체 시뮬 최소조건이다.
- 설계 의도·리포트 자체감사와 합산한 총 자체예상은 최소 70/100, 운영 목표 75/100이다.
- 공식 evaluator의 명령·지형·push·DR·tracking 변환·통과선은 미공개이므로 `공식 재현`이라 쓰지 않는다.
- 시나리오 점수는 case·seed 최솟값이다(registry `scenario_aggregation`, 내부 설계). 그래서 G5는 15cm 오르기 0 근처에 묶여 계단 능력의 변화를 보여 주지 못한다. **계단은 점수와 함께 오른 로봇 수(`tools/go2_climb_count.py`)로 보고·판정한다**(2026-09-17, G-A038에서 10cm 오르기가 무너졌는데 G5 손실은 0.045/70이었다).

## 7. 제출 계약

260901 사용자 제공 1라운드 제출 화면 기준:

1. 로봇 유형 `사족보행 로봇` 선택
2. `policy.pt` 업로드
3. 해당 정책과 같은 run의 `env.yaml` 업로드
4. 기술 개선 리포트 입력 — **2라운드부터 500자 상한**(루트 `AGENTS.md` R-4a). 1라운드는 30~200자였다.

장문 내부 보고서는 제출문(500자)을 뒷받침하는 증거다.
제출문의 작업 방법 설명은 "Isaac Lab 공식 Go2 rough 설정 대비 바꾼 항·근거·측정 결과" 형식으로 쓴다(MASTER §1-b 규칙 6).
`config/go2_self_eval_registry.json`의 `technical_report.maximum_characters: 200`은 1라운드 화면 기록이며 **의도적으로 고치지 않는다**.
registry SHA(`8d8c34ca…9ba6`)는 A027 평가의 `registry_sha256` 지문이다. 바꾸면 기준선(G-A033, 같은 지문)과 다음 후보의 계측 대칭이 깨진다.
제출문 상한의 정본은 이 절과 R-4a다. `report.html`과 영상은 기본 제출물이 아니다.
제공 화면상 팀원 누구나 제출 파일을 수정·삭제할 수 있고 심사 시작 전까지 자유롭게 수정할 수 있다.
다만 **현재 심사가 시작됐는지**는 외부 대시보드 상태이므로 실제 화면 증거가 없으면 `[미측정]`으로 둔다.

## 8. 역할 라우팅

- 점수축·단계·순서: `go2-campaign-manager`
- 다음 단일변수 실험: `go2-test-planner`
- run 결과·원장·제출문(2라운드부터 500자, §7): `go2-report-writer`
- G1~G7·score math·seed·증거계층 독립 감사: `go2-evaluation-auditor`
- SHA·tar·manifest: 공용 `artifact-verifier` (`explore`/Luna/low)

메인 팀장이 최종 통합·서버 종료·공식 제출 판정을 소유한다.

## 9. 휘발성 서버

- 서버는 접속마다 초기화된다. 로컬 `workspace/training`이 정본이다.
- 서버를 켜기 전에 package, SHA, CRLF, `bash -n`, 예상시간, 완료표식, 다운로드 경로를 로컬에서 닫는다.
- 사용자 작업은 `zip 업로드 → 검증된 한 줄 실행 → bundle 다운로드`로 제한한다.
- 사용자가 다운로드/서버 종료를 말하면 분석보다 로컬 SHA·manifest·필수 artifact 확인을 먼저 한다.
- 필수 영상·telemetry·bundle의 로컬 검증 전에는 서버 종료 가능이라고 말하지 않는다.

### 9-a. 사용자 실행 패키지 자동 제공 계약

- 새 튜닝은 서버 생성 원본 `exported/report.html`을 평가 재생 전에 `_keep/<튜닝명칭>/exported/report.html`로 보존하고 결과 ZIP·SHA 목록에 포함한다. 누락·빈 파일·이전 실행 report는 `REPORT_REQUIRED_NOT_ACQUIRED`; 회수 완료로 표시하지 않는다. 재개 시에도 보존 report와 SHA를 검사한다. 모든 서브에이전트와 새 패키지에 적용하고 과거 승인 ZIP은 보존한다.

- 넘버링은 G-D98·G-D175·G-D178을 따른다. 원장·upload 중복 확인 후 다음 미사용 ID를 등록하고 패키지 파일명에 회차 ID를 넣는다. 실행 정본은 `upload/<ID>/current/`, 미승인 검토 자료는 `upload/<ID>/review/`에 둔다. 날짜·정책명으로 회차를 대신하지 않으며 예약 번호를 실행 완료처럼 보고하지 않는다. **튜닝 요청에는 `current/` 실행 패키지로 답한다. `review/`는 사용자가 검토를 명시 요청했을 때만 만든다.**

- **경로 계약(2026-09-13 사용자 정정): `upload/plan/`에는 계획 문서만 저장한다.** 튜닝 업로드 ZIP, 검토용 ZIP, SHA, 배포 manifest와 실행 파일은 `upload/` 또는 기존 작업별 release 디렉터리에 저장한다. 생성 전 `upload/README.md`를 확인하고 전달 전 경로를 검사한다. 이 규칙은 모든 서브에이전트에도 적용한다. 검토용 자료와 서버 실행 패키지는 별도로 표시한다.

- 사용자의 역할이 서버 실행·회수인 작업은 사용자가 다시 요구하지 않아도 메인 루프가 먼저 다음을 완성한다:
  `업로드 ZIP 생성 → 로컬 SHA/CRC/manifest/CRLF/bash -n 검증 → 로컬 ZIP 절대경로 → 서버 업로드 경로 →
  복사 가능한 한 줄 명령 → tmux 확인 명령 → 완료 표식 → 필수 다운로드 경로 → 서버 종료 게이트`.
- 결과 artifact가 여러 종류면 server runner가 이를 **단일 결과 ZIP**으로 자동 묶는다. 사용자는 개별 영상·로그·
  telemetry를 하나씩 내려받지 않는다.
- 실행 ZIP이 아직 없거나 로컬 검증이 끝나지 않았으면 명령만 먼저 주지 않는다. `HOLD — package 미검증`으로 두고
  package와 테스트를 먼저 만든다.
- 사용자 보고 첫 화면의 `[지금 할 일]`에는 위 계약에서 사용자가 실제로 수행할 다음 동작 하나만 쓴다.
- 완료 보고에는 최소한 `ZIP 경로 / SHA256 / 업로드 위치 / 한 줄 실행 / 완료 표식 / 결과 ZIP / 서버 종료 조건`을
  자동으로 포함한다.

아래 표시 구간은 `tools/update_go2_report_first_contract.py`가 관리하는 2026-09-13 기록이다. 그 안의 NEXT·HOLD·기준선 언급은 당시 상태이며 현재 지시가 아니다(현재는 `GO2_NOW.md`).

<!-- GO2:REPORT-FIRST:START -->
## 학습 report 필독·원인 우선 연구 계약 (2026-09-13 사용자 결정)

H1·Go2 튜닝 기획·평가·보고를 수행하는 메인과 모든 서브에이전트에 적용한다.
보고서 존재 확인이나 다른 배우의 요약만으로 읽었다고 하지 않는다.

1. **튜닝 후보 선정 전에 해당 정책과 대조군의 학습 `report.html` 본문을 직접 읽는다.**
   학습 run·checkpoint iter/model SHA·env reward snapshot·학습 로그와 대응을 확인한다.
   파일명/수정시각/같은 폴더만으로 대응을 확정하지 않는다. export 해시 차이는 tensor 의미 차이로 단정하지 않는다.
2. `REPORT_READ_STATUS=READ_MATCHED|READ_UNMATCHED|MISSING|NOT_APPLICABLE`를 출력한다.
   읽은 경로·보고서의 학습시각/iter/보상값·대조한 로그와 정책 식별자·일치/불일치·미확인 근거를 남긴다.
   `READ_MATCHED`는 대응 확인이지 성능 판정이 아니다.
3. 학습 HTML, 내부 `SELF_EVAL_REPORT`, 기술 개선 제출문은 서로 다른 자료다.
   평가 전용 run은 새 학습 HTML이 없을 수 있으나, 튜닝에 쓰는 정책의 원 학습 report 조회를 생략하지 않는다.
   `NOT_APPLICABLE`은 정책을 생성하지 않은 도구 smoke 등 실제 비해당 사유를 적을 때만 사용한다.
4. report 누락/오래된 파일/정책 대응 불명은 `REPORT_REQUIRED_NOT_ACQUIRED` 또는
   `REPORT_POLICY_UNMATCHED`로 기록한다. 먼저 로컬 원 학습 bundle·보존 snapshot·로그를 검색한다.
   그래도 없으면 회수/복구 방법을 기록한다. 추정 HTML을 원본인 것처럼 만들지 않는다.
   **[2026-09-14 개정] 휘발 서버에서 이미 사라진 과거 run의 report는 `REPORT_REQUIRED_NOT_ACQUIRED — 복구 불가`로
   한 번 기록하고, 같은 run의 원 학습 로그 요약값(최고 reward·terrain level·학습 낙상률·action std)과
   SELF_EVAL을 대체 근거로 삼아 진행한다. 이 상태는 새 reward 후보 확정·새 학습 패키지 발행을 막지 않는다.**
   막히는 것은 새 run의 회수 완결 판정(§7)뿐이다. 같은 archive를 재검색하거나 원본 제공을 반복 요청하지 않는다.
   (구판 차단 문구는 `SUPERSEDED` — 루트 「튜닝 요청 산출물 계약」 참조.)
5. 연구 순서는 **학습 report·env·로그 대응 → 내부 시나리오 평가 → 영상/telemetry로 실패 유형 구분
   → 경쟁 가설 비교 → 근거 있는 단일변수 후보 → 대조 실험·독립 seed**다.
   HTML의 안정/공격 설명과 일반 경고는 가설 단서일 뿐 인과효과·최적 가중치 근거가 아니다.
6. 학습낙상률/terrain level/mean reward를 시나리오 survival/tracking 또는 공식 점수로 바꾸지 않는다.
   보고서 수치의 집계 구간과 지표 출처를 확인하고, 충돌은 원 로그와 evaluator 조건으로 해소한다.
7. 새 학습 회수에는 같은 run의 `report.html`과 로그·env·checkpoint 대응 자료를 결과 bundle 및 SHA 목록에 포함한다.
   누락하면 해당 공백을 기록하며 다운로드 완결 또는 튜닝 근거 완결로 보고하지 않는다.
8. 최신 지침은 역할 문서의 과거 다음 실행·고정 현재단계보다 우선한다. H1/Go2 캠페인은 분리한다.
   서브에이전트는 권한 범위 내 직접 읽기만 수행하고 공백을 상위에 보고한다. 이 계약은 편집/서버 권한을 추가하지 않는다.

## 2026-09-13 연구 방향 변경 — G-D-REPORT-FIRST-20260913
- 사용자 결정: 지침과 서브에이전트에 학습 report 필독을 강제하고 연구 방향을 변경한다.
- 새 순서: report·env·학습로그/정책 대응 → 시나리오 약점 → 실패 유형/경쟁 가설 → 후보 선정.
- 이전 T1 `ang_vel_xy_l2 -0.05→-0.06`은 **DEFERRED_HYPOTHESIS**로 내린다. 다음 튜닝값/1순위가 아니며 효과 INCONCLUSIVE.
- G5 하강 생존은 현재 평가상 우선 진단 대상이나 원인은 미확정. 회전 과다, 발걸림/정지, 낮은 자세,
  학습 성숙도 및 평가/영상 대응 문제를 구분한다. 모두 가설이며 보고서만으로 인과를 판정하지 않는다.
- Pilot HTML은 직접 읽었으나 이번 작업에서 정책 대응을 완결 검증하지 않았으므로 READ_UNMATCHED.
  A017 원 학습 HTML은 현재 탐색 범위에서 MISSING / REPORT_REQUIRED_NOT_ACQUIRED.
  A027 SELF_EVAL_REPORT는 원 학습 HTML을 대체하지 않는다.
- NEXT: 로컬 원 학습 bundle·snapshot·로그에서 A017/Pilot report 대응을 먼저 회수·검증한다.
  그 후 필요한 진단을 다시 동결한다. 기존 18case 목록은 제안 범위이며 실행 승인/고정 패키지가 아니다.
- 서버 실행·reward/배포코드 변경 없음. 새 학습 HOLD — report 대응 및 진단 근거 미완료.
- 작업 ID GO2-P1-PREP-20260913 유지. 과거 승인 release와 결과는 변경하지 않는다.
<!-- GO2:REPORT-FIRST:END -->
