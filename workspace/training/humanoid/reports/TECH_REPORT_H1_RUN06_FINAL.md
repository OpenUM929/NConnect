# H1 기술 개선 리포트 — Run06 제출 후보

## 1. 후보 식별

- 학습 run: `train_260831-06_run05cfg_10000`
- 선택 checkpoint: `model_9900.pt` (`iter=9900`)
- checkpoint SHA-256: `8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636`
- 학습 조건: from scratch, seed 42, 4,096 environments, 10,000 iterations
- 제출 정책: `policy.pt`
- 제출 환경: `env.yaml`

`policy.pt`의 actor tensor 8개를 checkpoint actor tensor와 대조해 8/8 동일함을 확인했다.
직렬화 파일 해시는 달라질 수 있으므로 정책 동일성은 tensor 대조로 판정했다.

## 2. 개선 목표와 점수 해석

목표는 낙상 억제와 속도 명령 추종을 함께 개선하는 것이다. 공개 가이드는 시나리오 점수를
`survival_rate × tracking_score` 구조로 설명하지만 정확한 tracking 변환과 evaluator 구현은
공개하지 않는다. 이 문서의 `base_contact`, RMSE, recovery time과 simulation proxy는 모두
내부 근거이며 공식 점수가 아니다.

## 3. 변경 과정

| 비교 | 단일 변경 | 결과 | 결정 |
|---|---|---|---|
| Run01→02 | `termination_penalty -5→-50` | base contact 크게 감소, timeout 증가 | 생존 proxy 개선으로 채택 |
| Run02→03 | `termination_penalty -50→-90` | 생존 이득은 작고 xy·yaw 오차 악화 | -50 복원 |
| Run02→04 | `track_ang_vel_z_exp 0.5→1.0` | yaw 오차 감소 | 회전 추종 보완으로 채택 |
| Run04→05 | `track_lin_vel_xy_exp 0.5→1.0` | xy 개선, yaw 악화의 교환관계 관측 | 두 축 1.0 유지 |
| Run05→06 | reward 변경 없이 3,000→10,000 iter | xy 9.71%, yaw 16.61% 개선; episode length 7.25% 증가; base contact 14.76%, std 4.39% 감소 | 장기학습 후보 채택 |

Run06은 새로운 reward 실험이 아니라 Run05 설정의 학습시간 연장 실험이다. 따라서 Run06의
개선은 추가 최적화 구간에서 관측된 것이며 특정 reward 항의 인과효과로 주장하지 않는다.

## 4. 제출 `env.yaml` 주요 reward

| reward | weight |
|---|---:|
| `track_lin_vel_xy_exp` | 1.0 |
| `track_ang_vel_z_exp` | 1.0 |
| `feet_air_time` | 0.2 |
| `termination_penalty` | -50.0 |
| `flat_orientation_l2` | -1.5 |
| `ang_vel_xy_l2` | -0.05 |
| `joint_deviation_hip` | -0.2 |
| `joint_deviation_torso` | -0.1 |
| `action_rate_l2` | -0.0005 |

`feet_air_time`과 `flat_orientation_l2`는 후보였지만 Run06에서는 변경하지 않았다.

## 5. 고정 정책 H1~H7 계측

Run06 model_9900을 변경하지 않고 seed 42, 32 environments, 시나리오당 1,000 step으로
측정했다. 10개 case 모두 32/32가 20초 timeout까지 생존했고 조기 종료는 없었다.

| 시나리오 | survival | tracking proxy | scenario proxy | 내부 판정 |
|---|---:|---:|---:|---|
| H1 제자리 | 1.0000 | 0.9268 | 0.9268 | calibration gate 통과 |
| H2 전진 | 1.0000 | 0.9631 | 0.9631 | calibration gate 통과 |
| H3 좌·우 | 1.0000 | 0.9812 | 0.9812 | calibration gate 통과 |
| H4 복합 이동·회전 | 1.0000 | 0.9051 | 0.9051 | calibration gate 통과 |
| H5 요철 | 1.0000 | 0.9568 | 0.9568 | calibration gate 통과 |
| H6 ±10° 근사 | 1.0000 | 0.9738 | 0.9738 | calibration gate 통과 |
| H7 밀침 | 1.0000 | 0.8906 | 0.8906 | calibration gate 통과 |

가중 simulation proxy는 0.9434489, 환산값은 66.0414/70이다. H7은 예상 push 128회 중
114회만 disturbance로 검출됐으므로, 관측 114/114 회복 대신 보수적으로 114/128을 사용했다.

## 6. 영상과 계측의 증거 수준

- H1·H2·H3·H5: 기존 Run06 영상에서 요구 행동과 무낙상을 직접 관찰했다.
- H4: 영상에서는 yaw를 분리하기 어렵지만 좌·우 계측에서 32/32 생존과 추종 오차를 확보했다.
- H6: 영상에서는 경사각이 명확하지 않지만 ±10° 근사 지형 계측에서 각각 32/32 생존했다.
- H7: 영상에서는 push 사건이 보이지 않지만 telemetry에서 예상 128회, 검출 114회,
  회복 114회, 중앙값 0.18초, 최대 0.88초를 기록했다.

영상 판독 한계를 telemetry로 보완했지만 어느 것도 운영진 공식 결과로 승격하지 않는다.

## 7. 높은 자체점수의 한계와 독립 검증

66.04/70은 계산 오류가 아니지만 다음 편향이 있다.

1. 학습과 교정 평가가 모두 seed 42다.
2. 평가 명령·지형은 학습 분포 안에 있다.
3. proxy 식 `exp(-(RMSE/0.5)^2)`과 threshold는 내부 정의다.
4. threshold는 부분 H4·H6·H7 telemetry를 본 뒤 고정돼 seed 42와 독립적이지 않다.
5. checkpoint 하나와 seed 하나는 일반화를 입증하지 않는다.

이 한계를 줄이기 위해 정책·proxy·threshold를 고정한 뒤, 사전등록 seed 101·202·303에서
각각 H1~H7 10개 case를 독립 반복했다. 총 30개 case가 모두 정상 종료했고 누락 seed와
실패 seed는 없었다. 시나리오별 세 seed 중 최악값은 다음과 같다.

| 시나리오 | 최악 survival | 최악 tracking | 최악 proxy | 내부 판정 |
|---|---:|---:|---:|---|
| H1 | 1.0000 | 0.9269 | 0.9269 | `INDEPENDENT_SCENARIO_PASS` |
| H2 | 1.0000 | 0.9630 | 0.9630 | `INDEPENDENT_SCENARIO_PASS` |
| H3 | 1.0000 | 0.9810 | 0.9810 | `INDEPENDENT_SCENARIO_PASS` |
| H4 | 1.0000 | 0.9062 | 0.9062 | `INDEPENDENT_SCENARIO_PASS` |
| H5 | 1.0000 | 0.9584 | 0.9584 | `INDEPENDENT_SCENARIO_PASS` |
| H6 | 1.0000 | 0.9735 | 0.9735 | `INDEPENDENT_SCENARIO_PASS` |
| H7 | 1.0000 | 0.8594 | 0.8594 | `INDEPENDENT_SCENARIO_PASS` |

최악 seed 기준 내부 simulation proxy는 0.9390, 환산값은 65.73/70이다. 따라서 현재 내부
상태는 `INDEPENDENT_VALIDATION_PASS`다. 이는 평가 seed 변화에 대한 안정성을 보강하지만,
서로 다른 seed로 정책 자체를 다시 학습한 training-seed 일반화나 운영진 공식 점수를
입증하지는 않는다.

## 8. 결론

Run06은 현재까지 확보한 후보 중 학습 곡선, checkpoint, 정책 tensor, H1~H7 영상, 고정 계측과
사전등록 독립 3-seed 평가가 가장 잘 연결된 제출 후보다. 제출 파일 정합성은
`ARTIFACT_VERIFIED`, 내부 성능 판정은 `INDEPENDENT_VALIDATION_PASS`다. 다만 내부 proxy와
근사 시나리오의 결과이므로 이를 운영진 공식 점수나 예선 합격으로 표현하지 않는다.
