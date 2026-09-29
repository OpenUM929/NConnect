#!/usr/bin/env python3
"""보호 설계 비교 — 현재 기준과 대안 두 개 (2026-09-26, D2 다음 단계).

외부 검토(2026-09-26)가 정한 범위:
  - 현재 기준(`post_a043_push4_v1` 보호 22검사, 여유 0)을 비교 대상으로 유지하고, 대안은 **최대 두 개**.
  - 먼저 **허용할 손실**과 **놓치면 안 되는 악화**를 정의한다.
  - 같은 경험분포에서의 탈락 빈도(거짓 실패)와, 정해진 악화가 있는 조건에서 그것을 **놓치는** 빈도를 함께 센다.
  - G-A048 이 통과하도록 허용치를 역산하지 않는다.  **새 설계는 G-A048 에 적용하지 않는다** — 판정은 보존된다.
  - 새 기준은 향후 실험용으로 사전등록 대상이며, 이 도구는 비교만 한다(screening 코드는 바꾸지 않는다).

정의(계산 전에 고정, 근거는 판독 문서 §1):
  놓치면 안 되는 악화 H   보호 case 하나에서 seed 마다 자세 낙상 +3대(pooled +9/96, 생존 −3/32),
                          또는 추종 proxy −0.02(seed 마다).
  허용할 손실 L           H 의 절반을 내림: seed 마다 낙상 +1대(pooled +3, 생존 −1/32), 추종 −0.01.

설계:
  current   여유 0 — pooled 낙상 ≤ 기준선, 생존·추종 seed 차이 중앙값 ≥ 0 (screening 과 같은 식)
  margin    같은 22검사에 허용 손실 L 만큼 여유: pooled 낙상 ≤ 기준선 + 3, 생존 중앙값 ≥ −1/32, 추종 중앙값 ≥ −0.01
  margin_split  (2026-09-26 사용자 선택) margin 과 같되, 잡음이 큰 세 칸만 악화·허용 손실을 따로 둔다.
            10cm 오르기·험지 옆걸음의 낙상·생존: H = seed 마다 +5대(pooled +15), L = seed 마다 +2대(pooled +6,
            생존 중앙값 −2/32).  험지 전진 추종: H = −0.04, L = −0.02.  나머지는 margin 과 같다.  계산 전에 고정했다.
  resample  검사마다 한쪽 1% 재표집 문턱: 별도 난수로 뽑은 기준선 재표집 분포에서 나쁜 쪽 1% 값보다 나쁘면 실패
            (문턱 보정용 표본과 평가용 표본의 난수를 나눠 낙관 편향을 막는다)

세는 것:
  null_any_fail      같은 경험분포 후보에서 보호 검사가 하나 이상 실패하는 비율(거짓 실패 쪽)
  harm_case_miss     악화를 넣은 case 의 검사가 **하나도** 실패하지 않은 비율(놓침 쪽) — case 마다
  harm_any_fail      악화 조건에서 전체 보호 묶음이 실패한 비율(참고: current 는 null 에서도 거의 항상 실패한다)

한계: 저장된 G-A033 표본에 조건부인 재표집이다.  악화는 case 값에 직접 더한 모형이고(로봇 궤적을 새로 만들지
않는다), 서버 재실행·학습 재실행 흔들림은 담지 않는다.

    python -B tools/go2_guard_design_compare.py [--draws 2000 --harm-draws 500]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_guard_resampling as rs  # noqa: E402

OUT = rs.QUAD / "reports/evidence/go2_guard_design_20260926"
SEEDS = rs.SEEDS
H_FALLS_PER_SEED = 3
H_TRACK = 0.02
L_FALLS_POOLED = 3          # floor(H/2) per seed x 3 seeds
L_SURVIVAL = -1 / 32
L_TRACK = -0.01
CALIBRATION_SEED, NULL_SEED, HARM_SEED = 20260927, 20260928, 20260929
# margin_split 의 잡음 큰 칸(사용자 선택 2026-09-26, 계산 전 고정)
SPLIT_FALL_CASES = ("stairs_10_down", "rough_lateral")
SPLIT_H_FALLS_PER_SEED, SPLIT_L_FALLS_POOLED, SPLIT_L_SURVIVAL = 5, 6, -2 / 32
SPLIT_TRACK_CASES = ("rough_forward",)
SPLIT_H_TRACK, SPLIT_L_TRACK = 0.04, -0.02


def harm_size(case_id: str, kind: str, design: str) -> float:
    """그 설계가 '놓치면 안 된다'고 정의한 악화 크기(낙상은 seed 당 대수, 추종은 proxy 감소)."""
    if design == "margin_split":
        if kind == "falls" and case_id in SPLIT_FALL_CASES:
            return SPLIT_H_FALLS_PER_SEED
        if kind == "tracking" and case_id in SPLIT_TRACK_CASES:
            return SPLIT_H_TRACK
    return H_FALLS_PER_SEED if kind == "falls" else H_TRACK


def draw(base_stats: dict, std: float, rng: random.Random) -> dict:
    return {k: rs.metrics(k[0], [envs[rng.randrange(len(envs))] for _ in envs], std)
            for k, envs in base_stats.items()}


def harm(cand: dict, case_id: str, kind: str, size: float) -> dict:
    out = {k: dict(v) for k, v in cand.items()}
    for seed in SEEDS:
        cell = out[(case_id, seed)]
        if kind == "falls":
            added = min(int(size), 32 - cell["posture_falls"])
            cell["posture_falls"] += added
            cell["survival"] -= added / 32
        else:
            cell["tracking"] -= size
    return out


def check_fail(name: str, stat: float, design: str, cut: dict[str, float]) -> bool:
    falls = "posture falls" in name
    if design == "current":
        return stat > 0 if falls else stat < 0
    if design == "margin":
        if falls:
            return stat > L_FALLS_POOLED
        return stat < (L_SURVIVAL if "survival" in name else L_TRACK)
    if design == "margin_split_dedup":
        # (2026-09-26 사용자 선택) 생존은 같은 로봇 낙상에서 나온 값이라 낙상 검사와 한 번을 두 번 센다.
        # case 마다 낙상 검사 하나만 남긴다(22 → 14검사).  값은 margin_split 그대로다.
        if "survival" in name:
            return False
        return check_fail(name, stat, "margin_split", cut)
    if design == "margin_split":
        case_id = name.split(" ")[0]
        if case_id in SPLIT_FALL_CASES and ("posture falls" in name or "survival" in name):
            return stat > SPLIT_L_FALLS_POOLED if falls else stat < SPLIT_L_SURVIVAL
        if case_id in SPLIT_TRACK_CASES and "tracking" in name:
            return stat < SPLIT_L_TRACK
        return check_fail(name, stat, "margin", cut)
    return stat > cut[name] if falls else stat < cut[name]


def verdict(stats: dict[str, float], design: str, cut: dict[str, float]) -> list[str]:
    return [n for n, s in stats.items() if check_fail(n, s, design, cut)]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--harm-draws", type=int, default=500)
    args = parser.parse_args(argv)
    base_stats, std = rs.load(rs.BASE_ARM)
    faults = rs.validate(rs.BASE_ARM, base_stats, std)
    if faults:
        print("RECOUNT MISMATCH", faults[:5])
        return 1
    base = {k: rs.metrics(k[0], v, std) for k, v in base_stats.items()}
    names = list(rs.guard_statistics(base, base))

    # resample 설계의 문턱 — 보정 전용 난수
    rng = random.Random(CALIBRATION_SEED)
    calib = {n: [] for n in names}
    for _ in range(args.draws):
        for n, s in rs.guard_statistics(base, draw(base_stats, std, rng)).items():
            calib[n].append(s)
    cut = {}
    for n, values in calib.items():
        values.sort()
        k = int(0.01 * len(values))
        cut[n] = values[len(values) - 1 - k] if "posture falls" in n else values[k]

    designs = ("current", "margin", "margin_split", "margin_split_dedup", "resample")
    rng = random.Random(NULL_SEED)
    null_any = {d: 0 for d in designs}
    null_check = {d: {n: 0 for n in names} for d in designs}
    for _ in range(args.draws):
        stats = rs.guard_statistics(base, draw(base_stats, std, rng))
        for d in designs:
            bad = verdict(stats, d, cut)
            null_any[d] += bool(bad)
            for n in bad:
                null_check[d][n] += 1

    scenarios = [(c, "falls") for c in rs.CASES] + [(c, "tracking") for c in rs.TRACKED]
    rng = random.Random(HARM_SEED)
    rows = []
    # 악화 크기 둘: 모든 설계에 같은 공통 H, 그리고 margin_split 이 자기 정의로 쓰는 H(세 칸만 다르다).
    for case_id, kind in scenarios:
        common = H_FALLS_PER_SEED if kind == "falls" else H_TRACK
        own = harm_size(case_id, kind, "margin_split")
        cells = [(d, "common", common) for d in designs] + [("margin_split", "own", own),
                                                            ("margin_split_dedup", "own", own)]
        miss = {c[:2]: 0 for c in cells}
        any_fail = {c[:2]: 0 for c in cells}
        for _ in range(args.harm_draws):
            drawn = draw(base_stats, std, rng)
            for d, label, size in cells:
                bad = verdict(rs.guard_statistics(base, harm(drawn, case_id, kind, size)), d, cut)
                any_fail[(d, label)] += bool(bad)
                if not any(n.startswith(case_id + " ") for n in bad):
                    miss[(d, label)] += 1
        for d, label, size in cells:
            rows.append({"harm_case": case_id, "harm_kind": kind, "design": d, "harm_size": label,
                         "harm_value": size,
                         "harm_case_miss": round(miss[(d, label)] / args.harm_draws, 4),
                         "harm_any_fail": round(any_fail[(d, label)] / args.harm_draws, 4)})

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "HARM_DETECTION.csv").open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with (OUT / "NULL_CHECK_FAIL.csv").open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["check", *[f"{d}_fail_rate" for d in designs], "resample_cut"])
        for n in names:
            w.writerow([n, *[f"{null_check[d][n] / args.draws:.4f}" for d in designs], f"{cut[n]:.5f}"])
    summary = {
        "definitions_fixed_before_computing": {
            "must_not_miss_harm": f"one guard case: +{H_FALLS_PER_SEED} posture falls per evaluation seed "
                                  f"(pooled +{3 * H_FALLS_PER_SEED}/96, survival -{H_FALLS_PER_SEED}/32), "
                                  f"or tracking proxy -{H_TRACK} per seed",
            "allowed_loss": f"half of the harm, rounded down: pooled falls +{L_FALLS_POOLED}, survival median "
                            f"{L_SURVIVAL:.5f}, tracking median {L_TRACK}",
        },
        "designs": {"current": "zero margin (post_a043_push4_v1 guard block)",
                    "margin": "allowed-loss margin on the same 22 checks",
                    "margin_split": "margin, with separate harm/allowed loss for stairs_10_down and rough_lateral "
                                    "falls/survival (+5/seed harm, +2/seed allowed) and rough_forward tracking "
                                    "(-0.04 harm, -0.02 allowed); user choice 2026-09-26, fixed before computing",
                    "margin_split_dedup": "margin_split with the eight survival checks removed (they re-count the "
                                          "same robot falls); 14 checks; same values; user choice 2026-09-26",
                    "resample": "one-sided 1% per-check cut from a separate calibration resample"},
        "not_applied_to": "G-A048 (its verdict INTERNAL_GATE_FAIL is preserved; no design here is evaluated on it)",
        "draws": args.draws, "harm_draws_per_scenario": args.harm_draws,
        "rng_seeds": {"calibration": CALIBRATION_SEED, "null": NULL_SEED, "harm": HARM_SEED},
        "null_any_guard_fail": {d: null_any[d] / args.draws for d in designs},
        "harm_case_miss_mean_common_harm": {
            d: round(sum(r["harm_case_miss"] for r in rows if r["design"] == d and r["harm_size"] == "common")
                     / len(scenarios), 4) for d in designs},
        "harm_case_miss_worst_common_harm": {
            d: max((r["harm_case_miss"], r["harm_case"] + "/" + r["harm_kind"])
                   for r in rows if r["design"] == d and r["harm_size"] == "common") for d in designs},
        "own_harm": {
            d: {"miss_mean": round(sum(r["harm_case_miss"] for r in rows
                                       if r["harm_size"] == "own" and r["design"] == d) / len(scenarios), 4),
                "miss_worst": max((r["harm_case_miss"], r["harm_case"] + "/" + r["harm_kind"])
                                  for r in rows if r["harm_size"] == "own" and r["design"] == d)}
            for d in ("margin_split", "margin_split_dedup")},
        "reported_as": "resampling sensitivity conditional on the stored G-A033 sample; harms are added to "
                       "case values, not simulated; not a server re-run error rate",
    }
    (OUT / "DESIGN_COMPARISON_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                        encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
