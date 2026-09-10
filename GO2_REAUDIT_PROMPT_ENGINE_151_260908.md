# 독립 재감사 프롬프트 — Go2 채점기 engine 1.5.1과 G-A027 실행 계획

작성일: 2026-09-08 · 대상: 다음 감사 AI · 선행 문서: `OPUS_GO2_REAUDIT_PROMPT_260907.md`(1차), `GO2_CODEX_REPAIR_REVIEW_FOR_OPUS_260908.md`(Codex 검토)

이 문서 하나만 읽고도 감사를 시작할 수 있도록 썼다. 이 문서의 주장은 **감사 대상이지 근거가 아니다.**

---

## 0. 예선 기준 현재 위치

- **[예선 목표]** 규정 제10조 — 200점 = H1 100 + Go2 100. 로봇 유형별 최고점만 합산하고 한 라운드에 한 로봇만 제출한다.
- **[현재 단계]** Go2 단계 3/6 — 환경 적응 게이트. H1은 `H1_FROZEN_FOR_SUBMISSION`.
- **[확보]** 채점기 수리(engine 1.5.1)와 Go2 계약 테스트 9종 통과. G-A027 패키지 빌드 완료.
- **[미확보]** Go2 지형 시나리오 가중 0.60의 유효 측정, **잔여 GPU 시간 `[미확인]`**, H1 실제 제출 여부 `[미측정]`.
- **[이번 감사]** engine 1.5.1 수리가 실제로 집행되는지, G-A027 실행 계획이 안전하고 판독 가능한지.
- **[보장하지 않음]** 계약 테스트 통과는 공식 합격이 아니다. 아래 모든 수치는 내부 proxy이며 `OFFICIAL_RESULT_UNMEASURED`다.

---

## 1. 역할과 목표

당신은 이 캠페인 밖의 독립 감사자다. 목표는 세 가지다.

1. **engine 1.5.1이 주장하는 차단이 실제로 집행되는지** 코드와 재현 출력으로 확인한다.
2. **Codex R1~R8에 대한 이번 세션의 처리(수용 7 / 부분수용 1)가 타당한지** 판정한다. 특히 R4를 "사실 주장은 반증됐다"고 처리한 근거를 직접 검증한다.
3. **G-A027을 지금 서버에서 돌려도 되는지** 판정하고, 차단 항목이 있으면 명시한다.

**결론을 이 문서에 맞추지 마라.** 반증이 나오면 그것이 이 감사의 가장 큰 산출물이다.

---

## 2. 증거 규칙

- 모든 판정은 **파일 경로 + 줄 번호**, 또는 **JSON 필드 + 재현 출력**으로 뒷받침한다.
- **문서의 서술을 증거로 인용하지 마라.** 이 문서, `GO2_PROJECT_STATE.md`, Codex 검토서 모두 마찬가지다. 원자료는 `workspace/_keep/**` 아래의 `summary.json`·`tier1_registry.json`·spec JSON과 소스 코드다.
- 각 항목을 **확인 사실 / 해석 / 미확인 / 제안**으로 명시적으로 나눈다. 해석을 확인 사실로 승격하지 마라.
- 판정 어휘는 아래로 고정한다. `PASS`·`합격`·`제출 가능`·`공식 점수` 같은 표현은 금지한다.

| 어휘 | 의미 |
|---|---|
| `ARTIFACT_VERIFIED` | 파일 해시·구조가 확인됨 |
| `VIDEO_OBSERVED` / `VIDEO_UNKNOWN` | 영상을 직접 봤는가 |
| `INTERNAL_GATE_PASS` / `INTERNAL_GATE_FAIL` / `INTERNAL_GATE_INCONCLUSIVE` | 내부 절대 게이트 |
| `INTERNAL_EARLY_KILL_PASS` / `INTERNAL_EARLY_KILL_FAIL` | tier-1 조기기각 게이트 |
| `INTERNAL_MEASUREMENT_INVALID` | 비교 자체가 성립하지 않음 |
| `OFFICIAL_RESULT_UNMEASURED` | 공식 결과 없음 |

- **남은 GPU 시간을 지어내지 마라.** 마지막 원기록은 260903 `GO2_CAMPAIGN_SCHEDULE.md:228` "잔여 25시간"이고 이후 차감 기록이 없다. 현재 값은 `[미확인]`이다.

---

## 3. 배경 — 무엇이 고쳐졌다고 주장되는가

`GO2_PROJECT_STATE.md` §34가 1.5.0 수리를, §35가 Codex 검토 반영과 1.5.1을 기록한다. 요약하면 두 가지 결함이 캠페인을 왜곡했다는 주장이다.

**(가) 정지 정책이 최고 안전 점수를 받았다.** 생존율을 "종료됐는가"로만 정의하면 제자리에 선 정책은 종료되지 않으므로 매 case 1.0을 받는다. 그렇게 만점 안전을 받은 비보행 정책이 기준선이 됐고, 실제로 걷기 시작한 후보는 "생존 후퇴"로 조기 사살됐다.

**(나) 두 arm을 서로 다른 채점기로 쟀다.** 기준선은 구형(termination-only), 후보는 신형(posture gate)으로 잰 비교가 다수였다.

1.5.x는 (가)에 대해 보행 하한(`locomotion` 판정)과 비보행 기준선 거부를, (나)에 대해 계측 지문 대칭 검사를 도입했다고 주장한다.

---

## 4. 1.5.1이 1.5.0에서 바꾼 것 — 이번 감사의 핵심 대상

Codex 검토 R1~R8을 받아 이번 세션이 적용한 변경이다. **각 항목을 독립적으로 검증하라.**

| ID | Codex 지적 | 이번 세션 처리 | 검증 포인트 |
|---|---|---|---|
| R1 | 양쪽 다 지문이 없으면 동일 측정으로 통과 | 수용 — `instrument_unusable()` 신설, 지문 부재·비`posture_gate_v2`·arm 내부 혼재를 각각 차단 | 부재/한쪽 부재/같은 schema 다른 수집기/DR 조건 차이를 실제로 구분하는가 |
| R2 | 무효 비교에서도 delta를 계산·출력 | 수용 — `comparison_blockers()`를 먼저 돌리고, 무효면 delta·시나리오 delta를 `null`로 반환. arm별 자기 수치는 `*_diagnostics`로 분리 보존 | 무효 판정 경로에서 숫자가 어디로도 새지 않는가 |
| R3 | legacy G6·불완전 측정이 tier-1을 우회 | 수용 — `INADMISSIBLE_ARM_STATUS`로 차단. 단 `INTERNAL_GATE_PASS`는 요구하지 않음(요구하면 개선 스크리닝이 막힘) | 측정 유효성과 성능 기준의 분리가 적절한가. 우회 경로가 남는가 |
| R4 | Pilot G1~G6 재사용 동등성 미증명 | **부분수용** — 구조는 수용(telemetry `schema_version` 2→3, `measurement_contract` 필드 신설). 사실 주장은 반증했다고 판단. 그럼에도 **Pilot-01 69건 전량 재측정으로 변경** | §5.1 필수 재검증 |
| R5 | 실패를 채점 결함 하나로 환원하지 말 것 | 수용 — A015/A016/A018의 실제 성능 저하는 그대로 남는다고 기록 | 서술이 실제로 분리됐는가 |
| R6 | 11건 표를 12전과 비교, A010 사유 오기, legacy gates 임의 대입 | 수용 — 표 서술 정정, `migrate_gates()`가 대입값·출처를 `gate_migration`에 기록 | 대입값이 판정을 바꾸는가(§5.2) |
| R7 | 제출 승급 조건이 registry와 불일치 | 수용 — 판독을 Q1(스크리닝)·Q2(제출)로 분리, Q2는 registry `score.internal_gates`만 사용 | §5.3 |
| R8 | 시간·회수 안전성 과장 | 수용 — 재실행 시 기존 결과 파괴 금지, resume 지문에 `EVAL_STEPS`·evaluator SHA 추가, 영상도 지문 판정, `[NO_DEADLINE]` 명시 | 코드로 보장되는가, 문자열 존재 확인에 그치지 않는가 |

---

## 5. 반드시 독립 검증할 5개 주장

이번 세션이 **원자료로 확인했다고 주장하는 것들**이다. 하나라도 반증되면 계획이 바뀐다.

### 5.1 R4 반증 주장 — "OR→AND 변경은 기존 자료에 무연산이다"

주장: 저장된 Pilot-01 69건과 A017 양 arm 14건 전부에서 높이 채널이 실측이므로(`height_rel_mean` null 0건), 자세 측정을 OR에서 AND로 바꿔도 바뀌는 case가 없다. 또 `NCRC_EVAL_DR`이 환경에 설정된 적이 없다는 것은 `dr_seed_*`가 `rough_forward`와 byte-identical한 steps.csv를 냈다는 사실(G-F168)로 증명된다.

```bash
python -c "
import json,glob
n=b=0
for f in glob.glob('workspace/_keep/go2_pilot_v2_baseline/evaluation/pilot_v2/cases/*/*/summary.json'):
    d=json.load(open(f,encoding='utf-8')); n+=1
    if d.get('height_rel_mean') is None: b+=1
print(n,'cases,',b,'with a dead height channel')"
```

**따져볼 것:** `height_rel_mean`이 집계값인데 이것으로 per-step·per-env 채널 생존을 증명할 수 있는가? `posture_measured`, `steps.csv`의 `height_rel`·`upright` 열까지 봐야 하지 않는가? 이번 세션은 이 논증이 성립한다고 보면서도 **전량 재측정으로 대체**했다 — 그 판단이 과잉인지 적정인지도 답하라(추가 GPU 약 30분).

### 5.2 A017 통과가 대입 게이트에 의존하지 않는다는 주장

주장: A017의 최악 시나리오 곱 delta는 −0.006756(G6)이고 대입된 한계는 0.1이므로, 0.007 이상 어떤 한계값에서도 `INTERNAL_EARLY_KILL_PASS`가 유지된다.

```bash
python -c "
import sys,json; from pathlib import Path
sys.path.insert(0,'workspace/training/quadruped')
from go2_fixed_eval_report import build_policy
from go2_tuning_eval_report import tier1_decision
K=Path('workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140'); reg=K/'meta'/'tier1_registry.json'
b=build_policy(K/'evaluation'/'baseline_tier1',reg,{}); c=build_policy(K/'evaluation'/'candidate',reg,{})
g=json.loads((K/'meta'/'G_A017_pilot_track_lin_vel_xy_140.json').read_text(encoding='utf-8'))['evaluation']['gates']
d=tier1_decision(b,c,g)
print(d['status'], d['candidate_minus_baseline_points_70'], d['worst_scenario_proxy_delta'], d['scenario_proxy_regression_limit'])
print(json.dumps(d['gate_migration'],ensure_ascii=False))"
```

**따져볼 것:** `min_total_points_delta` 대입값(0.0)도 판정을 바꾸지 않는가? A010·A013처럼 이 키가 없는 spec에서 대입이 결과를 만들어내지 않는가?

### 5.3 두 정책 모두 절대 게이트 불합격이라는 주장

주장: tier-1 실측에서 A017 후보와 Pilot-01 **둘 다** `INTERNAL_GATE_FAIL`이며, 사유는 G3·G4·G5·G7의 추종 proxy가 registry 하한 0.70에 미달하기 때문이다. 따라서 G-A027의 예상 결과는 **상대 개선 + 절대 불합격**이다.

**따져볼 것:** registry의 어느 기준이 스크리닝에, 어느 기준이 최종 승급에 적용되는가가 정합적으로 명시됐는가? 영상 근거와 문서 감사 점수(20+10점)는 어디서 판정되는가? 이 실행이 Q2를 답할 수 없다면, Q2를 답하려면 무엇이 더 필요한가?

### 5.4 차단 7건의 사유 분해

주장: 1.5.1은 네 가지 독립 사유를 구분하며, A010은 3개, 나머지 6건은 4개 전부에 걸린다.

```bash
python -c "
import sys,re; from pathlib import Path
sys.path.insert(0,'workspace/training/quadruped')
from go2_fixed_eval_report import build_policy
from go2_tuning_eval_report import comparison_blockers
for K in sorted(Path('workspace/_keep').glob('go2_g_a0*')):
    reg=K/'meta'/'tier1_registry.json'
    if not reg.is_file() or not list(K.glob('meta/G_A0*.json')): continue
    b=build_policy(K/'evaluation'/'baseline_tier1',reg,{}); c=build_policy(K/'evaluation'/'candidate',reg,{})
    print('G-A'+re.search(r'g_a(\\d+)',K.name).group(1), comparison_blockers(b,c) or 'comparable')"
```

**특히 확인할 것:** A013 기준선 arm의 `telemetry_schema_versions`가 `['1','2']`라는 주장 — **하나의 arm 안에서 69 case가 서로 다른 세대의 채점기로 측정됐다**는 뜻이다. 사실이면 1.5.0까지 이 상태를 볼 수 있는 검사가 없었다는 것도 확인하라.

### 5.5 A017을 "정지 기준선 함정"의 사례로 설명하면 안 된다는 Codex 지적

A017의 기준선은 **보행하는** Pilot-01이다. 그러므로 A017의 오판정은 (가) 정지 기준선 문제의 직접 사례가 아니라, **생존 인자 단독 조기기각 조항**의 사례다. 이번 세션의 서술이 이 둘을 섞고 있지 않은지 확인하라. 또 A015·A016·A018의 −30 ~ −46/70은 같은 측정 조건에서도 남는 **실제 성능 저하**다.

---

## 6. 읽을 파일과 문서화 시점 해시

해시는 무손상·버전 식별용이며 policy tensor 동등성 증거가 아니다. **먼저 현재 해시를 아래와 대조하고, 다르면 "검토 시점 결함"과 "이후 수정으로 해소됨"을 분리하라.**

`Q/` = `workspace/training/quadruped/`

### 수리 대상 코드

| 파일 | SHA256 | Codex 검토 시점 대비 |
|---|---|---|
| `Q/go2_fixed_eval_report.py` | `2d74e585f8ae2b676e0167684300fd4b2c8417f5d6e1d1034dccd96bc9083791` | 변경됨 (`a022557b…`) |
| `Q/go2_tuning_eval_report.py` | `cacb87ed6fc2f763972339f010b3dd11906558a611713860b8e7855266dbe94c` | 변경됨 (`b09e5307…`) |
| `Q/go2_eval_telemetry.py` | `d801d9910f2bc920570736c9e26c276f0d7b657dcc38dd5d077cf828468c78ce` | 변경됨 (`34edd178…`) |
| `Q/go2_tuning_config.py` | `1a0eeeaef7576fceb398f357e1702981489c83da5ebeaa62eb1897e246a43218` | — |
| `Q/config/go2_self_eval_registry.json` | `8d8c34caf66813e2c18070fb9a85ed7c843c379cb3a5ffb3d0a73923b9349ba6` | 변경 없음 |
| `Q/config/go2_tuning_experiment_schema.json` | `75f0743e54e607a7539c281baefab1e739ff50950774e138766661649a7e3523` | — |

### G-A027 실행 패키지

| 파일 | SHA256 |
|---|---|
| `Q/go2_a017_full_suite.zip` | `8d97fc1b1963524dbb402e383ce6c878dc61eed8fe5bd0ce39bc7f45b79ffb93` |
| `Q/server_run_go2_a017_full_suite.sh` | `5e813d49106a8eecc76231a00416c64b4949b5cf4ce6289259e6bfd1604ec390` |
| `tools/build_go2_a017_full_suite_package.py` | `650d96f6266844aa251a1f9b1df2293d3a3a51da5d22396fe30fa98ff1b78ba8` |

업로드 정본은 `Q/upload/G-A027/current/`이며 zip은 위와 동일 해시다.

### 계약 테스트

| 파일 | SHA256 |
|---|---|
| `tools/test_go2_scoring_repair_contract.py` | `c04bcb917d0ea91b46b5ba1e8f7f4e154a7c603367f7b461c7d58fa140497efa` |
| `tools/test_go2_a017_full_suite_contract.py` | `aa91bffb86c333a17b86e86c09106e4bac96787761c09d08e734e5a3d5005965` |
| `tools/test_go2_tuning_engine_contract.py` | `b4f1524967c64df6d0451cc1d616d8f9a4a8863256356a884f33d0bfdf29af6f` |
| `tools/test_go2_posture_survival_contract.py` | `cd48f95586296e2b541bb8593c651289c71af6a73d0959664a893f4453f00f55` |
| `tools/test_go2_default_vs_pilot_contract.py` | `d612c31d1b5aff1afcd45ea743d1b9511962db8f924745561412c97551bd5c1c` |

### 원장·런북·선행 감사

| 파일 | SHA256 |
|---|---|
| `GO2_PROJECT_STATE.md` (§34, §35) | `468f98180f0f7f96dac4fadf017dd01f6536733c8c61d7a6a66b602fe7ddeb49` |
| `SERVER_SESSION_RUNBOOK.md` (G-A027 절) | `7fcad69d5a7ad5215ab032f899f99489a62ff0672c0c7a48ecdd5912c7108c4f` |
| `GO2_CODEX_REPAIR_REVIEW_FOR_OPUS_260908.md` | `4e6d7102a64961c99a99f12fa2a69522102f93e6d1c296d27fec3f815ee666e6` |

### 원자료

- `workspace/_keep/go2_pilot_v2_baseline/` — Pilot-01 69 case × 3 seed
- `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/` — A017 양 arm tier-1 + 학습 아티팩트
- `workspace/_keep/go2_g_a0{10,13,15,16,18,20,21,22,24,25}*/` — 나머지 재판정 대상
- 각 폴더의 `meta/tier1_registry.json`, `meta/G_A0*.json`, `evaluation/{baseline_tier1,candidate}/cases/*/*/summary.json`

### 규정·불변식 (해석 시 반드시 반영)

- 예선 규정집 제2·4·8·10·14조 — 특히 제14조 "제출된 정책 파일과 설정(env.yaml)은 대회 서버에 기록된 학습 이력과 대조할 수 있다"
- `Q/quadruped_rewards.py` 상단 주석 및 `Q/README.md:19` — 수정 허용 범위
- `AGENTS.md:250` — H1 결론을 Go2에 사실처럼 복사 금지
- `SERVER_SESSION_RUNBOOK.md` — 대회 서버는 접속마다 초기화되는 휘발성 환경

---

## 7. 실행 준비 상태 판정 — G-A027

패키지는 **학습을 하지 않는다.** 동결된 두 정책(A017 후보, Pilot-01)을 각각 69 case-run(23 case × seed 101/202/303) 재생하고 영상 7건을 남긴다. 추정 1시간 45분이며 **강제 상한이 아니다.**

다음을 코드로 확인하고 각각 판정하라.

1. 학습 진입점이 실제로 없는가 (`train.py` 참조가 동시성 가드뿐인가).
2. 정책 SHA 불일치 시 중단하는가.
3. 모든 case가 `posture_gate_v2` 근거를 요구하는가, 없으면 해당 case가 실패하는가.
4. 기본 재실행이 회수 전 결과를 파괴하지 않는가 (`GO2_DISCARD_PREVIOUS` 게이트).
5. resume이 파일 존재가 아니라 지문 일치로 판정하는가 — 서로 다른 설정을 같은 결과로 건너뛰지 않는가. **음성 회귀 테스트로 확인하라.**
6. 두 arm이 같은 evaluator 바이너리로 측정되는가 (`EVALUATOR_SHA`가 결과에 기록되는가).
7. 실패 시 부분 회수(`package_result PARTIAL`)가 동작하는가.

**서버 실행 전 필수 선행 조건 두 가지도 판정에 포함하라.**

- **잔여 GPU 시간 실측.** 현재 `[미확인]`이고 이 실행은 1시간 45분을 요구한다.
- **학습 이력 자동 백업을 껐던 과거 실행이 제출 자격에 영향을 주는지.** 과거 러너가 `NO_AUTO_SUBMIT`를 하드코딩해 운영진 학습 이력 백업을 끈 채로 학습했다. 규정 제14조가 대조 가능성을 명시하므로 운영진 확인이 필요하다. 확인 비용 0, 최악의 경우 손실 전부.

---

## 8. 품질 게이트

산출물이 아래를 만족하지 않으면 미완성이다.

- R1~R8 각각에 **수용 / 부분수용 / 반증 / 미확인** 판정과 원자료 근거가 있다.
- §5의 5개 주장 각각에 독립 재현 출력이 있다.
- 확인 사실 / 해석 / 미확인 / 제안이 문장 단위로 구분돼 있다.
- 계약 테스트 통과를 공식 합격으로 번역하지 않았다.
- 남은 GPU 시간을 추정하지 않았다.
- 서버 실행 준비 여부와 **차단 항목 목록**이 마지막에 있다.

---

## 9. 금지 사항

- 승인되지 않은 GPU 실행, 제출, 기존 artifact 삭제·덮어쓰기.
- `quadruped_rewards.py` 외 참가자 수정 금지 파일 변경.
- H1의 시나리오·임계값·학습 단가·reward 결론을 Go2에 사실처럼 전용.
- 이 문서·원장·Codex 검토서의 서술을 증거로 인용.
- `PASS` / `합격` / `제출 가능` / `공식 점수` 표현 사용.
- 검증 단계와 구현 단계를 섞기 — 구현한다면 변경 목록·부정 회귀 테스트·실행 출력을 분리해 남긴다.

---

## 10. 산출물

루트에 `GO2_REAUDIT_RESPONSE_ENGINE_151_260908.md`로 작성한다.

**표 1 — R1~R8 판정**: `ID / 판정 / 원자료(경로+줄 또는 필드) / 재현 출력 / 이번 세션 수정의 적절성 / 남은 위험`

**표 2 — §5의 5개 주장 검증**: `주장 / 판정 / 재현 / 반증 시 계획에 미치는 영향`

**마지막 절 — 실행 준비 판정**: `INTERNAL_GATE_PASS`/`FAIL`/`INCONCLUSIVE` 어휘로 서버 실행 준비 여부, 그리고 차단 항목을 우선순위대로.
