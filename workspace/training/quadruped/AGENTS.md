# Go2 예선 캠페인 지침

이 파일은 저장소 루트 `AGENTS.md`를 대체하지 않는다. `workspace/training/quadruped/`에서
Go2 학습·평가·보고를 수행할 때 적용하는 최소 차이 지침이다.

## 1. 캠페인 정본과 범위

- H1 캠페인과 원장·점수·artifact를 섞지 않는다.
- 매 작업 시작 시 다음 순서로 읽는다.
  1. `GO2_PROJECT_STATE.md`
  2. `GO2_CAMPAIGN_SCHEDULE.md`
  3. `GO2_REWARD_EVIDENCE_MASTER.md`
  4. `workspace/training/quadruped/config/go2_self_eval_registry.json`
  5. `workspace/training/quadruped/reports/PLANNER_BRIEF.md`
  6. `workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md`
  7. `.omx/plans/go2-default-baseline-experiment-plan.md`
  8. `ARTIFACT_MANAGEMENT.md`
- 현재 보존 비교군은 `train_260831-Go2_5var_1000`, iter 999,
  `model_best.pt sha256=c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d`다.
- 위 비교군은 실질 4변수 동시 변경이므로 `MULTIVARIABLE_EXPLORATORY_BASELINE`이다.
  개별 reward의 효과, G1~G7 성능, 제출 적합성을 확정하지 않는다.
- 향후 실험 계보의 기준선은 배포 기본 reward로 새로 만들 `Default-01`이다. Pilot-01은 resume하지 않는다.

### 1-a. Default Baseline PRD는 살아있는 정본

- `reports/GO2_DEFAULT_BASELINE_TEST_PRD.md`는 단발 계획서가 아니다. Go2 기획자는 매 기획 턴 시작과
  종료에 이 문서를 읽고, 최신 사용자 결정·artifact·구현 확정값·평가 결과·다음 분기를 반영한다.
- `go2-campaign-manager`는 목표·순서·분기·완료조건, `go2-test-planner`는 통제변수·metric·허용오차·
  산출물·후속 실험을 같은 턴에 갱신한다.
- 실제 artifact가 PRD보다 최신이면 artifact를 우선 판정하고 즉시 PRD를 갱신한다.
- PRD 변경 시 `GO2_PROJECT_STATE.md`, `GO2_CAMPAIGN_SCHEDULE.md`, `GO2_REWARD_EVIDENCE_MASTER.md`,
  `ARTIFACT_MANAGEMENT.md`, 상세계획·planner brief 중 영향받는 문서를 함께 동기화한다.
- PRD와 원장이 불일치하면 `HOLD — PRD 동기화 미완료`이며 새 학습·승급·서버 명령을 내리지 않는다.

## 2. Go2 G1~G7 정본

시나리오명·가중치·필수 측정은 반드시 `config/go2_self_eval_registry.json`에서 읽는다.

| ID | 시나리오 | 가중치 |
|---|---|---:|
| G1 | 전진 속도 추종 | 0.15 |
| G2 | 전방위 속도 추종 | 0.15 |
| G3 | 거친 지형 | 0.20 |
| G4 | 경사 ±20° | 0.15 |
| G5 | 계단 10~15cm | 0.15 |
| G6 | 밀침 회복 | 0.10 |
| G7 | 도메인 랜덤화 | 0.10 |

`server_run_Go2_videos.sh`는 G1 제자리·G2 전진·G3 좌우·G4 복합·G5 rough·G6 ±10°·G7 push로
구성된 H1형 복사본이다. 이 파일은 **`LEGACY_INVALID_MAPPING`**이며 Go2 G1~G7 커버리지,
자체 점수, 제출 승급의 근거로 사용하지 않는다. 역사적 파일을 조용히 덮어쓰지 말고 새 evaluator를 만든다.

## 3. 현재 단계와 다음 행동

- 현재 단계는 **3/6 환경 적응 게이트**다.
- Default/Pilot 쌍대 G1~G7 평가는 완료됐고 분기는 `SHARED_WEAKNESS_FOUND`다. Pilot은 성능 상한으로 보존하되 resume하지 않는다.
- 현재 허용된 새 학습은 G-A007의 Default 계보 `feet_air_time 0.01→0.20` only, 1,000 iter뿐이다.
- 현재 순서는 `검증된 ZIP 실행 → candidate artifact·69 telemetry·7영상 회수 → 영상 관찰·사전 gate 판정 → 통과 시 독립 학습 seed`다.
- 실행 package는 `go2_feet_air_time_020_v1.zip`, SHA `36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f`다.
- 긴 10,000~15,000 iter 학습은 1,000~5,000 iter 단일변수 승자, survival·tracking 비열등,
  독립 평가 seed 결과가 있어야 승급한다.

## 4. 튜닝 규칙

1. 강좌 14강의 기본 원칙대로 한 번에 reward 하나만 바꾼다.
2. `기본값`, `권장 범위 중간`, `몇 배`는 값 선정 근거가 아니다.
3. 변경 전 목적함수, 직접 영향 G 시나리오, 예상 부작용, 성공·실패·INCONCLUSIVE,
   seed, iteration, 중단점, 영상·telemetry·bundle을 사전등록한다.
4. 점수는 `survival_proxy × tracking_proxy`로 분리한다. 평균 reward, terrain level,
   학습 `base_contact`만으로 자체 시나리오 점수를 만들지 않는다.
5. 현재 Pilot-01과 Default-01을 동일 evaluator에서 비교하기 전에는 특정 reward를
   `만족` 또는 `개선 원인`으로 쓰지 않는다.
6. 정책 간 성능 비교에 reward 계수가 다른 `Train/mean_reward` 절대값을 사용하지 않는다.
7. 단일 seed는 `exploratory`다. 장기 승급 전 최소 평가 seed 101·202·303을 적용한다.

## 5. 증거 계층

다음 용어만 사용한다.

- `ARTIFACT_VERIFIED`
- `VIDEO_OBSERVED` / `VIDEO_UNKNOWN`
- `INTERNAL_GATE_PASS` / `INTERNAL_GATE_FAIL` / `INTERNAL_GATE_INCONCLUSIVE`
- `SELF_ASSESSMENT_PASS` / `SELF_ASSESSMENT_INCOMPLETE`
- `OFFICIAL_RESULT_UNMEASURED` / 실제 공식 결과

bare `PASS`, `합격`, `통과 확정`을 쓰지 않는다. 영상, telemetry, 내부 proxy, 공식 결과는 서로 승격하지 않는다.

## 6. 자체평가 규칙

- 내부 v1은 후보 `env.yaml`에서 tracking `std`를 읽어
  `tracking_proxy=exp(-(RMSE/std)^2)`로 계산한다. 공식 변환식이라고 부르지 않는다.
- 시나리오 내부 게이트: survival ≥0.95, tracking ≥0.70. 양방향·다중 조건은 최악값을 쓴다.
- G1~G7 중 하나라도 survival/tracking이 빠지면 `SELF_ASSESSMENT_INCOMPLETE`이며 보수적으로 0점 처리한다.
- 전 시나리오 측정, 각 게이트 통과, 가중 simulation proxy ≥0.70이 자체 시뮬 최소조건이다.
- 설계 의도·리포트 자체감사와 합산한 총 자체예상은 최소 70/100, 운영 목표 75/100이다.
- 공식 evaluator의 명령·지형·push·DR·tracking 변환·통과선은 미공개이므로 `공식 재현`이라 쓰지 않는다.

## 7. 제출 계약

260901 사용자 제공 1라운드 제출 화면 기준:

1. 로봇 유형 `사족보행 로봇` 선택
2. `policy.pt` 업로드
3. 해당 정책과 같은 run의 `env.yaml` 업로드
4. 기술 개선 리포트 30~200자 입력

장문 내부 보고서는 200자 제출문을 뒷받침하는 증거다. `report.html`과 영상은 기본 제출물이 아니다.
제공 화면상 팀원 누구나 제출 파일을 수정·삭제할 수 있고 심사 시작 전까지 자유롭게 수정할 수 있다.
다만 **현재 심사가 시작됐는지**는 외부 대시보드 상태이므로 실제 화면 증거가 없으면 `[미측정]`으로 둔다.

## 8. 역할 라우팅

- 점수축·단계·순서: `go2-campaign-manager`
- 다음 단일변수 실험: `go2-test-planner`
- run 결과·원장·200자 제출문: `go2-report-writer`
- G1~G7·score math·seed·증거계층 독립 감사: `go2-evaluation-auditor`
- SHA·tar·manifest: 공용 `artifact-verifier` (`explore`/Luna/low)

메인 팀장이 최종 통합·서버 종료·공식 제출 판정을 소유한다.

## 9. 휘발성 서버

- 서버는 접속마다 초기화된다. 로컬 `workspace/training`이 정본이다.
- 서버를 켜기 전에 package, SHA, CRLF, `bash -n`, 예상시간, 완료표식, 다운로드 경로를 로컬에서 닫는다.
- 사용자 작업은 `zip 업로드 → 검증된 한 줄 실행 → bundle 다운로드`로 제한한다.
- 사용자가 다운로드/서버 종료를 말하면 분석보다 로컬 SHA·manifest·필수 artifact 확인을 먼저 한다.
- 필수 영상·telemetry·bundle의 로컬 검증 전에는 서버 종료 가능이라고 말하지 않는다.

### 9-a. 사용자 실행 패키지 자동 제공 계약

- 사용자의 역할이 서버 실행·회수인 작업은 사용자가 다시 요구하지 않아도 메인 루프가 먼저 다음을 완성한다:
  `업로드 ZIP 생성 → 로컬 SHA/CRC/manifest/CRLF/bash -n 검증 → 로컬 ZIP 절대경로 → 서버 업로드 경로 →
  복사 가능한 한 줄 명령 → tmux 확인 명령 → 완료 표식 → 필수 다운로드 경로 → 서버 종료 게이트`.
- 결과 artifact가 여러 종류면 server runner가 이를 **단일 결과 ZIP**으로 자동 묶는다. 사용자는 개별 영상·로그·
  telemetry를 하나씩 내려받지 않는다.
- 실행 ZIP이 아직 없거나 로컬 검증이 끝나지 않았으면 명령만 먼저 주지 않는다. `HOLD — package 미검증`으로 두고
  package와 테스트를 먼저 만든다.
- 사용자 보고 첫 화면의 `[지금 할 일]`에는 위 계약에서 사용자가 실제로 수행할 다음 동작 하나만 쓴다.
- 완료 보고에는 최소한 `ZIP 경로 / SHA256 / 업로드 위치 / 한 줄 실행 / 완료 표식 / 결과 ZIP / 서버 종료 조건`을
  자동으로 포함한다.
