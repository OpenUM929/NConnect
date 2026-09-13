# Go2 Planner Brief

## 1. 현재 결론

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
