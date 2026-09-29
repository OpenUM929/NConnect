"""G-A050 패키지 계약 — `lin_vel_z_l2` -2.0 -> -1.375, G3 험지 표적 회차 (2026-09-27).

계획 `workspace/training/quadruped/upload/plan/GO2_G3_FIRST_20260927.md`, 사용자 결정 G-D-G3-FIRST-20260927.
G-A049 의 실행 계약(전수 69 · 단일 단계)과 fact_rules_v1 문턱을 그대로 쓰고, 계획 screening 만 계단 개선 묶음을
뺀 보호 전용 허용 손실 판 `g3_guard_margin_v1` 로 바꾼다.  가설 두 지표(선은 G-A049 와 같다)는 채택과 별개이고,
15cm 는 가설에서 기록만 한다 — 계단은 채택 보호에서 판정된다.

  * fact_rules_v1 문턱은 G-A049 와 **글자 그대로** 같다 — 다른 칸은 서술 칸, 가설 블록, 계획 screening 판, 그리고
    새 판에서 더는 기준이 아닌 계단 기록의 문구(required_records·target_group_roles)뿐이다.
  * 계획 screening 판은 개선 묶음이 없고 보호 묶음은 post_a048_guard_margin_v1 과 같은 값이다.
  * 값은 험지를 올린 두 측정점(-1.5, -1.25) 사이이고 BETWEEN_OBSERVED 다.
  * 바뀌는 보상은 한 줄이고, 러너는 저장소 러너이며, 발행물은 빌더가 다시 만든 바이트와 같다.
  * 안내문의 판독 명령 셋이 실제 CLI 에서 돌고, 돌리는 동안 `reports/` 를 쓰지 않는다.
  * 채택 판정기가 이 사양으로 끝까지 도는지를 G-A049 수확물을 대역으로 본다(판정 값 자체는 의미가 없고 기록하지 않는다).
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

WORK_ID = "G-A050"
SPEC = reward.load(WORK_ID)
PREVIOUS = reward.load("G-A049")
HISTORY = reward.output_path(SPEC)
CURRENT = GO2 / "upload" / WORK_ID / "current"
EDITION = "g3_guard_margin_v1"
# 서술 칸, 가설 블록, 계획 screening 판, 계단 기록 문구.  이 밖의 preregistered 칸은 G-A049 와 같아야 한다.
DECLARED = {"source", "threshold_basis", "mechanism_readout", "hypothesis", "plan_screening",
            "required_records", "target_group_roles"}
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
        self.assertEqual(SPEC["single_change"], {**PREVIOUS["single_change"], "to": -1.375})
        self.assertEqual(SPEC["training"], PREVIOUS["training"])
        self.assertEqual(SPEC["rewards"]["baseline"], PREVIOUS["rewards"]["baseline"])
        self.assertEqual(base_data.spec_problems(SPEC), [])
        term = SPEC["base_data"]["terms"]["lin_vel_z_l2"]
        self.assertEqual(term["status"], "BETWEEN_OBSERVED")
        self.assertEqual(term["walking_values"], [-2.0, -1.75, -1.5, -1.25])

    def test_2_fact_rules_thresholds_are_g_a049s_and_the_screening_is_the_guard_only_margin_edition(self) -> None:
        mine, theirs = SPEC["preregistered"], PREVIOUS["preregistered"]
        self.assertEqual(set(mine), set(theirs))
        for key in sorted(set(theirs) - DECLARED):
            with self.subTest(key=key):
                self.assertEqual(mine[key], theirs[key])
        self.assertEqual(mine["rule_version"], "fact_rules_v1")
        self.assertEqual(mine["plan_screening"]["version"], EDITION)
        self.assertEqual(screening.guard_margin(EDITION), screening.guard_margin("post_a048_guard_margin_v1"))
        self.assertEqual(screening.cases_for(EDITION), screening.RULE_VERSIONS["post_a043_push4_v1"])
        self.assertFalse(screening.improvement_required(EDITION))
        self.assertTrue(screening.improvement_required("post_a048_guard_margin_v1"))
        for key in ("climb_counts", "stairs_forward_distance", "stall_time_share"):
            self.assertIn("NOT A PLAN SCREENING CRITERION UNDER g3_guard_margin_v1", mine["required_records"][key])
        for key in ("push_both_directions", "push_all_directions"):
            self.assertIn("g3_guard_margin_v1", mine["required_records"][key])
        self.assertIn("baseline + 3", mine["required_records"]["push_all_directions"])
        self.assertIn("no survival-median check", mine["required_records"]["push_all_directions"])
        self.assertNotIn("is not supported at this step size", mine["target_group_roles"]["stairs"])
        self.assertIn("carries no hypothesis in this run", mine["target_group_roles"]["stairs"])
        walk = SPEC["inference"]["predictions"]["walk"]["basis"]
        self.assertNotIn("rules out a standing policy", walk)
        self.assertIn("does not rule out a standing policy", walk)
        rest = set(theirs["required_records"]) - {"climb_counts", "stairs_forward_distance", "stall_time_share",
                                                  "push_both_directions", "push_all_directions"}
        for key in sorted(rest):
            self.assertEqual(mine["required_records"][key], theirs["required_records"][key])
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
        for text in ("험지 옆걸음 자세 낙상 ≤41 지지 / ≥59 미지지", "복합 우회전 낙상 seed 수 ≥2 PRESENT / 0 ABSENT",
                     "15cm ≥2단은 기록만", "`g3_guard_margin_v1`", "A048·A049를 이 판으로 다시 판정하지 않는다"):
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

    def test_6_it_is_an_exploratory_g3_search_position_not_a_recommendation(self) -> None:
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        self.assertIn("Not a promise of a higher score", SPEC["why"][0])
        self.assertIn("not proven better than -1.4 or -1.35", SPEC["value_derivation"]["rule"])
        self.assertIn("a midpoint does not inherit its neighbours' performance", SPEC["value_derivation"]["not_claimed"])
        self.assertIn("G-A048 and G-A049 are not re-judged", SPEC["decision_ref"])
        readout = SPEC["preregistered"]["mechanism_readout"]
        for text in ("never merged", "no automatic rerun", "deltas against G-A048",
                     "is not reported as progress by itself"):
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
        self.assertIn('"lin_vel_z_l2":        -1.375,', moved[0][1])

    def test_9_the_runner_is_the_repository_runner_and_the_config_pins_the_full_run(self) -> None:
        runner = self.member(SPEC["runner"])
        self.assertEqual(runner, (GO2 / SPEC["runner"]).read_bytes())
        self.assertNotIn(b"\r", runner)
        done = subprocess.run(["bash", "-n"], input=runner, capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = self.member("run_config.env").decode("utf-8")
        self.assertNotIn("\r", config)
        for line in ("GO2_STAGE=full\n", "COLLECT_REQUIRED_ON_STATIONARY=1\n", "SINGLE_CHANGE_TO=-1.375\n",
                     "TRAIN_SEED=42\n", "BASELINE_VIDEOS=()\n", "WORK_ID=G-A050\n"):
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
        self.assertIn("go2_dial_hypothesis.py G-A050", commands[2])
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
    """느리다(수 분).  G-A049 수확물을 대역으로 채택 판정기의 끝까지 간다 — 회차가 다르다는 식별 결함만 뺀다."""

    STAND_IN = ROOT / "workspace/_keep/go2_g_a049_a033_lin_vel_z_m1"
    EXPECTED = ("work_id=", "train_single_change=", "env_reward_lin_vel_z_l2=")

    def test_11_the_verifier_reaches_a_verdict_with_the_margin_edition(self) -> None:
        if not self.STAND_IN.is_dir():
            self.skipTest("대역 수확물(G-A049)이 이 PC 에 없다")
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
        self.assertTrue(dropped, "the stand-in should differ from G-A050 by identity only")
        self.assertEqual(report["combined_verdict"]["artifact"], "ARTIFACT_VERIFIED")
        self.assertIn(report["combined_verdict"]["plan_screening"],
                      (screening.PASS, screening.FAIL, screening.INCONCLUSIVE))
        self.assertIn(EDITION, report["plan_screening"]["rule"])
        groups = {c["group"] for c in report["plan_screening"]["checks"]}
        self.assertEqual(groups, {"guard"}, "the G3 edition has no stairs-improvement or stall block")
        guard = [c["check"] for c in report["plan_screening"]["checks"] if c["group"] == "guard"]
        self.assertEqual(len(guard), 14)
        self.assertIn(report["verdict"], ("PASS", "FAIL"))


if __name__ == "__main__":
    unittest.main()
