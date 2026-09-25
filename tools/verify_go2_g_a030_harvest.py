#!/usr/bin/env python3
"""Verify a recovered G-A030 harvest, then apply the pre-registered reading.

The order is fixed and each step gates the next:
  1 artifacts: result state, runner status, internal SHA256SUMS, preserved
    report.html, the trained model/env and the reward weights actually in force
  2 each arm's 69-case measurement, with verify_go2_a027_harvest.verify_arm
  3 one ruler: compare_arms on the two arms, and -- when the stored G-A027 arm
    is reused -- the sentinel cases measured again in this run against it
  4 only then the numbers, against plan section 6-1 as written in the spec JSON

Verdicts
  INCONCLUSIVE                        a step 1-3 check failed; no score is read
  BASELINE_REMEASURE_REQUIRED         the stored baseline arm cannot be reused;
                                      rerun with GO2_REMEASURE_BASELINE=1
  FAIL                                complete data, a pre-registered condition not met
  QUANT_SUCCESS_VIDEO_REVIEW_PENDING  every quantitative condition met; item 5
                                      (videos) is a human reading
Exit 0 for FAIL or QUANT_SUCCESS_VIDEO_REVIEW_PENDING, 1 otherwise.

    python -B tools/verify_go2_g_a030_harvest.py \
        --harvest workspace/_keep/go2_g_a030_a017_flat_orientation_m1 \
        [--out <harvest>/harvest_verification.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import verify_go2_a027_harvest as harvest  # noqa: E402
from candidate_suite_checks import reward_weights  # noqa: E402
from go2_fixed_eval_report import _case_proxy, build_policy, instrument_mismatch  # noqa: E402

SPEC = GO2 / "config" / "experiments" / "G_A030_a017_flat_orientation_m1.json"
REGISTRY = GO2 / "config" / "go2_self_eval_registry.json"
RUNNER = GO2 / "server_run_go2_candidate_suite.sh"
TOL = 1e-9
DECISIONS = ("SUITE_COMPLETE", "CATASTROPHE_STATIONARY", "CATASTROPHE_TRAINING_NONFINITE")


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_kv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    pairs = (line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)
    return {key.strip(): value.strip() for key, value in pairs}


def check_artifacts(keep: Path, spec: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    faults: list[str] = []
    facts: dict[str, Any] = {}
    if read_kv(keep / "RESULT_STATUS.txt").get("RESULT_STATE") != "FULL":
        faults.append("result_state_not_FULL")
    status = read_kv(keep / "RUNNER_STATUS.txt")
    facts["runner_status"] = status
    if status.get("RUNNER_RC") != "0":
        faults.append("runner_rc=%r" % status.get("RUNNER_RC"))
    if status.get("WORK_ID") != spec["work_id"]:
        faults.append("work_id=%r" % status.get("WORK_ID"))
    if status.get("DECISION") not in DECISIONS:
        faults.append("decision=%r" % status.get("DECISION"))

    manifest = keep / "SHA256SUMS.txt"
    if manifest.is_file():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            target = keep / name.lstrip("./") if name.startswith("./") else keep / name
            if not target.is_file():
                faults.append("manifest_member_absent:" + name)
            elif sha_file(target) != digest:
                faults.append("manifest_member_changed:" + name)
    else:
        faults.append("SHA256SUMS_absent")

    report = keep / "exported" / "report.html"
    if read_kv(keep / "exported" / "REPORT_STATUS.txt").get("REPORT_STATUS") != "REPORT_ACQUIRED":
        faults.append("REPORT_REQUIRED_NOT_ACQUIRED")
    elif not report.is_file() or sha_file(report) not in (keep / "exported" / "report.html.sha256").read_text(encoding="utf-8"):
        faults.append("report_html_checksum")

    train = read_kv(keep / "training" / "TRAIN_STATUS.txt")
    single = spec["single_change"]
    if train.get("TRAIN_RC") != "0" or train.get("SEED") != str(spec["training"]["seed"]) \
            or train.get("MAX_ITERATIONS") != str(spec["training"]["max_iterations"]):
        faults.append("train_status=%r" % train)
    if train.get("SINGLE_CHANGE") != "%s:%s->%s" % (single["name"], single["from"], single["to"]):
        faults.append("train_single_change=%r" % train.get("SINGLE_CHANGE"))
    model, env = keep / "training" / "model_best.pt", keep / "training" / "env.yaml"
    if not model.is_file() or not env.is_file():
        faults.append("trained_model_or_env_absent")
        return faults, facts
    facts["candidate_model_sha256"] = sha_file(model)
    facts["candidate_env_sha256"] = sha_file(env)
    if status.get("CANDIDATE_MODEL_SHA") != facts["candidate_model_sha256"]:
        faults.append("runner_candidate_sha_differs_from_trained_model")
    found = reward_weights(env.read_text(encoding="utf-8"))
    # 2026-09-18: an env reward arm (change_class env_reward_weight) moves a term that is not one of
    # the six names in the deployed list, so it is carried in candidate_env_extra.  It is checked the
    # same way -- the trained env.yaml is the only proof the weight was actually applied.
    expected_rewards = {**spec["rewards"]["candidate"], **(spec["rewards"].get("candidate_env_extra") or {})}
    facts["candidate_env_rewards"] = {name: found.get(name) for name in expected_rewards}
    for name, value in expected_rewards.items():
        if found.get(name) is None or abs(found[name] - float(value)) > TOL:
            faults.append("env_reward_%s=%r expected %r" % (name, found.get(name), value))

    base = spec["baseline"]
    for name, expected in (("evaluator.sha256", base["evaluator_sha256"]), ("registry.sha256", base["registry_sha256"])):
        path = keep / "meta" / name
        if not path.is_file() or path.read_text(encoding="utf-8").split()[0] != expected:
            faults.append("meta_%s_not_%s" % (name, expected[:12]))
    return faults, facts


def run_plan(spec: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    """The approved conditions each arm is checked against.

    The baseline expectations are frozen before the run.  The candidate's model
    cannot be: it is produced by the run.  It is tied instead to the trained
    artifact, the runner's own record of it and the reward weights in force
    (check_artifacts), which is the most that can be fixed for a new policy.
    """
    text = RUNNER.read_text(encoding="utf-8")
    body = re.search(r"^run_eval_case\(\)\s*\{(.*?)^\}", text, re.M | re.S)
    envs = re.search(r"--num_envs\s+(\d+)", body.group(1)) if body else None
    steps = re.search(r"^EVAL_STEPS=\$\{GO2_EVAL_STEPS:-(\d+)\}", text, re.M)
    base = spec["baseline"]
    return {
        "num_envs": int(envs.group(1)) if envs else None,
        "steps": int(steps.group(1)) if steps else None,
        "evaluator_sha256": base["evaluator_sha256"],
        "registry_sha256": base["registry_sha256"],
        "models": {"candidate": facts.get("candidate_model_sha256"), base["label"]: base["model_sha256"]},
        "envs": {"candidate": facts.get("candidate_env_sha256"), base["label"]: base["env_sha256"]},
        "faults": [],
    }


def stored_label(spec: dict[str, Any]) -> str:
    """The baseline's folder inside its stored arm.  Usually its label in this run.

    They differ when the baseline was itself a candidate: G-A033 sits in evaluation/candidate of its
    own harvest, but in a G-A035 harvest "candidate" is G-A035.  Reading the stored arm by the run
    label would miss it; naming the run arm "candidate" would compare the candidate with itself.
    """
    return spec["baseline"].get("stored_label", spec["baseline"]["label"])


def compare_sentinel(keep: Path, stored: Path, spec: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Re-measured baseline cases against the stored arm they stand in for."""
    label = spec["baseline"]["label"]
    tol = spec["evaluation"]["sentinel_tolerance"]
    std = float(registry["score"].get("tracking_proxy_std", 0.5))
    rows, faults = [], []
    for entry in spec["evaluation"]["sentinel_cases"]:
        scenario, case_id, seed = entry.split(":")
        here = keep / "evaluation" / f"{label}_sentinel" / "cases" / f"seed_{seed}" / case_id
        there = stored / "evaluation" / stored_label(spec) / "cases" / f"seed_{seed}" / case_id
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


def _case(policy: dict[str, Any], case_id: str, seed: int) -> dict[str, Any]:
    return next(item for item in policy["cases"].values() if item["case_id"] == case_id and item["seed"] == seed)


def judge(base: dict[str, Any], cand: dict[str, Any], prereg: dict[str, Any]) -> dict[str, Any]:
    """Apply plan section 6-1 to two build_policy reports measured on one ruler."""
    seeds = (101, 202, 303)
    target, watch = prereg["target_case"], prereg["watch_case"]

    per_seed = []
    for seed in seeds:
        b, c = _case(base, target, seed), _case(cand, target, seed)
        per_seed.append({
            "seed": seed,
            "survival_baseline": b["proxy"]["survival_proxy"],
            "survival_candidate": c["proxy"]["survival_proxy"],
            "survival_delta": c["proxy"]["survival_proxy"] - b["proxy"]["survival_proxy"],
            # Survival +0.10 is not "four fewer terminations": terminations can
            # fall while posture-gate falls rise.  Both are read, separately.
            "terminated_baseline": b["raw"].get("terminated_env_count"),
            "terminated_candidate": c["raw"].get("terminated_env_count"),
            "posture_falls_baseline": b["raw"].get("posture_fall_env_count_pessimistic"),
            "posture_falls_candidate": c["raw"].get("posture_fall_env_count_pessimistic"),
        })
    g3_delta = cand["scenarios"]["G3"]["scenario_proxy"] - base["scenarios"]["G3"]["scenario_proxy"]
    c1 = all(row["survival_delta"] >= prereg["min_target_survival_delta_each_seed"] - TOL for row in per_seed) \
        and g3_delta > 0
    h_a = all(row["terminated_candidate"] < row["terminated_baseline"] for row in per_seed)

    points_delta = cand["simulation_points_70"] - base["simulation_points_70"]
    c2 = points_delta >= prereg["min_total_points_delta"] - TOL

    violations = []
    for key, b in base["cases"].items():
        c = cand["cases"][key]
        ds = c["proxy"]["survival_proxy"] - b["proxy"]["survival_proxy"]
        dt = c["proxy"]["tracking_proxy"] - b["proxy"]["tracking_proxy"]
        if ds < -prereg["max_case_survival_drop"] - TOL:
            violations.append("%s survival %+.5f" % (key, ds))
        if dt < -prereg["max_case_tracking_drop"] - TOL:
            violations.append("%s tracking %+.5f" % (key, dt))
    watch_rows = []
    for seed in seeds:
        b, c = _case(base, watch, seed), _case(cand, watch, seed)
        rise = c["raw"]["posture_fall_env_count_pessimistic"] - b["raw"]["posture_fall_env_count_pessimistic"]
        watch_rows.append({"seed": seed, "posture_fall_increase": rise,
                           "height_p10_baseline": b["raw"].get("height_rel_p10"),
                           "height_p10_candidate": c["raw"].get("height_rel_p10")})
        if rise > prereg["max_watch_posture_fall_increase_each_seed"]:
            violations.append("%s@%d posture falls +%d" % (watch, seed, rise))
    c3 = not violations

    cand_loco, base_loco = cand["locomotion"], base["locomotion"]
    c4 = cand_loco["verdict"] == "POLICY_LOCOMOTES" \
        and cand_loco["stationary_case_count"] <= base_loco["stationary_case_count"]

    criteria = {
        "1_target_survival_each_seed": c1,
        "2_total_points_delta": c2,
        "3_non_inferiority": c3,
        "4_locomotion": c4,
        "5_video": "VIDEO_UNKNOWN",
    }
    passed = c1 and c2 and c3 and c4
    return {
        "verdict": "QUANT_SUCCESS_VIDEO_REVIEW_PENDING" if passed else "FAIL",
        "criteria": criteria,
        "failed": [name for name, ok in criteria.items() if ok is False],
        "target_per_seed": per_seed,
        "g3_scenario_proxy_delta": g3_delta,
        "h_a_terminations_fell_every_seed": h_a,
        "points_70": {"baseline": base["simulation_points_70"], "candidate": cand["simulation_points_70"],
                      "delta": points_delta},
        "non_inferiority_violations": violations,
        "watch_case": watch_rows,
        "locomotion": {"baseline": base_loco["stationary_case_count"],
                       "candidate": cand_loco["stationary_case_count"], "candidate_verdict": cand_loco["verdict"]},
        "scenario_delta": {sid: cand["scenarios"][sid]["scenario_proxy"] - base["scenarios"][sid]["scenario_proxy"]
                           for sid in base["scenarios"]},
        "expected_weighted_gain": "미추정",
        "status": "exploratory",
    }


def verify(keep: Path, stored: Path, spec: dict[str, Any]) -> dict[str, Any]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    report: dict[str, Any] = {"schema_version": 1, "work_id": spec["work_id"], "harvest": str(keep)}
    faults, facts = check_artifacts(keep, spec)
    report.update(artifact_faults=faults, facts=facts)
    if sha_file(REGISTRY) != spec["baseline"]["registry_sha256"]:
        faults.append("local_registry_changed")
    decision = facts.get("runner_status", {}).get("DECISION")
    if faults:
        report["verdict"] = "INCONCLUSIVE"
        return report
    if decision != "SUITE_COMPLETE":
        # A diverged or standing policy is a result about this configuration,
        # recorded as a failure of the run, not as missing data (plan 5-2 H-D).
        report["verdict"] = "FAIL"
        report["reason"] = decision
        return report

    label = spec["baseline"]["label"]
    plan = run_plan(spec, facts)
    remeasured = (keep / "evaluation" / label / "cases").is_dir()
    base_parent = keep if remeasured else stored
    report["baseline_arm"] = "REMEASURED_SAME_RUN" if remeasured else "STORED_" + spec["baseline"]["stored_arm_work_id"]
    arms = [harvest.verify_arm(keep, "candidate", registry, plan), harvest.verify_arm(base_parent, label, registry, plan)]
    report["arms"] = {arm["label"]: {"measurement": arm["measurement"], "faults": arm["faults"],
                                     "invalid_cases": arm["invalid_cases"]} for arm in arms}
    mismatches = harvest.compare_arms(arms)
    report["ruler_mismatches"] = mismatches
    if any(arm["measurement"] != "INTERNAL_MEASUREMENT_OK" for arm in arms):
        report["verdict"] = "INCONCLUSIVE"
        return report
    if not remeasured:
        sentinel = compare_sentinel(keep, stored, spec, registry)
        report["sentinel"] = sentinel
        if mismatches or not sentinel["agrees"]:
            # Not a verdict on the candidate: the stored arm is not shown to be
            # the same ruler, so measure the baseline again on this one.
            report["verdict"] = "BASELINE_REMEASURE_REQUIRED"
            return report
    elif mismatches:
        report["verdict"] = "INCONCLUSIVE"
        return report

    reg_path = REGISTRY
    cand = build_policy(keep / "evaluation" / "candidate", reg_path,
                        json.loads((keep / "evaluation" / "candidate" / "identity.json").read_text(encoding="utf-8")))
    base = build_policy(base_parent / "evaluation" / label, reg_path,
                        json.loads((base_parent / "evaluation" / label / "identity.json").read_text(encoding="utf-8")))
    mismatch = instrument_mismatch(base, cand)
    if mismatch:
        report["verdict"] = "INCONCLUSIVE"
        report["instrument_mismatch"] = mismatch
        return report
    report["judgement"] = judge(base, cand, spec["preregistered"])
    report["verdict"] = report["judgement"]["verdict"]
    return report


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description="verify a recovered G-A030 harvest")
    parser.add_argument("--harvest", required=True, type=Path)
    parser.add_argument("--stored-baseline", type=Path, default=ROOT / spec["baseline"]["stored_arm"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = verify(args.harvest, args.stored_baseline, spec)
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, default=str)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text if len(text) < 6000 else json.dumps({k: report.get(k) for k in ("verdict", "reason", "artifact_faults",
                                                                                   "ruler_mismatches", "baseline_arm")},
                                                    indent=2, ensure_ascii=False, default=str))
    print("VERDICT", report["verdict"])
    return 0 if report["verdict"] in ("FAIL", "QUANT_SUCCESS_VIDEO_REVIEW_PENDING") else 1


if __name__ == "__main__":
    raise SystemExit(main())
