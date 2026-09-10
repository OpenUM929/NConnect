import ast,json,sys,tempfile,csv,re,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
p=Path('tools/test_go2_harvest_verifier_contract.py').resolve()
t=ast.parse(p.read_text(encoding='utf-8'));nodes=[]
for n in t.body:
 if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)):nodes.append(n)
 elif isinstance(n,(ast.Assign,ast.AnnAssign)):
  names=[x.id for x in ast.walk(n) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Store)]
  if any(x in names for x in ['ROOT','REGISTRY','FAILURES','NUM_ENVS','STEPS','STEP_DT']):nodes.append(n)
ns={'__file__':str(p)};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
vh=ns['vh'];reg=json.loads(ns['REGISTRY'].read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='codex_r5_') as d:
 root=Path(d);ns['build_harvest'](root,reg);target=ns['a017_case'](root)
 def verdict(label):
  r=ns['run'](root,reg);print(label,r['verdict'],ns['faults_of'](r),r['mismatches'])
 verdict('CLEAN_SYNTHETIC_3_STEPS')
 raw=(target/'steps.csv').read_text();summ=(target/'summary.json').read_text();meta=(target/'metadata.json').read_text()
 rows=list(csv.DictReader(raw.splitlines()));fields=list(rows[0])
 def wr(rr):
  with (target/'steps.csv').open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rr)
 rr=[dict(r) for r in rows];rr[1]=dict(rr[0]);wr(rr);verdict('DUPLICATE_STEP_ENV_MISSING_PAIR');(target/'steps.csv').write_text(raw)
 rr=[dict(r) for r in rows];rr[0]['upright']='banana';wr(rr);verdict('UPRIGHT_BANANA');(target/'steps.csv').write_text(raw)
 s=json.loads(summ);s['tracking_xy_rmse']=0.0;s['survival_proxy']=0.5;(target/'summary.json').write_text(json.dumps(s));verdict('FORGED_FINITE_SCORE');(target/'summary.json').write_text(summ)
 m=json.loads(meta);m['max_steps']=999;m['step_dt']=99;(target/'metadata.json').write_text(json.dumps(m));verdict('METADATA_TIMING_MISMATCH');(target/'metadata.json').write_text(meta)
 (target/'STATUS.txt').write_text('EVAL_RC=01\n');verdict('STATUS_RC_01');(target/'STATUS.txt').write_text('EVAL_RC=0\n')
 push=next(x for x in sorted(vh.expected_cases(reg)) if x[1].startswith('push_'));pp=root/'evaluation'/'a017'/'cases'/('seed_%d'%push[2])/push[1]
 s=json.loads((pp/'summary.json').read_text());s['post_push_tracking_xy_rmse']=float('nan');s['recovery']={'recovery_rate_upright':float('inf')};(pp/'summary.json').write_text(json.dumps(s));verdict('PUSH_UNCHECKED_NONFINITE')
text=Path('GO2_REAUDIT_ROUND5_PROMOTION_260908.md').read_text(encoding='utf-8')
pins=re.findall(r'\| `([^`]+)` \| `([0-9a-f]{64})`',text)
for f,h in pins:
 f=f.replace('Q/','workspace/training/quadruped/');assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
print('PINNED_HASHES_OK',len(pins))
sys.path.insert(0,str(Path('workspace/training/quadruped').resolve()));scope={};exec(re.findall(r'```python\n(.*?)```',text,re.S)[-1],scope)
a=scope['arm'](scope['scen'](.96,.71,sf=float('nan')));print('NAN_FLOOR',scope['ter'].representative_decision(a,scope['gates'])['status'])
