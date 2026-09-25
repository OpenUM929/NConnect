"""Read-only recursive ZIP/manifest, LF, shell and single-weight release check."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify(path: Path) -> dict:
    checks = []
    bash = Path('C:/Program Files/Git/bin/bash.exe')
    if not bash.is_file():
        import shutil
        bash = Path(shutil.which('bash') or '')
    def visit(data: bytes, label: str):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None, label
            names = z.namelist()
            assert len(names) == len(set(names)), 'duplicate members'
            assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
            manifests = [n for n in names if n.endswith(('PACKAGE_SHA256SUMS.txt', 'CAMPAIGN_SHA256SUMS.txt'))]
            assert len(manifests) == 1, label
            manifest = manifests[0]
            prefix = manifest.rsplit('/', 1)[0] + '/'
            listed = set()
            for line in z.read(manifest).decode().splitlines():
                digest, rel = line.split('  ', 1)
                member = prefix + rel.removeprefix('./')
                assert hashlib.sha256(z.read(member)).hexdigest() == digest, member
                listed.add(member)
            assert listed == set(names) - {manifest}, 'manifest coverage'
            shells = 0
            for name in names:
                blob = z.read(name)
                if name.endswith('.zip'):
                    visit(blob, label + '!' + name)
                if name.endswith(('.sh', '.env')):
                    assert b'\r' not in blob, 'CR bytes: ' + name
                    env = dict(os.environ)
                    env['PATH'] = str(bash.parent) + os.pathsep + str(bash.parent.parent / 'usr/bin') + os.pathsep + env.get('PATH', '')
                    done = subprocess.run([str(bash), '-n'], input=blob, capture_output=True, env=env)
                    assert done.returncode == 0, (name, done.stderr)
                    shells += 1
            if prefix + 'experiment.json' in names:
                spec = json.loads(z.read(prefix + 'experiment.json'))
                baseline = z.read(prefix + 'reference/baseline_quadruped_rewards.py').decode()
                candidate = z.read(prefix + 'candidate/quadruped_rewards.py').decode()
                changes = [(a, b) for a, b in zip(baseline.splitlines(), candidate.splitlines()) if a != b]
                assert len(baseline.splitlines()) == len(candidate.splitlines()) and len(changes) == 1
                assert all('track_lin_vel_xy_exp' in line for line in changes[0])
                assert '1.5' in changes[0][0] and '1.6' in changes[0][1]
                config = z.read(prefix + 'run_config.env').decode()
                assert 'COLLECT_REQUIRED_ON_STATIONARY=1\n' in config
                runner = z.read(prefix + spec['runner']).decode()
                assert '"$KEEP/exported/report.html"' in runner
                assert 'REPORT_REQUIRED_NOT_ACQUIRED' in runner
                for name in names:
                    if name.startswith(prefix + 'candidate/') and name.endswith('.py') and not name.endswith('/quadruped_rewards.py'):
                        relative = name.removeprefix(prefix + 'candidate/')
                        assert z.read(name) == (ROOT / 'workspace/training/quadruped' / relative).read_bytes(), relative
            checks.append({'zip': label, 'members': len(names), 'manifest_entries': len(listed), 'shell_syntax': shells})
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert path.with_suffix('.zip.sha256').read_text().split()[0] == digest
    visit(path.read_bytes(), path.name)
    return {'status': 'ARTIFACT_VERIFIED', 'sha256': digest, 'archives': checks,
            'scope': 'Package only; no GPU execution, behavior or official result verified.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('zip', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = json.dumps(verify(args.zip), indent=2)
    if args.out:
        args.out.write_text(result + '\n', encoding='utf-8')
    print(result)
