"""G-A059 A043 계단 진단 재생 — 로컬 계약 테스트 (GPU 없음).

G-A056 계약 테스트의 가짜 env·가짜 회수물 도구를 그대로 빌려 쓴다.
  A 러너: bash -n·LF, 평가 명령 네 개가 G-A043 launcher.log 의 seed 101 계단 명령과 같고, 영상 명령은 거기에 영상 플래그만 더한다.
  B 패키지: 발행본을 다시 빌드하면 바이트가 같다, SHA 목록·정책·평가기·계측 모듈 바이트(G-A056 v2 와 같음).
  C 검증기: 정상 가짜 회수물 → 0, 영상 하나 없음 → 3, 필수 파일 없음 → 1.
  D 판독기: 가짜 회수물에서 돌고, G-A052 A048 실자료 판독 결과가 있다.
    python -B tools/test_go2_g_a059_diag_contract.py
"""
from __future__ import annotations

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
import build_go2_g_a059_a043_stairs_diag_package as builder  # noqa: E402
import go2_g_a059_stairs_foot_readout as readout  # noqa: E402
import test_go2_g_a056_diag_contract as t56  # noqa: E402
import verify_go2_g_a059_harvest as verifier  # noqa: E402

t56.builder = builder  # zip_harvest names the result ZIP from this module
GO2 = ROOT / "workspace/training/quadruped"
A043 = ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15"


def a043_stairs_commands() -> dict[str, str]:
    want, last = {}, None
    for line in (A043 / "launcher.log").read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("COMMAND: "):
            last = line[len("COMMAND: "):].rstrip()
        for case in builder.CASES:
            if "telemetry enabled: out=" in line and f"candidate/cases/seed_{builder.SEED}/{case} " in line:
                want.setdefault(case, last)
    return want


class A_Runner(unittest.TestCase):
    def test_1_bash_n_and_lf(self):
        p = GO2 / builder.RUNNER
        self.assertNotIn(b"\r", p.read_bytes())
        self.assertEqual(subprocess.run(["bash", "-n", str(p)]).returncode, 0)

    def test_2_commands_equal_g_a043_issued_commands(self):
        want = a043_stairs_commands()
        self.assertEqual(set(want), set(builder.CASES))
        with tempfile.TemporaryDirectory() as t:
            shutil.copy(GO2 / builder.RUNNER, t)
            Path(t, "PACKAGE_SHA256SUMS.txt").write_text("x\n")
            Path(t, "run_config.env").write_text("WORK_ID=x\nKEEP_DIR_NAME=x\nRESULT_ZIP_NAME=x\n")
            out = subprocess.run(["bash", f"{t}/{builder.RUNNER}"], capture_output=True, text=True,
                                 env={**os.environ, "GO2_DIAG_DRY_RUN": "1"}).stdout.splitlines()
        runs = [l for l in out if l.startswith("RUN ")]
        vids = [l for l in out if l.startswith("VIDEO ")]
        self.assertEqual(len(runs), 4)
        self.assertEqual(len(vids), 4)
        for l in runs:
            self.assertEqual(l.split(" COMMAND: ", 1)[1].rstrip(), want[l.split()[3]], l[:40])
        head = "/workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 32 --headless "
        for l in vids:
            _, seed, case, env_index = l.split(" COMMAND: ", 1)[0].split()
            got = l.split(" COMMAND: ", 1)[1].rstrip()
            self.assertTrue(want[case].startswith(head))
            self.assertEqual(got, head + "--video --video_length 1000 --enable_cameras " + want[case][len(head):]
                             + f" env.viewer.env_index={env_index}")
        self.assertEqual({tuple(l.split(" COMMAND: ")[0].split()[2:]) for l in vids},
                         {(c, str(e)) for c, e in builder.VIDEOS})


class B_Package(unittest.TestCase):
    def test_1_published_zip_rebuilds_identically(self):
        cur = builder.UPLOAD / "current" / builder.ZIP_NAME
        data = cur.read_bytes()
        self.assertEqual(builder.build_zip(builder.payload()), data)
        side = (cur.parent / (cur.name + ".sha256")).read_text().split()[0]
        self.assertEqual(side, builder.sha(data))

    def test_2_contents(self):
        z = zipfile.ZipFile(builder.UPLOAD / "current" / builder.ZIP_NAME)
        pre = builder.PKG + "/"
        sums = z.read(pre + "PACKAGE_SHA256SUMS.txt").decode().splitlines()
        for line in sums:
            digest, name = line.split("  ", 1)
            self.assertEqual(builder.sha(z.read(pre + name)), digest, name)
        self.assertEqual(len(sums) + 1, len(z.namelist()))
        sha = lambda n: builder.sha(z.read(pre + n))  # noqa: E731
        self.assertEqual(sha("plain/go2_eval_telemetry.py"), builder.EVALUATOR_SHA)
        self.assertEqual(sha("diag/go2_eval_telemetry_v6.py"), builder.EVALUATOR_SHA)
        self.assertEqual(sha("policy/model_best.pt"), builder.MODEL_SHA)
        self.assertEqual(sha("policy/env.yaml"), builder.ENV_SHA)
        a056 = zipfile.ZipFile(builder.G_A056_ZIP)
        for n in ("diag/go2_eval_diag_v2.py", "diag/go2_eval_telemetry.py", "video/go2_eval_camera_probe.py",
                  "video/go2_eval_telemetry.py", "plain/play.py", "plain/quadruped_rewards.py"):
            self.assertEqual(z.read(pre + n), a056.read("go2_g_a056/" + n), n)
        self.assertFalse(any(n.endswith("train.py") for n in z.namelist()))
        self.assertEqual(z.getinfo(pre + builder.RUNNER).external_attr >> 16 & 0o777, 0o755)
        exp = json.loads(z.read(pre + "experiment.json"))
        self.assertEqual(exp["runs"], [{"label": l, "case": c, "seed": 101}
                                       for c in builder.CASES for l in ("plain", "diag")])


def fake_harvest(root: Path) -> Path:
    h = root / builder.KEEP_DIR_NAME
    stored = A043 / "evaluation/candidate/cases"
    for label, seed, case in verifier.RUNS:
        d = verifier.run_dir(h, label, seed, case)
        d.mkdir(parents=True)
        shutil.copy(stored / f"seed_{seed}" / case / "steps.csv", d / "steps.csv")
        shutil.copy(stored / f"seed_{seed}" / case / "summary.json", d / "summary.json")
        (d / "STATUS.txt").write_text("EVAL_RC=0\nSTEPS=1000\nROWS=32000\n")
        (h / "logs").mkdir(parents=True, exist_ok=True)
        (h / f"logs/{label}_seed_{seed}_{case}.log").write_text("x\n")
        if label == "diag":
            t56.run_recorder(d, 1000, seed=seed)
            t56.mark_resets_stale(d)
    mp4 = root / "fake.mp4"
    t56.write_mp4(mp4, 999)
    status = []
    for case, env in verifier.VIDEOS:
        d = verifier.video_dir(h, case, env)
        d.mkdir(parents=True)
        shutil.copy(stored / f"seed_{verifier.SEED}/{case}/steps.csv", d / "steps.csv")
        (d / "STATUS.txt").write_text("EVAL_RC=0\nSTEPS=1000\nROWS=32000\n")
        shutil.copy(mp4, d / "video.mp4")
        t56.run_probe(d, 1000, env)
        (d / "video_identity.json").write_text(json.dumps({"model_sha256": builder.MODEL_SHA, "env_sha256": builder.ENV_SHA,
                                                           "case": case, "seed": verifier.SEED, "env_index": env,
                                                           "video_steps": 1000}))
        (h / f"logs/video_seed_{verifier.SEED}_{case}_env{env}.log").write_text("x\n")
        status.append(f"{case} env{env} rc=0 file=present")
    (h / "video/VIDEO_STATUS.txt").write_text("\n".join(status) + "\n")
    (h / "meta").mkdir()
    (h / "meta/identity.json").write_text(json.dumps({"model_sha256": builder.MODEL_SHA, "env_sha256": builder.ENV_SHA,
                                                      "evaluator_sha256": builder.EVALUATOR_SHA}))
    for name in ("meta/RUN_TIMES.txt", "meta/REPRO_STATUS.txt", "meta/run_config.env", "meta/experiment.json",
                 "RUNNER_STATUS.txt", "launcher.snapshot.log"):
        (h / name).write_text("x\n")
    (h / "RESULT_STATUS.txt").write_text("RESULT_STATE=PACKAGED\nCOLLECTION_STATUS=COMPLETE_4_OF_4\n")
    t56.rewrite_sums(h)
    return h


class C_VerifierAndReadout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name)
        cls.h = fake_harvest(cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run(self, mutate=None):
        t = tempfile.TemporaryDirectory()
        h2 = Path(t.name) / builder.KEEP_DIR_NAME
        shutil.copytree(self.h, h2)
        if mutate:
            mutate(h2)
            t56.rewrite_sums(h2)
        z = t56.zip_harvest(h2, Path(t.name))
        out = Path(t.name) / "o"
        code = verifier.main([str(z), "--out", str(out)])
        verdict = json.loads((out / "HARVEST_VERDICT.json").read_text(encoding="utf-8"))
        t.cleanup()
        return code, verdict

    def test_1_normal_zip_is_0_ok(self):
        code, v = self._run()
        self.assertEqual((code, v["shutdown"]), (0, "OK"), v)

    def test_2_video_missing_is_3(self):
        case, env = builder.VIDEOS[0]
        code, v = self._run(lambda h: (verifier.video_dir(h, case, env) / "video.mp4").unlink())
        self.assertEqual((code, v["shutdown"]), (3, "EXCEPTION_DECISION_REQUIRED"), v)

    def test_3_required_file_missing_is_1(self):
        code, v = self._run(lambda h: (verifier.run_dir(h, "diag", 101, "stairs_15_down") / "diag.csv.gz").unlink())
        self.assertEqual((code, v["shutdown"]), (1, "DO_NOT_SHUTDOWN"), v)

    def test_4_readout_runs_on_fake_harvest(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(readout.main([str(self.h), "--out", t]), 0)
            with open(Path(t) / "PER_ENV.csv", encoding="utf-8") as fh:
                rows = list(__import__("csv").DictReader(fh))
            self.assertEqual(len(rows), 64)
            self.assertEqual({r["case"] for r in rows}, set(builder.CASES))

    def test_5_readout_on_real_a052_a048_exists(self):
        p = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a059_readout_on_a052_a048/GROUP_SUMMARY.csv"
        with open(p, encoding="utf-8") as fh:
            rows = list(__import__("csv").DictReader(fh))
        self.assertEqual(sum(int(r["robots"]) for r in rows), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
