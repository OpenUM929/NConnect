# Go2 A006~A025 독립 감사 보고서 (Codex)

- 작성일: 2026-09-07 (Asia/Seoul)
- 독립 감사 범위: `G-A006`~`G-A025`, 채점 코드, 실험 JSON, 실행 artifact, 강좌, 지침·서브에이전트
- 독립성 통제: 본 문서의 §0~§4를 작성·고정할 때까지 `GO2_DESIGN_REVIEW_260907.md`의 본문을 열거나 검색하지 않았다. 해당 파일은 §5 비교 단계에서만 최초 열람한다.
- 증거 강도: **A1** 원시 JSON/CSV/코드 직접 대조, **A2** 서로 독립인 복수 artifact 교차검증, **B** 원장·보고서와 원자료 일치, **C** 출처 원문 부재 또는 추론
- 판정 용어: `ARTIFACT_VERIFIED`, `INTERNAL_*`, `OFFICIAL_RESULT_UNMEASURED`를 구분한다. 이 감사의 점수는 공식 점수가 아니다 (`AGENTS.md:288-301`; `workspace/PRELIM_RL_GUID.md:92-104`).

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 proxy 70점의 측정 타당성, 설계 의도 20점의 실험 정당성, 리포트 품질 10점의 근거 완결성을 감사한다 (`AGENTS.md:272-280`).
- [현재 단계] **단계 0/6 — 증거·artifact 정합성**. 다음 행동을 막는 가장 이른 공백은 Default-01의 `posture_gate_v2` 기준선 부재와 비교 arm evaluator 비대칭이다 (`workspace/_keep/go2_g_a025_flat_orientation_m1/evaluation/baseline_tier1/cases/seed_101/rough_forward/summary.json#schema_version`; 같은 실행 candidate summary의 `survival_proxy_source`).
- [확보] A006~A025 artifact 위치, 실행/미실행 구분, 공식형 곱셈 코드, v1/v2 survival 필드, A015~A018의 대칭 비교를 확인했다 (세부 표 §3).
- [미확보] Default-01 v2 기준선, 독립적인 G7 DR rollout, 공식 evaluator의 tracking 변환·명령·push·DR, 정확한 잔여 서버 시간은 미확인이다 (`config/go2_self_eval_registry.json:27-35`; `GO2_CAMPAIGN_SCHEDULE.md:227-228`).
- [이번 테스트] A025까지의 실험 설계와 판정이 동일 evaluator·동일 공식형 목적함수로 비교됐는지 판정한다.
- [흐름] A006~A025 회수 → **독립 감사** → 계측 대칭성 복구 → 유효 후보 재판정 → 최종 제출
- [지금 할 일] **새 학습을 실행하지 않는다.** 먼저 Default-01을 학습 없이 `posture_gate_v2`로 재평가하는 G-A026을 준비·실행해야 한다 (§4).
- [보장하지 않음] 내부 proxy, 단일 seed, 단일 rollout, 평균 reward는 공식 점수·예선 통과를 보장하지 않는다 (`workspace/training/quadruped/AGENTS.md:63-74`).

## 1. 요약

1. **[A1, 확정] 산술 계층은 공식형 곱셈 구조를 재현한다.** case 점수는 `survival * tracking`, 시나리오 가중합은 `sum(weight * scenario_proxy)`, 70점 환산은 `70 * fraction`이다 (`workspace/training/quadruped/go2_fixed_eval_report.py:19-20,23-47,114-142`; `workspace/PRELIM_RL_GUID.md:92-102`). 단 tracking 변환 `exp(-(RMSE/0.5)^2)`, worst-case 집계, 내부 threshold는 공식 세부식이 아니라 내부 설계다 (`config/go2_self_eval_registry.json:27-50`).
2. **[A1, 확정] 비교 파이프라인의 핵심 결함은 arm evaluator 비대칭이다.** G-A010 재측정, A013, A020~A022, A024, A025는 candidate가 `posture_gate_v2`인데 baseline 7개 중 6개가 `termination_only_v1` 캐시다. runner가 오래된 `baseline_seed`를 복사하고 candidate만 새 evaluator로 계산한다 (`server_run_go2_tuning_engine_v1.sh:334-350`; `tools/build_go2_tuning_engine.py:58-60,77-114`). 따라서 이 실행들의 delta·survival-regression 판정은 `EVALUATOR_MISMATCH / UNDETERMINED`다.
3. **[A1, 확정] 비대칭은 결론의 부호를 실제로 뒤집었다.** 보고 delta→양 arm v1 재계산 delta는 A010 `-7.632522→+2.257160`, A013/A025 `-1.427788→+3.654378`, A020 `-18.182232→-0.221130`, A021 `-6.607936→-0.351602`, A022 `-13.727549→+0.449132`, A024 `-17.132070→+3.461676`이다 (각 실행 `evaluation/{baseline_tier1,candidate}/SELF_EVAL_REPORT.json#/cases/*/raw/survival_proxy_v1` 및 `#/scenarios/*/tracking_proxy`; 교차확인 `GO2_PROJECT_STATE.md:647-650`). v1 재계산은 후보 채택 근거가 아니라, 기존 음수 delta가 같은 자의 비교가 아니었음을 증명한다.
4. **[A1, 확정] G-A017은 내부 veto가 공식형 총점 신호를 뒤집은 대표 사례다.** 총점은 `46.491241→50.199157`(`+3.707916/70`)이고 G4 scenario product도 `+0.015871`이지만, G4 survival delta `-0.21875` 하나가 `max_survival_regression=0.1`을 넘어 `INTERNAL_EARLY_KILL_FAIL`이 됐다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json#/candidate_minus_baseline_points_70,#/scenario_deltas/G4,#/failure_reasons`). 이는 **공식식 FAIL이 아니라 내부 위험정책 veto**다. 다만 절대점수 `50.199<60`, 단일 평가 seed이므로 대표 승급은 여전히 불가하다 (`go2_tuning_eval_report.py:61-85`).
5. **[A2, 확정] A025는 A013의 중복 실행이며 정보이득이 0이다.** 두 candidate model SHA가 `676cc1cb...b12e1c`, 총점·delta·7 scenario delta가 동일하다. A013 candidate는 이미 schema 2/v2였으므로 “v1 후보 재측정” 전제가 틀렸다 (두 실행 `RUNNER_STATUS.txt#CANDIDATE_MODEL_SHA`, `reports/TIER1_DECISION.json`; `GO2_PROJECT_STATE.md:627-641`).
6. **[A1, 확정] full-suite의 G7이 G3와 독립적이지 않다.** A006, A007, A012, A023에서 같은 seed의 `G3/rough_forward/steps.csv`와 `G7/dr_seed_<seed>/steps.csv` SHA-256이 동일하다. full runner는 `rough_forward|rough_lateral|dr_seed_*`를 같은 terrain/command 분기로 처리한다 (`server_run_go2_pilot_v2_baseline.sh:120-140`; `server_run_go2_chain01_baseline.sh:126-145`). 따라서 69개 파일은 69개 독립 조건이 아니며 G7 점수 근거는 무효다.

## 2. 채점 체계 진단

### 2.1 로컬 규정 출처와 강좌의 역할

- 저장소에서 직접 확인되는 채점 정의는 `workspace/PRELIM_RL_GUID.md:60-70,92-104`의 G1~G7 가중치와 `survival_rate × tracking_score`다. 규정집 PDF·공지 원문·URL snapshot은 저장소에서 식별되지 않아, 이 Markdown이 실제 운영진 원문과 동일한지는 **미확인[C]**이다.
- `test/` 강좌 전수 검색에서는 `survival_rate`, `tracking_score`, `70점`, `생존율`, `추종 점수`, Go2 시나리오 G3~G7, schema/실험 명세 정의가 0건이었다. 강좌가 직접 지지하는 것은 reward 의미 (`test/14강의. 보상 함수 설계와 조정 · 진화 · NAVER CONNECT ROBOTICS GUIDE BOOK.html:659-674`), 한 번에 하나씩 (`:708-715,738-739`), 1,000 iter 예시와 영상 비교 (`:946-967,971-990`)다.
- 따라서 `config/go2_self_eval_registry.json:12-16`의 `course_or_guide_direct`는 출처가 뭉쳐 있다. G1~G7/terrain/weights는 **guide direct**, single-variable guidance만 **course direct**로 분리해야 한다 (`config/...registry.json:5-16`; `workspace/PRELIM_RL_GUID.md:60-70`).

### 2.2 산술 구현: 곱셈은 맞지만 공식 evaluator 재현은 아니다

- `go2_fixed_eval_report.py`는 RMSE를 `exp(-(RMSE/0.5)^2)`로 변환하고 (`:12,19-20`), case proxy를 `survival * tracking`으로 계산한다 (`:23-47`). scenario는 case/seed 중 최소 proxy를 취해 가중합하고 70을 곱한다 (`:83-100,114-142`). 공식 공개형 `Σ(weight × survival × tracking)`과 대수 구조는 일치한다 (`workspace/PRELIM_RL_GUID.md:92-102`).
- 하지만 정확한 tracking 변환, seed·episode 수, command grid, terrain, push, DR, 공식 통과선은 미공개로 등록돼 있다 (`config/go2_self_eval_registry.json:27-35`). worst-case case/seed 집계도 내부 설계다 (`:18-25,48-50`). 따라서 산출값은 `simulation proxy /70`이지 공식 점수가 아니다.
- registry는 env의 tracking std를 읽는다고 명세한다 (`config/go2_self_eval_registry.json:37-40`), 실제 reporter는 `TRACKING_STD=0.5`를 하드코딩한다 (`go2_fixed_eval_report.py:12,19-20`). 현재 A025 env도 `std: 0.5`라 현 수치 차이는 없지만 (`workspace/_keep/go2_g_a025_flat_orientation_m1/training/env.yaml:822-832`), 구현과 스펙의 provenance가 불일치한다.

### 2.3 생존 판정: v1은 부적합, v2도 계약을 완전히 강제하지 않는다

- v1은 `1 - terminated_envs/num_envs`뿐이다 (`go2_hotfix_verify/go2_default_vs_pilot_v1/default/go2_eval_telemetry.py:216-227`). 이는 “넘어지지 않고 완주”가 아니라 “termination event 없음”이므로 내부 규정과 불일치한다 (`AGENTS.md:288-301`).
- v2는 projected gravity와 base-to-ground height를 수집하고 0.5초 연속 비정상 자세를 낙상으로 센다 (`go2_eval_telemetry.py:77-86,176-194,233-260,348-384`). 이 방향은 v1보다 타당하다.
- 그러나 코드 주석은 두 채널을 요구한다고 쓰지만 (`:79-82`), 실제 `measured = gravity_finite OR height_available`, `height_ok = True` when height missing이다 (`:235-243`). 둘 다 없으면 `termination_only_v1`으로 자동 fallback한다 (`:349-377`). 상위 계약은 두 채널을 요구하고 적용 불가 시 `POSTURE_UNMEASURED`로 점수 사용을 금지한다 (`AGENTS.md:297-301`). 따라서 v2 구현도 **부분 준수**이며, 두 채널·gate parameter fingerprint를 강제해야 한다.

### 2.4 내부 gate와 공식형 목적함수의 관계

- 최신 tier-1은 `min_total_points_delta`와 scenario별 `max_survival_regression`을 veto로 사용한다 (`go2_tuning_eval_report.py:27-48`). `target_scenario`는 정보용이다 (`:37-45`). 대표 승급은 절대 `minimum_points_70`, 모든 scenario survival/tracking threshold, 3 seed 완결성을 요구한다 (`:61-85`).
- `min_total_points_delta`, `max_survival_regression`, `minimum_points_70=60`, survival 0.95, tracking 0.70은 공식 채점식에 없는 **내부 risk/promotion policy**다 (`config/go2_self_eval_registry.json:42-50,60-70`). 이들은 제출 후보의 안전 여유로는 사용할 수 있으나 “공식식상 FAIL”로 표현하면 안 된다.
- A009와 A010 최초 판정은 총점이 각각 `+3.090285`, `+2.257160`인데 목표 G1 delta만으로 FAIL이었다 (`workspace/_keep/go2_track_lin_vel_120_v1/reports/TIER1_DECISION.json`; `workspace/_keep/go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json`). 이는 공식형 총점 목적과 불일치했고 최신 코드 주석도 이 문제를 인정한다 (`go2_tuning_eval_report.py:27-31`).
- A017은 같은 evaluator의 양 arm 비교라 수치는 유효하지만, survival 단독 veto가 이미 survival을 포함한 scenario product와 가중 총점보다 우선했다. 따라서 “총점 개선 신호 + 내부 안전 veto”로 분리 기록해야 한다.

### 2.5 비교 파이프라인·스키마·지침 인프라 결함

1. **Evaluator fingerprint 불변식 부재 [A1].** runner는 cached baseline을 복사하고 G7 하나만 다시 실행한다 (`server_run_go2_tuning_engine_v1.sh:334-350`). report는 arm별 `schema_version`, `survival_proxy_source`, `posture_gate` 일치를 확인하지 않는다 (`go2_tuning_eval_report.py:14-58`).
2. **Baseline cache 세대 혼합 [A1].** Default cache는 구 builder, Chain cache는 A009 artifact의 v1 summary를 복사한다. Pilot cache만 A012 v2를 쓴다 (`tools/build_go2_tuning_engine.py:58-74,77-114`). 그 결과 A015~A018만 양 arm v2이고, Default/Chain 기반 후속 비교는 비대칭이다.
3. **JSON Schema stale/얕음 [A1].** schema는 `engine_version: 1.2.0`만 허용하고 nested object 계약을 정의하지 않는다 (`config/go2_tuning_experiment_schema.json:6-63`), runtime은 `ENGINE_VERSION=1.3.0`과 exact-one-change·baseline hash·gates를 검사한다 (`go2_tuning_config.py:17,156-211`). A025 spec도 `engine_version: 1.3.0`이다 (`upload/G-A025/current/G_A025_flat_orientation_m1.json#/engine_version`). 즉 JSON Schema 단독 검증은 현재 spec을 거부하면서도 nested gate 타당성은 검증하지 못한다.
4. **G7 독립성 계약 부재 [A1].** full runner의 DR case가 G3와 같은 command/terrain이며 별도 `DR_MODE`가 없다 (`server_run_go2_pilot_v2_baseline.sh:120-140`). 반면 A009 tier-1 runner는 `dr_seed_*`에서 `DR_MODE=1`을 설정한다 (`server_run_go2_track_lin_vel_120_v1.sh:138-169`). hash-negative contract가 필요하다.
5. **수정 허용 범위 충돌 [A1].** 강좌는 `REWARD_WEIGHTS`의 값만 바꾸라고 한다 (`test/14강의...html:658,738-739`), 상위 규정도 값만 허용한다 (`AGENTS.md:357-370`). 그런데 `quadruped_rewards.py:38`은 줄 추가/삭제/주석 자유라고 적는다. 이 주석은 제출 무결성 위험을 만들므로 “기존 key의 값만”으로 수정해야 한다.
6. **서브에이전트 지침은 사후 보완됐으나 대칭성 검사는 아직 코드화되지 않았다 [B].** `go2-evaluation-auditor.md:94-104`는 telemetry code·posture source·raw CSV 대조를 의무화한다. 그러나 현재 engine/report 코드에는 arm fingerprint equality가 없다 (`go2_tuning_eval_report.py:14-58`). 문서 지침만으로 재발을 막기 어렵다.

### 2.6 문헌·H1 참고의 사용 한계

- H1에서 정당하게 전이 가능한 것은 단일변수, 사전등록, reward-independent evaluation, missing-data=INCOMPLETE, 동일 evaluator·seed 비교 같은 **방법론**이다 (`H1_REWARD_EVIDENCE_MASTER.md:12-17,86-99,131-169`; `PROJECT_STATE.md:292-294`).
- H1 reward 수치·시나리오·임계값·GPU 단가·`base_contact` 결론은 Go2에 전이할 수 없다 (`workspace/training/quadruped/AGENTS.md:8-22,65-74`).
- `GO2_REWARD_EVIDENCE_MASTER.md`의 Rudin et al. 관련 reward table 인용은 로컬에 논문 원문/pinned source가 없어 본 감사에서는 **외부 원문 미보존[C]**으로 처리한다 (`GO2_REWARD_EVIDENCE_MASTER.md:209-220`). R-Sci-2/3에서 DR·push robust 원인을 직접 도출하거나 로컬 height scanner와 논문 perception stack을 동일시하는 서술도 로컬 원문·버전 pin 없이 확정할 수 없다 (`GO2_REWARD_EVIDENCE_MASTER.md:241-268`).

## 3. 실행별 감사 표 — G-A006~G-A025

> `candidate_points_70`은 해당 evaluator가 산출한 절대 내부 proxy다. delta가 무효여도 candidate v2 raw measurement 자체는 남을 수 있다. `OFFICIAL_RESULT`는 전 실행 미측정이다.

| ID | 설계·기준선 | evaluator | 기록 수치/판정 | 독립 감사 |
|---|---|---|---|---|
| **A006** | Default-01 vs 4변수 Pilot-01. 초기 상한 탐색은 가능하나 인과 분리 불가 (`GO2_PROJECT_STATE.md:143-146`) | 양 arm termination-only v1 | `17.906992→41.979898`; 양 정책 `INTERNAL_GATE_FAIL`; 비교 `SHARED_WEAKNESS_FOUND` (`workspace/_keep/go2_default_vs_pilot_v1/reports/GO2_DEFAULT_VS_PILOT_PAIRED_REPORT.json`) | **PARTIAL** — 같은 v1 자의 상대 방향만 남고 공식 생존 근거는 아니다. G7=G3 byte-identical이라 G7 무효. |
| **A007** | Default에서 `feet_air_time .01→.20`, G5 개선 사전등록 (`GO2_PROJECT_STATE.md:157-168`) | 양 arm v1; full G7 중복 | `17.906992→21.772582`, `+3.865590`; `INTERNAL_SCREEN_FAIL` (`workspace/_keep/go2_feet_air_time_020_v1/reports/GO2_FEET_AIR_TIME_020_SCREENING_REPORT.json`) | **목표 가설 FAIL / 총점 신호 PARTIAL** — G5 proxy `0.131756→0.099007`로 목표 `+0.03`의 반대. 전체 양수 delta를 “무가치”로 확대하면 안 됨. |
| **A008** | A007 crash/graceful shutdown hotfix, reward·checkpoint 변화 없음 (`ARTIFACT_MANAGEMENT.md:340-360`) | 성능 evaluator 신규 세대 아님 | 점수 없음 | **인프라 작업 N/A** — 별도 튜닝 실행으로 집계 금지. |
| **A009** | Default에서 `track_lin 1.0→1.2`, Pilot의 속도 항 인과 분리 (`GO2_PROJECT_STATE.md:220-235`) | 양 arm v1; tier1 G7은 DR_MODE 사용 | `17.537121→20.627405`, `+3.090285`; target G1 미달로 FAIL (`workspace/_keep/go2_track_lin_vel_120_v1/reports/TIER1_DECISION.json`) | **G1 가설 FAIL / 총점 PARTIAL** — target-only gate가 총점 개선을 veto. v1이라 survival 안전성 미확정. |
| **A010** | Default에서 `lin_vel_z -3→-2`; 단일변수 자체는 타당 (`upload/G-A010/current/G_A010_lin_vel_z_m2.json#/single_change`) | 최초 양 arm v1; 260906 재측정 candidate v2 vs baseline mixed | 최초 `+2.257160` target FAIL; 재측정 `17.132070→9.499548`, `-7.632522` (`workspace/_keep/go2_g_a010_lin_vel_z_m2_v2_260906/.../reports/TIER1_DECISION.json`) | **delta UNDETERMINED; candidate 절대 v2 낮음**. 양 arm v1 재계산은 `+2.257160`; 참 v2 delta는 Default-v2 필요. |
| **A011** | 별도 artifact 없음. 조건부 `ang_vel -.08→-.05`와 withdrawn terrain plan이 ID에 혼재 (`GO2_CAMPAIGN_SCHEDULE.md:214,284`) | 미확인 | 후속 원장이 A009의 `+3.090285`를 A011로 재명명 (`GO2_PROJECT_STATE.md:506-507`) | **LEDGER_IDENTITY_FAIL** — 실제 verifier는 `work_id=G-A009` (`workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/VERIFICATION.json#/work_id`). 별도 실행으로 세지 않는다. |
| **A012** | 학습 없이 Pilot-01 69-case posture 측정 (`GO2_PROJECT_STATE.md:330-349`) | candidate-only/full posture v2 | `33.793106/70`, `INTERNAL_GATE_FAIL`; `TRAINING=none` (`workspace/_keep/go2_pilot_v2_baseline/evaluation/pilot_v2/SELF_EVAL_REPORT.json`) | **PARTIAL** — G1~G6 절대 v2 측정은 유효. G7 steps가 G3와 3 seed 모두 동일하므로 G7 무효. |
| **A013** | Default에서 `flat_orientation 0→-1`; 미사용 자세 dial 탐색 (`upload/G-A013/current/G_A013_flat_orientation_m1.json#/single_change`) | candidate v2, baseline mixed | `17.132070→15.704282`, `-1.427788`, recorded FAIL; G3 proxy `+0.060788` (`workspace/_keep/go2_g_a013_flat_orientation_m1/reports/TIER1_DECISION.json`) | **delta UNDETERMINED; candidate 절대 v2 낮음**. 같은 v1 재계산 `+3.654378`; G4/G5 악화의 인과 단정 불가. |
| **A014** | `flat_orientation -2` 조건부 후속이 취소됨 (`GO2_CAMPAIGN_SCHEDULE.md:340-351`) | 실행 없음 | 없음 | **N/A** — A013 비교가 비대칭이므로 취소의 인과 근거는 약해졌지만, 신규 실행을 즉시 복원할 근거도 없음. |
| **A015** | Pilot에서 `feet_air .20→.35`, 지형 dial 상한 탐색 (`upload/G-A015/current/G_A015_pilot_feet_air_time_035.json#/single_change`) | 양 arm posture v2 | `46.491241→16.369309`, `-30.121932`, 5 scenario survival veto (`workspace/_keep/go2_g_a015_pilot_feet_air_time_035/reports/TIER1_DECISION.json`) | **유효 INTERNAL FAIL** — 절대·delta·생존이 같은 방향. |
| **A016** | Pilot에서 `ang_vel -.05→-.15`; 3배 penalty로 폭이 공격적 (`upload/G-A016/current/G_A016_pilot_ang_vel_xy_m015.json#/single_change`) | 양 arm posture v2 | `46.491241→1.375697`, `-45.115544`, 7/7 survival 회귀 (`.../go2_g_a016_pilot_ang_vel_xy_m015/reports/TIER1_DECISION.json`) | **유효 INTERNAL FAIL**. |
| **A017** | Pilot에서 `track_lin 1.2→1.4`, +0.2 소폭 (`upload/G-A017/current/G_A017_pilot_track_lin_vel_xy_140.json#/single_change`) | 양 arm posture v2 | `46.491241→50.199157`, `+3.707916`; G4 survival veto 하나 (`.../go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json`) | **TOTAL-PROXY IMPROVEMENT + RISK-VETO**. 공식형 총점 신호는 양수. 절대 `<60`, seed 101뿐이라 representative 승급은 불가; 다이얼 완전 기각도 과도. |
| **A018** | Pilot에서 `action_rate -.01→-.008`; 직접 시나리오 근거 약함 (`upload/G-A018/current/G_A018_pilot_action_rate_m008.json#/single_change`) | 양 arm posture v2 | `46.491241→2.092602`, `-44.398639`, 7/7 survival 회귀 (`.../go2_g_a018_pilot_action_rate_m008/reports/TIER1_DECISION.json`) | **유효 INTERNAL FAIL**. |
| **A019** | Pilot에서 `track_lin 1.2→1.3`; A017 양수 신호를 절반 폭으로 재검증하려던 설계 (`GO2_PROJECT_STATE.md:488-493`) | 실행 없음 | withdrawn/cancelled; result artifact 없음 | **미실행** — 설계 정보가치는 높았으나 새 측정으로 간주할 수 없음. |
| **A020** | Chain에서 `lin_vel -3→-2`; A009/A010 v1 양수 신호를 검증된 승자로 과대승격해 합성 (`GO2_PROJECT_STATE.md:506-515`) | candidate v2 vs Chain baseline mixed | `18.610562→0.428330`, `-18.182232`, FAIL (`.../go2_g_a020_chain01_lin_vel_z_m2/reports/TIER1_DECISION.json`) | **설계 순서 부당 + delta UNDETERMINED**. Chain-v2 자체 측정을 먼저 했어야 함. candidate 절대 v2는 낮음; 대칭 v1 delta `-0.221130`. |
| **A021** | Chain에서 `ang_vel -.08→-.05`, Pilot 다변수 항 분리 (`upload/G-A021/current/G_A021_chain01_ang_vel_xy_m005.json#/single_change`) | candidate v2 vs mixed baseline | `18.610562→12.002626`, `-6.607936`, FAIL (`.../go2_g_a021_chain01_ang_vel_xy_m005/reports/TIER1_DECISION.json`) | **delta UNDETERMINED; candidate 절대 v2 낮음**. 대칭 v1 delta `-0.351602`. |
| **A022** | Chain에서 `feet_air .01→.20`, A007 양수 총점 신호 재사용 (`upload/G-A022/current/G_A022_chain01_feet_air_time_020.json#/single_change`) | candidate v2 vs mixed baseline | `18.610562→4.883013`, `-13.727549`, FAIL (`.../go2_g_a022_chain01_feet_air_time_020/reports/TIER1_DECISION.json`) | **delta UNDETERMINED; candidate 절대 v2 낮음**. 대칭 v1 delta는 `+0.449132`; 변경이 붕괴 원인이라는 결론은 입증되지 않음. |
| **A023** | 학습 없이 Chain-01 69-case v2 측정; 필요했지만 A020~A022 뒤로 늦음 (`GO2_PROJECT_STATE.md:545-554`) | Chain arm posture v2 | `2.307745/70`, `INTERNAL_GATE_FAIL` (`workspace/_keep/go2_chain01_baseline/evaluation/chain01/SELF_EVAL_REPORT.json`) | **Chain 절대 v2 낮음은 유효**. Default v1 `17.90699`와의 우열 비교는 세대 혼용으로 무효. G7=G3 중복으로 G7 증거도 무효. |
| **A024** | Default에서 `ang_vel -.08→-.15`; A016 동일 값의 파국 뒤여서 정보가치 제한 (`upload/G-A024/current/G_A024_ang_vel_xy_m015.json#/single_change`) | candidate v2 vs mixed baseline | `17.132070→0`, `-17.132070`, 7/7 survival 회귀 (`.../go2_g_a024_ang_vel_xy_m015/reports/TIER1_DECISION.json`) | **candidate 절대 INTERNAL FAIL; delta UNDETERMINED**. raw `fallen_env_count=32/32`인 case들이 있어 후보 자체 부적합. 대칭 v1 delta `+3.461676`은 mismatch 크기만 증명. |
| **A025** | A013 재측정 명목이나 동일 seed/설정/model의 중복 (`upload/G-A025/current/G_A025_flat_orientation_m1.json`; 두 run `RUNNER_STATUS.txt`) | candidate v2 vs mixed baseline | A013과 동일 `17.132070→15.704282`, `-1.427788` (`.../go2_g_a025_flat_orientation_m1/reports/TIER1_DECISION.json`) | **실행 정당성 FAIL / delta UNDETERMINED**. 정보이득 0. 후보 절대 v2 낮음이나 flat-orientation 인과효과는 Default-v2 전까지 미확인. |

### 3.1 절대점수와 delta가 충돌할 때

- **최종 제출 후보 판단:** 동일 evaluator의 candidate 절대점수와 G1~G7 완결성·대표 seed가 우선이다. delta가 양수여도 절대 `minimum_points_70`과 scenario gates를 못 넘으면 대표 승급은 안 된다 (`go2_tuning_eval_report.py:61-85`).
- **reward 인과효과 판단:** 같은 evaluator·같은 case/seed의 baseline delta가 우선이다. candidate 절대점수가 낮아도 “변경 때문에 낮아졌다”는 결론은 대칭 baseline 없이는 낼 수 없다.
- **A017:** 절대 50.199는 최종 승급 미달이나, 양 arm v2의 `+3.7079`는 후속 축소값/추가 seed를 정당화하는 개선 신호다.
- **A010/A013/A020~A022/A024/A025:** candidate 절대 v2는 낮지만 delta가 비대칭이므로 reward 방향의 채택/기각은 `UNDETERMINED`다.

## 4. 남은 GPU 예산 대비 개선 계획

### 4.1 예산 사실

- 규정상 팀 총 100시간이라는 저장소 정본이 있다 (`AGENTS.md:351-355`).
- `GO2_CAMPAIGN_SCHEDULE.md:227-228`은 260903 시점 잔여 25시간을 Go2에 배정했지만, 이후 A013~A025 다수 실행이 진행됐다. 매 작업 후 갱신된 단일 잔여시간 원장은 확인되지 않았다. 따라서 **현재 잔여 GPU/서버 과금시간은 미확인**이며 25시간을 현재 잔여로 사용하지 않는다.
- 아래 계획은 우선 **학습 0회**, 다음 **최대 1회 1,000 iter**, 그 뒤에만 조건부 장기학습으로 시간 상한을 둔다. 1,000 iter 실측은 약 59분이다 (`GO2_PROJECT_STATE.md:360`).

### 4.2 사전등록 실행 순서

| 순서 | 등급 | 작업·목적 | 서버 시간 상한 | 성공 기준 | 실패 시 fallback |
|---:|---|---|---:|---|---|
| 0 | 필수(계측) | engine/report에 arm fingerprint 불변식 추가: 각 case의 `schema_version`, `survival_proxy_source`, `posture_gate`가 양 arm 동일하지 않으면 `EVALUATOR_MISMATCH`로 점수 계산 중단. stale JSON Schema 1.3.0 동기화, nested gates/one-change 명시. | GPU 0 | mismatch fixture가 실패하고 대칭 fixture만 통과 | 코드 수정 전 신규 학습·판정 전부 HOLD |
| 1 | 필수(계측) | G7 runner를 G3와 분리: `DR_MODE=1` 및 realized randomization values를 보존하고, 같은 seed G3/G7 `steps.csv` SHA가 같으면 실패하는 hash-negative test 추가. | GPU 0 | G3/G7 command/override/fingerprint가 다르고 realized DR 필드 존재 | G7은 `SELF_ASSESSMENT_INCOMPLETE`, 점수 0 처리 |
| 2 | 필수(기준선) | **G-A026: Default-01 학습 없이 posture_gate_v2 재평가.** 먼저 tier1 7 case, 가능하면 69-case×3seed. 두 posture 채널이 모두 존재해야 함. | tier1 20~35분; full 60~90분(과거 artifact 기반 추정) | 7/7 또는 69/69 완료, 양 채널, `survival_proxy_source=posture_gate_v2`, G7 독립 hash | posture channel/DR 실패 시 `POSTURE_UNMEASURED`로 중단; 새 reward 학습 금지 |
| 3 | 필수(재판정) | 새 Default-v2 cache로 A010, A013(=A025), A024를 **재학습 없이** 재계산. Chain-v2(A023) tier1 대응값으로 A020~A022 재계산. | GPU 0 | 동일 fingerprint의 baseline/candidate delta와 absolute score 동시 보고 | case 정의 불일치면 해당 candidate checkpoint만 같은 7 case로 평가(학습 없음) |
| 4 | 개선 | A017 frozen checkpoint를 seed 202·303 동일 v2 tier1로 추가 평가. primary=`weighted points delta`; survival regression은 별도 risk flag로 표시. | 20~40분 | 3 seed delta 방향 일치, 절대점수 상승, G4 product/생존 변동 범위 보고 | seed inversion 또는 절대 붕괴면 1.4 폐기, Pilot-01 유지 |
| 5 | 개선 | A017 신호가 유지될 때만 A019 `track_lin 1.2→1.3` 1,000 iter from-scratch 1회. 나머지 reward·seed·case·evaluator 고정. | 학습 약 60분 + tier1 20~35분 | 양 arm v2, total delta >0, no catastrophic absolute posture failure; 결과와 무관하게 representative 전 자동중단 | 실패 시 1.2 Pilot로 복귀; 다른 reward 다이얼로 즉시 전환 금지 |
| 6 | 개선 | A019가 seed 101에서 유망하면 evaluation seed 202·303만 추가. 21-case 대표 점수와 per-scenario absolute gate 평가. | 30~60분 | 3 seed 완결, candidate ≥60/70, 각 survival ≥.95·tracking ≥.70은 **내부 승급 정책**으로 별도 표기 | 미달이면 장기학습 금지; 최고 동결 policy 제출 후보와 문서축만 정리 |
| 7 | 개선(조건부) | 위 모든 조건을 만족한 단일 조합만 3,000 iter로 확장 후 재평가. 5,000 이상은 3,000 결과 후 별도 승인. | 약 3시간 + 평가 | 동일 evaluator에서 absolute/delta 비열등, artifact·영상·telemetry 완결 | 3k 중간 checkpoint/curve 악화 시 조기중단·bundle 회수 |

### 4.3 게이트 재정의 권고

- **Tier-1 primary:** `candidate_points_70 - baseline_points_70 > 0` 및 bootstrap/반복 seed 방향. `min_total_points_delta=1.0`은 공식식이 아니라 최소 효과크기 정책으로 이름을 `min_operational_effect_points_70`로 바꾼다.
- **Risk flags:** scenario survival regression, absolute posture failure, video anomaly를 veto와 분리해 함께 보고한다. 파국적 자세 실패는 early kill 가능하지만 “공식식 FAIL”이 아니라 `INTERNAL_SAFETY_VETO`다.
- **Representative promotion:** 절대 score·3 seed·각 scenario survival/tracking threshold를 유지하되, 내부 기준임을 명시한다.
- **A017 처리:** `INTERNAL_EARLY_KILL_FAIL` 기록은 보존하되 해석을 “총점 개선 + G4 safety veto”로 정정한다. 가장 정보가치 높은 다음 reward 실험은 A019 1.3이며, 그 전에 계측/기준선 복구와 A017 추가 seed가 선행돼야 한다.

### 4.4 현재 reward 파일 처리

- 루트 현재 `quadruped_rewards.py`는 `1.2 / 0.2 / -2 / -0.05 / -0.01 / 0.0`의 4변수 Pilot 조합이다 (`workspace/training/quadruped/quadruped_rewards.py:41-83`). 이는 A025 candidate(`1.0 / .01 / -3 / -.08 / -.01 / -1`)가 아니다 (`upload/G-A025/current/G_A025_flat_orientation_m1.json#/rewards/candidate`). “현재 파일”과 “평가 대상 checkpoint”를 동일시하지 말고, 보고서 식별자는 checkpoint iter + model SHA + env SHA로 고정한다.

### 4.5 감사 중 확인 불가능했던 항목

1. **미확인:** 운영진 원본 규정집/PDF/공지와 `workspace/PRELIM_RL_GUID.md`의 진본 동일성. 저장소에는 후자만 확인됨.
2. **미확인:** 공식 tracking 변환, command grid, episode/seed 수, terrain generator, push, DR, 공식 통과선 (`config/go2_self_eval_registry.json:27-35`).
3. **미확인:** 현재 남은 팀 서버 과금시간. 260903의 “잔여 25시간” 뒤 실행비용이 단일 원장에 합산되지 않음 (`GO2_CAMPAIGN_SCHEDULE.md:227-228`).
4. **미확인:** Default-01의 posture_gate_v2 점수. cached baseline은 v1이고 raw `steps.csv`가 없어 로컬 재채점 불가.
5. **미확인:** G-A011이라는 별도 실행의 존재. 확인된 track-linear artifact ID는 G-A009다.
6. **미확인:** 공식 G7 DR의 정확한 fields/ranges. 현재 full runner의 G7은 G3와 byte-identical하여 사용할 수 없음.
7. **미확인:** `FALL_TILT_COS=0.5`, `FALL_HEIGHT_M=0.18`, hold/grace 0.5s의 공식 calibration. 이 값은 내부 설정이다 (`go2_eval_telemetry.py:83-86`).
8. **미확인:** 로컬에 원문이 보존되지 않은 외부 논문/Isaac Lab version pin에 대한 인용 정확성. 해당 주장은 제출 리포트에서 원문 snapshot·버전 SHA 없이 확정 사실로 쓰지 않는다.
9. **미측정:** 모든 실행의 공식 대시보드 결과. artifact는 일관되게 `OFFICIAL_RESULT_UNMEASURED`를 기록한다.

---

### 독립 단계 봉인

이 지점까지는 `GO2_DESIGN_REVIEW_260907.md`를 열지 않고 작성했다. 다음 단계에서 본 파일의 SHA-256을 기록한 뒤 기존 감사 문서를 처음 열어 §5를 추가한다.

## 5. 기존 감사(`GO2_DESIGN_REVIEW_260907.md`)와의 대조

### 5.0 독립성 확인과 비교 전 추가 발견

- §0~§4의 최초 고정본 SHA-256은 `a635e53ae735c6abd51d77891da865c787430d14d4d29b3289566735fe0bd4bf`이며 `GO2_INDEPENDENT_AUDIT_CODEX_260907.phase3.sha256`에 보존했다. 이 해시를 기록·재확인한 뒤에만 기존 감사 문서를 처음 열었다.
- 비교 문서를 열기 전에 채점 체계 담당 독립 감사에서 §0~§4에 없던 결함 두 건을 추가 확인했다.
  1. **시나리오 집계가 표시된 `survival × tracking`과 일치하지 않는다.** case 단위 곱은 맞지만 (`workspace/training/quadruped/go2_fixed_eval_report.py:23-47`), scenario의 survival·tracking·proxy를 각각 독립 최소값으로 뽑는다 (`workspace/training/quadruped/go2_fixed_eval_report.py:83-100`). Pilot-v1 G3은 `survival=0.5625`, `tracking=0.5904083599`, 두 값의 곱 `0.3321047025`인데 저장된 `scenario_proxy=0.4403176288`이다 (`workspace/_keep/go2_default_vs_pilot_v1/evaluation/pilot/SELF_EVAL_REPORT.json#/scenarios/G3`). 차이 `0.1082129264`, G3 가중치 환산 약 `1.515/70점`이다. 현재 구현을 공식 scenario 곱셈의 정확한 재현이라고 부를 수 없다.
  2. **G6은 upright 회복값을 계산하고도 사용하지 않는다.** collector는 누운 채 정지를 회복으로 인용하면 안 된다고 쓰고 `recovery_rate_upright`를 계산한다 (`workspace/training/quadruped/go2_eval_telemetry.py:286-334`). reporter는 구형 `recovery_rate`를 tracking에 사용한다 (`workspace/training/quadruped/go2_fixed_eval_report.py:37-40`). Chain-01 `push_pos_x`는 `recovery_rate=1.0`, `recovery_rate_upright=0.78125`, `survival_proxy=0.5625`다 (`workspace/_keep/go2_chain01_baseline/evaluation/chain01/cases/seed_101/push_pos_x/summary.json#/recovery,#/survival_proxy`). G6은 upright 값을 사용하도록 고치고 posture 미측정이면 `SELF_ASSESSMENT_INCOMPLETE`여야 한다.

### 5.1 E1~E4 대조

| 주장 | 대조 판정 | 독립 근거와 조정 결론 |
|---|---|---|
| **E1 — survival 경성 게이트가 목적함수와 불일치** (`GO2_DESIGN_REVIEW_260907.md:108-171`) | **부분동의** | A017은 양 arm v2이고 총점 `+3.707916`, G4 case-worst proxy도 `+0.015871`인데 survival `-0.21875` 하나로 기각됐다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json#/candidate_minus_baseline_points_70,#/scenario_deltas/G4,#/failure_reasons`). 따라서 **공식형 점수 개선과 내부 안전 veto의 혼동**은 확정이다. 그러나 이것이 “17회 0채택의 주원인”이라는 인과 주장은 과대하다. A015·A016·A018은 양 arm v2에서 총점도 크게 하락했고, A010 재측정·A013·A020~A022·A024·A025는 evaluator 비대칭이라 원인 자체가 미정이다 (각 실행 `reports/TIER1_DECISION.json`; §3 표). 확정 가능한 E1 실사례는 A017 한 건이다.
| **E2 — 절대점수 대신 delta만 봄** (`GO2_DESIGN_REVIEW_260907.md:173-179,272-296`) | **부분동의** | 각 candidate의 v2 절대값은 baseline arm 비대칭의 직접 영향은 받지 않는다. 하지만 절대값도 posture OR/fallback (`workspace/training/quadruped/go2_eval_telemetry.py:233-243,348-377`), scenario 독립 최소 집계 (`go2_fixed_eval_report.py:83-100`), G6 구형 recovery (`:37-40`), G3/G7 중복, 7-case/1-seed와 69-case/3-seed 혼합의 영향을 받는다. 따라서 “절대 서열이 확정”은 과도하다. **제출 후보는 동일한 완전 evaluator의 절대점수**, reward 인과는 **동일 evaluator의 delta**를 함께 써야 한다.
| **E3 — 1,000 iter가 성격 판별 하한 3,000 미만** (`GO2_DESIGN_REVIEW_260907.md:180-200`) | **불일치** | `workspace/training/PRELIM_RL_GUIDE.md:173-183`은 실험 단계를 `1000~5000`, 성격 발현도 `1000~5000`으로 쓴다. `quadruped_rewards.py:112-120`의 3,000 권장과 충돌하므로 3,000을 운영진의 단일 하한으로 확정할 수 없다. 1,000 iter는 **exploratory screening에는 허용**, 최종 제출 성능 확정에는 불충분하다는 것이 정확하다. 기존 감사도 후반부에서 이를 자체 반증했다 (`GO2_DESIGN_REVIEW_260907.md:895-897,1055`).
| **E4 — 미탐색 dial** (`GO2_DESIGN_REVIEW_260907.md:202-231`) | **수정본에 부분동의** | A017 `env.yaml`에는 `track_ang_vel_z_exp`와 `std:0.5`가 정의되고 `undesired_contacts:null`이며 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/training/env.yaml:826-883`), reward 파일에는 track-ang/undesired/termination이 주석 상태다 (`workspace/training/quadruped/quadruped_rewards.py:85-94`). 따라서 “실제 미시험 값은 track-ang 하나”라는 축소는 대체로 맞다. 다만 파일 주석은 줄 추가·주석 해제를 허용한다고 쓰지만 (`quadruped_rewards.py:32-39`), 상위 규정 계약은 기존 reward의 **값만** 변경하도록 한다 (`AGENTS.md:357-370`). 원 규정 원문이 로컬에 없으므로 주석 해제의 제출 적법성은 **미확인**이며, 확인 전 실행해서는 안 된다.

### 5.2 §7 계획과 현재 §14 개정안 대조

#### §7 제2판

**불일치 — 실행 계획으로 사용하면 안 된다.** 기존 감사 자체가 §7을 폐기했다 (`GO2_DESIGN_REVIEW_260907.md:442-448,878-882`). 독립 감사 기준에서도 §7은 다음 선행조건을 건너뛴다.

1. Default/Chain baseline arm mismatch를 엔진에서 차단하지 않은 채 장기학습을 먼저 배치한다 (`workspace/training/quadruped/server_run_go2_tuning_engine_v1.sh:334-350`; `workspace/training/quadruped/go2_tuning_eval_report.py:14-58`).
2. A017의 기준값은 tier-1 seed 101·7 case뿐인데 장기 6.8시간의 기준으로 사용한다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json`; `GO2_DESIGN_REVIEW_260907.md:509-523`).
3. 하드 스톱 시 `TRAIN_RC != 0`이면 러너가 `exit 3`으로 평가 전에 끝난다 (`workspace/training/quadruped/server_run_go2_tuning_engine_v1.sh:107-121`). 기본 finalize는 best 외 checkpoint를 정리한다 (`workspace/training/quadruped/go2_task/_finalize.py:108-134,178-180`). 따라서 §7의 중단·복구 경로는 코드와 맞지 않는다.
4. A017 학습 로그의 iter 999 `terrain_levels=4.2503`은 평가된 `model_900.pt`와 같은 시점이 아니다. best 선택은 step 856→`model_900.pt`, 중간 checkpoint 10개는 삭제됐다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/launcher.log:33276-33282`; `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/logs/candidate_training.log:29849-29904,33149-33171`). 따라서 §7의 terrain 4.2503 교차 게이트는 정책-지표 식별자가 맞지 않는다.

#### §14 제3판

**부분동의 — 방향은 개선됐지만 그대로 실행하면 안 된다.** S0에서 evaluator equality와 게이트 부호 테스트를 먼저 두고, S0.5에서 A017을 69-case×3seed로 재평가하며, 정상 종료 5,000 iter 러너를 쓰려는 순서는 §7보다 타당하다 (`GO2_DESIGN_REVIEW_260907.md:1037-1094`). 그러나 다음 수정을 선행해야 한다.

- S0에 **scenario 집계식 수정, 두 posture 채널 AND/`POSTURE_UNMEASURED`, G6 upright recovery, G3/G7 독립 hash-negative, env std provenance, JSON Schema 1.3 동기화**를 추가해야 한다 (`workspace/training/quadruped/go2_fixed_eval_report.py:12,23-47,83-100`; `go2_eval_telemetry.py:233-243,348-384`; `config/go2_tuning_experiment_schema.json:23-63`; `go2_tuning_config.py:17,156-211`). 이들이 없으면 S0.5의 69-case도 결함을 반복한다.
- 학습 전 G-A026 Default-01 v2 측정과 기존 A010/A013/A020~A025 무학습 재판정을 먼저 수행해야 한다. 원장도 신규 tier-1을 금지하고 G-A026을 다음 작업으로 둔다 (`GO2_PROJECT_STATE.md:657-675`).
- 5,000 iter 선택을 H1 terrain 포화곡선으로 정당화하면 Go2에 H1 reward/학습 결론을 복사하지 말라는 캠페인 경계와 충돌한다 (`workspace/training/quadruped/AGENTS.md:8-22`; `GO2_DESIGN_REVIEW_260907.md:1069-1080,1117-1119`). 5,000은 Go2 파일의 허용 범위 하단이라는 근거까지만 사용할 수 있다 (`workspace/training/quadruped/quadruped_rewards.py:112-120`).
- `NO_AUTO_SUBMIT=1`이 실제 자동 백업을 건너뛴 것은 로컬 로그로 확인된다 (`workspace/training/quadruped/server_run_go2_tuning_engine_v1.sh:107`; `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/launcher.log:33292`; `_finalize.py:845-860`). 그러나 이 사실이 공식 제출 자격을 막는지는 운영진 원문·서버 상태가 없어 **미확인**이다. 외부 업로드를 성능 게이트와 혼합하지 말고 별도 제출 무결성 확인으로 둬야 한다.

### 5.3 §9 약점 W1~W11 대조

| 항목 | 판정 | 근거 |
|---|---|---|
| W1 1k 서열 자기모순 | **동의** | A017은 tier-1 seed 101뿐이며 representative seed 202/303가 없다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json`; `go2_tuning_eval_report.py:61-85`). |
| W2 내부 proxy 불확실 | **동의, 더 심각** | 공식 세부식 미공개 (`config/go2_self_eval_registry.json:27-35`)에 더해 std 하드코딩·scenario 집계 불일치가 있다 (`go2_fixed_eval_report.py:12,19-20,83-100`). |
| W3 G4 survival 위험 | **동의** | A017 G4 survival `-0.21875`, proxy 이득은 `+0.015871`에 불과하다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json#/scenario_deltas/G4`). |
| W4 6.4~7.2k가 가이드 미달 | **불일치** | Go2 파일은 최종 `5000~15000`을 제시한다 (`workspace/training/quadruped/quadruped_rewards.py:112-120`). 공식 최적 길이는 미확인이다. |
| W5 termination 존재 미확인 | **문서 최신 정정에 동의** | A017 env rewards block에 `termination_penalty`가 없고 `undesired_contacts:null`이다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/training/env.yaml:819-888`). §9 W5는 낡았고 문서 후반이 정정했다 (`GO2_DESIGN_REVIEW_260907.md:737-741`). |
| W6 v1 raw 부재 | **동의** | Default cached summaries에는 v2 posture raw가 없어 로컬 변환이 불가능하다 (예: `workspace/_keep/go2_g_a025_flat_orientation_m1/evaluation/baseline_tier1/cases/seed_101/forward_fast/summary.json`). |
| W7 서버 이력 | **부분동의** | 자동 백업 skip은 확인되지만 (`server_run_go2_tuning_engine_v1.sh:107`; A017 `launcher.log:33292`), 이것이 제출 금지인지와 서버가 보유한 별도 이력은 로컬에서 확인 불가다. |
| W8 잔여 라운드/마감 | **동의** | 로컬 원장에는 260903 잔여 25시간 이후의 단일 최신 합산이 없다 (`GO2_CAMPAIGN_SCHEDULE.md:227-228`). |
| W9 단일 장기 run 집중 | **부분동의** | 집중 위험은 맞다. A013/A025 model SHA 동일은 특정 조건의 재현성을 보이지만 (`GO2_PROJECT_STATE.md:640-641`), 모든 장기 run이 결정적이라는 일반화는 한 쌍으로 증명되지 않는다. |
| W10 terrain 4.2503 자의성 | **동의, 게이트 폐기** | 수치 출처가 iter 999이고 평가 정책은 model_900이다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/launcher.log:33276-33282`; `candidate_training.log:29849-29904,33149-33171`). |
| W11 screening 정보가치 | **동의** | 다음 라운드가 남는다면 즉시 장기화하지 못해도 결과는 후속 의사결정 정보다. 다만 남은 라운드 자체가 로컬에서 미측정이다 (`GO2_CAMPAIGN_SCHEDULE.md:227-228`). |

### 5.4 §10 질문에 대한 독립 답변

**Q1 — 부분동의.** A017은 E1을 직접 지지한다. 그러나 A015·A016·A018은 점수 자체가 악화했고, 다수 Default/Chain 실행은 v1/v2 mismatch라 0채택 전체의 주원인을 E1 하나로 귀속할 수 없다 (`workspace/_keep/go2_g_a015_pilot_feet_air_time_035/reports/TIER1_DECISION.json`; `workspace/_keep/go2_g_a016_pilot_ang_vel_xy_m015/reports/TIER1_DECISION.json`; `workspace/_keep/go2_g_a018_pilot_action_rate_m008/reports/TIER1_DECISION.json`; §3).

**Q2 — 부분동의.** arm 비대칭은 candidate 절대값의 산술에는 직접 들어가지 않는다. 그러나 “candidate가 v2”만으로 유효성이 충분하지 않다. posture fallback, scenario 집계, G6 recovery, G7 중복, case/seed breadth가 남는다 (`workspace/training/quadruped/go2_eval_telemetry.py:233-243,348-377`; `go2_fixed_eval_report.py:37-40,83-100`; §5.0).

**Q3 — 독립 검증으로는 불성립, 보조 상관으로만 사용 가능.** `terrain_levels`·`error_vel_xy`는 evaluator와 다른 코드 경로의 학습 지표지만 같은 정책·학습 궤적을 공유하고 공식 scenario score가 아니다. 더구나 A017의 4.2503은 iter 999, 평가 정책은 model_900이라 객체가 다르다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/launcher.log:33276-33282`; `candidate_training.log:29849-29904,33149-33171`). 독립 확인은 frozen checkpoint의 동일 G1~G7 evaluator·추가 seeds·영상으로 해야 한다.

**Q4 — §7 장기 베팅을 무효화할 정도다.** 해결은 resume 추정이 아니라 먼저 A017 frozen checkpoint를 69-case×3seed로 재평가하고, 그 전 evaluator/G7 결함을 고치는 것이다 (`go2_fixed_eval_report.py:83-100`; `server_run_go2_pilot_v2_baseline.sh:120-140`). 결과가 유지된 뒤에만 동일 조합 장기화를 검토한다.

**Q5-a — §7 선택은 옳지 않다.** B/C/채택안 중 바로 고르지 말고 `계측 수정 → G-A026 → 기존 무학습 재판정 → A017 3seed/full 평가`를 먼저 한다 (§4.2). 그 뒤에도 장기학습이 타당하면 한 개 10k보다 checkpoint ladder가 포함된 3k~5k 정상 종료 run이 정보량·회수 안전성에서 낫다 (`workspace/training/quadruped/quadruped_rewards.py:112-120`; `GO2_PROJECT_STATE.md:657-675`).

**Q5-b — 6.8h의 근거가 부족하다.** 17건 중 무효 3건을 장기 run 실패확률의 Bernoulli 표본으로 사용할 수 없고, 정확한 잔여시간도 최신 원장에 없다 (`GO2_CAMPAIGN_SCHEDULE.md:227-228`). 먼저 0~1.5h 계측·평가를 끝낸 뒤 실제 잔여시간과 1k 실측 약 59분 (`GO2_PROJECT_STATE.md:360`)으로 상한을 다시 계산해야 한다.

**Q5-c — A017 값을 장기 run에서 임의 조정하면 안 된다.** A017 그대로의 69-case×3seed 재평가로 전제를 먼저 검증한다. `track_lin 1.3`은 1.4가 반복 seed에서도 양수일 때만 별도 1k 단일변수 A019로 비교한다 (`GO2_PROJECT_STATE.md:488-493`; §4.2 순서 4~6). `feet_air_time=.2`, `lin_vel_z=-2`의 개별 인과는 다변수 Pilot 기원이라 확정되지 않았다 (`GO2_PROJECT_STATE.md:143-146`).

**Q5-d — terrain 임계값은 폐기한다.** 대체 교차확인은 같은 checkpoint·같은 evaluator·동일 case/3seed의 절대점수와 delta, scenario별 survival/tracking/product, upright G6 recovery, G3/G7 독립 fingerprint, 영상이다 (`go2_tuning_eval_report.py:14-85`; `go2_eval_telemetry.py:286-334`; §5.0).

**Q5-e — `termination_penalty`에 1.2h를 쓸 근거가 없다.** A017 env에 해당 항이 없고 `undesired_contacts`는 null이다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/training/env.yaml:819-888`). H1 reward 효과를 Go2 사실로 복사할 수 없다 (`workspace/training/quadruped/AGENTS.md:8-22`). 남은 track-ang은 env에 존재하지만 reward 파일 주석을 푸는 적법성부터 원 규정으로 확인해야 한다 (`quadruped_rewards.py:85-94`; `AGENTS.md:357-370`).

**Q5-f — W11의 논리 지적은 맞지만 즉시 장기 계획을 바꾸는 단독 근거는 아니다.** 후속 라운드가 있으면 screening은 가치가 있으나 남은 라운드가 미측정이다 (`GO2_CAMPAIGN_SCHEDULE.md:227-228`). 현재 계획을 바꿔야 하는 더 직접적인 근거는 evaluator mismatch와 G7 중복이다 (`server_run_go2_tuning_engine_v1.sh:334-350`; `server_run_go2_pilot_v2_baseline.sh:120-140`).

**Q6 — “Fr=1.06이 주원인”은 미확인 가설이며 실행 우선순위로 쓰지 않는다.** command range는 코드로 확인되지만 (`workspace/training/quadruped/go2_task/env_cfg.py:67-74`), 문서가 사용한 다리 길이 `L≈0.386m`와 전이 임계값 원문은 로컬 pinned source가 없다. 같은 환경에서 A017이 다른 결과를 냈으므로 환경은 유일 병목이 아니다 (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/logs/candidate_training.log:33149-33171`).

**Q7 — 로컬에서 확인 가능한 부분은 확인했다.** 러너가 `NO_AUTO_SUBMIT=1`을 설정했고 A017 로그는 자동 백업 skip을 기록한다 (`server_run_go2_tuning_engine_v1.sh:107`; `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/launcher.log:33292`). 그러나 운영 서버의 별도 학습 이력과 이것이 공식 제출을 막는지는 로컬로 확인할 수 없다. 따라서 `ARTIFACT_VERIFIED / SUBMISSION_HISTORY_UNCONFIRMED`이며, 제출 전 운영진 대시보드 또는 공식 문의로 확인할 외부 게이트다.

**Q8 — 기존 감사가 놓친 핵심은 다음 여덟 건이다.** ① scenario 표시 survival×tracking 불일치, ② G6 non-upright recovery 사용, ③ posture channel OR와 termination fallback, ④ full-suite G3/G7 byte-identical, ⑤ tracking std 하드코딩, ⑥ JSON Schema 1.2 vs runtime 1.3, ⑦ A011/A009 work-id 충돌, ⑧ 강좌에는 공식 채점 정의가 없다는 출처 혼합이다 (`go2_fixed_eval_report.py:12,23-47,83-100`; `go2_eval_telemetry.py:233-243,286-334,348-377`; `server_run_go2_pilot_v2_baseline.sh:120-140`; `config/go2_tuning_experiment_schema.json:23-63`; `go2_tuning_config.py:17,156-211`; `workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/VERIFICATION.json#/work_id`; `test/14강의. 보상 함수 설계와 조정 · 진화 · NAVER CONNECT ROBOTICS GUIDE BOOK.html:659-674,708-715`; `workspace/PRELIM_RL_GUID.md:60-70,92-104`).

### 5.5 한쪽만 포착한 사실

#### Codex 독립 감사만 포착

- 기존 감사 문서에는 `scenario_proxy != scenario_survival × scenario_tracking` 검증이 없었다. Pilot G3의 수치 반례는 §5.0에 제시했다 (`workspace/_keep/go2_default_vs_pilot_v1/evaluation/pilot/SELF_EVAL_REPORT.json#/scenarios/G3`; `go2_fixed_eval_report.py:83-100`).
- 기존 감사는 `recovery_rate_upright`를 A017 위험 설명에는 언급하지만, reporter가 G6에서 구형 `recovery_rate`를 실제 채점에 사용한다는 코드 결함은 찾지 않았다 (`go2_fixed_eval_report.py:37-40`; `go2_eval_telemetry.py:286-334`).
- 기존 감사는 full-suite G3/G7 raw duplicate, posture OR/fallback, std 하드코딩, stale JSON Schema, A011 ID 충돌을 식별하지 않았다 (각 근거 §5.4 Q8).

#### 기존 감사에서 추가로 포착했고 로컬로 재확인한 것

- A017의 `terrain_levels=4.2503`과 평가된 model_900의 시점 불일치, finalize의 checkpoint cleanup (`workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/launcher.log:33276-33282`; `workspace/training/quadruped/go2_task/_finalize.py:108-134,178-180`).
- 현행 러너에서 비정상 종료 `TRAIN_RC`가 평가 단계 진입을 막는 하드 스톱 경로 (`workspace/training/quadruped/server_run_go2_tuning_engine_v1.sh:107-121`).
- 모든 해당 Go2 runner가 자동 백업을 끄고 A017에서도 실제 skip됐다는 사실 (`server_run_go2_tuning_engine_v1.sh:107`; A017 `launcher.log:33292`). 단 공식 제출 자격 영향은 여전히 미확인이다.

### 5.6 §0~§4 축약 경로의 정규화

§0~§4 봉인본의 `.../`는 아래 전체 경로를 뜻한다. 이 표는 봉인 내용의 결론을 바꾸지 않고 모든 인용을 재현 가능하게 만든다. §5 추가 후 최종 파일 해시는 별도 `.sha256`에 기록했다.

또한 §0~§5에서 `config/`, `upload/`, `go2_*.py`, `server_run_go2_*.sh`, `quadruped_rewards.py`처럼 시작하는 경로는 별도 접두사가 없으면 모두 `workspace/training/quadruped/` 기준 상대경로다. 예를 들어 `upload/G-A017/current/G_A017_pilot_track_lin_vel_xy_140.json`의 전체 경로는 `workspace/training/quadruped/upload/G-A017/current/G_A017_pilot_track_lin_vel_xy_140.json`이다.

| 축약 표기 | 전체 경로 |
|---|---|
| `config/...registry.json` | `workspace/training/quadruped/config/go2_self_eval_registry.json` |
| `test/14강의...html` | `test/14강의. 보상 함수 설계와 조정 · 진화 · NAVER CONNECT ROBOTICS GUIDE BOOK.html` |
| `workspace/_keep/go2_g_a010_lin_vel_z_m2_v2_260906/.../reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a010_lin_vel_z_m2_v2_260906/go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json` |
| `.../go2_g_a016_pilot_ang_vel_xy_m015/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a016_pilot_ang_vel_xy_m015/reports/TIER1_DECISION.json` |
| `.../go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/reports/TIER1_DECISION.json` |
| `.../go2_g_a018_pilot_action_rate_m008/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a018_pilot_action_rate_m008/reports/TIER1_DECISION.json` |
| `.../go2_g_a020_chain01_lin_vel_z_m2/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a020_chain01_lin_vel_z_m2/reports/TIER1_DECISION.json` |
| `.../go2_g_a021_chain01_ang_vel_xy_m005/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a021_chain01_ang_vel_xy_m005/reports/TIER1_DECISION.json` |
| `.../go2_g_a022_chain01_feet_air_time_020/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a022_chain01_feet_air_time_020/reports/TIER1_DECISION.json` |
| `.../go2_g_a024_ang_vel_xy_m015/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a024_ang_vel_xy_m015/reports/TIER1_DECISION.json` |
| `.../go2_g_a025_flat_orientation_m1/reports/TIER1_DECISION.json` | `workspace/_keep/go2_g_a025_flat_orientation_m1/reports/TIER1_DECISION.json` |

### 5.7 최종 감사 판정

- **채점 인프라:** `REQUEST_CHANGES`. 공식형 곱셈의 case 산술은 있으나 scenario 집계·posture 완결성·G6·G7·arm fingerprint가 제출 전 자체 70점 게이트를 만족시키지 못한다 (`go2_fixed_eval_report.py:23-47,83-100`; `go2_eval_telemetry.py:233-243,286-334,348-377`).
- **A006~A025 캠페인:** `INTERNAL_AUDIT_PARTIAL`. 유효한 동세대 v2 비교는 A015~A018이며, 그중 A017만 총점 개선 신호가 있다. 이것은 제출 성능 합격이 아니라 후속 평가 우선순위다 (각 실행 `reports/TIER1_DECISION.json`; §3).
- **즉시 다음 단계:** 새 학습을 멈추고 §4.2 순서 0~4 — evaluator 수정, G7 분리, G-A026, 기존 무학습 재판정, A017 추가 seed/full 평가 — 를 먼저 수행한다. 그 결과가 나온 뒤에만 A019 또는 조건부 3k~5k를 승인한다.
- **공식 결과:** 전 실행 `OFFICIAL_RESULT_UNMEASURED`. 본 보고서는 예선 점수·통과를 보장하지 않는다 (`workspace/training/quadruped/go2_tuning_eval_report.py:46-58,77-85`).
