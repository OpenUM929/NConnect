import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from tools import build_go2_g_a028_package as b
from tools.test_h1_report_recovery import BASH, shell_path


class P1PackageTests(unittest.TestCase):
    def exercise(self, fail=False):
        with tempfile.TemporaryDirectory(dir=b.ROOT) as tmp:
            root=Path(tmp)
            archive=b.build(root/'current')
            first=archive.read_bytes()
            self.assertEqual(b.build(root/'current').read_bytes(),first)
            with zipfile.ZipFile(archive) as z: z.extractall(root)
            package=root/b.PREFIX
            runner=package/'server_run_GO2_G_A028.sh'
            script=runner.read_text()
            self.assertNotIn('-p train.py',script)
            spec=json.loads((package/'P1_SPEC.json').read_text())
            self.assertEqual(len(spec['cases']),18)
            self.assertFalse(spec['training'])
            # Change only destination constants in the test copy; production paths are immutable.
            keep=root/'keep'
            result=root/'result.zip'
            script=script.replace('/workspace/_keep/GO2_G_A028_P1',shell_path(keep)).replace('/workspace/_keep/GO2_G_A028_RESULT.zip',shell_path(result))
            runner.write_text(script,encoding='utf-8',newline='\n')
            # Refresh test-copy manifest after destination substitution.
            lines=(package/'PACKAGE_SHA256SUMS.txt').read_text().splitlines()
            lines=[f'{b.sha(runner.read_bytes())}  server_run_GO2_G_A028.sh' if line.endswith('  server_run_GO2_G_A028.sh') else line for line in lines]
            (package/'PACKAGE_SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='ascii',newline='\n')
            fake=root/'isaac.sh'
            fake.write_text('''#!/usr/bin/env bash
set -e
shift
if [[ "$1" == play.py ]]; then
  mkdir -p "$NCRC_EVAL_OUT" exported
  printf 'mock video' > exported/play_video.mp4
  printf 'EVAL_RC=0\\nSTEPS=1000\\nROWS=4000\\n' > "$NCRC_EVAL_OUT/STATUS.txt"
  printf 'mock telemetry\\n' > "$NCRC_EVAL_OUT/steps.csv"
  for i in {1..4000}; do echo "$i"; done >> "$NCRC_EVAL_OUT/steps.csv"
  echo '{"schema_version":6,"nonfinite_row_count":0,"posture_fall_verdict_ambiguous":false,"survival_proxy_source":"posture_gate_v2","posture_measured":true,"completed":true,"survival_proxy":1,"tracking_xy_rmse":0,"posture_min_coverage_required":0.99,"posture_coverage":1,"posture_min_env_coverage":1}' > "$NCRC_EVAL_OUT/summary.json"
  exit '''+('9' if fail else '0')+'''
fi
exec "'''+shell_path(sys.executable)+'''" "$@"
''',encoding='utf-8',newline='\n')
            subprocess.run([BASH,'-n',str(runner)],check=True)
            for sh in package.glob('*.sh'): self.assertNotIn(b'\r',sh.read_bytes())
            env=dict(os.environ,PACKAGE_ROOT=shell_path(package),ISAACLAB=shell_path(fake))
            proc=subprocess.run([BASH,str(runner),'--inner'],env=env,capture_output=True,text=True)
            self.assertEqual(proc.returncode,5 if fail else 0,proc.stdout[-3000:]+proc.stderr)
            with zipfile.ZipFile(result) as z:
                videos=[n for n in z.namelist() if n.endswith('/play_video.mp4')]
                self.assertEqual(len(videos),1 if fail else 18)
                self.assertIn('RESULT_STATE='+('PARTIAL' if fail else 'FULL'),z.read('keep/RESULT_STATUS.txt').decode())
                self.assertIn(b'play_video.mp4',z.read('keep/SHA256SUMS.txt'))
            # A second outer launch must refuse existing results without deleting them.
            preserved=result.read_bytes()
            fake_tmux=root/'tmux'
            fake_tmux.write_text('#!/usr/bin/env bash\nexit 1\n',encoding='ascii')
            env['PATH']=str(root)+os.pathsep+env['PATH']
            proc=subprocess.run([BASH,str(runner)],env=env,capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertEqual(result.read_bytes(),preserved)

    def test_complete_mock_replay_and_repeat_guard(self): self.exercise()
    def test_failed_mock_replay_recovers_partial_video(self): self.exercise(True)


if __name__=='__main__': unittest.main()
