"""참고 자료 나침반 관문 — 자료가 실제로 있고, 왜 있는지 적혀 있고, 성격이 분류돼 있는가.

2026-09-18: 받아 둔 Isaac Lab 원문이 scratchpad 에만 있어 검증할 수 없었고, 추천은 원장을 읽지 않고
나왔다.  나침반은 "무엇이 있고 왜 있는가"를 코드로 유지하기 위한 것이므로, 다음을 검사한다.
  - 나침반이 재생성 결과와 바이트가 같은가 (손으로 고치지 않았는가)
  - 목록의 모든 경로가 실제로 존재하는가
  - 존재 이유가 비어 있는 자료가 없는가 (`WHY_MISSING`)
  - 데이터 표가 **측정 / 예측 / 이득구간** 중 하나로 분류돼 있는가 (`UNCLASSIFIED` 금지)
  - 원장·증거의 CSV 가 하나도 빠지지 않았는가
  - 감사자 역할 문서가 가리키는 경로가 실제로 있는가

    python -B -m unittest tools.test_go2_reference_compass_contract
"""
from __future__ import annotations

import csv
import io
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_reference_compass as compass  # noqa: E402

AUDITOR = ROOT / ".claude/agents/go2-auditor.md"


def table() -> list[dict[str, str]]:
    with compass.OUT_CSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class ReferenceCompassTest(unittest.TestCase):
    def test_1_is_regenerated_not_hand_edited(self) -> None:
        rows = compass.rows()
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerows(rows)
        self.assertEqual(compass.OUT_CSV.read_text(encoding="utf-8"), buffer.getvalue(),
                         "COMPASS.csv 가 재생성 결과와 다르다 — python -B tools/go2_reference_compass.py")
        self.assertEqual(compass.OUT_DOC.read_text(encoding="utf-8"), compass.document(rows),
                         "나침반 문서가 재생성 결과와 다르다")

    def test_2_every_listed_path_exists(self) -> None:
        missing = [r["path"] for r in table() if r["exists"] != "YES"]
        self.assertEqual(missing, [], "나침반이 가리키는 자료가 없다")
        for row in table():
            with self.subTest(row["path"]):
                self.assertTrue((ROOT / row["path"]).exists())

    def test_3_every_material_records_why_it_exists(self) -> None:
        nowhy = [r["path"] for r in table() if r["why_as_recorded"] == "WHY_MISSING"]
        self.assertEqual(nowhy, [], "존재 이유를 스스로 적지 않은 자료가 있다 — 나침반이 아니라 그 파일을 고친다")

    def test_4_every_table_is_measured_forecast_or_limit(self) -> None:
        """측정·예측·이득구간을 섞지 않기 위한 분류.  새 CSV 는 생성기에 등록돼야 한다."""
        unclassified = [r["path"] for r in table() if r["kind"] == "UNCLASSIFIED"]
        self.assertEqual(unclassified, [], "성격이 분류되지 않은 표가 있다")
        kinds = {r["path"].rsplit("/", 1)[-1]: r["kind"] for r in table()}
        for name in compass.FORECAST_FILES:
            if name in kinds:
                self.assertEqual(kinds[name], "예측", name)
        for name in compass.LIMIT_FILES:
            if name in kinds:
                self.assertEqual(kinds[name], "이득구간", name)
        counts = {kind: sum(1 for r in table() if r["kind"] == kind) for kind in ("측정", "예측", "이득구간")}
        for kind, count in counts.items():
            self.assertGreater(count, 0, f"{kind} 표가 하나도 없다")

    def test_5_no_ledger_or_evidence_table_is_left_out(self) -> None:
        listed = {r["path"] for r in table()}
        for path in sorted(compass.RUNS.glob("*.csv")) + sorted(compass.EVIDENCE.rglob("*.csv")):
            with self.subTest(path.name):
                self.assertIn(path.relative_to(ROOT).as_posix(), listed, "나침반에 빠진 표가 있다")

    def test_6_the_auditor_role_points_at_files_that_exist(self) -> None:
        """감사자가 '읽어라'라고 지시받은 자료가 실제로 있어야 한다."""
        text = AUDITOR.read_text(encoding="utf-8")
        cited = {m for m in re.findall(r"`([A-Za-z0-9_./-]+\.(?:md|csv|json|py))`", text)}
        self.assertGreater(len(cited), 15, "감사자 문서가 자료를 거의 가리키지 않는다")
        roots = (ROOT, ROOT / "workspace/training/quadruped", ROOT / "workspace/training/quadruped/reports",
                 ROOT / "tools", compass.EVIDENCE, compass.RUNS)
        for name in sorted(cited):
            if name.endswith("*.json") or "*" in name:
                continue
            with self.subTest(name):
                self.assertTrue(any((base / name).exists() for base in roots)
                                or any(p.name == name.rsplit("/", 1)[-1]
                                       for p in ROOT.rglob(name.rsplit("/", 1)[-1])),
                                f"감사자 문서가 없는 파일을 가리킨다: {name}")

    def test_7_the_compass_is_reachable_from_the_rules(self) -> None:
        now = (ROOT / "GO2_NOW.md").read_text(encoding="utf-8")
        self.assertIn("GO2_REFERENCE_COMPASS.md", now + AUDITOR.read_text(encoding="utf-8"),
                      "나침반을 가리키는 포인터가 규칙 문서에 없다")


if __name__ == "__main__":
    unittest.main()
