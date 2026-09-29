#!/usr/bin/env python3
"""G-A057 일괄 탐색 결과 비교표·그래프 (2026-09-29, Codex 작업 지시 §5).

행: SWEEP_PLAN 의 모든 (변수, 값).  열: 그 정책의 평가 행동.  승자를 고르지 않고 다음 값을 제안하지 않는다.
정책 폴더: REUSE 행은 근거 회차, BASE_SHARED 행은 A048, NEW_TRAIN 행은 workspace/_keep/go2_g_a057_<key>/.
폴더·case 가 없으면 그 칸은 '미측정'이다.  학습 지표(tfevents)는 평가 행동 대신 쓰지 않는다.

지표(모두 평가 seed 101·202·303 합 또는 중앙값):
  G1~G7 점수·최악 case 의 생존·추종   tools/go2_axis_bottleneck.case_row 와 같은 식(min 집계)
  우회전·험지 옆걸음·험지 전진·밀침 네 방향   자세 낙상 수(평가기 summary), 속도 평균, case 점수 최소
  계단 10·15cm(`*_down` = 오르기)            ≥1단·≥2단(tools/go2_climb_count), 완주율 평균(진행/목표 거리),
                                             정체 로봇 수(1초 연속 수평 속도 < 0.05 m/s — GO2_STAIRS_PROCESS 문서의 정의)
  몸통                                       계단 절대 높이 상승 중앙값(첫 episode root_z 최대 − 1초 값),
                                             지형 대비 높이 중앙값(summary), 기울기 중앙값(1~3초)
  속도 동반 여부                              A048 대비 낙상이 줄었을 때 속도도 줄었는지(부호만, 문턱 없음)
  환경                                       meta/gpu.csv (서버 RTX 5080 과 다르면 표시)

    python -B tools/go2_g_a057_sweep_compare.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a057_sweep_compare/
      SWEEP_METRICS.csv, SWEEP_COMPARE.md, <variable>.png
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a043_tilt_onset as om  # noqa: E402
import go2_axis_bottleneck as axis  # noqa: E402
import go2_climb_count as climb  # noqa: E402
import go2_dial_hypothesis as hypothesis  # noqa: E402
import go2_g_a057_sweep_plan as planmod  # noqa: E402

KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a057_sweep_compare"
SEEDS = (101, 202, 303)
ROBOTS = 32
SERVER_GPU = "NVIDIA GeForce RTX 5080"
FALL_CASES = ("combined_yaw_right", "rough_lateral", "rough_forward", "push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y")
STAIRS = {"stairs_10_down": 0.10, "stairs_15_down": 0.15}
AXIS_OF = {"combined_yaw_right": "G2", "rough_lateral": "G3", "rough_forward": "G3", "push_pos_x": "G6", "push_neg_x": "G6",
           "push_pos_y": "G6", "push_neg_y": "G6", "stairs_10_down": "G5", "stairs_15_down": "G5"}
STALL_SPEED, STALL_HOLD = 0.05, 1.0  # GO2_STAIRS_PROCESS_A043_A048_A050_20260927.md §3 의 정체 정의
NA = "미측정"


def arm_dir(row: dict) -> Path:
    if row["status"] == "REUSE":
        return KEEP / row["arm"]
    if row["status"] == "BASE_SHARED":
        return KEEP / planmod.BASE_ARM
    return KEEP / f"go2_g_a057_{row['key']}"


def cases(arm: Path) -> Path:
    return arm / "evaluation/candidate/cases"


def summary(arm: Path, seed: int, case: str) -> dict | None:
    p = cases(arm) / f"seed_{seed}" / case / "summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def expected_name(case: str, seed: int) -> str | None:
    """평가 seed 에서 기대하는 case 이름.  이름에 seed 가 박힌 case(dr_seed_101)는 그 seed 에서만 돈다.

    2026-09-29 결함 수정: 이전 판은 dr_seed_101 을 seed 202·303 에서도 찾아 A048 총점을 늘 '미측정'으로 만들었다.
    """
    if "{seed}" in case:
        return case.replace("{seed}", str(seed))
    m = re.fullmatch(r"(.+)_seed_(\d+)", case)
    if m:
        return case if int(m.group(2)) == seed else None
    return case


def axis_scores(arm: Path) -> dict:
    """G1~G7 점수.  기대 case 가 하나라도 없으면 그 축은 '미측정'이고, 총점도 '미측정'이다.

    빠진 case 를 0 으로 채우지 않고, 남은 case 만으로 min 을 잡지도 않는다(그러면 축 점수가 부풀거나 줄어든다).
    """
    reg = axis.registry()
    std = float(reg["score"]["tracking_proxy_std"])
    points = float(reg["score"]["simulation_points"])
    out, total = {}, 0.0
    complete = True
    for sc in reg["scenarios"]:
        rows, missing = [], []
        for case in sc["internal_cases"]:
            for seed in SEEDS:
                name = expected_name(case, seed)
                if name is None:
                    continue
                s = summary(arm, seed, name)
                if s is None:
                    missing.append(f"{name}:{seed}")
                    continue
                r = axis.case_row(sc["id"], name, seed, s, std)
                if r["proxy"] is None:
                    missing.append(f"{name}:{seed}")
                    continue
                rows.append(r)
        if missing or not rows:
            out[sc["id"]] = {"score": NA, "missing": missing}
            complete = False
            continue
        w = min(rows, key=lambda r: r["proxy"])
        score = w["proxy"] * float(sc["weight"]) * points
        total += score
        out[sc["id"]] = {"score": round(score, 3), "survival": round(w["survival"], 4), "tracking": round(w["tracking"], 4),
                         "worst": f"{w['case']}:{w['seed']}"}
    out["total"] = round(total, 3) if complete else NA
    return out


def steps_rows(arm: Path, seed: int, case: str) -> dict[int, list[dict]] | None:
    p = cases(arm) / f"seed_{seed}" / case / "steps.csv"
    if not p.is_file():
        return None
    envs = om.load(p)
    rz: dict[int, list[tuple[float, float]]] = {}
    with p.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rz.setdefault(int(r["env_id"]), []).append((float(r["time_s"]), float(r["root_z"])))
    for e, rows in envs.items():
        zs = dict(rz.get(e, []))
        for row in rows:
            row["root_z"] = zs.get(row["time_s"])
    return envs


def stall(rows: list[dict]) -> bool:
    run_start = None
    for r in rows:
        if math.hypot(r["actual_vx"], r["actual_vy"]) < STALL_SPEED:
            run_start = r["time_s"] if run_start is None else run_start
            if r["time_s"] - run_start >= STALL_HOLD:
                return True
        else:
            run_start = None
    return False


def case_metrics(arm: Path, case: str, std: float) -> dict:
    falls, speeds, scores, heights, tilts, rises = [], [], [], [], [], []
    stalls = ge1 = ge2 = 0
    completion = []
    for seed in SEEDS:
        s = summary(arm, seed, case)
        if s is None:
            return {"state": NA}
        f = hypothesis.posture_falls(cases(arm) / f"seed_{seed}" / case / "summary.json", ROBOTS)
        if f is None:
            return {"state": NA}
        falls.append(f)
        speeds.append(s.get("speed_xy_mean"))
        r = axis.case_row(AXIS_OF[case], case, seed, s, std)
        scores.append(r["proxy"])
        heights.append(s.get("height_rel_median"))
        if case in STAIRS:
            c = climb.count(cases(arm) / f"seed_{seed}" / case / "steps.csv", STAIRS[case])
            if c is None:
                return {"state": NA}
            ge1 += int(c["ge1"])
            ge2 += int(c["ge2"])
            completion.append(r["completion"])
        envs = steps_rows(arm, seed, case)
        if envs is None:
            return {"state": NA}
        for rows in envs.values():
            tf = om.fall_time(rows)
            win = [r for r in rows if 1.0 <= r["time_s"] < min(3.0, tf if tf else 99.0)]
            if win:
                tilts.append(st.median(r["tilt"] for r in win))
            if case in STAIRS:
                stalls += stall(rows)
                z1 = [r["root_z"] for r in rows if r["root_z"] is not None and r["time_s"] >= 1.0]
                if z1:
                    rises.append(max(z1) - z1[0])
    out = {"state": "OK", "falls": sum(falls),
           "speed": None if None in speeds else round(st.fmean(speeds), 4),
           "case_score_min": None if None in scores else round(min(scores), 4),
           "height_rel": None if None in heights else round(st.fmean(heights), 4),
           "tilt_deg": round(st.median(tilts), 2) if tilts else None}
    if case in STAIRS:
        out.update(ge1=ge1, ge2=ge2, stall=stalls, completion=round(st.fmean(completion), 4),
                   abs_rise_m=round(st.median(rises), 4) if rises else None)
    return out


def gpu(arm: Path) -> str:
    p = arm / "meta/gpu.csv"
    return p.read_text(encoding="utf-8").strip().splitlines()[0] if p.is_file() and p.read_text(encoding="utf-8").strip() else NA


def collect() -> list[dict]:
    plan = planmod.plan()
    std = float(axis.registry()["score"]["tracking_proxy_std"])
    cache: dict[str, dict] = {}
    out = []
    for row in plan["runs"]:
        arm = arm_dir(row)
        rec = {"variable": row["variable"], "value": row["value"], "status": row["status"], "arm": arm.name,
               "present": arm.is_dir() and cases(arm).is_dir()}
        if rec["present"]:
            if arm.name not in cache:
                m = {"axes": axis_scores(arm), "gpu": gpu(arm)}
                for c in (*FALL_CASES, *STAIRS):
                    m[c] = case_metrics(arm, c, std)
                cache[arm.name] = m
            rec.update(cache[arm.name])
        out.append(rec)
    return out


def flat(rec: dict) -> dict:
    row = {k: rec[k] for k in ("variable", "value", "status", "arm")}
    if not rec["present"]:
        row["note"] = "결과 미회수 — 전 칸 미측정"
        return row
    g = rec["gpu"]
    row["gpu"] = g
    row["env_note"] = "" if g.startswith(SERVER_GPU) else "서버와 다른 GPU — 차이를 보상 효과로만 읽지 않는다"
    for ax in ("G1", "G2", "G3", "G4", "G5", "G6", "G7"):
        a = rec["axes"].get(ax, {})
        row[f"{ax}_score"] = a.get("score", NA)
        row[f"{ax}_worst_survival"] = a.get("survival", NA)
        row[f"{ax}_worst_tracking"] = a.get("tracking", NA)
    row["total_70"] = rec["axes"]["total"]
    for c in (*FALL_CASES, *STAIRS):
        m = rec[c]
        for k in ("falls", "speed", "case_score_min", "height_rel", "tilt_deg", "ge1", "ge2", "stall", "completion", "abs_rise_m"):
            if k in ("ge1", "ge2", "stall", "completion", "abs_rise_m") and c not in STAIRS:
                continue
            row[f"{c}_{k}"] = m.get(k, NA) if m.get("state") == "OK" else NA
    push = [rec[c]["falls"] for c in FALL_CASES if c.startswith("push") and rec[c].get("state") == "OK"]
    row["push_falls_sum"] = sum(push) if len(push) == 4 else NA
    return row


def speed_flags(rows: list[dict]) -> None:
    base = next((r for r in rows if r["status"] in ("REUSE", "BASE_SHARED") and r["arm"] == planmod.BASE_ARM and "total_70" in r), None)
    for r in rows:
        if base is None or "total_70" not in r:
            continue
        notes = []
        for c in ("combined_yaw_right", "rough_lateral", "rough_forward", "stairs_15_down"):
            f, s = r.get(f"{c}_falls"), r.get(f"{c}_speed")
            bf, bs = base.get(f"{c}_falls"), base.get(f"{c}_speed")
            if NA in (f, s, bf, bs) or None in (f, s, bf, bs):
                continue
            if f < bf:
                notes.append(f"{c}: 낙상↓({bf}→{f})·속도{'↓' if s < bs else '↑/='}({bs}→{s})")
        r["fall_down_with_speed"] = "; ".join(notes)


def markdown(rows: list[dict]) -> str:
    cols = [("value", "값"), ("status", "상태"), ("total_70", "총점"), ("G2_score", "G2"), ("G3_score", "G3"), ("G5_score", "G5"),
            ("G6_score", "G6"), ("combined_yaw_right_falls", "우회전 낙상"), ("rough_lateral_falls", "험지옆 낙상"),
            ("rough_lateral_speed", "험지옆 속도"), ("rough_forward_falls", "험지전진 낙상"), ("push_falls_sum", "밀침 합"),
            ("stairs_10_down_ge2", "10cm ≥2단"), ("stairs_15_down_ge2", "15cm ≥2단"), ("stairs_15_down_completion", "15cm 완주율"),
            ("stairs_15_down_stall", "15cm 정체"), ("stairs_15_down_abs_rise_m", "15cm 상승 m"),
            ("rough_lateral_height_rel", "험지옆 높이"), ("rough_lateral_tilt_deg", "험지옆 기울기°"), ("env_note", "환경")]
    lines = ["# G-A057 변수별 반응 표 (자동 생성: tools/go2_g_a057_sweep_compare.py)", "",
             "승자를 고르지 않는다. 미측정 칸은 결과가 없는 것이다. 모든 행은 학습 seed 42 한 번이다.", ""]
    for var in planmod.GRID:
        lines += [f"## {var}", "", "| " + " | ".join(h for _, h in cols) + " |", "|" + "---|" * len(cols)]
        for r in sorted((r for r in rows if r["variable"] == var), key=lambda r: r["value"]):
            lines.append("| " + " | ".join(str(r.get(k, NA)) for k, _ in cols) + " |")
        flags = [f"- {r['value']}: {r['fall_down_with_speed']}" for r in rows if r["variable"] == var and r.get("fall_down_with_speed")]
        if flags:
            lines += ["", "A048 대비 낙상이 줄어든 case 의 속도 변화:", *flags]
        lines.append("")
    return "\n".join(lines) + "\n"


def plots(rows: list[dict]) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    panels = [("total_70", "total /70"), ("rough_lateral_falls", "rough lateral falls"), ("combined_yaw_right_falls", "yaw right falls"),
              ("push_falls_sum", "push falls (4 dir)"), ("stairs_15_down_ge2", "15cm >=2 steps"), ("stairs_10_down_ge2", "10cm >=2 steps"),
              ("rough_lateral_height_rel", "rough lat. height_rel"), ("rough_lateral_tilt_deg", "rough lat. tilt deg")]
    made = []
    for var in planmod.GRID:
        sel = sorted((r for r in rows if r["variable"] == var), key=lambda r: r["value"])
        fig, axes = plt.subplots(2, 4, figsize=(16, 7))
        for ax, (k, title) in zip(axes.flat, panels):
            xs = [r["value"] for r in sel if isinstance(r.get(k), (int, float))]
            ys = [r[k] for r in sel if isinstance(r.get(k), (int, float))]
            miss = [r["value"] for r in sel if not isinstance(r.get(k), (int, float))]
            ax.plot(xs, ys, "o-")
            for m in miss:
                ax.axvline(m, color="lightgray", ls=":")
            ax.set_title(title + (" (gray = not measured)" if miss else ""), fontsize=9)
            ax.set_xlabel(var, fontsize=8)
        fig.suptitle(f"G-A057 {var} (A048 base, seed 42, one run per value)")
        fig.tight_layout()
        path = OUT / f"{var}.png"
        fig.savefig(path, dpi=90)
        plt.close(fig)
        made.append(str(path))
    return made


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [flat(r) for r in collect()]
    speed_flags(rows)
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with (OUT / "SWEEP_METRICS.csv").open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, restval=NA, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (OUT / "SWEEP_COMPARE.md").write_text(markdown(rows), encoding="utf-8", newline="\n")
    made = plots(rows)
    print(json.dumps({"rows": len(rows), "measured": sum("total_70" in r for r in rows), "plots": len(made), "out": str(OUT)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
