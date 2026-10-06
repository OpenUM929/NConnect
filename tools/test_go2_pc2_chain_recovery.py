"""Exercise the real chain body with a fake runner; no Isaac processes started."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAIN = ROOT / 'workspace/_keep/go2_g_a060_pc2_run_chain.sh'


class ChainRecoveryTests(unittest.TestCase):
    def run_chain(self, first=0, second=0, third=0):
        source = CHAIN.read_text(encoding='utf-8')
        body = source[source.index('run_point()'):]
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / 'runner.sh').write_text(
                'echo "VISIT:$2"\ncase "$2" in\n'
                f'a048_seed42) exit {first};;\n'
                f'ang_vel_xy_l2_m0p08) exit {second};;\n'
                f'track_lin_vel_xy_exp_p1p4) exit {third};;\nesac\n',
                encoding='utf-8')
            (p / 'chain.sh').write_text('set -uo pipefail\nR=./runner.sh\n' + body,
                                        encoding='utf-8')
            return subprocess.run(['bash', 'chain.sh'], cwd=p, capture_output=True, text=True)

    def test_success_order(self):
        result = self.run_chain()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([s for s in result.stdout.splitlines() if s.startswith('VISIT:')],
                         ['VISIT:a048_seed42', 'VISIT:ang_vel_xy_l2_m0p08',
                          'VISIT:track_lin_vel_xy_exp_p1p4'])

    def test_baseline_failure_blocks_candidates(self):
        result = self.run_chain(first=30)
        self.assertEqual(result.returncode, 30)
        self.assertEqual(result.stdout.count('VISIT:'), 1)

    def test_second_failure_preserves_requested_third_run(self):
        result = self.run_chain(second=31)
        self.assertEqual(result.returncode, 31)
        self.assertEqual(result.stdout.count('VISIT:'), 3)

    def test_third_failure_is_not_hidden(self):
        self.assertEqual(self.run_chain(third=30).returncode, 30)

    def test_no_broad_kill_or_whole_point_timeout(self):
        source = CHAIN.read_text(encoding='utf-8')
        self.assertNotIn('Stop-Process', source)
        self.assertNotIn('timeout -', source)
        self.assertIn('export PYTHONUNBUFFERED=1', source)
        self.assertEqual(subprocess.run(['bash', '-n', str(CHAIN)]).returncode, 0)


if __name__ == '__main__':
    unittest.main()
