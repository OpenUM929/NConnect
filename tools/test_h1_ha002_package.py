from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

import tools.build_h1_ha002_package as build


class H1HA002PackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.zip_path = build.build(Path(cls.temp.name))
        cls.z = zipfile.ZipFile(cls.zip_path)

    @classmethod
    def tearDownClass(cls):
        cls.z.close(); cls.temp.cleanup()

    def read(self, name: str) -> bytes:
        return self.z.read(build.PREFIX + name)

    def function(self, name: str) -> str:
        lines = self.read("server_run_h1_ha002.sh").decode().splitlines()
        start = lines.index(f"{name}() {{")
        for end in range(start + 1, len(lines)):
            if lines[end] == "}":
                return "\n".join(lines[start : end + 1]) + "\n"
        self.fail(f"unterminated function {name}")

    def run_bash(self, functions: tuple[str, ...], body: str):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash unavailable")
        script = "set -euo pipefail\n" + "".join(self.function(name) for name in functions) + body
        return subprocess.run([bash, "-c", script], capture_output=True, text=True)

    def test_single_reward_diff(self):
        control = self.read("rewards/control/humanoid_rewards.py").decode()
        candidate = self.read("rewards/candidate/humanoid_rewards.py").decode()
        c_lines = control.splitlines(); n_lines = candidate.splitlines()
        diffs = [(a, b) for a, b in zip(c_lines, n_lines) if a != b]
        self.assertEqual(1, len(diffs))
        self.assertIn("-0.0005", diffs[0][0]); self.assertIn("-0.002", diffs[0][1])

    def test_deployment_originals_and_r6(self):
        sums = self.read("ORIGINAL_SHA256SUMS.txt").decode().splitlines()
        self.assertEqual(len(build.ORIGINALS), len(sums))
        for line in sums:
            digest, rel = line.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256(self.read(f"original/{rel}")).hexdigest())
        runner = self.read("server_run_h1_ha002.sh").decode()
        self.assertIn('cp -f "$PKG/original/$rel" "$ROOT/$rel"', runner)
        self.assertIn('cp -f "$PKG/rewards/$arm/humanoid_rewards.py"', runner)

    def test_matched_design_and_no_auto_promotion(self):
        exp = json.loads(self.read("experiment.json"))
        self.assertEqual(-0.0005, exp["single_change"]["control"])
        self.assertEqual(-0.002, exp["single_change"]["candidate"])
        self.assertEqual(1000, exp["training"]["iterations_each"])
        self.assertEqual(114, exp["evaluation"]["telemetry_total"])
        self.assertIn("retain Run06", exp["decision"])
        self.assertIn("not an optimum", exp["value_basis"])

    def test_required_collection_and_preflight_before_training(self):
        runner = self.read("server_run_h1_ha002.sh").decode()
        self.assertIn("/workspace/isaaclab_venv/Scripts/python.exe", runner)
        self.assertLess(runner.rindex("preflight\n"), runner.rindex("train_arm control"))
        self.assertIn("EVAL_CASES=114/114", runner)
        self.assertIn("VIDEOS=20/20", runner)
        self.assertIn("REPORTS=2/2", runner)
        self.assertIn("REPORT_REQUIRED_NOT_ACQUIRED", runner)
        self.assertIn("find \"$KEEP/$arm/evaluation\" -name summary.json | wc -l", runner)

    def test_stale_outputs_and_run_identity_are_rejected(self):
        runner = self.read("server_run_h1_ha002.sh").decode()
        self.assertIn('model_best.pt" -nt "$marker"', runner)
        self.assertIn('env.yaml" -nt "$marker"', runner)
        self.assertIn("validate_fresh_training_outputs", runner)
        self.assertIn("'selected_iter': int(selected_iter)", runner)
        self.assertIn("'model_sha256': digest(model)", runner)
        self.assertIn("'env_sha256': digest(env)", runner)
        self.assertIn("'reward_sha256': digest(reward_file)", runner)
        self.assertIn("'evaluator_sha256': digest(evaluator)", runner)
        self.assertIn("s.get('completed') is not True", runner)
        self.assertIn("s.get('steps') != steps", runner)
        self.assertIn("s.get('rows') != steps * envs", runner)
        self.assertIn("grep -qx 'EVAL_RC=0'", runner)
        self.assertIn('validate_eval "$out" 1000 32 "$marker"', runner)
        self.assertIn('"$out/identity.json" "$seed" "$name"', runner)
        self.assertIn("'evaluation_case': sys.argv[4]", runner)

    def test_exit_trap_restores_sources_and_audit_metadata(self):
        runner = self.read("server_run_h1_ha002.sh").decode()
        trap = next(line for line in runner.splitlines() if line.startswith("trap 'rc=$?"))
        self.assertIn("cleanup_runtime", trap)
        self.assertIn("restore_exported", trap)
        cleanup = runner[runner.index("cleanup_runtime()") : runner.index("package_result()")]
        self.assertIn("restore_originals", cleanup)
        self.assertIn('rewards/control/humanoid_rewards.py', cleanup)
        self.assertIn("local rc=0", cleanup)
        self.assertIn("reward_got", cleanup)
        self.assertIn('return "$rc"', cleanup)
        self.assertIn("EXPORTED_RESTORE_RC", trap)
        self.assertIn("CLEANUP_RC", trap)
        self.assertIn('cp -f "$PKG/experiment.json"', runner)
        self.assertIn('"$PKG/PACKAGE_SHA256SUMS.txt"', runner)
        self.assertIn('"$PKG/eval_telemetry.py"', runner)
        self.assertIn('evaluation/identity.json', runner)

    def test_exported_snapshot_restored_on_success_and_failure(self):
        runner = self.read("server_run_h1_ha002.sh").decode()
        snapshot = runner[runner.index("snapshot_exported()") : runner.index("restore_exported()")]
        restore = runner[runner.index("restore_exported()") : runner.index("package_result()")]
        for name in ("model_best.pt", "env.yaml", "policy.pt", "play_video.mp4", "report.html"):
            self.assertIn(name, snapshot)
        self.assertIn("present", restore)
        self.assertIn("rm -f --", restore)
        success_tail = runner[runner.index("videos_arm control; videos_arm candidate") :]
        self.assertLess(success_tail.index("restore_exported"), success_tail.index("cleanup_runtime"))
        self.assertIn('[[ ! -e "$KEEP" ]]', runner)
        self.assertIn("stale H-A002 KEEP already exists", runner)

    def test_runtime_training_freshness_validator(self):
        import os
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"; exported = root / "exported"; run = Path(td) / "run"
            exported.mkdir(parents=True); run.mkdir()
            marker = Path(td) / "marker"; marker.write_text("marker")
            model = b"fresh-model"; (run / "model_900.pt").write_bytes(model)
            (exported / "model_best.pt").write_bytes(model)
            (exported / "env.yaml").write_text("rewards:\n  action_rate_l2:\n    weight: -0.002\n")
            (exported / "report.html").write_text("report")
            now = time.time()
            for path in exported.iterdir(): os.utime(path, (now - 20, now - 20))
            os.utime(marker, (now - 10, now - 10))
            args = f"'{root.as_posix()}' '{marker.as_posix()}' '{run.as_posix()}'"
            stale = self.run_bash(("py_cmd", "validate_fresh_training_outputs"),
                                  f"validate_fresh_training_outputs {args} -0.002\n")
            self.assertNotEqual(0, stale.returncode)
            for path in exported.iterdir(): os.utime(path, (now, now))
            valid = self.run_bash(("py_cmd", "validate_fresh_training_outputs"),
                                  f"validate_fresh_training_outputs {args} -0.002\n[[ \"$VALID_SELECTED_ITER\" == 900 ]]\n")
            self.assertEqual(0, valid.returncode, valid.stderr)
            wrong = self.run_bash(("py_cmd", "validate_fresh_training_outputs"),
                                  f"validate_fresh_training_outputs {args} -0.0005\n")
            self.assertNotEqual(0, wrong.returncode)

    def test_runtime_incomplete_eval_rejected_then_complete_accepted(self):
        import os
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "eval"; out.mkdir(); marker = Path(td) / "marker"; marker.write_text("m")
            old = time.time() - 10; os.utime(marker, (old, old))
            (out / "steps.csv").write_text("header\n")
            (out / "STATUS.txt").write_text("EVAL_RC=0\nSTEPS=2\nROWS=2\n")
            (out / "summary.json").write_text('{"completed":false,"steps":2,"rows":2}')
            call = f"validate_eval '{out.as_posix()}' 2 1 '{marker.as_posix()}'\n"
            bad = self.run_bash(("py_cmd", "validate_eval"), call)
            self.assertNotEqual(0, bad.returncode)
            (out / "summary.json").write_text('{"completed":true,"steps":2,"rows":2}')
            good = self.run_bash(("py_cmd", "validate_eval"), call)
            self.assertEqual(0, good.returncode, good.stderr)

    def test_runtime_exported_restore_hash_and_absence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"; exported = root / "exported"; keep = Path(td) / "keep"
            exported.mkdir(parents=True); keep.mkdir()
            original = b"canonical-model"; (exported / "model_best.pt").write_bytes(original)
            (exported / "env.yaml").write_text("env"); (exported / "report.html").write_text("report")
            body = (
                f"ROOT='{root.as_posix()}'\nKEEP='{keep.as_posix()}'\n"
                "snapshot_exported\nprintf changed >\"$ROOT/exported/model_best.pt\"\n"
                "printf generated >\"$ROOT/exported/policy.pt\"\nrestore_exported\n"
                "[[ ! -e \"$ROOT/exported/policy.pt\" ]]\n"
            )
            result = self.run_bash(("snapshot_exported", "restore_exported"), body)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(original, (exported / "model_best.pt").read_bytes())
            self.assertFalse((exported / "policy.pt").exists())

    def test_runtime_original_restore_aggregates_early_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"; root.mkdir(); pkg = Path(td) / "pkg"; (pkg / "original").mkdir(parents=True)
            (pkg / "original/good.py").write_text("good")
            missing_digest = hashlib.sha256(b"missing").hexdigest()
            good_digest = hashlib.sha256(b"good").hexdigest()
            (pkg / "ORIGINAL_SHA256SUMS.txt").write_bytes(
                f"{missing_digest}  missing.py\n{good_digest}  good.py\n".encode()
            )
            body = (
                f"ROOT='{root.as_posix()}'\nPKG='{pkg.as_posix()}'\n"
                "if restore_originals; then exit 9; else exit 0; fi\n"
            )
            result = self.run_bash(("restore_originals",), body)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((root / "good.py").exists(), f"stdout={result.stdout} stderr={result.stderr}")
            self.assertEqual("good", (root / "good.py").read_text())

    def test_video_seed_and_checkpoint_identity(self):
        runner = self.read("server_run_h1_ha002.sh").decode()
        self.assertIn("agent.seed=101", runner)
        self.assertNotIn("enable_cameras agent.seed=42", runner)
        self.assertIn("'video_seed': 101", runner)
        self.assertIn("'video_checkpoint_sha256': identity['model_sha256']", runner)
        self.assertIn('${name}.identity.json', runner)
        self.assertIn('"checkpoint_sha256":"%s"', runner)

    def test_crc_manifest_lf_shell(self):
        self.assertIsNone(self.z.testzip())
        files = {n[len(build.PREFIX):]: self.z.read(n) for n in self.z.namelist()}
        manifest = files.pop("PACKAGE_SHA256SUMS.txt").decode().splitlines()
        for line in manifest:
            digest, name = line.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256(files[name]).hexdigest(), name)
        for name, data in files.items():
            if Path(name).suffix in {".py", ".sh", ".txt", ".json"}:
                self.assertNotIn(b"\r\n", data, name)
        bash = shutil.which("bash")
        if bash:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "runner.sh"; path.write_bytes(self.read("server_run_h1_ha002.sh"))
                result = subprocess.run([bash, "-n", str(path)], capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)

    def test_sidecar_sha_is_lf_and_correct(self):
        sidecar = Path(self.temp.name) / f"{build.NAME}.sha256"
        data = sidecar.read_bytes(); self.assertNotIn(b"\r", data)
        self.assertEqual(hashlib.sha256(self.zip_path.read_bytes()).hexdigest(), data.decode().split()[0])


if __name__ == "__main__":
    unittest.main()
