# H1 보상·실험 근거 마스터

> **역할:** H1 튜닝값, 실험 상태, 과학적 근거, 다음 판정 기준의 단일 진입점이다.  
> **정본 우선순위:** 실제 run artifact·로그·YAML → 이 문서 → `experiment_history.csv` → 개별 보고서 → 과거 계획.  
> **artifact 운영 정본:** 파일 목록·서버 회수·검증·선택 병합·작업 내역은 `ARTIFACT_MANAGEMENT.md`를 따른다.  
> **갱신일:** 2026-08-31

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 70점 후보의 H1~H7 실제 행동과 설계 의도 20점·리포트 10점의 영상 증거를 확보한다.
- [현재 단계] **단계 5/6 — 최종 평가·문서.** 증거 계층 정정과 다음 실험의 승인 조건을 확정한다.
- [확보] Run06 10,000 iter·model_9900·학습/영상 artifact 정합, 내부 학습 게이트 5/5 통과, H4·H6·H7 고정 telemetry 회수, H1·H2·H3·H5 요구 행동 영상 관찰.
- [미확보] 운영진 evaluator 점수, 예선 통과 결과, H1~H3·H5 격리 정량값, 독립 seed. H4·H6·H7은 영상만으로 조건 식별이 불가능하다.
- [이번 테스트] 새 학습 없이 Run06의 `artifact/영상/내부 정량/공식 결과`를 분리하고 후속 screening 순서를 사전등록한다.
- [흐름] Run06 학습·영상·고정 telemetry 완료 → **증거 재분류·문서 정합** → 첫 공식 평가 또는 단기 screening → 승자만 장기 학습 → 최종 제출.
- [지금 할 일] 없음. 서버를 켜지 않고 로컬 보고서와 실험 설계를 먼저 확정한다.
- [보장하지 않음] 영상 1세트나 단일 seed만으로 공식 survival_rate, 최적 reward, 예선 점수 또는 통과 가능성을 보장하지 않는다.

### Run06 현재 운영 결정 (260831)

- 사용자 최신 관측에서 약 30분만 남았으므로 5k 중단안은 철회했다.
- `SIGINT`/tmux 종료 없이 10,000 iter 자연 완료를 우선한다. 이는 결과 성능 보장이 아니라 완료 bundle 생성 실패 위험을 줄이는 운영 결정이다.
- `.saved_5000`은 중간 milestone으로 보존하되 최종 판정은 10k 결과와 함께 수행한다.
- 서버의 `/workspace/training` 전체 다운로드는 허용하지만, `/workspace/_keep/..._DOWNLOAD.tar.gz`가 그 폴더 밖에 있으므로 먼저 별도 회수하거나 `training/_server_returns/`로 복사해야 한다.
- 내려받은 전체 폴더는 로컬 정본에 즉시 덮어쓰지 않고 `workspace/server_returns/<RUN_ID>/training_snapshot/`에 격리한 뒤 검증·선택 병합한다.

## 1. 판정 어휘

| 판정 | 의미 |
|---|---|
| **만족** | 사전 기준, 비교 조건, 부작용 게이트, 반복/평가 근거가 모두 충족됨 |
| **부분 만족** | 학습 proxy 또는 영상은 개선됐지만 공식 평가·반복·부작용 중 일부가 부족함 |
| **미만족** | 사전 기준 또는 핵심 비열등성 게이트를 위반함 |
| **미측정** | 해당 값의 효과를 분리할 로그·대조군·평가가 없음 |
| **INCONCLUSIVE** | 개선과 악화가 교환되거나 통계·사전 기준이 없어 방향을 확정할 수 없음 |

`기본값`, `권장 범위`, `상류 H1 값`은 후보의 출발 근거이지 우리 대회의 만족 판정이 아니다.
문서의 bare `PASS`는 사용하지 않는다. `ARTIFACT_VERIFIED`, `VIDEO_OBSERVED`,
`INTERNAL_GATE_PASS`, `OFFICIAL_RESULT` 중 증거 계층을 붙인다.

## 2. 현재 reward 9개 판정

| reward | 현재값 | Run05까지의 결과 | 현재 판정 | 판단 근거와 한계 |
|---|---:|---|---|---|
| `track_lin_vel_xy_exp` | 1.0 | Run04→05 마지막 500 iter 정규화 xy 오차 약 **19.7~21.2% 개선** | **부분 만족** | 직진 proxy는 개선됐지만 yaw 약 **47.9~50.6% 악화**, `mean_std` 17.5% 악화. Run05는 사전등록이 없어 최종 채택 불가 (`experiment_history.csv`, Run05 행). |
| `track_ang_vel_z_exp` | 1.0 | Run02→04 yaw 오차 0.9341→0.6230, **33.31% 개선**. Run05에서는 마지막 500 정규화 yaw 0.6303으로 statue 0.6681의 0.94배 수준 | **부분 만족·위험** | Run04 학습지표 게이트는 통과했지만 단일 seed, 영상 게이트 미측정. Run05의 선속도 강화 후 회전 proxy가 경계로 후퇴함. |
| `termination_penalty` | -50.0 | -5→-50에서 `base_contact` 0.9244→0.2979; -50→-90은 0.2785로 소폭 개선했지만 xy/yaw/std 악화 | **학습 proxy 만족 / 공식 생존 미측정** | -90은 FAIL이므로 -50은 실용 기준선. 단 `base_contact`는 혼합 학습지형 termination 비율이지 공식 `survival_rate`가 아니다. |
| `feet_air_time` | 0.2 | Run05 마지막 500 reward 0.0062 | **미측정** | 한발지지·명령 게이트가 포함돼 reward 크기만으로 발 높이/등반성을 분리할 수 없다. 0.75는 코드의 의도적 reward-hacking 체험값이지 채택 후보가 아니다. |
| `flat_orientation_l2` | -1.5 | H1/H4/H7 및 H5/H6 근사 영상에서 직립 관찰 | **부분 만족(시각 proxy)** | 단독 대조, torso 자세각, 시나리오 survival이 없어 직립을 이 항의 효과로 귀속할 수 없다. |
| `ang_vel_xy_l2` | -0.05 | 값과 범위만 확인 | **미측정** | roll/pitch 각속도 분포·단독 대조·수용 기준 없음. |
| `joint_deviation_hip` | -0.2 | 값과 범위만 확인 | **미측정** | 골반 대칭·절뚝임 정량치와 단독 대조 없음. |
| `joint_deviation_torso` | -0.1 | 값과 범위만 확인 | **미측정** | torso twist 정량치와 단독 대조 없음. |
| `action_rate_l2` | -0.0005 | 값과 범위만 확인 | **미측정** | action jerk/떨림 지표와 단독 대조 없음. |

### 결론

- **확정 만족 reward: 0개.** 현재 데이터는 최적값을 확정할 수준이 아니다.
- **작업 기준선:** `termination_penalty=-50`, `track_ang_vel_z_exp=1.0`.
- **탐색 후보:** `track_lin_vel_xy_exp=1.0`; 직진 개선과 회전/탐색 잡음 악화의 Pareto 후보다.
- **미탐색:** 나머지 6개. 실패했다고 단정하지 않으며, 효과가 확인됐다고도 말하지 않는다.

## 3. Run별 과학적 지위

| Run | 단일 변경 | 직접 결과 | 지위 |
|---|---|---|---|
| 01 | baseline | 조기 낙상, `base_contact=0.9244` | 기준선 FAIL |
| 02 | termination -5→-50 | 생존 proxy 큰 폭 개선, 추종·std 악화 | PARTIAL |
| 03 | termination -50→-90 | 생존 proxy 소폭 개선, 두 추종 오차·std·영상 회전 악화 | FAIL; -50 유지 |
| 04 | angular 0.5→1.0 | yaw 33.31% 개선, 당시 부작용 게이트 통과 | `INTERNAL_GATE_PASS`, 최종 채택 미확정 |
| 05 | linear 0.5→1.0 | xy 개선, yaw·std 악화 | INCONCLUSIVE; 사후 기준 |
| 06 | iteration 3k→10k | 마지막 500 기준 xy 오차 9.71%, yaw 오차 16.61%, base_contact 14.76%, std 4.39% 개선; episode length 7.25% 증가; `W=+7.487` | **`INTERNAL_GATE_PASS` 5/5; 고정 evaluator 후보. 단일-seed 한계 유지** |

Run06은 reward 튜닝도, 독립 seed 반복도 아니다. Run05와 Run06의 처음 3000 iter는 성능/시간 태그를 제외한 TensorBoard 31개 태그가 bit-identical했다. 따라서 같은 seed·설정의 학습시간 확장 근거로는 강하지만 일반화·최적 reward의 근거는 아니다.

### Run06 최종 판정 (260831)

| 지표 | Run05 마지막 500 | Run06 마지막 500 | 판정 |
|---|---:|---:|---|
| `error_vel_xy / step` | 0.2219138 | 0.2003666 | 9.7097% 개선 |
| `error_vel_yaw / step` | 0.6302623 | 0.5255630 | 16.6120% 개선 |
| `mean_episode_length` | 762.6120 | 817.9275 | 7.25% 증가 |
| `base_contact` | 0.3019631 | 0.2573795 | 14.76% 감소 |
| `mean_std` | 1.6640916 | 1.5910067 | 4.39% 감소 |

사전등록 `W≥5`, episode length, base_contact, mean_std, xy 상한을 모두 통과했다. 이는
`INTERNAL_GATE_PASS`이며 공식 H1~H7 판정이 아니다. 이 결과는
`model_9900.pt`를 **고정 evaluator 후보로 승급**시키며 reward 변경 실험은 일단 동결한다.
H4 yaw·H6 경사·H7 밀침 회복의 시나리오 정량 결과 전에는 최종 제출 후보로 승급하지 않는다.

## 4. Run06 완료·회수 규칙

### 팀장 판정

**중단하지 않고 10,000 iter를 자연 완료한다.** 사용자 최신 관측에서 약 30분만 남았으므로, SIGINT 중단보다 정상 종료와 자동 bundle 생성을 우선한다.

- `.saved_5000`은 중간 비교 milestone이며 중단 신호가 아니다.
- NaN, crash, 설정 불일치 또는 서버 강제 종료 임박이 새로 확인되지 않는 한 Ctrl-C·SIGINT·`tmux kill-session`을 실행하지 않는다.
- `[DONE] DOWNLOAD=...`와 tar SHA-256을 보기 전에 tmux나 서버를 닫지 않는다.
- 10k 결과가 좋아도 최종 승급이 아니다. 동일 evaluator와 독립 seed 검증이 뒤따라야 한다.

```bash
cd /workspace/training/humanoid
KEEP=/workspace/_keep/train_260831-06_run05cfg_10000

while ! grep -q '\[DONE\] DOWNLOAD=' "$KEEP/launcher.log" 2>/dev/null; do
  echo "=== $(date -Is) ==="
  tail -n 12 "$KEEP/train.log" 2>/dev/null || true
  sleep 30
done

echo '=== COMPLETED ==='
grep '\[DONE\] DOWNLOAD=' "$KEEP/launcher.log"
cat "$KEEP/STATUS.txt"
cat "$KEEP/DOWNLOAD_SHA256.txt"
ls -lh /workspace/_keep/train_260831-06_run05cfg_10000_DOWNLOAD.tar.gz
```

`RUN_ID`를 바꿔 실행했다면 `KEEP`만 실제 경로로 바꾼다. `[DONE]` 이전 Ctrl-C, `tmux kill-session`, 서버 종료는 bundle 생성을 끊을 수 있으므로 금지한다.

## 5. Run06 회수 후 판정

동일한 마지막 500 iter window에서 `/step` 정규화 값을 계산한다.

- 추종 proxy: `W = 0.60 × Δxy% + 0.10 × Δyaw%`
- 비열등성: `mean_episode_length ≥ 762.61`, `base_contact ≤ 0.3200`, `mean_std ≤ 1.7500`
- `W ≤ 0`이면서 비열등성 위반이 지속되면 현재 장기화 가설 **미만족**.
- `0 < W < 5`는 **INCONCLUSIVE**.
- `W ≥ 5`와 비열등성 통과는 `INTERNAL_GATE_PASS` 조건일 뿐 `OFFICIAL_RESULT`가 아니다.

공식 가이드 `PRELIM_RL_GUIDE.md:95-100`은 시나리오 점수를
`survival_rate × tracking_score`로 설명한다. 다만 `W`와 `base_contact`는 자체 학습 로그의
내부 proxy이며 운영진 evaluator의 공식 survival/tracking 입력값과 동일하다고 확인되지 않았다.

## 6. H1~H7 측정 연결

| 항목 | Run06 학습 로그가 직접 측정 | 측정하지 않는 것 |
|---|---|---|
| H1 제자리 | episode/base-contact proxy 일부 | 고정 zero-command survival |
| H2 전진 | 혼합 명령의 xy 오차 | H2 격리 tracking·survival |
| H3 좌우 | 혼합 명령의 xy 오차 | 좌/우 각각의 격리 점수 |
| H4 회전복합 | 혼합 명령의 yaw·xy 오차 | 대회 명령 조합의 공식 점수 |
| H5 요철 | curriculum 집계 일부 | 2~10cm 전 구간 survival |
| H6 경사 | curriculum 집계 일부 | +10°/-10° 분리 survival |
| H7 밀침 | 직접 측정 안 함 | 반복 push recovery survival |

### Run06 증거 계층 행렬

| 시나리오 | 영상 판독 | 내부 정량 | 공식 결과 |
|---|---|---|---|
| H1 제자리 | `VIDEO_OBSERVED` — 약 20초 직립; drift 미측정 | 격리 정량 없음 | `[미측정]` |
| H2 전진 | `VIDEO_OBSERVED` — 지속 전진·직립 | 격리 속도 오차 없음 | `[미측정]` |
| H3 좌·우 | `VIDEO_OBSERVED` — 양방향 이동·직립; 좌표 정밀 대응 미확정 | 격리 좌·우 오차 없음 | `[미측정]` |
| H4 회전복합 | `VIDEO_UNKNOWN` — 카메라로 yaw 분리 불가 | actual wz `+0.4646/-0.4856`, yaw MAE `0.1241/0.1263`, 조기 종료 0; threshold 없음 | `[미측정]` |
| H5 약한 요철 | `VIDEO_OBSERVED` — rough 보행·직립; 공식 난이도 미확정 | 격리 정량 없음 | `[미측정]` |
| H6 경사 | `VIDEO_UNKNOWN` — 경사각 식별 불가 | 내부 ±10° 근사 양방향 32/32 timeout, xy MAE `0.0643/0.0638`; 공식 조건 동일성 미확정 | `[미측정]` |
| H7 밀침 | `VIDEO_UNKNOWN` — 외력 순간·크기 식별 불가 | 내부 proxy 114/114 회복, 중앙값 `0.18s`, 최대 `0.88s`, 조기 종료 0; threshold 없음 | `[미측정]` |

이 표에서 `VIDEO_OBSERVED`는 행동이 보였다는 뜻이고 성능 판정이 아니다. 내부 정량의 긍정적
수치도 운영진 evaluator와 threshold가 없으므로 `OFFICIAL_RESULT`로 승격하지 않는다.

**260831 정정 판정:** Run06의 현 성능 상태는 `SELF_ASSESSMENT_INCOMPLETE`다. H4는 20초
완주 생존율이 없고 H1·H2·H3·H5는 격리 telemetry가 없으므로, 기존의 부분적 긍정 판정을
H1~H7 자체 PASS나 70점 추정에 사용하지 않는다. 전체 evaluator 결과 전 현재 자체 점수는
`산출 불가`이며, 누락 시나리오를 0점으로 보수 처리하면 제출 승급 게이트는 FAIL이다.

내부 proxy v1을 기존 부분 telemetry에 진단용으로만 적용하면 H4 tracking `0.9041`(survival 누락),
H6 scenario `0.9738`, H7 scenario `0.8906`이다. H7은 114/114 관측분만 보지 않고 미관측 push까지
포함한 `114/128`을 회복 하한으로 사용했다. 이 threshold는 기존 부분 자료를 본 뒤 정한
**post-hoc calibration**이므로 H4·H6·H7 독립 검증이라고 부르지 않는다. 앞으로의 전체 평가와
모든 후보 비교에는 식과 threshold를 고정해 사후 변경하지 않는다.

## 7. 과학·기술 근거

1. Henderson et al., *Deep Reinforcement Learning that Matters* — 비결정성과 분산 때문에 표준화된 보고와 유의성 검토 없이 단일 run 개선을 일반화하기 어렵다. https://arxiv.org/abs/1709.06560
2. Colas et al., *How Many Random Seeds?* — seed 수는 통계 오류와 직접 연결되며, 비교에는 반복과 통계적 검정 설계가 필요하다. https://arxiv.org/abs/1806.08295
3. Isaac Lab H1 upstream — H1 예제는 lin=1.0, ang=1.0, flat orientation=-1.0을 사용한다. 이는 **합리적 screening 점**의 근거이지 NCRC 최적값의 증거가 아니다. https://github.com/isaac-sim/IsaacLab/blob/release/3.0.0-beta2/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/h1/rough_env_cfg.py
4. Isaac Lab MDP API — linear/yaw tracking은 exponential tracking reward, termination은 non-timeout termination, orientation/action terms는 L2 penalty로 정의된다. 의미를 지지할 뿐 weight 최적값은 제공하지 않는다. https://isaac-sim.github.io/IsaacLab/v3.0.0-beta2/source/api/lab/isaaclab.envs.mdp.html

## 8. 앞으로 모든 튜닝 제안에 반드시 붙일 항목

1. 현재 단계와 막는 가장 이른 미완료 게이트
2. 변경할 단일 변수와 유지할 통제 변수
3. 로컬 사실 근거 `파일:줄` 또는 run artifact
4. 외부 공식문서/논문 근거와 적용 한계
5. H1~H7 중 직접 측정/미측정 항목
6. 사전 가설, 성공·실패·INCONCLUSIVE 기준
7. seed 계획과 evaluator 반복 수
8. 안전 중단점, 회수 artifact, 다음 분기

이 8개가 없으면 5,000 iter 초과 학습은 `HOLD — 근거 불충분`이다.

## 9. Run06 이후 개선 학습 방향 (260831 사전 계획)

### 9-a. 원칙

- Run06(`iter=9900`, checkpoint SHA `8eb06e2…b636`)은 **동결 기준선**이다. 덮어쓰지 않는다.
- 공식 평가는 제출 뒤 일괄 진행되어 개선 입력으로 쓸 수 없다고 보고, **제출 전 자체 점수표**를
  약점 지도로 사용한다. 공식 결과를 기다리는 계획은 철회한다.
- 먼저 기존 H4·H6·H7 evaluator를 H1·H2·H3·H5까지 확장해
  모든 시나리오의 survival·tracking proxy를 같은 형식으로 기록한다. 이 계측 공백이 남아 있으면
  Run06은 `SELF_ASSESSMENT_INCOMPLETE`이며 새 reward 학습은 `HOLD — 비교자 미완성`이다.
- 내부 proxy v1은 Run06 `env.yaml`의 exponential tracking과 `std=0.5`를 사용한다:
  `tracking_proxy=exp(-(RMSE/0.5)^2)`. 정확한 공식 변환식은 공개되지 않았으므로 공식 점수가 아니다.
- 각 H1~H7은 `survival_proxy≥0.95`와 `tracking_proxy≥0.70`을 모두 만족해야
  `INTERNAL_SCENARIO_PASS`다. 부분 측정은 점수로 세지 않는다.
- 7개가 모두 측정·통과하고 가중 시뮬 proxy≥0.70일 때만 `SELF_ASSESSMENT_PASS`다.
  제출 최소조건은 문서 자체감사를 포함한 총 70/100, 운영 목표는 75/100 이상이다.
- 각 screening은 동일 코드·seed·num_envs·3,000 iter·고정 H1~H7 evaluator에서 단일 reward만 바꾼다.
- 성공 판정은 시나리오 가중 tracking proxy 개선과 survival proxy 비열등성을 함께 요구한다.

### 9-b. 후보 순서

| 우선 | 단일 변경 후보 | 이유 | 직접 목표 | 핵심 위험 | 현재 결정 |
|---:|---|---|---|---|---|
| 0 | Run06 H1~H7 전체 자체 채점 | 제출 전 유일하게 사용 가능한 약점 지도 | 시뮬 proxy /70 | 내부식≠공식식 | **현재 필수 작업** |
| 조건 1 | `track_lin_vel_xy_exp: 1.0 → 1.5` | 자체 scorecard에서 H2/H3/H5/H6 tracking이 최대 감점일 때만 | H2/H3/H5/H6 tracking | yaw·std·생존 악화; 1.0→1.5 단조성 미증명 | 조건 충족 시 3k screening |
| 조건 2 | `feet_air_time: 0.2 → 0.3` | 자체 scorecard에서 H5/H6 생존·통과가 약할 때만 | 요철·경사 생존/추종 | 한발 깡총·평지 안정 저하 | 0.75는 함정 체험값이므로 채택 실험 금지 |
| 조건 3 | `flat_orientation_l2: -1.5 → -1.0` | 자체 scorecard에서 H1/H5/H6/H7 survival이 약하고 자세 telemetry가 원인을 지지할 때 | torso 자세·생존 | 약화 시 낙상, 강화 시 이동·경사 적응 저하 | 원인 확인 뒤 screening |
| 보류 | `termination_penalty` | -50→-90에서 추종·std 악화가 이미 관측됨 | 전 시나리오 생존 | 소극 정책 | 자체 생존 FAIL과 추가 근거 전 재개 금지 |
| 보류 | `track_ang_vel_z_exp` | Run04에서 1.0이 개선됐고 Run06 H4 내부 telemetry가 긍정적 | H4 | 선속도 축과 다시 시소 | 자체 H4 최대 감점 전 변경 금지 |

`1.5`, `0.3`, `-1.0`은 최적값 주장이 아니라 현재값과 극단값 사이의 보수적 screening 점이다.
Isaac Lab/가이드의 의미 설명은 방향 가설을 지지하지만 NCRC 최적값을 제공하지 않는다.

### 9-c. 승급 규칙

1. 3,000 iter 결과를 Run06의 **동일 3,000-window 대조**와 비교한다. Run06 10k 마지막 구간과
   바로 비교해 reward 효과와 학습시간 효과를 섞지 않는다.
2. 주 목표 시나리오의 가중 내부 tracking proxy가 개선되고, 전체 evaluator의 조기 종료·생존 proxy가
   비열등이며, H1/H4/H7 안정성 영상에서 새 부작용이 없어야 `screening winner`다.
3. 개선·악화가 교환되거나 threshold가 없으면 `INCONCLUSIVE`; 장기 학습하지 않는다.
4. screening winner만 독립 seed와 같은 자체 evaluator로 재검증한 뒤 10,000 iter 장기 후보가 된다.
5. 최종 선택은 `Run06 동결본`과 `장기 후보`를 같은 evaluator·영상·artifact 계약으로 비교해 결정한다.
