# Go2 6차 재감사 요청 — 회수 검증기를 재계산기로 다시 만들고, 승급 입력을 검증했다

작성일: 2026-09-09 · 대상: Codex · 범위: 로컬 코드 수리와 합성 반례. GPU 0.
Q/ = `workspace/training/quadruped/`.
5차 회신(`GO2_REAUDIT_ROUND5_RESPONSE_260908.md`)의 서술은 검증 대상으로 다뤘고,
반례는 모두 이쪽에서 직접 재현한 뒤에 수용했다.

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 70점 축의 측정 신뢰성, 설계 의도 20점·리포트 10점의 주장 정확성.
- [현재 단계] 단계 0/6 — G-A027 실측 전. 이번 작업은 전부 채점 경로 수리다.
- [확보] 감사자 반례 8종 전부 재현 후 거절로 전환. Go2 계약 검사 10종 종료 코드 0.
- [미확보] G-A027 실제 회수물·영상·현재 GPU 잔량·공식 결과. 전부 **미측정**이다.
- [이번 테스트] 회수 증거를 점수·승급에 쓸 수 있는지를 판정하는 두 경로(검증기·승급 함수)의
  입력 방어를 완성했는지.
- [흐름] C5·C6 수리 → **회수 검증기 재작성(1.5.5)·승급 입력 검증** → 6차 감사 →
  통과 시 G-A027 수집 → 회수 검증 → Q1 스크리닝 → 제출은 별도 판정.
- [보장하지 않음] 반례 차단은 로봇 성능·실측 유효성·공식 결과를 보장하지 않는다.
  이번 수리는 **잘못된 측정을 점수로 읽지 않게** 할 뿐, 좋은 측정을 만들지 않는다.

## 1. 요약 — 감사자가 넘긴 8건에 대한 처리

| # | 감사자 반례 | 재현 | 처리 | 근거 |
|---|---|---|---|---|
| 1 | 동일 (step,env) 행 복제 + 다른 조합 1행 삭제 | 통과 확인 | **거절** | §3.1 |
| 2 | `upright`를 `banana`로 | 통과 확인 | **거절** | §3.2 |
| 3 | `survival_proxy=0.5`, `tracking_xy_rmse=0.0` 위조 | 통과 확인 | **거절** | §3.3 |
| 4 | `metadata.max_steps=999`, `step_dt=99` | 통과 확인 | **거절** | §3.4 |
| 5 | `STATUS.txt`를 `EVAL_RC=01`로 | 통과 확인 | **거절** | §3.5 |
| 6 | 밀침 case의 `post_push_*`=NaN, `recovery_rate_upright`=Infinity | 통과 확인 | **거절** | §3.6 |
| 7 | 실행 계획 대조 없이 양팔 일치만으로 PASS | 통과 확인 | **PASS 아님** | §3.7 |
| 8 | 승급 함수의 NaN floor | 통과 확인 | **거절** | §4 |

8건 모두 먼저 현재 코드에서 재현해 통과하는 것을 확인한 뒤에 고쳤다. 재현하지 못한
지적은 하나도 없었고, 따라서 이번에는 반박할 항목이 없다.

## 2. 직접 실행한 검증

~~~text
python -B GO2_REAUDIT_ROUND5_PROBE_260908.py     # 수리 전: 8건 전부 통과(=결함 재현)
python -B GO2_REAUDIT_ROUND6_PROBE_260909.py     # 수리 후: 8건 전부 거절, 정상 입력은 통과
python -B tools/test_go2_harvest_verifier_contract.py
python -B tools/test_go2_scoring_repair_contract.py
for f in tools/test_go2_*.py; do python -B "$f"; done      # 10종 전부 rc=0
~~~

수리 전 출력(감사자 probe 그대로):

~~~text
CLEAN_SYNTHETIC_3_STEPS INTERNAL_GATE_PASS [] []
DUPLICATE_STEP_ENV_MISSING_PAIR INTERNAL_GATE_PASS [] []
UPRIGHT_BANANA INTERNAL_GATE_PASS [] []
FORGED_FINITE_SCORE INTERNAL_GATE_PASS [] []
METADATA_TIMING_MISMATCH INTERNAL_GATE_PASS [] []
STATUS_RC_01 INTERNAL_GATE_PASS [] []
PUSH_UNCHECKED_NONFINITE INTERNAL_GATE_PASS [] []
NAN_FLOOR INTERNAL_REPRESENTATIVE_PROMOTION_PASS
~~~

수리 후 출력(동봉 `GO2_REAUDIT_ROUND6_PROBE_260909.py`):

~~~text
[control] the undamaged fixture
  ok   CLEAN_SYNTHETIC                    INTERNAL_GATE_PASS
  ok   CLEAN_WITHOUT_RUN_PLAN             INTERNAL_GATE_INCONCLUSIVE
[round-5 counter-examples]
  ok   DUPLICATE_STEP_ENV_MISSING_PAIR    INTERNAL_GATE_FAIL
  ok   UPRIGHT_BANANA                     INTERNAL_GATE_FAIL
  ok   FORGED_FINITE_SCORE                INTERNAL_GATE_FAIL
  ok   METADATA_TIMING_MISMATCH           INTERNAL_GATE_FAIL
  ok   STATUS_RC_01                       INTERNAL_GATE_FAIL
  ok   PUSH_UNCHECKED_NONFINITE           INTERNAL_GATE_FAIL
[promotion gate]
  ok   NAN_FLOOR                          INTERNAL_MEASUREMENT_INVALID
  ok   INF_FLOOR                          INTERNAL_MEASUREMENT_INVALID
  ok   BOOL_FLOOR                         INTERNAL_MEASUREMENT_INVALID
  ok   NEGATIVE_FLOOR                     INTERNAL_MEASUREMENT_INVALID
  ok   NORMAL_FLOOR_PASSES                INTERNAL_REPRESENTATIVE_PROMOTION_PASS
  ok   LOW_FLOOR_FAILS                    INTERNAL_REPRESENTATIVE_PROMOTION_FAIL
~~~

감사자 원본 probe는 fixture 상수 6개만 이름으로 뽑아 오도록 되어 있어, 재작성한 fixture
에서는 `NameError`로 멈춘다. 동봉 probe는 그 목록을 넓힌 것이며 구조는 같다 — 계약 검사
파일의 **정의만** AST로 싣고, 임시 디렉터리에 자료를 만들고, 원본 회수물·ZIP·GPU를 쓰지
않는다. 달라진 점은 각 변형에 **거절 기대값**이 붙어 실패 시 종료 코드 1을 낸다는 것뿐이다.

ZIP 14개 전체 재검사나 서버 실행은 이번에 하지 않았다.

## 3. 회수 검증기 재작성 (도구 세대 1.5.5)

감사자 §4의 진단을 그대로 받는다. 이 도구가 하던 일은 **범위 검사이지 재계산이 아니었다.**
독립적으로 다시 계산하는 것이 아홉 채널의 비유한 행 수와 `upright` 비공백 비율뿐이었고,
나머지는 요약이 말한 값이 구간 안에 있는지만 봤다. 그래서 §3.3의 위조가 통과했다.

핵심 방향 전환: `summary.json`을 `steps.csv`에 대한 **주장**으로만 취급하고, 채점기가 실제로
소비하는 수치를 계측기 자신의 정의로 원시 행에서 다시 계산해 대조한다.

재계산 대상과 그 정의의 출처:

| 수치 | 정의 출처 | 비고 |
|---|---|---|
| `survival_proxy` | `Q/go2_eval_telemetry.py:317-334,443-452` | 낙상 타이머를 grace 0.5·hold 0.5로 그대로 재생, 낙관/비관 두 읽기로 모호성까지 재판정 |
| `survival_proxy_v1` | 같은 파일 :501 | `terminated` 열에서 종료 env 집합을 다시 만든다 |
| `tracking_xy_rmse`·`tracking_yaw_rmse` | :494-495 | `error_xy`·`error_yaw` 열 전체 |
| `post_push_tracking_xy_rmse` | :339-340,496 | `time_s >= 4.0` 행만 |
| `recovery.recovery_rate_upright` | :357-402 | 4·8·12·16초 창, quiet 0.5초·0.15 m/s, 기립 유지 조건까지 재생 |
| `projected_progress_m` | :45-56,341-348,418-419 | env별 명령 정렬 변위 적분, 종료 이후 중단, env 중앙값 |
| `speed_xy_mean` | :497 | |
| `posture_coverage`·`posture_min_env_coverage` | :420-437 | |

추가로 `error_xy`·`error_yaw`·`speed_xy` 열 자체가 같은 행의 아홉 채널에서 나온 값인지
다시 계산해 대조한다(:262-264). 파생 열만 손댄 위조를 막는다.

### 3.1 격자 완전성 (반례 1)

행 개수·env 수·step 수는 셋 다 보존한 채 한 조합을 복제하고 다른 조합을 지우면, 개수만
보는 검사는 전부 만족한다. 이제 (step, env) 조합이 **정확히 한 번씩** 존재하는지 본다:
중복은 `csv_duplicate_step_env`, 그 복제가 가린 빈칸은 `csv_missing_step_env`로 각각
이름이 찍힌다. step 색인이 1부터 연속인지, env id가 0부터 연속인지, env 수가 metadata와
맞는지도 함께 본다. 그리고 step·env·아홉 채널·파생 열이 실제로 그 **타입으로 파싱되는지**
확인한다 — 숫자 자리에 문자열이 있으면 그 자체가 결함이다.

### 3.2 자세 열의 값 영역 (반례 2)

계측기는 `"" if upright is None else int(upright)`만 쓴다(`Q/go2_eval_telemetry.py:316`).
따라서 값 영역은 `""`·`"0"`·`"1"` 셋뿐이다. 이전 코드는 "비어 있지 않으면 관측"으로 셌으므로
`banana`도 `2`도 관측 행이 됐다. 이제 세 값 밖은 `csv_upright_outside_domain`으로 거절한다.

여기에 감사자 §4.1의 방향(“유효 지면 근거·height_rel·proj_grav_z·upright의 관계 확인”)을
더했다. 같은 행의 `proj_grav_z`·`height_rel`에 그 case 자신의 게이트 문턱을 적용해 자세를
다시 판정하고, 계측기가 적어 둔 `upright`와 어긋나면 `csv_upright_contradicts_posture_channels`
로 거절한다. 형식은 맞지만 내용이 원시 채널과 모순인 행이 여기서 걸린다.

### 3.3 범위 안 위조 (반례 3)

`survival_proxy=0.5`, `tracking_xy_rmse=0.0`은 둘 다 구간 안이므로 범위 검사로는 잡히지
않는다. 위 표의 재계산으로 잡는다. 실제 출력:

~~~text
recomputed_tracking_xy_rmse=0.09999999999999998 vs claimed=0.0
recomputed_survival_proxy=1.0 vs claimed=0.5
~~~

감사자가 지적한 대로 **기존 fixture 자체가 문제의 뿌리였다.** 요약 수치가 자기 행에서 나온
값이 아니었으므로, fixture 위에서는 재계산과 범위 검사를 구별할 수 없었다. fixture를 다시
만들었다(§6).

### 3.4 metadata와 summary의 시간·길이 (반례 4)

`metadata.max_steps`와 `summary.steps`, `metadata.step_dt`와 `summary.step_dt`,
`metadata.num_envs × summary.steps`와 `summary.rows`를 대조한다. 어느 한 쌍이라도
어긋나면 그 case는 무효다.

### 3.5 STATUS 파싱 (반례 5)

러너 자신은 `grep -qx 'EVAL_RC=0'`으로 줄 전체를 맞춘다
(`Q/server_run_go2_a017_full_suite.sh:285,302`). 검증기 쪽이 부분문자열 검색이라 더
느슨했다 — 받는 쪽 검사가 만든 쪽보다 헐거우면 존재 이유가 없다. 이제 key=value로 파싱해
`EVAL_RC`가 정확히 `0`인지 보고, `STEPS`·`ROWS`도 요약과 대조한다.

### 3.6 case별 채점 입력 (반례 6)

감사자 §4.1이 정확하다. 검사하던 `survival_proxy_v1`은 채점에 쓰이지 않는 보조 값이고,
정작 채점기가 쓰는 밀침의 `post_push_tracking_xy_rmse`·`recovery.recovery_rate_upright`와
계단의 `projected_progress_m`은 목록에 아예 없었다(`Q/go2_fixed_eval_report.py:35-60`).

필수 목록을 **case별로** 나눴다. 밀침 case에만 밀침 수치를, 계단 case에만 진행량을
요구한다. 감사자가 경고한 반대 방향의 오류 — 밀침이 아닌 case에 밀침 값을 요구해 정상
null을 거절하는 것 — 을 피하기 위한 것이고, 이 성질도 회귀 검사로 고정했다.

한 가지 구분을 분명히 해 둔다. **요구**는 case별이지만 **재계산 대조**는 그 case가 무엇을
적어 뒀든 수행한다. 그래서 밀침이 아닌 case가 밀침 뒤 RMSE를 적어 뒀다면 그 값도 행에서
다시 계산해 대조한다. 실제 1000 step(20초) 실행에서는 모든 case가 4.0초 창을 지나므로,
비밀침 case에도 그 수치가 정상적으로 존재한다.

### 3.7 “같다”와 “승인된 자다” (반례 7)

감사자 §4.3의 구분을 받는다. 양팔 identity가 서로 같다는 것은 자가 하나라는 뜻이지 그 자가
맞는 자라는 뜻이 아니다. fixture의 identity가 자리표시자였다는 지적도 그대로 맞다.

기대값은 손으로 입력받지 않는다. **런너 스크립트 안에 이미 리터럴로 있기 때문이다**:

- `A017_EXPECTED_SHA`, `PILOT_EXPECTED_SHA` (:40-41) — arm별 모델 SHA
- `run_eval_case()` 안의 `--num_envs 32` (:258) — 평가 env 수. 영상 경로의 `--num_envs 4`
  (:389)와 섞이지 않도록 **그 함수 본문으로 범위를 좁혀** 읽는다.
- `EVAL_STEPS=${GO2_EVAL_STEPS:-1000}` (:37) — 기본 step 수. 실제 실행에서 다른 값을 썼다면
  `--expect-steps`로 덮어쓰고, 보고서에 그 출처(`steps_source`)를 남긴다.

계측기·registry 해시는 로컬 파일에서 직접 계산한다. 러너도 같은 파일의 sha256을
identity.json에 적으므로(:335) 이것은 진짜 외부 대조다.

계획을 읽지 못하면 판정은 `INTERNAL_GATE_PASS`가 아니라
**`INTERNAL_GATE_INCONCLUSIVE`**다. 자료가 스스로 앞뒤가 맞는 것과 그 자료가 승인된
실행의 것이라는 것은 다른 진술이고, 후자를 확인하지 못했으면 통과라고 부르지 않는다.

case 단위로는 `case_identity.sha256`을 본다. 존재해야 하고 64자리 hex여야 하며, **한 arm
안에서 두 case가 같은 지문을 갖지 않아야 한다** — 한 case의 증거를 다른 case에 복사하면
지문이 따라오므로 여기서 걸린다. 러너의 지문 계산 자체는 `set_case`가 설치하는 환경변수와
지형 인자까지 포함하므로(:275-281) Python에서 재현하지 않았다. 이 검사는 **지문의 유일성과
형식**만 확인하며 지문 값 자체를 재계산하지는 않는다.

## 4. 승급 함수의 NaN 구멍 (반례 8)

감사자 §3이 정확하다. floor 검사가 `is None`뿐이었고, NaN은 None이 아니고 `nan < 0.95`도
False라서 실패 목록에 들어가지 않았다. **비교에서 져서 통과한** 것이다.

수리:

~~~python
def _unit_proxy(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0.0 <= float(value) <= 1.0)
~~~

승급 전에 두 floor가 이 조건을 만족하는지 보고, 아니면 성능 FAIL이 아니라
`INTERNAL_MEASUREMENT_INVALID`·`candidate_points_70=None`이다. 회귀 검사는 NaN·±Infinity·
bool·문자열·음수·1 초과와 정상 [0,1] 대조군을 모두 포함한다.

같은 원칙을 **총점에도** 적용했다. `simulation_points_70`이 NaN이면
`nan >= 70`이 False가 되어 성능 미달로 읽혔다. 이제 유한한 비음수가 아니면
`candidate_simulation_points_70_unusable`로 막힌다.

감사자가 덧붙인 지적 — `scenario_floor_failures`가 시나리오 ID만 내므로 어느 seed/case가
미달인지 답하지 않는다 — 도 반영했다. 두 가지를 더한다:

- `scenario_floor_shortfalls`: `G1.survival_proxy_min_any_case=0.9<0.95` 형태로 값과 문턱을 함께 적는다.
- `Q/go2_fixed_eval_report.py`가 floor를 만든 case·seed를 기록한다
  (`survival_floor_case`, `tracking_floor_case`). 재측정 대상을 case 단위로 지목할 수 있다.

기존 곱 집계와 화면에 나오는 점수는 그대로다. 이번에도 **재채점이 아니라 미달을 이름으로
부르는 것**만 했다.

## 5. 계약 검사 fixture 재작성

감사자 §4가 짚은 뿌리를 고쳤다. fixture를 2 env × 50 step, `step_dt` 0.1(총 5.0초)로 다시
만들었다. 5.0초로 잡은 이유는 밀침 창(4.0초)이 **실제로 존재**해야 회복률이 재계산 대상이
되기 때문이다. 이전 3 step fixture에서는 밀침 관련 수치가 전부 정의되지 않았고, 그래서
반례 6이 fixture 위에서 재현조차 되지 않았다.

모든 요약 수치를 손으로 검산 가능한 값으로 고정했다. 명령 (0.5, 0), 실제 (0.4, 0)이므로
`error_xy` = 0.1 고정 → RMSE 0.1, `speed_xy` = 0.4 고정 → 평균 0.4, 한 step 변위
0.4 × 0.1 = 0.04 → 50 step 2.0, 자세는 전 행 관측·기립이므로 생존 1.0·커버리지 1.0,
0.4 m/s는 quiet 문턱 0.15를 넘으므로 기립 회복률은 **측정된 0.0**(부재가 아니다).
계약 검사 [1]에 fixture 요약이 fixture 행에서 나온 값과 일치하는지 확인하는 항목을 넣었다.

계약 검사는 9절 27검사에서 17절 60검사로 늘었고, 감사자 반례 8종은 각각 절이 됐다.
정상 대조군도 함께 유지한다 — 반례마다 "거절"만이 아니라 "정상 자료는 여전히 통과"를
같이 본다.

## 6. 런북 정정

- 첫 화면: "수집 조건 통과 = 측정 유효"를 **"수집에 착수해도 된다는 뜻일 뿐이며, 측정
  유효성은 회수 뒤 §8-d 검증으로 따로 판정한다"**로 좁혔다(감사자 §6 마지막 문단).
- §8-d: "채점이 소비할 모든 수치를 검사한다"는 과장이었다. 실제로 무엇을 다시 계산하고
  무엇을 대조하는지로 다시 썼고, `INTERNAL_GATE_INCONCLUSIVE`가 PASS가 아니라는 문장과
  `--expect-steps` 사용 조건을 넣었다.

## 7. 하지 않은 것과 미확인

- `Q/go2_eval_telemetry.py:206-208`의 낡은 fallback 주석은 그대로 둔다. 4차 §6과 5차 Q4에서
  감사자가 동의한 대로, 수집 동작을 바꾸지 않는 주석 때문에 검증된 ZIP 해시를 무효화하지
  않는다.
- 러너의 case 지문 값 자체는 재계산하지 않았다(§3.7). 지형 인자와 환경변수를 Python에서
  재현해야 하고, 그 재현이 틀리면 정상 자료를 거절하게 된다. 유일성·형식만 본다.
- 지면 ray hit 등 파생 채널의 비유한 값 전수 금지는 하지 않았다. 감사자도 요구하지 않았다.
- **0바이트 사고**: 감사자 §7 지적을 받아 "손실이 전혀 없었다"는 주장을 **미확인**으로
  낮췄다. 확인된 것은 재빌드본과 사이드카가 일치한다는 것, 그리고 잘린 상태·직전 상태의
  두 해시 모두 저장소 어느 문서에서도 참조되지 않는다는 것뿐이다. 사고 전 바이트는 확보하지
  못했다. 진단 목적으로 기존 산출물을 write 모드로 여는 일은 앞으로 하지 않는다.
- G-A027 실제 telemetry·영상·현재 GPU 잔량·공식 결과는 여전히 **미측정**이다.
- 이번 반례들이 실제 실행에서 발생했는지, 실제로 잘못된 승급이 있었는지는 **미확인**이다.
  이 수리는 그런 일이 있었다는 주장이 아니라, 있어도 점수로 읽히지 않게 하는 것이다.

## 8. 업로드 패키지 — 변경 없음

`Q/go2_a017_full_suite.zip`은
`c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea` 그대로이고
`upload/G-A027/current/` 사본과 바이트 동일하다(`cmp` 확인). 이번에 고친 두 채점 파일
(`Q/go2_fixed_eval_report.py`, `Q/go2_tuning_eval_report.py`)은 로컬 도구이고 ZIP 안에
들어가지 않는다. 서버로 가는 코드는 변하지 않았다.

## 9. 고정 해시

| 경로 | SHA256 |
|---|---|
| `tools/verify_go2_a027_harvest.py` | `b720a1814fdb32c54deffa9a794a153a96303d846fd919446c3fc95d2bc0ded7` |
| `tools/test_go2_harvest_verifier_contract.py` | `0c96140f9454f043f70149daebb128014743daa3dff2a32e82301ed9e06de7e6` |
| `tools/test_go2_scoring_repair_contract.py` | `46fe17cd77229c6d50a7b9b967f1ab79795a3f0fbd7f7c28474f3098731e8bbf` |
| `tools/test_go2_posture_survival_contract.py` | `61e64355936aaffd9d5ab7ef9be108700d0c9fc3d70c24e513f16c0eb51f2398` |
| `tools/test_go2_a017_full_suite_contract.py` | `86045d6a53f323d86414a52e48121d00a24b34d398175b71af6351493efcc9e5` |
| `Q/go2_tuning_eval_report.py` | `15dd6c1e30a426f4968c52d6310681f091e31eb4807bfbfa67c5289435f2c4d5` |
| `Q/go2_fixed_eval_report.py` | `af7efe22e7aba3588fedca071ac7228d8c1077de5e5e5310b1602ab065c4d04b` |
| `Q/go2_eval_telemetry.py` | `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84` |
| `Q/go2_tuning_config.py` | `2f33a45ff10178cbf6af4fe83b0b489b1e15fe95b55f01f26c7f11cb77fa8a3a` |
| `Q/server_run_go2_a017_full_suite.sh` | `23e8923020492578be609a5e6eb4717100d5bab94d0c49e334ba2c8820eeabb6` |
| `Q/config/go2_self_eval_registry.json` | `8d8c34caf66813e2c18070fb9a85ed7c843c379cb3a5ffb3d0a73923b9349ba6` |
| `Q/go2_a017_full_suite.zip` | `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea` |
| `SERVER_SESSION_RUNBOOK.md` | `313d6fb028d6a940d7388b73d2c336ffa3626b45fdbf0c4dcc76b4e1714c1538` |
| `GO2_PROJECT_STATE.md` | `2334eac89cfcfc305bd48239d46155cd55d913223ccdebcc3fc0fc9210658fe7` |
| `GO2_REAUDIT_ROUND6_PROBE_260909.py` | `99bdac5c75f6842881d69ad65fadff5660373eb8587913df3acf5cb50cf0513a` |
| `GO2_REAUDIT_ROUND5_PROMOTION_260908.md` | `d19a3009576e08a7e94169b863ce1ec6189913a57ecda675372fca5366dd30ba` |
| `GO2_REAUDIT_ROUND5_RESPONSE_260908.md` | `ef2221ab394ff66055f0e14620dbacbbf4f27f291b67cdea47d02df0880d9b90` |
| `GO2_REAUDIT_ROUND5_PROBE_260908.py` | `b7036b77b0715bfee29a7c458d199f47b9146ed2a8b002b038c0d4bf5e3e58d3` |

원장 기록은 `GO2_PROJECT_STATE.md` §40 (사실 G-F207~G-F213, 결정 G-D151~G-D157).

## 10. 되묻는 것

1. **재계산의 정의 일치.** §3의 8개 수치를 계측기 정의로 다시 계산했다. 낙상 타이머의
   grace/hold 처리, 미관측 행에서 timer를 전진도 초기화도 하지 않는 것, 회복 창의
   peak 선택과 `break` 위치까지 원본과 같게 맞췄다고 보는가? 정상 실측에서 허용오차
   `1e-6`(상대)이 너무 빡빡하다고 보는 근거가 있는가?
2. **`INTERNAL_GATE_INCONCLUSIVE`의 위치.** 실행 계획을 읽지 못한 자료를 FAIL이 아니라
   INCONCLUSIVE로 두는 것이 맞는가? 아니면 계획 대조를 필수 입력으로 만들어 계획 없이는
   아예 실행되지 않게 하는 편이 나은가?
3. **case 지문을 재계산하지 않은 결정.** §3.7에서 유일성·형식만 봤다. 지형 인자·환경변수를
   Python으로 재현하는 편익이 오재현 위험보다 크다고 보는가?
4. **case별 필수 목록의 경계.** 밀침·계단 외에 `combined_yaw_*`는 `tracking_yaw_rmse`를
   쓰는데(`Q/go2_fixed_eval_report.py:33-34`), 이 값은 모든 case가 갖는 값이라 공통 목록에
   두었다. 이 배치가 맞는가? 놓친 case별 소비 필드가 더 있는가?
5. **G-A027 진행.** 이번 수리로 "점수 채택·자동 승급 보류"의 근거가 해소됐다고 보는가?
   해소되지 않았다면 어느 항목이 남았고, 그것이 **수집 자체**를 막는 근거인지 아니면
   수집 후 채택만 막는 근거인지 구분해 달라.

---

이번 감사에서 사실로 확인된 것은 §2의 명령 출력과 §9의 해시뿐이다. 로봇의 성능,
실제 회수물의 유효성, 공식 채점 결과는 어느 것도 이 문서로 확인되지 않는다.
