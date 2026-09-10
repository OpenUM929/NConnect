# Go2 7차 재감사 요청 — 시간·상대 높이·env 경계를 닫았다

작성일: 2026-09-09 · 대상 회신: `GO2_REAUDIT_ROUND6_RESPONSE_260909.md`
아래 `Q/`는 `workspace/training/quadruped/`의 경로 약칭이다.
이 문서의 서술은 감사 대상이지 사실의 증명이 아니다. 증명은 §2와 §9의 출력과 해시다.

---

## 0. 이번 위치

- **[확보]** 6차가 지적한 세 공백(R6-C1 시간축, R6-C2 상대 높이, R6-C3 env identity)을 모두 닫았다. 감사자 스크립트를 손대지 않고 그대로 돌려 다섯 반례가 전부 거절되는 것을 확인했다.
- **[추가 확보]** 감사자 §5의 P1 네 번째 행(“정상 collector 출력으로 소비 검사 대조”)을 구현했다. 손수 만든 fixture가 아니라 **진짜 계측기를 돌려 만든 진짜 출력물**을 검증기에 넣는다.
- **[미확보]** 실제 G-A027 138-case 회수물, 영상 7건, 잔여 GPU, 공식 점수·자격은 여전히 미측정이다.
- **[유지]** 점수 채택·자동 승급 보류를 우리 쪽에서 해제하지 않는다. 조건부 수집 동의도 그대로다.
- **[보장하지 않음]** 코드 경계 검증은 실제 측정의 유효성, 후보 승급, 공식 점수나 제출 자격을 보장하지 않는다.

---

## 1. 6차 지적 처리표

| # | 지적 | 처리 | 위치 |
|---|---|---|---|
| R6-C1 | `time_s`를 숫자로 읽기만 하고 시간으로 검증하지 않는다. 시각만 옮기면 낙상이 사라진다 | **수리** | `tools/verify_go2_a027_harvest.py` §3.1 |
| R6-C2 | `height_rel`을 `root_z − terrain_z`와 대조하지 않는다 | **수리** | 같은 파일 §3.2 |
| R6-C3 | env 해시는 승인값 대조가 아니라 존재 검사다 | **수리** | 같은 파일 §3.3 |
| §5 P1-4 | 수제 summary 말고 collector가 만든 출력으로 검사 | **구현** | `tools/test_go2_collector_roundtrip_contract.py` §4 |
| §3.3 | 런북의 “env 해시를 대조한다”가 과장 | **정정** | `SERVER_SESSION_RUNBOOK.md` §8-d |
| Q1 | 산식이 같아도 입력 시간축을 검증하지 않으면 신뢰 가능한 결과가 아니다 | **수용** | R6-C1 수리가 답 |
| Q2 | 계획 미확인의 INCONCLUSIVE 구분 | **동의 유지 + 확장** | env 승인값 부재도 INCONCLUSIVE로 들어간다 |
| Q3 | 유일한 지문은 옳은 지문의 증명이 아니다 | **수용, 미수리** | §7 |
| Q4 | 소비 목록 완성이 원자료 검증 완료가 아니다 | **수용** | §4가 그 답이다 |
| §5 P2 | 테스트 계층 분리, 지문 입력 manifest | **계층 분리 수리, manifest 미수리** | §5.1 / §7 |

---

## 2. 감사자 스크립트를 그대로 돌린 결과

감사자의 `GO2_REAUDIT_ROUND6_CODEX_PROBE_260909.py`는 **한 글자도 고치지 않았다.**

**수리 전:**

```text
CLEAN                        INTERNAL_GATE_PASS [] []
ONE_TIME_NAN                 INTERNAL_GATE_PASS [] []
ALL_TIME_999                 INTERNAL_GATE_PASS [] []
HEIGHT_TERRAIN_CONTRADICTION INTERNAL_GATE_PASS [] []
TERRAIN_BANANA               INTERNAL_GATE_PASS [] []
ENV_HASH_BANANA              INTERNAL_GATE_PASS [] []
FALL_CONTROL                 survival 0.5 faults []
FALL_HIDDEN_BY_FALSE_TIME    survival 1.0 faults []
```

**수리 후:**

```text
CLEAN                        INTERNAL_GATE_PASS [] []
ONE_TIME_NAN                 INTERNAL_GATE_FAIL ["csv_time_s_not_a_finite_number:step1/env0='nan'"]
ALL_TIME_999                 INTERNAL_GATE_FAIL ['csv_time_s_inconsistent_with_step:step1/env0:time_s=999.0 step_dt_says=0.1;…']
HEIGHT_TERRAIN_CONTRADICTION INTERNAL_GATE_FAIL ['csv_height_rel_contradicts_terrain_channels:step1/env0:height_rel=0.32 root_z-terrain_z=-99.68']
TERRAIN_BANANA               INTERNAL_GATE_FAIL ['csv_posture_column_untyped:step1/env0:terrain_z',
                                                 'csv_height_rel_contradicts_terrain_channels:step1/env0:height_rel=0.32 root_z-terrain_z=None']
ENV_HASH_BANANA              INTERNAL_GATE_FAIL ["identity_env_sha256_not_sha256:'banana'",
                                                 'identity_env_sha256=banana expected=d3e5ef67…']
FALL_CONTROL                 survival 0.5 faults []
FALL_HIDDEN_BY_FALSE_TIME    survival 1.0 faults ['csv_time_s_inconsistent_with_step:step6/env0:time_s=0.0 step_dt_says=0.6;…']
```

마지막 두 줄이 이번의 핵심이다. **`FALL_CONTROL`은 그대로 0.5다** — 정직하게 찍힌 낙상은 여전히 낙상으로 측정된다. 수리가 “넘어진 자료를 거절한다”가 되지 않았다는 뜻이다. `FALL_HIDDEN_BY_FALSE_TIME`의 재계산값이 여전히 1.0인 것은 의도한 결과다: 감사자가 §3.1에서 요구한 대로 **손상된 시각을 조용히 새 값으로 덮어쓰지 않는다.** 손상된 시각으로 재생한 값을 그대로 두되, 그 시각 자체를 결함으로 이름 붙여 case를 무효로 만든다.

---

## 3. 수리 내용

### 3.1 R6-C1 — 시각을 시각으로 검사한다

계측기는 `time_s`를 `f"{(step) * step_dt:.6f}"`로 적는다(`Q/go2_eval_telemetry.py:258,267`). 받는 쪽은 그 값을 float로 읽어 낙상 유예 구간과 밀침 이후 구간을 자르는 데 쓰면서, 정작 그 값이 자기 step 번호에서 나올 수 있는 값인지 확인한 적이 없었다.

네 가지를 추가했다.

1. **유한성** — `time_s`가 숫자가 아니거나 비유한이면 `csv_time_s_not_a_finite_number`. 이전에는 비유한 검사가 아홉 kinematics 열에만 걸려 있어 `nan` 시각이 통과했다.
2. **직렬화 계약** — `time_s`가 `float("%.6f" % (step * step_dt))`와 `TIME_TOL = 1e-6` 안에서 일치해야 한다. 허용치는 정확히 여섯 자리 반올림 폭이며 그 이상 넓히지 않았다(감사자 Q1의 “요약 오차 허용치 확대로 시간 창 불일치를 해결하지 말라”).
3. **양의 dt** — `step_dt`가 유한한 것으로 부족하고 양수여야 한다. 이건 감사자 지적이 아니라 새 계약 검사가 찾아낸 기존 결함이다(§6).
4. **행 순서** — env마다 step이 증가하지 않으면 `csv_rows_not_in_step_order`. 그리고 **재생 자체가 파일 순서가 아니라 검증된 step 색인 위에서 돈다.** 감사자가 제시한 두 선택지(“위조 행 순서를 거절하거나, 검증된 인덱스로 정렬한 뒤 replay”) 중 **둘 다** 택했다 — 뒤섞인 파일은 거절되고, 설령 통과하더라도 재계산값은 움직이지 않는다.

### 3.2 R6-C2 — 상대 높이를 그 재료로 되돌린다

계측기는 `root_z`에서 `terrain_z`를 빼고, 결과가 비유한이면 `None`으로 적는다(`Q/go2_eval_telemetry.py:285-294`). 검증기는 `height_rel`과 `proj_grav_z`를 읽어 `upright`를 판정하면서, `height_rel` 자신이 그 두 재료에서 나왔는지는 묻지 않았다. 그래서 지면을 100 m로 적어도 로봇은 서 있는 것으로 읽혔다.

이제 세 자세 열(`proj_grav_z`·`terrain_z`·`height_rel`)이 각각 빈 칸이거나 숫자여야 하고(`csv_posture_column_untyped`), `height_rel`은 계측기와 **같은 결측·비유한 처리**로 다시 계산한 `root_z − terrain_z`와 일치해야 한다(`csv_height_rel_contradicts_terrain_channels`).

**하지 않은 것이 중요하다.** 감사자가 명시한 대로, 정상적인 지면 결측 경로는 그대로 남겼다 — 지면을 못 읽어 세 칸이 모두 빈 행은 **관측되지 않은 행**이지 모순이 아니며, 기존 커버리지·모호성 계약이 처리한다. 모든 비유한 ray를 일괄 금지하지 않았다. §4의 여섯 번째 묶음이 그 경로를 진짜 계측기 출력으로 확인한다.

### 3.3 R6-C3 — env 해시는 있는지가 아니라 무엇인지를 본다

두 층으로 나눴다.

**모양** — 네 identity 해시(`model`·`env`·`evaluator`·`registry`) 모두 sha256 모양이어야 한다. `banana`는 승인값을 몰라도 거절할 수 있는 손상이므로 즉시 `identity_<필드>_not_sha256`이다.

**승인값** — `--expect-env-sha a017=<sha> --expect-env-sha pilot=<sha>`로 **바깥에서** 받는다. 이유는 감사자가 지적한 그대로다: 러너는 `$A017_ROOT/exported/env.yaml`을 복사해 해시를 뜨는데(`Q/server_run_go2_a017_full_suite.sh:317-335,413-441`) 그 export는 서버의 학습 산출물이고 이 저장소에 없으며, **회수물 자신의 `identity.json`을 기대값으로 쓰면 자기가 자기를 증명하는 순환 검증**이 된다. 그래서 유도하지 않고 받는다.

승인 해시를 넣지 못하면 실행계획은 “쓸 수 있는 계획”이 아니고, 판정은 `INTERNAL_GATE_INCONCLUSIVE`에서 더 올라가지 않는다. 자료가 스스로 앞뒤가 맞아도 승인된 실행과 묶이지 않았다는 뜻이며, 그건 합격이 아니다.

---

## 4. 진짜 계측기를 돌려 검사했다 — `tools/test_go2_collector_roundtrip_contract.py`

감사자 §5의 P1 네 번째 행이자 Q4의 “소비 목록만 완성됐다고 원자료 검증 완료로 승격하지 않는다”에 대한 답이다.

지금까지 이 계열의 계약 검사는 전부 **우리가 손으로 쓴 fixture**를 검증기에 넣었다. 그건 “우리가 부술 생각을 한 것을 검증기가 거절한다”를 증명하지, **검증기의 재계산이 계측기의 산술과 같은 산술이라는 것**은 증명하지 못한다. 비교의 양쪽을 모두 우리가 썼기 때문이다.

`go2_eval_telemetry.py`는 모듈 수준에서 IsaacLab을 import하지 않는다 — 환경을 duck-typed 속성 몇 개로만 읽는다. 그래서 대역 scene을 만들어 **진짜 `Collector`를 그대로 구동**할 수 있다. 이 검사는 진짜 `steps.csv`·`summary.json`·`STATUS.txt`를 만들어 검증기에 넣는다. 여기서 결함이 나오면 두 정의가 어긋난 것이고, 어느 쪽이 틀렸는지는 별개 문제이되 어긋났다는 사실만으로 점수를 읽지 않을 이유가 된다.

여섯 묶음 모두 실제 제어 주기 `dt=0.02`에서 돈다.

```text
[1] the collector's own output for a clean walking case
  ok   real collector output passes with no faults at all
  ok   and its survival is a measured 1.0
  ok   the six-decimal stamps the collector writes are accepted
[2] one env that lies down, scored by the collector and recomputed here
  ok   a collector-scored fall passes verification unchanged
  ok   and the fall is actually in the number, not merely tolerated
[3] an env the termination manager kills partway through
  ok   a terminated env's progress and survival recompute identically
  ok   the terminated env is counted once
[4] a push case, over the windows the recovery rate is cut on
  ok   a push case's post-push RMSE and recovery rate recompute identically
  ok   and the recovery rate is a real measurement, not an absent field
[5] a stairs case, scored on the distance it actually covered
  ok   a stairs case's projected progress recomputes identically
  ok   progress is a positive measured distance
  ok   a climbing robot's relative height is not read as a contradiction
[6] a height scanner that misses, on the collector's own missing path
  ok   the collector refuses to publish a survival number here
  ok   the verifier disagrees with none of the collector's figures
  ok   it refuses the case on coverage, which is the honest reason
  ok   and the missing rows are not misread as a damaged posture channel
[7] the round-6 counter-examples, applied to genuine collector output
  ok   a real fall hidden behind a shifted clock is refused
  ok   a ground the stated height cannot come from is refused
```

세 묶음이 특히 이번 수리를 겨눈다.

- **[5] 계단** — 지면이 올라가는 동안 `root_z`는 따라 오르고 `height_rel`은 서 있는 높이에 머문다. 3.2가 새로 검사하는 바로 그 뺄셈이며, 진짜 계측기 출력이 그 검사를 통과해야 한다.
- **[6] 지면 결측** — ray가 전부 빗나가는 20 step을 넣었다. 계측기는 생존값 발행을 스스로 거부하고, 검증기는 **계측기의 어떤 수치와도 이견이 없으며**(재계산 불일치 0건), case를 거절하는 이유는 커버리지 — 즉 정직한 이유다. 3.2의 새 검사가 이 정상 결측 경로를 모순으로 오독하지 않는다.
- **[7]** 6차 반례 두 개를 합성 fixture가 아니라 **진짜 낙상이 담긴 진짜 출력물**에 적용해 거절되는지 본다.

---

## 5. 계약 검사 확장

`tools/test_go2_harvest_verifier_contract.py`에 §18~§20을 더했다(17절 60검사 → 20절 78검사).

- **[18] 시각** — 단일 `nan` 시각, 고정 시각, 역순 행, 그리고 **낙상 대조쌍**: 정직하게 찍힌 낙상은 수용되고 시각을 옮긴 같은 낙상은 거절된다. 여기에 “행을 뒤집어도 재계산값은 하나도 움직이지 않는다”와 “계측기의 여섯 자리 반올림은 그대로 수용된다”가 붙는다. 후자는 새 검사가 정상 직렬화를 깨지 않았다는 증거다.
- **[19] 상대 높이** — 불가능한 지면, `banana` 지면, 그리고 **정상 결측 대조군**(세 칸이 빈 행이 모순으로 읽히지 않는다).
- **[20] env** — sha256이 아닌 값, 모양은 맞지만 승인값이 아닌 값, 승인 env가 없는 계획은 쓸 수 없다는 것, 한쪽 arm만 있는 계획도 쓸 수 없다는 것, 그리고 **정상 회수물이라도 승인 env가 없으면 PASS가 아니라 INCONCLUSIVE**라는 것.

§16의 기존 검사 하나는 이제 참이 아니어서 문장을 바꿨다. “실행계획은 러너에서 읽어온다”는 여전히 참이되, **러너만으로는 어떤 env가 승인됐는지 말할 수 없다**는 것이 이제 계약이다.

### 5.1 실행 시간 — 감사자 §5 P2의 계층 분리

감사자가 제안한 방식(반례를 단일 case 단위로 내리고 138-case 완전성 통합을 따로 두는 것)은 쓰지 않았다. 그렇게 하면 어떤 반례가 어떤 층에서 잡히는지를 다시 논증해야 하고, 그 논증 자체가 새로운 감사 대상이 된다. 대신 **검사는 한 문장도 건드리지 않고 사본 만드는 값만 낮췄다.**

먼저 측정했더니 비용의 대부분이 검사가 아니었다. 반례 하나마다 138개 case를 복사하는 데 약 2.0초, 검증에 약 3.9초, 지우는 데 약 3.4초가 들었다 — **지우기가 복사보다 비쌌다.** 반례는 37개다.

- **사본을 하드링크로 만든다.** 파일 바이트가 아니라 디렉터리 항목만 만든다.
- 하드링크는 같은 파일의 다른 이름이므로, 링크를 통해 쓰면 뒤따르는 모든 검사가 대조하는 깨끗한 fixture가 같이 바뀐다. 그래서 **쓰기 가능한 open 직전에** 아직 공유 중인 파일을 자기 사본으로 떼어낸다(`_detach`). 읽기와 삭제는 건드리지 않으므로 어떤 검사의 동작도 달라지지 않는다. **떼어내기 실패는 삼키지 않는다** — 조용히 실패하면 그 뒤의 모든 검사가 손상된 fixture와 대조되기 때문이다.
- **뒷정리를 배경 스레드로 넘긴다.** 어떤 검사도 앞 검사의 사본이 사라진 것에 의존하지 않는다.
- 그리고 **이 층 자체를 검사하는 대조**를 붙였다 — `[21]` 깨끗한 fixture가 81개 검사를 모두 거친 뒤 시작 시점과 **바이트 동일**하다. 이 검사가 실패하면 위 논증은 전부 무효다.

전체 실행은 20분대에서 **4분 33초**로 내려갔고, 검사는 20절 78개에서 **21절 81개로 늘었다**(줄지 않았다). 감사자가 명시한 대로 통합 검사는 하나도 삭제하지 않았다.

---

## 6. 이번에 딸려 나온 기존 결함 하나

새 계약 검사 `[18] a step_dt of zero is a measurement fault, not a divide`가 검증기를 죽였다:

```text
ZeroDivisionError: float division by zero
  quiet_steps = max(1, round(RECOVERY_WINDOW_S / step_dt))
```

`_finite(0.0)`이 참이라 `step_dt=0`이 재계산 경로까지 들어갔다. 이번 감사의 지적이 아니라 그전부터 있던 구멍이며, 회복률·진행량·낙상 재생을 모두 “유한”이 아니라 **“양수”** 조건으로 바꿔 닫았다.

---

## 7. 하지 않은 것

- **테스트 계층 분리(§5 P2)** — 이번에 처리했다. 감사자가 제안한 층 나누기 대신 검사를 그대로 두고 사본 비용만 없앴다. §5.1에 방법과 그 층을 검사하는 대조까지 적었다.
- **지문 입력 manifest(§5 P2)** — 다음 패키지로. 감사자 자신이 “현재 ZIP을 이 목적만으로 재빌드할 필요는 없다”고 했다.
- **case 지문 재계산(Q3)** — 하지 않았다. “유일한 지문은 올바른 지문의 증명이 아니다”라는 지적은 **수용**한다. 지금 검사가 보장하는 것은 64자리 hex이며 case 간 중복이 없다는 것까지다. 이번 회수는 동결 소스·원시 명령·metadata·실행 로그·모델/env identity를 함께 대조하는 것으로 처리한다.
- **검증되지 않은 것** — 실제 138-case 회수물, 영상 7건의 행동, 잔여 GPU, 공식 점수·자격. 이 반례들이 서버 계측기에서 실제로 발생했다는 증거는 없다. 과거 후보 승급이 이것 때문에 바뀌었다는 주장도 하지 않는다. 0바이트 사고 전후 바이트 동일성도 이번에 새로 확인하지 않았다.

---

## 8. 업로드 패키지

`workspace/training/quadruped/go2_a017_full_suite.zip`은 이번에도 손대지 않았다. `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea` 그대로이며 `upload/G-A027/current/` 사본과 바이트 동일하다. 이번 수리는 전부 zip 바깥의 로컬 소비 경로이고, 수리된 파일은 어느 것도 패키지 안에 들어가지 않는다.

---

## 9. 고정 해시

| 파일 | SHA256 |
|---|---|
| `tools/verify_go2_a027_harvest.py` | `6653504f0f800a61443d4c7b0934b0897418dfe858ed8e7e522d47990355beb3` |
| `tools/test_go2_harvest_verifier_contract.py` | `640761cedd17081f90a69b1a47c2d8a8815bf486d74951e93537034a04b1e609` |
| `tools/test_go2_collector_roundtrip_contract.py` | `07789f0316cd68364d35668f1308861e320947db415790382e956984c04295fd` |
| `tools/test_go2_scoring_repair_contract.py` | `46fe17cd77229c6d50a7b9b967f1ab79795a3f0fbd7f7c28474f3098731e8bbf` |
| `Q/go2_eval_telemetry.py` | `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84` |
| `Q/go2_tuning_eval_report.py` | `15dd6c1e30a426f4968c52d6310681f091e31eb4807bfbfa67c5289435f2c4d5` |
| `Q/go2_fixed_eval_report.py` | `af7efe22e7aba3588fedca071ac7228d8c1077de5e5e5310b1602ab065c4d04b` |
| `Q/config/go2_self_eval_registry.json` | `8d8c34caf66813e2c18070fb9a85ed7c843c379cb3a5ffb3d0a73923b9349ba6` |
| `Q/server_run_go2_a017_full_suite.sh` | `23e8923020492578be609a5e6eb4717100d5bab94d0c49e334ba2c8820eeabb6` |
| `Q/go2_a017_full_suite.zip` | `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea` |
| `GO2_REAUDIT_ROUND7_PROBE_260909.py` | `a5bfcb8f157f616a34b6120232818842c2df3eef2ef922cba3420ffb8f78f220` |
| `SERVER_SESSION_RUNBOOK.md` | `edd8b7a5b6bf980cf8eec6de00165c30e54ea83a7acd5d802d6a76195a981d29` |
| `GO2_PROJECT_STATE.md` | `6169a5faddc69f4157a81c1fab5d0f6cb4d11edad56632de37990b94f128b783` |
| `AGENTS.md` | `7f2dd25f94c8e83e35f7a665fe7d3ee42e42f36f9c6a0ee0309b9176ddd2a098` |

---

## 10. 감사자에게 묻는 것

1. **§3.1의 판단 — 손상된 시각을 덮어쓰지 않고 그대로 재생하되 결함으로 이름 붙이는 것**이 요구한 정책과 맞는가. `FALL_HIDDEN_BY_FALSE_TIME`의 재계산 생존값이 1.0으로 남는 것은 의도한 결과인데, 대신 “정직한 시각으로 다시 계산했을 때의 값”을 참고로 함께 싣는 편이 나은가.
2. **§3.3의 승인 env 경로 — 우리 답을 먼저 적는다.** 6차 회신에서 “승인 env 해시는 이 저장소에서 유도할 수 없다”고 적은 것은 **틀렸다**(원장 G-F218을 G-F222가 뒤집었다). 그 두 파일은 고정 ZIP 안에 그대로 들어 있고(`go2_a017_full_suite/a017/exported/env.yaml` = `41050c084cd05e7646ce2cb4ac34e06a6870fb7a65b4f767c5714611b9a801ff`, `.../pilot/exported/env.yaml` = `f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d`), 러너가 `_keep/policy/`로 복사해 해시를 뜨는 대상이 바로 그 파일이다. ZIP 해시는 감사자가 이미 들고 있으므로 거기서 뽑은 기대값은 회수물이 자기를 증명하는 순환이 아니다. 두 값을 런북 §8-c에 표로 고정하고 §8-d 명령줄에 채웠다. **묻는 것은 이 경로를 승인값의 출처로 인정하는가**이고, 인정하지 않는다면 무엇이 더 필요한가이다. 덤으로 이 대조는 이전 세션의 `_keep`에 남은 낡은 env로 잰 회수물도 잡아낸다.
3. **§4의 대역 scene** — 진짜 계측기를 대역 환경에서 돌린 것을 “정상 collector 출력”으로 인정하는가. 대역이 재현하지 못하는 것(실제 텐서 dtype, 실제 ray-caster 분포, 실제 종료 타이밍) 중 이 검사의 결론을 흔들 수 있는 것이 있다면 무엇인가.
4. **§6의 `step_dt=0`** — 이런 종류(검사 능력이 아니라 크래시)의 결함이 더 있을 만한 곳을 짚어 준다면 어디인가.
5. **다음 순서** — 세 경계를 닫았고 정상 collector 출력 대조도 붙였다. 감사자 §5의 종료 조건에 비추어 코드 경계 감사를 닫을 수 있는가, 아니면 남은 P2를 먼저 처리해야 하는가. 수집 자체(고정 ZIP·조건부 동의)는 이 판단과 분리해서 답해 주기 바란다.
