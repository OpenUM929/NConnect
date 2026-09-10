"""Bounded read-only-source diagnostic; synthetic temp files only. Exit 0 is not a gate verdict."""
import ast
import csv
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "workspace/training/quadruped"))
source = ROOT / "tools/test_go2_collector_roundtrip_contract.py"
nodes = []
for node in ast.parse(source.read_text(encoding="utf-8")).body:
    if isinstance(node, ast.Assign) and any(isinstance(n, ast.Name) and n.id == "work" for n in node.targets):
        break
    if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
        nodes.append(node)
    elif isinstance(node, (ast.Assign, ast.AnnAssign)) and any(
        isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id.isupper()
        for n in ast.walk(node)
    ):
        nodes.append(node)
ns = {"__file__": str(source)}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), ns)
with tempfile.TemporaryDirectory(prefix="codex_r7_") as tmp:
    case = Path(tmp) / "case"
    def frame(step, env):
        stamp = (step + 1) * 0.02
        since = min((stamp-t for t in (4.,8.,12.,16.) if stamp >= t), default=None)
        return ns["standing"](step, env, vx=1.4 if since is not None and since < .25 else .05, cmd_vx=.1)
    ns["collect"](case, "push_pos_x", "G6", 101, 4, 1000, .02, frame)
    original = (case / "summary.json").read_text()
    result = ns["vh"].verify_case(case, "G6", "push_pos_x", 101)
    print("TIME_CONTROL", result["csv"]["recomputed"]["post_push_tracking_xy_rmse"], result["faults"])
    raw = (case / "steps.csv").read_text()
    rows = list(csv.DictReader(raw.splitlines()))
    for row in rows:
        if int(row["step"]) == 200:
            row["time_s"] = "3.999997"
    with (case / "steps.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    interim = ns["vh"].verify_case(case, "G6", "push_pos_x", 101)
    summary = json.loads(original)
    summary["post_push_tracking_xy_rmse"] = interim["csv"]["recomputed"]["post_push_tracking_xy_rmse"]
    (case / "summary.json").write_text(json.dumps(summary))
    result = ns["vh"].verify_case(case, "G6", "push_pos_x", 101)
    print("TIME_SHIFT_ACCEPTED", result["csv"]["recomputed"]["post_push_tracking_xy_rmse"], result["faults"])
    (case / "steps.csv").write_text(raw)
    for label, text in (
        ("SUMMARY_LIST", "[]"),
        ("GATE_LIST", json.dumps(dict(json.loads(original), posture_gate=[1]))),
        ("BROKEN_JSON", "{"),
    ):
        (case / "summary.json").write_text(text)
        try:
            result = ns["vh"].verify_case(case, "G6", "push_pos_x", 101)
            print(label, result["faults"])
        except Exception as exc:
            print(label, type(exc).__name__, str(exc))

package = ROOT / "workspace/training/quadruped/go2_a017_full_suite.zip"
print("ZIP_SHA256", hashlib.sha256(package.read_bytes()).hexdigest())
with zipfile.ZipFile(package) as archive:
    for name in archive.namelist():
        if name.endswith("/exported/env.yaml"):
            print("FROZEN_ENV", name, hashlib.sha256(archive.read(name)).hexdigest())
