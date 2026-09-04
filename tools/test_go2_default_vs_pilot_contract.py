"""Static and pure-Python contract tests for the Go2 one-file workflow."""

from __future__ import annotations

import importlib.util
import difflib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(GO2))
spec = importlib.util.spec_from_file_location("go2_report", GO2 / "go2_fixed_eval_report.py")
report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(report)
builder_spec = importlib.util.spec_from_file_location("go2_builder", ROOT / "tools" / "build_go2_default_vs_pilot_package.py")
builder = importlib.util.module_from_spec(builder_spec)
assert builder_spec.loader is not None
builder_spec.loader.exec_module(builder)


class Go2WorkflowContract(unittest.TestCase):
    def test_runner_is_one_upload_one_command_one_result_zip(self) -> None:
        raw = (GO2 / "server_run_go2_default_vs_pilot_v1.sh").read_bytes()
        text = raw.decode("utf-8")
        self.assertNotIn(b"\r\n", raw)
        self.assertIn("GO2_DEFAULT_VS_PILOT_RESULT.zip", text)
        self.assertIn("--max_iterations 1000", text)
        self.assertIn("--num_envs 4096", text)
        self.assertIn("--seed 42", text)
        self.assertNotIn("--resume", text)
        self.assertIn("TELEMETRY_PER_POLICY=69", text)
        self.assertIn("VIDEOS_PER_POLICY=7", text)
        self.assertNotIn("server_run_Go2_videos.sh", text)

    def test_resume_preserves_pilot_checkpoint_and_packages_without_bare_python(self) -> None:
        text = (GO2 / "server_run_go2_default_vs_pilot_v1.sh").read_text(encoding="utf-8")
        self.assertIn('PILOT_MODEL="$KEEP/training/pilot_model_best.pt"', text)
        self.assertIn('cp -a "$PILOT_ROOT/exported/model_best.pt" "$PILOT_MODEL"', text)
        self.assertLess(text.index('PILOT_MODEL="$KEEP/training/pilot_model_best.pt"'), text.index("run_policy default"))
        self.assertIn('/workspace/IsaacLab/isaaclab.sh -p "$PACKAGE_ROOT/package_go2_result.py"', text)
        self.assertNotIn('python3 "$PACKAGE_ROOT/package_go2_result.py"', text)

    def test_registry_contract_is_69_per_policy(self) -> None:
        registry = json.loads((GO2 / "config" / "go2_self_eval_registry.json").read_text(encoding="utf-8"))
        g1_g6 = sum(len(item["internal_cases"]) for item in registry["scenarios"] if item["id"] != "G7")
        g7 = sum(len(item["internal_cases"]) for item in registry["scenarios"] if item["id"] == "G7")
        self.assertEqual(g1_g6 * 3 + g7, 69)
        self.assertAlmostEqual(sum(item["weight"] for item in registry["scenarios"]), 1.0)
        runner = (GO2 / "server_run_go2_default_vs_pilot_v1.sh").read_text(encoding="utf-8")
        for scenario in registry["scenarios"]:
            for case_id in scenario["internal_cases"]:
                if scenario["id"] == "G7":
                    self.assertIn("dr_seed_${seed}", runner)
                else:
                    self.assertIn(case_id, runner)

    def test_default_staging_changes_only_four_pilot_lines(self) -> None:
        pilot = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
        default = builder.default_reward_source().decode("utf-8")
        self.assertEqual(builder.reward_dict(default), builder.DEFAULT_REWARDS)
        changes = [line for line in difflib.ndiff(pilot.splitlines(), default.splitlines()) if line.startswith(("- ", "+ "))]
        self.assertEqual(len(changes), 8)  # four removed + four added; action_rate is unchanged.

    def test_paired_decisions(self) -> None:
        base = {
            "status": "INTERNAL_GATE_PASS", "simulation_fraction": 0.75,
            "seed_fractions": {"101": 0.75, "202": 0.74, "303": 0.76},
            "failed_scenarios": [],
            "scenarios": {"G1": {"survival_proxy": 0.96, "tracking_proxy": 0.80, "scenario_proxy": 0.77}},
        }
        pilot = {
            "status": "INTERNAL_GATE_PASS", "simulation_fraction": 0.80,
            "seed_fractions": {"101": 0.80, "202": 0.79, "303": 0.81},
            "failed_scenarios": [],
            "scenarios": {"G1": {"survival_proxy": 0.96, "tracking_proxy": 0.84, "scenario_proxy": 0.81}},
        }
        self.assertEqual(report.paired(base, pilot)["decision"], "PILOT_COMBINATION_PROMISING_VIDEO_REVIEW_PENDING")
        self.assertEqual(report.paired(pilot, base)["decision"], "RESTART_FROM_DEFAULT_CONFIRMED")

    def test_missing_telemetry_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "cases").mkdir()
            result = report.build_policy(root, GO2 / "config" / "go2_self_eval_registry.json")
            self.assertEqual(result["status"], "SELF_ASSESSMENT_INCOMPLETE")
            self.assertEqual(result["expected_telemetry_count"], 69)


if __name__ == "__main__":
    unittest.main()
