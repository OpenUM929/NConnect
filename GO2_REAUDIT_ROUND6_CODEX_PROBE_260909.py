"""Independent Round6 boundary probes. Synthetic temporary data only; no GPU/ZIP writes."""
import ast,csv,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path("tools").resolve()))
source=Path("tools/test_go2_harvest_verifier_contract.py").resolve()
tree=ast.parse(source.read_text(encoding="utf-8"))
nodes=[]
for node in tree.body:
    if isinstance(node,(ast.Import,ast.ImportFrom,ast.FunctionDef)):
        nodes.append(node)
    elif isinstance(node,(ast.Assign,ast.AnnAssign)):
        names=[n.id for n in ast.walk(node) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)]
        if names and any(n.isupper() for n in names): nodes.append(node)
ns={"__file__":str(source)}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),"exec"),ns)
registry=json.loads(ns["REGISTRY"].read_text(encoding="utf-8"))
with tempfile.TemporaryDirectory(prefix="codex_r6_") as tmp:
    root=Path(tmp); ns["build_harvest"](root,registry)
    target=ns["a017_case"](root)
    raw=(target/"steps.csv").read_text()
    original=list(csv.DictReader(raw.splitlines())); fields=list(original[0])
    def show(name):
        result=ns["run"](root,registry)
        print(name,result["verdict"],ns["faults_of"](result),result["mismatches"],flush=True)
    show("CLEAN")
    for name,col,val,allrows in [
        ("ONE_TIME_NAN","time_s","nan",False),
        ("ALL_TIME_999","time_s","999",True),
        ("HEIGHT_TERRAIN_CONTRADICTION","terrain_z","100",False),
        ("TERRAIN_BANANA","terrain_z","banana",False),
    ]:
        rows=[dict(r) for r in original]
        for row in rows if allrows else rows[:1]: row[col]=val
        with (target/"steps.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        show(name)
        (target/"steps.csv").write_text(raw)
    p=root/"evaluation/a017/identity.json"; saved=p.read_text()
    data=json.loads(saved);data["env_sha256"]="banana";p.write_text(json.dumps(data))
    show("ENV_HASH_BANANA");p.write_text(saved)
    summary_path=target/"summary.json"
    saved_summary=summary_path.read_text()
    for label,hide_time in [("FALL_CONTROL",False),("FALL_HIDDEN_BY_FALSE_TIME",True)]:
        rows=[dict(r) for r in original]
        for row in rows:
            if row["env_id"]=="0" and 6<=int(row["step"])<=12:
                row["root_z"]=row["height_rel"]="0.1"
                row["upright"]="0"
                if hide_time: row["time_s"]="0.0"
        with (target/"steps.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        data=json.loads(saved_summary);data["survival_proxy"]=1.0 if hide_time else 0.5
        summary_path.write_text(json.dumps(data))
        result=ns["vh"].verify_case(target,"G3","rough_forward",101)
        print(label,"survival",result["csv"]["recomputed"]["survival_proxy"],"faults",result["faults"],flush=True)
