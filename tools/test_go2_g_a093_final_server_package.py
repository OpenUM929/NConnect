"""Contract tests for G-A093 (final official-server training, two reward editions).

Static tests check both editions against the G-A079 v3 base.  End-to-end tests reuse the G-A079 v3
sandbox harness (fake isaaclab.sh, scripted train.py/play.py, stub torch/cv2) on the a092 edition:
an uninterrupted run with one crashed case and one crashed video (both must be retried), and a
non-finite collapse (the checkpoint before it is evaluated).

    python tools/test_go2_g_a093_final_server_package.py
"""
from __future__ import annotations

import functools
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_g_a093_final_server_package as builder  # noqa: E402
import test_go2_g_a079_v3 as base_test  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

EDITION = "a092"
ED = builder.EDITIONS[EDITION]

# Crash the first attempt of one case and of one video, as Isaac Sim did on G-A079 v3 case 61/69.
CRASH_ONCE = r'''import os, sys
from pathlib import Path
_fake = Path(os.environ["FAKE_DIR"])
if "--video" in sys.argv:
    _m = _fake / "VIDEO_CRASHED"
    if not _m.exists():
        _m.write_text("1")
        print("[Fatal] fake video crash", flush=True)
        sys.exit(1)
elif os.environ.get("NCRC_EVAL_CASE") == "stairs_10_up" and os.environ.get("NCRC_EVAL_SEED") == "303":
    _m = _fake / "CASE_CRASHED"
    if not _m.exists():
        _m.write_text("1")
        print("[Fatal] fake case crash", flush=True)
        sys.exit(1)
'''


@functools.lru_cache(maxsize=None)
def built(edition: str = EDITION):
    return builder.build(edition)


def env_with_rewards(env_text: str, rewards: dict[str, float]) -> str:
    for name, value in rewards.items():
        env_text, count = re.subn(r"(\n  " + re.escape(name) + r":\n(?:    .*\n)*?    weight: )-?[0-9.]+",
                                  lambda m: m.group(1) + repr(value), env_text, count=1)
        assert count == 1, name
    return env_text


class StaticTests(unittest.TestCase):
    def test_both_editions_validate(self):
        for edition in builder.EDITIONS:
            files, base = builder.build(edition)
            builder.validate(edition, files, base)

    def test_reward_values(self):
        a083 = reward_dict(built("a083")[0]["runs/final_a083/candidate/quadruped_rewards.py"].decode())
        a092 = reward_dict(built("a092")[0]["runs/final_a092_feet0p05/candidate/quadruped_rewards.py"].decode())
        self.assertEqual(a083, builder.A083)
        self.assertEqual(a083["track_ang_vel_z_exp"], 0.75)
        self.assertEqual({k for k in a083 if a083[k] != a092[k]}, {"feet_air_time"})
        self.assertEqual(a092["feet_air_time"], 0.05)

    def test_deployed_files_match_g_a079_v3(self):
        v3_files, _ = builder.v3.build()
        files = built()[0]
        for name in ("train.py", "play.py", "go2_task/agent_cfg.py", "go2_task/env_cfg.py", "go2_task/_finalize.py"):
            self.assertEqual(files["shared/candidate/" + name], v3_files["shared/candidate/" + name], name)

    def test_config(self):
        cfg = built()[0][f"runs/{ED['key']}/run_config.env"].decode()
        for line in ("MAX_ITERATIONS=5000", "EVAL_CHECKPOINT_ITER=4900", "MAX_RECOVERIES=0", "TRAIN_SEED=42"):
            self.assertIn(line + "\n", cfg)
        self.assertIn(f"run_point.sh --only {ED['key']}", built()[0]["README.txt"].decode())


class EndToEnd(base_test.EndToEnd):
    def setUp(self):
        base_test.built = lambda: built()
        base_test.KEY, base_test.ARM, base_test.SLUG = ED["key"], f"runs/{ED['key']}/", ED["slug"]
        base_test.builder = type("B", (), {"DEPLOYED": tuple(
            n.replace(builder.v3.ARM, f"runs/{ED['key']}/") for n in builder.v3.DEPLOYED), "RESULT": ED["result"]})

    def sandbox(self, name: str) -> dict:
        box = base_test.EndToEnd.sandbox(self, "a093_" + name)
        env_text = built()[0]["shared/baseline/exported/env.yaml"].decode()
        (box["fake"] / "env.yaml").write_text(env_with_rewards(env_text, ED["rewards"]), newline="\n")
        play = box["fake"] / "fake_play.py"
        play.write_text(CRASH_ONCE + play.read_text())
        box["env"]["GO2_EVAL_RETRY_SLEEP_S"] = "0"
        return box

    def test_uninterrupted_run_evaluates_4900(self):
        box = self.sandbox("ok")
        box["env"].update({"FAKE_PLAN": "ok", "FAKE_TRAIN_HOLD_S": "90"})
        r = self.run_point(box)
        self.assertEqual(r.returncode, 0, r.stdout[-4000:])
        self.result(box, 4900)
        retries = (box["keep"] / "logs/EVAL_RETRIES.txt").read_text().splitlines()
        self.assertEqual(len(retries), 2, retries)
        self.assertIn("stairs_10_up seed=303 attempt 1", retries[0] + retries[1])
        self.assertTrue(any(line.startswith("[RETRY] video") for line in retries))
        with zipfile.ZipFile(box["result"]) as archive:
            names = set(archive.namelist())
            prefix = ED["slug"] + "/"
            self.assertIn(prefix + "evaluation/candidate/policy.pt", names)
            self.assertIn(prefix + "training/env.yaml", names)
            check = archive.read(prefix + "training/ENV_REWARD_CHECK.txt").decode()
            self.assertIn("feet_air_time", check)
        self.assertIn("--max_iterations 5000", self.calls(box)[0])
        self.finish(box)

    def test_collapse_is_not_continued_and_checkpoint_before_runup_is_evaluated(self):
        box = self.sandbox("collapse")
        box["env"].update({"FAKE_PLAN": "nan@2584", "FAKE_TRAIN_HOLD_S": "60"})
        r = self.run_point(box)
        self.assertEqual(r.returncode, 0, r.stdout[-4000:])
        self.assertEqual(len(self.calls(box)), 1)
        out = self.result(box, 2500)
        self.assertIn("EVAL_CHECKPOINT_ITER=2500\n", out["training/EVAL_CHECKPOINT_OVERRIDE.txt"])
        self.assertIn("LAST_SEGMENT_NONFINITE_ITER=2584\n", out["training/TRAIN_STATUS.txt"])
        self.finish(box)

    # Covered by the G-A079 v3 suite on the same runner; not repeated here.
    test_killed_after_collapse_is_not_continued = None
    test_killed_then_continued_on_new_server = None


if __name__ == "__main__":
    unittest.main()
