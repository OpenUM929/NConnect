"""변수별 영향도 전수 판독 관문 (2026-09-17 사용자 지시: 모든 변수를 track처럼 검수).

지키는 것:
  1. 보고서는 증거 CSV에서 글자 그대로 생성된다(손으로 고친 표가 없다).
  2. 쌍 원장(PAIRS.csv)은 `_keep` 산출물 재계산과 같고, 지표 행은 표본 쌍에서 재계산과 같다.
  3. 조건 대조가 실제로 성립한다: 모든 쌍의 env 차이가 한 줄, 기준 캐시가 전수 평가와 같다.
  4. 특이점(멈춤·등급 A·기준 정책 고유 방향)이 표에서 계산한 값과 같다.
  5. 기반 데이터·지침·NOW가 이 보고서를 가리킨다.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_variable_influence as vi  # noqa: E402

SAMPLE = {"G-A031", "G-A016"}   # 걷는 기준 등급 A 하나 + 멈춤 쌍 하나 (seed 3개·1개 경로를 모두 지난다)


class VariableInfluenceContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pairs, cls.metrics = vi.build(metrics_for=SAMPLE)
        cls.f = vi.findings()

    def test_1_report_is_generated_from_evidence(self) -> None:
        self.assertEqual(vi.DOC.read_text(encoding="utf-8"), vi.render(),
                         "python tools/go2_variable_influence.py --report 로 재생성하라")

    def test_2_evidence_matches_the_raw_records(self) -> None:
        header, *rows = self.pairs
        published = [[r[h] for h in header] for r in vi.read("PAIRS.csv")]
        self.assertEqual(published, rows)
        header, *rows = self.metrics
        published = [[r[h] for h in header] for r in vi.read("PAIR_METRICS.csv") if r["work_id"] in SAMPLE]
        self.assertEqual(published, rows)
        self.assertTrue(rows)

    def test_3_conditions_were_actually_checked(self) -> None:
        for p in vi.read("PAIRS.csv"):
            with self.subTest(p["work_id"]):
                self.assertEqual(p["env_diff_lines"], "1", p["env_diff"])
                values = [float(v) for v in re.findall(r"weight: (-?[\d.]+)", p["env_diff"])]
                self.assertEqual(values, [float(p["from"]), float(p["to"])])
                self.assertEqual(p["cache_same"], p["cache_total"])
                self.assertTrue(p["ckpt_base"] and p["ckpt_cand"], "체크포인트를 산출물에서 찾지 못했다")
        by = {p["work_id"]: p for p in vi.read("PAIRS.csv")}
        self.assertEqual((by["G-A033"]["ckpt_base"], by["G-A033"]["ckpt_cand"]), ("900", "900"))
        self.assertEqual((by["G-A017"]["ckpt_base"], by["G-A017"]["ckpt_cand"]), ("999", "900"))
        self.assertEqual((by["G-A032"]["ckpt_base"], by["G-A032"]["ckpt_cand"]), ("900", "700"))
        self.assertEqual(by["G-A025"]["duplicate_of"], "G-A013")

    def test_4_grades_and_singularities(self) -> None:
        f = self.f
        # 2026-09-22: 회수된 한 항 변경 회차 세 개(A041·A042·A043)를 규칙대로 PAIRS 에 넣었다
        # (`workspace/training/quadruped/AGENTS.md` §4-9).  셋 다 조건이 같고 양쪽이 걸어 등급 A 다 —
        # 등급은 **비교 조건의 품질**이지 성능 판정이 아니다(A042 는 등급 A 이면서 INTERNAL_GATE_FAIL).
        self.assertEqual({k for k, v in f["class"].items() if v == "A"},
                         {"G-A031", "G-A033", "G-A038", "G-A041", "G-A042", "G-A043"})
        # G-A038 is a partial evaluation: walking was judged on flat forward, and the 10cm climb's fewer
        # terminations came with less progress (a stall), which the report must flag (2026-09-17).
        pairs = {p["work_id"]: p for p in vi.read("PAIRS.csv")}
        self.assertEqual(pairs["G-A038"]["walk_case"], "forward_nominal")
        self.assertEqual(pairs["G-A033"]["walk_case"], "rough_forward")
        doc = vi.DOC.read_text(encoding="utf-8")
        self.assertIn("종료 감소가 전진 감소와 함께 나온 case: stairs_10_down", doc)
        self.assertEqual({p["work_id"] for p in f["collapse"]}, {"G-A015", "G-A016", "G-A018"})
        self.assertEqual(f["revive"], [])
        # A043 이 `lin_vel_z_l2` 의 첫 등급 A 쌍을 만들었으므로 이 항은 더 이상 "깨끗한 쌍 없음" 이 아니다.
        self.assertEqual(set(f["no_walking_clean"]), {"flat_orientation_l2", "action_rate_l2"})
        quirks = {(q["baseline"], q["case"], q["metric"]) for q in f["baseline_quirks"]}
        self.assertIn(("Default-01", "push_pos_x", "terminated"), quirks)
        self.assertIn(("A017", "forward_nominal", "progress_m"), quirks)

    def test_5_agrees_with_the_base_data_tables(self) -> None:
        """같은 원시 기록을 두 도구가 읽는다 — 험지 옆걸음 종료 합이 같아야 한다."""
        import go2_tuning_base_data as base
        m = {(r["work_id"], r["case"], r["metric"]): r for r in vi.read("PAIR_METRICS.csv")}
        row = m[("G-A033", "rough_lateral", "terminated")]
        self.assertEqual(round(float(row["base"]) * 3), int(base.lateral(*base.LATERAL_OF["A017"])["terminated"]))
        self.assertEqual(round(float(row["cand"]) * 3), int(base.lateral(*base.LATERAL_OF["G-A033"])["terminated"]))

    def test_6_pointers(self) -> None:
        rel = vi.DOC_REL
        self.assertIn(rel, (ROOT / "GO2_NOW.md").read_text(encoding="utf-8"))
        self.assertIn("reports/GO2_VARIABLE_INFLUENCE.md",
                      (ROOT / "workspace/training/quadruped/AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("GO2_VARIABLE_INFLUENCE.md", (vi.QUAD / "reports/GO2_TUNING_BASE_DATA.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
