"""Drive the real collector, then verify what it actually wrote.

Every other contract test in this family hands the verifier a fixture this
repository wrote by hand.  That proves the verifier rejects what we thought to
break; it cannot prove the verifier's recomputation is the same arithmetic the
collector does, because both sides of that comparison were written here.

This test closes that gap.  ``go2_eval_telemetry.py`` imports nothing from
Isaac Lab at module level -- it reaches into the environment through a handful
of duck-typed attributes -- so the real ``Collector`` can be run against a
stand-in scene, producing a real ``steps.csv``, a real ``summary.json`` and a
real ``STATUS.txt``.  Those are then handed to ``verify_go2_a027_harvest.py``.

A fault here means the two definitions have drifted apart.  Which one is wrong
is a separate question; that they disagree is already a reason not to read a
score.  Nothing here touches a recovered harvest, a package, or a GPU.

    python -B tools/test_go2_collector_roundtrip_contract.py
"""

from __future__ import annotations

import hashlib
import importlib
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(QUAD))
sys.path.insert(0, str(ROOT / "tools"))

import verify_go2_a027_harvest as vh  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if condition:
        print("  ok   " + name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


# --------------------------------------------------------------------------
# The stand-in scene.  Only the attributes the collector actually reads.
# --------------------------------------------------------------------------
class Tensor:
    """The slice of the tensor protocol ``go2_eval_telemetry.py`` uses."""

    def __init__(self, data: Any) -> None:
        self.data = data

    def detach(self) -> "Tensor":
        return self

    def to(self, _device: str) -> "Tensor":
        return self

    @property
    def ndim(self) -> int:
        depth, node = 0, self.data
        while isinstance(node, list):
            depth += 1
            node = node[0] if node else None
        return depth

    def unsqueeze(self, _axis: int) -> "Tensor":
        return Tensor([[value] for value in self.data])

    def reshape(self, _shape: int) -> "Tensor":
        flat: list[Any] = []

        def walk(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    walk(item)
            else:
                flat.append(node)

        walk(self.data)
        return Tensor(flat)

    def tolist(self) -> Any:
        return self.data

    def __getitem__(self, key: Any) -> "Tensor":
        # The collector's one fancy index: ``ray_hits_w[..., 2]``.
        assert isinstance(key, tuple) and key[0] is Ellipsis
        axis = key[1]
        return Tensor([[ray[axis] for ray in env] for env in self.data])


class Bag:
    def __init__(self, **fields: Any) -> None:
        self.__dict__.update(fields)


class Terminations:
    def __init__(self, names: list[str], values: dict[str, list[bool]]) -> None:
        self.active_terms = names
        self._values = values

    def get_term(self, name: str) -> Tensor:
        return Tensor(self._values[name])


class Commands:
    def __init__(self, rows: list[list[float]]) -> None:
        self._rows = rows

    def get_command(self, _name: str) -> Tensor:
        return Tensor(self._rows)


class Scene:
    def __init__(self, members: dict[str, Any]) -> None:
        self._members = members

    def __getitem__(self, key: str) -> Any:
        if key not in self._members:
            raise KeyError(key)  # A scene without a height scanner.
        return self._members[key]


class Env:
    """One frame of the environment, rebuilt each step like the real one."""

    def __init__(self, num_envs: int, step_dt: float) -> None:
        self.num_envs = num_envs
        self.step_dt = step_dt
        self.cfg = Bag(events=None)
        self.termination_manager = Terminations(["base_contact"],
                                                {"base_contact": [False] * num_envs})
        self.command_manager = Commands([[0.0, 0.0, 0.0] for _ in range(num_envs)])
        self.scene = Scene({})

    @property
    def unwrapped(self) -> "Env":
        return self


# --------------------------------------------------------------------------
# Running the real collector over a scripted scene.
# --------------------------------------------------------------------------
def collect(out: Path, case_id: str, scenario: str, seed: int,
            num_envs: int, steps: int, step_dt: float, frame) -> Path:
    """Run the real Collector for ``steps`` frames and return the case dir."""
    out.mkdir(parents=True, exist_ok=True)
    os.environ["NCRC_EVAL_CASE"] = case_id
    os.environ["NCRC_EVAL_SCENARIO"] = scenario
    os.environ["NCRC_EVAL_SEED"] = str(seed)
    # Imported fresh so the module-level gate constants are read under the
    # environment this test sets, exactly as a real evaluation does.
    telemetry = importlib.reload(importlib.import_module("go2_eval_telemetry"))
    collector = telemetry.Collector(out, steps)
    env = Env(num_envs, step_dt)
    for step in range(steps):
        commands, linear, angular, position, gravity, hits, terminated = [], [], [], [], [], [], []
        for env_id in range(num_envs):
            state = frame(step, env_id)
            commands.append(list(state["cmd"]))
            linear.append([state["vel"][0], state["vel"][1], 0.0])
            angular.append([0.0, 0.0, state["wz"]])
            position.append(list(state["pos"]))
            gravity.append([0.0, 0.0, state["grav_z"]])
            hits.append(state["ray_hits"])
            terminated.append(state["terminated"])
        env.command_manager = Commands(commands)
        env.termination_manager = Terminations(["base_contact"],
                                               {"base_contact": terminated})
        robot = Bag(data=Bag(root_lin_vel_b=Tensor(linear),
                             root_ang_vel_b=Tensor(angular),
                             root_pos_w=Tensor(position),
                             projected_gravity_b=Tensor(gravity)))
        members: dict[str, Any] = {"robot": robot}
        if any(ray is not None for env_rays in hits for ray in env_rays):
            members["height_scanner"] = Bag(data=Bag(ray_hits_w=Tensor(hits)))
        env.scene = Scene(members)
        collector.record(env, (None, None, Tensor(terminated),
                               Tensor([False] * num_envs), None))
    collector.close(True)
    # The runner writes this one; the collector does not.
    (out / "case_identity.sha256").write_text(
        hashlib.sha256(("a017/%s/%s/%d" % (scenario, case_id, seed)).encode()).hexdigest()
        + "\n", encoding="utf-8")
    return out


UP = 0.32          # the height a Go2 stands at
DOWN = 0.10        # belly on the ground: below the 0.18 m gate
GROUND = [[0.0, 0.0, 0.0]] * 4   # four ray hits, all at terrain height zero


def standing(step: int, env_id: int, *, vx: float = 0.5, cmd_vx: float = 0.5,
             z: float = UP, grav_z: float = -1.0, terminated: bool = False,
             ground: float = 0.0, rays: Any = None) -> dict[str, Any]:
    return {
        "cmd": (cmd_vx, 0.0, 0.0),
        "vel": (vx, 0.0),
        "wz": 0.0,
        "pos": (vx * step, 0.0, z + ground),
        "grav_z": grav_z,
        "ray_hits": [[0.0, 0.0, ground]] * 4 if rays is None else rays,
        "terminated": terminated,
    }


work = Path(tempfile.mkdtemp(prefix="go2_collector_roundtrip_"))


def faults_for(case_dir: Path, scenario: str, case_id: str, seed: int) -> list[str]:
    return vh.verify_case(case_dir, scenario, case_id, seed)["faults"]


def summary_of(case_dir: Path) -> dict[str, Any]:
    import json
    return json.loads((case_dir / "summary.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# 1. A plain walking case at the real control period.
# --------------------------------------------------------------------------
print("[1] the collector's own output for a clean walking case")

clean = collect(work / "clean", "forward_nominal", "G1", 101,
                num_envs=4, steps=300, step_dt=0.02,
                frame=lambda step, env: standing(step, env, vx=0.5 - 0.02 * env))
clean_faults = faults_for(clean, "G1", "forward_nominal", 101)
check("real collector output passes with no faults at all", not clean_faults, clean_faults)
check("and its survival is a measured 1.0",
      summary_of(clean)["survival_proxy"] == 1.0, summary_of(clean)["survival_proxy"])
check("the six-decimal stamps the collector writes are accepted",
      not any("time_s" in f for f in clean_faults), clean_faults)

# --------------------------------------------------------------------------
# 2. A real fall, produced by the collector's own gate rather than asserted.
# --------------------------------------------------------------------------
print("[2] one env that lies down, scored by the collector and recomputed here")


def falls(step: int, env_id: int) -> dict[str, Any]:
    # env 3 collapses at 2 s and stays down for the rest of the run.
    down = env_id == 3 and step >= 100
    return standing(step, env_id, vx=0.0 if down else 0.5, z=DOWN if down else UP)


fallen = collect(work / "fallen", "rough_forward", "G3", 101,
                 num_envs=4, steps=300, step_dt=0.02, frame=falls)
fallen_faults = faults_for(fallen, "G3", "rough_forward", 101)
check("a collector-scored fall passes verification unchanged",
      not fallen_faults, fallen_faults)
check("and the fall is actually in the number, not merely tolerated",
      summary_of(fallen)["survival_proxy"] == 0.75,
      summary_of(fallen)["survival_proxy"])

# --------------------------------------------------------------------------
# 3. Termination, which stops an env's progress mid-run.
# --------------------------------------------------------------------------
print("[3] an env the termination manager kills partway through")


def terminates(step: int, env_id: int) -> dict[str, Any]:
    return standing(step, env_id, terminated=(env_id == 2 and step >= 150))


killed = collect(work / "killed", "forward_slow", "G1", 202,
                 num_envs=4, steps=300, step_dt=0.02, frame=terminates)
killed_faults = faults_for(killed, "G1", "forward_slow", 202)
check("a terminated env's progress and survival recompute identically",
      not killed_faults, killed_faults)
check("the terminated env is counted once",
      summary_of(killed)["terminated_env_count"] == 1
      and summary_of(killed)["survival_proxy_v1"] == 0.75,
      summary_of(killed))

# --------------------------------------------------------------------------
# 4. A push case: the post-push window and the upright recovery rate.
# --------------------------------------------------------------------------
print("[4] a push case, over the windows the recovery rate is cut on")


def pushed(step: int, env_id: int) -> dict[str, Any]:
    # 20 s at 0.02 s: four push windows at 4, 8, 12 and 16 s.  Each push
    # throws the speed up for a quarter second and it settles below the
    # 0.15 m/s quiet threshold shortly after, still upright.
    stamp = (step + 1) * 0.02
    since = min((stamp - t for t in (4.0, 8.0, 12.0, 16.0) if stamp >= t), default=None)
    if since is not None and since < 0.25:
        return standing(step, env_id, vx=1.4, cmd_vx=0.1)
    return standing(step, env_id, vx=0.05, cmd_vx=0.1)


push = collect(work / "push", "push_pos_x", "G6", 101,
               num_envs=4, steps=1000, step_dt=0.02, frame=pushed)
push_faults = faults_for(push, "G6", "push_pos_x", 101)
check("a push case's post-push RMSE and recovery rate recompute identically",
      not push_faults, push_faults)
check("and the recovery rate is a real measurement, not an absent field",
      summary_of(push)["recovery"]["recovery_rate_upright"] == 1.0,
      summary_of(push)["recovery"])

# --------------------------------------------------------------------------
# 5. A stairs case, scored on projected progress.
# --------------------------------------------------------------------------
print("[5] a stairs case, scored on the distance it actually covered")


def climbing(step: int, env_id: int) -> dict[str, Any]:
    rise = 0.15 * (step // 100)
    return standing(step, env_id, vx=0.3, cmd_vx=0.3, ground=rise)


stairs = collect(work / "stairs", "stairs_10_up", "G5", 303,
                 num_envs=4, steps=300, step_dt=0.02, frame=climbing)
stairs_faults = faults_for(stairs, "G5", "stairs_10_up", 303)
check("a stairs case's projected progress recomputes identically",
      not stairs_faults, stairs_faults)
check("progress is a positive measured distance",
      summary_of(stairs)["projected_progress_m"] > 1.0,
      summary_of(stairs)["projected_progress_m"])
# The rising ground is the point: height_rel stays at the standing height while
# root_z climbs, which is exactly the derivation the round-6 audit found
# unchecked.  Real collector output must survive that new check.
check("a climbing robot's relative height is not read as a contradiction",
      not any("height_rel" in f for f in stairs_faults), stairs_faults)

# --------------------------------------------------------------------------
# 6. The degraded path: a height scanner that misses.  The case is not
#    admissible -- and must not be -- but the verifier must still agree with
#    the collector about why, rather than disagreeing about the figures.
# --------------------------------------------------------------------------
print("[6] a height scanner that misses, on the collector's own missing path")


def blind(step: int, env_id: int) -> dict[str, Any]:
    if 40 <= step < 60:
        # Every ray misses.  ``_finite_mean`` returns None, the height is
        # unknown, and upright is written as an empty cell.
        return standing(step, env_id, rays=[[0.0, 0.0, float("inf")]] * 4)
    return standing(step, env_id)


gaps = collect(work / "gaps", "rough_lateral", "G3", 101,
               num_envs=4, steps=300, step_dt=0.02, frame=blind)
gap_faults = faults_for(gaps, "G3", "rough_lateral", 101)
check("the collector refuses to publish a survival number here",
      summary_of(gaps)["survival_proxy"] is None, summary_of(gaps)["survival_proxy"])
check("the verifier disagrees with none of the collector's figures",
      not any(f.startswith("recomputed_") for f in gap_faults), gap_faults)
check("it refuses the case on coverage, which is the honest reason",
      any(f.startswith("posture_coverage=") or f.startswith("posture_min_env_coverage=")
          for f in gap_faults), gap_faults)
check("and the missing rows are not misread as a damaged posture channel",
      not any("csv_posture_column_untyped" in f
              or "csv_height_rel_contradicts_terrain_channels" in f
              or "csv_upright_contradicts_posture_channels" in f for f in gap_faults),
      gap_faults)

# --------------------------------------------------------------------------
# 7. The forgery the round-6 audit reproduced, now against real output.
# --------------------------------------------------------------------------
print("[7] the round-6 counter-examples, applied to genuine collector output")

import csv as _csv  # noqa: E402
import json as _json  # noqa: E402


def _shift_the_fall(case_dir: Path) -> None:
    """Move only the fallen rows' stamps inside the grace window."""
    text = (case_dir / "steps.csv").read_text(encoding="utf-8")
    rows = list(_csv.DictReader(text.splitlines()))
    fields = list(rows[0])
    for row in rows:
        if row["env_id"] == "3" and int(row["step"]) >= 101:
            row["time_s"] = "0.000000"
    with (case_dir / "steps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = _csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    data = _json.loads((case_dir / "summary.json").read_text(encoding="utf-8"))
    data["survival_proxy"] = data["survival_proxy_v2"] = 1.0
    data["fallen_env_count"] = 0
    (case_dir / "summary.json").write_text(_json.dumps(data, indent=2, sort_keys=True),
                                           encoding="utf-8")


forged = work / "forged"
shutil.copytree(work / "fallen", forged)
_shift_the_fall(forged)
forged_faults = faults_for(forged, "G3", "rough_forward", 101)
check("a real fall hidden behind a shifted clock is refused",
      any(f.startswith("csv_time_s_inconsistent_with_step:") for f in forged_faults),
      forged_faults)


def _raise_the_ground(case_dir: Path) -> None:
    text = (case_dir / "steps.csv").read_text(encoding="utf-8")
    rows = list(_csv.DictReader(text.splitlines()))
    fields = list(rows[0])
    rows[0]["terrain_z"] = "100.0"
    with (case_dir / "steps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = _csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


lifted = work / "lifted"
shutil.copytree(work / "clean", lifted)
_raise_the_ground(lifted)
lifted_faults = faults_for(lifted, "G1", "forward_nominal", 101)
check("a ground the stated height cannot come from is refused",
      any(f.startswith("csv_height_rel_contradicts_terrain_channels:")
          for f in lifted_faults), lifted_faults)

shutil.rmtree(work, ignore_errors=True)

print()
if FAILURES:
    print("FAILED %d: %s" % (len(FAILURES), ", ".join(FAILURES)))
    raise SystemExit(1)
print("the verifier's recomputation agrees with the collector's own output")
