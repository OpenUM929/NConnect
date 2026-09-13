"""Local shell fixtures; no simulator or training is started."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from tools.test_h1_report_recovery import BASH, ROOT, shell_path

RUNNER = ROOT / 'workspace/training/quadruped/server_run_go2_tuning_engine_v1.sh'


class Go2ReportRecoveryTests(unittest.TestCase):
    def exercise(self, mode):
        text = RUNNER.read_text(encoding='utf-8')
        block = text.split('# BEGIN GO2_REPORT_RECOVERY\n')[1].split('# END GO2_REPORT_RECOVERY')[0]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            base = Path(tmp)
            source = base / 'candidate/exported/report.html'
            source.parent.mkdir(parents=True)
            marker = base / 'start'
            marker.touch()
            os.utime(marker, (1700000200, 1700000200))
            if mode != 'missing':
                source.write_bytes(b'' if mode == 'empty' else b'<html>server report</html>')
                os.utime(source, ((1700000100 if mode == 'stale' else 1700000300),) * 2)
            keep = base / 'keep'
            command = (f'KEEP="{shell_path(keep)}"; CANDIDATE_ROOT="{shell_path(source.parent.parent)}"; '
                       f'TRAIN_START_MARKER="{shell_path(marker)}";\n' + block + '\nrecover_training_report\n')
            result = subprocess.run([BASH, '-c', command], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0 if mode == 'fresh' else 4, result.stderr)
            status = (keep / 'exported/REPORT_STATUS.txt').read_text()
            self.assertIn('REPORT_ACQUIRED' if mode == 'fresh' else 'REPORT_REQUIRED_NOT_ACQUIRED', status)
            if mode == 'fresh':
                copied = keep / 'exported/report.html'
                self.assertEqual(copied.read_bytes(), source.read_bytes())
                digest = hashlib.sha256(copied.read_bytes()).hexdigest()
                self.assertIn(digest, (keep / 'exported/report.html.sha256').read_text())
                checksum = subprocess.run([BASH, '-c', f'export PATH=/usr/bin:$PATH; cd "{shell_path(keep)}" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt'], capture_output=True)
                self.assertEqual(checksum.returncode, 0)
                import sys
                archive = base / 'result.zip'
                subprocess.run([sys.executable, str(ROOT / 'workspace/training/quadruped/package_go2_result.py'), str(keep), str(archive)], check=True)
                with zipfile.ZipFile(archive) as z:
                    self.assertEqual(z.read('keep/exported/report.html'), source.read_bytes())
                    self.assertIn(b'exported/report.html', z.read('keep/SHA256SUMS.txt'))

    def test_fresh(self): self.exercise('fresh')
    def test_missing(self): self.exercise('missing')
    def test_empty(self): self.exercise('empty')
    def test_stale(self): self.exercise('stale')

    def test_runner_contract(self):
        data = RUNNER.read_bytes()
        self.assertNotIn(b'\r', data)
        subprocess.run([BASH, '-n', str(RUNNER)], check=True)
        text = data.decode()
        self.assertIn('touch "$TRAIN_START_MARKER"', text)
        self.assertIn('sha256sum -c report.html.sha256', text)
        self.assertLess(text.index('recover_training_report || exit 4'), text.index('CANDIDATE_MODEL='))


if __name__ == '__main__': unittest.main()
