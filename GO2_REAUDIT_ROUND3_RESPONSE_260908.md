# Go2 Engine 1.5.3 — Codex 독립 재감사 회신

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점의 내부 측정 신뢰성, 설계 의도·리포트의 근거 정합성.
- [현재 단계] 단계 0/6 — 증거·artifact 정합성. 본 회신은 측정기의 수정 감사다.
- [확보] C3·C4 원래 반례 차단, 계약 테스트 3종 종료 코드 0, 고정 해시 15개 일치.
- [미확보] 새 평가기의 실제 G1~G7 결과·영상, 잔여 GPU 실측, 모든 case의 승급 기준 검사.
- [이번 테스트] 결측이 낙상을 지우는지, legacy 예외가 현대 자료와 후보 승급까지 허용하는지.
- [흐름] 기존 반례 확보 → **수정 검증 완료·수집 조건 명시** → 고정 패키지 재측정 → 측정 무효면 회수·원인 분리 → 최종 제출.
- [지금 할 일] Opus에 이 회신을 전달하고 §6의 수집·사후 검사 조건을 실행 원장에 반영한다.
- [보장하지 않음] 코드 검증은 정책 성능·공식 점수·제출 자격을 보장하지 않는다.

작성일: 2026-09-08. 감사 ID: `CODEX-REAUDIT-153-260908`.
범위: Round 3의 C3·C4 수정, 호출부 연결, 고정 패키지 수집 준비. A006~A025 전수 재감사는 하지 않았다.
감사 과정은 원자료 읽기·임시 디렉터리 테스트로 제한하고, 산출물 작성 단계에서 이 회신만 추가했다. 서버·학습·백업 POST·커밋·패키지 재빌드는 실행하지 않았다.

경로 약칭:
- `Q/` = `workspace/training/quadruped/`
- `K/` = `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/evaluation/`
- `F` = `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/training/source/go2_task/_finalize.py`

Opus 요청서와 원장은 주장 목록으로만 사용했다. 아래 판정의 근거는 코드, 실제 JSON, 직접 실행한 테스트다. `[증거]`, `[추론]`, `[미확인]`, `[제안]`을 구분한다.

## 1. 결론

| 항목 | 독립 판정 | 근거·강도 |
|---|---|---|
| C3: 결측 한 프레임이 생존 0→1을 만드는 반례 | `INTERNAL_GATE_PASS` — 원래 반례 해소 | [증거·강] 실제 Collector와 실제 러너 검사 실행. §2 |
| C4: contract 없는 schema 4/999/banana 허용 | `INTERNAL_GATE_PASS` — 원래 반례 해소 | [증거·강] 실제 `instrument_unusable()` 실행. §3 |
| legacy 자료의 대표 승급 차단 | `INTERNAL_GATE_PASS` — 해당 경로 해소 | [증거·강] `representative_eligibility()` 및 계약 테스트 실행. §3 |
| 결측의 낙상 상·하한 비교 방식 | 수용, 관측률 1.0 강제 불필요 | [추론·강] 단조성 설명 + 실제 타이머 6,561 패턴의 모든 완성값 대조. §2 |
| G-A027 고정 패키지의 새 데이터 수집 | **§6 조건으로 재개하는 데 동의** | 수집과 승급을 분리한다. C3·C4를 이유로 다시 막지 않는다. 새 C5는 사후 원자료 검사로 차단해야 한다 |
| 자동 대표 승급 및 모든 입력에 안전한 평가기 | `INTERNAL_GATE_INCONCLUSIVE` | all-case 인자 검사 미수리 및 새 C5. 수집 동의는 이 경로의 승인 아님 |

핵심은 **기존 결함을 고친 사실을 인정하되, 그 사실을 평가기 전체의 무결성 인증으로 확대하지 않는 것**이다.

## 2. C3 — 수정 수용과 결측 방식의 정당성

### 2.1 같은 반례를 직접 실행한 결과

[증거] `Q/go2_eval_telemetry.py:281–310`은 결측을 `None`으로 표현한다. 주 타이머는 건너뛰며, 낙관 타이머는 정상, 비관 타이머는 비정상으로 처리한다. `:428–437`은 종료 env를 합친 두 낙상 집합이 같을 때만 생존값을 낸다. `Q/server_run_go2_a017_full_suite.sh:225–245,301–305`는 schema 5·모호성 False·수치/커버리지를 확인한다.

실제 Collector 출력에 러너에서 추출한 Python 검사 본문을 실행했다. GPU 시뮬레이션은 아니다.

| 입력 | survival_proxy | coverage / min_env | source | ambiguous | 검사 종료 코드 |
|---|---:|---|---|---|---:|
| full | 1.0 | 1 / 1 | posture_gate_v2 | False | 0 |
| half | null | 0.5 / 0 | POSTURE_COVERAGE_INSUFFICIENT | True | 1 |
| none | null | 0 / 0 | POSTURE_UNMEASURED | True | 1 |
| gap_control | 0.0 | 1 / 1 | posture_gate_v2 | False | 0 |
| gap_missing | null | 0.999 / 0.999 | POSTURE_FALL_VERDICT_AMBIGUOUS | True | 1 |
| 정상 자세에서 한 프레임 결측 | 1.0 | 0.999 / 0.999 | posture_gate_v2 | False | 0 |

`gap_control`과 `gap_missing`은 2 env·1,000 step·dt 0.02, 100≤step<140 동안 상대 높이 0.106m이며 후자만 step 120의 지면 관측을 지웠다. 이전 반례의 입력을 유지했다. 실행 근거는 실제 `Collector.record()/close()`와 `posture_ok()`이며, 요청서의 출력 복사로 대체하지 않았다.

### 2.2 왜 두 극단만으로 충분한가

[추론] 고정 dt·동일 grace/hold 아래, 한 행을 정상에서 비정상으로 바꾸면 연속 비정상 구간이 짧아질 수 없다. 따라서 낙관 낙상 집합 ⊆ 임의 결측 완성의 낙상 집합 ⊆ 비관 낙상 집합이다. 양 끝이 같으면 중간의 모든 해석도 같다. 공통 종료 env와의 합집합도 이 성질을 보존한다. 근거: `Q/go2_eval_telemetry.py:217–231,300–310,428–430`.

[증거] 실제 `_fall_timer()`를 dt 0.2, 기본 hold 0.5에서 호출했다. 정상/비정상/결측으로 구성된 길이 8의 **6,561개 패턴**마다 모든 결측 완성값을 열거했다. 끝점 일치 여부와 전체 가능한 판정의 단일성은 모두 일치했다. 결측을 건너뛴 주 타이머도 양 끝 사이에 있었다. 재현 코드는 부록 A.

[한계] 이는 이산 관측열과 내부 낙상 정의의 검증이지, 관측 사이의 연속 물리 움직임이나 공식 생존 정의 전체의 증명은 아니다. 주 타이머의 중간 집계만으로 확정 낙상을 주장하면 안 된다. 모호한 경우에는 최종 survival null이 우선이다.

**판정:** 모호성 검사 + env별 커버리지 방식에 동의한다. 관측률 1.0보다 무조건 더 정확하다고 표현하지 말고, 동일한 내부 판정을 확정할 수 있는 결측까지 허용한다고 설명한다. “결측 한 행 때문에 138건 전체가 실패한다”는 필연적 표현은 부정확하다. 러너는 해당 case에서 종료하므로 전체 작업이 미완료될 수 있지만, 이미 측정한 모든 case가 무효가 되는 것은 아니다(`Q/server_run_go2_a017_full_suite.sh:298–305`). 실제 결측 빈도와 재실행 비용은 [미확인]이다.

## 3. C4 — 좁힌 legacy 예외 수용

[증거] `Q/go2_fixed_eval_report.py:270,275–309`의 허용 목록은 `("2",)`이며 자세 임계값 네 개는 숫자·유한값이어야 한다. `:312–334`는 허용 이유를 note로 기록한다. `Q/go2_tuning_eval_report.py:220–229,239–257`은 그 note를 승급 차단으로 바꾸고 점수를 null로 반환한다.

| 직접 실행 입력 | 실제 결과 |
|---|---|
| contract=`None`, params=`{}`, schema 2/4/999/banana | 모두 `measurement_contracts_null_placeholder` |
| contract=`None`, 네 임계값 완비, schema 2 | faults=[] + `legacy_measurement_contract_absent_schema_2` |
| 같은 값, schema 3/4/5/999/banana | 모두 거절 |
| schema 2, hold_s 누락 | 거절 |
| schema 5, 정상 contract와 임계값 | faults=[], notes=[] |
| legacy arm 대표 적격 검사 | `candidate_legacy_measurement_contract_absent_schema_2` |

[증거] 실제 저장 자료 `K/baseline_tier1/cases/seed_101/diagonal_left/summary.json`과 `K/candidate/cases/seed_101/diagonal_left/summary.json`은 schema_version=2, measurement_contract 미기록이며 posture_gate={grace_s:0.5,height_rel_min_m:0.18,hold_s:0.5,tilt_cos_max:0.5}, survival_proxy_source=`posture_gate_v2`다. 허용 대상은 적어도 이 원자료로 확인된다. 522/50 전수 개수는 이번에 재확인하지 않았다.

**판정:** 과거 결과를 탐색 진단으로 읽는 목적에는 충분하다. 전면 차단으로 되돌릴 필요 없다. 그러나 schema 2라는 사실은 실제 두 채널을 모두 측정했다는 증거가 아니다. A017의 +3.707916/70은 기존 자료에 현재 legacy 규칙을 적용한 탐색 진단이지, schema 5 동등 계측이나 대표 승급 근거가 아니다. 직접 실행한 `tools/test_go2_a017_full_suite_contract.py`의 `[5]` 결과도 이 범위에서만 읽는다.

[잔여 한계] 이 수정은 **contract가 없는 자료의 예외**를 닫았다. 모든 현대 contract 문자열과 schema의 의미를 검증하는 일반 validator를 만든 것은 아니다(`Q/go2_fixed_eval_report.py:350–373`). 임의 JSON을 신뢰할 수 있다는 인증으로 확대하지 않는다.

## 4. 추가 발견 C5 — 유한하지 않은 높이가 정상 관측으로 인정됨

[증거·강] 실제 `_posture()`는 레이캐스트 지면값을 유한값으로 필터링하지만, root_z에서 계산한 height_rel의 유한성은 검사하지 않는다(`Q/go2_eval_telemetry.py:210–212,272–284`). `height_rel is not None`이면 측정으로 집계하고, `+inf >= FALL_HEIGHT_M`는 참이다.

실제 StubEnv의 root height만 +inf로 두고 2 env·1,000 step·중력 -1·속도 1·termination 0으로 실행:

```text
infinite_height survival_proxy=1.0 posture_coverage=1.0
posture_fall_verdict_ambiguous=False runner_rc=0
```

부록 A로 재현된다. runner의 유한값 검사는 survival·RMSE·coverage에만 적용돼 이 사례를 거절하지 않는다(`Q/server_run_go2_a017_full_suite.sh:217–242`).

**분류:** 측정 입력 유효성의 잔여 결함. C3·C4 수정 실패와는 다르다. 실제 A017/Pilot 데이터에 이 값이 발생했다는 증거는 없으며 [미확인]이다. 이번에 새 GPU 작업 전체를 무기한 막는 이유로 확대하지 않는다.

[제안] G-A027은 원시 CSV를 회수하는 측정 작업으로 진행하되, **점수 채택 전 root_z·지면 높이·상대 높이·중력·추종 채널의 유한성 검사를 필수로 적용**한다. 실제 nonfinite 입력이 발견되면 영향 case를 `INTERNAL_MEASUREMENT_INVALID`로 분리하고 그 수치를 승급에 사용하지 않는다. 계측기 후속 수정에서는 nonfinite 높이를 관측 결측으로 분류해 상·하한 검사에 넣는다. 조용히 정상값으로 치환하지 않는다.

## 5. NO_AUTO_SUBMIT 및 요청한 네 질문에 대한 답

1. **legacy 예외가 충분한가?** 탐색 진단용으로 수용. 현대 자료·대표 승급에 같은 예외를 쓰지 않는 경계를 직접 확인했다(§3).
2. **모호성 게이트가 관측률 1.0보다 나은 선택인가?** 이 내부 판정 모델에서는 합리적 선택. 극단 해석의 일치가 판단 가능한 결측을 구분한다. 운영 비용 우월성은 실제 결측 빈도 미측정이므로 확정하지 않는다(§2).
3. **NO_AUTO_SUBMIT의 네 층위 분리가 맞는가?** 동의한다. `F:859–871`은 코드상 백업 생략 경로, `F:874–880`은 model_best.pt/env.yaml/선택 report.html 묶음, `F:882–891`은 현재 시각 이름의 인증 POST다. `F:844–847`의 공식 수동 제출과 다르다. 이 스위치만으로 위반이라고 단정할 근거는 이 코드에서 나오지 않으며, 반대로 공식 자격 보장도 나오지 않는다. 나중 백업이 과거 서버 이력 복원이라는 주장도 성립하지 않는다. 본 감사에서 외부 POST는 실행하지 않았다.
4. **실행 준비가 해소됐는가?** C3·C4 차단 사유는 해소됐다. **새 고정 패키지의 데이터 수집에는 조건부 동의**, 대표 승급 자동화에는 동의하지 않는다. §6 조건을 명시적으로 적용한다.

## 6. 고정 실행 조건과 사후 순서

아래는 [제안]하는 감사 수용 조건이며 실제 서버 실행·예산 확인 사실이 아니다.

| 등급 | 시점·시간 박스 | 작업 및 판정 | 실패 시 대안 |
|---|---|---|---|
| 조사 | 시작 전 | 잔여 GPU 실측. 15시간은 전달받은 계획 입력일 뿐 현재 잔량 아님 | 확보 예산 내 회수 여유를 두고 범위 재산정 |
| 조사 | 새 실행 | ZIP SHA `f64706d61d877356f0223dca411a108a387e802e10617016dc5a951b9082f655` 고정, 두 정책 전체 재측정. 이전 결과와 섞지 않음 | 기존 결과 존재 시 먼저 회수; discard 옵션으로 우회하지 않음 |
| 조사 | 첫 10분 | 실제 case 진행·측정 source·coverage·ambiguity·로그와 저장 경로 확인 | 실패 로그와 원시 결과 회수. null을 0/1로 치환하거나 게이트 완화 금지 |
| 조사 | 약 1시간 45분 예상, 2시간 재평가 지점 | 러너 추정은 상한 아님. 예산·속도·회수 여유를 다시 판단 | 자동 타임아웃 보장은 없음. 중단 필요 시 현재 결과 보존·회수 우선 |
| 조사 | 종료 후, 추가 학습 전 | 두 arm 각각 69 summary, 원시 CSV·metadata·지문·로그·manifest, 요구 영상 7개 회수·검증 | PARTIAL 생성 실패 가능성을 전제로 KEEP 원시 파일도 회수 |
| 개선 | 로컬 판정 전, GPU 0 | C5 유한성 검사, 동일 source/DR/명령/seed·길이 대조. invalid case 제외로 전체 점수를 억지 완성하지 않음 | 영향 case 격리, 전체 측정은 미완료로 표시 |
| 개선 | 후보 승급 전, GPU 0 | 모든 case의 생존·추종 인자 기준 검사와 절대 점수/상대 개선 분리. 영상 확인 | worst-product case만 보는 자동 승급 결과 채택 금지 |

운영 근거: `Q/server_run_go2_a017_full_suite.sh:70–100`(manifest·기존 결과 보호·추정), `:109–115`(PARTIAL은 best effort), `:270–306`(resume 지문·case 검사). 패키지 계약 테스트 `[1]–[4]`에서 두 정책 전체 69건·영상 7개·학습 비호출·LF·bash 문법·ZIP manifest를 확인했다.

미수리 네 항목은 수집과 승급에 다르게 적용한다:
- all-case 인자 검사 부재: **승급 차단**, 수집 자체는 막지 않음. `Q/go2_tuning_eval_report.py:259–264`.
- 보고서 지문에 evaluator SHA/DR/argv 부재: **서로 다른 실행 결과를 자동 합치지 않음**. `Q/go2_fixed_eval_report.py:244–250`; 이번 고정 패키지의 두 arm과 회수 원자료를 별도 대조.
- PARTIAL/시간 상한/변경 resume: 운영 위험을 남겨 둠. 신버전 새 실행만 대상으로 하고 기존 결과는 먼저 회수. `Q/server_run_go2_a017_full_suite.sh:57,80–100,109–115,280–285`.
- FALL 환경변수 지문: `:274–276`에 포함돼 있으나 실제 서버 변경 재개 실증은 [미확인]. 이번에는 값 변경 없이 고정 실행.

## 7. 검증 내역과 한계

[증거] 요청서의 15개 고정 해시 및 요청서 sidecar를 디스크 파일과 대조해 모두 일치했다. 아래 3종을 직접 실행했고 모두 종료 코드 0이었다.

```text
python -B tools/test_go2_posture_survival_contract.py
python -B tools/test_go2_scoring_repair_contract.py
python -B tools/test_go2_a017_full_suite_contract.py
```

추가로 요청서 §6의 Python 재현 코드를 그대로 실행했다. §2·§3의 출력은 일치했다. 본 회신 부록 A는 별도의 추가 검사다. ZIP 검사는 기존 ZIP 및 메모리 payload 검사이며 원본 ZIP 재작성은 하지 않았다. Opus가 말한 전체 9종을 이번 감사가 모두 실행했다고 주장하지 않는다.

[미확인] GPU 잔량, 실제 G-A027 실행·회수, 서버 실패시 복구 실증, 공식 자격·점수, 최신 영상 행동, 과거 11건 전수 재판정, H1 대비 Go2 실패의 정량적 인과 비교. 이 회신의 수정 검증으로 이 항목들이 해결된 것은 아니다.

## 부록 A. 독립 추가 반례·타이머 검증

저장소 루트에서 Python으로 실행. 실제 생산 모듈과 테스트의 StubEnv를 사용하며 임시 디렉터리에만 쓴다. 첫 검사 성공 시 `EXHAUSTIVE_TIMER 6561`이 출력된다. 두 번째는 무해한 결측 허용, 세 번째는 C5 잔여 결함 재현이다.

```python
import ast, itertools, json, subprocess, sys, tempfile
from pathlib import Path
q = Path('workspace/training/quadruped')
sys.path.insert(0, str(q))
p = Path('tools/test_go2_posture_survival_contract.py')
m = ast.parse(p.read_text(encoding='utf-8'))
m.body = [x for x in m.body if isinstance(
    x, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))]
ns = {'__file__': str(p.resolve())}
exec(compile(m, str(p), 'exec'), ns)
tel = ns['tel']
c = object.__new__(tel.Collector)
c.step_dt = .2
assert tel.FALL_HOLD_S == .5
def verdict(seq):
    runs, fallen = {}, set()
    for x in seq:
        c._fall_timer(runs, fallen, 0, x)
    return bool(fallen)
count = 0
for seq in itertools.product([True, False, None], repeat=8):
    choices = [(True, False) if x is None else (x,) for x in seq]
    outcomes = {verdict(xs) for xs in itertools.product(*choices)}
    lo = verdict([True if x is None else x for x in seq])
    hi = verdict([False if x is None else x for x in seq])
    assert (lo == hi) == (len(outcomes) == 1)
    mid = verdict([x for x in seq if x is not None])
    assert int(lo) <= int(mid) <= int(hi)
    count += 1
print('EXHAUSTIVE_TIMER', count)
runner = (q / 'server_run_go2_a017_full_suite.sh').read_text(encoding='utf-8')
check = runner.split("python3 - \"$1\" <<'PYEOF'", 1)[1].split('\nPYEOF', 1)[0]
for kind in ['benign_missing', 'infinite_height']:
    env = ns['StubEnv'](num_envs=2,
        height=float('inf') if kind == 'infinite_height' else .306,
        grav_z=-1., speed=1.)
    with tempfile.TemporaryDirectory() as td:
        obj = tel.Collector(Path(td), 1000)
        obj.attach(env)
        if kind == 'benign_missing':
            obj._posture = lambda *_: ([-1., -1.],
                [None, None] if obj.step == 120 else [0., 0.])
        z = ns['FakeTensor'](ns['np'].zeros(2))
        for _ in range(1000):
            obj.record(env, (None, None, z, z, {}))
        path = Path(td) / 'summary.json'
        s = json.loads(path.read_text(encoding='utf-8'))
        rc = subprocess.run([sys.executable, '-c', check, str(path)],
                            capture_output=True).returncode
        print(kind, {k: s[k] for k in ['survival_proxy', 'posture_coverage',
              'posture_fall_verdict_ambiguous']}, 'runner_rc', rc)
```
