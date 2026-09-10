# Go2 연속 실패 원인 — 독립 재감사 (Phase I)

- 문서 ID: `GO2_OPUS_REAUDIT_INDEPENDENT_260907.md`
- 작성: 독립 수석 감사관 (신규 컨텍스트, 원자료 재구성)
- 대상 저장소: `C:\dev\Nconnect`
- 근거 규칙: `OPUS_GO2_REAUDIT_PROMPT_260907.md` §1~§5.6
- 증거 용어: `ARTIFACT_VERIFIED` / `VIDEO_OBSERVED` / `VIDEO_UNKNOWN` /
  `INTERNAL_GATE_PASS` / `INTERNAL_GATE_FAIL` / `INTERNAL_GATE_INCONCLUSIVE` / `OFFICIAL_RESULT`
  만 사용한다. bare "PASS/합격/제출 가능/공식 점수"는 사용하지 않는다.

---

## 0. 독립성 봉인 선언

**본 Phase I 작성 시점까지 다음 두 문서의 내용을 열지 않았다.**

- `C:\dev\Nconnect\GO2_DESIGN_REVIEW_260907.md` — **미열람**
- `C:\dev\Nconnect\GO2_INDEPENDENT_AUDIT_CODEX_260907.md` — **미열람**

두 파일명은 `ls`/`git status` 출력에서만 보았고, `cat`·`sed`·`head`·`grep` 중 어떤 방법으로도
본문을 읽지 않았다. 저장소 전역 `grep`을 실행할 때도 두 파일이 결과에 포함될 수 있는
패턴은 사용하지 않고 **파일을 명시적으로 지정**해 검색했다. 두 문서를 인용한 2차 문서·SHA
파일·요약본도 열지 않았다.

본 문서의 모든 사실 주장은 아래 §0-a의 열람 순서에 나열된 원자료에서 직접 재구성했다.
`GO2_PROJECT_STATE.md`·`GO2_CAMPAIGN_SCHEDULE.md`는 캠페인 원장으로서 읽었으나,
**원장 문장을 근거로 채택한 결론은 없다.** 원장이 기록한 수치는 전부 `_keep`의 JSON·CSV·
로그로 재계산해 대조했고, 대조 결과가 다르거나 원장이 놓친 항목은 §2·§4에 별도로 표시했다.

### 0-a. 파일 열람 순서 (Phase I 전 구간)

| # | 파일 | 목적 |
|---:|---|---|
| 1 | `OPUS_GO2_REAUDIT_PROMPT_260907.md` | 감사 지시 |
| 2 | `workspace/PRELIM_RL_GUID.md` (= `workspace/training/PRELIM_RL_GUIDE.md`, byte-identical) | 채점식·G1~G7 정본 |
| 3 | `test/**/*.html` (키워드 전수 검색 + 12·13강 본문 추출) | 강좌에 채점식이 있는지 전수 확인 |
| 4 | `AGENTS.md` L240–L383 | 규정집 정본 절, Go2 라우팅, R-1~R-7 |
| 5 | `workspace/training/quadruped/config/go2_self_eval_registry.json` | 내부 proxy 계약 |
| 6 | `workspace/training/quadruped/go2_eval_telemetry.py` | 생존·추종·회복 계측 구현 |
| 7 | `workspace/training/quadruped/go2_tuning_eval_report.py` | tier-1 게이트 구현 |
| 8 | `workspace/training/quadruped/go2_fixed_eval_report.py` | 시나리오 집계·점수식 구현 |
| 9 | `workspace/training/quadruped/go2_task/env_cfg.py` | 명령 범위·push·G7 DR |
| 10 | `workspace/training/quadruped/quadruped_rewards.py` | 참가자 수정 영역·권장 iter |
| 11 | `GO2_PROJECT_STATE.md` §0–§33 (구간 분할 열람) | 캠페인 원장 |
| 12 | `workspace/_keep/*/RUNNER_STATUS.txt`·`RESULT_STATUS.txt`·`reports/TIER1_DECISION.json` (전수, 스크립트) | 실행·판정 원자료 |
| 13 | `workspace/_keep/*/evaluation/*/cases/**/summary.json` (전수, 스크립트) | evaluator 지문·생존·추종 원자료 |
| 14 | `workspace/_keep/*/evaluation/*/SELF_EVAL_REPORT.json` | 시나리오 집계 결과 |
| 15 | `workspace/_keep/*/meta/tier1_registry.json` | tier-1 case/seed 계약 |
| 16 | `GO2_CAMPAIGN_SCHEDULE.md` (L1–L110, L218–L300, L340–L400, L440–L680) | 사전등록·철회 이력 |
| 17 | `H1_REWARD_EVIDENCE_MASTER.md` §3, §10–§12 | H1 비교 원자료 |
| 18 | `PROJECT_STATE.md` L100–L180, L550–L650, L890–L935 | H1 F40·F42·F43·D20–D32 |
| 19 | `workspace/training/humanoid/eval_telemetry.py` L195–L220, `fixed_eval_report.py`, `independent_eval_report.py` | H1 evaluator 구현 |
| 20 | `workspace/training/quadruped/go2_task/_finalize.py`, `go2_task/agent_cfg.py` | checkpoint 선택 규칙·PPO 설정 |
| 21 | `workspace/training/quadruped/server_run_go2_chain01_baseline.sh` (+ `pilot_v2`·`default_vs_pilot`·`tuning_engine`·`track_lin_vel_120` runner의 해당 절) | case 명령·지형·push·DR 실현값 |
| 22 | `GO2_REWARD_EVIDENCE_MASTER.md` §2, §16, §17 | 문헌 근거 사용 이력 |
| 23 | `tools/test_go2_tuning_engine_contract.py` (테스트 이름 목록) | 계약 테스트 범위 |
| 24 | `workspace/_keep/*/training/env.yaml`, `*/logs/**/*training*.log`, `launcher.snapshot.log` | 렌더된 reward·checkpoint 선택 로그 |
| 25 | `workspace/_keep/*/evaluation/*/cases/**/steps.csv` (SHA-256 대조) | G3/G7 독립성 |

**직접 재계산한 것** (열람이 아니라 실행):
`go2_fixed_eval_report.build_policy()`를 로컬에서 실행해 Default-01·Pilot-01(2세대)·Chain-01·
G-A007 후보의 69-case 점수를 **재현**했고, `_case_proxy`를 `survival_proxy_v1`로 치환한
대칭 재채점(v1-대-v1)을 13개 실행에 적용했다. 결과는 §2·§3에 있다.

---
## 1. 감사 인프라와 공식 채점 구조 진단 (§5.1)

### 1-1. 채점식의 출처 — 강좌에는 없다

| 항목 | 판정 | 근거 |
|---|---|---|
| 강좌(`test/`)에 `survival_rate` 문자열 | **0건** | `grep -rl "survival_rate" test/` 결과 없음 |
| 강좌에 `tracking_score` | **0건** | 같은 방식 |
| 강좌에 `시나리오 점수` | **0건** | 같은 방식 |
| 강좌에 `배점`·`70점` | **0건** | 같은 방식 |
| 강좌에 `채점` | 2개 파일 | `test/12강의…html`, `test/13강의…html` — 문맥은 `model_best.pt (실제 채점에 쓰이는 RSL-RL checkpoint)` 한 줄뿐이며 **점수식이 아니다** |
| 채점식 로컬 정본 | `workspace/PRELIM_RL_GUID.md:92-103` | `시나리오 점수 = survival_rate × tracking_score`, `종합 = Σ(시나리오 점수 × 가중치)`, `×70점` |
| 규정집 요약 정본 | `AGENTS.md:292-303` (R-2, 제8조) | 동일 식 + **"넘어지지 않고 완주한 비율"이지 "종료 이벤트 미발생 비율"이 아니다"** 명문 |
| 규정집 원본 PDF/문서 | **로컬 부재** | `find . -iname "*규정*"` 0건 → 규정집 원문은 `[미확인: 파일 부재]`, `AGENTS.md`의 요약만 존재 |

**판정:** "강좌에는 공식 채점식 근거가 없다" — `ARTIFACT_VERIFIED`(전수 검색). 채점 개념의
로컬 출처는 `PRELIM_RL_GUID.md`와 `AGENTS.md` R-1~R-3 요약이며, 규정집 정본 자체는 로컬에 없다.

### 1-2. 세 층위 분리

| 층위 | 정의 | 로컬 산출 여부 |
|---|---|---|
| `FORMULA_PROXY_RESULT` | 공식형 곱셈·가중합. 시나리오 점수 = 생존율×추종, 케이스 **평균**으로 집계 후 Σ(w×점수)×70 | 계산 가능 (§1-6) |
| `CAMPAIGN_GATE_RESULT` | 캠페인이 추가한 **worst-case 집계** + 안전·승급 gate | `_keep`의 모든 리포트가 이것 |
| `OFFICIAL_RESULT` | 운영진 evaluator·결과 | **전부 `[미측정]`.** 로컬에 공식 evaluator 코드·공식 점수 파일 0건. `go2_tuning_eval_report.py:57` 자체가 모든 판정문에 `"official_result": "OFFICIAL_RESULT_UNMEASURED"`를 박아 넣는다 |

### 1-3. 내부 proxy 구조와 registry 계약의 불일치

registry `workspace/training/quadruped/config/go2_self_eval_registry.json`:

- `:2` `schema_version: "1.0.0"`
- `:37` `scenario_proxy = survival_proxy * tracking_proxy` — 공식형과 구조 일치
- `:38` `tracking_proxy_v1 = exp(-pow(rmse / env_track_std, 2))`
- `:39` `env_track_std_path = "rewards.track_lin_vel_xy_exp.params.std"` — **env에서 읽으라는 계약**
- `:40` `aggregation = "sum(weight * scenario_proxy)"`
- `:49` `pair_aggregation: "worst_case"`

구현 `go2_fixed_eval_report.py`:

- `:12` `TRACKING_STD = 0.5` — **하드코딩.** `env_track_std_path`를 읽는 코드는 저장소 어디에도
  없다(`grep -rn "env_track_std_path" workspace/training/quadruped` → registry 1건뿐).
  수치 자체는 현재 env(`std=0.5`)와 일치하므로 지금까지의 점수는 틀리지 않았으나,
  **계약이 코드로 강제되지 않는다.** `ARTIFACT_VERIFIED` 결함(잠재).
- `:89-92` 시나리오 집계는 `min(...)` 3개를 **서로 독립적으로** 취한다:
  `survival = min(모든 case의 survival)`, `tracking = min(모든 case의 tracking)`,
  `proxy = min(모든 case의 survival×tracking)`.
  → 리포트가 표시하는 `survival_proxy`/`tracking_proxy`는 `scenario_proxy`를 만든 case와
  **다른 case에서 올 수 있다.** 세 값은 같은 rollout의 분해가 아니다. 해석 시 위험.
- `:114` `fraction = Σ(weight × scenario_proxy)`, `:142` `simulation_points_70 = 70×fraction`
- `:86-88` 어떤 시나리오의 유효 case 수가 기대치와 다르면 `continue` — 그 시나리오는
  **총점에서 통째로 빠진다.** 총점은 여전히 `/70`으로 보고되므로 **누락 = 감점**으로 보인다.
  (`_keep` 전 실행에서 `observed/expected`가 69/69 또는 7/7로 완전해 실제 발현은 0건 — `ARTIFACT_VERIFIED`.)

### 1-4. 생존 판정 — `termination_only_v1` 대 `posture_gate_v2`

`go2_eval_telemetry.py`:

- `:369` `survival_proxy_v1 = 1 - terminated_env_count / num_envs` (종료 이벤트만)
- `:238-241` 자세 게이트:
  `tilt_ok = isfinite(proj_grav_z) and proj_grav_z <= -0.5` (약 60°),
  `height_ok = (height_rel is None) or (height_rel >= 0.18)`,
  `measured = isfinite(proj_grav_z) or (height_rel is not None)`,
  `upright = tilt_ok and height_ok if measured else True`
- `:253-260` 유예 0.5 s 이후, **연속 0.5 s 이상 비직립**이면 그 env는 영구 `fallen`
- `:348-353` `survival_proxy_v2 = 1 - |fallen ∪ terminated| / num_envs`
- `:374-377` 최종 `survival_proxy`는 v2가 있으면 v2, 없으면 v1. `survival_proxy_source`에 기록

**논리식 결합 방식:** 중력 투영과 지면 대비 높이는 **AND**로 결합된다(`:241`). 그런데
`height_ok`는 `height_rel is None`일 때 **무조건 True**(`:239`)이고, `measured`는
`grav_z`만 유한해도 True(`:240`)다. 즉 **height_scanner가 없는 scene에서는
`survival_proxy_source`가 여전히 `posture_gate_v2`로 기록되지만 실제로는 기울기 전용 게이트**다.
동일 라벨 아래 두 가지 강도의 게이트가 공존할 수 있다 — 계약 결함. (`_keep`의 v2 case는
모두 `height_rel_*`가 채워져 있어 실제 발현은 확인되지 않음: `INTERNAL_GATE_INCONCLUSIVE`.)

`height_rel`은 `_finite_mean(ray_hits_w[...,2])`, 즉 **스캐너 격자 전체의 평균 지면 높이**를
쓴다(`:189-193`). 몸통 바로 아래 한 점이 아니다. 계단·험지에서 계통 편향이 생긴다.

**같은 rollout, 두 규칙의 크기 (직접 재계산):** Pilot-01 동일 checkpoint(`c4d78adf…`)를
G-A006(v1)과 G-A012(v2)에서 각각 69-case로 채점한 결과
`41.979898/70` → `33.793106/70` (**−8.19/70**). 두 실행의
`tracking_xy_rmse`·`speed_xy_mean`은 case 단위로 완전히 동일(예: `forward_fast` seed 101
`rmse=0.1680`, `spd=1.1736` 양쪽 일치)하므로 **차이는 전부 생존 규칙**이다. `ARTIFACT_VERIFIED`.

### 1-5. G6 밀침 회복 — reporter가 읽는 필드는 무의미하다

- `go2_eval_telemetry.py:286-291` 주석 원문: *"`recovery_rate` alone is not evidence of recovery:
  its quiet-window test (speed <= 0.15 m/s) is satisfied trivially by a robot that is lying on the
  ground and never moved. `recovery_rate_upright` … is the figure that may be quoted as recovery."*
- `go2_fixed_eval_report.py:39` reporter는 **`recovery_rate`를 읽는다.**
  `recovery_rate_upright`를 읽는 코드는 저장소에 **0건**
  (`grep -rn "recovery_rate_upright" workspace/training/quadruped` → 정의부 1곳뿐).
- **전수 실측:** `_keep` 전체의 push case `summary.json`에서 `recovery_rate == 1.0`이 **100%**다.
  G-A024 후보(`survival_proxy_v2=0.0`, `recovery_rate_upright=0.125`)조차 `recovery_rate=1.0`.
  `tracking = min(post_push_rmse_track, recovery_rate) = min(x, 1.0) = x` →
  **회복 인수는 항상 항등원이며 G6에 아무 정보도 넣지 않는다.** `ARTIFACT_VERIFIED`.
- 더 나아가 push case의 **명령 속도가 0**이다:
  `server_run_go2_chain01_baseline.sh:126` `VX=0 VY=0 WZ=0` 기본값이고 `push_*` 분기는
  `PUSH_X/PUSH_Y`만 설정한다(`:163-166`). 따라서 `post_push_tracking_xy_rmse`는
  **정지 상태로부터의 이탈**을 재고, 쓰러져 움직이지 않는 정책이 tracking ≈ 1.0을 얻는다.
  실측: G-A024 후보 G6 `tracking_proxy = 0.979`인데 `survival_proxy = 0.000`.
  → **G6은 사실상 생존 단독 지표**이며 "밀침 회복"을 측정하지 않는다.
- 밀침 시점은 `go2_eval_telemetry.py:299`에 `(4.0, 8.0, 12.0, 16.0)`으로 **하드코딩**돼 있고
  event config에서 읽지 않는다. 현재 `env_cfg.py:121` `interval_range_s=(4.0,4.0)`과 우연히
  일치하므로 지금은 맞지만, 결합이 없다.
- `env_cfg.py:99-101` 주석: *"평가의 밀침은 채점기가 별도로 구성하며 값도 여기와 다르다"*
  → 공식 push 파라미터는 `[미확인]`.

### 1-6. G3 / G7 독립성 — 69-case 스위트에서는 지금도 동일 데이터다

`dr_seed_*`(G7)와 `rough_forward`(G3)의 `steps.csv` SHA-256 직접 대조:

| 69-case 실행 | seed 101 | seed 202 | seed 303 |
|---|---|---|---|
| G-A006 Default-01 (260901) | **동일** `b19282878a038866…` | **동일** `d484f1a91fa596f8…` | **동일** `646d52bf30f1afc5…` |
| G-A012 Pilot-01 (260903, posture_gate_v2) | **동일** `f9e768079eeb80a3…` | **동일** `df1f75892c01a8a0…` | **동일** `f262778aa15528fd…` |
| G-A023 Chain-01 (260905, posture_gate_v2) | **동일** `bac47e60da5e9b0e…` | **동일** `cfa5a2b3588fd567…` | **동일** `77f77460fa5ff20e…` |

원인: `server_run_go2_chain01_baseline.sh:140-146`이 `rough_forward|rough_lateral|dr_seed_*`를
**하나의 분기**로 묶어 동일 지형·동일 명령(VX=0.50, `random_rough noise 0.02~0.10`)을 주고,
이 스크립트에는 `NCRC_EVAL_DR` 문자열이 **아예 없다**. `pilot_v2`·`default_vs_pilot` runner도 동일.

> **원장 대비 정정.** `GO2_PROJECT_STATE.md` G-F45(260902)는 "G7 v2는 `NCRC_EVAL_DR=1`에서
> G3와 다른 실행 fingerprint를 가진다"고 기록했고 G-D60은 "다음 evaluator에서 수정한다"고
> 했다. 실제로 수정된 것은 **tuning engine runner와 track_lin_vel_120 runner뿐**이다
> (`grep -n NCRC_EVAL_DR workspace/training/quadruped/server_run_go2_*.sh` → 2개 파일만 hit,
> `server_run_go2_tuning_engine_v1.sh:226,229`, `server_run_go2_track_lin_vel_120_v1.sh:200,203`).
> **69-case 기준선 3종은 수정 이후에도 전부 G7=G3로 실행됐다.** G-A023(260905)이 그 증거다.
> tier-1 7-case에서는 분리가 확인된다(G-A017 후보 `rough_forward` `12c652a2…` vs
> `dr_seed_101` `bc8d8f24…`, G-A024 `ad9c5a6f…` vs `1bd33a78…`).

**영향:** 69-case 총점에서 G3(0.20)+G7(0.10) = **가중 0.30이 하나의 rollout 집합에 의존**한다.
Default-01 `17.90699/70`, Pilot-01 `41.979898`/`33.793106`, Chain-01 `2.307745`,
G-A007 `21.772582` — 이 다섯 숫자 전부가 이 중복을 포함한다.

### 1-7. G5 완주도 · G2 yaw — 부분적 정합

- `go2_fixed_eval_report.py:31-34` 계단은 `expected = 0.5 × duration`으로 완주도를 정의하고
  `tracking = min(tracking, completion)`. runner의 stairs case 명령은 `VX=0.50`
  (`server_run_go2_chain01_baseline.sh:155`)이므로 **현재는 정합**하지만, 명령값이
  코드 상수로 복제돼 있어 결합이 없다.
- registry `:95`는 G2에 `yaw_rmse`를 필수 metric으로 요구하지만, `_case_proxy`는
  `combined_yaw*` case에서만 yaw를 쓴다(`:28-29`). `backward`/`left`/`right`/`diagonal_*`의
  yaw 오차는 점수에 들어가지 않는다. **registry와 구현 불일치**(경미).

### 1-8. evaluator fingerprint 검사 부재 — 구조적 결함

`go2_fixed_eval_report.build_policy()`는 case `summary.json`에서 `schema_version`,
`survival_proxy_source`, `posture_gate` 파라미터를 **한 번도 읽지 않는다**(`:66-79`).
`go2_tuning_eval_report.tier1_decision()`도 두 arm의 지문을 대조하지 않는다(`:14-58`).
`identity.json`에는 baseline arm의 `evaluator_sha256`이 없다(예:
`workspace/_keep/go2_g_a013_flat_orientation_m1/evaluation/baseline_tier1/identity.json`은
`policy`·`model_sha256` 2개 필드뿐; 반면 `go2_chain01_baseline/evaluation/chain01/identity.json`에는
`evaluator_sha256: f8ed1d01…`이 있다).

계약 테스트 `tools/test_go2_tuning_engine_contract.py`의 16개 테스트 이름을 전수 확인한 결과
**두 arm의 evaluator 세대 일치를 검사하는 항목은 0건**이다(전부 spec 자기일관성·게이트 산술·
ZIP 재현성). `ARTIFACT_VERIFIED`.

### 1-9. gate와 공식형 목적함수의 관계

`go2_tuning_eval_report.py:32-36`:

```
if points_delta < gates["min_total_points_delta"]:      -> FAIL
for each scenario: if survival_delta < -max_survival_regression: -> FAIL
```

- `min_total_points_delta`(현행 1.0)는 **공식형 목적함수(가중 총점)와 방향이 같다.**
  엔진 1.2.0에서 도입됐고, 그 이전(1.0.1/1.1.0)에는 `target_scenario` 단일 시나리오 절이
  게이트였다(`:28-31` 주석: *"on G-A010, G-A011 and G-A013 that clause disagreed with the
  weighted total on every run"*). 실측으로 확인: G-A010 `+2.25716`·G-A009/A011 `+3.09028`이
  `target_G1_improvement_below_0.05` 단 하나로 조기 종료됐다
  (`workspace/_keep/go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json#/failure_reasons`,
  `workspace/_keep/go2_track_lin_vel_120_v1/reports/TIER1_DECISION.json#/failure_reasons`).
- `max_survival_regression`(0.1)은 **공식형 목적함수와 방향이 다르다.** 공식형은
  생존×추종의 **곱**을 채점하는데, 이 게이트는 **인수 하나**를 단독으로 본다.
  → 곱이 개선돼도 인수 하나가 후퇴하면 거절된다. G-A017이 정확히 이 사례다(§2-4).
- registry `:42-50`의 `minimum_survival_proxy_each 0.95` / `minimum_tracking_proxy_each 0.70` /
  `minimum_weighted_simulation_proxy 0.70` 역시 **인수별 하한**이며 공식형에는 없는 조건이다.
  이 세 조건 때문에 지금까지 측정된 **모든** Go2 정책이 `INTERNAL_GATE_FAIL`이다.

### 1-10. FORMULA_PROXY_RESULT 대 CAMPAIGN_GATE_RESULT — 직접 계산

`build_policy()`가 만든 case별 `scenario_proxy`를 그대로 쓰되 집계만 바꿔 계산했다.

| 정책 | evaluator | `FORMULA_PROXY_RESULT` (case 평균, /70) | `CAMPAIGN_GATE_RESULT` (worst-case, /70) | 차이 |
|---|---|---:|---:|---:|
| Default-01 (G-A006) | termination_only_v1 | **24.6721** | 17.9070 | −6.77 |
| Pilot-01 (G-A006) | termination_only_v1 | **51.5913** | 41.9799 | −9.61 |
| Pilot-01 (G-A012) | posture_gate_v2 | **45.0310** | 33.7931 | −11.24 |
| Chain-01 (G-A023) | posture_gate_v2 | **11.5976** | 2.3077 | −9.29 |
| G-A007 `feet 0.20` | termination_only_v1 | **29.7187** | 21.7726 | −7.95 |

- worst-case 집계는 공식형 대비 **6.8~11.2점/70을 계통적으로 깎는다.** 규정 제8조의
  "비율"은 케이스 평균에 가깝지 worst-case가 아니다.
- 다만 위 5개 정책의 **순위는 두 집계에서 동일**하다. 따라서 "worst-case 때문에 잘못된
  정책을 골랐다"는 주장은 이 자료로는 **성립하지 않는다**(`INTERNAL_GATE_INCONCLUSIVE`).
  worst-case의 실제 해악은 순위 역전이 아니라 **delta의 분산 증폭**이다: 21개 case 중
  최악 1개가 시나리오 점수를 전부 결정하므로, tier-1의 7-case×1-seed 구성에서는
  **케이스 1개의 우연이 시나리오 점수 1개를 통째로 결정**한다.

### 1-11. `OFFICIAL_RESULT`

로컬에 공식 evaluator 코드·공식 채점 결과·제출 접수 증거가 **하나도 없다.**
`AGENTS.md` R-4에 따르면 제출물은 `policy.pt`·`env.yaml`·리포트 3종이며,
Go2의 **제출 자체가 `[미측정]`**이다. 따라서 본 문서의 모든 점수는
`FORMULA_PROXY_RESULT` 또는 `CAMPAIGN_GATE_RESULT`이며 `OFFICIAL_RESULT`는 **전부 `[미측정]`**이다.

---
## 2. G-A006 ~ G-A025 전수 감사 (§5.2)

### 2-1. 표기 규칙

- **절대 proxy /70**: 그 실행의 판정문이 쓴 집계(worst-case) 기준 후보 총점 = `CAMPAIGN_GATE_RESULT`.
- **delta /70**: `candidate_points_70 − baseline_points_70` (판정문 원본값).
- **공식형 결과**: 케이스 평균 집계(= `FORMULA_PROXY_RESULT`). tier-1(7 case×1 seed)은
  case가 시나리오당 1개라 평균=worst이므로 **동일**하다. 69-case 실행만 별도 값을 적었다.
- **evaluator/schema**: `cand`=후보 arm, `base`=기준선 arm의 `summary.json#/schema_version` 및
  `#/survival_proxy_source`. 전수 스캔 결과.
- **판정 유효성**: 두 arm의 evaluator 지문이 같으면 `대칭·유효`, 다르면 `비대칭·무효`.
- **실패 분류**: `실제정책실패` / `계측실패` / `운영실패` / `미실행` / `중복` / `인프라`.
  한 실행에 둘 이상 붙을 수 있다.
- `OFFICIAL_RESULT`는 모든 행에서 `[미측정]`이므로 열을 반복하지 않는다.

### 2-2. 전수 표

| Run | 실행 유형 | baseline 정책·iter·SHA | candidate 정책·iter·SHA | 학습 seed | 평가 seed | evaluator/schema | 단일변수 여부 | 절대 proxy /70 | delta /70 | 공식형 결과 | gate 결과 | 판정 유효성 | 실패 분류 | 근거 |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|
| **G-A006** | 학습(Default-01 신규) + 69-case×3seed 쌍대평가 | Default-01 · iter 800 · `99ceeaa1a3a1ebee…` (본 실행에서 생성) | Pilot-01 동결 · best iter 972 → `model_999` · `c4d78adf3fbd9031…` | 42 (양쪽) | 101/202/303 | cand v1(schema 1)·base v1(schema 1) | ✕ (Pilot은 4항 동시변경) | Default **17.9070** / Pilot **41.9799** | +24.0729 | Default 24.6721 / Pilot 51.5913 | 양쪽 `INTERNAL_GATE_FAIL` | 대칭·유효 (단 G7=G3 중복 포함) | 계측실패(G7 중복) | `_keep/go2_default_vs_pilot_v1/evaluation/{default,pilot}/SELF_EVAL_REPORT.json`; steps.csv SHA 대조 |
| **G-A007** | 학습(feet 0.20) + 후보 69-case×3seed. 1차 실행 `PARTIAL`(RUNNER_RC=5, telemetry 8/69) 후 v2 패키지로 완주 | Default-01 69-case 캐시 · iter 800 · `99ceeaa1…` | feet_air_time 0.01→0.20 · step 829 → `model_800` · `0dc8815f54498642…` | 42 | 101/202/303 | cand v1(schema 1)·base v1(schema 1) | ○ | **21.7726** | +3.8656 | 29.7187 (base 24.6721) | `INTERNAL_GATE_FAIL`; screening 탈락 사유 `g5_proxy_delta_at_least_plus_0_03` 1건 | 대칭·유효 | 운영실패(양의 총점을 단일 시나리오 절로 폐기) | `_keep/go2_feet_air_time_020_v1/evaluation/candidate/SELF_EVAL_REPORT.json`; `GO2_PROJECT_STATE.md` G-F93 |
| **G-A008** | 인프라 — telemetry hard-exit 제거·graceful stop v2 패키지(`73c6ba1f…`) 빌드·검증 | — | — | — | — | — | — | — | — | — | — | 해당 없음 | 인프라 | `GO2_PROJECT_STATE.md` G-F35~G-F37 |
| **G-A009** | 학습(track 1.2) + tier-1 7 case | Default-01 tier-1 캐시 · iter 800 · `99ceeaa1…` | track_lin_vel_xy_exp 1.0→1.2 · step 900 → `model_900` · `143871e3f69514a4…` | 42 | 101 | cand v1(schema 1)·base v1(schema 1) | ○ | **20.6274** | **+3.0903** | 동일(20.6274) | `INTERNAL_EARLY_KILL_FAIL` — 사유 `target_G1_improvement_below_0.05` **단 1건** | 대칭·유효 | 운영실패(양의 총점 거절) | `_keep/go2_track_lin_vel_120_v1/reports/TIER1_DECISION.json` (`schema_version:1`, `work_id` 필드 **없음**) |
| **G-A010** (원 실행 260902) | 학습(lin_vel_z −2.0) + tier-1 7 case, engine `1.0.1`/archive `e8f8b3cd…` | Default-01 tier-1 캐시 · iter 800 · `99ceeaa1…` | lin_vel_z_l2 −3.0→−2.0 · step 864 → `model_900` · `dc131ae512850b6b…` | 42 | 101 | cand v1(schema 1)·base v1(schema 1) | ○ | **19.7943** | **+2.2572** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 사유 `target_G1_improvement_below_0.05` **단 1건** | 대칭·유효 | 운영실패(양의 총점 거절) | `_keep/go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json#/failure_reasons` |
| **G-A010** (재측정 260906) | 동일 변수·동일 baseline 재실행, engine `1.3.0`/archive `81c3bcce…` | Default-01 tier-1 캐시(**v1 세대**) · `99ceeaa1…` | 동일 후보 SHA `dc131ae5…` · `model_900` | 42 | 101 | **cand v2(schema 2, posture_gate_v2)·base v1 6/7 + v2 1/7** | ○ | **9.4995** | **−7.6325** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 절 + G1~G6 생존 절 6건 | **비대칭·무효** | 계측실패 | 전수 지문 스캔; `_keep/go2_g_a010_lin_vel_z_m2_v2_260906/**/TIER1_DECISION.json` |
| **G-A011** | (a) 원안 `go2_terrain_5k_v1.zip` 5,000 iter — `WITHDRAWN_PRE_LAUNCH`, GPU 소비 0. (b) 260903 이후 **G-A009 결과에 재부여된 라벨** | (b) G-A009과 동일 | (b) G-A009과 동일 (`143871e3…`) | 42 | 101 | (b) v1/v1 | ○ | (b) 20.6274 | (b) +3.0903 | (b) 동일 | (b) G-A009과 동일 | (a) 미실행 / (b) **식별자 중복** | 미실행 + 중복 | `GO2_CAMPAIGN_SCHEDULE.md:284-288`; `GO2_PROJECT_STATE.md` G-F92·G-F131 |
| **G-A012** | 평가 전용(학습 없음). Pilot-01 동결 69-case×3seed, `EVALUATOR=posture_gate_v2` | — (단일 arm) | Pilot-01 · `c4d78adf…` | (학습 없음) | 101/202/303 | v2(schema 2) 69/69 | 해당 없음 | **33.7931** | — | **45.0310** | `INTERNAL_GATE_FAIL` (G3·G5 붕괴) | 유효(단일 arm) | 계측실패(G7 중복 잔존) | `_keep/go2_pilot_v2_baseline/`; 로컬 `build_policy()` 재현 |
| **G-A013** | 학습(flat_orientation −1.0) + tier-1, engine `1.1.0` | Default-01 tier-1 캐시(**v1**) · `99ceeaa1…` | flat_orientation_l2 0.0→−1.0 · step 884 → `model_900` · `676cc1cb93c70cd6…` | 42 | 101 | **cand v2(7/7)·base v1 6/7 + v2 1/7** | ○ | **15.7043** | **−1.4278** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G2·G4·G5·G6 생존 | **비대칭·무효** | 계측실패 | `_keep/go2_g_a013_flat_orientation_m1/**`; 지문 전수 스캔 |
| **G-A014** | flat_orientation −2.0. 사전등록 후 **취소** | — | — | — | — | — | — | — | — | — | — | 해당 없음 | 미실행 | `GO2_PROJECT_STATE.md` G-D67 |
| **G-A015** | 학습(feet 0.35) + tier-1, engine `1.2.0` | **Pilot-01** tier-1 캐시(**v2**) · `c4d78adf…` | feet_air_time 0.20→0.35 · step 935 → `model_900` · `994562a171251696…` | 42 | 101 | **cand v2·base v2 (7/7 동일 세대)** | ○ | **16.3693** | **−30.1219** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G1·G3·G4·G5·G7 생존 | **대칭·유효** | **실제정책실패** | `_keep/go2_g_a015_.../reports/TIER1_DECISION.json`; v1-대-v1 재계산도 **−14.3714** |
| **G-A016** | 학습(ang_vel_xy −0.15) + tier-1, engine `1.2.0` | Pilot-01(**v2**) · `c4d78adf…` | ang_vel_xy_l2 −0.05→−0.15 · step 977 → `model_999` · `4f839e0fa6d8da89…` | 42 | 101 | cand v2·base v2 | ○ | **1.3757** | **−45.1155** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G1~G7 **전부** | **대칭·유효** | **실제정책실패** | 같은 경로; v1-대-v1 **−28.7557** |
| **G-A017** | 학습(track 1.4) + tier-1, engine `1.2.0` | Pilot-01(**v2**) · `c4d78adf…` | track_lin_vel_xy_exp 1.2→1.4 · step 856 → `model_900` · `0563deffae52552c…` | 42 | 101 | cand v2·base v2 | ○ | **50.1992** | **+3.7079** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 사유 `G4_survival_regressed_over_0.1` **단 1건** | **대칭·유효** | **운영실패** (§2-4) | 같은 경로; v1-대-v1 **+5.3803**, 생존 후퇴 0건 |
| **G-A018** | 학습(action_rate −0.008) + tier-1, engine `1.2.0` | Pilot-01(**v2**) · `c4d78adf…` | action_rate_l2 −0.01→−0.008 · step 937 → `model_900` · `0d338316605ca8f4…` | 42 | 101 | cand v2·base v2 | ○ | **2.0926** | **−44.3986** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G1~G7 전부 | **대칭·유효** | **실제정책실패** | 같은 경로; v1-대-v1 **−30.9528** |
| **G-A019** | track 1.3. 사양(`643b36c9…`)·업로드 준비 완료 후 캠페인 리셋으로 **미실행** | — | — | — | — | — | — | — | — | — | — | 해당 없음 | 미실행 | `GO2_PROJECT_STATE.md` G-F128, §26 말미 |
| **G-A020** | 학습(Chain-01 + lin_vel_z −2.0) + tier-1, engine `1.3.0`/archive `a0304277…` | **Chain-01** tier-1 캐시(**v1**) · iter 900 · `143871e3…` | step 964 → `model_999` · `1843ad6cca85f930…` | 42 | 101 | **cand v2·base v1 6/7 + v2 1/7** | ○ | **0.4283** | **−18.1822** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G1~G6 | **비대칭·무효** | 계측실패 + 실제정책실패(절대 자세 미달, §2-5) | `_keep/go2_g_a020_.../`; v1-대-v1 **−0.2211**, 생존 후퇴 0건 |
| **G-A021** | 학습(Chain-01 + ang_vel_xy −0.05) + tier-1 | Chain-01(**v1**) · `143871e3…` | step 876 → `model_900` · `414a4fd124379b0e…` | 42 | 101 | cand v2·base v1 6/7 | ○ | **12.0026** | **−6.6079** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G2~G6 | **비대칭·무효** | 계측실패 | v1-대-v1 **−0.3516**, 생존 후퇴 0건 |
| **G-A022** | 학습(Chain-01 + feet 0.20) + tier-1 | Chain-01(**v1**) · `143871e3…` | step 979 → `model_999` · `92c08d9001b6c987…` | 42 | 101 | cand v2·base v1 6/7 | ○ | **4.8830** | **−13.7275** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G1~G6 | **비대칭·무효** | 계측실패 + 실제정책실패(절대 자세 미달) | v1-대-v1 **+0.4491**, 생존 후퇴 0건 |
| **G-A023** | 평가 전용(학습 없음). Chain-01 동결 69-case×3seed, `EVALUATOR=posture_gate_v2` | — (단일 arm) | Chain-01 · `143871e3…` | (학습 없음) | 101/202/303 | v2(schema 2) 69/69 | 해당 없음 | **2.3077** | — | **11.5976** | `INTERNAL_GATE_FAIL` (G1·G3·G4·G5·G7 생존 0) | 유효(단일 arm) | 실제정책실패 확인 + 계측실패(G7 중복 잔존) | `_keep/go2_chain01_baseline/`; 로컬 `build_policy()` 재현 |
| **G-A024** | 학습(Default-01 + ang_vel_xy −0.15) + tier-1, archive `81c3bcce…` | Default-01(**v1**) · `99ceeaa1…` | step **662** → `model_700` · `ef8ef705dbbfc564…` | 42 | 101 | cand v2·base v1 6/7 | ○ | **0.0000** | **−17.1321** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G1~G7 전부 | **비대칭·무효** | 계측실패 + 실제정책실패(절대 자세 미달) + 운영실패(비교 iter 662 vs 800) | v1-대-v1 **+3.4617**, 생존 후퇴 0건; `height_rel_median 0.132`, `fallen 32/32` |
| **G-A025** | 학습(Default-01 + flat_orientation −1.0) + tier-1, archive `81c3bcce…` | Default-01(**v1**) · `99ceeaa1…` | step 884 → `model_900` · **`676cc1cb93c70cd6…` = G-A013과 동일 SHA** | 42 | 101 | cand v2·base v1 6/7 | ○ | **15.7043** | **−1.4278** | 동일 | `INTERNAL_EARLY_KILL_FAIL` — 총점 + G2·G4·G5·G6 | **비대칭·무효** + **중복** | 중복 + 계측실패 + 운영실패 | 두 `TIER1_DECISION.json`의 `baseline_points_70`·`candidate_points_70`·`delta`가 소수 16자리까지 동일 |

**A006~A025 등장 횟수: 각 1회.** G-A011만 (a)미실행 원안과 (b)재부여 라벨을 한 행 안에 병기했다.

### 2-3. 단일변수 통제는 실제로 지켜졌다 (긍정 확인)

각 실행의 서버 산출 `training/env.yaml`에서 6개 reward weight를 직접 파싱한 결과:

| Run | track | feet | lin_z | ang_xy | action | flat | 기준선 대비 변경 |
|---|---:|---:|---:|---:|---:|---:|---|
| G-A009/A011 | 1.2 | 0.01 | −3.0 | −0.08 | −0.01 | 0.0 | track 1개 |
| G-A010 | 1.0 | 0.01 | **−2.0** | −0.08 | −0.01 | 0.0 | lin_z 1개 |
| G-A013 / G-A025 | 1.0 | 0.01 | −3.0 | −0.08 | −0.01 | **−1.0** | flat 1개 |
| G-A015 | 1.2 | **0.35** | −2.0 | −0.05 | −0.01 | 0.0 | feet 1개 |
| G-A016 | 1.2 | 0.2 | −2.0 | **−0.15** | −0.01 | 0.0 | ang 1개 |
| G-A017 | **1.4** | 0.2 | −2.0 | −0.05 | −0.01 | 0.0 | track 1개 |
| G-A018 | 1.2 | 0.2 | −2.0 | −0.05 | **−0.008** | 0.0 | action 1개 |
| G-A020 | 1.2 | 0.01 | **−2.0** | −0.08 | −0.01 | 0.0 | lin_z 1개 |
| G-A021 | 1.2 | 0.01 | −3.0 | **−0.05** | −0.01 | 0.0 | ang 1개 |
| G-A022 | 1.2 | **0.2** | −3.0 | −0.08 | −0.01 | 0.0 | feet 1개 |
| G-A024 | 1.0 | 0.01 | −3.0 | **−0.15** | −0.01 | 0.0 | ang 1개 |

**모든 학습 실행이 정확히 1개 항만 바꿨다.** `ARTIFACT_VERIFIED`. 단일변수 통제 자체는
캠페인의 실패 원인이 **아니다**. 실패는 통제된 변수의 **비교 대상(기준선)과 계측**에 있었다.

### 2-4. 양의 총점 delta가 gate로 거절된 사례 (§5.2-4)

| Run | delta /70 | 발화 gate | 성격 |
|---|---:|---|---|
| G-A007 | **+3.8656** (69-case, 대칭 v1) | `g5_proxy_delta_at_least_plus_0_03` | 지정 시나리오 절 |
| G-A009/A011 | **+3.0903** (tier-1, 대칭 v1) | `target_G1_improvement_below_0.05` | 지정 시나리오 절 |
| G-A010(원) | **+2.2572** (tier-1, 대칭 v1) | `target_G1_improvement_below_0.05` | 지정 시나리오 절 |
| G-A017 | **+3.7079** (tier-1, **대칭 v2**) | `G4_survival_regressed_over_0.1` | **생존 인수 단독 절** |

앞의 3건은 엔진 1.2.0에서 `target_scenario` 절이 관측값으로 강등되며 **규칙 자체가 폐기**됐다
(`go2_tuning_eval_report.py:28-31,44`). 즉 이 3건은 **지금은 존재하지 않는 규칙**에 의해 죽었다.

**G-A017은 성격이 다르다.** 시나리오별 `scenario_proxy`를 직접 대조하면:

| G | base proxy | cand proxy | Δproxy | base surv | cand surv | Δsurv |
|---|---:|---:|---:|---:|---:|---:|
| G1 | 0.89322 | 0.90312 | **+0.0099** | 1.000 | 1.000 | 0 |
| G2 | 0.92471 | 0.96591 | **+0.0412** | 1.000 | 1.000 | 0 |
| G3 | 0.48483 | 0.56930 | **+0.0845** | 0.8125 | 0.90625 | +0.094 |
| G4 | 0.55333 | 0.56920 | **+0.0159** | 1.000 | 0.78125 | **−0.219** |
| G5 | 0.40941 | 0.51871 | **+0.1093** | 0.71875 | 0.71875 | 0 |
| G6 | 0.94082 | 0.93407 | −0.0068 | 0.96875 | 0.96875 | 0 |
| G7 | 0.56013 | 0.66323 | **+0.1031** | 0.9375 | 1.000 | +0.063 |

**7개 시나리오 중 6개의 공식형 시나리오 점수가 올랐고, "후퇴했다"는 G4조차 시나리오 점수는
+0.0159 개선됐다.** 거절 사유는 곱의 **인수 하나**(생존)의 후퇴다. 공식형 목적함수는
인수가 아니라 곱을 채점한다(`AGENTS.md:294-298`). 이것은 계측 결함이 아니라
**게이트 설계와 목적함수의 불일치**, 즉 운영 실패다.

또한 G-A017 후보의 tier-1 가중 분수는 `50.19916/70 = 0.7171`로, registry
`minimum_weighted_simulation_proxy: 0.70`(`:45`)을 **넘긴 유일한 Go2 측정치**다.
그럼에도 대표평가(seed 202·303)·69-case로 승급되지 않았고, 260905 리셋에서 계보 전체가 폐기됐다.
후보의 `model_best.pt`(`0563deffae52552c…`)와 `evaluation/candidate/policy.pt`는
`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/`에 **로컬 보존돼 있다** — 재학습 없이
재평가 가능하다. `ARTIFACT_VERIFIED`.

### 2-5. 같은 세대 평가에서도 실제로 붕괴한 사례 (§5.2-5) — 계측 결함 뒤에 숨기지 않는다

대칭 v2 비교(Pilot-01 기준선) 4건 중 **3건은 진짜 붕괴**다. 대칭 v1 재채점으로도 부호가 유지된다.

| Run | 대칭 v2 delta | 대칭 v1 delta | 후보 절대 실측 (`forward_fast` seed 101) | 판정 |
|---|---:|---:|---|---|
| G-A015 | −30.1219 | **−14.3714** (G5 생존 −0.906) | 속도 1.2017 m/s(명령 1.2 — **보행은 함**), `height_rel_median 0.164` (임계 0.18 미달) | **실제 붕괴** — 걷지만 주저앉음 |
| G-A016 | −45.1155 | **−28.7557** | 속도 **0.0269** m/s, `height_rel_median 0.122` | **실제 붕괴** — 보행 미습득 |
| G-A018 | −44.3986 | **−30.9528** | 속도 **0.0338** m/s, `height_rel_median 0.097` | **실제 붕괴** — 보행 후 에피소드 내 붕괴 |
| G-A017 | +3.7079 | **+5.3803** | 속도 1.1733 m/s, `height_rel_median 0.339` | **실제 개선** |

비대칭 실행 중에서도 **기준선과 무관한 절대 지표만으로 이미 실격**인 후보가 있다:

| Run | 후보 `height_rel_median` | 후보 속도(명령 1.2) | `fallen/num_envs` | 절대 판정 |
|---|---:|---:|---|---|
| G-A020 | 0.121 | 0.0334 | — | 자세 임계 0.18 미달 → 실제 실패 |
| G-A022 | 0.151 | 0.0298 | — | 자세 임계 미달 → 실제 실패 |
| G-A024 | 0.132 | 0.0320 | **32/32** | 자세 임계 미달·전원 낙상 → 실제 실패 |
| G-A010(재) | 0.331 | 0.0239 | — | 자세는 정상, **이동 불가** |
| G-A013/A025 | 0.387 | 0.0257 | — | 자세는 정상, **이동 불가** |
| G-A021 | 0.395 | 0.0224 | — | 자세는 정상, **이동 불가** |

→ 비대칭 때문에 **delta는 무효**지만, G-A020·G-A022·G-A024 세 후보는 **기준선이 무엇이든
자세 임계 미달**이다. 계측 결함이 이 세 후보를 복권하지 않는다.

### 2-6. 중복 계상 (§5.2-6)

| 항목 | 내용 | 근거 |
|---|---|---|
| **G-A025 = G-A013** | `CANDIDATE_MODEL_SHA` 동일(`676cc1cb…`), `TIER1_DECISION.json`의 base/cand/delta가 소수 16자리까지 동일 | 두 `reports/TIER1_DECISION.json` 직접 대조 |
| **G-A011 = G-A009** | 동일 결과(`+3.0902846/70`, `143871e3…`)가 두 ID로 원장에 기록됨. 해당 `TIER1_DECISION.json`은 `schema_version:1`이라 `work_id`·`run_id` 필드가 **없어** ID를 결과 자체로 확정할 수 없다 | `_keep/go2_track_lin_vel_120_v1/reports/TIER1_DECISION.json`; `GO2_PROJECT_STATE.md` §15·§16 vs G-F92·G-F131 |
| **G7 = G3 (69-case)** | 3개 69-case 스위트 전부에서 `steps.csv` byte-identical | §1-6 |
| **기준선 재사용** | Pilot-01 tier-1 캐시가 G-A015·A016·A017·A018 4회에 **동일 `46.49124/70`**로 재사용됨. 4회의 "독립 비교"가 아니라 **1회 기준선 측정에 4개 후보를 붙인 것** | 4개 `TIER1_DECISION.json#/baseline_points_70` 모두 `46.4912409491015` |
| **Default-01 캐시** | `SOURCE=VERIFIED_G_A006` 스탬프로 260901 산출물이 260906까지 재사용 | `evaluation/baseline_tier1/cases/seed_101/*/STATUS.txt` |

### 2-7. 반복 설계 (§5.2-7)

**모든 학습 실행이 `1,000 iteration · 학습 seed 42 단일 · 평가 seed 101 단일 · case 7개`다.**

- tier-1 registry(`meta/tier1_registry.json`)는 `schema_version "1.2.0"`,
  `required_evaluation_seeds: [101]`, 시나리오당 case **1개**
  (`G1:forward_fast, G2:diagonal_left, G3:rough_forward, G4:slope_plus_20, G5:stairs_15_up,
  G6:push_pos_x, G7:dr_seed_101`).
- 즉 판정 하나가 **7개 rollout 집합**에 근거한다. worst-case 집계이므로 시나리오 점수 =
  그 1개 case 값이다.
- `quadruped_rewards.py:120` 배포 원문: *"같은 설정·같은 seed 라도 cudnn 비결정성으로 매번
  조금씩 다릅니다 (정상)."* → **배포 파일 스스로 단일 seed 재현성을 부정한다.**
- `quadruped_rewards.py:119` 배포 원문: *"걸음 '성격' 은 3000~5000 iter 면 드러납니다"*,
  `:113` *"0) 그대로 학습(3000 iter) → play.py 로 '기본 성격' 관찰 (기준점)"*
  → **배포 지침이 요구한 기준점은 3,000 iter인데 캠페인은 1,000 iter로 기준점을 만들었다.**
- 반대 방향의 재현성 증거도 있다: G-A013과 G-A025는 동일 설정에서 **비트 동일한 checkpoint**를
  만들었다(`676cc1cb…`). 즉 **학습 자체는 결정론적으로 재현**된다. 재현되지 않는 것은
  seed·초기조건 일반화이지 같은 seed의 반복이 아니다.
- **no-op control은 캠페인 전체에서 0건.** `G-D103`이 계획했으나 `G-D105`에서 보류됐다.

### 2-8. `model_best.pt` 선택과 비교 iter 정합성 (§5.2-8·9)

`go2_task/_finalize.py:66-92`: `Train/mean_reward` 태그의 **argmax**를 취하고
(워밍업 앞 10% 제외, `:84-85`), 가장 가까운 `save_interval=100` 격자 checkpoint를 고른다.

실측 선택 결과 (`logs/**/candidate_training.log`의 `[INFO] Best by 'Train/mean_reward'` 행):

| Run | best step | 선택된 checkpoint | 기준선 checkpoint iter |
|---|---:|---|---:|
| G-A007 | 829 | `model_800.pt` | Default 800 |
| G-A009/A011 | 900 | `model_900.pt` | Default 800 |
| G-A010 | 864 | `model_900.pt` | Default 800 |
| G-A013 / G-A025 | 884 | `model_900.pt` | Default 800 |
| G-A015 | 935 | `model_900.pt` | Pilot 972→`model_999` |
| G-A016 | 977 | `model_999.pt` | Pilot 972→`model_999` |
| G-A017 | 856 | `model_900.pt` | Pilot 972→`model_999` |
| G-A018 | 937 | `model_900.pt` | Pilot 972→`model_999` |
| G-A020 | 964 | `model_999.pt` | Chain-01 900 |
| G-A021 | 876 | `model_900.pt` | Chain-01 900 |
| G-A022 | 979 | `model_999.pt` | Chain-01 900 |
| **G-A024** | **662** | **`model_700.pt`** | Default 800 |

**비교 iter가 700~999로 최대 300 iteration(30%) 벌어진다.** 1,000-iter 구간은 학습 곡선이
아직 상승 중이므로 이 격차는 무시할 수 없다. 특히 **최악의 결과를 낸 G-A024가 가장 이른
checkpoint(662→700)로 평가됐다** — "reward가 나빠서 붕괴"와 "300 iteration 덜 학습돼서 붕괴"를
현재 자료로는 분리할 수 없다(`INTERNAL_GATE_INCONCLUSIVE`).

또한 `Train/mean_reward`는 **reward 계수가 다르면 스케일이 다른 목적함수**다.
`G-D11`(`GO2_PROJECT_STATE.md:59`)은 정책 비교에 `Train/mean_reward` 절대값 사용을
금지했지만, **checkpoint 선택에는 그대로 쓰이고 있다.** 즉 후보마다 서로 다른 목적함수의
argmax로 평가 대상이 정해진다. H1 캠페인은 같은 구조를 `PROJECT_STATE.md:606-620`(F42)에서
"`model_best.pt` 선별은 품질 순위가 아니라 잡음의 argmax"로 이미 판정해 두었으나,
그 판정이 Go2 원장·엔진 계약에 반영된 흔적은 없다.

### 2-9. 영상 증거

| 상태 | 실행 |
|---|---|
| `VIDEO_OBSERVED` | G-A006 (14편, `reports/evidence/go2_default_vs_pilot_260901/VIDEO_OBSERVATION.md`), G-A009/A011 G1 1편 (`GO2_PROJECT_STATE.md` G-D46) |
| `VIDEO_UNKNOWN` | G-A012(7편), G-A023(7편), G-A007(7편), G-A010·A010재·A013·A015·A016·A017·A018·A020·A021·A022·A024·A025 (각 1편) |

G-A012 분석 보고서 자신이 `VIDEO_UNKNOWN`을 명시한다
(`reports/GO2_PILOT_V2_BASELINE_RESULT_ANALYSIS_260903.md:32,80`).
**G-A015 이후의 모든 실패 진단(웅크림·고착·리듬 붕괴)은 `steps.csv`만으로 내려졌고
영상은 한 번도 판독되지 않았다.** `G-D24`가 정한 영상 게이트는 실질적으로 작동하지 않았다.

---
### 2-10. 원장에 없는 발견 — **Default-01 계보는 걷지 못한다**

`summary.json#/speed_xy_mean`을 seed 101의 대표 case에서 직접 대조했다.
(명령 속도: `forward_slow 0.30` / `forward_nominal 0.75` / `forward_fast 1.20` /
`rough_forward 0.50` / `slope_plus_20 0.50` / `stairs_15_up 0.50` m/s —
`server_run_go2_chain01_baseline.sh:130-161`)

| 정책 | forward_slow | forward_nominal | forward_fast | rough_forward | slope_plus_20 | stairs_15_up |
|---|---:|---:|---:|---:|---:|---:|
| **Default-01** (G-A006) | 0.029 | 0.027 | **0.026** | 0.032 | 0.029 | 0.028 |
| **G-A007** feet 0.20 | 0.028 | 0.030 | **0.031** | 0.030 | 0.028 | 0.028 |
| **Chain-01** (G-A023) | 0.027 | 0.026 | **0.027** | 0.031 | 0.026 | 0.025 |
| **Pilot-01** (G-A006·G-A012, 동일값) | 0.202 | 0.742 | **1.174** | 0.241 | 0.214 | 0.320 |

**Default-01은 명령이 무엇이든 0.026~0.032 m/s로 제자리에 서 있다.** 명령 1.2 m/s에 대해
`tracking_xy_rmse = 1.1852` → `tracking_proxy = exp(−(1.1852/0.5)²) = 0.0036`.
Pilot-01은 같은 1,000 iteration·같은 seed 42로 학습됐는데 1.174 m/s로 **정상 추종**한다.

같은 표를 후보 전체로 확장하면 (후보 `forward_fast` seed 101):

| 계보 | Run | 후보 속도 | 후보 `height_rel_median` | 보행 여부 |
|---|---|---:|---:|---|
| Default-01 | G-A010(원·재) | 0.0239 | 0.331 (재측정) | ✕ |
| Default-01 | G-A009/A011 (→Chain-01) | 0.0275 | — (v1) | ✕ |
| Default-01 | G-A013 / G-A025 | 0.0257 | 0.387 | ✕ |
| Default-01 | G-A024 | 0.0320 | 0.132 | ✕ |
| Chain-01 | G-A020 | 0.0334 | 0.121 | ✕ |
| Chain-01 | G-A021 | 0.0224 | 0.395 | ✕ |
| Chain-01 | G-A022 | 0.0298 | 0.151 | ✕ |
| **Pilot-01** | G-A015 | **1.2017** | 0.164 | ○ (주저앉음) |
| **Pilot-01** | G-A016 | 0.0269 | 0.122 | ✕ |
| **Pilot-01** | G-A017 | **1.1733** | **0.339** | ○ (정상) |
| **Pilot-01** | G-A018 | 0.0338 | 0.097 | ✕ |

**Default-01·Chain-01 계보에서 학습된 9개 후보 전부가 보행을 습득하지 못했다.**
Pilot-01 계보에서만 보행하는 정책이 나온다(4개 중 2개).

이 현상은 배포 코드가 이미 경고한 국소최적이다 —
`go2_task/env_cfg.py:68-71`:
*"추종 보상이 exp(-err²/0.5²) 라 2 m/s+ 명령은 보상 ≈ 0 → 학습 초기 gradient 없음 →
'전진 포기 + 제자리 회전' 국소최적 (실측: track_lin 만 0.13 · error_vel_xy 1.99 · terrain 0)."*

**결과적 의미 3가지**

1. `G-D92`(260907 시점 동결 기준선 = Default-01)가 지정한 기준선은 **이동 능력이 0에 가까운
   퇴화 정책**이다. 이 기준선 위의 단일변수 delta는 바닥 근처의 잡음이다.
2. `G-F141`이 "Chain-01의 6/7 붕괴는 `track_lin_vel_xy_exp 1.0→1.2` 한 값이 만든 자세 회귀"라고
   해석한 것은 **원자료와 맞지 않는다.** Default-01(0.0265 m/s)과 Chain-01(0.0275 m/s)은
   **사실상 같은 행동**이며, 두 정책의 차이는 `posture_gate_v2`로 측정된 쪽이 Chain-01뿐이라는 것이다.
   Default-01의 `survival_proxy_v2`는 지금도 `[미측정]`이지만, 같은 속도·같은 명령에서
   Chain-01이 `height_rel_median 0.1225`·`fallen 32/32`를 낸 것을 보면
   **Default-01도 v2에서 붕괴할 가능성이 높다**(유력한 추론, 확정 아님).
3. `GO2_REWARD_EVIDENCE_MASTER.md:257-258`이 세운 가설 —
   *"1,000 iter가 빠른 gait를 형성하기엔 짧을 수 있다"* — 는 **Pilot-01 반례로 부분 반증된다.**
   Pilot-01은 같은 1,000 iter로 1.17 m/s를 낸다. 따라서 병목은 iteration 수 단독이 아니라
   **reward 조합 × iteration 수의 상호작용**이며, 배포 기본값 조합이 1,000 iter 안에
   국소최적을 탈출하지 못한다는 것이다.

---
## 3. H1 대 Go2 비교 (§5.3)

> H1을 성공 신화로 두지 않는다. H1의 내부 점수 `92.73/100`은 `OFFICIAL_RESULT`가 아니라
> 내부 proxy이며(`H1_REWARD_EVIDENCE_MASTER.md:281-285`), H1의 **실제 제출 여부조차
> `[미측정]`**이다(같은 문서 L373-376). H1이 "잘됐다"고 말할 수 있는 범위는
> **증거 폐쇄 절차**이지 공식 성적이 아니다.

### 3-1. 비교표

| 비교 축 | H1 원자료에서 확인된 사실 | Go2 원자료에서 확인된 사실 | 차이가 실패 연속성에 미친 영향 | 증거 강도 |
|---|---|---|---|---|
| baseline 확정 시점·조건 | Run01이 baseline이고 `base_contact=0.9244`로 **명시적 FAIL 판정**을 받은 뒤, 이후 run은 직전 채택 run 위에 쌓임. 최종 기준(Run06)은 **모든 reward 탐색이 끝난 뒤** 동결됨 (`H1_REWARD_EVIDENCE_MASTER.md:65-73`) | 기준선이 4회 교체됨: Default-01(260901) → Pilot-01(260903 `G-D69`) → Chain-01(260905 `G-F132`) → Default-01 복귀(260905 `G-D92`). 각 교체에 **재검증 없음** | 기준선이 바뀔 때마다 이전 delta가 비교 불능이 됨. A007·A009/A011·A010은 Default 기준, A015~A018은 Pilot 기준, A020~A022는 Chain 기준 → **하나의 시계열이 아니다** | 높음 |
| 한 번에 바꾼 reward 변수 수 | Run02~05 각 1개 (`termination`, `angular`, `linear`) | 전 학습 실행 각 1개 (§2-3 전수 확인). 단 Pilot-01 자체가 4항 동시변경 산물 | Go2의 단일변수 규율은 **H1과 동등하거나 더 엄격**. 실패 원인이 아님 | 높음 |
| screening iteration·승급 기준 | screening 3,000 iter(≈36분), 승급 후 장기 10,000 iter (`PROJECT_STATE.md:998`, `H1_..._MASTER.md:70`) | screening **1,000 iter**(≈59분, `G-F80`). 배포 파일 권장은 3,000 (`quadruped_rewards.py:113,119`) | 배포 기본값 조합이 1,000 iter에 국소최적을 못 벗어나 **기준선 자체가 퇴화**(§2-10) | 높음 |
| 학습 seed / 평가 seed 반복 | 학습 seed **42 단일**(한계 명시, `H1_..._MASTER.md:294-297`). 평가 seed **101·202·303 3개**, 30/30 case 완주, 시나리오별 **최악 seed** 채택 (`:266-280`) | 학습 seed **42 단일**. 평가 seed: 기준선 3종(A006·A012·A023)만 101·202·303. **모든 후보 판정은 seed 101 단일** | 후보 판정이 1-seed·1-case/시나리오. worst-case 집계까지 겹쳐 **케이스 1개의 우연이 시나리오 점수를 결정** | 높음 |
| evaluator 세대 고정 | Run06 동결 후 **하나의 evaluator로만** 30 case 실행. 세대 교체 없음. 사후 자세 재채점은 GPU 0분 로컬 스크립트(`tools/retro_score_h1_flat_survival.py`)로 수행, 원 점수는 손대지 않음 | v1(termination-only) → v2(posture_gate) 전환이 **캠페인 중간**에 일어났고, 엔진의 **기준선 캐시만 v1로 남았다** (§3-2) | 6개 실행(A010재·A013·A020·A021·A022·A024·A025 중 A025 포함 시 6~7건)의 delta가 무효 | 높음 |
| 자세 기반 생존 검증 범위 | 평지 계열 21 case·672 env-episode 재채점, **0/672 낙상**, 최저 골반 0.8764 m(임계 0.55의 1.59배). **`H5_rough`·`H6_slope`(가중 0.30)는 `POSTURE_UNMEASURED`** (`H1_..._MASTER.md:306-331`) | Pilot-01·Chain-01·후보 arm만 v2. **Default-01은 단 한 번도 v2로 측정된 적 없음**(전수 지문 스캔) | H1은 0.70 커버·0.30 미측정을 **명시**했고, Go2는 기준선 미측정을 **인지하지 못한 채** 비교를 계속했다 | 높음 |
| checkpoint 선택 기준·비교 iter 정합성 | `_finalize.py` argmax. **F42로 이미 결함 판정**: "잡음의 argmax", 5 run의 best iter 2999/2800/2500/2800/2700 (`PROJECT_STATE.md:606-641`) | 동일 로직(`go2_task/_finalize.py:86`). 비교 iter 662~979, 기준선 800/900/972 (§2-8). **동일 결함이 Go2 원장·엔진에 반영되지 않음** | 최악 결과(G-A024)가 가장 이른 checkpoint. reward 효과와 checkpoint 효과 분리 불가 | 높음 |
| 정책 평가 완료 후 다음 학습 진행 | Run06 3-seed 30/30 완주 → `INDEPENDENT_VALIDATION_PASS` → **동결·재학습 금지**(`12-e`). 그 다음 학습 0건 | A012(Pilot 69-case) 이후 A013~A018을 **대표평가·69-case 없이** 연속 실행. A017이 승급선을 넘겼는데도 seed 202·303 미실행 | 유일한 개선 후보가 확인 없이 폐기 | 높음 |
| 시나리오 구성·지형/경사/계단/DR 비중 | H1~H7: 평지 0.70 + 요철 0.15 + 완만 경사 ±10° 0.15. **계단·박스 없음** (`AGENTS.md:376-383`) | G1~G7: 평지 0.40(G1+G2+G6) + 험지 0.20 + 경사 ±20° 0.15 + 계단 10~15cm 0.15 + DR 0.10 (`AGENTS.md:387-397`) | **구조적으로 Go2가 어렵다**: 비평지 가중이 0.30 → 0.60, 경사가 ±10° → ±20°, 계단·DR 신규 | 높음(규정 요약 기준) |
| 안전성 reward/lever 실제 활성 상태 | `termination_penalty`가 실재하고 Run02·03에서 실제로 튜닝됨(−5→−50→−90) | 서버 `env.yaml` 실측: `undesired_contacts`가 `null`, `termination_penalty` 항 **부재**. 11개 reward 중 `flat_orientation_l2`·`dof_pos_limits`만 정의·미사용 (`G-F77`·`G-F78`) | Go2에는 **생존을 직접 겨냥하는 lever가 사실상 `flat_orientation_l2` 하나뿐**. H1의 튜닝 경로를 그대로 쓸 수 없다 | 높음 |
| 영상·telemetry·내부 정량·공식 결과 분리 | 4층 분리 유지. Run06 `CALIBRATION_PASS / GENERALIZATION_UNVERIFIED` → `INDEPENDENT_VALIDATION_PASS`로 단계 표기 | 층위 표기는 유지(`official_result: OFFICIAL_RESULT_UNMEASURED`가 코드에 박힘). 그러나 **영상 층이 A015 이후 비어 있음**(§2-9) | 실패 메커니즘 진단이 telemetry 단일 소스에 의존 | 중간 |
| 실패 실험이 다음 결정을 실제로 구분했는가 | Run03(−90) 실패 → −50 유지로 **되돌아감**. D24로 노브 탐색 종료 후 수렴(iteration)으로 레버 전환 | A013 실패 → A014 취소, A016 실패 → 다이얼째 기각, A018 실패 → 다이얼째 기각. **6개 항 전부 소진 후에도 같은 파이프라인으로 A020~A025 계속** | 실패가 "다이얼 제거"만 낳고 **파이프라인 의심으로 전환되지 않음**. G-D111(이상신호 규칙)은 260907에야 신설 | 높음 |

### 3-2. evaluator 비대칭 — 지문 전수 스캔 결과

`workspace/_keep/*/evaluation/*/cases/**/summary.json`의 `schema_version`·`survival_proxy_source`
전수 집계:

| 실행 | 후보 arm | 기준선 arm | 대칭? |
|---|---|---|---|
| G-A006 (default/pilot) | v1 69/69 | v1 69/69 | ○ |
| G-A007 | v1 69/69 | v1 (캐시) | ○ |
| G-A009/A011 | v1 7/7 | v1 7/7 | ○ |
| G-A010 (원, 260902) | v1 7/7 | v1 7/7 | ○ |
| **G-A013** | **v2 7/7** | **v1 6/7 + v2 1/7** | **✕** |
| G-A015 | v2 7/7 | v2 7/7 | ○ |
| G-A016 | v2 7/7 | v2 7/7 | ○ |
| G-A017 | v2 7/7 | v2 7/7 | ○ |
| G-A018 | v2 7/7 | v2 7/7 | ○ |
| **G-A020** | **v2 7/7** | **v1 6/7 + v2 1/7** | **✕** |
| **G-A021** | **v2 7/7** | **v1 6/7 + v2 1/7** | **✕** |
| **G-A022** | **v2 7/7** | **v1 6/7 + v2 1/7** | **✕** |
| **G-A010 (재, 260906)** | **v2 7/7** | **v1 6/7 + v2 1/7** | **✕** |
| **G-A024** | **v2 7/7** | **v1 6/7 + v2 1/7** | **✕** |
| **G-A025** | **v2 7/7** | **v1 6/7 + v2 1/7** | **✕** |
| G-A012 / G-A023 | v2 69/69 (단일 arm) | — | 해당 없음 |

**비대칭 6건**(A013, A020, A021, A022, A010재, A024, A025 = 7건이나 A025는 A013의 중복이므로
**고유 6건**). 규칙성: 기준선이 **Default-01 또는 Chain-01**이면 비대칭, **Pilot-01**이면 대칭.
매 실행 새로 계산되는 `dr_seed_101` 1건만 v2인 것도 전 실행 동일하다.

**대칭 v1으로 재채점한 결과** (`_case_proxy`를 `survival_proxy_v1`로 치환, tier-1 registry 사용):

| Run | 보고된 delta (비대칭) | v1-대-v1 delta | 생존 후퇴 >0.1 건수 (v1-대-v1) |
|---|---:|---:|---:|
| G-A010 (재) | −7.6325 | **+2.2572** | 0 |
| G-A013 | −1.4278 | **+3.6544** | 0 |
| G-A020 | −18.1822 | **−0.2211** | 0 |
| G-A021 | −6.6079 | **−0.3516** | 0 |
| G-A022 | −13.7275 | **+0.4491** | 0 |
| G-A024 | −17.1321 | **+3.4617** | 0 |
| G-A025 | −1.4278 | **+3.6544** | 0 |

G-A010(재)의 v1-대-v1 값 `+2.2572`가 260902 원 실행의 `+2.2571599`
(`_keep/go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json`)와 **일치**한다 →
재채점 절차 자체의 교차 검증. `ARTIFACT_VERIFIED`.

**주의:** v1-대-v1 값은 **채택 근거가 아니다.** v1은 규정 제8조("넘어지지 않고 완주한 비율")를
만족하지 못하는 지표다(`AGENTS.md:296-299`). 두 arm이 **모두 v2**가 되기 전에는 이 7건의
참값을 모른다 → `INTERNAL_GATE_INCONCLUSIVE`.

### 3-3. 여섯 질문에 대한 답

#### Q1. "Go2의 연속 FAIL" 중 몇 건이 무엇인가?

분류 기준:
- **실제 정책 실패** = 두 arm이 같은 evaluator이거나, 기준선과 무관한 **절대 지표**
  (`height_rel_median < 0.18` 또는 명령 대비 속도 < 5%)로 이미 실격.
- **비교 무효/계측 실패** = 두 arm의 evaluator 지문 불일치, 또는 점수식·집계 결함이
  판정을 지배.
- **관리상 실패** = 측정은 유효한데 gate·기준선 교체·실험 순서가 증거를 앞질렀다.
- **미실행·중복** = GPU 소비 0 또는 비트 동일 재현.

| 분류 | 건수 | 실행 |
|---|---:|---|
| **실제 정책 실패** | **3** | G-A015, G-A016, G-A018 (대칭 v2·v1 양쪽에서 큰 음수) |
| **실제 정책 실패 (비대칭이지만 절대 지표로 실격)** | **3** | G-A020, G-A022, G-A024 |
| **비교 무효/계측 실패 (판정 불능)** | **4** | G-A010(재), G-A013, G-A021, G-A025 — 단 A025는 중복과 겹침 |
| **관리상 실패 (유효 측정을 잘못 처리)** | **4** | G-A007, G-A009/A011, G-A010(원), **G-A017** |
| **미실행** | **3** | G-A011(a) 원안, G-A014, G-A019 |
| **중복** | **2** | G-A025(=A013), G-A011(b) 라벨 재사용 |
| **인프라(GPU 학습 없음)** | **1** | G-A008 |
| **기준선 측정(성공적 회수)** | **3** | G-A006, G-A012, G-A023 |

**"연속 FAIL"로 관측된 학습 실행 12건**(A007, A009/A011, A010원, A013, A015, A016, A017, A018,
A020, A021, A022, A010재, A024, A025 = 14 슬롯 중 중복 1·재측정 1 제외하면 12 고유 학습)
중에서:

- **진짜로 정책이 무너진 것: 6건** (A015, A016, A018, A020, A022, A024)
- **계측 비대칭 때문에 판정 불능: 3건** (A010재, A013/A025, A021)
- **측정은 멀쩡한데 gate·운영이 죽인 것: 4건** (A007, A009/A011, A010원, A017)

즉 **"12전 12패"의 절반은 정책 실패가 아니다.**

#### Q2. H1이 더 잘 진행된 핵심 이유는 정책·reward인가, 실험 설계·증거 폐쇄성인가?

**설계와 증거 폐쇄성이 지배적이다.** 근거:

1. H1도 학습 seed는 42 하나뿐이고(`H1_..._MASTER.md:294-296`) `model_best.pt` 선택 결함(F42)도
   동일하다. 즉 **방법론의 절대 수준이 높아서가 아니다.**
2. H1은 **reward 탐색 단계에서 시나리오 evaluator를 쓰지 않았다.** Run02~05의 판정은
   tfevents 31개 태그(`error_vel_xy/step`, `base_contact`, `mean_std`, episode length)로 내렸다
   (`PROJECT_STATE.md:553,561,614`). 이 계측은 **두 arm이 구조적으로 같은 자**다 —
   같은 학습 로그 포맷에서 같은 태그를 읽으므로 비대칭이 원리적으로 불가능하다.
   시나리오 evaluator는 **탐색이 끝난 뒤 동결 정책 1개에만** 적용됐다.
3. Go2는 반대로 **시나리오 evaluator를 스크리닝 도구로 썼고**, 그 evaluator가 캠페인 중간에
   세대 교체됐으며, 기준선 arm은 캐시로 고정돼 세대가 갈렸다. 같은 reward 방법론이라도
   이 배치에서는 신호가 나오지 않는다.
4. 반증 가능 조건: 만약 H1의 성과가 reward 값 자체에서 왔다면, Go2에서도 동일한 reward
   방향(추종↑)이 통해야 한다. 실제로 **통했다** — G-A017(track 1.2→1.4)이 대칭 비교에서
   `+3.71/70`(v2)·`+5.38/70`(v1)로 개선했다. 즉 reward 지식이 부족한 것이 아니라
   **그 개선을 확인하고 승급시킬 설계가 없었다.**

#### Q3. "Go2 시나리오가 더 어렵다"는 주장은 로컬 규정으로 어디까지 확인되는가?

**확인되는 것 (규정 요약 기준, `AGENTS.md:376-397`):**

| 축 | H1 | Go2 |
|---|---|---|
| 평지 계열 가중 | **0.70** | **0.40** |
| 비평지 가중 | 0.30 (요철 0.15 + 경사 ±10° 0.15) | **0.60** (험지 0.20 + 경사 ±20° 0.15 + 계단 0.15 + DR 0.10) |
| 경사 각도 | ±10° | **±20°** |
| 계단 | **없음** | 10~15 cm, 가중 0.15 |
| 도메인 랜덤화 | 없음 | 가중 0.10 |

→ **구조적 난도가 Go2가 높다는 것은 규정 요약으로 확인된다.**

**확인되지 않는 것 / 직접 원인이 아닌 것:**

- 실측이 말하는 실점 위치는 지형만이 아니다. Default-01의 최대 실점은 **G1(평지 전진)**이며
  `tracking_proxy = 0.0036`이다(§2-10). 평지에서 걷지 못하는 것은 **시나리오 난도의 결과가
  아니라 정책 자체의 문제**다.
- Pilot-01은 같은 시나리오에서 G1 0.8925·G2 0.7521·G6 0.9359를 얻는다. 즉 **평지 0.40 블록은
  현재 정책 능력으로 충분히 도달 가능**하다. 어려운 것은 G3·G5(각 0.20/0.15)다.
- 따라서 **구조적 난도**(경사·계단·DR 0.60)와 **현 캠페인의 연속 실패 원인**(기준선 퇴화 +
  계측 비대칭 + gate 불일치)은 **다른 층위**다. 난도는 최종 점수 상한을 낮추지만,
  A007~A025의 FAIL 연속을 설명하지 못한다 — Pilot-01 기준 대칭 비교 4건 중
  1건은 개선(A017)이었기 때문이다.

#### Q4. H1 evaluator에도 생존 판정 한계가 있는가?

**있다. 두 가지.**

1. `workspace/training/humanoid/eval_telemetry.py:206-208`:
   `survival_rate_completed = timeouts / completed_episodes` — **종료 이벤트 기반**이며
   Go2 v1과 같은 계열이다. `H1_REWARD_EVIDENCE_MASTER.md:309-312`이 이 사실을 스스로 밝혔다.
2. 사후 자세 재채점은 **평지 계열 21 case(가중 0.70)만** 커버한다. `H5_rough`·`H6_plus10`·
   `H6_minus10`(가중 **0.30**)은 "지형 높이가 몸체 아래에서 움직여 월드좌표 높이 검사가
   성립하지 않는다"는 이유로 `POSTURE_UNMEASURED`다(`:327-331`).

**H1을 비교 기준으로 쓸 수 있는 범위:**

- 사용 가능: 실험 방법(단일변수·순차 판정), 증거 폐쇄 순서(탐색용 계측 → 동결 → 시나리오
  evaluator → 독립 seed), 반복 설계(평가 seed 3개·최악 seed 채택), 실패 기록 방식.
- 사용 불가: H1의 reward **값**과 임계값(저장소 규칙 `AGENTS.md:254-255`),
  H1의 `survival = 1.0000`을 "생존 지표가 건전하다"의 일반 근거로 쓰는 것
  (가중 0.30이 `POSTURE_UNMEASURED`),
  H1의 `65.73/70`·`92.73/100`을 성적 기준선으로 쓰는 것(`OFFICIAL_RESULT` `[미측정]`).

#### Q5. reward 값 문제라고 인과적으로 확정할 수 있는 실행 / 확정할 수 없는 실행

**확정 가능 (같은 evaluator·같은 기준선·단일변수·절대 지표 일치):**

| Run | 변경 | 결론 |
|---|---|---|
| G-A015 | Pilot `feet_air_time 0.20→0.35` | **인과 확정 — 해롭다.** 대칭 v2 −30.12, 대칭 v1 −14.37, 절대 `height_rel 0.164`. 보행은 유지하나 주저앉는다 |
| G-A016 | Pilot `ang_vel_xy_l2 −0.05→−0.15` | **인과 확정 — 해롭다.** 대칭 v2 −45.12, 대칭 v1 −28.76, 속도 0.027 |
| G-A018 | Pilot `action_rate_l2 −0.01→−0.008` | **인과 확정 — 해롭다.** 대칭 v2 −44.40, 대칭 v1 −30.95, 속도 0.034 |
| G-A017 | Pilot `track_lin_vel_xy_exp 1.2→1.4` | **인과 확정 — 이롭다.** 대칭 v2 +3.71, 대칭 v1 +5.38, 7개 시나리오 중 6개 proxy 개선, 속도·자세 모두 정상 |

단, 네 건 모두 **평가 seed 1개·case 7개·학습 seed 1개**이므로 효과의 **부호**는 확정,
**크기와 일반화**는 미확정이다.

**확정 불가:**

| Run | 이유 |
|---|---|
| G-A007, G-A009/A011, G-A010(원) | 대칭 v1 비교로 **양의 delta**를 냈으나, v1은 규정 제8조를 만족하지 못하는 생존 지표다. 같은 checkpoint의 v2 값이 없다 |
| G-A010(재), G-A013/A025, G-A021 | evaluator 비대칭. 절대 지표로도 실격이 아니다(자세 0.33~0.40 정상). 참값 불명 |
| G-A020, G-A022, G-A024 | 비대칭이라 **delta는 불명**이지만, 절대 자세 지표로 **후보 자체는 실격**이다. "reward가 나쁘다"와 "1,000 iter 재학습이 불안정하다"를 분리할 no-op control이 없다 |
| Pilot-01의 4항 조합 | 개별 인과 귀속 불가(`G-D02`). 다만 그 조합이 **보행을 습득한다**는 사실은 확정 |

#### Q6. 평가기를 먼저 고치지 않고 새 reward 학습을 계속하면 어떤 오류가 반복되는가?

1. **비대칭 오류의 재생산.** `tools/build_go2_tuning_engine.py:58-110`의
   `_default_baseline_payload()`가 260901판 `summary.json` 바이트를 복사하고
   `SOURCE=VERIFIED_G_A006`을 찍는 구조가 그대로 있는 한, Default-01·Chain-01 기준선의
   신규 tier-1은 **전부 v2-대-v1**로 채점된다. 지금까지 6건이 그렇게 나왔다.
2. **양의 delta를 생존 인수 단독 절로 죽이는 오류.** `max_survival_regression`은 곱의
   인수 하나를 본다. G-A017형(모든 시나리오 점수 개선 + 인수 하나 후퇴)이 다시 나오면
   또 거절된다.
3. **G6 무정보 판정.** `recovery_rate`가 항상 1.0이고 push case 명령이 0이므로,
   G6은 "밀침 회복"이 아니라 "정지 상태 유지"를 채점한다. 어떤 reward를 바꿔도
   G6 tracking은 0.94~0.99로 고정돼 신호를 주지 않는다.
4. **G3/G7 가중 0.30의 이중 계상.** 69-case로 승급 평가를 하면 험지 rollout 하나가
   전체 가중의 30%를 결정한다.
5. **바닥 근처 잡음의 유의성 오인.** Default-01 기준선(속도 0.026 m/s, G1 proxy 0.0036) 위에서는
   총점 delta의 대부분이 G3·G6 생존 인수의 ±0.06~0.34 요동에서 나온다.
   실제로 G-A009/A011의 `+3.09/70` 중 **77.99%가 G6 단독 기여**였다(`G-F54`).
6. **checkpoint 혼입.** `Train/mean_reward` argmax는 reward 조합마다 스케일이 다른 목적함수의
   argmax이므로, 비교 iter가 662~999로 흔들린다. reward 효과와 학습량 효과가 계속 섞인다.

---
## 4. 인과사슬과 우선순위 (§5.4)

형식: `원자료 사실 → 잘못된 측정/판정 또는 의사결정 → 다음 실행 선택에 미친 영향 → 연속 실패처럼 관측된 결과`

---

### C1 (영향도 1위) — 퇴화한 기준선 위에서 단일변수를 쟀다

`Default-01(iter 800, 99ceeaa1…)의 모든 case 평균 속도가 0.026~0.032 m/s이고 G1
tracking_proxy가 0.0036이다(전 case summary.json 실측)`
→ `이 정책을 "배포 기본값 control"로 승격하고(G-D09·G-D10), 그 위의 총점 delta를 reward
인과효과로 해석했다. 정책이 '걷지 못한다'는 사실은 원장 어디에도 기록되지 않았다`
→ `A007·A009/A011·A010(원·재)·A013·A024·A025 7건과, 이 계보에서 파생된 Chain-01 위의
A020·A021·A022 3건, 총 10건의 학습이 이 기준선에 묶였다. 260905 리셋에서
보행 가능한 Pilot-01을 버리고 다시 이 계보로 돌아왔다(G-D92)`
→ `총점이 17~21/70 대역에 갇힌 채 ±1~3점씩 흔들리는 "연속 미달"이 관측됐다.
개선처럼 보인 것(A009/A011 +3.09)의 78%가 G6 생존 인수 요동이었다(G-F54)`

- **증거 강도: 높음.** 5개 정책 × 6개 case의 `speed_xy_mean` 직접 대조(§2-10),
  `env_cfg.py:68-71`의 국소최적 경고와 서명 일치.
- **반증 가능 조건:** Default-01 checkpoint를 `forward_fast`(cmd 1.2)에서 다시 굴렸을 때
  `speed_xy_mean ≥ 0.6`이 나오면 이 사슬은 무너진다. 또는 Default-01의 `survival_proxy_v2`가
  0.9 이상으로 나오면 "퇴화" 표현을 철회해야 한다.
- **영향 A-run:** A006, A007, A009/A011, A010(원·재), A013, A020, A021, A022, A024, A025.
- **교정하지 않으면:** 어떤 단일변수를 얹어도 총점이 바닥 근처에 머물고, 그 잡음이
  "이 다이얼도 실패"로 기록되며 참가자 파일 6개 항이 순차적으로 소진된다(이미 발생: G-F127).

---

### C2 (영향도 2위) — 후보는 새 자로, 기준선은 옛 자로 쟀다

`엔진 빌더가 260901판 baseline summary.json 바이트를 복사하고 SOURCE=VERIFIED_G_A006을
찍는다(tools/build_go2_tuning_engine.py의 _default_baseline_payload). 지문 전수 스캔 결과
Default-01·Chain-01 기준선 캐시는 schema_version 1(survival_proxy_source 필드 자체가 없음),
후보는 schema_version 2 + posture_gate_v2다`
→ `같은 판정문 안에서 후보는 자세 게이트로, 기준선은 종료 이벤트로 채점됐다.
build_policy()·tier1_decision()에 지문 대조 코드가 없고, 계약 테스트 16개 중 이를 검사하는
항목이 0건이라 아무도 멈추지 않았다`
→ `A013·A020·A021·A022·A010(재)·A024·A025 판정이 전부 이 배치로 나왔다. 세 번의 극단적
결과가 각각 "검증된 개선의 합성은 위험"(G-F135), "v1의 맹점"(G-F140),
"Default-01은 얇은 균형점"(G-F153)이라는 서로 다른 물리 가설로 해석됐다`
→ `−1.43 / −6.61 / −13.73 / −17.13 / −18.18의 "전멸" 시리즈가 관측됐다.
대칭 v1으로 다시 채점하면 같은 실행들이 +3.65 / −0.35 / +0.45 / +3.46 / −0.22이고
생존 후퇴는 0건이다`

- **증거 강도: 높음.** 지문 전수 스캔 + 대칭 재채점 교차검증(G-A010 재채점값이 260902
  원 기록 `+2.2571599`와 일치).
- **반증 가능 조건:** Default-01의 `survival_proxy_v2`가 실측돼 v2-대-v2 delta가
  보고된 값과 유사하게 나오면 이 사슬의 크기는 축소된다.
- **영향 A-run:** A013, A020, A021, A022, A010(재), A024, A025.
- **교정하지 않으면:** 신규 tier-1이 전부 같은 비대칭으로 채점되고, 극단적 음수 delta가
  계속 나와 새로운 물리 가설이 계속 생산된다.

---

### C3 (영향도 3위) — 안전 게이트가 곱이 아니라 인수를 본다

`AGENTS.md:294-298의 공식형은 시나리오 점수 = 생존율 × 추종 점수의 곱이고 종합은
가중합이다. 반면 go2_tuning_eval_report.py:35-36의 게이트는 시나리오별 survival delta
단독으로 판정한다`
→ `G-A017은 총점 +3.7079/70, 7개 시나리오 중 6개의 scenario_proxy 개선, G4조차 proxy
+0.0159 개선이었는데 G4 survival 1.000→0.781 하나로 INTERNAL_EARLY_KILL_FAIL이 됐다.
같은 구조의 이전 세대 규칙(target_scenario)은 A007 +3.87, A009/A011 +3.09, A010 +2.26을
동일하게 죽였다`
→ `G-D79가 track_lin_vel_xy_exp 다이얼을 "완전 기각"했고, 축소 재탐색(1.3, G-A019)도
캠페인 리셋으로 미실행됐다. 6개 항 소진 선언(G-F127)의 마지막 조각이 됐다`
→ `"유일하게 총점을 올린 후보조차 실패"라는 서사가 만들어졌고, 승급선
minimum_weighted_simulation_proxy 0.70을 넘긴 유일한 측정치(0.7171)가 폐기됐다`

- **증거 강도: 높음.** `TIER1_DECISION.json#/scenario_deltas`와 양 arm
  `SELF_EVAL_REPORT.json#/scenarios` 직접 대조.
- **반증 가능 조건:** G-A017 후보를 seed 202·303과 69-case로 재평가했을 때 총점이
  Pilot-01 이하로 떨어지면, 게이트의 거절이 결과적으로 옳았던 것이 된다.
- **영향 A-run:** A007, A009/A011, A010(원), A017.
- **교정하지 않으면:** 공식형 점수를 올리는 후보가 계속 거절되고, 남는 후보는
  "아무것도 안 바꾼 것"뿐이다.

---

### C4 (영향도 4위) — 기준선을 네 번 바꾸면서 control을 한 번도 만들지 않았다

`GO2_REWARD_EVIDENCE_MASTER.md L65·L77-82가 "학습 seed는 42 하나라 독립 학습 재현성은
미확보", "control 생성 전까지 Pilot-01이 개선됐다는 표현 금지"를 명시했다`
→ `G-D69(260903)가 재검토 없이 동결 기준선을 Pilot-01로 바꿨고, G-F132(260905)가 Chain-01로,
G-D92(260905)가 다시 Default-01로 바꿨다. control(무변경 재학습)은 끝내 만들어지지 않았다`
→ `A007·A009/A011·A010은 Default 기준, A013은 Default 기준, A015~A018은 Pilot 기준,
A020~A022는 Chain 기준, A024·A025는 다시 Default 기준으로 실행됐다.
baseline_points_70이 17.54 → 46.49 → 18.61 → 17.13으로 널뛴다`
→ `하나의 실험 시계열처럼 보이는 "12전 12패"가 실제로는 서로 비교 불가능한 4개 계열의
합집합이었다. 계열이 바뀔 때마다 이전 결론(예: feet_air_time 상한 확정)이
새 기준선에서 재현되지 않아 "가장 강한 사전 근거를 가졌던 항조차 붕괴"(G-F138) 같은
과잉 해석이 나왔다`

- **증거 강도: 높음.** 12개 `TIER1_DECISION.json#/baseline_points_70` 실측.
- **반증 가능 조건:** 같은 후보 값(예: `feet_air_time 0.20`)이 세 기준선 위에서
  같은 부호의 delta를 낸다면 기준선 교체는 무해했던 것이 된다. 실측은 반대다 —
  Default 위 `+3.8656`(A007), Chain-01 위 `−13.7275`(A022, 비대칭)/`+0.4491`(대칭 v1).
- **영향 A-run:** A013~A025 전부.
- **교정하지 않으면:** 다음 기준선 교체에서도 이전 지식이 통째로 무효화된다.

---

### C5 (영향도 5위) — 7 case × 1 seed × worst-case 집계로 판정했다

`meta/tier1_registry.json은 required_evaluation_seeds:[101], 시나리오당 internal_cases 1개다.
go2_fixed_eval_report.py:89-92는 시나리오 점수를 case들의 최솟값으로 정의한다.
따라서 tier-1에서 시나리오 점수 = 그 1개 case의 값이다`
→ `한 판정이 7개 rollout 집합에 근거하고, 32개 env의 worst가 아니라 case 단위 단일값이다.
quadruped_rewards.py:120은 배포 원문으로 "같은 설정·같은 seed 라도 cudnn 비결정성으로
매번 조금씩 다릅니다"라고 경고한다`
→ `조기중단 판정이 GPU를 아꼈지만(설계 의도대로), 동시에 seed 202·303 확장이
A015 이후 한 번도 실행되지 않았다. A017이 승급선을 넘겼을 때조차 확장되지 않았다`
→ `단일 표본 판정이 12회 연속 누적되면서, 개별 판정의 불확실성이 사라진 채
"연속 실패"라는 하나의 강한 패턴으로 읽혔다`

- **증거 강도: 중간~높음.** registry·리포터 코드는 확정(높음). 잡음 크기 자체는
  no-op control이 없어 정량화 불가(`[미측정]`).
- **반증 가능 조건:** 무변경 재학습 2~3회의 총점 산포가 ±1.0/70 이내면 단일 seed 판정이
  정당화된다.
- **영향 A-run:** A009/A011 이후 전 학습 실행.
- **교정하지 않으면:** 잡음이 계속 다이얼 기각 근거로 소비된다.

---

### C6 (영향도 6위) — 가중 0.40이 무정보 또는 중복이다

`(a) go2_fixed_eval_report.py:39가 recovery_rate를 읽는데, 이 값은 _keep 전체 push case에서
100% 1.0이다. go2_eval_telemetry.py:286-291이 이 필드를 근거로 쓰지 말라고 주석에 적어 두었고
쓸 수 있는 recovery_rate_upright는 아무도 읽지 않는다. 게다가 push case의 명령 속도는
VX=VY=WZ=0이라 정지한 로봇이 tracking≈1.0을 얻는다.
(b) 69-case runner 3종에 NCRC_EVAL_DR이 없어 dr_seed_*의 steps.csv가 rough_forward와
SHA-256까지 동일하다 — G-A006·G-A012·G-A023 전부`
→ `G6(0.10)은 생존 단독 지표가 되고, G7(0.10)은 G3(0.20)의 복사본이 된다.
69-case 총점에서 가중 0.30이 하나의 험지 rollout 집합에 의존하고, 0.10이 무정보다`
→ `가중 실점 순위표(G-F71: G3 12.97 > G5 10.50 > G4 4.95 > G7 3.61)가 사전등록 규칙의
유일한 출력으로 다음 단일변수를 결정했다(G-D58·G-D70). 즉 중복된 측정이 실험 순서를 정했다`
→ `G3를 겨냥한 실험이 반복되고, G7 결과가 독립 증거처럼 인용됐다`

- **증거 강도: 높음.** SHA-256 대조 9건, push case 100% 포화 전수 확인, runner 소스 직접 확인.
- **반증 가능 조건:** `NCRC_EVAL_DR=1`을 켠 69-case에서 G7이 G3와 다른 점수를 내면
  중복은 해소된다(tier-1에서는 이미 분리 확인됨).
- **영향 A-run:** A006, A007, A012, A023의 69-case 총점 전부; 그 총점을 근거로 선정된
  A013·A015 이후 실험 순서.
- **교정하지 않으면:** 승급 평가(69-case)를 다시 돌려도 30%가 중복, 10%가 무정보인 점수가 나온다.

---

### C7 (영향도 7위) — 비교 checkpoint의 iteration이 서로 다르다

`go2_task/_finalize.py:86이 Train/mean_reward의 argmax로 checkpoint를 고르고 save_interval=100
격자에 스냅한다. 실측 best step은 662~979, 선택된 파일은 model_700~model_999다.
기준선은 Default 800 / Chain-01 900 / Pilot 972(model_999)에 고정돼 있다`
→ `후보마다 학습량이 최대 300 iteration(30%) 다른 상태로 비교됐다. Train/mean_reward는
reward 계수가 다르면 스케일이 다른 목적함수인데(G-D11이 정책 비교 용도로는 금지한 값),
checkpoint 선택에는 계속 쓰였다. H1 캠페인이 PROJECT_STATE.md:606-620(F42)에서 같은 결함을
이미 "잡음의 argmax"로 판정했으나 Go2 계약에는 반영되지 않았다`
→ `가장 나쁜 결과를 낸 G-A024가 가장 이른 checkpoint(step 662 → model_700)로 평가됐다`
→ `"reward 강화 방향이 더 나쁘다"(G-D101)는 결론이 학습량 차이와 분리되지 않은 채 내려졌다`

- **증거 강도: 중간.** 선택 로그·checkpoint 파일명은 확정(높음). 300 iteration 차이가
  점수에 미치는 크기는 `[미측정]`.
- **반증 가능 조건:** 동일 run의 `model_700`과 `model_999`를 같은 7 case로 채점해
  총점 차이가 1.0/70 미만이면 무해하다.
- **영향 A-run:** 전 학습 실행, 특히 A024(662), A007(829), A017(856), A010(864).
- **교정하지 않으면:** reward 효과와 학습량 효과가 계속 섞인다.

---

### 4-1. 세 범주로의 분해

| 범주 | 해당 사슬 | 이번 캠페인 실패에서의 몫(감사 판단) |
|---|---|---|
| **실제 정책 성능 실패** | C1(기준선 퇴화는 실제 정책 상태이기도 하다) | 6건의 후보 붕괴는 진짜다: A015·A016·A018(대칭 확인), A020·A022·A024(절대 자세 미달) |
| **측정·평가기 실패** | C2, C5, C6, C7 | 판정 무효 4건 + 모든 69-case 총점의 가중 0.30 중복 + 0.10 무정보 |
| **캠페인 운영·의사결정 실패** | C1(기준선 승격 결정), C3, C4 | 유효 측정 4건을 잘못 처리(A007·A009/A011·A010원·A017), 기준선 4회 교체, control 0건, 영상 게이트 미작동 |

**어느 하나로 환원되지 않는다.** reward 값 문제로 확정된 것은 4건(§3-3 Q5)뿐이며,
그중 1건(A017)은 **이로운 방향**이다.

---
## 5. 독립 개선 계획 (§5.5) — 사전등록 형식

**원칙:** 새 학습을 기본값으로 두지 않는다. 순서는 **정보가치 ÷ GPU 비용**이다.
S1~S3는 GPU 0분, S4는 학습 0분, S5부터 학습이 있다.
각 단계는 **직전 단계의 성공 기준을 만족해야** 시작한다.

> **GPU 예산 전제.** 원자료가 기록한 마지막 잔여값은 `GO2_CAMPAIGN_SCHEDULE.md:228`의
> "잔여 25시간"(260903)과 같은 문서 L243·L277의 "캠페인이 이미 5.81시간을 썼다"뿐이다.
> `SERVER_SESSION_RUNBOOK.md:115,1268`은 이후에도 "예산 25시간의 4.4%"를 반복 인용하며
> **차감 갱신을 하지 않았다** — `AGENTS.md:353` R-5가 요구한 예산 원장 갱신 미이행.
> 따라서 **현재 잔여 GPU 시간은 `[미확인]`**이다. 아래 시간 추정은 실측 단가
> (1,000 iter 학습 `00:59:11` = `G-F80`; tier-1 7 case 약 300초 = `_keep` summary
> `wall_seconds` 합계; 69-case×3seed 약 1,360~1,391초 = A012·A023 실측)로만 적었다.

---

### S1 — evaluator 계약·지문 고정 (GPU 0분)

- **목적과 직접 측정 G1~G7:** 없음(계측 자체를 고정). 산출은 코드·테스트.
- **입력 policy/checkpoint 식별자:** 없음. 대상은
  `workspace/training/quadruped/go2_fixed_eval_report.py`,
  `go2_tuning_eval_report.py`, `tools/build_go2_tuning_engine.py`,
  `tools/test_go2_tuning_engine_contract.py`.
- **변경값:**
  1. `build_policy()`가 각 case `summary.json`의 `schema_version`·`survival_proxy_source`·
     `posture_gate`(4개 파라미터)를 수집하고 리포트에 `evaluator_fingerprint`로 기록.
  2. `tier1_decision()`이 두 arm의 fingerprint가 다르면 점수를 계산하지 않고
     `EVALUATOR_MISMATCH`를 반환.
  3. `TRACKING_STD`를 `registry.score.env_track_std_path`로부터 env.yaml에서 읽고,
     읽지 못하면 실패(현재 하드코딩 `0.5`는 기본값으로만 유지).
  4. `_case_proxy`의 push 분기가 `recovery_rate` 대신 `recovery_rate_upright`를 읽는다
     (`recovery_rate`는 정보용으로만 보고).
  5. `_default_baseline_payload()`/`_chain01_baseline_payload()`가 v1 세대 `summary.json`을
     복사하면 **빌드가 실패**한다.
- **고정값:** registry 가중치, 시나리오 정의, case 격자, seed 집합.
- **seed·반복:** 해당 없음.
- **성공:** 계약 테스트가 16 → 21건 이상으로 늘고 전부 통과. 신규 테스트에
  (a) 두 arm 지문 일치 강제, (b) v1 캐시 감지 시 빌드 실패, (c) `recovery_rate_upright` 사용,
  (d) TRACKING_STD 출처 검증, (e) `EVALUATOR_MISMATCH` 반환 경로가 포함될 것.
- **실패:** 위 5개 중 하나라도 구현 불가 → 원인을 기록하고 S2로 넘어가지 않는다.
- **`INCONCLUSIVE`:** 없음(결정적 테스트).
- **GPU 시간:** 0분. 조기중단점 없음.
- **필수 artifact:** 수정 diff, `python -m unittest discover -s tools` 전체 출력,
  새 엔진 ZIP SHA-256.
- **성공 시 분기:** S2. **실패 시 fallback:** 최소한 (a)+(b)만이라도 넣고 나머지는 보류.

---

### S2 — G1~G7 회귀 테스트 (GPU 0분)

- **목적:** 점수식·집계·시나리오 정의가 규정 요약(`AGENTS.md` R-2·R-3)과 일치하는지
  **기존 telemetry만으로** 검증. 직접 측정 대상 G1~G7 전부.
- **입력:** `workspace/_keep/go2_pilot_v2_baseline/evaluation/pilot_v2/`(69 case, v2),
  `workspace/_keep/go2_chain01_baseline/evaluation/chain01/`(69 case, v2),
  `workspace/_keep/go2_default_vs_pilot_v1/evaluation/{default,pilot}/`(69 case, v1).
- **변경값:** 없음(읽기 전용 검증). **고정값:** 전부.
- **검사 항목과 판정선:**
  1. **G3/G7 독립성** — 같은 seed의 `rough_forward`와 `dr_seed_*`의 `steps.csv` SHA-256이
     다를 것. **현재 3개 스위트 전부 동일 → 현 상태 FAIL이 예상되며, 이것이 S3의 입력이다.**
  2. **posture gate 산술** — `steps.csv`의 `proj_grav_z`·`height_rel`로 `fallen_env_count`를
     재계산해 `summary.json`과 일치할 것(허용 오차 0).
  3. **G6 recovery** — `recovery_rate`가 전 case 1.0임을 회귀 테스트로 고정(현상 기록),
     `recovery_rate_upright`가 정책별로 분산을 가질 것.
  4. **집계** — worst-case와 평균 두 방식을 모두 산출하고 리포트에 병기.
  5. **가중치** — registry 7개 가중 합 = 1.00, `AGENTS.md:390-397` 표와 일치.
  6. **std** — `env.yaml`의 `track_lin_vel_xy_exp.params.std`가 0.5임을 3개 정책에서 확인.
- **seed·반복:** 기존 101/202/303 데이터 전량, 재실행 없음.
- **성공:** 2·4·5·6 통과 + 1·3의 현 상태가 테스트로 고정됨.
- **실패:** 2가 불일치하면 posture 게이트 구현 자체를 신뢰할 수 없다 → S4 이후 전면 보류.
- **`INCONCLUSIVE`:** `steps.csv`에 필요한 열이 없어 재계산 불가한 case가 있으면 그 case만.
- **GPU 시간:** 0분.
- **필수 artifact:** 회귀 테스트 파일, 실행 로그, 두 집계 방식 병기 리포트.
- **성공 시:** S3. **실패 시:** posture 산술 결함 수정 후 S2 재실행.

---

### S3 — 69-case runner의 G7 DR 결함 수정 (GPU 0분, 서버 실행은 S4에 합류)

- **목적:** G7(가중 0.10)을 G3(0.20)와 분리해 **가중 0.30의 이중 계상**을 제거.
  직접 측정: G3, G7.
- **입력:** `server_run_go2_chain01_baseline.sh:140-146`(및 `pilot_v2`·`default_vs_pilot` 동형).
- **변경값:** `dr_seed_*` 분기를 `rough_*`에서 떼어 내고
  `NCRC_EVAL_DR=1`을 주입(`server_run_go2_tuning_engine_v1.sh:226,229`와 동일 방식).
- **고정값:** G3 case 정의, 지형 파라미터, 명령값.
- **seed·반복:** 해당 없음(코드 수정).
- **성공:** 새 runner의 `bash -n` 통과 + CRLF 0 + `NCRC_EVAL_DR` 주입 경로가 정적으로 확인됨.
  S4 실행 후 `dr_seed_101`과 `rough_forward`의 `steps.csv` SHA가 **달라야** 최종 성공.
- **실패:** 주입 후에도 SHA가 같으면 `env_cfg.py:134-147`의 DR 분기가 동작하지 않는 것 →
  `metadata.json#/realized_randomization_values`를 대조해 원인 특정.
- **GPU 시간:** 0분(코드). S4에 흡수.
- **필수 artifact:** runner diff, `bash -n` 로그.
- **성공 시:** S4. **실패 시:** G7 점수를 **가중에서 제외**하고 나머지 0.90을 정규화한
  보조 지표를 병기(중복 계상을 하지 않는 쪽이 낫다).

---

### S4 — 기존 baseline/candidate를 **같은 evaluator로** 재판정 (학습 0분, 평가만)

이 단계가 캠페인 전체에서 빠져 있는 단 하나의 숫자를 만든다.

- **목적:** ① Default-01의 `survival_proxy_v2` 실측, ② A017 후보의 다중 seed 검증.
  직접 측정: G1~G7 전부.
- **입력 policy/checkpoint 식별자 (전부 로컬 보존 확인됨):**
  - **P1 = Default-01** `model_sha256 = 99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`
    (`workspace/_keep/go2_default_vs_pilot_v1/evaluation/default/policy.pt`)
  - **P2 = G-A017 후보** `model_best.pt SHA = 0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4`
    (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/training/model_best.pt`, `model_900.pt`와 동일)
  - **P3 = Pilot-01(대조 재현)** `c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d`
- **변경값:** 없음 — **reward도 학습도 바꾸지 않는다.** evaluator만 S1~S3판으로 고정.
- **고정값:** 69-case 격자, 평가 seed 101/202/303, `EVAL_STEPS`, num_envs 32,
  `posture_gate_v2` 파라미터(0.5 / 0.18 / 0.5 / 0.5).
- **seed와 반복 수:** 평가 seed 3개 × 69 case × 정책 3개. 학습 seed 반복 없음(학습 없음).
- **성공 기준:**
  - P1이 v2로 채점돼 `survival_proxy_v2`가 69/69 case에 존재 → 이 자체가 S4의 1차 성공.
  - 두 arm 지문이 동일하다는 `evaluator_fingerprint` 일치가 리포트에 기록됨.
  - P2의 3-seed 69-case 총점이 P3(Pilot-01 v2 `33.793106/70`)보다 **높으면** P2를
    `INTERNAL_REPRESENTATIVE_PROMOTION` 후보로 승급.
- **실패 기준:** P2 총점이 P3 이하이거나, 어떤 시나리오의 3 seed 중 하나라도
  `survival_proxy_v2 = 0` → P2 기각, S5로 직행.
- **`INCONCLUSIVE`:** seed 간 총점 산포가 3.0/70을 넘으면 판정 보류하고 seed를 2개 추가.
- **예상 GPU 시간:** 정책당 69-case 약 23~25분(A012 `1,391초`·A023 `1,360초` 실측) →
  3정책 약 **1.2~1.5시간**, 영상 7편×3 포함 시 **약 1.5~1.8시간**.
  **조기중단점:** P1의 seed 101 7-case 직후. 여기서 P1의 `survival_proxy_v2`가
  Chain-01처럼 6/7 시나리오 0이면 나머지 seed를 돌리지 않고 즉시 회수한다
  (그 사실만으로 C1·C2가 확정되고 기준선 정책이 바뀐다).
- **필수 artifact·telemetry·영상·다운로드:**
  `SELF_EVAL_REPORT.json`(3정책) + case별 `summary.json`·`steps.csv` 전량 +
  `evaluator_fingerprint` + 시나리오당 1편 영상 21편 + `POLICY_LINEAGE.json` +
  `SHA256SUMS.txt` + 단일 결과 ZIP과 `.sha256`.
- **성공 시 분기:** P2가 P3보다 높으면 **P2를 새 동결 기준선**으로 삼고 S6(승급 학습)로.
  P1이 v2에서 붕괴로 확인되면 **Default-01을 기준선에서 영구 제외**하고 A010재·A013·A020·
  A021·A022·A024·A025의 delta를 **재계산 없이 `UNDETERMINED`로 확정 폐기**.
- **실패 시 fallback:** P2·P3 모두 승급 불가면 S5로 가서 잡음 하한부터 잰다.

---

### S5 — 무변경(no-op) 재학습으로 PPO/checkpoint 분산 추정

- **목적:** "reward를 안 바꿔도 1,000-iter from-scratch 재학습이 이만큼 흔들리는가"를
  분리 측정. 직접 측정: G1~G7 tier-1 7 case.
- **입력:** S4에서 확정된 동결 기준선(P2 또는 P3)의 **reward 6개 값 그대로**.
  checkpoint는 입력이 아니라 산출(from scratch).
- **변경값: 없음(0개).** 이것이 실험의 요점이다.
- **고정값:** reward 6항, 4096 env, 1,000 iter, evaluator, case, 평가 seed 101.
- **seed와 반복 수:** **학습 seed 43, 44 두 번**(기존 42와 합쳐 3점).
  평가 seed는 101 고정(잡음 원인을 학습 쪽으로 한정하기 위해).
- **성공 기준:** 세 학습 seed의 tier-1 총점 표준편차가 **1.0/70 미만** →
  기존 단일-seed 판정이 정당화되고, |delta| > 3.0/70만 신호로 인정한다.
- **실패 기준:** 표준편차 **3.0/70 이상** → **1,000-iter 단일 seed 스크리닝을 폐기**하고
  screening을 3,000 iter(배포 파일 권장, `quadruped_rewards.py:113,119`)로 올리거나
  seed 2개 이상을 필수화한다.
- **`INCONCLUSIVE`:** 표준편차 1.0~3.0/70 → 판정선을 그 값의 3배로 재설정하고 기록.
- **예상 GPU 시간:** 학습 2회 × `00:59:11` + tier-1 평가 2회 × 5분 ≈ **2.1시간**.
  **조기중단점:** 첫 재학습의 `forward_fast` 속도가 기준선의 50% 미만이면 두 번째를 돌리기
  전에 중단하고 원인(커리큘럼·초기화)을 먼저 본다.
- **필수 artifact:** 2개 `model_best.pt`와 그 `best step`, tfevents,
  tier-1 `SELF_EVAL_REPORT.json` 2건, `TIER1_DECISION.json` 2건, G1 영상 2편.
- **성공 시 분기:** S6. **실패 시 fallback:** S6의 screening 길이를 3,000 iter로 상향하고
  단일변수 후보 수를 절반으로 줄인다(예산 보존).

---

### S6 — 그 뒤에만: 단일변수 3,000 → 5,000 iteration 승급 결정

- **목적:** S4에서 살아남은 방향(현재 자료상 유일한 후보는 `track_lin_vel_xy_exp` 상향)을
  **충분한 학습 길이**에서 확인. 직접 측정: G1~G7 전부(대표 21 case → 69 case).
- **입력 policy/checkpoint:** S4 확정 기준선(P2 우선). 후보는 그 reward에서 1개 항 변경.
- **변경값:** 1개. **고정값:** 나머지 5개 항, seed, env 수, evaluator, case, 집계 방식.
- **seed와 반복 수:** 학습 seed 42 + S5에서 잡음이 컸다면 43 추가.
  평가 seed 101 → (통과 시) 101/202/303.
- **성공 기준 (사전 확정, 결과를 본 뒤 바꾸지 않는다):**
  1. **1차 게이트는 가중 총점 delta ≥ +1.0/70** (공식형 목적함수와 같은 방향).
  2. **안전 게이트는 인수가 아니라 시나리오 점수로 판정한다** — 어떤 시나리오의
     `scenario_proxy` delta가 **−0.03 미만**이면 실패. `survival` 단독 후퇴는 **경고로만** 기록.
     (근거: `AGENTS.md:294-298`은 곱을 채점한다. G-A017형 오거절 방지.)
  3. **절대 하한:** 모든 case의 `height_rel_median ≥ 0.18`, `forward_fast` 속도 ≥ 명령의 60%.
     기준선과 무관한 실격선이다.
  4. 두 arm의 `evaluator_fingerprint` 일치(S1이 강제).
- **실패 기준:** 1 또는 3 위반. **`INCONCLUSIVE`:** 1 통과·2 위반 → 대표평가 3 seed로 확장해
  재판정(기각하지 않는다).
- **예상 GPU 시간:** 3,000 iter ≈ `3.48초/iter × 3,000` ≈ **2.9시간**(G-F80 단가),
  tier-1 5분 + 대표평가 21 case 약 10분 → 후보 1건당 **약 3.2시간**.
  5,000 iter 승급 시 추가 **약 1.9시간**.
  **조기중단점:** iter 500에서 `Train/track_lin_vel_xy_exp`가 기준선 곡선의 50% 미만이면
  중단(G-A016의 iter 150 고착 서명 재발 방지).
- **필수 artifact:** 학습 로그·tfevents·`model_best.pt`와 best step·`reward_only.diff`·
  `env.yaml`·tier-1/대표 `SELF_EVAL_REPORT.json`·`TIER1_DECISION.json`·
  시나리오별 영상 7편(**`VIDEO_OBSERVED` 판독 기록 포함, 이번에는 실제로 본다**)·
  `POLICY_LINEAGE.json`·`SHA256SUMS.txt`·단일 ZIP과 `.sha256`.
- **성공 시 분기:** 5,000 iter 승급 → 69-case×3seed → 제출 후보.
  **실패 시 fallback:** 기준선을 그대로 두고 **제출 가능한 최고 정책을 제출하는 것**을
  다음 행동으로 삼는다(`AGENTS.md:283-286` R-1 파생 규칙: 미제출 정책은 0점).

---

### 5-1. 이 순서를 쓰는 이유 (비용 대비 정보가치)

| 단계 | GPU | 얻는 것 | 이것이 없으면 |
|---|---:|---|---|
| S1 | 0분 | 판정의 대칭성 보증 | 신규 실험 6건이 또 비대칭으로 채점 |
| S2 | 0분 | 점수식 산술 신뢰 | 자세 게이트 자체를 못 믿음 |
| S3 | 0분 | 가중 0.10 회복 | 69-case 총점의 30%가 계속 중복 |
| **S4** | **1.5~1.8h** | **Default-01의 v2값 + A017의 3-seed 검증 = 무효 판정 7건의 재판정 근거** | 캠페인 전체가 판정 불능 상태로 유지 |
| S5 | 2.1h | 잡음 하한 = 판정선의 근거 | 모든 delta가 "신호인지 잡음인지" 미결 |
| S6 | 3.2h/후보 | 실제 승급 후보 | — |

**S4를 S5·S6보다 앞에 두는 이유:** S5의 no-op control도, S6의 새 후보도
**같은 비대칭 게이트로 채점되면 똑같이 무효**다. 계측을 먼저 닫지 않은 학습은
GPU를 쓰고 판정 불능 결과를 하나 더 만든다 — 이미 7건 그랬다.

---
## 6. 확인 불가능했던 항목 — `[미확인]` / `[미측정]`

| # | 항목 | 표기 | 사유 |
|---:|---|---|---|
| 1 | 공식 evaluator 코드·파라미터 | `[미확인]` | 로컬에 없음. registry `official_unknowns`(`:27-35`)가 tracking 변환식·평가 seed·에피소드 수·명령 격자·험지 생성 파라미터·push 크기/방향/시각·DR 필드·공식 통과선 8개를 스스로 미상으로 선언 |
| 2 | Go2 `OFFICIAL_RESULT` | `[미측정]` | 공식 채점 결과 파일 0건 |
| 3 | Go2 제출 여부·접수 증거 | `[미측정]` | 대시보드 행위 증거 없음(`GO2_PROJECT_STATE.md` 서문) |
| 4 | H1 제출 여부 | `[미측정]` | `H1_REWARD_EVIDENCE_MASTER.md:373-376`이 스스로 최우선 미해결로 표기 |
| 5 | 예선 규정집 원문 | `[미확인: 파일 부재]` | `find . -iname "*규정*"` 0건. `AGENTS.md`의 요약(R-1~R-7)만 존재 |
| 6 | **현재 잔여 GPU 시간** | `[미확인]` | 마지막 raw 기록은 `GO2_CAMPAIGN_SCHEDULE.md:228`의 "잔여 25시간"(260903)과 L243·L277의 "이미 5.81시간 소비". 이후 `SERVER_SESSION_RUNBOOK.md:115,1268`이 계속 "25시간의 4.4%"를 인용하며 차감하지 않음. `AGENTS.md:353` R-5의 예산 원장 갱신 미이행 |
| 7 | Default-01의 `survival_proxy_v2` | `[미측정]` | 69 case 전부 `schema_version:1`. 기준선 캐시에 `steps.csv`가 없어 로컬 재채점 불가(`evaluation/baseline_tier1/cases/seed_101/forward_fast/` 파일 목록 확인) |
| 8 | A010(재)·A013/A025·A021의 참 delta | `[미측정]` | 두 arm이 같은 세대로 채점된 적 없음. S4 후에만 계산 가능 |
| 9 | 1,000-iter 재학습의 잡음 하한 | `[미측정]` | no-op control 0건. S5의 대상 |
| 10 | checkpoint 300 iteration 차이의 점수 효과 | `[미측정]` | 같은 run의 두 checkpoint를 같은 case로 채점한 자료 없음 |
| 11 | A015~A025 후보의 영상 관찰 | `VIDEO_UNKNOWN` | MP4는 있으나 판독 기록 0건. 실패 메커니즘 진단이 telemetry 단일 소스 |
| 12 | height_scanner 부재 시 posture gate 거동 | `INTERNAL_GATE_INCONCLUSIVE` | 코드상 기울기 전용으로 퇴화하면서 라벨은 `posture_gate_v2` 유지(`go2_eval_telemetry.py:239-241`). `_keep`에서는 발현 사례 미발견 |
| 13 | 서버 세션 총 과금 시간 | `[미측정]` | `G-F27`이 이미 그렇게 기록. 이후 갱신 없음 |
| 14 | Pilot-01 4항 조합 각 항의 개별 기여 | `[미확인]` | `G-D02` 그대로. 4항 동시변경 |
| 15 | worst-case 집계가 순위를 뒤집는지 | `INTERNAL_GATE_INCONCLUSIVE` | 측정된 5개 69-case 정책에서는 순위 보존(§1-10). 다른 정책군에서는 미확인 |

---

## 7. 품질 게이트 자체 점검 (§8)

- [x] **A006~A025가 모두 한 번씩 등장하며 미실행·중복은 별도 분류됐다.**
      §2-2에 20개 ID가 각 1행. 미실행 3건(A011(a), A014, A019), 중복 2건(A025=A013,
      A011(b) 라벨), 인프라 1건(A008)을 `실패 분류` 열에 명시.
- [x] **모든 핵심 결론에 파일 경로와 줄 번호 또는 JSON pointer가 있다.**
      코드 결함은 `파일:줄`, 실행 결과는 `_keep/<run>/reports/TIER1_DECISION.json#/필드`
      또는 `evaluation/<arm>/SELF_EVAL_REPORT.json#/scenarios/<G>`로 지시.
- [x] **H1 성공을 공식 결과로 과장하지 않았다.**
      §3 서두에 H1의 `92.73/100`이 내부 proxy이고 제출 여부가 `[미측정]`임을 명시.
      §3-3 Q4에서 H1 evaluator의 종료-전용 지표와 가중 0.30 `POSTURE_UNMEASURED`를 기록.
- [x] **Go2 연속 실패를 reward 실패 하나로 환원하지 않았다.**
      7개 인과사슬 중 reward 값 자체가 원인인 것은 §3-3 Q5의 4건뿐이고, 그중 1건(A017)은
      이로운 방향이다.
- [x] **같은 evaluator 비교와 다른 evaluator 비교를 섞지 않았다.**
      §3-2에 실행별 지문 표를 두고, 대칭 v1 재채점 값은 "채택 근거가 아님"을 명시.
      §2-2의 `판정 유효성` 열이 행마다 대칭/비대칭을 표기.
- [x] **절대 proxy 개선과 안전 gate 실패를 동시에 기록했다.**
      §2-4에 4건(A007 +3.87, A009/A011 +3.09, A010원 +2.26, A017 +3.71)을 발화 gate와 함께 기록.
- [x] **실제 정책 붕괴 사례도 계측 문제 뒤에 숨기지 않았다.**
      §2-5에서 A015·A016·A018을 대칭 v2·v1 양쪽 음수로 확정하고,
      A020·A022·A024를 기준선과 무관한 절대 자세 지표로 실격 처리했다.
      §4-1에서 "6건의 후보 붕괴는 진짜다"라고 명시.
- [x] **공식 결과가 없는 항목은 `[미측정]`이다.** §6 표.
- [x] **개선 계획이 evaluator 복구·기존 artifact 재판정을 새 GPU 학습보다 앞세운다.**
      S1~S3는 GPU 0분, S4는 학습 0분. 새 학습은 S5부터.
- [x] **기존 Opus 문서의 폐기된 계획과 최신 계획을 혼동하지 않았다.**
      Phase I에서 두 감사 문서를 읽지 않았으므로 인용 자체가 없다.
- [x] **최종 문서와 SHA256 파일이 실제로 생성됐다.**
      `GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` / `.sha256`.

### 7-1. 원장·코드를 수정하지 않았음

본 감사는 **읽기 전용**으로 수행했다. `GO2_PROJECT_STATE.md`,
`GO2_CAMPAIGN_SCHEDULE.md`, `GO2_REWARD_EVIDENCE_MASTER.md`, `AGENTS.md`,
`workspace/training/**`, `tools/**`를 하나도 수정하지 않았다.
재계산은 전부 스크래치패드의 임시 스크립트에서 `go2_fixed_eval_report`를 **import**해
수행했으며, 원본 모듈을 변경하지 않았다(런타임에 `_case_proxy`만 치환하고 즉시 복원).
생성한 파일은 본 문서와 그 `.sha256` **2개뿐**이다.

---

## 8. 한 줄 요약

> Go2의 "연속 실패"는 하나의 사건이 아니라 **네 개의 서로 비교 불가능한 실험 계열**이며,
> 그중 절반은 **걷지 못하는 기준선 위에서 잰 바닥 잡음**이었고, 여섯 건은 **후보와 기준선을
> 서로 다른 자로 잰 무효 판정**이었으며, 진짜 정책 붕괴는 여섯 건, 그리고
> **총점을 올린 네 건은 공식형 목적함수가 아니라 인수 단독 게이트에 걸려 죽었다.**
> 지금 필요한 것은 다음 reward가 아니라, **Default-01을 `posture_gate_v2`로 한 번 재는 것**과
> **G-A017 후보를 3 seed로 다시 재는 것**이다. 둘 다 학습이 없다.

---

**본 문서는 Phase I 산출물이다. `GO2_DESIGN_REVIEW_260907.md`와
`GO2_INDEPENDENT_AUDIT_CODEX_260907.md`는 이 시점까지 열람하지 않았다.**
