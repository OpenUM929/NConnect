"""Aggregate predeclared multi-seed Run06 validation telemetry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fixed_eval_report


EXPECTED_SEEDS = (101, 202, 303)


def build_validation(seed_reports: dict[int, dict]) -> dict:
    """Use the worst seed for every scenario and require every seed to pass."""

    missing_seeds = [seed for seed in EXPECTED_SEEDS if seed not in seed_reports]
    scenarios: dict[str, dict] = {}
    failed_seeds: list[int] = []

    for seed, report in sorted(seed_reports.items()):
        if report["self_assessment"]["status"] != "SELF_ASSESSMENT_PASS":
            failed_seeds.append(seed)

    if not missing_seeds:
        for scenario, weight in fixed_eval_report.SCENARIO_WEIGHTS.items():
            per_seed = {
                str(seed): seed_reports[seed]["self_assessment"]["scenarios"][scenario]
                for seed in EXPECTED_SEEDS
            }
            survival = min(item["survival_proxy"] for item in per_seed.values())
            tracking = min(item["tracking_proxy"] for item in per_seed.values())
            proxy = min(item["scenario_proxy"] for item in per_seed.values())
            scenarios[scenario] = {
                "weight": weight,
                "per_seed": per_seed,
                "worst_survival_proxy": survival,
                "worst_tracking_proxy": tracking,
                "worst_scenario_proxy": proxy,
                "weighted_fraction": weight * proxy,
                "gate": (
                    "INDEPENDENT_SCENARIO_PASS"
                    if survival >= fixed_eval_report.MIN_SURVIVAL
                    and tracking >= fixed_eval_report.MIN_TRACKING
                    else "INDEPENDENT_SCENARIO_FAIL"
                ),
            }

    fraction = sum(item["weighted_fraction"] for item in scenarios.values())
    failed_scenarios = [
        name for name, item in scenarios.items()
        if item["gate"] != "INDEPENDENT_SCENARIO_PASS"
    ]
    if missing_seeds:
        status = "INDEPENDENT_VALIDATION_INCOMPLETE"
    elif failed_seeds or failed_scenarios or fraction < fixed_eval_report.MIN_SIMULATION_FRACTION:
        status = "INDEPENDENT_VALIDATION_FAIL"
    else:
        status = "INDEPENDENT_VALIDATION_PASS"

    return {
        "schema_version": 1,
        "status": status,
        "official_score": False,
        "predeclared_seeds": list(EXPECTED_SEEDS),
        "missing_seeds": missing_seeds,
        "failed_seeds": failed_seeds,
        "failed_scenarios": failed_scenarios,
        "method": "worst seed per H1-H7 scenario; frozen proxy-v1 thresholds",
        "scenarios": scenarios,
        "simulation_fraction_worst_seed_by_scenario": fraction,
        "simulation_normalized_100": 100.0 * fraction,
        "simulation_points_70": 70.0 * fraction,
    }


def build(root: Path) -> dict:
    seed_reports: dict[int, dict] = {}
    for seed in EXPECTED_SEEDS:
        seed_root = root / "seeds" / f"seed_{seed}"
        if seed_root.is_dir():
            seed_reports[seed] = fixed_eval_report.build(seed_root)
    return {
        "schema_version": 1,
        "scope": "frozen Run06 policy; independent seeds; no training",
        "seed_reports": {str(seed): report for seed, report in seed_reports.items()},
        "independent_validation": build_validation(seed_reports),
        "limitations": [
            "This remains an internal proxy, not an official competition score.",
            "Three seeds reduce but do not eliminate simulation generalization uncertainty.",
            "The scenario definitions approximate the disclosed competition descriptions.",
            "The policy, proxy formula and thresholds are frozen before these seeds are run.",
        ],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: independent_eval_report.py <evaluation-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    report = build(root)
    validation = report["independent_validation"]
    (root / "INDEPENDENT_EVAL_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# Run06 independent multi-seed validation",
        "",
        f"- status: {validation['status']}",
        f"- simulation proxy: {validation['simulation_normalized_100']:.2f}/100",
        f"- simulation points proxy: {validation['simulation_points_70']:.2f}/70",
        f"- predeclared seeds: {', '.join(map(str, validation['predeclared_seeds']))}",
        f"- missing seeds: {', '.join(map(str, validation['missing_seeds'])) or 'none'}",
        f"- failed seeds: {', '.join(map(str, validation['failed_seeds'])) or 'none'}",
        "",
        "| scenario | worst survival | worst tracking | worst proxy | gate |",
        "|---|---:|---:|---:|---|",
    ]
    for name, item in validation["scenarios"].items():
        lines.append(
            f"| {name} | {item['worst_survival_proxy']:.4f} | "
            f"{item['worst_tracking_proxy']:.4f} | {item['worst_scenario_proxy']:.4f} | "
            f"{item['gate']} |"
        )
    lines += ["", "## Limitations", *[f"- {item}" for item in report["limitations"]]]
    (root / "INDEPENDENT_EVAL_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
