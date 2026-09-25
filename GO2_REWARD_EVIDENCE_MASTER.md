# Go2 Reward Evidence Master

## G-A044-READOUT-20260924 — 최신 회수 근거
- lin_vel_z_l2 -2→-1.75(seed42/eval900): ARTIFACT_VERIFIED / INTERNAL_GATE_FAIL. 내부proxy42.528610→38.893793/70(-3.634817). G3/G6 보호 악화, G2 left seed101 생존 한도 초과. A033 유지; -1.75는 이제 OBSERVED(실패 조건 한정), 더 이상 미측정 후보가 아니다.
- 10cm≥2단43→62/96이나 자세낙상34→65; 15cm≥2단0→0(A043는77). 이 표본에서 중간값=중간성능 가설 반박. 이번 -1.75 후보 미만족; lin_vel_z 항 전체 최적성/독립seed 재현은 미측정. 아래 §1-a의 -1.75 미측정 문구는 발행 당시 이력으로 보존하며 최신 판정은 이 행을 따른다.
- report READ_MATCHED(원 학습 대응):20.13@758,terrain4.92,학습낙상17.1%,std.576,report800≠평가900. VIDEO_UNKNOWN. 근거 `workspace/training/quadruped/reports/GO2_G_A044_READOUT.md`; 다음 분석 `workspace/training/quadruped/upload/plan/GO2_POST_A044_POLICY_ANALYSIS_20260924.md`. 자동 이분탐색 대신 독립seed 대칭재현 권고; 실행 승인/새 ZIP 아님.

## GO2-POST-A043-PLAN-20260922
- User requested the next plan, not package execution. Saved: `workspace/training/quadruped/upload/plan/GO2_POST_A043_PLAN_20260922.md`.
- Planned candidate: A033 lin_vel_z_l2 -2.0 -> -1.75 only; seed42/1000iter/eval900; full69 required, G2 bilateral protection, G6 all-direction reporting/protection. Unmeasured exploratory interpolation; A033 retained.
- No new ID reserved, package issued, server execution, or GPU usage. This plan supersedes the historical next-action to run A043, not its immutable artifacts or failed verdict.

## G-A043-READOUT-20260922
2026-09-22 G-A043 RECOVERY VERIFIED: ARTIFACT_VERIFIED / INTERNAL_GATE_FAIL; A033 retained. Full69, sentinel5, new videos8, reused4 and original report acquired. Internal proxy 42.528610 -> 44.624542/70 (+2.095932 < required2.53); G2 weighted loss4.636928; stairs improve but protection fails. Server shutdown permitted. Readout: workspace/training/quadruped/reports/GO2_G_A043_READOUT.md; verification: workspace/server_returns/G-A043_LOCAL_VERIFY.json. This supersedes A043 unexecuted status only.
- Classification: investigation; training 58m19s, campaign budget remaining UNMEASURED. No new server run authorized or performed by this review. Raw harvest retained without canonical merge.

> 2026-09-22 다음 계획: A033 위 lin_vel_z_l2 -2.0→-1.5, 1000iter/평가900 정보 실험을 선택(아직 미측정). 계획 `workspace/training/quadruped/upload/plan/GO2_POST_A042_PLAN_20260922.md`. A042 상향 실패로 track1.5 유지. 기존 G-A037(-1.0) 사양을 재승인/수정한 것이 아니다. 새 값은25% 완화 설계점이지 최적값 아님. spec_margin 결과0.1480, climb+0.0258/sway−0.0470/push−0.0386은 고정행동 산술이며 성능예측량이 아니다. G3/G6 위험과 이미 높은 오르기 두 항 보상합이라는 반대 근거를 공개하고, 기존 계획 screening+G6 양방향 생존/추종/낙상 보호를 모두 요구한다. 후보 번호/ZIP/새 학습은 없음.

> 2026-09-21 A042 최신 판독: track1.5→1.6 단일변경·seed42·평가900은 **INTERNAL_GATE_FAIL**. 10cm ≥2단43→0/96, 낙상34→85/96; 15cm ≥1단4→0/96, 낙상90→94/96; 험지 전진 낙상4→20/96. 이번1.6 후보 **미만족**; A033 유지. A033 위 추가 상향 효과는 이제 이 조건에서 관측됐으며 개선 가설은 반박됐다. 독립 학습 seed/직접 기전/1.5 최적성은 여전히 미확정. ARTIFACT_VERIFIED, 원 학습 report READ_MATCHED, 영상은 표본 관찰. 근거 `workspace/training/quadruped/reports/GO2_G_A042_READOUT.md`, `workspace/server_returns/G-A042_LOCAL_VERIFY.json`. 아래 미실행/추가상향 미측정 기록은 이 행으로 정정한다.

> 2026-09-21 G-A041 회수 판독 반영: 산출물은 검증됐고(ARTIFACT_VERIFIED) 판정은 **INTERNAL_GATE_FAIL**이다(artifact/stage faults `0`, sentinel `5`/`5`). 10cm 오르기 ≥1단 `90`→`34`/96 · ≥2단 `43`→`8`/96, 자세 포함 낙상 `34`→`93`/96. **G-A033 유지**, 후보는 승급하지 않는다. `ang_vel_xy_l2` 완화가 계단을 돕는다는 이번 방향 예측은 반박됐다 — 모든 seed·가중치 구간의 일반법칙이나 직접 기전은 확정하지 않는다. 15cm 계단 기록이 회수되지 않아 회수 완결은 **PARTIAL**이고 공식 `/70` 점수는 미측정이다. 상세 `workspace/training/quadruped/reports/GO2_G_A041_READOUT.md`와 `GO2_G_A041_LOCAL_VERIFY.json`. 새 서버 실행은 없다. (이 줄은 2026-09-21 한글이 깨진 채 저장돼 판독문 원문에서 다시 썼다.)


## 0. 목적

Go2 reward 값의 **출처**, 실제 **성능 증거**, G1~G7 직접 측정 범위와 한계를 분리한다.
코드 주석이나 강좌의 예시는 후보 출발점이며 NCRC 최적값이 아니다.

### G-D-REWARD-KNOWLEDGE-20260920 — 습득 정보와 미습득 정보 기반 정책

사용자 결정: 보상 변경으로 이미 얻은 정보와 아직 얻지 못한 정보를 구분하여 후보와 실험 목적을 정한다. 기존 §1-a의 실행 이력·기준선은 유지한다. 이 절은 정보 수준을 해석하는 최신 계약이며 새 가중치 선택이나 실행 지시가 아니다.

**항 전체가 아니라 `기준선 × 변경 전후 값 × 학습 seed/iter × 평가 조건 × 측정 범위`별로 분류한다.** 아래 표는 §1-a 이력의 요약이며 새 원자료 재분석이 아니다. 각 상세 수치·정책 식별자는 해당 이력과 원 artifact를 따른다.

| 항·방향 | 습득한 정보(해당 실험 조건 한정) | 미습득 정보 / 다음 질문 |
|---|---|---|
| track_lin_vel_xy_exp 상향 | A017·A033의 같은 계측 전수 비교 결과가 있음 | 다른 학습 seed 재현, A033 위 추가 상향 효과, 직접 기전은 미확정 |
| feet_air_time 상·하향 | A015 상향 및 A031·A032 하향에서 불리한 평가 결과 관측 | 0.2의 일반적 최적성, A033 위 동일 효과, 발 높이 개선 효과는 미확정 |
| ang_vel_xy_l2 강화 | A016 결과와 A038의 험지 옆걸음 개선·10cm 계단 악화 관측. A038 회수/판정 공백은 유지 | 완화 방향 효과 미탐색. 강화의 반대 효과를 완화의 사실로 쓰지 않음 |
| action_rate_l2 완화 | A018의 불리한 결과 관측 | 강화 방향 및 다른 기준선 효과, 악화 기전은 미확정 |
| lin_vel_z_l2 / flat_orientation_l2 | 과거 실행 기록과 수식은 있음 | 보행 기준선에서 비교 가능한 유효 변경 효과 부족. 과거 비대칭 계측 결과로 효과를 확정하지 않음 |
| dof_acc_l2 / dof_torques_l2 / track_ang_vel_z_exp / dof_pos_limits | 원문 역할·설정 정보가 있음 | 단일변경 결과 없음. 항 크기나 수식만으로 개선 방향 확정 금지. 허용 변경 경로는 R-6 별도 확인 |

모든 항에 다음 네 칸을 별도로 유지한다: **수식·조건 확인 / 재학습 후 결과 관측 / 기전 원 채널 직접 측정 / 독립 학습 seed 재현**. 하나의 '알고 있음' 등급으로 합치지 않는다. 현재 독립 학습 seed 재현은 미확보이며 평가 seed 반복과 구별한다. 직접 채널을 확인하지 않은 기전은 UNKNOWN이다. 기존 대리 측정치는 GO2_DATA_STANDARD.md의 한계를 따른다.

정책 수립 순서:
1. 목표 시나리오의 원자료 → 항의 원문 수식·좌표계 → 이미 관측한 변경 결과와 반례 → 아직 모르는 질문을 연결한다.
2. 후보마다 `유지할 관측`, `새로 얻을 정보`, `개선 가설`, `경쟁 가설`, `반증 관측`, `보호 시나리오`, `비용·회수·R-6`를 기록한다. 미탐색이라는 이유만으로 우선하지 않고, 특정 조건에서 실패한 방향도 근거 없이 반복하지 않는다.
3. 실험 결과는 **성능 판정**과 **정보 획득 판정**을 분리한다. 성능이 악화돼도 가설을 반박하는 유효 정보가 생길 수 있지만 후보 승급은 하지 않는다. 필수 채널/조건이 빠지면 기전 정보는 INCONCLUSIVE다.
4. 동일 행동의 가중치 재계산은 산술 효과만 보인다. 실제 학습 정책 변화와 구별한다. 커리큘럼 변화는 보상 변경에 따른 매개 경로일 수 있으므로 함께 기록하되 독립 물리 기전의 증명으로 쓰지 않는다.
5. 알려진 사실로 기준선을 유지하면서, 의사결정을 바꿀 미지의 효과를 단일변수 실험으로 확인한다. G5 최저점은 대상 선정 근거이지 특정 항이 가장 쉽게 개선된다는 증거가 아니다. ang_vel_xy_l2 -0.04는 탐색 가설이며 이 결정으로 다음 실행값에 승격하지 않는다.

증거 관리자는 각 인계에서 네 칸과 위 경계를 확인한다(MANUAL_PM_DISPATCH). 역할 파일·기존 생성 문서의 일반적 기전 표현은 이 계약과 데이터 표준을 넘는 근거로 사용하지 않는다. 전체 과거 산문의 정정 완료를 뜻하지 않는다.

## 1. 현재 정책 역할

2026-09-14 정정(G-D113·G-D184 반영, 캠페인 감사 P1). 현재 식별자의 정본은 루트 `GO2_NOW.md` §1이다.

- 동결 스크리닝 기준선: **G-A033** — A017 + `track_lin_vel_xy_exp 1.4→1.5`, model SHA `ccd60e19…6044`, env SHA `ac43a435…d375`, 69case **42.52861/70**(iter 900 고정, 내부 proxy). 승급 결정 **G-D-BASELINE-A033-20260916**: 총점이 A017보다 +2.76이고, 기각 사유였던 비열등 한도 0.5/70이 실측 잡음 sd 1.018/70의 절반이었다. **G-A033의 2단계 FAIL 판정 기록은 유지한다**(판정 번복이 아니라 기준선 선택의 새 결정이다).
- 이전 기준선: **A017**(`0563deff…95a4`, env `41050c08…01ff`, 69case 39.76495/70, G-D184, 2026-09-14~09-16). 그 이전 Pilot-01(`c4d78adf…af8d`, 같은 계측 69case 33.67/70). Default-01(`99ceeaa1…4676`)과 Chain-01은 보행하지 않아 스크리닝 기준선에서 제외됐다(G-D113). 아래 "Default-01" 표기는 과거 계보 설명이다.
- **Default-01은 Isaac Lab 기본값이 아니다.** 배포 시작값은 IL Go2 rough에서 세 항이 다르다: `track_lin_vel_xy_exp` 1.0(IL 1.5) · `lin_vel_z_l2` −3.0(IL −2.0) · `ang_vel_xy_l2` −0.08(IL −0.05). 목표 보상을 낮추고 안정화 벌점을 키운 조합이라 R-Sci-4의 정지 편법 배합과 일치한다. **IL Go2 rough 정확값으로 학습한 회차는 25건 중 0건이다**(2026-09-16 확인).
- 제한: 학습 seed 42 하나. 독립 학습 seed 재현은 한 번도 없다.
- 260901 원문(SUPERSEDED): 실험 기준선 Default-01, 비교군 Pilot-01(reward 18.02@972, terrain 3.94, 학습 낙상 진단 13.8%, std 0.499, 네 reward 동시 변경).

## 1-a. 다이얼 시도 이력 — 정본 (2026-09-14 신설)

새 후보 사양서는 이 절의 해당 항 행을 인용해야 한다(`dial_history_ref`). `tools/test_go2_canonical_consistency.py`가
아래 요약 표의 "현재 상태"와 §2 "현재 성능 판정" 칸의 일치를 검사한다.
**유효** = 두 arm이 같은 evaluator 지문(posture_gate_v2)으로 채점됐고 기준선이 보행한다(G-F160, G-F170~172).
모든 결과는 학습 seed 42 하나의 `exploratory` 결과다.

### 요약 (현재 상태)

| reward | 현재 상태 | 보행 기준선 유효 시도 | 결정 |
|---|---|---|---|
| `track_lin_vel_xy_exp` | 채택 | 1.2→1.4 채택(A017) | G-D184 · 1.4→1.5는 G-A033 2단계 FAIL(3항 비열등 초과, 2026-09-15, **판정 기록 유지**)이나 그 한도 0.5/70이 실측 잡음 sd 1.018의 절반이어서 **G-D-BASELINE-A033-20260916으로 1.5를 기준선 승급**. 현재 값 **1.5 = IL rough**. 상향 `1.6`은 **기각**: G-A042 실행·회수(2026-09-21) ARTIFACT_VERIFIED / INTERNAL_GATE_FAIL — 10cm ≥2단 `43→0`/96·자세 낙상 `34→85`/96(`reports/GO2_G_A042_READOUT.md`). A033 유지 |
| `feet_air_time` | 기각(상향 0.35) | 0.2→0.35 기각(A015) | G-D73 · 하향 0.01·0.1도 1단계 FAIL(G-A031·A032, 2026-09-15). 계획 §6-3에 따라 0.2 유지 |
| `lin_vel_z_l2` | 기각(완화 −1.5·−1.75) | `−2.0→−1.5` 기각(G-A043) · `−2.0→−1.75` 기각(G-A044) | G-D116 · G-A037(`−2→−1`, G-A033 위) 패키지는 **보류**: 추론 사슬에 반대 행(기반 데이터 S5)이 있다(2026-09-17). 이 다이얼은 이제 걷는 기준선 위에서 **세 값이 측정됐다** — `−2.0`(G-A033, 42.52861/70) · `−1.75`(G-A044, 38.89379/70) · `−1.5`(G-A043, 44.62454/70). 둘 다 INTERNAL_GATE_FAIL 이고 A033 유지다. **계수기가 서로 다른 말을 한다**: 계단에 오른 로봇 수는 세 점에서 단조로 늘고(10cm ≥2단 `43→62→94`/96, 15cm ≥1단 `4→39→88`/96) 자세 낙상 수는 가운데 값에서만 솟는다(계단10cm `34→65→17`, 험지 옆걸음 `59→80→24`, 밀침 4방향 `22→66→10`/384). 총점은 낙상 쪽을 따라가 비단조다. 원자료 `reports/evidence/go2_seed_pair_20260924/DIAL_THREE_POINTS.csv`·`MONOTONICITY.csv`. 이 어긋남이 다이얼의 성질인지 학습 경로 갈라짐인지는 **학습 seed 대조군이 0건이라 가를 수 없고**, 그것을 재는 회차가 G-A045·G-A046(2026-09-24, seed 43 대칭 쌍)이다 |
| `ang_vel_xy_l2` | 기각(강화) | -0.05→-0.15 기각(A016) · `-0.05→-0.08` 판정 없음(G-A038, G-A033 위: 험지 옆걸음 개선, 10cm 오르기 붕괴). 완화 `-0.04`도 **기각**: G-A041 실행·회수(2026-09-21) INTERNAL_GATE_FAIL — 10cm ≥1단 `90→34`/96·자세 낙상 `34→93`/96, 15cm 기록 미회수로 회수 완결은 PARTIAL(`reports/GO2_G_A041_READOUT.md`) | G-D77 · G-A038 승급 후보 아님(2026-09-17, `reports/GO2_G_A038_READOUT.md`) |
| `action_rate_l2` | 기각(완화) | -0.01→-0.008 기각(A018). 강화는 미탐색 | G-D81 |
| `flat_orientation_l2` | 미탐색 | 없음 | G-D104 · G-A040(`0.0→−0.5`, G-A033 위) 사양은 **보류**: 추론 사슬에 반대 행 6건(구간 부분 margin의 정책 간 부호 엇갈림, IL Go2 rough가 이 항을 험지에서 끈다)이 있다(2026-09-19) |

이전 판 요약 행(실행된 사양 G-A038이 인용한 그대로, 2026-09-17 G-A038 결과로 위 행을 갱신): `` `ang_vel_xy_l2` | 기각(강화) | -0.05→-0.15 기각(A016). 완화는 미탐색 | G-D77 ``

이전 판 요약 행(2026-09-24 A044 회수로 위 행을 갱신하기 전의 줄): `` | `lin_vel_z_l2` | 기각(완화 −1.5) | `−2.0→−1.5` 기각(G-A043) | G-D116 · G-A037(`−2→−1`, G-A033 위) 패키지는 **보류**: 추론 사슬에 반대 행(기반 데이터 S5)이 있다(2026-09-17). 절반 폭 `−1.5`는 **G-A043으로 측정됐다**(2026-09-22 실행·회수, ARTIFACT_VERIFIED / INTERNAL_GATE_FAIL): 계단은 크게 올랐으나(15cm ≥2단 `0→77`/96) G2 복합 우회전 보호가 깨져 총점 `+2.096/70`이 사전등록 `+2.53`에 미달했다. A033 유지. 이 회차로 이 다이얼의 걷는 관측값이 `−2.0`·`−1.5` 둘이 됐고, 중간값 `−1.75`는 `BETWEEN_OBSERVED`이며 미측정 — 첫 사양 G-A044(2026-09-22, 계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md`) | ``.

이전 판 요약 행(보류 중인 사양 G-A037이 인용한 그대로, 2026-09-22 G-A043 회수로 위 행을 갱신): `` `lin_vel_z_l2` | 미탐색 | 없음 | G-D116 ``. 발행된 사양의 `dial_history_ref`는 **발행 시점의 줄**을 글자 그대로 인용하고 발행 ZIP은 불변이므로, 갱신할 때 옛 줄을 지우지 않고 여기에 보존한다.

### 전체 시도 (`workspace/_keep/*/reports/TIER1_DECISION.json` 원값)

| work | reward·값 | 기준선 | 지문(기준선/후보) | 기준선 보행 | 유효 | delta/70 | 결정 |
|---|---|---|---|---|---|---:|---|
| G-A015 | feet_air .2→.35 | Pilot-01 | v2/v2 | ✓ | ✓ | −30.12 | G-D73 기각 |
| G-A016 | ang_vel_xy −.05→−.15 | Pilot-01 | v2/v2 | ✓ | ✓ | −45.12 | G-D77 기각 |
| G-A017 | track 1.2→1.4 | Pilot-01 | v2/v2 | ✓ | ✓ | +3.71 (69case +6.09, A027) | G-D184 채택 |
| G-A018 | action_rate −.01→−.008 | Pilot-01 | v2/v2 | ✓ | ✓ | −44.40 | G-D81 기각 |
| G-A031 | feet_air .2→.01 | A017 | v2/v2 | ✓ | ✓ | 1단계만: 표적 9case proxy −.022 | 1단계 FAIL(2026-09-15) |
| G-A032 | feet_air .2→.1 | A017 | v2/v2 | ✓ | ✓ | 1단계만: 표적 9case proxy −.437 | 1단계 FAIL(2026-09-15) |
| G-A033 | track 1.4→1.5 (iter 900 고정) | A017 | v2/v2 | ✓ | ✓ | 69case +2.76 (39.76→42.53), 표적 +.174 | 2단계 FAIL: G3 가중 손실 .743>.5, G2 left 생존 −1/16(2 seed) (2026-09-15) |
| G-A007 | feet_air .01→.20 | Default-01 | v1/v1 | ✗ | ✗ | +3.87 (69case) | 정보 없음 |
| G-A009 | track 1.0→1.2 | Default-01 | v1/v1 | ✗ | ✗ | +3.09 | 정보 없음 |
| G-A010 | lin_vel_z −3→−2 | Default-01 | v1/v1 · v1/v2 | ✗ | ✗ | +2.26 · −7.63 | G-D116 철회 |
| G-A013·G-A025 | flat 0→−1 (비트 동일 재실행) | Default-01 | 혼재/v2 | ✗ | ✗ | −1.43 | G-D104 판정 보류 |
| G-A024 | ang_vel_xy −.08→−.15 | Default-01 | v1/v2 | ✗ | ✗ | −17.13 | G-D116 철회 |
| G-A020 | lin_vel_z −3→−2 | Chain-01 | v1/v2 | ✗ | ✗ | −18.18 | G-D116 철회 |
| G-A021 | ang_vel_xy −.08→−.05 | Chain-01 | v1/v2 | ✗ | ✗ | −6.61 | G-D116 철회 |
| G-A022 | feet_air .01→.20 | Chain-01 | v1/v2 | ✗ | ✗ | −13.73 | G-D116 철회 |
| G-A001 | 4항 동시(Pilot-01 생성) | 배포 시작값 | — | — | ✗ | — | 단일변수 아님 |
| G-A038 | ang_vel_xy `−.05→−.08` | G-A033 | v2/v2 | ✓ | ✓ | 1단계만, 판정 필드 없음: 표적 9case proxy `+.088` · 10cm 오르기 묶음 `−.140` | INCONCLUSIVE(러너 영상 로그 결함, 2026-09-17). 새 규칙 fact_rules_v1이면 1단계 FAIL(묶음 하한·오른 로봇 수) |
| G-A037 | lin_vel_z `−2→−1` | G-A033 | — | ✓ | — | **미실행** | 보류(추론 사슬 `HOLD_CONTRADICTED`) |
| G-A035 | 학습 길이 1000→1500 (reward 무변경) | G-A033 | v2/v2 | ✓ | — | **미실행** | 사전등록 계획 §15. reward 다이얼이 아니라 학습 길이 회차다(IL go2_rough 1500). R-6 밖이라 G-D-BASELINE-A033-20260916과 함께 사용자 승인 |
| G-A039 | dof_acc `−2.5e-07→−1.25e-07` | G-A033 | — | ✓ | — | **미실행** | 2026-09-18 패키지(서버 미해제). 배포 `REWARD_WEIGHTS` 6개 목록 밖의 env 보상 항이라 §1-a 요약 표·§2 대장은 다이얼 6개 그대로 둔다 — 적용은 `go2_task/env_cfg.py` 경로 |
| G-A040 | flat_orient `0.0→−0.5` | G-A033 | — | ✓ | — | **미실행** | 2026-09-19 사양(서버 미해제). §1-a 미탐색 4방향 중 `flat_orientation_l2`. 걷는 기준선 유효 측정 0건이라 `OUT_OF_RANGE`이고, A013·A025(`-1.0`)는 정지 기준선 위 비대칭 계측이라 기각 이력이 아니다 |
| G-A041 | ang_vel_xy `−0.05→−0.04` | G-A033 | — | ✓ | — | **미실행** | 2026-09-20 사양(서버 미해제). §1-a 미탐색 4방향 중 `ang_vel_xy_l2` 완화 방향. 걷는 기준선에서 완화를 돌린 회차가 0건이라 `OUT_OF_RANGE`이고, A016·A024(`-0.15`)와 G-A038(`-0.08`)은 반대 방향(강화)이라 이 값의 기각 이력이 아니다. 감사 `workspace/training/quadruped/reports/GO2_ANG_VEL_RELAX_AUDIT_20260920.md` |
| G-A042 | track `1.5→1.6` | G-A033 | — | ✓ | — | **미실행** | 2026-09-21 사양(서버 미해제). 계획 `upload/plan/GO2_FORWARD_STAIRS_POLICY_20260921.md` §3. 걷는 기준선 유효 시도는 `1.2→1.4` 채택(A017)과 `1.4→1.5` 승급(G-A033) 둘이고 둘 다 같은 방향이다. `1.6`은 관측 범위 밖(`OUT_OF_RANGE`)이라 기각 이력이 아니라 **미측정**이고, 반대 근거는 같은 두 인상에서 늘어난 험지 옆걸음 종료(`48→58`, 자세 낙상 `8→45`)와 G-A033의 2단계 FAIL 기록이다 직접 비교 A017→A033은 checkpoint900/900 1건이며 Pilot→A017은999/900 보조 관측이다. 두 건을 동일 조건 반복으로 부르지 않고 손실의 배타적 원인도 확정하지 않는다. |
| G-A043 | lin_vel_z `−2.0→−1.5` | G-A033 | — | ✓ | — | **미실행** | 2026-09-22 사양(서버 미해제). 계획 `upload/plan/GO2_POST_A042_PLAN_20260922.md` §2. 걷는 기준선에서 이 항은 `-2.0` 한 값만 관측됐으므로 `-1.5`는 `OUT_OF_RANGE`이고 기각 이력이 아니라 **미측정**이다. 같은 완화 방향의 G-A037(`−2→−1`)은 도출 원리가 기반 데이터 §5 S5와 반대여서 `HOLD_CONTRADICTED`로 보류됐고, 이 회차는 그 반대 행을 `contradicting`에 싣고 절반 폭으로 재설계한 정보 회차다. A010·A020(`−3→−2`)은 정지 기준선·비대칭 계측이라 이 값의 근거도 기각 이력도 아니다. |

| G-A044 | lin_vel_z `−2.0→−1.75` | G-A033 | — | ✓ | — | **미실행** | 2026-09-22 사양(서버 미해제). 계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md` §1~§2. 이 항의 걷는 관측값은 이제 `−2.0`(A017·G-A033 등)과 `−1.5`(G-A043) 둘이고 `−1.75`는 그 사이(`BETWEEN_OBSERVED`)다 — 기각 이력이 아니라 **미측정**이다. G-A043(`−1.5`)은 계단을 크게 올렸으나(15cm ≥2단 `0→77`/96) G2 복합 우회전에서 가중 `−4.637/70`을 잃어 INTERNAL_GATE_FAIL이었고, 이 회차는 완화 폭을 절반으로 줄여 그 교환을 다시 잰다. 중간값이 중간 성능이라는 가정은 사전등록된 반증 대상이다(계획 §9-1: 선형 절반이면 c2·c3 둘 다 실패). 1단계 분기 없이 69 case 전수를 수집하고(결함 C-11), 밀침 보호를 네 방향으로 넓힌다(`post_a043_push4_v1`). |
| G-A045 | 학습 seed `42→43` (보상 무변경) | G-A033 | — | ✓ | — | **미실행** | 2026-09-24 사양(서버 미해제). 계획 `upload/plan/GO2_A045_SEED_PAIR_PLAN_20260924.md` §3. **보상 다이얼 회차가 아니다** — G-A033 의 보상 파일 그대로를 학습 seed 43 으로 다시 학습해, 저장된 G-A033(seed 42) 기록과의 차이로 **학습 경로 흔들림**을 한 표본 잰다. 전 회차가 seed 42 하나라 이 양은 측정 0건이었고(`reports/GO2_SEED_SENSITIVITY.md` §0), 그 공백 때문에 같은 다이얼 세 점의 낙상 비단조를 다이얼 탓과 경로 탓으로 가를 수 없다. R-6 안팎 해석은 열린 결정 U2-SEED-REPLICATE-20260918 이며, 보상 변경이 아니므로 **승급 대상이 아니다**(사양 `promotion: forbidden_not_a_reward_change`). |
| G-A046 | lin_vel_z `−2.0→−1.5` @ 학습 seed 43 | G-A045(같은 seed) | — | ✓ | — | **미실행** | 2026-09-24 사양(서버 미해제). 계획 `upload/plan/GO2_A045_SEED_PAIR_PLAN_20260924.md` §3~§4. G-A043 과 **같은 값**을 둘째 학습 경로에서 다시 걸어, seed 43 안에서 G-A045 와 짝을 이루는 대칭 비교를 만든다(seed 42 의 G-A033↔G-A043 쌍과 대칭). 재현 판독은 사전 등록됐다 — 15cm ≥2단 `50/96` 이상이면 계단 이득 재현, `10/96` 이하면 미재현, 그 사이는 INCONCLUSIVE. 학습 seed 가 기준선과 다르므로 이 팔도 **승급 대상이 아니다** (열린 결정 U2-SEED-REPLICATE-20260918). |

**실행 결과 갱신 (2026-09-22).** 위 표의 G-A041·G-A042·G-A043 행은 **사양 발행 시점의 문장이며 그대로 보존한다** — 세 회차의 사양 `dial_history_ref`가 그 줄을 글자 그대로 인용하고 발행 ZIP은 불변이기 때문이다. 세 회차는 그 뒤 실제로 실행·회수됐고 결과는 모두 **A033 유지**다: G-A041 INTERNAL_GATE_FAIL(회수 PARTIAL, 10cm ≥1단 `90→34`/96) · G-A042 INTERNAL_GATE_FAIL(10cm ≥2단 `43→0`/96) · G-A043 INTERNAL_GATE_FAIL(총점 `+2.096/70` < `+2.53`, G2 가중 `−4.637`). 최신 상태는 위 **요약 표**와 `GO2_NOW.md`가 정본이고, 아래 전체 시도 표의 `미실행` 표기는 그 줄이 쓰인 시점의 기록이다.

**실행 결과 갱신 (2026-09-24).** G-A044 도 실행·회수됐다 — ARTIFACT_VERIFIED / INTERNAL_GATE_FAIL, 총점 `38.89379/70`(기준선 대비 `−3.635`), A033 유지. 위 G-A044 행 역시 **사양 발행 시점의 문장이며 그대로 보존한다**(발행 ZIP 불변). 판독 `workspace/training/quadruped/reports/GO2_G_A044_READOUT.md`.

참고: A013·A025 후보도 7case 전부 평균 속도 0.026~0.050 m/s로 정지했다. 따라서 `flat_orientation_l2`는 보행 정책 기준 효과 정보가 없다.
G-A029(`action_rate_l2 -0.008` 재제안)는 G-A018과 같은 값이라 AUDIT_FAIL로 발행되지 않았다.

**이 표가 결과 모음의 정본이다.** `reports/experiment_history.csv`(G-A001 1행에서 멈춤, 260831)와
`reports/GO2_EVIDENCE_INDEX.md`(Pilot-01 증거만)는 갱신이 끊겼다. 조회하지 않는다.
`delta/70` 칼럼은 §5-3 추론 사슬의 원자료 행 후보다(유효 행만). 점수 이득 산정 입력이 아니다(2026-09-17 규칙 교체).

## 1-b. 외부 기준 — Isaac Lab·문헌 (필독, 2026-09-15 사용자 결정 G-D-EXTREF-20260915)

**원문 보관(2026-09-18 추가).** 인용하는 Isaac Lab v2.3.1 파일은 URL·SHA256과 함께 저장소 안에 둔다 — 대화에서 읽고 버리지 않는다. 숫자는 문서에 옮겨 적지 않고 아래 사실표에서 읽는다.
- 보상 항 수식·Go2 rough 가중치: `workspace/training/quadruped/reports/evidence/go2_reward_term_roles_20260917/`(원문 + `SOURCES.csv`)
- 지형 커리큘럼·학습 길이: `.../reports/evidence/go2_curriculum_source_20260918/`(원문 + `SOURCES.csv`) — `terrain_importer.py`(승급·강등, **마지막 레벨 도달 시 무작위 재배치**), `terrains/config/rough.py`(행·열 수, 계단 높이 범위), `terrain_generator.py`(난이도 = (행 + 난수)/행수), `trimesh/mesh_terrains.py`(난이도 → 계단 높이), `curriculums.py`(기록값은 **평균**), `go2/agents/rsl_rl_ppo_cfg.py`(`max_iterations`)
- 그 파일들에서 뽑은 사실표: `.../go2_curriculum_source_20260918/CURRICULUM_FACTS.csv` (생성 `tools/go2_curriculum_facts.py`, 관문 `tools/test_go2_curriculum_facts_contract.py`). 계단 오르기 두 case 가 각각 어느 커리큘럼 행에서 학습되는지는 `stairs_15_curriculum_row`·`stairs_10_curriculum_row` 행에 있고, 우리 학습 지형이 원문과 같은 설정인지는 `our_env_*` 행이 G-A033 `env.yaml` 과 대조한다. **평균 지형 레벨은 무작위 재배치로 상한이 걸려 있어 포화 판정·반증 조건으로 쓰지 않는다**(`mean_level_saturation_unreadable`).

4족 분석·후보 비교·결과 판독·제출문은 이 절을 먼저 대조한다.
기계용 정본은 `workspace/training/quadruped/config/go2_external_reference.json`이다. 대조 도구는 `python tools/go2_external_reference_diff.py <env.yaml>`이다.
`tools/test_go2_canonical_consistency.py` test_11이 아래 표, JSON, A017 `env.yaml`의 일치를 검사한다.

**사용 규칙**
1. 1순위 외부 기준은 **Isaac Lab v2.3.1 공식 Go2 rough 설정**(R-IL-1)이다. 우리 과제 env가 이 설정 위에 서 있다. 서버 버전 근거는 G-F35이고, A017의 프레임워크 항 값이 이 설정과 같다.
2. 후보 비교표에는 항마다 Isaac Lab Go2 rough 값·배포 시작값·기준선 값·이탈 여부를 적는다. Isaac Lab 값에서 **멀어지는** 후보는 이탈 근거를 적는다. 근거는 우리 계측 관측과 문헌 원리 두 가지다.
3. Isaac Lab 값은 유지보수자 관행값이다. ablation이나 논문 근거는 없다(§16). 그래서 Isaac Lab 값으로 **되돌리는** 후보도 같은 사전등록·판정을 거친다. "Isaac Lab 값이니 최적"이라고 쓰지 않는다.
4. 문헌은 **원리**의 근거이지 숫자의 근거가 아니다. 로봇·dt·센서가 다르다.
5. R-6상 바꿀 수 없는 레버는 "R-6 적용 불가"로 적고 reward로 흉내 내지 않는다. 커리큘럼·DR·push·명령 범위·신경망 구조가 여기에 해당한다.
6. 제출문의 작업 방법 설명은 "Isaac Lab 공식 Go2 rough 설정 대비 바꾼 항·근거·측정 결과" 형식으로 쓴다.

**A-0. 항의 역할과 기전 (2026-09-17 사용자 지시: "기준 문서의 역할 설명 없이 우리 결과로만 판단하지 않는다. 원문 역할에 기반한 사실 추론으로 현재와 변경 결과를 예측한다")**

값보다 역할을 먼저 읽는다. 식 원문·항별 수치는 생성 문서가 정본이고, 이 표는 요약이다.
- 원문 식(Isaac Lab v2.3.1 함수 본문): `workspace/training/quadruped/reports/GO2_TUNING_BASE_DATA.md` §0-1
- 기전·예측·정책: `workspace/training/quadruped/reports/GO2_REWARD_MECHANISM_FORECAST.md` (생성 `tools/go2_reward_mechanism.py`)

| 항 | 원문 식이 계산하는 것 | 걸을 때와 멈출 때 | 평가 영역과의 연결 |
|---|---|---|---|
| `track_lin_vel_xy_exp` | 명령 속도와 실제 속도의 차이에 대한 지수 보상 | 걸을 때 커진다. 멈춰도 exp(−\|명령\|²/std²)만큼 남는다 | 걷기를 보상하는 **유일한** 항. 올리면 전진 계열이 오르고 옆걸음·밀침 종료가 늘었다(등급 A) |
| `track_ang_vel_z_exp` | 회전 속도 추종 지수 보상 | 멈출 때 오히려 크다 | 걷기 비용으로 작동 |
| `lin_vel_z_l2` | 몸통 위아래 속도² | 걸을 때 커진다 | 올라서기 자체를 벌한다(G5). 단 오르기 보상률 표는 주 원인이 아니라고 말한다 |
| `ang_vel_xy_l2` | 몸통 구르기·끄덕임 **속도**² | 걸을 때 크게 커진다 | 강화하면 걷기가 먼저 무너진다(A016). 옆 뒤집힘 속도와 연결 |
| `flat_orientation_l2` | 몸통 기울기 **각도**(중력 xy 성분²) | 걷기/정지 차이가 작다 | 옆으로 넘어지기 전에 이미 기운다(G3). 경사·계단에서 상시 벌점(G4·G5). IL은 평지에서만 켠다 |
| `action_rate_l2` | 직전 행동과의 차이² | 걸을 때 커진다 | 약화했는데 멈춘 기록(A018) — 걷기 예측이 가장 불확실한 항 |
| `dof_acc_l2` | 관절 가속도² | 걸을 때 크게 커진다 | **G-A033 걷기 비용 1위, 한 번도 바꾸지 않음.** 빠른 발 올리기(G5)의 비용 |
| `dof_torques_l2` | 관절 토크² | 걸을 때 커진다 | 한 번도 바꾸지 않음. 오르기의 큰 토크 비용 |
| `feet_air_time` | 착지 순간 (체공 시간 − threshold) 합. 명령이 작으면 0 | threshold보다 짧은 걸음이면 음수 | **발 높이가 아니다.** 배포 안내의 "발을 높이 들어 험지 돌파"와 식이 다르다. 올리면 짧은 걸음 벌점이 강해진다 |
| 종료 `base_contact` | 몸통 접촉력 > threshold면 종료 | — | G3 험지 옆걸음 "종료"의 정의 |

- **걷기 margin**: 가중치 × (걷는 행동 식 값 − 멈춘 행동 식 값)의 합이다. 음수면 보상 식이 멈춤을 더 높게 친다. 과거 학습 회차 전부에서 경계대(Pilot-01·A018) 밖의 걷기/정지와 어긋나지 않았다(사후 대조, LOO 포함).
- **상황 margin(계단·흔들림·밀침)**: 평가 기록에서 원하는 상태(오르기·생존)와 실패 상태(멈춤·넘어지기 직전)의 식 값을 잰 부분 margin이다. 관절·행동 항은 기록에 없다. 세 정책에서 부호가 일치하는 항만 근거로 쓴다.
  - 흔들림에서 일치하는 벌점은 구르기 속도와 수직 속도다.
  - 기울기 각도는 엇갈린다.
  - `lin_vel_z_l2` 약화는 계단을 올리고 흔들림·밀침을 낮춘다.
- 새 reward 사양은 `base_data.walk_margin`에 네 구간 예측을 적는다. 걷기 구간이 아니거나 나빠지는 구간이 있으면 이유를 적어야 관문을 통과한다.
- **향후 튜닝 정책**은 생성 문서 §8을 따른다.

**A. reward 가중치** (IL = Isaac Lab v2.3.1. 배포 시작값의 출처는 `go2_task/_finalize.py` `_REP_BASELINE`이고, 거기에 없는 항은 IL Go2 rough 값이다)

| 항 | IL 기본 | IL Go2 rough | IL Go2 flat | 배포 시작값 | G-A033 | G-A033 vs rough |
|---|---:|---:|---:|---:|---:|---|
| `track_lin_vel_xy_exp` | 1.0 | 1.5 | 1.5 | 1.0 | 1.5 | **같음** |
| `track_ang_vel_z_exp` | 0.5 | 0.75 | 0.75 | 0.75 | 0.75 | 같음 |
| `lin_vel_z_l2` | -2.0 | -2.0 | -2.0 | -3.0 | -2.0 | 같음 |
| `ang_vel_xy_l2` | -0.05 | -0.05 | -0.05 | -0.08 | -0.05 | 같음 |
| `dof_torques_l2` | -1e-05 | -0.0002 | -0.0002 | -0.0002 | -0.0002 | 같음 |
| `dof_acc_l2` | -2.5e-07 | -2.5e-07 | -2.5e-07 | -2.5e-07 | -2.5e-07 | 같음 |
| `action_rate_l2` | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | 같음 |
| `feet_air_time` | 0.125 | 0.01 | 0.25 | 0.01 | 0.2 | **다름(20배)** |
| `undesired_contacts` | -1.0 | None | None | None | None | 같음 |
| `flat_orientation_l2` | 0.0 | 0.0 | -2.5 | 0.0 | 0.0 | 같음 |
| `dof_pos_limits` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 같음 |

- `flat_orientation_l2`는 IL 기본 설정에서 "optional penalties"로 분류돼 있다. Go2는 **평지 설정에서만** -2.5로 켜고, 험지 설정에서는 0이다.
- **G-A033이 rough와 다른 항은 `feet_air_time` 하나뿐이다**(10항 중 9항 일치, 2026-09-16 학습 산출물 `env.yaml` 원본 확인).
  - `track` 1.5는 1.2→1.4(A017)→1.4→1.5(G-A033) 두 단계로 rough 값에 **도달**했다.
  - `feet_air_time` 0.2는 유효 단일변수 근거가 없다. Pilot-01의 4항 동시 변경(G-A001)에서 온 값이고,
    그 행의 원문은 *"four variables changed simultaneously so causal attribution is invalid"*다.
    IL rough 0.01에서 20배 이탈이며 IL **평지** 값 0.25 쪽에 가깝다. 현재 기준선에서 가장 취약한 값이다.
- 이전 기준선 A017의 열 값은 `track` 1.4였고 나머지 9항은 G-A033과 같다.

**B. reward 밖 학습 설정** (전부 R-6 밖. 대조와 해석에만 쓴다)

| 항목 | Isaac Lab v2.3.1 | 우리 | 해석 |
|---|---|---|---|
| 학습 길이 | Go2 rough `max_iterations` 1500 (flat 300) | 스크리닝 1000 | 배포 파일 안내는 기준 관찰 3000, 제출본 5000~15000(`quadruped_rewards.py:113-119`) |
| 학습 중 밀침 | Go2 rough `push_robot = None` | 같음 | G6 개선 레버는 reward가 아니다(§17-c) |
| 지형 커리큘럼 | `terrain_levels_vel`: 경계를 넘으면 상승, 명령 거리 절반 미만이면 하강(R-Sci-1 규칙) | 켜짐. A017 평균 레벨 4.25(0~9) | 쉬운 지형 먼저는 학습 안에서 이미 자동으로 적용된다 |
| 명령 범위 | x −1~1, y −1~1, yaw −1~1 | x −1~2, y −0.6~0.6, yaw −1~1 | 과제 env가 바꾼 값이다 |
| PPO `entropy_coef` | Go2 rough 값(`rsl_rl_ppo_cfg.py`) | 다름 — 배포 `go2_task/agent_cfg.py:45` | 배포 값이다. 2026-09-16 추가(이전 표에서 빠짐) |
| `boxes` 높이 범위 | Go2 rough가 기본값을 낮춤(`rough_env_cfg.py:25`) | 다름 — 배포 `go2_task/env_cfg.py:60`이 상한을 더 높임 | 배포 값이다. 2026-09-16 추가(이전 표에서 빠짐) |
| 커리큘럼 로그 값 | `terrain_levels_vel`은 `torch.mean(terrain_levels)`를 반환하고, 시작 레벨은 `max_init_terrain_level`까지 균등 | 같음 | **평균이다.** 계단 열의 도달 높이로 읽지 않는다(재계획 §2 S4) |

**C. 문헌** (원문 확인은 2026-09-05 §16·§17과 2026-09-15)

| ID | 문헌 | 확인한 원리 | 우리 적용(R-6) |
|---|---|---|---|
| R-Sci-1 | Rudin et al., CoRL 2021, arXiv:2109.11978 | 게임식 지형 커리큘럼. 보상항 형태(exp 추종, L2 벌점, 체공 0.5 s) | 커리큘럼은 이미 켜져 있다. 형태 근거로만 쓰고 숫자는 이식하지 않는다 |
| R-Sci-2 | Lee et al., Sci. Robotics 2020, arXiv:2010.11251 | 커리큘럼+DR이 강인성의 주 동력 | 적용 불가(DR). 기대치 조정용 |
| R-Sci-3 | Miki et al., Sci. Robotics 2022, arXiv:2201.08117 | 지형 인지 encoder | 적용 불가(구조). 진단용 |
| R-Sci-4 | Hwangbo et al., Sci. Robotics 2019, arXiv:1901.08652 | 목표 항을 뺀 모든 벌점에 커리큘럼 계수 k_c를 곱한다(0.3에서 시작, k_c←k_c^0.997). "the robot first learns how to achieve the objective and then how to respect various constraints". 시작값은 제자리 서기를 피하려고 골랐다 | 벌점 커리큘럼 자체는 적용 불가(코드). **원리 적용:** 새 벌점을 첫 iter부터 전량 거는 후보는 정지 편법 위험을 사전등록한다. 기본 움직임을 안정시킨 뒤 자세·낙상 벌점을 다룬다. 이어 학습 방식은 train.py 지원 여부가 미확인이다 |
| R-Sci-5 | Margolis et al., RSS 2022, arXiv:2205.02824 | 넓은 명령 범위를 처음부터 균일하게 뽑으면 "learning fails". 좁게 시작해 넓힌다 | 적용 불가(명령 범위). 쉬운 조건 먼저라는 원리만 참고 |

**D. 현재 후보 대조 (2026-09-15)**
- G-A030(`flat_orientation_l2 0→-1.0`)은 IL Go2 rough 값 0.0에서 이탈한다.
  - IL은 이 벌점을 평지 설정에서만 켠다.
  - 첫 iter부터 전량 거는 방식이라 R-Sci-4 원리와도 어긋난다.
  - 이탈 근거는 우리 계측의 기울기 선행 관측(계획 §3-1)뿐이고 원인은 미확정이다.
  - **보류(2026-09-15 사용자 방향: 기본 동작 먼저, G-D-BASIC-MOTION-20260915).** 패키지는 보존하고 낙상·자세 단계에서 재비교한다.
- 다음 후보는 **G-A031·G-A032**(`feet_air_time` 0.2→0.01·0.1 용량 쌍)다. 계획 `workspace/training/quadruped/upload/plan/GO2_BASIC_MOTION_TUNING_PLAN_20260915.md`.
  - 근거: IL은 0.01을 험지, 0.25를 평지 설정에 쓴다. A015(0.2→0.35)는 7 case 모두 몸 높이를 낮췄다. A017의 약점은 비평지 속도(속도/명령 .49~.60)와 높이 게이트 낙상(slope 7/8/4, 기울기 낙상 0)이다.
  - 반대 근거: R-Sci-1은 체공 항을 추종보다 크게 둔다. 문헌은 하향을 지지하지 않는다(계획 §3).
  - **결과(2026-09-15 서버, 계획 §9-2): 두 회차 모두 1단계 FAIL.**
    - G-A031(0.01): 표적 −.022. 몸은 높아졌다(높이 p10 .235→.302, 게이트 낙상 26→14). 대신 경사 속도가 떨어졌다(.28→.17~.22).
    - G-A032(0.1): 표적 −.437. 몸이 낮게 무너졌다(높이 p10 .129, 게이트 낙상 189).
    - 계획 §6-3 규칙대로 0.2를 유지한다.
  - 다음은 **G-A033**(`track` 1.4→1.5, IL Go2 rough 값으로 복귀, 계획 §12)이다. 낙상 표적은 마지막이다.
  - **정정(2026-09-15, 기존 telemetry 재분석, `upload/plan/GO2_FALL_POSTURE_CANDIDATES_20260915.md` §6):**
    - G-A031의 게이트 낙상 감소는 몸이 높아져서가 아니라 오르막을 덜 올라서다(0.5m 이상 오른 로봇 6~11 vs A017 22~28).
    - G-A032는 체크포인트 iter 700으로 평가돼 A017(iter 900)과 시점이 다르다. −.437을 `feet_air_time` 0.1의 효과로 읽지 않는다.
- **낙상·자세 단계 전환(2026-09-15 사용자 결정).** 후보 비교 `upload/plan/GO2_FALL_POSTURE_CANDIDATES_20260915.md` §4.
  - G-A033은 서버 미실행 상태로 철회 권고다. Pilot(1.2)이 A017(1.4)보다 계단을 더 올랐으므로 1.5는 계단 반대 방향이다.
  - 추천 A = `flat_orientation_l2` 0→−1.0. IL rough 0에서 이탈한다. 이탈 근거는 G3 옆걸음 종료 0.5~1.0초 전 기울기 선행(종료 48건 중 32건)이다.
  - 위험은 IL flat 전용·R-Sci-4 정지 편법·G4 경사 벌점이다. 체크포인트 iter 고정 수정판이 필요하다.
  - `lin_vel_z_l2` 완화는 항 크기(0.066/s vs 정지 손실 약 0.6/s)상 오르막 정지의 원인이 아니라 제외했다. `undesired_contacts`·termination 벌점은 R-6 적용 불가(항 미정의)다.
- **정정 — 사용자 순서(경사·밀침·DR → 계단) 재분석(2026-09-15, 계획 §8~§10).**
  - G7 손실은 DR이 아니라 험지 속도 부족이다. dr 추종이 같은 지형 rough_forward와 같고, 질량-속도 상관은 r +.05~+.36이다.
  - Pilot→A017(`track` 1.2→1.4)은 rough_forward·dr를 세 평가 seed 모두 개선했다. 그래서 G-A033 철회 권고를 거두고 **튜닝값 1 = `track` 1.4→1.5(IL Go2 rough 값)**로 둔다. 계단 2단 도달 감소(10~11→3~5)는 위험으로 사전등록한다.
  - **튜닝값 2 = `flat_orientation_l2` 0→−1.0**(G6·G3 옆 넘어짐)이다.
  - IL v2.3.1 `feet_air_time` 식 `Σ(체공−0.5)·첫 접지`는 짧은 걸음마다 음수다. A017 로그 −.027/s로 확인했다.
  - G4 정지와 G5 계단은 근거 있는 가중치를 도출하지 못했다. 발 수준 계측이 없다.

## 2. reward 대장

| reward | 강좌 배포 기준 | Pilot-01 | 변경 | 역할·출처 | 현재 성능 판정 | 직접 측정 G | 한계 |
|---|---:|---:|---:|---|---|---|---|
| `track_lin_vel_xy_exp` | 1.0 | 1.2 | +0.2 | 속도 추종. 강좌 14강은 1.0→1.5 단일변수 예시. **Rudin et al. 2021(R-Sci-1) Table 2: `φ(v*-v)` 가중 1·dt, φ std²=0.25(std=0.5) — 우리 내부 `tracking_proxy=exp(-(RMSE/0.5)^2)`의 0.5와 동일 커널** | **채택 — 보행 기준선에서 1.2→1.4 유효 개선(A027 69case +6.09/70, G-D184). 부분 만족: G4·G6 손실.** `1.4→1.5`는 기준선 승급(G-D-BASELINE-A033-20260916, 현재 값 `1.5`). 상향 `1.6`은 G-A042 실행으로 기각(2026-09-21, INTERNAL_GATE_FAIL). 과거 'G-A009·G-A023 미만족'은 정지 기준선 위 측정이라 SUPERSEDED(G-D116) | G1~G7 tier 1 · 69-case | seed 101 G1 delta `-0.0000663`; 논문은 이 항 **단독**이 아니라 9항 동시 튜닝의 결과이므로 이 항만 올리는 것의 안전성은 논문 근거가 아니다 |
| `feet_air_time` | 0.01 | 0.2 | +0.19 | 발 들기. 강좌는 낮으면 발을 거의 안 든다고 설명. **R-Sci-1 Table 2: `Σ(t_air-0.5)` 가중 2·dt — 목표 체공시간 0.5초가 `quadruped_rewards.py`의 "0.5+ 면 바운딩 가능성" 경고와 정확히 일치** | **기각(상향 0.35) — 보행 기준선 A015 −30.12/70 유효(G-D73).** 하향 0.01(G-A031 표적 −.022)·0.1(G-A032 표적 −.437)도 1단계 FAIL(2026-09-15). 0.20은 G-A033 유지값. 'G-A007 0.20 screen fail'은 정지 기준선 위라 SUPERSEDED | G1~G7 69-case·7영상 | G1 정체, 보정 G5 진행 회귀, 60/70 승급선 미달; foot contact 직접 계측 없음. 논문 가중치(2·dt)는 track_lin_vel(1·dt)보다 **크다** — 우리 기본값(0.01≪1.0)과는 상대적 비중이 반대 방향 |
| `lin_vel_z_l2` | -3.0 | -2.0 | 완화 | 상하 흔들림. 강좌 14강의 1k 예시는 -3→-2 후 전진 관찰. **R-Sci-1 Table 2: `-v²_z` 가중 4·dt** | **기각(완화 −1.5·−1.75) — 보행 기준선 유효 시도 2건(G-A043 2026-09-22 · G-A044 2026-09-23, 둘 다 ARTIFACT_VERIFIED / INTERNAL_GATE_FAIL).** 260906 '최종 기각'은 비대칭 계측·정지 기준선이라 G-D116에서 철회(SUPERSEDED). G-A033 값 -2.0. G-A033 위 `−1.0`(G-A037)은 보류. `−1.5`(G-A043)는 계단 개선·G2 보호 실패로 총점 `+2.096/70`(<`+2.53`), `−1.75`(G-A044)는 총점 `38.894/70`으로 기준선보다 `−3.635` 낮아 둘 다 기각이다. **세 점을 한 표에 놓으면 계수기가 갈린다** — 계단에 오른 로봇 수는 단조(10cm ≥2단 43→62→94/96)인데 자세 낙상은 가운데 값에서만 솟는다(계단10cm 34→65→17/96). 다이얼 탓인지 학습 경로 탓인지는 학습 seed 대조군이 0건이라 미확정이고, 그것을 재는 회차가 G-A045·G-A046(seed 43 대칭 쌍, 승급 불가)이다 (`reports/evidence/go2_seed_pair_20260924/MONOTONICITY.csv`) | G1~G7 69case(G-A043·G-A044) | Default-01 위 A010 결과는 무효. 상세 §15·G-D116 |
| `ang_vel_xy_l2` | -0.08 | -0.05 | 완화 | 몸통 roll/pitch 흔들림 억제. **R-Sci-1 Table 2: `-\|ω_xy\|²` 가중 0.05·dt** | **기각(강화) — 보행 기준선 A016 -0.05→-0.15 −45.12/70 유효(G-D77).** G-A033 위 `-0.05→-0.08`(G-A038)은 판정 없음·승급 후보 아님(옆걸음 개선, 10cm 오르기 붕괴). 완화 `-0.04`도 기각 — G-A041 실행·회수(2026-09-21) INTERNAL_GATE_FAIL, 회수 PARTIAL, 감사 `workspace/training/quadruped/reports/GO2_ANG_VEL_RELAX_AUDIT_20260920.md`). G-A033 값 -0.05 | G1~G7(A016) | Default-01 위 A024 '최종 기각'은 G-D116에서 철회. 상세 §18 |
| `action_rate_l2` | -0.01 | -0.01 | 불변 | 관절 명령 급변·떨림 억제. **R-Sci-1 Table 2: action rate 가중 0.25·dt(정의가 관절속도 항이라 Isaac Lab의 "직전 액션과의 차분" 정의와 완전히 같지 않음 — 이름만 대응, 수식은 다름)** | **기각(완화) — 보행 기준선 A018 -0.01→-0.008 −44.40/70·G1~G7 생존 7/7 후퇴 유효(G-D81).** 강화 방향은 미탐색. G-A033 값 -0.01 | G1~G7(A018) | 단일 학습 seed(exploratory). jerk 정량 없음. G-A029 재제안은 AUDIT_FAIL |
| `track_ang_vel_z_exp` | 0.75 | 0.75 | 불변 | 회전 추종, env 기본 활성 | **부분 만족** | G2 | Pilot G2 worst survival 1.0·tracking .7521, 단독 yaw reward 효과는 아님 |
| `flat_orientation_l2` | 0.0 | 0.0 | 불변(A013·A025가 -1.0 시험) | 자세 직접 벌점. 현재 Go2 env는 비활성(0.0) | **미탐색 — 보행 기준선 유효 측정 없음.** A013·A025는 비대칭 계측(G-D104)이고 후보도 7case 전부 속도 0.026~0.050 m/s로 정지. G-A033 값 0.0 | G2·G4·G5·G6(G-A013 v1 실측 실점 시나리오) | H1 자세 reward 결론 복사 금지. G4/G5는 경사·계단에서 기울임 자체를 벌줄 위험 있음 — 상세 §18 |
| termination penalty | 미정의 | 미정의 | — | 현재 env termination은 base contact 조건 | **미측정** | 없음 | 없는 항을 임의 추가하지 않음 |

## 3. 현재 만족/미만족 표

| 분류 | 항목 |
|---|---|
| 만족 | 없음 — A017·Pilot-01 모두 `INTERNAL_GATE_FAIL`(A027) |
| 부분 만족 | `track_lin_vel_xy_exp` 1.4(A017 채택, G4·G6 손실); A017의 G1·G2(생존 1.0·추종 ≥.89); 불변 `track_ang_vel_z_exp`의 G2 행동 |
| 미만족 | A017의 G3·G4·G5·G6·G7 시나리오 게이트; 보행 기준선에서 기각된 값 `feet_air_time` 0.35, `ang_vel_xy_l2` -0.15, `action_rate_l2` -0.008 |
| 미측정 | 보행 기준선 미탐색: `lin_vel_z_l2` 양방향, `ang_vel_xy_l2` 완화, `action_rate_l2` 강화, `flat_orientation_l2`; action_rate jerk, 공식 결과, 독립 학습 seed, termination reward 효과 |
| INCONCLUSIVE | A017에 남은 Pilot 조합(feet .2·lin_z -2·ang_xy -.05)의 개별 인과효과 |

2026-09-14 정정: 이전 판은 정지 기준선 위 결과와 유효 결과를 섞어 적었다(캠페인 감사 P1). 항별 근거는 §1-a.

## 4. 강좌 기반 실험 원칙

근거: 강좌 14강.

1. reward는 가중합이며 항목 간 비율이 행동을 바꾼다.
2. 한 번에 하나씩 바꾸어 변인을 통제한다.
3. 숫자와 `play.py` 영상을 함께 비교한다.
4. 짧은 실험으로 방향을 잡고 최종 후보만 길게 학습한다.
5. 과한 속도는 장애물 안정성을, 과한 feet_air는 bounding을, 과한 penalty는 정지 편법을 만들 수 있다.

Pilot-01은 1항의 trade-off를 탐색한 기준선이지만 2항의 인과설계를 충족하지 못했다.

## 5. 다음 후보 선정 규칙

1. 정확한 G1~G7 자체평가에서 시나리오별 `weight × (1-scenario_proxy)` 감점과 survival·tracking 중 약한 인수를 표로 만든다.
   최대 감점 시나리오는 후보를 찾는 입력이지 자동 1순위가 아니다.
2. 약한 인수와 직접 연결되는 reward 후보를 시나리오별로 적고, 후보마다 **사실 근거 추론 사슬·반증 조건·실험 비용**을 비교한다.
   낙상 완치를 다른 개선의 선행조건으로 두지 않는다(2026-09-14 사용자 결정, G-D-PRIORITY-20260914).
3. **사실 근거 추론 사슬(2026-09-17 사용자 지시 G-D-FACT-RULES-20260917: "이득 추정이 아니라 사실관계 근거 추론이 더 중요하다")**
   - 순서: 원문 역할(기반 데이터 §0-1) → 원자료 행(지지 행과 **반대 행** 모두) → 특이점 → 걷기·계단·흔들림·밀침 방향 예측 → 반증 조건 → 위험 축과 그 관문.
   - 원자료 행은 파일과 글자 그대로의 키·값으로 사양 `inference.rows`에 적는다. 반대 행이 있으면 권고(`RECOMMENDED`)로 적지 않는다.
   - 반박된 모델(다이얼 모델, 계단 부분 margin의 크기)은 근거로 쓰지 않는다(`reports/GO2_G_A038_READOUT.md` §5).
   - 위험 축은 `fact_rules_v1` 사전 등록(`tools/go2_fact_rules.py`)으로 지킨다.
   - `tools/test_go2_detectability_gate.py`가 사양 발행 시 검사한다(파일을 열어 행이 실제로 있는지 본다).
   - 70점 이득 수치는 요구하지 않는다. 민감도(가정한 개선이 달성됐을 때의 점수 변화)는 이득이 아니다. 수치를 적는다면 검출 한계 **`2.53/70`** 이상이어야 한다.
   - 이전 규칙("기대 가중 이득 수치 필수, 없으면 waiver")은 2026-09-17 폐기했다. 그 규칙에서는 어떤 후보도 이득을 추정하지 못해 전 사양이 waiver로 빠져나갔고(G-A035·G-A037·G-A038), waiver로 실행된 G-A038은 계단 붕괴를 예측하지 못했다.
   - 결과는 학습 seed 1개라 **가설의 지지·반박**으로만 읽는다(`reports/GO2_SEED_SENSITIVITY.md` §5).
4. 현재 동결 기준선(`GO2_NOW.md` §1)에서 한 항만 바꾸고 동일 evaluator 지문·seed·iteration으로 비교한다.
   260901 원문 "배포 기본 Default-01에서"는 Default-01이 보행하지 않아 SUPERSEDED(G-D113).
5. 성공은 primary 개선 + 나머지 G worst-case 비열등 + 정상 네발 gait를 모두 요구한다.
6. 후보 사양서는 §1-a 다이얼 시도 이력의 해당 항 행을 인용한다(`dial_history_ref`).

~~Default/Pilot 쌍대평가 완료 뒤 현재 다음 reward 값은 **`feet_air_time 0.20` 단일변수**로 확정됐다.~~ SUPERSEDED(260901 결정). 다음 후보는 §1-a와 `GO2_NOW.md` §4를 따른다.

## 6. Default-vs-Pilot FULL 분석 — 260901

- Default `17.90699/70`, Pilot `41.97990/70`, delta `+24.07291/70`; 둘 다 `INTERNAL_GATE_FAIL`.
- Pilot은 G1·G2·G6 `INTERNAL_SCENARIO_PASS`, G3·G4·G5·G7 `INTERNAL_SCENARIO_FAIL`이다.
- 세 평가 seed delta가 모두 양수지만 학습 seed는 42 하나라 독립 학습 재현성은 미확보다.
- 최대 감점은 G5 `8.12/70`, 다음은 G3 `7.84/70`. G5의 약한 인수는 tracking/completion이다.
- 분기: `SHARED_WEAKNESS_FOUND`. Pilot은 비교 상한으로 보존하되 resume하지 않고, Default 계보에서 한 항씩 재검증한다.
- 첫 사전등록 후보: `feet_air_time .01→.2` 단일 변경 1,000 iter. 최적값 주장이 아니라 Pilot 개선·회귀의 인과 분리 실험이다.
- 영상: 정책별 7개, 총 14개 contact sheet 직접 관찰로 `VIDEO_OBSERVED`; 연속 gait timing·foot contact는 미측정.
- 상세: `workspace/training/quadruped/reports/GO2_DEFAULT_VS_PILOT_ANALYSIS_260901.md`.

## 6-a. 배포 기본 control 상태 — 260901 결정

- `exported/model_best_20260831154121.pt`는 별도 SHA를 가지지만 paired
  `env_20260831154121.yaml`도 Pilot-01 튜닝 reward `1.2/0.2/-2.0/-0.05/-0.01`을 보유한다.
- 따라서 이 timestamped backup은 배포 기본 control의 성능·lineage 근거가 아니다.
- provenance-valid control은 현재 **미확보**다. Default-01은 기본값·seed 42·4096 env·1,000 iter로
  from-scratch 생성하며, 조건부가 아닌 첫 쌍대 비교의 필수 기준이다.
- 260901 실행 package `go2_default_vs_pilot_v1.zip`은 위 값을 reward-only staging으로 고정해 로컬
  검증됐지만 아직 서버 학습 artifact가 아니므로 control 성능은 계속 **미측정**이다.
- control 생성 전까지 Pilot-01이 배포 기본보다 개선됐다는 표현은 금지한다.
- 향후 reward screening은 Default-01 계보에서 하나씩 추가한다. Pilot-01은 resume하지 않는다.

## 6-b. Default-01 ↔ Pilot-01 비교 규칙

- 두 정책 모두 같은 G1~G7 registry, 평가 seed 101/202/303, case fingerprint를 사용한다.
- `Train/mean_reward`는 reward 계수가 달라 정책 간 비교에서 제외한다.
- survival·tracking·completion·recovery·영상 부작용만 비교한다.
- weighted simulation proxy 차이 `0.03`, survival 비열등 `-0.02`, tracking 비열등 `-0.05`를
  내부 의사결정 허용오차로 사전등록한다.
- 상세 분기는 `workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md` §6을 따른다.

## 7. 과학적 표현 규칙

- 두 관측점은 탐색이지 최적값 증명이 아니다.
- 평가 seed 반복은 정책 평가 변동성만 다루며 독립 학습 seed 재현성을 증명하지 않는다.
- 평균 reward·terrain level·training base_contact는 G1~G7 공식 survival/tracking과 다르다.
- 내부 `exp(-(RMSE/std)^2)`는 candidate env의 reward 모양을 빌린 proxy이며 공식식이 아니다.
- 최종 제출문은 실제 검증된 문제·변경·결과·한계만 30~200자로 요약한다.

## 8. Default-vs-Pilot 부분 결과 반영 — 260901

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
- 상세 사전등록: `workspace/training/quadruped/upload/plan/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md`.

## 10. G-A007 PARTIAL 결과 (인코딩 손상 구간 재구성) — 260901

> ⚠️ 이 섹션 원문은 한글 부분이 인코딩 손상으로 `?`로 깨져 있었다. 아래는 남아 있는 영문·수치·상태코드(SHA, `INCONCLUSIVE`, `BUGGY_DO_NOT_REUSE` 등)를 근거로 재구성한 내용이며, 원본 기록 시스템에서 대조 확인이 필요하다.

- candidate 실행에서 telemetry 8/69, 영상 0/7만 확보되어 `feet_air_time=0.20` 후보는 여전히 `INCONCLUSIVE`다.
- reward 값 자체는 변경되지 않았고 runner 오류로 나머지 case가 수집되지 못한 것으로 보인다 — reward 설정 문제로 인한 실패는 아니다.
- 확보된 candidate model SHA: `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5`.
- v1 runner는 `BUGGY_DO_NOT_REUSE`로 확정됐고, graceful shutdown과 bounded retry를 갖춘 v2 package로 교체됐다.
- 이 실험의 최종 결과는 §11 "G-A007 최종 결과와 후속 평가비용 결정 — 260902" 참고.



## 11. G-A007 최종 결과와 후속 평가비용 결정 — 260902

(PARTIAL 중간 기록: §10)

- `feet_air_time 0.01→0.20` 단일변수 후보는 artifact·7영상까지 확보했지만 내부 v1 proxy가 `21.77258/70`로 대표평가 full-suite 승급선 `60/70`에 미달한다.
- G5 기존 진행도는 env 간 초기 위치를 섞은 전역 max-min이므로 무효다. 기존 CSV를 body-frame 속도로 재적분하면 계단 진행 중앙값은 Default 약 `0.336m`, Pilot 약 `4.218m`, candidate 약 `0.049m`다.
- G7은 같은 seed의 G3 `rough_forward`와 byte-identical telemetry여서 독립 DR 근거가 아니며 `INTERNAL_GATE_INCONCLUSIVE`로 정정한다.
- 따라서 `feet_air_time=0.20`은 **미만족 / INTERNAL_SCREEN_FAIL**이며 장기 승급하지 않는다.
- 이후 모든 H1·Go2 신규 후보는 `6~8 case 조기중단 → 21 case 대표평가 → 60/70과 안정성 동시 충족 시 기체별 전체평가` 순서를 사용한다.
- 69-case의 직접 출처는 강좌가 아니다. 강좌·가이드는 G1~G7 범주·가중치와 단일변수 조정 원칙을 제공했고, case grid·평가 seed·69건 합계는 내부 설계다.

## 12. G-A009 `track_lin_vel_xy_exp=1.20` 단일변수 사전등록 — 260902

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
- 상세 PRD: `workspace/training/quadruped/upload/plan/GO2_TRACK_LIN_VEL_120_SCREENING_PRD.md`.

## 13. G-A009 결과 — 260902

- artifact: FULL result ZIP SHA `d9d84f68c19eac9c84ec932154c7edf9d40743b8a05e92468ff0348bbc7661c3`, manifest 125/125, candidate/baseline 7/7, 영상 1, lineage 8/8로 `ARTIFACT_VERIFIED`.
- primary: G1 proxy `0.00356288`, baseline `0.00362921`, delta `-0.0000663`; 사전 최소 개선 `+0.05`에 미달.
- secondary: 총 내부 proxy는 `20.62741/70`로 baseline `17.53712/70`보다 `+3.09028` 높지만 주로 G6 개선의 영향이며 G1 목적을 충족하지 못한다.
- scenario gate: G1·G2·G3·G4·G5·G7 `INTERNAL_SCENARIO_FAIL`, G6만 `INTERNAL_SCENARIO_PASS`; seed 101 exploratory 결과다.
- 판정: `track_lin_vel_xy_exp=1.20` 단독 후보는 **미만족 / INTERNAL_EARLY_KILL_FAIL**. 대표 3-seed·69-case·장기학습으로 승급하지 않는다.
- 영상·공식: G1 영상은 직접 판독해 `VIDEO_OBSERVED`; 네 환경 모두 전진 명령 대비 시작 격자 부근에 머물러 정량 실패와 일치한다. G2~G7은 `VIDEO_UNKNOWN`; `OFFICIAL_RESULT_UNMEASURED`.

## 14. G-A009 최종 분석과 G-A010 선정 — 260902

- 동일 repaired-v2 tier-1에서 총 내부 proxy는 Default `17.53712/70` 대비 candidate `20.62741/70`, `+3.09028`이다.
- 증가분 기여는 G6 `+2.41007/70`(`77.99%`), G3 `+0.61589/70`(`19.93%`) 순이다. 목표 G1은 `-0.00070/70`로 개선되지 않았다.
- 학습 best reward `16.2977@900`과 마지막 training-terrain 낙상 진단 `6.52%`는 고정 G1 evaluator 점수가 아니다. G1 evaluator의 평균 속도는 `0.02748 m/s`, tracking RMSE `1.18714`다.
- G-A009 최종 분류는 `미만족 / INTERNAL_EARLY_KILL_FAIL`; 상세 보고서는 `workspace/training/quadruped/reports/GO2_TRACK_LIN_VEL_120_RESULT_ANALYSIS_260902.md`다.
- 다음 정보가치 1순위는 Default 계보 `lin_vel_z_l2 -3.0→-2.0` 단독 1,000 iter다. 강좌의 1k 전진 관찰과 남은 미분리 Pilot 항이라는 점을 근거로 하며 최적값 주장은 아니다.
- G-A010 실패 시 `ang_vel_xy_l2 -0.08→-0.05` 단독 G-A011로 간다. 둘 다 실패할 때만 두 항의 상호작용을 검토한다.

## 15. G-A010 `lin_vel_z_l2=-2.0` 단일변수 사전등록·package — 260902

| reward | 기준 | candidate | 현재 상태 | 직접 측정 | 승급 전 필요한 증거 |
|---|---:|---:|---|---|---|
| `lin_vel_z_l2` | `-3.0` | `-2.0` | **최종 기각(260906, posture_gate_v2 실측) — `-3.0` 유지** | G1~G6 survival 전부 `-0.1` 초과 회귀, 총점 `-7.63/70`, tracking 개선 없음 | (탈락 — 승급 대상 아님) |

- 유지값: `track_lin_vel_xy_exp=1.0`, `feet_air_time=0.01`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`.
- 학습: Default-01 from-scratch, seed 42, 4096 env, 1,000 iter. 단일 학습 seed이므로 결과는 exploratory다.
- engine v1.0 SHA `4489bef4…8a5a`는 서버 bare `python3` 결함으로 `BUGGY_DO_NOT_REUSE`; 학습 시작 전 실패했다.
- **정정(260906): engine v1.1(SHA `e8f8b3cde…`)은 폐기되지 않고 실제로 260902에 실행됐다.** `workspace/_keep/go2_g_a010_lin_vel_z_m2/`에 launcher.log(1,000 iter, 실측 00:59:11)·RUNNER_STATUS.txt(`ENGINE_ARCHIVE_SHA256=e8f8b3cde9…`)·TIER1_DECISION.json이 실물로 남아 있다. 결과: 가중 총점 `+2.2571599/70`(17.54→19.79), G3 survival `+0.094`, G6 survival `+0.344`, 그러나 목표 시나리오 G1 개선이 `+0.05` 미달이라는 이유 하나로 `target_G1_improvement_below_0.05` 조기종료 판정(당시 gate는 G1 단독 기준 — 이후 G-D68로 가중 총점 기준으로 교체됨). 이 결과의 evaluator는 `schema_version:1`(termination-only, 직접 재확인)이라 **G-D92가 규정한 신뢰 불가 evaluator와 같은 세대다** — Chain-01(G-A011~22)과 별개로 실행됐지만 posture_gate_v2(commit `f229e06`)보다 시간상 앞서므로 같은 맹점을 공유한다. 따라서 이 값은 폐기가 아니라 **"방향성 참고(총점 개선 신호), survival 결론은 불신"**으로 다룬다.
- **260905 재등록:** engine v1.4(posture_gate_v2 포함, SHA `81c3bccef543eae116732a3965f6ad5fee692431243eb0ec00615acab2243b37`, 계약 테스트 16/16 통과 — G-F144·G-F145)로 spec을 재검증(`engine_version`·`baseline.env_sha256`·`flat_orientation_l2` 키·`min_total_points_delta` gate 갱신)해 `upload/G-A010/current/`에 재게시했다(release `20260905_lin_vel_z_m2_engine_v1_4_r2`, spec SHA `2910450db9e107875410a80ed1d947d80cced0e31e67b1734f544e300374861d`).
- **260906 재측정 결과(FINAL):** `INTERNAL_EARLY_KILL_FAIL`. `baseline_points_70=17.132070`→`candidate_points_70=9.499548`(`-7.632522/70`), G1~G6 survival 전부 `-0.1` 초과 회귀(G1 `-0.40625`~G5 `-0.6875`), G7만 허용 내(`-0.09375`). G1 tracking 개선은 사실상 없었다(`-0.00055`). G1 raw case에서 메커니즘 직접 확인: `terminated_env_count:0`(v1은 "전원 생존"으로 봄)인데 `fallen_env_count:13/32`·`height_rel_mean:0.261`·`survival_proxy_v1:1.0` vs `survival_proxy_v2:0.59375` — G-A011의 `track_lin_vel_xy_exp` 사례(§14-a 아래, `GO2_PROJECT_STATE.md` G-F141)와 동일 패턴으로 v1→v2 뒤집힘이 재현됐다. 260902 v1 측정값(`+2.2571599/70`, "생존 후퇴 0건")은 폐기가 아니라 이제 "termination-only evaluator의 맹점을 보여주는 반증 사례"로 확정한다. `-3.0`을 그대로 유지하고 이 다이얼은 닫는다(`GO2_PROJECT_STATE.md` G-D99). 아티팩트: `workspace/_keep/go2_g_a010_lin_vel_z_m2_v2_260906/`, 검증 상세는 같은 문서 G-F147~150.
- 현재 experiment spec: 같은 폴더의 `G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`; release 이력은 `upload/G-A010/UPLOAD_HISTORY.tsv`에서 관리한다.
- 같은 폴더의 spec: `workspace/training/quadruped/G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- engine은 reward 값을 내장하지 않고 JSON을 schema·Default identity·정확히 한 reward 변경으로 검증한 뒤 runtime source를 만든다.
- 실행 전 상태는 `ARTIFACT_VERIFIED`일 뿐 candidate 성능·영상·내부 gate·공식 결과는 `[미측정]` / `VIDEO_UNKNOWN` / `OFFICIAL_RESULT_UNMEASURED`다.
- 상세 PRD: `workspace/training/quadruped/upload/plan/GO2_LIN_VEL_Z_M2_SCREENING_PRD.md`.

## 16. 과학적 근거 감사 — 260905

사용자가 이전에 지시한 "튜닝 수치는 논문 등 과학적 근거로 잡는다"가 실제로 지켜졌는지 감사했다.

- **감사 결과: 지켜지지 않았다.** §2 reward 대장 전체(260905 이전 판)에서 외부 논문·arXiv·DOI 인용은
  **0건**이었다. 모든 "역할·출처" 칸은 "강좌 14강" 또는 "코드/env 기본값"이었다 — 이는 후보
  출발점의 출처이지 논문 근거가 아니다(본 문서 §0 원칙과 이미 모순).
- Isaac Lab 자체의 Go2/H1 rough_env_cfg.py도 논문을 인용하지 않는다(직접 GitHub 소스 확인,
  H1 쪽은 `H1_REWARD_EVIDENCE_MASTER.md` §7 항목3-4가 이미 같은 파일을 인용하되 "합리적
  screening 점이지 최적값 근거 아님"으로 정확히 한계를 밝혀 두었다). 즉 Isaac Lab 기본값 자체도
  논문에서 그대로 받아온 숫자가 아니라 엔지니어링 관행값이다.
- **실제로 존재하는 논문 근거를 찾아 연결했다(R-Sci-1):** Rudin, Hoeller, Reist, Hutter,
  *Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning*, CoRL 2021,
  arXiv:2109.11978. 이 논문 Table 2가 우리가 지금 튜닝 중인 5개 항(`track_lin_vel_xy_exp`,
  `feet_air_time`, `lin_vel_z_l2`, `ang_vel_xy_l2`, `action_rate_l2`)과 **같은 이름·같은 함수형**의
  보상항을 정의한다 — Isaac Lab의 사족 locomotion 보상 구조가 유래한 실제 1차 문헌이다. 상세는
  §2 표에 각 항목별로 직접 붙였다(WebFetch로 arXiv 원문·ar5iv 렌더링에서 Table 2 직접 확인,
  추측 아님).
- **이 논문이 실제로 뒷받침하는 것과 뒷받침하지 못하는 것을 분리한다:**
  - 뒷받침: 보상항의 **형태**(exponential tracking, L2 penalty, feet-air-time bonus)와 **목표
    체공시간 0.5초**(우리 저장소의 "0.5+ 면 바운딩" 경고와 독립적으로 일치), tracking 커널
    std=0.5(우리 내부 `tracking_proxy` 공식과 일치).
  - 뒷받침하지 못함: 우리 config의 정확한 가중치 값. 논문의 가중치(`dt` 스케일링, ANYmal 시뮬레이터·제어주기 50Hz 기준)는 Isaac Lab Go2 config의 dt·decimation과 다르므로 **숫자를 그대로 이식할 수 없다** — 형태·상대적 방향성의 근거이지 정확한 값의 근거가 아니다.
  - **가장 중요한 발견:** 논문의 9개 항은 **하나의 고정된 조합으로 함께 튜닝**된 것이지, 개별
    항을 하나씩 올려도 안전하다는 근거가 아니다. 이는 Chain-01이 왜 무너졌는지(G-D91,
    `GO2_PROJECT_STATE.md`)와 정확히 같은 결론이다 — **개별로 검증된 변경들의 단순 합이 안전
    하다는 것은 이 논문에서도, 우리 실험에서도 증명된 적이 없다.**
- **결정 — 앞으로 새 reward 후보를 사전등록할 때마다 §2 표의 "역할·출처" 칸에 실제 논문/1차
  문헌을 찾아 붙인다.** 못 찾으면 "강좌/코드 기본값 — 논문 근거 없음"이라고 명시하고 추측하지
  않는다. 이번 감사로 5개 항은 R-Sci-1로 채웠다. 나머지(`track_ang_vel_z_exp`,
  `flat_orientation_l2`, termination penalty)는 R-Sci-1 Table 2에 없는 항이라 **여전히 논문 근거
  없음** — 다음에 이 항을 건드릴 실험을 사전등록할 때 별도로 찾는다.

## 17. 우리 환경과 같은 계열의 문헌 확장 탐색 — 260905

우리 환경(`go2_task/env_cfg.py:3`)은 IsaacLab `UnitreeGo2RoughEnvCfg` — **height_scanner(지형
스캔) 장착 rough terrain 과제**다. R-Sci-1(Rudin et al. 2021)의 직접 후속 계보에서 두 편을 더
찾아 WebFetch로 원문을 직접 확인했다(추측 아님).

### 17-a. 새로 연결한 문헌

| ID | 문헌 | 확인된 사실 | 우리 환경과의 관계 |
|---|---|---|---|
| **R-Sci-2** | Lee, Hwangbo, Wellhausen, Koltun, Hutter, *Learning Quadrupedal Locomotion over Challenging Terrain*, Science Robotics 2020, arXiv:2010.11251 | 배포 정책은 **순수 proprioceptive(맹목)** — 지형 스캔 없이 진흙·자갈·잔해 지형을 극복. 핵심 주장: "훨씬 단순한 도메인에서 훈련해도 실제 환경의 강인성을 얻을 수 있다"(curriculum + domain randomization) | **부분 일치.** 우리 env는 height_scanner가 있어 이 논문의 맹목 정책과 센서 조건이 다르다. 그러나 이 논문이 확립한 "지형 커리큘럼 + 도메인 랜덤화가 강인성의 주 동력이지 reward 미세조정이 아니다"라는 결론은 우리에게도 적용된다 — 그리고 그 커리큘럼·DR은 **IsaacLab의 terrain_generator·이벤트 매니저가 이미 담당**하고 있어 우리가 만질 수 있는 부분(reward weight)이 아니다 |
| **R-Sci-3** | Miki, Lee, Hwangbo, Wellhausen, Koltun, Hutter, *Learning Robust Perceptive Locomotion for Quadrupedal Robots in the Wild*, Science Robotics 2022, arXiv:2201.08117 | height_scanner류 exteroceptive 입력과 proprioceptive 입력을 **attention 기반 encoder**로 결합해 노이즈·가림·반사 지형에서도 강인하게 만듦. 계단 접촉 전에 지형을 "미리 인지"하는 것이 핵심 | **센서 구성은 우리와 가장 가깝다**(둘 다 height-scan 보유). 그러나 핵심 기여는 **신경망 구조**(attention encoder)이며 이는 R-6-1 규정상 우리가 건드릴 수 없는 `go2_task/`·`train.py` 영역이다. 이 논문에서 우리가 가져올 수 있는 것은 구조가 아니라 "지형 정보를 다리가 닿기 전에 미리 반영해야 계단·경사 실패가 준다"는 **문제 진단**뿐이다 |

### 17-b. 내 지식으로 보태는 분석 — G1이 가장 크게 깎이는 이유

Default-01의 시나리오별 실점(가중치×(1-proxy))을 다시 계산하면 **G1(전진, 가중 .15)이
`0.1495`로 전 시나리오 중 최대 실점**이다 — G3(거친 지형, `0.1469`)이나 G5(계단, `0.1302`)보다도
크다. G1의 `tracking_xy_rmse=1.18714 m/s`는 tracking 커널 std(0.5, R-Sci-1과 우리 내부식이 공유하는
값)의 2배가 넘어 `exp(-(1.187/0.5)^2)≈0.0036`으로 사실상 0에 가깝다.

이미 두 번(G-A007 `feet_air_time→0.2`, G-A009 `track_lin_vel_xy_exp→1.2`) **개별** 단일변수로
이 G1을 겨냥했지만 **둘 다 실패**했다(delta 사실상 0). R-Sci-1의 발견(§16 — 9개 항은 하나의
고정 조합으로 튜닝됐다)에 내 지식을 더하면, 이건 우연이 아니라 **legged RL의 잘 알려진 패턴과
일치한다**: `lin_vel_z_l2`·`ang_vel_xy_l2` 같은 안정화 벌점이 상대적으로 강하면 정책이 빠른 보폭
자체를 회피해 **추종 보상을 올려도(또는 발 들기를 늘려도) 물리적으로 도달 가능한 속도 자체가
오르지 않는** 상한(ceiling)이 생긴다. 이 경우 필요한 건 track 항 단독 인상이 아니라 **안정화
벌점을 같은 방향으로 함께 낮추는 조합**이거나, 애초에 **1,000 iter가 빠른 gait를 형성하기엔
짧을 수 있다**(R-Sci-1·R-Sci-2 둘 다 이 종류의 정책을 수만 iteration 단위로 학습시킨다 — 우리
1,000 iter 스크리닝은 방향 탐색용이지 최종 gait 형성용이 아니었을 가능성).

### 17-c. G6(밀침 회복)에 대한 기대치 조정 — 정직하게 미리 밝힌다

`env_cfg.py:98-102`의 주석대로 **`push_robot` 이벤트는 학습 중엔 항상 비활성**이고 평가(`play.py
--push`)에서만 켠다. R-Sci-1·R-Sci-2 모두 밀침 강인성을 **학습 중 외력 랜덤화(도메인
랜덤화)의 결과물**로 얻는다 — 즉 문헌상 G6 개선의 주 레버는 reward 가중치가 아니라 학습 중
이벤트 설정이다. 그런데 이벤트 설정은 `go2_task/`이고 우리가 만질 수 있는 건 `quadruped_rewards.py`
뿐이다(R-6-1). **정직한 결론: G6은 reward 튜닝만으로 문헌이 뒷받침하는 만큼의 개선을 기대하기
어렵다.** 과욕으로 G6에 실험을 우선 배정하지 않는다.

### 17-d. 결정 — 엔진 재빌드 이후 실험 우선순위 (문헌 기반, 사전등록)

| 우선 | 후보 | 문헌 근거 | 목표 | 이전 실패와의 차이 |
|---:|---|---|---|---|
| 1 | ~~`lin_vel_z_l2 -3.0→-2.0`~~ — **260906 posture_gate_v2 실측 결과 최종 기각**(G-A010, G1~G6 survival 전부 붕괴, 총점 `-7.63/70`). `-3.0` 유지, 이 다이얼은 닫힘 | R-Sci-1 Table 2 근거는 방향만 맞았고 크기는 틀렸다 — 안정화 벌점을 낮추는 건 안전하지 않았다 | (기각) | §15 260906 갱신, `GO2_PROJECT_STATE.md` G-D99 |
| 2 | ~~`ang_vel_xy_l2 -0.08→-0.15`~~(방향 정정: 완화(`-0.05`)는 1과 같은 이미 실패한 방향이라 반대인 강화로 실행) — **260906 posture_gate_v2 실측 결과 최종 기각**(G-A024, G1~G7 전 시나리오 붕괴, 총점 `-17.13/70`, 1보다 더 심함). `-0.08` 유지, 이 다이얼도 닫힘 | 동일 진단, R-Sci-1 안정화 계열 — 방향은 틀렸다 | (기각) | §18, `GO2_PROJECT_STATE.md` G-D101 |
| 3 | **재측정**: `flat_orientation_l2 0.0→-1.0`(G-A013, 260903의 재측정 — 새 실험 아님. 그때 evaluator가 v1 termination-only였음이 확인돼 결과 불신, ID는 G-A025) | 이 항은 R-Sci-1에 없으나 자세를 간접이 아니라 직접 벌점화하는 유일한 미신뢰 레버 | G4/G5 survival 특별 주시, 전 시나리오 비붕괴 | posture_gate_v2 엔진(v1.4)으로 재실행 — `GO2_PROJECT_STATE.md` G-D102 |
| 4 | 1·2·3이 모두 실패하면 iteration 수를 3,000~5,000으로 늘린 **동일 reward 재실행**(새 변수 아님) 또는 reward 무변경 대조군으로 재학습 자체의 변동성부터 분리 측정 | R-Sci-1·R-Sci-2 원 실험은 수만 iter 단위 학습 | gait 성숙 시간 부족 가설 vs 재학습 변동성 가설 분리 | 지금까지 posture_gate_v2로 측정한 Default-01 단일변수 3건(track_lin_vel_xy_exp·lin_vel_z_l2·ang_vel_xy_l2)이 방향 불문 전부 실패 — `GO2_PROJECT_STATE.md` G-D103 |
| 보류 | G6 전용 reward 실험 | §17-c | — | 문헌상 reward만으로는 기대이득이 낮음 — DR/이벤트 변경은 규정상 우리 권한 밖 |

이 순서는 G-D93·G-D95(엔진 재빌드·계약 테스트 통과 전 신규 실험 금지)를 대체하지 않는다.
재빌드가 끝난 뒤 다음 실험을 고를 때 이 순서를 따른다.

## 18. G-A024 결과와 G-A025 재측정 등록 — 260906

- **G-A024 결과(FINAL): `INTERNAL_EARLY_KILL_FAIL`.** `ang_vel_xy_l2 -0.08→-0.15`(강화)는 `candidate_points_70=0.0`(완전 붕괴), G1~G7 **전 시나리오** survival `-0.1` 초과 회귀(G1·G2·G4·G5 `-1.0` 완전 전멸). G1 raw: `fallen_env_count:32/32`, `height_rel_mean:0.144`(임계 `0.18` 미달), 학습 자체는 수치적으로 안정(mean reward 11.9~12.9, 발산 없음) — 정책이 새 reward를 잘 최적화해서 낮게 웅크려 거의 움직이지 않는 국소최적해로 수렴한 전형적 reward hacking. `-0.08` 유지, 다이얼 닫힘. 아티팩트: `workspace/_keep/go2_g_a024_ang_vel_xy_m015/`, 상세는 `GO2_PROJECT_STATE.md` G-F151~153·G-D101.
- **패턴 확정:** Default-01 위 posture_gate_v2 실측 단일변수 3건(`track_lin_vel_xy_exp` 강화, `lin_vel_z_l2` 완화, `ang_vel_xy_l2` 강화) 전부 실패 — 완화·강화 양방향, 서로 다른 두 안정화 항 모두 붕괴. 방향의 문제가 아니라 Default-01의 현재 6개 가중치 조합 자체가 얇은 균형점에 있다는 뜻(`GO2_PROJECT_STATE.md` G-F153).
- **G-A025 재측정 등록:** `flat_orientation_l2 0.0→-1.0`, Default-01, 나머지 5개 항 불변(`lin_vel_z_l2=-3.0`·`ang_vel_xy_l2=-0.08` 둘 다 위 실패로 원복 확정값 그대로). G-A013(260903)이 같은 값을 이미 시험해 `-1.4278/70`(G2·G4·G5·G6 후퇴)로 기각했으나, 그 실행의 `RUNNER_STATUS.txt`(`ENGINE_VERSION=1.1.0`) 및 tier1 case summary(`schema_version:1`)를 직접 열람해 v1 termination-only evaluator였음을 확인했다 — G-A010과 같은 세대 결함이라 결과 불신, posture_gate_v2로 재측정한다. engine v1.4 대상 `load_and_validate`·`materialize_runtime` 드라이런 통과, `upload/G-A025/current/`에 게시. 위험 고지: 이 항은 지형과 무관하게 평평한 자세를 요구하므로 G4(경사)·G5(계단)에서 필요한 기울임을 오히려 벌줄 수 있다 — 결과 해석 시 G4/G5를 특히 주의 깊게 본다.

## 19. G-A027 실제 회수 독립 감사 — 2026-09-11 기록
- 기존 A017/Pilot 재평가이며 새 학습 아님. 원시69case씩 승인 대응 검증완료. raw39.76495 vs33.67132(+6.09363), 양쪽 절대성능 INTERNAL_GATE_FAIL.
- track_lin_vel_xy_exp1.2→1.4: **부분 만족**(동일 evaluator 총점 증가), G4/G6 손실 및 동일case 생존회귀 때문에 확정만족/안전비열등은 아님. 다른 유지 reward의 개별 인과효과는 **INCONCLUSIVE**다.
- 최대손실 G5 10.50, 다음G3 9.03. A017 stairs_15_down 생존3seed 모두0. G5하강 영상없음; 원인을 reward로 단정하지 않는다. 다음 reward 변경값은 추가행동증거 전 지정하지 않음.
- 사용자 결정대로 raw를 보존하고 H1관측비율 보정참고34.75490 vs29.42901을 별도표시. 공식점수·검증된 Go2 예측식 아님.
- §17~18의 과거 무효비교 기반 기각이나 인과패턴 단정은 이번 결과의 근거로 재사용하지 않는다. 개별과거 정책 재판정은 이번 감사범위 밖.
- 근거: GO2_RESULT_AUDIT_G-A027_20260910.md; workspace/server_returns/G-A027/audit_20260910/COMPARISON.json 및 H1_RATIO_SENSITIVITY.json.

## 20. A027 후속 조건부 가설 — 2026-09-11
- workspace/training/quadruped/upload/plan/GO2_A027_TUNING_PLAN_FOR_OPUS_20260911.md에 T1 ang_vel_xy_l2 -0.05→-0.06 초안 등록. INCONCLUSIVE/미실행. 과도한 몸통 회전이 하강 실패 전에 관찰되는 경우에만 검토하며, 정확한 값의 성능·외부문헌 보증 없음.
- 사용자 요청은 Opus 검토 후 Codex 재감사. §19 결과를 변경하지 않고 새 성공·안전 조건은 새 실험에만 적용한다.

### 2026-09-13 회수 report 직접 열람 정정
- 작업 ID GO2-P1-PREP-20260913. A027 회수 경로의 `workspace/_keep/go2_a017_full_suite/evaluation/{a017,pilot}/SELF_EVAL_REPORT.md` 두 파일을 직접 읽었다. A017 39.765/70, Pilot 33.671/70, 양쪽 INTERNAL_GATE_FAIL. 이는 내부 평가 report이며 학습 report.html이 아니다.
- A017 G5 최저곱 case stairs_10_down@202: survival 0, tracking 0.1614. G3 rough_lateral@303: survival 0.4688, tracking 0.7574. G4 slope_plus_20@202: survival 0.75, tracking 0.6810. 이 값은 각 시나리오 최저곱 case의 인수이며 모든 case의 독립 최저값은 아니다.
- 로컬 `workspace/training/quadruped/exported/report.html`도 본문 전체를 읽었다. tracking 1.2, 2026-08-31 학습, 최고보상18.02@972, terrain3.94, 마지막10회 학습낙상률13.8%, std0.499. GO2_PROJECT_STATE G-F03과 일치하는 Pilot 계열 보고서이며 tracking1.4인 A017 학습 report로 인용하지 않는다. 이번에 모델 텐서와의 보고서 대응을 재검증한 것은 아니다.
- A027 회수 디렉터리에서 report.html은 발견하지 못했다. 재귀 탐색한 로컬 workspace의 Go2 report.html은 위 exported 파일뿐이다. 별도 미회수/다른 위치 파일 존재 여부는 미확인.
- 판단: G5 하강 생존 우선 진단 유지. 학습낙상률13.8%를 G5 생존율로 변환하지 않는다. 보고서의 일반적 흔들림 허용 설명은 ang_vel_xy_l2 -0.06의 효과 또는 하강 원인을 증명하지 못하므로 조건부 가설 INCONCLUSIVE 유지.

## GO2 next tuning preparation - 2026-09-13
- User requested preparation for the next quadruped tuning. Work ID: GO2-P1-PREP-20260913. Lifecycle: PLANNED. No server execution or new training performed.
- Plan: workspace/training/quadruped/upload/plan/GO2_A027_NEXT_TUNING_PREP_20260913.md; adjacent JSON fixes 18 diagnostic cases. Existing policies, rewards and approved releases preserved.
- Evidence: existing CSV stores actual_wz, not wx/wy; run_video does not request simultaneous telemetry. Prior assumption that existing angular channels suffice is withdrawn.
- Four review findings addressed in the plan. Numeric diagnostic thresholds, separate instrumentation and independent review remain open. HOLD: package unverified, training evidence insufficient. Historical schedule remains CLOSED.
- Local verification: 5 preparation-contract assertions passed (18 unique cases); git diff --check passed. No runtime/package test claimed.

<!-- GO2:REPORT-FIRST:START -->
## 2026-09-13 연구 방향 변경 — G-D-REPORT-FIRST-20260913
- 사용자 결정: 지침과 서브에이전트에 학습 report 필독을 강제하고 연구 방향을 변경한다.
- 새 순서: report·env·학습로그/정책 대응 → 시나리오 약점 → 실패 유형/경쟁 가설 → 후보 선정.
- 이전 T1 `ang_vel_xy_l2 -0.05→-0.06`은 **DEFERRED_HYPOTHESIS**로 내린다. 다음 튜닝값/1순위가 아니며 효과 INCONCLUSIVE.
- G5 하강 생존은 현재 평가상 우선 진단 대상이나 원인은 미확정. 회전 과다, 발걸림/정지, 낮은 자세,
  학습 성숙도 및 평가/영상 대응 문제를 구분한다. 모두 가설이며 보고서만으로 인과를 판정하지 않는다.
- Pilot HTML은 직접 읽었으나 이번 작업에서 정책 대응을 완결 검증하지 않았으므로 READ_UNMATCHED.
  A017 원 학습 HTML은 현재 탐색 범위에서 MISSING / REPORT_REQUIRED_NOT_ACQUIRED.
  A027 SELF_EVAL_REPORT는 원 학습 HTML을 대체하지 않는다.
- NEXT: 로컬 원 학습 bundle·snapshot·로그에서 A017/Pilot report 대응을 먼저 회수·검증한다.
  그 후 필요한 진단을 다시 동결한다. 기존 18case 목록은 제안 범위이며 실행 승인/고정 패키지가 아니다.
- 서버 실행·reward/배포코드 변경 없음. 새 학습 HOLD — report 대응 및 진단 근거 미완료.
- 작업 ID GO2-P1-PREP-20260913 유지. 과거 승인 release와 결과는 변경하지 않는다.
<!-- GO2:REPORT-FIRST:END -->

### 2026-09-13 report의 자료 대체 가능성 확인
- report 필독은 영상/telemetry 대체가 아니다. Pilot HTML은 학습 요약만 제공하고 G5 실패 trajectory는 없다.
- 근거 및 자료별 표: workspace/training/quadruped/upload/plan/GO2_EVIDENCE_NECESSITY_REVIEW_20260913.md.
- 이미 유효한 A027 정량을 중복 실행하지 않는다. 기존18case 제안은 재사용/결측 목록 대조 후 수량을 동결한다.
- 다음 변수 미확정, -0.06 DEFERRED_HYPOTHESIS 유지. 새 wx/wy 계측도 가설 구분에 필요한 경우에만 검토한다.

### G-A028 — 2026-09-13 실행 준비 선행조건 실측
- 기존 G-A027 current의 RUN_GUIDE·builder·runner·발행 도구를 직접 확인했다. 다음 실행 정본도 같은 current/history/manifest/guide 체계를 사용한다.
- workspace 내 upload/history 제외 ZIP·tar.gz 52개 내부 목록까지 검색했다. A017 원 학습 report.html은 발견하지 못했다. A017 결과 ZIP(GO2_PILOT_TRACK_LIN_VEL_XY_140_RESULT.zip)에도 없다. 검색 오류 0건.
- 증거: workspace/training/quadruped/upload/G-A028/review/REPORT_RECOVERY_SEARCH.json. 기존 Pilot 계열 exported/report.html로 A017 보고서를 대신하지 않는다.
- 실제 차단: REPORT_REQUIRED_NOT_ACQUIRED 및 다음 단일 변경값 미확정. 실행 패키지 완성·서버 실행을 주장하지 않는다. report 원본은 외부 보관 사본 회수가 필요하며 과거 checkpoint로 당시 학습 HTML을 꾸며 생성하지 않는다.
- 배포 train.py/play.py/go2_task/quadruped_rewards.py 변경 없음. 학습 미실행. G-A028은 PLANNED 유지.

### G-A028 P1 — 실행 패키지 발행(2026-09-13)
- current: workspace/training/quadruped/upload/G-A028/current/GO2_G_A028_P1.zip. SHA256 0d9843681e7d1b852273a09c0964c94cef47d3ac4a8c153d5d84ee6bc25eaacf. history/20260913_p1 및 UPLOAD_HISTORY.tsv 보존.
- 기존 계획 P1의 서버 재생 실행 패키지다. P2 새 튜닝 학습 패키지와 구별한다. 가중치 변경/학습 없음. 18영상·동일 실행 telemetry/summary·로그·model/env를 단일 결과 ZIP으로 회수.
- 검증:15 tests 성공(모의18case완료·실패부분회수·기존결과보존·report 회수 포함), CRC/내부SHA30개·bash -n·py_compile·diff check 정상. 실제 IsaacLab 실행은 미측정. ARTIFACT_VERIFIED_LOCAL_TESTED, 성능 판정 아님.
- 공용 학습 engine의 Default baseline hash 문제는 P1에 해당하지 않는다. P1은 승인 A027 ZIP SHA를 직접 검증하고 두 보존 정책과 계측 소스를 그대로 사용한다. 일반 학습 engine의 남은 문제를 해결했다고 주장하지 않는다.
- 원 학습 report 공백은 유지, 새 학습 HTML은 평가 전용으로 NOT_APPLICABLE. 신규 튜닝의 report 필수회수는 공용 학습 runner에 별도 구현한 상태.
- 외부 실행 상태 PLANNED. 다음: 사용자 서버 실행·단일결과ZIP/SHA 회수, 로컬 18영상/정량/로그/identity 확인 후 판독. P2 자동 학습 없음.

### G-A028-RESULT-AUDIT-20260913 ? result/report relationship correction
- Download verified: ZIP SHA 6e4a807b276e566e01aa58e5f12a61f01e74df999809e975220f69722794ed1e; internal SHA192/192, model/env4/4,18 valid telemetry cases.18 videos decoded, each999frames/19.98s; exact step/frame alignment unverified. ARTIFACT_VERIFIED only.
- Report body read: existing Pilot HTML READ_UNMATCHED; A017 HTML MISSING; A028 new HTML NOT_APPLICABLE(TRAINING=none). No new training occurred.
- Frozen proxy survivors (3seeds x4env): A017 stairs10=0/12, stairs15=0/12, slope+20=11/12; Pilot2/12,0/12,12/12. No /70 score. SELF_ASSESSMENT_INCOMPLETE.
- IMPORTANT correction: stairs_down label does not establish actual descent. Sampled video shows approach/stalling inside inverted stairs. Withdraw unconditional descent-fall explanation; descent coverage VIDEO_UNKNOWN.
- IMPORTANT measurement limit: approved telemetry uses mean scanner ray height, not ground directly under body. Stair boundary bias can contribute to low-height verdict; physical fall interpretation INTERNAL_GATE_INCONCLUSIVE. Applies to same A027 measurement method too; preserve historic numeric outputs, do not promote them to verified physical falls.
- Report does not replace videos,steps.csv,execution logs or policy/config identity. Current strongest observed problem is stair stalling, not proven excessive roll/pitch. -0.06 remains DEFERRED_HYPOTHESIS; no new training or reward change authorized by these results.
- Evidence/report: workspace/server_returns/G-A028/audit_20260913/REPORT_RELATIONSHIP_AUDIT.md; case_metrics.json, artifact_verification.json, video_validation.json, contact sheets. Original downloads preserved; ZIP/SHA copied to workspace/server_returns/G-A028/received/. No training merge.

### G-A029 — 2026-09-14 로컬 검토 파일 및 회수 검증 결과
- 사용자 요청을 난이도 기반 검토 정책으로 기록: 낙상 완치 대신 기대 이득·비용·원인 확실성을 함께 비교. G3 또는 특정 reward의 실행 우선순위 확정은 아님.
- 계획: workspace/training/quadruped/upload/plan/GO2_G_A029_DIFFICULTY_SCREENING.md.
- 검토 파일: workspace/training/quadruped/upload/G-A029/review/GO2_G_A029_TUNING_REVIEW.zip (+SHA). 실행 JSON과 구별되는 NON_EXECUTABLE_TUNING_REVIEW, execution/training=false, single_change=null. current 미발행.
- 회수·지침·엔진 계약 총32 tests 성공. 정상 report의 ZIP/SHA 포함, missing/empty/stale 거부, bash -n/LF 확인. 회수 후 본문과 정책 의미 대응은 별도 필요.
- 발견/수정: 러너 CRLF를 LF로 정규화하고 .gitattributes로 고정. Windows shell fixture PATH 고정. 엔진 계약 테스트가 기존 ZIP을 덮어쓰던 부작용을 임시폴더 빌드로 차단.
- 이번 테스트가 변경한 기존 엔진 ZIP/SHA 두 파일만 초기 clean 상태 및 HEAD=index 확인 후 원 바이트 복원. 후속 테스트에서 두 파일 불변 확인. 승인 upload/current/history 변경 없음.
- 증거: review/GO2_G_A029_VALIDATION.json 및 GO2_G_A029_TEST_OUTPUT.txt. ZIP CRC/내부SHA 확인. 실제 서버/성능 미측정.
- A017 원 학습 report MISSING 및 변경값 미확정 유지. 로컬 파일 준비 완료이나 학습 작업 상태 PLANNED, 실행본 생성은 HOLD. 이전 engine baseline 실패 기록은 이번 로컬19개 계약 테스트 성공으로 현 상태 정정하며 A017 실행 spec 검증 완료를 뜻하지 않음.

### G-A029 ? 2026-09-14 ?? ?? ?? ? ?? ??? ??
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시).** 원문을 추측으로 복원하지 않는다. 대체 기록: 바로 아래 「2026-09-14 G-A029 §3 판단 종료」 절, `GO2_PROJECT_STATE.md` 같은 날짜 정상 절.
- ??? ??: ?? ?? ??? ???? ???? ????? ?? ?? ?? ??. ?????? ?? ??? ?? ???.
- ?? ???: workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md. G3/G7 ?? ??? ?? ???? G1/G2 ???G4/G6 ?? ??, G5 ??? ?? ????. ?? ??? ?? ??? ?????? ?? ???.
- A017 ??? ??: action_rate_l2 -0.01?-0.008(20% ?? ???, ??/??? ???). ?? Python reward ?? ??? baseline ??, ??? JSON? upload/G-A029/review? ??. ?? ??? ?? ??? ??.
- REPORT_READ_STATUS: A017 MISSING, Pilot READ_UNMATCHED ??. ?? ??: ?? engine? A017 frozen baseline ???, ?? manifest ? ?? ?? ?? ???. ?? ?? ??/current/history ?? ??.
- ?? ??: 35 unittest ??(?????Python ??/LF??????report fresh/missing/empty/stale?ZIP/SHA?shell ???engine ??). ?? ??/?? ?? ???. ?? lifecycle PLANNED, ?? ?? ??.

## 2026-09-14 G-A029 §3 판단 종료 — NEW-CONTINUATION / HOLD
- 재개 감사: 시작 시 git status 확인. 기존 사용자 수정과 미추적 파일은 보존했다. 이전 입력의 기준 해시가 없어 파일 불변을 주장하지 않으며, 현재 계획·약점 보고서·조건부 JSON을 직접 읽었다. 한국어가 ?로 깨진 과거 append는 근거에서 제외한다.
- §3-B: **조건부 실험 채택(실험 가치만, 후보 확정·학습 승인 아님)**. action_rate_l2 -0.01→-0.008은 동작 변화 벌점 크기를 20% 줄이는 단일변수 탐색이다. 기존 G3/G7 속도 부족과 연결되는 반증 가능한 가설이며, track 추가 강화에서 관찰된 G4/G6 회귀를 무시하지 않는 대안이다. 원인을 증명한 것은 아니다. 목표 RMSE/진행거리 개선 실패 또는 생존·기존 추종 회귀 시 철회하며 자동 연장하지 않는다. action/contact 별도 서버 진단을 선행조건으로 추가하지 않는다.
- 직접 근거: quadruped_rewards.py:73-76은 부드러움/민첩성 tradeoff를 설명한다. A017 candidate_training.log:33165의 action_rate 보상 -0.1004는 항이 작동했다는 단서일 뿐 억제 원인·포화 증거가 아니다. 같은 로그 말미의 최고19.78@856, 지형4.25, 학습낙상 진단10.6%, std0.548은 원 HTML의 예상 대조값이지 시나리오 성능이 아니다.
- 로컬에서 함수 정의를 찾지 못해 공식 upstream만 좁게 열람했다: https://raw.githubusercontent.com/isaac-sim/IsaacLab/main/source/isaaclab/isaaclab/envs/mdp/rewards.py (2026-09-14 열람, action_rate_l2 L225-227). 연속 action 차이 제곱합을 벌점화하는 정의다. main의 현재 정의이며 당시 서버 버전 동일성 또는 -0.008 최적값을 검증하지 않는다.
- §3-C: **REPORT_READ_STATUS=MISSING (A017), REPORT_REQUIRED_NOT_ACQUIRED**. 기존 52archive 내부 목록은 재검색하지 않았다. 기존 목록에 없던 6개 ZIP만 추가 확인했고 모두 report.html 항목 0개였다. 6개 모두 파일 수정시각은 이전 검색보다 오래되어 새로 다운로드됐다고 주장하지 않는다.
- 추가 확인 경로: workspace/_keep/{GO2_A017_FULL_SUITE_RESULT.zip,GO2_DEFAULT_VS_PILOT_RESULT.zip,GO2_FEET_AIR_TIME_020_RESULT.zip,GO2_PILOT_V2_BASELINE_RESULT.zip}; workspace/server_returns/{go2_default_vs_pilot_v1_full_260901/original/GO2_DEFAULT_VS_PILOT_RESULT.zip,go2_feet_air_time_020_v1_full_260901/original/GO2_FEET_AIR_TIME_020_RESULT.zip}. 이번 검사는 내부 이름 목록 확인이며 SHA/CRC 검증 완료 주장이 아니다.
- Pilot READ_UNMATCHED는 앞선 직접 열람 기록을 유지하며 이번에 HTML 본문을 새로 읽거나 정책 대응을 확정한 것은 아니다. A017 원 HTML 부재 상태에서 Pilot 재감사를 늘리지 않는다.
- 정확한 차단: AGENTS.md report-first §4가 원 학습 report 누락 시 새 reward 후보 확정·학습 착수를 금지한다. 사용자 인계 요청은 규칙 변경이 아니다. 따라서 current 실행 ZIP·실행 명령은 발행하지 않았다. A017 엔진 지원과 측정 manifest 검증도 아직 수행하지 않았으며 보고서 도착만으로 실행 준비 완료가 되지는 않는다.
- 단일 해소 조치: **A017 원 학습 report.html의 외부 보관 사본 제공**. 원 로그가 기록한 생성 위치는 /workspace/_go2_tuning_runtime/go2_g_a017_pilot_track_lin_vel_xy_140/candidate/exported/report.html 이다. 대상 model_900.pt, reward-best step856, model SHA 0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4. 원본을 받으면 run/env/log 대응 확인 후 기존 계획 §4부터 진행한다. 재생성 HTML이나 SELF_EVAL_REPORT로 대체하지 않는다.
- 서버 실행·학습·원 artifact/승인 ZIP 변경 없음. G-A029 학습 lifecycle PLANNED 유지. 현재 단계 0/6. reward 효과: track 부분 만족(기존 한계 유지), action_rate 미측정, feet/lin_z/ang_xy/flat INCONCLUSIVE.
### GO2-REPLAN-A029-20260914 — 감사 후 사용자 요청 재계획
- 사용자 결정: G-A029 감사에 따라 메인 문제를 진단하고 튜닝 계획을 수립한다. 이번 요청은 계획이며 서버 실행/패키지 발행으로 확대하지 않는다. 역사 일정 CLOSED는 유지한다.
- G-A029 REJECTED_BY_AUDIT 및 -0.008 NEXT 철회 유지, review 불변. 과거 A017 HTML 누락을 발행 차단으로 복원하지 않는다.
- 계획 정본: workspace/training/quadruped/upload/plan/GO2_POST_A029_TUNING_PLAN_20260914.md.
- 직접 근거: A018 양 arm 각7case 모두 schema2/v2; A013/A025 baseline은 schema1/2 혼재, candidate는 schema2라 합산 비대칭. A027 G3 rough_lateral seed101/202/303의 base-contact 종료는 17/14/17개(/32), 첫 종료 전0.5초 q=1-gz² 평균 .688/.628/.660. 기울기는 연관성이지 최초 원인 확정 아님.
- 계획값: A017 조건 flat_orientation_l2 0→-1.0 단일변수, G3 접촉 종료/생존 표적; G5 정체·경사 회귀 동시 감시. -1은 관측 기반 단위 크기 exploratory 값이지 upstream 최적값/만족 판정 아님.
- REPORT_READ_STATUS: A017 MISSING(기존 복구 불가 확정 유지), Pilot READ_UNMATCHED(이번 HTML 본문 직접 열람, 정책 대응 미완결).
- NEXT: 다음 미사용 번호로 위 계획의 current 실행 패키지 구현·검증. 이번에 번호 예약/실행 ZIP/서버 명령은 발행하지 않았다. 학습·성능·공식 결과 새 측정 없음.

## 2026-09-19 PM 전략 검토 정정
G-A040 과거 HOLD_CONTRADICTED는 INFORMATION_RUN으로 정정(미실행·성능 미측정). 반대 증거 여섯 행은 보존한다. flat_orientation −0.5는 관측 최적값이 아닌 기존 탐침 격자의 최소 크기이며, G3 생존 목표의 정보 실험 후보이다. 원문 수식·반대 증거·다른 후보와 비용 비교·report 대응은 `workspace/training/quadruped/upload/plan/GO2_PM_REPAIR_STRATEGY_20260919.md` 참조. 기존 15cm guard가 검출 불가하므로 실행 준비 완료로 표시하지 않는다.
