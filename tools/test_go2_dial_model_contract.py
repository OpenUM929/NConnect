"""다이얼 모델이 스스로를 과신하지 못하게 잡아두는 관문.

지난번에 표본 안 r² 0.935를 예측력으로 인용했고, 그 모델은 유일한 성공 A017을
실패로 예측했다. 그래서 여기서는 교차검증 수치만 계약으로 둔다.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from go2_dial_model import (DRIVER, KILL_AT, KILL_DIAL, MODEL_STATUS, REFUTING_RUNS,  # noqa: E402
                            cross_validate, design, fit, predict, refutation, split)


class DialModelContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.all_rows = design()
        cls.rows, cls.refuting = split(cls.all_rows)   # 모델을 세운 표본 (09-16 종합의 15회차)
        cls.model = fit(cls.rows)
        cls.cv = cross_validate(cls.rows)

    def test_1_the_experiment_is_actually_a_designed_one(self) -> None:
        """다이얼 말고 다른 것이 섞이면 이 모델의 전제가 깨진다."""
        self.assertGreaterEqual(len(self.rows), 15)
        runs = {r["run"] for r in self.rows}
        self.assertNotIn("g_a025_flat_orientation_m1", runs, "재현 회차를 두 번 셌다")
        self.assertNotIn("g_a010_lin_vel_z_m2_v2_260906", runs, "재현 회차를 두 번 셌다")

    def test_2_model_beats_guessing_the_mean_out_of_sample(self) -> None:
        """표본 안 적합도가 아니라 교차검증으로만 성능을 주장한다."""
        self.assertLess(self.cv["mae"], self.cv["mae_baseline"] * 0.5)
        self.assertLess(self.cv["mae_supported"], 0.30)

    def test_3_the_kill_rule_is_exact_where_it_applies(self) -> None:
        dead = [r for r in self.rows if r["dials"][KILL_DIAL] <= KILL_AT]
        self.assertEqual(len(dead), 2)
        for row in dead:
            self.assertEqual(row["terrain"], 0.0, row["run"])

    def test_4_the_driver_has_a_threshold_not_a_slope(self) -> None:
        """1.2 -> 1.4 도약이 사라지면 선형 모델로 돌아가도 된다는 뜻이라 알아야 한다."""
        levels = self.model["levels"]
        self.assertGreater(levels[1.4]["mean"], levels[1.2]["mean"] * 3)
        self.assertLess(levels[1.2]["mean"], levels[1.0]["mean"] * 2.5)

    def test_5_unobserved_levels_are_reported_as_unsupported(self) -> None:
        """관측 없는 다이얼 값에 대해 조용히 숫자를 내면 안 된다."""
        value, basis = predict(self.model, {DRIVER: 9.9, KILL_DIAL: -0.05})
        self.assertIn("지지 없음", basis)
        self.assertIsInstance(value, float)
        supported, reason = predict(self.model, {DRIVER: 1.4, KILL_DIAL: -0.05})
        self.assertNotIn("지지 없음", reason)
        self.assertAlmostEqual(supported, self.model["levels"][1.4]["mean"], places=6)

    def test_6_the_one_level_with_a_single_observation_stays_flagged(self) -> None:
        """track 1.5는 관측 1건이라 교차검증이 불가능하다. 그 사실이 남아야 한다."""
        self.assertEqual(self.model["levels"][1.5]["n"], 1)
        self.assertIn("g_a033_a017_track_lin_vel_xy_150", self.cv["unsupported"])

    def test_7_the_model_predicts_a017_as_a_success(self) -> None:
        """이전 모델은 유일한 성공을 실패로 예측했다. 그 실패가 재발하면 여기서 걸린다."""
        a017 = next(d for d in self.cv["detail"] if d["run"].startswith("g_a017"))
        self.assertGreater(a017["predicted"], 3.0, "A017을 다시 저조하게 예측한다")
        self.assertLess(abs(a017["error"]), 0.6)


    def test_8_g_a038_refutes_rule_2(self) -> None:
        """새 표본이 모델을 깨면 모델을 고치지 말고 반박으로 적는다(사후 적합 금지).

        G-A038은 track 1.5·ang_vel_xy -0.08(사망 규칙 밖)인데 terrain@999가 G-A033보다 크게 낮다.
        """
        self.assertEqual(len(self.rows), 15)
        self.assertEqual([r["run"] for r in self.refuting], list(REFUTING_RUNS))
        self.assertEqual(MODEL_STATUS, "REFUTED_BY_G_A038")
        (g38,) = self.refuting
        self.assertGreater(g38["dials"][KILL_DIAL], KILL_AT)
        self.assertEqual(g38["dials"][DRIVER], 1.5)
        (d,) = refutation(self.all_rows)
        self.assertIn(f"{DRIVER}=1.5", d["basis"])
        self.assertLess(d["error"], -1.0, "track 1.5 수준평균보다 1 넘게 낮아야 반박이다")
        with_refuting = cross_validate(self.all_rows)
        self.assertGreaterEqual(with_refuting["mae_supported"], 0.30, "반박 표본을 넣으면 계약 성능을 못 지킨다")


if __name__ == "__main__":
    unittest.main()
