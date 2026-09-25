"""Contract for the 2026-09-20 `ang_vel_xy_l2` relaxation audit (reports/GO2_ANG_VEL_RELAX_AUDIT_20260920.md).

왜 있는가.  이 감사는 PM 1안의 칸을 원자료와 대조해 두 개를 고쳤다(A016은 "보행 악화"가 아니라 보행 소실,
G5는 생존이 아니라 전진거리가 묶는다).  산문으로만 남기면 다음 감사자가 같은 것을 다시 찾는다
(메모리 규칙 "감사 결함은 파일로", "규칙은 기계 관문으로").  그래서 문서가 인용한 수치를 전부 원자료
셀에서 다시 읽어 대조하고, 감사가 만든 탐침 행이 실제로 생성기에서 나오는지 확인한다.

    python -m unittest tools.test_go2_ang_vel_relax_audit_contract
"""
from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
DOC = QUAD / "reports/GO2_ANG_VEL_RELAX_AUDIT_20260920.md"
SPEC = QUAD / "config/experiments/G_A041_a033_ang_vel_xy_m004.json"
MECH = QUAD / "reports/evidence/go2_reward_mechanism_20260917"
REREAD = QUAD / "reports/evidence/go2_a038_reread_20260919"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def one(path: Path, **selector: str) -> dict[str, str]:
    hits = [r for r in rows(path) if all(r[k] == v for k, v in selector.items())]
    if len(hits) != 1:
        raise AssertionError(f"{path.name} {selector} matched {len(hits)} rows")
    return hits[0]


class AngVelRelaxAuditContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")
        cls.spec = json.loads(SPEC.read_text(encoding="utf-8"))

    def test_1_the_probe_grid_carries_the_relaxation_points(self) -> None:
        """감사가 계산한 `-0.04`·`-0.03` 행이 생성기 산출물에 실제로 있다."""
        for value in ("-0.04", "-0.03"):
            probe = one(MECH / "PROBE_SITUATIONS.csv", term="ang_vel_xy_l2", to=value)
            for column in ("walk_delta", "climb_delta", "sway_delta", "push_delta"):
                self.assertTrue(probe[column].strip(), f"{value}: {column} 이 비어 있다")
        relax = one(MECH / "PROBE_SITUATIONS.csv", term="ang_vel_xy_l2", to="-0.04")
        self.assertEqual(relax["climb_delta"], "+0.0036")
        self.assertEqual(relax["sway_delta"], "-0.1077")
        self.assertEqual(relax["push_delta"], "-0.0512")
        self.assertEqual(relax["walk_delta"], "+0.0210")
        for cell in relax.values():
            self.assertIn(cell, self.text, f"문서가 {cell} 을 적지 않았다")

    def test_2_relaxing_cannot_lower_the_walk_margin(self) -> None:
        """벌점을 줄이면 걷기 margin 은 오른다 — 방향이 뒤집히면 문서의 '안전한 쪽'이 거짓이 된다."""
        probe = one(MECH / "PROBES.csv", term="ang_vel_xy_l2", to="-0.04")
        self.assertEqual(probe["zone"], "WALK")
        self.assertGreater(float(probe["margin"]), float(probe["margin_from"]))
        self.assertEqual(probe["range_status"], "OUT_OF_RANGE")
        self.assertIn(probe["margin"], self.text)

    def test_3_the_dial_history_is_one_sided(self) -> None:
        """걷는 회차는 전부 -0.05 이고, 이탈은 전부 강화 쪽이다 (문서 2절)."""
        ledger = rows(QUAD / "reports/runs/LEDGER.csv")
        walking = {r["ang_vel_xy_l2"] for r in ledger
                   if r["locomotion"] == "POLICY_LOCOMOTES" and r["ang_vel_xy_l2"]}
        self.assertEqual(walking, {"-0.05", "-0.08"}, "걷는 회차의 값 집합이 바뀌었다")
        relaxed = [r for r in ledger if r["ang_vel_xy_l2"] and float(r["ang_vel_xy_l2"]) > -0.05]
        self.assertEqual(relaxed, [], "완화 값을 돌린 회차가 생겼다 — 이 감사의 전제가 바뀐다")

    def test_4_a016_lost_locomotion_it_did_not_merely_degrade(self) -> None:
        """PM 표의 정정 1: -0.15 는 '보행 성능 악화'가 아니라 보행 소실이다."""
        a016 = one(QUAD / "reports/runs/LEDGER.csv",
                   run="go2_g_a016_pilot_ang_vel_xy_m015", arm="candidate")
        self.assertEqual(a016["ang_vel_xy_l2"], "-0.15")
        self.assertEqual(a016["locomotion"], "POLICY_DOES_NOT_LOCOMOTE")
        self.assertEqual(a016["terrain_999"], "0.0")
        self.assertIn("보행 소실", self.text)

    def test_5_g5_is_bound_by_distance_not_survival(self) -> None:
        """PM 표의 정정 2: G5 에서 생존으로 회수되는 몫은 1.43139 뿐이다."""
        bottleneck = (QUAD / "reports/GO2_AXIS_BOTTLENECK.md").read_text(encoding="utf-8")
        self.assertIn("1.43139", bottleneck)
        self.assertIn("10.71746", bottleneck)
        self.assertIn("1.43139", self.text)
        self.assertIn("10.71746", self.text)

    def test_6_the_measured_stair_movement_is_quoted_exactly(self) -> None:
        a033 = one(REREAD / "CLIMB_COUNT.csv", arm="A033", seed="SUM", case="stairs_10_down")
        a038 = one(REREAD / "CLIMB_COUNT.csv", arm="A038", seed="SUM", case="stairs_10_down")
        self.assertEqual((a033["ge1"], a033["ge2"]), ("90", "43"))
        self.assertEqual((a038["ge1"], a038["ge2"]), ("5", "0"))
        for value in ("90", "43", "5"):
            self.assertIn(value, self.text)

    def test_7_the_only_relaxation_in_the_ledger_is_stationary(self) -> None:
        """반대 행 1: A021 은 정지 기준선 위의 비대칭 계측이다."""
        a021 = one(QUAD / "reports/runs/LEDGER.csv",
                   run="go2_g_a021_chain01_ang_vel_xy_m005", arm="candidate")
        self.assertEqual(a021["locomotion"], "POLICY_DOES_NOT_LOCOMOTE")
        self.assertEqual(a021["instrument_symmetric"], "False")
        self.assertIn("A021", self.text)

    def test_8_the_isaaclab_anchor_is_the_same_in_all_three_configs(self) -> None:
        """반대 행 3: -0.04 는 외부 앵커가 없다."""
        extref = json.loads((QUAD / "config/go2_external_reference.json").read_text(encoding="utf-8"))
        rewards = extref["isaaclab"]["rewards"]
        values = {name: rewards[name]["ang_vel_xy_l2"] for name in ("base", "go2_rough", "go2_flat")}
        self.assertEqual(set(values.values()), {-0.05}, "IL 세 설정의 값이 갈라졌다")
        self.assertIn("세 설정", self.text)

    def test_9_the_spec_matches_the_audit(self) -> None:
        self.assertEqual(self.spec["single_change"], {
            "name": "ang_vel_xy_l2", "from": -0.05, "to": -0.04,
            "scope": "deployed_reward_weights_list",
            "applied_by": self.spec["single_change"]["applied_by"]})
        self.assertEqual(self.spec["change_class"], "reward_weight")
        self.assertEqual(self.spec["inference"]["status"], "INFORMATION_RUN")
        self.assertEqual(self.spec["open_decisions"], [])
        self.assertIn(SPEC.name, self.text)

    def test_10_the_inoperable_climb_group_is_left_out(self) -> None:
        """결함 S-2: 하한이 음수인 관문은 실을 수 없다."""
        guard = self.spec["preregistered"]["climb_guard"]["groups"]
        self.assertEqual(set(guard), {"stairs_10_climb_ge1", "stairs_10_climb_ge2"})
        for group in guard.values():
            self.assertGreater(float(group["baseline_sum"]) - float(group["max_drop"]), 0.0)
        self.assertIn("stairs_15_climb_ge1", self.text)

    def test_11_the_losing_channel_is_the_better_predicted_one(self) -> None:
        """§4-1: 흔들림 예측은 맞았고 계단 크기는 틀렸다 — 이 비대칭이 상태를 INFORMATION_RUN 으로 만든다."""
        forecast = (QUAD / "reports/GO2_REWARD_MECHANISM_FORECAST.md").read_text(encoding="utf-8")
        self.assertIn("`+0.3230` | `+0.356`", forecast)
        self.assertIn("+0.356", self.text)
        self.assertIn("13배", self.text)


if __name__ == "__main__":
    unittest.main()
