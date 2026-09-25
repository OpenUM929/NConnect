#!/usr/bin/env python3
"""G-A043 사후 대조 — 기전 예측(`GO2_REWARD_MECHANISM_FORECAST.md`)이 실제와 맞았는가.

왜 있는가.  예측 문서 §8-8 은 "새 회차는 먼저 `HELD_OUT` 에 넣어 §9 에서 예측과 대조한다.  대조를
기록한 뒤에만 계수에 합친다" 고 적는다.  G-A038 하나만 그렇게 대조됐고 A041·A042·A043 은 회수된 뒤에도
대조되지 않았다.  계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md` §7 첫 줄이 요구하는 것이
"A043 held-out 대조 후 반영 · 이전예측/실측 구분" 이다.

무엇을 재는가.  `-1.5` 에서 계산된 네 상황의 부분 margin 변화(`PROBE_SITUATIONS.csv`)와, 같은 상황에
해당하는 평가 case 의 **실제** proxy 변화를 나란히 놓는다.  방향이 같은지만 본다 — 부분 margin 의
**크기**는 G-A038 에서 이미 틀린 것이 확인됐다(계단).  표는 판정이 아니다.

한계.  상황 ↔ case 대응은 우리가 정한 것이고(`SITUATION_CASES`), 예측은 G-A033 의 궤적을 고정한 보상
산수라 학습이 바꾼 행동을 담지 않는다.  한 회차·학습 seed 42 하나다.

    python -B tools/go2_a043_forecast_check.py            # 표를 만든다
    python -B tools/go2_a043_forecast_check.py --check     # 같은지만 본다
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))

OUT = QUAD / "reports" / "evidence" / "go2_g_a043_readout_20260922"
SPLIT = QUAD / "reports" / "evidence" / "go2_a043_scenario_split_20260922" / "CASE_DELTAS.csv"
SITUATIONS = QUAD / "reports" / "evidence" / "go2_reward_mechanism_20260917" / "PROBE_SITUATIONS.csv"
BASE_ARM = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
CAND_ARM = ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15/evaluation/candidate"
TERM, TO = "lin_vel_z_l2", "-1.5"
WORK, BASELINE_NAME = "G-A043", "G-A033"
# 상황 → 그 상황에 해당한다고 우리가 정한 평가 case.  기전 문서 §6-0 의 네 구간과 같은 이름이다.
SITUATION_CASES = (("walk", "forward_nominal"), ("climb", "stairs_10_down"), ("climb", "stairs_15_down"),
                   ("sway", "rough_lateral"), ("push", "push_pos_x"), ("push", "push_neg_x"),
                   ("push", "push_pos_y"), ("push", "push_neg_y"))
FLAT_CASE = ("G1", "forward_nominal", "101")
FLAT_FIELDS = ("survival_proxy", "tracking_proxy", "scenario_proxy", "tracking_xy_rmse",
               "speed_xy_mean", "height_rel_mean", "posture_falls", "terminated")


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def forecast_rows() -> list[list[str]]:
    deltas = _read(SPLIT)
    situations = {(r["term"], r["to"]): r for r in _read(SITUATIONS)}[(TERM, TO)]
    rows = [["zone", "forecast_partial_margin_delta", "target_group",
             "observed_mean_proxy_delta", "direction_agrees"]]
    for zone, case in SITUATION_CASES:
        cell = situations.get(f"{zone}_delta", "").strip()
        observed = [float(r["proxy_delta"]) for r in deltas if r["case"] == case and r["proxy_delta"]]
        if not cell or not observed:
            rows.append([zone, cell, case, "", ""])
            continue
        mean = sum(observed) / len(observed)
        rows.append([zone, cell, case, f"{mean:.6f}",
                     str(_sign(float(cell)) == _sign(mean))])
    return rows


def flat_rows() -> list[list[str]]:
    scenario, case, seed = FLAT_CASE
    rows = [["arm", "case", *FLAT_FIELDS]]
    sys.path.insert(0, str(QUAD))
    from go2_fixed_eval_report import _case_proxy  # noqa: E402  (평가 채점식과 한 곳에서 읽는다)
    for name, arm in ((BASELINE_NAME, BASE_ARM), (WORK, CAND_ARM)):
        summary = json.loads((arm / "cases" / f"seed_{seed}" / case / "summary.json").read_text(encoding="utf-8"))
        proxy = _case_proxy(case, summary)
        values = {"survival_proxy": proxy["survival_proxy"], "tracking_proxy": proxy["tracking_proxy"],
                  "scenario_proxy": proxy["scenario_proxy"], "tracking_xy_rmse": summary.get("tracking_xy_rmse"),
                  "speed_xy_mean": summary.get("speed_xy_mean"), "height_rel_mean": summary.get("height_rel_mean"),
                  "posture_falls": summary.get("posture_fall_env_count_pessimistic"),
                  "terminated": summary.get("terminated_env_count")}
        cells = []
        for field in FLAT_FIELDS:
            value = values[field]
            cells.append("" if value is None else
                         str(value) if isinstance(value, int) else f"{float(value):.6f}")
        rows.append([name, f"{scenario}:{case}:{seed}", *cells])
    return rows


def tables() -> dict[str, list[list[str]]]:
    return {"FORECAST_CHECK.csv": forecast_rows(), "FLAT_NOMINAL.csv": flat_rows()}


def render(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
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
