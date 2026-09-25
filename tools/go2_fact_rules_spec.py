"""`fact_rules_v1` 한도를 G-A033 원시 기록에서 계산해 증거 CSV와 사양에 적는다.

한도는 의도가 아니라 측정값이다(`tools/go2_eval_resolution.py`와 같은 이항 표집 원리, 하한).
  target_group_floor  묶음 평균 proxy 변화의 하한 = −2 × sqrt(Σ 2·t²·s(1−s)/n) / k
                      s = G-A033 생존(0.5/n ~ 1−0.5/n로 자름), t = 추종, n = 로봇 수, k = 묶음 case 수.
                      두 arm이 독립 표집이라 분산을 2배로 둔다.
  climb_guard         3 seed 오른 로봇 수 합의 하한 = 기준 합 − 2 × sqrt(Σ 2·n·p(1−p)), p = 기준 비율(같게 자름).
  보호 한도            `reports/runs/BASELINE_MARGIN.csv` delta_resample_sd × 2 (G-A037 이후와 같다).
학습 seed 흔들림은 들어 있지 않다 — 전 학습이 seed 42다(`GO2_NOW.md` §0).  그래서 이 한도는 **하한**이다.

    python -B tools/go2_fact_rules_spec.py                    # 증거 CSV 재생성
    python -B tools/go2_fact_rules_spec.py --write G-A035 G-A037   # 미실행 사양에 규칙 기록
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import go2_climb_count as climb  # noqa: E402
import go2_fact_rules as fact  # noqa: E402
from go2_fixed_eval_report import _case_proxy  # noqa: E402

BASE = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
MARGIN = QUAD / "reports/runs/BASELINE_MARGIN.csv"
REGISTRY = QUAD / "config/go2_self_eval_registry.json"
OUT = QUAD / "reports/evidence/go2_fact_rules_20260917"
SPEC_DIR = QUAD / "config/experiments"
# G-A042·G-A043 은 여기 없다.  두 사양은 이 모듈의 `rules_for` 로 한도를 계산하지만, 발화할 수
# 없는 계단 관문 하나(`stairs_15_climb_ge1`, 하한 −1.523)를 빼고 그 사실을 `climb_guard.omitted`
# 에 적는다(결함 S-2).  그래서 `--write` 로 덮어쓰면 죽은 관문이 되살아난다 — 등록하지 않는다.
SPECS = {"G-A035": "G_A035_a033_iter1500.json", "G-A037": "G_A037_a033_lin_vel_z_m1.json",
         "G-A038": "G_A038_a033_ang_vel_xy_m008.json"}
SEEDS = ("101", "202", "303")
# 분석 §8-4의 계단 지표: 15cm ≥1단, 10cm ≥2단.  10cm ≥1단은 G-A038 붕괴(한 단도 못 오름)를 직접 본다.
CLIMB_GROUPS = {
    "stairs_10_climb_ge1": ("stairs_10_down", "ge1"),
    "stairs_10_climb_ge2": ("stairs_10_down", "ge2"),
    "stairs_15_climb_ge1": ("stairs_15_down", "ge1"),
}
SCENARIO_OF = {"stairs_10_down": "G5", "stairs_15_down": "G5"}
SOURCE = ("reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md 8-3b (target G3 G5, guard G1 G2 G4 G6 G7) "
          "and 8-4 (stairs measured by climbed robots); gap found by reports/GO2_G_A038_READOUT.md section 4")


def clip(p: float, n: int) -> float:
    return min(max(p, 0.5 / n), 1.0 - 0.5 / n)


def std() -> float:
    return float(json.loads(REGISTRY.read_text(encoding="utf-8"))["score"].get("tracking_proxy_std", 0.5))


def case_stats(entry: str) -> dict:
    _, case_id, seed = entry.split(":")
    summary = json.loads((BASE / "cases" / f"seed_{seed}" / case_id / "summary.json").read_text(encoding="utf-8"))
    proxy = _case_proxy(case_id, summary, std())
    n = int(summary["posture_envs_observed"])
    s, t = float(proxy["survival_proxy"]), float(proxy["tracking_proxy"])
    var = 2.0 * t * t * clip(s, n) * (1.0 - clip(s, n)) / n
    return {"entry": entry, "n": n, "survival": s, "tracking": t, "proxy": float(proxy["scenario_proxy"]), "var": var}


def group_floor(entries: list[str]) -> tuple[float, list[dict]]:
    stats = [case_stats(e) for e in entries]
    return -2.0 * math.sqrt(sum(x["var"] for x in stats)) / len(stats), stats


def climb_group(case_id: str, metric: str) -> dict:
    entries = [f"{SCENARIO_OF[case_id]}:{case_id}:{seed}" for seed in SEEDS]
    counts, var = [], 0.0
    for seed in SEEDS:
        got = climb.count(BASE / "cases" / f"seed_{seed}" / case_id / "steps.csv", climb.STAIR_HEIGHTS[case_id])
        counts.append(got[metric])
        p = clip(got[metric] / got["robots"], got["robots"])
        var += 2.0 * got["robots"] * p * (1.0 - p)
    return {"entries": entries, "metric": metric, "baseline_counts": counts, "baseline_sum": sum(counts),
            "max_drop": round(2.0 * math.sqrt(var), 3)}


def guard_limits() -> dict[str, float]:
    with MARGIN.open(encoding="utf-8") as handle:
        sd = {r["scenario"]: float(r["value"]) for r in csv.DictReader(handle) if r["metric"] == "delta_resample_sd"}
    return {sid: round(2.0 * sd[sid], 5) for sid in ("G3", "G4", "G5", "G6", "G7")}


def rules_for(spec: dict) -> dict:
    groups = spec["preregistered"]["target_groups"]
    return {
        "rule_version": fact.RULE_VERSION,
        "rule_source": SOURCE,
        "target_axes": list(fact.TARGET_AXES),
        "guard_axes": list(fact.GUARD_AXES),
        "target_group_floor": {name: round(group_floor(entries)[0], 5) for name, entries in groups.items()},
        "climb_guard": {
            "counter": "tools/go2_climb_count.py (the rule of tools/go2_stairs_behavior.py STAIRS_CLIMB.csv)",
            # 2026-09-18 감사: 여기는 "G-A033 evaluation/candidate steps.csv" 라는 **설명문**이었다.
            # 사양 쪽은 test_14_every_path_in_a_spec_can_be_opened 요구대로 분석가가 그대로 열 수
            # 있는 glob 으로 고쳤는데 생성기를 따라 고치지 않아, test_5_unexecuted_specs_carry_the
            # _measured_rules 가 G-A035·G-A037 에서 2건 실패한 채로 남아 있었다.  경로는 BASE 에서
            # 만들어 두 곳이 갈라지지 않게 한다.
            "baseline": f"{BASE.relative_to(ROOT).as_posix()}/cases/seed_*/*/steps.csv",
            "groups": {name: climb_group(case_id, metric) for name, (case_id, metric) in CLIMB_GROUPS.items()},
        },
        "max_scenario_weighted_loss_70_by_scenario": guard_limits(),
    }


def evidence() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [["spec", "group", "case", "n", "survival", "tracking", "proxy", "floor"]]
    for work_id, name in SPECS.items():
        spec = json.loads((SPEC_DIR / name).read_text(encoding="utf-8"))
        for group, entries in spec["preregistered"]["target_groups"].items():
            floor, stats = group_floor(entries)
            for x in stats:
                rows.append([work_id, group, x["entry"], str(x["n"]), f"{x['survival']:.5f}",
                             f"{x['tracking']:.5f}", f"{x['proxy']:.5f}", f"{floor:.5f}"])
    with (OUT / "TARGET_GROUP_FLOOR.csv").open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    rows = [["group", "case", "metric", "count_101", "count_202", "count_303", "baseline_sum", "max_drop", "floor"]]
    for name, (case_id, metric) in CLIMB_GROUPS.items():
        g = climb_group(case_id, metric)
        rows.append([name, case_id, metric, *map(str, g["baseline_counts"]), str(g["baseline_sum"]),
                     f"{g['max_drop']:.3f}", f"{g['baseline_sum'] - g['max_drop']:.3f}"])
    with (OUT / "CLIMB_GUARD.csv").open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    print("wrote", OUT)


def block(value: dict, indent: int) -> str:
    """사양 파일 서식: 스칼라 배열은 한 줄, 나머지는 2칸 들여쓰기."""
    text = json.dumps(value, indent=2, ensure_ascii=False)
    text = re.sub(r"\[\n\s*([^\[\]{}]*?)\n\s*\]",
                  lambda m: "[" + ", ".join(x.strip().rstrip(",") for x in m.group(1).split("\n")) + "]", text)
    return text.replace("\n", "\n" + " " * indent)


def write_spec(work_id: str) -> None:
    """`preregistered` 블록만 바꿔 쓴다.  나머지 줄은 바이트 그대로 둔다."""
    path = SPEC_DIR / SPECS[work_id]
    text = path.read_text(encoding="utf-8")
    spec = json.loads(text)
    start = text.index('\n  "preregistered": {') + len('\n  "preregistered": ')
    depth, end = 0, start
    for end in range(start, len(text)):
        depth += {"{": 1, "}": -1}.get(text[end], 0)
        if depth == 0:
            break
    prereg = {**spec["preregistered"], **rules_for(spec)}
    new = text[:start] + block(prereg, 2) + text[end + 1:]
    if json.loads(new)["preregistered"] != prereg:
        raise RuntimeError("preregistered block rewrite does not round-trip")
    path.write_bytes(new.encode("utf-8"))   # LF as written, whatever the OS
    print("wrote", path.relative_to(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", nargs="*", default=[], choices=["G-A035", "G-A037"],
                        help="unexecuted specs only; G-A038 ran under the old rule and stays as it ran")
    args = parser.parse_args()
    evidence()
    for work_id in args.write:
        write_spec(work_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
