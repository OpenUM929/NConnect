"""관문: G-A052 진단 재생 (계측 모듈 · 래퍼 · 러너 · 패키지 · 가짜 회수물로 판독기 실행).

    python -B -m unittest tools/test_go2_g_a052_diag_contract.py
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))
import build_go2_diag_replay_package as builder  # noqa: E402
import go2_diag_replay_readout as readout  # noqa: E402
import go2_eval_diag as diagmod  # noqa: E402
import verify_go2_diag_replay_harvest as verifier  # noqa: E402

A048 = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125"
FEET = ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]


class _NoLazy:
    """센서 .data 를 읽으면 실패한다 — lazy update 를 부르지 않는다는 계약."""

    def __get__(self, obj, owner):
        raise AssertionError("contact sensor .data accessed (would trigger a lazy update)")


class FakeSensor:
    data = _NoLazy()

    def __init__(self, n, g):
        self.cfg = types.SimpleNamespace(update_period=0.005, history_length=3, force_threshold=1.0, track_air_time=True)
        self.n, self.g = n, g
        self._data = types.SimpleNamespace()
        self._timestamp = torch.full((n,), 1.0)
        self._timestamp_last_update = torch.full((n,), 1.0)
        self._is_outdated = torch.zeros(n, dtype=torch.bool)
        self.refresh()

    def refresh(self):
        n, g = self.n, self.g
        self._data.net_forces_w = torch.randn(n, 5, 3, generator=g) * 50
        self._data.net_forces_w_history = torch.randn(n, 3, 5, 3, generator=g) * 50
        self._data.current_contact_time = (torch.rand(n, 5, generator=g) - 0.4).clamp(min=0) * 0.3
        self._data.current_air_time = (torch.rand(n, 5, generator=g) - 0.5).clamp(min=0) * 0.3
        self._data.last_air_time = torch.rand(n, 5, generator=g) * 0.4

    def find_bodies(self, keys, preserve_order=False):
        names = ["base"] + FEET
        keys = [keys] if isinstance(keys, str) else list(keys)
        if keys == ["base"]:
            return [0], ["base"]
        if keys == [".*_foot"] or keys == FEET:
            return [1, 2, 3, 4], FEET
        raise ValueError(keys)


class FakeEnv:
    def __init__(self, n=32, seed=0, break_group=None):
        g = torch.Generator().manual_seed(seed)
        self.g, self.num_envs, self.step_dt = g, n, 0.02
        robot = types.SimpleNamespace(data=types.SimpleNamespace())
        robot.find_bodies = lambda pat, preserve_order=False: ([1, 2, 3, 4], FEET)
        self.robot = robot
        self.sensor = FakeSensor(n, g)
        self.scanner = types.SimpleNamespace(data=types.SimpleNamespace())
        self.scene = {"robot": robot, "contact_forces": self.sensor, "height_scanner": self.scanner}
        terms = ["track_lin_vel_xy_exp", "ang_vel_xy_l2", "feet_air_time"]
        self.reward_manager = types.SimpleNamespace(
            active_terms=terms, get_term_cfg=lambda name: types.SimpleNamespace(weight={"track_lin_vel_xy_exp": 1.5,
                                                                                         "ang_vel_xy_l2": -0.05,
                                                                                         "feet_air_time": 0.2}[name]))
        self.action_manager = types.SimpleNamespace()
        self.break_group = break_group
        self.advance()

    @property
    def unwrapped(self):
        return self

    def advance(self):
        n, g, d = self.num_envs, self.g, self.robot.data
        d.root_lin_vel_b = torch.randn(n, 3, generator=g) * 0.2
        d.root_ang_vel_b = torch.randn(n, 3, generator=g) * 0.3
        d.projected_gravity_b = torch.tensor([0.0, 0.0, -1.0]).repeat(n, 1) + torch.randn(n, 3, generator=g) * 0.02
        d.root_quat_w = torch.tensor([1.0, 0, 0, 0]).repeat(n, 1)
        d.root_pos_w = torch.randn(n, 3, generator=g) + torch.tensor([0, 0, 0.3])
        d.body_pos_w = (torch.randn(n, 5, 3, generator=g) * 0.2).clamp(-0.4, 0.4)
        d.body_lin_vel_w = torch.randn(n, 5, 3, generator=g) * 0.1
        if self.break_group == "feet":
            del d.body_lin_vel_w
        # Go2 height_scanner 처럼 몸통 주변 1.6 x 1.0 m 를 0.1 m 격자(17 x 11 = 187 광선)로 덮는다
        xs, ys = torch.meshgrid(torch.linspace(-0.8, 0.8, 17), torch.linspace(-0.5, 0.5, 11), indexing="ij")
        grid = torch.stack([xs.reshape(-1), ys.reshape(-1)], dim=1).expand(n, -1, -1)
        self.scanner.data.ray_hits_w = torch.cat([grid, torch.randn(n, 187, 1, generator=g) * 0.05], dim=2)
        self.sensor.refresh()
        self.reward_manager._step_reward = torch.randn(n, 3, generator=g)
        self.action_manager.action = torch.randn(n, 12, generator=g)
        self.action_manager.prev_action = torch.randn(n, 12, generator=g)


def run_recorder(out: Path, steps: int, seed=0, break_group=None, n=32) -> FakeEnv:
    env = FakeEnv(n=n, seed=seed, break_group=break_group)
    rec = diagmod.DiagRecorder(out, steps)
    for _ in range(steps):
        before = {k: v.clone() for k, v in vars(env.robot.data).items()}
        rec.record(env)
        after = vars(env.robot.data)
        assert all(torch.equal(before[k], after[k]) for k in before), "recorder modified robot data"
        env.advance()
    return env


def read_gz(p: Path) -> list[dict]:
    with gzip.open(p, "rt", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class A_Recorder(unittest.TestCase):
    def test_1_columns_rows_and_status(self):
        with tempfile.TemporaryDirectory() as t:
            run_recorder(Path(t), 5)
            rows = read_gz(Path(t) / "diag.csv.gz")
            self.assertEqual(len(rows), 5 * 32)
            meta = json.loads((Path(t) / "diag_meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["unavailable"], {})
            self.assertEqual(meta["reward_weights"]["ang_vel_xy_l2"], -0.05)
            self.assertIn("post-reset", meta["timing_note"])
            self.assertEqual((Path(t) / "DIAG_STATUS.txt").read_text().splitlines()[0], "DIAG_STATUS=DIAG_COMPLETE")
            for col in ("ang_vel_b_x", "FL_contact_time", "RR_first_contact", "FL_terrain_zmax015_derived",
                        "action_11", "prev_action_0", "rew_feet_air_time", "base_force_hist_max",
                        "contact_fresh", "contact_age_s"):
                self.assertIn(col, rows[0])
            self.assertTrue(all(v != "" for v in rows[0].values()))

    def test_2_first_contact_matches_sensor_definition(self):
        with tempfile.TemporaryDirectory() as t:
            env = FakeEnv(seed=3)
            ct = env.sensor._data.current_contact_time[:, 1].clone()
            rec = diagmod.DiagRecorder(Path(t), 1)
            rec.record(env)
            rows = read_gz(Path(t) / "diag.csv.gz")
            want = ((ct > 0) & (ct < 0.02 + 1e-8)).float().tolist()
            self.assertEqual([float(r["FL_first_contact"]) for r in rows], want)

    def test_2b_contact_freshness_is_recorded_per_env(self):
        with tempfile.TemporaryDirectory() as t:
            env = FakeEnv(seed=4)
            env.sensor._is_outdated[3] = True           # 이 step 에 reset 된 env 처럼
            env.sensor._timestamp_last_update[5] = 0.98  # 갱신이 한 번 밀린 env
            rec = diagmod.DiagRecorder(Path(t), 1)
            rec.record(env)
            rows = read_gz(Path(t) / "diag.csv.gz")
            fresh = [float(r["contact_fresh"]) for r in rows]
            self.assertEqual(fresh[3], 0.0)
            self.assertEqual(fresh[5], 0.0)
            self.assertEqual(sum(fresh), 30.0)
            self.assertAlmostEqual(float(rows[5]["contact_age_s"]), 0.02, places=5)

    def test_3_broken_group_is_recorded_not_guessed(self):
        with tempfile.TemporaryDirectory() as t:
            run_recorder(Path(t), 3, break_group="feet")
            meta = json.loads((Path(t) / "diag_meta.json").read_text(encoding="utf-8"))
            self.assertIn("feet", meta["unavailable"])
            rows = read_gz(Path(t) / "diag.csv.gz")
            self.assertEqual(rows[0]["FL_vel_x"], "")
            self.assertNotEqual(rows[0]["ang_vel_b_x"], "")
            self.assertIn("DIAG_PARTIAL", (Path(t) / "DIAG_STATUS.txt").read_text())

    def test_4_wrapper_runs_evaluator_first_and_passes_result_through(self):
        calls = []
        fake_gym = types.ModuleType("gymnasium")

        class Env:
            def step(self, action):
                calls.append(("raw", action))
                return ("obs", action)
        fake_gym.make = lambda *a, **k: Env()
        base = types.ModuleType("go2_eval_telemetry_v6")

        def base_install():
            inner = fake_gym.make

            def make(*a, **k):
                env = inner(*a, **k)
                raw = env.step

                def measured(action):
                    r = raw(action)
                    calls.append(("evaluator", action))
                    return r
                env.step = measured
                return env
            fake_gym.make = make
        base.install = base_install
        saved = {k: sys.modules.get(k) for k in ("gymnasium", "go2_eval_telemetry_v6", "go2_eval_telemetry_diag_wrapper")}
        sys.modules["gymnasium"], sys.modules["go2_eval_telemetry_v6"] = fake_gym, base
        sys.modules.pop("go2_eval_telemetry_diag_wrapper", None)
        try:
            with tempfile.TemporaryDirectory() as t:
                os.environ["NCRC_EVAL_OUT"], os.environ["NCRC_EVAL_STEPS"] = t, "10"
                import go2_eval_telemetry_diag_wrapper as w
                w.DiagRecorder = lambda out, steps: types.SimpleNamespace(record=lambda env: calls.append(("diag", None)))
                w.install()
                env = fake_gym.make("Quadruped-v0")
                self.assertEqual(env.step(7), ("obs", 7))
                self.assertEqual(calls, [("raw", 7), ("evaluator", 7), ("diag", None)])
        finally:
            os.environ.pop("NCRC_EVAL_OUT", None)
            os.environ.pop("NCRC_EVAL_STEPS", None)
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v


def _rows_with(omega: float, contact: bool, n: int = 60) -> list[dict]:
    row = {"ang_vel_b_x": omega, "ang_vel_b_y": 0.0, "contact_fresh": 1.0 if contact else None}
    for f in ("FL", "FR", "RL", "RR"):
        row.update({f"{f}_contact_time": 0.1 if contact else None, f"{f}_vel_x": 0.0 if contact else None,
                    f"{f}_vel_y": 0.0 if contact else None})
    return [dict(row) for _ in range(n)]


class A2_ReadoutMissingIsNotZero(unittest.TestCase):
    """Codex 재현 입력(2026-09-28): 발 접촉 전부 결측 + 회전 있음."""
    FEET = ["FL", "FR", "RL", "RR"]

    def test_1_missing_contact_with_rotation_is_unknown_not_rotation_only(self):
        cal = {"R_omega_xy_p95": 0.5, "S_stance_speed_p95": None, "D_low_support_run_p95_s": None}
        out = readout.window_readout(_rows_with(2.0, contact=False), 0, 50, self.FEET, cal)
        self.assertEqual(out["order"], "unknown")
        self.assertIsNone(out["mean_support"])
        self.assertEqual((out["rotation_valid"], out["contact_valid"]), (1, 0))
        self.assertIsNotNone(out["t_rot"])          # 관측한 회전은 버리지 않는다

    def test_2_missing_contact_with_support_calibration_is_unknown_not_simultaneous(self):
        cal = {"R_omega_xy_p95": 0.5, "S_stance_speed_p95": 0.2, "D_low_support_run_p95_s": 0.04}
        out = readout.window_readout(_rows_with(2.0, contact=False), 0, 50, self.FEET, cal)
        self.assertEqual(out["order"], "unknown")
        self.assertIsNone(out["mean_support"])
        self.assertEqual(out["FL_contact_bins"], "??????????")

    def test_3_stale_buffer_is_unknown(self):
        cal = {"R_omega_xy_p95": 0.5, "S_stance_speed_p95": 0.2, "D_low_support_run_p95_s": 0.04}
        rows = _rows_with(2.0, contact=True)
        rows[10]["contact_fresh"] = 0.0
        out = readout.window_readout(rows, 0, 50, self.FEET, cal)
        self.assertEqual((out["order"], out["contact_invalid_reason"]), ("unknown", "contact_stale"))

    def test_4_valid_channels_still_order(self):
        cal = {"R_omega_xy_p95": 0.5, "S_stance_speed_p95": 0.2, "D_low_support_run_p95_s": 0.04}
        out = readout.window_readout(_rows_with(2.0, contact=True), 0, 50, self.FEET, cal)
        self.assertEqual(out["order"], "rotation_only")
        self.assertEqual(out["mean_support"], 4.0)

    def test_5_calibration_skips_missing_rows(self):
        diag = {0: _rows_with(0.1, contact=False, n=100)}
        cal = readout.calibrate(diag, {0: 100}, [0], self.FEET)
        self.assertEqual((cal["rows_contact_valid"], cal["low_support_runs"]), (0, 0))
        self.assertIsNone(cal["D_low_support_run_p95_s"])


class B_Runner(unittest.TestCase):
    def test_1_bash_n_and_lf(self):
        p = GO2 / "server_run_go2_diag_replay.sh"
        self.assertNotIn(b"\r", p.read_bytes())
        self.assertEqual(subprocess.run(["bash", "-n", str(p)]).returncode, 0)

    def test_2_commands_equal_g_a048_issued_commands(self):
        log = (A048 / "launcher.log").read_text(encoding="utf-8", errors="replace").splitlines()
        want = {}
        last = None
        for line in log:
            if line.startswith("COMMAND: "):
                last = line[len("COMMAND: "):].rstrip()
            for key in ("seed_202/rough_lateral ", "seed_101/stairs_10_down ", "seed_101/stairs_15_down "):
                if "telemetry enabled: out=" in line and f"candidate/cases/{key}" in line:
                    want.setdefault(key.strip(), last)
        with tempfile.TemporaryDirectory() as t:
            shutil.copy(GO2 / "server_run_go2_diag_replay.sh", t)
            Path(t, "PACKAGE_SHA256SUMS.txt").write_text("x\n")
            Path(t, "run_config.env").write_text("WORK_ID=x\nKEEP_DIR_NAME=x\nRESULT_ZIP_NAME=x\n")
            out = subprocess.run(["bash", f"{t}/server_run_go2_diag_replay.sh"], capture_output=True, text=True,
                                 env={**os.environ, "GO2_DIAG_DRY_RUN": "1"}).stdout.splitlines()
        got = {f"seed_{l.split()[2]}/{l.split()[3]}" + ("#plain" if l.split()[1] == "plain" else ""):
               l.split(" COMMAND: ", 1)[1].rstrip() for l in out if l.startswith("RUN ")}
        self.assertEqual(len(got), 4)
        self.assertEqual(got["seed_202/rough_lateral#plain"], want["seed_202/rough_lateral"])
        self.assertEqual(got["seed_202/rough_lateral"], want["seed_202/rough_lateral"])
        self.assertEqual(got["seed_101/stairs_10_down"], want["seed_101/stairs_10_down"])
        self.assertEqual(got["seed_101/stairs_15_down"], want["seed_101/stairs_15_down"])


class C_Package(unittest.TestCase):
    def test_1_published_zip_rebuilds_identically(self):
        cur = builder.UPLOAD / "current" / builder.ZIP_NAME
        data = cur.read_bytes()
        self.assertEqual(builder.build_zip(builder.payload()), data)
        side = (cur.parent / (cur.name + ".sha256")).read_text().split()[0]
        self.assertEqual(side, hashlib.sha256(data).hexdigest())

    def test_2_contents(self):
        z = zipfile.ZipFile(builder.UPLOAD / "current" / builder.ZIP_NAME)
        names = set(z.namelist())
        pre = builder.PKG + "/"
        sums = z.read(pre + "PACKAGE_SHA256SUMS.txt").decode().splitlines()
        for line in sums:
            digest, name = line.split("  ", 1)
            self.assertEqual(hashlib.sha256(z.read(pre + name)).hexdigest(), digest, name)
        self.assertEqual(len(sums) + 1, len(names))
        src = A048 / "evaluation/candidate/source"
        for p in src.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                rel = p.relative_to(src).as_posix()
                self.assertEqual(z.read(pre + "plain/" + rel), p.read_bytes(), rel)
        sha = lambda n: hashlib.sha256(z.read(pre + n)).hexdigest()  # noqa: E731
        self.assertEqual(sha("plain/go2_eval_telemetry.py"), builder.EVALUATOR_SHA)
        self.assertEqual(sha("diag/go2_eval_telemetry_v6.py"), builder.EVALUATOR_SHA)
        self.assertEqual(sha("policy/model_best.pt"), builder.MODEL_SHA)
        self.assertEqual(sha("policy/env.yaml"), builder.ENV_SHA)
        self.assertEqual(z.read(pre + "diag/play.py"), z.read(pre + "plain/play.py"))
        self.assertFalse(any(n.endswith("train.py") for n in names))
        self.assertEqual(z.getinfo(pre + "server_run_go2_diag_replay.sh").external_attr >> 16 & 0o777, 0o755)
        for n in ("server_run_go2_diag_replay.sh", "run_config.env", "diag/go2_eval_diag.py", "diag/go2_eval_telemetry.py"):
            self.assertNotIn(b"\r", z.read(pre + n), n)
        rewards = z.read(pre + "plain/quadruped_rewards.py")
        self.assertEqual(rewards, (A048 / "training/source/quadruped_rewards.py").read_bytes())


def mark_resets_stale(d: Path) -> None:
    """실물처럼, 그 step 에 reset 된 env 의 행은 contact_fresh = 0 으로 둔다."""
    with (d / "steps.csv").open(encoding="utf-8", newline="") as fh:
        resets = {(r["step"], r["env_id"]) for r in csv.DictReader(fh) if r["terminated"] == "1" or r["truncated"] == "1"}
    rows = read_gz(d / "diag.csv.gz")
    for r in rows:
        if (r["step"], r["env_id"]) in resets:
            r["contact_fresh"] = "0"
    with gzip.open(d / "diag.csv.gz", "wt", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def rewrite_sums(h: Path) -> None:
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  ./{p.relative_to(h).as_posix()}"
             for p in sorted(h.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.txt"]
    (h / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def fake_harvest(root: Path) -> Path:
    """저장된 A048 steps.csv 로 plain·diag 궤적을, 가짜 env 로 diag 채널을 만든 회수물."""
    h = root / builder.KEEP_DIR_NAME
    stored = A048 / "evaluation/candidate/cases"
    for label, seed, case in verifier.RUNS:
        d = h / label / "cases" / f"seed_{seed}" / case
        d.mkdir(parents=True)
        shutil.copy(stored / f"seed_{seed}" / case / "steps.csv", d / "steps.csv")
        shutil.copy(stored / f"seed_{seed}" / case / "summary.json", d / "summary.json")
        (d / "STATUS.txt").write_text("EVAL_RC=0\nSTEPS=1000\nROWS=32000\n")
        if label == "diag":
            run_recorder(d, 1000, seed=seed)
            mark_resets_stale(d)
    (h / "meta").mkdir()
    (h / "logs").mkdir()
    (h / "meta/identity.json").write_text(json.dumps({"model_sha256": builder.MODEL_SHA, "env_sha256": builder.ENV_SHA,
                                                      "evaluator_sha256": builder.EVALUATOR_SHA}))
    for name in ("meta/RUN_TIMES.txt", "meta/REPRO_STATUS.txt", "meta/run_config.env", "meta/experiment.json",
                 "RUNNER_STATUS.txt", "launcher.snapshot.log"):
        (h / name).write_text("x\n")
    for label, seed, case in verifier.RUNS:
        (h / f"logs/{label}_seed_{seed}_{case}.log").write_text("x\n")
    (h / "RESULT_STATUS.txt").write_text("RESULT_STATE=PACKAGED\nCOLLECTION_STATUS=COMPLETE_4_OF_4\n")
    lines = []
    for p in sorted(h.rglob("*")):
        if p.is_file():
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  ./{p.relative_to(h).as_posix()}")
    (h / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    return h


class D_ReadersOnFakeHarvest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.h = fake_harvest(Path(cls.tmp.name))
        cls.out = Path(cls.tmp.name) / "out"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_1_verifier_accepts_and_reports_repro(self):
        self.assertEqual(verifier.main([str(self.h), "--out", str(self.out)]), 0)
        v = json.loads((self.out / "HARVEST_VERDICT.json").read_text())
        self.assertEqual((v["artifact"], v["channels"]), ("ARTIFACT_VERIFIED", "DIAG_CHANNELS_COMPLETE"))
        self.assertEqual(v["repro"]["plain_vs_stored"], "NO_DIFFERENCE_IN_STORED_CHANNELS")
        self.assertIn("not a proof", v["repro_meaning"])

    def _variant(self, mutate):
        t = tempfile.TemporaryDirectory()
        h2 = Path(t.name) / "h"
        shutil.copytree(self.h, h2)
        mutate(h2)
        code = verifier.main([str(h2), "--out", str(Path(t.name) / "o")])
        v = json.loads((Path(t.name) / "o/HARVEST_VERDICT.json").read_text())
        t.cleanup()
        return code, v

    def test_2b_required_file_missing_from_sums_fails(self):
        def m(h):
            lines = [l for l in (h / "SHA256SUMS.txt").read_text().splitlines() if "RUN_TIMES" not in l]
            (h / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
        code, v = self._variant(m)
        self.assertEqual(code, 1)
        self.assertIn("required file not in SHA256SUMS: meta/RUN_TIMES.txt", v["problems"])

    def test_2c_required_file_absent_fails(self):
        def m(h):
            (h / "diag/cases/seed_101/stairs_10_down/steps.csv").unlink()
            rewrite_sums(h)
        code, v = self._variant(m)
        self.assertEqual(code, 1)
        self.assertTrue(any("repro input missing" in p for p in v["problems"]))

    def test_2d_duplicate_diag_key_fails(self):
        def m(h):
            p = h / "diag/cases/seed_101/stairs_15_down/diag.csv.gz"
            rows = read_gz(p)
            rows[1]["env_id"] = rows[0]["env_id"]
            with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
            rewrite_sums(h)
        code, v = self._variant(m)
        self.assertEqual(code, 1)
        self.assertTrue(any("duplicate=1 missing=1" in p for p in v["problems"]))

    def _edit_rows(self, case_rel, fn):
        def m(h):
            p = h / case_rel / "diag.csv.gz"
            rows = read_gz(p)
            fn(rows, h / case_rel)
            with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
            rewrite_sums(h)
        return self._variant(m)

    @staticmethod
    def _resets(d):
        with (d / "steps.csv").open(encoding="utf-8", newline="") as fh:
            return {(r["step"], r["env_id"]) for r in csv.DictReader(fh) if r["terminated"] == "1" or r["truncated"] == "1"}

    def test_2f_rear_right_contact_missing_everywhere_is_exit_3(self):
        """Codex 재현(2026-09-28): RR_contact_time 전체 결측이 artifact·channel 모두 통과하던 결함."""
        def fn(rows, d):
            for r in rows:
                r["RR_contact_time"] = ""
        code, v = self._edit_rows("diag/cases/seed_202/rough_lateral", fn)
        self.assertEqual((code, v["artifact"], v["channels"]), (3, "ARTIFACT_VERIFIED", "DIAG_CHANNELS_INCOMPLETE"))
        self.assertTrue(any("RR_contact_time missing or non-finite in" in c for c in v["channel_problems"]))

    def test_2g_single_non_reset_row_missing_is_exit_3_with_location(self):
        def fn(rows, d):
            resets = self._resets(d)
            r = next(r for r in rows if (r["step"], r["env_id"]) not in resets and r["step"] == "500")
            r["RL_vel_y"] = ""
            fn.loc = f"step={r['step']} env={r['env_id']}"
        code, v = self._edit_rows("diag/cases/seed_101/stairs_10_down", fn)
        self.assertEqual(code, 3)
        hit = [c for c in v["channel_problems"] if "RL_vel_y" in c]
        self.assertEqual(len(hit), 1)
        self.assertIn("in 1/", hit[0])
        self.assertIn(fn.loc, hit[0])

    def test_2h_non_finite_values_are_exit_3(self):
        def fn(rows, d):
            resets = self._resets(d)
            good = [r for r in rows if (r["step"], r["env_id"]) not in resets]
            good[10]["ang_vel_b_y"] = "inf"
            good[20]["FR_pos_z"] = "nan"
            good[30]["action_7"] = "-Infinity"
        code, v = self._edit_rows("diag/cases/seed_101/stairs_15_down", fn)
        self.assertEqual(code, 3)
        for col in ("ang_vel_b_y", "FR_pos_z", "action_7"):
            self.assertTrue(any(f"{col} missing or non-finite in 1/" in c for c in v["channel_problems"]), col)

    def test_2j_one_registered_reward_column_dropped_is_exit_3(self):
        """Codex 재현(2026-09-28): 등록된 보상 항 열 하나만 빠지면 통과하던 공백."""
        def fn(rows, d):
            for r in rows:
                del r["rew_ang_vel_xy_l2"]
        code, v = self._edit_rows("diag/cases/seed_202/rough_lateral", fn)
        self.assertEqual((code, v["artifact"], v["channels"]), (3, "ARTIFACT_VERIFIED", "DIAG_CHANNELS_INCOMPLETE"))
        self.assertIn("rough_lateral: reward column rew_ang_vel_xy_l2 absent (registered in diag_meta reward_weights)",
                      v["channel_problems"])

    def test_2i_blank_in_reset_row_is_allowed(self):
        def fn(rows, d):
            resets = self._resets(d)
            for r in rows:
                if (r["step"], r["env_id"]) in resets:
                    r["FL_contact_time"] = ""
        code, v = self._edit_rows("diag/cases/seed_202/rough_lateral", fn)
        self.assertEqual((code, v["channels"]), (0, "DIAG_CHANNELS_COMPLETE"))

    def test_2e_unavailable_or_stale_contact_is_exit_3_not_0(self):
        def m(h):
            p = h / "diag/cases/seed_202/rough_lateral/diag_meta.json"
            meta = json.loads(p.read_text())
            meta["unavailable"]["contact"] = "AttributeError: _is_outdated"
            p.write_text(json.dumps(meta))
            rewrite_sums(h)
        code, v = self._variant(m)
        self.assertEqual((code, v["artifact"], v["channels"]), (3, "ARTIFACT_VERIFIED", "DIAG_CHANNELS_INCOMPLETE"))

        def s(h):
            p = h / "diag/cases/seed_101/stairs_10_down/diag.csv.gz"
            rows = read_gz(p)
            rows[100]["contact_fresh"] = "0"
            with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
            rewrite_sums(h)
        code, v = self._variant(s)
        self.assertEqual(code, 3)
        self.assertTrue(any("contact_fresh" in c for c in v["channel_problems"]))

    def test_2_verifier_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as t:
            h2 = Path(t) / "h"
            shutil.copytree(self.h, h2)
            p = h2 / "meta/identity.json"
            p.write_text(p.read_text().replace(builder.MODEL_SHA, "0" * 64))
            self.assertEqual(verifier.main([str(h2), "--out", str(Path(t) / "o")]), 1)

    def test_3_readout_runs_and_uses_only_the_preregistered_orders(self):
        self.assertEqual(readout.main([str(self.h), "--out", str(self.out)]), 0)
        with (self.out / "EVENTS_DIAG.csv").open(encoding="utf-8") as fh:
            ev = list(csv.DictReader(fh))
        rough = [e for e in ev if e["case"] == "rough_lateral"]
        self.assertEqual(len(rough), 8)  # A048 seed 202: 전복 7 + 낮은 자세 1 (1단계 사건표)
        allowed = {"rotation_first", "contact_first", "simultaneous", "rotation_only", "contact_only",
                   "not_observed", "unknown"}
        self.assertTrue({e["order"] for e in ev} <= allowed)
        cal = json.loads((self.out / "CALIBRATION.json").read_text())
        self.assertTrue(all(c["R_omega_xy_p95"] is not None for c in cal))


if __name__ == "__main__":
    unittest.main()
