#!/usr/bin/env python3
"""Server-side target-stage gate for the basic-motion pair (G-A031 / G-A032).

The pair runner (server_run_go2_basic_motion_pair.sh) calls this after an arm's
target stage to decide one thing: whether that arm's full stage gets GPU time.
It schedules; it does not judge.  tools/verify_go2_basic_motion_harvest.py reads
every returned harvest again and its verdict is the one of record.

Criterion 1 of plan section 6-1 is read with target_reading, which is defined here
and imported by the local verifier, on the cases the local verifier reads: the
catastrophe case and the target cases the spec declares.  Those cases also carry the
stationary guard in this stage (defect S-4, 2026-09-19): before, only the full stage read
`stationary_guard_scenarios`, so a policy that walked on the flat and crouched elsewhere
passed stage 1 on a single flat case -- that is what G-A038 did.  Each case the run measured is checked
against its own steps.csv with verify_go2_a027_harvest.verify_case.  The stored
A017 arm (G-A027) travels as summary.json files only; the pair builder verifies
those cases in full before packing them and PAIR_SHA256SUMS.txt pins them.

Standard library only; runs from the pair package folder or from the repository.

2026-09-17: a spec with preregistered.rule_version == "fact_rules_v1" also gets
go2_fact_rules.py (each target group has its own floor; the climbed-robot counts of
the stairs cases in this stage have a floor).  The copy the pair, G-A033 and G-A038
ran is kept byte for byte in workspace/training/quadruped/runner_history/.

    python go2_target_gate.py --keep /workspace/_keep/<arm keep> --package /workspace/go2_g_a031 \\
        --stored <pair>/stored_baseline [--out gate.json]

Exit  0 TARGET_PASS         criterion 1 met: run the full stage
     10 FAIL                criterion 1 not met, or a catastrophe decision: the arm ends
     11 REMEASURE_BASELINE  the sentinel disagrees with the stored arm: rerun the
                            target stage with the baseline remeasured
     12 UNDECIDED           a check before the numbers failed: no full stage
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
for _path in (HERE.parent / "workspace" / "training" / "quadruped", HERE):
    if _path.is_dir():
        sys.path.insert(0, str(_path))

import go2_fact_rules as fact  # noqa: E402
import verify_go2_a027_harvest as harvest  # noqa: E402
from go2_fixed_eval_report import _case_proxy  # noqa: E402

TOL = 1e-9
TARGET_DECISION = "TARGET_STAGE_COMPLETE"
CATASTROPHE_DECISIONS = ("CATASTROPHE_STATIONARY", "CATASTROPHE_TRAINING_NONFINITE")
EXIT = {"TARGET_PASS": 0, "FAIL": 10, "REMEASURE_BASELINE": 11, "UNDECIDED": 12}


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_kv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    pairs = (line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)
    return {key.strip(): value.strip() for key, value in pairs}


def targets(spec: dict[str, Any]) -> list[str]:
    return [entry for entries in spec["preregistered"]["target_groups"].values() for entry in entries]


def _mean(values: list[float | None]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def target_reading(base_of: Callable[[str], dict[str, Any]], cand_of: Callable[[str], dict[str, Any]],
                   prereg: dict[str, Any]) -> dict[str, Any]:
    """Criterion 1 and the mechanism readout, from case records {proxy, raw}."""
    groups, deltas = [], []
    for name, entries in prereg["target_groups"].items():
        rows = []
        for entry in entries:
            b, c = base_of(entry), cand_of(entry)
            delta = c["proxy"]["scenario_proxy"] - b["proxy"]["scenario_proxy"]
            deltas.append(delta)
            rows.append({
                "case": entry,
                "proxy_baseline": b["proxy"]["scenario_proxy"], "proxy_candidate": c["proxy"]["scenario_proxy"],
                "delta": delta,
                "survival_baseline": b["proxy"]["survival_proxy"], "survival_candidate": c["proxy"]["survival_proxy"],
                "tracking_baseline": b["proxy"]["tracking_proxy"], "tracking_candidate": c["proxy"]["tracking_proxy"],
                "speed_baseline": b["raw"].get("speed_xy_mean"), "speed_candidate": c["raw"].get("speed_xy_mean"),
                "height_p10_baseline": b["raw"].get("height_rel_p10"),
                "height_p10_candidate": c["raw"].get("height_rel_p10"),
                "posture_falls_baseline": b["raw"].get("posture_fall_env_count_pessimistic"),
                "posture_falls_candidate": c["raw"].get("posture_fall_env_count_pessimistic"),
                "terminated_baseline": b["raw"].get("terminated_env_count"),
                "terminated_candidate": c["raw"].get("terminated_env_count"),
            })
        mean_delta = _mean([row["delta"] for row in rows])
        groups.append({"group": name, "mean_delta": mean_delta, "improved": mean_delta > TOL, "rows": rows})
    target_delta = _mean(deltas)
    improved = sum(group["improved"] for group in groups)
    rows = [row for group in groups for row in group["rows"]]
    # fact_rules_v1: the mean may not hide one group's collapse (G-A038's 10cm climb).
    floor_violations = fact.group_floor_violations(groups, prereg) if fact.active(prereg) else []
    return {
        "passed": target_delta >= prereg["min_target_mean_proxy_delta"] - TOL
        and improved >= prereg["min_target_groups_improved"] and not floor_violations,
        "group_floor_violations": floor_violations,
        "target_mean_proxy_delta": target_delta,
        "target_groups_improved": improved,
        "target_groups": groups,
        "mechanism": {
            "height_p10_mean_baseline": _mean([r["height_p10_baseline"] for r in rows]),
            "height_p10_mean_candidate": _mean([r["height_p10_candidate"] for r in rows]),
            "posture_falls_baseline": sum(r["posture_falls_baseline"] or 0 for r in rows),
            "posture_falls_candidate": sum(r["posture_falls_candidate"] or 0 for r in rows),
            "speed_mean_baseline": _mean([r["speed_baseline"] for r in rows]),
            "speed_mean_candidate": _mean([r["speed_candidate"] for r in rows]),
            "note": "H1 (a higher stance) is read here; it is not a success criterion",
        },
    }


# The stationary criterion of `go2_fixed_eval_report.py:192-199`.  A robot holding under
# 0.10 m/s while its own tracking RMSE is at least 0.30 is ignoring a non-trivial command.
STATIONARY_SPEED = 0.10
STATIONARY_RMSE = 0.30


def _is_stationary(raw: dict[str, Any]) -> bool:
    return (raw.get("speed_xy_mean") or 0.0) < STATIONARY_SPEED \
        and (raw.get("tracking_xy_rmse") or 0.0) >= STATIONARY_RMSE


def stationary_reading(records: dict[tuple[str, str], dict[str, Any]],
                       prereg: dict[str, Any]) -> dict[str, Any]:
    """Stage 1's stationary guard, over the cases this stage actually measured.

    Defect S-4 (2026-09-19): only `verify_go2_basic_motion_harvest.py` read
    `stationary_guard_scenarios`, so standing still was caught in the full stage alone and
    stage 1 held a single flat catastrophe case.  G-A038 is the demonstration -- it walked
    12.3 m on the flat and crouched only on the stairs, and the catastrophe case passed.
    Stage 1 cannot see cases it did not measure, but it can apply the same criterion to the
    catastrophe and target cases it does read, restricted to the declared guard scenarios.
    """
    guard = set(prereg.get("stationary_guard_scenarios") or ())
    if not guard:
        return {"declared": False, "passed": True, "new_stationary": [], "read_cases": 0,
                "note": "spec declares no stationary_guard_scenarios"}
    limit = int(prereg.get("max_new_stationary_cases_in_guard", 0))
    read, base_stationary, cand_stationary = [], set(), set()
    for (arm, entry), record in records.items():
        if entry.split(":")[0] not in guard:
            continue
        if arm == "candidate":
            read.append(entry)
        if _is_stationary(record["raw"]):
            (cand_stationary if arm == "candidate" else base_stationary).add(entry)
    new_stationary = sorted(cand_stationary - base_stationary)
    return {
        "declared": True,
        "criterion": "speed_xy_mean < %.2f m/s and tracking_xy_rmse >= %.2f" % (
            STATIONARY_SPEED, STATIONARY_RMSE),
        "guard_scenarios": sorted(guard),
        "read_cases": len(read),
        "baseline_stationary": sorted(base_stationary),
        "candidate_stationary": sorted(cand_stationary),
        "new_stationary": new_stationary,
        "max_new_stationary_cases_in_guard": limit,
        "passed": len(new_stationary) <= limit,
    }


def compare_sentinel(keep: Path, stored: Path, spec: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """The sentinel cases measured in this run against the stored arm (G-A030's rule)."""
    label = spec["baseline"]["label"]
    tol = spec["evaluation"]["sentinel_tolerance"]
    std = float(registry["score"].get("tracking_proxy_std", 0.5))
    rows, faults = [], []
    for entry in spec["evaluation"]["sentinel_cases"]:
        scenario, case_id, seed = entry.split(":")
        here = keep / "evaluation" / f"{label}_sentinel" / "cases" / f"seed_{seed}" / case_id
        there = stored / "evaluation" / label / "cases" / f"seed_{seed}" / case_id
        checked = harvest.verify_case(here, scenario, case_id, int(seed)) if here.is_dir() else {"faults": ["absent"]}
        if checked["faults"]:
            faults.append("sentinel_case_invalid:%s:%s" % (entry, ",".join(map(str, checked["faults"][:3]))))
            continue
        a = json.loads((here / "summary.json").read_text(encoding="utf-8"))
        b = json.loads((there / "summary.json").read_text(encoding="utf-8"))
        ruler = [key for key in harvest.CASE_IDENTITY_FIELDS if a.get(key) != b.get(key)]
        pa, pb = _case_proxy(case_id, a, std), _case_proxy(case_id, b, std)
        ds = pa["survival_proxy"] - pb["survival_proxy"]
        dt = pa["tracking_proxy"] - pb["tracking_proxy"]
        agree = not ruler and abs(ds) <= tol["survival_abs"] + TOL and abs(dt) <= tol["tracking_proxy_abs"] + TOL
        rows.append({"case": entry, "survival_now": pa["survival_proxy"], "survival_stored": pb["survival_proxy"],
                     "tracking_now": pa["tracking_proxy"], "tracking_stored": pb["tracking_proxy"],
                     "ruler_fields_differ": ruler, "agrees": agree})
    return {"rows": rows, "faults": faults, "agrees": not faults and bool(rows) and all(r["agrees"] for r in rows)}


def gate(keep: Path, stored: Path, spec: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    base = spec["baseline"]
    label = base["label"]
    report: dict[str, Any] = {
        "work_id": spec["work_id"], "keep": str(keep),
        "role": "schedules the full stage only; tools/verify_go2_basic_motion_harvest.py decides",
    }
    status = read_kv(keep / "RUNNER_STATUS.txt")
    decision = status.get("DECISION")
    report["runner_status"] = {key: status.get(key) for key in ("RUNNER_RC", "WORK_ID", "DECISION", "STAGE")}
    faults: list[str] = []
    if status.get("RUNNER_RC") != "0":
        faults.append("runner_rc=%r" % status.get("RUNNER_RC"))
    if status.get("WORK_ID") != spec["work_id"]:
        faults.append("work_id=%r" % status.get("WORK_ID"))
    if not faults and decision in CATASTROPHE_DECISIONS:
        # A diverged or standing policy is a result about this value (plan 6-3), not missing data.
        report.update(verdict="FAIL", reason=decision, faults=[])
        return report
    if decision != TARGET_DECISION:
        faults.append("decision=%r" % decision)
    model = keep / "training" / "model_best.pt"
    cand_sha = sha_file(model) if model.is_file() else None
    if cand_sha is None or status.get("CANDIDATE_MODEL_SHA") != cand_sha:
        faults.append("candidate_model_sha=%r runner=%r" % (cand_sha, status.get("CANDIDATE_MODEL_SHA")))
    if faults:
        report.update(verdict="UNDECIDED", faults=faults)
        return report

    remeasured = (keep / "evaluation" / label / "cases").is_dir()
    arms = {"candidate": keep / "evaluation" / "candidate",
            "baseline": (keep if remeasured else stored) / "evaluation" / label}
    report["baseline_arm"] = "REMEASURED_SAME_RUN" if remeasured else "STORED_" + base["stored_arm_work_id"]
    expected_model = {"candidate": cand_sha, "baseline": base["model_sha256"]}
    for arm, root in arms.items():
        path = root / "identity.json"
        identity = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        identity = identity.get("identity", identity)
        for key, expected in (("evaluator_sha256", base["evaluator_sha256"]),
                              ("registry_sha256", base["registry_sha256"]),
                              ("model_sha256", expected_model[arm])):
            if identity.get(key) != expected:
                faults.append("%s_identity_%s=%r" % (arm, key, identity.get(key)))

    std = float(registry["score"].get("tracking_proxy_std", 0.5))
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in [spec["evaluation"]["catastrophe_case"], *targets(spec)]:
        scenario, case_id, seed = entry.split(":")
        summaries = {}
        for arm, root in arms.items():
            case_dir = root / "cases" / f"seed_{seed}" / case_id
            if arm == "baseline" and not remeasured:
                # The stored arm: summary.json only, verified in full when the pair was built.
                checked = {"faults": [] if (case_dir / "summary.json").is_file() else ["absent"]}
            elif case_dir.is_dir():
                checked = harvest.verify_case(case_dir, scenario, case_id, int(seed))
            else:
                checked = {"faults": ["absent"]}
            if checked["faults"]:
                faults.append("%s_case_invalid:%s:%s" % (arm, entry, ",".join(map(str, checked["faults"][:3]))))
                continue
            summaries[arm] = json.loads((case_dir / "summary.json").read_text(encoding="utf-8"))
            records[(arm, entry)] = {"proxy": _case_proxy(case_id, summaries[arm], std), "raw": summaries[arm]}
        if len(summaries) == 2:
            ruler = [k for k in harvest.CASE_IDENTITY_FIELDS
                     if summaries["candidate"].get(k) != summaries["baseline"].get(k)]
            if ruler:
                faults.append("ruler_differs:%s:%s" % (entry, ruler))
    report["faults"] = faults
    if faults:
        report["verdict"] = "UNDECIDED"
        return report
    if not remeasured:
        sentinel = compare_sentinel(keep, stored, spec, registry)
        report["sentinel"] = sentinel
        if not sentinel["agrees"]:
            report["verdict"] = "REMEASURE_BASELINE"
            return report
    prereg = spec["preregistered"]
    reading = target_reading(lambda e: records[("baseline", e)], lambda e: records[("candidate", e)], prereg)
    if fact.active(prereg):
        def case_dir(entry: str) -> Path:
            _, case_id, seed = entry.split(":")
            return arms["candidate"] / "cases" / f"seed_{seed}" / case_id
        reading["climb_guard"] = fact.climb_reading(case_dir, prereg, set(targets(spec)))
        if reading["climb_guard"]["violations"]:
            reading["passed"] = False
    # Defect S-4: standing still must be caught in stage 1 too, not only in the full stage.
    reading["stationary_guard"] = stationary_reading(records, prereg)
    if not reading["stationary_guard"]["passed"]:
        reading["passed"] = False
    report["target_stage"] = reading
    report["verdict"] = "TARGET_PASS" if reading["passed"] else "FAIL"
    if not reading["passed"]:
        report["reason"] = "1_target_basic_motion"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="target-stage gate for one arm of the basic-motion pair")
    parser.add_argument("--keep", required=True, type=Path, help="the arm's /workspace/_keep/<keep dir>")
    parser.add_argument("--package", required=True, type=Path, help="the arm's extracted package root")
    parser.add_argument("--stored", required=True, type=Path, help="stored baseline root (holds evaluation/<label>)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        spec = json.loads((args.package / "experiment.json").read_text(encoding="utf-8"))
        registry_path = args.package / "go2_self_eval_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        if sha_file(registry_path) != spec["baseline"]["registry_sha256"]:
            report = {"verdict": "UNDECIDED", "faults": ["registry_changed"]}
        else:
            report = gate(args.keep, args.stored, spec, registry)
    except Exception as error:  # a gate that cannot read is undecided, never a pass
        report = {"verdict": "UNDECIDED", "faults": ["gate_error:%s: %s" % (type(error).__name__, error)]}
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    reading = report.get("target_stage") or {}
    print("GATE %s verdict=%s target_delta=%s groups_improved=%s faults=%s" % (
        report.get("work_id"), report["verdict"], reading.get("target_mean_proxy_delta"),
        reading.get("target_groups_improved"), (report.get("faults") or [])[:3]))
    return EXIT[report["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
