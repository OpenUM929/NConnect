from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import tools.build_go2_g_a077_package as build


class G_A077PackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.zip_path = Path(cls.temp.name) / f"{build.RELEASE}.zip"
        cls.info = build.write_zip(cls.zip_path)
        cls.archive = zipfile.ZipFile(cls.zip_path)
        cls.prefix = build.PREFIX

    @classmethod
    def tearDownClass(cls) -> None:
        cls.archive.close()
        cls.temp.cleanup()

    def read(self, name: str) -> bytes:
        return self.archive.read(self.prefix + name)

    def test_identity_and_single_reward_diff(self) -> None:
        cfg = self.read(f"runs/{build.KEY}/run_config.env").decode()
        self.assertIn("WORK_ID=G-A077", cfg)
        self.assertIn(f"BASELINE_MODEL_SHA={build.G074_MODEL_SHA}", cfg)
        self.assertIn(f"BASELINE_ENV_SHA={build.G074_ENV_SHA}", cfg)
        self.assertIn("EVAL_CHECKPOINT_ITER=2400", cfg)
        expected = json.loads(self.read(f"runs/{build.KEY}/expected_rewards.json"))
        changed = [key for key in expected["baseline"] if expected["baseline"][key] != expected["candidate"][key]]
        self.assertEqual(["flat_orientation_l2"], changed)
        self.assertEqual(-0.25, expected["baseline"]["flat_orientation_l2"])
        self.assertEqual(-0.225, expected["candidate"]["flat_orientation_l2"])

    def test_real_g074_baseline_is_embedded(self) -> None:
        model = self.read("shared/baseline/exported/model_best.pt")
        env = self.read("shared/baseline/exported/env.yaml")
        self.assertEqual(build.G074_MODEL_SHA, hashlib.sha256(model).hexdigest())
        self.assertEqual(build.G074_ENV_SHA, hashlib.sha256(env).hexdigest())
        names = self.archive.namelist()
        base = self.prefix + "shared/baseline/stored_evaluation/"
        self.assertEqual(69, sum(name.startswith(base + "cases/") and name.endswith("/summary.json") for name in names))
        self.assertEqual(10, sum(name.startswith(base + "videos/") and name.endswith(".mp4") for name in names))
        identity = json.loads(self.read("shared/baseline/stored_evaluation/identity.json"))
        self.assertEqual(build.G074_MODEL_SHA, identity["model_sha256"])
        self.assertEqual(build.G074_ENV_SHA, identity["env_sha256"])
        self.assertEqual(build.EVALUATOR_SHA, identity["evaluator_sha256"])

    def test_preregistration_has_requested_thresholds(self) -> None:
        exp = json.loads(self.read(f"runs/{build.KEY}/experiment.json"))
        threshold = exp["preregistered_thresholds"]
        self.assertEqual({"101": ">0", "202": ">0", "303": ">0"}, threshold["stairs_15_down"]["full_count_each_seed"])
        self.assertEqual({"101": 17, "202": 19, "303": 14}, threshold["stairs_15_down"]["ge2_min_each_seed"])
        self.assertEqual(
            {"101": 0.84375, "202": 0.9375, "303": 0.96875},
            threshold["stairs_15_down"]["survival_proxy_min_each_seed"],
        )
        self.assertEqual({"101": 32, "202": 30, "303": 28}, threshold["stairs_10_down_ge2_min_each_seed"])
        self.assertEqual(1e-9, threshold["all_69_case_protection"]["absolute_tolerance"])
        self.assertEqual("exploratory_single_seed_no_automatic_followup", exp["promotion"])
        self.assertIn("OUT_OF_RANGE", exp["single_change"]["matched_series_classification"])
        self.assertIn("NOT_APPLICABLE", exp["evidence_basis"]["inference"])
        self.assertEqual("POSTHOC_AUTHOR_CHECKER_REQUIRED", exp["decision_authority"]["preregistered_threshold_enforcement"])

    def test_deployment_code_is_unchanged_between_arms(self) -> None:
        unchanged = (
            "train.py",
            "play.py",
            "go2_eval_telemetry.py",
            "go2_policy_lineage.py",
            "go2_task/__init__.py",
            "go2_task/_finalize.py",
            "go2_task/agent_cfg.py",
            "go2_task/env_cfg.py",
        )
        for relative in unchanged:
            self.assertEqual(
                self.read(f"shared/baseline/{relative}"),
                self.read(f"shared/candidate/{relative}"),
                relative,
            )
        g074_source = build.G074_SOURCE
        for relative in unchanged:
            expected = (g074_source / relative).read_bytes()
            self.assertEqual(expected, self.read(f"shared/candidate/{relative}"), relative)
        self.assertEqual(
            (g074_source / "quadruped_rewards.py").read_bytes(),
            self.read(f"runs/{build.KEY}/reference/baseline_quadruped_rewards.py"),
        )

    def test_runner_guards_precede_training(self) -> None:
        runner = self.read("shared/server_run_go2_candidate_iter_pinned.sh").decode()
        preflight = runner.index("Go2 USD asset is unavailable")
        training = runner.index("[PHASE 1/6]")
        self.assertLess(preflight, training)
        self.assertIn("REUSED_G_A074_FULL_NO_RERUN", runner)
        self.assertIn("exp_base=69", runner)
        self.assertIn("exp_sent=0", runner)
        self.assertNotIn('run_video_list "${BASELINE_LABEL}_videos"', runner)
        self.assertIn("NON_AUTHORITATIVE_EXECUTION_SAFETY_ONLY", runner)
        self.assertIn("POSTHOC_AUTHOR_CHECKER_REQUIRED", runner)
        self.assertIn("pgrep -af 'train.py|play.py'", self.read("run_point.sh").decode())
        py_block = runner[runner.index("PY=()"):runner.index("# Both roles ship")]
        self.assertLess(py_block.index('[[ -x "$ISAACLAB_SH" ]]'), py_block.index("command -v python3"))

    def test_identity_preflight_accepts_exact_and_rejects_wrong_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            identity_path = Path(directory) / "identity.json"
            identity = {
                "model_sha256": build.G074_MODEL_SHA,
                "env_sha256": build.G074_ENV_SHA,
                "evaluator_sha256": build.EVALUATOR_SHA,
                "registry_sha256": build.REGISTRY_SHA,
            }
            environment = {
                **os.environ,
                "STORED_BASELINE": directory,
                "BASELINE_MODEL_SHA": build.G074_MODEL_SHA,
                "BASELINE_ENV_SHA": build.G074_ENV_SHA,
                "EXPECTED_EVALUATOR_SHA": build.EVALUATOR_SHA,
                "EXPECTED_REGISTRY_SHA": build.REGISTRY_SHA,
            }
            identity_path.write_text(json.dumps(identity, separators=(",", ":")), encoding="utf-8")
            accepted = subprocess.run(["bash", "-c", build.IDENTITY_GREP_LINES], env=environment, capture_output=True)
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            identity["model_sha256"] = "0" * 64
            identity_path.write_text(json.dumps(identity, separators=(",", ":")), encoding="utf-8")
            rejected = subprocess.run(["bash", "-c", build.IDENTITY_GREP_LINES], env=environment, capture_output=True)
            self.assertEqual(23, rejected.returncode)

    def test_manifests_crc_lf_and_shell_syntax(self) -> None:
        self.assertIsNone(self.archive.testzip())
        materialized: dict[str, bytes] = {}
        for name in self.archive.namelist():
            relative = name[len(self.prefix):]
            if relative.startswith("shared/"):
                materialized[relative[len("shared/"):]] = self.archive.read(name)
            elif relative.startswith(f"runs/{build.KEY}/"):
                materialized[relative[len(f"runs/{build.KEY}/"):]] = self.archive.read(name)
        manifest = materialized.pop("PACKAGE_SHA256SUMS.txt").decode().splitlines()
        for line in manifest:
            digest, path = line.split("  ", 1)
            self.assertIn(path, materialized)
            self.assertEqual(digest, hashlib.sha256(materialized[path]).hexdigest(), path)
        text_suffixes = {".env", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
        for name in self.archive.namelist():
            immutable_evidence = (
                "/shared/baseline/exported/" in name
                or "/shared/baseline/stored_evaluation/" in name
            )
            if Path(name).suffix in text_suffixes and not immutable_evidence:
                self.assertNotIn(b"\r\n", self.archive.read(name), name)
        with tempfile.TemporaryDirectory() as directory:
            for name in ("run_all.sh", "run_point.sh", "shared/server_run_go2_candidate_iter_pinned.sh"):
                path = Path(directory) / Path(name).name
                path.write_bytes(self.read(name))
                result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
