"""Apply an H1 observed ratio as a non-decision Go2 sensitivity, not a predictor."""
import argparse
import json
import math
from pathlib import Path


def build_sensitivity(comparison, calibration):
    if comparison.get("evidence") != "INTERNAL_MEASUREMENT_OK":
        raise ValueError("Go2 measurement must be verified before projection")
    ratio = calibration["totals"]["observed_ratio_official_over_internal"]
    if not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio < 0:
        raise ValueError("invalid observed ratio")
    rows = []
    for row in comparison["scenarios"]:
        baseline, candidate = row["baseline_points"], row["candidate_points"]
        if not all(math.isfinite(x) and 0 <= x <= 70 * row["weight"] for x in (baseline, candidate)):
            raise ValueError("invalid raw scenario points")
        rows.append({"scenario": row["scenario"], "raw_baseline": baseline,
                     "raw_candidate": candidate, "raw_delta": candidate - baseline,
                     "sensitivity_baseline": baseline * ratio,
                     "sensitivity_candidate": candidate * ratio,
                     "sensitivity_delta": (candidate - baseline) * ratio})
    return {"schema_version": 1, "label": "H1_RATIO_STRESS_SENSITIVITY",
            "validated_prediction": False, "used_for_decisions": False,
            "official_result": "UNMEASURED", "raw_gates_changed": False,
            "h1_submission_identity": calibration["comparison_eligibility"],
            "multiplier": ratio, "scenarios": rows,
            "totals": {key: sum(r[key] for r in rows) for key in
                       ("raw_baseline", "raw_candidate", "raw_delta",
                        "sensitivity_baseline", "sensitivity_candidate", "sensitivity_delta")},
            "warning": "H1 single-observation transfer is unvalidated; not a confidence bound or Go2 official prediction."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_sensitivity(json.loads(args.comparison.read_text(encoding="utf-8")),
                               json.loads(args.calibration.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"]))


if __name__ == "__main__":
    main()
