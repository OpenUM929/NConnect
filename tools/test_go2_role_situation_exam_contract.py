"""상황 인지 시험 관문 — 정답이 원자료에 실제로 있는가.

시험지는 '내가 아는 것'이 아니라 '산출물에 적힌 것'으로 채점해야 한다.  그래서 문항마다 정답
출처 파일과 그 안에 **글자 그대로** 있어야 하는 문자열을 적어 두고, 이 관문이 파일을 열어 대조한다.
출처가 바뀌어 문자열이 사라지면 시험지가 먼저 깨진다 — 낡은 정답으로 역할을 채점하는 일을 막는다.

    python -B -m unittest tools.test_go2_role_situation_exam_contract
"""
from __future__ import annotations

import csv
import io
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_role_situation_exam as exam  # noqa: E402

QUAD = exam.QUAD


class SituationExamContractTest(unittest.TestCase):
    def test_1_csv_and_doc_are_regenerated(self) -> None:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerows(exam.rows())
        self.assertEqual(exam.OUT_CSV.read_text(encoding="utf-8"), buffer.getvalue(),
                         "EXAM.csv 가 현행 생성기 결과가 아니다 —"
                         " python -B tools/go2_role_situation_exam.py 를 다시 돌려라")
        self.assertEqual(exam.OUT_DOC.read_text(encoding="utf-8"), exam.document(exam.rows()))

    def test_2_every_answer_literal_is_in_its_source(self) -> None:
        """정답 문자열이 출처 파일 안에 글자 그대로 있어야 한다."""
        for item, _axis, _q, _a, _k, _t, source, literal, _w in exam.ITEMS:
            with self.subTest(item):
                path = ROOT / source if (ROOT / source).is_file() else QUAD / source
                self.assertTrue(path.is_file(), f"{item}: 출처 {source} 가 없다")
                self.assertIn(literal, path.read_text(encoding="utf-8"),
                              f"{item}: {source} 안에 '{literal}' 이 없다 — 정답이 낡았다")

    def test_3_the_answer_key_itself_passes_the_grader(self) -> None:
        """정답표를 답안으로 넣으면 12/12 여야 한다 — 채점 정규식이 정답을 못 맞히면 관문이 썩은 것이다."""
        key_text = "\n".join(f"{item[0]} {item[3]}" for item in exam.ITEMS)
        for row in exam.grade(key_text):
            with self.subTest(row["item"]):
                self.assertEqual(row["verdict"], "PASS",
                                 f"{row['item']}: 정답표가 자기 채점을 통과하지 못한다")

    def test_4_every_trap_actually_catches_the_stale_answer(self) -> None:
        """함정 정규식은 '낡은 문서를 옮겨 적은 답'을 실제로 잡아야 하고,
        그 낡은 답은 정답어를 담고 있지 않아야 한다 — 둘 다여야 `stale_copy` 가 켜진다."""
        stale = {
            "Q01": "Q01 기준선은 A017 이다",
            "Q02": "Q02 다음 회차로 G-A035 를 권한다",
            "Q03": "Q03 G5 는 추종이 막는다",
            "Q04": "Q04 멈춘 회차는 224000~404000 이다",
            "Q10": "Q10 G-A038 은 PASS 판정이다",
        }
        traps = {item[0]: item[5] for item in exam.ITEMS if item[5]}
        self.assertEqual(sorted(traps), sorted(stale),
                         "함정 문항이 늘거나 줄었는데 이 검사의 예시가 따라오지 않았다")
        keys = {item[0]: item[4] for item in exam.ITEMS}
        for item, text in stale.items():
            with self.subTest(item):
                self.assertTrue(re.search(traps[item], text),
                                f"{item}: 함정 정규식이 낡은 답 '{text}' 를 잡지 못한다")
                self.assertFalse(re.search(keys[item], text),
                                 f"{item}: 낡은 답 '{text}' 가 정답어까지 맞는다 — 문항이 변별력이 없다")
                graded = {row["item"]: row for row in exam.grade(text)}[item]
                self.assertEqual(graded["verdict"], "FAIL")
                self.assertEqual(graded["stale_copy"], "YES")

    def test_4b_an_answer_may_not_pass_on_another_items_sentence(self) -> None:
        """2026-09-18 1회차: Q12 의 정답어가 Q05 의 문장('관문 상수 DETECTION_LIMIT_70')에 걸려
        통과했다.  머리표로 자른 뒤에는 남의 문항 문장으로 통과할 수 없어야 한다."""
        borrowed = "Q05 관문 상수 DETECTION_LIMIT_70 는 2.53 이다\nQ12 change_class 는 env_reward_weight 다"
        graded = {row["item"]: row for row in exam.grade(borrowed)}
        self.assertEqual(graded["Q05"]["verdict"], "PASS")
        self.assertEqual(graded["Q12"]["verdict"], "FAIL",
                         "Q12 가 자기 답 밖의 문장으로 통과했다 — 채점 구간이 새고 있다")

    def test_5_the_exam_only_grows(self) -> None:
        self.assertGreaterEqual(len(exam.ITEMS), 12,
                                "2026-09-18 에 만든 12문항보다 줄었다 — 시험지는 지우지 않는다")
        self.assertEqual(len({item[0] for item in exam.ITEMS}), len(exam.ITEMS),
                         "문항 번호가 겹친다")

    def test_6_known_wrong_conclusions_do_not_pass_on_keywords(self) -> None:
        wrong = {
            "Q01": "Q01 G-A033 점수는 0점이다.",
            "Q03": "Q03 G5는 전진거리 부족이 아니다. 계단 앞에서 멈춘 것도 아니다.",
            "Q12": "Q12 env_reward_weight를 R6_CHANGE_CLASSES에 넣었다. 사용자 승인은 필요 없다.",
        }
        for item, answer in wrong.items():
            with self.subTest(item):
                graded = {row["item"]: row for row in exam.grade(answer)}[item]
                self.assertEqual(graded["verdict"], "FAIL", answer)

    def test_7_g5_answer_uses_current_axis_bottleneck(self) -> None:
        item = next(entry for entry in exam.ITEMS if entry[0] == "Q03")
        self.assertIn("전진거리", item[3])
        self.assertIn("GO2_NOW.md", item[6])


if __name__ == "__main__":
    unittest.main()
