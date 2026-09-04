# Go2 `feet_air_time=0.20` 단일변수 1,000-iter screening PRD

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 70점 축에서 최대 내부 감점인 G5 계단과 G3 험지의 원인을 분리하고, 설계 의도 20점·리포트 10점에 사용할 인과 근거를 만든다.
- [현재 단계] 단계 3/6 — 환경 적응 게이트. Default-01과 Pilot-01 비교는 끝났지만 G3·G4·G5·G7이 내부 기준에 미달했다.
- [확보] Default-01 `17.90699/70`, Pilot-01 `41.97990/70`, Pilot 개선 `+24.07291/70`, 정책별 telemetry 69건과 영상 7개를 검증·관찰했다.
- [미확보] `feet_air_time` 단독 효과, G3·G4·G5·G7 `INTERNAL_SCENARIO_PASS`, 독립 학습 seed 재현성, `OFFICIAL_RESULT`.
- [이번 테스트] Default-01 계보에서 `feet_air_time`만 `0.01→0.20`으로 바꿔 G5 진행 개선과 G3/G5 survival 회귀 중 이 변수의 기여를 분리한다.
- [흐름] 쌍대평가 완료 → **단일변수 1k screening** → 정량·영상 게이트 충족 시 독립 seed/3k~5k → 실패 시 후보 폐기·재계획 → 최종 제출.
- [지금 할 일] 로컬 package 검증이 끝날 때까지 서버를 켜지 않는다. 검증 후 단일 ZIP 업로드와 한 줄 실행만 수행한다.
- [보장하지 않음] 단일 학습 seed, 내부 proxy, 1,000 iteration은 공식 점수·최적 reward·예선 통과를 보장하지 않는다.

## 1. 식별자와 가설

| 항목 | 사전등록값 |
|---|---|
| work ID | `G-A007` |
| run ID | `train_260901-Go2_feet_air_time_020_1000` |
| 실험 등급 | 개선 |
| 기준 policy | Default-01, checkpoint iter 800, `model_best.pt sha256=99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676` |
| 기준 env | `sha256=4d1d294b63dafeceb223fb48226cbe6a533157bc54f97ce486f644bd1bda262c` |
| 기준 평가 artifact | `GO2_DEFAULT_VS_PILOT_RESULT.zip sha256=af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b` |
| candidate 출발 | Default reward 소스에서 from-scratch |
| 단일 변경 | `feet_air_time: 0.01 → 0.20` |
| 1차 가설 | 발 들기 보상이 G5 계단 진행·tracking proxy를 개선한다. |
| 위험 가설 | 과도한 발 들기가 bounding·착지 불안정을 일으켜 G3/G5 survival을 낮춘다. |

`0.20`은 최적값 주장이 아니다. Pilot-01의 동시변경 네 항목 중 `feet_air_time`의 정보가치를 분리하는 진단점이다.

## 2. 통제 변수

| 통제 항목 | 고정값 |
|---|---|
| `track_lin_vel_xy_exp` | `1.0` |
| `lin_vel_z_l2` | `-3.0` |
| `ang_vel_xy_l2` | `-0.08` |
| `action_rate_l2` | `-0.01` |
| task | `Quadruped-v0` |
| training seed | `42` |
| `num_envs` | `4096` |
| `max_iterations` | `1000` |
| 초기화 | `--resume` 없이 from-scratch |
| evaluator | `go2_self_eval_registry.json` + 내부 proxy v1 |
| evaluation seeds | `101, 202, 303` |
| evaluation envs/steps | case당 `32 env`, `1000 steps` |
| 영상 | 시나리오별 candidate worst case 7개, `4 env`, `500 steps`, 약 10초 |

Default-01 영상 재생성은 `VIDEO_NOT_REQUIRED`다. 동일 checkpoint tensor·동일 registry/evaluator 조건의 G1~G7 worst-case 영상 7개가 G-A006에서 이미 `ARTIFACT_VERIFIED`·`VIDEO_OBSERVED`됐으며, 경로는 `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/extracted/videos/default/`이다. 새 checkpoint인 candidate 영상 7개는 `VIDEO_REQUIRED`다.

`4096 env`는 강좌에 제시된 Go2 학습 명령이며 동일 서버의 Default-01에서 실제 완료됐다. 그러나 서버 하드웨어의 절대 최대 병렬값을 측정한 결과는 아니다. GPU 학습 프로세스를 여러 개 동시에 실행하지 않고, Isaac Lab 단일 프로세스 안의 4,096개 환경 병렬화만 사용한다.

## 3. 근거와 한계

- 로컬 근거: Pilot-01은 G5 tracking/completion proxy를 `.13176→.25948`로 높였지만 survival을 `1.0→.875`로 낮췄다.
- 우선순위 근거: G5 최대 내부 감점 `8.12/70`; 다음은 G3 `7.84/70`이다.
- 강좌 근거: `feet_air_time`은 발 들기·험지 돌파와 직접 연결된 조절 항목으로 설명된다.
- 한계: Pilot은 `track_lin_vel_xy_exp`, `feet_air_time`, `lin_vel_z_l2`, `ang_vel_xy_l2`를 동시에 바꿨으므로 기존 결과에서 개별 인과를 확정할 수 없다.
- 공식 한계: 공식 evaluator 입력·tracking 변환·통과선은 공개 확인되지 않았다. 본 테스트는 `INTERNAL_GATE_*`만 판정한다.

## 4. G1~G7 측정 계약

| G | 직접 측정 | 이 실험에서의 역할 | 영상 | 공식 결과 |
|---|---|---|---|---|
| G1 전진 | survival·xy tracking | 기본 전진 비열등 | 필수 | `OFFICIAL_RESULT_UNMEASURED` |
| G2 전방위 | survival·xy/yaw tracking | 방향 전환 비열등 | 필수 | `OFFICIAL_RESULT_UNMEASURED` |
| G3 험지 | survival·xy tracking | 발 들기 효과·착지 불안정 핵심 안전 게이트 | 필수 | `OFFICIAL_RESULT_UNMEASURED` |
| G4 ±20° | survival·xy tracking | 자세 안정 비열등 | 필수 | `OFFICIAL_RESULT_UNMEASURED` |
| G5 계단 | survival·tracking·진행거리 completion | **1차 개선 목표** | 필수 | `OFFICIAL_RESULT_UNMEASURED` |
| G6 밀침 | survival·회복·post-push tracking | 반응 안정 비열등 | 필수 | `OFFICIAL_RESULT_UNMEASURED` |
| G7 DR | survival·xy tracking·실현 randomization | 일반화 비열등 | 필수 | `OFFICIAL_RESULT_UNMEASURED` |

## 5. 사전 판정 게이트

### 5-a. 정량 승급 조건 — 모두 충족

1. candidate telemetry `69/69`이고 G1~G7 survival·tracking이 모두 계산된다.
2. G5 scenario proxy가 Default-01 대비 `+0.03` 이상이다.
3. G5 survival delta가 `-0.02` 이상이다.
4. 모든 G1~G7 survival delta가 `-0.02` 이상이다.
5. 모든 G1~G7 tracking delta가 `-0.05` 이상이다.
6. 평가 seed 101·202·303 중 어느 것도 전체 weighted proxy delta가 `-0.02` 미만으로 역전되지 않는다.

정량 조건 충족만으로는 승급하지 않고 `INTERNAL_SCREEN_QUANTITATIVE_PASS_VIDEO_REVIEW_PENDING`으로 기록한다.

### 5-b. 영상 승급 조건

- candidate worst-case 영상 7/7을 회수한다.
- bounding, 반복 점프, 계단 정체, 배·무릎 접촉, 낙상 증가가 Default 관찰보다 악화되지 않는다.
- 영상 판독 후에만 `VIDEO_OBSERVED`를 부여한다.
- 정량과 영상 조건을 모두 만족해야 `INTERNAL_SCREEN_PROMISING_EXPLORATORY`로 분류한다.

### 5-c. 실패·INCONCLUSIVE

- 정량 비열등 조건 하나라도 위반: `INTERNAL_SCREEN_FAIL`, 3k 이상 승급 금지.
- telemetry·영상·lineage 누락: `INTERNAL_GATE_INCONCLUSIVE` 및 `HOLD — 평가 미완료`.
- G5 tracking은 개선하지만 survival이 악화: `0.20`은 승급시키지 않고 낮은 값 탐색 여부를 새 계획으로 결정한다.
- G5 개선이 없음: `feet_air_time=0.20` 가설을 폐기하고 reward master의 다음 정보가치 후보를 다시 선정한다.

## 6. 조기중단·회수 안전성

- 정상 실험의 재평가점은 1,000 iter 완료 후다. 학습 곡선만으로 중간 성능 판정을 하지 않는다.
- OOM, 비정상 종료, NaN/Inf, finalize 실패, model/env 누락 시 즉시 실패 처리한다.
- 실패 시 runner가 `PARTIAL` 결과 ZIP과 SHA를 생성하며 launcher log, 가능한 checkpoint, source, config를 포함한다.
- 정상 종료 후에도 candidate 영상 7개·telemetry 69건·policy lineage가 결과 ZIP에 없으면 서버 종료 게이트는 해제되지 않는다.

## 7. 서버 실행·시간 예산

- Default-01 재학습과 재평가는 생략하고, 검증된 Default-01 내부 report를 고정 비교 기준으로 package에 포함한다.
- 이전 실측: Default 1k 학습 약 65분, 정책 하나의 69-case 평가 약 22분, 정책 하나의 영상 7개 약 4분.
- 이번 package 예상 실행 창: **약 1시간 35분~2시간**. Isaac Sim 시작·파일 packaging 여유를 포함한 추정이며 전체 서버 과금 시간을 보장하지 않는다.
- 완료 전까지 서버에서 별도 학습·play 프로세스를 병렬 실행하지 않는다.

## 8. 필수 산출물과 결과 분기

필수 결과 ZIP에는 다음을 포함한다.

1. `RUNNER_STATUS.txt`, `RESULT_STATUS.txt`, `SHA256SUMS.txt`
2. candidate `model_best.pt`, `env.yaml`, 학습 log·checkpoint·tfevents·params
3. candidate source와 Default 대비 `reward_only.diff`
4. candidate telemetry 69건과 `SELF_EVAL_REPORT.json/md`
5. 고정 Default baseline report·identity·artifact provenance
6. candidate worst-case 영상 7개와 영상 log
7. `policy.pt`, `POLICY_LINEAGE.json`
8. Default-vs-candidate screening report JSON/Markdown

결과 분기는 `승급 후보 / 실패 / INCONCLUSIVE` 세 가지뿐이다. 승급 후보도 training seed 42 한 번이므로 `exploratory`이며, 다음 단계는 독립 학습 seed 재현이지 즉시 장기 학습이 아니다.
