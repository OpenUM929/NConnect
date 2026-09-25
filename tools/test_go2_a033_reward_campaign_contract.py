"""Contract for the G-A037 one-command campaign (G-A033 + lin_vel_z_l2 -2.0 -> -1.0).  Local only.

A package is not ready until the code that will read its harvest has run on one (memory rule
"준비 완료 = 판독 코드를 돌려봤다").  So besides what the builder writes, these tests run the server
gate and the local verifier on synthetic harvests shaped like the runner's output, and check that
the tuning value and every limit come from the files they cite.

    python -m unittest tools.test_go2_a033_reward_campaign_contract
"""
from __future__ import annotations

import copy
import csv
import hashlib
import io
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
import build_go2_basic_motion_pair as pair  # noqa: E402
import build_go2_campaign_package as g_a033_campaign  # noqa: E402
import build_go2_training_length_campaign as build  # noqa: E402
import go2_target_gate as gate  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

CAMPAIGN_ID = "G-A037"
SPEC = reward.load(CAMPAIGN_ID)
BASE = SPEC["baseline"]
STORED_ARM = ROOT / BASE["stored_arm"]
A017_ARM = ROOT / "workspace" / "_keep" / "go2_a017_full_suite" / "evaluation" / "a017"
PAYLOAD = build.build_payload(CAMPAIGN_ID)
ARM = reward.build_payload(SPEC)
REGISTRY = json.loads(ARM["go2_self_eval_registry.json"].decode("utf-8"))
CAMP = build.CAMPAIGNS[CAMPAIGN_ID]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evidence(name: str) -> list[dict[str, str]]:
    with (reward.EVIDENCE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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

    def test_2_server_runner_and_gate_are_what_ran_for_g_a033(self) -> None:
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
        self.assertEqual(ARM[SPEC["runner"]], (GO2 / SPEC["runner"]).read_bytes())

    def test_3_exactly_one_reward_line_moves(self) -> None:
        candidate = ARM["candidate/quadruped_rewards.py"].decode("utf-8")
        reference = ARM["reference/baseline_quadruped_rewards.py"].decode("utf-8")
        differing = [(a, b) for a, b in zip(reference.splitlines(), candidate.splitlines()) if a != b]
        self.assertEqual(len(differing), 1)
        self.assertIn('"lin_vel_z_l2"', differing[0][1])
        self.assertEqual(reward_dict(candidate)["lin_vel_z_l2"], -1.0)
        trained = reward.BASELINE_SOURCE / "source" / "quadruped_rewards.py"
        self.assertEqual(reward_dict(reference), reward_dict(trained.read_text(encoding="utf-8")),
                         "the reference must be the reward file G-A033 was trained with")
        config = ARM["run_config.env"].decode("utf-8")
        for line in ("SINGLE_CHANGE_NAME=lin_vel_z_l2", "SINGLE_CHANGE_FROM=-2.0", "SINGLE_CHANGE_TO=-1.0",
                     "TRAIN_SEED=42", "NUM_ENVS=4096", "MAX_ITERATIONS=1000", "EVAL_CHECKPOINT_ITER=900",
                     "BASELINE_LABEL=g_a033"):
            self.assertIn(line + "\n", config)

    def test_4_arm_is_the_builder_output_and_launches_nothing_missing(self) -> None:
        name = f"arms/{SPEC['output']['upload_zip']}"
        self.assertEqual(PAYLOAD[name], reward.build_zip(SPEC))
        self.assertIn(sha(PAYLOAD[name]), PAYLOAD["campaign_config.env"].decode("utf-8"))
        shipped = {k: v for k, v in PAYLOAD.items() if not k.startswith("arms/")}
        self.assertEqual(build.unreachable_scripts(shipped, ARM, SPEC["runner"]), [])

    def test_5_the_value_is_derived_from_the_climb_table(self) -> None:
        """-1.0 brings the estimated 15cm share back to the 10cm share G-A033 already climbs with."""
        rows = {(r["case"], r["group"]): r for r in evidence("CLIMB_REWARD.csv")
                if r["run"] == BASE["stored_arm"].rsplit("/", 1)[1]}
        climb, stall = rows[("stairs_10_down", "climb")], rows[("stairs_15_down", "stall")]
        gain = float(climb["track_rate"]) - float(stall["track_rate"])
        cost = float(stall["lin_vel_z_rate"]) - float(climb["lin_vel_z_rate"])
        share_10 = cost / gain
        share_15 = share_10 * (15 / 10) ** 2
        self.assertEqual(round(100 * share_10), 34)
        self.assertEqual(round(100 * share_15), 76)
        weight_ratio = SPEC["single_change"]["to"] / SPEC["single_change"]["from"]
        self.assertEqual(round(100 * share_15 * weight_ratio), 38)
        self.assertLess(abs(share_15 * weight_ratio - share_10), 0.05)
        derivation = SPEC["value_derivation"]
        self.assertIn("34%", derivation["measured_10cm_share"])
        self.assertIn("76%", derivation["estimated_15cm_share"])

    def test_6_levers_the_analysis_ruled_out_did_not_move(self) -> None:
        base, cand = SPEC["rewards"]["baseline"], SPEC["rewards"]["candidate"]
        for name in ("ang_vel_xy_l2", "track_lin_vel_xy_exp", "feet_air_time"):
            with self.subTest(name):
                self.assertEqual(base[name], cand[name])
                self.assertIn(name, SPEC["rejected_alternatives"])
        lateral = {r["arm"]: r for r in evidence("LATERAL_BEHAVIOR.csv")
                   if r["case"] == "rough_lateral" and r["run"] in ("go2_a017_full_suite", STORED_ARM.name)}
        self.assertLess(float(lateral["candidate"]["tilt_cos_min_median"]), 0)
        self.assertEqual([int(lateral[a]["terminated"]) for a in ("pilot", "a017", "candidate")], [31, 48, 58])

    def test_7_per_scenario_limits_are_twice_the_measured_sd(self) -> None:
        with (ROOT / "workspace/training/quadruped/reports/runs/BASELINE_MARGIN.csv").open(encoding="utf-8") as h:
            sd = {r["scenario"]: float(r["value"]) for r in csv.DictReader(h) if r["metric"] == "delta_resample_sd"}
        limits = SPEC["preregistered"]["max_scenario_weighted_loss_70_by_scenario"]
        for scenario, limit in limits.items():
            with self.subTest(scenario):
                self.assertAlmostEqual(limit, 2 * sd[scenario], places=5)
        self.assertAlmostEqual(SPEC["preregistered"]["max_flat_scenario_proxy_drop"], 2 * sd["G2"] / 10.5, places=3)

    def test_8_target_groups_are_the_two_holes(self) -> None:
        groups = SPEC["preregistered"]["target_groups"]
        cases = {entry.split(":")[1] for entries in groups.values() for entry in entries}
        self.assertEqual(cases, {"stairs_15_down", "stairs_10_down", "rough_lateral"})
        climb = {r["case"]: r["direction"] for r in evidence("STAIRS_CLIMB.csv")}
        self.assertEqual((climb["stairs_15_down"], climb["stairs_10_down"]), ("climb", "climb"))

    def test_9_the_verifier_accepts_this_arm_and_g_a035_is_untouched(self) -> None:
        self.assertIn(CAMPAIGN_ID, verifier.SPECS)
        self.assertEqual(verifier.load_spec(CAMPAIGN_ID), SPEC)
        self.assertEqual(verifier.load_spec("G-A035")["change_class"], "training_length")
        a035 = build.CAMPAIGNS["G-A035"]
        current = GO2 / "upload" / a035["upload_id"] / "current"
        digest = sha((current / a035["upload_zip"]).read_bytes())
        self.assertEqual(sha(build.build(  # rebuilding G-A035 must reproduce the published bytes
            "G-A035").read_bytes()), digest)
        self.assertEqual(build.run_guide("G-A035", digest).encode("utf-8"), (current / a035["guide"]).read_bytes())

    def test_10_a_second_reward_change_is_refused(self) -> None:
        broken = copy.deepcopy(SPEC)
        broken["rewards"]["candidate"]["ang_vel_xy_l2"] = -0.03
        with self.assertRaises(RuntimeError) as caught:
            reward.validate_spec(broken)
        self.assertIn("single_change", str(caught.exception))


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir() and A017_ARM.is_dir(),
                     "G-A033 or A017 harvest not present")
class GateAndVerifierTest(unittest.TestCase):
    """The server gate and the verifier of record read a G-A037 harvest the same way."""

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
        patched, count = re.subn(r"(\n  lin_vel_z_l2:\n(?:    .*\n)*?    weight: )-2\.0\n", r"\g<1>-1.0\n", text)
        assert count == 1, "lin_vel_z_l2 weight line not found exactly once"
        return patched

    def harvest(self, name: str) -> Path:
        keep = Path(self.tmp.name) / name
        model = b"synthetic G-A037 model"
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

    def test_3_a_wrong_trained_weight_is_caught(self) -> None:
        keep = self.harvest("wrong_weight")
        (keep / "training" / "env.yaml").write_text((STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8"),
                                                     encoding="utf-8", newline="\n")
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["verdict"], "INCONCLUSIVE")
        self.assertTrue(any(f.startswith("env_reward_lin_vel_z_l2") for f in local["artifact_faults"]))

    def test_4_a_missing_target_case_is_never_a_verdict(self) -> None:
        keep = self.harvest("missing")
        shutil.rmtree(keep / "evaluation" / "candidate" / "cases" / "seed_202" / "rough_lateral")
        self.assertEqual(gate.gate(keep, self.stored, SPEC, REGISTRY)["verdict"], "UNDECIDED")
        self.assertEqual(verifier.verify(keep, STORED_ARM, SPEC)["verdict"], "INCONCLUSIVE")

    def test_5_the_per_scenario_limit_bites_where_the_uniform_one_would_not(self) -> None:
        """A G6 loss between twice its own sd (0.862) and the old uniform 2.04 must fail."""
        identity = json.loads((STORED_ARM / "evaluation" / "candidate" / "identity.json").read_text(encoding="utf-8"))
        base = verifier.build_policy(STORED_ARM / "evaluation" / "candidate", verifier.a030.REGISTRY, identity)
        cand = copy.deepcopy(base)
        weight = float(base["scenarios"]["G6"]["weight"])
        cand["scenarios"]["G6"]["scenario_proxy"] -= 1.2 / (weight * 70.0)
        cand["simulation_points_70"] = base["simulation_points_70"] + 3.0
        judged = verifier.judge(base, cand, SPEC["preregistered"])
        self.assertIn("3_non_inferiority", judged["failed"])
        self.assertTrue(any(v.startswith("G6 weighted loss") for v in judged["non_inferiority_violations"]))
        uniform = {k: v for k, v in SPEC["preregistered"].items() if k != "max_scenario_weighted_loss_70_by_scenario"}
        self.assertFalse(any(v.startswith("G6") for v in verifier.judge(base, cand, uniform)["non_inferiority_violations"]))


if __name__ == "__main__":
    unittest.main()
