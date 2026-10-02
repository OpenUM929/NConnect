"""Local G-A058 readout. Published v1 thresholds; no training or adoption.

python -B tools/go2_g_a058_readout.py
Completion markers are not an artifact-integrity verdict. Missing/partial
rows never become failures or zero scores. Local policies remain exploratory.
"""
import json
from pathlib import Path
from go2_g_a057_prereg_readout import run_state
from go2_climb_count import count
from go2_dial_hypothesis import posture_falls

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / 'workspace/_keep'
OUT = ROOT / 'workspace/training/quadruped/reports/evidence/go2_g_a058_codex_readout'
KEYS = ('a048_seed42', 'a043_seed43', 'a043_seed44')

def individual(climbs, yaw):
    if climbs is None or yaw is None:
        return 'INCONCLUSIVE_MISSING'
    return 'JOINT_CANDIDATE_FOR_REVIEW' if climbs >= 50 and yaw <= 5 else 'NOT_JOINT_CANDIDATE'

def setting(a, b):
    if a is None or b is None: return 'NOT_YET'
    if min(a, b) >= 50: return 'REPRODUCED'
    if max(a, b) <= 10: return 'DEGRADED'
    return 'INCONCLUSIVE'

def yaw_band(value):
    if value is None: return 'MISSING'
    return 'PROTECTED' if value <= 5 else 'PARTIAL' if value < 15 else 'REPRODUCED'

def read(key, keep=KEEP):
    arm = keep / f'go2_g_a058_{key}'
    out = {'row': key, 'run_state': 'NOT_RECOVERED', 'climb15': None, 'yaw_right': None}
    if not arm.is_dir(): return out
    out['run_state'], out['reason'] = run_state(arm)
    if out['run_state'] != 'COMPLETE': return out
    cases = arm / 'evaluation/candidate/cases'
    summaries = list(cases.glob('seed_*/*/summary.json'))
    if len(summaries) != 69:
        out.update(run_state='INCOMPLETE_DATA', reason=f'{len(summaries)}/69 summaries')
        return out
    climbs, yaw = [], []
    for seed in (101, 202, 303):
        stairs = cases / f'seed_{seed}/stairs_15_down/steps.csv'
        c = count(stairs, .15) if stairs.is_file() else None
        climbs.append(c['ge2'] if c and c['robots'] == 32 and c['direction']=='climb' else None)
        yaw.append(posture_falls(cases / f'seed_{seed}/combined_yaw_right/summary.json', 32))
    total = lambda x: None if any(v is None for v in x) else sum(x)
    out.update(climb15=total(climbs), yaw_right=total(yaw), per_seed={'climb15': climbs, 'yaw_right': yaw})
    out['individual'] = 'REFERENCE_ONLY' if key == KEYS[0] else individual(out['climb15'], out['yaw_right'])
    out['yaw_defect'] = yaw_band(out['yaw_right'])
    out['adoption'] = 'NOT_JUDGED_LOCAL_EXPLORATORY'
    return out

def main():
    rows = {k: read(k) for k in KEYS}
    result = {'scope': 'published exploratory thresholds; not artifact verification or adoption',
              'rules_source': 'G-A058 v1 READOUT / GO2_OTHER_PC_SEQUENCE_PROPOSAL_20260930.md',
              'rows': rows, 'setting_reproducibility': setting(rows[KEYS[1]]['climb15'], rows[KEYS[2]]['climb15']),
              'next': 'Verify newly received A043 seed43/44 artifacts, then rerun; keep G-A057 prereg and local comparison separate.'}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'READOUT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
