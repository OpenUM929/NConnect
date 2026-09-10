"""Aggregate Go2 G1-G7 telemetry and build a paired internal comparison."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


# Fallback only.  The authoritative value is the registry's
# score.tracking_proxy_std, which must mirror the env's
# rewards.track_lin_vel_xy_exp.params.std.  Engine 1.5.0 stopped hard-coding it
# silently because a reviewer could not tell whether a scored number used the env
# value or this constant.
TRACKING_STD = 0.5


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _track(rmse: float | None, std: float = TRACKING_STD) -> float | None:
    return None if rmse is None else math.exp(-((float(rmse) / float(std)) ** 2))


def _case_proxy(case_id: str, summary: dict[str, Any], std: float = TRACKING_STD) -> dict[str, Any]:
    survival = summary.get("survival_proxy")
    xy = _track(summary.get("tracking_xy_rmse"), std)
    yaw = _track(summary.get("tracking_yaw_rmse"), std)
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
    recovery_metric = None
    if case_id.startswith("push_"):
        tracking = _track(summary.get("post_push_tracking_xy_rmse"), std)
        block = summary.get("recovery") or {}
        # go2_eval_telemetry.py:286-291 states in its own words that
        # ``recovery_rate`` is satisfied by a robot lying on the ground that never
        # moved, and that ``recovery_rate_upright`` is the figure that may be
        # quoted as recovery.  Engine 1.5.0 scores the upright figure.  The legacy
        # field is still read when re-scoring pre-v2 artifacts, but the case is
        # tagged and the report status is downgraded so it cannot pass silently.
        recovery = block.get("recovery_rate_upright")
        recovery_metric = "recovery_rate_upright"
        if recovery is None:
            recovery = block.get("recovery_rate")
            recovery_metric = "legacy_recovery_rate" if recovery is not None else None
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
        "recovery_metric": recovery_metric,
    }


def build_policy(root: Path, registry_path: Path, identity: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = _load(registry_path)
    std = float(registry["score"].get("tracking_proxy_std", TRACKING_STD))
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
            "proxy": _case_proxy(case_id, summary, std),
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
        # Aggregation order is now stated, not implied.  The scored figure is
        # min over cases of (survival * tracking), and the two factors reported
        # beside it are that same worst case's own factors, so proxy is exactly
        # survival * tracking in the report a reviewer reads.  Engine 1.4.0 and
        # earlier reported three independent minimums, which generally come from
        # three different cases and therefore do not multiply out.
        survival = worst["proxy"]["survival_proxy"]
        tracking = worst["proxy"]["tracking_proxy"]
        proxy = worst["proxy"]["scenario_proxy"]
        # The stability gate is a per-case floor, so it keeps using the minimum
        # over all cases rather than the worst product's factors.
        # The floor is named as well as valued: a promotion refused on a floor
        # has to say which case and seed to re-measure, and the scenario id
        # alone does not answer that.
        survival_case = min(valid, key=lambda item: item["proxy"]["survival_proxy"])
        tracking_case = min(valid, key=lambda item: item["proxy"]["tracking_proxy"])
        survival_floor = survival_case["proxy"]["survival_proxy"]
        tracking_floor = tracking_case["proxy"]["tracking_proxy"]
        scenarios[scenario["id"]] = {
            "name": scenario["name"],
            "weight": scenario["weight"],
            "survival_proxy": survival,
            "tracking_proxy": tracking,
            "scenario_proxy": proxy,
            "aggregation": "min_over_cases_of(survival_proxy*tracking_proxy); factors are that case's own",
            "survival_proxy_min_any_case": survival_floor,
            "tracking_proxy_min_any_case": tracking_floor,
            "survival_floor_case": {"case_id": survival_case["case_id"],
                                    "seed": survival_case["seed"]},
            "tracking_floor_case": {"case_id": tracking_case["case_id"],
                                    "seed": tracking_case["seed"]},
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
                if survival_floor >= gates["minimum_survival_proxy_each"]
                and tracking_floor >= gates["minimum_tracking_proxy_each"]
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

    # Instrument fingerprint.  Two policies may only be compared when every case
    # of both was measured by the same survival definition and the same posture
    # gate parameters.  Recording it here is what lets tier1_decision refuse an
    # asymmetric pair instead of publishing a delta between two different rulers.
    instrument = {
        "tracking_proxy_std": std,
        "survival_proxy_sources": sorted(
            {str(item["raw"].get("survival_proxy_source")) for item in cases.values()}
        ),
        "telemetry_schema_versions": sorted(
            {str(item["raw"].get("schema_version")) for item in cases.values()}
        ),
        "posture_gate_params": sorted(
            {
                json.dumps(item["raw"].get("posture_gate"), sort_keys=True)
                for item in cases.values()
            }
        ),
        "measurement_contracts": sorted(
            {str(item["raw"].get("measurement_contract")) for item in cases.values()}
        ),
    }

    # Locomotion floor.  A policy that stands still is never terminated, so the
    # termination-only survival definition scores it 1.0 on every case; that is
    # how a non-walking checkpoint was able to serve as a frozen baseline.  A case
    # that holds under 0.10 m/s while its own tracking RMSE is at least 0.30 is a
    # robot ignoring a non-trivial command, and is reported as such.
    stationary = sorted(
        key
        for key, item in cases.items()
        if (item["raw"].get("speed_xy_mean") or 0.0) < 0.10
        and (item["raw"].get("tracking_xy_rmse") or 0.0) >= 0.30
    )
    locomotes = not (cases and len(stationary) * 2 >= len(cases))
    locomotion = {
        "stationary_case_count": len(stationary),
        "observed_case_count": len(cases),
        "stationary_cases": stationary,
        "criterion": "speed_xy_mean < 0.10 m/s and tracking_xy_rmse >= 0.30",
        "verdict": "POLICY_LOCOMOTES" if locomotes else "POLICY_DOES_NOT_LOCOMOTE",
    }

    legacy_recovery = sorted(
        key
        for key, item in cases.items()
        if item["proxy"].get("recovery_metric") == "legacy_recovery_rate"
    )

    reasons: list[str] = []
    if missing or len(scenarios) != len(registry["scenarios"]):
        reasons.append("telemetry_incomplete")
        status = "SELF_ASSESSMENT_INCOMPLETE"
    elif legacy_recovery:
        reasons.append("g6_scored_on_legacy_recovery_rate")
        status = "SELF_ASSESSMENT_LEGACY_METRIC"
    elif not locomotes:
        reasons.append("policy_does_not_locomote")
        status = "INTERNAL_GATE_FAIL"
    elif failed or fraction < gates["minimum_weighted_simulation_proxy"]:
        reasons.append("scenario_or_weighted_total_gate_failed")
        status = "INTERNAL_GATE_FAIL"
    else:
        status = "INTERNAL_GATE_PASS"
    return {
        "schema_version": 2,
        "official_result": False,
        "method": "Go2 internal proxy v2; min over cases of survival*tracking, posture-gated survival",
        "identity": identity or {},
        "instrument": instrument,
        "locomotion": locomotion,
        "legacy_recovery_cases": legacy_recovery,
        "status_reasons": reasons,
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


INSTRUMENT_KEYS = (
    "tracking_proxy_std",
    "survival_proxy_sources",
    "telemetry_schema_versions",
    "posture_gate_params",
    "measurement_contracts",
)

# Every case of an admissible arm must carry this and nothing else.  A fingerprint
# listing "None", "POSTURE_UNMEASURED" or a mix of sources is not evidence that the
# two arms agree -- it is evidence that at least one of them was not measured.
REQUIRED_SURVIVAL_SOURCES = ["posture_gate_v2"]

# The fingerprint is built with str() and json.dumps(), so a case that recorded
# nothing arrives as the *string* "None" or "null" -- non-empty, length one, and
# therefore indistinguishable from a real reading to a truthiness test.  These are
# absences wearing the shape of evidence.
NULL_PLACEHOLDERS = {"", "None", "null", "NULL", "nan", "NaN"}


# measurement_contract was introduced by engine 1.5.1.  These are the telemetry
# schema versions written before it existed, so a case carrying one of them can be
# missing the contract string for a reason other than a hole in its evidence.  The
# list is explicit and closed: "the version is present and non-null" admitted
# schema 4, 999 and "banana" -- schemas that either must carry a contract or do not
# exist -- and so was not a legacy rule at all.
LEGACY_CONTRACTLESS_SCHEMAS = ("2",)

# What "posture_gate_v2" means is these four thresholds.  A fingerprint that names
# the gate but records "{}" for its parameters has not pinned the ruler, so it may
# not use the legacy tolerance either.
REQUIRED_POSTURE_GATE_KEYS = ("tilt_cos_max", "height_rel_min_m", "hold_s", "grace_s")


def _posture_params_complete(fingerprint: dict[str, Any]) -> bool:
    """Return whether one complete set of posture-gate thresholds was recorded."""
    values = fingerprint.get("posture_gate_params")
    if not values or len(values) != 1:
        return False
    raw = str(values[0]).strip()
    if raw in NULL_PLACEHOLDERS:
        return False
    try:
        params = json.loads(raw)
    except (TypeError, ValueError):
        return False
    if not isinstance(params, dict):
        return False
    for key in REQUIRED_POSTURE_GATE_KEYS:
        value = params.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(float(value)):
            return False
    return True


def _schema_pins_contract(fingerprint: dict[str, Any]) -> bool:
    """Return whether a known pre-contract schema names the ruler by itself."""
    versions = fingerprint.get("telemetry_schema_versions")
    if not versions or len(versions) != 1:
        return False
    return (
        str(versions[0]).strip() in LEGACY_CONTRACTLESS_SCHEMAS
        and _posture_params_complete(fingerprint)
    )


def instrument_notes(policy: dict[str, Any]) -> list[str]:
    """Return non-blocking observations about an arm's fingerprint.

    A note is something a reader must be told and a screening gate must not act
    on.  The pre-1.5.1 contract absence is the only one so far: it is tolerated
    because a known legacy schema plus a complete posture-gate parameter set
    carries the same information, and it is reported so that the toleration is
    never invisible.  A promotion may not rest on a tolerated arm at all -- see
    representative_eligibility.
    """
    fingerprint = policy.get("instrument") or {}
    notes: list[str] = []
    contracts = fingerprint.get("measurement_contracts")
    if (
        contracts
        and any(str(item).strip() in NULL_PLACEHOLDERS for item in contracts)
        and _schema_pins_contract(fingerprint)
    ):
        notes.append(
            "legacy_measurement_contract_absent_schema_"
            + str(fingerprint["telemetry_schema_versions"][0])
        )
    return notes


LEGACY_TOLERANCE_PREFIX = "legacy_measurement_contract_absent_schema_"


def instrument_unusable(policy: dict[str, Any]) -> list[str]:
    """Return why this arm's fingerprint cannot support a comparison, if it cannot.

    Absence is not agreement.  Engine 1.5.0 compared the two fingerprints field by
    field, so two arms that both recorded nothing compared equal and their delta was
    published as if the rulers had been checked.
    """
    fingerprint = policy.get("instrument")
    if not fingerprint:
        return ["instrument_absent"]
    faults = [key for key in INSTRUMENT_KEYS if not fingerprint.get(key)]
    sources = fingerprint.get("survival_proxy_sources")
    if sources and sources != REQUIRED_SURVIVAL_SOURCES:
        faults.append("survival_proxy_sources_not_posture_gate_v2:" + ",".join(sources))
    for key in ("telemetry_schema_versions", "posture_gate_params", "measurement_contracts"):
        value = fingerprint.get(key)
        if not value:
            continue
        if len(value) != 1:
            faults.append(f"{key}_mixed_within_arm")
        if not any(str(item).strip() in NULL_PLACEHOLDERS for item in value):
            continue
        if key == "measurement_contracts" and _schema_pins_contract(fingerprint):
            # measurement_contract was added in engine 1.5.1, so every case
            # measured before it reports "None".  For a schema on the closed
            # legacy list, whose posture thresholds were all recorded, that
            # absence is not a hole in the evidence: the contract string is
            # derived from the schema version, which is why the version was
            # bumped in the same change.  Recorded as a note (see
            # instrument_notes) rather than accepted silently.  A schema off the
            # list -- including a modern one that must carry a contract -- is
            # still fatal, and so is an empty posture-gate parameter set.
            continue
        faults.append(f"{key}_null_placeholder")
    std = fingerprint.get("tracking_proxy_std")
    if std is not None and not isinstance(std, bool) and isinstance(std, (int, float)):
        if not math.isfinite(std) or std <= 0.0:
            faults.append("tracking_proxy_std_not_positive")
    return faults


def instrument_mismatch(baseline: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    """Return the fingerprint fields on which the two arms disagree.

    A non-empty result means the two policies were measured by different rulers,
    so their delta has no meaning and must not be turned into a verdict.  An arm
    whose own fingerprint is absent or unusable is reported here too, because
    "neither side recorded a ruler" must never read as "both used the same ruler".
    """
    # Report both arms.  Returning on the first faulty arm hid the other one's
    # independent defects behind a single prefix, so a reader could not tell a
    # one-sided problem from a two-sided one.
    unusable = [
        f"{label}_{fault}"
        for label, policy in (("baseline", baseline), ("candidate", candidate))
        for fault in instrument_unusable(policy)
    ]
    if unusable:
        return unusable
    base = baseline["instrument"]
    cand = candidate["instrument"]
    return [key for key in INSTRUMENT_KEYS if base.get(key) != cand.get(key)]


# An arm whose own self-assessment is incomplete or was scored on the retired
# recovery metric cannot stand on either side of a comparison.
INADMISSIBLE_ARM_STATUS = ("SELF_ASSESSMENT_INCOMPLETE", "SELF_ASSESSMENT_LEGACY_METRIC")


def pair_blockers(default: dict[str, Any], pilot: dict[str, Any]) -> list[str]:
    """Return why this pair may not be compared at all, if it may not."""
    blocking: list[str] = []
    mismatch = instrument_mismatch(default, pilot)
    if mismatch:
        blocking.append("instrument_fingerprint_asymmetric:" + ",".join(mismatch))
    for label, arm in (("default", default), ("pilot", pilot)):
        if arm.get("status") in INADMISSIBLE_ARM_STATUS:
            blocking.append(f"{label}_measurement_{arm['status'].lower()}")
        elif arm.get("legacy_recovery_cases"):
            blocking.append(f"{label}_g6_scored_on_legacy_recovery_rate")
    if default.get("locomotion", {}).get("verdict") == "POLICY_DOES_NOT_LOCOMOTE":
        blocking.append("default_does_not_locomote")
    return blocking


def paired(default: dict[str, Any], pilot: dict[str, Any]) -> dict[str, Any]:
    mismatch = instrument_mismatch(default, pilot)
    blocking = pair_blockers(default, pilot)
    if blocking:
        # Engine 1.5.1 suppressed the delta in tier1_decision but not here, so the
        # same invalid pair still published pilot_minus_default and a full
        # per-scenario delta table from this path.  A number that must not be read
        # must not be printed; each arm's own figures stay, as diagnostics.
        return {
            "schema_version": 3,
            "official_result": False,
            "comparison_metrics": "reward-independent survival/tracking/completion/recovery only",
            "comparison_published": False,
            "comparison_note": "arms are not on one ruler; no delta exists to report",
            "blocking_reasons": blocking,
            "instrument_mismatch": mismatch,
            "instrument_baseline": default.get("instrument"),
            "instrument_candidate": pilot.get("instrument"),
            "instrument_notes": {
                "baseline": instrument_notes(default),
                "candidate": instrument_notes(pilot),
            },
            "baseline_locomotion": default.get("locomotion"),
            "candidate_locomotion": pilot.get("locomotion"),
            "default": {"status": default["status"], "simulation_fraction": default["simulation_fraction"]},
            "pilot": {"status": pilot["status"], "simulation_fraction": pilot["simulation_fraction"]},
            "pilot_minus_default": None,
            "per_scenario": None,
            "per_seed_delta": None,
            "seed_direction_consistent": None,
            "no_seed_proxy_inversion_below_minus_0_02": None,
            "decision": "INTERNAL_MEASUREMENT_INVALID",
            "video_status": "VIDEO_UNKNOWN",
        }
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
    if default["simulation_fraction"] - pilot["simulation_fraction"] >= 0.03 or (
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
        "schema_version": 3,
        "official_result": False,
        "comparison_metrics": "reward-independent survival/tracking/completion/recovery only",
        "comparison_published": True,
        "blocking_reasons": [],
        "instrument_mismatch": mismatch,
        "instrument_baseline": default.get("instrument"),
        "instrument_candidate": pilot.get("instrument"),
        "instrument_notes": {
            "baseline": instrument_notes(default),
            "candidate": instrument_notes(pilot),
        },
        "baseline_locomotion": default.get("locomotion"),
        "candidate_locomotion": pilot.get("locomotion"),
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
        f"- reasons: {', '.join(report.get('status_reasons') or []) or 'none'}",
        f"- telemetry: {report['observed_telemetry_count']}/{report['expected_telemetry_count']}",
        f"- locomotion: {report.get('locomotion', {}).get('verdict')}"
        f" ({report.get('locomotion', {}).get('stationary_case_count')}"
        f"/{report.get('locomotion', {}).get('observed_case_count')} stationary cases)",
        f"- survival definition: {', '.join(report.get('instrument', {}).get('survival_proxy_sources') or [])}",
        f"- tracking std: {report.get('instrument', {}).get('tracking_proxy_std')}",
        f"- simulation proxy: {report['simulation_points_70']:.3f}/70 (not official)", "",
        "survival and tracking below are the worst-product case's own factors, so"
        " proxy = survival x tracking exactly.", "",
        "| G | survival | tracking | proxy | worst case | gate |", "|---|---:|---:|---:|---|---|",
    ]
    for key, item in report["scenarios"].items():
        worst = item["worst_case"]
        lines.append(f"| {key} | {item['survival_proxy']:.4f} | {item['tracking_proxy']:.4f} | {item['scenario_proxy']:.4f} | {worst['case_id']}@{worst['seed']} | {item['gate']} |")
    lines += ["", "Official evaluator details remain unknown; this is INTERNAL_PROXY_SPEC v2."]
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
