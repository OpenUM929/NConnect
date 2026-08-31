"""Lightweight fixed-policy telemetry for the existing Isaac Lab play runner.

The module is enabled only when ``NCRC_EVAL_OUT`` is set.  It patches
``gymnasium.make`` before Isaac Lab's play script creates the environment and
records the raw command, robot velocity, pose, and termination flags returned
by every environment step.  Normal training and normal video playback are not
changed.

The evaluation runner also sets ``NCRC_EVAL_STEPS``.  After exactly that many
steps the child process flushes the evidence and exits with status 0.  The
outer ``play.py`` process remains alive and performs its usual cleanup/export.
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
    """Return the torch tensor behind Isaac Lab's optional tensor wrapper."""

    return getattr(value, "torch", value)


def _cpu_rows(value: Any) -> list[list[float]]:
    value = _tensor(value).detach().to("cpu")
    if value.ndim == 1:
        value = value.unsqueeze(1)
    return value.tolist()


def _bool_list(value: Any, count: int) -> list[bool]:
    if value is None:
        return [False] * count
    tensor = _tensor(value).detach().to("cpu").reshape(-1)
    return [bool(item) for item in tensor.tolist()]


def _safe_mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _rmse(values: list[float]) -> float | None:
    return math.sqrt(statistics.fmean(value * value for value in values)) if values else None


class TelemetryCollector:
    """Collect per-environment samples without changing policy inputs or actions."""

    def __init__(self, output_dir: Path, max_steps: int) -> None:
        self.output_dir = output_dir
        self.max_steps = max_steps
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.output_dir / "steps.csv"
        self.summary_path = self.output_dir / "summary.json"
        self.status_path = self.output_dir / "STATUS.txt"
        self._file = None
        self._writer = None
        self._step = 0
        self._started = time.time()
        self._term_names: list[str] = []
        self._rows_written = 0
        self._tracking_xy: list[float] = []
        self._tracking_yaw: list[float] = []
        self._speed_xy: list[float] = []
        self._early_terminations = 0
        self._timeouts = 0
        self._termination_counts: dict[str, int] = {}
        self._closed = False

    @staticmethod
    def _base(env: Any) -> Any:
        return getattr(env, "unwrapped", env)

    def attach(self, env: Any) -> None:
        base = self._base(env)
        manager = base.termination_manager
        self._term_names = list(manager.active_terms)
        self._termination_counts = {name: 0 for name in self._term_names}
        self._file = self.csv_path.open("w", newline="", encoding="utf-8")
        fields = [
            "step", "time_s", "env_id",
            "cmd_vx", "cmd_vy", "cmd_wz",
            "actual_vx", "actual_vy", "actual_wz",
            "error_xy", "error_yaw", "speed_xy",
            "root_x", "root_y", "root_z",
            "terminated", "truncated",
        ] + [f"term_{name}" for name in self._term_names]
        self._writer = csv.DictWriter(self._file, fieldnames=fields)
        self._writer.writeheader()

        metadata = {
            "schema_version": 1,
            "max_steps": self.max_steps,
            "num_envs": int(base.num_envs),
            "step_dt": float(base.step_dt),
            "termination_terms": self._term_names,
            "command_term": "base_velocity",
            "robot_asset": "robot",
        }
        (self.output_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
        )

    def record(self, env: Any, result: Any) -> None:
        if self._closed:
            return
        if self._writer is None:
            self.attach(env)

        base = self._base(env)
        command = _cpu_rows(base.command_manager.get_command("base_velocity"))
        robot = base.scene["robot"]
        linear = _cpu_rows(robot.data.root_lin_vel_b)
        angular = _cpu_rows(robot.data.root_ang_vel_b)
        position = _cpu_rows(robot.data.root_pos_w)
        count = len(command)

        terminated = result[2] if isinstance(result, tuple) and len(result) >= 5 else None
        truncated = result[3] if isinstance(result, tuple) and len(result) >= 5 else None
        terminated_rows = _bool_list(terminated, count)
        truncated_rows = _bool_list(truncated, count)
        term_rows = {
            name: _bool_list(base.termination_manager.get_term(name), count)
            for name in self._term_names
        }

        sim_time = (self._step + 1) * float(base.step_dt)
        for env_id in range(count):
            cmd_vx, cmd_vy, cmd_wz = command[env_id][:3]
            actual_vx, actual_vy = linear[env_id][:2]
            actual_wz = angular[env_id][2]
            error_xy = math.hypot(cmd_vx - actual_vx, cmd_vy - actual_vy)
            error_yaw = abs(cmd_wz - actual_wz)
            speed_xy = math.hypot(actual_vx, actual_vy)
            row = {
                "step": self._step + 1,
                "time_s": f"{sim_time:.6f}",
                "env_id": env_id,
                "cmd_vx": f"{cmd_vx:.9g}",
                "cmd_vy": f"{cmd_vy:.9g}",
                "cmd_wz": f"{cmd_wz:.9g}",
                "actual_vx": f"{actual_vx:.9g}",
                "actual_vy": f"{actual_vy:.9g}",
                "actual_wz": f"{actual_wz:.9g}",
                "error_xy": f"{error_xy:.9g}",
                "error_yaw": f"{error_yaw:.9g}",
                "speed_xy": f"{speed_xy:.9g}",
                "root_x": f"{position[env_id][0]:.9g}",
                "root_y": f"{position[env_id][1]:.9g}",
                "root_z": f"{position[env_id][2]:.9g}",
                "terminated": int(terminated_rows[env_id]),
                "truncated": int(truncated_rows[env_id]),
            }
            for name in self._term_names:
                active = term_rows[name][env_id]
                row[f"term_{name}"] = int(active)
                if active:
                    self._termination_counts[name] += 1
            self._writer.writerow(row)
            self._tracking_xy.append(error_xy)
            self._tracking_yaw.append(error_yaw)
            self._speed_xy.append(speed_xy)
            self._early_terminations += int(terminated_rows[env_id])
            self._timeouts += int(truncated_rows[env_id])
            self._rows_written += 1

        self._step += 1
        if self._step % 25 == 0:
            self._file.flush()
        if self._step >= self.max_steps:
            self.close(completed=True)
            os._exit(0)

    def close(self, completed: bool) -> None:
        if self._closed:
            return
        self._closed = True
        if self._file is not None:
            self._file.flush()
            os.fsync(self._file.fileno())
            self._file.close()

        completed_episodes = self._early_terminations + self._timeouts
        summary = {
            "schema_version": 1,
            "completed": completed,
            "steps": self._step,
            "rows": self._rows_written,
            "wall_seconds": time.time() - self._started,
            "tracking_xy_mae": _safe_mean(self._tracking_xy),
            "tracking_xy_rmse": _rmse(self._tracking_xy),
            "tracking_yaw_mae": _safe_mean(self._tracking_yaw),
            "tracking_yaw_rmse": _rmse(self._tracking_yaw),
            "speed_xy_mean": _safe_mean(self._speed_xy),
            "early_terminations": self._early_terminations,
            "timeouts": self._timeouts,
            "completed_episodes": completed_episodes,
            "survival_rate_completed": (
                self._timeouts / completed_episodes if completed_episodes else None
            ),
            "termination_counts": self._termination_counts,
        }
        self.summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
        )
        self.status_path.write_text(
            f"EVAL_RC={0 if completed else 3}\n"
            f"STEPS={self._step}\nROWS={self._rows_written}\n",
            encoding="utf-8",
        )


_INSTALLED = False


def install() -> None:
    """Install the one-shot gym.make hook requested by the evaluation runner."""

    global _INSTALLED
    if _INSTALLED:
        return
    output = os.environ.get("NCRC_EVAL_OUT")
    steps_text = os.environ.get("NCRC_EVAL_STEPS")
    if not output:
        return
    if not steps_text or not steps_text.isdigit() or int(steps_text) <= 0:
        raise RuntimeError("NCRC_EVAL_STEPS must be a positive integer")

    import gymnasium as gym

    collector = TelemetryCollector(Path(output), int(steps_text))
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
    print(f"[eval] telemetry enabled: out={output} steps={steps_text}")

