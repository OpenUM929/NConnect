# G-A029 난이도 기반 튜닝 준비

상태: REVIEW_ONLY / HOLD — 실행용 튜닝 파일 아님.
작업: G-A029, 2026-09-14. 기존 승인 ZIP 및 배포 학습 코드는 보존한다.

## 목적과 결정
낙상 완치를 모든 개선의 선행조건으로 두지 않는다. 기대 가중 이득,
실험 비용, 원인 확실성을 함께 비교한다. 이는 사용자 요청에 따른 검토 정책이며
G3 우선 학습이나 특정 reward 값의 효과를 확정한 것이 아니다.

| 등급 | 범위 | 처리 |
|---|---|---|
| 조사 | A017 report·checkpoint·env·로그 대응 | 원 학습 HTML 미확보. READ_MATCHED 전 새 후보 확정 금지 |
| 개선 | G1/G2 | 기존 내부 결과를 회귀 감시로 재사용. 추가 이득이 작을 수 있음 |
| 조사 | G3 rough_lateral | 좁은 실패 조건의 저비용 후보 검토. 실제 전도·정체·추종 오차 구분 필요 |
| 조사 | G4/G5 | 경사 안전 회귀, 계단 정체와 높이 판정 의미를 분리. 낙상 원인 단정 금지 |
| 조사 | G6/G7 | 기준과의 거리만으로 튜닝이 쉽다고 판정하지 않음 |
| 필수(제출요건) | 최종 G1~G7·정책/env/제출문 | ▲ 제출 불가 — 이 검토 작업은 제출 후보를 생성하지 않음 |

## 실행 spec에 동결할 항목
기존 config/experiments JSON 구조를 참고하되, 미확정 자료는 실행 schema에
가짜 값으로 채우지 않는다. review JSON은 의도적으로 실행 schema와 다르다.

- baseline: A017의 정확한 checkpoint iter/model SHA/env SHA와 원 학습 report 대응.
- single_change: 근거 있는 한 항의 전→후 값. 현재 null이며 -0.06을 재사용하지 않는다.
- training: 짧은 1,000~5,000 iter 범위에서 판별력 있는 예산을 사전등록.
  기존 seed42/4096env는 참고 조건이지 이번 실행 확정값이 아니다.
- evaluation: 목표 case와 G1~G7 회귀 감시를 고정. 6~8case 조기평가 →
  21case 대표평가 → 전체평가 원칙. 측정 결함은 INCONCLUSIVE, 부분 평가로 /70 생성 금지.
- branch: primary 개선, survival/tracking 비열등, 정지 편법 및 영상 기준을
  실행 전에 수치로 동결. 장기 승급 전 독립 학습 seed 검증. 자동 장기학습 없음.
- video: reward/정책 변경 시 필수. case/seed/env수/길이/수량/동일 rollout 대응 동결.
- output: _keep/<튜닝명칭>/exported/report.html 원본, model/env/policy,
  학습로그/tfevents/source, 영상/telemetry, 종료상태, 내부 SHA 및 결과 ZIP/SHA.

## report 회수 계약
공용 server_run_go2_tuning_engine_v1.sh는 학습 시작 marker 이후의 nonempty
report.html만 평가 재생 전에 보존한다. missing/empty/stale은
REPORT_REQUIRED_NOT_ACQUIRED 및 실패 반환, 기존 증거는 PARTIAL 포장 경로로 보존한다.
재개 시 보존 report SHA를 재검사한다. mtime·SHA만으로 report와 정책의 의미적 대응을
입증하지 않으므로 회수 후 본문/iter/reward/log/model 대응을 별도로 확인한다.

## 전달 형식과 제한
upload/G-A029/review/GO2_G_A029_TUNING_REVIEW.zip 및 SHA는 검토 자료다.
current/, 서버 실행 명령, 예상 서버 시간, 완료 표식은 발행하지 않는다.
실행본은 근거 및 engine identity 문제 해결 후 기존 publisher의
current/history/CURRENT_UPLOAD/UPLOAD_HISTORY/manifest 양식으로 별도 발행한다.
REPORT_READ_STATUS: Pilot READ_UNMATCHED(앞선 직접 본문 열람), A017 MISSING(원장상).
이번 검토는 성능 실측이 아니며 학습 코드/가중치 변경을 포함하지 않는다.

### G-A029 ? 2026-09-14 ?? ?? ?? ? ?? ??? ??
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 같은 주제의 확인한 정상 기록: `workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md`, `workspace/training/quadruped/upload/G-A029/review/GO2_G_A029_ACTION_RATE_M0008_DRAFT.json`. 손상 줄의 "35 unittest" 검증 결과는 대체 기록 미확보(`review/GO2_G_A029_TEST_OUTPUT.txt`는 32 tests로 다른 회차다).
- ??? ??: ?? ?? ??? ???? ???? ????? ?? ?? ?? ??. ?????? ?? ??? ?? ???.
- ?? ???: workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md. G3/G7 ?? ??? ?? ???? G1/G2 ???G4/G6 ?? ??, G5 ??? ?? ????. ?? ??? ?? ??? ?????? ?? ???.
- A017 ??? ??: action_rate_l2 -0.01?-0.008(20% ?? ???, ??/??? ???). ?? Python reward ?? ??? baseline ??, ??? JSON? upload/G-A029/review? ??. ?? ??? ?? ??? ??.
- REPORT_READ_STATUS: A017 MISSING, Pilot READ_UNMATCHED ??. ?? ??: ?? engine? A017 frozen baseline ???, ?? manifest ? ?? ?? ?? ???. ?? ?? ??/current/history ?? ??.
- ?? ??: 35 unittest ??(?????Python ??/LF??????report fresh/missing/empty/stale?ZIP/SHA?shell ???engine ??). ?? ??/?? ?? ???. ?? lifecycle PLANNED, ?? ?? ??.
