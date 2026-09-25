"""Contract: the G-A038 readout is regenerated from the harvest and the report says what it shows.

Local only.  Run from the repository root:
    python -m unittest tools.test_go2_g_a038_readout_contract
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_g_a038_readout as readout  # noqa: E402

REPORT = readout.QUAD / "reports/GO2_G_A038_READOUT.md"
TEXT = REPORT.read_text(encoding="utf-8")
FILES = ("FINGERPRINT.csv", "TARGET_CASES.csv", "TARGET_SUMMARY.csv", "SENTINEL.csv",
         "STAIRS_10_CLIMB_TIMELINE.csv", "FLAT_NOMINAL.csv", "GUARD_BOUNDS.csv", "FORECAST_CHECK.csv",
         "CURRICULUM_LAG.csv", "REPORT_VALUES.csv")


def rows(name: str) -> list[dict[str, str]]:
    with (readout.OUT / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summary() -> dict[str, str]:
    return {r["item"]: r["value"] for r in rows("TARGET_SUMMARY.csv")}


class RegenerationTests(unittest.TestCase):
    def test_evidence_is_exactly_what_the_tool_writes(self) -> None:
        self.assertEqual(sorted(p.name for p in readout.OUT.iterdir()), sorted(FILES))
        original = readout.OUT
        with tempfile.TemporaryDirectory(dir=ROOT / "workspace") as tmp:
            readout.OUT = Path(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    readout.main()
            finally:
                readout.OUT = original
            for name in FILES:
                with self.subTest(name):
                    self.assertEqual((Path(tmp) / name).read_bytes(), (original / name).read_bytes())


class FingerprintTests(unittest.TestCase):
    def test_same_ruler_and_only_the_intended_change(self) -> None:
        checks = {r["check"]: r for r in rows("FINGERPRINT.csv")}
        measurement = [c for c in checks if c.split(":")[0] not in ("runner_rc", "runner_decision", "runner_stop")]
        for name in measurement:
            with self.subTest(name):
                self.assertEqual(checks[name]["ok"], "True")
        self.assertEqual(checks["env_reward:ang_vel_xy_l2"]["observed"], "-0.080000")
        self.assertEqual(checks["runner_rc"]["observed"], "1")
        self.assertIn("launcher.log:37492", checks["runner_stop"]["observed"])
        self.assertIn("launcher.log:37492", TEXT)
        for r in rows("SENTINEL.csv"):
            with self.subTest(r["case"]):
                self.assertEqual((r["survival_now"], r["tracking_now"]), (r["survival_stored"], r["tracking_stored"]))
                self.assertEqual(r["agrees"], "True")

    def test_the_verdict_of_record_is_inconclusive(self) -> None:
        verification = json.loads((readout.CAND / "harvest_verification.json").read_text(encoding="utf-8"))
        self.assertEqual(verification["verdict"], "INCONCLUSIVE")
        self.assertIn("**판정 없음(INCONCLUSIVE)**", TEXT)
        self.assertNotIn("FAIL 판정", TEXT)


class ReportNumberTests(unittest.TestCase):
    def test_target_stage_numbers(self) -> None:
        s = summary()
        self.assertEqual(s["criterion_1_passed"], "True")
        self.assertIn(f"+{float(s['target_mean_proxy_delta']):.3f}, {s['target_groups_improved']}개", TEXT)
        for group, shown in (("rough_lateral", "+0.356"), ("push_pos_x", "+0.049"), ("stairs_10_climb", "−0.140")):
            with self.subTest(group):
                value = float(s[f"group_mean_delta:{group}"])
                self.assertEqual(f"{value:+.3f}".replace("-", "−"), shown)
                self.assertIn(shown, TEXT)
        climb = [r for r in rows("TARGET_CASES.csv") if r["group"] == "stairs_10_climb"]
        self.assertEqual([r["posture_falls_g_a038"] for r in climb], ["32", "32", "32"])
        self.assertEqual([r["proxy_g_a038"] for r in climb], ["0.000000"] * 3)
        self.assertIn("4·15·15 → **32·32·32**", TEXT)

    def test_timeline_table(self) -> None:
        table = {(r["arm"], r["t_from_s"], r["seed"]): r for r in rows("STAIRS_10_CLIMB_TIMELINE.csv")}
        for t in ("4", "10", "18"):
            line = next(l for l in TEXT.splitlines() if l.startswith(f"| {t}~"))
            cells = [c.strip() for c in line.strip("|").split("|")[1:]]
            for cell, arm, key in ((cells[0], "G-A033", "upright_fraction"), (cells[1], "G-A038", "upright_fraction"),
                                   (cells[2], "G-A038", "height_rel_mean")):
                for shown, seed in zip(cell.split("·"), ("101", "202", "303")):
                    with self.subTest(t=t, arm=arm, key=key, seed=seed):
                        self.assertAlmostEqual(float(shown), float(table[(arm, t, seed)][key]), delta=0.00051)

    def test_guard_bounds_and_the_gap(self) -> None:
        guard = {r["scenario"]: r for r in rows("GUARD_BOUNDS.csv")}
        self.assertEqual(guard["G5"]["g_a038_scenario_proxy_upper_bound"], "0.000000")
        self.assertEqual(guard["G5"]["exceeds_limit"], "False")   # the collapse passes the G5 guard
        self.assertEqual(guard["G1"]["exceeds_limit"], "False")
        self.assertIn(f"손실은 **{float(guard['G5']['loss_lower_bound']):.3f}/70으로 한도 "
                      f"{float(guard['G5']['limit']):.3f} 안**", TEXT)
        self.assertIn(f"`stairs_15_down`@202 {float(guard['G5']['g_a033_scenario_proxy']):.4f}", TEXT)
        self.assertIn(f"`forward_fast`@101 {float(guard['G1']['g_a033_scenario_proxy']):.3f}", TEXT)
        self.assertIn(f"손실 하한은 {float(guard['G1']['loss_lower_bound']):.3f}", TEXT)
        self.assertIn("**전체 단계 판정은 모른다** [모름]", TEXT)

    def test_flat_case(self) -> None:
        flat = {r["arm"]: r for r in rows("FLAT_NOMINAL.csv")}
        for key, a, b in (("tracking_proxy", "0.949", "0.876"), ("speed_xy_mean", "0.736", "0.618"),
                          ("height_rel_mean", "0.358", "0.319")):
            with self.subTest(key):
                self.assertEqual((f"{float(flat['G-A033'][key]):.3f}", f"{float(flat['G-A038'][key]):.3f}"), (a, b))
                self.assertIn(f"{a} → {b}", TEXT)

    def test_forecast_directions(self) -> None:
        for r in rows("FORECAST_CHECK.csv"):
            with self.subTest(r["zone"]):
                self.assertEqual(r["direction_agrees"], "True")
                self.assertIn(r["forecast_partial_margin_delta"].replace("-", "−"), TEXT)
        self.assertIn("조합은 철회한다", TEXT)

    def test_curriculum_lag_is_printed_with_the_collapse(self) -> None:
        """2026-09-18: 두 팔을 같은 iter에서 읽었는데 커리큘럼 도달 레벨이 달랐다.  그 차이를 적지 않으면
        계단 붕괴가 레버 효과로만 읽힌다 — 값은 원장 TERRAIN_AT_PIN.csv 에서 온다."""
        table = {r["iteration"]: r for r in rows("CURRICULUM_LAG.csv")}
        pinned = [r for r in table.values() if r["is_eval_checkpoint"] == "True"]
        self.assertEqual(len(pinned), 1, "평가 고정 iter 는 하나다")
        row = pinned[0]
        self.assertEqual(row["iteration"], str(readout.SPEC["evaluation"]["checkpoint_iter"]))
        self.assertLess(float(row["delta"]), 0, "이 회차는 기준선보다 커리큘럼이 뒤처졌다")
        for value in (row["g_a033_terrain"], row["g_a038_terrain"], row["delta"].replace("-", "−")):
            self.assertIn(value, TEXT, f"판독 문서가 {value} 를 적지 않았다")
        ledger = (readout.QUAD / "reports/runs/TERRAIN_AT_PIN.csv").read_text(encoding="utf-8")
        for name, column in ((readout.BASE.name, "g_a033_terrain"), (readout.CAND.name, "g_a038_terrain")):
            self.assertIn(f"{name},{row['iteration']},{row[column]}", ledger)


if __name__ == "__main__":
    unittest.main()
