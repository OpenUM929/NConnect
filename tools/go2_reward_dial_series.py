#!/usr/bin/env python3
"""Go2 보상 변수별 '값 → 결과' 표 — 회수물 case 기록에서 같은 계수기로 센다 (2026-09-28).

왜 따로 있는가.  사용자 지시(2026-09-28): 변수마다 값 변화에 따른 결과 표가 있어야 제대로 된 분석이 된다.
참고본 `workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md`는 표를 손으로 옮기지 않고
이 도구가 만든 `DIAL_SERIES_TABLES.md`를 가리킨다.

계열.  한 계열은 **같은 기준 정책 계보** 안에서 한 항만 다른 arm들이다. 계보가 다르면 같은 표에 놓지 않는다.
  - Pilot-01 계보 tier-1 쌍(A015·A016·A018): 각 회차가 같은 패키지 안에서 동결 Pilot-01을 다시 잰 `baseline_tier1`과 짝이다.
  - A017→A033 계보: A027 전수(`go2_a017_full_suite`의 pilot·a017 arm)와 A031·A032·A033·A038~A050.
  - Default-01·Chain-01 위 회차는 기준 정책이 걷지 않아(정지 기준선) 넣지 않는다(원장 G-D116 철회·G-D104 보류).

셈(case·arm마다, 그 arm에서 평가한 seed 전부):
  robots        32 × seed 수
  falls         summary.json `posture_fall_env_count_pessimistic` 합 (없으면 `fallen_env_count`, 출처 열에 적음)
  survival      `survival_proxy` 평균
  speed         `speed_xy_mean` 평균 (m/s)
  progress      `projected_progress_m` 평균 (m)
  height_med    `height_rel_median` 평균 (m)
  track_rmse    `tracking_xy_rmse` 평균
  climb_ge1/2   계단 case만, tools/go2_climb_count.py `count()` 합 (기록이 없으면 빈칸)
DR case는 이름에 seed가 들어가므로(dr_seed_101) `dr`로 묶는다.

한계.  모든 회차는 학습 seed 42 하나다. arm마다 평가한 seed 수가 다를 수 있다(robots 열로 표시).
평가 checkpoint iter가 arm마다 다를 수 있다(Pilot 999, A017 이후 900 고정). 표는 판정이 아니라 관측이다.

    python -B tools/go2_reward_dial_series.py           # CSV와 표를 만든다
    python -B tools/go2_reward_dial_series.py --check   # 저장본과 재계산이 같은지만 본다
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep"
sys.path.insert(0, str(ROOT / "tools"))
import go2_climb_count as climb  # noqa: E402

OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_reward_trial_reference_20260928"
CSV_PATH = OUT / "DIAL_SERIES_CASES.csv"
MD_PATH = OUT / "DIAL_SERIES_TABLES.md"

A017_FULL = "go2_a017_full_suite/evaluation"


def cand(run: str) -> str:
    return f"{run}/evaluation/candidate"


# (계열 id, 변수, 계보 설명, [(arm 이름, 회차, 값, 평가 arm 경로)])
SERIES = (
    ("track_A017_line", "track_lin_vel_xy_exp", "Pilot-01 → A017 → A033 계보, posture_gate_v2 (Pilot 999·A017 900 checkpoint)", [
        ("Pilot-01", "Pilot-01", "1.2", f"{A017_FULL}/pilot"),
        ("A017", "G-A017", "1.4", f"{A017_FULL}/a017"),
        ("A033", "G-A033", "1.5", cand("go2_g_a033_a017_track_lin_vel_xy_150")),
        ("A042", "G-A042", "1.6", cand("go2_g_a042_a033_track_lin_vel_xy_160")),
    ]),
    ("feet_air_time_A017", "feet_air_time", "A017 기준 (A027 전수의 a017 arm이 0.2)", [
        ("A031", "G-A031", "0.01", cand("go2_g_a031_a017_feet_air_time_001")),
        ("A032", "G-A032", "0.1", cand("go2_g_a032_a017_feet_air_time_010")),
        ("A017", "G-A017", "0.2", f"{A017_FULL}/a017"),
    ]),
    ("feet_air_time_Pilot", "feet_air_time", "Pilot-01 tier-1 쌍 (같은 패키지, 평가 seed 101)", [
        ("Pilot-01", "Pilot-01", "0.2", "go2_g_a015_pilot_feet_air_time_035/evaluation/baseline_tier1"),
        ("A015", "G-A015", "0.35", cand("go2_g_a015_pilot_feet_air_time_035")),
    ]),
    ("lin_vel_z_A033", "lin_vel_z_l2", "A033 기준, 69 case 전수", [
        ("A033", "G-A033", "-2.0", cand("go2_g_a033_a017_track_lin_vel_xy_150")),
        ("A044", "G-A044", "-1.75", cand("go2_g_a044_a033_lin_vel_z_m175")),
        ("A043", "G-A043", "-1.5", cand("go2_g_a043_a033_lin_vel_z_m15")),
        ("A050", "G-A050", "-1.375", cand("go2_g_a050_a033_lin_vel_z_m1375")),
        ("A048", "G-A048", "-1.25", cand("go2_g_a048_a033_lin_vel_z_m125")),
        ("A049", "G-A049", "-1.0", cand("go2_g_a049_a033_lin_vel_z_m1")),
    ]),
    ("ang_vel_xy_A033", "ang_vel_xy_l2", "A033 기준 (A038·A041은 1단계 일부 case)", [
        ("A038", "G-A038", "-0.08", cand("go2_g_a038_a033_ang_vel_xy_m008")),
        ("A033", "G-A033", "-0.05", cand("go2_g_a033_a017_track_lin_vel_xy_150")),
        ("A041", "G-A041", "-0.04", cand("go2_g_a041_a033_ang_vel_xy_m004")),
    ]),
    ("ang_vel_xy_Pilot", "ang_vel_xy_l2", "Pilot-01 tier-1 쌍 (같은 패키지, 평가 seed 101)", [
        ("A016", "G-A016", "-0.15", cand("go2_g_a016_pilot_ang_vel_xy_m015")),
        ("Pilot-01", "Pilot-01", "-0.05", "go2_g_a016_pilot_ang_vel_xy_m015/evaluation/baseline_tier1"),
    ]),
    ("action_rate_Pilot", "action_rate_l2", "Pilot-01 tier-1 쌍 (같은 패키지, 평가 seed 101)", [
        ("Pilot-01", "Pilot-01", "-0.01", "go2_g_a018_pilot_action_rate_m008/evaluation/baseline_tier1"),
        ("A018", "G-A018", "-0.008", cand("go2_g_a018_pilot_action_rate_m008")),
    ]),
    ("flat_orientation_A033", "flat_orientation_l2", "A033 기준, 69 case 전수", [
        ("A033", "G-A033", "0.0", cand("go2_g_a033_a017_track_lin_vel_xy_150")),
        ("A047", "G-A047", "-0.5", cand("go2_g_a047_a033_flat_orientation_m05")),
    ]),
)

COLUMNS = ["series", "variable", "arm", "work_id", "value", "case", "seeds", "robots", "falls", "fall_source",
           "survival", "speed", "progress", "height_med", "track_rmse", "climb_ge1", "climb_ge2"]
STAIRS = {"stairs_10_down": 0.10, "stairs_15_down": 0.15, "stairs_10_up": 0.10, "stairs_15_up": 0.15}
# 표에 싣는 순서. 이름과 실제 방향: `*_down`이 오르기, `*_up`이 내려가기(tools/go2_climb_count.py 머리말).
CASE_ORDER = ["forward_nominal", "forward_slow", "forward_fast", "backward", "left", "right", "diagonal_left",
              "diagonal_right", "combined_yaw_left", "combined_yaw_right", "rough_forward", "rough_lateral",
              "slope_plus_20", "slope_minus_20", "stairs_10_down", "stairs_15_down", "stairs_10_up", "stairs_15_up",
              "push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y", "dr"]
CASE_KO = {"forward_nominal": "평지 전진", "forward_slow": "평지 저속", "forward_fast": "평지 고속", "backward": "후진",
           "left": "왼쪽 옆", "right": "오른쪽 옆", "diagonal_left": "왼쪽 대각", "diagonal_right": "오른쪽 대각",
           "combined_yaw_left": "전진+좌회전", "combined_yaw_right": "전진+우회전", "rough_forward": "험지 전진",
           "rough_lateral": "험지 옆걸음", "slope_plus_20": "경사 +20°", "slope_minus_20": "경사 −20°",
           "stairs_10_down": "10cm 계단 오르기", "stairs_15_down": "15cm 계단 오르기",
           "stairs_10_up": "10cm 계단 내려가기", "stairs_15_up": "15cm 계단 내려가기",
           "push_pos_x": "밀침 앞", "push_neg_x": "밀침 뒤", "push_pos_y": "밀침 왼쪽", "push_neg_y": "밀침 오른쪽",
           "dr": "도메인 랜덤화"}


def case_key(name: str) -> str:
    return "dr" if name.startswith("dr_seed_") else name


def arm_rows(series: str, variable: str, arm: str, work_id: str, value: str, rel: str) -> list[dict[str, str]]:
    root = KEEP / rel / "cases"
    if not root.is_dir():
        raise RuntimeError(f"{rel}: no cases directory")
    by_case: dict[str, list[Path]] = {}
    for seed_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for case_dir in sorted(p for p in seed_dir.iterdir() if (p / "summary.json").is_file()):
            by_case.setdefault(case_key(case_dir.name), []).append(case_dir)
    out = []
    for case, dirs in by_case.items():
        sums = [json.loads((d / "summary.json").read_text(encoding="utf-8")) for d in dirs]
        key = "posture_fall_env_count_pessimistic" if all(
            "posture_fall_env_count_pessimistic" in s for s in sums) else "fallen_env_count"

        def mean(field: str) -> str:
            vals = [s[field] for s in sums if isinstance(s.get(field), (int, float))]
            return f"{sum(vals) / len(vals):.4f}" if len(vals) == len(sums) else ""

        row = {"series": series, "variable": variable, "arm": arm, "work_id": work_id, "value": value,
               "case": case, "seeds": str(len(dirs)), "robots": str(32 * len(dirs)),
               "falls": str(sum(int(s[key]) for s in sums)), "fall_source": key,
               "survival": mean("survival_proxy"), "speed": mean("speed_xy_mean"),
               "progress": mean("projected_progress_m"), "height_med": mean("height_rel_median"),
               "track_rmse": mean("tracking_xy_rmse"), "climb_ge1": "", "climb_ge2": ""}
        if case in STAIRS:
            counts = []
            for d in dirs:
                try:
                    counts.append(climb.count(d / "steps.csv", STAIRS[case]))
                except (KeyError, ValueError, FileNotFoundError):
                    counts.append(None)
            if counts and all(c is not None and int(c["robots"]) == 32 for c in counts):
                row["climb_ge1"] = str(sum(int(c["ge1"]) for c in counts))
                row["climb_ge2"] = str(sum(int(c["ge2"]) for c in counts))
        out.append(row)
    return out


def build() -> list[dict[str, str]]:
    rows = []
    for series, variable, _desc, arms in SERIES:
        for arm in arms:
            rows.extend(arm_rows(series, variable, *arm))
    return rows


def cell(r: dict[str, str] | None) -> str:
    if r is None:
        return "—"
    parts = [f"낙상 {r['falls']}/{r['robots']}"]
    if r["speed"]:
        parts.append(f"속도 {float(r['speed']):.2f}")
    if r["height_med"]:
        parts.append(f"높이 {float(r['height_med']):.2f}")
    if r["climb_ge1"]:
        verb = "내려감" if r["case"].endswith("_up") else "오름"
        parts.append(f"{verb}≥1 {r['climb_ge1']}·≥2 {r['climb_ge2']}")
    return "<br>".join(parts)


def tables(rows: list[dict[str, str]]) -> str:
    lines = ["# 보상 변수별 값 → 결과 표 (생성물 — 손으로 고치지 않는다)", "",
             "생성: `python -B tools/go2_reward_dial_series.py`. 정의·계보·한계는 도구 머리말.",
             "칸: 낙상 = 자세 낙상 수/로봇 수, 속도 = speed_xy 평균(m/s), 높이 = 지면 대비 몸 높이 중앙값(m),",
             "오름/내려감 = 계단 ≥1단·≥2단을 지난 로봇 수. `—` = 그 arm에서 평가하지 않은 case.",
             "case 이름 `*_down`이 실제 오르기, `*_up`이 실제 내려가기다(표에는 실제 방향으로 적었다).", ""]
    for series, variable, desc, arms in SERIES:
        lines += [f"## `{variable}` — {series}", "", f"계보: {desc}", ""]
        header = "| case | " + " | ".join(f"{a[0]} `{a[2]}`" for a in arms) + " |"
        lines += [header, "|---|" + "---|" * len(arms)]
        index = {(r["arm"], r["case"]): r for r in rows if r["series"] == series}
        cases = [c for c in CASE_ORDER if any((a[0], c) in index for a in arms)]
        for c in cases:
            lines.append(f"| {CASE_KO.get(c, c)} | " + " | ".join(cell(index.get((a[0], c))) for a in arms) + " |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rows = build()
    md = tables(rows)
    if args.check:
        with CSV_PATH.open(encoding="utf-8", newline="") as handle:
            same_csv = list(csv.DictReader(handle)) == rows
        same_md = MD_PATH.read_text(encoding="utf-8") == md
        print("OK" if same_csv and same_md else "MISMATCH")
        return 0 if same_csv and same_md else 1
    OUT.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    MD_PATH.write_text(md, encoding="utf-8", newline="\n")
    print(CSV_PATH)
    print(MD_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
