"""Contract for the G-A057 sweep package and launcher (2026-09-29, Codex 작업 지시 §6·3·4).

왜 있는가.  발행 전에 (1) 실행 목록·패키지 바이트·실행별 체크섬이 계획대로인지, (2) 일괄 러너가 GPU 없이 가짜 러너로
실제로 돌 때 실패·재개·중단 규칙을 지키는지, (3) 실행 안전 중단과 실행 실패와 완료가 서로 다른 상태 단어로 남는지를
확인한다.  러너는 평가 결과를 보고 멈추지 않는다 — 그 판단은 판독기(tools/go2_g_a057_prereg_readout.py)의 몫이다.

    python -m unittest tools.test_go2_g_a057_sweep_contract
"""
from __future__ import annotations

import csv
import hashlib
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
import build_go2_g_a057_sweep_package as builder  # noqa: E402
import go2_g_a057_sweep_plan as planmod  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict  # noqa: E402

BASH = shutil.which("bash")

FAKE_RUNNER = r'''#!/usr/bin/env bash
# fake per-arm runner for the GPU-free contract test.  Behaviour per key comes from $FAKE_PLAN ("key behaviour").
set -u
cfg="$PACKAGE_ROOT/run_config.env"
keep_name=$(sed -n 's/^KEEP_DIR_NAME=//p' "$cfg")
zip_name=$(sed -n 's/^RESULT_ZIP_NAME=//p' "$cfg")
key=$(basename "$PACKAGE_ROOT")
keep="$GO2_SWEEP_KEEP_BASE/$keep_name"
zip="$GO2_SWEEP_KEEP_BASE/$zip_name"
echo "$key resume=$GO2_RESUME" >>"$FAKE_CALLS"
beh=$(awk -v k="$key" '$1==k {print $2}' "$FAKE_PLAN")
beh=${beh:-ok}
if [[ "$beh" == fail_once && "$GO2_RESUME" == 1 ]]; then beh=ok; fi
package() {  # state collection decision
  mkdir -p "$keep"
  printf 'DECISION=%s\n' "$3" >"$keep/RUNNER_STATUS.txt"
  printf 'RESULT_STATE=%s\nCOLLECTION_STATUS=%s\n' "$1" "$2" >"$keep/RESULT_STATUS.txt"
  echo "payload $key" >"$zip"
  sha256sum "$zip" | awk -v n="$zip_name" '{print $1"  "n}' >"$zip.sha256"
}
case "$beh" in
  ok) mkdir -p "$keep/training"; : >"$keep/training/TRAIN_STARTED.marker"; echo TRAIN_RC=0 >"$keep/training/TRAIN_STATUS.txt"
      package FULL FULL_69_COMPLETE SUITE_COMPLETE; exit 0 ;;
  stationary) mkdir -p "$keep/training"; : >"$keep/training/TRAIN_STARTED.marker"; echo TRAIN_RC=0 >"$keep/training/TRAIN_STATUS.txt"
      package FULL FULL_69_COMPLETE SUITE_COMPLETE; exit 0 ;;   # the real runner collects all 69 for a stationary policy
  fail_train|fail_once) mkdir -p "$keep/training"; : >"$keep/training/TRAIN_STARTED.marker"; echo TRAIN_RC=1 >"$keep/training/TRAIN_STATUS.txt"; exit 3 ;;
  fail_pre) exit 2 ;;
  nonfinite) mkdir -p "$keep/training"; : >"$keep/training/TRAIN_STARTED.marker"; echo TRAIN_RC=0 >"$keep/training/TRAIN_STATUS.txt"
      package FULL INCOMPLETE_EARLY_STOP CATASTROPHE_TRAINING_NONFINITE; exit 0 ;;
  incomplete) mkdir -p "$keep/training"; : >"$keep/training/TRAIN_STARTED.marker"; echo TRAIN_RC=0 >"$keep/training/TRAIN_STATUS.txt"
      package FULL INCOMPLETE_COLLECTION SUITE_COMPLETE; exit 0 ;;
  eval_error) mkdir -p "$keep/training"; : >"$keep/training/TRAIN_STARTED.marker"; echo TRAIN_RC=0 >"$keep/training/TRAIN_STATUS.txt"; exit 5 ;;
esac
'''


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Package(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, cls.info = builder.build()
        cls.z = zipfile.ZipFile(io.BytesIO(cls.data))
        cls.files = cls.info["files"]
        cls.plan = cls.info["plan"]

    def test_1_plan_counts_and_no_substitution(self) -> None:
        st = [r["status"] for r in self.plan["runs"]]
        self.assertEqual((st.count("NEW_TRAIN"), st.count("REUSE"), st.count("BASE_SHARED"), st.count("EVAL_ONLY")), (12, 6, 5, 0))
        ang = next(r for r in self.plan["runs"] if r["variable"] == "ang_vel_xy_l2" and r["value"] == -0.08)
        self.assertEqual(ang["status"], "NEW_TRAIN")  # A038(lin −2.0) 은 A048 위 −0.08 을 대신하지 않는다

    def test_2_order_is_the_twelve_rows_unchanged(self) -> None:
        order = [l.split()[0] for l in self.files["sweep_order.txt"].decode().splitlines()]
        self.assertEqual(order, [r["key"] for r in self.plan["runs"] if r["status"] == "NEW_TRAIN"])
        self.assertFalse(any("a043" in k or "seed43" in k or "calibration" in k for k in order))

    def test_3_each_arm_changes_exactly_one_reward(self) -> None:
        base = {k: float(self.plan["base_env_rewards"][k]) for k in REWARD_NAMES}
        for r in self.info["new_rows"]:
            with self.subTest(key=r["key"]):
                cand = reward_dict(self.files[f"runs/{r['key']}/candidate/quadruped_rewards.py"].decode())
                diff = [k for k in REWARD_NAMES if cand[k] != base[k]]
                self.assertEqual(diff, [r["variable"]])
                self.assertEqual(cand[r["variable"]], float(r["value"]))

    def test_4_shared_bytes_are_the_g_a055_v2_bytes(self) -> None:
        src = builder.source_payload()
        shared = {k[len("shared/"):]: v for k, v in self.files.items() if k.startswith("shared/")}
        self.assertEqual(shared, {k: v for k, v in src.items() if k not in builder.OVERLAY})

    def test_5_each_materialised_tree_matches_its_checksums(self) -> None:
        shared = {k[len("shared/"):]: v for k, v in self.files.items() if k.startswith("shared/")}
        for r in self.info["new_rows"]:
            with self.subTest(key=r["key"]):
                pre = f"runs/{r['key']}/"
                tree = {**shared, **{k[len(pre):]: v for k, v in self.files.items() if k.startswith(pre)}}
                sums = tree.pop("PACKAGE_SHA256SUMS.txt").decode().splitlines()
                listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in sums}
                self.assertEqual(listed, {k: sha(v) for k, v in tree.items()})

    def test_6_preregistration_is_shipped_and_pinned(self) -> None:
        pre = self.files["PREREGISTRATION.json"]
        self.assertEqual(pre, builder.PREREG_JSON.read_bytes().replace(b"\r\n", b"\n"))
        for r in self.info["new_rows"]:
            exp = json.loads(self.files[f"runs/{r['key']}/experiment.json"])
            self.assertEqual(exp["preregistration"]["sha256"], sha(pre))
            self.assertEqual(exp["preregistration"]["row"], r["key"])
            self.assertEqual(exp["promotion"], "forbidden_sweep_data_only")

    def test_7_launcher_is_the_repo_launcher_and_parses(self) -> None:
        self.assertEqual(self.files["run_sweep.sh"], builder.LAUNCHER.read_bytes().replace(b"\r\n", b"\n"))
        self.assertNotIn(b"\r\n", self.files["run_sweep.sh"])
        if BASH:
            r = subprocess.run([BASH, "-n", str(builder.LAUNCHER)], capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_8_guide_separates_run_stops_from_evaluation(self) -> None:
        g = builder.guide(self.info["new_rows"], "x")
        for word in ("SAFETY_STOP_NONFINITE", "RUN_ERROR", "COLLECTION_FAILED", "평가 결과가 나쁘다는 이유로 멈추거나 건너뛰지 않는다"):
            self.assertIn(word, g)


@unittest.skipUnless(BASH, "bash 없음")
class Launcher(unittest.TestCase):
    """가짜 러너로 일괄 러너 --inner 를 실제로 돌린다 (GO2_SWEEP_TEST_MODE=1)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data, cls.info = builder.build()
        cls.keys = [r["key"] for r in cls.info["new_rows"]]

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        zipfile.ZipFile(io.BytesIO(self.data)).extractall(self.tmp / "pkg")
        self.root = self.tmp / "pkg/go2_g_a057"
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

    def run_inner(self, free_gb: int = 500) -> int:
        env = {**os.environ, "GO2_SWEEP_TEST_MODE": "1", "GO2_SWEEP_KEEP_BASE": self.keep.as_posix(),
               "GO2_SWEEP_TEST_RUNNER": self.runner.as_posix(), "GO2_SWEEP_TEST_FREE_GB": str(free_gb),
               "GO2_SWEEP_WORK": (self.tmp / "work").as_posix(), "FAKE_PLAN": self.plan.as_posix(),
               "FAKE_CALLS": self.calls.as_posix()}
        r = subprocess.run([BASH, (self.root / "run_sweep.sh").as_posix(), "--inner"], env=env,
                           capture_output=True, timeout=600)
        self.last = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        return r.returncode

    def status(self) -> list[dict]:
        p = self.keep / "go2_g_a057_sweep/SWEEP_STATUS.tsv"
        return list(csv.DictReader(p.open(encoding="utf-8"), delimiter="\t")) if p.is_file() else []

    def last_status(self) -> dict[str, str]:
        out = {}
        for row in self.status():
            out[row["key"]] = row["status"]
        return out

    def test_a_one_failure_is_recorded_and_the_loop_continues(self) -> None:
        self.behave(**{self.keys[1]: "fail_train"})
        self.assertEqual(self.run_inner(), 0, self.last)
        st = self.last_status()
        self.assertEqual(st[self.keys[1]], "RUN_ERROR")
        self.assertEqual(sum(v == "DONE" for v in st.values()), 11)

    def test_b_rerun_skips_done_arms_untouched_and_resumes_the_failed_one(self) -> None:
        self.behave(**{self.keys[2]: "fail_once"})
        self.assertEqual(self.run_inner(), 0, self.last)
        done0 = self.keys[0]
        before = {p.name: sha(p.read_bytes()) for p in (self.keep / f"go2_g_a057_{done0}").rglob("*") if p.is_file()}
        self.calls.write_text("", encoding="utf-8")
        self.assertEqual(self.run_inner(), 0, self.last)
        after = {p.name: sha(p.read_bytes()) for p in (self.keep / f"go2_g_a057_{done0}").rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        calls = self.calls.read_text(encoding="utf-8").split("\n")
        self.assertEqual([c for c in calls if c], [f"{self.keys[2]} resume=1"])
        self.assertEqual(self.last_status()[self.keys[2]], "DONE")
        self.assertIn("SKIP_DONE", {r["status"] for r in self.status()})

    def test_c_failure_before_training_stops_the_sweep_23(self) -> None:
        self.behave(**{self.keys[0]: "fail_pre"})
        self.assertEqual(self.run_inner(), 23, self.last)

    def test_d_low_disk_stops_20(self) -> None:
        self.assertEqual(self.run_inner(free_gb=5), 20, self.last)
        self.assertEqual(self.status()[0]["status"], "ABORT_DISK")

    def test_e_result_zip_without_folder_is_blocked_not_overwritten(self) -> None:
        cfg = (self.root / f"runs/{self.keys[0]}/run_config.env").read_text(encoding="utf-8")
        zip_name = next(l.split("=", 1)[1] for l in cfg.splitlines() if l.startswith("RESULT_ZIP_NAME="))
        (self.keep / zip_name).write_text("someone else's result", encoding="utf-8")
        self.assertEqual(self.run_inner(), 0, self.last)
        self.assertEqual(self.last_status()[self.keys[0]], "BLOCKED_EXISTING_RESULT")
        self.assertEqual((self.keep / zip_name).read_text(encoding="utf-8"), "someone else's result")

    def test_f_two_consecutive_training_failures_stop_24(self) -> None:
        self.behave(**{self.keys[0]: "fail_train", self.keys[1]: "fail_train"})
        self.assertEqual(self.run_inner(), 24, self.last)

    def test_g_safety_stop_error_and_incomplete_are_distinct_states(self) -> None:
        self.behave(**{self.keys[0]: "nonfinite", self.keys[2]: "incomplete", self.keys[4]: "eval_error",
                       self.keys[6]: "stationary"})
        self.assertEqual(self.run_inner(), 0, self.last)
        st = self.last_status()
        self.assertEqual(st[self.keys[0]], "SAFETY_STOP_NONFINITE")
        self.assertEqual(st[self.keys[2]], "COLLECTION_FAILED")
        self.assertEqual(st[self.keys[4]], "RUN_ERROR")
        self.assertEqual(st[self.keys[6]], "DONE")      # 정지 정책도 실행은 완료 — 제외는 판독 단계
        # 다시 치면: 안전 중단은 다시 돌리지 않고, 수집 미완은 이어 간다
        self.behave()
        self.calls.write_text("", encoding="utf-8")
        self.assertEqual(self.run_inner(), 0, self.last)
        st = self.last_status()
        self.assertEqual(st[self.keys[0]], "SKIP_SAFETY_STOPPED")
        called = {c.split()[0] for c in self.calls.read_text(encoding="utf-8").split("\n") if c}
        self.assertNotIn(self.keys[0], called)
        self.assertIn(self.keys[2], called)

    def test_h_package_checksum_mismatch_stops_25(self) -> None:
        with (self.root / "sweep_order.txt").open("a", encoding="utf-8") as fh:
            fh.write("\n")
        self.assertEqual(self.run_inner(), 25, self.last)


if __name__ == "__main__":
    unittest.main()
