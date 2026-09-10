"""Contract test for the 260908 Go2 scoring repair (engine 1.5.0).

Every case below is a defect the re-audit found in real campaign artifacts. The
test fails if any of them can happen again.

Run:  python tools/test_go2_scoring_repair_contract.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ENGINE))

import go2_fixed_eval_report as fer  # noqa: E402
import go2_tuning_eval_report as ter  # noqa: E402
import go2_tuning_config as cfg  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


# --------------------------------------------------------------------------
# 1. G6 must score recovery_rate_upright, not the legacy recovery_rate.
# --------------------------------------------------------------------------
print("[1] G6 recovery metric")
summary = {
    "survival_proxy": 1.0,
    "tracking_xy_rmse": 0.10,
    "post_push_tracking_xy_rmse": 0.10,
    "recovery": {"recovery_rate": 1.0, "recovery_rate_upright": 0.40},
}
proxy = fer._case_proxy("push_pos_x", summary)
check(
    "push case uses recovery_rate_upright",
    proxy["recovery_rate"] == 0.40 and proxy["recovery_metric"] == "recovery_rate_upright",
    f"got recovery={proxy['recovery_rate']} metric={proxy['recovery_metric']}",
)
legacy = fer._case_proxy(
    "push_pos_x",
    {**summary, "recovery": {"recovery_rate": 1.0}},
)
check(
    "missing upright field is tagged legacy, not scored silently",
    legacy["recovery_metric"] == "legacy_recovery_rate",
    f"got {legacy['recovery_metric']}",
)

# --------------------------------------------------------------------------
# 2. tracking std comes from the registry, not a module constant.
# --------------------------------------------------------------------------
print("[2] tracking std source")
registry = json.loads(
    (ENGINE / "config" / "go2_self_eval_registry.json").read_text(encoding="utf-8")
)
check(
    "registry publishes tracking_proxy_std",
    registry["score"].get("tracking_proxy_std") == 0.5,
    f"got {registry['score'].get('tracking_proxy_std')}",
)
check(
    "_track honours an explicit std",
    abs(fer._track(0.5, 1.0) - fer.math.exp(-0.25)) < 1e-12,
)

# --------------------------------------------------------------------------
# 3. Scenario aggregation must be self-consistent: proxy == survival * tracking.
# --------------------------------------------------------------------------
print("[3] scenario aggregation order")


def _build(tmp: Path, cases: dict[str, dict], seeds: list[int]) -> dict:
    reg = json.loads(json.dumps(registry))
    reg["score"]["internal_gates"]["required_evaluation_seeds"] = seeds
    reg["scenarios"] = [
        {
            "id": "G3",
            "name": "거친 지형",
            "terrain": "험지",
            "weight": 1.0,
            "internal_cases": sorted(cases),
            "required_metrics": [],
            "required_video": False,
        }
    ]
    reg_path = tmp / "registry.json"
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    for case_id, payload in cases.items():
        for seed in seeds:
            out = tmp / "cases" / f"seed_{seed}" / case_id
            out.mkdir(parents=True, exist_ok=True)
            (out / "summary.json").write_text(json.dumps(payload), encoding="utf-8")
    return fer.build_policy(tmp, reg_path, {})


def _case(survival: float, rmse: float, speed: float = 0.5, source: str = "posture_gate_v2") -> dict:
    return {
        "schema_version": 2,
        "survival_proxy": survival,
        "tracking_xy_rmse": rmse,
        "speed_xy_mean": speed,
        "survival_proxy_source": source,
        "posture_gate": {"tilt_cos_max": 0.5, "height_rel_min_m": 0.18, "hold_s": 0.5, "grace_s": 0.5},
    }


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    # Deliberately split the minimums across two cases: A has the lower survival,
    # B has the lower tracking. The old code multiplied min(A.survival) by
    # min(B.tracking) and reported a product that matched neither case.
    report = _build(
        tmp,
        {"rough_forward": _case(0.60, 0.20), "rough_lateral": _case(0.95, 0.60)},
        [101],
    )
    g3 = report["scenarios"]["G3"]
    check(
        "reported proxy equals reported survival x tracking",
        abs(g3["scenario_proxy"] - g3["survival_proxy"] * g3["tracking_proxy"]) < 1e-12,
        f"{g3['scenario_proxy']} vs {g3['survival_proxy'] * g3['tracking_proxy']}",
    )
    check(
        "per-case floors are still published for the stability gate",
        "survival_proxy_min_any_case" in g3 and "tracking_proxy_min_any_case" in g3,
    )
    check(
        "aggregation order is stated in the report",
        "min_over_cases_of" in g3.get("aggregation", ""),
    )

# --------------------------------------------------------------------------
# 4. A policy that stands still cannot be reported as a healthy baseline.
# --------------------------------------------------------------------------
print("[4] locomotion floor")
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    # Default-01's own G-A006 numbers: survival 1.0 under termination-only, but
    # 0.027 m/s against a 0.75 m/s command.
    stationary = _build(
        tmp,
        {"rough_forward": _case(1.0, 0.7369, speed=0.0267)},
        [101],
    )
    check(
        "stationary policy is flagged",
        stationary["locomotion"]["verdict"] == "POLICY_DOES_NOT_LOCOMOTE",
        f"got {stationary['locomotion']['verdict']}",
    )
    check(
        "stationary policy cannot report INTERNAL_GATE_PASS",
        stationary["status"] != "INTERNAL_GATE_PASS",
        f"got {stationary['status']}",
    )

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    walking = _build(tmp, {"rough_forward": _case(1.0, 0.10, speed=0.74)}, [101])
    check(
        "walking policy is not flagged",
        walking["locomotion"]["verdict"] == "POLICY_LOCOMOTES",
        f"got {walking['locomotion']['verdict']}",
    )

# --------------------------------------------------------------------------
# 5. Asymmetric instrument fingerprints must void the comparison.
# --------------------------------------------------------------------------
print("[5] instrument symmetry")
with tempfile.TemporaryDirectory() as td:
    base_dir, cand_dir = Path(td) / "b", Path(td) / "c"
    base_dir.mkdir()
    cand_dir.mkdir()
    base = _build(base_dir, {"rough_forward": _case(1.0, 0.10, source="termination_only_v1")}, [101])
    cand = _build(cand_dir, {"rough_forward": _case(0.90, 0.08, source="posture_gate_v2")}, [101])
    mismatch = fer.instrument_mismatch(base, cand)
    check(
        "different survival definitions are detected",
        any("survival_proxy_sources" in item for item in mismatch),
        f"got {mismatch}",
    )
    # Absence of a fingerprint is not agreement on one.  Engine 1.5.0 compared the
    # two dicts field by field, so two arms that recorded nothing compared equal.
    check(
        "two arms with no fingerprint at all are refused, not matched",
        fer.instrument_mismatch({}, {}) != [],
        f"got {fer.instrument_mismatch({}, {})}",
    )
    check(
        "an arm scored on the legacy recovery rate cannot be compared",
        any(
            "legacy_recovery" in reason
            for reason in ter.comparison_blockers(
                dict(cand, legacy_recovery_cases=["push_pos_x"]), cand
            )
        ),
    )
    gates = {
        "min_total_points_delta": 1.0,
        "max_survival_regression": 0.10,
        "max_scenario_proxy_regression": 0.10,
        "minimum_points_70": 60.0,
        "required_survival_proxy": 0.95,
        "required_tracking_proxy": 0.70,
    }
    decision = ter.tier1_decision(base, cand, gates)
    check(
        "tier-1 refuses an asymmetric pair instead of publishing a delta",
        decision["status"] == "INTERNAL_MEASUREMENT_INVALID",
        f"got {decision['status']}",
    )
    check(
        "no delta is published for a void comparison",
        decision["candidate_minus_baseline_points_70"] is None
        and decision["scenario_deltas"] is None
        and decision["comparison_published"] is False,
    )
    check(
        "each arm's own numbers survive for diagnosis",
        decision["baseline_diagnostics"]["points_70"] is not None
        and decision["candidate_diagnostics"]["points_70"] is not None,
    )

# --------------------------------------------------------------------------
# 6. The tier-1 kill clause gates the product, not the survival factor.
# --------------------------------------------------------------------------
print("[6] tier-1 gate is on the scenario product")


def _report(points: float, scenarios: dict[str, tuple[float, float]]) -> dict:
    return {
        "simulation_points_70": points,
        "instrument": {
            "tracking_proxy_std": 0.5,
            "survival_proxy_sources": ["posture_gate_v2"],
            "telemetry_schema_versions": ["3"],
            "posture_gate_params": ["{}"],
            "measurement_contracts": ["posture_gate_v2/both_channels_required/no_v1_fallback"],
        },
        "locomotion": {"verdict": "POLICY_LOCOMOTES"},
        "scenarios": {
            key: {
                "survival_proxy": s,
                "tracking_proxy": t,
                "scenario_proxy": s * t,
            }
            for key, (s, t) in scenarios.items()
        },
    }


# G-A017's real shape: +3.71/70 overall, G4 survival -0.219 but G4 product +0.016.
baseline = _report(46.4912409491015, {"G4": (1.00, 0.4000)})
candidate = _report(50.19915737233102, {"G4": (0.78125, 0.5232)})
gates = {
    "min_total_points_delta": 1.0,
    "max_survival_regression": 0.10,
    "max_scenario_proxy_regression": 0.10,
    "minimum_points_70": 60.0,
    "required_survival_proxy": 0.95,
    "required_tracking_proxy": 0.70,
}
decision = ter.tier1_decision(baseline, candidate, gates)
check(
    "survival factor alone no longer kills a run whose product improved",
    decision["status"] == "INTERNAL_EARLY_KILL_PASS",
    f"got {decision['status']} reasons={decision['failure_reasons']}",
)
check(
    "the survival regression is still reported",
    "G4" in decision["survival_regressions_observed"],
    f"got {decision['survival_regressions_observed']}",
)

# A candidate that genuinely traded away more than it gained must still die.
worse = _report(50.19915737233102, {"G4": (0.50, 0.4000)})
decision2 = ter.tier1_decision(baseline, worse, gates)
check(
    "a real product regression still fails",
    decision2["status"] == "INTERNAL_EARLY_KILL_FAIL"
    and any("scenario_proxy_regressed" in r for r in decision2["failure_reasons"]),
    f"got {decision2['status']} {decision2['failure_reasons']}",
)

# A non-walking baseline voids the comparison outright.
dead_baseline = _report(17.90699218052112, {"G4": (1.00, 0.4000)})
dead_baseline["locomotion"] = {"verdict": "POLICY_DOES_NOT_LOCOMOTE"}
decision3 = ter.tier1_decision(dead_baseline, candidate, gates)
check(
    "a non-walking baseline voids the comparison",
    decision3["status"] == "INTERNAL_MEASUREMENT_INVALID"
    and "baseline_does_not_locomote" in decision3["blocking_reasons"],
    f"got {decision3['status']} {decision3['blocking_reasons']}",
)

# --------------------------------------------------------------------------
# 7. Engine and schema versions agree; Default-01 is not an admissible baseline.
# --------------------------------------------------------------------------
print("[7] engine contract")
schema = json.loads(
    (ENGINE / "config" / "go2_tuning_experiment_schema.json").read_text(encoding="utf-8")
)
check(
    "JSON schema engine_version matches the runtime constant",
    schema["properties"]["engine_version"]["const"] == cfg.ENGINE_VERSION,
    f"schema={schema['properties']['engine_version']['const']} runtime={cfg.ENGINE_VERSION}",
)
for name in ("Default-01", "Chain-01"):
    check(
        f"{name} is marked inadmissible as a screening baseline",
        cfg.FROZEN_BASELINES[name].get("locomotion_status")
        == "BASELINE_INVALID_PENDING_MEASUREMENT",
        f"got {cfg.FROZEN_BASELINES[name].get('locomotion_status')}",
    )
check(
    "Pilot-01 is the admissible baseline",
    cfg.FROZEN_BASELINES["Pilot-01"].get("locomotion_status")
    == "BASELINE_WALKS_VERIFIED_69_CASE",
    f"got {cfg.FROZEN_BASELINES['Pilot-01'].get('locomotion_status')}",
)
check(
    "every frozen baseline env SHA resolves to a file on disk",
    all(
        len(entry["env_sha256"]) == 64 for entry in cfg.FROZEN_BASELINES.values()
    ),
)

# --------------------------------------------------------------------------
# 7b. Re-scoring the real 69-case artifacts must reproduce the audited numbers.
# --------------------------------------------------------------------------
print("[7b] measured artifacts")
KEEP = ROOT / "workspace" / "_keep"
REGISTRY = ENGINE / "config" / "go2_self_eval_registry.json"
measured = [
    ("Default-01", KEEP / "go2_default_vs_pilot_v1/evaluation/default", 17.906992, "POLICY_DOES_NOT_LOCOMOTE"),
    ("Pilot-01 (v1 instrument)", KEEP / "go2_default_vs_pilot_v1/evaluation/pilot", 41.979898, "POLICY_LOCOMOTES"),
    ("Pilot-01 (v2 instrument)", KEEP / "go2_pilot_v2_baseline/evaluation/pilot_v2", 33.793106, "POLICY_LOCOMOTES"),
    ("Chain-01", KEEP / "go2_chain01_baseline/evaluation/chain01", 1.579102, "POLICY_DOES_NOT_LOCOMOTE"),
]
for label, root, points, verdict in measured:
    if not root.is_dir():
        print(f"  skip {label} (artifact not present)")
        continue
    report = fer.build_policy(root, REGISTRY, {})
    check(
        f"{label}: {points}/70",
        abs(report["simulation_points_70"] - points) < 5e-6,
        f"got {report['simulation_points_70']}",
    )
    check(
        f"{label}: {verdict}",
        report["locomotion"]["verdict"] == verdict,
        f"got {report['locomotion']['verdict']}",
    )

# --------------------------------------------------------------------------
# 8. Telemetry: both posture channels required, no silent v1 fallback.
# --------------------------------------------------------------------------
print("[8] telemetry posture contract")
telemetry = (ENGINE / "go2_eval_telemetry.py").read_text(encoding="utf-8")
check(
    "posture requires both channels",
    "measured = math.isfinite(grav_z) and height_rel is not None" in telemetry,
)
check(
    "no silent termination-only fallback on the scored field",
    '"survival_proxy": survival_v2,' in telemetry
    and "POSTURE_UNMEASURED" in telemetry,
)

# --------------------------------------------------------------------------
# 9. G7 must not re-run G3 in the 69-case runners.
# --------------------------------------------------------------------------
print("[9] G7 domain randomization")
for name in ("server_run_go2_pilot_v2_baseline.sh", "server_run_go2_chain01_baseline.sh"):
    text = (ENGINE / name).read_text(encoding="utf-8")
    check(
        f"{name}: dr_seed_* has its own branch",
        "rough_forward|rough_lateral|dr_seed_*" not in text and "dr_seed_*)" in text,
    )
    check(
        f"{name}: NCRC_EVAL_DR is passed for G7",
        'push_env+=("NCRC_EVAL_DR=1")' in text,
    )

# --------------------------------------------------------------------------
# 10. The operator training-history backup is on by default.
# --------------------------------------------------------------------------
print("[10] submission history backup")
runner = (ENGINE / "server_run_go2_tuning_engine_v1.sh").read_text(encoding="utf-8")
check(
    "NO_AUTO_SUBMIT is no longer hard-coded on",
    "NO_AUTO_SUBMIT=1 /workspace/IsaacLab" not in runner,
)
check(
    "the variable is unset unless the caller asks for it",
    "train_env+=(-u NO_AUTO_SUBMIT)" in runner,
)

# --------------------------------------------------------------------------
# 11. Absence wearing the shape of evidence, and the two paths that had no guard.
# --------------------------------------------------------------------------
print("[11] null placeholders, paired(), representative_decision()")

_NULLED = {
    "tracking_proxy_std": 0.5,
    "survival_proxy_sources": ["posture_gate_v2"],
    "telemetry_schema_versions": ["None"],
    "posture_gate_params": ["null"],
    "measurement_contracts": ["None"],
}
# The fingerprint is built with str() and json.dumps(), so an unrecorded field
# arrives as the string "None" -- non-empty, length one, and truthy.  Engine 1.5.1
# read that as a recorded value and called two such arms identically measured.
faults = fer.instrument_unusable({"instrument": dict(_NULLED)})
check("a fingerprint of stringified nulls is not a fingerprint", faults != [], f"got {faults}")
check(
    "both arms' faults are reported, not just the first",
    any(item.startswith("baseline_") for item in fer.instrument_mismatch(
        {"instrument": dict(_NULLED)}, {"instrument": dict(_NULLED)}))
    and any(item.startswith("candidate_") for item in fer.instrument_mismatch(
        {"instrument": dict(_NULLED)}, {"instrument": dict(_NULLED)})),
)
# measurement_contract was introduced in 1.5.1, so pre-1.5.1 cases legitimately
# have none.  That single absence is tolerated -- a known legacy schema whose
# posture thresholds were all recorded already names the ruler -- but it is
# reported rather than passed over in silence.
_GATE = json.dumps(
    {"grace_s": 0.5, "height_rel_min_m": 0.18, "hold_s": 0.5, "tilt_cos_max": 0.5},
    sort_keys=True,
)
_LEGACY = dict(_NULLED, telemetry_schema_versions=["2"], posture_gate_params=[_GATE])
check(
    "a pre-1.5.1 contract absence does not block when the schema is recorded",
    fer.instrument_unusable({"instrument": dict(_LEGACY)}) == [],
    f"got {fer.instrument_unusable({'instrument': dict(_LEGACY)})}",
)
check(
    "but it is recorded as a note",
    fer.instrument_notes({"instrument": dict(_LEGACY)}) != [],
)
check(
    "a null schema version is still fatal",
    fer.instrument_unusable({"instrument": dict(_LEGACY, telemetry_schema_versions=["None"])}) != [],
)

# --------------------------------------------------------------------------
# 12. The legacy tolerance must be a legacy allowlist, not "any non-null string".
# --------------------------------------------------------------------------
print("[12] legacy tolerance boundary and its separation from promotion")

# Engine 1.5.2 asked only whether the schema was present, single and non-null, so
# it explained away a missing contract on schema 4 -- a version that must carry one
# -- and on 999 and "banana", which name no ruler at all.
for _schema in ("3", "4", "5", "999", "banana", "2.0", "22", "2x"):
    _off_list = dict(_LEGACY, telemetry_schema_versions=[_schema])
    check(
        f"schema {_schema!r} may not use the pre-1.5.1 tolerance",
        fer.instrument_unusable({"instrument": _off_list}) != []
        and fer.instrument_notes({"instrument": _off_list}) == [],
        f"faults={fer.instrument_unusable({'instrument': _off_list})}",
    )
check(
    "only the recorded legacy schemas are on the list",
    fer.LEGACY_CONTRACTLESS_SCHEMAS == ("2",), fer.LEGACY_CONTRACTLESS_SCHEMAS,
)
check(
    "surrounding whitespace is normalised, not treated as a different schema",
    fer.instrument_unusable({"instrument": dict(_LEGACY, telemetry_schema_versions=[" 2 "])}) == [],
)

# "posture_gate_v2" names four thresholds.  A fingerprint that records "{}" for
# them has not pinned the ruler and so may not lean on the tolerance either.
for _params in ("{}", "null", '{"hold_s": 0.5}',
                json.dumps({"grace_s": 0.5, "height_rel_min_m": 0.18,
                            "hold_s": "banana", "tilt_cos_max": 0.5}, sort_keys=True)):
    _thin = dict(_LEGACY, posture_gate_params=[_params])
    check(
        f"posture params {_params!r} do not pin the gate",
        fer.instrument_unusable({"instrument": _thin}) != [],
        f"faults={fer.instrument_unusable({'instrument': _thin})}",
    )

# A modern arm that actually carries its contract is unaffected by all of this.
_MODERN = dict(_LEGACY, telemetry_schema_versions=["5"],
               measurement_contracts=["posture_gate_v2/both_channels_required"
                                      "/no_v1_fallback/row_and_env_coverage_0.99"
                                      "/missing_rows_not_upright/fall_verdict_unambiguous"])
check(
    "an arm carrying its own contract needs no tolerance",
    fer.instrument_unusable({"instrument": dict(_MODERN)}) == []
    and fer.instrument_notes({"instrument": dict(_MODERN)}) == [],
    f"faults={fer.instrument_unusable({'instrument': dict(_MODERN)})}",
)

# The tolerance is a screening convenience.  Promotion is the strictest reading in
# the engine, so a tolerated arm may not be promoted on that evidence at all.
_arm = {"instrument": dict(_LEGACY), "status": "SELF_ASSESSMENT_COMPLETE",
        "simulation_points_70": 60.0, "scenarios": {}, "seed_fractions": {},
        "locomotion": {"verdict": "LOCOMOTES"}}
_blockers = ter.representative_eligibility(_arm)
check(
    "a legacy-tolerated arm cannot be promoted",
    any(item.startswith("candidate_" + fer.LEGACY_TOLERANCE_PREFIX) for item in _blockers),
    _blockers,
)
check(
    "the same arm on a modern fingerprint is promotable",
    ter.representative_eligibility(dict(_arm, instrument=dict(_MODERN))) == [],
    ter.representative_eligibility(dict(_arm, instrument=dict(_MODERN))),
)
check(
    "and the blocked promotion publishes no points",
    ter.representative_decision(_arm, {"minimum_points_70": 0.0,
                                       "required_survival_proxy": 0.0,
                                       "required_tracking_proxy": 0.0})
    ["candidate_points_70"] is None,
)

with tempfile.TemporaryDirectory() as td:
    b_dir, c_dir = Path(td) / "b", Path(td) / "c"
    b_dir.mkdir(); c_dir.mkdir()
    arm_b = _build(b_dir, {"rough_forward": _case(1.0, 0.10, source="posture_gate_v2")}, [101])
    arm_c = _build(c_dir, {"rough_forward": _case(0.90, 0.08, source="posture_gate_v2")}, [101])

    # paired() was left behind when tier1_decision learned to suppress deltas, so
    # the same invalid pair still published pilot_minus_default from this path.
    voided = fer.paired(dict(arm_b, instrument={}), arm_c)
    check("paired() refuses an unusable pair", voided["decision"] == "INTERNAL_MEASUREMENT_INVALID",
          voided["decision"])
    check("paired() publishes no delta when it refuses",
          voided["pilot_minus_default"] is None and voided["per_scenario"] is None
          and voided["per_seed_delta"] is None)
    check("paired() says why", voided["blocking_reasons"] != [])
    check("paired() keeps each arm's own figures as diagnostics",
          voided["default"]["simulation_fraction"] is not None
          and voided["pilot"]["simulation_fraction"] is not None)
    check("a usable pair is still compared",
          fer.paired(arm_b, arm_c)["comparison_published"] is True)

    # representative_decision is the strictest reading in the engine and had the
    # weakest guard: it never looked at the fingerprint or the arm's status at all.
    rep_gates = {"minimum_points_70": 60.0, "required_survival_proxy": 0.95,
                 "required_tracking_proxy": 0.70}
    forged = {
        "status": "SELF_ASSESSMENT_LEGACY_METRIC",
        "instrument": {},
        "simulation_points_70": 69.9,
        "seed_fractions": {"101": 1.0, "202": 1.0, "303": 1.0},
        "scenarios": {f"G{i}": {"survival_proxy": 1.0, "tracking_proxy": 0.99} for i in range(1, 8)},
        "locomotion": {"verdict": "POLICY_LOCOMOTES"},
    }
    promotion = ter.representative_decision(forged, rep_gates)
    check("promotion refuses an arm with no recorded ruler",
          promotion["status"] == "INTERNAL_MEASUREMENT_INVALID", promotion["status"])
    check("promotion publishes no score when it refuses",
          promotion["candidate_points_70"] is None
          and promotion["promotion_published"] is False)
    check("promotion names both grounds",
          len(promotion["blocking_reasons"]) >= 2, promotion["blocking_reasons"])

# --------------------------------------------------------------------------
# 13. Promotion asks an all-case question, so it must read the per-case floors.
#     Round-4 audit C6.  A scenario's published score is the minimum over its
#     cases of (survival * tracking), and the factors printed beside it belong
#     to that one worst-product case.  Promotion read those factors, so a case
#     that failed a factor floor while carrying a better product was invisible
#     to the strictest reading in the engine.
# --------------------------------------------------------------------------
_REP_GATES = {"minimum_points_70": 60.0, "required_survival_proxy": 0.95,
              "required_tracking_proxy": 0.70}


def _scenario(survival, tracking, survival_floor=None, tracking_floor=None):
    return {
        "survival_proxy": survival,
        "tracking_proxy": tracking,
        "scenario_proxy": survival * tracking,
        "survival_proxy_min_any_case":
            survival if survival_floor is None else survival_floor,
        "tracking_proxy_min_any_case":
            tracking if tracking_floor is None else tracking_floor,
    }


def _promotable(g1):
    return {
        "status": "SELF_ASSESSMENT_COMPLETE",
        "instrument": dict(_MODERN),
        "simulation_points_70": 65.0,
        "seed_fractions": {"101": 0.9, "202": 0.9, "303": 0.9},
        "locomotion": {"verdict": "LOCOMOTES"},
        "scenarios": dict({"G1": g1},
                          **{f"G{i}": _scenario(0.99, 0.95) for i in range(2, 8)}),
    }


# The auditor's two synthetic cases, in one scenario:
#   case A  survival 0.96  tracking 0.71  product 0.6816  <- worst product
#   case B  survival 0.90  tracking 0.99  product 0.8910  <- fails the survival floor
_hidden = ter.representative_decision(
    _promotable(_scenario(0.96, 0.71, survival_floor=0.90, tracking_floor=0.71)),
    _REP_GATES,
)
check(
    "a case below the survival floor blocks promotion even when it is not the worst product",
    _hidden["status"] == "INTERNAL_REPRESENTATIVE_PROMOTION_FAIL"
    and "one_or_more_scenario_stability_gates_failed" in _hidden["failure_reasons"],
    f"got {_hidden['status']} {_hidden['failure_reasons']}",
)
check(
    "and the scenario is named on the floor reading, not the worst-product reading",
    _hidden["scenario_floor_failures"] == ["G1"]
    and _hidden["scenario_worst_product_factor_failures"] == [],
    f"floors={_hidden['scenario_floor_failures']} "
    f"worst={_hidden['scenario_worst_product_factor_failures']}",
)
check(
    "the published aggregate is untouched -- the fix names the shortfall, it does not rescore",
    _hidden["candidate_points_70"] == 65.0,
    _hidden["candidate_points_70"],
)
check(
    "an arm whose every case clears both floors is still promotable",
    ter.representative_decision(
        _promotable(_scenario(0.96, 0.71)), _REP_GATES,
    )["status"] == "INTERNAL_REPRESENTATIVE_PROMOTION_PASS",
)
# A report from an engine that never computed the floors cannot answer the
# all-case question.  That is a measurement fault, not a performance failure.
_stale = ter.representative_decision(
    _promotable({"survival_proxy": 0.96, "tracking_proxy": 0.71,
                 "scenario_proxy": 0.6816}),
    _REP_GATES,
)
check(
    "a report with no per-case floors is inadmissible rather than read optimistically",
    _stale["status"] == "INTERNAL_MEASUREMENT_INVALID"
    and any(item.startswith("candidate_scenario_case_floors_unusable")
            for item in _stale["blocking_reasons"]),
    f"got {_stale['status']} {_stale['blocking_reasons']}",
)
check(
    "and it publishes no promotion score",
    _stale["candidate_points_70"] is None and _stale["promotion_published"] is False,
)
check(
    "a promotion refused on a floor says by how much and against which threshold",
    _hidden["scenario_floor_shortfalls"] == ["G1.survival_proxy_min_any_case=0.9<0.95"],
    _hidden["scenario_floor_shortfalls"],
)

# --------------------------------------------------------------------------
# 13b. Round-5 audit.  Presence was the whole floor check, and NaN is present.
#      ``nan < 0.95`` is False, so a NaN floor was never compared to the gate at
#      all: it passed by losing the comparison.  Every value that is not a
#      finite number in [0, 1] is a measurement fault, not a performance result.
# --------------------------------------------------------------------------
_NAN = float("nan")
for _label, _value in (("NaN", _NAN), ("+Infinity", float("inf")),
                       ("-Infinity", float("-inf")), ("a bool", True),
                       ("a string", "0.99"), ("a negative", -0.1),
                       ("above one", 1.5)):
    _bad = ter.representative_decision(
        _promotable(_scenario(0.96, 0.71, survival_floor=_value)), _REP_GATES)
    check(
        f"a survival floor of {_label} is a measurement fault, not a pass",
        _bad["status"] == "INTERNAL_MEASUREMENT_INVALID"
        and any(item.startswith("candidate_scenario_case_floors_unusable")
                for item in _bad["blocking_reasons"])
        and _bad["candidate_points_70"] is None
        and _bad["scenario_floor_failures"] is None,
        f"got {_bad['status']} {_bad['blocking_reasons']}",
    )
    _bad_t = ter.representative_decision(
        _promotable(_scenario(0.96, 0.71, tracking_floor=_value)), _REP_GATES)
    check(
        f"and so is a tracking floor of {_label}",
        _bad_t["status"] == "INTERNAL_MEASUREMENT_INVALID",
        f"got {_bad_t['status']} {_bad_t['blocking_reasons']}",
    )
# The total is read by the same gate and loses the same comparison.
for _label, _value in (("NaN", _NAN), ("Infinity", float("inf")),
                       ("absent", None), ("a string", "65.0")):
    _bad_points = _promotable(_scenario(0.96, 0.71))
    _bad_points["simulation_points_70"] = _value
    _out = ter.representative_decision(_bad_points, _REP_GATES)
    check(
        f"a total of {_label} is a measurement fault, not a failed gate",
        _out["status"] == "INTERNAL_MEASUREMENT_INVALID"
        and any(item.startswith("candidate_simulation_points_70_unusable")
                for item in _out["blocking_reasons"]),
        f"got {_out['status']} {_out['blocking_reasons']}",
    )
# The control the audit asked for: normal values must still be admitted.
check(
    "and an arm whose floors are ordinary numbers is still promotable",
    ter.representative_decision(
        _promotable(_scenario(0.96, 0.71, survival_floor=0.95, tracking_floor=0.70)),
        _REP_GATES)["status"] == "INTERNAL_REPRESENTATIVE_PROMOTION_PASS",
)
check(
    "including the exact boundary values the gate names",
    ter.representative_decision(
        _promotable(_scenario(1.0, 1.0, survival_floor=0.0, tracking_floor=0.0)),
        _REP_GATES)["scenario_floor_failures"] == ["G1"],
)
# Screening is a relative question and must not inherit the absolute floors.
_screen_gates = dict(_REP_GATES, min_total_points_delta=1.0,
                     max_survival_regression=0.10,
                     max_scenario_proxy_regression=0.10)
check(
    "the absolute floors stay out of screening",
    ter.tier1_decision(
        _report(46.49, {"G4": (1.00, 0.4000)}),
        _report(50.19, {"G4": (0.78125, 0.5232)}),
        _screen_gates,
    )["status"] == "INTERNAL_EARLY_KILL_PASS",
)


print()
if FAILURES:
    print(f"FAILED {len(FAILURES)}: {', '.join(FAILURES)}")
    raise SystemExit(1)
print("all scoring-repair contract checks passed")
