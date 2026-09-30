# G-A057 인계 — 다른 PC에서 보상 단일변수 일괄 학습 (새 Claude 세션용, 2026-09-29 작성)

> **2026-09-30 순서 변경(Codex 합의):** 진행 중인 track 1.2 한 행이 끝나면 G-A057을 멈추고 **G-A058을 먼저** 돈 뒤 G-A057 나머지 11행을 이어 돈다. 절차는 §10.

> 새 세션의 Claude는 **이 문서를 처음부터 끝까지 읽고 §1 → §7 순서대로** 진행한다. 사용자에게 같은 설명을 다시 요구하지 않는다.
> 루트 `AGENTS.md`(최우선 절·R-1~R-7), `GO2_NOW.md` 맨 위 줄들, 메모리(MEMORY.md)의 규칙을 함께 따른다.

## 0. 한눈에

- **예선 목표:** Go2 시뮬레이션 70점.
- **이번 작업:** 1순위는 험지(G3)·우회전(G2)·밀침(G6), 2순위는 계단(G5)이다. 각 보상 변수를 바꿨을 때 이 축들이 어떻게 반응하는지 데이터를 모은다.
- **작업 지시자:** Codex(2026-09-29 "기존 완료 시험을 제외한 보상 변수 일괄 탐색 도구").
  - 결과를 받은 뒤 다음 튜닝 정책은 **Codex가 정한다.**
  - Claude는 승자를 고르거나, 값을 합치거나, 값을 추가하지 않는다.
- **출발 설정:** A048 보상(50.16/70, `workspace/_keep/go2_g_a048_a033_lin_vel_z_m125`).
  - 한 실행에서 **한 항만** 바꾼다.
  - 학습 seed 42, 4096 env, 1000 iter, 평가 checkpoint 900, 평가 seed 101·202·303, 69 case.
- **새 학습 12개** (`tools/go2_g_a057_sweep_plan.py`로 확정):
  - track_lin_vel_xy_exp: 1.2, 1.4, 1.6
  - ang_vel_xy_l2: −0.04, −0.08
  - feet_air_time: 0.01, 0.1, 0.35
  - action_rate_l2: −0.008, −0.012
  - flat_orientation_l2: −0.25, −0.5
- **재사용 6개:** lin_vel_z 여섯 점(A033·A044·A043·A050·A048·A049).
  - 보상 전체, 학습 조건, 학습 코드 해시, 평가기·registry 해시, 69 case가 모두 일치해서 재사용한다.
- **A048 기준값 공유 5개. 평가만 필요한 행 0개.**
- **서버 기준 환경:** RTX 5080 16 GB, 4096 env. 한 실행 약 95분(학습 58분)이므로 12개는 서버 기준 약 19시간이다.
- **이 PC의 학습은 탐색용이다.** 제출 정책은 서버 학습 이력과 대조되므로 서버에서 다시 학습한다(R-6·제14조). 이 PC의 정책을 제출 후보로 올리지 않는다.

## 1. pull 직후 상태 확인 (파일이 다 왔는가)

1. `git status`로 rebase가 끝났는지 보고, `git log --oneline -10`에 아래 커밋이 있는지 확인한다.
   - "feat: add Go2 G-A057 sweep plan package"(작성 PC 커밋 adae1fa)
   - 없으면 사용자에게 알리고 멈춘다.
2. 다음 파일이 모두 있어야 한다.
   - `tools/go2_g_a057_sweep_plan.py`: 실행 목록 확정(재사용·새 학습·평가만 필요)
   - `tools/go2_g_a057_run_sweep.sh`: 일괄 러너 원본. 패키지에는 `go2_g_a057/run_sweep.sh`로 들어간다.
   - `tools/build_go2_g_a057_sweep_package.py`: 패키지 빌더
   - `tools/go2_g_a057_sweep_compare.py`: 비교표·그래프
     - **작성 PC에서 커밋 뒤에 만든 파일이다.** 없으면 사용자에게 작성 PC에서 커밋·푸시해 달라고 요청한다.
   - `workspace/training/quadruped/reports/evidence/go2_g_a057_sweep_plan/SWEEP_PLAN.{json,md}`
   - 입력 자료
     - `workspace/training/quadruped/upload/G-A055/current/GO2_G_A055_a043_ang_vel_xy_m008_full69_v2.zip`: 러너·배포 코드·평가기·registry·G-A033 sentinel의 원천. **바이트를 바꾸지 않는다.**
     - `workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/`와 재사용 5개 회차 폴더: 목록 도구와 비교 도구가 읽는다. 대용량이라 git에 없으면 사용자에게 복사를 요청한다.
3. 러너 수정 두 가지가 들어갔는지 확인한다. 커밋 시점이 수정 시점과 겹쳐 확인이 필요하다.
   - `grep -n '</dev/null' tools/go2_g_a057_run_sweep.sh`: 실행마다 러너 표준입력을 끊는다. 없으면 목록 파일을 러너가 먹어 다음 실행이 사라진다.
   - `grep -n 'Restore only package files' tools/go2_g_a057_run_sweep.sh`: 작업 폴더 체크섬이 깨지면 패키지 파일만 다시 깐다.
   - 없으면 넣는다. 위치는 `bash "$runner" --inner` 줄, 그리고 `sha256sum -c` 검사 앞이다.
4. `python -B tools/go2_g_a057_sweep_plan.py`를 돌려 목록이 §0과 같은지 본다(NEW_TRAIN 12, REUSE 6, BASE_SHARED 5, EVAL_ONLY 0).
   - 다르면 이유(입력 폴더 누락 등)를 적고 멈춘다.

## 2. 남은 코드 작업 (학습 전에 끝낸다)

1. **비교 도구 결함 수정**
   - 증상: 작성 PC에서 A048(재사용)이 총점·밀침 합·계단 칸 모두 "미측정"으로 나왔다. G2·G3·G6 축 점수와 험지 옆걸음 낙상 16은 정상이었다.
   - 의심 지점 세 곳을 먼저 확인한다.
     - `axis_scores`: registry의 `internal_cases` 중 summary를 못 찾은 case가 있으면 total을 미측정으로 만든다. 어떤 case 이름이 비는지 출력해 본다(G7 `dr_seed_{seed}` 치환 등).
     - `hypothesis.posture_falls`가 밀침 case에서 None을 내는지. 밀침 summary의 `posture_envs_observed`와 `posture_measured`를 확인한다.
     - `climb.count`가 계단 steps.csv에서 None을 내는지.
   - 원인을 찾아 고치되, **판정 문턱을 새로 만들지 않는다.**
   - 기존 수치로 검증한다. A048은 총점 50.16, 험지 옆걸음 16, 밀침 합 1, 15cm ≥2단 24, 10cm ≥2단 90이 나와야 한다(`GO2_SYNTHESIS_A043_A048_A055_20260929.md` §1).
2. **계약 테스트 `tools/test_go2_g_a057_sweep_contract.py` 작성** (Codex 지시 §6: GPU 없이 가짜 실행)
   - 목록: NEW 12, REUSE 6, BASE_SHARED 5. A038(ang −0.08, lin −2.0)이 A048 위 ang −0.08을 대체하지 않는다.
   - 패키지: 실행마다 `candidate/quadruped_rewards.py`가 A048과 정확히 한 항만 다르다. 러너와 shared 파일은 G-A055 v2와 바이트가 같다. 실행마다 shared + runs/<key>를 펼친 트리가 `PACKAGE_SHA256SUMS.txt`를 통과한다.
   - 러너(가짜 러너 사용, `GO2_SWEEP_TEST_MODE=1`, `GO2_SWEEP_KEEP_BASE`, `GO2_SWEEP_TEST_RUNNER`, `GO2_SWEEP_TEST_FREE_GB`)
     - ① 한 실행이 실패해도 기록하고 다음으로 간다.
     - ② 다시 실행하면 완료된 실행은 SKIP_DONE이고 그 폴더 해시가 바뀌지 않는다. 실패한 실행은 GO2_RESUME=1로 이어 간다.
     - ③ 학습 시작 전 실패는 종료코드 23으로 전체를 멈춘다.
     - ④ 디스크 부족은 20으로 멈춘다.
     - ⑤ 폴더 없이 결과 ZIP만 있으면 BLOCKED로 두고 덮어쓰지 않는다.
     - ⑥ 두 실행 연속 학습 실패는 24로 멈춘다.
   - 가짜 러너는 `PACKAGE_ROOT/run_config.env`의 `KEEP_DIR_NAME`·`RESULT_ZIP_NAME`을 읽어 `$GO2_SWEEP_KEEP_BASE` 아래에 `RESULT_STATUS.txt`(RESULT_STATE=FULL, COLLECTION_STATUS=FULL_69_COMPLETE)·ZIP·`.sha256`을 쓴다.
   - 테스트가 통과하기 전에는 "준비 완료"라고 말하지 않는다(메모리: 판독 코드를 돌려봤다).
3. **발행:** `python -B tools/build_go2_g_a057_sweep_package.py`
   - 출력: `workspace/training/quadruped/upload/G-A057/current/GO2_G_A057_a048_single_var_sweep_v1.zip`, `.sha256`, `GO2_G_A057_RUN_GUIDE.txt`
   - 발행한 ZIP은 불변이다. 고쳐야 하면 v2로 새로 낸다(메모리: 발행물 이름이 판을 말한다).
4. **원장 등록:** `ARTIFACT_MANAGEMENT.md`에 G-A057 작업 ID·상태(PLANNED)·영상 판정을 적는다. 영상은 필수이며, 실행마다 후보 영상 10편을 러너가 찍는다. `GO2_NOW.md` 맨 위에는 한 줄을 추가한다.

## 3. Isaac 설치 확인 (사용자가 설치 중 — 끝났는지부터 본다)

1. **OS 확인.** `uname -a`(Linux)나 `ver`(Windows)로 본다.
   - 러너는 bash·tmux·`/workspace` 경로를 쓰는 **Linux용**이다(G-A055 서버 러너 그대로).
   - Windows면 §5-b를 따른다.
2. **GPU.** `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv`
   - 서버 기준은 RTX 5080 16303 MiB다. VRAM이 16 GB보다 작으면 4096 env 학습이 메모리 부족으로 실패할 수 있다. §4-2에서 확인한다.
   - **로봇 수를 줄이지 않는다.** 줄이면 서버 결과와 비교할 수 없다.
3. **Isaac Sim / Isaac Lab 버전.**
   - 서버는 Isaac Lab **v2.3.1**이다(GO2 MASTER, G-F35). Isaac Lab 2.3은 Isaac Sim **5.1** 기반이고, 사용자는 5.1을 설치 중이다.
   - Isaac Lab 위치를 찾는다(`isaaclab.sh` 또는 `isaaclab.bat`). `git -C <IsaacLab> describe --tags`로 버전을 확인한다.
   - 2.3.1이 아니면 사용자에게 알리고, 2.3.1로 맞출지 묻는다. 다른 버전이면 결과를 서버와 비교할 수 없다.
   - `<isaaclab.sh> -p -c "import isaaclab, isaacsim; print('ok')"`
   - `rsl_rl`·`torch` 버전도 기록한다: `<isaaclab.sh> -p -m pip show rsl-rl-lib torch`
4. **디스크.** 실행 하나에 수 GB가 든다. 12개와 여유분을 합쳐 **100 GB 이상**을 권한다. 러너는 20 GB 미만이면 멈춘다.
5. 확인 결과는 `workspace/training/quadruped/reports/GO2_G_A057_OTHER_PC_ENV_<날짜>.md`에 적는다. OS, GPU, 드라이버, Isaac Sim, Isaac Lab, rsl_rl, torch, 디스크를 쓰고 서버와의 차이를 표시한다.

## 4. 동작 확인 (smoke) — 짧게, 상한을 걸고

패키지의 `shared/candidate`(배포 학습 코드) 사본으로 **작업용 임시 폴더**에서만 한다. 발행물이나 `workspace/training` 원본은 건드리지 않는다. 모든 명령에 `timeout`을 건다(메모리: 실행에 상한을 박는다).

1. **학습이 도는가:** 보상 파일을 A048 값으로 둔 사본에서 `timeout 900 <isaaclab.sh> -p train.py --task Quadruped-v0 --num_envs 64 --max_iterations 3 --seed 42 --headless`
   - 종료코드 0, `logs/rsl_rl/quadruped/*/model_*.pt`, `exported/env.yaml`이 나오는지 본다.
2. **4096 env 메모리:** 같은 명령을 `--num_envs 4096 --max_iterations 2`로 돌린다.
   - OOM이면 **여기서 멈추고** 사용자·Codex에 보고한다(GPU 부족 → 이 PC로 서버 조건 재현 불가).
   - 한 iter 시간을 적는다. 서버는 1000 iter에 58분(iter당 약 3.5초)이었다. 이 비율로 12개 예상 시간을 다시 계산한다.
3. **평가가 서버와 같은가:** A048 정책(`workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/training/model_best.pt`, `env.yaml`)을 `exported/`에 두고 G1 forward_nominal seed 101 한 case를 돈다.
   - 명령은 러너의 `run_eval_case`와 같게 한다. play.py, `--num_envs 32`, `NCRC_EVAL_*` 환경변수, 명령 오버라이드를 쓴다(`shared/server_run_go2_candidate_iter_pinned.sh`의 `run_eval_case` 참고).
   - 결과 `summary.json`을 서버 저장본 `.../evaluation/candidate/cases/seed_101/forward_nominal/summary.json`과 비교한다. 생존, 추종 RMSE, 속도를 본다.
   - 차이는 기록만 하고 문턱을 새로 만들지 않는다. 러너의 G-A033 sentinel 5 case도 실행마다 같은 비교를 남긴다.
4. 세 가지가 모두 되면 §5로 간다. 하나라도 안 되면 무엇이 안 되는지 적고 사용자에게 보고한 뒤 멈춘다.

## 5. 학습 실행 (Claude가 직접 돌린다)

### 5-a. Linux (기본 경로)
1. `/workspace`에 쓸 수 있는지 확인한다(`sudo mkdir -p /workspace && sudo chown $USER /workspace`는 사용자 승인 뒤).
   - Isaac Lab이 `/workspace/IsaacLab`에 없으면 `ISAACLAB_SH=<경로>/isaaclab.sh`를 넘긴다.
   - 러너는 **평가·영상 줄에서 `/workspace/IsaacLab/isaaclab.sh`를 직접 부른다.** 그러므로 `/workspace/IsaacLab`이 실제 설치를 가리키는 심볼릭 링크라도 있어야 한다.
2. 결과 위치: 러너는 `/workspace/_keep`에 쓴다. 저장소의 `workspace/_keep`과 다르면 실행 뒤 §6에서 복사한다(원본은 지우지 않는다).
3. 실행: `unzip -oq <ZIP> -d /workspace && bash /workspace/go2_g_a057/run_sweep.sh`
   - tmux 세션 `go2_g_a057`에서 순서대로 돈다.
   - 먼저 `bash /workspace/go2_g_a057/run_sweep.sh --list`로 목록과 예상 시간을 사용자에게 보여 준다.
4. 감시: Bash `run_in_background`나 Monitor로 `SWEEP_STATUS.tsv`와 `sweep.log`를 본다. 짧은 간격으로 폴링하는 루프는 띄우지 않는다.
   - 실행 하나가 끝날 때마다 상태 한 줄(DONE/FAILED/SKIP)을 사용자에게 보고한다.
5. 끊기면 같은 명령을 다시 친다. 완료된 실행은 건너뛰고, 부분 결과는 이어 간다.
   - 학습 도중 끊긴 실행은 러너가 보존하고 종료코드 9로 멈춘다. 처음부터 다시 할지는 사용자에게 묻는다(`GO2_RESTART_TRAINING=1`은 보존본을 지운다).

### 5-b. Windows인 경우 (러너가 그대로는 안 돈다)
- 막히는 것: tmux 없음, `/workspace` 경로, `isaaclab.sh`(Windows는 `isaaclab.bat`), `pgrep` 없음.
- 가능한 우회(검증 전)
  - Git Bash의 `/etc/fstab`에 `C:/workspace /workspace` 마운트를 추가한다.
  - `C:\workspace\IsaacLab\isaaclab.sh`로 `isaaclab.bat -p "$@"`를 부르는 작은 bash 래퍼를 둔다.
  - tmux 대신 `bash run_sweep.sh --inner`를 백그라운드로 돌린다.
- **G-A055 러너 바이트는 바꾸지 않는다.** 래퍼와 마운트만으로 되는지 §4 smoke를 이 경로로 다시 돌려 확인한다.
- 안 되면 사용자에게 Linux(Ubuntu 22.04/24.04) 설치나 듀얼부팅을 권하고 멈춘다.

## 6. 결과 회수와 비교
1. 실행마다 `/workspace/_keep/go2_g_a057_<key>/`(폴더 전체)와 `GO2_G_A057_<KEY>_RESULT.zip`·`.sha256`이 생긴다. `/workspace/_keep/go2_g_a057_sweep/`에는 상태 표·환경 기록·실행 로그가 있다.
2. 저장소 `workspace/_keep/`에 같은 이름으로 **복사**한다(원본 유지). ZIP은 `sha256sum -c`로 확인한다.
3. `python -B tools/go2_g_a057_sweep_compare.py`
   - 출력: `workspace/training/quadruped/reports/evidence/go2_g_a057_sweep_compare/`(`SWEEP_METRICS.csv`, `SWEEP_COMPARE.md`, 변수별 PNG)
   - 없는 칸은 "미측정"이다. 학습 지표로 평가 행동을 대신하지 않는다.
   - 서버와 다른 GPU면 표의 환경 열에 표시된다.
4. 사용자에게는 `## 0. 예선 기준 현재 위치`로 시작해 변수별 반응을 관측 그대로 보고한다. 승자·다음 값은 쓰지 않는다. Codex 전달용은 표 없이 문장으로 쓴다(메모리). 판독 보고서와 원장(ARTIFACT_MANAGEMENT, GO2_NOW)도 갱신한다.

## 7. 미결 결정과 지켜야 할 것
- **Codex 결정 대기 — A048 보정 재학습 1회**를 목록 맨 앞에 넣을지.
  - 목적: 이 PC 차이와 학습 흔들림을 합친 크기를 재서, 나머지 12개의 차이를 읽는 기준으로 쓴다.
  - Codex 지시의 "A048 반복 실행 안 함"과 충돌하므로 **승인 전에는 넣지 않는다.**
  - 승인되면 빌더에 행 하나(A048 그대로, 키 예: `a048_calibration`)를 더하고 v2로 발행한다.
- **사용자 고정·기각 사항**
  - lin_vel_z는 고정이다. 이번 탐색은 재사용 행만 쓰고 새로 학습하지 않는다.
  - feet_air_time 0.25는 사용자가 기각했다. 이번 목록에 0.25는 없고, 0.35는 Codex 목록 값이다.
  - 학습 연장은 제외다.
- **금지·규칙**
  - 배포 학습 코드는 수정하지 않는다(보상 가중치만).
  - 결과를 본 뒤 문턱을 바꾸지 않는다. 발행물은 불변이다.
  - `sed -i`나 줄끝 변환을 glob에 걸지 않는다.
  - 커밋·푸시는 사용자가 요청할 때만 한다.
  - 사용자 보고는 `## 0. 예선 기준 현재 위치`로 시작한다.
- **분석 원칙:** 관측 → 넘어진 이유 설명 여부 → 강좌·배포 예측 → 반례 순서를 지킨다(AGENTS 최우선 절). 이번 작업은 데이터 수집이므로 해석은 Codex 결정 뒤에 한다.
- **작성 PC에서 끝난 판단 기록**(다시 분석하지 않는다)
  - `reports/GO2_FAILURE_TO_LECTURE_ACTION_20260929.md`
  - `reports/GO2_LIN_VEL_Z_A043_VS_A048_WHY_20260929.md`
  - `reports/GO2_ANG_VEL_XY_STRENGTHEN_EVIDENCE_20260929.md`
  - `reports/GO2_A048_AIR_TIME_CHECK_20260929.md`
  - `reports/GO2_EXTERNAL_TUNING_CASES_20260929.md`

## 8. 추가 — Codex 계단 전략 (2026-09-29, 인계 문서 작성 뒤 수신)
- **사용자가 탐색 제약을 풀었다**(lin_vel_z 고정·feet_air_time 기각을 이 탐색 범위에서 해제, Codex 전달). 공식 규정 R-6 변경은 아니다.
- Codex 추천 계단 시험 네 칸 (나머지 항 전부 고정: ang_vel_xy −0.05, flat 0, action_rate −0.01, track 1.5):
  - lin_vel_z −1.5 × feet_air_time 0.2 = 기존 A043 (재사용)
  - lin_vel_z −1.5 × feet_air_time 0.01 = **새 시험 1 (계단 중심 우선)** — **G-A057 목록에 없다.** A048 기준 빌더라 A043 기준 행을 받도록 확장해야 한다.
  - lin_vel_z −1.25 × feet_air_time 0.2 = 기존 A048 (재사용)
  - lin_vel_z −1.25 × feet_air_time 0.01 = **새 시험 2 (종합 성능 보존 비교)** — **G-A057의 `feet_air_time_p0p01`과 같은 설정이다(중복 학습 금지).**
- 할 일:
  1. `tools/go2_g_a057_sweep_plan.py`에 A043 기준 행 하나(`a043_feet_air_time_p0p01`: A043 env.yaml 보상에서 feet_air_time만 0.01)를 추가하고, 재사용 판정 규칙(보상 전체·조건·코드·평가기 일치)을 그대로 적용한다. 빌더의 `reference/*` 는 그 행의 기준(A043) 보상으로 렌더한다.
  2. Codex가 이 두 시험을 우선했으므로 `sweep_order.txt` 맨 앞에 새 시험 1 → 새 시험 2(`feet_air_time_p0p01`) 순으로 둔다. 순서 변경은 Codex 추천을 따른 것으로 적는다.
  3. 판독 주 결과: 10cm·15cm 완주율과 추종, 정지 여부. 과정: 모서리 통과·몸통 상승·다음 발 재접지(채널 없으면 미측정). 보호: 험지·우회전·밀침과 G1~G7. **두 새 시험 모두 계단 이득이 없으면 체공 항 완화를 계단 해결책으로 계속 밀지 않는다**(Codex).
- Claude 보충 — 경쟁 예측 (우리 자료, 판독 때 함께 본다, `reports/GO2_A048_AIR_TIME_CHECK_20260929.md`):
  - A048 15cm 계단에서 출발점 대비 수직 들림이 0.15 m 이상인 걸음은 **체공 0.2~0.3초에 몰렸고**(21.5%), 0.1초 미만은 2.5%였다.
  - 0.01로 낮추면 짧은 착지 벌점이 거의 사라져 체공이 더 짧은 쪽(0.1초 미만)으로 갈 수 있다. 그러면 발 들림이 낮은 걸음이 늘어 계단에 불리하다는 예측이 Codex의 "재접지 덜 억제" 예측과 경쟁한다. 판독 때 두 시험의 체공 시간 분포(진단 채널이 없으면 미측정)와 계단 결과를 함께 본다.
  - 반례: A031(A017 위 0.2→0.01) 표적 proxy −0.022, 1단계 FAIL. 계단 오르기는 그 회차에서 따로 세지 않았다.
- **정정 필요 (Codex 지적, 작성 PC에서 확인됨):** 우리 env는 `UnitreeGo2RoughEnvCfg` 계열로 **height_scan 관측(`observations.policy.height_scan`, `scene.height_scanner`)과 terrain_levels 커리큘럼이 이미 있다**(A048 학습 env.yaml L323·L599·L925 확인). `reports/GO2_EXTERNAL_TUNING_CASES_20260929.md` §2 마지막 항과 `upload/plan/GO2_CLAUDE_OPINION_AFTER_EXTERNAL_CASES_20260929.md` §5의 "지형 높이 관측·… 우리 env에 없거나"는 **틀렸다** — 높이 관측과 커리큘럼은 있고, 없는 것은 발 스윙 높이·몸 높이 추적 항, 계단 모서리 벌점, 교사-학생 학습, 계단 미세조정 단계다. 또 외부 사례의 "1500 iter"만 떼어 가져오는 것도 잘못이다(Rudin은 높이 관측·커리큘럼과 함께 쓴 결과). 두 문서를 이 내용으로 고친다(작성 PC에서는 rebase 진행 중이라 손대지 못했다).

## 9. Codex 최종 지시 (2026-09-29, §8 할 일 1·2 취소)
- **G-A057 목록은 바꾸지 않는다.** `feet_air_time_p0p01`은 일반 변수 탐색 행으로 두고, 계단 목적으로 맨 앞에 올리지 않는다(`sweep_order.txt` 순서 그대로).
- **A043+0.01 행(`a043_feet_air_time_p0p01`)은 추가하지 않는다.** 빌더를 A043 기준으로 확장하지 않는다.
- **Codex의 '계단 우선 2×2' 권고는 근거 확대 오류로 정정한다.** 기존 문서와 발행물은 수정하지 않고 보존한다. 오류 내용:
  - 강좌·배포 예측은 feet_air_time 하향이 "발 낮게 ↓ 등반약"(`_finalize.py` `_REP_INTENT`)이라고 한다. 계단 개선 가설과 방향이 반대다.
  - 근거로 쓴 A048 음수 착지 관측은 같은 날 "하향은 이 자료로 선정하지 않는다"(`GO2_A048_AIR_TIME_CHECK_20260929.md` §3)고 판정된 자료다.
  - A048에서 발을 0.15 m 이상 든 걸음은 체공 0.2~0.3초 구간에 몰렸다(21.5%). 0.1초 미만은 2.5%였다.
  - 철회의 핵심은 **같은 A048 자료를 계단 개선의 우선 근거로 확대해 쓴 판단 오류**다. 칸마다 학습 seed가 하나뿐인 것은 상호작용을 확정하기 어렵다는 **한계**일 뿐, 2×2 탐색 자체를 무효로 만들지 않는다(Codex 정정 2026-09-29).
- §8 할 일 3의 계단 판독 틀은 쓰지 않는다. `feet_air_time_p0p01` 행은 다른 행과 똑같이 판독한다.
- **옛 문장 두 곳 정정 — 완료(2026-09-29, rebase 종료 후 적용).** `reports/GO2_EXTERNAL_TUNING_CASES_20260929.md` §1-1(Rudin 1500 iter에 "높이 관측·커리큘럼과 함께 쓴 결과" 부기)·§2 마지막 항, `upload/plan/GO2_CLAUDE_OPINION_AFTER_EXTERNAL_CASES_20260929.md` §5 외부 계단 해법 항을 "지형 높이 관측과 terrain_levels 커리큘럼은 이미 있다"로 고쳤다. 근거 A048 `training/env.yaml`: `height_scanner` L323, `height_scan` L599, `terrain_levels` L926(§8의 L925는 오기). 발행 ZIP은 바꾸지 않았다.
- **A043 행을 넣지 않는 이유 (Codex 정정 2026-09-29).** "A048에서 이득이 없으면 A043을 생략해도 결론이 같다"는 틀렸다. 기준 설정에 따라 효과가 뒤집힌 전례(ang_vel_xy −0.08: A033 험지 옆걸음 낙상 59→18, A043 24→50)가 있어 두 설계는 같은 질문에 답하지 않는다. 생략하는 이유는 결론이 같아서가 아니라, 지금 추가 비용을 우선 배정할 근거가 부족하기 때문이다.

## 10. 순서 변경 — G-A058 먼저 (2026-09-30, Claude 제안 + Codex 합의)
- 근거·판독: `workspace/training/quadruped/upload/plan/GO2_OTHER_PC_SEQUENCE_PROPOSAL_20260930.md`. §7의 'A048 보정 재학습'은 이 G-A058 첫 행으로 해결한다(Codex: 이 한 번의 대조 실행에 한해 'A048 반복 실행 안 함' 변경).
- 패키지: `workspace/training/quadruped/upload/G-A058/current/GO2_G_A058_replicate_a048s42_a043s43s44_v1.zip` SHA256 `ece5a1900cf7b1da5d348c68c9d4423a42c1892322a9c75b47bc0ddc79362da2`, 안내 `GO2_G_A058_RUN_GUIDE.txt`.
  - 행: a048_seed42(A048 보상, seed 42) → a043_seed43(A043 보상, seed 43) → a043_seed44(A043 보상, seed 44). 보상 변경 없음. 선택 행 A043 seed 42는 넣지 않는다(Codex).
  - 러너·shared는 G-A055 v2 바이트 그대로이고, 일괄 러너는 G-A057 러너에서 이름만 바꿨다(계약 테스트 `tools/test_go2_g_a058_replicate_contract.py`).
- 절차:
  1. G-A057 track 1.2 행이 DONE이 되면 G-A057 tmux를 멈춘다. 다음 행이 이미 학습을 시작했으면 러너가 부분 결과를 보존하고 종료코드 9로 멈춘다. 그 행을 처음부터 다시 할지는 나중에 사용자에게 묻는다.
  2. `unzip -oq /workspace/GO2_G_A058_replicate_a048s42_a043s43s44_v1.zip -d /workspace && bash /workspace/go2_g_a058/run_sweep.sh` (먼저 `--list`로 목록 확인). 다른 학습 프로세스가 돌고 있으면 러너가 21로 멈춘다.
  3. 세 행이 끝나면 `bash /workspace/go2_g_a057/run_sweep.sh`로 G-A057을 이어 돈다(완료된 1.2 행은 SKIP_DONE).
- 회수: `/workspace/_keep/go2_g_a058_<key>/`, `GO2_G_A058_<KEY>_RESULT.zip`+`.sha256`, `/workspace/_keep/go2_g_a058_sweep/`를 저장소 `workspace/_keep/`에 복사한다.
- 판독(Codex 정정 반영): A048 seed 42는 서버 A048과의 차이를 기록만 하는 비교 기준이며 효과 판정 문턱이 아니다. G-A057 행은 이 행과 먼저 비교하고, 서버 A048 대비 결과와 기존 사전등록 판정도 따로 유지한다. A043 행은 개별 정책과 설정 재현성을 나눠 판정한다. 다른 PC 정책은 제출 후보가 아니다.
