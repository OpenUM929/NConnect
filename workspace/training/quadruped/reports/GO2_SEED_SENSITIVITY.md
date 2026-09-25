# Go2 seed 흔들림과 보상 항 (2026-09-17)

> **생성 문서 — 손으로 고치지 않는다.** `python -B tools/go2_seed_sensitivity.py`가 만든다.
> 증거 `reports/evidence/go2_seed_sensitivity_20260917/`, 관문 `tools/test_go2_seed_sensitivity_contract.py`.
> 표기: [확인] 원자료에서 직접 · [추정] 확인된 사실에서 유추 · [모름] 근거 없음.

## 0. 세 가지 흔들림을 구분한다

| 종류 | 상태 | 근거 |
|---|---|---|
| 같은 설정·같은 seed 재학습 | **0** [확인] | §1 |
| 평가 seed(101·202·303) 사이 | **측정됨** [확인] | §4, `BASELINE_MARGIN.csv`(생존 이항 재표집) |
| 학습 seed 사이 | **측정된 적 없음** [확인] — 전 학습이 seed 42 | `GO2_NOW.md` §0 |

한 항을 바꾸면 seed가 같아도 학습 궤적 전체가 달라진다. 그래서 한 항 변경 회차의 차이에는 **레버 효과와 궤적 갈라짐이 섞여 있고**, 둘을 가를 대조군(같은 설정의 다른 seed)이 없다 [확인: 대조군 0건].

## 1. 같은 seed 재학습은 결정론이다 (`SAME_SEED_REPEAT.csv`)

| first | repeat | terrain_999_first | terrain_999_repeat | identical |
|---|---|---|---|---|
| `go2_g_a010_lin_vel_z_m2` | `go2_g_a010_lin_vel_z_m2_v2_260906` | `0.5545` | `0.5545` | `True` |
| `go2_g_a013_flat_orientation_m1` | `go2_g_a025_flat_orientation_m1` | `0.8163` | `0.8163` | `True` |

- [확인] 배포 주석 중 cudnn 비결정성 문장(아래 둘째 줄)은 이 스택에서 반례 2건이다. 첫째 줄(발 들기 경계)은 §3-2에서 쓴다.
  - `quadruped_rewards.py:102` — #    (정확한 경계는 실행마다 다름 — 직접 확인하세요).
  - `quadruped_rewards.py:120` — #   ※ 같은 설정·같은 seed 라도 cudnn 비결정성으로 매번 조금씩 다릅니다 (정상).

## 2. 같은 seed의 한 항 변경 — margin 변화 대 결과 변화 (`ONE_CHANGE_DRIFT.csv`)

| from | to | change | margin_from | margin_to | margin_delta | terrain_999_from | terrain_999_to | terrain_delta | climb10_ge1_from | climb10_ge1_to | climb10_ge2_from | climb10_ge2_to |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `A017` | `A031` | `feet_air_time 0.2->0.01` | `+0.0917` | `+0.1069` | `+0.0152` | `4.2503` | `4.7864` | `+0.5361` | — | — | — | — |
| `A017` | `A032` | `feet_air_time 0.2->0.1` | `+0.0917` | `+0.0997` | `+0.0080` | `4.2503` | `4.5819` | `+0.3316` | — | — | — | — |
| `A017` | `G-A033` | `track_lin_vel_xy_exp 1.4->1.5` | `+0.0917` | `+0.1359` | `+0.0442` | `4.2503` | `4.7087` | `+0.4584` | `28` | `90` | `2` | `43` |
| `G-A033` | `G-A038` | `ang_vel_xy_l2 -0.05->-0.08` | `+0.1359` | `+0.0728` | `-0.0631` | `4.7087` | `3.0348` | `-1.6739` | `90` | `5` | `43` | `0` |

- [확인] 걷기 margin 변화가 `+0.0152`(A031)·`+0.0442`(G-A033)처럼 같은 방향이어도 지형 레벨은 `+0.5361`·`+0.4584`로 크기 순서가 뒤집힌다.
- [확인] G-A038은 margin이 걷기 구간(`+0.0728`)에 남았고 실제로 걸었지만, 지형 레벨은 `-1.6739`, 10cm 오르기 ≥1단은 `90` → `5`대로 무너졌다.
- [추정] margin은 **걷기/정지**만 설명하고, 지형 레벨·계단은 margin 변화의 크기와 맞지 않는다. 이 어긋남이 레버 때문인지 궤적 갈라짐 때문인지는 학습 seed 대조군 없이는 가를 수 없다 [모름].

## 3. seed 운과 가까운 보상 항

### 3-1. margin 경계대의 회차 (`BAND_RUNS.csv`)

| run | margin | margin_loo | zone | zone_loo | walked |
|---|---|---|---|---|---|
| `A021` | `-0.0056` | `-0.0056` | `STOP` | `BAND` | `False` |
| `Pilot-01` | `0.0033` | `-0.0244` | `BAND` | `BAND` | `True` |
| `A015` | `-0.0087` | `-0.0087` | `STOP` | `BAND` | `False` |
| `A018` | `0.0155` | `0.0155` | `BAND` | `BAND` | `False` |

- [확인] 경계대(margin `+0.0033`~`+0.0155`)에서 Pilot-01은 걸었고 A018은 멈췄다. margin 순서와 결과가 반대인 유일한 쌍이다.
- [추정] 경계대 안에서는 보상 식이 걷기·정지를 거의 같게 치므로, 결과를 가르는 것은 seed·궤적이다. A018에서 바꾼 항은 `action_rate_l2`다 — **margin으로 설명되지 않은 유일한 항**이다(FORECAST §3).

### 3-2. G-A033 가중치에서 걷기 구간 경계까지의 거리 (`TERM_HEADROOM.csv`)

| term | g_a033_value | walk_zone_edge | edge_over_value | side |
|---|---|---|---|---|
| `track_lin_vel_xy_exp` | `1.5` | `1.22752` | `0.818` | `reward: edge below value` |
| `lin_vel_z_l2` | `-2.0` | `-6.98491` | `3.492` | `penalty: edge stronger than value` |
| `ang_vel_xy_l2` | `-0.05` | `-0.107243` | `2.145` | `penalty: edge stronger than value` |
| `action_rate_l2` | `-0.01` | `-0.0297831` | `2.978` | `penalty: edge stronger than value` |
| `dof_acc_l2` | `-2.5e-07` | `-4.64717e-07` | `1.859` | `penalty: edge stronger than value` |
| `dof_torques_l2` | `-0.0002` | `-0.000648745` | `3.244` | `penalty: edge stronger than value` |
| `feet_air_time` | `0.2` | `1.70517` | `8.526` | `reward: edge above value` |

- 읽는 법: `edge_over_value`가 1에 가까울수록 작은 변경으로 경계대에 들어간다.
- [확인: 계산] `track_lin_vel_xy_exp`는 `1.22752`까지 내려가면 경계다(현재의 `0.818`배). 벌점 항은 `dof_acc_l2`·`ang_vel_xy_l2`가 현재의 약 2배, `action_rate_l2`가 약 3배에서 경계다.
- [추정] 경계에 가까운 항일수록 그 항을 움직인 회차의 걷기/정지는 seed 운의 영향을 크게 받는다. G-A033 자체는 margin `+0.1359`로 경계대 최고값의 약 9배라, **G-A033의 걷기 자체는 seed에 강할 것**이다. 계단·옆걸음 결과에는 이 말이 해당하지 않는다(§2).
- [확인: 배포 주석] `feet_air_time`은 "정확한 경계는 실행마다 다름"이라고 배포 파일이 직접 적는다.

## 4. 평가 seed 흔들림이 큰 상황 (`EVAL_SEED_SPREAD.csv`, G-A033, 로봇 32대)

폭 = 세 평가 seed 사이 넘어지지 않은 로봇 수의 최대 − 최소. 폭 4대 이상만 적는다.

| scenario | case | situation | upright_101 | upright_202 | upright_303 | robots | spread |
|---|---|---|---|---|---|---|---|
| `G5` | `stairs_10_down` | `climb` | `28` | `17` | `17` | `32` | `11` |
| `G6` | `push_pos_x` | `push` | `27` | `31` | `30` | `32` | `4` |

- [확인] 폭 4대 이상은 `stairs_10_down` 11대, `push_pos_x` 4대뿐이다. 가장 넓은 case가 G-A038이 무너진 10cm 오르기다. 험지 옆걸음(`rough_lateral`)은 1대로 좁다 — 옆걸음 종료는 평가 seed와 상관없이 일정하게 일어난다.
- [확인: FORECAST §5-1] `lin_vel_z_l2`·`ang_vel_xy_l2`는 비교 가능한 정책 전부(계단·밀침 2개, 흔들림 3개)에서 **계단(오르는 쪽이 값이 크다)과 흔들림·밀침(넘어지기 직전이 값이 크다)의 부호가 반대**다. 한쪽을 강하게 벌하면 다른 쪽을 돕는 맞교환 항이다. G-A038(`ang_vel_xy_l2` 강화)이 옆걸음을 얻고 10cm 오르기를 잃은 것과 같은 방향이다.
- [추정] 10cm 오르기는 평가 seed만 바꿔도 폭이 가장 넓은 상황이고, 위 두 항이 그 상황의 보상 균형을 직접 움직인다. 그래서 이 두 항을 바꾼 회차의 계단 결과가 학습 seed에도 가장 민감할 것이다. 측정은 없다 [모름].

## 5. 학습 seed 흔들림을 잡으면 풀리는 것

| # | 지금 가를 수 없는 것 | 원자료 | seed 대조군이 있으면 |
|---|---|---|---|
| 1 | 기준선 승급 근거 G4 `+3.65467`가 `track 1.5` 때문인가 | `BASELINE_MARGIN.csv` | G-A033 설정의 다른 seed가 같은 G4를 내는지로 판정 |
| 2 | G-A038의 10cm 오르기 붕괴가 `ang_vel_xy_l2` 때문인가 | §2 | G-A033 설정 다른 seed의 10cm ≥1단 수가 `90` 근처에 머물면 레버, 크게 흔들리면 판정 보류 |
| 3 | 경계대의 폭(Pilot 걷기·A018 정지) | §3-1 | 같은 설정의 걷기/정지 비율로 경계대를 측정값으로 바꿈 |
| 4 | 사전 등록 한도가 진짜 잡음보다 넓은가 | `reports/evidence/go2_fact_rules_20260917/` | 지금 한도는 평가 표집만 넣은 **하한**이다. 학습 seed 분산을 더하면 FAIL/PASS가 잡음인지 가려진다 |
| 5 | 10cm ≥2단이 한 항 변경마다 크게 흔들린 것 | `STAIRS_CLIMB.csv` | 흔들림 폭 안의 차이는 레버로 인용하지 않게 됨 |
| 6 | 학습 18회의 단일 seed 결과 중 어느 것이 흔들림 밖인가 | `reports/runs/INDEX.md` | 과거 결론을 흔들림 밖/안으로 다시 표시 |

- [확인] 이 표의 1~6은 지금 모두 [모름]이다. 풀리는 것은 **해석 가능성**이지 점수 상승이 아니다.
- [모름] seed 반복 회차가 R-6(보상 가중치만) 안인지는 사용자 결정 대기다 — 열린 결정
  `U2-SEED-REPLICATE-20260918`(`reports/GO2_OPEN_DECISIONS.md`). 2026-09-19: 이 번호를 생성
  문서에 손으로 적어 두었더니 다음 재생성이 지웠다. 생성 문서의 문구는 생성기에서 고친다.
