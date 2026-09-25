"""표를 셀 단위로 아티팩트에 대조한다 — 존재가 아니라 **귀속**을 본다.

`go2_claim_check`는 "이 숫자가 어딘가 있느냐"만 묻는다.  그래서 §7에서 G3과 G4를
바꿔 적어도 통과한다.  둘 다 표에 있는 숫자이기 때문이다.  이 도구가 그 구멍을 막는다.

각 바인딩은 (문서, 앵커, 행 이름, 열 이름) → 아티팩트 키를 선언한다.  선언되지 않은
행·열은 UNBOUND 로 보고한다 — 조용히 넘어가면 검사하지 않은 칸이 생기고, 검사하지
않은 칸이 바로 지난번에 내가 틀린 자리다.

    python tools/go2_table_audit.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
RUNS = QUAD / "reports/runs"
SYNTH = QUAD / "reports/GO2_RUN_SYNTHESIS_20260916.md"

CELL_NUMBER = re.compile(r"[+\-−]?\d+\.\d+")


def load_csv(name: str) -> list[dict[str, str]]:
    path = RUNS / name
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def table_after(path: Path, anchor: str) -> tuple[list[str], list[list[str]]]:
    """앵커 문자열이 나온 뒤 첫 번째 마크다운 표를 (헤더, 행들)로 돌려준다."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if anchor in line), None)
    if start is None:
        raise LookupError(f"앵커 없음: {anchor!r} in {path.name}")
    rows = []
    for line in lines[start:]:
        if line.lstrip().startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif rows:
            break
    if len(rows) < 2:
        raise LookupError(f"표 없음: {anchor!r}")
    return rows[0], [r for r in rows[2:] if any(r)]


def clean(cell: str) -> str:
    return cell.replace("**", "").replace("`", "").replace("−", "-").strip()


def number(cell: str) -> float | None:
    text = clean(cell)
    match = CELL_NUMBER.fullmatch(text.replace("−", "-"))
    return float(match.group()) if match else None


# ─────────────────────────────────────────────────────────────────────────────
# 바인딩 — (행 이름, 열 이름) 을 아티팩트 값으로 푼다.
# ─────────────────────────────────────────────────────────────────────────────
def margin_lookup() -> dict[tuple[str, str], float]:
    """§7 표: 행=A017/G-A033/Δ/표집 sd, 열=G1..G7, 계."""
    out: dict[tuple[str, str], float] = {}
    row_of = {"a017_observed": "A017", "a033_observed": "G-A033",
              "delta_observed": "Δ", "delta_resample_sd": "표집 sd"}
    total_of = {"delta_total_observed": ("Δ", "계"),
                "delta_total_resample_sd": ("표집 sd", "계")}
    for row in load_csv("BASELINE_MARGIN.csv"):
        metric, key, value = row["metric"], row["scenario"], float(row["value"])
        if metric in row_of and key.startswith("G"):
            out[(row_of[metric], key)] = value
        elif metric in total_of:
            out[total_of[metric]] = value
    for row in load_csv("SCENARIO_SCORES.csv"):
        if row["run"] == "go2_a017_full_suite" and row["arm"] == "a017":
            out[("A017", "계")] = float(row["total_70"])
        if row["run"] == "go2_g_a033_a017_track_lin_vel_xy_150":
            out[("G-A033", "계")] = float(row["total_70"])
    return out


def dial_level_lookup() -> dict[tuple[str, str], float]:
    """§11-3 표: 행=track 값, 열=terrain 평균."""
    out: dict[tuple[str, str], float] = {}
    for row in load_csv("DIAL_MODEL.csv"):
        if row["metric"] == "level_mean":
            out[(row["key"].split("=")[1], "terrain 평균")] = float(row["value"])
    return out


def dial_loo_lookup() -> dict[tuple[str, str], float]:
    """§11-2 표: 행=모델 이름, 열=LOO 평균절대오차."""
    keyed = {row["metric"]: float(row["value"]) for row in load_csv("DIAL_MODEL.csv")
             if row["key"] == "ALL"}
    col = "LOO 평균절대오차"
    return {("평균으로 찍기(대조군)", col): keyed.get("loo_mae_baseline"),
            ("track 선형", col): keyed.get("loo_mae_linear"),
            ("track 수준평균", col): keyed.get("loo_mae_levels_only"),
            ("사망 규칙 + track 수준평균", col): keyed.get("loo_mae_model")}


def tier1_lookup() -> dict[tuple[str, str], float]:
    """§8 표: 행=회차, 열=terrain@999 / Δ / 회귀 예측 / 잔차."""
    col = {"terrain_999": "terrain@999", "delta_tier1": "Δ(7 case tier1)",
           "insample_predicted": "회귀 예측", "insample_residual": "잔차"}
    return {(row["run"], col[row["metric"]]): float(row["value"])
            for row in load_csv("TIER1_REGRESSION.csv") if row["metric"] in col}


def tier1_loo_lookup() -> dict[tuple[str, str], float]:
    """§8-1 표: 행=뺀 회차, 열=실제 Δ / 예측 / 오차."""
    col = {"delta_tier1": "실제 Δ", "loo_predicted": "예측", "loo_error": "오차"}
    return {(row["run"], col[row["metric"]]): float(row["value"])
            for row in load_csv("TIER1_REGRESSION.csv") if row["metric"] in col}


BINDINGS = (
    ("§7 시나리오별 이동", SYNTH, "승급 근거는 사실상 G4 하나다", margin_lookup),
    ("§8 tier1 회귀", SYNTH, "전 회차에서 `terrain@999`와 결과는", tier1_lookup),
    ("§8-1 교차검증", SYNTH, "3개로 맞추고 남은 1개를", tier1_loo_lookup),
    ("§11-2 교차검증", SYNTH, "11-2. 모델과 교차검증", dial_loo_lookup),
    ("§11-3 track 수준", SYNTH, "규칙 2 — ", dial_level_lookup),
)


def audit() -> tuple[list[str], list[str]]:
    mismatch: list[str] = []
    unbound: list[str] = []
    for label, path, anchor, resolver in BINDINGS:
        header, rows = table_after(path, anchor)
        truth = resolver()
        for row in rows:
            name = clean(row[0])
            for col, cell in zip(header[1:], row[1:]):
                written = number(cell)
                if written is None:
                    continue
                key = (name, clean(col))
                if key not in truth or truth[key] is None:
                    unbound.append(f"{label}  [{name} × {clean(col)}] = {written}")
                    continue
                if round(truth[key], len(clean(cell).split(".")[1])) != written:
                    mismatch.append(
                        f"{label}  [{name} × {clean(col)}]  문서 {written}  아티팩트 {truth[key]:.5f}")
    return mismatch, unbound


def main() -> int:
    mismatch, unbound = audit()
    print(f"바인딩 {len(BINDINGS)}개 표 · 불일치 {len(mismatch)}건 · 미바인딩 {len(unbound)}칸\n")
    for line in mismatch:
        print(f"  [불일치] {line}")
    for line in unbound:
        print(f"  [미바인딩] {line}")
    return 1 if mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
