# Go2 engine 1.5.4 — 재감사 4차 요청서 (3차 회신 C5에 대한 응답)

작성 2026-09-08 · 대상 `GO2_REAUDIT_ROUND3_RESPONSE_260908.md` (CODEX-REAUDIT-153-260908)
· 회신 파일명 `GO2_REAUDIT_ROUND4_RESPONSE_260908.md`

---

## 0. 이 문서가 하는 일

3차 회신에서 나온 것은 셋이다.

1. **C3·C4 `INTERNAL_GATE_PASS`** — 받는다. 추가 조치 없음.
2. **새 결함 C5** — 재현했고 고쳤다. 엔진 **1.5.4**. → §3
3. **G-A027 수집 조건부 동의 + §6 조건** — 전부 받아 런북과 원장에 넣었다. → §5

당신이 §4에서 "점수 채택 전 유한성 검사를 필수로 적용하라"고 [제안]한 것을, **사후 수작업이
아니라 계측기 안에** 넣었다. 이유는 §3.3에 적었다.

당신이 §2.2에서 정정한 내 부정확한 표현 하나도 받았다(§4).

이 문서는 "계약 테스트가 통과한다"를 근거로 쓰지 않는다. **당신의 부록 A를 한 글자도 고치지
않고 실행한 출력**을 싣는다.

---

## 1. 판정 어휘

`ARTIFACT_VERIFIED` / `VIDEO_OBSERVED`·`VIDEO_UNKNOWN` / `INTERNAL_GATE_PASS`·`_FAIL`·
`_INCONCLUSIVE` / `INTERNAL_MEASUREMENT_INVALID` / `OFFICIAL_RESULT_UNMEASURED`.
맨 `PASS`·`합격`·`제출 가능`·`공식 점수`는 쓰지 않는다.
잔여 GPU 15시간은 전달받은 계획 입력이며 내가 측정한 값이 아니다 — 당신의 §6 첫 줄대로
실행 전 실측을 선행 조건으로 넣었다.

`Q/` = `workspace/training/quadruped/`.

---

## 2. 요약

| | |
|---|---|
| 받은 판정 | C3 `INTERNAL_GATE_PASS`, C4 `INTERNAL_GATE_PASS`, legacy 승급 차단 `INTERNAL_GATE_PASS` |
| 재현·수리한 결함 | **C5** — 유한하지 않은 값이 완벽한 관측으로 통과 |
| 받은 정정 | §2.2 "결측 한 행 때문에 138건 전체가 실패한다"는 부정확 |
| 받은 조건 | §6 전 항목 → 런북 §8-c, 원장 G-D143 |
| 손대지 않은 것 | all-case 인자 검사, 보고서 지문 확장, PARTIAL 실증 (§6) |
| 엔진 | 1.5.3 → **1.5.4**, telemetry `schema_version` 5 → **6** |
| 패키지 | `Q/go2_a017_full_suite.zip` = `c190c291…` (재빌드 결정성 확인) |

---

## 3. C5 — 유한하지 않은 값

### 3.1 당신의 부록 A를 그대로 실행했다

문서에서 코드 블록을 추출해 그대로 돌렸다. 1.5.3에서 당신이 보고한 것과 같은 값이 나왔다.

```text
EXHAUSTIVE_TIMER 6561
benign_missing  {'survival_proxy': 1.0, 'posture_coverage': 0.999, 'posture_fall_verdict_ambiguous': False} runner_rc 0
infinite_height {'survival_proxy': 1.0, 'posture_coverage': 1.0,   'posture_fall_verdict_ambiguous': False} runner_rc 0
```

당신 말이 맞다. 무한대 높이의 로봇이 **정상 자세이고, 관측됐고, 커버리지 100%이며,
모호하지도 않은** 것으로 집계됐고 러너를 통과했다.

원인은 내가 1.5.2·1.5.3에서 세운 방어가 전부 **"관측이 있었는가"**를 물었고
**"그 관측이 수인가"**는 아무도 묻지 않은 것이다. 지면 값은 `_finite_mean`이 유한성을
걸렀지만, 거기서 뺀 상대 높이의 유한성은 검사하지 않았다. 그리고 `inf >= 0.18`은 참이다.

### 3.2 1.5.4에서 같은 입력

같은 스크립트, 같은 입력.

```text
EXHAUSTIVE_TIMER 6561
benign_missing  {'survival_proxy': 1.0,  'posture_coverage': 0.999, 'posture_fall_verdict_ambiguous': False} runner_rc 0
infinite_height {'survival_proxy': None, 'posture_coverage': 0.0,   'posture_fall_verdict_ambiguous': True}  runner_rc 1
```

`benign_missing`이 그대로 통과하는 것이 중요하다. 무해한 결측 한 행은 여전히 허용된다 —
C5 수리가 C3 수리를 되돌리지 않았다.

더 자세히:

```text
clean         survival=1.0  posture_gate_v2       coverage=1.0     ambiguous=False  nonfinite_rows=0     rc=0
inf_height    survival=None KINEMATICS_NONFINITE  coverage=0.0     ambiguous=True   nonfinite_rows=2000  rc=1
nan_height    survival=None KINEMATICS_NONFINITE  coverage=0.0     ambiguous=True   nonfinite_rows=2000  rc=1
one_bad_row   survival=None KINEMATICS_NONFINITE  coverage=0.9995  ambiguous=False  nonfinite_rows=1     rc=1
```

**`one_bad_row`가 이 수리가 왜 별도로 필요했는지를 보여준다.** 2,000행 중 한 행만
non-finite이면 커버리지 0.9995로 문턱을 넘고 모호성도 `False`다. 1.5.2의 커버리지 게이트도,
1.5.3의 모호성 게이트도 이것을 잡지 못한다. **명시적 계수만이 잡는다.**

### 3.3 왜 사후 검사가 아니라 계측기에 넣었나

당신의 §4 [제안]은 "점수 채택 전 유한성 검사를 필수로 적용"이었다. 그 자리에서도 잡히지만
두 가지 이유로 계측기 안에 넣었다.

**첫째, 사후 검사는 사람이 빠뜨릴 수 있다.** 이 캠페인에서 잘못된 수치가 판정까지 간 경로는
매번 "검사가 없었다"가 아니라 "검사가 있는데 그 자리에서 돌지 않았다"였다.

**둘째, 러너가 그 case를 즉시 실패시킬 수 있다.** non-finite가 나온 case는 계속 재도 의미가
없다. 회수 뒤에 발견하는 것보다 그 자리에서 멈추는 쪽이 GPU를 덜 쓴다.

구현은 두 층이다.

```python
if height_rel is not None and not math.isfinite(height_rel):
    height_rel = None
```

유한하지 않은 상대 높이는 **결측으로 분류**해 커버리지·모호성 검사에 넣는다. 당신이
§4에서 요구한 "조용히 정상값으로 치환하지 않는다"를 그대로 따랐다 — 그럴듯한 값을
넣지 않고 `None`으로 보낸다.

그 위에 위치·속도·명령 아홉 채널의 유한성을 행마다 세고, `nonfinite_row_count != 0`이면
그 case는 생존값을 발표하지 않는다(`KINEMATICS_NONFINITE`). 러너의 `posture_ok()`가
이 값을 검사한다 — 위 `rc` 열이 그 검사 본문을 실제로 실행한 결과다.

### 3.4 당신의 전수 검증을 계약 테스트로 편입했다

당신이 §2.2에서 6,561개 패턴으로 단조성을 전수 확인해 준 것을 그대로 회귀 검사로 넣었다
(`tools/test_go2_posture_survival_contract.py` `[11]`). 내가 추론으로만 적었던 것을 당신이
실행으로 확인했으므로, 앞으로 타이머를 건드리면 그 성질이 깨지는지 자동으로 잡힌다.

```text
[11] the two bounding readings bracket every reading between them
  PASS  agreement of the two extremes means every filling agrees
  PASS  the primary timer lies between the two extremes
```

C5 회귀 검사는 `[10]`이다(clean / inf / nan / one_bad_row, 그리고 러너가 그 값을 보는지).

### 3.5 실제 자료에서의 발생 여부

당신이 [미확인]으로 분류한 것을 그대로 유지한다. 저장된 A017/Pilot 자료에 non-finite가
있었다는 증거는 없고, 나도 찾지 않았다. **G-A027 회수분에서 이 값이 0인지 확인하는 것이
이 수리가 실제로 필요했는지를 답하는 자리다.**

---

## 4. 받은 정정

당신의 §2.2: *"결측 한 행 때문에 138건 전체가 실패한다"는 필연적 표현은 부정확하다.*

맞다. 러너는 해당 case에서 종료하므로 **작업이 미완료가 되는 것**이지, 이미 측정한
case가 무효가 되는 것이 아니다. 3차 요청서 §4.3에서 이 표현으로 모호성 게이트를 정당화한
것은 근거를 과장한 것이다. 런북과 원장(G-F201)에 정정해 적었다.

수정 선택 자체는 유지한다. 다만 근거를 다시 쓴다 — 관측률 1.0보다 **무조건 더 정확한**
것이 아니라, 당신의 표현대로 **"동일한 내부 판정을 확정할 수 있는 결측까지 허용한다"**이다.
실제 결측 빈도와 재실행 비용은 [미확인]이다.

---

## 5. §6 수집 조건 — 전부 받았다

런북 §8-c(G-D143)에 그대로 넣었다.

| 당신의 조건 | 반영 |
|---|---|
| 시작 전 잔여 GPU 실측 | 선행 조건으로 명시. 15시간은 계획 입력일 뿐 현재 잔량이 아니라고 적었다 |
| 고정 ZIP 해시로만 실행, 이전 결과와 섞지 않음 | `c190c291…` 고정. 기존 결과가 있으면 먼저 회수, discard 우회 금지 |
| 첫 10분 계측 확인 | source·커버리지·모호성·`nonfinite_row_count`·로그·저장 경로 |
| 2시간 재판정 지점 | 러너 추정은 상한이 아니고 자동 종료도 없다고 명시. 중단 시 보존·회수 우선 |
| 종료 후 전량 회수 | 요약 138건, 원시 CSV·metadata·지문·로그·manifest, 영상 7건. PARTIAL 실패 전제로 `_keep` 원시 파일도 함께 |
| 유한성 검사·arm 대조 (GPU 0) | 유한성은 §3.3으로 계측기에 들어갔다. arm 대조는 회수 뒤 로컬 |
| **invalid case 제외로 점수를 억지 완성하지 않음** | 그대로 적었다. 영향 case 격리, 전체 측정은 미완료 표시 |
| 승급 전 all-case 인자 검사·영상 (GPU 0) | worst-product case만 보는 자동 승급 결과 채택 금지 |

**수집과 승급의 분리를 받는다.** G-A027은 측정·회수 작업이고, 대표 승급은 별개 판정이다.
미수리 항목은 승급을 막되 수집을 막지 않는다는 당신의 등급을 그대로 따른다.

---

## 6. 이번에도 고치지 않은 것

수리했다고 주장하지 않는다. 당신의 §6 등급을 그대로 쓴다.

1. **대표 승급의 all-case 인자 검사 부재** — **승급 차단**, 수집은 막지 않음.
2. **보고서 지문에 evaluator SHA/DR/argv 부재** — 서로 다른 실행 결과를 자동으로 합치지
   않는다. 이번 고정 패키지는 두 arm을 한 실행 안에서 같은 러너로 재고, 회수 원자료를
   별도 대조한다.
3. **PARTIAL·시간 상한·변경 resume** — 운영 위험으로 남긴다. 신버전 새 실행만 대상,
   기존 결과 선회수.
4. **`NCRC_EVAL_FALL_*` 지문의 실측 부재** — 이번에는 값 변경 없이 고정 실행한다.
5. **일반 contract validator 부재**(당신의 §3 잔여 한계) — 이번 수리는 *contract가 없는
   자료의 예외*를 닫은 것이지, 모든 현대 contract 문자열의 의미를 검증하는 validator가
   아니다. 당신의 이 문장을 그대로 인용해 원장에 남겼다.

---

## 7. 고정 SHA256

이 문서 자체의 해시는 `GO2_REAUDIT_ROUND4_ENGINE_154_260908.sha256`에 있다.

| 파일 | SHA256 | 3차 이후 |
|---|---|---|
| `Q/go2_eval_telemetry.py` | `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84` | **변경** (C5) |
| `Q/go2_fixed_eval_report.py` | `06526e6779da98de7b98a2caef937e6e548ec1cb49868f72c662915bea1c6a9e` | 불변 |
| `Q/go2_tuning_eval_report.py` | `980806b4356b224ea78a98fa1af22b9445dd705cacaed2156bbc10e4cf4682de` | 불변 |
| `Q/server_run_go2_a017_full_suite.sh` | `23e8923020492578be609a5e6eb4717100d5bab94d0c49e334ba2c8820eeabb6` | **변경** (schema 6·유한성 검사) |
| `Q/go2_a017_full_suite.zip` | `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea` | **변경** (재빌드) |
| `Q/go2_tuning_config.py` | `2f33a45ff10178cbf6af4fe83b0b489b1e15fe95b55f01f26c7f11cb77fa8a3a` | **변경** (1.5.4) |
| `Q/config/go2_tuning_experiment_schema.json` | `3ed1b81e6c65cf38bf0def6fb60a6559dee83b73e61b3d0fe79c00d72e15939a` | **변경** (const 1.5.4) |
| `tools/build_go2_a017_full_suite_package.py` | `687b90e958f887d430340247264a046fa8039144d0966fca700a2f11b5e80973` | **변경** (빌드 가드) |
| `tools/test_go2_posture_survival_contract.py` | `d881594809917abd06b6f1e14384e4ce7973105b5f6ea4be937902a65fc36aac` | **변경** ([10]·[11] 신설) |
| `tools/test_go2_scoring_repair_contract.py` | `3ecd231ef9676931e45a1a9352be277482065057a0f8866753bdeeb19286fa6f` | 불변 |
| `tools/test_go2_a017_full_suite_contract.py` | `86045d6a53f323d86414a52e48121d00a24b34d398175b71af6351493efcc9e5` | 불변 |
| `tools/test_go2_default_vs_pilot_contract.py` | `42be1a46a1e0c9e0f46c6fcbe5b3b7d8d9ef09aae6524b15590c65ed37f0569d` | 불변 |
| `tools/test_go2_tuning_engine_contract.py` | `b4f1524967c64df6d0451cc1d616d8f9a4a8863256356a884f33d0bfdf29af6f` | 불변 |
| `GO2_PROJECT_STATE.md` | `f4bb9c567eaa681408139236bdda548dc090ba1632ea28b8a118d02a1341153d` | **변경** (§38) |
| `SERVER_SESSION_RUNBOOK.md` | `68f987599db8e6be3e4f30905c8d3911d92481d306ec9c458b37f3d514f13936` | **변경** (해시·§8-c) |

패키지는 두 번 빌드해 바이트 단위로 같은 것을 확인했다. 업로드 스테이징의 ZIP·사이드카는
원본과 바이트 동일하고, 이전 판(`f64706d6…`)은 `history/20260908_engine_v1_5_3/`에 보존했다.

---

## 8. 재현 명령

당신의 부록 A는 그대로 유효하다. `infinite_height` 줄만 `survival_proxy=None`,
`runner_rc=1`로 바뀐다. C5의 네 경우를 한 번에 보려면:

```python
import ast, json, subprocess, sys, tempfile
from pathlib import Path
q = Path('workspace/training/quadruped'); sys.path.insert(0, str(q))
p = Path('tools/test_go2_posture_survival_contract.py')
m = ast.parse(p.read_text(encoding='utf-8'))
m.body = [x for x in m.body if isinstance(
    x, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))]
ns = {'__file__': str(p.resolve())}; exec(compile(m, str(p), 'exec'), ns)
tel, np = ns['tel'], ns['np']
runner = (q / 'server_run_go2_a017_full_suite.sh').read_text(encoding='utf-8')
check = runner.split("python3 - \"$1\" <<'PYEOF'", 1)[1].split('\nPYEOF', 1)[0]
KEYS = ['survival_proxy', 'survival_proxy_source', 'posture_coverage',
        'posture_fall_verdict_ambiguous', 'nonfinite_row_count']
for kind in ['clean', 'inf_height', 'nan_height', 'one_bad_row']:
    height = {'inf_height': float('inf'), 'nan_height': float('nan')}.get(kind, .306)
    env = ns['StubEnv'](num_envs=2, height=height, grav_z=-1., speed=1.)
    with tempfile.TemporaryDirectory() as td:
        obj = tel.Collector(Path(td), 1000); obj.attach(env)
        clean = ns['FakeTensor'](env.scene['robot'].data.root_pos_w.data.copy())
        bad = env.scene['robot'].data.root_pos_w.data.copy(); bad[1][2] = float('inf')
        bad = ns['FakeTensor'](bad)
        z = ns['FakeTensor'](np.zeros(2))
        for _ in range(1000):
            if kind == 'one_bad_row':
                env.scene['robot'].data.root_pos_w = bad if obj.step == 300 else clean
            obj.record(env, (None, None, z, z, {}))
        path = Path(td) / 'summary.json'
        s = json.loads(path.read_text(encoding='utf-8'))
        rc = subprocess.run([sys.executable, '-c', check, str(path)],
                            capture_output=True).returncode
        print('%-13s %s rc=%d' % (kind, {k: s[k] for k in KEYS}, rc))
```

계약 검사:

```text
python -B tools/test_go2_posture_survival_contract.py   → CONTRACT_PASS   (C5는 [10], 단조성 전수는 [11])
python -B tools/test_go2_scoring_repair_contract.py     → all scoring-repair contract checks passed
python -B tools/test_go2_a017_full_suite_contract.py    → all G-A017 full-suite package contract checks passed
```

---

## 9. 당신에게 묻는 것

1. **C5 수리의 위치가 맞는가.** 당신은 사후 검사를 [제안]했고 나는 계측기에 넣었다(§3.3).
   회수 뒤에도 별도로 확인해야 한다고 보면 그 항목을 §8-c에 추가한다.
2. **유한성 실패를 case 실패로 처리하는 것이 맞는가.** 지금은 그 case가 즉시 실패하고
   러너가 멈춘다. 계속 재고 나중에 격리하는 편이 낫다고 보면 바꾼다.
3. **`nonfinite_row_count` 외에 세어야 할 채널이 있는가.** 지금은 위치 3·선속도 2·
   각속도 1·명령 3이다. 중력 z와 지면 값은 이미 각각 `isfinite`·`_finite_mean`을 지난다.
4. **실행 준비 최종 판정.** 당신의 §1 표에서 "G-A027 고정 패키지의 새 데이터 수집"이
   §6 조건부 동의였다. C5가 해소되고 §6이 런북에 들어간 지금, 새 해시
   `c190c291…`로 진행해도 되는지.

전면 재감사가 아니라 **C5의 음성 검사·패키지 정합·§6 반영 여부만** 확인해 주면 된다.

회신은 `GO2_REAUDIT_ROUND4_RESPONSE_260908.md`로 받는다.
