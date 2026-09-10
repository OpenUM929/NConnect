"""Contract test for the G-A017 full-suite package (work id G-A027).

Run:  python tools/test_go2_a017_full_suite_contract.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a017_full_suite_package as pkg  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


print("[1] the package builds and is internally consistent")
payload = pkg.build_payload()
check("candidate policy is present", "a017/exported/model_best.pt" in payload)
check("reference policy is present", "pilot/exported/model_best.pt" in payload)
check("runner is present", pkg.RUNNER in payload)
check("registry is present", "go2_self_eval_registry.json" in payload)
check(
    "all three roles ship a byte-identical evaluator",
    len({payload[f"{r}/go2_eval_telemetry.py"] for r in ("candidate", "a017", "pilot")}) == 1,
)
check(
    "all three roles ship a byte-identical play.py",
    len({payload[f"{r}/play.py"] for r in ("candidate", "a017", "pilot")}) == 1,
)
manifest = payload["PACKAGE_SHA256SUMS.txt"].decode("utf-8").splitlines()
check(
    "manifest covers every member except itself",
    len(manifest) == len(payload) - 1,
    f"{len(manifest)} vs {len(payload) - 1}",
)
recomputed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in manifest}
check(
    "every manifest hash matches its member",
    all(hashlib.sha256(payload[n]).hexdigest() == h for n, h in recomputed.items()),
)

print("[2] the two policies differ in exactly one reward dial")
a017 = pkg.env_rewards(payload["a017/exported/env.yaml"])
pilot = pkg.env_rewards(payload["pilot/exported/env.yaml"])
diff = sorted(k for k in a017 if abs(a017[k] - pilot.get(k, a017[k])) > 1e-9)
check("exactly one dial moved", diff == ["track_lin_vel_xy_exp"], f"got {diff}")
check(
    "the dial moved 1.2 -> 1.4",
    abs(pilot["track_lin_vel_xy_exp"] - 1.2) < 1e-9 and abs(a017["track_lin_vel_xy_exp"] - 1.4) < 1e-9,
    f"got {pilot.get('track_lin_vel_xy_exp')} -> {a017.get('track_lin_vel_xy_exp')}",
)

print("[3] the runner carries the repaired evaluator contract")
runner = payload[pkg.RUNNER].decode("utf-8")
check("no CRLF in the shipped runner", "\r\n" not in runner)
check("G7 has its own case branch", "rough_forward|rough_lateral|dr_seed_*" not in runner)
check("G7 passes NCRC_EVAL_DR", 'push_env+=("NCRC_EVAL_DR=1")' in runner)
check("candidate SHA is pinned", pkg.A017_MODEL_SHA in runner)
check("reference SHA is pinned", pkg.PILOT_MODEL_SHA in runner)
# A substring test is not a value test: measurement_contract carries the literal
# "posture_gate_v2" on a summary whose survival number is null, so the retired
# grep passed on exactly the file it existed to reject.
check("every case must carry posture evidence", "posture_ok() {" in runner
      and 'posture_ok "$out/summary.json"' in runner)
check("the retired substring test is gone",
      "grep -q 'posture_gate_v2' \"$out/summary.json\"" not in runner)
# Both policies are measured in full on the same evaluator on the same day; the
# earlier plan refreshed only Pilot-01's three G7 cases and reused 66 measured on
# a different build.
check("both policies run the full suite",
      "run_full_suite a017 " in runner and "run_full_suite pilot " in runner)
check("no partial G7-only Pilot arm remains", "pilot_g7" not in runner)
check("69 summaries are required per policy", '== 69' in runner)
check("7 videos are required", '== 7' in runner)
# The only train.py reference allowed is the pgrep guard that refuses to start
# while somebody else's training is live.
check("the run never invokes train.py", "-p train.py" not in runner)
check(
    "train.py appears only in the concurrency guard",
    all("pgrep" in line for line in runner.splitlines() if "train.py" in line),
)
proc = subprocess.run(
    ["bash", "-n", str(GO2 / pkg.RUNNER)], capture_output=True, text=True
)
check("runner parses under bash -n", proc.returncode == 0, proc.stderr.strip())

print("[4] the archive on disk matches the payload")
if pkg.OUTPUT.is_file():
    with zipfile.ZipFile(pkg.OUTPUT) as archive:
        names = archive.namelist()
        check("archive CRCs are intact", archive.testzip() is None)
        check("member count matches", len(names) == len(payload), f"{len(names)} vs {len(payload)}")
        check(
            "every member is under the package prefix and path-safe",
            all(n.startswith("go2_a017_full_suite/") and ".." not in Path(n).parts for n in names),
        )
        check(
            "the runner is executable in the archive",
            (archive.getinfo(f"go2_a017_full_suite/{pkg.RUNNER}").external_attr >> 16) & 0o111 != 0,
        )
    digest = hashlib.sha256(pkg.OUTPUT.read_bytes()).hexdigest()
    recorded = pkg.OUTPUT.with_suffix(pkg.OUTPUT.suffix + ".sha256").read_text(encoding="utf-8")
    check("recorded sha256 matches the archive", digest in recorded)
else:
    print("  skip archive checks (run tools/build_go2_a017_full_suite_package.py first)")

print("[5] the stored G-A017 artifacts justify this run")
from go2_fixed_eval_report import build_policy, instrument_mismatch  # noqa: E402
from go2_tuning_eval_report import tier1_decision  # noqa: E402

K = ROOT / "workspace" / "_keep" / "go2_g_a017_pilot_track_lin_vel_xy_140"
if (K / "meta" / "tier1_registry.json").is_file():
    reg = K / "meta" / "tier1_registry.json"
    base = build_policy(K / "evaluation" / "baseline_tier1", reg, {})
    cand = build_policy(K / "evaluation" / "candidate", reg, {})
    gates = json.loads((K / "meta" / "G_A017_pilot_track_lin_vel_xy_140.json").read_text(encoding="utf-8"))
    gates = dict(gates["evaluation"]["gates"])
    gates.setdefault("max_scenario_proxy_regression", gates["max_survival_regression"])
    decision = tier1_decision(base, cand, gates)
    check("the two arms used the same ruler", instrument_mismatch(base, cand) == [])
    check(
        "the baseline arm walks",
        base["locomotion"]["verdict"] == "POLICY_LOCOMOTES",
        base["locomotion"]["verdict"],
    )
    check(
        "the candidate arm walks",
        cand["locomotion"]["verdict"] == "POLICY_LOCOMOTES",
        cand["locomotion"]["verdict"],
    )
    check(
        "the repaired gate returns INTERNAL_EARLY_KILL_PASS",
        decision["status"] == "INTERNAL_EARLY_KILL_PASS",
        f"{decision['status']} {decision['failure_reasons']}",
    )
    check(
        "the measured delta is +3.707916/70",
        abs(decision["candidate_minus_baseline_points_70"] - 3.707916) < 5e-6,
        str(decision["candidate_minus_baseline_points_70"]),
    )
    # G6's product did move against the candidate, by -0.006756.  The claim the
    # package may make is that nothing regressed *past the limit*, and that the
    # verdict does not depend on the substituted limit: it holds from 0.007 up.
    check(
        "no scenario product regressed past the limit",
        not any("scenario_proxy_regressed" in r for r in decision["failure_reasons"]),
    )
    check(
        "the worst product delta is reported, not hidden",
        abs(decision["worst_scenario_proxy_delta"] + 0.006756232448085542) < 1e-12,
        str(decision["worst_scenario_proxy_delta"]),
    )
    check(
        "the verdict does not rest on the substituted limit",
        all(
            tier1_decision(base, cand, dict(gates, max_scenario_proxy_regression=limit))["status"]
            == "INTERNAL_EARLY_KILL_PASS"
            for limit in (0.007, 0.05, 0.1)
        ),
    )
    check(
        "the G4 survival regression is recorded but not a kill clause",
        "G4" in decision["survival_regressions_observed"] and decision["failure_reasons"] == [],
    )
else:
    print("  skip (G-A017 artifacts not present)")

# --------------------------------------------------------------------------
# 6. A resume must re-run any case whose conditions changed.  This is a
#    behavioural test, not a search for variable names: the fingerprint
#    expressions are lifted out of the runner and evaluated.
# --------------------------------------------------------------------------
print("[6] resume fingerprints respond to every condition that changes a result")


def _extract(text: str, start: str, end: str) -> str:
    head = text.index(start)
    return text[head : text.index(end, head) + len(end)]


def _hash(block: str, assignments: dict[str, str], array: str = "") -> str:
    script = "set -eu\n"
    for name, value in assignments.items():
        script += f"{name}={value!r}\n"
    script += array
    script += block.replace("local fingerprint\n", "").replace("local vmodel_sha venv_sha\n", "")
    script += '\nprintf "%s" "${fingerprint:-$vfingerprint}"\n'
    done = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    if done.returncode != 0:
        return "ERROR:" + done.stderr.strip()[:200]
    return done.stdout.strip()


eval_block = _extract(runner, "  local fingerprint\n", "| sha256sum | awk '{print $1}'\n  )")
eval_base = {
    "ACTIVE_MODEL_SHA": "model", "ACTIVE_ENV_SHA": "envcfg", "scenario": "G7",
    "case_id": "dr_seed_101", "seed": "101", "EVAL_STEPS": "1000",
    "EVALUATOR_SHA": "evaluator", "DR_MODE": "0", "PUSH_X": "", "PUSH_Y": "",
}
CMD = "cmd=(play.py --task Quadruped-v0)\n"
reference = _hash(eval_block, eval_base, CMD)
check("the eval fingerprint evaluates", bool(reference) and not reference.startswith("ERROR"), reference)
# argv alone was the old fingerprint's idea of "the conditions".  DR_MODE, PUSH_X
# and PUSH_Y reach play.py as environment variables and never appear in cmd, so
# two runs differing only in those hashed identically and a resume banked either.
for field, changed in (
    ("DR_MODE", "1"), ("PUSH_X", "0.50"), ("PUSH_Y", "-0.50"),
    ("EVAL_STEPS", "1001"), ("EVALUATOR_SHA", "other"), ("ACTIVE_MODEL_SHA", "other"),
    ("ACTIVE_ENV_SHA", "other"), ("seed", "202"),
):
    check(
        f"changing {field} changes the eval fingerprint",
        _hash(eval_block, dict(eval_base, **{field: changed}), CMD) != reference,
    )

video_block = _extract(runner, "  local vmodel_sha venv_sha\n", "| sha256sum | awk '{print $1}')")
# The two sha256sum calls at the top of the block read real files; point them at
# stand-ins so the expression can be evaluated here.
video_block = video_block.replace('sha256sum "$model"', 'printf "%s" "$model" | sha256sum')
video_block = video_block.replace('sha256sum "$env"', 'printf "%s" "$env" | sha256sum')
video_base = {
    "model": "policy1.pt", "env": "env1.yaml", "scenario": "G7", "case_id": "dr_seed_101",
    "seed": "101", "VIDEO_STEPS": "500", "EVALUATOR_SHA": "evaluator",
    "DR_MODE": "1", "PUSH_X": "", "PUSH_Y": "",
}
video_reference = _hash(video_block, video_base)
check("the video fingerprint evaluates",
      bool(video_reference) and not video_reference.startswith("ERROR"), video_reference)
# The old video fingerprint omitted the policy entirely, so a recording of one
# robot satisfied a resume for a different robot under the same filename.
for field, changed in (("model", "policy2.pt"), ("env", "env2.yaml"),
                       ("DR_MODE", "0"), ("VIDEO_STEPS", "600"), ("seed", "202")):
    check(
        f"changing {field} changes the video fingerprint",
        _hash(video_block, dict(video_base, **{field: changed})) != video_reference,
    )

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)}: {', '.join(FAILURES)}")
    raise SystemExit(1)
print("all G-A017 full-suite package contract checks passed")
