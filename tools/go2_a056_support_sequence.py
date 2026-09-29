#!/usr/bin/env python3
"""G-A056 사후 판독(탐색) — 넘어지는 쪽 다리의 지지 순서 (2026-09-29).

**사전등록 판독이 아니다.**  사전등록 판독(tools/go2_a043_diag_readout.py)의 축 A·B 는 낙상과 생존을 가르지 못했다
(생존 로봇에서도 같은 창에서 '미끄러짐'이 잡힌다).  그래서 회수물을 본 뒤 아래 정의를 정했다.  결과는 가설 단서일 뿐이고,
판정이나 채택의 근거가 아니다.  같은 재생의 생존 로봇은 비교군이지 인과 대조군이 아니다.

정의 (넘어지는 쪽 = 명령 옆 방향.  험지 옆걸음은 cmd_vy +0.3 이라 왼쪽, 복합 우회전은 cmd_vy −0.15·wz −0.5 라 오른쪽)
  기울기(도)     = atan2(grav_b_y, −grav_b_z).  넘어지는 쪽이 내려가면 + 가 되도록 부호를 맞춘다.
  안쪽 hip(rad)  = 넘어지는 쪽 두 다리 hip 관절각의 평균.  발이 몸 중심선 쪽으로 가면 + 다.
                 (Go2 hip 축은 +x 다.  왼다리는 −, 오른다리는 + 가 안쪽이다.  몸이 그쪽으로 기울면 땅을 딛은 다리는
                  오히려 바깥쪽 값을 보이므로, 기울기만으로는 이 값이 +로 가지 않는다.)
  반대쪽 하중(N) = 반대쪽 두 발의 접촉력 z 합.
  무릎 끝        = calf 관절각이 soft 상한(가장 편 자세)에서 0.05 rad 안에 있는 행.
  기준 시각      = 사전등록 판독의 onset.  생존 로봇은 낙상 onset 의 중앙값을 쓴다.
출력
  SUPPORT_PROFILE.csv   onset 전 3 s 를 0.5 s 칸으로 나눈다.  칸마다 낙상/생존 로봇의 중앙값을 적는다
                        (다리별 접촉·하중·hip·무릎 끝, 기울기, 안쪽 hip, 반대쪽 하중, 옆 속도 초과).
  SUPPORT_PER_ROBOT.csv 로봇별로 세 구간(1~3 s, onset−3~−1 s, onset−1~0 s)의 기울기와 안쪽 hip 평균.
  SUPPORT_ORDER.csv     낙상 로봇별로, 0.1 s 이동평균이 생존 로봇 기준을 넘은 채 onset 까지 이어진 구간의 시작 시각
                        (onset 기준 초).  기준은 기울기·안쪽 hip 은 p95, 반대쪽 하중은 p05 다.  onset 전 1.5 s 만 본다.

    python -B tools/go2_a056_support_sequence.py [결과 폴더] [--out <dir>]
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import math
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "workspace/_keep/go2_g_a056_a043_diag_replay"
EVID = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a056_diag_20260928"
DT = 0.02
LEGS = ("FL", "FR", "RL", "RR")
CASES = {  # case: (넘어지는 쪽 부호, 넘어지는 쪽 다리, 반대쪽 다리, cmd_vy)
    "rough_lateral": (1, ("FL", "RL"), ("FR", "RR"), 0.3),
    "combined_yaw_right": (-1, ("FR", "RR"), ("FL", "RL"), -0.15),
}
BINS = [(-3.0 + 0.5 * i, -2.5 + 0.5 * i) for i in range(6)]


def p_at(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    return xs[int(q * (len(xs) - 1))]


def load(harvest: Path, evid: Path, case: str):
    sgn, side, far, cmd_vy = CASES[case]
    d = harvest / "diag/cases/seed_202" / case
    meta = json.loads((d / "diag_meta.json").read_text(encoding="utf-8"))["joints"]
    names, soft = meta["names"], meta["soft_joint_pos_limits_env0"]
    soft = json.loads(soft) if isinstance(soft, str) else soft
    with (evid / "EVENTS_A043_DIAG.csv").open(encoding="utf-8") as fh:
        ev = {int(r["env_id"]): float(r["onset_t"]) for r in csv.DictReader(fh) if r["case"] == case}
    with (evid / "SURVIVOR_CONTRAST.csv").open(encoding="utf-8") as fh:
        sv = {int(r["env_id"]): float(r["T_median_onset"]) for r in csv.DictReader(fh) if r["case"] == case}
    rows = collections.defaultdict(list)
    with gzip.open(d / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            e, t = int(r["env_id"]), int(r["step"]) * DT
            if e in ev and t >= ev[e]:
                continue
            x = {"t": t,
                 "roll_deg": sgn * math.degrees(math.atan2(float(r["grav_b_y"]), -float(r["grav_b_z"]))),
                 "inward_hip": st.fmean((-float(r[f"jpos_{L}_hip_joint"]) if L[1] == "L" else float(r[f"jpos_{L}_hip_joint"]))
                                        for L in side),
                 "far_load": sum(float(r[f"{L}_force_z"]) for L in far),
                 "vy_excess": sgn * (float(r["lin_vel_b_y"]) - cmd_vy)}
            for L in LEGS:
                x[f"contact_{L}"] = float(float(r[f"{L}_force_z"]) > 1.0)
                x[f"fz_{L}"] = float(r[f"{L}_force_z"])
                x[f"hip_{L}"] = float(r[f"jpos_{L}_hip_joint"])
                i = names.index(f"{L}_calf_joint")
                x[f"knee_end_{L}"] = float(soft[i][1] - float(r[f"jpos_{L}_calf_joint"]) < 0.05)
            rows[e].append(x)
    return ev, sv, rows


def profile(case, ev, sv, rows):
    ref = {**ev, **sv}
    keys = [k for k in rows[next(iter(rows))][0] if k != "t"]
    out = []
    for grp, envs in (("fall", ev), ("survivor", sv)):
        for lo, hi in BINS:
            rec = {"case": case, "group": grp, "n_robots": len(envs), "bin_from_s": lo, "bin_to_s": hi}
            for k in keys:
                xs = []
                for e in envs:
                    sel = [x[k] for x in rows[e] if lo <= x["t"] - ref[e] < hi]
                    if sel:
                        xs.append(st.fmean(sel))
                rec[k] = round(st.median(xs), 4) if xs else ""
            out.append(rec)
    return out


def per_robot(case, ev, sv, rows):
    ref = {**ev, **sv}
    out = []
    for e in sorted(ref):
        rec = {"case": case, "env_id": e, "group": "fall" if e in ev else "survivor", "ref_onset_t": ref[e]}
        spans = {"early_1_3s": (1.0, 3.0), "pre_m3_m1s": (ref[e] - 3.0, ref[e] - 1.0), "last_1s": (ref[e] - 1.0, ref[e])}
        for w, (lo, hi) in spans.items():
            sel = [x for x in rows[e] if lo <= x["t"] < hi]
            rec[f"roll_deg_{w}"] = round(st.fmean(x["roll_deg"] for x in sel), 3) if sel else ""
            rec[f"inward_hip_{w}"] = round(st.fmean(x["inward_hip"] for x in sel), 4) if sel else ""
        out.append(rec)
    return out


def smooth(xs: list[dict], k: str) -> list[float]:
    return [st.fmean(v[k] for v in xs[max(0, i - 4):i + 1]) for i in range(len(xs))]


def order(case, ev, sv, rows):
    base = {k: [] for k in ("roll_deg", "inward_hip", "far_load")}
    for e in sv:
        s = [x for x in rows[e] if x["t"] >= 1.0]
        for k in base:
            base[k] += smooth(s, k)
    thr = {"roll_deg": p_at(base["roll_deg"], 0.95), "inward_hip": p_at(base["inward_hip"], 0.95),
           "far_load": p_at(base["far_load"], 0.05)}
    out = []
    for e, on in sorted(ev.items()):
        s = [x for x in rows[e] if x["t"] >= max(1.0, on - 1.5)]
        rec = {"case": case, "env_id": e, "onset_t": on, "rows": len(s), "valid": int(len(s) >= 10),
               "thr_roll_p95_deg": round(thr["roll_deg"], 3), "thr_inward_p95_rad": round(thr["inward_hip"], 4),
               "thr_far_load_p05_n": round(thr["far_load"], 2)}
        for k, above in (("roll_deg", True), ("inward_hip", True), ("far_load", False)):
            start = ""
            if len(s) >= 10:
                vals = smooth(s, k)
                for i in range(len(vals) - 1, -1, -1):
                    if (vals[i] > thr[k]) if above else (vals[i] < thr[k]):
                        start = round(s[i]["t"] - on, 2)
                    else:
                        break
            rec[f"start_{k}_rel_onset_s"] = start
        out.append(rec)
    return out


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("harvest", nargs="?", default=str(HARVEST))
    ap.add_argument("--out", default=str(EVID))
    a = ap.parse_args(argv)
    out = Path(a.out)
    prof, per, ordr = [], [], []
    for case in CASES:
        ev, sv, rows = load(Path(a.harvest), out, case)
        prof += profile(case, ev, sv, rows)
        per += per_robot(case, ev, sv, rows)
        ordr += order(case, ev, sv, rows)
    write(out / "SUPPORT_PROFILE.csv", prof)
    write(out / "SUPPORT_PER_ROBOT.csv", per)
    write(out / "SUPPORT_ORDER.csv", ordr)
    print(json.dumps({"profile_rows": len(prof), "per_robot_rows": len(per), "order_rows": len(ordr)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
