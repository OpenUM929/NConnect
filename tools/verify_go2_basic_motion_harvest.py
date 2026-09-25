#!/usr/bin/env python3
"""Verify a recovered basic-motion harvest (G-A031 / G-A032), then apply the pre-registered reading.

The staged runner returns one of two harvests:
  target stage (DECISION=TARGET_STAGE_COMPLETE): the catastrophe case and the 9
    target cases.  Criterion 1 of plan section 6-1 needs only those cases, so it
    is read here and a failure is final.  A pass asks for the full stage.
  full stage (DECISION=SUITE_COMPLETE): all 69 cases.  Steps 1-3 are G-A030's,
    reused unchanged (artifacts, each arm's 69 cases, one ruler); step 4 is
    criteria 1-4 of plan section 6-1.

Verdicts
  INCONCLUSIVE                        a check before the numbers failed; no score is read
  BASELINE_REMEASURE_REQUIRED         the stored baseline arm cannot be reused
  FAIL                                complete data, a pre-registered condition not met
  TARGET_PASS_FULL_STAGE_REQUIRED     target stage: criterion 1 met, run the full stage
  QUANT_SUCCESS_VIDEO_REVIEW_PENDING  full stage: criteria 1-4 met; videos are a human reading
One arm never settles the direction; the pair is read with plan section 6-3.

    python -B tools/verify_go2_basic_motion_harvest.py G-A031 \\
        --harvest workspace/_keep/go2_g_a031_a017_feet_air_time_001 [--out <harvest>/harvest_verification.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as reward  # noqa: E402
import build_go2_candidate_package as pkg  # noqa: E402
import build_go2_seed_pair_package as seed_pair  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402
import go2_fact_rules as fact  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import verify_go2_g_a030_harvest as a030  # noqa: E402
from go2_fixed_eval_report import _case_proxy, build_policy, instrument_mismatch  # noqa: E402
# The pair runner's server gate reads criterion 1 with this same function.
from go2_target_gate import target_reading  # noqa: E402

TOL = a030.TOL
harvest = a030.harvest
TARGET_DECISION = "TARGET_STAGE_COMPLETE"
PASS_VERDICTS = ("FAIL", "TARGET_PASS_FULL_STAGE_REQUIRED", "QUANT_SUCCESS_VIDEO_REVIEW_PENDING")

# Every staged arm this verifier can read.  G-A035 (training length) has its own builder; before
# 2026-09-16 it was missing here, so a G-A035 harvest could not be judged at all.
# G-A037 (a reward change on G-A033) likewise has its own builder.
# G-A045/G-A046 (학습 seed 대칭 쌍) 도 자기 빌더를 가진다.  여기 없으면 안내문이 시키는 판독
# 명령이 argparse 에서 죽는다 — 결함 C-15 와 같은 모양이라, 관문이 명령을 **실행해서** 확인한다.
SPECS = {**pkg.SPECS, **length.SPECS, **reward.SPECS, **seed_pair.SPECS}


def load_spec(work_id: str) -> dict[str, Any]:
    for module in (seed_pair, reward, length):
        if work_id in module.SPECS:
            return module.load(work_id)
    return pkg.load(work_id)


def target_stage_entries(spec: dict[str, Any]) -> list[str]:
    """All cases that stage 1 promises to validate, including unscored required records."""
    measured = reward.targets(spec) if spec["preregistered"].get("required_target_cases") else pkg.targets(spec)
    return [spec["evaluation"]["catastrophe_case"], *measured]


def required_case_presence_faults(arm: Path, spec: dict[str, Any]) -> list[str]:
    faults = []
    for entry in spec.get("preregistered", {}).get("required_target_cases", []):
        _scenario, case_id, seed = entry.split(":")
        if not (arm / "cases" / f"seed_{seed}" / case_id).is_dir():
            faults.append("required_case_absent:" + entry)
    return faults


def plan_screening_version(spec: dict[str, Any]) -> str | None:
    """The screening rule edition this spec preregistered, or None when it opted out.

    2026-09-22 (G-A043): the editions differ only in which cases the protection block covers
    (tools/go2_screening_gate.RULE_VERSIONS).  An unknown name is not silently downgraded to the
    default - go2_screening_gate.cases_for raises on it - so a typo cannot turn a guarded run into
    an unguarded one.
    """
    version = spec.get("preregistered", {}).get("plan_screening", {}).get("version")
    return version if version in screening.RULE_VERSIONS else None


def plan_screening_active(spec: dict[str, Any]) -> bool:
    """The plan screening is opt-in; historical campaign verdicts remain byte-for-byte semantic."""
    return plan_screening_version(spec) is not None


def combined_verdict(*, artifact_faults: list[str], fact_verdict: str,
                     screening_verdict: str | None) -> dict[str, Any]:
    """Combine integrity, fact_rules and plan screening without allowing numeric override."""
    if artifact_faults or fact_verdict in ("INCONCLUSIVE", "BASELINE_REMEASURE_REQUIRED") \
            or screening_verdict == screening.INCONCLUSIVE:
        verdict = "INCONCLUSIVE"
    elif screening_verdict == screening.FAIL:
        verdict = "FAIL"
    else:
        verdict = fact_verdict
    return {
        "artifact": "INCONCLUSIVE" if artifact_faults else "ARTIFACT_VERIFIED",
        "fact_rules": fact_verdict,
        "plan_screening": screening_verdict or "NOT_APPLICABLE",
        "verdict": verdict,
    }


def screening_identities(spec: dict[str, Any], facts: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    base = spec["baseline"]
    candidate = {
        "model_sha256": facts.get("candidate_model_sha256"),
        "env_sha256": facts.get("candidate_env_sha256"),
        "evaluator_sha256": base["evaluator_sha256"],
        "registry_sha256": base["registry_sha256"],
        "checkpoint_iter": spec.get("evaluation", {}).get("checkpoint_iter"),
    }
    baseline = {key: base[key] for key in ("model_sha256", "env_sha256", "evaluator_sha256", "registry_sha256")}
    return candidate, baseline


def apply_plan_screening(report: dict[str, Any], keep: Path, baseline_arm: Path,
                         spec: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    if not plan_screening_active(spec):
        report["combined_verdict"] = combined_verdict(
            artifact_faults=report.get("artifact_faults", []), fact_verdict=report["verdict"],
            screening_verdict=None)
        return report
    candidate_identity, baseline_identity = screening_identities(spec, facts)
    plan_report = screening.screen(
        keep, baseline_arm,
        expected_candidate_identity=candidate_identity,
        expected_baseline_identity=baseline_identity,
        cases=screening.cases_for(plan_screening_version(spec)))
    report["plan_screening"] = plan_report
    report["combined_verdict"] = combined_verdict(
        artifact_faults=report.get("artifact_faults", []), fact_verdict=report["verdict"],
        screening_verdict=plan_report["verdict"])
    report["verdict"] = report["combined_verdict"]["verdict"]
    return report


def fail_closed(report: dict[str, Any], spec: dict[str, Any], faults: list[str]) -> dict[str, Any]:
    """Persist the combined verdict when integrity blocks both numeric readers."""
    if plan_screening_active(spec):
        report["combined_verdict"] = combined_verdict(
            artifact_faults=faults or ["verification_incomplete"], fact_verdict="INCONCLUSIVE",
            screening_verdict=screening.INCONCLUSIVE)
        report["verdict"] = report["combined_verdict"]["verdict"]
    return report


def stored_arm_dir(stored: Path, spec: dict[str, Any]) -> Path:
    return stored / "evaluation" / a030.stored_label(spec)


def stored_plan(plan: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """verify_arm looks the expected SHA up by folder name.  Map the stored folder to the baseline."""
    base, folder = spec["baseline"], a030.stored_label(spec)
    return {**plan, "models": {**plan["models"], folder: base["model_sha256"]},
            "envs": {**plan["envs"], folder: base["env_sha256"]}}


def _entry(policy: dict[str, Any], entry: str) -> dict[str, Any]:
    _, case_id, seed = entry.split(":")
    return a030._case(policy, case_id, int(seed))


def judge(base: dict[str, Any], cand: dict[str, Any], prereg: dict[str, Any],
          climb: dict[str, Any] | None = None) -> dict[str, Any]:
    """Apply plan section 6-1 to two build_policy reports measured on one ruler.

    fact_rules_v1 specs (tools/go2_fact_rules.py) add: a floor per target group (criterion 1),
    the climbed-robot floor of the stairs cases (criterion 3, `climb` from fact.climb_reading) and
    a rise of the target axes G3+G5 (criterion 6).
    """
    reading = target_reading(lambda e: _entry(base, e), lambda e: _entry(cand, e), prereg)
    c1 = reading["passed"]

    points_delta = cand["simulation_points_70"] - base["simulation_points_70"]
    c2 = points_delta >= prereg["min_total_points_delta"] - TOL

    flat = set(prereg["flat_scenarios"])
    # G-A037 on: each scenario may lose at most twice its own evaluation sd.  Specs without the
    # table keep the single uniform limit, so every earlier verdict reads the same.
    by_scenario = prereg.get("max_scenario_weighted_loss_70_by_scenario") or {}
    violations, scenario_rows = [], {}
    for sid, b in base["scenarios"].items():
        drop = b["scenario_proxy"] - cand["scenarios"][sid]["scenario_proxy"]
        weighted = max(0.0, drop) * float(b["weight"]) * 70.0
        limit = float(by_scenario.get(sid, prereg["max_scenario_weighted_loss_70"]))
        scenario_rows[sid] = {"delta": -drop, "weighted_loss_70": weighted,
                              "limit_70": None if sid in flat else limit}
        if sid in flat:
            if drop > prereg["max_flat_scenario_proxy_drop"] + TOL:
                violations.append("%s flat scenario proxy %+.5f" % (sid, -drop))
        elif weighted > limit + TOL:
            violations.append("%s weighted loss %.3f/70 > %.5f" % (sid, weighted, limit))
    for key, b in base["cases"].items():
        if b["scenario_id"] in flat:
            ds = cand["cases"][key]["proxy"]["survival_proxy"] - b["proxy"]["survival_proxy"]
            if ds < -prereg["max_flat_case_survival_drop"] - TOL:
                violations.append("%s survival %+.5f" % (key, ds))
    if fact.active(prereg):
        if climb is None:
            violations.append("climb_guard not read")
        else:
            violations.extend(climb["violations"])
    c3 = not violations

    # Standing still is the shortcut this guards against, in basic motion.  Stairs (G5) are
    # excluded: A017 already stands on all three stairs_15_down cases, which score 0 and are
    # held by the weighted-loss guard above (plan 6-1, "falls last").
    cand_loco, base_loco = cand["locomotion"], base["locomotion"]
    guard = set(prereg["stationary_guard_scenarios"])
    base_stationary = {case for case in base_loco["stationary_cases"] if case.split("/")[0] in guard}
    new_stationary = sorted(case for case in cand_loco["stationary_cases"]
                            if case.split("/")[0] in guard and case not in base_stationary)
    c4 = cand_loco["verdict"] == "POLICY_LOCOMOTES" \
        and len(new_stationary) <= prereg["max_new_stationary_cases_in_guard"]

    criteria = {
        "1_target_basic_motion": c1,
        "2_total_points_delta": c2,
        "3_non_inferiority": c3,
        "4_locomotion": c4,
        "5_video": "VIDEO_UNKNOWN",
    }
    axes = fact.target_axes_reading(base, cand, prereg) if fact.active(prereg) else None
    if axes is not None:
        criteria["6_target_axes_rise"] = axes["rises"]
    passed = c1 and c2 and c3 and c4 and (axes is None or axes["rises"])
    return {
        "verdict": "QUANT_SUCCESS_VIDEO_REVIEW_PENDING" if passed else "FAIL",
        "criteria": criteria,
        "failed": [name for name, ok in criteria.items() if ok is False],
        "target_mean_proxy_delta": reading["target_mean_proxy_delta"],
        "target_groups_improved": reading["target_groups_improved"],
        "target_groups": reading["target_groups"],
        "points_70": {"baseline": base["simulation_points_70"], "candidate": cand["simulation_points_70"],
                      "delta": points_delta},
        "non_inferiority_violations": violations,
        "scenarios": scenario_rows,
        "locomotion": {"baseline_stationary": base_loco["stationary_cases"],
                       "candidate_stationary": cand_loco["stationary_cases"],
                       "new_stationary_in_guard": new_stationary, "candidate_verdict": cand_loco["verdict"]},
        "mechanism": reading["mechanism"],
        "group_floor_violations": reading.get("group_floor_violations", []),
        "climb_guard": climb,
        "target_axes": axes,
        "expected_weighted_gain": "미추정",
        "status": "exploratory",
    }


def run_plan(spec: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    """G-A030's run plan, read from the staged runner this package ships."""
    text = (GO2 / pkg.RUNNER).read_text(encoding="utf-8")
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


def check_artifacts(keep: Path, spec: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    faults, facts = a030.check_artifacts(keep, spec)
    # G-A030's list of decisions predates the target stage.
    faults = [f for f in faults if f != "decision=%r" % TARGET_DECISION]
    if plan_screening_active(spec):
        faults = [f for f in faults if f != "decision=%r" %
                  "CATASTROPHE_STATIONARY_MANDATORY_COLLECTION_COMPLETE"]
    # G-A033 v2 on: the candidate must have been evaluated at the baseline's checkpoint
    # iteration, and the pin record must name the model that was evaluated.
    pinned = spec["evaluation"].get("checkpoint_iter")
    if pinned is not None:
        status = facts.get("runner_status", {})
        pin = a030.read_kv(keep / "training" / "CHECKPOINT_PIN.txt")
        facts["checkpoint_pin"] = pin
        if status.get("CANDIDATE_EVAL_ITER") != str(pinned) or pin.get("EVAL_CHECKPOINT_ITER") != str(pinned):
            faults.append("candidate_eval_iter=%r pin=%r expected=%s" % (
                status.get("CANDIDATE_EVAL_ITER"), pin.get("EVAL_CHECKPOINT_ITER"), pinned))
        if pin.get("EVAL_CHECKPOINT_SHA") != facts.get("candidate_model_sha256"):
            faults.append("checkpoint_pin_sha=%r candidate=%r" % (pin.get("EVAL_CHECKPOINT_SHA"),
                                                                facts.get("candidate_model_sha256")))
    return faults, facts


def verify_target_stage(keep: Path, stored: Path, spec: dict[str, Any], registry: dict[str, Any],
                        facts: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    label, base_spec = spec["baseline"]["label"], spec["baseline"]
    std = float(registry["score"].get("tracking_proxy_std", 0.5))
    entries = target_stage_entries(spec)
    remeasured = (keep / "evaluation" / label / "cases").is_dir()
    arms = {"candidate": keep / "evaluation" / "candidate",
            "baseline": keep / "evaluation" / label if remeasured else stored_arm_dir(stored, spec)}
    report["baseline_arm"] = "REMEASURED_SAME_RUN" if remeasured else "STORED_" + base_spec["stored_arm_work_id"]
    faults: list[str] = []
    expected_identity = {
        "candidate": {"model_sha256": facts.get("candidate_model_sha256"),
                      "env_sha256": facts.get("candidate_env_sha256")},
        "baseline": {"model_sha256": base_spec["model_sha256"],
                     "env_sha256": base_spec["env_sha256"]},
    }
    for arm, root in arms.items():
        faults.extend(f"{arm}_{fault}" for fault in required_case_presence_faults(root, spec))
        path = root / "identity.json"
        identity = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        identity = identity.get("identity", identity)
        for key, expected in (("evaluator_sha256", base_spec["evaluator_sha256"]),
                              ("registry_sha256", base_spec["registry_sha256"]),
                              ("model_sha256", expected_identity[arm]["model_sha256"]),
                              ("env_sha256", expected_identity[arm]["env_sha256"])):
            if identity.get(key) != expected:
                faults.append("%s_identity_%s=%r" % (arm, key, identity.get(key)))
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        scenario, case_id, seed = entry.split(":")
        summaries = {}
        for arm, root in arms.items():
            case_dir = root / "cases" / f"seed_{seed}" / case_id
            checked = harvest.verify_case(case_dir, scenario, case_id, int(seed)) if case_dir.is_dir() \
                else {"faults": ["absent"]}
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
    report["stage_faults"] = faults
    if faults:
        report["verdict"] = "INCONCLUSIVE"
        return fail_closed(report, spec, faults)
    if not remeasured:
        sentinel = a030.compare_sentinel(keep, stored, spec, registry)
        report["sentinel"] = sentinel
        if not sentinel["agrees"]:
            report["verdict"] = "BASELINE_REMEASURE_REQUIRED"
            return fail_closed(report, spec, ["baseline_sentinel_disagrees"])
    reading = target_reading(lambda e: records[("baseline", e)], lambda e: records[("candidate", e)],
                             spec["preregistered"])
    gate = spec["evaluation"]["catastrophe_case"]
    reading["catastrophe_case"] = {"case": gate, "proxy_baseline": records[("baseline", gate)]["proxy"]["scenario_proxy"],
                                   "proxy_candidate": records[("candidate", gate)]["proxy"]["scenario_proxy"]}
    reading["note"] = "criterion 1 needs only these cases; criteria 2-4 need the full stage"
    if fact.active(spec["preregistered"]):
        reading["climb_guard"] = fact.climb_reading(
            lambda e: arms["candidate"] / "cases" / f"seed_{e.split(':')[2]}" / e.split(":")[1],
            spec["preregistered"], set(entries))
        if reading["climb_guard"]["violations"]:
            reading["passed"] = False
    report["target_stage"] = reading
    report["verdict"] = "TARGET_PASS_FULL_STAGE_REQUIRED" if reading["passed"] else "FAIL"
    if not reading["passed"]:
        report["reason"] = "1_target_basic_motion"
    return apply_plan_screening(report, keep, arms["baseline"], spec, facts)


def verify(keep: Path, stored: Path, spec: dict[str, Any]) -> dict[str, Any]:
    registry = json.loads(a030.REGISTRY.read_text(encoding="utf-8"))
    report: dict[str, Any] = {"schema_version": 2, "work_id": spec["work_id"], "harvest": str(keep)}
    faults, facts = check_artifacts(keep, spec)
    report.update(artifact_faults=faults, facts=facts)
    if a030.sha_file(a030.REGISTRY) != spec["baseline"]["registry_sha256"]:
        faults.append("local_registry_changed")
    decision = facts.get("runner_status", {}).get("DECISION")
    report["stage"] = facts.get("runner_status", {}).get("STAGE")
    if faults:
        report["verdict"] = "INCONCLUSIVE"
        return fail_closed(report, spec, faults)
    if decision == TARGET_DECISION:
        return verify_target_stage(keep, stored, spec, registry, facts, report)
    if decision != "SUITE_COMPLETE":
        # A diverged or standing policy is a result about this value (plan 6-3), not missing data.
        # forward_stairs_v1 nevertheless promises all stage-1 records before it finishes.  Validate
        # those cases, their per-case fingerprints and both arm identities before accepting the
        # performance failure; missing mandatory evidence overrides FAIL as INCONCLUSIVE.
        if plan_screening_active(spec):
            checked = verify_target_stage(keep, stored, spec, registry, facts, report)
            if checked["verdict"] in ("INCONCLUSIVE", "BASELINE_REMEASURE_REQUIRED"):
                return checked
            checked["fact_rules_verdict_before_plan_screening"] = checked.get(
                "combined_verdict", {}).get("fact_rules", checked["verdict"])
            checked["reason"] = decision
            plan_verdict = checked.get("plan_screening", {}).get("verdict")
            checked["combined_verdict"] = combined_verdict(
                artifact_faults=checked.get("artifact_faults", []), fact_verdict="FAIL",
                screening_verdict=plan_verdict)
            checked["verdict"] = checked["combined_verdict"]["verdict"]
            return checked
        report["verdict"] = "FAIL"
        report["reason"] = decision
        return report

    label = spec["baseline"]["label"]
    plan = run_plan(spec, facts)
    remeasured = (keep / "evaluation" / label / "cases").is_dir()
    base_parent = keep if remeasured else stored
    report["baseline_arm"] = "REMEASURED_SAME_RUN" if remeasured else "STORED_" + spec["baseline"]["stored_arm_work_id"]
    if remeasured:
        base_arm = harvest.verify_arm(keep, label, registry, plan)
    else:
        base_arm = harvest.verify_arm(stored, a030.stored_label(spec), registry, stored_plan(plan, spec))
        base_arm["label"] = label
    arms = [harvest.verify_arm(keep, "candidate", registry, plan), base_arm]
    report["arms"] = {arm["label"]: {"measurement": arm["measurement"], "faults": arm["faults"],
                                     "invalid_cases": arm["invalid_cases"]} for arm in arms}
    mismatches = harvest.compare_arms(arms)
    report["ruler_mismatches"] = mismatches
    if any(arm["measurement"] != "INTERNAL_MEASUREMENT_OK" for arm in arms):
        report["verdict"] = "INCONCLUSIVE"
        return fail_closed(report, spec, [fault for arm in arms for fault in arm.get("faults", [])])
    if not remeasured:
        sentinel = a030.compare_sentinel(keep, stored, spec, registry)
        report["sentinel"] = sentinel
        if mismatches or not sentinel["agrees"]:
            report["verdict"] = "BASELINE_REMEASURE_REQUIRED"
            return fail_closed(report, spec, list(mismatches) or ["baseline_sentinel_disagrees"])
    elif mismatches:
        report["verdict"] = "INCONCLUSIVE"
        return fail_closed(report, spec, list(mismatches))

    def policy(parent: Path, arm: str) -> dict[str, Any]:
        identity = json.loads((parent / "evaluation" / arm / "identity.json").read_text(encoding="utf-8"))
        return build_policy(parent / "evaluation" / arm, a030.REGISTRY, identity)

    cand, base = policy(keep, "candidate"), policy(base_parent, label if remeasured else a030.stored_label(spec))
    mismatch = instrument_mismatch(base, cand)
    if mismatch:
        report["verdict"] = "INCONCLUSIVE"
        report["instrument_mismatch"] = mismatch
        return fail_closed(report, spec, list(mismatch))
    prereg = spec["preregistered"]
    climb = None
    if fact.active(prereg):
        climb = fact.climb_reading(
            lambda e: keep / "evaluation" / "candidate" / "cases" / f"seed_{e.split(':')[2]}" / e.split(":")[1],
            prereg)
    report["judgement"] = judge(base, cand, prereg, climb)
    report["verdict"] = report["judgement"]["verdict"]
    baseline_arm = base_parent / "evaluation" / (label if remeasured else a030.stored_label(spec))
    return apply_plan_screening(report, keep, baseline_arm, spec, facts)


def main() -> int:
    parser = argparse.ArgumentParser(description="verify a recovered G-A031/G-A032 harvest")
    parser.add_argument("work_id", choices=sorted(SPECS))
    parser.add_argument("--harvest", required=True, type=Path)
    parser.add_argument("--stored-baseline", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    spec = load_spec(args.work_id)
    stored = args.stored_baseline or ROOT / spec["baseline"]["stored_arm"]
    report = verify(args.harvest, stored, spec)
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, default=str)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text if len(text) < 6000 else json.dumps({k: report.get(k) for k in ("verdict", "reason", "stage",
                                                                                   "artifact_faults", "stage_faults",
                                                                                   "ruler_mismatches", "baseline_arm")},
                                                    indent=2, ensure_ascii=False, default=str))
    print("VERDICT", report["verdict"])
    return 0 if report["verdict"] in PASS_VERDICTS else 1


if __name__ == "__main__":
    raise SystemExit(main())
