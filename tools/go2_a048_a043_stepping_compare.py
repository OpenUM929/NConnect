#!/usr/bin/env python3
"""A048 대 A043 험지 옆걸음 걸음 비교 — 기존 진단 재생 두 개만 쓴다 (2026-09-29, 사용자 요청 분석).

입력 (새 서버 실행 없음)
  A043: workspace/_keep/go2_g_a056_a043_diag_replay/diag/cases/seed_202/rough_lateral   (G-A056, diag v2)
  A048: workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases/seed_202/rough_lateral   (G-A052, diag v1)
  같은 case·같은 평가 seed 202·32대.  두 정책은 lin_vel_z_l2 한 항만 다르다(−1.5 대 −1.25).

로봇마다 첫 episode, 낙상·onset 은 tools/go2_a043_tilt_onset.py 정의.  비교 구간은 넘어지는 과정을 빼려고
1 s ~ (onset − 1 s), 낙상하지 않은 로봇은 1 s ~ 끝이다.  접지는 접촉 센서 문턱 1.0 N 이다.
값 (로봇별, 그 구간)
  vy            옆 속도 평균(steps.csv actual_vy, 명령 +0.3)
  vz_rms        몸통 상하 속도 RMS (lin_vel_b_z) — lin_vel_z_l2 가 벌점을 거는 양
  wxy_rms       roll·pitch 각속도 RMS (ang_vel_b_x·y) — ang_vel_xy_l2 가 벌점을 거는 양
  td_rate_lead  가는 쪽(왼쪽) 두 다리의 착지 횟수 / 초
  stance_lead   가는 쪽 다리 접지 한 번의 길이 중앙값(초)
  td_out_lead   가는 쪽 다리 착지 순간, 발이 몸(base 원점) 바깥으로 떨어진 수평 거리 중앙값(m)
  out_lead      가는 쪽 접지 발의 수평 바깥 거리 평균(m)
출력: reports/evidence/go2_a048_a043_stepping_20260929/ROBOTS.csv, SUMMARY.csv
한계: 정책 둘·평가 seed 하나.  생존/낙상 로봇 구성이 다르다.  비교이지 인과가 아니다.
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a043_tilt_onset as onset_mod  # noqa: E402

KEEP = ROOT / "workspace/_keep"
ARMS = {"A043": KEEP / "go2_g_a056_a043_diag_replay/diag/cases/seed_202/rough_lateral",
        "A048": KEEP / "go2_g_a052_a048_diag_replay/diag/cases/seed_202/rough_lateral"}
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a048_a043_stepping_20260929"
LEAD, TRAIL = ("FL", "RL"), ("FR", "RR")
DT = 0.02


def yaw_of(w, x, y, z):
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def windows(case_dir: Path) -> dict[int, tuple[float, float, int]]:
    envs = onset_mod.load(case_dir / "steps.csv")
    out = {}
    for e, rows in envs.items():
        tf = onset_mod.fall_time(rows)
        ton = onset_mod.onset_time(rows, tf) if tf is not None else None
        ref = (ton if ton is not None else tf) if tf is not None else None
        hi = (ref - 1.0) if ref is not None else rows[-1]["time_s"] + 1e-9
        out[e] = (1.0, hi, int(tf is not None))
    return out


def arm_rows(label: str, case_dir: Path) -> list[dict]:
    win = windows(case_dir)
    base, vy = {}, {}
    with (case_dir / "steps.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            base[(int(r["step"]), int(r["env_id"]))] = (float(r["root_x"]), float(r["root_y"]))
            vy[(int(r["step"]), int(r["env_id"]))] = float(r["actual_vy"])
    seq: dict[int, list[dict]] = {}
    with gzip.open(case_dir / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            step, e = int(r["step"]), int(r["env_id"])
            lo, hi, _ = win.get(e, (0, -1, 0))
            t = step * DT
            if not (lo <= t < hi):
                continue
            bx, by = base[(step, e)]
            yaw = yaw_of(*(float(r[k]) for k in ("quat_w", "quat_x", "quat_y", "quat_z")))
            x = {"t": t, "vy": vy[(step, e)], "vz": float(r["lin_vel_b_z"]),
                 "wxy2": float(r["ang_vel_b_x"]) ** 2 + float(r["ang_vel_b_y"]) ** 2}
            for L in LEAD + TRAIL:
                dx, dy = float(r[f"{L}_pos_x"]) - bx, float(r[f"{L}_pos_y"]) - by
                yh = -math.sin(yaw) * dx + math.cos(yaw) * dy
                x[L] = (float(r[f"{L}_force_z"]) > 1.0, (1 if L[1] == "L" else -1) * yh)
            seq.setdefault(e, []).append(x)
    out = []
    for e in sorted(seq):
        s = seq[e]
        dur = len(s) * DT
        if dur < 1.0:
            continue
        td, stance_len, td_out, out_lead = 0, [], [], []
        for L in LEAD:
            run = 0
            for a, b in zip(s, s[1:]):
                if b[L][0]:
                    run += 1
                    out_lead.append(b[L][1])
                    if not a[L][0]:
                        td += 1
                        td_out.append(b[L][1])
                elif run:
                    stance_len.append(run * DT)
                    run = 0
        out.append({"arm": label, "env_id": e, "fell": win[e][2], "window_s": round(dur, 2),
                    "vy": round(st.fmean(x["vy"] for x in s), 4),
                    "vz_rms": round(math.sqrt(st.fmean(x["vz"] ** 2 for x in s)), 4),
                    "wxy_rms": round(math.sqrt(st.fmean(x["wxy2"] for x in s)), 4),
                    "td_rate_lead": round(td / dur, 3),
                    "stance_lead": round(st.median(stance_len), 3) if stance_len else "",
                    "td_out_lead": round(st.median(td_out), 4) if td_out else "",
                    "out_lead": round(st.fmean(out_lead), 4) if out_lead else ""})
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    robots = []
    for label, d in ARMS.items():
        robots += arm_rows(label, d)
    keys = ["vy", "vz_rms", "wxy_rms", "td_rate_lead", "stance_lead", "td_out_lead", "out_lead"]
    summary = []
    for label in ARMS:
        for grp, cond in (("all", lambda r: True), ("fell", lambda r: r["fell"] == 1), ("survived", lambda r: r["fell"] == 0)):
            sel = [r for r in robots if r["arm"] == label and cond(r)]
            rec = {"arm": label, "group": grp, "n": len(sel)}
            for k in keys:
                xs = [r[k] for r in sel if r[k] != ""]
                rec[f"{k}_median"] = round(st.median(xs), 4) if xs else ""
            summary.append(rec)
    for name, rows in (("ROBOTS.csv", robots), ("SUMMARY.csv", summary)):
        with (OUT / name).open("w", encoding="utf-8", newline="\n") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print(json.dumps({"robots": len(robots)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
