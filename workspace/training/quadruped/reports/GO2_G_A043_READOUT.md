# G-A043 회수 검토 — 2026-09-22

## 결론
- ARTIFACT_VERIFIED / INTERNAL_GATE_FAIL. A033 기준선 유지, A043 승급·장기학습 근거 미충족. 서버 종료 가능, 필수 추가 회수 없음.
- 내부 시뮬 proxy 42.528610 → 44.624542/70 (+2.095932). 사전등록 개선폭 2.53 미달이며 G2 보호 기준도 위반했다. 공식 점수가 아니다.
- 계단 개선은 관측됐지만 부작용 없는 개선은 아니다. 기준을 사후 완화하지 않는다. 학습 seed42 한 회차이므로 exploratory.

## 무결성·회수
- 원자료: `workspace/_keep/go2_g_a043_a033_lin_vel_z_m15/`, 같은 위치의 RESULT ZIP과 campaign ZIP. 기존 정본 덮어쓰기·병합 없음.
- RESULT ZIP SHA256 `9a5e7d2858702c1a766421cf221c8b3233e3b98043c914bb65b345366c68c8c6`.
- ZIP 외부 SHA·CRC·안전 경로·내부 SHA 530항목, 압축 해제본 531파일 불일치 0. campaign ZIP 외부 SHA·CRC·내부 5항목 일치. generic tar 검증기는 ZIP 미지원이어서 ZIP 전용 대조로 검증했다.
- 후보69 case·sentinel5·신규 영상8(후보6/기준선2)·재사용 기준선4 SHA 확인. 원 학습 HTML·로그·env·checkpoint 포함.
- v3 release 실행, RUNNER_RC=0, SUITE_COMPLETE. sentinel5 재측정은 저장 기준선과 동일. 로컬 artifact_faults와 ruler_mismatches 없음.

## 조건·학습 report
- `lin_vel_z_l2`는 몸통 좌표 위아래 속도 제곱의 벌점이다. 올라서기만 선택적으로 보상하는 항이 아니다. A033 -2.0 → A043 -1.5 단일 변경, seed42/4096env/1000iter, 평가900 고정.
- 평가 model SHA `4d9236818f998bdb87efaea4acfa1e4c861b0d87947229e88f9175495066bd6b`.
- 기준선 A033 평가900 SHA `ccd60e192bf4ec900a269cc264d7739a4962a4ce07a0c3607568346778646044`.
- REPORT_READ_STATUS=READ_MATCHED(학습 run 대응). 양쪽 `exported/report.html` 본문 직접 읽음. A043 12:22~13:20/58분19초, 최고20.41@825, 마지막 terrain5.24·학습낙상18.1%·std0.640. `logs/candidate_training.log`의 finalize 출력 및 `training/TRAIN_STATUS.txt`, env, CHECKPOINT_PIN과 대조.
- A043 HTML 모델800은 reward best이고 평가900과 다르다. A033 HTML 모델700, 최고19.28@651·terrain4.71·학습낙상17.1%·std0.613도 평가900의 성능 자체가 아니다.

## 실측 비교
평가 seed101/202/303 × 32개체; 독립 학습96회가 아니다. 낙상은 posture_gate_v2 판정이다.

| 지표 | A033 | A043 |
|---|---:|---:|
| 10cm ≥1단 | 90/96 | 96/96 |
| 10cm ≥2단 | 43/96 | 94/96 |
| 15cm ≥1단 | 4/96 | 88/96 |
| 15cm ≥2단 | 0/96 | 77/96 |
| 10cm 자세 낙상 | 34/96 | 17/96 |
| 15cm 자세 낙상 | 90/96 | 49/96 |
| 험지 옆걸음 자세 낙상 | 59/96 | 24/96 |
| 험지 전진 자세 낙상 | 4/96 | 6/96 |
| 밀침 +x 자세 낙상 | 8/96 | 2/96 |
| 밀침 -x 자세 낙상 | 6/96 | 4/96 |

- 계단 전진거리 seed별 차이 중앙값: 10cm +2.8521m, 15cm +1.8014m. 정체 비율 차이 중앙값 각각 -0.128409/-0.421482.
- G3 +3.18654점, G5 +1.57274점이지만 G2 -4.63693점(/70 가중 proxy) 손실.
- G2 `combined_yaw_right` 생존은 3seed 모두 1.0에서 0.71875/0.71875/0.65625로 하락. 종료 이벤트는 여전히 각0: 종료 횟수만 보면 놓치는 자세 게이트 위반이다. 해당 case 영상은 없으므로 넘어짐 형태를 시각적으로 확정하지 않는다.
- 계획 screening 추가 위반: 험지 전진 낙상 4→6, 밀침 +x/-x tracking proxy 차이 중앙값 -0.004256/-0.007162. 작은 차이를 통계적 악화 확정으로 과장하지 않되 사전등록 비열등 기준은 미충족이다.

## 증거 계층
| 범위 | 영상 | 내부 정량 | 공식 결과 |
|---|---|---|---|
| G1 | VIDEO_UNKNOWN | 69case 평가에 포함 | 미측정 |
| G2 | VIDEO_UNKNOWN | 복합 우회전 자세·추종 악화 | 미측정 |
| G3 | 표본 프레임 직접 관찰; 전 구간 행동 VIDEO_UNKNOWN | 옆걸음 개선, 전진 낙상 보호 미달 | 미측정 |
| G4 | VIDEO_UNKNOWN | 측정 완료 | 미측정 |
| G5 | 표본에서 계단 위 위치 확인; 연속 완주 VIDEO_UNKNOWN | 등반·거리·정체 개선 | 미측정 |
| G6 | 표본 프레임 직접 관찰; 회복 과정 VIDEO_UNKNOWN | 낙상 감소, ±x 추종 보호 미달 | 미측정 |
| G7 | VIDEO_UNKNOWN | 측정 완료 | 미측정 |

신규 후보6개는 각각499frame/50fps. 표본3장씩 확인한 이미지 `workspace/server_returns/G-A043_video_samples.jpg`는 영상 전체 관찰을 대신하지 않는다.

## 해석·다음 판독
- 사실: 이번 조건에서 -1.5는 계단·험지 옆걸음에 개선을 보였으나 G2 보호 손실이 크다. 보상 산수의 사전 예측과 실제 학습 행동은 구별한다.
- 추론: 계단 이득을 보존하면서 복합 회전 손실을 줄이는 조건 탐색이 다음 문제다. 이번 한 점만으로 최적값이나 다음 수치를 확정하지 않는다.
- 다음 읽기 전용 분석은 `combined_yaw_right`의 자세·추종 telemetry를 반대 방향과 대조해 손실 유형을 분해하는 것이다. 이번 검토에서 새 패키지·서버 실행은 하지 않았다.

## 재현·검증
- `python -B tools/verify_go2_basic_motion_harvest.py G-A043 --harvest workspace/_keep/go2_g_a043_a033_lin_vel_z_m15 --out workspace/server_returns/G-A043_LOCAL_VERIFY.json`
- `python -B tools/go2_screening_gate.py --candidate workspace/_keep/go2_g_a043_a033_lin_vel_z_m15 --rule-version post_a042_push_v1 --out workspace/server_returns/G-A043_SCREENING.json`
- 두 명령 exit1은 검사기 실행 오류가 아니라 성능 기준 미충족 결과다. 양쪽 screening 실패3항 동일. 구현 수정·계약 테스트 재실행은 하지 않았다.
