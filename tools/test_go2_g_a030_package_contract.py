"""Contract tests for the G-A030 candidate-suite package (measurement path 나′).

Local only: no simulator, no training.  Run from the repository root:
    python -m unittest tools.test_go2_g_a030_package_contract
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_g_a030_package as pkg  # noqa: E402
import verify_go2_g_a030_harvest as verifier  # noqa: E402
from candidate_suite_checks import reward_weights  # noqa: E402
from go2_fixed_eval_report import build_policy  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402
from tools.test_h1_report_recovery import BASH, shell_path  # noqa: E402

KEEP = ROOT / "workspace" / "_keep"
A027 = KEEP / "go2_a017_full_suite"
A027_ZIP = GO2 / "upload" / "G-A027" / "current" / "go2_a017_full_suite.zip"
A017_TRAINING = KEEP / "go2_g_a017_pilot_track_lin_vel_xy_140" / "training"
SPEC = pkg.load_spec()
PAYLOAD = pkg.build_payload(SPEC)
RUNNER = PAYLOAD[pkg.RUNNER].decode("utf-8")


def lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def extract(text: str, start: str, end: str) -> str:
    head = text.index(start)
    return text[head: text.index(end, head) + len(end)]


class PayloadTest(unittest.TestCase):
    def test_manifest_covers_every_member(self):
        lines = PAYLOAD["PACKAGE_SHA256SUMS.txt"].decode("utf-8").splitlines()
        self.assertEqual(len(lines), len(PAYLOAD) - 1)
        for line in lines:
            digest, name = line.split("  ", 1)
            self.assertEqual(hashlib.sha256(PAYLOAD[name]).hexdigest(), digest, name)

    def test_single_variable_is_flat_orientation_only(self):
        cand = reward_dict(PAYLOAD["candidate/quadruped_rewards.py"].decode("utf-8"))
        ref = reward_dict(PAYLOAD["reference/baseline_quadruped_rewards.py"].decode("utf-8"))
        self.assertEqual(ref, SPEC["rewards"]["baseline"])
        self.assertEqual(cand, SPEC["rewards"]["candidate"])
        self.assertEqual([k for k in cand if cand[k] != ref[k]], ["flat_orientation_l2"])
        self.assertEqual((ref["flat_orientation_l2"], cand["flat_orientation_l2"]), (0.0, -1.0))
        diff = [(a, b) for a, b in zip(PAYLOAD["reference/baseline_quadruped_rewards.py"].splitlines(),
                                       PAYLOAD["candidate/quadruped_rewards.py"].splitlines()) if a != b]
        self.assertEqual(len(diff), 1, "text diff must be one line")

    def test_baseline_rewards_are_what_a017_was_trained_with(self):
        trained = A017_TRAINING / "source" / "quadruped_rewards.py"
        if not trained.is_file():
            self.skipTest("A017 training source not present")
        self.assertEqual(reward_dict(trained.read_text(encoding="utf-8")), SPEC["rewards"]["baseline"])

    def test_deployed_code_is_unchanged_r6(self):
        # Every shipped source except the candidate's reward file is the working
        # tree byte for byte, in both roles.
        for name, data in PAYLOAD.items():
            role, _, rel = name.partition("/")
            if role not in ("candidate", "baseline") or rel.startswith("exported/"):
                continue
            if name == "candidate/quadruped_rewards.py":
                continue
            self.assertEqual(data, (GO2 / rel).read_bytes(), name)

    def test_training_code_matches_the_a017_training_run(self):
        source = A017_TRAINING / "source"
        if not source.is_dir():
            self.skipTest("A017 training source not present")
        for rel in ("train.py", "play.py", "pyproject.toml", "go2_policy_lineage.py", "go2_task/__init__.py",
                    "go2_task/_finalize.py", "go2_task/agent_cfg.py", "go2_task/env_cfg.py"):
            self.assertEqual(lf(PAYLOAD[f"candidate/{rel}"]), lf((source / rel).read_bytes()), rel)

    def test_both_arms_ship_one_evaluator_and_it_is_the_stored_arms(self):
        self.assertEqual(PAYLOAD["candidate/go2_eval_telemetry.py"], PAYLOAD["baseline/go2_eval_telemetry.py"])
        self.assertEqual(PAYLOAD["candidate/play.py"], PAYLOAD["baseline/play.py"])
        base = SPEC["baseline"]
        self.assertEqual(hashlib.sha256(PAYLOAD["candidate/go2_eval_telemetry.py"]).hexdigest(), base["evaluator_sha256"])
        self.assertEqual(hashlib.sha256(PAYLOAD["go2_self_eval_registry.json"]).hexdigest(), base["registry_sha256"])
        identity = A027 / "evaluation" / "a017" / "identity.json"
        if identity.is_file():
            stored = json.loads(identity.read_text(encoding="utf-8"))
            self.assertEqual(stored["evaluator_sha256"], base["evaluator_sha256"])
            self.assertEqual(stored["registry_sha256"], base["registry_sha256"])
            self.assertEqual(stored["model_sha256"], base["model_sha256"])
            self.assertEqual(stored["env_sha256"], base["env_sha256"])

    def test_baseline_role_is_the_g_a027_a017_role(self):
        if not A027_ZIP.is_file():
            self.skipTest("G-A027 upload ZIP not present")
        with zipfile.ZipFile(A027_ZIP) as archive:
            for name, data in PAYLOAD.items():
                if name.startswith("baseline/"):
                    member = "go2_a017_full_suite/a017/" + name[len("baseline/"):]
                    self.assertEqual(archive.read(member), data, member)

    def test_baseline_artifacts_are_frozen_a017(self):
        base = SPEC["baseline"]
        self.assertEqual(hashlib.sha256(PAYLOAD["baseline/exported/model_best.pt"]).hexdigest(), base["model_sha256"])
        self.assertEqual(hashlib.sha256(PAYLOAD["baseline/exported/env.yaml"]).hexdigest(), base["env_sha256"])
        weights = reward_weights(PAYLOAD["baseline/exported/env.yaml"].decode("utf-8"))
        self.assertEqual({k: weights[k] for k in SPEC["rewards"]["baseline"]}, SPEC["rewards"]["baseline"])
        self.assertIsNone(weights["undesired_contacts"], "undesired_contacts is undefined in A017 env.yaml")

    def test_run_config_is_the_spec(self):
        script = PAYLOAD["run_config.env"].decode("utf-8") + (
            'printf "%s|" "$WORK_ID" "$SINGLE_CHANGE_NAME" "$SINGLE_CHANGE_TO" "$TRAIN_SEED" "$MAX_ITERATIONS" '
            '"$BASELINE_MODEL_SHA" "$EXPECTED_EVALUATOR_SHA" "$CATASTROPHE_CASE" "$DONE_MARKER" '
            '"${#SENTINEL_CASES[@]}" "${#CANDIDATE_VIDEOS[@]}" "${#BASELINE_VIDEOS[@]}"\n')
        done = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        base = SPEC["baseline"]
        self.assertEqual(done.stdout.split("|")[:-1], [
            "G-A030", "flat_orientation_l2", "-1.0", "42", "1000", base["model_sha256"], base["evaluator_sha256"],
            "G1:forward_nominal:101", "[DONE] GO2_G_A030_RESULT_READY", "5", "12", "2"])

    def test_spec_carries_dial_history_ref(self):
        self.assertIn("flat_orientation_l2", SPEC["dial_history_ref"])


class RunnerTest(unittest.TestCase):
    def test_runner_is_lf_and_parses(self):
        self.assertNotIn("\r", RUNNER)
        done = subprocess.run([BASH, "-n", shell_path(GO2 / pkg.RUNNER)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_report_recovery_is_the_engine_block_and_runs_before_evaluation(self):
        engine = (GO2 / pkg.ENGINE_RUNNER).read_text(encoding="utf-8")
        self.assertEqual(pkg.REPORT_BLOCK.search(RUNNER).group(0), pkg.REPORT_BLOCK.search(engine).group(0))
        self.assertIn('touch "$TRAIN_START_MARKER"', RUNNER)
        self.assertIn("sha256sum -c report.html.sha256", RUNNER)
        self.assertLess(RUNNER.index("recover_training_report || exit 4"), RUNNER.index("CANDIDATE_MODEL="))

    def test_phase_order(self):
        order = ["-p train.py", "env-rewards", "[PHASE 2/6]", '"$CHECKS" moving', "run_full_suite candidate ",
                 "[PHASE 4/6]", 'run_video_list candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "${',
                 "finish SUITE_COMPLETE"]
        positions = [RUNNER.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions), order)

    def test_training_reward_check_is_on_env_yaml_after_training(self):
        self.assertIn('"$CHECKS" env-rewards "$KEEP/training/env.yaml" "$EXPECTED_REWARDS" candidate', RUNNER)

    def test_stored_arm_reuse_is_guarded_and_remeasure_uses_same_ruler(self):
        self.assertIn('[[ "$EVALUATOR_SHA" == "$EXPECTED_EVALUATOR_SHA" ]]', RUNNER)
        self.assertIn('[[ "$REGISTRY_SHA" == "$EXPECTED_REGISTRY_SHA" ]]', RUNNER)
        self.assertIn('run_full_suite "$BASELINE_LABEL" "$BASELINE_ROOT"', RUNNER)
        self.assertIn('for entry in "${SENTINEL_CASES[@]}"', RUNNER)
        # The evaluator hash in every fingerprint is one variable for both arms.
        self.assertEqual(RUNNER.count("EVALUATOR_SHA=$("), 1)

    def test_counts_and_single_trainer(self):
        self.assertIn("== 69 ]]", RUNNER)
        self.assertEqual(RUNNER.count("-p train.py"), 1)
        self.assertIn("finish \"$DECISION\" NOT_MEASURED", RUNNER)
        self.assertIn('echo "$DONE_MARKER"', RUNNER)

    def test_previous_results_are_not_destroyed_by_default(self):
        self.assertIn('if [[ "$RESUME" == 0 && ( -d "$KEEP" || -e "$RESULT_ZIP" ) ]]; then', RUNNER)
        self.assertIn('"${GO2_DISCARD_PREVIOUS:-0}" != 1', RUNNER)

    def test_fingerprints_are_the_g_a027_expressions(self):
        a027 = (GO2 / "server_run_go2_a017_full_suite.sh").read_text(encoding="utf-8")
        for start, end in (("  local fingerprint\n", "| sha256sum | awk '{print $1}'\n  )"),
                           ("  local vmodel_sha venv_sha\n", "| sha256sum | awk '{print $1}')")):
            self.assertEqual(extract(RUNNER, start, end), extract(a027, start, end))
        self.assertEqual(extract(RUNNER, "set_case() {", "\n}\n"), extract(a027, "set_case() {", "\n}\n"))


class ChecksTest(unittest.TestCase):
    def run_checks(self, *args):
        return subprocess.run([sys.executable, str(GO2 / "candidate_suite_checks.py"), *args],
                              capture_output=True, text=True)

    def test_env_rewards(self):
        with tempfile.TemporaryDirectory() as tmp:
            expected = Path(tmp) / "expected.json"
            expected.write_bytes(PAYLOAD["expected_rewards.json"])
            env = str(A017_TRAINING / "env.yaml")
            if not Path(env).is_file():
                self.skipTest("A017 env.yaml not present")
            self.assertEqual(self.run_checks("env-rewards", env, str(expected), "baseline").returncode, 0)
            refused = self.run_checks("env-rewards", env, str(expected), "candidate")
            self.assertEqual(refused.returncode, 1)
            self.assertIn("flat_orientation_l2=0.0 expected -1.0", refused.stderr)

    def test_moving(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            for data, code in (({"speed_xy_mean": 0.7, "tracking_xy_rmse": 0.1}, 0),
                               ({"speed_xy_mean": 0.05, "tracking_xy_rmse": 0.6}, 1),
                               ({"speed_xy_mean": 0.05, "tracking_xy_rmse": 0.2}, 0),
                               ({"speed_xy_mean": None, "tracking_xy_rmse": 0.6}, 2)):
                path.write_text(json.dumps(data), encoding="utf-8")
                self.assertEqual(self.run_checks("moving", str(path)).returncode, code, data)
        real = A027 / "evaluation" / "a017" / "cases" / "seed_101" / "forward_nominal" / "summary.json"
        if real.is_file():
            self.assertEqual(self.run_checks("moving", str(real)).returncode, 0)


class ArchiveTest(unittest.TestCase):
    def test_archive_on_disk_matches_payload(self):
        if not pkg.OUTPUT.is_file():
            self.skipTest("run tools/build_go2_g_a030_package.py first")
        with zipfile.ZipFile(pkg.OUTPUT) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertEqual(len(names), len(PAYLOAD))
            for name, data in PAYLOAD.items():
                self.assertEqual(archive.read(f"go2_g_a030/{name}"), data, name)
            mode = archive.getinfo(f"go2_g_a030/{pkg.RUNNER}").external_attr >> 16
            self.assertTrue(mode & 0o111)
        digest = hashlib.sha256(pkg.OUTPUT.read_bytes()).hexdigest()
        self.assertIn(digest, pkg.OUTPUT.with_suffix(".zip.sha256").read_text(encoding="utf-8"))
        current = pkg.UPLOAD / "current" / pkg.ZIP_NAME
        if current.is_file():
            self.assertEqual(hashlib.sha256(current.read_bytes()).hexdigest(), digest)
            self.assertIn(digest, (pkg.UPLOAD / "current" / pkg.GUIDE_NAME).read_text(encoding="utf-8"))


@unittest.skipUnless((A027 / "evaluation" / "pilot" / "cases").is_dir(), "G-A027 harvest not present")
class JudgeTest(unittest.TestCase):
    """The pre-registered reading, exercised on real 69-case arms."""

    @classmethod
    def setUpClass(cls):
        reg = GO2 / "config" / "go2_self_eval_registry.json"
        cls.a017 = build_policy(A027 / "evaluation" / "a017", reg, {})
        cls.pilot = build_policy(A027 / "evaluation" / "pilot", reg, {})
        cls.prereg = SPEC["preregistered"]

    def test_no_change_is_not_success(self):
        result = verifier.judge(self.a017, self.a017, self.prereg)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["failed"], ["1_target_survival_each_seed", "2_total_points_delta"])

    def test_track_140_would_have_failed_non_inferiority_on_g4(self):
        # Pilot -> A017 (track 1.2 -> 1.4) raised rough_lateral survival on every
        # seed and the total by +6.09/70, and still broke the G4 guard (posture
        # falls 0 -> 7/8/4).  The guard exists for exactly this side effect.
        result = verifier.judge(self.pilot, self.a017, self.prereg)
        self.assertTrue(result["criteria"]["1_target_survival_each_seed"])
        self.assertTrue(result["criteria"]["2_total_points_delta"])
        self.assertFalse(result["criteria"]["3_non_inferiority"])
        self.assertTrue(any("slope_plus_20@202 posture falls +8" in v for v in result["non_inferiority_violations"]))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertAlmostEqual(result["points_70"]["delta"], 6.09, delta=0.01)

    def test_terminations_and_gate_falls_are_read_separately(self):
        rows = verifier.judge(self.pilot, self.a017, self.prereg)["target_per_seed"]
        self.assertEqual([r["terminated_candidate"] for r in rows], [17, 14, 17])
        self.assertEqual([r["terminated_baseline"] for r in rows], [6, 11, 14])
        # Pilot's rough_lateral lost survival to posture-gate falls, not terminations.
        self.assertTrue(all(r["posture_falls_baseline"] > r["terminated_baseline"] for r in rows))


if __name__ == "__main__":
    unittest.main()
