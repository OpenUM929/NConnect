"""PM 보고 문서가 손으로 쓰이지 않았는지, 그리고 셈이 대장과 맞는지 검사한다.

2026-09-19: PM 이 사용자에게 직접 하는 말에만 관문이 없었고, 그 자리에서 D-0 중계 오류가 났다.
이 문서는 그 말을 관문 안으로 들이기 위한 것이므로, 문서 자체가 손으로 고쳐지면 목적이 사라진다.
"""
from __future__ import annotations

import csv
import unittest
from pathlib import Path

from tools import go2_defect_ledger as ledger
from tools import go2_pm_brief as brief
from tools import go2_open_decisions as decisions

ROOT = Path(__file__).resolve().parents[1]


class PmBriefContractTest(unittest.TestCase):
    def test_1_document_is_exactly_what_the_generator_makes(self) -> None:
        self.assertEqual(brief.OUT_DOC.read_text(encoding="utf-8"), brief.document(),
                         "GO2_PM_BRIEF.md 이 생성기 출력과 다르다 — 손으로 고치지 마라")

    def test_2_every_number_in_the_document_is_a_cell_in_the_evidence(self) -> None:
        """주장 검사는 칸 전체만 근거로 받는다 — 표의 수가 CSV 칸과 같아야 한다."""
        with brief.OUT_CSV.open(encoding="utf-8", newline="") as handle:
            cells = {cell for row in csv.reader(handle) for cell in row}
        for key, value in brief.tally():
            with self.subTest(key):
                self.assertIn(value, cells)

    def test_3_the_counts_match_the_ledger(self) -> None:
        """PM 이 따로 세지 않는다 — 대장이 유일한 출처다."""
        counts = dict(brief.tally())
        self.assertEqual(int(counts["defects_total"]), len(ledger.DEFECTS))
        self.assertEqual(
            int(counts["status_OPEN"]) + int(counts["status_FIXED"]) + int(counts["status_ACCEPTED"]),
            len(ledger.DEFECTS), "상태 합이 전체와 다르다")
        self.assertEqual(int(counts["severity_중대"]) + int(counts["severity_경미"]),
                         len(ledger.DEFECTS), "심각도 합이 전체와 다르다")
        self.assertEqual(int(counts["confidence_확인"]) + int(counts["confidence_추정"]),
                         len(ledger.DEFECTS), "확신도 합이 전체와 다르다")

    def test_4_a_closed_defect_names_the_gate_that_keeps_it_closed(self) -> None:
        """관문 없이 닫은 결함은 '고쳤다'가 아니라 '고쳤다고 적었다'이다."""
        for defect_id, gate in brief.gates():
            with self.subTest(defect_id):
                self.assertNotEqual(gate, "(관문 없음)",
                                    f"{defect_id}: 닫혔는데 그것을 지키는 계약 테스트가 없다")
                for name in gate.split(" · "):
                    self.assertTrue((ROOT / name).is_file(), f"{defect_id}: {name} 이 없다")

    def test_5_blocking_reasons_are_not_confused_with_user_decisions(self) -> None:
        """차단 사유는 R-6 위반 · 테스트 실패 · 회수 불가 셋뿐이다.

        2026-09-19 결함 PM-1: 차단 사유가 아닌 항목을 '사용자 결정 대기'로 돌리고 작업을 멈췄다.
        문서가 그 구분을 적고 있는지 본다.
        """
        text = brief.OUT_DOC.read_text(encoding="utf-8")
        self.assertIn("R-6 위반", text)
        self.assertIn("회수 불가", text)
        self.assertIn("사전등록", text)

    def test_6_pending_decisions_are_open_defects(self) -> None:
        for d in brief.awaiting_user():
            with self.subTest(d["id"]):
                self.assertEqual(d["status"], "OPEN", "닫힌 결함을 결정 대기로 내걸지 않는다")

    def test_7_open_decision_registry_is_not_silently_omitted(self) -> None:
        open_ids = {row[0] for row in decisions.DECISIONS if row[8] == "OPEN"}
        self.assertEqual({row[0] for row in brief.open_decisions()}, open_ids)
        doc = brief.document()
        with brief.OUT_CSV.open(encoding="utf-8", newline="") as handle:
            csv_ids = {row[1] for row in csv.reader(handle)
                       if len(row) == 3 and row[0] == "open_decision"}
        self.assertEqual(csv_ids, open_ids)
        for decision_id in open_ids:
            with self.subTest(decision_id):
                self.assertIn(decision_id, doc)


if __name__ == "__main__":
    unittest.main()
