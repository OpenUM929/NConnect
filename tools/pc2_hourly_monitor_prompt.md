# NConnect PC2 시간별 HANDOFF 감시 작업

이 실행은 PC2의 한 번짜리 감시 주기다. 질문하거나 승인 대기하지 말고, 루트 `AGENTS.md`의
`PC2 작업 인계 — HANDOFF 자동 실행 계약`과 각 HANDOFF 문서를 그대로 따른다.

1. `C:\dev\NConnect`에서 `git pull --ff-only`를 실행한다.
2. `workspace/_keep/pc2_handoff_ledger.tsv`, `workspace/_keep/author_pc_ledger.tsv`,
   루트 `HANDOFF_*_PC2.md` 머리말을 읽는다.
3. 먼저 현재 실행 중인 `train.py`·`play.py` 및 `/workspace/_keep/*/BATCH_RUN.log` 상태를 확인한다.
   학습이 진행 중이면 새 학습을 시작하지 않는다.
4. 진행 중 작업에서 완료된 점의 결과가 있으면 해당 HANDOFF §4대로 즉시 회수한다.
   100MB 초과 ZIP은 95MB parts로 나누고 원본 ZIP은 커밋하지 않는다. SHA, `report.html`,
   필수 영상, `FULL_69_COMPLETE`를 확인한 결과만 회수 완료로 기록한다.
5. 배치가 끝났으면 PC2 원장에 `DONE` 또는 `FAILED<TAB>rc`를 append하고 commit/push한다.
   직후 다시 `git pull` 및 HANDOFF 스캔을 한 번 수행한다.
6. 실행 중인 학습이 없으면, 머리말이 있고 `STATUS: READY`이며 PC2 원장에 없는 작업 중
   START_MARKER가 충족된 가장 작은 WORK_ID를 선택한다. 패키지 SHA와 R-6를 확인하고,
   원장 `STARTED`를 먼저 commit/push한 뒤 HANDOFF의 기존 실행 한 줄로 시작한다.
7. PC2는 성능 판독이나 다음 reward 값 선택을 하지 않는다. 배포 `train.py`, `play.py`,
   `*_task/`와 reward 파일을 임의 수정하지 않는다. 새 실행 프로그램을 만들지 않고 제공된
   패키지·빌더·러너만 사용한다.
8. 이번 주기의 확인·회수·시작 작업이 끝나면 종료한다. 다음 주기는 예약 작업이 1시간 뒤 실행한다.

현재 우선 확인 작업은 `G-A072`다. 경로는 Windows `C:\workspace`와 Git Bash `/workspace`가
같은 junction이다. 사실 확인 없이 `STARTED`, `DONE`, 회수 완료, 자동 진행을 주장하지 않는다.
