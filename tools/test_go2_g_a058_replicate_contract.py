"""Contract for the G-A058 replicate package and launcher (2026-09-30).

왜 있는가.  발행 전에 (1) 세 행이 기준 회차의 학습 env.yaml 보상과 정확히 같고 학습 seed 만 42/43/44 인지,
(2) 러너·shared 가 G-A055 v2 바이트 그대로이고 실행별 체크섬이 통과하는지, (3) G-A057 에서 이름만 바꾼 일괄 러너가
가짜 러너로 실제로 돌 때 완료·실패 계속·재개·학습 전 실패 중단을 지키는지 확인한다.

    python -m unittest tools.test_go2_g_a058_replicate_contract
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
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
import build_go2_g_a058_replicate_package as builder  # noqa: E402
import build_go2_g_a057_sweep_package as a057  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402
from test_go2_g_a057_sweep_contract import FAKE_RUNNER  # noqa: E402

BASH = shutil.which("bash")
EXPECT = {"a048_seed42": ("go2_g_a048_a033_lin_vel_z_m125", 42),
          "a043_seed43": ("go2_g_a043_a033_lin_vel_z_m15", 43),
          "a043_seed44": ("go2_g_a043_a033_lin_vel_z_m15", 44)}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Package(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, cls.info = builder.build()
        cls.files = cls.info["files"]

    def test_1_order_is_the_three_agreed_rows(self) -> None:
        order = [l.split()[0] for l in self.files["sweep_order.txt"].decode().splitlines()]
        self.assertEqual(order, ["a048_seed42", "a043_seed43", "a043_seed44"])

    def test_2_rewards_equal_base_env_and_seed_per_row(self) -> None:
        for key, (arm, seed) in EXPECT.items():
            want = builder.weights6(arm)
            got = reward_dict(self.files[f"runs/{key}/candidate/quadruped_rewards.py"].decode())
            self.assertEqual(got, want, key)
            cfg = self.files[f"runs/{key}/run_config.env"].decode()
            self.assertIn(f"\nTRAIN_SEED={seed}\n", cfg, key)
            self.assertIn("\nWORK_ID=G-A058\n", cfg)
            self.assertIn(f"\nKEEP_DIR_NAME=go2_g_a058_{key}\n", cfg)
            exp = json.loads(self.files[f"runs/{key}/expected_rewards.json"])
            self.assertEqual(exp["candidate"], want)
        # A048 과 A043 은 lin_vel_z 한 항만 다르다
        a, b = builder.weights6(EXPECT["a048_seed42"][0]), builder.weights6(EXPECT["a043_seed43"][0])
        self.assertEqual([k for k in a if a[k] != b[k]], ["lin_vel_z_l2"])

    def test_3_shared_bytes_are_the_g_a055_v2_bytes(self) -> None:
        src = a057.shared_files(a057.source_payload())
        for k, v in src.items():
            self.assertEqual(self.files["shared/" + k], v, k)

    def test_4_each_materialised_tree_matches_its_checksums(self) -> None:
        for key in EXPECT:
            tree = {k[len("shared/"):]: v for k, v in self.files.items() if k.startswith("shared/")}
            tree.update({k[len(f"runs/{key}/"):]: v for k, v in self.files.items() if k.startswith(f"runs/{key}/")})
            sums = tree.pop("PACKAGE_SHA256SUMS.txt").decode().splitlines()
            listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in sums}
            self.assertEqual(set(listed), set(tree), key)
            for name, digest in listed.items():
                self.assertEqual(sha(tree[name]), digest, f"{key}:{name}")

    def test_5_launcher_is_g_a057_renamed_only_and_parses(self) -> None:
        mine = self.files["run_sweep.sh"].decode()
        self.assertEqual(mine.encode(), builder.LAUNCHER.read_bytes().replace(b"\r\n", b"\n"))
        base = (ROOT / "tools/go2_g_a057_run_sweep.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
        renamed = re.sub("go2_g_a057", "go2_g_a058", base)
        renamed = renamed.replace("GO2_G_A057", "GO2_G_A058").replace("G-A057", "G-A058")
        code = lambda t: [l for l in t.splitlines() if not l.lstrip().startswith(("#", "echo"))]
        self.assertEqual(code(mine), code(renamed))  # 설명 문구(주석·echo) 밖의 코드는 이름 교체뿐이다
        if BASH:
            r = subprocess.run([BASH, "-n", "-"], input=mine.encode(), capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_6_readout_keeps_the_codex_corrections(self) -> None:
        plan = json.loads(self.files["SWEEP_PLAN.json"])
        text = json.dumps(plan["readout"], ensure_ascii=False)
        self.assertIn("효과 판정 문턱으로 쓰지 않는다", json.dumps(builder.PURPOSE, ensure_ascii=False))
        self.assertIn("충돌하면 그대로 공개", text)
        self.assertIn("탐색용 기준", text)
        self.assertNotIn("효과로 읽지 않는다", text)


@unittest.skipUnless(BASH, "bash needed")
class Launcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, _ = builder.build()
        cls.keys = list(EXPECT)

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        zipfile.ZipFile(io.BytesIO(self.data)).extractall(self.tmp / "pkg")
        self.root = self.tmp / "pkg/go2_g_a058"
        self.keep = self.tmp / "keep"
        self.keep.mkdir()
        self.runner = self.tmp / "fake_runner.sh"
        self.runner.write_bytes(FAKE_RUNNER.encode())
        self.plan = self.tmp / "plan.txt"
        self.calls = self.tmp / "calls.txt"
        self.plan.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def behave(self, **beh: str) -> None:
        self.plan.write_text("".join(f"{k} {v}\n" for k, v in beh.items()), encoding="utf-8")

    def run_inner(self) -> int:
        env = {**os.environ, "GO2_SWEEP_TEST_MODE": "1", "GO2_SWEEP_KEEP_BASE": self.keep.as_posix(),
               "GO2_SWEEP_TEST_RUNNER": self.runner.as_posix(), "GO2_SWEEP_TEST_FREE_GB": "500",
               "GO2_SWEEP_WORK": (self.tmp / "work").as_posix(), "FAKE_PLAN": self.plan.as_posix(),
               "FAKE_CALLS": self.calls.as_posix()}
        r = subprocess.run([BASH, (self.root / "run_sweep.sh").as_posix(), "--inner"], env=env,
                           capture_output=True, timeout=600)
        self.last = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        return r.returncode

    def status(self) -> dict[str, str]:
        p = self.keep / "go2_g_a058_sweep/SWEEP_STATUS.tsv"
        out = {}
        if p.is_file():
            for row in csv.DictReader(p.open(encoding="utf-8"), delimiter="\t"):
                out[row["key"]] = row["status"]
        return out

    def test_a_all_three_complete_in_order(self) -> None:
        self.assertEqual(self.run_inner(), 0, self.last)
        self.assertEqual(self.status(), {k: "DONE" for k in self.keys})
        calls = [l.split()[0] for l in self.calls.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(calls, self.keys)
        for k in self.keys:
            self.assertTrue((self.keep / f"GO2_G_A058_{k.upper()}_RESULT.zip").is_file())

    def test_b_one_failure_continues_and_rerun_resumes_only_it(self) -> None:
        self.behave(**{self.keys[1]: "fail_once"})
        self.assertEqual(self.run_inner(), 0, self.last)
        self.assertEqual(self.status()[self.keys[1]], "RUN_ERROR")
        self.assertEqual(self.status()[self.keys[2]], "DONE")
        self.calls.write_text("", encoding="utf-8")
        self.assertEqual(self.run_inner(), 0, self.last)
        calls = self.calls.read_text(encoding="utf-8").splitlines()
        self.assertEqual(calls, [f"{self.keys[1]} resume=1"])
        self.assertEqual(self.status(), {k: ("DONE" if k == self.keys[1] else "SKIP_DONE") for k in self.keys})

    def test_c_failure_before_training_stops_23(self) -> None:
        self.behave(**{self.keys[0]: "fail_pre"})
        self.assertEqual(self.run_inner(), 23, self.last)


if __name__ == "__main__":
    unittest.main()
