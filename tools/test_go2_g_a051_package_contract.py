"""G-A051 패키지 계약 — G-A048 보상 위 `ang_vel_xy_l2` -0.05 -> -0.06 (2026-09-27).

계획 `workspace/training/quadruped/upload/plan/GO2_G_A051_PLAN_20260927.md`, Codex 후보 선택(사용자 중계)
G-D-A051-ANGVEL-20260927.  보상 기준이 채택 기준선과 다른 첫 회차다.

  * 후보는 G-A048 이 **학습한** 보상과 한 줄, 채택 기준선 G-A033 과 두 줄 다르다(빌더가 A048 학습 원본으로 대조).
  * 채택 판정(fact_rules_v1 + g3_guard_margin_v1)은 G-A050 과 글자 그대로 같고 G-A033 대비다.
  * 효과 판정은 따로다 — 가설 지표(험지 옆걸음 ≤8 지지 / ≥16 미지지)와 정량 후보 검토 판정(tools/go2_reward_base_comparison.py, 최종 진보 판정이 아니다).
  * 효과 판독기가 저장된 A050 수확물로 Codex 의 A050 비교값(-2.90202)을 재현하고, 미검증 수확물에는 판정을 내리지 않는다.
  * 발행물은 빌더가 다시 만든 바이트와 같고, 안내문의 판독 명령 넷이 실제 CLI 에서 돈다.
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
import go2_reward_base_comparison as comparison  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

WORK_ID = "G-A051"
SPEC = reward.load(WORK_ID)
PREVIOUS = reward.load("G-A050")
HISTORY = reward.output_path(SPEC)
CURRENT = GO2 / "upload" / WORK_ID / "current"
EDITION = "g3_guard_margin_v1"
A048_KEEP = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125"
A050_KEEP = ROOT / "workspace/_keep/go2_g_a050_a033_lin_vel_z_m1375"
# 서술 칸, 가설 블록, 효과 판정 블록, 필수 기록 문구.  이 밖의 preregistered 칸은 G-A050 과 같아야 한다.
DECLARED = {"source", "threshold_basis", "mechanism_readout", "hypothesis", "plan_screening",
            "required_records", "target_group_roles", "reward_base_comparison"}
INDICATORS = SPEC["preregistered"]["hypothesis"]["indicators"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reports_bytes() -> dict[str, str]:
    base = GO2 / "reports"
    return {str(p.relative_to(base)): sha(p.read_bytes()) for p in sorted(base.rglob("*")) if p.is_file()}


class SpecTest(unittest.TestCase):
    def test_1_one_change_on_g_a048s_trained_rewards_two_against_g_a033(self) -> None:
        release.validate(SPEC)
        self.assertEqual(SPEC["single_change"]["name"], "ang_vel_xy_l2")
        self.assertEqual((SPEC["single_change"]["from"], SPEC["single_change"]["to"]), (-0.05, -0.06))
        rb = SPEC["reward_base"]
        self.assertEqual(rb["name"], "G-A048")
        self.assertEqual(reward_dict((ROOT / rb["trained_source"]).read_text(encoding="utf-8")), rb["rewards"])
        base, cand = SPEC["rewards"]["baseline"], SPEC["rewards"]["candidate"]
        self.assertEqual(base, PREVIOUS["rewards"]["baseline"])
        self.assertEqual({k for k in base if base[k] != cand[k]}, {"lin_vel_z_l2", "ang_vel_xy_l2"})
        self.assertEqual({k for k in cand if rb["rewards"][k] != cand[k]}, {"ang_vel_xy_l2"})
        self.assertEqual(SPEC["training"], PREVIOUS["training"])
        self.assertEqual(base_data.spec_problems(SPEC), [])
        self.assertEqual(SPEC["base_data"]["terms"]["ang_vel_xy_l2"]["status"], "OUT_OF_RANGE")
        self.assertEqual(SPEC["base_data"]["terms"]["lin_vel_z_l2"]["status"], "OBSERVED")

    def test_1b_the_builder_refuses_a_reward_base_that_is_not_what_g_a048_trained(self) -> None:
        bad = json.loads(json.dumps(SPEC))
        bad["reward_base"]["rewards"]["lin_vel_z_l2"] = -1.375
        bad["rewards"]["candidate"]["lin_vel_z_l2"] = -1.375
        with self.assertRaises(RuntimeError):
            reward.validate_spec(bad)
        two = json.loads(json.dumps(SPEC))
        two["rewards"]["candidate"]["feet_air_time"] = 0.25
        with self.assertRaises(RuntimeError):
            reward.validate_spec(two)

    def test_2_adoption_is_g_a050s_unchanged_against_g_a033(self) -> None:
        mine, theirs = SPEC["preregistered"], PREVIOUS["preregistered"]
        self.assertEqual(set(mine) - {"reward_base_comparison"}, set(theirs))
        for key in sorted(set(theirs) - DECLARED):
            with self.subTest(key=key):
                self.assertEqual(mine[key], theirs[key])
        self.assertEqual(mine["rule_version"], "fact_rules_v1")
        self.assertEqual(mine["plan_screening"]["version"], EDITION)
        for key in ("version", "entrypoint", "implementation", "inherits", "combination", "partial_coverage"):
            self.assertEqual(mine["plan_screening"][key], theirs["plan_screening"][key])
        self.assertEqual(SPEC["evaluation"], PREVIOUS["evaluation"])
        self.assertEqual(SPEC["baseline"], PREVIOUS["baseline"])
        self.assertEqual(SPEC["collection"]["mode"], "full_69_single_stage")
        self.assertNotIn("does not charge attitude", json.dumps(mine["required_records"]))

    def test_3_hypothesis_is_read_against_g_a048(self) -> None:
        block = SPEC["preregistered"]["hypothesis"]
        self.assertIs(block["separate_from_adoption"], True)
        rough, yaw = INDICATORS["rough_lateral_posture_falls"], INDICATORS["yaw_right_posture_cost"]
        self.assertEqual((rough["supported_if_at_most"], rough["not_supported_if_at_least"]), (8, 16))
        self.assertEqual((yaw["present_if_seeds_at_least"], yaw["absent_if_seeds_at_most"]), (2, 0))
        self.assertEqual(set(block["recorded"]), {"stairs_10_ge2", "stairs_15_ge2"})
        plan = (ROOT / SPEC["plan"]).read_text(encoding="utf-8")
        for text in ("**SUPPORTED ≤ 8**", "**NOT_SUPPORTED ≥ 16**", "≥ 0.164 m/s", "−0.055·−0.065 자동 탐색 없음",
                     "튜닝 진보로 보고하지 않는다", "4.4937 대 A038 1.9499"):
            with self.subTest(text=text):
                self.assertIn(text, plan)

    def test_4_the_reader_judges_the_a048_relative_lines(self) -> None:
        seeds = lambda values: dict(zip(("101", "202", "303"), values))
        for values, want in (((3, 3, 2), "SUPPORTED"), ((3, 3, 3), "INSUFFICIENT"), ((5, 8, 3), "NOT_SUPPORTED")):
            with self.subTest(values=values):
                self.assertEqual(hypothesis.judge(INDICATORS["rough_lateral_posture_falls"], seeds(values))[0], want)

    def test_5_a_review_candidate_needs_all_four_and_is_not_final_progress(self) -> None:
        block = SPEC["preregistered"]["reward_base_comparison"]
        self.assertNotIn("progress_requires", block)
        need = block["review_requires"]
        self.assertEqual(need["adoption"], "QUANT_SUCCESS_VIDEO_REVIEW_PENDING")
        self.assertEqual(need["hypothesis"], {"rough_lateral_posture_falls": "SUPPORTED"})
        self.assertEqual(need["min_total_delta_70"], 0.0)
        self.assertEqual(need["min_speed"]["rough_lateral_speed_below"], 0.164)
        self.assertIn("does NOT show the policy did not slow down", need["min_speed"]["basis"])
        self.assertIn("not final progress", block["verdicts"])
        self.assertIn("no preregistered limit", block["not_judged"])
        self.assertIn("not an adoption PASS", SPEC["preregistered"]["mechanism_readout"])
        self.assertIn("reduced, below the target of 8", SPEC["preregistered"]["hypothesis"]["edge_rule"])
        self.assertIn("direct mechanism is not separated", SPEC["preregistered"]["required_records"]["terrain_level_at_pin"])
        self.assertNotIn("reported as a confound", json.dumps(SPEC))
        self.assertEqual(SPEC["preregistered"]["reward_base_comparison"]["base_arm"],
                         "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125")

    def test_5b_the_effect_reader_reproduces_the_a050_comparison(self) -> None:
        if not (A050_KEEP.is_dir() and A048_KEEP.is_dir()):
            self.skipTest("저장된 수확물이 이 PC 에 없다")
        result = comparison.compare(SPEC, A050_KEEP, verify=False)
        # workspace/server_returns/G-A050_REVIEW_20260927/A048_COMPARISON.json
        self.assertEqual(result["total_70"]["delta"], -2.90202)
        self.assertEqual(result["axes"]["G5"]["delta"], 0.0)
        self.assertEqual(result["verdict"], "NOT_REVIEW_CANDIDATE")
        self.assertIn("not a final progress verdict", result["verdict_scope"])
        self.assertTrue(any("preregistered floor" in f for f in result["failed"]))

    def test_5c_an_unverified_harvest_gets_no_progress_verdict(self) -> None:
        if not A048_KEEP.is_dir():
            self.skipTest("저장된 수확물이 이 PC 에 없다")
        # A048 의 harvest_verification.json 은 G-A048 것이라 G-A051 판정의 근거가 될 수 없다.
        self.assertEqual(comparison.compare(SPEC, A048_KEEP)["verdict"], "INCONCLUSIVE")

    def test_6_exploratory_and_selection_owner_recorded(self) -> None:
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        self.assertIn("Not a promise of a higher score", SPEC["why"][0])
        self.assertIn("no data says -0.06 beats -0.055 or -0.065", SPEC["value_derivation"]["rule"])
        self.assertIn("the direct mechanism is not separated", SPEC["value_derivation"]["not_claimed"])
        self.assertIn("Selection responsibility stays with Codex", SPEC["decision_ref"])
        readout = SPEC["preregistered"]["mechanism_readout"]
        for text in ("never merged", "never as tuning progress", "no -0.055 / -0.065"):
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

    def lines(self, name: str) -> list[str]:
        return self.member(name).decode("utf-8").splitlines()

    def test_7_the_published_bytes_are_what_the_builder_makes(self) -> None:
        self.assertEqual(reward.build_zip(SPEC), self.data)
        self.assertIsNone(self.zip.testzip())
        if CURRENT.is_dir():
            self.assertEqual((CURRENT / HISTORY.name).read_bytes(), self.data)
            self.assertEqual((CURRENT / f"{HISTORY.name}.sha256").read_text(encoding="utf-8").split()[0], sha(self.data))

    def test_8_one_line_against_g_a048_two_against_g_a033(self) -> None:
        cand = self.lines("candidate/quadruped_rewards.py")
        base48 = self.lines("reference/reward_base_quadruped_rewards.py")
        base33 = self.lines("reference/baseline_quadruped_rewards.py")
        moved48 = [(a, b) for a, b in zip(base48, cand) if a != b]
        moved33 = [(a, b) for a, b in zip(base33, cand) if a != b]
        self.assertEqual(len(cand), len(base48))
        self.assertEqual(len(moved48), 1)
        self.assertIn('"ang_vel_xy_l2":       -0.05,', moved48[0][0])
        self.assertIn('"ang_vel_xy_l2":       -0.06,', moved48[0][1])
        self.assertEqual(len(moved33), 2)
        self.assertEqual(self.member("baseline/quadruped_rewards.py"), self.member("reference/baseline_quadruped_rewards.py"))
        self.assertEqual(reward_dict("\n".join(base33)), SPEC["rewards"]["baseline"])

    def test_9_the_runner_is_the_repository_runner_and_the_config_pins_the_full_run(self) -> None:
        runner = self.member(SPEC["runner"])
        self.assertEqual(runner, (GO2 / SPEC["runner"]).read_bytes())
        self.assertNotIn(b"\r", runner)
        done = subprocess.run(["bash", "-n"], input=runner, capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = self.member("run_config.env").decode("utf-8")
        self.assertNotIn("\r", config)
        for line in ("GO2_STAGE=full\n", "COLLECT_REQUIRED_ON_STATIONARY=1\n", "SINGLE_CHANGE_TO=-0.06\n",
                     "TRAIN_SEED=42\n", "BASELINE_VIDEOS=()\n", "WORK_ID=G-A051\n"):
            self.assertIn(line, config)
        expected = json.loads(self.member("expected_rewards.json").decode("utf-8"))
        self.assertEqual(expected["candidate"], SPEC["rewards"]["candidate"])


class GuideTest(unittest.TestCase):
    def test_10_the_guide_commands_run_and_write_nothing_tracked(self) -> None:
        if not CURRENT.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (CURRENT / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn(sha(HISTORY.read_bytes()), guide)
        self.assertIn("G-A048 보상 위에서 ang_vel_xy_l2 -0.05 -> -0.06", guide)
        self.assertIn("최종 진보 판정이 아니다", guide)
        self.assertIn("영상 검토 전 정량 조건 충족이지 채택 PASS 가 아니다", guide)
        joined = guide.replace("\\\n", " ")
        commands = [line.strip() for line in joined.splitlines() if line.strip().startswith("python -B tools/")]
        self.assertEqual(len(commands), 4, commands)
        self.assertIn(f"--rule-version {EDITION}", commands[1])
        self.assertIn("go2_dial_hypothesis.py G-A051", commands[2])
        self.assertIn("go2_reward_base_comparison.py G-A051", commands[3])
        before = reports_bytes()
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "no_harvest")
            for command in commands[:3]:
                with self.subTest(command=command[:70]):
                    argv = [missing if part.startswith("workspace/_keep/") else part for part in command.split()[1:]]
                    if "--out" not in argv:
                        argv += ["--out", str(Path(tmp) / "out")]
                    done = subprocess.run([sys.executable, *argv], cwd=str(ROOT), env=env, capture_output=True,
                                          text=True, encoding="utf-8", timeout=300)
                    self.assertNotEqual(done.returncode, 2, done.stderr[-400:])
            # 넷째(효과 판정)는 없는 수확물에서 축을 못 읽고 죽는다 — CLI 연결만 저장된 A050 으로 본다.
            if A050_KEEP.is_dir():
                argv = commands[3].split()[1:]
                argv = [str(A050_KEEP) if part.startswith("workspace/_keep/") else part for part in argv]
                done = subprocess.run([sys.executable, *argv, "--out", str(Path(tmp) / "cmp.json")], cwd=str(ROOT),
                                      env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)
                self.assertEqual(done.returncode, 0, done.stderr[-400:])
                self.assertEqual(json.loads((Path(tmp) / "cmp.json").read_text(encoding="utf-8"))["verdict"], "INCONCLUSIVE")
        self.assertEqual(reports_bytes(), before, "a wiring check wrote into tracked evidence")


class VerifierPathTest(unittest.TestCase):
    """느리다(수 분).  G-A048 수확물을 대역으로 채택 판정기의 끝까지 간다 — 회차가 다르다는 식별 결함만 뺀다."""

    EXPECTED = ("work_id=", "train_single_change=", "env_reward_ang_vel_xy_l2=")

    def test_11_the_verifier_reaches_a_verdict_and_checks_both_moved_weights(self) -> None:
        if not A048_KEEP.is_dir():
            self.skipTest("대역 수확물(G-A048)이 이 PC 에 없다")
        original = verifier.check_artifacts
        dropped: list[str] = []

        def stand_in(keep, spec):
            faults, facts = original(keep, spec)
            dropped.extend(f for f in faults if f.startswith(self.EXPECTED))
            return [f for f in faults if not f.startswith(self.EXPECTED)], facts

        verifier.check_artifacts = stand_in
        try:
            report = verifier.verify(A048_KEEP, ROOT / SPEC["baseline"]["stored_arm"], SPEC)
        finally:
            verifier.check_artifacts = original
        # A048 은 ang_vel_xy -0.05 로 학습했으므로 -0.06 대조가 걸려야 하고, lin_vel_z -1.25 는 통과해야 한다.
        self.assertTrue(any(f.startswith("env_reward_ang_vel_xy_l2=") for f in dropped), dropped)
        self.assertFalse(any(f.startswith("env_reward_lin_vel_z_l2=") for f in dropped), dropped)
        self.assertEqual(report["combined_verdict"]["artifact"], "ARTIFACT_VERIFIED")
        self.assertIn(EDITION, report["plan_screening"]["rule"])
        guard = [c["check"] for c in report["plan_screening"]["checks"] if c["group"] == "guard"]
        self.assertEqual(len(guard), 14)
        self.assertIn(report["verdict"], ("PASS", "FAIL", "QUANT_SUCCESS_VIDEO_REVIEW_PENDING"))


if __name__ == "__main__":
    unittest.main()
