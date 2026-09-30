# G-A058 판독 (자동, 규칙: 순서 제안 문서 §3)

설정 재현성: **NOT_YET**

| 행 | 역할 | 상태 | 총점/70 | 15cm ≥2단 /96 | 10cm ≥2단 /96 | 우회전 낙상 /96 | 개별 판정 | 우회전 결함 |
|---|---|---|---|---|---|---|---|---|
| a048_seed42 | reference | COMPLETE | 43.397 | 6 | 76 | 0 | 기록만 | - |
| a043_seed43 | a043_replicate | NOT_YET | | | | | | |
| a043_seed44 | a043_replicate | NOT_YET | | | | | | |

행 1 기록: 서버 A048(사전등록 내장값) vs 이 PC A048 seed 42 — 기록만, 판정 아님

| 지표 | 서버 A048 | 이 PC | 차이 |
|---|---|---|---|
| 총점/70 | 50.16 | 43.397 | -6.76 |
| 15cm ≥2단 /96 | 24 | 6 | -18 |
| 10cm ≥2단 /96 | 90 | 76 | -14 |
| 우회전 낙상 /96 | 0 | 0 | 0 |
| 험지 옆걸음 낙상 /96 | 16 | 68 | 52 |
| 험지 전진 낙상 /96 | 3 | 6 | 3 |
| 밀침 -y 낙상 /96 | 1 | 4 | 3 |

험지·밀침 낙상(/96):

- a048_seed42: rough_lateral=68, rough_forward=6, push_pos_x=4, push_neg_x=2, push_pos_y=0, push_neg_y=4 | 축 점수 G1=9.562, G2=9.782, G3=2.178, G4=9.844, G5=0.251, G6=6.329, G7=5.451

- 행 1은 기준 기록이며 판정 문턱이 아니다.
- 이 PC 정책은 탐색용이며 제출 후보가 아니다.
- 서버 A048·A043 원본 폴더가 이 PC에 없어 서버 대비 차이는 계산하지 않았다.

## Isaac 실행 사양

| 항목 | 이 PC (판독 시점 실측) | 서버 (인계 기록) |
|---|---|---|
| GPU | NVIDIA GeForce RTX 3050, 580.88, 6144 MiB | NVIDIA GeForce RTX 5080, 580.126.09, 16303 MiB (meta/gpu.csv of server arms) |
| Isaac Sim | 5.1.0.0 | 5.1 |
| Isaac Lab | 0.54.4 (git b0542fe2d 2026-07-24), isaaclab_rl 0.5.2, isaaclab_tasks 0.11.16 | 미기록 |
| rsl-rl-lib | 5.0.1 | >=4 (actor_state_dict checkpoints) |
| torch / Python | 2.7.0+cu128 / 3.11.9 | 미기록 |
| OS | Windows-10-10.0.19045-SP0 (Git Bash, Windows 대체 스크립트) | Linux |
| 에셋 | local mirror D:/dev/Nconnect/isaac_assets (kit_args asset_root); arrow_x.usd PLACEHOLDER (video arrow only) | NVIDIA S3 cloud |
| 학습 설정 | seed 42·43·44, 4096 env, 1000 iter, iter 900 고정, 평가 seed 101/202/303, 69 case | 동일 |
| 속도 | 약 18~37 s/iter (6GB VRAM 초과분 공유 메모리 사용), 행당 약 8.5~9시간 | 미기록 |
