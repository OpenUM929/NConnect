#!/usr/bin/env python3
"""위험 축이 1단계에서 보이는가 — 저장된 기준선의 **최약 case** 와 1단계 목록을 대조한다.

왜 있는가.  2026-09-22 G-A043 은 `inference.risk_axes` 에 G2 를 적고, 1단계 23 case 에는 G2 에서
lateral 인 `left`·`right` 만 넣었다.  실제로 회차를 떨어뜨린 것은 G2 의 기준선 **최약 case** 인
`combined_yaw_right`(평가 seed 3개 전부, 생존 1.0 -> 0.72/0.72/0.66)였고, 1단계는 그 case 를 재지
않은 채 TARGET_PASS 를 냈다.  결함 `C-11`.

핵심은 이것이 **회차 전에 계산할 수 있었다**는 점이다.  저장된 A033 69 case 안에서 G2 의 최약 case 는
`combined_yaw_right`(생존x추종 0.8774)이고, 이 도구가 0.1 초에 읽는다.  사람의 주의력이 아니라 파일에서
읽으므로 다음 기획자도 같은 자리를 다시 놓치지 않는다.

1단계는 **표적 축**에서 만들어진다.  그래서 표적 축의 악화는 조기에 멎지만(G-A042 가 실제로 1단계에서
멎었다) 보호 축의 악화는 멎지 않는다.  이 도구는 그 비대칭을 보호 축 쪽에서 메운다.

한계 — 최약 case 는 '가장 먼저 무너질 자리'의 **대용**이지 증명이 아니다.  다른 case 가 먼저 무너질 수
있고, 그때 이 관문은 아무 말도 하지 않는다.  1단계 분기를 쓰지 않고 전수 69 를 걷는 회차에는 애초에
못 보는 자리가 없으므로 해당하지 않는다.

    python -B tools/go2_stage1_blind_spot.py --spec workspace/training/quadruped/config/experiments/<사양>.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
SPECS = QUAD / "config" / "experiments"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import verify_go2_basic_motion_harvest as verifier  # noqa: E402
import verify_go2_g_a030_harvest as a030  # noqa: E402
from go2_fixed_eval_report import build_policy  # noqa: E402


def uses_stage_1(spec: dict[str, Any]) -> bool:
    """1단계 비용절감 분기를 쓰는 회차인가.  전수 회차는 못 보는 자리가 없다."""
    return bool(spec.get("preregistered", {}).get("required_target_cases"))


def stored_arm(spec: dict[str, Any], root: Path = ROOT) -> Path:
    base = spec["baseline"]
    return root / base["stored_arm"] / "evaluation" / base["stored_label"]


def entry_name(case_key: str) -> str:
    """`G2/combined_yaw_right/seed_303` -> `G2:combined_yaw_right:303` (사양 표기)."""
    scenario, case_id, seed = case_key.split("/")
    return "%s:%s:%s" % (scenario, case_id, seed.replace("seed_", ""))


def weakest_case(policy: dict[str, Any], scenario: str) -> tuple[str, float] | None:
    """기준선에서 그 시나리오의 생존x추종이 가장 낮은 case.  동점은 이름 순으로 고정한다."""
    keys = sorted(key for key, row in policy["cases"].items() if row["scenario_id"] == scenario)
    if not keys:
        return None

    def score(key: str) -> float:
        proxy = policy["cases"][key]["proxy"]
        return proxy["survival_proxy"] * proxy["tracking_proxy"]

    best = min(keys, key=score)
    return best, score(best)


def read_spec(spec: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    """사양 하나를 읽어 위험 축별로 최약 case 와 1단계 포함 여부를 돌려준다."""
    arm = stored_arm(spec, root)
    if not arm.is_dir():
        return {"work_id": spec.get("work_id"), "stored_arm": str(arm), "readable": False,
                "uses_stage_1": uses_stage_1(spec), "axes": [], "blind": []}
    policy = build_policy(arm, a030.REGISTRY, None)
    stage_1 = set(verifier.target_stage_entries(spec))
    # 1단계가 어느 seed 를 골랐는지는 이 판정의 대상이 아니다 — 그 case 를 **재기는 하는가** 만 본다.
    measured_cases = {":".join(item.split(":")[:2]) for item in stage_1}
    axes, blind = [], []
    for axis in spec.get("inference", {}).get("risk_axes", []):
        found = weakest_case(policy, axis)
        if found is None:
            continue
        key, score = found
        name = entry_name(key)
        seen = ":".join(name.split(":")[:2]) in measured_cases
        axes.append({"axis": axis, "weakest_case": name, "baseline_score": score, "in_stage_1": seen})
        if not seen:
            blind.append(name)
    return {"work_id": spec.get("work_id"), "stored_arm": str(arm), "readable": True,
            "uses_stage_1": uses_stage_1(spec), "stage_1_entries": len(stage_1),
            "axes": axes, "blind": blind}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, help="사양 JSON.  생략하면 1단계를 쓰는 사양 전부")
    args = parser.parse_args()
    paths = [args.spec] if args.spec else sorted(SPECS.glob("*.json"))
    faults = 0
    for path in paths:
        spec = json.loads(path.read_text(encoding="utf-8"))
        if not args.spec and not uses_stage_1(spec):
            continue
        report = read_spec(spec)
        if not report["readable"]:
            print("%s  기준선 없음 %s" % (report["work_id"], report["stored_arm"]))
            continue
        for row in report["axes"]:
            print("%s  %s  최약 %s (%.4f)  1단계 %s"
                  % (report["work_id"], row["axis"], row["weakest_case"],
                     row["baseline_score"], "포함" if row["in_stage_1"] else "**빠짐**"))
        if report["uses_stage_1"] and report["blind"]:
            faults += 1
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
