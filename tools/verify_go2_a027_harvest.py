#!/usr/bin/env python3
"""Verify a recovered G-A027 harvest before any of its numbers are scored.

The evaluator checks its own output while it runs, and the runner checks the
summary it wrote.  Both of those are the producer's word for it.  This tool is
the consumer's own check, run locally on GPU 0 after the harvest comes back.

Engine 1.5.5 of this tool answers the round-5 audit: a range check is not a
recomputation.  ``summary.json`` is now treated as a *claim about* ``steps.csv``
and every scored figure is re-derived from the rows with the collector's own
definitions -- RMSE, survival, recovery, progress, coverage -- so a summary
whose numbers are merely plausible no longer passes.  Specifically it checks:

  * the case set is exactly the registry's 69 per arm -- no missing case, and
    no extra case that would let a bad one be quietly dropped;
  * the raw rows form a complete (step, env) grid: no duplicate pair standing
    in for a deleted one, no step or env outside the declared run;
  * every column the scoring path reads parses as the type it must be, and the
    ``upright`` column holds only the three values the collector can write;
  * posture is re-derived from ``proj_grav_z`` and ``height_rel`` through the
    case's own gate and compared with the ``upright`` the collector recorded;
  * survival, tracking RMSE, post-push RMSE, upright recovery rate, projected
    progress, mean speed and both coverages are recomputed from the rows and
    compared with the summary, so a forged in-range figure is caught;
  * each case carries the figures *its own scenario* is scored on -- push cases
    the post-push RMSE and the upright recovery rate, stairs cases the
    projected progress -- and none of them is NaN or infinite;
  * ``STATUS.txt`` is parsed as key=value, so ``EVAL_RC=01`` is not ``EVAL_RC=0``;
  * ``metadata.json`` agrees with the summary on run length, step_dt and envs;
  * both arms were measured with one ruler, and that ruler is the approved one:
    model, env, evaluator and registry hashes and the run's env/step counts are
    compared with the run plan read out of the runner script, not assumed.

It never repairs and never excludes.  A case that fails is named and the arm's
measurement is reported incomplete; dropping it to complete the other 68 is the
one move this tool exists to prevent.

Without a readable run plan the harvest can be found internally consistent but
not identified, and the verdict is INTERNAL_GATE_INCONCLUSIVE, never PASS.

Exit 0 only when every arm passes every check against a known run plan.

    python -B tools/verify_go2_a027_harvest.py --harvest <_keep/go2_a017_full_suite> \
        [--registry workspace/training/quadruped/config/go2_self_eval_registry.json] \
        [--runner workspace/training/quadruped/server_run_go2_a017_full_suite.sh] \
        [--evaluator workspace/training/quadruped/go2_eval_telemetry.py] \
        [--expect-steps N] [--arms a017,pilot] [--out harvest_verification.json]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any

# The ruler this harvest must have been measured with.  Engine 1.5.4.
EXPECTED_SCHEMA = 6
EXPECTED_CONTRACT = (
    "posture_gate_v2/both_channels_required/no_v1_fallback"
    "/row_and_env_coverage_0.99/missing_rows_not_upright"
    "/fall_verdict_unambiguous/finite_kinematics_required"
)
EXPECTED_SOURCE = "posture_gate_v2"
EXPECTED_GATE = {
    "tilt_cos_max": 0.5,
    "height_rel_min_m": 0.18,
    "hold_s": 0.5,
    "grace_s": 0.5,
}
MIN_COVERAGE = 0.99

# The nine inputs the collector counts.  Re-counted here from the CSV columns
# they are written to, so this is an independent reading of the same evidence
# rather than a second look at the collector's own tally.
KINEMATIC_COLUMNS = (
    "root_x", "root_y", "root_z",
    "actual_vx", "actual_vy", "actual_wz",
    "cmd_vx", "cmd_vy", "cmd_wz",
)
# Columns the collector derives from the nine above.  Recomputed here too, so a
# forged error column is caught even when its inputs are untouched.
DERIVED_COLUMNS = ("error_xy", "error_yaw", "speed_xy")
POSTURE_COLUMNS = ("proj_grav_z", "terrain_z", "height_rel", "upright")
INDEX_COLUMNS = ("step", "env_id", "time_s")
FLAG_COLUMNS = ("terminated", "truncated")
REQUIRED_COLUMNS = (
    INDEX_COLUMNS + KINEMATIC_COLUMNS + DERIVED_COLUMNS
    + POSTURE_COLUMNS + FLAG_COLUMNS
)

# go2_eval_telemetry.py writes ``"" if upright is None else int(upright)``, so
# these three strings are the entire value domain.  Anything else is a damaged
# or hand-edited file, not an unobserved row, and must not be counted as one.
UPRIGHT_DOMAIN = frozenset({"", "0", "1"})
TERMINATED_DOMAIN = frozenset({"", "0", "1", "True", "False"})
TERMINATED_TRUE = frozenset({"1", "True"})

# The recovery definition the collector scores, restated so it can be recomputed.
RECOVERY_PUSH_TIMES = (4.0, 8.0, 12.0, 16.0)
RECOVERY_WINDOW_S = 0.5
RECOVERY_QUIET_SPEED = 0.15
# Rows at or after this stamp are the post-push tracking window.
PUSH_WINDOW_START_S = 4.0

# Recomputation tolerance.  The summary is written from float accumulations in
# the same order this tool replays, so agreement is close to exact; the margin
# covers CSV round-tripping of the columns, not a difference of definition.
TOL = 1e-6
# time_s is serialised as ``f"{sim_time:.6f}"`` over ``step * step_dt``, so for a
# given step index exactly one stamp is writable and there is no tolerance to
# set.  A tolerance was the wrong shape for this check: the scored figures split
# on stamps (the push window at 4s, the four recovery windows, the fall grace),
# so a shift small enough to pass any tolerance can still carry a row across a
# boundary and change the figure the score is read from.  Equality of the value
# is the check; anything else is a clock that disagrees with its own step index.


def canonical_stamp(step: int, step_dt: float) -> float:
    """The one stamp the collector can write for this step index."""
    return float("%.6f" % (step * float(step_dt)))

# Every identity hash the runner writes is a sha256sum digest.  A value that is
# not one is a damaged or hand-edited identity, not an unknown policy.
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA256_IDENTITY_FIELDS = ("evaluator_sha256", "registry_sha256",
                          "model_sha256", "env_sha256")

# Figures every case's scoring path consumes, with the range each must lie in.
# None as an upper bound means "finite and non-negative"; a metric outside its
# range is a measurement fault, never a performance result.
BASE_SCORED_FIELDS: dict[str, tuple[float, float | None]] = {
    "survival_proxy": (0.0, 1.0),
    "survival_proxy_v1": (0.0, 1.0),
    "tracking_xy_rmse": (0.0, None),
    "tracking_yaw_rmse": (0.0, None),
    "speed_xy_mean": (0.0, None),
    "posture_coverage": (0.0, 1.0),
    "posture_min_env_coverage": (0.0, 1.0),
}
# go2_fixed_eval_report.py:44-60 scores push cases on these two and nothing
# else; they were absent from this tool until the round-5 audit found them.
PUSH_SCORED_FIELDS: dict[str, tuple[float, float | None]] = {
    "post_push_tracking_xy_rmse": (0.0, None),
    "recovery.recovery_rate_upright": (0.0, 1.0),
}
# go2_fixed_eval_report.py:35-39 scores stairs cases on progress against the
# run's own duration, so the two duration terms are scored inputs there too.
STAIRS_SCORED_FIELDS: dict[str, tuple[float, float | None]] = {
    "projected_progress_m": (0.0, None),
    "steps": (1.0, None),
    "step_dt": (0.0, None),
}

# Fields that must read identically on both arms, or the two 69-case scorecards
# were produced by two different instruments and their difference means nothing.
ARM_IDENTITY_FIELDS = ("evaluator_sha256", "registry_sha256")
ARM_IDENTITY_REQUIRED = ARM_IDENTITY_FIELDS + ("model_sha256", "env_sha256")
CASE_IDENTITY_FIELDS = (
    "schema_version", "measurement_contract", "survival_proxy_source",
    "step_dt", "steps", "posture_gate", "posture_min_coverage_required",
)


def expected_cases(registry: dict[str, Any]) -> set[tuple[str, str, int]]:
    """Return every (scenario, case, seed) the registry says must be present."""
    seeds = registry["score"]["internal_gates"]["required_evaluation_seeds"]
    wanted: set[tuple[str, str, int]] = set()
    for scenario in registry["scenarios"]:
        for case_id in scenario["internal_cases"]:
            if scenario["id"] == "G7":
                # G7's case id carries its own seed; it is not crossed with the
                # seed set, so crossing it here would demand 9 runs the runner
                # never performs.
                wanted.add((scenario["id"], case_id, int(case_id.rsplit("_", 1)[1])))
            else:
                for seed in seeds:
                    wanted.add((scenario["id"], case_id, int(seed)))
    return wanted


def scored_fields_for(case_id: str) -> dict[str, tuple[float, float | None]]:
    """Return the scored figures this particular case must carry.

    Scoped by case, deliberately.  Demanding the push figures of every case
    would reject the legitimate ``None`` a non-push case writes for them.
    """
    fields = dict(BASE_SCORED_FIELDS)
    if case_id.startswith("push_"):
        fields.update(PUSH_SCORED_FIELDS)
    if case_id.startswith("stairs_"):
        fields.update(STAIRS_SCORED_FIELDS)
    return fields


def _finite(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _dig(data: dict[str, Any], dotted: str) -> Any:
    """Read ``a.b`` out of nested dicts, returning None at the first gap."""
    node: Any = data
    for part in dotted.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def _agree(recomputed: Any, claimed: Any) -> bool:
    """True when the recomputed figure and the summary's claim are the same."""
    if recomputed is None or claimed is None:
        return recomputed is None and claimed is None
    if not _finite(recomputed) or not _finite(claimed):
        return False
    return abs(float(recomputed) - float(claimed)) <= TOL * max(1.0, abs(float(claimed)))


def _rmse(values: list[float]) -> float | None:
    return math.sqrt(statistics.fmean(v * v for v in values)) if values else None


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _parse_optional_float(text: Any) -> float | None:
    """Return the float in a CSV cell, or None for the collector's empty cell."""
    if text is None or str(text).strip() == "":
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _projected_displacement(actual_vx: float, actual_vy: float,
                            cmd_vx: float, cmd_vy: float,
                            step_dt: float) -> float | None:
    """One step of command-aligned body-frame displacement, as the collector."""
    norm = math.hypot(cmd_vx, cmd_vy)
    if norm <= 1.0e-9:
        return None
    return ((actual_vx * cmd_vx + actual_vy * cmd_vy) / norm) * step_dt


def _fell(samples: list[tuple[float, bool | None]], step_dt: float,
          hold_s: float, grace_s: float, mode: str) -> bool:
    """Replay one env's continuous non-upright timer under one reading of gaps.

    ``strict`` leaves the timer untouched across an unobserved row, exactly as
    the collector does; ``optimistic`` reads the gap as upright and
    ``pessimistic`` as fallen, which is how the collector decides whether the
    gaps could have changed the verdict.
    """
    run = 0.0
    for sim_time, flag in samples:
        if sim_time < grace_s:
            continue
        if flag is None:
            if mode == "strict":
                continue
            value = mode == "optimistic"
        else:
            value = flag
        if value:
            run = 0.0
            continue
        run += step_dt
        if run >= hold_s:
            return True
    return False


def _recovery_rate_upright(speeds: dict[int, list[tuple[float, float]]],
                           uprights: dict[int, list[tuple[float, bool]]],
                           step_dt: float) -> float | None:
    """Recompute go2_eval_telemetry.py's ``recovery_rate_upright`` from raw rows."""
    upright_recoveries = 0
    expected = 0
    quiet_steps = max(1, round(RECOVERY_WINDOW_S / step_dt))
    for env_id, samples in speeds.items():
        upright_samples = uprights.get(env_id, [])
        max_time = samples[-1][0] if samples else 0.0
        for push_time in RECOVERY_PUSH_TIMES:
            if push_time + 1.0 > max_time:
                continue
            expected += 1
            candidates = [
                (index, stamp, speed)
                for index, (stamp, speed) in enumerate(samples)
                if push_time <= stamp <= push_time + 1.0
            ]
            if not candidates:
                continue
            peak_index = max(candidates, key=lambda item: item[2])[0]
            for index in range(peak_index, len(samples) - quiet_steps + 1):
                window = samples[index:index + quiet_steps]
                if not all(speed <= RECOVERY_QUIET_SPEED for _, speed in window):
                    continue
                upright_window = upright_samples[index:index + quiet_steps]
                if upright_window and all(flag for _, flag in upright_window):
                    upright_recoveries += 1
                    break
    return upright_recoveries / expected if expected else None


def read_raw(path: Path, gate: dict[str, Any], step_dt: float,
             num_envs: Any) -> dict[str, Any]:
    """Re-derive from ``steps.csv`` every figure the summary claims.

    Returns the structural findings and, when the rows are structurally sound
    enough to replay, the recomputed figures.  Nothing is estimated: a channel
    the raw data does not carry comes back as None, never as a filled-in value.
    """
    faults: list[str] = []
    result: dict[str, Any] = {"faults": faults}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        raw_rows = list(reader)

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in header]
    result["missing_columns"] = missing_columns
    result["rows"] = len(raw_rows)
    if missing_columns:
        faults.append("csv_missing_columns:" + ",".join(missing_columns))
        return result

    tilt_cos = gate.get("tilt_cos_max")
    height_min = gate.get("height_rel_min_m")
    hold_s = gate.get("hold_s")
    grace_s = gate.get("grace_s")

    seen: dict[tuple[int, int], int] = {}
    steps_seen: set[int] = set()
    envs_seen: set[int] = set()
    bad_types: list[str] = []
    bad_upright: list[str] = []
    bad_terminated: list[str] = []
    nonfinite_rows = 0
    nonfinite_envs: set[int] = set()
    nonfinite_columns: dict[str, int] = {}
    first_bad: dict[str, Any] | None = None
    posture_mismatch: list[str] = []
    derived_mismatch: list[str] = []
    bad_time: list[str] = []
    time_mismatch: list[str] = []
    out_of_order: list[str] = []
    bad_posture_types: list[str] = []
    height_mismatch: list[str] = []
    last_step_by_env: dict[int, int] = {}
    dt_ok = _finite(step_dt) and float(step_dt) > 0.0

    per_env: dict[int, list[dict[str, Any]]] = {}
    rows_by_env: dict[int, int] = {}
    measured_by_env: dict[int, int] = {}
    xy_errors: list[float] = []
    yaw_errors: list[float] = []
    post_push_xy: list[float] = []
    speeds_flat: list[float] = []
    speed_samples: dict[int, list[tuple[float, float]]] = {}
    upright_samples: dict[int, list[tuple[float, bool]]] = {}
    upright_timeline: dict[int, list[tuple[float, bool | None]]] = {}
    terminated_envs: set[int] = set()

    for index, row in enumerate(raw_rows):
        try:
            step = int(str(row["step"]).strip())
            env_id = int(str(row["env_id"]).strip())
        except (TypeError, ValueError):
            if len(bad_types) < 8:
                bad_types.append("row%d:step_or_env_not_integer" % index)
            continue
        steps_seen.add(step)
        envs_seen.add(env_id)
        seen[(step, env_id)] = seen.get((step, env_id), 0) + 1

        values: dict[str, float | None] = {}
        row_bad: list[str] = []
        for column in KINEMATIC_COLUMNS + DERIVED_COLUMNS + ("time_s",):
            try:
                values[column] = float(row[column])
            except (TypeError, ValueError):
                values[column] = None
                if len(bad_types) < 8:
                    bad_types.append("step%d/env%d:%s_not_a_number" % (step, env_id, column))
        # The nine inputs, counted here rather than read off the summary.
        for column in KINEMATIC_COLUMNS:
            value = values[column]
            if value is None or not math.isfinite(value):
                row_bad.append(column)
        if row_bad:
            nonfinite_rows += 1
            nonfinite_envs.add(env_id)
            for column in row_bad:
                nonfinite_columns[column] = nonfinite_columns.get(column, 0) + 1
            if first_bad is None:
                first_bad = {"step": step, "env_id": env_id, "columns": sorted(row_bad)}

        # --- the time axis -------------------------------------------------
        # The collector writes ``time_s`` as ``f"{step * step_dt:.6f}"``.  It was
        # read here but never checked against its own step index, and it is the
        # column the fall grace window and the post-push window are cut on: move
        # every stamp below the grace threshold and the fall disappears, while a
        # summary forged to match the shifted replay still agrees with it.
        stamp = values["time_s"]
        if stamp is None or not math.isfinite(stamp):
            if len(bad_time) < 8:
                bad_time.append("step%d/env%d=%r" % (step, env_id, row.get("time_s")))
            stamp = None
        elif dt_ok:
            want_stamp = canonical_stamp(step, step_dt)
            if stamp != want_stamp:
                if len(time_mismatch) < 8:
                    time_mismatch.append(
                        "step%d/env%d:time_s=%r step_dt_says=%r"
                        % (step, env_id, stamp, want_stamp))
        previous = last_step_by_env.get(env_id)
        if previous is not None and step <= previous and len(out_of_order) < 8:
            out_of_order.append("env%d:step%d_after_step%d" % (env_id, step, previous))
        last_step_by_env[env_id] = step

        upright_text = (row.get("upright") or "").strip()
        if upright_text not in UPRIGHT_DOMAIN:
            if len(bad_upright) < 8:
                bad_upright.append("step%d/env%d=%r" % (step, env_id, row.get("upright")))
            continue
        upright: bool | None = None if upright_text == "" else upright_text == "1"

        # Posture is not taken on the collector's word either: it is re-derived
        # from the two raw channels through this case's own gate thresholds.
        grav = _parse_optional_float(row.get("proj_grav_z"))
        height = _parse_optional_float(row.get("height_rel"))

        # height_rel is derived, so it is re-derived rather than believed: the
        # collector writes ``root_z - terrain_z`` and records an unusable
        # reading as an empty cell.  Checking upright against height_rel while
        # never checking height_rel against its own two inputs left the ground
        # channel unconstrained -- a terrain of 100 m under a robot standing at
        # 0.32 m still read as upright.
        texts = {name: (row.get(name) or "").strip()
                 for name in ("proj_grav_z", "terrain_z", "height_rel")}
        untyped = [name for name, text in texts.items()
                   if text and _parse_optional_float(text) is None]
        if untyped and len(bad_posture_types) < 8:
            bad_posture_types.append(
                "step%d/env%d:%s" % (step, env_id, ",".join(sorted(untyped))))
        ground = _parse_optional_float(texts["terrain_z"])
        root_z = values["root_z"]
        if ground is None or root_z is None or not math.isfinite(root_z - ground):
            # No ground reading, or one that cannot yield a finite height: the
            # collector stores None here, and so must the file.
            want_height: float | None = None
        else:
            want_height = root_z - ground
        if "height_rel" not in untyped and not _agree(want_height, height):
            if len(height_mismatch) < 8:
                height_mismatch.append(
                    "step%d/env%d:height_rel=%r root_z-terrain_z=%r"
                    % (step, env_id, height, want_height))

        measured = (grav is not None and math.isfinite(grav)
                    and height is not None and math.isfinite(height))
        if measured and _finite(tilt_cos) and _finite(height_min):
            derived_upright: bool | None = bool(
                grav <= -float(tilt_cos) and height >= float(height_min))
        else:
            derived_upright = None
        if derived_upright != upright and len(posture_mismatch) < 8:
            posture_mismatch.append(
                "step%d/env%d:upright=%r raw_says=%r" % (step, env_id, upright, derived_upright))

        # error_xy, error_yaw and speed_xy are functions of the nine inputs.
        if not row_bad:
            want_xy = math.hypot(values["cmd_vx"] - values["actual_vx"],
                                 values["cmd_vy"] - values["actual_vy"])
            want_yaw = abs(values["cmd_wz"] - values["actual_wz"])
            want_speed = math.hypot(values["actual_vx"], values["actual_vy"])
            for column, want in (("error_xy", want_xy), ("error_yaw", want_yaw),
                                 ("speed_xy", want_speed)):
                got = values[column]
                if not _agree(want, got) and len(derived_mismatch) < 8:
                    derived_mismatch.append(
                        "step%d/env%d:%s=%r raw_says=%r" % (step, env_id, column, got, want))

        terminated_text = str(row.get("terminated", "")).strip()
        if terminated_text not in TERMINATED_DOMAIN and len(bad_terminated) < 8:
            bad_terminated.append("step%d/env%d=%r" % (step, env_id, row.get("terminated")))

        rows_by_env[env_id] = rows_by_env.get(env_id, 0) + 1
        if upright is not None:
            measured_by_env[env_id] = measured_by_env.get(env_id, 0) + 1
        if values["error_xy"] is not None:
            xy_errors.append(values["error_xy"])
            if stamp is not None and stamp >= PUSH_WINDOW_START_S:
                post_push_xy.append(values["error_xy"])
        if values["error_yaw"] is not None:
            yaw_errors.append(values["error_yaw"])
        if values["speed_xy"] is not None:
            speeds_flat.append(values["speed_xy"])
            speed_samples.setdefault(env_id, []).append(
                (step, stamp or 0.0, values["speed_xy"]))
        upright_samples.setdefault(env_id, []).append((step, stamp or 0.0, bool(upright)))
        upright_timeline.setdefault(env_id, []).append((step, stamp or 0.0, upright))
        per_env.setdefault(env_id, []).append({
            "step": step,
            "cmd_vx": values["cmd_vx"], "cmd_vy": values["cmd_vy"],
            "actual_vx": values["actual_vx"], "actual_vy": values["actual_vy"],
            "terminated": terminated_text,
        })

    # Every replay below runs on the step index, not on the order the rows
    # happened to sit in the file, so a shuffled file cannot quietly become a
    # different run.  The order it arrived in is reported separately.
    for table in (speed_samples, upright_samples, upright_timeline):
        for env_id in list(table):
            table[env_id] = [item[1:] for item in sorted(table[env_id],
                                                         key=lambda item: item[0])]
    for env_id in list(per_env):
        per_env[env_id] = sorted(per_env[env_id], key=lambda item: item["step"])

    # --- the grid ----------------------------------------------------------
    duplicates = sorted(pair for pair, count in seen.items() if count > 1)
    if duplicates:
        faults.append("csv_duplicate_step_env:" + ",".join(
            "step%d/env%d" % pair for pair in duplicates[:8]))
    absent = sorted(
        (step, env_id) for step in steps_seen for env_id in envs_seen
        if (step, env_id) not in seen)
    if absent:
        faults.append("csv_missing_step_env:" + ",".join(
            "step%d/env%d" % pair for pair in absent[:8]))
    if steps_seen and steps_seen != set(range(1, max(steps_seen) + 1)):
        faults.append("csv_step_index_not_contiguous_from_1")
    if envs_seen and envs_seen != set(range(len(envs_seen))):
        faults.append("csv_env_ids_not_0_based_contiguous")
    if _finite(num_envs) and envs_seen and len(envs_seen) != int(num_envs):
        faults.append("csv_envs=%d vs metadata_num_envs=%r" % (len(envs_seen), num_envs))
    if bad_types:
        faults.append("csv_untyped_values:" + ";".join(bad_types))
    if bad_upright:
        faults.append("csv_upright_outside_domain:" + ";".join(bad_upright))
    if bad_terminated:
        faults.append("csv_terminated_outside_domain:" + ";".join(bad_terminated))
    if not dt_ok:
        faults.append("csv_step_dt_not_positive_finite=%r" % (step_dt,))
    if bad_time:
        faults.append("csv_time_s_not_a_finite_number:" + ";".join(bad_time))
    if time_mismatch:
        faults.append("csv_time_s_inconsistent_with_step:" + ";".join(time_mismatch))
    if out_of_order:
        faults.append("csv_rows_not_in_step_order:" + ";".join(out_of_order))
    if bad_posture_types:
        faults.append("csv_posture_column_untyped:" + ";".join(bad_posture_types))
    if height_mismatch:
        faults.append("csv_height_rel_contradicts_terrain_channels:"
                      + ";".join(height_mismatch))
    if posture_mismatch:
        faults.append("csv_upright_contradicts_posture_channels:" + ";".join(posture_mismatch))
    if derived_mismatch:
        faults.append("csv_derived_column_mismatch:" + ";".join(derived_mismatch))
    if nonfinite_rows:
        faults.append("csv_nonfinite_rows=%d first=%r" % (nonfinite_rows, first_bad))

    result.update({
        "env_count": len(envs_seen),
        "step_count": len(steps_seen),
        "nonfinite_row_count": nonfinite_rows,
        "nonfinite_env_count": len(nonfinite_envs),
        "nonfinite_by_column": nonfinite_columns,
        "first_nonfinite": first_bad,
        "duplicate_pairs": len(duplicates),
        "missing_pairs": len(absent),
    })

    # --- the figures, recomputed ------------------------------------------
    total_rows = sum(rows_by_env.values())
    measured_rows = sum(measured_by_env.values())
    coverage = measured_rows / total_rows if total_rows else 0.0
    env_coverages = [measured_by_env.get(env_id, 0) / count
                     for env_id, count in sorted(rows_by_env.items()) if count]
    min_env_coverage = min(env_coverages) if env_coverages else 0.0

    for env_id, rows in per_env.items():
        if any(row["terminated"] in TERMINATED_TRUE for row in rows):
            terminated_envs.add(env_id)

    # dt_ok, not merely finite: a step_dt of zero is a damaged measurement and
    # every window below is cut in units of it.
    replayable = dt_ok and _finite(hold_s) and _finite(grace_s)
    strict = {env_id for env_id, samples in upright_timeline.items()
              if _fell(samples, step_dt, hold_s, grace_s, "strict")} if replayable else set()
    optimistic = {env_id for env_id, samples in upright_timeline.items()
                  if _fell(samples, step_dt, hold_s, grace_s, "optimistic")} if replayable else set()
    pessimistic = {env_id for env_id, samples in upright_timeline.items()
                   if _fell(samples, step_dt, hold_s, grace_s, "pessimistic")} if replayable else set()
    fallen = strict | terminated_envs
    ambiguous = (optimistic | terminated_envs) != (pessimistic | terminated_envs)

    envs_total = int(num_envs) if _finite(num_envs) and int(num_envs) > 0 else None
    coverage_ok = (envs_total is not None and len(rows_by_env) == envs_total
                   and coverage >= MIN_COVERAGE and min_env_coverage >= MIN_COVERAGE)
    survival = (1.0 - len(fallen) / envs_total
                if envs_total is not None and replayable and not nonfinite_rows
                and measured_rows and coverage_ok and not ambiguous else None)
    survival_v1 = (1.0 - len(terminated_envs) / envs_total
                   if envs_total is not None else None)

    progress_by_env: dict[int, float] = {}
    if dt_ok:
        for env_id, rows in per_env.items():
            total = 0.0
            contributed = False
            dead = False
            for row in rows:
                if not dead and None not in (row["actual_vx"], row["actual_vy"],
                                             row["cmd_vx"], row["cmd_vy"]):
                    step_progress = _projected_displacement(
                        row["actual_vx"], row["actual_vy"],
                        row["cmd_vx"], row["cmd_vy"], float(step_dt))
                    if step_progress is not None:
                        total += step_progress
                        contributed = True
                if row["terminated"] in TERMINATED_TRUE:
                    dead = True
            if contributed:
                progress_by_env[env_id] = total

    result["recomputed"] = {
        "posture_coverage": coverage,
        "posture_min_env_coverage": min_env_coverage,
        "posture_fall_verdict_ambiguous": ambiguous,
        "survival_proxy": survival,
        "survival_proxy_v1": survival_v1,
        "terminated_env_count": len(terminated_envs),
        "tracking_xy_rmse": _rmse(xy_errors),
        "tracking_yaw_rmse": _rmse(yaw_errors),
        "post_push_tracking_xy_rmse": _rmse(post_push_xy),
        "speed_xy_mean": _mean(speeds_flat),
        "projected_progress_m": (
            max(0.0, statistics.median(progress_by_env.values()))
            if progress_by_env else None),
        "recovery.recovery_rate_upright": (
            _recovery_rate_upright(speed_samples, upright_samples, float(step_dt))
            if dt_ok else None),
    }
    return result


def parse_status(text: str) -> dict[str, str]:
    """Parse STATUS.txt as key=value lines.

    The runner writes ``grep -qx 'EVAL_RC=0'`` -- a whole-line match.  This tool
    used a substring search, under which ``EVAL_RC=01`` passed.
    """
    fields: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        fields[key.strip()] = value.strip()
    return fields


def load_json_object(path: Path, label: str, faults: list[str]) -> dict[str, Any]:
    """Read one JSON object, recording a fault instead of raising.

    Only the read, the parse and the shape are caught.  A file that is damaged
    or is not an object at all is a measurement fault of that one case, and the
    run has to name the case and carry on; an exception here would lose the
    report for every other case in the harvest.  Nothing about the contents is
    excused: every later check still runs against what was read.
    """
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        faults.append("%s_unreadable:%s" % (label, type(exc).__name__))
        return {}
    if not isinstance(loaded, dict):
        faults.append("%s_not_an_object:%s" % (label, type(loaded).__name__))
        return {}
    return loaded


def read_text_file(path: Path, label: str, faults: list[str]) -> str:
    """Read one text file, recording a fault instead of raising."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        faults.append("%s_unreadable:%s" % (label, type(exc).__name__))
        return ""


def verify_case(case_dir: Path, scenario: str, case_id: str, seed: int) -> dict[str, Any]:
    """Check one case directory against its own raw data.  Returns its faults."""
    faults: list[str] = []
    result: dict[str, Any] = {
        "scenario": scenario, "case_id": case_id, "seed": seed,
        "path": str(case_dir), "faults": faults,
    }
    for name in ("summary.json", "metadata.json", "steps.csv", "STATUS.txt"):
        if not (case_dir / name).is_file():
            faults.append("missing_" + name)
    if faults:
        return result

    summary = load_json_object(case_dir / "summary.json", "summary_json", faults)
    metadata = load_json_object(case_dir / "metadata.json", "metadata_json", faults)
    status = parse_status(read_text_file(case_dir / "STATUS.txt", "status_txt", faults))
    if faults:
        # The case's own evidence could not be read.  Every check below reads
        # these three, so going on would report their emptiness as findings
        # about the policy rather than as the damaged files they are.
        return result

    # --- the ruler ---------------------------------------------------------
    if summary.get("schema_version") != EXPECTED_SCHEMA:
        faults.append("schema_version=%r" % summary.get("schema_version"))
    if summary.get("measurement_contract") != EXPECTED_CONTRACT:
        faults.append("measurement_contract_mismatch")
    if summary.get("survival_proxy_source") != EXPECTED_SOURCE:
        faults.append("survival_source=%r" % summary.get("survival_proxy_source"))
    gate = summary.get("posture_gate") or {}
    if not isinstance(gate, dict):
        faults.append("posture_gate_not_an_object:%s" % type(gate).__name__)
        # The fault is recorded; the replay below reads its thresholds out of
        # this object, so it continues against an empty one rather than taking
        # the whole harvest down over one case's damaged summary.
        gate = {}
    elif {key: gate.get(key) for key in EXPECTED_GATE} != EXPECTED_GATE:
        faults.append("posture_gate=%r" % (gate,))
    if summary.get("completed") is not True:
        faults.append("case_not_completed")

    # --- STATUS.txt, parsed rather than searched ---------------------------
    if status.get("EVAL_RC") != "0":
        faults.append("eval_rc=%r" % status.get("EVAL_RC"))
    if status.get("STEPS") != str(summary.get("steps")):
        faults.append("status_steps=%r vs summary_steps=%r"
                      % (status.get("STEPS"), summary.get("steps")))
    if status.get("ROWS") != str(summary.get("rows")):
        faults.append("status_rows=%r vs summary_rows=%r"
                      % (status.get("ROWS"), summary.get("rows")))

    # --- the gates the collector claims to have passed ---------------------
    for field in ("posture_coverage", "posture_min_env_coverage"):
        value = summary.get(field)
        if not _finite(value) or value < MIN_COVERAGE:
            faults.append("%s=%r" % (field, value))
    if summary.get("posture_fall_verdict_ambiguous") is not False:
        faults.append("fall_verdict_ambiguous")
    if summary.get("nonfinite_row_count") != 0:
        faults.append("summary_nonfinite_row_count=%r" % summary.get("nonfinite_row_count"))

    # --- every figure this case's scoring path will read -------------------
    for field, (low, high) in sorted(scored_fields_for(case_id).items()):
        value = _dig(summary, field)
        if not _finite(value):
            faults.append("%s_not_finite:%r" % (field, value))
        elif value < low or (high is not None and value > high):
            faults.append("%s_out_of_range:%r" % (field, value))

    # --- the case is the case it claims to be ------------------------------
    if str(metadata.get("case_id")) != case_id:
        faults.append("metadata_case_id=%r" % metadata.get("case_id"))
    if str(metadata.get("scenario_id")) != scenario:
        faults.append("metadata_scenario_id=%r" % metadata.get("scenario_id"))
    if str(metadata.get("evaluation_seed")) != str(seed):
        faults.append("metadata_seed=%r" % metadata.get("evaluation_seed"))
    identity_file = case_dir / "case_identity.sha256"
    if not identity_file.is_file():
        faults.append("missing_case_identity.sha256")
        result["case_fingerprint"] = None
    else:
        fingerprint = identity_file.read_text(encoding="utf-8").strip()
        result["case_fingerprint"] = fingerprint
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            faults.append("case_identity_not_a_sha256:%r" % fingerprint)

    # --- metadata and summary must describe the same run -------------------
    num_envs = metadata.get("num_envs")
    if not _agree(metadata.get("step_dt"), summary.get("step_dt")):
        faults.append("metadata_step_dt=%r vs summary_step_dt=%r"
                      % (metadata.get("step_dt"), summary.get("step_dt")))
    if metadata.get("max_steps") != summary.get("steps"):
        faults.append("metadata_max_steps=%r vs summary_steps=%r"
                      % (metadata.get("max_steps"), summary.get("steps")))
    if _finite(num_envs) and _finite(summary.get("steps")):
        if summary.get("rows") != summary.get("steps") * num_envs:
            faults.append("summary_rows_not_steps_times_envs")

    # --- the raw data, read and replayed independently ---------------------
    step_dt = summary.get("step_dt")
    evidence = read_raw(case_dir / "steps.csv", gate,
                        float(step_dt) if _finite(step_dt) else float("nan"), num_envs)
    result["csv"] = evidence
    result["summary_rows"] = summary.get("rows")
    faults.extend(evidence["faults"])
    if evidence.get("missing_columns"):
        return result
    if evidence["rows"] != summary.get("rows"):
        faults.append("csv_rows=%d vs summary_rows=%r"
                      % (evidence["rows"], summary.get("rows")))
    if evidence["step_count"] != summary.get("steps"):
        faults.append("csv_steps=%d vs summary_steps=%r"
                      % (evidence["step_count"], summary.get("steps")))

    # The point of this tool: every scored figure is recomputed from the rows
    # and compared, so an in-range but forged number no longer passes.
    for field, value in sorted((evidence.get("recomputed") or {}).items()):
        claimed = _dig(summary, field)
        if field == "posture_fall_verdict_ambiguous":
            if bool(value) != bool(claimed):
                faults.append("recomputed_%s=%r vs claimed=%r" % (field, value, claimed))
            continue
        if not _agree(value, claimed):
            faults.append("recomputed_%s=%r vs claimed=%r" % (field, value, claimed))
    return result


def read_run_plan(runner: Path | None, registry: Path, evaluator: Path | None,
                  steps_override: int | None,
                  env_expectations: dict[str, str] | None = None) -> dict[str, Any]:
    """Read the approved run conditions out of the runner script and the files.

    Nothing here is a hard-coded guess: the two model hashes, the eval env count
    and the eval step count are the runner's own values, and the evaluator and
    registry hashes are computed from the files this tool was pointed at.
    """
    plan: dict[str, Any] = {
        "runner": str(runner) if runner else None,
        "models": {},
        # The env each arm was approved to run under.  It is not derived here,
        # because taking the expectation from the harvest's own identity would
        # be checking a claim against itself -- but it is not unknowable
        # either.  Both env.yaml files are members of the frozen upload
        # go2_a017_full_suite.zip, which is exactly what the runner copies to
        # _keep/policy/ and hashes, so the approved digest is fixed before any
        # harvest comes back and is passed in with --expect-env-sha.  Its
        # absence is still an unknown rather than a pass.
        "envs": dict(env_expectations or {}),
        "num_envs": None,
        "steps": None,
        "steps_source": None,
        "evaluator_sha256": None,
        "registry_sha256": None,
        "faults": [],
    }
    for label, digest in sorted(plan["envs"].items()):
        if not SHA256_RE.match(str(digest)):
            plan["faults"].append("expected_env_sha_not_sha256:%s=%r" % (label, digest))
    if registry.is_file():
        plan["registry_sha256"] = hashlib.sha256(registry.read_bytes()).hexdigest()
    else:
        plan["faults"].append("registry_file_absent")
    if evaluator and evaluator.is_file():
        plan["evaluator_sha256"] = hashlib.sha256(evaluator.read_bytes()).hexdigest()
    else:
        plan["faults"].append("evaluator_file_absent")

    if not runner or not runner.is_file():
        plan["faults"].append("runner_script_absent")
        return plan
    text = runner.read_text(encoding="utf-8", errors="replace")
    for label, variable in (("a017", "A017_EXPECTED_SHA"), ("pilot", "PILOT_EXPECTED_SHA")):
        match = re.search(r"^%s=([0-9a-f]{64})\s*$" % variable, text, re.M)
        if match:
            plan["models"][label] = match.group(1)
        else:
            plan["faults"].append("runner_missing_" + variable)
    # Scope the env-count read to the eval function: the runner also renders
    # video at a different env count, and picking that one up would compare the
    # harvest against a number no scored case was ever measured at.
    body = re.search(r"^run_eval_case\(\)\s*\{(.*?)^\}", text, re.M | re.S)
    if body:
        envs = re.search(r"--num_envs\s+(\d+)", body.group(1))
        if envs:
            plan["num_envs"] = int(envs.group(1))
        else:
            plan["faults"].append("runner_eval_num_envs_unreadable")
    else:
        plan["faults"].append("runner_eval_function_unreadable")
    if steps_override is not None:
        plan["steps"] = int(steps_override)
        plan["steps_source"] = "--expect-steps"
    else:
        steps = re.search(r"^EVAL_STEPS=\$\{GO2_EVAL_STEPS:-(\d+)\}", text, re.M)
        if steps:
            plan["steps"] = int(steps.group(1))
            plan["steps_source"] = "runner_default"
        else:
            plan["faults"].append("runner_eval_steps_unreadable")
    return plan


def plan_is_usable(plan: dict[str, Any], labels: list[str]) -> bool:
    """True when the plan can identify the instrument for every arm asked for.

    The evaluation environment is part of that identity.  Without an approved
    env digest for every arm the harvest can still be checked against itself,
    but it cannot be tied to the run that was approved, and the verdict for
    that is INCONCLUSIVE rather than a pass.
    """
    return (not plan["faults"]
            and plan["num_envs"] is not None
            and plan["steps"] is not None
            and plan["evaluator_sha256"] is not None
            and plan["registry_sha256"] is not None
            and all(label in plan["models"] for label in labels)
            and all(label in (plan.get("envs") or {}) for label in labels))


def verify_arm(root: Path, label: str, registry: dict[str, Any],
               plan: dict[str, Any] | None = None) -> dict[str, Any]:
    """Check one arm's whole 69-case harvest."""
    arm_dir = root / "evaluation" / label
    faults: list[str] = []
    arm: dict[str, Any] = {"label": label, "path": str(arm_dir), "faults": faults, "cases": []}
    if not arm_dir.is_dir():
        faults.append("arm_directory_absent")
        arm["expected_case_count"] = len(expected_cases(registry))
        arm["observed_case_count"] = 0
        arm["invalid_cases"] = []
        arm["measurement"] = "INTERNAL_MEASUREMENT_INCOMPLETE"
        return arm

    identity_path = arm_dir / "identity.json"
    if identity_path.is_file():
        arm["identity"] = load_json_object(identity_path, "identity_json", faults)
        for field in ARM_IDENTITY_REQUIRED:
            value = arm["identity"].get(field)
            if not value:
                faults.append("identity_missing_" + field)
            elif field in SHA256_IDENTITY_FIELDS and not SHA256_RE.match(str(value)):
                # The runner writes sha256sum output here.  Anything else is a
                # damaged identity, and saying so does not need an expectation.
                faults.append("identity_%s_not_sha256:%r" % (field, value))
    else:
        arm["identity"] = {}
        faults.append("identity_json_absent")

    # The arm's own hashes against the approved run plan.  Two arms agreeing
    # with each other only proves one instrument, not the right one.
    if plan:
        for field, expected in (("evaluator_sha256", plan.get("evaluator_sha256")),
                                ("registry_sha256", plan.get("registry_sha256")),
                                ("model_sha256", (plan.get("models") or {}).get(label)),
                                ("env_sha256", (plan.get("envs") or {}).get(label))):
            observed = arm["identity"].get(field)
            if expected and observed and observed != expected:
                faults.append("identity_%s=%s expected=%s" % (field, observed, expected))

    wanted = expected_cases(registry)
    found: set[tuple[str, str, int]] = set()
    scenario_of = {
        case_id: scenario["id"]
        for scenario in registry["scenarios"]
        for case_id in scenario["internal_cases"]
    }
    cases_root = arm_dir / "cases"
    seed_dirs = sorted(cases_root.glob("seed_*")) if cases_root.is_dir() else []
    for seed_dir in seed_dirs:
        try:
            seed = int(seed_dir.name.split("_", 1)[1])
        except (IndexError, ValueError):
            faults.append("unreadable_seed_dir:" + seed_dir.name)
            continue
        for case_dir in sorted(p for p in seed_dir.iterdir() if p.is_dir()):
            case_id = case_dir.name
            scenario = scenario_of.get(case_id)
            if scenario is None:
                faults.append("case_not_in_registry:" + case_id)
                continue
            found.add((scenario, case_id, seed))
            arm["cases"].append(verify_case(case_dir, scenario, case_id, seed))

    missing = sorted(wanted - found)
    extra = sorted(found - wanted)
    if missing:
        faults.append("missing_cases:" + ",".join("%s/%s@%d" % item for item in missing))
    if extra:
        faults.append("unexpected_cases:" + ",".join("%s/%s@%d" % item for item in extra))

    # Two cases with one fingerprint means one case was copied over the other.
    fingerprints: dict[str, list[str]] = {}
    for case in arm["cases"]:
        value = case.get("case_fingerprint")
        if value:
            fingerprints.setdefault(value, []).append(
                "%s/%s@%d" % (case["scenario"], case["case_id"], case["seed"]))
    for value, owners in sorted(fingerprints.items()):
        if len(owners) > 1:
            faults.append("case_identity_shared_by:" + ",".join(sorted(owners)))

    # The run plan's env and step counts, against what the cases were measured at.
    if plan and plan.get("num_envs") is not None and plan.get("steps") is not None:
        for case in arm["cases"]:
            metadata_path = Path(case["path"]) / "metadata.json"
            if not metadata_path.is_file():
                continue
            # verify_case has already faulted an unreadable metadata file and
            # named the case; re-reading it here must add nothing and, above
            # all, must not raise out of the whole harvest.
            metadata = load_json_object(metadata_path, "metadata_json", [])
            if metadata.get("num_envs") != plan["num_envs"]:
                case["faults"].append("num_envs=%r expected=%r"
                                      % (metadata.get("num_envs"), plan["num_envs"]))
            if metadata.get("max_steps") != plan["steps"]:
                case["faults"].append("max_steps=%r expected=%r"
                                      % (metadata.get("max_steps"), plan["steps"]))

    arm["expected_case_count"] = len(wanted)
    arm["observed_case_count"] = len(found)
    arm["invalid_cases"] = [
        "%s/%s@%d" % (case["scenario"], case["case_id"], case["seed"])
        for case in arm["cases"] if case["faults"]
    ]
    # Named, not dropped.  An arm with one invalid case is an incomplete
    # measurement of 69, not a complete measurement of 68.
    arm["measurement"] = (
        "INTERNAL_MEASUREMENT_OK"
        if not faults and not arm["invalid_cases"]
        else "INTERNAL_MEASUREMENT_INCOMPLETE"
    )
    return arm


def _case_rulers(arm: dict[str, Any]) -> set[str]:
    """Return the distinct instrument fingerprints found across an arm's cases."""
    keys: set[str] = set()
    for case in arm["cases"]:
        path = Path(case["path"]) / "summary.json"
        if not path.is_file():
            continue
        # A case whose evidence cannot be read has already been faulted by
        # verify_case and named in the arm's invalid list.  It contributes no
        # fingerprint here: an unreadable file is not a second instrument, and
        # reading it again must not be what ends the run.
        unreadable: list[str] = []
        summary = load_json_object(path, "summary_json", unreadable)
        if unreadable:
            continue
        ruler = {k: summary.get(k) for k in CASE_IDENTITY_FIELDS}
        # num_envs lives in metadata, and a case measured over a different
        # number of envs carries a survival denominator of its own.
        metadata_path = Path(case["path"]) / "metadata.json"
        if metadata_path.is_file():
            metadata = load_json_object(metadata_path, "metadata_json", unreadable)
            if unreadable:
                continue
            ruler["num_envs"] = metadata.get("num_envs")
        keys.add(json.dumps(ruler, sort_keys=True))
    return keys


def compare_arms(arms: list[dict[str, Any]]) -> list[str]:
    """Return every way the arms were not measured with the same instrument."""
    if len(arms) < 2:
        return ["only_one_arm_present"]
    mismatches: list[str] = []
    for field in ARM_IDENTITY_FIELDS:
        values = {arm.get("identity", {}).get(field) for arm in arms}
        if len(values) != 1:
            mismatches.append("%s_differs:%s" % (field, sorted(str(v) for v in values)))

    # The case-level ruler has to match case for case, not just arm for arm.
    rulers = [_case_rulers(arm) for arm in arms]
    for arm, keys in zip(arms, rulers):
        if len(keys) > 1:
            mismatches.append("%s_mixed_rulers_within_arm:%d" % (arm["label"], len(keys)))
    if rulers[0] and any(keys and keys != rulers[0] for keys in rulers[1:]):
        mismatches.append("arm_rulers_differ")

    ids = [{(c["scenario"], c["case_id"], c["seed"]) for c in arm["cases"]} for arm in arms]
    if any(other != ids[0] for other in ids[1:]):
        mismatches.append("arms_measured_different_case_sets")
    return mismatches


def main() -> int:
    here = Path("workspace/training/quadruped")
    parser = argparse.ArgumentParser(description="verify a recovered G-A027 harvest")
    parser.add_argument("--harvest", required=True, type=Path,
                        help="the recovered _keep/go2_a017_full_suite directory")
    parser.add_argument("--registry", type=Path,
                        default=here / "config" / "go2_self_eval_registry.json")
    parser.add_argument("--runner", type=Path,
                        default=here / "server_run_go2_a017_full_suite.sh",
                        help="the runner script the approved run conditions are read from")
    parser.add_argument("--evaluator", type=Path, default=here / "go2_eval_telemetry.py")
    parser.add_argument("--expect-steps", type=int, default=None,
                        help="the EVAL_STEPS actually used, if it was not the runner default")
    parser.add_argument("--expect-env-sha", action="append", default=[],
                        metavar="LABEL=SHA256",
                        help="the approved env.yaml digest for one arm; without one "
                             "per arm the verdict cannot rise above INCONCLUSIVE")
    parser.add_argument("--arms", default="a017,pilot")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    labels = args.arms.split(",")
    envs: dict[str, str] = {}
    for item in args.expect_env_sha:
        label, _, digest = str(item).partition("=")
        envs[label.strip()] = digest.strip()
    plan = read_run_plan(args.runner, args.registry, args.evaluator, args.expect_steps,
                         envs)
    usable = plan_is_usable(plan, labels)
    arms = [verify_arm(args.harvest, label, registry, plan if usable else None)
            for label in labels]
    mismatches = compare_arms(arms)

    clean = all(arm["measurement"] == "INTERNAL_MEASUREMENT_OK" for arm in arms) and not mismatches
    if not clean:
        verdict = "INTERNAL_GATE_FAIL"
    elif usable:
        verdict = "INTERNAL_GATE_PASS"
    else:
        # Internally consistent, but nothing tied it to the approved run.  That
        # is not a pass, and it is not a failure of the harvest either.
        verdict = "INTERNAL_GATE_INCONCLUSIVE"
    report = {
        "schema_version": 2,
        "harvest": str(args.harvest),
        "registry": str(args.registry),
        "expected_engine": {"schema_version": EXPECTED_SCHEMA,
                            "measurement_contract": EXPECTED_CONTRACT},
        "run_plan": plan,
        "run_plan_usable": usable,
        "arms": arms,
        "instrument_mismatches": mismatches,
        # This tool verifies that the measurement is admissible.  Whether the
        # policy is any good is a separate question, and whether it passes the
        # official evaluator is a third one this tool cannot answer at all.
        "verdict": verdict,
        "official_result": "OFFICIAL_RESULT_UNMEASURED",
    }
    if args.out:
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for arm in arms:
        print("[%s] %s %d/%d cases" % (arm["label"], arm["measurement"],
                                       arm["observed_case_count"],
                                       arm["expected_case_count"]))
        for fault in arm["faults"]:
            print("  arm fault: " + fault)
        for case in arm["cases"]:
            if case["faults"]:
                print("  %s/%s@%d: %s" % (case["scenario"], case["case_id"],
                                          case["seed"], "; ".join(case["faults"])))
    for mismatch in mismatches:
        print("[instrument] " + mismatch)
    if not usable:
        missing = [label for label in labels if label not in (plan.get("envs") or {})]
        detail = list(plan["faults"])
        if missing:
            detail.append("no approved env digest for " + ",".join(missing)
                          + " (pass --expect-env-sha LABEL=SHA256)")
        print("[run plan] not readable: " + ", ".join(detail or ["incomplete"]))

    print("\nverdict: " + verdict)
    if verdict == "INTERNAL_GATE_FAIL":
        print("invalid cases are named above; do not drop them to complete the score")
    if verdict == "INTERNAL_GATE_INCONCLUSIVE":
        print("the harvest is self-consistent but was not matched to an approved run plan")
    return 0 if verdict == "INTERNAL_GATE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
