"""보호 허용 손실 판 `post_a048_guard_margin_v1` 의 계약 (2026-09-26 사용자 선택·사전등록).

근거: `workspace/training/quadruped/reports/GO2_GUARD_DESIGN_COMPARISON_20260926.md` §6~§7.

  1. 기존 판은 바이트 그대로다 — 저장된 G-A043·G-A044·G-A048 판정을 각자의 판으로 다시 내면 실패 목록이 같다.
     G-A048 은 post_a043_push4_v1 로 INTERNAL_GATE_FAIL 그대로다(새 판을 소급 적용하지 않는다).
  2. 새 판의 값은 비교 도구의 margin_split_dedup 과 같다(한쪽만 고치면 깨진다).
  3. 새 판은 보호 14검사(낙상 8 + 추종 6)이고 생존 검사가 없다.  개선 9검사는 post_a043_push4_v1 과 같다.
  4. 여유는 정확히 경계에서 통과한다(≤ 기준선 + L, ≥ −L).
  5. 기본 판과 사양 없는 호출은 여전히 여유 0 이다.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_guard_design_compare as compare  # noqa: E402
import go2_screening_gate as gate  # noqa: E402

NEW = "post_a048_guard_margin_v1"
STORED = (
    ("go2_g_a043_a033_lin_vel_z_m15", "post_a042_push_v1"),
    ("go2_g_a044_a033_lin_vel_z_m175", "post_a043_push4_v1"),
    ("go2_g_a048_a033_lin_vel_z_m125", "post_a043_push4_v1"),
)


def rows(value: float, falls: int) -> dict:
    """모든 case·seed 가 같은 값인 합성 행(판정식만 시험한다)."""
    out = {}
    for case_id in gate.RULE_VERSIONS[NEW]:
        for seed in gate.SEEDS:
            out[(case_id, seed)] = {"missing": [], "fingerprint": None, "posture_falls": falls,
                                    "survival": value, "tracking": value, "progress_m": 1.0,
                                    "ge1": 1, "ge2": 1, "stall_share": 0.5}
    return out


class GuardMarginRuleTest(unittest.TestCase):
    def test_1_stored_verdicts_are_reproduced_by_their_own_editions(self) -> None:
        for keep, version in STORED:
            with self.subTest(keep=keep):
                harvest = ROOT / "workspace/_keep" / keep
                stored = json.loads((harvest / "harvest_verification.json").read_text(encoding="utf-8"))
                self.assertIsNone(gate.guard_margin(version))
                again = gate.screen(harvest, cases=gate.cases_for(version),
                                    improvement=gate.improvement_required(version),
                                    margin=gate.guard_margin(version))
                self.assertEqual(again["failed"], stored["plan_screening"]["failed"])
                self.assertEqual(again["verdict"], stored["plan_screening"]["verdict"])
        a048 = json.loads((ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/harvest_verification.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(a048["plan_screening"]["verdict"], gate.FAIL)

    def test_2_values_match_the_design_comparison(self) -> None:
        m = gate.GUARD_MARGINS[NEW]
        for case_id in gate.RULE_VERSIONS[NEW]:
            expected = compare.SPLIT_L_FALLS_POOLED if case_id in compare.SPLIT_FALL_CASES else compare.L_FALLS_POOLED
            self.assertEqual(m["falls_pooled"].get(case_id, m["falls_pooled"]["default"]), expected, case_id)
        for case_id in compare.rs.TRACKED:
            expected = -compare.SPLIT_L_TRACK if case_id in compare.SPLIT_TRACK_CASES else -compare.L_TRACK
            self.assertAlmostEqual(m["tracking"].get(case_id, m["tracking"]["default"]), expected, places=12)

    def test_3_check_set(self) -> None:
        report = gate.judge(rows(0.5, 5), rows(0.5, 5), gate.RULE_VERSIONS[NEW], True, gate.guard_margin(NEW))
        guard = [c["check"] for c in report["checks"] if c["group"] == "guard"]
        self.assertEqual(len(guard), 14)
        self.assertFalse([c for c in guard if "survival" in c])
        old = gate.judge(rows(0.5, 5), rows(0.5, 5), gate.RULE_VERSIONS["post_a043_push4_v1"], True, None)
        self.assertEqual([c["check"] for c in report["checks"] if c["group"] != "guard"],
                         [c["check"] for c in old["checks"] if c["group"] != "guard"])

    def _tracking_failures(self, offset: float) -> list[str]:
        """모든 추종 case 의 후보 값을 (기준선 − 허용 손실 + offset) 으로 두고 실패한 추종 검사를 돌려준다."""
        margin = gate.guard_margin(NEW)
        base, cand = rows(0.5, 5), rows(0.5, 5)
        for (case_id, _seed), row in cand.items():
            row["tracking"] = 0.5 - margin["tracking"].get(case_id, margin["tracking"]["default"]) + offset
        report = gate.judge(base, cand, gate.RULE_VERSIONS[NEW], True, margin)
        return [c["check"] for c in report["checks"] if "tracking" in c["check"] and not c["ok"]]

    def test_4_margins_are_inclusive(self) -> None:
        # 낙상 — 정수: 정확히 경계는 통과, 한 대 넘으면 실패.
        margin = gate.guard_margin(NEW)
        base, cand = rows(0.5, 5), rows(0.5, 5)
        for (case_id, seed), row in cand.items():
            allowed = margin["falls_pooled"].get(case_id, margin["falls_pooled"]["default"])
            row["posture_falls"] = 5 + (allowed if seed == gate.SEEDS[0] else 0)
        report = gate.judge(base, cand, gate.RULE_VERSIONS[NEW], True, margin)
        self.assertEqual([c["check"] for c in report["checks"] if "posture falls" in c["check"] and not c["ok"]], [])
        for row in cand.values():
            row["posture_falls"] += 1
        report = gate.judge(base, cand, gate.RULE_VERSIONS[NEW], True, margin)
        self.assertEqual(len([c for c in report["checks"] if "posture falls" in c["check"] and not c["ok"]]), 8)

    def test_4b_tracking_boundary_is_inclusive_with_declared_tolerance(self) -> None:
        # 정확히 경계: 실수 뺄셈 오차(-0.010000000000000009 등)가 있어도 통과해야 한다.
        self.assertEqual(self._tracking_failures(0.0), [])
        # 경계 바로 안쪽: 통과.
        self.assertEqual(self._tracking_failures(+1e-6), [])
        # 경계 바깥쪽(허용 오차보다 확실히 큼): 여섯 추종 검사 모두 실패.
        self.assertEqual(len(self._tracking_failures(-1e-6)), 6)
        # 허용 오차는 선언된 값 하나이고, proxy 흔들림보다 충분히 작다.
        self.assertLess(gate.TRACKING_TOLERANCE, 1e-6)

    def test_4c_old_editions_keep_the_strict_zero_comparison(self) -> None:
        # 기존 판은 오차 처리 없이 delta >= 0 그대로다 — 아주 작은 음수도 실패한다.
        base, cand = rows(0.5, 5), rows(0.5, 5)
        for row in cand.values():
            row["tracking"] = 0.5 - 1e-12
        report = gate.judge(base, cand, gate.RULE_VERSIONS["post_a043_push4_v1"], True, None)
        self.assertEqual(len([c for c in report["checks"] if "tracking" in c["check"] and not c["ok"]]), 6)

    def test_5_defaults_stay_zero_margin(self) -> None:
        self.assertIsNone(gate.guard_margin(None))
        for version in ("forward_stairs_v1", "post_a042_push_v1", "post_a043_push4_v1", "g3_guard_push4_v1"):
            self.assertIsNone(gate.guard_margin(version))
        self.assertIn(NEW, gate.RULE_VERSIONS)


if __name__ == "__main__":
    unittest.main()
