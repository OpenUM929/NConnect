# Go2 G-A010 `lin_vel_z_l2=-2.0` 단일변수 screening PRD

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 proxy 70점 축에서 G1 전진 추종과 G3·G5 지형 적응의 정보가치를 확인하고, 설계 의도·리포트 축에 단일변수 근거를 남긴다.
- [현재 단계] 단계 2/6 — 짧은 학습 pilot.
- [확보] Default-01 기준 artifact, repaired-v2 evaluator, G-A007·G-A009 실패 판정, G-A009 G1 `VIDEO_OBSERVED`.
- [미확보] `lin_vel_z_l2=-2.0` 단독 candidate checkpoint, tier-1 G1~G7, G1 영상, 독립 학습 seed.
- [이번 테스트] Default-01에서 `lin_vel_z_l2 -3.0→-2.0`만 바꿔 G1 개선과 survival 비열등성을 판정한다.
- [흐름] G-A009 실패 → **G-A010 1k+tier-1** → 통과 시 21-case → 실패 시 G-A011 → 최종 제출.
- [지금 할 일] 로컬 검증된 engine ZIP과 G-A010 JSON을 서버에 업로드하고 한 줄 명령을 실행한다.
- [보장하지 않음] 단일 seed·1,000 iter·내부 proxy는 공식 점수, 최적 reward 또는 예선 통과를 보장하지 않는다.

## 1. 목적과 가설

G-A007 `feet_air_time=0.20`과 G-A009 `track_lin_vel_xy_exp=1.20`은 목표 G1을 개선하지 못했다.
Pilot-01에 함께 들어 있던 아직 분리되지 않은 값 중 `lin_vel_z_l2 -3.0→-2.0`의 단독 효과를
측정한다. 약한 수직 속도 벌점이 동작성을 늘릴 수 있지만 바운딩·착지 불안정을 만들 수 있으므로
G1 proxy와 모든 시나리오 survival을 동시에 본다. 강좌의 1k 전진 관찰은 출발 근거일 뿐 최적값
증명이 아니다.

## 2. 사전등록 입력

| 항목 | 고정값 |
|---|---|
| 기준 policy | Default-01 iter 800, model SHA `99ceeaa1…4676` |
| 단일 변경 | `lin_vel_z_l2 -3.0→-2.0` |
| 유지 reward | `track_lin_vel_xy_exp=1.0`, `feet_air_time=0.01`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01` |
| 학습 | from-scratch, seed 42, 4096 env, 1,000 iter |
| tier-1 | seed 101, G1~G7 대표 7 case + repaired baseline G7 1 case |
| 조건부 대표평가 | tier-1 통과 때만 seed 202·303 추가, candidate 총 21 case |
| 영상 | `VIDEO_REQUIRED`, G1 forward-fast, seed 101, 4 env, 500 step, 1개 |

기계판독 정본은 `config/experiments/G_A010_lin_vel_z_m2.json`이다.

## 3. 직접 측정 범위

| 시나리오 | 영상 | 내부 정량 | 공식 결과 |
|---|---|---|---|
| G1 전진 속도 추종 | forward-fast 1개 필수 | survival·tracking proxy | `OFFICIAL_RESULT_UNMEASURED` |
| G2 전방위 속도 추종 | `VIDEO_UNKNOWN` | diagonal-left survival·tracking | `OFFICIAL_RESULT_UNMEASURED` |
| G3 거친 지형 | `VIDEO_UNKNOWN` | rough-forward survival·tracking | `OFFICIAL_RESULT_UNMEASURED` |
| G4 경사 ±20° | `VIDEO_UNKNOWN` | +20° 대표 방향만 | `OFFICIAL_RESULT_UNMEASURED` |
| G5 계단 10~15cm | `VIDEO_UNKNOWN` | 15cm up survival·tracking·보정 진행 | `OFFICIAL_RESULT_UNMEASURED` |
| G6 밀침 회복 | `VIDEO_UNKNOWN` | +x push survival·recovery·tracking | `OFFICIAL_RESULT_UNMEASURED` |
| G7 도메인 랜덤화 | `VIDEO_UNKNOWN` | repaired DR seed 101 | `OFFICIAL_RESULT_UNMEASURED` |

## 4. 조기판정과 분기

다음 중 하나면 `INTERNAL_EARLY_KILL_FAIL`로 결과 ZIP을 즉시 만든다.

1. candidate weighted proxy가 repaired baseline보다 낮다.
2. G1 scenario proxy 개선이 `+0.05` 미만이다.
3. 어느 G든 survival proxy가 baseline보다 `0.10` 초과 하락한다.

모두 충족한 경우에만 seed 202·303을 추가한다. 대표평가 승급은 candidate `60/70` 이상,
G1~G7 각각 survival `0.95` 이상·tracking `0.70` 이상, 세 seed 완결을 동시에 요구한다.

## 5. Artifact·회수 계약

- engine: `go2_tuning_engine_v1.zip`과 `.sha256`.
- experiment: `config/experiments/G_A010_lin_vel_z_m2.json`과 `.sha256`.
- 완료 표식: `[DONE] GO2_LIN_VEL_Z_M2_RESULT_READY`.
- 결과: `/workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip`과 `.sha256`.
- 성공·실패 모두 engine/spec identity, checkpoint, env, log, source, reward diff, 완료 telemetry,
  G1 영상, policy lineage를 가능한 범위에서 자동 패키징한다.
- 두 결과 파일을 로컬 `workspace/_keep/`에 내려받아 외부 SHA·CRC·manifest·case·영상·lineage를
  확인하기 전에는 서버 종료 가능 판정을 내리지 않는다.

## 6. 결과별 NEXT

| 결과 | 다음 행동 |
|---|---|
| `INTERNAL_EARLY_KILL_FAIL` | G-A010 폐기, G-A011 `ang_vel_xy_l2 -0.08→-0.05` only |
| `INTERNAL_REPRESENTATIVE_PROMOTION_FAIL` | 최대 감점 scenario와 survival/tracking 약한 인수 재분석 |
| `INTERNAL_REPRESENTATIVE_PROMOTION_PASS` + G1 영상 이상 없음 | 독립 학습 seed 재검증; 즉시 장기학습 금지 |
| artifact/evaluator/video 누락 | `INTERNAL_GATE_INCONCLUSIVE`; 같은 checkpoint로 회수 복구 우선 |

