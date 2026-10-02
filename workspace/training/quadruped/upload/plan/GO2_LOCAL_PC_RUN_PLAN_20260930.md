# 이 PC(로컬, RTX 3050 6GB) 실행 계획 — G-A057 1.2 → G-A058 → G-A057 나머지 (Claude, 2026-09-30 21시)

작성 PC(다른 PC)에서 **요구한 순서·판독과 이 PC가 실제로 하도록 설정된 동작이 같은지** 확인하는 문서다.
대조 원문: `HANDOFF_G_A057_OTHER_PC.md`, `upload/plan/GO2_OTHER_PC_SEQUENCE_PROPOSAL_20260930.md`(§2 순서, §3 판독, §6 Codex 합의).
표기: [설정됨] 지금 자동으로 돌도록 걸려 있음 / [미설정] 확인 후 설정할 것 / [확인 요청] 작성 PC의 답이 필요.

## 0. 한눈에

| 순서 | 작업 | 상태 | 이 PC 예상 시각 |
|---|---|---|---|
| 1 | G-A057 `track_lin_vel_xy_exp_p1p2` (track 1.5→1.2) | 학습 완료(20:48), **평가 진행 중**(재개 실행) | 평가·영상·ZIP 끝 약 22:20~22:40 |
| 2 | G-A058 행 1 `a048_seed42` (A048 보상, seed 42) | [설정됨] 1이 검증 완료되면 자동 시작 | 약 22:40 → 10/1 07:30 |
| 3 | G-A058 행 2 `a043_seed43` (A043 보상, seed 43) | [설정됨] 행 1 뒤 자동 | → 10/1 16:30 |
| 4 | G-A058 행 3 `a043_seed44` (A043 보상, seed 44) | [설정됨] 행 2 뒤 자동 | → 10/2 01:30 |
| 5 | G-A057 나머지 11행 (v1 순서 그대로) | [설정됨] (21:45, 사용자 승인) G-A058 rc=0 종료 후 자동 | 약 10/2 01:30 → 10/6 전후 |

시각은 이 PC 실측 기준 한 실행 약 8.5~9시간(학습 1000 iter 약 7시간 + 평가 74 case 약 1시간 + 영상·ZIP)으로 잡은 추정이다.
서버(RTX 5080)는 한 실행 약 95분이다. **GPU 메모리 6GB가 학습에 모자라(학습 약 6.8GB 필요) 공유 메모리로 넘치는 것이 이 PC의 정상 상태다.**
넘쳐도 계산 결과는 같고 속도만 느리다.

**순서 대조:** 제안서 §6 합의 "track 1.2 완료 → G-A058(A048 seed 42 → A043 seed 43·44) → G-A057 나머지 11행"과 같다.
G-A058 순서는 패키지 `sweep_order.txt`(a048_seed42 → a043_seed43 → a043_seed44)를 그대로 쓴다.

## 1. 실행 한 번(한 행)에 일어나는 일 — 러너 바이트 그대로

G-A057 v1(SHA `c225879e…`)과 G-A058 v1(SHA `ece5a190…`) 패키지의 러너를 **바이트 변경 없이** 쓴다.
두 패키지의 실행 단위 러너(`server_run_go2_candidate_iter_pinned.sh`)는 G-A055 v2와 같은 바이트다.

1. 학습: 4096 env, 1000 iter, `run_config.env`의 `TRAIN_SEED`
2. iter 900 체크포인트 고정(평가 대상), 보상 최고 체크포인트는 `model_best_by_reward.pt`로 따로 보존
3. `report.html` 회수(`REPORT_ACQUIRED` 확인), `env.yaml` 보상값 검사(`ENV_REWARDS_OK`)
4. 재앙 관문 `G1:forward_nominal:101` → 움직이지 않아도 `COLLECT_REQUIRED_ON_STATIONARY=1`이라 **전 case를 끝까지 잰다**
5. 후보 69 case(평가 seed 101·202·303) → G-A033 sentinel 5 case → 영상 10편 → 결과 ZIP + `.sha256`

결과는 서버와 같은 이름으로 `D:\workspace\_keep\`에 생긴다:
`go2_g_a05x_<key>/`(폴더 전체) · `GO2_G_A05X_<KEY>_RESULT.zip` · `.sha256` · `go2_g_a05x_sweep/`(상태 표·로그).

## 2. 자동으로 걸려 있는 것 (세션과 분리된 프로세스, Claude가 꺼져도 돈다)

| 스크립트 | 하는 일 |
|---|---|
| `D:\workspace\plan_supervisor.sh` (21:48부터, 아래 두 체인 대체) | 1.2 러너 종료 → `go2_g_a058/run_sweep.sh --inner` → `go2_g_a057/run_sweep.sh --inner` 순서로 실행. **멈춤이 나와도 다음 단계로 진행**하고, 계획 전체에서 **멈춤이 2회가 되면 그 즉시 전부 정지**(run_sweep·러너·train/play 종료, `D:\workspace\_keep\PLAN_HALTED.txt` 작성). 멈춤 = 1.2가 완전 결과 아님 / 상태 표에 DONE·SKIP_DONE 외 행(RUN_ERROR, COLLECTION_FAILED, SAFETY_STOP, ABORT_* 등) / 행 없이 run_sweep rc≠0. 1.2가 불완전하면 G-A057 스윕이 나중에 이어서 수집한다. 로그 `D:\workspace\_keep\plan_supervisor.log` |
| ~~`chain_after_a057_p1p2.sh`, `chain_after_g_a058.sh`~~ | 21:48 종료·대체(완전 결과가 아니면 멈춰 버리는 방식이었음) |
| `D:\workspace\sync_results_to_repo.sh` | 5분마다 검증 완료된 행을 `D:\dev\Nconnect\NConnect\workspace\_keep\`로 **복사**(원본 유지, ZIP 해시 재검사). 복사 후 분석 도구 실행(§4). 로그 `D:\workspace\_keep\sync_results_to_repo.log` |
| `run_sweep.sh`의 상태 표 | `D:\workspace\_keep\go2_g_a058_sweep\SWEEP_STATUS.tsv` (DONE / RUN_ERROR 등, 인계 문서의 정의 그대로) |

G-A058 뒤 G-A057 나머지 11행 연결은 **[설정됨]**(2026-09-30 사용자 승인): 위 `plan_supervisor.sh`가 담당한다(1.2는 `SKIP_DONE`, 불완전하면 이어서 수집).
사용자 규칙(21:5x): "멈추는 경우에는 계획서에 따라 진행, 2회 이상 멈추면 그때 작업을 멈춘다".

## 3. 이 PC가 서버와 다른 점 — 판독 때 반드시 함께 볼 것

| 항목 | 서버 | 이 PC | 영향 |
|---|---|---|---|
| GPU | RTX 5080 16GB | RTX 3050 6GB (학습 중 약 1.1~1.4GB 공유 메모리로 넘침) | 속도만. 러너가 `meta/gpu.csv`에 기록 → 비교 도구가 환경 열에 표시 |
| Isaac Sim | 5.1 (서버 env.yaml의 에셋 경로 `Assets/Isaac/5.1`) | 5.1 (pip) | 같음 |
| Isaac Lab / rsl-rl | 정확한 커밋 [모름]. rsl-rl 4 이상 형식(`MLPModel`, `actor_state_dict`) | IsaacLab `main` b0542fe2d(2026-07-24), rsl-rl-lib 5.0.1 | `agent.yaml` 서버와 동일(seed·iter·run·device 제외), `env.yaml` 651키 중 차이 10개(에셋 경로·num_envs 등) |
| 에셋 | S3 원격 | 사내망이 S3 차단 → 로컬 사본(`D:\dev\Nconnect\isaac_assets`). Go2·재질·하늘은 S3 사본, 평지 `Environments/Grid`는 NVIDIA 공식 environments 팩 | **`Props/UIElements/arrow_x.usd`는 임시 대체 파일(막대 모양)**. 명령 화살표 표시 전용 — 물리·관측 무관, 영상 속 화살표 모양만 다름 |
| 실행 방식 | Linux, tmux | Windows + Git Bash. 러너 바이트 그대로, 주변 대체물만 둠: `/workspace`→`D:\workspace` 연결, `isaaclab.sh` 래퍼(로컬 에셋 경로 전달), `python.bat` 런처(finalize·평가 계측용), `python3`·`pgrep` 대체 | 러너·배포 학습 코드·평가기 바이트 불변 |
| 결과 env.yaml | S3 URL | `D:/dev/...` 로컬 에셋 경로가 박힘 | 이 PC 정책은 탐색용이라 제출하지 않음(인계 §0). 제출 시에는 서버 재학습 |

**이 PC 환경이 믿을 만한지는 G-A058 행 1(`a048_seed42`)로 판단한다.** 서버 A048과 보상·seed가 같으므로 차이가 곧
"이 PC + 학습 흔들림"의 크기다(제안서 §3: 한 쌍의 관측이며 효과 판정 문턱으로 쓰지 않는다).

## 4. 분석 — 이 PC에서 자동으로 도는 것과 막혀 있는 것

| 도구 | 대상 | 입력 | 상태 |
|---|---|---|---|
| `tools/go2_g_a057_prereg_readout.py --all` | G-A057 각 행 | 결과 + `PREREGISTRATION.json`(A048 seed별 기준값 내장) | [설정됨] 행 복사 때마다 실행 → `reports/evidence/go2_g_a057_prereg_readout/` |
| `tools/go2_g_a057_sweep_compare.py` | G-A057 변수별 비교표·그래프 | 결과 + **기준 회차 13개 폴더**(A048·A043 포함) | **막힘 — 이 PC `_keep`에 기준 폴더가 없다.** 실패를 로그에 남기고, 폴더가 들어오면 자동 재실행 |
| G-A058 판독(제안서 §3) | 행 1·2·3 | 결과 + 서버 A048·A043 폴더 | **전용 도구 없음** — §6 확인 요청 |
| `tools/go2_stairs_six_edge_compare.py`, `tools/go2_stairs_push_forward_simultaneity.py` | 계단 모서리 동작 | 결과 + A043 등 | 기준 폴더 필요 |

사용자 지정 비교 기준(2026-09-30): **계단은 A043, 험지·밀침·우회전은 A048(50.16/70)과 비교한다.**

## 5. 오늘 실행에서 생긴 일 (기록)

1. **20:48 1.2 평가 첫 case 실패(rc 5)** — 평지 바닥 `Isaac/Environments/Grid/default_environment.usd` 로컬 누락.
   NVIDIA 공식 팩에서 받아 해결, `GO2_RESUME=1`로 학습은 건너뛰고 평가부터 재개(20:51). 학습 결과 보존.
2. **1.2 정책은 움직이지 않는 정책(`LOCOMOTION STATIONARY`, speed 0.037 m/s)으로 판정됐다.** 평지·험지 모두
   몸을 세운 채 주저앉음(높이 0.40→0.12 m). 같은 로컬 평가에서 A033 정책은 정상 보행(생존 1.0, 0.42 m/s) → 평가 환경은 정상.
   학습 곡선은 iter 10~60에서 서버 A017과 거의 같다가(지형 3.20/3.21 → 1.62/1.54) 서버는 회복(iter 999 지형 4.25), 1.2는 1.18에 머묾.
   원인 판정은 하지 않았다(설정 효과인지 이 PC 영향인지는 G-A058 행 1로 가린다). 러너는 설계대로 69 case를 전부 잰다.
3. 1.2 결과 폴더에는 20:48 실패 때의 `RESULT_STATUS.txt`(PARTIAL)·`RUNNER_STATUS.txt`가 남아 있다. 재개 실행이
   끝나면 `RESULT_STATUS.txt`는 새로 쓰이지만 `RUNNER_STATUS.txt`(RC=5)는 남을 수 있다 — 판독 때 `RESULT_STATUS.txt`를 본다.

## 6. 작성 PC에 확인 요청

1. **G-A058 뒤 G-A057 나머지 11행을 이 PC에서 자동으로 이어 돌려도 되는가?** (제안서 §6 합의 순서와 같음. 약 4일 소요)
2. **기준 회차 폴더 복사:** 비교 도구·G-A058 판독에 필요하다. 최소 `go2_g_a048_a033_lin_vel_z_m125`,
   `go2_g_a043_a033_lin_vel_z_m15`, 비교표 전체에는 `SWEEP_PLAN.json`의 `searched_arms` 13개.
   → 이 PC `D:\dev\Nconnect\NConnect\workspace\_keep\`에 두면 자동 분석이 다음 주기에 돈다.
3. **G-A058 판독 도구:** 제안서 §3의 규칙(행 1 기록, 행 2·3 두 단위 판정, 우회전 결함 구간)을 계산하는 도구가 저장소에 없다.
   작성 PC에서 만들 것인가, 이 PC에서 만들 것인가.
4. **1.2 결과(움직이지 않는 정책)의 처리:** 러너·사전등록대로 `EXCLUDED_STATIONARY`로 읽히는 것이 맞는지.
   이 행을 이 PC에서 다시 돌리지는 않는다(제안서: 재학습 자동 추가 금지).
5. 임시 화살표 에셋으로 찍힌 영상(명령 화살표 모양만 다름)을 그대로 써도 되는가. 진짜 `arrow_x.usd`는 2차 전달을 요청해 둔 상태다.

## 7. 멈추거나 바꾸는 방법 (사용자용)

- 상태 보기: `powershell -ExecutionPolicy Bypass -File D:\workspace\status.ps1 -Watch 60` (G-A058 행: `-Key go2_g_a058_a048_seed42`)
- 로그: `Get-Content D:\workspace\_keep\<행 폴더>\launcher.log -Wait -Tail 20`
- 자동 시작 취소·순서 변경은 Claude에게 요청한다(대기 스크립트만 멈추면 되고, 진행 중인 학습은 건드리지 않는다).

## 변경 기록 2026-10-01 19:53 — A058 후 정지 (사용자 결정)
- 사용자 결정: G-A058 3행(a043_seed44)이 끝나면 정지한다. G-A057 나머지 11행은 시작하지 않는다.
- `plan_supervisor.sh`를 내리고 `D:\workspace\plan_supervisor_a058_only.sh`로 교체했다. 진행 중이던 G-A058 run_sweep(PID 3753)과 3행 학습은 그대로 유지했다.
- 새 감독은 G-A058 종료까지만 지켜보며 상태 행을 기록한다. 로그는 같은 `plan_supervisor.log`이다.
- 지금까지 멈춤 0회. 1·2행은 DONE(FULL_69_COMPLETE)이고 분석이 저장됐다. 결과 복사와 분석(sync v2)은 그대로 동작한다.
- 위 §0 표의 5번(G-A057 나머지 11행)은 이번 변경으로 **실행하지 않음**이다.

## 변경 기록 2026-10-02 08:50 — 3행 중단, 사용자 판단 대기
- 3행 a043_seed44는 iter 376/1000에서 중단했다. 2026-10-01 20:28 모니터를 끈 뒤로 iter당 약 300초로 느려졌기 때문이다.
  - 원인 근거: 같은 시각 Windows 이벤트(conhost 오류, 화면보호기 오류)와 겹치고, 모니터를 끄거나 켜면 디스플레이 구성이 바뀌어 VRAM이 재배치된다는 추정이다.
  - 폴더는 지우지 않고 보관하기로 했다(이름 변경 예정, 아래 참고).
- 재학습은 하지 않고 사용자 판단을 기다린다. 1·2행 결과를 다른 PC에 전달한 뒤 결정한다.
- 재발 방지: 학습 중에는 모니터 전원 버튼을 쓰지 않는다. 모니터를 끈 상태에서 시작하면 정상이었다(1행).
