"""G-A036 재평가 패키지 계약.

이 회차의 위험은 둘이다.
  1. 학습 0이라고 적어놓고 학습이 섞이는 것.
  2. 검증된 러너를 베끼면서 조용히 다른 것까지 바꾸는 것.
둘 다 여기서 막는다. 특히 2번은 "선언한 치환 말고는 한 글자도 다르지 않다"로 검사한다.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_go2_reeval_package as build  # noqa: E402
from go2_run_ledger import _text  # noqa: E402


def members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()}


class ReevalPackageContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload, cls.entries = build.build_payload()
        cls.runner = cls.payload[build.RUNNER].decode("utf-8")
        cls.source = build.SOURCE_RUNNER.read_text(encoding="utf-8")

    def test_1_no_training_anywhere(self) -> None:
        """이 회차의 정의. 학습이 들어오면 견적도 근거도 전부 무효다."""
        self.assertNotIn("max_iterations", self.runner)
        invocations = [line for line in self.runner.splitlines()
                       if "train.py" in line and "pgrep" not in line]
        self.assertEqual(invocations, [], invocations)
        self.assertIn("TRAINING=none", self.runner)

    def test_2_core_differs_only_by_the_declared_substitutions(self) -> None:
        """검증된 러너 본문을 베끼되, 선언한 곳 말고는 바뀌지 않았음을 보인다."""
        original = self.source[self.source.index(build.CORE_START): self.source.index(build.CORE_END)]
        expected = original
        for old, new in build.SUBSTITUTIONS:
            self.assertIn(old, expected)
            expected = expected.replace(old, new)
        self.assertIn(expected, self.runner, "러너 본문이 선언한 치환 외에 달라졌다")
        self.assertNotEqual(expected, original)

    def test_3_proven_guards_survive(self) -> None:
        """베끼면서 잃으면 안 되는 것들 — 자세 게이트·case 지문·69 case 개수."""
        for marker in ('posture_ok "$out/summary.json"',
                       'case_identity.sha256',
                       'telemetry count is not 69',
                       '"${PY[@]}" "$POSTURE_CHECK"'):
            self.assertIn(marker, self.runner, marker)

    def test_4_every_shipped_checkpoint_matches_its_manifest_row(self) -> None:
        for i, entry in enumerate(self.entries):
            data = self.payload[f"arm{i}/policy/model.pt"]
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["model_sha256"], entry["run"])
            self.assertIn(f"arm{i}/policy/env.yaml", self.payload, entry["run"])

    def test_5_checkpoints_are_staged_outside_the_directory_stage_policy_wipes(self) -> None:
        """`stage_policy`는 arm 루트의 `exported/`를 지우고 시작한다.

        원본을 거기 두면 복사되기 전에 사라진다. 처음 판이 정확히 그랬다.
        """
        self.assertIn('rm -rf -- exported', self.runner)
        staged = [name for name in self.payload if re.match(r"arm\d+/exported/", name)]
        self.assertEqual(staged, [], staged)

    def test_6_already_measured_policies_are_not_re_measured(self) -> None:
        """Pilot-01·A017·G-A033 iter900은 이미 69 case v2로 쟀다. GPU를 다시 쓰지 않는다."""
        shipped = {entry["model_sha256"] for entry in self.entries}
        self.assertEqual(shipped & build.ALREADY_MEASURED, set())
        self.assertGreaterEqual(len(self.entries), 14)

    def test_7_terrain_is_paired_with_the_same_iteration_as_the_checkpoint(self) -> None:
        """이 회차 전체가 이 짝짓기 위에 서 있다. 핀과 terrain이 어긋나면 결과가 무의미하다."""
        checked = 0
        for entry in self.entries:
            if entry["terrain_at_pin"] is None:
                continue
            run_dir = ROOT / "workspace/_keep" / entry["run"]
            logs = sorted(run_dir.rglob("candidate_training.log"))
            if not logs:
                continue
            self.assertAlmostEqual(build.terrain_at(logs[0], entry["iteration"]),
                                   entry["terrain_at_pin"], places=6, msg=entry["run"])
            self.assertIn(f"model_{entry['iteration']}", entry["checkpoint"], entry["run"])
            checked += 1
        self.assertGreaterEqual(checked, 12)

    def test_7b_anchors_are_paired_with_the_iteration_that_was_scored(self) -> None:
        """이미 잰 정책의 기준점도 arm과 같은 규칙으로 짝짓는다. 999 값이 섞이면 거리가 틀린다."""
        found = build.anchors()
        self.assertGreaterEqual(len(found), 2, "A017·G-A033 둘은 학습 로그가 있다")
        for run, iteration, value in found:
            with self.subTest(run):
                log = sorted((ROOT / "workspace/_keep" / run).rglob("candidate_training.log"))[0]
                self.assertEqual(iteration, 900, "이미 잰 두 정책은 iter 900에서 평가됐다")
                self.assertEqual(build.terrain_at(log, iteration), value)
                self.assertNotEqual(build.terrain_at(log, 999), value,
                                    "999 값과 같으면 짝을 검사할 수 없다")

    def test_8_arm_order_puts_the_most_distant_point_first(self) -> None:
        """예산이 끊겨도 가장 쓸모 있는 점이 남아야 한다."""
        # 기준점을 테스트에 다시 손으로 적으면 빌더와 같은 오류를 같이 품는다 — 예전 판이
        # 그랬다(둘 다 @999 값을 "iter900"이라고 적었다).  빌더가 산출물에서 읽은 값을 쓰고,
        # 그 값이 정말 평가 iteration의 값인지는 test_7b 가 따로 검사한다.
        anchors = [value for _run, _iteration, value in build.anchors()]
        pinned = [e["terrain_at_pin"] for e in self.entries if e["terrain_at_pin"] is not None]
        self.assertEqual(pinned[0], 0.0, "가장 먼 점은 커리큘럼 미출발 회차다")

        # 고른 순서대로 '고를 당시의 최소거리'는 커질 수 없다. 같을 수는 있다 —
        # terrain 0.0000 회차가 둘이라 두 번째 0은 거리 0으로 맨 뒤에 온다.
        have, gaps = list(anchors), []
        for value in pinned:
            gaps.append(min(abs(value - h) for h in have))
            have.append(value)
        self.assertEqual(gaps, sorted(gaps, reverse=True), gaps)
        self.assertEqual(gaps[0], max(min(abs(v - h) for h in anchors) for v in pinned))

    def test_9_budget_gate_refuses_to_start_an_arm_it_cannot_finish(self) -> None:
        """반쯤 측정된 arm은 69 case가 아니라 70점 축에 못 올린다. 시작하지 않는 편이 낫다."""
        self.assertIn("GO2_REEVAL_BUDGET_MIN", self.runner)
        self.assertRegex(self.runner, r"elapsed_min \+ \d+ > BUDGET_MIN")
        self.assertIn("ARMS_SKIPPED", self.runner)

    def test_10_build_is_reproducible(self) -> None:
        again, entries = build.build_payload()
        self.assertEqual(again, self.payload)
        self.assertEqual(entries, self.entries)

    def test_11_one_file_one_command(self) -> None:
        readme = self.payload["README.txt"].decode("utf-8")
        self.assertIn(f"bash {build.RUNNER}", readme)
        self.assertEqual(len([n for n in self.payload if n.endswith(".sh")]), 1)
        self.assertIn("PACKAGE_SHA256SUMS.txt", self.payload)


if __name__ == "__main__":
    unittest.main()
