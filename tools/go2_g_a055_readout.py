#!/usr/bin/env python3
"""G-A055 case 판독 — 사전등록 upload/plan/GO2_G_A055_PLAN_20260928.md §4 를 그대로 읽는다 (2026-09-29).

채택(A033 대비, tools/verify_go2_basic_motion_harvest.py)과 가설 수(tools/go2_dial_hypothesis.py)와 별도로,
1순위 case 를 **A043 대비** 결과 전 고정 규칙으로 분류한다.  문턱은 사양 `preregistered.g_a055_case_readout` 에서만
읽는다 — 결과를 본 뒤 여기서 경계를 옮기지 않게 하기 위해서다.  채택·승급·다음 값을 판정하지 않는다.

case 점수 = 생존 × 추종 (tools/go2_axis_bottleneck.case_row 와 같은 식; 계단 min(추종, 완주율), 복합 회전 min(xy, yaw),
밀침 복귀 후 추종·직립 회복).  세 seed 의 최솟값을 비교한다.  낙상은 평가기 summary 의 자세 낙상 수(낙관=비관일 때만).

  험지 옆걸음  ≥ 24 NOT_SUPPORTED / 13~23 REDUCED_BELOW_TARGET(C 결과 병기) / ≤ 12 이고 C → SUPPORTED /
              ≤ 12 이지만 C 아님 → FALL_TARGET_MET_OVERALL_UNCONFIRMED
              C = case 점수 최소 > 0.5296 그리고 속도(3 seed 평균) ≥ 0.158 (운영상 하한)
  복합 우회전  ≤ 14 이고 S → TARGET_LEVEL / 15~28 이고 S → REDUCED_BELOW_TARGET /
              ≤ 28 이지만 S 아님 → FALLS_REDUCED_OVERALL_UNCONFIRMED / = 29 SAME_FALLS / ≥ 30 WORSE
              S = case 점수 최소 > 0.4358
  밀침 네 방향  방향마다: 낙상 ≤ A043 그리고 case 점수 최소 ≥ A043 − 0.02 → NO_WORSE, 아니면 WORSE
  공개만      험지 전진, 계단 10·15cm(낙상·case 점수·≥1단·≥2단) — 판정 없음
결손(요약 없음·로봇 수 모자람·낙상 판정 모호)은 그 case 만 MISSING 이다.

    python -B tools/go2_g_a055_readout.py --harvest workspace/_keep/go2_g_a055_a043_ang_vel_xy_m008
    python -B tools/go2_g_a055_readout.py --harvest <다른 arm> --no-verify     (판독기 자체 확인)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_axis_bottleneck as axis  # noqa: E402
import go2_climb_count as climb  # noqa: E402
import go2_dial_hypothesis as hypothesis  # noqa: E402

WORK_ID = "G-A055"
SEEDS = (101, 202, 303)
ROBOTS = 32
AXIS_OF = {"rough_lateral": "G3", "rough_forward": "G3", "combined_yaw_right": "G2", "stairs_10_down": "G5",
           "stairs_15_down": "G5", "push_pos_x": "G6", "push_neg_x": "G6", "push_pos_y": "G6", "push_neg_y": "G6"}
STEP_HEIGHT = {"stairs_10_down": 0.10, "stairs_15_down": 0.15}


def case_facts(harvest: Path, case: str, std: float) -> dict:
    falls, scores, speeds, ge1, ge2 = [], [], [], [], []
    for seed in SEEDS:
        d = hypothesis.cases_dir(harvest) / f"seed_{seed}" / case
        summary = d / "summary.json"
        f = hypothesis.posture_falls(summary, ROBOTS)
        if f is None:
            return {"state": "MISSING", "reason": f"seed {seed}: summary absent, robots != {ROBOTS} or ambiguous fall verdict"}
        data = json.loads(summary.read_text(encoding="utf-8"))
        row = axis.case_row(AXIS_OF[case], case, seed, data, std)
        if row["proxy"] is None:
            return {"state": "MISSING", "reason": f"seed {seed}: case score not computable"}
        falls.append(f)
        scores.append(row["proxy"])
        speeds.append(data.get("speed_xy_mean"))
        if case in STEP_HEIGHT:
            c = climb.count(d / "steps.csv", STEP_HEIGHT[case]) if (d / "steps.csv").is_file() else None
            ge1.append(None if c is None else int(c["ge1"]))
            ge2.append(None if c is None else int(c["ge2"]))
    out = {"state": "OK", "falls_per_seed": falls, "falls": sum(falls), "case_score_per_seed": [round(x, 5) for x in scores],
           "case_score_min": round(min(scores), 5),
           "speed_mean": None if any(v is None for v in speeds) else round(statistics.fmean(speeds), 5)}
    if case in STEP_HEIGHT:
        out["climb_ge1"] = None if None in ge1 else sum(ge1)
        out["climb_ge2"] = None if None in ge2 else sum(ge2)
    return out


def rough_verdict(f: dict, rule: dict) -> dict:
    if f["state"] != "OK":
        return {"verdict": "MISSING"}
    c = rule["condition_c"]
    score_ok = f["case_score_min"] > float(c["case_score_min_above"])
    speed_ok = f["speed_mean"] is not None and f["speed_mean"] >= float(c["speed_mean_at_least"])
    cond = score_ok and speed_ok
    n = f["falls"]
    if n >= int(rule["not_supported_at_least"]):
        v = "NOT_SUPPORTED"
    elif n > int(rule["supported_at_most"]):
        v = "REDUCED_BELOW_TARGET"
    else:
        v = "SUPPORTED" if cond else "FALL_TARGET_MET_OVERALL_UNCONFIRMED"
    return {"verdict": v, "condition_c": cond, "case_score_ok": score_ok, "speed_ok": speed_ok}


def yaw_verdict(f: dict, rule: dict) -> dict:
    if f["state"] != "OK":
        return {"verdict": "MISSING"}
    s = f["case_score_min"] > float(rule["condition_s"]["case_score_min_above"])
    n, base = f["falls"], int(rule["base_falls"])
    if n >= base + 1:
        v = "WORSE"
    elif n == base:
        v = "SAME_FALLS"
    elif not s:
        v = "FALLS_REDUCED_OVERALL_UNCONFIRMED"
    elif n <= int(rule["target_at_most"]):
        v = "TARGET_LEVEL"
    else:
        v = "REDUCED_BELOW_TARGET"
    return {"verdict": v, "condition_s": s}


def push_verdict(f: dict, case: str, rule: dict) -> dict:
    if f["state"] != "OK":
        return {"verdict": "MISSING"}
    base_f = int(rule["base_falls"][case])
    base_s = float(rule["base_case_score_min"][case])
    ok = f["falls"] <= base_f and f["case_score_min"] >= base_s - float(rule["score_margin"])
    return {"verdict": "NO_WORSE" if ok else "WORSE", "base_falls": base_f, "base_case_score_min": base_s}


def read(spec: dict, harvest: Path, verify: bool = True) -> dict:
    rule = spec["preregistered"]["g_a055_case_readout"]
    std = float(axis.registry()["score"]["tracking_proxy_std"])
    verified, reason = hypothesis.harvest_check(spec, harvest) if verify else (True, "not checked (--no-verify)")
    base_arm = ROOT / spec["comparison_arm"]["stored_arm"]
    out = {"work_id": spec["work_id"], "tier": "INTERNAL_CASE_READOUT", "effect": "candidate vs G-A043",
           "harvest": str(harvest), "harvest_check": {"verified": verified, "reason": reason},
           "adoption": "not judged here - tools/verify_go2_basic_motion_harvest.py", "cases": {}}
    cases = ["rough_lateral", "combined_yaw_right", *rule["push"]["base_falls"], *rule["disclosed"]]
    for case in cases:
        cand, base = case_facts(harvest, case, std), case_facts(base_arm, case, std)
        item = {"candidate": cand, "g_a043": base}
        if case == "rough_lateral":
            item.update(rough_verdict(cand, rule["rough_lateral"]))
        elif case == "combined_yaw_right":
            item.update(yaw_verdict(cand, rule["combined_yaw_right"]))
        elif case.startswith("push_"):
            item.update(push_verdict(cand, case, rule["push"]))
        else:
            item["verdict"] = "DISCLOSED_NOT_JUDGED" if cand["state"] == "OK" else "MISSING"
        if not verified:
            item["verdict"] = hypothesis.UNVERIFIED
        out["cases"][case] = item
    out["limits"] = ["one training seed (42)", "internal proxy, not an official score",
                     "not a cause analysis: the rule reads outcomes, not why G-A043 tilts",
                     "the 0.158 speed floor compares a three-seed mean with G-A043's lowest seed (operational floor)"]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", type=Path, required=True)
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    spec = hypothesis.load_spec(WORK_ID)
    result = read(spec, a.harvest, verify=not a.no_verify)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8", newline="\n")
    for case, item in result["cases"].items():
        c = item["candidate"]
        detail = "" if c["state"] != "OK" else f" falls {c['falls']} score_min {c['case_score_min']}"
        print(f"CASE {case}: {item['verdict']}{detail}")
    bad = [c for c, i in result["cases"].items() if i["verdict"] in ("MISSING", hypothesis.UNVERIFIED)]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
