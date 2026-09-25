"""산문 속 숫자를 아티팩트에 대조한다.

이 도구가 존재하는 이유는 하나다.  계약 테스트는 전부 통과하는데 보고서 본문과
대화에서 내가 말한 숫자가 틀렸다.  게이트가 코드에만 있고 주장에는 없었다.

7건의 회수를 다시 읽으면 기전은 하나다 — **숫자를 만든 자리에서 곧바로 주장했다.**
생성과 주장 사이에 아무것도 없었다.  여기가 그 사이다.

규칙:
  * 문서의 소수는 전부 생성 아티팩트에서 나온 값이어야 한다.
  * 나오지 않는 값은 `DERIVED` 등록부에 유도식과 함께 적어야 통과한다.
  * 따라서 등록부의 길이가 곧 "내가 손으로 친 숫자"의 개수다.  짧게 유지한다.

정수는 검사하지 않는다.  절·연도·case 수·iteration이 섞여 잡음이 신호를 덮는다.
정수 주장은 `test_go2_canonical_consistency`의 countable-claims 검사가 맡는다.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
RUNS = QUAD / "reports/runs"
KEEP = ROOT / "workspace/_keep"

# ─────────────────────────────────────────────────────────────────────────────
# 문서 분류.  세 부류다.  어느 쪽도 아닌 문서가 있으면 계약이 깨진다 — 분류되지 않은
# 문서가 바로 내가 다음에 아무 표시 없이 인용할 문서이기 때문이다.
#
#   MEASURED  측정 결과를 보고하는 문서.  소수는 전부 아티팩트에 있어야 한다.
#   PLAN      제안·목표·게이트 값.  측정 주장이 아니므로 게이트를 걸지 않는다.
#             "목표 60점"에 아티팩트를 요구하면 근거를 지어내게 된다.
#   ARCHIVE   지난 감사·결과 기록.  현재 값이 아니다.  인용하려면 먼저 재측정한다.
# ─────────────────────────────────────────────────────────────────────────────
MEASURED = (
    ROOT / "GO2_NOW.md",
    ROOT / "GO2_PROJECT_STATE.md",
    ROOT / "GO2_REWARD_EVIDENCE_MASTER.md",
    ROOT / "ARTIFACT_MANAGEMENT.md",
    QUAD / "reports/GO2_RUN_SYNTHESIS_20260916.md",
    QUAD / "reports/GO2_G_A029_TUNING_AUDIT_20260914.md",
    QUAD / "reports/GO2_POST_A029_PLAN_POLICY_AUDIT_20260914.md",
    QUAD / "reports/GO2_TUNING_CAMPAIGN_AUDIT_20260914.md",
    QUAD / "reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md",
    QUAD / "reports/GO2_TUNING_BASE_DATA.md",
    QUAD / "reports/GO2_VARIABLE_INFLUENCE.md",
    QUAD / "reports/GO2_REWARD_MECHANISM_FORECAST.md",
    QUAD / "reports/GO2_G_A038_READOUT.md",
    QUAD / "reports/GO2_SEED_SENSITIVITY.md",
    QUAD / "reports/GO2_TUNING_POLICY_READOUT_20260918.md",
    QUAD / "reports/GO2_AXIS_BOTTLENECK.md",
    QUAD / "reports/GO2_A038_REREAD_20260919.md",
    QUAD / "reports/GO2_DEFECT_LEDGER.md",
    QUAD / "reports/GO2_PM_BRIEF.md",
)

# 문서 하나에만 묶는 진실 집합.  전역 풀에 넣으면 다른 문서의 근거 없는 숫자가 우연히
# 통과한다(2026-09-16: 계단 CSV 3개를 전역에 넣자 PROJECT_STATE·MASTER에서 11건씩 사라졌다).
DOC_SOURCES: dict[Path, tuple[Path, ...]] = {
    QUAD / "reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md": tuple(
        QUAD / "reports/evidence/go2_stairs_behavior_20260916" / name
        for name in ("STAIRS_CLIMB.csv", "CASE_BEHAVIOR.csv", "TRAINING_TERMS.csv",
                     "CLIMB_REWARD.csv", "WEIGHT_OUTCOME.csv", "LATERAL_BEHAVIOR.csv")),
    # 튜닝 기반 데이터(생성 문서, tools/go2_tuning_base_data.py).  표 칸을 CSV에서 글자 그대로 옮긴다.
    QUAD / "reports/GO2_TUNING_BASE_DATA.md": tuple(
        QUAD / "reports/evidence/go2_stairs_behavior_20260916" / name
        for name in ("WEIGHT_OUTCOME.csv", "LATERAL_BEHAVIOR.csv", "CLIMB_REWARD.csv",
                     "TRAINING_TERMS.csv", "CASE_BEHAVIOR.csv", "STAIRS_CLIMB.csv")),
    # 변수별 영향도 전수 판독(생성 문서, tools/go2_variable_influence.py).
    QUAD / "reports/GO2_VARIABLE_INFLUENCE.md": tuple(
        QUAD / "reports/evidence/go2_variable_influence_20260917" / name
        for name in ("PAIRS.csv", "PAIR_METRICS.csv")),
    # 정본 GO2_NOW.md.  2026-09-18 감사: NOW 가 G-A039 사슬을 요약하며 margin 네 값
    # (+0.0033 · +0.0155 · +0.1359 · +0.2060)을 인용하는데, 그 값이 든 보상 기전 CSV 가 전역 풀에
    # 없어 네 건 모두 '근거 없음'으로 남아 있었다.  값은 실제로 RUN_MARGIN.csv · PROBES.csv 칸이다 —
    # 상한(0)은 그대로 두고, 숫자가 나온 아티팩트를 문서에 묶는다.  전역 풀에 넣지 않는 이유는
    # 2026-09-16 의 교훈 그대로다(다른 문서의 근거 없는 숫자가 우연히 통과한다).
    ROOT / "GO2_NOW.md": tuple(
        QUAD / "reports/evidence/go2_reward_mechanism_20260917" / name
        for name in ("RUN_MARGIN.csv", "PROBES.csv")) + (
        # 2026-09-19: 축 병목 판독(생성 `tools/go2_axis_bottleneck.py`)의 재계산 값.
        QUAD / "reports/evidence/go2_axis_bottleneck_20260919/AXIS_BOTTLENECK.csv",),
    # 축 병목 판독(생성 문서).  표의 모든 칸이 이 CSV 에서 나온다.
    QUAD / "reports/GO2_AXIS_BOTTLENECK.md": (
        QUAD / "reports/evidence/go2_axis_bottleneck_20260919/AXIS_BOTTLENECK.csv",),
    # 2026-09-19 G-A038 재판독(생성 `tools/go2_a038_reread.py`).  분류되지 않은 채로 있었다 —
    # 분류되지 않은 문서가 바로 다음에 아무 표시 없이 인용할 문서다(test_2b 가 잡았다).
    # 측정 보고이므로 MEASURED 로 넣고, 표 칸이 나온 증거 CSV 를 이 문서에만 묶는다.
    QUAD / "reports/GO2_A038_REREAD_20260919.md": tuple(
        QUAD / "reports/evidence/go2_a038_reread_20260919" / name
        for name in ("CASE_SUMMARY.csv", "AXIS_RECON.csv", "CLIMB_COUNT.csv", "STAIRS10_ROLLUP.csv",
                     "STAIRS10_TIME_PROFILE.csv", "ROUGH_LATERAL_ROLLUP.csv", "FALL_CHANNEL_ROLLUP.csv")) + (
        QUAD / "reports/evidence/go2_fact_rules_20260917/CLIMB_GUARD.csv",
        # §4-3 이 축 병목 판독을 인용한다(생존 1.0 반사실 두 값).
        QUAD / "reports/evidence/go2_axis_bottleneck_20260919/AXIS_BOTTLENECK.csv"),
    # 결함 대장(생성 `tools/go2_defect_ledger.py`).  문서의 모든 칸이 이 CSV 에서 나온다 —
    # 결함 설명에 인용된 수치(바이트 수·하한·오탐률)도 대장 기록에서 나온 것이라 함께 묶는다.
    QUAD / "reports/GO2_DEFECT_LEDGER.md": (
        QUAD / "reports/evidence/go2_defect_ledger/DEFECTS.csv",),
    # PM 보고(생성 `tools/go2_pm_brief.py`).  PM 이 사용자에게 내는 수치가 관문을 지나게 하려고
    # 만든 문서다 — 표의 모든 칸이 이 CSV 에서 나온다.
    QUAD / "reports/GO2_PM_BRIEF.md": (
        QUAD / "reports/evidence/go2_pm_brief/BRIEF.csv",),
    # 튜닝 정책 판독문(2026-09-18 분석가).  표의 모든 칸이 원장·증거 CSV 에서 나왔다.
    # `reports/runs/` 의 원장(SCENARIO_SCORES·ARM_DELTAS·BASELINE_MARGIN·TERRAIN_AT_PIN)은
    # 이미 전역 풀이라 여기 적지 않는다 — test_5b 가 막는다.
    QUAD / "reports/GO2_TUNING_POLICY_READOUT_20260918.md": (
        QUAD / "reports/evidence/go2_axis_bottleneck_20260919/AXIS_BOTTLENECK.csv",
        QUAD / "reports/evidence/go2_fact_rules_20260917/CLIMB_GUARD.csv",
        QUAD / "reports/evidence/go2_stairs_behavior_20260916/STAIRS_CLIMB.csv",
        QUAD / "reports/evidence/go2_stairs_behavior_20260916/WEIGHT_OUTCOME.csv",
        QUAD / "reports/evidence/go2_stairs_behavior_20260916/LATERAL_BEHAVIOR.csv",
        QUAD / "reports/evidence/go2_reward_mechanism_20260917/RUN_MARGIN.csv",
        QUAD / "reports/evidence/go2_reward_mechanism_20260917/TERM_VALUES.csv",
        QUAD / "reports/evidence/go2_seed_sensitivity_20260917/ONE_CHANGE_DRIFT.csv",
        QUAD / "reports/evidence/go2_seed_sensitivity_20260917/SAME_SEED_REPEAT.csv",
        QUAD / "reports/evidence/go2_seed_sensitivity_20260917/EVAL_SEED_SPREAD.csv",
        QUAD / "reports/evidence/go2_g_a038_readout_20260917/CURRICULUM_LAG.csv",
        QUAD / "reports/evidence/go2_g_a038_readout_20260917/GUARD_BOUNDS.csv",
    ),
    # 보상 기전 예측(생성 문서, tools/go2_reward_mechanism.py).  식 값·margin·기울기는 이 CSV 칸이다.
    QUAD / "reports/GO2_REWARD_MECHANISM_FORECAST.md": tuple(
        QUAD / "reports/evidence/go2_reward_mechanism_20260917" / name
        for name in ("TERM_VALUES.csv", "RUN_MARGIN.csv", "PROBES.csv", "TILT.csv")) + (
        QUAD / "reports/evidence/go2_stairs_behavior_20260916/WEIGHT_OUTCOME.csv",
        QUAD / "reports/evidence/go2_stairs_behavior_20260916/CLIMB_REWARD.csv"),
    # G-A038 판독(tools/go2_g_a038_readout.py).  수치는 이 CSV 칸이고, 문서와 CSV의 일치는
    # test_go2_g_a038_readout_contract 가 따로 검사한다.
    QUAD / "reports/GO2_G_A038_READOUT.md": tuple(
        QUAD / "reports/evidence/go2_g_a038_readout_20260917" / name
        for name in ("REPORT_VALUES.csv", "FORECAST_CHECK.csv")) + (
        QUAD / "reports/evidence/go2_reward_mechanism_20260917/PROBE_SITUATIONS.csv",),
    # seed 흔들림 판독(생성 문서, tools/go2_seed_sensitivity.py).  표 칸은 이 CSV 글자 그대로다.
    QUAD / "reports/GO2_SEED_SENSITIVITY.md": tuple(
        QUAD / "reports/evidence/go2_seed_sensitivity_20260917" / name
        for name in ("SAME_SEED_REPEAT.csv", "ONE_CHANGE_DRIFT.csv", "TERM_HEADROOM.csv", "BAND_RUNS.csv",
                     "EVAL_SEED_SPREAD.csv")),
}

PLAN_DIRS = (QUAD / "upload/plan",)
# 2026-09-18 감사: 새 자산 셋이 어느 부류도 아니었다 — 분류되지 않은 문서가 바로 다음에
# 아무 표시 없이 인용할 문서다.
#   * 열린 결정 원장·역할 시험지는 측정 보고가 아니라 규칙·문항이다 -> PLAN.
#   * 튜닝 정책 판독문은 분석가가 원자료에서 꺼낸 **측정 보고**다 -> MEASURED(아래).
PLAN = (ROOT / "GO2_CAMPAIGN_SCHEDULE.md",
        QUAD / "reports/GO2_OPEN_DECISIONS.md",
        QUAD / "reports/GO2_ROLE_SITUATION_EXAM.md")

ARCHIVE_PREFIXES = ("GO2_DESIGN_REVIEW_", "GO2_INDEPENDENT_AUDIT_", "GO2_OPUS_REAUDIT_",
                    "GO2_CODEX_REPAIR_REVIEW_", "GO2_REAUDIT_", "GO2_RESULT_AUDIT_")
ARCHIVE_NAMES = ("GO2_DEFAULT_VS_PILOT_ANALYSIS_260901.md",
                 "GO2_PILOT_V2_BASELINE_RESULT_ANALYSIS_260903.md",
                 "GO2_TRACK_LIN_VEL_120_RESULT_ANALYSIS_260902.md",
                 "GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md",
                 "GO2_EVALUATION_PROTOCOL.md", "GO2_EVIDENCE_INDEX.md",
                 "NEW_SESSION_HANDOFF.md")

PROSE = MEASURED  # 게이트가 실제로 검사하는 것


def go2_documents() -> list[Path]:
    """분류 대상 — 사람이 쓰는 Go2 문서 전부. 생성물(`reports/runs`)은 제외한다."""
    docs = sorted(ROOT.glob("GO2_*.md")) + [ROOT / "ARTIFACT_MANAGEMENT.md"]
    docs += [p for p in sorted(QUAD.rglob("*.md")) if RUNS not in p.parents]
    return [p for p in docs if p.is_file()]


def is_closed(path: Path) -> bool:
    """머리말에 스스로 CLOSED 라고 적은 문서.  손으로 등록하지 않아도 잡힌다.

    GO2_CAMPAIGN_SCHEDULE.md 가 그 예다 — 260906 에 닫혔다고 자기 3번째 줄에 적어놓고
    분류는 PLAN 이었다.  닫힌 문서를 계획으로 분류하면 지난 계획을 현재 계획처럼 인용한다.
    """
    try:
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
    except OSError:
        return False
    return "CLOSED" in head


def classify(path: Path) -> str:
    if path in MEASURED:
        return "MEASURED"
    if path.name == "GO2_ROLE_REGRESSION_CASES.md":
        # 역할 회귀 사례(생성 문서, tools/go2_role_regression.py).  지난 실수의 기록이다 — 현재 측정이
        # 아니라 시험 자료이므로 숫자 게이트를 걸지 않는다.  사례와 관문의 대응은
        # tools/test_go2_role_regression_contract.py 가 실제로 돌려서 검사한다.
        return "ARCHIVE"
    if path.name == "GO2_REFERENCE_COMPASS.md":
        # 참고 자료 나침반(생성 문서, tools/go2_reference_compass.py).  로봇 측정 주장이 아니라
        # 파일 목록·성격 분류다 — 숫자는 파일 크기뿐이므로 숫자 게이트를 걸지 않는다.  경로 존재와
        # 재생성 일치는 tools/test_go2_reference_compass_contract.py 가 검사한다.
        return "INDEX"
    if path.name in ("AGENTS.md", "README.md"):
        return "RULES"          # 절차·규칙. 측정 주장이 아니다.
    if is_closed(path):
        return "ARCHIVE"        # 스스로 닫혔다고 적은 문서는 계획이 아니다.
    if path.name.endswith(".VERIFICATION.md"):
        return "ARCHIVE"        # 그 패키지가 무엇을 담았는지의 동결 기록.
    if (QUAD / "reports/evidence") in path.parents:
        return "ARCHIVE"        # 회차별 증거 묶음. 당시 값이다.
    if path in PLAN or any(d in path.parents for d in PLAN_DIRS):
        return "PLAN"
    if path.name in ARCHIVE_NAMES or path.name.startswith(ARCHIVE_PREFIXES):
        return "ARCHIVE"
    return "UNCLASSIFIED"


def unclassified() -> list[Path]:
    return [p for p in go2_documents() if classify(p) == "UNCLASSIFIED"]

# 유니코드 빼기(−)를 쓰는 표가 있다.  ASCII 하이픈과 같이 받는다.
NUMBER = re.compile(r"[+\-−]?\d+\.\d+")

# 코드·경로·해시 안의 숫자는 주장이 아니다.
MASKS = (
    re.compile(r"`[^`]*`"),                     # 인라인 코드
    re.compile(r"```.*?```", re.S),             # 코드 블록
    re.compile(r"\[[^\]]*\]\([^)]*\)"),         # 링크
    re.compile(r"\b[0-9a-f]{8,}\b"),            # sha256 조각
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),       # 날짜
    re.compile(r"\bv\d+\.\d+(\.\d+)?\b"),       # 버전 (Isaac Lab v2.3.1)
    re.compile(r"§\s*\d+(-\d+)?"),              # 절 번호
)


# ─────────────────────────────────────────────────────────────────────────────
# 손으로 친 숫자 등록부.
#
# 여기 있는 항목은 "측정값이 아니라 내가 계산한 값"이다.  각 항목은 유도식을 달아야
# 한다.  유도식이 비면 통과하지 않는다.  이 표가 길어지면 그만큼 검증되지 않은
# 숫자를 말하고 있다는 뜻이므로, 길이 자체가 경고다.
# ─────────────────────────────────────────────────────────────────────────────
DERIVED: dict[str, str] = {
    "0.15": "70점 축 가중치 G1/G2/G4/G5 — go2_fixed_eval_report 상수",
    "0.20": "70점 축 가중치 G3 — go2_fixed_eval_report 상수",
    "0.10": "70점 축 가중치 G6/G7 — go2_fixed_eval_report 상수",
    "0.99": "posture_gate_v2 measurement_contract 커버리지 하한 — 계측 정의값",
    "23.7": "A033 캠페인 실측 74 case / 28.9분 = 23.4~23.7 s/case (러너 로그)",
    "6.8": "69 case x 23.7s x 15 arm / 3600 = 6.8h — 견적, 측정 아님",
    "2.7": "69 case x 23.7s x 6 arm / 3600 = 2.7h — 견적, 측정 아님",
    "0.0006": "추종 rmse 폭 = v2 0.1999 - blind 0.1993 (SCENARIO_SCORES.csv 두 행의 차)",
}
# 2026-09-18: 튜닝 정책 판독문의 축별 2σ 를 여기 12줄로 등록하려다 멈췄다.  등록부 상한(8)은
# 올리지 않는 규칙이고, 애초에 그 값들은 손으로 친 숫자가 아니라 GUARD_BOUNDS.csv 의 칸이다 —
# 문서를 그 아티팩트에 묶는 것이 옳다.  나머지(감점 합·채움률·한계 초과 폭)는 판독문에서 지웠다:
# 유도값을 등록해 통과시키는 것보다 원장 칸을 그대로 인용하는 편이 낫다.


def unmask(text: str) -> str:
    for mask in MASKS:
        text = mask.sub(" ", text)
    return text


def numbers_in(text: str) -> list[str]:
    return NUMBER.findall(unmask(text))


def norm(token: str) -> float:
    return float(token.replace("−", "-"))


def decimals(token: str) -> int:
    return len(token.split(".")[1])


# ─────────────────────────────────────────────────────────────────────────────
# 진실 집합 — 전부 생성물에서만 읽는다.  손으로 넣는 경로는 없다.
# ─────────────────────────────────────────────────────────────────────────────
def walk_json(node: Any, out: list[float]) -> None:
    if isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        out.append(float(node))
    elif isinstance(node, dict):
        for value in node.values():
            walk_json(value, out)
    elif isinstance(node, list):
        for value in node:
            walk_json(value, out)


def measured() -> list[float]:
    """생성 아티팩트에 실제로 적힌 수치 전부."""
    values: list[float] = []

    for table in sorted(RUNS.glob("*.csv")):
        with table.open(encoding="utf-8", newline="") as handle:
            for row in csv.reader(handle):
                for cell in row:
                    try:
                        values.append(float(cell))
                    except (TypeError, ValueError):
                        continue

    for report in sorted(RUNS.glob("*.md")):
        for token in NUMBER.findall(report.read_text(encoding="utf-8")):
            values.append(norm(token))

    for path in KEEP.rglob("SELF_EVAL_REPORT.json"):
        try:
            walk_json(json.loads(path.read_text(encoding="utf-8")), values)
        except (json.JSONDecodeError, OSError):
            continue

    return values


_INDEX: dict[int, set[float]] = {}


def index_for(places: int, pool: Iterable[float]) -> set[float]:
    """자릿수별 반올림 집합.  `supported` 를 선형 탐색에서 O(1) 로 바꾼다."""
    if places not in _INDEX:
        seen: set[float] = set()
        for value in pool:
            seen.add(round(value, places))
            seen.add(round(value * 100, places))   # 백분율로 적은 비율
        _INDEX[places] = seen
    return _INDEX[places]


def supported(token: str, pool: Iterable[float]) -> bool:
    """문서의 값은 반올림돼 있다.  적힌 자릿수로 맞춰 비교한다."""
    return norm(token) in index_for(decimals(token), pool)


# ─────────────────────────────────────────────────────────────────────────────
# 게이트의 힘.
#
# 존재 게이트는 풀이 커질수록 약해진다.  18,473개까지 커지면 소수 1자리는 거의
# 무엇이든 우연히 맞는다 — 즉 "근거 없는 소수 0건"이 "검증됐다"를 뜻하지 않는다.
# 그래서 개수만 보고하는 것을 금지하고, 도구가 자기 오탐률을 같이 재서 말한다.
#
# 2026-09-16 실측(무작위 2,000건): 1자리 98.9% · 2자리 55.0% · 3자리 9.2% · 4자리 1.2%.
# 소수 2자리 이하는 게이트의 맹점이다.  그 숫자들은 존재가 아니라 **귀속**으로
# 지켜야 한다 (`go2_table_audit`).
# ─────────────────────────────────────────────────────────────────────────────
BLIND_PLACES = 2


def false_pass_rate(places: int, pool: list[float], trials: int = 2000,
                    seed: int = 42) -> float:
    """그 자릿수의 무작위 숫자가 통과하는 비율.  게이트가 주는 정보량의 역수다."""
    import random
    rng = random.Random(seed)
    lo, hi = 0.0002, 40.0          # 문서에 실제로 나오는 크기 범위
    index = index_for(places, pool)
    hits = sum(1 for _ in range(trials)
               if round(rng.uniform(lo, hi), places) in index)
    return hits / trials


def strength(paths: Iterable[Path] = ()) -> dict[str, tuple[int, int]]:
    """문서별 (게이트가 검사한 수, 게이트가 못 보는 수)."""
    out: dict[str, tuple[int, int]] = {}
    for path in paths or PROSE:
        if not path.is_file():
            continue
        blind = checked = 0
        for token in numbers_in(path.read_text(encoding="utf-8")):
            if decimals(token) <= BLIND_PLACES:
                blind += 1
            else:
                checked += 1
        out[str(path.relative_to(ROOT)).replace("\\", "/")] = (checked, blind)
    return out


def own_values(path: Path) -> set[str]:
    """DOC_SOURCES 에 묶인 CSV 칸을 적힌 그대로(문자열) 모은다 — 반올림 일치가 아니라 글자 일치."""
    values: set[str] = set()
    for table in DOC_SOURCES.get(path, ()):
        with table.open(encoding="utf-8", newline="") as handle:
            for row in csv.reader(handle):
                values.update(cell.lstrip("+-") for cell in row)
    return values


def own_rounded(path: Path) -> dict[int, set[float]]:
    """묶인 CSV 칸을 **자릿수별로 반올림**해 모은다.

    2026-09-19: `own_values` 는 글자 일치만 본다.  생성기가 전체 자릿수로 쓴 칸(`0.30379...`)을
    문서가 4자리(`0.3038`)로 인용하면 글자가 달라 근거 없음으로 잡혔다 — 자기 CSV 에서 나온
    값인데도다(G-A038 재판독 79건).  여기서 **그 문서에 묶인 표만** 반올림해 받는다.  전역 풀이
    아니라 문서 하나의 표이므로 우연 통과 위험은 전역 존재 게이트보다 훨씬 작고, 묶이지 않은
    문서에는 아무 영향이 없다.
    """
    values = [float(v) for v in own_values(path) if _is_number(v)]
    return {places: {round(v, places) for v in values} for places in range(1, 11)}


def _is_number(cell: str) -> bool:
    try:
        float(cell)
    except (TypeError, ValueError):
        return False
    return True


def check(paths: Iterable[Path] = PROSE) -> list[tuple[str, int, str, str]]:
    pool = measured()
    unbacked: list[tuple[str, int, str, str]] = []
    for path in paths:
        if not path.is_file():
            continue
        own = own_values(path)
        own_round = own_rounded(path)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for token in numbers_in(line):
                key = token.lstrip("+−-")
                if key in DERIVED or key in own:
                    continue
                if norm(token) in own_round.get(decimals(token), ()):
                    continue
                if supported(token, pool):
                    continue
                unbacked.append((str(path.relative_to(ROOT)), lineno, token, line.strip()[:90]))
    return unbacked


def main() -> int:
    pool = measured()
    unbacked = check()
    print(f"아티팩트 수치 {len(pool)}개 · 손으로 친 숫자 등록부 {len(DERIVED)}개")

    # 개수만 보고하는 것을 금지한다.  0건이 검증을 뜻하지 않기 때문이다.
    print("\n게이트 오탐률 — 무작위 숫자가 그냥 통과하는 비율")
    for places in (1, 2, 3, 4):
        rate = false_pass_rate(places, pool)
        mark = "  <- 맹점" if places <= BLIND_PLACES else ""
        print(f"  소수 {places}자리 {rate:6.1%}{mark}")

    print("\n문서별 (게이트가 검사한 수 / 못 보는 수)")
    for name, (checked, blind) in strength().items():
        total = checked + blind
        if total:
            print(f"  {name:58} {checked:4} / {blind:4}  맹점 {blind/total:3.0%}")
    print("  맹점 숫자는 존재가 아니라 귀속으로 지킨다 — tools/go2_table_audit.py")

    if not unbacked:
        print("\n근거 없는 소수 0건 (단, 위 맹점은 애초에 검사되지 않았다)")
        return 0
    print(f"\n근거 없는 소수 {len(unbacked)}건 — 아티팩트에도 등록부에도 없다\n")
    for path, lineno, token, line in unbacked:
        print(f"  {path}:{lineno}  {token}\n      {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
