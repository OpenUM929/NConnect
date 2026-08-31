"""Contract tests for the fixed-policy evaluation package."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workspace" / "training" / "humanoid" / "eval_telemetry.py"
spec = importlib.util.spec_from_file_location("eval_telemetry", MODULE_PATH)
telemetry = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(telemetry)

REPORT_MODULE_PATH = ROOT / "workspace" / "training" / "humanoid" / "fixed_eval_report.py"
report_spec = importlib.util.spec_from_file_location("fixed_eval_report", REPORT_MODULE_PATH)
fixed_report = importlib.util.module_from_spec(report_spec)
assert report_spec.loader is not None
report_spec.loader.exec_module(fixed_report)


class _Manager:
    active_terms = ["time_out", "base_contact"]

    def __init__(self) -> None:
        self.values = {
            "time_out": torch.tensor([False, True]),
            "base_contact": torch.tensor([True, False]),
        }

    def get_term(self, name: str) -> torch.Tensor:
        return self.values[name]


class _Commands:
    def get_command(self, name: str) -> torch.Tensor:
        assert name == "base_velocity"
        return torch.tensor([[0.5, 0.0, 0.5], [0.5, 0.0, 0.5]])


class _Data:
    root_lin_vel_b = torch.tensor([[0.4, 0.0, 0.0], [0.6, 0.0, 0.0]])
    root_ang_vel_b = torch.tensor([[0.0, 0.0, 0.4], [0.0, 0.0, 0.6]])
    root_pos_w = torch.tensor([[1.0, 2.0, 1.1], [2.0, 3.0, 1.2]])


class _Robot:
    data = _Data()


class _Env:
    num_envs = 2
    step_dt = 0.02
    termination_manager = _Manager()
    command_manager = _Commands()
    scene = {"robot": _Robot()}

    @property
    def unwrapped(self):
        return self


class FixedEvalContractTest(unittest.TestCase):
    def test_collector_writes_raw_rows_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            collector = telemetry.TelemetryCollector(Path(temp), max_steps=10)
            env = _Env()
            collector.attach(env)
            result = ({}, torch.zeros(2), torch.tensor([True, False]),
                      torch.tensor([False, True]), {})
            collector.record(env, result)
            collector.close(completed=True)

            rows = (Path(temp) / "steps.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 3)
            summary = json.loads((Path(temp) / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["steps"], 1)
            self.assertEqual(summary["rows"], 2)
            self.assertEqual(summary["early_terminations"], 1)
            self.assertEqual(summary["timeouts"], 1)
            self.assertAlmostEqual(summary["survival_rate_completed"], 0.5)
            self.assertAlmostEqual(summary["tracking_xy_mae"], 0.1, places=6)
            self.assertAlmostEqual(summary["tracking_yaw_mae"], 0.1, places=6)

    def test_play_has_opt_in_hook(self) -> None:
        play = (MODULE_PATH.parent / "play.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("NCRC_EVAL_OUT")', play)
        self.assertIn("_install_eval_telemetry()", play)

    def test_server_runner_is_evaluation_only_and_pins_run06(self) -> None:
        runner_path = MODULE_PATH.parent / "server_run06_fixed_eval.sh"
        raw = runner_path.read_bytes()
        runner = raw.decode("utf-8")
        self.assertNotIn(b"\r\n", raw)
        self.assertIn(
            "8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636",
            runner,
        )
        self.assertNotIn("--max_iterations", runner)
        self.assertNotIn(" -p train.py", runner)
        self.assertNotIn("python3 fixed_eval_report.py", runner)
        self.assertIn("isaaclab.sh -p fixed_eval_report.py", runner)
        for scenario in (
            "H1_stand", "H2_forward", "H3_left", "H3_right",
            "H4_left", "H4_right", "H5_rough",
            "H6_plus10", "H6_minus10", "H7_push",
        ):
            self.assertIn(f"run_case {scenario}", runner)

    def test_self_score_requires_all_seven_scenarios(self) -> None:
        cases = {
            name: {
                "survival_rate_completed": 1.0,
                "tracking_xy_rmse": 0.1,
                "tracking_yaw_rmse": 0.1,
            }
            for name in (
                "H1_stand", "H2_forward", "H3_left", "H3_right",
                "H4_left", "H4_right", "H5_rough",
                "H6_plus10", "H6_minus10", "H7_push",
            )
        }
        score = fixed_report.build_self_score(cases, {"recovery_rate_observed": 1.0})
        self.assertEqual(score["status"], "SELF_ASSESSMENT_PASS")
        self.assertEqual(len(score["scenarios"]), 7)
        self.assertGreater(score["simulation_points_70"], 49.0)

        del cases["H5_rough"]
        score = fixed_report.build_self_score(cases, {"recovery_rate_observed": 1.0})
        self.assertEqual(score["status"], "SELF_ASSESSMENT_INCOMPLETE")
        self.assertIn("H5", score["missing_scenarios"])

    def test_self_score_fails_low_survival_or_tracking(self) -> None:
        cases = {
            name: {
                "survival_rate_completed": 1.0,
                "tracking_xy_rmse": 0.1,
                "tracking_yaw_rmse": 0.1,
            }
            for name in (
                "H1_stand", "H2_forward", "H3_left", "H3_right",
                "H4_left", "H4_right", "H5_rough",
                "H6_plus10", "H6_minus10", "H7_push",
            )
        }
        cases["H5_rough"]["survival_rate_completed"] = 0.5
        score = fixed_report.build_self_score(cases, {"recovery_rate_observed": 1.0})
        self.assertEqual(score["status"], "SELF_ASSESSMENT_FAIL")
        self.assertEqual(score["scenarios"]["H5"]["gate"], "INTERNAL_SCENARIO_FAIL")

    def test_h7_counts_missed_pushes_against_recovery(self) -> None:
        case = {
            "survival_rate_completed": 1.0,
            "tracking_xy_rmse": 0.0,
            "tracking_yaw_rmse": 0.0,
        }
        proxy = fixed_report._case_proxy(
            "H7", case,
            {"expected_env_events": 128, "recovered_events": 114, "recovery_rate_observed": 1.0},
        )
        self.assertAlmostEqual(proxy["tracking_proxy"], 114 / 128)

    def test_staged_model_is_exact_run06_checkpoint(self) -> None:
        import hashlib

        model = MODULE_PATH.parent / "_eval_run06" / "model_best.pt"
        digest = hashlib.sha256(model.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636",
        )

    def test_package_builder_has_no_training_entrypoint(self) -> None:
        builder = (ROOT / "tools" / "build_run06_fixed_eval_package.py").read_text(encoding="utf-8")
        self.assertNotIn('HUMANOID / "train.py"', builder)
        self.assertIn('HUMANOID / "_eval_run06" / "model_best.pt"', builder)


if __name__ == "__main__":
    unittest.main()
