"""G-A047 패키지 계약 — `flat_orientation_l2` 0.0 -> -0.5, G3 험지 생존 탐색 (2026-09-26).

계획 `workspace/training/quadruped/upload/plan/GO2_G_A047_PLAN_20260926.md`.  G-A044 의 실행 계약(전수 69 ·
단일 단계)을 그대로 쓰고, 판정은 fact_rules_v1 과 보호 전용 screening 이다.  이 계약이 지키는 것:

  * 문턱은 G-A044 와 **글자 그대로** 같다 — 다른 것은 계획 §4 가 선언한 곳(계획 screening 을 보호 전용 판
    `g3_guard_push4_v1` 로 교체)과 그 결과로 바뀐 서술 칸뿐이다.  문턱을 조용히 옮기면 여기서 떨어진다.
  * 보호 전용 판은 `post_a043_push4_v1` 의 보호 묶음(여덟 case, 밀침 네 방향 각각)을 한 글자도 바꾸지 않고
    계단 개선·정체 감소 두 묶음만 뺀다(v2 — v1 은 판 전체를 빼 밀침 방향별 보호가 기록으로만 남았다).
  * 바뀌는 보상은 한 줄이고, 러너는 v10 팔과 같은 저장소 러너다.
  * 발행물은 빌더가 다시 만든 바이트와 같다.
  * 안내문의 판독 명령이 실제 CLI 에서 돌고, 돌리는 동안 `reports/` 를 쓰지 않는다(결함 C-36).
  * 판정기가 이 사양으로 끝까지 도는지 — 보호 전용 screening 이 합쳐지는지 — 를
    G-A044 수확물을 대역으로 써서 본다(판정 값 자체는 의미가 없다).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as reward  # noqa: E402
import build_go2_full_collection_release as release  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402

WORK_ID = "G-A047"
SPEC = reward.load(WORK_ID)
A044 = reward.load("G-A044")
HISTORY = reward.output_path(SPEC)
CURRENT = GO2 / "upload" / WORK_ID / "current"
# 계획 §4 가 선언한 차이.  이 밖의 preregistered 칸은 G-A044 와 같아야 한다.
DECLARED = {"plan_screening", "source", "threshold_basis", "target_group_roles", "required_records",
            "mechanism_readout"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reports_bytes() -> dict[str, str]:
    base = GO2 / "reports"
    return {str(p.relative_to(base)): sha(p.read_bytes()) for p in sorted(base.rglob("*")) if p.is_file()}


class SpecTest(unittest.TestCase):
    def test_1_the_spec_validates_as_a_full_collection_reward_arm(self) -> None:
        release.validate(SPEC)
        self.assertEqual(SPEC["change_class"], "reward_weight")
        self.assertEqual(SPEC["training"]["seed"], 42)
        self.assertEqual(base_data.spec_problems(SPEC), [])

    def test_2_thresholds_are_g_a044s_unchanged(self) -> None:
        mine, theirs = SPEC["preregistered"], A044["preregistered"]
        self.assertEqual(set(theirs) ^ set(mine), set())
        for key in sorted(set(theirs) - DECLARED):
            with self.subTest(key=key):
                self.assertEqual(mine[key], theirs[key])
        self.assertEqual(SPEC["evaluation"], A044["evaluation"])

    def test_3_the_one_departure_is_declared(self) -> None:
        version = SPEC["preregistered"]["plan_screening"]["version"]
        self.assertEqual(version, "g3_guard_push4_v1")
        self.assertEqual(A044["preregistered"]["plan_screening"]["version"], "post_a043_push4_v1")
        self.assertIn("post_a043_push4_v1", SPEC["criteria_changes"])
        self.assertIn("section 4", SPEC["criteria_changes"])
        plan = (ROOT / SPEC["plan"]).read_text(encoding="utf-8")
        self.assertIn("계획 screening은 보호 전용 판 `g3_guard_push4_v1`로 **바꾼다.**", plan)

    def test_3b_the_guard_only_edition_keeps_the_whole_guard_block(self) -> None:
        """개선 두 묶음만 빠지고 보호 묶음은 post_a043_push4_v1 과 같은 case·같은 검사다."""
        version = SPEC["preregistered"]["plan_screening"]["version"]
        self.assertEqual(screening.cases_for(version), screening.cases_for("post_a043_push4_v1"))
        self.assertFalse(screening.improvement_required(version))
        self.assertTrue(screening.improvement_required("post_a043_push4_v1"))
        rows = lambda falls: {(case, seed): {"missing": [], "fingerprint": None, "progress_m": 1.0,
                                             "ge1": 5, "ge2": 3, "stall_share": 0.1, "survival": 0.9,
                                             "tracking": 0.8, "posture_falls": falls}
                              for case in screening.cases_for(version) for seed in screening.SEEDS}
        base = rows(2)
        cand = rows(2)
        for seed in screening.SEEDS:
            cand[("push_neg_y", seed)] = {**cand[("push_neg_y", seed)], "posture_falls": 3}
        guard_only = screening.judge(base, cand, screening.cases_for(version), improvement=False)
        full = screening.judge(base, cand, screening.cases_for(version))
        self.assertEqual({c["group"] for c in guard_only["checks"]}, {"guard"})
        self.assertEqual([c for c in full["checks"] if c["group"] == "guard"], guard_only["checks"])
        self.assertEqual(guard_only["verdict"], screening.FAIL)
        self.assertEqual(guard_only["failed"], ["push_neg_y pooled posture falls <= baseline"])

    def test_4_the_run_is_a_g3_question_not_a_stairs_or_combination_question(self) -> None:
        roles = SPEC["preregistered"]["target_group_roles"]
        self.assertIn("GUARD", roles["stairs"])
        self.assertIn("the target", roles["rough"])
        self.assertIn("not a stairs candidate", SPEC["why"][0])
        self.assertIn("lin_vel_z -1.5", SPEC["why"][0])
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIs(SPEC["inference"]["exploratory"], True)

    def test_5_a_partial_collection_is_read_first_and_not_as_a_refutation(self) -> None:
        readout = SPEC["preregistered"]["mechanism_readout"]
        self.assertTrue(readout.startswith("Read in order (plan section 5): (1) partial collection"))
        self.assertIn("not a performance refutation", readout)
        self.assertIn("consistency of the reward effect unestablished", readout)
        self.assertIn("A partial collection is INCONCLUSIVE, not a refutation", SPEC["inference"]["falsified_if"])


class PackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not HISTORY.is_file():
            raise unittest.SkipTest("아직 빌드하지 않았다")
        cls.data = HISTORY.read_bytes()
        cls.zip = zipfile.ZipFile(HISTORY)
        cls.prefix = length.prefix(SPEC).as_posix() + "/"

    def member(self, name: str) -> bytes:
        return self.zip.read(self.prefix + name)

    def test_6_the_published_bytes_are_what_the_builder_makes(self) -> None:
        self.assertEqual(reward.build_zip(SPEC), self.data)
        self.assertIsNone(self.zip.testzip())

    def test_7_one_reward_line_moves(self) -> None:
        cand = self.member("candidate/quadruped_rewards.py").decode("utf-8").splitlines()
        ref = self.member("reference/baseline_quadruped_rewards.py").decode("utf-8").splitlines()
        self.assertEqual(len(cand), len(ref))
        moved = [(a, b) for a, b in zip(ref, cand) if a != b]
        self.assertEqual(len(moved), 1)
        self.assertIn('"flat_orientation_l2":  0.0,', moved[0][0])
        self.assertIn('"flat_orientation_l2":  -0.5,', moved[0][1])

    def test_8_the_runner_is_the_repository_runner_and_the_config_pins_the_full_run(self) -> None:
        runner = self.member(SPEC["runner"])
        self.assertEqual(runner, (GO2 / SPEC["runner"]).read_bytes())
        self.assertNotIn(b"\r", runner)
        done = subprocess.run(["bash", "-n"], input=runner, capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = self.member("run_config.env").decode("utf-8")
        for line in ("GO2_STAGE=full\n", "COLLECT_REQUIRED_ON_STATIONARY=1\n", "SINGLE_CHANGE_TO=-0.5\n",
                     "TRAIN_SEED=42\n", "BASELINE_VIDEOS=()\n"):
            self.assertIn(line, config)


class GuideTest(unittest.TestCase):
    def test_9_the_guide_commands_run_and_write_nothing_tracked(self) -> None:
        if not CURRENT.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (CURRENT / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        joined = guide.replace("\\\n", " ")
        commands = [line.strip() for line in joined.splitlines() if line.strip().startswith("python -B tools/")]
        self.assertEqual(len(commands), 2, commands)
        self.assertIn("go2_screening_gate.py", commands[1])
        self.assertIn("--rule-version g3_guard_push4_v1", commands[1])
        before = reports_bytes()
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "no_harvest")
            for command in commands:
                with self.subTest(command=command[:70]):
                    argv = [missing if part.startswith("workspace/_keep/") else part for part in command.split()[1:]]
                    if "--out" not in argv:
                        argv += ["--out", str(Path(tmp) / "out")]
                    done = subprocess.run([sys.executable, *argv], cwd=str(ROOT), env=env, capture_output=True,
                                          text=True, encoding="utf-8", timeout=300)
                    self.assertNotEqual(done.returncode, 2, done.stderr[-400:])
        self.assertEqual(reports_bytes(), before, "a wiring check wrote into tracked evidence")


class VerifierPathTest(unittest.TestCase):
    """느리다(수 분).  G-A044 수확물을 대역으로 판정기의 끝까지 간다 — 회차가 다르다는 식별 결함 넷만 뺀다."""

    STAND_IN = ROOT / "workspace/_keep/go2_g_a044_a033_lin_vel_z_m175"
    EXPECTED = ("work_id=", "train_single_change=", "env_reward_lin_vel_z_l2=", "env_reward_flat_orientation_l2=")

    def test_10_the_verifier_reaches_a_verdict_with_the_guard_only_screening(self) -> None:
        if not self.STAND_IN.is_dir():
            self.skipTest("대역 수확물(G-A044)이 이 PC 에 없다")
        original = verifier.check_artifacts
        dropped: list[str] = []

        def stand_in(keep, spec):
            faults, facts = original(keep, spec)
            dropped.extend(f for f in faults if f.startswith(self.EXPECTED))
            return [f for f in faults if not f.startswith(self.EXPECTED)], facts

        verifier.check_artifacts = stand_in
        try:
            report = verifier.verify(self.STAND_IN, ROOT / SPEC["baseline"]["stored_arm"], SPEC)
        finally:
            verifier.check_artifacts = original
        self.assertEqual(len(dropped), 4, dropped)
        self.assertEqual(report["combined_verdict"]["artifact"], "ARTIFACT_VERIFIED")
        self.assertIn(report["combined_verdict"]["plan_screening"],
                      (screening.PASS, screening.FAIL, screening.INCONCLUSIVE))
        self.assertEqual({c["group"] for c in report["plan_screening"]["checks"]}, {"guard"})
        self.assertIn("g3_guard_push4_v1", report["plan_screening"]["rule"])
        self.assertIn(report["verdict"], ("PASS", "FAIL"))


if __name__ == "__main__":
    unittest.main()
