"""회수한 회차가 정본 원장 밖에 있으면 떨어지는 관문 (결함 C-25).

`GO2_NOW.md` 의 원장 우선 규칙(G-D-LEDGER-FIRST-20260918)은 "회차·곡선·수치는 `reports/runs/`
에서 읽는다" 고 정한다.  그런데 그 폴더는 **생성물**이라 회수가 끝날 때마다 다시 만들어야 하고,
다시 만들지 않아도 아무것도 붉어지지 않았다.  2026-09-24 A044 회수 뒤 실제로 그렇게 됐다 —
생성기는 돌았지만 출력이 `workspace/server_returns/G-A044/generated_runs/` 안에만 남았고,
정본 `reports/runs/LEDGER.csv` 는 seq 26(A038)에서 멈춰 A041·A042·A043·A044 **네 회차**가
빠진 채였다.  다음 회차를 원장에서 고르는 규칙이 걸려 있는데 원장이 네 회차만큼 과거였다.

그래서 이 관문은 "최신인가" 를 묻지 않고 **다시 만들어서 대조한다**: 지금 산출물에서 생성기를
한 번 더 돌린 결과가 디스크의 정본과 한 바이트라도 다르면 실패다.  고치는 법은 한 줄이다:

    python -B tools/build_go2_run_reports.py

이 관문은 성능을 판정하지 않는다.  원장이 산출물을 따라왔는지만 본다.
"""

from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_go2_run_reports as reports  # noqa: E402

FIX = "python -B tools/build_go2_run_reports.py 를 돌려 정본을 산출물에 맞춘다"


def csv_text(rows: list[list[str]]) -> str:
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerows(rows)
    return buffer.getvalue()


class RunLedgerFreshnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = reports.harvest()
        cls.out = reports.OUT

    def read(self, name: str) -> str:
        """디스크의 글자 그대로.  줄끝은 생성기가 쓴 대로 둔다 — csv 는 CRLF, 보고서는 OS 기본."""
        path = self.out / name
        self.assertTrue(path.is_file(), f"{name} 가 없다 — {FIX}")
        return path.read_bytes().decode("utf-8")

    def test_1_every_recovered_harvest_is_in_the_ledger(self) -> None:
        """생성기가 찾은 회차는 전부 정본 LEDGER.csv 에 있어야 한다."""
        rows = list(csv.DictReader(io.StringIO(self.read("LEDGER.csv"))))
        listed = {row["run"] for row in rows}
        missing = sorted({record["run"] for record in self.records} - listed)
        self.assertEqual(missing, [], f"회수했는데 원장에 없는 회차: {missing} — {FIX}")

    def test_2_the_ledger_rebuilds_byte_for_byte(self) -> None:
        expected = csv_text([list(reports.CSV_COLUMNS)] + reports.csv_rows(self.records))
        self.assertEqual(self.read("LEDGER.csv"), expected, f"LEDGER.csv 가 산출물과 다르다 — {FIX}")

    def test_3_the_other_generated_tables_rebuild_too(self) -> None:
        for name, rows in (("SCENARIO_SCORES.csv", reports.scenario_rows(self.records)),
                           ("ARM_DELTAS.csv", reports.delta_rows(self.records)),
                           ("TERRAIN_AT_PIN.csv", reports.terrain_rows(self.records))):
            with self.subTest(table=name):
                self.assertEqual(self.read(name), csv_text(rows), f"{name} 가 산출물과 다르다 — {FIX}")

    def test_4_one_page_per_run_and_no_stale_page(self) -> None:
        expected = {f"{i:02d}_{record['run']}.md": reports.render(i, record)
                    for i, record in enumerate(self.records, 1)}
        expected["INDEX.md"] = reports.index_page(self.records)
        expected["CHRONOLOGY.md"] = reports.chronology_page(self.records)
        on_disk = {path.name for path in self.out.glob("*.md")}
        self.assertEqual(sorted(on_disk), sorted(expected), f"회차 보고서 목록이 다르다 — {FIX}")
        for name, text in expected.items():
            with self.subTest(page=name):
                # 보고서는 write_text 가 쓴 것이라 OS 줄끝이다.  내용만 본다.
                self.assertEqual(self.read(name).replace("\r\n", "\n"), text,
                                 f"{name} 가 산출물과 다르다 — {FIX}")


if __name__ == "__main__":
    unittest.main()
