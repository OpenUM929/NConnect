"""Contract for the G-A042 one-command campaign (G-A033 + track_lin_vel_xy_exp 1.5 -> 1.6).  Local only.

A package is not ready until the code that will read its harvest has run on one (memory rule
"준비 완료 = 판독 코드를 돌려봤다").  So besides what the builder writes, these tests run the server
gate and the local verifier on synthetic harvests shaped like the runner's output, and they run the
two new readers on the real G-A033 and G-A041 harvests.

What is new in this arm, and what these tests pin down:
  This is the first package built from a user plan (upload/plan/GO2_FORWARD_STAIRS_POLICY_20260921.md,
  decision G-D-FORWARD-STAIRS-20260921) rather than from an audit of our own.  Three things in it
  have never existed before and each has a test here:
    - preregistered.required_target_cases: 15 cm is measured in stage 1 and excluded from the
      server allocation score, but binding in local plan screening (defect C-5, test_13);
    - videos.baseline_reuse: three of the four baseline videos already exist and are reused by SHA
      with their runner fingerprint recomputed, so four cases are filmed on both arms while only one
      baseline video is rendered (test_15);
    - the release states the number of cases it measures instead of the constant 9 that shipped with
      G-A041 (defect C-4, test_14).
  A017->A033 is one direct checkpoint900/900 comparison; Pilot->A017 (999/900) is auxiliary,
  not identical-condition replication. Lateral loss is observed, not an exclusive causal source.

    python -m unittest tools.test_go2_g_a042_campaign_contract
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import re
import shutil
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
import build_go2_campaign_package as g_a033_campaign  # noqa: E402
import build_go2_training_length_campaign as build  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402
import go2_fact_rules as fact  # noqa: E402
import go2_fact_rules_spec as rules  # noqa: E402
import go2_reward_mechanism as mech  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import go2_stall_diagnostics as stall  # noqa: E402
import go2_target_gate as gate  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict  # noqa: E402

CAMPAIGN_ID = "G-A042"
SPEC = reward.load(CAMPAIGN_ID)
BASE = SPEC["baseline"]
TERM = SPEC["single_change"]["name"]
STORED_ARM = ROOT / BASE["stored_arm"]
A017_ARM = ROOT / "workspace" / "_keep" / "go2_a017_full_suite" / "evaluation" / "a017"
A041_ARM = ROOT / "workspace" / "_keep" / "go2_g_a041_a033_ang_vel_xy_m004"
PAYLOAD = build.build_payload(CAMPAIGN_ID)
ARM = reward.build_payload(SPEC)
REGISTRY = json.loads(ARM["go2_self_eval_registry.json"].decode("utf-8"))
CAMP = build.CAMPAIGNS[CAMPAIGN_ID]
REQUIRED = SPEC["preregistered"]["required_target_cases"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PackageTest(unittest.TestCase):
    def test_1_build_is_reproducible_and_published(self) -> None:
        self.assertEqual(build.build_payload(CAMPAIGN_ID), PAYLOAD)
        current = GO2 / "upload" / CAMP["upload_id"] / "current" / CAMP["upload_zip"]
        with zipfile.ZipFile(current) as archive:
            shipped = {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()}
        # Hash values rather than rendering megabytes of binary diffs on a stale release.
        self.assertEqual({k: sha(v) for k, v in shipped.items()},
                         {k: sha(v) for k, v in PAYLOAD.items()}, "the published ZIP is not this build")
        digest = sha(current.read_bytes())
        self.assertIn(digest, (current.parent / "CURRENT_UPLOAD.txt").read_text(encoding="utf-8"))
        self.assertIn(digest, (current.parent / CAMP["guide"]).read_text(encoding="utf-8"))
        manifest = json.loads((current.parent / "UPLOAD_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["published_at_utc"], CAMP["published_at"])
        self.assertEqual(manifest["upload_files"][0]["sha256"], digest)

    def test_2_the_release_note_does_not_claim_a_history_it_does_not_have(self) -> None:
        note = (GO2 / "upload" / CAMP["upload_id"] / "current" / "CURRENT_UPLOAD.txt").read_text(encoding="utf-8")
        self.assertNotIn("옛 판정 규칙", note)
        self.assertNotIn("러너 결함", note)
        self.assertNotIn("supersede_note", CAMP, "이 회차는 대체한 판이 없다")

    def test_3_campaign_runner_and_gate_are_what_ran_for_g_a033(self) -> None:
        released = g_a033_campaign.output_path(g_a033_campaign.CAMPAIGNS["G-A033"])
        with zipfile.ZipFile(released) as archive:
            prefix = g_a033_campaign.CAMPAIGNS["G-A033"]["prefix"]
            self.assertEqual(PAYLOAD[build.RUNNER], archive.read(f"{prefix}/{build.RUNNER}"))
        # 2026-09-24 (defect C-32): 이 회차는 2026-09-22 에 러너가 고정됐다(C-14).  고정된 회차의
        # 팔은 정의상 작업본이 아니라 **자기가 돌았던 바이트**를 싣는다 — 작업본과의 동일성을 묻던
        # 옛 단정은 고정이 생긴 날부터 거짓이었다.  물어야 할 것은 발행 바이트와의 동일성이다.
        cand = reward.length.cand
        self.assertIn((SPEC["work_id"], SPEC["output"]["release_id"]), cand.EXECUTED_RUNNERS,
                      "고정이 사라지면 이 발행 ZIP 이 재빌드되지 않는다")
        self.assertEqual(ARM[SPEC["runner"]], cand.runner_bytes(SPEC))

    def test_4_exactly_one_reward_number_moves(self) -> None:
        candidate = ARM["candidate/quadruped_rewards.py"].decode("utf-8")
        reference = ARM["reference/baseline_quadruped_rewards.py"].decode("utf-8")
        self.assertIn(TERM, REWARD_NAMES, "a listed name must use change_class reward_weight")
        moved = [name for name in REWARD_NAMES
                 if reward_dict(candidate)[name] != reward_dict(reference)[name]]
        self.assertEqual(moved, [TERM])
        self.assertEqual(reward_dict(candidate)[TERM], 1.6)
        self.assertEqual(reward_dict(reference)[TERM], 1.5)
        trained = reward.BASELINE_SOURCE / "source" / "quadruped_rewards.py"
        self.assertEqual(reward_dict(reference), reward_dict(trained.read_text(encoding="utf-8")),
                         "the reference must be the reward file G-A033 was trained with")
        config = ARM["run_config.env"].decode("utf-8")
        for line in (f"SINGLE_CHANGE_NAME={TERM}", "SINGLE_CHANGE_FROM=1.5", "SINGLE_CHANGE_TO=1.6",
                     "TRAIN_SEED=42", "NUM_ENVS=4096", "MAX_ITERATIONS=1000", "EVAL_CHECKPOINT_ITER=900",
                     "BASELINE_LABEL=g_a033"):
            self.assertIn(line + "\n", config)

    def test_5_arm_is_the_builder_output_and_launches_nothing_missing(self) -> None:
        name = f"arms/{SPEC['output']['upload_zip']}"
        self.assertEqual(PAYLOAD[name], reward.build_zip(SPEC))
        self.assertIn(sha(PAYLOAD[name]), PAYLOAD["campaign_config.env"].decode("utf-8"))
        shipped = {k: v for k, v in PAYLOAD.items() if not k.startswith("arms/")}
        self.assertEqual(build.unreachable_scripts(shipped, ARM, SPEC["runner"]), [])

    def test_6_the_value_is_outside_the_observed_range_and_says_so(self) -> None:
        self.assertEqual(base_data.spec_problems(SPEC), [])
        self.assertEqual(base_data.walking_values(TERM), [1.2, 1.4, 1.5],
                         "no walking run has trained another value for this term")
        declared = SPEC["base_data"]["terms"][TERM]
        self.assertEqual(declared["status"], "OUT_OF_RANGE")
        self.assertGreaterEqual(len(declared["out_of_range_reason"]), 20)
        probes = {(r["term"], r["to"]): r for r in mech.read("PROBES.csv")}
        row = probes[(TERM, "1.6")]
        self.assertEqual((row["zone"], row["range_status"]), ("WALK", "OUT_OF_RANGE"))
        self.assertGreater(float(row["margin"]), float(row["margin_from"]))
        self.assertIn(row["margin"], SPEC["value_derivation"]["walk_margin"])

    def test_7_the_forecast_is_recorded_and_the_measurement_overrules_it(self) -> None:
        """네 칸이 전부 양수라 이 팔에는 모델이 예측하는 손실이 없다 — 그래서 측정을 싣는다."""
        situ = {(r["term"], r["to"]): r for r in mech.read("PROBE_SITUATIONS.csv")}[(TERM, "1.6")]
        for column in ("walk_delta", "climb_delta", "sway_delta", "push_delta"):
            self.assertTrue(situ[column].strip(), column)
            self.assertGreater(float(situ[column]), 0.0, f"{column} is no longer positive")
        predictions = SPEC["inference"]["predictions"]
        for situation in ("walk", "climb", "sway", "push"):
            self.assertEqual(predictions[situation]["direction"], "up", situation)
        # 모델이 '좋아진다'고 적은 흔들림 칸은 실측과 반대다.  그 반대 행이 사양에 있어야 한다.
        adverse = [row for row in SPEC["inference"]["contradicting"] if "rough_lateral" in row["key"]]
        self.assertTrue(adverse, "the measured side-step loss row is missing")
        # 근거는 원자료의 **한 레코드**다(seed 202). 세 seed 합 48 -> 58 은 그 행을 읽은 문장에 있다.
        self.assertEqual(adverse[0]["selector"]["seed"], "202")
        self.assertEqual(adverse[0]["cells"], {"terminated_env_count": "20", "fallen_env_count": "15"})
        self.assertIn("48 -> 58", adverse[0]["reads"])
        self.assertIn("A017->A033 (900/900)", predictions["sway"]["basis"],
                      "흔들림 예측은 반대 실측을 함께 적어야 한다")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")

    def test_8_no_other_lever_moved_and_each_says_why(self) -> None:
        base, cand = SPEC["rewards"]["baseline"], SPEC["rewards"]["candidate"]
        for name in REWARD_NAMES:
            with self.subTest(name):
                if name == TERM:
                    self.assertNotEqual(base[name], cand[name])
                    continue
                self.assertEqual(base[name], cand[name])
                self.assertIn(name, SPEC["rejected_alternatives"])
        for name in ("dof_acc_l2", "max_iterations", "training_seed"):
            self.assertIn(name, SPEC["rejected_alternatives"])

    def test_9_the_measured_loss_is_measured_in_stage_one(self) -> None:
        groups = SPEC["preregistered"]["target_groups"]
        self.assertEqual(set(groups), {"stairs", "rough", "push"})
        self.assertEqual(len(groups["rough"]), 6, "G3 축은 6쌍 전수가 있어야 점수가 생긴다")
        self.assertTrue(all(e.startswith("G3:") for e in groups["rough"]))
        floors = SPEC["preregistered"]["target_group_floor"]
        self.assertEqual(set(floors), set(groups))
        for name, floor in floors.items():
            self.assertLess(float(floor), 0.0, name)
        with (GO2 / "reports/runs/BASELINE_MARGIN.csv").open(encoding="utf-8") as handle:
            sd = {r["scenario"]: float(r["value"]) for r in csv.DictReader(handle)
                  if r["metric"] == "delta_resample_sd"}
        limits = SPEC["preregistered"]["max_scenario_weighted_loss_70_by_scenario"]
        for scenario, limit in limits.items():
            with self.subTest(scenario):
                self.assertAlmostEqual(limit, 2 * sd[scenario], places=5)
        # 한도는 손으로 적지 않는다 — G-A033 원시 기록에서 다시 계산해 대조한다.
        generated = rules.rules_for(SPEC)
        self.assertEqual(SPEC["preregistered"]["target_group_floor"], generated["target_group_floor"])
        self.assertEqual(SPEC["preregistered"]["max_scenario_weighted_loss_70_by_scenario"],
                         generated["max_scenario_weighted_loss_70_by_scenario"])

    def test_10_every_climb_guard_can_actually_fire(self) -> None:
        """결함 S-2: 하한이 0 이하인 관문은 어떤 결과도 막지 못한다 — 그래서 싣지 않는다."""
        guard = SPEC["preregistered"]["climb_guard"]["groups"]
        self.assertEqual(set(guard), {"stairs_10_climb_ge1", "stairs_10_climb_ge2"})
        for name, group in guard.items():
            with self.subTest(name):
                self.assertEqual(group["baseline_sum"], sum(group["baseline_counts"]))
                self.assertGreater(float(group["baseline_sum"]) - float(group["max_drop"]), 0.0)
        omitted = str(SPEC["preregistered"]["climb_guard"].get("omitted", ""))
        self.assertIn("stairs_15_climb_ge1", omitted)
        # 뺀 관문이 '측정도 안 한다'로 읽히면 안 된다 — 15cm 는 1단계에서 잰다.
        self.assertIn("stage 1", omitted)
        self.assertEqual(SPEC["preregistered"]["rule_version"], fact.RULE_VERSION)
        self.assertIn("G3", SPEC["inference"]["risk_axes"])

    def test_11_the_isaac_lab_anchor_is_left_and_the_spec_says_why(self) -> None:
        rewards = json.loads((GO2 / "config/go2_external_reference.json").read_text(encoding="utf-8"))
        rewards = rewards["isaaclab"]["rewards"]
        self.assertEqual(rewards["go2_rough"][TERM], SPEC["single_change"]["from"],
                         "the frozen baseline sits exactly on the Isaac Lab Go2 rough value")
        self.assertNotEqual(SPEC["single_change"]["to"], SPEC["external_reference"]["isaaclab_go2_rough"])
        self.assertTrue(str(SPEC["external_reference"]["departure_reason"]).strip())
        deployed = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
        self.assertIn("추천 0.5 ~ 2.0", deployed)
        # 배포 파일이 이 방향을 스스로 경고한다.  그 경고가 반대 행으로 실려 있어야 한다.
        self.assertIn("너무 높이면", deployed)
        self.assertTrue([row for row in SPEC["inference"]["contradicting"]
                         if "너무 높이면" in row["key"]], "the deployed warning row is missing")

    def test_12_the_earlier_releases_are_untouched(self) -> None:
        """이 회차가 앞 회차의 발행물을 건드리지 않았다 (ZIP 과 안내문 둘 다)."""
        self.assertIn(CAMPAIGN_ID, verifier.SPECS)
        self.assertEqual(verifier.load_spec(CAMPAIGN_ID), SPEC)
        known_diverged = {"G-A035", "G-A037", "G-A039"}   # 결함 C-2, reports/GO2_DEFECT_LEDGER.md
        diverged = set()
        for work_id in ("G-A035", "G-A037", "G-A038", "G-A039", "G-A041"):
            with self.subTest(work_id):
                camp = build.CAMPAIGNS[work_id]
                current = GO2 / "upload" / camp["upload_id"] / "current"
                digest = sha((current / camp["upload_zip"]).read_bytes())
                self.assertEqual(build.run_guide(work_id, digest).encode("utf-8"),
                                 (current / camp["guide"]).read_bytes(),
                                 "안내문 서식을 고치면서 발행된 판의 바이트가 바뀌었다")
                with zipfile.ZipFile(current / camp["upload_zip"]) as archive:
                    shipped = {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()}
                try:
                    rebuilt = build.build_payload(work_id)
                except RuntimeError as error:
                    self.assertIn("differs from a rebuild", str(error))
                    diverged.add(work_id)
                    continue
                self.assertEqual(shipped, rebuilt)
        self.assertEqual(diverged, known_diverged,
                         "결함 C-2 의 범위가 바뀌었다 — 고쳤으면 known_diverged 를 줄이고, "
                         "늘었으면 이 회차가 앞 회차의 발행물을 건드린 것이다")

    def test_13_the_15cm_records_are_measured_before_the_gate_decides(self) -> None:
        """결함 C-5: G-A041 은 15cm 를 '필수 기록'이라 적고 2단계에 뒀다가 통째로 잃었다."""
        scored = length.targets(SPEC)
        measured = reward.targets(SPEC)
        self.assertEqual(len(scored), 12)
        self.assertEqual(REQUIRED[:3], ["G5:stairs_15_down:101", "G5:stairs_15_down:202",
                                        "G5:stairs_15_down:303"], "15cm 세 seed가 먼저 온다")
        # 계획 §4 의 초기 보호 표지: 평지 좌·우와 표적이 아닌 밀침 세 방향 (평지 전진은 파국 case).
        self.assertEqual(REQUIRED[3:], ["G2:left:101", "G2:right:101",
                                        "G6:push_neg_x:101", "G6:push_pos_y:101", "G6:push_neg_y:101"])
        self.assertEqual(SPEC["evaluation"]["catastrophe_case"], "G1:forward_nominal:101",
                         "평지 전진은 파국 case 로 이미 재고 있다")
        self.assertEqual(measured, [*scored, *REQUIRED], "required records must follow the scored targets")
        self.assertFalse(set(REQUIRED) & set(scored), "a required record must not be scored twice")
        # 러너는 이 목록을 잰다 (run_config.env 의 TARGET_CASES).
        config = ARM["run_config.env"].decode("utf-8")
        line = next(l for l in config.splitlines() if l.startswith("TARGET_CASES="))
        for entry in REQUIRED:
            self.assertIn(entry, line)
        # 서버 게이트는 이 case 들을 채점하지 않는다.
        self.assertEqual(gate.targets(SPEC), scored)
        for entry in REQUIRED:
            self.assertNotIn(entry, str(SPEC["preregistered"]["target_groups"]))
        # 그리고 G-A041 에서 실제로 사라진 자리가 여기다.
        for seed in ("101", "202", "303"):
            self.assertFalse((A041_ARM / "evaluation/candidate/cases" / f"seed_{seed}"
                              / "stairs_15_down" / "summary.json").is_file(),
                             "G-A041 이 15cm 를 회수했다면 이 결함의 전제가 바뀐 것이다")
        self.assertGreaterEqual(len(SPEC["preregistered"]["required_target_cases_reason"]), 40)

    def test_14_the_release_states_the_number_of_cases_it_measures(self) -> None:
        """결함 C-4: 표적 case 수가 상수 9 로 박혀 있어 G-A041 이 12 를 재면서 9 라고 발행됐다."""
        readme = PAYLOAD["README.txt"].decode("utf-8")
        guide = build.run_guide(CAMPAIGN_ID, "0" * 64)
        self.assertIn("the 20 target cases", readme)
        self.assertIn("표적 20 case", guide)
        self.assertIn("표적 12 case proxy 평균", guide, "게이트가 채점하는 수는 1단계가 재는 수와 다르다")
        self.assertEqual(build.target_case_count(CAMP, SPEC), len(reward.targets(SPEC)))
        self.assertEqual(build.scored_case_count(CAMP, SPEC), len(length.targets(SPEC)))
        self.assertEqual(build.FROZEN_TARGET_COUNT, {"G-A041": 9},
                         "얼려 둔 수는 이미 실행된 G-A041 하나뿐이어야 한다")

    def test_15_four_cases_are_filmed_on_both_arms_and_only_one_is_rendered(self) -> None:
        videos = SPEC["videos"]
        self.assertEqual(videos["candidate"], ["G5:stairs_10_down:101", "G5:stairs_15_down:101",
                                               "G3:rough_forward:101", "G3:rough_lateral:101"])
        self.assertEqual(videos["baseline"], ["G5:stairs_15_down:101"], "한 개만 새로 찍는다")
        reuse = videos["baseline_reuse"]
        self.assertEqual(set(reuse) | set(videos["baseline"]), set(videos["candidate"]),
                         "네 case 모두 기준선 짝이 있어야 한다")
        self.assertEqual(length.reuse_problems(SPEC), [])
        for entry, row in reuse.items():
            with self.subTest(entry):
                path = ROOT / row["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(sha(path.read_bytes()), row["sha256"])
                # 이름이 아니라 지문이 '그 정책의 그 조건'을 증명한다.
                self.assertEqual(row["identity_sha256"], length.video_fingerprint(SPEC, entry))
        tampered = copy.deepcopy(SPEC)
        first = next(iter(tampered["videos"]["baseline_reuse"]))
        tampered["videos"]["baseline_reuse"][first]["sha256"] = "0" * 64
        self.assertTrue(length.reuse_problems(tampered), "바뀐 파일이 통과하면 재사용은 근거가 아니다")

    def test_16_a_second_reward_change_is_refused(self) -> None:
        broken = copy.deepcopy(SPEC)
        broken["rewards"]["candidate"]["lin_vel_z_l2"] = -1.0
        with self.assertRaises(RuntimeError) as caught:
            reward.validate_spec(broken)
        self.assertIn("exactly the single_change reward must differ", str(caught.exception))

    def test_17_a_required_record_that_is_also_scored_is_refused(self) -> None:
        broken = copy.deepcopy(SPEC)
        broken["preregistered"]["required_target_cases"] = ["G5:stairs_10_down:101"]
        with self.assertRaises(RuntimeError) as caught:
            reward.validate_spec(broken)
        self.assertIn("must not also be a scored target", str(caught.exception))


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir() and A017_ARM.is_dir(),
                     "G-A033 or A017 harvest not present")
class GateAndVerifierTest(unittest.TestCase):
    """The server gate and the verifier of record read a G-A042 harvest the same way."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.stored = Path(cls.tmp.name) / "campaign" / "stored_baseline"
        for name, data in PAYLOAD.items():
            if name.startswith("stored_baseline/"):
                target = Path(cls.tmp.name) / "campaign" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    @staticmethod
    def copy_cases(source: Path, out: Path, entries: list[str], model_sha: str,
                   env_sha: str = BASE['env_sha256']) -> None:
        for entry in entries:
            _scenario, case_id, seed = entry.split(":")
            shutil.copytree(source / "cases" / f"seed_{seed}" / case_id, out / "cases" / f"seed_{seed}" / case_id)
        (out / "identity.json").write_text(json.dumps({
            "model_sha256": model_sha, "env_sha256": env_sha, "evaluator_sha256": BASE["evaluator_sha256"],
            "registry_sha256": BASE["registry_sha256"]}), encoding="utf-8")

    @staticmethod
    def candidate_env() -> str:
        """G-A033's env.yaml with the one weight the runner's training would have written."""
        text = (STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8")
        patched, count = re.subn(rf"(\n  {TERM}:\n(?:    .*\n)*?    weight: )1\.5\n", r"\g<1>1.6\n", text)
        assert count == 1, f"{TERM} weight line not found exactly once"
        return patched

    def harvest(self, name: str) -> Path:
        keep = Path(self.tmp.name) / name
        model = b"synthetic G-A042 model"
        model_sha = sha(model)
        single = SPEC["single_change"]
        files = {
            "RESULT_STATUS.txt": "RESULT_STATE=FULL\n",
            "exported/report.html": "<html>synthetic</html>\n",
            "exported/REPORT_STATUS.txt": "REPORT_STATUS=REPORT_ACQUIRED\n",
            "training/TRAIN_STATUS.txt": f"TRAIN_RC=0\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS=1000\n"
                                         f"SINGLE_CHANGE={single['name']}:{single['from']}->{single['to']}\n",
            "training/env.yaml": self.candidate_env(),
            "training/CHECKPOINT_PIN.txt": f"EVAL_CHECKPOINT_ITER=900\nEVAL_CHECKPOINT_SHA={model_sha}\n"
                                           f"REWARD_BEST_MODEL_ITER=950\nREWARD_BEST_MODEL_SHA={'0' * 64}\n",
            "meta/evaluator.sha256": f"{BASE['evaluator_sha256']}  go2_eval_telemetry.py\n",
            "meta/registry.sha256": f"{BASE['registry_sha256']}  go2_self_eval_registry.json\n",
        }
        for rel, content in files.items():
            (keep / rel).parent.mkdir(parents=True, exist_ok=True)
            (keep / rel).write_text(content, encoding="utf-8", newline="\n")
        (keep / "training" / "model_best.pt").write_bytes(model)
        report = (keep / "exported" / "report.html").read_bytes()
        (keep / "exported" / "report.html.sha256").write_text(f"{sha(report)}  report.html\n")
        (keep / "RUNNER_STATUS.txt").write_text(
            f"RUNNER_RC=0\nWORK_ID={CAMPAIGN_ID}\nDECISION=TARGET_STAGE_COMPLETE\nCANDIDATE_MODEL_SHA={model_sha}\n"
            f"STAGE=target\nCANDIDATE_EVAL_ITER=900\n", encoding="utf-8")
        stored = STORED_ARM / "evaluation" / BASE["stored_label"]
        self.copy_cases(stored, keep / "evaluation" / "candidate",
                        [SPEC["evaluation"]["catastrophe_case"], *reward.targets(SPEC)], model_sha,
                        sha(self.candidate_env().encode('utf-8')))
        self.copy_cases(stored, keep / "evaluation" / f"{BASE['label']}_sentinel",
                        SPEC["evaluation"]["sentinel_cases"], BASE["model_sha256"])
        (keep / "SHA256SUMS.txt").write_text(f"{sha(report)}  ./exported/report.html\n")
        return keep

    def test_1_no_change_fails_against_the_stored_baseline_in_both_readers(self) -> None:
        keep = self.harvest("same")
        server = gate.gate(keep, self.stored, SPEC, REGISTRY)
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["artifact_faults"], [])
        self.assertEqual(server.get("faults", []), [])
        self.assertEqual((server["baseline_arm"], local["baseline_arm"]), ("STORED_G-A033", "STORED_G-A033"))
        self.assertTrue(server["sentinel"]["agrees"])
        self.assertEqual((server["verdict"], local["verdict"]), ("FAIL", "FAIL"))
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0, places=12)

    def test_2_the_extra_records_are_measured_and_not_scored(self) -> None:
        """1단계 수확물에 15cm 가 들어 있어도 게이트의 판정 수는 12 case 그대로다."""
        keep = self.harvest("records")
        for entry in REQUIRED:
            _scenario, case_id, seed = entry.split(":")
            self.assertTrue((keep / "evaluation/candidate/cases" / f"seed_{seed}" / case_id
                             / "summary.json").is_file())
        server = gate.gate(keep, self.stored, SPEC, REGISTRY)
        self.assertEqual(server.get("faults", []), [])
        scored = [row["case"] for group in server["target_stage"]["target_groups"] for row in group["rows"]]
        self.assertEqual(sorted(scored), sorted(length.targets(SPEC)))
        for entry in REQUIRED:
            self.assertNotIn(entry, scored)
        # 15cm 오르기 관문은 사양에 없으므로 게이트가 보류하지도, 위반을 만들지도 않는다.
        self.assertEqual(sorted(server["target_stage"]["climb_guard"]["groups"], key=lambda g: g["group"])[0]["group"],
                         "stairs_10_climb_ge1")
        self.assertEqual(server["target_stage"]["climb_guard"]["violations"], [])

    def test_3_a_real_difference_is_read_identically(self) -> None:
        keep = self.harvest("differ")
        self.copy_cases(A017_ARM, keep / "evaluation" / BASE["label"],
                        [SPEC["evaluation"]["catastrophe_case"], *reward.targets(SPEC)], BASE["model_sha256"])
        (keep / 'policy').mkdir(exist_ok=True)
        shutil.copy2(STORED_ARM / 'training/model_best.pt', keep / 'policy/baseline_model_best.pt')
        shutil.copy2(STORED_ARM / 'training/env.yaml', keep / 'policy/baseline_env.yaml')
        server = gate.gate(keep, self.stored, SPEC, REGISTRY)
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual((server["baseline_arm"], local["baseline_arm"]),
                         ("REMEASURED_SAME_RUN", "REMEASURED_SAME_RUN"))
        self.assertNotAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0, places=6)
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"],
                               local["target_stage"]["target_mean_proxy_delta"], places=12)
        expected = {"TARGET_PASS": "TARGET_PASS_FULL_STAGE_REQUIRED", "FAIL": "FAIL"}[server["verdict"]]
        self.assertEqual(local['combined_verdict']['fact_rules'], expected)
        self.assertEqual(local['verdict'], local['combined_verdict']['verdict'])

    def test_4_a_wrong_trained_weight_is_caught(self) -> None:
        """The whole arm rests on the trained env carrying 1.6; the stored baseline carries 1.5."""
        keep = self.harvest("wrong_weight")
        (keep / "training" / "env.yaml").write_text(
            (STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["verdict"], "INCONCLUSIVE")
        self.assertTrue(any(f.startswith(f"env_reward_{TERM}") for f in local["artifact_faults"]),
                        local["artifact_faults"])

    def test_5_a_missing_target_case_is_never_a_verdict(self) -> None:
        keep = self.harvest("missing")
        entry = reward.targets(SPEC)[0]
        _scenario, case_id, seed = entry.split(":")
        shutil.rmtree(keep / "evaluation" / "candidate" / "cases" / f"seed_{seed}" / case_id)
        self.assertEqual(gate.gate(keep, self.stored, SPEC, REGISTRY)["verdict"], "UNDECIDED")
        self.assertEqual(verifier.verify(keep, STORED_ARM, SPEC)["verdict"], "INCONCLUSIVE")


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir(),
                     "G-A033 harvest not present")
class PlanReadersTest(unittest.TestCase):
    """계획 §4의 두 판독기를 **실제 수확물**에 돌려 본다 — 안 돌려본 코드는 준비된 것이 아니다."""

    def test_1_the_stall_diagnostic_reads_the_frozen_baseline(self) -> None:
        arm = STORED_ARM / "evaluation" / "candidate"
        rows = {(r["case"], r["seed"]): r for r in stall.arm_reading(arm)}
        self.assertEqual(len(rows), 6)
        for (case_id, seed), row in rows.items():
            with self.subTest(f"{case_id}:{seed}"):
                self.assertEqual(row["robots"], 32)
                self.assertEqual(row["direction"], "climb", "`*_down` 은 이름과 달리 오르기다")
                self.assertGreater(row["valid_seconds"], 0.0)
                self.assertTrue(0.0 <= row["stall_share"] <= 1.0)
                self.assertEqual(row["censored"], row["robots"] - row["arrivals"])
        # 15cm 가 10cm 보다 더 서 있고 덜 오른다 — 판독기가 두 높이를 구분한다.
        for seed in stall.SEEDS:
            self.assertGreater(rows[("stairs_15_down", seed)]["stall_share"],
                               rows[("stairs_10_down", seed)]["stall_share"])
            self.assertGreater(rows[("stairs_10_down", seed)]["arrival_rate"],
                               rows[("stairs_15_down", seed)]["arrival_rate"])

    def test_2_a_missing_record_is_null_with_a_reason_not_zero(self) -> None:
        reading = stall.case_reading(Path("no/such/steps.csv"), "stairs_15_down")
        self.assertIsNone(reading["stall_share"])
        self.assertIsNone(reading["arrival_rate"])
        self.assertEqual(reading["robots"], 0)
        self.assertIn("absent", reading["reason"])

    def test_3_no_change_is_a_screening_fail_not_a_pass(self) -> None:
        report = screening.screen(STORED_ARM)
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertEqual(report["unreadable"], [])
        self.assertIn("stairs_10_down forward distance median delta > 0", report["failed"])
        self.assertIn("at least one climb count strictly up", report["failed"])
        for check in report["checks"]:
            if check["group"] == "guard":
                self.assertIs(check["ok"], True, check["check"])

    @unittest.skipUnless(A041_ARM.is_dir(), "G-A041 harvest not present")
    def test_4_the_a041_harvest_screens_inconclusive_for_the_reason_this_arm_fixes(self) -> None:
        report = screening.screen(A041_ARM)
        self.assertEqual(report["verdict"], screening.INCONCLUSIVE)
        self.assertTrue(any("stairs_15_down" in name for name in report["unreadable"]),
                        "INCONCLUSIVE 의 이유가 15cm 결측이 아니면 이 검사는 다른 것을 보고 있다")
        # 그리고 잰 자리는 판독문과 같은 수를 낸다.
        rows = {(r["case"], r["seed"]): r for r in stall.arm_reading(A041_ARM / "evaluation" / "candidate")}
        for seed in stall.SEEDS:
            self.assertGreater(rows[("stairs_10_down", seed)]["stall_share"], 0.5)
        failed = " ".join(report["failed"])
        self.assertIn("stairs_10_down pooled ge1 >= baseline", failed)


if __name__ == "__main__":
    unittest.main()
