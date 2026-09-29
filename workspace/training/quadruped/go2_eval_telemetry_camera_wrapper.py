"""Evaluator entry point for the G-A056 video replay (shipped as ``go2_eval_telemetry.py`` in the video root).

play.py imports ``go2_eval_telemetry.install`` when NCRC_EVAL_OUT is set.  In the video root that name
is this wrapper.  It installs the unchanged schema-6 evaluator first (shipped next to it as
``go2_eval_telemetry_v6.py``), so the video run also writes steps.csv for the reproduction check, then
wraps the environment's step once more so the read-only camera probe runs after the evaluator on every
step.  GO2_CAMERA_TARGET_ENV is the env index the command line asked the viewer to follow.  The wrapper
passes the action through and returns the step result unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import go2_eval_telemetry_v6 as _base
from go2_eval_camera_probe import CameraProbe

_INSTALLED = False


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _base.install()
    output = os.environ.get("NCRC_EVAL_OUT")
    steps = os.environ.get("NCRC_EVAL_STEPS")
    target = os.environ.get("GO2_CAMERA_TARGET_ENV")
    if not output:
        return
    if target is None or not target.isdigit():
        raise RuntimeError("GO2_CAMERA_TARGET_ENV must be the env index the viewer follows")
    import gymnasium as gym

    probe = CameraProbe(Path(output), int(steps), int(target))
    evaluator_make = gym.make  # already the evaluator's make_with_telemetry

    def make_with_probe(*args: Any, **kwargs: Any) -> Any:
        env = evaluator_make(*args, **kwargs)
        evaluator_step = env.step

        def probe_step(action: Any) -> Any:
            result = evaluator_step(action)
            probe.record(env)
            return result

        env.step = probe_step
        return env

    gym.make = make_with_probe
    _INSTALLED = True
    print(f"[go2-camera] read-only camera probe enabled: target_env={target} out={output}/camera.csv")
