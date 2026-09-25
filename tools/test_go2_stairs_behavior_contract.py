"""계단·실패 동작 분석의 사실을 산출물에 못 박는다.

분석 문서(`reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md`)의 결론은 세 번 틀린 진단을
대체한다.  같은 오류가 되돌아오지 않도록 결론이 기대는 사실을 원시 기록에서 다시 계산해
확인하고, 틀렸던 서술이 현재 문서에 다시 들어오면 실패한다.
"""
from __future__ import annotations

import csv
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_stairs_behavior as stairs  # noqa: E402

RUNS = stairs.OUT
REPORT = ROOT / "workspace/training/quadruped/reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md"
NOW = ROOT / "GO2_NOW.md"
CLIMBING_POLICIES = (
    ("go2_a017_full_suite", "pilot"),
    ("go2_a017_full_suite", "a017"),
    ("go2_g_a033_a017_track_lin_vel_xy_150", "candidate"),
)


def read(name: str) -> list[dict[str, str]]:
    with (RUNS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class StairsBehaviorContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.climb = stairs.stairs_rows()
        cls.behavior = stairs.behavior_rows()
        cls.training = stairs.training_rows()
        cls.climb_reward = stairs.climb_reward_rows()
        cls.weight_outcome = stairs.weight_outcome_rows(cls.behavior, cls.climb)
        cls.lateral = stairs.lateral_rows()

    def test_1_published_tables_are_what_the_tool_produces(self) -> None:
        for name, rows in (("STAIRS_CLIMB.csv", self.climb),
                           ("CASE_BEHAVIOR.csv", self.behavior),
                           ("TRAINING_TERMS.csv", self.training),
                           ("CLIMB_REWARD.csv", self.climb_reward),
                           ("WEIGHT_OUTCOME.csv", self.weight_outcome),
                           ("LATERAL_BEHAVIOR.csv", self.lateral)):
            with self.subTest(name=name), (RUNS / name).open(encoding="utf-8", newline="") as h:
                self.assertEqual(list(csv.reader(h)), rows,
                                 f"{name} is stale — run python tools/go2_stairs_behavior.py")

    def test_2_case_names_are_the_opposite_of_terrain_direction(self) -> None:
        seen = defaultdict(set)
        for row in read("STAIRS_CLIMB.csv"):
            seen[row["case"]].add(row["direction"])
        for case in ("stairs_10_down", "stairs_15_down"):
            self.assertEqual(seen[case], {"climb"}, case)
        for case in ("stairs_10_up", "stairs_15_up"):
            self.assertEqual(seen[case], {"descend"}, case)

    def test_3_no_policy_has_climbed_two_fifteen_cm_steps(self) -> None:
        rows = [r for r in read("STAIRS_CLIMB.csv")
                if r["case"] == "stairs_15_down"]
        self.assertTrue(rows)
        self.assertEqual(sum(int(r["body_rise_ge2"]) for r in rows), 0)

    def test_4_walking_policies_descend_and_stall_on_the_climb(self) -> None:
        rows = read("STAIRS_CLIMB.csv")
        for run, arm in CLIMBING_POLICIES:
            mine = [r for r in rows if r["run"] == run and r["arm"] == arm]
            down = [r for r in mine if r["case"] == "stairs_15_up"]
            up = [r for r in mine if r["case"] == "stairs_10_down"]
            with self.subTest(run=run, arm=arm):
                self.assertEqual(len(down), 3)
                self.assertGreaterEqual(sum(int(r["body_rise_ge2"]) for r in down), 95)
                per_seed = [int(r["body_rise_ge2"]) for r in up]
                self.assertEqual(len(per_seed), 3)
        counts = {(run, arm): [int(r["body_rise_ge2"]) for r in rows
                               if r["run"] == run and r["arm"] == arm and r["case"] == "stairs_10_down"]
                  for run, arm in CLIMBING_POLICIES}
        self.assertEqual(counts[CLIMBING_POLICIES[0]], [8, 6, 5])
        self.assertEqual(counts[CLIMBING_POLICIES[1]], [0, 1, 1])
        self.assertEqual(counts[CLIMBING_POLICIES[2]], [16, 13, 14])

    def test_5_the_screening_stage_never_measured_a_climb(self) -> None:
        screening = [r for r in read("STAIRS_CLIMB.csv")
                     if not any(r["run"] == run for run, _arm in CLIMBING_POLICIES)
                     and r["run"] not in ("go2_default_vs_pilot_v1", "go2_pilot_v2_baseline",
                                          "go2_chain01_baseline", "go2_feet_air_time_020_v1",
                                          # 표적 단계에 10cm 오르기를 일부러 넣은 첫 회차(2026-09-17)
                                          "go2_g_a038_a033_ang_vel_xy_m008")]
        self.assertTrue(screening)
        self.assertEqual({r["direction"] for r in screening}, {"descend"})

    def test_6_training_error_separates_walkers_from_stallers(self) -> None:
        walkers = {"go2_g_a017_pilot_track_lin_vel_xy_140", "go2_g_a031_a017_feet_air_time_001",
                   "go2_g_a032_a017_feet_air_time_010", "go2_g_a033_a017_track_lin_vel_xy_150",
                   "train_260831-Go2_5var_1000",   # Pilot-01 원본 회수본(2026-09-17 표에 추가)
                   "go2_g_a038_a033_ang_vel_xy_m008"}   # 평지 기준 case에서 걷는다(G-A038 판독 §3-3)
        error = {r["run"]: float(r["error_vel_xy"]) for r in read("TRAINING_TERMS.csv")}
        self.assertLessEqual(max(error[r] for r in walkers - {"go2_g_a038_a033_ang_vel_xy_m008"}), 0.727)
        self.assertEqual(error["go2_g_a038_a033_ang_vel_xy_m008"], 0.762)   # 두 값 사이의 첫 관측
        self.assertLessEqual(max(error[r] for r in walkers), 0.762)
        self.assertGreaterEqual(min(v for r, v in error.items() if r not in walkers), 1.054)

    def test_7_feet_air_time_term_is_negative_in_every_training_log(self) -> None:
        values = [float(r["feet_air_time"]) for r in read("TRAINING_TERMS.csv")]
        self.assertEqual(len(values), 20)   # 학습 회차 19(G-A038 포함) + Pilot-01 원본 회수본
        self.assertTrue(all(v < 0 for v in values), values)

    def test_8_withdrawn_diagnoses_do_not_return_to_the_current_file(self) -> None:
        text = NOW.read_text(encoding="utf-8")
        for phrase in ("추종 병목", "G5 병목은 생존이 아니라 추종", "올라가기는 이미 된다"):
            self.assertNotIn(phrase, text, phrase)
        self.assertIn("GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md", text)

    def test_9_report_is_classified_and_names_its_generator(self) -> None:
        import go2_claim_check as claim
        self.assertEqual(claim.classify(REPORT), "MEASURED")
        body = REPORT.read_text(encoding="utf-8")
        self.assertIn("tools/go2_stairs_behavior.py", body)
        self.assertIn("mesh_terrains.py:245", body)

    def test_10_tuning_direction_rests_on_the_climb_reward_table(self) -> None:
        """§8 의 비율은 표에서 다시 계산해 문서의 글자와 맞춘다.  표가 바뀌면 방향도 다시 읽는다."""
        table = {(r["run"], r["arm"], r["case"], r["group"]): r for r in read("CLIMB_REWARD.csv")}
        body = REPORT.read_text(encoding="utf-8")
        for (run, arm), share in (((CLIMBING_POLICIES[2]), 34), ((CLIMBING_POLICIES[0]), 52)):
            climb = table[(run, arm, "stairs_10_down", "climb")]
            stall = table[(run, arm, "stairs_15_down", "stall")]
            gain = float(climb["track_rate"]) - float(stall["track_rate"])
            cost = float(stall["lin_vel_z_rate"]) - float(climb["lin_vel_z_rate"])
            with self.subTest(run=run, arm=arm):
                self.assertGreater(gain, 0)
                self.assertEqual(round(100 * cost / gain), share)
                self.assertIn(f"{share}%", body)
        for run, arm in CLIMBING_POLICIES:
            walk = float(table[(run, arm, "forward_nominal", "walk")]["sum_rate"])
            stall = float(table[(run, arm, "stairs_15_down", "stall")]["sum_rate"])
            with self.subTest(run=run, arm=arm):
                self.assertTrue(0.4 < stall / walk < 0.55, stall / walk)
        # 방향만 적고 회차는 권하지 않는다는 판단이 문서에서 빠지면 실패한다.
        self.assertIn("회차 하나로는 효과를 판정할 수 없어 권하지 않는다", body)

    def test_11_weight_table_singularities(self) -> None:
        """§8-1b 특이점.  회차가 늘어 반례가 생기면 여기서 깨지고, 문서를 다시 읽게 된다."""
        rows = {r["name"]: r for r in read("WEIGHT_OUTCOME.csv")}
        self.assertEqual(len(rows), len(stairs.WEIGHT_RUNS))
        moving = {n for n, r in rows.items() if float(r["rough_forward_speed"]) >= 0.1}
        self.assertEqual(moving, {"Pilot-01", "A015", "A017", "A031", "A032", "G-A033"})
        for name, row in rows.items():
            both = float(row["lin_vel_z_l2"]) == -2 and float(row["ang_vel_xy_l2"]) == -0.05
            with self.subTest(name=name):
                if name in moving:
                    self.assertTrue(both)
                if not both:
                    self.assertLess(float(row["rough_forward_speed"]), 0.04)
        # 하나만 푼 짝: A020 은 lin_vel_z 만, A021 은 ang_vel_xy 만.
        self.assertEqual((rows["A020"]["lin_vel_z_l2"], rows["A020"]["ang_vel_xy_l2"]), ("-2", "-0.08"))
        self.assertEqual((rows["A021"]["lin_vel_z_l2"], rows["A021"]["ang_vel_xy_l2"]), ("-3", "-0.05"))
        # A018 은 벌점 완화였다.
        self.assertLess(abs(float(rows["A018"]["action_rate_l2"])),
                        abs(float(rows["Pilot-01"]["action_rate_l2"])))
        # track 1.4 기준에서 feet_air_time 이 오를수록 경사 전진이 늘었다.
        slope = [float(rows[n]["slope_plus_20_progress_m"]) for n in ("A031", "A032", "A017")]
        self.assertEqual(slope, sorted(slope))
        self.assertIn("WEIGHT_OUTCOME.csv", REPORT.read_text(encoding="utf-8"))

    def test_12_the_goal_is_all_axes_not_stairs_alone(self) -> None:
        """계단만 올리는 방향으로 되돌아가지 않게 한다.  G5·G3 가 A033 의 가장 큰 감점 둘이고,
        문서는 나머지 다섯 축의 보호 조건을 적고 있어야 한다."""
        import go2_claim_check as claim
        with (claim.RUNS / "SCENARIO_SCORES.csv").open(encoding="utf-8", newline="") as handle:
            row = next(r for r in csv.DictReader(handle)
                       if r["run"] == CLIMBING_POLICIES[2][0] and r["arm"] == "candidate")
        deductions = sorted((float(row[f"G{i}_deduction"]), f"G{i}") for i in range(1, 8))
        self.assertEqual({axis for _d, axis in deductions[-2:]}, {"G5", "G3"})
        body = REPORT.read_text(encoding="utf-8")
        self.assertIn("8-3b. 목표 조건", body)
        self.assertIn("G1·G2·G4·G6·G7이 각각 A033보다 평가 표집 sd의 2배", body)

    def test_13_rough_lateral_failure_is_a_roll_over_that_track_made_worse(self) -> None:
        """§9 특이점.  방향 판단(`ang_vel_xy` 유지, `track` 보류)이 이 사실들에 기대고 있다."""
        rows = {(r["arm"], r["case"]): r for r in read("LATERAL_BEHAVIOR.csv")
                if r["run"] in {run for run, _arm in CLIMBING_POLICIES}}
        walkers = [("pilot", 31), ("a017", 48), ("candidate", 58)]
        for arm, terminated in walkers:
            lateral = rows[(arm, "rough_lateral")]
            with self.subTest(arm=arm):
                self.assertEqual(int(lateral["terminated"]), terminated)
                self.assertLess(float(lateral["tilt_cos_min_median"]), 0)      # 90° 넘게 뒤집힘
                self.assertLessEqual(int(rows[(arm, "rough_forward")]["terminated"]), 3)
                self.assertLessEqual(int(rows[(arm, "left")]["terminated"]), 4)
                self.assertEqual(int(rows[(arm, "right")]["terminated"]), 0)
        a033 = rows[("candidate", "rough_lateral")]
        self.assertGreater(float(a033["mass_auc"]), 0.75)
        self.assertLess(max(float(rows[(a, "rough_lateral")]["mass_auc"]) for a in ("pilot", "a017")), 0.6)
        body = REPORT.read_text(encoding="utf-8")
        self.assertIn("server_run_go2_candidate_suite.sh:228", body)
        self.assertIn("| `ang_vel_xy_l2`는 `-0.05` 유지 |", body)


if __name__ == "__main__":
    unittest.main()
