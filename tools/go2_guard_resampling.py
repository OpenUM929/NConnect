#!/usr/bin/env python3
"""보호 검사 재표집 민감도 — 저장된 G-A033 표본에 조건부 (D2, 2026-09-26).

무엇을 묻는가.  계획 screening `post_a043_push4_v1` 의 **보호 묶음**(여덟 case 의 pooled 자세 낙상 ≤ 기준선,
seed 별 생존 차이 중앙값 ≥ 0, 험지 두 case·밀침 네 방향의 추종 차이 중앙값 ≥ 0 — 22검사)이, 저장된
G-A033 과 **같은 로봇 궤적 집합에서 다시 뽑은** 후보를 저장된 G-A033 과 비교할 때 얼마나 자주 실패하는가.

무엇을 묻지 않는가.
  - 개선 묶음(계단 전진거리·등반수·정체 감소, 9검사)은 **엄격한 개선**을 요구한다.  같은 정책이 개선하지
    않아 떨어지는 것은 거짓 실패가 아니므로 이 셈에서 뺀다(외부 검토 2026-09-26).
  - 이 값은 **서버 재실행 오판율이 아니다.**  저장된 96대(case·seed 마다 32대)를 모집단으로 삼은 재표집
    민감도다.  학습을 다시 하거나 시뮬레이터를 다시 돌린 흔들림은 담지 않는다.
  - 문턱을 바꾸지 않는다.  재표집 결과가 높아도 그것만으로 보호 문턱 완화가 정당화되지 않는다.

재표집 단위.  **로봇 한 대의 전체 궤적**(1000 step).  case·평가 seed 마다 따로 32대를 복원 추출한다
— 평가 seed 구조가 보존되고, 한 로봇의 낙상·생존·추종이 함께 뽑혀 지표 간 의존이 보존된다.  기준선은
저장값 그대로 고정한다(screening 이 실제로 하는 비교와 같다).

셈이 평가기와 같은지 먼저 확인한다.  steps.csv 에서 로봇별로 다시 센 낙상 수·생존·추종이 원 시행
(재표집 없이 32대 전부)에서 screening `case_rows` 값과 같아야 한다.  다르면 재표집을 하지 않는다.

    python -B tools/go2_guard_resampling.py [--draws 2000]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import go2_screening_gate as gate  # noqa: E402
import go2_eval_telemetry as tele  # noqa: E402

VERSION = "post_a043_push4_v1"
CASES = gate.RULE_VERSIONS[VERSION]
TRACKED = (*gate.ROUGH, *[c for c in CASES if c in gate.PUSH_ALL])
SEEDS = gate.SEEDS
BASE_ARM = gate.BASELINE_ARM
A048_ARM = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/evaluation/candidate"
OUT = QUAD / "reports/evidence/go2_guard_resampling_20260926"
RNG_SEED = 20260926
TOL = 1e-9


def env_stats(case_dir: Path) -> tuple[list[dict], float]:
    """로봇별 원값 — 평가기(`go2_eval_telemetry.Collector`)와 같은 규칙으로 다시 센다."""
    summary = json.loads((case_dir / "summary.json").read_text(encoding="utf-8"))
    dt = float(summary["step_dt"])
    per: dict[int, dict] = {}
    with (case_dir / "steps.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            env = int(row["env_id"])
            s = per.setdefault(env, {"sq": 0.0, "n": 0, "post_sq": 0.0, "post_n": 0, "run": 0.0,
                                     "fallen": False, "terminated": False, "speed": [], "upright": []})
            t = int(row["step"]) * dt
            err = float(row["error_xy"])
            s["sq"] += err * err
            s["n"] += 1
            if t >= 4.0:
                s["post_sq"] += err * err
                s["post_n"] += 1
            up = row["upright"]
            upright = None if up == "" else bool(int(up))
            if t >= tele.FALL_GRACE_S:                  # 비관 타이머: 못 읽은 행은 넘어진 것으로
                if upright is not False and upright is not None:
                    s["run"] = 0.0
                else:
                    s["run"] += dt
                    if s["run"] >= tele.FALL_HOLD_S:
                        s["fallen"] = True
            if int(row["terminated"]):
                s["terminated"] = True
            s["speed"].append((t, float(row["speed_xy"])))
            s["upright"].append((t, bool(upright)))
    out = []
    for env in sorted(per):
        s = per[env]
        expected, upright_rec = recovery(s["speed"], s["upright"], dt)
        out.append({"fallen": s["fallen"] or s["terminated"], "sq": s["sq"], "n": s["n"],
                    "post_sq": s["post_sq"], "post_n": s["post_n"],
                    "rec_expected": expected, "rec_upright": upright_rec})
    return out, float(gate.std())


def recovery(samples: list, upright: list, dt: float) -> tuple[int, int]:
    """`Collector._recovery` 의 한 로봇 몫(예정 사건 수, 똑바로 회복한 사건 수)."""
    quiet = max(1, round(0.5 / dt))
    expected = recovered = 0
    max_time = samples[-1][0] if samples else 0.0
    for push_time in (4.0, 8.0, 12.0, 16.0):
        if push_time + 1.0 > max_time:
            continue
        expected += 1
        cands = [(i, st, sp) for i, (st, sp) in enumerate(samples) if push_time <= st <= push_time + 1.0]
        if not cands:
            continue
        peak_index = max(cands, key=lambda item: item[2])[0]
        for index in range(peak_index, len(samples) - quiet + 1):
            window = samples[index:index + quiet]
            if not all(speed <= 0.15 for _, speed in window):
                continue
            up_window = upright[index:index + quiet]
            if up_window and all(flag for _, flag in up_window):
                recovered += 1
                break
    return expected, recovered


def track(rmse: float | None, std: float) -> float | None:
    return None if rmse is None else math.exp(-((rmse / std) ** 2))


def metrics(case_id: str, envs: list[dict], std: float) -> dict:
    """뽑힌 로봇 묶음의 case 값 — screening 이 읽는 세 값."""
    fallen = sum(1 for e in envs if e["fallen"])
    n = sum(e["n"] for e in envs)
    rmse = math.sqrt(sum(e["sq"] for e in envs) / n) if n else None
    tracking = track(rmse, std)
    if case_id.startswith("push_"):
        pn = sum(e["post_n"] for e in envs)
        post = math.sqrt(sum(e["post_sq"] for e in envs) / pn) if pn else None
        exp_ = sum(e["rec_expected"] for e in envs)
        rec = sum(e["rec_upright"] for e in envs) / exp_ if exp_ else None
        t = track(post, std)
        tracking = min(t, rec) if t is not None and rec is not None else None
    return {"posture_falls": fallen, "survival": 1.0 - fallen / len(envs), "tracking": tracking}


def guard_checks(base: dict, cand: dict) -> dict[str, bool]:
    """`go2_screening_gate.judge` 의 보호 묶음과 같은 식."""
    out = {}
    for case_id in CASES:
        b = sum(base[(case_id, s)]["posture_falls"] for s in SEEDS)
        c = sum(cand[(case_id, s)]["posture_falls"] for s in SEEDS)
        out[f"{case_id} pooled posture falls <= baseline"] = c <= b
        d = statistics.median(cand[(case_id, s)]["survival"] - base[(case_id, s)]["survival"] for s in SEEDS)
        out[f"{case_id} survival median delta >= 0"] = d >= 0
    for case_id in TRACKED:
        d = statistics.median(cand[(case_id, s)]["tracking"] - base[(case_id, s)]["tracking"] for s in SEEDS)
        out[f"{case_id} tracking proxy median delta >= 0"] = d >= 0
    return out


def guard_statistics(base: dict, cand: dict) -> dict[str, float]:
    """각 보호 검사가 문턱과 비교하는 값 — 낙상은 (후보 − 기준선) pooled 대수, 나머지는 seed 차이 중앙값.
    낙상은 클수록, 생존·추종은 작을수록 나쁘다."""
    out = {}
    for case_id in CASES:
        out[f"{case_id} pooled posture falls <= baseline"] = float(
            sum(cand[(case_id, s)]["posture_falls"] - base[(case_id, s)]["posture_falls"] for s in SEEDS))
        out[f"{case_id} survival median delta >= 0"] = statistics.median(
            cand[(case_id, s)]["survival"] - base[(case_id, s)]["survival"] for s in SEEDS)
    for case_id in TRACKED:
        out[f"{case_id} tracking proxy median delta >= 0"] = statistics.median(
            cand[(case_id, s)]["tracking"] - base[(case_id, s)]["tracking"] for s in SEEDS)
    return out


def load(arm: Path) -> tuple[dict, float]:
    stats, std = {}, None
    for case_id in CASES:
        for seed in SEEDS:
            stats[(case_id, seed)], std = env_stats(arm / "cases" / f"seed_{seed}" / case_id)
    return stats, std


def validate(arm: Path, stats: dict, std: float) -> list[str]:
    """다시 센 원 시행 값이 screening case_rows 값과 같은가."""
    rows = gate.case_rows(arm, CASES)
    faults = []
    for key, envs in stats.items():
        mine = metrics(key[0], envs, std)
        theirs = rows[key]
        # 계단 case 의 추종은 보호 묶음이 읽지 않는다(완주율과 min 을 취하므로 여기서 다시 세지 않는다).
        for field in ("posture_falls", "survival", *(("tracking",) if key[0] in TRACKED else ())):
            a, b = mine[field], theirs[field]
            if a is None or b is None or abs(float(a) - float(b)) > TOL:
                faults.append(f"{arm.parts[-3]} {key} {field}: recount {a} vs screening {b}")
    return faults


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=2000)
    args = parser.parse_args(argv)
    base_stats, std = load(BASE_ARM)
    a048_stats, _ = load(A048_ARM)
    faults = validate(BASE_ARM, base_stats, std) + validate(A048_ARM, a048_stats, std)
    if faults:
        for fault in faults[:20]:
            print("RECOUNT MISMATCH", fault)
        return 1
    base = {k: metrics(k[0], v, std) for k, v in base_stats.items()}
    a048 = {k: metrics(k[0], v, std) for k, v in a048_stats.items()}

    rng = random.Random(RNG_SEED)
    names = list(guard_checks(base, base))
    fails = {name: 0 for name in names}
    any_fail = 0
    fail_counts = []
    drawn: dict[str, list[float]] = {name: [] for name in names}
    for _ in range(args.draws):
        cand = {k: metrics(k[0], [envs[rng.randrange(len(envs))] for _ in envs], std)
                for k, envs in base_stats.items()}
        result = guard_checks(base, cand)
        for n, value in guard_statistics(base, cand).items():
            drawn[n].append(value)
        bad = [n for n, ok in result.items() if not ok]
        for n in bad:
            fails[n] += 1
        any_fail += bool(bad)
        fail_counts.append(len(bad))

    OUT.mkdir(parents=True, exist_ok=True)
    a048_result = guard_checks(base, a048)
    with (OUT / "GUARD_CHECK_RESAMPLING.csv").open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["check", "baseline_value", "resample_fail_rate", "a048_observed_ok"])
        for n in names:
            case_id = n.split(" ")[0]
            if "posture falls" in n:
                bv = sum(base[(case_id, s)]["posture_falls"] for s in SEEDS)
            else:
                field = "survival" if "survival" in n else "tracking"
                bv = "/".join(f"{base[(case_id, s)][field]:.5f}" for s in SEEDS)
            w.writerow([n, bv, f"{fails[n] / args.draws:.4f}", a048_result[n]])
    # G-A048 의 실제 변화량이 재표집 분포의 어디에 있는가(외부 검토 2026-09-26: 실패 빈도만으로는 위치를 말할 수 없다).
    # tail = 재표집에서 G-A048 만큼 나쁘거나 더 나쁜 값이 나온 비율.  위치일 뿐 검정·판정이 아니다.
    a048_stat = guard_statistics(base, a048)
    with (OUT / "A048_POSITION_IN_RESAMPLING.csv").open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["check", "a048_value", "resample_p05", "resample_median", "resample_p95",
                    "share_at_least_as_bad_as_a048"])
        for n in names:
            values = sorted(drawn[n])
            worse_up = "posture falls" in n
            a = a048_stat[n]
            share = sum(1 for v in values if (v >= a if worse_up else v <= a)) / len(values)
            q = lambda f: values[min(len(values) - 1, int(f * len(values)))]
            w.writerow([n, f"{a:.5f}", f"{q(0.05):.5f}", f"{statistics.median(values):.5f}", f"{q(0.95):.5f}",
                        f"{share:.4f}"])
    dist = {k: fail_counts.count(k) for k in sorted(set(fail_counts))}
    summary = {
        "question": "how often the post_a043_push4_v1 guard block fails when a candidate is a whole-robot "
                    "resample of the stored G-A033 arm, compared against the stored G-A033 arm",
        "reported_as": "resampling sensitivity conditional on the stored G-A033 sample; NOT a server "
                       "re-run false-failure rate; thresholds unchanged",
        "rule_version": VERSION, "guard_checks": len(names), "improvement_checks_excluded": 9,
        "unit": "whole robot trajectory, resampled with replacement within each case x evaluation seed",
        "dependence_preserved": "between metrics of the same robot within one case x seed only; case x seed "
                                "cells are drawn independently",
        "scope": "candidates drawn from the same empirical distribution as G-A033; says nothing about the "
                 "failure rate of a genuinely improved candidate",
        "draws": args.draws, "rng_seed": RNG_SEED,
        "recount_validated_against_screening": ["G-A033 stored arm", "G-A048 candidate arm"],
        "any_guard_fail_rate": any_fail / args.draws,
        "guard_fail_count_distribution": dist,
        "a048_guard_failures": [n for n, ok in a048_result.items() if not ok],
    }
    (OUT / "GUARD_RESAMPLING_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                       encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
