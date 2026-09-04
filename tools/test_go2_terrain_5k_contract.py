"""Contract test for the G-A011 package: verify the ZIP before it costs GPU time."""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "workspace" / "training" / "quadruped" / "go2_terrain_5k_v1.zip"
PREFIX = "go2_terrain_5k_v1/"
PILOT_SHA = "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{'' if ok else '  ' + str(detail)}")
    if not ok:
        FAILURES.append(label)


def main() -> int:
    check("package ZIP exists", ZIP.exists())
    if not ZIP.exists():
        return 1

    with zipfile.ZipFile(ZIP) as archive:
        names = {n[len(PREFIX):] for n in archive.namelist()}
        blobs = {n[len(PREFIX):]: archive.read(n) for n in archive.namelist()}
        check("archive CRC intact", archive.testzip() is None)

    print("[1] required members")
    for name in ("server_run_go2_terrain_5k_v1.sh", "package_go2_result.py",
                 "go2_self_eval_registry.json", "README.txt", "PACKAGE_SHA256SUMS.txt",
                 "pilot/exported/model_best.pt", "pilot/exported/env.yaml",
                 "candidate/train.py", "candidate/play.py",
                 "candidate/quadruped_rewards.py", "candidate/go2_eval_telemetry.py"):
        check(f"member {name}", name in names)

    print("[2] frozen baseline identity")
    check("pilot model is the frozen Pilot-01 checkpoint",
          hashlib.sha256(blobs["pilot/exported/model_best.pt"]).hexdigest() == PILOT_SHA)

    print("[3] reward parity is real, not asserted")
    cand = blobs["candidate/quadruped_rewards.py"]
    pilot = blobs["pilot/quadruped_rewards.py"]
    check("candidate and pilot reward sources are byte-identical", cand == pilot)

    def weights(data: bytes) -> dict:
        for node in ast.walk(ast.parse(data.decode("utf-8"))):
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "REWARD_WEIGHTS":
                return {k: float(v) for k, v in ast.literal_eval(node.value).items()}
        return {}

    expected = {"track_lin_vel_xy_exp": 1.2, "feet_air_time": 0.2, "lin_vel_z_l2": -2.0,
                "ang_vel_xy_l2": -0.05, "action_rate_l2": -0.01}
    check("reward weights are Pilot-01 5var", weights(cand) == expected, weights(cand))

    print("[4] shipped evaluator carries the posture gate")
    for role in ("candidate", "pilot"):
        tele = blobs[f"{role}/go2_eval_telemetry.py"].decode("utf-8")
        check(f"{role} telemetry has survival_proxy_v2", "survival_proxy_v2" in tele)
        check(f"{role} telemetry has posture_gate_v2 label", "posture_gate_v2" in tele)
        check(f"{role} telemetry keeps survival_proxy_v1", "survival_proxy_v1" in tele)
        check(f"{role} telemetry parses", _parses(tele))
    check("candidate and pilot evaluators are identical",
          blobs["candidate/go2_eval_telemetry.py"] == blobs["pilot/go2_eval_telemetry.py"])

    print("[5] runner")
    with tempfile.TemporaryDirectory() as tmp:
        runner = Path(tmp) / "runner.sh"
        runner.write_bytes(blobs["server_run_go2_terrain_5k_v1.sh"])
        rc = subprocess.run(["bash", "-n", str(runner)], capture_output=True)
        check("runner passes bash -n", rc.returncode == 0, rc.stderr.decode()[:200])
    text = blobs["server_run_go2_terrain_5k_v1.sh"].decode("utf-8")
    check("runner has no CRLF line endings", "\r" not in text)
    check("runner enforces reward parity before training",
          "REWARD_PARITY" in text and "reward_parity.diff" in text)
    check("runner rejects a case that lost posture evidence", "posture_gate_v2" in text)
    check("runner trains 5000 iterations by default", "GO2_MAX_ITERATIONS:-5000" in text)
    check("runner preserves ladder checkpoints", "SNAPSHOT" in text and "LADDER=" in text)
    check("runner evaluates frozen pilot under the new evaluator", "pilot_v2" in text)
    check("runner verifies the frozen pilot SHA", PILOT_SHA in text)
    check("runner requires 69 cases per suite", "!= 69" in text or "== 69" in text)

    print("[6] internal checksum manifest")
    manifest = blobs["PACKAGE_SHA256SUMS.txt"].decode("utf-8").splitlines()
    listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in manifest if line.strip()}
    check("manifest covers every member except itself",
          set(listed) == set(names) - {"PACKAGE_SHA256SUMS.txt"},
          set(names) ^ (set(listed) | {"PACKAGE_SHA256SUMS.txt"}))
    bad = [n for n, d in listed.items() if hashlib.sha256(blobs[n]).hexdigest() != d]
    check("every listed checksum matches", not bad, bad)

    print()
    if FAILURES:
        print(f"CONTRACT_FAIL ({len(FAILURES)}): {FAILURES}")
        return 1
    print("CONTRACT_PASS")
    return 0


def _parses(text: str) -> bool:
    try:
        ast.parse(text)
        return True
    except SyntaxError:
        return False


if __name__ == "__main__":
    sys.exit(main())
