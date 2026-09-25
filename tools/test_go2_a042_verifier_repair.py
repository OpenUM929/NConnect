"""Focused regressions for the G-A042 verifier repair."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as reward  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402


SPEC = reward.load("G-A042")


class RequiredTargetCasesTest(unittest.TestCase):
    def test_required_records_are_part_of_local_target_stage_validation(self) -> None:
        entries = verifier.target_stage_entries(SPEC)
        self.assertEqual(entries[0], SPEC["evaluation"]["catastrophe_case"])
        for entry in SPEC["preregistered"]["required_target_cases"]:
            self.assertIn(entry, entries)

    def test_old_spec_without_required_records_keeps_old_target_list(self) -> None:
        old = copy.deepcopy(SPEC)
        old["preregistered"].pop("required_target_cases")
        old["preregistered"].pop("plan_screening", None)
        self.assertEqual(verifier.target_stage_entries(old),
                         [old["evaluation"]["catastrophe_case"], *verifier.pkg.targets(old)])

    def test_each_and_all_required_records_are_mandatory(self) -> None:
        required = SPEC["preregistered"]["required_target_cases"]
        with tempfile.TemporaryDirectory() as td:
            arm = Path(td)
            for entry in required:
                _scenario, case_id, seed = entry.split(":")
                (arm / "cases" / f"seed_{seed}" / case_id).mkdir(parents=True)
            self.assertEqual(verifier.required_case_presence_faults(arm, SPEC), [])
            for entry in required:
                _scenario, case_id, seed = entry.split(":")
                target = arm / "cases" / f"seed_{seed}" / case_id
                target.rmdir()
                self.assertIn("required_case_absent:" + entry,
                              verifier.required_case_presence_faults(arm, SPEC))
                target.mkdir()
            for entry in required:
                _scenario, case_id, seed = entry.split(":")
                (arm / "cases" / f"seed_{seed}" / case_id).rmdir()
            self.assertEqual(len(verifier.required_case_presence_faults(arm, SPEC)), len(required))


class ScreeningIdentityTest(unittest.TestCase):
    def test_improvement_requires_valid_identity_even_with_identical_numeric_inputs(self):
        # Synthetic numeric control, not a robot-performance claim. Identity uses actual local
        # recovered model/env/pin while the numeric boundary is injected to keep the test small.
        baseline = ROOT / SPEC['baseline']['stored_arm'] / 'evaluation/candidate'
        def rows(improved):
            return {(case, seed): {'missing': [], 'progress_m': 2 if improved else 1,
                    'survival': 1, 'tracking': 1, 'posture_falls': 0,
                    'ge1': 3 if improved else 2, 'ge2': 2 if improved else 1,
                    'stall_share': .1 if improved else .2, 'fingerprint': {}}
                    for case in screening.CASES for seed in screening.SEEDS}
        with patch.object(screening, 'case_rows', side_effect=[rows(False), rows(True)]):
            self.assertEqual(screening.screen(baseline, baseline)['verdict'], screening.PASS)
        with patch.object(screening, 'case_rows', side_effect=[rows(False), rows(True)]), \
             patch.object(screening, '_identity', return_value={key: 'a' * 64 for key in screening.IDENTITY_FIELDS}):
            self.assertEqual(screening.screen(baseline, baseline)['verdict'], screening.INCONCLUSIVE)

    def test_wrong_identity_is_inconclusive_before_numbers_are_read(self) -> None:
        good = {
            "model_sha256": "1" * 64,
            "env_sha256": "2" * 64,
            "evaluator_sha256": "3" * 64,
            "registry_sha256": "4" * 64,
        }
        with tempfile.TemporaryDirectory() as td:
            arm = Path(td)
            (arm / "identity.json").write_text(json.dumps({key: "WRONG" for key in good}), encoding="utf-8")
            faults = screening.identity_faults(arm, good)
        self.assertTrue(faults)
        self.assertTrue(any("model_sha256" in fault for fault in faults))
        self.assertTrue(any("evaluator_sha256" in fault for fault in faults))
        self.assertTrue(any("registry_sha256" in fault for fault in faults))

    def test_well_formed_identity_lie_is_checked_against_recovered_files_and_pin(self) -> None:
        evaluator_sha = hashlib.sha256((GO2 / "go2_eval_telemetry.py").read_bytes()).hexdigest()
        registry_sha = hashlib.sha256((GO2 / "config/go2_self_eval_registry.json").read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            arm = root / "evaluation/candidate"
            training = root / "training"
            arm.mkdir(parents=True)
            training.mkdir()
            (training / "model_best.pt").write_bytes(b"actual model")
            (training / "env.yaml").write_bytes(b"actual env\n")
            (training / "CHECKPOINT_PIN.txt").write_text(
                "EVAL_CHECKPOINT_ITER=899\nEVAL_CHECKPOINT_SHA=" + "9" * 64 + "\n", encoding="utf-8")
            (arm / "identity.json").write_text(json.dumps({
                "model_sha256": "1" * 64, "env_sha256": "2" * 64,
                "evaluator_sha256": evaluator_sha, "registry_sha256": registry_sha}), encoding="utf-8")
            faults = screening.identity_faults(arm, {"checkpoint_iter": 900})
        self.assertIn("identity_model_sha256_differs_from_recovered_artifact", faults)
        self.assertIn("identity_env_sha256_differs_from_recovered_artifact", faults)
        self.assertIn("checkpoint_pin_sha_differs_from_recovered_model", faults)
        self.assertIn("checkpoint_pin_iter_mismatch", faults)

    def test_screen_rejects_missing_and_well_formed_bad_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            baseline, candidate = root / "baseline", root / "candidate"
            baseline.mkdir()
            candidate.mkdir()
            missing = screening.screen(candidate, baseline)
            self.assertEqual(missing["verdict"], screening.INCONCLUSIVE)
            self.assertTrue(missing["identity_faults"])
            lie = {key: "a" * 64 for key in screening.IDENTITY_FIELDS}
            (candidate / "identity.json").write_text(json.dumps(lie), encoding="utf-8")
            (baseline / "identity.json").write_text(json.dumps(lie), encoding="utf-8")
            bad = screening.screen(candidate, baseline)
            self.assertEqual(bad["verdict"], screening.INCONCLUSIVE)
            self.assertTrue(any("local_authority" in fault for fault in bad["identity_faults"]))


class CombinedVerdictTest(unittest.TestCase):
    def test_stationary_collection_decision_is_not_an_artifact_error(self):
        decision = 'CATASTROPHE_STATIONARY_MANDATORY_COLLECTION_COMPLETE'
        facts = {'candidate_model_sha256': 'a' * 64,
                 'runner_status': {'CANDIDATE_EVAL_ITER': '900'}}
        with patch.object(verifier.a030, 'check_artifacts',
                          return_value=(["decision=%r" % decision], facts)), \
             patch.object(verifier.a030, 'read_kv', return_value={
                 'EVAL_CHECKPOINT_ITER': '900', 'EVAL_CHECKPOINT_SHA': 'a' * 64}):
            faults, _ = verifier.check_artifacts(Path('unused'), SPEC)
        self.assertEqual(faults, [])

    def test_inconclusive_identity_dominates_numeric_passes(self) -> None:
        combined = verifier.combined_verdict(
            artifact_faults=[], fact_verdict="QUANT_SUCCESS_VIDEO_REVIEW_PENDING",
            screening_verdict=screening.INCONCLUSIVE)
        self.assertEqual(combined["verdict"], "INCONCLUSIVE")

    def test_screening_failure_dominates_fact_success(self) -> None:
        combined = verifier.combined_verdict(
            artifact_faults=[], fact_verdict="QUANT_SUCCESS_VIDEO_REVIEW_PENDING",
            screening_verdict=screening.FAIL)
        self.assertEqual(combined["verdict"], "FAIL")

    def test_missing_fact_data_dominates_screening_failure(self) -> None:
        combined = verifier.combined_verdict(
            artifact_faults=[], fact_verdict="INCONCLUSIVE", screening_verdict=screening.FAIL)
        self.assertEqual(combined["verdict"], "INCONCLUSIVE")

    def test_old_campaign_without_plan_screening_preserves_fact_verdict(self) -> None:
        combined = verifier.combined_verdict(
            artifact_faults=[], fact_verdict="TARGET_PASS_FULL_STAGE_REQUIRED",
            screening_verdict=None)
        self.assertEqual(combined["verdict"], "TARGET_PASS_FULL_STAGE_REQUIRED")

    def test_artifact_fault_dominates_two_numeric_passes(self) -> None:
        combined = verifier.combined_verdict(
            artifact_faults=["candidate_identity_env_sha256_mismatch"],
            fact_verdict="QUANT_SUCCESS_VIDEO_REVIEW_PENDING", screening_verdict=screening.PASS)
        self.assertEqual(combined["verdict"], "INCONCLUSIVE")

    def test_plan_screening_is_explicitly_versioned(self) -> None:
        self.assertTrue(verifier.plan_screening_active(SPEC))
        old = copy.deepcopy(SPEC)
        old["preregistered"].pop("plan_screening")
        self.assertFalse(verifier.plan_screening_active(old))


if __name__ == "__main__":
    unittest.main()
