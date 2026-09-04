# Go2 Default-01 vs Pilot-01 결과 분석 보고서 — 260901

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 proxy /70의 개선 근거를 확보하고, 설계 의도 /20과 리포트 /10에 사용할 인과·한계 기록을 만든다.
- [현재 단계] **단계 3/6 — 환경 적응 게이트**. 단계 0 artifact 정합성, 단계 1 G1·G2 기본 행동, 단계 2 1,000-iter pilot 비교는 완료됐지만 G3·G4·G5·G7이 내부 기준에 미달했다.
- [확보] Default/Pilot 각 69 telemetry, 정책별 worst-case 영상 7개, model/env/registry lineage, `ARTIFACT_VERIFIED`, 14개 영상의 12-frame 직접 관찰.
- [미확보] G3·G4·G5·G7 `INTERNAL_SCENARIO_PASS`, 독립 학습 seed 재현성, Go2 설계 의도·리포트 자체감사, `OFFICIAL_RESULT`.
- [이번 테스트] 배포 기본 reward와 1차 4변수 동시 튜닝을 동일 evaluator에서 비교해 전면 재시작과 Pilot 기반 업그레이드 중 어느 경로가 효율적인지 판정한다.
- [흐름] Default/Pilot 쌍대평가 완료 → **환경 약점 분리** → 통과 시 단일변수 승자 조합 → 실패 시 Default 계보에서 후보 폐기·교체 → 최종 제출.
- [지금 할 일] 서버를 켜지 않고, 다음 단일변수 screening package가 사전등록·검증될 때까지 대기한다.
- [보장하지 않음] 내부 proxy, 단일 학습 seed, 10초 worst-case 영상만으로 공식 점수·예선 통과·reward별 인과효과를 보장하지 않는다.

## 1. 결론

1. **Pilot 조합은 Default보다 명확히 우수하다.** 동일 evaluator의 시뮬레이션 proxy는 Default `17.90699/70`, Pilot `41.97990/70`이며 절대 차이는 `+24.07291/70`, 상대 증가는 `+134.43%`다. 세 평가 seed 모두 Pilot 방향으로 `+0.3555~+0.3784` 개선됐다.
2. **그러나 Pilot은 최종 후보가 아니다.** Pilot도 `INTERNAL_GATE_FAIL`이며 G3·G4·G5·G7이 실패했다. 내부 최소선 `49/70`에도 `7.0201점` 부족하다.
3. **전면적으로 Default 성능으로 되돌아가는 것은 비효율적이다.** Default는 G1~G7 모두 실패했고, Pilot은 G1·G2·G6을 내부 기준까지 끌어올렸다.
4. **학습 계보는 Default에서 다시 시작하는 기존 결정이 여전히 맞다.** Pilot의 네 변경은 동시에 적용됐으므로 어느 reward가 개선·회귀를 만들었는지 분리할 수 없다. Pilot은 resume 대상이 아니라 성능 상한·가설 출처로 보존한다.
5. 사전등록 분기는 **`SHARED_WEAKNESS_FOUND`**다. 두 정책이 G3·G4·G5·G7에서 함께 실패했고, Pilot은 G3·G4·G5 survival 비열등 기준도 위반했다.

## 2. 예상 결과와 실제 결과

| 항목 | 사전 예상·판정 기준 | 실제 결과 | 판정 |
|---|---|---|---|
| 산출물 | 정책별 69 telemetry, 7영상, paired report, FULL ZIP | 69×2 telemetry, 7×2 영상, `RUNNER_RC=0`, 외부 ZIP SHA 일치 | `ARTIFACT_VERIFIED` |
| 서버 벽시계 | package 실행 1.5~3시간 추정 | artifact 로그가 덮는 최초 학습 시작~FULL 완료 창은 약 2시간 8분(15:46~17:54) | 기록 창은 추정 범위 안. 서버 생성~종료 전체 과금 시간은 미측정이고 runner 실패가 불필요한 대기·재개를 추가함 |
| Pilot 우위 최소폭 | weighted fraction `+0.03` 이상 | `+0.34390`, 즉 약 `+24.07/70` | 최소폭을 크게 초과 |
| seed 방향 | 3 seed 중 2개 이상 같은 방향, 어느 seed도 `-0.02` 미만 역전 없음 | 101 `+0.3784`, 202 `+0.3668`, 303 `+0.3555` | 세 seed 모두 Pilot 우위 |
| 시나리오 비열등 | survival `-0.02`, tracking `-0.05` 이내 | G3 survival `-0.1563`, G4 `-0.0313`, G5 `-0.1250` | Pilot promising 조건 불충족 |
| 내부 전체 게이트 | 모든 G survival≥.95, tracking≥.70, weighted≥.70 | Pilot G1·G2·G6만 통과, fraction `.5997` | `INTERNAL_GATE_FAIL` |
| 영상 | 정책별 정량 worst-case를 사람이 관찰 | 14영상×12프레임 직접 관찰 완료 | `VIDEO_OBSERVED`; 연속 gait timing은 미측정 |
| 공식 결과 | 공식 evaluator는 별도 회수 | 없음 | `OFFICIAL_RESULT_UNMEASURED` |

artifact 내부 실행 창은 사전 추정에 들어왔지만, 최초 package 오류로 재개가 필요했고 서버 생성·업로드·진단·다운로드·종료 시각은 artifact만으로 복원되지 않는다. 따라서 **사용자가 실제로 소비한 총 서버 과금 시간은 `[미측정]`**이며, runner 오류가 그 시간을 불필요하게 늘린 사실만 확정한다.

## 3. G1~G7 쌍대 결과

`scenario_proxy`는 공개된 채점 개념을 흉내 낸 내부식 `survival_proxy × tracking_proxy`의 case별 값이며, scenario는 고정 case·seed 중 최악값을 채택한다. 공식 점수가 아니다.

| G | Default S/T/P | Pilot S/T/P | Pilot ΔP | Pilot 내부 판정 | Pilot 최대 감점 `/70` | 영상 | 공식 |
|---|---:|---:|---:|---|---:|---|---|
| G1 전진 | `1.000/.0036/.0036` | `1.000/.8925/.8925` | `+.8889` | `INTERNAL_SCENARIO_PASS` | 1.13 | `VIDEO_OBSERVED`: 평지에서 뚜렷한 전진, Default는 제자리 성향 | 미측정 |
| G2 전방위 | `1.000/.2653/.2653` | `1.000/.7521/.7521` | `+.4868` | `INTERNAL_SCENARIO_PASS` | 2.60 | `VIDEO_OBSERVED`: Pilot 이동·회전 범위 증가, Default는 이동량이 작음 | 미측정 |
| G3 rough | `.7188/.3677/.2655` | `.5625/.5904/.4403` | `+.1748` | `INTERNAL_SCENARIO_FAIL` | 7.84 | `VIDEO_OBSERVED`: Pilot은 더 움직이지만 거친 지형에서 낮은 자세·불안정이 보임 | 미측정 |
| G4 ±20° | `1.000/.3835/.3835` | `.9688/.5288/.5288` | `+.1453` | `INTERNAL_SCENARIO_FAIL` | 4.95 | `VIDEO_OBSERVED`: Pilot의 경사 이동이 늘었으나 추종 부족 | 미측정 |
| G5 계단 | `1.000/.1318/.1318` | `.8750/.2595/.2270` | `+.0953` | `INTERNAL_SCENARIO_FAIL` | **8.12** | `VIDEO_OBSERVED`: 계단에서 접근·움직임은 늘지만 정체·불안정, 깨끗한 통과 미관찰 | 미측정 |
| G6 push | `.6250/.9352/.5854` | `.9688/.9661/.9378` | `+.3524` | `INTERNAL_SCENARIO_PASS` | 0.44 | `VIDEO_OBSERVED`: Pilot은 밀침 뒤 대체로 자세 유지·회복 | 미측정 |
| G7 DR | `.7188/.3677/.2655` | `.9375/.5904/.5781` | `+.3125` | `INTERNAL_SCENARIO_FAIL` | 2.95 | `VIDEO_OBSERVED`: rough+DR 이동 개선, 안정·추종 기준에는 미달 | 미측정 |

`S/T/P`는 각각 scenario 집계 survival/tracking/proxy다. survival 최악 case와 tracking 최악 case가 다를 수 있으므로 세 값을 하나의 동일 rollout 관측값처럼 해석하지 않는다.

## 4. 시나리오별 해석

### 4-a. G1·G2 — 정지 편법에서 실제 이동으로 전환

- Default G1 worst tracking은 `.0036`이고 실제 평균 속도는 약 `0.026 m/s` 수준이라 빠른 전진 명령을 사실상 따라가지 못했다.
- Pilot G1 worst RMSE는 `0.169 m/s`, tracking `.8925`, survival `1.0`이다.
- G2도 Pilot이 `.7521`로 내부 기준 `.70`을 넘었다. 영상에서 Default보다 위치·방향 변화가 뚜렷하다.
- **추론:** 네 변경 조합은 Default의 “안전하게 거의 움직이지 않기” 편법을 크게 줄였다. 다만 네 항 중 어느 하나의 효과인지 분리되지 않는다.

### 4-b. G6 — 가장 완전한 개선

- Default worst survival `.625`에서 Pilot `.96875`로 개선됐다.
- Pilot worst push case는 32 env 중 1개 종료, recovery rate `1.0`, median recovery `0.16s`다.
- tracking도 `.9352→.9661`로 비열등하다.
- **판정:** 현재 bundle에서 가장 신뢰도 높은 개선 시나리오다. 그래도 공식 push 크기·방향·시점은 공개되지 않아 공식 결과로 승격하지 않는다.

### 4-c. G3·G5 — 속도/발동작과 안정성의 trade-off

- G3 proxy는 좋아졌지만 survival이 `.71875→.5625`로 악화됐다. Pilot worst rough lateral에서는 32 env 중 14개가 종료됐다.
- G5는 tracking/completion proxy가 `.1318→.2595`로 좋아졌지만 survival이 `1.0→.875`로 악화됐다. worst stairs 15cm down은 32 env 중 4개 종료, progress 기반 completion `.259`다.
- **추론:** Pilot은 더 적극적으로 움직여 추종과 진행량을 늘렸지만 rough·stairs에서 안정성 비용을 지불했다. `feet_air_time` 증가와 수직/roll-pitch penalty 완화가 가능한 원인이지만 동시변경이라 인과 확정은 금지한다.

### 4-d. G4·G7 — 개선됐지만 승급하기에는 부족

- G4는 tracking `.3835→.5288`; survival은 `1.0→.96875`다. 작은 survival 회귀와 큰 tracking 미달이 동시에 남는다.
- G7은 survival `.71875→.9375`, tracking `.3677→.5904`로 개선됐지만 두 내부 기준 `.95/.70`에 모두 조금씩 미달한다.
- G7 metadata에는 실제 randomized body mass와 event config가 보존돼 있으나, 공식 DR 항목·범위는 미공개다.

## 5. reward별 현재 판정

| reward | Default→Pilot | 현재 판정 | 근거 | 한계 |
|---|---:|---|---|---|
| `track_lin_vel_xy_exp` | `1.0→1.2` | `INCONCLUSIVE` | G1·G2 tracking 대폭 개선 | 네 reward 동시 변경 |
| `feet_air_time` | `.01→.2` | `INCONCLUSIVE` | G5 진행·tracking 개선 가능성과 rough/stairs survival 회귀가 함께 관찰됨 | 발 높이·contact timing 직접 계측 없음 |
| `lin_vel_z_l2` | `-3→-2` | `INCONCLUSIVE` | 적극적 이동과 수직 안정성 trade-off 가능 | 단독 실험 없음 |
| `ang_vel_xy_l2` | `-.08→-.05` | `INCONCLUSIVE` | 회전·경사 이동 개선과 rough/stairs 불안정이 공존 | 단독 실험 없음 |
| `action_rate_l2` | `-.01→-.01` | `미측정` | 변경하지 않은 control | jerk·관절 명령 급변 정량 없음 |
| `track_ang_vel_z_exp` | `.75→.75` | `부분 만족` | Pilot G2 worst-case가 survival 1.0, tracking .7521 | combined metric이며 단독 yaw reward 효과 아님 |

Pilot **조합 전체**는 `부분 만족`이다. G1·G2·G6은 유효한 개선이지만 G3·G4·G5·G7과 전체 게이트가 미달한다.

## 6. Upgrade-or-Restart 결정

### 확정 결정

- **Pilot 성능을 버리고 Default 결과로 돌아가지는 않는다.** Pilot은 앞으로의 비교 상한과 변경 가설로 보존한다.
- **Pilot checkpoint를 resume하지 않는다.** 다음 인과 실험은 Default-01과 동일한 배포 기본 계보에서 from-scratch로 수행한다.
- 즉, 운영 결정은 “성능 기준은 Pilot, 실험 출발점은 Default”다.

### 첫 단일변수 후보

내부 규칙 `weight × (1-scenario_proxy)`의 최대 감점은 G5 `8.12/70`, 다음은 G3 `7.84/70`이다. G5의 약한 인수는 tracking/completion `.2595`이며 강좌상 가장 직접 연결된 Pilot 변경은 `feet_air_time`이다.

따라서 첫 정보가치 높은 screening 후보는 **Default-01에서 `feet_air_time .01→.2`만 변경한 1,000 iter**다. 이는 `.2`가 최적이라는 뜻이 아니라 Pilot 개선·회귀 중 feet-air 기여를 분리하기 위한 진단이다.

승급 조건은 다음과 같다.

1. G5 proxy가 Default보다 `+0.03` 이상 개선.
2. G5 survival이 Default 대비 `-0.02` 이내.
3. G1~G7 어느 scenario도 survival `-0.02`, tracking `-0.05`를 초과해 회귀하지 않음.
4. 동일 69-case evaluator와 필수 영상에서 bounding·계단 정체·낙상 증가가 관찰되지 않음.
5. 1,000 iter 결과가 위 조건을 만족할 때만 3,000~5,000 iter 또는 독립 학습 seed로 승급.

## 7. 증거와 한계

### 직접 증거

- 회수 원본: `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/original/GO2_DEFAULT_VS_PILOT_RESULT.zip`
- 외부 SHA-256: `af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b`
- 선택 병합 증거: `reports/evidence/go2_default_vs_pilot_260901/`
- 영상 관찰 시트: `reports/evidence/go2_default_vs_pilot_260901/contact_sheets/`
- 내부 산식·분기: `go2_fixed_eval_report.py`, `config/go2_self_eval_registry.json`

### 한계

1. 정책별 학습 seed는 42 하나뿐이다. 평가 seed 3개는 학습 재현성을 증명하지 않는다.
2. 영상은 scenario별 정책 자체 worst-case라 Default와 Pilot의 exact case가 다를 수 있고, 500 steps 약 10초다.
3. G5 completion은 실제 계단 완주 판정이 아니라 진행거리 기반 내부 proxy다.
4. 내부 tracking 변환식, case grid, terrain, push, DR와 공식 evaluator의 동일성은 확인되지 않았다.
5. `OFFICIAL_RESULT`와 Go2 총 자체예상 `/100`은 아직 계산하지 않았다.

## 8. 최종 판정

| 계층 | Default-01 | Pilot-01 |
|---|---|---|
| artifact | `ARTIFACT_VERIFIED` | `ARTIFACT_VERIFIED` |
| video | `VIDEO_OBSERVED` — 7개 worst-case contact sheet 관찰 | `VIDEO_OBSERVED` — 7개 worst-case contact sheet 관찰 |
| internal | `INTERNAL_GATE_FAIL`, `17.90699/70` | `INTERNAL_GATE_FAIL`, `41.97990/70` |
| official | `OFFICIAL_RESULT_UNMEASURED` | `OFFICIAL_RESULT_UNMEASURED` |

**최종 해석:** Pilot은 실패한 튜닝이 아니라 **큰 개선과 명확한 환경 안정성 부채를 동시에 가진 유효한 탐색 결과**다. 따라서 전면 폐기·resume 어느 쪽도 선택하지 않고, Default 계보에서 Pilot 변경을 하나씩 재검증한다.
