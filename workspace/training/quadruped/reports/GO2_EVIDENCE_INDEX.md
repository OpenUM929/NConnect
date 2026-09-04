# Go2 Evidence Index

## Pilot-01

| 증거 | 경로 | 식별/상태 |
|---|---|---|
| reward source | `../quadruped_rewards.py` | SHA `2b432994…5a37` |
| checkpoint | `../exported/model_best.pt` | SHA `c4d78adf…af8d` |
| recovered checkpoint | `../../../_keep/train_260831-Go2_5var_1000/train_260831-Go2_5var_1000_DOWNLOAD/quadruped/logs/rsl_rl/quadruped/2026-08-31_15-42-43/model_999.pt` | exported와 SHA 일치 |
| env | `../exported/env.yaml` | SHA `f5550641…975d` |
| recovered env | recovered run `params/env.yaml` | exported와 SHA 일치 |
| TensorBoard | recovered run `events.out.tfevents.*` | 존재 |
| report | `../exported/report.html` | reward 18.02@972, terrain 3.94, fall diagnostic 13.8%, std .499 |
| generic video | `../exported/play_video.mp4` | SHA `5beb7445…957c`, checkpoint sidecar 없음 |
| tar | `../../../_keep/train_260831-Go2_5var_1000/...DOWNLOAD.tar.gz` | SHA `3eb3b697…1b4a` |
| policy | `../exported/policy.pt` | **없음** |

## 강좌·가이드

| 주제 | 경로·줄 |
|---|---|
| G1~G7·가중치 | `workspace/PRELIM_RL_GUID.md:60-70` |
| survival×tracking | `workspace/PRELIM_RL_GUID.md:95-100` |
| Go2 reward 역할·trade-off | 강좌 14강 659~730 |
| Go2 단계 예시 | 강좌 14강 916~1121 |
| 정량+영상 진단 | 강좌 15강 578~588, 745~927 |
| policy 제출 흐름 | 강좌 16강 578~731 |
| 1라운드 실제 제출 필드 | 사용자 제공 대시보드 원문(260901) |

## 격리 대상

| 파일 | 상태 | 이유 |
|---|---|---|
| `../server_run_Go2_videos.sh` | `LEGACY_INVALID_MAPPING` | 제공 Go2 G1~G7와 ID·조건 불일치 |

## 증거 공백

- G1~G7 격리 telemetry·영상 전부
- 평가 seed 반복
- policy actor tensor lineage
- 공식 evaluator 상세와 공식 결과
- 대시보드 제출 여부
