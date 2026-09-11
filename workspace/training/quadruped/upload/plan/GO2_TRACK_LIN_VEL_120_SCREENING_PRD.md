# Go2 `track_lin_vel_xy_exp=1.20` 단일변수 1,000-iter screening PRD

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 proxy 70점 축에서 전진·전방위·환경 지형 추종을 개선한다.
- [현재 단계] 단계 3/6 — 환경 적응 게이트.
- [확보] Default-01 17.90699/70, Pilot-01 41.97990/70, G-A007 21.77258/70 및 7영상·69 telemetry를 확보했다.
- [미확보] 수정 evaluator의 G7 독립 DR, 다음 단일변수 후보의 3-seed 대표평가, `OFFICIAL_RESULT`.
- [이번 테스트] Default-01에서 `track_lin_vel_xy_exp`만 `1.0→1.2`로 바꾸어 Pilot의 큰 G1 개선 인과를 분리한다.
- [흐름] G-A007 폐기 → **G-A009 7-case 조기중단** → 통과 시 21-case 대표평가 → 실패 시 즉시 결과 ZIP → 최종 69-case·제출.
- [지금 할 일] 검증 완료된 ZIP 한 개를 업로드하고 README의 한 줄만 실행한다.
- [보장하지 않음] 1,000 iter·단일 학습 seed·내부 proxy는 공식 점수나 예선 통과를 보장하지 않는다. `OFFICIAL_RESULT_UNMEASURED`.

## 1. 실험 식별자와 단일 변경

| 항목 | 값 |
|---|---|
| work ID | `G-A009` |
| run ID | `train_260902-Go2_track_lin_vel_120_1000` |
| 기준 | Default-01 iter 800 |
| 기준 model SHA-256 | `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676` |
| 단일 변경 | `track_lin_vel_xy_exp: 1.0 → 1.2` |
| 학습 | from-scratch, seed 42, 4096 env, 1,000 iter |
| 평가 seed | tier 1=`101`; 대표평가=`101,202,303` |
| 공식 결과 | `OFFICIAL_RESULT_UNMEASURED` |

### 고정 reward

```text
track_lin_vel_xy_exp = 1.20  # 유일한 변경
feet_air_time        = 0.01
lin_vel_z_l2         = -3.00
ang_vel_xy_l2        = -0.08
action_rate_l2       = -0.01
```

`1.20`은 최적값 주장이 아니다. Pilot-01의 네 동시변경 중 선속도 추종 보상의 인과를 분리하는 진단점이다.

## 2. 값 선택 근거와 한계

- Default→Pilot G1 proxy는 `0.003619→0.892505`, 전체 내부 v1 proxy는 `17.90699→41.97990/70`이었다.
- `feet_air_time=0.20` 단독 G-A007의 G1은 `0.003553`으로 거의 변하지 않았고, 보정된 계단 순진행 중앙값은 Default 약 `0.336m` 대비 candidate 약 `0.049m`로 악화했다.
- 따라서 다음 정보가치 후보는 Pilot에 포함됐던 `track_lin_vel_xy_exp=1.20` 단일 변경이다.
- 강좌는 선속도 추종 reward와 한 번에 하나만 바꾸는 원칙을 제공한다. `1.20`이 NCRC 최적값이라는 공식 근거는 없다.
- G5 진행량은 env별 body-frame 속도 적분 중앙값으로 수정했다. G7은 평가 전용 마찰·반발·base mass·joint reset 범위를 켜 G3와 다른 fingerprint를 만든다. 이 DR 범위도 공식 evaluator 값이 아니라 내부 stress test다.

## 3. 직접 측정과 미측정

| 시나리오 | tier 1 직접 측정 | 대표평가 직접 측정 | 이번 테스트가 측정하지 않는 것 |
|---|---|---|---|
| G1 | fast forward survival·tracking | 3 seed 동일 case | 공식 command grid |
| G2 | diagonal-left survival·tracking | 3 seed 동일 case | 모든 전방위 명령 |
| G3 | rough-forward survival·tracking | 3 seed 동일 case | rough 전체 분포 |
| G4 | +20° survival·tracking | 3 seed 동일 case | -20° 방향 |
| G5 | 15cm up survival·tracking·env별 순진행 | 3 seed 동일 case | 10cm·down 전체 |
| G6 | +x push survival·회복·post-push tracking | 3 seed 동일 case | 나머지 3방향 push |
| G7 | repaired DR seed 101 | repaired DR 3 seed | 공식 DR 항목·범위 |

## 4. 비용 게이트와 분기

1. 학습 뒤 tier 1은 candidate 7 case와 Default G7 repaired-DR 1 case만 실행한다.
2. 다음 중 하나면 `INTERNAL_EARLY_KILL_FAIL`로 즉시 중단하고 결과 ZIP을 만든다.
   - candidate weighted proxy가 보정 baseline보다 낮음
   - G1 proxy 개선이 `+0.05` 미만
   - 어느 시나리오든 survival이 baseline보다 `0.10` 초과 하락
3. tier 1 통과 때만 seed 202·303의 14 case를 추가해 총 21 candidate case를 만든다.
4. 대표평가 승급은 **60/70 이상**, G1~G7 각각 `survival≥0.95`와 `tracking≥0.70`, 세 seed 완결을 모두 요구한다.
5. 69-case 전체평가는 이 package에서 실행하지 않는다. 대표평가 승급 후에만 별도 실행한다.

## 5. 영상·artifact 계약

- 영상 판정: `VIDEO_REQUIRED`.
- 필수 영상: candidate G1 `forward_fast`, seed 101, 4 env, 500 step, 1개.
- 필수 telemetry: 조기중단 시 candidate 7 + baseline 7, 대표평가 시 candidate 21 + baseline 7.
- 필수 학습물: `model_best.pt`, `env.yaml`, checkpoint/tfevents/params, source, reward diff.
- 필수 정책물: `policy.pt`, `POLICY_LINEAGE.json`.
- 정상 결과: `/workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 실패도 `PARTIAL` ZIP으로 checkpoint·log·완료 case를 자동 회수한다.
- 서버 종료는 결과 ZIP과 SHA가 로컬에 도착해 무결성·case·영상·lineage를 확인한 뒤 판정한다.

## 6. 결과별 다음 분기

| 결과 | 다음 행동 |
|---|---|
| `INTERNAL_EARLY_KILL_FAIL` | 이 후보 폐기; 추가 seed·69-case·장기학습 금지 |
| `INTERNAL_REPRESENTATIVE_PROMOTION_FAIL` | 감점 시나리오·약한 인수 재분석; 장기학습 금지 |
| `INTERNAL_REPRESENTATIVE_PROMOTION_PASS` + `VIDEO_OBSERVED` 이상 없음 | 독립 학습 seed 또는 기체 전용 69-case 중 정보가치 높은 순서 결정 |
| evaluator/영상/artifact 누락 | `INTERNAL_GATE_INCONCLUSIVE`; 같은 checkpoint로 복구 우선 |

