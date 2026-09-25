"""종합 §8 의 tier1 회귀를 아티팩트에서 재생성한다.

§8 은 §8-1 에서 이미 철회된 분석이다(표본 안 r² 를 예측력으로 인용했다).  그런데
표는 문서에 그대로 남아 있고, 숫자는 내가 손으로 옮겨 적은 것이었다.  철회한 분석일수록
숫자가 검증돼 있어야 한다 — 누군가 다시 인용할 때 근거가 있어야 하고, 인용하면 안 되는
이유도 같은 파일에서 나와야 한다.

출처는 각 회차의 `reports/TIER1_DECISION.json` 의 `candidate_minus_baseline_points_70`
이고, x 는 학습 로그의 `terrain@999` 다.  두 축이 다르다는 사실(7 case tier1 대 69 case
70점)은 §8 본문이 말한다.  여기서는 숫자만 만든다.

    python tools/go2_tier1_regression.py
"""
from __future__ import annotations

import csv
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from go2_run_ledger import harvest  # noqa: E402

KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/runs/TIER1_REGRESSION.csv"

# 문서가 쓰는 짧은 이름.
SHORT = {"go2_g_a015_pilot_feet_air_time_035": "A015",
         "go2_g_a016_pilot_ang_vel_xy_m015": "A016",
         "go2_g_a017_pilot_track_lin_vel_xy_140": "A017",
         "go2_g_a018_pilot_action_rate_m008": "A018"}


def points() -> list[dict[str, float | str]]:
    """(회차, terrain@999, tier1 Δ). 같은 기준선(Pilot-01)·같은 7 case 인 회차만."""
    curves = {}
    for record in harvest():
        curve = (record.get("training") or {}).get("curve") or {}
        if curve.get("999", {}).get("terrain") is not None:
            curves[record["run"]] = curve["999"]

    rows = []
    for run, short in SHORT.items():
        decision = KEEP / run / "reports/TIER1_DECISION.json"
        if not decision.is_file() or run not in curves:
            continue
        body = json.loads(decision.read_text(encoding="utf-8"))
        rows.append({"run": short,
                     "terrain_999": curves[run]["terrain"],
                     "curve": curves[run],
                     "delta_tier1": body["candidate_minus_baseline_points_70"]})
    return sorted(rows, key=lambda r: r["run"])


def fit(rows) -> tuple[float, float]:
    xs = [r["terrain_999"] for r in rows]
    ys = [r["delta_tier1"] for r in rows]
    mx, my = st.mean(xs), st.mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return my - slope * mx, slope


def pearson(rows) -> float:
    xs = [r["terrain_999"] for r in rows]
    ys = [r["delta_tier1"] for r in rows]
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den


def main() -> int:
    rows = points()
    if len(rows) < 3:
        print(f"회수된 tier1 회차가 {len(rows)}건이라 회귀를 세우지 않는다")
        return 1

    intercept, slope = fit(rows)
    r = pearson(rows)
    out = [["metric", "run", "value"]]
    for row in rows:
        pred = intercept + slope * row["terrain_999"]
        out += [["terrain_999", row["run"], f"{row['terrain_999']:.4f}"],
                ["delta_tier1", row["run"], f"{row['delta_tier1']:+.2f}"],
                ["insample_predicted", row["run"], f"{pred:+.2f}"],
                ["insample_residual", row["run"], f"{row['delta_tier1'] - pred:+.2f}"]]

    print(f"n={len(rows)}  r={r:+.3f}  r2={r * r:.3f}  기울기 {slope:+.2f}/레벨")
    out += [["pearson_r", "ALL", f"{r:+.3f}"],
            ["r_squared", "ALL", f"{r * r:.3f}"],
            ["slope_per_level", "ALL", f"{slope:+.2f}"]]

    # leave-one-out — §8-1 의 근거. 대조군은 '나머지의 평균으로 찍기'.
    errors, baseline = [], []
    print("\n== leave-one-out ==")
    for i, held in enumerate(rows):
        train = [r for j, r in enumerate(rows) if j != i]
        b, m = fit(train)
        pred = b + m * held["terrain_999"]
        error = held["delta_tier1"] - pred
        errors.append(abs(error))
        baseline.append(abs(held["delta_tier1"] - st.mean(r["delta_tier1"] for r in train)))
        print(f"  {held['run']}  실제 {held['delta_tier1']:+7.2f}  예측 {pred:+7.2f}  오차 {error:+7.2f}")
        out += [["loo_predicted", held["run"], f"{pred:+.2f}"],
                ["loo_error", held["run"], f"{error:+.2f}"]]

    print(f"  LOO MAE {st.mean(errors):.2f}   평균으로 찍기 {st.mean(baseline):.2f}")
    out += [["loo_mae", "ALL", f"{st.mean(errors):.2f}"],
            ["loo_mae_baseline", "ALL", f"{st.mean(baseline):.2f}"]]

    # 대안 예측변수. "terrain 이 그중 가장 낫다"는 §8-1 의 주장은 이 네 숫자의 비교이고,
    # 그 숫자를 만드는 코드가 없었다. terrain 이 대조군보다 나은 유일한 변수인지 여기서 본다.
    print("\n== 대안 예측변수 (LOO MAE) ==")
    for name in ("terrain", "track_lin_vel", "episode_length", "base_contact"):
        alt = [{"terrain_999": r["curve"][name], "delta_tier1": r["delta_tier1"]}
               for r in rows if r["curve"].get(name) is not None]
        if len(alt) < len(rows):
            print(f"  {name:16s} 회수 부족 ({len(alt)}/{len(rows)}) — 세우지 않는다")
            continue
        alt_errors = []
        for i, held in enumerate(alt):
            train = [r for j, r in enumerate(alt) if j != i]
            b, m = fit(train)
            alt_errors.append(abs(held["delta_tier1"] - (b + m * held["terrain_999"])))
        mae = st.mean(alt_errors)
        print(f"  {name:16s} {mae:6.2f}" + ("   ← 대조군보다 나쁘다" if mae > st.mean(baseline) else ""))
        out += [["alt_predictor_loo_mae", name, f"{mae:.2f}"]]

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(out)
    print(f"\n-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
