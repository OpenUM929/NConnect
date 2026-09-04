# Run06 높은 자체점수 신뢰성 감사

## 결론

Run06은 학습을 하지 않은 정책이 아니다. Run05와 같은 reward·seed 설정을 사용해 처음부터
10,000 iteration을 학습했고, Run05의 3,000 iteration 이후 구간을 추가로 확보했다. 그러나
66.04/70은 같은 seed와 유사 분포에서 계산한 **교정 점수**였다. 이후 정책·proxy·threshold를
동결하고 seed 101·202·303에서 독립 반복하여 30개 case 전부 통과했고, 최악 seed 기준
65.73/70을 얻었다. 따라서 평가 seed 변화에 대한 신뢰도는 보강됐지만 공식 점수는 아니다.

## 실제로 학습한 것

- Run05: 동일 reward 설정으로 3,000 iterations
- Run06: 동일 reward 설정을 처음부터 10,000 iterations
- Run05 대비 Run06 마지막 구간:
  - `error_vel_xy`: 9.71% 개선
  - `error_vel_yaw`: 16.61% 개선
  - `mean_episode_length`: 7.25% 증가
  - `base_contact`: 14.76% 감소
  - `mean_std`: 4.39% 감소

이는 **학습시간 연장 효과가 관측됐다**는 뜻이지 reward 최적화나 예선 성능 확정을 뜻하지 않는다.

## 높은 점수가 나온 직접 원인

1. 10개 case 모두 32/32 environment가 20초 timeout까지 생존해 survival proxy가 1.0이었다.
2. 관측 RMSE가 약 0.06~0.19였고 내부식 `exp(-(RMSE/0.5)^2)`은 이 구간을 약 0.87~0.99로 변환한다.
3. H7은 관측된 114회가 모두 회복했지만 예상 128회 중 미관측 14회를 실패로 처리해 0.890625가 됐다.
4. 가중합 결과가 0.9434489이므로 66.0414/70이 됐다.

따라서 계산 오류로 높아진 것은 아니지만, **내부 변환식이 공식 evaluator보다 쉽거나 다를 수 있다.**

## 독립 검증 결과

- 사전등록 seed: 101, 202, 303
- 범위: seed별 H1~H7 10 case, 32 environments, 1,000 step
- 누락/실패: 0/0
- 시나리오별 최악 survival: 전부 1.0
- 시나리오별 최악 proxy: H1 0.9269, H2 0.9630, H3 0.9810, H4 0.9062,
  H5 0.9584, H6 0.9735, H7 0.8594
- 내부 simulation proxy: 65.73/70
- 판정: `INDEPENDENT_VALIDATION_PASS`

## 신뢰도를 제한하는 요인

- 정책 학습은 seed 42 한 번이므로 training-seed 분산은 아직 측정하지 않았다.
- threshold는 seed 42의 부분 telemetry를 본 뒤 고정했지만 독립 seed 실행 전에는 동결했다.
- 평가 명령이 학습 command 범위 안에 있다.
- 공식 tracking 변환식과 정확한 H1~H7 가중치는 확인되지 않았다.
- H4 yaw·H6 경사·H7 push는 기존 영상만으로 사건을 명확히 식별하지 못했다.
- checkpoint 하나와 seed 하나는 분산과 일반화를 보여주지 않는다.

## 교정 조치와 현재 상태

- 정책·계산식·threshold 동결 후 seed 101·202·303 반복을 완료했다.
- 각 시나리오의 최악 seed로 판정했고 세 seed가 모두 통과했다.
- 현재 상태는 `ARTIFACT_VERIFIED / INDEPENDENT_VALIDATION_PASS / OFFICIAL_RESULT_UNMEASURED`다.
- 추가 reward tuning보다 제출 3종의 대시보드 업로드와 제출 증거 회수를 우선한다.

## 외부 기술 근거

- Isaac Lab `RewardManager`는 여러 reward 항의 가중합을 계산한다. 따라서 reward weight의
  비율을 대회 점수 가중치로 직접 해석할 수 없다.
  <https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.managers.html>
- PPO는 환경 상호작용 표본으로 surrogate objective를 최적화한다. iteration 수 증가만으로
  미관측 조건의 행동 성능이 보장되지는 않는다.
  <https://arxiv.org/abs/1707.06347>
- Deep RL은 비결정성과 분산 때문에 단일 실행의 개선을 해석하기 어렵고, 표준화된 반복과
  재현성 보고가 필요하다는 실증 연구가 있다.
  <https://arxiv.org/abs/1709.06560>
