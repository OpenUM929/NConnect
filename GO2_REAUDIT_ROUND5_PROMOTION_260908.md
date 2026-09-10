# Go2 승급 게이트 수리(C6)와 회수 검증 도구 — 5차 재감사 요청

작성일: 2026-09-08 · 작업 ID: OPUS-REAUDIT-R5-260908
대상: `GO2_REAUDIT_ROUND4_RESPONSE_260908.md` §7 개선안의 P0·P1 항목 이행 결과.
직전 문서: `GO2_REAUDIT_ROUND4_ENGINE_154_260908.md`.

## 0. 이 문서가 무엇인가

4차 회신의 §7 개선안 중 **GPU를 쓰지 않고 수집 전·점수 채택 전·승급 전에 끝내야
한다고 지정된 것**을 구현하고, 그 결과를 검증받으려는 요청서다. 새 실험은 하지
않았고 배포 패키지는 건드리지 않았다.

- [확보] C6 재현과 수리, 회수 검증 도구와 그 계약 검사, 런북 P0 정정.
- [미확보] G-A027 실측·영상·현재 GPU 잔량·공식 결과.
- [보장하지 않음] 이 문서의 검사 통과는 실제 로봇 성능이나 공식 합격을 뜻하지 않는다.

경로 약칭 `Q/` = `workspace/training/quadruped/`.

**판정 어휘** — `ARTIFACT_VERIFIED` / `VIDEO_OBSERVED`·`VIDEO_UNKNOWN` /
`INTERNAL_GATE_PASS`·`_FAIL`·`_INCONCLUSIVE` / `INTERNAL_MEASUREMENT_INVALID` /
`OFFICIAL_RESULT_UNMEASURED`. 맨 `PASS`·`합격`·`제출 가능`·`공식 점수`는 쓰지 않는다.
현재 남은 GPU 시간은 `[미측정]`이며 이 문서는 그 값을 만들어내지 않는다.

## 1. 요약

| 항목 | 4차 회신에서 | 이번에 |
|---|---|---|
| C5 수리 위치·거절 정책 | 동의(Q1·Q2) | 변경 없음 |
| C6 승급 게이트 all-case 인자 검사 | P1 · 승급 전 | **재현하고 수리했다** (§2) |
| 회수 검증 자동화 | P1 · 점수 채택 전 | **도구와 계약 검사를 만들었다** (§3) |
| 런북 잔량 표현·중단 시점 설명 | P0 · 수집 전 | **정정했다** (§4) |
| 내 유일해법 주장 | §3.3 정정 요구 | **철회했다** (§5) |
| 배포 ZIP | "몰래 덮어쓰지 말 것" | **건드리지 않았다** — `c190c291…` 그대로 (§6) |
| P2 두 항목 | 다음 패키지 | 미이행, 이유를 적었다 (§7) |

## 2. C6 — 승급 게이트가 case 하나만 본다

### 2.1 재현

당신의 §7.3 합성 두 case를 한 시나리오(G1)에 넣고 나머지 여섯 시나리오는 여유 있게
통과시켰다. 나머지 arm 속성은 승급이 가능한 상태로 채웠다(현대 지문, `LOCOMOTES`,
seed 3종, 점수 65.0 ≥ 60.0).

```
case A  생존 0.96 × 추종 0.71 = 곱 0.6816   <- worst product
case B  생존 0.90 × 추종 0.99 = 곱 0.8910   <- 생존 문턱 0.95 미달
```

수리 전 `Q/go2_tuning_eval_report.py:259-264` 결과:

```text
eligibility blockers: []
status              : INTERNAL_REPRESENTATIVE_PROMOTION_PASS
scenario_gates_ok   : True
failure_reasons     : []
```

당신의 지적대로다. 시나리오 점수는 case별 곱의 최솟값이고, 그 옆에 실리는 두 인자는
**그 worst-product case 자신의 것**이다. 승급 게이트가 그 인자를 읽었으므로, 곱이 더
높아서 worst-product가 아닌 case의 생존 미달은 승급 판정에 도달하지 못했다.

### 2.2 필요한 값은 이미 계산돼 있었다

`Q/go2_fixed_eval_report.py:118-121`이 시나리오마다

```python
survival_floor = min(item["proxy"]["survival_proxy"] for item in valid)
tracking_floor = min(item["proxy"]["tracking_proxy"] for item in valid)
```

를 구해 `survival_proxy_min_any_case`·`tracking_proxy_min_any_case`로 싣고, 같은 파일
`:140-145`의 시나리오 게이트는 **이미 그 값을 쓰고 있었다.** 승급 경로만 읽지 않았다.
그래서 이번 수리는 새 집계를 만드는 일이 아니라 **이미 있는 값을 읽게 하는 일**이다.

### 2.3 수리

`Q/go2_tuning_eval_report.py`:

```python
SCENARIO_FLOOR_KEYS = ("survival_proxy_min_any_case", "tracking_proxy_min_any_case")

floor_failures = sorted(
    key
    for key, item in scenarios.items()
    if item["survival_proxy_min_any_case"] < gates["required_survival_proxy"]
    or item["tracking_proxy_min_any_case"] < gates["required_tracking_proxy"]
)
gates_ok = len(scenarios) == 7 and not floor_failures
```

세 가지를 지켰다.

**곱 집계를 바꾸지 않았다.** `simulation_points_70`도 `scenario_proxy`도 그대로다.
수리는 **미달한 case를 이름 붙여 승급을 막는 것**이지 점수를 다시 매기는 것이 아니다.
판정문에 두 읽기를 나란히 싣는다 — `scenario_floor_failures`(전 case 기준)와
`scenario_worst_product_factor_failures`(기존 기준). 어느 기준으로 걸렸는지 감사자가
구분할 수 있어야 한다.

**floor가 없는 보고서는 성능 실패가 아니라 측정 무효로 처리한다.** 그 값을 계산하지
않은 엔진이 쓴 보고서는 all-case 질문에 답할 수 없다. worst-product 인자로 조용히
대신 읽으면 그것이 바로 이번에 고친 버그다. 그래서
`representative_eligibility()`가 `candidate_scenario_case_floors_absent:<ids>`로
막고 `INTERNAL_MEASUREMENT_INVALID`를 낸다 — 당신의 §7.5 "입력 유효성 오류를 로봇
성능 실패로 기록해서는 안 된다"를 그대로 따랐다.

**screening에는 이 절대 기준을 넣지 않았다.** 당신의 §7.3 마지막 문장 그대로다.
`tier1_decision()`은 손대지 않았고, 계약 검사가 그것을 고정한다.

### 2.4 수리 후

```text
[hidden case B]  status: INTERNAL_REPRESENTATIVE_PROMOTION_FAIL
                 floors failed        : ['G1']
                 worst-product failed : []
[all cases pass] status: INTERNAL_REPRESENTATIVE_PROMOTION_PASS []
[no floors]      status: INTERNAL_MEASUREMENT_INVALID ['candidate_scenario_case_floors_absent:G1']
```

두 번째 줄이 중요하다. 모든 case가 두 문턱을 넘는 arm은 여전히 승급 가능하다 —
수리가 과도하게 거절하지 않는다.

### 2.5 회귀 검사

`tools/test_go2_scoring_repair_contract.py` [13]에 여섯 검사로 고정했다.

| 검사 | 고정하는 것 |
|---|---|
| 숨은 case가 승급을 막는다 | C6 반례 자체 |
| floor 기준으로 이름이 찍히고 worst-product 기준으로는 안 찍힌다 | 두 읽기가 구분된다 |
| 발표 총점이 그대로다 | 수리가 점수를 다시 매기지 않는다 |
| 전 case 통과 arm은 승급된다 | 과도 거절이 없다 |
| floor 없는 보고서는 무효이고 점수를 내지 않는다 | 낙관적 대체 읽기 금지 |
| screening은 절대 기준을 상속하지 않는다 | §7.3 마지막 문장 |

## 3. 회수 검증 도구 (P1 · 점수 채택 전)

`tools/verify_go2_a027_harvest.py`. 회수물을 받은 자리에서, **어떤 수치도 읽기 전에**
돌린다. GPU 0.

```
python -B tools/verify_go2_a027_harvest.py \
  --harvest workspace/_keep/go2_a017_full_suite \
  --out workspace/_keep/go2_a017_full_suite/harvest_verification.json
```

### 3.1 이 도구의 전제

계측기가 자기 출력을 검사하고 러너가 자기가 쓴 요약을 검사한 것은 **둘 다 만든 쪽의
말**이다. C5가 정확히 그 지점에서 났다 — 요약이 "관측률 100%, 모호성 없음"이라고
썼고 러너가 그 요약을 읽고 통과시켰다. 이 도구는 받는 쪽의 검사이고,
`summary.json`이 주장하는 것을 `steps.csv`에서 다시 계산한다.

| 검사 | 무엇을 다시 계산하는가 |
|---|---|
| case 집합 | registry가 지정한 69건과 정확히 일치하는가. 빠진 것도, **더 있는 것도** 거절 |
| 행·env·step | 요약의 `rows`가 CSV에 실제로 있는가, metadata의 env 수와 맞는가 |
| **아홉 채널 비유한 값** | 요약의 `nonfinite_row_count=0`을 **CSV에서 직접 다시 센다** |
| 커버리지 | `upright` 열의 관측 행 비율을 다시 구해 요약값과 대조 |
| 채점 입력 | 소비될 일곱 수치가 유한하고 범위 안인가 (`survival_proxy` ∈ [0,1] 등) |
| 두 arm의 자 | evaluator·registry 해시, 그리고 **case 단위**로 schema·계약·문턱·`step_dt` |

`first_nonfinite`로 최초 이상 행의 step·env·column을 함께 낸다 — 당신의 P2 진단
항목을 계측기가 아니라 이쪽에서 먼저 제공한다.

### 3.2 이 도구가 존재하는 이유

`INTERNAL_GATE_PASS`가 아니면 어떤 점수도 읽지 않는다. 실패한 case는 이름이 찍히고,
**그 case를 빼고 68건으로 점수를 완성하지 않는다.** arm은
`INTERNAL_MEASUREMENT_INCOMPLETE`이며 case 수는 여전히 69로 센다. 68건의 완전한
측정이 아니라 69건의 미완료 측정이다 — 당신의 §4 "임의 제외나 0 대입으로 완전
측정처럼 만들지 않는다"가 도구의 동작으로 들어가 있다.

### 3.3 계약 검사

`tools/test_go2_harvest_verifier_contract.py`. 합성 2-arm × 69-case 회수물을 만든 뒤
**한 번에 한 곳씩 망가뜨려** 각 검사가 실제로 거절하는지 확인한다. 27개 검사 전부
통과한다. 손상 종류:

case 하나 삭제 · 요약은 0이라 쓰고 CSV에 `inf`·`-inf`·`nan` 한 행 · `upright` 한 칸
결측 · `survival_proxy` 1.5 / `tracking_xy_rmse` -0.1 / `survival_proxy` null ·
CSV 한 행 절단 · arm 간 evaluator 해시 불일치 · arm 안에서 문턱이 바뀜 · registry에
없는 case 추가 · `posture_fall_verdict_ambiguous` true · `nonfinite_row_count` 3 ·
`posture_min_env_coverage` 0.5 · `schema_version` 5 · `completed` false.

[1]번 검사는 **손상되지 않은 회수물이 통과하는지**다. 전부 거절하는 도구는 검사가
아니다.

[9]번이 §3.2의 성질을 고정한다 — 한 case가 망가진 arm은 69건 중 미완료로 남고, 그
case 이름이 나오고, **다른 arm의 유효한 측정은 그대로 유효하다.**

## 4. 런북 P0 정정 (§7.2 첫 줄)

**잔량.** 첫 화면이 "잔여 GPU 15시간(260908 확인)"이라고 단정하고 §8-c는 "15시간은
계획 입력일 뿐 현재 잔량이 아니다"라고 적혀 있었다. 첫 화면을 §8-c에 맞췄다 —
`[미측정]`, 시작 전 대시보드 실측.

**중단 시점.** "러너가 case마다 검사하고 미달이면 **그 자리에서** 실패한다"를
정정했다. 실제 코드는 case가 끝난 뒤 요약을 검사한다. 새 문장:

> 러너는 **case가 끝난 뒤** 그 요약을 검사하고, 미달이거나 모호하면 그 case의
> 생존값을 채택하지 않고 다음 case를 중지한다. 이상 프레임이 나온 그 순간에 play를
> 죽이지는 않으므로 해당 case의 실행 비용은 이미 쓴 것이다.

**계수의 범위.** `nonfinite_row_count=0`이 위치 3·속도 3·명령 3의 아홉 입력에
한정된 의미이고 모든 센서·파생값이 온전하다는 뜻이 아님을 §8-a에 적었다(당신의 §3.2).

**수집과 승급의 분리.** 첫 화면에 한 줄 넣었다 — 수집 조건 통과는 측정이 유효하다는
뜻일 뿐 후보 자격이 아니고, 승급은 모든 case의 인자를 각각 보고 판정한다.

**§8-d 신설.** 회수 검증 절차를 실행 원장에 넣었다.

## 5. 내 주장 철회

G-F199에 "오직 명시적 계수만이 C5를 잡는다"라고 적었다. 과했다. 증명된 것은 현재
계수가 그 반례를 차단한다는 것뿐이고, 당신 말대로 무효 행 Boolean이나 원시자료 검사도
구현 가능한 대안이다. 원장 G-D150으로 철회했다.

지난번 "결측 한 행 때문에 138건 전체가 실패한다"에 이어 두 번째다. 두 경우 모두 내
설계 선택을 정당화하려고 필요 이상으로 강한 근거를 붙였다. 3·4차 요청서에서 그 문장을
그대로 쓴 것은 내 잘못이다.

## 6. 배포 패키지는 건드리지 않았다

`Q/go2_a017_full_suite.zip` = `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea`.
당신이 §5에서 검증한 그 파일 그대로이고, `upload/G-A027/current/`의 사본과 바이트
동일하다(`cmp` 확인). 이번 변경은 전부 zip **밖의** 로컬 채점 경로다 —
`go2_tuning_eval_report.py`와 두 개의 새 `tools/` 파일. zip 안에 들어가는 파일은
하나도 바뀌지 않았다.

한 가지 미이행을 밝힌다. 당신이 §3.3에서 지적한 `Q/go2_eval_telemetry.py:206-208`의
legacy fallback 주석은 1.4.0 잔재이며 실제 null 처리와 충돌한다. **고치지 않았다.**
그 파일은 zip 안에 있고, 주석 한 줄 때문에 다시 빌드하면 당신이 §5에서 검증한 해시가
무효가 되어 수집 전에 재감사가 한 번 더 필요해진다. 당신이 "비차단 문서 정리 항목"
으로 분류했으므로 다음 패키지로 미뤘다. `tools/test_go2_posture_survival_contract.py`의
같은 취지 주석은 zip 밖이라 정정했다.

## 7. 하지 않은 것

**P2 두 항목**(현대 `measurement_contract` 검증과 resume 검사 연결, 무효 값의 최초
위치 기록)은 다음 패키지다. 후자는 회수 검증 도구가 `first_nonfinite`로 이미 내므로
계측기 쪽은 급하지 않다고 판단했다.

**§7.5에서 하지 말라고 한 것들**은 손대지 않았다 — 전면 evaluator 재설계, 관측률
100% 강제, 모든 비유한 ray 즉시 실패, 최초 이상 프레임 강제 종료. C3의 무해 결측
허용도 되돌리지 않았다.

**작업 중 사고 하나.** 파일 쓰기 가능 여부를 진단하다가
`Q/go2_tuning_engine_v1_4.zip`을 0바이트로 잘랐다. 빌더로 즉시 재생성했고 사이드카가
일치한다. 이 zip은 바이트 재현성이 없는 빌드 산출물이고 어느 문서에도 해시가 박혀
있지 않아(저장소 전체에서 참조 0건) 잃은 기록은 없다. 업로드 패키지는 영향받지
않았다. 원장 §39-d에 적었다.

## 8. 고정 해시

| 파일 | SHA256 | 4차 대비 |
|---|---|---|
| `Q/go2_tuning_eval_report.py` | `b5ca71c6b7853ee21d1829fd1ca55156b79e108d93f9600c01ced2942667a294` | **변경** (C6) |
| `tools/test_go2_scoring_repair_contract.py` | `fd28450ef8a037cf388747747168b6df94839050d88c5e6d8d02c57a93dd7314` | **변경** ([13] 신설) |
| `tools/verify_go2_a027_harvest.py` | `6b1868e32da30f0e8c6a84b45e675c7a27a7a3858585f398976bc2f589300f62` | **신규** |
| `tools/test_go2_harvest_verifier_contract.py` | `7939e9df9bb75800c510d0fcfe582b57d8a14f36658d6ab12e98128b99be5c63` | **신규** |
| `tools/test_go2_posture_survival_contract.py` | `61e64355936aaffd9d5ab7ef9be108700d0c9fc3d70c24e513f16c0eb51f2398` | **변경** (주석 정정) |
| `SERVER_SESSION_RUNBOOK.md` | `c49c916a8447ae7b331d670a897d1f01a8a6cdb65a130adc79439df93e4637f1` | **변경** (P0·§8-d) |
| `GO2_PROJECT_STATE.md` | `2bd95d8e728ce50a6167635024347cb603d68d8987df5d30ead6aedddf23b750` | **변경** (§39) |
| `Q/go2_a017_full_suite.zip` | `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea` | 불변 |
| `Q/go2_eval_telemetry.py` | `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84` | 불변 |
| `Q/go2_fixed_eval_report.py` | `06526e6779da98de7b98a2caef937e6e548ec1cb49868f72c662915bea1c6a9e` | 불변 |
| `Q/server_run_go2_a017_full_suite.sh` | `23e8923020492578be609a5e6eb4717100d5bab94d0c49e334ba2c8820eeabb6` | 불변 |
| `Q/go2_tuning_config.py` | `2f33a45ff10178cbf6af4fe83b0b489b1e15fe95b55f01f26c7f11cb77fa8a3a` | 불변 |
| `Q/config/go2_tuning_experiment_schema.json` | `3ed1b81e6c65cf38bf0def6fb60a6559dee83b73e61b3d0fe79c00d72e15939a` | 불변 |
| `tools/build_go2_a017_full_suite_package.py` | `687b90e958f887d430340247264a046fa8039144d0966fca700a2f11b5e80973` | 불변 |
| `tools/test_go2_a017_full_suite_contract.py` | `86045d6a53f323d86414a52e48121d00a24b34d398175b71af6351493efcc9e5` | 불변 |
| `tools/test_go2_default_vs_pilot_contract.py` | `42be1a46a1e0c9e0f46c6fcbe5b3b7d8d9ef09aae6524b15590c65ed37f0569d` | 불변 |
| `tools/test_go2_tuning_engine_contract.py` | `b4f1524967c64df6d0451cc1d616d8f9a4a8863256356a884f33d0bfdf29af6f` | 불변 |

Go2 계약 검사 10종 전부 rc=0. 로컬 zip 사이드카 14개 전부 일치.

## 9. C6 재현 코드

`Q/`에서 실행한다. 수리 전 코드에서는 첫 줄이 `INTERNAL_REPRESENTATIVE_PROMOTION_PASS`,
수리 후에는 §2.4의 세 줄이 나온다.

```python
import sys, json
sys.path.insert(0, '.')
import go2_fixed_eval_report as fer, go2_tuning_eval_report as ter

GATE = json.dumps({'grace_s': 0.5, 'height_rel_min_m': 0.18,
                   'hold_s': 0.5, 'tilt_cos_max': 0.5}, sort_keys=True)
MODERN = {k: ['x'] for k in fer.INSTRUMENT_KEYS}
MODERN.update(survival_proxy_sources=fer.REQUIRED_SURVIVAL_SOURCES,
              telemetry_schema_versions=['6'], posture_gate_params=[GATE],
              measurement_contracts=['posture_gate_v2/x'])

def scen(s, t, sf=None, tf=None):
    return {'survival_proxy': s, 'tracking_proxy': t, 'scenario_proxy': s * t,
            'survival_proxy_min_any_case': s if sf is None else sf,
            'tracking_proxy_min_any_case': t if tf is None else tf}

def arm(g1):
    return {'status': 'SELF_ASSESSMENT_COMPLETE', 'instrument': MODERN,
            'simulation_points_70': 65.0,
            'seed_fractions': {'101': .9, '202': .9, '303': .9},
            'locomotion': {'verdict': 'LOCOMOTES'},
            'scenarios': dict({'G1': g1},
                              **{g: scen(.99, .95) for g in
                                 ('G2', 'G3', 'G4', 'G5', 'G6', 'G7')})}

gates = {'minimum_points_70': 60.0, 'required_survival_proxy': 0.95,
         'required_tracking_proxy': 0.70}

hidden = ter.representative_decision(arm(scen(.96, .71, sf=.90, tf=.71)), gates)
print('[hidden case B] ', hidden['status'],
      hidden.get('scenario_floor_failures'),
      hidden.get('scenario_worst_product_factor_failures'))
print('[all cases pass]', ter.representative_decision(arm(scen(.96, .71)), gates)['status'])
stale = ter.representative_decision(
    arm({'survival_proxy': .96, 'tracking_proxy': .71, 'scenario_proxy': .6816}), gates)
print('[no floors]     ', stale['status'], stale['blocking_reasons'])
```

계약 검사 두 개:

```text
python -B tools/test_go2_scoring_repair_contract.py
python -B tools/test_go2_harvest_verifier_contract.py
```

## 10. 되묻는 것

1. **C6 수리가 당신 §7.3의 기대 결과와 일치하는가.** 곱 집계를 바꾸지 않고 all-case
   미달을 별도 표시해 승급을 막는 것 — 이 형태가 맞는가. `scenario_floor_failures`와
   `scenario_worst_product_factor_failures`를 나란히 싣는 것이 감사에 충분한가.

2. **floor 부재를 측정 무효로 처리한 것이 맞는가.** 성능 실패가 아니라 자격 문제로
   본 판단이다. 과거 보고서를 재판정할 수 없게 만드는 부작용이 있는데, 그쪽이
   낙관적 대체 읽기보다 낫다고 봤다.

3. **회수 검증 도구의 검사 범위가 충분한가.** 특히 두 arm 동일성을 case 단위 지문
   집합으로 비교한 것, 그리고 `survival_proxy_v1`까지 범위 검사에 넣은 것.
   당신이 §3.2에서 든 지면 ray hit와 파생값 overflow는 이 도구도 다루지 않는다 —
   다뤄야 하는가.

4. **엔진 주석 정정을 다음 패키지로 미룬 판단이 맞는가.** zip 재빌드를 피하려고
   `Q/go2_eval_telemetry.py:206-208`을 그대로 뒀다. 아니면 지금 고치고 새 해시로
   재감사받는 편이 나은가.

5. **G-A027을 지금 진행해도 되는가.** 배포 ZIP은 `c190c291…` 그대로다. 남은
   선행조건은 잔여 GPU 실측 하나라고 이해하고 있다.

---

**이 문서는 요청서다.** 여기의 검사 통과는 측정 도구가 자기 계약을 지킨다는 뜻이지,
정책이 좋다거나 예선을 통과한다는 뜻이 아니다. 공식 결과는
`OFFICIAL_RESULT_UNMEASURED`다.
