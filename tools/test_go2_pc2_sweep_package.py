"""PC2 계단 집중 범위 스윕 패키지(G-A063) 계약 테스트 — tools/build_go2_pc2_sweep_package.py.

python -B -m unittest tools.test_go2_pc2_sweep_package
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
import build_go2_pc2_sweep_package as sw  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

BASH = shutil.which("bash")
# 배포 quadruped_rewards.py 추천 범위(go2_hotfix_verify/go2_default_vs_pilot_v1/default/quadruped_rewards.py L51-74)
DEPLOY_RANGE = {"lin_vel_z_l2": (-5.0, -0.5), "feet_air_time": (0.01, 0.5),
                "ang_vel_xy_l2": (-0.3, -0.02), "action_rate_l2": (-0.02, -0.005)}
P0 = {"track_lin_vel_xy_exp": 1.5, "feet_air_time": 0.2, "lin_vel_z_l2": -1.25, "ang_vel_xy_l2": -0.05,
      "action_rate_l2": -0.01, "flat_orientation_l2": 0.0, **bb.EXTRA_DEFAULTS}


class Sweep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.info = sw.build()
        cls.f = cls.info["files"]
        cls.points = sw.points()

    def rw(self, key, role):
        return {**bb.EXTRA_DEFAULTS, **reward_dict(self.f[f"runs/{key}/{role}"].decode())}

    def test_every_parent_is_p0_with_track_fixed(self):
        for key, pc, *_ in self.points:
            self.assertEqual(pc, {}, key)
            self.assertEqual(self.rw(key, "reference/baseline_quadruped_rewards.py"), P0, key)
            self.assertEqual(self.rw(key, "candidate/quadruped_rewards.py")["track_lin_vel_xy_exp"], 1.5, key)

    def test_one_term_changed_within_deploy_range_and_ends_covered(self):
        seen: dict[str, set] = {}
        for key, _, var, value, _, _ in self.points:
            cand = self.rw(key, "candidate/quadruped_rewards.py")
            diff = [k for k in bb.TERMS if cand[k] != P0[k]]
            if key.endswith("p0_repeat"):
                self.assertEqual(diff, [], key)
                continue
            self.assertEqual(diff, [var], key)
            lo, hi = DEPLOY_RANGE[var]
            self.assertTrue(lo <= value <= hi, f"{key} {value} outside {lo}~{hi}")
            seen.setdefault(var, set()).add(value)
        for var, (lo, hi) in DEPLOY_RANGE.items():
            self.assertTrue({lo, hi} <= seen[var], f"{var} 범위 양 끝 누락: {seen.get(var)}")

    def test_no_value_already_measured_on_p0(self):
        p0_measured = {("lin_vel_z_l2", -1.5), ("ang_vel_xy_l2", -0.08), ("track_lin_vel_xy_exp", 1.4)}
        for key, _, var, value, _, _ in self.points:
            self.assertNotIn((var, value), p0_measured, key)

    def test_repeat_is_the_only_unchanged_point(self):
        reps = [k for k, _, _, _, ex, _ in self.points if ex and ex.startswith("REPEAT:")]
        self.assertEqual(reps, ["s14_p0_repeat"])

    def test_scripts_and_checksums(self):
        self.assertEqual([l.split()[0] for l in self.f["points.txt"].decode().splitlines()], [p[0] for p in self.points])
        self.assertEqual(self.info["names"]["release"], "GO2_G_A063_PC2_STAIRS_SWEEP_v1")
        z = zipfile.ZipFile(io.BytesIO(self.data))
        self.assertTrue(all(n.startswith(self.info["names"]["prefix"]) for n in z.namelist()))
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

    def test_build_does_not_leak_into_g_a062_builder(self):
        self.assertEqual(bb.PROVISIONAL_WORK_ID, "G-A062")
        self.assertEqual(bb.POINTS[0][0], "q0_lin_vel_z_l2_m1p5")
        self.assertEqual(bb.names("G-A062")["release"], "GO2_G_A062_PC2_BATCH60_v1")

    def test_expected_rewards_match_candidate(self):
        for key, *_ in self.points:
            exp = json.loads(self.f[f"runs/{key}/expected_rewards.json"])["candidate"]
            self.assertEqual(exp, self.rw(key, "candidate/quadruped_rewards.py"), key)


if __name__ == "__main__":
    unittest.main()
