"""규칙 문서 동기화 관문 — 반박·교체된 내용이 필독·규칙 문서에 남지 않게 한다.

2026-09-17 원인 조사(GO2_PROJECT_STATE.md G-D-FACT-RULES-20260917 ③):
  - `workspace/training/quadruped/AGENTS.md` §4-9가 기전 예측 §8의 레버를 옮겨 적은 사본이었고,
    G-A038이 그 레버를 반박한 뒤에도 사본이 남았다.
  - 기전 예측 생성기에 새 회차를 대조할 자리가 없었다.
  - `GO2_NOW.md`만 고치고 "NOW가 이긴다"에 기댔다.
  - 문구 관문이 옛 규칙 문구를 '있어야 하는 문구'로 고정했다.
이 테스트는 정책 내용의 사본, 반박된 레버·모델의 근거 인용, 옛 기준선 문구를 막는다.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
NOW = ROOT / "GO2_NOW.md"
RULE_DOCS = {
    "root AGENTS": ROOT / "AGENTS.md",
    "quad AGENTS": QUAD / "AGENTS.md",
    "NOW": NOW,
    "MASTER": ROOT / "GO2_REWARD_EVIDENCE_MASTER.md",
    **{p.stem: p for p in sorted((ROOT / ".codex/agents").glob("go2-*.md"))},
}
FORECAST = QUAD / "reports/GO2_REWARD_MECHANISM_FORECAST.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class PolicyTextContractTest(unittest.TestCase):
    def test_1_quad_agents_does_not_copy_the_policy(self) -> None:
        text = read(QUAD / "AGENTS.md")
        for phrase in ("구르기 속도 벌점 `ang_vel_xy_l2`를 걷기 구간 경계 안에서", "track `1.5` 유지.",
                       "G5: 관절 가속도 벌점 약화를 정보 측정으로"):
            self.assertNotIn(phrase, text, "튜닝 정책은 기전 예측 §8에서 읽는다 — 사본을 두지 않는다")
        self.assertIn("정책 내용을 이 파일에 옮겨 적지 않는다", text)

    def test_2_refuted_lever_is_not_a_first_choice_anywhere(self) -> None:
        pattern = re.compile(r"1순위[^\n]{0,20}`ang_vel_xy_l2`")
        for name, path in {**RULE_DOCS, "forecast": FORECAST}.items():
            with self.subTest(name):
                self.assertIsNone(pattern.search(read(path)), f"{name}: G-A038이 반박한 레버를 1순위로 적는다")
        forecast = read(FORECAST)
        self.assertIn("## 9. 사후 대조", forecast)
        self.assertIn("G-A038", forecast[forecast.index("## 9."):])

    def test_3_refuted_models_are_named_as_refuted(self) -> None:
        for name, path in {**RULE_DOCS, "forecast": FORECAST}.items():
            text = read(path)
            for line in text.splitlines():
                if "다이얼 모델" in line and "go2_dial_model" in line:
                    with self.subTest(name, line=line[:60]):
                        self.assertIn("반박", line, f"{name}: 다이얼 모델을 반박 표시 없이 인용한다")

    def test_4_no_stale_baseline_or_submission_text(self) -> None:
        stale = ("현재 기준선은 A017이다", "2026-09-14 기준 A017, G-D184)", "200자 제출문",
                 "A017 값 -0.05 |", "현재 A017)")
        for name, path in RULE_DOCS.items():
            text = read(path)
            for phrase in stale:
                with self.subTest(name, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_5_rule_docs_point_to_the_new_rules(self) -> None:
        quad = read(QUAD / "AGENTS.md")
        for needle in ("fact_rules_v1", "tools/go2_fact_rules.py", "사실 근거 추론 사슬",
                       "GO2_SEED_SENSITIVITY.md", "tools/go2_climb_count.py"):
            self.assertIn(needle, quad)
        now = read(NOW)
        for needle in ("fact_rules_v1", "GO2_SEED_SENSITIVITY.md", "G-D-FACT-RULES-20260917"):
            self.assertIn(needle, now)
        self.assertNotIn("이득 미추정", now, "NOW가 옛 권고 규칙(이득 추정)으로 판정을 적는다")

    def test_6_forecast_does_not_state_cudnn_noise_as_fact(self) -> None:
        text = read(FORECAST)
        line = next(line for line in text.splitlines() if "cudnn" in line)
        self.assertIn("같았다", line, "같은 seed 재학습 2쌍의 결정론을 함께 적어야 한다")

    def test_7_master_history_lists_every_executed_reward_run(self) -> None:
        master = read(ROOT / "GO2_REWARD_EVIDENCE_MASTER.md")
        history = master[master.index("## 1-a."):master.index("## 1-b.")]
        for work in ("G-A031", "G-A032", "G-A033", "G-A038", "G-A037", "G-A035"):
            self.assertIn(f"| {work} |", history)


if __name__ == "__main__":
    unittest.main()
