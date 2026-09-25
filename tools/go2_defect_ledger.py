"""감사가 찾은 결함을 **파일로** 남긴다 — 대장과 증거 CSV를 함께 만든다.

이 도구가 존재하는 이유.  2026-09-19 에 사용자가 물었다: "확인을 요청할 때마다 왜 문제가
터지느냐".  뿌리를 찾아보니 결함 자체가 아니라 **결함을 적어두는 곳이 없다**는 것이었다.

    grep -rl "결함 표" workspace/training/quadruped/reports/*.md  ->  0건
    2026-09-14 감사는 파일 3개로 남았다.  2026-09-18 · 2026-09-19 감사는 0개다.
    `.claude/agents/go2-auditor.md:97-98` 의 보고 형식은 "결론 한 줄 + 결함 표"이고
    **파일 경로가 없다** — 감사자의 출력이 반환값이라 대화가 끝나면 사라진다.

그래서 G-1 · G-2 · A-7 은 이전 감사에서 이미 나왔는데도 다음 감사자가 **처음부터 다시 찾았다**.
결함 수가 산출물 품질이 아니라 *마지막 확인 이후 경과 시간*의 함수가 된 원인이 이것이다.

숫자와 상태를 사람이 문서에 손으로 적으면 같은 실패를 반복하므로, 기록은 아래 `DEFECTS` 한
곳에만 두고 문서 · CSV 는 이 도구가 만든다.  상태를 바꾸는 방법은 이 파일을 고치는 것뿐이다.

상태:
    OPEN      아직 안 고쳤다.
    FIXED     원천에서 고쳤다.  `resolution` 에 고친 파일과 그것을 지키는 관문을 적는다.
    ACCEPTED  사용자가 알고 받아들였다.  `resolution` 에 언제 · 무슨 근거로 받아들였는지 적는다.
              **감사자나 기획자는 ACCEPTED 로 못 바꾼다** — 그것은 사용자 결정이다.
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
OUT_DOC = QUAD / "reports/GO2_DEFECT_LEDGER.md"
OUT_DIR = QUAD / "reports/evidence/go2_defect_ledger"
OUT_CSV = OUT_DIR / "DEFECTS.csv"

FIELDS = ("id", "found_on", "found_by", "confidence", "severity", "status", "where", "what",
          "repro", "repro_expect", "verbatim", "source_checked", "origin_fix", "resolution")

# 2026-09-19.  대장에 `confidence` · `repro` · `verbatim` 이 생긴 이유.
#
# 이 세션에서 철회된 주장 4건 중 3건이 **감사자의 결함이 아니라 내 중계**에서 나왔다.
# D-0 이 표본이다.  감사자는 정확한 줄(`test_go2_claim_check_contract.py:65-66`)을 짚고,
# 재현 명령(`git cat-file -e HEAD:<path>` 전수 실패)을 달고, 범위를 "**선언된** 집행 기제"로
# 한정하고, **`test_2`(상한-실측 < 5)가 상한을 조이고 있다는 사실까지 적은 뒤** 자기 결론을
# `[모름]` 으로 표시했다.  나는 그것을 "커밋 금지라 원리적으로 집행 불가, 사용자 결정 필요"로
# 바꿔 전했다 — 원본에 없는 문장이다.
#
# 그래서 결함마다 **발견자의 원문**과 **재현 명령**을 같이 싣는다.  중계가 원문보다 세지면
# 원문을 열어 대조할 수 있고, 재현 명령이 없는 결함은 `확인` 이 아니라 `추정`이다.
#
#   확인  `repro` 가 **실행되는 파이썬 코드**이고, 관문이 그것을 돌려 `repro_expect` 가 나오는지
#         확인한다(`tools/test_go2_defect_ledger_contract.py::test_3b`).
#   추정  보고는 받았으나 아직 재현하지 않았다 — 중계할 때 확신을 올리지 않는다.
#
# 2026-09-19 침투 시험: `repro` 가 산문이던 판에서는 "아무 말이나 적어도 된다"를 넣고 `확인`이라
# 주장해도 관문 10/10 이 통과했다.  자칭 딱지는 관문이 아니다 — 그래서 실행으로 바꿨다.
# `repro` 는 저장소 최상위에서 `python -B -c <repro>` 로 돌아가며, 표준출력에 `repro_expect` 가
# 그대로 들어 있어야 한다.  OPEN 결함이면 결함이 아직 있음을, FIXED 결함이면 고침이 아직
# 자리에 있음을 보인다 — 닫힌 결함의 회귀 관문 노릇을 겸한다.
CONFIDENCE = ("확인", "추정")

# 결함 설명에 인용한 수치.  `figures` 에 **한 칸에 하나씩** 다시 내보내는 이유:
# 주장 검사의 `own_values`(`tools/go2_claim_check.py:371`)는 CSV 의 **칸 전체**만 근거로 받는다.
# `what` 산문 칸 안에 박힌 `5.523` 은 칸 전체가 아니라서 '근거 없음'으로 잡힌다(2026-09-19 실측 5건).
# 그래서 인용 수치를 아래 표로 한 번 더 낸다 — 손으로 문서에 적는 대신 생성기가 낸다.
FIGURE_FIELDS = ("id", "figure", "means")

# 심각도 정렬 순서 — 문서의 행 순서를 사람이 정하지 않게 한다.
SEVERITY_ORDER = {"중대": 0, "경미": 1}
STATUS_ORDER = {"OPEN": 0, "ACCEPTED": 1, "FIXED": 2}

DEFECTS: tuple[dict, ...] = (
    dict(
        id="X-1", found_on="2026-09-19", found_by="감사자/PM 직접확인", confidence="확인",
        repro="import hashlib,subprocess,pathlib;z=pathlib.Path('workspace/training/quadruped/"
              "go2_feet_air_time_020_v2.zip');h=hashlib.sha256(z.read_bytes()).hexdigest();"
              "c=hashlib.sha256(subprocess.run(['git','show','HEAD:workspace/training/quadruped/"
              "go2_feet_air_time_020_v2.zip'],capture_output=True).stdout).hexdigest();"
              "print('matches_head',h==c,'bytes',z.stat().st_size)",
        repro_expect="matches_head True bytes 34298008",
        severity="중대", status="FIXED",
        where="workspace/training/quadruped/go2_feet_air_time_020_v2.zip(+.sha256)",
        what="이미 발행된 회차 ZIP 의 바이트가 34298008 -> 34298254 로 바뀌었고 .sha256 도 함께 고쳐져 "
             "현재 파일과 기록이 일치한다 — 어떤 관문도 이 변경을 잡지 못한다. 불변 릴리스 규칙 위반.",
        source_checked="git diff --stat HEAD; 현재 sha256 ce53c262…dd9b / HEAD 기록 cc43ac30…5c34e. "
                       "ZIP 내용 대조(2026-09-19): 항목 95개로 동일, 추가·삭제 0건, 변경 2건 — "
                       "GO2_FEET_AIR_TIME_020_SCREENING_PRD.md 와 PACKAGE_SHA256SUMS.txt. "
                       "실제 변경은 `## 9 PARTIAL` 절에 'CORRUPTED — 인코딩 손상, 근거 사용 금지' "
                       "경고 배너 한 줄 추가이고 조작이 아니다. 현재 파일은 스크래치패드에 보존.",
        origin_fix="사용자 결정(HEAD 로 되돌릴지 / 현재 파일이 정본인지). PM 권고: HEAD 로 되돌리고 "
                   "경고문은 ZIP 밖(VERIFICATION.md 또는 이 대장)에 둔다 — 얼어붙은 산출물에 주석을 "
                   "다는 것이 불변 규칙이 막으려던 일이다. 어느 쪽이든 발행 ZIP 의 바이트 변경을 "
                   "잡는 관문을 추가한다(.sha256 을 같이 고치면 현재 관문이 못 잡는다).",
        resolution="2026-09-19 사용자 승인으로 ZIP 과 .sha256 을 HEAD 로 되돌렸다 — 바이트 34298008, "
                   "sha256 cc43ac30…5c34e, 기록과 일치, git status 에서 사라졌다. 경고문은 산출물 "
                   "밖 go2_feet_air_time_020_v2.NOTICE.md 에 옮겼다(VERIFICATION.md 는 추적 중이고 "
                   "안 바뀐 상태라 건드리지 않았다). 관문 "
                   "tools/test_go2_published_release_contract.py 4/4 — 기준을 파일 옆 체크섬이 "
                   "아니라 HEAD 에 둔다. 침투 시험: 1바이트 추가 + .sha256 동시 갱신(X-1 과 같은 "
                   "수법)을 심었더니 잡았다. 되돌리기 전 파일은 스크래치패드에 보존.",
    ),
    dict(
        id="D-0", found_on="2026-09-19", found_by="감사자", confidence="확인",
        severity="중대", status="FIXED",
        repro="t=open('tools/test_go2_claim_check_contract.py',encoding='utf-8').read();"
              "print('test_2f',('def test_2f' in t),'test_3b',('def test_3b' in t))",
        repro_expect="test_2f True test_3b True",
        verbatim="감사자 원문: 「`tools/test_go2_claim_check_contract.py:65-66`은 래칫의 집행 근거를 "
                 "\"늘리려면 이 상수를 같이 올려야 하고, 그러면 커밋에 그 의도가 남는다\"로 적는다. "
                 "그 커밋이 존재하지 않으므로 래칫의 선언된 집행 기제가 지금 작동하지 않는다.」 "
                 "같은 감사문에 「현재 실측 대 상한이 전부 붙어 있다(PROJECT_STATE 50/51, "
                 "MASTER 35/37, 나머지 전부 동일). test_2(상한-실측 < 5)가 통과하는 것도 같은 "
                 "방향이다. 확정은 [모름]」 이라고 적혀 있었다. "
                 "**PM 중계 오류**: 나는 이것을 '커밋 금지라 원리적으로 집행 불가, 사용자 결정 필요'로 "
                 "바꿔 전했다 — 원문에 없는 문장이고, 감사자가 이미 적어둔 test_2 를 떨어뜨린 결과다.",
        where="tools/test_go2_claim_check_contract.py:65-66 (래칫의 집행 근거 진술)",
        what="주장검사 래칫은 상한이 낮아지지 않았다는 것을 커밋 이력으로 집행한다고 선언하는데, "
             "도구 6개가 전부 untracked 라 그 이력이 존재하지 않는다 — 선언된 집행 수단이 없다.",
        source_checked="git status --porcelain (tools/go2_*.py 다수 ??)",
        origin_fix="래칫의 집행 근거를 커밋이 아니라 **실측**으로 바꾼다. 사용자에게 커밋 허용을 "
                   "요구하지 않는다 — 집행 수단을 커밋으로 정한 것은 우리 설계이고, 사용자 제약과 "
                   "맞지 않으면 설계를 바꾸는 것이 우리 일이다.",
        resolution="CEILING 은 이미 실측에 묶여 있었다(test_2 가 상한-실측 간격 5 이상이면 깨진다) "
                   "— 커밋에 기댄 것은 DERIVED_CEILING 한 곳뿐이었다. 그 주석을 고치고 같은 조임을 "
                   "나머지 둘에 걸었다: test_2f(BLIND_CEILING, 현재 최대 여유 2) · "
                   "test_3b(DERIVED_CEILING, 8/8). 이제 상한을 미리 부풀려 둘 수 없으므로 커밋 "
                   "이력 없이 래칫이 작동한다. tools/test_go2_claim_check_contract.py 13/13 통과.",
    ),
    dict(
        id="S-2", found_on="2026-09-19", found_by="감사자/PM 직접확인", confidence="확인",
        repro="import json;g=json.load(open('workspace/training/quadruped/config/experiments/G_A040_a033_flat_orientation_m05.json',encoding='utf-8'))['preregistered']['climb_guard']['groups'];print({k:round(v['baseline_sum']-v['max_drop'],3) for k,v in g.items()})",
        repro_expect="'stairs_15_climb_ge1': -1.523",
        severity="중대", status="FIXED",
        where="tools/go2_fact_rules_spec.py climb_group()",
        what="반증 하한이 baseline_sum - max_drop 인데 음수 클램프가 없다. stairs_15_climb_ge1 은 "
             "4 - 5.523 = -1.523 이라 어떤 결과로도 발화할 수 없다 — 15cm 역방향 관문이 죽어 있다.",
        source_checked="tools/go2_fact_rules_spec.py climb_group() 본문; max_drop = 2*sqrt(var)",
        origin_fix="하한을 0 이상으로 클램프하거나, 표본이 부족해 하한이 0 이하가 되는 관문은 "
                   "'발화 불가'로 명시적 실패시킨다. 후자가 맞다 — 조용히 통과하는 관문이 더 위험하다.",
        resolution="tools/go2_fact_rules.py:64 — 하한이 0 이하면 ok=None·inoperable 로 표시하고 "
                   "violations 에 소리를 낸다. 0 클램프는 소용없다(오른 로봇 수가 음수가 못 되므로 "
                   "하한 0 도 발화 불가). 관문 tools/test_go2_fact_rules_contract.py::test_3 이 "
                   "발화 불가 집합을 {stairs_15_climb_ge1} 로 못 박아 늘어날 수 없게 한다. 8/8 통과.",
    ),
    dict(
        id="S-4", found_on="2026-09-19", found_by="감사자", confidence="확인",
        repro="import pathlib;print(sorted(q.name for q in pathlib.Path('tools').glob('*.py') if 'stationary_guard_scenarios' in q.read_text(encoding='utf-8')))",
        repro_expect='go2_target_gate.py',
        severity="중대", status="FIXED",
        where="tools/go2_target_gate.py",
        what="서버 1단계 게이트가 사양의 stationary_guard_scenarios 를 읽지 않는다. 정지 편법을 "
             "잡는 것이 평지 1케이스뿐이라 G2/G6 이 구조적으로 안 보인다. G-A038 이 이 구멍의 실증 "
             "— 평지는 걷고 계단에서만 웅크렸는데 파국 관문이 통과했다.",
        source_checked="tools/go2_target_gate.py 전문; 유일한 독자는 tools/verify_go2_basic_motion_harvest.py",
        origin_fix="go2_target_gate.py 가 stationary_guard_scenarios 를 읽게 하고, 읽었다는 사실을 "
                   "계약 테스트로 고정한다.",
        resolution="tools/go2_target_gate.py 에 stationary_reading() 을 넣어 1단계가 자기가 읽는 "
                   "case(파국+표적)에 채점기와 같은 기준을 적용한다. 관문 "
                   "tools/test_go2_stationary_guard_contract.py 8/8 — 합성 기록으로 실제 발화를 "
                   "확인했고 test_7 이 채점기 상수와 대조한다. G-A040 기준 1단계 감시 대상 "
                   "0 -> 10 case(G1 1 + G3 6 + G4 3, 한도 0). "
                   "**한계**: G2·G6·G7 은 1단계가 그 case 를 측정하지 않아 여전히 전체 단계에서만 "
                   "본다. G5 는 설계상 감시 밖이라 G-A038 형 계단 웅크림은 1단계에서 여전히 "
                   "안 잡힌다 — 같은 편법이 G3 에서 나오면 이제 잡힌다. 회귀: fact_rules 8/8.",
    ),
    dict(
        id="S-1", found_on="2026-09-19", found_by="감사자", severity="중대", status="OPEN",
        where="config/experiments/G_A040_a033_flat_orientation_m05.json value_derivation.rule",
        what="'세 갈래 독립 근거'라고 적었으나 PROBE_SITUATIONS 는 가중치에 완전 선형이고 "
             "TERM_VALUES.csv 에 이 항의 학습 로그가 0행이다. 선형 탐침은 문턱 정보를 원리적으로 "
             "담을 수 없다. 결함은 값이 아니라 **문장**이다.",
        source_checked="PROBE_SITUATIONS.csv, TERM_VALUES.csv (flat_orientation_l2 0행)",
        origin_fix="사양의 근거 문장을 '선형 외삽 1갈래 + 외부 기준 대조'로 정정하고, 선형 탐침을 "
                   "독립 근거로 세는 것을 금지하는 규칙을 감사 체크리스트에 넣는다.",
        resolution="",
    ),
    dict(
        id="S-3", found_on="2026-09-19", found_by="감사자", severity="중대", status="OPEN",
        where="G_A040 사양이 인용한 외부 기준 go2_flat = -2.5",
        # 설정값은 백틱으로 가린다 — 주장 검사의 맹점(2자리 이하)을 늘리지 않기 위해서다.
        what="증거 폴더에 이 값의 원문 파일이 없다. Isaac Lab Go2 rough = `0.0` 은 원문 확인됐지만 "
             "`-2.5` 는 우리 JSON 진술뿐인데 사양이 그것으로 정당성을 빌려온다.",
        source_checked="reports/evidence/ 외부 기준 폴더; go2_external_reference_diff.py 출력",
        origin_fix="원문 파일을 증거로 넣거나, 넣지 못하면 사양에서 `-2.5` 인용을 삭제한다.",
        resolution="",
    ),
    dict(
        id="B-1", found_on="2026-09-19", found_by="감사자", severity="중대", status="OPEN",
        where="tools/build_go2_training_length_package.py:171, tools/build_go2_candidate_package.py:144",
        what="표적 상한을 9 -> 12 로 넓혔는데 12 가 유도되지 않았다. G-A040 의 표적이 정확히 "
             "3+6+3=12 이고 다른 사양 4개는 전부 9 다. 값을 정하는 역할이 그 값을 검사할 관문 "
             "상수까지 고친 것 — 부주의가 아니라 권한 설계 결함이다. 두 빌더가 서로 불일치(144줄은 아직 9).",
        source_checked="build_go2_training_length_package.py:171, build_go2_candidate_package.py:144, "
                       "기존 사양 4건의 표적 수",
        origin_fix="상한을 유도하거나 9 로 되돌린다. 더 근본적으로: 사양이 관문 상수를 바꾸면 "
                   "gate_constants_changed 에 적게 하고, 그 회차는 감사자 승인 없이 못 올리게 한다.",
        resolution="",
    ),
    dict(
        id="P-1", found_on="2026-09-19", found_by="감사자", confidence="확인",
        # 2026-09-20: 원래 이 repro 는 GO2_PROJECT_STATE.md 안의 '2026-09-19' **문자열 수**를 셌다.
        # 그날 다른 작업이 09-19 판독을 인용하자 0 -> 1 이 되어 관문이 울었는데, 결함(09-19 실수
        # 3건이 보존 사례로 등재되지 않았다)은 그대로였다.  **측정이 결함을 보지 않고 있었다** —
        # 지나가는 언급 하나로 뒤집히는 값이었다.  그래서 보존 사례 대장(CASES.csv)의 09-19 행 수를
        # 직접 센다.  C09~C11 이 등재되면 이 값이 0 에서 올라가고 관문이 그때 운다.
        repro="import csv,pathlib;rows=list(csv.DictReader(pathlib.Path("
              "'workspace/training/quadruped/reports/evidence/go2_role_regression_20260918/CASES.csv')"
              ".open(encoding='utf-8')));"
              "print('cases_0919',sum(1 for r in rows if '2026-09-19' in ','.join(r.values())),"
              "'cases_rows',len(rows))",
        repro_expect='cases_0919 0 cases_rows 14',
        severity="중대", status="OPEN",
        where="tools/go2_role_regression.py CASES, GO2_PROJECT_STATE.md",
        what="2026-09-19 의 실수 3건이 보존 사례로 등재되지 않았다. CASES.csv 14행에 09-19 항목이 "
             "0건이다. 보존 사례 규칙 위반. (2026-09-20 정정: 처음에는 'GO2_PROJECT_STATE.md 에 "
             "2026-09-19 문자열이 0건'도 근거로 적혀 있었는데, 그 값은 지나가는 인용 하나로 바뀌는 "
             "값이라 결함의 척도가 아니었다 — 실제로 09-20 작업이 09-19 판독을 인용하자 1 이 됐다. "
             "결함 자체는 그대로 OPEN 이다.)",
        source_checked="reports/evidence/go2_role_regression_20260918/CASES.csv (C01-C08, M01-M06), "
                       "GO2_PROJECT_STATE.md 전문 검색",
        origin_fix="생성기 CASES 에 C09/C10/C11 을 추가하고(CSV 를 손으로 고치지 않는다) "
                   "PROJECT_STATE 에 09-19 행을 넣는다.",
        resolution="",
    ),
    dict(
        id="R-1", found_on="2026-09-19", found_by="감사자", severity="중대", status="OPEN",
        where="tools/test_go2_a038_reread_contract.py (없음)",
        what="분석가 재판독문 GO2_A038_REREAD_20260919.md 에 계약 테스트가 없다. 200여 수치를 "
             "지키는 것이 존재 관문뿐이라, 감사자가 조작값 0.7431 을 심었더니 통과했다.",
        source_checked="ls tools/test_go2_*.py (47개 중 reread 없음); 감사자의 조작값 삽입 시험",
        origin_fix="계약 테스트를 만들고, 더 근본적으로 분석가 역할 파일에 '계약 테스트까지가 "
                   "자산이다'를 명시한다.",
        resolution="",
    ),
    dict(
        id="A-1", found_on="2026-09-19", found_by="감사자", confidence="확인",
        repro="t=open('tools/go2_table_audit.py',encoding='utf-8').read();i=t.index('BINDINGS');print('reread_bound',('A038_REREAD' in t[i:i+2000]))",
        repro_expect='reread_bound False',
        severity="중대", status="OPEN",
        where="tools/go2_table_audit.py:121 BINDINGS",
        what="BINDINGS 가 손으로 적은 5개 표뿐이고 전부 GO2_RUN_SYNTHESIS 에서 온다 — 재판독문의 "
             "귀속 결속은 0건이다. 손 목록이라 새 문서는 태어날 때 항상 무관문이다.",
        source_checked="tools/go2_table_audit.py:121 BINDINGS 전문",
        origin_fix="reports/*.md 를 자동 열거해 DOC_SOURCES · BINDINGS · 계약 테스트 중 어느 것에도 "
                   "걸리지 않는 문서를 실패시키는 관문을 만든다. 손 목록의 반대편이 필요하다.",
        resolution="",
    ),
    dict(
        id="D-1", found_on="2026-09-19", found_by="감사자", severity="중대", status="OPEN",
        where="tools/test_go2_claim_check_contract.py::test_5b",
        what="새로 넣은 own_rounded 완화 경로를 시험하는 관문이 없다. test_5b 는 결속되지 않은 "
             "새 파일에 탐침을 심어서 own_rounded 경로를 한 번도 지나지 않는다. "
             "(누수는 없음이 실측 확인됐으나, 문서별 오탐률이 `0.05`~`1.8`%p 늘었다.)",
        source_checked="tools/test_go2_claim_check_contract.py::test_5b; 감사자 오탐률 측정",
        origin_fix="결속된 문서에 탐침을 심어 own_rounded 경로를 실제로 지나는 관문을 추가한다.",
        resolution="",
    ),
    dict(
        id="G-1", found_on="2026-09-18", found_by="감사자(이전 회차)", severity="중대", status="OPEN",
        where="정본 일치 관문",
        what="이전 감사에서 이미 보고됐으나 적어둔 곳이 없어 그대로 남았다.",
        source_checked="(이전 감사 기록이 파일로 없어 원본 재인용 불가 — 이 결함 자체가 X-대장 부재의 증거)",
        origin_fix="이 대장에 옮겨 적었으므로 다음 감사에서 재발견이 아니라 상태 갱신으로 처리한다.",
        resolution="",
    ),
    dict(
        id="G-2", found_on="2026-09-18", found_by="감사자(이전 회차)", severity="중대", status="OPEN",
        where="철회된 G5 주장",
        what="철회된 G5 주장이 아직 [확인] 표시를 달고 있는데 정본 일치 관문 16/16 이 그것을 보지 않는다.",
        source_checked="tools/test_go2_canonical_consistency.py 검사 범위",
        origin_fix="철회 표시를 정본 일치 관문의 검사 대상에 넣는다.",
        resolution="",
    ),
    dict(
        id="A-7", found_on="2026-09-18", found_by="감사자(이전 회차)", severity="중대", status="OPEN",
        where="(이전 감사 항목)",
        what="이전 감사에서 보고됐으나 적어둔 곳이 없어 그대로 남았다.",
        source_checked="(이전 감사 기록이 파일로 없어 원본 재인용 불가)",
        origin_fix="다음 감사자가 원본을 다시 특정하면 이 행을 갱신한다.",
        resolution="",
    ),
    dict(
        id="PM-1", found_on="2026-09-19", found_by="사용자", confidence="확인",
        repro="import sys;sys.path.insert(0,'.');import tools.go2_defect_ledger as l;d={x['id']:x for x in l.DEFECTS}['D-0'];v=l.field(d,'verbatim');print('has_test_2',('test_2' in v),'has_unknown',('[모름]' in v))",
        repro_expect='has_test_2 True has_unknown True',
        severity="중대", status="OPEN",
        where="PM 보고(대화)",
        what="차단 사유가 아닌 항목 셋(X-1 · D-0 · 외부 기준 이탈)을 '사용자 결정 대기'로 돌리고 "
             "작업을 멈췄다. AGENTS.md:56-58 의 차단 사유는 R-6 위반 · 테스트 실패 · 회수 불가 "
             "셋뿐이고 과학적 불확실성은 사전등록 항목이다. D-0 은 사용자 제약(커밋 금지)을 풀라는 "
             "압박이었고, 요청받지 않은 상시 결재 의무('ACCEPTED 는 사용자만')를 새로 만들어 지웠다. "
             "같은 답변에서 'PM 보고문만 관문이 없다'고 진단해놓고 그 실패를 그대로 저질렀다.",
        source_checked="사용자 2026-09-19 지적('왜 이렇게 이야기한거야'); AGENTS.md:56-58",
        origin_fix="래칫 집행 근거를 커밋 이력이 아니라 선언된 상수로 바꾼다(CEILING 방식). "
                   "외부 기준 이탈은 사양의 사전등록 항목으로 적고 진행한다. PM 보고문이 인용하는 "
                   "수치는 주장 검사를 통과한 문서 경유로만 낸다. 이 사례를 "
                   "tools/go2_role_regression.py CASES 에 보존 사례로 넣는다(P-1 과 함께).",
        resolution="",
    ),
    dict(
        id="R-2", found_on="2026-09-19", found_by="감사자", severity="경미", status="OPEN",
        where="reports/GO2_A038_REREAD_20260919.md:131",
        what="1.786 으로 적혔으나 원자료는 1.785 다 — 손으로 옮겨 적은 수치의 전형적 실패.",
        source_checked="증거 CSV 원값",
        origin_fix="생성기 tools/go2_a038_reread.py 가 이 셀을 만들게 한다(문서를 손으로 고치지 않는다).",
        resolution="",
    ),
    dict(
        id="B-3", found_on="2026-09-19", found_by="감사자", severity="경미", status="OPEN",
        where="reports/GO2_A038_REREAD_20260919.md 델타 셀 3개",
        what="델타 3칸이 손으로 뺀 값이다. 값 자체는 맞지만 생성기를 거치지 않아 다음 회차에 어긋난다.",
        source_checked="증거 CSV 와 문서 대조",
        origin_fix="생성기가 델타를 계산해 내보내게 한다.",
        resolution="",
    ),
    dict(
        id="C-1", found_on="2026-09-20", found_by="기획자/직접확인", confidence="확인",
        severity="중대", status="FIXED",
        repro="t=open('workspace/training/quadruped/upload/G-A041/current/CURRENT_UPLOAD.txt',"
              "encoding='utf-8').read();print('claims_old_rule',('옛 판정 규칙' in t),"
              "'claims_runner_defect',('러너 결함' in t))",
        repro_expect="claims_old_rule False claims_runner_defect False",
        where="tools/build_go2_training_length_campaign.py publish() -> upload/*/current/CURRENT_UPLOAD.txt",
        what="첫 발행인 G-A041 의 안내문이 '직전 판은 옛 판정 규칙(9 case 평균·이득 추정 waiver)으로 "
             "대체됐다. 그 전 판은 러너 결함으로 대체됐다'를 달고 나왔다. 그 문단은 G-A035/37/38/39 의 "
             "이력이고 G-A041 에는 그런 판이 없다. 조건이 'history 폴더가 비어 있지 않으면'이었는데, "
             "회차 ZIP 을 만들면 arm 빌더가 staged 판을 history 에 남기므로 첫 발행에도 붙는다. "
             "G-A039 v5 결함(판 수를 supersedes 로 읽어 '첫 판이다'라고 적음)과 같은 자리의 반대 방향 "
             "오류다 — 발행문이 자기 이력을 스스로 세는 규칙은 고쳤는데, 그 이력에 붙는 **이유**는 "
             "여전히 한 회차의 것이 전부에게 붙고 있었다.",
        source_checked="upload/G-A041/history/20260920_a033_ang_vel_xy_m004_one_command_v1/CURRENT_UPLOAD.txt "
                       "(보존된 v1 바이트)와 publish() 의 runner_note 분기.",
        origin_fix="이유를 회차별 CAMPAIGNS['<work>']['supersede_note'] 로 옮기고, 없는 회차는 아무 말도 "
                   "하지 않게 한다. G-A035/37/38/39 에는 같은 문장을 그대로 실어 발행 바이트를 유지한다.",
        resolution="2026-09-20 원천에서 고쳤다(runner_note = camp.get('supersede_note', '')). G-A041 은 "
                   "one_command_v3 로 다시 냈고 v1·v2 바이트는 history 에 보존한다(서버에 올린 적 없음). "
                   "관문 tools/test_go2_g_a041_campaign_contract.py test_2 — 안내문에 '옛 판정 규칙'·"
                   "'러너 결함'이 없고, 넷은 여전히 supersede_note 를 가진다.",
    ),
    dict(
        id="C-2", found_on="2026-09-20", found_by="기획자/직접확인", confidence="확인",
        severity="중대", status="OPEN",
        repro="import sys,json,zipfile;sys.path.insert(0,'tools');"
              "sys.path.insert(0,'workspace/training/quadruped');"
              "import build_go2_a033_reward_package as r, build_go2_training_length_package as l;"
              "pick=lambda w:(l,json.loads(l.SPECS[w].read_text(encoding='utf-8'))) if w=='G-A035' "
              "else (r,r.load(w));"
              "zipped=lambda m,s:json.loads(zipfile.ZipFile(m.output_path(s)).read("
              "[x for x in zipfile.ZipFile(m.output_path(s)).namelist() "
              "if x.endswith('experiment.json')][0]).decode('utf-8'));"
              "rebuilt=lambda m,s:json.loads(m.build_payload(s)['experiment.json'].decode('utf-8'));"
              "bad=[w for w in ('G-A035','G-A037','G-A038','G-A039') "
              "if zipped(*pick(w))!=rebuilt(*pick(w))];print('diverged',','.join(bad))",
        repro_expect="diverged G-A035,G-A037,G-A039",
        where="upload/G-A035|G-A037|G-A039 의 발행 ZIP 안 experiment.json vs config/experiments/*.json",
        what="발행된 arm ZIP 세 개가 현재 사양에서 다시 빌드한 것과 다르다 — 사양을 발행 뒤에 고치고 "
             "ZIP 을 그대로 뒀기 때문이다. G-A035 는 **판정이 바뀌었다**(추론 사슬 상태 INFORMATION_RUN "
             "-> HOLD_UNSUPPORTED, 2026-09-20). G-A037·G-A039 는 `inference.rows`(와 G-A037 의 "
             "`contradicting`)가 바뀌었다 — 2026-09-20 의 CSV 셀 결합 작업으로 근거 행에 selector·cells "
             "가 붙었다. 값은 같지만 발행물은 옛 행을 싣고 있다. 그래서 회차 ZIP 을 다시 만드는 코드가 "
             "전부 'differs from a rebuild' 로 멈춘다: tools.test_go2_fact_rules_contract test_6, "
             "tools.test_go2_g_a041_campaign_contract test_12. G-A038 은 실행된 회차이고 어긋나지 않는다. "
             "**사양과 발행물이 서로 다른 말을 하는 동안에는, 사양을 읽는 사람과 ZIP 을 받는 서버가 다른 "
             "회차를 본다.**",
        source_checked="세 ZIP 안의 experiment.json 을 파싱해 현재 사양과 키 단위로 대조했다(위 repro). "
                       "2026-09-20 의 생성기 변경(탐침 -0.04 추가)은 이 파일들에 들어가지 않으므로 원인이 "
                       "아니다 — G-A038 이 같은 조건에서 어긋나지 않는 것이 그 대조군이다.",
        origin_fix="사용자 결정이 필요하다. (가) 셋을 각각 다음 판으로 다시 내고 옛 바이트는 history 에 "
                   "보존한다 — 사양과 발행물이 같은 말을 하게 된다(셋 다 비실행·서버에 올린 적 없음). "
                   "(나) 사양 변경을 되돌린다. 어긋남을 잡는 관문은 이미 있다(test_6). 고친 뒤에는 "
                   "tools/test_go2_g_a041_campaign_contract.py 의 KNOWN_DIVERGED 를 줄여야 통과한다 — "
                   "래칫이라 조용히 되살아나지 않는다.",
        resolution="",
    ),
    dict(
        id="C-3", found_on="2026-09-20", found_by="기획자/직접확인", confidence="확인",
        severity="경미", status="OPEN",
        repro="t=open('workspace/training/quadruped/upload/G-A041/current/CURRENT_UPLOAD.txt',"
              "encoding='utf-8').read();seg=t.split('가장 최근 ')[1].split(')')[0];"
              "print('names_as_latest',seg)",
        repro_expect="names_as_latest 20260920_a033_ang_vel_xy_m004_staged_v3",
        where="tools/build_go2_training_length_campaign.py publish() 의 `earlier[-1]`",
        what="'가장 최근' 판을 폴더 이름의 사전순 마지막으로 고른다. G-A041 의 history 에는 "
             "one_command_v1·v2 와 staged_v2 가 있고, 사전순으로는 staged_v2 가 마지막이라 실제로 가장 "
             "나중에 만든 one_command_v2 가 아니라 arm 판이 '가장 최근'으로 적힌다. 수치 판단에는 쓰이지 "
             "않지만 안내문이 사실과 다르다.",
        source_checked="upload/G-A041/history/ 의 폴더 3개와 각 폴더의 mtime.",
        origin_fix="이름 정렬 대신 폴더 mtime 또는 release_id 의 날짜·판 번호로 고른다. 이미 발행된 "
                   "넷의 안내문 바이트가 바뀌지 않는지 확인하고 고친다(바뀌면 그 회차도 판을 올려야 한다).",
        resolution="",
    ),
    dict(
        id="C-4", found_on="2026-09-21", found_by="기획자/직접확인", confidence="확인",
        severity="경미", status="FIXED",
        repro="import sys,zipfile;sys.path.insert(0,'tools');"
              "sys.path.insert(0,'workspace/training/quadruped');"
              "import build_go2_training_length_campaign as b, build_go2_training_length_package as l;"
              "z=zipfile.ZipFile('workspace/training/quadruped/upload/G-A041/current/"
              "GO2_G_A041_a033_ang_vel_xy_m004_one_command.zip');"
              "t=z.read('go2_campaign_g_a041/README.txt').decode('utf-8');"
              "s=b.arm_builder('G-A042').load('G-A042');"
              "print('released_says_9',('the 9 target cases' in t),"
              "'measured',len(l.targets(s))+len(s['preregistered'].get('required_target_cases') or []),"
              "'scored',len(l.targets(s)))",
        repro_expect="released_says_9 True measured 20 scored 12",
        where="tools/build_go2_training_length_campaign.py 의 README·안내문 서식 4곳",
        what="발행문과 안내문의 표적 case 수가 상수 `9` 로 박혀 있었다. G-A041 은 표적 묶음이 "
             "3+6+3=12 인데 발행된 README·안내문이 '9 target cases'·'표적 9 case' 라고 적은 채 "
             "서버에서 실행됐다. 같은 파일의 `chain_status_line` 이 이미 배운 교훈과 같은 자리다 — "
             "회차마다 갱신을 기억해야 하는 수는 반드시 어긋난다.",
        source_checked="발행된 G-A041 ZIP 안 README.txt 와 현재 사양의 target_groups(3+6+3). "
                       "G-A035·G-A037·G-A038·G-A039 는 실제로 9 라 문장이 맞았고, 그래서 이 오류는 "
                       "표적을 넓힌 회차에서 처음 드러났다.",
        origin_fix="수를 사양에서 센다(`target_case_count`·`scored_case_count`). 이미 실행된 G-A041 "
                   "발행물의 바이트는 불변이므로 그 판이 적은 수만 `FROZEN_TARGET_COUNT` 에 남기고, "
                   "그 상수가 이 대장을 가리킨다.",
        resolution="2026-09-21 고침. `tools/build_go2_training_length_campaign.py` 의 네 서식이 "
                   "`target_case_count(camp, spec)`(1단계가 재는 수)와 `scored_case_count(camp, spec)`"
                   "(게이트가 채점하는 수)를 쓴다. 이전 다섯 회차의 발행 바이트가 그대로인 것은 "
                   "`tools/test_go2_g_a042_campaign_contract.py` 의 이전 발행물 검사와 "
                   "`tools/test_go2_g_a041_campaign_contract.py::test_12` 가 지킨다.",
    ),
    dict(
        id="C-5", found_on="2026-09-21", found_by="기획자/직접확인", confidence="확인",
        severity="중대", status="FIXED",
        repro="import sys;sys.path.insert(0,'tools');"
              "sys.path.insert(0,'workspace/training/quadruped');"
              "from pathlib import Path;"
              "import build_go2_a033_reward_package as r;"
              "gone=not Path('workspace/_keep/go2_g_a041_a033_ang_vel_xy_m004/evaluation/candidate/"
              "cases/seed_101/stairs_15_down/summary.json').is_file();"
              "print('a041_15cm_missing',gone,'a042_measures_in_stage1',"
              "len([e for e in r.targets(r.load('G-A042')) if 'stairs_15' in e]))",
        repro_expect="a041_15cm_missing True a042_measures_in_stage1 3",
        where="config/experiments/G_A041_a033_ang_vel_xy_m004.json preregistered.required_records "
              "vs 러너의 단계 구분",
        what="사양이 '필수 기록'이라고 적은 자료가 **성능 판정 뒤에** 놓여 있었다. G-A041 의 15cm 계단 "
             "telemetry·등반수·전진거리는 required_records 인데 2단계(전수)에서만 측정되고, 1단계가 "
             "FAIL 이라 2단계가 돌지 않아 통째로 사라졌다(회수 완결 PARTIAL, "
             "reports/GO2_G_A041_READOUT.md). 다운로드 손상이 아니라 사양과 실행 경로의 불일치다 — "
             "필수 자료를 조건부 단계에 두면 실패한 회차일수록 자료가 없다.",
        source_checked="회수된 _keep/go2_g_a041_a033_ang_vel_xy_m004 의 case 목록(15cm 3 seed 없음)과 "
                       "같은 사양의 preregistered.required_records·stages 블록.",
        origin_fix="필수 기록을 1단계에서 재게 한다. 사양에 `preregistered.required_target_cases` 를 "
                   "두고 러너의 TARGET_CASES 에 넣되 게이트 묶음에는 넣지 않는다 — 측정은 무조건, "
                   "채점은 안 한다. 15cm 를 묶음으로 만들 수는 없다: 표본이 적어 하한이 발화 불가다(S-2).",
        resolution="2026-09-21 고침. `tools/build_go2_a033_reward_package.py` 의 `targets()` 가 "
                   "required_target_cases 를 1단계 목록에 더하고, 같은 파일의 validate_spec 이 그 "
                   "목록을 검사한다. 첫 사용자는 G-A042(15cm 3 seed)이고, 관문은 "
                   "`tools/test_go2_g_a042_campaign_contract.py` 다. 키가 없는 사양의 동작은 그대로라 "
                   "기존 발행물은 바이트가 바뀌지 않는다.",
    ),
    dict(
        id="C-6", found_on="2026-09-21", found_by="기획자/직접확인", confidence="확인",
        severity="중대", status="FIXED",
        # FIXED 결함의 재현은 **고침이 아직 자리에 있는지**를 본다: 전체 계약을 돌린 뒤에도
        # 발행 ZIP 의 바이트가 그대로여야 한다.
        repro="import subprocess,sys,hashlib,pathlib;"
              "z=pathlib.Path('workspace/training/quadruped/go2_feet_air_time_020_v2.zip');"
              "before=hashlib.sha256(z.read_bytes()).hexdigest();"
              "r=subprocess.run([sys.executable,'-B','-m','unittest',"
              "'tools.test_go2_feet_air_time_020_contract'],capture_output=True);"
              "after=hashlib.sha256(z.read_bytes()).hexdigest();"
              "print('tests_ok',r.returncode==0,'published_untouched',before==after)",
        repro_expect="tests_ok True published_untouched True",
        where="tools/test_go2_feet_air_time_020_contract.py::test_built_package_manifest_and_structure "
              "-> tools/build_go2_feet_air_time_020_package.py build()",
        what="계약 테스트가 **발행된 회차 ZIP 을 그 자리에서 다시 만들었다**. `builder.build()` 가 "
             "`OUTPUT`(발행 경로)에 쓰고 `.sha256` 도 함께 고치므로, 테스트를 한 번 돌릴 때마다 "
             "발행물이 조용히 바뀌고 옆의 체크섬이 그것을 따라갔다. 이것이 X-1 의 원인이었다.",
        source_checked="2026-09-21 재확인. 현재 테스트는 `patch.object(builder,'OUTPUT',<임시경로>)` 로 "
                       "빌드를 임시 디렉터리에 보내고 발행 파일의 sha 가 그대로인지 검사한다"
                       "(같은 파일 103-112행). 실제로 모듈을 돌려도 "
                       "workspace/training/quadruped/go2_feet_air_time_020_v2.zip 은 HEAD 와 같고 "
                       "git status 가 깨끗하다.",
        origin_fix="테스트가 발행 경로에 쓰지 않게 한다 — 빌드는 임시 경로로 보내고 발행물은 읽기만 한다.",
        resolution="2026-09-21 고침(원천). `tools/test_go2_feet_air_time_020_contract.py` 가 "
                   "`builder.OUTPUT` 을 임시 경로로 바꿔 빌드하고, 빌드 뒤 발행 ZIP 의 sha 가 "
                   "변하지 않았음을 단언한다. 위 재현이 그 고침의 회귀 관문이다. "
                   "**남은 것은 C-9 로 분리한다** — 쓰기는 멎었지만 발행본과 현재 원본의 차이를 "
                   "아무도 검사하지 않는다.",
    ),
    dict(
        id="C-9", found_on="2026-09-21", found_by="검토/직접확인", confidence="확인",
        severity="경미", status="OPEN",
        repro="import importlib.util,sys,zipfile,tempfile,pathlib,hashlib;"
              "from unittest.mock import patch;"
              "s=importlib.util.spec_from_file_location('b','tools/build_go2_feet_air_time_020_package.py');"
              "b=importlib.util.module_from_spec(s);sys.modules['b']=b;s.loader.exec_module(b);"
              "d=tempfile.mkdtemp();out=pathlib.Path(d)/'rebuild.zip';"
              "patch.object(b,'OUTPUT',out).__enter__();b.build();"
              "h=lambda z,n:hashlib.sha256(z.read(n)).hexdigest();"
              "A=zipfile.ZipFile(b.OUTPUT if False else "
              "'workspace/training/quadruped/go2_feet_air_time_020_v2.zip');B=zipfile.ZipFile(out);"
              "na={i.filename:h(A,i.filename) for i in A.infolist() if not i.is_dir()};"
              "nb={i.filename:h(B,i.filename) for i in B.infolist() if not i.is_dir()};"
              "diff=[k for k in set(na)|set(nb) if na.get(k)!=nb.get(k)];A.close();B.close();"
              "print('differing',len(diff),'prd_changed',any('SCREENING_PRD' in k for k in diff))",
        repro_expect="differing 2 prd_changed True",
        where="tools/test_go2_feet_air_time_020_contract.py 103-118행 — 임시 빌드의 구조만 보고 "
              "발행 ZIP 의 member 와 대조하지 않는다.",
        what="C-6 의 고침은 **쓰기를 멈췄을 뿐** 차이를 드러내지는 않는다. 발행된 "
             "`go2_feet_air_time_020_v2.zip` 은 옛 PRD 를 싣고 현재 작업본에서 다시 만들면 "
             "member 95개 중 2개(`GO2_FEET_AIR_TIME_020_SCREENING_PRD.md` 와 그것을 담은 "
             "`PACKAGE_SHA256SUMS.txt`)가 다른데, 이제 그 사실을 보는 관문이 없다. "
             "C-2(발행 ZIP ↔ 현재 사양 불일치)와 같은 모양이고, 조용한 쪽이 더 나쁘다 — "
             "다음 감사자는 '테스트가 통과하니 발행본이 최신'이라고 읽는다.",
        source_checked="발행 ZIP 과 임시 경로 재빌드의 member 를 이름·sha 로 전수 대조(95 대 95, "
                       "다른 것 2개). git status 의 `M workspace/training/quadruped/upload/plan/"
                       "GO2_FEET_AIR_TIME_020_SCREENING_PRD.md` 가 그 차이의 출처다.",
        origin_fix="G-A041·G-A042 계약처럼 `build_payload()` 를 **발행된 ZIP 의 member 와 대조**하는 "
                   "검사를 같은 테스트에 더한다. 그러면 위 2개 차이가 실패로 드러나고 그 다음은 "
                   "사용자 결정이다 — (가) 그 회차를 다음 판으로 다시 내거나 (나) PRD 변경을 되돌린다.",
        resolution="",
    ),
    dict(
        id="C-7", found_on="2026-09-21", found_by="검토/직접확인", confidence="확인",
        severity="경미", status="OPEN",
        repro="import zipfile,re;"
              "z=zipfile.ZipFile('workspace/training/quadruped/upload/G-A042/current/"
              "GO2_G_A042_a033_track_lin_vel_xy_160_one_command.zip');"
              "r=z.read('go2_campaign_g_a042/server_run_go2_campaign.sh').decode('utf-8');"
              "d=z.read('go2_campaign_g_a042/README.txt').decode('utf-8');"
              "print('runner_says',re.search(r'the (\\d+) target cases',r).group(1),"
              "'readme_says',re.search(r'the (\\d+) target cases',d).group(1),"
              "'old_baseline_mentions',r.count('A017'))",
        repro_expect="runner_says 9 readme_says 20 old_baseline_mentions 5",
        where="workspace/training/quadruped/server_run_go2_campaign.sh 8행·13행(주석)과 "
              "266·269·273행(실행 중 찍히는 log 문구). 발행본은 G-A042 v4 ZIP 안의 같은 파일.",
        what="C-4 가 고친 것은 README·안내문 서식 4곳이고 **러너 본문은 남았다**. 발행된 v4 의 "
             "러너가 아직 'the 9 target cases' 라고 적고(같은 ZIP 의 README 는 20 으로 맞다), "
             "REMEASURE_BASELINE 분기의 log 3줄이 기준선을 'A017' 이라고 부른다 — 이 회차의 "
             "기준선은 `BASELINE_LABEL=g_a033` 이다. 동작은 config 에서 읽으므로 바뀌지 않지만, "
             "재측정 분기가 돌면 CAMPAIGN_LOG.txt 에 틀린 기준선 이름이 남는다. 회차마다 사람이 "
             "기억해야 하는 수·이름은 반드시 어긋난다는 C-4 의 교훈이 같은 파일에서 반복됐다.",
        source_checked="발행된 v4 ZIP(sha a95d3b6d…6133) 안의 server_run_go2_campaign.sh 와 "
                       "README.txt, 그리고 arm ZIP 의 run_config.env(BASELINE_LABEL=g_a033, "
                       "TARGET_CASES 20개).",
        origin_fix="러너의 주석·log 를 사양·config 에서 세게 한다 — 수는 이미 있는 "
                   "target_case_count/scored_case_count 를, 기준선 이름은 $BASELINE_LABEL 을 쓴다. "
                   "발행된 v4 의 바이트는 불변이므로 다음 판에서 고치고, 이 회차를 v4 로 실행하면 "
                   "log 의 'A017' 은 이 대장을 가리키는 표기 오류로 읽는다.",
        resolution="",
    ),
    dict(
        id="C-8", found_on="2026-09-21", found_by="검토/직접확인", confidence="확인",
        severity="경미", status="FIXED",
        repro="import sys;"
              "sys.path.insert(0,'tools');"
              "import build_go2_a033_reward_package as r;"
              "from go2_tuning_config import reward_dict;"
              "n=r.build_payload(r.load('G-A043'));"
              "o=r.build_payload(r.load('G-A042'));"
              "f=lambda p,k:reward_dict(p[k].decode('utf-8'))['track_lin_vel_xy_exp'];"
              "print('fixed_arm_baseline',f(n,'baseline/quadruped_rewards.py'),"
              "'fixed_arm_reference',f(n,'reference/baseline_quadruped_rewards.py'),"
              "'released_arm_baseline',f(o,'baseline/quadruped_rewards.py'))",
        repro_expect="fixed_arm_baseline 1.5 fixed_arm_reference 1.5 released_arm_baseline 1.2",
        where="tools/build_go2_a033_reward_package.py build_payload() 의 "
              "`for role in ('candidate','baseline')` 복사 — baseline/quadruped_rewards.py 가 "
              "작업본 파일을 그대로 싣는다.",
        what="회차 ZIP 의 `baseline/quadruped_rewards.py` 가 기준선 G-A033 의 값(1.5)이 아니라 "
             "**작업본의 현재 값(1.2)** 을 싣는다. 학습에는 쓰이지 않는다 — 기준선은 SHA 로 고정된 "
             "model_best.pt·env.yaml 로 재생만 하고 다시 학습하지 않으므로 단일변수는 깨지지 않는다"
             "(대조는 reference/baseline_quadruped_rewards.py 1.5 ↔ candidate 1.6 한 줄뿐). "
             "그러나 패키지를 열어 두 파일을 비교하는 사람에게는 **없는 두 번째 차이**가 보인다.",
        source_checked="v4 ZIP 안 arm ZIP 의 baseline/quadruped_rewards.py(1.2)·"
                       "baseline/exported/env.yaml(weight 1.5)·reference/baseline_quadruped_rewards.py"
                       "(1.5), 그리고 baseline 을 재학습하지 않고 SHA 고정 정책을 재생하는 "
                       "server_run_go2_candidate_iter_pinned.sh 159-160·743-744행.",
        origin_fix="baseline/ 에도 렌더된 reference 를 싣는다(같은 바이트). 발행된 arm 의 바이트를 "
                   "지켜야 하므로 사양이 켜는 방식으로 넣는다 — 키가 없는 사양은 예전과 똑같이 "
                   "만들어진다. 관문은 회차 계약 테스트에 baseline 파일의 다이얼 값이 "
                   "expected_rewards.baseline 과 같은지 보는 검사를 더한다.",
        resolution="2026-09-22 G-A043 v2 에서 원천 수정: tools/build_go2_a033_reward_package.py "
                   "build_payload() 가 `output.baseline_reward_file == 'rendered_reference'` 인 "
                   "사양에 렌더된 기준선 파일을 싣는다. G-A043 사양이 그 키를 갖고, 발행된 "
                   "G-A035~G-A042 는 키가 없어 바이트가 그대로다(결함 C-2 를 키우지 않는다). "
                   "관문은 tools/test_go2_g_a043_campaign_contract.py "
                   "test_20_the_shipped_baseline_reward_file_is_the_baseline 이고, 이 행의 repro 가 "
                   "고침과 '발행판 불변'을 함께 지킨다. 근거 "
                   "reports/GO2_G_A043_CRITERIA_CHANGES_20260922.md 8절.",
    ),
    dict(
        id="C-10", found_on="2026-09-22", found_by="기획자/관문실행", confidence="확인",
        severity="경미", status="FIXED",
        repro="import json,re;"
              "from pathlib import Path;"
              "q=Path('workspace/training/quadruped');"
              "src=json.load(open(q/'config/experiments/G_A040_a033_flat_orientation_m05.json',"
              "encoding='utf-8'))['value_derivation']['source'];"
              "refs=re.findall(r'[A-Za-z0-9_][A-Za-z0-9_./-]*\\.csv',src);"
              "bare=[r for r in refs if '/' not in r];"
              "print('bare',len(bare),'worst_duplicate_count',"
              "max(len(list(q.rglob(r))) for r in bare))",
        repro_expect="bare 3 worst_duplicate_count 1",
        where="workspace/training/quadruped/config/experiments/"
              "G_A040_a033_flat_orientation_m05.json 의 value_derivation.source.",
        what="G-A040 사양이 근거 CSV 를 맨 이름(`FALL_CHANNEL_ROLLUP.csv`)으로 적었는데, "
             "2026-09-21 에 `reports/evidence/go2_a041_20260921/FALL_CHANNEL_ROLLUP.csv` 가 "
             "생기면서 같은 이름이 2개가 됐다. 그 순간부터 분석가는 사양이 가리키는 파일을 "
             "특정할 수 없고, `tools/test_go2_detectability_gate.py` "
             "test_14_every_path_in_a_spec_can_be_opened 가 실패한 채로 남아 있었다. "
             "G-A040 은 미실행·발행 ZIP 없음이라 패키지 바이트는 영향이 없다.",
        source_checked="같은 이름 2개(go2_a038_reread_20260919/ 와 go2_a041_20260921/), "
                       "G-A040 사양의 source 필드, test_14 의 판정 규칙(경로에 '/' 가 있으면 "
                       "이름 대체를 허용하지 않고, 없으면 저장소에서 유일해야 한다), "
                       "그리고 upload/ 에 G-A040 디렉터리가 없다는 사실.",
        origin_fix="사양의 두 rollup 참조를 저장소 기준 전체 경로로 적는다. 관문은 이미 있다 — "
                   "test_14 가 맨 이름의 중복을 잡는다. 회귀는 이 행의 repro 가 지킨다.",
        resolution="2026-09-22 G-A043 작업 중 원천(G-A040 사양)에서 고쳤다: "
                   "`reports/evidence/go2_a038_reread_20260919/FALL_CHANNEL_ROLLUP.csv and "
                   "reports/evidence/go2_a038_reread_20260919/ROUGH_LATERAL_ROLLUP.csv`. "
                   "test_14 가 다시 통과한다. 남은 맨 이름 3개(TILT.csv·SITUATIONS.csv·"
                   "PROBE_SITUATIONS.csv)는 저장소에서 유일하므로 규칙 안이다.",
    ),
    dict(
        id="C-11", found_on="2026-09-22", found_by="회수분석/직접확인", confidence="확인",
        severity="경미", status="FIXED",
        repro="import io,sys,unittest;"
              "sys.path.insert(0,'tools');"
              "import test_go2_detectability_gate as gate;"
              "n=sum(len(v) for v in gate.STAGE1_BLIND_SPOTS.values());"
              "gate.STAGE1_BLIND_SPOTS={};"
              "res=unittest.TextTestRunner(verbosity=0,stream=io.StringIO()).run("
              "unittest.TestLoader().loadTestsFromName("
              "'InferenceChainGateTest.test_17_a_risk_axis_is_visible_in_stage_1',gate));"
              "print('waived',n,'fires',len(res.failures),'errors',len(res.errors))",
        repro_expect="waived 2 fires 2 errors 0",
        where="workspace/training/quadruped/config/experiments/"
              "G_A043_a033_lin_vel_z_m15.json 의 preregistered.required_target_cases 와 "
              "그것으로 만들어지는 1단계 목록(verify_go2_basic_motion_harvest.target_stage_entries).",
        what="G-A043 의 1단계는 23 case 를 재고 TARGET_PASS 를 냈지만, 회차를 실제로 떨어뜨린 "
             "case 3개(G2 combined_yaw_right 의 seed 101·202·303)는 그 23개 안에 **하나도 "
             "없었다**. 1단계 목록은 G2 에서 lateral 인 `left`·`right` 만 골랐고 복합 회전은 "
             "넣지 않았다. 그래서 서버 게이트는 전수 단계를 예약했고, 결정적 손실은 69 case 를 "
             "다 돌린 뒤에야 보였다. 판정 규칙 자체는 멀쩡했다 — G2 는 flat 이라 "
             "max_flat_case_survival_drop(0.0625) 이 이미 모든 G2 case 에 걸려 있었고 실제로 "
             "3행을 잡았다. 빠진 것은 **규칙이 아니라 1단계가 그 case 를 보게 하는 일**이다. "
             "게이트 스스로는 '전수 단계를 예약할 뿐 판정은 로컬 검증기가 한다'고 적고 있으므로"
             "(CAMPAIGN_STATUS.txt 의 GATE_ROLE) 잘못된 최종 판정이 나온 적은 없다. 대가는 "
             "조기중단의 방향이 한쪽으로만 선다는 것 — 계단 실패는 1단계에서 멎지만 보호 파괴는 "
             "멎지 않는다.",
        verbatim="",
        source_checked="G-A043 사양의 required_target_cases 10개와 catastrophe_case, "
                       "target_stage_entries 가 만드는 23개 목록, "
                       "workspace/server_returns/G-A043_LOCAL_VERIFY.json 의 "
                       "criteria.1_target_basic_motion=true 와 non_inferiority_violations 4행, "
                       "그리고 verify_go2_basic_motion_harvest.judge 의 flat case 생존 규칙.",
        origin_fix="1단계 비용절감을 쓰는 회차라면, 보호 대상 시나리오의 **가장 약한 case** 가 "
                   "1단계 목록에 들어가야 한다 — G-A043 기준선에서 G2 의 최약 case 는 "
                   "combined_yaw_right 였고(기준선 tracking 0.8774~0.8939 로 G2 최저), "
                   "그 사실은 저장된 A033 69 case 에서 회차 **전에** 읽을 수 있었다. "
                   "다음 회차 계획(upload/plan/GO2_POST_A043_PLAN_20260922.md 5절)은 이번 회차에 "
                   "1단계 분기를 쓰지 않고 전수 69 를 필수로 걷는 쪽을 택했다. 그러나 그것은 "
                   "이번 한 회차에만 듣는 처방이므로, 1단계 분기를 다시 쓰는 회차를 위해 "
                   "판정을 사람의 주의력에서 파일로 옮긴다.",
        resolution="2026-09-22 원천에서 고쳤다. `tools/go2_stage1_blind_spot.py` 가 저장된 "
                   "기준선 69 case 에서 위험 축별 최약 case 를 0.1 초에 읽고, "
                   "`tools/test_go2_detectability_gate.py` "
                   "test_17_a_risk_axis_is_visible_in_stage_1 이 1단계 분기를 쓰는 **새** 사양에 "
                   "그 case 가 들어 있기를 요구한다. 침투 시험: 면제 목록을 비우면 관문이 실제로 "
                   "발화한다(이 행의 repro). 이미 실행된 G-A042·G-A043 두 사양은 발행본 불변 "
                   "원칙에 따라 고치지 않고 `STAGE1_BLIND_SPOTS` 에 이름으로 남겼다 — 두 회차는 "
                   "지금도 그 자리를 못 본다. 관문의 한계는 도구 docstring 과 test_17 에 적었다: "
                   "최약 case 는 '가장 먼저 무너질 자리'의 대용이지 증명이 아니다.",
    ),
    dict(
        id="C-12", found_on="2026-09-22", found_by="패키지제작/직접확인", confidence="확인",
        severity="중대", status="OPEN",
        repro="import sys;sys.path.insert(0,'tools');"
              "import go2_tuning_base_data as b;"
              "names={r['name'] for r in b.weights()};"
              "print('lin_vel_z',b.walking_values('lin_vel_z_l2'),"
              "'status',b.range_status('lin_vel_z_l2',-1.75),"
              "'missing',sorted({'A038','A041','A042'}-names))",
        repro_expect="lin_vel_z [-2.0, -1.5] status BETWEEN_OBSERVED missing ['A038', 'A041', 'A042']",
        where="tools/go2_stairs_behavior.py 의 WEIGHT_RUNS 와 그것으로 만들어지는 "
              "reports/evidence/go2_stairs_behavior_20260916/WEIGHT_OUTCOME.csv, "
              "그리고 그 표를 읽는 go2_tuning_base_data.walking_values/range_status.",
        what="회수된 회차가 기반 데이터의 가중치 표에 들어가지 않아, **이미 관측된 값이 "
             "`OUT_OF_RANGE` 로 계산됐다**. 표는 2026-09-16 의 G-A033 에서 멈춰 있었고 그 뒤 "
             "A038·A041·A042·A043 네 회차가 실행·회수됐다. A043 은 `lin_vel_z_l2 = -1.5` 에서 "
             "실제로 걷는 정책을 만들어 69 case 를 남겼는데, 생성 표는 이 다이얼의 걷는 관측값을 "
             "`-2.0` 하나로 셌다. 그래서 다음 회차의 어떤 값도 `OUT_OF_RANGE` 로 찍히고, 사양은 "
             "없는 `out_of_range_reason` 을 적게 된다. 규칙은 있었다 — "
             "`workspace/training/quadruped/AGENTS.md` §4-9 가 '새 학습 회수 후에는 "
             "go2_stairs_behavior.py -> go2_tuning_base_data.py 순서로 재생성한다' 고 적는다. "
             "**규칙이 있었는데 네 회차 연속 실행되지 않았다**: 재생성을 강제하는 관문이 "
             "없었기 때문이다(문서 자기일치 검사는 통과한다 — 낡은 CSV 로 만든 낡은 문서는 "
             "자기 자신과 일치한다).",
        verbatim="",
        source_checked="WEIGHT_OUTCOME.csv 의 회차 목록(A043 이전 18행), "
                       "go2_stairs_behavior.WEIGHT_RUNS 의 마지막 항목이 G-A033 이라는 것, "
                       "_keep 에 A038·A041·A042·A043 수확물이 모두 있다는 것, "
                       "그리고 A043 의 rough_forward 속도 0.419 >= 0.2(걷기 경계).",
        origin_fix="생성기 입력 표에 회수된 회차를 넣고 증거 CSV·문서를 재생성한다. 재생성을 "
                   "기억에 맡기지 않으려면 '회수된 회차가 표에 있는가' 를 세는 관문이 필요하다 — "
                   "그 관문은 아직 없다(아래 남은 일).",
        resolution="2026-09-22 A043 을 넣고 전체를 재생성했다. `walking_values(lin_vel_z_l2)` 가 "
                   "`[-2.0, -1.5]` 가 되고 `-1.75` 가 `BETWEEN_OBSERVED` 로 바뀌어 G-A044 사양이 "
                   "사실대로 적을 수 있게 됐다. 딸려 나온 셋도 원천에서 고쳤다: (1) 특이점 S1 "
                   "('걷는 회차는 전부 lin_vel_z -2 다')이 A043 으로 반증돼 생성 문장이 반례를 "
                   "세도록 바뀌었고, (2) track 선·feet_air 선이 '한 항만 다른 회차' 로 좁혀졌으며 "
                   "(예전 필터는 다른 항이 다른 회차를 같은 선에 섞었다), (3) 1단계만 잰 회차의 "
                   "빈 칸이 예외를 던지던 것을 '미측정' 으로 다루게 했다. "
                   "**아직 OPEN 인 이유**: A038·A041·A042 는 여전히 표 밖이다 — 세 회차 모두 "
                   "1단계만 재서 이 표의 칸(rough_forward 속도·경사 전진·15cm 오르기) 중 일부가 "
                   "미측정이고, 빈 칸 표기를 정하기 전에 넣으면 기울기 판독이 조용히 망가진다. "
                   "재생성을 강제하는 관문도 아직 없다.",
    ),
    dict(
        id="C-13", found_on="2026-09-22", found_by="패키지제작/직접확인", confidence="확인",
        severity="경미", status="FIXED",
        repro="import sys;sys.path.insert(0,'tools');"
              "sys.path.insert(0,'workspace/training/quadruped');"
              "import build_go2_a033_reward_package as r, build_go2_training_length_package as l;"
              "s=r.load('G-A044');ok=len(l.reuse_problems(s));"
              "saved=dict(l.CASE_PLAY_ENV);l.CASE_PLAY_ENV.clear();"
              "bad=len(l.reuse_problems(s));l.CASE_PLAY_ENV.update(saved);"
              "print('fixed',ok,'broken',bad)",
        repro_expect="fixed 0 broken 2",
        where="tools/build_go2_training_length_package.py 의 video_fingerprint — 러너 "
              "server_run_go2_candidate_iter_pinned.sh 의 run_video 가 만드는 지문과 같아야 한다.",
        what="기준선 영상을 재사용할 때 빌더는 그 파일이 **정말 그 조건의 그 정책인지** 를 지문 "
             "재계산으로 확인한다. 러너의 지문에는 `DR_MODE`·`PUSH_X`·`PUSH_Y` 가 들어가는데 "
             "빌더는 그 세 칸을 `\"0\", \"\", \"\"` 로 박아 두고 있었다. 지금까지 재사용한 "
             "영상이 전부 밀침도 DR 도 아니어서 드러나지 않았고, G-A044 가 A043 이 찍은 밀침 "
             "±x 기준선 영상을 재사용하려 하자 지문이 어긋났다. **fail-closed 라 잘못된 파일을 "
             "받아들인 적은 없다 — 맞는 파일을 거부하고 있었다.** 그래서 과거 회차의 판정과 "
             "발행물에는 영향이 없고, 비용은 '재사용할 수 있는 영상을 다시 찍는 것' 이었다.",
        verbatim="",
        source_checked="러너 run_video 의 vfingerprint 인자 10개, set_case 의 밀침 4행과 "
                       "dr_seed_* 분기, A043 이 남긴 두 밀침 기준선 영상의 "
                       ".identity.sha256 파일 값, 그리고 같은 값을 손으로 재계산한 결과.",
        origin_fix="러너 set_case 와 같은 표를 빌더에 두고, 둘이 어긋나면 잡히도록 관문을 만든다. "
                   "지문 자체는 fail-closed 이므로 넓히는 방향의 수정이다.",
        resolution="2026-09-22 원천에서 고쳤다. `CASE_PLAY_ENV`·`play_env()` 가 밀침 네 방향과 "
                   "DR case 를 모형화하고, `tools/test_go2_video_fingerprint_contract.py` 가 그 표를 "
                   "러너 원문에서 다시 읽어 대조한다. 침투 시험: 표를 비우면 재사용이 실제로 "
                   "거부된다(이 행의 repro). 발행된 회차의 ZIP 바이트는 변하지 않는다 — G-A043 "
                   "재빌드가 바이트로 같음을 확인했다.",
    ),
    dict(
        id="C-14", found_on="2026-09-22", found_by="사용자검토/독립검토+직접확인", confidence="확인",
        severity="중대", status="FIXED",
        repro="import re,zipfile,pathlib;"
              "cur=sorted(pathlib.Path('workspace/training/quadruped/upload/G-A044/current')"
              ".glob('*.zip'))[0];"
              "zf=zipfile.ZipFile(cur);"
              "shipped={n.rsplit('/',1)[-1] for n in zf.namelist()};"
              "hist=open('workspace/training/quadruped/runner_history/"
              "server_run_go2_candidate_iter_pinned.6fd78eeb8eac5342.sh',encoding='utf-8').read();"
              "now=zf.read('go2_g_a044/server_run_go2_candidate_iter_pinned.sh').decode('utf-8');"
              "g=lambda t:re.search(r'bash (\\S+) --inner',t).group(1);"
              "print('v3',g(hist),g(hist) in shipped,'| v4',g(now))",
        repro_expect="v3 server_run_go2_candidate_staged.sh False | v4 %q",
        where="server_run_go2_candidate_iter_pinned.sh 의 바깥 launcher — tmux 로 자기 자신을 "
              "--inner 로 다시 부르는 한 줄.",
        what="러너는 자기 자신을 다시 부를 때 파일 이름을 **글자로 박아** 두고 있었다: "
             "`bash server_run_go2_candidate_staged.sh --inner`. 그것은 이 러너가 복사되어 나온 "
             "조상 파일의 이름이고, 패키지에는 그런 파일이 없다. G-A031 이후 모든 회차는 "
             "campaign wrapper(`server_run_go2_campaign.sh`)가 진입점이었고 wrapper 는 팔 러너를 "
             "직접 `--inner` 로 불렀으므로 **이 줄은 한 번도 실행된 적이 없었다.** G-A044 는 "
             "campaign wrapper 를 없애고 팔 러너를 진입점으로 삼은 첫 회차라 이 줄이 유일한 경로가 "
             "된다. 결과: 바깥 스크립트는 `[STARTED]` 를 찍고 **exit 0** 으로 끝나는데 tmux 세션은 "
             "`No such file or directory`(rc 127)로 즉시 죽는다. 학습도 평가도 영상도 시작되지 "
             "않고, 사용자는 성공 표시를 본 채 빈 서버를 기다리게 된다.",
        verbatim="bash: server_run_go2_candidate_staged.sh: No such file or directory (rc 127)",
        source_checked="G-A031·A032·A033·A035·A037·A038·A039·A041·A042·A043 발행 ZIP 안의 .sh 목록"
                       "(전부 server_run_go2_campaign.sh 가 진입점), campaign wrapper 의 L39 이름 "
                       "해석과 L224 `bash \"$ARM_RUNNER\" --inner`, 그리고 v3 패키지를 풀어 그 이름을 "
                       "실제로 실행한 결과.",
        origin_fix="이름을 글자로 적지 말고 `${BASH_SOURCE[0]}` 로 자기 경로를 풀어 재진입한다. "
                   "그리고 '러너가 재진입하는 경로가 패키지 안에 실제로 있는가'를 관문이 "
                   "**실행해서** 확인하게 한다 — 읽어서가 아니라.",
        resolution="2026-09-22 원천에서 고쳤다. 러너에 `SELF` 를 두고 `printf %q` 로 그 경로를 넘기며, "
                   "넘기기 전에 `[[ -f \"$SELF\" ]]` 로 막는다. 관문은 "
                   "test_go2_g_a044_package_contract.PackageTest.test_13 이고, 그 시험은 패키지를 "
                   "풀어 러너의 launcher 블록을 **가짜 tmux 와 함께 실제로 돌린 뒤** 넘어간 경로가 "
                   "파일인지 본다. G-A044 v4 로 재발행했다. 발행된 이전 회차는 바이트가 변하지 "
                   "않는다 — 실행된 러너를 쓰는 G-A042·G-A043 을 runner_history 에 고정했고 "
                   "(6fd78eeb8eac5342) test_11 이 그것을 지킨다.",
    ),
    dict(
        id="C-15", found_on="2026-09-22", found_by="사용자검토", confidence="확인",
        severity="중대", status="FIXED",
        repro="import subprocess,sys;from pathlib import Path;"
              "v3=Path('workspace/training/quadruped/upload/G-A044/history/"
              "20260922_a033_lin_vel_z_m175_full69_v3/GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt')"
              ".read_text(encoding='utf-8');"
              "cmd=[l.strip() for l in v3.splitlines() if 'verify_go2_basic_motion_harvest' in l][0]"
              ".split()[1:];"
              "r=subprocess.run([sys.executable,*cmd],capture_output=True,text=True);"
              "print('v3_rc',r.returncode,'usage_error',"
              "'the following arguments are required' in r.stderr)",
        repro_expect="v3_rc 2 usage_error True",
        where="tools/build_go2_full_collection_release.py 의 run_guide — 회수 뒤 로컬 판독 두 줄.",
        what="안내문이 `--keep` 을 쓰라고 적었는데 `verify_go2_basic_motion_harvest.py` 에 그런 "
             "선택지는 없다(`--harvest` 가 필수다). 시키는 대로 치면 argparse 가 **exit 2** 로 "
             "죽는다. 하필 그 명령을 치는 순간이 서버가 아직 돌면서 예산을 쓰고 있고 끌지 말지를 "
             "정하는 자리다. 같은 오타가 G-A043 안내문 L78 에도 있었지만 그 회차는 바로 위 L75 에 "
             "옳은 `--harvest` 줄이 함께 있어서 드러나지 않았다 — G-A044 에는 틀린 줄만 남았다.",
        verbatim="verify_go2_basic_motion_harvest.py: error: the following arguments are required: "
                 "--harvest",
        source_checked="verify_go2_basic_motion_harvest.py 의 argparse 정의 4줄, go2_screening_gate.py "
                       "의 argparse 정의, G-A043 안내문 L75·L78, 그리고 v3 안내문의 그 줄을 그대로 "
                       "실행한 결과.",
        origin_fix="안내문의 명령을 **읽어서** 검사하지 말고 **돌려서** 검사한다. 없는 선택지는 "
                   "exit 2 로 나타나므로 관문이 그것을 잡을 수 있다.",
        resolution="2026-09-22 생성기에서 고쳤다. 두 줄이 `--harvest` · `--out` · `--candidate` · "
                   "`--rule-version` 을 쓴다. 관문은 test_14 이고, 발행된 안내문에서 "
                   "`python -B tools/` 로 시작하는 줄을 모두 뽑아 실제로 실행한 뒤 exit 2 와 "
                   "argparse 오류 문구를 금지한다. G-A044 v4 로 재발행했다. G-A043 은 발행본이라 "
                   "고치지 않는다 — 그 회차는 옳은 줄이 함께 있다.",
    ),
    dict(
        id="C-16", found_on="2026-09-22", found_by="사용자검토", confidence="확인",
        severity="중대", status="FIXED",
        repro="from pathlib import Path;"
              "b='workspace/training/quadruped/upload/G-A044/';"
              "old=Path(b+'history/20260922_a033_lin_vel_z_m175_full69_v3/"
              "GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt').read_text(encoding='utf-8');"
              "new=Path(b+'current/GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt')"
              ".read_text(encoding='utf-8');"
              "need=('REPORT_ACQUIRED','telemetry','영상','하나라도 비면 종료 불가');"
              "seg=lambda t,h:t.split(h)[1].split('6. 이 패키지')[0];"
              "f=lambda s:sum(k in s for k in need);"
              "print('v3',f(seg(old,'5. 서버 종료 조건')),'v4',f(seg(new,'5. SERVER SHUTDOWN GATE')))",
        repro_expect="v3 0 v4 4",
        where="같은 생성기의 5절 — 서버를 꺼도 되는지 정하는 자리.",
        what="5절이 `결과 ZIP 과 .sha256 을 내려받고 SHA 가 맞는지 확인한 뒤에 끈다` 한 줄이었다. "
             "SHA 는 **파일이 깨지지 않았다**는 증거일 뿐 회수가 끝났다는 증거가 아니다. 루트 "
             "AGENTS.md 「학습 종료 후 영상 증거 게이트」 §5·§7 은 종료 판정에 영상 판정·생성·"
             "다운로드·로컬 검증·미측정 목록을 각각 요구하고, §4 에 흩어져 있던 report 조건도 "
             "'회수 완결' 이라는 다른 말로 적혀 있어서 5절만 읽으면 건너뛸 수 있었다. 서버는 "
             "휘발성이라 이 순서를 틀리면 영상과 report 가 **영구 소실**된다 — G-A028·G-A029 가 "
             "그렇게 만들어진 공백이다. A043 안내문에는 있던 `SERVER SHUTDOWN GATE` 절이 이 "
             "생성기에는 옮겨지지 않았다.",
        verbatim="결과 ZIP 과 .sha256 을 로컬로 내려받고 SHA 가 맞는지 확인한 **뒤에** 끈다.",
        source_checked="루트 AGENTS.md 「학습 종료 후 영상 증거 게이트」 §5·§7 과 「서버 제한시간 "
                       "우선 보고 규칙」 §3, G-A043 안내문의 SERVER SHUTDOWN GATE 절, v3 안내문 5절 전문.",
        origin_fix="종료 조건을 문장이 아니라 **항목 목록**으로 적고, 그 목록이 안내문에 실제로 "
                   "있는지 관문이 본다. 규칙을 문서에 적는 것만으로는 준수가 아니다.",
        resolution="2026-09-22 생성기에서 고쳤다. 5절이 `SERVER SHUTDOWN GATE — SHA 일치만으로 끄지 "
                   "않는다` 로 바뀌고 a~e 다섯 줄(ZIP·report·telemetry·영상·로컬 판독)과 "
                   "`하나라도 비면 종료 불가` 를 싣는다. 관문은 test_15 다. G-A044 v4 로 재발행했다. "
                   "**이 절은 종료 판정을 대신하지 않는다 — 서버 실행과 종료는 사용자 결정이다.**",
    ),
    dict(
        id="C-17", found_on="2026-09-22", found_by="C-14 수정 뒤 회귀 점검", confidence="확인",
        severity="경미", status="FIXED",
        # 2026-09-24 FIXED: 옛 재현은 `screening_identities({})` 가 None 을 낸다는 **함수의
        # 성질**을 물었다 — 그건 fail-closed 설계 그대로라 고쳐도 계속 재현된다.  FIXED 결함의
        # 재현은 **고침이 자리에 있음**을 보여야 하므로, 합성 수확물을 만드는 하네스들이 이제
        # 후보 신원의 `env_sha256` 을 쓰는지 묻는다.
        repro="import pathlib;"
              "ps=['tools/test_go2_basic_motion_package_contract.py',"
              "'tools/test_go2_campaign_contract.py'];"
              "print(all('env_sha256' in pathlib.Path(x).read_text(encoding='utf-8')"
              " for x in ps))",
        repro_expect="True",
        where="tools/verify_go2_basic_motion_harvest.py 의 screening_identities/apply_plan_screening — "
              "plan screening 이 켜진 사양에서 판정을 합치는 자리.",
        what="plan screening 이 켜지면 검증기는 `facts` 에서 후보의 model/env SHA 를 꺼내 신원으로 "
             "넘긴다. 그 칸이 없으면 신원이 `None` 이 되고 screening 은 INCONCLUSIVE 를 내며, "
             "합쳐진 판정이 **결정적 FAIL 을 INCONCLUSIVE 로 덮는다.** 방향은 fail-closed 라 "
             "성공을 주장하는 쪽으로는 틀리지 않는다 — 비용은 판정을 잃는 것이다. 현재 계약 "
             "테스트 6건이 이것 때문에 빨갛다: "
             "test_go2_basic_motion_package_contract.TargetStageHarvestTest.test_target_stage_readings, "
             "test_go2_basic_motion_pair_contract.GateParityTest 3건, "
             "test_go2_campaign_contract.GateParityTest 2건. 여섯 다 합성 수확물을 "
             "만드는 오래된 하네스가 `candidate_env_sha256` 을 쓰지 않아서다. "
             "(2026-09-24 정정: 초판은 4건으로 셌다 — 뒤의 2건은 C-23 의 source_checked 에만 "
             "귀속돼 있어 이 칸만 읽으면 원인 없는 실패로 보였다. 지문은 같다: 합쳐진 판정이 "
             "`TARGET_PASS_FULL_STAGE_REQUIRED`·`FAIL` 자리에서 INCONCLUSIVE 로 덮인다.)",
        verbatim="AssertionError: 'INCONCLUSIVE' != 'FAIL' : ['candidate_identity_env_sha256=None']",
        source_checked="verify_go2_basic_motion_harvest.py L116~147(screening_identities 와 "
                       "apply_plan_screening), 그리고 네 실패를 **C-14 수정 전 러너 바이트로 "
                       "되돌려 다시 돌린 결과** — 똑같이 실패했다. 즉 C-14 수정과 무관한 기존 상태다.",
        origin_fix="합성 수확물 하네스가 러너와 같은 신원 칸을 쓰게 하거나, 신원 결손을 "
                   "screening 안에서 INCONCLUSIVE 로 흡수하지 말고 artifact_faults 로 올려 "
                   "'무엇이 없어서 판정을 못 했는지'가 판정문에 남게 한다.",
        resolution="2026-09-24 원인은 판독기가 아니라 **합성 수확물을 만드는 하네스**였다. "
                   "`test_go2_basic_motion_package_contract.copy_arm` 이 identity.json 에 "
                   "`env_sha256` 을 쓰도록 고쳤고(그 하네스를 basic_motion_package 1건과 "
                   "basic_motion_pair 3건이 공유한다), `test_go2_campaign_contract` 의 "
                   "GateParityTest 는 make_harvest 뒤에 env.yaml 을 덮어쓰므로 덮어쓴 파일로 "
                   "후보 신원을 다시 찍게 했다. 단정은 하나도 바꾸지 않았다 — 자료만 채웠다. "
                   "여섯 건 모두 개별 실행으로 통과했다(검사당 139~152MB). 판독기의 fail-closed "
                   "동작 자체는 의도한 것이라 그대로 둔다. 같은 뿌리의 형제가 C-31 이고, "
                   "이것을 걷어내자 그 아래에서 C-33 이 드러났다.",
    ),
    dict(
        id="C-18", found_on="2026-09-22", found_by="사용자검토", confidence="확인",
        severity="중대", status="FIXED",
        repro="import json,pathlib;"
              "b=pathlib.Path('workspace/training/quadruped/upload/G-A044');"
              "dup=[q for q in b.glob('history/*/*.zip') if q.name=="
              "'GO2_G_A044_a033_lin_vel_z_m175_full69.zip'];"
              "out=json.loads(pathlib.Path('workspace/training/quadruped/config/experiments/"
              "G_A044_a033_lin_vel_z_m175.json').read_text(encoding='utf-8'))['output'];"
              "v=out['release_id'].rsplit('_',1)[-1];"
              "now=[q.name for q in (b/'current').glob('*.zip')];"
              "print('one_name',len(dup),'now_named',now[0].endswith('_'+v+'.zip'))",
        repro_expect="one_name 4 now_named True",
        where="사양의 output.upload_zip — 사용자가 서버에 올리는 파일의 이름.",
        what="발행 판은 `release_id` 에 `_v<N>` 으로 남는데 **ZIP 이름에는 판이 없었다.** A031~A044 "
             "열두 회차 전부 그랬다. 그래서 A044 는 `history` 에 **똑같은 이름의 ZIP 이 넷** 쌓였고, "
             "그중 v3 는 올리면 아무것도 돌지 않는 판이다(C-14). 책상 위에 같은 이름의 파일 넷이 "
             "있고 하나는 110분을 버리게 하는데, 어느 것인지 가리는 근거가 **사람이 손으로 하는 "
             "SHA 대조 한 줄**뿐이었다. 손대조는 건너뛸 수 있고, 건너뛴 것은 티가 나지 않는다.",
        verbatim="GO2_G_A044_a033_lin_vel_z_m175_full69.zip  x 4 (v1 v2 v3 v4)",
        source_checked="열두 사양의 release_id 와 upload_zip 대조(전부 판 번호 없음), A044 history 의 "
                       "ZIP 넷, 그리고 v3 가 실제로 죽는 것을 확인한 C-14 의 재현.",
        origin_fix="이름이 판을 말하게 한다. 사양 검증이 `upload_zip` 의 끝과 `release_id` 의 "
                   "`_v<N>` 이 같은지 보고, 다르면 **빌드를 거부**한다. 손대조에 기대지 않는다.",
        resolution="2026-09-22 사양 검증에서 고쳤다 — "
                   "build_go2_candidate_package.check_release_version_in_zip_name 을 "
                   "build_go2_training_length_package.validate_spec 이 부르므로 "
                   "**앞으로 나올 모든 회차**에 적용된다. 이 규칙 이전 발행본 11개는 "
                   "LEGACY_UNVERSIONED_ZIPS 에 얼려 두었고(발행물은 바이트도 이름도 고치지 않는다) "
                   "새 사양은 규칙을 지켜야 하므로 그 집합은 자라지 않는다. 관문은 "
                   "test_go2_g_a044_package_contract.PackageTest.test_16 이고 발행된 이름·안내문·"
                   "manifest 가 같은 판을 가리키는지 본다. G-A044 는 v5 로 재발행했다 — v4 와 "
                   "페이로드 차이는 experiment.json 두 줄(이름·판)뿐이다.",
    ),
    dict(
        id="C-19", found_on="2026-09-22", found_by="사용자질문(계획서를 따랐는가)", confidence="확인",
        severity="경미", status="FIXED",
        repro="import re,pathlib;"
              "g='workspace/training/quadruped/upload/G-A044/';"
              "plan=pathlib.Path('workspace/training/quadruped/upload/plan/"
              "GO2_POST_A043_PLAN_20260922.md').read_text(encoding='utf-8');"
              "b=re.search(r'(\\d{2,3})~(\\d{2,3})분 세션 계획치',plan);"
              "old=pathlib.Path(g+'history/20260922_a033_lin_vel_z_m175_full69_v5/"
              "GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt').read_text(encoding='utf-8');"
              "new=pathlib.Path(g+'current/GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt')"
              ".read_text(encoding='utf-8');"
              "k='%s~%s분'%b.groups();"
              "print('plan',k,'v5',k in old,'v6',k in new)",
        repro_expect="plan 120~150분 v5 False v6 True",
        where="tools/build_go2_full_collection_release.py 의 run_guide, 그리고 사양의 비교 대상 기록.",
        what="계획서가 약속한 것 중 **셋이 산출물로 옮겨지지 않았다.** ① 계획 §7 은 회수 여유를 "
             "포함해 `120~150분 세션 계획치` 를 잡으라고 적는데 안내문은 서버가 도는 `110분` 만 "
             "적었다 — 사용자가 읽는 것은 안내문이므로 실행 시간으로 TTL 을 잡게 되고, 회수 "
             "도중에 끊기면 잃는 것은 영상과 report 다. ② 사양은 G-A043 을 63번 인용하면서 그 "
             "정책의 model/env SHA 를 한 번도 고정하지 않았다 — 판독 때 '어느 A043 인가' 를 "
             "사양 안에서 확인할 수 없었다. ③ 계획 §9-1 의 c3 상한 `0.567/70` 이 서술로만 있어 "
             "읽는 사람이 `0.054 x 10.5` 를 다시 계산해야 했다. **판정 문턱은 셋 다 건드리지 "
             "않는다** — 기록과 전달의 공백이다.",
        verbatim="110분 안팎으로 본다. (안내문 v5 — 계획 §7 의 120~150분 세션 계획치 없음)",
        source_checked="계획서 §1·§5·§6·§7·§9 전문과 사양의 기계 대조 — 값·기준선·학습·평가·전수 69·"
                       "sentinel 5·영상 10/4/6·사전등록 숫자 19개가 모두 일치했고(숫자 차이 0) "
                       "어긋난 것이 이 셋이었다. G-A043 의 SHA 는 계획 산문이 아니라 회수 산출물 "
                       "workspace/server_returns/G-A043_LOCAL_VERIFY.json 에서 읽었다.",
        origin_fix="계획서와 산출물의 대조를 사람 눈에 맡기지 않는다. 관문이 **계획서를 열어** 그 "
                   "숫자를 읽고 안내문에 있는지 본다 — 시험 안에 숫자를 다시 적으면 둘이 함께 틀린다.",
        resolution="2026-09-22 생성기와 사양에서 고쳤다. 안내문이 계획서의 세션 계획치를 싣고, "
                   "사양에 `comparison_arm`(G-A043 의 model/env SHA, 출처 명시)이 생겼으며, c3 "
                   "상한이 숫자로 적힌다. 관문 셋: test_19 는 **계획서에서 정규식으로 읽은** 세션 "
                   "계획치가 안내문에 있는지, test_18 은 사양이 고정한 G-A043 SHA 가 회수 산출물과 "
                   "같은지, test_17 은 사전등록 **숫자 전부**를 열거 없이 A043 과 대조한다 — "
                   "기존 test_9 는 대조할 키를 손으로 적어 두어 목록 밖의 문턱을 놓칠 수 있었다. "
                   "G-A044 는 v6 으로 재발행했다.",
    ),
    dict(
        id="C-20", found_on="2026-09-23", found_by="사용자검토(안내문 exit code 설명)", confidence="확인",
        severity="중대", status="FIXED",
        repro="import sys,pathlib;sys.path.insert(0,'tools');"
              "import verify_go2_basic_motion_harvest as v;"
              "g='workspace/training/quadruped/upload/G-A044/';"
              "r=lambda p:pathlib.Path(g+p+'/GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt')"
              ".read_text(encoding='utf-8');"
              "k='BASELINE_REMEASURE_REQUIRED';"
              "print('fail_exits_0',('FAIL' in v.PASS_VERDICTS),"
              "'v6',(k in r('history/20260922_a033_lin_vel_z_m175_full69_v6')),"
              "'v7',(k in r('current')))",
        repro_expect="fail_exits_0 True v6 False v7 True",
        where="tools/build_go2_full_collection_release.py 의 run_guide — 안내문 §5(SERVER SHUTDOWN "
              "GATE)의 마지막 줄.",
        what="안내문이 **exit code 를 성능 판정으로 읽으라고 가르쳤다.** 옛 문장은 "
             "`두 명령의 exit 1 은 검사기 오류가 아니라 성능 기준 미충족이다` 인데 두 번 틀렸다. "
             "① 첫 명령(verify_go2_basic_motion_harvest)은 성능 FAIL 에 exit **0** 을 낸다 — "
             "`PASS_VERDICTS` 에 FAIL 이 들어 있고, 그 뜻은 '판정을 했다' 다. 그 명령의 exit 1 은 "
             "INCONCLUSIVE 나 BASELINE_REMEASURE_REQUIRED, 곧 **판정 불가**다. ② 둘째 명령"
             "(go2_screening_gate)은 INTERNAL_GATE_PASS 에만 exit 0 이라 FAIL 과 INCONCLUSIVE 가 "
             "같은 exit 1 에 섞인다. 이 줄이 놓인 자리가 **서버 종료 게이트**라는 점이 대가를 "
             "정한다 — 결측·identity 불일치로 판정을 못 한 상태를 '성능이 나빴다' 로 읽으면 "
             "회수를 더 하지 않고 서버를 끄고, 그 결손은 휘발 서버가 꺼지는 순간 영구가 된다. "
             "잃는 것은 영상과 report 다.",
        verbatim="두 명령의 exit 1 은 검사기 오류가 아니라 성능 기준 미충족이다.",
        source_checked="tools/verify_go2_basic_motion_harvest.py L51(PASS_VERDICTS = FAIL · "
                       "TARGET_PASS_FULL_STAGE_REQUIRED · QUANT_SUCCESS_VIDEO_REVIEW_PENDING)와 "
                       "L482(return 0 if verdict in PASS_VERDICTS else 1), "
                       "tools/go2_screening_gate.py L68 과 그 main 의 "
                       "`return 0 if report['verdict'] == PASS else 1`. 두 판독기를 빈 수확물로 "
                       "실제 실행해 확인했다 — 각각 VERDICT INCONCLUSIVE · SCREENING "
                       "INTERNAL_GATE_INCONCLUSIVE 로 exit 1 이었고 성능은 아예 읽히지 않았다.",
        origin_fix="안내문이 판독기의 계약을 산문으로 옮겨 적는 한 둘은 따로 늙는다. 관문이 "
                   "판독기를 **실행**해 exit 1 이 성능이 아님을 보이고, 판독기 소스에서 비통과 "
                   "판정 이름을 읽어 안내문이 그것을 담는지 본다 — 시험이 이름을 다시 적지 않는다.",
        resolution="2026-09-23 생성기에서 고치고 v7 로 재발행했다. 새 문장은 exit code 만으로 "
                   "성능도 종료 여부도 판단하지 말라고 적고, 첫 명령의 성능 FAIL=exit 0 · "
                   "exit 1=판정 불가(볼 곳은 artifact_faults·ruler_mismatches)와 둘째 명령의 "
                   "FAIL·INCONCLUSIVE 동일 exit 1 을 구분해 적는다. 관문은 "
                   "test_go2_g_a044_package_contract.PackageTest.test_20 이고, 옛 문장으로 "
                   "되돌리면 `BASELINE_REMEASURE_REQUIRED 가 안내문에 없다` 로 깨지는 것을 "
                   "확인했다. 값·문턱·러너 바이트는 v6 과 같다.",
    ),
    dict(
        id="C-21", found_on="2026-09-23", found_by="사용자검토(ZIP 내부 사양의 판독 명령)", confidence="확인",
        severity="중대", status="FIXED",
        repro="import json,zipfile,pathlib;"
              "g='workspace/training/quadruped/upload/G-A044/';"
              "t=lambda p:zipfile.ZipFile(p).read('go2_g_a044/experiment.json').decode('utf-8');"
              "old=t(g+'history/20260922_a033_lin_vel_z_m175_full69_v7/"
              "GO2_G_A044_a033_lin_vel_z_m175_full69_v7.zip');"
              "new=t(sorted(pathlib.Path(g+'current').glob('*.zip'))[0]);"
              "print('v7',('--keep' in old),'v8',('--keep' in new))",
        repro_expect="v7 True v8 False",
        where="workspace/training/quadruped/config/experiments/G_A044_a033_lin_vel_z_m175.json 의 "
              "campaign_text.readout_ko — ZIP 안 experiment.json 으로 실려 서버로 간다.",
        what="**C-15 를 반쪽만 고쳤다.** 회수 명령의 `--keep` 은 검증기에 없는 선택지이고 치면 "
             "argparse 가 exit 2 를 낸다. v4 에서 안내문을 고쳤지만 **같은 명령이 사양에도 있었고 "
             "사양은 패키지 안에 실려 서버로 간다.** 서버에서 손에 잡히는 것은 ZIP 이므로, "
             "안내문을 잃어버린 사람은 사양의 틀린 줄을 친다. v7 발행본으로 실제 확인했다: "
             "사양이 싣고 간 판독 명령 둘 중 하나가 exit 2 였다.",
        verbatim="verify_go2_basic_motion_harvest.py: error: the following arguments are required: --harvest",
        source_checked="v7 ZIP 의 go2_g_a044/experiment.json 에서 `python -B tools/` 로 시작하는 줄을 "
                       "뽑아 실제 실행 — go2_stall_diagnostics 는 통과, verify 는 exit 2. "
                       "저장소의 다른 사양도 훑었다: G-A043 사양에도 같은 줄이 있으나 그 회차는 "
                       "이미 발행·실행됐고 발행물의 바이트는 고치지 않는다(재빌드 일치 관문 test_11).",
        origin_fix="관문이 **발행된 ZIP 안의 사양**에서도 명령을 뽑아 실행하게 한다. 한 자리에서만 "
                   "고치고 끝내지 않으려면, 같은 문자열이 몇 군데서 서버로 가는지를 관문이 세게 한다.",
        resolution="2026-09-23 사양의 readout 을 `--harvest` 로 고치고 v8 로 재발행했다. 관문 "
                   "test_go2_g_a044_package_contract.PackageTest.test_14 는 이제 안내문과 발행된 "
                   "ZIP 안의 사양 **양쪽**에서 명령을 뽑아 전부 실행하고 exit 2 와 argparse 오류 "
                   "문구를 금지한다. v7 바이트에 그대로 적용해 실패하는 것을 확인했다.",
    ),
    dict(
        id="C-22", found_on="2026-09-23", found_by="사용자검토(독립 코드 검토 회신)", confidence="확인",
        severity="중대", status="FIXED",
        repro="import zipfile,pathlib;"
              "g='workspace/training/quadruped/upload/G-A044/';"
              "r=lambda p:zipfile.ZipFile(p).read("
              "'go2_g_a044/server_run_go2_candidate_iter_pinned.sh').decode('utf-8');"
              "old=r(g+'history/20260922_a033_lin_vel_z_m175_full69_v7/"
              "GO2_G_A044_a033_lin_vel_z_m175_full69_v7.zip');"
              "new=r(sorted(pathlib.Path(g+'current').glob('*.zip'))[0]);"
              "print('v7',old.count('COLLECTION'),'v8',new.count('COLLECTION'),"
              "'marker',old.count('DONE_MARKER'),new.count('DONE_MARKER'))",
        repro_expect="v7 6 v8 16 marker 3 3",
        where="러너 `finish()` — 그리고 그것을 부르는 두 자리: 정상 종료(PHASE 6)와 파국 게이트의 "
              "조기 종료(`finish \"$DECISION\" NOT_MEASURED`).",
        what="**수집이 중단된 실행이 전수 완료와 똑같이 보였다.** `finish` 는 어느 경로로 불리든 "
             "`package_result FULL` 을 부르고 같은 `[DONE]` 표식을 찍었다. 파국 게이트가 아무것도 "
             "재지 못하고 멈춘 실행(조기 종료)도 `RESULT_STATE=FULL` + `[DONE]` 을 냈다는 뜻이다. "
             "**자료가 실제로 빠졌다는 말이 아니라, 빠지는 실패 경로의 상태 표시가 틀렸다는 말이다** "
             "— 그리고 그 표시를 읽고 서버를 끄면 결손은 영구가 된다(휘발 서버). 정상 경로만 "
             "시험하는 관문으로는 보이지 않는다.",
        verbatim="package_result FULL   # finish() — 조기 종료 경로에서도 같은 줄",
        source_checked="러너 :495~520(finish), :689(조기 종료의 finish 호출), :124(package_result), "
                       ":211(on_exit 의 PARTIAL). run_full_suite 는 69 미만이면 이미 exit 6 으로 "
                       "죽어 PARTIAL 로 포장되므로, 남은 구멍은 조기 종료 경로였다.",
        origin_fix="`회수 준비`와 `전수 완료`를 한 신호에 싣지 않는다. 표식은 회수 준비를 뜻하게 "
                   "두고(사용자는 그것을 기다린다), 수집 상태는 **디스크의 개수에서** 따로 적는다.",
        resolution="2026-09-23 러너가 case·sentinel·영상 개수를 세어 `COLLECTION_STATUS` 를 "
                   "RUNNER_STATUS.txt·RESULT_STATUS.txt 에 적고(FULL_69_COMPLETE / "
                   "TARGET_STAGE_COMPLETE_NOT_FULL_69 / INCOMPLETE_EARLY_STOP / INCOMPLETE_COLLECTION / "
                   "INCOMPLETE_CRASH), 결손이면 `[INCOMPLETE COLLECTION]` 두 줄을 찍는다. `[DONE]` 은 "
                   "그대로 나온다 — 회수 준비 신호이기 때문이다. 안내문 §4·§5 가 그 구분을 싣고 "
                   "종료 게이트가 `COLLECTION_STATUS=FULL_69_COMPLETE` 를 요구한다. 관문 test_21 은 "
                   "발행된 러너의 finish 를 **실행**해 세 경우(조기 종료·전수 완료·69 중 68)를 "
                   "가른다. 두 러너 파일(pinned·staged)에 같은 수정을 넣어 "
                   "test_go2_campaign_contract 의 동치 관계를 지켰다. G-A044 는 v8 로 재발행했다.",
    ),
    dict(
        id="C-23", found_on="2026-09-23", found_by="C-22 수정 뒤 회귀 점검", confidence="확인",
        severity="경미", status="FIXED",
        repro="import pathlib;"
              "t=pathlib.Path('tools/test_go2_campaign_contract.py').read_text(encoding='utf-8');"
              "g=pathlib.Path('workspace/training/quadruped');"
              "p=(g/'server_run_go2_candidate_iter_pinned.sh').read_text(encoding='utf-8');"
              "s=(g/'server_run_go2_candidate_staged.sh').read_text(encoding='utf-8');"
              "print('equality_gate','test_runner_is_the_staged_runner_plus_the_pin_blocks' in t,"
              "'named_divergence','differ_only_where_a_named_contract' in t,"
              "'reentry_executed','test_each_runner_re_enters_its_own_file' in t,"
              "'pinned_self','bash %q --inner' in p,"
              "'staged_name','bash server_run_go2_candidate_staged.sh --inner' in s)",
        repro_expect="equality_gate False named_divergence True reentry_executed True "
                     "pinned_self True staged_name True",
        where="tools/test_go2_campaign_contract.py CheckpointPinTest "
              "(옛 test_runner_is_the_staged_runner_plus_the_pin_blocks).",
        what="러너 머리글과 이 관문은 **`pinned = staged + CHECKPOINT PIN 블록`** 이라는 관계를 "
             "주장했다. 2026-09-22 의 C-14 수정이 그 관계를 깼다 — 재진입을 파일 이름 대신 경로로 "
             "바꾼 `SELF=` 줄과 `COLLECT_REQUIRED_ON_STATIONARY` 옵트인이 **pinned 에만** 들어갔다. "
             "staged 러너는 자기 이름으로 재진입하므로 C-14 가 애초에 해당하지 않는다. 즉 관계가 "
             "의도적으로 갈라졌는데 **관문이 그 예외를 배우지 못했고**, 그래서 관문은 빨간 채로 "
             "남았다. 빨간 관문은 다음 회귀를 가려 준다 — 오늘 러너를 고칠 때도 이 관문은 이미 "
             "빨갰으므로 '내가 깼는지' 를 색으로는 알 수 없었다(두 파일의 문자열 수를 세어 확인했다). "
             "발행물에는 영향이 없다: A044 가 싣는 것은 pinned 러너이고, 이전 발행본은 "
             "runner_history 로 고정돼 재빌드가 일치한다(test_11 통과).",
        verbatim="FAIL: test_runner_is_the_staged_runner_plus_the_pin_blocks (executed=False)",
        source_checked="working tree 의 두 러너를 관문과 같은 방식으로 벗겨 비교 — 차이 81줄, "
                       "그중 2026-09-23 수정이 넣은 문자열(COLLECTION_STATUS 등)을 담은 줄 0. "
                       "executed=True 짝(발행된 바이트끼리)은 처음부터 통과했다. 같은 모듈의 다른 "
                       "실패 2건(GateParityTest.test_gain_passes_everywhere·"
                       "test_no_change_fails_everywhere)은 C-17 이며 "
                       "`('FAIL','INCONCLUSIVE') != ('FAIL','FAIL')` 로 같은 신원 결손이다.",
        origin_fix="관문에 '의도된 예외' 를 그냥 적지 않는다. C-14 가 staged 에 해당하지 않는 이유를 "
                   "관문이 **실행해서 확인**하게 하고(재진입 대상이 자기 파일인지), 두 러너의 동치 "
                   "주장은 발행된 바이트에만 남긴다. **정정: 이 칸의 초판은 '어느 쪽이든 러너 "
                   "바이트가 바뀌므로 회차와 분리한다' 고 적었는데 틀렸다**(사용자 검토 2026-09-23 "
                   "3회차). 고칠 것은 관문이지 러너가 아니었고, 실제로 러너 바이트를 한 글자도 "
                   "건드리지 않고 닫혔다 — v8 ZIP 이 같은 SHA 로 재빌드된다.",
        resolution="2026-09-23 동치 관문을 넷으로 갈랐다. ① 발행된 바이트(G-A031 staged · G-A033 "
                   "pinned)의 동치는 그대로 지킨다. ② 작업본의 차이는 이름 붙인 계약 두 개"
                   "(C-14 재진입·필수 수집 옵트인)의 것만 허용하고, 계약 없는 차이 — 한쪽 러너에만 "
                   "들어간 편집 — 는 떨어뜨린다. ③ 두 러너 각각이 **자기 파일로** 재진입하는지 스텁 "
                   "tmux 로 실행해 본다. ④ `catastrophe_action` 을 실행해 비유한 학습이 옵트인과 "
                   "무관하게 STOP_UNSAFE 임을 본다. 반증: pinned 에만 한 줄을 넣으면 ② 가 "
                   "'계약이 0 개다' 로 떨어지고, 재진입을 옛 이름으로 되돌리면 ③ 이 떨어진다. "
                   "러너는 그대로이고 v8 ZIP 은 5e93b80a… 로 동일 재빌드된다.",
    ),
    dict(
        id="C-24", found_on="2026-09-23", found_by="사용자검토(실패 경로 안내)", confidence="확인",
        severity="중대", status="FIXED",
        repro="import pathlib,zipfile;"
              "h=pathlib.Path('workspace/training/quadruped/upload/G-A044/history');"
              "r=lambda v:(h/('20260922_a033_lin_vel_z_m175_full69_'+v)/"
              "'GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt').read_text(encoding='utf-8');"
              "z=zipfile.ZipFile(h/'20260922_a033_lin_vel_z_m175_full69_v9'/"
              "'GO2_G_A044_a033_lin_vel_z_m175_full69_v9.zip');"
              "run=z.read('go2_g_a044/server_run_go2_candidate_iter_pinned.sh').decode('utf-8');"
              "on=run[run.index('on_exit() {'):run.index('trap on_exit EXIT')];"
              "print('crash_marker',('DONE_MARKER' in on),"
              "'v8',('늘 나오는 것도 아니다' in r('v8')),'v9',('늘 나오는 것도 아니다' in r('v9')))",
        repro_expect="crash_marker False v8 False v9 True",
        where="tools/build_go2_full_collection_release.py 안내문 §4·§5 (v8 까지).",
        what="C-22 를 고치면서 안내문에 「[DONE] 은 어느 경우에도 나온다」는 뜻으로 적었다. **틀렸다.** "
             "러너의 `on_exit` crash 경로는 부분 ZIP 과 `COLLECTION_STATUS=INCOMPLETE_CRASH` 만 "
             "남기고 표식 없이 끝난다 — 그 줄을 기다리는 사용자는 오지 않을 줄을 기다리며 휘발 "
             "서버의 예산을 태운다. 두 번째로, 불완전 상태를 하나로 묶어 「빠진 것을 메운 뒤 종료」로 "
             "적었다. 복구 가능한 누락과 파국 게이트의 안전 중단은 **대응이 반대다** — 후자는 학습이 "
             "비유한하거나 정책이 실행되지 않은 판이고, 자료를 얻자고 시뮬레이터를 다시 띄우지 않는 "
             "것이 러너의 계약이다(C-14 의 STOP_UNSAFE). 69 를 채우라는 안내는 그 계약과 충돌한다. "
             "C-22 와 같은 결을 가진 결함이다: 상태를 나눠 놓고 **그 상태를 읽는 법을 잘못 적었다.**",
        verbatim="[DONE] 은 결과 ZIP 이 만들어졌다는 뜻뿐이다. 파국 게이트가 아무것도 재지 못하고 "
                 "멈춘 실행도 같은 표식을 찍는다",
        source_checked="러너 `on_exit`(pinned :215–224)에 표식 echo 가 없다 — 발행된 ZIP 안의 바이트에서 "
                       "확인했고, 그 경로를 실행해 stdout 에 표식이 없음을 보았다(test_22). "
                       "`finish` 를 지나는 세 경우는 표식을 찍는다(test_21).",
        origin_fix="실패 경로의 안내는 실패 경로를 **실행해서** 쓴다. 정상 경로만 돌려 보면 표식이 "
                   "늘 나온다고 믿게 된다. 그리고 「불완전」을 한 덩어리로 적지 않는다 — 메울 수 있는 "
                   "결손과 메우면 안 되는 결손은 같은 단어를 쓰면 안 된다.",
        resolution="2026-09-23 안내문 §4 를 세 상태로 나눴다 — ① 정상 완료(표식 있음·"
                   "FULL_69_COMPLETE, 개수 확인일 뿐 SHA·지문·identity·report 검사를 대신하지 않음) "
                   "② 복구 가능한 누락(표식 있음·INCOMPLETE_COLLECTION, 서버를 켠 채로 메움) "
                   "③ crash·안전상 평가 불가(표식 **없음**·INCOMPLETE_CRASH 또는 표식 있음·"
                   "INCOMPLETE_EARLY_STOP, 69 를 채우지 않고 회수 가능한 것을 보존한 뒤 결측을 적음). "
                   "§5-a 와 종료 문장이 그 구분을 따른다. 관문 test_22 가 발행된 러너의 crash 경로를 "
                   "실행해 표식 부재를 보이고 안내문과 대조한다 — v8 안내문은 다섯 검사 중 넷에서 "
                   "떨어진다. G-A044 는 v9 로 재발행했고 러너 바이트는 그대로다.",
    ),
    dict(
        id="C-25", found_on="2026-09-24", found_by="A044 회수 뒤 다음 회차 준비(원장 먼저 규칙 적용)",
        confidence="확인", severity="중대", status="FIXED",
        repro="import csv,pathlib;"
              "runs={r['run'] for r in csv.DictReader(open("
              "'workspace/training/quadruped/reports/runs/LEDGER.csv',encoding='utf-8'))};"
              "keep=[q.name for q in pathlib.Path('workspace/_keep').iterdir() "
              "if (q/'evaluation').is_dir()];"
              "print('missing',len([n for n in keep if n not in runs]),"
              "'a043',('go2_g_a043_a033_lin_vel_z_m15' in runs),"
              "'a044',('go2_g_a044_a033_lin_vel_z_m175' in runs))",
        repro_expect="missing 0 a043 True a044 True",
        where="workspace/training/quadruped/reports/runs/ (생성물), 생성기 tools/build_go2_run_reports.py.",
        what="`GO2_NOW.md` 의 원장 우선 규칙(G-D-LEDGER-FIRST-20260918)은 다음 회차를 "
             "`reports/runs/` 에서 고르라고 정한다. 그런데 그 폴더는 **생성물**이고, 회수 뒤 다시 "
             "만들지 않아도 아무 관문도 붉어지지 않았다. 2026-09-24 A044 회수 시점에 정본 "
             "`LEDGER.csv` 는 seq 26(A038)에서 멈춰 있었고 **A041·A042·A043·A044 네 회차가 통째로 "
             "빠져 있었다** — 그 사이 같은 다이얼(`lin_vel_z_l2`)에서 두 회차가 돌았는데, 회차를 "
             "고르는 규칙이 읽는 표에는 둘 다 없었다. A044 회수 세션이 생성기를 돌리기는 했지만 "
             "출력을 `workspace/server_returns/G-A044/generated_runs/` 안에만 두었다. 즉 "
             "**생성은 했고 정본은 그대로였다.** 이것은 C-12(회수 회차가 기반 데이터 표 밖)와 "
             "같은 결의 결함이며, 그때는 표 하나를 손으로 채워 닫았기 때문에 다시 벌어졌다.",
        verbatim="회차·곡선·수치는 `reports/runs/`(INDEX·`TERRAIN_AT_PIN.csv`·LEDGER·"
                 "SCENARIO_SCORES·ARM_DELTAS)와 `reports/evidence/`에서 읽는다",
        source_checked="디스크의 `LEDGER.csv` 46줄 대 같은 날 생성분 57줄; 빠진 회차 넷의 이름을 "
                       "두 파일의 `run` 열에서 직접 대조했다.",
        origin_fix="원장이 생성물이면 **최신인지 묻지 말고 다시 만들어 대조한다.** 사람이 "
                   "「회수 뒤 생성기를 돌린다」를 기억하는 절차는 네 회차를 놓쳤다.",
        resolution="2026-09-24 생성기를 정본 경로로 다시 돌려 33 회차(A041~A044 포함)로 맞췄고, "
                   "`tools/test_go2_run_ledger_freshness.py` 를 새로 넣었다 — 이 관문은 산출물에서 "
                   "생성기를 한 번 더 돌려 `LEDGER.csv`·`SCENARIO_SCORES.csv`·`ARM_DELTAS.csv`·"
                   "`TERRAIN_AT_PIN.csv`·회차 보고서 전부를 디스크와 바이트 대조한다. 옛 46줄 "
                   "원장으로 되돌려 실패(빠진 회차 여섯을 이름으로 출력)를 확인한 뒤 복구했다. "
                   "같은 날 `reports/evidence/go2_stairs_behavior_20260916/` 도 A044 를 포함해 "
                   "다시 만들었다.",
    ),
    dict(
        id="C-26", found_on="2026-09-24", found_by="사용자검토(두 팔 실험의 해석 규칙)",
        confidence="확인", severity="중대", status="FIXED",
        repro="import json,pathlib;"
              "b=json.loads(pathlib.Path('workspace/training/quadruped/config/experiments/"
              "G_A046_seed43_lin_vel_z_m15.json').read_text(encoding='utf-8'));"
              "f=b['inference']['falsified_if'];"
              "q=pathlib.Path('workspace/training/quadruped/upload/plan/"
              "GO2_A045_SEED_PAIR_PLAN_20260924.md').read_text(encoding='utf-8');"
              "print('paired',('(B - A)' in f),"
              "'no_retire',('does NOT retire the promotion rule' in f),"
              "'cause',('미확정' in q and '다이얼 탓이다' not in q),"
              "'threshold',('2.53' in q and '문턱은 총점 `+2.5`/70' not in q))",
        repro_expect="paired True no_retire True cause True threshold True",
        where="upload/plan/GO2_A045_SEED_PAIR_PLAN_20260924.md 초판 §1·§2·§4-1·§4-2·§5, "
              "그리고 그 문장을 옮긴 두 사양의 `falsified_if`·`promotion_reason`(발행 v2).",
        what="값·문턱·러너·수집 계약은 옳았는데 **그 결과를 읽는 규칙**이 네 곳에서 과했다. "
             "① 「`D_path` 가 작으면 A044 의 비단조는 다이얼 탓」 — `−2.0` 에서 seed 차이가 작아도 "
             "`−1.75` 에서는 클 수 있고 이 회차는 `−1.75` 를 반복하지 않는다. 게다가 보상 효과와 "
             "학습 경로는 배타적이지도 않다(보상이 경로를 바꾸고 그 민감도가 값마다 다를 수 있다). "
             "② 「B 의 15cm ≥2단이 50/96 이상이면 계단 이득 재현」 — **절대값만 보면** A 가 70 인데 "
             "B 가 50 이어도 재현이 된다. 후보의 계단 성능은 오히려 나빠졌는데도. "
             "③ 「차이가 크면 단일 seed 승급 규칙을 폐기하고 기준선 장기 학습으로 전환」 — 한 표본은 "
             "그 결론을 지지하지 않고, 기존 INTERNAL_GATE_FAIL 관측을 무효로 만들지도 않으며, "
             "장기 학습이 흔들림을 줄인다는 증거도 없다. ④ R-6 을 「차단 조건에 걸리지 않는다」로 "
             "**닫힌 것처럼** 적었다 — CLI 인자가 전달된다는 사실은 규정 허용의 증거가 아니고, "
             "반대로 공식 제출 불가라는 단정도 근거가 없다. 곁들여 정본끼리 어긋난 곳도 있었다: "
             "문턱을 계획서는 `2.5`, 기준 문서는 `2.53` 으로 적었고, 「같은 보상으로 두 번 학습한 적 "
             "없다」는 같은 seed 재학습 2건과 충돌했으며(정확한 공백은 **다른 seed 로의 반복** 부재), "
             "`stairs_*_down` 을 이름대로 「하강」이라 적었다(원장은 `climb` 으로 정정해 둔 case 다).",
        verbatim="`D_path` < 1.26443 (평가 흔들림 이하) | 경로 흔들림이 작다 → §1 ②의 비단조는 "
                 "**다이얼 탓**이다(가)",
        source_checked="계획서 초판 §4-1 표와 §4-2 목록, 발행 v2 사양의 falsified_if, "
                       "`SAME_SEED_REPEAT.csv`(identical=True 2건), `STAIRS_CLIMB.csv` 의 "
                       "`direction=climb`, A044 사양의 `min_total_points_delta=2.53`.",
        origin_fix="사전등록은 **값만이 아니라 읽는 법도** 반증 가능해야 한다. 쌍 실험의 재현은 "
                   "절대 수준(행동이 나타났는가)과 쌍 차이(같은 seed 의 B−A)를 **따로** 적는다. "
                   "관측 하나로 규칙을 폐기하거나 기존 관측을 무효로 만드는 분기를 미리 적지 않는다. "
                   "규정 해석은 '확인된 사실' 과 '그 사실이 증명하지 않는 것' 을 갈라 적고, 닫는 "
                   "주체(운영진·공식 근거)를 함께 적는다.",
        resolution="2026-09-24 계획서를 2판으로 다시 쓰고(§4-1 세 줄·§4-2 세 질문·§4-3·§5·§8), "
                   "기준 변경 문서에 §2-5·§2-6 을 넣고, 두 사양의 `falsified_if`·`promotion_reason`·"
                   "`singularity`·`seed_limit` 을 고쳤다. 총점이 어디로 갔는지는 산문 대신 같은 "
                   "채점기의 반사실로 쟀다(`tools/go2_score_decomposition.py` → `SCORE_SPLIT.csv`: "
                   "A044 는 생존 −4.62775 · 추종 +0.99438 · 교차항 −0.00144, 자기 검증으로 세 회차의 "
                   "기록된 총점을 재현). 관문 `tools/test_go2_g_a045_package_contract.py::"
                   "ReviewCorrectionsTest` 7 검사가 네 정정을 고정하고, 둘은 반대로 심어 떨어지는 "
                   "것까지 확인했다. 발행은 팔 v3 · 쌍 v4 로 다시 냈다 — v2 바이트는 고치지 않는다.",
    ),
    dict(
        id="C-27", found_on="2026-09-24", found_by="독립검토(발행 v7 바이트의 중단·재개 경로)",
        confidence="확인", severity="중대", status="FIXED",
        repro="import pathlib;"
              "s=pathlib.Path('workspace/training/quadruped/"
              "server_run_go2_candidate_iter_pinned.sh').read_text(encoding='utf-8');"
              "i=s.index('candidate training artifact already present');"
              "w=s.index('rm -rf -- logs exported',i);"
              "print('guarded',('GO2_RESTART_TRAINING' in s[i:w]),"
              "'preserves',('preserve_interrupted_training' in s[i:w]),"
              "'stops',('exit 9' in s[i:w]))",
        repro_expect="guarded True preserves True stops True",
        where="server_run_go2_candidate_iter_pinned.sh 의 학습 분기 — 재개 조건이 거짓일 때 "
              "들어가는 else 절(발행 v7 기준 624~662행).",
        what="`GO2_RESUME=1` 로 들어왔는데 보존된 학습이 `TRAIN_RC=0` 이 아니면 — 즉 학습이 "
             "**중단된 바로 그 경우** — 러너가 말없이 `$CANDIDATE_ROOT/logs`(그 학습의 checkpoint "
             "전부)와 `exported/` 를 지우고, `$KEEP/training` 의 고정 checkpoint·pin 기록을 지우고, "
             "`tee` 로 `$KEEP/logs/candidate_training.log` 를 비운 뒤 처음부터 재학습했다. "
             "「이어 하기」라고 친 명령이 **증거와 GPU 시간을 함께** 태운다. 정상 경로만 도는 "
             "계약 검사는 이 분기에 한 번도 들어가지 않으므로 12/12 통과와 양립한다.",
        verbatim="else\n  rm -rf -- logs exported",
        source_checked="발행본 `GO2_G_A045_A046_seed43_pair_full69_v7.zip` 안의 팔 러너 바이트를 "
                       "떼어 harness 로 실행 — 중단 학습을 심은 상태에서 `DESTROYED_AND_RETRAINED` "
                       "가 나왔다(역증명).",
        origin_fix="파괴적 기본값은 쓰기 전에 읽는 사람이 막을 수 있어야 한다. 되돌릴 수 없는 "
                   "동작(자료 삭제·재학습)은 **묵시적 경로에 두지 않고** 이름 있는 선택으로 "
                   "분리한다. 그리고 그 분기에 들어가는 검사를 함께 만든다 — 정상 경로만 도는 "
                   "검사는 복구 경로를 한 번도 보지 않는다.",
        resolution="2026-09-24 가드를 넣었다: 재개가 미완료 학습을 만나면 `interrupted_<시각>/` 에 "
                   "로그·고정 checkpoint·학습 로그·exported 를 SHA 와 함께 복사하고 "
                   "`TRAINING_STATE=INTERRUPTED_TRAINING_PRESERVED` 를 적은 뒤 rc 9 로 멈춘다. "
                   "재학습은 `GO2_RESTART_TRAINING=1` 이라는 별도 선택이고, 보존할 것이 없을 때와 "
                   "신규 실행(RESUME=0)은 그대로 진행한다. 관문 "
                   "`tools/test_go2_g_a045_package_contract.py::RecoveryPathTest::test_35` 가 네 "
                   "경우를 **실행해서** 확인하고, test_37 이 안내문·README 에 상태 이름과 스위치가 "
                   "적혔는지 본다. 발행은 팔 v7 · 쌍 v8 — v7 바이트는 고치지 않는다.",
    ),
    dict(
        id="C-28", found_on="2026-09-24", found_by="독립검토(발행 v7 바이트의 완료 판단)",
        confidence="확인", severity="중대", status="FIXED",
        repro="import pathlib;"
              "s=pathlib.Path('workspace/training/quadruped/"
              "server_run_go2_full69_campaign.sh').read_text(encoding='utf-8');"
              "i=s.index('full_complete() {');f=s[i:s.index(chr(10)+'}',i)];"
              "print('collection',('COLLECTION_STATUS' in f),"
              "'zip',('sha256sum -c' in f and '.sha256' in f))",
        repro_expect="collection True zip True",
        where="server_run_go2_full69_campaign.sh 의 `full_complete`(55~58행)와 그것을 부르는 "
              "`arm_phase`(211·219행). 같은 함수가 server_run_go2_campaign.sh 에도 있다.",
        what="완료 판단이 `RUNNER_RC`·`STAGE`·`DECISION` 세 줄만 보았다. 그런데 "
             "`DECISION=SUITE_COMPLETE` 는 **러너가 끝까지 갔다**는 뜻이고, 69 case 가 디스크에 "
             "있다는 뜻은 `COLLECTION_STATUS=FULL_69_COMPLETE` 다. 그래서 수집이 모자란 팔도 "
             "재개 때 「완료」로 건너뛰었다. 게다가 `RUNNER_STATUS.txt` 는 결과 ZIP 을 만들기 "
             "**전에** 쓰이므로, 그 사이에 끊긴 팔은 내려받을 것이 없는데도 건너뛴다.",
        verbatim="[[ \"$(status_of \"$1\" RUNNER_RC)\" == 0 && ... DECISION)\" == SUITE_COMPLETE ]]",
        source_checked="발행 v7 의 캠페인 러너에서 `full_complete` 를 떼어 "
                       "`COLLECTION_STATUS=INCOMPLETE_COLLECTION` 을 물려 실행 → `SKIP`(역증명).",
        origin_fix="「끝까지 돌았다」와 「다 모았다」와 「내려받을 것이 있다」는 서로 다른 질문이다. "
                   "건너뛰기는 셋을 모두 만족할 때만 허용한다 — 건너뛰어서 잃는 것이 "
                   "다시 도는 비용보다 크기 때문이다(휘발 서버에서는 영구 결손이 된다).",
        resolution="2026-09-24 `full_complete` 가 `COLLECTION_STATUS=FULL_69_COMPLETE` 와 결과 "
                   "ZIP·`.sha256` 존재·`sha256sum -c` 통과까지 요구하도록 고쳤고, 두 캠페인 러너에 "
                   "같은 바이트로 넣었다(test_2 가 대조한다). 관문 `RecoveryPathTest::test_36` 이 "
                   "여섯 경우(수집 3종 · ZIP 없음 · ZIP 깨짐 · 정상)를 실행해 확인한다. "
                   "같은 모양이 `server_run_go2_basic_motion_pair.sh`(G-A031+G-A032, 2026-09-15 "
                   "실행 완료)에도 남아 있으나 그 파일은 빌더가 생성하는 발행본이고 재빌드 "
                   "대조 대상이라 고치지 않았다 — 그 회차는 이미 끝났고 재개 경로가 다시 "
                   "돌 일이 없다. 새 회차가 그 러너를 다시 쓰면 같은 수정을 함께 옮긴다.",
    ),
    dict(
        id="C-29", found_on="2026-09-24", found_by="C-27/C-28 회귀 검증 중 A043 계약 실패 8건 판독",
        confidence="확인", severity="경미", status="OPEN",
        repro="import sys;sys.path.insert(0,'tools');"
              "sys.path.insert(0,'workspace/training/quadruped');"
              "import go2_tuning_base_data as b;"
              "print(b.walking_values('lin_vel_z_l2'))",
        repro_expect="[-2.0, -1.5]",
        where="tools/test_go2_g_a043_campaign_contract.py:133 "
              "`PackageTest::test_6_the_value_is_outside_the_observed_range_and_says_so`.",
        what="이 검사는 「걷는 회차는 전부 -2.0 이므로 이 다이얼의 기울기는 미측정이다」를 "
             "`walking_values(TERM) == [-2.0]` 으로 못박았다. 그런데 **G-A043 자신이 -1.5 로 "
             "돌아 걸었고**(WEIGHT_OUTCOME.csv 의 A043 행, rough_forward_speed=0.419) 그 결과가 "
             "기반 데이터에 실렸다. 그래서 같은 사실이 이제 `[-2.0, -1.5]` 다. 계약이 **기획 "
             "시점의 사실**을 시점 표시 없이 굳혀서, 그 회차가 실행되는 순간 스스로 빨개진다.",
        verbatim="AssertionError: Lists differ: [-2.0, -1.5] != [-2.0]",
        source_checked="검사 3건만 따로 실행(151s) → 이 1건만 FAIL. "
                       "WEIGHT_OUTCOME.csv 에서 -1.5 를 가진 걷는 행이 A043 하나임을 확인.",
        origin_fix="회차 계약은 **그 회차가 실행되기 전의 세계**를 검사한다. 기획 시점 사실을 "
                   "시점 없이 적으면 실행이 곧 반증이 된다 — 자기 결과를 제외한 모집단으로 "
                   "묻거나, 사양이 선언한 `OUT_OF_RANGE` 근거 자체를 물어야 한다.",
        resolution="미해결. 값·관문·발행 ZIP 에는 영향이 없다(A043 ZIP 은 재빌드 대조 통과). "
                   "임계값을 사후에 무르지 않기 위해 **단정 완화로 고치지 않는다** — 모집단을 "
                   "「사양 발행 시점까지의 회차」로 한정하는 수정이 맞고, 그것은 별도 결정이다.",
    ),
    dict(
        id="C-30", found_on="2026-09-24", found_by="A043 계약의 ERROR 2건을 클래스 단독 실행으로 재현",
        confidence="확인", severity="경미", status="OPEN",
        # 쌓인 잔여물의 개수는 치우면 사라지는 상태다 — 재현은 **사라지지 않는 것**,
        # 즉 수확물을 복사하는 계약에 여유 공간 가드가 없다는 사실을 묻는다(해소 ①).
        repro="import pathlib;"
              "ms=[f for f in pathlib.Path('tools').glob('test_go2_*.py') "
              "if 'copytree' in f.read_text(encoding='utf-8')];"
              "print(sum(1 for f in ms "
              "if 'disk_usage' not in f.read_text(encoding='utf-8')) > 0)",
        repro_expect="True",
        where="tools/test_go2_g_a043_campaign_contract.py:460 `copy_cases` 의 `shutil.copytree` — "
              "같은 모양이 저장 팔을 임시로 복사하는 모든 계약에 있다.",
        what="계약 한 건이 저장 팔의 case 를 임시 디렉터리로 **수백 MB** 복사한다. 정리는 "
             "`TemporaryDirectory` 가 하므로 **프로세스가 정상 종료해야** 지워진다. 메모리 부족으로 "
             "강제 종료된 배치는 그 단계에 닿지 못해 매번 수백 MB 를 남겼고, 970개 13.8GB 가 쌓여 "
             "디스크 여유가 1.21GB 로 떨어졌다. 그 뒤의 계약은 논리와 무관하게 "
             "`[WinError 112] 디스크 공간이 부족합니다` 로 ERROR 를 냈다. **거짓 빨강이 "
             "진짜 빨강과 같은 자리에 찍히는 것**이 이 결함의 해악이다 — A043 의 ERROR 2건이 "
             "이번 수정의 회귀인지 판정하는 데 시간이 들었다.",
        verbatim="shutil.Error: [('...seed_101/push_pos_x/steps.csv', '...tmpmhsshbnp/...', "
                 "'[WinError 112] 디스크 공간이 부족합니다')]",
        source_checked="GateAndVerifierTest 클래스 단독 실행(423s) 에서 test_5·test_6 이 같은 줄에서 "
                       "같은 WinError 112 로 재현. 단일 실행에서는 3건 모두 통과. "
                       "저장 팔 cases 345 파일 600.3MB, C: 여유 1.21GB.",
        origin_fix="시험이 쓰는 자원은 **메모리만이 아니다**. 잘게 자르라는 규칙을 어긴 비용이 "
                   "메모리에서 한 번, 디스크에서 다시 한 번 청구됐다. 게다가 이 청구서는 "
                   "**다음 회차의 판정을 오염시키는 형태**로 온다.",
        resolution="미해결. 판정에 필요한 조치는 둘이다 — ① 시험 시작 시 여유 공간을 요구해 "
                   "부족하면 ERROR 가 아니라 SKIP 으로 갈라 거짓 빨강을 없앤다, "
                   "② 배치를 강제 종료하지 않도록 한 모듈씩 돈다(2026-09-24 사용자 지시). "
                   "임시 폴더가 표준 경로(LOCALAPPDATA 아래 Temp)가 아니라 "
                   "C:/Users/Public/Documents/ESTsoft/CreatorTemp 라서 일반적인 "
                   "디스크 정리로는 지워지지 않는다는 점을 함께 적는다.",
    ),
    dict(
        id="C-31", found_on="2026-09-24", found_by="C-27/C-28 회귀 검증 중 A038 계약 3건 판독",
        confidence="확인", severity="경미", status="FIXED",
        repro="import json,pathlib;"
              "p=pathlib.Path('workspace/_keep');"
              "ids=[json.loads(f.read_text(encoding='utf-8')) for f in "
              "p.glob('*/evaluation/candidate/identity.json')];"
              "print(all('env_sha256' in d for d in ids), len(ids))",
        repro_expect="True",
        where="tools/test_go2_g_a038_campaign_contract.py:223 `copy_cases` 가 쓰는 identity.json.",
        what="계약이 만드는 **가짜 수확물**의 후보 identity 에 `env_sha256` 칸이 없었다. 판독기는 "
             "그 칸을 요구하므로 `stage_faults=['candidate_identity_env_sha256=None']` 로 "
             "INCONCLUSIVE 를 냈고, 그래서 `test_1`(FAIL/FAIL 대조)과 `test_2`(proxy delta 대조)가 "
             "**진짜 단정에 닿지도 못한 채** 빨개졌다. 진짜 수확물은 그 칸을 쓴다 — 즉 시험 자료가 "
             "현실보다 부실했던 것이고, 제품 결함이 아니다. A038 계약은 2026-09-17 에 얼어붙었는데 "
             "판독기는 09-19~09-24 에 세 번 바뀌었다. 더 새 계약(A043, 09-22)에는 그 칸이 있다.",
        verbatim="AssertionError: Tuples differ: ('FAIL', 'INCONCLUSIVE') != ('FAIL', 'FAIL')",
        source_checked="workspace/_keep 의 후보 identity 전수에 `env_sha256` 존재 확인. "
                       "사양 baseline.env_sha256=ac43a435 이미 존재. 수정 후 모듈 15검사 중 "
                       "빨강이 3건에서 1건(C-2)으로 줄었다.",
        origin_fix="가짜 수확물은 **러너가 실제로 쓰는 것보다 부실하면 안 된다**. 부실하면 그 계약은 "
                   "제품이 아니라 자기 자신을 재는 셈이고, 빨강의 뜻이 「제품이 틀렸다」가 아니라 "
                   "「내 자료가 낡았다」가 되어 판독에 시간이 든다. 판독기를 고칠 때 그것을 먹이는 "
                   "가짜 수확물들도 같은 턴에 따라가야 한다.",
        resolution="2026-09-24 `copy_cases` 가 `env_sha` 를 받아 identity.json 에 쓰도록 고쳤고, "
                   "후보 호출부는 학습된 env 의 sha 를 넘긴다(A043 계약과 같은 모양). "
                   "단정은 하나도 바꾸지 않았다 — 자료만 채웠고 원래 단정이 그대로 통과했다.",
    ),
    dict(
        id="C-32", found_on="2026-09-24", found_by="C-27/C-28 회귀 검증 중 A041 계약 3건 판독",
        confidence="확인", severity="경미", status="FIXED",
        repro="import sys,hashlib;sys.path.insert(0,'tools');"
              "sys.path.insert(0,'workspace/training/quadruped');"
              "import build_go2_a033_reward_package as r, build_go2_candidate_package as c;"
              "s=r.load('G-A041');"
              "print(hashlib.sha256(c.runner_bytes(s)).hexdigest()[:16])",
        repro_expect="1cd87f425d5b89f5",
        where="tools/test_go2_g_a041_campaign_contract.py:92 와 "
              "tools/test_go2_g_a042_campaign_contract.py:102 — 두 계약의 "
              "`test_3_campaign_runner_and_gate_are_what_ran_for_g_a033`.",
        what="검사가 팔의 러너를 **작업본 파일**과 대조했다. 그런데 이 회차는 2026-09-22 에 "
             "C-14 때문에 `1cd87f425d5b89f5` 로 고정됐고, 고정된 회차의 팔은 정의상 작업본이 "
             "아니라 **자기가 돌았던 바이트**를 싣는다. 그래서 그 단정은 **고정이 생긴 날부터 "
             "거짓**이었다. C-27 직전의 작업본은 3e4dd15257f2b2af 로 이미 핀과 달랐으므로, "
             "이 빨강은 2026-09-24 의 수정이 만든 것이 아니다.",
        verbatim="AssertionError: b'#!/[2637 chars]...' != b'#!/[2637 chars]# The outer launcher ...'",
        source_checked="`cand.runner_bytes(SPEC)` = 1cd87f42(37181B), 작업본 = 1913e4db(44840B), "
                       "C-27 직전 작업본 = 3e4dd152. 셋이 모두 다르다.",
        origin_fix="고정 장치를 들여올 때 **그 장치를 모르는 옛 계약**이 남으면, 그 계약의 빨강은 "
                   "제품이 아니라 계약 자신을 가리킨다. 고정은 한 곳에서 켜고 그것을 묻는 "
                   "계약들을 같은 턴에 옮겨야 한다.",
        resolution="2026-09-24 단정을 `ARM[runner] == cand.runner_bytes(SPEC)` 로 바꾸고, 고정이 "
                   "사라지면 잡히도록 `EXECUTED_RUNNERS` 에 이 회차가 있는지도 함께 묻는다. "
                   "원래 의도(이 팔은 G-A038 이 돌린 바이트를 싣지 않는다)는 그대로 남겼다. "
                   "같은 수정을 G-A042 계약(고정본 6fd78eeb8eac5342)에도 넣었다. 수정 뒤 "
                   "A041 은 17검사 OK, A042 는 클래스 셋으로 나눠 26검사 OK.",
    ),
    dict(
        id="C-33", found_on="2026-09-24", found_by="C-17 을 걷어내자 그 아래에서 드러남",
        confidence="확인", severity="경미", status="OPEN",
        repro="import pathlib;"
              "g=pathlib.Path('tools/go2_target_gate.py').read_text(encoding='utf-8');"
              "v=pathlib.Path('tools/verify_go2_basic_motion_harvest.py')"
              ".read_text(encoding='utf-8');"
              "i=v.index('def verify_target_stage');"
              "j=v.index('def ', i+10);"
              "print('gate', 'stationary_reading' in g,"
              " 'local_stage', 'stationary_reading' in v[i:j])",
        repro_expect="gate True local_stage False",
        where="tools/go2_target_gate.py:295 는 1단계 판독에 `stationary_guard` 를 넣는다. "
              "tools/verify_go2_basic_motion_harvest.py 의 `verify_target_stage`(307~374행)에는 "
              "그것이 없다 — 로컬은 정지 가드를 전수 단계의 `4_locomotion` 으로만 본다.",
        what="서버 게이트와 로컬 판독기가 **1단계에서 같은 것을 읽지 않는다.** S-4(2026-09-19)가 "
             "게이트의 1단계에 정지 가드를 넣었는데 로컬 판독기의 1단계는 따라가지 않았다. "
             "방향은 fail-closed 다 — 서버가 더 엄하므로 성공을 과대 주장하지는 않는다. 비용은 "
             "**두 판독기가 다른 답을 줄 수 있다**는 것이다: 로컬이 "
             "`TARGET_PASS_FULL_STAGE_REQUIRED` 를 줄 때 서버는 `FAIL` 일 수 있다. C-17 이 "
             "판정을 INCONCLUSIVE 로 덮고 있는 동안에는 이 차이가 보이지 않았다.",
        verbatim="AssertionError: {...'stationary_guard': {'declared': True, ...}} != {...}",
        source_checked="verify_go2_basic_motion_harvest.py:362~374 의 1단계 판독은 "
                       "target_reading + catastrophe_case + note + climb_guard 뿐이다. "
                       "grep 결과 `stationary_reading` 은 go2_target_gate.py 에만 있다.",
        origin_fix="판독기가 둘이면 **한쪽만 고치는 수정**이 가능해진다. 규칙을 한 곳에 넣을 때 "
                   "그것을 읽는 두 경로가 같이 움직이는지 묻는 관문이 없으면, 차이는 다른 "
                   "결함(C-17)이 걷힐 때까지 숨는다.",
        resolution="미해결. v8 쌍은 `full_69_single_stage` 라 1단계 분기를 쓰지 않으므로 이번 "
                   "회차의 판정에는 닿지 않는다. 다만 안내문이 사용자에게 돌리라고 하는 것이 "
                   "로컬 판독기이므로, 1단계 분기를 쓰는 다음 회차 전에 닫아야 한다. 지금은 "
                   "`test_go2_basic_motion_pair_contract.GateParityTest.test_gain_passes_on_both` "
                   "에 **이름 붙인 발산**으로 고정했다 — 그 검사가 `stationary_guard` 가 로컬에 "
                   "**없음**을 단정하므로, 고치는 순간 빨개져서 알려준다.",
    ),
    dict(
        id="C-34", found_on="2026-09-25", found_by="C-29 가 v8 에 닿는지 확인하다가",
        confidence="확인", severity="중대", status="OPEN",
        repro="import sys,json,pathlib;sys.path.insert(0,'tools');"
              "sys.path.insert(0,'workspace/training/quadruped');"
              "import go2_tuning_base_data as b;"
              "s=json.loads(pathlib.Path('workspace/training/quadruped/config/experiments/"
              "G_A046_seed43_lin_vel_z_m15.json').read_text(encoding='utf-8'));"
              "print(s['base_data']['terms']['lin_vel_z_l2']['walking_values'],"
              "b.walking_values('lin_vel_z_l2'), len(b.spec_problems(s)))",
        # 사양이 적은 목록과 기반 데이터의 목록을 **둘 다** 찍는다 — 어긋남 자체가 출력이다.
        repro_expect="[-2.0, -1.75, -1.5] [-2.0, -1.5] 2",
        where="config/experiments/G_A046_seed43_lin_vel_z_m15.json 의 `base_data` — 그리고 그것을 "
              "싣고 나간 발행본 GO2_G_A045_A046_seed43_pair_full69_v8.zip 안의 experiment.json.",
        what="발행된 v8 팔의 사전등록 자료가 기반 데이터와 어긋난다. ① `walking_values` 를 "
             "`[-2.0, -1.75, -1.5]` 로 적었으나 기반 데이터는 `[-2.0, -1.5]` 다 — `-1.75`(G-A044)는 "
             "WEIGHT_OUTCOME.csv 19행 어디에도 **행이 없다**. 즉 사양이 근거 파일에 없는 관측을 "
             "인용한다. ② `walk_margin` 이 비어 있다(null) — 기반 데이터는 margin 0.148·zone WALK·"
             "worse=[push, sway] 를 낸다. **자를 대는 회차의 사전등록이 자를 과장하고 있다.** "
             "더 나쁜 것은 관문의 공백이다: 옛 A043 계약은 `base_data.spec_problems(SPEC)` 를 "
             "부르는데 새 A045/A046 계약은 부르지 않는다 — 검사가 뒤로 갔다.",
        verbatim="base_data.terms.lin_vel_z_l2 != {... 'walking_values': [-2.0, -1.5] ...}; "
                 "base_data.walk_margin != {...}",
        source_checked="b.spec_problems(G-A046) 가 2건을 낸다. b.walking_values('lin_vel_z_l2') = "
                       "[-2.0, -1.5]. WEIGHT_OUTCOME.csv 에 A044 행 없음(19행 전수). "
                       "G-A045 는 spec_problems 0건 — 어긋난 것은 A046 한 팔이다.",
        origin_fix="사전등록을 **손으로 적고 기계가 대조하지 않으면**, 기반 데이터가 움직일 때 "
                   "사양만 과거에 남는다. 같은 뿌리가 C-29 다 — 그쪽은 계약이 낡아 빨개졌고, "
                   "이쪽은 계약이 없어 조용했다. 빨간 것보다 조용한 쪽이 위험하다.",
        resolution="미해결. 발행 ZIP 은 불변이므로 이 판을 고치지 않는다 — 다음 판(v9)에서 "
                   "`base_data` 를 기반 데이터에서 생성하고, A045/A046 계약에 "
                   "`spec_problems(SPEC) == []` 를 넣어 같은 일이 조용히 지나가지 않게 한다. "
                   "그 전까지 v8 은 **실행 보류**다: 자를 대는 회차의 자가 과장돼 있으면 "
                   "그 회차로 잰 값의 해석이 흔들린다.",
    ),
)


FIGURES: tuple[tuple[str, str, str], ...] = (
    ("X-1", "34298008", "HEAD 의 발행 ZIP 바이트 수"),
    ("X-1", "34298254", "현재 파일의 바이트 수"),
    ("S-2", "4", "stairs_15_climb_ge1 의 baseline_sum"),
    ("S-2", "5.523", "같은 관문의 max_drop = 2*sqrt(var)"),
    ("S-2", "-1.523", "그래서 나오는 하한 — 음수라 발화 불가"),
    ("S-2", "83.329", "살아 있는 10cm 관문의 하한"),
    ("S-3", "-2.5", "사양이 인용한 외부 기준 go2_flat 값 — 원문 파일 없음"),
    ("S-3", "0.0", "원문 확인된 Isaac Lab Go2 rough 값"),
    ("B-1", "9", "다른 사양 4건이 지키는 표적 수 상한"),
    ("B-1", "12", "넓힌 상한 — G-A040 표적 3+6+3 과 같다"),
    ("R-1", "0.7431", "감사자가 심어 통과한 조작값"),
    ("R-2", "1.786", "문서에 적힌 값"),
    ("R-2", "1.785", "원자료 값"),
    ("D-1", "0.05", "own_rounded 가 늘린 문서별 오탐률 하단(%p)"),
    ("D-1", "1.8", "같은 오탐률 상단(%p)"),
    ("P-1", "14", "CASES.csv 의 기존 행 수 — 09-19 항목 0건"),
    ("C-2", "INFORMATION_RUN", "발행 ZIP 이 싣는 G-A035 추론 사슬 상태"),
    ("C-2", "HOLD_UNSUPPORTED", "현재 사양이 적는 같은 회차 상태"),
    ("C-2", "3", "사양과 어긋난 발행 ZIP 수 (G-A035·G-A037·G-A039)"),
    ("C-2", "-0.04", "2026-09-20 예측 격자에 넣은 탐침 값 — 이 결함과 무관함을 보이는 대조"),
    ("C-4", "9", "발행된 G-A041 README·안내문이 적은 표적 case 수"),
    ("C-4", "12", "그 회차가 실제로 채점한 표적 case 수"),
    ("C-4", "20", "G-A042 가 1단계에서 재는 case 수"),
    ("C-5", "3", "G-A041 에서 사라진 15cm 기록의 seed 수"),
    ("C-5", "PARTIAL", "그래서 기록된 G-A041 회수 완결 상태"),
    ("C-6", "95", "발행 ZIP 의 member 수"),
    ("C-6", "2", "재빌드와 실제로 다른 member 수"),
    ("C-7", "9", "발행된 v4 러너 주석이 적은 표적 case 수"),
    ("C-7", "5", "같은 러너가 기준선을 A017 이라 부르는 자리 수"),
    ("C-8", "1.2", "회차 ZIP 의 baseline/quadruped_rewards.py 가 싣는 값"),
    ("C-11", "23", "G-A043 1단계가 잰 case 수"),
    ("C-11", "0", "그 안에 든 결정적 위반 case 수 — 3개 모두 밖에 있었다"),
    ("C-8", "1.5", "같은 ZIP 의 기준선 env.yaml 과 reference 파일의 값"),
    ("C-9", "95", "발행된 feet_air_time ZIP 의 member 수"),
    ("C-9", "2", "재빌드와 다른 member 수 — 이제 아무 관문도 보지 않는다"),
    ("C-12", "4", "표가 멈춘 뒤 실행·회수된 회차 수"),
    ("C-12", "1", "그 중 기반 데이터 표에 들어간 회차 수 — 나머지 셋은 아직 밖이다"),
    ("C-13", "10", "러너 영상 지문에 들어가는 인자 수"),
    ("C-13", "3", "빌더가 상수로 박아 두었던 인자 수"),
    ("C-14", "10", "팔 러너의 재진입 줄을 한 번도 실행하지 않은 발행 회차 수"),
    ("C-14", "127", "그 줄이 유일한 경로가 되었을 때 tmux 세션의 종료 코드"),
    ("C-14", "0", "그때 바깥 스크립트가 사용자에게 돌려주던 종료 코드"),
    ("C-15", "2", "안내문대로 친 회수 명령의 argparse 종료 코드"),
    ("C-16", "4", "SHA 한 줄이 가리고 있던 종료 게이트 항목 수"),
    ("C-17", "4", "신원 결손이 INCONCLUSIVE 로 덮고 있는 계약 테스트 수"),
    ("C-18", "4", "A044 history 에 같은 이름으로 쌓여 있던 ZIP 수"),
    ("C-18", "12", "판 번호 없는 이름으로 발행된 회차 수(A031~A044)"),
    ("C-19", "19", "계획서와 일치한 사전등록 숫자 항목 수(차이 0)"),
    ("C-19", "3", "계획서 약속 중 산출물로 옮겨지지 않았던 항목 수"),
    ("C-20", "0", "성능 FAIL 일 때 첫 판독기가 내는 exit code"),
    ("C-20", "2", "그 판독기가 exit 1 로 내는 비성능 판정의 수"),
    ("C-21", "2", "v7 사양이 ZIP 에 싣고 간 판독 명령 수"),
    ("C-21", "1", "그중 argparse exit 2 로 죽는 명령 수"),
    ("C-22", "3", "test_21 이 가르는 수집 상태의 수"),
    ("C-22", "68", "전수 완료로 오인되면 안 되는 잘린 수집의 case 수"),
    ("C-23", "81", "두 러너를 관문 방식으로 벗겨 비교했을 때의 차이 줄 수"),
    ("C-23", "0", "그 차이 중 2026-09-23 수정이 만든 줄 수"),
    ("C-24", "3", "안내문 §4 가 이제 나누어 적는 종료 상태의 수"),
    ("C-24", "0", "러너의 crash 경로가 찍는 완료 표식의 수"),
    ("C-25", "4", "정본 원장이 멈춘 뒤 실행·회수된 회차 수 (A041~A044)"),
    ("C-25", "0", "그 넷 중 회차 선택 규칙이 읽는 표에 들어 있던 회차 수"),
    ("C-26", "4", "사전등록 해석에서 고친 자리 수 (원인·재현·분기·규정)"),
    ("C-26", "0", "그 정정으로 바뀐 판정 문턱의 수"),
    ("C-27", "3", "재개가 말없이 지우던 자료 종류 (checkpoint · exported · 학습 로그)"),
    ("C-27", "0", "그 삭제를 막을 수 있던 기존 검사의 수"),
    ("C-28", "3", "이제 건너뛰기가 요구하는 조건 수 (완료 · ZIP · SHA)"),
    ("C-28", "0", "고치기 전 판단이 수집·ZIP 을 보던 횟수"),
    ("C-29", "0.419", "A043 의 rough_forward_speed — 걷는 회차로 집계된 이유"),
    ("C-29", "-1.5", "그래서 걷는 관측값에 새로 들어온 lin_vel_z_l2"),
    ("C-30", "970", "강제 종료가 남긴 임시 디렉터리 수"),
    ("C-30", "13.8", "그 잔여물이 차지한 GB"),
    ("C-30", "1.21", "그래서 남은 C: 여유 GB — 시험 하나가 0.6GB 를 쓴다"),
    ("C-31", "3", "고치기 전 A038 계약의 빨강 수"),
    ("C-31", "1", "고친 뒤 남은 빨강 수 — 그 하나가 C-2 다"),
    ("C-32", "37181", "A041 이 돌린 러너의 바이트 수"),
    ("C-32", "44840", "같은 이름의 작업본 파일 — 계약이 이것과 같기를 요구했다"),
    ("C-33", "152", "검사 한 건의 최대 메모리 MB — 분할의 바닥"),
    ("C-34", "0.148", "A046 사양이 비워 둔 walk_margin 의 실제 값"),
    ("C-34", "19", "WEIGHT_OUTCOME.csv 의 행 수 — 그중 A044 행은 없다"),
)


def field(d: dict, name: str) -> str:
    """기록에 없는 칸은 빈 칸이다.  `confidence` 만 기본값이 `추정` — 재현하지 않았다는 뜻이다."""
    if name == "confidence":
        return d.get("confidence", "추정")
    return d.get(name, "")


def sort_key(d: dict) -> tuple:
    return (STATUS_ORDER.get(d["status"], 9), SEVERITY_ORDER.get(d["severity"], 9), d["id"])


def counts() -> dict[str, int]:
    got = {"OPEN": 0, "FIXED": 0, "ACCEPTED": 0}
    for d in DEFECTS:
        got[d["status"]] = got.get(d["status"], 0) + 1
    return got


def write_csv(stream: io.StringIO) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("section",) + FIELDS)
    for d in sorted(DEFECTS, key=sort_key):
        writer.writerow(("defect",) + tuple(field(d, f) for f in FIELDS))
    writer.writerow(())
    writer.writerow(("section",) + FIGURE_FIELDS)
    for row in FIGURES:
        writer.writerow(("figure",) + row)


def document() -> str:
    got = counts()
    lines = [
        "# Go2 결함 대장 — 감사 결과를 파일로 남긴다",
        "",
        f"생성 `tools/go2_defect_ledger.py`, 증거 `{OUT_CSV.relative_to(QUAD).as_posix()}`.",
        "**이 문서를 손으로 고치지 않는다** — 기록은 생성기의 `DEFECTS` 한 곳에만 있다.",
        "",
        "이 대장이 생긴 이유(2026-09-19). 감사자의 보고 형식(`.claude/agents/go2-auditor.md:97-98`)이",
        "\"결론 한 줄 + 결함 표\"이고 **파일 경로가 없어서**, 감사 결과가 대화와 함께 사라졌다.",
        "2026-09-14 감사는 파일 3개로 남았지만 2026-09-18 · 2026-09-19 감사는 0개다. 그래서",
        "`G-1` · `G-2` · `A-7` 은 이전 감사에서 이미 나왔는데도 다음 감사자가 **처음부터 다시 찾았다**.",
        "결함 수가 산출물 품질이 아니라 *마지막 확인 이후 경과 시간*의 함수가 된 원인이 이것이다.",
        "",
        f"현재: **OPEN {got['OPEN']}건 / ACCEPTED {got['ACCEPTED']}건 / FIXED {got['FIXED']}건**"
        f" (총 {len(DEFECTS)}건)",
        "",
        "`ACCEPTED` 로 바꿀 수 있는 것은 **사용자뿐이다**. 감사자도 기획자도 PM도 못 바꾼다.",
        "",
        "`확인`은 재현 명령을 실제로 돌려 본 것이고, `추정`은 보고만 받은 것이다 —",
        "**중계할 때 `추정`의 확신을 올리지 않는다.** 발견자의 원문이 있으면 `발견자 원문` 절에 그대로 싣는다.",
        "",
        "| ID | 상태 | 확신 | 심각도 | 발견 | 어디 | 무엇이 틀렸나 | 원천 수정 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in sorted(DEFECTS, key=sort_key):
        lines.append(
            f"| `{d['id']}` | {d['status']} | {field(d, 'confidence')} | {d['severity']} |"
            f" {d['found_on']} | `{d['where']}` | {d['what']} | {d['origin_fix']} |")
    lines += [
        "",
        "## 재현 명령 — 없으면 `확인`이 아니다",
        "",
        "| ID | 확신 | 재현 |",
        "|---|---|---|",
    ]
    for d in sorted(DEFECTS, key=sort_key):
        lines.append(f"| `{d['id']}` | {field(d, 'confidence')} | {field(d, 'repro') or '—'} |")
    lines += [
        "",
        "## 확인한 원본",
        "",
        "| ID | 확인한 원본 | 처리 |",
        "|---|---|---|",
    ]
    for d in sorted(DEFECTS, key=sort_key):
        lines.append(f"| `{d['id']}` | {d['source_checked']} | {d['resolution'] or '—'} |")
    verbatim = [d for d in sorted(DEFECTS, key=sort_key) if field(d, "verbatim")]
    if verbatim:
        lines += ["", "## 발견자 원문 — 중계가 원문보다 세지면 여기를 연다", ""]
        for d in verbatim:
            lines += [f"**`{d['id']}`** ({d['found_by']})", "", f"> {field(d, 'verbatim')}", ""]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    write_csv(buffer)
    OUT_CSV.write_text(buffer.getvalue(), encoding="utf-8", newline="")
    OUT_DOC.write_text(document(), encoding="utf-8", newline="")
    got = counts()
    print(OUT_CSV.relative_to(ROOT).as_posix())
    print(OUT_DOC.relative_to(ROOT).as_posix())
    print(f"결함 {len(DEFECTS)}건 — OPEN {got['OPEN']} / ACCEPTED {got['ACCEPTED']} / FIXED {got['FIXED']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
