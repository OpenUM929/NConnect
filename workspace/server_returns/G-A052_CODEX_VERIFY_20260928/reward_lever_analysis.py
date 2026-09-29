"""Post-hoc full reward-term comparison; no canonical output or threshold changes."""
import csv
import json
import statistics as st
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import go2_diag_replay_readout as dr
import go2_failure_events as fe
H=ROOT/'workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases'
events=list(csv.DictReader((OUT/'readout/EVENTS_DIAG.csv').open()))
results=[]; phase=[]
for case,seed in dr.CASES:
 p=H/f'seed_{seed}'/case
 _,diag=dr.load_diag(p/'diag.csv.gz'); steps=fe.load(p/'steps.csv')
 survivors=[e for e,s in steps.items() if not fe.classify(s)['channel']]
 keys=[k for k in diag[0][0] if k.startswith('rew_')]
 for event in [e for e in events if e['case']==case]:
  env=int(event['env_id']);t=float(event['T']);hi=round(t/.02)-1;lo=max(24,hi-50)
  if hi<=lo:continue
  for key in keys:
   fm=st.fmean(d[key] for d in diag[env][lo:hi])
   controls=[st.fmean(d[key] for d in diag[e][lo:hi]) for e in survivors]
   results.append(dict(case=case,seed=seed,env=env,T=t,start=(lo+1)*.02,end=hi*.02,n_rows=hi-lo,
    term=key,fail_mean=fm,control_n=len(controls),control_median=st.median(controls),
    control_min=min(controls),control_max=max(controls),
    controls_more_negative=sum(c<fm for c in controls)))
 # Fixed time bins for same-individual low-height sequence. No resetting.
 if case=='rough_lateral':
  for start,end in [(12,13),(13,14),(14,15),(15,16),(16,16.9),(16.9,17.9),(17.9,18.9),(18.9,19.9)]:
   ix=[i for i,r in enumerate(steps[23]) if start<=r['time_s']<end]
   ds=[diag[23][i] for i in ix];ss=[steps[23][i] for i in ix]
   assert all(not r['term'] and not r['trunc'] for r in ss)
   phase.append(dict(start=start,end=end,n=len(ix),root_z_start=ss[0]['root_z'],root_z_end=ss[-1]['root_z'],
     relative_height_start=ss[0]['height_rel'],relative_height_end=ss[-1]['height_rel'],
     vy_mean=st.fmean(r['actual_vy'] for r in ss),
     **{k:st.fmean(d[k] for d in ds) for k in keys}))
dr.write_csv(OUT/'REWARD_MATCHED_WINDOWS.csv',results)
dr.write_csv(OUT/'ENV23_REWARD_PHASES.csv',phase)
meta=dict(classification='POST_HOC_DESCRIPTIVE_NOT_CAUSAL',input='A052 raw diag.csv.gz and steps.csv; source hashes in DIAGNOSTIC_SUPPLEMENT.json',
 units='weighted reward per second; heights world/scanner-relative metres; vy body m/s',
 window='preregistered T, preceding 1 second clipped to t>=0.5; exclude T; early empty env25 omitted',
 control='same case/eval-seed survivors, each averaged in same clock-time window; NOT terrain or gait-phase matched',
 population='46 failure windows; repeated controls not independent; 15cm one survivor; one trained A048 policy',
 interpretation='cost is not torque saturation or evidence that reducing weight improves behavior; zero-weight terms conceal raw values',
 rows=len(results))
(OUT/'REWARD_MATCHED_SEMANTICS.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
for case,seed in dr.CASES:
 print(case)
 for term in ['rew_dof_torques_l2','rew_dof_acc_l2','rew_action_rate_l2']:
  rows=[r for r in results if r['case']==case and r['term']==term]
  print(term,'N',len(rows),'fail_median',st.median(r['fail_mean'] for r in rows),
   'matched_control_median',st.median(r['control_median'] for r in rows),
   'fail_more_cost_count',sum(r['fail_mean']<r['control_median'] for r in rows))
print('ENV23 same time', [r for r in results if r['case']=='rough_lateral' and r['env']==23])
print('ENV23 phases',phase)
