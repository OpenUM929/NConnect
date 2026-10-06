"""G-A060 PC2 분석 자료 계약 테스트 — 회수본이 있을 때 낙상 수·축 점수가 원자료와 맞는지 확인한다.

python -B -m unittest tools.test_go2_g_a060_pc2_analysis
"""
import csv
import json
import unittest
from pathlib import Path

import go2_g_a060_pc2_analysis as ana

OUT = ana.OUT


@unittest.skipUnless(all((ana.SRC / f).is_dir() for _, _, f in ana.ARMS), "G-A060 회수 압축 해제본 없음")
class G060Analysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rc = ana.main()

    def test_fall_counts_match_summary(self) -> None:
        self.assertEqual(self.rc, 0)
        rows = list(csv.DictReader((OUT / "rough_lateral_events/EVENTS_COUNT_CHECK.csv").open(encoding="utf-8")))
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(r["match"] == "True" for r in rows))

    def test_axis_totals_complete_and_b1_matches_readout(self) -> None:
        rows = {r["arm"]: r for r in csv.DictReader((OUT / "AXIS_SCORES.csv").open(encoding="utf-8"))}
        for r in rows.values():
            float(r["total_70"])  # '미측정'이면 실패
        readout = json.loads((ana.ROOT / "workspace/training/quadruped/reports/evidence/go2_pc2_point_readout/"
                              "ang_vel_xy_l2_m0p08.json").read_text(encoding="utf-8"))
        b1 = [readout["target"]["seeds"][s]["b1"] for s in ("101", "202", "303")]
        cases = {(r["arm"], r["case"]): r for r in csv.DictReader((OUT / "CASE_METRICS.csv").open(encoding="utf-8"))}
        self.assertEqual(int(cases[("PC2_B1", "rough_lateral")]["falls"]), sum(b1))


if __name__ == "__main__":
    unittest.main()
