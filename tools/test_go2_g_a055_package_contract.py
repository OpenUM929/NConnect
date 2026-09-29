"""G-A055 패키지 계약 — G-A043 보상 위 `ang_vel_xy_l2` -0.05 -> -0.08 (2026-09-29).

사전등록 `workspace/training/quadruped/upload/plan/GO2_G_A055_PLAN_20260928.md`(Codex 후보 선택, 사용자 중계).
**조건부 준비 / 실행 미승인**(Codex 2026-09-29): G-A056 진단 판독 뒤 Codex 가 실행 여부를 정한다.

  * 후보는 G-A043 이 **학습한** 보상에서 한 줄만 바꾼다.  채택 기준선 G-A033 대비로는 `lin_vel_z_l2` 와 그 줄이 다르다.
  * 채택 판정(fact_rules_v1 + g3_guard_margin_v1)은 G-A051 과 글자 그대로 같다(문턱 불변).
  * 1순위 case(험지 옆걸음·복합 우회전·밀침 네 방향)는 A043 대비로 tools/go2_g_a055_readout.py 가 사전등록 §4 대로 읽는다.
  * G-A056 러너·패키지와 연결되지 않는다 — 진단이 끝나도 이 학습이 자동으로 돌지 않는다.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
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
import go2_g_a055_readout as readout  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

WORK_ID = "G-A055"
SPEC = reward.load(WORK_ID)
PREVIOUS = reward.load("G-A051")
HISTORY = reward.output_path(SPEC)
CURRENT = GO2 / "upload" / WORK_ID / "current"
A043_KEEP = ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15"
A048_KEEP = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125"
PLAN = ROOT / SPEC["plan"]
DECLARED = {"source", "threshold_basis", "mechanism_readout", "hypothesis", "plan_screening",
            "required_records", "target_group_roles", "reward_base_comparison", "g_a055_case_readout"}
RULE = SPEC["preregistered"]["g_a055_case_readout"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SpecTest(unittest.TestCase):
    def test_1_g_a043s_rewards_with_one_line_changed(self) -> None:
        release.validate(SPEC)
        single = SPEC["single_change"]
        self.assertEqual((single["name"], single["from"], single["to"]), ("ang_vel_xy_l2", -0.05, -0.08))
        rb = SPEC["reward_base"]
        self.assertEqual(rb["name"], "G-A043")
        self.assertEqual(reward_dict((ROOT / rb["trained_source"]).read_text(encoding="utf-8")), rb["rewards"])
        self.assertEqual(rb["change"], {"name": "lin_vel_z_l2", "from": -2.0, "to": -1.5})
        self.assertEqual(SPEC["rewards"]["baseline"], PREVIOUS["rewards"]["baseline"])
        moved = {k for k in rb["rewards"] if rb["rewards"][k] != SPEC["rewards"]["candidate"][k]}
        self.assertEqual(moved, {"ang_vel_xy_l2"})
        self.assertEqual(SPEC["training"], PREVIOUS["training"])
        self.assertEqual(base_data.spec_problems(SPEC), [])
        self.assertEqual(SPEC["comparison_arm"]["model_sha256"],
                         "4d9236818f998bdb87efaea4acfa1e4c861b0d87947229e88f9175495066bd6b")

    def test_2_adoption_rules_are_g_a051s_unchanged(self) -> None:
        mine, theirs = SPEC["preregistered"], PREVIOUS["preregistered"]
        for key in sorted(set(theirs) - DECLARED):
            with self.subTest(key=key):
                self.assertEqual(mine[key], theirs[key])
        self.assertEqual(mine["rule_version"], "fact_rules_v1")
        for key in ("version", "entrypoint", "implementation", "inherits", "combination", "partial_coverage"):
            self.assertEqual(mine["plan_screening"][key], theirs["plan_screening"][key])
        self.assertEqual(SPEC["evaluation"], PREVIOUS["evaluation"])
        self.assertEqual(SPEC["baseline"], PREVIOUS["baseline"])
        self.assertEqual(SPEC["collection"]["mode"], "full_69_single_stage")
        self.assertEqual(SPEC["videos"]["candidate"], PREVIOUS["videos"]["candidate"])
        self.assertEqual(SPEC["videos"]["baseline_reuse"], PREVIOUS["videos"]["baseline_reuse"])

    def test_3_preregistered_numbers_are_the_plans(self) -> None:
        rough = SPEC["preregistered"]["hypothesis"]["indicators"]["rough_lateral_posture_falls"]
        self.assertEqual((rough["supported_if_at_most"], rough["not_supported_if_at_least"]), (12, 24))
        self.assertEqual(RULE["rough_lateral"]["condition_c"], {"case_score_min_above": 0.5296, "speed_mean_at_least": 0.158})
        self.assertEqual(RULE["combined_yaw_right"], {"base_falls": 29, "target_at_most": 14,
                                                      "condition_s": {"case_score_min_above": 0.4358}})
        self.assertEqual(RULE["push"]["base_falls"], {"push_pos_x": 2, "push_neg_x": 4, "push_pos_y": 0, "push_neg_y": 4})
        self.assertEqual(RULE["push"]["base_case_score_min"],
                         {"push_pos_x": 0.9329, "push_neg_x": 0.8983, "push_pos_y": 0.9645, "push_neg_y": 0.8967})
        self.assertEqual(RULE["push"]["score_margin"], 0.02)
        plan = PLAN.read_text(encoding="utf-8")
        for text in ("**≥ 24: NOT_SUPPORTED.**", "**≤ 12이고 (C) 충족: SUPPORTED.**", "0.5296", "0.1580", "0.4358",
                     "**≤ 14이고 (S) 충족: 목표 수준 개선.**", "+x 0.9329, −x 0.8983, +y 0.9645, −y 0.8967",
                     "A043 − 0.02"):
            with self.subTest(text=text):
                self.assertIn(text, plan)
        rbc = SPEC["preregistered"]["reward_base_comparison"]
        self.assertEqual((rbc["base_name"], rbc["base_total_70"]), ("G-A043", 44.62454))
        self.assertEqual(rbc["review_requires"]["min_speed"]["rough_lateral_speed_below"], 0.158)

    def test_4_conditional_and_not_linked_to_g_a056(self) -> None:
        self.assertIn("CONDITIONAL / EXECUTION NOT APPROVED", SPEC["decision_ref"])
        self.assertIn("Selection responsibility stays with Codex", SPEC["decision_ref"])
        self.assertIn("EXECUTION NOT APPROVED", SPEC["notes"]["execution_status"])
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        for path in (GO2 / "server_run_go2_a043_diag_replay.sh", ROOT / "tools/build_go2_a043_diag_replay_package.py"):
            text = path.read_text(encoding="utf-8")
            for name in ("G-A055", "g_a055", "go2_g_a055"):
                self.assertNotIn(name, text, f"{path.name} mentions {name}")
        a056 = GO2 / "upload/G-A056/current"
        for z in a056.glob("*.zip"):
            with zipfile.ZipFile(z) as archive:
                self.assertFalse(any("a055" in n.lower() for n in archive.namelist()))

    def test_5_readers_judge_the_preregistered_lines(self) -> None:
        seeds = lambda values: dict(zip(("101", "202", "303"), values))  # noqa: E731
        ind = SPEC["preregistered"]["hypothesis"]["indicators"]["rough_lateral_posture_falls"]
        for values, want in (((4, 4, 4), "SUPPORTED"), ((5, 4, 4), "INSUFFICIENT"), ((8, 11, 5), "NOT_SUPPORTED")):
            with self.subTest(values=values):
                self.assertEqual(hypothesis.judge(ind, seeds(values))[0], want)
        ok = lambda falls, score, speed=0.2: {"state": "OK", "falls": falls, "case_score_min": score, "speed_mean": speed}  # noqa: E731
        r = RULE["rough_lateral"]
        self.assertEqual(readout.rough_verdict(ok(12, 0.6), r)["verdict"], "SUPPORTED")
        self.assertEqual(readout.rough_verdict(ok(12, 0.52), r)["verdict"], "FALL_TARGET_MET_OVERALL_UNCONFIRMED")
        self.assertEqual(readout.rough_verdict(ok(12, 0.6, 0.15), r)["verdict"], "FALL_TARGET_MET_OVERALL_UNCONFIRMED")
        self.assertEqual(readout.rough_verdict(ok(13, 0.6), r)["verdict"], "REDUCED_BELOW_TARGET")
        self.assertEqual(readout.rough_verdict(ok(24, 0.9), r)["verdict"], "NOT_SUPPORTED")
        y = RULE["combined_yaw_right"]
        cases = ((14, 0.5, "TARGET_LEVEL"), (15, 0.5, "REDUCED_BELOW_TARGET"), (28, 0.5, "REDUCED_BELOW_TARGET"),
                 (10, 0.43, "FALLS_REDUCED_OVERALL_UNCONFIRMED"), (29, 0.9, "SAME_FALLS"), (30, 0.9, "WORSE"))
        for falls, score, want in cases:
            with self.subTest(falls=falls, score=score):
                self.assertEqual(readout.yaw_verdict(ok(falls, score), y)["verdict"], want)
        # 0~96 의 모든 낙상 수가 정확히 하나의 이름을 받는다(점수 조건 두 경우).
        for s in (0.3, 0.9):
            for n in range(97):
                self.assertIn(readout.yaw_verdict(ok(n, s), y)["verdict"],
                              {"TARGET_LEVEL", "REDUCED_BELOW_TARGET", "FALLS_REDUCED_OVERALL_UNCONFIRMED", "SAME_FALLS", "WORSE"})
                self.assertIn(readout.rough_verdict(ok(n, s), r)["verdict"],
                              {"SUPPORTED", "FALL_TARGET_MET_OVERALL_UNCONFIRMED", "REDUCED_BELOW_TARGET", "NOT_SUPPORTED"})
        p = RULE["push"]
        self.assertEqual(readout.push_verdict(ok(4, 0.8783), "push_neg_x", p)["verdict"], "NO_WORSE")
        self.assertEqual(readout.push_verdict(ok(5, 0.95), "push_neg_x", p)["verdict"], "WORSE")
        self.assertEqual(readout.push_verdict(ok(0, 0.94), "push_pos_y", p)["verdict"], "WORSE")
        self.assertEqual(readout.rough_verdict({"state": "MISSING"}, r)["verdict"], "MISSING")

    def test_6_the_case_reader_reproduces_g_a043_on_its_stored_arm(self) -> None:
        if not A043_KEEP.is_dir():
            self.skipTest("저장된 A043 수확물이 이 PC 에 없다")
        out = readout.read(SPEC, A043_KEEP, verify=False)["cases"]
        self.assertEqual(out["rough_lateral"]["candidate"]["falls_per_seed"], [8, 11, 5])
        self.assertEqual(round(out["rough_lateral"]["candidate"]["case_score_min"], 4), 0.5296)
        self.assertEqual(out["rough_lateral"]["verdict"], "NOT_SUPPORTED")
        self.assertEqual(out["combined_yaw_right"]["candidate"]["falls_per_seed"], [9, 9, 11])
        self.assertEqual(round(out["combined_yaw_right"]["candidate"]["case_score_min"], 4), 0.4358)
        self.assertEqual(out["combined_yaw_right"]["verdict"], "SAME_FALLS")
        for case, want in RULE["push"]["base_falls"].items():
            self.assertEqual(out[case]["candidate"]["falls"], want, case)
            self.assertEqual(round(out[case]["candidate"]["case_score_min"], 4), RULE["push"]["base_case_score_min"][case])
            self.assertEqual(out[case]["verdict"], "NO_WORSE")
        self.assertEqual((out["stairs_10_down"]["candidate"]["climb_ge2"], out["stairs_15_down"]["candidate"]["climb_ge2"]), (94, 77))

    def test_7_an_unverified_harvest_gets_no_verdict_name(self) -> None:
        if not A048_KEEP.is_dir():
            self.skipTest("저장된 수확물이 이 PC 에 없다")
        out = readout.read(SPEC, A048_KEEP)
        self.assertFalse(out["harvest_check"]["verified"])
        self.assertTrue(all(i["verdict"] == hypothesis.UNVERIFIED for i in out["cases"].values()))


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

    def test_8_the_published_bytes_are_what_the_builder_makes(self) -> None:
        self.assertEqual(reward.build_zip(SPEC), self.data)
        self.assertIsNone(self.zip.testzip())
        if CURRENT.is_dir():
            self.assertEqual((CURRENT / HISTORY.name).read_bytes(), self.data)
            self.assertEqual((CURRENT / f"{HISTORY.name}.sha256").read_text(encoding="utf-8").split()[0], sha(self.data))

    def test_9_one_changed_weight_line_against_g_a043(self) -> None:
        cand = self.lines("candidate/quadruped_rewards.py")
        base43 = self.lines("reference/reward_base_quadruped_rewards.py")
        base33 = self.lines("reference/baseline_quadruped_rewards.py")
        removed = [line for line in base43 if line not in cand]
        added = [line for line in cand if line not in base43]
        self.assertEqual(len(removed), 1, removed)
        self.assertEqual(len(added), 1, added)
        self.assertIn("ang_vel_xy_l2", removed[0])
        self.assertIn("-0.08", added[0])
        self.assertEqual(reward_dict("\n".join(cand)), SPEC["rewards"]["candidate"])
        self.assertEqual(reward_dict("\n".join(base43)), SPEC["reward_base"]["rewards"])
        self.assertEqual(reward_dict("\n".join(base33)), SPEC["rewards"]["baseline"])

    def test_10_the_runner_is_the_repository_runner_and_the_config_pins_the_full_run(self) -> None:
        runner = self.member(SPEC["runner"])
        self.assertEqual(runner, (GO2 / SPEC["runner"]).read_bytes())
        self.assertNotIn(b"\r", runner)
        done = subprocess.run(["bash", "-n"], input=runner, capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = self.member("run_config.env").decode("utf-8")
        self.assertNotIn("\r", config)
        for line in ("GO2_STAGE=full\n", "SINGLE_CHANGE_NAME=ang_vel_xy_l2\n", "SINGLE_CHANGE_TO=-0.08\n",
                     "TRAIN_SEED=42\n", "BASELINE_VIDEOS=()\n", "WORK_ID=G-A055\n"):
            self.assertIn(line, config)
        expected = json.loads(self.member("expected_rewards.json").decode("utf-8"))
        self.assertEqual(expected["candidate"], SPEC["rewards"]["candidate"])


class GuideTest(unittest.TestCase):
    def test_11_the_guide_states_the_conditional_status_and_all_readers(self) -> None:
        if not CURRENT.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (CURRENT / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn(sha(HISTORY.read_bytes()), guide)
        self.assertIn("조건부 준비·실행 미승인", guide)
        joined = guide.replace("\\\n", " ")
        commands = [line.strip() for line in joined.splitlines() if line.strip().startswith("python -B tools/")]
        self.assertTrue(any("go2_g_a055_readout.py" in c for c in commands), commands)
        self.assertTrue(any("go2_dial_hypothesis.py G-A055" in c for c in commands), commands)
        self.assertTrue(any("go2_reward_base_comparison.py G-A055" in c for c in commands), commands)


if __name__ == "__main__":
    unittest.main()
