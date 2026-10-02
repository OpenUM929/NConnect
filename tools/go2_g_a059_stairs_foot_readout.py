"""G-A059 판독 — 계단을 오르는 로봇의 발 들기 높이·앞 들기 각도·디딤판 기준 몸높이 (읽기 전용).

목적: 15cm 계단 성공 상태의 기준을 정의한다(사용자 2026-10-01). 성공(판정 없이 ≥2단)과 실패 집단을 같은 정의로
나눠 적는다. 원인을 판정하지 않는다. 정의는 결과를 보기 전에 고정했다(계획
upload/plan/GO2_G_A059_A043_STAIRS_DIAG_PLAN_20261001.md §3).

입력  압축 푼 회수 폴더(go2_g_a059_a043_stairs_diag_replay/)의 diag/cases/seed_101/<case>/{steps.csv,diag.csv.gz}
형상  tools/go2_stairs_tread_height.py 와 같다. 타일 중심 = 첫 행 몸통에 가장 가까운 격자점(x = 0, y = 4 + 8k),
      첫 모서리 R0 = 1.2 m, 디딤판 0.3 m, 6단. 중심이 격자로 정해지므로 A052 의 중심 맞춤은 쓰지 않고,
      모서리 불확실성 u 는 스캐너 광선 간격의 절반 0.05 m 로 둔다.
정의  z0 = 첫 행 네 발 아래 지형(terrain_z_near) 최솟값(가운데 판). 발바닥 높이 zf = 발 pos_z - z0 - 0.023(발 반지름).
      d = 발의 체비셰프 거리 - R0 (음수 = 첫 모서리 앞, 0~0.3 = 첫 디딤판).
      edge_lift  = 발이 처음 d >= -0.15 가 된 행부터 처음 d > U(0.05) 가 되기 전(또는 끝)까지 zf 최댓값 —
                   첫 모서리를 넘기 직전까지 든 높이. 첫 디딤판 윗면 높이 h 와 비교한다(zf >= h 라야 단 위로 넘는다).
                   [정정 2026-10-01, G-A052 A048 자료로 판독기를 먼저 돌린 뒤] 초판은 끝을 d > 0.3 으로 잡아 첫 단에
                   올라선 발이 둘째 단으로 들리는 높이(약 2h)까지 섞였다. 결과에 맞춘 것이 아니라 구간 정의 오류의 수정이다.
      flat_apex  = t 1~2 초, d < -0.3 인 행의 zf 최댓값(평지 걸음의 발 최고점).
      kind       = tools/go2_a052_stairs_edge_trajectory.classify(같은 정의: early/in_band/late/never/passed_low/no_entry).
      nose_up    = 몸통 pitch(쿼터니언)의 부호를 바꾼 값(앞이 들리면 +), 몸통 d 가 -0.4~0.3 인 행의 최댓값(도).
      body_over_tread = root_z - 몸통 아래 디딤판 높이(z0 + 단 수 x h), 몸통 d 0.1~0.3 행의 중앙값.
집단  steps.csv 로 계산한 내부 판정 기준(영상 확인 아님): clean(≥2단·판정 없음), ge2_then_judged,
      judged_before_ge2, lt2_judged, lt2_unjudged (tools/go2_stairs_tread_height.py 와 같은 규칙).
첫 episode 만 읽는다. 한 정책·한 평가 seed. 성공 로봇의 값은 성공의 상태 기술이지 인과 조건이 아니다.

    python -B tools/go2_g_a059_stairs_foot_readout.py <회수 폴더> [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import go2_a052_stairs_edge_trajectory as traj  # noqa: E402
from go2_failure_events import classify as posture_classify  # noqa: E402
from go2_state_order_sink_check import t_ge2  # noqa: E402
from go2_state_outcome import first_episode, load  # noqa: E402
from go2_stairs_tread_height import R0, centre, cheb, level  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a059_readout"
SEED = 101
CASES = (("stairs_15_down", 0.15), ("stairs_10_down", 0.10))
FEET = ("FL", "FR", "RL", "RR")
FOOT_R, U, FORCE_ON, FORCE_TOP = 0.023, 0.05, 1.0, 5.0
GROUPS = ("clean", "ge2_then_judged", "judged_before_ge2", "lt2_judged", "lt2_unjudged")


def group_of(rows, h):
    c = posture_classify(rows)
    term = next((i for i, r in enumerate(rows) if r["term"]), None)
    starts = [i for i in (c["union_fall_start"], term) if i is not None]
    fall_t = rows[min(starts)]["time_s"] if starts else None
    tg = t_ge2(first_episode(rows), h)
    if tg is not None:
        g = "clean" if fall_t is None else ("ge2_then_judged" if fall_t > tg else "judged_before_ge2")
    else:
        g = "lt2_unjudged" if fall_t is None else "lt2_judged"
    return g, fall_t


def nose_up_deg(r):
    w, x, y, z = (float(r[k]) for k in ("quat_w", "quat_x", "quat_y", "quat_z"))
    s = max(-1.0, min(1.0, 2 * (w * y - z * x)))
    return -math.degrees(math.asin(s))


def load_diag(path):
    by = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            by.setdefault(int(r["env_id"]), {})[int(r["step"])] = r
    return by


def q(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def read_case(h_dir: Path, case: str, h: float):
    d = h_dir / "diag" / "cases" / f"seed_{SEED}" / case
    steps = load(d / "steps.csv")
    diag = load_diag(d / "diag.csv.gz")
    envs, feet = [], []
    for env, rows in sorted(steps.items()):
        g, fall_t = group_of(rows, h)
        ep = first_episode(rows)
        end = fall_t if fall_t is not None else 20.0
        c = centre(rows[0]["root_x"], rows[0]["root_y"])
        dr = diag.get(env, {})
        joined = [(r, dr.get(round(r["time_s"] / 0.02))) for r in ep if r["time_s"] <= end + 1e-9]
        joined = [(r, x) for r, x in joined if x is not None]
        if not joined:
            continue
        z0 = min(float(joined[0][1][f + "_terrain_z_near_derived"]) for f in FEET)
        nose = [nose_up_deg(x) for r, x in joined if -0.4 <= cheb(r["root_x"], r["root_y"], c) - R0 < 0.3]
        bot = [r["root_z"] - (z0 + level(cheb(r["root_x"], r["root_y"], c)) * h)
               for r, x in joined if 0.1 <= cheb(r["root_x"], r["root_y"], c) - R0 < 0.3]
        envs.append({"case": case, "env": env, "group": g, "fall_t": fall_t,
                     "nose_up_max_deg": max(nose) if nose else None,
                     "body_over_tread": st.median(bot) if len(bot) >= 5 else None})
        for f in FEET:
            t, dd, zf, ld, top = [], [], [], [], []
            for r, x in joined:
                fx, fy = float(x[f + "_pos_x"]), float(x[f + "_pos_y"])
                fz = float(x[f + "_force_z"])
                foot_z = float(x[f + "_pos_z"]) - z0
                t.append(round(r["time_s"], 2))
                dd.append(max(abs(fx - c[0]), abs(fy - c[1])) - R0)
                zf.append(foot_z - FOOT_R)
                ld.append(fz > FORCE_ON)
                top.append(fz > FORCE_TOP and float(x[f + "_terrain_z_near_derived"]) - z0 > 0.5 * h and foot_z > 0.8 * h)
            kind = traj.classify(t, dd, zf, ld, top, h, U, end)
            i0 = next((i for i, v in enumerate(dd) if v >= -0.15), None)
            lift = None
            if i0 is not None:
                i1 = next((i for i in range(i0, len(dd)) if dd[i] > U), len(dd))
                lift = max(zf[i0:i1]) if i1 > i0 else None
            apex = [zf[i] for i in range(len(t)) if 1.0 <= t[i] < 2.0 and dd[i] < -0.3]
            feet.append({"case": case, "env": env, "group": g, "foot": f, "pair": "front" if f[0] == "F" else "hind",
                         "edge_lift": lift, "reached_h": None if lift is None else int(lift >= h),
                         "flat_apex": max(apex) if apex else None, **kind})
    return envs, feet


def summarize(envs, feet):
    out = []
    for case, h in CASES:
        for g in GROUPS:
            e = [r for r in envs if r["case"] == case and r["group"] == g]
            if not e:
                continue
            row = {"case": case, "h": h, "group": g, "robots": len(e)}
            for k in ("nose_up_max_deg", "body_over_tread"):
                v = [r[k] for r in e if r[k] is not None]
                row[f"{k}_n"] = len(v)
                row[f"{k}_med"] = st.median(v) if v else None
                row[f"{k}_q25"] = q(v, .25) if v else None
                row[f"{k}_q75"] = q(v, .75) if v else None
            for pair in ("front", "hind"):
                fs = [r for r in feet if r["case"] == case and r["group"] == g and r["pair"] == pair]
                lifts = [r["edge_lift"] for r in fs if r["edge_lift"] is not None]
                apex = [r["flat_apex"] for r in fs if r["flat_apex"] is not None]
                row[f"{pair}_feet"] = len(fs)
                row[f"{pair}_edge_lift_n"] = len(lifts)
                row[f"{pair}_edge_lift_med"] = st.median(lifts) if lifts else None
                row[f"{pair}_edge_lift_q25"] = q(lifts, .25) if lifts else None
                row[f"{pair}_edge_lift_q75"] = q(lifts, .75) if lifts else None
                row[f"{pair}_reached_h"] = sum(1 for v in lifts if v >= h)
                row[f"{pair}_flat_apex_med"] = st.median(apex) if apex else None
                for k in traj.KINDS:
                    row[f"{pair}_{k}"] = sum(1 for r in fs if r["kind"] == k)
            out.append(row)
    return out


def write(path, data):
    keys = list(dict.fromkeys(k for d in data for k in d)) or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(data)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("harvest")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    h_dir, out = Path(a.harvest), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    envs, feet = [], []
    for case, h in CASES:
        e, f = read_case(h_dir, case, h)
        envs += e
        feet += f
    summary = summarize(envs, feet)
    write(out / "PER_ENV.csv", envs)
    write(out / "PER_FOOT.csv", feet)
    write(out / "GROUP_SUMMARY.csv", summary)
    print(f"robots={len(envs)} feet={len(feet)} groups={len(summary)} -> {out}")
    return 0 if envs else 1


if __name__ == "__main__":
    raise SystemExit(main())
