# Go2 Planner Brief

> **§1~§6은 `HISTORICAL — 260901 스냅샷`이다(2026-09-14 표시, 캠페인 감사 P2).** 현재 위치·기준선·NEXT는 루트 `GO2_NOW.md`를 따른다.
> 이 문서의 §1~§6을 현재 상태로 인용하지 않는다. §7 이후는 날짜별 이력이다.

## 1. 현재 결론 (HISTORICAL 260901)

- 가장 이른 미완료 단계: **3/6 환경 적응 게이트**
- 보존 비교군: `train_260831-Go2_5var_1000`, iter 999, model SHA `c4d78adf…af8d`
- 분류: `MULTIVARIABLE_EXPLORATORY_BASELINE`
- 실험 기준선: Default-01 iter 800, model SHA `99ceeaa1…4676`; G1~G7 69 telemetry·7영상 검증 완료
- 새 학습: **`feet_air_time 0.01→0.20` only, 1,000 iter G-A007만 승인**

## 2. 확보

- Pilot-01과 Default-01 checkpoint/model/env/tfevents/report 회수·lineage 검증
- 정책별 G1~G7 telemetry 69건·worst-case 영상 7개와 `VIDEO_OBSERVED`
- Default `17.90699/70`, Pilot `41.97990/70`, 분기 `SHARED_WEAKNESS_FOUND`
- 강좌 기반 reward 근거와 canonical G1~G7 registry
- G-A007 단일변수 PRD와 상세 승급·실패·INCONCLUSIVE 계약
- 실행 package `go2_feet_air_time_020_v1.zip` 로컬 검증 완료(SHA `f7da2c5e…af49`)

## 3. 미확보

- G-A007 candidate 학습 artifact·69 telemetry·7영상
- `feet_air_time` 단독 인과 판정
- G3·G4·G5·G7 내부 게이트 충족 정책
- 독립 학습 seed 재현성
- 공식 결과

## 4. reward 축 상태

| 축 | 상태 | 이유 |
|---|---|---|
| track_lin | INCONCLUSIVE | Pilot 조합 개선은 확인됐지만 네 변수 동시 변경 |
| feet_air | INCONCLUSIVE — G-A007 실행 대기 | G5 개선과 G3/G5 survival 회귀의 단독 기여 미측정 |
| lin_vel_z | INCONCLUSIVE | Pilot 적극 이동·안정 trade-off 가능, 단독 실험 없음 |
| ang_vel_xy | INCONCLUSIVE | rough/stairs 불안정과 경사 개선 공존, 단독 실험 없음 |
| action_rate | 미측정 | 불변이며 jerk 정량 없음 |

어떤 축도 포화·탐색 종료로 표시하지 않는다.

## 5. 다음 기획 제약

1. 기존 `server_run_Go2_videos.sh` 사용 금지.
2. 검증된 통합 package 외 runner를 사용하지 않는다.
3. 후속 학습은 Default-01 계보 from-scratch·one-at-a-time만 허용한다.
4. `Train/mean_reward`는 정책 간 비교에 사용하지 않는다.
5. 현재 최대 감점 G5와 약한 tracking/completion 때문에 `feet_air_time=0.20`만 1k로 검사한다.
6. G-A007이 정량·영상 게이트를 모두 만족하기 전 다른 reward나 3k 이상을 시작하지 않는다.

## 6. NEXT

`workspace/training/quadruped/go2_feet_air_time_020_v1.zip`을 `/workspace/`에 업로드하고 아래 한 줄을 실행한다.

`cd /workspace && unzip -oq go2_feet_air_time_020_v1.zip && cd /workspace/go2_feet_air_time_020_v1 && bash server_run_go2_feet_air_time_020_v1.sh`

완료 후 `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip`과 `.sha256`을 `workspace/_keep/`에 회수한다. 로컬 검증 전에는 서버를 종료하지 않는다.

## 7. ?? ?? ? G-A008 evaluator v2

> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시).** 원문을 추측으로 복원하지 않는다. 대체 기록: `GO2_REWARD_EVIDENCE_MASTER.md` §10·§11.

- v1 ?? resume ??? ????: `BUGGY_DO_NOT_REUSE`.
- ??? reward? checkpoint? ??? telemetry hard exit? upstream cleanup? ????, runner? ?? startup crash? fail-fast? ???.
- v2? graceful loop stop, case/video 3? bounded retry, ?? case fingerprint ???, stable launcher snapshot? ????.
- package: `workspace/training/quadruped/go2_feet_air_time_020_v2.zip`
- SHA: `73c6ba1f9cc29b22889d146e4c949ff54b7a9e2b4638199f61c9961dc9f88dbc`
- ?? ??: `INTERNAL_GATE_INCONCLUSIVE`; reward ? ?????? ??.
- NEXT: ?? v1 ????? ?? ???? ?? v2? ??? resume??.

<!-- GO2:REPORT-FIRST:START -->
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

### G-A029 ? 2026-09-14 ?? ?? ?? ? ?? ??? ??
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시).** 원문을 추측으로 복원하지 않는다. 대체 기록: 바로 아래 「G-A029 §3 종료」 절과 이후 정상 절.
- ??? ??: ?? ?? ??? ???? ???? ????? ?? ?? ?? ??. ?????? ?? ??? ?? ???.
- ?? ???: workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md. G3/G7 ?? ??? ?? ???? G1/G2 ???G4/G6 ?? ??, G5 ??? ?? ????. ?? ??? ?? ??? ?????? ?? ???.
- A017 ??? ??: action_rate_l2 -0.01?-0.008(20% ?? ???, ??/??? ???). ?? Python reward ?? ??? baseline ??, ??? JSON? upload/G-A029/review? ??. ?? ??? ?? ??? ??.
- REPORT_READ_STATUS: A017 MISSING, Pilot READ_UNMATCHED ??. ?? ??: ?? engine? A017 frozen baseline ???, ?? manifest ? ?? ?? ?? ???. ?? ?? ??/current/history ?? ??.
- ?? ??: 35 unittest ??(?????Python ??/LF??????report fresh/missing/empty/stale?ZIP/SHA?shell ???engine ??). ?? ??/?? ?? ???. ?? lifecycle PLANNED, ?? ?? ??.

### 2026-09-14 G-A029 §3 종료 — HOLD / 원 보고서 회수
- NEW-CONTINUATION으로 지정 계획 §3을 종료했다. -0.008은 조건부 실험 가치만 인정하며 후보 확정/학습 승인이 아니다. A017 REPORT_READ_STATUS=MISSING / REPORT_REQUIRED_NOT_ACQUIRED로 실행본 발행 차단.
- 기존 52archive 재검색 없이 목록 밖 ZIP 6개를 확인했으나 report.html 0개. 상세 경로·직접 코드/로그 근거·한계는 GO2_REWARD_EVIDENCE_MASTER.md의 같은 날짜 §3 판단 종료 행과 기존 인계 계획에 기록했다. 깨진 과거 append는 판정 근거에서 제외한다.
- NEXT 하나: A017 원 학습 report.html 외부 보관 사본 회수 → run/env/log/model_900 대응 확인 → 기존 계획 §4 패키지 구현·검증. 추가 서버 진단이나 새 검토 ZIP을 만들지 않는다.
- G-A029 PLANNED, 단계0/6, 서버/학습/실행 ZIP 발행 없음. 역사 일정 CLOSED 유지. 원 자료·승인 release 보존.

### 2026-09-14 G-D-TUNING-DELIVERABLE-20260914 — 위 HOLD·NEXT 대체
- 사용자 결정: 튜닝 요청의 산출물은 `upload/<ID>/current/` 실행 패키지다. 검토 자료로 대체하지 않는다(루트 `AGENTS.md` 「튜닝 요청 산출물 계약」).
- A017 원 report.html 부재는 `REPORT_REQUIRED_NOT_ACQUIRED — 복구 불가`로 기록 완료. 원 학습 로그 요약(최고 19.78@856·지형 4.25·학습 낙상 10.6%·std 0.548)과 A027 SELF_EVAL로 대체하며 더 이상 발행을 막지 않는다.
- NEXT 하나: A017 기준 `action_rate_l2 -0.01→-0.008` 단일변수 1,000 iter 패키지를 `current/`로 구현·검증·발행한다. 외부 사본 회수·추가 진단·review ZIP은 만들지 않는다.

### 2026-09-14 G-A029 감사 AUDIT_FAIL — 위 NEXT 철회
- 같은 변경이 G-A018에서 대칭 v2 −44.40/70·7/7 생존 후퇴로 기각됐다(G-D81). 표적도 최대 감점 인수(G5 10.50, G3 생존 .469)와 어긋나고, 값 근거는 "20% 완화"다. 성공해도 기대 이득은 약 0.29/70이다. 보고서: `reports/GO2_G_A029_TUNING_AUDIT_20260914.md`.
  - SUPERSEDED(G-D-PRIORITY-20260914, 2026-09-14): "표적이 최대 감점 인수와 어긋남"은 철회한다. 0.29/70은 민감도이고, 기대 가중 이득은 `미추정`이다. 판정은 같은 값 유효 기각과 비율 값 근거로 유지된다. 감사 보고서 §5 참조.
- 재시도 금지 축: `action_rate_l2` 완화(-0.008).
  - SUPERSEDED(F5): `-0.008`은 유효 기각 이력이 있으므로 새로운 검증 근거 없이 재시도하지 않는다. 같은 방향의 다른 크기도 기존 실패와 구별되는 근거가 필요하다. 방향 전체를 영구 금지하는 것은 아니다.
- NEXT: G5 또는 G3 생존을 표적으로 다음 단일변수를 선정한다. 유력 방향은 `flat_orientation_l2`(유효 측정 없음, 값 미확정)다. 선정한 값으로 `current/` 패키지까지 만든다.
  - SUPERSEDED(G-D-PRIORITY-20260914): 표적은 원장 §5 비교표로 정한다. flat은 비교 후보다. 현재 NEXT는 `GO2_NOW.md`를 따른다.
### GO2-REPLAN-A029-20260914 — 감사 후 사용자 요청 재계획
- 사용자 결정: G-A029 감사에 따라 메인 문제를 진단하고 튜닝 계획을 수립한다. 이번 요청은 계획이며 서버 실행/패키지 발행으로 확대하지 않는다. 역사 일정 CLOSED는 유지한다.
- G-A029 REJECTED_BY_AUDIT 및 -0.008 NEXT 철회 유지, review 불변. 과거 A017 HTML 누락을 발행 차단으로 복원하지 않는다.
- 계획 정본: workspace/training/quadruped/upload/plan/GO2_POST_A029_TUNING_PLAN_20260914.md.
- 직접 근거: A018 양 arm 각7case 모두 schema2/v2; A013/A025 baseline은 schema1/2 혼재, candidate는 schema2라 합산 비대칭. A027 G3 rough_lateral seed101/202/303의 base-contact 종료는 17/14/17개(/32), 첫 종료 전0.5초 q=1-gz² 평균 .688/.628/.660. 기울기는 연관성이지 최초 원인 확정 아님.
- 계획값: A017 조건 flat_orientation_l2 0→-1.0 단일변수, G3 접촉 종료/생존 표적; G5 정체·경사 회귀 동시 감시. -1은 관측 기반 단위 크기 exploratory 값이지 upstream 최적값/만족 판정 아님.
- REPORT_READ_STATUS: A017 MISSING(기존 복구 불가 확정 유지), Pilot READ_UNMATCHED(이번 HTML 본문 직접 열람, 정책 대응 미완결).
- NEXT: 다음 미사용 번호로 위 계획의 current 실행 패키지 구현·검증. 이번에 번호 예약/실행 ZIP/서버 명령은 발행하지 않았다. 학습·성능·공식 결과 새 측정 없음.
