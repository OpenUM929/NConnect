"""Read-only diagnostic channels for a Go2 fixed-policy replay — v2 (G-A056, 2026-09-28).

Plan: upload/plan/GO2_G_A056_A043_DIAG_REPLAY_PLAN_20260928.md.  A copy of go2_eval_diag.py (G-A052, v1,
left unchanged) with one added channel group, ``joints``.  Everything else is the v1 recorder.

This module never writes to the simulation, never calls a manager's compute(),
and never triggers a sensor's lazy update.  After every ``env.step`` it copies
tensors the environment already computed during that step into
``diag.csv.gz`` next to the evaluator's ``steps.csv`` (same ``step`` and
``env_id`` keys).  The evaluator itself (go2_eval_telemetry, schema 6) runs
unchanged underneath.

What one row holds and where it comes from (Isaac Lab v2.3.1 names):
  body   root_lin_vel_b, root_ang_vel_b, projected_gravity_b, root_quat_w, root_pos_w z
  feet   robot.data.body_pos_w / body_lin_vel_w for the bodies matching ".*_foot"
  contact  contact sensor ``_data`` buffers for the same feet and for "base":
           net force now, max |force| over the sensor history, current / last air time,
           current contact time, and first_contact recomputed exactly as
           ContactSensor.compute_first_contact does, from the same buffer.
           ``_data`` is read directly because ``.data`` runs the lazy update, which
           would add an update point the uninstrumented run does not have.  Reading
           ``_data`` does not prove the buffer is current, so every row also records
           ``contact_fresh`` (1 when the sensor is not marked outdated and its last update
           is at the current sensor time: ``~_is_outdated`` and
           ``_timestamp - _timestamp_last_update`` < 1e-6) and ``contact_age_s``.  In this
           task the base_contact termination and the feet_air_time reward read ``.data``
           after the last physics substep of every step, which is what normally refreshes
           it; an env reset on this step is marked stale by the sensor's own reset.
  terrain  height_scanner ray hits (already read by the evaluator this step):
           z of the ray nearest each foot in xy, the max ray z within 0.15 m, and the
           xy distance to that nearest ray.  Derived, not a contact geometry.
  action   action_manager.action and prev_action (policy output, before scaling)
  reward   reward_manager._step_reward: each active term's weighted value per second
           for this step (raw value = weighted / weight; weights are in diag_meta.json)
  joints   (v2) robot.data.joint_pos, joint_vel, computed_torque, applied_torque, per joint in
           robot.joint_names order (Isaac Lab v2.3.1 ArticulationData).  computed_torque is the actuator
           model output before clipping, applied_torque the clipped value set into the simulation
           (Articulation._apply_actuator_model).  Both are rewritten before every physics substep
           (Articulation.write_data_to_sim), so a row holds the last substep of the step only; clipping in
           the earlier substeps of the same step is not recorded.  joint_pos / joint_vel are properties
           that read the PhysX view when their buffer is older than the sim time (a read, no write; the
           observation manager already reads them after every step).  Limits are recorded once in
           diag_meta.json: joint_effort_limits, joint_pos_limits, soft_joint_pos_limits (env 0) and each
           actuator's cfg (effort_limit, saturation_effort, velocity_limit, stiffness, damping).  For the
           DC motor model the clip bound depends on joint velocity, so a torque near effort_limit alone is
           not saturation; computed != applied is the recorded clip.

Timing limit: Isaac Lab's step computes rewards and terminations, then resets the
terminated envs, then computes observations.  For an env that terminated on this
step, every robot and sensor channel in the row is the post-reset state, exactly as
in steps.csv; the reward row is the pre-reset step.  diag_meta.json records this.
"""

from __future__ import annotations

import gzip
import io
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "go2_eval_diag_v2"
FOOT_PATTERN = ".*_foot"
NEAR_RADIUS_M = 0.15
TIMING_NOTE = ("robot and sensor channels of an env that terminated on this step are the post-reset state; "
               "reward values are the pre-reset step (Isaac Lab ManagerBasedRLEnv.step order); "
               "computed/applied torque are the last physics substep of the step only")


def _t(value: Any) -> Any:
    return getattr(value, "torch", value)


def _fmt(value: float) -> str:
    return "" if value is None or not math.isfinite(value) else f"{value:.6g}"


class DiagRecorder:
    """One gzip CSV per case.  Channel groups that fail are recorded as unavailable, never guessed."""

    def __init__(self, output: Path, max_steps: int) -> None:
        self.output = Path(output)
        self.max_steps = max_steps
        self.step = 0
        self.closed = False
        self.handle = None
        self.fields: list[str] = []
        self.meta: dict[str, Any] = {"schema": SCHEMA, "timing_note": TIMING_NOTE, "unavailable": {},
                                     "read_only": True}
        self.foot_names: list[str] = []

    # ----- setup -------------------------------------------------------------------------------
    def _disable(self, group: str, exc: BaseException) -> None:
        self.meta["unavailable"].setdefault(group, f"{type(exc).__name__}: {exc}")

    def attach(self, base: Any) -> None:
        robot = base.scene["robot"]
        self.step_dt = float(base.step_dt)
        self.meta["step_dt"] = self.step_dt
        self.meta["num_envs"] = int(base.num_envs)
        try:
            ids, names = robot.find_bodies(FOOT_PATTERN, preserve_order=True)
            self.foot_ids, self.foot_names = list(ids), list(names)
        except Exception as exc:  # noqa: BLE001
            self.foot_ids, self.foot_names = [], []
            self._disable("feet", exc)
        self.meta["foot_names_robot"] = self.foot_names
        try:
            sensor = base.scene["contact_forces"]
            s_ids, s_names = sensor.find_bodies(self.foot_names or FOOT_PATTERN, preserve_order=True)
            b_ids, _ = sensor.find_bodies("base")
            self.sensor, self.s_foot_ids, self.s_base_ids = sensor, list(s_ids), list(b_ids)
            cfg = sensor.cfg
            self.meta["contact_sensor"] = {
                "foot_names": list(s_names), "update_period": getattr(cfg, "update_period", None),
                "history_length": getattr(cfg, "history_length", None),
                "force_threshold": getattr(cfg, "force_threshold", None),
                "track_air_time": getattr(cfg, "track_air_time", None),
                "read": "sensor._data (no lazy update); freshness per row in contact_fresh / contact_age_s"}
            if list(s_names) != self.foot_names:
                raise RuntimeError(f"sensor feet {s_names} != robot feet {self.foot_names}")
        except Exception as exc:  # noqa: BLE001
            self.sensor = None
            self._disable("contact", exc)
        try:
            self.scanner = base.scene["height_scanner"]
        except Exception as exc:  # noqa: BLE001
            self.scanner = None
            self._disable("terrain", exc)
        try:
            rm = base.reward_manager
            self.reward_names = list(rm.active_terms)
            self.meta["reward_weights"] = {n: float(rm.get_term_cfg(n).weight) for n in self.reward_names}
            self.meta["reward_unit"] = "weighted value per second (RewardManager._step_reward)"
        except Exception as exc:  # noqa: BLE001
            self.reward_names = []
            self._disable("reward", exc)
        try:
            self.action_dim = int(_t(base.action_manager.action).shape[-1])
        except Exception as exc:  # noqa: BLE001
            self.action_dim = 0
            self._disable("action", exc)
        self.meta["action_dim"] = self.action_dim
        try:
            self.joint_names = list(robot.joint_names)
        except Exception as exc:  # noqa: BLE001
            self.joint_names = [f"joint{i}" for i in range(12)]
            self._disable("joints", exc)
        try:
            import torch
            d = robot.data
            first = lambda x: _t(x)[0].detach().cpu().tolist()  # noqa: E731
            self.meta["joints"] = {
                "names": self.joint_names,
                "joint_effort_limits_env0": first(d.joint_effort_limits),
                "joint_pos_limits_env0": first(d.joint_pos_limits),
                "soft_joint_pos_limits_env0": first(d.soft_joint_pos_limits),
                "actuators": {k: {"class": type(a).__name__,
                                  **{f: (float(getattr(a.cfg, f)) if isinstance(getattr(a.cfg, f, None), (int, float))
                                         else repr(getattr(a.cfg, f, None)))
                                     for f in ("effort_limit", "saturation_effort", "velocity_limit",
                                               "stiffness", "damping")}}
                              for k, a in robot.actuators.items()},
                "row_timing": "computed/applied torque of the last physics substep of the step",
            }
            if not all(isinstance(v, torch.Tensor) or hasattr(v, "shape")
                       for v in (d.joint_pos, d.joint_vel, d.computed_torque, d.applied_torque)):
                raise RuntimeError("joint tensors missing")
        except Exception as exc:  # noqa: BLE001
            self._disable("joints", exc)
        feet = [n.replace("_foot", "") for n in self.foot_names] or ["FL", "FR", "RL", "RR"]
        self.fields = (["step", "env_id",
                        "lin_vel_b_x", "lin_vel_b_y", "lin_vel_b_z", "ang_vel_b_x", "ang_vel_b_y", "ang_vel_b_z",
                        "grav_b_x", "grav_b_y", "grav_b_z", "quat_w", "quat_x", "quat_y", "quat_z", "root_z"]
                       + [f"{f}_{k}" for f in feet for k in (
                           "pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z",
                           "force_z", "force_norm", "force_hist_max", "contact_time", "air_time",
                           "last_air_time", "first_contact",
                           "terrain_z_near_derived", "terrain_zmax015_derived", "ray_dist_derived")]
                       + ["base_force_hist_max", "contact_fresh", "contact_age_s"]
                       + [f"action_{i}" for i in range(self.action_dim)]
                       + [f"prev_action_{i}" for i in range(self.action_dim)]
                       + [f"rew_{n}" for n in self.reward_names]
                       + [f"{k}_{j}" for k in ("jpos", "jvel", "jtau_cmd", "jtau_app") for j in self.joint_names])
        self.feet = feet
        self.output.mkdir(parents=True, exist_ok=True)
        self.handle = io.TextIOWrapper(gzip.open(self.output / "diag.csv.gz", "wb"), encoding="utf-8", newline="")
        self.handle.write(",".join(self.fields) + "\n")

    # ----- per step ----------------------------------------------------------------------------
    def _group(self, name: str, fn: Any, n: int, width: int) -> list[list[float | None]]:
        if name in self.meta["unavailable"]:
            return [[None] * width for _ in range(n)]
        try:
            out = fn()
            if len(out) != n or any(len(r) != width for r in out):
                raise RuntimeError(f"shape {len(out)}x{len(out[0]) if out else 0} != {n}x{width}")
            return out
        except Exception as exc:  # noqa: BLE001
            self._disable(name, exc)
            return [[None] * width for _ in range(n)]

    def record(self, env: Any) -> None:
        if self.closed:
            return
        base = getattr(env, "unwrapped", env)
        if self.handle is None:
            self.attach(base)
        robot = base.scene["robot"]
        n = int(base.num_envs)
        nf = len(self.feet)

        def body() -> list[list[float]]:
            import torch
            d = robot.data
            t = torch.cat([_t(d.root_lin_vel_b), _t(d.root_ang_vel_b), _t(d.projected_gravity_b),
                           _t(d.root_quat_w), _t(d.root_pos_w)[:, 2:3]], dim=1)
            return t.detach().cpu().tolist()

        def feet() -> list[list[float]]:
            import torch
            d = robot.data
            pos = _t(d.body_pos_w)[:, self.foot_ids]
            vel = _t(d.body_lin_vel_w)[:, self.foot_ids]
            cols = []
            for k in range(nf):
                cols.append(torch.cat([pos[:, k], vel[:, k]], dim=1))
            return torch.cat(cols, dim=1).detach().cpu().tolist() if cols else [[] for _ in range(n)]

        def contact() -> list[list[float]]:
            import torch
            sd = self.sensor._data  # no lazy update (see module docstring)
            f = _t(sd.net_forces_w)[:, self.s_foot_ids]
            hist = _t(sd.net_forces_w_history)[:, :, self.s_foot_ids].norm(dim=-1).amax(dim=1)
            ct = _t(sd.current_contact_time)[:, self.s_foot_ids]
            at = _t(sd.current_air_time)[:, self.s_foot_ids]
            lat = _t(sd.last_air_time)[:, self.s_foot_ids]
            first = ((ct > 0.0) & (ct < self.step_dt + 1.0e-8)).float()
            base_hist = _t(sd.net_forces_w_history)[:, :, self.s_base_ids].norm(dim=-1).amax(dim=(1, 2))
            cols = []
            for k in range(nf):
                cols.append(torch.stack([f[:, k, 2], f[:, k].norm(dim=-1), hist[:, k], ct[:, k], at[:, k],
                                         lat[:, k], first[:, k]], dim=1))
            cols.append(base_hist.unsqueeze(1))
            age = (_t(self.sensor._timestamp) - _t(self.sensor._timestamp_last_update)).float()
            fresh = ((~_t(self.sensor._is_outdated)) & (age.abs() < 1.0e-6)).float()
            cols.append(torch.stack([fresh, age], dim=1))
            return torch.cat(cols, dim=1).detach().cpu().tolist()

        def terrain() -> list[list[float]]:
            import torch
            hits = _t(self.scanner.data.ray_hits_w)  # the evaluator already read it this step
            pos = _t(robot.data.body_pos_w)[:, self.foot_ids]
            finite = torch.isfinite(hits).all(dim=-1)
            d2 = ((hits[:, None, :, :2] - pos[:, :, None, :2]) ** 2).sum(-1)
            d2 = torch.where(finite[:, None, :], d2, torch.full_like(d2, float("inf")))
            idx = d2.argmin(dim=-1)
            z = hits[..., 2].unsqueeze(1).expand(-1, nf, -1)
            near_z = torch.gather(z, 2, idx.unsqueeze(-1)).squeeze(-1)
            dist = torch.gather(d2, 2, idx.unsqueeze(-1)).squeeze(-1).sqrt()
            zmax = torch.where(d2 <= NEAR_RADIUS_M ** 2, z, torch.full_like(z, float("-inf"))).amax(dim=-1)
            return torch.stack([near_z, zmax, dist], dim=2).reshape(n, nf * 3).detach().cpu().tolist()

        def action() -> list[list[float]]:
            import torch
            am = base.action_manager
            return torch.cat([_t(am.action), _t(am.prev_action)], dim=1).detach().cpu().tolist()

        def reward() -> list[list[float]]:
            return _t(base.reward_manager._step_reward).detach().cpu().tolist()

        def joints() -> list[list[float]]:
            import torch
            d = robot.data
            return torch.cat([_t(d.joint_pos), _t(d.joint_vel), _t(d.computed_torque), _t(d.applied_torque)],
                             dim=1).detach().cpu().tolist()

        b = self._group("body", body, n, 14)
        fe = self._group("feet", feet, n, nf * 6)
        co = self._group("contact", contact, n, nf * 7 + 3) if self.sensor is not None else [[None] * (nf * 7 + 3)] * n
        te = self._group("terrain", terrain, n, nf * 3) if self.scanner is not None else [[None] * (nf * 3)] * n
        ac = self._group("action", action, n, 2 * self.action_dim)
        rw = self._group("reward", reward, n, len(self.reward_names))
        jt = self._group("joints", joints, n, 4 * len(self.joint_names))
        step = self.step + 1
        lines = []
        for e in range(n):
            row: list[float | None] = list(b[e])
            for k in range(nf):
                row += fe[e][6 * k: 6 * k + 6] + co[e][7 * k: 7 * k + 7] + te[e][3 * k: 3 * k + 3]
            row += co[e][nf * 7: nf * 7 + 3] + ac[e] + rw[e] + jt[e]
            lines.append(f"{step},{e}," + ",".join(_fmt(v) for v in row))
        self.handle.write("\n".join(lines) + "\n")
        self.step += 1
        if self.step >= self.max_steps:
            self.close(True)

    def close(self, completed: bool) -> None:
        if self.closed:
            return
        self.closed = True
        if self.handle is not None:
            self.handle.close()
        self.meta.update(completed=completed, steps=self.step, fields=self.fields)
        (self.output / "diag_meta.json").write_text(json.dumps(self.meta, indent=1, sort_keys=True), encoding="utf-8")
        status = "DIAG_COMPLETE" if completed and not self.meta["unavailable"] else (
            "DIAG_PARTIAL" if completed else "DIAG_INCOMPLETE")
        (self.output / "DIAG_STATUS.txt").write_text(f"DIAG_STATUS={status}\nSTEPS={self.step}\n", encoding="utf-8")
