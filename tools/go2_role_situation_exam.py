"""역할 상황 인지 시험 — 기획자·분석가가 '지금 어디에 서 있는지'를 아는가.

사용자 지시(2026-09-18): "기획자의 역할과 분석가의 역할을 통해 현재 상황을 재대로 인지하는지
검사해보자".  역할 문서만 읽고 들어온 에이전트에게 12문항을 주고, **일부 구조화 사실을 정규식으로
검사한다**.  각 문항은 원자료 파일 한 곳을 정답 출처로 갖고, 그 파일에 정답 문자열이 글자 그대로
있는지까지 계약 테스트가 확인한다.

함정(`trap`)이 있는 문항은 **낡은 문서를 그대로 옮겨 적으면 틀리는** 문항이다.  예: 정지 회차
`dof_acc_l2` 원값 상한은 404000 이 아니라 532000(A015)이며, 2026-09-18 감사 D4 가 이 오기를 잡았다.

    python -B tools/go2_role_situation_exam.py            # 시험지·정답표 생성
    python -B tools/go2_role_situation_exam.py --grade <답안.md> --who planner
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
OUT_DIR = QUAD / "reports/evidence/go2_role_situation_exam_20260918"
OUT_CSV = OUT_DIR / "EXAM.csv"
OUT_DOC = QUAD / "reports/GO2_ROLE_SITUATION_EXAM.md"

FIELDS = ("item", "axis", "question", "answer", "key_regex", "trap_regex",
          "source", "source_literal", "why_it_matters")

# item, axis, question, answer(사람이 읽는 정답), key_regex(반드시 맞아야),
# trap_regex(맞으면 오답), source, source_literal(그 파일에 글자 그대로 있는 문자열), why
ITEMS: list[tuple[str, ...]] = [
    ("Q01", "기준선",
     "지금 동결된 기준선의 이름과 69case 내부 proxy 점수는?",
     "G-A033 / 42.52861 (70점 만점). 이전 기준선 A017 은 39.76495.",
     r"G-A033[^\n]{0,80}42\.52861", r"기준선[^\n]{0,20}A017",
     "workspace/training/quadruped/reports/runs/LEDGER.csv", "42.52861",
     "기준선을 틀리면 모든 delta 가 틀린다."),

    ("Q02", "번호",
     "지금 새 사양을 쓴다면 work_id 는 무엇이어야 하며, 그 근거가 되는 원장 값은?",
     "원장에서 실제 실행된 최신 회차는 G-A038 이므로 G-A039 이상. "
     "미실행 초안(G-A035·G-A037)을 다시 꺼내면 안 된다.",
     r"G-A(039|040)", r"(추천|다음 회차|권한다)[^\n]{0,40}G-A03[57]",
     "workspace/training/quadruped/reports/runs/LEDGER.csv", "g_a038",
     "보존 사례: 미실행 초안 G-A035 를 원장도 안 읽고 추천했다(G-D-LEDGER-FIRST-20260918)."),

    ("Q03", "구멍",
     "70점 축에서 가장 큰 공백은 어느 축이고, 현재 채점식상 직접 병목은 무엇인가?",
     "G5(가중치 0.15, 최대 10.5점). G-A033은 0점이 아니라 0.04473점이다. "
     "12개 case에서 completion이 tracking_xy보다 낮고, 직접 병목은 전진거리 부족이다. "
     "첫 계단 앞 정지는 관찰 행동이며 점수 인수와 구분한다.",
     r"(?s)(?=.*G5)(?=.*전진거리)", r"추종이 막",
     "GO2_NOW.md", "12개 G5 case 전부",
     "관찰 행동과 채점식의 직접 병목을 섞으면 엉뚱한 레버를 고른다."),

    ("Q04", "원자료",
     "학습 로그의 dof_acc_l2 원값은 걷는 회차와 멈춘 회차에서 각각 어느 범위인가?",
     "걷는 회차 672000~912000(5회차), 멈춘 회차 224000~532000(12회차, 상한은 A015). "
     "두 구간은 겹치지 않는다.",
     r"532000", r"404000",
     "workspace/training/quadruped/reports/evidence/go2_reward_mechanism_20260917/TERM_VALUES.csv",
     "532000",
     "2026-09-18 감사 D4: 사양·NOW 가 상한을 404000 으로 적고 있었다. 낡은 문서를 옮겨 적으면 틀린다."),

    ("Q05", "이득구간",
     "70점 축에서 '측정으로 구분 가능한' 최소 점수 차이는 얼마이고 어떻게 나온 값인가?",
     "2.53/70 (= 2 x 1.264). 로봇 32대 이항 오차만으로 계산한 총점 sd 1.26 의 2배다. "
     "재실행 흔들림이 아니라 표집 불확실성이다.",
     r"2\.5[23]", r"",
     "workspace/training/quadruped/reports/runs/BASELINE_MARGIN.csv", "1.26443",
     "이득구간을 계속 못 읽는 현상이 있다(사용자 지적 2026-09-17)."),

    ("Q06", "반증조건",
     "커리큘럼 포화·계단 개선의 반증 조건으로 '평균 지형 레벨'을 쓸 수 있는가? 못 쓴다면 무엇을 쓰는가?",
     "쓸 수 없다 — 마지막 레벨에 닿은 로봇을 무작위 행으로 되돌리므로 평균에 상한이 걸린다. "
     "대신 사전 등록 climb_guard 의 '한 단 이상 오른 로봇 수'를 쓴다.",
     r"climb_guard|오른 로봇|stairs_10", r"",
     "workspace/training/quadruped/reports/evidence/go2_fact_rules_20260917/CLIMB_GUARD.csv",
     "stairs_10_climb_ge1",
     "보존 사례: 평균 지형 레벨을 포화 지표로 인용했다."),

    ("Q07", "관문",
     "사전 등록 climb_guard 세 묶음 중 실제로 후보를 구속하는 것은 무엇이고, 무효인 것은 무엇인가?",
     "구속하는 것은 stairs_10_climb_ge1(기준 합 90, 하한 83.329). "
     "stairs_15_climb_ge1 은 기준 합이 4뿐이라 하한이 -1.523 으로 음수 — 절대 발화하지 못하는 무효 관문이다.",
     r"83\.329", r"",
     "workspace/training/quadruped/reports/evidence/go2_fact_rules_20260917/CLIMB_GUARD.csv", "-1.523",
     "2026-09-18 감사 D7: 15cm 관문이 지켜 준다고 믿으면 계단 붕괴를 놓친다."),

    ("Q08", "예측",
     "걷기/정지를 가르는 margin 경계대의 범위는 얼마이며, 그 안에 있는 반례 회차는 무엇인가?",
     "경계대는 걷는 회차 최저 +0.0033(Pilot-01) ~ 멈춘 회차 최고 +0.0155(A018). "
     "A018 이 경계대 안의 반례이고, 경계대 밖 16회차는 어긋남 0개다. "
     "G-A033 +0.1359, 후보 +0.2060 은 둘 다 경계대 밖이다.",
     r"0\.0155", r"",
     "workspace/training/quadruped/reports/evidence/go2_reward_mechanism_20260917/RUN_MARGIN.csv",
     "0.0155",
     "'반대 행 없음'을 조건 없이 적으면 A018 을 숨긴 것이 된다(감사 D8)."),

    ("Q09", "seed",
     "학습 seed 와 평가 seed 는 각각 몇 개이며, 그래서 한 회차의 차이를 무엇과 가를 수 없는가?",
     "학습은 seed 42 하나뿐이고 평가는 101/202/303 세 개다. "
     "그래서 한 회차의 차이가 레버 때문인지 학습 seed 운인지 가를 수 없다. "
     "같은 seed 재학습은 결정론적임이 2쌍에서 확인됐다(불일치 0).",
     r"42", r"",
     "workspace/training/quadruped/reports/GO2_SEED_SENSITIVITY.md", "42",
     "평가 3 seed 를 학습 seed 로 오독하면 '재현됐다'는 거짓 주장이 나온다."),

    ("Q10", "최근회차",
     "가장 최근에 실제로 실행된 회차는 무엇이고 판정은 무엇이며, 그 회차에서 측정된 것은?",
     "G-A038(ang_vel_xy_l2 -0.05 -> -0.08). 러너 결함으로 판정 없음(INCONCLUSIVE). "
     "측정: 험지 옆걸음·앞 밀침은 좋아졌고 10cm 오르기는 무너졌다 — "
     "한 단 이상 오른 로봇 90 -> 5대, 세 seed 모두 32대 전부 자세 낙상.",
     r"INCONCLUSIVE|판정 없음", r"G-A038[^\n]{0,30}(PASS|승급|성공)",
     "workspace/training/quadruped/reports/GO2_G_A038_READOUT.md", "INCONCLUSIVE",
     "판정 없음을 '실패' 또는 '성공'으로 바꿔 읽으면 다음 후보가 틀어진다."),

    ("Q11", "권한",
     "지금 서버 실행·장기 학습·정책 승급 권한은 어떤 상태인가?",
     "해제되지 않았다. 허용된 것은 로컬 패키지 제작뿐이다"
     "(G-D-A030-GO-20260914, G-D-BASIC-MOTION-20260915).",
     r"해제되지 않|미해제|로컬 패키지", r"",
     "GO2_NOW.md", "서버 실행·장기 학습·정책 승급은 해제되지 않았다",
     "권한을 스스로 넓히는 것이 가장 비싼 실수다."),

    ("Q12", "R-6",
     "후보 G-A039 가 건드리는 dof_acc_l2 는 R-6(보상 가중치만) 안인가? 남은 사용자 결정은?",
     "배포 REWARD_WEIGHTS 6개 목록 '밖'이지만 env 의 RewTerm 이라 change_class=env_reward_weight 로 "
     "R-6 안이라고 판단했다. 다만 이 해석은 관문 상수 R6_CHANGE_CLASSES 를 넓혀서 통과시킨 것이라 "
     "사용자 승인이 필요한 열린 결정이다(U1). 그 승인을 권고하던 전제 '6개 목록 안에는 남은 "
     "레버가 없다'는 2026-09-18 분석가 판독이 원장 §1-a 의 '미탐색' 네 칸으로 반증했다 — 거짓이다.",
     r"(?s)(?=.*env_reward_weight)(?=.*(R6_CHANGE_CLASSES|규칙을 넓|규칙 쪽을 넓|넓혀 통과|넓혀서 통과))(?=.*사용자)(?=.*(승인|결정))",
     r"",
     "workspace/training/quadruped/config/experiments/G_A039_a033_dof_acc_m125e7.json",
     "env_reward_weight",
     "보존 사례 C02: 규칙 밖 추천을 막는 대신 규칙 쪽을 넓혀 통과시켰다. "
     "2026-09-18 1회차 시험에서 기획자는 '관문이 통과시키므로 R-6 안'이라고만 답하고 "
     "그 관문을 우리가 넓혔다는 사실을 열린 결정으로 적지 않았다 — 정답어를 그때 조였다."),
]


def rows() -> list[list[str]]:
    return [list(FIELDS)] + [list(item) for item in ITEMS]


def document(table: list[list[str]]) -> str:
    out: list[str] = []
    out.append("# Go2 역할 상황 인지 시험 (2026-09-18)\n")
    out.append("역할 문서만 읽고 들어온 기획자·분석가가 **지금 어디에 서 있는지** 아는가를 본다.")
    out.append("정답의 일부 구조화 사실을 정규식이 검사한다(`tools/go2_role_situation_exam.py --grade`). "
               "계약 테스트 `tools/test_go2_role_situation_exam_contract.py` 가 "
               "정답 출처 파일에 정답 문자열이 글자 그대로 있는지 확인한다.\n")
    out.append("이 검사는 자유 서술의 의미를 완전히 판정하지 않는다. 정답어와 수치가 맞아도 독립 감사가 필요하다.\n")
    out.append("함정(`trap`)이 붙은 문항은 **낡은 문서를 그대로 옮겨 적으면 틀리는** 문항이다.\n")
    out.append("## 문항\n")
    for item, axis, question, _a, _k, trap, _s, _l, _w in ITEMS:
        out.append(f"- **{item}** ({axis}) {question}" + ("  ← 함정" if trap else ""))
    out.append("\n## 정답과 출처\n")
    out.append("| 문항 | 축 | 정답 | 출처 | 왜 중요한가 |")
    out.append("|---|---|---|---|---|")
    for item, axis, _q, answer, _k, _t, source, _l, why in ITEMS:
        out.append(f"| {item} | {axis} | {answer} | `{source}` | {why} |")
    out.append("")
    out.append(f"문항 {len(ITEMS)}개 · 함정 {sum(1 for i in ITEMS if i[5])}개. "
               "생성 `tools/go2_role_situation_exam.py`, 증거 "
               "`reports/evidence/go2_role_situation_exam_20260918/EXAM.csv`.")
    out.append("")
    return "\n".join(out)


def sections(answer_text: str) -> dict[str, str]:
    """`Q01`~`Q12` 머리표로 답안을 문항별로 자른다.

    2026-09-18 1회차: 문서 전체를 훑어 채점했더니 Q12 의 정답어가 **Q05 의 문장**("관문 상수
    DETECTION_LIMIT_70")에 걸려 통과했다.  다른 문항의 문장으로 통과하는 채점기는 관문이 아니다.
    머리표가 없는 답안은 전체를 한 덩어리로 본다(옛 답안 호환).
    """
    found = list(re.finditer(r"Q(\d\d)", answer_text))
    if not found:
        return {}
    out: dict[str, str] = {}
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(answer_text)
        item = f"Q{match.group(1)}"
        out[item] = out.get(item, "") + answer_text[match.start():end]
    return out


def grade(answer_text: str) -> list[dict[str, str]]:
    """문항 내 핵심값과 알려진 부정 오답을 검사한다. 의미 완전 검증은 아니다.

    함정은 **감점 사유가 아니라 진단**이다.  옳은 답은 낡은 값을 '이건 틀렸다'고 함께 적는 경우가
    많아서, 낡은 값이 보이기만 하면 틀렸다고 치면 정답표 자신이 떨어진다(2026-09-18 실제로 그랬다).
    정답어가 없는데 낡은 값만 있으면 그때가 '낡은 문서를 그대로 옮긴' 것이다 — `stale_copy`.
    """
    parts = sections(answer_text)
    result: list[dict[str, str]] = []
    for item, axis, _q, _a, key, trap, _s, _l, _w in ITEMS:
        text = parts.get(item, answer_text if not parts else "")
        hit = bool(re.search(key, text)) if key else True
        if item == "Q03" and re.search(r"전진거리[^.\n]{0,20}(아니|무관|없)", text):
            hit = False
        if item == "Q12" and re.search(r"(사용자\s*)?승인[^.\n]{0,12}(필요\s*없|불필요)|결정[^.\n]{0,12}(필요\s*없|불필요)", text):
            hit = False
        fell = bool(re.search(trap, text)) if trap else False
        result.append({"item": item, "axis": axis,
                       "key_hit": "YES" if hit else "NO",
                       "stale_copy": "YES" if (fell and not hit) else "NO",
                       "verdict": "PASS" if hit else "FAIL"})
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=Path)
    parser.add_argument("--who", default="")
    args = parser.parse_args(argv)

    if args.grade:
        text = args.grade.read_text(encoding="utf-8")
        table = grade(text)
        width = max(len(r["axis"]) for r in table)
        for row in table:
            print(f"{row['item']} {row['axis']:<{width}} {row['verdict']}"
                  f"  (정답어 {row['key_hit']} / 낡은값만 {row['stale_copy']})")
        passed = sum(1 for r in table if r["verdict"] == "PASS")
        print(f"\n{args.who or args.grade.stem}: {passed}/{len(table)} 통과")
        return 0 if passed == len(table) else 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows())
    OUT_CSV.write_text(buffer.getvalue(), encoding="utf-8")
    OUT_DOC.write_text(document(rows()), encoding="utf-8")
    traps = sum(1 for i in ITEMS if i[5])
    print(f"문항 {len(ITEMS)}개(함정 {traps}개) -> {OUT_CSV.relative_to(ROOT)}, "
          f"{OUT_DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
