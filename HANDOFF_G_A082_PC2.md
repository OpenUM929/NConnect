<!-- PC2_HANDOFF
WORK_ID: G-A082
STATUS: READY
START_AFTER: NONE
START_MARKER: NONE
PACKAGE: workspace/training/quadruped/upload/G-A082/current/GO2_G_A082_TRACK_ANG_VEL_Z_P0P75_v1.zip
PACKAGE_SHA256: eb65c70c92528cee7d8c83443adfd0b4d9cd9215b39b43954a280b44cac93724
-->

# G-A082 — PC2 G-A077에서 회전 추종 한 항 변경 (3000회)

## 0. 한눈에

- **목적:** 경사 오르막과 계단 내리기에서 회전 명령이 0인데도 몸이 100~150° 돌아가는 미보정 회전을 줄이는지 시험한다. 계단·험지 성능은 보존해야 한다.
- **근거:** `workspace/training/quadruped/reports/GO2_G_A077_WEAKNESS_20261014.md` §4·§5.
- **설계:** PC2 G-A077 보상에서 `track_ang_vel_z_exp`만 0.3→0.75로 바꾼다. 나머지 6항(track_lin 2.0, feet_air 0.01, lin_vel_z −3, ang_vel_xy −0.05, action_rate −0.005, flat −0.225)은 그대로다.
- **학습 조건:** 처음부터 3000 iter, seed 42, 4096 env. 평가는 iter 2400 checkpoint로 69 case를 돌리고 영상 10편을 만든다.
- **대조군:** PC2 G-A077 iter 2400(model `23c08ab15617b0001ee90d20c2682cf78041d80058bd83c1d090fdf94d756ca1`, env `825fdc698328e1d886c8c7ae9f9d0cfdcc24e818851ed2b1b6484b2b836fd88d`). 같은 PC2, 같은 seed, 같은 길이다. 패키지에 저장된 69 case와 영상 10편을 그대로 쓰고, 대조군은 다시 학습하거나 평가하지 않는다.
- **점 목록:** `track_ang_vel_z_exp_p0p75` 하나.
- **예상 시간:** G-A077 실측 기준 학습 약 4시간 36분, 평가 약 1시간 24분. 완료 시간을 보장하지는 않는다.

## 1. 준비 확인

1. `upload/G-A082/current/`의 `.zip.001`~`.003`을 번호 순으로 이어 붙여 `/workspace/GO2_G_A082_TRACK_ANG_VEL_Z_P0P75_v1.zip`을 만든다. 원본 ZIP은 git에 넣지 않는다.
2. 이어 붙인 ZIP의 `sha256sum`이 `eb65c70c92528cee7d8c83443adfd0b4d9cd9215b39b43954a280b44cac93724`일 때만 `/workspace`에 압축을 푼다.
3. 다른 `train.py`/`play.py`가 돌고 있으면 시작하지 않는다. 기존 프로세스를 끄지 않는다.
4. 기존 PC2의 IsaacLab venv와 GPU를 확인하고, 여유 공간이 20GB 이상인지 확인한다. Go2 USD 접근에 실패하면 학습 전에 종료하며, 자동으로 재시도하지 않는다.

## 2. 실행

```bash
cd /workspace && unzip -oq GO2_G_A082_TRACK_ANG_VEL_Z_P0P75_v1.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/go2_g_a082_track_ang_vel_z_p0p75/run_all.sh
```

- 기존 `run_point.sh`와 runner를 쓴다. 남은 점을 멈추려면 `touch <상태 폴더>/STOP`만 한다.
- 진행 기록은 G-A077과 같이 `tools/watch_go2_pc2_progress.ps1 -Publish`로 남긴다(iter/3000, case/69, 영상/10).

## 3. 실패 처리

| rc | 의미 | 할 일 |
|---|---|---|
| 20 / 21 / 22 | 디스크 부족, 중복 프로세스, Isaac/GPU 차단 | 기록을 보존한다. 진행 중인 프로세스는 끄지 않는다 |
| 23 / 25 | USD, identity, 패키지 사전검사 실패 | 학습이 시작됐는지 로그로 확인한다. 자동 재학습은 하지 않는다 |
| 3 이면서 `TRAIN_RC≠0` (학습 중 발산 등) | 학습 실패 | 부분 결과 ZIP을 그대로 회수한다. `training/model_iter2400.pt`(학습 중 복사된 checkpoint), `training/env.yaml`, `training/logs`(tfevents 포함)가 들어 있는지 확인해 보고한다. 재학습, seed 변경, 이어서 학습은 하지 않는다. 2400 평가는 작성 PC가 별도 평가 패키지로 낸다 |
| 30~34 | 수집·패키징 실패 | 원 로그, 부분 결과, checkpoint를 보존한다. 완료한 학습을 새 번호로 다시 실행하지 않는다 |

## 4. 회수

- 결과 폴더: `/workspace/_keep/go2_g_a082_track_ang_vel_z_p0p75/`
- 결과 ZIP: `/workspace/_keep/GO2_G_A082_TRACK_ANG_VEL_Z_P0P75_RESULT.zip`과 `.sha256`
- 포함 확인: 원 `report.html`, model/env/source/log/tfevents, 후보 69 case와 영상 10편, 대조군 증거(`evaluation/g_a077_pc2`), 상태 파일과 manifest
- 100MB가 넘는 ZIP은 95MiB parts로 나눠 등재한다. SHA·CRC·manifest를 검증한 뒤 결과와 원장을 commit/push한다.

## 5. 보고

- PC2는 시작·종료·rc·SHA·진행률만 보고한다. 판독과 다음 값 선택은 하지 않는다.
- 작성 PC는 다음을 판독한다.
  - 사전등록 예측(`runs/track_ang_vel_z_exp_p0p75/experiment.json`): 경사 오르막, 10cm·15cm 내리기의 머리 방향 변화 중앙값 108° / 106° / 156°가 절반 아래로 내려가는지
  - 보호 축: 계단 완주, G3 생존, 지형 위 명령 방향 속도, G2 회전 복합
- 회전 추종을 연달아 더 올리지 않는다. 다른 값을 자동으로 발행하지도 않는다.
