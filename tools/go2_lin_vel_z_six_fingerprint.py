#!/usr/bin/env python3
"""lin_vel_z 여섯 점(A033·A044·A043·A050·A048·A049) 걸음 지문 — 학습 기록 + 평가 기록 (2026-09-29, 사용자 요청).

질문: −1.5(A043)는 왜 계단을 오르고 밀침·험지·우회전에서 무너졌나, −1.25(A048)는 왜 반대인가.
입력 (새 서버 실행 없음)
  학습: workspace/_keep/<run>/training/logs/rsl_rl/quadruped/*/events*  (tools/tfcurve.py로 읽음)
        iter 850~949 평균(평가 체크포인트 900 부근).
  평가: workspace/_keep/<run>/evaluation/candidate/cases/seed_{101,202,303}/<case>/steps.csv
        로봇마다 첫 episode, 1~3초(낙상이면 낙상 시각 전까지). 낙상 정의 tools/go2_a043_tilt_onset.py.
값: height 지형 대비 몸 높이 중앙값, tilt 기울기(도), speed 수평 속도, vz_rms root_z 0.02초 차분 RMS(월드 좌표 상하 흔들림),
    err_xy 추종 오차 평균. 로봇별 값의 중앙값.
출력: reports/evidence/go2_lin_vel_z_six_fingerprint_20260929/TRAIN.csv, EVAL.csv
한계: 각 설정 학습 seed 42 한 번. 설정 사이 차이와 학습 재현 흔들림을 구분할 수 없다.
"""
from __future__ import annotations

import csv
import glob
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a043_tilt_onset as om  # noqa: E402
import tfcurve  # noqa: E402

K = ROOT / "workspace/_keep"
RUNS = [("A033", -2.0, "go2_g_a033_a017_track_lin_vel_xy_150"), ("A044", -1.75, "go2_g_a044_a033_lin_vel_z_m175"),
        ("A043", -1.5, "go2_g_a043_a033_lin_vel_z_m15"), ("A050", -1.375, "go2_g_a050_a033_lin_vel_z_m1375"),
        ("A048", -1.25, "go2_g_a048_a033_lin_vel_z_m125"), ("A049", -1.0, "go2_g_a049_a033_lin_vel_z_m1")]
CASES = ["forward_nominal", "rough_lateral", "rough_forward", "combined_yaw_right", "push_pos_y", "stairs_15_down"]
TAGS = ["Curriculum/terrain_levels", "Episode_Reward/lin_vel_z_l2", "Episode_Reward/ang_vel_xy_l2",
        "Episode_Reward/track_lin_vel_xy_exp", "Episode_Reward/feet_air_time", "Episode_Termination/base_contact",
        "Metrics/base_velocity/error_vel_xy", "Policy/mean_std"]
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_lin_vel_z_six_fingerprint_20260929"


def train_rows():
    rows = []
    for arm, w, d in RUNS:
        p = glob.glob(str(K / d / "training/logs/rsl_rl/quadruped/*/events*"))[0]
        s: dict[str, list[float]] = {}
        for t, v in tfcurve.scalars(p):
            s.setdefault(t, []).append(v)
        rec = {"arm": arm, "lin_vel_z": w}
        for t in TAGS:
            win = s[t][850:950]
            rec[t.split("/")[-1]] = round(st.fmean(win), 4)
        rec["lin_vel_z_raw"] = round(rec["lin_vel_z_l2"] / w, 4)  # 가중치로 나눈 원 크기
        rows.append(rec)
    return rows


def eval_rows():
    rows = []
    for arm, w, d in RUNS:
        for c in CASES:
            H, T, S, VZ, E = [], [], [], [], []
            for seed in (101, 202, 303):
                p = K / d / "evaluation/candidate/cases" / f"seed_{seed}" / c / "steps.csv"
                envs = om.load(p)
                rz: dict[int, list[tuple[float, float, float]]] = {}
                with p.open(encoding="utf-8") as fh:
                    for r in csv.DictReader(fh):
                        rz.setdefault(int(r["env_id"]), []).append((float(r["time_s"]), float(r["root_z"]), float(r["error_xy"])))
                for e, rs in envs.items():
                    tf = om.fall_time(rs)
                    hi = min(3.0, tf if tf else 99.0)
                    sel = [r for r in rs if 1.0 <= r["time_s"] < hi]
                    if len(sel) < 10:
                        continue
                    H.append(st.median(r["height_rel"] for r in sel))
                    T.append(st.median(r["tilt"] for r in sel))
                    S.append(st.median(math.hypot(r["actual_vx"], r["actual_vy"]) for r in sel))
                    z = [x for x in rz[e] if 1.0 <= x[0] < hi]
                    vz = [(b[1] - a[1]) / 0.02 for a, b in zip(z, z[1:]) if 0 < b[0] - a[0] < 0.03]
                    if vz:
                        VZ.append(math.sqrt(st.fmean(v * v for v in vz)))
                    E.append(st.fmean(x[2] for x in z))
            rows.append({"arm": arm, "lin_vel_z": w, "case": c, "robots": len(H), "height_m": round(st.median(H), 3),
                         "tilt_deg": round(st.median(T), 2), "speed": round(st.median(S), 3),
                         "vz_rms": round(st.median(VZ), 3), "err_xy": round(st.median(E), 3)})
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (("TRAIN.csv", train_rows()), ("EVAL.csv", eval_rows())):
        with (OUT / name).open("w", encoding="utf-8", newline="\n") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            wr.writeheader()
            wr.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
