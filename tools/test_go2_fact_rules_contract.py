"""fact_rules_v1 관문 — 분석이 정한 판정이 코드에서 실제로 FAIL을 내는지 G-A038 실제 수확물로 확인한다.

2026-09-17: G-A038은 10cm 오르기가 무너졌는데도 1단계 판정(9 case 평균)을 통과했다.  이 테스트는
  1  옛 규칙(G-A038 사양 그대로) → 서버 게이트 TARGET_PASS  (빈틈이 실제로 있었다는 기록)
  2  같은 수확물 + fact_rules_v1   → 서버 게이트 FAIL, 이유는 묶음 하한과 오른 로봇 수
  3  로컬 검증기의 전체 단계 판정은 목표 축(G3+G5)이 오르지 않으면 FAIL
  4  미실행 사양(G-A035·G-A037)의 한도는 G-A033 원시 기록에서 다시 계산한 값과 같다
  5  새 패키지는 규칙 모듈을 싣고, 실행된 패키지는 실행 당시 게이트 바이트 그대로다
  6  서버에 실리는 게이트 파일만으로(표준 라이브러리) 가져오기가 된다
를 확인한다.  수확물은 복사하지 않고 하드링크로 임시 폴더에 세운다(RUNNER_STATUS만 판정 가능 상태로 바꾼다).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import build_go2_basic_motion_pair as pair  # noqa: E402
import build_go2_campaign_package as campaign  # noqa: E402
import build_go2_training_length_campaign as length_campaign  # noqa: E402
import go2_climb_count as climb  # noqa: E402
import go2_fact_rules as fact  # noqa: E402
import go2_fact_rules_spec as fact_spec  # noqa: E402
import go2_target_gate as gate  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_fixed_eval_report import build_policy  # noqa: E402

KEEP = ROOT / "workspace/_keep"
A038 = KEEP / "go2_g_a038_a033_ang_vel_xy_m008"
A033_ARM = KEEP / "go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
SPEC_DIR = QUAD / "config/experiments"
REGISTRY = json.loads((QUAD / "config/go2_self_eval_registry.json").read_text(encoding="utf-8"))


def load(name: str) -> dict:
    return json.loads((SPEC_DIR / name).read_text(encoding="utf-8"))


def link_tree(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        target = dst / path.relative_to(src)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(path, target)
            except OSError:
                shutil.copy2(path, target)


@unittest.skipUnless(A038.is_dir() and A033_ARM.is_dir(), "_keep G-A038/G-A033 not present")
class FactRulesContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="go2_fact_rules_"))
        cls.spec_old = load("G_A038_a033_ang_vel_xy_m008.json")
        cls.spec_new = copy.deepcopy(cls.spec_old)
        cls.spec_new["preregistered"].update(fact_spec.rules_for(cls.spec_old))
        keep = cls.tmp / "keep"
        link_tree(A038 / "evaluation/candidate", keep / "evaluation/candidate")
        link_tree(A038 / "evaluation/g_a033_sentinel", keep / "evaluation/g_a033_sentinel")
        (keep / "training").mkdir(parents=True)
        os.link(A038 / "training/model_best.pt", keep / "training/model_best.pt")
        model_sha = hashlib.sha256((keep / "training/model_best.pt").read_bytes()).hexdigest()
        # 실제 RUNNER_STATUS에는 판정 필드가 없다(러너 결함).  측정은 모두 끝났으므로 판정 가능 상태로만 바꾼다.
        (keep / "RUNNER_STATUS.txt").write_text(
            "RUNNER_RC=0\nWORK_ID=G-A038\nDECISION=TARGET_STAGE_COMPLETE\nSTAGE=target\n"
            f"CANDIDATE_MODEL_SHA={model_sha}\n", encoding="utf-8")
        stored = cls.tmp / "stored"
        for name, data in length_campaign.stored_payload(cls.spec_old).items():
            path = stored / name.split("/", 1)[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        cls.keep, cls.stored = keep, stored

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_1_old_rule_passes_the_collapse(self) -> None:
        report = gate.gate(self.keep, self.stored, self.spec_old, REGISTRY)
        self.assertEqual(report["verdict"], "TARGET_PASS", report.get("faults"))
        self.assertEqual(report["baseline_arm"], "STORED_G-A033")
        self.assertTrue(report["sentinel"]["agrees"])
        self.assertAlmostEqual(report["target_stage"]["target_mean_proxy_delta"], 0.088377, places=5)
        self.assertEqual(report["target_stage"]["group_floor_violations"], [])

    def test_2_fact_rules_fail_it(self) -> None:
        report = gate.gate(self.keep, self.stored, self.spec_new, REGISTRY)
        self.assertEqual(report["verdict"], "FAIL")
        stage = report["target_stage"]
        self.assertEqual(len(stage["group_floor_violations"]), 1)
        self.assertTrue(stage["group_floor_violations"][0].startswith("stairs_10_climb "))
        guard = {row["group"]: row for row in stage["climb_guard"]["groups"]}
        self.assertEqual(guard["stairs_10_climb_ge1"]["counts"], [2, 1, 2])
        self.assertEqual(guard["stairs_10_climb_ge2"]["counts"], [0, 0, 0])
        self.assertFalse(guard["stairs_10_climb_ge1"]["ok"])
        self.assertFalse(guard["stairs_10_climb_ge2"]["ok"])
        # 15cm 오르기는 이 회차 1단계에 없었다 — 전체 단계로 미룬다.
        self.assertEqual(stage["climb_guard"]["deferred_to_full_stage"], ["stairs_15_climb_ge1"])

    def test_3_baseline_counts_are_the_analysis_counts(self) -> None:
        rows = {(r[0], r[1]): r for r in (line.split(",") for line in
                (QUAD / "reports/evidence/go2_stairs_behavior_20260916/STAIRS_CLIMB.csv")
                .read_text(encoding="utf-8").splitlines()[1:])}
        for name, group in self.spec_new["preregistered"]["climb_guard"]["groups"].items():
            column = {"ge1": 9, "ge2": 10}[group["metric"]]
            _, case_id, _ = group["entries"][0].split(":")
            expected = []
            for seed in ("101", "202", "303"):
                row = next(r for r in (line.split(",") for line in
                           (QUAD / "reports/evidence/go2_stairs_behavior_20260916/STAIRS_CLIMB.csv")
                           .read_text(encoding="utf-8").splitlines()[1:])
                           if r[0] == "go2_g_a033_a017_track_lin_vel_xy_150" and r[2] == case_id and r[3] == seed)
                expected.append(int(row[column]))
            self.assertEqual(group["baseline_counts"], expected, name)
        self.assertTrue(rows)
        # 기준선 자신은 관문을 통과한다 — **데이터 위반**이 없다는 뜻이다.
        same = fact.climb_reading(
            lambda e: A033_ARM / "cases" / f"seed_{e.split(':')[2]}" / e.split(":")[1], self.spec_new["preregistered"])
        data_violations = [v for v in same["violations"] if "guard inoperable" not in v]
        self.assertEqual(data_violations, [])
        # 2026-09-19 결함 S-2 래칫.  `baseline_sum - max_drop <= 0` 인 묶음은 **발화할 수 없다**
        # (오른 로봇 수는 음수가 못 되므로 어떤 결과도 하한을 넘는다).  예전에는 이것이 조용한
        # 통과였고 사양은 그 관문을 주된 반증 조건이라고 적었다.  이제 소리를 내며, 여기서
        # **늘어나지 않게 못 박는다** — 새 묶음이 발화 불가로 태어나면 이 검사가 깨진다.
        # 이 집합을 줄이는 길은 표본을 늘리거나(seed·환경 수) 검출 가능한 지표로 바꾸는 것이다.
        self.assertEqual(set(same["inoperable_guards"]), {"stairs_15_climb_ge1"},
                         "발화 불가 관문이 늘었다 — 관문이 약해진 것이지 결과가 좋아진 게 아니다")

    def test_4_full_stage_needs_the_target_axes_to_rise(self) -> None:
        identity = json.loads((A033_ARM / "identity.json").read_text(encoding="utf-8"))
        base = build_policy(A033_ARM, QUAD / "config/go2_self_eval_registry.json", identity)
        prereg = self.spec_new["preregistered"]
        climb_ok = {"violations": [], "groups": [], "deferred_to_full_stage": []}
        unchanged = verifier.judge(base, copy.deepcopy(base), prereg, climb_ok)
        self.assertEqual(unchanged["verdict"], "FAIL")
        self.assertIs(unchanged["criteria"]["6_target_axes_rise"], False)
        self.assertIn("climb_guard not read", verifier.judge(base, copy.deepcopy(base), prereg)["non_inferiority_violations"])
        raised = copy.deepcopy(base)
        raised["scenarios"]["G5"]["scenario_proxy"] += 0.01
        self.assertIs(verifier.judge(base, raised, prereg, climb_ok)["criteria"]["6_target_axes_rise"], True)
        broken = {"violations": ["stairs_10_climb_ge1 ge1 5 < floor 83.329 (baseline 90)"]}
        self.assertIn(broken["violations"][0], verifier.judge(base, raised, prereg, broken)["non_inferiority_violations"])
        # 옛 규칙 사양의 판정 항목은 그대로다.
        self.assertNotIn("6_target_axes_rise", verifier.judge(base, raised, self.spec_old["preregistered"])["criteria"])

    def test_5_unexecuted_specs_carry_the_measured_rules(self) -> None:
        for name in ("G_A035_a033_iter1500.json", "G_A037_a033_lin_vel_z_m1.json"):
            spec = load(name)
            with self.subTest(name):
                self.assertTrue(fact.active(spec["preregistered"]))
                expected = fact_spec.rules_for(spec)
                for key, value in expected.items():
                    self.assertEqual(spec["preregistered"][key], value, key)
                self.assertEqual(set(spec["preregistered"]["target_group_floor"]),
                                 set(spec["preregistered"]["target_groups"]))
        self.assertFalse(fact.active(self.spec_old["preregistered"]), "G-A038 ran under the old rule")

    def test_6_packages_ship_the_rule_modules(self) -> None:
        frozen = pair.EXECUTED_GATE.read_bytes()
        self.assertTrue(hashlib.sha256(frozen).hexdigest().startswith(pair.EXECUTED_GATE.name.split(".")[1]))
        self.assertNotEqual(frozen, (ROOT / "tools/go2_target_gate.py").read_bytes())
        executed = [campaign.output_path(campaign.CAMPAIGNS["G-A033"]),
                    length_campaign.output_path(length_campaign.CAMPAIGNS["G-A038"]),
                    pair.output_path() if hasattr(pair, "output_path") else None]
        for path in filter(None, executed):
            with self.subTest(path.name), zipfile.ZipFile(path) as archive:
                names = {n.split("/", 1)[1]: n for n in archive.namelist()}
                self.assertEqual(archive.read(names["go2_target_gate.py"]), frozen)
                self.assertNotIn("go2_fact_rules.py", names)
        for camp_id in ("G-A035", "G-A037"):
            payload = length_campaign.build_payload(camp_id)
            with self.subTest(camp_id):
                for name, path in {**pair.GATE_FILES, **pair.FACT_RULE_FILES}.items():
                    self.assertEqual(payload[name], path.read_bytes(), name)

    def test_7_server_gate_imports_from_its_own_folder(self) -> None:
        folder = self.tmp / "server"
        folder.mkdir()
        for name, data in pair.gate_payload(executed=False).items():
            (folder / name).write_bytes(data)
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        done = subprocess.run([sys.executable, "-S", "-B", "-c",
                               "import sys; sys.path.insert(0, '.'); import go2_target_gate, go2_fact_rules"],
                              cwd=folder, env=env, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_8_counter_is_shared_with_the_analysis_tool(self) -> None:
        import go2_stairs_behavior as sb
        self.assertIs(sb.gained_steps, climb.gained_steps)
        self.assertIs(sb.alive_rows, climb.alive_rows)
        self.assertEqual(sb.STAIR_CASES, climb.STAIR_HEIGHTS)


if __name__ == "__main__":
    unittest.main()
