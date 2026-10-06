# Go2 로컬 PC 무인 운영 계획·인계 (2026-10-02 ~ 2026-10-06 화)

새 세션은 이 문서부터 읽는다. 상세 이력은 `GO2_LOCAL_PC_RUN_PLAN_20260930.md`의 변경 기록에 있다.

## 0. 한눈에 보기
- **사용자 부재:** 2026-10-02(금)부터 10-06(화)까지. 이 기간에는 Claude가 제어 책임자이다. 실제 제어는 분리 실행된 스크립트가 하고, Claude 세션이 꺼져도 동작한다.
- **실행 순서(2026-10-02 11:06 사용자 정정):** **G-A058은 취소됐다. 3행 `a043_seed44`는 돌리지 않는다.** G-A057 나머지 11행만 실행한다. guardian은 11:21에 시작하도록 걸어 두었다. `plan_controller_v4.sh`의 `SWEEPS`는 G-A057만 남겼고, 원본은 `_keep/plan_controller_v4.with_a058.bak`에 보존했다.
- **완료 표식:** `D:\workspace\_keep\PLAN_FINISHED.txt`
- **예상 시점**(모니터를 건드리지 않을 때, 행당 약 9.2시간): G-A057 11행은 10/6(화) 오후 4~5시쯤 끝난다.

## 1. 사용자 조건 (2026-10-02)
1. 학습이 300 s/iter 이상이면 자동으로 재실행한다.
2. 문제가 생겨도 테스트와 분석을 최대한 많이 마무리한다. 그래서 멈춤 2회 정지 규칙은 없앴다.
3. 속도는 30분마다 확인한다.
4. 그 밖에 필요한 사항은 Claude가 확인해서 추가한다(아래 §2 a~f).

## 2. 자동 구성 (모두 `D:\workspace\`, 패키지·러너 바이트는 변경 없음)

| 스크립트 | 역할 |
|---|---|
| `start_plan.sh 15` | 15분 뒤 guardian을 시작한다. 모니터를 학습 전에 끌 시간을 주기 위한 지연이다. |
| `plan_guardian.sh` | 5분마다 controller, sync v3, speed_watchdog가 살아 있는지 보고, 죽었으면 다시 띄운다. `PLAN_FINISHED.txt`가 생기면 종료한다. |
| `plan_controller_v4.sh` | G-A057만 `run_sweep.sh --inner`로 실행한다(G-A058은 10/2 사용자 지시로 취소). 30분마다 점검한다(아래). |
| `sync_results_to_repo_v3.sh` | 5분마다 완료 행을 `NConnect\workspace\_keep\`로 복사하고 ZIP 해시를 재검사한 뒤 분석을 돌린다. |
| `speed_watchdog.sh` | 1분마다 속도를 기록만 한다. SLOW/RECOVERED와 직전 15분의 앱 오류를 남긴다. |
| 로그온 예약 작업 `Go2PlanGuardian` | 재부팅 뒤 로그온하면 guardian을 시작한다(자동 로그온은 없다). |

**controller v4의 30분 점검 규칙**
- 학습이 300 s/iter 이상이면 재학습한다(사용자 규칙).
- ~~(a) 90 s/iter 이상이 2회 연속이고 남은 학습이 7시간을 넘으면 재학습한다.~~ 2026-10-02 사용자 지시로 삭제했다. 속도 때문에 재학습하는 경우는 300 s/iter 이상일 때뿐이다.
- (b) 학습 로그가 30분 동안 갱신되지 않으면 멈춘 것으로 보고 재학습한다.
- (c) 평가 로그가 60분 동안 갱신되지 않으면 러너를 재시작한다. 평가는 `GO2_RESUME=1`로 이어서 진행한다.
- (d) 재학습은 행당 최대 3회이다. 횟수는 `*_SLOW_ABORTED_*` 폴더 수로 센다. 넘으면 그 행은 그대로 진행한다.
- (e) 환경 오류로 중단되면(rc 20~24) 10분 뒤 재시도하며, 최대 3회이다.
- (f) controller가 (재)시작될 때 이미 돌고 있는 run_sweep이 있으면 그것을 이어받는다. `TRAIN_STATUS.txt`가 없는 행은 이어서 할 수 없으므로 보관 처리한다.
- 아무것도 지우지 않는다. 재학습한 행은 `<이름>_SLOW_ABORTED_<시각>`으로 이름만 바꾼다.

## 3. 결과·분석 위치
- **원본:** `D:\workspace\_keep\go2_g_a05{7,8}_<key>\`와 `GO2_G_A05x_<KEY>_RESULT.zip`(+ `.sha256`)
- **저장소 사본과 분석:** `D:\dev\Nconnect\NConnect\workspace\_keep\`
  - `go2_g_a058_readout\READOUT.md/.json`: 순서 제안 문서 §3 판정, 서버 A048 대비 기록, Isaac 실행 사양
  - `go2_g_a058_readout\FALLS.md`, `FALL_EVENTS.csv`: 완료된 모든 이 PC 행의 case별 낙상 수, 그리고 어디서·어떻게 넘어졌는지(방식·시점·이동거리·계단 단)
  - `go2_g_a057_local_compare\LOCAL_COMPARE.md`: G-A057 각 행 vs 이 PC A048(G-A058 1행)
  - `workspace/training/quadruped/reports/evidence/go2_g_a057_prereg_readout/`: 사전등록 판정
- **로그:**
  - `D:\workspace\_keep\plan_supervisor.log`([ctl]/[guard] 줄)
  - `speed_watchdog.log`
  - `sync_results_to_repo.log`
  - `go2_g_a05x_sweep\SWEEP_STATUS.tsv`

## 4. 현재까지 결과 (2026-10-02 오전)
- **G-A057 1.2:** 완료. 사전등록 판정 EXCLUDED_STATIONARY(웅크린 채 움직이지 않음).
- **G-A058 1행 (A048 s42):** 총점 43.40/70(서버 A048 50.16). 험지 옆걸음 낙상 68/96(서버 16). 15cm ≥2단 6/96(서버 24).
- **G-A058 2행 (A043 s43):** 41.89/70. 15cm ≥2단 0/96이라 개별 판정은 NOT_CANDIDATE. 복합 우회전 낙상은 0이다(보호 목표 충족). 밀침 4방향 낙상이 87/384.
- **G-A058 3행:** 1차 시도는 10/1 20:28 모니터 OFF 이후 약 300 s/iter로 느려져 중단했다. `go2_g_a058_a043_seed44_SLOW_ABORTED_20261002`로 보관했다. **10/2 사용자가 G-A058을 취소해서 재학습은 하지 않는다.**

## 5. 지켜야 할 사용자 원칙
- **비교 기준:** 계단은 서버 A043, 험지·밀침·우회전은 서버 A048(50.16)이다. A033은 비교 기준이 아니다(보상 출발점일 뿐이다).
- **표 주제 통일:** 낙상을 다루면 모든 열을 낙상으로, 성공을 다루면 모든 열을 성공으로 쓴다. 낙상은 어디서·어떻게 넘어졌는지까지 보여 준다. 목적은 왜 넘어졌는지 분석하는 것이다.
- **관측과 원인 구분:** 관측 사실과 원인 추정을 구분한다. 루트 `AGENTS.md` 분석 순서를 따른다.
- **모니터:** 학습 중 모니터 전원 버튼은 금지이다. 모니터 ON/OFF가 디스플레이를 재구성하고, 이것이 VRAM 재배치를 일으켜 감속한다(추정). 근거는 같은 시각의 conhost와 KEPCO 화면보호기 오류이다.
- **보고 방식:** 자동화를 약속했으면 되묻지 말고 끝까지 자동으로 만든다. 상태를 묻는 질문에는 확인한 사실로 답한다.
- **제출 후보 아님:** 이 PC 정책은 탐색용이다. 제출 후보가 아니다.

## 6. 새 세션이 할 일
1. **상태 확인:**
   - `tail -40 /workspace/_keep/plan_supervisor.log`
   - `cat /workspace/_keep/go2_g_a05{8,7}_sweep/SWEEP_STATUS.tsv`
   - `cat /workspace/_keep/speed_watchdog.log`
   - `ls -d /workspace/_keep/*SLOW_ABORTED*`
   - `ps -ef | grep -E "plan_(guardian|controller)|sync_results|speed_watchdog"`
2. **돌고 있으면:** 개입하지 않는다. 사용자가 물으면 위 사실로 보고한다.
3. **멈춰 있고 `PLAN_FINISHED.txt`도 없으면:** `bash /workspace/plan_guardian.sh`를 nohup으로 실행해 재개한다. 단, 모니터 상태를 먼저 확인한다.
4. **사용자 복귀 보고:** 아래 항목을 순서대로 정리한다.
   - 행별 완료와 재학습 이력
   - G-A058 재현성 판정(3행 포함)
   - 낙상 비교: A048/A043 기준, 어디서·어떻게
   - G-A057 각 행 vs 이 PC A048
   - 실패 행과 원인
5. **열린 항목:**
   - 서버 A048·A043 원본 결과 폴더가 없어 `go2_g_a057_sweep_compare.py`가 막혀 있다. 서버 A043의 case별 낙상도 일부만 있다.
   - `arrow_x.usd`는 임시 대체 파일이다(영상 화살표만 해당).
   - 이 PC 결과가 서버보다 낮은 원인은 미확정이다(1행 기준 총점 −6.8, 험지 옆걸음 낙상 16 → 68).

## 7. 상태 기록 2026-10-06 09:00
- G-A057은 12행 중 5행이 끝났다(1.2, p1p4, p1p6, m0p04, m0p08). 모두 FULL_69_COMPLETE이다. 지금 `feet_air_time_p0p01`을 학습 중이며 1000 iter 중 432, 약 308 s/iter이다. 나머지 6행은 아직 시작하지 않았다.
- 관측: 느려진 행은 매번 iter 40~41에서 Collection time이 약 20초에서 약 315초로 뛰었다(p1p6, m0p04, p0p01 3회). 정상 행(p1p4, m0p08)은 끝까지 약 20초였다. 이 시각 GPU 메모리는 5806/6144 MiB였다. 원인은 확정하지 않았고, VRAM이 넘친다는 설명은 추정이다.
- `feet_air_time_p0p01`은 재학습 3회 한도를 다 썼다. 사용자 결정(10/6)으로 그대로 계속한다. 학습은 10/8 오전쯤 끝날 것으로 본다. 그 뒤 6행이 남는다.
