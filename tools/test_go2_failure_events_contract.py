"""관문: 험지 옆걸음 낙상 직전 사건표(tools/go2_failure_events.py, 2026-09-28).

저장된 증거만 읽는다(도구를 다시 돌리지 않는다 — 9개 steps.csv 를 읽는 데 약 1분).
    python -B -m unittest tools/test_go2_failure_events_contract.py
"""
from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_failure_events as tool  # noqa: E402

EV = ROOT / "workspace/training/quadruped/reports/evidence/go2_failure_data_20260928"
REPORT = ROOT / "workspace/training/quadruped/reports/GO2_FAILURE_DATA_FINDINGS_20260928.md"


def rows(name: str) -> list[dict]:
    with (EV / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class FailureEventsContract(unittest.TestCase):
    def test_1_counts_match_fall_channels(self):
        check = rows("EVENTS_COUNT_CHECK.csv")
        self.assertEqual(len(check), 9)
        self.assertTrue(all(r["fall_channels_csv_match"] == "True" for r in check))

    def test_2_one_row_per_robot_and_fall_totals(self):
        ev = rows("EVENTS.csv")
        self.assertEqual(len(ev), 3 * 3 * 32)
        falls = {a: sum(1 for r in ev if r["arm"] == a and r["outcome"] == "FALL") for a in ("G-A048", "G-A033", "G-A038")}
        self.assertEqual(falls, {"G-A048": 16, "G-A033": 59, "G-A038": 18})

    def test_3_missing_channels_are_declared_not_invented(self):
        status = {r["channel"]: r["status"] for r in rows("CHANNEL_AVAILABILITY.csv")}
        for key in ("roll/pitch rate", "foot contact", "air time", "policy action", "per-term reward"):
            hit = [s for c, s in status.items() if key in c]
            self.assertEqual(hit, ["NOT_STORED"], key)
        header = json.loads((EV / "PROVENANCE.json").read_text(encoding="utf-8"))["steps_csv_header"]
        for col in rows("EVENTS.csv")[0]:
            self.assertFalse(col.startswith(("contact", "foot", "air_time", "action", "rew_")), col)
        self.assertNotIn("actual_wx", header)

    def test_4_evidence_folder_has_no_fake_channel_files(self):
        self.assertEqual(sorted(p.name for p in EV.iterdir()),
                         sorted(["CANDIDATE_COMPARISON.csv", "CHANNEL_AVAILABILITY.csv", "EVENTS.csv",
                                 "EVENTS_COUNT_CHECK.csv", "FAMILY_SUMMARY.csv", "PROVENANCE.json"]))

    def test_5_report_family_counts_match_summary(self):
        fam = {(r["arm"], r["family"]): int(r["n"]) for r in rows("FAMILY_SUMMARY.csv")}
        self.assertEqual((fam[("G-A048", "tilt_early")], fam[("G-A048", "tilt_mid_late")], fam[("G-A048", "height_first")]),
                         (4, 7, 5))
        text = REPORT.read_text(encoding="utf-8")
        for phrase in ("시작 직후 전복 4대", "중·후반 전복 7대", "낮은 자세로 가라앉음 5대", "A048 11/11"):
            self.assertIn(phrase, text)
        self.assertTrue(text.split("\n## 0. 예선 기준 현재 위치", 1)[0].count("\n") < 6)

    def test_6_yaw_is_not_a_precursor_in_a048(self):
        a048 = [r for r in rows("EVENTS.csv") if r["arm"] == "G-A048" and r["event_order"] == "tilt_first"]
        self.assertEqual(len(a048), 11)
        self.assertTrue(all(r["yaw_vs_tilt_order"] == "tilt_first" for r in a048))

    def test_7_tool_writes_only_its_evidence_folder(self):
        self.assertEqual(tool.OUT, EV)
        src = (ROOT / "tools/go2_failure_events.py").read_text(encoding="utf-8")
        writes = [line for line in src.splitlines() if "write_text(" in line or "write_csv(OUT" in line]
        self.assertTrue(writes)
        self.assertTrue(all("OUT /" in line or "def write_csv" in line or "path.open" in line for line in writes), writes)


if __name__ == "__main__":
    unittest.main()
