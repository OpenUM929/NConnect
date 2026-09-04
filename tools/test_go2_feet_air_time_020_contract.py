"""Static and pure-Python contract tests for the Go2 single-variable workflow."""

from __future__ import annotations

import ast
import difflib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(GO2))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("go2_feet_builder", ROOT / "tools" / "build_go2_feet_air_time_020_package.py")
reporter = load_module("go2_feet_report", GO2 / "go2_single_variable_report.py")
telemetry = load_module("go2_eval_telemetry_contract", GO2 / "go2_eval_telemetry.py")


class Go2FeetAirTimeContract(unittest.TestCase):
    def test_reward_change_is_exactly_one_variable(self) -> None:
        default = builder.reward_source(builder.DEFAULT_REWARDS).decode("utf-8")
        candidate = builder.reward_source(builder.CANDIDATE_REWARDS).decode("utf-8")
        changes = [line for line in difflib.ndiff(default.splitlines(), candidate.splitlines()) if line.startswith(("- ", "+ "))]
        self.assertEqual(changes, [
            '-     "feet_air_time":        0.01,    # 추천 0.01 ~ 0.5',
            '+     "feet_air_time":        0.2,    # 추천 0.01 ~ 0.5',
        ])
        self.assertEqual(builder.reward_dict(default), builder.DEFAULT_REWARDS)
        self.assertEqual(builder.reward_dict(candidate), builder.CANDIDATE_REWARDS)

    def test_frozen_baseline_report_is_complete_and_identified(self) -> None:
        baseline = json.loads(builder.baseline_report())
        self.assertEqual(baseline["observed_telemetry_count"], 69)
        self.assertEqual(baseline["identity"]["model_sha256"], builder.BASELINE_MODEL_SHA)
        self.assertEqual(baseline["identity"]["env_sha256"], builder.BASELINE_ENV_SHA)

    def test_runner_contract(self) -> None:
        raw = (GO2 / "server_run_go2_feet_air_time_020_v1.sh").read_bytes()
        text = raw.decode("utf-8")
        self.assertNotIn(b"\r\n", raw)
        self.assertIn("--max_iterations 1000", text)
        self.assertIn("--num_envs 4096", text)
        self.assertIn("--seed 42", text)
        self.assertNotIn("--resume", text)
        self.assertIn("TELEMETRY_CANDIDATE=69", text)
        self.assertIn("VIDEOS_CANDIDATE=7", text)
        self.assertIn("GO2_FEET_AIR_TIME_020_RESULT.zip", text)
        self.assertIn("GO2_FEET_AIR_TIME_020_RESULT_READY", text)
        self.assertNotIn("server_run_Go2_videos.sh", text)
        self.assertIn("CASE_ATTEMPTS=${GO2_CASE_ATTEMPTS:-3}", text)
        self.assertIn("launcher.snapshot.log", text)
        self.assertIn("EVALUATOR_TERMINATION=GRACEFUL", text)
        self.assertIn("GO2_RECOVERY_ONLY", text)
        self.assertIn("recovery-only mode refuses retraining", text)

    def test_telemetry_uses_graceful_app_stop_instead_of_hard_exit(self) -> None:
        source = (GO2 / "go2_eval_telemetry.py").read_text(encoding="utf-8")
        hard_exit_calls = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr == "_exit"
        ]
        self.assertEqual(hard_exit_calls, [])

        class FakeApp:
            def is_running(self) -> bool:
                return True

        class FakeLauncher:
            def __init__(self) -> None:
                self.app = FakeApp()

        with tempfile.TemporaryDirectory() as directory:
            collector = telemetry.Collector(Path(directory), max_steps=10)
            telemetry._install_graceful_stop(FakeLauncher, collector)
            launcher = FakeLauncher()
            self.assertTrue(launcher.app.is_running())
            collector.step = collector.max_steps
            collector.closed = True
            self.assertFalse(launcher.app.is_running())

    def test_built_package_manifest_and_structure(self) -> None:
        builder.build()
        with zipfile.ZipFile(builder.OUTPUT) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertGreater(len(names), 21)
            self.assertTrue(all(name.startswith("go2_feet_air_time_020_v1/") for name in names))
            self.assertIn(
                "go2_feet_air_time_020_v1/baseline_DEFAULT_SELF_EVAL_REPORT.json", names
            )
            self.assertIn(
                "go2_feet_air_time_020_v1/candidate/quadruped_rewards.py", names
            )
            self.assertIn(
                "go2_feet_air_time_020_v1/GO2_FEET_AIR_TIME_020_V2_README.txt", names
            )
            self.assertIn(
                "go2_feet_air_time_020_v1/recovery_seed/training/model_best.pt", names
            )
            manifest = archive.read("go2_feet_air_time_020_v1/PACKAGE_SHA256SUMS.txt").decode("utf-8")
            self.assertEqual(len(manifest.splitlines()), len(names) - 1)
            self.assertIn("candidate/quadruped_rewards.py", manifest)
            self.assertIn("server_run_go2_feet_air_time_020_v1.sh", manifest)

    def test_quantitative_pass_requires_all_pre_registered_gates(self) -> None:
        def policy(model_sha: str, g5_delta: float = 0.0) -> dict:
            scenarios = {
                f"G{i}": {"survival_proxy": 0.98, "tracking_proxy": 0.80, "scenario_proxy": 0.78}
                for i in range(1, 8)
            }
            scenarios["G5"]["scenario_proxy"] += g5_delta
            return {
                "identity": {"model_sha256": model_sha, "env_sha256": reporter.BASELINE_ENV_SHA},
                "observed_telemetry_count": 69,
                "expected_telemetry_count": 69,
                "scenarios": scenarios,
                "seed_fractions": {"101": 0.75, "202": 0.75, "303": 0.75},
                "simulation_fraction": 0.75,
                "simulation_points_70": 52.5,
            }

        baseline = policy(reporter.BASELINE_MODEL_SHA)
        candidate = policy("candidate", g5_delta=0.031)
        candidate["simulation_fraction"] = 0.781
        candidate["simulation_points_70"] = 54.67
        result = reporter.compare(baseline, candidate)
        self.assertEqual(result["quantitative_status"], "INTERNAL_SCREEN_QUANTITATIVE_PASS_VIDEO_REVIEW_PENDING")
        candidate["scenarios"]["G3"]["survival_proxy"] = 0.90
        self.assertEqual(reporter.compare(baseline, candidate)["quantitative_status"], "INTERNAL_SCREEN_FAIL")


if __name__ == "__main__":
    unittest.main()
