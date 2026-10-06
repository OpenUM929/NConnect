"""PC2 일괄 실행 패키지(G-A062) 계약 테스트 — tools/build_go2_pc2_batch_package.py.

python -B -m unittest tools.test_go2_pc2_batch_package
"""
from __future__ import annotations

import csv
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
from go2_tuning_config import reward_dict  # noqa: E402
from test_go2_pc2_point_contract import FAKE_RUNNER  # noqa: E402

BASH = shutil.which("bash")
CHECKS = ROOT / "workspace/training/quadruped/candidate_suite_checks.py"
B1_ENV = ROOT / "workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42/training/env.yaml"
KEYS = [p[0] for p in bb.POINTS]


class Package(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.info = bb.build()
        cls.f = cls.info["files"]

    def rw(self, key, role):
        return reward_dict(self.f[f"runs/{key}/{role}"].decode())

    def test_each_point_changes_exactly_one_term_from_its_parent(self):
        for key, pc, var, value, _, _ in bb.POINTS:
            cand = {**bb.EXTRA_DEFAULTS, **self.rw(key, "candidate/quadruped_rewards.py")}
            par = {**bb.EXTRA_DEFAULTS, **self.rw(key, "reference/baseline_quadruped_rewards.py")}
            self.assertEqual([k for k in bb.TERMS if cand[k] != par[k]], [var], key)
            self.assertEqual(cand[var], value, key)
            self.assertEqual(par["lin_vel_z_l2"], pc.get("lin_vel_z_l2", -1.25), key)
            self.assertEqual(cand["track_lin_vel_xy_exp"], 1.5, key)  # 트랙 고정

    def test_q0_children_sit_on_a043_rewards(self):
        q0 = {**bb.EXTRA_DEFAULTS, **self.rw(KEYS[0], "candidate/quadruped_rewards.py")}
        for key, pc, *_ in bb.POINTS:
            if pc:
                par = {**bb.EXTRA_DEFAULTS, **self.rw(key, "reference/baseline_quadruped_rewards.py")}
                self.assertEqual(par, q0, key)

    def test_expected_rewards_carry_the_extra_terms(self):
        exp = json.loads(self.f["runs/q1_track_ang_vel_z_exp_p1p0/expected_rewards.json"])["candidate"]
        self.assertEqual((exp["track_ang_vel_z_exp"], exp["lin_vel_z_l2"], exp["dof_torques_l2"]), (1.0, -1.5, -2e-4))
        exp = json.loads(self.f["runs/p4_dof_torques_l2_m5e_5/expected_rewards.json"])["candidate"]
        self.assertEqual((exp["dof_torques_l2"], exp["track_ang_vel_z_exp"]), (-5e-5, 0.75))

    def test_points_order_and_scripts(self):
        self.assertEqual([l.split()[0] for l in self.f["points.txt"].decode().splitlines()], KEYS)
        for name in ("run_all.sh", "run_point.sh"):
            self.assertNotIn(b"\r\n", self.f[name], name)
        if BASH:
            for name in ("run_all.sh", "run_point.sh"):
                with tempfile.NamedTemporaryFile("wb", suffix=".sh", delete=False) as t:
                    t.write(self.f[name])
                try:
                    self.assertEqual(subprocess.run([BASH, "-n", t.name]).returncode, 0, name)
                finally:
                    os.unlink(t.name)

    def test_zip_names_and_checksums(self):
        z = zipfile.ZipFile(io.BytesIO(self.data))
        prefix = self.info["names"]["prefix"]
        self.assertTrue(all(n.startswith(prefix) for n in z.namelist()))
        self.assertEqual(self.info["names"]["release"], "GO2_G_A062_PC2_BATCH60_v1")
        sums = dict(reversed(l.split("  ", 1)) for l in self.f["SHA256SUMS.txt"].decode().splitlines())
        self.assertEqual(len(sums), len(self.f) - 1)


class History(unittest.TestCase):
    def test_only_q0_is_exempt_and_others_have_no_history(self):
        for key, _, var, value, ex, _ in bb.POINTS:
            own = ("| G-A062 ", f"_keep/go2_g_a062_pc2_{key}")  # 회수 뒤 생긴 자기 결과는 이력이 아니다
            hits = [h for h in bb.tb.history_conflicts(var, value) if not any(o in h for o in own)]
            if key == KEYS[0]:
                self.assertTrue(hits and ex, hits)  # A043 의 −1.5 이력이 잡히고, 예외로 명시돼 있다
            else:
                self.assertIsNone(ex, key)
                self.assertEqual(hits, [], key)

    def test_tested_value_without_exemption_is_refused(self):
        bad = (("x", {}, "dof_torques_l2", -1e-4, None, "N3 값"),)  # G-A061 N3 에서 시험됨
        orig = bb.POINTS
        bb.POINTS = bad
        try:
            with self.assertRaises(ValueError):
                bb.build()
        finally:
            bb.POINTS = orig


@unittest.skipUnless(B1_ENV.is_file(), "PC2 B1 env.yaml 없음")
class ServerEnvCheck(unittest.TestCase):
    """서버 env-rewards 검사가 추가한 track_ang_vel_z_exp 와 lin_vel_z 를 실제로 대조하는지."""

    def check(self, text, key):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "env.yaml").write_text(text, encoding="utf-8")
            (tmp / "exp.json").write_bytes(bb.build()[1]["files"][f"runs/{key}/expected_rewards.json"])
            return subprocess.run([sys.executable, "-B", str(CHECKS), "env-rewards", str(tmp / "env.yaml"),
                                   str(tmp / "exp.json"), "candidate"], capture_output=True, text=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    @staticmethod
    def set_weight(text, term, value):
        lines = text.splitlines()
        i = lines.index(f"  {term}:")
        j = next(k for k in range(i, i + 12) if lines[k].strip().startswith("weight:"))
        lines[j] = lines[j].split("weight:")[0] + f"weight: {value}"
        return "\n".join(lines) + "\n"

    def test_track_ang_point(self):
        key = "q1_track_ang_vel_z_exp_p1p0"
        text = B1_ENV.read_text(encoding="utf-8")
        r = self.check(text, key)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("track_ang_vel_z_exp", r.stderr)
        text = self.set_weight(self.set_weight(text, "lin_vel_z_l2", -1.5), "track_ang_vel_z_exp", 1.0)
        self.assertEqual(self.check(text, key).returncode, 0)


@unittest.skipUnless(BASH, "bash needed")
class RunAll(unittest.TestCase):
    def setUp(self):
        data, info = bb.build()
        self.tmp = Path(tempfile.mkdtemp())
        zipfile.ZipFile(io.BytesIO(data)).extractall(self.tmp / "pkg")
        self.root = self.tmp / "pkg" / info["names"]["prefix"].rstrip("/")
        self.keep, self.work = self.tmp / "keep", self.tmp / "work"
        self.keep.mkdir()
        (self.tmp / "fake_runner.sh").write_bytes(FAKE_RUNNER.encode())
        (self.tmp / "plan.txt").write_text("", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_all(self):
        env = {**os.environ, "GO2_POINT_TEST_MODE": "1", "GO2_POINT_KEEP_BASE": self.keep.as_posix(),
               "GO2_POINT_TEST_RUNNER": (self.tmp / "fake_runner.sh").as_posix(), "GO2_POINT_TEST_FREE_GB": "500",
               "GO2_POINT_WORK": self.work.as_posix(), "FAKE_PLAN": (self.tmp / "plan.txt").as_posix(),
               "FAKE_CALLS": (self.tmp / "calls.txt").as_posix(), "GO2_BATCH_LOG_DIR": (self.tmp / "log").as_posix()}
        r = subprocess.run([BASH, (self.root / "run_all.sh").as_posix()], env=env, capture_output=True, timeout=1200)
        self.last = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        return r.returncode

    def calls(self):
        return [l.split()[0] for l in (self.tmp / "calls.txt").read_text(encoding="utf-8").splitlines() if l.strip()]

    def statuses(self):
        st = next(self.keep.glob("*_pc2_points/POINT_STATUS.tsv"))
        with st.open(encoding="utf-8") as fh:
            return [(r["key"], r["status"]) for r in csv.DictReader(fh, delimiter="\t")]

    def test_runs_all_points_in_order_then_skips_done_on_rerun(self):
        self.assertEqual(self.run_all(), 0, self.last)
        self.assertEqual(self.calls(), KEYS)
        self.assertEqual(self.statuses(), [(k, "DONE") for k in KEYS])
        (self.tmp / "calls.txt").write_text("", encoding="utf-8")
        self.assertEqual(self.run_all(), 0, self.last)
        self.assertEqual(self.calls(), [])  # 끝난 점은 재학습하지 않는다

    def test_post_training_failure_continues_to_next_point(self):
        (self.tmp / "plan.txt").write_text(f"{KEYS[1]} fail_once\n", encoding="utf-8")
        self.assertEqual(self.run_all(), 30, self.last)
        self.assertEqual(self.calls(), KEYS)

    def test_package_error_stops_remaining_points(self):
        cfg = self.root / "runs" / KEYS[2] / "run_config.env"
        cfg.write_bytes(cfg.read_bytes() + b"# tampered\n")
        # 패키지 전체 체크섬은 첫 점의 사전 검사에서 걸린다 — 어느 점도 학습하지 않고 일괄 실행이 멈춘다
        self.assertEqual(self.run_all(), 25, self.last)
        self.assertFalse((self.tmp / "calls.txt").exists() and self.calls())
        log = (self.tmp / "log" / "BATCH_RUN.log").read_text(encoding="utf-8")
        self.assertIn(f"[BATCH STOP] environment/package error rc=25 at {KEYS[0]}", log)
        self.assertNotIn(f"[BATCH POINT] {KEYS[1]}", log)


if __name__ == "__main__":
    unittest.main()
