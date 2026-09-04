# Go2 Reward Evidence Master

## 0. 목적

Go2 reward 값의 **출처**, 실제 **성능 증거**, G1~G7 직접 측정 범위와 한계를 분리한다.
코드 주석이나 강좌의 예시는 후보 출발점이며 NCRC 최적값이 아니다.

## 1. 현재 정책 역할

- 실험 기준선: 배포 기본 reward의 `Default-01` — seed 42, 4096 env, 1,000 iter, model SHA `99ceeaa1…4676`
- 비교군: `train_260831-Go2_5var_1000`, iter 999, SHA `c4d78adf…af8d`
- 비교군 분류: `MULTIVARIABLE_EXPLORATORY_BASELINE`
- 비교군 진단: reward 18.02@972, terrain 3.94, training-terrain fall diagnostic 13.8%, std 0.499
- 제한: 네 reward 동시 변경, 학습 seed 1개. G1~G7 격리 telemetry는 확보됐으나 reward별 인과 귀속은 불가

## 2. reward 대장

| reward | 강좌 배포 기준 | Pilot-01 | 변경 | 역할·출처 | 현재 성능 판정 | 직접 측정 G | 한계 |
|---|---:|---:|---:|---|---|---|---|
| `track_lin_vel_xy_exp` | 1.0 | 1.2 | +0.2 | 속도 추종. 강좌 14강은 1.0→1.5 단일변수 예시 | **미만족 — G-A009 단독 1.20 조기중단** | G1~G7 tier 1 | seed 101 G1 delta `-0.0000663`; Pilot 개선은 다른 동시 변경 또는 상호작용 가능 |
| `feet_air_time` | 0.01 | 0.2 | +0.19 | 발 들기. 강좌는 낮으면 발을 거의 안 든다고 설명 | **미만족 — G-A007 단독 0.20 screen fail** | G1~G7 69-case·7영상 | G1 정체, 보정 G5 진행 회귀, 60/70 승급선 미달; foot contact 직접 계측 없음 |
| `lin_vel_z_l2` | -3.0 | -2.0 | 완화 | 상하 흔들림. 강좌 14강의 1k 예시는 -3→-2 후 전진 관찰 | **INCONCLUSIVE** | G3~G5·G7 | 적극적 이동과 안정성 trade-off 가능, 단독 실험 없음 |
| `ang_vel_xy_l2` | -0.08 | -0.05 | 완화 | 몸통 roll/pitch 흔들림 억제 | **INCONCLUSIVE** | G2~G5·G7 | 경사·회전 개선과 rough/stairs 불안정이 공존, 단독 실험 없음 |
| `action_rate_l2` | -0.01 | -0.01 | 불변 | 관절 명령 급변·떨림 억제 | **미측정** | 14개 영상은 관찰 | jerk·관절 명령 급변 정량 없음 |
| `track_ang_vel_z_exp` | 0.75 | 0.75 | 불변 | 회전 추종, env 기본 활성 | **부분 만족** | G2 | Pilot G2 worst survival 1.0·tracking .7521, 단독 yaw reward 효과는 아님 |
| `flat_orientation_l2` | 0.0 | 0.0 | 불변 | 현재 Go2 env에서는 비활성 | **미측정** | 없음 | H1 자세 reward 결론 복사 금지 |
| termination penalty | 미정의 | 미정의 | — | 현재 env termination은 base contact 조건 | **미측정** | 없음 | 없는 항을 임의 추가하지 않음 |

## 3. 현재 만족/미만족 표

| 분류 | 항목 |
|---|---|
| 만족 | 없음 — Pilot 전체도 `INTERNAL_GATE_FAIL` |
| 부분 만족 | Pilot 조합의 G1·G2·G6; 불변 `track_ang_vel_z_exp`의 현재 G2 행동 |
| 미만족 | Pilot 조합의 G3·G4·G5·G7; `feet_air_time=0.20` 단독; `track_lin_vel_xy_exp=1.20` 단독 |
| 미측정 | action_rate jerk, 공식 결과, 독립 학습 seed, termination reward 효과 |
| INCONCLUSIVE | `lin_vel_z_l2`, `ang_vel_xy_l2` 개별 인과효과와 두 항의 상호작용 |

## 4. 강좌 기반 실험 원칙

근거: 강좌 14강.

1. reward는 가중합이며 항목 간 비율이 행동을 바꾼다.
2. 한 번에 하나씩 바꾸어 변인을 통제한다.
3. 숫자와 `play.py` 영상을 함께 비교한다.
4. 짧은 실험으로 방향을 잡고 최종 후보만 길게 학습한다.
5. 과한 속도는 장애물 안정성을, 과한 feet_air는 bounding을, 과한 penalty는 정지 편법을 만들 수 있다.

Pilot-01은 1항의 trade-off를 탐색한 기준선이지만 2항의 인과설계를 충족하지 못했다.

## 5. 다음 후보 선정 규칙

1. 정확한 G1~G7 자체평가에서 `weight × (1-scenario_proxy)`가 가장 큰 시나리오를 찾는다.
2. 그 시나리오의 survival과 tracking 중 약한 인수를 확인한다.
3. 약한 인수와 직접 연결되는 reward 하나만 후보로 고른다.
4. 배포 기본 Default-01에서 한 항만 바꾸고 동일 evaluator·seed·iteration으로 비교한다.
5. 성공은 primary 개선 + 나머지 G worst-case 비열등 + 정상 네발 gait를 모두 요구한다.

Default/Pilot 쌍대평가 완료 뒤 현재 다음 reward 값은 **`feet_air_time 0.20` 단일변수**로 확정됐다. 이는 최적값 판정이 아니라 G5 개선과 G3/G5 survival 회귀의 인과 분리점이다.

## 8. Default-vs-Pilot FULL 분석 — 260901

- Default `17.90699/70`, Pilot `41.97990/70`, delta `+24.07291/70`; 둘 다 `INTERNAL_GATE_FAIL`.
- Pilot은 G1·G2·G6 `INTERNAL_SCENARIO_PASS`, G3·G4·G5·G7 `INTERNAL_SCENARIO_FAIL`이다.
- 세 평가 seed delta가 모두 양수지만 학습 seed는 42 하나라 독립 학습 재현성은 미확보다.
- 최대 감점은 G5 `8.12/70`, 다음은 G3 `7.84/70`. G5의 약한 인수는 tracking/completion이다.
- 분기: `SHARED_WEAKNESS_FOUND`. Pilot은 비교 상한으로 보존하되 resume하지 않고, Default 계보에서 한 항씩 재검증한다.
- 첫 사전등록 후보: `feet_air_time .01→.2` 단일 변경 1,000 iter. 최적값 주장이 아니라 Pilot 개선·회귀의 인과 분리 실험이다.
- 영상: 정책별 7개, 총 14개 contact sheet 직접 관찰로 `VIDEO_OBSERVED`; 연속 gait timing·foot contact는 미측정.
- 상세: `workspace/training/quadruped/reports/GO2_DEFAULT_VS_PILOT_ANALYSIS_260901.md`.

## 5-a. 배포 기본 control 상태 — 260901 결정

- `exported/model_best_20260831154121.pt`는 별도 SHA를 가지지만 paired
  `env_20260831154121.yaml`도 Pilot-01 튜닝 reward `1.2/0.2/-2.0/-0.05/-0.01`을 보유한다.
- 따라서 이 timestamped backup은 배포 기본 control의 성능·lineage 근거가 아니다.
- provenance-valid control은 현재 **미확보**다. Default-01은 기본값·seed 42·4096 env·1,000 iter로
  from-scratch 생성하며, 조건부가 아닌 첫 쌍대 비교의 필수 기준이다.
- 260901 실행 package `go2_default_vs_pilot_v1.zip`은 위 값을 reward-only staging으로 고정해 로컬
  검증됐지만 아직 서버 학습 artifact가 아니므로 control 성능은 계속 **미측정**이다.
- control 생성 전까지 Pilot-01이 배포 기본보다 개선됐다는 표현은 금지한다.
- 향후 reward screening은 Default-01 계보에서 하나씩 추가한다. Pilot-01은 resume하지 않는다.

## 5-b. Default-01 ↔ Pilot-01 비교 규칙

- 두 정책 모두 같은 G1~G7 registry, 평가 seed 101/202/303, case fingerprint를 사용한다.
- `Train/mean_reward`는 reward 계수가 달라 정책 간 비교에서 제외한다.
- survival·tracking·completion·recovery·영상 부작용만 비교한다.
- weighted simulation proxy 차이 `0.03`, survival 비열등 `-0.02`, tracking 비열등 `-0.05`를
  내부 의사결정 허용오차로 사전등록한다.
- 상세 분기는 `workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md` §6을 따른다.

## 6. 과학적 표현 규칙

- 두 관측점은 탐색이지 최적값 증명이 아니다.
- 평가 seed 반복은 정책 평가 변동성만 다루며 독립 학습 seed 재현성을 증명하지 않는다.
- 평균 reward·terrain level·training base_contact는 G1~G7 공식 survival/tracking과 다르다.
- 내부 `exp(-(RMSE/std)^2)`는 candidate env의 reward 모양을 빌린 proxy이며 공식식이 아니다.
- 최종 제출문은 실제 검증된 문제·변경·결과·한계만 30~200자로 요약한다.

## 7. Default-vs-Pilot 부분 결과 반영 — 260901

- Default-01은 seed 42, 4096 env, 1,000 iter의 학습 artifact와 G1~G7 telemetry 69/69까지 확보했다.
- Pilot-01 telemetry는 runner 오류로 0/69이며 비교 보고서와 영상도 아직 없다.
- 따라서 `track_lin_vel_xy_exp`, `feet_air_time`, `lin_vel_z_l2`, `ang_vel_xy_l2`, `action_rate_l2`의 만족도는 모두 기존처럼 `미측정` 또는 `INCONCLUSIVE`를 유지한다.
- Default 단독 telemetry가 존재해도 Pilot 대비 개선량과 네 reward 동시변경의 인과효과를 판정하지 않는다.
- 다음 reward 학습은 FULL paired 결과와 PRD §6 분기 판정 전까지 `HOLD — 평가 미완료`다.
- 근거: `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/INGEST_STATUS.md`, 작업 `G-A006`.

## 9. `feet_air_time=0.20` 단일변수 사전등록 — G-A007

| reward | 기준 | candidate | 사전 상태 | 직접 측정 | 승급 전 필요한 증거 |
|---|---:|---:|---|---|---|
| `feet_air_time` | `0.01` | `0.20` | **INCONCLUSIVE — 실험 승인, 결과 미측정** | G1~G7 survival·tracking, G5 completion, 7영상 | G5 proxy `+0.03`, G5/전 G survival 비열등, 전 G tracking 비열등, 영상 부작용 없음 |

- 유지 reward: `track_lin_vel_xy_exp=1.0`, `lin_vel_z_l2=-3.0`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`.
- 기준 policy: Default-01 iter 800, model SHA `99ceeaa1…4676`.
- 학습: from-scratch, seed 42, 4096 env, 1,000 iter. 단일 학습 seed이므로 결과는 `exploratory`다.
- 평가: fixed registry, seeds 101/202/303, candidate telemetry 69건, worst-case 영상 7개.
- 현재 package: `go2_feet_air_time_020_v1.zip`, SHA `36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f`, `ARTIFACT_VERIFIED`.
- 외부 실행·candidate 성능·공식 결과는 아직 `[미측정]` / `OFFICIAL_RESULT_UNMEASURED`다.
- 상세 사전등록: `workspace/training/quadruped/reports/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md`.

## 10. G-A007 PARTIAL? evaluator v2 ?? ? 260901

- candidate ??? ????? telemetry 8/69??? 0/7??? `feet_air_time=0.20` ??? ?? `INCONCLUSIVE`?.
- ??? reward ?? ??? ??? ?? runner ?? ??? ????. ??? reward ?? ???? ????? ???.
- ?? ??? ?? candidate model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5`? ?? ??? ????.
- v1 runner? ?? ???? `BUGGY_DO_NOT_REUSE`; graceful shutdown?bounded retry? ??? v2 package? ????.



## 8. 260902 G-A007 결과와 후속 평가비용 결정

- `feet_air_time 0.01→0.20` 단일변수 후보는 artifact·7영상까지 확보했지만 내부 v1 proxy가 `21.77258/70`로 대표평가 full-suite 승급선 `60/70`에 미달한다.
- G5 기존 진행도는 env 간 초기 위치를 섞은 전역 max-min이므로 무효다. 기존 CSV를 body-frame 속도로 재적분하면 계단 진행 중앙값은 Default 약 `0.336m`, Pilot 약 `4.218m`, candidate 약 `0.049m`다.
- G7은 같은 seed의 G3 `rough_forward`와 byte-identical telemetry여서 독립 DR 근거가 아니며 `INTERNAL_GATE_INCONCLUSIVE`로 정정한다.
- 따라서 `feet_air_time=0.20`은 **미만족 / INTERNAL_SCREEN_FAIL**이며 장기 승급하지 않는다.
- 이후 모든 H1·Go2 신규 후보는 `6~8 case 조기중단 → 21 case 대표평가 → 60/70과 안정성 동시 충족 시 기체별 전체평가` 순서를 사용한다.
- 69-case의 직접 출처는 강좌가 아니다. 강좌·가이드는 G1~G7 범주·가중치와 단일변수 조정 원칙을 제공했고, case grid·평가 seed·69건 합계는 내부 설계다.

## 9. G-A009 `track_lin_vel_xy_exp=1.20` 단일변수 사전등록 — 260902

| reward | 기준 | candidate | 상태 | 직접 측정 | 승급 전 필요한 증거 |
|---|---:|---:|---|---|---|
| `track_lin_vel_xy_exp` | `1.00` | `1.20` | **미만족 — `INTERNAL_EARLY_KILL_FAIL`** | G1~G7 tier 1 survival·tracking, G5 보정 진행, G6 회복, G7 repaired DR, G1 영상 파일 | 목표 G1 `+0.05` 미충족; 대표평가·장기 승급 금지 |

- 고정: `feet_air_time=0.01`, `lin_vel_z_l2=-3.0`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`.
- 기준: Default-01 iter 800, model SHA `99ceeaa1…4676`; from-scratch seed 42, 4096 env, 1,000 iter.
- 근거: Pilot G1 `0.892505` vs Default `0.003619`; G-A007 feet-air 단독 G1 `0.003553` 및 보정 계단 진행 회귀.
- 한계: Pilot은 4변수 동시 변경이므로 `track=1.20`의 인과·최적성은 아직 확정되지 않았다.
- 비용 분기: 7 candidate + 1 Default repaired-G7 조기평가에서 회귀면 자동 종료; 통과 때만 candidate 21-case.
- package: `go2_track_lin_vel_120_v1.zip`, SHA `8d341d5dbae5aac6c6a4376442f2cdf20264fa2439d3b22c68e64811a81aefa7`, `ARTIFACT_VERIFIED`(업로드 package만).
- 외부 실행: 완료. candidate `20.62741/70`, repaired baseline `17.53712/70`; G1 delta `-0.0000663`, `VIDEO_UNKNOWN`, `OFFICIAL_RESULT_UNMEASURED`.
- 상세 PRD: `workspace/training/quadruped/reports/GO2_TRACK_LIN_VEL_120_SCREENING_PRD.md`.

## 10. G-A009 결과 — 260902

- artifact: FULL result ZIP SHA `d9d84f68c19eac9c84ec932154c7edf9d40743b8a05e92468ff0348bbc7661c3`, manifest 125/125, candidate/baseline 7/7, 영상 1, lineage 8/8로 `ARTIFACT_VERIFIED`.
- primary: G1 proxy `0.00356288`, baseline `0.00362921`, delta `-0.0000663`; 사전 최소 개선 `+0.05`에 미달.
- secondary: 총 내부 proxy는 `20.62741/70`로 baseline `17.53712/70`보다 `+3.09028` 높지만 주로 G6 개선의 영향이며 G1 목적을 충족하지 못한다.
- scenario gate: G1·G2·G3·G4·G5·G7 `INTERNAL_SCENARIO_FAIL`, G6만 `INTERNAL_SCENARIO_PASS`; seed 101 exploratory 결과다.
- 판정: `track_lin_vel_xy_exp=1.20` 단독 후보는 **미만족 / INTERNAL_EARLY_KILL_FAIL**. 대표 3-seed·69-case·장기학습으로 승급하지 않는다.
- 영상·공식: G1 영상은 직접 판독해 `VIDEO_OBSERVED`; 네 환경 모두 전진 명령 대비 시작 격자 부근에 머물러 정량 실패와 일치한다. G2~G7은 `VIDEO_UNKNOWN`; `OFFICIAL_RESULT_UNMEASURED`.

## 11. G-A009 최종 분석과 G-A010 선정 — 260902

- 동일 repaired-v2 tier-1에서 총 내부 proxy는 Default `17.53712/70` 대비 candidate `20.62741/70`, `+3.09028`이다.
- 증가분 기여는 G6 `+2.41007/70`(`77.99%`), G3 `+0.61589/70`(`19.93%`) 순이다. 목표 G1은 `-0.00070/70`로 개선되지 않았다.
- 학습 best reward `16.2977@900`과 마지막 training-terrain 낙상 진단 `6.52%`는 고정 G1 evaluator 점수가 아니다. G1 evaluator의 평균 속도는 `0.02748 m/s`, tracking RMSE `1.18714`다.
- G-A009 최종 분류는 `미만족 / INTERNAL_EARLY_KILL_FAIL`; 상세 보고서는 `workspace/training/quadruped/reports/GO2_TRACK_LIN_VEL_120_RESULT_ANALYSIS_260902.md`다.
- 다음 정보가치 1순위는 Default 계보 `lin_vel_z_l2 -3.0→-2.0` 단독 1,000 iter다. 강좌의 1k 전진 관찰과 남은 미분리 Pilot 항이라는 점을 근거로 하며 최적값 주장은 아니다.
- G-A010 실패 시 `ang_vel_xy_l2 -0.08→-0.05` 단독 G-A011로 간다. 둘 다 실패할 때만 두 항의 상호작용을 검토한다.

## 12. G-A010 `lin_vel_z_l2=-2.0` 단일변수 사전등록·package — 260902

| reward | 기준 | candidate | 현재 상태 | 직접 측정 | 승급 전 필요한 증거 |
|---|---:|---:|---|---|---|
| `lin_vel_z_l2` | `-3.0` | `-2.0` | **미측정 — upload package `ARTIFACT_VERIFIED`** | 실행 뒤 G1~G7 tier-1 survival·tracking, G1 영상 | G1 `+0.05`, 전 G survival 회귀 `≤0.10`, weighted proxy 비회귀 |

- 유지값: `track_lin_vel_xy_exp=1.0`, `feet_air_time=0.01`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`.
- 학습: Default-01 from-scratch, seed 42, 4096 env, 1,000 iter. 단일 학습 seed이므로 결과는 exploratory다.
- engine v1.0 SHA `4489bef4…8a5a`는 서버 bare `python3` 결함으로 `BUGGY_DO_NOT_REUSE`; 학습 시작 전 실패했다.
- 현재 engine v1.1: `workspace/training/quadruped/upload/G-A010/current/go2_tuning_engine_v1_1.zip`, SHA `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- 현재 experiment spec: 같은 폴더의 `G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`; release 이력은 `upload/G-A010/UPLOAD_HISTORY.tsv`에서 관리한다.
- 같은 폴더의 spec: `workspace/training/quadruped/G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- engine은 reward 값을 내장하지 않고 JSON을 schema·Default identity·정확히 한 reward 변경으로 검증한 뒤 runtime source를 만든다.
- 실행 전 상태는 `ARTIFACT_VERIFIED`일 뿐 candidate 성능·영상·내부 gate·공식 결과는 `[미측정]` / `VIDEO_UNKNOWN` / `OFFICIAL_RESULT_UNMEASURED`다.
- 상세 PRD: `workspace/training/quadruped/reports/GO2_LIN_VEL_Z_M2_SCREENING_PRD.md`.
