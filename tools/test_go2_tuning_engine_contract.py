"""Contracts for the reusable Go2 tuning engine and the G-A016 specification."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
SPEC = GO2 / "config" / "experiments" / "G_A016_pilot_ang_vel_xy_m015.json"
RETIRED_SPEC = GO2 / "config" / "experiments" / "G_A015_pilot_feet_air_time_035.json"
ENGINE_DIR = "go2_tuning_engine_v1_3"
sys.path.insert(0, str(GO2))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Go2TuningEngineContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_module("go2_tuning_config", GO2 / "go2_tuning_config.py")
        cls.report = load_module("go2_tuning_report", GO2 / "go2_tuning_eval_report.py")
        cls.builder = load_module(
            "go2_tuning_builder", ROOT / "tools" / "build_go2_tuning_engine.py"
        )
        cls.experiment = cls.config.load_and_validate(SPEC)

    def test_flat_orientation_is_an_active_reward_key_not_a_comment(self) -> None:
        weights = self.config.reward_dict(
            (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
        )
        self.assertIn("flat_orientation_l2", weights)
        self.assertIn("flat_orientation_l2", self.config.REWARD_NAMES)
        self.assertEqual(self.config.DEFAULT_REWARDS["flat_orientation_l2"], 0.0)

    def test_g_a016_is_exactly_one_reward_change(self) -> None:
        experiment = self.experiment
        self.assertEqual(experiment["work_id"], "G-A016")
        self.assertEqual(experiment["single_change"], {
            "name": "ang_vel_xy_l2", "from": -0.05, "to": -0.15
        })
        changed = [
            name for name, baseline in experiment["rewards"]["baseline"].items()
            if experiment["rewards"]["candidate"][name] != baseline
        ]
        self.assertEqual(changed, ["ang_vel_xy_l2"])

    def test_g_a016_keeps_feet_air_time_at_the_measured_ceiling(self) -> None:
        # G-A015 measured feet_air_time 0.35 as a collapse (-30.12/70), so 0.20
        # stays pinned on both arms; it is not the variable under test any more.
        for arm in ("baseline", "candidate"):
            self.assertEqual(self.experiment["rewards"][arm]["feet_air_time"], 0.2)

    def test_the_retired_g_a015_spec_still_validates(self) -> None:
        retired = self.config.load_and_validate(RETIRED_SPEC)
        self.assertEqual(retired["work_id"], "G-A015")

    def test_invalid_second_reward_change_is_rejected(self) -> None:
        invalid = json.loads(json.dumps(self.experiment))
        invalid["rewards"]["candidate"]["lin_vel_z_l2"] = -1.5
        with self.assertRaisesRegex(ValueError, "exactly one reward"):
            self.config.validate_experiment(invalid)

    def test_gate_requires_a_positive_total_points_delta(self) -> None:
        gates = self.experiment["evaluation"]["gates"]
        self.assertNotIn("target_scenario", gates)
        self.assertGreater(gates["min_total_points_delta"], 0.0)
        missing = json.loads(json.dumps(self.experiment))
        missing["evaluation"]["gates"].pop("min_total_points_delta")
        with self.assertRaisesRegex(ValueError, "min_total_points_delta"):
            self.config.validate_experiment(missing)
        nonpositive = json.loads(json.dumps(self.experiment))
        nonpositive["evaluation"]["gates"]["min_total_points_delta"] = 0.0
        with self.assertRaisesRegex(ValueError, "must be positive"):
            self.config.validate_experiment(nonpositive)

    def test_optional_target_scenario_must_still_be_canonical(self) -> None:
        invalid = json.loads(json.dumps(self.experiment))
        invalid["evaluation"]["gates"]["target_scenario"] = "G9"
        invalid["evaluation"]["gates"]["target_min_proxy_delta"] = 0.05
        with self.assertRaisesRegex(ValueError, "target scenario"):
            self.config.validate_experiment(invalid)

    def test_materialized_sources_use_default_and_candidate_values(self) -> None:
        template = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
        default = self.config.render_reward_source(
            template, self.experiment["rewards"]["baseline"]
        )
        candidate = self.config.render_reward_source(
            template, self.experiment["rewards"]["candidate"]
        )
        self.assertEqual(self.config.reward_dict(default)["ang_vel_xy_l2"], -0.05)
        self.assertEqual(self.config.reward_dict(candidate)["ang_vel_xy_l2"], -0.15)
        for name in (
            "track_lin_vel_xy_exp",
            "feet_air_time",
            "lin_vel_z_l2",
            "action_rate_l2",
            "flat_orientation_l2",
        ):
            self.assertEqual(
                self.config.reward_dict(default)[name], self.config.reward_dict(candidate)[name]
            )

    def test_runtime_materialization_snapshots_experiment_and_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            self.config.materialize_runtime(
                engine_root=GO2,
                experiment_path=SPEC,
                runtime_root=runtime,
                source_root=GO2,
                baseline_root=self.builder.baseline_fixture_root(),
            )
            self.assertTrue((runtime / "candidate" / "train.py").is_file())
            self.assertTrue((runtime / "candidate" / "quadruped_rewards.py").is_file())
            self.assertTrue((runtime / "default" / "model_best.pt").is_file())
            self.assertTrue((runtime / "meta" / "experiment.json").is_file())
            self.assertTrue((runtime / "meta" / "experiment.sha256").is_file())
            self.assertEqual(
                len(json.loads((runtime / "tier1_registry.json").read_text(encoding="utf-8"))["scenarios"]),
                7,
            )

    def test_tier_gate_scores_the_weighted_total_not_one_scenario(self) -> None:
        def policy(points: float, survival: float = 1.0, scenario_proxy: float = 0.8) -> dict:
            return {
                "simulation_points_70": points,
                "scenarios": {
                    f"G{i}": {
                        "scenario_proxy": scenario_proxy,
                        "survival_proxy": survival,
                        "tracking_proxy": 0.8,
                        "gate": "INTERNAL_SCENARIO_PASS",
                    }
                    for i in range(1, 8)
                },
                "seed_fractions": {"101": 0.8, "202": 0.8, "303": 0.8},
            }

        gates = self.experiment["evaluation"]["gates"]
        threshold = gates["min_total_points_delta"]
        baseline = policy(20.0)

        passed = self.report.tier1_decision(baseline, policy(20.0 + threshold), gates)
        self.assertEqual(passed["status"], "INTERNAL_EARLY_KILL_PASS")
        self.assertEqual(passed["failure_reasons"], [])

        failed = self.report.tier1_decision(baseline, policy(20.0 + threshold / 2), gates)
        self.assertEqual(failed["status"], "INTERNAL_EARLY_KILL_FAIL")
        self.assertIn(
            f"total_points_70_delta_below_{threshold}", failed["failure_reasons"]
        )

    def test_survival_regression_still_kills_a_total_positive_candidate(self) -> None:
        """G-A013 shape: a candidate must not buy points by collapsing survival."""
        gates = self.experiment["evaluation"]["gates"]
        baseline = {
            "simulation_points_70": 20.0,
            "scenarios": {
                f"G{i}": {
                    "scenario_proxy": 0.8,
                    "survival_proxy": 1.0,
                    "tracking_proxy": 0.8,
                    "gate": "INTERNAL_SCENARIO_PASS",
                }
                for i in range(1, 8)
            },
            "seed_fractions": {"101": 0.8, "202": 0.8, "303": 0.8},
        }
        candidate = json.loads(json.dumps(baseline))
        candidate["simulation_points_70"] = 25.0
        candidate["scenarios"]["G4"]["survival_proxy"] = 1.0 - 0.3125
        decision = self.report.tier1_decision(baseline, candidate, gates)
        self.assertEqual(decision["status"], "INTERNAL_EARLY_KILL_FAIL")
        self.assertIn(
            f"G4_survival_regressed_over_{gates['max_survival_regression']}",
            decision["failure_reasons"],
        )

    def test_pinned_scenario_gate_no_longer_kills_a_net_positive(self) -> None:
        """Regression guard for the measured G-A010 and G-A011 mis-kills."""
        gates = self.experiment["evaluation"]["gates"]
        base_scenarios = {
            f"G{i}": {
                "scenario_proxy": 0.8,
                "survival_proxy": 1.0,
                "tracking_proxy": 0.8,
                "gate": "INTERNAL_SCENARIO_PASS",
            }
            for i in range(1, 8)
        }
        baseline = {
            "simulation_points_70": 17.537120722509602,
            "scenarios": json.loads(json.dumps(base_scenarios)),
            "seed_fractions": {"101": 0.8, "202": 0.8, "303": 0.8},
        }
        candidate = {
            "simulation_points_70": 19.794280652672406,
            "scenarios": json.loads(json.dumps(base_scenarios)),
            "seed_fractions": {"101": 0.8, "202": 0.8, "303": 0.8},
        }
        # G1 did not move at all, which is exactly what engine 1.1.0 killed G-A010 for.
        candidate["scenarios"]["G7"]["survival_proxy"] = 1.0 - 0.03125
        decision = self.report.tier1_decision(baseline, candidate, gates)
        self.assertEqual(decision["status"], "INTERNAL_EARLY_KILL_PASS")
        self.assertEqual(decision["failure_reasons"], [])
        self.assertEqual(decision["schema_version"], 3)

    def test_runner_is_generic_and_packages_one_result_zip(self) -> None:
        raw = (GO2 / "server_run_go2_tuning_engine_v1.sh").read_bytes()
        text = raw.decode("utf-8")
        self.assertNotIn(b"\r\n", raw)
        self.assertIn('EXPERIMENT_PATH=${1:-/workspace/experiment.json}', text)
        self.assertIn("go2_tuning_config.py", text)
        self.assertIn("ENGINE_ARCHIVE_SHA256", text)
        self.assertIn("EXPERIMENT_SHA256", text)
        self.assertIn("package_go2_result.py", text)
        self.assertNotIn("track_lin_vel_xy_exp=1.20-only", text)
        self.assertNotIn("PYTHON_BIN=${PYTHON_BIN:-python3}", text)
        self.assertIn("/workspace/IsaacLab/isaaclab.sh", text)
        self.assertIn("shell-env", text)
        self.assertIn('--experiment "$EXPERIMENT_PATH" --out "$ENV_FILE"', text)
        self.assertIn(f"/workspace/{ENGINE_DIR}", text)

    def test_engine_zip_does_not_embed_any_experiment_spec(self) -> None:
        self.builder.build()
        with zipfile.ZipFile(self.builder.OUTPUT) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertTrue(all(name.startswith(f"{ENGINE_DIR}/") for name in names))
            self.assertFalse(any(f"{ENGINE_DIR}/config/experiments/" in name for name in names))
            self.assertIn(f"{ENGINE_DIR}/config/go2_tuning_experiment_schema.json", names)
            manifest = archive.read(f"{ENGINE_DIR}/PACKAGE_SHA256SUMS.txt").decode("utf-8")
            self.assertEqual(len(manifest.splitlines()), len(names) - 1)

    def test_built_engine_is_self_contained_for_runtime_materialization(self) -> None:
        self.builder.build()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(self.builder.OUTPUT) as archive:
                archive.extractall(root)
            engine = root / ENGINE_DIR
            runtime = root / "runtime"
            self.config.materialize_runtime(
                engine_root=engine,
                experiment_path=SPEC,
                runtime_root=runtime,
            )
            self.assertTrue((runtime / "candidate" / "train.py").is_file())
            self.assertEqual(
                self.config.reward_dict(
                    (runtime / "candidate" / "quadruped_rewards.py").read_text(encoding="utf-8")
                )["ang_vel_xy_l2"],
                -0.15,
            )
            self.assertEqual(
                self.config.reward_dict(
                    (runtime / "default" / "quadruped_rewards.py").read_text(encoding="utf-8")
                )["ang_vel_xy_l2"],
                -0.05,
            )

    def test_measured_g_a015_collapse_is_killed_on_both_clauses(self) -> None:
        """Replay of the real G-A015 tier-1 measurement (-30.12/70)."""
        measured = {
            #        baseline (survival, tracking)   candidate (survival, tracking)
            "G1": ((1.0, 0.8932), (0.03125, 0.5561)),
            "G2": ((1.0, 0.9247), (1.0, 0.9122)),
            "G3": ((0.8125, 0.5967), (0.0, 0.4312)),
            "G4": ((1.0, 0.5533), (0.0, 0.4577)),
            "G5": ((0.71875, 0.5696), (0.0, 0.1888)),
            "G6": ((0.96875, 0.9712), (0.9375, 0.9481)),
            "G7": ((0.9375, 0.5975), (0.125, 0.4427)),
        }

        weights = {"G1": 0.15, "G2": 0.15, "G3": 0.20, "G4": 0.15,
                   "G5": 0.15, "G6": 0.10, "G7": 0.10}

        def policy(index: int) -> dict:
            scenarios = {}
            for name, arms in measured.items():
                survival, tracking = arms[index]
                scenarios[name] = {
                    "scenario_proxy": survival * tracking,
                    "survival_proxy": survival,
                    "tracking_proxy": tracking,
                    "gate": "INTERNAL_SCENARIO_PASS",
                }
            points = 70.0 * sum(
                weights[name] * item["scenario_proxy"]
                for name, item in scenarios.items()
            )
            return {
                "simulation_points_70": points,
                "scenarios": scenarios,
                "seed_fractions": {"101": 0.8, "202": 0.8, "303": 0.8},
            }

        baseline, candidate = policy(0), policy(1)
        # The tracking proxies above are the 4-decimal values printed in
        # SELF_EVAL_REPORT.md, so the replay lands within 0.01/70 of the run.
        self.assertAlmostEqual(baseline["simulation_points_70"], 46.4912, delta=0.01)
        self.assertAlmostEqual(candidate["simulation_points_70"], 16.3693, delta=0.01)

        decision = self.report.tier1_decision(
            baseline, candidate, self.experiment["evaluation"]["gates"]
        )
        self.assertEqual(decision["status"], "INTERNAL_EARLY_KILL_FAIL")
        self.assertLess(decision["candidate_minus_baseline_points_70"], -30.0)
        self.assertIn("total_points_70_delta_below_1.0", decision["failure_reasons"])
        self.assertIn("G4_survival_regressed_over_0.1", decision["failure_reasons"])


if __name__ == "__main__":
    unittest.main()
