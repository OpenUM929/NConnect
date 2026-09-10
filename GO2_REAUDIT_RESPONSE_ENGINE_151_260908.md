# Go2 engine 1.5.1 독립 재감사 — Codex

작성일: 2026-09-08 · 작업 ID: CODEX-REAUDIT-151-260908 · 대상: 지시서에 고정된 engine 1.5.1 / G-A027 패키지.

## 0. 예선 기준 현재 위치
- **[예선 목표]** Go2 시뮬레이션 70점의 내부 평가 신뢰성, 설계 의도 20점·리포트 10점의 근거 정확성.
- **[현재 단계]** 단계 0/6 — 평가기·기존 측정 정합성. 환경 적응보다 앞선 측정 차단이 남아 있다(§3, §8).
- **[확보]** 지시서 17개 고정 SHA와 sidecar 일치, 안전한 로컬 계약 테스트 6종 종료 코드 0, 기존 11건 재판정 재현(§1, §4).
- **[미확보]** G-A027 신규 G1~G7 측정·영상, 완전한 결측 차단, 현재 GPU 잔여 시간, 운영진의 과거 이력 처리 답변.
- **[이번 테스트]** 평가 불능 자료의 차단과 G-A027의 재실행·회수 안전성 검증. 정책을 학습하거나 서버에서 재생하지 않았다.
- **[흐름]** 이전 검토 완료 → **수리 재감사** → 결함 해소 시 고정 정책 재측정 → 미해소 시 실행 보류·음성 테스트 → 최종 제출 검토.
- **[지금 할 일]** 이 문서를 Opus에 전달하고 §8의 로컬 차단 해소 결과를 받는다. 현재 ZIP의 서버 실행을 권고하지 않는다.
- **[보장하지 않음]** 로컬 계약 테스트와 과거 tier-1 결과는 공식 결과를 보장하지 않는다. `VIDEO_UNKNOWN`, `OFFICIAL_RESULT_UNMEASURED`.

## 1. 범위·증거 강도·버전 고정

**[확인 사실]** `GO2_REAUDIT_PROMPT_ENGINE_151_260908.md`의 SHA256은 `5324d656755e32a3d0e709f8d730b425826be27533b838763ae81d610b85370a`이며 sidecar와 같다. §6에 기재된 17개 파일의 현재 바이트 SHA를 각각 계산했고 17/17 일치했다. 이 확인은 무손상·검토 버전 확인이지 문서 주장에 대한 동의가 아니다.

이하 `Q/`는 `workspace/training/quadruped/`, `K/`는 `workspace/_keep/`다. 원자료 근거는 코드와 회수 JSON/CSV다. 지시서·원장·이전 검토서의 서술은 **감사 대상**으로만 사용했다. 이전 검토의 결론도 보호하지 않았다. 문장/표의 **확인 사실 / 해석 / 미확인 / 제안**을 구분한다.

| 주요 대상 | 이번 검토 SHA256 |
|---|---|
| `Q/go2_fixed_eval_report.py` | `2d74e585f8ae2b676e0167684300fd4b2c8417f5d6e1d1034dccd96bc9083791` |
| `Q/go2_tuning_eval_report.py` | `cacb87ed6fc2f763972339f010b3dd11906558a611713860b8e7855266dbe94c` |
| `Q/go2_eval_telemetry.py` | `d801d9910f2bc920570736c9e26c276f0d7b657dcc38dd5d077cf828468c78ce` |
| `Q/server_run_go2_a017_full_suite.sh` | `5e813d49106a8eecc76231a00416c64b4949b5cf4ce6289259e6bfd1604ec390` |
| `Q/go2_a017_full_suite.zip` | `8d97fc1b1963524dbb402e383ce6c878dc61eed8fe5bd0ce39bc7f45b79ffb93` |

**[확인 사실]** 本監査는 제품 코드·기존 artifact·ZIP을 변경하거나 커밋하지 않았다. 테스트의 임시 출력은 로컬 임시 디렉터리다. 요청된 보고 문서 작성은 분석과 분리한 산출물 단계다. 병렬 코드 검토를 요청했으나 해당 호출은 모델 용량 오류로 결과를 반환하지 않았다. 아래 결론은 메인 감사자가 직접 재현한 것만 포함하며 복수 감사자 합의로 포장하지 않는다.

### 핵심 발견
1. **[확인 사실 / 강]** tier-1의 무효 delta 차단과 legacy G6 차단은 개선됐다. 그러나 `paired()`와 `representative_decision()`에는 같은 보호가 적용되지 않았다(§3 R2·R3).
2. **[확인 사실 / 강]** 새 러너는 `POSTURE_UNMEASURED` JSON도 정상 자세 증거로 받아들인다. 실제 Collector 출력에 러너의 grep을 실행한 종료 코드가 0이었다(§3 추가 결함 C1).
3. **[확인 사실 / 강]** Pilot 69건 2,208,000행에서 OR/AND 차이가 없었다. 그 데이터에 대한 무변경 주장은 이번에 더 강한 증거로 확인됐다. 다만 이것이 모든 계측 조건의 동일성을 증명하지는 않는다(§5.1).
4. **[확인 사실 / 강]** A017의 +3.707916/70과 새 조기기각 결과는 재현된다. 후보 G4·G5의 절대 게이트 미달 원인은 추종이 아니라 생존이다. “둘 다 G3~G7 추종 미달”이라는 설명은 정정해야 한다(§5.3).
5. **[해석 / 강]** 전량 재측정의 목적은 타당하지만 현재 패키지를 안전·완결된 것으로 승인할 근거는 부족하다. 학습 실패 원인을 채점 결함 하나로 환원하는 설명도 여전히 과하다(§6, §8).

## 2. 채점식과 판정 의미

**[확인 사실]** `workspace/PRELIM_RL_GUID.md:60–70,95–104`는 G1~G7 가중치와 생존×추종, 가중합 구조를 제시한다. `Q/go2_fixed_eval_report.py:24–60,108–140`는 exponential tracking, G5 진행도·G6 자세 회복의 추가 제한, case별 곱의 최솟값을 사용한다. 곱셈 구조는 유지되지만 변환식·최악 case 집계·회복 제한은 **내부 proxy 설계**다. 이 감사는 규정집 원본 전체의 재인증이나 운영진의 법적/자격 해석을 수행하지 않았다.

**[해석]** `max_scenario_proxy_regression=0.1`도 공식 곱셈식에서 유도되는 필연적 수치가 아니다. 총점 개선과 국소 손실 허용을 조정하는 내부 위험 선호다. 생존 단독 차단을 곱 차단으로 옮기는 것은 합리적인 수리이지만, 새 규칙에서의 성공을 과거 사전등록 규칙 자체의 계산 오류와 동일시하면 안 된다. A017은 **과거 생존 제약의 기회비용을 보여주는 사례**이자 **변경된 규칙의 사후 재판정 후보**다.

**[확인 사실]** registry의 `score.internal_gates`와 `evaluation_tiers.tier_2_representative`에는 서로 다른 절대/단계 기준이 있다(`Q/config/go2_self_eval_registry.json:47–80`). **[제안]** 측정 적격성 → 상대 스크리닝 → 절대 기준 → 영상/문서 감사 → 제출 판단을 별도 출력해야 한다. 스크리닝에 모든 절대 기준 충족을 강요하면 미완성 기준선의 개선을 다시 막게 된다.

## 3. 표 1 — R1~R8 수리 판정

판정은 이번 세션의 “처리 완료” 주장에 대한 것이다. `부분수용`은 수리가 없었다는 뜻이 아니라 잔여 경로/증거가 있다는 뜻이다.

| ID | 판정 | 원자료·재현 출력 | 이번 수정의 적절성 / 남은 위험 |
|---|---|---|---|
| R1 | **부분수용** | **[확인 사실]** `Q/go2_fixed_eval_report.py:258–293`: 빈 instrument 자체는 거절한다. 그러나 `telemetry_schema_versions=['None']`, `posture_gate_params=['null']`, `measurement_contracts=['None']`인 양 arm에 `instrument_unusable=[]`, `instrument_mismatch=[]`를 재현했다. `:161–178,244–250`에는 evaluator SHA·case별 DR/명령 지문이 없다. | **[해석]** “부재는 일치가 아니다”가 dict 수준까지만 집행된다. 문자열화한 null과 수집기/DR 차이는 여전히 누락된다. 과거 schema 2를 허용하려면 명시적인 legacy 동등성 증명 경로가 필요하며, null을 신형 지문처럼 인정하면 안 된다. |
| R2 | **부분수용** | **[확인 사실]** `Q/go2_tuning_eval_report.py:100–120`의 무효 tier-1은 delta와 scenario_deltas가 null이다. 반면 `Q/go2_fixed_eval_report.py:296–350`의 `paired()`는 무효 status에서도 delta를 계산·출력한다. A017 baseline instrument를 비운 음성 probe: 무효 decision과 `pilot_minus_default=0.05297023461756445` 동시 반환. | tier-1 수정은 적절하다. **[해석]** “어디로도 숫자가 새지 않는다”는 전체 경로 주장은 반증된다. arm 진단 수치 보존 자체와 비교 delta 누출은 구분해야 한다. |
| R3 | **부분수용** | **[확인 사실]** `comparison_blockers()`의 `INADMISSIBLE_ARM_STATUS` 검사는 `Q/go2_tuning_eval_report.py:16,35–41`에 있다. 그러나 `representative_decision():196–224`에는 status/지문 검사가 없다. legacy status·빈 지문·충분한 합성 수치를 넣으면 `INTERNAL_REPRESENTATIVE_PROMOTION_PASS`를 반환했다. | tier-1에서 성능과 적격성을 분리한 점은 적절하다. **[해석]** 대표 평가까지 수리됐다는 확대 주장은 불가. 또한 대표 평가가 worst-product case의 인자만 읽어 다른 case의 floor를 놓칠 여지가 있다(`:199–202`; fixed report `:118–121`). 실제 A017이 대표 평가를 통과했다는 주장은 아니다. |
| R4 | **부분수용** | **[확인 사실]** `Q/go2_eval_telemetry.py:238–249,364–365`의 AND·schema 3·contract 추가 확인. Pilot 69건의 모든 CSV 행에서 양 채널 존재 확인(§5.1). 러너 `:354,376`는 두 정책의 전량 suite를 호출한다. | **[해석]** Pilot의 해당 채널 변경이 실측상 무연산이라는 주장은 수용한다. 이전 “동등성 미증명”은 그때의 증거 상태였으며 “모든 기존 수치가 바뀐다”는 주장이 아니었다. 이번 증거는 좁은 공백을 해소하지만 전체 evaluator 동등성·외부 환경 변수 부재까지 반증하지는 않는다. |
| R5 | **부분수용** | **[확인 사실]** A015/16/18의 큰 음수 delta 및 A017의 보행 baseline을 원본 summary로 재현(§4). 반면 builder `tools/build_go2_a017_full_suite_package.py:13`와 runner `:10`은 아직 “시나리오 곱 회귀 없음”이라고 한다. 실제 G6 delta는 −0.0067562324. | **[제안]** “허용 한계를 넘는 곱 회귀 없음”으로 정정해야 한다. **[해석]** 모든 실패가 심판 문제라는 단일 인과 설명은 불가하다. |
| R6 | **부분수용** | **[확인 사실]** `migrate_gates():54–75,138,175`는 적용 수치와 출처를 기록한다. A017은 `min_total_points_delta`가 원 spec에 있어 대입되지 않았다. A010/13은 적격성 단계에서 차단되어 migration 자체에 도달하지 않는다. 11건 목록과 arm 혼재는 §4 참조. | **[해석]** 사후 gate 값 기록은 개선이다. “독립 사유 4개”는 논리적 범주이지 반환 list 길이와 같지 않다. A010에 실제 비대칭이 있다고 표현하면 틀리다. A013 tier-1 arm의 표본 수도 69가 아니라 7이다. |
| R7 | **부분수용** | **[확인 사실]** builder `:245–281`의 Q1/Q2·훈련 seed 구분은 개선됐다. 그러나 `:262`의 후보 G4/G5 tracking 미달 주장은 반증된다(§5.3). Q1의 “past the gate” 수치는 README에 명시돼 있지 않고 runner `:390–395`는 포장만 한다. | **[해석]** 서술로 정의한 판독 계약과 실제 자동 판독 집행은 다르다. 영상 관찰·20+10 감사는 이 러너가 판정하지 않는다. registry `:77–80`의 tier-2 후 full-suite 원칙과 이번 진단용 직행의 예외를 명시할 필요가 있다. |
| R8 | **부분수용** | **[확인 사실]** runner `:77–97`에 기본 덮어쓰기 거절과 NO_DEADLINE가 생겼다. 하지만 `:221–224`의 eval 지문은 DR/PUSH/env YAML/FALL_*를 포함하지 않는다. `:309–311`의 video 지문은 model/env/argv가 없다. 실제 추출 식으로 DR·PUSH 변경 시 eval hash 동일, model/env 변경 시 video hash 동일을 재현(§7). | **[해석]** 정상 기본 시작은 개선됐지만 resume 완전성은 미확보다. 실패 trap은 최선 회수 시도이지 전원 소실·강제 종료·포장 실패에서도 회수를 보장하는 장치가 아니다. |

### 추가 결함 C1 — `POSTURE_UNMEASURED`를 받는 러너 (높음)

**[확인 사실]** `Q/server_run_go2_a017_full_suite.sh:249`는 `grep -q 'posture_gate_v2' summary.json`이다. `Q/go2_eval_telemetry.py:365`는 정상/결측에 관계없이 `measurement_contract="posture_gate_v2/both_channels_required/no_v1_fallback"`를 쓴다. scanner 없는 StubEnv를 실제 Collector로 100 step 실행한 출력은 다음과 같았다.

```text
survival_proxy_source=POSTURE_UNMEASURED
survival_proxy=null
grep -q posture_gate_v2 summary.json -> exit 0
```

**[해석]** “모든 case가 자세 근거를 요구하고 없으면 실패한다”는 실행 준비 조건은 현재 반증됐다. JSON 키의 정확한 값·수치 존재·완료 상태를 검사해야 한다. 단순 문자열 계약 테스트로는 이 결함이 드러나지 않았다.

### 추가 결함 C2 — 일부 env/step만 관측돼도 전체 생존 수치 생성 (높음)

**[확인 사실]** Collector는 미측정 행의 `upright=True`, 한 행이라도 측정되면 전역 `posture_measured=True`로 둔다(`Q/go2_eval_telemetry.py:244–247`). 마지막 생존은 전체 `num_envs`를 분모로 계산한다(`:352–356`). 2개 env 중 한 env의 높이만 항상 결측인 100-step probe는 `survival_proxy=1.0`, `survival_proxy_source=posture_gate_v2`, `posture_measured=True`였다.

**[해석]** C1만 JSON 키 검사로 고쳐도 C2는 남는다. **[제안]** 사전등록된 허용 결측률과 env/step별 coverage를 집계해 측정 적격성을 판단해야 한다. 이번 probe는 도달 가능한 결함을 증명한 것이며 실제 저장 Pilot CSV에 결측이 있었다는 뜻은 아니다.

## 4. 원자료 11건 재판정

**[확인 사실]** 아래 각 폴더의 `meta/tier1_registry.json`, `meta/G_A0*.json#evaluation.gates`, `evaluation/{baseline_tier1,candidate}/cases/*/*/summary.json`을 직접 읽고 현재 `build_policy` → `tier1_decision`을 호출했다. 모두 tier-1 관측 수는 **arm당 7건**이다. 무효 arm의 자체 숫자는 제출 근거나 유효 비교점수로 표에 싣지 않았다.

| `K/` 아래 run 폴더 | 현재 반환 status | delta /70 | 확인한 차단/해석 |
|---|---|---:|---|
| `go2_g_a010_lin_vel_z_m2` | INTERNAL_MEASUREMENT_INVALID | null | 양 arm schema 1, source 없음, 양 arm legacy G6, 기준 비보행. 양 arm의 기록된 지문은 서로 같지만 사용 불능. |
| `go2_g_a013_flat_orientation_m1` | INTERNAL_MEASUREMENT_INVALID | null | baseline schema 1×6 + 2×1 혼재, baseline legacy G6, 기준 비보행; candidate schema 2×7. |
| `go2_g_a015_pilot_feet_air_time_035` | INTERNAL_EARLY_KILL_FAIL | −30.121931640 | 현재 비교 차단 없음; worst product delta −0.875840760. |
| `go2_g_a016_pilot_ang_vel_xy_m015` | INTERNAL_EARLY_KILL_FAIL | −46.081376175 | 현재 비교 차단 없음; worst product delta −0.924710415. |
| `go2_g_a017_pilot_track_lin_vel_xy_140` | INTERNAL_EARLY_KILL_PASS | +3.707916423 | 현재 비교 차단 없음; worst product delta −0.006756232。 |
| `go2_g_a018_pilot_action_rate_m008` | INTERNAL_EARLY_KILL_FAIL | −44.941368664 | 현재 비교 차단 없음; worst product delta −0.924710415. |
| `go2_g_a020_chain01_lin_vel_z_m2` | INTERNAL_MEASUREMENT_INVALID | null | baseline schema混在・legacy G6・非歩行、candidate schema 2。 |
| `go2_g_a021_chain01_ang_vel_xy_m005` | INTERNAL_MEASUREMENT_INVALID | null | 同上。 |
| `go2_g_a022_chain01_feet_air_time_020` | INTERNAL_MEASUREMENT_INVALID | null | 同上。 |
| `go2_g_a024_ang_vel_xy_m015` | INTERNAL_MEASUREMENT_INVALID | null | 同上。 |
| `go2_g_a025_flat_orientation_m1` | INTERNAL_MEASUREMENT_INVALID | null | 同上。 |

**[해석]** 정확한 요약은 “현재 구현에서 11건 중 7건 비교 차단, 4건 중 1건 새 조기기각 기준 충족”이다. R1의 미완성 지문 검사 때문에 이 4건을 완전한 측정 적격성 인증이나 정책 성능 인증으로 승격하면 안 된다. 다만 A015/16/18의 관측된 수치 저하를 삭제하는 것도 옳지 않다.

**[확인 사실]** `instrument_mismatch():287–290`는 baseline 결함을 만나면 즉시 반환한다. 따라서 `instrument_fingerprint_asymmetric:`라는 prefix 하나에 arm 내부 혼재/사용 불능이 합쳐지며 candidate의 독립 결함은 모두 열거되지 않을 수 있다. A010의 blocker list는 4항목, 나머지 6건은 3항목으로 재현됐다. 이것과 “3/4개 원인 범주”는 서로 다른 집계다.

**[해석]** 저장 arm의 세대 혼재는 확실하지만 그것만으로 실제 단일 실행 중 코드가 바뀌었다고 단정할 수 없다. 이전 case 복사·부분 재측정·resume 혼합도 가능하다. 생성/복사 provenance 없이 “하나의 로봇을 재는 도중 변경”이라는 시간적 인과는 **미확인**이다.

## 5. 표 2 — 필수 주장 5개 검증

| 주장 | 판정 | 독립 재현 / 계획 영향 |
|---|---|---|
| 5.1 OR→AND 무연산 | **부분수용** | Pilot 69건은 CSV 전행에서 확인. A017 후보 7건도 전행 확인. baseline은 7개 summary 중 6개에 해당 로컬 steps.csv가 없어 직접 전행 검증 불가. 전체 83건의 무조건 동등성·환경 변수 부재까지 확장하지 않는다. |
| 5.2 A017 gate 민감도 | **수용(범위 제한)** | delta +3.707916423, 최악 G6 −0.0067562324. product limit 0/0.006이면 조기기각 실패, 0.007/0.1이면 조기기각 기준 충족. A017의 min_total_points_delta는 원 spec 값이며 대입되지 않았다. A010/13은 delta 이전에 무효라 대입으로 성공을 만들지 않는다. |
| 5.3 두 정책 절대 기준 미달 | **부분수용·사유 반증** | 둘 다 INTERNAL_GATE_FAIL는 재현. 후보 G4 tracking .728572, G5 .721683으로 .70 이상이며 생존이 미달한다. 향후 실험의 약한 인수를 잘못 고르는 오류로 이어질 수 있어 우선 정정. |
| 5.4 7건의 복수 차단 사유 | **부분수용** | 7건 차단, 6개 baseline의 schema 1/2 혼재 재현. 그러나 A013의 검사 대상은 69가 아닌 7건. 네 범주를 네 독립 인과로 해석하거나 모두 비대칭이라고 부르면 과장이다. |
| 5.5 A017과 정지 기준선 구분 | **수용** | A017 baseline/candidate `locomotion.verdict=POLICY_LOCOMOTES`; A015/16/18 음수 delta 유지. A017은 정지 기준선 함정의 직접 사례가 아니다. |

### 5.1 전행 검사 결과와 한계

`summary.json`과 같은 디렉터리의 `steps.csv`에 대해 각 행의 `proj_grav_z`가 finite인지, `height_rel`이 비어 있지 않은지 검사했다. 조건 `finite_gravity OR height_present`와 `finite_gravity AND height_present`의 차이도 셌다.

| 원자료 root | summary 수 / height_rel_mean null | CSV 행 수 | 누락 CSV | 관측 CSV의 OR/AND 차이 |
|---|---:|---:|---:|---:|
| `K/go2_pilot_v2_baseline/evaluation/pilot_v2` | 69 / 0 | 2,208,000 | 0 | 0 |
| `K/go2_g_a017_pilot_track_lin_vel_xy_140/evaluation/baseline_tier1` | 7 / 0 | 32,000 | 6 | 0 |
| `K/go2_g_a017_pilot_track_lin_vel_xy_140/evaluation/candidate` | 7 / 0 | 224,000 | 0 | 0 |

**[확인 사실]** Pilot의 각 `cases/seed_{101,202,303}/dr_seed_{seed}/steps.csv`와 같은 seed의 `rough_forward/steps.csv`는 각각 SHA가 같았다. A017 후보 seed 101의 해당 두 CSV는 달랐다.

**[해석]** 동일 CSV는 Pilot의 기록된 두 궤적이 같다는 강한 증거다. 그러나 두 경로 모두 DR가 켜져 있었을 가능성 등까지 배제하여 `NCRC_EVAL_DR`의 과거 환경 변수 부재를 단독 증명하지는 못한다. “height_rel_mean이 null이 아니다”는 최소 하나의 표본을 뜻할 뿐 전행 측정의 증명이 아니다(`Q/go2_eval_telemetry.py:248–249,400`). 이번 Pilot 결론은 평균이 아니라 전행 검사로 지지한다.

**[해석]** Pilot 전량 재측정은 원자료 부족 때문에 유일하게 가능한 선택은 아니다. 고정된 새 수집기와 조건을 한 번에 비교하려는 보수적 선택으로는 타당하다. 추가 GPU “약 30분”은 69×28초≈32.2분이라는 가정 기반 추정이며 설치·시작·실패·회수 시간을 포함한 실측 상한이 아니다. 잔여 예산 확인 뒤 비용과 이득을 판단해야 한다.

### 5.3 생존과 추종을 분리한 A017 진단

**[확인 사실]** 아래는 A017 run의 `build_policy(...).scenarios[G].survival_proxy/tracking_proxy` 재현값이다. arm당 해당 scenario는 1 case·seed 101이다.

| 시나리오 | Pilot 생존 / 추종 | A017 생존 / 추종 | 후보의 .95/.70 하한 미달 인수 |
|---|---:|---:|---|
| G3 | .812500 / .596709 | .906250 / .628191 | 생존·추종 둘 다 |
| G4 | 1.000000 / .553326 | .781250 / .728572 | **생존** |
| G5 | .718750 / .569612 | .718750 / .721683 | **생존** |
| G7 | .937500 / .597477 | 1.000000 / .663233 | **추종** |

**[해석]** “절대 기준 실패”라는 같은 결과에서도 개선할 인수가 다르다. 이후 후보 선택은 전량 재측정에서 최대 가중 감점과 약한 인수를 다시 구한 뒤 해야 한다. G-A027에서 두 arm을 새로 재므로 과거 tier-1 결과를 미래 결과로 확정할 수 없다.

**[미확인]** 영상 관찰과 설계 의도/리포트 감사 점수는 이 재감사에서 부여하지 않았다. runner는 영상 7건을 저장하고 `VIDEO_UNKNOWN`을 기록할 뿐(`:378–392`), 20+10을 채점하지 않는다. 따라서 이 실행만으로 Q2의 모든 조건을 답하지 못한다.

## 6. 왜 H1보다 Go2가 난항이었는가 — 이번 증거로 말할 수 있는 범위

**[확인 사실]** Go2에는 ① 비보행 기준선, ② 서로 다른/혼재한 생존 측정, ③ 생존 단독 조기기각, ④ 실제로 큰 수치 저하를 보인 후보가 함께 있었다(§3–5의 원자료). **[해석]** 관측 오염과 탐색 정책의 문제, 학습 결과의 문제가 복합적으로 작용했다는 설명이 현재 증거에 가장 잘 맞는다. “로봇 학습은 실패하지 않았고 채점만 실패했다”는 배타적 설명은 지지되지 않는다.

**[미확인]** H1은 정지 균형이 어려워 같은 함정이 발생하지 않았다는 기체역학 가설은 이번 Go2 JSON으로 입증할 수 없다. H1의 기준선 보행/정지 telemetry, 평가기 버전, 동등 예산·학습 seed·실험 판정 이력까지 맞춰야 비교 인과를 주장할 수 있다. H1과 Go2 reward의 직접 전용도 이 근거로 정당화되지 않는다.

**[해석]** 정지 기준선을 검색의 incumbent로 쓰지 않는 조치는 합리적이다. 다만 정지 정책을 동일 평가기로 재는 진단용 대조군 자체가 과학적으로 무효인 것은 아니다. `baseline_does_not_locomote`는 엔진의 **운영상 비교 금지 정책**이며 evaluator 비대칭과 같은 종류의 측정 오류는 아니다(`Q/go2_tuning_eval_report.py:43–47`).

## 7. 실행 검증·재현 방법

### 실행한 계약 테스트

**[확인 사실]** 아래 6개 파일을 `python -B tools/test_go2_<이름>_contract.py`로 실행했고 각각 종료 코드 0이었다. bash가 필요한 테스트에는 Git Bash 경로를 PATH에 추가했다.

```text
scoring_repair       RC=0
a017_full_suite      RC=0  (bash -n 및 현재 ZIP 검사 포함)
posture_survival     RC=0
default_vs_pilot     RC=0  (6 tests)
evaluator_v2         RC=0  (3 tests)
terrain_5k          RC=0
```

**[미확인]** 사용자가 말한 “9종 전부”를 이번 세션에서 그대로 재인증하지 않았다. `test_go2_tuning_engine_contract.py:392–405`, `test_go2_feet_air_time_020_contract.py:102`, `test_go2_track_lin_vel_120_contract.py:122`는 builder를 호출해 기존 ZIP을 쓸 수 있어 제외했다. 이들까지 검증하려면 격리된 복제 작업공간에서 실행해야 한다. 6종의 종료 코드 0은 C1/C2/R1~R3/R8 음성 probe의 실패를 상쇄하지 않는다.

### 기존 11건 및 A017 gate 재현

다음은 저장 자료를 읽기만 하며 보고 JSON을 덮어쓰지 않는다. 리포터 CLI main은 파일을 쓰므로 호출하지 않았다.

```python
import json, sys
from pathlib import Path
sys.path.insert(0, 'workspace/training/quadruped')
from go2_fixed_eval_report import build_policy
from go2_tuning_eval_report import tier1_decision
for k in sorted(Path('workspace/_keep').glob('go2_g_a0*')):
    reg = k / 'meta/tier1_registry.json'
    specs = list(k.glob('meta/G_A0*.json'))
    if not reg.is_file() or not specs:
        continue
    b = build_policy(k/'evaluation/baseline_tier1', reg, {})
    c = build_policy(k/'evaluation/candidate', reg, {})
    g = json.loads(specs[0].read_text(encoding='utf-8'))['evaluation']['gates']
    d = tier1_decision(b, c, g)
    print(k.name, b['instrument'], c['instrument'], d)
    if 'a017_' in k.name:
        for limit in [0, .006, .007, .1]:
            print(limit, tier1_decision(b, c, dict(g,
                  max_scenario_proxy_regression=limit))['status'])
```

### resume 음성 검사

**[확인 사실]** runner의 eval `fingerprint=$(...)` 블록(`:221–225`)과 video `vfingerprint=$(...)` 블록(`:310–311`)을 그대로 추출해 Git Bash에서 실행했다. play/IsaacLab/runner 전체를 실행하지 않았다. 고정 입력은 model SHA=`model`, evaluator SHA=`evaluator`, scenario=G7, case=dr_seed_101, seed=101, cmd=`(play.py same-argv)`다.

| 조작 | 결과 |
|---|---|
| DR_MODE=0/PUSH_X=.5 → DR_MODE=1/PUSH_X=9, EVAL_STEPS=1000 고정 | 두 eval hash 모두 `dd36ae83a8b0c0773f4207dde3875736a30d3af58f4025a32c1e92d5b06bd735` |
| EVAL_STEPS=1000 → 1001 | `80370e0974ab44a495e8714865c4974ea6a6152e3e12e4f1519ae66a58da79c9`로 변경 |
| VIDEO_STEPS=500·DR_MODE=1 고정, model/env=policy1 → policy2 | 두 video hash 모두 `6e8fd091bd8d416c544272f1c6886a35700eb8ad2ff77031a2aba74e89d0de08` |

**[해석]** EVAL_STEPS 추가는 실제로 작동한다. 반면 DR/PUSH·정책/설정 변경 누락은 여전히 존재한다. 고정 현재 패키지가 자동으로 서로 다른 모델을 쓰고 있다는 뜻은 아니며, **변경 후 resume 안전성** 주장에 대한 음성 테스트다. eval 재측정은 `:231`에서 기존 case 디렉터리를 삭제하므로 이전 자료의 별도 보존도 고려해야 한다.

## 8. 실행 준비 판정 및 다음 단계

### 준비 조건 7개 판정

| 항목 | 판정 | 근거·한계 |
|---|---|---|
| 1. 학습 진입 없음 | INTERNAL_GATE_PASS | runner `:68`의 train.py는 동시성 가드이며 실제 실행 배열은 play.py(`:205–215,323–332`). ZIP 안 train.py 포함은 실행 증거가 아니다. |
| 2. 정책 SHA 불일치 중단 | INTERNAL_GATE_PASS | runner `:268–270`, builder `:124–138`의 model/env SHA 검사. 이번 판정은 정적 실행 경로와 패키지 계약에 한정. |
| 3. 모든 case의 자세 증거 요구 | **INTERNAL_GATE_FAIL** | 실제 결측 Collector JSON이 grep을 통과(C1), 부분 결측도 숫자 생성(C2). |
| 4. 기본 재실행 기존 결과 보호 | INTERNAL_GATE_PASS | 정상 외부 실행 경로 `:77–87`에서 기존 KEEP/ZIP 존재 시 명시 discard 없으면 중단. resume/직접 --inner 실행까지의 무조건 보장은 아님. |
| 5. resume 설정 동일성 | **INTERNAL_GATE_FAIL** | §7 음성 probe. eval DR/PUSH/FALL/env, video model/env/argv 누락. |
| 6. 두 arm 동일 evaluator | INTERNAL_GATE_PASS(고정 패키지 범위) | builder `:159–165`의 동일 바이트 source, 패키지 계약 종료 코드 0; runner `:276,391–392`가 SHA 기록. 단 report의 실제 지문 비교에는 이 SHA가 포함되지 않는다(R1). |
| 7. 실패 시 부분 회수 | INTERNAL_GATE_INCONCLUSIVE | runner `:106–114`가 비정상 EXIT 때 PARTIAL 시도. `:55`의 IsaacLab Python 포장 실행을 실제 서버에서 강제 실패 테스트하지 않았다. SIGKILL/서버 소멸/포장 실패에 대한 보장은 없다. |

### 최종 결론

**현재 패키지의 서버 실행 준비: `INTERNAL_GATE_FAIL`.** 이는 정책 성능 판정이 아니라 C1/C2 및 resume 음성 검사로 확인된 실행 계약 결함에 대한 판정이다. 신규 학습 대신 A017/Pilot 고정 정책을 재평가하려는 방향은 유지할 수 있으나, 현재 ZIP 그대로 실행을 승인하지 않는다.

| 우선순위·등급 | 다음 행동 / 종료 조건 | 시간·실패 대안 |
|---|---|---|
| P0 · 개선(평가 신뢰성) | C1의 JSON 정확값 검사, C2의 env/step 결측 적격성, R1~R3의 공통 측정 차단을 각각 음성 테스트로 재검증 | **[제안]** GPU 0. 로컬 수리 단계. 미해소 시 새 GPU 측정 보류; 현재 자료는 진단용으로 보존. |
| P0 · 개선(회수 안전성) | eval/video 지문에 실행에 영향을 주는 설정을 포함하고 변경/손상/부분 완료 resume을 거절하는 테스트 | **[제안]** GPU 0. 해결 전에는 resume 보장 주장 철회. 기존 회수물 덮어쓰기 금지. |
| P1 · 조사 | 실제 GPU 잔여 시간 및 서버 초기화/시간 제한 확인 | **[미확인]** 현재 잔여량은 로컬 코드로 알 수 없다. 확인 전 25시간을 예산으로 사용하지 않는다. |
| P1 · 필수(제출 무결성) | 과거 이력 백업 비활성화의 자격 영향에 대한 운영진 답변·원문/대상 run 확보 | **[미확인]** 자격 판정은 본 감사 권한 밖. 제출 무결성 미확정은 즉시 해소 대상이며 최종 후보 승급 근거로 숨기지 않는다. 이것을 읽기 전용 평가의 기술적 불능과 혼동하지 않는다. |
| P2 · 개선 | 수정된 패키지 고정 후 두 arm 동일 평가. 먼저 공통 소수 case를 smoke하고 전량 측정으로 확장하는 진단 예외를 등록 | **[제안]** 기준 예산은 runner의 1h45m 추정이지 상한이 아니다. 첫 case 실측으로 남은 예상시간을 다시 계산하고 별도 회수 여유를 남긴다. 시간 부족/오류면 부분 회수; 불완전 총점으로 승급 금지. |
| P3 · 개선 | Q1의 수치 gate를 명시한 spec으로 재판정. 최대 가중 감점·약한 인수 표 갱신 후 단일변수 후보 선택 | **[제안]** 상대 개선만 있으면 검색 기준 후보, 절대·영상·문서까지 충족한 경우에만 최종 후보 검토. 낮은 결과면 Pilot 유지하되 reward 방향 전체를 기각하지 않는다. |

**[미확인 목록]** 현재 잔여 GPU 시간, 과거 백업 비활성화의 실제 운영진 영향, G-A027 서버 실행/회수 결과, 정책 생성 당시 배포 원본 무결성의 완전한 재감사, H1 대비 정량 인과, A017 baseline의 누락 CSV 6건과 원본의 대응, G-A027 영상 관찰·문서 30점, 실제 서버 PARTIAL 복구, 제외한 계약 테스트 3종의 이번 버전 실행 결과.

**[제안 — Opus에 요청]** R1~R8와 C1/C2별로 현재 pinned SHA에서의 재현 여부를 먼저 답하고, 수정했다면 새 SHA·음성 테스트·실행 출력을 별도로 제시해 달라. “기존 테스트가 모두 성공했다”는 답 대신 위 반례가 실제로 거절되는지 증명해 달라. Pilot 전행 증거가 좁은 OR/AND 우려를 해소한 것은 수용하되, 그것을 전체 evaluator·과거 환경의 동일성 증명으로 확장하지 말아 달라.
