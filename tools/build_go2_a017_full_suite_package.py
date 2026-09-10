"""Build the G-A017 full-suite server package (work id G-A027).

One upload, one command, one result ZIP.  This package trains NOTHING.

WHY THIS RUN EXISTS
  G-A017 (Pilot-01 + track_lin_vel_xy_exp 1.2->1.4, single variable) was
  recorded as INTERNAL_EARLY_KILL_FAIL on 260904.  The 260907 re-audit and the
  engine 1.5.0 repair showed why that verdict was wrong:

    - both arms were measured by posture_gate_v2, so the pair is symmetric
    - the baseline arm walks (Pilot-01, POLICY_LOCOMOTES on 69/69 cases)
    - the candidate improved by +3.707916/70 on the tier-1 scale
    - not one scenario product regressed
    - the sole kill clause was G4's survival *factor* (-0.21875), while G4's
      own product rose (+0.015871) because tracking gained more than survival
      lost.  Engine 1.5.0 gates the product, and re-adjudicating the stored
      artifacts now returns INTERNAL_EARLY_KILL_PASS.

  Because the run was killed at tier-1 it never received seeds 202/303 and
  never ran the 69-case suite.  It is the campaign's only surviving positive
  signal on a baseline that actually walks.  It does have a tier-1 absolute
  score (50.199157/70 vs Pilot-01's 46.491241/70 on that 7-case scale); what
  is missing is a score on the 69-case worst-case scale that Pilot-01's
  33.793106/70 comes from.  The two scales are not comparable with each other.

WHY PILOT-01 IS REMEASURED IN FULL
  Engine 1.5.0 also fixed G7: the 69-case runners never passed NCRC_EVAL_DR,
  so every dr_seed_* case re-ran G3 byte for byte.  Pilot-01's stored G7
  numbers are therefore G3 numbers.

  An earlier draft of this package refreshed only those three cases and reused
  Pilot-01's other 66, on the argument that nothing else had changed.  That
  argument does hold for this data -- every stored Pilot case carries a live
  height channel, so requiring both posture channels changes none of them, and
  NCRC_EVAL_DR was provably never set in the old environment.  But it stays an
  argument about numbers measured on another day by another engine build, and
  this campaign has already lost weeks to a comparison that rested on an
  argument instead of a measurement.  Remeasuring all 69 costs about half an
  hour and puts both arms on one evaluator binary on one day.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
A017_SOURCE = ROOT / "workspace" / "_keep" / "go2_g_a017_pilot_track_lin_vel_xy_140" / "training"
PILOT_SOURCE = ROOT / "workspace" / "_keep" / "go2_pilot_v2_baseline" / "policy"
OUTPUT = GO2 / "go2_a017_full_suite.zip"
PREFIX = Path("go2_a017_full_suite")
FIXED_TIMESTAMP = (2026, 9, 8, 0, 0, 0)
RUNNER = "server_run_go2_a017_full_suite.sh"

A017_MODEL_SHA = "0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4"
A017_ENV_SHA = "41050c084cd05e7646ce2cb4ac34e06a6870fb7a65b4f767c5714611b9a801ff"
PILOT_MODEL_SHA = "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d"
PILOT_ENV_SHA = "f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d"

# The candidate is Pilot-01 with exactly one dial moved.
A017_REWARDS = {
    "track_lin_vel_xy_exp": 1.4,
    "feet_air_time": 0.2,
    "lin_vel_z_l2": -2.0,
    "ang_vel_xy_l2": -0.05,
    "action_rate_l2": -0.01,
    "flat_orientation_l2": 0.0,
}
PILOT_REWARDS = dict(A017_REWARDS, track_lin_vel_xy_exp=1.2)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files() -> list[Path]:
    files = [
        GO2 / "train.py",
        GO2 / "play.py",
        GO2 / "pyproject.toml",
        GO2 / "go2_eval_telemetry.py",
        GO2 / "go2_policy_lineage.py",
        GO2 / "quadruped_rewards.py",
    ]
    files.extend(sorted((GO2 / "go2_task").glob("*.py")))
    return files


def env_rewards(env_yaml: bytes) -> dict[str, float]:
    """Read the six participant reward weights out of a serialized env.yaml.

    The policy's own env.yaml is the identity evidence for an evaluation-only
    run; the working tree's quadruped_rewards.py is irrelevant here because no
    training happens, so this checks the shipped artifact instead.
    """
    text = env_yaml.decode("utf-8", errors="replace")
    found: dict[str, float] = {}
    for name in A017_REWARDS:
        match = re.search(rf"\b{re.escape(name)}\b.{{0,800}}?weight:\s*([-\d.eE+]+)", text, re.S)
        if match:
            found[name] = float(match.group(1))
    return found


def check_rewards(label: str, env_bytes: bytes, expected: dict[str, float]) -> None:
    found = env_rewards(env_bytes)
    missing = [name for name in expected if name not in found]
    if missing:
        raise RuntimeError(f"{label} env.yaml: reward weights not found: {missing}")
    wrong = {k: (found[k], expected[k]) for k in expected if abs(found[k] - expected[k]) > 1e-9}
    if wrong:
        raise RuntimeError(f"{label} env.yaml reward mismatch (found, expected): {wrong}")


def build_payload() -> dict[str, bytes]:
    a017_model = (A017_SOURCE / "model_best.pt").read_bytes()
    a017_env = (A017_SOURCE / "env.yaml").read_bytes()
    pilot_model = (PILOT_SOURCE / "pilot_model_best.pt").read_bytes()
    pilot_env = (PILOT_SOURCE / "pilot_env.yaml").read_bytes()

    for label, data, expected in (
        ("G-A017 model_best.pt", a017_model, A017_MODEL_SHA),
        ("G-A017 env.yaml", a017_env, A017_ENV_SHA),
        ("Pilot-01 model_best.pt", pilot_model, PILOT_MODEL_SHA),
        ("Pilot-01 env.yaml", pilot_env, PILOT_ENV_SHA),
    ):
        if sha(data) != expected:
            raise RuntimeError(f"{label} SHA mismatch: {sha(data)}")

    check_rewards("G-A017", a017_env, A017_REWARDS)
    check_rewards("Pilot-01", pilot_env, PILOT_REWARDS)

    changed = [
        name for name in A017_REWARDS
        if abs(A017_REWARDS[name] - PILOT_REWARDS[name]) > 1e-9
    ]
    if changed != ["track_lin_vel_xy_exp"]:
        raise RuntimeError(f"candidate must differ from Pilot-01 in exactly one dial: {changed}")

    telemetry = (GO2 / "go2_eval_telemetry.py").read_text(encoding="utf-8")
    for marker in ("survival_proxy_v2", "posture_gate_v2", "POSTURE_UNMEASURED",
                   "POSTURE_COVERAGE_INSUFFICIENT", "POSTURE_FALL_VERDICT_AMBIGUOUS",
                   "KINEMATICS_NONFINITE"):
        if marker not in telemetry:
            raise RuntimeError(f"telemetry is missing the repaired posture gate: {marker}")
    if "measured = math.isfinite(grav_z) and height_rel is not None" not in telemetry:
        raise RuntimeError("telemetry still accepts a single posture channel")
    if "upright = bool(tilt_ok and height_ok) if measured else None" not in telemetry:
        raise RuntimeError("telemetry still scores an unobserved row upright")
    if "if height_rel is not None and not math.isfinite(height_rel):" not in telemetry:
        raise RuntimeError("telemetry still accepts a non-finite height as a reading")

    runner = (GO2 / RUNNER).read_text(encoding="utf-8")
    if 'push_env+=("NCRC_EVAL_DR=1")' not in runner or "rough_forward|rough_lateral|dr_seed_*" in runner:
        raise RuntimeError("runner still re-runs G3 in place of G7")
    # The server has no system python3.  A hard-coded interpreter stops the run
    # at preflight, which is what happened on 260909, so the runner must resolve
    # one and the check it runs must be a shipped file rather than stdin.
    if "python3 - " in runner or "command -v python3 >/dev/null 2>&1 ||" in runner:
        raise RuntimeError("runner still hard-codes python3 for the posture check")
    for marker in ('PY=("$ISAACLAB_SH" -p)', '"${PY[@]}" "$POSTURE_CHECK"'):
        if marker not in runner:
            raise RuntimeError(f"runner does not resolve an interpreter: {marker}")

    registry = json.loads((GO2 / "config" / "go2_self_eval_registry.json").read_text(encoding="utf-8"))
    if registry["score"].get("tracking_proxy_std") is None:
        raise RuntimeError("registry does not publish tracking_proxy_std")

    payload: dict[str, bytes] = {}
    # All three roles get a byte-identical source tree so the evaluator cannot
    # differ between the arms. candidate/ is shipped but unused (no training).
    for role in ("candidate", "a017", "pilot"):
        for path in source_files():
            rel = path.relative_to(GO2).as_posix()
            payload[f"{role}/{rel}"] = path.read_bytes()
    payload["a017/exported/model_best.pt"] = a017_model
    payload["a017/exported/env.yaml"] = a017_env
    payload["pilot/exported/model_best.pt"] = pilot_model
    payload["pilot/exported/env.yaml"] = pilot_env
    payload["go2_self_eval_registry.json"] = (
        GO2 / "config" / "go2_self_eval_registry.json"
    ).read_bytes()
    for name in ("package_go2_result.py", "posture_contract_check.py", RUNNER):
        payload[name] = (GO2 / name).read_bytes()
    payload["README.txt"] = README.encode("utf-8")

    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


README = """GO2 G-A017 FULL SUITE  (work id G-A027)
=========================================

This package trains NOTHING.  It measures.

WHY
  G-A017 is Pilot-01 with one reward dial moved: track_lin_vel_xy_exp
  1.2 -> 1.4.  On 260904 it was recorded as a tier-1 failure.  The 260907
  re-audit found that verdict was produced by a defective gate:

    total points          +3.707916 / 70   (candidate over baseline)
    scenario products     6 of 7 improved, 0 regressed
    kill clause fired on  G4 survival factor -0.21875
    but G4's own product  +0.015871   (tracking gained more than survival lost)

  Engine 1.5.0 gates the scenario product, which is what the official form
  scores (시나리오 점수 = 생존율 x 추종 점수).  Re-adjudicating the stored
  G-A017 artifacts under the repaired gate returns INTERNAL_EARLY_KILL_PASS
  with both arms measured by the same evaluator and both arms walking.

  Because the run was killed at tier-1 it never received seeds 202/303 and
  never ran the 69-case suite.  It has a tier-1 absolute score
  (50.199157/70, against Pilot-01's 46.491241/70 on that same 7-case scale);
  what it lacks is a score on the 69-case worst-case scale that Pilot-01's
  33.793106/70 comes from.  The two scales are not comparable with each other.
  This run produces the missing one, for both policies, on the same day.

WHAT IT DOES
  1  frozen G-A017, all 69 G1-G7 case-runs (23 cases x seeds 101/202/303),
     posture-gated, with real domain randomization on G7
  2  frozen Pilot-01, the same 69 case-runs on the same evaluator binary
  3  one video per scenario G1-G7, so the numbers have a witness
  4  one-file result ZIP

  No training happens and no reward file is edited, so no submission candidate
  and no training artifact can change.  The one thing this run can destroy is
  its own previous output: launching it again writes to the same KEEP tree, so
  it refuses to start when results are already there unless you pass
  GO2_RESUME=1 or GO2_DISCARD_PREVIOUS=1.

RUN
  unzip go2_a017_full_suite.zip -d /workspace
  bash /workspace/go2_a017_full_suite/server_run_go2_a017_full_suite.sh

  It starts inside tmux and returns immediately.
  Finish marker:  [DONE] GO2_A017_FULL_SUITE_RESULT_READY

  Estimate ~1h45m from prior wall time.  It is an estimate, not a cap: nothing
  in the script stops the run when it is exceeded.

DOWNLOAD
  /workspace/_keep/GO2_A017_FULL_SUITE_RESULT.zip
  /workspace/_keep/GO2_A017_FULL_SUITE_RESULT.zip.sha256

GATES BUILT INTO THE RUNNER
  - each staged policy SHA must equal its frozen SHA, or the run aborts
  - every case summary must carry survival_proxy_source = posture_gate_v2,
    or that case FAILS rather than being banked on the old metric
  - a case FAILS if its posture was only partly observed, and also if the
    unobserved rows could have changed which robots counted as fallen: a
    missing frame is not evidence that the robot was standing
  - a case FAILS if any row carried a non-finite position or velocity.  inf
    clears every threshold in the gate, so an exploded step would otherwise
    read as a perfectly upright robot
  - all 69 case-runs per policy and all 7 videos must exist before packaging
  - a resume re-runs any case whose policy, case, seed, argv, step count or
    evaluator hash differs from what produced the stored summary
  - a second default launch refuses to overwrite an undownloaded result

PRE-REGISTERED READING (fixed before the run, not renegotiated after)
  Two questions are answered separately, because a screening result and a
  submission decision are not the same judgement and were previously conflated.

  Q1 SCREENING -- is the dial worth keeping?
     Compare the two 69-case scorecards.  A higher weighted total with no
     scenario product regression past the gate means the dial is kept and
     G-A017 becomes the frozen baseline that later single-variable runs are
     measured against.  This is a relative judgement between two policies on
     one ruler, and it is all this run can settle.

  Q2 SUBMISSION -- may either policy be submitted as our Go2 entry?
     Judged only by the registry's own bar in go2_self_eval_registry.json
     (score.internal_gates), which is stricter than Q1 and is not renegotiated
     here: every scenario needs survival >= 0.95 AND tracking >= 0.70, the
     weighted proxy needs >= 0.70, the self-assessment total needs >= 70, and
     seeds 101/202/303 must all be present.  On the tier-1 data BOTH policies
     are INTERNAL_GATE_FAIL, so the expected outcome of this run is a better
     relative number and a still failing absolute one.  Which factor fails
     matters and was previously stated wrongly: on the candidate G3 misses both
     floors, G4 and G5 miss on SURVIVAL with tracking already above 0.70
     (0.7286 and 0.7217), and G7 misses on tracking alone.  The next dial is
     chosen from that breakdown, so getting it backwards would send the search
     after the wrong factor.  A policy that wins Q1 and loses Q2 is the new
     screening baseline, not the entry.

  Three outcomes for Q1, decided in advance:

    candidate total above Pilot-01, no scenario product regression past the limit
        -> dial kept; G-A017 becomes the frozen screening baseline
    candidate total above Pilot-01 but a scenario product regressed past gate
        -> record both, keep Pilot-01 as the screening baseline, and read the
           videos before promoting anything
    candidate total at or below Pilot-01
        -> the tier-1 gain did not survive the wider case set.  Pilot-01 stays
           the screening baseline.  This is one training run at one value, so
           it closes 1.4 as a value, not the direction as a whole.

  This run does not itself select a next reward variable.  The three evaluation
  seeds are three replays of one trained policy, not three independent training
  seeds, so they bound measurement noise and not training variance.
  Official evaluator and official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def build() -> int:
    payload = build_payload()
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo((PREFIX / name).as_posix(), date_time=FIXED_TIMESTAMP)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)

    with zipfile.ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        names = archive.namelist()
        if len(names) != len(payload):
            raise RuntimeError("member count mismatch")
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError(f"unsafe member: {name}")

    digest = sha(OUTPUT.read_bytes())
    OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="utf-8"
    )
    print(f"built  {OUTPUT}")
    print(f"members {len(payload)}   size {OUTPUT.stat().st_size / 1_048_576:.1f} MB")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
