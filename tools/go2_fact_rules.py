"""Go2 사실 기반 판정 규칙 `fact_rules_v1` — 서버 게이트와 로컬 검증기가 함께 쓴다 (표준 라이브러리만).

왜 있는가 (2026-09-17).  분석이 정한 판정(`reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md` §8-3b·§8-4)과
사양·게이트에 실제로 들어간 판정이 달랐다.
  - 분석: 목표 축은 G3·G5, 보호 축은 G1·G2·G4·G6·G7(각각 평가 표집 sd 2배), 계단은 **오른 로봇 수**로 잰다.
  - 구현: 표적 9 case의 **평균** proxy 하나, 보호 한도를 G3·G5에도 똑같이 걸고, 오른 로봇 수는 "기록만"이었다.
G-A038은 10cm 오르기가 32/32대 정지로 무너졌는데도 1단계를 통과했다(평균 +0.088, `GO2_G_A038_READOUT.md` §4).
G5 점수는 이미 0 근처라 더 떨어질 곳이 없어 보호 한도도 잡지 못했다.  이 모듈이 그 빈틈을 닫는다.

사양 `preregistered.rule_version == "fact_rules_v1"`일 때만 켜진다.  그 전 사양의 판정은 그대로 읽힌다.
한도 수치는 사양에 적힌 **측정값**이다(`tools/go2_fact_rules_spec.py`가 G-A033 원시 기록에서 계산해 적는다).
  target_group_floor   표적 묶음마다 평균 proxy 변화의 하한.  평균이 개별 붕괴를 덮지 못하게 한다.
  climb_guard          계단 오르기 case의 오른 로봇 수(3 seed 합)의 하한.  G5 점수가 못 보는 붕괴를 잡는다.
  target_axes          G3·G5.  전체 단계에서 두 축의 가중 점수 합이 올라야 채택한다(분석 §8-3b 5항).
  guard_axes           G1·G2·G4·G6·G7.  한도 표(`max_scenario_weighted_loss_70_by_scenario`)는 이 축만 가진다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

import go2_climb_count as climb

RULE_VERSION = "fact_rules_v1"
TARGET_AXES = ("G3", "G5")
GUARD_AXES = ("G1", "G2", "G4", "G6", "G7")
TOL = 1e-9


def active(prereg: dict[str, Any]) -> bool:
    return prereg.get("rule_version") == RULE_VERSION


def group_floor_violations(groups: Iterable[dict[str, Any]], prereg: dict[str, Any]) -> list[str]:
    """표적 묶음마다 평균 proxy 변화가 사양의 하한 아래면 위반이다."""
    floors = prereg["target_group_floor"]
    out = []
    for group in groups:
        floor = float(floors[group["group"]])
        if group["mean_delta"] is None or group["mean_delta"] < floor - TOL:
            out.append("%s mean proxy %+.5f < floor %+.5f" % (group["group"], group["mean_delta"] or 0.0, floor))
    return out


def climb_reading(case_dir: Callable[[str], Path], prereg: dict[str, Any],
                  available: set[str] | None = None) -> dict[str, Any]:
    """오른 로봇 수 관문.  `available`이 주어지면 그 안에 case가 모두 있는 묶음만 본다(1단계)."""
    rows, violations, deferred, inoperable_groups = [], [], [], []
    for name, group in prereg["climb_guard"]["groups"].items():
        entries = group["entries"]
        if available is not None and not set(entries) <= available:
            deferred.append(name)
            continue
        counts = []
        for entry in entries:
            _, case_id, _ = entry.split(":")
            steps = case_dir(entry) / "steps.csv"
            got = climb.count(steps, climb.STAIR_HEIGHTS[case_id]) if steps.is_file() else None
            counts.append(None if got is None else got[group["metric"]])
        if None in counts:
            violations.append("%s unreadable" % name)
            continue
        total = sum(counts)
        floor = float(group["baseline_sum"]) - float(group["max_drop"])
        # 하한이 0 이하이면 이 관문은 **발화할 수 없다** — 오른 로봇 수는 음수가 될 수 없으므로
        # 어떤 결과도 `total >= floor` 를 만족한다.  0 으로 클램프해도 마찬가지다.  잡음(max_drop)
        # 이 신호(baseline_sum)보다 커서 감소를 검출할 수 없다는 뜻이고, 그것은 통과가 아니라
        # **작동 불능**이다.  2026-09-19 결함 S-2: stairs_15_climb_ge1 이 4 - 5.523 = -1.523 로
        # 발화 불가였는데 조용히 통과하고 있었고, 사양은 그것을 주된 반증 조건이라고 적었다.
        inoperable = floor <= 0.0
        ok = None if inoperable else total >= floor - TOL
        rows.append({"group": name, "metric": group["metric"], "counts": counts, "total": total,
                     "baseline_counts": group["baseline_counts"], "baseline_sum": group["baseline_sum"],
                     "floor": floor, "ok": ok, "inoperable": inoperable})
        if inoperable:
            inoperable_groups.append(name)
            violations.append("%s %s guard inoperable: floor %.3f <= 0 (baseline %d, max_drop %s) "
                              "— 표본이 적어 감소를 검출할 수 없다" % (
                                  name, group["metric"], floor, group["baseline_sum"], group["max_drop"]))
        elif not ok:
            violations.append("%s %s %d < floor %.3f (baseline %d)" % (
                name, group["metric"], total, floor, group["baseline_sum"]))
    return {"groups": rows, "violations": violations, "deferred_to_full_stage": deferred,
            "inoperable_guards": inoperable_groups}


def target_axes_reading(base: dict[str, Any], cand: dict[str, Any], prereg: dict[str, Any]) -> dict[str, Any]:
    """전체 단계: 목표 축(G3·G5) 가중 점수 합의 변화.  올라야 채택한다."""
    rows = {}
    for sid in prereg["target_axes"]:
        b, c = base["scenarios"][sid], cand["scenarios"][sid]
        rows[sid] = (c["scenario_proxy"] - b["scenario_proxy"]) * float(b["weight"]) * 70.0
    delta = sum(rows.values())
    return {"by_axis_70": rows, "delta_70": delta, "rises": delta > TOL}
