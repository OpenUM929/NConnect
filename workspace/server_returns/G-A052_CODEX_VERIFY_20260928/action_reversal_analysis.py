"""Post-hoc command reversals, not a tremor detector or causal onset test."""
import csv
import gzip
import json
import statistics as st
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
B = ROOT / 'workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases/seed_202/rough_lateral'
with (OUT / 'readout/EVENTS_DIAG.csv').open() as f:
    events = {int(r['env_id']): float(r['T']) for r in csv.DictReader(f) if r['case'] == 'rough_lateral'}
data, steps = {}, {}
with gzip.open(B / 'diag.csv.gz', 'rt', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        data.setdefault(int(r['env_id']), {})[int(r['step'])] = r
with (B / 'steps.csv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f):
        steps.setdefault(int(r['env_id']), {})[int(r['step'])] = r
survivors = sorted(set(data) - set(events))
assert len(events) == 8 and len(survivors) == 24
fields = list(data[0][1])
joint_fields = [k for k in fields if k.startswith(('joint_', 'dof_'))]

def delta(r):
    return [float(r[f'action_{i}']) - float(r[f'prev_action_{i}']) for i in range(12)]

def metrics(env, start, end):
    valid = []
    for s, r in steps[env].items():
        if r['terminated'] == '1' or r['truncated'] == '1':
            break
        if start <= float(r['time_s']) < end:
            valid.append(s)
    pairs = [(s-1, s) for s in valid if s-1 in valid]
    if not pairs:
        return {'pairs': 0}
    turns = energy = total = 0
    for a, b in pairs:
        da, db = delta(data[env][a]), delta(data[env][b])
        for x, y in zip(da, db):
            turn = x*y < 0  # exact zero excluded; no fitted amplitude threshold
            turns += turn
            energy += y*y*turn
            total += y*y
    return {'pairs': len(pairs), 'reversal_fraction': turns/(12*len(pairs)),
            'reversal_delta_rms': (energy/(12*len(pairs)))**0.5,
            'all_delta_rms': (total/(12*len(pairs)))**0.5}

rows = []
for e, t in sorted(events.items()):
    windows = [('early', 1., 3.)] if t >= 4 else []
    if t >= 4:
        windows.append(('middle', t-3, t-1))
    windows.append(('last', max(.5, t-1), t))
    for label, start, end in windows:
        m = metrics(e, start, end)
        row = {'env': e, 'T': t, 'window': label, 'start': start, 'end': end, **m}
        if m['pairs']:
            controls = [metrics(v, start, end) for v in survivors]
            assert all(c['pairs'] == m['pairs'] for c in controls)
            for k in ['reversal_fraction', 'reversal_delta_rms', 'all_delta_rms']:
                row[k+'_control_median'] = st.median(c[k] for c in controls)
        rows.append(row)
result = {'classification': 'POST_HOC_DESCRIPTIVE', 'joint_state_fields': joint_fields,
          'dt_s': .02, 'population': '8 failures, 24 survivors; rough_lateral seed202 only',
          'window': 'early [1,3), middle [T-3,T-1) only T>=4; last [max(.5,T-1),T); first episode',
          'metric': 'componentwise consecutive delta sign changes / (12 * pairs); zero excluded; RMS includes all component-pair slots, reversals masked for reversal RMS',
          'limits': 'No tremor cutoff, no causal onset inferred, no terrain/gait matching; same controls reused; no physical joint oscillation claim',
          'rows': rows}
(OUT / 'ACTION_REVERSAL_COMPARISON.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
