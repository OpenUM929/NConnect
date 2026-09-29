#!/usr/bin/env python3
"""사후 대조 — 기전 예측(`GO2_REWARD_MECHANISM_FORECAST.md`)이 실제와 맞았는가 (G-A043 · G-A047 · G-A048).

왜 있는가.  예측 문서 §8-8 은 "새 회차는 먼저 `HELD_OUT` 에 넣어 §9 에서 예측과 대조한다.  대조를
기록한 뒤에만 계수에 합친다" 고 적는다.  G-A038 하나만 그렇게 대조됐고 A041·A042·A043 은 회수된 뒤에도
대조되지 않았다.  계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md` §7 첫 줄이 요구하는 것이
"A043 held-out 대조 후 반영 · 이전예측/실측 구분" 이다.
2026-09-26 (G-A047): 같은 대조를 `flat_orientation_l2 -0.5` 에 건다.  A047 은 case 별 차이 표가 따로
없어서 이 도구가 두 arm 의 summary.json 에서 직접 만든다(`CASE_PAIRS.csv`) — 낙상·속도·자세 높이까지
같은 case·같은 seed 로 나란히 둔다.  A043 의 표는 글자 하나 바뀌지 않는다.
2026-09-26 (G-A048): 같은 대조를 `lin_vel_z_l2 -1.25` 에 건다.  표 형식은 G-A047 과 같다(`CASE_PAIRS.csv`).

무엇을 재는가.  바꾼 값에서 계산된 네 상황의 부분 margin 변화(`PROBE_SITUATIONS.csv`)와, 같은 상황에
해당하는 평가 case 의 **실제** proxy 변화를 나란히 놓는다.  방향이 같은지만 본다 — 부분 margin 의
**크기**는 G-A038 에서 이미 틀린 것이 확인됐다(계단).  표는 판정이 아니다.

한계.  상황 ↔ case 대응은 우리가 정한 것이고(`SITUATION_CASES`), 예측은 G-A033 의 궤적을 고정한 보상
산수라 학습이 바꾼 행동을 담지 않는다.  부분 margin 은 보상 단위이고 관측은 평가 proxy 단위라, 같은 것은
방향뿐이다.  한 회차·학습 seed 42 하나다.

    python -B tools/go2_a043_forecast_check.py [--work G-A047]            # 표를 만든다
    python -B tools/go2_a043_forecast_check.py [--work G-A047] --check    # 같은지만 본다
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

SITUATIONS = QUAD / "reports" / "evidence" / "go2_reward_mechanism_20260917" / "PROBE_SITUATIONS.csv"
REGISTRY = QUAD / "config" / "go2_self_eval_registry.json"
BASE_ARM = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
BASELINE_NAME = "G-A033"
SEEDS = ("101", "202", "303")
# 회차 → (출력 폴더, case 차이 표, 후보 arm, 바꾼 항, 값).  case 차이 표가 None 이면 이 도구가 만든다.
WORKS = {
    "G-A043": (QUAD / "reports" / "evidence" / "go2_g_a043_readout_20260922",
               QUAD / "reports" / "evidence" / "go2_a043_scenario_split_20260922" / "CASE_DELTAS.csv",
               ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15/evaluation/candidate",
               "lin_vel_z_l2", "-1.5"),
    "G-A047": (QUAD / "reports" / "evidence" / "go2_g_a047_readout_20260926",
               None,
               ROOT / "workspace/_keep/go2_g_a047_a033_flat_orientation_m05/evaluation/candidate",
               "flat_orientation_l2", "-0.5"),
    "G-A048": (QUAD / "reports" / "evidence" / "go2_g_a048_readout_20260926",
               None,
               ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/evaluation/candidate",
               "lin_vel_z_l2", "-1.25"),
}
DEFAULT_WORK = "G-A043"
# 상황 → 그 상황에 해당한다고 우리가 정한 평가 case.  기전 문서 §6-0 의 네 구간과 같은 이름이다.
SITUATION_CASES = (("walk", "forward_nominal"), ("climb", "stairs_10_down"), ("climb", "stairs_15_down"),
                   ("sway", "rough_lateral"), ("push", "push_pos_x"), ("push", "push_neg_x"),
                   ("push", "push_pos_y"), ("push", "push_neg_y"))
FLAT_CASE = ("G1", "forward_nominal", "101")
FLAT_FIELDS = ("survival_proxy", "tracking_proxy", "scenario_proxy", "tracking_xy_rmse",
               "speed_xy_mean", "height_rel_mean", "posture_falls", "terminated")
DELTA_HEAD = ("scenario", "case", "seed", "survival_base", "survival_cand", "survival_delta",
              "tracking_base", "tracking_cand", "proxy_base", "proxy_cand", "proxy_delta",
              "posture_falls_base", "posture_falls_cand", "speed_base", "speed_cand",
              "height_p10_base", "height_p10_cand")


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def _case_proxy():
    sys.path.insert(0, str(QUAD))
    from go2_fixed_eval_report import _case_proxy as proxy  # noqa: E402  (평가 채점식과 한 곳에서 읽는다)
    return proxy


def case_delta_rows(cand_arm: Path) -> list[list[str]]:
    """두 arm 의 69 case 를 같은 case·seed 로 나란히.  G7 은 case 이름이 곧 seed 라 seed 하나만 있다."""
    proxy = _case_proxy()
    std = float(json.loads(REGISTRY.read_text(encoding="utf-8"))["score"].get("tracking_proxy_std", 0.5))
    rows = [list(DELTA_HEAD)]
    for scenario in json.loads(REGISTRY.read_text(encoding="utf-8"))["scenarios"]:
        for case in scenario["internal_cases"]:
            seeds = [case.rsplit("_", 1)[1]] if scenario["id"] == "G7" else list(SEEDS)
            for seed in seeds:
                pair = []
                for arm in (BASE_ARM, cand_arm):
                    summary = json.loads((arm / "cases" / f"seed_{seed}" / case / "summary.json")
                                         .read_text(encoding="utf-8"))
                    pair.append((proxy(case, summary, std), summary))
                (pb, sb), (pc, sc) = pair

                def f(value) -> str:
                    return "" if value is None else f"{float(value):.5f}"

                def d(a, b) -> str:
                    return "" if a is None or b is None else f"{float(b) - float(a):.5f}"

                rows.append([scenario["id"], case, seed,
                             f(pb["survival_proxy"]), f(pc["survival_proxy"]),
                             d(pb["survival_proxy"], pc["survival_proxy"]),
                             f(pb["tracking_proxy"]), f(pc["tracking_proxy"]),
                             f(pb["scenario_proxy"]), f(pc["scenario_proxy"]),
                             d(pb["scenario_proxy"], pc["scenario_proxy"]),
                             str(sb.get("posture_fall_env_count_pessimistic")),
                             str(sc.get("posture_fall_env_count_pessimistic")),
                             f(sb.get("speed_xy_mean")), f(sc.get("speed_xy_mean")),
                             f(sb.get("height_rel_p10")), f(sc.get("height_rel_p10"))])
    return rows


def _as_dicts(rows: list[list[str]]) -> list[dict[str, str]]:
    head, *body = rows
    return [dict(zip(head, row)) for row in body]


def forecast_rows(work: str, deltas: list[dict[str, str]]) -> list[list[str]]:
    _out, _split, _cand, term, to = WORKS[work]
    situations = {(r["term"], r["to"]): r for r in _read(SITUATIONS)}[(term, to)]
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


def flat_rows(work: str) -> list[list[str]]:
    _out, _split, cand_arm, _term, _to = WORKS[work]
    scenario, case, seed = FLAT_CASE
    rows = [["arm", "case", *FLAT_FIELDS]]
    proxy = _case_proxy()
    for name, arm in ((BASELINE_NAME, BASE_ARM), (work, cand_arm)):
        summary = json.loads((arm / "cases" / f"seed_{seed}" / case / "summary.json").read_text(encoding="utf-8"))
        values_proxy = proxy(case, summary)
        values = {"survival_proxy": values_proxy["survival_proxy"], "tracking_proxy": values_proxy["tracking_proxy"],
                  "scenario_proxy": values_proxy["scenario_proxy"], "tracking_xy_rmse": summary.get("tracking_xy_rmse"),
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


# 사전등록 1차 판독(사양 `required_records.fall_channel_split`): 자세 낙상 판정이 기울기 채널과 높이 채널 중
# 어디서 났는가.  G-A038 재판독 도구의 재생 규칙(`tools/go2_a038_reread.py` fall_channel_attribution)을
# 그대로 쓰고, 그 도구의 arm 이름표만 잠시 이 회차로 바꾼다 — 규칙을 두 벌 두지 않는다.
CHANNEL_CASES = ("rough_lateral", "rough_forward", "stairs_10_down", "slope_plus_20")
CHANNEL_FIELDS = ("arm", "seed", "case", "n_envs", "envs_fall_height_only", "envs_fall_tilt_only",
                  "envs_fall_both_channels", "envs_fall_either")


def channel_rows(work: str, cand_root: Path) -> list[list[str]]:
    import go2_a038_reread as reread  # noqa: E402
    saved = dict(reread.ARMS)
    reread.ARMS["A038"] = cand_root
    try:
        rolled = [row for case in CHANNEL_CASES
                  for row in reread.channel_rollup(reread.fall_channel_attribution(case))]
    finally:
        reread.ARMS.clear()
        reread.ARMS.update(saved)
    label = {"A033": BASELINE_NAME, "A038": work}
    rows = [list(CHANNEL_FIELDS)]
    for r in rolled:
        rows.append([label[r["arm"]], *[str(r[k]) for k in CHANNEL_FIELDS[1:]]])
    return rows


def tables(work: str = DEFAULT_WORK) -> dict[str, list[list[str]]]:
    _out, split, cand_arm, _term, _to = WORKS[work]
    built: dict[str, list[list[str]]] = {}
    if split is None:
        # 이름은 다른 증거 폴더와 겹치지 않게 한다 — 발행된 사양이 파일 이름만으로 인용하는 표가 있다
        # (G-A044 `CASE_DELTAS.csv`, G-A047 `FALL_CHANNEL_ROLLUP.csv`).  관문 test_go2_detectability_gate test_14.
        built["CASE_PAIRS.csv"] = case_delta_rows(cand_arm)
        built["FALL_CHANNELS.csv"] = channel_rows(work, cand_arm.parents[1])
        deltas = _as_dicts(built["CASE_PAIRS.csv"])
    else:
        deltas = _read(split)
    built["FORECAST_CHECK.csv"] = forecast_rows(work, deltas)
    built["FLAT_NOMINAL.csv"] = flat_rows(work)
    return built


def render(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--work", choices=sorted(WORKS), default=DEFAULT_WORK)
    args = parser.parse_args(argv)
    out = WORKS[args.work][0]
    built = tables(args.work)
    if args.check:
        stale = [name for name, rows in built.items()
                 if not (out / name).is_file() or (out / name).read_text(encoding="utf-8") != render(rows)]
        print("표가 원자료와 같다" if not stale else "낡았다 — 다시 만들어라: " + ", ".join(stale))
        return 1 if stale else 0
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in built.items():
        (out / name).write_text(render(rows), encoding="utf-8", newline="\n")
        print(f"{out / name}  rows={len(rows) - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
