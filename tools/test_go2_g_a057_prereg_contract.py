"""Contract for the G-A057 preregistration and its reader (2026-09-29, Codex 작업 지시 2·3).

왜 있는가.  12개 새 학습 행마다 실행 전에 고정해야 하는 여섯 항목(변경·유지값, 원문 출처와 예측 방향, 기존 관측·반례,
표적 관측, 보호 항목, 지지·미지지·판독 불가 기준)이 빠지지 않았는지, 문턱이 A048 회수물에서 계산됐는지, 그리고
판독기가 (1) 변화 없음을 지지로 읽지 않고 (2) 판독 불가 실행을 판정하지 않고 (3) 정지를 실행 중단이 아닌 평가 후
제외로 다루는지를 저장 회수물로 실제 실행해 확인한다(메모리: "준비 완료" = 판독 코드를 돌려봤다).

    python -m unittest tools.test_go2_g_a057_prereg_contract
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_g_a057_prereg_readout as rd  # noqa: E402
import go2_g_a057_preregistration as gen  # noqa: E402
import go2_g_a057_sweep_plan as planmod  # noqa: E402

KEEP = ROOT / "workspace/_keep"
A048 = KEEP / planmod.BASE_ARM
A043 = KEEP / "go2_g_a043_a033_lin_vel_z_m15"
TYPES = {"LECTURE_DIRECT", "DEPLOY_DIRECT", "MECHANISM_HYPOTHESIS", "NO_DIRECT_PREDICTION"}
FULL = "RESULT_STATE=FULL\nCOLLECTION_STATUS=FULL_69_COMPLETE\n"


def needed_cases(pre: dict) -> set[str]:
    cases = {i["case"] for r in pre["rows"].values() for i in r["targets"].values()}
    cases |= {p["case"] for p in pre["protection"].values() if "case" in p}
    return cases


def stand_in(src: Path, dst: Path, pre: dict, status: str | None = FULL) -> Path:
    """저장 회수물에서 판독에 필요한 case 만 복사한 가짜 G-A057 수확물."""
    for case in needed_cases(pre):
        for seed in (101, 202, 303):
            s = rd.dial.cases_dir(src) / f"seed_{seed}" / case
            d = rd.dial.cases_dir(dst) / f"seed_{seed}" / case
            d.mkdir(parents=True, exist_ok=True)
            for name in ("summary.json", "steps.csv"):
                if (s / name).is_file():
                    shutil.copyfile(s / name, d / name)
    if status is not None:
        (dst / "RESULT_STATUS.txt").write_text(status, encoding="utf-8")
    return dst


class Registration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pre = rd.load()

    def test_1_rows_are_exactly_the_twelve_new_training_rows(self) -> None:
        new = [r["key"] for r in planmod.plan()["runs"] if r["status"] == "NEW_TRAIN"]
        self.assertEqual(len(new), 12)
        self.assertEqual(sorted(self.pre["rows"]), sorted(new))
        self.assertNotIn("a043_feet_air_time_p0p01", self.pre["rows"])

    def test_2_every_row_fixes_the_six_items(self) -> None:
        plan_rows = planmod.plan()["runs"]
        for key, r in self.pre["rows"].items():
            with self.subTest(key=key):
                c = r["change"]
                self.assertNotEqual(c["from"], c["to"])
                self.assertNotIn(c["name"], c["held"])
                plan_row = next(p for p in plan_rows if p["key"] == key)
                self.assertEqual({**c["held"], c["name"]: c["to"]}, plan_row["rewards"])
                self.assertIn(r["source"]["prediction_type"], TYPES)
                self.assertTrue(r["source"]["cite"] and r["source"]["text"] and r["source"]["direction"])
                self.assertTrue(r["prior"].startswith("A048 위 관측 없음"))
                self.assertGreaterEqual(len(r["targets"]), 1)
        rules = self.pre["verdict_rules"]
        for k in ("SUPPORTED", "NOT_SUPPORTED", "INSUFFICIENT", "MISSING", "UNREADABLE_RUN",
                  "exclusion_after_evaluation", "run_safety_stop", "no_winner"):
            self.assertIn(k, rules)
        self.assertIn("moving_gate", self.pre["protection"])

    def test_3_mechanism_claims_are_labelled_not_passed_off_as_lecture(self) -> None:
        for key in ("feet_air_time_p0p01", "feet_air_time_p0p1", "feet_air_time_p0p35"):
            self.assertIn("기전 가설", self.pre["rows"][key]["mechanism_hypothesis"])
        self.assertIn("계단 개선 우선 근거가 아니다", self.pre["rows"]["feet_air_time_p0p01"]["mechanism_hypothesis"])
        self.assertIn("직접 예측 없음", self.pre["rows"]["action_rate_l2_m0p012"]["no_direct_prediction"])

    @unittest.skipUnless(rd.dial.cases_dir(A048).is_dir(), "A048 회수물 없음")
    def test_4_thresholds_come_from_the_a048_harvest_and_are_current(self) -> None:
        t = self.pre["rows"]["ang_vel_xy_l2_m0p08"]["targets"]["rough_lateral_falls_down"]
        self.assertEqual((t["a048_pooled"], t["supported_if_at_most"], t["not_supported_if_at_least"]), (16, 8, 16))
        s = self.pre["rows"]["feet_air_time_p0p35"]["targets"]["stairs_15_ge2_up"]
        self.assertEqual((s["a048_pooled"], s["supported_if_at_least"], s["not_supported_if_at_most"]), (24, 60, 24))
        self.assertEqual(json.dumps(gen.build(), ensure_ascii=False, indent=1) + "\n", rd.PREREG.read_text(encoding="utf-8"))


@unittest.skipUnless(rd.dial.cases_dir(A048).is_dir() and rd.dial.cases_dir(A043).is_dir(), "저장 회수물 없음")
class Reader(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pre = rd.load()
        cls.tmp = Path(tempfile.mkdtemp())
        cls.same = stand_in(A048, cls.tmp / "same", cls.pre)
        cls.a043 = stand_in(A043, cls.tmp / "a043", cls.pre)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_5_no_change_is_never_support(self) -> None:
        for key in self.pre["rows"]:
            with self.subTest(key=key):
                out = rd.read(key, self.same, self.pre)
                self.assertEqual(out["run_state"], "COMPLETE")
                for t in out["targets"].values():
                    self.assertEqual(t["verdict"], "NOT_SUPPORTED")
                for name, p in out["protection"].items():
                    self.assertIn(p["state"], ("NOT_CONSISTENT", "MOVING"), name)
                self.assertEqual(out["exclusion"], "EXCLUDED_NO_TARGET_SUPPORT"
                                 if any(not t["cost"] for t in out["targets"].values()) else "KEPT_FOR_REVIEW")

    def test_6_a_real_different_policy_is_read_with_the_fixed_lines(self) -> None:
        out = rd.read("feet_air_time_p0p35", self.a043, self.pre)
        self.assertEqual(out["targets"]["stairs_15_ge2_up"]["value"], 77)        # A043 15cm ≥2단 77/96
        self.assertEqual(out["targets"]["stairs_15_ge2_up"]["verdict"], "SUPPORTED")   # ≥ 60
        lat = rd.read("ang_vel_xy_l2_m0p08", self.a043, self.pre)["targets"]["rough_lateral_falls_down"]
        self.assertEqual((lat["value"], lat["verdict"]), (24, "NOT_SUPPORTED"))  # A043 24 ≥ 16
        yaw = rd.read("ang_vel_xy_l2_m0p08", self.a043, self.pre)["protection"]["yaw_right_falls"]
        self.assertEqual(yaw["state"], "WORSE_ALL_SEEDS")                         # A043 우회전 9/9/11 vs A048 0

    def test_7_unreadable_run_is_not_judged(self) -> None:
        bad = stand_in(A048, self.tmp / "bad", self.pre, status="RESULT_STATE=FULL\nCOLLECTION_STATUS=INCOMPLETE_EARLY_STOP\n")
        out = rd.read("track_lin_vel_xy_exp_p1p6", bad, self.pre)
        self.assertEqual(out["run_state"], "UNREADABLE_RUN")
        self.assertEqual(out["targets"], {})
        self.assertEqual(out["exclusion"], "NOT_JUDGED_UNREADABLE_RUN")
        none = stand_in(A048, self.tmp / "none", self.pre, status=None)
        self.assertEqual(rd.read("track_lin_vel_xy_exp_p1p6", none, self.pre)["run_state"], "UNREADABLE_RUN")

    def test_8_a_missing_case_is_missing_only_for_its_indicator(self) -> None:
        part = stand_in(A048, self.tmp / "part", self.pre)
        (rd.dial.cases_dir(part) / "seed_202/rough_forward/summary.json").unlink()
        out = rd.read("track_lin_vel_xy_exp_p1p4", part, self.pre)
        self.assertEqual(out["targets"]["rough_forward_speed_down_cost"]["verdict"], "MISSING")
        self.assertEqual(out["targets"]["rough_lateral_falls_down"]["verdict"], "NOT_SUPPORTED")

    def test_9_stationary_is_a_post_evaluation_exclusion(self) -> None:
        still = stand_in(A048, self.tmp / "still", self.pre)
        p = rd.dial.cases_dir(still) / "seed_101/forward_nominal/summary.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        d.update(speed_xy_mean=0.0, tracking_xy_rmse=1.0)
        p.write_text(json.dumps(d), encoding="utf-8")
        out = rd.read("action_rate_l2_m0p008", still, self.pre)
        self.assertEqual(out["run_state"], "COMPLETE")                 # 실행은 끝까지 수집됐다
        self.assertEqual(out["protection"]["moving_gate"]["state"], "STATIONARY")
        self.assertEqual(out["exclusion"], "EXCLUDED_STATIONARY")


if __name__ == "__main__":
    unittest.main()
