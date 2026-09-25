# Go2 캠페인 감사 권고 시행 계획 (G-P-AUDIT-REMEDIATION-20260914)

근거 감사: `workspace/training/quadruped/reports/GO2_TUNING_CAMPAIGN_AUDIT_20260914.md` §6 권고 1~6.
상태: **A·B `DONE`(2026-09-14), C `HOLD — 사용자 재검토`.** 시행 기록은 `GO2_PROJECT_STATE.md` 「G-P-AUDIT-REMEDIATION-20260914」 절에 있다.
C는 캠페인 감사를 포함해 재검토한 뒤 사용자가 결정한다. 이 문서는 C의 실행 승인·학습 착수를 뜻하지 않는다.

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 축. 튜닝이 다시 유효한 실험을 공급하도록 정본과 엔진을 복구한다.
- [현재 단계] 2/6 짧은 학습 pilot. 동결 기준선은 A017(69case 39.76/70, 내부 proxy)이다.
- [확보] 유효 대칭 비교 5건(A015~A018, A027). A017 69case posture_gate_v2 텔레메트리(schema 6).
- [미확보] 엔진의 A017 기준선 등록, 다이얼 시도 이력표, 잔여 GPU 실측, G5·G3 생존 후보.
- [이번 계획] 단계 A~B는 문서·검증 복구(GPU 0), 단계 C는 다음 단일변수 실행 패키지(G-A030)다.
- [흐름] 감사 완료 → **A 정본 정정 → B 필독 구조·검사 도구** → C G-A030 패키지 → 서버 1,000 iter → 69case 판독
- [지금 할 일] 이 계획의 §7 결정 두 가지를 확인한다.
- [보장하지 않음] 문서 정정은 점수를 올리지 않는다. G-A030 결과도 단일 학습 seed의 `exploratory` 결과다.

## 1. 원칙
1. **과거 기록은 지우지 않는다.** 틀린 현재 상태 문구만 고친다. 과거 판정 행에는 `SUPERSEDED by <ID>`를 붙인다.
2. **정정은 판정을 새로 만들지 않는다.** 원장에 이미 있는 결정(G-D81·G-D113·G-D116·G-D184 등)을 현재 상태 문구에 반영하는 작업이다.
3. **기존 계약 테스트의 고정 문자열을 지킨다.**
   - `tools/test_go2_report_first_contract.py:27-34`는 원장 7개에 `G-D-REPORT-FIRST-20260913`과 `DEFERRED_HYPOTHESIS` 문자열을 요구한다.
   - `tools/validate_go2_campaign.py:74-92`는 원장 5개에 `Default-01`을 요구하고, 역할 문서 2개에 `PRD_CHANGE=NONE|UPDATED`와 `LEDGER_SYNC=PASS|FAIL`을 요구한다.
   - 이 블록들은 삭제하지 않고 이력으로 남긴다.
4. **규칙을 늘리지 않고 검사 도구로 강제한다.** 사람이 기억해서 지키는 규칙은 이미 실패했다(G-D109 교훈).
5. 한국어 파일은 편집 후 매번 UTF-8 유효성을 검사한다. 과거 `?` 손상은 편집 도구의 인코딩 사고였다.

## 2. 단계표

| 단계 | 등급 | 작업 | 대상 | 완료 기준 | GPU |
|---|---|---|---|---|---:|
| A1 | 필수 | reward 원장 현재 판정 정정 | `GO2_REWARD_EVIDENCE_MASTER.md` §2·§3·§5 | 아래 §3-A1 표와 일치 | 0 |
| A2 | 필수 | 다이얼 시도 이력표 신설 | 같은 파일 §1-a(최상단) | 유효·무효 실험 전부 기록, 결정 ID 인용 | 0 |
| A3 | 필수 | 정본 간 충돌 제거 | 기체 AGENTS §1·§7, registry, 검증 스크립트, 역할 문서, PLANNER_BRIEF, upload README | §3-A3 목록 전부 해소, 계약 테스트 통과 | 0 |
| A4 | 개선 | 인코딩 손상 구간 격리 | §3-A4 목록 | 손상 행마다 `CORRUPTED — 근거 사용 금지` 표시 | 0 |
| B1 | 개선 | 필독 목록 축소 | 신설 `GO2_NOW.md`, 기체 AGENTS §1, 루트 Go2 라우팅 §5, 역할 문서 입력 정본 | 필독 2개(`GO2_NOW.md` + 이력표) | 0 |
| B2 | 개선 | 처리량 지표 3종 | `GO2_NOW.md` 첫 화면 | 마지막 학습일·유효 비교 누적·잔여 GPU(실측일) | 0 |
| B3 | 필수 | 정본 일관성 검사 도구 | 신설 `tools/test_go2_canonical_consistency.py` | §3-B3 검사 6개 통과 | 0 |
| C1 | 필수 | 엔진에 A017 동결 기준선 등록 | `go2_tuning_config.py`, `tools/build_go2_tuning_engine.py`, 엔진 계약 테스트 | 계측 지문이 후보와 대칭이고 빌드가 재현됨 | 0 |
| C2 | 필수 | G-A030 값 선정·사전등록 | 원장 이력표, 실험 JSON | 이력표 인용, 비율이 아닌 값 근거 | 0 |
| C3 | 필수 | G-A030 실행 패키지 발행 | `upload/G-A030/current/` | 튜닝 요청 산출물 계약 6항 | 0 |
| C4 | 필수 | 서버 실행·회수 | 사용자 서버 | 결과 ZIP·report.html·SHA 회수 | 약 1~1.5h |

순서: A1 → A2 → A3 → B3 → (A4·B1·B2 병행 가능) → C1 → C2 → C3 → C4.
A1·A2가 먼저인 이유: C2의 값 선정이 이력표를 인용해야 하기 때문이다.
B3을 C보다 먼저 두는 이유: 틀린 정본 위에서 다시 패키지를 만드는 것을 막기 위해서다.

## 3. 단계별 상세

### A1. reward 원장 §2·§3·§5 정정

| 항 | 현재 문구(`GO2_REWARD_EVIDENCE_MASTER.md`) | 정정 후 상태 | 근거 |
|---|---|---|---|
| `track_lin_vel_xy_exp` | 미만족(G-A009·G-A023) | **부분 만족 — 1.4 채택(A017 기준선)**. G4·G6 손실 있음 | G-D184, A027 +6.09/70 |
| `feet_air_time` | 미만족(G-A007) | 보행 기준선에서 **0.35 기각**(A015 −30.12, 유효). 0.20은 Pilot·A017 유지값 | G-D73, A015 대칭 비교 |
| `lin_vel_z_l2` | 최종 기각(G-A010) | **보행 기준선에서 미탐색**. Default 위 기각은 철회됨 | G-D116 |
| `ang_vel_xy_l2` | 최종 기각(G-A024) | 보행 기준선에서 **강화(−0.15) 기각**(A016 −45.12, 유효). 완화 방향은 미탐색 | G-D77, G-D116 |
| `action_rate_l2` | **미측정** | 보행 기준선에서 **완화(−0.008) 기각**(A018 −44.40, 유효). 강화 방향은 미탐색 | G-D81, G-A029 감사 |
| `flat_orientation_l2` | 재측정 대기(G-A025) | **보행 기준선에서 유효 측정 없음.** A013·A025 후보도 7case 전부 속도 0.026~0.050 m/s로 정지 | G-D104, G-F170 |
| §3 만족/미만족 표 | "만족 없음 / feet·track 미만족" | 위 표 기준으로 다시 작성 | — |
| §5 마지막 문단 | "다음 reward 값 feet 0.20 확정" | `SUPERSEDED — 다음 후보는 이력표와 GO2_NOW.md NEXT를 따른다` | 감사 P1 |
| §1 현재 정책 역할 | 실험 기준선 Default-01 | 기준선 A017(model `0563deff…`, env `41050c08…`) | G-D113, G-D184 |

### A2. 다이얼 시도 이력표 (원장 최상단 §1-a)

칼럼: `항 · 방향·값 · 기준선 · 계측 지문(기준선/후보) · 기준선 보행 · 유효 · delta/70 · 결정 ID · 재시도`.
초안(시행 시 각 행을 `TIER1_DECISION.json`과 대조한다):

| 항 | 값 | 기준선 | 지문 | 보행 | 유효 | delta/70 | 결정 | 재시도 |
|---|---|---|---|---|---|---:|---|---|
| track | 1.2→1.4 | Pilot | v2/v2 | ✓ | ✓ | +3.71 (69case +6.09) | G-D184 채택 | 추가 상향은 G4·G6 확인 후 |
| feet_air | .2→.35 | Pilot | v2/v2 | ✓ | ✓ | −30.12 | G-D73 | 금지 |
| ang_xy | −.05→−.15 | Pilot | v2/v2 | ✓ | ✓ | −45.12 | G-D77 | 강화 금지 |
| action_rate | −.01→−.008 | Pilot | v2/v2 | ✓ | ✓ | −44.40 | G-D81 | 완화 금지 |
| feet_air | .01→.20 | Default | v1/v1 | ✗ | ✗ | +3.87 | 무효 | 정보 없음 |
| track | 1.0→1.2 | Default | v1/v1 | ✗ | ✗ | +3.09 | 무효 | 정보 없음 |
| lin_z | −3→−2 | Default | v1·v2 혼재 | ✗ | ✗ | +2.26 / −7.63 | G-D116 철회 | 미탐색 |
| flat | 0→−1 | Default | v1/v2 | ✗ | ✗ | −1.43 (A013=A025) | G-D104 | 미탐색 |
| ang_xy | −.08→−.15 | Default | v1/v2 | ✗ | ✗ | −17.13 | G-D116 철회 | 미탐색 |
| lin_z / ang_xy / feet | Chain-01 위 3건 | Chain-01 | v1/v2 | ✗ | ✗ | −18.18 / −6.61 / −13.73 | G-D116 철회 | 미탐색 |

> SUPERSEDED(F5, 2026-09-14 사용자 결정): "재시도" 칸의 "금지·강화 금지·완화 금지"는 영구 금지로 읽지 않는다.
> - 해당 값(feet .35, ang_xy −.15, action_rate −.008)은 유효 기각 이력이 있으므로, 새로운 검증 근거 없이 재시도하지 않는다.
> - 같은 방향의 다른 크기도 기존 실패와 구별되는 근거가 필요하다.
> - 근거: `reports/GO2_POST_A029_PLAN_POLICY_AUDIT_20260914.md` F5, 계획 `GO2_G_A029_REVISION_PLAN_20260914.md` R3.

규칙 한 줄을 표 위에 둔다: **새 후보 사양서는 이 표의 해당 항 행을 인용해야 발행된다(B3 검사가 강제).**

### A3. 정본 충돌 제거

| # | 위치 | 현재 | 조치 |
|---|---|---|---|
| 1 | 기체 `AGENTS.md:18-22` | 보존 비교군 Pilot, 기준선 Default-01 | 고정 식별자를 삭제하고 "현재 기준선은 `GO2_NOW.md`"로 바꾼다 |
| 2 | 기체 `AGENTS.md:103-106` §7 | 제출문 30~200자 | 루트 R-4a대로 "2라운드부터 500자, 수치와 이유"로 바꾼다 |
| 3 | `config/go2_self_eval_registry.json:157` | `maximum_characters: 200` | **시행 중 변경: registry는 고치지 않는다.** registry SHA `8d8c34ca…9ba6`가 A027 평가의 `registry_sha256` 지문이므로, 바꾸면 C1의 A017 기준선 대칭이 깨진다. 기체 AGENTS §7에 "1라운드 기록, 의도적 미변경"을 명시하고, B3 검사 3이 registry 해시 불변을 강제한다 |
| 4 | `tools/validate_go2_campaign.py:59` | `== 200` 단정 | 3과 같은 이유로 유지한다(1라운드 registry 기록 검사) |
| 5 | `.codex/agents/go2-campaign-manager.md:58` | "현재는 단계 0/6" | 삭제하고 `GO2_NOW.md` 참조로 바꾼다 |
| 6 | `PLANNER_BRIEF.md` §1~§6 | "G-A007만 승인", G-A007 NEXT | 머리에 `HISTORICAL — 260901 스냅샷`을 붙이고 현재 상태는 `GO2_NOW.md`로 옮긴다. REPORT-FIRST 블록은 유지한다 |
| 7 | `upload/README.md:14-16` Current experiment | G-A028 | G-A030 발행 전까지 "없음 — 다음은 G-A030 준비 중"으로 바꾼다 |
| 8 | 루트 `AGENTS.md` 학습 승인 §1 | Go2 사전등록 위치를 `H1_REWARD_EVIDENCE_MASTER.md`로 적음 | "Go2는 `GO2_REWARD_EVIDENCE_MASTER.md` §1-a"를 한 줄 추가한다 |

### A4. 인코딩 손상 격리
대상: `PLANNER_BRIEF.md:57-65, 83-88`, `GO2_REWARD_EVIDENCE_MASTER.md:371-376`, `GO2_PROJECT_STATE.md` §11(174행~)·1714행 절.
각 구간 머리에 `> CORRUPTED — 인코딩 손상, 근거 사용 금지. 대체 기록: <같은 날짜의 정상 절>`을 붙인다.
원문은 추측으로 복원하지 않는다.

### B1·B2. `GO2_NOW.md` (루트, 1쪽 상한 60줄)
내용:
- `## 0` 8항
- 현재 기준선 식별자
- 처리량 3종
  - 마지막 학습: 2026-09-07 A025
  - 유효 비교 누적: 5
  - 잔여 GPU: 9/8 운영자 확인 15h. 이후 A027 약 1.75h, A028 사용분은 미기록이므로 `[미측정 — 다음 접속 시 실측]`
- NEXT 한 줄
- 필독 2개 목록

**갱신 의무:** 학습 결과 판독, 기준선 변경, 서버 세션 종료 때마다 이 파일만 갱신하면 된다. 긴 원장은 조회·이력용으로 강등한다.
기체 AGENTS §1의 "8개 문서 순서대로 읽기"는 "`GO2_NOW.md`와 이력표를 읽고, 필요한 절만 조회"로 바꾼다.
역할 문서 4개의 입력 정본 목록 첫 줄에도 반영한다.

### B3. `tools/test_go2_canonical_consistency.py` 검사 7개 (시행 결과 반영)
1. 이력표 요약의 "현재 상태"가 원장 §2 판정 칸에 그대로 들어 있다.
   1b(추가). 원장 §2의 Pilot-01 열이 엔진 `FROZEN_BASELINES["Pilot-01"]`과 같다. 시행 중 ang_xy(−0.15)·flat(−1.0) 오기를 발견해 고쳤다.
2. 역할 문서·기체 AGENTS에 고정 단계("현재는 단계 N/6")가 없다. 모두 `GO2_NOW.md`로 연결되고, test-planner "현재 기준선" 절은 `GO2_NOW.md`를 가리킨다.
3. **변경:** 루트·기체 AGENTS가 모두 500자를 적는다. registry 파일 SHA가 `GO2_NOW.md`의 `REGISTRY_SHA256`과 A027 identity의 `registry_sha256`과 같다(지문 동결).
4. **변경:** `GO2_NOW.md` 기준선 model·env SHA가 `_keep` A017 산출물의 실제 해시와 A027 identity와 같다. 엔진 `FROZEN_BASELINES` 대조는 C1 이후로 미룬다.
5. `config/experiments/G_A030` 이후 사양은 `dial_history_ref`를 갖고, 그 문자열이 §1-a에 있다.
6. `GO2_NOW.md`의 `LAST_TRAINING_WORK_ID`가 `_keep`에서 학습 산출물이 있는 최신 work ID보다 작지 않다.

`_keep`이 없는 환경에서는 4·6을 skip한다.

기존 `test_go2_report_first_contract.py`와 `validate_go2_campaign.py`도 함께 통과해야 한다.

### C1. 엔진에 A017 기준선 등록 (engine 1.5.4 → 1.6.0)
- `FROZEN_BASELINES["A017"]`
  - rewards: track 1.4 · feet .2 · lin_z −2.0 · ang_xy −.05 · action_rate −.01 · flat 0.0
  - model·env SHA: `_keep/go2_g_a017_pilot_track_lin_vel_xy_140/training/`의 전체 값
  - `locomotion_status=BASELINE_WALKS_VERIFIED_69_CASE` (A027 `POLICY_LOCOMOTES`)
- `_a017_baseline_payload()`
  - 원천: `_keep/go2_a017_full_suite/evaluation/a017/cases/seed_101/`의 tier-1 7case(summary schema 6, `posture_gate_v2`)
  - `SOURCE=VERIFIED_G_A027`로 기록한다
- **대칭 확인(필수):** 현재 엔진이 후보를 채점하는 telemetry schema·게이트 파라미터·evaluator SHA가 A027 캐시와 같은지 계약 테스트로 확인한다.
  - 다르면 캐시를 쓰지 않는다. 기준선 arm도 서버에서 다시 잰다(약 +15분).
  - 다른 지문으로 판정하는 경로는 두지 않는다(G-D109).
- 차단 사유: 빌드·계약 테스트 실패는 튜닝 요청 산출물 계약의 차단 사유 ②에 해당한다. 이때는 수리만 하고 대체 문서를 만들지 않는다.

### C2. G-A030 값 선정·사전등록 — 병행 계획 채택

> **2026-09-14 재판정(본문 미수정):** 아래 flat -1 채택은 후보 비교 없이 정한 것이라 효력을 멈춘다. G-A030 후보는 원장 §5 비교표(기대 가중 이득·실험 비용·원인 확실성, G-D-PRIORITY-20260914)로 다시 고른다. flat -1은 비교 대상 후보로 보존한다. 근거: `reports/GO2_POST_A029_PLAN_POLICY_AUDIT_20260914.md` §7.
같은 날 별도 세션이 `GO2_POST_A029_TUNING_PLAN_20260914.md`(GO2-REPLAN-A029-20260914)를 작성했다.
값과 판정 기준은 **그 계획 §4·§5를 그대로 채택**하고, 이 계획에서 새 값을 따로 정하지 않는다. 두 계획이 서로 다른 값을 내는 상황을 막기 위해서다.
- 값: A017 조합에서 `flat_orientation_l2 0.0 → -1.0`만 변경.
- 표적: G3 `rough_lateral` 생존. G5는 동시 측정 대상이다.
- 값 근거: A027 rough_lateral 종료 직전 0.5초 기울기 q = .628~.688(비가중)이다. 이 관측 크기에 선택 압력을 주는 단위 크기 탐색이다. 비율·중간값 근거가 아니며 upstream 부모값은 0.0이라 추천 근거가 아니다(그 계획 §4에 명시).
- 판정 기준: 그 계획 §5를 사전등록 정본으로 쓴다.
  - 성공: G3 최저 생존 ≥ +.10, 총 proxy ≥ +1.0/70, case별 비열등.
  - 메커니즘 보강: rough_lateral 종료 개체 수 감소.
  - 기각: G4·G5 회귀 시 후보를 폐기한다. 비율로 재탐색하지 않는다.
- 이 계획이 추가하는 조건 두 가지:
  1. 사양 JSON에 A2 이력표의 `flat` 행 인용(`dial_history_ref`)을 넣는다(B3 검사 5).
  2. 그 계획 §5-4("새로운 evaluator면 양쪽 재평가")는 C1의 대칭 확인 결과로 결정한다.
- 차순위(그 계획 §4 대안과 동일): `ang_vel_xy_l2` 완화, `lin_vel_z_l2`. action_rate 완화는 제외한다(A018).

### C3. G-A030 패키지 — 튜닝 요청 산출물 계약 6항
1. `upload/G-A030/current/` 실행 ZIP + SHA
2. 로컬 검증: 단일변수 diff, LF, `bash -n`, CRC/SHA, report 회수 경로 테스트
3. 한 줄 실행 명령
4. 결과 ZIP 경로(`/workspace/_keep/…RESULT.zip` + `.sha256`)
5. 서버 종료 게이트: 기체 AGENTS §9-a
6. `UPLOAD_HISTORY.tsv`, `upload/README.md` Current experiment 갱신

발행 전 ID 중복을 확인한다. 원장·upload에 G-A030이 없어야 한다(G-D98).

### C4. 서버 실행
- 접속 즉시 잔여 GPU를 실측하고 `GO2_NOW.md`에 적는다.
- 결과 회수 뒤 artifact 검증 → tier-1 판독 → 이력표·`GO2_NOW.md` 갱신을 같은 턴에 끝낸다.

## 4. 완료 판정과 검증 명령
- 단계 A·B 완료: `python -m unittest tools.test_go2_report_first_contract tools.test_go2_canonical_consistency`, `python tools/validate_go2_campaign.py`, 편집한 모든 파일의 UTF-8 검사.
- 단계 C1 완료: 엔진 계약 테스트 전부 통과, 엔진 ZIP 재빌드 SHA 재현.
- 단계 C3 완료: 위 6항과 패키지 계약 테스트 통과.
- 각 단계 완료 시 `GO2_PROJECT_STATE.md`에 한 절, `GO2_NOW.md`에 상태 한 줄을 남긴다.

## 5. 위험과 대응

| 위험 | 대응 |
|---|---|
| 정정 중 과거 판정을 소급 변경 | 현재 상태 문구만 고치고 과거 행은 `SUPERSEDED`로 둔다 |
| 기존 계약 테스트 파손 | §1-3의 고정 문자열 블록을 보존하고 단계마다 테스트를 실행한다 |
| A027 캐시와 현재 엔진의 지문 불일치 | 기준선 재측정으로 전환한다. 비대칭 판정 경로는 금지 |
| `GO2_NOW.md`가 또 하나의 방치 문서가 됨 | B3 검사 4·6이 기준선 SHA와 마지막 학습일을 강제한다 |
| flat 항이 G4·G5를 악화 | 사전등록 실패 조건으로 즉시 기각한다. 크기 재탐색은 이력표 근거가 있을 때만 한다 |

## 6. 하지 않는 것
- 과거 원장 절·승인 ZIP·회수물 삭제나 재작성
- Default-01·Chain-01 위 새 학습(G-D113)
- review ZIP·진단 계획 등 대체 산출물(G-A030은 `current/` 실행 패키지로만 낸다)
- 서버 설치나 배포 학습 코드 수정(R-6)

## 7. 사용자 결정 필요
1. **필독 문서를 2개(`GO2_NOW.md` + 이력표)로 줄이는 것(B1)을 승인하는가.** 기존 지침 8문서 필독 규칙을 바꾸는 결정이다.
2. **A~C를 한 번에 진행하는가, A·B 완료 후 확인받고 C로 가는가.** 권장은 A→B→C 연속 진행이다. C1 계약 테스트가 실패하면 그 자리에서 멈추고 보고한다.
