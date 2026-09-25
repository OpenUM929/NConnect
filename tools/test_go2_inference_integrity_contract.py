"""Regression checks for evidence attribution and exploratory recommendations."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import test_go2_detectability_gate as gate


class InferenceIntegrityTest(unittest.TestCase):
    def test_csv_cells_bind_exactly_to_one_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "rows.csv").write_text("run,seed,score,other\nA,101,1.5,9.8\nA,202,11.5,9.8\n", encoding="utf-8")
            row = {"source": "rows.csv", "key": "A,101", "value": "1.5", "reads": "score",
                   "selector": {"run": "A", "seed": "101"}, "cells": {"score": "1.5"}}
            bad_rows = [
                {**row, "value": "9.8", "cells": {"score": "9.8"}},
                {**row, "selector": {"run": "A", "seed": "202"}},
                {**row, "selector": {"run": "A"}},
                {**row, "cells": {"missing": "1.5"}},
                {**row, "selector": {"run": "absent"}},
                {k: v for k, v in row.items() if k != "selector"},
            ]
            with patch.object(gate, "QUAD", root):
                gate._check_rows(self, "good", [row])
                for bad in bad_rows:
                    with self.subTest(bad=bad), self.assertRaises(AssertionError):
                        gate._check_rows(self, "bad", [bad])

    def test_csv_duplicate_headers_and_records_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = {"source": "rows.csv", "key": "A", "value": "1.5", "reads": "score",
                   "selector": {"run": "A"}, "cells": {"score": "1.5"}}
            for data in ("run,score,score\nA,1.5,9.8\n", "run,score\nA,1.5\nA,1.5\n",
                         "run,score\nA,1.5,extra\n"):
                (root / "rows.csv").write_text(data, encoding="utf-8")
                with patch.object(gate, "QUAD", root), self.subTest(data=data), self.assertRaises(AssertionError):
                    gate._check_rows(self, "bad", [row])

    def test_healthy_execution_candidates_pass_common_checks(self):
        from tools.go2_role_regression import healthy_base
        methods = [method for method in dir(gate.InferenceChainGateTest)
                   if method.startswith(("test_10_", "test_11_", "test_12_", "test_15_", "test_16_"))]
        for status in ("RECOMMENDED", "INFORMATION_RUN"):
            spec = healthy_base()
            spec["work_id"] = "G-A999"
            spec["inference"]["status"] = status
            for method in methods:
                with patch.object(gate, "_new_specs", return_value=[(Path("healthy.json"), spec)]):
                    result = unittest.TestResult()
                    gate.InferenceChainGateTest(method).run(result)
                with self.subTest(status=status, method=method):
                    self.assertTrue(result.wasSuccessful(), str(result.failures + result.errors))

    def test_information_run_requires_counterevidence_response(self):
        block = {"status": "INFORMATION_RUN", "contradicting": [{"key": "adverse"}]}
        with self.assertRaises(AssertionError):
            gate._check_recommendation(self, "bad", block)
        gate._check_recommendation(self, "good", {**block, "exploratory": True,
            "counterevidence_response": "Measure the competing explanation.", "falsified_if": "Guard fails."})

    def test_information_run_cannot_skip_common_checks(self):
        methods = (
            "test_10_a_recommendation_is_newer_than_every_executed_run",
            "test_11_only_a_reward_weight_change_can_be_recommended",
            "test_15_a_recommendation_that_leans_on_an_open_decision_must_name_it",
            "test_16_a_recommendation_stands_on_an_analyst_readout",
            "test_12_a_recommendation_cites_the_run_ledger",
        )
        spec = {"work_id": "G-A001", "change_class": "training_length",
                "inference": {"status": "INFORMATION_RUN", "rows": []}}
        for method in methods:
            # The open-decision test needs a class with a known decision hook.
            candidate = {**spec, "change_class": "env_reward_weight"} if "test_15" in method else spec
            case = gate.InferenceChainGateTest(method)
            with patch.object(gate, "_new_specs", return_value=[(Path("probe.json"), candidate)]):
                result = unittest.TestResult()
                case.run(result)
            with self.subTest(method=method):
                self.assertTrue(result.failures, "INFORMATION_RUN bypassed " + method)
                self.assertFalse(result.errors)

    def test_csv_value_from_another_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "rows.csv").write_text("run,score\nA,1.5\nB,9.8\n", encoding="utf-8")
            row = {"source": "rows.csv", "key": "A,", "value": "9.8", "reads": "claim",
                   "selector": {"run": "A"}, "cells": {"score": "9.8"}}
            with patch.object(gate, "QUAD", root):
                with self.assertRaises(AssertionError):
                    gate._check_rows(self, "bad", [row])
                gate._check_rows(self, "good", [{**row, "value": "1.5", "cells": {"score": "1.5"}}])

    def test_exploratory_recommendation_can_preserve_counterevidence(self):
        block = {"status": "RECOMMENDED", "contradicting": [{"key": "adverse"}],
                 "exploratory": True, "counterevidence_response": "Test competing explanations; do not promote yet.",
                 "falsified_if": "Reject if the preregistered stair guard fails."}
        gate._check_recommendation(self, "exploratory", block)

    def test_unanswered_counterevidence_cannot_be_recommended(self):
        with self.assertRaises(AssertionError):
            gate._check_recommendation(self, "bad", {
                "status": "RECOMMENDED", "contradicting": [{"key": "adverse"}]})


if __name__ == "__main__":
    unittest.main()
