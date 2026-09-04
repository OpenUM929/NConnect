"""Contract tests for independent multi-seed Run06 validation."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUMANOID = ROOT / "workspace" / "training" / "humanoid"
MODULE = HUMANOID / "independent_eval_report.py"
sys.path.insert(0, str(HUMANOID))
spec = importlib.util.spec_from_file_location("independent_eval_report", MODULE)
independent = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(independent)


def seed_report(proxy: float = 0.9, status: str = "SELF_ASSESSMENT_PASS") -> dict:
    scenarios = {
        name: {
            "survival_proxy": 1.0,
            "tracking_proxy": proxy,
            "scenario_proxy": proxy,
        }
        for name in independent.fixed_eval_report.SCENARIO_WEIGHTS
    }
    return {"self_assessment": {"status": status, "scenarios": scenarios}}


class IndependentEvalContractTest(unittest.TestCase):
    def test_runner_is_evaluation_only_and_uses_predeclared_seeds(self) -> None:
        path = HUMANOID / "server_run06_independent_eval.sh"
        raw = path.read_bytes()
        runner = raw.decode("utf-8")
        self.assertNotIn(b"\r\n", raw)
        self.assertIn("SEEDS=(101 202 303)", runner)
        self.assertIn('"agent.seed=$seed"', runner)
        self.assertNotIn("--max_iterations", runner)
        self.assertNotIn(" -p train.py", runner)
        for scenario in (
            "H1_stand", "H2_forward", "H3_left", "H3_right",
            "H4_left", "H4_right", "H5_rough",
            "H6_plus10", "H6_minus10", "H7_push",
        ):
            self.assertIn(f'"$seed" {scenario}', runner)

    def test_three_passing_seeds_pass_by_worst_scenario(self) -> None:
        reports = {seed: seed_report(0.9) for seed in independent.EXPECTED_SEEDS}
        result = independent.build_validation(reports)
        self.assertEqual(result["status"], "INDEPENDENT_VALIDATION_PASS")
        self.assertAlmostEqual(result["simulation_points_70"], 63.0)

    def test_missing_seed_is_incomplete(self) -> None:
        reports = {101: seed_report(), 202: seed_report()}
        result = independent.build_validation(reports)
        self.assertEqual(result["status"], "INDEPENDENT_VALIDATION_INCOMPLETE")
        self.assertEqual(result["missing_seeds"], [303])

    def test_one_failed_seed_fails_validation(self) -> None:
        reports = {seed: seed_report() for seed in independent.EXPECTED_SEEDS}
        reports[202] = seed_report(status="SELF_ASSESSMENT_FAIL")
        result = independent.build_validation(reports)
        self.assertEqual(result["status"], "INDEPENDENT_VALIDATION_FAIL")
        self.assertEqual(result["failed_seeds"], [202])

    def test_worst_seed_scenario_controls_aggregate(self) -> None:
        reports = {seed: seed_report() for seed in independent.EXPECTED_SEEDS}
        reports[303]["self_assessment"]["scenarios"]["H7"].update(
            survival_proxy=0.8, tracking_proxy=0.9, scenario_proxy=0.72
        )
        result = independent.build_validation(reports)
        self.assertEqual(result["scenarios"]["H7"]["gate"], "INDEPENDENT_SCENARIO_FAIL")
        self.assertEqual(result["status"], "INDEPENDENT_VALIDATION_FAIL")


if __name__ == "__main__":
    unittest.main()
