#!/usr/bin/env python3
"""A033 → A047(flat_orientation_l2 0→−0.5) 손실이 기울기와 함께 났는가, 자세를 유지한 채 났는가 (2026-09-29, Codex 지시).

기존 평가 기록(steps.csv)만 쓴다.  새 서버 진단·계단 원인 재분석은 하지 않는다.  새 성공 문턱은 만들지 않는다.
기울기 방향 채널(grav_b_x·y)은 이 평가 기록에 없다.  proj_grav_z 로 기울기 크기만 잰다.  그래서 A043 의 '회전 안쪽 기울기'와
같은 현상이라고 쓰지 않는다.

팔(arm): A033 = workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150 (G_A047 사양 comparison_arm.stored_arm),
         A047 = workspace/_keep/go2_g_a047_a033_flat_orientation_m05.  평가 seed 101·202·303, case 당 32대.
case: 복합 우회전·험지 옆걸음·밀침 네 방향(1순위), 험지 전진·경사 ±20°·DR(2순위).  계단은 보지 않는다.

로봇마다 첫 episode 만 쓴다(첫 terminated/truncated 행에서 자르고 그 행도 뺀다).  낙상·onset 은
tools/go2_a043_tilt_onset.py 의 fall_time·onset_time 그대로다(0.5 s 유예 뒤 자세 게이트 0.5 s 또는 몸통 접촉 종료;
onset = 낙상 전 기울기 18° 를 마지막으로 위로 넘은 시각).  기울기(도) = acos(−proj_grav_z).
구간 (생존 중 구간과 실패 직전 구간을 섞지 않는다)
  early    1~3 s.  낙상 로봇은 실패 직전 구간과 겹치지 않는 부분만.
  survive  1 s ~ (기준 − 1 s).  기준은 onset, onset 이 없으면 낙상 시각.  낙상하지 않은 로봇은 1 s ~ 끝.
  pre_fail (기준 − 1 s) ~ 기준.  낙상 로봇만.
값: 기울기 평균, speed_xy 평균, error_xy 평균(추종 오차), error_yaw 평균, height_rel 평균.
같은 기울기 비교: case·seed 마다 A033 survive 행 기울기의 중앙값 m 을 기준으로, 두 팔의 survive 행 중 기울기 ≤ m 인 행만 모아
  error_xy·speed_xy 평균을 비교한다(m 은 비교용 기준값이지 성공 문턱이 아니다).
분류 (부호만, 세 평가 seed 가 모두 같은 방향일 때만 방향으로 센다)
  tilt_higher   survive 기울기(로봇 평균의 중앙값)가 A047 > A033 인 seed 수
  loss          survive error_xy(로봇 평균의 중앙값)가 A047 > A033 인 seed 수
  matched_loss  같은 기울기 비교에서 A047 error_xy > A033 인 seed 수
  EXCESS_TILT_WITH_LOSS   tilt_higher 3/3, loss 3/3, matched_loss 3/3 아님 — 과도한 기울기 동반
  POSTURE_KEPT_LOSS       tilt_higher 3/3 아님, matched_loss 3/3 — 자세 유지 중 성능 손실
  NO_TRACKING_LOSS        loss 0/3 — 생존 구간 추종 손실 없음
  MIXED                   그 밖 — 혼재·구분 불가

    python -B tools/go2_a047_tilt_vs_speed.py [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a043_tilt_onset as onset_mod  # noqa: E402

KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a047_tilt_vs_speed_20260929"
ARMS = (("A033", "go2_g_a033_a017_track_lin_vel_xy_150"), ("A047", "go2_g_a047_a033_flat_orientation_m05"))
SEEDS = (101, 202, 303)
CASES = ("combined_yaw_right", "rough_lateral", "push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y",
         "rough_forward", "slope_plus_20", "slope_minus_20", "dr")
F = ("time_s", "proj_grav_z", "height_rel", "speed_xy", "error_xy", "error_yaw")


def case_dir(arm: str, seed: int, case: str) -> Path:
    name = f"dr_seed_{seed}" if case == "dr" else case
    return KEEP / arm / "evaluation/candidate/cases" / f"seed_{seed}" / name


def load(path: Path) -> dict[int, list[dict]]:
    envs: dict[int, list[dict]] = {}
    stopped: set[int] = set()
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            e = int(r["env_id"])
            if e in stopped:
                continue
            if r["terminated"] == "1" or r["truncated"] == "1":
                stopped.add(e)
                if r["terminated"] == "1" and r.get("term_base_contact") == "1" and envs.get(e):
                    envs[e][-1]["base_contact_end"] = True
                continue
            row = {k: float(r[k]) for k in F}
            row["tilt"] = math.degrees(math.acos(max(-1.0, min(1.0, -row["proj_grav_z"]))))
            envs.setdefault(e, []).append(row)
    return envs


def mean(rows: list[dict], k: str):
    return round(st.fmean(r[k] for r in rows), 5) if rows else ""


def robot_rows(arm_label: str, arm: str, seed: int, case: str) -> tuple[list[dict], list[dict]]:
    envs = load(case_dir(arm, seed, case) / "steps.csv")
    out, survive_rows = [], []
    for e, rows in sorted(envs.items()):
        tf = onset_mod.fall_time(rows)
        ton = onset_mod.onset_time(rows, tf) if tf is not None else None
        ref = (ton if ton is not None else tf) if tf is not None else None
        end = rows[-1]["time_s"] + 1e-9
        surv_hi = (ref - 1.0) if ref is not None else end
        phases = {"early": [r for r in rows if 1.0 <= r["time_s"] < min(3.0, surv_hi)],
                  "survive": [r for r in rows if 1.0 <= r["time_s"] < surv_hi],
                  "pre_fail": [r for r in rows if ref is not None and ref - 1.0 <= r["time_s"] < ref]}
        rec = {"arm": arm_label, "case": case, "seed": seed, "env_id": e, "fell": int(tf is not None),
               "fall_t": "" if tf is None else tf, "onset_t": "" if ton is None else ton}
        for ph, sel in phases.items():
            rec[f"{ph}_rows"] = len(sel)
            for k in ("tilt", "speed_xy", "error_xy", "error_yaw", "height_rel"):
                rec[f"{ph}_{k}"] = mean(sel, k)
        out.append(rec)
        survive_rows += phases["survive"]
    return out, survive_rows


def med(recs: list[dict], k: str):
    xs = [r[k] for r in recs if r[k] != ""]
    return round(st.median(xs), 5) if xs else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    robots, seeds_rows, verdicts = [], [], []
    for case in CASES:
        per_seed = []
        for seed in SEEDS:
            data, surv = {}, {}
            for label, arm in ARMS:
                data[label], surv[label] = robot_rows(label, arm, seed, case)
                robots += data[label]
            m = st.median(r["tilt"] for r in surv["A033"])
            rec = {"case": case, "seed": seed, "a033_survive_tilt_median_deg": round(m, 4)}
            for label in ("A033", "A047"):
                d = data[label]
                fallen = [r for r in d if r["fell"]]
                rec[f"{label}_falls"] = len(fallen)
                for ph in ("early", "survive"):
                    for k in ("tilt", "speed_xy", "error_xy", "error_yaw", "height_rel"):
                        rec[f"{label}_{ph}_{k}_med"] = med(d, f"{ph}_{k}")
                for k in ("tilt", "speed_xy", "error_xy"):
                    rec[f"{label}_pre_fail_{k}_med"] = med(fallen, f"pre_fail_{k}")
                matched = [r for r in surv[label] if r["tilt"] <= m]
                rec[f"{label}_matched_rows"] = len(matched)
                rec[f"{label}_matched_error_xy"] = mean(matched, "error_xy")
                rec[f"{label}_matched_speed_xy"] = mean(matched, "speed_xy")
            per_seed.append(rec)
        seeds_rows += per_seed

        def count(k47, k33):
            return sum(1 for r in per_seed if r[k47] != "" and r[k33] != "" and r[k47] > r[k33])
        th = count("A047_survive_tilt_med", "A033_survive_tilt_med")
        ls = count("A047_survive_error_xy_med", "A033_survive_error_xy_med")
        ml = count("A047_matched_error_xy", "A033_matched_error_xy")
        et = count("A047_early_tilt_med", "A033_early_tilt_med")
        el = count("A047_early_error_xy_med", "A033_early_error_xy_med")
        es = sum(1 for r in per_seed if r["A047_early_speed_xy_med"] < r["A033_early_speed_xy_med"])
        if ls == 0:
            v = "NO_TRACKING_LOSS"
        elif th == 3 and ls == 3 and ml < 3:
            v = "EXCESS_TILT_WITH_LOSS"
        elif th < 3 and ml == 3:
            v = "POSTURE_KEPT_LOSS"
        else:
            v = "MIXED"
        verdicts.append({"case": case, "seeds_tilt_higher_survive": th, "seeds_error_higher_survive": ls,
                         "seeds_error_higher_matched_tilt": ml, "seeds_tilt_higher_early": et,
                         "seeds_error_higher_early": el, "seeds_speed_lower_early": es,
                         "falls_a033": sum(r["A033_falls"] for r in per_seed), "falls_a047": sum(r["A047_falls"] for r in per_seed),
                         "verdict": v})
    for name, rows in (("ROBOTS.csv", robots), ("SEEDS.csv", seeds_rows), ("VERDICT.csv", verdicts)):
        with (out / name).open("w", encoding="utf-8", newline="\n") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print(json.dumps({"robots": len(robots), "seed_rows": len(seeds_rows), "verdicts": {v["case"]: v["verdict"] for v in verdicts}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
