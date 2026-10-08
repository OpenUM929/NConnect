"""Contract tests for H-A001 P0 package and readout (run: python -m unittest tools/test_h1_ha001_p0_package.py)."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

TOOLS = Path(__file__).resolve().parent


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


builder = _mod("build_h1_ha001_p0_package")
readout = _mod("h1_ha001_p0_readout")

CASES = {"plane_vx0p75": (.75, 0), "plane_vx1p00": (1.0, 0), "plane_vx1p25": (1.25, 0),
         "rough_vx0p75": (.75, 0), "rough_vx1p00": (1.0, 0), "turn_vx0p50_L": (.5, .5),
         "turn_vx0p50_R": (.5, -.5), "turn_vx1p00_L": (1.0, .5), "turn_vx1p00_R": (1.0, -.5)}


def fake_case(path: Path, vx, wz, ratio=1.0, yaw_sd=0.15, fall_env=None, rng=None):
    rows = []
    for env in range(4):
        rng = np.random.default_rng(env)  # same noise in every case: only the injected change differs
        for step in range(1, 201):
            t = step * 0.02
            avx = vx * ratio + rng.normal(0, .03)
            awz = wz + rng.normal(0, 1.0) * yaw_sd
            z = 0.9 if not (env == fall_env and step > 150) else 0.4
            rows.append(dict(step=step, time_s=t, env_id=env, cmd_vx=vx, cmd_vy=0, cmd_wz=wz,
                             actual_vx=avx, actual_vy=0, actual_wz=awz, error_xy=abs(avx - vx),
                             error_yaw=abs(awz - wz), speed_xy=abs(avx), root_x=0, root_y=0, root_z=z,
                             terminated=0, truncated=int(step == 200), term_time_out=int(step == 200),
                             term_base_contact=0))
    path.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(path / "steps.csv", index=False)


class PackageTest(unittest.TestCase):
    def test_package_contract(self):
        with tempfile.TemporaryDirectory() as td:
            z = builder.build(Path(td))
            with zipfile.ZipFile(z) as zz:
                names = zz.namelist()
            self.assertTrue(all(n.startswith("h1_ha001/") for n in names), names)
            for n in names:
                self.assertFalse(n.startswith(builder.FORBIDDEN_PREFIXES), n)
            with zipfile.ZipFile(z) as zz:
                blobs = {n: zz.read(n) for n in names}
            for n in names:
                if n.endswith((".sh", ".py", ".txt")):
                    self.assertNotIn(b"\r\n", blobs[n], n)
            sums = blobs.get("h1_ha001/SHA256SUMS.txt").decode().splitlines()
            for line in sums:
                h, n = line.split("  ")
                self.assertEqual(builder.sha(blobs.get(n)), h, n)
            sh = Path(td) / "run.sh"
            sh.write_bytes(blobs.get("h1_ha001/server_run_h1_ha001_p0.sh"))
            bash = shutil.which("bash")
            if bash:
                self.assertEqual(subprocess.run([bash, "-n", str(sh)]).returncode, 0)
            self.assertIn(builder.NAME, blobs.get("h1_ha001/README_H_A001.txt").decode())
            self.assertNotIn(b"\r", (Path(td) / (builder.NAME + ".sha256")).read_bytes())


class ReadoutTest(unittest.TestCase):
    def _harvest(self, root: Path, slow_at=None, wobbly_at=None, fall_at=None):
        rng = np.random.default_rng(0)
        for p in readout.POLICIES:
            for s in readout.SEEDS:
                for c, (vx, wz) in CASES.items():
                    fake_case(root / "cases" / p / f"seed_{s}" / c, vx, wz,
                              ratio=0.85 if c == slow_at else 1.0,
                              yaw_sd=0.25 if c == wobbly_at else 0.15,
                              fall_env=0 if c == fall_at else None, rng=rng)

    def _run(self, **kw):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "H_A001_P0_SPEED_GRID"
            self._harvest(root, **kw)
            subprocess.run([sys.executable, "-I", str(TOOLS / "h1_ha001_p0_readout.py"), str(root)],
                           check=True, capture_output=True)
            return json.loads((root / "readout/P0_SUMMARY.json").read_text(encoding="utf-8"))

    def test_all_pass_keeps_run06(self):
        s = self._run()
        self.assertEqual(s["branch"], "iii_KEEP_RUN06_UPPER_UNKNOWN")
        self.assertEqual(s["run06"]["families"]["plane"]["verified_highest_vx"], 1.25)

    def test_slow_high_command_points_to_A(self):
        s = self._run(slow_at="plane_vx1p25")
        self.assertEqual(s["branch"], "i_A_lin_vel")
        self.assertEqual(s["run06"]["families"]["plane"]["verified_highest_vx"], 1.0)

    def test_yaw_worse_points_to_B(self):
        s = self._run(wobbly_at="rough_vx1p00")
        self.assertEqual(s["branch"], "ii_B_action_rate")

    def test_posture_fall_is_counted(self):
        s = self._run(fall_at="plane_vx1p00")
        self.assertEqual(s["run06"]["families"]["plane"]["verified_highest_vx"], 0.75)
        self.assertEqual(s["branch"], "iv_REJUDGE")


if __name__ == "__main__":
    unittest.main()
