"""Contract for the PC2 single-point package, launcher and readout (2026-10-02).

왜 있는가.  설계(upload/plan/GO2_PC2_DENSE_SWEEP_PROPOSAL_20261002.md §13-3·§14)를 기계로 고정한다.
  - 패키지: 점마다 A048 과 정확히 한 항(B1 은 0항)만 다르고, G-A057·G-A058 과 같은 설정인 점은 발행본과 보상 바이트가 같고,
    shared 는 G-A055 v2 바이트이며, 이름이 PC1 폴더·ZIP·상태·tmux 와 겹치지 않는다.
  - 러너: 지정한 한 점만 돌고 멈춘다. 인수 없음·알 수 없는 옵션·key 누락·목록 밖·경로 형태 key 는 폴더를 만들기 전에 거부한다.
    완료 점은 SKIP_DONE, 실패 점은 같은 --only 로 GO2_RESUME=1 재개하며 기존 증거와 다른 key 폴더는 그대로다.
  - 판독: 표적/이동·추종/보호를 나누고(과속은 개선 아님, 바닥값 seed 표시, 일부 seed 손실 보존), 불완전 run 도 부분 관측을 남기며,
    sentinel 범위 밖은 표시만 하고, 다음 점을 고르지 않는다.

    python -m unittest tools.test_go2_pc2_point_contract
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
import build_go2_pc2_point_package as builder  # noqa: E402
import build_go2_g_a057_sweep_package as a057  # noqa: E402
import go2_pc2_point_readout as readout  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict  # noqa: E402
from test_go2_g_a057_sweep_contract import FAKE_RUNNER as A057_FAKE  # noqa: E402

BASH = shutil.which("bash")
G_A057_ZIP = ROOT / "workspace/training/quadruped/upload/G-A057/current/GO2_G_A057_a048_single_var_sweep_v1.zip"
G_A058_ZIP = ROOT / "workspace/training/quadruped/upload/G-A058/current/GO2_G_A058_replicate_a048s42_a043s43s44_v1.zip"
# The G-A057 fake runner reads GO2_SWEEP_KEEP_BASE; the PC2 launcher exports GO2_POINT_KEEP_BASE.
FAKE_RUNNER = A057_FAKE.replace("GO2_SWEEP_KEEP_BASE", "GO2_POINT_KEEP_BASE")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def tree_hash(p: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(p).as_posix().encode() + b"\0" + f.read_bytes())
    return h.hexdigest()


class Package(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, cls.info = builder.build()
        cls.files = cls.info["files"]
        cls.n = cls.info["names"]

    def test_1_points_and_one_term_difference(self) -> None:
        keys = [l.split()[0] for l in self.files["points.txt"].decode().splitlines()]
        self.assertEqual(keys, [p[0] for p in builder.POINTS])
        base = builder.base6()
        self.assertEqual({k: base[k] for k in readout.A048_REWARDS}, readout.A048_REWARDS)  # readout's A048 table = env.yaml
        for key, var, value, _ in builder.POINTS:
            got = reward_dict(self.files[f"runs/{key}/candidate/quadruped_rewards.py"].decode())
            diff = [k for k in REWARD_NAMES if got[k] != base[k]]
            self.assertEqual(diff, [] if var is None else [var], key)
            if var:
                self.assertEqual(got[var], value, key)
            cfg = self.files[f"runs/{key}/run_config.env"].decode()
            self.assertIn("\nTRAIN_SEED=42\n", cfg)
            self.assertIn("\nNUM_ENVS=4096\n", cfg)
            self.assertIn("\nMAX_ITERATIONS=1000\n", cfg)
            self.assertIn("\nEVAL_CHECKPOINT_ITER=900\n", cfg)

    @unittest.skipUnless(G_A057_ZIP.is_file() and G_A058_ZIP.is_file(), "published G-A057/G-A058 ZIPs needed")
    def test_2_same_settings_match_published_reward_bytes(self) -> None:
        z57, z58 = zipfile.ZipFile(G_A057_ZIP), zipfile.ZipFile(G_A058_ZIP)
        for mine, theirs in builder.SAME_AS_G_A057.items():
            self.assertEqual(self.files[f"runs/{mine}/candidate/quadruped_rewards.py"],
                             z57.read(f"go2_g_a057/runs/{theirs}/candidate/quadruped_rewards.py"), mine)
        self.assertEqual(self.files[f"runs/{builder.B1_KEY}/candidate/quadruped_rewards.py"],
                         z58.read("go2_g_a058/runs/a048_seed42/candidate/quadruped_rewards.py"))

    def test_3_shared_bytes_are_the_g_a055_v2_bytes(self) -> None:
        for k, v in a057.shared_files(a057.source_payload()).items():
            self.assertEqual(self.files["shared/" + k], v, k)

    def test_4_each_materialised_tree_matches_its_checksums(self) -> None:
        shared = {k[len("shared/"):]: v for k, v in self.files.items() if k.startswith("shared/")}
        for key, *_ in builder.POINTS:
            tree = dict(shared)
            tree.update({k[len(f"runs/{key}/"):]: v for k, v in self.files.items() if k.startswith(f"runs/{key}/")})
            listed = dict(reversed(l.split("  ", 1)) for l in tree.pop("PACKAGE_SHA256SUMS.txt").decode().splitlines())
            self.assertEqual(set(listed), set(tree), key)
            for name, digest in listed.items():
                self.assertEqual(sha(tree[name]), digest, f"{key}:{name}")

    def test_5_names_are_pc2_and_do_not_collide_with_pc1(self) -> None:
        pc1 = set()
        for z, pre in ((G_A057_ZIP, "go2_g_a057/"), (G_A058_ZIP, "go2_g_a058/")):
            if z.is_file():
                order = zipfile.ZipFile(z).read(pre + "sweep_order.txt").decode().split()
                pc1.update(order)
        for line in self.files["points.txt"].decode().splitlines():
            key, keep, zipn = line.split()
            self.assertIn("_pc2_", keep)
            self.assertIn("_PC2_", zipn)
            self.assertNotIn(keep, pc1)
            self.assertNotIn(zipn, pc1)
        cfg = self.files["point_config.env"].decode()
        for word in ("go2_g_a057", "go2_g_a058"):
            self.assertNotIn(word, cfg)
        self.assertIn("pc2", self.n["tmux"])
        self.assertIn("pc2", self.n["status_dir"])
        self.assertIn("pc2", self.n["work_dir"])

    def test_6_launcher_bytes_and_syntax(self) -> None:
        mine = self.files["run_point.sh"]
        self.assertEqual(mine, builder.LAUNCHER.read_bytes().replace(b"\r\n", b"\n"))
        self.assertNotIn(b"\r\n", mine)
        if BASH:
            r = subprocess.run([BASH, "-n", "-"], input=mine, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_7_publish_needs_an_explicit_unused_work_id(self) -> None:
        with self.assertRaises(SystemExit):
            builder.main(["--publish"])
        self.assertTrue(builder.id_in_use("G-A059"))  # existing number is detected
        with self.assertRaises(ValueError):
            builder.names("../x")


@unittest.skipUnless(BASH, "bash needed")
class Launcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, info = builder.build()
        cls.prefix = info["names"]["prefix"]
        cls.lines = {l.split()[0]: l.split()[1:] for l in info["files"]["points.txt"].decode().splitlines()}

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        zipfile.ZipFile(io.BytesIO(self.data)).extractall(self.tmp / "pkg")
        self.root = self.tmp / "pkg" / self.prefix.rstrip("/")
        self.keep = self.tmp / "keep"
        self.keep.mkdir()
        self.work = self.tmp / "work"
        self.runner = self.tmp / "fake_runner.sh"
        self.runner.write_bytes(FAKE_RUNNER.encode())
        self.plan = self.tmp / "plan.txt"
        self.plan.write_text("", encoding="utf-8")
        self.calls = self.tmp / "calls.txt"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_point(self, *args: str) -> int:
        env = {**os.environ, "GO2_POINT_TEST_MODE": "1", "GO2_POINT_KEEP_BASE": self.keep.as_posix(),
               "GO2_POINT_TEST_RUNNER": self.runner.as_posix(), "GO2_POINT_TEST_FREE_GB": "500",
               "GO2_POINT_WORK": self.work.as_posix(), "FAKE_PLAN": self.plan.as_posix(),
               "FAKE_CALLS": self.calls.as_posix()}
        r = subprocess.run([BASH, (self.root / "run_point.sh").as_posix(), *args], env=env,
                           capture_output=True, timeout=600)
        self.last = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        return r.returncode

    def calls_list(self) -> list[str]:
        return self.calls.read_text(encoding="utf-8").splitlines() if self.calls.is_file() else []

    def status(self) -> list[tuple[str, str]]:
        p = next(self.keep.glob("*_pc2_points/POINT_STATUS.tsv"), None)
        if p is None:
            return []
        with p.open(encoding="utf-8") as fh:
            return [(r["key"], r["status"]) for r in csv.DictReader(fh, delimiter="\t")]

    def assert_nothing_created(self) -> None:
        self.assertEqual(list(self.keep.iterdir()), [], self.last)
        self.assertFalse(self.work.exists(), self.last)
        self.assertEqual(self.calls_list(), [])

    def test_a_no_argument_is_help_only(self) -> None:
        self.assertEqual(self.run_point(), 0, self.last)
        self.assertIn("--only", self.last)
        self.assert_nothing_created()

    def test_b_refusals_create_nothing(self) -> None:
        for args in (("--bogus",), ("--only",), ("--inner",), ("--only", "not_a_point"), ("--only", "../x"),
                     ("--only", "a/b"), ("--only", "a048 seed42"), ("--only", "a048_seed42", "extra"),
                     ("a048_seed42",), ("--list", "x")):
            self.assertEqual(self.run_point(*args), 64, f"{args}: {self.last}")
            self.assert_nothing_created()

    def test_c_only_runs_exactly_that_point_and_stops(self) -> None:
        key = "ang_vel_xy_l2_m0p08"
        self.assertEqual(self.run_point("--only", key), 0, self.last)
        self.assertEqual(self.calls_list(), [f"{key} resume=0"])  # key survived the outer → inner call
        self.assertEqual(self.status(), [(key, "DONE")])
        made = {p.name for p in self.keep.iterdir() if p.is_dir() and not p.name.endswith("_points")}
        self.assertEqual(made, {self.lines[key][0]})
        self.assertEqual({p.name for p in self.work.iterdir()}, {key})

    def test_d_done_point_is_skipped_and_untouched(self) -> None:
        key = builder.B1_KEY
        self.assertEqual(self.run_point("--only", key), 0, self.last)
        keep_dir = self.keep / self.lines[key][0]
        before = tree_hash(keep_dir)
        self.calls.write_text("", encoding="utf-8")
        self.assertEqual(self.run_point("--only", key), 0, self.last)
        self.assertEqual(self.calls_list(), [])
        self.assertEqual(self.status()[-1], (key, "SKIP_DONE"))
        self.assertEqual(tree_hash(keep_dir), before)

    def test_e_failure_then_resume_keeps_evidence_and_other_points(self) -> None:
        done, failing = builder.B1_KEY, "track_lin_vel_xy_exp_p1p4"
        self.assertEqual(self.run_point("--only", done), 0, self.last)
        other_before = tree_hash(self.keep / self.lines[done][0])
        self.plan.write_text(f"{failing} fail_once\n", encoding="utf-8")
        self.assertEqual(self.run_point("--only", failing), 30, self.last)
        self.assertEqual(self.status()[-1], (failing, "RUN_ERROR"))
        evidence = self.keep / self.lines[failing][0] / "training" / "EVIDENCE_KEEP.txt"
        evidence.write_text("partial evidence", encoding="utf-8")
        self.calls.write_text("", encoding="utf-8")
        self.assertEqual(self.run_point("--only", failing), 0, self.last)
        self.assertEqual(self.calls_list(), [f"{failing} resume=1"])
        self.assertEqual(self.status()[-1], (failing, "DONE"))
        self.assertEqual(evidence.read_text(encoding="utf-8"), "partial evidence")
        self.assertEqual(tree_hash(self.keep / self.lines[done][0]), other_before)

    def test_f_failure_before_training_is_23_and_list_works(self) -> None:
        key = "track_lin_vel_xy_exp_p1p3"
        self.plan.write_text(f"{key} fail_pre\n", encoding="utf-8")
        self.assertEqual(self.run_point("--only", key), 23, self.last)
        self.assertEqual(self.run_point("--list"), 0, self.last)
        self.assertIn(key, self.last)

    def test_g_existing_zip_without_folder_is_not_overwritten(self) -> None:
        key = "ang_vel_xy_l2_m0p1"
        zp = self.keep / self.lines[key][1]
        zp.write_text("old", encoding="utf-8")
        self.assertEqual(self.run_point("--only", key), 33, self.last)
        self.assertEqual(zp.read_text(encoding="utf-8"), "old")


# ---------------- readout on synthetic harvests ----------------
# 완전한 정상 수확물(§16 R1): 69 summary, 판독에 쓰는 case 의 steps 전부, run 대응 사슬(RUNNER_STATUS ↔ CHECKPOINT_PIN ↔
# checkpoint·env.yaml 해시 ↔ 평가 identity.json ↔ report 출처·해시), 장비 기록.  각 회귀 테스트는 여기서 한 가지만 깬다.
CASES = ("backward", "combined_yaw_left", "combined_yaw_right", "diagonal_left", "diagonal_right", "dr", "forward_fast",
         "forward_nominal", "forward_slow", "left", "push_neg_x", "push_neg_y", "push_pos_x", "push_pos_y", "right",
         "rough_forward", "rough_lateral", "slope_minus_20", "slope_plus_20", "stairs_10_down", "stairs_10_up",
         "stairs_15_down", "stairs_15_up")
HEAD = ("step,time_s,env_id,cmd_vx,cmd_vy,cmd_wz,actual_vx,actual_vy,actual_wz,error_xy,error_yaw,speed_xy,"
        "root_x,root_y,root_z,proj_grav_z,terrain_z,height_rel,upright,terminated,truncated")
H64 = {k: hashlib.sha256(k.encode()).hexdigest() for k in ("evaluator", "registry", "baseline", "code")}


def fall_summary(n: int, **extra) -> dict:
    return {"posture_measured": True, "posture_fall_verdict_ambiguous": False, "posture_envs_observed": 32,
            "posture_fall_env_count_optimistic": n, "posture_fall_env_count_pessimistic": n, **extra}


WALK_ROWS = 100
STAIRS_ROWS = 160


def walk_steps(cmd: tuple[float, float], vel: tuple[float, float], early_term_env: int | None = None) -> str:
    """실제 구조처럼 32대 x WALK_ROWS 행. early_term_env 는 50행에서 종료 기록 뒤에도 행이 이어진다(실측 구조)."""
    out = [HEAD]
    for e in range(32):
        for i in range(1, WALK_ROWS + 1):
            t = i * 0.02
            term = 1 if (e == early_term_env and i == 50) else 0
            out.append(f"{i},{t:.2f},{e},{cmd[0]},{cmd[1]},0.0,{vel[0]},{vel[1]},0.0,0.05,0.0,0.3,"
                       f"{vel[0] * t:.4f},{vel[1] * t:.4f},0.35,-1.0,0.0,0.35,1,{term},0")
    return "\n".join(out) + "\n"


def stairs_steps(height: float, reached: int, stall: bool, events: dict[int, str] | None = None) -> str:
    """32대 x STAIRS_ROWS 행. 1 m/s 로 가다가 1~2 s 사이 앞 reached 대만 2.5 단 높이를 오른다(1 s 정착 뒤라 계수기가 센다,
    첫 2단 도달은 약 1.68 s). 2 s 뒤 stall 이면 멈추고, 아니면 0.5 m/s 로 계속 간다.
    events: tilt_before(0.6~1.2 s 기울기 뒤 회복), tilt_after(2.2~2.8 s 기울기), term_after(2.4 s 종료 뒤 reset 행),
    trunc_after(2.4 s 절단 뒤 reset 행이 0.8 s 기울어짐)."""
    events = events or {}
    out = [HEAD]
    for e in range(32):
        rise = 2.5 * height if e < reached else 0.0
        ev = events.get(e)
        x = 0.0
        for i in range(1, STAIRS_ROWS + 1):
            t = i * 0.02
            vx = 1.0 if t <= 2.0 else (0.0 if stall else 0.5)
            x += vx * 0.02
            z = 0.35 + rise * min(max(t - 1.0, 0.0), 1.0)
            grav, term, trunc, xx, zz = -1.0, 0, 0, x, z
            if ev == "tilt_before" and 0.6 <= t <= 1.2:
                grav = 0.0
            if ev == "tilt_after" and 2.2 <= t <= 2.8:
                grav = 0.0
            if ev in ("term_after", "trunc_after") and i >= 120:
                if i == 120:
                    term, trunc = (1, 0) if ev == "term_after" else (0, 1)
                else:
                    xx, zz = 0.0, 0.35  # reset 뒤 상태
                    grav = 0.0 if ev == "trunc_after" else -1.0
            out.append(f"{i},{t:.2f},{e},0.5,0.0,0.0,{vx},0.0,0.0,0.05,0.0,{vx},{xx:.4f},0.0,{zz:.4f},{grav},"
                       f"0.0,0.35,1,{term},{trunc}")
    return "\n".join(out) + "\n"


def make_harvest(d: Path, key: str, *, rewards: dict | None = None, lateral_falls=(5, 5, 5),
                 lateral_vy=(0.25, 0.25, 0.25), lateral_rmse=(0.2, 0.2, 0.2), push_falls=(1, 1, 1),
                 stairs15=(10, 10, 10), stairs15_stall=False, stairs15_events=None, lateral_early_term=None,
                 seed_cfg="42", forward_speed=0.75, sentinel_lateral=20, gpu="NVIDIA GeForce RTX 3050") -> Path:
    rewards = rewards or dict(readout.A048_REWARDS)
    for i, s in enumerate(readout.SEEDS):
        for c in CASES:
            case = f"dr_seed_{s}" if c == "dr" else c
            p = d / "evaluation/candidate/cases" / f"seed_{s}" / case
            p.mkdir(parents=True, exist_ok=True)
            data, steps = fall_summary(1), None
            if case == "rough_lateral":
                data = fall_summary(lateral_falls[i], tracking_xy_rmse=lateral_rmse[i])
                steps = walk_steps((0.0, 0.3), (0.0, lateral_vy[i]), lateral_early_term)
            elif case == "forward_nominal":
                data = fall_summary(0, speed_xy_mean=forward_speed, tracking_xy_rmse=0.1 if forward_speed > 0.2 else 0.7)
                steps = walk_steps((0.75, 0.0), (forward_speed, 0.0))
            elif case == "rough_forward":
                data = fall_summary(1, tracking_xy_rmse=0.25)
                steps = walk_steps((0.5, 0.0), (0.45, 0.0))
            elif case.startswith("push_pos_x"):
                data = fall_summary(push_falls[i])
                steps = walk_steps((0.0, 0.0), (0.0, 0.0))
            elif case.startswith("push_") or case == "combined_yaw_right":
                steps = walk_steps((0.0, 0.0), (0.0, 0.0))
            elif case == "stairs_10_down":
                steps = stairs_steps(0.10, 20, False)
            elif case == "stairs_15_down":
                steps = stairs_steps(0.15, stairs15[i], stairs15_stall, stairs15_events)
            if steps is not None:
                n = STAIRS_ROWS if case.startswith("stairs") else WALK_ROWS
                data = {**data, "steps": n, "rows": 32 * n}
                (p / "steps.csv").write_text(steps, encoding="utf-8")
                (p / "metadata.json").write_text(json.dumps({"num_envs": 32, "max_steps": n}), encoding="utf-8")
            (p / "summary.json").write_text(json.dumps(data), encoding="utf-8")
    sent = {("101", "rough_lateral"): sentinel_lateral, ("101", "rough_forward"): 1, ("101", "forward_nominal"): 0,
            ("202", "slope_plus_20"): 0, ("202", "dr_seed_202"): 1}
    for (s, c), v in sent.items():
        p = d / "evaluation/g_a033_sentinel/cases" / f"seed_{s}" / c
        p.mkdir(parents=True, exist_ok=True)
        (p / "summary.json").write_text(json.dumps({"posture_fall_env_count_pessimistic": v}), encoding="utf-8")
    vid = d / "evaluation/candidate/videos"
    vid.mkdir(parents=True, exist_ok=True)
    for i in range(10):
        (vid / f"v{i}.mp4").write_bytes(b"x")
    (d / "RESULT_STATUS.txt").write_text("RESULT_STATE=FULL\nCOLLECTION_STATUS=FULL_69_COMPLETE\n", encoding="utf-8")
    (d / "training").mkdir(exist_ok=True)
    env_yaml = ("rewards:\n" + "".join(f"  {k}:\n    weight: {v}\n" for k, v in rewards.items()) + "other: 1\n").encode()
    (d / "training/env.yaml").write_bytes(env_yaml)
    model = f"model {key}".encode()
    (d / "training/model_best.pt").write_bytes(model)
    msha, esha = sha(model), sha(env_yaml)
    (d / "training/CHECKPOINT_PIN.txt").write_text(f"EVAL_CHECKPOINT_ITER=900\nEVAL_CHECKPOINT_SHA={msha}\n", encoding="utf-8")
    (d / "RUNNER_STATUS.txt").write_text(
        f"RUNNER_RC=0\nRUN_ID=train_G-A060-Go2_pc2_{key}_1000\nTRAIN_SEED={seed_cfg}\nCANDIDATE_MODEL_SHA={msha}\n"
        f"CANDIDATE_ENV_SHA={esha}\nEVALUATOR_SHA={H64['evaluator']}\nREGISTRY_SHA={H64['registry']}\n", encoding="utf-8")
    (d / "evaluation/candidate/identity.json").write_text(json.dumps(
        {"policy": "candidate", "model_sha256": msha, "env_sha256": esha, "registry_sha256": H64["registry"],
         "evaluator_sha256": H64["evaluator"]}), encoding="utf-8")
    (d / "exported").mkdir(exist_ok=True)
    rep = f"<html>report {key}</html>".encode()
    (d / "exported/report.html").write_bytes(rep)
    (d / "exported/report.html.sha256").write_text(f"{sha(rep)} *report.html\n", encoding="utf-8")
    (d / "exported/REPORT_STATUS.txt").write_text(
        f"REPORT_STATUS=REPORT_ACQUIRED\nSOURCE=/workspace/go2_g_a060_pc2_work/{key}/candidate/exported/report.html\n",
        encoding="utf-8")
    (d / "meta").mkdir(exist_ok=True)
    (d / "meta/gpu.csv").write_text(f"{gpu}, 580.88, 6144 MiB\n", encoding="utf-8")
    (d / "meta/run_config.env").write_text(
        f"KEEP_DIR_NAME={d.name}\nTRAIN_SEED={seed_cfg}\nNUM_ENVS=4096\nMAX_ITERATIONS=1000\nEVAL_CHECKPOINT_ITER=900\n"
        f"GO2_STAGE=full\nEXPECTED_EVALUATOR_SHA={H64['evaluator']}\nEXPECTED_REGISTRY_SHA={H64['registry']}\n"
        f"BASELINE_MODEL_SHA={H64['baseline']}\n", encoding="utf-8")
    (d / "meta/PACKAGE_SHA256SUMS.txt").write_text(f"{H64['code']}  train.py\n{sha(d.name.encode())}  candidate/quadruped_rewards.py\n",
                                                  encoding="utf-8")
    (d / "meta/evaluator.sha256").write_text(f"{H64['evaluator']}  evaluator\n", encoding="utf-8")
    (d / "meta/registry.sha256").write_text(f"{H64['registry']}  registry\n", encoding="utf-8")
    return d


KEY = "ang_vel_xy_l2_m0p08"


class Readout(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = make_harvest(cls.tmp / "b1", builder.B1_KEY, lateral_falls=(5, 8, 3))
        cls.rw = dict(readout.A048_REWARDS, ang_vel_xy_l2=-0.08)
        cls.good = make_harvest(cls.tmp / "good", KEY, rewards=cls.rw, lateral_falls=(2, 4, 1))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def variant(self, name: str, base: bool = False, **kw) -> Path:
        key = builder.B1_KEY if base else KEY
        if not base:
            kw.setdefault("rewards", self.rw)
            kw.setdefault("lateral_falls", (2, 4, 1))
        return make_harvest(self.tmp / name, key, **kw)

    def read(self, point: Path | None = None, base: Path | None = None) -> dict:
        return readout.read(KEY, point or self.good, base or self.base, ("ang_vel_xy_l2", -0.08))

    def assert_hold(self, r: dict, cls: str) -> None:
        self.assertEqual(r["combined"]["class"], cls, json.dumps(r["combined"], ensure_ascii=False))
        self.assertNotIn(r["combined"]["class"], ("PROMISING_SINGLE_POINT", "TRADE_OFF_POINT"))

    # --- 정상 fixture ---
    def test_r00_complete_fixture_reads_clean(self) -> None:
        r = self.read()
        self.assertEqual(r["state"]["gaps"], [])
        self.assertEqual(r["base_state"]["gaps"], [])
        self.assertEqual(r["comparison"]["label"], "OK", r["comparison"]["problems"])
        self.assertEqual(r["moving_gate"], "MOVING")
        self.assertEqual(r["target"]["class"], "TARGET_IMPROVED")
        self.assertEqual(r["motion_tracking"]["label"], "NONE_WORSE")
        self.assertTrue(all(p["label"] != "MISSING" for p in r["protection"]))
        self.assertEqual(r["combined"]["missing_parts"], [])
        self.assertEqual(r["combined"]["class"], "PROMISING_SINGLE_POINT")
        self.assertIn("자동 선택 없음", r["combined"]["next_point"])

    # --- R1: 필수 지표 결측은 승격하지 않는다 ---
    def test_r01_each_missing_required_file_blocks_promotion(self) -> None:
        for case, f in (("rough_lateral", "steps.csv"), ("stairs_15_down", "steps.csv"),
                        ("push_neg_y", "summary.json"), ("combined_yaw_right", "steps.csv"),
                        ("forward_nominal", "steps.csv")):
            p = self.variant(f"miss_{case}_{f}")
            (p / "evaluation/candidate/cases/seed_202" / case / f).unlink()
            r = self.read(p)
            self.assertNotIn(r["combined"]["class"], ("PROMISING_SINGLE_POINT", "TRADE_OFF_POINT"), f"{case}/{f}")
            self.assertEqual(r["target"]["class"], "TARGET_IMPROVED")  # 부분 관측은 남는다

    def test_r02_missing_motion_or_protection_metric_is_hold_missing(self) -> None:
        # 파일 수는 맞지만 지표가 판독 불가(자세 모호) — 상태 게이트를 지나도 HOLD_MISSING
        p = self.variant("ambiguous_push")
        f = p / "evaluation/candidate/cases/seed_101/push_neg_x/summary.json"
        f.write_text(json.dumps(fall_summary(1, posture_fall_verdict_ambiguous=True, steps=WALK_ROWS, rows=32 * WALK_ROWS)),
                     encoding="utf-8")
        r = self.read(p)
        self.assertEqual(r["state"]["overall"], "COMPLETE")
        self.assert_hold(r, "HOLD_MISSING")
        self.assertIn("push_neg_x_falls", r["combined"]["missing_parts"])
        direct = readout.combined({"overall": "COMPLETE"}, {"overall": "COMPLETE"}, {"label": "OK"}, "MOVING",
                                  {"class": "TARGET_IMPROVED"}, {"label": "MISSING"},
                                  [{"item": "stairs_15_ge2", "label": "MISSING", "worse_seeds": []}])
        self.assertEqual(direct["class"], "HOLD_MISSING")  # §16 R1 의 직접 재현 사례

    # --- R2: B1 유효성·identity·장비 ---
    def test_r03_b1_must_itself_be_a048_complete_and_identified(self) -> None:
        wrong = self.variant("b1_wrong_reward", base=True, rewards=self.rw)
        self.assert_hold(self.read(base=wrong), "HOLD_BASE_INVALID")
        partial = self.variant("b1_partial", base=True, lateral_falls=(5, 8, 3))
        (partial / "RESULT_STATUS.txt").write_text("RESULT_STATE=PARTIAL\nCOLLECTION_STATUS=X\n", encoding="utf-8")
        (partial / "exported/report.html").unlink()
        r = self.read(base=partial)
        self.assert_hold(r, "HOLD_BASE_INVALID")
        self.assertTrue(any(g.startswith("report") for g in r["base_state"]["gaps"]))

    def test_r04_held_fields_missing_on_both_sides_is_not_ok(self) -> None:
        b = self.variant("b1_nocfg", base=True, lateral_falls=(5, 8, 3))
        p = self.variant("pt_nocfg")
        for h in (b, p):
            (h / "meta/run_config.env").write_text("", encoding="utf-8")
        r = self.read(p, b)
        self.assertEqual(r["comparison"]["label"], "MISMATCH")
        self.assertTrue(any("없음 또는 형식 아님" in x for x in r["comparison"]["problems"]))
        # 빈 설정은 B1 자신의 identity(실제 값 ↔ 기대 설정) 연결도 끊으므로 B1 단계에서 먼저 보류된다(§18 R2)
        self.assert_hold(r, "HOLD_BASE_INVALID")

    def test_r05_identity_chain_breaks_are_gaps(self) -> None:
        breaks = {
            "report_other_run": lambda h: (h / "exported/REPORT_STATUS.txt").write_text(
                "REPORT_STATUS=REPORT_ACQUIRED\nSOURCE=/workspace/w/other_key/candidate/exported/report.html\n", encoding="utf-8"),
            "report_hash": lambda h: (h / "exported/report.html").write_text("<html>changed</html>", encoding="utf-8"),
            "policy_mismatch": lambda h: (h / "training/model_best.pt").write_bytes(b"another model"),
            "eval_identity": lambda h: (h / "evaluation/candidate/identity.json").write_text(
                json.dumps({"model_sha256": "0" * 64}), encoding="utf-8"),
            "run_id": lambda h: (h / "RUNNER_STATUS.txt").write_text(
                (h / "RUNNER_STATUS.txt").read_text(encoding="utf-8").replace(KEY, "other_key"), encoding="utf-8"),
        }
        for name, brk in breaks.items():
            p = self.variant(f"id_{name}")
            brk(p)
            r = self.read(p)
            self.assertEqual(r["state"]["overall"], "INVALID_OR_INCOMPLETE", name)
            self.assert_hold(r, "HOLD_INVALID_OR_INCOMPLETE")
            self.assertEqual(r["target"]["class"], "TARGET_IMPROVED", name)  # 부분 관측 보존

    def test_r06_baseline_from_another_device_is_refused(self) -> None:
        other = self.variant("b1_server", base=True, lateral_falls=(5, 8, 3), gpu="NVIDIA GeForce RTX 5080")
        r = self.read(base=other)
        self.assertTrue(any("다른 GPU 모델" in x for x in r["comparison"]["problems"]))
        self.assert_hold(r, "HOLD_COMPARISON_INVALID")

    def test_r07_held_condition_value_mismatch(self) -> None:
        r = self.read(self.variant("seed43", seed_cfg="43"))
        self.assertTrue(any(x.startswith("TRAIN_SEED 다름") for x in r["comparison"]["problems"]))

    # --- R3: RMSE 결측·비유한값은 결측, 측정된 0 은 값 ---
    def test_r08_rmse_missing_nan_inf_propagate_and_zero_is_valid(self) -> None:
        for name, v in (("none", None), ("nan", float("nan")), ("inf", float("inf"))):
            p = self.variant(f"rmse_{name}", lateral_rmse=(0.2, v, 0.2))
            r = self.read(p)
            self.assertEqual(r["motion_tracking"]["label"], "MISSING", name)
            self.assert_hold(r, "HOLD_MISSING")
        self.assertIsNone(readout.fnum(True))
        zero = self.read(self.variant("rmse_zero", lateral_rmse=(0.0, 0.0, 0.0)))
        self.assertEqual(zero["motion_tracking"]["label"], "NONE_WORSE")
        self.assertEqual(zero["motion_tracking"]["seeds"]["101"]["point"]["tracking_xy_rmse"], 0.0)

    def test_r09_motion_rules(self) -> None:
        slow = self.read(self.variant("slow", lateral_vy=(0.15, 0.15, 0.15)))
        self.assertEqual(slow["combined"]["class"], "FALLS_DOWN_MOTION_TRACKING_LOSS")
        over = self.read(self.variant("over", lateral_vy=(0.25, 0.25, 0.40)))
        self.assertEqual(over["motion_tracking"]["worse_seeds"], ["303"])
        self.assertEqual(over["motion_tracking"]["overspeed_seeds"], ["303"])
        self.assertEqual(over["combined"]["class"], "FALLS_DOWN_MOTION_TRACKING_LOSS")

    # --- R4: 같은 ≥2단 수, 다른 도달 뒤 상태 ---
    def test_r10_same_ge2_different_post_reach_state(self) -> None:
        r = self.read(self.variant("stall", stairs15_stall=True))
        item = next(p for p in r["protection"] if p["item"] == "stairs_15_ge2")
        for s in readout.SEEDS:
            v = item["seeds"][s]
            self.assertEqual(v["b1"], v["point"])  # ≥2단 수는 같다
            self.assertEqual(v["post_reach"]["b1"]["reached_ge2"], v["b1"])
            self.assertEqual(v["post_reach"]["b1"]["stalled_after_reach"], 0)
            self.assertEqual(v["post_reach"]["point"]["stalled_after_reach"], v["point"])
            self.assertEqual(v["post_reach"]["point"]["post_channel_none"], v["point"])
        self.assertEqual(item["label"], "COMMON_LOSS_NOT_OBSERVED")  # 새 문턱 없음 — 상태는 별도 필드

    # --- 기타 정정 ---
    def test_r11_floor_seed_and_partial_protection_loss(self) -> None:
        b = self.variant("b1_floor", base=True, lateral_falls=(0, 8, 3))
        r = self.read(self.variant("floor", lateral_falls=(0, 4, 1)), b)
        self.assertEqual(r["target"]["class"], "MIXED")
        self.assertIn("101", r["target"]["floor_note"])
        r2 = self.read(self.variant("push2", push_falls=(9, 9, 1)))
        item = next(p for p in r2["protection"] if p["item"] == "push_pos_x_falls")
        self.assertEqual(item["label"], "COMMON_LOSS_NOT_OBSERVED")
        self.assertIn("push_pos_x_falls", r2["combined"]["partial_loss_items"])
        r3 = self.read(self.variant("push3", push_falls=(9, 9, 9)))
        self.assertEqual(r3["combined"]["class"], "TRADE_OFF_POINT")

    def test_r12_sentinel_outside_is_label_only(self) -> None:
        r = self.read(self.variant("sent", sentinel_lateral=27))
        self.assertEqual(r["sentinel"]["label"], "EVAL_LAYER_DIFFERS")
        self.assertEqual(r["combined"]["class"], "PROMISING_SINGLE_POINT")

    def test_r13_reward_snapshot_and_stationary(self) -> None:
        r = self.read(self.variant("two_terms", rewards=dict(self.rw, track_lin_vel_xy_exp=1.4)))
        self.assertTrue(any(g.startswith("reward snapshot") for g in r["state"]["gaps"]))
        st = self.read(self.variant("stationary", forward_speed=0.03))
        self.assertEqual(st["combined"]["class"], "STATIONARY")


class ReadoutR18(unittest.TestCase):
    """§18 잔여 결함 회귀: 실제·기대 identity 연결, 로봇 coverage, 손상 CSV, 도달 후 시간창."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = make_harvest(cls.tmp / "b1", builder.B1_KEY, lateral_falls=(5, 8, 3))
        cls.rw = dict(readout.A048_REWARDS, ang_vel_xy_l2=-0.08)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def point(self, name: str, **kw) -> Path:
        kw.setdefault("rewards", self.rw)
        kw.setdefault("lateral_falls", (2, 4, 1))
        return make_harvest(self.tmp / name, KEY, **kw)

    def read(self, p: Path) -> dict:
        return readout.read(KEY, p, self.base, ("ang_vel_xy_l2", -0.08))

    def not_promoted(self, r: dict) -> None:
        self.assertNotIn(r["combined"]["class"], ("PROMISING_SINGLE_POINT", "TRADE_OFF_POINT"),
                         json.dumps(r["combined"], ensure_ascii=False))

    # --- R2: 실제 evaluator·registry·seed 가 기대 설정·meta 와 이어져야 한다 ---
    def test_s01_actual_evaluator_or_registry_unlinked_from_expected(self) -> None:
        other = hashlib.sha256(b"another evaluator").hexdigest()
        for runner_key, id_key, label in (("EVALUATOR_SHA", "evaluator_sha256", "evaluator"),
                                          ("REGISTRY_SHA", "registry_sha256", "registry")):
            p = self.point(f"unlinked_{label}")
            rs = p / "RUNNER_STATUS.txt"
            old = readout.env_file(rs)[runner_key]
            rs.write_text(rs.read_text(encoding="utf-8").replace(old, other), encoding="utf-8")
            idj = json.loads((p / "evaluation/candidate/identity.json").read_text(encoding="utf-8"))
            idj[id_key] = other  # 실제 값 두 곳은 서로 같다 — 그래도 기대 값과 이어지지 않는다
            (p / "evaluation/candidate/identity.json").write_text(json.dumps(idj), encoding="utf-8")
            r = self.read(p)
            self.assertTrue(any(f"실제 {label} 해시가 run_config" in g for g in r["state"]["gaps"]), label)
            self.assertTrue(any(f"실제 {label.upper()}_SHA 다름" in x for x in r["comparison"]["problems"]), label)
            self.not_promoted(r)

    def test_s02_actual_seed_unlinked_from_config(self) -> None:
        p = self.point("seed_unlinked")
        rs = p / "RUNNER_STATUS.txt"
        rs.write_text(rs.read_text(encoding="utf-8").replace("TRAIN_SEED=42", "TRAIN_SEED=43"), encoding="utf-8")
        r = self.read(p)
        self.assertTrue(any("실제 학습 seed(43)" in g for g in r["state"]["gaps"]))
        self.not_promoted(r)

    # --- R1: coverage — 일부 로봇만 남은 파일은 관측 완료가 아니다 ---
    def test_s03_one_robot_left_is_not_a_full_observation(self) -> None:
        p = self.point("one_robot")
        f = p / "evaluation/candidate/cases/seed_101/rough_lateral/steps.csv"
        lines = f.read_text(encoding="utf-8").splitlines()
        f.write_text("\n".join([lines[0]] + [l for l in lines[1:] if l.split(",")[2] == "0"]) + "\n", encoding="utf-8")
        r = self.read(p)
        self.assertTrue(any("env coverage 1/32" in g for g in r["state"]["gaps"]), r["state"]["gaps"])
        self.assertEqual(r["motion_tracking"]["label"], "MISSING")
        self.not_promoted(r)

    def test_s04_dropped_rows_differ_from_early_termination(self) -> None:
        p = self.point("short_env")
        f = p / "evaluation/candidate/cases/seed_202/rough_lateral/steps.csv"
        lines = f.read_text(encoding="utf-8").splitlines()
        keep = [lines[0]] + [l for l in lines[1:] if not (l.split(",")[2] == "5" and int(l.split(",")[0]) > 60)]
        f.write_text("\n".join(keep) + "\n", encoding="utf-8")
        r = self.read(p)
        self.assertTrue(any("행 수가 steps" in g for g in r["state"]["gaps"]), r["state"]["gaps"])
        self.not_promoted(r)
        early = self.read(self.point("early_term", lateral_early_term=7))  # 종료 기록 뒤 행이 이어짐 = 정상
        self.assertEqual(early["state"]["gaps"], [])
        self.assertEqual(early["combined"]["class"], "PROMISING_SINGLE_POINT")

    # --- R1: 손상 CSV 는 구체적 gap, 다른 관측은 남는다 ---
    def test_s05_corrupt_stairs_csv_keeps_partial_observations(self) -> None:
        p = self.point("corrupt")
        (p / "evaluation/candidate/cases/seed_101/stairs_15_down/steps.csv").write_text("env_id,root_z\n0,bad\n",
                                                                                         encoding="utf-8")
        r = self.read(p)  # 예외 없이 반환해야 한다
        self.assertTrue(any("필수 열 없음" in g for g in r["state"]["gaps"]), r["state"]["gaps"])
        item = next(x for x in r["protection"] if x["item"] == "stairs_15_ge2")
        self.assertEqual(item["label"], "MISSING")
        self.assertEqual(r["target"]["class"], "TARGET_IMPROVED")
        self.not_promoted(r)
        p2 = self.point("corrupt_value")
        f = p2 / "evaluation/candidate/cases/seed_303/stairs_10_down/steps.csv"
        lines = f.read_text(encoding="utf-8").splitlines()
        cells = lines[5].split(",")
        cells[14] = "bad"  # root_z
        lines[5] = ",".join(cells)
        f.write_text("\n".join(lines) + "\n", encoding="utf-8")
        r2 = self.read(p2)
        self.assertTrue(any("root_z='bad' 수 아님" in g for g in r2["state"]["gaps"]), r2["state"]["gaps"])

    # --- R4: post_reach 는 첫 도달부터 그 episode 끝까지만 ---
    def test_s06_post_reach_window_separates_before_after_and_reset(self) -> None:
        events = {0: "tilt_before", 1: "tilt_after", 2: "term_after", 3: "trunc_after"}
        r = self.read(self.point("windows", stairs15=(10, 10, 10), stairs15_events=events))
        item = next(x for x in r["protection"] if x["item"] == "stairs_15_ge2")
        post = item["seeds"]["101"]["post_reach"]["point"]
        self.assertEqual(post["reached_ge2"], 10)
        self.assertEqual(post["post_channel_tilt_or_both"], 1)   # 도달 뒤 기울기만
        self.assertEqual(post["post_channel_terminated"], 1)     # 도달 뒤 종료 사건은 잃지 않는다
        self.assertEqual(post["post_channel_none"], 8)           # 도달 전 사건·reset 뒤 사건은 제외
        self.assertEqual(post["run_channel_tilt_or_both"], 3)    # 전체 run 채널은 별도 이름으로 보존
        self.assertEqual(post["run_channel_terminated"], 1)
        self.assertEqual(post["run_channel_none"], 6)


if __name__ == "__main__":
    unittest.main()
