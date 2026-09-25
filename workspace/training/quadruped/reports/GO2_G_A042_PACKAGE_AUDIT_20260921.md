# G-A042 실행 전 감사 — 2026-09-21

## 2026-09-21 수정 대응 — G-A042-REPAIR-20260921
아래 감사 원문은 당시 v3 기록으로 보존한다. 수정 v4 ZIP은 `upload/G-A042/current/`이며 SHA `a95d3b6d2164354381e850ed7749d4c97d3a6df6ae02ef5bb4f29ef8dda06133`.

| 감사 항목 | 원천 수정 | 검증 |
|---|---|---|
| 계획 판정 미연결 | verifier에 versioned plan_screening·combined_verdict 연결, 사양/안내에 양 높이 조건 반영 | `test_go2_a042_verifier_repair.py`, `test_go2_g_a042_release_repair.py` |
| 정지 시 필수 수집 생략 | A042 config `COLLECT_REQUIRED_ON_STATIONARY=1`; 유효 정지 후 target·영상 수집 | `test_go2_candidate_iter_pinned_mandatory_collection.py` |
| screening 지문 미검증 | model/env 실제 SHA·pin·evaluator/registry·case 지문, 누락 우선 INCONCLUSIVE | `test_go2_a042_verifier_repair.py` |
| env별 진단/provenance 누락 | 개체 CSV+case CSV+JSON sidecar, expected/valid/missing·coverage_complete | `test_go2_stall_diagnostics_contract.py` |
| 반복/원인 과장 | 사양의 900/900 직접 비교1건과999/900 보조 관측 구분; curriculum 매개/직접 기전 구별 | `test_go2_g_a042_release_repair.py` |
| C-6 필수case/시험 출력 | required_target_cases 검증, 각/전체 삭제 반례; builder 테스트 TemporaryDirectory 격리 | verifier repair·feet_air_time_020 contract |

패키지 CRC/SHA: 외부26항/manifest25항·내부33항/32항, LF·bash -n 4개, 단일 reward1.5→1.6·report 회수 경로 검사 성공(`upload/G-A042/REPAIR_RELEASE_VERIFY.json`). 기존 v3 전체를 `history/20260921_pre_repair_snapshot`에 SHA 대조 보존. GPU 실행·행동·공식 점수는 미측정이며 이 수정은 성능 승급이 아니다.

추가 한계: 원 서버 GPU 배분 gate는 새 `CATASTROPHE_STATIONARY_MANDATORY_COLLECTION_COMPLETE`를 UNDECIDED로 남겨 전수 단계로 보내지 않는다. 이는 필수 자료 회수 후 로컬 통합 검증기가 성능 FAIL/자료 INCONCLUSIVE를 판정하는 경로다. 서버 gate를 최종 계획 판정으로 인용하지 않는다. 다른 회차의 발행 gate 바이트는 수정하지 않았다.

## PM 판정
발행 ZIP 무결성은 ARTIFACT_VERIFIED. 계획 §4·§5의 완전한 구현은 아직 아니다. 서버 실행 미해제 유지. 학습 결과/행동/공식 점수는 미측정이다. 이번은 사용자 요청에 따른 검토이며 발행물과 구현 코드는 수정하지 않았다.

## 확인한 것
- ZIP SHA256 `7952cd021438863fccd8f961333b4890db7b35ee87100bee595b4c555bd7ea15` 일치. 외부26항 CRC 정상·내부 SHA25/25; 중첩 arm33항 CRC 정상·SHA32/32. artifact-verifier의 tar 전용 도구는 ZIP을 거부하므로 zipfile 대체 검사 결과다.
- 실행 ZIP 속 iter-pinned runner가 현재 로컬 파일과 바이트 동일함을 확인했다.
- 15cm3seed 및 보호표지5case를 target 수집 목록으로 이동한 것은 일반 TARGET_FAIL 경로의 실제 개선이다. 그러나 아래 early-stop 경로까지 닫힌 것은 아니다.

## 수정 필요 사항

### P1 — 최종 판정 경로와 계획 §4 불일치
`config/experiments/G_A042_a033_track_lin_vel_xy_160.json:199,203`은 stall_time_share와15cm를 기록 전용으로 적는다. 계획 §4는 두 높이 전진/등반 비열등 및 정체 감소를 판정 조건으로 명시한다.
`upload/G-A042/current/GO2_G_A042_ONE_COMMAND_RUN_GUIDE.txt:75-82`는 기존 verifier와 진단기만 안내하며 `go2_screening_gate.py` 실행을 누락한다. verifier도 해당 모듈을 호출하지 않는다. 따라서 별도 판독기가 존재하고 단위시험이 통과해도 발행 절차가 계획 판정을 강제하지 않는다.
수정: 로컬 단일 판독 진입점에서 artifact/fact_rules와 계획 screening을 모두 실행하고 통합 verdict를 저장한다. 서버 GPU 배분용 gate는 별도로 유지 가능하나 그 판정을 최종 계획 판정으로 부르지 않는다. 안내의 stall 명령에는 필수 --candidate 인자도 넣는다.

### P1 — 정지 정책이면 필수 계단 수집 전에 종료
`server_run_go2_candidate_iter_pinned.sh:629-652`: `CATASTROPHE_STATIONARY`에서도 witness 영상 하나 뒤 `finish "$DECISION" NOT_MEASURED`. 실제 ZIP에서도 동일하다. 15cm는 이후 phase3이므로 실행되지 않는다.
수정: 비유한 학습/실행 불능은 회수 후 중단하되 유효 checkpoint의 단순 정지 성능은 최소 필수10/15cm 평가를 실행한다. 파국 정지와 일반 TARGET_FAIL 각각의 모의 실행으로 수집 목록을 검증한다. C-5의 좁은 TARGET_FAIL 해결과 ‘실패해도 필수 수집’ 전체 계약을 구분한다.

### P1 — screening 지문 검증 부재
`tools/go2_screening_gate.py:52-84,162-167`은 identity.json을 읽지 않고 summary/steps만 집계한다. docstring의 ‘지문 불일치→INCONCLUSIVE’ 계약이 구현되어 있지 않다.
로컬 합성 반례: 개선 수치 행을 case_rows 경계에 주입하고 임시 arm identity를 model/evaluator/registry 모두 WRONG으로 둬도 screen()은 INTERNAL_GATE_PASS. 이는 실제 성능 자료가 아니라 검증 경계 단위 반례다.
수정: 통합 판독에서 정책·평가기·registry·checkpoint·case 지문 확인 실패는 INCONCLUSIVE로 우선 처리하고, 독립 screening 호출 역시 검증된 입력만 받도록 강제한다. 정상 개선 대조군과 wrong/missing identity 반례를 함께 추가한다.

### P2 — 신규 진단 출력의 명세 누락
`tools/go2_stall_diagnostics.py:46-47,124-143,157-160`은 case별 집계만 출력한다. env별 first_step/null/censored 값은 집계 후 버리고, 모델 SHA·iter·evaluator·좌표계·유효 개체수·버전이 출력에 없다. 원자료에서 재계산 가능하다는 것과 명세대로 보존했다는 것은 다르다.
수정: env별 도달/검열 기록과 case 집계, 공통 provenance/명세 sidecar를 함께 저장. 기존 원자료는 변경하지 않는다.

### P2 — 근거 문구가 비교 가능성을 과장
‘두 번 인상 모두 동일 조건의 반복 증거’로 읽히면 부당하다. `GO2_TUNING_BASE_DATA.md:134-135`는 Pilot→A017의 평가 checkpoint999/900 차이를 명시한다. A017→A033은900/900이다. ‘유일한 손실 출처’는 원인 배타성까지 증명하지 못한다.
수정: 동일 조건 직접 비교1건과 checkpoint 차이가 있는 보조 관측을 구별한다. curriculum 변화는 reward 효과의 매개일 수 있으므로 변화가 동반됐다는 이유만으로 단일변수 총효과 비교를 무효화하지 않는다. 직접 기전/일반화만 유보한다.

## C-6
独立 code-reviewer `/root/a042_semantic_audit` 추가 확인: `verify_go2_basic_motion_harvest.py:210,227-246`의 검사 목록은 채점용 pkg.targets(spec)이며 required_target_cases 전체를 검사하지 않는다. 필수15cm/보호표지 수집과 수확물 완결 검증이 끊겨 있다. 채점하지 않는 case도 무결성·지문·존재 검증 목록에는 포함하고, 하나/전체 삭제 반례를 추가해야 한다.
추가로 `go2_stall_diagnostics.py:110-138`은 일부 env에 유효 시간이 없어도 나머지만 집계하고 reason을 비운다. 기대32개체와 실제 유효개체/결측사유를 함께 보존하고 부분 누락 시 판정 정책을 명시해야 한다. screening CLI의 항상0 반환은 자동 연결 시 verdict JSON 합성 또는 명시적 종료코드 계약으로 해결한다.

`tools/test_go2_feet_air_time_020_contract.py:102`의 builder.build()가 발행 경로를 쓰는 구조는 직접 확인했다. 발행물 손상을 피하기 위해 이 시험과 전체 시험은 실행하지 않았다. 따라서 이번에 ‘95중2바이트 구성 변경’을 새로 재현했다고 주장하지 않는다.
권장 해결은 테스트 출력을 TemporaryDirectory로 격리하고 발행 ZIP은 읽기 전용 검증만 하는 것이다. 이는 과거 발행물 수정/재발행을 요구하지 않으며 C-2의 사양 정합성 결정과 분리해서 처리할 수 있다. 전체 시험 후 git checkout으로 되돌리기를 정상 운영 절차로 삼지 않는다.

## 검증 범위
G-A042 전용26검사를 재실행해 26/26 OK(470.307초, exit0)를 확인했다. GO2_NOW.md도60줄이다. 기타 검사 수·claim-check118·기존 실패가 모두 선행이라는 주장은 전체 재실행/변경 전 대조를 하지 않아 독립 확인하지 않았다. 위 결함은 계약 테스트 성공과 양립한다.
