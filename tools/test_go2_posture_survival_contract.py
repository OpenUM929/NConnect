"""Contract test for the posture-gated survival metric.

Runs the real ``Collector`` against stub environments, so it needs neither
Isaac Sim nor a GPU.  The contract it pins down:

  * a collapsed-but-never-terminated robot scores 1.00 on v1 and below 1.00
    on v2 -- this is the Default-lineage artifact the metric change targets;
  * a normally walking robot scores 1.00 on both, so the gate does not
    misjudge good behaviour;
  * a scene with no posture evidence degrades to v1 and says so, rather than
    silently reporting a legacy number as a v2 number;
  * ``recovery_rate_upright`` refuses to credit a motionless collapsed robot.
"""

from __future__ import annotations

import csv
import json
import math
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
check("schema_version bumped to 2", collapsed["schema_version"] == 2)
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
check("source labelled termination_only_v1", blind["survival_proxy_source"] == "termination_only_v1")
check("posture_measured is false", blind["posture_measured"] is False)

# 6. CSV carries the new evidence columns.
print("[6] steps.csv schema")
with (collapsed_dir / "steps.csv").open(encoding="utf-8") as handle:
    header = next(csv.reader(handle))
for column in ("proj_grav_z", "terrain_z", "height_rel", "upright"):
    check(f"column {column} present", column in header)

print()
if FAILURES:
    print(f"CONTRACT_FAIL ({len(FAILURES)}): {FAILURES}")
    sys.exit(1)
print("CONTRACT_PASS")
