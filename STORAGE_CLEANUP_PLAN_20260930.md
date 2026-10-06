# 저장 공간 정리 계획 (2026-09-30)

- 상태: 사용자가 A+B+C+D 전체를 승인했다(2026-09-30). 실행 결과는 §4에 있다.
- 이전 검토 문서 `LARGE_FILES_DELETION_REVIEW.md`(2026-09-04)는 Q1~Q5에 답을 받지 못했다. 이 문서가 그 문서를 대체한다.

## 1. 실측 결과 (2026-09-30)

프로젝트 전체 37 GB = `workspace` 25.1 GB + `.git` 12.3 GB + 기타 0.2 GB.

| 종류 | 용량 | 비고 |
|---|---:|---|
| `steps.csv` (평가 telemetry) | 14.05 GB / 1,665개 | 실제로 가장 큰 항목 |
| `.zip` (서버 결과 원본) | 8.56 GB / 244개 | 결과 ZIP 하나에 영상은 약 10%, 나머지는 steps.csv |
| `.mp4` 영상 (압축 해제본) | **1.12 GB / 265개** | 영상만 지우면 전체의 약 3%만 줄어든다 |
| `.git` 참조 없는 객체 | **8.07 GB** (디스크 기준) | 어떤 커밋에서도 참조하지 않는 blob 4,017개 |

영상 265개 위치: `_keep` 578 MB·169개, `server_returns` 212 MB·46개, H1 `exported` 153 MB·21개, H1 `reports/S0*` 121 MB·16개(git 추적 중), 기타 소량.

바이트가 같은 중복 사본은 842개, 7.14 GB다. 이 중 run 폴더마다 복사된 A033 기준선 자료는 분석 도구가 폴더 경로로 읽으므로 지우지 않는다.

## 2. 단계별 계획

### 단계 A — 중복 사본 삭제 (정보 손실 없음) · 약 3.9 GB

- 대상: `_keep`에 같은 바이트 사본이 있는 `server_returns/*`·루트 파일 452개(영상 48개·0.22 GB 포함). 목록은 `STORAGE_CLEANUP_STEP_A_LIST_20260930.tsv`에 있다.
- 폴더별 용량: `server_returns/G-A027` 1.31 GB, `go2_feet_air_time_020_v1_full_260901` 0.74 GB, `train_260831-06_run05cfg_10000` 0.64 GB, `go2_default_vs_pilot_v1_partial` 0.52 GB, `go2_default_vs_pilot_v1_full` 0.46 GB, 기타 0.24 GB.
- `_keep` 사본을 남기는 이유: `tools/`의 분석 도구와 계약 테스트가 `_keep` 경로를 읽는다. `server_returns` 경로를 읽는 도구는 `go2_seed_sensitivity.py` 하나이고, 그 도구가 읽는 파일(`G-A027/approved/.../quadruped_rewards.py`)은 이 목록에 없다.
- 실행 조건: 삭제 직전에 각 파일과 `_keep` 사본의 SHA를 다시 비교하고, 일치할 때만 지운다. 삭제 전후 `git status`와 삭제 목록을 `ARTIFACT_MANAGEMENT.md`에 작업 ID로 기록한다.

### 단계 B — 분석이 끝난 run의 영상 (요청 대상) · 약 0.6~0.9 GB

- 규칙: 결과 ZIP 안에 **같은 경로·같은 크기**로 들어 있는 영상만 압축 해제본에서 지운다. 다시 봐야 하면 ZIP에서 풀면 된다.
- Go2 `_keep/*/evaluation/**/videos`: 판독이 끝나 REPORTED로 기록된 run(A031~A050, A055, 초기 a010~a025, pilot/default/chain01/feet_air_time_020)이 대상이다. ZIP이 없는 run(a016·a018·a020·a021·a022·a024 등)은 제외한다.
- 유지: `_keep/go2_g_a056_a043_diag_replay/video`, `_keep/go2_g_a052_*`, `reports/evidence/go2_g_a056_diag_20260928/` 영상. 현재 험지·계단 원인 분석(`GO2_TUNING_POLICY_A_B_20260930.md` 등)이 이 영상들을 근거로 인용한다.
- 유지: 곧 들어올 G-A057·G-A058 결과 영상은 판독 전까지 지우지 않는다.
- H1 `training/humanoid/exported/play_video_*.mp4` 21개(153 MB): 18개(135 MB)는 `reports/S0*`에 같은 바이트 사본이 있어 지운다. 나머지 3개는 H1 제출 이력(D52 동결, 공식 57.45 전사)과 무관한 8/28~29 초기 재생이다. 이 3개도 삭제 후보에 넣을지 한 번 확인한다.
- 이 단계만으로는 공간이 1 GB 미만으로 줄어든다. 공간이 필요하면 단계 C와 D를 진행해야 한다.

### 단계 C — 종료된 run의 압축 해제 폴더 (ZIP은 보존) · 약 3~4 GB

- 대상: 결과 ZIP이 있고, 현재 `tools/`의 어떤 도구·테스트도 경로를 참조하지 않는 run의 해제 폴더. 후보는 `go2_default_vs_pilot_v1`(1.01 GB), `go2_pilot_v2_baseline`(0.64 GB), `go2_feet_air_time_020_v1`(0.51 GB), `go2_track_lin_vel_120_v1`(0.08 GB), ZIP이 있는 초기 a010·a013·a015·a025다.
- `go2_a017_full_suite`(1.25 GB)는 `go2_eval_resolution.py`와 `verify_go2_a027_harvest.py`가 참조한다. 두 도구를 더 이상 돌리지 않는다면 대상에 넣을 수 있다.
- `go2_chain01_baseline`(0.64 GB)은 대응하는 ZIP을 확인하지 못했다. 확인되기 전에는 제외한다.
- 실행 조건: ZIP 목록과 해제 폴더의 `SHA256SUMS.txt`를 대조해 모든 파일이 ZIP에 있을 때만 폴더를 지운다.
- 규칙 대조: `AGENTS.md`는 "과거 회수 snapshot은 불변 증거로 보존"을 요구한다. 원본 ZIP을 남기므로 이 규칙에 맞는다고 판단한다. 해제 폴더는 파생본이다.

### 단계 D — `.git` 정리 · 약 8 GB

- `git reflog expire --expire-unreachable=now --all && git gc --prune=now`로 참조 없는 객체 8.07 GB를 지운다. 작업 트리와 커밋 이력은 바뀌지 않는다.
- 잃는 것: 커밋하지 않은 채 스테이징했다가 취소한 파일은 복구할 수 없게 된다.
- 주의: 오늘 조사 중 "paging file too small" 오류가 났다. gc는 메모리를 많이 쓰므로 다른 프로그램(opencode 등)을 닫고 실행한다.

### 이번 계획에서 하지 않는 것 (별도 결정 필요)

- **원본 결과 ZIP 삭제:** 불변 증거 규칙과 충돌한다. 공간이 더 필요하면 삭제 대신 외장 디스크나 클라우드로 옮기는 방안을 따로 정한다.
- **git 추적 중인 대용량 파일:** 현재 커밋에 `steps.csv` 976개와 mp4·zip·gz 400개가 추적되어 있다(원본 크기 합 13.18 GB). `git rm --cached`로 추적을 끊어도 이력에 남아 로컬 용량은 줄지 않는다. 이력을 다시 쓰려면 원격 저장소(`origin`)에 강제 push가 필요하다.

## 3. 예상 효과

| 단계 | 줄어드는 용량 | 정보 손실 |
|---|---:|---|
| A 중복 사본 | ~3.9 GB | 없음 (같은 바이트 사본이 남는다) |
| B 영상 | ~0.6~0.9 GB | 없음 (ZIP에서 다시 풀 수 있다) |
| C 해제 폴더 | ~3~4 GB | 없음 (ZIP 보존, 풀면 복원된다) |
| D .git | ~8 GB | 커밋되지 않은 옛 스테이징 내용 |
| 합계 | **약 15~17 GB (37 GB → 약 20~22 GB)** | |

단계 B와 C는 실행할 때 ZIP 목록과 대조해 정확한 용량을 다시 계산한다. 위 값은 추정이다.

## 4. 실행 결과 (2026-09-30)

실행 스크립트는 삭제 직전에 SHA256(단계 A, H1 영상)와 ZIP 항목의 크기·CRC(단계 B)를 다시 대조했다. git이 추적하는 파일은 건너뛰었다. 행별 기록은 `STORAGE_CLEANUP_DRYRUN_20260930.tsv`(모의 실행)와 `STORAGE_CLEANUP_RESULT_20260930.tsv`(실제 삭제)에 있다. 삭제 후 `git status`에서 추적 파일 삭제는 0건이다.

| 단계 | 결과 |
|---|---|
| A | 2개·0.62 GB 삭제. **450개·3.28 GB는 git 추적 파일이라 건너뜀.** 9월 4일 문서의 "untracked" 전제는 이후 커밋으로 더 이상 맞지 않는다. |
| B | 영상 100개·0.32 GB 삭제(ZIP에 같은 CRC로 있는 Go2 영상과 H1 `exported` 중복분). 56개·0.23 GB는 git 추적 파일이라 건너뜀. 25개·0.11 GB는 ZIP에 없어 보존. |
| C | 0건. 후보 폴더 전부가 `tools/`의 옛 판독·빌더 도구에서 경로로 참조되어 "참조 없음" 조건을 통과하지 못했다. H1 run 폴더 3개는 원본이 ZIP이 아닌 tar.gz라 대조 대상이 아니었다. |
| D | `git reflog expire` 완료. `git gc --prune=now`는 진행 중(메모리 부족으로 Claude Code가 감싼 셸을 종료했지만 git 프로세스는 계속 실행 중). |

### 남은 결정

- **git 추적 중복 3.5 GB(A 450개 + B 56개):** 작업 트리에서 지우려면 `git rm` 후 커밋해야 한다. 파일 내용은 git 이력에 남아 언제든 복원할 수 있다. 커밋이 필요하므로 별도 승인이 필요하다.
- **단계 C:** 옛 도구의 참조를 무시하고 종료된 run의 해제 폴더를 지울지 결정해야 한다. 지우면 해당 도구를 다시 돌리기 전에 ZIP을 풀어야 한다.

## 5. 후속 실행 — 남은 결정 1·2항 (2026-09-30, 사용자 지시 "1항 2항 모두 처리")

- `git gc` 완료: `.git` 12.3 GB → 3.5 GB(팩 1개 3.43 GiB, 느슨한 객체 0개).
- 브랜치 `chore/storage-cleanup-20260930`, 커밋 `784663b`에서 git 추적 파일 2,837개를 삭제했다. 내용은 git 이력과 보존한 ZIP에 남아 있다.
- 1항: A·B 추적 중복 3.51 GB. 삭제 직전에 SHA256(중복 사본)과 ZIP 크기·CRC(영상)를 다시 대조했고 전부 일치했다.
- 2항: 종료된 초기 run의 해제 폴더를 **파일 단위**로 처리해 2.80 GB를 삭제했다. ZIP과 크기·CRC가 같은 파일만 지웠다.
  - ZIP 생성 뒤 내용이 바뀐 `launcher.log` 등은 남겼다.
  - 대응 ZIP이 없는 chain01, a010_v2, a016~a024, 5var_1000(1.46 GB)은 보존했다.
- 보존: 현재 분석이 쓰는 run(A017 suite, A031~A056)과 H1 run 폴더.
- 행별 기록: `STORAGE_CLEANUP_DRYRUN2_20260930.tsv`, `STORAGE_CLEANUP_RESULT2_20260930.tsv`.
- 결과: 프로젝트 37.4 GB → **21.9 GB**(workspace 18.2 GB, .git 3.5 GB).
- 브랜치 주의: master로 체크아웃하면 삭제한 파일이 작업 폴더에 다시 생긴다. 정리 상태를 유지하려면 이 브랜치를 master에 fast-forward 병합한다.
