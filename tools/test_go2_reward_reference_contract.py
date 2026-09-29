"""보상 변수 참고본 계약 (2026-09-28 사용자 지시: 변수 검토 때 반드시 볼 수 있게, 변수별 값 → 결과 표).

- 참고본의 생성 표가 회수물 재계산과 같다(두 도구의 --check).
- 지침이 두 참고본을 필독으로 가리킨다.
- 강좌 참고본 §7이 생성 표를 출처로 인용하고 모든 변수 절을 가진다.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
TRIAL = QUAD / "reports/GO2_REWARD_TRIAL_REFERENCE.md"
LECTURE = QUAD / "reports/GO2_LECTURE_REWARD_REFERENCE.md"


def run(tool: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(ROOT / "tools" / tool), "--check"],
                          capture_output=True, text=True, timeout=900)


class ReferenceContract(unittest.TestCase):
    def test_generated_tables_match_harvests(self):
        for tool in ("go2_reward_trial_reference.py", "go2_reward_dial_series.py"):
            result = run(tool)
            self.assertEqual(result.returncode, 0, f"{tool}: {result.stdout}{result.stderr}")

    def test_guidelines_require_both_references(self):
        for agents in (ROOT / "AGENTS.md", QUAD / "AGENTS.md"):
            text = agents.read_text(encoding="utf-8")
            self.assertIn("GO2_REWARD_TRIAL_REFERENCE.md", text, agents)
            self.assertIn("GO2_LECTURE_REWARD_REFERENCE.md", text, agents)

    def test_lecture_reference_compares_every_variable(self):
        text = LECTURE.read_text(encoding="utf-8")
        self.assertIn("DIAL_SERIES_TABLES.md", text)
        for term in ("track_lin_vel_xy_exp", "feet_air_time", "lin_vel_z_l2", "ang_vel_xy_l2",
                     "action_rate_l2", "flat_orientation_l2"):
            self.assertRegex(text, rf"### 7-\d\. {term}", term)

    def test_trial_reference_points_to_series_tables(self):
        self.assertIn("DIAL_SERIES_TABLES.md", TRIAL.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
