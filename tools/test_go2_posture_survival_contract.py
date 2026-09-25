"""Contract test for the posture-gated survival metric.

Runs the real ``Collector`` against stub environments, so it needs neither
Isaac Sim nor a GPU.  The contract it pins down:

  * a collapsed-but-never-terminated robot scores 1.00 on v1 and below 1.00
    on v2 -- this is the Default-lineage artifact the metric change targets;
  * a normally walking robot scores 1.00 on both, so the gate does not
    misjudge good behaviour;
  * a scene with no posture evidence publishes no scored survival at all --
    ``survival_proxy`` is None and the source says POSTURE_UNMEASURED, with the
    v1 number kept beside it as a reference figure only.  Engine 1.4.0 did
    degrade to v1 under the scored key; since 1.5.0 nothing does;
  * ``recovery_rate_upright`` refuses to credit a motionless collapsed robot.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workspace" / "training" / "quadruped"))

import go2_eval_telemetry as tel  # noqa: E402


class FakeTensor:
    """Minimal stand-in for the torch tensors ``Collector`` reads."""

    def __init__(self, data) -> None:
        self.data = np.asarray(data, dtype=float)

    @property
    def ndim(self) -> int:
        return self.data.ndim

    def detach(self) -> "FakeTensor":
        return self

    def to(self, _device) -> "FakeTensor":
        return self

    def unsqueeze(self, axis) -> "FakeTensor":
        return FakeTensor(np.expand_dims(self.data, axis))

    def reshape(self, *shape) -> "FakeTensor":
        return FakeTensor(self.data.reshape(*shape))

    def __getitem__(self, key) -> "FakeTensor":
        return FakeTensor(self.data[key])

    def tolist(self):
        return self.data.tolist()


class StubScene:
    def __init__(self, robot, scanner) -> None:
        self._items = {"robot": robot}
        if scanner is not None:
            self._items["height_scanner"] = scanner

    def __getitem__(self, key):
        if key not in self._items:
            raise KeyError(key)
        return self._items[key]


class StubData:
    pass


class StubManager:
    def __init__(self, command, terms) -> None:
        self._command = command
        self.active_terms = list(terms)

    def get_command(self, _name):
        return FakeTensor(self._command)

    def get_term(self, _name):
        return FakeTensor(np.zeros(len(self._command)))


class StubEnv:
    """One evaluation environment held at a fixed posture for the whole run."""

    def __init__(self, *, num_envs, height, grav_z, speed, scanner=True, terrain_z=0.0):
        self.num_envs = num_envs
        self.step_dt = 0.02
        self.command_manager = StubManager([[1.0, 0.0, 0.0]] * num_envs, ["time_out", "base_contact"])
        self.termination_manager = self.command_manager

        robot = StubData()
        robot.data = StubData()
        robot.data.root_lin_vel_b = FakeTensor([[speed, 0.0, 0.0]] * num_envs)
        robot.data.root_ang_vel_b = FakeTensor([[0.0, 0.0, 0.0]] * num_envs)
        robot.data.root_pos_w = FakeTensor([[0.0, 0.0, height + terrain_z]] * num_envs)
        robot.data.projected_gravity_b = FakeTensor([[0.0, 0.0, grav_z]] * num_envs)
        robot.root_physx_view = None

        scanner_obj = None
        if scanner:
            scanner_obj = StubData()
            scanner_obj.data = StubData()
            scanner_obj.data.ray_hits_w = FakeTensor(
                np.tile(np.array([0.0, 0.0, terrain_z]), (num_envs, 9, 1))
            )
        self.scene = StubScene(robot, scanner_obj)
        self.cfg = StubData()
        self.cfg.events = None


def run(env, steps):
    out = Path(tempfile.mkdtemp()) / "case"
    collector = tel.Collector(out, steps)
    collector.attach(env)
    result = (None, None, FakeTensor(np.zeros(env.num_envs)), FakeTensor(np.zeros(env.num_envs)), {})
    for _ in range(steps):
        collector.record(env, result)
    if not collector.closed:
        collector.close(True)
    return json.loads((out / "summary.json").read_text(encoding="utf-8")), out


FAILURES: list[str] = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label} {detail}")
        FAILURES.append(label)


# 1. Collapsed robot: belly on the ground, base still level, never terminated.
#    Measured Default lineage: root_z median 0.115 m against Pilot's 0.306 m.
print("[1] collapsed robot (height 0.115 m, level base, no termination)")
collapsed, collapsed_dir = run(StubEnv(num_envs=32, height=0.115, grav_z=-1.0, speed=0.02), 250)
check("v1 reports full survival (the artifact)", collapsed["survival_proxy_v1"] == 1.0, collapsed["survival_proxy_v1"])
check("v2 reports zero survival", collapsed["survival_proxy_v2"] == 0.0, collapsed["survival_proxy_v2"])
check("survival_proxy now follows v2", collapsed["survival_proxy"] == 0.0)
check("source labelled posture_gate_v2", collapsed["survival_proxy_source"] == "posture_gate_v2")
check("all envs marked fallen", collapsed["fallen_env_count"] == 32, collapsed["fallen_env_count"])
check("schema_version bumped to 6", collapsed["schema_version"] == 6)
check(
    "the measurement contract is stated in the summary",
    collapsed.get("measurement_contract")
    == "posture_gate_v2/both_channels_required/no_v1_fallback"
       "/row_and_env_coverage_0.99/missing_rows_not_upright/fall_verdict_unambiguous"
       "/finite_kinematics_required",
    collapsed.get("measurement_contract"),
)
check("a fully observed run has no verdict ambiguity",
      collapsed.get("posture_fall_verdict_ambiguous") is False)
check("full coverage is reported, not just a measured flag",
      collapsed.get("posture_coverage") == 1.0
      and collapsed.get("posture_min_env_coverage") == 1.0,
      (collapsed.get("posture_coverage"), collapsed.get("posture_min_env_coverage")))
check("recovery_rate_upright denies a motionless robot",
      collapsed["recovery"]["recovery_rate_upright"] in (0.0, None),
      collapsed["recovery"]["recovery_rate_upright"])
check("legacy recovery_rate still credits it (unchanged)",
      collapsed["recovery"]["recovery_rate"] == 1.0, collapsed["recovery"]["recovery_rate"])

# 2. Walking robot at the Pilot's measured stance height.
print("[2] walking robot (height 0.306 m, level base)")
walking, _ = run(StubEnv(num_envs=32, height=0.306, grav_z=-1.0, speed=1.17), 250)
check("v2 reports full survival", walking["survival_proxy_v2"] == 1.0, walking["survival_proxy_v2"])
check("no env marked fallen", walking["fallen_env_count"] == 0)

# 3. Upright height but tipped past 60 degrees.
print("[3] tipped robot (height 0.306 m, base tilted ~75 deg)")
tipped, _ = run(StubEnv(num_envs=16, height=0.306, grav_z=-math.cos(math.radians(75)), speed=0.4), 250)
check("v2 counts a tipped base as fallen", tipped["survival_proxy_v2"] == 0.0, tipped["survival_proxy_v2"])

# 4. Stairs: absolute root_z is meaningless, terrain-relative height is not.
print("[4] descending stairs (terrain_z -0.80 m, stance height 0.306 m)")
stairs, _ = run(StubEnv(num_envs=16, height=0.306, grav_z=-1.0, speed=0.9, terrain_z=-0.80), 250)
check("v2 survives a negative world-frame root_z", stairs["survival_proxy_v2"] == 1.0, stairs["survival_proxy_v2"])
check("height_rel measured against terrain, not world zero",
      abs(stairs["height_rel_median"] - 0.306) < 1e-6, stairs["height_rel_median"])

# 5. No posture evidence at all -> must degrade honestly.
print("[5] scene without a height scanner or projected gravity")
env = StubEnv(num_envs=8, height=0.115, grav_z=-1.0, speed=0.02, scanner=False)
del env.scene["robot"].data.projected_gravity_b
blind, _ = run(env, 120)
check("v2 is None when unmeasurable", blind["survival_proxy_v2"] is None, blind["survival_proxy_v2"])
# Engine 1.5.0 removed the silent fallback: when posture is unmeasurable the
# scored field is None and the source says so, instead of quietly publishing the
# termination-only number under the same key a posture run uses.
check("source labelled POSTURE_UNMEASURED", blind["survival_proxy_source"] == "POSTURE_UNMEASURED")
check("scored survival_proxy is None, not the v1 number", blind["survival_proxy"] is None)
check("v1 number is still available for reference", blind["survival_proxy_v1"] is not None)
check("posture_measured is false", blind["posture_measured"] is False)

# 6. CSV carries the new evidence columns.
print("[6] steps.csv schema")
with (collapsed_dir / "steps.csv").open(encoding="utf-8") as handle:
    header = next(csv.reader(handle))
for column in ("proj_grav_z", "terrain_z", "height_rel", "upright"):
    check(f"column {column} present", column in header)

# 7. Partial coverage.  Engine 1.5.1 marked the whole run measured as soon as one
# row carried both channels, scored every unmeasured row upright, and then divided
# the fall count by *every* env -- so a run that watched half its robots published
# a survival number over all of them.  Coverage is now counted per row and per env.
print("[7] half the envs blind for the whole run")


class HalfBlindEnv(StubEnv):
    """Even env ids report both posture channels; odd env ids report neither."""


def _half_blind_posture(self, base, robot, count):
    return (
        [-1.0 if env_id % 2 == 0 else float("nan") for env_id in range(count)],
        [0.0 if env_id % 2 == 0 else None for env_id in range(count)],
    )


_real_posture = tel.Collector._posture
try:
    tel.Collector._posture = _half_blind_posture
    half, _ = run(HalfBlindEnv(num_envs=32, height=0.306, grav_z=-1.0, speed=1.17), 100)
finally:
    tel.Collector._posture = _real_posture

check("a half-watched run publishes no survival number", half["survival_proxy"] is None,
      half["survival_proxy"])
check("and says why", half["survival_proxy_source"] == "POSTURE_COVERAGE_INSUFFICIENT",
      half["survival_proxy_source"])
check("row coverage is reported", abs(half["posture_coverage"] - 0.5) < 1e-9,
      half["posture_coverage"])
check("the worst env's coverage is reported", half["posture_min_env_coverage"] == 0.0,
      half["posture_min_env_coverage"])
check("posture_measured alone is no longer sufficient", half["posture_measured"] is True)

# 8. The runner's acceptance test must read values, not search for a substring.
# measurement_contract contains the literal "posture_gate_v2" on every summary,
# including the two above, so `grep -q posture_gate_v2` passed on exactly the
# files it existed to reject.
print("[8] runner accepts only a summary that carries a real posture number")
RUNNER = Path(__file__).resolve().parents[1] / "workspace/training/quadruped/server_run_go2_a017_full_suite.sh"
runner_text = RUNNER.read_text(encoding="utf-8")
# The field checks moved out of the runner body into the script the runner
# delegates to, and this file kept grepping the runner -- so it failed on a
# guard that had got stronger, not weaker.  Follow the delegation instead of
# naming the file, so extracting the check again does not break this contract.
_delegate = re.search(r'POSTURE_CHECK="\$PACKAGE_ROOT/([^"]+)"', runner_text)
if _delegate:
    _path = RUNNER.parent / _delegate.group(1)
    check("the delegated posture check ships next to the runner", _path.is_file())
    runner_text += "\n" + _path.read_text(encoding="utf-8")
for blocked in (half, blind):
    check("the retired substring test would have passed this summary",
          "posture_gate_v2" in json.dumps(blocked))
check("the runner no longer greps summary.json for the label",
      "grep -q 'posture_gate_v2' \"$out/summary.json\"" not in runner_text)
check("the runner defines a value-level posture check", "posture_ok() {" in runner_text)
check("and calls it on every case", 'posture_ok "$out/summary.json"' in runner_text)
for field in ("survival_proxy_source", "posture_coverage", "posture_min_env_coverage",
              "schema_version", "completed", "posture_fall_verdict_ambiguous"):
    check(f"the check inspects {field}", field in runner_text)

# 9. Coverage is not enough.  Engine 1.5.2 scored an unobserved row upright, and
# that reset the continuous-fall timer -- so ONE missing frame inside a 0.8 s
# collapse split it into two 0.4 s runs, neither long enough to be a fall, and the
# case published full survival at 99.9% coverage.  A gap may not be read as good
# news, and the verdict must not depend on how the gaps are read.
print("[9] one missing frame inside a sustained collapse")


def _gap_run(missing_step):
    """0.8 s below the height floor, optionally with one env-wide blind frame.

    Raising the ground under the robot to 0.2 m leaves a relative height of
    0.106 m, under the 0.18 m floor, for steps 100-139 -- 0.8 s, well past the
    0.5 s hold.  ``missing_step`` blanks the terrain reading on one step.
    """
    env = StubEnv(num_envs=2, height=0.306, grav_z=-1.0, speed=1.0)
    out = Path(tempfile.mkdtemp()) / "case"
    collector = tel.Collector(out, 1000)
    collector.attach(env)

    def posture(_base, _robot, _count):
        if collector.step == missing_step:
            return [-1.0, -1.0], [None, None]
        ground = 0.2 if 100 <= collector.step < 140 else 0.0
        return [-1.0, -1.0], [ground, ground]

    collector._posture = posture
    zero = FakeTensor(np.zeros(2))
    for _ in range(1000):
        collector.record(env, (None, None, zero, zero, {}))
    if not collector.closed:
        collector.close(True)
    return json.loads((out / "summary.json").read_text(encoding="utf-8")), out


control, _ = _gap_run(None)
missing, missing_dir = _gap_run(120)
check("the fully observed collapse is a fall", control["survival_proxy"] == 0.0,
      control["survival_proxy"])
check("removing one observation does not raise survival",
      missing["survival_proxy"] in (None, 0.0), missing["survival_proxy"])
check("the same collapse is still counted",
      missing["fallen_env_count"] == control["fallen_env_count"],
      (missing["fallen_env_count"], control["fallen_env_count"]))
check("coverage alone would have admitted it",
      missing["posture_coverage"] >= missing["posture_min_coverage_required"],
      missing["posture_coverage"])
check("so the gap is caught as verdict ambiguity instead",
      missing["posture_fall_verdict_ambiguous"] is True)
check("and the case says so", missing["survival_proxy_source"] == "POSTURE_FALL_VERDICT_AMBIGUOUS",
      missing["survival_proxy_source"])
check("the two readings of the gap are both reported",
      missing["posture_fall_env_count_optimistic"] == 0
      and missing["posture_fall_env_count_pessimistic"] == 2,
      (missing["posture_fall_env_count_optimistic"],
       missing["posture_fall_env_count_pessimistic"]))
with (missing_dir / "steps.csv").open(encoding="utf-8") as handle:
    gap_rows = [row for row in csv.DictReader(handle) if row["step"] == "121"]
check("an unobserved row is blank in the CSV, not a 1",
      gap_rows and all(row["upright"] == "" for row in gap_rows),
      [row["upright"] for row in gap_rows])

# 10. inf passes every threshold test there is.  ``inf >= FALL_HEIGHT_M`` is true,
# so engine 1.5.3 scored a robot at infinite height upright, measured and fully
# covered -- coverage and the ambiguity gate both saw a flawless run.  A reading
# that is not a finite number is not a reading.
print("[10] non-finite kinematics")


def _kinematics_run(kind):
    """Drive the collector with a stub whose root height is inf / nan / sane."""
    height = {"inf": float("inf"), "nan": float("nan")}.get(kind, 0.306)
    env = StubEnv(num_envs=2, height=height, grav_z=-1.0, speed=1.0)
    out = Path(tempfile.mkdtemp()) / "case"
    collector = tel.Collector(out, 200)
    collector.attach(env)
    clean = FakeTensor(env.scene["robot"].data.root_pos_w.data.copy())
    spoiled = env.scene["robot"].data.root_pos_w.data.copy()
    spoiled[1][2] = float("inf")
    spoiled = FakeTensor(spoiled)
    zero = FakeTensor(np.zeros(2))
    for _ in range(200):
        if kind == "one_row":
            env.scene["robot"].data.root_pos_w = spoiled if collector.step == 100 else clean
        collector.record(env, (None, None, zero, zero, {}))
    if not collector.closed:
        collector.close(True)
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))


sane = _kinematics_run("sane")
check("a finite run reports no non-finite rows", sane["nonfinite_row_count"] == 0)
check("and still publishes its survival number", sane["survival_proxy"] == 1.0)
for kind in ("inf", "nan"):
    spoiled_summary = _kinematics_run(kind)
    check(f"a {kind} root height publishes no survival",
          spoiled_summary["survival_proxy"] is None, spoiled_summary["survival_proxy"])
    check(f"and says the {kind} kinematics are why",
          spoiled_summary["survival_proxy_source"] == "KINEMATICS_NONFINITE",
          spoiled_summary["survival_proxy_source"])
    check(f"a {kind} height is not counted as a posture observation",
          spoiled_summary["posture_coverage"] == 0.0, spoiled_summary["posture_coverage"])

# One bad row in four hundred clears the 0.99 coverage floor and leaves the fall
# verdict unambiguous, so only the explicit count catches it.
single = _kinematics_run("one_row")
check("one non-finite row is counted", single["nonfinite_row_count"] == 1,
      single["nonfinite_row_count"])
check("coverage alone would have admitted it",
      single["posture_coverage"] >= single["posture_min_coverage_required"],
      single["posture_coverage"])
check("the ambiguity gate alone would have admitted it too",
      single["posture_fall_verdict_ambiguous"] is False)
check("but the case publishes no survival", single["survival_proxy"] is None)
check("the runner checks the count", "nonfinite_row_count" in runner_text)

# 11. The bounding readings are only a valid test if the timer is monotone in how
# a gap is read.  Enumerated rather than argued: every 8-step sequence over
# {upright, not upright, unobserved}, against every way of filling its gaps.
print("[11] the two bounding readings bracket every reading between them")
timer_owner = object.__new__(tel.Collector)
timer_owner.step_dt = 0.2


def _fell(sequence):
    runs, fallen = {}, set()
    for flag in sequence:
        timer_owner._fall_timer(runs, fallen, 0, flag)
    return bool(fallen)


bracket_failures = 0
for pattern in itertools.product([True, False, None], repeat=8):
    low = _fell([True if flag is None else flag for flag in pattern])
    high = _fell([False if flag is None else flag for flag in pattern])
    reachable = {
        _fell(filled)
        for filled in itertools.product(
            *[(True, False) if flag is None else (flag,) for flag in pattern]
        )
    }
    held = _fell([flag for flag in pattern if flag is not None])
    if (low == high) != (len(reachable) == 1) or not low <= held <= high:
        bracket_failures += 1
check("agreement of the two extremes means every filling agrees",
      bracket_failures == 0, bracket_failures)
check("the primary timer lies between the two extremes", bracket_failures == 0)

print()
if FAILURES:
    print(f"CONTRACT_FAIL ({len(FAILURES)}): {FAILURES}")
    sys.exit(1)
print("CONTRACT_PASS")
