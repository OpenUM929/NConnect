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
OUTPUT = GO2 / "go2_terrain_5k_v1.zip"
PREFIX = Path("go2_terrain_5k_v1")
FIXED_TIMESTAMP = (2026, 9, 3, 0, 0, 0)
RUNNER = "server_run_go2_terrain_5k_v1.sh"

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


README = """\
G-A011  Go2 terrain curriculum, 5,000 iterations
================================================

WHAT THIS RUN ASKS
  Pilot-01 reached terrain curriculum level 3.94 after 1,000 iterations.  The
  exam terrain needs about level 5.0 for 15 cm stairs (G5) and 7.9 for +-20
  degree slopes (G4).  The single question here is whether that gap closes with
  more iterations or not.  Reward weights are therefore byte-identical to
  Pilot-01: the only variable is training length.

WHAT ELSE COMES BACK FOR FREE
  * a tier-1 score curve at iterations 1000 / 2000 / 3000 / 4000
  * a full 69-case suite on frozen Pilot-01 under the NEW evaluator, which is
    the v2 baseline the campaign does not currently have

EVALUATOR CHANGE (read before comparing to older numbers)
  survival_proxy used to be 1 - terminated/num_envs, so a Go2 lying belly-down
  scored 1.00 as long as no termination fired.  Re-scoring the archived results
  showed every Default-lineage policy dropping from 1.000 to 0.000 on flat
  ground.  survival_proxy is now posture-gated: upright means gravity still
  points down through the base (<= 60 deg tilt) AND the base is >= 0.18 m above
  the terrain directly beneath it, sustained for 0.5 s before a fall is called.
  Old numbers remain readable as survival_proxy_v1.  Numbers from this package
  are NOT comparable to pre-v2 numbers except through pilot_v2.

RUN IT
  unzip go2_terrain_5k_v1.zip -d /workspace
  bash /workspace/go2_terrain_5k_v1/server_run_go2_terrain_5k_v1.sh

  Starts a tmux session and returns immediately.  Watch it with
      tmux attach -t go2_terrain_5k_v1
  Re-running with GO2_RESUME=1 skips work already verified on disk.

COST (measured on this server: 3.86 s/iter at 4096 envs)
  training 5,000 iter   ~5h 20m
  ladder + two suites   ~1h 20m
  total                 ~6h 40m

DOWNLOAD WHEN DONE
  /workspace/_keep/GO2_TERRAIN_5K_RESULT.zip
  /workspace/_keep/GO2_TERRAIN_5K_RESULT.zip.sha256
  Marker line: [DONE] GO2_TERRAIN_5K_RESULT_READY

PRE-REGISTERED VERDICT (fixed before the run, do not renegotiate after)
  PRIMARY   Curriculum/terrain_levels at 5,000 iterations
              >= 7.0        terrain was an iteration problem -> move to reward
                            refinement for stair descent
              5.5 to 7.0    partial; extend only if the ladder is still rising
              <= 5.5        not an iteration problem -> reward / curriculum work
  SECONDARY survival_proxy_v2 >= 0.95 on G1, G2, G6 (guards the new gate)
            G3, G4, G5 scenario proxy above pilot_v2 on the same evaluator
  VIDEO     7 scenario videos; a policy parked on a stair top platform is a
            fail regardless of its survival number
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
