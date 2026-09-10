"""Generic tier-1 and representative reports driven by a validated experiment JSON."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from go2_fixed_eval_report import (
    INADMISSIBLE_ARM_STATUS,
    LEGACY_TOLERANCE_PREFIX,
    _load,
    _write_policy,
    build_policy,
    instrument_mismatch,
    instrument_notes,
    instrument_unusable,
)
from go2_tuning_config import load_and_validate

# Measurement states that make an arm's numbers unfit to be one side of a delta.
# This is a measurement-validity list, deliberately not a performance list: a
# candidate that is merely bad must still be comparable, or screening cannot run.


def comparison_blockers(baseline: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    """Return every reason this pair may not be compared at all.

    Called before any delta is computed.  Engine 1.5.0 computed the deltas first
    and returned them alongside the invalid status, so numbers produced from two
    different rulers stayed in the record and could be read back as findings.
    """
    blocking: list[str] = []

    # Instrument symmetry.  Seven of the stored tuning runs measured the baseline
    # arm with the termination-only definition and the candidate arm with the
    # posture gate; those deltas were differences between two rulers.
    mismatch = instrument_mismatch(baseline, candidate)
    if mismatch:
        blocking.append("instrument_fingerprint_asymmetric:" + ",".join(mismatch))

    # An arm scored on the legacy recovery rate, or missing cases, is not a valid
    # side of a comparison even when its own performance looks acceptable.
    for label, arm in (("baseline", baseline), ("candidate", candidate)):
        if arm.get("status") in INADMISSIBLE_ARM_STATUS:
            blocking.append(f"{label}_measurement_{arm['status'].lower()}")
        elif arm.get("legacy_recovery_cases"):
            blocking.append(f"{label}_g6_scored_on_legacy_recovery_rate")

    # A baseline that does not walk pins its own survival at 1.0 under any
    # termination-based definition, so every candidate that starts walking looks
    # like a survival regression.  Comparisons against such a baseline are void.
    if baseline.get("locomotion", {}).get("verdict") == "POLICY_DOES_NOT_LOCOMOTE":
        blocking.append("baseline_does_not_locomote")
    return blocking


# Gate keys that a spec written before the engine that introduced them cannot
# carry.  Re-adjudicating an old run needs a value for each; supplying one silently
# would let a substituted number decide a verdict without appearing in the record.
GATE_MIGRATIONS: dict[str, tuple[str, str]] = {
    # added in engine 1.2.0; A010 and A013 predate it
    "min_total_points_delta": ("0.0", "engine 1.2.0; pre-1.2.0 specs gated a pinned scenario instead"),
    # added in engine 1.5.0; every stored spec predates it
    "max_scenario_proxy_regression": (
        "max_survival_regression",
        "engine 1.5.0; the old survival-only limit is reused as the product limit",
    ),
}


def migrate_gates(gates: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fill gate keys a legacy spec cannot carry, and record every value supplied."""
    migrated = dict(gates)
    applied: dict[str, Any] = {}
    for key, (source, note) in GATE_MIGRATIONS.items():
        if key in migrated:
            continue
        value = float(source) if source not in migrated else float(migrated[source])
        migrated[key] = value
        applied[key] = {"value": value, "taken_from": source, "introduced_in": note}
    return migrated, applied


def _arm_diagnostics(arm: dict[str, Any]) -> dict[str, Any]:
    """One arm's own absolute numbers, which stay readable even when the pair is void."""
    return {
        "points_70": arm.get("simulation_points_70"),
        "status": arm.get("status"),
        "status_reasons": arm.get("status_reasons"),
        "locomotion": arm.get("locomotion"),
        "instrument": arm.get("instrument"),
        "scenarios": {
            scenario: {
                "survival_proxy": item.get("survival_proxy"),
                "tracking_proxy": item.get("tracking_proxy"),
                "scenario_proxy": item.get("scenario_proxy"),
            }
            for scenario, item in arm.get("scenarios", {}).items()
        },
    }


def tier1_decision(
    baseline: dict[str, Any], candidate: dict[str, Any], gates: dict[str, Any]
) -> dict[str, Any]:
    blocking = comparison_blockers(baseline, candidate)
    if blocking:
        # No delta is computed and none is published.  Each arm's own measurement
        # is kept, clearly separated, so the run is still diagnosable.
        return {
            "schema_version": 5,
            "status": "INTERNAL_MEASUREMENT_INVALID",
            "blocking_reasons": blocking,
            "comparison_published": False,
            "comparison_note": "arms are not on one ruler; no delta exists to report",
            "baseline_points_70": None,
            "candidate_points_70": None,
            "candidate_minus_baseline_points_70": None,
            "scenario_deltas": None,
            "survival_regressions_observed": None,
            "failure_reasons": [],
            "gates": gates,
            "instrument_notes": {
                "baseline": instrument_notes(baseline),
                "candidate": instrument_notes(candidate),
            },
            "baseline_diagnostics": _arm_diagnostics(baseline),
            "candidate_diagnostics": _arm_diagnostics(candidate),
            "official_result": "OFFICIAL_RESULT_UNMEASURED",
        }

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
    gates, migration = migrate_gates(gates)
    if points_delta + 1.0e-12 < gates["min_total_points_delta"]:
        reasons.append(f"total_points_70_delta_below_{gates['min_total_points_delta']}")

    # Engine 1.5.0 gates the scenario product, not the survival factor alone.
    # survival and tracking are the two factors of one score; a candidate that
    # trades survival for more than as much tracking has a lower product and is
    # caught here, while a candidate whose product improved is no longer killed by
    # a factor that moved against it. G-A017 was rejected under the old clause with
    # +3.71/70 overall and its own G4 product up +0.0159.
    proxy_limit = float(gates["max_scenario_proxy_regression"])
    for scenario, item in deltas.items():
        if item["proxy"] < -proxy_limit:
            reasons.append(f"{scenario}_scenario_proxy_regressed_over_{proxy_limit}")
    survival_observations = {
        scenario: item["survival"]
        for scenario, item in deltas.items()
        if item["survival"] < -gates["max_survival_regression"]
    }
    target = gates.get("target_scenario")
    observed_target = None
    if target is not None:
        observed_target = {
            "scenario": target,
            "proxy_delta": deltas.get(target, {}).get("proxy"),
            "reference_min_proxy_delta": gates.get("target_min_proxy_delta"),
            "note": "informational since engine 1.2.0; does not gate promotion",
        }
    status = "INTERNAL_EARLY_KILL_FAIL" if reasons else "INTERNAL_EARLY_KILL_PASS"
    # How much slack the verdict has against the substituted product limit.  When a
    # migrated gate decided the outcome, this is the number that shows it.
    worst_proxy_delta = min((item["proxy"] for item in deltas.values()), default=None)
    return {
        "schema_version": 5,
        "status": status,
        "blocking_reasons": [],
        "comparison_published": True,
        "gate_migration": migration,
        "worst_scenario_proxy_delta": worst_proxy_delta,
        "scenario_proxy_regression_limit": proxy_limit,
        "instrument_baseline": baseline.get("instrument"),
        "instrument_candidate": candidate.get("instrument"),
        "instrument_notes": {
            "baseline": instrument_notes(baseline),
            "candidate": instrument_notes(candidate),
        },
        "baseline_locomotion": baseline.get("locomotion"),
        "candidate_locomotion": candidate.get("locomotion"),
        "survival_regressions_observed": survival_observations,
        "survival_regression_is_informational_since": "engine 1.5.0",
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


# Every scenario's score is the minimum over its cases of (survival * tracking),
# and the two factors printed beside it are that one worst-product case's own.
# The per-case floors are computed separately, because a case can carry a good
# product and still fail a factor floor: survival .90 * tracking .99 = .891 beats
# survival .96 * tracking .71 = .6816, so the .90 case is not the worst product
# and its survival never reached the promotion gate.  Promotion asks "is this the
# policy we submit", which is an all-case question, so it reads the floors.
SCENARIO_FLOOR_KEYS = ("survival_proxy_min_any_case", "tracking_proxy_min_any_case")


def _unit_proxy(value: Any) -> bool:
    """True only for a real, finite number inside [0, 1].

    ``is not None`` was the whole test until the round-5 audit found the hole:
    NaN is not None, and ``nan < 0.95`` is False, so a NaN floor cleared the
    promotion gate without ever being compared to it.  Presence is not a value.
    A proxy that is not a finite number in [0, 1] is a measurement fault, and a
    bool is not a proxy however cleanly it compares.
    """
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0.0 <= float(value) <= 1.0)


def _non_negative_number(value: Any) -> bool:
    """True only for a real, finite, non-negative number."""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and float(value) >= 0.0)


def scenario_floor_problems(scenarios: dict[str, Any]) -> list[str]:
    """Name every per-case floor that is missing or is not a usable number.

    Absence is not agreement, and neither is NaN.  A report whose floors cannot
    be compared to the gate cannot answer the all-case question, so it is unfit
    to support a promotion -- that is a measurement fault, not a performance
    failure, and it must not be silently read as the worst-product case's own
    factors nor waved through by a comparison that quietly evaluates False.
    """
    return sorted(
        "%s.%s=%r" % (key, field, item.get(field))
        for key, item in scenarios.items()
        for field in SCENARIO_FLOOR_KEYS
        if not _unit_proxy(item.get(field))
    )


def scenario_floors(scenarios: dict[str, Any]) -> list[str]:
    """Return the scenarios whose per-case floors cannot be read, if any."""
    return sorted({problem.split(".", 1)[0] for problem in scenario_floor_problems(scenarios)})


def representative_eligibility(candidate: dict[str, Any]) -> list[str]:
    """Return why this arm's own measurement cannot support a promotion, if it cannot.

    tier1_decision refused unusable measurement from engine 1.5.1 on, but this
    path never looked: an arm with no fingerprint, a retired G6 metric and large
    enough synthetic numbers returned INTERNAL_REPRESENTATIVE_PROMOTION_PASS.
    Promotion is the strictest reading in the engine and had the weakest guard.
    """
    blocking = [f"candidate_{fault}" for fault in instrument_unusable(candidate)]
    # A legacy tolerance is a screening convenience, never a promotion ground.
    # The tolerated arm is missing the field that states its own measurement
    # contract; that is tolerable while ranking two arms against each other, and
    # not tolerable when the answer is "this policy is the one we submit".
    blocking += [
        "candidate_" + note
        for note in instrument_notes(candidate)
        if note.startswith(LEGACY_TOLERANCE_PREFIX)
    ]
    if candidate.get("status") in INADMISSIBLE_ARM_STATUS:
        blocking.append(f"candidate_measurement_{candidate['status'].lower()}")
    elif candidate.get("legacy_recovery_cases"):
        blocking.append("candidate_g6_scored_on_legacy_recovery_rate")
    if candidate.get("locomotion", {}).get("verdict") == "POLICY_DOES_NOT_LOCOMOTE":
        blocking.append("candidate_does_not_locomote")
    floor_problems = scenario_floor_problems(candidate.get("scenarios", {}))
    if floor_problems:
        blocking.append("candidate_scenario_case_floors_unusable:" + ",".join(floor_problems))
    # The total is consumed by the promotion gate too, and NaN loses every
    # comparison it is put in, so it would read as a performance failure rather
    # than as the unmeasured figure it is.
    if not _non_negative_number(candidate.get("simulation_points_70")):
        blocking.append("candidate_simulation_points_70_unusable:%r"
                        % (candidate.get("simulation_points_70"),))
    return blocking


def representative_decision(candidate: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    blocking = representative_eligibility(candidate)
    if blocking:
        return {
            "schema_version": 4,
            "status": "INTERNAL_MEASUREMENT_INVALID",
            "blocking_reasons": blocking,
            "promotion_published": False,
            "promotion_note": "the arm's own measurement is not admissible; no promotion verdict exists",
            "candidate_points_70": None,
            "candidate_locomotion": candidate.get("locomotion"),
            "instrument_candidate": candidate.get("instrument"),
            "gates": gates,
            "scenario_stability_gates_ok": None,
            "scenario_stability_gate_reading": "min_over_all_cases_of_each_factor",
            "scenario_floor_failures": None,
            "scenario_floor_shortfalls": None,
            "scenario_worst_product_factor_failures": None,
            "required_seeds_complete": None,
            "failure_reasons": [],
            "instrument_notes": {"candidate": instrument_notes(candidate)},
            "candidate_diagnostics": _arm_diagnostics(candidate),
            "official_result": "OFFICIAL_RESULT_UNMEASURED",
        }
    points_ok = candidate.get("simulation_points_70", 0.0) >= gates["minimum_points_70"]
    scenarios = candidate.get("scenarios", {})
    # Every floor reaching this line was checked by representative_eligibility
    # to be a finite number in [0, 1], so this comparison decides performance
    # and nothing else.  Each shortfall is named with the value and the
    # threshold it missed, so the scenario to re-measure is not a guess.
    floor_failures = sorted(
        key
        for key, item in scenarios.items()
        if item["survival_proxy_min_any_case"] < gates["required_survival_proxy"]
        or item["tracking_proxy_min_any_case"] < gates["required_tracking_proxy"]
    )
    floor_shortfalls = sorted(
        "%s.%s=%r<%r" % (key, field, item[field], threshold)
        for key, item in scenarios.items()
        for field, threshold in (
            ("survival_proxy_min_any_case", gates["required_survival_proxy"]),
            ("tracking_proxy_min_any_case", gates["required_tracking_proxy"]),
        )
        if item[field] < threshold
    )
    gates_ok = len(scenarios) == 7 and not floor_failures
    seeds_ok = sorted(candidate.get("seed_fractions", {})) == ["101", "202", "303"]
    reasons: list[str] = []
    if not points_ok:
        reasons.append("simulation_proxy_below_minimum")
    if not gates_ok:
        reasons.append("one_or_more_scenario_stability_gates_failed")
    if not seeds_ok:
        reasons.append("required_seed_set_incomplete")
    if candidate.get("locomotion", {}).get("verdict") == "POLICY_DOES_NOT_LOCOMOTE":
        reasons.append("candidate_does_not_locomote")
    return {
        "schema_version": 4,
        "status": "INTERNAL_REPRESENTATIVE_PROMOTION_PASS" if not reasons else "INTERNAL_REPRESENTATIVE_PROMOTION_FAIL",
        "blocking_reasons": [],
        "promotion_published": True,
        "candidate_points_70": candidate.get("simulation_points_70"),
        "candidate_locomotion": candidate.get("locomotion"),
        "instrument_candidate": candidate.get("instrument"),
        "instrument_notes": {"candidate": instrument_notes(candidate)},
        "gates": gates,
        "scenario_stability_gates_ok": gates_ok,
        "scenario_stability_gate_reading": "min_over_all_cases_of_each_factor",
        "scenario_floor_failures": floor_failures,
        "scenario_floor_shortfalls": floor_shortfalls,
        "scenario_worst_product_factor_failures": sorted(
            key
            for key, item in scenarios.items()
            if item.get("survival_proxy", 0.0) < gates["required_survival_proxy"]
            or item.get("tracking_proxy", 0.0) < gates["required_tracking_proxy"]
        ),
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
