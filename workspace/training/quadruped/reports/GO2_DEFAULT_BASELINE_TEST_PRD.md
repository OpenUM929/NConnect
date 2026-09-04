# Go2 Default-01 대조 실험 PRD v1

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 proxy /70의 개선 근거와 설계 의도 /20의 변인 통제 근거를 동시에 확보한다.
- [현재 단계] **단계 2/6 — 짧은 학습 pilot**.
- [확보] Default/Pilot 쌍대평가, G-A007·G-A009 실패 근거, G-A010 고정 engine·JSON upload package `ARTIFACT_VERIFIED`.
- [미확보] G-A010 checkpoint·tier-1 telemetry·G1 영상, screening 승자, 독립 학습 seed, 공식 결과.
- [이번 테스트] Default 계보에서 `lin_vel_z_l2 -3.0→-2.0`만 바꾼 1,000-iter candidate의 G1 개선과 전 G survival 비열등을 판정한다.
- [흐름] G-A007·G-A009 폐기 → engine·JSON 검증 완료 → **G-A010 서버 실행·회수** → tier-1 판정 → 독립 seed/장기 승급 → 최종 제출.
- [지금 할 일] `go2_tuning_engine_v1.zip`과 `G_A010_lin_vel_z_m2.json`을 서버에 업로드하고 검증된 한 줄을 실행한다.
- [보장하지 않음] 한 학습 seed, 1,000 iter, 내부 proxy는 공식 점수·예선 통과·reward별 인과효과를 보장하지 않는다.

## 1. 제품 결정

향후 **실험 계보는 배포 기본값에서 새로 시작**한다. Pilot-01을 resume하거나 네 변경을 한꺼번에
추가한 상태에서 바로 업그레이드하지 않는다. 다만 Pilot-01은 폐기하지 않고 다음 두 용도로 동결한다.

1. Default-01과의 동일 조건 성능 비교군.
2. 기본값에서 하나씩 검증할 reward 가설의 출처.

이 결정은 “Pilot-01이 배포 기본보다 얼마나 좋아졌는가”를 현재 artifact만으로 계산할 수 없고,
reward 계수가 달라 평균 reward 자체도 정책 간 공정한 성능척도가 아니기 때문이다.

## 2. 목표와 비목표

### 2-a. 목표

1. 배포 기본 reward의 provenance-valid 1,000-iter 정책 `Default-01`을 생성한다.
2. `Default-01`과 `Pilot-01`을 같은 G1~G7 case·평가 seed·metric으로 쌍대 비교한다.
3. 객관식 분기 규칙으로 다음 단일변수 실험의 출발점과 우선 reward를 결정한다.
4. 학습·영상·telemetry·policy·env의 lineage를 제출 근거로 보존한다.

### 2-b. 비목표

- 1,000 iter 결과로 최적 reward 조합을 확정하지 않는다.
- `Train/mean_reward`의 절대값으로 Default-01과 Pilot-01을 비교하지 않는다.
- 내부 evaluator를 공식 evaluator 또는 공식 점수라고 부르지 않는다.
- 이번 테스트에서 5,000~15,000 iter 장기학습을 실행하지 않는다.
- `LEGACY_INVALID_MAPPING`인 `server_run_Go2_videos.sh`를 사용하지 않는다.

## 3. 실험 대상과 고정 변수

| 항목 | Default-01 | Pilot-01 | 통제 목적 |
|---|---|---|---|
| 출발 | from scratch | 보존된 iter 999 checkpoint | resume 편향 제거 |
| 학습 seed | 42 | 42 | 1차 탐색의 학습 seed 일치 |
| num_envs | 4096 | 4096 | batch 규모 일치 |
| max iterations | 1,000 | 1,000 | 학습 예산 일치 |
| task/agent/terrain | `Quadruped-v0`, 동일 코드·설정 | 회수 artifact 기준 | reward 외 차이 최소화 |
| `track_lin_vel_xy_exp` | **1.0** | 1.2 | 비교 변수 |
| `feet_air_time` | **0.01** | 0.2 | 비교 변수 |
| `lin_vel_z_l2` | **-3.0** | -2.0 | 비교 변수 |
| `ang_vel_xy_l2` | **-0.08** | -0.05 | 비교 변수 |
| `action_rate_l2` | **-0.01** | -0.01 | 불변 control |
| 평가 seed | 101, 202, 303 | 101, 202, 303 | 동일 정책 평가 변동성 |

Default-01 package 생성 시 reward 다섯 값 외의 source diff는 허용하지 않는다. 실행 전 diff, source SHA,
agent/env config SHA를 저장한다. Pilot-01의 frozen 식별자는 iter 999, model SHA
`c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d`다.

## 4. 측정 설계

정본 case와 가중치는 `workspace/training/quadruped/config/go2_self_eval_registry.json`에서 읽는다.

| 시나리오 | 영상 | 내부 정량 | 공식 결과 | 직접 측정하지 않는 것 |
|---|---|---|---|---|
| G1 전진 | gait·drift·배 끌기 | survival, vx RMSE, tracking proxy | `OFFICIAL_RESULT_UNMEASURED` | 공식 command grid |
| G2 전방위 | 방향 편향·회전 gait | survival, xy/yaw RMSE, worst tracking | 동일 | 공식 방향·속도 조합 |
| G3 rough | 걸림·미끄러짐·발 들기 | 실현 terrain, survival, xy RMSE | 동일 | 공식 rough generator |
| G4 ±20° | 상승·하강 자세 | 실현 경사각, survival, xy RMSE | 동일 | 공식 마찰·경사 길이 |
| G5 10/15cm 계단 | 걸림·배 접촉·점프 편법 | step 높이, completion, survival, tracking | 동일 | 공식 계단 형상 |
| G6 push | 충격·회복 인과 | 힘·방향·시각, recovery, post-push tracking | 동일 | 공식 push 조건 |
| G7 DR | 조건별 gait 붕괴 | 실현 randomization, survival, tracking | 동일 | 공식 DR 항목·범위 |

G1~G6 22개 canonical case를 seed 101/202/303으로 실행해 66개 telemetry를 만들고,
G7의 세 registry case를 1:1로 실행해 정책당 총 69개 telemetry를 만든다. 필수 실현값이 없으면
해당 scenario는 `INTERNAL_GATE_INCONCLUSIVE`다.

## 5. 비교 metric과 판정식

### 5-a. 공통 metric

- `survival_proxy`
- 속도축별 RMSE와 `tracking_proxy = exp(-(RMSE / env_track_std)^2)`
- `scenario_proxy = survival_proxy × tracking_proxy`
- `simulation_proxy = Σ(weight × scenario_proxy)`와 `/70` 환산값
- G5 completion, G6 recovery time, G7 realized randomization
- 영상 부작용: bounding, 배 끌기, 정지 편법, 심한 미끄러짐, 떨림

정책 간 비교에는 위와 같은 **reward 계수 독립 metric**만 사용한다. 학습의 `mean_reward`는 각 run 내부
수렴 진단으로만 보존한다.

### 5-b. 내부 시나리오 게이트

- scenario별 survival ≥ 0.95
- scenario별 tracking ≥ 0.70
- G1~G7 전부 측정
- 방향·강도 쌍은 worst case 채택
- weighted simulation proxy ≥ 0.70

### 5-c. 쌍대 비교의 사전등록 허용오차

| 항목 | 실질 차이 기준 |
|---|---:|
| weighted simulation proxy | `0.03` 이상 차이(70점 환산 2.1점) |
| scenario survival 비열등 | 상대 정책 대비 `-0.02` 이상 |
| scenario tracking 비열등 | 상대 정책 대비 `-0.05` 이상 |
| seed 방향 일관성 | 3개 평가 seed 중 2개 이상 같은 방향, 어떤 seed도 proxy `-0.02` 초과 역전 없음 |

이 허용오차는 공식 통과선이 아니라 이번 내부 의사결정용 v1 규칙이다. 실제 분산이 허용오차보다 크면
정책 우열을 강제하지 않고 `INTERNAL_GATE_INCONCLUSIVE`로 둔다.

## 6. Upgrade-or-Restart 분기

향후 학습의 출발점은 모든 분기에서 Default-01이다. 차이는 Pilot-01 변경을 어떤 우선순위로 다시
검증할지에 있다.

| 관측 결과 | 판정 | 다음 행동 |
|---|---|---|
| Pilot이 weighted proxy `+0.03` 이상, seed 일관성·전 G 비열등·영상 무회귀 | `PILOT_COMBINATION_PROMISING` | Pilot을 제출 후보가 아닌 가설 상한으로 보존하고, 기본값에 Pilot 변경을 하나씩 추가하는 forward ablation 시작 |
| Default가 `+0.03` 이상이거나 Pilot이 Default의 scenario gate를 PASS→FAIL로 회귀 | `RESTART_FROM_DEFAULT_CONFIRMED` | Pilot 조합 폐기; Default 최대 감점 G와 약한 인수부터 단일변수 실험 |
| 차이 `±0.03` 미만, seed 방향 혼재, metric/영상 상충 | `INTERNAL_GATE_INCONCLUSIVE` | 학습 seed 1개를 추가 복제하거나 가장 판별력 높은 단일변수 1,000-iter 실험 1개만 수행 |
| 둘 다 같은 G에서 실패 | `SHARED_WEAKNESS_FOUND` | 우열 대신 해당 G의 survival/tracking 약한 인수에 연결된 reward 하나를 기본값에서 변경 |
| telemetry·영상·실현값·lineage 누락 | `SELF_ASSESSMENT_INCOMPLETE` | package 수리 후 동일 checkpoint 재평가; 새 reward 학습 금지 |

## 7. 단일변수 후속 실험 규칙

1. 기본값 다섯 값을 기준선으로 둔다.
2. Pilot 변경 네 개 중 최대 감점 G와 직접 연결된 것 하나만 추가한다.
3. 1,000 iter에서 Default-01·Pilot-01과 같은 evaluator로 비교한다.
4. primary G 개선, 나머지 G 비열등, 영상 무회귀일 때만 다음 변경을 누적하거나 3k~5k로 확장한다.
5. 독립 학습 seed 없이 나온 승자는 `exploratory`다.
6. 5k 초과는 독립 seed 재검증과 회수 package 사전등록 후에만 승인한다.

## 8. 필수 산출물

### 8-a. Default-01 학습 bundle

- run ID, 시작·종료 시각, `TRAIN_RC`, seed, num_envs, iterations
- reward/source/agent/env SHA와 reward-only diff
- checkpoint, tfevents, train log, params
- 학습 종료 시점의 `model_best.pt`·`env.yaml`

### 8-b. 정책별 평가 bundle

- 정책당 69개 case telemetry/summary/log 또는 명시적 실패 상태
- canonical 영상과 worst-case replay, model SHA sidecar
- `SELF_EVAL_REPORT.json/md`, `VIDEO_STATUS.tsv`, `RUNNER_STATUS.txt`
- exact model/env/registry/source SHA, exported `policy.pt`, actor tensor 비교 결과
- 내부 `SHA256SUMS.txt`, 외부 tar SHA

### 8-c. 비교 보고서

- seed·scenario별 raw metric
- Default-01 대비 Pilot-01 delta와 허용오차 판정
- `영상 / 내부 정량 / 공식 결과` 분리 표
- 선택된 분기와 다음 단일변수 사전등록

## 9. 완료·중단 기준

### 완료

1. Default-01이 reward-only diff와 고정 학습 조건으로 생성·회수·검증됨.
2. 두 정책 모두 동일 evaluator에서 필수 case와 영상이 검증됨.
3. 비교 보고서가 §6의 정확히 한 분기를 선택하거나 `INCONCLUSIVE` 이유를 특정함.
4. 다음 실험은 기본값에서 한 변수만 바꾸도록 사전등록됨.

### 즉시 중단

- reward 외 source/config drift 발견
- Pilot/Default model·env·policy lineage 불일치
- 평가 case 또는 실현값 누락
- bundle SHA/manifest 실패
- 서버 TTL 안에 필수 영상·telemetry 회수가 불가능해진 경우

중단은 성능 FAIL이 아니라 증거 미완료다. 복구 가능한 checkpoint·source·config·실패 로그를 먼저 회수한다.

## 10. 살아있는 PRD 운영 계약

이 PRD는 최초 계획을 보관하는 정적 문서가 아니라 **Go2 기획자가 매 기획·실험·판정에서 계속
참조하고 갱신하는 실행 정본**이다.

### 10-a. 갱신 책임

| 역할 | 책임 범위 |
|---|---|
| `go2-campaign-manager` | 목표·범위·Upgrade/Restart 분기·완료/중단 기준·일정 영향 |
| `go2-test-planner` | 실험 대상·통제 변수·metric·허용오차·산출물·단일변수 후속 규칙 |
| `go2-report-writer` | 실제 결과와 PRD 불일치를 명시하고 planner가 반영할 정정안을 handoff |
| `go2-evaluation-auditor` | PRD 판정식·case·seed·증거 계층 준수 여부를 read-only 감사 |

### 10-b. 의무 갱신 시점

다음 사건이 발생한 **같은 턴**에 PRD와 관련 원장을 함께 갱신한다.

1. 사용자 결정이 목표·범위·순서·예산·판정 기준을 바꿈.
2. package 구현으로 case 수·metric·경로·실행시간·회수물이 확정 또는 변경됨.
3. Default-01/Pilot-01 artifact나 평가 결과가 도착함.
4. `INTERNAL_GATE_FAIL|INCONCLUSIVE`, 영상 반증, source/config drift가 발견됨.
5. 다음 단일변수·seed·iteration 승급 또는 중단 분기가 선택됨.
6. 공식 공지·제출 계약·외부 evaluator 정보가 새로 확인됨.

### 10-c. 동기화 대상과 불변식

- 결정·현재 위치: `GO2_PROJECT_STATE.md`
- 일정·단계·사용자 결정: `GO2_CAMPAIGN_SCHEDULE.md`
- reward 상태·근거: `GO2_REWARD_EVIDENCE_MASTER.md`
- 실행 이력·회수 상태: `ARTIFACT_MANAGEMENT.md`, `reports/experiment_history.csv`
- 상세 작업 순서: `.omx/plans/go2-default-baseline-experiment-plan.md`
- 다음 세션 요약: `reports/PLANNER_BRIEF.md`, 필요 시 `reports/NEW_SESSION_HANDOFF.md`

과거 판정은 삭제하지 않는다. 전제가 바뀌면 새 결정 ID와 변경 이유를 남기고 이전 항목을
`대체됨`으로 연결한다. 실제 artifact가 PRD보다 최신이면 artifact를 우선 판정한 뒤 같은 턴에 PRD를
수정한다. PRD와 원장이 불일치하면 새 서버 학습·승급은 `HOLD — PRD 동기화 미완료`다.

## 11. 구현 확정 — 단일 업로드·단일 실행·단일 결과 ZIP (260901)

사용자의 서버 역할을 `ZIP 업로드 → 한 줄 실행 → 결과 ZIP 다운로드`로 제한하기 위해 P1 evaluator와 P2 Default
training package를 하나의 실행 package로 통합한다. 이 구현 변경은 실험 설계·69 telemetry·두 정책 비교 범위를
바꾸지 않고 전달·회수 단계를 단순화한다.

| 항목 | 확정값 |
|---|---|
| 로컬 실행 ZIP | `workspace/training/quadruped/go2_default_vs_pilot_v1.zip` |
| ZIP SHA256 | `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356` |
| 서버 업로드 위치 | `/workspace/go2_default_vs_pilot_v1.zip` |
| 실행 | `cd /workspace && unzip -oq go2_default_vs_pilot_v1.zip && cd /workspace/go2_default_vs_pilot_v1 && bash server_run_go2_default_vs_pilot_v1.sh` |
| Default 학습 | 배포 기본 reward, from-scratch, seed 42, 4096 env, 1,000 iter |
| 정량 평가 | 정책별 69 telemetry, 평가 seed 101/202/303 |
| 영상 | 정책별 시나리오 worst-case 7개; 회수 시 `VIDEO_UNKNOWN` |
| 단일 결과 ZIP | `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip` |
| SHA companion | `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip.sha256` |
| 완료 표식 | `[DONE] GO2_DEFAULT_VS_PILOT_RESULT_READY` |
| 예상 벽시계 | 1.5~3시간 사전 추정; 첫 서버 실행으로 보정 |
| 부분 복구 | 동일 서버에서 `GO2_RESUME=1`; fingerprint가 맞는 telemetry·영상만 재사용 |

결과 ZIP은 Default checkpoint·env·tfevents·source, 두 정책의 `policy.pt`·actor tensor lineage,
69 telemetry·보고서·영상·명령 로그·내부 manifest를 포함한다. `PARTIAL` ZIP은 복구 자료이며 평가 완료가 아니다.
결과 ZIP이 로컬에서 SHA·CRC·manifest·69×2 telemetry·7×2 영상을 검증하기 전 서버 종료 판정은 금지한다.

관련 결정: `G-D09`~`G-D13`. 구현 작업: `G-A002`, `G-A004`, `G-A005`.

## 12. 병렬 처리 근거와 한계 — 260901 정정

- `num_envs=4096`은 강좌 13·14강의 Go2 공식 예제 명령과 일치하고 Pilot-01 비교 조건을 보존한다.
- 이 값은 할당 서버에서 1024/2048/4096/8192 env를 비교하거나 GPU 사용률·VRAM·iteration/s를 계측해 찾은 최대 처리량 값이 아니다.
- 과거 회수 로그에서 확인된 서버 자원은 GPU 1개 `NVIDIA GeForce RTX 5080`, 메모리 `16303 MB`다. 현재 세션 자원은 결과 bundle의 `meta/gpu.csv`가 회수되기 전까지 동일하다고 확정하지 않는다.
- 현 runner는 Default 학습의 4096 env만 단일 프로세스에서 벡터 병렬화한다. Default/Pilot 평가, 3개 seed, 69개 case, 14개 영상은 순차 실행하며 `CUDA_VISIBLE_DEVICES` 기반 다중 GPU 분배가 없다.
- 따라서 이번 package의 목표는 **공식 예제값 준수 + Pilot 대비 실험 통제 + 단일 GPU 안정 회수**다. **서버 최대 병렬 처리**는 별도 자원 계측·smoke benchmark를 통과하기 전 주장하지 않는다.

관련 사실: `G-F13`~`G-F15`. 이 정정은 실험 조건을 변경하지 않으며, 결과 회수 후 성능 최적화 계획의 입력으로 사용한다.

## 13. 첫 실행 부분 결과와 복구 계약 — 260901

### 13-a. 관측 결과

- `RESULT_STATE=PARTIAL`, `RUNNER_RC=1`.
- Default-01 학습 artifact와 Default telemetry 69/69는 보존됐다.
- Pilot telemetry 0/69, Default/Pilot 영상 0/14, paired report 및 FULL ZIP은 미확보다.
- 이 상태는 `ARTIFACT_VERIFIED` 완료나 성능 판정이 아니라 `RECEIVED_PARTIAL`이다.

### 13-b. 원인과 수정

1. Pilot 평가 진입 시 Pilot `exported/`를 삭제한 뒤 같은 위치의 checkpoint를 복사하려 한 순서 오류를 수정했다.
2. Pilot model/env를 `$KEEP/training/`에 먼저 staging한 뒤 평가·영상 단계가 `exported/`를 재생성하도록 변경했다.
3. 결과 packaging의 bare `python3`를 `/workspace/IsaacLab/isaaclab.sh -p`로 변경했다.
4. 같은 회귀를 막는 contract test를 추가했다.

### 13-c. 실행 artifact

| 용도 | 파일 | SHA-256 | 상태 |
|---|---|---|---|
| 현재 살아 있는 서버 복구 | `go2_default_vs_pilot_v1_hotfix.zip` | `b2fa2d57aee9ab55ea9765171d8230c8aeac8c38bbe46285548c864b4eee2d39` | `ARTIFACT_VERIFIED` |
| 새 서버 전체 실행 | `go2_default_vs_pilot_v1.zip` | `db239f77fe3336209ecb8d4f38478c1fc1dd605fbf5c0351e95a9ba1b7e74cfd` | `ARTIFACT_VERIFIED` |
| 최초 package | 격리된 `go2_default_vs_pilot_v1_buggy.zip` | `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356` | `BUGGY_DO_NOT_REUSE` |

현재 서버에서는 hotfix를 덮어쓴 뒤 `GO2_RESUME=1`로 실행한다. Default 학습을 다시 하지 않고 fingerprint가 일치하는 Default telemetry를 건너뛴다. FULL ZIP·SHA가 로컬에서 검증될 때까지 서버 종료 게이트는 닫혀 있다.

## 14. FULL 회수 결과와 다음 게이트 — 260901

- FULL result ZIP 외부 SHA 일치, `RESULT_STATE=FULL`, `RUNNER_RC=0`.
- Default/Pilot telemetry 69/69씩과 worst-case 영상 7개씩을 회수했다.
- package 무결성은 `ARTIFACT_VERIFIED`; 영상 내용은 아직 `VIDEO_UNKNOWN`이다.
- 내부 simulation proxy는 Default `17.90699/70`, Pilot `41.97990/70`이다. Pilot은 Default 대비 약 `+24.07/70` 개선됐으나 둘 다 `INTERNAL_GATE_FAIL`이다.
- 현재 의사결정은 `SHARED_WEAKNESS_FOUND`: 배포 기본값으로 전면 회귀하지 않고 Pilot을 비교 기준으로 보존하되, 영상 관찰과 시나리오별 약점 분석 전 추가 학습은 승인하지 않는다.
- 서버 종료 게이트는 열렸다. 다음 로컬 게이트는 `14개 영상 관찰 → G1~G7 시나리오별 비교 → 최대 감점 축 단일변수 후보 사전등록`이다.

## 15. 예상 대비 실제 분석과 최종 분기 — 260901

- artifact 로그가 덮는 최초 학습 시작~FULL 완료 창은 약 2시간 8분으로 예상 1.5~3시간 안이었다. 그러나 서버 생성~종료 전체 과금 시간은 `[미측정]`이고, 최초 runner 오류가 불필요한 진단·재개 시간을 추가했다.
- 사전 최소 개선폭 `+0.03` 대비 실제 Pilot delta는 `+0.34390`이고, 평가 seed 101·202·303 모두 Pilot 방향이었다.
- Pilot은 G1·G2·G6을 내부 기준까지 개선했지만 G3·G4·G5·G7이 실패했다. G3·G4·G5 survival은 사전 비열등 허용치 `-0.02`를 위반했다.
- 14개 worst-case 영상의 12-frame 직접 관찰을 완료해 `VIDEO_OBSERVED`로 갱신했다. Pilot의 평지 이동·push 회복 개선과 rough/stairs 불안정이 정량과 일치한다.
- §6의 최종 분기는 `SHARED_WEAKNESS_FOUND`다. Pilot을 폐기하거나 resume하지 않고 **성능 비교 상한으로 보존**, 후속 인과 실험은 **Default 계보에서 한 항씩** 시작한다.
- 최대 감점 G5와 약한 tracking/completion에 따라 첫 screening 후보는 Default의 `feet_air_time .01→.2` 단일 변경 1,000 iter다. 실행 전 별도 사전등록·package 검증이 필요하다.
- 상세 분석 보고서: `GO2_DEFAULT_VS_PILOT_ANALYSIS_260901.md`.

## 16. 후속 단일변수 실행 확정 — G-A007 (260901)

§15의 최종 분기에 따라 `feet_air_time 0.01→0.20`만 변경한 1,000-iter screening을 별도 PRD로 사전등록하고 실행 package를 로컬 검증했다.

| 항목 | 확정값 |
|---|---|
| 상세 PRD | `GO2_FEET_AIR_TIME_020_SCREENING_PRD.md` |
| 기준 policy | Default-01 iter 800, model SHA `99ceeaa1…4676` |
| 변경 | `feet_air_time 0.01→0.20` only |
| 유지 | `track_lin=1.0`, `lin_vel_z=-3.0`, `ang_vel_xy=-0.08`, `action_rate=-0.01` |
| 학습 | from-scratch, seed 42, 4096 env, 1,000 iter |
| 평가 | candidate G1~G7 69 telemetry, seeds 101/202/303 |
| 영상 | candidate 시나리오별 worst case 7개, 500 steps |
| 로컬 ZIP | `workspace/training/quadruped/go2_feet_air_time_020_v1.zip` |
| ZIP SHA256 | `36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f` |
| 서버 결과 | `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` 및 `.sha256` |
| 완료 표식 | `[DONE] GO2_FEET_AIR_TIME_020_RESULT_READY` |
| 예상 실행 창 | 이전 artifact 실측 기반 1시간 35분~2시간 |

Default-01을 다시 학습·평가하지 않고 G-A006에서 검증한 Default self-eval report를 고정 입력으로 사용한다. 이는 같은 registry·evaluator 결과를 재사용해 서버 시간을 줄이는 것으로, candidate는 동일 69-case 규격으로 새로 측정한다.

정량 승급은 G5 proxy `+0.03`, G5 survival delta `≥-0.02`, 전 G survival `≥-0.02`, 전 G tracking `≥-0.05`, 평가 seed delta `≥-0.02`를 모두 요구한다. 정량 충족 뒤에도 7영상은 `VIDEO_UNKNOWN`이므로 직접 관찰 전에는 승급하지 않는다. 실행 결과는 아직 `[미측정]`이다.

## 17. G-A007·G-A009 결과로 인한 분기 갱신 — 260902

- G-A007 `feet_air_time=0.20`은 G1을 개선하지 못했고 보정된 G5 진행도도 Default보다 악화해 `INTERNAL_SCREEN_FAIL`로 폐기했다.
- G-A009 `track_lin_vel_xy_exp=1.20`은 총 proxy가 `+3.09/70` 증가했지만 77.99%가 G6 기여였고 목표 G1 delta는 음수였다. G1 영상도 시작 격자 부근 정체를 보여 `INTERNAL_EARLY_KILL_FAIL`로 폐기했다.
- 따라서 Pilot-01의 남은 미분리 항 중 `lin_vel_z_l2 -3.0→-2.0`을 G-A010 단일변수로 선택했다. 이 선택은 최적값 주장이 아니라 정보가치 순서다.

## 18. G-A010 고정 engine·JSON 계약 — 260902

| 항목 | 확정값 |
|---|---|
| engine | `workspace/training/quadruped/go2_tuning_engine_v1_1.zip` |
| engine SHA | `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd` |
| experiment | `workspace/training/quadruped/G_A010_lin_vel_z_m2.json` |
| experiment SHA | `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9` |
| 단일 변경 | `lin_vel_z_l2 -3.0→-2.0` |
| 학습 | from-scratch, seed 42, 4096 env, 1,000 iter |
| 조기평가 | G1~G7 대표 7 case, G1 `+0.05`, survival 회귀 `≤0.10` |
| 영상 | G1 forward-fast seed 101, 4 env, 500 step, 1개 |
| 결과 | `/workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip` 및 `.sha256` |

engine ZIP에는 실험값을 넣지 않고 별도 JSON을 검증해 runtime source를 만든다. reward 값만 바뀌는
G-A011에서는 engine SHA를 유지하고 JSON만 새로 검증한다. 현재는 upload package만
`ARTIFACT_VERIFIED`이며 G-A010 성능·영상·공식 결과는 `[미측정]` / `VIDEO_UNKNOWN` /
`OFFICIAL_RESULT_UNMEASURED`다.
