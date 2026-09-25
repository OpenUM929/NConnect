# Go2 튜닝 정책 판독문 — 2026-09-18 (분석가)

역할: **분석가**(`.claude/agents/go2-analyst.md`). 이 문서는 **판독**이다 — 값을 고르거나 다음 회차를 권하지 않는다(기획자 몫).
순서: 분석가(판독) → 기획자(값) → 감사자(결함). 기획 사양은 이 문서를 `inference.readout` 에 지목하고,
`tools/test_go2_detectability_gate.py::test_16_a_recommendation_stands_on_an_analyst_readout` 이 기준선 회차 이름이 여기 있는지 검사한다.

읽은 순서: `reports/GO2_REFERENCE_COMPASS.md` → `GO2_NOW.md` → `reports/runs/`(LEDGER·SCENARIO_SCORES·ARM_DELTAS·BASELINE_MARGIN·TERRAIN_AT_PIN) → `reports/GO2_TUNING_BASE_DATA.md` §4·§5 → `reports/GO2_G_A038_READOUT.md` → 배포 코드(`go2_task/`, `quadruped_rewards.py`) → `reports/GO2_OPEN_DECISIONS.md` → `GO2_REWARD_EVIDENCE_MASTER.md` §1-a. 회귀 사례 `reports/GO2_ROLE_REGRESSION_CASES.md` 를 먼저 읽었다.

> **주 세션 검증 (2026-09-18)** — §2의 "미탐색" 4칸, `_REP_BASELINE["quadruped"]` 5항, `dof_acc_l2` 가 `_finalize.py` 전체에 없다는 것, 목록 안 주석 3항이 `_REP_INTENT` 에 등재돼 있다는 것은 주 세션이 원본을 다시 열어 확인했다 [확인].

---

## 1. 현재 기준선과 축별 성적 — 어느 축이 비어 있는가

| 주장 | 값 | 출처 파일:칸 | 성격 |
|---|---|---|---|
| 기준선은 G-A033 | `go2_g_a033_a017_track_lin_vel_xy_150,candidate,posture_gate_v2` | `reports/runs/SCENARIO_SCORES.csv:run,arm,instrument` | 측정 |
| 총점 | 42.52861/70 | 같은 파일:`total_70` | 측정 |
| G1 | 9.22452 (감점 1.27548, 만점 10.5) | 같은 행:`G1`,`G1_deduction` | 측정 |
| G2 | 9.21294 (감점 1.28706, 만점 10.5) | 같은 행:`G2`,`G2_deduction` | 측정 |
| G3 | **4.22726 (감점 9.77274, 만점 14)** | 같은 행:`G3`,`G3_deduction` | 측정 |
| G4 | 9.01774 (감점 1.48226, 만점 10.5) | 같은 행:`G4`,`G4_deduction` | 측정 |
| G5 | **0.04473 (감점 10.45527, 만점 10.5)** | 같은 행:`G5`,`G5_deduction` | 측정 |
| G6 | 5.69295 (감점 1.30705, 만점 7) | 같은 행:`G6`,`G6_deduction` | 측정 |
| G7 | 5.10847 (감점 1.89153, 만점 7) | 같은 행:`G7`,`G7_deduction` | 측정 |

- 감점이 큰 두 축은 **G5 10.45527 · G3 9.77274** 이고, 나머지 다섯 축은 1.27548 ~ 1.89153 로 고르게 낮다 [확인]. 위 표의 `*_deduction` 칸 그대로다 — 합·비율은 손으로 계산한 값이라 적지 않는다.
- **실제로 비어 있는 축은 G5 하나이고(0.04473 / 만점 10.5), G3가 그 다음이다(4.22726 / 만점 14)** [확인].
- 만점 배분은 `SCENARIO_SCORES.csv` 의 `go2_chain01_baseline` 행(전 축 0점)의 `*_deduction` 이 그대로 만점이다: 10.5/10.5/14/10.5/10.5/7/7 = 70 [확인].
- **[2026-09-19 정정 — 이 줄의 아래 설명은 틀렸다]** G5 를 묶는 것은 오른 단수가 아니다. 채점식(`go2_fixed_eval_report.py:29-60`)에 `body_rise_*` 는 들어가지 않는다. 최솟값 case `stairs_15_down`@202 의 proxy 는 `생존 0.03125 x completion 0.13632` 이고, `completion` 은 **전진거리 `1.363` m / 기대 `10` m** 다. 12개 G5 case 전부 `completion < tracking_xy` 다. 생존을 전부 `1.00000` 으로 놓아도 축은 `1.43139` 에 그친다 — 즉 감점 10.455 중 자세 게이트가 설명할 수 있는 최대치가 그 `1.43139` 이고 나머지는 전진거리다(`reports/GO2_AXIS_BOTTLENECK.md`, 생성 `tools/go2_axis_bottleneck.py`, 관문 `tools/test_go2_axis_bottleneck_contract.py` 가 7축을 원장과 대조한다). 아래 원문은 지우지 않고 남긴다 — 오른 단수를 G5 의 이유로 읽은 것이 2026-09-18~19 판독·기획·감사 셋 모두의 공통 실패였다.
- ~~G5가 0점인 이유는 15cm 계단을 못 올라서다~~ — `stairs_15_down`(이름과 반대로 실제 오르기)에서 G-A033은 96대 중 4대만 한 단 이상 올랐고, **두 단 이상은 전 회차 전부 0이다**(`reports/evidence/go2_stairs_behavior_20260916/STAIRS_CLIMB.csv:body_rise_ge1,body_rise_ge2`) [확인].

## 2. 배포 `REWARD_WEIGHTS` 6항 — 남은 레버가 있는가

배포 6항은 `quadruped_rewards.py:41-94` 의 `REWARD_WEIGHTS` 에 ①~⑥으로 적혀 있다 [확인]. 배포 첫 시작값의 정본은 `go2_task/_finalize.py:228-229` 의 `_REP_BASELINE["quadruped"]` 다 [확인]. 저장소의 `quadruped_rewards.py:51,56,67` 은 이미 Pilot-01 값(1.2/0.2/-2)으로 고쳐져 있어 시작값이 아니다 [확인].

| 항 | 배포 시작값 | G-A033 | 걷는 기준선 유효 시도 | 결과·기각 사유 | 남은 방향 |
|---|---|---|---|---|---|
| `track_lin_vel_xy_exp` | 1.0 | **1.5** | 1.2→1.4(A017) · 1.4→1.5(G-A033) | 둘 다 채택 | 1.5 초과 미시도(추천 상한 2.0). 위험: 옆걸음 종료 31→48→58 |
| `feet_air_time` | 0.01 | 0.2 | 0.35(A015 -30.12) · 0.01(A031) · 0.1(A032) | 상향·하향 **둘 다 기각** | 양방향 유효 기각 — 실질 소진 |
| `lin_vel_z_l2` | -3.0 | -2.0 | **0건** | §1-a 현재 상태 **"미탐색"** | **남아 있음** |
| `ang_vel_xy_l2` | -0.08 | -0.05 | -0.15(A016 -45.12) · -0.08(G-A038 판정없음) | 강화 두 값 실패 | **완화 방향 "미탐색"** |
| `action_rate_l2` | -0.01 | -0.01 | -0.008(A018 -44.40) | 완화 기각 | **강화 방향 "미탐색"** |
| `flat_orientation_l2` | (미등재·프레임워크 0.0) | 0.0 | **0건**(A013·A025는 정지 정책) | §1-a **"미탐색"**, G-D104 판정 보류 | **남아 있음** |

출처: `GO2_REWARD_EVIDENCE_MASTER.md` §1-a 요약 표·전체 시도 표, `reports/GO2_TUNING_BASE_DATA.md` §4, `GO2_NOW.md` §4 유효 기각 이력. 성격: 전부 **측정** [확인].

**판정: "6개 목록 안에는 남은 레버가 없다"는 원자료로 성립하지 않는다 — FAIL** [확인].

- 반증 원본은 우리 정본 원장 자신이다: `GO2_REWARD_EVIDENCE_MASTER.md` §1-a 가 `lin_vel_z_l2` **"미탐색"**, `flat_orientation_l2` **"미탐색"**, `ang_vel_xy_l2` **"완화는 미탐색"**, `action_rate_l2` **"강화는 미탐색"** 이라고 글자로 적고, 같은 절의 **미측정 행**이 그 넷을 한 줄로 다시 열거한다 [확인].
- 그 거짓 주장은 `GO2_NOW.md` §0 [튜닝 패키지 G-A039] 절에 있었고, 근거로 든 6개 사유 중 **유효 기각은 2개뿐**이다(feet_air 3값, action_rate -0.008). 나머지는 "올리면 옆걸음↑"(위험 서술), "G-A037 보류"(한 값의 보류), "G-A038 붕괴"(한 방향), "D-1 반대"(문헌 논거) — 어느 것도 항 전체를 닫는 측정이 아니다 [확인].
- **양방향 유효 기각으로 닫힌 항은 `feet_air_time` 하나다** [확인].
- 다만 `lin_vel_z_l2`·`flat_orientation_l2` 는 "쓸 수 있다"가 아니라 **"모른다"**이다 — 걷는 기준선 유효 비교가 0건이라 기울기를 잴 수 없고, `GO2_TUNING_BASE_DATA.md` §4가 "걷는 회차에서 값이 하나뿐인 가중치는 기울기를 잴 수 없다. 그 가중치를 움직이는 값은 전부 `OUT_OF_RANGE`다"라고 적는다 [확인].

## 3. 이득구간 — 넘은 회차가 있는가

| 주장 | 값 | 출처 파일:칸 | 성격 |
|---|---|---|---|
| 총점 표집 sd | 1.26443/70 | `reports/runs/BASELINE_MARGIN.csv:delta_total_resample_sd` | 이득구간 |
| 2σ 검출 한계 | **2.52886** | 같은 파일:`detect_limit_2sigma` | 이득구간 |
| 95% 재표집 구간 | [+0.04666, +5.04652] | 같은 파일:`delta_total_ci95_lo/hi` | 이득구간 |
| 계단 10cm ≥1단 하한 | **83.329**(baseline_sum 90, max_drop 6.671) | `reports/evidence/go2_fact_rules_20260917/CLIMB_GUARD.csv:floor` | 이득구간 |
| 계단 10cm ≥2단 하한 | 29.261(baseline 43) | 같은 파일:`floor` | 이득구간 |
| 계단 15cm ≥1단 하한 | **-1.523**(baseline_sum 4) | 같은 파일:`floor` | 이득구간 |

**이 sd 는 검출 한계가 아니라 그 하한이다** [확인]. `tools/go2_eval_resolution.py` 모듈 docstring: "추종 proxy는 case-seed당 집계값만 남아 있어 재표집할 수 없다. 고정으로 둔다. 따라서 아래 값은 계측 흔들림의 **하한**이다." 2.529를 넘는 것은 이득의 필요조건이지 충분조건이 아니다 [확인].

### 수치로: 몇 회차가 구간 안이었나

- **70점 축 비교가 가능한 회차는 2건뿐이다** [확인]. 원장 18회 학습 중 나머지는 7case tier1(`ARM_DELTAS.csv` 의 `cases=7` 행 전부 `delta_70 = +0.00000`) 또는 10case 부분 평가라 판정 대상이 아니다 [확인].
  1. Pilot-01 → A017 **+6.09363** (`reports/runs/ARM_DELTAS.csv`, 양팔 posture_gate_v2, 69case) — 한계 밖. **단 이 쌍의 sd 는 산출된 적이 없다** [모름].
  2. A017 → G-A033 **+2.76366** — 한계 2.52886 보다 크다(초과 폭은 손으로 뺀 값이라 적지 않는다) [확인].
- **총점이 구간 안이었던 회차: 0건 / 2건** [확인]. 위 하한 서술 때문에 "2건 다 이득"이라고 읽어서는 안 된다 [확인].

**축별(sd 가 있는 유일한 쌍 A017→G-A033)**: 한계 밖 2축, 안 4축, 판정 불가 1축 [확인].

판정 규칙: **구간 밖 = |delta| > 2 × sd**. 2σ 를 곱해서 적지 않고 원장 칸(`BASELINE_MARGIN.csv:delta_resample_sd`)을 그대로 싣는다 — 곱셈은 읽는 쪽이 한다.

| 축 | delta | sd (`delta_resample_sd`) | 판정 |
|---|---:|---:|---|
| G1 | -0.16621 | 0.00000 | **판정 불가** |
| G2 | -0.15445 | 0.28229 | 구간 안 |
| G3 | -0.74289 | 1.01823 | 구간 안 |
| G4 | +3.65467 | 0.49816 | 구간 밖(이득) |
| G5 | **+0.04473** | **0.02802** | **구간 안** |
| G6 | -0.40740 | 0.43098 | 구간 안 |
| G7 | +0.53521 | 0.20179 | 구간 밖(이득) |

- **G1 의 sd 0.00000 은 "잡음 없음"이 아니다** [확인]. 전 case 생존 32/32 포화라 이항 재표집이 0이 되고(`reports/evidence/go2_seed_sensitivity_20260917/EVAL_SEED_SPREAD.csv` G1 세 case `spread=0`), -0.16621 은 추종 차이인데 이 모델에 추종 항이 없다 [모름].
- **목표 축 두 개가 모두 구간 안이다** [확인]. G3 -0.743 은 sd 1.018 안, **G5 +0.04473 은 sd 0.02802 의 2배 안**이다. 원장 전체에서 G5 가 0이 아닌 회차는 G-A033 하나이고(`SCENARIO_SCORES.csv`: pilot 0, pilot_v2 0, chain01 0, a017 0), **그 유일한 비영 값이 잡음 폭 안이다** [확인].
- **계단 하한을 위로 넘은 회차는 0건이다** [확인]. 하한은 비열등 바닥이지 이득선이 아니다 [확인]. 15cm ≥1단(3 seed 합, 96대 중): pilot/pilot_v2 **12** · G-A033 **4** · a017 0 · default 0 · chain01 0 · feet_air_020_v1 0 [확인]. 15cm ≥2단은 **전 회차 전부 0** [확인]. `stairs_15_climb_ge1` 하한이 -1.523(음수)이라 발화하지 않는 무효 관문이다 [확인].
- 10cm ≥1단: G-A033 **90** · pilot 65 · a017 28 · G-A038 **5** [확인]. G-A038은 하한 83.329 대비 5로 무너졌다 [확인].

## 4. 열린 결정 — 찬성 행과 반대 행

### U1-R6-ENV-REWARD-20260918 (`OPEN` · `WIDENS`)

**찬성 행**
- `go2_task/env_cfg.py:38-46` — `for name, weight in reward_weights.items(): attr = getattr(self.rewards, name, None) … attr.weight = float(weight)`. **임의 키**를 env RewTerm 이름으로 찾아 적용한다 [확인].
- `quadruped_rewards.py:38` — "줄 추가/삭제/주석(#) 자유" [확인].
- 같은 파일 `:35-37` — "여기 적은 항목만 IsaacLab 기본값에서 변경됩니다 … 없는 이름/오타는 무시됩니다(경고만 출력)" [확인].
- 서버 로그 `[OK] dof_acc_l2.weight = -1.25e-07` — `GO2_NOW.md` 가 인용한다. **판독에서 로그 원본은 열지 않았다** [모름].

**반대 행 (보존 사례 M05 가 요구한 줄 — 직접 열어 인용한다)**

`go2_task/_finalize.py:580-591`:
```
    base = _REP_BASELINE.get(robot, {})
    changed = [(t, base[t], rewards[t]) for t in base if t in rewards and abs(rewards[t] - base[t]) > 1e-9]
    # 프레임워크 기본값은 '참가자가 손댄 항목' 이 아니므로 제외 (표·판정 모두)
    extras = [(t, rewards[t]) for t in rewards
              if t not in base and t in _REP_INTENT and abs(rewards[t]) > 1e-9
              and not _rep_is_framework_default(robot, t, rewards[t])]
    # ⚠️ extras(REWARD_WEIGHTS 에 없는 항목)는 **판정에서 제외**한다. …
    bias, phrases, warns = _rep_classify(changed, [])
```
- `extras` 는 계산만 되고 `_rep_classify` 에 **빈 리스트 `[]`** 가 넘어간다 — 판정·표 양쪽에서 빠진다 [확인].
- **`GO2_NOW.md` 의 서술보다 더 강한 반대 행이 있다**: `dof_acc_l2` 는 `_REP_INTENT`(`:267-279`)에 **없다**. 그래서 `t in _REP_INTENT` 조건에서 걸려 **extras 에조차 들어가지 않는다** [확인]. `_REP_ADV`(`:245-249`)·`_REP_FRAMEWORK`(`:254-258`)·`_REP_RANGES`(`:241-243`)에도 없다 — **배포 판정기에게 그 변경은 존재하지 않는다** [확인].
- `_REP_BASELINE["quadruped"]`(`:228-229`)는 **5항뿐**이다: `track_lin_vel_xy_exp 1.0, feet_air_time 0.01, lin_vel_z_l2 -3.0, action_rate_l2 -0.01, ang_vel_xy_l2 -0.08`. **`flat_orientation_l2` 는 base 에 없다** [확인]. 배포가 "참가자가 손댄 항목"으로 세는 기준은 6개가 아니라 5개다 [확인].
- **관문 통과를 규칙 준수의 증거로 쓰지 않는다** [확인]. `R6_CHANGE_CLASSES` 에 `env_reward_weight` 를 넣은 것은 우리다(회귀 사례 C07).

**추가 원자료 행 — 이 결정과 별개다** [확인]: 배포 `REWARD_WEIGHTS` 딕셔너리 **안**에 주석으로 3항이 더 있다 — `quadruped_rewards.py:89-93` 의 `track_ang_vel_z_exp` 0.75 · `undesired_contacts` -1.0 · `termination_penalty` -200.0, 머리말 "[고급 옵션] 익숙해지면 주석(#) 풀어서 — 효과 큼" [확인]. 이 셋은 `_REP_INTENT` 와 `_REP_ADV["quadruped"]` 에 **모두 등재돼 있어** 배포 판정기가 이름으로 안다 [확인]. 즉 U1(목록 **밖**)과 달리 이들은 목록 **안**이다 [확인]. 단 `quadruped_rewards.py:92` 스스로 "Go2 기본값엔 미정의일 수 있음 → skip 경고 가능"이라 적고, `TUNING_BASE_DATA.md` §5-1 마지막 줄은 "회전 추종 가중치를 올리는 후보는 이 표로 뒷받침되지 않는다"고 적는다 [확인].

### U2-SEED-REPLICATE-20260918 (`OPEN` · `NARROWS`)

**찬성 행(열어야 한다 쪽)**
- 전 학습 18회가 **seed 42 하나**다 — `reports/runs/LEDGER.csv` 전 행, 관문 `tools/test_go2_run_ledger_contract.py` test_13 [확인].
- 같은 seed 재학습은 **결정론적**이다 — `reports/evidence/go2_seed_sensitivity_20260917/SAME_SEED_REPEAT.csv` 2쌍 모두 `identical=True`. 재학습은 새 정보가 0이고 **다른 seed 만이 새 정보다** [확인].
- 한 항만 바꾼 4쌍의 커리큘럼 도달점 표류가 크다 — `ONE_CHANGE_DRIFT.csv:terrain_delta` +0.5361 / +0.3316 / +0.4584 / **-1.6739** [확인].
- **직전 회차가 바로 이 이유로 판정 불가였다** — G-A038은 평가 iter 900 시점 지형 레벨이 G-A033 4.4937 대 1.9499(차 -2.5438)였다(`reports/runs/TERRAIN_AT_PIN.csv`, `reports/evidence/go2_g_a038_readout_20260917/CURRICULUM_LAG.csv`) [확인].

**반대 행(닫아 두는 쪽)**
- R-6은 보상 가중치만이고 seed 는 가중치가 아니다 [확인]. 회귀 사례 C02가 "학습 seed 반복을 추천으로 올림"을 보존된 실패로 박아 두었고 `test_11` 이 막는다 [확인].
- `NARROWS` 라 의존 산출물이 `reports/GO2_SEED_SENSITIVITY.md` 하나뿐이다 — 기각돼도 되돌릴 것이 없고, 승인돼도 **새 레버 값을 주지 않는다** [확인].
- GPU 잔량은 실측된 적이 없다 [모름].

## 5. 반대 행 (결론에 불리한 행을 따로 모은다)

1. **15cm 계단에서 가장 잘 오른 정책은 현재 기준선이 아니다** [확인]. Pilot-01(총점 33.67132) 12대 > G-A033(42.52861) 4대 > A017(39.76495) 0대. **70점 총점 순위와 15cm 계단 순위가 같은 방향이 아니다** [확인]. "모든 점수가 높은 상태에서 계단"을 한 방향 최적화로 다룰 근거가 원자료에 없다 [확인].
2. **10cm 오르기도 단조가 아니다** — Pilot 19 → A017 2 → G-A033 43 (≥2단, `GO2_TUNING_BASE_DATA.md` §5 S3 "단조: `False`") [확인].
3. **S5가 기전 가설을 반박한다** — "오르기 수직 벌점 몫이 작을수록 15cm를 더 오른다"는 `False`(Pilot 52%/12대, A017 22%/0대, G-A033 34%/4대) [확인]. G-A037(`lin_vel_z -2→-1`)의 도출 원리가 여기서 반대로 나온다 [확인].
4. **track 을 올릴 때마다 G3 위험이 커졌다** — 험지 옆걸음 종료 31 → 48 → 58, 무게 AUC 0.530 → 0.525 → 0.784 (§5 S2) [확인].
5. **G-A033 승급 자체가 얇다** — +2.76366 의 95% 하한이 **+0.04666** 이고, 승급 근거는 G4 한 축이며, 2단계 FAIL 판정 기록이 남아 있다(§1-a "2단계 FAIL: G3 가중 손실 .743>.5") [확인].
6. **G-A038의 10cm 붕괴를 레버 효과로 읽을 수 없다**(회귀 사례 M01) — 두 팔의 iter 900 지형 레벨이 4.4937 대 1.9499이다 [확인].
7. **`feet_air_time` 0.2 는 기준선 값 중 가장 취약하다** — 출처 무효(A001 4항 동시)이고 Isaac Lab rough 0.01에서 20배 이탈이다. 그런데 이 항이 §2 표에서 유일하게 양방향 유효 기각으로 닫힌 항이다 [확인].
8. **다이얼 모델은 반박됐다** — `reports/runs/DIAL_MODEL.csv` 는 `REFUTED_BY_G_A038` 이고 근거로 쓰지 않았다 [확인].
9. **경계대 안에서는 margin 예측이 뒤집힌다** — `BAND_RUNS.csv` 4회차 중 Pilot-01은 걷는데 +0.0033, A018은 멈췄는데 +0.0155다 [확인].

## 6. 측정되지 않아 답할 수 없는 것

1. **학습 seed 흔들림** — 0건. 전 18회 seed 42 [모름].
2. **`lin_vel_z_l2`·`flat_orientation_l2` 의 걷는 기준선 효과** — 유효 시도 0건 [모름].
3. **`ang_vel_xy_l2` 완화·`action_rate_l2` 강화** — 시도 0건 [모름].
4. **추종 proxy 의 표집 오차** — 재표집 불가. 2σ 2.52886 은 하한이고 **참 검출 한계는 모른다** [모름].
5. **Pilot-01→A017 쌍의 sd** — `BASELINE_MARGIN.csv` 는 A017↔G-A033 한 쌍만 담는다 [모름].
6. **G1 축의 검출 한계** — sd 0.00000 은 생존 포화가 만든 값이다 [모름].
7. **G-A038의 69case 전체 단계 점수와 15cm 계단** — 10 case만 쟀다 [모름].
8. **커리큘럼 포화 여부** — 평균 지형 레벨로는 판정 불가, 18회 전부 1000 iter [모름].
9. **`dof_acc_l2` 를 바꾼 회차의 관측** — G-A039 미실행. 평가 기록에 관절 열이 없어 흔들림·밀침 방향은 `unknown` [모름].
10. **배포 report 가 `dof_acc_l2` 변경을 참가자 변경으로 세지 않는다는 사실의 대회 규정상 의미** — 규정 원문을 이 판독에서 열지 않았다 [모름].
11. **7case tier1 축 ↔ 69case 70점 축 환산 계수** — 측정된 적 없다 [모름].
12. **잔여 GPU** — 서버 실측 없음 [모름].
13. **15cm 계단을 두 단 이상 오른 관측** — 전 회차 0건. 그 지형에서 무엇이 성공인지의 측정 기준이 없다 [모름].

## 7. 관문 실행

`PYTHONIOENCODING=utf-8 python -B -m unittest tools.test_go2_detectability_gate` — 16 tests, 출력 마지막 줄: `OK`.
이 통과는 R-6 준수의 증거가 아니다 [확인] — `R6_CHANGE_CLASSES` 의 `env_reward_weight` 는 U1 해석으로 우리가 넣은 상수다.

---

## 결론

**INCONCLUSIVE** — 정책을 정할 근거는 원자료에 **부분적으로만** 있다.

근거 있음 [확인]: ① 비어 있는 축이 G5(감점 10.455) 하나이고 G3(9.773)가 그 다음이라는 사실. ② 배포 6항 중 미탐색 방향이 남은 항이 어디인지. ③ 70점 축 대칭 비교가 2건뿐이라는 사실.

근거 없음 [확인]: ① **목표 축 G5·G3 는 유일하게 sd 가 있는 비교에서 둘 다 이득구간 안**이라, 어떤 레버가 목표 축을 움직인다는 측정이 원장에 0건이다. ② `lin_vel_z_l2`·`flat_orientation_l2` 는 걷는 기준선 시도가 0건이라 기울기를 잴 수 없고 전 값이 `OUT_OF_RANGE` 다. ③ 15cm 계단은 총점과 순위가 반대로 움직여(Pilot 12 > G-A033 4 > A017 0) 단일 방향 정책을 세울 원자료가 없다.

**하위 판정 하나는 확정이다: "6개 목록 안에는 남은 레버가 없다"는 FAIL** [확인] — 반증 원본은 `GO2_REWARD_EVIDENCE_MASTER.md` §1-a 의 "미탐색" 네 칸이다. 이 문장이 U1 승인 필요의 전제로 `GO2_NOW.md`·`GO2_OPEN_DECISIONS.md` 양쪽에 들어가 있었으므로, 정정 전에는 U1 을 사용자에게 올릴 때 전제가 틀린 채로 간다 [확인]. → 2026-09-18 주 세션이 세 곳(`tools/go2_open_decisions.py`, 생성된 `GO2_OPEN_DECISIONS.md`, `GO2_NOW.md`)에서 정정했고, 관문 `tools/test_go2_canonical_consistency.py::test_1e_no_doc_may_claim_the_deployed_six_are_exhausted` 가 재발을 막는다.
