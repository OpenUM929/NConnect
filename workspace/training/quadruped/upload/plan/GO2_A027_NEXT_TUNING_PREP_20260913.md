# Go2 다음 튜닝 준비 v2 — 2026-09-13

상태: PREPARATION_ONLY / HOLD — 진단 계측 및 독립 검토 미완료.
작업 ID: GO2-P1-PREP-20260913. v1과 승인 release는 보존한다.
이 문서는 v1의 다음 실행 준비에 대한 보완 정본이며 실행 승인서가 아니다.

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 개선을 위한 원인 진단.
- [현재 단계] 단계 3/6 환경 적응 게이트.
- [확보] A027 감사 기록, A017/Pilot 보존 정책. 이번 작업에서 재검증한 성능은 없음.
- [미확보] G5 하강 영상, wx/wy 계측, 독립 검토문, 실행 ZIP 검증.
- [이번 테스트] G5 하강 실패 이전 회전과 정지/발걸림을 구분한다.
- [흐름] 감사 → 준비 → 진단 충족 시 단일변수 screening → 미충족 시 가설 철회 → 제출 별도.
- [지금 할 일] 서버 접속 불필요. 검증되지 않은 기존 ZIP을 대신 실행하지 않는다.
- [보장하지 않음] 제안값·영상·단일 seed는 공식 점수 또는 개선을 보장하지 않는다.

## 1. 범위와 유지값
기준: GO2_REWARD_EVIDENCE_MASTER.md §19~20 및 v1 E1~E7.
A017 reward: tracking 1.4, feet_air_time 0.2, lin_vel_z -2.0,
ang_vel_xy -0.05, action_rate -0.01, flat_orientation 0.0.
tracking은 부분 만족, 나머지 개별 인과효과는 INCONCLUSIVE.
조건부 T1은 ang_vel_xy_l2 -0.05 → -0.06 only. 현재 미실행이며 가중치는 수정하지 않는다.
정확한 -0.06의 외부 문헌·성능 근거는 없음. 20%라는 간격은 탐색 제안일 뿐이다.

## 2. 검토 네 항목 반영
1. 진단: 각 영상의 policy/case/seed/env_id/frame↔step 대응을 기록한다.
   같은 seed라도 4env 영상과 32env 정량은 다른 rollout이며 인과 시간축을 연결하지 않는다.
   P1에서 먼저 실패 유형과 최초 이상 시점을 관찰한다. wx/wy 임계값·지속시간·반복 수는
   독립 검토 후 새 미관측 진단 실행 전에 동결해야 한다. 미동결이면 P2 진입 불가.
2. 채택: 새 paired control 대비 screening 성공은 reward 탐색 결과일 뿐이다.
   보존 A017 교체에는 동일 evaluator 전체69case에서 A017 대비 raw delta ≥0,
   각 case 생존 delta ≥-1/32, tracking delta ≥-0.05, G4/G6 점수 delta ≥0도 요구한다.
   새 control이 붕괴한 상태에서 상대 개선만으로 A017을 교체하지 않는다.
   이것은 제안된 공학적 안전선이며 통계적 비열등 증명이 아니다.
3. 조기중단: 유효한 paired case 생존 delta < -0.10이면
   INTERNAL_EARLY_KILL_FAIL(관측된 안전 위반)과 SELF_ASSESSMENT_INCOMPLETE(전체 미평가)를 병기한다.
   부분 점수 합산과 후보 승급은 금지한다. 원시 결함은 INTERNAL_GATE_INCONCLUSIVE로 구분한다.
4. 정지 편법: env별 root_x/root_y를 명령 방향으로 투영해 진행을 계산하되 reset 구간을 분리한다.
   영상에서 실제 첫 하강 계단 접촉, 정지/주저앉음/전도 시점과 마지막 도달 위치를 기록한다.
   접촉·진행 판독 불가이면 VIDEO_UNKNOWN이며 후보 채택 불가.
   진행량의 수치 문턱은 지형 위치와 종료 구간을 확인한 독립 검토에서 동결한다.

v1의 from-scratch 1000iter paired seed42, 재검증 seed43, 전체69case/arm,
성과 및 안전 문턱은 유지한다. 새 대조군·후보 모두 동일 배포 학습 원본을 사용한다.
5,000iter 초과 학습 및 자동 연장은 이 준비 범위 밖이다.

## 3. 발견된 실제 선행조건
- go2_eval_telemetry.py:168~175의 CSV에는 actual_wz만 있고 actual_wx/actual_wy가 없다.
  따라서 v1의 기존 각속도 채널로 roll/pitch 회전을 확인한다는 전제는 철회한다.
- server_run_go2_a017_full_suite.sh의 run_video는 NCRC_EVAL_OUT을 지정하지 않는다.
  기존 영상 runner는 같은 영상 rollout의 telemetry 확보를 보장하지 않는다.
- 새 계측은 배포 train.py/play.py/go2_task를 고치지 않는 별도 읽기 전용 모듈로 설계·검토한다.
  A027 scorer 및 승인 evaluator는 보존하며 새로운 계측 지문을 기존 승인 지문이라고 쓰지 않는다.
- GO2_A027_TUNING_OPUS_REVIEW_20260911.md는 로컬 탐색에서 발견되지 않았다.
  이번 사용자 요청은 준비 지시로 기록하며 과거 독립 검토 완료를 꾸미지 않는다.

## 4. 준비 단계와 실행 게이트
| 단계 | 등급 | 완료 조건 | 현재 |
|---|---|---|---|
| 계획 보완·case 목록 | 조사 | 2정책×3조건×3seed=18 고정 | 작성 완료 |
| 진단 계측 설계·검토 | 조사 | 같은 rollout wx/wy·자세·진행·영상 대응, 배포 원본 무수정 | 미완료 |
| P1 ZIP 준비 | 조사 | SHA/CRC/manifest/LF/bash -n, 실패 회수, 로컬 테스트 | HOLD — package 미검증 |
| P1 실행·회수 | 조사 | 영상18개+정량18case+영상 동시계측18개, 로그/identity/SHA | 외부 실행 미측정 |
| P2/P3 학습 | 개선 | 독립 검토와 진단 조건 충족, v1 실험 계약 동결 | HOLD — 근거 불충분 |
| 제출 검증 | 필수(제출요건) | 정책/env/리포트 대응 및 제출 무결성 | ▲ 제출 불가 — 이 작업은 제출 후보를 생성하지 않음 |

## 5. 회수·예산 계약
새 결과는 workspace/server_returns/GO2-P1-PREP-20260913/에 격리한다.
영상은 필수: 18개 각20초. 정량은32env×1000step、영상은4env 별도 동시계측.
직접 측정: G5 stairs_10_down/stairs_15_down, G4 slope_plus_20.
G1/G2/G3/G6/G7, G4 하강경사, G5 상승은 직접 측정하지 않으며 전체 /70을 만들지 않는다.
필수 회수: model/env 식별, source/evaluator 지문, case manifest, 18정량+18영상계측,
영상18개, 각 로그·종료코드, 실패로그, 결과 ZIP 및 SHA.
동일 보존 정책의 진단 재생이므로 새 학습 report.html을 생성했다고 주장하지 않는다.
서버 잔량·실측 시간은 미측정. 첫 paired case 비용과 포장·다운로드 여유를 재산정하며
잔량이 다음 단위+회수여유보다 적으면 새 단위를 시작하지 않는다.
실행 ZIP·한 줄 명령·완료표식·결과 경로를 검증해 제공하기 전 서버 실행 명령은 발행하지 않는다.

## 6. 남은 검토의 종료조건

2026-09-13 report 열람 반영: 회수 SELF_EVAL_REPORT 두 정책과 로컬 exported/report.html을 읽었다.
후자는 tracking1.2·2026-08-31 Pilot 계열 보고서이며 A017(tracking1.4)의 학습 report로 전용하지 않는다.
학습낙상률13.8%는 G5 생존 지표가 아니다. G5 우선 진단은 유지하되 -0.06 효과는 여전히 INCONCLUSIVE.
상세 근거는 GO2_REWARD_EVIDENCE_MASTER.md의 같은 날짜 report 열람 정정 참조.

정량 회전 판독 문턱, reset/영상 정렬 및 계단 접촉 판독 계약, 별도 계측의 무침습성,
실패 시 필수 자료 회수 테스트를 독립 검토한다. 이 문서는 그 검토를 대신하지 않는다.
현재 옛 baseline PRD/AGENTS의 G-A007/G-A010 명령을 새 준비에 재사용하지 않는다.
최신 GO2_PROJECT_STATE §48 및 본 문서를 다음 준비 참조로 사용하되 상위 규정을 대체하지 않는다.

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

## 자료 최소화 보완 — 2026-09-13
`GO2_EVIDENCE_NECESSITY_REVIEW_20260913.md`의 대체 가능성 표를 적용한다.
report는 영상/telemetry를 대체하지 않지만 기존 유효한 자료는 재사용한다.
위18case+18영상+동시계측 목록은 승인 수량이 아니다. 기존 자료별 identity/조건/판독성을 확인해
재사용분과 결측분을 분리한 뒤 새 실행량을 동결한다. report 확인만을 이유로 전체 평가를 재실행하지 않는다.
