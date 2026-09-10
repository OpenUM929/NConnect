"""Round-8 probe: every counter-example raised in rounds 5, 6 and 7, expecting rejection.

This is the round-7 probe with the two boundaries the seventh audit opened
added to it:

  * a stamp moved by less than the old tolerance, sitting on the 4.0 s edge the
    push window is cut at, so that one row leaves the window and the figure the
    scenario is scored on changes while the file still reads as honest;
  * evidence that cannot be read at all -- a summary that is a list, a summary
    that is not JSON, a posture gate that is a list, an arm identity that is not
    JSON -- which used to end the run with an exception and lose the report for
    the other 137 cases with it.

The controls that keep each repair from becoming a blanket refusal are kept and
extended:

  * an honestly stamped fall is still measured as a fall;
  * an honestly unobserved ground is still an unobserved row, not a forgery;
  * a harvest with no approved env digest is INCONCLUSIVE, never a pass;
  * a case whose scored figure turns on one boundary row is still measured;
  * the same instant spelled with fewer digits is not a moved clock.

It loads only the fixture *definitions* out of the contract test -- none of
that file's own check sections run -- and builds its data in a temporary
directory.  No recovered harvest, no package, no GPU.

    python -B GO2_REAUDIT_ROUND8_PROBE_260909.py
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

# The fixture constants the contract test defines at module level.
WANTED = {
    "ROOT", "REGISTRY", "RUNNER", "EVALUATOR", "FAILURES",
    "NUM_ENVS", "STEPS", "STEP_DT",
    "CMD_VX", "CMD_VY", "CMD_WZ", "ACT_VX", "ACT_VY", "ACT_WZ",
    "ERROR_XY", "ERROR_YAW", "SPEED_XY", "GRAV_Z", "HEIGHT_REL",
    "EXPECT_ROWS", "EXPECT_XY_RMSE", "EXPECT_YAW_RMSE", "EXPECT_SPEED_MEAN",
    "EXPECT_PROGRESS", "EXPECT_RECOVERY_UPRIGHT",
    "IDENTITY", "PLAN", "EVALUATOR_SHA", "REGISTRY_SHA",
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
    print("  %-4s %-36s %s" % ("ok" if ok else "FAIL", label, verdict))
    if not ok:
        print("       wanted %s%s; faults=%s"
              % (want, "" if marker is None else " with " + marker, faults[:4]))
        FAILED.append(label)


def flat(label: str, ok: bool, detail: object = "") -> None:
    print("  %-4s %-36s" % ("ok" if ok else "FAIL", label))
    if not ok:
        print("       %s" % (detail,))
        FAILED.append(label)


with tempfile.TemporaryDirectory(prefix="opus_r8_") as tmp:
    root = Path(tmp)
    ns["build_harvest"](root, registry)
    target = ns["a017_case"](root)
    push = ns["a017_case"](root, "push_pos_x", 101)

    def verdict(label, want, marker=None, plan=ns["PLAN"]):
        result = ns["run"](root, registry, plan)
        expect(label, result["verdict"], want, ns["faults_of"](result) + result["mismatches"],
               marker)

    raw = (target / "steps.csv").read_text()
    summ = (target / "summary.json").read_text()
    meta = (target / "metadata.json").read_text()
    status = (target / "STATUS.txt").read_text()
    identity_path = root / "evaluation" / "a017" / "identity.json"
    identity = identity_path.read_text()
    rows = list(csv.DictReader(raw.splitlines()))
    fields = list(rows[0])

    def write_rows(new_rows):
        with (target / "steps.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(new_rows)

    print("[control] the undamaged fixture")
    verdict("CLEAN_SYNTHETIC", "INTERNAL_GATE_PASS")
    verdict("CLEAN_WITHOUT_RUN_PLAN", "INTERNAL_GATE_INCONCLUSIVE", plan=None)
    verdict("CLEAN_WITHOUT_APPROVED_ENV", "INTERNAL_GATE_INCONCLUSIVE",
            plan=dict(ns["PLAN"], envs={}))

    print("[round-5 counter-examples]")
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

    print("[round-6 counter-examples: the time axis]")
    edited = [dict(r) for r in rows]
    edited[0]["time_s"] = "nan"
    write_rows(edited)
    verdict("ONE_TIME_NAN", "INTERNAL_GATE_FAIL", "csv_time_s_not_a_finite_number")
    (target / "steps.csv").write_text(raw)

    edited = [dict(r) for r in rows]
    for row in edited:
        row["time_s"] = "999.000000"
    write_rows(edited)
    verdict("ALL_TIME_999", "INTERNAL_GATE_FAIL", "csv_time_s_inconsistent_with_step")
    (target / "steps.csv").write_text(raw)

    write_rows(list(reversed([dict(r) for r in rows])))
    verdict("ROWS_REVERSED", "INTERNAL_GATE_FAIL", "csv_rows_not_in_step_order")
    (target / "steps.csv").write_text(raw)

    # env 0 lies down from step 6 to step 12: 0.7 s of continuous non-upright
    # posture past a 0.5 s grace and a 0.5 s hold, so survival is 0.5.
    def lay_down(hide_time):
        edited = [dict(r) for r in rows]
        for row in edited:
            if row["env_id"] == "0" and 6 <= int(row["step"]) <= 12:
                row["root_z"] = row["height_rel"] = "0.100000"
                row["upright"] = "0"
                if hide_time:
                    row["time_s"] = "0.000000"
        write_rows(edited)
        data = json.loads(summ)
        data["survival_proxy"] = 1.0 if hide_time else 0.5
        (target / "summary.json").write_text(json.dumps(data))

    # The control matters as much as the counter-example: the repair must not
    # have been "refuse anything that fell".
    lay_down(False)
    honest = vh.verify_case(target, "G3", "rough_forward", 101)
    flat("FALL_CONTROL_STILL_MEASURED",
         honest["csv"]["recomputed"]["survival_proxy"] == 0.5
         and not [f for f in honest["faults"] if "time_s" in f],
         honest["faults"])
    lay_down(True)
    verdict("FALL_HIDDEN_BY_FALSE_TIME", "INTERNAL_GATE_FAIL",
            "csv_time_s_inconsistent_with_step")
    (target / "steps.csv").write_text(raw)
    (target / "summary.json").write_text(summ)

    data = json.loads(summ)
    data["step_dt"] = 0.0
    (target / "summary.json").write_text(json.dumps(data))
    verdict("STEP_DT_ZERO", "INTERNAL_GATE_FAIL", "csv_step_dt_not_positive_finite")
    (target / "summary.json").write_text(summ)

    print("[round-6 counter-examples: the relative height]")
    edited = [dict(r) for r in rows]
    edited[0]["terrain_z"] = "100"
    write_rows(edited)
    verdict("HEIGHT_TERRAIN_CONTRADICTION", "INTERNAL_GATE_FAIL",
            "csv_height_rel_contradicts_terrain_channels")
    (target / "steps.csv").write_text(raw)

    edited = [dict(r) for r in rows]
    edited[0]["terrain_z"] = "banana"
    write_rows(edited)
    verdict("TERRAIN_BANANA", "INTERNAL_GATE_FAIL", "csv_posture_column_untyped")
    (target / "steps.csv").write_text(raw)

    # The control: the collector's own missing-ground path writes three empty
    # cells, and that row is an unobserved row, not a contradiction.
    edited = [dict(r) for r in rows]
    edited[0]["terrain_z"] = edited[0]["height_rel"] = edited[0]["upright"] = ""
    write_rows(edited)
    unobserved = vh.verify_case(target, "G3", "rough_forward", 101)
    flat("MISSING_GROUND_STILL_UNOBSERVED",
         not [f for f in unobserved["faults"]
              if "contradicts" in f or "csv_posture_column_untyped" in f],
         unobserved["faults"])
    (target / "steps.csv").write_text(raw)

    print("[round-6 counter-examples: the approved env]")
    data = json.loads(identity)
    data["env_sha256"] = "banana"
    identity_path.write_text(json.dumps(data))
    verdict("ENV_HASH_BANANA", "INTERNAL_GATE_FAIL", "identity_env_sha256_not_sha256")
    data["env_sha256"] = "d" * 64
    identity_path.write_text(json.dumps(data))
    verdict("ENV_HASH_WELL_FORMED_BUT_WRONG", "INTERNAL_GATE_FAIL", "identity_env_sha256=")
    identity_path.write_text(identity)

    print("[round-7 counter-examples: the scored time boundary]")
    # 4.0 s at this fixture's step is the step the push window opens on.  One
    # step is given a velocity unlike every other step's, so whether it falls
    # inside the window changes the number the case is scored on.  Everything
    # the summary claims about those rows is recomputed honestly first: the
    # control has to be measured, or the counter-example proves nothing.
    push_raw = (push / "steps.csv").read_text()
    push_summ = (push / "summary.json").read_text()
    push_rows = list(csv.DictReader(push_raw.splitlines()))
    push_fields = list(push_rows[0])
    b_step = int(round(vh.PUSH_WINDOW_START_S / ns["STEP_DT"]))
    b_vx = 0.9
    b_err = abs(ns["CMD_VX"] - b_vx)
    others = ns["STEPS"] - 1
    post_rows = ns["STEPS"] - b_step + 1
    rmse_all = math.sqrt((others * ns["ERROR_XY"] ** 2 + b_err ** 2) / ns["STEPS"])
    rmse_post = math.sqrt(
        ((post_rows - 1) * ns["ERROR_XY"] ** 2 + b_err ** 2) / post_rows)
    speed_mean = (others * ns["SPEED_XY"] + b_vx) / ns["STEPS"]
    progress = (others * ns["ACT_VX"] + b_vx) * ns["STEP_DT"]

    def boundary(stamp_text=None, post=None):
        edited = [dict(r) for r in push_rows]
        for row in edited:
            if int(row["step"]) == b_step:
                row["actual_vx"] = "%.6f" % b_vx
                row["error_xy"] = "%.6f" % b_err
                row["speed_xy"] = "%.6f" % b_vx
                if stamp_text is not None:
                    row["time_s"] = stamp_text
        with (push / "steps.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=push_fields)
            writer.writeheader()
            writer.writerows(edited)
        data = json.loads(push_summ)
        data["tracking_xy_rmse"] = rmse_all
        data["post_push_tracking_xy_rmse"] = rmse_post if post is None else post
        data["speed_xy_mean"] = speed_mean
        data["projected_progress_m"] = progress
        (push / "summary.json").write_text(json.dumps(data, indent=2, sort_keys=True))

    def restore_push():
        (push / "steps.csv").write_text(push_raw)
        (push / "summary.json").write_text(push_summ)

    boundary()
    verdict("BOUNDARY_ROW_HONESTLY_STAMPED", "INTERNAL_GATE_PASS")

    boundary("3.999997", ns["ERROR_XY"])
    verdict("BOUNDARY_SHIFTED_3_MICROSECONDS", "INTERNAL_GATE_FAIL",
            "csv_time_s_inconsistent_with_step")

    boundary("3.999999", ns["ERROR_XY"])
    verdict("BOUNDARY_SHIFTED_ONE_DIGIT", "INTERNAL_GATE_FAIL",
            "csv_time_s_inconsistent_with_step")

    # The control for the repair: what is pinned is the stamp's value, not its
    # spelling.  The same instant with fewer digits is the same instant.
    boundary("4.0")
    verdict("BOUNDARY_RESPELLED_SAME_INSTANT", "INTERNAL_GATE_PASS")
    restore_push()

    print("[round-7 counter-examples: evidence that cannot be read]")
    for label, text, marker in (
            ("SUMMARY_IS_A_LIST", "[]", "summary_json_not_an_object"),
            ("SUMMARY_IS_NOT_JSON", "{", "summary_json_unreadable"),
    ):
        (target / "summary.json").write_text(text)
        verdict(label, "INTERNAL_GATE_FAIL", marker)
    (target / "summary.json").write_text(summ)

    (target / "metadata.json").write_text("[]")
    verdict("METADATA_IS_A_LIST", "INTERNAL_GATE_FAIL", "metadata_json_not_an_object")
    (target / "metadata.json").write_text(meta)

    (target / "summary.json").write_text(
        json.dumps(dict(json.loads(summ), posture_gate=[1])))
    verdict("POSTURE_GATE_IS_A_LIST", "INTERNAL_GATE_FAIL", "posture_gate_not_an_object")
    (target / "summary.json").write_text(summ)

    identity_path.write_text("{")
    verdict("ARM_IDENTITY_IS_NOT_JSON", "INTERNAL_GATE_FAIL", "identity_json_unreadable")
    identity_path.write_text(identity)

    # The point of naming rather than raising: one unreadable case must not
    # cost the report on the other 137.
    (target / "summary.json").write_text("{")
    damaged_run = ns["run"](root, registry, ns["PLAN"])
    damaged_arm = next(a for a in damaged_run["arms"] if a["label"] == "a017")
    flat("UNREADABLE_CASE_STILL_COUNTED_AND_NAMED",
         damaged_arm["observed_case_count"] == 69
         and damaged_arm["invalid_cases"] == ["G3/rough_forward@101"]
         and next(a for a in damaged_run["arms"]
                  if a["label"] == "pilot")["measurement"] == "INTERNAL_MEASUREMENT_OK",
         (damaged_arm["observed_case_count"], damaged_arm["invalid_cases"]))
    (target / "summary.json").write_text(summ)

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
    flat(label, out["status"] == "INTERNAL_MEASUREMENT_INVALID"
         and out["candidate_points_70"] is None, out["status"])

for label, floor, want in (("NORMAL_FLOOR_PASSES", 0.96, "INTERNAL_REPRESENTATIVE_PROMOTION_PASS"),
                           ("LOW_FLOOR_FAILS", 0.90, "INTERNAL_REPRESENTATIVE_PROMOTION_FAIL")):
    out = ter.representative_decision(arm(floor), GATES)
    flat(label, out["status"] == want, out["status"])

print("[pinned hashes]")
document = Path("GO2_REAUDIT_ROUND8_PROMOTION_260909.md")
if document.is_file():
    import hashlib
    pins = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})`", document.read_text(encoding="utf-8"))
    stale = [f for f, h in pins
             if hashlib.sha256(Path(f.replace("Q/", "workspace/training/quadruped/"))
                               .read_bytes()).hexdigest() != h]
    flat("ROUND8_DOCUMENT_HASHES", not stale,
         "%d pinned, stale: %s" % (len(pins), stale))
    print("       %d pinned, %d stale" % (len(pins), len(stale)))
else:
    print("  --   ROUND8_DOCUMENT_HASHES              document not present")

print()
if FAILED:
    print("FAILED %d: %s" % (len(FAILED), ", ".join(FAILED)))
    raise SystemExit(1)
print("every round-5, round-6 and round-7 counter-example is rejected, "
      "and honest measurement still passes")
