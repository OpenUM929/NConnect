"""회차 원장이 산출물과 어긋나지 않게 잡아두는 관문.

원장을 문서에 적는 것으로는 부족하다. 지난번에 그래서 `GO2_NOW.md`와
`GO2_PROJECT_STATE.md`가 서로 다른 회차 수를 주장한 채로 96개 테스트를 통과했다.
여기 적힌 것만이 검사된다.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from go2_run_ledger import harvest, occurred  # noqa: E402

FULL_SUITE = 69


class RunLedgerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = harvest()
        cls.by_run = {r["run"]: r for r in cls.records}

    def arm(self, run: str, arm: str) -> dict:
        return self.by_run[run]["arms"][arm]

    def test_0_runs_are_selected_by_artifact_not_by_name(self) -> None:
        """로봇을 디렉터리 이름으로 가리면 안 된다.

        `go2_` 접두사로 걸렀더니 Pilot-01의 원본 학습 `train_260831-Go2_5var_1000`이
        이름 때문에 통째로 빠졌고, 그 상태로 회차 수를 세어 문서에 적었다.
        """
        names = {r["run"] for r in self.records}
        self.assertIn("train_260831-Go2_5var_1000", names, "이름에 go2_가 없는 4족 회차가 빠졌다")
        self.assertFalse([n for n in names if "run05cfg" in n], "휴머노이드 회차가 섞였다")
        for record in self.records:
            self.assertTrue(record.get("robot_evidence"), record["run"])

    def test_1_chronology_is_monotonic(self) -> None:
        """회차는 산출물에 박힌 시각 순이다. 파일 mtime이 아니라 로그 내장값을 쓴다."""
        stamps = [occurred(r) for r in self.records if occurred(r)]
        self.assertEqual(stamps, sorted(stamps))
        self.assertGreaterEqual(len(stamps), 22, "시각을 못 읽은 회차가 늘었다")
        self.assertEqual(occurred(self.by_run["train_260831-Go2_5var_1000"]), "2026-08-31_15-42-43")

    def test_2_every_training_ran_exactly_1000_iterations(self) -> None:
        """'짧은 학습'이라는 전제가 실제로 전 회차에 걸려 있는지."""
        trained = [r for r in self.records if r.get("training")]
        self.assertGreaterEqual(len(trained), 17)
        for record in trained:
            training = record["training"]
            self.assertEqual(training["max_iterations"], 1000, record["run"])
            self.assertEqual(training["iterations_logged"], 1000, record["run"])

    def test_3_canonical_rescore_reproduces_the_stored_full_suite_reports(self) -> None:
        """재채점기가 당시 보고서와 같은 숫자를 낸다 — 이게 깨지면 아래 비교가 전부 무효다."""
        for arm in ("a017", "pilot"):
            body = self.arm("go2_a017_full_suite", arm)
            self.assertEqual(body["observed_cases"], FULL_SUITE)
            self.assertAlmostEqual(body["total_70"], body["as_recorded_70"], places=4, msg=arm)

    def test_4_a033_score_is_derivable_from_artifacts(self) -> None:
        """A033은 표준 보고서가 생성되지 않았다. 숫자가 산출물에서 나오는지 직접 확인한다."""
        body = self.arm("go2_g_a033_a017_track_lin_vel_xy_150", "candidate")
        self.assertEqual(body["observed_cases"], FULL_SUITE)
        self.assertAlmostEqual(body["total_70"], 42.52861, places=4)
        self.assertIsNone(body["as_recorded_70"], "보고서가 생겼다면 원장 서술을 고쳐야 한다")

    def test_5_repeated_trainings_are_detected(self) -> None:
        """같은 설정 재학습은 원장이 스스로 찾아내야 한다. 회차 수를 부풀리면 안 된다."""
        self.assertEqual(self.by_run["go2_g_a025_flat_orientation_m1"]["replicate_of"],
                         "go2_g_a013_flat_orientation_m1")
        self.assertEqual(self.by_run["go2_g_a010_lin_vel_z_m2_v2_260906"]["replicate_of"],
                         "go2_g_a010_lin_vel_z_m2")

    def test_6_replicates_are_bit_identical(self) -> None:
        """재학습 2쌍이 지표 한 줄도 다르지 않다 = 이 스택에서 학습 seed 흔들림 0."""
        for later, first in (("go2_g_a025_flat_orientation_m1", "go2_g_a013_flat_orientation_m1"),
                             ("go2_g_a010_lin_vel_z_m2_v2_260906", "go2_g_a010_lin_vel_z_m2")):
            a, b = self.by_run[later]["training"], self.by_run[first]["training"]
            self.assertEqual(a["metric_fingerprint"], b["metric_fingerprint"], later)
            self.assertGreater(a["metric_line_count"], 10000, later)

    def test_7_instrument_generations_are_separated(self) -> None:
        """같은 정책이 계측 세대에 따라 다른 점수를 낸다. 세대가 기록되지 않으면 비교가 새어나간다."""
        blind = self.arm("go2_default_vs_pilot_v1", "pilot")
        gated = self.arm("go2_a017_full_suite", "pilot")
        self.assertEqual(blind["instrument"], "no_fall_detection")
        self.assertEqual(gated["instrument"], "posture_gate_v2")
        self.assertGreater(blind["total_70"] - gated["total_70"], 5.0,
                           "같은 모델인데 세대차가 사라졌다면 재채점기가 바뀐 것이다")

    def test_8_partial_evaluations_are_never_read_as_full_suite(self) -> None:
        """7 case·10 case 회차의 70점은 전수 평가와 같은 축이 아니다."""
        for record in self.records:
            for name, body in record.get("arms", {}).items():
                if body["observed_cases"] in (None, FULL_SUITE):
                    continue
                self.assertLess(body["total_70"], 10.0,
                                f"{record['run']}/{name}: 부분 평가가 전수급 점수를 냈다")

    def test_9_baseline_candidates_share_one_instrument(self) -> None:
        """기준선 후보끼리는 같은 계측으로 재채점된 전수 평가여야 한다."""
        candidates = {
            "Pilot-01": self.arm("go2_a017_full_suite", "pilot"),
            "A017": self.arm("go2_a017_full_suite", "a017"),
            "G-A033": self.arm("go2_g_a033_a017_track_lin_vel_xy_150", "candidate"),
        }
        for name, body in candidates.items():
            self.assertEqual(body["observed_cases"], FULL_SUITE, name)
            self.assertEqual(body["instrument"], "posture_gate_v2", name)
            self.assertEqual(body["locomotion"], "POLICY_LOCOMOTES", name)
        ranked = sorted(candidates.items(), key=lambda kv: kv[1]["total_70"])
        self.assertEqual([n for n, _ in ranked], ["Pilot-01", "A017", "G-A033"])

    def test_10_asymmetric_instrument_pairs_stay_flagged(self) -> None:
        """두 arm을 다른 계측으로 잰 회차 7건. 이게 지워지면 무효 비교가 다시 새어 들어온다."""
        asymmetric = {r["run"] for r in self.records if r.get("instrument_symmetric") is False}
        self.assertEqual(len(asymmetric), 7, sorted(asymmetric))
        self.assertIn("go2_g_a024_ang_vel_xy_m015", asymmetric)
        for run in ("go2_g_a015_pilot_feet_air_time_035", "go2_g_a017_pilot_track_lin_vel_xy_140",
                    "go2_g_a033_a017_track_lin_vel_xy_150", "go2_a017_full_suite"):
            self.assertTrue(self.by_run[run]["instrument_symmetric"], run)

    def test_11_now_countable_claims_match_the_ledger(self) -> None:
        """`GO2_NOW.md`가 세는 숫자는 원장에서 나와야 한다.

        지난번에는 `GO2_NOW.md` 8건과 `GO2_PROJECT_STATE.md` 4건이 서로 다른 채로
        전체 테스트를 통과했다. 세는 값은 문서가 아니라 여기서 정한다.
        """
        now = (ROOT / "GO2_NOW.md").read_text(encoding="utf-8")
        trained = [r for r in self.records if r.get("training")]
        unique = [r for r in trained if not r.get("replicate_of")]

        for label, count in (("회차 디렉터리", len(self.records)),
                             ("학습 로그", len(trained)),
                             ("고유 학습", len(unique))):
            self.assertRegex(now, rf"{label}\*{{0,2}} \*{{0,2}}{count}\b",
                             f"GO2_NOW.md의 '{label}' 수가 산출물과 다르다 (실측 {count})")

        symmetric = sum(
            1 for r in self.records
            for body in r.get("arms", {}).values()
            if body["observed_cases"] == FULL_SUITE and body["instrument"] == "posture_gate_v2"
        ) - 1  # n개의 전수 v2 평가 사이에 만들 수 있는 연쇄 비교는 n-1건이다
        self.assertEqual(symmetric, 2)
        self.assertIn("VALID_SYMMETRIC_COMPARISONS: 2", now)

    def test_12_rewards_belong_to_the_arm_not_to_the_run(self) -> None:
        """회차 env.yaml 하나를 모든 arm에 붙이면 안 된다.

        2026-09-16까지 LEDGER의 Pilot arm이 Default 가중치(1.0·0.01·−3)로, 각 baseline
        arm이 후보 가중치로 적혀 있었다.
        """
        pilot = self.arm("go2_default_vs_pilot_v1", "pilot")["rewards"]
        self.assertEqual((pilot["track_lin_vel_xy_exp"], pilot["feet_air_time"], pilot["lin_vel_z_l2"]),
                         (1.2, 0.2, -2.0))
        default = self.arm("go2_default_vs_pilot_v1", "default")["rewards"]
        self.assertEqual(default["track_lin_vel_xy_exp"], 1.0)
        self.assertEqual(self.arm("go2_g_a033_a017_track_lin_vel_xy_150", "a017_sentinel")
                         ["rewards"]["track_lin_vel_xy_exp"], 1.4)
        self.assertEqual(self.arm("go2_g_a033_a017_track_lin_vel_xy_150", "candidate")
                         ["rewards"]["track_lin_vel_xy_exp"], 1.5)
        self.assertEqual(self.arm("go2_g_a017_pilot_track_lin_vel_xy_140", "baseline_tier1")["rewards"], {},
                         "근거 없는 arm에 가중치를 채웠다")

    def test_13_training_seed_noise_is_unmeasured(self) -> None:
        """모든 학습이 seed 42다. 같은 seed 재학습의 일치는 결정론이지 seed 흔들림 측정이 아니다.

        2026-09-16까지 `GO2_NOW.md`는 이것을 "학습 seed 흔들림은 0이다"로 적었고,
        그 문장이 G-A035 권고 근거("한 번에 답")로 쓰였다.
        """
        import re
        seeds = set()
        for record in self.records:
            log = record.get("training", {}).get("log")
            if log:
                found = re.findall(r"Environment seed\s*:\s*(\d+)", (ROOT / log).read_text(
                    encoding="utf-8", errors="replace"))
                seeds.update(found)
        self.assertEqual(seeds, {"42"}, "다른 학습 seed가 생겼다면 흔들림 서술을 실측으로 바꾼다")
        live = [ROOT / "GO2_NOW.md",
                ROOT / "workspace/training/quadruped/config/experiments/G_A035_a033_iter1500.json"]
        banned = ("학습 seed 흔들림은 0", "학습 흔들림이 0", "학습 흔들림 0이라",
                  "first measurement of training-seed noise", "cannot be lost in noise")
        for path in live:
            text = path.read_text(encoding="utf-8")
            for phrase in banned:
                self.assertNotIn(phrase, text, f"{path.name}: '{phrase}'")


if __name__ == "__main__":
    unittest.main()
