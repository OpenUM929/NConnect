#!/usr/bin/env python3
"""Compare the frozen H1 internal proxy with one transcribed official result.

This tool deliberately does not replace the internal scoring formula.  It emits
an observational calibration artifact whose coefficients remain disabled until
the evaluated submission identity is independently matched and out-of-sample
official results exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCENARIOS = ("H1", "H2", "H3", "H4", "H5", "H6", "H7")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def build_calibration(internal_path: Path, official_path: Path) -> dict[str, Any]:
    internal = json.loads(internal_path.read_text(encoding="utf-8"))
    official = json.loads(official_path.read_text(encoding="utf-8"))
    validation = internal["independent_validation"]
    internal_scenarios = validation["scenarios"]
    official_scenarios = official["scenarios"]

    if set(internal_scenarios) != set(SCENARIOS):
        raise ValueError("internal report must contain exactly H1-H7")
    if set(official_scenarios) != set(SCENARIOS):
        raise ValueError("official transcription must contain exactly H1-H7")

    rows: dict[str, Any] = {}
    internal_total = 0.0
    official_total = 0.0
    maximum_total = 0.0
    for scenario in SCENARIOS:
        internal_row = internal_scenarios[scenario]
        official_row = official_scenarios[scenario]
        internal_fraction = _finite_number(
            internal_row["worst_scenario_proxy"],
            f"{scenario}.worst_scenario_proxy",
        )
        weight = _finite_number(internal_row["weight"], f"{scenario}.weight")
        received = _finite_number(official_row["received_points"], f"{scenario}.received_points")
        maximum = _finite_number(official_row["maximum_points"], f"{scenario}.maximum_points")
        if not 0.0 <= internal_fraction <= 1.0:
            raise ValueError(f"{scenario} internal proxy must be in [0, 1]")
        if maximum <= 0.0 or not 0.0 <= received <= maximum:
            raise ValueError(f"{scenario} official points are out of range")
        expected_maximum = 70.0 * weight
        if not math.isclose(maximum, expected_maximum, abs_tol=1e-9):
            raise ValueError(
                f"{scenario} maximum {maximum} does not match weight-derived {expected_maximum}"
            )

        official_fraction = received / maximum
        internal_points = internal_fraction * maximum
        signed_error_points = internal_points - received
        multiplier = official_fraction / internal_fraction if internal_fraction else None
        rows[scenario] = {
            "weight": weight,
            "maximum_points": maximum,
            "internal_fraction_original": internal_fraction,
            "internal_points_original": internal_points,
            "official_fraction_transcribed": official_fraction,
            "official_points_transcribed": received,
            "internal_minus_official_points": signed_error_points,
            "absolute_error_points": abs(signed_error_points),
            "observed_ratio_official_over_internal": multiplier,
        }
        internal_total += internal_points
        official_total += received
        maximum_total += maximum

    declared_total = _finite_number(official["total"]["received_points"], "total.received_points")
    declared_maximum = _finite_number(official["total"]["maximum_points"], "total.maximum_points")
    if not math.isclose(official_total, declared_total, abs_tol=1e-9):
        raise ValueError("official scenario points do not sum to declared total")
    if not math.isclose(maximum_total, declared_maximum, abs_tol=1e-9):
        raise ValueError("official scenario maxima do not sum to declared maximum")
    reported_internal_total = _finite_number(
        validation["simulation_points_70"], "independent_validation.simulation_points_70"
    )
    if not math.isclose(internal_total, reported_internal_total, abs_tol=1e-9):
        raise ValueError("internal scenario points do not sum to report total")

    identity_status = official["submission_identity"]["match_status"]
    comparable = identity_status == "MATCHED"
    global_multiplier = official_total / internal_total
    for scenario in SCENARIOS:
        rows[scenario]["adjusted_reference_points_global_ratio"] = (
            rows[scenario]["internal_points_original"] * global_multiplier
        )
    fraction_errors = [
        rows[scenario]["internal_fraction_original"]
        - rows[scenario]["official_fraction_transcribed"]
        for scenario in SCENARIOS
    ]
    internal_loss_ranking = sorted(
        SCENARIOS, key=lambda scenario: rows[scenario]["internal_fraction_original"]
    )
    official_loss_ranking = sorted(
        SCENARIOS, key=lambda scenario: rows[scenario]["official_fraction_transcribed"]
    )
    return {
        "schema_version": 1,
        "artifact_kind": "H1_OFFICIAL_OBSERVATION_CALIBRATION",
        "evidence": {
            "official_result_layer": "OFFICIAL_RESULT_USER_TRANSCRIPTION",
            "internal_result_layer": "HISTORICAL_INTERNAL_GATE_PASS",
            "current_posture_scope": {
                "status": "PARTIAL",
                "verified_scenarios": ["H1", "H2", "H3", "H4", "H7"],
                "posture_unmeasured_scenarios": ["H5", "H6"],
                "effect": "The 65.73/70 raw proxy is not a current all-scenario posture-verified score.",
            },
            "official_input_path": official_path.as_posix(),
            "official_input_sha256": sha256(official_path),
            "internal_input_path": internal_path.as_posix(),
            "internal_input_sha256": sha256(internal_path),
        },
        "comparison_eligibility": {
            "submission_identity_match_status": identity_status,
            "status": "DIRECTLY_COMPARABLE" if comparable else "CONDITIONAL_ONLY_IDENTITY_UNCONFIRMED",
            "reason": official["submission_identity"]["reason"],
        },
        "totals": {
            "internal_points_original": internal_total,
            "official_points_transcribed": official_total,
            "maximum_points": maximum_total,
            "internal_minus_official_points": internal_total - official_total,
            "absolute_error_points": abs(internal_total - official_total),
            "observed_ratio_official_over_internal": global_multiplier,
            "adjusted_reference_points_global_ratio": internal_total * global_multiplier,
        },
        "observed_precision_diagnostics": {
            "scenario_fraction_signed_bias_mean": sum(fraction_errors) / len(fraction_errors),
            "scenario_fraction_mae": sum(abs(value) for value in fraction_errors) / len(fraction_errors),
            "scenario_fraction_rmse": math.sqrt(
                sum(value * value for value in fraction_errors) / len(fraction_errors)
            ),
            "maximum_fraction_error_scenario": max(
                SCENARIOS,
                key=lambda scenario: abs(
                    rows[scenario]["internal_fraction_original"]
                    - rows[scenario]["official_fraction_transcribed"]
                ),
            ),
            "internal_weakest_to_strongest": internal_loss_ranking,
            "official_weakest_to_strongest": official_loss_ranking,
            "weakest_scenario_agrees": internal_loss_ranking[0] == official_loss_ranking[0],
        },
        "scenarios": rows,
        "calibration_review": {
            "original_proxy_changed": False,
            "exploratory_global_multiplier": global_multiplier,
            "exploratory_per_scenario_multipliers": {
                scenario: rows[scenario]["observed_ratio_official_over_internal"]
                for scenario in SCENARIOS
            },
            "coefficients_enabled_for_prediction": False,
            "validated_prediction": False,
            "sample_count_official_submissions": 1,
            "out_of_sample_validation_count": 0,
            "uncertainty_interval": None,
            "same_sample_fit_warning": (
                "Applying these coefficients to the source observation reproduces it by construction; "
                "that is calibration fit, not predictive validation."
            ),
            "recommended_reporting_policy": {
                "raw_internal_proxy": "retain as the decision and gate input",
                "h1_global_ratio_sensitivity": "show alongside raw and official; label non-validated",
                "h1_per_scenario_ratios": "diagnostic only; do not use for tuning priority",
            },
        },
        "cross_robot_transfer": {
            "apply_h1_coefficients_to_go2": False,
            "default_enabled": False,
            "reason": "H1 and Go2 use different bodies, scenarios, commands, terrains, and evaluator implementations.",
            "allowed_use": "disabled sensitivity projection only, never Go2 score evidence",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    totals = result["totals"]
    lines = [
        "# H1 official-observation calibration",
        "",
        f"- Comparison: `{result['comparison_eligibility']['status']}`",
        f"- Internal raw: **{totals['internal_points_original']:.4f}/70**",
        f"- Official transcription: **{totals['official_points_transcribed']:.2f}/70**",
        f"- Conditional difference: **{totals['internal_minus_official_points']:+.4f}**",
        f"- Observed global ratio: **{totals['observed_ratio_official_over_internal']:.9f}**",
        "- Prediction coefficients: **DISABLED / NOT VALIDATED**",
        "- H5/H6 posture status: **POSTURE_UNMEASURED**",
        "",
        "| Scenario | Internal raw | Global-ratio reference | Official | Conditional difference | Observed ratio |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for scenario in SCENARIOS:
        row = result["scenarios"][scenario]
        lines.append(
            f"| {scenario} | {row['internal_points_original']:.4f}/{row['maximum_points']:g} "
            f"| {row['adjusted_reference_points_global_ratio']:.4f}/{row['maximum_points']:g} "
            f"| {row['official_points_transcribed']:.2f}/{row['maximum_points']:g} "
            f"| {row['internal_minus_official_points']:+.4f} "
            f"| {row['observed_ratio_official_over_internal']:.6f} |"
        )
    lines.extend(
        [
            "",
            "> Differences assume the official submission is Run06; that identity is not yet confirmed.",
            "> These ratios describe one source observation. Same-sample reproduction is not predictive validation.",
            "> H1 coefficients are not transferable Go2 score evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--internal", type=Path, required=True)
    parser.add_argument("--official", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    result = build_calibration(args.internal, args.official)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({
        "status": "OK",
        "out": str(args.out),
        "markdown_out": str(args.markdown_out) if args.markdown_out else None,
        "totals": result["totals"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
