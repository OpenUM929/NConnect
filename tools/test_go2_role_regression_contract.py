"""역할 회귀 관문 — 보존한 실수를 관문이 지금도 잡는가.

사례표(`reports/GO2_ROLE_REGRESSION_CASES.md`, 증거 `CASES.csv`)의 기계 검사 사례마다 고장난 사양을
관문에 통과시켜 본다.  **실패해야 정상이다.**  통과해 버리면 그 관문은 썩은 것이고, 우리는 같은 실수를
다시 저지를 수 있는 상태다.

    python -B -m unittest tools.test_go2_role_regression_contract
"""
from __future__ import annotations

import csv
import re
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_role_regression as reg  # noqa: E402

EXPERIMENTS = reg.EXPERIMENTS


def cases() -> list[dict[str, str]]:
    with reg.OUT_CSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_gate(module_and_test: str, spec: dict) -> tuple[int, str]:
    """Run against a private snapshot; never stage fixtures in live experiments."""
    path, _, test = module_and_test.partition("::")
    module = "tools." + Path(path).stem
    with tempfile.TemporaryDirectory(prefix="go2-regression-") as directory:
        private = Path(directory)
        for source in EXPERIMENTS.glob("*.json"):
            shutil.copyfile(source, private / source.name)
        (private / "ZZ_REGRESSION_UNDER_TEST.json").write_text(
            json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        script = (
            "import importlib,sys,unittest; from pathlib import Path; "
            "m=importlib.import_module(sys.argv[1]); "
            "assert hasattr(m,'SPECS'); m.SPECS=Path(sys.argv[2]); "
            "r=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(m)); "
            "sys.exit(not r.wasSuccessful())"
        )
        proc = subprocess.run([sys.executable, "-B", "-c", script, module, str(private)],
                              cwd=ROOT, capture_output=True, text=True, errors="replace")
    return proc.returncode, proc.stdout + proc.stderr


class RoleRegressionTest(unittest.TestCase):
    def test_concurrent_probes_do_not_share_staging(self) -> None:
        from concurrent.futures import ThreadPoolExecutor
        good = reg.healthy_base()
        good["work_id"] = "G-A999"
        bad = {**good, "change_class": "training_length"}
        target = "tools/test_go2_detectability_gate.py"
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run_gate, target, good)
            second = pool.submit(run_gate, target, bad)
            good_code, good_output = first.result()
            bad_code, bad_output = second.result()
        self.assertEqual(good_code, 0, good_output)
        self.assertNotEqual(bad_code, 0)
        self.assertIn("FAIL: test_11_only_a_reward_weight_change_can_be_recommended", bad_output)
        self.assertFalse((EXPERIMENTS / "ZZ_REGRESSION_UNDER_TEST.json").exists())

    def test_1_cases_and_fixtures_are_regenerated(self) -> None:
        """2026-09-18 감사 D1/D2: 이 검사는 이름과 달리 fixture 는 `is_file()` 만 봤다.  그래서
        기준 사양(G-A039)을 고친 뒤 fixture 를 다시 만들지 않아도 통과했고, 고장난 사양 6개가
        **의도한 변형 말고도** 옛 사양의 결함(열 수 없는 경로 4곳, 옛 release_id)을 품게 됐다.
        시험지가 오염되면 "관문이 그 실수를 잡았다"는 증명 자체가 오염된다 — 바이트로 잠근다."""
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerows(reg.rows())
        self.assertEqual(reg.OUT_CSV.read_text(encoding="utf-8"), buffer.getvalue())
        self.assertEqual(reg.OUT_DOC.read_text(encoding="utf-8"), reg.document(reg.rows()))
        for case, _role, what, _why, _source, _verdict, _gate, mutate in reg.CASES:
            fixture = reg.FIXTURES / f"{case}.json"
            with self.subTest(case):
                self.assertTrue(fixture.is_file(), f"{case}: fixture 가 없다")
                expected = mutate(reg.healthy_base())
                expected["_regression_case"] = {
                    "case": case, "source_spec": reg.BASE_SPEC.name,
                    "broken_on_purpose": what,
                    "note": "이 파일은 시험지다. 회차 사양이 아니다 — config/experiments 에 두지 않는다.",
                }
                blob = (json.dumps(expected, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
                self.assertEqual(fixture.read_bytes(), blob,
                                 f"{case}: fixture 가 현행 사양에서 재생성된 것이 아니다 —"
                                 " python -B tools/go2_role_regression.py 를 다시 돌려라")

    def test_2_every_case_names_a_source_that_exists(self) -> None:
        for row in cases():
            with self.subTest(row["case"]):
                source = row["refuting_source"]
                path = ROOT / source if (ROOT / source).exists() else reg.QUAD / source
                self.assertTrue(path.exists(), f"{row['case']}: 반증 원본 {source} 이 없다")
                for field in ("what_happened", "why_wrong", "correct_verdict"):
                    self.assertTrue(row[field].strip(), f"{row['case']}: {field} 가 비었다")

    def test_3_each_preserved_mistake_still_fails_its_gate(self) -> None:
        """고장난 사양을 사양 폴더에 놓으면 관문이 실패해야 한다."""
        for row in cases():
            if row["machine_checkable"] != "YES" or row["gate"] == "-":
                continue
            with self.subTest(row["case"]):
                fixture = reg.OUT_DIR / row["fixture"]
                code, output = run_gate(row["gate"], json.loads(fixture.read_text(encoding="utf-8")))
                self.assertNotEqual(code, 0,
                                    f"{row['case']}: {row['gate']} 가 이 실수를 잡지 못했다 — 관문이 썩었다")
                test_name = row["gate"].partition("::")[2]
                if test_name:
                    # 2026-09-18 감사 D10: 모듈 전체를 돌리므로 '아무 검사나' 실패해도 code != 0 이다.
                    # 실패 목록을 뽑아 **지정한 그 검사**가 실제로 실패했는지 확인한다.
                    failed = set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", output, re.MULTILINE))
                    self.assertIn(test_name, failed,
                                  f"{row['case']}: 실패한 검사가 {test_name} 가 아니다 (실패: {sorted(failed)})")

    def test_4_the_healthy_spec_passes_the_same_gates(self) -> None:
        """대조군: 고장내지 않은 사양(G-A039)은 같은 관문을 통과한다."""
        # 2026-09-18: 여기서 상태만 RECOMMENDED 로 되돌리고 `contradicting` 은 살아 있는 사양에서
        # 그대로 가져왔더니, G-A039 강등 때 기록한 반대 행 3개가 딸려 와 대조군 자신이
        # test_3_contradicted_chains_are_not_recommended 에 걸렸다.  출발점은 생성기와 같은
        # `healthy_base()` 하나로 맞춘다.
        staged = reg.healthy_base()
        staged["work_id"] = "G-A999"          # 사양 폴더에 같은 work_id 가 둘이면 그 자체가 결함이다
        for gate in ("tools/test_go2_detectability_gate.py",):
            code, output = run_gate(gate, staged)
            self.assertEqual(code, 0, f"{gate} 가 정상 사양을 실패시켰다:\n{output[-2000:]}")

    def test_5b_every_named_gate_file_and_test_exists(self) -> None:
        """사례가 가리키는 관문 파일과 그 안의 검사 함수가 실제로 있어야 한다 —
        이름만 적어 두고 함수가 없으면 test_3 는 엉뚱한 실패를 통과로 읽는다."""
        import re
        for row in cases():
            if row["gate"] == "-":
                continue
            with self.subTest(row["case"]):
                module, _, test = row["gate"].partition("::")
                path = ROOT / module
                self.assertTrue(path.is_file(), f"{row['case']}: 관문 파일 {module} 이 없다")
                names = re.findall(r"def (test_\w+)", path.read_text(encoding="utf-8"))
                # 2026-09-18 감사 D10: startswith 였다 — 사례가 `::test_1` 이라 적으면
                # test_10·test_13·test_14 가 있어 통과해 버린다.  정확 일치로 잠근다.
                self.assertIn(test, names, f"{row['case']}: {module} 안에 {test} 가 없다")

    def test_5_the_case_file_only_grows(self) -> None:
        """사례는 지우지 않는다 — 생성기에 적힌 사례 수가 문서·CSV와 같아야 한다."""
        self.assertEqual(len(cases()), len(reg.CASES) + len(reg.MANUAL_CASES))
        self.assertGreaterEqual(len(reg.CASES) + len(reg.MANUAL_CASES), 10,
                                "2026-09-18 에 기록한 사례 10건보다 줄었다")


if __name__ == "__main__":
    unittest.main()
