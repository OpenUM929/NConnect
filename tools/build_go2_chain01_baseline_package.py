"""Build the Chain-01 terrain-curriculum server package (work id G-A023).

One upload, one command, one result ZIP.  This package trains nothing --
it evaluates the frozen Chain-01 checkpoint (Default-01 + track_lin_vel_xy_exp
1.0->1.2, single-variable verified, G-A011) across the full 69-case G1-G7
suite at seeds 101/202/303, with one video per scenario.  Chain-01 has never
been measured under the posture-gated evaluator or on terrain -- only its
tier-1 (seed-101-only) proxy score exists.  Three individual reward-weight
overlays on top of Chain-01 (G-A020 lin_vel_z_l2, G-A021 ang_vel_xy_l2,
G-A022 feet_air_time) have each failed the tier-1 gate, and the remaining
two participant-file dials (action_rate_l2, flat_orientation_l2) were both
already exhausted -- every coherent direction tried or ruled out -- before
the Chain-01 reset even began.  Chain-01 itself is therefore the campaign's
best verified point and needs its own real score.
"""

from __future__ import annotations

import ast
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
CHAIN01_SOURCE = ROOT / "workspace" / "_keep" / "go2_track_lin_vel_120_v1" / "training"
OUTPUT = GO2 / "go2_chain01_baseline.zip"
PREFIX = Path("go2_chain01_baseline")
FIXED_TIMESTAMP = (2026, 9, 5, 0, 0, 0)
RUNNER = "server_run_go2_chain01_baseline.sh"

CHAIN01_MODEL_SHA = "143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4"
CHAIN01_ENV_SHA = "2ba9a1e11b52792c7ee7a76c9891a98d5f2d7d56c058f1182410f773bac5aa71"
CHAIN01_REWARDS = {
    "track_lin_vel_xy_exp": 1.2,
    "feet_air_time": 0.01,
    "lin_vel_z_l2": -3.0,
    "ang_vel_xy_l2": -0.08,
    "action_rate_l2": -0.01,
    "flat_orientation_l2": 0.0,
}


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


def reward_weights(source: str) -> dict[str, float]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "REWARD_WEIGHTS":
            return {k: float(v) for k, v in ast.literal_eval(node.value).items()}
    raise RuntimeError("REWARD_WEIGHTS not found")


def build_payload() -> dict[str, bytes]:
    model = CHAIN01_SOURCE / "model_best.pt"
    env = CHAIN01_SOURCE / "env.yaml"
    rewards_src = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")

    weights = reward_weights(rewards_src)
    if weights != CHAIN01_REWARDS:
        raise RuntimeError(f"working tree rewards are not Chain-01: {weights}")
    model_bytes = model.read_bytes()
    if sha(model_bytes) != CHAIN01_MODEL_SHA:
        raise RuntimeError("Chain-01 source model_best.pt SHA mismatch")
    env_bytes = env.read_bytes()
    if sha(env_bytes) != CHAIN01_ENV_SHA:
        raise RuntimeError("Chain-01 source env.yaml SHA mismatch")

    telemetry = (GO2 / "go2_eval_telemetry.py").read_text(encoding="utf-8")
    for marker in ("survival_proxy_v2", "posture_gate_v2", "FALL_TILT_COS"):
        if marker not in telemetry:
            raise RuntimeError(f"telemetry is missing the posture gate: {marker}")

    payload: dict[str, bytes] = {}
    # candidate/ is shipped but unused by the runner; chain01/ replays the
    # frozen checkpoint.  Both get the identical source tree so the evaluator
    # cannot differ between them.
    for role in ("candidate", "chain01"):
        for path in source_files():
            rel = path.relative_to(GO2).as_posix()
            payload[f"{role}/{rel}"] = path.read_bytes()
    payload["chain01/exported/model_best.pt"] = model_bytes
    payload["chain01/exported/env.yaml"] = env_bytes
    payload["go2_self_eval_registry.json"] = (GO2 / "config" / "go2_self_eval_registry.json").read_bytes()
    for name in ("package_go2_result.py", RUNNER):
        payload[name] = (GO2 / name).read_bytes()
    payload["README.txt"] = README.encode("utf-8")

    checksums = "".join(
        f"{sha(data)}  {name}\n" for name, data in sorted(payload.items())
    )
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


README = """GO2 CHAIN-01 BASELINE  (work id G-A023)
==========================================

This package trains NOTHING.  It measures.

WHY
  Chain-01 (Default-01 + track_lin_vel_xy_exp 1.0->1.2 only, G-A011) is the
  campaign's frozen baseline -- the only reward dial with an independently
  verified, zero-survival-regression single-variable result.  It has only
  ever been scored by the tier-1 proxy (1 seed, internal early-kill cutoff).
  It has never run the full 69-case G1-G7 suite, never run seeds 202/303,
  and never been scored under the posture-gated evaluator on terrain.

  Three individual reward-weight overlays on top of Chain-01 have since each
  failed the tier-1 gate: lin_vel_z_l2 -3.0->-2.0 (G-A020, total collapse),
  ang_vel_xy_l2 -0.08->-0.05 (G-A021, partial regression), feet_air_time
  0.01->0.20 (G-A022, near-total collapse despite a positive prior on
  Default-01).  The remaining two participant-file dials (action_rate_l2,
  flat_orientation_l2) were already dial-wise exhausted on other baselines
  before the Chain-01 reset -- every direction either caused full-scenario
  collapse or was withdrawn as a sign/mechanism error, with no basis to
  expect a different outcome on Chain-01.  No further single-variable
  reward experiment is pre-registered.

  Chain-01 is therefore the campaign's best verified point and is the
  candidate this run gives a real score.

WHAT IT DOES
  1  frozen Chain-01, all 69 G1-G7 cases, seeds 101/202/303, posture-gated
  2  one video per scenario G1-G7, so the numbers have a witness
  3  one-file result ZIP

  Cost: about 1h05m of the remaining budget.  No training happens, so nothing
  about the submission candidate changes -- this run cannot damage it.

RUN
  unzip go2_chain01_baseline.zip -d /workspace
  bash /workspace/go2_chain01_baseline/server_run_go2_chain01_baseline.sh

  It starts inside tmux and returns immediately.
  Finish marker:  [DONE] GO2_CHAIN01_BASELINE_RESULT_READY

DOWNLOAD
  /workspace/_keep/GO2_CHAIN01_BASELINE_RESULT.zip
  /workspace/_keep/GO2_CHAIN01_BASELINE_RESULT.zip.sha256

GATES BUILT INTO THE RUNNER
  - the staged policy SHA must equal the frozen Chain-01 SHA, or it aborts
  - every case summary must carry survival_proxy_source = posture_gate_v2,
    or that case FAILS rather than being banked on the old metric
  - all 69 cases and all 7 videos must exist before packaging

PRE-REGISTERED READING (fixed before the run, not renegotiated after)
  Primary output is Chain-01's real /70 scorecard -- the number the campaign
  submits unless a future single-variable experiment with a genuinely new,
  untested, mechanically coherent direction is proposed and separately
  pre-registered.  This run does not itself select a next variable.
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
    size_mb = OUTPUT.stat().st_size / 1_048_576
    print(f"built  {OUTPUT}")
    print(f"members {len(payload)}   size {size_mb:.1f} MB")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
