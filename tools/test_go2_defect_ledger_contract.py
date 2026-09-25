"""결함 대장이 대장 노릇을 하는지 검사한다.

2026-09-19 사용자 질문("확인을 요청할 때마다 왜 문제가 터지느냐")의 뿌리는 결함이 아니라
**결함을 적어두는 곳이 없다**는 것이었다.  그래서 `tools/go2_defect_ledger.py` 를 만들었는데,
대장 자체가 손으로 고쳐지거나 역할 파일이 대장을 가리키지 않으면 같은 실패가 되풀이된다.

규칙을 문서에 적는 것은 준수가 아니다 — 이 파일이 그 규칙의 관문이다.
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tools import go2_defect_ledger as ledger

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / ".claude/agents/go2-auditor.md"


class DefectLedgerContractTest(unittest.TestCase):
    def test_1_document_is_exactly_what_the_generator_makes(self) -> None:
        """손으로 고친 대장은 대장이 아니다.  기록은 생성기 한 곳에만 있다."""
        self.assertEqual(ledger.OUT_DOC.read_text(encoding="utf-8"), ledger.document(),
                         f"{ledger.OUT_DOC.name} 이 생성기 출력과 다르다 — "
                         "문서를 손으로 고치지 말고 DEFECTS 를 고친 뒤 생성기를 다시 돌려라")

    def test_2_every_defect_has_an_origin_fix(self) -> None:
        """'어디서 고치나'가 없으면 다음 감사자가 같은 것을 다시 찾는다."""
        for d in ledger.DEFECTS:
            with self.subTest(d["id"]):
                self.assertTrue(d["origin_fix"].strip(), f"{d['id']}: origin_fix 가 비었다")
                self.assertTrue(d["where"].strip(), f"{d['id']}: where 가 비었다")
                self.assertTrue(d["source_checked"].strip(), f"{d['id']}: 확인한 원본이 비었다")

    def test_3_closed_defects_say_how_they_were_closed(self) -> None:
        """FIXED·ACCEPTED 로 바꾸면서 근거를 안 적으면 조용히 지운 것과 같다."""
        for d in ledger.DEFECTS:
            if d["status"] in ("FIXED", "ACCEPTED"):
                with self.subTest(d["id"]):
                    self.assertTrue(d["resolution"].strip(),
                                    f"{d['id']}: {d['status']} 인데 resolution 이 비었다")

    def test_3b_confirmed_defects_actually_reproduce(self) -> None:
        """`확인` 결함의 `repro` 를 **실제로 돌려** `repro_expect` 가 나오는지 본다.

        2026-09-19 침투 시험: `repro` 가 산문이던 판에서는 "아무 말이나 적어도 된다"를 넣고
        `확인`이라 주장해도 이 관문이 통과했다. 자칭 딱지는 관문이 아니다.

        OPEN 결함이면 결함이 아직 있음을, FIXED 결함이면 고침이 아직 자리에 있음을 보인다 —
        닫힌 결함의 회귀 관문을 겸한다.
        """
        for d in ledger.DEFECTS:
            with self.subTest(d["id"]):
                confidence = ledger.field(d, "confidence")
                self.assertIn(confidence, ledger.CONFIDENCE)
                if confidence != "확인":
                    continue
                repro, expect = ledger.field(d, "repro"), ledger.field(d, "repro_expect")
                self.assertTrue(repro.strip(), f"{d['id']}: 확인이라면서 재현 코드가 없다")
                self.assertTrue(expect.strip(), f"{d['id']}: 확인이라면서 기대 출력이 없다")
                got = subprocess.run([sys.executable, "-B", "-c", repro], cwd=ROOT,
                                     capture_output=True, timeout=180,
                                     env={**os.environ, "PYTHONIOENCODING": "utf-8"})
                # 관문이 오류 조립에서 죽으면 관문이 아니다 — 디코딩 실패도 그냥 글자로 받는다.
                out = (got.stdout or b"").decode("utf-8", "replace")
                err = (got.stderr or b"").decode("utf-8", "replace")
                self.assertEqual(got.returncode, 0,
                                 f"{d['id']}: 재현 코드가 실패했다\n{err[:400]}")
                self.assertIn(expect, out,
                              f"{d['id']}: 재현 결과에 기대 출력이 없다\n{out[:400]}")
                # 침투 시험 B(2026-09-19): `print('통과')` + expect '통과' 는 돌아가고 통과했다.
                # 기대 문자열이 코드 안에 글자 그대로 있으면 그 코드는 저장소에서 아무것도 읽지
                # 않은 것이다 — 자기가 적은 답을 자기가 출력한 것뿐이다.  참 재현은 값을 파일에서
                # 끌어오므로 기대 문자열이 코드에 나타나지 않는다(현재 7건 모두 그렇다).
                # 이것은 **증명이 아니라 장벽**이다: `print('통'+'과')` 같은 우회는 여전히 가능하다.
                self.assertNotIn(expect, repro,
                                 f"{d['id']}: 기대 출력이 재현 코드 안에 그대로 있다 — "
                                 "저장소에서 값을 읽어 오게 고쳐라")

    def test_3c_the_relay_error_keeps_the_finders_own_words(self) -> None:
        """중계 오류를 기록하면서 원문을 안 실으면 다음에 또 내 말만 남는다."""
        by_id = {d["id"]: d for d in ledger.DEFECTS}
        self.assertIn("D-0", by_id)
        verbatim = ledger.field(by_id["D-0"], "verbatim")
        self.assertTrue(verbatim.strip(), "D-0 에 감사자 원문이 없다")
        self.assertIn("test_2", verbatim,
                      "감사자가 test_2 를 이미 적었다는 사실이 원문에 남아 있어야 한다")
        self.assertIn("[모름]", verbatim, "감사자가 결론을 [모름] 으로 표시한 사실이 남아 있어야 한다")

    def test_4_status_values_are_known(self) -> None:
        for d in ledger.DEFECTS:
            with self.subTest(d["id"]):
                self.assertIn(d["status"], ("OPEN", "FIXED", "ACCEPTED"))
                self.assertIn(d["severity"], ("중대", "경미"))

    def test_5_ids_are_unique(self) -> None:
        ids = [d["id"] for d in ledger.DEFECTS]
        self.assertEqual(len(ids), len(set(ids)), "결함 ID 가 겹치면 상태 갱신이 엉킨다")

    def test_6_cited_figures_are_their_own_cells_in_the_evidence_csv(self) -> None:
        """주장 검사(`go2_claim_check.own_values`)는 CSV 의 **칸 전체**만 근거로 받는다.

        산문 칸 안에 박힌 숫자는 근거가 되지 못하므로 `FIGURES` 로 한 칸씩 다시 낸다.
        이 검사가 없으면 대장이 늘어날수록 근거 없는 숫자가 조용히 늘어난다.
        """
        with ledger.OUT_CSV.open(encoding="utf-8", newline="") as handle:
            cells = {cell.lstrip("+-") for row in csv.reader(handle) for cell in row}
        for defect_id, figure, means in ledger.FIGURES:
            with self.subTest(f"{defect_id}:{figure}"):
                self.assertIn(figure.lstrip("+-"), cells,
                              f"{figure} 가 CSV 의 독립 칸이 아니다")
                self.assertTrue(means.strip(), f"{defect_id}:{figure} 에 뜻이 안 적혀 있다")

    def test_7_every_figure_belongs_to_a_real_defect(self) -> None:
        known = {d["id"] for d in ledger.DEFECTS}
        for defect_id, figure, _means in ledger.FIGURES:
            with self.subTest(f"{defect_id}:{figure}"):
                self.assertIn(defect_id, known)

    def test_8_the_auditor_role_file_points_at_this_ledger(self) -> None:
        """규칙을 역할 파일에 적어두고 관문을 안 걸면 다음 감사자가 다시 대화로만 보고한다."""
        text = AUDITOR.read_text(encoding="utf-8")
        self.assertIn("tools/go2_defect_ledger.py", text,
                      "감사자 역할 파일이 대장 생성기를 가리키지 않는다")
        self.assertIn(ledger.OUT_DOC.relative_to(ROOT / "workspace/training/quadruped").as_posix(),
                      text.replace("\\", "/"),
                      "감사자 역할 파일이 대장 문서를 가리키지 않는다")


if __name__ == "__main__":
    unittest.main()
