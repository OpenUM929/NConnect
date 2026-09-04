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


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return repr(value)


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
        self.projected_progress: list[float] = []
        self.speed_by_env: dict[int, list[tuple[float, float]]] = {}
        self.closed = False

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
            "speed_xy", "root_x", "root_y", "root_z", "terminated", "truncated",
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
                "root_z": position[env_id][2], "terminated": int(terminated[env_id]),
                "truncated": int(truncated[env_id]),
            }
            for name in self.term_names:
                row[f"term_{name}"] = int(term_values[name][env_id])
            self.writer.writerow(row)
            self.xy_errors.append(error_xy)
            self.yaw_errors.append(error_yaw)
            if sim_time >= 4.0:
                self.post_push_xy_errors.append(error_xy)
            norm = math.hypot(cmd_vx, cmd_vy)
            if norm > 1.0e-9:
                self.projected_progress.append(
                    (position[env_id][0] * cmd_vx + position[env_id][1] * cmd_vy) / norm
                )
            self.speed_by_env.setdefault(env_id, []).append((sim_time, speed_xy))
            if terminated[env_id]:
                self.terminated_envs.add(env_id)
        self.step += 1
        if self.step % 25 == 0:
            self.handle.flush()
        if self.step >= self.max_steps:
            self.close(True)
            os._exit(0)

    def _recovery(self) -> dict[str, Any]:
        recoveries: list[float] = []
        expected = 0
        quiet_steps = max(1, round(0.5 / self.step_dt))
        for samples in self.speed_by_env.values():
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
                for index in range(peak_index, len(samples) - quiet_steps + 1):
                    window = samples[index:index + quiet_steps]
                    if all(speed <= 0.15 for _, speed in window):
                        recoveries.append(window[0][0] - peak_time)
                        break
        return {
            "expected_events": expected,
            "recovered_events": len(recoveries),
            "recovery_rate": len(recoveries) / expected if expected else None,
            "median_recovery_s": statistics.median(recoveries) if recoveries else None,
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
        if self.projected_progress:
            progress = max(0.0, max(self.projected_progress) - min(self.projected_progress))
        summary = {
            "schema_version": 1,
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
            "survival_proxy": 1.0 - len(self.terminated_envs) / self.num_envs if self.num_envs else None,
            "projected_progress_m": progress,
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

    collector = Collector(Path(output), int(steps))
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
