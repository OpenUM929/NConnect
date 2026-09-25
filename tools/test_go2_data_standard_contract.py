"""Data semantics and lossless migration tests, not reward-effect validation."""
import copy
import math
import unittest

from tools import go2_standardize_evidence as standard


class DataStandardTest(unittest.TestCase):
    def test_all_original_cells_are_preserved_with_explicit_meaning(self):
        sources = [standard.ROOT / d["source"] for d in standard.load_dictionary()["datasets"].values()]
        before = {str(p): standard.sha(p) for p in sources}
        result = standard.build()
        self.assertEqual(before, {str(p): standard.sha(p) for p in sources})
        self.assertEqual(len(result["datasets"]), 5)
        for dataset in result["datasets"]:
            definition = result["dictionary"]["datasets"][dataset["id"]]
            original = standard.read_rows(standard.ROOT / definition["source"])
            self.assertEqual(len(original), len(dataset["records"]))
            for raw, record in zip(original, dataset["records"]):
                for column, spec in definition["metrics"].items():
                    value = record["metrics"][spec["canonical_name"]]
                    self.assertEqual(value["raw_value"], raw[column])
                    self.assertEqual(value["status"], "MISSING" if raw[column] == "" else "PRESENT")
                    self.assertEqual(value["value"] is None, raw[column] == "")
                    self.assertTrue(value["reason"] if raw[column] == "" else True)
                    for field in ("unit", "formula", "population", "window", "aggregation", "kind", "limitations"):
                        self.assertTrue(spec[field], (dataset["id"], column, field))

    def test_published_view_matches_current_dictionary_and_sources(self):
        import json
        self.assertEqual(json.loads(standard.OUTPUT.read_text(encoding="utf-8")), standard.build())

    def test_legacy_names_cannot_masquerade_as_exact_rewards(self):
        definitions = standard.load_dictionary()["datasets"]
        tilt = definitions["tilt"]["metrics"]
        self.assertEqual(tilt["terminated"]["canonical_name"], "base_contact_env_count")
        for term in ("lin_vel_z_l2", "ang_vel_xy_l2", "flat_orientation_l2"):
            self.assertEqual(definitions["situations"]["metrics"][term]["kind"], "SURROGATE")
        self.assertEqual(definitions["probes"]["metrics"]["sway_delta"]["kind"], "COUNTERFACTUAL")
        self.assertIn("whole", tilt["tilt_survivors"]["window"])
        self.assertIn("end-1.0", tilt["tilt_pre_term"]["window"])

    def test_ambiguous_or_invalid_tables_fail_closed(self):
        spec = standard.load_dictionary()["datasets"]["tilt"]
        rows = standard.read_rows(standard.ROOT / spec["source"])
        with self.assertRaises(ValueError):
            standard.normalize(spec, rows + [rows[0]])
        for value in ("nan", "inf", "not-a-number"):
            bad = copy.deepcopy(rows)
            bad[0]["tilt_mean"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                standard.normalize(spec, bad)
        bad = copy.deepcopy(rows)
        bad[0]["undeclared"] = "3"
        with self.assertRaises(ValueError):
            standard.normalize(spec, bad)

    def test_missing_semantics_are_rejected_before_publication(self):
        original = standard.load_dictionary()["datasets"]["tilt"]
        rows = standard.read_rows(standard.ROOT / original["source"])
        for field in ("unit", "formula", "population", "window", "aggregation",
                      "kind", "limitations", "missing_reason", "canonical_name"):
            for replacement in (None, "", "   "):
                spec = copy.deepcopy(original)
                if replacement is None:
                    del spec["metrics"]["tilt_mean"][field]
                else:
                    spec["metrics"]["tilt_mean"][field] = replacement
                with self.subTest(field=field, replacement=replacement):
                    with self.assertRaises(ValueError):
                        standard.normalize(spec, rows)
        spec = copy.deepcopy(original)
        spec["metrics"]["tilt_mean"]["kind"] = "PROVEN_IMPROVEMENT"
        with self.assertRaises(ValueError):
            standard.normalize(spec, rows)

    def test_dataset_contract_rejects_ambiguous_dimensions(self):
        original = standard.load_dictionary()["datasets"]["tilt"]
        rows = standard.read_rows(standard.ROOT / original["source"])
        for keys in ([], ["name", "name"], original["keys"] + ["tilt_mean"]):
            spec = copy.deepcopy(original)
            spec["keys"] = keys
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                standard.normalize(spec, rows)
        for field in ("source", "producer", "population", "window",
                      "aggregation", "limitations", "identity_status"):
            spec = copy.deepcopy(original)
            spec[field] = ""
            with self.subTest(field=field), self.assertRaises(ValueError):
                standard.normalize(spec, rows)

    def test_formula_counterexamples_prevent_false_equivalence(self):
        # Constant tilt magnitude can rotate around gravity: d(tilt)/dt=0
        # does not imply body omega_x^2+omega_y^2=0.
        omega_xy_squared = math.sin(math.radians(20)) ** 2
        self.assertGreater(omega_xy_squared, 0)
        self.assertEqual((math.radians(20)-math.radians(20))**2, 0)
        # Non-unit gravity invalidates gx²+gy² == 1-gz².
        self.assertNotEqual(0.2**2 + 0.3**2, 1-(-0.8)**2)

    def test_known_case_keeps_population_and_channel_distinctions(self):
        datasets = {d["id"]: d for d in standard.build()["datasets"]}
        tilt = next(r for r in datasets["tilt"]["records"]
                    if r["dimensions"] == {"name": "G-A033", "case": "rough_lateral", "seed": "101"})
        self.assertEqual(tilt["metrics"]["base_contact_env_count"]["value"], 19)
        self.assertEqual(tilt["metrics"]["base_contact_gravity_z_surrogate_prewindow_mean"]["value"], .31123)
        stairs = next(r for r in datasets["fall_channels"]["records"]
                      if r["dimensions"] == {"arm": "A033", "case": "stairs_10_down", "seed": "101"})
        self.assertEqual(stairs["metrics"]["tilt_only_hold_env_count"]["value"], 0)
        self.assertEqual(stairs["metrics"]["both_channel_hold_env_count"]["value"], 1)


if __name__ == "__main__":
    unittest.main()
