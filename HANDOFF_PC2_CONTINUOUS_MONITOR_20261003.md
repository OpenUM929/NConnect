# PC2 연속 감시·Go2 자동 재개 인계 (2026-10-03)

## 0. 다음 세션 첫 판단

**현재 Go2 체인은 이미 실행 중이다. 중복 실행·재부팅·수동 `play.py` 실행을 하지 않는다.**

- 실행 체인: PID `25752` (Git Bash), 시작 `2026-10-03T10:51:30+09:00`
- 체인 로그: `workspace/_keep/go2_g_a060_pc2_recovery_20261003-105130.log`
- 점 상태/상세 로그: `C:/workspace/_keep/go2_g_a060_pc2_points/POINT_STATUS.tsv`, `.../logs/`
- 현재 점: B1 `a048_seed42`의 full 69-case 평가. 첫 case `G1/forward_nominal/seed101`은 `EVAL_RC=0`, 1000 steps, 32000 rows, `summary.json completed=true`까지 확인됐다.
- 현재 GPU compute 프로세스: PID `6240`, `uv` Python. 감시 allow-list(`uv.python.cpython`)에 포함되며 채굴 서명은 아니다.

## 2026-10-03 15:28 최신 복구 — 아래 과거 PID/진행률보다 우선

- 재개 체인 PID **24112**, 로그 `C:/workspace/_keep/go2_g_a060_pc2_points/logs/a048_seed42_20261003-152543.log`. 중복 재실행 금지.
- 첫 영상 Vulkan RTX 초기화 access violation을 PC2 영상 자식 전용 **Direct3D12 + multiGpu 비활성 + Kit GPU1(RTX5070)** 설정으로 우회했다. `tools/pc2_video_python_launcher.py`를 외부 `C:/workspace/IsaacLab/_isaac_sim/python.bat`에서 호출. 원본 `.before_single_gpu` 보존. 학습/telemetry 인자는 변경하지 않는다.
- 진단 실제 영상 exit0, 원래 체인 G2 좌/우회전 두 영상까지 생성·디코딩 확인(1080p, 50fps, 9.98초). 69-case와 sentinel은 resume 재사용. 나머지 영상/패키징/점2/점3 완료는 아직 미확인. 영상 파일 디코딩은 행동 성능 판정이 아니다.
- 단일 GPU만 끈 startup smoke는 Intel fallback이었으므로 해결 증거가 아니다. NVIDIA+Vulkan은 재현됐고 NVIDIA+D3D12에서 영상 생성 성공. 드라이버 자체 원인/다운그레이드 필수는 입증되지 않았다. performance 옵션의 과거 수동 패치는 runner checksum 복원으로 사라져 실제 시험되지 않았다.
- 검증: 런처 4 tests, 체인 5 tests, bash -n, Python compile, diff check. GPU1은 이 PC의 Kit 열거 순서이며 CUDA 번호가 아니다. 하드웨어 열거 변경 시 재검증한다.
- B1 수집 정상 완료 후 점2, 점2 실패 여부와 무관하게 점3 순서는 유지. 실행 중 런처/배포 파일 수정 금지.

## 1. 체인이 보장하는 순서

`a048_seed42` 수집·영상·결과 ZIP이 정상 완료(`rc=0`)되어야 점2 `ang_vel_xy_l2_m0p08`이 시작된다. 점2의 성공/실패와 관계없이, 사용자 인계 `HANDOFF_G_A060_PC2.md`에 따라 점3 `track_lin_vel_xy_exp_p1p4`을 한 번 실행한다. 세 점 이후에는 **새 reward 값·네 번째 튜닝을 자동으로 고르거나 실행하지 않는다.** 결과 해석은 반드시 관측 → 낙상 원인 검토 → 강좌 보상 설명 → 기존 시험 반례 순서로 한다.

체인 파일 `workspace/_keep/go2_g_a060_pc2_run_chain.sh`은 다음을 고쳤다.

- 전체 점을 600초에 중지하던 timeout 제거
- 명령줄 문자열로 chain/monitor까지 죽일 수 있던 광범위 `Stop-Process` 제거
- Python 자식 런처 `C:/workspace/IsaacLab/_isaac_sim/python.bat` 추가로 telemetry hook·고정 checkpoint 전달 경로 복구
- B1 실패 시 점2·점3 차단, 점2 실패 시에도 점3 실행, 각 종료 코드는 체인 종료 코드로 보존

배포 `train.py`, `play.py`, task 코드, 고정 runner, 발행 ZIP은 수정하지 않았다.

## 2. GPU 채굴 감시·정지

실행 스크립트: `workspace/_keep/go2_g_a060_pc2_resource_monitor.sh`

- 매 20초 `nvidia-smi` compute-apps를 조회한다.
- allow-list 밖 GPU 프로세스는 `[ANOMALY]`로 로그 기록 후 그 **PID만** `Stop-Process -Force` 한다.
- 서비스에 연결되지 않은 `svchost.exe`는 자식 PID와 함께 종료를 시도한다.
- 채굴 명령 서명 `progpowz`, `woolypooly`, `ssl-maimai`, `rx/0`은 관리자 읽기 검사로 별도 확인한다.
- monitor log: `workspace/_keep/go2_g_a060_pc2_resource_monitor.log`

확인된 과거 악성 자동 실행은 `GoogleUpdateTaskSYSTEM` 및 `C:/ProgramData/Google`이었고, 08:52~08:55에 task·명시적 Defender exclusion·파일을 제거했다. 이 제거는 재발 부재 보증이 아니다. 과거 제거 결과는 `.omx/diagnostics/miner-remediation-20261003/result.json`과 `miner-file-removal-20261003/result.json`이다.

## 3. 다음 세션의 3분 점검 순서

1. **먼저 체인이 살아 있는지** 확인한다. 살아 있으면 상태만 읽고 재실행하지 않는다.
   ```powershell
   Get-Process -Id 25752 -ErrorAction SilentlyContinue
   Get-Content C:\dev\NConnect\workspace\_keep\go2_g_a060_pc2_recovery_20261003-105130.log -Tail 30
   Get-Content C:\workspace\_keep\go2_g_a060_pc2_points\POINT_STATUS.tsv -Tail 10
   ```
2. 감시 로그의 최신 시각과 `[ANOMALY]`, `[KILLED]`, `[STALL]`만 확인한다.
   ```powershell
   Get-Content C:\dev\NConnect\workspace\_keep\go2_g_a060_pc2_resource_monitor.log -Tail 60
   ```
3. GPU process와 채굴 서명을 관리자 권한으로 읽는다. **발견된 서명 PID 이외에는 종료하지 않는다.**
   ```powershell
   nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
   Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'progpowz|woolypooly|ssl-maimai|rx/0' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine
   ```

## 4. 재개 규칙

- chain PID가 살아 있으면: **재개 금지**. case 수·최근 로그만 관찰한다.
- chain PID가 없고 B1/점2/점3이 `DONE` 또는 `SKIP_DONE`이 아니면: `POINT_STATUS.tsv`와 마지막 `RUNNER_STATUS.txt`를 읽어 원인을 기록한 뒤 아래 한 줄을 **한 번만** 실행한다. 완료 case는 runner resume이 건너뛴다.
  ```powershell
  Start-Process 'C:\Program Files\Git\bin\bash.exe' -ArgumentList '/c/dev/NConnect/workspace/_keep/go2_g_a060_pc2_run_chain.sh' -WorkingDirectory 'C:\dev\NConnect' -WindowStyle Hidden
  ```
- `[STALL]` 하나만으로 chain을 종료하지 않는다. telemetry가 실제 case `steps.csv`·`summary.json`을 만들고 있는지 먼저 확인한다.
- `[ANOMALY]` 또는 `[KILLED]`가 나오면, 해당 시각의 GPU/프로세스 로그·PID·명령줄을 보존한 뒤 Go2 실행이 계속 살아 있는지 확인한다. 악성 PID만 종료된 경우 chain은 재시작하지 않는다.
- `EVAL_RC=0`, `summary.json`, `steps.csv`가 없으면 그 case는 완료가 아니다.

## 5. 검증과 금지

- 체인 테스트: `python tools/test_go2_pc2_chain_recovery.py` (5 tests)
- 문법: `bash -n workspace/_keep/go2_g_a060_pc2_run_chain.sh`
- 모델/정책 identity는 `C:/workspace/_keep/go2_g_a060_pc2_a048_seed42/training/CHECKPOINT_PIN.txt`와 평가 `identity.json`을 SHA로 대조한다.
- 새 평가·신규 튜닝 결과는 report.html, 69 case telemetry, 영상 10편, 결과 ZIP/SHA 회수 전에는 완료·성능 판정으로 말하지 않는다.
- `VIDEO_OBSERVED`, 내부 정량, `OFFICIAL_RESULT`를 서로 승격하지 않는다.

## 6. 현 시점 한계

체인 실행과 첫 telemetry case의 정상 완료만 확인됐다. B1 full suite, baseline/sentinel, 영상, 패키징, 점2·점3은 아직 완료/성능 판정이 아니다. 원인 분석 및 다음 보상값 선정도 아직 수행하지 않는다.
