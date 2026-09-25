"""Contract for the 2026-09-20 plan assessment (upload/plan/GO2_PLAN_ASSESSMENT_20260920.md).

왜 있는가.  이 문서는 **판단**이지 측정이 아니다.  판단 문서일수록 근거 수치가 조용히 낡는다 —
축 점수가 바뀌거나 회차가 하나 더 쌓이면 "18회 중 2건", "검출 한계의 1.09배" 같은 문장이 사실이
아니게 되는데, 산문은 그것을 스스로 알리지 못한다(메모리 규칙 "규칙은 기계 관문으로").

그래서 여기서는 문서의 주장을 **원자료 셀에서 다시 계산해** 대조한다.  수치가 움직이면 이 관문이
먼저 실패하고, 그때 문서를 고치거나 판단을 바꾸라고 말한다.

    python -m unittest tools.test_go2_plan_assessment_contract
"""
from __future__ import annotations

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
DOC = QUAD / "upload/plan/GO2_PLAN_ASSESSMENT_20260920.md"
RUNS = QUAD / "reports/runs"
AXIS_CSV = QUAD / "reports/evidence/go2_axis_bottleneck_20260919/AXIS_BOTTLENECK.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def margin() -> dict[tuple[str, str], str]:
    return {(r["metric"], r["scenario"]): r["value"] for r in rows(RUNS / "BASELINE_MARGIN.csv")}


def number(value: str) -> float:
    return float(value.replace("+", ""))


class PlanAssessmentContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")
        cls.margin = margin()

    def test_1_the_recoverable_gap_still_favours_g3(self) -> None:
        """§2 의 판단 전체가 이 부등식 하나에 걸려 있다."""
        bottleneck = (QUAD / "reports/GO2_AXIS_BOTTLENECK.md").read_text(encoding="utf-8")
        g3 = re.search(r"\| G3 \|.*?\| \*\*([\d.]+)\*\* \| 14\.0 \| `survival` \| ([\d.]+) \|", bottleneck)
        g5 = re.search(r"\| G5 \|.*?\| \*\*([\d.]+)\*\* \| 10\.5 \| `survival` \| ([\d.]+) \|", bottleneck)
        self.assertIsNotNone(g3, "G3 행 형식이 바뀌었다")
        self.assertIsNotNone(g5, "G5 행 형식이 바뀌었다")
        g3_score, g3_counter = float(g3.group(1)), float(g3.group(2))
        g5_score, g5_counter = float(g5.group(1)), float(g5.group(2))
        self.assertGreater(g3_counter - g3_score, g5_counter - g5_score,
                           "G3 의 회수 상한이 더 이상 크지 않다 — 이 문서의 P1 권고를 다시 판단하라")
        for value in (f"{g3_score:.5f}", f"{g3_counter:.5f}", f"{g5_score:.5f}", f"{g5_counter:.5f}"):
            self.assertIn(value, self.text, f"문서가 {value} 를 적지 않았다")

    def test_2_g5_is_bound_by_distance_not_posture(self) -> None:
        """§2: 12개 (case, seed) 전부 completion < tracking_xy 이고 9개는 묶는 인수가 completion 이다."""
        cases = [r for r in rows(AXIS_CSV) if r["axis"] == "G5" and r["case"]]
        numeric = [r for r in cases if r["completion"] and r["tracking_xy"]
                   and re.fullmatch(r"[\d.eE+-]+", r["completion"])]
        self.assertEqual(len(numeric), 12, "G5 case×seed 수가 12가 아니다")
        worse = [r for r in numeric if float(r["completion"]) < float(r["tracking_xy"])]
        self.assertEqual(len(worse), 12, "completion 이 tracking 보다 큰 case 가 생겼다")
        by_completion = [r for r in numeric if r["binding_factor"] == "completion"]
        self.assertEqual(len(by_completion), 9)
        worst = min(numeric, key=lambda r: float(r["progress_m"]))
        self.assertEqual(worst["case"], "stairs_15_down")
        self.assertIn(worst["progress_m"], self.text, "가장 나쁜 전진거리 셀이 문서에 없다")
        self.assertEqual(worst["expected_m"], "10.0")

    def test_3_only_two_comparisons_are_readable_on_the_70_point_axis(self) -> None:
        """§3 의 '18 대 2'. 비교 가능 행이 늘면 이 문서의 진단이 약해진다 — 그때 다시 판단한다."""
        index = (RUNS / "INDEX.md").read_text(encoding="utf-8")
        table = [line for line in index.splitlines() if re.match(r"\| \d\d \|", line)]
        trainings = [line for line in table if "1000 iter" in line]
        self.assertEqual(len(table), 26, "회차 디렉터리 수가 바뀌었다")
        self.assertEqual(len(trainings), 18, "학습 회차 수가 바뀌었다")
        pairs = [r for r in rows(RUNS / "ARM_DELTAS.csv")
                 if r["cases"] == "69" and r["instrument_from"] == r["instrument_to"] == "posture_gate_v2"]
        self.assertEqual(len(pairs), 2, "ARM_DELTAS 의 대칭 69case 행 수가 바뀌었다")   # 양방향 1쌍
        self.assertEqual({p["delta_70"] for p in pairs}, {"+6.09363", "-6.09363"})
        self.assertIn("+6.09363", self.text)
        self.assertIn(self.margin[("delta_total_observed", "ALL")], self.text)

    def test_4_the_baseline_margin_is_as_thin_as_the_document_says(self) -> None:
        """§3 의 1.09배. 문서가 인용한 유일한 손계산이라 여기서 다시 나눈다."""
        observed = number(self.margin[("delta_total_observed", "ALL")])
        limit = number(self.margin[("detect_limit_2sigma", "ALL")])
        self.assertAlmostEqual(round(observed / limit, 2), 1.09, places=2)
        self.assertIn("1.09", self.text)
        lo, hi = self.margin[("delta_total_ci95_lo", "ALL")], self.margin[("delta_total_ci95_hi", "ALL")]
        self.assertIn(lo, self.text)
        self.assertIn(hi, self.text)
        self.assertGreater(number(lo), 0.0, "하한이 0 아래로 내려갔다 — 승급 서술을 다시 판단하라")
        g4 = number(self.margin[("delta_observed", "G4")]) / number(self.margin[("delta_resample_sd", "G4")])
        self.assertAlmostEqual(round(g4, 1), 7.3, places=1)
        self.assertIn("7.3", self.text)

    def test_5_the_seed_ruler_still_does_not_exist(self) -> None:
        """§3 P3 권고의 전제: 전 학습이 seed 42이고 흔들림 측정이 0건이다."""
        ledger_contract = (ROOT / "tools/test_go2_run_ledger_contract.py").read_text(encoding="utf-8")
        self.assertIn("test_13_training_seed_noise_is_unmeasured", ledger_contract,
                      "seed 관문이 사라졌다 — 이 문서의 P3 전제를 다시 확인하라")
        self.assertIn('self.assertEqual(seeds, {"42"}', ledger_contract,
                      "다른 학습 seed 가 생겼다면 눈금이 이미 있는 것이다 — P3 를 다시 판단하라")
        # 눈금이 없다는 서술은 문서에도 그대로 있어야 한다
        self.assertIn("seed 복제", self.text)
        self.assertIn("0건", self.text)

    def test_6_the_curriculum_confound_is_quoted_from_the_ledger(self) -> None:
        pin = {(r["run"], r["iteration"]): r["terrain"] for r in rows(RUNS / "TERRAIN_AT_PIN.csv")}
        a033 = pin[("go2_g_a033_a017_track_lin_vel_xy_150", "900")]
        a038 = pin[("go2_g_a038_a033_ang_vel_xy_m008", "900")]
        self.assertIn(a033, self.text)
        self.assertIn(a038, self.text)
        self.assertNotEqual(a033, a038)

    def test_7_the_submission_budget_numbers_are_the_external_ones(self) -> None:
        extref = json.loads((QUAD / "config/go2_external_reference.json").read_text(encoding="utf-8"))
        runner = extref["isaaclab"]["runner"]
        self.assertEqual(runner["go2_rough_max_iterations"], 1500)
        self.assertEqual(runner["go2_flat_max_iterations"], 300)
        self.assertIn("1500", self.text)
        self.assertIn("300", self.text)
        deployed = (QUAD / "quadruped_rewards.py").read_text(encoding="utf-8")
        self.assertIn("5000~15000 iter", deployed, "배포 안내의 제출본 길이 문구가 바뀌었다")
        self.assertIn("5000~15000 iter", self.text)

    def test_8_the_lever_space_table_matches_the_master(self) -> None:
        master = (ROOT / "GO2_REWARD_EVIDENCE_MASTER.md").read_text(encoding="utf-8")
        for dial in ("track_lin_vel_xy_exp", "feet_air_time", "lin_vel_z_l2",
                     "ang_vel_xy_l2", "action_rate_l2", "flat_orientation_l2"):
            with self.subTest(dial):
                self.assertIn(dial, self.text)
                self.assertIn(dial, master)
        self.assertIn("미탐색", master)

    def test_9_the_judgement_is_marked_as_judgement(self) -> None:
        """판단 문서가 측정처럼 읽히지 않게 한다 — 확신도 표기와 반증 조건이 있어야 한다."""
        for mark in ("[확인]", "[추정]", "[모름]"):
            self.assertIn(mark, self.text, f"{mark} 표기가 없다")
        self.assertIn("반증 조건", self.text)
        self.assertIn("판단 문서", self.text)
        self.assertGreaterEqual(self.text.count("[추정]"), 5, "추측이 표시 없이 섞였을 수 있다")

    def test_17_the_handoff_tells_a_reviewer_how_to_check(self) -> None:
        """§9: 검토자는 문서를 믿지 않고 돌려 볼 수 있어야 한다 — 명령·선행 실패·한계가 있어야 한다."""
        self.assertIn("외부 검토자에게", self.text)
        for command in ("tools.test_go2_plan_assessment_contract",
                        "tools.test_go2_ang_vel_relax_audit_contract",
                        "tools/go2_claim_check.py"):
            self.assertIn(command, self.text, f"§9 에 {command} 가 없다")
        # 선행 실패(C-2)를 이 작업의 실패로 오독하지 않게 하는 안내
        self.assertIn("C-2", self.text)
        self.assertIn("diverged G-A035,G-A037,G-A039", self.text)
        self.assertIn("G-A038", self.text, "대조군을 적지 않았다")
        # 판단과 측정의 경계, 그리고 내가 틀린 자리
        self.assertIn("판단 문서다", self.text)
        self.assertIn("세 번 틀렸", self.text)

    def test_18_the_handoff_repro_still_reproduces(self) -> None:
        """§9-3 이 인용한 기대 출력이 결함 대장의 것과 같아야 한다 (문서가 대장을 앞지르지 않게)."""
        defects = QUAD / "reports/evidence/go2_defect_ledger/DEFECTS.csv"
        row = next(r for r in rows(defects) if r["id"] == "C-2")
        self.assertIn(row["repro_expect"], self.text,
                      "§9-3 의 기대 출력이 결함 대장과 다르다")
        self.assertEqual(row["status"], "OPEN", "C-2 가 닫혔다 — §9-3 을 다시 쓰라")

    def test_14_every_schedule_quote_is_verbatim(self) -> None:
        """부록이 계획서에서 따온 문장은 계획서에 **글자 그대로** 있어야 한다.

        §2·§4·§4-1 의 판단이 전부 이 인용 네 개에 걸려 있다.  계획서가 갱신되면(P0) 여기가 먼저 운다.
        """
        schedule = (ROOT / "GO2_CAMPAIGN_SCHEDULE.md").read_text(encoding="utf-8")
        quotes = ("기본값 기반 최대 감점 시나리오 단일변수 1k~5k",
                  "동일 evaluator에서 목표 G 개선 + 타 G 비열등",
                  "현재 — G-A010 package 검증 완료·서버 실행 대기",
                  "screening 승자 5k→10k→15k",
                  "다중 seed 최종 평가·제출 bundle·200자 리포트")
        for quote in quotes:
            with self.subTest(quote=quote[:24]):
                self.assertIn(quote, schedule, "계획서에 이 문장이 없다 — 인용을 다시 확인하라")
                self.assertIn(quote, self.text, "문서가 이 인용을 부록에 적지 않았다")

    def test_15_the_hand_computed_numbers_are_declared_and_correct(self) -> None:
        """손으로 친 숫자는 개수를 선언하고, 전부 인용 칸의 사칙연산이어야 한다."""
        self.assertIn("손으로 계산한 값은 **여덟**", self.text)
        observed = number(self.margin[("delta_total_observed", "ALL")])
        limit = number(self.margin[("detect_limit_2sigma", "ALL")])
        g4 = number(self.margin[("delta_observed", "G4")]) / number(self.margin[("delta_resample_sd", "G4")])
        index = (RUNS / "INDEX.md").read_text(encoding="utf-8")
        trainings = [line for line in index.splitlines()
                     if re.match(r"\| \d\d \|", line) and "1000 iter" in line]
        checks = {
            f"{observed / limit:.2f}": "1.09",
            f"{g4:.1f}": "7.3",
            str(5000 + 10000 + 15000): "30000",
            str(len(trainings) * 1000): "18000",
            str((5000 + 10000 + 15000) // 1000): "30",
            f"{self.counter('G3')[1] / self.counter('G5')[1]:.5f}": "7.48745",
            f"{(self.counter('G3')[1] - self.counter('G3')[0]) / (self.counter('G5')[1] - self.counter('G5')[0]):.5f}": "4.68046",
            f"{self.counter('G5')[1] - self.counter('G5')[0]:.5f}": "1.38666",
        }
        for computed, written in checks.items():
            with self.subTest(written):
                self.assertEqual(computed, written, "문서의 손계산이 원자료와 맞지 않는다")
                self.assertIn(written, self.text)

    def test_16_the_side_fix_is_recorded(self) -> None:
        """평가 중에 고친 것(P-1 재현식)이 문서에 남아 있어야 한다 — 조용한 수정 금지."""
        self.assertIn("부록 2", self.text)
        self.assertIn("P-1", self.text)
        ledger = (ROOT / "tools/go2_defect_ledger.py").read_text(encoding="utf-8")
        self.assertIn("cases_0919 0 cases_rows 14", ledger, "P-1 의 재현 기대값이 바뀌었다")
        self.assertIn('id="P-1"', ledger)

    def test_11_the_schedule_and_the_current_plan_still_disagree(self) -> None:
        """§4-1: 단계표가 낡았다는 지적은 표가 갱신되면 사라져야 한다 — 그때 이 관문이 먼저 운다."""
        schedule = (ROOT / "GO2_CAMPAIGN_SCHEDULE.md").read_text(encoding="utf-8")
        self.assertIn("G-A010 package 검증 완료·서버 실행 대기", schedule,
                      "단계표가 갱신됐다 — 이 문서 §4-1 의 '표가 낡았다'를 다시 판단하라")
        self.assertIn("다중 seed 최종 평가", schedule, "단계 5 의 제출요건 문구가 바뀌었다")
        self.assertIn("5k→10k→15k", schedule, "단계 4 의 학습량 문구가 바뀌었다")
        for phrase in ("닫힌 문서를 현재 단계표로 읽었다", "미이행 절차",
                       "중단 규칙은 있고 문턱이 없다", "승급 경로가 표와 다르다"):
            self.assertIn(phrase, self.text, f"§4-1 에 '{phrase}' 가 없다")

    def test_12_stage_four_outweighs_every_training_so_far(self) -> None:
        """§4-1 의 산술: 5000+10000+15000 = 30000 > 학습 18회 x 1000."""
        index = (RUNS / "INDEX.md").read_text(encoding="utf-8")
        trainings = [line for line in index.splitlines()
                     if re.match(r"\| \d\d \|", line) and "1000 iter" in line]
        stage_four = 5000 + 10000 + 15000
        self.assertEqual(stage_four, 30000)
        self.assertGreater(stage_four, len(trainings) * 1000,
                           "학습 총량이 단계 4 를 넘어섰다 — §4-1 의 비교를 다시 쓰라")
        self.assertIn("30000", self.text)
        self.assertIn(str(len(trainings) * 1000), self.text)

    def test_13_the_document_keeps_the_criticism_it_withdrew(self) -> None:
        """틀린 지적을 조용히 지우지 않는다 — 철회 사실과 이유가 문서에 남아야 한다."""
        self.assertIn("틀린 지적이었다", self.text)
        self.assertIn("GO2_CAMPAIGN_SCHEDULE.md", self.text)
        self.assertIn("P0", self.text, "철회 뒤 나온 권고가 표에 없다")

    def test_10_a_run_costing_recommendation_names_its_approval(self) -> None:
        """회차를 쓰는 권고는 R-6 밖인지·승인이 필요한지 문서가 말해야 한다."""
        self.assertIn("R-6 밖", self.text)
        self.assertIn("사용자 승인이 필요", self.text)
        self.assertIn("서버 실행", self.text)

    # ── 2026-09-21 PM 재검토를 본문에 반영하면서 늘린 관문 ────────────────────────────

    @classmethod
    def counter(cls, axis: str) -> tuple[float, float]:
        """`GO2_AXIS_BOTTLENECK.md` 의 (축 점수, 생존 1.0 반사실) 두 칸."""
        bottleneck = (QUAD / "reports/GO2_AXIS_BOTTLENECK.md").read_text(encoding="utf-8")
        cap = {"G3": "14.0", "G5": "10.5"}[axis]
        hit = re.search(rf"\| {axis} \|.*?\| \*\*([\d.]+)\*\* \| {cap} \| `survival` \| ([\d.]+) \|",
                        bottleneck)
        if hit is None:
            raise AssertionError(f"{axis} 행 형식이 바뀌었다")
        return float(hit.group(1)), float(hit.group(2))

    def test_19_the_two_ratios_are_separated(self) -> None:
        """PM 반박 1.  도달점 비율과 회수량 비율은 다른 수다 — 초판은 앞의 것을 뒤의 뜻으로 썼다."""
        g3_score, g3_counter = self.counter("G3")
        g5_score, g5_counter = self.counter("G5")
        reach = g3_counter / g5_counter
        gain = (g3_counter - g3_score) / (g5_counter - g5_score)
        self.assertIn(f"{reach:.5f}", self.text, "도달점 비율이 문서에 없다")
        self.assertIn(f"{gain:.5f}", self.text, "회수량 비율이 문서에 없다")
        self.assertNotAlmostEqual(reach, gain, places=2, msg="두 비율이 같아졌다 — §2 의 구분을 다시 쓰라")
        self.assertIn("도달점", self.text)
        self.assertIn("회수량", self.text)
        # 규칙 갱신 제안이 쓰는 값은 회수량 쪽이어야 한다
        self.assertIn(f"**뒤쪽(`{gain:.5f}`배)**", self.text)
        self.assertGreater(gain, 1.0, "회수량 비율이 1 아래다 — P1 권고를 다시 판단하라")

    def test_20_the_new_schedule_quotes_are_verbatim(self) -> None:
        """PM 반박 2·3.  P3 의 근거와 중단 규칙은 계획서의 **다른** 문장에서 온다."""
        schedule = (ROOT / "GO2_CAMPAIGN_SCHEDULE.md").read_text(encoding="utf-8")
        quotes = ("승급 시에도 즉시 장기 학습하지 않고 독립 학습 seed를 먼저 수행한다",
                  "폐기 / 3k~5k 확장 / 독립 학습 seed 재검증 결정",
                  "다음 iter 승급 또는 직전 verified checkpoint 동결")
        for quote in quotes:
            with self.subTest(quote=quote[:24]):
                self.assertIn(quote, schedule, "계획서에 이 문장이 없다 — §3·§4-1 의 근거를 다시 확인하라")
                self.assertIn(quote, self.text, "문서가 이 인용을 적지 않았다")
        # 평가 seed 는 이미 여럿이다 — 없는 것은 학습 seed 다
        seeds = {r["seed"] for r in rows(AXIS_CSV) if r["seed"].isdigit()}
        self.assertEqual(seeds, {"101", "202", "303"}, "평가 seed 집합이 바뀌었다")
        for seed in sorted(seeds):
            self.assertIn(seed, self.text)

    def test_21_the_lever_count_matches_the_master_table(self) -> None:
        """PM 반박 4.  '유효 측정이 있는 다이얼은 둘뿐'은 정본과 충돌했다 — 여기서 다시 센다."""
        master = (ROOT / "GO2_REWARD_EVIDENCE_MASTER.md").read_text(encoding="utf-8")
        table = master.partition("### 전체 시도")[2]
        stems = {"track": "track_lin_vel_xy_exp", "feet_air": "feet_air_time",
                 "ang_vel_xy": "ang_vel_xy_l2", "action_rate": "action_rate_l2",
                 "lin_vel_z": "lin_vel_z_l2", "flat": "flat_orientation_l2"}
        valid: set[str] = set()
        tried: dict[str, list[tuple[str, str]]] = {dial: [] for dial in stems.values()}
        for line in table.splitlines():
            if not line.startswith("| G-A"):
                continue
            cell = [c.strip() for c in line.split("|")]
            if cell[6] != "✓":                      # '유효' 칸
                continue
            for stem, dial in stems.items():
                if cell[2].startswith(stem):
                    valid.add(dial)
                    tried[dial].append((cell[2], cell[8]))   # (변경 값, 결정)
        self.assertEqual(valid, {"track_lin_vel_xy_exp", "feet_air_time",
                                 "ang_vel_xy_l2", "action_rate_l2"},
                         "걷는 기준선 유효 시도가 있는 다이얼 집합이 바뀌었다 — §5 를 다시 세라")
        unmeasured = set(stems.values()) - valid
        self.assertEqual(unmeasured, {"lin_vel_z_l2", "flat_orientation_l2"})
        # 2026-09-21 PM 재감사: 종류만 세면 "넷 다 한 방향만 재고 기각"이라는 거짓을 놓친다.
        # 그래서 여기서는 **방향의 부호**와 **채택 여부**까지 원표에서 읽는다.
        def direction(cell: str) -> int:
            body = cell.split(" ", 1)[1].replace("`", "").replace("−", "-")
            lo, _, hi = body.partition("→")
            a, b = float(lo.strip().split()[0]), float(hi.strip().split()[0])
            return (b > a) - (b < a)

        signs = {dial: {direction(cell) for cell, _ in attempts}
                 for dial, attempts in tried.items() if attempts}
        self.assertTrue(any("채택" in outcome for _, outcome in tried["track_lin_vel_xy_exp"]),
                        "track 의 채택 이력이 사라졌다 — §5 를 다시 쓰라")
        self.assertEqual(len(signs["feet_air_time"]), 2,
                         "feet_air_time 의 양방향 시도가 아니게 됐다 — §5 를 다시 쓰라")
        for dial in ("ang_vel_xy_l2", "action_rate_l2"):
            self.assertEqual(len(signs[dial]), 1,
                             f"{dial} 의 유효 시도가 더 이상 한 방향이 아니다 — §5 를 다시 쓰라")
            self.assertTrue(all("채택" not in outcome for _, outcome in tried[dial]),
                            f"{dial} 에 채택 이력이 생겼다 — §5 를 다시 쓰라")
        for phrase in ("상향을 재서 **채택**됐고", "**양방향을 다 재서**", "한 방향만 재고"):
            self.assertIn(phrase, self.text, f"§5 에 '{phrase}' 가 없다")
        self.assertIn("여섯 중 넷", self.text, "§5 가 개수를 적지 않았다")
        for dial in sorted(unmeasured):
            self.assertIn(dial, self.text)
        # 초판이 틀렸다는 사실 자체를 남긴다 (조용한 수정 금지)
        self.assertIn("초판은 여기서 틀렸다", self.text)

    def test_22_claim_check_does_not_cover_this_document(self) -> None:
        """PM 반박 6.  claim-check 를 이 문서의 근거로 인용하면 안 된다 — 도구에 직접 물어 확인한다."""
        from tools.go2_claim_check import PROSE, classify        # noqa: PLC0415
        self.assertEqual(classify(DOC), "PLAN",
                         "분류가 바뀌었다 — §9-1 의 안내를 다시 쓰라")
        self.assertNotIn(DOC, PROSE, "이 문서가 claim-check 대상이 됐다 — §9-1 을 다시 쓰라")
        self.assertIn("claim-check를 이 문서의 근거로 인용하면 안 된다", self.text)

    def test_23_the_schedule_is_closed_and_the_rule_lives_elsewhere(self) -> None:
        """§4·P0 의 전제.  예산이 적힌 계획서는 스스로 닫혔고, 규칙은 결정 원장에 이어져 있다."""
        schedule = (ROOT / "GO2_CAMPAIGN_SCHEDULE.md").read_text(encoding="utf-8")
        head = "\n".join(schedule.splitlines()[:12])
        self.assertIn("⚠️ CLOSED (260906).", head,
                      "계획서가 더 이상 닫혀 있지 않다 — §4·§4-1·P0 를 다시 판단하라")
        self.assertIn("G-A010 최초 사전등록(260902) 시점까지의 계획", head)
        self.assertIn("⚠️ CLOSED (260906).", self.text)
        state = (ROOT / "GO2_PROJECT_STATE.md").read_text(encoding="utf-8")
        self.assertIn("장기학습은 단일변수 screening 승자만 5k→10k→15k로 승급한다", state,
                      "G-D06 이 사라졌다 — §4 의 '규칙은 살아 있다'를 다시 확인하라")
        self.assertIn("G-D06", self.text)
        # 두 읽기(15000 / 30000)를 둘 다 적어야 한다
        self.assertIn("15000", self.text)
        self.assertIn("30000", self.text)


if __name__ == "__main__":
    unittest.main()
