"""Evaluator entry point for the G-A052 diagnostic replay (shipped as ``go2_eval_telemetry.py`` in the diag root).

play.py imports ``go2_eval_telemetry.install`` when NCRC_EVAL_OUT is set.  In the diag
root that name is this wrapper.  It installs the unchanged schema-6 evaluator first
(shipped next to it as ``go2_eval_telemetry_v6.py``, byte-identical to the evaluator
that measured G-A048), then wraps the environment's step once more so the read-only
diagnostic recorder runs after the evaluator on every step.  The wrapper passes the
action through and returns the step result unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import go2_eval_telemetry_v6 as _base
from go2_eval_diag import DiagRecorder

_INSTALLED = False


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _base.install()
    output = os.environ.get("NCRC_EVAL_OUT")
    steps = os.environ.get("NCRC_EVAL_STEPS")
    if not output:
        return
    import gymnasium as gym

    recorder = DiagRecorder(Path(output), int(steps))
    evaluator_make = gym.make  # already the evaluator's make_with_telemetry

    def make_with_diag(*args: Any, **kwargs: Any) -> Any:
        env = evaluator_make(*args, **kwargs)
        evaluator_step = env.step

        def diag_step(action: Any) -> Any:
            result = evaluator_step(action)
            recorder.record(env)
            return result

        env.step = diag_step
        return env

    gym.make = make_with_diag
    _INSTALLED = True
    print(f"[go2-diag] read-only diagnostic channels enabled: out={output}/diag.csv.gz")
