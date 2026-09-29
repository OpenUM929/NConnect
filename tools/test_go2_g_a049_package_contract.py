"""G-A049 패키지 계약 — `lin_vel_z_l2` -2.0 -> -1.0, 분기 B 탐색 회차 (2026-09-27).

계획 `workspace/training/quadruped/upload/plan/GO2_NEXT_CANDIDATE_20260927.md` §2, 사용자 결정 G-D-BRANCH-B-20260927.
G-A048 의 실행 계약(전수 69 · 단일 단계)과 fact_rules_v1 문턱을 그대로 쓰고, 계획 screening 만 2026-09-26 사전등록한
`post_a048_guard_margin_v1` 로 바꾼다.  채택과 **별개인** 가설 판정 두 지표를 결과 전에 고정하고, 15cm 는 기록만 한다.

  * fact_rules_v1 문턱은 G-A048 과 **글자 그대로** 같다 — 다른 칸은 서술 셋, 가설 블록, 계획 screening 판뿐이다.
  * 계획 screening 판은 판정기에 등록된 사전등록 판이고, 그 값은 비교 문서의 값이다(`test_go2_guard_margin_rule_contract`).
  * 가설 문턱은 계획서 §2 의 숫자와 같다.  15cm 는 `recorded` 에만 있고 판정 이름이 붙지 않는다.
  * 판독기는 저장된 관측점에서 기존 표의 수를 재현한다(G-A048 포함).
  * 바뀌는 보상은 한 줄이고, 러너는 저장소 러너이며, 발행물은 빌더가 다시 만든 바이트와 같다.
  * 안내문의 판독 명령 셋이 실제 CLI 에서 돌고, 돌리는 동안 `reports/` 를 쓰지 않는다.
  * 채택 판정기가 이 사양으로 끝까지 도는지를 G-A048 수확물을 대역으로 본다(판정 값 자체는 의미가 없다).
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
import go2_dial_hypothesis as hypothesis  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402

WORK_ID = "G-A049"
SPEC = reward.load(WORK_ID)
PREVIOUS = reward.load("G-A048")
HISTORY = reward.output_path(SPEC)
CURRENT = GO2 / "upload" / WORK_ID / "current"
EDITION = "post_a048_guard_margin_v1"
# 서술 칸 셋, 가설 블록, 계획 screening 판.  이 밖의 preregistered 칸은 G-A048 과 같아야 한다.
DECLARED = {"source", "threshold_basis", "mechanism_readout", "hypothesis", "plan_screening"}
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
        self.assertEqual(SPEC["single_change"], {**PREVIOUS["single_change"], "to": -1.0})
        self.assertEqual(SPEC["training"], PREVIOUS["training"])
        self.assertEqual(SPEC["rewards"]["baseline"], PREVIOUS["rewards"]["baseline"])
        self.assertEqual(base_data.spec_problems(SPEC), [])
        term = SPEC["base_data"]["terms"]["lin_vel_z_l2"]
        self.assertEqual(term["status"], "OUT_OF_RANGE")
        self.assertEqual(term["walking_values"], [-2.0, -1.75, -1.5, -1.25])

    def test_2_fact_rules_thresholds_are_g_a048s_and_the_screening_is_the_preregistered_edition(self) -> None:
        mine, theirs = SPEC["preregistered"], PREVIOUS["preregistered"]
        self.assertEqual(set(mine), set(theirs))
        for key in sorted(set(theirs) - DECLARED):
            with self.subTest(key=key):
                self.assertEqual(mine[key], theirs[key])
        self.assertEqual(mine["rule_version"], "fact_rules_v1")
        self.assertEqual(mine["plan_screening"]["version"], EDITION)
        self.assertIsNotNone(screening.guard_margin(EDITION))
        self.assertEqual(screening.cases_for(EDITION), screening.RULE_VERSIONS["post_a043_push4_v1"])
        self.assertTrue(screening.improvement_required(EDITION))
        self.assertEqual(SPEC["evaluation"], PREVIOUS["evaluation"])
        self.assertEqual(SPEC["collection"]["mode"], "full_69_single_stage")

    def test_3_hypothesis_thresholds_are_the_plans_numbers_and_15cm_is_recorded_only(self) -> None:
        block = SPEC["preregistered"]["hypothesis"]
        self.assertIs(block["separate_from_adoption"], True)
        self.assertEqual(block["reader"], "tools/go2_dial_hypothesis.py")
        self.assertEqual(set(INDICATORS), {"rough_lateral_posture_falls", "yaw_right_posture_cost"})
        rough, yaw = INDICATORS["rough_lateral_posture_falls"], INDICATORS["yaw_right_posture_cost"]
        self.assertEqual((rough["supported_if_at_most"], rough["not_supported_if_at_least"]), (41, 59))
        self.assertEqual((yaw["present_if_seeds_at_least"], yaw["absent_if_seeds_at_most"]), (2, 0))
        recorded = block["recorded"]["stairs_15_ge2"]
        self.assertEqual(recorded["metric"], "climb_ge2_pooled")
        self.assertFalse({"supported_if_at_least", "not_supported_if_at_most"} & set(recorded))
        plan = (ROOT / SPEC["plan"]).read_text(encoding="utf-8")
        for text in ("옆걸음 낙상 `41`/`59`", "우회전 seed `2`/`0`", "기록만 하고 판정하지 않는다",
                     "G-A037의 도출 원리(벌점 몫 → 15cm 오르기)로 −1.0을 고르지 않는다"):
            with self.subTest(text=text):
                self.assertIn(text, plan)

    def test_4_the_reader_judges_two_indicators_and_names_no_verdict_for_the_recorded_count(self) -> None:
        seeds = lambda values: dict(zip(("101", "202", "303"), values))
        cases = [
            ("rough_lateral_posture_falls", (14, 14, 13), "SUPPORTED"),
            ("rough_lateral_posture_falls", (14, 14, 14), "INSUFFICIENT"),
            ("rough_lateral_posture_falls", (20, 20, 19), "NOT_SUPPORTED"),
            ("yaw_right_posture_cost", (1, 0, 1), "PRESENT"), ("yaw_right_posture_cost", (0, 0, 2), "INSUFFICIENT"),
            ("yaw_right_posture_cost", (0, 0, 0), "ABSENT"), ("yaw_right_posture_cost", (0, None, 0), "MISSING"),
        ]
        for name, values, want in cases:
            with self.subTest(name=name, values=values):
                self.assertEqual(hypothesis.judge(INDICATORS[name], seeds(values))[0], want)

    def test_5_the_reader_reproduces_the_stored_points(self) -> None:
        rows = hypothesis.stored_arms(SPEC)
        got = {(r[0], r[2]): (r[3], r[5]) for r in rows[1:]}
        if not got or any(v[1] == "MISSING" for v in got.values()):
            self.skipTest("저장된 수확물이 이 PC 에 없다")
        # reports/evidence/go2_g_a048_readout_20260926/DIAL_FOUR_POINTS.csv
        self.assertEqual(got[("G-A033", "rough_lateral_posture_falls")], ("20/20/19", "NOT_SUPPORTED"))
        self.assertEqual(got[("G-A043", "stairs_15_ge2")], ("25/23/29", hypothesis.RECORDED))
        self.assertEqual(got[("G-A048", "rough_lateral_posture_falls")], ("5/8/3", "SUPPORTED"))
        self.assertEqual(got[("G-A048", "yaw_right_posture_cost")], ("0/0/0", "ABSENT"))
        self.assertEqual(got[("G-A048", "stairs_15_ge2")], ("8/4/12", hypothesis.RECORDED))
        self.assertEqual(got[("G-A043", "yaw_right_posture_cost")], ("9/9/11", "PRESENT"))

    def test_5b_an_unverified_harvest_gets_no_verdict_names_including_the_recorded_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = hypothesis.read(SPEC, Path(tmp) / "none")
        names = {i["verdict"] for i in result["indicators"].values()} | {i["verdict"] for i in result["recorded"].values()}
        self.assertEqual(names, {hypothesis.UNVERIFIED})

    def test_6_it_is_an_exploratory_range_extension_not_a_recommendation(self) -> None:
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        self.assertIn("Not a promise of a higher score", SPEC["why"][0])
        self.assertIn("not proven more informative", SPEC["value_derivation"]["rule"])
        self.assertIn("does not make G-A048's result luck", SPEC["value_derivation"]["not_claimed"])
        self.assertIn("not chosen by that derivation", SPEC["value_derivation"]["not_claimed"])
        self.assertIn("does not stand in for a U2 permission", SPEC["decision_ref"])
        readout = SPEC["preregistered"]["mechanism_readout"]
        for text in ("never merged", "not collapsed into one INCONCLUSIVE", "no automatic rerun"):
            self.assertIn(text, readout)


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
        self.assertIn('"lin_vel_z_l2":        -1.0,', moved[0][1])

    def test_9_the_runner_is_the_repository_runner_and_the_config_pins_the_full_run(self) -> None:
        runner = self.member(SPEC["runner"])
        self.assertEqual(runner, (GO2 / SPEC["runner"]).read_bytes())
        self.assertNotIn(b"\r", runner)
        done = subprocess.run(["bash", "-n"], input=runner, capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = self.member("run_config.env").decode("utf-8")
        self.assertNotIn("\r", config)
        for line in ("GO2_STAGE=full\n", "COLLECT_REQUIRED_ON_STATIONARY=1\n", "SINGLE_CHANGE_TO=-1.0\n",
                     "TRAIN_SEED=42\n", "BASELINE_VIDEOS=()\n", "WORK_ID=G-A049\n"):
            self.assertIn(line, config)
        spec_in_zip = json.loads(self.member("experiment.json").decode("utf-8"))
        self.assertEqual(spec_in_zip["preregistered"]["plan_screening"]["version"], EDITION)


class GuideTest(unittest.TestCase):
    def test_10_the_guide_commands_run_and_write_nothing_tracked(self) -> None:
        if not CURRENT.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (CURRENT / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn(sha(HISTORY.read_bytes()), guide)
        joined = guide.replace("\\\n", " ")
        commands = [line.strip() for line in joined.splitlines() if line.strip().startswith("python -B tools/")]
        self.assertEqual(len(commands), 3, commands)
        self.assertIn(f"--rule-version {EDITION}", commands[1])
        self.assertIn("go2_dial_hypothesis.py G-A049", commands[2])
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
    """느리다(수 분).  G-A048 수확물을 대역으로 채택 판정기의 끝까지 간다 — 회차가 다르다는 식별 결함만 뺀다."""

    STAND_IN = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125"
    EXPECTED = ("work_id=", "train_single_change=", "env_reward_lin_vel_z_l2=")

    def test_11_the_verifier_reaches_a_verdict_with_the_margin_edition(self) -> None:
        if not self.STAND_IN.is_dir():
            self.skipTest("대역 수확물(G-A048)이 이 PC 에 없다")
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
        self.assertTrue(dropped, "the stand-in should differ from G-A049 by identity only")
        self.assertEqual(report["combined_verdict"]["artifact"], "ARTIFACT_VERIFIED")
        self.assertIn(report["combined_verdict"]["plan_screening"],
                      (screening.PASS, screening.FAIL, screening.INCONCLUSIVE))
        self.assertIn(EDITION, report["plan_screening"]["rule"])
        guard = [c["check"] for c in report["plan_screening"]["checks"] if c["group"] == "guard"]
        self.assertEqual(len(guard), 14)
        self.assertIn(report["verdict"], ("PASS", "FAIL"))


if __name__ == "__main__":
    unittest.main()
