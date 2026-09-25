#!/usr/bin/env python3
"""총점 차이가 **생존에서 왔는지 추종에서 왔는지** 반사실로 가른다 — 생성 도구.

왜 필요한가.  회차 판독은 "총점이 내려갔다" 와 "낙상이 늘었다" 를 나란히 적고, 읽는 사람은 둘을
인과로 잇는다.  그러나 채점식은 시나리오마다 **case 최솟값의 `survival x tracking`** 이고
(`workspace/training/quadruped/go2_fixed_eval_report.py` `_case_proxy` · `build_policy`), 최솟값을
쥔 case 가 팔마다 다를 수 있어 **낙상이 늘어도 총점은 추종 때문에 움직였을 수** 있다.  그래서
설명을 붙이는 대신 같은 채점기로 두 번 더 채점한다:

  actual        후보 그대로
  survival_swap 후보의 추종 + **기준선의 생존**(같은 case·seed)
  tracking_swap 후보의 생존 + **기준선의 추종 인수 원자료**(rmse·진행·회복)

`actual - survival_swap` 은 생존 차이가 총점에 남긴 몫, `actual - tracking_swap` 은 추종 쪽 몫이다.
**교차항은 잔차로 정의한다**(`delta - from_survival - from_tracking`), 그래서 세 항의 합은 언제나
총점 차이와 같다 — 합이 맞는 것은 검증이 아니라 정의다.  읽을 것은 합이 아니라 **교차항의 크기**이고,
크기를 재는 분모를 **두 가지로 나눠 적는다**:

  interaction_share_pct            |교차항| / |순변화|      — G-A044 0.04% · G-A043 79.89%
  interaction_share_of_magnitude   |교차항| / (|생존|+|추종|+|교차항|)  — 0.03% · 30.75%

앞엣것은 **순변화 대비 잔차 비율**이다.  순변화가 작으면(큰 반대 몫들이 상쇄되면) 얼마든지 커지므로
**인과적 기여율도, 설명 실패율도 아니다** — 2026-09-24 검토 지적.  뒤엣것은 몫들의 절대 크기 합을
분모로 써서 그 불안정을 덜어 낸다.  두 수가 크게 벌어지면(G-A043: 79.89% 대 30.75%) 그 자체가
"상쇄가 심하다" 는 신호다(같은 회차의 |순변화|/크기합 = 38.49%).

**이것은 인과 증명이 아니다.**  고정된 채점식 안에서 "어느 인수를 통해 총점이 움직였는가" 를 세는
**산술적 기여 분해**일 뿐이고, "보상 변경이 낙상을 일으켰다" 는 명제는 여기서 나오지 않는다 —
그 질문은 같은 보상을 다른 학습 seed 로 반복해야 손댈 수 있다.

이 도구는 판정하지 않는다.  자기 검증은 한다: 재구현한 집계가 각 팔의 기록된 총점을 그대로
재현하지 못하면 아무것도 쓰지 않고 실패한다(이것은 **집계 재구현**의 검증이고, 위 분해의 검증이 아니다).

    python -B tools/go2_score_decomposition.py

출력 `reports/evidence/go2_seed_pair_20260924/SCORE_SPLIT.csv`.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
KEEP = ROOT / "workspace" / "_keep"
OUT = QUAD / "reports" / "evidence" / "go2_seed_pair_20260924"
REGISTRY = QUAD / "config" / "go2_self_eval_registry.json"
SCORES = QUAD / "reports" / "runs" / "SCENARIO_SCORES.csv"
sys.path.insert(0, str(QUAD))

from go2_fixed_eval_report import _case_proxy  # noqa: E402

BASELINE = "go2_g_a033_a017_track_lin_vel_xy_150"
ARMS = (
    ("G-A044", "go2_g_a044_a033_lin_vel_z_m175"),
    ("G-A043", "go2_g_a043_a033_lin_vel_z_m15"),
)
# 추종 인수를 만드는 원자료 칸.  생존은 `survival_proxy` 하나이고, 나머지는 전부 추종 쪽이다.
TRACKING_FIELDS = ("tracking_xy_rmse", "tracking_yaw_rmse", "projected_progress_m",
                   "post_push_tracking_xy_rmse", "recovery", "steps", "step_dt")


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def summaries(run: str) -> dict[tuple[str, str, int], dict]:
    """(scenario, case, seed) -> summary.json, 채점기가 기대하는 목록 그대로."""
    registry = load_registry()
    seeds = [int(seed) for seed in registry["score"]["internal_gates"]["required_evaluation_seeds"]]
    out: dict[tuple[str, str, int], dict] = {}
    for scenario in registry["scenarios"]:
        for case_id in scenario["internal_cases"]:
            wanted = ([int(case_id.rsplit("_", 1)[1])] if scenario["id"] == "G7" else seeds)
            for seed in wanted:
                path = (KEEP / run / "evaluation" / "candidate" / "cases"
                        / f"seed_{seed}" / case_id / "summary.json")
                if path.is_file():
                    out[(scenario["id"], case_id, seed)] = json.loads(path.read_text(encoding="utf-8"))
    return out


def total_70(cases: dict[tuple[str, str, int], dict]) -> float:
    """채점기의 집계를 그대로: 시나리오마다 case 최솟값의 곱, 가중합, x70."""
    registry = load_registry()
    std = float(registry["score"].get("tracking_proxy_std", 0.5))
    seeds = [int(seed) for seed in registry["score"]["internal_gates"]["required_evaluation_seeds"]]
    total = 0.0
    for scenario in registry["scenarios"]:
        required = (len(scenario["internal_cases"]) if scenario["id"] == "G7"
                    else len(scenario["internal_cases"]) * len(seeds))
        values = [_case_proxy(case_id, summary, std)["scenario_proxy"]
                  for (scenario_id, case_id, _seed), summary in cases.items()
                  if scenario_id == scenario["id"]]
        values = [value for value in values if value is not None]
        if len(values) != required:
            continue
        total += float(scenario["weight"]) * min(values)
    return total * 70.0


def swapped(candidate: dict, baseline: dict, take: str) -> dict:
    """한쪽 인수만 기준선 것으로 바꾼 case 표.  없는 짝은 후보 값을 그대로 둔다."""
    out = {}
    for key, summary in candidate.items():
        other = baseline.get(key)
        merged = dict(summary)
        if other is not None:
            if take == "survival":
                merged["survival_proxy"] = other.get("survival_proxy")
            else:
                for field in TRACKING_FIELDS:
                    if field in other:
                        merged[field] = other[field]
        out[key] = merged
    return out


def recorded_total(run: str) -> float:
    with SCORES.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["run"] == run and row["arm"] == "candidate":
                return float(row["total_70"])
    raise RuntimeError(f"{run} not in {SCORES.name}")


def main() -> int:
    base_cases = summaries(BASELINE)
    base_total = total_70(base_cases)
    # 자기 검증: 재구현이 기록된 총점을 재현하지 못하면 아무것도 쓰지 않는다.
    for run in (BASELINE, *(run for _work, run in ARMS)):
        cases = base_cases if run == BASELINE else summaries(run)
        got, want = total_70(cases), recorded_total(run)
        if abs(got - want) > 1e-4:
            raise RuntimeError(f"{run}: 재구현 총점 {got:.5f} != 기록 {want:.5f}")

    rows = [["arm", "run", "total_70", "baseline_total_70", "delta_70",
             "delta_from_survival_70", "delta_from_tracking_70", "interaction_70",
             "interaction_share_pct", "interaction_share_of_magnitude_pct",
             "net_change_share_of_magnitude_pct", "reads"]]
    for work_id, run in ARMS:
        cases = summaries(run)
        actual = total_70(cases)
        survival_swap = total_70(swapped(cases, base_cases, "survival"))
        tracking_swap = total_70(swapped(cases, base_cases, "tracking"))
        delta = actual - base_total
        from_survival = actual - survival_swap
        from_tracking = actual - tracking_swap
        interaction = delta - from_survival - from_tracking
        bigger = "survival" if abs(from_survival) > abs(from_tracking) else "tracking"
        share = abs(interaction) / abs(delta) * 100.0 if delta else float("nan")
        magnitude = abs(from_survival) + abs(from_tracking) + abs(interaction)
        share_mag = abs(interaction) / magnitude * 100.0 if magnitude else float("nan")
        net_mag = abs(delta) / magnitude * 100.0 if magnitude else float("nan")
        rows.append([work_id, run, f"{actual:.5f}", f"{base_total:.5f}", f"{delta:+.5f}",
                     f"{from_survival:+.5f}", f"{from_tracking:+.5f}", f"{interaction:+.5f}",
                     f"{share:.2f}", f"{share_mag:.2f}", f"{net_mag:.2f}",
                     f"arithmetic attribution inside a fixed scoring formula, not a cause: the "
                     f"larger single factor is {bigger}. The interaction is the residual, so the "
                     f"three parts always sum to delta_70 by construction. Its size is reported "
                     f"against two denominators because the first one is unstable: "
                     f"{share:.2f}% of the NET change and {share_mag:.2f}% of the summed "
                     f"magnitudes. The net-change ratio is neither a causal contribution nor an "
                     f"explanation-failure rate - when opposite factors cancel, the net change "
                     f"shrinks and the ratio blows up (net change is {net_mag:.2f}% of the summed "
                     f"magnitudes here)"])
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "SCORE_SPLIT.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    for row in rows[1:]:
        print("  ".join(row[:8]))
    print(f"-> {(OUT / 'SCORE_SPLIT.csv').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
