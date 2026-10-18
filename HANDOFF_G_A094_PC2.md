<!-- PC2_HANDOFF
WORK_ID: G-A094
STATUS: READY
START_AFTER: NONE
START_MARKER: NONE
PACKAGE: workspace/training/quadruped/upload/G-A094/current/GO2_G_A094_A093_EVAL4999_v1.zip
PACKAGE_SHA256: 643f5af39849e28f56aa71ce7559e228698f567f9339f74006652fd1fcc61e97
-->

# G-A094 — PC2 평가 전용: G-A093 공식 서버 정책의 iter 4999 checkpoint (학습 없음)

## 0. 한눈에
- **목적:** G-A093(G-A083 보상, 공식 서버 5,000회)의 보상 최고 checkpoint인 iter 4999를 69 case와 영상 10편으로 평가한다.
  - 사용자 결정(2026-10-18): "제일 좋은걸로 해주고".
  - 사전등록한 4900은 이미 평가했다(57.18).
- **학습:** 없다. runner의 학습 경로는 rc 40으로 막혀 있다.
  - checkpoint는 서버 학습에서 나온 것을 SHA와 함께 넣었다: `4466db85…`, env `8c2215ce…`.
  - play.py가 이 checkpoint에서 policy.pt를 export한다.
- **시작 조건:** 바로 시작한다. G-A092는 원장에 DONE이다. 다른 train.py나 play.py가 돌고 있으면 기다린다.
- **예상 시간 [추정]:** 1시간 ~ 1시간 30분.

## 1. 준비 확인
1. parts `.001`~`.003`을 순서대로 이어 `/workspace/GO2_G_A094_A093_EVAL4999_v1.zip`으로 만든다. SHA256이 `643f5af39849e28f56aa71ce7559e228698f567f9339f74006652fd1fcc61e97`인지 확인한다.
2. Isaac Lab venv와 GPU를 확인하고, 다른 train.py·play.py 프로세스가 없는지 확인한다.

## 2. 실행
```bash
cd /workspace && unzip -oq GO2_G_A094_A093_EVAL4999_v1.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/go2_g_a094_a093_eval/server_run.sh --inner
```
- PC2에는 tmux가 없으므로 `--inner`로 실행한다(Windows에서는 `nohup … &`). 패키지와 a093 자료의 SHA, checkpoint의 iteration과 유한성은 스크립트가 직접 확인한다.
- **진행 상태:** `cat /workspace/_keep/GO2_G_A094_A093_EVAL_STATUS.txt`로 본다. 확인할 줄은 `ITER_4999_CASES=n/69`, `ITER_4999_VIDEOS=n/10`.
- **완료 표식:** `[DONE] GO2_G_A094_A093_EVAL_RESULT_READY`
- 평가 case나 영상이 충돌하면 각각 최대 3번까지 자동으로 다시 시도한다. 기록은 `logs/EVAL_RETRIES.txt`에 남는다.

## 3. 실패 처리
| rc | 의미 | 처리 |
|---|---|---|
| 21 / 22 / 25 | 중복 프로세스, Isaac/GPU 없음, 패키지 SHA 불일치 | 아무것도 시작하지 않은 상태다. 로그를 회수한다. |
| 41 | a093 자료의 SHA, iteration, 유한성 검사 실패 | 평가하지 않는다. STATUS와 로그를 회수한다. |
| 40 | 학습 경로에 진입함(정상이면 나오지 않음) | 멈추고 보고한다. |
| 그 밖 / 31 | 평가 중 실패 | 같은 한 줄을 한 번만 다시 실행한다. 이미 잰 case는 건너뛴다. 또 실패하면 STATUS와 로그를 회수한다. |

## 4. 회수
- **최종 결과:** `/workspace/_keep/GO2_G_A094_A093_EVAL_RESULT.zip`과 `.sha256`. 안에 `GO2_G_A094_A093_EVAL4999_RESULT.zip`이 들어 있다.
- **함께 올릴 것:** `/workspace/_keep/GO2_G_A094_A093_EVAL_STATUS.txt`, `GO2_G_A094_A093_EVAL.log`
- 100MB를 넘으면 95MiB parts로 나누고 원본 SHA를 보존한다. 커밋하고 push한다.

## 5. 보고
- 시작과 종료 시각, 최종 rc, 69 case와 영상 10편 수량, 결과 ZIP SHA, `evaluation/candidate/identity.json`의 model_sha256(= `4466db85…`인지)을 적는다.
- 판독과 제출 선택은 작성 PC가 한다.
