<!-- PC2_HANDOFF
WORK_ID: H-A001
STATUS: READY
START_AFTER: G-A072
START_MARKER: /workspace/_keep/go2_g_a072_pc2_points/BATCH_RUN.log 에 [BATCH END]
PACKAGE: workspace/training/humanoid/upload/H-A001/current/H_A001_P0_SPEED_GRID_v2.zip
PACKAGE_SHA256: ad66bb8104cf976a114b682d1fa97f01fb181c4243b0819cfede8b46bf7ce898
-->
# H-A001 인계 — PC2(RTX 5070) H1 속도 격자 측정, 학습 없음 (PC2 Claude 세션용, 2026-10-08)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. **이 작업은 2족(H1)이다.** Go2 작업과 폴더·원장 키가 다르다.

## 0. 한눈에
- **설계·합의:** `workspace/training/humanoid/upload/plan/H1_STABLE_SPEED_TUNING_DEBATE_20261008.md` §12·§14(Astra APPROVE §13), 발행 §15.
- **무엇을 하나:** H1 제출 정책 Run06(model_9900)과 대조 Run05(model_2700)를 **학습 없이** 재생한다. 속도 명령 9가지 × 평가 seed 101/202/303 × 32 env × 1000 step의 기록(steps.csv)을 남긴다.
  - 평지 직진 0.75 / 1.0 / 1.25 m/s
  - 요철 직진 0.75 / 1.0 m/s
  - 평지 복합: 직진 0.5 또는 1.0 m/s에 회전 ±0.5 rad/s
- **왜:** "안정적이면서 Run06보다 빠르게"라는 H1 튜닝 목표의 출발점(지금 넘어지지 않고 따라가는 최고 속도)을 잰다.
- **시작 조건:** G-A072(Go2 seed 43 재현 4점)가 끝난 뒤 시작한다. GPU를 쓰므로 Go2 학습과 동시에 돌리지 않는다.
- **순서 규칙:** 같은 때에 다른 READY 문서가 있어도, `START_AFTER: G-A072`인 이 문서를 G-A072 다음 첫 작업으로 한다(사용자 지시 "4족 튜닝 작업이 끝나면 우리 작업을 진행").
- **시간 [추정]:** 1~2시간. 정책 2 × case 9 × seed 3 = 54회 재생이다.
- **R-6:** 패키지는 `h1_ha001/` 폴더만 추가한다. `play.py`·`train.py`·`h1_task/`·`humanoid_rewards.py`·`exported/`는 패키지에 없다. 러너는 `play.py`가 배포 원본(SHA `bba3c5ac…8dbdb`)일 때만 시작한다.

## 1. 준비 확인
1. `git pull` 뒤 SHA를 확인한다: `cd workspace/training/humanoid/upload/H-A001/current && sha256sum -c H_A001_P0_SPEED_GRID_v2.zip.sha256`
2. 다른 train.py·play.py가 돌고 있지 않은지 확인한다(G-A072 `[BATCH END]` 확인 포함).
3. **H1 실행 폴더 준비.** `/workspace/training/humanoid/play.py`가 없거나 SHA가 다르면, 저장소 루트에서 아래를 실행한다. 저장소의 `play.py`는 평가 훅이 들어간 사본이라 쓰지 않는다. 원본은 커밋 `e288246`에서 꺼낸다.
   ```bash
   mkdir -p /workspace/training/humanoid
   git show e288246:workspace/training/humanoid/play.py > /workspace/training/humanoid/play.py
   cp -r workspace/training/humanoid/h1_task workspace/training/humanoid/humanoid_rewards.py workspace/training/humanoid/pyproject.toml /workspace/training/humanoid/
   echo "bba3c5acbdd37281430875b87175716a23e91bf830da64794f809d60383d8bdb  /workspace/training/humanoid/play.py" | sha256sum -c -
   ```
   `/workspace/training/humanoid`에 이미 다른 파일이 있으면 지우지 않는다. 위 4개만 맞춘다.
4. 원장에 `H-A001<TAB>STARTED<TAB>시각`을 적고 커밋·푸시한다.
5. `cp workspace/training/humanoid/upload/H-A001/current/H_A001_P0_SPEED_GRID_v2.zip /workspace/training/humanoid/`

## 2. 실행 (Git Bash)
1. 환경 변수는 G-A064 인계 §2와 같다(`mount …`, `ISAACLAB_SH=/workspace/bin/isaaclab.sh`, `PYTHONIOENCODING`, `PYTHONUTF8`, `KMP_DUPLICATE_LIB_OK`, `PYTHONUNBUFFERED`, `PATH` pyshim).
2. 실행 한 줄(백그라운드, tmux 없이):
   ```bash
   cd /workspace/training/humanoid && unzip -oq H_A001_P0_SPEED_GRID_v2.zip && NO_TMUX=1 nohup bash h1_ha001/server_run_h1_ha001_p0.sh > /workspace/_keep/h1_ha001_console.log 2>&1 &
   ```
3. 진행 확인: `tail -n 3 /workspace/_keep/H_A001_P0_SPEED_GRID/EVAL_STATUS.tsv` (54행 + 머리행이면 끝)
4. 끝 표식: `/workspace/_keep/h1_ha001_console.log`에 `[DONE] H-A001 P0 speed grid complete`

## 3. 실패 처리
- `[BLOCKED] play.py is not the distributed original` → §1-3을 다시 한다. `play.py`를 고쳐서 맞추지 않는다.
- 첫 case에서 실패(`[FAIL] ... rc=` 또는 telemetry missing)하면 → 콘솔 로그와 `/workspace/_keep/H_A001_P0_SPEED_GRID/logs/`의 해당 `.log`를 회수하고 `FAILED<TAB>rc`로 보고한다. 진입 모듈(`h1_ha001/h1_eval_entry.py`)은 Isaac에서 처음 실행되는 것이라, 이 경우는 작성 PC가 고친다. PC2는 코드를 고치지 않는다.
- 중간 case 실패(일시 오류로 보임) → 한 번만 이어서 실행한다: `cd /workspace/training/humanoid && EVAL_RESUME=1 NO_TMUX=1 nohup bash h1_ha001/server_run_h1_ha001_p0.sh >> /workspace/_keep/h1_ha001_console.log 2>&1 &`. 또 실패하면 보고한다.
- 실패 시에도 `/workspace/_keep/H_A001_P0_SPEED_GRID_PARTIAL.tar.gz`가 생긴다. 함께 회수한다.

## 4. 회수
- `/workspace/_keep/H_A001_P0_SPEED_GRID_FULL.tar.gz`와 `.sha256`을 저장소 `workspace/_keep/`로 복사한다. 100MB를 넘으면 95MB parts 규칙(`ARTIFACT_MANAGEMENT.md` §6-a)으로 올린다.
- `/workspace/_keep/h1_ha001_console.log`도 같이 올린다.
- 영상은 없다(VIDEO_NOT_REQUIRED). 학습이 없으므로 report.html도 없다(NOT_APPLICABLE). 이 둘이 없다고 미완료로 보지 않는다.
- 커밋·푸시한 뒤 원장에 `H-A001<TAB>DONE<TAB>시각`을 추가한다.

## 5. 보고 (판독은 하지 않는다)
- 상태(DONE/FAILED), rc, 실측 시간, FULL tar SHA만 적는다. 판독은 작성 PC(H1 세션)가 `tools/h1_ha001_p0_readout.py`로 한다.
