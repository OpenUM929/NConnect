#!/usr/bin/env python3
"""A043 기울어짐 시작 원인 분석 — 저장된 평가 steps.csv만 쓴다 (2026-09-28).

질문 (사용자 원칙 2단계: 왜 넘어지는가):
  Q1 보행 자체의 차이 — 넘어지지 않은 구간(정상 보행 창)에서 A043의 옆 속도·회전·기울기 흔들림이
     A048·A033과 다른가, 우회전과 좌회전이 비대칭인가.
  Q2 넘어지기 직전 — 기울어짐 시작(18° 마지막 상향 통과) 전 1초에 무엇이 생존 로봇과 다른가.
  Q3 험지 — 기울어짐 시작 직전 발밑 지형 변화가 생존 로봇의 같은 시각보다 큰가.

정의 (새 판정 문턱이 아니라 분석 편의값; 낙상 판정은 평가기와 같다):
  기울기 각 tilt_deg = acos(-proj_grav_z) (도). 낙상 = 0.5초 유예 뒤 (proj_grav_z > -0.5 또는 height_rel < 0.18)이
  0.5초 연속된 첫 시각(평가기 posture_gate_v2와 같은 규칙, tools/go2_failure_events.py와 같다).
  onset = 낙상 시각 이전 마지막으로 tilt_deg가 18°를 위로 넘은 시각.
  정상 보행 창 = 2.0초 ~ min(8.0초, onset−1.5초). 생존 로봇은 2.0~8.0초.
  직전 창 = [onset−1.0, onset]. 생존 대조 = 같은 arm·seed 낙상 onset 중앙값의 같은 창.
  옆 속도 초과 = actual_vy − cmd_vy (몸통 좌표, 부호 포함). 회전 오차 = actual_wz − cmd_wz.
  지형 변화 = 창 안 terrain_z 최댓값 − 최솟값.
평가 기록에는 발·관절·roll/pitch 분리 채널이 없다 — 기울기 방향(roll인지 pitch인지)은 알 수 없다.

    python -B tools/go2_a043_tilt_onset.py
출력: workspace/training/quadruped/reports/evidence/go2_a043_tilt_onset_20260928/
"""
from __future__ import annotations

import csv
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a043_tilt_onset_20260928"
ARMS = (("A043", "go2_g_a043_a033_lin_vel_z_m15"),
        ("A048", "go2_g_a048_a033_lin_vel_z_m125"),
        ("A033", "go2_g_a033_a017_track_lin_vel_xy_150"))
CASES = ("combined_yaw_right", "combined_yaw_left", "rough_lateral")
SEEDS = (101, 202, 303)
DT, GRACE, HOLD = 0.02, 0.5, 0.5
F = ("time_s", "cmd_vx", "cmd_vy", "cmd_wz", "actual_vx", "actual_vy", "actual_wz",
     "proj_grav_z", "terrain_z", "height_rel")


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


def fall_time(rows: list[dict]) -> float | None:
    run = 0
    for i, r in enumerate(rows):
        if r["time_s"] < GRACE:
            continue
        bad = r["proj_grav_z"] > -0.5 or r["height_rel"] < 0.18
        run = run + 1 if bad else 0
        if run * DT >= HOLD:
            return rows[i - run + 1]["time_s"]
    # 자세 판정이 0.5초 이어지기 전에 몸통 접촉으로 종료된 로봇도 낙상이다(평가기 pessimistic 집계와 같게).
    if rows and rows[-1].get("base_contact_end"):
        return rows[-1]["time_s"]
    return None


def onset_time(rows: list[dict], t_fall: float) -> float | None:
    t = None
    for a, b in zip(rows, rows[1:]):
        if b["time_s"] > t_fall:
            break
        if a["tilt"] < 18.0 <= b["tilt"]:
            t = b["time_s"]
    return t


def window(rows: list[dict], lo: float, hi: float) -> list[dict]:
    return [r for r in rows if lo <= r["time_s"] < hi]


def stats(win: list[dict], prefix: str) -> dict:
    if len(win) < 10:
        return {}
    m = lambda k: statistics.fmean(r[k] for r in win)  # noqa: E731
    tilts = [r["tilt"] for r in win]
    ter = [r["terrain_z"] for r in win]
    return {f"{prefix}_vx": m("actual_vx"), f"{prefix}_vy": m("actual_vy"), f"{prefix}_wz": m("actual_wz"),
            f"{prefix}_vy_excess": statistics.fmean(r["actual_vy"] - r["cmd_vy"] for r in win),
            f"{prefix}_wz_err": statistics.fmean(r["actual_wz"] - r["cmd_wz"] for r in win),
            f"{prefix}_tilt_mean": statistics.fmean(tilts), f"{prefix}_tilt_std": statistics.pstdev(tilts),
            f"{prefix}_tilt_max": max(tilts), f"{prefix}_height": m("height_rel"),
            f"{prefix}_terrain_range": max(ter) - min(ter)}


LEAD_WIN = 3.0   # onset 전 몇 초를 보는가 (분석 편의값)
K_SIGMA = 2.0    # 자기 정상 보행 창 평균에서 표준편차의 몇 배를 벗어나면 이탈로 보는가 (분석 편의값)
SMOOTH = 5       # 0.1초 이동 평균


def _smooth(v: list[float]) -> list[float]:
    out = []
    for i in range(len(v)):
        seg = v[max(0, i - SMOOTH + 1):i + 1]
        out.append(sum(seg) / len(seg))
    return out


def departure_start(times: list[float], vals: list[float], mu: float, sd: float, sign: int) -> float | None:
    """onset 쪽 끝에서 거꾸로 올라가며, 이탈(부호 방향으로 mu ± K·sd 밖)이 끊김 없이 이어진 구간의 시작 시각."""
    thr = mu + sign * K_SIGMA * max(sd, 1e-6)
    out = lambda x: (x > thr) if sign > 0 else (x < thr)  # noqa: E731
    if not out(vals[-1]):
        return None
    i = len(vals) - 1
    while i > 0 and out(vals[i - 1]):
        i -= 1
    return times[i]


def lead_lag(rows: list[dict], ton: float, steady: list[dict], lat_sign: int) -> dict:
    """기울기 이탈과 옆 속도 이탈 중 무엇이 먼저 시작됐나 (onset 직전 LEAD_WIN초)."""
    win = window(rows, ton - LEAD_WIN, ton + 0.02)
    if len(win) < 20 or len(steady) < 20:
        return {}
    t = [r["time_s"] for r in win]
    tilt = _smooth([r["tilt"] for r in win])
    vy = _smooth([lat_sign * (r["actual_vy"] - r["cmd_vy"]) for r in win])
    wz = _smooth([abs(r["actual_wz"] - r["cmd_wz"]) for r in win])
    s_tilt = [r["tilt"] for r in steady]
    s_vy = [lat_sign * (r["actual_vy"] - r["cmd_vy"]) for r in steady]
    s_wz = [abs(r["actual_wz"] - r["cmd_wz"]) for r in steady]
    res = {"lead_tilt_start": departure_start(t, tilt, statistics.fmean(s_tilt), statistics.pstdev(s_tilt), +1),
           "lead_vy_start": departure_start(t, vy, statistics.fmean(s_vy), statistics.pstdev(s_vy), +1),
           "lead_wzerr_start": departure_start(t, wz, statistics.fmean(s_wz), statistics.pstdev(s_wz), +1)}
    for k in list(res):
        if res[k] is not None:
            res[k + "_rel"] = round(res[k] - ton, 2)
    return res


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict] = []
    for arm, run in ARMS:
        for case in CASES:
            for seed in SEEDS:
                p = KEEP / run / "evaluation/candidate/cases" / f"seed_{seed}" / case / "steps.csv"
                envs = load(p)
                recs = []
                for e, rows in sorted(envs.items()):
                    tf = fall_time(rows)
                    ton = onset_time(rows, tf) if tf is not None else None
                    rec = {"arm": arm, "case": case, "seed": seed, "env": e,
                           "outcome": "FALL" if tf is not None else "SURVIVE", "fall_t": tf, "onset_t": ton}
                    hi = min(8.0, ton - 1.5) if ton is not None else 8.0
                    rec.update(stats(window(rows, 2.0, hi), "steady"))
                    if ton is not None:
                        rec.update(stats(window(rows, ton - 1.0, ton), "pre"))
                        # 옆 방향 부호: 명령 옆 속도 방향을 +로 둔다(우회전 cmd_vy<0 → 오른쪽이 +).
                        lat = -1 if rows[0]["cmd_vy"] < 0 else 1
                        rec.update(lead_lag(rows, ton, window(rows, 2.0, hi), lat))
                    recs.append((rec, rows))
                onsets = [r["onset_t"] for r, _ in recs if r["onset_t"] is not None]
                if onsets:
                    t0 = statistics.median(onsets)
                    for r, rows in recs:
                        if r["outcome"] == "SURVIVE":
                            r.update(stats(window(rows, t0 - 1.0, t0), "ctrl"))
                rows_out += [r for r, _ in recs]
    cols: list[str] = []
    for r in rows_out:
        cols += [k for k in r if k not in cols]
    with (OUT / "ROBOTS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows_out)

    def med(pool, key):
        v = [r[key] for r in pool if r.get(key) is not None]
        return round(statistics.median(v), 4) if v else None

    summary = []
    keys = ("vx", "vy", "wz", "vy_excess", "wz_err", "tilt_mean", "tilt_std", "tilt_max", "height", "terrain_range")
    for arm, _ in ARMS:
        for case in CASES:
            pool = [r for r in rows_out if r["arm"] == arm and r["case"] == case]
            for group, sel, pref in (("all_steady", pool, "steady"),
                                     ("survive_steady", [r for r in pool if r["outcome"] == "SURVIVE"], "steady"),
                                     ("fall_steady", [r for r in pool if r["outcome"] == "FALL"], "steady"),
                                     ("fall_pre1s", [r for r in pool if r["outcome"] == "FALL"], "pre"),
                                     ("survive_ctrl1s", [r for r in pool if r["outcome"] == "SURVIVE"], "ctrl")):
                row = {"arm": arm, "case": case, "group": group, "n": len(sel)}
                row.update({k: med(sel, f"{pref}_{k}") for k in keys})
                summary.append(row)
    with (OUT / "SUMMARY.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(summary)
    print(OUT / "SUMMARY.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
