from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import tools.build_go2_g_a087_package as build


class G_A087PackageTest(unittest.TestCase):
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

    def test_identity_and_reward_diff(self) -> None:
        cfg = self.read(f"runs/{build.KEY}/run_config.env").decode()
        self.assertIn("WORK_ID=G-A087", cfg)
        self.assertIn("MAX_ITERATIONS=3000", cfg)
        self.assertIn("TRAIN_SEED=42", cfg)
        self.assertIn(f"BASELINE_MODEL_SHA={build.B_MODEL_SHA}", cfg)
        self.assertIn(f"BASELINE_ENV_SHA={build.B_ENV_SHA}", cfg)
        self.assertIn("EVAL_CHECKPOINT_ITER=2400", cfg)
        expected = json.loads(self.read(f"runs/{build.KEY}/expected_rewards.json"))
        changed = [k for k in expected["baseline"] if expected["baseline"][k] != expected["candidate"][k]]
        self.assertEqual(["flat_orientation_l2"], sorted(changed))
        self.assertEqual(-0.01, expected["baseline"]["action_rate_l2"])
        self.assertEqual(-0.225, expected["baseline"]["flat_orientation_l2"])
        self.assertEqual(-0.01, expected["candidate"]["action_rate_l2"])
        self.assertEqual(-0.23, expected["candidate"]["flat_orientation_l2"])
        self.assertEqual(-0.05, expected["candidate"]["ang_vel_xy_l2"])
        cand = self.read(f"runs/{build.KEY}/candidate/quadruped_rewards.py").decode()
        rewards = build.a082.a077.reward_dict(cand)
        self.assertEqual(expected["candidate"], rewards)
        self.assertEqual(0.75, rewards["track_ang_vel_z_exp"])
        base = build.a082.a077.reward_dict(self.read(f"runs/{build.KEY}/reference/baseline_quadruped_rewards.py").decode())
        self.assertEqual(expected["baseline"], base)

    def test_baseline_video_count_matches_stored_arm(self) -> None:
        cfg = self.read(f"runs/{build.KEY}/run_config.env").decode()
        line = next(l for l in cfg.splitlines() if l.startswith("BASELINE_VIDEOS="))
        self.assertEqual(10, len(line.split("=", 1)[1].strip("()").split()))
        names = self.archive.namelist()
        base = self.prefix + "shared/baseline/stored_evaluation/videos/"
        self.assertEqual(10, sum(n.startswith(base) and n.endswith(".mp4") for n in names))

    def test_real_pc2_g_a083_baseline_is_embedded(self) -> None:
        self.assertEqual(build.B_MODEL_SHA, hashlib.sha256(self.read("shared/baseline/exported/model_best.pt")).hexdigest())
        self.assertEqual(build.B_ENV_SHA, hashlib.sha256(self.read("shared/baseline/exported/env.yaml")).hexdigest())
        names = self.archive.namelist()
        base = self.prefix + "shared/baseline/stored_evaluation/"
        self.assertEqual(69, sum(n.startswith(base + "cases/") and n.endswith("/summary.json") for n in names))
        identity = json.loads(self.read("shared/baseline/stored_evaluation/identity.json"))
        self.assertEqual(build.B_MODEL_SHA, identity["model_sha256"])
        self.assertEqual(build.EVALUATOR_SHA, identity["evaluator_sha256"])

    def test_preregistration(self) -> None:
        exp = json.loads(self.read(f"runs/{build.KEY}/experiment.json"))
        pred = exp["preregistered_predictions"]["primary"]
        self.assertIn("57.59", pred["metric"])
        self.assertIn("0.65", pred["fit_transfers_if"])
        self.assertIn("56.94", pred["fit_fails_if"])
        sec = exp["preregistered_predictions"]["secondary"]
        self.assertEqual({"push_falls", "total_falls", "stairs_15_climb_falls", "low_type_robots"}, set(sec))
        self.assertIn("stairs_full_proxy", exp["preregistered_predictions"]["protection"])
        self.assertEqual("exploratory_single_seed_no_automatic_followup", exp["promotion"])
        self.assertEqual({"flat_orientation_l2": (-0.225, -0.23)},
                         {k: (v["from"], v["to"]) for k, v in exp["changes"].items() if isinstance(v, dict)})
        self.assertEqual(exp["rewards"], json.loads(self.read(f"runs/{build.KEY}/expected_rewards.json"))["candidate"])
        self.assertIn("0.65", exp["evidence_basis"]["noise"])
        self.assertIn("if_train_rc_nonzero_after_2400", exp["divergence_plan"])

    def test_deployment_code_is_unchanged(self) -> None:
        unchanged = ("train.py", "play.py", "go2_eval_telemetry.py", "go2_policy_lineage.py", "go2_task/__init__.py",
                     "go2_task/_finalize.py", "go2_task/agent_cfg.py", "go2_task/env_cfg.py")
        for rel in unchanged:
            self.assertEqual(self.read(f"shared/baseline/{rel}"), self.read(f"shared/candidate/{rel}"), rel)
            self.assertEqual((build.B_SOURCE / rel).read_bytes(), self.read(f"shared/candidate/{rel}"), rel)
        self.assertEqual((build.B_SOURCE / "quadruped_rewards.py").read_bytes(),
                         self.read(f"runs/{build.KEY}/reference/baseline_quadruped_rewards.py"))

    def test_runner_guards_precede_training(self) -> None:
        runner = self.read("shared/server_run_go2_candidate_iter_pinned.sh").decode()
        self.assertLess(runner.index("Go2 USD asset is unavailable"), runner.index("[PHASE 1/6]"))
        self.assertIn("REUSED_G_A083_PC2_FULL_NO_RERUN", runner)
        self.assertNotIn("REUSED_G_A082", runner)
        self.assertNotIn("REUSED_G_A077", runner)
        self.assertIn("exp_base=69", runner)
        self.assertNotIn('run_video_list "${BASELINE_LABEL}_videos"', runner)
        self.assertIn("pgrep -af 'train.py|play.py'", self.read("run_point.sh").decode())

    def test_shared_runtime_matches_g_a082_chain(self) -> None:
        # 2026-10-15: a hand-rolled source payload dropped the result packager, the two
        # checkers and the Isaac-Lab-first python pick.  The runtime must come from the
        # same chain as the published G-A082 package.
        names = {n[len(self.prefix + "shared/"):] for n in self.archive.namelist()
                 if n.startswith(self.prefix + "shared/") and not n.startswith(self.prefix + "shared/baseline/")
                 and not n.startswith(self.prefix + "shared/candidate/")}
        for required in ("package_go2_result.py", "candidate_suite_checks.py", "posture_contract_check.py",
                         "server_run_go2_candidate_iter_pinned.sh"):
            self.assertIn(required, names)
        runner = self.read("shared/server_run_go2_candidate_iter_pinned.sh")
        self.assertIn(b'if [[ -x "$ISAACLAB_SH" ]]; then\n  PY=("$ISAACLAB_SH" -p)\nelif', runner)

    def test_identity_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "identity.json"
            ident = {"model_sha256": build.B_MODEL_SHA, "env_sha256": build.B_ENV_SHA,
                     "evaluator_sha256": build.EVALUATOR_SHA, "registry_sha256": build.REGISTRY_SHA}
            env = {**os.environ, "STORED_BASELINE": d, "BASELINE_MODEL_SHA": build.B_MODEL_SHA,
                   "BASELINE_ENV_SHA": build.B_ENV_SHA, "EXPECTED_EVALUATOR_SHA": build.EVALUATOR_SHA,
                   "EXPECTED_REGISTRY_SHA": build.REGISTRY_SHA}
            p.write_text(json.dumps(ident, separators=(",", ":")), encoding="utf-8")
            self.assertEqual(0, subprocess.run(["bash", "-c", build.IDENTITY_GREP_LINES], env=env, capture_output=True).returncode)
            ident["model_sha256"] = "0" * 64
            p.write_text(json.dumps(ident, separators=(",", ":")), encoding="utf-8")
            self.assertEqual(23, subprocess.run(["bash", "-c", build.IDENTITY_GREP_LINES], env=env, capture_output=True).returncode)

    def test_manifests_crc_lf_and_shell_syntax(self) -> None:
        self.assertIsNone(self.archive.testzip())
        mat: dict[str, bytes] = {}
        for name in self.archive.namelist():
            rel = name[len(self.prefix):]
            if rel.startswith("shared/"):
                mat[rel[len("shared/"):]] = self.archive.read(name)
            elif rel.startswith(f"runs/{build.KEY}/"):
                mat[rel[len(f"runs/{build.KEY}/"):]] = self.archive.read(name)
        for line in mat.pop("PACKAGE_SHA256SUMS.txt").decode().splitlines():
            digest, path = line.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256(mat[path]).hexdigest(), path)
        top = self.read("SHA256SUMS.txt").decode().splitlines()
        for line in top:
            digest, path = line.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256(self.read(path)).hexdigest(), path)
        text = {".env", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
        for name in self.archive.namelist():
            if Path(name).suffix in text and "/shared/baseline/exported/" not in name and "/stored_evaluation/" not in name:
                self.assertNotIn(b"\r\n", self.archive.read(name), name)
        with tempfile.TemporaryDirectory() as d:
            for name in ("run_all.sh", "run_point.sh", "shared/server_run_go2_candidate_iter_pinned.sh"):
                path = Path(d) / Path(name).name
                path.write_bytes(self.read(name))
                r = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
                self.assertEqual(0, r.returncode, r.stderr)


if __name__ == "__main__":
    unittest.main()


