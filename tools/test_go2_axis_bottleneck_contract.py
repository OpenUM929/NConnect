"""`tools/go2_axis_bottleneck.py` 계약.

가장 중요한 검사는 test_2 다 — 이 도구가 다시 계산한 7축 점수가 **원장 SCENARIO_SCORES.csv 와
글자 그대로 같아야** 한다.  같지 않으면 우리가 읽고 있는 채점식이 실제 채점식이 아니라는 뜻이고,
그 위에 세운 모든 진단이 무효다.
"""
from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_axis_bottleneck as axis  # noqa: E402

LEDGER = ROOT / "workspace/training/quadruped/reports/runs/SCENARIO_SCORES.csv"
LEDGER_RUN = "go2_g_a033_a017_track_lin_vel_xy_150"


class AxisBottleneckContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.detail, self.summary = axis.rows()

    def test_1_csv_and_doc_are_regenerated(self) -> None:
        buffer = io.StringIO()
        axis.write_csv(buffer, self.detail, self.summary)
        self.assertEqual(axis.OUT_CSV.read_text(encoding="utf-8"), buffer.getvalue(),
                         "AXIS_BOTTLENECK.csv 가 재생성 결과와 다르다 —"
                         " python -B tools/go2_axis_bottleneck.py")
        self.assertEqual(axis.OUT_DOC.read_text(encoding="utf-8"), axis.document(self.summary),
                         "GO2_AXIS_BOTTLENECK.md 가 재생성 결과와 다르다")

    def test_2_recomputed_axes_match_the_run_ledger(self) -> None:
        """다시 계산한 7축이 원장 값과 같아야 한다 — 식을 우리가 옳게 읽었다는 유일한 증거다."""
        with LEDGER.open(encoding="utf-8") as handle:
            ledger = [r for r in csv.DictReader(handle) if r["run"].startswith(LEDGER_RUN)]
        self.assertEqual(len(ledger), 1, f"{LEDGER_RUN} 행이 원장에 하나여야 한다")
        recorded = ledger[0]
        self.assertEqual(len(self.summary), 7, "7축이 모두 계산돼야 한다")
        for row in self.summary:
            with self.subTest(axis=row["axis"]):
                self.assertAlmostEqual(
                    row["score_70"], float(recorded[row["axis"]]), places=4,
                    msg=f"{row['axis']}: 재계산 {row['score_70']} != 원장 {recorded[row['axis']]}"
                        " — 채점식을 잘못 읽고 있다")

    def test_3_the_counterfactual_is_never_labelled_as_measured(self) -> None:
        """생존 1.0 반사실은 예측이다.  '측정'으로 적히면 C05 형태의 실패다."""
        for row in self.summary:
            with self.subTest(axis=row["axis"]):
                self.assertIn("반사실", row["kind"], f"{row['axis']}: 반사실 표시가 없다")
                self.assertGreaterEqual(row["counterfactual_survival_1"], row["score_70"],
                                        f"{row['axis']}: 반사실이 실측보다 낮다")

    def test_4_every_case_row_names_what_binds_it(self) -> None:
        allowed = {"survival", "tracking_xy", "tracking_yaw", "completion",
                   "post_push_tracking", "recovery_rate_upright"}
        for row in self.detail:
            with self.subTest(case=f"{row['case']}@{row['seed']}"):
                self.assertIn(row["binding_factor"], allowed)
                self.assertEqual(row["kind"], "측정", "case 행은 전부 측정이다")

    def test_5_stairs_cases_carry_a_completion_column(self) -> None:
        """계단 case 의 전진거리 칸이 비어 있으면 completion 구속을 볼 수 없다."""
        stairs = [r for r in self.detail if r["case"].startswith("stairs_")]
        self.assertEqual(len(stairs), 12, "계단 case 는 4종 x 3 seed 다")
        for row in stairs:
            with self.subTest(case=f"{row['case']}@{row['seed']}"):
                self.assertIsNotNone(row["completion"])
                self.assertIsNotNone(row["progress_m"])


if __name__ == "__main__":
    unittest.main()
