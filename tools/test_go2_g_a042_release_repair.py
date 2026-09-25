"""Release-only repair contracts; never write a published output."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_a033_reward_package as reward
import build_go2_training_length_campaign as campaign


class ReleaseRepair(unittest.TestCase):
    def setUp(self):
        self.spec = reward.load("G-A042")

    def test_plan_screening_is_binding_not_record_only(self):
        prereg = self.spec["preregistered"]
        self.assertEqual(prereg["plan_screening"]["version"], "forward_stairs_v1")
        self.assertIn("CRITERION", prereg["required_records"]["stall_time_share"])
        self.assertNotIn("NOT A CRITERION", prereg["required_records"]["stall_time_share"])
        guide = campaign.run_guide("G-A042", "0" * 64)
        self.assertIn("go2_screening_gate.py", guide)
        self.assertIn("go2_stall_diagnostics.py --candidate", guide)
        self.assertIn("통합", guide)

    def test_experimental_observations_are_not_claimed_as_replication(self):
        text = json.dumps(self.spec, ensure_ascii=False)
        self.assertIn("999/900", text)
        self.assertIn("900/900", text)
        self.assertNotIn("only evidence that the arm does not risk a stalled policy", text)
        self.assertNotIn("the loss channel scales with the step", text)

    def test_new_release_identity(self):
        self.assertTrue(self.spec["output"]["release_id"].endswith("staged_v4"))
        self.assertTrue(campaign.CAMPAIGNS["G-A042"]["release_id"].endswith("one_command_v4"))

    def test_stationary_collection_is_enabled_in_generated_config(self):
        self.assertIn("COLLECT_REQUIRED_ON_STATIONARY=1\n", reward.run_config(self.spec))


if __name__ == "__main__":
    unittest.main()
