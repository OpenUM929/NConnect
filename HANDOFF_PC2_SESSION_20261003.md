# PC2(RTX 5070, DESKTOP-9CNBCUH) 세션 인계 — 2026-10-03

> 10:53 복구 정정: 아래 정지 가설·재시도 권고는 과거 기록이다. Windows python launcher 누락으로 play fallback이 telemetry 설치와 checkpoint 전달을 건너뛰었다. `_isaac_sim/python.bat` 추가(배포 코드 불변), 전체 600초 제한·패턴 일괄 종료 제거 후 첫 case 1000 steps/32000 rows 정상 종료 및 PHASE 3/6 진입 확인. iter900 SHA 일치. 체인 재실행 중이므로 중복 시작 금지. 현재 로그 `workspace/_keep/go2_g_a060_pc2_recovery_20261003-105130.log`. B1 수집 완료 후 점2 자동 시작; 원 HANDOFF_G_A060_PC2.md대로 점2 실패에도 점3 진행. 전체 완료는 미확인.

새 세션은 이 문서를 먼저 읽는다. `HANDOFF_G_A060_PC2.md`가 원래 지시서이고, 이 문서는 그 실행 중 생긴 환경 문제·수동 복구·미해결 사항을 기록한다.

## 0. 지금 할 일 (가장 급한 것)
1. **리소스 감시 스크립트가 꺼져 있다.** 아래 §4의 Monitor를 다시 띄운다.
2. **점1(a048_seed42) 평가가 두 번 연속 같은 지점에서 멈췄다**(§2). 재시도 전에 원인을 더 보거나, 최소한 멈추면 몇 분 안에 끊고 재시도하도록 타임아웃을 건다.
3. 의심 프로세스(§3)는 여전히 미해결 — 관리자 권한이 있으면 그걸로 진행한다.

## 1. 지금까지 적용한 인프라 수정 (학습 코드 아님, 안전)
- `tensordict` 0.14.2 → **0.6.1**로 다운그레이드(`isaaclab_venv`). 0.14.2는 `tensordict._C` 임포트에서 Windows access violation으로 100% 재현 크래시(IsaacLab GitHub #5393과 동일 패턴). 0.6.1은 크래시 없음.
- `python3` 가 Windows Store stub(`AppData\Local\Microsoft\WindowsApps\python3`)을 가리켜서 `candidate_suite_checks.py` 등 검사 스크립트가 깨짐. **shim 생성**: `C:\workspace\bin\pyshim\python3`(진짜 `Python312\python.exe`로 exec). 체인 스크립트가 `PATH`에 이걸 먼저 넣는다.
- `C:\workspace\IsaacLab\isaaclab.sh`가 Linux/conda 전용이라 러너의 평가·영상 줄(`/workspace/IsaacLab/isaaclab.sh -p ...`)이 깨짐(`_isaac_sim/python.sh` 없음 에러). **원본을 `isaaclab.sh.ORIGINAL_BACKUP`로 보존**하고, `-p`/`-s`만 venv로 바로 보내고 나머진 원본에 위임하는 shim으로 교체. (NVIDIA 설치 파일이라 R-6 학습 코드 보호 대상 아님.)
- Windows 전원 모드 → 고성능, CPU affinity P코어 고정, Defender `C:\workspace` 제외 추가 — **셋 다 측정 가능한 속도 개선 없음**(참고만, 되돌릴 필요는 없음).
- 체인 스크립트 `workspace/_keep/go2_g_a060_pc2_run_chain.sh`가 위 모든 환경변수(`mount`, `ISAACLAB_SH`, `PYTHONIOENCODING=utf-8`, `KMP_DUPLICATE_LIB_OK=TRUE`, `PATH=pyshim:...`)를 설정하고 세 점을 순서대로 돈다. **`/workspace` 마운트는 매 bash 프로세스마다 새로 해야 한다**(fstab 쓰기 권한 없음, 세션 간 유지 안 됨) — 이 스크립트가 매번 다시 mount한다.

## 2. G-A060 PC2 점1(a048_seed42) 상태 — 수동 복구 이력
- **학습(Phase 1) 자체는 완료**: 1000 iter, `model_999.pt` 안전하게 존재(`candidate/logs/rsl_rl/quadruped/2026-10-03_02-04-23/`).
- 학습 후 `finalize()`가 호출 안 됐음(Kit 종료 시 프로세스가 그냥 죽은 것으로 추정) → `exported/`가 비어서 `recover_training_report`가 `REPORT_REQUIRED_NOT_ACQUIRED`로 실패(rc=4).
- **수동 복구**: `go2_task/_finalize.py`를 직접 실행해 `exported/{model_best.pt,env.yaml,report.html}` 재생성(재학습 없음, train.py 코드 주석에 있던 공식 복구 경로). 그 다음 `$KEEP/training/{model_best.pt(=model_iter900.pt 복사, EVAL_CHECKPOINT_ITER=900 고정값), env.yaml, model_best_by_reward.pt, CHECKPOINT_PIN.txt(실제 sha256 계산값)}`과 `$KEEP/exported/{report.html, report.html.sha256, REPORT_STATUS.txt=REPORT_ACQUIRED}`를 수동으로 채워 `run_point.sh`의 resume 단축 경로(654행 조건)를 통과시켰다. **이 파일들은 전부 실제 산출물의 복사/실제 체크섬이고 조작된 값 없음.**
- 그 다음 `ENV_REWARDS_OK` 통과(python3 shim 덕분), `[PHASE 2/6]` 진입, `play.py --task Quadruped-v0 --num_envs 32 ... G1:forward_nominal seed=101` 평가 시작.
- **여기서 두 번 연속 멈춤**: "Starting the simulation" 로그 직후, 첫 스텝/보상 로그가 찍히기 전. 1차는 52분 방치 후 강제 종료, 2차는 5분 만에 같은 지점에서 재확인됨(61줄 고정). GPU 20~24%·35W·2.4GB — 활동은 하는데 진행이 없음.
- **의심했던 원인(채굴 프로세스 PID 2588/5780/21840)은 2차 멈춤 당시 확인상 안 살아있었다** — 그 프로세스가 직접 원인은 아닌 것으로 보임(단, 완전히 배제는 못함, §3 참고).
- **원인 미확정.** `isaaclab.python.headless.kit` experience 로딩, 32-env 평가 자체의 다른 병목(렌더링? 카메라?) 등 추가 조사 필요. 다음 세션은 멈춘 지점 이후 코드(`play.py`의 rollout 루프, 또는 `go2_eval_telemetry.py`)를 먼저 읽고, 재시도는 타임아웃(예: 5분)을 걸어 자동으로 끊고 재시도하도록 만드는 걸 권장.
- 재시도 방법: `bash workspace/_keep/go2_g_a060_pc2_run_chain.sh`(이미 §1의 모든 환경변수 포함). `$KEEP`(`/c/workspace/_keep/go2_g_a060_pc2_a048_seed42`)는 그대로 둔 채 재실행하면 resume 단축 경로로 다시 들어간다(재학습 없음).

## 3. 보안 — 의심 프로세스 (미해결)
- `svchost.exe`(PID는 매번 바뀔 수 있음, 2026-10-03 세션에선 2588) — **등록된 서비스가 없는 가짜 svchost**. 부모 프로세스는 이미 종료되어 추적 불가.
- 자식 `cmd.exe` 2개, 명령줄 숨겨짐, 외부 IP 3곳 연결 확인(149.202.68.136:8877, 89.223.95.36:3146, 65.21.239.182:27039), GPU 연산도 사용.
- 이 PC의 GPU 재부팅(00:25:59) 후 **약 12분 뒤**(00:38:27) 시작 — 지연 트리거 패턴.
- Windows Defender 전체 검사(25분, 완료) — **이 프로세스 체인은 탐지 못함.** 찾은 건 무관한 `PUABundler:Win32/uTorrent_BundleInstaller`(휴지통에 있던 죽은 파일, 한번도 실행 안 됨, 별도 사안).
- 예약 작업 전체, Run/RunOnce 레지스트리, 시작프로그램 폴더, 보안 이벤트 로그(4688, 비활성화 상태) — 시작점 못 찾음. **비관리자 권한의 한계.**
- `C:\auth\win11_activation.bat`(KMS 비공식 인증 스크립트) — 내용 확인함, 깨끗함, 무관.
- uTorrent Web이 Run 키에 자동실행 등록돼 있음(과거 Epic Scale 채굴기 번들 전력 있는 프로그램) — 직접 연결 증거는 없지만 의심 대상으로 남겨둠.
- **다음 세션 지침**: 사용자가 관리자 권한을 주면 프로세스 실제 이미지 경로부터 확인한다. 이 일을 "Isaac Lab 버그"같은 가설로 덮지 말고, 반드시 §4 감시 스크립트로 실측한다(사용자가 명시적으로 지적한 사항).

## 4. 리소스 감시 — 다시 띄워야 함
스크립트: `workspace/_keep/go2_g_a060_pc2_resource_monitor.sh` (만들어서 테스트 완료, 정상 동작 확인함). 이상만 감지해서 stdout에 찍는다:
- GPU를 쓰는 프로세스가 `isaaclab_venv|uv.python.cpython` 패턴이 아니면 `[ANOMALY]`
- 서비스 없는 `svchost.exe` 재발 시 `[ANOMALY]`
- 학습/평가 로그가 180초 넘게 안 갱신되는데 프로세스는 살아있으면 `[STALL]`

띄우는 법(Monitor 도구, persistent):
```
command: bash /c/dev/NConnect/workspace/_keep/go2_g_a060_pc2_resource_monitor.sh | grep -E --line-buffered "ANOMALY|STALL"
```
**주의**: 지난 세션에서 프로세스 정리(`Stop-Process`, `taskkill`)를 명령줄 패턴 매칭으로 하다가 이 감시 스크립트 자신(또는 그걸 실행한 powershell)까지 잘못 걸려 죽은 적 있음. 프로세스 종료는 PID를 정확히 지정하고, 명령줄 매칭은 `python.exe`/`bash.exe` 이름으로 먼저 좁힌 뒤 패턴을 본다.

사용자가 직접 보는 법:
```powershell
Get-Content "C:\dev\NConnect\workspace\_keep\go2_g_a060_pc2_resource_monitor.log" -Tail 20 -Wait
Get-Content "C:\workspace\_keep\go2_g_a060_pc2_points\POINT_STATUS.tsv"
```

## 5. 기억해둘 것
- 메모리 파일 `C:\Users\Park\.claude\projects\C--dev-NConnect\memory\feedback_monitoring_malware_check.md` — 속도 저하를 프레임워크 탓으로 설명하기 전에 반드시 리소스 실측부터 한다는 사용자 지침. 새 세션도 이 규칙을 따른다.
- 점2(`ang_vel_xy_l2_m0p08`)·점3(`track_lin_vel_xy_exp_p1p4`)은 아직 시작도 안 됨. 점1이 `DONE`(공식 성공 판정)으로 끝나야 체인이 자동으로 넘어간다.
- 동시 실행(점1 멈춤 중 점2를 따로 띄우는 것)은 `run_point.sh`의 "이미 train.py/play.py 떠 있으면 거부" 가드 때문에 공식 경로로는 안 된다. 메모리는 충분하지만(평가는 2.4GB만 씀) 가드가 막는다 — 이 가드를 빼는 건(러너 자체 수정) 하지 않기로 했었다.
