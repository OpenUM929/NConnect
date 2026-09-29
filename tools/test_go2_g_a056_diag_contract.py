"""관문: G-A056 A043 진단 재생 (계측 v2 · 카메라 계측 · 래퍼 · 러너 · 패키지 · 가짜 회수물로 검증기·판독기 실행).

    python -B -m unittest tools/test_go2_g_a056_diag_contract.py
"""
from __future__ import annotations

import csv
import gzip
import hashlib
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
import build_go2_a043_diag_replay_package as builder  # noqa: E402
import build_go2_diag_replay_package as builder_a052  # noqa: E402
import go2_a043_diag_readout as readout  # noqa: E402
import go2_eval_camera_probe as probemod  # noqa: E402
import go2_eval_diag_v2 as diagmod  # noqa: E402
import verify_go2_a043_diag_replay_harvest as verifier  # noqa: E402

A043 = ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15"
FEET = ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]
JOINTS = [f"{leg}_{p}_joint" for p in ("hip", "thigh", "calf") for leg in ("FL", "FR", "RL", "RR")]
EYE = [-4.0, -4.0, 4.0]


class _NoLazy:
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
        keys = [keys] if isinstance(keys, str) else list(keys)
        if keys == ["base"]:
            return [0], ["base"]
        if keys == [".*_foot"] or keys == FEET:
            return [1, 2, 3, 4], FEET
        raise ValueError(keys)


class FakeEnv:
    """A052 관문의 가짜 env 에 관절 채널·카메라 컨트롤러를 더했다."""

    def __init__(self, n=32, seed=0, break_group=None, camera_env=None, camera_offset=0.0):
        g = torch.Generator().manual_seed(seed)
        self.g, self.num_envs, self.step_dt = g, n, 0.02
        robot = types.SimpleNamespace(data=types.SimpleNamespace(), joint_names=list(JOINTS))
        robot.find_bodies = lambda pat, preserve_order=False: ([1, 2, 3, 4], FEET)
        robot.actuators = {"base_legs": types.SimpleNamespace(cfg=types.SimpleNamespace(
            effort_limit=23.5, saturation_effort=23.5, velocity_limit=30.0, stiffness=25.0, damping=0.5))}
        self.robot = robot
        self.sensor = FakeSensor(n, g)
        self.scanner = types.SimpleNamespace(data=types.SimpleNamespace())
        self.scene = {"robot": robot, "contact_forces": self.sensor, "height_scanner": self.scanner}
        terms = ["track_lin_vel_xy_exp", "ang_vel_xy_l2", "feet_air_time"]
        w = {"track_lin_vel_xy_exp": 1.5, "ang_vel_xy_l2": -0.05, "feet_air_time": 0.2}
        self.reward_manager = types.SimpleNamespace(active_terms=terms,
                                                    get_term_cfg=lambda name: types.SimpleNamespace(weight=w[name]))
        self.action_manager = types.SimpleNamespace()
        self.cfg = types.SimpleNamespace(viewer=types.SimpleNamespace(cam_prim_path="/OmniverseKit_Persp",
                                                                      resolution=(1920, 1080)))
        self.camera_env, self.camera_offset = camera_env, camera_offset
        if camera_env is not None:
            self.viewport_camera_controller = types.SimpleNamespace(
                cfg=types.SimpleNamespace(env_index=camera_env, origin_type="asset_root", asset_name="robot"),
                default_cam_eye=list(EYE), viewer_origin=None)
        self.break_group = break_group
        d = robot.data
        d.joint_effort_limits = torch.full((n, 12), 23.5)
        d.joint_pos_limits = torch.tensor([[-1.0, 1.0]]).repeat(n, 12, 1)
        d.soft_joint_pos_limits = torch.tensor([[-0.9, 0.9]]).repeat(n, 12, 1)
        self.advance()

    @property
    def unwrapped(self):
        return self

    def read_prim(self, path):
        root = self.robot.data.root_pos_w[self.camera_env].tolist()
        return [root[0] + EYE[0] + self.camera_offset, root[1] + EYE[1], root[2] + EYE[2]]

    def advance(self):
        n, g, d = self.num_envs, self.g, self.robot.data
        d.root_lin_vel_b = torch.randn(n, 3, generator=g) * 0.2
        d.root_ang_vel_b = torch.randn(n, 3, generator=g) * 0.3
        d.projected_gravity_b = torch.tensor([0.0, 0.0, -1.0]).repeat(n, 1) + torch.randn(n, 3, generator=g) * 0.02
        d.root_quat_w = torch.tensor([1.0, 0, 0, 0]).repeat(n, 1)
        d.root_pos_w = torch.randn(n, 3, generator=g) * 3 + torch.tensor([0, 0, 0.3])
        d.body_pos_w = (torch.randn(n, 5, 3, generator=g) * 0.2).clamp(-0.4, 0.4)
        d.body_lin_vel_w = torch.randn(n, 5, 3, generator=g) * 0.1
        d.joint_pos = torch.randn(n, 12, generator=g) * 0.3
        d.joint_vel = torch.randn(n, 12, generator=g)
        d.computed_torque = torch.randn(n, 12, generator=g) * 10
        d.applied_torque = d.computed_torque.clamp(-23.5, 23.5)
        if self.break_group == "joints":
            del d.applied_torque
        xs, ys = torch.meshgrid(torch.linspace(-0.8, 0.8, 17), torch.linspace(-0.5, 0.5, 11), indexing="ij")
        grid = torch.stack([xs.reshape(-1), ys.reshape(-1)], dim=1).expand(n, -1, -1)
        self.scanner.data.ray_hits_w = torch.cat([grid, torch.randn(n, 187, 1, generator=g) * 0.05], dim=2)
        self.sensor.refresh()
        self.reward_manager._step_reward = torch.randn(n, 3, generator=g)
        self.action_manager.action = torch.randn(n, 12, generator=g)
        self.action_manager.prev_action = torch.randn(n, 12, generator=g)
        if self.camera_env is not None:
            self.viewport_camera_controller.viewer_origin = d.root_pos_w[self.camera_env].clone()


def run_recorder(out: Path, steps: int, seed=0, break_group=None) -> None:
    env = FakeEnv(seed=seed, break_group=break_group)
    rec = diagmod.DiagRecorder(out, steps)
    for _ in range(steps):
        before = {k: v.clone() for k, v in vars(env.robot.data).items()}
        rec.record(env)
        after = vars(env.robot.data)
        assert all(torch.equal(before[k], after[k]) for k in before), "recorder modified robot data"
        env.advance()


def run_probe(out: Path, steps: int, target: int, offset=0.0) -> None:
    env = FakeEnv(seed=target, camera_env=target, camera_offset=offset)
    probe = probemod.CameraProbe(out, steps, target, read_prim=env.read_prim)
    for _ in range(steps):
        probe.record(env)
        env.advance()


def read_gz(p: Path) -> list[dict]:
    with gzip.open(p, "rt", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class A_RecorderV2(unittest.TestCase):
    def test_1_joint_columns_and_meta(self):
        with tempfile.TemporaryDirectory() as t:
            run_recorder(Path(t), 4)
            rows = read_gz(Path(t) / "diag.csv.gz")
            meta = json.loads((Path(t) / "diag_meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["schema"], "go2_eval_diag_v2")
            self.assertEqual(meta["unavailable"], {})
            self.assertEqual(meta["joints"]["names"], JOINTS)
            self.assertEqual(meta["joints"]["joint_effort_limits_env0"], [23.5] * 12)
            self.assertEqual(meta["joints"]["actuators"]["base_legs"]["saturation_effort"], 23.5)
            self.assertIn("last physics substep", meta["timing_note"])
            for k in ("jpos", "jvel", "jtau_cmd", "jtau_app"):
                self.assertIn(f"{k}_RR_calf_joint", rows[0])
            self.assertIn("contact_fresh", rows[0])
            self.assertTrue(all(v != "" for v in rows[0].values()))

    def test_2_joint_failure_is_recorded_as_unavailable_and_partial(self):
        with tempfile.TemporaryDirectory() as t:
            run_recorder(Path(t), 3, break_group="joints")
            meta = json.loads((Path(t) / "diag_meta.json").read_text(encoding="utf-8"))
            self.assertIn("joints", meta["unavailable"])
            self.assertIn("DIAG_PARTIAL", (Path(t) / "DIAG_STATUS.txt").read_text())
            rows = read_gz(Path(t) / "diag.csv.gz")
            self.assertEqual(rows[0]["jtau_app_FL_hip_joint"], "")
            self.assertNotEqual(rows[0]["ang_vel_b_x"], "")

    def test_3_a052_module_untouched(self):
        import go2_eval_diag as v1
        self.assertEqual(v1.SCHEMA, "go2_eval_diag_v1")
        z = zipfile.ZipFile(builder_a052.UPLOAD / "current" / builder_a052.ZIP_NAME)
        self.assertEqual(z.read("go2_g_a052/diag/go2_eval_diag.py"), (GO2 / "go2_eval_diag.py").read_bytes())


class A2_CameraProbe(unittest.TestCase):
    def test_1_rows_follow_target(self):
        with tempfile.TemporaryDirectory() as t:
            run_probe(Path(t), 20, 7)
            with (Path(t) / "camera.csv").open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 20)
            self.assertTrue(all(r["cfg_env_index"] == "7" and float(r["target_dist_xy"]) < 1e-5 for r in rows))
            self.assertTrue(all(r["nearest_env"] == "7" for r in rows))
            self.assertIn("CAMERA_PROBE_COMPLETE", (Path(t) / "CAMERA_STATUS.txt").read_text())

    def test_2_missing_controller_or_prim_is_unavailable(self):
        with tempfile.TemporaryDirectory() as t:
            env = FakeEnv(seed=1)  # no viewport_camera_controller
            probe = probemod.CameraProbe(Path(t), 2, 3, read_prim=lambda p: (_ for _ in ()).throw(RuntimeError("no prim")))
            probe.record(env)
            probe.record(env)
            meta = json.loads((Path(t) / "camera_meta.json").read_text(encoding="utf-8"))
            self.assertIn("controller", meta["unavailable"])
            self.assertIn("prim", meta["unavailable"])
            self.assertIn("CAMERA_PROBE_PARTIAL", (Path(t) / "CAMERA_STATUS.txt").read_text())


class A3_Wrappers(unittest.TestCase):
    def _run(self, modname, attr, env_extra):
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
        saved = {k: sys.modules.get(k) for k in ("gymnasium", "go2_eval_telemetry_v6", modname)}
        sys.modules["gymnasium"], sys.modules["go2_eval_telemetry_v6"] = fake_gym, base
        sys.modules.pop(modname, None)
        try:
            with tempfile.TemporaryDirectory() as t:
                os.environ.update({"NCRC_EVAL_OUT": t, "NCRC_EVAL_STEPS": "10", **env_extra})
                w = __import__(modname)
                setattr(w, attr, lambda *a: types.SimpleNamespace(record=lambda env: calls.append(("probe", None))))
                w.install()
                env = fake_gym.make("Quadruped-v0")
                self.assertEqual(env.step(7), ("obs", 7))
                self.assertEqual(calls, [("raw", 7), ("evaluator", 7), ("probe", None)])
        finally:
            for k in ("NCRC_EVAL_OUT", "NCRC_EVAL_STEPS", *env_extra):
                os.environ.pop(k, None)
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v

    def test_1_diag_wrapper_v2_order(self):
        self._run("go2_eval_telemetry_diag_wrapper_v2", "DiagRecorder", {})

    def test_2_camera_wrapper_order(self):
        self._run("go2_eval_telemetry_camera_wrapper", "CameraProbe", {"GO2_CAMERA_TARGET_ENV": "5"})


def a043_commands() -> dict[str, str]:
    want, last = {}, None
    for line in (A043 / "launcher.log").read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("COMMAND: "):
            last = line[len("COMMAND: "):].rstrip()
        for case in ("rough_lateral", "combined_yaw_right"):
            if "telemetry enabled: out=" in line and f"candidate/cases/seed_202/{case} " in line:
                want.setdefault(case, last)
    return want


class B_Runner(unittest.TestCase):
    def test_1_bash_n_and_lf(self):
        p = GO2 / builder.RUNNER
        self.assertNotIn(b"\r", p.read_bytes())
        self.assertEqual(subprocess.run(["bash", "-n", str(p)]).returncode, 0)

    def test_2_commands_equal_g_a043_issued_commands(self):
        want = a043_commands()
        self.assertEqual(set(want), {"rough_lateral", "combined_yaw_right"})
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
            case = l.split()[3]
            self.assertEqual(l.split(" COMMAND: ", 1)[1].rstrip(), want[case], l[:40])
        for l in vids:
            _, seed, case, env_index = l.split(" COMMAND: ", 1)[0].split()
            got = l.split(" COMMAND: ", 1)[1].rstrip()
            head = "/workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 32 --headless "
            self.assertTrue(want[case].startswith(head))
            expect = (head + "--video --video_length 1000 --enable_cameras " + want[case][len(head):]
                      + f" env.viewer.env_index={env_index}")
            self.assertEqual(got, expect)
        self.assertEqual({tuple(l.split(" COMMAND: ")[0].split()[2:]) for l in vids},
                         {(c, str(e)) for c, e in verifier.VIDEOS})


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
        src = A043 / "evaluation/candidate/source"
        for p in src.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                rel = p.relative_to(src).as_posix()
                self.assertEqual(z.read(pre + "plain/" + rel), p.read_bytes(), rel)
        sha = lambda n: hashlib.sha256(z.read(pre + n)).hexdigest()  # noqa: E731
        self.assertEqual(sha("plain/go2_eval_telemetry.py"), builder.EVALUATOR_SHA)
        self.assertEqual(sha("diag/go2_eval_telemetry_v6.py"), builder.EVALUATOR_SHA)
        self.assertEqual(sha("video/go2_eval_telemetry_v6.py"), builder.EVALUATOR_SHA)
        self.assertEqual(sha("policy/model_best.pt"), builder.MODEL_SHA)
        self.assertEqual(sha("policy/env.yaml"), builder.ENV_SHA)
        for root in ("diag", "video"):
            self.assertEqual(z.read(pre + f"{root}/play.py"), z.read(pre + "plain/play.py"))
            self.assertEqual(z.read(pre + f"{root}/quadruped_rewards.py"), z.read(pre + "plain/quadruped_rewards.py"))
        self.assertFalse(any(n.endswith("train.py") for n in names))
        self.assertEqual(z.getinfo(pre + builder.RUNNER).external_attr >> 16 & 0o777, 0o755)
        for n in (builder.RUNNER, "run_config.env", "diag/go2_eval_diag_v2.py", "diag/go2_eval_telemetry.py",
                  "video/go2_eval_camera_probe.py", "video/go2_eval_telemetry.py"):
            self.assertNotIn(b"\r", z.read(pre + n), n)
        self.assertEqual(z.read(pre + "plain/quadruped_rewards.py"), (A043 / "training/source/quadruped_rewards.py").read_bytes())

    def test_3_a052_release_still_rebuilds_identically(self):
        cur = builder_a052.UPLOAD / "current" / builder_a052.ZIP_NAME
        self.assertEqual(builder_a052.build_zip(builder_a052.payload()), cur.read_bytes())


# ---------------------------------------------------------------- 가짜 회수물
def write_mp4(p: Path, frames: int) -> None:
    import cv2
    import numpy as np
    w = cv2.VideoWriter(str(p), cv2.VideoWriter_fourcc(*"mp4v"), 50.0, (32, 24))
    img = np.zeros((24, 32, 3), dtype=np.uint8)
    for i in range(frames):
        img[:] = i % 255
        w.write(img)
    w.release()


def mark_resets_stale(d: Path) -> None:
    with (d / "steps.csv").open(encoding="utf-8", newline="") as fh:
        resets = {(r["step"], r["env_id"]) for r in csv.DictReader(fh) if r["terminated"] == "1" or r["truncated"] == "1"}
    rows = read_gz(d / "diag.csv.gz")
    for r in rows:
        if (r["step"], r["env_id"]) in resets:
            r["contact_fresh"] = "0"
    write_gz(d / "diag.csv.gz", rows)


def write_gz(p: Path, rows: list[dict]) -> None:
    with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def rewrite_sums(h: Path) -> None:
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  ./{p.relative_to(h).as_posix()}"
             for p in sorted(h.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.txt"]
    (h / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def zip_harvest(h: Path, dest: Path) -> Path:
    z = dest / builder.RESULT_ZIP_NAME
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as a:
        for p in sorted(h.rglob("*")):
            if p.is_file():
                a.write(p, (Path(h.name) / p.relative_to(h)).as_posix())
    (dest / (z.name + ".sha256")).write_text(f"{hashlib.sha256(z.read_bytes()).hexdigest()}  {z.name}\n")
    return z


def fake_harvest(root: Path) -> Path:
    """저장된 A043 steps.csv 로 plain·diag·영상 궤적을, 가짜 env 로 진단·카메라 채널을 만든 회수물."""
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
            run_recorder(d, 1000, seed=seed)
            mark_resets_stale(d)
    mp4 = root / "fake.mp4"
    write_mp4(mp4, 999)
    status = []
    for case, env in verifier.VIDEOS:
        d = verifier.video_dir(h, case, env)
        d.mkdir(parents=True)
        shutil.copy(stored / f"seed_202/{case}/steps.csv", d / "steps.csv")
        (d / "STATUS.txt").write_text("EVAL_RC=0\nSTEPS=1000\nROWS=32000\n")
        shutil.copy(mp4, d / "video.mp4")
        run_probe(d, 1000, env)
        (d / "video_identity.json").write_text(json.dumps({"model_sha256": builder.MODEL_SHA, "env_sha256": builder.ENV_SHA,
                                                           "case": case, "seed": 202, "env_index": env, "video_steps": 1000}))
        (h / f"logs/video_seed_202_{case}_env{env}.log").write_text("x\n")
        status.append(f"{case} env{env} rc=0 file=present")
    (h / "video/VIDEO_STATUS.txt").write_text("\n".join(status) + "\n")
    (h / "meta").mkdir()
    (h / "meta/identity.json").write_text(json.dumps({"model_sha256": builder.MODEL_SHA, "env_sha256": builder.ENV_SHA,
                                                      "evaluator_sha256": builder.EVALUATOR_SHA}))
    for name in ("meta/RUN_TIMES.txt", "meta/REPRO_STATUS.txt", "meta/run_config.env", "meta/experiment.json",
                 "RUNNER_STATUS.txt", "launcher.snapshot.log"):
        (h / name).write_text("x\n")
    (h / "RESULT_STATUS.txt").write_text("RESULT_STATE=PACKAGED\nCOLLECTION_STATUS=COMPLETE_4_OF_4\n")
    rewrite_sums(h)
    return h


class D_VerifierAndReadout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name)
        cls.h = fake_harvest(cls.base)
        cls.zip = zip_harvest(cls.h, cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run(self, mutate=None, as_dir=False):
        t = tempfile.TemporaryDirectory()
        h2 = Path(t.name) / builder.KEEP_DIR_NAME
        shutil.copytree(self.h, h2)
        if mutate:
            mutate(h2)
        target = h2 if as_dir else zip_harvest(h2, Path(t.name))
        out = Path(t.name) / "o"
        code = verifier.main([str(target), "--out", str(out)])
        v = json.loads((out / "HARVEST_VERDICT.json").read_text(encoding="utf-8"))
        return code, v, t, out

    def test_1_normal_zip_is_0_ok(self):
        code, v, t, _ = self._run()
        t.cleanup()
        self.assertEqual(code, 0)
        self.assertEqual((v["zip"], v["artifact"], v["channels"], v["shutdown"]),
                         ("ZIP_SHA_VERIFIED", "ARTIFACT_VERIFIED", "DIAG_CHANNELS_COMPLETE", "OK"))
        self.assertTrue(all(x == "VIDEO_ENV_MATCHED" for x in v["video"].values()), v["video"])
        self.assertEqual(v["repro"]["plain_vs_stored:rough_lateral"], "NO_DIFFERENCE_IN_STORED_CHANNELS")

    def test_2_directory_is_not_a_shutdown_ok(self):
        code, v, t, _ = self._run(as_dir=True)
        t.cleanup()
        self.assertEqual((code, v["zip"], v["shutdown"]), (3, "ZIP_NOT_CHECKED", "EXCEPTION_DECISION_REQUIRED"))

    def test_3_zip_sidecar_mismatch_is_1(self):
        with tempfile.TemporaryDirectory() as t:
            z = Path(t) / self.zip.name
            shutil.copy(self.zip, z)
            (Path(t) / (z.name + ".sha256")).write_text("0" * 64 + f"  {z.name}\n")
            self.assertEqual(verifier.main([str(z), "--out", str(Path(t) / "o")]), 1)
            v = json.loads((Path(t) / "o/HARVEST_VERDICT.json").read_text(encoding="utf-8"))
            self.assertEqual((v["zip"], v["shutdown"]), ("ZIP_SHA_MISMATCH", "DO_NOT_SHUTDOWN"))

    def test_4_required_file_missing_or_unlisted_is_1(self):
        def m(h):
            (h / "diag/cases/seed_202/combined_yaw_right/diag_meta.json").unlink()
            rewrite_sums(h)
        code, v, t, _ = self._run(m)
        t.cleanup()
        self.assertEqual((code, v["shutdown"]), (1, "DO_NOT_SHUTDOWN"))

        def m2(h):
            lines = [l for l in (h / "SHA256SUMS.txt").read_text().splitlines() if "RUN_TIMES" not in l]
            (h / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
        code, v, t, _ = self._run(m2)
        t.cleanup()
        self.assertEqual(code, 1)
        self.assertIn("required file not in SHA256SUMS: meta/RUN_TIMES.txt", v["problems"])

    def test_5_unavailable_joint_channel_is_3_not_success(self):
        def m(h):
            p = h / "diag/cases/seed_202/rough_lateral/diag_meta.json"
            meta = json.loads(p.read_text())
            meta["unavailable"]["joints"] = "AttributeError: applied_torque"
            p.write_text(json.dumps(meta))
            rewrite_sums(h)
        code, v, t, _ = self._run(m)
        t.cleanup()
        self.assertEqual((code, v["channels"], v["shutdown"]), (3, "DIAG_CHANNELS_INCOMPLETE", "EXCEPTION_DECISION_REQUIRED"))
        self.assertTrue(any("joints unavailable" in c for c in v["channel_problems"]))
        self.assertTrue(v["collection"].startswith("PARTIAL_NOT_COMPLETE"))
        self.assertTrue(v["exception_evidence"]["diag_csv"]["rough_lateral"])

    def test_6_blank_joint_value_in_non_reset_row_is_3_but_reset_row_is_allowed(self):
        resets = verifier.reset_rows(self.h / "diag/cases/seed_202/combined_yaw_right/steps.csv")

        def bad(h):
            p = h / "diag/cases/seed_202/combined_yaw_right/diag.csv.gz"
            rows = read_gz(p)
            r = next(r for r in rows if (int(r["step"]), int(r["env_id"])) not in resets and r["step"] == "300")
            r["jtau_cmd_RL_calf_joint"] = "nan"
            write_gz(p, rows)
            rewrite_sums(h)
        code, v, t, _ = self._run(bad)
        t.cleanup()
        self.assertEqual(code, 3)
        self.assertTrue(any("jtau_cmd_RL_calf_joint missing or non-finite in 1/" in c for c in v["channel_problems"]))

        def reset_blank(h):
            p = h / "diag/cases/seed_202/combined_yaw_right/diag.csv.gz"
            rows = read_gz(p)
            for r in rows:
                if (int(r["step"]), int(r["env_id"])) in resets:
                    r["jpos_FL_hip_joint"] = ""
                    r["FL_contact_time"] = ""
            write_gz(p, rows)
            rewrite_sums(h)
        code, v, t, _ = self._run(reset_blank)
        t.cleanup()
        self.assertEqual((code, v["channels"]), (0, "DIAG_CHANNELS_COMPLETE"))

    def test_7_repro_mismatch_is_reported_and_readout_detaches_stored_table(self):
        def m(h):
            for rel in ("plain/cases/seed_202/rough_lateral/steps.csv",):
                p = h / rel
                lines = p.read_text(encoding="utf-8").splitlines()
                cols = lines[500].split(",")
                cols[7] = "0.123456"
                lines[500] = ",".join(cols)
                p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            rewrite_sums(h)
        code, v, t, out = self._run(m)
        self.assertEqual(v["repro"]["plain_vs_stored:rough_lateral"], "DIVERGED")
        # 영상 steps 는 저장본과 같으므로 plain 과 달라진다 → 자기 실행하고만 대응
        self.assertEqual(v["video"]["rough_lateral_env5"], "VIDEO_ENV_OWN_RUN_ONLY")
        self.assertEqual(code, 0)
        self.assertEqual(readout.main([str(out / "extracted" / builder.KEEP_DIR_NAME), "--out", str(out)]), 0)
        with (out / "EVENTS_A043_DIAG.csv").open(encoding="utf-8") as fh:
            ev = list(csv.DictReader(fh))
        rough = [e for e in ev if e["case"] == "rough_lateral"]
        self.assertTrue(all(e["stored_table_env_match"] == "0" and not e.get("stored_onset_t") for e in rough))
        self.assertTrue(all(not e.get("video_file") for e in rough))
        yaw = [e for e in ev if e["case"] == "combined_yaw_right"]
        self.assertTrue(all(e["stored_table_env_match"] == "1" for e in yaw))
        t.cleanup()

    def test_8_video_missing_is_3_with_reason(self):
        def m(h):
            (verifier.video_dir(h, "combined_yaw_right", 16) / "video.mp4").unlink()
            rewrite_sums(h)
        code, v, t, out = self._run(m)
        rows = list(csv.DictReader((out / "VIDEO_CHECK.csv").open(encoding="utf-8")))
        t.cleanup()
        self.assertEqual((code, v["shutdown"]), (3, "EXCEPTION_DECISION_REQUIRED"))
        self.assertEqual(v["video"]["combined_yaw_right_env16"], "VIDEO_NOT_ACQUIRED")
        self.assertIn("video.mp4", next(r for r in rows if r["env_index"] == "16")["reason"])

    def test_9_camera_off_target_or_wrong_frames_is_unverified(self):
        def m(h):
            d = verifier.video_dir(h, "rough_lateral", 11)
            for f in ("camera.csv", "camera_meta.json", "CAMERA_STATUS.txt"):
                (d / f).unlink()
            run_probe(d, 1000, 11, offset=0.5)      # 카메라가 대상에서 0.5 m 떨어져 있다
            rewrite_sums(h)
        code, v, t, _ = self._run(m)
        t.cleanup()
        self.assertEqual(code, 3)
        self.assertEqual(v["video"]["rough_lateral_env11"], "VIDEO_CAMERA_UNVERIFIED")

        def f(h):
            write_mp4(verifier.video_dir(h, "rough_lateral", 5) / "video.mp4", 400)
            rewrite_sums(h)
        code, v, t, _ = self._run(f)
        t.cleanup()
        self.assertEqual(v["video"]["rough_lateral_env5"], "VIDEO_NOT_ACQUIRED")

    def test_10_readout_values_are_preregistered_and_first_episode_only(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "o"
            self.assertEqual(readout.main([str(self.h), "--out", str(out)]), 0)
            ev = list(csv.DictReader((out / "EVENTS_A043_DIAG.csv").open(encoding="utf-8")))
            self.assertEqual(sum(e["case"] == "rough_lateral" for e in ev), 11)       # 기존 사건표와 같은 수
            self.assertEqual(sum(e["case"] == "combined_yaw_right" for e in ev), 9)
            a = {"rotation_first", "contact_first", "simultaneous", "rotation_only", "contact_only", "not_observed", "unknown"}
            b = {"lateral_first", "contact_first", "simultaneous", "lateral_only", "contact_only", "not_observed", "unknown"}
            self.assertTrue({e["order"] for e in ev} <= a)
            self.assertTrue({e["order_b"] for e in ev} <= b)
            self.assertTrue(all(e["stored_table_env_match"] == "1" for e in ev))
            self.assertTrue(any(e.get("video_file") for e in ev if e["env_id"] == "5" and e["case"] == "rough_lateral"))
            before = (out / "EVENTS_A043_DIAG.csv").read_bytes()
            # 첫 episode 뒤 행을 망가뜨려도 판독이 같아야 한다(C-39)
            h2 = Path(t) / builder.KEEP_DIR_NAME
            shutil.copytree(self.h, h2)
            d = h2 / "diag/cases/seed_202/rough_lateral"
            steps = readout.load_steps_first_episode(d / "steps.csv")
            rows = read_gz(d / "diag.csv.gz")
            for r in rows:
                e = int(r["env_id"])
                if int(r["step"]) > len(steps[e]):
                    for k in r:
                        if k not in ("step", "env_id"):
                            r[k] = "999"
            write_gz(d / "diag.csv.gz", rows)
            out2 = Path(t) / "o2"
            self.assertEqual(readout.main([str(h2), "--out", str(out2)]), 0)
            ev2 = list(csv.DictReader((out2 / "EVENTS_A043_DIAG.csv").open(encoding="utf-8")))
            strip = lambda es: [{k: v for k, v in e.items() if k not in ("video", "video_file")} for e in es]  # noqa: E731
            self.assertEqual(strip(ev2), strip(list(csv.DictReader(before.decode().splitlines()))))

    def test_12_effort_ratio_uses_actuator_limit_not_physx_1e9(self):
        # 2026-09-29 회수물: 명시 actuator 는 PhysX 관절 effort 한계를 1e9 로 둔다.  비율 분모는 모터 한계여야 한다.
        import go2_a043_diag_readout as ro
        names = ["FL_hip_joint", "FR_hip_joint"]
        meta = {"joints": {"names": names, "joint_effort_limits_env0": [1e9, 1e9],
                           "soft_joint_pos_limits_env0": [[-0.94, 0.94], [-0.94, 0.94]],
                           "actuators": {"base_legs": {"class": "DCMotor", "effort_limit": 23.5}}}}
        row = {"jtau_app_FL_hip_joint": 23.5, "jtau_cmd_FL_hip_joint": 30.0, "jpos_FL_hip_joint": 0.0,
               "jtau_app_FR_hip_joint": -11.75, "jtau_cmd_FR_hip_joint": -11.75, "jpos_FR_hip_joint": 0.0}
        out = ro.joint_summary([row], meta)
        self.assertEqual(out["tau_app_over_effort_limit_max"], 1.0)
        self.assertEqual(out["rows_cmd_ne_app_torque"], 1)
        meta["joints"]["actuators"] = {}
        self.assertEqual(ro.joint_summary([row], meta)["tau_app_over_effort_limit_max"], 0.0)

    def test_11_missing_inputs_are_unknown(self):
        self.assertEqual(readout.order_b(None, 3, "steady_window_too_short", ""), "unknown")
        self.assertEqual(readout.order_b(3, None, "", "contact_stale"), "unknown")
        self.assertEqual(readout.order_b(None, None, "", ""), "not_observed")
        self.assertEqual(readout.order_b(0, 2, "", ""), "simultaneous")    # 0.04 s 이하
        self.assertEqual(readout.order_b(0, 3, "", ""), "lateral_first")
        rows = [{f"action_{i}": 0.0 for i in range(12)} for _ in range(10)]
        self.assertEqual(readout.t_act_in(rows, 0.5), (None, "action_missing"))
        self.assertEqual(readout.t_act_in([], None), (None, "calibration_missing"))


if __name__ == "__main__":
    unittest.main()
