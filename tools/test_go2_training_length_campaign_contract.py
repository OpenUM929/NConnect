"""Contract for the G-A035 one-command campaign.  Local only: no simulator, no training.

Every test here names a way the first G-A035 package (v1, never run) was broken.  None of them
was caught by its own 9 contract tests, because those checked what the builder wrote, not what
the server and the verifier would do with it.  These tests run the server gate and the local
verifier on synthetic harvests shaped like the runner's output.

    python -m unittest tools.test_go2_training_length_campaign_contract
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_basic_motion_pair as pair  # noqa: E402
import build_go2_campaign_package as g_a033_campaign  # noqa: E402
import build_go2_training_length_campaign as build  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402
import go2_target_gate as gate  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402

CAMPAIGN_ID = "G-A035"
SPEC = length.load(CAMPAIGN_ID)
BASE = SPEC["baseline"]
STORED_ARM = ROOT / BASE["stored_arm"]
A017_ARM = ROOT / "workspace" / "_keep" / "go2_a017_full_suite" / "evaluation" / "a017"
PAYLOAD = build.build_payload(CAMPAIGN_ID)
ARM = length.build_payload(SPEC)
REGISTRY = json.loads(ARM["go2_self_eval_registry.json"].decode("utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PackageTest(unittest.TestCase):
    def test_1_build_is_reproducible(self) -> None:
        self.assertEqual(build.build_payload(CAMPAIGN_ID), PAYLOAD)

    def test_2_server_runner_and_gate_are_what_ran_for_g_a033(self) -> None:
        """Only code that completed on the server ships.  The G-A033 campaign ZIP is the witness."""
        released = g_a033_campaign.output_path(g_a033_campaign.CAMPAIGNS["G-A033"])
        with zipfile.ZipFile(released) as archive:
            prefix = g_a033_campaign.CAMPAIGNS["G-A033"]["prefix"]
            for name in (build.RUNNER, *build.GATE_FILES):
                with self.subTest(name):
                    # 2026-09-17 (G-D-FACT-RULES-20260917): an unexecuted campaign ships the fact_rules_v1 gate.
                    # The runner and the gate's two dependencies are what ran; the gate that ran is kept in
                    # runner_history byte for byte.
                    ran = archive.read(f"{prefix}/{name}")
                    if name == "go2_target_gate.py":
                        self.assertEqual(ran, pair.EXECUTED_GATE.read_bytes())
                        self.assertEqual(PAYLOAD[name], pair.GATE_FILES[name].read_bytes())
                        self.assertNotEqual(PAYLOAD[name], ran)
                    else:
                        self.assertEqual(PAYLOAD[name], ran)
            for name, path in pair.FACT_RULE_FILES.items():
                self.assertEqual(PAYLOAD[name], path.read_bytes())

    def test_3_arm_is_the_builder_output(self) -> None:
        name = f"arms/{SPEC['output']['upload_zip']}"
        self.assertEqual(PAYLOAD[name], length.build_zip(SPEC))
        config = PAYLOAD["campaign_config.env"].decode("utf-8")
        self.assertIn(sha(PAYLOAD[name]), config)
        self.assertIn(f"ARM_RUNNER={SPEC['runner']}", config)

    def test_4_every_launched_script_is_in_the_package(self) -> None:
        """v1 defect 1: the arm runner launched a script its ZIP did not carry."""
        shipped = {k: v for k, v in PAYLOAD.items() if not k.startswith("arms/")}
        self.assertEqual(build.unreachable_scripts(shipped, ARM, SPEC["runner"]), [])
        # The check has teeth: run standalone (outer path included) the v1 way, it fails.
        runner = ARM[SPEC["runner"]].decode("utf-8")
        self.assertIn("server_run_go2_candidate_staged.sh", build.outer_only_calls(runner))
        standalone = [c for c in build.BASH_CALL.findall(runner)
                      if Path(c).name not in {Path(n).name for n in ARM}]
        self.assertEqual(standalone, ["server_run_go2_candidate_staged.sh"],
                         "the outer path of the arm runner is still broken; only the campaign may run it")

    def test_5_the_arm_guide_does_not_offer_a_standalone_run(self) -> None:
        text = length.guide(SPEC, "0" * 64)
        self.assertIn("DO NOT RUN THIS ZIP ON ITS OWN", text)
        self.assertNotIn("bash server_run", text)
        self.assertNotIn("runner prints TARGET_PASS", text)

    def test_6_baseline_label_is_never_candidate(self) -> None:
        """v1 defect 2: label candidate made both readers compare the candidate with itself."""
        self.assertNotEqual(BASE["label"], "candidate")
        broken = copy.deepcopy(SPEC)
        broken["baseline"]["label"] = "candidate"
        with self.assertRaises(RuntimeError):
            length.validate_spec(broken)

    def test_7_stored_summaries_are_g_a033_under_the_run_label(self) -> None:
        folder = f"stored_baseline/evaluation/{BASE['label']}"
        identity = json.loads(PAYLOAD[f"{folder}/identity.json"])
        self.assertEqual(identity["model_sha256"], BASE["model_sha256"])
        for entry in build.stored_entries(SPEC):
            _scenario, case_id, seed = entry.split(":")
            name = f"{folder}/cases/seed_{seed}/{case_id}/summary.json"
            with self.subTest(entry):
                self.assertEqual(PAYLOAD[name],
                                 (STORED_ARM / "evaluation" / BASE["stored_label"] / "cases" / f"seed_{seed}"
                                  / case_id / "summary.json").read_bytes())

    def test_8_spec_carries_every_key_the_readers_use(self) -> None:
        """v1 defect 3: no sentinel_tolerance -> KeyError in the server gate after training."""
        self.assertIn("sentinel_tolerance", SPEC["evaluation"])
        broken = copy.deepcopy(SPEC)
        del broken["evaluation"]["sentinel_tolerance"]
        with self.assertRaises(RuntimeError):
            length.validate_spec(broken)

    def test_9_the_verifier_accepts_this_arm(self) -> None:
        """v1 defect 4: the verifier's argument parser refused G-A035."""
        self.assertIn(CAMPAIGN_ID, verifier.SPECS)
        self.assertEqual(verifier.load_spec(CAMPAIGN_ID), SPEC)


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir() and A017_ARM.is_dir(),
                     "G-A033 or A017 harvest not present")
class GateAndVerifierTest(unittest.TestCase):
    """The server gate and the verifier of record read a G-A035 target harvest the same way."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.stored = Path(cls.tmp.name) / "campaign" / "stored_baseline"
        for name, data in PAYLOAD.items():
            if name.startswith("stored_baseline/"):
                target = Path(cls.tmp.name) / "campaign" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    @staticmethod
    def copy_cases(source: Path, out: Path, entries: list[str], model_sha: str) -> None:
        for entry in entries:
            _scenario, case_id, seed = entry.split(":")
            shutil.copytree(source / "cases" / f"seed_{seed}" / case_id, out / "cases" / f"seed_{seed}" / case_id)
        (out / "identity.json").write_text(json.dumps({
            "model_sha256": model_sha, "evaluator_sha256": BASE["evaluator_sha256"],
            "registry_sha256": BASE["registry_sha256"]}), encoding="utf-8")

    def harvest(self, name: str) -> Path:
        """What the iteration-pinned runner leaves after a G-A035 target stage, candidate == G-A033."""
        keep = Path(self.tmp.name) / name
        model = b"synthetic G-A035 model"
        model_sha = sha(model)
        single = SPEC["single_change"]
        files = {
            "RESULT_STATUS.txt": "RESULT_STATE=FULL\n",
            "exported/report.html": "<html>synthetic</html>\n",
            "exported/REPORT_STATUS.txt": "REPORT_STATUS=REPORT_ACQUIRED\n",
            "training/TRAIN_STATUS.txt": f"TRAIN_RC=0\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS={SPEC['training']['max_iterations']}\n"
                                         f"SINGLE_CHANGE={single['name']}:{single['from']}->{single['to']}\n",
            "training/env.yaml": (STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8"),
            "training/CHECKPOINT_PIN.txt": f"EVAL_CHECKPOINT_ITER={SPEC['evaluation']['checkpoint_iter']}\n"
                                           f"EVAL_CHECKPOINT_SHA={model_sha}\nREWARD_BEST_MODEL_ITER=1400\n"
                                           f"REWARD_BEST_MODEL_SHA={'0' * 64}\n",
            "meta/evaluator.sha256": f"{BASE['evaluator_sha256']}  go2_eval_telemetry.py\n",
            "meta/registry.sha256": f"{BASE['registry_sha256']}  go2_self_eval_registry.json\n",
        }
        for rel, content in files.items():
            (keep / rel).parent.mkdir(parents=True, exist_ok=True)
            (keep / rel).write_text(content, encoding="utf-8", newline="\n")
        (keep / "training" / "model_best.pt").write_bytes(model)
        report = (keep / "exported" / "report.html").read_bytes()
        (keep / "exported" / "report.html.sha256").write_text(f"{sha(report)}  report.html\n")
        (keep / "RUNNER_STATUS.txt").write_text(
            f"RUNNER_RC=0\nWORK_ID={CAMPAIGN_ID}\nDECISION=TARGET_STAGE_COMPLETE\nCANDIDATE_MODEL_SHA={model_sha}\n"
            f"STAGE=target\nCANDIDATE_EVAL_ITER={SPEC['evaluation']['checkpoint_iter']}\n", encoding="utf-8")
        stored = STORED_ARM / "evaluation" / BASE["stored_label"]
        self.copy_cases(stored, keep / "evaluation" / "candidate",
                        [SPEC["evaluation"]["catastrophe_case"], *length.targets(SPEC)], model_sha)
        self.copy_cases(stored, keep / "evaluation" / f"{BASE['label']}_sentinel",
                        SPEC["evaluation"]["sentinel_cases"], BASE["model_sha256"])
        (keep / "SHA256SUMS.txt").write_text(f"{sha(report)}  ./exported/report.html\n")
        return keep

    def test_1_no_change_fails_against_the_stored_baseline_in_both_readers(self) -> None:
        keep = self.harvest("same")
        server = gate.gate(keep, self.stored, SPEC, REGISTRY)
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["artifact_faults"], [])
        self.assertEqual(server.get("faults", []), [])
        # Stored, not remeasured: v1 read the candidate's own folder as the baseline here.
        self.assertEqual((server["baseline_arm"], local["baseline_arm"]), ("STORED_G-A033", "STORED_G-A033"))
        self.assertTrue(server["sentinel"]["agrees"])
        self.assertTrue(local["sentinel"]["agrees"])
        self.assertEqual((server["verdict"], local["verdict"]), ("FAIL", "FAIL"))
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0, places=12)

    def test_2_a_real_difference_is_read_identically(self) -> None:
        """A017 remeasured as the baseline: a nonzero reading, and the gate and verifier agree on it."""
        keep = self.harvest("differ")
        self.copy_cases(A017_ARM, keep / "evaluation" / BASE["label"],
                        [SPEC["evaluation"]["catastrophe_case"], *length.targets(SPEC)], BASE["model_sha256"])
        server = gate.gate(keep, self.stored, SPEC, REGISTRY)
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual((server["baseline_arm"], local["baseline_arm"]),
                         ("REMEASURED_SAME_RUN", "REMEASURED_SAME_RUN"))
        self.assertNotAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0, places=6)
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"],
                               local["target_stage"]["target_mean_proxy_delta"], places=12)
        expected = {"TARGET_PASS": "TARGET_PASS_FULL_STAGE_REQUIRED", "FAIL": "FAIL"}[server["verdict"]]
        self.assertEqual(local["verdict"], expected)

    def test_3_a_missing_target_case_is_never_a_verdict(self) -> None:
        keep = self.harvest("missing")
        shutil.rmtree(keep / "evaluation" / "candidate" / "cases" / "seed_101" / "stairs_15_down")
        self.assertEqual(gate.gate(keep, self.stored, SPEC, REGISTRY)["verdict"], "UNDECIDED")
        self.assertEqual(verifier.verify(keep, STORED_ARM, SPEC)["verdict"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
