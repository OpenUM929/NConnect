"""Contract for the G-A043 one-command campaign (G-A033 + lin_vel_z_l2 -2.0 -> -1.5).  Local only.

A package is not ready until the code that will read its harvest has run on one (memory rule
"준비 완료 = 판독 코드를 돌려봤다").  So besides what the builder writes, these tests run the server
gate and the local verifier on synthetic harvests shaped like the runner's output, and they run the
screening readers on the real G-A033 and G-A042 harvests.

What is new in this arm, and what these tests pin down:
  It is the first arm whose own forecast predicts a loss on two of the four situations (sway
  -0.0470, push -0.0386 against climb +0.0258), and the first whose supporting evidence is
  contradicted inside the same file it comes from - the 15 cm stallers carry the SMALLEST share of
  this penalty while climbing least.  Three things follow, each with a test here:
    - the plan screening edition post_a042_push_v1 adds both G6 x directions to the protection
      block, and forward_stairs_v1 keeps judging exactly what it judged for G-A042 (test_18);
    - push_neg_x moves from one marker seed to three and becomes a paired-seed guard, in exchange
      for the two lateral push markers, under the builder's 21-case stage-1 cap (test_13);
    - both push directions are filmed on both arms, which is why this run renders two baseline
      videos and reuses four by SHA (test_15).
  The dial's own history is one hold (G-A037 at -1.0, HOLD_CONTRADICTED) and two runs on stopped
  baselines.  Nothing here claims -1.5 is an improvement; the status is INFORMATION_RUN.

    python -m unittest tools.test_go2_g_a043_campaign_contract
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

CAMPAIGN_ID = "G-A043"
SPEC = reward.load(CAMPAIGN_ID)
BASE = SPEC["baseline"]
TERM = SPEC["single_change"]["name"]
STORED_ARM = ROOT / BASE["stored_arm"]
A017_ARM = ROOT / "workspace" / "_keep" / "go2_a017_full_suite" / "evaluation" / "a017"
A042_ARM = ROOT / "workspace" / "_keep" / "go2_g_a042_a033_track_lin_vel_xy_160"
PAYLOAD = build.build_payload(CAMPAIGN_ID)
ARM = reward.build_payload(SPEC)
REGISTRY = json.loads(ARM["go2_self_eval_registry.json"].decode("utf-8"))
CAMP = build.CAMPAIGNS[CAMPAIGN_ID]
REQUIRED = SPEC["preregistered"]["required_target_cases"]
PROBE_TO = "-1.5"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PackageTest(unittest.TestCase):
    def test_1_build_is_reproducible_and_published(self) -> None:
        self.assertEqual(build.build_payload(CAMPAIGN_ID), PAYLOAD)
        current = GO2 / "upload" / CAMP["upload_id"] / "current" / CAMP["upload_zip"]
        with zipfile.ZipFile(current) as archive:
            shipped = {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()}
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
        self.assertIn(f"추론 사슬 {SPEC['inference']['status']}", note,
                      "권고 상태는 사양에서 나온다 — 손으로 박지 않는다")

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
        self.assertEqual(reward_dict(candidate)[TERM], -1.5)
        self.assertEqual(reward_dict(reference)[TERM], -2.0)
        trained = reward.BASELINE_SOURCE / "source" / "quadruped_rewards.py"
        self.assertEqual(reward_dict(reference), reward_dict(trained.read_text(encoding="utf-8")),
                         "the reference must be the reward file G-A033 was trained with")
        config = ARM["run_config.env"].decode("utf-8")
        for line in (f"SINGLE_CHANGE_NAME={TERM}", "SINGLE_CHANGE_FROM=-2.0", "SINGLE_CHANGE_TO=-1.5",
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
        self.assertEqual(base_data.walking_values(TERM), [-2.0],
                         "every walking run carries -2.0, so the slope of this dial is unmeasured")
        declared = SPEC["base_data"]["terms"][TERM]
        self.assertEqual(declared["status"], "OUT_OF_RANGE")
        self.assertGreaterEqual(len(declared["out_of_range_reason"]), 20)
        probes = {(r["term"], r["to"]): r for r in mech.read("PROBES.csv")}
        row = probes[(TERM, PROBE_TO)]
        self.assertEqual((row["zone"], row["range_status"]), ("WALK", "OUT_OF_RANGE"))
        self.assertGreater(float(row["margin"]), float(row["margin_from"]))
        self.assertIn(row["margin"], SPEC["value_derivation"]["walk_margin"])

    def test_7_the_forecast_predicts_a_loss_and_the_spec_carries_it(self) -> None:
        """G-A042 의 네 칸은 전부 양수였다.  이 팔은 두 칸이 음수다 — 예측된 손실을 숨기지 않는다."""
        situ = {(r["term"], r["to"]): r for r in mech.read("PROBE_SITUATIONS.csv")}[(TERM, PROBE_TO)]
        for column in ("walk_delta", "climb_delta", "sway_delta", "push_delta"):
            self.assertTrue(situ[column].strip(), column)
        self.assertGreater(float(situ["walk_delta"]), 0.0)
        self.assertGreater(float(situ["climb_delta"]), 0.0)
        self.assertLess(float(situ["sway_delta"]), 0.0)
        self.assertLess(float(situ["push_delta"]), 0.0)
        predictions = SPEC["inference"]["predictions"]
        self.assertEqual([predictions[s]["direction"] for s in ("walk", "climb", "sway", "push")],
                         ["up", "up", "down", "down"])
        for situation in ("sway", "push"):
            self.assertIn(situ[f"{situation}_delta"], predictions[situation]["basis"],
                          f"{situation} 예측은 자기 칸의 수를 인용해야 한다")
        self.assertIs(SPEC["inference"]["exploratory"], True)
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")
        self.assertIn("worse", str(SPEC["base_data"]["walk_margin"]))
        self.assertEqual(SPEC["base_data"]["walk_margin"]["worse"], ["push", "sway"])

    def test_8_the_supporting_row_is_contradicted_in_its_own_file_and_says_so(self) -> None:
        """이 팔의 근거는 같은 파일 안에서 반박된다 — 그 행이 사양에 있어야 한다 (S5·15cm)."""
        climb_file = "reports/evidence/go2_stairs_behavior_20260916/CLIMB_REWARD.csv"
        support = [r for r in SPEC["inference"]["rows"]
                   if r["source"] == climb_file and r["selector"].get("group") == "climb"]
        against = [r for r in SPEC["inference"]["contradicting"]
                   if r["source"] == climb_file and r["selector"].get("case") == "stairs_15_down"]
        self.assertTrue(support, "10cm 오르기 집단의 벌점률 행이 없다")
        self.assertTrue(against, "15cm 정체 집단의 반대 행이 없다")
        self.assertEqual(support[0]["cells"]["lin_vel_z_rate"], "-0.124")
        self.assertEqual(against[0]["cells"]["lin_vel_z_rate"], "-0.021")
        self.assertLess(abs(float(against[0]["cells"]["lin_vel_z_rate"])),
                        abs(float(support[0]["cells"]["lin_vel_z_rate"])),
                        "가장 못 오르는 집단이 이 벌점을 가장 적게 낸다 — 그것이 반대 근거다")
        s5 = [r for r in SPEC["inference"]["contradicting"] if "S5" in r["key"]]
        self.assertTrue(s5, "기반 데이터 S5 행이 없다")
        self.assertIn("False", s5[0]["value"])
        self.assertIn("HOLD_CONTRADICTED", s5[0]["reads"], "G-A037 를 보류시킨 행임을 밝혀야 한다")
        self.assertIn("S5", str(SPEC["inference"]["singularity"]))

    def test_9_no_other_lever_moved_and_each_says_why(self) -> None:
        base, cand = SPEC["rewards"]["baseline"], SPEC["rewards"]["candidate"]
        for name in REWARD_NAMES:
            with self.subTest(name):
                if name == TERM:
                    self.assertNotEqual(base[name], cand[name])
                    continue
                self.assertEqual(base[name], cand[name])
                self.assertIn(name, SPEC["rejected_alternatives"])
        for name in ("dof_acc_l2", "max_iterations", "training_seed", "lin_vel_z_l2_to_m1"):
            self.assertIn(name, SPEC["rejected_alternatives"])
        held = SPEC["rejected_alternatives"]["lin_vel_z_l2_to_m1"]
        self.assertIn("G-A037", held)
        self.assertIn("does not license -1.0", held, "FAIL 이 자동 추가 완화로 이어지지 않는다고 적어야 한다")
        self.assertIn("G-A042", SPEC["rejected_alternatives"]["track_lin_vel_xy_exp"],
                      "직전 회차의 실패가 그 레버를 멈춘 이유여야 한다")

    def test_10_the_measured_limits_are_recomputed_not_typed(self) -> None:
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
        generated = rules.rules_for(SPEC)
        self.assertEqual(SPEC["preregistered"]["target_group_floor"], generated["target_group_floor"])
        self.assertEqual(SPEC["preregistered"]["max_scenario_weighted_loss_70_by_scenario"],
                         generated["max_scenario_weighted_loss_70_by_scenario"])
        # 계단 관문도 생성기 값 그대로다 — 뺀 것은 발화할 수 없는 15cm 묶음 하나뿐이고(test_11),
        # 그 사실이 `omitted` 에 적혀 있다.
        shipped = SPEC["preregistered"]["climb_guard"]["groups"]
        for name, group in shipped.items():
            self.assertEqual(group, generated["climb_guard"]["groups"][name], name)
        self.assertEqual(set(generated["climb_guard"]["groups"]) - set(shipped), {"stairs_15_climb_ge1"})
        self.assertEqual(SPEC["preregistered"]["climb_guard"]["baseline"],
                         generated["climb_guard"]["baseline"])

    def test_11_every_climb_guard_can_actually_fire(self) -> None:
        guard = SPEC["preregistered"]["climb_guard"]["groups"]
        self.assertEqual(set(guard), {"stairs_10_climb_ge1", "stairs_10_climb_ge2"})
        for name, group in guard.items():
            with self.subTest(name):
                self.assertEqual(group["baseline_sum"], sum(group["baseline_counts"]))
                self.assertGreater(float(group["baseline_sum"]) - float(group["max_drop"]), 0.0)
        omitted = str(SPEC["preregistered"]["climb_guard"].get("omitted", ""))
        self.assertIn("stairs_15_climb_ge1", omitted)
        self.assertIn("stage 1", omitted)
        self.assertEqual(SPEC["preregistered"]["rule_version"], fact.RULE_VERSION)
        for axis in ("G2", "G3", "G6"):
            self.assertIn(axis, SPEC["inference"]["risk_axes"])

    def test_12_the_isaac_lab_anchor_is_left_and_the_spec_says_why(self) -> None:
        rewards = json.loads((GO2 / "config/go2_external_reference.json").read_text(encoding="utf-8"))
        rewards = rewards["isaaclab"]["rewards"]
        self.assertEqual(rewards["go2_rough"][TERM], SPEC["single_change"]["from"],
                         "the frozen baseline sits exactly on the Isaac Lab Go2 rough value")
        self.assertEqual(rewards["base"][TERM], rewards["go2_flat"][TERM],
                         "이 항은 세 설정이 모두 같은 값이라 이탈이 더 분명하다")
        self.assertNotEqual(SPEC["single_change"]["to"], SPEC["external_reference"]["isaaclab_go2_rough"])
        self.assertTrue(str(SPEC["external_reference"]["departure_reason"]).strip())
        deployed = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
        self.assertIn("추천 -5.0 ~ -0.5", deployed)
        self.assertIn("험지/계단 유리", deployed)
        self.assertTrue([row for row in SPEC["inference"]["contradicting"]
                         if "험지/계단 유리" in row["key"]],
                        "배포 파일이 강한 쪽을 계단에 유리하다고 적은 행이 반대 근거로 실려 있어야 한다")

    def test_13_the_push_guard_is_added_without_dropping_a_marker(self) -> None:
        """2026-09-22 검토 결함: v1 은 ±y 표지를 빼면서 "예측에 지목되지 않았다"고 적었다.

        코드가 반대다 — `tools/go2_reward_mechanism.PUSH_CASES` 는 밀침 상황을 네 방향에서
        계산한다.  그래서 이 검사는 두 가지를 함께 본다: ①G-A042 의 필수 기록이 하나도 빠지지
        않았다 ②−x 가 3 seed 로 올라갔다.  상한은 회차마다 올리는 수가 아니라 평가 전체의 1/3 이다.
        """
        scored = length.targets(SPEC)
        measured = reward.targets(SPEC)
        self.assertEqual(len(scored), 12)
        self.assertEqual(REQUIRED[:3], ["G5:stairs_15_down:101", "G5:stairs_15_down:202",
                                        "G5:stairs_15_down:303"], "15cm 세 seed가 먼저 온다")
        self.assertEqual(REQUIRED[3:6], ["G6:push_neg_x:101", "G6:push_neg_x:202", "G6:push_neg_x:303"],
                         "밀침 −x 는 표지 1 seed 가 아니라 3 seed 짝 비교다")
        a042_required = set(reward.load("G-A042")["preregistered"]["required_target_cases"])
        self.assertTrue(a042_required <= set(REQUIRED),
                        f"G-A042 의 필수 기록이 빠졌다: {sorted(a042_required - set(REQUIRED))}")
        for entry in ("G6:push_pos_y:101", "G6:push_neg_y:101"):
            self.assertIn(entry, REQUIRED, "밀침 상황은 네 방향에서 계산되므로 ±y 표지를 빼지 않는다")
        self.assertEqual(len(scored) + len(REQUIRED), 22)
        # 2026-09-22 2차 검토: 상한을 "1단계 전체" 라 부르면서 빌더는 파국 case 를 빼고 셌다.
        # 이제 1단계가 실제로 재는 목록(verifier.target_stage_entries)과 같은 수를 센다.
        stage1 = verifier.target_stage_entries(SPEC)
        self.assertEqual(len(stage1), 23, "파국 1 + 채점 12 + 기록 10")
        self.assertEqual(len(set(stage1)), len(stage1), "1단계 목록에 중복이 없다")
        self.assertEqual(reward.MAX_STAGE1_CASES, 23, "상한은 69 case 의 1/3 이고, 세는 범위가 같다")
        self.assertLessEqual(len(stage1), reward.MAX_STAGE1_CASES)
        too_many = copy.deepcopy(SPEC)
        too_many["preregistered"]["required_target_cases"] = REQUIRED + ["G6:push_pos_y:202"]
        with self.assertRaises(RuntimeError) as caught:
            reward.validate_spec(too_many)
        self.assertIn("at most 23 measured cases", str(caught.exception))
        self.assertEqual(mech.PUSH_CASES, ("push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y"),
                         "이 검사의 전제는 밀침 상황 계산의 네 방향이다")
        reason = SPEC["preregistered"]["required_target_cases_reason"]
        self.assertIn("PUSH_CASES", reason, "왜 ±y 를 남기는지 코드 근거를 적어야 한다")
        self.assertIn("23", reason)
        self.assertIn("observation", reason, "±y 는 관측이고 판정이 아니라고 적어야 한다")
        # ±y 를 관문에서 뺀 이유는 "비교 불가" 가 아니라 "seed 간 일관성이 없다" 다 (2차 검토).
        self.assertIn("consistency across seeds", reason)
        self.assertIn("possible", reason, "같은 seed 비교가 가능하다는 사실을 적어야 한다")
        self.assertEqual(SPEC["evaluation"]["catastrophe_case"], "G1:forward_nominal:101")
        self.assertEqual(measured, [*scored, *REQUIRED], "required records must follow the scored targets")
        self.assertFalse(set(REQUIRED) & set(scored), "a required record must not be scored twice")
        config = ARM["run_config.env"].decode("utf-8")
        line = next(l for l in config.splitlines() if l.startswith("TARGET_CASES="))
        for entry in REQUIRED:
            self.assertIn(entry, line)
        self.assertEqual(gate.targets(SPEC), scored, "서버 게이트는 필수 기록을 채점하지 않는다")
        self.assertGreaterEqual(len(SPEC["preregistered"]["required_target_cases_reason"]), 40)

    def test_14_the_release_states_the_number_of_cases_it_measures(self) -> None:
        readme = PAYLOAD["README.txt"].decode("utf-8")
        guide = build.run_guide(CAMPAIGN_ID, "0" * 64)
        self.assertIn("the 22 target cases", readme)
        self.assertIn("표적 22 case", guide)
        self.assertIn("표적 12 case proxy 평균", guide, "게이트가 채점하는 수는 1단계가 재는 수와 다르다")
        self.assertEqual(build.target_case_count(CAMP, SPEC), len(reward.targets(SPEC)))
        self.assertEqual(build.scored_case_count(CAMP, SPEC), len(length.targets(SPEC)))
        self.assertNotIn(CAMPAIGN_ID, build.FROZEN_TARGET_COUNT, "실행되지 않은 회차는 수를 얼리지 않는다")
        self.assertIn("영상 6+2개", guide, "양방향 밀침을 두 팔 모두에서 찍는다")

    def test_15_six_cases_are_filmed_on_both_arms_and_two_are_rendered(self) -> None:
        videos = SPEC["videos"]
        self.assertEqual(videos["candidate"], ["G5:stairs_10_down:101", "G5:stairs_15_down:101",
                                               "G3:rough_forward:101", "G3:rough_lateral:101",
                                               "G6:push_pos_x:101", "G6:push_neg_x:101"])
        self.assertEqual(videos["baseline"], ["G6:push_pos_x:101", "G6:push_neg_x:101"],
                         "기준선 영상이 없는 두 밀침 case 만 새로 찍는다")
        reuse = videos["baseline_reuse"]
        self.assertEqual(set(reuse) | set(videos["baseline"]), set(videos["candidate"]),
                         "여섯 case 모두 기준선 짝이 있어야 한다")
        self.assertEqual(len(reuse), 4)
        self.assertEqual(length.reuse_problems(SPEC), [])
        for entry, row in reuse.items():
            with self.subTest(entry):
                path = ROOT / row["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(sha(path.read_bytes()), row["sha256"])
                self.assertEqual(row["identity_sha256"], length.video_fingerprint(SPEC, entry))
        tampered = copy.deepcopy(SPEC)
        first = next(iter(tampered["videos"]["baseline_reuse"]))
        tampered["videos"]["baseline_reuse"][first]["sha256"] = "0" * 64
        self.assertTrue(length.reuse_problems(tampered), "바뀐 파일이 통과하면 재사용은 근거가 아니다")

    def test_16_a_second_reward_change_is_refused(self) -> None:
        broken = copy.deepcopy(SPEC)
        broken["rewards"]["candidate"]["ang_vel_xy_l2"] = -0.04
        with self.assertRaises(RuntimeError) as caught:
            reward.validate_spec(broken)
        self.assertIn("exactly the single_change reward must differ", str(caught.exception))

    def test_17_a_required_record_that_is_also_scored_is_refused(self) -> None:
        broken = copy.deepcopy(SPEC)
        broken["preregistered"]["required_target_cases"] = ["G6:push_pos_x:101"]
        with self.assertRaises(RuntimeError) as caught:
            reward.validate_spec(broken)
        self.assertIn("must not also be a scored target", str(caught.exception))

    def test_18_the_new_screening_edition_only_adds_the_push_block(self) -> None:
        version = SPEC["preregistered"]["plan_screening"]["version"]
        self.assertEqual(version, "post_a042_push_v1")
        self.assertEqual(verifier.plan_screening_version(SPEC), version)
        self.assertTrue(verifier.plan_screening_active(SPEC))
        added = set(screening.cases_for(version)) - set(screening.cases_for("forward_stairs_v1"))
        self.assertEqual(added, set(screening.PUSH))
        self.assertEqual(screening.cases_for("forward_stairs_v1"), screening.CASES,
                         "옛 판의 case 목록은 그대로다 — G-A042 판정이 재현된다")
        self.assertEqual(screening.cases_for(None), screening.CASES)
        with self.assertRaises(ValueError):
            screening.cases_for("no_such_version")
        a042 = reward.load("G-A042")
        self.assertEqual(verifier.plan_screening_version(a042), "forward_stairs_v1")

    def test_20_the_shipped_baseline_reward_file_is_the_baseline(self) -> None:
        """결함 C-8: `baseline/` 이 작업본 값을 싣던 것을 이 회차에서 고쳤다 — 발행된 판은 그대로.

        기준선은 SHA 고정 `model_best.pt`·`env.yaml` 재생이라 학습에는 쓰이지 않는 파일이지만,
        패키지를 열어 비교하는 사람에게 **없는 두 번째 차이**를 보여 주던 자리다.
        """
        self.assertEqual(SPEC["output"]["baseline_reward_file"], "rendered_reference")
        shipped = reward_dict(ARM["baseline/quadruped_rewards.py"].decode("utf-8"))
        reference = reward_dict(ARM["reference/baseline_quadruped_rewards.py"].decode("utf-8"))
        self.assertEqual(shipped, reference)
        self.assertEqual(shipped, SPEC["rewards"]["baseline"], "기준선 파일은 기준선 값이어야 한다")
        candidate = reward_dict(ARM["candidate/quadruped_rewards.py"].decode("utf-8"))
        self.assertEqual([n for n in REWARD_NAMES if shipped[n] != candidate[n]], [TERM],
                         "패키지 안의 유일한 다이얼 차이는 단일변수 하나다")
        # 발행된 회차는 키가 없으므로 예전 바이트 그대로 만들어진다 (C-2 를 키우지 않는다).
        older = reward.build_payload(reward.load("G-A042"))
        self.assertIsNone(reward.load("G-A042")["output"].get("baseline_reward_file"))
        self.assertNotEqual(older["baseline/quadruped_rewards.py"],
                            older["reference/baseline_quadruped_rewards.py"])

    def test_21_the_criteria_changes_document_exists_and_is_named(self) -> None:
        """기준을 바꿨으면 근거는 별도 문서다 (2026-09-22 사용자 지시)."""
        ref = SPEC["criteria_changes"]
        path = GO2 / ref.split(" ", 1)[0]
        self.assertTrue(path.is_file(), f"{path} 가 없다")
        text = path.read_text(encoding="utf-8")
        for needle in ("PUSH_CASES", "MAX_STAGE1_CASES", "post_a042_push_v1", "C-8", "C-10",
                       SPEC["single_change"]["name"]):
            self.assertIn(needle, text, f"근거 문서가 {needle} 를 적지 않았다")
        # 문서는 ZIP 발행과 로컬 검증을 분리하고, 실행 준비 완료를 주장하지 않는다
        # (v1 보고의 실패가 그것이었다).  낱말이 아니라 그 문장을 검사한다.
        self.assertIn("실행 준비 완료로 보고하지 않는다", text)
        self.assertIn("서버 실행·회수", text)
        self.assertRegex(text, r"\*\*미실행\*\*")

    def test_19_the_earlier_releases_are_untouched(self) -> None:
        self.assertIn(CAMPAIGN_ID, verifier.SPECS)
        self.assertEqual(verifier.load_spec(CAMPAIGN_ID), SPEC)
        known_diverged = {"G-A035", "G-A037", "G-A039"}   # 결함 C-2, reports/GO2_DEFECT_LEDGER.md
        diverged = set()
        for work_id in ("G-A035", "G-A037", "G-A038", "G-A039", "G-A041", "G-A042"):
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


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir() and A017_ARM.is_dir(),
                     "G-A033 or A017 harvest not present")
class GateAndVerifierTest(unittest.TestCase):
    """The server gate and the verifier of record read a G-A043 harvest the same way."""

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
        patched, count = re.subn(rf"(\n  {TERM}:\n(?:    .*\n)*?    weight: )-2\.0\n", r"\g<1>-1.5\n", text)
        assert count == 1, f"{TERM} weight line not found exactly once"
        return patched

    def harvest(self, name: str) -> Path:
        keep = Path(self.tmp.name) / name
        model = b"synthetic G-A043 model"
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

    def test_2_the_push_records_are_measured_and_not_scored(self) -> None:
        """1단계 수확물에 −x 밀침 3 seed 가 들어 있어도 게이트의 판정 수는 12 case 그대로다."""
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
        """The whole arm rests on the trained env carrying -1.5; the stored baseline carries -2.0."""
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

    def test_6_a_missing_push_record_makes_the_plan_screening_inconclusive(self) -> None:
        """밀침 −x 가 빠지면 이 회차의 screening 은 판정이 아니라 INCONCLUSIVE 다."""
        keep = self.harvest("missing_push")
        shutil.rmtree(keep / "evaluation" / "candidate" / "cases" / "seed_202" / "push_neg_x")
        report = screening.screen(keep, STORED_ARM / "evaluation" / BASE["stored_label"],
                                  cases=screening.cases_for(SPEC["preregistered"]["plan_screening"]["version"]))
        self.assertEqual(report["verdict"], screening.INCONCLUSIVE)
        self.assertTrue(any("push_neg_x" in name for name in report["unreadable"]), report["unreadable"])


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir(),
                     "G-A033 harvest not present")
class PlanReadersTest(unittest.TestCase):
    """계획 §5의 판독기를 **실제 수확물**에 돌려 본다 — 안 돌려본 코드는 준비된 것이 아니다."""

    VERSION = "post_a042_push_v1"

    def test_1_no_change_is_a_screening_fail_not_a_pass(self) -> None:
        report = screening.screen(STORED_ARM, cases=screening.cases_for(self.VERSION))
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertEqual(report["unreadable"], [])
        self.assertIn("stairs_10_down forward distance median delta > 0", report["failed"])
        self.assertIn("at least one climb count strictly up", report["failed"])
        for check in report["checks"]:
            if check["group"] == "guard":
                self.assertIs(check["ok"], True, check["check"])

    def test_2_the_push_block_is_present_and_per_direction(self) -> None:
        report = screening.screen(STORED_ARM, cases=screening.cases_for(self.VERSION))
        names = [check["check"] for check in report["checks"]]
        for case_id in screening.PUSH:
            for suffix in ("pooled posture falls <= baseline", "survival median delta >= 0",
                           "tracking proxy median delta >= 0"):
                self.assertIn(f"{case_id} {suffix}", names)
        self.assertEqual(report["cases"], list(screening.cases_for(self.VERSION)))
        self.assertIn("post_a042_push_v1", report["rule"])

    def test_3_the_old_edition_is_unchanged_on_the_same_harvest(self) -> None:
        """G-A042 가 판정받은 판은 case 도 검사도 그대로다 — 새 판이 옛 판정을 흔들지 않는다."""
        old = screening.screen(STORED_ARM)
        self.assertEqual(old["cases"], list(screening.CASES))
        self.assertNotIn("post_a042_push_v1", old["rule"])
        old_names = {check["check"] for check in old["checks"]}
        new_names = {check["check"] for check in
                     screening.screen(STORED_ARM, cases=screening.cases_for(self.VERSION))["checks"]}
        self.assertEqual(new_names - old_names,
                         {f"{case_id} {suffix}" for case_id in screening.PUSH
                          for suffix in ("pooled posture falls <= baseline", "survival median delta >= 0",
                                         "tracking proxy median delta >= 0")})
        self.assertEqual(old_names - new_names, set())

    def test_5_the_push_block_fails_on_degradation_not_only_on_absence(self) -> None:
        """결측 검출과 **악화 검출**은 다른 증거다 (2026-09-22 2차 검토 지적 3).

        test_6(GateAndVerifierTest)은 −x seed 하나를 지워 `INCONCLUSIVE` 를 확인한다 — 그것은
        결측 검출이고 성능 악화 검출이 아니다.  이 검사는 `judge` 를 직접 불러, 자료가 **전부
        있는데 밀침만 나빠진** 경우에 각 검사가 FAIL 로 잡히는지 본다.  파일을 만들지 않으므로
        수확물 복사 없이 판정 논리만 시험한다.
        """
        cases = screening.cases_for(self.VERSION)

        def rows(**tweak):
            out = {}
            for case_id in cases:
                for seed in screening.SEEDS:
                    row = {"case": case_id, "seed": seed, "missing": [], "progress_m": 4.0,
                           "survival": 0.9, "tracking": 0.8, "posture_falls": 4,
                           "fingerprint": {"case": case_id, "seed": seed}}
                    if case_id in screening.STAIRS:
                        row.update(ge1=10, ge2=5, stall_share=0.5,
                                   first_step_time_median_s=1.0, arrival_rate=1.0)
                    row.update(tweak.get(case_id, {}))
                    out[(case_id, seed)] = row
            return out

        # 계단이 좋아지고 보호축이 그대로면 통과한다 — 기준선을 맞추는 대조군.
        better = {"stairs_10_down": {"progress_m": 5.0, "ge1": 11, "ge2": 6, "stall_share": 0.4},
                  "stairs_15_down": {"progress_m": 5.0, "ge1": 11, "ge2": 6, "stall_share": 0.4}}
        passing = screening.judge(rows(), rows(**better), cases)
        self.assertEqual(passing["verdict"], screening.PASS, passing["failed"])

        # 같은 계단 개선에 밀침 −x 낙상만 늘리면 FAIL 이고, 그 방향의 검사 이름이 나온다.
        worse_falls = dict(better, push_neg_x={"posture_falls": 6})
        report = screening.judge(rows(), rows(**worse_falls), cases)
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertIn("push_neg_x pooled posture falls <= baseline", report["failed"])
        self.assertNotIn("push_pos_x pooled posture falls <= baseline", report["failed"])
        self.assertEqual(report["unreadable"], [], "자료는 전부 있다 — 결측이 아니라 악화다")

        # 생존·추종이 내려가는 경우도 방향별로 잡힌다.
        worse_survival = dict(better, push_pos_x={"survival": 0.8, "tracking": 0.7})
        report = screening.judge(rows(), rows(**worse_survival), cases)
        self.assertEqual(report["verdict"], screening.FAIL)
        for name in ("push_pos_x survival median delta >= 0",
                     "push_pos_x tracking proxy median delta >= 0"):
            self.assertIn(name, report["failed"])

        # 옛 판에서는 같은 악화가 아무 검사에도 걸리지 않는다 — 새 판이 더하는 것이 이것이다.
        old_cases = screening.cases_for("forward_stairs_v1")
        old = screening.judge(rows(), rows(**worse_falls), old_cases)
        self.assertEqual(old["verdict"], screening.PASS,
                         "옛 판이 이 악화를 잡았다면 새 판의 근거가 달라진다")

    @unittest.skipUnless(A042_ARM.is_dir(), "G-A042 harvest not present")
    def test_4_the_a042_harvest_still_screens_the_way_it_was_judged(self) -> None:
        report = screening.screen(A042_ARM)
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertIn("stairs_10_down pooled ge2 >= baseline", report["failed"])
        rows = {(r["case"], r["seed"]): r for r in stall.arm_reading(A042_ARM / "evaluation" / "candidate")}
        for seed in stall.SEEDS:
            self.assertGreater(rows[("stairs_10_down", seed)]["stall_share"], 0.0)


if __name__ == "__main__":
    unittest.main()
