"""Build a pre-registered Default-01 vs single-variable candidate report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from go2_fixed_eval_report import _write_policy, build_policy


BASELINE_MODEL_SHA = "99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676"
BASELINE_ENV_SHA = "4d1d294b63dafeceb223fb48226cbe6a533157bc54f97ce486f644bd1bda262c"
G5_MIN_PROXY_DELTA = 0.03
MIN_SURVIVAL_DELTA = -0.02
MIN_TRACKING_DELTA = -0.05
MIN_SEED_DELTA = -0.02


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    identity = baseline.get("identity", {})
    if identity.get("model_sha256") != BASELINE_MODEL_SHA:
        raise RuntimeError("frozen Default-01 model identity mismatch")
    if identity.get("env_sha256") != BASELINE_ENV_SHA:
        raise RuntimeError("frozen Default-01 env identity mismatch")

    common = sorted(set(baseline.get("scenarios", {})) & set(candidate.get("scenarios", {})))
    per_scenario = {
        scenario: {
            "baseline": baseline["scenarios"][scenario],
            "candidate": candidate["scenarios"][scenario],
            "delta_survival": candidate["scenarios"][scenario]["survival_proxy"]
            - baseline["scenarios"][scenario]["survival_proxy"],
            "delta_tracking": candidate["scenarios"][scenario]["tracking_proxy"]
            - baseline["scenarios"][scenario]["tracking_proxy"],
            "delta_proxy": candidate["scenarios"][scenario]["scenario_proxy"]
            - baseline["scenarios"][scenario]["scenario_proxy"],
        }
        for scenario in common
    }
    seeds = sorted(set(baseline.get("seed_fractions", {})) | set(candidate.get("seed_fractions", {})))
    seed_delta = {
        seed: candidate.get("seed_fractions", {}).get(seed, 0.0)
        - baseline.get("seed_fractions", {}).get(seed, 0.0)
        for seed in seeds
    }
    complete = (
        baseline.get("observed_telemetry_count") == baseline.get("expected_telemetry_count") == 69
        and candidate.get("observed_telemetry_count") == candidate.get("expected_telemetry_count") == 69
        and len(common) == 7
    )
    gates = {
        "telemetry_complete": complete,
        "g5_proxy_delta_at_least_plus_0_03": per_scenario.get("G5", {}).get("delta_proxy", -1.0)
        >= G5_MIN_PROXY_DELTA,
        "g5_survival_delta_at_least_minus_0_02": per_scenario.get("G5", {}).get("delta_survival", -1.0)
        >= MIN_SURVIVAL_DELTA,
        "all_survival_deltas_at_least_minus_0_02": len(common) == 7
        and all(item["delta_survival"] >= MIN_SURVIVAL_DELTA for item in per_scenario.values()),
        "all_tracking_deltas_at_least_minus_0_05": len(common) == 7
        and all(item["delta_tracking"] >= MIN_TRACKING_DELTA for item in per_scenario.values()),
        "all_seed_deltas_at_least_minus_0_02": len(seed_delta) == 3
        and all(value >= MIN_SEED_DELTA for value in seed_delta.values()),
    }
    if not complete:
        status = "INTERNAL_GATE_INCONCLUSIVE"
    elif all(gates.values()):
        status = "INTERNAL_SCREEN_QUANTITATIVE_PASS_VIDEO_REVIEW_PENDING"
    else:
        status = "INTERNAL_SCREEN_FAIL"
    return {
        "schema_version": 1,
        "official_result": "OFFICIAL_RESULT_UNMEASURED",
        "experiment": "Default-01 vs feet_air_time_0.20-only candidate",
        "training_seed": 42,
        "baseline_model_sha256": BASELINE_MODEL_SHA,
        "candidate_model_sha256": candidate.get("identity", {}).get("model_sha256"),
        "baseline_simulation_points_70": baseline.get("simulation_points_70"),
        "candidate_simulation_points_70": candidate.get("simulation_points_70"),
        "candidate_minus_baseline_fraction": candidate.get("simulation_fraction", 0.0)
        - baseline.get("simulation_fraction", 0.0),
        "per_scenario": per_scenario,
        "per_seed_delta": seed_delta,
        "pre_registered_gates": gates,
        "quantitative_status": status,
        "video_status": "VIDEO_UNKNOWN",
        "promotion_rule": "quantitative pass plus VIDEO_OBSERVED without increased adverse behavior; independent training seed still required",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--baseline-report", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    baseline = load(args.baseline_report)
    identity = load(args.candidate_root / "identity.json")
    candidate = build_policy(args.candidate_root, args.registry, identity)
    _write_policy(args.candidate_root, candidate)
    result = compare(baseline, candidate)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "GO2_FEET_AIR_TIME_020_SCREENING_REPORT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# Go2 feet_air_time=0.20 single-variable screening",
        "",
        f"- quantitative status: {result['quantitative_status']}",
        f"- baseline proxy: {result['baseline_simulation_points_70']:.4f}/70",
        f"- candidate proxy: {result['candidate_simulation_points_70']:.4f}/70",
        f"- candidate minus baseline: {result['candidate_minus_baseline_fraction'] * 70:+.4f}/70",
        "- video status: VIDEO_UNKNOWN",
        "- official result: OFFICIAL_RESULT_UNMEASURED",
        "",
        "| gate | result |",
        "|---|---|",
    ]
    lines.extend(f"| {name} | {value} |" for name, value in result["pre_registered_gates"].items())
    (args.out / "GO2_FEET_AIR_TIME_020_SCREENING_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
