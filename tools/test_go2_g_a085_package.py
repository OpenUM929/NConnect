"""Contract tests for G-A085 (precision evaluation, no training).

The last test runs go2_g_a085_eval.sh --inner end to end with a fake isaaclab.sh that copies
stored G-A083 case files (steps.csv truncated) instead of launching Isaac Sim, so the
orchestration, resume, diag comparison, analysis and both archives are exercised.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import tools.build_go2_g_a085_package as build

ROOT = Path(__file__).resolve().parents[1]
A083 = ROOT / "workspace/_keep/go2_g_a083_action_rate_m0p01"
BASH = shutil.which("bash") or "C:/Program Files/Git/bin/bash.exe"


class G_A085PackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.zip_path = Path(cls.temp.name) / f"{build.RELEASE}.zip"
        cls.info = build.write_zip(cls.zip_path)
        cls.files = cls.info["files"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_eval_functions_are_the_g_a084_runner_bytes(self) -> None:
        src = build.b84.a082.a076.source_payload()
        runner = build.b84.patched_runner(src["server_run_go2_candidate_iter_pinned.sh"])
        block = build.runner_functions(runner)
        self.assertIn(block, self.files["go2_g_a085_eval.sh"])
        self.assertNotIn(b"train.py --task", self.files["go2_g_a085_eval.sh"])

    def test_ruler_and_policies(self) -> None:
        f = self.files
        self.assertEqual(build.EVALUATOR_SHA, hashlib.sha256(f["shared/eval_root/go2_eval_telemetry.py"]).hexdigest())
        self.assertNotIn("shared/eval_root/train.py", f)
        for key, (_, msha, esha) in build.POLICIES.items():
            self.assertEqual(msha, hashlib.sha256(f[f"policies/{key}/model_best.pt"]).hexdigest())
            self.assertEqual(esha, hashlib.sha256(f[f"policies/{key}/env.yaml"]).hexdigest())
        exp = json.loads(f["experiment.json"])
        self.assertEqual([[404, 505, 606], [707, 808, 909]], exp["evaluation"]["new_seed_sets"])
        self.assertIn("twice the evaluation sd", exp["preregistered_rules"]["real_difference"])
        self.assertEqual("evaluation_only_no_training_no_reward_change", exp["kind"])

    def test_manifest_lf_and_shell_syntax(self) -> None:
        f = self.files
        for line in f["SHA256SUMS.txt"].decode().splitlines():
            digest, name = line.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256(f[name]).hexdigest(), name)
        for name in ("go2_g_a085_eval.sh", "run_all.sh", "shared/go2_g_a085_precision_analysis.py"):
            self.assertNotIn(b"\r", f[name], name)
        with tempfile.TemporaryDirectory() as d:
            for name in ("go2_g_a085_eval.sh", "run_all.sh"):
                p = Path(d) / name
                p.write_bytes(f[name])
                r = subprocess.run([BASH, "-n", str(p)], capture_output=True, text=True)
                self.assertEqual(0, r.returncode, r.stderr)
        with zipfile.ZipFile(self.zip_path) as z:
            self.assertIsNone(z.testzip())

    def test_inner_run_end_to_end_with_fake_isaac(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            with zipfile.ZipFile(self.zip_path) as z:
                z.extractall(d / "pkg")
            pkg = d / "pkg" / build.SLUG
            fixture = A083 / "evaluation/candidate"
            fake = d / "isaaclab.sh"
            fake.write_text(
                "#!/usr/bin/env bash\n[[ \"$1\" == -p ]] || exit 9; shift\n"
                "if [[ \"$1\" == play.py ]]; then\n"
                "  c=$NCRC_EVAL_CASE; [[ $c == dr_seed_* ]] && c=dr_seed_101\n"
                f"  src='{fixture.as_posix()}'/cases/seed_101/$c\n"
                "  mkdir -p \"$NCRC_EVAL_OUT\"; cp \"$src/summary.json\" \"$src/STATUS.txt\" \"$NCRC_EVAL_OUT/\"\n"
                "  head -n 1921 \"$src/steps.csv\" >\"$NCRC_EVAL_OUT/steps.csv\"; echo fake-play; exit 0\nfi\n"
                "exec python \"$@\"\n", encoding="utf-8", newline="\n")
            # Test-only rewrites: the hardcoded Isaac path and the network asset probe.
            script = pkg / "go2_g_a085_eval.sh"
            text = script.read_text(encoding="utf-8")
            text = text.replace("/workspace/IsaacLab/isaaclab.sh -p play.py", f"{fake.as_posix()} -p play.py")
            text = text.replace("if command -v curl >/dev/null 2>&1; then\n  curl", "if false; then\n  curl")
            script.write_text(text, encoding="utf-8", newline="\n")
            lines = []
            for line in (pkg / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
                digest, name = line.split("  ", 1)
                lines.append(f"{hashlib.sha256((pkg / name).read_bytes()).hexdigest()}  {name}")
            (pkg / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            # Fake G-A084 harvest built from the G-A083 policy files.
            a084 = d / "kb/go2_g_a084_ang_vel_xy_m0p065"
            (a084 / "training/source").mkdir(parents=True)
            (a084 / "evaluation/candidate").mkdir(parents=True)
            shutil.copy(A083 / "training/model_best.pt", a084 / "training/model_best.pt")
            shutil.copy(A083 / "training/env.yaml", a084 / "training/env.yaml")
            shutil.copy(A083 / "training/source/quadruped_rewards.py", a084 / "training/source/quadruped_rewards.py")
            msha, esha = build.POLICIES["a083"][1], build.POLICIES["a083"][2]
            (a084 / "RUNNER_STATUS.txt").write_text("RUNNER_RC=0\n", encoding="utf-8")
            (a084 / "training/CHECKPOINT_PIN.txt").write_text(f"EVAL_CHECKPOINT_ITER=2400\nEVAL_CHECKPOINT_SHA={msha}\n", encoding="utf-8")
            (a084 / "evaluation/candidate/identity.json").write_text(json.dumps(
                {"model_sha256": msha, "env_sha256": esha, "evaluator_sha256": build.EVALUATOR_SHA},
                separators=(",", ":")), encoding="utf-8")
            env = {**os.environ, "ISAACLAB_SH": fake.as_posix(), "GO2_A085_KEEP_BASE": (d / "kb").as_posix(),
                   "GO2_A085_WORK": (d / "work").as_posix(), "GO2_A085_A084_KEEP": a084.as_posix(),
                   "GO2_A085_A082_STORED": (ROOT / "workspace/_keep/go2_g_a082_track_ang_vel_z_p0p75/evaluation/candidate").as_posix(),
                   "GO2_A085_A083_STORED": fixture.as_posix()}
            r = subprocess.run([BASH, str(script), "--inner"], env=env, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=3000)
            status = (d / "kb/GO2_G_A085_STATUS.txt").read_text(encoding="utf-8")
            self.assertEqual(0, r.returncode, status + r.stdout[-3000:] + r.stderr[-3000:])
            self.assertIn("STATE=DONE", status)
            keep = d / "kb/go2_g_a085_precision_eval"
            for k in ("a082", "a083", "a084"):
                for s in ("404", "707"):
                    self.assertEqual(69, len(list((keep / f"evaluation/{k}_s{s}/cases").rglob("summary.json"))), f"{k}_s{s}")
            self.assertEqual(32, len(list((keep / "diag").rglob("summary.json"))))
            cmp_a083 = (keep / "diag/a083_PLAIN_VS_DIAG.txt").read_text(encoding="utf-8").split()
            self.assertEqual(16, cmp_a083.count("DIFFERENT"))  # fake steps.csv are truncated copies
            summary = json.loads((keep / "analysis/SUMMARY.json").read_text(encoding="utf-8"))
            self.assertEqual(["101", "202", "303", "404", "505", "606", "707", "808", "909"], summary["a083"]["seeds"])
            self.assertEqual(["404", "505", "606", "707", "808", "909"], summary["a084"]["seeds"])
            self.assertIsNotNone(summary["a083"]["formula_score_sd_over_sets"])
            for z in ("GO2_G_A085_PRECISION_EVAL_RESULT.zip", "GO2_G_A085_PRECISION_EVAL_SUMMARY.zip"):
                p = d / "kb" / z
                self.assertTrue(p.is_file(), z)
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                                 (d / "kb" / f"{z}.sha256").read_text(encoding="utf-8").split()[0])
            with zipfile.ZipFile(d / "kb/GO2_G_A085_PRECISION_EVAL_SUMMARY.zip") as z:
                names = z.namelist()
            self.assertTrue(any(n.endswith("analysis/SUMMARY.json") for n in names))
            # Resume: the same line again keeps every measured case.
            r2 = subprocess.run([BASH, str(script), "--inner"], env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=3000)
            self.assertEqual(0, r2.returncode, r2.stdout[-2000:])
            self.assertNotIn("fake-play", r2.stdout)
            rows = list(csv.DictReader((keep / "analysis/ROWS.csv").open(encoding="utf-8")))
            # 23 rows per seed (22 cases + DR); a082/a083 have 3 stored + 6 new seeds, a084 6 new.
            self.assertEqual(23 * (9 + 9 + 6), len(rows))


if __name__ == "__main__":
    unittest.main()
