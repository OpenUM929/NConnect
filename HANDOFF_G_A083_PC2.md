<!-- PC2_HANDOFF
WORK_ID: G-A083
STATUS: READY
START_AFTER: NONE
START_MARKER: NONE
PACKAGE: workspace/training/quadruped/upload/G-A083/current/GO2_G_A083_ACTION_RATE_M0P01_v1.zip
PACKAGE_SHA256: 50ff9dc9058b866e5dbed9aea9c0204d8295a3b4dc69b89be9bdc701774d9110
-->

# G-A083 — PC2 G-A082 위 action_rate_l2 한 항 변경 (3000 iter)

## 0. 한눈에

- **목적:** G-A082에서 높아진 `Policy/mean_std`를 낮추고 G6 밀침 xy 오차 및 G5 15cm 계단 생존 proxy가 개선되는지 단일변수로 확인한다.
- **기준:** `G_A082_PC2_VERIFIED`, PC2 G-A082 iter 2400 model SHA `df214dc9aa1fa13acff0e13987943580c3d7d181b60dde282a463e8080bb2f04`, env SHA `862a59adb8b60ac9caa3b5f9e46df3a801bb056198c0bd36a9dfbcf1d4f6dce2`.
- **설계:** `action_rate_l2` -0.005 → -0.01만 변경한다. 나머지는 track_lin_vel_xy_exp 2.0, feet_air_time 0.01, lin_vel_z_l2 -3, ang_vel_xy_l2 -0.05, flat_orientation_l2 -0.225, track_ang_vel_z_exp 0.75로 고정한다.
- **학습 조건:** 처음부터 3000 iter, seed 42, 4096 env. 평가는 iter 2400 checkpoint로 69 case, 영상은 seed 101의 10편이다.
- **대조군:** G-A082 저장 평가 69 case와 영상 10편을 재사용한다. 대조군을 다시 학습하거나 평가하지 않는다. 러너 라벨은 `REUSED_G_A082_PC2_FULL_NO_RERUN`이다.
- **예상 시간:** G-A082와 같은 PC2 조건을 기준으로 학습 약 4~5시간, 평가·영상·패키징 약 1~2시간으로 계획한다. 실제 시간은 보장하지 않는다.
- **패키지:** 3 parts, SHA `50ff9dc9058b866e5dbed9aea9c0204d8295a3b4dc69b89be9bdc701774d9110`.

## 1. 준비 확인

1. parts를 순서대로 이어 `/workspace/GO2_G_A083_ACTION_RATE_M0P01_v1.zip`으로 만든다. 원본 ZIP은 git에 올리지 않는다.
2. 이어 붙인 ZIP의 SHA256이 `50ff9dc9058b866e5dbed9aea9c0204d8295a3b4dc69b89be9bdc701774d9110`인지 확인한다.
3. 디스크 여유 공간, Isaac Lab venv, GPU, Go2 USD asset을 확인한다. USD preflight가 실패하면 학습을 시작하지 않는다.
4. 동일 WORK_ID의 다른 train/play 프로세스가 없는지 확인한다. seed를 바꾸거나 기존 학습을 이어서 실행하지 않는다.
5. 패키지 안의 identity/registry/evaluator SHA와 G-A082 저장 대조군 identity를 러너가 사전 검사한다. 실패하면 rc 23으로 멈춘다.

## 2. 실행

### 한 줄

```bash
cd /workspace && unzip -oq GO2_G_A083_ACTION_RATE_M0P01_v1.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/go2_g_a083_action_rate_m0p01/run_all.sh
```

- 실행 전 parts 결합 및 SHA 검증을 끝낸다.
- 진행 기록은 `tools/watch_go2_pc2_progress.ps1 -Publish`로 확인한다. iter/3000, candidate case/69, 영상/10, baseline case/69·영상/10을 별도로 기록한다.
- 중지해야 할 때는 해당 작업 상태 폴더의 `STOP` 파일만 사용한다. 실행 중인 train.py/play.py를 직접 kill하지 않는다.
- 결과 폴더는 `/workspace/_keep/go2_g_a083_action_rate_m0p01/`이다.
- 영상은 G2 combined_yaw 좌/우, G3 rough forward/lateral, G5 stairs 10/15 down, G6 push ±x/±y의 10편(seed 101)이다.

### 사전등록 판정 항목

- **primary:** iter 2380~2420 `Policy/mean_std` 평균. ≤0.80이면 supported, ≥0.98이면 refuted, 그 밖은 INCONCLUSIVE. G-A082 기준은 1.03이다.
- **secondary 1:** `tools/go2_weakness_breakdown.py`의 G6 12행 `exy_mean` ≤0.065. G-A082 기준은 0.081이다.
- **secondary 2:** seed 3의 `stairs_15_up`, `stairs_15_down` 생존 proxy 평균 ≥0.92. G-A082 기준은 0.875이다.
- **protection:** slope_plus_20/stairs_10_down/stairs_15_down 머리 방향 변화 중앙값 각 ≤40°; stairs_15_down full proxy 합 ≥51; G3 생존 합 ≥5.75; G3·G4·G5 명령 방향 속도 평균 ≥0.425 m/s; G2 combined_yaw 6행 survival=1.0.
- 69 case 전체는 보고용이며 단일 거부 기준이 아니다. H1 공식 역산 수식은 내부 proxy 옆에 보고하되 공식 결과로 부르지 않는다.

## 3. 실패 처리

| rc | 의미 | 처리 |
|---|---|---|
| 20 / 21 / 22 | 디스크 부족, 중복 프로세스, Isaac/GPU 사전 차단 | 현재 로그·상태를 보존하고 재시작하지 않는다. |
| 23 | identity/evaluator/registry, 기준 model/env SHA, 기준 69 case·영상 검사 실패 | 학습·평가를 시작하지 않는다. 로그와 `RUNNER_STATUS.txt`만 회수한다. |
| 25 | Go2 USD asset 또는 패키지 preflight 실패 | 실행을 중단하고 asset/preflight 로그를 회수한다. |
| 3 | TRAIN_RC 비정상 | iter 2400 checkpoint가 있으면 partial artifact, `TRAIN_STATUS.txt`, logs, env.yaml, pinned checkpoint를 보존한다. seed 변경·자동 재학습은 하지 않는다. |
| 30~34 | telemetry·영상·결과 패키징 실패 | 결과 폴더, 실패 로그, checkpoint/source/config를 그대로 보존하고 해당 rc를 보고한다. |
| 9 | 중단된 학습을 보호하기 위해 resume 거부 | `interrupted_*` 보존물을 회수하고 재실행하지 않는다. |

- iter 2400 이후 발산은 pinned checkpoint 평가 후 판정한다. 발산만으로 action_rate 값을 기각하지 않는다.
- iter 2400 이전 발산은 `DIVERGED_BEFORE_PIN`으로 기록하며 seed 변경이나 자동 후속 값을 실행하지 않는다.
- PC2에서는 보상 효과 판독, 보호 기준 채택, G-A082 유지/후보 승급을 하지 않는다.

## 4. 회수

- 결과 폴더: `/workspace/_keep/go2_g_a083_action_rate_m0p01/`.
- 결과 ZIP: `/workspace/_keep/GO2_G_A083_ACTION_RATE_M0P01_RESULT.zip` 및 `.sha256`.
- 반드시 회수할 항목: candidate model/env, pinned iter-2400 checkpoint, training logs/tfevents, `candidate_source.sha256`, `exported/report.html`와 SHA/status, evaluation 69 case identity/manifest, 영상 10편과 각 identity, `RUNNER_STATUS.txt`, `TRAIN_STATUS.txt`, `CHECKPOINT_PIN.txt`.
- 결과 ZIP이 100MB를 넘으면 95MiB parts로 나누고 원본 SHA를 보존한다. 작성 PC는 `bash tools/keep_fetch_result.sh <archive>.zip`로 회수·SHA 대조·압축 해제·용량 정리를 한 작업으로 수행한다.
- PC2는 결과를 판독하지 않고 실행 시작, 종료, rc, SHA, 진행량과 회수 경로만 보고한다.

## 5. 보고

PC2 보고에는 다음만 포함한다.

- 시작 시각·종료 시각·실행 명령·WORK_ID/RUN_ID
- 최종 rc와 `TRAIN_STATUS.txt`의 iter/seed/env 수
- pinned iter 2400 checkpoint 존재 여부와 SHA
- candidate model/env/source/report/result ZIP SHA
- candidate telemetry case 수/영상 수와 G-A082 재사용 baseline case 수/영상 수
- 실패 시 rc와 보존된 경로

성능 해석은 작성 PC가 artifact 검증, 영상 관찰, 내부 정량을 각각 `ARTIFACT_VERIFIED`, `VIDEO_OBSERVED/VIDEO_UNKNOWN`, `INTERNAL_GATE_*`로 분리해 수행한다. PC2 실행 결과만으로 예선 점수나 공식 결과를 보고하지 않는다.

