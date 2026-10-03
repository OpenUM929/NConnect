"""PC2 탐색트리 노드 패키지 계약 테스트 (계획 GO2_TRACK_FIXED_SEARCH_TREE_20261003.md §12·§13, Codex §37).

python -B -m unittest tools.test_go2_pc2_tree_package
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
import build_go2_g_a057_sweep_package as a057  # noqa: E402
import build_go2_pc2_point_package as pkg  # noqa: E402
import build_go2_pc2_tree_package as b  # noqa: E402
import go2_pc2_tree_readout as tree  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402
from test_go2_pc2_point_contract import FAKE_RUNNER  # noqa: E402

BASH = shutil.which("bash")
N3, N4, N5, N6 = (k for _, pts in tree.TREE for k, _ in pts)
CHECKS = ROOT / "workspace/training/quadruped/candidate_suite_checks.py"
B1_ENV = ROOT / "workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42/training/env.yaml"


def step(nodes=None, siblings=None):
    return tree.next_step({"nodes": nodes or {}, "siblings": siblings or {}})


class Package(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.info = b.build(step())
        cls.f = cls.info["files"]

    def arm(self, name):
        return self.f[f"runs/{N3}/{name}"]

    def test_1_first_node_is_n3_one_term_on_p0(self):
        self.assertEqual(self.info["key"], N3)
        cand, par = reward_dict(self.arm("candidate/quadruped_rewards.py").decode()), \
            reward_dict(self.arm("reference/baseline_quadruped_rewards.py").decode())
        self.assertEqual(cand.pop("dof_torques_l2"), -1e-4)
        self.assertNotIn("dof_torques_l2", par)  # P0 은 env 기본값이라 줄이 없다
        self.assertNotIn("dof_acc_l2", cand)
        self.assertEqual(cand, par)
        self.assertEqual({k: par[k] for k in tree.pr.A048_REWARDS}, tree.pr.A048_REWARDS)  # track 1.5 고정
        self.assertEqual(par["track_lin_vel_xy_exp"], 1.5)

    def test_2_expected_rewards_carry_both_env_terms(self):
        exp = json.loads(self.arm("expected_rewards.json"))
        self.assertEqual(exp["candidate"]["dof_torques_l2"], -1e-4)
        self.assertEqual(exp["candidate"]["dof_acc_l2"], -2.5e-7)
        cfg = self.arm("run_config.env").decode()
        for line in ("TRAIN_SEED=42", "NUM_ENVS=4096", "MAX_ITERATIONS=1000", "EVAL_CHECKPOINT_ITER=900",
                     "SINGLE_CHANGE_NAME=dof_torques_l2", "SINGLE_CHANGE_FROM=-0.0002", "SINGLE_CHANGE_TO=-0.0001",
                     f"RUN_ID=train_G-A061-Go2_pc2_{N3}_1000"):
            self.assertIn("\n" + line + "\n", cfg)

    def test_3_shared_and_launcher_bytes(self):
        for k, v in a057.shared_files(a057.source_payload()).items():
            self.assertEqual(self.f["shared/" + k], v, k)
        sh = self.f["run_point.sh"]
        self.assertEqual(sh, pkg.LAUNCHER.read_bytes().replace(b"\r\n", b"\n"))
        self.assertNotIn(b"\r\n", sh)
        if BASH:
            r = subprocess.run([BASH, "-n", "-"], input=sh, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_4_checksums(self):
        shared = {k[len("shared/"):]: v for k, v in self.f.items() if k.startswith("shared/")}
        arm = {k[len(f"runs/{N3}/"):]: v for k, v in self.f.items() if k.startswith(f"runs/{N3}/")}
        listed = dict(reversed(l.split("  ", 1)) for l in arm.pop("PACKAGE_SHA256SUMS.txt").decode().splitlines())
        tree_files = {**shared, **arm}
        self.assertEqual(set(listed), set(tree_files))
        for name, digest in listed.items():
            self.assertEqual(a057.sha(tree_files[name]), digest, name)
        top = dict(reversed(l.split("  ", 1)) for l in self.f["SHA256SUMS.txt"].decode().splitlines())
        self.assertEqual(set(top), set(self.f) - {"SHA256SUMS.txt"})

    def test_5_names_are_pc2_and_g_a061(self):
        key, keep, zipn = self.f["points.txt"].decode().split()
        self.assertEqual((key, keep, zipn), (N3, f"go2_g_a061_pc2_{N3}", f"GO2_G_A061_PC2_{N3.upper()}_RESULT.zip"))
        self.assertIn("go2_g_a061_pc2", self.f["point_config.env"].decode())
        self.assertTrue(self.info["names"]["release"].startswith("GO2_G_A061_PC2_TREE_"))


class Gates(unittest.TestCase):
    def test_only_run_steps_build(self):
        for st in (step({N3: "INSUFFICIENT_UNRECOVERABLE"}), step({N3: "INSUFFICIENT"}),
                   step({N3: "WORSENED", N5: "WORSENED"}), step({N3: "IMPROVED", N4: "IMPROVED"})):
            with self.assertRaises(ValueError):
                b.build(st)

    def test_same_value_history_refuses(self):
        with self.assertRaises(ValueError) as e:  # flat −0.5 는 A047 에서 시험됨
            b.build({"action": "RUN", "node": "x_flat", "variable": "flat_orientation_l2", "value": -0.5, "parent_changes": {}})
        self.assertIn("EXCLUDED_HISTORY", str(e.exception))
        self.assertEqual(b.history_conflicts("dof_acc_l2", -3e-7), [])  # G-A053 미실행은 이력 아님
        self.assertFalse(b.line_hit("| G-A999 | dof_acc -2.5e-7 -> -1e-7 | 완료 |", "dof_acc_l2", -1.25e-7))

    def test_parent_winner_carried_and_child_changes_one_term(self):
        st = step({N3: "IMPROVED", N4: "EXCLUDED_HISTORY"})
        self.assertEqual((st["node"], st["parent_changes"]), (N5, {"dof_torques_l2": -1e-4}))
        _, info = b.build(st)
        f = info["files"]
        cand = reward_dict(f[f"runs/{N5}/candidate/quadruped_rewards.py"].decode())
        par = reward_dict(f[f"runs/{N5}/reference/baseline_quadruped_rewards.py"].decode())
        self.assertEqual((cand["dof_torques_l2"], cand["dof_acc_l2"]), (-1e-4, -1.25e-7))
        self.assertEqual(par["dof_torques_l2"], -1e-4)
        self.assertNotIn("dof_acc_l2", par)
        self.assertEqual(json.loads(f[f"runs/{N5}/experiment.json"])["single_change"],
                         {"name": "dof_acc_l2", "from": -2.5e-7, "to": -1.25e-7})


class HistoryNumbers(unittest.TestCase):
    """§39-R3 회귀: 수 경계가 있는 정확한 비교."""

    def test_prefix_is_not_the_same_value(self):
        self.assertFalse(b.line_hit("| G-A999 | dof_torques -2e-4 -> -0.00015 | 완료 |", "dof_torques_l2", -1e-4))

    def test_equal_spellings_match(self):
        for v in ("-0.00010", "-1e-4", "\u22121e\u22124", "-1.0e-04", "\u22120.0001"):
            self.assertTrue(b.line_hit(f"| G-A999 | dof_torques \u22122e\u22124\u2192{v} | 완료 |", "dof_torques_l2", -1e-4), v)

    def test_unrun_row_and_other_term_are_not_history(self):
        self.assertFalse(b.line_hit("| G-A999 | dof_torques -2e-4 -> -1e-4 | 미실행 |", "dof_torques_l2", -1e-4))
        self.assertFalse(b.line_hit("| G-A999 | dof_acc -2e-4 -> -1e-4 | 완료 |", "dof_torques_l2", -1e-4))
        self.assertFalse(b.line_hit("| G-A999 | dof_torques -2e-4 -> -1.5e-4 | 22 | 0.0001 |", "dof_torques_l2", -1e-4))

    def test_folder_names_need_a_boundary(self):
        self.assertTrue(b.folder_hit(f"go2_g_a061_pc2_{N3}", "dof_torques_l2", -1e-4))
        self.assertFalse(b.folder_hit("go2_x_dof_torques_l2_m1e_45", "dof_torques_l2", -1e-4))
        self.assertFalse(b.folder_hit("go2_x_dof_torques_l2_m1p5e_4", "dof_torques_l2", -1e-4))
        self.assertTrue(b.folder_hit(f"go2_g_a061_pc2_{N5}", "dof_acc_l2", -1.25e-7))
        self.assertFalse(b.folder_hit(f"go2_g_a061_pc2_{N5}", "dof_acc_l2", -1.25e-6))


class ParentHarvestRecord(unittest.TestCase):
    """§39-3: 부모가 P0 가 아니면 P0 경로를 판독 부모로 적지 않는다."""

    def parent(self, st, harvest=None):
        _, info = b.build(st, parent_harvest=harvest)
        return json.loads(info["files"][f"runs/{info['key']}/experiment.json"])["parent"]

    def test_records(self):
        self.assertEqual(self.parent(step())["harvest_for_readout"], b.P0_HARVEST)
        st = step({N3: "IMPROVED", N4: "EXCLUDED_HISTORY"})
        self.assertIn("미지정", self.parent(st)["harvest_for_readout"])
        self.assertEqual(self.parent(st, "workspace/_keep/go2_g_a061_pc2_" + N3)["harvest_for_readout"],
                         "workspace/_keep/go2_g_a061_pc2_" + N3)

    def test_cli_refuses_bad_state(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            p.write_text(json.dumps({"nodes": {N3: "TYPO"}}), encoding="utf-8")
            self.assertEqual(b.main(["--tree-state", str(p), "--check"]), 2)


@unittest.skipUnless(B1_ENV.is_file(), "PC2 B1 env.yaml 없음")
class ServerEnvCheck(unittest.TestCase):
    """서버 러너의 env-rewards 검사가 목록 밖 항 값을 실제로 대조하는지."""

    def run_check(self, env_text):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "env.yaml").write_text(env_text, encoding="utf-8")
            _, info = b.build(step())
            (tmp / "exp.json").write_bytes(info["files"][f"runs/{N3}/expected_rewards.json"])
            return subprocess.run([sys.executable, "-B", str(CHECKS), "env-rewards", str(tmp / "env.yaml"),
                                   str(tmp / "exp.json"), "candidate"], capture_output=True, text=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_env_check_catches_unapplied_torque_term(self):
        text = B1_ENV.read_text(encoding="utf-8")
        r = self.run_check(text)  # B1 은 −0.0002 — 줄이 적용되지 않은 학습이면 거부돼야 한다
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("dof_torques_l2", r.stderr)
        lines = text.splitlines()
        i = lines.index("  dof_torques_l2:")
        j = next(k for k in range(i, i + 12) if lines[k].strip().startswith("weight:"))
        lines[j] = lines[j].split("weight:")[0] + "weight: -0.0001"
        r = self.run_check("\n".join(lines) + "\n")
        self.assertEqual(r.returncode, 0, r.stderr)


@unittest.skipUnless(BASH, "bash needed")
class Launcher(unittest.TestCase):
    def setUp(self):
        self.data, info = b.build(step())
        self.tmp = Path(tempfile.mkdtemp())
        zipfile.ZipFile(io.BytesIO(self.data)).extractall(self.tmp / "pkg")
        self.root = self.tmp / "pkg" / info["names"]["prefix"].rstrip("/")
        self.keep, self.work = self.tmp / "keep", self.tmp / "work"
        self.keep.mkdir()
        (self.tmp / "fake_runner.sh").write_bytes(FAKE_RUNNER.encode())
        (self.tmp / "plan.txt").write_text("", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_point(self, *args):
        env = {**os.environ, "GO2_POINT_TEST_MODE": "1", "GO2_POINT_KEEP_BASE": self.keep.as_posix(),
               "GO2_POINT_TEST_RUNNER": (self.tmp / "fake_runner.sh").as_posix(), "GO2_POINT_TEST_FREE_GB": "500",
               "GO2_POINT_WORK": self.work.as_posix(), "FAKE_PLAN": (self.tmp / "plan.txt").as_posix(),
               "FAKE_CALLS": (self.tmp / "calls.txt").as_posix()}
        r = subprocess.run([BASH, (self.root / "run_point.sh").as_posix(), *args], env=env, capture_output=True, timeout=600)
        self.last = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        return r.returncode

    def test_runs_only_n3_and_refuses_other_keys(self):
        self.assertEqual(self.run_point("--only", N4), 64, self.last)
        self.assertEqual(list(self.keep.iterdir()), [])
        self.assertEqual(self.run_point("--only", N3), 0, self.last)
        self.assertEqual((self.tmp / "calls.txt").read_text(encoding="utf-8").split(), [N3, "resume=0"])
        st = next(self.keep.glob("*_pc2_points/POINT_STATUS.tsv"))
        with st.open(encoding="utf-8") as fh:
            self.assertEqual([(r["key"], r["status"]) for r in csv.DictReader(fh, delimiter="\t")], [(N3, "DONE")])

    def test_post_training_failure_resumes_without_retraining_marker_loss(self):
        (self.tmp / "plan.txt").write_text(f"{N3} fail_once\n", encoding="utf-8")
        self.assertEqual(self.run_point("--only", N3), 30, self.last)
        ev = next(self.keep.glob(f"*{N3}")) / "training" / "EVIDENCE_KEEP.txt"
        ev.write_text("checkpoint evidence", encoding="utf-8")
        (self.tmp / "calls.txt").write_text("", encoding="utf-8")
        self.assertEqual(self.run_point("--only", N3), 0, self.last)
        self.assertEqual((self.tmp / "calls.txt").read_text(encoding="utf-8").split(), [N3, "resume=1"])
        self.assertEqual(ev.read_text(encoding="utf-8"), "checkpoint evidence")


if __name__ == "__main__":
    unittest.main()
