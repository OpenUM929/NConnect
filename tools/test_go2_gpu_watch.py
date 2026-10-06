"""go2_gpu_watch.sh 계약 테스트 — 가짜 nvidia-smi 와 가짜 학습 로그로 경보를 확인한다.

실행: PATH="C:/Program Files/Git/bin:$PATH" python -B -m unittest tools.test_go2_gpu_watch
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "go2_gpu_watch.sh"
BASH = shutil.which("bash") or "bash"

FAKE_SMI = """#!/usr/bin/env bash
case "$*" in
  *query-gpu*) cat "$FAKE_DIR/gpu.csv" ;;
  *query-compute-apps*) [[ -n "${FAKE_APPS_RC:-}" ]] && exit "$FAKE_APPS_RC"; cat "$FAKE_DIR/apps.csv" ;;
  *) exit 1 ;;
esac
"""


def training_log(times: list[float], total: int = 1000) -> str:
    out = []
    for i, t in enumerate(times):
        out.append(f"\x1b[1m                           Learning iteration {i}/{total}                            \x1b[0m ")
        out.append(f"                         Iteration time: {t:.2f}s")
        out.append(f"                                    ETA: 01:{i % 60:02d}:00")
    return "\n".join(out) + "\n"


class GpuWatch(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.keep = self.tmp / "keep"
        self.fake = self.tmp / "fake"
        self.fake.mkdir()
        (self.keep / "go2_g_a060_pc2_a048_seed42" / "logs").mkdir(parents=True)
        smi = self.fake / "nvidia-smi"
        smi.write_text(FAKE_SMI, encoding="utf-8", newline="\n")
        self.smi = smi
        self.set_gpu("40, 6000, 12227, 61, 150.2")
        self.set_apps("4321, C:\\isaac\\kit\\python.exe, 5800")
        self.write_log([2.0] * 40)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_gpu(self, line: str) -> None:
        (self.fake / "gpu.csv").write_text(line + "\n", encoding="utf-8", newline="\n")

    def set_apps(self, text: str) -> None:
        (self.fake / "apps.csv").write_text(text + ("\n" if text else ""), encoding="utf-8", newline="\n")

    def write_log(self, times: list[float]) -> Path:
        p = self.keep / "go2_g_a060_pc2_a048_seed42" / "logs" / "candidate_training.log"
        p.write_text(training_log(times), encoding="utf-8", newline="\n")
        return p

    def run_once(self, *extra: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
        env = dict(os.environ, NVSMI=self.smi.as_posix(), FAKE_DIR=self.fake.as_posix())
        env.update(env_extra or {})
        return subprocess.run([BASH, SCRIPT.as_posix(), "--once", "--keep", self.keep.as_posix(), *extra],
                              capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)

    def last_row(self) -> dict:
        lines = (self.keep / "go2_gpu_watch" / "WATCH.tsv").read_text(encoding="utf-8").splitlines()
        return dict(zip(lines[0].split("\t"), lines[-1].split("\t")))

    def alerts(self) -> str:
        p = self.keep / "go2_gpu_watch" / "ALERTS.txt"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def test_1_normal_training_has_no_alert(self) -> None:
        r = self.run_once()
        self.assertEqual(r.returncode, 0, r.stderr)
        row = self.last_row()
        self.assertEqual(row["alerts"], "-")
        self.assertEqual((row["point"], row["iter"], row["iter_total"]), ("go2_g_a060_pc2_a048_seed42", "39", "1000"))
        self.assertEqual((row["iter_s_recent"], row["iter_s_base"]), ("2.00", "2.00"))
        self.assertEqual(self.alerts(), "")

    def test_2_foreign_gpu_process_is_flagged_not_killed(self) -> None:
        self.set_apps("4321, C:\\isaac\\kit\\python.exe, 5800\n9999, C:\\Users\\x\\AppData\\xmrig.exe, 3000")
        r = self.run_once()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("FOREIGN_GPU_PROCESS pid=9999 name=xmrig.exe vram_mb=3000", self.alerts())
        procs = (self.keep / "go2_gpu_watch" / "GPU_PROCS.txt").read_text(encoding="utf-8")
        self.assertIn("FOREIGN\t9999", procs)
        self.assertIn("OK\t4321", procs)
        self.assertEqual(self.last_row()["foreign"], "1")

    def test_3_slowdown_against_own_start_and_given_base(self) -> None:
        self.write_log([2.0] * 30 + [3.0] * 10)  # 처음 2.0초 → 최근 3.0초 (1.5배)
        self.run_once()
        self.assertIn("SLOWDOWN point=go2_g_a060_pc2_a048_seed42 iter_s=3.00 base=2.00", self.alerts())
        shutil.rmtree(self.keep / "go2_gpu_watch")
        self.write_log([3.0] * 40)  # 처음부터 느렸다면 자기 기준으로는 못 잡는다 → 정상 기준값을 주면 잡는다
        self.run_once()
        self.assertNotIn("SLOWDOWN", self.alerts())
        self.run_once("--base-iter-s", "2.0")
        self.assertIn("SLOWDOWN", self.alerts())

    def test_4_busy_gpu_without_training_process(self) -> None:
        self.set_gpu("55, 3000, 12227, 70, 180.0")
        self.set_apps("")
        self.run_once()
        self.assertIn("GPU_BUSY_NO_TRAINING util=55%", self.alerts())

    def test_5_vram_high_and_stall(self) -> None:
        self.set_gpu("90, 11800, 12227, 75, 200.0")
        log = self.write_log([2.0] * 40)
        old = time.time() - 30 * 60
        os.utime(log, (old, old))
        self.run_once()
        a = self.alerts()
        self.assertIn("VRAM_HIGH 11800/12227MB", a)
        self.assertIn("STALL no log update 30min", a)

    def test_6_alert_written_once_then_cleared(self) -> None:
        self.set_apps("4321, python.exe, 5800\n9999, miner.exe, 3000")
        self.run_once(); self.run_once()
        self.assertEqual(self.alerts().count("ALERT"), 1)
        self.set_apps("4321, python.exe, 5800")
        self.run_once()
        self.assertIn("CLEARED", self.alerts())

    def test_7_smi_failure_and_bad_args(self) -> None:
        self.run_once(env_extra={"NVSMI": (self.fake / "missing").as_posix()})
        self.assertIn("NVIDIA_SMI_FAILED", self.alerts())
        r = subprocess.run([BASH, SCRIPT.as_posix(), "--hours", "x", "--keep", self.keep.as_posix()],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 64)
        r = subprocess.run([BASH, "-n", SCRIPT.as_posix()], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(b"\r", SCRIPT.read_bytes())


    # --- §27 Codex 재현 결함 회귀 ---
    def test_8_process_query_failure_is_not_an_empty_list(self) -> None:
        self.set_gpu("10, 1000, 12227, 61, 100")
        r = self.run_once(env_extra={"FAKE_APPS_RC": "9"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("NVIDIA_SMI_FAILED query-compute-apps", self.alerts())
        self.assertNotEqual(self.last_row()["alerts"], "-")
        self.set_gpu("55, 3000, 12227, 70, 180.0")  # 조회 실패를 '학습 프로세스 없음'으로 오판하지 않는다
        shutil.rmtree(self.keep / "go2_gpu_watch")
        self.run_once(env_extra={"FAKE_APPS_RC": "9"})
        self.assertNotIn("GPU_BUSY_NO_TRAINING", self.alerts())

    def test_9_second_gpu_is_reported_as_unsupported(self) -> None:
        self.set_gpu("10, 1000, 12227, 61, 100\n99, 12000, 12227, 80, 200")
        self.set_apps("")
        self.run_once()
        self.assertIn("MULTI_GPU_UNSUPPORTED gpus=2", self.alerts())
        self.assertNotEqual(self.last_row()["alerts"], "-")

    def test_10_option_without_value_exits_64_quickly(self) -> None:
        for opt in ("--hours", "--interval", "--keep", "--pattern", "--out", "--allow", "--base-iter-s"):
            r = subprocess.run([BASH, SCRIPT.as_posix(), opt], capture_output=True, text=True, timeout=15)
            self.assertEqual(r.returncode, 64, opt)
            self.assertIn("needs a value", r.stderr, opt)

    def test_11_points_dir_follows_pattern(self) -> None:
        """G-A061 N3 실측: 기본 패턴(G-A060)으로 떠서 지난 회차 상태를 STALL로 보고했다. 상태 폴더는 --pattern 을 따른다."""
        log = self.write_log([2.0] * 40)
        old = time.time() - 30 * 60
        os.utime(log, (old, old))
        a060 = self.keep / "go2_g_a060_pc2_points"
        a060.mkdir()
        (a060 / "POINT_STATUS.tsv").write_text("key\tstatus\nold_point\tDONE\n", encoding="utf-8", newline="\n")
        pts = self.keep / "go2_g_a061_pc2_points"
        pts.mkdir()
        (pts / "POINT_STATUS.tsv").write_text("key\tstatus\nn3_x\tRUNNING\n", encoding="utf-8", newline="\n")
        run = self.keep / "go2_g_a061_pc2_n3_x" / "logs"
        run.mkdir(parents=True)
        p = run / "candidate_training.log"
        p.write_text(training_log([2.0] * 40), encoding="utf-8", newline="\n")
        os.utime(p, (old, old))
        self.run_once("--pattern", "go2_g_a061_pc2_*")
        a = self.alerts()
        self.assertIn("last status n3_x:RUNNING", a)
        self.assertNotIn("old_point", a)


if __name__ == "__main__":
    unittest.main()
