"""Opt-in telemetry hook for Go2 fixed-policy evaluation.

Enabled only when ``NCRC_EVAL_OUT`` is set by the server runner.  The hook
observes the environment after every step and stops after the requested fixed
horizon.  It does not alter observations, actions, rewards, or training.
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
import time
from pathlib import Path
from typing import Any


def _tensor(value: Any) -> Any:
    return getattr(value, "torch", value)


def _rows(value: Any) -> list[list[float]]:
    tensor = _tensor(value).detach().to("cpu")
    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(1)
    return tensor.tolist()


def _bools(value: Any, count: int) -> list[bool]:
    if value is None:
        return [False] * count
    return [bool(item) for item in _tensor(value).detach().to("cpu").reshape(-1).tolist()]


def _rmse(values: list[float]) -> float | None:
    return math.sqrt(statistics.fmean(value * value for value in values)) if values else None


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _projected_displacement(
    actual_vx: float,
    actual_vy: float,
    cmd_vx: float,
    cmd_vy: float,
    step_dt: float,
) -> float | None:
    """Return one step of command-aligned body-frame displacement."""
    norm = math.hypot(cmd_vx, cmd_vy)
    if norm <= 1.0e-9:
        return None
    return ((actual_vx * cmd_vx + actual_vy * cmd_vy) / norm) * step_dt


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return repr(value)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    try:
        return float(raw) if raw not in (None, "") else default
    except ValueError:
        return default


# Posture gate.  The prelim guide defines survival as "넘어지지 않고 완주한 비율"
# (the share that finished without falling), not as "no termination event fired".
# A Go2 that splays its legs and rests its belly on the ground has fallen by that
# definition while never tripping ``base_contact``.  Upright therefore requires
# both that gravity still points down through the base and that the base is held
# clear of the terrain directly beneath it.
FALL_TILT_COS = _env_float("NCRC_EVAL_FALL_TILT_COS", 0.5)      # 0.5 -> 60 deg
FALL_HEIGHT_M = _env_float("NCRC_EVAL_FALL_HEIGHT", 0.18)       # Go2 stands ~0.32
# Fraction of rows -- and of each env's rows -- that must carry both posture
# channels before a survival number may be published at all.  Not operator
# overridable: it is what makes the published number mean what it says.
POSTURE_MIN_COVERAGE = 0.99
FALL_HOLD_S = _env_float("NCRC_EVAL_FALL_HOLD_S", 0.5)
FALL_GRACE_S = _env_float("NCRC_EVAL_FALL_GRACE_S", 0.5)


def _finite_mean(values: list[float]) -> float | None:
    """Mean of the finite entries only; ray-caster misses come back as inf."""
    finite = [v for v in values if math.isfinite(v)]
    return statistics.fmean(finite) if finite else None


class Collector:
    def __init__(self, output: Path, max_steps: int) -> None:
        self.output = output
        self.max_steps = max_steps
        self.output.mkdir(parents=True, exist_ok=True)
        self.step = 0
        self.started = time.time()
        self.handle = None
        self.writer = None
        self.num_envs = 0
        self.step_dt = 0.0
        self.term_names: list[str] = []
        self.terminated_envs: set[int] = set()
        self.xy_errors: list[float] = []
        self.yaw_errors: list[float] = []
        self.post_push_xy_errors: list[float] = []
        # Net command-aligned travel is accumulated independently per
        # environment from body-frame velocity.  World-space spawn locations
        # differ by terrain tile, so aggregating absolute root positions across
        # environments falsely reports the tile spacing as robot progress.
        self.projected_progress_by_env: dict[int, float] = {}
        self.speed_by_env: dict[int, list[tuple[float, float]]] = {}
        # Posture bookkeeping: how long each env has been continuously
        # non-upright, and whether that ever exceeded FALL_HOLD_S.  A row with no
        # posture evidence used to be scored upright, which reset this timer -- so
        # one missing frame inside a 0.8 s collapse split the run in two and the
        # fall disappeared.  The primary timer now holds across an unmeasured row,
        # and two bounding timers record what the verdict would be if every gap
        # were read the best way (optimistic) and the worst way (pessimistic).
        self.non_upright_run_s: dict[int, float] = {}
        self.optimistic_run_s: dict[int, float] = {}
        self.pessimistic_run_s: dict[int, float] = {}
        self.fallen_envs: set[int] = set()
        self.fallen_envs_optimistic: set[int] = set()
        self.fallen_envs_pessimistic: set[int] = set()
        self.upright_by_env: dict[int, list[tuple[float, bool]]] = {}
        self.height_rel_samples: list[float] = []
        self.posture_measured = False
        # A single measured row used to be enough to mark the whole run measured,
        # while every unmeasured row was scored upright.  Coverage is counted per
        # row and per env so a partially blind run cannot publish a survival
        # number computed over every env.
        self.posture_rows_measured = 0
        self.posture_rows_total = 0
        self.posture_rows_by_env: dict[int, int] = {}
        self.rows_by_env: dict[int, int] = {}
        # Rows whose kinematics were not finite numbers.  A blown-up physics step
        # arrives as inf/nan, and inf passed every threshold test in the gate --
        # ``inf >= FALL_HEIGHT_M`` is true, so a robot at infinite height was
        # scored upright, measured, and fully covered.
        self.nonfinite_rows = 0
        self.nonfinite_envs: set[int] = set()
        self.closed = False

    @property
    def finished(self) -> bool:
        """Return whether the fixed evaluation horizon has been collected."""
        return self.closed and self.step >= self.max_steps

    @staticmethod
    def _base(env: Any) -> Any:
        return getattr(env, "unwrapped", env)

    def attach(self, env: Any) -> None:
        base = self._base(env)
        self.num_envs = int(base.num_envs)
        self.step_dt = float(base.step_dt)
        self.term_names = list(base.termination_manager.active_terms)
        self.handle = (self.output / "steps.csv").open("w", newline="", encoding="utf-8")
        fields = [
            "step", "time_s", "env_id", "cmd_vx", "cmd_vy", "cmd_wz",
            "actual_vx", "actual_vy", "actual_wz", "error_xy", "error_yaw",
            "speed_xy", "root_x", "root_y", "root_z",
            "proj_grav_z", "terrain_z", "height_rel", "upright",
            "terminated", "truncated",
        ] + [f"term_{name}" for name in self.term_names]
        self.writer = csv.DictWriter(self.handle, fieldnames=fields)
        self.writer.writeheader()

        robot = base.scene["robot"]
        masses = None
        try:
            masses = _rows(robot.root_physx_view.get_masses())
        except Exception:  # Isaac Lab/PhysX version dependent evidence field.
            pass
        events = getattr(getattr(base, "cfg", None), "events", None)
        metadata = {
            "schema_version": 1,
            "case_id": os.environ.get("NCRC_EVAL_CASE"),
            "scenario_id": os.environ.get("NCRC_EVAL_SCENARIO"),
            "evaluation_seed": os.environ.get("NCRC_EVAL_SEED"),
            "max_steps": self.max_steps,
            "num_envs": self.num_envs,
            "step_dt": self.step_dt,
            "termination_terms": self.term_names,
            "realized_randomization_values": {
                "robot_body_masses": masses,
                "events_config": _jsonable(events),
            },
        }
        (self.output / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
        )

    def _posture(self, base: Any, robot: Any, count: int) -> tuple[list[float], list[float | None]]:
        """Return per-env (projected gravity z, terrain height under the base).

        Both are optional evidence: an Isaac Lab build without
        ``projected_gravity_b`` or a scene without ``height_scanner`` must
        degrade to the legacy metric rather than abort a paid evaluation.
        """
        try:
            gravity = [row[2] for row in _rows(robot.data.projected_gravity_b)]
        except Exception:  # Isaac Lab version dependent field.
            gravity = [float("nan")] * count
        terrain: list[float | None] = [None] * count
        try:
            hits = _tensor(base.scene["height_scanner"].data.ray_hits_w)
            hits = hits.detach().to("cpu")[..., 2].tolist()
            terrain = [_finite_mean(row if isinstance(row, list) else [row]) for row in hits]
        except Exception:  # Scene without a height scanner.
            pass
        return gravity, terrain

    def _fall_timer(
        self,
        runs: dict[int, float],
        fallen: set[int],
        env_id: int,
        upright: bool,
    ) -> None:
        """Advance one reading of the continuous non-upright timer for one env."""
        if upright:
            runs[env_id] = 0.0
            return
        run = runs.get(env_id, 0.0) + self.step_dt
        runs[env_id] = run
        if run >= FALL_HOLD_S:
            fallen.add(env_id)

    def record(self, env: Any, result: Any) -> None:
        if self.closed:
            return
        if self.writer is None:
            self.attach(env)
        base = self._base(env)
        commands = _rows(base.command_manager.get_command("base_velocity"))
        robot = base.scene["robot"]
        linear = _rows(robot.data.root_lin_vel_b)
        angular = _rows(robot.data.root_ang_vel_b)
        position = _rows(robot.data.root_pos_w)
        count = len(commands)
        gravity_z, terrain_z = self._posture(base, robot, count)
        terminated = _bools(result[2] if len(result) >= 5 else None, count)
        truncated = _bools(result[3] if len(result) >= 5 else None, count)
        term_values = {
            name: _bools(base.termination_manager.get_term(name), count)
            for name in self.term_names
        }
        sim_time = (self.step + 1) * self.step_dt
        for env_id in range(count):
            cmd_vx, cmd_vy, cmd_wz = commands[env_id][:3]
            actual_vx, actual_vy = linear[env_id][:2]
            actual_wz = angular[env_id][2]
            error_xy = math.hypot(cmd_vx - actual_vx, cmd_vy - actual_vy)
            error_yaw = abs(cmd_wz - actual_wz)
            speed_xy = math.hypot(actual_vx, actual_vy)
            row = {
                "step": self.step + 1, "time_s": f"{sim_time:.6f}", "env_id": env_id,
                "cmd_vx": cmd_vx, "cmd_vy": cmd_vy, "cmd_wz": cmd_wz,
                "actual_vx": actual_vx, "actual_vy": actual_vy, "actual_wz": actual_wz,
                "error_xy": error_xy, "error_yaw": error_yaw, "speed_xy": speed_xy,
                "root_x": position[env_id][0], "root_y": position[env_id][1],
                "root_z": position[env_id][2],
                "terminated": int(terminated[env_id]),
                "truncated": int(truncated[env_id]),
            }
            if not all(
                math.isfinite(value)
                for value in (
                    cmd_vx, cmd_vy, cmd_wz, actual_vx, actual_vy, actual_wz,
                    position[env_id][0], position[env_id][1], position[env_id][2],
                )
            ):
                self.nonfinite_rows += 1
                self.nonfinite_envs.add(env_id)
            grav_z = gravity_z[env_id]
            ground = terrain_z[env_id]
            height_rel = (
                position[env_id][2] - ground if ground is not None else None
            )
            # An unusable reading is an absence of a reading.  Substituting a
            # plausible value here would hide the fault; None routes it into the
            # coverage and ambiguity checks like any other unobserved row.
            if height_rel is not None and not math.isfinite(height_rel):
                height_rel = None
            tilt_ok = math.isfinite(grav_z) and grav_z <= -FALL_TILT_COS
            height_ok = height_rel is None or height_rel >= FALL_HEIGHT_M
            # Both channels are required.  Engine 1.4.0 accepted either one, so a
            # scene without a height scanner still reported posture_gate_v2 while
            # only the tilt channel was live -- two runs could then carry the same
            # source label and different evidence.
            measured = math.isfinite(grav_z) and height_rel is not None
            # None, not True.  An unobserved row is an absence of evidence, and an
            # absence of evidence is not evidence of an upright robot.
            upright = bool(tilt_ok and height_ok) if measured else None
            self.posture_rows_total += 1
            self.rows_by_env[env_id] = self.rows_by_env.get(env_id, 0) + 1
            if measured:
                self.posture_measured = True
                self.posture_rows_measured += 1
                self.posture_rows_by_env[env_id] = self.posture_rows_by_env.get(env_id, 0) + 1
            if height_rel is not None:
                self.height_rel_samples.append(height_rel)
            row["proj_grav_z"] = grav_z
            row["terrain_z"] = ground
            row["height_rel"] = height_rel
            row["upright"] = "" if upright is None else int(upright)
            # Ignore the drop-in transient, then require FALL_HOLD_S of
            # continuous non-upright posture before calling it a fall.  One bad
            # frame on a stair edge is not a fall; lying down for half a second is.
            if sim_time >= FALL_GRACE_S:
                if upright is not None:
                    self._fall_timer(self.non_upright_run_s, self.fallen_envs, env_id, upright)
                self._fall_timer(
                    self.optimistic_run_s, self.fallen_envs_optimistic, env_id,
                    True if upright is None else upright,
                )
                self._fall_timer(
                    self.pessimistic_run_s, self.fallen_envs_pessimistic, env_id,
                    False if upright is None else upright,
                )
            # Recovery credit needs positive evidence of an upright base, so an
            # unobserved row counts against it rather than for it.
            self.upright_by_env.setdefault(env_id, []).append((sim_time, bool(upright)))
            for name in self.term_names:
                row[f"term_{name}"] = int(term_values[name][env_id])
            self.writer.writerow(row)
            self.xy_errors.append(error_xy)
            self.yaw_errors.append(error_yaw)
            if sim_time >= 4.0:
                self.post_push_xy_errors.append(error_xy)
            displacement = _projected_displacement(
                actual_vx, actual_vy, cmd_vx, cmd_vy, self.step_dt
            )
            if displacement is not None and env_id not in self.terminated_envs:
                self.projected_progress_by_env[env_id] = (
                    self.projected_progress_by_env.get(env_id, 0.0)
                    + displacement
                )
            self.speed_by_env.setdefault(env_id, []).append((sim_time, speed_xy))
            if terminated[env_id]:
                self.terminated_envs.add(env_id)
        self.step += 1
        if self.step % 25 == 0:
            self.handle.flush()
        if self.step >= self.max_steps:
            self.close(True)

    def _recovery(self) -> dict[str, Any]:
        # ``recovery_rate`` alone is not evidence of recovery: its quiet-window
        # test (speed <= 0.15 m/s) is satisfied trivially by a robot that is
        # lying on the ground and never moved.  ``recovery_rate_upright``
        # additionally requires the base to be upright across the whole window,
        # and is the figure that may be quoted as recovery.
        recoveries: list[float] = []
        upright_recoveries: list[float] = []
        expected = 0
        quiet_steps = max(1, round(0.5 / self.step_dt))
        for env_id, samples in self.speed_by_env.items():
            upright_samples = self.upright_by_env.get(env_id, [])
            max_time = samples[-1][0] if samples else 0.0
            for push_time in (4.0, 8.0, 12.0, 16.0):
                if push_time + 1.0 > max_time:
                    continue
                expected += 1
                candidates = [
                    (index, stamp, speed) for index, (stamp, speed) in enumerate(samples)
                    if push_time <= stamp <= push_time + 1.0
                ]
                if not candidates:
                    continue
                peak_index, peak_time, _ = max(candidates, key=lambda item: item[2])
                found_quiet = False
                for index in range(peak_index, len(samples) - quiet_steps + 1):
                    window = samples[index:index + quiet_steps]
                    if not all(speed <= 0.15 for _, speed in window):
                        continue
                    if not found_quiet:
                        recoveries.append(window[0][0] - peak_time)
                        found_quiet = True
                    upright_window = upright_samples[index:index + quiet_steps]
                    if upright_window and all(flag for _, flag in upright_window):
                        upright_recoveries.append(window[0][0] - peak_time)
                        break
        return {
            "expected_events": expected,
            "recovered_events": len(recoveries),
            "recovery_rate": len(recoveries) / expected if expected else None,
            "median_recovery_s": statistics.median(recoveries) if recoveries else None,
            "upright_recovered_events": len(upright_recoveries),
            "recovery_rate_upright": (
                len(upright_recoveries) / expected if expected else None
            ),
            "median_upright_recovery_s": (
                statistics.median(upright_recoveries) if upright_recoveries else None
            ),
            "posture_measured": self.posture_measured,
        }

    def close(self, completed: bool) -> None:
        if self.closed:
            return
        self.closed = True
        if self.handle is not None:
            self.handle.flush()
            os.fsync(self.handle.fileno())
            self.handle.close()
        progress = None
        if self.projected_progress_by_env:
            progress = max(0.0, statistics.median(self.projected_progress_by_env.values()))
        fallen = len(self.fallen_envs | self.terminated_envs)
        # Survival divides by every env, so it may only be published when every
        # env was actually watched.  ``posture_measured`` alone is satisfied by
        # one measured row out of millions.
        coverage = (
            self.posture_rows_measured / self.posture_rows_total
            if self.posture_rows_total
            else 0.0
        )
        env_coverages = [
            self.posture_rows_by_env.get(env_id, 0) / rows
            for env_id, rows in sorted(self.rows_by_env.items())
            if rows
        ]
        min_env_coverage = min(env_coverages) if env_coverages else 0.0
        envs_seen = len(self.rows_by_env)
        coverage_ok = (
            bool(self.num_envs)
            and envs_seen == self.num_envs
            and coverage >= POSTURE_MIN_COVERAGE
            and min_env_coverage >= POSTURE_MIN_COVERAGE
        )
        # Coverage alone does not make a fall verdict safe: at 0.99 the worst env
        # may still miss 1% of its rows, and a single missing row landing inside a
        # collapse used to erase the whole fall.  The verdict is published only if
        # reading every gap the best way and reading every gap the worst way give
        # the same set of fallen envs -- i.e. only if the gaps could not have
        # changed the answer.
        optimistic_fallen = self.fallen_envs_optimistic | self.terminated_envs
        pessimistic_fallen = self.fallen_envs_pessimistic | self.terminated_envs
        fall_verdict_ambiguous = optimistic_fallen != pessimistic_fallen
        survival_v2 = (
            1.0 - fallen / self.num_envs
            if self.num_envs
            and not self.nonfinite_rows
            and self.posture_measured
            and coverage_ok
            and not fall_verdict_ambiguous
            else None
        )
        if survival_v2 is None:
            if self.nonfinite_rows:
                survival_source = "KINEMATICS_NONFINITE"
            elif not self.posture_measured:
                survival_source = "POSTURE_UNMEASURED"
            elif not coverage_ok:
                survival_source = "POSTURE_COVERAGE_INSUFFICIENT"
            else:
                survival_source = "POSTURE_FALL_VERDICT_AMBIGUOUS"
        else:
            survival_source = "posture_gate_v2"
        heights = sorted(self.height_rel_samples)
        summary = {
            # The version is the ruler's name.  Two summaries can carry the same
            # survival_proxy_source string and rest on different evidence, so a
            # change in what "survived" means bumps this:
            #   3 (1.5.0) both posture channels required, no v1 fallback;
            #   4 (1.5.2) row and per-env coverage floor;
            #   5 (1.5.3) an unobserved row is no longer scored upright, and the
            #             fall verdict must be insensitive to how the gaps read;
            #   6 (1.5.4) a non-finite reading is an absent reading, and a case
            #             with non-finite kinematics publishes no survival.
            "schema_version": 6,
            "measurement_contract": (
                "posture_gate_v2/both_channels_required/no_v1_fallback"
                f"/row_and_env_coverage_{POSTURE_MIN_COVERAGE}"
                "/missing_rows_not_upright/fall_verdict_unambiguous"
                "/finite_kinematics_required"
            ),
            "completed": completed,
            "steps": self.step,
            "step_dt": self.step_dt,
            "rows": self.step * self.num_envs,
            "wall_seconds": time.time() - self.started,
            "tracking_xy_rmse": _rmse(self.xy_errors),
            "tracking_yaw_rmse": _rmse(self.yaw_errors),
            "post_push_tracking_xy_rmse": _rmse(self.post_push_xy_errors),
            "speed_xy_mean": _mean([speed for rows in self.speed_by_env.values() for _, speed in rows]),
            "terminated_env_count": len(self.terminated_envs),
            # v1 counts only termination events and scores a collapsed-but-alive
            # robot 1.0.  Retained unchanged so v1 results stay comparable.
            "survival_proxy_v1": 1.0 - len(self.terminated_envs) / self.num_envs if self.num_envs else None,
            # v2 is the posture-gated figure aligned with the guide's wording.
            # It is None when neither posture channel was available, so a
            # consumer can never silently read a legacy number as a v2 number.
            "survival_proxy_v2": survival_v2,
            # No silent fallback.  Engine 1.4.0 quietly published the
            # termination-only number under the plain ``survival_proxy`` key when
            # posture was unavailable, which is how a non-walking policy scored
            # 1.0 survival on every case.  When posture is unmeasured the scored
            # field is None, the scenario goes incomplete, and the run says so.
            "survival_proxy": survival_v2,
            "survival_proxy_source": survival_source,
            "fallen_env_count": len(self.fallen_envs),
            "posture_measured": self.posture_measured,
            "posture_coverage": coverage,
            "posture_min_env_coverage": min_env_coverage,
            "posture_envs_observed": envs_seen,
            "posture_min_coverage_required": POSTURE_MIN_COVERAGE,
            # True means the unobserved rows could have changed who fell, so no
            # survival number is published for this case.
            "posture_fall_verdict_ambiguous": fall_verdict_ambiguous,
            "posture_fall_env_count_optimistic": len(optimistic_fallen),
            "posture_fall_env_count_pessimistic": len(pessimistic_fallen),
            # Non-zero means the physics produced values a metric cannot be
            # computed from, so this case carries no survival number at all.
            "nonfinite_row_count": self.nonfinite_rows,
            "nonfinite_env_count": len(self.nonfinite_envs),
            "posture_gate": {
                "tilt_cos_max": FALL_TILT_COS,
                "height_rel_min_m": FALL_HEIGHT_M,
                "hold_s": FALL_HOLD_S,
                "grace_s": FALL_GRACE_S,
            },
            "height_rel_p10": heights[len(heights) // 10] if heights else None,
            "height_rel_median": statistics.median(heights) if heights else None,
            "height_rel_mean": _mean(heights),
            "projected_progress_m": progress,
            "projected_progress_method": "median_per_env_body_velocity_integral_v2",
            "recovery": self._recovery(),
        }
        (self.output / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
        )
        (self.output / "STATUS.txt").write_text(
            f"EVAL_RC={0 if completed else 3}\nSTEPS={self.step}\nROWS={self.step * self.num_envs}\n",
            encoding="utf-8",
        )


_INSTALLED = False


def _install_graceful_stop(app_launcher_type: type[Any], collector: Collector) -> None:
    """Stop the upstream play loop without bypassing Isaac Sim cleanup.

    Isaac Lab's play loop is controlled by ``simulation_app.is_running()`` and
    closes both the environment and the SimulationApp after that method returns
    false.  The previous telemetry hook performed a hard process exit inside
    ``env.step``.  That skipped both cleanup calls and made the next Kit startup
    inherit the risk from an unclean GPU/Kit shutdown.
    """

    original_init = app_launcher_type.__init__

    def init_with_fixed_horizon(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        app = self.app
        original_is_running = app.is_running

        def is_running_until_collected() -> bool:
            return not collector.finished and bool(original_is_running())

        app.is_running = is_running_until_collected

    app_launcher_type.__init__ = init_with_fixed_horizon


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    output = os.environ.get("NCRC_EVAL_OUT")
    steps = os.environ.get("NCRC_EVAL_STEPS")
    if not output:
        return
    if not steps or not steps.isdigit() or int(steps) <= 0:
        raise RuntimeError("NCRC_EVAL_STEPS must be a positive integer")
    import gymnasium as gym
    from isaaclab.app import AppLauncher

    collector = Collector(Path(output), int(steps))
    _install_graceful_stop(AppLauncher, collector)
    original_make = gym.make

    def make_with_telemetry(*args: Any, **kwargs: Any) -> Any:
        env = original_make(*args, **kwargs)
        collector.attach(env)
        original_step = env.step

        def measured_step(action: Any) -> Any:
            result = original_step(action)
            collector.record(env, result)
            return result

        env.step = measured_step
        return env

    gym.make = make_with_telemetry
    _INSTALLED = True
    print(f"[go2-eval] telemetry enabled: out={output} steps={steps}")
