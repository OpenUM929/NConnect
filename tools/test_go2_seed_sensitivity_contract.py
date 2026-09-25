"""seed 흔들림 판독 관문 — 보고서가 원자료에서 다시 만들어지고, 핵심 사실이 고정돼 있다."""
from __future__ import annotations

import csv
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_seed_sensitivity as seed  # noqa: E402


def rows(name: str) -> list[dict[str, str]]:
    with (seed.OUT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@unittest.skipUnless(seed.BASE.is_dir(), "_keep G-A033 not present")
class SeedSensitivityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before = {p.name: p.read_bytes() for p in seed.OUT.glob("*.csv")}
        cls.report_before = seed.REPORT.read_bytes()
        with redirect_stdout(io.StringIO()):
            seed.main()

    def test_1_regeneration_is_byte_identical(self) -> None:
        self.assertEqual({p.name: p.read_bytes() for p in seed.OUT.glob("*.csv")}, self.before)
        self.assertEqual(seed.REPORT.read_bytes(), self.report_before)

    def test_2_same_seed_repeats_are_identical(self) -> None:
        for row in rows("SAME_SEED_REPEAT.csv"):
            self.assertEqual(row["identical"], "True", row["first"])

    def test_3_training_seed_noise_is_not_invented(self) -> None:
        text = seed.REPORT.read_text(encoding="utf-8")
        self.assertIn("**측정된 적 없음**", text)
        for header in rows("ONE_CHANGE_DRIFT.csv")[0]:
            self.assertNotIn("seed_sd", header)

    def test_4_g_a038_drift_is_the_readout(self) -> None:
        drift = {r["to"]: r for r in rows("ONE_CHANGE_DRIFT.csv")}
        row = drift["G-A038"]
        self.assertEqual((row["climb10_ge1_from"], row["climb10_ge1_to"]), ("90", "5"))
        self.assertEqual((row["climb10_ge2_from"], row["climb10_ge2_to"]), ("43", "0"))
        self.assertEqual(row["margin_to"], "+0.0728")
        self.assertLess(float(row["terrain_delta"]), -1.0)

    def test_5_band_and_headroom(self) -> None:
        band = {r["run"]: r for r in rows("BAND_RUNS.csv")}
        self.assertEqual(band["Pilot-01"]["walked"], "True")
        self.assertEqual(band["A018"]["walked"], "False")
        head = {r["term"]: float(r["edge_over_value"]) for r in rows("TERM_HEADROOM.csv")}
        self.assertLess(head["track_lin_vel_xy_exp"], 1.0)
        self.assertLess(head["dof_acc_l2"], head["ang_vel_xy_l2"])

    def test_6_eval_seed_spread_is_widest_on_the_10cm_climb(self) -> None:
        spread = sorted(rows("EVAL_SEED_SPREAD.csv"), key=lambda r: -int(r["spread"]))
        self.assertEqual(spread[0]["case"], "stairs_10_down")
        self.assertEqual(len({r["case"] for r in spread}), len(spread))


if __name__ == "__main__":
    unittest.main()
