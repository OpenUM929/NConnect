"""영상 재사용 지문 관문 — 빌더의 재생 환경 표가 러너 `set_case` 와 같은가.

왜 있는가 (결함 C-13, 2026-09-22).  `build_go2_training_length_package.video_fingerprint` 는 저장된
기준선 영상이 **정말 그 조건의 그 정책인지**를 다시 계산해서 확인한다.  그 계산에 들어가는 값 중
`DR_MODE`·`PUSH_X`·`PUSH_Y` 세 칸이 `"0", "", ""` 로 박혀 있었다.  지금까지 재사용한 영상이 전부 밀침도
DR 도 아니어서 드러나지 않았지만, G-A044 가 A043 이 찍은 밀침 ±x 기준선 영상을 재사용하려 하자 지문이
맞지 않았다.  fail-closed 라 **잘못된 파일을 받아들인 적은 없고, 맞는 파일을 거부**하고 있었다.

이 관문은 표를 러너 원문(`set_case`)에서 다시 읽어 대조한다.  러너가 밀침 값을 바꾸거나 case 를
추가하면 여기서 걸린다 — 기억이 아니라 파일이 판정한다.

한계: 러너의 `set_case` 는 지형·명령 속도도 정하는데 그 값들은 지문에 들어가지 않는다.  이 관문은
지문에 실제로 들어가는 세 칸만 본다.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import build_go2_a033_reward_package as reward  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402

RUNNER = QUAD / "server_run_go2_candidate_iter_pinned.sh"
PUSH_LINE = re.compile(r"^\s*(push_[a-z_]+)\)\s*(PUSH_[XY])=(-?[0-9.]+)\s*;;", re.M)


def set_case_body() -> str:
    text = RUNNER.read_text(encoding="utf-8")
    start = text.index("set_case() {")
    return text[start:text.index("\n}\n", start)]


class VideoFingerprintContractTest(unittest.TestCase):
    def test_1_push_table_is_the_runner_s(self) -> None:
        body = set_case_body()
        found = {}
        for case_id, name, value in PUSH_LINE.findall(body):
            x = value if name == "PUSH_X" else ""
            y = value if name == "PUSH_Y" else ""
            found[case_id] = ("0", x, y)
        self.assertEqual(found, length.CASE_PLAY_ENV,
                         "러너 set_case 의 밀침 값과 빌더 표가 다르다")

    def test_2_dr_cases_carry_the_dr_flag(self) -> None:
        self.assertIn("dr_seed_*)", set_case_body())
        self.assertIn("DR_MODE=1", set_case_body())
        self.assertEqual(length.play_env("dr_seed_101"), ("1", "", ""))
        self.assertEqual(length.play_env("forward_nominal"), ("0", "", ""))

    def test_3_the_check_bites(self) -> None:
        """박힌 값으로 되돌리면 밀침 재사용이 실제로 거부된다 — 이 관문이 무용지물이 아니다."""
        spec = reward.load("G-A044")
        entry = "G6:push_pos_x:101"
        self.assertIn(entry, spec["videos"].get("baseline_reuse", {}), "밀침 재사용이 없는 사양이다")
        good = length.video_fingerprint(spec, entry)
        self.assertEqual(good, spec["videos"]["baseline_reuse"][entry]["identity_sha256"])
        saved = length.CASE_PLAY_ENV.copy()
        try:
            length.CASE_PLAY_ENV.clear()
            self.assertNotEqual(length.video_fingerprint(spec, entry), good)
            self.assertTrue(length.reuse_problems(spec), "표를 비웠는데도 재사용이 통과했다")
        finally:
            length.CASE_PLAY_ENV.update(saved)
        self.assertEqual(length.reuse_problems(spec), [])


if __name__ == "__main__":
    unittest.main()
