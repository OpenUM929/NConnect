# Go2 New Session Handoff

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 proxy 70점 축의 G3·G4·G5·G7 약점을 줄이고, 설계 의도 20점·리포트 10점에 쓸 단일변수 근거를 만든다.
- [현재 단계] 단계 3/6 — 환경 적응 게이트.
- [확보] Default-01 `17.90699/70`, Pilot-01 `41.97990/70`, 정책별 telemetry 69건·영상 7개, `VIDEO_OBSERVED`, 분기 `SHARED_WEAKNESS_FOUND`.
- [미확보] G-A007 candidate 결과, `feet_air_time` 단독 인과, G3·G4·G5·G7 내부 통과, 독립 학습 seed, `OFFICIAL_RESULT`.
- [이번 테스트] Default 계보에서 `feet_air_time 0.01→0.20`만 바꾼 1,000-iter candidate를 G1~G7 69-case·7영상으로 판정한다.
- [흐름] 쌍대평가 완료 → package 검증 완료 → **G-A007 서버 실행·회수** → 영상·정량 판정 → 통과 시 독립 seed → 최종 제출.
- [지금 할 일] 사용자가 `go2_feet_air_time_020_v1.zip`을 서버 `/workspace/`에 업로드하고 §4의 한 줄을 실행한다.
- [보장하지 않음] 단일 학습 seed·내부 proxy·영상은 공식 점수나 예선 통과를 보장하지 않는다.

## 1. 새 세션 read order

1. 루트 `AGENTS.md`
2. `workspace/training/quadruped/AGENTS.md`
3. `ARTIFACT_MANAGEMENT.md` — `G-A007`
4. `GO2_PROJECT_STATE.md` — §10, G-D23~G-D26
5. `GO2_CAMPAIGN_SCHEDULE.md` — §9
6. `GO2_REWARD_EVIDENCE_MASTER.md` — §9
7. `workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md` — §16
8. `workspace/training/quadruped/reports/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md`
9. `workspace/training/quadruped/config/go2_self_eval_registry.json`

## 2. frozen inputs

```text
WORK_ID=G-A007
RUN_ID=train_260901-Go2_feet_air_time_020_1000
BASELINE=Default-01
BASELINE_CHECKPOINT_ITER=800
BASELINE_MODEL_SHA=99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676
BASELINE_ENV_SHA=4d1d294b63dafeceb223fb48226cbe6a533157bc54f97ce486f644bd1bda262c
BASELINE_RESULT_SHA=af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b
SINGLE_CHANGE=feet_air_time:0.01->0.20
TRAIN_SEED=42
NUM_ENVS=4096
MAX_ITERATIONS=1000
EVAL_SEEDS=101,202,303
```

## 3. 절대 금지

- `server_run_Go2_videos.sh` 실행·재사용: `LEGACY_INVALID_MAPPING`.
- Pilot-01 resume 또는 Pilot 네 변경을 한꺼번에 적용.
- G-A007 결과 전 다른 reward·3k 이상 학습 시작.
- `Train/mean_reward`로 Default와 candidate 성능 비교.
- 정량 gate만으로 영상 판정이나 공식 결과를 승격.
- 결과 ZIP·SHA 로컬 검증 전 서버 종료.

## 4. 구현 완료·사용자 실행

로컬 실행 ZIP:

```text
C:\dev\Nconnect\workspace\training\quadruped\go2_feet_air_time_020_v1.zip
SHA256 36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f
```

서버 업로드 위치: `/workspace/go2_feet_air_time_020_v1.zip`

한 줄 실행:

```text
cd /workspace && unzip -oq go2_feet_air_time_020_v1.zip && cd /workspace/go2_feet_air_time_020_v1 && bash server_run_go2_feet_air_time_020_v1.sh
```

진행 확인: `tmux attach -t go2_feet_air_time_020_v1`

완료 표식: `[DONE] GO2_FEET_AIR_TIME_020_RESULT_READY`

필수 결과 ZIP: `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip`

SHA companion: `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip.sha256`

예상 실행 창: 이전 artifact 실측 기반 약 1시간 35분~2시간. 전체 서버 과금 시간은 보장하지 않는다.

## 5. package verification

- package SHA: `36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f`
- 21 members, ZIP CRC·safe paths OK.
- 내부 manifest 94/94 OK.
- reward diff: `feet_air_time` 한 줄만 변경.
- frozen Default report: 69/69, model/env identity 일치.
- Python compile·contract tests 5/5.
- runner CRLF 0, Git Bash `bash -n` OK.
- 상세: `workspace/training/quadruped/go2_feet_air_time_020_v1.VERIFICATION.md`.

## 6. 결과 회수 직후 순서

1. 사용자 제공 파일을 `workspace/_keep/`에서 확인한다.
2. `workspace/server_returns/go2_feet_air_time_020_v1_<date>/original/`에 격리한다.
3. 외부 SHA·CRC·안전 경로·내부 manifest·`RUNNER_RC`를 검증한다.
4. telemetry 69, 영상 7, model/env/policy/lineage/source/log를 확인한다.
5. 영상 7개를 직접 관찰해 `VIDEO_OBSERVED` 또는 판독 한계를 기록한다.
6. 사전 gate로 `승급 후보 / INTERNAL_SCREEN_FAIL / INTERNAL_GATE_INCONCLUSIVE` 중 하나를 결정한다.
7. PRD·reward master·일정·상태·artifact 원장을 같은 턴에 갱신한다.

## 7. 서버 종료 게이트

다음이 모두 로컬에서 확인되기 전 서버 종료 불가:

- 결과 ZIP과 SHA companion 도착·일치
- `RESULT_STATE=FULL`, `RUNNER_RC=0`
- candidate telemetry 69/69
- candidate 영상 7/7
- `policy.pt`와 `POLICY_LINEAGE.json`
- 재현 가능한 model/env/source/config/log

PARTIAL ZIP은 복구 artifact이며 평가 완료가 아니다. 실패 시 같은 서버에서 `GO2_RESUME=1`을 사용할 수 있지만, 먼저 PARTIAL 원인과 보존 checkpoint를 확인한다.

## 8. ?? handoff ? G-A008 root fix

### ?? ??

- G-A007 training? ????? telemetry 8/69 ? Isaac Sim startup segmentation fault? PARTIAL ????.
- v1 telemetry? `env.step()` ??? hard process exit? ??? upstream `env.close()`? `simulation_app.close()`? ????.
- v1 runner? ? case failure? ??? ?? ?? ????.

### ?? ??

- v1 runner: `BUGGY_DO_NOT_REUSE`.
- v2: graceful stop + case/video ?? 3? retry + ?? fingerprint ??? + stable launcher snapshot.
- package: `C:\dev\Nconnect\workspace\training\quadruped\go2_feet_air_time_020_v2.zip`
- SHA: `73c6ba1f9cc29b22889d146e4c949ff54b7a9e2b4638199f61c9961dc9f88dbc`
- ??: deterministic build, CRC, manifest 94/94, compile, contract 6/6, AST hard-exit 0, Git Bash `bash -n`.

### ?? ??

- ?? v1 ????? v2? ??? ???? ???.
- ?? ?? ?? ??? ??? ?? ??? `[???]`??.
- v2? `GO2_RESUME=1`? ?? training? ?? case? ????? ????? ???.
- ?? Isaac Sim graceful close? ?? ???? ???? ??? ?? ??? `INTERNAL_GATE_INCONCLUSIVE`?.


## 260902 비용 게이트·69-case 출처 정정

- 69-case는 강좌 직접 요구가 아니다. 강좌·제공 가이드는 G1~G7 범주·지형·가중치를 제공했고, 명령 격자·seed 101/202/303·69건 합계는 내부 설계다.
- H1·Go2 공통 실행 순서는 `6~8건 조기중단 → 21건 대표평가 → proxy ≥60/70 + 전 시나리오 안정성 충족 시 기체별 전체평가`다.
- 전체 평가는 H1 30-case, Go2 69-case로 서로 다르며 case grid를 복사하지 않는다.
- G-A007은 `INTERNAL_SCREEN_FAIL`; G5 진행도와 G7 DR evaluator 수리 전 새 서버 실행은 `HOLD`다.

## 260902 G-A009 실행 handoff

- 다음 값: `track_lin_vel_xy_exp=1.20` only; `feet_air_time=0.01`, `lin_vel_z_l2=-3.0`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01` 고정.
- package: `C:\dev\Nconnect\workspace\training\quadruped\go2_track_lin_vel_120_v1.zip`.
- SHA: `8d341d5dbae5aac6c6a4376442f2cdf20264fa2439d3b22c68e64811a81aefa7`.
- 서버 업로드: `/workspace/go2_track_lin_vel_120_v1.zip`.
- 한 줄 실행: `cd /workspace && unzip -oq go2_track_lin_vel_120_v1.zip && cd /workspace/go2_track_lin_vel_120_v1 && bash server_run_go2_track_lin_vel_120_v1.sh`.
- 완료 표식: `[DONE] GO2_TRACK_LIN_VEL_120_RESULT_READY`.
- 다운로드: `/workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 비용 게이트: 7 candidate + 1 Default DR에서 회귀 시 자동 종료; 통과 때만 candidate 21-case. 69-case 자동 실행 없음.
- 영상: G1 forward-fast 1개 필수. 다운로드 후 로컬 검증 전 서버 종료 여부는 확정하지 않는다.
- 현재 판정: package `ARTIFACT_VERIFIED`; 외부 실행 `[미측정]`; `VIDEO_UNKNOWN`; `OFFICIAL_RESULT_UNMEASURED`.

## 260902 범용 engine 전환 결정

- G-A009 현 ZIP은 로컬 `ARTIFACT_VERIFIED`이며 그대로 실행한다. 재포장하지 않는다.
- 현 package 생성은 로컬 작업이므로 서버 GPU 시간을 소비하지 않았다.
- G-A010부터 reward 값 때문에 runner·builder·reporter를 복제하지 않는다.
- 목표 구조: versioned `go2_tuning_engine_v1.zip` + validated `experiment.json`.
- JSON 필드: work/run ID, base identity, reward overrides, seed/env/iter, tier cases, gates, video, required output paths.
- engine version은 evaluator/schema 동작 변경 때만 올리고, reward 값 변경 때는 SHA를 유지한다.
- 결과 ZIP은 engine/spec SHA와 실제 artifact를 자동 snapshot한다.

## 260902 G-A010 실행 준비 완료

- engine: `C:\dev\Nconnect\workspace\training\quadruped\go2_tuning_engine_v1.zip`.
- engine SHA: `4489bef429a38a145763b5af8c4d55081c0a10f501a9b552194f111116f98a5a`.
- experiment: `C:\dev\Nconnect\workspace\training\quadruped\config\experiments\G_A010_lin_vel_z_m2.json`.
- experiment SHA: `fa0bb3b749aa4412cb5023807cc895db08f416e626730ee34477c516bc6ec425`.
- single change: Default-01 `lin_vel_z_l2 -3.0→-2.0`; 다른 reward·seed 42·4096 env·1,000 iter 고정.
- 검증: deterministic engine SHA 2/2, CRC, manifest 33/33, extracted-engine materialization, contract 14/14, Python compile, CRLF 0, Git Bash `bash -n`.
- 서버 업로드: `/workspace/go2_tuning_engine_v1.zip`, `/workspace/G_A010_lin_vel_z_m2.json`.
- 한 줄 실행: `cd /workspace && unzip -oq go2_tuning_engine_v1.zip && cd /workspace/go2_tuning_engine_v1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.
- 완료 표식: `[DONE] GO2_LIN_VEL_Z_M2_RESULT_READY`.
- 다운로드: `/workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip` 및 `.sha256`.
- 결과 ZIP 로컬 검증 전 서버 종료 판정 금지. 외부 실행·candidate 성능·영상은 아직 `[미측정]` / `VIDEO_UNKNOWN`.
- 사용자용 정본: `workspace/training/quadruped/GO2_G_A010_RUN_GUIDE.txt`.

### server preflight hotfix

- v1.0 SHA `4489bef4…8a5a`는 bare `python3` 결함으로 `BUGGY_DO_NOT_REUSE`; 학습 시작 전 실패했다.
- v1.1 engine과 spec은 모두 `workspace/training/quadruped/`에 배치했다.
- engine: `go2_tuning_engine_v1_1.zip`, SHA `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- spec: `G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- 실행: `cd /workspace && unzip -oq go2_tuning_engine_v1_1.zip && cd /workspace/go2_tuning_engine_v1_1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.
