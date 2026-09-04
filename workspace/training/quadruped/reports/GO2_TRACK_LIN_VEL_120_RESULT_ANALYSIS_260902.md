# Go2 G-A009 `track_lin_vel_xy_exp=1.20` 결과 분석 — 260902

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 proxy /70 개선 여부를 판별하고 설계 의도 /20·리포트 /10의 근거를 보존한다.
- [현재 단계] **단계 2/6 — 짧은 학습 pilot**. Default 계보 단일변수 1,000-iter screening에서 아직 승자가 없다.
- [확보] G-A009 FULL bundle·정책 lineage·candidate/baseline tier-1 telemetry·G1 영상이 `ARTIFACT_VERIFIED`; G1 영상은 직접 판독했다.
- [미확보] 대표 3-seed, Go2 69-case, G1~G7 전체 내부 통과 후보, 독립 학습 seed, `OFFICIAL_RESULT`.
- [이번 테스트] `track_lin_vel_xy_exp 1.0→1.2`가 Default-01보다 G1 전진 추종을 직접 개선하는지 판정한다.
- [흐름] G-A009 회수 → **비교 분석 완료** → G-A010 단일변수 → 통과 시 대표평가 / 실패 시 다음 단일변수 → 최종 제출.
- [지금 할 일] 없음. 서버는 종료 가능한 상태이며 다음 package가 로컬 검증되기 전에는 새 서버를 켜지 않는다.
- [보장하지 않음] 단일 학습 seed·tier-1 7-case·내부 proxy·영상 1개는 공식 점수나 예선 통과를 보장하지 않는다.

## 1. 분석 질문과 결론

**질문:** G-A009가 같은 repaired-v2 tier-1 evaluator에서 Default-01보다 얼마나 좋아졌고, 그 개선이 목표였던 G1에서 발생했는가?

**결론:** 총 내부 proxy는 `17.53712→20.62741/70`, 즉 `+3.09028/70`(`+17.62%`) 증가했다. 그러나 증가분의 `77.99%`가 G6 밀침 회복에서 나왔고, 목표 G1은 `0.00362921→0.00356288`로 `-0.00006633` 감소했다. 따라서 이 결과는 **전체 합계 일부 개선 / 목표 인과 미확인**이며 사전등록에 따라 `INTERNAL_EARLY_KILL_FAIL`이다.

`track_lin_vel_xy_exp=1.20`은 장기학습·대표평가·69-case로 승급하지 않는다. Pilot-01의 큰 G1 개선은 이 값 하나의 효과가 아니며, 아직 분리하지 않은 `lin_vel_z_l2`, `ang_vel_xy_l2` 또는 항목 간 상호작용에서 발생했을 가능성이 남는다.

## 2. 예상 결과와 실제 결과

| 항목 | 사전 예상·게이트 | 실제 | 판정 |
|---|---:|---:|---|
| artifact | FULL ZIP, 학습물·policy·lineage·telemetry·영상 완결 | outer/internal SHA, manifest 125/125, candidate/baseline 7/7, 영상 1, actor tensor 8/8 | `ARTIFACT_VERIFIED` |
| tier-1 총 proxy | baseline보다 낮으면 즉시 실패 | `17.53712→20.62741/70`, `+3.09028` | 총합은 증가 |
| 목표 G1 | proxy `+0.05` 이상 | `-0.00006633` | 목표 미달 |
| 생존 비열등 | 어느 G도 baseline보다 `-0.10` 초과 하락 금지 | 하락 없음; G3 `+0.09375`, G6 `+0.34375` | 이 조건은 충족 |
| 대표평가 | 조기 게이트를 모두 통과할 때만 seed 202·303 추가 | G1 게이트 실패로 미실행 | 비용 절감 분기 정상 작동 |
| 69-case | 대표평가 승급 뒤 별도 실행 | 미실행 | 사전계획 준수 |
| G1 영상 | 4 env, seed 101, 500 step 1개 | 499 frames, 50 fps, 9.98 s, 1920×1080 | `VIDEO_OBSERVED` |
| 공식 결과 | 별도 회수 전 미측정 | 없음 | `OFFICIAL_RESULT_UNMEASURED` |

## 3. Default 대비 시나리오별 변화

동일한 repaired-v2 tier-1의 seed 101끼리 비교했다. `Δ /70`은 `scenario proxy delta × scenario weight × 70`이다.

| G | Default proxy | G-A009 proxy | Δ proxy | Δ /70 | 내부 판정 | 해석 |
|---|---:|---:|---:|---:|---|---|
| G1 전진 | 0.003629 | 0.003563 | -0.000066 | -0.000696 | `INTERNAL_SCENARIO_FAIL` | 직접 목표가 개선되지 않음 |
| G2 전방위 | 0.265276 | 0.267219 | +0.001943 | +0.020403 | `INTERNAL_SCENARIO_FAIL` | 사실상 정체 |
| G3 rough | 0.278188 | 0.322180 | +0.043992 | +0.615886 | `INTERNAL_SCENARIO_FAIL` | survival `.7500→.84375`; 아직 `.95` 미달 |
| G4 경사 | 0.383481 | 0.381867 | -0.001614 | -0.016947 | `INTERNAL_SCENARIO_FAIL` | 미세 회귀 |
| G5 계단 | 0.033567 | 0.031940 | -0.001627 | -0.017084 | `INTERNAL_SCENARIO_FAIL` | 진행 proxy 회귀 |
| G6 밀침 | 0.619103 | 0.963398 | +0.344296 | +2.410071 | `INTERNAL_SCENARIO_PASS` | 총 증가분의 77.99%; survival `.65625→1.0` |
| G7 DR | 0.300895 | 0.312131 | +0.011236 | +0.078651 | `INTERNAL_SCENARIO_FAIL` | survival `.8125` 정체, tracking 소폭 증가 |

현재 후보의 내부 감점 `weight × (1-proxy) × 70`은 G1 `10.46`, G5 `10.16`, G3 `9.49`, G2 `7.69`, G4 `6.49`, G7 `4.82`, G6 `0.26`점 순이다. 다음 실험은 G1을 살리면서 G3·G5를 악화시키지 않는지를 우선 본다.

## 4. 학습 로그와 evaluator가 말하는 것이 다른 이유

### 직접 증거

- 학습은 정상 종료했고 best checkpoint는 iter 900, `Train/mean_reward=16.2977`이다.
- 마지막 iter 999 진단은 mean reward `15.51`, episode length `993.30`, training-terrain base-contact 종료율 `0.0652`, velocity error `1.3099`다.
- 같은 정책의 G1 evaluator는 평균 XY 속도 `0.02748 m/s`, tracking RMSE `1.18714`, proxy `0.003563`이다.

### 해석

학습의 평균 reward와 training-terrain 종료율은 여러 무작위 명령·지형이 섞인 학습 진단이며, 고정 G1 `forward_fast`의 survival·tracking 점수가 아니다. reward 계수 자체가 `1.0→1.2`로 바뀌었으므로 평균 reward 증가를 Default 정책의 행동 개선으로 직접 비교할 수도 없다. 공통 evaluator의 paired 결과가 우선이며, 이 기준에서 G1은 개선되지 않았다.

## 5. 영상 판정

- 원본 격리 경로: `workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/extracted/go2_track_lin_vel_120_v1/evaluation/candidate/videos/G1_forward_fast_seed_101.mp4`
- 찾기 쉬운 복사본: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/videos/G1_forward_fast_seed_101.mp4`
- contact sheet: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/contact_sheets/G1_forward_fast_seed_101_contact_sheet.jpg`
- 영상 SHA-256: `9d81170136efebbcfb1e708a36b438900365a1da47a32d1cc25a83ba303c6cdb`; 원본과 복사본 일치.
- `VIDEO_OBSERVED`: 10초 동안 네 환경의 전진 명령 화살표는 유지되지만 로봇은 시작 격자 부근에 머물고 유의미한 전진이 보이지 않는다. 이는 telemetry의 낮은 속도·진행과 일치한다.
- 이 영상은 G1 seed 101만 보여 준다. G2~G7 행동과 공식 evaluator 결과는 이 영상으로 판정하지 않는다.

## 6. 다음 단일변수 결정

### G-A010 1순위

Default-01 from-scratch에서 **`lin_vel_z_l2 -3.0→-2.0`만 변경**한다.

근거는 다음 순서다.

1. Pilot의 네 동시변경 중 `feet_air_time=0.20`과 `track_lin_vel_xy_exp=1.20`은 단독 screening에서 목표 G1을 살리지 못했다.
2. 남은 미분리 항은 `lin_vel_z_l2`와 `ang_vel_xy_l2`다.
3. 로컬 강좌 근거에는 Go2 1,000-iter 예시에서 `lin_vel_z_l2 -3→-2` 후 전진을 관찰한 기록이 있어 G1 활성화에 대한 정보가치가 더 높다. 이는 최적값 근거가 아니라 다음 진단점의 근거다.
4. `lin_vel_z_l2`는 수직 움직임 억제를 완화하므로 G1 보행 활성화와 G3/G5 지형 적응을 동시에 구분할 수 있지만, 통통 튐·착지 불안정 위험도 함께 측정해야 한다.

고정값은 `track_lin_vel_xy_exp=1.0`, `feet_air_time=0.01`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`, 학습 seed 42, 4096 env, 1,000 iter다. G1 `+0.05`, 전 G survival 회귀 `≤0.10`, 동일 tier-1 7-case·G1 영상으로 조기 판정한다.

### 실패 시 분기

G-A010이 같은 G1 기준을 충족하지 못하면 **`ang_vel_xy_l2 -0.08→-0.05` 단독**을 G-A011로 검사한다. 두 단독 실험이 모두 실패하면 그때 처음으로 `lin_vel_z × ang_vel_xy` 상호작용 실험을 검토한다. 단독 근거 없이 Pilot 조합을 그대로 재학습하지 않는다.

## 7. 증거·추론·미확정 경계

| 구분 | 내용 |
|---|---|
| 증거 | artifact·lineage 완결, paired tier-1 수치, 학습 로그, G1 영상 직접 관찰 |
| 추론 | 총 proxy 증가의 주원인은 G6이며 `track=1.20`이 Pilot G1 개선의 원인이라는 가설은 지지되지 않음 |
| 미확정 | 독립 학습 seed 재현성, 21/69-case 성능, `lin_vel_z`·`ang_vel_xy` 단독 효과, reward 상호작용, 공식 점수 |

기계판독용 비교 자료는 `reports/evidence/go2_track_lin_vel_120_260902/ANALYSIS_SUMMARY.json`, 시나리오별 표는 같은 폴더의 `G_A009_COMPARISON.csv`, 무결성 목록은 `SHA256SUMS.txt`에 보존했다.

## 8. 판정 요약

| 계층 | 판정 |
|---|---|
| artifact | `ARTIFACT_VERIFIED` |
| video | G1 `VIDEO_OBSERVED`; G2~G7 `VIDEO_UNKNOWN` |
| internal | G-A009 `INTERNAL_EARLY_KILL_FAIL`; G6만 `INTERNAL_SCENARIO_PASS` |
| official | `OFFICIAL_RESULT_UNMEASURED` |
