"""Contract for tools/go2_g_a057_sweep_compare.py — 미측정 처리 회귀 (2026-09-29, Codex 작업 지시 1).

왜 있는가.  비교 도구가 A048(재사용 기준)의 총점을 늘 '미측정'으로 냈다.  원인은 이름에 seed 가 박힌 G7 case
(`dr_seed_101`)를 세 평가 seed 모두에서 찾은 것이다 — seed 202·303 에는 그 폴더가 없으니 6칸이 '빠진' 것으로
잡혔다.  또 이전 판은 case 가 빠져도 남은 case 로 축 점수를 계산했다(min 이 빠진 case 만큼 부푼다).
이 테스트는 (1) 실제 A048 회수물로 기록값(총점 50.16, 험지 옆걸음 16, 밀침 합 1, 15cm ≥2단 24, 10cm ≥2단 90)이
나오는지, (2) case 가 빠지면 0 이나 열세가 아니라 '미측정'으로 남는지를 고정한다.

    python -m unittest tools.test_go2_g_a057_sweep_compare_contract
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_g_a057_sweep_compare as cmp  # noqa: E402

BASE = cmp.KEEP / cmp.planmod.BASE_ARM


def summaries_only(dst: Path) -> Path:
    """A048 회수물에서 summary.json 만 복사한 가짜 arm (축 점수 계산에 필요한 것만)."""
    for p in cmp.cases(BASE).rglob("summary.json"):
        q = cmp.cases(dst) / p.relative_to(cmp.cases(BASE))
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, q)
    return dst


@unittest.skipUnless(cmp.cases(BASE).is_dir(), "A048 회수물이 이 PC에 없다")
class A048Reproduces(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.axes = cmp.axis_scores(BASE)

    def test_1_seeded_case_is_looked_up_only_under_its_own_seed(self) -> None:
        self.assertEqual(cmp.expected_name("dr_seed_101", 101), "dr_seed_101")
        self.assertIsNone(cmp.expected_name("dr_seed_101", 202))
        self.assertEqual(cmp.expected_name("rough_lateral", 303), "rough_lateral")
        self.assertEqual(cmp.expected_name("x_{seed}", 202), "x_202")

    def test_2_a048_total_matches_the_recorded_value(self) -> None:
        self.assertNotEqual(self.axes["total"], cmp.NA)
        self.assertAlmostEqual(self.axes["total"], 50.157, places=2)
        self.assertEqual(self.axes["G7"]["worst"].split(":")[0][:8], "dr_seed_")

    def test_3_a048_case_counters_match_the_record(self) -> None:
        std = float(cmp.axis.registry()["score"]["tracking_proxy_std"])
        self.assertEqual(cmp.case_metrics(BASE, "rough_lateral", std)["falls"], 16)
        push = sum(cmp.case_metrics(BASE, c, std)["falls"] for c in cmp.FALL_CASES if c.startswith("push"))
        self.assertEqual(push, 1)
        self.assertEqual(cmp.case_metrics(BASE, "stairs_15_down", std)["ge2"], 24)
        self.assertEqual(cmp.case_metrics(BASE, "stairs_10_down", std)["ge2"], 90)


@unittest.skipUnless(cmp.cases(BASE).is_dir(), "A048 회수물이 이 PC에 없다")
class MissingStaysUnmeasured(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.arm = summaries_only(self.tmp / "arm")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_4_one_missing_case_makes_its_axis_and_the_total_unmeasured(self) -> None:
        (cmp.cases(self.arm) / "seed_202/rough_lateral/summary.json").unlink()
        axes = cmp.axis_scores(self.arm)
        self.assertEqual(axes["G3"]["score"], cmp.NA)
        self.assertIn("rough_lateral:202", axes["G3"]["missing"])
        self.assertEqual(axes["total"], cmp.NA)
        # 다른 축은 그대로 계산된다 — 빠진 축 때문에 나머지를 지우지 않는다.
        self.assertAlmostEqual(axes["G2"]["score"], 9.573, places=3)

    def test_5_missing_dr_seed_case_is_unmeasured_not_zero(self) -> None:
        (cmp.cases(self.arm) / "seed_303/dr_seed_303/summary.json").unlink()
        axes = cmp.axis_scores(self.arm)
        self.assertEqual(axes["G7"]["score"], cmp.NA)
        self.assertEqual(axes["total"], cmp.NA)

    def test_6_missing_case_metrics_are_unmeasured_in_the_flat_row(self) -> None:
        std = float(cmp.axis.registry()["score"]["tracking_proxy_std"])
        self.assertEqual(cmp.case_metrics(self.arm, "push_pos_x", std), {"state": cmp.NA})  # steps.csv 없음
        rec = {"variable": "v", "value": 1.0, "status": "NEW_TRAIN", "arm": "a", "present": True, "gpu": cmp.NA,
               "axes": cmp.axis_scores(self.arm)}
        for c in (*cmp.FALL_CASES, *cmp.STAIRS):
            rec[c] = {"state": cmp.NA}
        row = cmp.flat(rec)
        self.assertEqual(row["push_falls_sum"], cmp.NA)
        self.assertEqual(row["stairs_15_down_ge2"], cmp.NA)
        self.assertEqual(row["rough_lateral_falls"], cmp.NA)
        for k, v in row.items():
            if k.endswith(("_falls", "_ge2", "_ge1", "_stall")):
                self.assertNotEqual(v, 0, k)

    def test_7_unmeasured_rows_do_not_enter_the_speed_flags(self) -> None:
        base = {"status": "BASE_SHARED", "arm": cmp.planmod.BASE_ARM, "total_70": 50.157,
                "rough_lateral_falls": 16, "rough_lateral_speed": 0.17}
        miss = {"status": "NEW_TRAIN", "arm": "x", "total_70": cmp.NA,
                "rough_lateral_falls": cmp.NA, "rough_lateral_speed": cmp.NA}
        cmp.speed_flags([base, miss])
        self.assertEqual(miss["fall_down_with_speed"], "")

    def test_8_unrecovered_run_is_all_unmeasured(self) -> None:
        row = cmp.flat({"variable": "v", "value": 1.0, "status": "NEW_TRAIN", "arm": "a", "present": False})
        self.assertEqual(row["note"], "결과 미회수 — 전 칸 미측정")
        self.assertNotIn("total_70", row)


if __name__ == "__main__":
    unittest.main()
