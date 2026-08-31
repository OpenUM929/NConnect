"""Build a compact report from fixed-evaluation telemetry (standard library only)."""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from pathlib import Path


# Self-assessment v1.  The competition guide discloses survival * tracking but
# not the evaluator's exact tracking transform.  We therefore reuse the
# exponential tracking shape and std=0.5 recorded in Run06 env.yaml.  This is
# an internal, versioned proxy and must never be labelled an official score.
TRACKING_STD = 0.5
MIN_SURVIVAL = 0.95
MIN_TRACKING = 0.70
MIN_SIMULATION_FRACTION = 0.70
SCENARIO_WEIGHTS = {
    "H1": 0.15,
    "H2": 0.20,
    "H3": 0.10,
    "H4": 0.10,
    "H5": 0.15,
    "H6": 0.15,
    "H7": 0.15,
}
SCENARIO_CASES = {
    "H1": ("H1_stand",),
    "H2": ("H2_forward",),
    "H3": ("H3_left", "H3_right"),
    "H4": ("H4_left", "H4_right"),
    "H5": ("H5_rough",),
    "H6": ("H6_plus10", "H6_minus10"),
    "H7": ("H7_push",),
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _h7_recovery(case_dir: Path) -> dict:
    """Estimate recovery after configured 4 s pushes; this is an analysis proxy."""

    metadata = _load_json(case_dir / "metadata.json")
    dt = float(metadata["step_dt"])
    by_env: dict[int, list[tuple[float, float]]] = {}
    with (case_dir / "steps.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_env.setdefault(int(row["env_id"]), []).append(
                (float(row["time_s"]), float(row["speed_xy"]))
            )

    recoveries: list[float] = []
    observed = 0
    expected = 0
    quiet_steps = max(1, round(0.5 / dt))
    max_time = max((samples[-1][0] for samples in by_env.values()), default=0.0)
    push_times = [value for value in (4.0, 8.0, 12.0, 16.0) if value + 1.0 <= max_time]
    for samples in by_env.values():
        for push_time in push_times:
            expected += 1
            candidates = [
                (index, time_s, speed)
                for index, (time_s, speed) in enumerate(samples)
                if push_time <= time_s <= push_time + 1.0
            ]
            if not candidates:
                continue
            peak_index, peak_time, peak_speed = max(candidates, key=lambda item: item[2])
            if peak_speed < 0.20:
                continue
            observed += 1
            for index in range(peak_index, len(samples) - quiet_steps + 1):
                window = samples[index:index + quiet_steps]
                if all(speed <= 0.15 for _, speed in window):
                    recoveries.append(window[0][0] - peak_time)
                    break

    return {
        "method": "push at configured 4 s intervals; peak >=0.20 m/s; recovery <=0.15 m/s for 0.5 s",
        "expected_env_events": expected,
        "observed_disturbances": observed,
        "recovered_events": len(recoveries),
        "recovery_rate_observed": len(recoveries) / observed if observed else None,
        "median_recovery_s": statistics.median(recoveries) if recoveries else None,
        "max_recovery_s": max(recoveries) if recoveries else None,
    }


def _tracking_reward(rmse: float | None) -> float | None:
    if rmse is None:
        return None
    return math.exp(-((float(rmse) / TRACKING_STD) ** 2))


def _case_proxy(scenario: str, case: dict, h7_recovery: dict | None) -> dict:
    survival = case.get("survival_rate_completed")
    xy = _tracking_reward(case.get("tracking_xy_rmse"))
    yaw = _tracking_reward(case.get("tracking_yaw_rmse"))

    if scenario in {"H2", "H3", "H5", "H6"}:
        tracking = xy
    else:
        # Standing, combined turning and push recovery all require both linear
        # and angular command compliance; use the weaker axis conservatively.
        values = [value for value in (xy, yaw) if value is not None]
        tracking = min(values) if len(values) == 2 else None
    if scenario == "H7":
        recovery_data = h7_recovery or {}
        expected = recovery_data.get("expected_env_events")
        recovered = recovery_data.get("recovered_events")
        recovery = (
            recovered / expected
            if expected and recovered is not None
            else recovery_data.get("recovery_rate_observed")
        )
        tracking = min(tracking, recovery) if tracking is not None and recovery is not None else None

    score = survival * tracking if survival is not None and tracking is not None else None
    return {
        "survival_proxy": survival,
        "tracking_proxy": tracking,
        "scenario_proxy": score,
    }


def build_self_score(cases: dict[str, dict], h7_recovery: dict | None) -> dict:
    """Build a conservative seven-scenario readiness score, never an official score."""

    scenarios: dict[str, dict] = {}
    missing: list[str] = []
    for scenario, required_cases in SCENARIO_CASES.items():
        if any(name not in cases for name in required_cases):
            missing.append(scenario)
            continue
        case_proxies = {
            name: _case_proxy(scenario, cases[name], h7_recovery)
            for name in required_cases
        }
        if any(item["scenario_proxy"] is None for item in case_proxies.values()):
            missing.append(scenario)
            continue
        survival = min(item["survival_proxy"] for item in case_proxies.values())
        tracking = min(item["tracking_proxy"] for item in case_proxies.values())
        proxy = min(item["scenario_proxy"] for item in case_proxies.values())
        gate = (
            "INTERNAL_SCENARIO_PASS"
            if survival >= MIN_SURVIVAL and tracking >= MIN_TRACKING
            else "INTERNAL_SCENARIO_FAIL"
        )
        scenarios[scenario] = {
            "weight": SCENARIO_WEIGHTS[scenario],
            "cases": case_proxies,
            "survival_proxy": survival,
            "tracking_proxy": tracking,
            "scenario_proxy": proxy,
            "weighted_fraction": SCENARIO_WEIGHTS[scenario] * proxy,
            "gate": gate,
        }

    simulation_fraction = sum(item["weighted_fraction"] for item in scenarios.values())
    failed = [name for name, item in scenarios.items() if item["gate"] != "INTERNAL_SCENARIO_PASS"]
    if missing:
        status = "SELF_ASSESSMENT_INCOMPLETE"
    elif failed or simulation_fraction < MIN_SIMULATION_FRACTION:
        status = "SELF_ASSESSMENT_FAIL"
    else:
        status = "SELF_ASSESSMENT_PASS"
    return {
        "schema_version": 1,
        "method": "internal proxy v1; survival * exp(-(tracking_RMSE/0.5)^2); worst case for paired directions",
        "official_score": False,
        "thresholds": {
            "min_survival_per_scenario": MIN_SURVIVAL,
            "min_tracking_per_scenario": MIN_TRACKING,
            "min_simulation_fraction": MIN_SIMULATION_FRACTION,
        },
        "scenarios": scenarios,
        "missing_scenarios": missing,
        "failed_scenarios": failed,
        "simulation_fraction": simulation_fraction,
        "simulation_normalized_100": 100.0 * simulation_fraction,
        "simulation_points_70": 70.0 * simulation_fraction,
        "status": status,
    }


def build(root: Path) -> dict:
    case_root = root / "cases"
    cases = {
        path.name: _load_json(path / "summary.json")
        for path in sorted(case_root.iterdir())
        if path.is_dir() and (path / "summary.json").is_file()
    }
    h7_recovery = _h7_recovery(case_root / "H7_push") if "H7_push" in cases else None
    report = {
        "schema_version": 1,
        "scope": "fixed-policy evaluation; no training",
        "cases": cases,
        "h4_yaw_tracking": {
            name: cases[name].get("tracking_yaw_mae")
            for name in ("H4_left", "H4_right") if name in cases
        },
        "h6_slope_tracking": {
            name: {
                "tracking_xy_mae": cases[name].get("tracking_xy_mae"),
                "early_terminations": cases[name].get("early_terminations"),
                "timeouts": cases[name].get("timeouts"),
            }
            for name in ("H6_plus10", "H6_minus10") if name in cases
        },
        "h7_push_recovery_proxy": h7_recovery,
        "self_assessment": build_self_score(cases, h7_recovery),
        "limitations": [
            "The exact official tracking-score transform is not disclosed; self_assessment is internal proxy v1.",
            "Proxy-v1 thresholds were frozen after viewing partial H4/H6/H7 telemetry; those cases are calibration, not independent validation.",
            "One checkpoint and one fixed seed do not establish generalization.",
            "The H7 recovery calculation is an internal proxy, not an official score definition.",
            "A completed run is evidence collection, not an automatic PASS decision.",
        ],
    }
    return report


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fixed_eval_report.py <evaluation-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    report = build(root)
    (root / "FIXED_EVAL_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# Run06 fixed-policy evaluation",
        "",
        "This report contains measurements only; final PASS/FAIL is decided after local review.",
        "",
        "| case | xy MAE | yaw MAE | early terminations | timeouts |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, case in report["cases"].items():
        lines.append(
            f"| {name} | {case.get('tracking_xy_mae')} | {case.get('tracking_yaw_mae')} | "
            f"{case.get('early_terminations')} | {case.get('timeouts')} |"
        )
    h7 = report.get("h7_push_recovery_proxy") or {}
    self_score = report["self_assessment"]
    lines += [
        "",
        "## H7 recovery proxy",
        f"- observed disturbances: {h7.get('observed_disturbances')}",
        f"- recovered events: {h7.get('recovered_events')}",
        f"- median recovery seconds: {h7.get('median_recovery_s')}",
        "",
        "## Internal seven-scenario scorecard",
        f"- status: {self_score['status']}",
        f"- simulation proxy: {self_score['simulation_normalized_100']:.2f}/100",
        f"- simulation points proxy: {self_score['simulation_points_70']:.2f}/70",
        f"- missing scenarios: {', '.join(self_score['missing_scenarios']) or 'none'}",
        f"- failed scenarios: {', '.join(self_score['failed_scenarios']) or 'none'}",
        "",
        "| scenario | survival proxy | tracking proxy | scenario proxy | gate |",
        "|---|---:|---:|---:|---|",
        *[
            f"| {name} | {item['survival_proxy']:.4f} | {item['tracking_proxy']:.4f} | "
            f"{item['scenario_proxy']:.4f} | {item['gate']} |"
            for name, item in self_score["scenarios"].items()
        ],
        "",
        "## Limitations",
        *[f"- {item}" for item in report["limitations"]],
    ]
    (root / "FIXED_EVAL_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
