# G-A042 회수 분석 — 2026-09-21

## 판정
- **INTERNAL_GATE_FAIL**: fact_rules FAIL, 계획 screening INTERNAL_GATE_FAIL. artifact_faults=0, stage_faults=0, identity_faults=0. 기준선 A033 유지; 1.6 후보 승급/장기 학습 근거 없음.
- 재현: `python tools/verify_go2_basic_motion_harvest.py G-A042 --harvest workspace/_keep/go2_g_a042_a033_track_lin_vel_xy_160 --out workspace/server_returns/G-A042_LOCAL_VERIFY.json`.
- 원자료는 `workspace/_keep/`에 보존; 기존 정본으로 병합하거나 덮어쓰지 않았다. 분석 JSON은 별도 `server_returns/`에 저장했다.

## 조건과 report
- track_lin_vel_xy_exp는 몸통 xy 명령속도 오차에 지수 보상을 주는 항이다. 발 높이를 직접 보상하지 않는다. A033 1.5 → A042 1.6 하나만 변경, seed42·4096env·1000iter; 평가 iter900 고정.
- A042 model SHA `780fd1e303300607f8a41e129f86f9780221c552f02bc48a0fef181c60cc5e1f`, A033 `ccd60e192bf4ec900a269cc264d7739a4962a4ce07a0c3607568346778646044`.
- REPORT_READ_STATUS=READ_MATCHED (학습 run 대응만). A042 `workspace/_keep/go2_g_a042_a033_track_lin_vel_xy_160/exported/report.html` 본문 직접 읽음: 20:21~21:20, 59분2초, 최고20.34@957, 마지막 terrain4.21·학습 낙상15.2%·std0.579. 원 로그 `logs/candidate_training.log:31763,31772,33236-33238`와 대응.
- HTML 상단 선택 모델999와 평가900은 별개이며 `training/CHECKPOINT_PIN.txt`로 구분. HTML 수치를 평가900의 성능으로 쓰지 않는다.
- 대조 A033 report: 최고19.28@651, terrain4.71, 학습 낙상17.1%, std0.613. 최고 reward 증가/학습 낙상 감소에도 평가가 악화했으므로 이 지표들로 행동 개선을 대체하지 않는다.

## 직접 관측 — 평가 seed101/202/303 × 각32개체 (독립 학습96회 아님)
| 항목 | A033 | A042 |
|---|---:|---:|
| 10cm 계단 ≥1단 | 90/96 | 4/96 |
| 10cm 계단 ≥2단 | 43/96 | 0/96 |
| 10cm 자세 포함 낙상 | 34/96 | 85/96 |
| 15cm 계단 ≥1단 | 4/96 | 0/96 |
| 15cm 계단 ≥2단 | 0/96 | 0/96 |
| 15cm 자세 포함 낙상 | 90/96 | 94/96 |
| 험지 전진 자세 포함 낙상 | 4/96 | 20/96 |
| 험지 좌우 자세 포함 낙상 | 59/96 | 53/96 |

계획 screening의 paired seed 중앙값 차이: 전진 거리10cm −0.846821m, 15cm −0.233925m; 정체 비율10cm +52.757%p, 15cm +22.0214%p. 험지 전진 tracking proxy −0.200309, 좌우 −0.020374. 좌우 생존 개선만으로 추종 악화를 상쇄하여 승급하지 않는다.

## 영상과 범위
- 후보4개 및 A033 15cm 신규1개 회수. 후보4개의 10%/45%/80% 프레임을 직접 관찰(`workspace/server_returns/G-A042_video_samples.jpg`). 계단 표본에서 첫 턱 앞 낮아진 몸통과 진행 부족이 보임: VIDEO_OBSERVED(표본 한정). 연속 동작 전체·96개체 전수 시각 검증 아님.
- G3/G5: 표본 영상 관찰, 내부 정량 있음, 공식 결과 미측정. G1/G2/G4/G6/G7은 일부 보호 측정이며 전수 평가로 승격하지 않는다. 전체69case 평가 미실행으로 자체 /70 재계산 및 공식 점수 주장 없음.

## 해석과 한계
- 확인: 기대했던 계단 진행 증가·정체 감소와 반대이며, 험지 전진도 악화했다. 이번 조건의 1.6 후보는 미만족.
- 추론: A017 1.4→A033 1.5의 개선을 1.6까지 단조 연장할 근거가 사라졌다. 가중치 증가가 재학습 후 더 빠른 정책을 보장하지 않는다.
- 미확정: 직접 실패 기전, 독립 학습 seed 재현, 1.5의 전역 최적성. 보상 항 원 채널의 경쟁 기전은 이 결과만으로 확정하지 않는다.
- 다음 판단: A033 유지. A042를 장기 학습하거나 1.7로 자동 상향하지 않는다. 새 실행 패키지는 이번 분석 요청 범위에서 발행하지 않는다.
