"""Contract: a runner that tees a video log creates the log directory first.

G-A038 (2026-09-17) trained and measured everything, then stopped at the first G-A033 video:
run_video tees into $KEEP/logs/<baseline>_videos/, which nothing created, and pipefail ended
the run before RUNNER_STATUS.txt was written, so neither the gate nor the verifier could read
the harvest.  Releases that ran keep the bytes they ran.  The first two archived runner hashes
retain the defect; G-A041 is the first executed archive carrying the log-directory fix.

Local only: no simulator.  Run from the repository root:
    python -m unittest tools.test_go2_runner_video_log_contract
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as reward  # noqa: E402
import build_go2_candidate_package as pkg  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402
from tools.test_h1_report_recovery import BASH, shell_path  # noqa: E402

WORKING = (pkg.RUNNER, pkg.PINNED_RUNNER)
KEEP = ROOT / "workspace" / "_keep"
# Harvests of the executed releases: the run the frozen runner bytes are taken from.
HARVESTS = {
    "G-A031": "go2_g_a031_a017_feet_air_time_001",
    "G-A032": "go2_g_a032_a017_feet_air_time_010",
    "G-A033": "go2_g_a033_a017_track_lin_vel_xy_150",
    "G-A038": "go2_g_a038_a033_ang_vel_xy_m008",
    "G-A041": "go2_g_a041_a033_ang_vel_xy_m004",
    # Pinned 2026-09-22 with defect C-14: both ran with the working-tree runner, and the
    # fix for C-14 changes it.  The pin is provable from what the server returned.
    "G-A042": "go2_g_a042_a033_track_lin_vel_xy_160",
    "G-A043": "go2_g_a043_a033_lin_vel_z_m15",
}
NOW = ROOT / "GO2_NOW.md"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def all_specs() -> dict[str, dict]:
    specs = {work: pkg.load(work) for work in pkg.SPECS}
    specs.update({work: json.loads(path.read_text(encoding="utf-8")) for work, path in length.SPECS.items()})
    specs.update({work: json.loads(path.read_text(encoding="utf-8")) for work, path in reward.SPECS.items()})
    return specs


def run_video_harness(runner: str, keep: Path, root: Path) -> subprocess.CompletedProcess:
    """run_video as shipped, with isaaclab.sh replaced by a stub that writes the video."""
    body = re.search(r"^run_video\(\) \{\n.*?^\}\n", runner, re.M | re.S).group(0)
    assert body.count("/workspace/IsaacLab/isaaclab.sh") == 1
    stub = root / "isaaclab_stub.sh"
    stub.write_text('#!/usr/bin/env bash\necho "stub play $*"\necho video >exported/play_video.mp4\n',
                    encoding="utf-8", newline="\n")
    body = body.replace("/workspace/IsaacLab/isaaclab.sh", f"bash {shell_path(stub)}")
    model, env = root / "model.pt", root / "env.yaml"
    model.write_bytes(b"model")
    env.write_bytes(b"env")
    script = "\n".join([
        "set -euo pipefail",
        # Some Windows test hosts launch Git Bash with a transient minimal PATH.
        # Pin the shell tools this harness exercises; this does not affect runner bytes.
        "PATH=/usr/bin:/bin:$PATH",
        f"KEEP={shell_path(keep)}",
        "RESUME=0 VIDEO_STEPS=500 EVALUATOR_SHA=x",
        "set_case() { VX=0.3 VY=0 WZ=0 PUSH_X= PUSH_Y= DR_MODE=0; TERRAIN_ARGS=(); }",
        body,
        f"mkdir -p {shell_path(keep)}/logs {shell_path(keep)}/evaluation",
        f"run_video g_a033_videos {shell_path(root)} {shell_path(model)} {shell_path(env)} G3 rough_lateral 101",
        "echo HARNESS_DONE",
    ]) + "\n"
    return subprocess.run([BASH, "-c", script], capture_output=True, text=True, encoding="utf-8")


class DetectorTests(unittest.TestCase):
    def test_working_tree_runners_create_the_video_log_directory(self) -> None:
        for name in WORKING:
            with self.subTest(name):
                self.assertEqual(pkg.video_log_dir_faults((GO2 / name).read_text(encoding="utf-8")), [])

    def test_executed_copies_preserve_their_historical_fix_state(self) -> None:
        copies = sorted(set(pkg.EXECUTED_RUNNERS.values()))
        self.assertEqual(len(copies), 4)
        expected = {
            "server_run_go2_candidate_staged.5ce14f1cdc1da54e.sh":
                ["run_video tees into $KEEP/logs/$label without creating it"],
            "server_run_go2_candidate_iter_pinned.47a5c5c6840e2331.sh":
                ["run_video tees into $KEEP/logs/$label without creating it"],
            "server_run_go2_candidate_iter_pinned.1cd87f425d5b89f5.sh": [],
            # G-A042/G-A043 ran with this one; the video-log fault was already fixed in it.
            "server_run_go2_candidate_iter_pinned.6fd78eeb8eac5342.sh": [],
        }
        self.assertEqual(set(copies), set(expected))
        for name in copies:
            with self.subTest(name):
                faults = pkg.video_log_dir_faults((pkg.RUNNER_HISTORY / name).read_text(encoding="utf-8"))
                self.assertEqual(faults, expected[name])


class HarnessTests(unittest.TestCase):
    """The shell itself: the fixed run_video finishes, the executed one stops where G-A038 stopped."""

    def run_one(self, runner: str) -> tuple[subprocess.CompletedProcess, Path]:
        tmp = Path(tempfile.mkdtemp(dir=ROOT / "workspace"))
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        keep, root = tmp / "keep", tmp / "root"
        root.mkdir()
        return run_video_harness(runner, keep, root), keep

    def test_fixed_runners_write_the_video_and_its_log(self) -> None:
        for name in WORKING:
            with self.subTest(name):
                done, keep = self.run_one((GO2 / name).read_text(encoding="utf-8"))
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertIn("HARNESS_DONE", done.stdout)
                self.assertTrue((keep / "logs/g_a033_videos/video_G3_rough_lateral_seed_101.log").is_file())
                self.assertTrue((keep / "evaluation/g_a033_videos/videos/G3_rough_lateral_seed_101.mp4").is_file())

    def test_executed_runners_reproduce_their_historical_video_behavior(self) -> None:
        for name in sorted(set(pkg.EXECUTED_RUNNERS.values())):
            with self.subTest(name):
                done, keep = self.run_one((pkg.RUNNER_HISTORY / name).read_text(encoding="utf-8"))
                faults = pkg.video_log_dir_faults((pkg.RUNNER_HISTORY / name).read_text(encoding="utf-8"))
                if faults:
                    self.assertNotEqual(done.returncode, 0)
                    self.assertNotIn("HARNESS_DONE", done.stdout)
                    self.assertIn("No such file or directory", done.stdout + done.stderr)
                else:
                    self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                    self.assertIn("HARNESS_DONE", done.stdout)
                    self.assertTrue((keep / "logs/g_a033_videos/video_G3_rough_lateral_seed_101.log").is_file())
                    self.assertTrue((keep / "evaluation/g_a033_videos/videos/"
                                     "G3_rough_lateral_seed_101.mp4").is_file())


class ReleaseTests(unittest.TestCase):
    def test_executed_releases_are_the_runs_that_happened(self) -> None:
        specs = all_specs()
        self.assertEqual({work for work, _ in pkg.EXECUTED_RUNNERS}, set(HARVESTS))
        for (work, release), name in pkg.EXECUTED_RUNNERS.items():
            with self.subTest(work):
                harvest = KEEP / HARVESTS[work] / "meta"
                ran = json.loads((harvest / "experiment.json").read_text(encoding="utf-8"))
                self.assertEqual((ran["work_id"], ran["output"]["release_id"]), (work, release))
                self.assertEqual(specs[work]["output"]["release_id"], release)
                sums = dict(reversed(line.split("  ", 1)) for line in
                            (harvest / "PACKAGE_SHA256SUMS.txt").read_text(encoding="utf-8").splitlines())
                data = (pkg.RUNNER_HISTORY / name).read_bytes()
                self.assertEqual(sums[specs[work]["runner"]], sha(data))
                self.assertEqual(name, f"{Path(specs[work]['runner']).stem}.{sha(data)[:16]}.sh")
                self.assertEqual(pkg.runner_bytes(specs[work]), data)

    def test_every_other_release_ships_the_working_tree_runner(self) -> None:
        for work, spec in all_specs().items():
            key = (work, spec["output"]["release_id"])
            if key in pkg.EXECUTED_RUNNERS:
                continue
            with self.subTest(work):
                self.assertEqual(pkg.runner_bytes(spec), (GO2 / spec["runner"]).read_bytes())

    def test_the_builder_refuses_a_runner_without_the_directory(self) -> None:
        spec = all_specs()["G-A037"]
        broken = (GO2 / spec["runner"]).read_text(encoding="utf-8").replace(
            ' "$KEEP/evaluation/$label/videos" "$KEEP/logs/$label"\n', ' "$KEEP/evaluation/$label/videos"\n')
        original = pkg.GO2
        with tempfile.TemporaryDirectory(dir=ROOT / "workspace") as tmp:
            (Path(tmp) / spec["runner"]).write_text(broken, encoding="utf-8", newline="\n")
            pkg.GO2 = Path(tmp)
            try:
                with self.assertRaisesRegex(RuntimeError, "run_video tees into"):
                    pkg.runner_bytes(spec)
            finally:
                pkg.GO2 = original


def packaged_runners(data: bytes, where: str):
    """(where, run_config text, experiment.json, runner name, runner text) for every candidate runner inside."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        for name in names:
            if name.endswith(".zip"):
                yield from packaged_runners(archive.read(name), f"{where}!{name}")
            base = name.rsplit("/", 1)[-1]
            if base.startswith("server_run_go2_candidate") and base.endswith(".sh"):
                folder = name[: -len(base)]
                config = archive.read(folder + "run_config.env").decode("utf-8")
                spec = json.loads(archive.read(folder + "experiment.json")) if folder + "experiment.json" in names else {}
                yield where, config, spec, base, archive.read(name).decode("utf-8")


class UploadTests(unittest.TestCase):
    def test_no_current_upload_can_stop_at_a_baseline_video(self) -> None:
        now = NOW.read_text(encoding="utf-8")
        seen = 0
        for path in sorted((GO2 / "upload").glob("*/current/*.zip")):
            for where, config, spec, name, runner in packaged_runners(path.read_bytes(), path.name):
                videos = re.search(r"^BASELINE_VIDEOS=\((.*)\)$", config, re.M).group(1).strip()
                faults = pkg.video_log_dir_faults(runner)
                if not videos or not faults:
                    continue
                seen += 1
                work = re.search(r"^WORK_ID=(\S+)$", config, re.M).group(1)
                with self.subTest(where):
                    key = (work, (spec.get("output") or {}).get("release_id"))
                    if key in pkg.EXECUTED_RUNNERS:
                        continue  # the record of a run that happened, not an upload candidate
                    # Anything else must be named as not uploadable in the NOW pointer.
                    self.assertTrue(any(work in line and "업로드 금지" in line and "영상 로그" in line
                                        for line in now.splitlines()), f"{work} ({where}) {faults}")
        self.assertGreaterEqual(seen, 2)  # G-A038 (executed) and G-A030 (suite runner, recorded)


if __name__ == "__main__":
    unittest.main()
