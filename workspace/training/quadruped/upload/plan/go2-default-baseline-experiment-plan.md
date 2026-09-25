# Go2 기본값 재시작·쌍대평가 상세 실행계획

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 proxy /70의 개선 여부를 공정하게 비교하고, 설계 의도 /20에 필요한 단일변수 근거를 만든다.
- [현재 단계] **단계 0/6 — 증거·artifact 정합성**.
- [확보] Pilot-01 iter 999 model/env/tfevents/report와 배포 기본 reward 원문.
- [미확보] provenance-valid Default-01, 정확한 G1~G7 evaluator 결과, 쌍대 비교 보고서, policy lineage.
- [이번 테스트] 기본값 1,000-iter 정책을 새로 만들고 Pilot-01과 동일 조건에서 비교해 후속 단일변수 순서를 결정한다.
- [흐름] PRD 동결 → **evaluator·Default package 구현** → Default 학습 → 두 정책 쌍대평가 → 기본값 단일변수 → 장기 승급 → 제출.
- [지금 할 일] 구현·package 검증 전에는 서버를 켜지 않는다.
- [보장하지 않음] 이번 1회 학습·내부 proxy만으로 공식 점수, 통과 가능성, reward별 최종 인과효과를 보장하지 않는다.

## 1. 요구사항 요약

1. 테스트 계약은 `workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md`를 정본으로 한다.
2. 실험 계보는 기본 reward에서 from-scratch로 시작하며 Pilot-01은 resume 대상이 아니라 비교군이다.
3. Default-01과 Pilot-01의 유일한 의도된 학습 차이는 네 reward 값이다.
4. 두 정책은 canonical registry의 같은 G1~G7 evaluator와 seed 101/202/303으로 평가한다.
5. 정책 비교는 survival·tracking·completion·recovery·영상으로 하고 `Train/mean_reward`는 사용하지 않는다.
6. 비교가 끝나기 전 새 reward 값, 3k 이상 확장, 장기학습을 승인하지 않는다.
7. 모든 외부 실행은 `ARTIFACT_MANAGEMENT.md`의 `G-A004` lifecycle로 추적한다.

## 2. 검증 가능한 완료 기준

- [ ] G-A002 evaluator가 registry 7개 scenario, 정책당 69 telemetry, 필수 영상·sidecar를 생성한다.
- [ ] Default package가 reward-only diff, seed 42, 4096 env, 1,000 iter를 강제한다.
- [ ] package Python test·compile, `bash -n`, CRLF 0, ZIP CRC·manifest·embedded SHA가 모두 통과한다.
- [ ] Default-01 학습 bundle이 `ARTIFACT_VERIFIED`다.
- [ ] Default-01과 Pilot-01 모두 G1~G7 `영상 / 내부 정량 / 공식 결과` 표가 완성된다.
- [ ] paired report가 PRD §6의 한 분기를 재현 가능하게 선택한다.
- [ ] 후속 학습은 Default-01 계보에서 reward 하나만 변경한다.

## 3. 작업 패키지

### P0. 결정·PRD 동결 — 조사 — 완료

산출물:

- `workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md`
- `GO2_PROJECT_STATE.md`의 사실·결정·공백 정정
- `GO2_CAMPAIGN_SCHEDULE.md`의 필수 control 순서
- `GO2_REWARD_EVIDENCE_MASTER.md`의 control 상태
- `ARTIFACT_MANAGEMENT.md`의 `G-A004` 등록

완료 기준: 네 정본이 “조건부 control”이 아니라 “Default-01 필수 생성·쌍대평가”로 일치한다.

### P1. G-A002 evaluator 구현 — 필수(제출요건)

소유 파일:

- `workspace/training/quadruped/go2_eval_telemetry.py`
- `workspace/training/quadruped/go2_fixed_eval_report.py`
- `workspace/training/quadruped/server_run_go2_eval_v1.sh`
- `tools/build_go2_eval_package.py`
- `tools/test_go2_eval_contract.py`

핵심 계약:

1. registry를 직접 읽고 G1~G6 22 case×3 seed + G7 3 case = 정책당 69 telemetry를 만든다.
2. survival과 tracking을 분리하고 terrain/push/DR 실현값을 기록한다.
3. 정책별 model/env/source/registry SHA와 영상 sidecar를 보존한다.
4. policy actor tensor 비교를 포함한다.
5. legacy runner import/call을 정적 검사로 금지한다.

중단조건: 로컬 검증 하나라도 실패하면 서버 실행 명령을 만들지 않는다.

### P2. G-A004 Default-01 학습 package 구현 — 조사(필수 비교게이트)

신규 권장 파일:

- `workspace/training/quadruped/server_train_go2_default_1000.sh`
- `workspace/training/quadruped/GO2_DEFAULT_1000_README.txt`
- `tools/build_go2_default_1000_package.py`
- `tools/test_go2_default_training_contract.py`

구현 규칙:

1. pre-pilot 기본값 `1.0 / 0.01 / -3.0 / -0.08 / -0.01`을 run-specific source에 고정한다.
2. 현재 working tree를 덮어쓰지 않고 package 내부 staging copy에서만 기본값 source를 만든다.
3. reward 외 source diff가 있으면 build를 실패시킨다.
4. seed 42, num_envs 4096, max_iterations 1000, from-scratch를 강제하고 `--resume`을 거부한다.
5. 학습 종료 후 checkpoint·params·tfevents·train log·source diff·SHA를 bundle에 넣는다.
6. evaluator 실행 전 exact Default checkpoint를 명시적으로 선택한다. “latest run” 자동 탐색만으로 정책을 고르지 않는다.

중단조건: reward-only diff 또는 frozen command 검증 실패 시 package를 배포하지 않는다.

### P3. 서버 세션 1 — Default-01 학습·회수 — 조사(필수 비교게이트)

순서:

1. 검증된 package ZIP SHA 확인.
2. tmux에서 한 줄 실행.
3. `[STARTED]`에서 run ID·seed·env·iteration 확인.
4. 1,000 iter 종료 후 `TRAIN_RC=0`, checkpoint·tfevents·params 확인.
5. `VIDEO_REQUIRED`로 재판정하고 같은 checkpoint의 evaluator 준비.
6. 학습 bundle과 `.sha256`을 로컬로 다운로드.

서버 종료는 아직 금지한다. 같은 세션에서 P4 평가를 수행하거나, 평가 package 실행이 불가능하면
Default checkpoint·source·config·실패 로그를 먼저 회수하고 `VIDEO_REQUIRED_NOT_ACQUIRED`로 기록한다.

### P4. 서버 세션 1 — Default/Pilot 쌍대 G1~G7 평가 — 필수(제출요건)

1. Default-01 exact checkpoint로 정책당 69 telemetry와 필수 영상을 생성한다.
2. Pilot-01 frozen model SHA를 복원해 같은 evaluator를 실행한다.
3. 두 정책의 registry·case·seed·명령·terrain/push/DR 조건 fingerprint가 일치하는지 검사한다.
4. 정책별 FULL bundle과 외부 SHA를 생성한다.
5. 두 bundle이 로컬에 도착한 뒤에만 서버 종료 가능 여부를 판정한다.

예상시간은 package 구현 후 smoke 측정으로 확정한다. 측정 전 임의 시간을 사용자에게 약속하지 않는다.

### P5. 로컬 ingest·paired analysis — 필수(의사결정 게이트)

1. `workspace/server_returns/<RUN_ID>/original/`에 원본을 격리한다.
2. tar 안전성·외부/내부 SHA·member 수·model/env/source 대응을 검증한다.
3. `MERGE_PLAN.tsv`, `MERGE_RESULT.tsv`, `LOCAL_SHA256SUMS.txt`를 남긴다.
4. reward 계수 독립 metric만으로 seed·scenario paired delta를 계산한다.
5. PRD §5-c 허용오차와 §6 분기를 기계적으로 적용한다.
6. `GO2_PROJECT_STATE.md`, 일정, reward master, experiment history를 같은 verdict로 갱신한다.

분석 산출물 권장 경로:

- `workspace/training/quadruped/reports/GO2_DEFAULT_VS_PILOT_PAIRED_REPORT.json`
- `workspace/training/quadruped/reports/GO2_DEFAULT_VS_PILOT_PAIRED_REPORT.md`

### P6. 기본값 기반 단일변수 screening — 개선

비교 결과와 무관하게 학습 출발점은 Default-01 계보다. 한 번에 하나만 추가한다.

| 최대 약점 | 첫 후보 | 1차 측정 |
|---|---|---|
| G1/G2 선속도 tracking | `track_lin_vel_xy_exp: 1.0 → 1.2` | vx/xy tracking과 타 G 비열등 |
| G3/G5 발 걸림·completion | `feet_air_time: 0.01 → 0.2` | rough/stairs completion, gait |
| G3/G4/G5 수직 튐·낙상 | `lin_vel_z_l2: -3.0 → -2.0` | vertical stability, survival |
| G4/G6 roll/pitch 붕괴 | `ang_vel_xy_l2: -0.08 → -0.05` | slope/push stability |
| G2 yaw만 취약 | `track_ang_vel_z_exp` 별도 단일 후보 | yaw tracking과 선속도 비열등 |
| G7 실현값 누락 | reward 변경 금지 | evaluator/DR 계측 수리 |

1차 예산은 후보 1개×1,000 iter다. primary 개선 + 반대 인수 비열등 + 나머지 G worst-case
비열등 + 영상 무회귀일 때만 3k→5k 또는 다음 변경 누적을 고려한다.

### P7. 장기 승급 — 개선

screening 승자만 5k→10k→15k로 승급한다. 각 지점에서 다음을 재검증한다.

- primary G 개선 유지
- scenario별 survival/tracking gate
- 다른 G worst-case 비열등
- 독립 학습 seed 또는 미수행 한계
- 필수 영상·telemetry·bundle·lineage

조건 미달이면 직전 verified checkpoint로 동결하고 다음 iteration을 승인하지 않는다.

### P8. 최종 평가·문서·제출 — 필수(제출요건)

1. 선택 정책을 seed 101/202/303, G1~G7 전체로 재평가한다.
2. simulation proxy /70, 설계 의도 /20, 리포트 /10을 분리한다.
3. total 자체예상 최소 70, 목표 75를 확인한다.
4. `policy.pt` actor tensor와 checkpoint를 비교하고 같은 run `env.yaml`을 묶는다.
5. 검증된 문제·단일 변경·결과·한계를 30~200자로 작성해 글자수를 검사한다.
6. Go2 선택·2파일·리포트 업로드 및 접수 증거 회수 후에만 `OFFICIAL_RESULT`와 별개로 제출 완료를 기록한다.

## 4. 최소 경로·1차 계획 예산·재평가 지점

| 구분 | 범위 | 승인/중단 기준 |
|---|---|---|
| 최소 경로 | evaluator 구현 → Default-01 1k → Default/Pilot 쌍대평가 | PRD §6 분기 하나 선택 |
| 1차 계획 예산 | 신규 학습 1회(Default-01 1k), 정책 평가 2회 | 새 reward 학습은 포함하지 않음 |
| 재평가 1 | 두 package 로컬 검증 | 서버 실행 가능 여부 |
| 재평가 2 | Default 학습 bundle 수신 | 정확한 checkpoint 평가 가능 여부 |
| 재평가 3 | 두 정책 평가 bundle 수신 | restart/promising/inconclusive/shared weakness |
| 재평가 4 | 첫 단일변수 1k | 폐기/3k~5k/독립 seed |
| 재평가 5 | 5k·10k·15k 각각 | 다음 승급 또는 직전 checkpoint 동결 |

## 5. 검증 순서

계획 정합성:

```powershell
python tools/validate_go2_campaign.py
git diff --check
```

구현 후:

```powershell
python -m py_compile workspace/training/quadruped/go2_eval_telemetry.py workspace/training/quadruped/go2_fixed_eval_report.py tools/build_go2_eval_package.py tools/test_go2_eval_contract.py
python tools/test_go2_eval_contract.py
python tools/test_go2_default_training_contract.py
bash -n workspace/training/quadruped/server_run_go2_eval_v1.sh
bash -n workspace/training/quadruped/server_train_go2_default_1000.sh
python tools/build_go2_eval_package.py
python tools/build_go2_default_1000_package.py
```

추가 정적 검사:

- 신규 shell CRLF 0
- ZIP CRC·안전 상대경로·manifest·embedded SHA
- default source reward-only diff
- `--resume` 부재
- legacy runner import/call 0
- 정책당 69 telemetry execution plan

## 6. 위험과 완화

| 위험 | 완화 |
|---|---|
| Default와 Pilot의 mean reward를 직접 비교 | reward-independent metric만 paired report에 사용 |
| working tree를 기본값으로 덮어써 Pilot 계보 손상 | staging copy와 run-specific SHA 사용 |
| 한 학습 seed 우연성 | exploratory 표기, INCONCLUSIVE 시 seed 1회 복제 |
| evaluator 조건 drift | case fingerprint와 registry/source SHA 쌍대 검사 |
| 다변수 Pilot을 그대로 장기 연장 | Pilot resume 금지, 기본값 one-at-a-time forward ablation |
| 서버 초기화로 결과 유실 | 두 FULL bundle·SHA 로컬 도착 전 종료 금지 |
| 내부 proxy를 공식 점수로 오인 | 증거 계층과 공식 결과 열을 끝까지 분리 |

## 7. 계획 종료 조건

이 계획 문서의 작성 단계는 PRD·상태·일정·reward·artifact 원장이 Default-01 필수 비교 순서로
동기화되고 정적 검증이 통과하면 끝난다. 구현과 서버 실행은 다음 실행 단계이며, 현재 계획만으로
학습 완료나 성능 개선을 선언하지 않는다.

## 8. PRD 지속 갱신 규칙

`workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md`는 이 계획보다 상위의
실험 계약이다. 기획자는 매 작업 시작 시 PRD §10의 갱신 시점을 확인하고, 사용자 결정·구현 확정값·
실측 결과·분기 선택이 생기면 같은 턴에 PRD와 상태·일정·reward·artifact 원장을 동기화한다.

각 계획 단계의 종료 체크에는 다음 세 항목을 추가한다.

1. `PRD_CHANGE=NONE|UPDATED`와 근거.
2. `LEDGER_SYNC=PASS|FAIL` 및 갱신 파일 목록.
3. 다음 단계가 참조할 PRD section과 현재 decision ID.

`LEDGER_SYNC=FAIL`이면 서버 실행, 새 reward 학습, iteration 승급을 승인하지 않는다. 과거 내용을
조용히 덮어쓰지 않고 새 결정·정정 행으로 연결한다.

## 9. 260901 구현 확정

P1 evaluator와 P2 Default training 전달물은 서버 사용자의 작업을 줄이기 위해 단일 package
`workspace/training/quadruped/go2_default_vs_pilot_v1.zip`으로 통합했다. 내부 실행 순서는 여전히
`Default 1k → Default 69 telemetry → Pilot 69 telemetry → paired report → 정책별 worst-case 영상 7개 → 단일 결과 ZIP`이다.
결과는 `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip` 하나로 회수한다. ZIP SHA와 명령은 PRD §11을 정본으로 한다.

## 10. 260901 쌍대평가 완료와 G-A007 실행 전환

- Default/Pilot FULL 결과·영상 분석으로 본 계획의 쌍대평가 분기는 `SHARED_WEAKNESS_FOUND`로 종료됐다.
- Default `17.90699/70`, Pilot `41.97990/70`; G5 최대 감점 `8.12/70`과 약한 tracking/completion을 확인했다.
- 후속 계획은 `GO2_FEET_AIR_TIME_020_SCREENING_PRD.md`로 이관한다.
- 단일 변경: Default `feet_air_time 0.01→0.20`, seed 42, 4096 env, 1,000 iter.
- package: `workspace/training/quadruped/go2_feet_air_time_020_v1.zip`, SHA `36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f`.
- 사용자 역할: ZIP 업로드 → 한 줄 실행 → 결과 ZIP·SHA 회수.
- 다음 재평가점: candidate telemetry 69/69·영상 7/7을 로컬 검증·관찰한 뒤 사전 gate 판정.

`PRD_CHANGE=UPDATED`; `LEDGER_SYNC=PASS`; 현재 decision은 G-D23~G-D26이며 PRD §16과 screening PRD §5를 참조한다.

### GO2-REPLAN-A029-20260914 — 감사 후 사용자 요청 재계획
- 사용자 결정: G-A029 감사에 따라 메인 문제를 진단하고 튜닝 계획을 수립한다. 이번 요청은 계획이며 서버 실행/패키지 발행으로 확대하지 않는다. 역사 일정 CLOSED는 유지한다.
- G-A029 REJECTED_BY_AUDIT 및 -0.008 NEXT 철회 유지, review 불변. 과거 A017 HTML 누락을 발행 차단으로 복원하지 않는다.
- 계획 정본: workspace/training/quadruped/upload/plan/GO2_POST_A029_TUNING_PLAN_20260914.md.
- 직접 근거: A018 양 arm 각7case 모두 schema2/v2; A013/A025 baseline은 schema1/2 혼재, candidate는 schema2라 합산 비대칭. A027 G3 rough_lateral seed101/202/303의 base-contact 종료는 17/14/17개(/32), 첫 종료 전0.5초 q=1-gz² 평균 .688/.628/.660. 기울기는 연관성이지 최초 원인 확정 아님.
- 계획값: A017 조건 flat_orientation_l2 0→-1.0 단일변수, G3 접촉 종료/생존 표적; G5 정체·경사 회귀 동시 감시. -1은 관측 기반 단위 크기 exploratory 값이지 upstream 최적값/만족 판정 아님.
- REPORT_READ_STATUS: A017 MISSING(기존 복구 불가 확정 유지), Pilot READ_UNMATCHED(이번 HTML 본문 직접 열람, 정책 대응 미완결).
- NEXT: 다음 미사용 번호로 위 계획의 current 실행 패키지 구현·검증. 이번에 번호 예약/실행 ZIP/서버 명령은 발행하지 않았다. 학습·성능·공식 결과 새 측정 없음.
