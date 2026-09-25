#!/usr/bin/env python3
"""Re-read the G-A038 (ang_vel_xy_l2 -0.08) harvest against G-A033 from raw artifacts.

Answers, from files only, four questions the 2026-09-19 PM re-open asked:

  1. stairs_10_down: terminations down, posture falls up to 32/32, projected
     progress down ~30%.  What do the per-env step rows say the bodies are
     actually doing?
  2. rough_lateral: is the improvement separable from the curriculum
     (terrain level at the pinned iteration) confound?
  3. rough_forward is MISSING in the A038 harvest.  What does it score in A033
     and could it own the G3 minimum?
  4. What would each scoring variant (v1 / v2 / with-completion) make of the
     two arms on the measured cases?

Nothing here is a forecast.  Every number is either read out of a summary.json /
steps.csv / tfevents-derived ledger CSV, or computed from those rows by this
file.  Outputs land in
``workspace/training/quadruped/reports/evidence/go2_a038_reread_20260919/``.

Usage:
    PYTHONIOENCODING=utf-8 python -B tools/go2_a038_reread.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
KEEP = REPO / "workspace" / "_keep"
QUAD = REPO / "workspace" / "training" / "quadruped"
OUT = QUAD / "reports" / "evidence" / "go2_a038_reread_20260919"

ARMS = {
    "A033": KEEP / "go2_g_a033_a017_track_lin_vel_xy_150",
    "A038": KEEP / "go2_g_a038_a033_ang_vel_xy_m008",
}
SEEDS = (101, 202, 303)

# Cases the A038 harvest actually contains, plus the G3 partner that it does not.
FOCUS_CASES = ("forward_nominal", "rough_lateral", "stairs_10_down", "push_pos_x")
G3_CASES = ("rough_forward", "rough_lateral")

SUMMARY_FIELDS = [
    "survival_proxy",
    "survival_proxy_v1",
    "survival_proxy_v2",
    "survival_proxy_source",
    "tracking_xy_rmse",
    "tracking_yaw_rmse",
    "post_push_tracking_xy_rmse",
    "projected_progress_m",
    "terminated_env_count",
    "fallen_env_count",
    "posture_fall_env_count_optimistic",
    "posture_fall_env_count_pessimistic",
    "posture_measured",
    "posture_coverage",
    "height_rel_mean",
    "height_rel_median",
    "height_rel_p10",
    "speed_xy_mean",
    "steps",
    "step_dt",
    "rows",
    "schema_version",
    "measurement_contract",
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _track(rmse: float | None, std: float) -> float | None:
    """Mirror of go2_fixed_eval_report.py:24-25."""
    return None if rmse is None else math.exp(-((float(rmse) / float(std)) ** 2))


def case_dir(arm: str, seed: int, case: str) -> Path:
    return ARMS[arm] / "evaluation" / "candidate" / "cases" / f"seed_{seed}" / case


# ---------------------------------------------------------------- summaries


def collect_summaries(std: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cases = sorted(set(FOCUS_CASES) | set(G3_CASES))
    for arm in ("A033", "A038"):
        for seed in SEEDS:
            for case in cases:
                path = case_dir(arm, seed, case) / "summary.json"
                row: dict[str, Any] = {
                    "arm": arm,
                    "seed": seed,
                    "case": case,
                    "summary_present": path.is_file(),
                    "summary_path": str(path.relative_to(REPO)).replace("\\", "/"),
                }
                if not path.is_file():
                    rows.append(row)
                    continue
                s = _load(path)
                for field in SUMMARY_FIELDS:
                    row[field] = s.get(field)
                rec = s.get("recovery") or {}
                row["recovery_rate"] = rec.get("recovery_rate")
                row["recovery_rate_upright"] = rec.get("recovery_rate_upright")
                row["posture_gate_height_rel_min_m"] = (s.get("posture_gate") or {}).get(
                    "height_rel_min_m"
                )
                row["posture_gate_tilt_cos_max"] = (s.get("posture_gate") or {}).get(
                    "tilt_cos_max"
                )

                # Score reconstruction (go2_fixed_eval_report.py:28-68).
                xy = _track(s.get("tracking_xy_rmse"), std)
                yaw = _track(s.get("tracking_yaw_rmse"), std)
                tracking = xy
                completion = None
                if case.startswith("combined_yaw"):
                    tracking = min(xy, yaw) if xy is not None and yaw is not None else None
                if case.startswith("stairs_"):
                    duration = float(s.get("steps", 0)) * float(s.get("step_dt", 0.02))
                    expected = 0.5 * duration
                    completion = (
                        min(1.0, float(s.get("projected_progress_m") or 0.0) / expected)
                        if expected
                        else None
                    )
                    tracking = (
                        min(tracking, completion)
                        if tracking is not None and completion is not None
                        else None
                    )
                if case.startswith("push_"):
                    tracking = _track(s.get("post_push_tracking_xy_rmse"), std)
                    up = rec.get("recovery_rate_upright")
                    if up is None:
                        up = rec.get("recovery_rate")
                    tracking = min(tracking, up) if tracking is not None and up is not None else None
                row["tracking_xy_proxy"] = xy
                row["tracking_yaw_proxy"] = yaw
                row["obstacle_completion"] = completion
                row["tracking_proxy_engine"] = tracking
                for tag, surv in (
                    ("v1", s.get("survival_proxy_v1")),
                    ("v2", s.get("survival_proxy_v2")),
                    ("engine", s.get("survival_proxy")),
                ):
                    row[f"scenario_proxy_{tag}"] = (
                        surv * tracking if surv is not None and tracking is not None else None
                    )
                # Official formula (PRELIM_RL_GUID.md:95-100) has no completion factor.
                official_track = xy
                if case.startswith("push_"):
                    official_track = _track(s.get("post_push_tracking_xy_rmse"), std)
                row["tracking_proxy_official_shape"] = official_track
                for tag, surv in (("v1", s.get("survival_proxy_v1")), ("v2", s.get("survival_proxy_v2"))):
                    row[f"scenario_proxy_official_shape_{tag}"] = (
                        surv * official_track
                        if surv is not None and official_track is not None
                        else None
                    )
                rows.append(row)
    return rows


# ------------------------------------------------------------- per-env steps


def per_env_stairs(case: str = "stairs_10_down") -> list[dict[str, Any]]:
    """Read steps.csv per env for both arms and describe the terminal posture.

    Columns available (header of steps.csv): step,time_s,env_id,cmd_vx,cmd_vy,
    cmd_wz,actual_vx,actual_vy,actual_wz,error_xy,error_yaw,speed_xy,root_x,
    root_y,root_z,proj_grav_z,terrain_z,height_rel,upright,terminated,truncated,
    term_time_out,term_base_contact
    """
    rows: list[dict[str, Any]] = []
    for arm in ("A033", "A038"):
        for seed in SEEDS:
            path = case_dir(arm, seed, case) / "steps.csv"
            if not path.is_file():
                continue
            envs: dict[int, dict[str, Any]] = {}
            with path.open("r", encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    env = int(r["env_id"])
                    e = envs.setdefault(
                        env,
                        {
                            "n": 0,
                            "upright_n": 0,
                            "hr_sum": 0.0,
                            "hr_min": None,
                            "pg_sum": 0.0,
                            "pg_min": None,
                            "speed_sum": 0.0,
                            "terminated_any": 0,
                            "base_contact_any": 0,
                            "first_hr_below_gate_step": None,
                            "last": None,
                            "first": None,
                            "hr_last200": [],
                            "pg_last200": [],
                            "speed_last200": [],
                        },
                    )
                    step = int(r["step"])
                    hr = float(r["height_rel"])
                    pg = float(r["proj_grav_z"])
                    sp = float(r["speed_xy"])
                    e["n"] += 1
                    e["upright_n"] += int(float(r["upright"]) > 0.5)
                    e["hr_sum"] += hr
                    e["pg_sum"] += pg
                    e["speed_sum"] += sp
                    e["hr_min"] = hr if e["hr_min"] is None else min(e["hr_min"], hr)
                    e["pg_min"] = pg if e["pg_min"] is None else min(e["pg_min"], pg)
                    if float(r["terminated"]) > 0.5:
                        e["terminated_any"] = 1
                    if float(r.get("term_base_contact") or 0) > 0.5:
                        e["base_contact_any"] = 1
                    if hr < 0.18 and e["first_hr_below_gate_step"] is None:
                        e["first_hr_below_gate_step"] = step
                    if e["first"] is None:
                        e["first"] = r
                    e["last"] = r
                    if step >= 800:
                        e["hr_last200"].append(hr)
                        e["pg_last200"].append(pg)
                        e["speed_last200"].append(sp)
            for env, e in sorted(envs.items()):
                first, last = e["first"], e["last"]
                dx = float(last["root_x"]) - float(first["root_x"])
                dy = float(last["root_y"]) - float(first["root_y"])
                dz_terrain = float(last["terrain_z"]) - float(first["terrain_z"])
                rows.append(
                    {
                        "arm": arm,
                        "seed": seed,
                        "case": case,
                        "env_id": env,
                        "rows": e["n"],
                        "upright_frac": e["upright_n"] / e["n"],
                        "height_rel_mean": e["hr_sum"] / e["n"],
                        "height_rel_min": e["hr_min"],
                        "height_rel_mean_last200": (
                            sum(e["hr_last200"]) / len(e["hr_last200"]) if e["hr_last200"] else None
                        ),
                        "proj_grav_z_mean": e["pg_sum"] / e["n"],
                        "proj_grav_z_min": e["pg_min"],
                        "proj_grav_z_mean_last200": (
                            sum(e["pg_last200"]) / len(e["pg_last200"]) if e["pg_last200"] else None
                        ),
                        "speed_xy_mean": e["speed_sum"] / e["n"],
                        "speed_xy_mean_last200": (
                            sum(e["speed_last200"]) / len(e["speed_last200"])
                            if e["speed_last200"]
                            else None
                        ),
                        "first_height_rel_below_0p18_step": e["first_hr_below_gate_step"],
                        "terminated_any": e["terminated_any"],
                        "term_base_contact_any": e["base_contact_any"],
                        "net_dx_m": dx,
                        "net_dy_m": dy,
                        "net_dxy_m": math.hypot(dx, dy),
                        "terrain_z_first": float(first["terrain_z"]),
                        "terrain_z_last": float(last["terrain_z"]),
                        "terrain_z_climb_m": dz_terrain,
                        "root_z_first": float(first["root_z"]),
                        "root_z_last": float(last["root_z"]),
                    }
                )
    return rows


def fall_channel_attribution(case: str) -> list[dict[str, Any]]:
    """Which posture channel actually fired the fall verdict, per env.

    go2_eval_telemetry.py:295-330 -- upright = (proj_grav_z <= -0.5) AND
    (height_rel >= 0.18); a fall is declared when non-upright holds continuously
    for FALL_HOLD_S = 0.5 s (25 steps at dt 0.02) after FALL_GRACE_S = 0.5 s.
    This replays the same timers per channel so the two can be separated.
    """
    grace_s, hold_s = 0.5, 0.5
    tilt_cos, height_min = 0.5, 0.18
    rows: list[dict[str, Any]] = []
    for arm in ("A033", "A038"):
        for seed in SEEDS:
            path = case_dir(arm, seed, case) / "steps.csv"
            if not path.is_file():
                continue
            st: dict[int, dict[str, Any]] = {}
            with path.open("r", encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    env = int(r["env_id"])
                    t = float(r["time_s"])
                    dt = 0.02
                    e = st.setdefault(
                        env,
                        {
                            "run_tilt": 0.0,
                            "run_height": 0.0,
                            "run_both": 0.0,
                            "fall_tilt": 0,
                            "fall_height": 0,
                            "fall_any": 0,
                            "max_run_tilt": 0.0,
                            "max_run_height": 0.0,
                            "terrain_z_min": None,
                            "terrain_z_max": None,
                        },
                    )
                    tz = float(r["terrain_z"])
                    e["terrain_z_min"] = tz if e["terrain_z_min"] is None else min(e["terrain_z_min"], tz)
                    e["terrain_z_max"] = tz if e["terrain_z_max"] is None else max(e["terrain_z_max"], tz)
                    if t < grace_s:
                        continue
                    tilt_bad = not (float(r["proj_grav_z"]) <= -tilt_cos)
                    height_bad = not (float(r["height_rel"]) >= height_min)
                    for tag, bad in (("tilt", tilt_bad), ("height", height_bad)):
                        if bad:
                            e[f"run_{tag}"] += dt
                            e[f"max_run_{tag}"] = max(e[f"max_run_{tag}"], e[f"run_{tag}"])
                            if e[f"run_{tag}"] >= hold_s:
                                e[f"fall_{tag}"] = 1
                        else:
                            e[f"run_{tag}"] = 0.0
                    if tilt_bad or height_bad:
                        e["run_both"] += dt
                        if e["run_both"] >= hold_s:
                            e["fall_any"] = 1
                    else:
                        e["run_both"] = 0.0
            for env, e in sorted(st.items()):
                rows.append(
                    {
                        "arm": arm,
                        "seed": seed,
                        "case": case,
                        "env_id": env,
                        "fall_by_height_channel": e["fall_height"],
                        "fall_by_tilt_channel": e["fall_tilt"],
                        "fall_by_either": e["fall_any"],
                        "max_continuous_low_height_s": round(e["max_run_height"], 3),
                        "max_continuous_tilted_s": round(e["max_run_tilt"], 3),
                        "terrain_z_min": e["terrain_z_min"],
                        "terrain_z_max": e["terrain_z_max"],
                        "terrain_z_span_m": e["terrain_z_max"] - e["terrain_z_min"],
                    }
                )
    return rows


def channel_rollup(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for arm, seed, case in sorted({(r["arm"], r["seed"], r["case"]) for r in rows}):
        sel = [r for r in rows if (r["arm"], r["seed"], r["case"]) == (arm, seed, case)]
        out.append(
            {
                "arm": arm,
                "seed": seed,
                "case": case,
                "n_envs": len(sel),
                "envs_fall_height_only": sum(
                    1 for r in sel if r["fall_by_height_channel"] and not r["fall_by_tilt_channel"]
                ),
                "envs_fall_tilt_only": sum(
                    1 for r in sel if r["fall_by_tilt_channel"] and not r["fall_by_height_channel"]
                ),
                "envs_fall_both_channels": sum(
                    1 for r in sel if r["fall_by_tilt_channel"] and r["fall_by_height_channel"]
                ),
                "envs_fall_either": sum(1 for r in sel if r["fall_by_either"]),
                "max_terrain_z_span_m": max(r["terrain_z_span_m"] for r in sel),
                "mean_terrain_z_span_m": sum(r["terrain_z_span_m"] for r in sel) / len(sel),
            }
        )
    return out


def per_env_rollup(env_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    keys = sorted({(r["arm"], r["seed"], r["case"]) for r in env_rows})
    for arm, seed, case in keys:
        sel = [r for r in env_rows if (r["arm"], r["seed"], r["case"]) == (arm, seed, case)]
        n = len(sel)

        def mean(field: str) -> float:
            vals = [r[field] for r in sel if r[field] is not None]
            return sum(vals) / len(vals) if vals else float("nan")

        out.append(
            {
                "arm": arm,
                "seed": seed,
                "case": case,
                "n_envs": n,
                "envs_terminated": sum(r["terminated_any"] for r in sel),
                "envs_base_contact": sum(r["term_base_contact_any"] for r in sel),
                "envs_upright_frac_ge_0p9": sum(1 for r in sel if r["upright_frac"] >= 0.9),
                "envs_hr_last200_below_gate": sum(
                    1
                    for r in sel
                    if r["height_rel_mean_last200"] is not None
                    and r["height_rel_mean_last200"] < 0.18
                ),
                "envs_tilted_last200_pgz_gt_m0p5": sum(
                    1
                    for r in sel
                    if r["proj_grav_z_mean_last200"] is not None
                    and r["proj_grav_z_mean_last200"] > -0.5
                ),
                "envs_climbed_ge_0p05m": sum(1 for r in sel if r["terrain_z_climb_m"] >= 0.05),
                "mean_upright_frac": mean("upright_frac"),
                "mean_height_rel": mean("height_rel_mean"),
                "mean_height_rel_last200": mean("height_rel_mean_last200"),
                "mean_proj_grav_z": mean("proj_grav_z_mean"),
                "mean_proj_grav_z_last200": mean("proj_grav_z_mean_last200"),
                "mean_speed_xy": mean("speed_xy_mean"),
                "mean_speed_xy_last200": mean("speed_xy_mean_last200"),
                "mean_net_dxy_m": mean("net_dxy_m"),
                "mean_terrain_z_climb_m": mean("terrain_z_climb_m"),
                "mean_first_below_gate_step": mean("first_height_rel_below_0p18_step"),
            }
        )
    return out


# ------------------------------------------------------------------- output


def axis_reconstruction(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rebuild the G3 / G5-stairs_10_down figures under each scoring variant.

    go2_fixed_eval_report.py:102-141 -- an axis score is the MINIMUM over all
    (case, seed) pairs of survival*tracking, and an axis with any missing pair is
    dropped from the weighted sum entirely (line 106-107 ``continue``).
    Variants:
      engine     survival_proxy (= v2) x tracking, stairs tracking capped by completion
      v1         survival_proxy_v1     x the same tracking
      official   survival x tracking_xy only, no completion factor (PRELIM_RL_GUID.md:95-100)
    """
    out: list[dict[str, Any]] = []
    specs = [
        ("G3", 0.20, ("rough_forward", "rough_lateral")),
        ("G3_measured_only", 0.20, ("rough_lateral",)),
        ("G5_stairs_10_down_only", 0.15, ("stairs_10_down",)),
    ]
    for arm in ("A033", "A038"):
        for axis, weight, cases in specs:
            for variant, surv_key, use_completion in (
                ("engine_v2", "scenario_proxy_engine", True),
                ("v1", "scenario_proxy_v1", True),
                ("official_shape_v1", "scenario_proxy_official_shape_v1", False),
                ("official_shape_v2", "scenario_proxy_official_shape_v2", False),
            ):
                pairs = [
                    r
                    for r in summaries
                    if r["arm"] == arm and r["case"] in cases and r["summary_present"]
                ]
                required = len(cases) * len(SEEDS)
                vals = [
                    float(r[surv_key])
                    for r in pairs
                    if r.get(surv_key) not in (None, "")
                ]
                complete = len(vals) == required
                worst = min(vals) if vals else None
                worst_row = None
                if vals:
                    worst_row = min(
                        (r for r in pairs if r.get(surv_key) not in (None, "")),
                        key=lambda r: float(r[surv_key]),
                    )
                out.append(
                    {
                        "arm": arm,
                        "axis": axis,
                        "weight": weight,
                        "variant": variant,
                        "uses_completion_factor": use_completion,
                        "pairs_required": required,
                        "pairs_present": len(vals),
                        "axis_scorable": complete,
                        "axis_proxy_min": worst,
                        "worst_case": None if worst_row is None else worst_row["case"],
                        "worst_seed": None if worst_row is None else worst_row["seed"],
                        "axis_points_of_70": None if worst is None else weight * worst * 70.0,
                        "axis_points_counted_by_engine": (
                            weight * worst * 70.0 if complete and worst is not None else 0.0
                        ),
                    }
                )
    # Paired deltas, so no figure in the readout is computed by hand.
    deltas: list[dict[str, Any]] = []
    for r38 in [r for r in out if r["arm"] == "A038"]:
        match = [
            r
            for r in out
            if r["arm"] == "A033" and r["axis"] == r38["axis"] and r["variant"] == r38["variant"]
        ]
        if not match or match[0]["axis_proxy_min"] is None or r38["axis_proxy_min"] is None:
            continue
        r33 = match[0]
        deltas.append(
            {
                "arm": "A038_minus_A033",
                "axis": r38["axis"],
                "weight": r38["weight"],
                "variant": r38["variant"],
                "uses_completion_factor": r38["uses_completion_factor"],
                "pairs_required": r38["pairs_required"],
                "pairs_present": r38["pairs_present"],
                "axis_scorable": r38["axis_scorable"] and r33["axis_scorable"],
                "axis_proxy_min": r38["axis_proxy_min"] - r33["axis_proxy_min"],
                "worst_case": f"{r33['worst_case']}@{r33['worst_seed']} -> {r38['worst_case']}@{r38['worst_seed']}",
                "worst_seed": "",
                "axis_points_of_70": r38["axis_points_of_70"] - r33["axis_points_of_70"],
                "axis_points_counted_by_engine": (
                    r38["axis_points_counted_by_engine"] - r33["axis_points_counted_by_engine"]
                ),
            }
        )
    return out + deltas


def climb_counts() -> list[dict[str, Any]]:
    """Posture-gate-free stair reading, using the same counter the gate uses.

    tools/go2_climb_count.py reads only steps.csv root_z (rise from the settled
    row, rows at least MIN_TRAVEL_M from the start, env rows truncated at first
    termination).  It never touches survival_proxy or the posture gate, which is
    why it is the figure the rejection rests on.
    """
    import sys

    sys.path.insert(0, str(REPO / "tools"))
    import go2_climb_count as climb  # noqa: E402

    case = "stairs_10_down"
    height = climb.STAIR_HEIGHTS[case]
    rows: list[dict[str, Any]] = []
    for arm in ("A033", "A038"):
        total = {"ge1": 0, "ge2": 0, "full": 0, "robots": 0}
        for seed in SEEDS:
            path = case_dir(arm, seed, case) / "steps.csv"
            if not path.is_file():
                continue
            r = climb.count(path, height)
            if r is None:
                continue
            rows.append({"arm": arm, "seed": seed, "case": case, **r})
            for k in total:
                total[k] += r[k]
        rows.append(
            {
                "arm": arm,
                "seed": "SUM",
                "case": case,
                "height_key": "",
                "terrain_start_m": "",
                "direction": "",
                **total,
            }
        )
    return rows


def stairs_time_profile(case: str = "stairs_10_down", bin_size: int = 100) -> list[dict[str, Any]]:
    import statistics

    rows: list[dict[str, Any]] = []
    for arm in ("A033", "A038"):
        for seed in SEEDS:
            path = case_dir(arm, seed, case) / "steps.csv"
            if not path.is_file():
                continue
            bins: dict[int, dict[str, Any]] = {}
            with path.open("r", encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    b = (int(r["step"]) - 1) // bin_size
                    e = bins.setdefault(b, {"hr": [], "pg": [], "sp": [], "tz": [], "up": 0, "n": 0})
                    e["hr"].append(float(r["height_rel"]))
                    e["pg"].append(float(r["proj_grav_z"]))
                    e["sp"].append(float(r["speed_xy"]))
                    e["tz"].append(float(r["terrain_z"]))
                    e["up"] += int(float(r["upright"]) > 0.5)
                    e["n"] += 1
            for b in sorted(bins):
                e = bins[b]
                rows.append(
                    {
                        "arm": arm,
                        "seed": seed,
                        "case": case,
                        "step_bin_start": b * bin_size + 1,
                        "step_bin_end": (b + 1) * bin_size,
                        "height_rel_median": statistics.median(e["hr"]),
                        "height_rel_mean": sum(e["hr"]) / e["n"],
                        "proj_grav_z_mean": sum(e["pg"]) / e["n"],
                        "speed_xy_mean": sum(e["sp"]) / e["n"],
                        "terrain_z_mean": sum(e["tz"]) / e["n"],
                        "upright_frac": e["up"] / e["n"],
                        "rows": e["n"],
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    registry = _load(QUAD / "config" / "go2_self_eval_registry.json")
    std = float(registry["score"].get("tracking_proxy_std", 0.5))

    summaries = collect_summaries(std)
    write_csv(out / "CASE_SUMMARY.csv", summaries)
    write_csv(out / "AXIS_RECON.csv", axis_reconstruction(summaries))

    env_rows = per_env_stairs("stairs_10_down")
    write_csv(out / "STAIRS10_PER_ENV.csv", env_rows)
    write_csv(out / "STAIRS10_ROLLUP.csv", per_env_rollup(env_rows))

    lat_rows = per_env_stairs("rough_lateral")
    write_csv(out / "ROUGH_LATERAL_PER_ENV.csv", lat_rows)
    write_csv(out / "ROUGH_LATERAL_ROLLUP.csv", per_env_rollup(lat_rows))

    chan: list[dict[str, Any]] = []
    chan_roll: list[dict[str, Any]] = []
    for case in ("stairs_10_down", "rough_lateral"):
        rows_c = fall_channel_attribution(case)
        chan.extend(rows_c)
        chan_roll.extend(channel_rollup(rows_c))
    write_csv(out / "FALL_CHANNEL_PER_ENV.csv", chan)
    write_csv(out / "FALL_CHANNEL_ROLLUP.csv", chan_roll)

    write_csv(out / "CLIMB_COUNT.csv", climb_counts())
    write_csv(out / "STAIRS10_TIME_PROFILE.csv", stairs_time_profile())

    print(f"tracking_proxy_std={std}")
    print(f"wrote {out}")
    for name in (
        "CASE_SUMMARY.csv",
        "AXIS_RECON.csv",
        "STAIRS10_PER_ENV.csv",
        "STAIRS10_ROLLUP.csv",
        "ROUGH_LATERAL_PER_ENV.csv",
        "ROUGH_LATERAL_ROLLUP.csv",
        "FALL_CHANNEL_PER_ENV.csv",
        "FALL_CHANNEL_ROLLUP.csv",
        "CLIMB_COUNT.csv",
        "STAIRS10_TIME_PROFILE.csv",
    ):
        p = out / name
        print(f"  {name}: {p.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
