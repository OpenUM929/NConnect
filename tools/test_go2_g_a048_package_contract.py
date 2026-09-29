"""G-A048 패키지 계약 — `lin_vel_z_l2` -2.0 -> -1.25, U2 미해결 분기의 탐색 회차 (2026-09-26).

계획 `workspace/training/quadruped/upload/plan/GO2_A043_YAW_RIGHT_AND_NEXT_20260926.md` §4.  G-A044 의 실행 계약
(전수 69 · 단일 단계)과 채택 판정(fact_rules_v1 + post_a043_push4_v1)을 그대로 쓰고, 채택과 **별개인** 가설 판정
세 지표를 결과 전에 고정한다.  이 계약이 지키는 것:

  * 채택 문턱은 G-A044 와 **글자 그대로** 같다 — 다른 칸은 서술 셋(source·threshold_basis·mechanism_readout)과
    새 `hypothesis` 블록뿐이다.  문턱을 조용히 옮기면 여기서 떨어진다.
  * 가설 문턱은 계획서 §4 의 숫자와 같고, 판독기는 문턱을 사양에서만 읽는다 — 경계의 바로 안쪽은 불충분이다.
  * 판독기는 저장된 세 관측점(G-A033·G-A044·G-A043)에서 기존 표의 수를 그대로 재현한다.
  * 바뀌는 보상은 한 줄이고, 러너는 저장소 러너이며, 발행물은 빌더가 다시 만든 바이트와 같다.
  * 안내문의 판독 명령 셋이 실제 CLI 에서 돌고, 돌리는 동안 `reports/` 를 쓰지 않는다(결함 C-36).
  * 채택 판정기가 이 사양으로 끝까지 도는지를 G-A044 수확물을 대역으로 본다(판정 값 자체는 의미가 없다).
"""
from __future__ import annotations

import hashlib
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
import go2_dial_hypothesis as hypothesis  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402

WORK_ID = "G-A048"
SPEC = reward.load(WORK_ID)
A044 = reward.load("G-A044")
HISTORY = reward.output_path(SPEC)
CURRENT = GO2 / "upload" / WORK_ID / "current"
# 서술 칸 셋과 새 가설 블록.  이 밖의 preregistered 칸은 G-A044 와 같아야 한다.
DECLARED = {"source", "threshold_basis", "mechanism_readout", "hypothesis"}
INDICATORS = SPEC["preregistered"]["hypothesis"]["indicators"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reports_bytes() -> dict[str, str]:
    base = GO2 / "reports"
    return {str(p.relative_to(base)): sha(p.read_bytes()) for p in sorted(base.rglob("*")) if p.is_file()}


class SpecTest(unittest.TestCase):
    def test_1_the_spec_validates_as_a_full_collection_reward_arm(self) -> None:
        release.validate(SPEC)
        self.assertEqual(SPEC["change_class"], "reward_weight")
        self.assertEqual(SPEC["single_change"], {**A044["single_change"], "to": -1.25})
        self.assertEqual(SPEC["training"], A044["training"])
        self.assertEqual(base_data.spec_problems(SPEC), [])
        self.assertEqual(SPEC["base_data"]["terms"]["lin_vel_z_l2"]["status"], "OUT_OF_RANGE")
        self.assertEqual(SPEC["base_data"]["terms"]["lin_vel_z_l2"]["walking_values"], [-2.0, -1.75, -1.5])

    def test_2_adoption_thresholds_are_g_a044s_unchanged(self) -> None:
        mine, theirs = SPEC["preregistered"], A044["preregistered"]
        self.assertEqual(set(mine) - set(theirs), {"hypothesis"})
        self.assertEqual(set(theirs) - set(mine), set())
        for key in sorted(set(theirs) - DECLARED):
            with self.subTest(key=key):
                self.assertEqual(mine[key], theirs[key])
        self.assertEqual(mine["plan_screening"]["version"], "post_a043_push4_v1")
        self.assertEqual(SPEC["evaluation"], A044["evaluation"])
        self.assertEqual(SPEC["collection"]["mode"], "full_69_single_stage")

    def test_3_hypothesis_thresholds_are_the_plans_numbers(self) -> None:
        block = SPEC["preregistered"]["hypothesis"]
        self.assertIs(block["separate_from_adoption"], True)
        self.assertEqual(block["reader"], "tools/go2_dial_hypothesis.py")
        stairs, rough, yaw = (INDICATORS[k] for k in ("stairs_15_ge2", "rough_lateral_posture_falls",
                                                      "yaw_right_posture_cost"))
        self.assertEqual((stairs["supported_if_at_least"], stairs["not_supported_if_at_most"]), (50, 10))
        self.assertEqual((rough["supported_if_at_most"], rough["not_supported_if_at_least"]), (41, 59))
        self.assertEqual((yaw["present_if_seeds_at_least"], yaw["absent_if_seeds_at_most"]), (2, 0))
        plan = (ROOT / SPEC["plan"]).read_text(encoding="utf-8")
        for text in ("50/96 이상이면 지지, 10/96 이하면 미지지", "41 이하면 지지, 59 이상이면 미지지",
                     "두 seed 이상에서 0보다 크면", "반증을 피했다는 것은 성공이 아니다"):
            with self.subTest(text=text):
                self.assertIn(text, plan)
        self.assertIn("operational criterion, not a statistical or official one", rough["basis"])

    def test_4_the_reader_takes_boundaries_from_the_spec_and_edges_are_insufficient(self) -> None:
        source = (ROOT / "tools/go2_dial_hypothesis.py").read_text(encoding="utf-8")
        for number in ("50", "41", "59"):
            self.assertNotRegex(source, rf"(?<![\w.]){number}(?![\w.])", f"threshold {number} hard-coded")
        seeds = lambda values: dict(zip(("101", "202", "303"), values))
        cases = [
            ("stairs_15_ge2", (17, 17, 16), "SUPPORTED"), ("stairs_15_ge2", (17, 17, 15), "INSUFFICIENT"),
            ("stairs_15_ge2", (4, 4, 3), "INSUFFICIENT"), ("stairs_15_ge2", (4, 3, 3), "NOT_SUPPORTED"),
            ("rough_lateral_posture_falls", (14, 14, 13), "SUPPORTED"),
            ("rough_lateral_posture_falls", (14, 14, 14), "INSUFFICIENT"),
            ("rough_lateral_posture_falls", (20, 20, 18), "INSUFFICIENT"),
            ("rough_lateral_posture_falls", (20, 20, 19), "NOT_SUPPORTED"),
            ("yaw_right_posture_cost", (1, 0, 1), "PRESENT"), ("yaw_right_posture_cost", (0, 0, 2), "INSUFFICIENT"),
            ("yaw_right_posture_cost", (0, 0, 0), "ABSENT"), ("yaw_right_posture_cost", (0, None, 0), "MISSING"),
        ]
        for name, values, want in cases:
            with self.subTest(name=name, values=values):
                self.assertEqual(hypothesis.judge(INDICATORS[name], seeds(values))[0], want)

    def test_5_the_reader_reproduces_the_three_measured_points(self) -> None:
        rows = hypothesis.stored_arms(SPEC)
        got = {(r[0], r[2]): (r[3], r[5]) for r in rows[1:]}
        if not got or any(v[1] == "MISSING" for v in got.values()):
            self.skipTest("저장된 수확물이 이 PC 에 없다")
        # reports/evidence/go2_seed_pair_20260924/DIAL_THREE_POINTS.csv · go2_a043_yaw_right_20260926/YAW_SUMMARY.csv
        self.assertEqual(got[("G-A033", "stairs_15_ge2")], ("0/0/0", "NOT_SUPPORTED"))
        self.assertEqual(got[("G-A033", "rough_lateral_posture_falls")], ("20/20/19", "NOT_SUPPORTED"))
        self.assertEqual(got[("G-A044", "rough_lateral_posture_falls")], ("25/27/28", "NOT_SUPPORTED"))
        self.assertEqual(got[("G-A043", "stairs_15_ge2")], ("25/23/29", "SUPPORTED"))
        self.assertEqual(got[("G-A043", "rough_lateral_posture_falls")], ("8/11/5", "SUPPORTED"))
        self.assertEqual(got[("G-A043", "yaw_right_posture_cost")], ("9/9/11", "PRESENT"))
        self.assertEqual(got[("G-A044", "yaw_right_posture_cost")], ("0/0/0", "ABSENT"))

    def test_5b_the_reader_names_no_verdict_on_an_unverified_or_short_harvest(self) -> None:
        """2026-09-26 외부 검토: 가설 판독기는 무결성 검증기가 아니다.  채택 검증기가 같은 회차의
        ARTIFACT_VERIFIED 로 남긴 수확물이 아니면 판정 이름을 내지 않고, 로봇 수가 모자란 case 는 MISSING 이다."""
        import json as _json
        with tempfile.TemporaryDirectory() as tmp:
            harvest = Path(tmp)
            self.assertFalse(hypothesis.harvest_check(SPEC, harvest)[0])
            record = {"work_id": "G-A048", "combined_verdict": {"artifact": "ARTIFACT_VERIFIED"}, "artifact_faults": []}
            for change, ok in (({}, True), ({"work_id": "G-A044"}, False), ({"artifact_faults": ["x"]}, False),
                               ({"combined_verdict": {"artifact": "ARTIFACT_FAULT"}}, False)):
                (harvest / "harvest_verification.json").write_text(_json.dumps({**record, **change}), encoding="utf-8")
                with self.subTest(change=change):
                    self.assertEqual(hypothesis.harvest_check(SPEC, harvest)[0], ok)
            result = hypothesis.read(SPEC, harvest / "none")
            self.assertEqual({i["verdict"] for i in result["indicators"].values()}, {hypothesis.UNVERIFIED})
            summary = harvest / "summary.json"
            base = {"posture_measured": True, "posture_fall_verdict_ambiguous": False,
                    "posture_fall_env_count_optimistic": 3, "posture_fall_env_count_pessimistic": 3}
            summary.write_text(_json.dumps({**base, "posture_envs_observed": 32}), encoding="utf-8")
            self.assertEqual(hypothesis.posture_falls(summary, 32), 3)
            summary.write_text(_json.dumps({**base, "posture_envs_observed": 31}), encoding="utf-8")
            self.assertIsNone(hypothesis.posture_falls(summary, 32))

    def test_6_it_is_an_exploratory_range_extension_not_a_recommendation(self) -> None:
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        self.assertIn("Not a promise of a higher score", SPEC["why"][0])
        self.assertIn("not proven more informative", SPEC["value_derivation"]["rule"])
        self.assertIn("does not make G-A043's -1.5 result luck", SPEC["value_derivation"]["not_claimed"])
        readout = SPEC["preregistered"]["mechanism_readout"]
        self.assertIn("never merged", readout)
        self.assertIn("not collapsed into one INCONCLUSIVE", readout)
        self.assertIn("no automatic rerun", readout)


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

    def test_7_the_published_bytes_are_what_the_builder_makes(self) -> None:
        self.assertEqual(reward.build_zip(SPEC), self.data)
        self.assertIsNone(self.zip.testzip())
        if CURRENT.is_dir():
            self.assertEqual((CURRENT / HISTORY.name).read_bytes(), self.data)
            self.assertEqual((CURRENT / f"{HISTORY.name}.sha256").read_text(encoding="utf-8").split()[0], sha(self.data))

    def test_8_one_reward_line_moves(self) -> None:
        cand = self.member("candidate/quadruped_rewards.py").decode("utf-8").splitlines()
        ref = self.member("reference/baseline_quadruped_rewards.py").decode("utf-8").splitlines()
        self.assertEqual(len(cand), len(ref))
        moved = [(a, b) for a, b in zip(ref, cand) if a != b]
        self.assertEqual(len(moved), 1)
        self.assertIn('"lin_vel_z_l2":        -2.0,', moved[0][0])
        self.assertIn('"lin_vel_z_l2":        -1.25,', moved[0][1])

    def test_9_the_runner_is_the_repository_runner_and_the_config_pins_the_full_run(self) -> None:
        runner = self.member(SPEC["runner"])
        self.assertEqual(runner, (GO2 / SPEC["runner"]).read_bytes())
        self.assertNotIn(b"\r", runner)
        done = subprocess.run(["bash", "-n"], input=runner, capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = self.member("run_config.env").decode("utf-8")
        self.assertNotIn("\r", config)
        for line in ("GO2_STAGE=full\n", "COLLECT_REQUIRED_ON_STATIONARY=1\n", "SINGLE_CHANGE_TO=-1.25\n",
                     "TRAIN_SEED=42\n", "BASELINE_VIDEOS=()\n", "WORK_ID=G-A048\n"):
            self.assertIn(line, config)


class GuideTest(unittest.TestCase):
    def test_10_the_guide_commands_run_and_write_nothing_tracked(self) -> None:
        if not CURRENT.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (CURRENT / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn(sha(HISTORY.read_bytes()), guide)
        joined = guide.replace("\\\n", " ")
        commands = [line.strip() for line in joined.splitlines() if line.strip().startswith("python -B tools/")]
        self.assertEqual(len(commands), 3, commands)
        self.assertIn("--rule-version post_a043_push4_v1", commands[1])
        self.assertIn("go2_dial_hypothesis.py G-A048", commands[2])
        self.assertIn("채택 판정과 합치지 않는다", guide)
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
    """느리다(수 분).  G-A044 수확물을 대역으로 채택 판정기의 끝까지 간다 — 회차가 다르다는 식별 결함만 뺀다."""

    STAND_IN = ROOT / "workspace/_keep/go2_g_a044_a033_lin_vel_z_m175"
    EXPECTED = ("work_id=", "train_single_change=", "env_reward_lin_vel_z_l2=")

    def test_11_the_verifier_reaches_a_verdict_with_the_four_direction_screening(self) -> None:
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
        self.assertTrue(dropped, "the stand-in should differ from G-A048 by identity only")
        self.assertEqual(report["combined_verdict"]["artifact"], "ARTIFACT_VERIFIED")
        self.assertIn(report["combined_verdict"]["plan_screening"],
                      (screening.PASS, screening.FAIL, screening.INCONCLUSIVE))
        self.assertIn("post_a043_push4_v1", report["plan_screening"]["rule"])
        self.assertIn(report["verdict"], ("PASS", "FAIL"))


if __name__ == "__main__":
    unittest.main()
