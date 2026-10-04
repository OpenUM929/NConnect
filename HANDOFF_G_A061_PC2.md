# G-A061 인계 — PC2(RTX 5070) 탐색트리 첫 노드 N3 (PC2 Claude 세션용, 2026-10-04)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 사용자에게 같은 설명을 다시 요구하지 않는다.
루트 `AGENTS.md`(R-1~R-7), `GO2_NOW.md` 맨 아래 줄을 함께 따른다. PC2 환경 우회(마운트, isaaclab.sh shim, pyshim, D3D12 영상 런처)는 `HANDOFF_PC2_CONTINUOUS_MONITOR_20261003.md`와 `workspace/_keep/go2_g_a060_pc2_run_chain.sh`에 있는 그대로 쓴다.

## 0. 한눈에
- **목적:** 트랙 1.5를 고정하고 다른 보상 항을 하나씩 바꿔 계단(G5)·험지(G3) 개선 값을 찾는 탐색트리의 첫 노드다.
  - 설계: `workspace/training/quadruped/upload/plan/GO2_TRACK_FIXED_SEARCH_TREE_20261003.md` §12·§13
  - 승인: Codex §37(계획), §41(구현)
  - PC2 결과는 탐색 근거이고 제출 정책이 아니다(R-6·제14조).
- **이번에 돌릴 것(한 노드만):** `n3_dof_torques_l2_m1e_4`
  - 부모 P0는 PC2 B1(A048 보상, track 1.5)이다.
  - 그 위에서 `dof_torques_l2`만 −2e−4에서 −1e−4로 바꾼다.
  - 학습 seed 42, 4096 env, 1000 iter, 평가 iter 900, 69 case, 영상 10편.
- **예상 시간 [추정]:** 약 2시간 25분. G-A060 점2·점3 실측 기준이다.
- **다음 노드는 자동으로 돌지 않는다.** 결과를 작성 PC가 판독한 뒤, 트리 규칙(`tools/go2_pc2_tree_readout.py next`)이 정한다.

## 1. 준비 확인
1. `git pull` 후 패키지를 확인한다.
   - 경로: `workspace/training/quadruped/upload/G-A061/current/GO2_G_A061_PC2_TREE_n3_dof_torques_l2_m1e_4_v1.zip`
   - SHA256: `f9665bf3d39f32de7f296f862534f797c4f8029372dab81fe9a7a4224b6580c5`
   - 확인 명령: `sha256sum -c`
2. ZIP을 `/workspace/`에 복사한다. 저장소 원본은 그대로 둔다.
3. 다른 학습(train.py·play.py)이 돌고 있지 않은지 확인한다. 돌고 있으면 러너가 rc 21로 거부한다.

## 2. 실행
- G-A060 때와 같은 환경 변수로 실행한다: `mount`, `ISAACLAB_SH`, `PYTHONIOENCODING=utf-8`, `KMP_DUPLICATE_LIB_OK=TRUE`, `PATH=pyshim:…`
  - `go2_g_a060_pc2_run_chain.sh` 머리의 export 줄을 그대로 쓴다.
  - 그 체인 스크립트 자체는 G-A060 점 key를 부르므로 실행하지 않는다.
- 한 줄:
  `unzip -oq /workspace/GO2_G_A061_PC2_TREE_n3_dof_torques_l2_m1e_4_v1.zip -d /workspace && bash /workspace/go2_g_a061_pc2/run_point.sh --only n3_dof_torques_l2_m1e_4`
  - Linux는 tmux, Windows는 `nohup … &`로 띄운다.
- GPU 감시를 함께 띄운다: `tools/go2_gpu_watch.sh --hours 6 --pattern 'go2_g_a061_pc2_*'` (`HANDOFF_G_A060_PC2.md` §6).
  - `--pattern`을 반드시 준다. 기본값은 G-A060이라, N3 때는 지난 회차 상태를 STALL로 기록했다(2026-10-04).
  - N5부터는 이 문서의 `--only` key를 `RUN_GUIDE.txt`의 node로 바꿔 실행한다.
  - 감시는 기록만 한다. 프로세스를 끄지 않는다.
- 상태 확인: `/workspace/_keep/go2_g_a061_pc2_points/POINT_STATUS.tsv`

## 3. 실패 처리 (계획 §13-3 — 이 순서를 바꾸지 않는다)

| 상황 | 처리 |
|---|---|
| 학습 시작 전 실패(rc 20~23) | 환경을 고친 뒤 같은 한 줄을 다시 실행한다. 고칠 수 없으면 보고하고 멈춘다 |
| 학습 완료 후 평가·회수 실패(rc 30·31, checkpoint 있음) | 같은 `--only` 명령을 다시 실행한다. 완료 단계는 건너뛰고 재학습하지 않는다 |
| 학습 도중 실패(고정 iter 900 checkpoint 없음), 또는 위 복구도 실패 | 자동 재학습하지 않는다. 보고하고 멈춘다. 같은 값 재학습은 사용자가 정한다 |

- 영상 단계에서 Vulkan 초기화가 실패하면 G-A060 때의 D3D12 영상 런처 우회를 그대로 쓴다. 배포 코드는 수정하지 않는다.

## 4. 회수
- 다음을 저장소 `workspace/_keep/`에 같은 이름으로 복사한다. 원본은 지우지 않는다.
  - `/workspace/_keep/go2_g_a061_pc2_n3_dof_torques_l2_m1e_4/` 폴더 전체(report.html, 69 case, 영상 10편)
  - `GO2_G_A061_PC2_N3_DOF_TORQUES_L2_M1E_4_RESULT.zip`과 `.sha256`
  - `/workspace/_keep/go2_g_a061_pc2_points/`
  - GPU 감시 기록 `/workspace/_keep/go2_gpu_watch/`
- ZIP은 `sha256sum -c`로 확인한다. 100MB가 넘으면 95MB parts로 등재한다(`workspace/_keep/reconstruct_zips.sh`에 이름 추가).
- report.html이 없거나 영상이 10편 미만이면 회수 완료로 보고하지 않는다.
- 커밋·푸시는 사용자가 요청할 때 한다.

## 5. 보고 (판독은 하지 않는다)
- 사용자 보고는 `## 0. 예선 기준 현재 위치`로 시작한다. 상태(DONE/FAILED), 실측 시간, 실패면 §3의 어느 칸인지만 적는다.
- 성능 판독과 다음 노드 결정은 작성 PC가 `tools/go2_pc2_tree_readout.py`로 한다.
- PC2 결과는 PC2 부모와만 비교한다. PC1·서버 결과와 한 표에서 효과로 비교하지 않는다.
