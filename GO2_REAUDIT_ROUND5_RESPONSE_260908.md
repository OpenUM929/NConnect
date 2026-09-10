# Go2 5차 재감사 회신 — 승급 수정 수용 범위와 회수 검증의 잔여 결함

작성일: 2026-09-09 (260908 요청서 회신) · 감사자: Codex · 범위: 로컬 코드 감사 및 합성 반례.
Q/ = workspace/training/quadruped/. 요청서의 서술은 검증 대상이지 사실의 근거로 사용하지 않았다.

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 축의 측정 신뢰성과 설계 의도 20점·리포트 10점의 주장 정확성.
- [현재 단계] 단계 0/6 — 이번 새 측정의 증거·artifact 정합성 확보 전.
- [확보] 아래 §2의 계약 검사 3종 종료 코드 0, C6 정상 수치 반례 차단, 고정 해시 17개 일치.
- [미확보] G-A027 실제 회수물·영상·현재 GPU 잔량·공식 결과. 새 검증기의 독립 반례 차단도 미확보.
- [이번 테스트] G1~G7 회수 증거를 점수·승급 판정에 사용할 수 있는지 로컬 합성 데이터로 검사.
- [흐름] C5·C6 부분 검증 완료 → **회수 검증 결함 확인** → 수정 검증 시 점수 채택 → 실패 시 해당 측정 보류 → 최종 제출은 별도 판정.
- [지금 할 일] 이 회신과 동봉 probe를 Opus에 전달. 서버 수집은 §6의 기존 조건을 유지한다.
- [보장하지 않음] 코드 반례 차단은 로봇 성능·실측 유효성·공식 결과를 보장하지 않는다.

캠페인 기준 문서: [GO2_REWARD_EVIDENCE_MASTER.md](GO2_REWARD_EVIDENCE_MASTER.md).
이 감사는 새 reward의 만족 여부를 판정하지 않는다. G-A027의 최신 동일 조건 실측은 미확인이다.

## 1. 다섯 질문에 대한 답

| 질문 | 답 | 근거·범위 |
|---|---|---|
| Q1 C6 수리 형태 | **정상 유한 입력에 한해 INTERNAL_GATE_PASS**. 기존 곱 집계를 유지하고 각 인자의 all-case 최솟값을 검사하는 방향에 동의. 그러나 NaN floor를 넣으면 승급되는 경계 결함은 남음 | Q/go2_fixed_eval_report.py:118-145; Q/go2_tuning_eval_report.py:222-235,293-299; §3 |
| Q2 floor 없는 옛 보고서 | 승급 근거로는 INTERNAL_MEASUREMENT_INVALID가 타당. 단, 과거 원시 측정 자체를 모두 무효화한 뜻은 아님 | Q/go2_tuning_eval_report.py:262-288. 보존된 case 자료로 floor를 재집계할 수 있다면 GPU 재실행 없이 재판정 가능 |
| Q3 회수 검증 범위 | **점수 채택의 유일한 검사로는 불충분**. 아홉 채널 재계수는 유효하지만 실제 채점 소비 필드가 빠지고 행 정합성도 충분히 검사하지 않음 | tools/verify_go2_a027_harvest.py:68-84,109-160,223-249; Q/go2_fixed_eval_report.py:27-63; §4 |
| Q4 주석 수정 연기 | 동의. 수집 동작을 바꾸지 않는 주석 때문에 검증된 ZIP을 교체할 필요 없음 | Q/go2_eval_telemetry.py:203-221,451-512. ZIP 해시 확인은 §2 |
| Q5 G-A027 진행 | **기존 조건부 수집 동의 유지**. 이번 결함들은 ZIP 밖의 결과 채택 경로에서 확인되어 새 수집 중지 근거로 삼지 않음. 다만 “GPU 잔량만 알면 모든 절차가 끝난다”는 해석에는 동의하지 않음 | Q/server_run_go2_a017_full_suite.sh:297-310; SERVER_SESSION_RUNBOOK.md §8-c·§8-d. 수집 이후 점수 채택·승급은 별도 보류 |

판정은 이번 코드와 합성 입력에 국한한다. 실제 정책이 이 결함 때문에 승급됐거나 G-A027 데이터가 이미 손상됐다는 주장은 **미확인**이다.

## 2. 직접 실행한 검증

다음 세 명령은 순차 실행했고 각각 성공 출력을 읽었으며, 실패 시 다음 명령을 실행하지 않도록 연결했다. 전체 종료 코드 0.

~~~text
python -B tools/test_go2_scoring_repair_contract.py
python -B tools/test_go2_harvest_verifier_contract.py
python -B tools/test_go2_a017_full_suite_contract.py
~~~

- scoring-repair: C6 숨은 생존 미달 거절·정상 후보 허용·floor 부재 무효·screening 분리 확인.
- harvest-verifier: 제공된 손상 입력에 대한 계약 검사 성공. 그러나 아래 추가 반례는 허용됨.
- package: 기존 ZIP CRC·manifest·LF·bash -n·payload 대응·69+69 case 및 영상 7건 계약 검사 성공.
- 요청서 §8의 17개 경로를 직접 SHA256 대조: **17/17 일치**.
- 업로드 ZIP: `c190c2910dc225b72cbf2df3376f2cc57f4ce36861d4a4bf859f018a3a9eb5ea`.

이번 감사에서 10종 전체 테스트나 ZIP 14개 전체를 재검사했다고 주장하지 않는다.
기존 ZIP을 재빌드하지 않았고 배포·계측·채점 소스도 수정하지 않았다.

## 3. C6 경계 결함 — 존재 검사는 유효한 숫자 검사와 다르다

**증거 강도: 높음 — 코드 및 직접 재현.**

Q/go2_tuning_eval_report.py:231-235는 floor가 None인지 검사한다.
:296-297은 floor < threshold로 실패를 찾는다. NaN은 None이 아니고,
NaN < 0.95도 False이므로 실패 목록에 들어가지 않는다.

요청서의 현대 지문 합성 arm에서 G1의 survival_proxy_min_any_case만 NaN으로 바꾼 실제 출력:

~~~text
NAN_FLOOR INTERNAL_REPRESENTATIVE_PROMOTION_PASS
~~~

이는 “정상 수치에서 C6를 고쳤다”는 결론을 뒤집지 않지만,
“승급 입력 검증까지 완결됐다”는 결론은 막는다. 직접 함수 입력 반례이며,
실제 정상 Collector가 이 floor를 생성한다는 인과 주장은 하지 않는다.

**수정 제안:** floor의 존재·숫자 타입(bool 제외)·유한성·[0,1] 범위를 승급 전에 검사.
실패 시 성능 FAIL이 아닌 INTERNAL_MEASUREMENT_INVALID, candidate_points_70=None.
NaN·±Infinity·bool·문자열·음수·1 초과 반례와 정상 [0,1] 입력을 모두 회귀 검사한다.
총점 등 승급에서 소비되는 다른 수치도 같은 원칙으로 명시 검증한다.

덧붙여 현재 scenario_floor_failures는 **case 이름이 아니라 G1 같은 시나리오 ID**를 낸다
(Q/go2_tuning_eval_report.py:293-298,322). 수리 효과 진단에는 유용하지만
어느 seed/case가 미달인지까지 답하지 않는다. floor를 만든 case/seed/값/문턱을 별도 기록하면 재측정 대상을 정확히 지정할 수 있다.

## 4. 회수 검증 도구의 새 반례

**증거 강도: 높음 — 모두 신규 probe에서 직접 실행.**
기존 fixture의 두 arm × 69 case를 복제하고 한 곳씩 바꿨다.
기존 fixture는 case당 2 env × 3 step이다
(tools/test_go2_harvest_verifier_contract.py:30-32, write_case, build_harvest).
이는 실제 G-A027 실측 데이터가 아니다.

| 변형 | 실제 출력 | 원인·출처 |
|---|---|---|
| 동일 (step,env_id) 행 복제 및 다른 조합 한 행 삭제, 총 행 수·env 수·step 수 유지 | INTERNAL_GATE_PASS | tools/verify_go2_a027_harvest.py:127-128,151-153,229-240는 개별 집합의 크기만 검사. Cartesian grid의 각 조합이 정확히 한 번 존재하는지 검사하지 않음 |
| upright 한 칸을 banana로 변경 | INTERNAL_GATE_PASS | :129-130은 비어 있지 않으면 관측으로 계산. 자세 상태의 값 영역과 원시 자세 채널 대응을 확인하지 않음 |
| summary.survival_proxy=0.5, tracking_xy_rmse=0.0으로 수정, CSV 유지 | INTERNAL_GATE_PASS | :206-213은 범위 검사일 뿐 생존·RMSE 재계산이 아님. fixture 자체의 원래 RMSE도 raw와 일치하도록 만든 자료가 아님 |
| metadata.max_steps=999, step_dt=99, summary 유지 | INTERNAL_GATE_PASS | :215-249에서 metadata와 summary의 시간·길이 조건을 대조하지 않음 |
| STATUS.txt를 EVAL_RC=01로 변경 | INTERNAL_GATE_PASS | :193은 정확한 key/value 파싱이 아니라 부분문자열 EVAL_RC=0 검색 |
| push case에 post_push_tracking_xy_rmse=NaN, recovery.recovery_rate_upright=Infinity 추가 | INTERNAL_GATE_PASS | :68-76의 검사 목록에 없지만 Q/go2_fixed_eval_report.py:44-60에서 실제 소비 |
| 원본 합성 3 step 양팔 자료 | INTERNAL_GATE_PASS | 양팔 일치 검사는 실행계획 충족 검사와 다름. 현재 CLI는 G-A027의 기대 env/step 조건을 독립 입력으로 받지 않음 |

### 4.1 가장 먼저 보완할 것은 실제 채점 입력 목록

Q/go2_fixed_eval_report.py:35-39는 계단에서 **projected_progress_m, steps, step_dt**를,
:44-60은 밀침에서 **post_push_tracking_xy_rmse, recovery.recovery_rate_upright**를 쓴다.
따라서 “채점이 소비할 모든 수치를 검사한다”는 도구 주석과 런북 §8-d 표현은 현재 과장이다.

survival_proxy_v1을 [0,1]로 검사하는 것은 보조 무결성 검사로는 무방하지만,
그 항목을 검사했다고 현재 G5/G6 채점 필드를 대체할 수는 없다.
필요 필드는 case별로 검사해야 한다. 밀침이 아닌 case에 밀침 측정값을 무조건 요구해서
정상 null을 거절하는 식으로 범위를 넓히면 안 된다.

파생값 overflow는 발생 빈도가 **미확인**이다. 다만 채점 경계에서 NaN/Infinity를 거절하는 것은
그 발생 빈도와 무관하게 필요하다. 모든 지면 ray hit의 비유한값을 금지하라는 요구는 아니다.
집계에 사용한 유효 지면 근거·height_rel·proj_grav_z·upright의 관계를 확인하는 방향이 적절하다.

### 4.2 독립 검증이라는 표현의 정확한 범위

현재 독립적으로 재계산하는 것은 아홉 채널 비유한 행 수와 전체 upright 비공백 비율이다.
생존 낙상 집합·RMSE·회복률·진행량·env별 최소 coverage는 전부 재계산하지 않는다
(tools/verify_go2_a027_harvest.py:109-160,196-249).

우선 raw 행의 키·순서·타입과 자세 관측 상태를 검증하고, 이후 재현 가능한 소비 지표를
Collector의 정의와 동일한 조건으로 재계산해야 한다.
C3의 무해 결측 허용을 없앨 필요는 없으며, 낙관/비관 낙상 집합 비교와 grace·hold 조건을 보존한다.
원시자료에 필요한 채널이 없으면 값을 추정해 채우지 말고 **미확인/측정 불완전**으로 남긴다.

### 4.3 “양쪽이 같다”와 “사전등록된 자다”는 다르다

:269-271은 arm 해시 필드의 비어 있지 않음만 검사하고 :340-343은 양팔의 동일성만 비교한다.
:81-84의 case ruler에는 num_envs가 없고, :323-351은 case별 매핑이 아니라 ruler 집합을 비교한다.
현재 모든 case의 자가 하나라는 제한 안에서는 집합 비교 자체로 해당 목록의 균질성은 확인되지만,
목록 밖의 env 수나 frozen evaluator/model/registry의 정체까지 확인하지는 못한다.

실제로 통과한 fixture의 identity는 model-a017·registry·evaluator라는 자리표시자다
(tools/test_go2_harvest_verifier_contract.py, build_harvest).
따라서 이 도구 단독 성공을 ARTIFACT_VERIFIED로 읽으면 안 된다.
동결 모델·env·evaluator·registry 해시와 실행 시 확정한 env/step 조건을 외부 기대값으로 대조해야 한다.
러너 기본값은 EVAL_STEPS=1000, --num_envs 32이며 steps는 환경변수로 조절 가능하다
(Q/server_run_go2_a017_full_suite.sh:37,258). 실제 승인된 실행값을 쓰고 하드코딩 추정하지 않는다.

## 5. 무엇을 어떤 순서로 고칠 것인가

아래는 **개선 제안**이며 구현 완료 주장이 아니다. 시간은 실측이 아닌 로컬 작업 계획 상자다.
모두 GPU 0이며, 검증된 수집 ZIP을 바꿀 필요가 없다.

| 우선순위·기한 | 변경 | 시간 상자 | 수용 기준 / 실패 시 대안 |
|---|---|---:|---|
| P1 점수 채택 전 | case별 G5/G6 소비값 검증, 정확한 STATUS 파싱, 기대 model/evaluator/registry 대조 | 45~60분 | §4의 비유한 밀침·잘못된 RC·가짜 identity 거절 / 점수 채택 보류 |
| P1 점수 채택 전 | (step,env) grid 완전성·타입·중복·metadata 조건·env별 coverage 검사 | 45~60분 | 행 복제로 삭제를 숨긴 자료·banana upright·시간 불일치 거절 / 유효 case 보존, 손상 case만 표시 |
| P1 승급 전 | 유한한 [0,1] floor 검증 및 미달 case/seed 식별 | 30~45분 | §3 NaN 무효화, 정상 arm 허용 / 자동 승급 보류 |
| P1 점수 채택 전 | RMSE·생존·회복·진행량의 raw→summary 대조 범위 완성 | 60~90분 | 정상 실측과 정의·허용오차 일치, 범위 안 위조값 거절 / 검증 못 한 지표를 미확인 처리 |
| P2 다음 패키지 | 알려진 주석, resume 검증 연결, Collector 최초 이상 위치 | 다음 묶음 | 새 버전·해시·회귀검사로 갱신 / 현재 frozen ZIP은 보존 |

모든 반례에 대해 거절만 확인하지 말고 정상 자료와 실제 Collector에서 생성한 정상 fixture도 허용되는지 검사한다.
예외를 새로 넣을 때는 허용 목록·필수 근거·판정 범위를 함께 고정한다.
과거 보고서 floor 누락은 원시 case가 충분하면 로컬 재집계를 먼저 시도하고, 이를 GPU 재학습 이유로 사용하지 않는다.

## 6. G-A027 수집 조건과 결과 채택 조건

**수집에 대한 기존 조건부 동의는 유지한다.** 이번에 확인한 결함은 로컬 검증·승급 경로에 있고,
업로드 ZIP은 §2의 고정값이다. 단, 잔량 실측 외의 기존 운영 조건을 없앤 뜻은 아니다.

1. 시작 전에 현재 GPU 잔량·동결 ZIP·실행 조건·회수 목록을 확인.
2. fresh 수집을 기준으로 하고, 이전 결과 혼합이나 resume은 검증된 지문/유효성 확인 없이 신뢰하지 않음.
3. 첫 10분 계측 확인, 2시간 재판정, 중단 시 기존 유효 출력 보존.
4. 69+69 case와 영상 7건·raw·metadata·identity·로그·manifest 전량 회수 확인.
5. 회수 검증의 위 결함을 해소하기 전에는 “검증 도구가 성공했다”만으로 점수를 채택하지 않음.
6. 상대 개선(screening)·모든 case의 절대 기준·영상 관찰·제출 문서 정합성을 각각 판정.

이 조건은 SERVER_SESSION_RUNBOOK.md §8-c·§8-d 및 Q/server_run_go2_a017_full_suite.sh:456의
작업 계약을 분리해 읽은 것이다. 실제 수집 조건 충족과 서버 실행 여부는 **미확인**이다.
런북 첫 화면의 “수집 조건 통과는 측정 유효”도 더 정확히는
“수집 착수 조건 충족이며, 측정 유효성은 회수 뒤 검증”으로 좁히는 것이 좋다.

## 7. 사고·미확인 항목

- ZIP 0바이트 사고와 복구 경위는 사용자·작성자의 보고다. 이번 감사는 사고 전 바이트를 확보하지 않았으므로
  **손실이 전혀 없었다는 주장은 미확인**이다. 현재 재빌드·sidecar 일치만으로 과거 원본 동일성을 증명하지 못한다.
- 파일 존재/쓰기 권한 진단에 기존 산출물을 write 모드로 여는 행위는 피하고 새 임시 파일로 분리하는 개선을 권한다.
- 실제 G-A027 telemetry·영상·GPU 잔량·공식 결과는 이번 감사의 확인 대상 자료로 제공되지 않았다.
- 위 반례가 실제 실행에서 발생했는지, 실제 잘못된 승급이 있었는지는 미확인.
- 별도 서버 lifecycle 작업을 실행하거나 artifact를 병합하지 않았다. 이 문서 작성은 로컬 감사 회신이다.

## 8. 재현 방법과 최종 의견

동봉한 `GO2_REAUDIT_ROUND5_PROBE_260908.py`는 기존 fixture의 정의만 AST로 불러오고,
임시 디렉터리에 합성 자료를 만든다. 원본 회수물·ZIP·소스를 쓰지 않는다.

~~~text
python -B GO2_REAUDIT_ROUND5_PROBE_260908.py
~~~

현재 probe는 관측 출력을 보여주는 **감사 재현 스크립트**이지, 결함이 고쳐졌을 때만 성공하는 계약 테스트가 아니다.
위 §3~§4 표는 이 스크립트와 같은 코드를 직접 실행한 출력이다.
Opus는 수정 후 이를 거절 기대값을 가진 회귀 검사로 옮기고 정상 대조군도 유지해야 한다.

**최종 의견:** C6의 핵심 계산 경로 수정은 수용한다. 회수 검증 도구를 만든 방향도 수용한다.
그러나 검사 항목이 존재한다는 것과 채점 입력 경계를 완전히 방어한다는 것은 다르다.
이번에는 새 반례가 검증기와 승급 함수 양쪽을 통과했으므로, **수집은 조건부 유지, 점수 채택·자동 승급은 보완 전 보류**가 정확한 결론이다.
