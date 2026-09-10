# Opus 제공용 — Go2 연속 실패 원인 독립 재감사 및 교차검증 프롬프트

아래 작업은 **새 대화/새 컨텍스트**에서 수행하라. 이전 대화에서 읽은 결론이나 기억을 근거로 사용하지 말고, `C:\dev\Nconnect`의 로컬 원자료에서 모든 사실을 다시 재구성하라.

## 1. 역할과 목표

너는 네이버 커넥티드 로봇틱스 컵 Go2 강화학습 튜닝 캠페인을 감사하는 **독립 수석 감사관**이다.

이번 감사의 핵심 질문은 다음과 같다.

> **왜 Go2 캠페인은 H1 캠페인보다 연속적인 실패 판정과 기준선 교체를 겪으며 튜닝이 난항에 빠졌는가?**

단순히 “Go2가 더 어렵다”거나 “reward 값이 나빴다”고 요약하지 말라. 다음 세 범주를 분리해 인과사슬을 재구성하라.

1. **실제 정책 성능 실패** — 같은 세대·같은 조건의 평가에서도 정책이 실제로 붕괴하거나 열화했는가
2. **측정·평가기 실패** — evaluator 세대, 생존 판정, 시나리오 집계, seed, checkpoint 선택 또는 baseline/candidate 비대칭이 결과를 왜곡했는가
3. **캠페인 운영·의사결정 실패** — 기준선 승급, 단일변수 통제, 반복 seed, 판정 gate, 실험 순서가 증거보다 앞서갔는가

각 원인은 **확인됨 / 유력한 추론 / 미확인** 중 하나로 분류하고, 영향도와 증거 강도를 별도로 표시하라.

## 2. 절대 독립성 규칙

### Phase I가 끝날 때까지 열면 안 되는 파일

- `C:\dev\Nconnect\GO2_DESIGN_REVIEW_260907.md`
- `C:\dev\Nconnect\GO2_INDEPENDENT_AUDIT_CODEX_260907.md`
- 위 두 문서의 SHA 파일, 요약본, 이를 직접 인용한 2차 문서

파일명 검색이나 디렉터리 목록에서 이름이 보이는 것은 허용하지만, **내용을 열거나 grep하지 말라.** 먼저 읽은 결론에 맞추는 감사는 무효다.

Phase I 결과를 저장하고 SHA256을 기록한 뒤에만 Phase II에서 두 감사 문서를 읽어라. 가능하면 셸 히스토리 또는 작업 로그에 열람 순서를 남겨라.

## 3. 증거 규칙

1. 모든 사실 주장은 `파일 경로:줄 번호` 또는 `JSON 경로#/필드`를 붙인다.
2. 줄 번호가 없는 JSON 요약만으로 판단하지 말고 가능한 경우 원본 `SELF_EVAL_REPORT.json`, `TIER1_DECISION.json`, step/case telemetry까지 추적한다.
3. 규정·주석·강좌 인용은 원문 위치를 밝히고, 요약과 원문을 구분한다.
4. `test/` 강좌에 공식 채점식이 실제로 있는지 전수 검색하라. 없으면 “강좌에는 공식 채점식 근거가 없다”고 증거와 함께 판정하고, 공식 규정 정본과 개념 교육 자료를 혼동하지 말라.
5. `survival × tracking`, 내부 proxy, 캠페인 gate, 공식 결과는 서로 다른 층위다. 내부 수치를 공식 점수로 부르지 말라.
6. 다음 증거 용어만 사용하라.
   - `ARTIFACT_VERIFIED`
   - `VIDEO_OBSERVED` / `VIDEO_UNKNOWN`
   - `INTERNAL_GATE_PASS` / `INTERNAL_GATE_FAIL` / `INTERNAL_GATE_INCONCLUSIVE`
   - `OFFICIAL_RESULT`
7. bare `PASS`, `합격`, `제출 가능`, `공식 점수` 표현을 금지한다.
8. 해시가 다르다는 이유만으로 정책 tensor가 다르다고 단정하지 말라. 정책 동일성은 가능한 경우 checkpoint iter, `model_best.pt` SHA256, tensor 비교를 구분해 판단하라.
9. H1의 reward 값·임계값을 Go2 사실로 전이하지 말라. H1에서 비교 가능한 것은 실험 방법, 증거 폐쇄성, 평가 순서, 반복 설계다.
10. 공식 evaluator와 공식 결과가 로컬에 없으면 `[미확인]` 또는 `[미측정]`으로 둔다.

## 4. 우선 읽을 정본과 원자료

AGENTS 지침 충돌 시 저장소의 최신 `AGENTS.md`와 하위 `workspace\training\quadruped\AGENTS.md`를 우선하라. 최소한 다음 자료군을 조사하되, 결론은 실제 파일 내용으로부터 재구성하라.

### 공식 규정·공통 개념

- `C:\dev\Nconnect\AGENTS.md`
- `C:\dev\Nconnect\workspace\PRELIM_RL_GUID.md`
- `C:\dev\Nconnect\workspace\training\PRELIM_RL_GUIDE.md`
- `C:\dev\Nconnect\test\**\*`

### Go2 정본·코드·실험 원자료

- `C:\dev\Nconnect\GO2_PROJECT_STATE.md`
- `C:\dev\Nconnect\GO2_CAMPAIGN_SCHEDULE.md`
- `C:\dev\Nconnect\GO2_REWARD_EVIDENCE_MASTER.md`
- `C:\dev\Nconnect\ARTIFACT_MANAGEMENT.md`
- `C:\dev\Nconnect\workspace\training\quadruped\AGENTS.md`
- `C:\dev\Nconnect\workspace\training\quadruped\quadruped_rewards.py`
- `C:\dev\Nconnect\workspace\training\quadruped\config\go2_self_eval_registry.json`
- `C:\dev\Nconnect\workspace\training\quadruped\go2_eval_telemetry.py`
- `C:\dev\Nconnect\workspace\training\quadruped\go2_fixed_eval_report.py`
- `C:\dev\Nconnect\workspace\training\quadruped\go2_task\_finalize.py`
- `C:\dev\Nconnect\workspace\training\quadruped\server_run_go2_tuning_engine_v1.sh`
- `C:\dev\Nconnect\workspace\_keep\**\SELF_EVAL_REPORT.json`
- `C:\dev\Nconnect\workspace\_keep\**\TIER1_DECISION.json`
- A006~A025와 연결되는 experiment spec, manifest, status, telemetry, checkpoint 및 로그

### H1 비교 원자료

- `C:\dev\Nconnect\H1_REWARD_EVIDENCE_MASTER.md`
- `C:\dev\Nconnect\PROJECT_STATE.md`
- `C:\dev\Nconnect\CAMPAIGN_SCHEDULE.md`
- `C:\dev\Nconnect\workspace\training\humanoid\humanoid_rewards.py`
- `C:\dev\Nconnect\workspace\training\humanoid\eval_telemetry.py`
- `C:\dev\Nconnect\workspace\training\humanoid\reports\**\*`
- H1 Run01~Run06의 config, checkpoint, evaluation seed, telemetry 및 판정 원자료

경로가 없으면 추정하지 말고 `[미확인: 파일 부재]`로 기록하라.

## 5. Phase I — 원자료 기반 독립 감사

### 5.1 감사 인프라와 공식 채점 구조

다음을 줄 단위로 대조하라.

- 공식형 구조: 시나리오 점수 `survival_rate × tracking_score`, 시나리오 가중 합산
- Go2 내부 proxy의 곱셈 구조와 tracking 변환식
- `termination_only_v1`과 `posture_gate_v2`의 실제 생존 판정
- 자세 게이트가 중력 투영과 지면 대비 높이를 어떤 논리식으로 결합하는지
- G1~G7 scenario aggregation이 같은 case/direction의 survival과 tracking을 결합하는지
- G6 밀침 회복에서 reporter가 실제로 읽는 필드
- G3와 G7이 독립 조건인지, step/case 데이터가 중복됐는지
- registry의 `schema_version`, evaluator fingerprint, `std`, 시나리오 weight와 실제 산출물의 일치 여부
- `min_total_points_delta`, `max_survival_regression`, target scenario gate가 공식형 목적함수와 어떤 관계인지

판정은 최소한 아래 세 가지로 나눠라.

- `FORMULA_PROXY_RESULT`: 공식형 곱셈·가중합으로 계산한 내부 결과
- `CAMPAIGN_GATE_RESULT`: 캠페인이 추가한 안전·승급 gate 결과
- `OFFICIAL_RESULT`: 실제 운영진 결과. 없으면 전부 `[미측정]`

### 5.2 A006~A025 전수 감사

A006부터 A025까지 빠짐없이 표로 정리하라. 각 행에 다음 열을 포함한다.

| Run | 실행 유형 | baseline 정책·iter·SHA | candidate 정책·iter·SHA | 학습 seed | 평가 seed | evaluator/schema | 단일변수 여부 | 절대 proxy /70 | delta /70 | 공식형 결과 | gate 결과 | 판정 유효성 | 실패 분류 | 근거 |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|

특히 다음을 검증하라.

1. 실행이 실제 학습인지, 평가 전용인지, 인프라 작업인지, 미실행인지, 중복인지
2. baseline과 candidate가 같은 evaluator 세대·schema·scenario set·seed 조건으로 비교됐는지
3. 절대 `candidate_points_70`과 delta/gate가 다른 결론을 냈는지
4. 양의 총점 delta가 target 또는 survival gate로 거절된 사례와 그 수치
5. 같은 세대 평가에서도 실제 성능이 크게 붕괴한 사례와 그 수치
6. 동일 checkpoint 또는 동일 결과를 별도 독립 증거처럼 중복 계상했는지
7. 1,000 iteration·단일 학습 seed·단일 평가 seed로 reward 효과를 확정했는지
8. `model_best.pt`가 어떤 기준으로 선택됐고, 실제 비교 checkpoint iter가 서로 달랐는지
9. reward 변경 효과와 PPO 학습 분산·checkpoint 선택 효과를 분리할 no-op control이 있었는지

### 5.3 H1 대 Go2 비교 — 이번 감사의 핵심

H1을 성공 신화로 가정하지 말고 H1 자체의 한계도 함께 감사하라. 아래 비교표를 작성한다.

| 비교 축 | H1 원자료에서 확인된 사실 | Go2 원자료에서 확인된 사실 | 차이가 실패 연속성에 미친 영향 | 증거 강도 |
|---|---|---|---|---|

최소 비교 축:

- baseline을 확정한 시점과 조건
- 한 번에 바꾼 reward 변수 수
- screening iteration과 장기 학습 승급 기준
- 학습 seed와 평가 seed 반복 수
- evaluator 세대 고정 여부
- 자세 기반 생존 검증 범위
- checkpoint 선택 기준과 비교 iter 정합성
- 정책 평가 완료 후 다음 학습으로 넘어갔는지
- 시나리오 구성과 지형·경사·계단·DR 비중
- 안전성 reward/levers의 실제 활성 상태
- 영상, telemetry, 내부 정량, 공식 결과의 분리
- 실패 실험이 다음 의사결정을 실제로 구분했는지

그 뒤 아래 질문에 답하라.

1. “Go2의 연속 FAIL” 중 몇 건이 **실제 정책 실패**, **비교 무효/계측 실패**, **관리상 실패**, **미실행·중복**인가? 숫자를 제시하되 분류 기준과 근거를 붙인다.
2. H1이 Go2보다 잘 진행된 핵심 이유가 정책·reward 자체인가, 아니면 실험 설계와 증거 폐쇄성인가?
3. Go2의 시나리오 구조가 H1보다 어려웠다는 주장이 로컬 규정으로 어디까지 확인되는가? 구조적 난도와 현재 캠페인 실패의 직접 원인을 구분하라.
4. H1 evaluator에도 생존 판정 한계가 있는가? 있다면 H1을 비교 기준으로 사용할 수 있는 범위를 제한하라.
5. Go2 reward 값의 문제라고 인과적으로 확정할 수 있는 실행과, 현재 자료로는 확정할 수 없는 실행을 나눠라.
6. 평가기를 먼저 고치지 않고 새 reward 학습을 계속할 경우 어떤 종류의 오류가 반복되는가?

### 5.4 인과사슬과 우선순위

최종 원인을 단순 나열하지 말고 다음 형식으로 작성하라.

`원자료 사실 → 잘못된 측정/판정 또는 의사결정 → 다음 실행 선택에 미친 영향 → 연속 실패처럼 관측된 결과`

상위 원인 3~7개를 영향도 순으로 배열하고 각 원인에 다음을 붙인다.

- 증거 강도: `높음 / 중간 / 낮음`
- 반증 가능 조건
- 영향을 받은 A-run 목록
- 교정하지 않을 때 재발하는 실패 형태

### 5.5 독립 개선 계획

새 학습을 기본값으로 두지 말고, 정보가치가 높은 순서로 계획하라.

계획은 최소한 다음 단계를 검토해야 한다.

1. evaluator 계약과 fingerprint를 고정하는 무-GPU 검증
2. G1~G7 scenario·posture·G6·G7·aggregation 회귀 테스트
3. 기존 baseline/candidate의 동일 evaluator 재판정
4. 기존 유망 후보의 다중 evaluation seed 재검증
5. 동일 reward no-op retrain을 통한 PPO/checkpoint 분산 추정
6. 그 뒤에만 단일변수 3,000→5,000 iteration 승급 여부 결정

각 단계에 아래를 사전등록 형식으로 써라.

- 목적과 직접 측정 G1~G7
- 입력 policy/checkpoint 식별자
- 변경값과 고정값
- seed와 반복 수
- 성공 / 실패 / `INCONCLUSIVE` 기준
- 예상 GPU 시간 범위와 조기중단점
- 필수 artifact·telemetry·영상·다운로드 목록
- 성공 시 다음 분기 / 실패 시 fallback

### 5.6 Phase I 산출물 봉인

Phase I 결과를 다음 파일로 저장하라.

`C:\dev\Nconnect\GO2_OPUS_REAUDIT_INDEPENDENT_260907.md`

저장 후 SHA256을 계산해 다음 파일에 기록하라.

`C:\dev\Nconnect\GO2_OPUS_REAUDIT_INDEPENDENT_260907.sha256`

이 시점까지 금지된 두 감사 문서를 읽지 않았음을 본문에 명시한다.

## 6. Phase II — Codex 감사 및 기존 Opus 감사와 교차검증

Phase I 봉인 뒤에만 다음 문서를 읽어라.

- `C:\dev\Nconnect\GO2_INDEPENDENT_AUDIT_CODEX_260907.md`
- `C:\dev\Nconnect\GO2_DESIGN_REVIEW_260907.md`

기존 Opus 문서는 개정 이력이 있으므로 폐기 표시된 §7을 현행 계획으로 취급하지 말고, §12~§14를 포함한 최신 상태를 읽어라.

다음 대조표를 작성하라.

| 쟁점 | Phase I 독립 결론 | Codex 감사 결론 | 기존 Opus 결론 | 분류 | 원자료 기준 최종 판정 |
|---|---|---|---|---|---|

`분류`는 `동의 / 부분동의 / 불일치 / 한쪽만 발견 / 양쪽 모두 누락` 중 하나다.

반드시 대조할 쟁점:

- Go2가 H1보다 연속 실패한 원인
- evaluator 세대 비대칭의 영향 범위
- 공식형 절대 proxy와 delta/gate 중 무엇이 어떤 의사결정에 적합한지
- 양의 총점 delta이나 안전 gate로 거절된 사례
- 같은 세대에서도 실제 붕괴한 후보
- 1,000 iteration의 정당한 용도와 오용 범위
- baseline 승급 및 교체 순서
- G3/G7 독립성
- posture gate 논리
- G6 recovery 필드
- scenario aggregation
- hard-coded tracking std와 schema 정합성
- A011 식별자 문제, A025 중복 여부
- H1 비교가 각 감사에서 충분했는지
- 최신 실행계획이 evaluator/control 복구보다 새 학습을 앞세우는지

어느 문서의 주장도 권위로 채택하지 말고 원자료로 재판정하라. 다수결을 금지한다.

## 7. Phase III — 최종 산출물

최종 문서를 다음 경로에 저장하라.

`C:\dev\Nconnect\GO2_OPUS_REAUDIT_COMPARISON_260907.md`

문서 첫 화면은 반드시 아래 형식으로 시작한다.

```markdown
## 0. 예선 기준 현재 위치
- [예선 목표] 이번 작업이 확보하려는 배점/시나리오:
- [현재 단계] 단계 N/6 — 이름:
- [확보] 검증 완료:
- [미확보] 다음 단계 차단 항목:
- [이번 테스트] 대상 시나리오와 판정 목적:
- [흐름] 완료 → **현재** → 통과 시 → 실패 시 → 최종 제출
- [지금 할 일] 사용자의 즉시 실행 항목:
- [보장하지 않음] 이번 결과만으로 말할 수 없는 것:
```

최종 문서 목차:

1. **집행 요약** — 핵심 원인 3~7개, 증거 강도, 영향 run
2. **감사 방법과 독립성 봉인** — Phase I SHA256 및 열람 순서
3. **공식형 채점·평가기 계약 진단**
4. **A006~A025 실행별 전수 감사표**
5. **H1 대비 Go2 연속 실패 원인 분석**
6. **실제 정책 실패 / 측정 실패 / 운영 실패 분해**
7. **Codex 감사와 기존 Opus 감사의 쟁점별 대조**
8. **남은 GPU 예산 대비 교정 계획과 fallback**
9. **감사 중 확인 불가능했던 항목**
10. **최종 판정** — 현재 새 학습 승인 여부를 `APPROVE / REQUEST_CHANGES / HOLD — 근거 불충분` 중 하나로 판정

최종 문서 SHA256도 다음 경로에 저장하라.

`C:\dev\Nconnect\GO2_OPUS_REAUDIT_COMPARISON_260907.sha256`

## 8. 품질 게이트

완료 전 다음을 자체 점검하라.

- [ ] A006~A025가 모두 한 번씩 등장하며 미실행·중복은 별도 분류됐다.
- [ ] 모든 핵심 결론에 파일 경로와 줄 번호 또는 JSON pointer가 있다.
- [ ] H1 성공을 공식 결과로 과장하지 않았다.
- [ ] Go2 연속 실패를 reward 실패 하나로 환원하지 않았다.
- [ ] 같은 evaluator 비교와 다른 evaluator 비교를 섞지 않았다.
- [ ] 절대 proxy 개선과 안전 gate 실패를 동시에 기록했다.
- [ ] 실제 정책 붕괴 사례도 계측 문제 뒤에 숨기지 않았다.
- [ ] 공식 결과가 없는 항목은 `[미측정]`이다.
- [ ] 개선 계획이 evaluator 복구·기존 artifact 재판정을 새 GPU 학습보다 앞세운다.
- [ ] 기존 Opus 문서의 폐기된 계획과 최신 계획을 혼동하지 않았다.
- [ ] 최종 문서와 SHA256 파일이 실제로 생성됐다.

## 9. 금지 사항

- 기존 감사 문장을 바꿔 쓰는 방식으로 Phase I를 작성하지 말라.
- 결론에 맞는 사례만 고르지 말라.
- 평균 reward, 한 seed, 한 rollout, 단일 영상만으로 최적·수렴·공식 통과를 선언하지 말라.
- evaluator 결함만으로 모든 candidate를 복권하지 말라.
- 실제 붕괴 사례만으로 evaluator·운영 결함을 무시하지 말라.
- 참가자 수정 허용 범위를 넘는 학습 경로 변경을 개선안으로 제시하지 말라.
- 원자료에 없는 GPU 잔여 시간을 만들어내지 말라.
- 보고서 작성 중 정본 원장이나 학습 코드를 수정하지 말라.

감사의 성공 조건은 어느 기존 문서와 같은 결론을 내는 것이 아니다. **동일한 원자료에서 재현 가능한 판정과, 반증 가능한 인과 설명을 만드는 것**이다.
