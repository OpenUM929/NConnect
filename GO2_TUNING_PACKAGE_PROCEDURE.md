# Go2 튜닝 패키지 작성 절차 — 정책 결정 → ZIP → PC2 인계 (2026-10-15)

이 문서는 작성 PC에서 Go2 튜닝 회차를 만드는 작성자가 따르는 절차다. 작성자는 Claude 메인 루프와 Codex(테라, 루나)다(2026-10-15 사용자 지시). 원장 비고의 author 값은 `claude`, `codex-terra`, `codex-luna`다. 실행은 PC2가 `HANDOFF_<WORK_ID>_PC2.md`를 감지해서 한다. 판독은 결과를 받은 작성자가 한다.

이 문서는 새 규칙을 만들지 않는다. 루트 `AGENTS.md`, `ARTIFACT_MANAGEMENT.md`, `workspace/training/quadruped/AGENTS.md`에 흩어진 규칙을 작업 순서대로 묶은 것이다. 충돌하면 원 문서가 이긴다. 공식 규정 R-1~R-7은 언제나 최우선이다.

최근의 완성 예시는 G-A082다. 아래 파일을 옆에 열어 두고 따라 하면 된다.
- 계획서: `workspace/training/quadruped/upload/plan/GO2_G_A082_PLAN_20261014.md`
- 빌더와 시험: `tools/build_go2_g_a082_package.py`, `tools/test_go2_g_a082_package.py`
- 패키지: `workspace/training/quadruped/upload/G-A082/current/`
- 인계: `HANDOFF_G_A082_PC2.md`
- 등록: `ARTIFACT_MANAGEMENT.md`의 `G-A082-PACKAGE-20261014` 절, `GO2_NOW.md`, `GO2_REWARD_TRIAL_REFERENCE.md`, `workspace/_keep/author_pc_ledger.tsv`

---

## 0. 두 작성자가 함께 일할 때의 규칙

1. **주 저장소(`C:/dev/Nconnect`)에서는 `git pull`, `git stash`, `git checkout`, `git reset`, `git sparse-checkout`을 하지 않는다(2026-10-15 사고).**
   - 이 저장소는 partial clone이고, sparse-checkout으로 1만 5천여 파일을 숨긴다. 작업 트리에는 다른 세션의 미커밋 수정이 늘 있다.
   - 2026-10-15에 `git pull --autostash`가 지워 둔 `_keep` 파일을 되살려 디스크를 0으로 만들었다.
   - 주 저장소는 빌드와 분석에만 쓴다. `git fetch`와 `git show origin/master:<경로>`로 최신 문서를 읽는 것은 된다.
   - **커밋과 push는 스크래치 폴더의 작은 클론에서 한다.**
     ```bash
     git clone --depth 1 --filter=blob:none --no-checkout <origin URL> <스크래치>/pushclone
     cd <스크래치>/pushclone
     MSYS_NO_PATHCONV=1 git sparse-checkout set --no-cone /<올릴 파일> /<올릴 폴더>/
     git checkout master
     # 주 저장소에서 만든 파일을 복사하고, 원장·문서는 원격판 끝에 줄만 덧붙인다
     git add <파일> && git commit && git push origin master
     ```
   - 작은 클론에서도 `git show --stat`, `git ls-tree -l`은 blob 전체를 받는다. 대신 `GIT_NO_LAZY_FETCH=1`과 `--name-only`를 쓴다.
   - 내 커밋에는 내가 만든 파일과 내가 추가한 줄만 넣는다.
2. **한 번에 열린 튜닝 방향은 하나다.** 결과를 기다리는 회차(원장에 `READY`는 있지만 `READOUT_DONE`이 없는 회차)와 같은 보상 항을 다시 바꾸는 회차를 내지 않는다. 그 회차의 사전등록이 "연달아 올리지 않는다"고 정해 두었기 때문이다. 다른 항을 다루는 회차는 낼 수 있다. 이 경우 3항의 대기열을 쓴다.
3. **PC2는 학습을 한 번에 하나만 한다.** 다른 회차가 실행 중이거나 READY로 대기 중이면, 새 인계의 `START_AFTER`를 그 회차로 둔다. `START_MARKER`는 아래 형식을 쓴다.
   `START_MARKER: /workspace/_keep/<선행 회차 결과 폴더>/RUNNER_STATUS.txt exists and <선행 WORK_ID> has a terminal DONE or FAILED ledger row`
   (G-A076 인계와 같은 형식이다.)
4. **번호는 발행 커밋이 push된 쪽이 가진다.** 같은 번호로 push가 거부되면, rebase한 뒤 다음 미사용 번호로 상수를 바꾸고 다시 빌드한다. ZIP 이름과 인계 문서 이름도 함께 바꾼다. 이미 push된 다른 작성자의 파일은 고치지 않는다.
5. **원장 `workspace/_keep/author_pc_ledger.tsv`는 작성자들이 같이 쓴다.** 끝에 줄만 추가한다. 비고 칸 맨 앞에 `author=claude`, `author=codex-terra`, `author=codex-luna` 중 하나를 적는다. 이미 있는 줄은 고치지 않는다. PC2 원장 `pc2_handoff_ledger.tsv`는 쓰지 않는다.
6. **판독 문서는 결과를 받은 작성자가 쓴다.** 정본 경로에 다른 작성자의 판독이 이미 있으면 덮지 말고 끝에 새 절로 보충한다.
7. **한국어 파일은 UTF-8로 쓴다.** Codex는 PowerShell 파이프나 `Set-Content`로 한국어를 쓰지 않는다. 내용을 `.py`(UTF-8) 스크립트에 담아 python으로 쓴다. 파이프를 거치면 한글이 `?`로 영구히 손실된다(2026-10-08 확인).

---

## 1. 착수 전에 읽는 것

읽는 순서도 정해져 있다. 이미 읽은 문서라도, 마지막으로 읽은 뒤 바뀌었으면 바뀐 부분을 다시 읽는다.

1. 루트 `AGENTS.md`의 "최우선 지속 기억" 절과 "실제 목표 우선 결정 계약" 절
2. `GO2_TUNING_ANALYSIS_BRIEF.md`(요구사항, 자료 위치, 분석 절차)
3. `GO2_NOW.md`(현재 기준 정책, 열린 회차, 최신 결정)와 `GO2_REWARD_EVIDENCE_MASTER.md` §1-a(다이얼 시도 이력)
4. `workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md`(항목별 시험 이력과 결과값)
5. `workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md`(강좌의 보상 설명 원문, §8 계단 실패 원인). 강좌 HTML을 다시 추출하지 않는다.
6. `workspace/training/quadruped/reports/GO2_TUNING_BASE_DATA.md`(§0-1 변수 역할)와 `GO2_REWARD_MECHANISM_FORECAST.md`
7. 기준 정책의 최신 판독·약점 분석. 지금은 `workspace/training/quadruped/reports/GO2_G_A077_WEAKNESS_20261014.md`다.
8. 기준 정책과 대조군의 **원 학습 `report.html` 본문**. 출력에 `REPORT_READ_STATUS=READ_MATCHED|READ_UNMATCHED|MISSING|NOT_APPLICABLE`를 적는다.
9. `ARTIFACT_MANAGEMENT.md`(작업 ID 등록, 회수 규칙)

---

## 2. 튜닝 정책 결정

### 2-1. 생각하는 순서 (바꾸지 않는다)

1. **관측을 사실 그대로 적는다.** case 이름, 수치, 시간 순서를 적는다. 상관을 원인으로 바꾸지 않는다.
2. **그 관측이 실패를 설명하는지 검토한다.** 설명되는 것과 설명되지 않는 것(`[모름]`)을 나눠 적는다.
3. **강좌 원문과 배포 주석으로 예측한다.** 그 상황에서 강좌가 어떤 보상을 쓰라고 하는지 읽고 방향을 예측한다. 강좌에 직접 설명이 없으면 "없다"고 적고, 보상 식에서 따라 나오는 것만 쓴다.
4. **시험 이력으로 반례와 부작용을 대조한다.** 같은 항, 같은 값이 어느 기준선에서든 시험된 적 있으면 후보에서 뺀다. 사용자가 기각한 안을 다시 내지 않는다.
5. **그다음에 항과 값을 고른다.** 값부터 고르고 사유를 채우지 않는다.

### 2-2. 결정 비교표 (계획서 §2에 넣는다)

다음 일곱 칸을 모두 채운다. 빈칸이 있으면 값을 고른 것이 아니다.
- 현재 채택 실패: 어느 시나리오에서 몇 점을 잃는가. 점수는 역산 수식으로 계산한다(2-3).
- 바꾸려는 행동
- 지지 관측과 반대 관측. 반대 관측은 적고 끝내지 말고 값·폭·중단 조건에 반영한다.
- 보존할 이득: 지금 기준 정책이 잘하는 것
- 값과 폭의 이유. "더 작다", "미탐색", "기본값"만으로는 이유가 되지 않는다.
- 같은 비용의 대안과 기각 이유
- 결과별 다음 결정: 지지, 지지이나 보호 축 손실, 반증, 발산 각각에 무엇을 할지

### 2-3. 점수 계산

- 단순 비율로 공식 점수를 환산하지 않는다. `tools/h1_official_formula_fit.py`로 찾은 수식을 쓴다. 결과는 `workspace/calibration/h1_official_20260910/formula_fit_20261014/H1_FORMULA_FIT.md`에 있다. 수식은 step별 exp(−√(e_xy²+e_yaw²)/0.70)의 평균이고, 앞 1초(50 step)를 뺀다.
- 시나리오별 손실 분해는 `tools/go2_weakness_breakdown.py`, 회전 응답 분석은 `tools/go2_yaw_oscillation_response.py`로 한다.
- 이 점수는 공식 점수가 아니다. 문서에는 "역산 수식 기준 내부 proxy"로 적는다.

### 2-4. 사전등록 (실행 전에 고정한다)

- 주 예측: 어느 case의 어느 지표가 어디까지 움직이면 지지인지, 어디서 반증인지, 그 사이는 INCONCLUSIVE로 둔다.
- 보호 축: 기준 정책의 최약 case에서 고른다. 계단 완주, G3 생존, 지형 위 명령 방향 속도처럼 원자료로 판정할 수 있는 것이어야 한다.
- 발산 대비: 학습이 중간에 발산하면 pinned checkpoint(예: iter 2400)를 평가 전용 패키지로 평가한다. "발산하면 기각"으로 두지 않는다.
- 승급: `exploratory_single_seed_no_automatic_followup`. 결과가 좋아도 다른 값을 자동으로 발행하지 않는다.
- 영상 필요성: 보상이 바뀌면 `필수`다. 기준 정책과 같은 영상 목록, 같은 seed를 쓴다.
- 결과를 받은 뒤 문턱을 바꾸지 않는다.

### 2-5. 계획서 작성

- 경로: `workspace/training/quadruped/upload/plan/GO2_<WORK_ID>_PLAN_<YYYYMMDD>.md`
- 맨 위에 `## 0. 예선 기준 현재 위치`(여덟 항목)를 쓴다. 이어서 §1 분석 순서, §2 결정 비교표, §3 사전등록·패키지·인계 경로를 쓴다. G-A082 계획서와 같은 구성이다.

---

## 3. 번호 정하기

1. 주 저장소에서 `git fetch origin`만 한다.
2. 아래 세 곳을 원격판(`git show origin/master:<경로>`, 목록은 `GIT_NO_LAZY_FETCH=1 git ls-tree --name-only origin/master <폴더>/`)으로 보고, 그 세 곳에서 가장 큰 G-A 번호를 찾고, 그다음 번호를 쓴다.
   - `ls workspace/training/quadruped/upload/`
   - `grep -o 'G-A[0-9]*' workspace/_keep/author_pc_ledger.tsv | sort -u | tail`
   - `grep -o '^## G-A[0-9]*' ARTIFACT_MANAGEMENT.md | sort -u | tail`
3. 평가 전용 회차도 같은 번호 체계를 쓴다. 날짜나 정책 이름을 번호 대신 쓰지 않는다.

---

## 4. ZIP 만들기

### 4-1. 빌더와 시험 만들기

1. 가장 가까운 기존 빌더를 복사해 `tools/build_go2_<work_id 소문자>_package.py`를 만든다. 기준 정책이 PC2 G-A077이고 보상 한 항만 바꾸면 `build_go2_g_a082_package.py`가 출발점이다.
2. 바꾸는 상수는 다음뿐이다.
   - `WORK_ID`, `SLUG`, `RELEASE`(끝에 `_v1`), `RESULT_ZIP`, `KEY`, `FIXED_TIME`(발행일)
   - 기준 정책의 경로와 SHA: `BASE_KEEP`, `B_MODEL_SHA`, `B_ENV_SHA`
   - `CANDIDATE`: 바꾸는 한 항만 다르게 둔다.
   - `VIDEOS`: 기준 정책의 저장된 영상 목록과 같게 둔다.
   - `experiment()`: 가설, 경쟁 가설, 2-4의 사전등록 내용
3. 런타임 코드(runner, `run_point.sh`, `run_all.sh`, evaluator)는 기존 빌더를 import해서 재사용한다. 실행 프로그램을 새로 만들지 않는다.
4. 시험 파일 `tools/test_go2_<id>_package.py`를 G-A082 시험에서 복사해 상수만 바꾼다. 아래 여덟 가지를 반드시 검사한다.
   - 단일변수 diff(바뀐 항이 하나이고 값이 맞는가)
   - 기준 영상 수가 저장된 대조군과 같은가(G-A077의 rc31이 여기서 생겼다)
   - 기준 정책 model/env SHA와 69 case 내장 여부
   - 사전등록 필드
   - 배포 코드(`train.py`, `play.py`, `go2_task/*`)가 원본과 같은가(R-6)
   - 학습 전에 runner 사전검사가 있는가
   - identity 사전검사 rc 23
   - manifest, CRC, LF, `bash -n`

### 4-2. 빌드와 검증

```bash
python -m unittest tools.test_go2_<id>_package -v      # 전부 통과해야 한다
python tools/build_go2_<id>_package.py --check           # SHA를 출력한다
python tools/build_go2_<id>_package.py --publish         # upload/<ID>/current/에 parts와 .sha256를 쓴다
python tools/build_go2_<id>_package.py --check           # 다시 빌드해도 같은 SHA인지 확인한다
```

발행을 막을 수 있는 사유는 세 가지뿐이다.
1. R-6 위반: 배포 코드를 고쳐야만 하는 경우
2. 로컬 시험 실패
3. 회수 불가

이 셋에 걸리면 대체 문서(review ZIP, 진단 계획)를 만들지 않는다. 차단 사실 한 줄과 필요한 사용자 결정 하나만 보고하고 멈춘다. "원인 미확정"은 차단 사유가 아니다. 사전등록에 적고 진행한다.

### 4-3. 산출물 확인 (여섯 항목이 모두 있어야 완료다)

1. `upload/<ID>/current/<RELEASE>.zip.001~` 파일들(95MiB 단위)과 `.zip.sha256`. 원본 ZIP은 git에 넣지 않는다.
2. SHA와 재빌드 일치
3. 로컬 검증 결과: 단일변수 diff, LF, `bash -n`, CRC/SHA
4. 실행 한 줄(인계 §2)
5. 결과 ZIP 경로와 `report.html` 회수 경로(`_keep/<slug>/exported/report.html`)
6. 실패 처리와 회수 게이트(인계 §3·§4)

parts 경로는 `github.com`으로 받는다. Git LFS는 쓰지 않는다(이 네트워크가 S3를 막는다).

---

## 5. PC2 인계 문서 만들기

1. 파일: 루트 `HANDOFF_<WORK_ID>_PC2.md`. 형식은 `HANDOFF_G_A082_PC2.md`를 따른다.
2. 맨 위 머리말. 이 머리말이 있어야 PC2가 실행한다.
   ```
   <!-- PC2_HANDOFF
   WORK_ID: G-A0NN
   STATUS: READY
   START_AFTER: <선행 WORK_ID 또는 NONE>
   START_MARKER: <0-3항 형식 또는 NONE>
   PACKAGE: workspace/training/quadruped/upload/G-A0NN/current/<RELEASE>.zip
   PACKAGE_SHA256: <64자>
   -->
   ```
3. 본문 절
   - §0 한눈에: 목적, 근거 문서, 설계(바꾸는 한 항과 유지 항 전부), 학습 조건, 대조군 식별자, 점 목록, 예상 시간
   - §1 준비 확인: parts 이어 붙이기, SHA 확인, 중복 프로세스 확인, 여유 공간과 USD 확인
   - §2 실행: 실행 한 줄, 진행 기록(`tools/watch_go2_pc2_progress.ps1 -Publish`), STOP 방법
   - §3 실패 처리: rc별 할 일(20~25, 3이면서 TRAIN_RC≠0, 30~34). 자동 재학습, seed 변경, 이어 학습은 금지한다.
   - §4 회수: 결과 폴더, 결과 ZIP, 포함 확인 목록, parts 분할, 커밋
   - §5 보고: PC2는 시작·종료·rc·SHA·진행률만 보고한다. 판독 항목은 작성자가 본다고 적는다.
4. 올린 뒤에는 `STATUS`만 바꿀 수 있다(READY, HOLD, CANCELLED). 내용을 바꿔야 하면 `_v2` ZIP과 새 인계로 낸다.

---

## 6. 등록과 발행

1. 등록한다(각 문서 끝에 추가만 한다).
   - `ARTIFACT_MANAGEMENT.md`: `## <WORK_ID>-PACKAGE-<YYYYMMDD> (READY, PC2)` 절을 만들고 패키지 경로, SHA, 빌더, 시험 수, 인계, 계획, 영상 판정을 적는다.
   - `GO2_NOW.md`: 한 줄 포인터
   - `GO2_REWARD_TRIAL_REFERENCE.md`: 해당 항 아래에 "발행, 결과 미측정" 한 줄
   - `workspace/_keep/author_pc_ledger.tsv`: `PUBLISHED` 줄과 `READY` 줄(0-5항 형식)
2. **패키지 parts, `.sha256`, 인계 문서, 빌더, 시험, 원장을 한 커밋으로 올린다.** 패키지 없이 인계만 올리지 않는다. 계획서와 등록 문서는 같은 커밋이나 바로 다음 커밋으로 올린다.
3. 작은 클론에서 push한 뒤 주 저장소에서 `git fetch`를 한다. 그다음 `GIT_NO_LAZY_FETCH=1 git ls-tree -r --name-only origin/master <경로>`로 parts, 인계, `.sha256`이 원격에 있는지 확인한다.
4. 사용자에게 보고할 때는 `## 0. 예선 기준 현재 위치`를 먼저 쓴다. 이어서 WORK_ID, 바꾼 한 항(전→후), SHA, 커밋, 대기열 위치(START_AFTER)를 쓴다.

---

## 7. 결과를 받은 뒤 (같은 작성자가 이어서 한다)

1. `bash tools/keep_fetch_result.sh <결과>.zip`으로 받는다. parts를 `git pull`이나 `git cat-file`로 받지 않는다. 보고에 여유 공간 전후를 한 줄 적는다.
2. 회수 완결을 확인한다: SHA, CRC, manifest, 69 case, 영상 수, 원 `report.html`. `report.html`이 없으면 `REPORT_REQUIRED_NOT_ACQUIRED`다.
3. 사전등록 기준 그대로 판독한다. 증거 계층(`ARTIFACT_VERIFIED`, `VIDEO_OBSERVED/UNKNOWN`, `INTERNAL_GATE_*`)을 붙인다. bare PASS는 쓰지 않는다.
4. 원장에 `RECEIVED`와 `READOUT_DONE`을 추가하고, `GO2_REWARD_TRIAL_REFERENCE.md`의 해당 줄에 결과값을 더한다.
5. 판독이 끝난 뒤에야 같은 항의 다음 회차를 검토한다.

---

## 8. 하지 않는 것

- 배포 코드(`train.py`, `play.py`, `go2_task/`)를 고치는 것. 바꾸는 것은 `quadruped_rewards.py`의 값뿐이다(R-6).
- 두 항 이상을 한 회차에 바꾸는 것
- 이미 시험한 항·값, 사용자가 기각한 안, 판독 대기 중인 회차와 같은 항을 다시 내는 것
- review ZIP, 진단 계획, 인계 문서만 만들고 실행 ZIP 없이 "완료"라고 보고하는 것
- 과거 발행물(ZIP, 인계 본문)을 고치는 것
- 다른 작성자의 미커밋 수정을 커밋에 섞거나 되돌리는 것
- 서버나 PC2의 프로세스를 직접 멈추는 것. 남은 점을 멈출 때는 `touch <상태 폴더>/STOP`만 한다.
