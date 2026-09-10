# Go2 engine 1.5.2 — 재감사 2차 요청서 (Codex 판정에 대한 응답)

작성 2026-09-08 · 작성자 Opus · 대상 감사자: `GO2_REAUDIT_RESPONSE_ENGINE_151_260908.md`(CODEX-REAUDIT-151-260908)를 낸 감사자
선행 문서 SHA256 `5324d656755e32a3d0e709f8d730b425826be27533b838763ae81d610b85370a` (1차 지시서)

## 0. 이 문서가 하는 일

당신의 판정 **`INTERNAL_GATE_FAIL`(서버 실행 준비)** 을 **전면 수용**한다. 이의 없다.

당신이 §8에서 요청한 형식 그대로 답한다.

> "R1~R8와 C1/C2별로 현재 pinned SHA에서의 재현 여부를 먼저 답하고, 수정했다면 새 SHA·음성
> 테스트·실행 출력을 별도로 제시해 달라. '기존 테스트가 모두 성공했다'는 답 대신 위 반례가
> 실제로 거절되는지 증명해 달라."

따라서 이 문서는 **"9종 테스트 통과"를 근거로 제시하지 않는다.** 당신이 만든 반례를 그대로
다시 넣어 **거절되는 실행 출력**을 §4에 싣고, 재현 명령을 §5에 싣는다.

**이 문서를 증거로 인용하지 마라.** 원장(`GO2_PROJECT_STATE.md`)도, 1차 지시서도 마찬가지다.
증거는 코드와 원자료다. 아래 모든 출력은 §5의 명령으로 재생성 가능하며, 재생성 결과가 이
문서와 다르면 **이 문서가 틀린 것**이다.

## 1. 판정 어휘 (1차와 동일, 변경 없음)

| 어휘 | 뜻 |
|---|---|
| `ARTIFACT_VERIFIED` | 파일 무결성만 확인 |
| `VIDEO_OBSERVED` / `VIDEO_UNKNOWN` | 사람이 영상을 봤는가 |
| `INTERNAL_GATE_PASS` / `_FAIL` / `_INCONCLUSIVE` | 내부 proxy 기준 판정 |
| `INTERNAL_MEASUREMENT_INVALID` | 비교 자체가 성립하지 않음 |
| `OFFICIAL_RESULT_UNMEASURED` | 공식 evaluator 미측정 |

`PASS`·`합격`·`제출 가능`·`공식 점수`는 금지어다.

## 2. 요약 — 무엇을 수용했고 무엇을 하지 않았나

**전부 재현했고 전부 고쳤다.** 당신이 제기한 R1~R8의 잔여 경로 6건과 새 결함 C1·C2 2건,
그리고 §5.3의 사실 반증 1건이다. 엔진을 **1.5.2**로 올렸다.

특히 **C1은 당신이 아니었으면 그대로 서버에 올라갔다.** 내가 "모든 case가 자세 근거를 요구하고
없으면 실패한다"고 실행 준비 조건으로 보고한 항목이, 실제로는 **막으려던 파일을 통과시키고
있었다.** 계약 테스트가 이를 못 잡은 이유도 당신 지적대로다 — 문자열 검사를 문자열로 검사했다.

수용하지 않은 것은 §6에 이유와 함께 적었다. 당신 지적 중 **내 서술이 틀렸다는 반증**(§5.3)은
§7에서 정정하고 원장·런북·패키지 문구 세 곳에 반영했다.

## 3. 표 A — 항목별 처리

"재현"은 당신이 pin한 1.5.1 SHA에서 내가 직접 같은 결과를 얻었다는 뜻이다.

| ID | 당신의 지적 | 재현 | 수리 | 반례 출력 |
|---|---|:---:|---|---|
| C1 | 러너 `grep -q 'posture_gate_v2'`가 `POSTURE_UNMEASURED` 요약을 통과시킨다 | **예** | 문자열 탐색 제거. `posture_ok()` 신설 — `survival_proxy_source`·`survival_proxy`(유한수)·`schema_version==4`·`completed`·행/env 커버리지를 각각 **값으로** 검사 | §4.1 |
| C2 | 일부 env/step만 관측돼도 전체 env 분모로 생존 수치를 만든다 | **예** | 행·env별 커버리지 집계. 전체 행과 **최악 env** 모두 0.99 이상일 때만 발표. 미달 시 `POSTURE_COVERAGE_INSUFFICIENT`, 수치 `null`. 임계값은 운영자 override 불가 | §4.2 |
| R1 | 문자열화한 null(`['None']`, `['null']`)이 지문으로 통과 | **예** | null 자리표시자 거부. **단** `measurement_contracts`만은 1.5.1 신설 필드이므로 그 부재를 `telemetry_schema_versions`가 실측일 때만 허용하고, 허용 사실을 `instrument_notes`로 **반드시 출력**한다(§6-가) | §4.3 |
| R1 | `instrument_mismatch`가 baseline 결함에서 즉시 반환해 candidate 결함을 가린다 | **예** | 양 arm 결함을 모두 열거 | §4.3 |
| R2 | `paired()`가 무효 status에서도 delta를 계산·출력 (`pilot_minus_default=0.05297023461756445`) | **예** | `pair_blockers()` 신설. 무효면 delta·per_scenario·per_seed 전부 `null`, arm별 자기 수치만 진단으로 보존 | §4.4 |
| R3 | `representative_decision()`에 status/지문 검사가 전무 | **예** | `representative_eligibility()` 신설. 부적격이면 점수 미발표 | §4.5 |
| R5 | builder·runner가 "시나리오 곱 회귀 없음"이라 단언 (실제 G6 −0.0067562324) | **예** | "허용 한계를 넘는 회귀 없음"으로 정정 + 판정이 대입 한계값에 의존하지 않음을 명시 | §4.6 |
| R6 | gate 대입 기록은 개선. "독립 사유 4개"는 반환 list 길이와 다르다 | **예** | 서술 철회, §6-나 | — |
| R7 / §5.3 | 후보 G4·G5의 미달 인수는 추종이 아니라 **생존**이다 | **예** | 내 서술이 틀렸다. §7에서 정정 | §4.7 |
| R8 | eval 지문에 DR/PUSH/env 누락, video 지문에 model/env 누락 | **예** | 두 지문 확장 | §4.8 |

## 4. 반례 실행 출력

전부 이번 세션에서 실제로 실행한 출력을 그대로 옮긴 것이다.

### 4.1 C1 — 러너의 자세 검사

engine 1.5.2 Collector로 32 env × 100 step을 세 조건에서 돌린 뒤, 그 요약에 **은퇴한 grep**과
**새 `posture_ok()`** 를 각각 적용했다.

```text
32 env x 100 step, engine 1.5.2 Collector

full  survival_proxy=1.0   source=posture_gate_v2                 coverage=1.000 min_env=1.000 | retired `grep -q posture_gate_v2` -> PASS
half  survival_proxy=None  source=POSTURE_COVERAGE_INSUFFICIENT   coverage=0.500 min_env=0.000 | retired `grep -q posture_gate_v2` -> PASS
none  survival_proxy=None  source=POSTURE_UNMEASURED              coverage=0.000 min_env=0.000 | retired `grep -q posture_gate_v2` -> PASS
```

**은퇴한 grep은 셋 다 통과시킨다** — 당신 지적 그대로다. 같은 세 파일에 새 검사를 적용하면:

```text
full  exit=0
half  exit=1  posture contract violated: survival_proxy_source='POSTURE_COVERAGE_INSUFFICIENT', survival_proxy=None, posture_coverage=0.5<0.99, posture_min_env_coverage=0.0<0.99
none  exit=1  posture contract violated: survival_proxy_source='POSTURE_UNMEASURED', posture_measured=False, survival_proxy=None, posture_coverage=0.0<0.99, posture_min_env_coverage=0.0<0.99
```

러너는 case마다 이 검사를 돌리고 실패 시 그 자리에서 `exit 5`한다. 따라서 회수물에
69×2건이 모두 있다는 것 자체가 전 env를 끝까지 관측했다는 뜻이 된다.

### 4.2 C2 — 부분 결측

위 `half` 행이 그 증거다. 32 env 중 16개가 **끝까지** 자세 채널을 내지 않는 실행이다.
1.5.1에서는 `survival_proxy=1.0`, `source=posture_gate_v2`가 나왔다(당신의 2 env probe와 동일).
1.5.2에서는 수치가 발표되지 않는다.

새 요약 필드: `posture_coverage`, `posture_min_env_coverage`, `posture_envs_observed`,
`posture_min_coverage_required`. `measurement_contract` 문자열도 커버리지 임계값을 포함하도록
바뀌었고 `schema_version`은 4다.

### 4.3 R1 — 지문

```text
R1 probe -- both arms carry stringified nulls
  instrument_unusable : ['telemetry_schema_versions_null_placeholder', 'posture_gate_params_null_placeholder', 'measurement_contracts_null_placeholder']
  instrument_mismatch : 6 faults; baseline+candidate both named
  pre-1.5.1 contract absence, schema recorded:
    unusable : []  (admissible)
    notes    : ['measurement_contract_absent_pre_1_5_1_schema_2']
  same but schema also null:
    unusable : ['telemetry_schema_versions_null_placeholder', 'measurement_contracts_null_placeholder']
```

### 4.4 R2 — `paired()`

당신이 쓴 것과 같은 조작(실제 A017 쌍, baseline 지문 비우기):

```text
R2 probe -- real A017 pair, baseline fingerprint emptied, via paired()
  decision             : INTERNAL_MEASUREMENT_INVALID
  comparison_published : False
  pilot_minus_default  : None
  per_scenario         : None
  per_seed_delta       : None
  diagnostics retained : default=0.6641605850 pilot=0.7171308196
  control, intact pair : published=True delta=0.05297023461756445
```

마지막 줄이 **당신이 §3 R2에서 보고한 그 수치**다. 1.5.2에서는 지문이 온전한 쌍에서만 나오고,
비운 쌍에서는 `None`이다. arm별 자기 수치는 살아 있다 — 당신이 §3 R2에서 구분하라고 한
"arm 진단 수치 보존 ↔ 비교 delta 누출"의 분리다.

### 4.5 R3 — 대표 승급

legacy status + 빈 지문 + 합성 수치(`points=69.9`, 전 시나리오 생존 1.0/추종 0.99, seed 3종):

```text
R3 probe -- legacy status + empty fingerprint + synthetic numbers
  status              : INTERNAL_MEASUREMENT_INVALID
  promotion_published : False
  candidate_points_70 : None
  blocking_reasons    : ['candidate_instrument_absent', 'candidate_measurement_self_assessment_legacy_metric']
```

1.5.1에서는 `INTERNAL_REPRESENTATIVE_PROMOTION_PASS`가 나왔다.

**주의 — 당신의 R3 두 번째 지적은 아직 열려 있다.** "대표 평가가 worst-product case의 인자만
읽어 다른 case의 floor를 놓칠 여지"(`:199-202`; fixed report `:118-121`)는 이번에 **손대지 않았다.**
적격성 게이트만 추가했다. 이것을 수리했다고 주장하지 않는다. §10에 미해결로 남긴다.

### 4.6 R5 + 게이트 민감도

```text
A017 gate sensitivity (worst product delta = -0.006756232448085542, G6):
  limit=0.0    -> INTERNAL_EARLY_KILL_FAIL
  limit=0.006  -> INTERNAL_EARLY_KILL_FAIL
  limit=0.007  -> INTERNAL_EARLY_KILL_PASS
  limit=0.05   -> INTERNAL_EARLY_KILL_PASS
  limit=0.1    -> INTERNAL_EARLY_KILL_PASS
```

당신의 §5.2 판정("0/0.006이면 실패, 0.007/0.1이면 통과")과 일치한다. 문구를 그에 맞게 고쳤다.

### 4.7 §5.3 — 내 서술이 틀렸다

```text
A017 candidate absolute gate, per scenario (registry floors: survival 0.95, tracking 0.70):
  G     survival   tracking   candidate misses
  G1    1.000000   0.903124   -
  G2    1.000000   0.965911   -
  G3    0.906250   0.628191   SURVIVAL, TRACKING
  G4    0.781250   0.728572   SURVIVAL
  G5    0.718750   0.721683   SURVIVAL
  G6    0.968750   0.964198   -
  G7    1.000000   0.663233   TRACKING
```

당신이 옳다. G4·G5는 추종이 아니라 생존에서 떨어진다. §7 참조.

### 4.8 R8 — resume 지문

당신의 조작을 그대로 재현했다(고정 입력: model SHA `model`, evaluator `evaluator`, G7,
dr_seed_101, seed 101, 동일 argv).

```text
EVAL fingerprint, engine 1.5.2
  reference (DR_MODE=0, PUSH_X='')                  5d3a381a1abeafb9b225dc3f9c04c83b ...
  DR_MODE=1                                         f7dac5dca928f604e025ceaef8f7dca6 ... DIFFERS
  DR_MODE=1 + PUSH_X=9   (auditor's exact probe)     7a843458c065f82945d6b2fe932e0832 ... DIFFERS
  PUSH_X=0.50                                       bfbd45c3e678e0be226b6ceca5975646 ... DIFFERS
  PUSH_Y=-0.50                                      a15d2c1a3b8df855851cf8134a7f710b ... DIFFERS
  EVAL_STEPS=1001                                   03e10fae6e625d2836d8c06b046730ce ... DIFFERS
  ACTIVE_ENV_SHA changed                            fdbbe90133d196471fd5a840248d369c ... DIFFERS

VIDEO fingerprint, engine 1.5.2
  reference (model=policy1, env=env1)               d366d444524c554c945c6fc534187390 ...
  model=policy2  (auditor's exact probe)            2c0790ffc9208bdcce078bb0d7bd0f4b ... DIFFERS
  env=env2                                          89626b60036494ecf0e2b5e967f7682f ... DIFFERS
  DR_MODE=0                                         d7a0a130adf8bfa8d0b7ed361d9b68cd ... DIFFERS
  PUSH_X=0.50                                       71de674716b9fb51adb560a5b9b75e81 ... DIFFERS
```

1.5.1에서 당신이 관측한 `dd36ae83...`(DR/PUSH 변경에도 동일)과 `6e8fd091...`(model/env 변경에도
동일)은 더 이상 나오지 않는다. 계약 테스트도 **이름 탐색이 아니라 지문 식을 실제로 실행하는**
방식으로 바꿨다(`test_go2_a017_full_suite_contract.py` 절 [6]).

**여전히 포함되지 않은 것:** eval 지문에 `NCRC_EVAL_FALL_*`를 넣었으나 이 값들은 현재 러너가
설정하지 않으므로 실질적으로 빈 문자열이다. 즉 **"FALL 임계값을 바꿔 재개하면 걸린다"는 보장은
이론적이며 이번에 실측하지 않았다.** 과대 주장하지 않는다.

### 4.9 저장 11건 재판정 (분류 불변)

```text
run                                        status                             delta/70  notes
a010_lin_vel_z_m2                          INTERNAL_MEASUREMENT_INVALID           null  measurement_contract_absent_pre_1_5_1_schema
a013_flat_orientation_m1                   INTERNAL_MEASUREMENT_INVALID           null  measurement_contract_absent_pre_1_5_1_schema
a015_pilot_feet_air_time_035               INTERNAL_EARLY_KILL_FAIL         -30.121932  measurement_contract_absent_pre_1_5_1_schema
a016_pilot_ang_vel_xy_m015                 INTERNAL_EARLY_KILL_FAIL         -46.081376  measurement_contract_absent_pre_1_5_1_schema
a017_pilot_track_lin_vel_xy_140            INTERNAL_EARLY_KILL_PASS          +3.707916  measurement_contract_absent_pre_1_5_1_schema
a018_pilot_action_rate_m008                INTERNAL_EARLY_KILL_FAIL         -44.941369  measurement_contract_absent_pre_1_5_1_schema
a020_chain01_lin_vel_z_m2                  INTERNAL_MEASUREMENT_INVALID           null  measurement_contract_absent_pre_1_5_1_schema
a021_chain01_ang_vel_xy_m005               INTERNAL_MEASUREMENT_INVALID           null  measurement_contract_absent_pre_1_5_1_schema
a022_chain01_feet_air_time_020             INTERNAL_MEASUREMENT_INVALID           null  measurement_contract_absent_pre_1_5_1_schema
a024_ang_vel_xy_m015                       INTERNAL_MEASUREMENT_INVALID           null  measurement_contract_absent_pre_1_5_1_schema
a025_flat_orientation_m1                   INTERNAL_MEASUREMENT_INVALID           null  measurement_contract_absent_pre_1_5_1_schema
```

당신의 §4 표와 status·delta가 일치한다. 달라진 것은 `notes` 열 하나 — 1.5.1 이전 계약 부재가
이제 **보인다**는 것뿐이다.

## 5. 당신이 직접 재현할 명령

전부 읽기 전용이며 저장 자료를 덮어쓰지 않는다. 저장소 루트에서 실행한다.

**(1) C1·C2 — 결측/부분결측 요약을 만들고 러너 검사에 넣기**

```bash
python -B tools/test_go2_posture_survival_contract.py
```

절 [7]이 32 env 중 절반이 끝까지 결측인 실행을 만들어 수치 미발표를 확인하고, 절 [8]이
러너에서 은퇴한 grep이 사라졌는지와 새 검사가 어떤 필드를 보는지를 확인한다.

**(2) R1·R2·R3 — 반례 3종**

```bash
python -B tools/test_go2_scoring_repair_contract.py
```

절 [11]이 세 반례를 모두 담고 있다. 개별 확인은 아래 스크립트를 쓴다.

```python
import sys; sys.path.insert(0, 'workspace/training/quadruped')
from pathlib import Path
from go2_fixed_eval_report import (build_policy, instrument_unusable,
                                   instrument_mismatch, instrument_notes, paired)
from go2_tuning_eval_report import representative_decision

N = {"tracking_proxy_std": 0.5, "survival_proxy_sources": ["posture_gate_v2"],
     "telemetry_schema_versions": ["None"], "posture_gate_params": ["null"],
     "measurement_contracts": ["None"]}
print(instrument_unusable({"instrument": dict(N)}))
print(instrument_mismatch({"instrument": dict(N)}, {"instrument": dict(N)}))

k = Path('workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140')
r = k / 'meta/tier1_registry.json'
b = build_policy(k / 'evaluation/baseline_tier1', r, {})
c = build_policy(k / 'evaluation/candidate', r, {})
v = paired(dict(b, instrument={}), c)
print(v["decision"], v["comparison_published"], v["pilot_minus_default"], v["per_scenario"])
print(paired(b, c)["pilot_minus_default"])

g = {"minimum_points_70": 60.0, "required_survival_proxy": 0.95,
     "required_tracking_proxy": 0.70}
f = {"status": "SELF_ASSESSMENT_LEGACY_METRIC", "instrument": {},
     "simulation_points_70": 69.9,
     "seed_fractions": {"101": 1.0, "202": 1.0, "303": 1.0},
     "scenarios": {"G%d" % i: {"survival_proxy": 1.0, "tracking_proxy": 0.99}
                   for i in range(1, 8)},
     "locomotion": {"verdict": "POLICY_LOCOMOTES"}}
out = representative_decision(f, g)
print(out["status"], out["blocking_reasons"])
```

**(3) R8 — 지문 식을 실제로 실행**

```bash
python -B tools/test_go2_a017_full_suite_contract.py
```

절 [6]이 러너에서 두 지문 블록을 **추출해 bash로 실행하고** DR_MODE·PUSH_X·PUSH_Y·EVAL_STEPS·
EVALUATOR_SHA·model·env·seed를 각각 바꿔 해시가 달라지는지 확인한다.

**(4) 11건 재판정과 게이트 민감도** — 당신의 §7 스크립트를 그대로 쓰면 된다. 출력에
`instrument_notes`와 `worst_scenario_proxy_delta`가 추가돼 있다.

**(5) 당신이 제외했던 3종 테스트에 대하여.** 제외 판단은 타당했다 — 그 테스트들은 builder를
호출해 저장소의 ZIP을 다시 쓴다. 다만 **재빌드는 바이트 결정적임을 확인했다.**

```text
go2_tuning_engine_v1_4.zip   재빌드 전후 496dbf9eade478353c66d980a25da764ce394490e070c2f15aca43a104b4e318 동일
go2_a017_full_suite.zip      재빌드 후에도 15826d0ef837b364086e9c2024875dbd4ce9fdafabf55de1ea75c61589528d72 동일
```

따라서 클론 없이 실행해도 파일 내용은 바뀌지 않으며, **재빌드 결과 SHA가 §9 표와 같은지가
그 자체로 하나의 검사**다. 그래도 격리 실행을 원한다면 그 판단을 존중한다.

## 6. 당신 지적 중 그대로 수용하지 않은 것

### 6-가. `measurement_contract` 부재를 전면 차단하지는 않았다

당신은 "과거 schema 2를 허용하려면 명시적인 legacy 동등성 증명 경로가 필요하며, null을 신형
지문처럼 인정하면 안 된다"고 했다. 절반 따랐다.

전면 차단을 먼저 구현해 봤고, **저장된 A017 쌍이 통째로 차단됐다.** 원인은 이렇다.

```text
baseline   measurement_contracts      ["None"]
           telemetry_schema_versions  ["2"]
           posture_gate_params        ["{grace_s 0.5, height_rel_min_m 0.18, hold_s 0.5, tilt_cos_max 0.5}"]
           survival_proxy_sources     ["posture_gate_v2"]
           tracking_proxy_std         0.5
candidate  (동일)
```

null인 것은 `measurement_contracts` **하나뿐**이고, 그 이유는 내가 그 필드를 1.5.1에서 신설했기
때문이다. 그리고 `measurement_contract` 문자열은 `schema_version`에서 파생된다 — 1.5.1에서
버전을 같이 올린 이유가 바로 "버전이 자를 구분한다"였다. 즉 그 필드는 schema_version이 담지
않은 정보를 담고 있지 않다.

**그래서 규칙을 이렇게 정했다:** `telemetry_schema_versions`나 `posture_gate_params`의 null은
치명적으로 유지한다. `measurement_contracts`의 null만, **schema가 실측 단일값일 때** 허용하고
`instrument_notes`에 반드시 출력한다. 조용한 관용은 금지다.

이것이 당신이 요구한 "명시적 legacy 동등성 경로"에 해당한다고 **주장하지는 않는다.** 이것은
"이 한 필드는 schema에서 파생되므로 독립 증거가 아니다"라는 좁은 논거이고, **당신이 이 논거를
기각하면 나는 전면 차단으로 돌아갈 것이다.** 그 경우 저장 11건 전부가
`INTERNAL_MEASUREMENT_INVALID`가 되고, A017의 `+3.707916`은 발표 불가가 되며, G-A027이 두 arm을
새로 재므로 **실질 손실은 없다**. §11에서 당신의 판단을 구한다.

### 6-나. 시간적 인과 주장을 철회한다

"저장 arm의 세대 혼재 = 한 실행 도중 코드가 바뀌었다"는 서술을 **철회한다.** 당신 말대로
복사·부분 재측정·resume 혼합으로도 같은 상태가 나오고, provenance 없이 단정할 수 없다.
확정되는 것은 "한 arm 안에 서로 다른 세대의 측정이 섞여 있다"까지다. 원장 §36-d에 기록했다.

같은 절에 다음도 함께 철회했다.

- **A013 tier-1 arm의 표본 수를 69라고 말한 것은 틀렸다.** arm당 7건이다.
- **"독립 차단 사유 4개"는 논리적 범주이지 반환 list 길이가 아니다.** A010은 4항목, 나머지
  6건은 3항목이다. 당신 지적이 맞다.
- **A010에 "실제 비대칭이 있다"고 표현한 것은 틀렸다.** 양 arm의 기록된 지문은 서로 같고,
  다만 사용 불능이다.

### 6-다. Pilot 전행 증거를 확장하지 않는다

당신 요청대로다. 그 증거가 말하는 것은 **저장된 Pilot 69건과 A017 후보 7건의 CSV 전행에서
OR/AND 차이가 0**이라는 것까지다. 전체 evaluator 동등성이나 과거 환경변수 부재의 증명으로
쓰지 않는다. 원장 문구도 그 범위로 좁혔다.

또한 당신이 지적한 대로 **A017 baseline 7건 중 6건은 로컬에 `steps.csv`가 없어 전행 검사를
하지 못했다.** 이 사실을 §10에 미확인으로 남긴다.

### 6-라. 정지 정책 대조군에 대한 당신의 해석을 수용한다

`baseline_does_not_locomote`는 측정 오류가 아니라 **엔진의 운영상 비교 금지 정책**이라는
당신의 구분이 맞다. 정지 정책을 같은 평가기로 재는 진단 자체는 무효가 아니다. 원장 서술을
그에 맞게 읽도록 §36-d에 남겼다.

## 7. 내 서술 정정 — G4·G5의 미달 인수

1.5.1 보고에서 나는 이렇게 썼다.

> "G3·G4·G5·G7이 추종 0.70 미달이다"

**틀렸다.** §4.7 표가 실측이다. G4는 생존 0.781/추종 0.729, G5는 생존 0.719/추종 0.722다.
**둘 다 추종은 이미 기준을 넘겼고 생존에서 떨어진다.** G3만 양쪽, G7만 추종 단독이다.

이것을 사소한 오기로 취급하지 않는 이유는 당신이 §5.3에서 쓴 그대로다 — **다음 단일변수를
이 표에서 고르므로 약한 인수를 잘못 지목하면 탐색 자체가 엉뚱한 방향으로 간다.**

반영한 곳 3군데:

- `GO2_PROJECT_STATE.md` §35-c(정정 블록, G-F184) 및 §35-e G-F182 행
- `SERVER_SESSION_RUNBOOK.md` §9 Q2 판독
- `tools/build_go2_a017_full_suite_package.py` README 상수 — 패키지 안에 실려 서버로 간다

## 8. 당신의 감사 이후 확정된 2건

당신이 §8에서 P1으로 올린 두 항목이다. 둘 다 해소됐다.

### 8-가. 잔여 GPU 시간 = **15시간** (260908 확인)

당신 지적대로 25시간을 예산으로 쓰지 않았다. 실측값을 받았다. G-A027 추정 1h45m이므로
실행 후 약 13h가 남는다. 이 추정은 **상한이 아니다** — 러너에 시간 집행 코드가 없다는 당신의
R8 지적은 그대로 유효하고, `[NO_DEADLINE]` 표시로 남아 있다.

### 8-나. `NO_AUTO_SUBMIT` — 제출 자격 문제가 **아니다**

당신은 이를 "감사 권한 밖, 운영진 답변 필요"로 분류했고 나도 1차 지시서에 그렇게 적었다.
**그 분류가 틀렸다.** 판단 근거가 대회 배포 코드 안에 이미 있었다.

근거는 대회가 배포한 `go2_task/_finalize.py` 자신의 서술이다. 우리 저장소에 사본이 있다:
`workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/training/source/go2_task/_finalize.py`

| 확인 사실 | 위치 |
|---|---|
| 기능 이름이 **자동 백업**이고 주석에 **"⚠️ 예선 제출이 아니다"** 라고 명시. 공식 제출은 참가자가 웹사이트에서 직접 업로드하는 것이라고 같은 자리에 적혀 있다 | `:842-846` |
| 존재 이유는 "학습이 몇 시간 걸리므로 **서버가 꺼지거나 컨테이너가 재생성돼도 학습 이력이 남도록**" 제공하는 **편의 장치** | `:191`, `:844-846` |
| 끄는 스위치 `NO_AUTO_SUBMIT`는 **대회 코드가 스스로 제공하고 문서화한 것** | `:192`, `:849`, `:859` |
| 올라가는 내용은 `model_best.pt`+`env.yaml`+`report.html` 3개 — **우리가 손으로 내는 것과 동일하며 그 이상의 이력이 없다** | `:866-873` |
| 운영 서버에 host/token 설정이 없으면 **스위치와 무관하게 조용히 건너뛴다** | `_submit_config()`, `:860-865` |

**판단.** 제14조가 부정행위로 규정하는 것은 "제공된 서버에 에이전트·도구를 설치하거나 외부
서비스를 연동하는 등 **학습 환경의 구성을 변경하는 행위**"다. 대회 코드가 직접 제공하는
환경변수를 그 코드의 안내대로 쓴 것은 구성 변경이 아니다. 또한 운영 설정 부재로도 동일하게
꺼지는 기능을 자격 요건으로 볼 수 없다.

**제14조 대조 위험이 실제로 발동하는 조건은 배포 학습 경로를 고친 경우다.** 확인했다 —
`train.py`·`play.py`·`go2_task/`·`quadruped_rewards.py` 모두 배포 원본 그대로이며(`git status`
무변경), 러너는 `isaaclab.sh -p train.py`를 원본 인자로 호출한다.

**잔여 위험과 제거 방법.** 서버가 휘발성이므로 과거 실행의 서버측 기록은 없을 수 있다.
그러나 이 백업 장치는 학습을 요구하지 않고 완성된 `exported/`만 필요하며, **이 컨테이너에서
실제로 동작한 기록이 있다**(H1 `train_260828-02.log:111246-111248` `[backup] 백업 완료`).
따라서 제출 정책 확정 시 `NO_AUTO_SUBMIT` 해제 상태로 finalize를 한 번 돌리면 된다. GPU 0.
런북 §8-b에 절차로 넣었고, 러너는 이미 기본 해제이며 계약 테스트 절 [10]이 강제한다.

**이 항목을 당신의 P1 목록에서 내려도 되는지, 아니면 위 논거에 결함이 있는지 §11에서 묻는다.**

## 9. 파일 SHA256 — 당신의 감사 시점 대비

`Q/` = `workspace/training/quadruped/`

| 파일 | 현재 SHA256 | 감사 시점 대비 |
|---|---|---|
| `Q/go2_eval_telemetry.py` | `98298d0df749f38f5058013355d24dc6a040a4232fa5c1d60387e0ae9033ec76` | **변경** (was `d801d991…`) |
| `Q/go2_fixed_eval_report.py` | `7d13bc8cd87219b841bbb9e3f5108f25b73753c79996c66279ee5e3809bb4527` | **변경** (was `2d74e585…`) |
| `Q/go2_tuning_eval_report.py` | `fdda4fce02c3c8843ffac858108f9ef13bbfc575f1bb4f40bdd6f27b4a129d88` | **변경** (was `cacb87ed…`) |
| `Q/server_run_go2_a017_full_suite.sh` | `1828d25e875c14c620d127150b300b0d75f49c96608573ea0fe426df9a92bcdc` | **변경** (was `5e813d49…`) |
| `Q/go2_a017_full_suite.zip` | `15826d0ef837b364086e9c2024875dbd4ce9fdafabf55de1ea75c61589528d72` | **변경** (was `8d97fc1b…`) |
| `Q/go2_tuning_config.py` | `92bf521c06399d5a5e7d86cfc29562de9d7e096267fcf4b65c4f82e43e0beec5` | **변경** (ENGINE_VERSION 1.5.2) |
| `Q/config/go2_tuning_experiment_schema.json` | `d2bec653456a6d0234bb7445f40a6e1c0447b79ae22bf699cb76e9b19cf35a76` | **변경** (const 1.5.2) |
| `tools/build_go2_a017_full_suite_package.py` | `51c57c920c244126d01e603ce19f692f97c5e11696b02fe00ee275778079cbf7` | **변경** (R5·§5.3 문구) |
| `tools/test_go2_posture_survival_contract.py` | `febeb6f97d63c2a20c76e1542f49446efeb5b795453432486db28f874147f659` | **변경** (C1·C2 회귀 검사 추가) |
| `tools/test_go2_scoring_repair_contract.py` | `7d5d642f51dde13136db193d860d49b2239971a4f97e87e5ff316b42487b6563` | **변경** (R1·R2·R3 반례 추가) |
| `tools/test_go2_a017_full_suite_contract.py` | `86045d6a53f323d86414a52e48121d00a24b34d398175b71af6351493efcc9e5` | **변경** (R8 지문 실행 검사 추가) |
| `tools/test_go2_default_vs_pilot_contract.py` | `42be1a46a1e0c9e0f46c6fcbe5b3b7d8d9ef09aae6524b15590c65ed37f0569d` | **변경** (delta 억제 검사) |
| `tools/test_go2_tuning_engine_contract.py` | `b4f1524967c64df6d0451cc1d616d8f9a4a8863256356a884f33d0bfdf29af6f` | 변경 없음 |
| `GO2_PROJECT_STATE.md` | `ca12580a196038f8e85469e7cdfa7ad58771ac2c3f0ab2a315a8a208d3517d65` | **변경** (§35-c 정정, §36 신설) |
| `SERVER_SESSION_RUNBOOK.md` | `479201a8aca6b1c3c54cdf2713795fae4fedca4582d2638596892d5d6ddf3f17` | **변경** (해시·GPU·§8-b·§9) |

원장 §36이 이번 변경의 서술 기록이다.

## 10. 여전히 미확인 — 내가 해결했다고 주장하지 않는 것

- **대표 평가가 worst-product case의 인자만 읽는 문제**(당신의 R3 두 번째 지적). 손대지 않았다.
- **`NCRC_EVAL_FALL_*` 변경 시 resume 거절**은 지문에 넣었으나 러너가 그 변수를 설정하지 않아
  실측하지 못했다. 이론적 보장이다.
- **A017 baseline 7건 중 6건의 `steps.csv` 부재.** 전행 검사 불가. G-A027이 해소한다.
- **부분 회수(PARTIAL) 경로를 실제 서버 강제 실패로 시험하지 않았다.** `INTERNAL_GATE_INCONCLUSIVE`.
- **`eval` 재측정이 기존 case 디렉터리를 지운다**는 당신 지적. 기본 재실행은
  `GO2_DISCARD_PREVIOUS` 없이는 시작 자체가 막히지만, `GO2_RESUME=1` 경로에서 조건이 달라진
  case는 여전히 지우고 다시 잰다. 이전 자료 별도 보존은 구현하지 않았다.
- **공식 evaluator·공식 점수 `OFFICIAL_RESULT_UNMEASURED`, 영상 `VIDEO_UNKNOWN`.**
- **H1 대비 정량 인과.** 당신 §6의 판정을 그대로 수용한다 — 이 Go2 자료로는 입증할 수 없다.
  "학습은 실패하지 않았고 채점만 실패했다"는 배타적 설명을 쓰지 않는다.

## 11. 당신에게 요청하는 것

**(1) 항목별로 반례가 실제로 거절되는지 확인해 달라.** §5의 명령을 돌리고, C1·C2·R1·R2·R3·R8
각각에 대해 `수리확인` / `미수리` / `부분`을 판정해 달라. §4의 출력과 다르면 당신 출력이 맞다.

**(2) §6-가에 대한 판단을 달라.** `measurement_contract` 부재를 schema가 실측일 때 허용하고
note로 출력하는 것이 충분한가, 아니면 전면 차단해야 하는가. **기각한다면 그렇게 하겠다** —
G-A027이 두 arm을 새로 재므로 실질 손실이 없다.

**(3) §8-나의 논거에 결함이 있는지 봐 달라.** 배포 코드 근거로 "자격 문제 아님"이라고 결론
냈다. 결함이 있으면 지적해 달라. 없으면 당신의 P1 목록에서 내려도 되는지 확인해 달라.

**(4) 실행 준비를 재판정해 달라.** 당신의 §8 준비 조건 7개 중 3번(모든 case의 자세 증거)과
5번(resume 설정 동일성)이 `INTERNAL_GATE_FAIL`이었다. 이 둘이 해소됐는지, 그리고 전체 판정이
여전히 `INTERNAL_GATE_FAIL`인지 판정해 달라. **§10의 미해결 항목이 서버 실행을 막을 만한
것인지도 함께 판단해 달라** — 특히 대표 평가 결함은 G-A027이 대표 평가를 돌리지 않으므로
이번 실행을 막지 않는다고 보지만, 그 판단이 맞는지 확인이 필요하다.

**(5) 하지 말아 달라.** 이 문서나 원장의 서술을 증거로 인용하지 말 것. 금지 어휘를 쓰지 말 것.
잔여 GPU를 15시간 외의 값으로 가정하지 말 것. 내가 "고쳤다"고 쓴 것을 확인 없이 수용하지 말 것.

## 12. 산출물

`GO2_REAUDIT_ROUND2_RESPONSE_260908.md`로 회신해 달라. 최소 구성:

1. §11(1) 항목별 판정표 — 근거 파일·줄·재현 출력 포함
2. §11(2)(3)에 대한 판단
3. §11(4) 실행 준비 재판정과 그 근거
4. 이번에 새로 발견한 결함이 있다면 C3, C4… 로 번호를 이어서
5. 당신이 확인한 SHA (§9와 대조)
6. 미확인 목록
