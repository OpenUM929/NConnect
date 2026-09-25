"""표 귀속 게이트 계약.

`go2_claim_check` 는 "이 숫자가 어딘가 있느냐"만 묻는다.  §7 에서 G3 칸과 G4 칸을
맞바꿔 적어도 통과한다 — 둘 다 표 안의 숫자이기 때문이다.  실제로 내가 틀린 방식이
바로 그 종류였다(축이 다른 두 값을 곱함, 다른 짝의 rmse 를 같은 짝에 붙임).
그래서 존재 게이트만으로는 부족하고, 이 파일이 귀속을 지킨다.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_table_audit as audit  # noqa: E402

# 바인딩은 늘기만 한다. 표를 새로 쓰면서 바인딩을 안 걸면 그 표는 검사되지 않는다.
MIN_BINDINGS = 5


class TableAuditContractTest(unittest.TestCase):
    def test_1_no_cell_disagrees_with_its_artifact(self) -> None:
        mismatch, _ = audit.audit()
        self.assertEqual(mismatch, [], "\n" + "\n".join(mismatch))

    def test_2_no_cell_is_left_unbound(self) -> None:
        """미바인딩은 '검사하지 않은 칸'이다. 조용히 두면 게이트에 구멍이 남는다."""
        _, unbound = audit.audit()
        self.assertEqual(unbound, [], "\n" + "\n".join(unbound))

    def test_3_binding_count_does_not_shrink(self) -> None:
        self.assertGreaterEqual(len(audit.BINDINGS), MIN_BINDINGS)

    def test_4_every_binding_anchor_still_resolves(self) -> None:
        """문서를 고치다 앵커가 사라지면 그 표는 조용히 검사에서 빠진다. 시끄럽게 만든다."""
        for label, path, anchor, _resolver in audit.BINDINGS:
            with self.subTest(label):
                header, rows = audit.table_after(path, anchor)
                self.assertGreater(len(rows), 0, label)
                self.assertGreater(len(header), 1, label)

    def test_5_swapping_two_cells_is_detected(self) -> None:
        """통과하는 귀속 검사가 아무것도 안 하고 있을 수 있다. 바꿔치기해서 확인한다."""
        truth = audit.margin_lookup()
        g3, g4 = truth[("Δ", "G3")], truth[("Δ", "G4")]
        self.assertNotAlmostEqual(g3, g4, places=2,
                                  msg="두 값이 같으면 이 검사가 무의미하다")
        swapped = dict(truth)
        swapped[("Δ", "G3")], swapped[("Δ", "G4")] = g4, g3
        # BINDINGS 는 함수 객체를 직접 담는다. 모듈 속성만 바꿔치면 튜플 안의 참조는
        # 그대로라 아무 일도 일어나지 않는다 — 처음 판이 그래서 '통과'했다.
        original = audit.BINDINGS
        audit.BINDINGS = tuple(
            (label, path, anchor, (lambda: swapped) if resolver is audit.margin_lookup else resolver)
            for label, path, anchor, resolver in original)
        try:
            mismatch, _ = audit.audit()
            self.assertTrue(any("G3" in m or "G4" in m for m in mismatch),
                            "칸을 맞바꿨는데 잡히지 않았다")
        finally:
            audit.BINDINGS = original

    def test_6_sign_is_part_of_the_claim(self) -> None:
        """부호가 뒤집힌 값을 같다고 보면 '올랐다/내렸다'가 검사되지 않는다."""
        self.assertIsNotNone(audit.number("-0.743"))
        self.assertNotEqual(audit.number("+0.743"), audit.number("-0.743"))
        self.assertEqual(audit.number("−0.743"), -0.743, "유니코드 빼기를 못 읽는다")


if __name__ == "__main__":
    unittest.main()
