import unittest
from tools.build_go2_calibration_sensitivity import build_sensitivity


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        self.comparison = {"evidence": "INTERNAL_MEASUREMENT_OK", "scenarios": [
            {"scenario": "G5", "weight": .15, "baseline_points": 0., "candidate_points": 0.},
            {"scenario": "G4", "weight": .15, "baseline_points": 6., "candidate_points": 5.}]}
        self.calibration = {"totals": {"observed_ratio_official_over_internal": .87},
                            "comparison_eligibility": {"status": "UNCONFIRMED"}}

    def test_separate_non_decision_output_preserves_zero_and_regression(self):
        result = build_sensitivity(self.comparison, self.calibration)
        self.assertFalse(result["validated_prediction"])
        self.assertFalse(result["used_for_decisions"])
        self.assertFalse(result["raw_gates_changed"])
        self.assertEqual(result["scenarios"][0]["sensitivity_candidate"], 0)
        self.assertAlmostEqual(result["totals"]["sensitivity_delta"], -.87)
        self.assertEqual(self.comparison["scenarios"][1]["candidate_points"], 5.)

    def test_invalid_measurement_rejected(self):
        self.comparison["evidence"] = "INTERNAL_MEASUREMENT_INCOMPLETE"
        with self.assertRaises(ValueError):
            build_sensitivity(self.comparison, self.calibration)

    def test_nonfinite_rejected(self):
        self.calibration["totals"]["observed_ratio_official_over_internal"] = float("nan")
        with self.assertRaises(ValueError):
            build_sensitivity(self.comparison, self.calibration)


if __name__ == "__main__":
    unittest.main()
