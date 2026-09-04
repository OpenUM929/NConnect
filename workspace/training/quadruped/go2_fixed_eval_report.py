"""Aggregate Go2 G1-G7 telemetry and build a paired internal comparison."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


TRACKING_STD = 0.5


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _track(rmse: float | None) -> float | None:
    return None if rmse is None else math.exp(-((float(rmse) / TRACKING_STD) ** 2))


def _case_proxy(case_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    survival = summary.get("survival_proxy")
    xy = _track(summary.get("tracking_xy_rmse"))
    yaw = _track(summary.get("tracking_yaw_rmse"))
    tracking = xy
    if case_id.startswith("combined_yaw"):
        tracking = min(xy, yaw) if xy is not None and yaw is not None else None
    if case_id.startswith("stairs_"):
        duration = float(summary.get("steps", 0)) * float(summary.get("step_dt", 0.02))
        expected = 0.5 * duration
        completion = min(1.0, float(summary.get("projected_progress_m") or 0.0) / expected) if expected else None
        tracking = min(tracking, completion) if tracking is not None and completion is not None else None
    else:
        completion = None
    if case_id.startswith("push_"):
        tracking = _track(summary.get("post_push_tracking_xy_rmse"))
        recovery = (summary.get("recovery") or {}).get("recovery_rate")
        tracking = min(tracking, recovery) if tracking is not None and recovery is not None else None
    else:
        recovery = None
    proxy = survival * tracking if survival is not None and tracking is not None else None
    return {
        "survival_proxy": survival,
        "tracking_proxy": tracking,
        "scenario_proxy": proxy,
        "obstacle_completion": completion,
        "recovery_rate": recovery,
    }


def build_policy(root: Path, registry_path: Path, identity: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = _load(registry_path)
    seeds = [int(seed) for seed in registry["score"]["internal_gates"]["required_evaluation_seeds"]]
    cases: dict[str, Any] = {}
    expected: list[tuple[str, str, int]] = []
    for scenario in registry["scenarios"]:
        for case_id in scenario["internal_cases"]:
            if scenario["id"] == "G7":
                expected.append((scenario["id"], case_id, int(case_id.rsplit("_", 1)[1])))
            else:
                expected.extend((scenario["id"], case_id, seed) for seed in seeds)

    missing: list[str] = []
    for scenario_id, case_id, seed in expected:
        path = root / "cases" / f"seed_{seed}" / case_id / "summary.json"
        key = f"{scenario_id}/{case_id}/seed_{seed}"
        if not path.is_file():
            missing.append(key)
            continue
        summary = _load(path)
        cases[key] = {
            "scenario_id": scenario_id,
            "case_id": case_id,
            "seed": seed,
            "raw": summary,
            "proxy": _case_proxy(case_id, summary),
        }

    gates = registry["score"]["internal_gates"]
    scenarios: dict[str, Any] = {}
    for scenario in registry["scenarios"]:
        scenario_cases = [item for item in cases.values() if item["scenario_id"] == scenario["id"]]
        required_count = len(scenario["internal_cases"]) if scenario["id"] == "G7" else len(scenario["internal_cases"]) * len(seeds)
        valid = [item for item in scenario_cases if item["proxy"]["scenario_proxy"] is not None]
        if len(valid) != required_count:
            continue
        worst = min(valid, key=lambda item: item["proxy"]["scenario_proxy"])
        survival = min(item["proxy"]["survival_proxy"] for item in valid)
        tracking = min(item["proxy"]["tracking_proxy"] for item in valid)
        proxy = min(item["proxy"]["scenario_proxy"] for item in valid)
        scenarios[scenario["id"]] = {
            "name": scenario["name"],
            "weight": scenario["weight"],
            "survival_proxy": survival,
            "tracking_proxy": tracking,
            "scenario_proxy": proxy,
            "weighted_fraction": scenario["weight"] * proxy,
            "worst_case": {"case_id": worst["case_id"], "seed": worst["seed"]},
            "per_seed": {
                str(seed): min(
                    item["proxy"]["scenario_proxy"] for item in valid if item["seed"] == seed
                )
                for seed in seeds
                if any(item["seed"] == seed for item in valid)
            },
            "gate": (
                "INTERNAL_SCENARIO_PASS"
                if survival >= gates["minimum_survival_proxy_each"] and tracking >= gates["minimum_tracking_proxy_each"]
                else "INTERNAL_SCENARIO_FAIL"
            ),
        }
    fraction = sum(item["weighted_fraction"] for item in scenarios.values())
    seed_fractions = {
        str(seed): sum(
            item["weight"] * item["per_seed"].get(str(seed), 0.0)
            for item in scenarios.values()
        )
        for seed in seeds
    }
    failed = [key for key, item in scenarios.items() if item["gate"] != "INTERNAL_SCENARIO_PASS"]
    if missing or len(scenarios) != len(registry["scenarios"]):
        status = "SELF_ASSESSMENT_INCOMPLETE"
    elif failed or fraction < gates["minimum_weighted_simulation_proxy"]:
        status = "INTERNAL_GATE_FAIL"
    else:
        status = "INTERNAL_GATE_PASS"
    return {
        "schema_version": 1,
        "official_result": False,
        "method": "Go2 internal proxy v1; worst case across frozen cases and seeds",
        "identity": identity or {},
        "expected_telemetry_count": len(expected),
        "observed_telemetry_count": len(cases),
        "missing": missing,
        "cases": cases,
        "scenarios": scenarios,
        "failed_scenarios": failed,
        "simulation_fraction": fraction,
        "seed_fractions": seed_fractions,
        "simulation_points_70": 70.0 * fraction,
        "status": status,
        "limitations": registry["official_unknowns"],
    }


def paired(default: dict[str, Any], pilot: dict[str, Any]) -> dict[str, Any]:
    delta = pilot["simulation_fraction"] - default["simulation_fraction"]
    common = sorted(set(default["scenarios"]) & set(pilot["scenarios"]))
    per_scenario = {
        scenario: {
            "default": default["scenarios"][scenario],
            "pilot": pilot["scenarios"][scenario],
            "delta_survival": pilot["scenarios"][scenario]["survival_proxy"] - default["scenarios"][scenario]["survival_proxy"],
            "delta_tracking": pilot["scenarios"][scenario]["tracking_proxy"] - default["scenarios"][scenario]["tracking_proxy"],
            "delta_proxy": pilot["scenarios"][scenario]["scenario_proxy"] - default["scenarios"][scenario]["scenario_proxy"],
        }
        for scenario in common
    }
    seed_deltas = {
        seed: pilot.get("seed_fractions", {}).get(seed, 0.0) - default.get("seed_fractions", {}).get(seed, 0.0)
        for seed in sorted(set(default.get("seed_fractions", {})) | set(pilot.get("seed_fractions", {})))
    }
    same_direction = sum(1 for value in seed_deltas.values() if value >= 0.0) >= 2
    no_seed_inversion = all(value >= -0.02 for value in seed_deltas.values())
    if default["status"] == "SELF_ASSESSMENT_INCOMPLETE" or pilot["status"] == "SELF_ASSESSMENT_INCOMPLETE":
        decision = "SELF_ASSESSMENT_INCOMPLETE"
    elif default["simulation_fraction"] - pilot["simulation_fraction"] >= 0.03 or (
        default["status"] == "INTERNAL_GATE_PASS" and pilot["status"] == "INTERNAL_GATE_FAIL"
    ):
        decision = "RESTART_FROM_DEFAULT_CONFIRMED"
    elif set(default["failed_scenarios"]) & set(pilot["failed_scenarios"]):
        decision = "SHARED_WEAKNESS_FOUND"
    elif delta >= 0.03 and same_direction and no_seed_inversion and all(item["delta_survival"] >= -0.02 and item["delta_tracking"] >= -0.05 for item in per_scenario.values()):
        # Quantitative gate only. Human video review is still required before promotion.
        decision = "PILOT_COMBINATION_PROMISING_VIDEO_REVIEW_PENDING"
    else:
        decision = "INTERNAL_GATE_INCONCLUSIVE"
    return {
        "schema_version": 1,
        "official_result": False,
        "comparison_metrics": "reward-independent survival/tracking/completion/recovery only",
        "default": {"status": default["status"], "simulation_fraction": default["simulation_fraction"]},
        "pilot": {"status": pilot["status"], "simulation_fraction": pilot["simulation_fraction"]},
        "pilot_minus_default": delta,
        "per_scenario": per_scenario,
        "per_seed_delta": seed_deltas,
        "seed_direction_consistent": same_direction,
        "no_seed_proxy_inversion_below_minus_0_02": no_seed_inversion,
        "decision": decision,
        "video_status": "VIDEO_UNKNOWN",
    }


def _write_policy(root: Path, report: dict[str, Any]) -> None:
    (root / "SELF_EVAL_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Go2 internal self evaluation", "", f"- status: {report['status']}",
        f"- telemetry: {report['observed_telemetry_count']}/{report['expected_telemetry_count']}",
        f"- simulation proxy: {report['simulation_points_70']:.3f}/70 (not official)", "",
        "| G | survival | tracking | proxy | worst case | gate |", "|---|---:|---:|---:|---|---|",
    ]
    for key, item in report["scenarios"].items():
        worst = item["worst_case"]
        lines.append(f"| {key} | {item['survival_proxy']:.4f} | {item['tracking_proxy']:.4f} | {item['scenario_proxy']:.4f} | {worst['case_id']}@{worst['seed']} | {item['gate']} |")
    lines += ["", "Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v1."]
    (root / "SELF_EVAL_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (root / "WORST_CASES.tsv").open("w", encoding="utf-8", newline="") as handle:
        handle.write("scenario\tcase_id\tseed\n")
        for key, item in report["scenarios"].items():
            handle.write(f"{key}\t{item['worst_case']['case_id']}\t{item['worst_case']['seed']}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--default-root", required=True, type=Path)
    parser.add_argument("--pilot-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    default = build_policy(args.default_root, args.registry, _load(args.default_root / "identity.json"))
    pilot = build_policy(args.pilot_root, args.registry, _load(args.pilot_root / "identity.json"))
    _write_policy(args.default_root, default)
    _write_policy(args.pilot_root, pilot)
    comparison = paired(default, pilot)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "GO2_DEFAULT_VS_PILOT_PAIRED_REPORT.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# Go2 Default-01 vs Pilot-01", "", f"- decision: {comparison['decision']}",
        f"- Pilot minus Default proxy: {comparison['pilot_minus_default']:+.4f}",
        "- video status: VIDEO_UNKNOWN (downloaded videos require human observation)",
        "- official result: not measured", "",
    ]
    (args.out / "GO2_DEFAULT_VS_PILOT_PAIRED_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
