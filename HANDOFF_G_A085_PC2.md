<!-- PC2_HANDOFF
WORK_ID: G-A085
STATUS: READY
START_AFTER: G-A084
START_MARKER: /workspace/_keep/go2_g_a084_ang_vel_xy_m0p065/RUNNER_STATUS.txt 에 RUNNER_RC=0 (그리고 pc2_handoff_ledger.tsv 에 G-A084 DONE)
PACKAGE: workspace/training/quadruped/upload/G-A085/current/GO2_G_A085_PRECISION_EVAL_v1.zip
PACKAGE_SHA256: 2ffd2b6c4296b16885e559a60cef64aca3967f98091bfc3bb161e29d1825db2a
-->

# G-A085 — PC2 정밀 평가 (G-A082·G-A083·G-A084, 학습 없음)

## 0. 한눈에

- **목적:** 정책 차이를 평가 잡음과 견줘 판정하려고, 평가 seed 사이의 sd를 잰다. 넘어지는 case는 roll/pitch와 발 접촉을 기록한다.
- **하지 않는 것:** 학습, 보상 변경, 영상 생성. 배포 파일(R-6)도 건드리지 않는다.
- **대상 정책:** iter 2400 정책 3개.
  - G-A082(`df214dc9…`)와 G-A083(`bbbc04f4…`)은 패키지에 들어 있다.
  - G-A084는 이 PC의 `/workspace/_keep/go2_g_a084_ang_vel_xy_m0p065/`에서 가져온다. 스크립트가 `RUNNER_RC=0`과 `CHECKPOINT_PIN` SHA를 확인한다.
- **평가:** 정책마다 새 평가 seed 6개(404·505·606, 707·808·909)로 69 case 스위트를 2번 돈다. 모두 6개 스위트다.
- **진단 재생:** G-A083과 G-A084를 원래 seed 101·202·303으로 돈다. 험지 전진, 험지 옆걸음, 밀침 +x·−x·+y에 DR(seed 101)을 더해 정책당 16회, 모두 32회다.
- **분석:** 끝나면 PC2에서 표준 라이브러리 분석을 돌려 `analysis/ROWS.csv`와 `SUMMARY.json`을 만든다. 판독은 하지 않는다.
- **예상 시간:** 약 5시간이다. 스위트 하나 약 45분 × 6, 진단 약 30분, 패키징 약 15분으로 잡았다 [추정].
- **패키지:** 단일 ZIP(약 13.9MB), SHA `2ffd2b6c4296b16885e559a60cef64aca3967f98091bfc3bb161e29d1825db2a`.

## 1. 준비 확인

1. `git pull` 뒤 `workspace/training/quadruped/upload/G-A085/current/GO2_G_A085_PRECISION_EVAL_v1.zip`을 `/workspace/`로 복사한다. 그 SHA256이 `2ffd2b6c4296b16885e559a60cef64aca3967f98091bfc3bb161e29d1825db2a`인지 확인한다.
2. G-A084가 끝났는지 확인한다. `/workspace/_keep/go2_g_a084_ang_vel_xy_m0p065/RUNNER_STATUS.txt`에 `RUNNER_RC=0`이 있어야 한다. 없으면 시작하지 않는다(스크립트도 rc 26으로 멈춘다).
3. 다른 train.py·play.py가 돌고 있지 않아야 한다. 디스크 여유는 15GB 이상이어야 한다.
4. 다음 폴더가 있으면 원래 seed 대조와 진단 비교에 쓴다. 없어도 실행은 된다(`STORED_MISSING`으로 기록된다).
   - `/workspace/_keep/go2_g_a082_track_ang_vel_z_p0p75/evaluation/candidate/`
   - `/workspace/_keep/go2_g_a083_action_rate_m0p01/evaluation/candidate/`

## 2. 실행

### 한 줄

```bash
cd /workspace && unzip -oq GO2_G_A085_PRECISION_EVAL_v1.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/go2_g_a085_precision_eval/run_all.sh
```

- tmux 세션 `go2_g_a085`에서 돈다.
- 진행 상황: `cat /workspace/_keep/GO2_G_A085_STATUS.txt`. 스위트별 case/69와 진단 수/32가 나온다.
- 중간에 끊겼으면 같은 한 줄을 다시 실행한다. 이미 잰 case는 지문(case_identity)으로 건너뛰고 이어서 한다.
- 실행 순서: a083 스위트 2개 → a084 스위트 2개 → a083 진단 → a084 진단 → a082 스위트 2개 → 분석 → 패키징.

## 3. 실패 처리

| rc | 의미 | 처리 |
|---|---|---|
| 20 / 21 / 22 | 디스크 15GB 미만, 중복 프로세스·tmux, Isaac·GPU·tmux 없음 | 시작하지 않는다. 원인만 보고한다. |
| 25 | 패키지 SHA 불일치 또는 Go2 USD asset 접근 실패 | 평가하지 않는다. 로그를 보고한다. |
| 26 | G-A084가 `RUNNER_RC=0`으로 끝나지 않았다 | 기다린다. G-A084가 실패로 끝났으면 실행하지 않고 `FAILED<TAB>26`으로 적는다. |
| 23 | 평가기·모델·env·identity가 일치하지 않는다 | 평가하지 않는다. `GO2_G_A085_STATUS.txt`와 로그를 회수한다. |
| 33 | 결과 폴더가 다른 작업의 것이다 | 손대지 않고 보고한다. |
| 5 / 6 / 7 | case 평가 실패, case 수 69 아님, 모델 SHA 불일치 | 같은 한 줄로 한 번 다시 실행한다(이어서 한다). 또 실패하면 멈추고 로그를 회수한다. |
| 30 | 분석 실패 | `analysis/ANALYSIS.log`와 상태 파일을 회수해 보고한다. 평가 결과 폴더는 그대로 두고, 손으로 패키징하지 않는다. |

- 실행 중인 play.py를 kill하지 않는다.
- PC2는 결과를 판독하지 않는다. 후보 선택이나 다음 값도 정하지 않는다.

## 4. 회수

- 결과 폴더: `/workspace/_keep/go2_g_a085_precision_eval/`
- **SUMMARY ZIP:** `/workspace/_keep/GO2_G_A085_PRECISION_EVAL_SUMMARY.zip`과 `.sha256`
  - 분석 결과, 모든 summary.json, identity, 진단 원자료가 들어 있다. 작성 PC는 이것만 받는다.
- **RESULT ZIP:** `/workspace/_keep/GO2_G_A085_PRECISION_EVAL_RESULT.zip`과 `.sha256`
  - 전체 steps.csv가 들어 있다. 보존용이다.
- 두 ZIP 모두 저장소의 `workspace/_keep/`에 올린다. 100MB를 넘으면 95MiB parts(`.001`부터)로 나누고 원본 SHA를 보존한다. SUMMARY를 먼저 올린다.
- 상태 파일 `GO2_G_A085_STATUS.txt`도 함께 올린다.
- 원장 `pc2_handoff_ledger.tsv`에 `DONE`(또는 `FAILED<TAB>rc`)을 적고 커밋·push한다.

## 5. 보고

다음만 보고한다.
- 시작 시각, 종료 시각, 최종 rc
- 스위트별 case 수(6 × 69), 진단 수(32), `DIAG_IDENTICAL` 수
- `STORED_ARMS.txt` 내용(원래 seed 폴더를 찾았는지)
- 두 ZIP의 SHA와 parts 수
- 실패했다면 rc와 보존한 경로

판정은 작성 PC가 한다. 판정 기준은 평가 sd 2배이고, 판정 결과는 `INTERNAL_GATE_*`로 표기한다. 공식 결과는 `OFFICIAL_RESULT_UNMEASURED`로 둔다.
