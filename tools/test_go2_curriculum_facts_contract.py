"""지형 커리큘럼 사실표 관문 — 값이 Isaac Lab 원문에서 나왔고, 우리 학습이 같은 지형이었는가.

2026-09-18: 커리큘럼 계산(15 cm 계단이 몇 번째 행인가, 평균 레벨로 포화를 볼 수 있는가, IL 은 1500 iter)이
대화에만 있었다.  원문을 SHA256 과 함께 보관하고, 표를 원문에서 생성하고, 여기서 다시 검사한다.

    python -B -m unittest tools.test_go2_curriculum_facts_contract
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_curriculum_facts as facts  # noqa: E402

QUAD = ROOT / "workspace/training/quadruped"
SPECS = QUAD / "config/experiments"
SRC = facts.SRC


def table() -> dict[str, dict[str, str]]:
    with facts.OUT.open(encoding="utf-8", newline="") as handle:
        return {row["fact"]: row for row in csv.DictReader(handle)}


class CurriculumFactsTest(unittest.TestCase):
    def test_1_table_is_regenerated_from_the_sources(self) -> None:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerows(facts.rows())
        self.assertEqual(facts.OUT.read_text(encoding="utf-8"), buffer.getvalue(),
                         "CURRICULUM_FACTS.csv 가 원문 재파싱 결과와 다르다 — 손으로 고치지 말고 재생성한다")

    def test_2_every_source_file_matches_its_recorded_sha256(self) -> None:
        self.assertEqual(facts.sources_match(), [])
        with (SRC / "SOURCES.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 6)
        for row in rows:
            with self.subTest(row["file"]):
                self.assertTrue(row["url"].startswith(
                    "https://raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.1/source/"))
                self.assertEqual(hashlib.sha256((SRC / row["file"]).read_bytes()).hexdigest(), row["sha256"])
                self.assertTrue(row["why"].strip())

    def test_3_each_quoted_line_is_at_that_line_of_that_file(self) -> None:
        for fact, row in table().items():
            if row["line"] == "0":
                continue
            with self.subTest(fact):
                path = SRC / row["source"]
                self.assertTrue(path.is_file(), row["source"])
                line = path.read_text(encoding="utf-8").splitlines()[int(row["line"]) - 1].strip()
                self.assertEqual(line, row["quote"], f"{row['source']}:{row['line']} 가 인용과 다르다")

    def test_4_stair_rows_follow_the_difficulty_formula(self) -> None:
        rows = table()
        low, high = (float(v) for v in rows["stairs_step_height_range_m"]["value"].split("-"))
        count = int(rows["terrain_num_rows"]["value"])
        for index in range(count):
            lo, hi = (float(v) for v in rows[f"stairs_height_row_{index}_m"]["value"].split("-"))
            self.assertAlmostEqual(lo, low + (high - low) * index / count, places=6)
            self.assertAlmostEqual(hi, low + (high - low) * (index + 1) / count, places=6)
        for label, height in (("stairs_10", 0.10), ("stairs_15", 0.15)):
            with self.subTest(label):
                row_index = int(rows[f"{label}_curriculum_row"]["value"])
                lo, hi = (float(v) for v in rows[f"stairs_height_row_{row_index}_m"]["value"].split("-"))
                self.assertTrue(lo <= height < hi, f"{height} m 가 행 {row_index} 구간 밖이다")

    def test_5_our_training_terrain_equals_the_reference(self) -> None:
        rows = table()
        self.assertEqual(rows["our_env_num_rows"]["value"], rows["terrain_num_rows"]["value"])
        self.assertEqual(rows["our_env_num_cols"]["value"], rows["terrain_num_cols"]["value"])
        self.assertEqual(rows["our_env_step_height_range"]["value"], rows["stairs_step_height_range_m"]["value"])

    def test_6_the_mean_level_may_not_be_used_as_a_saturation_metric(self) -> None:
        """평균 레벨은 무작위 재배치로 상한이 걸린다 — 반증 조건으로 쓰면 안 된다."""
        rows = table()
        self.assertEqual(rows["mean_level_is_capped_by_random_resend"]["value"], "True")
        importer = (SRC / "isaaclab_terrains_terrain_importer.py").read_text(encoding="utf-8")
        self.assertIn("randint_like", importer)
        self.assertIn("return torch.mean", (SRC / rows["logged_level_is_a_mean"]["source"]).read_text(encoding="utf-8"))
        # 새 사양(관문 통과 대상)은 평균 지형 레벨을 반증 조건으로 쓰지 않는다
        for path in sorted(SPECS.glob("*.json")):
            text = path.read_text(encoding="utf-8")
            if '"status": "RECOMMENDED"' not in text:
                continue
            with self.subTest(path.name):
                falsified = re.search(r'"falsified_if":\s*"([^"]+)"', text)
                self.assertIsNotNone(falsified, path.name)
                self.assertNotIn("terrain level at", falsified.group(1),
                                 "추천 사양이 평균 지형 레벨을 반증 조건으로 쓴다")

    def test_7_the_training_length_gap_is_the_recorded_one(self) -> None:
        rows = table()
        self.assertGreater(int(rows["isaaclab_go2_rough_max_iterations"]["value"]),
                           int(rows["our_max_iterations"]["value"]))
        self.assertEqual(int(rows["our_max_iterations"]["value"]), facts.OUR_ITERATIONS)
        import json
        for path in sorted(SPECS.glob("G_A03*.json")):
            spec = json.loads(path.read_text(encoding="utf-8"))
            training = spec.get("training") or {}
            if spec.get("change_class") == "training_length":
                continue
            with self.subTest(path.name):
                self.assertEqual(training.get("max_iterations"), facts.OUR_ITERATIONS)


if __name__ == "__main__":
    unittest.main()
