import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.read_h1_ha002_result import compare


class MatchedReadoutTest(unittest.TestCase):
    def test_no_promotion_when_speed_and_protection_fail(self):
        cases = ['plane_vx0p75', 'plane_vx1p00', 'plane_vx1p25',
                 'rough_vx0p75', 'rough_vx1p00', 'turn_vx0p50_L',
                 'turn_vx0p50_R', 'turn_vx1p00_L', 'turn_vx1p00_R']
        cases += [f'H_case_{i}' for i in range(10)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for arm in ('control', 'candidate'):
                for seed in (101, 202, 303):
                    for case in cases:
                        folder = root / arm / 'evaluation' / f'seed_{seed}' / case
                        folder.mkdir(parents=True)
                        (folder / 'steps.csv').touch()
                        (folder / 'summary.json').write_text(json.dumps({'completed': True, 'rows': 32000}))

            def metrics(csv):
                candidate = 'candidate' in csv.parts
                return {'envs': 32, 'falls': 0, 'vx_ratio': .8 if candidate else 1.,
                        'xy_rmse': 2. if candidate else 1., 'yaw_rmse': 1.}

            with patch('tools.read_h1_ha002_result.case_metrics', side_effect=metrics):
                result = compare(root)
            self.assertEqual('INTERNAL_GATE_FAIL', result['direction_gate'])
            self.assertEqual([], result['improved_families'])
            self.assertEqual(57, len(result['protection_violations']))
            self.assertEqual({'plane': None, 'rough': None, 'turn': None}, result['highest']['candidate'])
            (root / 'control/evaluation/seed_101/plane_vx0p75/summary.json').write_text('{"completed":false,"rows":32000}')
            with patch('tools.read_h1_ha002_result.case_metrics', side_effect=metrics):
                with self.assertRaisesRegex(ValueError, 'Incomplete'):
                    compare(root)


if __name__ == '__main__':
    unittest.main()
