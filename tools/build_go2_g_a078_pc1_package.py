"""Build a single PC1 1000-iteration trend trial on A077 reward settings."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / 'workspace/training/quadruped'
sys.path.insert(0, str(GO2))
from go2_tuning_config import reward_dict

SOURCE = GO2 / 'upload/G-A077/server/5000/current/GO2_G_A077_SERVER_5000_v2.zip'
KEEP = ROOT / 'workspace/_keep/go2_g_a077_server5000_eval2400'
OUT = GO2 / 'upload/G-A078/current'
PREFIX = 'go2_g_a078_pc1_track_p2p1/'
KEY = 'track_lin_vel_xy_exp_p2p1'
RELEASE = 'GO2_G_A078_PC1_TRACK_P2P1_1000_v1'
BASE = dict(track_lin_vel_xy_exp=2.0, feet_air_time=0.01, lin_vel_z_l2=-3.0,
            ang_vel_xy_l2=-0.05, action_rate_l2=-0.005, flat_orientation_l2=-0.225,
            track_ang_vel_z_exp=0.3)
MODEL = '657d51a2de4553b95aae47b254c74a7063d9b2308ce75b5d360892f5c0e11502'
ENV = '4ad5f81ac9373ec84597f833c2fb93fa2a6395a6daefa3c1225cbf8dee3e4f79'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build():
    expected = SOURCE.with_suffix('.zip.sha256').read_text().split()[0]
    assert sha(SOURCE.read_bytes()) == expected
    oldprefix = 'go2_g_a077_flat_orientation_m0p225/'
    with zipfile.ZipFile(SOURCE) as archive:
        assert archive.testzip() is None
        files = {n[len(oldprefix):]: archive.read(n) for n in archive.namelist()}
    oldarm = 'runs/flat_orientation_l2_m0p225/'
    files = {n.replace(oldarm, f'runs/{KEY}/'): b for n, b in files.items()
             if not n.startswith('shared/baseline/stored_evaluation/')}
    arm = f'runs/{KEY}/'
    identity = json.loads((KEEP / 'evaluation/candidate/identity.json').read_text())
    assert identity['model_sha256'] == MODEL and identity['env_sha256'] == ENV
    for relative, expected_sha in [('training/model_best.pt', MODEL), ('training/env.yaml', ENV)]:
        assert sha((KEEP / relative).read_bytes()) == expected_sha
    assert len(list((KEEP / 'evaluation/candidate/cases').rglob('summary.json'))) == 69
    assert len(list((KEEP / 'evaluation/candidate/videos').rglob('*.mp4'))) == 10
    baseline = (KEEP / 'training/source/quadruped_rewards.py').read_bytes()
    assert reward_dict(baseline.decode('utf-8')) == BASE
    candidate = re.sub(rb'("track_lin_vel_xy_exp"\s*:\s*)2\.0\b', rb'\g<1>2.1', baseline)
    assert candidate != baseline
    candidate_values = {**BASE, 'track_lin_vel_xy_exp': 2.1}
    assert reward_dict(candidate.decode('utf-8')) == candidate_values
    # R-6: every deployment code file except reward weights remains byte-identical.
    for p in (KEEP / 'training/source').rglob('*'):
        if p.is_file():
            rel = p.relative_to(KEEP / 'training/source').as_posix()
            if f'shared/candidate/{rel}' in files and rel != 'quadruped_rewards.py':
                assert files[f'shared/candidate/{rel}'] == p.read_bytes(), rel
    for n in ['shared/candidate/quadruped_rewards.py', arm+'candidate/quadruped_rewards.py']:
        files[n] = candidate
    for n in ['shared/baseline/quadruped_rewards.py', arm+'reference/baseline_quadruped_rewards.py',
              arm+'reference/reward_base_quadruped_rewards.py']:
        files[n] = baseline
    for name in ['model_best.pt', 'env.yaml']:
        files['shared/baseline/exported/'+name] = (KEEP / 'training' / name).read_bytes()
    for name in ['report.html', 'report.html.sha256', 'REPORT_STATUS.txt']:
        files['shared/baseline/exported/'+name] = (KEEP / 'exported' / name).read_bytes()
    for p in (KEEP / 'evaluation/candidate').rglob('*'):
        if p.is_file():
            files['shared/baseline/stored_evaluation/'+p.relative_to(KEEP/'evaluation/candidate').as_posix()] = p.read_bytes()
    cfg = files[arm+'run_config.env'].decode()
    replacements = dict(WORK_ID='G-A078', RUN_ID='train_G-A078-Go2_pc1_track_p2p1_1000',
        EXPERIMENT_SLUG='go2_g_a078_pc1_track_p2p1', KEEP_DIR_NAME='go2_g_a078_pc1_track_p2p1',
        RESULT_ZIP_NAME='GO2_G_A078_PC1_TRACK_P2P1_RESULT.zip',
        DONE_MARKER="'[DONE] GO2_G_A078_PC1_TRACK_P2P1_RESULT_READY'",
        TMUX_NAME='go2_g_a078_pc1_track_p2p1', MAX_ITERATIONS='1000', EVAL_CHECKPOINT_ITER='900',
        SINGLE_CHANGE_NAME='track_lin_vel_xy_exp', SINGLE_CHANGE_FROM='2.0', SINGLE_CHANGE_TO='2.1',
        BASELINE_NAME='G_A077_SERVER2400_REFERENCE', BASELINE_LABEL='g_a077',
        BASELINE_MODEL_SHA=MODEL, BASELINE_ENV_SHA=ENV)
    for name, value in replacements.items():
        cfg, count = re.subn(r'^'+name+r'=.*$', lambda m: name+'='+value, cfg, flags=re.M)
        assert count == 1, name
    files[arm+'run_config.env'] = cfg.encode()
    runnername = 'shared/server_run_go2_candidate_iter_pinned.sh'
    runner = files[runnername].decode().replace('G-A077', 'G-A078').replace('G-A074', 'G-A077')
    # Baseline identity is taken from run_config; remove obsolete hardcoded prose/labels.
    runner = runner.replace('REUSED_G_A074_FULL_NO_RERUN', 'REUSED_G_A077_FULL_NO_RERUN')
    files[runnername] = runner.encode()
    files[arm+'expected_rewards.json'] = (json.dumps({'baseline': BASE, 'candidate': candidate_values}, indent=2)+'\n').encode()
    exp = dict(schema='go2_g_a078_pc1_trend_v1', work_id='G-A078', device='PC1',
        single_change=dict(name='track_lin_vel_xy_exp', before=2.0, after=2.1), rewards=candidate_values,
        training=dict(seed=42, num_envs=4096, max_iterations=1000, from_scratch=True),
        evaluation=dict(checkpoint_iter=900, seeds=[101,202,303], case_count=69, candidate_videos=10),
        baseline=dict(work_id='G-A077', checkpoint_iter=2400, model_sha256=MODEL, env_sha256=ENV,
                      internal_proxy_points_70=63.7827174885, stored_evaluation=True),
        hypothesis='Stronger XY command tracking may improve right lateral tracking and return to zero velocity after pushes.',
        competing_hypothesis='Stronger command priority may reduce terrain adaptation and climbing.',
        cause_limit='Post-push XY error worsened in 11/12 cases; recovery was slower. Physical cause is unresolved.',
        value_design='5% exploratory increase, OUT_OF_RANGE against deployment guidance and prior matched trials; not an optimum or safety claim.',
        counterevidence='A042 track 1.5->1.6 lost stairs and rough survival on a different baseline.',
        external_reference='GO2_REWARD_EVIDENCE_MASTER.md section 1-b: Isaac Lab rough track=1.5 is a reference, not an optimum.',
        source_refs=['GO2_TUNING_ANALYSIS_BRIEF.md','workspace/training/quadruped/reports/GO2_LECTURE_REWARD_REFERENCE.md',
                     'workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md'],
        decision=dict(mode='exploratory_trend_only', success='G2 right lateral XY RMSE and G6 post-push XY RMSE/recovery improve in at least 2/3 seeds; inspect every loss and G3/G5 preservation separately.',
            failure='Target errors worsen in all three seeds or stair/rough loss outweighs target benefit; preserve A077 and do not auto-increase.',
            inconclusive='Incomplete artifacts, nonfinite training, or mixed target outcomes. Different device and training length preclude isolated reward-causal claims.',
            adoption='No performance promotion from this 1000-iteration trial alone.',
            next='Read results before any further training; no automatic escalation.'),
        required=['training bundle/source/config/checkpoint/tfevents/log','original report.html and SHA','69 cases steps.csv/summary.json and identity','10 videos','result ZIP and SHA'],
        early_stop='Existing nonfinite catastrophe safety stop; recover partial artifacts, do not auto-retry.')
    files[arm+'experiment.json'] = (json.dumps(exp, ensure_ascii=False, indent=2)+'\n').encode()
    files[arm+'README.txt'] = b'G-A078 PC1: A077 rewards, track 2.0->2.1 only; scratch 1000, evaluate 900. Trend only.\n'
    files['README.txt'] = files[arm+'README.txt']
    files['points.txt'] = f'{KEY} go2_g_a078_pc1_track_p2p1 GO2_G_A078_PC1_TRACK_P2P1_RESULT.zip\n'.encode()
    files['point_config.env'] = b'POINT_WORK_ID=G-A078\nPOINT_STATUS_DIR_NAME=go2_g_a078_pc1_track_p2p1\nPOINT_WORK_DIR=/workspace/go2_g_a078_pc1_track_p2p1_work\nPOINT_TMUX_NAME=go2_g_a078_pc1_track_p2p1\n'
    files['run_point.sh'] = files['run_point.sh'].replace(b'PC2', b'PC1')
    files['run_all.sh'] = ('#!/usr/bin/env bash\nset -euo pipefail\nROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)\nbash "$ROOT_DIR/run_point.sh" --inner '+KEY+'\n').encode()
    materialized = {}
    for n,b in files.items():
        if n.startswith('shared/'): materialized[n[7:]] = b
        elif n.startswith(arm): materialized[n[len(arm):]] = b
    materialized.pop('PACKAGE_SHA256SUMS.txt', None)
    files[arm+'PACKAGE_SHA256SUMS.txt'] = ''.join(f'{sha(b)}  {n}\n' for n,b in sorted(materialized.items())).encode()
    files.pop('SHA256SUMS.txt', None)
    files['SHA256SUMS.txt'] = ''.join(f'{sha(b)}  {n}\n' for n,b in sorted(files.items())).encode()
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (RELEASE+'.zip')
    assert not target.exists(), 'Published release is immutable'
    with tempfile.TemporaryDirectory() as tmp:
        for n,b in files.items():
            if n.endswith(('.sh','.env')):
                assert b'\r' not in b, n
            if n.endswith('.sh'):
                p = Path(tmp) / Path(n).name
                p.write_bytes(b)
                subprocess.run(['C:/Program Files/Git/bin/bash.exe','-n',str(p)],check=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for n,b in sorted(files.items()):
            info = zipfile.ZipInfo(PREFIX+n, (2026,10,12,0,0,0))
            info.compress_type = zipfile.ZIP_STORED if n.endswith(('.pt','.mp4')) else zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if n.endswith('.sh') else 0o644)<<16
            z.writestr(info,b)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for n,b in files.items(): assert sha(z.read(PREFIX+n)) == sha(b)
    digest = sha(target.read_bytes())
    target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n',encoding='utf-8')
    (OUT/'quadruped_rewards.py').write_bytes(candidate)
    (OUT/'experiment.json').write_bytes(files[arm+'experiment.json'])
    (OUT/'CURRENT_UPLOAD.txt').write_text(target.name+'\n'+target.name+'.sha256\n',encoding='utf-8')
    (OUT/'LOCAL_VALIDATION.json').write_text(json.dumps(dict(status='ARTIFACT_VERIFIED', files=len(files), sha256=digest,
        single_reward_diff=['track_lin_vel_xy_exp: 2.0 -> 2.1'], deployment_code_unchanged=True,
        LF=True, bash_n=True, zip_CRC=True, all_member_SHA=True, max_iterations=1000, eval_checkpoint=900),indent=2)+'\n')
    print(json.dumps(dict(path=str(target),bytes=target.stat().st_size,sha256=digest)))

if __name__ == '__main__': build()
