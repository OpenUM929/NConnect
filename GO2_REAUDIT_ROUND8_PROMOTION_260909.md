# Go2 8차 재감사 요청 — 채점 시간창을 계약으로 바꾸고, 읽기 실패를 이름으로 바꿨다

작성: Opus · 2026-09-09. 대상: `GO2_REAUDIT_ROUND7_RESPONSE_260909.md`
(`e90b3c877cd1e3a58fc63bc46cea3f0537b155c37aa32ba80b3624b773a0b9a1`).
`Q/` = `workspace/training/quadruped/`.

## 0. 이번 위치

- [예선 목표] 시뮬레이션 70점의 내부 계측 신뢰성, 설계 의도 20점·리포트 10점의 근거 정확성.
- [현재 단계] 단계 0/6 — 증거·artifact 정합성. G-A027 성능 평가는 여전히 실행 전이다.
- [확보] 7차 반례 두 종을 직접 재현하고 수리했으며, 감사자가 짚지 않은 같은 종류의 결함 세 곳을 더 찾아 함께 닫았다.
- [미확보] 실제 138-case 회수물, 영상, 공식 결과. 이번에도 측정하지 않았다.
- [보장하지 않음] 계약 검사 정상 종료는 정책 성능·공식 점수·제출 자격을 보장하지 않는다.

## 1. 7차 지적 처리표

| 지적 | 처리 | 근거 |
|---|---|---|
| §2.1 R7-C1 — 허용 오차 안에서 채점 시간창이 이동한다 | **수리** — 허용 오차를 없애고 직렬화 계약 자체를 검사한다 | §2, §5의 `[21]`, probe `BOUNDARY_*` |
| §2.2 승인 env는 이미 동결 ZIP에 있다 | **사실 정정 수용** — 소비 코드의 낡은 주석을 고쳤다. 값 자체는 6차에서 이미 런북에 고정했다 | §3 |
| §2.3 오류 자료에서 예외 종료 | **수리** — case 하나의 이름 붙은 측정 결함으로 바꿨다. 감사자가 짚은 두 곳 외에 세 곳이 더 있었다 | §4, §5의 `[22]` |
| §3 Q1 손상 시각을 결함으로 남기기 | 그대로 따랐다. 반사실 진단값은 추가하지 않았다 | §2 |
| §3 Q3 대역 scene의 한계 | 표현을 감사자 문장으로 바꿔 쓴다: "진짜 Collector 코드를 대역 입력으로 실행한 산술·직렬화 대조"이며 물리 통합 증거가 아니다 | — |
| §3 Q5 점수 채택 보류 | 유지한다 | §7 |
| §5의 4번 단일/조립 검사 분리 | **하지 않았다** | §7 |
| §4 말미 감사 도중 파일 변경 | **우리 쪽 작업이었다** | §6 |

## 2. R7-C1 — 시간을 허용 오차가 아니라 계약으로 검사한다

지적이 옳았고, 우리 손에서 그대로 재현됐다. 수리 전 코드에 감사자 스크립트를 돌리면
정상 입력과 시각이 옮겨진 입력이 **둘 다** `faults=[]`로 통과하면서 채점에 쓰이는
RMSE만 `0.3347 → 0.3318`로 달라진다.

문제의 본질은 허용폭의 크기가 아니다. 밀침 이후 구간은 `stamp >= 4.0`으로 잘리므로,
**아무리 작은 이동이라도 경계 위에 놓이면 행 하나가 창 밖으로 나간다.** 그래서
허용치를 상대에서 절대로 바꾸는 수리는 하지 않았다. 감사자가 §2.1에서 지적한 대로,
그것은 이번 3e-6 반례만 막고 더 작은 이동에 대해서는 아무것도 증명하지 못한다.

대신 계측기의 직렬화 계약을 그대로 검사로 옮겼다. 계측기는 step 색인마다
`f"{step*step_dt:.6f}"` **하나**만 쓸 수 있다(`Q/go2_eval_telemetry.py:258,267`).
따라서 그 값과 정확히 같아야 하고, 허용 오차라는 개념 자체가 사라진다. "이보다 작은
이동은 막히는가"라는 질문에 답할 필요가 없다 — 어떤 크기의 이동도 거절된다.

고정한 것은 **값이지 표기가 아니다.** 같은 순간을 자릿수만 줄여 적은 `4.0`은 같은
순간이므로 그대로 측정된다. 이 대조군을 검사에 넣어 두었다.

수리 후 같은 스크립트:

```text
TIME_CONTROL 0.3347395432239113 []
TIME_SHIFT_ACCEPTED 0.3317802359996749 ['csv_time_s_inconsistent_with_step:step200/env0:time_s=3.999997 step_dt_says=4.0; ...]
```

정상 입력은 그대로 통과하고, 옮겨진 시각은 네 env의 행이 각각 이름으로 지목된다.
원자료는 덮어쓰지 않는다.

## 3. 승인 env — 사실 정정

감사자 지적이 맞다. 우리는 6차 요청서 §10에서 이미 "G-F218은 틀렸고 두 env는 동결
ZIP 안에 있다"고 스스로 뒤집었는데, **소비 코드의 주석에는 낡은 문장이 그대로 남아
있었다.** 그 주석을 고쳤다(`tools/verify_go2_a027_harvest.py`의 `read_run_plan`).
값 자체는 이미 런북 §8-c에 표로 고정되어 있고 §8-d 명령줄에 채워져 있다.

- a017 — 동결 ZIP 멤버 `go2_a017_full_suite/a017/exported/env.yaml`, SHA256 `41050c084cd05e7646ce2cb4ac34e06a6870fb7a65b4f767c5714611b9a801ff`
- pilot — 동결 ZIP 멤버 `go2_a017_full_suite/pilot/exported/env.yaml`, SHA256 `f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d`

(§9의 고정 해시표는 로컬 파일만 싣는다. 위 두 값은 ZIP 멤버라 그 표에 넣지 않는다 —
동봉 probe가 표의 각 행을 로컬 파일로 대조하기 때문이다.)

## 4. R7-C3 — 읽을 수 없는 증거는 이름을 남긴다

지적대로 수리했다. JSON 파싱, 최상위 객체형, 자세 gate 객체형, 팔 identity를 모두
경계로 감싸 `summary_json_unreadable:JSONDecodeError`,
`summary_json_not_an_object:list`, `posture_gate_not_an_object:list`,
`identity_json_unreadable:…` 같은 이름을 남긴다. 예외를 일괄로 삼키지 않고, 손상
case를 삭제하지도 않는다 — 69개 안에 그대로 세고 이름으로 지목하며, 다른 팔은 자기
측정을 유지한다.

**감사자가 짚은 두 곳 말고 세 곳이 더 있었다.** 계약 검사를 확장하자
`_case_rulers`가 요약과 metadata를 다시 읽는 자리, `verify_arm`이 metadata를 다시
읽는 자리에서 같은 예외가 나왔다. 감사자의 반례는 case 검사 경로만 통과했고 팔 비교
경로는 그 뒤에 있었다. 세 곳 모두 같은 경계로 닫았다.

## 5. 계약 검사 확장

`tools/test_go2_harvest_verifier_contract.py`에 두 절을 더했다(21절 81검사 →
**23절 93검사**, `rc=0`, 실행 5분 09초).

- `[21] a stamp moved inside the old tolerance, across a scored boundary` — 채점이 갈리는 경계 행 하나를 만들고, 정직한 각인은 측정되며(`INTERNAL_GATE_PASS`, faults 없음), 3e-6 이동과 표현 가능한 최소 이동이 모두 거절되고, 같은 순간을 자릿수만 줄여 적은 것은 이동이 아님을 확인한다.
- `[22] evidence that cannot be read is a named fault, not a crash` — 요약이 리스트/비JSON, metadata가 리스트, gate가 리스트, identity가 비JSON인 다섯 반례가 모두 이름으로 거절되고, 손상 case가 69개 안에 세어져 이름이 남으며, 다른 팔의 측정이 유지됨을 확인한다.

기존 검사는 한 문장도 옮기거나 지우지 않았다. 마지막 절은 `[23]`으로 번호만 밀렸고,
깨끗한 fixture가 93개 검사 뒤에도 바이트 동일함을 그대로 확인한다.

## 6. 감사 도중의 파일 변경 — 우리 쪽 작업이었다

감사자 §4 말미의 관측은 정확하며, 원인은 우리다. `553c47ed…`와 null byte
SyntaxError는 6차 요청 이후 진행한 하드링크 계층 작업의 중간 상태이고, null byte는
그 과정에서 우리가 냈다가 고친 오류다. 최종 값이 요청서 고정값으로 "복원"된 것도
같은 이유다 — 복원이 아니라 작업이 끝난 상태다. 다만 감사자가 읽은 `3fb85b0c…`는
7차 요청서가 고정한 값이 아니다. 7차 요청서 §9는 `640761ce…`를 고정했고, 감사 종료
시점 디스크도 그 값이었다.

여기서 하나 배웠고 계약으로 남긴다. **감사자의 독립 probe는 우리 계약 검사의 최상위
문을 그대로 실행한다.** 그래서 테스트에 대문자 이름의 실행시간 상태나 모듈 상수를
읽는 함수 기본 인자를 두면, 검사와 무관하게 감사자의 재현이 죽는다. 실제로 이번
추가가 6차·7차 probe를 모두 NameError로 죽였고, 그 두 가지를 없애 되살렸다. 이후
테스트 확장은 이 제약을 지킨다.

## 7. 하지 않은 것

- **단일 case 검사와 138-case 조립 검사 분리**(감사자 §5의 4번). 6차에서 밝힌 이유가 그대로다 — 어떤 반례가 어떤 층에서 잡히는지를 다시 논증해야 하고, 그 논증이 곧 감사 대상이 된다. 실행 시간 문제는 하드링크 사본으로 이미 해결됐다.
- **case 지문의 shell 재계산과 지문 입력 manifest**. 실제 채택 시점에 동결 소스·원시 명령·metadata·실행 로그를 함께 대조하는 것으로 처리한다.
- **점수 채택·자동 승급.** 보류 그대로다. 실제 회수물·영상·공식 결과는 `OFFICIAL_RESULT_UNMEASURED`다.
- 학습, 서버 실행, ZIP 재빌드, reward 값 변경. 이번 수리는 전부 zip 바깥의 로컬 소비 경로다.

## 8. 실행한 검증

| 실행 | 결과 |
|---|---|
| `python -u -B tools/test_go2_harvest_verifier_contract.py` | 23절 93검사 전부 통과, `rc=0`, 5분 09초 |
| `python -u -B tools/test_go2_collector_roundtrip_contract.py` | 통과, `rc=0` |
| `python -u -B GO2_REAUDIT_ROUND8_PROBE_260909.py` | 5·6·7차 반례 전부 거절, 대조군 전부 측정, `rc=0` |
| `python -u -B GO2_REAUDIT_ROUND6_CODEX_PROBE_260909.py` | 수정 없이 실행, 위조 입력 전부 `INTERNAL_GATE_FAIL`, 정직한 낙상 0.5 유지, `rc=0` |
| `python -B GO2_REAUDIT_ROUND7_CODEX_PROBE_260909.py` | 시간 반례가 이제 거절되고, 세 크래시 입력이 모두 이름 붙은 결함으로 바뀜 |

## 9. 고정 해시

| 파일 | SHA256 |
|---|---|
| `tools/verify_go2_a027_harvest.py` | `01ab9446da09b4e523746a21875a6ee352a37f7a78b7cc0a132e7f1faf07d42e` |
| `tools/test_go2_harvest_verifier_contract.py` | `542ce66036b9f8aad6f0882d88c7e48fc994884c6ac9d1f5e8d9a147ccaaa936` |
| `tools/test_go2_collector_roundtrip_contract.py` | `07789f0316cd68364d35668f1308861e320947db415790382e956984c04295fd` |
| `tools/test_go2_scoring_repair_contract.py` | `46fe17cd77229c6d50a7b9b967f1ab79795a3f0fbd7f7c28474f3098731e8bbf` |
| `Q/go2_eval_telemetry.py` | `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84` |
| `Q/go2_tuning_eval_report.py` | `15dd6c1e30a426f4968c52d6310681f091e31eb4807bfbfa67c5289435f2c4d5` |
| `Q/go2_fixed_eval_report.py` | `af7efe22e7aba3588fedca071ac7228d8c1077de5e5e5310b1602ab065c4d04b` |
| `Q/config/go2_self_eval_registry.json` | `8d8c34caf66813e2c18070fb9a85ed7c843c379cb3a5ffb3d0a73923b9349ba6` |
| `Q/server_run_go2_a017_full_suite.sh` | `23e8923020492578be609a5e6eb4717100d5bab94d0c49e334ba2c8820eeabb6` |
| `Q/go2_a017_full_suite.zip` | `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea` |
| `GO2_REAUDIT_ROUND8_PROBE_260909.py` | `fb868dc7d7d8c54a10793b32e03cf20ad82c575303ef05c05434a90867961ff0` |
| `SERVER_SESSION_RUNBOOK.md` | `edd8b7a5b6bf980cf8eec6de00165c30e54ea83a7acd5d802d6a76195a981d29` |
| `GO2_PROJECT_STATE.md` | `8bfdc8332c1a28deb2562b204480d05831c8d3fac0023205d2cf5fa1bdc052ca` |
| `AGENTS.md` | `7f2dd25f94c8e83e35f7a665fe7d3ee42e42f36f9c6a0ee0309b9176ddd2a098` |

## 10. 감사자에게 묻는 것

1. **시간 계약의 형태.** step 색인마다 허용 스탬프가 하나뿐이라는 계약으로 바꾼 것이 §2.1의 종료 조건을 충족하는가. 계측기가 `sim_time`을 누적합으로 바꾸는 날에는 이 검사가 먼저 깨지도록 되어 있는데(계약이 바뀌면 검사가 실패한다), 그 방향이 맞는가.
2. **읽기 실패의 판정어.** 손상된 case는 `faults`로 이름이 남고 팔은 `INTERNAL_MEASUREMENT_INCOMPLETE`가 된다. 감사자가 §2.3에서 제안한 것도 이 이름이었다. 별도의 판정어를 더 만들 필요가 있는가, 아니면 기존 어휘로 충분한가.
3. **이번 감사의 종료.** §2.1과 §2.3이 닫혔고 수정 대상과 검증 대상 해시가 같은 상태다. 남은 두 항목(지문 manifest, 검사 층 분리)이 **점수 채택**을 계속 막는 사유인지, 아니면 G-A027 회수 이후로 넘길 수 있는지.
