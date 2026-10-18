# G-A094 — G-A093 서버 정책의 보상 최고 checkpoint(4999) 평가 (학습 없음)

- G-A093(G-A083 보상, seed 42, 공식 서버 5,000회)은 비유한값 없이 끝났다. 사전등록한 4900회로 평가해 57.18점이었다.
- 배포 finalize가 고른 보상 최고 checkpoint는 4999회(`4466db85…`)다. 이 패키지가 그 checkpoint를 같은 평가기로 잰다(69건, 영상 10편).
- play.py가 이 checkpoint에서 policy.pt를 export한다. runner의 학습 경로는 rc 40으로 막혀 있다.
- 학습이 없으므로 PC2에서 돌려도 제출 정책의 출처는 서버 학습 그대로다.

## 실행
- PC2 (tmux 없음):
  - `cd /workspace && unzip -oq GO2_G_A094_A093_EVAL4999_v1.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/go2_g_a094_a093_eval/server_run.sh --inner`
- 공식 서버 (tmux):
  - `cd /workspace && sha256sum -c GO2_G_A094_A093_EVAL4999_v1.zip.sha256 && unzip -oq GO2_G_A094_A093_EVAL4999_v1.zip -d /workspace && bash /workspace/go2_g_a094_a093_eval/server_run.sh`

## 회수
- `/workspace/_keep/GO2_G_A094_A093_EVAL_RESULT.zip`과 `.sha256`

## 해석 한계
- 내부 proxy이며 공식 결과가 아니다. 학습 실현은 하나다.
