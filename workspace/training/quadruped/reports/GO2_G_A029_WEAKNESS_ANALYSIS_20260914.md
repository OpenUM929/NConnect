# G-A029 약점 분석 및 조건부 튜닝 설계

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 개선과 설계 의도 근거 확보.
- [현재 단계] 0/6 증거·artifact 정합성: A017 원 학습 report 미확보.
- [확보] A027 정책별 69case 내부 결과, 학습 로그, env 및 기존 영상.
- [미확보] 원 report 대응, action/contact 원인 계측, 새 정책 성능.
- [이번 테스트] 로컬 가중치 파일 단일변경 및 report 회수 계약 검사. 새 학습 아님.
- [흐름] 기존 평가 → **약점별 초안** → 근거 해소 시 짧은 실험 → 실패 시 가설 철회 → 최종 평가·제출.
- [지금 할 일] 서버 실행하지 않음. 이 초안은 실행 승인을 대신하지 않는다.
- [보장하지 않음] 내부 수치·단일 seed·새 가중치 파일은 공식 성능 개선을 보장하지 않는다.

## 1. 결과: 낙상만이 문제가 아니다

직접 정량 근거는 `workspace/_keep/go2_a017_full_suite/evaluation/{a017,pilot}/SELF_EVAL_REPORT.json`과 해당 `cases/seed_*/<case>/steps.csv`다.
기존 내부식 합계는 A017 39.76495, Pilot 33.67132 /70이다. 높이 계측 한계가 있는 역사 수치이며 공식 점수·현재 제출 적합 판정이 아니다.

| 시나리오 | 영상 | 내부 정량: A017 최저곱 case의 생존/추종 | 공식 결과 |
|---|---|---|---|
| G1 전진 | 이 분석에서 재판독 안 함 | 1.000 / .8944 | 미측정 |
| G2 전방위 | 이 분석에서 재판독 안 함 | 1.000 / .8921 | 미측정 |
| G3 험지 | 전진 seed101 표본 3프레임만 관찰 | .4688 / .7574; 별도 전진 case 추종 .6282 | 미측정 |
| G4 경사 | +20도 seed101 표본 3프레임만 관찰 | .7500 / .6810 | 미측정 |
| G5 계단 | A028 원장상 정체 관찰; 이번 직접 재판독 아님 | .0000 / .1614; 물리적 낙상 해석 불확실 | 미측정 |
| G6 밀침 | 이 분석에서 재판독 안 함 | .9063 / .9616 | 미측정 |
| G7 DR | seed101 표본 3프레임만 관찰 | .9063 / .7209; 별도 seed202 추종 .6573 | 미측정 |

표의 생존·추종은 서로 독립적인 최저값이 아니다. 정성 표본 관찰로 전체 rollout을 VIDEO_OBSERVED로 승격하지 않는다.

원 CSV의 t>=0.5초 전체 env/time 행 평균(생존 개체만의 평균 아님):
- G3 rough_forward@101: vx 명령 .5, 실제 .221 m/s.
- G3 rough_lateral@303: vy 명령 .3, 실제 .077 m/s. A017의 자세 proxy 개선에도 Pilot 대비 진행거리는 개선되지 않았다.
- G7 dr_seed_202@202: vx 명령 .5, 실제 .244 m/s. 대부분 자세 기준을 유지하면서도 추종이 부족하다.
- G4 slope_plus_20@202: vx 명령 .5, 실제 .247 m/s. 낮은 높이 판정과 전도를 구별해야 한다.
- G5 stairs_15_down@303: 5초 이후 speed가 약 .02~.03 m/s로 정체한다. case 이름은 실제 하강 수행 증거가 아니다.

`evaluation/a017/source/go2_eval_telemetry.py:216-218`의 지면 높이는 scanner ray 평균이다. 경사·계단 경계에서 몸통 바로 아래 지면과 다를 수 있다. 낮은 높이 행 수를 낙상 횟수로 바꾸지 않는다. 기존 수치는 보존하고 해당 해석은 INTERNAL_GATE_INCONCLUSIVE다.

## 2. 개선 순서와 난이도

| 순서 | 등급 | 대상 | 의사결정 |
|---|---|---|---|
| 1 | 개선 | G3 전진·G7 속도 부족 | 같은 보행 반응 가설을 짧은 단일변수 실험으로 검토. 빠르게 해결된다는 보장은 없음 |
| 동시 감시 | 개선 | G1/G2 기존 추종, G4/G6 회귀 | 목표 개선을 위해 기존 강점을 잃지 않는지 확인 |
| 2 | 조사 | G3 횡이동 | 발 미끄러짐·접촉·자세 손실을 분리. 전진 결과로 대체하지 않음 |
| 별도 | 조사 | G5 정체 | 가장 큰 역사적 감점이지만 원인 불확실성이 큼. 다른 개선을 전부 막는 선행조건으로 두지 않음 |
| 최종 | 필수(제출요건) | 정책/env/제출문 및 최종 평가 | 이 초안은 제출물 아님. ▲ 제출 불가 — 이 작업에서 최종 제출 후보 미확정 |

## 3. 구체적인 변경 초안 — 확정 후보 아님

**A017 조건의 action_rate_l2 -0.01 → -0.008만 변경**하는 조건부 가설을 파일로 준비했다. 다른 값은 track 1.4, feet .2, lin_z -2, ang_xy -.05, flat 0으로 유지한다. yaw 등 나머지 배포 설정도 유지해야 한다.

- 가설: 동작 변화 벌점이 지형 대응을 과도하게 억제했다면 작은 완화로 전진 반응이 좋아질 수 있다.
- 경쟁 가설: 이미 떨림·미끄러짐이 크다면 완화가 악화시킨다. 현재 CSV에는 action/발 접촉이 없어 구분되지 않는다.
- 값 선정: 벌점 크기 20% 감소의 공학적 탐색 폭이다. 최적값·문헌 검증값이 아니다. 로컬 `quadruped_rewards.py`의 action_rate 설명은 방향의 단서일 뿐 원인 입증이 아니다. 외부 문헌 조회는 앞선 인증 오류로 확보하지 못했다.
- 단순 track 추가 인상은 보류: 1.2→1.4에서 G4/G6 회귀가 이미 관찰됐다. ang_xy -0.06도 원인 근거 없이 재채택하지 않는다.
- reward 상태: track **부분 만족**, action_rate **미측정**, feet/lin_z/ang_xy/flat **INCONCLUSIVE**. 유지 항의 개별 인과효과는 분리 측정되지 않았다.

조건부 실험 설계: from-scratch seed42, 4096env, 1000iter; 재평가 전 자동 연장 없음. 기존 A017와 학습 조건·checkpoint 선택 규칙을 일치시킨다. 개선 시 독립 학습 seed43로 재검증한다. 평가 seed101/202/303 및 동일 evaluator를 양쪽에 적용한다.

제안 판정: G3 전진·G7의 각 paired seed에서 RMSE 5% 이상 감소, 진행거리 비열등; 모든 case 생존 비회귀 및 다른 case tracking proxy 감소 .02 이내. 새로 설정한 내부 탐색 기준이지 공식 기준이 아니다. 자세 계측 모호성이나 필수 영상 누락 시 INCONCLUSIVE이며 후보 승급 금지. 실패하면 이 완화 가설을 철회하고 A017를 보존한다. 계단 완치를 이번 실험의 성공조건으로 두지 않는다.

## 4. 원 학습 report와 학습 길이

- Pilot `workspace/training/quadruped/exported/report.html`: 앞선 본문 직접 열람, READ_UNMATCHED. 2026-08-31, 최고18.02@972, terrain3.94, 마지막10회 학습낙상 진단13.8%. 모델 대응 재검증 미완료.
- A017: **REPORT_READ_STATUS=MISSING / REPORT_REQUIRED_NOT_ACQUIRED**. 기존 52개 archive 검색 기록은 `upload/G-A028/review/REPORT_RECOVERY_SEARCH.json`. 새로 전수검색했다는 뜻이 아니다. 외부 보관 원본을 확보하여 원 로그·env·checkpoint와 대조해야 한다. 로그로 HTML을 꾸며 만들지 않는다.
- 원 로그 `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/logs/candidate_training.log:33222`: reward-best step856에서 model_900.pt 선택. best step856, checkpoint900, 최종iter999를 구별한다. model SHA `0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4`.
- 700~799 / 800~899 / 900~999 구간 평균 reward 17.01 /17.56 /17.12, terrain 2.08 /2.94 /3.85, 학습 base_contact .0686 /.0849 /.0973. 난이도 상승과 교란되므로 수렴이나 장기학습 이득을 단정하지 않는다. 이 값은 시나리오 survival이 아니다.

## 5. 파일·회수 계약 및 미완료 경계

`upload/G-A029/review/GO2_G_A029_ACTION_RATE_M0008_DRAFT_quadruped_rewards.py`는 실제 reward Python 양식의 값 초안이다. 동봉 A017 baseline 파일과 비교하면 action_rate 한 항만 다르다. 현재 로컬 Pilot 파일과 비교하면 track도 다르므로 이를 2변수 신규 실험으로 오인하지 않는다.

공용 runner는 서버 생성 nonempty/fresh 원본 report를 **평가 이전**에 `_keep/<튜닝명칭>/exported/report.html`로 복사하고 ZIP/SHA에 포함한다. missing/empty/stale이면 회수 실패, 재개 시 report SHA 검사. 파일 시각만으로 정책 의미 대응이 입증되지는 않는다.

**실행본 미완료:** report gate 외에도 현재 engine frozen baseline에 A017가 없다. Pilot로 조용히 바꾸거나 JSON 버전만 맞춰 통과시키지 않는다. 영상 case manifest, 동등한 자세 평가, A017 engine 지원을 검증한 뒤에만 current/history/실행 가이드를 발행한다. 원본 report와 승인 release는 변경하지 않았다. 이 보고서나 조건부 파일을 서버 실행 준비 완료로 표현하지 않는다.
