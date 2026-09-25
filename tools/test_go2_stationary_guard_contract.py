"""1단계 정지 관문이 **실제로 발화하는지** 가짜 수확물로 시험한다.

결함 S-4(2026-09-19): `stationary_guard_scenarios` 를 읽는 곳이
`tools/verify_go2_basic_motion_harvest.py` 하나뿐이어서, 서 있기 편법은 전체 단계에서만
잡히고 1단계는 평지 파국 case 하나로 버티고 있었다.  G-A038 이 그 구멍의 실증이다 —
평지를 12.3 m 걷고 계단에서만 웅크렸는데 파국 case 가 통과했다.

관문을 코드에 적는 것은 준수가 아니다.  이 파일은 관문이 **막아야 할 것을 실제로 막는지**를
합성 기록으로 확인한다.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import go2_target_gate as gate

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "workspace/training/quadruped/config/experiments/G_A040_a033_flat_orientation_m05.json"

WALKING = {"speed_xy_mean": 0.62, "tracking_xy_rmse": 0.21}
CROUCHED = {"speed_xy_mean": 0.02, "tracking_xy_rmse": 0.48}
PREREG = {"stationary_guard_scenarios": ["G1", "G3", "G4"], "max_new_stationary_cases_in_guard": 0}


def records(pairs: dict[str, tuple[dict, dict]]) -> dict[tuple[str, str], dict]:
    """{entry: (baseline_raw, candidate_raw)} -> 게이트가 만드는 records 모양."""
    out: dict[tuple[str, str], dict] = {}
    for entry, (base, cand) in pairs.items():
        out[("baseline", entry)] = {"raw": base, "proxy": 0.0}
        out[("candidate", entry)] = {"raw": cand, "proxy": 0.0}
    return out


class StationaryGuardContractTest(unittest.TestCase):
    def test_1_a_candidate_that_stops_in_a_guard_scenario_is_caught(self) -> None:
        got = gate.stationary_reading(
            records({"G3:rough_forward:101": (WALKING, CROUCHED)}), PREREG)
        self.assertFalse(got["passed"], "감시 시나리오에서 멈춘 후보가 통과했다")
        self.assertEqual(got["new_stationary"], ["G3:rough_forward:101"])

    def test_2_a_candidate_that_keeps_walking_passes(self) -> None:
        got = gate.stationary_reading(
            records({"G3:rough_forward:101": (WALKING, WALKING)}), PREREG)
        self.assertTrue(got["passed"])
        self.assertEqual(got["new_stationary"], [])

    def test_3_scenarios_outside_the_guard_are_not_judged(self) -> None:
        """계단(G5)은 감시 밖이다 — A017 이 이미 stairs_15_down 에서 서 있기 때문이다."""
        got = gate.stationary_reading(
            records({"G5:stairs_15_up:101": (WALKING, CROUCHED)}), PREREG)
        self.assertTrue(got["passed"])
        self.assertEqual(got["read_cases"], 0)

    def test_4_a_baseline_that_already_stood_is_not_counted_as_new(self) -> None:
        got = gate.stationary_reading(
            records({"G3:rough_forward:101": (CROUCHED, CROUCHED)}), PREREG)
        self.assertTrue(got["passed"])
        self.assertEqual(got["baseline_stationary"], ["G3:rough_forward:101"])
        self.assertEqual(got["new_stationary"], [])

    def test_5_both_halves_of_the_criterion_are_required(self) -> None:
        """느리기만 하거나 빗나가기만 한 것은 정지가 아니다 — 기준은 두 조건의 곱이다."""
        slow_but_tracking = {"speed_xy_mean": 0.02, "tracking_xy_rmse": 0.05}
        fast_but_wandering = {"speed_xy_mean": 0.62, "tracking_xy_rmse": 0.48}
        for raw in (slow_but_tracking, fast_but_wandering):
            with self.subTest(raw):
                got = gate.stationary_reading(
                    records({"G3:rough_forward:101": (WALKING, raw)}), PREREG)
                self.assertTrue(got["passed"])

    def test_6_a_spec_without_the_keys_says_so_instead_of_passing_silently(self) -> None:
        got = gate.stationary_reading(records({"G3:rough_forward:101": (WALKING, CROUCHED)}), {})
        self.assertFalse(got["declared"], "선언이 없는데 선언된 것처럼 보고하면 안 된다")
        self.assertTrue(got["passed"])

    def test_7_the_criterion_matches_the_scorer(self) -> None:
        """게이트가 채점기와 다른 자를 쓰면 두 단계의 판정이 갈라진다."""
        scorer = (ROOT / "workspace/training/quadruped/go2_fixed_eval_report.py").read_text(encoding="utf-8")
        self.assertIn('("speed_xy_mean") or 0.0) < 0.10', scorer)
        self.assertIn('("tracking_xy_rmse") or 0.0) >= 0.30', scorer)
        self.assertEqual((gate.STATIONARY_SPEED, gate.STATIONARY_RMSE), (0.10, 0.30))

    def test_8_the_live_spec_is_actually_covered_in_stage_1(self) -> None:
        """G-A040 로 실측: 이 관문이 1단계에서 몇 case 를 덮는가.

        덮이지 않는 시나리오(G2·G6)는 1단계가 그 case 를 **측정하지 않기 때문**이고, 그것은
        이 관문이 아니라 1단계 범위의 한계다.  숨기지 않고 여기 적는다.
        """
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        prereg = spec["preregistered"]
        entries = [spec["evaluation"]["catastrophe_case"], *gate.targets(spec)]
        guard = set(prereg["stationary_guard_scenarios"])
        covered = sorted({e.split(":")[0] for e in entries} & guard)
        self.assertEqual(covered, ["G1", "G3", "G4"])
        got = gate.stationary_reading(records({e: (WALKING, WALKING) for e in entries}), prereg)
        self.assertEqual(got["read_cases"], 10, "1단계 정지 감시 대상 case 수")
        self.assertEqual(sorted(guard - set(covered)), ["G2", "G6", "G7"],
                         "1단계가 측정하지 않아 덮이지 않는 시나리오 — 전체 단계에서만 본다")


if __name__ == "__main__":
    unittest.main()
