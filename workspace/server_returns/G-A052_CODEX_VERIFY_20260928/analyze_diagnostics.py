"""Exploratory supplement; no canonical edits or new decision thresholds.
Run from repo root with python -B. Units/selection are recorded in output.
"""
import csv
import hashlib
import json
import math
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import go2_diag_replay_readout as dr
import go2_failure_events as fe

OUT = Path(__file__).resolve().parent
HARVEST = ROOT / 'workspace/_keep/go2_g_a052_a048_diag_replay'
events = list(csv.DictReader((OUT / 'readout/EVENTS_DIAG.csv').open()))
cals = json.loads((OUT / 'readout/CALIBRATION.json').read_text())
summary = {'schema': 'exploratory_diagnostic_supplement_v1',
 'semantics': {'population': 'A048 iter900; one evaluation seed per case, first episode only',
 'windows': 'preregistered [T-1,T); only clipped_order and clipped times use t>=0.5s; all other statistics/controls retain original windows; no relabeling original',
 'units': 'time s; height m; angular velocity body rad/s; foot velocity world m/s; forces world N',
 'support': 'contact_time>0 is contact indicator, NOT proof of load bearing',
 'slip': 'stance foot horizontal speed threshold, NOT proof of frictional slipping',
 'controls': 'same-time survivors, NOT terrain/phase matched; repeated windows not independent',
 'statistics': 'group summaries median of per-env window values; air stats pooled landing events; no causal or score estimate'},
 'cases': {}, 'sources': {}}

def avg(v): return st.fmean(v) if v else None
def stats(rows, feet):
    lands = [(f,d[f+'_last_air_time']) for d in rows for f in feet if d[f+'_first_contact'] == 1]
    speeds = [v for d in rows for _,v in dr.stance_speeds(d,feet)]
    return {'n_rows':len(rows), 'mean_support':avg([dr.support(d,feet) for d in rows]),
       'low_support_fraction':avg([dr.support(d,feet)<=1 for d in rows]),
       'omega_rms':math.sqrt(avg([dr.omega_xy(d)**2 for d in rows])) if rows else None,
       'stance_speed_mean':avg(speeds), 'landings':len(lands),
       'landing_air_mean':avg([a for _,a in lands]),'landing_air_over_05':sum(a>.5 for _,a in lands),
       'action_delta_norm_mean':avg([math.sqrt(sum((d[f'action_{i}']-d[f'prev_action_{i}'])**2 for i in range(12))) for d in rows]),
       **{k:avg([d[k] for d in rows]) for k in rows[0] if k.startswith('rew_')} } if rows else {'n_rows':0}

for (case,seed),cal in zip(dr.CASES,cals):
    p=HARVEST/'diag/cases'/f'seed_{seed}'/case
    fields,diag=dr.load_diag(p/'diag.csv.gz'); steps=fe.load(p/'steps.csv'); feet=dr.feet_of(fields)
    for name in ['steps.csv','diag.csv.gz','diag_meta.json']:
        source=p/name; summary['sources'][str(source.relative_to(ROOT))]=hashlib.sha256(source.read_bytes()).hexdigest()
    ep={e:fe.event_row('A048',seed,e,s,fe.classify(s)) for e,s in steps.items()}
    survivors=[e for e,r in ep.items() if r['outcome']=='SURVIVE']
    selected=[e for e in events if e['case']==case]
    details=[]; matched=[]
    for e in selected:
        en=int(e['env_id']); t=float(e['T']); hi=round(t/.02)-1; lo=max(0,hi-50)
        assert hi<=ep[en]['valid_rows']
        assert all(int(d['step'])==i+1 for i,d in enumerate(diag[en]))
        assert all(not (s['term'] or s['trunc']) for s in steps[en][lo:hi])
        clipped=max(lo,24)
        sensitivity=dr.window_readout(diag[en],clipped,hi,feet,cal)
        details.append({'env':en,'T':t,'n_pre_grace_rows':max(0,min(hi,24)-lo),
          'original_order':e['order'],'clipped_order':sensitivity['order'],
          't_rot_clipped':sensitivity['t_rot'],'t_contact_clipped':sensitivity['t_contact'],
          'slip_foot':e['slip_foot'],'t_support':e['t_support'],
          **stats(diag[en][lo:hi],feet)})
        controls=[dr.window_readout(diag[s],lo,hi,feet,cal) for s in survivors]
        matched.append({'fall_env':en,'T':t,'n_controls':len(controls),'orders':dict(Counter(c['order'] for c in controls)),
            'control_contact_any':sum(c['t_contact'] is not None for c in controls),
            'control_rotation_any':sum(c['t_rot'] is not None for c in controls)})
    med=st.median(float(e['T']) for e in selected); hi=round(med/.02)-1; lo=max(0,hi-50)
    contrast=[{'env':s,**stats(diag[s][lo:hi],feet)} for s in survivors]
    reset_differences=[]
    for en,rs in steps.items():
        end=ep[en]['valid_rows']
        first=fe.event_row('A048',seed,en,rs,fe.classify(rs[:min(end+1,len(rs))]))
        diff={k:[ep[en][k],first[k]] for k in ep[en] if ep[en][k]!=first[k]}
        if diff: reset_differences.append({'env':en,'differences':diff})
        assert all(k=='fall_channel' for k in diff), 'Reset changes event selection/anchor'
    result={'fall_events':details,'same_time_survivor_markers':matched,'median_T_survivor_metrics':contrast,
            'full_rollout_vs_first_episode_label_differences':reset_differences,
            'checks': 'event windows precede first reset; diag steps contiguous; reset label differences do not change anchors'}
    # 15cm survivor is not automatically a climber: report displacement and height.
    result['survivor_displacement']=[{'env':e,'dx_world':steps[e][ep[e]['valid_rows']-1]['root_x']-steps[e][0]['root_x'],
        'dz_world':steps[e][ep[e]['valid_rows']-1]['root_z']-steps[e][0]['root_z']} for e in survivors]
    if case=='rough_lateral':
        en=23; result['env23_timeline']=[]
        for t in [15,16,16.9,17.4,17.88,17.9,18.4,19.9]:
            i=round(t/.02)-1; d=diag[en][i]; s=steps[en][i]
            result['env23_timeline'].append({'t':t,**{k:s[k] for k in ['root_z','terrain_z','height_rel','proj_grav_z','actual_vy']},
                'omega_xy':dr.omega_xy(d),'support':dr.support(d,feet),'sum_foot_force_z':sum(d[f+'_force_z'] for f in feet),
                **{f+'_contact':d[f+'_contact_time'] for f in feet}})
    # Windows at the first stairs encounter, supplement only (same clock, not matched contact phase).
    if case.startswith('stairs'):
        result['approach_windows']=[]
        for en in range(32):
            for a,b in [(1.,2.),(2.,3.)]:
                lo=round(a/.02)-1; hi=min(round(b/.02)-1,ep[en]['valid_rows'])
                if hi<=lo: continue
                ds=diag[en][lo:hi]; ss=steps[en][lo:hi]
                result['approach_windows'].append({'env':en,'outcome':ep[en]['outcome'],'start':a,'end':b,
                    'actual_end':ss[-1]['time_s'],'world_root_dz':ss[-1]['root_z']-ss[0]['root_z'],
                    'world_dx':ss[-1]['root_x']-ss[0]['root_x'],
                    'height_rel_end':ss[-1]['height_rel'], **stats(ds,feet)})
    summary['cases'][case]=result

(OUT/'DIAGNOSTIC_SUPPLEMENT.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
for case,r in summary['cases'].items():
    print(case)
    for group in ['fall_events','median_T_survivor_metrics']:
        rows=r[group]; keys=['mean_support','omega_rms','stance_speed_mean','landing_air_mean','action_delta_norm_mean','rew_ang_vel_xy_l2','rew_feet_air_time','rew_action_rate_l2']
        print(group,len(rows),{k:round(st.median(x[k] for x in rows if x[k] is not None),4) for k in keys})
    print('clipped orders',dict(Counter(x['clipped_order'] for x in r['fall_events'])))
    print('matched controls',r['same_time_survivor_markers'] if case=='rough_lateral' else 'in JSON')
    if 'env23_timeline' in r: print('env23',r['env23_timeline'])
    if case=='stairs_15_down': print('survivor displacement',r['survivor_displacement'])
