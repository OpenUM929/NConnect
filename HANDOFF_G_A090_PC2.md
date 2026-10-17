<!-- PC2_HANDOFF
WORK_ID: G-A090
STATUS: READY
START_AFTER: NONE
START_MARKER: NONE
PACKAGE: workspace/training/quadruped/upload/G-A090/current/GO2_G_A090_TRACK_ANG_P0P85_v1.zip
PACKAGE_SHA256: 045554b8cdad0de0d34751da4a53086ba3638c8c73a916fc5307fc8a63e7c5cc
-->

# G-A090 — PC2 G-A083 위 track_ang_vel_z_exp 0.85 단독 (3000 iter)

## 0. 한눈에

- **목적:** 회전 추종 보상을 0.1 간격으로 교정하는 첫 점이다. G-A083의 추종 손실 11.59 중 회전 몫이 4.67(40%)이고, 이 계열에서 0.3→0.75로 올렸을 때 점수가 55.29→56.85로 올랐다.
- **사용자 결정 (2026-10-17):** "0.1씩만 변화를 줘서 튜닝 데이터를 만들고, 1차 테스트 결과를 보고 악화되면 다음 테스트를 이어서 진행하자." 악화이면 다음 점은 0.65다(별도 인계 문서로 낸다).
- **기준:** `G_A083_PC2_VERIFIED`
  - PC2 G-A083 iter 2400 model SHA `bbbc04f4624f6c1401f20b7937a3f8ed82427a288b0158525efb48091e07b27a`
  - env SHA `8bf58925f6de58206967d12d556d1e0cf4de76de5218195a14e5f3e25011e513`
- **바꾸는 값:** `track_ang_vel_z_exp` 0.75 → **0.85** (하나만)
- **고정하는 값:** track_lin_vel_xy_exp 2.0, feet_air_time 0.01, lin_vel_z_l2 −3, ang_vel_xy_l2 −0.05, action_rate_l2 −0.01, flat_orientation_l2 −0.225
- **학습 조건:** 처음부터 3000 iter, seed 42, 4096 env.
- **평가:** iter 2400 checkpoint로 69 case를 돈다. 영상은 seed 101로 10편이다.
- **대조군:** G-A083 저장 평가(69 case)와 영상 10편을 그대로 쓴다. 러너 라벨은 `REUSED_G_A083_PC2_FULL_NO_RERUN`이다.
- **실행 방식:** G-A086~G-A089와 같은 러너 체인이다(`run_all.sh` → `run_point.sh --inner`). tmux가 필요 없다.
- **시작 조건:** 바로(G-A089는 원장에 DONE).
- **예상 시간 [추정]:** 약 4시간 45분.
- **패키지:** parts 3개, SHA `045554b8cdad0de0d34751da4a53086ba3638c8c73a916fc5307fc8a63e7c5cc`

## 1. 준비 확인

1. parts `.001`~`.003`을 순서대로 이어 `/workspace/GO2_G_A090_TRACK_ANG_P0P85_v1.zip`으로 만든다. 원본 ZIP은 git에 올리지 않는다.
2. 이어 붙인 ZIP의 SHA256이 `045554b8cdad0de0d34751da4a53086ba3638c8c73a916fc5307fc8a63e7c5cc`인지 확인한다.
3. 디스크 여유 공간, Isaac Lab venv, GPU, Go2 USD asset을 확인한다. USD preflight가 실패하면 학습을 시작하지 않는다.
4. 다른 train.py·play.py 프로세스가 없는지 확인한다. seed를 바꾸거나 기존 학습을 이어서 실행하지 않는다.
5. 러너가 시작 전에 두 가지를 검사한다. 실패하면 rc 23으로 멈춘다.
   - 패키지 identity/registry/evaluator SHA
   - G-A083 저장 대조군 identity
6. G-A085(`FAILED rc22`)는 다시 실행하지 않는다. 이 작업과 무관하다.

## 2. 실행

### 한 줄

```bash
cd /workspace && unzip -oq GO2_G_A090_TRACK_ANG_P0P85_v1.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/go2_g_a090_track_ang_p0p85/run_all.sh
```

- parts 결합과 SHA 검증은 실행 전에 끝낸다.
- **진행 기록:** `tools/watch_go2_pc2_progress.ps1 -Publish`로 확인한다. 다음 항목을 따로 기록한다.
  - 학습: iter/3000
  - candidate: case/69, 영상/10
  - baseline: case/69, 영상/10
- **중지:** 해당 작업 상태 폴더에 `STOP` 파일만 만든다. 실행 중인 train.py·play.py를 직접 kill하지 않는다.
- **결과 폴더:** `/workspace/_keep/go2_g_a090_track_ang_p0p85/`
- **영상 10편 (seed 101):** G2 combined_yaw 좌/우, G3 rough forward/lateral, G5 stairs 10/15 down, G6 push ±x/±y
- **보상 확인:** 러너가 학습된 env.yaml의 보상값 7개를 `expected_rewards.json`과 대조한다. 다르면 rc 3으로 멈춘다(`ENV_REWARD_CHECK.txt`). 실행 기록의 `SINGLE_CHANGE` 줄은 `track_ang_vel_z_exp:0.75->0.85`이다.

### 사전등록 판정 항목 (판독은 작성 PC가 한다)

- **primary (계획서 `GO2_G_A087_A088_PLAN_20261016.md` §5 기준, 목표 58.0):** 신버전 점수(`tools/go2_weakness_breakdown.py`)를 G-A083 57.59와 비교한다.
  - **후보 검토:** ≥58.0, 보호 7축 유지, xy 오차·지형 속도가 G-A083보다 나쁘지 않음
  - **개선 신호:** 57.59 초과 58.0 미만, 방향 지표(회전 손실·xy 오차·지형 속도·밀침 넘어짐)가 같은 쪽
  - **악화:** 57.59 미만(차이 크기 기록). 악화이면 0.65를 이어서 시험한다(사용자 결정).
- **secondary (보고 후 판독):**
  - 추종 손실의 회전 몫 (G-A083 4.67 / 11.59)
  - 밀침 넘어짐: G6 12행 `fallen_envs` 합 (G-A083 4). G-A082에서 0.75로 올렸을 때 밀린 뒤 미끄러짐이 늘었다.
  - 15cm 계단 생존: G-A082에서 0.979/0.958 → 0.906/0.844로 떨어졌다.
  - 넘어짐 합, 주저앉음/기울어 넘어짐 수 (`tools/go2_g_a086_fall_cause.py` `case_rows`, G-A083 26/10)
  - 탐색 std (G-A082에서 iter 2000 뒤 1.03~1.08)
- **protection (G-A083 기준값):**
  - stairs_10_down·stairs_15_down full proxy 합 각각 ≥85 (G-A083 96, 95)
  - 15cm 계단 생존 평균 ≥0.92 (G-A083 0.974)
  - 머리 방향 변화 중앙값 slope_plus_20 / stairs_10_down / stairs_15_down 각각 ≤40°
  - G3 생존 합 ≥5.75
  - G3·G4·G5 명령 방향 속도 평균 ≥0.425 m/s (G-A083 0.470)
  - G2 combined_yaw 6행 survival=1.0
  - 탐색 std(iter 2380~2420) ≤0.98 (G-A083 0.798)
- 점수는 내부 proxy다. 공식 결과로 부르지 않는다. 신버전과 과거 버전을 함께 보고한다.

## 3. 실패 처리

| rc | 의미 | 처리 |
|---|---|---|
| 20 / 21 / 22 | 디스크 부족, 중복 프로세스, Isaac/GPU 사전 차단 | 현재 로그·상태를 보존하고 재시작하지 않는다. |
| 23 | identity/evaluator/registry, 기준 model/env SHA, 기준 69 case·영상 검사 실패 | 학습·평가를 시작하지 않는다. 로그와 `RUNNER_STATUS.txt`만 회수한다. |
| 25 | Go2 USD asset 또는 패키지 preflight 실패 | 실행을 중단하고 asset/preflight 로그를 회수한다. |
| 3 | TRAIN_RC 비정상, 또는 env.yaml 보상값 불일치 | iter 2400 checkpoint가 있으면 partial artifact, `TRAIN_STATUS.txt`, `ENV_REWARD_CHECK.txt`, logs, env.yaml, pinned checkpoint를 보존한다. seed 변경이나 자동 재학습은 하지 않는다. |
| 30~34 | telemetry·영상·결과 패키징 실패 | 결과 폴더, 실패 로그, checkpoint/source/config를 그대로 보존하고 해당 rc를 보고한다. |
| 9 | 중단된 학습을 보호하려고 resume을 거부함 | `interrupted_*` 보존물을 회수하고 재실행하지 않는다. |

- **iter 2400 이후 발산:** pinned checkpoint로 평가한 뒤 판정한다. 발산만으로 값을 기각하지 않는다.
- **iter 2400 이전 발산:** `DIVERGED_BEFORE_PIN`으로 기록한다. seed 변경이나 자동 후속 실행은 하지 않는다.
- **PC2가 하지 않는 일:** 보상 효과 판독, 보호 기준 채택, 후보 승급.

## 4. 회수

- **결과 폴더:** `/workspace/_keep/go2_g_a090_track_ang_p0p85/`
- **결과 ZIP:** `/workspace/_keep/GO2_G_A090_TRACK_ANG_P0P85_RESULT.zip`과 `.sha256`
- **반드시 회수할 항목:**
  - candidate model/env, pinned iter-2400 checkpoint
  - training logs/tfevents, `candidate_source.sha256`, `ENV_REWARD_CHECK.txt`
  - `exported/report.html`과 그 SHA/status
  - evaluation 69 case identity/manifest, 영상 10편과 각 identity
  - `RUNNER_STATUS.txt`, `TRAIN_STATUS.txt`, `CHECKPOINT_PIN.txt`
- **100MB 초과 시:** 결과 ZIP을 95MiB parts로 나누고 원본 SHA를 보존한다.
- **작성 PC의 회수:** `bash tools/keep_fetch_result.sh <archive>.zip`로 회수, SHA 대조, 압축 해제, 용량 정리를 한 번에 한다.
- **PC2의 보고 범위:** 결과를 판독하지 않는다. 실행 시작, 종료, rc, SHA, 진행량, 회수 경로만 보고한다.

## 5. 보고

PC2 보고에는 다음만 넣는다.

- 시작 시각, 종료 시각, 실행 명령, WORK_ID/RUN_ID
- 최종 rc와 `TRAIN_STATUS.txt`의 iter/seed/env 수
- `ENV_REWARD_CHECK.txt` 결과 줄(`ENV_REWARDS_OK`인지)
- pinned iter 2400 checkpoint가 있는지와 그 SHA
- candidate model/env/source/report/result ZIP의 SHA
- 수량
  - candidate: telemetry case 수, 영상 수
  - G-A083 재사용 baseline: case 수, 영상 수
- 실패했다면 rc와 보존한 경로

성능 해석은 작성 PC가 한다. 증거는 `ARTIFACT_VERIFIED`, `VIDEO_OBSERVED/VIDEO_UNKNOWN`, `INTERNAL_GATE_*`로 나눠 판정한다. PC2 실행 결과만으로 예선 점수나 공식 결과를 보고하지 않는다.
