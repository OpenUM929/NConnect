"""성공한 로봇과 실패한 로봇의 실제 상태값 (2026-10-01, 읽기 전용).

시나리오의 핵심 구간에서 로봇이 실제로 어떤 상태였는지를 로봇마다 잰다. 판정 수가 아니라 상태값이다.
원자료: 각 회수물 evaluation/candidate/cases/seed_*/<case>/steps.csv (모든 정책, 평가 seed 3 x 32대).
성공/실패는 내부 자세 게이트 판정(go2_state_outcome 와 같은 타이머) 기준이다. 계단 성공 = ≥2단 + 판정 없음.
구간은 첫 episode, 판정 시작 전 행만 쓴다(실패 로봇은 넘어지기 전 상태).

상태값 (단위)
  공통(t 1 s ~ 판정 전 또는 20 s)
    h_med      몸높이 중앙값 = root_z - 스캐너 평균 지형 (m)
    h_std      몸높이 표준편차 = 상하 출렁임 (m)
    tilt_med / tilt_p90   몸통 기울기 크기 acos(-proj_grav_z) (도)
    v_cmd      명령 방향 몸통 속도 중앙값 (m/s)
    v_side     명령에 수직인 몸통 속도 크기 중앙값 (m/s) — 옆으로 새는 정도
    wz_med     yaw 각속도 중앙값 (rad/s)
    vz_p90     세계 좌표 수직 속도 크기 90분위 (m/s, root_z 차분)
  계단(몸통 기준 첫 모서리 거리 d, tools/go2_stairs_tread_height.py 형상)
    approach_h   d -0.6~-0.2 디딤판 기준 몸높이 (m)
    tread1_h     d 0.1~0.3 디딤판 기준 몸높이 (m)
    edge_vz_max  d -0.3~0.3 최대 상승 속도 (m/s)
    edge_tilt_max d -0.3~0.3 최대 기울기 (도)
    edge_v       d -0.3~0.3 명령 방향 속도 중앙값 (m/s)
    cross_s      d -0.2 에서 0.3 까지 걸린 시간 (s, 도달 못 하면 없음)
    edge_full    관측 구간 안에 d 0.3 까지 지났는가 (0 이면 모서리 값이 관측 끝에서 잘림)
    edge_status  full / judged_in_edge / judged_after_backing / unjudged_not_crossed / not_reached
    edge_dwell_s 모서리 구간 최초 진입부터 마지막 관측 표본까지 경과 시간 (s, 구간 내 체류 시간 아님)
  밀침(이벤트마다, tools/go2_state_outcome.py PER_PUSH_EVENT 재사용)
    pre_h, peak_tilt_1p5(밀친 뒤 1.5 s 최대 기울기), min_h_1p5(최저 몸높이)
"""
from __future__ import annotations

import csv
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_failure_events import classify  # noqa: E402
from go2_state_order_sink_check import t_ge2  # noqa: E402
from go2_state_outcome import ARMS, KEEP, SEEDS, STATIONARY, first_episode, load, tilt_deg  # noqa: E402
from go2_stairs_tread_height import R0, centre, cheb, level  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "workspace/training/quadruped/reports/evidence"
OUT = EV / "go2_robot_state_profile_20261001"
CASES = {"stairs_15_down": 0.15, "stairs_10_down": 0.10, "rough_lateral": None, "rough_forward": None,
         "combined_yaw_right": None, "combined_yaw_left": None}
ZC = {0.15: -1.05, 0.10: -0.70}  # centre platform height (CHECKS.json of go2_stairs_tread_height)
STATE = ("h_med", "h_std", "tilt_med", "tilt_p90", "v_cmd", "v_side", "wz_med", "vz_p90")
STAIR = ("approach_h", "tread1_h", "edge_vz_max", "edge_tilt_max", "edge_v", "cross_s")


def p(v, q):
    s = sorted(v)
    if not s:
        return None
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def med(v):
    v = [x for x in v if x is not None]
    return st.median(v) if v else None


def env_state(rows, case, h):
    c = classify(rows)
    term = next((i for i, r in enumerate(rows) if r["term"]), None)
    starts = [i for i in (c["union_fall_start"], term) if i is not None]
    fall_t = rows[min(starts)]["time_s"] if starts else None
    ep = first_episode(rows)
    if h is not None:
        tg = t_ge2(ep, h)
        success = int(tg is not None and fall_t is None)
    else:
        success = int(fall_t is None)
    w = [r for r in ep if r["time_s"] >= 1 and (fall_t is None or r["time_s"] < fall_t)]
    rec = {"success": success, "fall_t": fall_t, "rows": len(w)}
    if len(w) < 25:
        return rec
    hs = [r["height_rel"] for r in w if r["height_rel"] is not None]
    tl = [tilt_deg(r["proj_grav_z"]) for r in w]
    vc, vs = [], []
    for r in w:
        n = math.hypot(r["cmd_vx"], r["cmd_vy"])
        if n > 0:
            ux, uy = r["cmd_vx"] / n, r["cmd_vy"] / n
            vc.append(r["actual_vx"] * ux + r["actual_vy"] * uy)
            vs.append(abs(-r["actual_vx"] * uy + r["actual_vy"] * ux))
    vz = [abs(b["root_z"] - a["root_z"]) / 0.02 for a, b in zip(w, w[1:])]
    rec.update(h_med=med(hs), h_std=st.pstdev(hs) if len(hs) > 1 else None, tilt_med=med(tl), tilt_p90=p(tl, .9),
               v_cmd=med(vc), v_side=med(vs), wz_med=med([r["actual_wz"] for r in w]), vz_p90=p(vz, .9))
    # fixed window 1 <= t < 4 s, only for robots not judged before 5 s (no fall dynamics inside the window)
    if fall_t is None or fall_t >= 5.0:
        fw = [r for r in ep if 1 <= r["time_s"] < 4]
        if len(fw) >= 100:
            fh = [r["height_rel"] for r in fw if r["height_rel"] is not None]
            ftl = [tilt_deg(r["proj_grav_z"]) for r in fw]
            fv = []
            for r in fw:
                n = math.hypot(r["cmd_vx"], r["cmd_vy"])
                if n > 0:
                    fv.append((r["actual_vx"] * r["cmd_vx"] + r["actual_vy"] * r["cmd_vy"]) / n)
            fz = [abs(b["root_z"] - a["root_z"]) / 0.02 for a, b in zip(fw, fw[1:])]
            rec.update(w_h=med(fh), w_h_std=st.pstdev(fh), w_tilt_med=med(ftl), w_tilt_p90=p(ftl, .9),
                       w_v_cmd=med(fv), w_vz_p90=p(fz, .9))
    if h is not None:
        cc = centre(ep[0]["root_x"], ep[0]["root_y"])
        zc = ZC[h]
        dd = [cheb(r["root_x"], r["root_y"], cc) - R0 for r in w]
        bot = [r["root_z"] - (zc + level(d + R0) * h) for r, d in zip(w, dd)]
        app = [b for b, d in zip(bot, dd) if -0.6 <= d < -0.2]
        t1 = [b for b, d in zip(bot, dd) if 0.1 <= d < 0.3]
        edge = [i for i, d in enumerate(dd) if -0.3 <= d < 0.3]
        rec["approach_h"] = med(app) if len(app) >= 5 else None
        rec["tread1_h"] = med(t1) if len(t1) >= 5 else None
        if edge:
            rec["edge_vz_max"] = max((w[i + 1]["root_z"] - w[i]["root_z"]) / 0.02 for i in edge if i + 1 < len(w)) if len(edge) > 1 else None
            rec["edge_tilt_max"] = max(tl[i] for i in edge)
            rec["edge_v"] = med([vc[i] for i in edge if i < len(vc)])
        i0 = next((i for i, d in enumerate(dd) if d >= -0.2), None)
        i1 = next((i for i, d in enumerate(dd) if d >= 0.3), None)
        rec["cross_s"] = (w[i1]["time_s"] - w[i0]["time_s"]) if i0 is not None and i1 is not None and i1 > i0 else None
        # 1 = 관측 구간(판정 전 또는 첫 episode 끝까지) 안에 모서리 구간 d -0.3~0.3 을 끝까지 지남.
        # 0 의 사정은 edge_status 로 나눈다(판정 때문에 잘렸는지, 판정 없이 못 지났는지).
        rec["edge_full"] = int(i1 is not None)
        ie = next((i for i, d in enumerate(dd) if d >= -0.3), None)
        if i1 is not None:
            rec["edge_status"] = "full"
        elif ie is None:
            rec["edge_status"] = "not_reached"           # 모서리 구간에 들어가지 못함
        elif fall_t is None:
            rec["edge_status"] = "unjudged_not_crossed"  # 판정 없이 관측 종료까지 미통과(정체 여부는 검사하지 않음)
        elif -0.3 <= dd[-1] < 0.3:
            rec["edge_status"] = "judged_in_edge"        # 판정 직전 마지막 표본이 모서리 구간 안
        else:
            rec["edge_status"] = "judged_after_backing"  # 모서리에 들어갔다가 물러난 뒤 판정
        # 모서리 구간 최초 진입부터 마지막 관측 표본까지 경과 시간. 구간 밖으로 물러난 시간도 포함할 수 있어 구간 내 체류 시간이 아니다
        rec["edge_dwell_s"] = (w[-1]["time_s"] - w[ie]["time_s"]) if ie is not None else None
    return rec


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    per = []
    for arm, (folder, layer) in ARMS.items():
        if arm in STATIONARY:
            continue
        for case, h in CASES.items():
            for seed in SEEDS:
                f = KEEP / folder / "evaluation/candidate/cases" / f"seed_{seed}" / case / "steps.csv"
                if not f.exists():
                    continue
                for env, rows in sorted(load(f).items()):
                    per.append({"arm": arm, "layer": layer, "case": case, "seed": seed, "env": env,
                                **env_state(rows, case, h)})
            print(arm, case, flush=True)
    keys = list(dict.fromkeys(k for d in per for k in d))
    with (OUT / "PER_ENV.csv").open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        wr.writeheader()
        wr.writerows(per)
    summ = []
    for arm in [a for a in ARMS if a not in STATIONARY]:
        for case in CASES:
            g = [r for r in per if r["arm"] == arm and r["case"] == case]
            if not g:
                continue
            for name, sub in (("success", [r for r in g if r["success"] == 1]), ("failure", [r for r in g if r["success"] == 0])):
                row = {"arm": arm, "case": case, "group": name, "robots": len(sub)}
                for k in STATE + STAIR:
                    v = [r.get(k) for r in sub if r.get(k) is not None]
                    if v:
                        row[f"{k}_n"], row[f"{k}_med"], row[f"{k}_q25"], row[f"{k}_q75"] = len(v), st.median(v), p(v, .25), p(v, .75)
                summ.append(row)
    keys = list(dict.fromkeys(k for d in summ for k in d))
    with (OUT / "STATE_SUMMARY.csv").open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        wr.writeheader()
        wr.writerows(summ)


if __name__ == "__main__":
    run()
