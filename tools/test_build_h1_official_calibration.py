import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_h1_official_calibration import build_calibration, render_markdown


class H1OfficialCalibrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_json(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def fixture(self, match_status="UNCONFIRMED"):
        weights = dict(H1=.15, H2=.20, H3=.10, H4=.10, H5=.15, H6=.15, H7=.15)
        proxies = dict(H1=.90, H2=.91, H3=.92, H4=.93, H5=.94, H6=.95, H7=.96)
        received = {key: proxies[key] * weight * 70 * .8 for key, weight in weights.items()}
        internal = {
            "independent_validation": {
                "simulation_points_70": sum(proxies[k] * weights[k] * 70 for k in weights),
                "scenarios": {
                    key: {"weight": weight, "worst_scenario_proxy": proxies[key]}
                    for key, weight in weights.items()
                },
            }
        }
        official = {
            "submission_identity": {"match_status": match_status, "reason": "fixture"},
            "scenarios": {
                key: {"received_points": received[key], "maximum_points": weight * 70}
                for key, weight in weights.items()
            },
            "total": {"received_points": sum(received.values()), "maximum_points": 70},
        }
        return self.write_json("internal.json", internal), self.write_json("official.json", official)

    def test_preserves_original_proxy_and_disables_single_observation_coefficients(self):
        internal, official = self.fixture()
        result = build_calibration(internal, official)
        self.assertFalse(result["calibration_review"]["original_proxy_changed"])
        self.assertFalse(result["calibration_review"]["coefficients_enabled_for_prediction"])
        self.assertFalse(result["calibration_review"]["validated_prediction"])
        self.assertEqual(result["comparison_eligibility"]["status"], "CONDITIONAL_ONLY_IDENTITY_UNCONFIRMED")
        self.assertTrue(math.isclose(result["totals"]["observed_ratio_official_over_internal"], .8))
        self.assertFalse(result["cross_robot_transfer"]["apply_h1_coefficients_to_go2"])
        self.assertIn("weakest_scenario_agrees", result["observed_precision_diagnostics"])
        self.assertEqual(result["evidence"]["current_posture_scope"]["posture_unmeasured_scenarios"], ["H5", "H6"])
        self.assertTrue(math.isclose(
            result["totals"]["adjusted_reference_points_global_ratio"],
            result["totals"]["official_points_transcribed"],
        ))
        self.assertIn("adjusted_reference_points_global_ratio", result["scenarios"]["H1"])

    def test_identity_match_changes_comparability_not_prediction_validation(self):
        internal, official = self.fixture("MATCHED")
        result = build_calibration(internal, official)
        self.assertEqual(result["comparison_eligibility"]["status"], "DIRECTLY_COMPARABLE")
        self.assertFalse(result["calibration_review"]["validated_prediction"])

    def test_rejects_weight_maximum_mismatch(self):
        internal, official = self.fixture()
        data = json.loads(official.read_text())
        data["scenarios"]["H1"]["maximum_points"] = 11
        official.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "weight-derived"):
            build_calibration(internal, official)

    def test_generated_markdown_keeps_calibration_disabled(self):
        internal, official = self.fixture()
        report = render_markdown(build_calibration(internal, official))
        self.assertIn("DISABLED / NOT VALIDATED", report)
        self.assertIn("not transferable Go2 score evidence", report)


if __name__ == "__main__":
    unittest.main()
