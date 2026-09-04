"""Build low-cost Go2 tier-1 and representative internal proxy reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from go2_fixed_eval_report import _load, _write_policy, build_policy


def _all_scenario_gates(policy: dict[str, Any]) -> bool:
    return len(policy.get("scenarios", {})) == 7 and all(
        item.get("gate") == "INTERNAL_SCENARIO_PASS"
        for item in policy["scenarios"].values()
    )


def tier1_decision(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    scenarios = sorted(set(baseline.get("scenarios", {})) & set(candidate.get("scenarios", {})))
    deltas = {
        scenario: {
            "proxy": candidate["scenarios"][scenario]["scenario_proxy"]
            - baseline["scenarios"][scenario]["scenario_proxy"],
            "survival": candidate["scenarios"][scenario]["survival_proxy"]
            - baseline["scenarios"][scenario]["survival_proxy"],
            "tracking": candidate["scenarios"][scenario]["tracking_proxy"]
            - baseline["scenarios"][scenario]["tracking_proxy"],
        }
        for scenario in scenarios
    }
    reasons: list[str] = []
    points_delta = candidate["simulation_points_70"] - baseline["simulation_points_70"]
    if points_delta < 0.0:
        reasons.append("weighted_proxy_regressed")
    if deltas.get("G1", {}).get("proxy", 0.0) < 0.05:
        reasons.append("target_G1_improvement_below_0.05")
    for scenario, item in deltas.items():
        if item["survival"] < -0.10:
            reasons.append(f"{scenario}_survival_regressed_over_0.10")
    return {
        "schema_version": 1,
        "status": "INTERNAL_EARLY_KILL_PASS" if not reasons else "INTERNAL_EARLY_KILL_FAIL",
        "purpose": "Reject a clear track_lin_vel_xy_exp regression before 3-seed representative evaluation.",
        "baseline_points_70": baseline["simulation_points_70"],
        "candidate_points_70": candidate["simulation_points_70"],
        "candidate_minus_baseline_points_70": points_delta,
        "scenario_deltas": deltas,
        "failure_reasons": reasons,
        "official_result": "OFFICIAL_RESULT_UNMEASURED",
    }


def representative_decision(candidate: dict[str, Any]) -> dict[str, Any]:
    points_ok = candidate.get("simulation_points_70", 0.0) >= 60.0
    gates_ok = _all_scenario_gates(candidate)
    seeds_ok = sorted(candidate.get("seed_fractions", {})) == ["101", "202", "303"]
    reasons: list[str] = []
    if not points_ok:
        reasons.append("simulation_proxy_below_60_of_70")
    if not gates_ok:
        reasons.append("one_or_more_scenario_stability_gates_failed")
    if not seeds_ok:
        reasons.append("required_seed_set_incomplete")
    return {
        "schema_version": 1,
        "status": (
            "INTERNAL_REPRESENTATIVE_PROMOTION_PASS"
            if not reasons
            else "INTERNAL_REPRESENTATIVE_PROMOTION_FAIL"
        ),
        "candidate_points_70": candidate.get("simulation_points_70"),
        "minimum_points_70": 60.0,
        "scenario_stability_gates_ok": gates_ok,
        "required_seeds_complete": seeds_ok,
        "failure_reasons": reasons,
        "official_result": "OFFICIAL_RESULT_UNMEASURED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("tier1", "representative"), required=True)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--baseline-root", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    candidate = build_policy(
        args.candidate_root,
        args.registry,
        _load(args.candidate_root / "identity.json"),
    )
    _write_policy(args.candidate_root, candidate)

    if args.mode == "tier1":
        if args.baseline_root is None:
            parser.error("--baseline-root is required for tier1")
        baseline = build_policy(
            args.baseline_root,
            args.registry,
            _load(args.baseline_root / "identity.json"),
        )
        _write_policy(args.baseline_root, baseline)
        decision = tier1_decision(baseline, candidate)
        name = "TIER1_DECISION.json"
    else:
        decision = representative_decision(candidate)
        name = "REPRESENTATIVE_DECISION.json"

    (args.out / name).write_text(
        json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(decision["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
