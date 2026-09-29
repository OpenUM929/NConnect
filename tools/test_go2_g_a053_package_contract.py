"""G-A053 패키지 계약 — G-A048 보상 위 목록 밖 항 `dof_acc_l2` -2.5e-07 -> -3e-07 (2026-09-28).

계획 `workspace/training/quadruped/upload/plan/GO2_G_A053_PLAN_20260928.md`, Codex 후보 선택(사용자 중계)
G-D-A053-DOFACC-20260928, 목록 밖 항 허용은 사용자 승인 G-D-U1-APPROVED-20260928.
보상 기준(reward_base)과 목록 밖 항(env_reward_weight)을 함께 쓰는 첫 회차다.

  * 후보는 G-A048 이 **학습한** 보상과 목록 6개가 같고, 목록 밖 한 줄(`dof_acc_l2`)만 더한다.  채택 기준선 G-A033 대비로는
    `lin_vel_z_l2` 와 그 줄이 다르다.
  * 채택 판정(fact_rules_v1 + g3_guard_margin_v1)과 효과 판정(A048 대비)은 G-A051 과 글자 그대로 같다.
  * 배포 report.html 은 이 항을 표시하지 않는다(`go2_task/_finalize.py`).  그래서 서버 env-rewards 검사가 이 항을 대조해야
    한다 — A048 의 학습 env.yaml(-2.5e-07)은 거부되고 -3e-07 은 통과하는 것을 패키지 안의 검사기로 확인한다.
  * 추론 행은 G-A052 진단 재생 증거(COST_PHASES.csv 등) 칸과 글자 그대로 맞는다(발행 빌더가 관문을 돌린다).
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
import go2_open_decisions as decisions  # noqa: E402
import go2_reward_base_comparison as comparison  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

WORK_ID = "G-A053"
SPEC = reward.load(WORK_ID)
PREVIOUS = reward.load("G-A051")
HISTORY = reward.output_path(SPEC)
CURRENT = GO2 / "upload" / WORK_ID / "current"
EDITION = "g3_guard_margin_v1"
A048_KEEP = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125"
A050_KEEP = ROOT / "workspace/_keep/go2_g_a050_a033_lin_vel_z_m1375"
EVIDENCE = GO2 / "reports/evidence/go2_g_a052_diag_20260928"
# 서술 칸, 가설 블록, 필수 기록 문구.  이 밖의 preregistered 칸은 G-A051 과 같아야 한다.
DECLARED = {"source", "threshold_basis", "mechanism_readout", "hypothesis", "plan_screening",
            "required_records", "target_group_roles"}
INDICATORS = SPEC["preregistered"]["hypothesis"]["indicators"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reports_bytes() -> dict[str, str]:
    base = GO2 / "reports"
    return {str(p.relative_to(base)): sha(p.read_bytes()) for p in sorted(base.rglob("*")) if p.is_file()}


class SpecTest(unittest.TestCase):
    def test_1_g_a048s_six_plus_one_unlisted_line(self) -> None:
        release.validate(SPEC)
        self.assertEqual(SPEC["change_class"], reward.ENV_REWARD_CLASS)
        single = SPEC["single_change"]
        self.assertEqual((single["name"], single["from"], single["to"]), ("dof_acc_l2", -2.5e-07, -3e-07))
        self.assertNotIn("dof_acc_l2", reward.REWARD_NAMES)
        rb = SPEC["reward_base"]
        self.assertEqual(rb, PREVIOUS["reward_base"])
        self.assertEqual(reward_dict((ROOT / rb["trained_source"]).read_text(encoding="utf-8")), rb["rewards"])
        rewards = SPEC["rewards"]
        self.assertEqual(rewards["baseline"], PREVIOUS["rewards"]["baseline"])
        self.assertEqual(rewards["candidate"], rb["rewards"])
        self.assertEqual(rewards["baseline_env_extra"], {})
        self.assertEqual(rewards["candidate_env_extra"], {"dof_acc_l2": -3e-07})
        self.assertEqual(SPEC["training"], PREVIOUS["training"])
        self.assertEqual(base_data.spec_problems(SPEC), [])
        self.assertEqual(SPEC["base_data"]["terms"]["dof_acc_l2"]["status"], "OUT_OF_RANGE")
        self.assertEqual(SPEC["base_data"]["walk_margin"]["margin"], 0.126)
        self.assertEqual(SPEC["base_data"]["walk_margin"]["zone"], "WALK")

    def test_1b_the_builder_refuses_a_moved_listed_weight_or_a_wrong_extra(self) -> None:
        moved = json.loads(json.dumps(SPEC))
        moved["rewards"]["candidate"]["action_rate_l2"] = -0.012
        with self.assertRaises(RuntimeError):
            reward.validate_spec(moved)
        wrong = json.loads(json.dumps(SPEC))
        wrong["rewards"]["candidate_env_extra"] = {"dof_acc_l2": -3.5e-07}
        with self.assertRaises(RuntimeError):
            reward.validate_spec(wrong)
        listed = json.loads(json.dumps(SPEC))
        listed["rewards"]["candidate_env_extra"] = {"action_rate_l2": -0.012}
        listed["single_change"].update({"name": "action_rate_l2", "from": -0.01, "to": -0.012})
        with self.assertRaises(RuntimeError):
            reward.validate_spec(listed)
        drifted = json.loads(json.dumps(SPEC))
        drifted["reward_base"]["rewards"]["lin_vel_z_l2"] = -1.375
        drifted["rewards"]["candidate"]["lin_vel_z_l2"] = -1.375
        with self.assertRaises(RuntimeError):
            reward.validate_spec(drifted)

    def test_1c_the_user_approved_the_unlisted_term(self) -> None:
        entry = next(e for e in decisions.DECISIONS if e[0] == "U1-R6-ENV-REWARD-20260918")
        self.assertEqual(entry[8], "APPROVED")
        self.assertIn("G-D-U1-APPROVED-20260928", entry[2])
        self.assertNotIn(reward.ENV_REWARD_CLASS, decisions.by_change_class())
        self.assertIn("G-D-U1-APPROVED-20260928", SPEC["external_reference"]["r6"])
        self.assertIn("report.html shows no change for it", SPEC["notes"]["deployed_list"])

    def test_2_adoption_and_effect_rules_are_g_a051s_unchanged(self) -> None:
        mine, theirs = SPEC["preregistered"], PREVIOUS["preregistered"]
        self.assertEqual(set(mine), set(theirs))
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
        self.assertEqual(SPEC["videos"]["candidate"], PREVIOUS["videos"]["candidate"])
        self.assertEqual(SPEC["videos"]["baseline_reuse"], PREVIOUS["videos"]["baseline_reuse"])

    def test_3_hypothesis_and_codexs_outcomes_are_preregistered(self) -> None:
        block = SPEC["preregistered"]["hypothesis"]
        self.assertIs(block["separate_from_adoption"], True)
        self.assertEqual(set(INDICATORS), {"rough_lateral_posture_falls"})
        rough = INDICATORS["rough_lateral_posture_falls"]
        self.assertEqual((rough["supported_if_at_most"], rough["not_supported_if_at_least"]), (8, 16))
        self.assertEqual(set(block["recorded"]), {"stairs_10_ge2", "stairs_15_ge2"})
        decisions_text = " ".join(block["decisions"])
        for text in ("worse climb or low-posture recovery", "slower or stopped policy", "no automatic stronger or neighbouring value"):
            self.assertIn(text, decisions_text)
        records = SPEC["preregistered"]["required_records"]
        self.assertIn("Episode_Reward/dof_acc_l2", records["dof_acc_cost_training"])
        self.assertIn("C-39", records["fall_channel_split"])
        plan = (ROOT / SPEC["plan"]).read_text(encoding="utf-8")
        for text in ("**SUPPORTED ≤ 8**", "**NOT_SUPPORTED ≥ 16**", "≥ 0.164 m/s", "G-D-U1-APPROVED-20260928",
                     "2배 강화는 걷기 margin 경계에 거의 닿으므로 제외한다", "−0.12456", "−0.14622",
                     "더 강한 값이나 인접값을 자동으로 반복하지 않는다"):
            with self.subTest(text=text):
                self.assertIn(text, plan)

    def test_4_the_inference_rows_are_the_diagnostic_evidence(self) -> None:
        rows = SPEC["inference"]["rows"] + SPEC["inference"]["contradicting"]
        sources = {row["source"] for row in rows}
        self.assertIn("reports/evidence/go2_g_a052_diag_20260928/COST_PHASES.csv", sources)
        self.assertIn("reports/evidence/go2_g_a052_diag_20260928/CASE_COST_SUMMARY.csv", sources)
        self.assertTrue(any(s.startswith("reports/runs/") for s in (r["source"] for r in SPEC["inference"]["rows"])))
        keys = {row["key"] for row in SPEC["inference"]["contradicting"]}
        self.assertIn("stairs_15_down|rew_dof_acc_l2", keys)
        self.assertIn("A048", keys)
        for name in ("COST_PHASES.csv", "CASE_COST_SUMMARY.csv", "TORQUE_BY_HEIGHT.csv"):
            self.assertTrue((EVIDENCE / name).is_file(), name)

    def test_5_the_reader_judges_the_a048_relative_line(self) -> None:
        seeds = lambda values: dict(zip(("101", "202", "303"), values))
        for values, want in (((3, 3, 2), "SUPPORTED"), ((3, 3, 3), "INSUFFICIENT"), ((5, 8, 3), "NOT_SUPPORTED")):
            with self.subTest(values=values):
                self.assertEqual(hypothesis.judge(INDICATORS["rough_lateral_posture_falls"], seeds(values))[0], want)

    def test_5b_the_effect_reader_reproduces_the_a050_comparison(self) -> None:
        if not (A050_KEEP.is_dir() and A048_KEEP.is_dir()):
            self.skipTest("저장된 수확물이 이 PC 에 없다")
        result = comparison.compare(SPEC, A050_KEEP, verify=False)
        self.assertEqual(result["total_70"]["delta"], -2.90202)
        self.assertEqual(result["verdict"], "NOT_REVIEW_CANDIDATE")
        self.assertIn("not a final progress verdict", result["verdict_scope"])

    def test_5c_an_unverified_harvest_gets_no_progress_verdict(self) -> None:
        if not A048_KEEP.is_dir():
            self.skipTest("저장된 수확물이 이 PC 에 없다")
        self.assertEqual(comparison.compare(SPEC, A048_KEEP)["verdict"], "INCONCLUSIVE")

    def test_6_exploratory_and_selection_owner_recorded(self) -> None:
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        self.assertIn("Not a promise of a higher score", SPEC["why"][0])
        self.assertIn("no data says 20 percent beats 10 or 25 percent", SPEC["value_derivation"]["rule"])
        self.assertIn("result of terrain contact rather than its cause", SPEC["value_derivation"]["not_claimed"])
        self.assertIn("Selection responsibility stays with Codex", SPEC["decision_ref"])
        self.assertIn("not an adoption PASS", SPEC["preregistered"]["mechanism_readout"])


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

    def test_8_one_added_weight_line_against_g_a048(self) -> None:
        cand = self.lines("candidate/quadruped_rewards.py")
        base48 = self.lines("reference/reward_base_quadruped_rewards.py")
        base33 = self.lines("reference/baseline_quadruped_rewards.py")
        removed48 = [line for line in base48 if line not in cand]
        added48 = [line for line in cand if line not in base48]
        self.assertEqual(removed48, [])
        weight_lines = [line for line in added48 if line.strip().startswith('"')]
        self.assertEqual(weight_lines, ['    "dof_acc_l2": -3e-07,'])
        self.assertEqual(reward_dict("\n".join(cand)), {**SPEC["rewards"]["candidate"], "dof_acc_l2": -3e-07})
        self.assertEqual(reward_dict("\n".join(base48)), SPEC["reward_base"]["rewards"])
        self.assertEqual(reward_dict("\n".join(base33)), SPEC["rewards"]["baseline"])
        self.assertEqual(self.member("baseline/quadruped_rewards.py"), self.member("reference/baseline_quadruped_rewards.py"))

    def test_9_the_runner_is_the_repository_runner_and_the_config_pins_the_full_run(self) -> None:
        runner = self.member(SPEC["runner"])
        self.assertEqual(runner, (GO2 / SPEC["runner"]).read_bytes())
        self.assertNotIn(b"\r", runner)
        done = subprocess.run(["bash", "-n"], input=runner, capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = self.member("run_config.env").decode("utf-8")
        self.assertNotIn("\r", config)
        for line in ("GO2_STAGE=full\n", "COLLECT_REQUIRED_ON_STATIONARY=1\n", "SINGLE_CHANGE_NAME=dof_acc_l2\n",
                     "SINGLE_CHANGE_TO=-3e-07\n", "TRAIN_SEED=42\n", "BASELINE_VIDEOS=()\n", "WORK_ID=G-A053\n"):
            self.assertIn(line, config)

    def test_9b_the_server_check_catches_an_unapplied_unlisted_weight(self) -> None:
        """배포 report.html 은 이 항을 보여 주지 않는다 — 서버 env-rewards 검사가 유일한 서버쪽 증거다."""
        expected = json.loads(self.member("expected_rewards.json").decode("utf-8"))
        self.assertEqual(expected["candidate"], {**SPEC["rewards"]["candidate"], "dof_acc_l2": -3e-07})
        trained = A048_KEEP / "training" / "env.yaml"
        if not trained.is_file():
            self.skipTest("대역 env.yaml(G-A048)이 이 PC 에 없다")
        text = trained.read_text(encoding="utf-8")
        head = text.index("  dof_acc_l2:")
        weight = text.index("weight:", head)
        end = text.index("\n", weight)
        self.assertEqual(text[weight:end], "weight: -2.5e-07")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "candidate_suite_checks.py").write_bytes(self.member("candidate_suite_checks.py"))
            (tmp / "expected_rewards.json").write_bytes(self.member("expected_rewards.json"))
            (tmp / "a048.yaml").write_text(text, encoding="utf-8")
            (tmp / "applied.yaml").write_text(text[:weight] + "weight: -3.0e-07" + text[end:], encoding="utf-8")
            for env, rc in (("a048.yaml", 1), ("applied.yaml", 0)):
                with self.subTest(env=env):
                    done = subprocess.run([sys.executable, "candidate_suite_checks.py", "env-rewards", env,
                                           "expected_rewards.json", "candidate"], cwd=tmp, capture_output=True, text=True)
                    self.assertEqual(done.returncode, rc, done.stdout + done.stderr)
            self.assertIn("dof_acc_l2=-2.5e-07 expected -3e-07", done.stderr if rc else subprocess.run(
                [sys.executable, "candidate_suite_checks.py", "env-rewards", "a048.yaml", "expected_rewards.json",
                 "candidate"], cwd=tmp, capture_output=True, text=True).stderr)


class GuideTest(unittest.TestCase):
    def test_10_the_guide_commands_run_and_write_nothing_tracked(self) -> None:
        if not CURRENT.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (CURRENT / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn(sha(HISTORY.read_bytes()), guide)
        self.assertIn("G-A048 보상 위에서 dof_acc_l2 -2.5e-07 -> -3e-07", guide)
        self.assertIn("배포 report.html 의 보상 변화 표에는 이 변경이 나오지 않는다", guide)
        self.assertIn("최종 진보 판정이 아니다", guide)
        joined = guide.replace("\\\n", " ")
        commands = [line.strip() for line in joined.splitlines() if line.strip().startswith("python -B tools/")]
        self.assertEqual(len(commands), 4, commands)
        self.assertIn(f"--rule-version {EDITION}", commands[1])
        self.assertIn("go2_dial_hypothesis.py G-A053", commands[2])
        self.assertIn("go2_reward_base_comparison.py G-A053", commands[3])
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

    EXPECTED = ("work_id=", "train_single_change=", "env_reward_dof_acc_l2=")

    def test_11_the_verifier_reaches_a_verdict_and_checks_the_unlisted_weight(self) -> None:
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
        # A048 은 dof_acc_l2 -2.5e-07 로 학습했으므로 -3e-07 대조가 걸려야 하고, 목록 6개는 통과해야 한다.
        self.assertTrue(any(f.startswith("env_reward_dof_acc_l2=") for f in dropped), dropped)
        self.assertFalse(any(f.startswith("env_reward_lin_vel_z_l2=") for f in dropped), dropped)
        self.assertEqual(report["combined_verdict"]["artifact"], "ARTIFACT_VERIFIED")
        self.assertIn(EDITION, report["plan_screening"]["rule"])
        guard = [c["check"] for c in report["plan_screening"]["checks"] if c["group"] == "guard"]
        self.assertEqual(len(guard), 14)
        self.assertIn(report["verdict"], ("PASS", "FAIL", "QUANT_SUCCESS_VIDEO_REVIEW_PENDING"))


if __name__ == "__main__":
    unittest.main()
