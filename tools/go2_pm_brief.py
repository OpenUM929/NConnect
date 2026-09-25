"""PM 이 사용자에게 내는 수치를 **관문을 지나는 문서**로 만든다.

이 도구가 존재하는 이유(2026-09-19).  하루 동안 철회된 주장 4건 중 3건이 서브에이전트의 결함이
아니라 **내 중계**에서 나왔다.  판독문 · 사양 · 감사문에는 전부 관문이 있는데 **PM 이 사용자에게
직접 하는 말에만 관문이 없었다** — `go2_claim_check` 는 `reports/*.md` 를 보지 내 대화 답변은
보지 않는다.  D-0 사고가 일어난 자리가 정확히 거기다.

그래서 보고 경로를 바꾼다.  결함 건수와 열린 결정은 생성 문서와 CSV 에 출처별로 놓는다.
생성기 일치 테스트는 숫자 집계의 일치를 확인하지만 자유 서술의 의미까지 보증하지 않는다.

숫자는 사람이 아니라 이 도구가 만든다 — 결함 대장(`tools/go2_defect_ledger.py`)에서 읽어 센다.
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import go2_defect_ledger as ledger  # noqa: E402
from tools import go2_open_decisions as decisions  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
OUT_DOC = QUAD / "reports/GO2_PM_BRIEF.md"
OUT_DIR = QUAD / "reports/evidence/go2_pm_brief"
OUT_CSV = OUT_DIR / "BRIEF.csv"

TEST_RE = re.compile(r"tools/test_go2_[a-z0-9_]+\.py")


def tally() -> list[tuple[str, str]]:
    """대장에서 센다 — 사람이 세지 않는다."""
    rows: list[tuple[str, str]] = [("defects_total", str(len(ledger.DEFECTS)))]
    for status in ("OPEN", "FIXED", "ACCEPTED"):
        rows.append((f"status_{status}", str(sum(1 for d in ledger.DEFECTS if d["status"] == status))))
    for severity in ("중대", "경미"):
        rows.append((f"severity_{severity}", str(sum(1 for d in ledger.DEFECTS if d["severity"] == severity))))
    for confidence in ledger.CONFIDENCE:
        rows.append((f"confidence_{confidence}",
                     str(sum(1 for d in ledger.DEFECTS if ledger.field(d, "confidence") == confidence))))
    rows.append(("open_중대", str(sum(1 for d in ledger.DEFECTS
                                    if d["status"] == "OPEN" and d["severity"] == "중대"))))
    return rows


def awaiting_user() -> list[dict]:
    """결함 대장에서 사용자 결정을 명시한 OPEN 항목."""
    return [d for d in ledger.DEFECTS
            if d["status"] == "OPEN" and "사용자 결정" in d["origin_fix"]]


def open_decisions() -> list[tuple[str, ...]]:
    """별도 열린 결정 원장에서 읽는다. 결함 대장 검색 결과와 합쳐 추측하지 않는다."""
    return [entry for entry in decisions.DECISIONS if entry[8] == "OPEN"]


def gates() -> list[tuple[str, str]]:
    """닫힌 결함마다 그것을 지키는 관문.  관문 없이 닫힌 결함은 여기서 드러난다."""
    rows = []
    for d in sorted(ledger.DEFECTS, key=ledger.sort_key):
        if d["status"] != "FIXED":
            continue
        found = sorted(set(TEST_RE.findall(d["resolution"])))
        rows.append((d["id"], " · ".join(found) if found else "(관문 없음)"))
    return rows


def write_csv(stream: io.StringIO) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("section", "key", "value"))
    for key, value in tally():
        writer.writerow(("tally", key, value))
    writer.writerow(())
    writer.writerow(("section", "id", "gate"))
    for defect_id, gate in gates():
        writer.writerow(("gate", defect_id, gate))
    writer.writerow(())
    writer.writerow(("section", "id", "decision"))
    for d in awaiting_user():
        writer.writerow(("awaiting_user", d["id"], d["origin_fix"]))
    for entry in open_decisions():
        writer.writerow(("open_decision", entry[0], entry[1]))


def document() -> str:
    counts = dict(tally())
    lines = [
        "# Go2 PM 보고 — 생성기 집계와 열린 결정 원장",
        "",
        f"생성 `tools/go2_pm_brief.py`, 증거 `{OUT_CSV.relative_to(QUAD).as_posix()}`,",
        "관문 `tools/test_go2_pm_brief_contract.py`. **이 문서를 손으로 고치지 않는다.**",
        "",
        "이 문서가 생긴 이유(2026-09-19). 하루 동안 철회된 주장 4건 중 3건이 서브에이전트의 결함이",
        "아니라 **PM 의 중계**에서 나왔다. 판독문·사양·감사문에는 관문이 있는데 **PM 이 사용자에게",
        "직접 하는 말에만 관문이 없었다.** 그래서 수치와 판정을 산문으로 요약해 내지 않고 이 문서를",
        "만들어 가리킨다. 집계는 계약 테스트로 대조하지만 의미 판단은 별도 감사가 필요하다.",
        "",
        "## 결함 현황",
        "",
        "| 항목 | 수 |",
        "|---|---:|",
        f"| 전체 | {counts['defects_total']} |",
        f"| OPEN | {counts['status_OPEN']} |",
        f"| FIXED | {counts['status_FIXED']} |",
        f"| ACCEPTED | {counts['status_ACCEPTED']} |",
        f"| 중대 | {counts['severity_중대']} |",
        f"| 경미 | {counts['severity_경미']} |",
        f"| OPEN 중 중대 | {counts['open_중대']} |",
        f"| 재현 확인(`확인`) | {counts['confidence_확인']} |",
        f"| 미재현(`추정`) | {counts['confidence_추정']} |",
        "",
        "`확인`은 재현 코드를 관문이 **실제로 돌려** 기대 출력이 나온 것이다. `추정`은 보고만 받고",
        "아직 재현하지 않은 것이므로, 중계할 때 확신을 올리지 않는다.",
        "",
        "## 닫힌 결함과 그것을 지키는 관문",
        "",
        "| 결함 | 관문 |",
        "|---|---|",
    ]
    for defect_id, gate in gates():
        lines.append(f"| `{defect_id}` | `{gate}` |")
    pending = awaiting_user()
    lines += [
        "",
        "## 사용자 결정 대기 — 결함 대장",
        "",
        "차단 사유(R-6 위반 · 테스트 실패 · 회수 불가)와 **다르다**. 과학적 불확실성은 차단 사유가",
        "아니라 사전등록 항목이므로 여기 적지 않는다.",
        "",
    ]
    if pending:
        lines += ["| 결함 | 무엇을 정해야 하나 |", "|---|---|"]
        for d in pending:
            lines.append(f"| `{d['id']}` | {d['origin_fix']} |")
    else:
        lines.append("결함 대장에서 사용자 결정을 명시한 OPEN 항목은 없다.")
    lines += ["", "## 열린 결정 원장", "",
              "아래는 결함과 별도로 `tools/go2_open_decisions.py`의 OPEN 행에서 읽었다.",
              "결정 대기는 곧 학습 패키지 발행 차단을 뜻하지 않는다.", ""]
    if open_decisions():
        lines += ["| 결정 | 해석 쟁점 |", "|---|---|"]
        for entry in open_decisions():
            lines.append(f"| `{entry[0]}` | {entry[1]} |")
    else:
        lines.append("열린 결정 원장에 OPEN 항목이 없다.")
    lines += ["", f"결함 원문과 재현 코드는 `reports/GO2_DEFECT_LEDGER.md` 에 있다.", ""]
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    write_csv(buffer)
    OUT_CSV.write_text(buffer.getvalue(), encoding="utf-8", newline="")
    OUT_DOC.write_text(document(), encoding="utf-8", newline="")
    print(OUT_CSV.relative_to(ROOT).as_posix())
    print(OUT_DOC.relative_to(ROOT).as_posix())
    print(f"결함 {len(ledger.DEFECTS)}건, 결함 대장 결정 {len(awaiting_user())}건, "
          f"열린 결정 원장 {len(open_decisions())}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
