"""Local-only tests for H1 report recovery; never launches training."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'workspace/training/humanoid/server_run06_long.sh'
BASH = shutil.which('bash') or 'C:/Program Files/Git/bin/bash.exe'


def shell_path(path):
    value = Path(path).resolve().as_posix()
    return '/' + value[0].lower() + value[2:] if len(value) > 1 and value[1] == ':' else value


class ReportRecoveryTests(unittest.TestCase):
    def run_case(self, mode):
        script = RUNNER.read_text(encoding='utf-8')
        block = script.split('# BEGIN REPORT_RECOVERY:', 1)[1].split('# END REPORT_RECOVERY', 1)[0]
        block = block.split('\n', 1)[1]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            base = Path(tmp)
            source = base / 'training/exported/report.html'
            source.parent.mkdir(parents=True)
            marker = base / 'marker'
            marker.touch()
            os.utime(marker, (200, 200))
            if mode != 'missing':
                source.write_text('report evidence' if mode != 'empty' else '', encoding='utf-8')
                os.utime(source, (100 if mode == 'stale' else 300,) * 2)
            keep = base / '_keep/tuning'
            (keep / 'final').mkdir(parents=True)
            preamble = 'set -euo pipefail\n' + '\n'.join(
                f'{key}="{shell_path(value)}"' for key, value in
                [('ROOT', source.parent.parent), ('KEEP', keep), ('MARKER', marker)])
            result = subprocess.run([BASH, '-c', preamble + '\n' + block + '\necho "$REPORT_STATUS"'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            target = keep / 'exported/report.html'
            if mode == 'fresh':
                self.assertIn('REPORT_ACQUIRED', result.stdout)
                self.assertEqual(target.read_bytes(), source.read_bytes())
                self.assertEqual((keep / 'final/report.html').read_bytes(), source.read_bytes())
            else:
                self.assertIn('REPORT_REQUIRED_NOT_ACQUIRED', result.stdout)
                self.assertFalse(target.exists())

    def test_fresh(self): self.run_case('fresh')
    def test_missing(self): self.run_case('missing')
    def test_empty(self): self.run_case('empty')
    def test_stale(self): self.run_case('stale')
    def test_shell_contract(self):
        data = RUNNER.read_bytes()
        self.assertNotIn(b'\r', data)
        self.assertEqual(subprocess.run([BASH, '-n', shell_path(RUNNER)]).returncode, 0)
        script = data.decode()
        self.assertLess(script.index('# END REPORT_RECOVERY'), script.index('>"$KEEP/SHA256SUMS.txt"'))
        self.assertIn('REPORT_STATUS=$REPORT_STATUS', script)
        self.assertIn('(( TRAIN_RC != 0 )) || TRAIN_RC=3', script)
        self.assertIn('RUN_ID already exists', script)


if __name__ == '__main__': unittest.main()
