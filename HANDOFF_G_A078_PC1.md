# G-A078 — PC1 1,000회 추세 학습 지시서

상태: READY — 로컬 패키지 검증 완료. PC1 실행 담당은 아래 한 회차를 실행하고 결과를 회수한다. PC2 자동 실행 대상이 아니다.

## 0. 한눈에

- 예선 목표: 시뮬레이션 성능 개선을 위한 G2 우측 이동 추종·G6 밀침 회복의 방향 확인, G3 험지·G5 계단 이득 보존.
- 현재 단계: 2/6 — 짧은 학습 pilot 준비. STAY: PC1에서 실행·회수, 작성 담당에게 결과 반환.
- 확보: 정식 서버 A077 iter2400의 모델·설정·69-case 정량 기록·10개 영상·원 report가 패키지 대조 증거로 포함된다. 영상 존재와 행동 판독은 별개다.
- 미확보: G-A078 학습과 행동 결과. 이 문서는 실행 완료를 뜻하지 않는다.
- 설계: A077 보상 설정을 재사용해 `track_lin_vel_xy_exp`만 2.0→2.1. 처음부터 1,000회, seed42, 4096env, 평가900. checkpoint 이어 학습 아님.
- 흐름: A077 평가 완료 → **PC1 1000회 추세 학습** → 개선 시 후속 검증 판단 → 악화 시 A077 보존·다른 방향 판단 → 최종 제출.
- 지금 할 일: 패키지 SHA 확인 후 아래 실행 한 줄을 PC1에서 수행한다.
- 보장하지 않음: 1000회 결과는 예선 점수·성능 채택을 보장하지 않는다. A077과 장비·학습량이 달라 단일 보상의 인과효과로 확정하지 않는다.
- 예상 시간: PC1 현재 속도 미측정. 초반 실제 반복시간으로 `남은 iter × 반복시간`을 계산하고 평가69case·영상10개·패키징 시간을 별도로 확보한다. 완료시각을 임의로 약속하지 않는다.

## 1. 준비 확인

패키지 정본: `workspace/training/quadruped/upload/G-A078/current/GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip`와 같은 이름의 `.sha256`.

SHA256: a344f34cd6b4d44fa04057331c10f95a5bd320fad0e61ee9228f565f39661a47

1. 저장소에는 100MB 제한 때문에 `.zip.001`~`.zip.003`와 `.sha256`을 등재한다. PC1에서 아래 명령으로 번호 순서대로 `/workspace`에 복원한다. 이미 원본 ZIP를 직접 전달받았다면 복원은 생략한다.

```bash
cd /c/dev/Nconnect/workspace/training/quadruped/upload/G-A078/current
cat GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip.001 GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip.002 GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip.003 > /workspace/GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip
cp GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip.sha256 /workspace/
```

Linux PC1은 실제 저장소 경로에서 같은 복원 명령을 사용한다.
2. 기존 Isaac Lab `isaaclab.sh`, Isaac Python 환경, NVIDIA GPU를 사용한다. 배포 train.py/play.py/환경 코드·환경 수·seed는 수정하지 않는다.
3. train.py/play.py가 이미 실행 중이면 이 회차를 동시에 시작하지 않는다. 기존 작업을 강제 종료하지 않는다. 실행 디스크 여유20GB 이상을 확보한다.
4. Git Bash/WSL/Linux에서 `sha256sum -c` 성공 후 ZIP를 해제한다. `current/quadruped_rewards.py`는 열람용이며 기존 학습 폴더에 수동 덮어쓰지 않는다. ZIP 실행기가 격리 작업 폴더를 만든다.
5. `experiment.json`에 가설·경쟁 가설·반증·불명확 판정·회수 목록이 포함된다. 추종 강화가 지형 적응을 해칠 수 있다는 A042 반례도 포함돼 있다.

## 2. 실행

PC1 Windows Git Bash에서 실행한다. 기존 PC1 환경이 다른 위치라면 `ISAACLAB_SH`와 PATH의 **설치 경로만** 실제 위치에 맞춘다.

```bash
cd /workspace && sha256sum -c GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip.sha256 && unzip -oq GO2_G_A078_PC1_TRACK_P2P1_1000_v1.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh bash /workspace/go2_g_a078_pc1_track_p2p1/run_all.sh
```

Windows에서는 실행 터미널을 유지한다. Linux/WSL에서 tmux가 있는 경우 마지막 실행 대신 아래 명령으로 분리 실행할 수 있다.

```bash
ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh bash /workspace/go2_g_a078_pc1_track_p2p1/run_point.sh --only track_lin_vel_xy_exp_p2p1
tmux attach -t go2_g_a078_pc1_track_p2p1
```

실행기는 한 점만 수행한다: 학습1000 → 원 report 보존 → 평가900/full69 → 영상10개 → 결과 ZIP/SHA. 다음 학습을 자동 실행하지 않는다. GPU는 `nvidia-smi`, 진행은 `/workspace/_keep/go2_g_a078_pc1_track_p2p1/logs/candidate_training.log`와 평가 case 수로 확인한다.

완료 표식: `[DONE] GO2_G_A078_PC1_TRACK_P2P1_RESULT_READY`. 최종 성공은 `POINT_STATUS.tsv`의 DONE, `RUNNER_STATUS.txt`의 RUNNER_RC=0 및 FULL_69_COMPLETE와 함께 확인한다. 완료 표식만으로 행동 성능을 판정하지 않는다.

## 3. 실패 처리

- rc20/21/22: 여유 공간·중복 실행·Isaac/GPU 차단. 환경 문제를 해결하고 기존 실행은 보존한다.
- rc23/25: USD 접근·정책 identity·패키지 SHA 실패. 로그를 반환하며 값을 바꾸거나 자동 재학습하지 않는다.
- rc30/32 또는 nonfinite: 부분 결과·checkpoint·report·로그를 회수한다. 자동 재시도·학습 연장 금지.
- rc31: 평가/회수 미완료. 남은 파일과 로그를 먼저 확인한다. 완료 학습을 반복하지 않는다. 같은 패키지는 기존 학습 완료 표식을 재사용한다.
- rc33/34: 기존 결과 또는 작업 폴더 정합성 충돌. 덮어쓰거나 삭제하지 않고 로그를 반환한다.

## 4. 결과 회수와 종료 조건

반환할 파일은 `/workspace/_keep/GO2_G_A078_PC1_TRACK_P2P1_RESULT.zip`와 `.sha256`이다. 작업 폴더 `/workspace/_keep/go2_g_a078_pc1_track_p2p1/`도 검증 완료까지 보존한다.

결과 ZIP에는 원본 `exported/report.html`·SHA·REPORT_STATUS, 학습 bundle/source/env/checkpoint/log/tfevents, 후보69case의 summary/steps/identity, 후보10영상, A077 대조 증거, 상태·manifest가 들어가야 한다. 부분 결과도 별도로 보존하고 완전 회수로 표시하지 않는다.

PC1 담당은 다음을 검증한 뒤 작성 담당에게 전달한다: ZIP SHA/CRC, 내부 manifest, 모델·env 대응, 평가69case, 영상10개, 원 report 존재. 100MB 초과 ZIP를 git에 등재할 때는 `ARTIFACT_MANAGEMENT.md` §6-a에 따라 95MiB parts로 분할하고 원본 SHA를 유지한다. 반환 위치는 `workspace/server_returns/G-A078/`; 기존 `workspace/training`에 통째로 덮어쓰지 않는다.

서버 종료 게이트를 적용할 경우: 학습 bundle·필수영상·telemetry·SHA/manifest의 로컬 도착과 검증을 모두 확인한 뒤에만 종료 가능으로 보고한다. 영상 판정/생성 결과/다운로드 결과/로컬 검증/미측정 시나리오를 각각 기록한다.

## 5. 결과 보고와 다음 결정

PC1 담당은 시작·종료시각, TRAIN_RC/RUNNER_RC, 실제 iter/평가900 pin, 69case/10영상 수, report 상태, ZIP SHA와 반환 경로를 보고한다. 후속 보상값을 임의 선정하지 않는다.

작성 담당은 G1~G7의 영상/정량/공식 결과를 구분해 판독한다. 표적은 G2 `right`의 XY RMSE와 G6 4방향 밀침 후 XY RMSE·회복시간이다. 각 표적이 최소2/3 평가 seed에서 개선되는지 확인하고, 혼합 결과를 숨기지 않는다. 회전 추종도 별도로 비교한다.

보존할 A077 지표: 15cm ≥2단84/96·완주 proxy26/96, 10cm ≥2단96/96·완주 proxy63/96, 험지 생존·추종, 전체 시나리오별 생존×추종. 계단 수치는 동일 판독 도구로 계산한다. 점수 상승만으로 계단 손실을 덮지 않는다.

개선과 이득 보존이 함께 보이면 후속 검증 후보로 검토한다. 표적이 세 seed 모두 악화하거나 계단·험지 손실이 이득을 상쇄하면 A077을 보존하고 2.2 등 추가 강화를 자동 실행하지 않는다. 불완전 회수·발산·혼합 결과는 INTERNAL_GATE_INCONCLUSIVE로 분리한다. 이 시험만으로 성능 채택·정식 서버 제출 리포트의 개선 실적으로 승격하지 않는다.
