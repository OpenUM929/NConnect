"""Round-6 probe: the auditor's own round-5 counter-examples, now expecting rejection.

This is GO2_REAUDIT_ROUND5_PROBE_260908.py with two changes and nothing else:

  * the AST lift takes the fixture constants the rebuilt contract test needs
    (the round-5 probe named six of them by hand and the fixture now has more);
  * every variant carries the verdict it must now produce, so this file fails
    loudly if a hole reopens instead of merely printing what it saw.

It still loads only the fixture *definitions* out of the contract test -- none
of that file's own check sections run -- and still builds its data in a
temporary directory.  No recovered harvest, no package, no GPU.

    python -B GO2_REAUDIT_ROUND6_PROBE_260909.py
"""

import ast
import csv
import json
import math
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path("tools").resolve()))

# The fixture constants the rebuilt contract test defines at module level.  The
# round-5 probe listed six; leaving the new ones out is what made it fail to
# load rather than fail to reject.
WANTED = {
    "ROOT", "REGISTRY", "RUNNER", "EVALUATOR", "FAILURES",
    "NUM_ENVS", "STEPS", "STEP_DT",
    "CMD_VX", "CMD_VY", "CMD_WZ", "ACT_VX", "ACT_VY", "ACT_WZ",
    "ERROR_XY", "ERROR_YAW", "SPEED_XY", "GRAV_Z", "HEIGHT_REL",
    "EXPECT_ROWS", "EXPECT_XY_RMSE", "EXPECT_YAW_RMSE", "EXPECT_SPEED_MEAN",
    "EXPECT_PROGRESS", "EXPECT_RECOVERY_UPRIGHT", "IDENTITY", "PLAN",
}

source = Path("tools/test_go2_harvest_verifier_contract.py").resolve()
tree = ast.parse(source.read_text(encoding="utf-8"))
nodes = []
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
        nodes.append(node)
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        names = [n.id for n in ast.walk(node)
                 if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)]
        if any(name in WANTED for name in names):
            nodes.append(node)

ns = {"__file__": str(source)}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), ns)
vh = ns["vh"]
registry = json.loads(ns["REGISTRY"].read_text(encoding="utf-8"))

FAILED: list[str] = []


def expect(label: str, verdict: str, want: str, faults: list[str], marker: str | None) -> None:
    ok = verdict == want and (marker is None or any(marker in f for f in faults))
    print("  %-4s %-34s %s" % ("ok" if ok else "FAIL", label, verdict))
    if not ok:
        print("       wanted %s%s; faults=%s"
              % (want, "" if marker is None else " with " + marker, faults[:4]))
        FAILED.append(label)


with tempfile.TemporaryDirectory(prefix="opus_r6_") as tmp:
    root = Path(tmp)
    ns["build_harvest"](root, registry)
    target = ns["a017_case"](root)
    push = ns["a017_case"](root, "push_pos_x", 101)

    def verdict(label, want, marker=None, plan=ns["PLAN"]):
        result = ns["run"](root, registry, plan)
        expect(label, result["verdict"], want, ns["faults_of"](result) + result["mismatches"],
               marker)

    print("[control] the undamaged fixture")
    verdict("CLEAN_SYNTHETIC", "INTERNAL_GATE_PASS")
    verdict("CLEAN_WITHOUT_RUN_PLAN", "INTERNAL_GATE_INCONCLUSIVE", plan=None)

    print("[round-5 counter-examples]")
    raw = (target / "steps.csv").read_text()
    summ = (target / "summary.json").read_text()
    meta = (target / "metadata.json").read_text()
    status = (target / "STATUS.txt").read_text()
    rows = list(csv.DictReader(raw.splitlines()))
    fields = list(rows[0])

    def write_rows(new_rows):
        with (target / "steps.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(new_rows)

    edited = [dict(r) for r in rows]
    edited[1] = dict(edited[0])
    write_rows(edited)
    verdict("DUPLICATE_STEP_ENV_MISSING_PAIR", "INTERNAL_GATE_FAIL", "csv_duplicate_step_env")
    (target / "steps.csv").write_text(raw)

    edited = [dict(r) for r in rows]
    edited[0]["upright"] = "banana"
    write_rows(edited)
    verdict("UPRIGHT_BANANA", "INTERNAL_GATE_FAIL", "csv_upright_outside_domain")
    (target / "steps.csv").write_text(raw)

    data = json.loads(summ)
    data["tracking_xy_rmse"] = 0.0
    data["survival_proxy"] = 0.5
    (target / "summary.json").write_text(json.dumps(data))
    verdict("FORGED_FINITE_SCORE", "INTERNAL_GATE_FAIL", "recomputed_tracking_xy_rmse")
    (target / "summary.json").write_text(summ)

    data = json.loads(meta)
    data["max_steps"] = 999
    data["step_dt"] = 99
    (target / "metadata.json").write_text(json.dumps(data))
    verdict("METADATA_TIMING_MISMATCH", "INTERNAL_GATE_FAIL", "metadata_max_steps")
    (target / "metadata.json").write_text(meta)

    (target / "STATUS.txt").write_text("EVAL_RC=01\n")
    verdict("STATUS_RC_01", "INTERNAL_GATE_FAIL", "eval_rc=")
    (target / "STATUS.txt").write_text(status)

    data = json.loads((push / "summary.json").read_text())
    data["post_push_tracking_xy_rmse"] = float("nan")
    data["recovery"] = {"recovery_rate_upright": float("inf")}
    (push / "summary.json").write_text(json.dumps(data))
    verdict("PUSH_UNCHECKED_NONFINITE", "INTERNAL_GATE_FAIL", "post_push_tracking_xy_rmse")
    (push / "summary.json").write_text(
        json.dumps(json.loads(summ) | {"recovery": {"recovery_rate_upright":
                                                    ns["EXPECT_RECOVERY_UPRIGHT"]}}))

print("[promotion gate]")
sys.path.insert(0, str(Path("workspace/training/quadruped").resolve()))
import go2_tuning_eval_report as ter  # noqa: E402

GATES = {"minimum_points_70": 60.0, "required_survival_proxy": 0.95,
         "required_tracking_proxy": 0.70}


def arm(survival_floor, tracking_floor=0.71):
    scenario = {"survival_proxy": 0.96, "tracking_proxy": 0.71, "scenario_proxy": 0.6816,
                "survival_proxy_min_any_case": survival_floor,
                "tracking_proxy_min_any_case": tracking_floor}
    ok = {"survival_proxy": 0.99, "tracking_proxy": 0.95, "scenario_proxy": 0.9405,
          "survival_proxy_min_any_case": 0.99, "tracking_proxy_min_any_case": 0.95}
    return {
        "status": "SELF_ASSESSMENT_COMPLETE",
        "instrument": {
            "survival_proxy_sources": ["posture_gate_v2"],
            "telemetry_schema_versions": ["6"],
            "measurement_contracts": [vh.EXPECTED_CONTRACT],
            "posture_gate_params": [json.dumps(vh.EXPECTED_GATE, sort_keys=True)],
            "posture_min_coverage_required": [str(vh.MIN_COVERAGE)],
            "tracking_proxy_std": 0.5,
        },
        "simulation_points_70": 65.0,
        "seed_fractions": {"101": 0.9, "202": 0.9, "303": 0.9},
        "locomotion": {"verdict": "LOCOMOTES"},
        "scenarios": dict({"G1": scenario}, **{f"G{i}": dict(ok) for i in range(2, 8)}),
    }


for label, value in (("NAN_FLOOR", float("nan")), ("INF_FLOOR", float("inf")),
                     ("BOOL_FLOOR", True), ("NEGATIVE_FLOOR", -0.1)):
    out = ter.representative_decision(arm(value), GATES)
    ok = (out["status"] == "INTERNAL_MEASUREMENT_INVALID"
          and out["candidate_points_70"] is None)
    print("  %-4s %-34s %s" % ("ok" if ok else "FAIL", label, out["status"]))
    if not ok:
        FAILED.append(label)

for label, floor, want in (("NORMAL_FLOOR_PASSES", 0.96, "INTERNAL_REPRESENTATIVE_PROMOTION_PASS"),
                           ("LOW_FLOOR_FAILS", 0.90, "INTERNAL_REPRESENTATIVE_PROMOTION_FAIL")):
    out = ter.representative_decision(arm(floor), GATES)
    ok = out["status"] == want
    print("  %-4s %-34s %s" % ("ok" if ok else "FAIL", label, out["status"]))
    if not ok:
        FAILED.append(label)

print("[pinned hashes]")
document = Path("GO2_REAUDIT_ROUND6_PROMOTION_260909.md")
if document.is_file():
    import hashlib
    pins = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})`", document.read_text(encoding="utf-8"))
    stale = [f for f, h in pins
             if hashlib.sha256(Path(f.replace("Q/", "workspace/training/quadruped/"))
                               .read_bytes()).hexdigest() != h]
    print("  %-4s %-34s %d pinned, %d stale"
          % ("ok" if not stale else "FAIL", "ROUND6_DOCUMENT_HASHES", len(pins), len(stale)))
    if stale:
        FAILED.extend(stale)
else:
    print("  --   ROUND6_DOCUMENT_HASHES              document not present")

print()
if FAILED:
    print("FAILED %d: %s" % (len(FAILED), ", ".join(FAILED)))
    raise SystemExit(1)
print("every round-5 counter-example is now rejected, and normal input still passes")
