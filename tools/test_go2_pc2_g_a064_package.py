"""PC2 G-A064 패키지 계약 테스트 — tools/build_go2_pc2_g_a064_package.py.

python -B -m unittest tools.test_go2_pc2_g_a064_package
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "workspace/training/quadruped"))
import build_go2_pc2_batch_package as bb  # noqa: E402
import build_go2_pc2_g_a064_package as g64  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

BASH = shutil.which("bash")
DEPLOY_RANGE = {"lin_vel_z_l2": (-5.0, -0.5), "feet_air_time": (0.01, 0.5),
                "ang_vel_xy_l2": (-0.3, -0.02), "action_rate_l2": (-0.02, -0.005)}
P0 = {"track_lin_vel_xy_exp": 1.5, "feet_air_time": 0.2, "lin_vel_z_l2": -1.25, "ang_vel_xy_l2": -0.05,
      "action_rate_l2": -0.01, "flat_orientation_l2": 0.0, **bb.EXTRA_DEFAULTS}
S07 = {**P0, "feet_air_time": 0.35}
# 합의 문서 §12·§14, v4 순서(c2 먼저)
EXPECTED = [("c2_s07_lin_vel_z_l2_m0p5", "lin_vel_z_l2", -0.5),
            ("c1_s07_ang_vel_xy_l2_m0p02", "ang_vel_xy_l2", -0.02),
            ("c3_s07_action_rate_l2_m0p0075", "action_rate_l2", -0.0075),
            ("c6_s07_ang_vel_xy_l2_m0p035", "ang_vel_xy_l2", -0.035),
            ("c5_s07_lin_vel_z_l2_m0p875", "lin_vel_z_l2", -0.875)]


class G064(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.info = g64.build("G-A064")
        cls.f = cls.info["files"]
        cls.points = g64.points()

    def rw(self, key, role):
        return {**bb.EXTRA_DEFAULTS, **reward_dict(self.f[f"runs/{key}/{role}"].decode())}

    def test_points_match_agreement(self):
        self.assertEqual([(k, v, x) for k, _, v, x, _, _ in self.points], EXPECTED)

    def test_parent_is_s07_with_track_fixed(self):
        for key, *_ in self.points:
            self.assertEqual(self.rw(key, "reference/baseline_quadruped_rewards.py"), S07, key)
            self.assertEqual(self.rw(key, "candidate/quadruped_rewards.py")["track_lin_vel_xy_exp"], 1.5, key)
            exp = json.loads(self.f[f"runs/{key}/experiment.json"])
            self.assertEqual(exp["parent"]["label"], "S07", key)
            self.assertEqual(exp["parent"]["harvest_for_readout"], g64.S07_HARVEST, key)

    def test_exactly_one_term_from_s07_within_deploy_range(self):
        for key, _, var, value, _, _ in self.points:
            cand = self.rw(key, "candidate/quadruped_rewards.py")
            self.assertEqual([k for k in bb.TERMS if cand[k] != S07[k]], [var], key)
            lo, hi = DEPLOY_RANGE[var]
            self.assertTrue(lo <= value <= hi, key)

    def test_expected_rewards_and_run_config(self):
        for key, _, var, value, _, _ in self.points:
            exp = json.loads(self.f[f"runs/{key}/expected_rewards.json"])["candidate"]
            self.assertEqual(exp, self.rw(key, "candidate/quadruped_rewards.py"), key)
            cfg = self.f[f"runs/{key}/run_config.env"].decode()
            self.assertIn(f"SINGLE_CHANGE_NAME={var}\n", cfg)
            self.assertIn(f"SINGLE_CHANGE_TO={value:g}\n", cfg)
            self.assertIn(f"RESULT_ZIP_NAME=GO2_G_A064_PC2_{key.upper()}_RESULT.zip\n", cfg)
            self.assertIn("TRAIN_SEED=42\n", cfg)

    def test_scripts_lf_bash_n_and_checksums(self):
        self.assertEqual([l.split()[0] for l in self.f["points.txt"].decode().splitlines()], [k for k, *_ in EXPECTED])
        self.assertEqual(self.info["names"]["release"], "GO2_G_A064_PC2_S07_COMBO_v4")
        z = zipfile.ZipFile(io.BytesIO(self.data))
        self.assertIsNone(z.testzip())
        self.assertTrue(all(n.startswith("go2_g_a064_pc2/") for n in z.namelist()))
        sums = dict(reversed(l.split("  ", 1)) for l in self.f["SHA256SUMS.txt"].decode().splitlines())
        self.assertEqual(len(sums), len(self.f) - 1)
        for name in ("run_all.sh", "run_point.sh"):
            self.assertNotIn(b"\r\n", self.f[name], name)
            if BASH:
                with tempfile.NamedTemporaryFile("wb", suffix=".sh", delete=False) as t:
                    t.write(self.f[name])
                try:
                    self.assertEqual(subprocess.run([BASH, "-n", t.name]).returncode, 0, name)
                finally:
                    os.unlink(t.name)

    def test_report_html_is_harvested(self):
        # report.html 회수는 공용 러너가 한다(G-A063 회수본마다 exported/report.html 존재로 확인).
        runner = self.f["shared/server_run_go2_candidate_iter_pinned.sh"].decode()
        self.assertIn("exported/report.html", runner)

    @unittest.skipUnless(BASH, "bash required")
    def test_stop_file_stops_before_next_point(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            zipfile.ZipFile(io.BytesIO(self.data)).extractall(tmp)
            root = tmp / "go2_g_a064_pc2"
            log_dir = tmp / "status"
            log_dir.mkdir()
            (log_dir / "STOP").write_text("stop")
            env = {**os.environ, "GO2_BATCH_LOG_DIR": str(log_dir)}
            r = subprocess.run([BASH, str(root / "run_all.sh")], env=env, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("[BATCH STOP] STOP file present", r.stdout)
            self.assertNotIn("[BATCH POINT] c2", r.stdout)

    def test_build_does_not_leak_into_g_a062_builder(self):
        self.assertEqual(bb.PROVISIONAL_WORK_ID, "G-A062")
        self.assertEqual(bb.PARENT_LABEL, "Q0")
        self.assertIsNone(bb.PARENT_HARVEST)
        self.assertEqual(bb.POINTS[0][0], "q0_lin_vel_z_l2_m1p5")


if __name__ == "__main__":
    unittest.main()
