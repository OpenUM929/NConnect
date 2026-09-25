"""발행된 회차 산출물의 바이트가 바뀌지 않았는지 검사한다.

결함 X-1(2026-09-19).  `go2_feet_air_time_020_v2.zip` 의 바이트가 34298008 -> 34298254 로
바뀌어 있었다.  안에서 바뀐 것은 손상 구간에 붙인 경고 한 줄이었으니 의도는 옳았지만,
**바깥 `.sha256` 도 함께 갱신돼 파일과 기록이 일치했다** — 그래서 체크섬 검사가 이 변경을
잡지 못했다.  자기 자신을 가리키는 체크섬은 위변조 검사가 아니다.

그래서 기준을 파일 옆이 아니라 **HEAD** 에 둔다.  발행 ZIP 은 커밋된 바이트와 같아야 하고,
`.sha256` 기록도 그 파일과 맞아야 한다.  표시할 것이 생기면 산출물 밖에 둔다
(`go2_feet_air_time_020_v2.NOTICE.md` 가 그 예다).
"""
from __future__ import annotations

import hashlib
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"


def published() -> list[Path]:
    """`.sha256` 짝이 있는 ZIP 을 '발행된 것'으로 본다."""
    return sorted(p for p in QUAD.glob("*.zip") if p.with_suffix(".zip.sha256").is_file())


def head_blob(path: Path) -> bytes | None:
    rel = path.relative_to(ROOT).as_posix()
    got = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return got.stdout if got.returncode == 0 else None


class PublishedReleaseContractTest(unittest.TestCase):
    def test_1_there_is_something_to_check(self) -> None:
        self.assertTrue(published(), "발행 ZIP 을 하나도 못 찾았다 — 검사 범위가 비었다")

    def test_2_published_zips_match_their_committed_bytes(self) -> None:
        """기준은 파일 옆의 체크섬이 아니라 HEAD 다."""
        for zip_path in published():
            with self.subTest(zip_path.name):
                committed = head_blob(zip_path)
                if committed is None:
                    self.skipTest(f"{zip_path.name} 은 HEAD 에 없다 — 아직 발행 전이다")
                current = zip_path.read_bytes()
                self.assertEqual(
                    hashlib.sha256(current).hexdigest(), hashlib.sha256(committed).hexdigest(),
                    f"{zip_path.name} 의 바이트가 HEAD 와 다르다 "
                    f"({len(committed)} -> {len(current)}). 발행된 산출물은 고치지 않는다 — "
                    "표시할 것이 있으면 ZIP 밖에 둔다(예: *.NOTICE.md)")

    def test_3_the_checksum_record_matches_its_file(self) -> None:
        for zip_path in published():
            with self.subTest(zip_path.name):
                record = zip_path.with_suffix(".zip.sha256").read_text(encoding="utf-8").split()[0]
                self.assertEqual(hashlib.sha256(zip_path.read_bytes()).hexdigest(), record,
                                 f"{zip_path.name} 과 .sha256 기록이 어긋난다")

    def test_4_the_x1_notice_lives_outside_the_zip(self) -> None:
        """경고문이 다시 ZIP 안으로 들어가면 X-1 이 되풀이된다."""
        notice = QUAD / "go2_feet_air_time_020_v2.NOTICE.md"
        self.assertTrue(notice.is_file(), "ZIP 바깥 고지 파일이 없다")
        self.assertIn("CORRUPTED", notice.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
