# Go2 새 세션 인계: 기존 분석을 짧은 개선 실험으로 연결

작성: 2026-09-14. 작업 참조 G-A029. 세션 경로 NEW-CONTINUATION.
문서 성격: **남은 판단을 한 번에 닫는 분석 계획 + 조건 충족 시 서버 실행 계획**.
서버 실행 승인이나 실행 패키지가 아니다. 새 작업 번호는 예약하지 않았다.

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 축의 실제 보행 개선. 분석 근거는 의도·리포트 축에도 보존한다.
- [현재 단계] 0/6 — A017 원 학습 report 대응 미완료. 행동 약점 분석은 일부 완료됐다.
- [확보] A027 비교 정량, 학습 로그, env, 영상 일부 판독, 구체 reward 초안.
- [미확보] 원 report 대응, 후보 선택 판단 완료, A017 실행 패키지 지원·최종 검증.
- [이번 테스트] 낙상 원인 전수규명 대신 G3/G7 속도 부족을 겨냥한 단일변수 screening.
- [흐름] 기존 평가 → **남은 로컬 판단** → 충족 시 패키지·짧은 학습 → 실패 시 가설 철회 → 전체 평가·제출.
- [지금 할 일] 이 문서를 새 세션에 전달. 아직 서버를 켜지 않는다.
- [보장하지 않음] 탐색값과 단일 seed 실험은 개선·공식 점수를 보장하지 않는다.

## 1. 요청과 완료조건

사용자는 10시간 넘는 반복 준비/진단 대신 보행 개선을 위한 실제 튜닝을 요구했다.
새 세션의 결과물은 문서 추가가 아니라 다음 둘 중 하나여야 한다.

1. 실행 조건 충족: **번호가 있는 서버 업로드 ZIP + SHA + 검증 결과 + 실행 한 줄 + 회수 경로**.
2. 조건 미충족: 실행을 막는 정확한 사실·규칙과 이를 해소할 단일 조치. 같은 자료 재평가나 검토 ZIP으로 완료를 대신하지 않는다.

분석 완료와 인과 확정을 구분한다. 실험 전에 원인을 전부 증명할 필요는 없지만,
어떤 가설을 시험하고 어떤 결과에서 철회할지는 확정해야 한다.

## 2. 재사용할 분석 — 다시 서버에서 측정하지 않는다

정본 보고서: `workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md`.
우선 읽을 원장: `GO2_REWARD_EVIDENCE_MASTER.md`, `GO2_PROJECT_STATE.md`, `ARTIFACT_MANAGEMENT.md`.
기체 규칙·upload 양식도 읽되 과거 고정 next-action보다 최신 사용자 결정을 우선한다.

| 자료 | 이미 얻은 판단 | 재사용 한계 |
|---|---|---|
| A027 `evaluation/{a017,pilot}/SELF_EVAL_REPORT.json`, 각 `steps.csv` | A017 기존 내부식 39.76495 vs Pilot 33.67132 /70; G3/G7 속도 부족, G4/G6 회귀 | 공식 점수 아님. 높이 계측 불확실성을 보존 |
| G3 forward@101 CSV | 명령 vx .5, 실제 평균 .221 m/s | t>=.5 전체 env/time 평균. 원인 인과 미확정 |
| G7 dr_seed_202@202 CSV | 명령 vx .5, 실제 평균 .244 m/s; 대부분 자세 유지 | DR가 쉬운 문제라는 뜻 아님 |
| A028 감사 원장 | 계단 정체와 scanner 평균높이 해석 한계 | 원자료가 없으면 직접 판독했다고 쓰지 않음 |
| A017 학습 로그 | 1000iter 학습, reward-best step856에서 model_900.pt 선택 | 원 HTML 대체 불가; 학습 보상은 시나리오 성능 아님 |
| 기존 로컬 35 tests | reward 단일변경/문법, report 회수·ZIP/SHA·엔진 계약 | 실제 시뮬레이터·보행 개선을 검증한 것이 아님 |

G1/G2는 보존, G3/G7은 우선 개선, G4/G6는 회귀 감시, G5는 별도 문제다.
G5 낙상 완치를 모든 개선의 시작 조건으로 두지 않는다. /70 비교가 불확실해도 유효한 원시 추종 부족 관측은 버리지 않는다.

## 3. 새 세션 첫 작업: 한 번의 로컬 판단 종료

### A. 재개 감사 — 기존 산출물 확인만
`git status --short`와 본 문서/분석 보고서/조건부 JSON의 변경 여부를 한 번 확인한다.
이전 한국어 원장 append 일부가 `?`로 저장된 사실이 확인됐다. 해당 행을 근거로 해석하지 않고
정상 UTF-8 분석 보고서와 이 인계 문서를 사용한다. 정정은 UTF-8을 검증한 append로만 남긴다.
원 artifact 및 승인 ZIP을 수정하지 않는다.

### B. 후보 판단 — 광범위한 추가 진단 금지
대상 초안: `upload/G-A029/review/GO2_G_A029_ACTION_RATE_M0008_DRAFT.json` 및 같은 이름의 reward Python 파일.

- A017 대비 **action_rate_l2 -0.01→-0.008**만 변경한다는 가설이다.
- 다른 5개 값: track1.4, feet.2, lin_z-2, ang_xy-.05, flat0. yaw 등 나머지 배포 설정 유지.
- 가설: 동작 변화 벌점 완화로 지형 대응 및 명령 추종이 개선될 수 있다.
- 경쟁 가설: 떨림·미끄러짐이 이미 문제라면 악화된다.
- 정확한 -.008은 20% 완화 탐색폭이지 실측 최적값/논문 권고값이 아니다.
- **미확정:** action_rate를 첫 screening으로 선택할 판단은 아직 닫히지 않았다.

다음 세션은 기존 reward 구현·현재 로그를 대조하여 이 가설을 짧은 실험으로 시험할 가치가 있는지 한 번 판단한다.
관련 함수가 로컬에 없으면 공식 upstream 정의만 좁게 확인한다. 외부 인증 실패를 반복 호출하지 않는다.
결과는 `조건부 실험 채택` 또는 `기각 + 구체 반증`으로 남긴다. 다른 값을 임의로 확정하거나 모든 reward 조사로 확장하지 않는다.
action/contact 추가 채널이 원인 설명에 유용하다는 이유만으로 별도 서버 진단을 선행시키지 않는다.
필요하다면 같은 후보 평가에 읽기 전용 계측으로 묶되, 규정·권한·구현이 확인된 범위로 한정한다.

### C. report 규칙 충돌 — 숨기거나 우회하지 않는다
현재 A017 REPORT_READ_STATUS=MISSING, Pilot READ_UNMATCHED.
G-A028 `review/REPORT_RECOVERY_SEARCH.json`에는 기존 52archive 탐색 기록이 있다.
**같은 archive 전수검색을 다시 하지 않는다.** 새로 들어온 보관 사본만 확인한다.

원본을 찾으면 본문·run·env·로그·checkpoint 대응을 확인한다.
찾지 못하면 현 AGENTS의 '원 report 누락 시 새 후보 확정/학습 착수 금지'가 여전히 적용된다.
이는 '원인 분석이 전부 부족함'과 다른 차단이다. 서버를 켜서 부가 진단을 해도 해소되지 않는다.
새로운 보관 사본도 없으면 **원본 제공 또는 해당 규칙의 명시적 변경이 필요하다**고 한 번만 보고한다.
새 세션이나 현재 사용자의 계획 요청을 규칙 변경 승인으로 해석하지 않는다.
원본 없는 상태에서 당시 HTML을 재생성해 원본으로 가장하거나 보고서 복구만을 위해 무단 재학습하지 않는다.

## 4. 조건 충족 시 로컬 패키지 완성

| 등급 | 작업 | 완료 증거 |
|---|---|---|
| 조사 | 후보 판단·report 조건 종료 | 위 B/C의 명시적 결론 |
| 개선 | 엔진의 A017 기준정책 지원 | 정확한 model/env 식별자·reward snapshot 검증. Pilot로 대체 금지 |
| 개선 | 실제 실행 spec·runner 연결 | 현재 schema 검증 및 재개/부분 실패 모의 검사 |
| 개선 | 측정 계약 고정 | 아래 평가 case·seed·영상 manifest, 동등한 baseline 조건 |
| 필수(제출요건) | 배포 생성 경로 무결성 | train.py/play.py/task 원본 유지. 위반 시 ▲ 제출 불가 |
| 개선 | numbered current 발행 | 중복 확인·번호 등록, publisher·history·manifest·SHA·실행 가이드 |

계획 파일은 upload/plan, 실행 ZIP은 `<ID>/current`, 미승인 파일은 `<ID>/review`에 둔다.
G-A029는 기존 작업 참조다. 실행 회차 ID는 당시 원장·upload 중복 및 기존 예약 의미를 확인한 후 정한다.
기존 공용 engine 테스트 성공을 A017 spec 지원 증거로 재사용하지 않는다.
최소 변경에 필요한 테스트만 실행한다: spec/identity, 단일변수, report 회수, 패키징 실패경로, LF/bash -n, ZIP CRC/SHA, diff check.

## 5. 서버 실험 — 채택 및 발행 조건 충족 후에만

### 학습
- 1차 예산: from-scratch seed42, 4096env, 1000iter **1회**. A017 원 설정과 동등함을 발행 전 확인한다.
- 기존 A017는 동결 비교군이며 resume하지 않는다. checkpoint 선택 규칙도 동일하게 유지한다.
- reward 한 값 이외의 배포 학습 코드는 변경하지 않는다. 3000/5000/장기학습 자동 분기 없음.
- 예상 학습 시간 참고: 기존 A017 로그 약57분. 평가·렌더링·업로드/다운로드 시간은 별도이며 현재 실측 없음.
- 발행 전 보존 로그의 실제 구간시간으로 전체 시간과 TTL 회수 여유를 산출한다. 57분을 총 서버 시간으로 안내하지 않는다.
- 수치 발산·프로세스 실패·회수 여유 소진 시 새 단계를 시작하지 않고 현재 checkpoint/로그/실패상태를 부분 회수한다.

### 평가: 학습 결과가 다음 결정을 가르는 최소 범위
1. 기존 registry에서 G1 forward_fast, G2 diagonal_left, G3 rough_forward,
   G4 slope_plus_20, G5 stairs_15_up, G6 push_pos_x, G7 dr_seed_101의 seed101을 먼저 평가한다.
2. G3/G7 목표와 기존 강점 회귀를 보고 명백한 악화면 종료·회수한다. 부분 평가로 /70 생성 금지.
3. 유망한 경우 같은 세션에서 registry의 seed202/303 대표평가를 이어간다. 별도 서버 재접속을 기본 경로로 만들지 않는다.
4. 후보 승급 판단에는 69case 전체, 생존·추종·진행거리와 필수 영상이 필요하다. G4 반대 경사, G6 반대 충격, G3 횡이동, G5 하강을 대표평가 성공으로 대신하지 않는다.
5. baseline 평가 조건을 바꾸지 않았고 identity가 같으면 기존 유효 결과를 재사용한다.
   자세 측정식을 고치면 영향받는 baseline/candidate를 동일 조건으로 비교한다. 높이 해석 모호성을 조용히 고치거나 무시하지 않는다.

영상: 대표 7case×3seed, 최대 21개 후보 영상, 1000step 기준으로 발행 manifest에 고정한다.
조기 종료 시 실행된 단계의 영상을 모두 보존한다. full 평가 승급 시 대표영상에서 빠진 실패/회귀 조건 영상을 추가한다.
영상과 telemetry의 동일 rollout 여부를 기록하고, 다른 실행이면 frame-step 일치라 주장하지 않는다.

제안 성공 기준(발행 전에 확정): 목표 G3/G7의 paired seed별 RMSE 5% 이상 감소·진행거리 비열등,
생존 비회귀, 기타 tracking proxy 감소 .02 이내. 공식 기준이 아니며 목표 개선만으로 최종 후보 승급하지 않는다.
하나라도 측정 의미가 모호하면 INCONCLUSIVE. 실패하면 -.008 가설 철회·A017 보존.
유망하면 독립 학습 seed43 반복을 다음 별도 결정으로 제안하며 자동 실행하지 않는다.

## 6. 회수와 종료 — 추가 요청 없이 패키지에 포함

학습 종료 직후, 평가가 exported를 덮어쓰기 **전**에 같은 run의 원본 `report.html`을
`_keep/<튜닝명칭>/exported/report.html`에 보존한다.
필수: model/checkpoint, policy, env, report 원본, 원 학습 로그/tfevents, source identity,
실행된 평가의 영상/telemetry/summary, STATUS·종료코드, 내부 SHA 목록.
정상 및 실패 경로에서 하나의 결과 ZIP과 외부 SHA를 만든다.
report missing/empty/stale은 REPORT_REQUIRED_NOT_ACQUIRED. 성공 완료 표식을 출력하지 않는다.

로컬 회수 후 manifest·SHA·report 대응·필수 영상/정량을 검증하기 전 서버 종료 가능이라 하지 않는다.
실행 가이드에 ZIP 절대경로, 서버 업로드 위치, 검증된 실행 한 줄, tmux 확인,
완료 표식, 결과 ZIP/SHA 다운로드 경로, 예상 총시간을 모두 넣는다.
이 계획에는 검증되지 않은 서버 명령을 넣지 않았다.

## 7. 새 세션 복사용 요청

```text
C:\dev\Nconnect에서 이어서 진행하라.
workspace/training/quadruped/upload/plan/GO2_G_A029_NEW_SESSION_EXECUTION_PLAN.md를 먼저 읽어라.
목표는 Go2 보행 개선 실험을 실제 서버 실행 패키지로 연결하는 것이다.
기존 약점 분석을 다시 시작하거나 A027/A028 전체를 반복 평가하지 마라.
첫 작업은 §3의 한 번의 로컬 판단이다. -.008은 조건부 가설이며 확정 효과가 아니다.
원 report 누락 규칙과 과학적 불확실성을 분리하라. 규칙을 임의 우회하지 마라.
실행 조건이 충족되면 §4~6의 번호 있는 ZIP·원본 report 회수·실행 가이드까지 완성하라.
조건이 충족되지 않으면 정확한 차단과 해소 조치 하나를 보고하고 대체 진단을 늘리지 마라.
허용: 로컬 분석/계획·패키지 도구·테스트. 금지: 서버 무단 실행, 배포 학습 코드 변경,
기존 정책·승인 ZIP·원자료 덮어쓰기, review 파일을 실행 완료로 보고하기.
결과는 이 새 세션에서 사용자에게 보고하고 GO2_PROJECT_STATE.md 및 마스터에 UTF-8로 기록하라.
새 세션은 이전 작성자의 후속 작업이며 독립 감사로 주장하지 마라.
```

NEXT: §3-A 재개 감사 → §3-B 후보 가치 판단과 §3-C report 조건을 한 번에 정리.
완료 후 목적지: 실행 조건 충족이면 패키지 발행/사용자 서버 실행, 아니면 구체 권한·원본 차단 보고.

## 2026-09-14 G-A029 §3 판단 종료 — NEW-CONTINUATION / HOLD
- 재개 감사: 시작 시 git status 확인. 기존 사용자 수정과 미추적 파일은 보존했다. 이전 입력의 기준 해시가 없어 파일 불변을 주장하지 않으며, 현재 계획·약점 보고서·조건부 JSON을 직접 읽었다. 한국어가 ?로 깨진 과거 append는 근거에서 제외한다.
- §3-B: **조건부 실험 채택(실험 가치만, 후보 확정·학습 승인 아님)**. action_rate_l2 -0.01→-0.008은 동작 변화 벌점 크기를 20% 줄이는 단일변수 탐색이다. 기존 G3/G7 속도 부족과 연결되는 반증 가능한 가설이며, track 추가 강화에서 관찰된 G4/G6 회귀를 무시하지 않는 대안이다. 원인을 증명한 것은 아니다. 목표 RMSE/진행거리 개선 실패 또는 생존·기존 추종 회귀 시 철회하며 자동 연장하지 않는다. action/contact 별도 서버 진단을 선행조건으로 추가하지 않는다.
- 직접 근거: quadruped_rewards.py:73-76은 부드러움/민첩성 tradeoff를 설명한다. A017 candidate_training.log:33165의 action_rate 보상 -0.1004는 항이 작동했다는 단서일 뿐 억제 원인·포화 증거가 아니다. 같은 로그 말미의 최고19.78@856, 지형4.25, 학습낙상 진단10.6%, std0.548은 원 HTML의 예상 대조값이지 시나리오 성능이 아니다.
- 로컬에서 함수 정의를 찾지 못해 공식 upstream만 좁게 열람했다: https://raw.githubusercontent.com/isaac-sim/IsaacLab/main/source/isaaclab/isaaclab/envs/mdp/rewards.py (2026-09-14 열람, action_rate_l2 L225-227). 연속 action 차이 제곱합을 벌점화하는 정의다. main의 현재 정의이며 당시 서버 버전 동일성 또는 -0.008 최적값을 검증하지 않는다.
- §3-C: **REPORT_READ_STATUS=MISSING (A017), REPORT_REQUIRED_NOT_ACQUIRED**. 기존 52archive 내부 목록은 재검색하지 않았다. 기존 목록에 없던 6개 ZIP만 추가 확인했고 모두 report.html 항목 0개였다. 6개 모두 파일 수정시각은 이전 검색보다 오래되어 새로 다운로드됐다고 주장하지 않는다.
- 추가 확인 경로: workspace/_keep/{GO2_A017_FULL_SUITE_RESULT.zip,GO2_DEFAULT_VS_PILOT_RESULT.zip,GO2_FEET_AIR_TIME_020_RESULT.zip,GO2_PILOT_V2_BASELINE_RESULT.zip}; workspace/server_returns/{go2_default_vs_pilot_v1_full_260901/original/GO2_DEFAULT_VS_PILOT_RESULT.zip,go2_feet_air_time_020_v1_full_260901/original/GO2_FEET_AIR_TIME_020_RESULT.zip}. 이번 검사는 내부 이름 목록 확인이며 SHA/CRC 검증 완료 주장이 아니다.
- Pilot READ_UNMATCHED는 앞선 직접 열람 기록을 유지하며 이번에 HTML 본문을 새로 읽거나 정책 대응을 확정한 것은 아니다. A017 원 HTML 부재 상태에서 Pilot 재감사를 늘리지 않는다.
- 정확한 차단: AGENTS.md report-first §4가 원 학습 report 누락 시 새 reward 후보 확정·학습 착수를 금지한다. 사용자 인계 요청은 규칙 변경이 아니다. 따라서 current 실행 ZIP·실행 명령은 발행하지 않았다. A017 엔진 지원과 측정 manifest 검증도 아직 수행하지 않았으며 보고서 도착만으로 실행 준비 완료가 되지는 않는다.
- 단일 해소 조치: **A017 원 학습 report.html의 외부 보관 사본 제공**. 원 로그가 기록한 생성 위치는 /workspace/_go2_tuning_runtime/go2_g_a017_pilot_track_lin_vel_xy_140/candidate/exported/report.html 이다. 대상 model_900.pt, reward-best step856, model SHA 0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4. 원본을 받으면 run/env/log 대응 확인 후 기존 계획 §4부터 진행한다. 재생성 HTML이나 SELF_EVAL_REPORT로 대체하지 않는다.
- 서버 실행·학습·원 artifact/승인 ZIP 변경 없음. G-A029 학습 lifecycle PLANNED 유지. 현재 단계 0/6. reward 효과: track 부분 만족(기존 한계 유지), action_rate 미측정, feet/lin_z/ang_xy/flat INCONCLUSIVE.

## 2026-09-14 사용자 결정 G-D-TUNING-DELIVERABLE-20260914 — §1-2·§3-C·위 차단 판정 대체
- 루트 `AGENTS.md` 「튜닝 요청 산출물 계약」과 개정된 report-first §4에 따라 **A017 report 부재는 더 이상 발행 차단이 아니다.**
  §3-C의 "새 세션이나 현재 사용자의 계획 요청을 규칙 변경 승인으로 해석하지 않는다"와 위 "정확한 차단"·"단일 해소 조치"는 `SUPERSEDED`.
- §3-B의 조건부 채택(-0.008)을 그대로 확정값으로 쓰고 §4~6을 진행한다. 결과물은 번호 있는 `current/` ZIP이며, 막히면 계약 3항의 세 사유 중 무엇인지만 보고한다.
- **[같은 날 정정 — G-A029 튜닝 감사 AUDIT_FAIL]** 위 행과 §3-B의 -0.008 채택을 철회한다. 같은 변경이 G-A018에서 대칭 v2 −44.40/70으로 기각(G-D81)됐는데 §2·§3-B가 이를 대조하지 않았다. 보고서: `workspace/training/quadruped/reports/GO2_G_A029_TUNING_AUDIT_20260914.md`. §4~6의 패키지·회수 계약은 다음 후보에 재사용한다.