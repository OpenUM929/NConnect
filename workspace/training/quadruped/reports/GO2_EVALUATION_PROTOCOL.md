# Go2 Preliminary Self-Evaluation Protocol v1

## 0. 상태

- 분류: `INTERNAL_PROXY_SPEC`
- 목적: 공식 evaluator가 공개되지 않은 상태에서 제출 전 약점과 회귀를 보수적으로 찾는다.
- 정본: `../config/go2_self_eval_registry.json`
- 금지: `공식 재현`, `공식 점수`, bare `PASS` 표현

## 1. 공식/제공 개념과 내부 가정

제공 가이드는 `scenario score = survival_rate × tracking_score`와 G1~G7 가중치를 제시한다.
정확한 tracking 변환, 명령 grid, terrain, push, DR 범위, seed와 통과선은 공개되지 않았다.

내부 v1:

```text
tracking_proxy = exp(-(RMSE / env_track_std)^2)
scenario_proxy = survival_proxy * tracking_proxy
simulation_proxy = Σ(weight_i * scenario_proxy_i)
simulation_points = 70 * simulation_proxy
```

`env_track_std`는 평가 대상 `env.yaml`에서 읽는다. 현재 Pilot-01은 0.5다.

## 2. 사전 게이트

- 각 scenario survival ≥0.95
- 각 scenario tracking ≥0.70
- G1~G7 모두 측정
- 방향·강도 쌍은 최악 case 채택
- 평가 seed 101·202·303 모두 완료
- weighted simulation proxy ≥0.70
- 총 자체예상 최소 70/100, 운영 목표 75/100

한 항목이라도 빠지면 `SELF_ASSESSMENT_INCOMPLETE`; 누락 scenario는 보수적으로 0점이다.

## 3. scenario 설계

| ID | 내부 case | 핵심 telemetry | 영상 관찰 |
|---|---|---|---|
| G1 | slow/nominal/fast forward | command vx, actual vx, RMSE, termination | 네발 gait, drift, 배 끌기 |
| G2 | backward, ±lateral, ±diagonal, ±combined yaw | command/actual xyz-yaw, worst tracking | 방향 편향, 회전 중 gait |
| G3 | rough forward/lateral | terrain realized values, survival, xy RMSE | 걸림·미끄러짐·발 들기 |
| G4 | +20°/-20° | 실제 경사각, survival, xy RMSE | 상승·하강 자세 |
| G5 | 10/15cm × up/down | 실제 step height, completion, survival, tracking | 발 걸림·배 접촉·점프 편법 |
| G6 | ±x/±y push | 사건 시각·크기·방향, recovery time, post-push tracking | 충격·복원 인과관계 |
| G7 | rough+DR seed 101/202/303 | 실현 mass/friction/기타 DR 값, survival, tracking | 조건별 gait 붕괴 |

G2 정확한 공식 명령 집합, G3 rough 세기, G5 상·하행 여부, G6 push 조건, G7 DR 범위는 미공개다.
구현 시 내부값을 package 버전에 고정하고 meta에 모두 기록한다.

## 4. G7 주의

Pilot-01 env는 base mass -1~+3kg을 randomize하지만 friction은 static 0.8/dynamic 0.6 고정이다.
고정 friction을 마찰 DR로 보고하지 않는다. evaluator가 추가 DR을 적용하면 source와 실현값을 보존하고,
적용하지 않으면 G7은 `INTERNAL_GATE_INCONCLUSIVE`다.

## 5. 영상과 정량의 분리

- 영상은 네발 정상 gait, 배 끌기, bounding, 발 미끄러짐, 떨림, 정지 편법을 관찰한다.
- 영상에는 scenario ID, seed, command, terrain/push/DR 실현값, model SHA overlay 또는 sidecar가 있어야 한다.
- `VIDEO_OBSERVED`는 survival/tracking 통과가 아니다.
- telemetry가 긍정적이어도 영상에서 reward hacking이 보이면 후보 승급을 보류한다.

## 6. package 산출물 계약

```text
meta/run.json
meta/source_sha256.txt
meta/model_sha256.txt
meta/env_sha256.txt
meta/registry.json
cases/<seed>/<case>/steps.csv
cases/<seed>/<case>/summary.json
cases/<seed>/<case>/play.log
videos/<seed>/<case>.mp4
VIDEO_STATUS.tsv
RUNNER_STATUS.txt
SHA256SUMS.txt
SELF_EVAL_REPORT.json
SELF_EVAL_REPORT.md
```

각 script는 `[STARTED]`, `[MONITOR]`, `[RESULT]`, `[DONE]`과 정확한 다운로드 경로를 출력한다.

## 7. 구현 검증

서버 package 전 다음을 모두 통과한다.

1. registry G1~G7 정확성·weight 합 1
2. Python compile 및 unit test
3. `bash -n`, CRLF 0
4. ZIP CRC, 안전한 상대경로, 내부 manifest
5. embedded model/env SHA
6. scenario case 수·필수 telemetry field test
7. score 재계산 golden test
8. legacy runner 파일을 import/호출하지 않는 정적 검사

## 8. 결과 판정

- `INTERNAL_GATE_PASS`: 해당 scenario의 모든 pre-registered gate 충족
- `INTERNAL_GATE_FAIL`: survival/tracking/영상 반증 중 하나 실패
- `INTERNAL_GATE_INCONCLUSIVE`: 필수 telemetry·사건·실현값·case 누락
- `SELF_ASSESSMENT_PASS`: G1~G7 전체 완료·통과 + weighted proxy gate 충족
- `SELF_ASSESSMENT_INCOMPLETE`: 하나라도 누락/INCONCLUSIVE
- `OFFICIAL_RESULT_UNMEASURED`: 운영진 결과 미회수

## 9. 개선 분기

1. 최대 감점 scenario를 고른다.
2. survival과 tracking 중 약한 인수를 고른다.
3. `GO2_REWARD_EVIDENCE_MASTER.md`에서 직접 관련 reward 하나를 선택한다.
4. 1,000~5,000 iter 단일변수 screening을 사전등록한다.
5. primary 개선, 나머지 scenario worst-case 비열등, 영상 부작용 없음이면 장기 후보로 승급한다.

## 10. 기존 runner 격리

`server_run_Go2_videos.sh`는 역사적 H1형 매핑 산출물이다. 삭제하지 않지만 이 protocol의 source,
case, report, G1~G7 근거에 포함하지 않는다. 새 파일명은 `server_run_go2_eval_v1.sh` 계열을 사용한다.
