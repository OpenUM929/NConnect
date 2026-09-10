"""Contract test for the local harvest verifier.

A verifier that has only ever seen a good harvest is the same failure the whole
campaign keeps repeating: a check that exists, runs, and has never once been
shown to reject anything.  So every check in ``verify_go2_a027_harvest`` is
exercised here against a harvest deliberately damaged in that one way, on
synthetic data -- no GPU, no Isaac Sim, no recovered run needed.

The round-5 audit passed seven counter-examples through the previous version,
and every one of them is now a section below.  The fixture itself was the root
of most of them: its summary carried numbers that were merely plausible rather
than derived from its own rows, so nothing in it could tell a recomputation
from a range check.  Every figure in the fixture summary is now the value the
collector's own definitions produce from the fixture rows, and each is small
enough to check by hand -- see ``write_case``.

The property that matters most is still the last one: the verifier must never
make a damaged harvest look complete by leaving the damaged case out of the count.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import verify_go2_a027_harvest as vh  # noqa: E402

REGISTRY = ROOT / "workspace" / "training" / "quadruped" / "config" / "go2_self_eval_registry.json"
RUNNER = ROOT / "workspace" / "training" / "quadruped" / "server_run_go2_a017_full_suite.sh"
EVALUATOR = ROOT / "workspace" / "training" / "quadruped" / "go2_eval_telemetry.py"
FAILURES: list[str] = []

# 5.0 s of run at 0.1 s per step: long enough that the 4.0 s push window exists,
# short enough that the whole 138-case harvest is cheap to copy and re-verify.
NUM_ENVS = 2
STEPS = 50
STEP_DT = 0.1

# One row's kinematics, held constant across the run so every aggregate below is
# a number that can be checked by hand rather than trusted.
CMD_VX, CMD_VY, CMD_WZ = 0.5, 0.0, 0.0
ACT_VX, ACT_VY, ACT_WZ = 0.4, 0.0, 0.0
ERROR_XY = math.hypot(CMD_VX - ACT_VX, CMD_VY - ACT_VY)       # 0.1
ERROR_YAW = abs(CMD_WZ - ACT_WZ)                              # 0.0
SPEED_XY = math.hypot(ACT_VX, ACT_VY)                         # 0.4
GRAV_Z, HEIGHT_REL = -1.0, 0.32                               # upright under the gate

# The figures the collector would write for those rows, restated as constants so
# a change of definition shows up here as a failure rather than as agreement.
EXPECT_ROWS = STEPS * NUM_ENVS                                # 100
EXPECT_XY_RMSE = ERROR_XY                                     # constant error
EXPECT_YAW_RMSE = ERROR_YAW
EXPECT_SPEED_MEAN = SPEED_XY
# One step of command-aligned displacement is (a.c/|c|)*dt = 0.4 * 0.1, over 50 steps.
EXPECT_PROGRESS = (ACT_VX * CMD_VX + ACT_VY * CMD_VY) / math.hypot(CMD_VX, CMD_VY) * STEP_DT * STEPS
# One push window exists (4.0 s, since 4.0+1.0 <= 5.0) and the robot never goes
# quiet at 0.4 m/s, so the upright recovery rate is a measured zero, not absent.
EXPECT_RECOVERY_UPRIGHT = 0.0

# The fixture's identity placeholders, and the run plan that recognises them.
# These are real sha256 digests rather than readable words, because the runner
# writes sha256sum output into identity.json and the verifier now says so: a
# fixture spelling them 'model-a017' could not tell a damaged digest apart
# from an unfamiliar one.
def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


IDENTITY = {
    label: {"model_sha256": _digest("model/" + label),
            "env_sha256": _digest("env/" + label)}
    for label in ("a017", "pilot")
}
EVALUATOR_SHA = _digest("evaluator")
REGISTRY_SHA = _digest("registry")
PLAN = {
    "runner": "synthetic",
    "models": {label: fields["model_sha256"] for label, fields in IDENTITY.items()},
    # The approved env digest per arm.  It is supplied to the verifier from
    # outside the harvest, so the fixture supplies it here too.
    "envs": {label: fields["env_sha256"] for label, fields in IDENTITY.items()},
    "num_envs": NUM_ENVS,
    "steps": STEPS,
    "steps_source": "contract_test",
    "evaluator_sha256": EVALUATOR_SHA,
    "registry_sha256": REGISTRY_SHA,
    "faults": [],
}


def check(name: str, condition: bool, detail: object = "") -> None:
    if condition:
        print("  ok   " + name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def write_case(case_dir: Path, scenario: str, case_id: str, seed: int, label: str) -> None:
    """Write one clean case whose summary is derived from its own rows."""
    case_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": vh.EXPECTED_SCHEMA,
        "measurement_contract": vh.EXPECTED_CONTRACT,
        "survival_proxy_source": vh.EXPECTED_SOURCE,
        "posture_gate": dict(vh.EXPECTED_GATE),
        "posture_min_coverage_required": vh.MIN_COVERAGE,
        "completed": True,
        "posture_coverage": 1.0,
        "posture_min_env_coverage": 1.0,
        "posture_fall_verdict_ambiguous": False,
        "nonfinite_row_count": 0,
        "survival_proxy": 1.0,
        "survival_proxy_v1": 1.0,
        "terminated_env_count": 0,
        "tracking_xy_rmse": EXPECT_XY_RMSE,
        "tracking_yaw_rmse": EXPECT_YAW_RMSE,
        "post_push_tracking_xy_rmse": EXPECT_XY_RMSE,
        "speed_xy_mean": EXPECT_SPEED_MEAN,
        "projected_progress_m": EXPECT_PROGRESS,
        "recovery": {"recovery_rate_upright": EXPECT_RECOVERY_UPRIGHT},
        "rows": EXPECT_ROWS,
        "steps": STEPS,
        "step_dt": STEP_DT,
    }
    metadata = {
        "case_id": case_id, "scenario_id": scenario, "evaluation_seed": str(seed),
        "num_envs": NUM_ENVS, "max_steps": STEPS, "step_dt": STEP_DT,
    }
    (case_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True),
                                           encoding="utf-8")
    (case_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True),
                                            encoding="utf-8")
    (case_dir / "STATUS.txt").write_text(
        "EVAL_RC=0\nSTEPS=%d\nROWS=%d\n" % (STEPS, EXPECT_ROWS), encoding="utf-8")
    # The runner writes one fingerprint per case; a copied case directory brings
    # its neighbour's fingerprint with it, which is how that copy is detected.
    (case_dir / "case_identity.sha256").write_text(
        hashlib.sha256(("%s/%s/%s/%d" % (label, scenario, case_id, seed)).encode()).hexdigest()
        + "\n", encoding="utf-8")
    fields = ["step", "time_s", "env_id", "cmd_vx", "cmd_vy", "cmd_wz",
              "actual_vx", "actual_vy", "actual_wz", "error_xy", "error_yaw",
              "speed_xy", "root_x", "root_y", "root_z",
              "proj_grav_z", "terrain_z", "height_rel", "upright",
              "terminated", "truncated"]
    with (case_dir / "steps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for step in range(1, STEPS + 1):
            stamp = step * STEP_DT
            for env_id in range(NUM_ENVS):
                writer.writerow({
                    "step": step, "time_s": "%.6f" % stamp, "env_id": env_id,
                    "cmd_vx": CMD_VX, "cmd_vy": CMD_VY, "cmd_wz": CMD_WZ,
                    "actual_vx": ACT_VX, "actual_vy": ACT_VY, "actual_wz": ACT_WZ,
                    "error_xy": ERROR_XY, "error_yaw": ERROR_YAW, "speed_xy": SPEED_XY,
                    "root_x": ACT_VX * stamp, "root_y": 0.0, "root_z": HEIGHT_REL,
                    "proj_grav_z": GRAV_Z, "terrain_z": 0.0, "height_rel": HEIGHT_REL,
                    "upright": 1, "terminated": 0, "truncated": 0,
                })


def build_harvest(root: Path, registry: dict) -> None:
    """Write a complete, clean two-arm 69-case harvest."""
    for label in ("a017", "pilot"):
        arm = root / "evaluation" / label
        arm.mkdir(parents=True, exist_ok=True)
        (arm / "identity.json").write_text(json.dumps(dict(
            IDENTITY[label], policy=label,
            registry_sha256=REGISTRY_SHA, evaluator_sha256=EVALUATOR_SHA,
        ), sort_keys=True), encoding="utf-8")
        for scenario, case_id, seed in sorted(vh.expected_cases(registry)):
            write_case(arm / "cases" / ("seed_%d" % seed) / case_id,
                       scenario, case_id, seed, label)


def run(root: Path, registry: dict, plan: dict | None = PLAN) -> dict:
    """The same three-way decision ``main()`` makes, on the same inputs.

    A plan that cannot identify the instrument for both arms -- one missing a
    model hash, or an approved env digest -- is not a weaker plan than none.
    It is none, and this helper has to say so or the checks below would be
    measuring something the tool does not do.
    """
    labels = ("a017", "pilot")
    usable = plan is not None and vh.plan_is_usable(plan, list(labels))
    arms = [vh.verify_arm(root, label, registry, plan if usable else None)
            for label in labels]
    mismatches = vh.compare_arms(arms)
    clean = all(a["measurement"] == "INTERNAL_MEASUREMENT_OK" for a in arms) and not mismatches
    if not clean:
        verdict = "INTERNAL_GATE_FAIL"
    elif usable:
        verdict = "INTERNAL_GATE_PASS"
    else:
        verdict = "INTERNAL_GATE_INCONCLUSIVE"
    return {"arms": arms, "mismatches": mismatches, "verdict": verdict}


def faults_of(result: dict, label: str = "a017") -> list[str]:
    arm = next(a for a in result["arms"] if a["label"] == label)
    return list(arm["faults"]) + [f for case in arm["cases"] for f in case["faults"]]


registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
base = Path(tempfile.mkdtemp(prefix="go2_harvest_clean_"))
build_harvest(base, registry)


# Each check below works on its own copy of the clean 138-case harvest, and the
# copying, not the checking, was the bulk of this test's runtime.  Two changes
# take that cost out without moving a single assertion.
#
# The copy is made of hard links, so it costs a directory entry per file instead
# of the file's bytes.  A hard link is the same file under two names, so a
# mutation that wrote through one would silently edit the clean fixture every
# later check is measured against.  ``_detach`` forecloses that: before any
# write-capable open, a file that is still shared is replaced by a private copy
# of itself, which is what a real copy would have given us in the first place.
# Reads and deletions are untouched, so nothing a check does is altered.
#
# The teardown is handed to a background thread.  Deleting a tree is slower here
# than creating it, and no check depends on an earlier check's copy being gone.
_ORIGINAL_OPEN = Path.open
_ORIGINAL_WRITE_TEXT = Path.write_text


def _detach(path: Path) -> None:
    """Give ``path`` a private copy of its contents if it is a shared hard link.

    Nothing is caught here.  A detach that failed quietly would leave the write
    going through to the shared fixture, which is the one outcome this layer
    exists to prevent, so a failure has to stop the run.
    """
    if path.is_file() and os.stat(path).st_nlink > 1:
        with _ORIGINAL_OPEN(path, "rb") as handle:
            data = handle.read()
        path.unlink()
        with _ORIGINAL_OPEN(path, "wb") as handle:
            handle.write(data)


def _cow_open(self, mode="r", *args, **kwargs):
    if any(flag in mode for flag in "wax+"):
        _detach(self)
    return _ORIGINAL_OPEN(self, mode, *args, **kwargs)


def _cow_write_text(self, *args, **kwargs):
    _detach(self)
    return _ORIGINAL_WRITE_TEXT(self, *args, **kwargs)


Path.open = _cow_open
Path.write_text = _cow_write_text


def _tree_fingerprint(root: Path) -> str:
    """One digest over every file in a harvest, path and bytes alike."""
    running = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            running.update(str(path.relative_to(root)).replace("\\", "/").encode())
            running.update(b"\0")
            running.update(hashlib.sha256(_ORIGINAL_OPEN(path, "rb").read()).digest())
    return running.hexdigest()


_base_fingerprint = _tree_fingerprint(base)
_REAPER = ThreadPoolExecutor(max_workers=2)


def damaged(mutate, plan: dict | None = PLAN) -> dict:
    """Link the clean harvest, damage the link tree, and verify that."""
    work = Path(tempfile.mkdtemp(prefix="go2_harvest_case_"))
    target = work / "harvest"
    try:
        shutil.copytree(base, target, copy_function=os.link)
    except OSError:
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(base, target)
    mutate(target)
    result = run(target, registry, plan)
    _REAPER.submit(shutil.rmtree, work, ignore_errors=True)
    return result


def a017_case(root: Path, case_id: str = "rough_forward", seed: int = 101) -> Path:
    return root / "evaluation" / "a017" / "cases" / ("seed_%d" % seed) / case_id


def push_case(root: Path) -> Path:
    return a017_case(root, "push_pos_x", 101)


def edit_summary(path: Path, mutate) -> None:
    data = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    mutate(data)
    (path / "summary.json").write_text(json.dumps(data, indent=2, sort_keys=True),
                                       encoding="utf-8")


def rewrite_rows(path: Path, mutate) -> None:
    """Read the case's rows, let the caller change them, write them back."""
    text = (path / "steps.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    fields = list(rows[0])
    rows = mutate(rows)
    with (path / "steps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------
# 1. A clean harvest passes, and passes for the right reason.
# --------------------------------------------------------------------------
print("[1] a complete, undamaged two-arm harvest")
clean = run(base, registry)
check("a clean harvest is admissible", clean["verdict"] == "INTERNAL_GATE_PASS",
      faults_of(clean) + clean["mismatches"])
check("both arms are counted at 69", all(
    arm["observed_case_count"] == 69 and arm["expected_case_count"] == 69
    for arm in clean["arms"]),
    [(a["label"], a["observed_case_count"]) for a in clean["arms"]])
check("a passing harvest names no invalid case",
      all(arm["invalid_cases"] == [] for arm in clean["arms"]))

# The fixture is only evidence if its summary really is what its rows produce.
sample = vh.read_raw(a017_case(base) / "steps.csv", dict(vh.EXPECTED_GATE),
                     STEP_DT, NUM_ENVS)["recomputed"]
check("the fixture summary is derived from the fixture rows", all((
    vh._agree(sample["tracking_xy_rmse"], EXPECT_XY_RMSE),
    vh._agree(sample["speed_xy_mean"], EXPECT_SPEED_MEAN),
    vh._agree(sample["projected_progress_m"], EXPECT_PROGRESS),
    vh._agree(sample["survival_proxy"], 1.0),
    vh._agree(sample["recovery.recovery_rate_upright"], EXPECT_RECOVERY_UPRIGHT),
)), sample)

# --------------------------------------------------------------------------
# 2. A missing case is the failure the runner's own count is meant to catch,
#    and the verifier must catch it independently of the runner.
# --------------------------------------------------------------------------
print("[2] one case never came back")


def _drop(root: Path) -> None:
    shutil.rmtree(a017_case(root))


dropped = damaged(_drop)
check("a missing case fails the harvest", dropped["verdict"] == "INTERNAL_GATE_FAIL")
check("and it is named", any(f.startswith("missing_cases:") and "G3/rough_forward@101" in f
                            for f in faults_of(dropped)), faults_of(dropped))
check("the arms are then reported as measuring different case sets",
      "arms_measured_different_case_sets" in dropped["mismatches"], dropped["mismatches"])

# --------------------------------------------------------------------------
# 3. The point of the tool: the summary's own tally is not evidence.  A row the
#    collector counted as clean is re-read here, so a summary that says zero
#    while the raw data says otherwise is caught.
# --------------------------------------------------------------------------
print("[3] the summary claims zero non-finite rows and the raw data disagrees")


def _forge(root: Path) -> None:
    path = a017_case(root) / "steps.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    row = lines[3].split(",")
    row[header.index("root_z")] = "inf"
    lines[3] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # summary.json is left saying nonfinite_row_count = 0, exactly as a
    # collector without the 1.5.4 check would have written it.


forged = damaged(_forge)
check("a forged clean summary does not survive the recount",
      forged["verdict"] == "INTERNAL_GATE_FAIL")
check("the recount names the row, not just the count",
      any(f.startswith("csv_nonfinite_rows=1") and "root_z" in f for f in faults_of(forged)),
      faults_of(forged))

# The same value written the two other ways physics produces it.
for token in ("-inf", "nan"):
    def _forge_token(root: Path, token: str = token) -> None:
        path = a017_case(root) / "steps.csv"
        lines = path.read_text(encoding="utf-8").splitlines()
        header = lines[0].split(",")
        row = lines[2].split(",")
        row[header.index("actual_vx")] = token
        lines[2] = ",".join(row)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = damaged(_forge_token)
    check("%r in a scored channel is rejected" % token,
          result["verdict"] == "INTERNAL_GATE_FAIL"
          and any("csv_nonfinite_rows=1" in f for f in faults_of(result)),
          faults_of(result))

# --------------------------------------------------------------------------
# 4. Coverage is recomputed, so a claimed coverage is checkable too.
# --------------------------------------------------------------------------
print("[4] the coverage claim is recomputed from the upright column")


def _gap(root: Path) -> None:
    path = a017_case(root) / "steps.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    row = lines[2].split(",")
    row[header.index("upright")] = ""
    lines[2] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


gap = damaged(_gap)
check("an unobserved row contradicts a claim of full coverage",
      any(f.startswith("recomputed_posture_coverage=") for f in faults_of(gap)), faults_of(gap))

# --------------------------------------------------------------------------
# 5. Figures the scoring path consumes must be finite and in range.
# --------------------------------------------------------------------------
print("[5] out-of-range and non-finite scored figures")
for field, value in (("survival_proxy", 1.5), ("tracking_xy_rmse", -0.1),
                     ("survival_proxy", None)):
    def _bend(root: Path, field: str = field, value: object = value) -> None:
        edit_summary(a017_case(root), lambda data: data.__setitem__(field, value))

    bent = damaged(_bend)
    check("%s = %r is refused" % (field, value),
          bent["verdict"] == "INTERNAL_GATE_FAIL"
          and any(f.startswith(field) for f in faults_of(bent)),
          faults_of(bent))

# --------------------------------------------------------------------------
# 6. The row count in the summary is checked against the rows that exist.
# --------------------------------------------------------------------------
print("[6] the summary's row count against the rows on disk")


def _truncate(root: Path) -> None:
    path = a017_case(root) / "steps.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")


truncated = damaged(_truncate)
check("a truncated CSV is caught",
      any(f.startswith("csv_rows=") for f in faults_of(truncated)), faults_of(truncated))

# --------------------------------------------------------------------------
# 7. Two arms, one ruler.  This is the invariant the whole campaign rests on.
# --------------------------------------------------------------------------
print("[7] instrument symmetry between the two arms")


def _reruler(root: Path) -> None:
    path = root / "evaluation" / "pilot" / "identity.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["evaluator_sha256"] = "a-different-evaluator"
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


reruled = damaged(_reruler)
check("two evaluators means no comparison",
      any(f.startswith("evaluator_sha256_differs") for f in reruled["mismatches"]),
      reruled["mismatches"])


def _mixed(root: Path) -> None:
    edit_summary(a017_case(root), lambda data: data.__setitem__(
        "posture_gate", dict(vh.EXPECTED_GATE, height_rel_min_m=0.25)))


mixed = damaged(_mixed)
check("a gate threshold that moved mid-arm is caught twice over",
      any(f.startswith("posture_gate=") for f in faults_of(mixed))
      and any("mixed_rulers_within_arm" in m for m in mixed["mismatches"]),
      (faults_of(mixed), mixed["mismatches"]))

# --------------------------------------------------------------------------
# 8. A case the registry does not name cannot be smuggled in, and the gates the
#    collector claims to have passed are re-read rather than trusted.
# --------------------------------------------------------------------------
print("[8] cases outside the registry, and the collector's own gate claims")


def _extra(root: Path) -> None:
    src = a017_case(root)
    shutil.copytree(src, src.parent / "forward_extra_fast")


extra = damaged(_extra)
check("a case the registry does not name is refused",
      any(f == "case_not_in_registry:forward_extra_fast" for f in faults_of(extra)),
      faults_of(extra))

for field, value in (("posture_fall_verdict_ambiguous", True),
                     ("nonfinite_row_count", 3),
                     ("posture_min_env_coverage", 0.5),
                     ("schema_version", 5),
                     ("completed", False)):
    def _claim(root: Path, field: str = field, value: object = value) -> None:
        edit_summary(a017_case(root), lambda data: data.__setitem__(field, value))

    claimed = damaged(_claim)
    check("%s = %r is refused" % (field, value),
          claimed["verdict"] == "INTERNAL_GATE_FAIL", faults_of(claimed))

# --------------------------------------------------------------------------
# 9. The move this tool exists to prevent.  One damaged case must leave the
#    harvest incomplete at 69, never complete at 68.
# --------------------------------------------------------------------------
print("[9] a damaged case is named, not dropped")
one_bad = damaged(_forge)
bad_arm = next(a for a in one_bad["arms"] if a["label"] == "a017")
check("the damaged case is still counted among the 69",
      bad_arm["observed_case_count"] == 69, bad_arm["observed_case_count"])
check("the arm is incomplete rather than complete-minus-one",
      bad_arm["measurement"] == "INTERNAL_MEASUREMENT_INCOMPLETE", bad_arm["measurement"])
check("and the case is named so it can be re-measured, not forgotten",
      bad_arm["invalid_cases"] == ["G3/rough_forward@101"], bad_arm["invalid_cases"])
check("the undamaged arm keeps its own valid measurement",
      next(a for a in one_bad["arms"] if a["label"] == "pilot")["measurement"]
      == "INTERNAL_MEASUREMENT_OK")

# --------------------------------------------------------------------------
# 10. Round-5 counter-example: a duplicated row standing in for a deleted one.
#     Row count, env count and step count are all preserved, so every check the
#     previous version had was satisfied while one measurement was gone.
# --------------------------------------------------------------------------
print("[10] a duplicated (step, env) row hiding a deleted one")


def _duplicate(root: Path) -> None:
    def mutate(rows: list[dict]) -> list[dict]:
        rows[1] = dict(rows[0])   # step 1/env 1 becomes a second step 1/env 0
        return rows
    rewrite_rows(a017_case(root), mutate)


duplicated = damaged(_duplicate)
check("a duplicated pair with the total preserved is refused",
      duplicated["verdict"] == "INTERNAL_GATE_FAIL", faults_of(duplicated))
check("the duplicate and the gap it hides are both named",
      any(f.startswith("csv_duplicate_step_env:") for f in faults_of(duplicated))
      and any(f.startswith("csv_missing_step_env:") for f in faults_of(duplicated)),
      faults_of(duplicated))

# --------------------------------------------------------------------------
# 11. Round-5 counter-example: the posture column is a value domain, not a
#     non-empty test.  ``banana`` used to count as an observed upright row.
# --------------------------------------------------------------------------
print("[11] a posture value the collector cannot write")
for token in ("banana", "2", "-1"):
    def _bad_upright(root: Path, token: str = token) -> None:
        def mutate(rows: list[dict]) -> list[dict]:
            rows[0]["upright"] = token
            return rows
        rewrite_rows(a017_case(root), mutate)

    bad = damaged(_bad_upright)
    check("upright=%r is refused rather than counted as observed" % token,
          bad["verdict"] == "INTERNAL_GATE_FAIL"
          and any(f.startswith("csv_upright_outside_domain:") for f in faults_of(bad)),
          faults_of(bad))


def _contradict(root: Path) -> None:
    # A well-formed 1 on a row whose raw channels say the robot is on its side.
    def mutate(rows: list[dict]) -> list[dict]:
        rows[0]["proj_grav_z"] = "-0.1"
        return rows
    rewrite_rows(a017_case(root), mutate)


contradicted = damaged(_contradict)
check("an upright flag its own posture channels contradict is refused",
      any(f.startswith("csv_upright_contradicts_posture_channels:")
          for f in faults_of(contradicted)), faults_of(contradicted))

# --------------------------------------------------------------------------
# 12. Round-5 counter-example: in-range is not correct.  Every scored figure is
#     recomputed from the rows, so a plausible forged number is caught.
# --------------------------------------------------------------------------
print("[12] a forged but perfectly in-range summary figure")
for field, value, expected in (("survival_proxy", 0.5, 1.0),
                               ("tracking_xy_rmse", 0.0, EXPECT_XY_RMSE),
                               ("speed_xy_mean", 0.9, EXPECT_SPEED_MEAN),
                               ("projected_progress_m", 99.0, EXPECT_PROGRESS)):
    def _fake(root: Path, field: str = field, value: object = value) -> None:
        edit_summary(a017_case(root), lambda data: data.__setitem__(field, value))

    faked = damaged(_fake)
    check("a forged in-range %s does not survive recomputation" % field,
          faked["verdict"] == "INTERNAL_GATE_FAIL"
          and any(f.startswith("recomputed_%s=" % field) for f in faults_of(faked)),
          faults_of(faked))

# --------------------------------------------------------------------------
# 13. Round-5 counter-example: metadata and summary must describe one run.
# --------------------------------------------------------------------------
print("[13] metadata that does not describe the run the summary reports")


def _retime(root: Path) -> None:
    path = a017_case(root) / "metadata.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["max_steps"] = 999
    data["step_dt"] = 99
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


retimed = damaged(_retime)
check("a metadata/summary timing mismatch is refused",
      retimed["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("metadata_step_dt=") for f in faults_of(retimed))
      and any(f.startswith("metadata_max_steps=") for f in faults_of(retimed)),
      faults_of(retimed))

# --------------------------------------------------------------------------
# 14. Round-5 counter-example: STATUS.txt is parsed, not searched.
# --------------------------------------------------------------------------
print("[14] an exit code that merely starts with zero")
for line, why in (("EVAL_RC=01", "01"), ("EVAL_RC=0 5", "trailing"), ("XEVAL_RC=0", "prefixed")):
    def _status(root: Path, line: str = line) -> None:
        (a017_case(root) / "STATUS.txt").write_text(
            "%s\nSTEPS=%d\nROWS=%d\n" % (line, STEPS, EXPECT_ROWS), encoding="utf-8")

    status = damaged(_status)
    check("%r is not EVAL_RC=0 (%s)" % (line, why),
          status["verdict"] == "INTERNAL_GATE_FAIL"
          and any(f.startswith("eval_rc=") for f in faults_of(status)), faults_of(status))


def _status_counts(root: Path) -> None:
    (a017_case(root) / "STATUS.txt").write_text(
        "EVAL_RC=0\nSTEPS=%d\nROWS=%d\n" % (STEPS, EXPECT_ROWS + 2), encoding="utf-8")


status_counts = damaged(_status_counts)
check("a STATUS row count that disagrees with the summary is caught",
      any(f.startswith("status_rows=") for f in faults_of(status_counts)),
      faults_of(status_counts))

# --------------------------------------------------------------------------
# 15. Round-5 counter-example: the push scoring inputs were never checked at
#     all.  They are checked on push cases only, so a non-push case that has no
#     recovery figure is still valid.
# --------------------------------------------------------------------------
print("[15] the figures each scenario is actually scored on")
for field, value in (("post_push_tracking_xy_rmse", float("nan")),
                     ("post_push_tracking_xy_rmse", None),
                     ("post_push_tracking_xy_rmse", -1.0)):
    def _push_field(root: Path, field: str = field, value: object = value) -> None:
        edit_summary(push_case(root), lambda data: data.__setitem__(field, value))

    pushed = damaged(_push_field)
    check("a push case with %s = %r is refused" % (field, value),
          pushed["verdict"] == "INTERNAL_GATE_FAIL"
          and any(f.startswith(field) for f in faults_of(pushed)), faults_of(pushed))

for value in (float("inf"), None, 2.0):
    def _recovery(root: Path, value: object = value) -> None:
        edit_summary(push_case(root),
                     lambda data: data.__setitem__("recovery", {"recovery_rate_upright": value}))

    recovered = damaged(_recovery)
    check("a push case whose upright recovery rate is %r is refused" % value,
          recovered["verdict"] == "INTERNAL_GATE_FAIL"
          and any(f.startswith("recovery.recovery_rate_upright") for f in faults_of(recovered)),
          faults_of(recovered))


# The required set is scoped by case, so a scenario that is not scored on the
# push figures is never failed for not carrying them.  Widening the set would
# reject the legitimate ``None`` a short or command-free case writes there.
# (This is a statement about what is *required*; whatever a case does report is
# still recomputed from its rows, which is why the fixture's non-push cases
# carry a post-push figure -- their rows run past the 4.0 s window too.)
check("the push figures are required of push cases only",
      set(vh.PUSH_SCORED_FIELDS) <= set(vh.scored_fields_for("push_pos_x"))
      and not set(vh.PUSH_SCORED_FIELDS) & set(vh.scored_fields_for("forward_nominal"))
      and not set(vh.PUSH_SCORED_FIELDS) & set(vh.scored_fields_for("stairs_10_up")),
      sorted(vh.scored_fields_for("forward_nominal")))
check("and the progress figure of stairs cases only",
      set(vh.STAIRS_SCORED_FIELDS) <= set(vh.scored_fields_for("stairs_10_up"))
      and not set(vh.STAIRS_SCORED_FIELDS) & set(vh.scored_fields_for("forward_nominal")),
      sorted(vh.scored_fields_for("stairs_10_up")))
check("no non-push case in a clean harvest is faulted for a push figure",
      not [f for f in faults_of(clean) if f.startswith(("post_push", "recovery."))],
      faults_of(clean))


def _stairs_progress(root: Path) -> None:
    edit_summary(a017_case(root, "stairs_10_up", 101),
                 lambda data: data.__setitem__("projected_progress_m", None))


stairs = damaged(_stairs_progress)
check("a stairs case without its projected progress is refused",
      stairs["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("projected_progress_m") for f in faults_of(stairs)),
      faults_of(stairs))

# --------------------------------------------------------------------------
# 16. Round-5 counter-example: agreement between two arms is not identity.  The
#     instrument has to match the run plan, and without a plan there is no pass.
# --------------------------------------------------------------------------
print("[16] the harvest against the approved run plan")
no_plan = run(base, registry, None)
check("a harvest not matched to a run plan is inconclusive, not passed",
      no_plan["verdict"] == "INTERNAL_GATE_INCONCLUSIVE", no_plan["verdict"])


def _wrong_model(root: Path) -> None:
    path = root / "evaluation" / "a017" / "identity.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["model_sha256"] = "some-other-model"
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


wrong_model = damaged(_wrong_model)
check("a harvest measured on a model the plan does not name is refused",
      wrong_model["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("identity_model_sha256=") for f in faults_of(wrong_model)),
      faults_of(wrong_model))


def _wrong_envs(root: Path) -> None:
    path = a017_case(root) / "metadata.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["num_envs"] = NUM_ENVS + 1
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


wrong_envs = damaged(_wrong_envs)
check("a case measured over a different env count is refused",
      wrong_envs["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("num_envs=") for f in faults_of(wrong_envs)), faults_of(wrong_envs))

# The runner is the source of every approved condition it actually carries.
# The one it cannot carry is the evaluation env: it copies env.yaml out of a
# training export that exists only on the server, so that digest is supplied
# from outside and the plan is not complete without it.
plan = vh.read_run_plan(RUNNER, REGISTRY, EVALUATOR, None)
check("the run plan is read out of the runner rather than assumed",
      not plan["faults"], plan["faults"])
check("but the runner alone cannot say which env was approved",
      not vh.plan_is_usable(plan, ["a017", "pilot"])
      and vh.plan_is_usable(
          vh.read_run_plan(RUNNER, REGISTRY, EVALUATOR, None,
                           {"a017": "a" * 64, "pilot": "b" * 64}),
          ["a017", "pilot"]))
check("and it carries the eval env count, not the video one",
      plan["num_envs"] == 32 and plan["steps"] == 1000,
      (plan["num_envs"], plan["steps"]))
check("with both model hashes and the two file hashes it computed itself",
      len(plan["models"]) == 2 and all(len(v) == 64 for v in plan["models"].values())
      and plan["registry_sha256"] == hashlib.sha256(REGISTRY.read_bytes()).hexdigest()
      and plan["evaluator_sha256"] == hashlib.sha256(EVALUATOR.read_bytes()).hexdigest(),
      plan["models"])
check("an unreadable runner leaves the plan unusable rather than guessed",
      not vh.plan_is_usable(
          vh.read_run_plan(ROOT / "no_such_runner.sh", REGISTRY, EVALUATOR, None),
          ["a017", "pilot"]))

# --------------------------------------------------------------------------
# 17. A copied case directory carries its neighbour's fingerprint.
# --------------------------------------------------------------------------
print("[17] one case's evidence copied over another's")


def _copy_over(root: Path) -> None:
    src = a017_case(root, "forward_slow", 101)
    dst = a017_case(root, "forward_fast", 101)
    shutil.rmtree(dst)
    shutil.copytree(src, dst)


copied = damaged(_copy_over)
check("two cases sharing one run fingerprint are refused",
      copied["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("case_identity_shared_by:") for f in faults_of(copied)),
      faults_of(copied))


def _no_fingerprint(root: Path) -> None:
    (a017_case(root) / "case_identity.sha256").unlink()


unsigned = damaged(_no_fingerprint)
check("a case with no run fingerprint at all is refused",
      any(f == "missing_case_identity.sha256" for f in faults_of(unsigned)),
      faults_of(unsigned))


# --------------------------------------------------------------------------
# 18. The time axis.  time_s steers the fall grace window and the post-push
#     window, so a stamp that does not match its own step index is a damaged
#     measurement -- even when every other column is untouched.
# --------------------------------------------------------------------------
print("[18] a clock that does not agree with its own step index")


def _one_nan_stamp(root: Path) -> None:
    def mutate(rows):
        rows[0]["time_s"] = "nan"
        return rows
    rewrite_rows(a017_case(root), mutate)


nan_time = damaged(_one_nan_stamp)
check("a single non-finite stamp is refused",
      nan_time["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_time_s_not_a_finite_number:")
              for f in faults_of(nan_time)),
      faults_of(nan_time))


def _frozen_clock(root: Path) -> None:
    def mutate(rows):
        for row in rows:
            row["time_s"] = "999.000000"
        return rows
    rewrite_rows(a017_case(root), mutate)


frozen = damaged(_frozen_clock)
check("a constant clock is refused",
      frozen["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_time_s_inconsistent_with_step:")
              for f in faults_of(frozen)),
      faults_of(frozen))

# The fall this pair is built around: env 0 lies down from step 6 to step 12,
# which is 0.7 s of continuous non-upright posture past a 0.5 s grace and a
# 0.5 s hold, so one of the two envs has fallen and survival is 0.5.
FALL_STEPS = range(6, 13)
FALL_HEIGHT = 0.1


def _lay_down(rows, hide_time: bool):
    for row in rows:
        if row["env_id"] == "0" and int(row["step"]) in FALL_STEPS:
            row["root_z"] = row["height_rel"] = "%.6f" % FALL_HEIGHT
            row["upright"] = "0"
            if hide_time:
                row["time_s"] = "0.000000"
    return rows


def _fall(hide_time: bool):
    def mutate(root: Path) -> None:
        rewrite_rows(a017_case(root), lambda rows: _lay_down(rows, hide_time))
        edit_summary(a017_case(root),
                     lambda data: data.update(survival_proxy=1.0 if hide_time else 0.5))
    return mutate


# The control proves the time check did not simply outlaw falling: the same
# rows, honestly stamped, are accepted as a measured survival of 0.5.
control = damaged(_fall(False))
control_faults = [f for f in faults_of(control) if "rough_forward" not in f]
check("a real fall, honestly stamped, is accepted",
      not any("csv_time_s" in f or "survival_proxy" in f for f in faults_of(control)),
      faults_of(control))

hidden = damaged(_fall(True))
check("the same fall hidden behind a shifted clock is refused",
      hidden["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_time_s_inconsistent_with_step:")
              for f in faults_of(hidden)),
      faults_of(hidden))


def _reverse_rows(root: Path) -> None:
    rewrite_rows(a017_case(root), lambda rows: list(reversed(rows)))


reversed_file = damaged(_reverse_rows)
check("rows out of step order are refused, not silently replayed backwards",
      reversed_file["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_rows_not_in_step_order:")
              for f in faults_of(reversed_file)),
      faults_of(reversed_file))
# The replay itself is index-keyed, so reordering the file changes the order
# it was read in and nothing else.  No recomputed figure may move.
check("reordering the file does not change any recomputed figure",
      not any(f.startswith("recomputed_") for f in faults_of(reversed_file)),
      faults_of(reversed_file))

# 0.1 * 3 is 0.30000000000000004 in binary floating point and the collector
# writes it as "0.300000".  The clean fixture is stamped the same way, so the
# fact that it passes at all is the proof that the rounding is allowed.
_sample = (a017_case(base) / "steps.csv").read_text(encoding="utf-8").splitlines()
check("the collector's six-decimal rounding is what the clean fixture carries",
      any(row.split(",")[1] == "0.300000" for row in _sample[1:]),
      _sample[1:3])


def _zero_step_dt(root: Path) -> None:
    edit_summary(a017_case(root), lambda data: data.update(step_dt=0.0))


zero_dt = damaged(_zero_step_dt)
check("a step_dt of zero is a measurement fault, not a divide",
      any(f.startswith("csv_step_dt_not_positive_finite") for f in faults_of(zero_dt)),
      faults_of(zero_dt))

# --------------------------------------------------------------------------
# 19. Relative height is derived, so it is re-derived.  Checking upright
#     against height_rel while never checking height_rel against root_z and
#     terrain_z left the ground channel free to say anything at all.
# --------------------------------------------------------------------------
print("[19] a relative height that its own two inputs do not produce")


def _impossible_ground(root: Path) -> None:
    def mutate(rows):
        rows[0]["terrain_z"] = "100.0"
        return rows
    rewrite_rows(a017_case(root), mutate)


ground = damaged(_impossible_ground)
check("a ground reading the stated height cannot come from is refused",
      ground["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_height_rel_contradicts_terrain_channels:")
              for f in faults_of(ground)),
      faults_of(ground))


def _banana_ground(root: Path) -> None:
    def mutate(rows):
        rows[0]["terrain_z"] = "banana"
        return rows
    rewrite_rows(a017_case(root), mutate)


banana = damaged(_banana_ground)
check("a ground reading that is not a number at all is refused",
      banana["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_posture_column_untyped:") for f in faults_of(banana)),
      faults_of(banana))

# The opposite error would be to outlaw the collector's own missing-ground
# path.  A row with no ray hit writes an empty ground, an empty height and an
# empty upright, and that row must reach the coverage and ambiguity checks as
# an unobserved row -- never as a contradiction.
def _missing_ground(root: Path) -> None:
    def mutate(rows):
        rows[0]["terrain_z"] = ""
        rows[0]["height_rel"] = ""
        rows[0]["upright"] = ""
        return rows
    rewrite_rows(a017_case(root), mutate)


absent_ground = damaged(_missing_ground)
check("an honestly unobserved ground is not read as a contradiction",
      not any(f.startswith("csv_height_rel_contradicts_terrain_channels:")
              or f.startswith("csv_posture_column_untyped:")
              or f.startswith("csv_upright_contradicts_posture_channels:")
              for f in faults_of(absent_ground)),
      faults_of(absent_ground))

# --------------------------------------------------------------------------
# 20. The evaluation environment is part of the instrument's identity.  The
#     tool used to require only that the field was not empty.
# --------------------------------------------------------------------------
print("[20] the env each arm was actually evaluated under")


def _env_identity(value):
    def mutate(root: Path) -> None:
        path = root / "evaluation" / "a017" / "identity.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["env_sha256"] = value
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
    return mutate


malformed = damaged(_env_identity("banana"))
check("an env digest that is not a sha256 is refused",
      malformed["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("identity_env_sha256_not_sha256:")
              for f in faults_of(malformed)),
      faults_of(malformed))

other = damaged(_env_identity(_digest("env/somebody-else")))
check("a well-formed env digest that is not the approved one is refused",
      other["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("identity_env_sha256=") for f in faults_of(other)),
      faults_of(other))

# Without an approved env digest the harvest can still be checked against
# itself, but nothing ties it to the approved run.  That is not a pass.
_no_env_plan = dict(PLAN, envs={})
check("a plan with no approved env digest cannot identify the run",
      not vh.plan_is_usable(_no_env_plan, ["a017", "pilot"]))
check("a plan carrying an env digest for only one arm is still not usable",
      not vh.plan_is_usable(dict(PLAN, envs={"a017": IDENTITY["a017"]["env_sha256"]}),
                            ["a017", "pilot"]))
check("an expectation that is itself not a sha256 is a plan fault",
      any(f.startswith("expected_env_sha_not_sha256:")
          for f in vh.read_run_plan(RUNNER, REGISTRY, EVALUATOR, None,
                                    {"a017": "banana"})["faults"]))
_clean_no_env = run(base, registry, _no_env_plan)
check("an undamaged harvest with no approved env is INCONCLUSIVE, not PASS",
      _clean_no_env["verdict"] == "INTERNAL_GATE_INCONCLUSIVE",
      _clean_no_env["verdict"])


# --------------------------------------------------------------------------
# 21. Round-7 counter-example: a stamp moved by less than the old tolerance,
#     sitting exactly on the boundary the push window is cut at.  The shift is
#     far too small to look like a wrong clock, and that was the point: it
#     carried one row out of the window, so the figure the scenario is scored
#     on changed while the file still read as honest.  The check is no longer a
#     tolerance at all -- the collector serialises one stamp per step index, so
#     that stamp is the only admissible one.
# --------------------------------------------------------------------------
print("[21] a stamp moved inside the old tolerance, across a scored boundary")

# 4.0 s at 0.1 s per step is step 40.
BOUNDARY_STEP = int(round(vh.PUSH_WINDOW_START_S / STEP_DT))
# That one step is given a velocity unlike every other step's, so whether it
# falls inside the push window changes the number the case is scored on.  0.9
# m/s is far above the recovery quiet speed, so the recovery rate is untouched.
BOUNDARY_VX = 0.9
BOUNDARY_ERROR = abs(CMD_VX - BOUNDARY_VX)
_OTHERS = STEPS - 1
_POST_ROWS = STEPS - BOUNDARY_STEP + 1
# The figures those rows produce, restated here rather than asked of the tool.
BOUNDARY_RMSE_ALL = math.sqrt((_OTHERS * ERROR_XY ** 2 + BOUNDARY_ERROR ** 2) / STEPS)
BOUNDARY_RMSE_POST = math.sqrt(
    ((_POST_ROWS - 1) * ERROR_XY ** 2 + BOUNDARY_ERROR ** 2) / _POST_ROWS)
BOUNDARY_SPEED_MEAN = (_OTHERS * SPEED_XY + BOUNDARY_VX) / STEPS
BOUNDARY_PROGRESS = (_OTHERS * ACT_VX + BOUNDARY_VX) * STEP_DT
# With the boundary step pushed just outside the window, the rows that remain
# all carry the ordinary error, so the scored figure becomes that error exactly.
SHIFTED_RMSE_POST = ERROR_XY


def _boundary(stamp_text: str | None = None, post: float | None = None):
    scored = BOUNDARY_RMSE_POST if post is None else post

    def mutate(root: Path) -> None:
        def rows_mutate(rows: list[dict]) -> list[dict]:
            for row in rows:
                if int(row["step"]) == BOUNDARY_STEP:
                    row["actual_vx"] = "%.6f" % BOUNDARY_VX
                    row["error_xy"] = "%.6f" % BOUNDARY_ERROR
                    row["speed_xy"] = "%.6f" % BOUNDARY_VX
                    if stamp_text is not None:
                        row["time_s"] = stamp_text
            return rows
        rewrite_rows(push_case(root), rows_mutate)
        edit_summary(push_case(root), lambda data: data.update(
            tracking_xy_rmse=BOUNDARY_RMSE_ALL,
            post_push_tracking_xy_rmse=scored,
            speed_xy_mean=BOUNDARY_SPEED_MEAN,
            projected_progress_m=BOUNDARY_PROGRESS))
    return mutate


# The control: the same distinguishing step, honestly stamped, is measured.
boundary_control = damaged(_boundary())
check("a case whose scored figure turns on one boundary row is accepted",
      boundary_control["verdict"] == "INTERNAL_GATE_PASS"
      and faults_of(boundary_control) == [],
      faults_of(boundary_control))

shifted = damaged(_boundary("3.999997", SHIFTED_RMSE_POST))
check("3 microseconds off the push boundary is refused, not tolerated",
      shifted["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_time_s_inconsistent_with_step:")
              for f in faults_of(shifted)),
      faults_of(shifted))

hair = damaged(_boundary("3.999999", SHIFTED_RMSE_POST))
check("and so is the smallest shift the format can express",
      hair["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("csv_time_s_inconsistent_with_step:")
              for f in faults_of(hair)),
      faults_of(hair))

# What is pinned is the stamp's value, not its spelling: the same instant
# written with fewer digits is the same instant and is still measured.
respelled = damaged(_boundary("4.0"))
check("the same instant spelled with fewer digits is not a moved clock",
      respelled["verdict"] == "INTERNAL_GATE_PASS"
      and faults_of(respelled) == [],
      faults_of(respelled))


# --------------------------------------------------------------------------
# 22. Round-7 counter-example: evidence that cannot be read at all.  A case
#     whose summary is a list, or is not JSON, used to end the run with an
#     exception, which loses the report for the other 137 cases with it.  A
#     file that cannot be read is one case's measurement fault and has to be
#     named like any other.
# --------------------------------------------------------------------------
print("[22] evidence that cannot be read is a named fault, not a crash")


def _overwrite(name: str, text: str):
    def mutate(root: Path) -> None:
        (a017_case(root) / name).write_text(text, encoding="utf-8")
    return mutate


not_an_object = damaged(_overwrite("summary.json", "[]"))
check("a summary that is a list is refused by name",
      not_an_object["verdict"] == "INTERNAL_GATE_FAIL"
      and "summary_json_not_an_object:list" in faults_of(not_an_object),
      faults_of(not_an_object))

unparseable = damaged(_overwrite("summary.json", "{"))
check("a summary that is not JSON is refused by name",
      unparseable["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("summary_json_unreadable:") for f in faults_of(unparseable)),
      faults_of(unparseable))

bad_metadata = damaged(_overwrite("metadata.json", "[]"))
check("metadata that is a list is refused by name",
      bad_metadata["verdict"] == "INTERNAL_GATE_FAIL"
      and "metadata_json_not_an_object:list" in faults_of(bad_metadata),
      faults_of(bad_metadata))


def _gate_is_a_list(root: Path) -> None:
    edit_summary(a017_case(root), lambda data: data.update(posture_gate=[1]))


gate_shape = damaged(_gate_is_a_list)
check("a posture gate that is a list is refused rather than dereferenced",
      gate_shape["verdict"] == "INTERNAL_GATE_FAIL"
      and "posture_gate_not_an_object:list" in faults_of(gate_shape),
      faults_of(gate_shape))


def _broken_identity(root: Path) -> None:
    (root / "evaluation" / "a017" / "identity.json").write_text("{", encoding="utf-8")


broken_identity = damaged(_broken_identity)
check("an arm identity that is not JSON is refused by name",
      broken_identity["verdict"] == "INTERNAL_GATE_FAIL"
      and any(f.startswith("identity_json_unreadable:")
              for f in faults_of(broken_identity)),
      faults_of(broken_identity))

# The point of naming rather than raising: the rest of the harvest is still
# reported, so the unreadable case can be re-measured on its own.
crashed_arm = next(a for a in unparseable["arms"] if a["label"] == "a017")
check("the unreadable case is still counted among the 69",
      crashed_arm["observed_case_count"] == 69, crashed_arm["observed_case_count"])
check("it is named so it can be re-measured",
      crashed_arm["invalid_cases"] == ["G3/rough_forward@101"],
      crashed_arm["invalid_cases"])
check("and the other arm keeps its own valid measurement",
      next(a for a in unparseable["arms"] if a["label"] == "pilot")["measurement"]
      == "INTERNAL_MEASUREMENT_OK")


print("[23] the shared clean fixture survived every check unaltered")

# Every check above was measured against a hard-linked copy of one clean
# harvest.  If any of those checks had written through a link, the fixture the
# later checks were compared with would have been the damaged one, and this
# whole file would have been measuring itself.  It did not.
check("the clean harvest is byte-identical to the one every check started from",
      _tree_fingerprint(base) == _base_fingerprint)

_REAPER.shutdown(wait=True)
shutil.rmtree(base, ignore_errors=True)

print()
if FAILURES:
    print("FAILED %d: %s" % (len(FAILURES), ", ".join(FAILURES)))
    raise SystemExit(1)
print("all harvest-verifier contract checks passed")
