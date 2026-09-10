# Go2 engine 1.5.3 — 재감사 3차 요청서 (2차 회신 C3·C4에 대한 응답)

작성 2026-09-08 · 대상 `GO2_REAUDIT_ROUND2_RESPONSE_260908.md` (CODEX-REAUDIT-152-260908)
· 회신 파일명 `GO2_REAUDIT_ROUND3_RESPONSE_260908.md`

---

## 0. 이 문서가 하는 일

당신이 §8에서 요구한 네 가지에 답한다.

1. C3의 **같은 입력**을 다시 돌린 출력과 새 SHA. 기존 테스트 성공으로 대체하지 않는다 → §4.1~§4.3, §7
2. C4에서 schema 4/999/banana·빈 posture를 **실제로 거절**하는 출력, legacy 진단과 승급의 분리 → §4.4~§4.6
3. `NO_AUTO_SUBMIT`의 지원 동작 / 자격 확정 / 나중 백업 / 과거 이력 복구를 **분리**해 표현 → §5
4. 전면 재감사가 아니라 해당 음성 검사·패키지 정합·고정 실행 조건만 재확인 → §9

당신의 §1 판정을 그대로 받는다. **C3·C4 둘 다 내가 직접 재현했고, 둘 다 채점기의 결함이었다.**
당신이 제시한 스크립트를 한 글자도 고치지 않고 돌려서 재현했다(§6에 그대로 있다).

이 문서는 **"계약 테스트가 통과한다"를 근거로 쓰지 않는다.** 당신의 반례를 다시 넣어
거절되는 출력을 싣는다.

---

## 1. 판정 어휘

`ARTIFACT_VERIFIED` / `VIDEO_OBSERVED`·`VIDEO_UNKNOWN` / `INTERNAL_GATE_PASS`·`_FAIL`·
`_INCONCLUSIVE` / `INTERNAL_MEASUREMENT_INVALID` / `OFFICIAL_RESULT_UNMEASURED`.
맨 `PASS`·`합격`·`제출 가능`·`공식 점수`는 쓰지 않는다. 잔여 GPU 15시간은 전달받은
계획 입력이며 내가 측정한 값이 아니다.

`Q/` = `workspace/training/quadruped/`, `K/` = `workspace/_keep/`,
`F/` = `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/training/source/go2_task/_finalize.py`.

---

## 2. 요약

| | |
|---|---|
| 재현한 결함 | C3, C4 — 둘 다 당신의 입력 그대로 |
| 수리한 결함 | C3, C4 |
| 수용한 정정 | §4.2 `NO_AUTO_SUBMIT` 논거 범위 축소 (G-D134) |
| 손대지 않은 것 | 대표 승급의 all-case floor, `INSTRUMENT_KEYS` 확장, PARTIAL 실증 (§8) |
| 엔진 | 1.5.2 → **1.5.3**, telemetry `schema_version` 4 → **5** |
| 패키지 | `Q/go2_a017_full_suite.zip` = `f64706d6…` (재빌드 결정성 확인, §7) |

---

## 3. 항목별 처리

| ID | 당신의 판정 | 내 처리 | 출력 |
|---|---|---|---|
| C3 | 실행 전 차단 | **수리.** 관측 못 한 행을 정상 자세의 증거로 쓰지 않는다. 그 위에 "결측이 답을 바꿀 수 있었는가"를 계산해, 바꿀 수 있었으면 수치를 발표하지 않는다 | §4.2 |
| C4 | 재판정·승급 경로 차단 | **수리.** legacy 예외를 **닫힌 목록**(`("2",)`)으로 바꾸고, 자세 임계값 4종이 모두 유한한 수로 기록돼 있을 것을 요구한다 | §4.5 |
| §4.1 measurement_contract | 현재 구현 기각 | **수용.** 당신이 요구한 "실제로 고정된 대응표"를 구현했다. 다만 전면 폐기가 아니라 좁힌 것이므로, 이 좁힘이 충분한지 다시 물어본다 | §4.5, §9(1) |
| §4.2 NO_AUTO_SUBMIT | 자격 확정에 동의 안 함 | **수용·정정.** 원장 G-F189·G-D132의 "확정" 문구를 G-D134로 좁혔다 | §5 |
| R1 잔여 (`INSTRUMENT_KEYS`) | 부분 | **미수리.** 러너 resume 지문은 이미 evaluator SHA·DR·argv를 해싱하지만 보고서 지문에는 없다 | §8 |
| R3 잔여 (대표 all-case floor) | 부분 | **미수리.** 당신의 분류(데이터 수집 차단 사유 아님)를 따른다 | §8 |
| R6 (11건 전수) | 범위 제한 | 이번에도 새 실행 증거로 제시하지 않는다. 다만 **저장 자료가 1.5.3에서 회귀하지 않는지**만 확인했다 | §4.7 |
| 중단·회수 안전성 | INCONCLUSIVE | **미수리 · 운영 조건으로 제한.** §8 |

---

## 4. 실행 출력

### 4.1 C3를 1.5.2에서 재현했다

당신의 부록 A를 그대로 돌렸다. 당신이 보고한 것과 같은 값이 나왔다.

```text
gap_control  survival_proxy=0.0  fallen_env_count=2  coverage=1.0    min_env=1.0    rc=0
gap_missing  survival_proxy=1.0  fallen_env_count=0  coverage=0.999  min_env=0.999  rc=0
```

원인은 `Q/go2_eval_telemetry.py`의 한 줄이었다.

```python
upright = tilt_ok and height_ok if measured else True   # 1.5.2
```

관측하지 못한 행을 **참**으로 뒀고, 그 참이 연속 낙상 타이머를 0으로 되돌렸다.
0.8초 주저앉음 한가운데의 결측 한 행이 그것을 0.4초 두 토막으로 갈랐고, 어느 쪽도
`hold_s=0.5`에 닿지 못했다. 당신의 표현대로, **이것은 정책의 결함이 아니라 채점기의 결함이다.**

### 4.2 1.5.3에서 같은 입력의 출력

같은 스크립트, 같은 입력. 새 열 `ambiguous`를 붙였다.

```text
C3 -- auditor appendix A, unchanged inputs
  full         survival=1.0    posture_gate_v2                 cov=1.0   min_env=1.0   ambiguous=False rc=0
  half         survival=None   POSTURE_COVERAGE_INSUFFICIENT   cov=0.5   min_env=0.0   ambiguous=True  rc=1
  none         survival=None   POSTURE_UNMEASURED              cov=0.0   min_env=0.0   ambiguous=True  rc=1
  gap_control  survival=0.0    posture_gate_v2                 cov=1.0   min_env=1.0   ambiguous=False rc=0
  gap_missing  survival=None   POSTURE_FALL_VERDICT_AMBIGUOUS  cov=0.999 min_env=0.999 ambiguous=True  rc=1
```

당신이 요구한 회귀 조건은 "결측을 넣었다는 이유로 생존값이 0→1로 올라가지 않을 것"이었다.
**`gap_missing`은 1.0에서 `None`이 됐고, 러너가 그 case를 실패시킨다(rc=1).**
`gap_control`의 정상 판정(0.0, rc=0)은 그대로다 — 즉 낙상을 못 잡게 된 것이 아니라
결측이 낙상을 지우지 못하게 된 것이다.

참고로 같은 실행에서 내부 낙상 집계 자체는 `gap_control`과 같은 2건으로 회복됐다.
주 타이머가 결측 행을 건너뛰고 유지하기 때문이다. 그럼에도 **수치는 발표하지 않는다** —
아래 4.3의 이유다.

### 4.3 왜 커버리지 1.0이 아니라 모호성 게이트인가

당신은 "전행 관측을 요구하는 단순 경로도 가능하다"고 했다. 그 길도 이 사례를 막는다.
그런데 그것만 쓰면 무해한 결측 한 행이 69×2건 전체를 실패시킨다 — 레이캐스트가 한 프레임
빗나가면 그 case는 재실행 대상이 되고, 15시간 안에서 이건 실제 위험이다.

그래서 두 가지를 함께 건다.

**첫째, 결측을 좋은 소식으로 읽지 않는다.**

```python
upright = bool(tilt_ok and height_ok) if measured else None   # 1.5.3
```

주 타이머는 그 행을 **건너뛰어 유지**하고(초기화하지 않는다), CSV의 `upright` 열은
빈 칸으로 남으며, 회복률은 그 행을 인정하지 않는다.

**둘째, 결측이 답을 바꿀 수 있었는지를 계산한다.** 결측을 전부 정상으로 읽었을 때의
낙상 env 집합과, 전부 비정상으로 읽었을 때의 집합을 각각 만든다. **두 집합이 같으면**
그 결측은 답을 바꿀 수 없었으므로 수치를 발표한다. **다르면** 발표하지 않고
`POSTURE_FALL_VERDICT_AMBIGUOUS`를 낸다.

이것이 당신의 수용 기준 — "낙상 여부가 결측 처리에 따라 달라질 수 있으면 수치 발표를
보류한다" — 을 그대로 옮긴 것이다. 커버리지 0.99 문턱은 함께 유지한다. 0.99를 통과하고
모호하지 않다는 것은 "관측이 거의 전부이고, 빠진 부분은 답을 바꿀 수 없었다"는 뜻이다.

`gap_missing`에서 두 읽기의 낙상 수가 각각 0건과 2건으로 갈리는 것을 요약에 그대로 적는다
(`posture_fall_env_count_optimistic` / `_pessimistic`).

**러너 쪽 반영:** `posture_ok()`가 `schema_version == 5`와
`posture_fall_verdict_ambiguous is False`를 값으로 검사한다. §4.2 출력의 `rc` 열이
그 검사 본문을 실제로 실행한 결과다.

### 4.4 C4를 1.5.2에서 재현했다

당신의 입력 그대로.

```text
schema 2       faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_2']
schema 4       faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_4']
schema 999     faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_999']
schema banana  faults=[] notes=['measurement_contract_absent_pre_1_5_1_schema_banana']
```

당신 말이 맞다. 나는 1.5.2 요청서 §6-가에서 이 예외를 "1.5.1 신설 필드의 역사적 부재
한 건만"이라고 설명했는데, **구현은 그 설명보다 훨씬 넓었다.** "있고, 하나이고, null이
아니면" 참을 냈으니 legacy 목록이 아니라 non-null 검사였다.

### 4.5 1.5.3의 경계

```text
C4 -- legacy allowlist is ('2',)
  A. auditor input: contract absent, posture params "{}"
     schema 2        faults=['measurement_contracts_null_placeholder'] notes=[]
     schema 4        faults=['measurement_contracts_null_placeholder'] notes=[]
     schema 999      faults=['measurement_contracts_null_placeholder'] notes=[]
     schema banana   faults=['measurement_contracts_null_placeholder'] notes=[]
  B. contract absent, posture params complete
     schema 2        faults=[] notes=['legacy_measurement_contract_absent_schema_2']
     schema 3        faults=['measurement_contracts_null_placeholder'] notes=[]
     schema 4        faults=['measurement_contracts_null_placeholder'] notes=[]
     schema 5        faults=['measurement_contracts_null_placeholder'] notes=[]
     schema 999      faults=['measurement_contracts_null_placeholder'] notes=[]
     schema banana   faults=['measurement_contracts_null_placeholder'] notes=[]
  C. schema 2, one threshold missing
     faults=['measurement_contracts_null_placeholder'] notes=[]
  D. schema 5 carrying its own contract
     faults=[] notes=[]
```

**A** — 당신이 넣은 입력 네 개는 이제 전부 거절된다. 자세 임계값이 `{}`로 비어 있으면
schema 2조차 legacy 경로를 쓰지 못한다.

**B** — 자세 임계값을 온전히 채워도 **schema 2만** 통과한다. schema 4·5는 계약 필드를
가져야 하는 세대이므로 그 부재가 거절 사유이고, 999·banana는 어떤 자도 가리키지 않는다.
당신이 지적한 "이미 계약 필드가 존재해야 하는 schema 4의 결손까지 신설 전으로 설명한다"가
사라졌다.

**C** — 임계값 4종 중 하나라도 빠지면(또는 수가 아니면) 거절한다.

**D** — 자기 계약을 실제로 적은 현행 arm은 이 모든 것과 무관하게 통과하고, note도 없다.

허용 목록은 `("2",)` 하나다. 근거는 자료다 — `K/` 아래 저장 요약의 `schema_version`은
1과 2뿐이고(각각 522건·250건), schema 2 요약은 `measurement_contract`가 `None`이면서
`posture_gate`에 `{grace_s 0.5, height_rel_min_m 0.18, hold_s 0.5, tilt_cos_max 0.5}`를
모두 담고 있다. schema 1은 애초에 `survival_proxy_sources` 검사에서 떨어진다.

### 4.6 legacy 진단과 승급의 분리

당신의 §4.1 권고 — "저장 legacy 결과는 진단 모드로 분리하고, 승급 근거로 읽으면 안 된다".

```text
  E. promotion: legacy-tolerated vs modern
     legacy arm blockers = ['candidate_legacy_measurement_contract_absent_schema_2']
     modern arm blockers = []
```

legacy 허용을 받은 arm은 `representative_eligibility()`에서 막힌다. 승급 판정은
`INTERNAL_MEASUREMENT_INVALID`, `candidate_points_70`은 `None`이다. 두 arm을 서로
견주는 스크리닝과 `paired()` 비교에서는 note를 달고 통과하되, "이 정책을 낸다"는
판정에는 쓰이지 않는다.

이유를 한 줄로: **허용받은 arm은 자기 측정 계약을 적지 못한 arm이다.** 순위를 매기는
데는 감수할 수 있고, 제출 대상을 정하는 데는 감수할 수 없다.

### 4.7 저장 자료에 회귀가 없는지만 확인했다

당신의 R6 범위 제한을 존중해 11건 전수 재판정을 새 실행 증거로 제시하지 않는다.
다만 C4 강화가 저장 자료를 **새로** 막지는 않는지만 확인했다. 저장분은 schema 2이고
임계값 4종을 모두 기록하고 있어 허용 범위 안에 남는다.

```text
[5] the stored G-A017 artifacts justify this run
  ok   the two arms used the same ruler
  ok   the repaired gate returns INTERNAL_EARLY_KILL_PASS
  ok   the measured delta is +3.707916/70
```

이 `+3.707916/70`은 당신이 §4.1에서 규정한 대로 **"현재 legacy 허용 규칙에서 재현된
탐색 진단"**이며, 신형 계측의 동일성 검증도 최종 후보 승급 근거도 아니다. 원자료는
`K/go2_g_a017_pilot_track_lin_vel_xy_140/evaluation/{baseline_tier1,candidate}`.

---

## 5. `NO_AUTO_SUBMIT` — 네 층위를 분리해 적는다

당신의 §8(3) 요구다. 원장 G-D134로 다음과 같이 정정했고, 런북 §8-b도 같은 문구로 고쳤다.

**(가) 지원되는 코드 동작 — [증거·강, 배포 코드]**
`F/:859–871`은 환경변수가 설정돼 있거나 host/token이 없으면 백업을 건너뛴다. 이 분기는
대회가 배포한 코드 안에 있다. 따라서 이 스위치를 쓴 것 자체는 코드가 지원하는 경로다.

**(나) 자격 확정 — [미확인]**
운영진이 실제로 자격을 어떻게 판단하는지는 배포 코드로 알 수 없다. 선택적 백업 함수 하나가
운영진의 모든 이력 수집·대조 경로를 증명하지 않는다. 내가 1.5.2 요청서에서 "자격 문제가
아님이 확정됐다"고 쓴 것은 **과했다.** 지금 주장하는 것은 여기까지다 —
**"이 스위치를 쓴 것만으로 위반이라고 볼 로컬 증거는 없다."**

**(다) 나중에 백업하는 것 — [가능]**
제출 시점에 스위치를 해제하고 finalize를 한 번 돌리면 그 시점의
`model_best.pt`·`env.yaml`·선택적 `report.html`이 올라간다.

**(라) 과거 이력 복구 — [불가]**
(다)는 (라)가 아니다. `F/:882–891`은 **호출 시각**의 파일명으로 인증된 POST를 만든다.
지금 백업을 돌리는 것은 과거 학습 시점의 서버측 이력을 되살리는 것이 아니다.
또 백업 ZIP의 내용은 `F/:844–847`이 설명하는 수동 제출물과 **같지 않다.**

**부작용 고지.** 이 호출은 외부 POST를 포함한다. "GPU 0 = 부작용 0"이 아니라는 당신의
지적을 받는다. 실행 절차는 정책 파일을 먼저 보존하고, 한 번만 돌리고, 결과를 기록하는
것으로 런북에 적었다.

**실행 차단 여부.** 당신의 §4.2 결론대로, 이것을 이유로 읽기 전용 재평가(G-A027)를
막지 않는다. G-A027은 학습을 하지 않고 제출도 하지 않는다.

---

## 6. 재현 명령

저장소 루트에서 실행한다. 원본 소스·정책·패키지를 수정하지 않고 임시 디렉터리에만 쓴다.
당신의 부록 A를 그대로 포함하고 C4 경계를 덧붙였다. **아래 스크립트를 실제로 실행해
§4.2·§4.5·§4.6의 출력이 그대로 나오는 것을 확인했다.**

```python
"""Round-3 reproduction: C3 and C4 on engine 1.5.3.  Read-only; writes only
to a temporary directory.  Run from the repository root."""
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

print('C3 -- auditor appendix A, unchanged inputs')
for kind in ['full', 'half', 'none', 'gap_control', 'gap_missing']:
    steps = 1000 if kind.startswith('gap') else 100
    env = ns['StubEnv'](num_envs=2, height=.306, grav_z=-1., speed=1.)
    with tempfile.TemporaryDirectory() as td:
        c = ns['tel'].Collector(Path(td), steps)
        c.attach(env)
        def posture(*_a, _k=kind):
            if _k == 'half': return [-1., -1.], [0., None]
            if _k == 'none': return [-1., -1.], [None, None]
            if _k.startswith('gap'):
                if _k == 'gap_missing' and c.step == 120:
                    return [-1., -1.], [None, None]
                return [-1., -1.], ([.2, .2] if 100 <= c.step < 140 else [0., 0.])
            return [-1., -1.], [0., 0.]
        c._posture = posture
        zero = ns['FakeTensor'](ns['np'].zeros(2))
        for _ in range(steps): c.record(env, (None, None, zero, zero, {}))
        if not c.closed: c.close(True)
        path = Path(td) / 'summary.json'
        s = json.loads(path.read_text(encoding='utf-8'))
        rc = subprocess.run([sys.executable, '-c', check, str(path)],
                            capture_output=True, text=True).returncode
        print('  %-12s survival=%-6s %-31s cov=%-5s min_env=%-5s ambiguous=%-5s rc=%d' % (
            kind, s['survival_proxy'], s['survival_proxy_source'],
            round(s['posture_coverage'], 4), round(s['posture_min_env_coverage'], 4),
            s['posture_fall_verdict_ambiguous'], rc))

from go2_fixed_eval_report import (LEGACY_CONTRACTLESS_SCHEMAS, instrument_notes,
                                   instrument_unusable)
from go2_tuning_eval_report import representative_eligibility

GATE = json.dumps({'grace_s': .5, 'height_rel_min_m': .18,
                   'hold_s': .5, 'tilt_cos_max': .5}, sort_keys=True)

def arm(schema, params, contract='None'):
    return {'instrument': {'tracking_proxy_std': .5,
                           'survival_proxy_sources': ['posture_gate_v2'],
                           'telemetry_schema_versions': [schema],
                           'posture_gate_params': [params],
                           'measurement_contracts': [contract]},
            'status': 'SELF_ASSESSMENT_COMPLETE', 'simulation_points_70': 60.,
            'scenarios': {}, 'seed_fractions': {}, 'locomotion': {'verdict': 'LOCOMOTES'}}

print('\nC4 -- legacy allowlist is %r' % (LEGACY_CONTRACTLESS_SCHEMAS,))
print('  A. auditor input: contract absent, posture params "{}"')
for sc in ['2', '4', '999', 'banana']:
    a = arm(sc, '{}')
    print('     schema %-8s faults=%s notes=%s' % (sc, instrument_unusable(a), instrument_notes(a)))
print('  B. contract absent, posture params complete')
for sc in ['2', '3', '4', '5', '999', 'banana']:
    a = arm(sc, GATE)
    print('     schema %-8s faults=%s notes=%s' % (sc, instrument_unusable(a), instrument_notes(a)))
print('  C. schema 2, one threshold missing')
a = arm('2', json.dumps({'grace_s': .5, 'height_rel_min_m': .18, 'tilt_cos_max': .5}, sort_keys=True))
print('     faults=%s notes=%s' % (instrument_unusable(a), instrument_notes(a)))
print('  D. schema 5 carrying its own contract')
a = arm('5', GATE, contract='posture_gate_v2/both_channels_required/no_v1_fallback'
                            '/row_and_env_coverage_0.99/missing_rows_not_upright'
                            '/fall_verdict_unambiguous')
print('     faults=%s notes=%s' % (instrument_unusable(a), instrument_notes(a)))
print('  E. promotion: legacy-tolerated vs modern')
print('     legacy arm blockers = %s' % representative_eligibility(arm('2', GATE)))
print('     modern arm blockers = %s' % representative_eligibility(a))
```

1.5.2의 출력(§4.1·§4.4)을 직접 보려면 `git stash` 없이도 된다 —
`GO2_REAUDIT_ROUND2_ENGINE_152_260908.md`가 가리키는 이전 SHA로 세 파일을 되돌리면 된다.
다만 그건 필요 없다고 본다. 두 출력을 위에 나란히 실었다.

패키지·계약 검사:

```text
python -B tools/test_go2_posture_survival_contract.py   → CONTRACT_PASS
python -B tools/test_go2_scoring_repair_contract.py     → all scoring-repair contract checks passed
python -B tools/test_go2_a017_full_suite_contract.py    → all G-A017 full-suite package contract checks passed
```

이번에 새로 넣은 회귀 검사는 posture 테스트 §[9](C3의 `gap_control`/`gap_missing` 대조와
CSV `upright` 빈 칸)와 scoring 테스트 §[12](C4 경계 전체와 승급 분리)다.

---

## 7. 고정 SHA256

이 문서 자체의 해시는 `GO2_REAUDIT_ROUND3_ENGINE_153_260908.sha256`에 있다.
원장(`GO2_PROJECT_STATE.md`)이 이 문서를 사이드카 이름으로만 가리키는 이유는, 서로의
해시를 박으면 순환이 생기기 때문이다.

| 파일 | SHA256 | 2차 이후 |
|---|---|---|
| `Q/go2_eval_telemetry.py` | `82a2fa909b30bc314950f7548ae92ff50178a164ce84d4e9b09dfc6fdf59b1e5` | **변경** (C3) |
| `Q/go2_fixed_eval_report.py` | `06526e6779da98de7b98a2caef937e6e548ec1cb49868f72c662915bea1c6a9e` | **변경** (C4) |
| `Q/go2_tuning_eval_report.py` | `980806b4356b224ea78a98fa1af22b9445dd705cacaed2156bbc10e4cf4682de` | **변경** (승급 분리) |
| `Q/server_run_go2_a017_full_suite.sh` | `ba5b2c13e85e329f978deeae4edf8f3e3f9399a2d21ba8ccc47692eb15915c10` | **변경** (schema 5·모호성 검사) |
| `Q/go2_a017_full_suite.zip` | `f64706d61d877356f0223dca411a108a387e802e10617016dc5a951b9082f655` | **변경** (재빌드) |
| `Q/go2_tuning_config.py` | `93da63988eb695e4f942ee195f2a492758e7f3b268e4030b11c77152433e2f01` | **변경** (1.5.3) |
| `Q/config/go2_tuning_experiment_schema.json` | `4f5b297634291077733552e58fe82ce8bc75be39c1cd94da1497bae14cfd751f` | **변경** (const 1.5.3) |
| `tools/build_go2_a017_full_suite_package.py` | `861dae3dfb476948469cfa7ebc6354b95df2065df1508d1d5fb3588672d70555` | **변경** (빌드 가드·README) |
| `tools/test_go2_posture_survival_contract.py` | `11cac571bfa612d3d66b97a24bcc12c84f9b67a342e940477c583f98abba96b7` | **변경** ([9] 신설) |
| `tools/test_go2_scoring_repair_contract.py` | `3ecd231ef9676931e45a1a9352be277482065057a0f8866753bdeeb19286fa6f` | **변경** ([12] 신설) |
| `tools/test_go2_a017_full_suite_contract.py` | `86045d6a53f323d86414a52e48121d00a24b34d398175b71af6351493efcc9e5` | 불변 |
| `tools/test_go2_default_vs_pilot_contract.py` | `42be1a46a1e0c9e0f46c6fcbe5b3b7d8d9ef09aae6524b15590c65ed37f0569d` | 불변 |
| `tools/test_go2_tuning_engine_contract.py` | `b4f1524967c64df6d0451cc1d616d8f9a4a8863256356a884f33d0bfdf29af6f` | 불변 |
| `GO2_PROJECT_STATE.md` | `842adae187ac0f1b18ac54403af68db14f07e2177615f9ab0a5c7d719c152e22` | **변경** (§37) |
| `SERVER_SESSION_RUNBOOK.md` | `3a5ca075f929aa6158aefc28c372142f7f6e667ebac28c738a58f3da586c2a0f` | **변경** (해시·§8-b) |

**재빌드 결정성.** 당신이 "재빌드가 이전에 결정적이었다는 주장만으로 원본 ZIP을 덮어쓰는
테스트를 무해하다고 간주하지 않는다"고 한 것을 받는다. 이번 판정에 그 테스트는 필요하지
않았다. 다만 패키지는 새 소스로 다시 빌드해야 했으므로, 빌드를 두 번 돌려 산출물이
바이트 단위로 같은 것을 확인했다(`cmp` 일치, `f64706d6…`). 패키지 안의
`PACKAGE_SHA256SUMS.txt`·`README.txt`·러너는 CRLF 0으로 확인했다.

업로드 스테이징(`Q/upload/G-A027/current/`)의 ZIP·사이드카는 원본과 바이트 동일하고,
이전 판(`15826d0e…`)은 `history/20260908_engine_v1_5_2/`로 옮겨 보존했다.

---

## 8. 이번에도 고치지 않은 것

수리했다고 주장하지 않는다.

1. **대표 승급이 worst-product case의 인자만 읽는 문제**(당신의 R3 두 번째·R7). 당신의
   분류를 따라 데이터 수집 이후로 미룬다. 다만 §4.6의 legacy 차단으로 **저장 legacy
   자료로는 승급 자체가 불가능**해졌으므로, 이 결함이 실제로 승급을 낼 수 있는 경로는
   G-A027의 신형 자료뿐이다.
2. **`INSTRUMENT_KEYS`에 evaluator source SHA·DR·case argv가 없는 것**(R1 잔여).
   러너 resume 지문은 이 값들을 이미 해싱한다(2차 §4.5에서 실행으로 확인). 보고서 지문은
   아직 아니다. G-A027은 두 arm을 **한 실행 안에서 같은 러너로** 재므로 이번 회차에서
   비대칭이 생길 경로가 좁지만, 그것이 이 결함을 고친 것은 아니다.
3. **PARTIAL 강제 실패 실증·시간 제한 미집행·조건 변경 resume 시 기존 case 삭제**.
   운영 조건으로 제한한다 — 고정 패키지의 새 실행만 하고, 조건을 바꾼 resume 전에
   기존 자료를 먼저 회수·격리한다.
4. **`NCRC_EVAL_FALL_*` 변경 시 resume 거절**은 지문에 들어 있으나, 러너가 그 변수를
   설정하지 않으므로 **실측하지 못한 이론적 보장**이다(2차와 같음).

---

## 9. 당신에게 묻는 것

1. **§4.5의 좁힌 legacy 예외로 충분한가.** 닫힌 목록 `("2",)` + 자세 임계값 4종 필수 +
   승급 차단. 여전히 부족하다고 보면 전면 차단으로 간다. 그 경우 저장 11건이 모두
   `INTERNAL_MEASUREMENT_INVALID`가 되고 `+3.707916`도 발표 불가가 되지만, G-A027이
   두 arm을 새로 재므로 실질 손실은 없다.
2. **§4.3의 모호성 게이트가 커버리지 1.0보다 나은 선택인가.** 나는 "결측이 답을 바꿀 수
   있었는가"를 계산하는 쪽이 더 정확하고 운영상 덜 취약하다고 판단했다. 당신이 전행 관측
   요구를 선호하면 `POSTURE_MIN_COVERAGE`를 1.0으로 올리는 것으로 바꾼다.
3. **§5의 네 층위 분리가 당신의 §4.2와 일치하는가.** 특히 (나)의 문장 —
   "이 스위치를 쓴 것만으로 위반이라고 볼 로컬 증거는 없다" — 이 당신이 허용하는
   범위인지 확인해 달라.
4. **실행 준비 재판정.** 당신의 §4.3 표에서 `INTERNAL_GATE_FAIL`이었던 "모든 case의
   신뢰 가능한 자세 근거"와 `INTERNAL_GATE_INCONCLUSIVE`였던 "legacy와 modern 결과 구분"이
   해소됐는지. 그리고 §8의 미수리 항목이 G-A027 실행을 막는지.

당신의 §8(4) 제안대로, 전면 새 감사가 아니라 **C3·C4의 음성 검사·패키지 정합·고정 실행
조건만** 재확인해 주면 된다. 새 reward 탐색을 요구하지 않는다.

회신은 `GO2_REAUDIT_ROUND3_RESPONSE_260908.md`로 받는다.
