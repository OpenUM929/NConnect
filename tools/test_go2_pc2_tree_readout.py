"""PC2 탐색트리 판독·진행 규칙 계약 테스트 (계획 GO2_TRACK_FIXED_SEARCH_TREE_20261003.md §12·§13, Codex §37-2).

python -B -m unittest tools.test_go2_pc2_tree_readout
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_pc2_tree_readout as t  # noqa: E402

S = ("101", "202", "303")


def same(v):
    return {s: v for s in S}


def res(name, role, cand, ref, good):
    return {"name": name, "role": role, **t.compare_indicator(cand, ref, good)}


class Classify(unittest.TestCase):
    """§12-4 우선순위와 §33 R2 반례."""

    def test_insufficient_first(self):
        r = [res("T", "target", same(1), same(5), "down")]
        self.assertEqual(t.classify(["report 누락"], "MOVING", r)["class"], "INSUFFICIENT")
        r = [res("T", "target", {"101": 1, "202": None, "303": 1}, same(5), "down")]
        self.assertEqual(t.classify([], "MOVING", r)["class"], "INSUFFICIENT")

    def test_stationary_beats_target_improvement(self):
        r = [res("T", "target", same(1), same(5), "down")]
        self.assertEqual(t.classify([], "STATIONARY", r)["class"], "WORSENED")

    def test_protection_only_loss_is_worsened_not_flat(self):
        # 표적은 부모와 같고 10cm ≥2단만 세 seed 모두 감소 → WORSENED (초판 FLAT→N4 결함)
        r = [res("T", "target", same(5), same(5), "down"), res("S10", "protect", same(20), same(26), "up")]
        self.assertEqual(t.classify([], "MOVING", r)["class"], "WORSENED")

    def test_improvement_plus_loss_is_tradeoff(self):
        r = [res("T", "target", same(1), same(5), "down"), res("Syaw", "protect", same(0.3), same(0.2), "down")]
        self.assertEqual(t.classify([], "MOVING", r)["class"], "TRADEOFF")

    def test_clean_improvement(self):
        r = [res("T", "target", same(1), same(5), "down"), res("S", "protect", same(10), same(10), "up")]
        self.assertEqual(t.classify([], "MOVING", r)["class"], "IMPROVED")

    def test_mixed_is_no_consistent_change(self):
        r = [res("T", "target", {"101": 3, "202": 3, "303": 9}, same(5), "down")]
        v = t.classify([], "MOVING", r)
        self.assertEqual(v["class"], "NO_CONSISTENT_CHANGE")
        self.assertEqual(v["partial_seed_losses"], {"T": ["303"]})

    def test_motion_rule(self):
        p = {"abs_error": 0.1, "rmse": 0.2}
        self.assertEqual(t.seed_dir("motion", {"abs_error": 0.09, "rmse": 0.21}, p), "worse")
        self.assertEqual(t.seed_dir("motion", {"abs_error": 0.09, "rmse": 0.19}, p), "better")
        self.assertEqual(t.seed_dir("motion", {"abs_error": 0.1, "rmse": 0.19}, p), "same")


class NonStall(unittest.TestCase):
    """§13-1 예 a~d: 32대 기준 '≥2단 도달 후 비정체 개체 수'."""

    def nonstall(self, reached, stalled):
        orig = t.pr.stairs_post_reach
        t.pr.stairs_post_reach = lambda *a: {"reached_ge2": reached, "stalled_after_reach": stalled}
        try:
            return t.nonstall(Path("."), "101", "stairs_15_down", 0.15)
        finally:
            t.pr.stairs_post_reach = orig

    def test_a_more_reach_is_improvement(self):
        a, b = self.nonstall(1, 1), self.nonstall(10, 2)
        self.assertEqual((a["value"], b["value"]), (0, 8))
        self.assertEqual(t.compare_indicator(same(8), same(0), "up")["label"], "COMMON_IMPROVEMENT")

    def test_b_fewer_stalls_from_fewer_reach_is_loss(self):
        self.assertEqual(self.nonstall(1, 0)["value"], 1)
        self.assertEqual(t.compare_indicator(same(1), same(8), "up")["label"], "COMMON_LOSS")

    def test_c_zero_reach_not_applicable_rate(self):
        n = self.nonstall(0, 0)
        self.assertEqual((n["value"], n["conditional_stall_rate"]), (0, "NOT_APPLICABLE"))
        self.assertEqual(t.compare_indicator(same(0), same(0), "up")["label"], "NO_COMMON_DIRECTION")

    def test_d_reach_without_nonstall_votes_on_ge2_only(self):
        self.assertEqual(self.nonstall(3, 3)["value"], 0)
        self.assertEqual(t.compare_indicator(same(0), same(0), "up")["label"], "NO_COMMON_DIRECTION")
        self.assertEqual(t.compare_indicator(same(3), same(0), "up")["label"], "COMMON_IMPROVEMENT")

    def test_missing_post_reach_is_missing_not_zero(self):
        orig = t.pr.stairs_post_reach
        t.pr.stairs_post_reach = lambda *a: None
        try:
            self.assertIsNone(t.nonstall(Path("."), "101", "stairs_15_down", 0.15))
        finally:
            t.pr.stairs_post_reach = orig
        self.assertEqual(t.compare_indicator({"101": None, "202": 1, "303": 1}, same(0), "up")["label"], "MISSING")


class SameSeedParent(unittest.TestCase):
    """§13-2: 손실은 실제 비교 부모의 같은 seed 값 대비."""

    def test_p2_vs_p0(self):
        c = t.compare_indicator({"101": 1, "202": 1, "303": 0}, same(0), "down")
        self.assertEqual((c["label"], c["worse_seeds"]), ("NO_COMMON_DIRECTION", ["101", "202"]))

    def test_n5_vs_p2(self):
        c = t.compare_indicator(same(1), {"101": 1, "202": 1, "303": 0}, "down")
        self.assertEqual((c["label"], c["worse_seeds"]), ("NO_COMMON_DIRECTION", ["303"]))


class Eligibility(unittest.TestCase):
    """§12-5 / §33 R3 재현: 보호 10/10/10 → N3 9/10/10 → N4 9/9/9."""

    def test_n4_ineligible_against_parent(self):
        tgt = res("T", "target", same(1), same(5), "down")
        n3 = t.classify([], "MOVING", [tgt, res("S", "protect", {"101": 9, "202": 10, "303": 10}, same(10), "up")])
        n4 = t.classify([], "MOVING", [tgt, res("S", "protect", same(9), same(10), "up")])
        self.assertEqual((n3["class"], n4["class"]), ("IMPROVED", "TRADEOFF"))
        w = t.select_winner({"n3": n3["class"], "n4": n4["class"]}, ["n3", "n4"], sibling_class="IMPROVED")
        self.assertEqual(w["winner"], "n3")

    def test_no_eligible_keeps_parent(self):
        w = t.select_winner({"n3": "NO_CONSISTENT_CHANGE", "n4": "WORSENED"}, ["n3", "n4"], None)
        self.assertIsNone(w["winner"])

    def test_both_eligible_needs_sibling_read(self):
        self.assertEqual(t.select_winner({"n3": "IMPROVED", "n4": "IMPROVED"}, ["n3", "n4"], None).get("pending"),
                         "SIBLING_READ")
        self.assertEqual(t.select_winner({"n3": "IMPROVED", "n4": "IMPROVED"}, ["n3", "n4"], "IMPROVED")["winner"], "n4")
        self.assertEqual(t.select_winner({"n3": "IMPROVED", "n4": "IMPROVED"}, ["n3", "n4"], "TRADEOFF")["winner"], "n3")


class TreeProgress(unittest.TestCase):
    """§12-7 + §13-3."""
    N3, N4, N5, N6 = (k for _, pts in t.TREE for k, _ in pts)

    def step(self, nodes, siblings=None):
        return t.next_step({"nodes": nodes, "siblings": siblings or {}})

    def test_first_node_is_n3(self):
        s = self.step({})
        self.assertEqual((s["action"], s["node"], s["value"], s["parent_changes"]), ("RUN", self.N3, -1e-4, {}))

    def test_unrecoverable_stops_and_emits_no_next_key(self):
        for nodes in ({self.N3: "INSUFFICIENT_UNRECOVERABLE"},
                      {self.N3: "IMPROVED", self.N4: "INSUFFICIENT_UNRECOVERABLE"},
                      {self.N3: "WORSENED", self.N5: "INSUFFICIENT_UNRECOVERABLE"}):
            s = self.step(nodes)
            self.assertEqual(s["action"], "STOP")
            self.assertNotEqual(s.get("action"), "RUN")

    def test_post_training_collection_failure_recovers_eval_only(self):
        s = self.step({self.N3: "INSUFFICIENT"})
        self.assertEqual((s["action"], s["node"]), ("RECOVER_EVAL_ONLY", self.N3))

    def test_excluded_predecessor_skips_dependent_child(self):
        s = self.step({self.N3: "EXCLUDED_HISTORY"})
        self.assertEqual((s["action"], s["node"], s["parent_changes"]), ("RUN", self.N5, {}))
        s = self.step({self.N3: "EXCLUDED_HISTORY", self.N5: "EXCLUDED_HISTORY"})
        self.assertEqual(s["action"], "END")

    def test_tradeoff_or_worsened_closes_variable(self):
        for c in ("TRADEOFF", "WORSENED"):
            s = self.step({self.N3: c})
            self.assertEqual((s["action"], s["node"], s["parent_changes"]), ("RUN", self.N5, {}))

    def test_no_consistent_change_runs_second_value_once_then_keeps_parent(self):
        s = self.step({self.N3: "NO_CONSISTENT_CHANGE"})
        self.assertEqual((s["action"], s["node"]), ("RUN", self.N4))
        s = self.step({self.N3: "NO_CONSISTENT_CHANGE", self.N4: "WORSENED"})
        self.assertEqual((s["action"], s["node"], s["parent_changes"]), ("RUN", self.N5, {}))

    def test_winner_carried_into_next_parent(self):
        s = self.step({self.N3: "IMPROVED", self.N4: "EXCLUDED_HISTORY"})
        self.assertEqual((s["node"], s["parent_changes"]), (self.N5, {"dof_torques_l2": -1e-4}))
        s = self.step({self.N3: "IMPROVED", self.N4: "IMPROVED"})
        self.assertEqual(s["action"], "SIBLING_READ")
        s = self.step({self.N3: "IMPROVED", self.N4: "IMPROVED"}, {"dof_torques_l2": "IMPROVED"})
        self.assertEqual((s["node"], s["parent_changes"]), (self.N5, {"dof_torques_l2": -5e-5}))

    def test_end_reports_final_parent(self):
        s = self.step({self.N3: "IMPROVED", self.N4: "WORSENED", self.N5: "WORSENED"})
        self.assertEqual((s["action"], s["parent_changes"]), ("END", {"dof_torques_l2": -1e-4}))

    def test_tree_values_not_previously_tested(self):
        # 같은 항·같은 값 이력 제외 규칙(§1-3): 트리 값은 원장·시험 이력에 없는 값이어야 한다.
        # 시험 이력 참고본·증거 원장에서 dof_torques 는 변경 기록이 없고, dof_acc 변경 행은 모두 미실행(G-A039·G-A053)이다.
        for rel in ("workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md", "GO2_REWARD_EVIDENCE_MASTER.md"):
            for line in (ROOT / rel).read_text(encoding="utf-8").splitlines():
                if line.startswith("| G-A") and ("dof_acc" in line or "dof_torques" in line):
                    self.assertIn("미실행", line, f"{rel}: {line[:80]}")
        keep = [p.name for p in (ROOT / "workspace/_keep").iterdir()]
        self.assertFalse([n for n in keep if "dof_torques" in n or "dof_acc" in n])
        self.assertEqual([v for _, pts in t.TREE for _, v in pts], [-1e-4, -5e-5, -1.25e-7, -6.25e-8])


class TreeStateGuards(unittest.TestCase):
    """§39-R1·R2 회귀: 형제 판독 오류·미지원 상태는 다음 학습(RUN)을 열지 않는다."""
    N3, N4, N5, N6 = (k for _, pts in t.TREE for k, _ in pts)

    def step(self, nodes, siblings=None):
        return t.next_step({"nodes": nodes, "siblings": siblings or {}})

    def test_sibling_insufficient_recovers_read_only(self):
        s = self.step({self.N3: "IMPROVED", self.N4: "IMPROVED"}, {"dof_torques_l2": "INSUFFICIENT"})
        self.assertEqual((s["action"], s["parent_changes"]), ("RECOVER_SIBLING_READ", {}))
        self.assertNotIn("node", s)

    def test_sibling_unrecoverable_stops(self):
        s = self.step({self.N3: "IMPROVED", self.N4: "IMPROVED"}, {"dof_torques_l2": "INSUFFICIENT_UNRECOVERABLE"})
        self.assertEqual((s["action"], s["parent_changes"]), ("STOP", {}))

    def test_sibling_tradeoff_or_flat_keeps_smaller_value(self):
        for c in ("TRADEOFF", "NO_CONSISTENT_CHANGE", "WORSENED"):
            s = self.step({self.N3: "IMPROVED", self.N4: "IMPROVED"}, {"dof_torques_l2": c})
            self.assertEqual((s["action"], s["node"], s["parent_changes"]), ("RUN", self.N5, {"dof_torques_l2": -1e-4}), c)

    def test_unsupported_values_raise(self):
        bad = [
            {"nodes": {self.N3: "TYPO"}}, {"nodes": {self.N3: None}}, {"nodes": {self.N3: "RUNNING"}},
            {"nodes": {self.N3: "IMPROVED", self.N4: "TYPO"}}, {"nodes": {self.N3: "IMPROVED", self.N4: None}},
            {"nodes": {self.N3: "IMPROVED", self.N4: "IMPROVED"}, "siblings": {"dof_torques_l2": "TYPO"}},
            {"nodes": {self.N3: "IMPROVED", self.N4: "IMPROVED"}, "siblings": {"dof_torques_l2": "EXCLUDED_HISTORY"}},
            {"nodes": {"n9_unknown": "IMPROVED"}}, {"nodes": {}, "siblings": {"feet_air_time": "IMPROVED"}},
            {"nodes": [], "siblings": {}}, {"nodes": {}, "extra": 1}, [],
            {"nodes": {self.N3: "WORSENED", self.N4: "IMPROVED"}},
            {"nodes": {self.N4: "IMPROVED"}},
        ]
        for st in bad:
            with self.assertRaises(t.TreeStateError, msg=repr(st)):
                t.next_step(st)

    def test_pre_recorded_history_exclusion_is_allowed(self):
        s = self.step({self.N4: "EXCLUDED_HISTORY"})
        self.assertEqual((s["action"], s["node"]), ("RUN", self.N3))
        s = self.step({self.N3: "IMPROVED", self.N4: "EXCLUDED_HISTORY"})
        self.assertEqual((s["node"], s["parent_changes"]), (self.N5, {"dof_torques_l2": -1e-4}))

    def test_select_winner_refuses_non_performance_classes(self):
        with self.assertRaises(t.TreeStateError):
            t.select_winner({"a": "INSUFFICIENT", "b": "IMPROVED"}, ["a", "b"], None)
        with self.assertRaises(t.TreeStateError):
            t.select_winner({"a": "IMPROVED", "b": "IMPROVED"}, ["a", "b"], "TYPO")

    def test_cli_next_rejects_bad_state(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            p.write_text(json.dumps({"nodes": {self.N3: "TYPO"}}), encoding="utf-8")
            self.assertEqual(t.main(["next", "--tree-state", str(p)]), 2)


X = ROOT / "workspace/server_returns/G-A060/extracted"


@unittest.skipUnless((X / "go2_g_a060_pc2_a048_seed42").is_dir(), "G-A060 회수 압축 해제본 없음")
class RealHarvest(unittest.TestCase):
    def test_snapshot_and_known_worsened_point(self):
        b1, ang = X / "go2_g_a060_pc2_a048_seed42", X / "go2_g_a060_pc2_ang_vel_xy_l2_m0p08"
        self.assertIsNone(t.snapshot_problem(ang, b1, {"ang_vel_xy_l2": -0.08}))
        self.assertIn("MISMATCH", t.snapshot_problem(ang, b1, {"dof_torques_l2": -1e-4}))
        self.assertEqual(t.rewards_all(b1)["dof_torques_l2"], -2e-4)
        r = t.read("ang_vel_xy_l2_m0p08", ang, b1, {"ang_vel_xy_l2": -0.08}, "a048_seed42")
        self.assertEqual(r["verdict"]["class"], "WORSENED")


if __name__ == "__main__":
    unittest.main()
