"""Validate the conditional reward files, not server execution or performance."""
import ast
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / 'workspace/training/quadruped'
OUT = GO2 / 'upload/G-A029/review'
spec = importlib.util.spec_from_file_location('a029_config', GO2 / 'go2_tuning_config.py')
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)


class DraftContract(unittest.TestCase):
    def test_only_one_change_against_a017(self):
        data = json.loads((OUT / 'GO2_G_A029_ACTION_RATE_M0008_DRAFT.json').read_text())
        b = cfg.reward_dict((OUT / 'GO2_G_A029_A017_BASELINE_quadruped_rewards.py').read_text(encoding='utf-8'))
        c = cfg.reward_dict((OUT / 'GO2_G_A029_ACTION_RATE_M0008_DRAFT_quadruped_rewards.py').read_text(encoding='utf-8'))
        self.assertEqual(b, data['rewards']['baseline'])
        self.assertEqual(c, data['rewards']['candidate'])
        self.assertEqual([k for k in b if b[k] != c[k]], ['action_rate_l2'])
        self.assertEqual((b['action_rate_l2'], c['action_rate_l2']), (-.01, -.008))
        self.assertEqual(c['track_lin_vel_xy_exp'], 1.4)

    def test_no_logic_change_and_valid_python(self):
        template = (GO2 / 'quadruped_rewards.py').read_text(encoding='utf-8')
        weights = cfg.reward_dict(template)
        for p in OUT.glob('*_quadruped_rewards.py'):
            source = p.read_text(encoding='utf-8')
            ast.parse(source)
            self.assertNotIn(b'\r', p.read_bytes())
            self.assertEqual(cfg.render_reward_source(source, weights),
                             cfg.render_reward_source(template, weights))

    def test_not_disguised_as_execution_spec(self):
        data = json.loads((OUT / 'GO2_G_A029_ACTION_RATE_M0008_DRAFT.json').read_text())
        self.assertFalse(data['execution_authorized'])
        self.assertFalse(data['training_authorized'])
        self.assertEqual(data['baseline']['report_read_status'], 'MISSING')
        self.assertNotIn('schema_version', data)
        self.assertTrue(data['report_recovery']['before_evaluation'])
        self.assertTrue(data['report_recovery']['include_in_result_zip_and_sha'])
        self.assertGreaterEqual(len(data['release_blockers']), 4)


if __name__ == '__main__':
    unittest.main()
