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
  5. `workspace/training/quadruped/upload/plan/PLANNER_BRIEF.md`
  6. `workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md`
  7. `workspace/training/quadruped/upload/plan/go2-default-baseline-experiment-plan.md`
  8. `ARTIFACT_MANAGEMENT.md`
- 현재 보존 비교군은 `train_260831-Go2_5var_1000`, iter 999,
  `model_best.pt sha256=c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d`다.
- 위 비교군은 실질 4변수 동시 변경이므로 `MULTIVARIABLE_EXPLORATORY_BASELINE`이다.
  개별 reward의 효과, G1~G7 성능, 제출 적합성을 확정하지 않는다.
- 향후 실험 계보의 기준선은 배포 기본 reward로 새로 만들 `Default-01`이다. Pilot-01은 resume하지 않는다.

### 1-a. Default Baseline PRD는 살아있는 정본

- `upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md`는 단발 계획서가 아니다. Go2 기획자는 매 기획 턴 시작과
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

- 새 튜닝은 서버 생성 원본 `exported/report.html`을 평가 재생 전에 `_keep/<튜닝명칭>/exported/report.html`로 보존하고 결과 ZIP·SHA 목록에 포함한다. 누락·빈 파일·이전 실행 report는 `REPORT_REQUIRED_NOT_ACQUIRED`; 회수 완료로 표시하지 않는다. 재개 시에도 보존 report와 SHA를 검사한다. 모든 서브에이전트와 새 패키지에 적용하고 과거 승인 ZIP은 보존한다.

- 넘버링은 G-D98·G-D175·G-D178을 따른다. 원장·upload 중복 확인 후 다음 미사용 ID를 등록하고 패키지 파일명에 회차 ID를 넣는다. 실행 정본은 `upload/<ID>/current/`, 미승인 검토 자료는 `upload/<ID>/review/`에 둔다. 날짜·정책명으로 회차를 대신하지 않으며 예약 번호를 실행 완료처럼 보고하지 않는다.

- **경로 계약(2026-09-13 사용자 정정): `upload/plan/`에는 계획 문서만 저장한다.** 튜닝 업로드 ZIP, 검토용 ZIP, SHA, 배포 manifest와 실행 파일은 `upload/` 또는 기존 작업별 release 디렉터리에 저장한다. 생성 전 `upload/README.md`를 확인하고 전달 전 경로를 검사한다. 이 규칙은 모든 서브에이전트에도 적용한다. 검토용 자료와 서버 실행 패키지는 별도로 표시한다.

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

<!-- GO2:REPORT-FIRST:START -->
## 학습 report 필독·원인 우선 연구 계약 (2026-09-13 사용자 결정)

H1·Go2 튜닝 기획·평가·보고를 수행하는 메인과 모든 서브에이전트에 적용한다.
보고서 존재 확인이나 다른 배우의 요약만으로 읽었다고 하지 않는다.

1. **튜닝 후보 선정 전에 해당 정책과 대조군의 학습 `report.html` 본문을 직접 읽는다.**
   학습 run·checkpoint iter/model SHA·env reward snapshot·학습 로그와 대응을 확인한다.
   파일명/수정시각/같은 폴더만으로 대응을 확정하지 않는다. export 해시 차이는 tensor 의미 차이로 단정하지 않는다.
2. `REPORT_READ_STATUS=READ_MATCHED|READ_UNMATCHED|MISSING|NOT_APPLICABLE`를 출력한다.
   읽은 경로·보고서의 학습시각/iter/보상값·대조한 로그와 정책 식별자·일치/불일치·미확인 근거를 남긴다.
   `READ_MATCHED`는 대응 확인이지 성능 판정이 아니다.
3. 학습 HTML, 내부 `SELF_EVAL_REPORT`, 기술 개선 제출문은 서로 다른 자료다.
   평가 전용 run은 새 학습 HTML이 없을 수 있으나, 튜닝에 쓰는 정책의 원 학습 report 조회를 생략하지 않는다.
   `NOT_APPLICABLE`은 정책을 생성하지 않은 도구 smoke 등 실제 비해당 사유를 적을 때만 사용한다.
4. report 누락/오래된 파일/정책 대응 불명은 `REPORT_REQUIRED_NOT_ACQUIRED` 또는
   `REPORT_POLICY_UNMATCHED`로 기록한다. 먼저 로컬 원 학습 bundle·보존 snapshot·로그를 검색한다.
   그래도 없으면 회수/복구 방법을 기록한다. 추정 HTML을 원본인 것처럼 만들지 않는다.
   이 상태는 **새 reward 후보 확정·새 학습 착수**를 막지만 기존 증거 읽기·누락 자료 복구·진단 설계는 허용한다.
5. 연구 순서는 **학습 report·env·로그 대응 → 내부 시나리오 평가 → 영상/telemetry로 실패 유형 구분
   → 경쟁 가설 비교 → 근거 있는 단일변수 후보 → 대조 실험·독립 seed**다.
   HTML의 안정/공격 설명과 일반 경고는 가설 단서일 뿐 인과효과·최적 가중치 근거가 아니다.
6. 학습낙상률/terrain level/mean reward를 시나리오 survival/tracking 또는 공식 점수로 바꾸지 않는다.
   보고서 수치의 집계 구간과 지표 출처를 확인하고, 충돌은 원 로그와 evaluator 조건으로 해소한다.
7. 새 학습 회수에는 같은 run의 `report.html`과 로그·env·checkpoint 대응 자료를 결과 bundle 및 SHA 목록에 포함한다.
   누락하면 해당 공백을 기록하며 다운로드 완결 또는 튜닝 근거 완결로 보고하지 않는다.
8. 최신 지침은 역할 문서의 과거 다음 실행·고정 현재단계보다 우선한다. H1/Go2 캠페인은 분리한다.
   서브에이전트는 권한 범위 내 직접 읽기만 수행하고 공백을 상위에 보고한다. 이 계약은 편집/서버 권한을 추가하지 않는다.

## 2026-09-13 연구 방향 변경 — G-D-REPORT-FIRST-20260913
- 사용자 결정: 지침과 서브에이전트에 학습 report 필독을 강제하고 연구 방향을 변경한다.
- 새 순서: report·env·학습로그/정책 대응 → 시나리오 약점 → 실패 유형/경쟁 가설 → 후보 선정.
- 이전 T1 `ang_vel_xy_l2 -0.05→-0.06`은 **DEFERRED_HYPOTHESIS**로 내린다. 다음 튜닝값/1순위가 아니며 효과 INCONCLUSIVE.
- G5 하강 생존은 현재 평가상 우선 진단 대상이나 원인은 미확정. 회전 과다, 발걸림/정지, 낮은 자세,
  학습 성숙도 및 평가/영상 대응 문제를 구분한다. 모두 가설이며 보고서만으로 인과를 판정하지 않는다.
- Pilot HTML은 직접 읽었으나 이번 작업에서 정책 대응을 완결 검증하지 않았으므로 READ_UNMATCHED.
  A017 원 학습 HTML은 현재 탐색 범위에서 MISSING / REPORT_REQUIRED_NOT_ACQUIRED.
  A027 SELF_EVAL_REPORT는 원 학습 HTML을 대체하지 않는다.
- NEXT: 로컬 원 학습 bundle·snapshot·로그에서 A017/Pilot report 대응을 먼저 회수·검증한다.
  그 후 필요한 진단을 다시 동결한다. 기존 18case 목록은 제안 범위이며 실행 승인/고정 패키지가 아니다.
- 서버 실행·reward/배포코드 변경 없음. 새 학습 HOLD — report 대응 및 진단 근거 미완료.
- 작업 ID GO2-P1-PREP-20260913 유지. 과거 승인 release와 결과는 변경하지 않는다.
<!-- GO2:REPORT-FIRST:END -->
