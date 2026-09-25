"""Contract for the G-A039 one-command campaign (G-A033 + dof_acc_l2 -2.5e-07 -> -1.25e-07).  Local only.

A package is not ready until the code that will read its harvest has run on one (memory rule
"준비 완료 = 판독 코드를 돌려봤다").  So besides what the builder writes, these tests run the server
gate and the local verifier on synthetic harvests shaped like the runner's output.

What is new in this arm, and what these tests pin down:
  dof_acc_l2 is NOT one of the six names in the deployed REWARD_WEIGHTS list, so the candidate reward
  file gains a line instead of changing a number.  go2_task/env_cfg.py applies any name that is a
  RewTerm of the env, and the trained env.yaml is the only proof it was applied -- so the verifier
  must fail when that weight is missing from env.yaml (test_3 of the gate class).

    python -m unittest tools.test_go2_g_a039_campaign_contract
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import re
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

import build_go2_a033_reward_package as reward  # noqa: E402
import go2_reward_mechanism as mech  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import build_go2_campaign_package as g_a033_campaign  # noqa: E402
import build_go2_training_length_campaign as build  # noqa: E402
import go2_target_gate as gate  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict  # noqa: E402

CAMPAIGN_ID = "G-A039"
SPEC = reward.load(CAMPAIGN_ID)
BASE = SPEC["baseline"]
TERM = SPEC["single_change"]["name"]
STORED_ARM = ROOT / BASE["stored_arm"]
A017_ARM = ROOT / "workspace" / "_keep" / "go2_a017_full_suite" / "evaluation" / "a017"
PAYLOAD = build.build_payload(CAMPAIGN_ID)
ARM = reward.build_payload(SPEC)
REGISTRY = json.loads(ARM["go2_self_eval_registry.json"].decode("utf-8"))
CAMP = build.CAMPAIGNS[CAMPAIGN_ID]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PackageTest(unittest.TestCase):
    def test_1_build_is_reproducible_and_published(self) -> None:
        self.assertEqual(build.build_payload(CAMPAIGN_ID), PAYLOAD)
        current = GO2 / "upload" / CAMP["upload_id"] / "current" / CAMP["upload_zip"]
        with zipfile.ZipFile(current) as archive:
            shipped = {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()}
        self.assertEqual(shipped, PAYLOAD, "the published ZIP is not this build")
        digest = sha(current.read_bytes())
        self.assertIn(digest, (current.parent / "CURRENT_UPLOAD.txt").read_text(encoding="utf-8"))
        self.assertIn(digest, (current.parent / CAMP["guide"]).read_text(encoding="utf-8"))
        manifest = json.loads((current.parent / "UPLOAD_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["published_at_utc"], CAMP["published_at"])
        self.assertEqual(manifest["upload_files"][0]["sha256"], digest)

    def test_2_campaign_runner_and_gate_are_what_ran_for_g_a033(self) -> None:
        released = g_a033_campaign.output_path(g_a033_campaign.CAMPAIGNS["G-A033"])
        with zipfile.ZipFile(released) as archive:
            prefix = g_a033_campaign.CAMPAIGNS["G-A033"]["prefix"]
            self.assertEqual(PAYLOAD[build.RUNNER], archive.read(f"{prefix}/{build.RUNNER}"))
        # The arm runner is the repaired one (video-log fix of 2026-09-17), not the bytes G-A038 ran:
        # this arm has not run, so it must ship the fixed runner.
        self.assertEqual(ARM[SPEC["runner"]], (GO2 / SPEC["runner"]).read_bytes())
        cand = reward.length.cand
        ran = {name for key, name in cand.EXECUTED_RUNNERS.items() if key[0] == "G-A038"}
        self.assertTrue(ran)
        for name in ran:
            self.assertNotEqual(ARM[SPEC["runner"]], (cand.RUNNER_HISTORY / name).read_bytes())

    def test_3_exactly_one_reward_line_is_added_and_none_moves(self) -> None:
        candidate = ARM["candidate/quadruped_rewards.py"].decode("utf-8")
        reference = ARM["reference/baseline_quadruped_rewards.py"].decode("utf-8")
        added = [line for line in candidate.splitlines() if line not in reference.splitlines()]
        weight_lines = [line for line in added if line.strip().startswith('"')]
        self.assertEqual(len(weight_lines), 1, added)
        self.assertIn(f'"{TERM}"', weight_lines[0])
        self.assertEqual(reward_dict(candidate)[TERM], SPEC["single_change"]["to"])
        self.assertNotIn(TERM, REWARD_NAMES, "a listed name must use change_class reward_weight")
        # the six listed weights are untouched, so nothing else moved
        self.assertEqual({k: v for k, v in reward_dict(candidate).items() if k in REWARD_NAMES},
                         reward_dict(reference))
        trained = reward.BASELINE_SOURCE / "source" / "quadruped_rewards.py"
        self.assertEqual(reward_dict(reference), reward_dict(trained.read_text(encoding="utf-8")),
                         "the reference must be the reward file G-A033 was trained with")
        config = ARM["run_config.env"].decode("utf-8")
        for line in (f"SINGLE_CHANGE_NAME={TERM}", "SINGLE_CHANGE_FROM=-2.5e-07", "SINGLE_CHANGE_TO=-1.25e-07",
                     "TRAIN_SEED=42", "NUM_ENVS=4096", "MAX_ITERATIONS=1000", "EVAL_CHECKPOINT_ITER=900",
                     "BASELINE_LABEL=g_a033"):
            self.assertIn(line + "\n", config)

    def test_4_arm_is_the_builder_output_and_launches_nothing_missing(self) -> None:
        name = f"arms/{SPEC['output']['upload_zip']}"
        self.assertEqual(PAYLOAD[name], reward.build_zip(SPEC))
        self.assertIn(sha(PAYLOAD[name]), PAYLOAD["campaign_config.env"].decode("utf-8"))
        shipped = {k: v for k, v in PAYLOAD.items() if not k.startswith("arms/")}
        self.assertEqual(build.unreachable_scripts(shipped, ARM, SPEC["runner"]), [])

    def test_5_the_value_comes_from_the_probe_grid_and_the_logged_weights(self) -> None:
        self.assertEqual(base_data.spec_problems(SPEC), [])
        self.assertEqual({k: v for k, v in SPEC["base_data"]["walk_margin"].items() if k != "reason"},
                         base_data.expected_base_data(SPEC)["walk_margin"])
        margin = SPEC["base_data"]["walk_margin"]
        self.assertEqual(margin["zone"], "WALK")
        self.assertEqual(margin["unmeasured_in_situations"], [TERM])
        probes = {(r["term"], r["to"]): r for r in mech.read("PROBES.csv")}
        half, double = probes[(TERM, "-1.25e-07")], probes[(TERM, "-5e-07")]
        self.assertEqual((half["zone"], double["zone"]), ("WALK", "STOP"))
        self.assertEqual(half["range_status"], "NEVER_CHANGED")
        derivation = SPEC["value_derivation"]
        self.assertIn(f"{float(half['margin']):+.4f}", derivation["walk_margin"])
        self.assertIn(half["edge_weight"], derivation["walk_margin"])
        # halving moves away from the walking-zone edge, it does not approach it
        self.assertGreater(SPEC["single_change"]["to"], float(half["edge_weight"]))
        self.assertGreater(float(half["margin"]), float(probes[("track_lin_vel_xy_exp", "1.6")]["margin"]),
                           "the spec calls this the largest probe rise")
        # the situation columns are empty for this term: the direction may not be quoted as measured
        situ = {(r["term"], r["to"]): r for r in mech.read("PROBE_SITUATIONS.csv")}[(TERM, "-1.25e-07")]
        self.assertEqual((situ["climb_delta"], situ["sway_delta"], situ["push_delta"]), ("", "", ""))
        self.assertEqual(SPEC["inference"]["predictions"]["sway"]["direction"], "unknown")
        self.assertEqual(SPEC["inference"]["predictions"]["push"]["direction"], "unknown")

    def test_6_the_walking_runs_are_the_ones_that_pay_this_penalty(self) -> None:
        """The chain's raw rows: every walking run's joint acceleration is above every stopped run's."""
        rows = [r for r in mech.read("TERM_VALUES.csv") if r["term"] == TERM]
        walking = [float(r["value"]) for r in rows if r["walking"] == "True"]
        stopped = [float(r["value"]) for r in rows if r["walking"] != "True"]
        self.assertTrue(walking and stopped)
        self.assertGreater(min(walking), max(stopped))
        self.assertEqual(max(walking), max(float(r["value"]) for r in rows))
        baseline_row = next(r for r in rows if r["name"] == "G-A033")
        self.assertEqual(float(baseline_row["weight"]), SPEC["single_change"]["from"])
        for row in SPEC["inference"]["rows"]:
            if row["source"].endswith("TERM_VALUES.csv"):
                self.assertIn(row["value"], [r["value"] for r in rows])
        self.assertEqual(base_data.walking_values(TERM), [SPEC["single_change"]["from"]],
                         "no run has ever trained another value for this term")

    def test_7_no_listed_lever_moved_and_each_says_why(self) -> None:
        base, cand = SPEC["rewards"]["baseline"], SPEC["rewards"]["candidate"]
        for name in REWARD_NAMES:
            with self.subTest(name):
                self.assertEqual(base[name], cand[name])
                self.assertIn(name, SPEC["rejected_alternatives"])
        for name in ("max_iterations", "training_seed"):
            self.assertIn(name, SPEC["rejected_alternatives"], "the R-6-outside options must say why not")

    def test_8_per_scenario_limits_are_twice_the_measured_sd(self) -> None:
        with (GO2 / "reports/runs/BASELINE_MARGIN.csv").open(encoding="utf-8") as handle:
            sd = {r["scenario"]: float(r["value"]) for r in csv.DictReader(handle) if r["metric"] == "delta_resample_sd"}
        limits = SPEC["preregistered"]["max_scenario_weighted_loss_70_by_scenario"]
        for scenario, limit in limits.items():
            with self.subTest(scenario):
                self.assertAlmostEqual(limit, 2 * sd[scenario], places=5)
        self.assertAlmostEqual(SPEC["preregistered"]["max_flat_scenario_proxy_drop"], 2 * sd["G2"] / 10.5, places=3)

    def test_9_the_climb_guard_is_the_falsification_metric(self) -> None:
        guard = SPEC["preregistered"]["climb_guard"]["groups"]
        self.assertEqual(set(guard), {"stairs_10_climb_ge1", "stairs_10_climb_ge2", "stairs_15_climb_ge1"})
        ge1 = guard["stairs_10_climb_ge1"]
        self.assertEqual(ge1["baseline_sum"], sum(ge1["baseline_counts"]))
        falsified = SPEC["inference"]["falsified_if"]
        self.assertIn(str(ge1["baseline_sum"]), falsified)
        self.assertIn(str(ge1["max_drop"]), falsified)
        self.assertIn("stairs_10_climb_ge1", falsified)
        self.assertIn("G5", SPEC["inference"]["risk_axes"])
        self.assertEqual(SPEC["preregistered"]["rule_version"], "fact_rules_v1")

    def test_10_the_earlier_releases_are_untouched(self) -> None:
        self.assertIn(CAMPAIGN_ID, verifier.SPECS)
        self.assertEqual(verifier.load_spec(CAMPAIGN_ID), SPEC)
        for work_id in ("G-A035", "G-A037", "G-A038"):
            with self.subTest(work_id):
                camp = build.CAMPAIGNS[work_id]
                current = GO2 / "upload" / camp["upload_id"] / "current"
                with zipfile.ZipFile(current / camp["upload_zip"]) as archive:
                    shipped = {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()}
                self.assertEqual(shipped, build.build_payload(work_id))
                digest = sha((current / camp["upload_zip"]).read_bytes())
                self.assertEqual(build.run_guide(work_id, digest).encode("utf-8"),
                                 (current / camp["guide"]).read_bytes())

    def test_11_a_listed_reward_may_not_move_in_this_class(self) -> None:
        broken = copy.deepcopy(SPEC)
        broken["rewards"]["candidate"]["lin_vel_z_l2"] = -1.0
        with self.assertRaises(RuntimeError) as caught:
            reward.validate_spec(broken)
        self.assertIn("must not move a listed name", str(caught.exception))
        # and an extra that is a listed name is refused as well
        broken = copy.deepcopy(SPEC)
        broken["rewards"]["candidate_env_extra"] = {"lin_vel_z_l2": -1.0}
        broken["single_change"] = {**SPEC["single_change"], "name": "lin_vel_z_l2", "from": -2.0, "to": -1.0}
        with self.assertRaises(RuntimeError):
            reward.validate_spec(broken)

    def test_12_the_unlisted_term_starts_at_the_isaac_lab_value(self) -> None:
        rough = json.loads((GO2 / "config/go2_external_reference.json").read_text(encoding="utf-8"))
        rough = rough["isaaclab"]["rewards"]["go2_rough"]
        self.assertEqual(float(rough[TERM]), SPEC["single_change"]["from"])
        env = (STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8")
        match = re.search(rf"\n  {TERM}:\n(?:    .*\n)*?    weight: (\S+)\n", env)
        self.assertIsNotNone(match, "the stored baseline env must carry the term")
        self.assertEqual(float(match.group(1)), SPEC["single_change"]["from"],
                         "G-A033 trained at the Isaac Lab value, so that is the baseline")
        self.assertTrue(str(SPEC["external_reference"]["departure_reason"]).strip())


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir() and A017_ARM.is_dir(),
                     "G-A033 or A017 harvest not present")
class GateAndVerifierTest(unittest.TestCase):
    """The server gate and the local verifier read a G-A039 harvest the same way."""

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

    @staticmethod
    def candidate_env() -> str:
        """G-A033's env.yaml with the one weight the runner's training would have written."""
        text = (STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8")
        patched, count = re.subn(rf"(\n  {TERM}:\n(?:    .*\n)*?    weight: )-2\.5e-07\n", r"\g<1>-1.25e-07\n", text)
        assert count == 1, f"{TERM} weight line not found exactly once"
        return patched

    def harvest(self, name: str) -> Path:
        keep = Path(self.tmp.name) / name
        model = b"synthetic G-A039 model"
        model_sha = sha(model)
        single = SPEC["single_change"]
        files = {
            "RESULT_STATUS.txt": "RESULT_STATE=FULL\n",
            "exported/report.html": "<html>synthetic</html>\n",
            "exported/REPORT_STATUS.txt": "REPORT_STATUS=REPORT_ACQUIRED\n",
            "training/TRAIN_STATUS.txt": f"TRAIN_RC=0\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS=1000\n"
                                         f"SINGLE_CHANGE={single['name']}:{single['from']}->{single['to']}\n",
            "training/env.yaml": self.candidate_env(),
            "training/CHECKPOINT_PIN.txt": f"EVAL_CHECKPOINT_ITER=900\nEVAL_CHECKPOINT_SHA={model_sha}\n"
                                           f"REWARD_BEST_MODEL_ITER=950\nREWARD_BEST_MODEL_SHA={'0' * 64}\n",
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
            f"STAGE=target\nCANDIDATE_EVAL_ITER=900\n", encoding="utf-8")
        stored = STORED_ARM / "evaluation" / BASE["stored_label"]
        self.copy_cases(stored, keep / "evaluation" / "candidate",
                        [SPEC["evaluation"]["catastrophe_case"], *reward.targets(SPEC)], model_sha)
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
        self.assertEqual((server["baseline_arm"], local["baseline_arm"]), ("STORED_G-A033", "STORED_G-A033"))
        self.assertTrue(server["sentinel"]["agrees"])
        self.assertEqual((server["verdict"], local["verdict"]), ("FAIL", "FAIL"))
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0, places=12)

    def test_2_a_real_difference_is_read_identically(self) -> None:
        keep = self.harvest("differ")
        self.copy_cases(A017_ARM, keep / "evaluation" / BASE["label"],
                        [SPEC["evaluation"]["catastrophe_case"], *reward.targets(SPEC)], BASE["model_sha256"])
        server = gate.gate(keep, self.stored, SPEC, REGISTRY)
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual((server["baseline_arm"], local["baseline_arm"]), ("REMEASURED_SAME_RUN", "REMEASURED_SAME_RUN"))
        self.assertNotAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0, places=6)
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"],
                               local["target_stage"]["target_mean_proxy_delta"], places=12)
        expected = {"TARGET_PASS": "TARGET_PASS_FULL_STAGE_REQUIRED", "FAIL": "FAIL"}[server["verdict"]]
        self.assertEqual(local["verdict"], expected)

    def test_3_an_unapplied_unlisted_weight_is_caught(self) -> None:
        """The whole arm rests on env_cfg.py applying a name the deployed list does not carry."""
        keep = self.harvest("wrong_weight")
        (keep / "training" / "env.yaml").write_text((STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8"),
                                                    encoding="utf-8", newline="\n")
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["verdict"], "INCONCLUSIVE")
        self.assertTrue(any(f.startswith(f"env_reward_{TERM}") for f in local["artifact_faults"]),
                        local["artifact_faults"])

    def test_4_a_missing_target_case_is_never_a_verdict(self) -> None:
        keep = self.harvest("missing")
        entry = reward.targets(SPEC)[0]
        _scenario, case_id, seed = entry.split(":")
        shutil.rmtree(keep / "evaluation" / "candidate" / "cases" / f"seed_{seed}" / case_id)
        self.assertEqual(gate.gate(keep, self.stored, SPEC, REGISTRY)["verdict"], "UNDECIDED")
        self.assertEqual(verifier.verify(keep, STORED_ARM, SPEC)["verdict"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
