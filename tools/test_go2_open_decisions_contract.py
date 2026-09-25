"""열린 결정 관문 — `[모름]` 이 하류에서 사실로 바뀌지 않는가.

2026-09-18: `GO2_REWARD_MECHANISM_FORECAST.md` 는 R-6 해석이 사용자 결정임을 적어 두었는데,
그 해석에 기대는 산출물 9곳이 전부 단정형으로 옮겨 적었다.  산문의 `[모름]` 은 파일을 건너가지
못한다 — 그래서 이 관문이 **원장의 결정 번호가 의존 산출물마다 글자로 박혀 있는지** 검사한다.
번호가 없으면 그 파일을 읽는 역할은 우리가 스스로 넓힌 규칙을 기성 사실로 읽게 된다.

    python -B -m unittest tools.test_go2_open_decisions_contract
"""
from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_open_decisions as reg  # noqa: E402


class OpenDecisionsContractTest(unittest.TestCase):
    def test_1_csv_and_doc_are_regenerated(self) -> None:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerows(reg.rows())
        self.assertEqual(reg.OUT_CSV.read_text(encoding="utf-8"), buffer.getvalue(),
                         "DECISIONS.csv 가 현행 생성기 결과가 아니다 —"
                         " python -B tools/go2_open_decisions.py 를 다시 돌려라")
        self.assertEqual(reg.OUT_DOC.read_text(encoding="utf-8"), reg.document(reg.rows()))

    def test_2_the_line_that_calls_it_a_user_decision_still_exists(self) -> None:
        """'이건 사용자 결정이다'라고 적어 둔 원문이 사라지면 그 결정은 흔적 없이 기성 사실이 된다."""
        for entry in reg.DECISIONS:
            did, source, literal = entry[0], entry[5], entry[6]
            with self.subTest(did):
                path = ROOT / source if (ROOT / source).is_file() else reg.QUAD / source
                self.assertTrue(path.is_file(), f"{did}: 원문 {source} 가 없다")
                self.assertIn(literal, path.read_text(encoding="utf-8"),
                              f"{did}: {source} 에서 '{literal}' 이 사라졌다")

    def test_3_every_dependent_artifact_carries_the_decision_id(self) -> None:
        """그 해석에 기대는 파일은 결정 번호를 글자로 달고 있어야 한다.

        이것이 이 관문의 전부다.  번호가 박혀 있으면, 그 파일만 읽고 들어온 역할도
        '이건 우리가 정한 것이고 아직 승인되지 않았다'를 함께 읽는다."""
        for entry in reg.DECISIONS:
            did, status, dependents = entry[0], entry[8], entry[7]
            if status != "OPEN":
                continue
            for dependent in dependents.split(";"):
                with self.subTest(decision=did, file=dependent):
                    path = ROOT / dependent
                    if not path.is_file():
                        path = reg.QUAD / dependent
                    self.assertTrue(path.is_file(), f"{did}: 의존 산출물 {dependent} 가 없다")
                    self.assertIn(did, path.read_text(encoding="utf-8"),
                                  f"{did}: {dependent} 가 이 해석에 기대면서 결정 번호를 적지 않았다"
                                  " — 이 파일만 읽는 역할은 우리가 넓힌 규칙을 기성 사실로 읽는다")

    def test_4_a_widening_reading_may_not_be_silently_settled(self) -> None:
        """권한을 넓히는 해석은 `OPEN` 인 동안 `change_class` 를 하나 지정해야 한다 —
        그래야 사양 관문(`test_15_...`)이 그 분류의 추천을 잡아낼 수 있다."""
        for entry in reg.DECISIONS:
            did, direction, change_class, status = entry[0], entry[3], entry[4], entry[8]
            if direction != "WIDENS" or status != "OPEN":
                continue
            with self.subTest(did):
                self.assertTrue(change_class,
                                f"{did}: 권한을 넓히는 열린 결정인데 어떤 change_class 를"
                                " 허용하는지 적지 않았다 — 사양 관문이 걸 고리가 없다")
        self.assertTrue(reg.by_change_class(), "열린 결정이 사양 관문에 아무 고리도 주지 않는다")

    def test_5_the_ledger_only_grows(self) -> None:
        self.assertGreaterEqual(len(reg.DECISIONS), 2,
                                "2026-09-18 에 기록한 열린 결정 2건보다 줄었다 — 결정은 지우지 않는다")
        self.assertEqual(len({entry[0] for entry in reg.DECISIONS}), len(reg.DECISIONS),
                         "결정 번호가 겹친다")


if __name__ == "__main__":
    unittest.main()
