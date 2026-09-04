"""Build the G-A011 terrain-curriculum server package.

One upload, one command, one result ZIP.  The controlled variable against the
frozen Pilot-01 baseline is training length; reward weights are byte-identical,
which the runner re-proves on the server before it spends a single iteration.
"""

from __future__ import annotations

import ast
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
OUTPUT = GO2 / "go2_pilot_v2_baseline.zip"
PREFIX = Path("go2_pilot_v2_baseline")
FIXED_TIMESTAMP = (2026, 9, 3, 0, 0, 0)
RUNNER = "server_run_go2_pilot_v2_baseline.sh"

PILOT_MODEL_SHA = "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d"
PILOT_REWARDS = {
    "track_lin_vel_xy_exp": 1.2,
    "feet_air_time": 0.2,
    "lin_vel_z_l2": -2.0,
    "ang_vel_xy_l2": -0.05,
    "action_rate_l2": -0.01,
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
    model = GO2 / "exported" / "model_best.pt"
    env = GO2 / "exported" / "env.yaml"
    rewards_src = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")

    weights = reward_weights(rewards_src)
    if weights != PILOT_REWARDS:
        raise RuntimeError(f"working tree rewards are not Pilot-01: {weights}")
    model_bytes = model.read_bytes()
    if sha(model_bytes) != PILOT_MODEL_SHA:
        raise RuntimeError("exported/model_best.pt is not the frozen Pilot-01 checkpoint")

    telemetry = (GO2 / "go2_eval_telemetry.py").read_text(encoding="utf-8")
    for marker in ("survival_proxy_v2", "posture_gate_v2", "FALL_TILT_COS"):
        if marker not in telemetry:
            raise RuntimeError(f"telemetry is missing the posture gate: {marker}")

    payload: dict[str, bytes] = {}
    # candidate/ trains; pilot/ only ever replays a frozen checkpoint.  Both get
    # the identical source tree so the evaluator cannot differ between them.
    for role in ("candidate", "pilot"):
        for path in source_files():
            rel = path.relative_to(GO2).as_posix()
            payload[f"{role}/{rel}"] = path.read_bytes()
    payload["pilot/exported/model_best.pt"] = model_bytes
    payload["pilot/exported/env.yaml"] = env.read_bytes()
    payload["go2_self_eval_registry.json"] = (GO2 / "config" / "go2_self_eval_registry.json").read_bytes()
    for name in ("package_go2_result.py", RUNNER):
        payload[name] = (GO2 / name).read_bytes()
    payload["README.txt"] = README.encode("utf-8")

    checksums = "".join(
        f"{sha(data)}  {name}\n" for name, data in sorted(payload.items())
    )
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


README = """GO2 PILOT-01 v2 BASELINE  (work id G-A012)
==========================================

This package trains NOTHING.  It measures.

WHY
  Prelim rule 8 scores each scenario as  survival x tracking,  and defines
  survival as "the share that finished WITHOUT FALLING" -- not as "no
  termination event fired".  The campaign's evaluator used the second
  definition until 260902, which counted a Go2 lying on its belly as alive.

  Re-scoring the archived flat-ground results with a posture gate (no GPU)
  moved every Default-lineage policy from survival 1.000 to 0.000 and left
  Pilot-01 unchanged at 1.000.  Pilot-01 is therefore the only Go2 policy
  known to actually walk.

  Rule 7 puts 0.60 of the Go2 weight on terrain -- G3 rough 0.20, G4 slope
  0.15, G5 stairs 0.15, G7 DR 0.10 -- and Pilot-01 has never been measured
  there with a valid survival metric.  Training again before that is known
  would be buying an answer to a question we cannot yet ask.

WHAT IT DOES
  1  frozen Pilot-01, all 69 G1-G7 cases, seeds 101/202/303, posture-gated
  2  one video per scenario G1-G7, so the numbers have a witness
  3  one-file result ZIP

  Cost: about 1h05m of the remaining budget.  No training happens, so nothing
  about the submission candidate changes -- this run cannot damage it.

RUN
  unzip go2_pilot_v2_baseline.zip -d /workspace
  bash /workspace/go2_pilot_v2_baseline/server_run_go2_pilot_v2_baseline.sh

  It starts inside tmux and returns immediately.
  Finish marker:  [DONE] GO2_PILOT_V2_BASELINE_RESULT_READY

DOWNLOAD
  /workspace/_keep/GO2_PILOT_V2_BASELINE_RESULT.zip
  /workspace/_keep/GO2_PILOT_V2_BASELINE_RESULT.zip.sha256

GATES BUILT INTO THE RUNNER
  - the staged policy SHA must equal the frozen Pilot-01 SHA, or it aborts
  - every case summary must carry survival_proxy_source = posture_gate_v2,
    or that case FAILS rather than being banked on the old metric
  - all 69 cases and all 7 videos must exist before packaging

PRE-REGISTERED READING (fixed before the run, not renegotiated after)
  Primary output is the first true G1-G7 scorecard for Go2.  The single
  largest weighted point loss in that scorecard selects the one reward
  variable for the next training run.  No other selection rule is admitted.
  Terrain curriculum level is NOT a target: rule 7 states that step climbing
  is not required of Go2, and G5 asks only for 10-15 cm stairs.
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
