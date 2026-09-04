"""Generic tier-1 and representative reports driven by a validated experiment JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from go2_fixed_eval_report import _load, _write_policy, build_policy
from go2_tuning_config import load_and_validate


def tier1_decision(
    baseline: dict[str, Any], candidate: dict[str, Any], gates: dict[str, Any]
) -> dict[str, Any]:
    scenarios = sorted(set(baseline.get("scenarios", {})) & set(candidate.get("scenarios", {})))
    deltas = {
        scenario: {
            "proxy": candidate["scenarios"][scenario]["scenario_proxy"] - baseline["scenarios"][scenario]["scenario_proxy"],
            "survival": candidate["scenarios"][scenario]["survival_proxy"] - baseline["scenarios"][scenario]["survival_proxy"],
            "tracking": candidate["scenarios"][scenario]["tracking_proxy"] - baseline["scenarios"][scenario]["tracking_proxy"],
        }
        for scenario in scenarios
    }
    reasons: list[str] = []
    points_delta = candidate["simulation_points_70"] - baseline["simulation_points_70"]
    # Engine 1.2.0 gates the weighted total, which is what the official rule scores
    # (시나리오 점수 = 생존율 x 추종 점수, summed with the published weights). Engine
    # 1.1.0 gated a single pinned scenario instead; on G-A010, G-A011 and G-A013 that
    # clause disagreed with the weighted total on every run, so it is now informational.
    if points_delta + 1.0e-12 < gates["min_total_points_delta"]:
        reasons.append(f"total_points_70_delta_below_{gates['min_total_points_delta']}")
    for scenario, item in deltas.items():
        if item["survival"] < -gates["max_survival_regression"]:
            reasons.append(f"{scenario}_survival_regressed_over_{gates['max_survival_regression']}")
    target = gates.get("target_scenario")
    observed_target = None
    if target is not None:
        observed_target = {
            "scenario": target,
            "proxy_delta": deltas.get(target, {}).get("proxy"),
            "reference_min_proxy_delta": gates.get("target_min_proxy_delta"),
            "note": "informational since engine 1.2.0; does not gate promotion",
        }
    return {
        "schema_version": 3,
        "status": "INTERNAL_EARLY_KILL_PASS" if not reasons else "INTERNAL_EARLY_KILL_FAIL",
        "target_scenario": target,
        "target_scenario_observation": observed_target,
        "gates": gates,
        "baseline_points_70": baseline["simulation_points_70"],
        "candidate_points_70": candidate["simulation_points_70"],
        "candidate_minus_baseline_points_70": points_delta,
        "scenario_deltas": deltas,
        "failure_reasons": reasons,
        "official_result": "OFFICIAL_RESULT_UNMEASURED",
    }


def representative_decision(candidate: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    points_ok = candidate.get("simulation_points_70", 0.0) >= gates["minimum_points_70"]
    scenarios = candidate.get("scenarios", {})
    gates_ok = len(scenarios) == 7 and all(
        item.get("survival_proxy", 0.0) >= gates["required_survival_proxy"]
        and item.get("tracking_proxy", 0.0) >= gates["required_tracking_proxy"]
        for item in scenarios.values()
    )
    seeds_ok = sorted(candidate.get("seed_fractions", {})) == ["101", "202", "303"]
    reasons: list[str] = []
    if not points_ok:
        reasons.append("simulation_proxy_below_minimum")
    if not gates_ok:
        reasons.append("one_or_more_scenario_stability_gates_failed")
    if not seeds_ok:
        reasons.append("required_seed_set_incomplete")
    return {
        "schema_version": 2,
        "status": "INTERNAL_REPRESENTATIVE_PROMOTION_PASS" if not reasons else "INTERNAL_REPRESENTATIVE_PROMOTION_FAIL",
        "candidate_points_70": candidate.get("simulation_points_70"),
        "gates": gates,
        "scenario_stability_gates_ok": gates_ok,
        "required_seeds_complete": seeds_ok,
        "failure_reasons": reasons,
        "official_result": "OFFICIAL_RESULT_UNMEASURED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("tier1", "representative"), required=True)
    parser.add_argument("--experiment", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--baseline-root", type=Path)
    args = parser.parse_args()
    experiment = load_and_validate(args.experiment)
    gates = experiment["evaluation"]["gates"]
    args.out.mkdir(parents=True, exist_ok=True)
    candidate = build_policy(args.candidate_root, args.registry, _load(args.candidate_root / "identity.json"))
    _write_policy(args.candidate_root, candidate)
    if args.mode == "tier1":
        if args.baseline_root is None:
            parser.error("--baseline-root is required for tier1")
        baseline = build_policy(args.baseline_root, args.registry, _load(args.baseline_root / "identity.json"))
        _write_policy(args.baseline_root, baseline)
        decision = tier1_decision(baseline, candidate, gates)
        name = "TIER1_DECISION.json"
    else:
        decision = representative_decision(candidate, gates)
        name = "REPRESENTATIVE_DECISION.json"
    decision["work_id"] = experiment["work_id"]
    decision["run_id"] = experiment["run_id"]
    (args.out / name).write_text(json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8")
    print(decision["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
