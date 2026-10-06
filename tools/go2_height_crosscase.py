"""Read-only input audit: initial upright height and rough/stair outcomes.

Outputs descriptive summaries, not causal tests. Missing cases stay missing.
Height is root_z minus scanner-area mean terrain_z, not foot clearance.
"""
import csv
import json
import statistics as st
from pathlib import Path
from go2_climb_count import alive_rows, gained_steps
from go2_dial_hypothesis import posture_falls

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / 'workspace/_keep'
OUT = ROOT / 'workspace/training/quadruped/reports/evidence/go2_height_crosscase_20261001'
IDS = ('033', '038', '041', '042', '043', '044', '047', '048', '049', '050', '055')
ARMS = {f'A{i}': next(KEEP.glob(f'go2_g_a{i}_*')) for i in IDS}
ARMS.update(PC_A048=KEEP/'go2_g_a058_a048_seed42', PC_track12=KEEP/'go2_g_a057_track_lin_vel_xy_exp_p1p2')
CASES = ('rough_lateral', 'rough_forward', 'stairs_10_down', 'stairs_15_down')

def med(values):
    return st.median(values) if values else None

def run():
    records, summaries = [], []
    max_error = 0
    for arm, path in ARMS.items():
        for case in CASES:
            seed_summaries = []
            group = []
            for seed in (101, 202, 303):
                folder = path/'evaluation/candidate/cases'/f'seed_{seed}'/case
                if not (folder/'steps.csv').exists() or not (folder/'summary.json').exists():
                    continue
                info = json.loads((folder/'summary.json').read_text(encoding='utf-8'))
                info['audit_falls'] = posture_falls(folder/'summary.json', 32)
                seed_summaries.append(info)
                for env, rows in alive_rows(folder/'steps.csv').items():
                    for r in rows:
                        if r['height_rel'] and r['terrain_z']:
                            max_error = max(max_error, abs(float(r['height_rel'])-float(r['root_z'])+float(r['terrain_z'])))
                    # Restrict to upright readings before the first non-upright
                    # reading at/after 1 s. This is a descriptive censor, not a fall gate.
                    early = []
                    for r in rows:
                        t = float(r['time_s'])
                        if t < 1: continue
                        if t >= 3 or r['upright'] != '1': break
                        early.append(r)
                    rec = dict(arm=arm, case=case, seed=seed, env=env,
                               early_samples=len(early), early_h=None, early_z=None,
                               early_ground=None, early_speed=None, ge2=None, preedge_h=None)
                    if len(early) >= 25:
                        for key, source in [('early_h','height_rel'), ('early_z','root_z'), ('early_ground','terrain_z'), ('early_speed','speed_xy')]:
                            rec[key] = med([float(r[source]) for r in early])
                    if case.startswith('stairs'):
                        height = .10 if '10' in case else .15
                        rec['ge2'] = int(gained_steps(rows, 'climb', height) >= 2)
                        baseline = float(rows[min(50, len(rows)-1)]['terrain_z'])
                        edge = next((i for i in range(50,len(rows)) if float(rows[i]['terrain_z'])-baseline > .5*height), None)
                        if edge is not None:
                            win = rows[max(0,edge-25):edge]
                            if len(win)==25 and all(r['upright']=='1' for r in win):
                                rec['preedge_h']=med([float(r['height_rel']) for r in win])
                    records.append(rec)
                    group.append(rec)
            if not seed_summaries: continue
            out = dict(arm=arm, case=case, seeds=len(seed_summaries), envs=len(group),
                       falls=sum(s['audit_falls'] for s in seed_summaries) if all(s['audit_falls'] is not None for s in seed_summaries) else None,
                       summary_h=st.fmean(s['height_rel_median'] for s in seed_summaries),
                       early_n=sum(r['early_h'] is not None for r in group),
                       ge2=sum(r['ge2'] or 0 for r in group) if case.startswith('stairs') else None)
            for key in ('early_h','early_z','early_ground','early_speed'):
                out[key]=med([r[key] for r in group if r[key] is not None])
            for success in (0,1):
                for key in ('early_h','preedge_h'):
                    vals=[r[key] for r in group if r['ge2']==success and r[key] is not None]
                    out[f'{key}_ge2_{success}']=med(vals)
                    out[f'{key}_ge2_{success}_n']=len(vals)
            summaries.append(out)
            print(arm,case,'n',out['early_n'],'h',out['early_h'],'falls',out['falls'],'ge2',out['ge2'],flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    for name, data in [('PER_ENV.csv',records),('SUMMARY.csv',summaries)]:
        with (OUT/name).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
    print('MAX_HEIGHT_ARITHMETIC_ERROR',max_error)
    assert max_error < 1e-9

if __name__=='__main__': run()
