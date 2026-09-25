#!/usr/bin/env python3
"""G-A043 의 총점 +2.096/70 을 시나리오·case 로 쪼갠다 — 어디서 얻고 어디서 잃었는가.

왜 있는가.  A043 판정문은 `+2.095932/70`, 사전등록 `+2.53` 미달이라는 한 줄로 요약된다.  그 한 줄은
**상쇄된 두 덩어리**를 감춘다: G2 를 뺀 여섯 축의 순이득 `B` 와 G2 한 축의 손실 `L` 이다.  다음 회차의
판정을 해석할 때 둘을 나누어 보지 않으면 "조금 모자랐다" 와 "크게 얻고 크게 잃었다" 가 같은 문장이 된다.
계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md` §9-1 이 사전등록한 `B`·`L` 이 이 표에서 나온다.

무엇을 계산하지 않는가.  이 도구는 **판정하지 않는다**.  사전등록 문턱(c2 `+2.53`, c3 평지 하락 `0.054`,
case 생존 하락 `0.0625`)은 `tools/verify_go2_basic_motion_harvest.py` 가 읽고, 이 표는 그 판정이 읽은
것과 같은 원자료를 사람이 읽을 수 있는 모양으로 옮길 뿐이다.  점수는 내부 proxy 이고 공식 점수가 아니다.

한계.  시나리오 점수는 **case 최솟값**이라 한 case 가 축 전체를 끌어내린다(registry `scenario_aggregation`).
그래서 `SCENARIO_SPLIT.csv` 의 축 변화는 대개 `binding_case` 한 칸의 변화이고, 축 안의 다른 case 가
좋아졌는지 나빠졌는지는 `CASE_DELTAS.csv` 를 봐야 한다.  두 표를 함께 읽어야 하는 이유가 그것이다.

    python -B tools/go2_a043_scenario_split.py            # 표를 다시 만든다
    python -B tools/go2_a043_scenario_split.py --check     # 표가 원자료와 같은지만 본다
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import verify_go2_g_a030_harvest as a030  # noqa: E402
from go2_fixed_eval_report import build_policy  # noqa: E402

OUT = QUAD / "reports" / "evidence" / "go2_a043_scenario_split_20260922"
BASELINE = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
CANDIDATE = ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15/evaluation/candidate"
# 계획 §9-1 이 `L` 로 부르는 축.  A043 에서 손실이 이 한 축에 모였다.
LOSS_AXIS = "G2"
# 사전등록 값 — 사양 `config/experiments/G_A043_a033_lin_vel_z_m15.json` `preregistered`.
MIN_TOTAL_POINTS_DELTA = 2.53
MAX_FLAT_SCENARIO_PROXY_DROP = 0.054
POINTS = 70.0


def _fmt(value: float | None, places: int = 5) -> str:
    return "" if value is None else f"{value:.{places}f}"


def policies() -> tuple[dict[str, Any], dict[str, Any]]:
    for arm in (BASELINE, CANDIDATE):
        if not (arm / "cases").is_dir():
            raise SystemExit(f"수확물이 없다: {arm}")
    return build_policy(BASELINE, a030.REGISTRY, None), build_policy(CANDIDATE, a030.REGISTRY, None)


def scenario_rows(base: dict[str, Any], cand: dict[str, Any]) -> list[list[str]]:
    rows = [["scenario", "weight", "baseline_proxy", "candidate_proxy",
             "baseline_points_70", "candidate_points_70", "delta_70",
             "baseline_binding_case", "candidate_binding_case"]]
    for axis in sorted(set(base["scenarios"]) | set(cand["scenarios"])):
        b, c = base["scenarios"].get(axis), cand["scenarios"].get(axis)
        if b is None or c is None:
            rows.append([axis, "", "", "", "", "", "", "", ""])
            continue
        weight = float(b["weight"])
        bp, cp = weight * float(b["scenario_proxy"]) * POINTS, weight * float(c["scenario_proxy"]) * POINTS
        rows.append([axis, f"{weight:.2f}", _fmt(b["scenario_proxy"]), _fmt(c["scenario_proxy"]),
                     _fmt(bp), _fmt(cp), _fmt(cp - bp),
                     "%s:%s" % (b["worst_case"]["case_id"], b["worst_case"]["seed"]),
                     "%s:%s" % (c["worst_case"]["case_id"], c["worst_case"]["seed"])])
    return rows


def case_rows(base: dict[str, Any], cand: dict[str, Any]) -> list[list[str]]:
    rows = [["scenario", "case", "seed", "survival_base", "survival_cand", "survival_delta",
             "tracking_base", "tracking_cand", "proxy_base", "proxy_cand", "proxy_delta"]]
    for key in sorted(set(base["cases"]) & set(cand["cases"])):
        b, c = base["cases"][key], cand["cases"][key]
        bp, cp = b["proxy"], c["proxy"]
        survival_delta = (None if bp["survival_proxy"] is None or cp["survival_proxy"] is None
                          else cp["survival_proxy"] - bp["survival_proxy"])
        proxy_delta = (None if bp["scenario_proxy"] is None or cp["scenario_proxy"] is None
                       else cp["scenario_proxy"] - bp["scenario_proxy"])
        rows.append([b["scenario_id"], b["case_id"], str(b["seed"]),
                     _fmt(bp["survival_proxy"]), _fmt(cp["survival_proxy"]), _fmt(survival_delta),
                     _fmt(bp["tracking_proxy"]), _fmt(cp["tracking_proxy"]),
                     _fmt(bp["scenario_proxy"]), _fmt(cp["scenario_proxy"]), _fmt(proxy_delta)])
    return rows


def summary_rows(scenarios: list[list[str]]) -> list[list[str]]:
    """계획 §9-1 의 `B`(비G2 순이득)·`L`(G2 손실)과 그 둘을 묶는 사전등록 값."""
    body = [r for r in scenarios[1:] if r[6]]
    total_base = sum(float(r[4]) for r in body)
    total_cand = sum(float(r[5]) for r in body)
    loss_rows = [r for r in body if r[0] == LOSS_AXIS]
    gain = sum(float(r[6]) for r in body if r[0] != LOSS_AXIS)
    loss = -sum(float(r[6]) for r in loss_rows)
    weight = float(loss_rows[0][1]) if loss_rows else 0.0
    cap = MAX_FLAT_SCENARIO_PROXY_DROP * weight * POINTS
    return [["metric", "value", "note"],
            ["total_points_70_baseline", _fmt(total_base), "G-A033 stored arm; 69 cases"],
            ["total_points_70_candidate", _fmt(total_cand), "G-A043 harvest; 69 cases"],
            ["total_points_70_delta", _fmt(total_cand - total_base), "internal proxy; not an official score"],
            ["non_loss_axis_gain_70", _fmt(gain), f"plan section 9-1 B: every axis except {LOSS_AXIS}"],
            ["loss_axis_loss_70", _fmt(loss), f"plan section 9-1 L: {LOSS_AXIS} only; sign flipped to positive"],
            ["min_total_points_delta", _fmt(MIN_TOTAL_POINTS_DELTA), "preregistered c2"],
            ["flat_scenario_weighted_cap_70", _fmt(cap),
             f"preregistered c3: {MAX_FLAT_SCENARIO_PROXY_DROP} proxy x weight {weight} x {POINTS:.0f}"],
            ["required_gain_if_loss_at_cap_70", _fmt(MIN_TOTAL_POINTS_DELTA + cap),
             "B needed for c2 when L sits exactly on the c3 cap"]]


def tables() -> dict[str, list[list[str]]]:
    base, cand = policies()
    scenarios = scenario_rows(base, cand)
    return {"SCENARIO_SPLIT.csv": scenarios,
            "CASE_DELTAS.csv": case_rows(base, cand),
            "SUMMARY.csv": summary_rows(scenarios)}


def render(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="다시 만들지 않고 같은지만 본다")
    args = parser.parse_args(argv)
    built = tables()
    if args.check:
        stale = [name for name, rows in built.items()
                 if not (OUT / name).is_file() or (OUT / name).read_text(encoding="utf-8") != render(rows)]
        print("표가 원자료와 같다" if not stale else "낡았다 — 다시 만들어라: " + ", ".join(stale))
        return 1 if stale else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in built.items():
        (OUT / name).write_text(render(rows), encoding="utf-8", newline="\n")
        print(f"{OUT / name}  rows={len(rows) - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
