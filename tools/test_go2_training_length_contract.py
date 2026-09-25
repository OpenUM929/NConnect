"""Contract for the training-length package (G-A035).

This run is the first that changes no reward weight, so the usual guard
("exactly one reward differs") is inverted here: the two rendered reward files
must be byte-identical, and the only difference between the arms must be the
training length that run_config.env carries to the server.
"""
from __future__ import annotations

import copy
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "workspace" / "training" / "quadruped"))

import build_go2_training_length_package as build  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

WORK = "G-A035"
NOW = ROOT / "GO2_NOW.md"


def zip_members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()}


class TrainingLengthContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = build.load(WORK)
        cls.data = build.build_zip(cls.spec)
        cls.files = zip_members(cls.data)

    def test_1_no_reward_weight_moves(self) -> None:
        """The defining property of this run, checked on the shipped bytes."""
        candidate = self.files["candidate/quadruped_rewards.py"]
        reference = self.files["reference/baseline_quadruped_rewards.py"]
        self.assertEqual(candidate, reference, "candidate and reference reward files must be identical")
        weights = reward_dict(candidate.decode("utf-8"))
        self.assertEqual(weights, self.spec["rewards"]["baseline"])
        self.assertEqual(weights, self.spec["rewards"]["candidate"])
        shipped = json.loads(self.files["expected_rewards.json"])
        self.assertEqual(shipped["baseline"], shipped["candidate"])

    def test_2_run_config_carries_the_training_length(self) -> None:
        text = self.files["run_config.env"].decode("utf-8")
        self.assertIn("MAX_ITERATIONS=1500\n", text)
        self.assertIn("EVAL_CHECKPOINT_ITER=1450\n", text)
        self.assertIn("SINGLE_CHANGE_NAME=max_iterations\n", text)
        self.assertIn("TRAIN_SEED=42\n", text)
        self.assertIn("NUM_ENVS=4096\n", text)

    def test_3_baseline_is_the_frozen_baseline(self) -> None:
        """The arm shipped for verification must be the one GO2_NOW.md calls canonical."""
        now = NOW.read_text(encoding="utf-8")
        for field, key in (("BASELINE_MODEL_SHA256", "model_sha256"),
                           ("BASELINE_ENV_SHA256", "env_sha256"),
                           ("REGISTRY_SHA256", "registry_sha256")):
            self.assertIn(f"{field}: {self.spec['baseline'][key]}", now, field)
        self.assertEqual(build.sha(self.files["baseline/exported/model_best.pt"]),
                         self.spec["baseline"]["model_sha256"])
        self.assertEqual(build.sha(self.files["baseline/exported/env.yaml"]),
                         self.spec["baseline"]["env_sha256"])

    def test_4_checkpoint_is_one_the_run_writes(self) -> None:
        """max_iterations N runs iterations 0..N-1; save_interval 50 must have saved the pin."""
        iters = int(self.spec["training"]["max_iterations"])
        pinned = int(self.spec["evaluation"]["checkpoint_iter"])
        self.assertEqual(pinned % build.SAVE_INTERVAL, 0)
        self.assertLessEqual(pinned, iters - 1)
        self.assertGreater(pinned, iters - 1 - build.SAVE_INTERVAL)

    def test_5_runner_ships_unmodified(self) -> None:
        shipped = self.files[self.spec["runner"]]
        working = (ROOT / "workspace/training/quadruped" / self.spec["runner"]).read_bytes()
        self.assertEqual(shipped, working, "the runner must ship byte for byte")
        self.assertNotIn(b"\r", shipped)

    def test_6_build_is_reproducible(self) -> None:
        self.assertEqual(build.build_zip(build.load(WORK)), self.data)

    def test_7_a_reward_change_is_refused(self) -> None:
        """The guard bites: this builder must never be used to smuggle a reward change."""
        spec = copy.deepcopy(self.spec)
        spec["rewards"]["candidate"]["feet_air_time"] = 0.01
        with self.assertRaises(RuntimeError) as caught:
            build.validate_spec(spec)
        self.assertIn("change no reward", str(caught.exception))

    def test_8_a_wrong_checkpoint_pin_is_refused(self) -> None:
        spec = copy.deepcopy(self.spec)
        spec["evaluation"]["checkpoint_iter"] = 1500
        with self.assertRaises(RuntimeError) as caught:
            build.validate_spec(spec)
        self.assertIn("last checkpoint", str(caught.exception))

    def test_9_thresholds_and_targets_are_anchored(self) -> None:
        prereg = self.spec["preregistered"]
        self.assertTrue(prereg["threshold_basis"].strip())
        self.assertIn("go2_eval_resolution", prereg["threshold_basis"])
        # The limits must be the measured ones, not the retired 0.5/70.
        self.assertAlmostEqual(prereg["max_scenario_weighted_loss_70"], 2.04, places=2)
        self.assertGreaterEqual(prereg["min_total_points_delta"], 2.528)
        stored = ROOT / self.spec["baseline"]["stored_arm"] / "evaluation" / self.spec["baseline"]["stored_label"]
        for entries in prereg["target_groups"].values():
            for entry in entries:
                _scenario, case_id, seed = entry.split(":")
                self.assertTrue((stored / "cases" / f"seed_{seed}" / case_id / "summary.json").is_file(), entry)


if __name__ == "__main__":
    unittest.main()
