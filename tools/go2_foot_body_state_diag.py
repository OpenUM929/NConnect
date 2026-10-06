"""성공/실패 로봇의 발·자세·관절 상태 (진단 재생이 있는 run 만, 2026-10-01, 읽기 전용).

진단 재생(diag.csv.gz)이 있는 것: A048(G-A052) 험지 옆 seed 202·계단 10/15cm seed 101,
A043(G-A056) 험지 옆·복합 우회전 seed 202. 관절 채널은 A043 run 에만 있다.
성공/실패 정의는 tools/go2_robot_state_profile.py 와 같다. 구간은 고정 1~4 s 이고, 5 s 전에 판정된 로봇은 뺀다(넘어지는 과정이 구간에 섞이지 않게).

상태값 (로봇마다)
  roll_p90 / pitch_med   몸통 roll 크기 90분위, pitch(앞 들림 +) 중앙값 (도, 쿼터니언)
  front_apex / hind_apex 발 높이 = pos_z - 발 아래 지형 - 0.023 의 발별 90분위 → 앞발·뒷발 평균 (m) = 평소 발 들기
  front_width / hind_width 좌우 발 사이 몸통 좌표 옆 거리 중앙값 (m) = 발 벌림
  duty          발 접촉(force_z > 1 N) 행 비율, 네 발 평균
  thigh / calf  관절 각도 네 다리 평균의 중앙값 (rad, A043 만)
"""
from __future__ import annotations

import csv
import gzip
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_robot_state_profile import env_state  # noqa: E402
from go2_state_outcome import first_episode, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_foot_body_state_diag_20261001"
RUNS = [("A048", "go2_g_a052_a048_diag_replay", 202, "rough_lateral", None),
        ("A048", "go2_g_a052_a048_diag_replay", 101, "stairs_15_down", 0.15),
        ("A048", "go2_g_a052_a048_diag_replay", 101, "stairs_10_down", 0.10),
        ("A043", "go2_g_a056_a043_diag_replay", 202, "rough_lateral", None),
        ("A043", "go2_g_a056_a043_diag_replay", 202, "combined_yaw_right", None)]
FEET = ("FL", "FR", "RL", "RR")
KEYS = ("roll_p90", "pitch_med", "front_apex", "hind_apex", "front_width", "hind_width", "duty", "thigh", "calf")


def q90(v):
    s = sorted(v)
    return s[int(0.9 * (len(s) - 1))] if s else None


def euler(r):
    w, x, y, z = (float(r[k]) for k in ("quat_w", "quat_x", "quat_y", "quat_z"))
    roll = math.degrees(math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)))
    pitch = math.degrees(math.asin(max(-1, min(1, 2 * (w * y - z * x)))))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, -pitch, yaw


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    per = []
    for arm, folder, seed, case, h in RUNS:
        d = KEEP / folder / "diag/cases" / f"seed_{seed}" / case
        steps = load(d / "steps.csv")
        diag = {}
        with gzip.open(d / "diag.csv.gz", "rt", encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                diag.setdefault(int(r["env_id"]), {})[int(r["step"])] = r
        for env, rows in sorted(steps.items()):
            s = env_state(rows, case, h)
            # fixed window 1 <= t < 4 s; robots judged before 5 s are left out (no fall dynamics in the window)
            if s["fall_t"] is not None and s["fall_t"] < 5.0:
                per.append({"arm": arm, "case": case, "seed": seed, "env": env, "success": s["success"], "rows": 0})
                continue
            w = [diag[env].get(round(r["time_s"] / 0.02)) for r in first_episode(rows) if 1 <= r["time_s"] < 4]
            w = [x for x in w if x is not None]
            rec = {"arm": arm, "case": case, "seed": seed, "env": env, "success": s["success"], "rows": len(w)}
            if len(w) >= 25:
                eu = [euler(x) for x in w]
                rec["roll_p90"] = q90([abs(e[0]) for e in eu])
                rec["pitch_med"] = st.median(e[1] for e in eu)
                ap = {f: q90([float(x[f + "_pos_z"]) - float(x[f + "_terrain_z_near_derived"]) - 0.023 for x in w]) for f in FEET}
                rec["front_apex"] = (ap["FL"] + ap["FR"]) / 2
                rec["hind_apex"] = (ap["RL"] + ap["RR"]) / 2
                for pair, (lf, rf) in (("front", ("FL", "FR")), ("hind", ("RL", "RR"))):
                    wid = []
                    for x, e in zip(w, eu):
                        dx = float(x[lf + "_pos_x"]) - float(x[rf + "_pos_x"])
                        dy = float(x[lf + "_pos_y"]) - float(x[rf + "_pos_y"])
                        wid.append(abs(-math.sin(e[2]) * dx + math.cos(e[2]) * dy))
                    rec[f"{pair}_width"] = st.median(wid)
                rec["duty"] = st.mean(sum(float(x[f + "_force_z"]) > 1.0 for x in w) / len(w) for f in FEET)
                if "jpos_FL_thigh_joint" in w[0]:
                    rec["thigh"] = st.median(st.mean(float(x[f"jpos_{f}_thigh_joint"]) for f in FEET) for x in w)
                    rec["calf"] = st.median(st.mean(float(x[f"jpos_{f}_calf_joint"]) for f in FEET) for x in w)
            per.append(rec)
        print(arm, case, flush=True)
    summ = []
    for arm, folder, seed, case, h in RUNS:
        for g, name in ((1, "success"), (0, "failure")):
            sub = [r for r in per if r["arm"] == arm and r["case"] == case and r["success"] == g]
            row = {"arm": arm, "case": case, "seed": seed, "group": name, "robots": len(sub)}
            for k in KEYS:
                v = [r[k] for r in sub if r.get(k) is not None]
                if v:
                    row[f"{k}_n"], row[f"{k}_med"] = len(v), st.median(v)
            summ.append(row)
    for name, data in (("PER_ENV.csv", per), ("SUMMARY.csv", summ)):
        keys = list(dict.fromkeys(k for r in data for k in r))
        with (OUT / name).open("w", encoding="utf-8", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
            wr.writeheader()
            wr.writerows(data)


if __name__ == "__main__":
    main()
