"""사실 근거 추론 관문 — 추론 사슬이 닫히지 않은 회차 사양은 통과하지 못한다.

2026-09-16판은 "70점 기대 이득(수치) ≥ 검출 한계 2.53/70, 아니면 waiver"를 요구했다.
그 판에서는 어떤 후보도 이득을 추정할 수 없어(학습 seed 1개, 70점 축 점 3개) 모든 사양이 waiver로
빠져나갔고, waiver 사양(G-A038)은 예측의 계단 크기를 틀렸다.  2026-09-17 사용자 지시:
"이득 추정이 아니라 우리는 사실관계 근거 추론이 더 중요해."

그래서 새 사양은 `inference` 블록으로 다음 사슬을 적어야 한다(MASTER §5, AGENTS §4-9).
  role            원문 역할 (Isaac Lab v2.3.1 식, 기반 데이터 §0-1)
  rows            지지하는 원자료 행 — 파일과 그 안에 **글자 그대로 있는** 키·값 (이 테스트가 파일을 읽어 확인)
  contradicting   반대로 나온 원자료 행 (없으면 빈 목록). 탐색 권고는 대응·반증 조건을 명시한다
  singularity     행들이 보여 주는 특이점
  predictions     걷기·계단·흔들림·밀침 방향 (up/down/same/unknown) 과 근거
  falsified_if    어떤 관측이 나오면 가설이 틀렸다고 하는가
  risk_axes       잃을 수 있는 G 축.  사전 등록이 fact_rules_v1 이어야 하고, G5 가 있으면 계단 오른 로봇 수 관문이 있어야 한다
  seed_limit      학습 seed 한계
  status          RECOMMENDED / HOLD_CONTRADICTED / HOLD_UNSUPPORTED / INFORMATION_RUN
반박된 모델(다이얼 모델)은 근거 행으로 쓸 수 없다.

점수 이득 수치는 요구하지 않는다.  적는다면 여전히 측정된 검출 한계 이상이어야 한다(잡음에 묻히는 이득을
근거처럼 쓰지 않게).
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import unittest
from pathlib import Path


def _probe_key(value) -> str:
    """사양의 숫자를 PROBE_SITUATIONS.csv 의 `to` 표기와 맞춘다(-1.25e-07 ↔ -1.25e-07)."""
    try:
        return repr(float(value)).replace("e-0", "e-0")
    except (TypeError, ValueError):
        return str(value)

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
SPECS = QUAD / "config/experiments"
sys.path.insert(0, str(ROOT / "tools"))

import go2_stage1_blind_spot as blind_spot  # noqa: E402

# tools/go2_eval_resolution.py 측정값(2026-09-16, A017 대 G-A033, 재표집 4000회).
TOTAL_DELTA_SD_70 = 1.264
DETECTION_LIMIT_70 = 2.0 * TOTAL_DELTA_SD_70  # 2.528

# 이 규칙 전에 만들어졌거나 실행된 사양. 배포된 ZIP의 바이트를 바꾸지 않기 위해 소급 적용하지 않는다.
# G-A038은 2026-09-17 옛 규칙(waiver)으로 실행됐다.  새 사양은 이 목록에 추가하지 않는다.
GRANDFATHERED = {
    "G-A010", "G-A013", "G-A015", "G-A016", "G-A017", "G-A018", "G-A019",
    "G-A020", "G-A021", "G-A022", "G-A024", "G-A025", "G-A027", "G-A030",
    "G-A031", "G-A032", "G-A033", "G-A038",
}
# 2026-09-22 (결함 C-12).  발행된 사양은 **발행 시점의 자료**를 인용한다.  회수된 회차가 기반 데이터와
# 탐침 표에 들어오면 그 인용이 현재 파일과 어긋난다 — 그런데 사양 JSON 은 발행 ZIP 안에 들어 있어
# 고칠 수 없다(빌더가 재빌드 바이트를 대조한다).  그래서 **이미 발행된** 사양의 **그 자료 하나**에
# 한해 글자 그대로 검사를 면제하고, 대신 발행본이 실제로 있는지 확인한다 — 면제의 근거가 "바꿀 수
# 없다" 이므로 바꿀 수 없다는 사실 자체를 검사한다.  새 사양은 여기에 들어갈 수 없다: 사람이 이 줄을
# 고쳐야 하고 그 순간 검토에 걸린다.  어긋난 내용은 각 값의 옆에 적는다.
PUBLISHED_SNAPSHOT = {
    ("G-A037", "reports/GO2_TUNING_BASE_DATA.md"):
        "A043 회수로 이 다이얼의 걷는 관측값이 `-3, -2 | -2` 에서 `-2.0`·`-1.5` 둘로 바뀌었다",
    ("G-A043", "reports/evidence/go2_reward_mechanism_20260917/PROBES.csv"):
        "같은 회수로 `-1.5` 의 range_status 가 OUT_OF_RANGE 에서 OBSERVED 가 됐다",
}


def _published(work_id: str) -> bool:
    """그 회차의 발행 ZIP 이 history 에 있는가 — 스냅샷 면제의 전제."""
    history = QUAD / "upload" / str(work_id) / "history"
    return history.is_dir() and any(history.rglob("*.zip"))


REQUIRED = ("role", "rows", "contradicting", "singularity", "predictions", "falsified_if",
            "risk_axes", "seed_limit", "status")
SITUATIONS = ("walk", "climb", "sway", "push")
DIRECTIONS = ("up", "down", "same", "unknown")
STATUSES = ("RECOMMENDED", "HOLD_CONTRADICTED", "HOLD_UNSUPPORTED", "INFORMATION_RUN")
EXECUTION_STATUSES = frozenset(("RECOMMENDED", "INFORMATION_RUN"))
# R-6 = 보상 가중치만.  env_reward_weight 는 배포 목록(6개 이름)에 없지만 env 의 RewTerm 인 보상 항을
# go2_task/env_cfg.py 의 같은 경로로 바꾸는 회차다 — 커리큘럼·지형·DR·명령은 그대로다.
# 2026-09-18: 이 둘째 값은 **우리가 넣은 것이고 사용자 승인 전이다** — 열린 결정 U1-R6-ENV-REWARD-20260918
# (workspace/training/quadruped/reports/GO2_OPEN_DECISIONS.md).  그러므로 이 관문의 통과는 R-6 준수의 증거가 아니다.
# 우리가 경계를 넓힌 것이고, 그 사실은 test_15 가 사양에 적히도록 강제한다.
R6_CHANGE_CLASSES = ("reward_weight", "env_reward_weight")
AXES = {"G1", "G2", "G3", "G4", "G5", "G6", "G7"}
# 반박된 모델의 산출물 (reports/GO2_G_A038_READOUT.md §5, tools/go2_dial_model.py MODEL_STATUS)
REFUTED_SOURCES = ("reports/runs/DIAL_MODEL.csv",)

# 이 관문(test_17)보다 먼저 만들어져 **이미 실행된** 회차.  발행 ZIP 은 불변이므로 사양을 고쳐 통과시키지
# 않고, 구멍을 이름으로 적어 남긴다 — 결함 C-11(reports/GO2_DEFECT_LEDGER.md).  새 사양은 여기에 들어갈
# 수 없다: test_17 이 실행 이력(reports/runs/RUNS.csv 가 아니라 upload/ 발행 여부)이 아니라 **이 목록에
# 없을 것**만 요구하므로, 추가하려면 사람이 이 줄을 고쳐야 하고 그 순간 검토에 걸린다.
STAGE1_BLIND_SPOTS = {
    "G-A042": ("G2:combined_yaw_right",),
    "G-A043": ("G2:combined_yaw_right",),
}


def _specs() -> list[tuple[Path, dict]]:
    return [(p, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(SPECS.glob("*.json"))]


def _new_specs() -> list[tuple[Path, dict]]:
    return [(p, s) for p, s in _specs() if s.get("work_id") not in GRANDFATHERED]


def _check_rows(test: unittest.TestCase, name: str, rows: list, work_id: str | None = None) -> None:
    for row in rows:
        test.assertIsInstance(row, dict, f"{name}: 행은 객체다")
        source = str(row.get("source", ""))
        if (work_id, source) in PUBLISHED_SNAPSHOT:
            # 발행된 사양이 인용한 자료가 그 뒤 갱신됐다 — 사양은 고칠 수 없다(아래 상수 설명).
            test.assertTrue(_published(work_id),
                            f"{name}: 발행본이 없는데 스냅샷 면제를 쓴다")
            continue
        test.assertNotIn(source, REFUTED_SOURCES, f"{name}: 반박된 모델 {source} 는 근거가 아니다")
        path = QUAD / source
        test.assertTrue(path.is_file(), f"{name}: 원자료 {source} 가 없다")
        text = path.read_text(encoding="utf-8")
        for key in ("key", "value"):
            test.assertTrue(str(row.get(key, "")).strip(), f"{name}: {source} 행에 {key} 가 없다")
            test.assertIn(str(row[key]), text, f"{name}: {source} 에 {row[key]!r} 가 글자 그대로 없다")
        if path.suffix.lower() == ".csv":
            # A literal somewhere in the same record is not a column attribution.
            # Keep old key/value citations, but require a unique exact row and cells.
            reader = csv.DictReader(io.StringIO(text))
            headers = reader.fieldnames or []
            test.assertTrue(headers and len(headers) == len(set(headers)),
                            f"{name}: {source} missing or duplicate CSV headers")
            for field in ("selector", "cells"):
                mapping = row.get(field)
                test.assertIsInstance(mapping, dict, f"{name}: {source} {field} required")
                test.assertTrue(mapping, f"{name}: {source} empty {field}")
                test.assertTrue(set(mapping) <= set(headers), f"{name}: {source} unknown column")
                test.assertTrue(all(isinstance(v, str) for v in mapping.values()),
                                f"{name}: CSV reference values must be exact strings")
            records = list(reader)
            test.assertTrue(all(None not in record and all(v is not None for v in record.values())
                                for record in records), f"{name}: malformed CSV record")
            matches = [record for record in records
                       if all(record[k] == v for k, v in row["selector"].items())]
            test.assertEqual(len(matches), 1, f"{name}: {source} selector must match exactly one row")
            for column, expected in row["cells"].items():
                test.assertEqual(matches[0][column], expected,
                                 f"{name}: {source} wrong value for column {column}")
            quoted = next(csv.reader([str(row["value"])]))
            test.assertTrue(all(value in row["cells"].values() for value in quoted),
                            f"{name}: legacy value is not bound to cited cells")
        test.assertTrue(str(row.get("reads", "")).strip(), f"{name}: {source} 행을 어떻게 읽었는지(reads) 없다")


def _check_recommendation(test: unittest.TestCase, name: str, block: dict) -> None:
    """Counterevidence limits certainty; it does not automatically ban an experiment.

    This validates disclosure, not scientific truth, release readiness or performance.
    R-6, package integrity and recovery-budget checks remain separate requirements.
    """
    if block["status"] not in EXECUTION_STATUSES or not block["contradicting"]:
        return
    test.assertIs(block.get("exploratory"), True, f"{name}: 반대 증거가 있는 권고는 탐색 실험이다")
    for key in ("counterevidence_response", "falsified_if"):
        test.assertTrue(str(block.get(key, "")).strip(), f"{name}: {key} 누락")


class InferenceChainGateTest(unittest.TestCase):
    def test_1_new_specs_carry_the_chain(self) -> None:
        for path, spec in _new_specs():
            with self.subTest(spec=path.name):
                block = spec.get("inference")
                self.assertIsInstance(block, dict, f"{path.name}: inference 블록이 없다")
                for key in REQUIRED:
                    self.assertIn(key, block, f"{path.name}: inference.{key} 가 없다")
                for key in ("role", "singularity", "falsified_if", "seed_limit"):
                    self.assertTrue(str(block[key]).strip(), f"{path.name}: inference.{key} 가 비어 있다")
                self.assertIn(block["status"], STATUSES)
                self.assertTrue(str(block.get("status_reason", "")).strip(), f"{path.name}: status_reason 이 없다")

    def test_2_rows_are_literally_in_the_sources(self) -> None:
        for path, spec in _new_specs():
            block = spec["inference"]
            with self.subTest(spec=path.name):
                self.assertGreaterEqual(len(block["rows"]), 2, f"{path.name}: 지지 행은 둘 이상")
                _check_rows(self, path.name, block["rows"], spec.get("work_id"))
                _check_rows(self, path.name, block["contradicting"], spec.get("work_id"))

    def test_3_counterevidence_requires_an_exploratory_response(self) -> None:
        for path, spec in _new_specs():
            block = spec["inference"]
            with self.subTest(spec=path.name):
                _check_recommendation(self, path.name, block)

    def test_4_predictions_cover_the_four_situations(self) -> None:
        for path, spec in _new_specs():
            predictions = spec["inference"]["predictions"]
            with self.subTest(spec=path.name):
                self.assertEqual(set(predictions), set(SITUATIONS))
                for situation, item in predictions.items():
                    self.assertIn(item.get("direction"), DIRECTIONS, f"{path.name}: {situation}")
                    self.assertTrue(str(item.get("basis", "")).strip(), f"{path.name}: {situation} 근거가 없다")

    def test_5_risk_axes_are_guarded(self) -> None:
        for path, spec in _new_specs():
            block, prereg = spec["inference"], spec["preregistered"]
            with self.subTest(spec=path.name):
                self.assertTrue(set(block["risk_axes"]) <= AXES)
                self.assertEqual(prereg.get("rule_version"), "fact_rules_v1",
                                 f"{path.name}: 위험 축을 지키는 fact_rules_v1 사전 등록이 없다")
                covered = set(prereg["target_axes"]) | set(prereg["guard_axes"])
                self.assertTrue(set(block["risk_axes"]) <= covered)
                if "G5" in block["risk_axes"]:
                    self.assertTrue(prereg["climb_guard"]["groups"], f"{path.name}: G5 위험인데 계단 관문이 없다")

    def test_17_a_risk_axis_is_visible_in_stage_1(self) -> None:
        """위험 축이라 적었으면 그 축이 무너지는 자리를 1단계가 재야 한다.

        2026-09-22 G-A043: `risk_axes` 에 G2 를 적고 1단계 23 case 에는 G2 의 lateral 만 넣었다.
        실제로 깨진 것은 G2 의 기준선 최약 case `combined_yaw_right` 였고(3 seed 전부), 1단계는
        TARGET_PASS 를 냈다.  결정적 손실은 69 case 를 다 돌린 뒤에야 보였다 — 결함 C-11.

        1단계 목록은 **표적 축**에서 만들어진다.  그래서 표적 축 악화는 조기에 멎지만(G-A042 가
        실제로 1단계에서 멎었다) 보호 축 악화는 멎지 않는다.  이 관문은 그 비대칭을 메운다.

        최약 case 는 저장된 기준선 69 case 에서 **회차 전에** 계산된다(0.1 초).  주의력이 아니라
        파일이 고른다.  seed 는 보지 않는다 — 그 case 를 재기는 하는가만 본다.

        한계: 최약 case 는 '가장 먼저 무너질 자리'의 대용이지 증명이 아니다.  다른 case 가 먼저
        무너지면 이 관문은 아무 말도 하지 않는다.  전수 69 회차에는 해당하지 않는다.
        """
        for path, spec in _new_specs():
            # 2026-09-22: **1단계 자체를 두지 않는 회차**는 전수 수집을 선언해야 한다.  그러지
            # 않으면 "1단계 목록을 비운다" 는 것만으로 이 관문을 빠져나갈 수 있고, 그것은 C-11 을
            # 고친 것이 아니라 감춘 것이다.  `stages.target` 이 있는 회차는 목록이 있으므로 아래
            # 최약 case 검사를 그대로 받는다(required_target_cases 가 없으면 채점 표적이 목록이다).
            if "target" not in (spec.get("stages") or {}):
                with self.subTest(spec=path.name):
                    self.assertEqual(
                        (spec.get("collection") or {}).get("mode"), "full_69_single_stage",
                        f"{path.name}: 1단계가 없는데 전수 수집도 선언하지 않았다 —"
                        " 그러면 위험 축이 무너지는 자리를 아무도 재지 않는다")
                continue
            if not blind_spot.uses_stage_1(spec):
                continue
            with self.subTest(spec=path.name):
                report = blind_spot.read_spec(spec)
                if not report["readable"]:
                    self.skipTest(f"{path.name}: 저장된 기준선 {report['stored_arm']} 가 없다")
                allowed = set(STAGE1_BLIND_SPOTS.get(spec.get("work_id"), ()))
                for row in report["axes"]:
                    case = ":".join(row["weakest_case"].split(":")[:2])
                    if case in allowed:
                        continue
                    self.assertTrue(
                        row["in_stage_1"],
                        f"{path.name}: 위험 축 {row['axis']} 의 기준선 최약 case "
                        f"{row['weakest_case']} (생존x추종 {row['baseline_score']:.4f}) 가 "
                        "1단계 목록에 없다 — 그 축이 무너져도 1단계는 통과한다")

    def test_6_a_stated_point_gain_must_clear_the_limit(self) -> None:
        for path, spec in _new_specs():
            gain = (spec.get("detectability") or {}).get("expected_weighted_gain_70")
            with self.subTest(spec=path.name):
                if gain is None:
                    continue
                self.assertIsInstance(gain, (int, float), f"{path.name}: 이득을 적는다면 수치다")
                self.assertGreaterEqual(float(gain), DETECTION_LIMIT_70,
                                        f"{path.name}: 검출 한계 미만의 이득은 근거로 적지 않는다")

    def test_7_thresholds_cite_a_measurement(self) -> None:
        for path, spec in _new_specs():
            with self.subTest(spec=path.name):
                self.assertTrue(str(spec["preregistered"].get("threshold_basis", "")).strip())

    def test_8_limit_constant_matches_the_recorded_measurement(self) -> None:
        plan = (QUAD / "upload/plan/GO2_BASIC_MOTION_TUNING_PLAN_20260915.md").read_text(encoding="utf-8")
        self.assertIn("1.264", plan)
        self.assertIn("2.53/70", plan)
        self.assertAlmostEqual(DETECTION_LIMIT_70, 2.528, places=3)

    def test_9_the_old_waiver_rule_is_gone_from_the_rule_texts(self) -> None:
        """규칙 문서가 '이득 수치 필수'로 되돌아가지 않는다."""
        master = (ROOT / "GO2_REWARD_EVIDENCE_MASTER.md").read_text(encoding="utf-8")
        self.assertNotIn("기대 가중 이득은 **수치여야 한다.**", master)
        self.assertIn("사실 근거 추론 사슬", master)
        replan = (QUAD / "upload/plan/GO2_REPLAN_20260916.md").read_text(encoding="utf-8")
        self.assertNotIn("규칙: 70점 축 기대 이득이 추정되지 않으면 권하지 않는다", replan)


    # 2026-09-18: 아래 셋은 추천(RECOMMENDED) 사양에만 건다.  보류 사양은 근거가 닫히지 않았다는
    # 기록이므로 번호·출처를 소급해서 막지 않는다.  막으려는 실패는 2026-09-18에 실제로 일어난 것이다:
    # 원장을 읽지 않고, 실행된 회차보다 앞 번호의 옛 초안을, R-6 밖 변경으로 1순위 추천했다.
    def test_10_a_recommendation_is_newer_than_every_executed_run(self) -> None:
        """추천 사양의 번호는 원장에 실행된 모든 회차보다 커야 한다 (옛 초안 재활용 금지)."""
        ledger = (QUAD / "reports/runs/LEDGER.csv").read_text(encoding="utf-8")
        executed = {int(m) for m in re.findall(r"go2_g_a(\d{3})", ledger)}
        self.assertTrue(executed, "원장에서 실행된 회차 번호를 읽지 못했다")
        newest = max(executed)
        for path, spec in _new_specs():
            if spec["inference"]["status"] not in EXECUTION_STATUSES:
                continue
            with self.subTest(spec=path.name):
                match = re.fullmatch(r"G-A(\d+)", str(spec.get("work_id", "")))
                self.assertIsNotNone(match, f"{path.name}: work_id 형식이 G-Annn 이 아니다")
                # 2026-09-24 범위 정정 (결함 C-25 를 고치다 드러났다).  이 검사는 **옛 초안을 다시
                # 꺼내 추천하는 것**을 막으려는 것이다.  그런데 회차가 실제로 실행되면 그 회차 자신의
                # 사양이 "실행된 최신 회차보다 앞 번호" 가 되어 떨어진다 — 원장이 A038 에서 멈춰 있던
                # 동안에는 A041~A044 가 이 조건에 걸리지 않아 보이지 않던 결함이다(빨간 관문이 아니라
                # **거짓 초록**이었다).  자기 자신이 이미 실행된 사양은 초안 재활용이 아니므로 건너뛴다.
                if int(match.group(1)) in executed:
                    continue
                self.assertGreater(int(match.group(1)), newest,
                                   f"{path.name}: 실행된 최신 회차 {newest} 보다 앞 번호를 추천했다")

    def test_11_only_a_reward_weight_change_can_be_recommended(self) -> None:
        """R-6 밖 변경(학습 길이·seed 등)은 **추천**으로 올릴 수 없다.

        2026-09-24 범위 정정.  이 검사는 `EXECUTION_STATUSES`(RECOMMENDED + INFORMATION_RUN)
        전체에 걸려 있었다.  그런데 이 규칙이 막으려는 것은 제 이름대로 **추천**이다 —
        "R-6 밖 변경을 후보로 올리지 않는다" 와 "R-6 밖 변경을 재지도 않는다" 는 다른 문장이고,
        우리 계획서들은 뒤엣것을 요구한 적이 없다.  오히려 반대다: `GO2_A027_TUNING_PLAN_FOR_OPUS`
        P3 와 `GO2_BASIC_MOTION_TUNING_PLAN` §6-3 은 **승급 전에 독립 학습 seed 재현을 먼저 하라**고
        적는다.  넓은 범위대로 읽으면 계획서가 요구하는 회차를 우리 관문이 실행 불가로 만든다.
        그래서 추천에만 걸고, 정보 회차 쪽은 아래 test_11b 가 승급 금지를 글자로 요구한다.
        규칙을 넓힌 것이 아니라 **두 문장을 갈라 각각에 관문을 붙인 것**이며, R-6 해석 자체는
        열린 결정 U2-SEED-REPLICATE-20260918 으로 사용자 결정 대기다.
        """
        for path, spec in _new_specs():
            with self.subTest(spec=path.name):
                if spec["inference"]["status"] != "RECOMMENDED":
                    continue
                self.assertIn(spec.get("change_class"), R6_CHANGE_CLASSES,
                              f"{path.name}: R-6(보상 가중치) 밖인데 추천이다")

    def test_11b_a_non_reward_run_must_forbid_promotion_in_writing(self) -> None:
        """R-6 밖 분류로 **실행**하는 사양은 승급 금지를 사양 안에 글자로 적어야 한다.

        열린 결정 U2-SEED-REPLICATE-20260918 이 열어 준 것은 측정이지 승급이 아니다.  사양만 읽고
        들어온 역할이 그 구분을 놓치면, 좋은 숫자가 나온 seed 회차가 조용히 후보가 된다.
        """
        for path, spec in _new_specs():
            with self.subTest(spec=path.name):
                if spec["inference"]["status"] not in EXECUTION_STATUSES:
                    continue
                if spec.get("change_class") in R6_CHANGE_CLASSES:
                    continue
                self.assertEqual(spec.get("promotion"), "forbidden_not_a_reward_change",
                                 f"{path.name}: R-6 밖 분류로 실행하면서 승급 금지를 적지 않았다")
                self.assertTrue(str(spec.get("promotion_reason", "")).strip(),
                                f"{path.name}: promotion_reason 이 비어 있다")

    def test_15_a_recommendation_that_leans_on_an_open_decision_must_name_it(self) -> None:
        """우리가 스스로 넓힌 규칙으로 통과하는 추천은 그 열린 결정 번호를 사양에 적어야 한다.

        2026-09-18 상황 인지 시험: 기획자가 "관문이 통과시키므로 R-6 안"이라고 답했다.  그런데
        `test_11` 을 통과시킨 `R6_CHANGE_CLASSES` 의 `env_reward_weight` 는 **이 회차를 위해 우리가
        넣은 값**이다.  관문이 경계를 검증한 것이 아니라 경계를 넓혀 통과시킨 것이고, 그 사실이
        사양 어디에도 없어 사양만 읽는 역할은 알 수 없었다.  열린 결정 원장
        (`tools/go2_open_decisions.py`, `reports/GO2_OPEN_DECISIONS.md`)에 `change_class` 가 걸려
        있으면, 그 분류로 추천하는 사양은 결정 번호를 `open_decisions` 에 적어야 한다.
        """
        sys.path.insert(0, str(ROOT / "tools"))
        import go2_open_decisions as decisions  # noqa: PLC0415

        hooks = decisions.by_change_class()
        for path, spec in _new_specs():
            with self.subTest(spec=path.name):
                if spec["inference"]["status"] not in EXECUTION_STATUSES:
                    continue
                needed = hooks.get(spec.get("change_class"))
                if not needed:
                    continue
                self.assertIn(needed, spec.get("open_decisions") or [],
                              f"{path.name}: `{spec.get('change_class')}` 로 추천하면서 그 분류를 허용한"
                              f" 열린 결정 {needed} 를 `open_decisions` 에 적지 않았다 —"
                              " 관문이 통과시킨 이유가 우리가 규칙을 넓힌 것임을 사양이 숨긴다")

    def test_16_a_recommendation_stands_on_an_analyst_readout(self) -> None:
        """기획은 **분석가 판독 위에** 선다 — 기준선 회차를 판독한 문서를 사양이 지목해야 한다.

        2026-09-18 사용자 지적: "기획자는 분석자의 자료를 기반으로 기획하는 것 아냐?"  맞다.
        그런데 역할 문서는 반대로 적혀 있었다 — `go2-analyst.md` 는 "**기획자의 사양을 받아** 판독"
        이고, `go2-planner.md` 의 읽기 순서 6개에는 분석가 판독이 아예 없었다.  두 역할이 같은
        원자료를 각자 따로 읽은 것이다.  그래서 기획자는 R-6 판단을 자기 역할 문서의 문장 하나에
        기댈 수밖에 없었고(상황 인지 시험 Q12 실패), 사후 검증은 이미 감사자 몫이라 분석가는
        감사자와 겹쳤다.  순서를 분석가 → 기획자 → 감사자로 되돌리고, 그 순서를 여기서 강제한다.

        검사는 문서 지목에 그치지 않는다: 사양이 고르는 **기준선 회차 이름**(`baseline.name`)이
        그 판독문 안에 글자 그대로 있어야 한다.  없으면 판독하지 않은 회차 위에 기획한 것이다.
        """
        for path, spec in _new_specs():
            with self.subTest(spec=path.name):
                if spec["inference"]["status"] not in EXECUTION_STATUSES:
                    continue
                readouts = spec["inference"].get("readout") or []
                self.assertTrue(readouts,
                                f"{path.name}: 추천인데 `inference.readout` 이 없다 —"
                                " 어느 분석가 판독 위에 선 기획인지 사양이 말하지 않는다")
                baseline = str((spec.get("baseline") or {}).get("name", "")).strip()
                self.assertTrue(baseline, f"{path.name}: baseline.name 이 없다")
                seen = False
                for ref in readouts:
                    found = [base / ref for base in (QUAD, ROOT, QUAD / "reports")
                             if (base / ref).is_file()]
                    self.assertTrue(found, f"{path.name}: 판독 {ref} 를 열 수 없다")
                    # 2026-09-19: 분석가 판독문이 재판독이면 이름이 `..._REREAD_...` 다
                    # (`reports/GO2_A038_REREAD_20260919.md`).  이름 검사는 "판독 문서인가"를 보려는
                    # 것이고 철자 하나를 보려는 것이 아니므로 판독 계열 이름을 함께 받는다.
                    # 실질 검사(기준선 이름이 그 판독문 안에 글자 그대로 있는가)는 아래가 그대로 한다.
                    self.assertTrue(any(word in Path(ref).name.upper() for word in ("READOUT", "REREAD")),
                                    f"{path.name}: {ref} 는 분석가 판독 문서가 아니다")
                    if baseline in found[0].read_text(encoding="utf-8"):
                        seen = True
                self.assertTrue(seen,
                                f"{path.name}: 기준선 {baseline} 가 지목한 판독문 어디에도 없다 —"
                                " 판독되지 않은 회차 위에 기획했다")

    def test_13_an_unmeasured_situation_may_not_be_quoted_as_measured(self) -> None:
        """예측표의 빈 칸은 0 이 아니라 '측정 없음'이다 (2026-09-18 회귀 사례 C05).

        `PROBE_SITUATIONS.csv` 는 보상 산술로 **계산한** 표이고, 항에 따라 구간 칸이 비어 있다
        (평가 기록에 관절·행동 열이 없어서다).  빈 칸을 근거로 방향을 주장하거나 '측정됐다'고
        적으면 예측을 측정으로 둔갑시키는 것이다."""
        probe_path = QUAD / "reports/evidence/go2_reward_mechanism_20260917/PROBE_SITUATIONS.csv"
        with probe_path.open(encoding="utf-8", newline="") as handle:
            probes = {(r["term"], r["to"]): r for r in csv.DictReader(handle)}
        for path, spec in _new_specs():
            single = spec.get("single_change") or {}
            key = (str(single.get("name")), _probe_key(single.get("to")))
            row = probes.get(key)
            if row is None:
                continue
            for situation in ("climb", "sway", "push"):
                cell = (row.get(f"{situation}_delta") or "").strip()
                basis = str(spec["inference"]["predictions"][situation].get("basis", ""))
                with self.subTest(spec=path.name, situation=situation):
                    if cell:
                        continue
                    self.assertNotRegex(basis, r"(?i)(measured|측정됨|측정된)",
                                        f"{path.name}: {situation} 은 측정이 없는데 측정이라 적었다")
                    if "PROBE_SITUATIONS" in basis:
                        self.assertRegex(basis, r"(?i)(empty|없|unknown)",
                                         f"{path.name}: 빈 칸을 근거처럼 인용했다")

    def test_14_every_path_in_a_spec_can_be_opened(self) -> None:
        """기획자가 적은 경로는 분석가가 그대로 열 수 있어야 한다 (2026-09-18 사용자 지시).

        `inference.rows` 는 test_2 가 이미 파일·키·값을 글자 그대로 확인한다.  막히지 않은 곳은
        사양의 **산문 필드**였다: G-A039 는 Isaac Lab 원문을 상류 경로(`envs/mdp/rewards.py`,
        `terrain_importer.py`)로, 기준선 기록을 벌거벗은 `steps.csv`(같은 이름 69개)로 적고 있었다.
        셋 다 분석가가 열 수 없으니 그 순간 근거가 아니라 주장이 된다 — 보존 사례 M02 와 같은 형태다.
        규칙: 저장소 기준 전체 경로이거나, 저장소 안에서 이름이 유일하거나, 여러 파일이면 glob 으로
        적고 그 glob 이 실제로 하나 이상 맞아야 한다.  말줄임(`...`)은 금지한다.
        `output.*` 은 아직 만들지 않은 산출물 이름이라 검사 밖이다."""
        pattern = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\-*]*\.(?:md|csv|py|json|yaml|sh)")
        index: dict[str, list[Path]] = {}
        for candidate in list(QUAD.rglob("*")) + list((ROOT / "tools").glob("*.py")):
            if candidate.is_file():
                index.setdefault(candidate.name, []).append(candidate)

        def walk(node, prefix=""):
            if isinstance(node, dict):
                for key, value in node.items():
                    yield from walk(value, f"{prefix}{key}.")
            elif isinstance(node, list):
                for item in node:
                    yield from walk(item, prefix)
            elif isinstance(node, str):
                yield prefix.rstrip("."), node

        for path, spec in _new_specs():
            refs: dict[str, str] = {}
            for field, text in walk(spec):
                if field.startswith("output."):
                    continue
                for ref in pattern.findall(text):
                    refs.setdefault(ref, field)
            for ref, field in sorted(refs.items()):
                with self.subTest(spec=path.name, ref=ref):
                    self.assertNotIn("...", ref, f"{path.name}({field}): 말줄임 경로 {ref}")
                    if any((base / ref).is_file() for base in (QUAD, ROOT, QUAD / "reports")):
                        continue
                    if "*" in ref:
                        self.assertTrue(list(QUAD.glob(ref)) or list(ROOT.glob(ref)),
                                        f"{path.name}({field}): glob {ref} 이 아무 파일도 맞지 않는다")
                        continue
                    # 2026-09-18 감사 D9: 이름만 유일하면 통과였다 — `foo/bar/TERM_VALUES.csv` 처럼
                    # 디렉터리를 틀리게 써도 지나갔다.  `/` 가 든 경로는 이름 대체를 허용하지 않는다.
                    self.assertNotIn("/", ref,
                                     f"{path.name}({field}): {ref} 는 그 경로에 파일이 없다"
                                     " — 원문이면 reports/evidence/ 의 보관본 경로로 적는다")
                    hits = index.get(Path(ref).name, [])
                    self.assertTrue(hits, f"{path.name}({field}): {ref} 를 저장소에서 열 수 없다")
                    self.assertEqual(len(hits), 1,
                                     f"{path.name}({field}): {ref} 는 같은 이름이 {len(hits)}개다"
                                     " — 전체 경로나 glob 으로 적는다")

    def test_12_a_recommendation_cites_the_run_ledger(self) -> None:
        """추천 사양은 회차 원장 산출물을 최소 한 행 인용한다 (원장을 읽지 않은 추천 금지)."""
        for path, spec in _new_specs():
            block = spec["inference"]
            if block["status"] not in EXECUTION_STATUSES:
                continue
            with self.subTest(spec=path.name):
                sources = [str(row.get("source", "")) for row in block["rows"]]
                self.assertTrue([s for s in sources if s.startswith("reports/runs/")],
                                f"{path.name}: reports/runs/ 원장 자산을 인용한 행이 없다")


if __name__ == "__main__":
    unittest.main()
