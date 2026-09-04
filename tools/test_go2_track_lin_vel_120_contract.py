"""Contract tests for the Go2 G-A009 single-variable package."""

from __future__ import annotations

import difflib
import importlib.util
import json
import sys
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


builder = load_module(
    "go2_track_lin_builder", ROOT / "tools" / "build_go2_track_lin_vel_120_package.py"
)
reporter = load_module("go2_tiered_report", GO2 / "go2_tiered_eval_report.py")


class Go2TrackLinVel120Contract(unittest.TestCase):
    def test_reward_change_is_exactly_track_linear_1_to_1_2(self) -> None:
        default = builder.reward_source(builder.DEFAULT_REWARDS).decode("utf-8")
        candidate = builder.reward_source(builder.CANDIDATE_REWARDS).decode("utf-8")
        changes = [
            line
            for line in difflib.ndiff(default.splitlines(), candidate.splitlines())
            if line.startswith(("- ", "+ "))
        ]
        self.assertEqual(
            changes,
            [
                '-     "track_lin_vel_xy_exp": 1.0,    # 추천 0.5 ~ 2.0',
                '+     "track_lin_vel_xy_exp": 1.2,    # 추천 0.5 ~ 2.0',
            ],
        )

    def test_tier_registries_have_7_and_21_cases(self) -> None:
        tier1 = json.loads(builder.registry_payload(1))
        representative = json.loads(builder.registry_payload(3))
        tier1_count = sum(
            len(item["internal_cases"])
            * (1 if item["id"] == "G7" else len(tier1["score"]["internal_gates"]["required_evaluation_seeds"]))
            for item in tier1["scenarios"]
        )
        rep_count = sum(
            len(item["internal_cases"])
            * (1 if item["id"] == "G7" else len(representative["score"]["internal_gates"]["required_evaluation_seeds"]))
            for item in representative["scenarios"]
        )
        self.assertEqual(tier1_count, 7)
        self.assertEqual(rep_count, 21)

    def test_frozen_baseline_g5_uses_per_env_velocity_integral(self) -> None:
        payload = builder.baseline_payload()
        summary = json.loads(
            payload["baseline_seed/cases/seed_101/stairs_15_up/summary.json"]
        )
        self.assertEqual(
            summary["projected_progress_method"],
            "median_per_env_body_velocity_integral_v2",
        )
        self.assertGreaterEqual(summary["projected_progress_m"], 0.0)
        self.assertLess(summary["projected_progress_m"], 10.0)
        self.assertIn("projected_progress_original_invalid", summary)

    def test_runner_has_distinct_dr_and_cost_gate(self) -> None:
        raw = (GO2 / "server_run_go2_track_lin_vel_120_v1.sh").read_bytes()
        text = raw.decode("utf-8")
        self.assertNotIn(b"\r\n", raw)
        self.assertIn("DR_MODE=1", text)
        self.assertIn('run_env+=("NCRC_EVAL_DR=1")', text)
        self.assertIn("INTERNAL_EARLY_KILL_PASS", text)
        self.assertIn("finish_full \"$TIER1_STATUS\" 7", text)
        self.assertIn("run_candidate_representatives 202", text)
        self.assertIn("run_candidate_representatives 303", text)
        self.assertIn("TELEMETRY_CANDIDATE=%s", text)
        self.assertIn("VIDEOS_CANDIDATE=1", text)
        self.assertNotIn("TELEMETRY_CANDIDATE=69", text)

    def test_tier1_and_representative_decisions_are_strict(self) -> None:
        def policy(points: float, g1: float = 0.8, gate: str = "INTERNAL_SCENARIO_PASS") -> dict:
            scenarios = {
                f"G{i}": {
                    "scenario_proxy": g1 if i == 1 else 0.8,
                    "survival_proxy": 1.0,
                    "tracking_proxy": 0.8,
                    "gate": gate,
                }
                for i in range(1, 8)
            }
            return {
                "simulation_points_70": points,
                "scenarios": scenarios,
                "seed_fractions": {"101": 0.8, "202": 0.8, "303": 0.8},
            }

        early = reporter.tier1_decision(policy(20.0, g1=0.01), policy(30.0, g1=0.20))
        self.assertEqual(early["status"], "INTERNAL_EARLY_KILL_PASS")
        representative = reporter.representative_decision(policy(60.0))
        self.assertEqual(
            representative["status"], "INTERNAL_REPRESENTATIVE_PROMOTION_PASS"
        )
        representative = reporter.representative_decision(policy(59.99))
        self.assertEqual(
            representative["status"], "INTERNAL_REPRESENTATIVE_PROMOTION_FAIL"
        )

    def test_built_package_manifest_and_structure(self) -> None:
        builder.build()
        with zipfile.ZipFile(builder.OUTPUT) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertTrue(all(name.startswith("go2_track_lin_vel_120_v1/") for name in names))
            self.assertIn("go2_track_lin_vel_120_v1/default/model_best.pt", names)
            self.assertIn("go2_track_lin_vel_120_v1/candidate/quadruped_rewards.py", names)
            self.assertIn("go2_track_lin_vel_120_v1/go2_tier1_registry.json", names)
            self.assertIn("go2_track_lin_vel_120_v1/go2_representative_registry.json", names)
            manifest = archive.read(
                "go2_track_lin_vel_120_v1/PACKAGE_SHA256SUMS.txt"
            ).decode("utf-8")
            self.assertEqual(len(manifest.splitlines()), len(names) - 1)


if __name__ == "__main__":
    unittest.main()
