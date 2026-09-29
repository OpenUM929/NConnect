#!/usr/bin/env python3
"""G-A056 사후 확인 — '지지 실패' 설명을 실제 발 위치로 확인한다 (2026-09-29, Codex 지시).

tools/go2_a056_support_sequence.py 의 안쪽 hip 관측을 hip 각도가 아닌 발 위치로 다시 본다.  새 문턱을 만들지 않는다.
구간은 그 도구와 같다: 로봇별 세 구간(1~3 s, onset−3~−1 s, onset−1~0 s; 생존 로봇은 낙상 onset 중앙값 기준)과,
낙상 로봇의 SUPPORT_ORDER.csv 안쪽 hip 시작 시각 t0 에서 onset 까지.  접지는 접촉 센서 문턱(force_z > 1.0 N, 기록 meta)이다.

좌표 (발 위치는 body_pos_w, 몸 위치는 steps.csv root_x·root_y 와 diag root_z; 같은 step·env 행을 맞춘다)
  몸통 좌표   rel = foot_w − root_w 를 root_quat_w 의 역회전으로 돌린 y (roll 포함).
  수평 좌표   rel 을 heading(yaw) 만 되돌린 y.  중력 기준 수평에서 발이 몸 옆 어디에 있는지다.
  바깥 거리   넘어지는 쪽 다리의 y 를 바깥이 + 가 되게 부호를 맞춘 값(왼다리 +y, 오른다리 −y 가 바깥).  작아지면 발이 몸 안쪽이다.
  hip 목표    default(왼 +0.1, 오른 −0.1) + 0.25 × action (A043 env.yaml actions.joint_pos scale 0.25, use_default_offset).
             안쪽 부호로 맞춘 (목표 − 실제) 가 + 이면 제어기가 다리를 더 안쪽으로 끌고 있고, − 이면 실제 다리가 목표보다 안쪽에 있다
             (다리가 명령보다 안쪽으로 밀려 있다).

출력 (reports/evidence/go2_g_a056_diag_20260928/)
  FOOT_WINDOWS.csv  로봇별·구간별: 넘어지는 쪽 접지 발의 몸통/수평 바깥 거리 평균, 반대쪽 접지 발 같은 값, 안쪽 부호 (목표 − 실제) hip 평균.
  FOOT_EVENTS.csv   낙상 로봇별 [t0, onset): 넘어지는 쪽 다리마다 접지 상태(계속 접지 / 새로 착지 / 접지 없음),
                    수평 바깥 거리 변화 = 발의 세계 좌표 옆 이동 기여 − 몸의 옆 이동 기여(t0 시각 heading 의 옆 축에 투영),
                    t0 전 0.3 s 와 [t0, onset) 의 안쪽 부호 (목표 − 실제) hip 평균, 그리고 판정.
  판정 (새 문턱 없이 부호와 크기 비교만):
    LEG_MOVED_INWARD      바깥 거리가 줄었고, 그 감소에서 발의 세계 이동 기여가 몸 이동 기여보다 크다
                          (다리가 들려 안쪽에 새로 착지했거나 접지 발이 안쪽으로 끌렸다).
    BODY_OVER_PLANTED_FOOT 바깥 거리가 줄었고, 몸 이동 기여가 더 크다(발은 거의 그 자리이고 몸이 발 위로 왔다).
    NOT_INWARD            바깥 거리가 줄지 않았다(반대 관측).
    UNRESOLVED            t0 가 없거나 접지 행이 없다.
  TOUCHDOWNS.csv    넘어지는 쪽 다리의 착지(접지 없음 → 접지) 순간마다 수평·몸통 바깥 거리.  낙상 로봇은 onset 전 3 s,
                    생존 로봇은 같은 기준 시각 전 3 s 안의 착지다.  onset 기준 시각을 함께 적는다.
  무게중심은 계측하지 않았다.  그래서 지지 다각형 이탈은 이 출력으로 확정하지 않는다.

    python -B tools/go2_a056_foot_position_check.py [결과 폴더] [--out <dir>]
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
FORCE = 1.0
SCALE, DEFAULT_HIP = 0.25, {"L": 0.1, "R": -0.1}
LEGS = ("FL", "FR", "RL", "RR")
CASES = {"rough_lateral": (("FL", "RL"), ("FR", "RR")), "combined_yaw_right": (("FR", "RR"), ("FL", "RL"))}
PRE_T0_S = 0.3


def rot_inv(q, v):
    """쿼터니언 (w,x,y,z) 의 역회전을 v 에 적용."""
    w, x, y, z = q
    x, y, z = -x, -y, -z
    tx, ty, tz = 2 * (y * v[2] - z * v[1]), 2 * (z * v[0] - x * v[2]), 2 * (x * v[1] - y * v[0])
    return (v[0] + w * tx + (y * tz - z * ty), v[1] + w * ty + (z * tx - x * tz), v[2] + w * tz + (x * ty - y * tx))


def yaw_of(q):
    w, x, y, z = q
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def outward_sign(leg: str) -> int:
    return 1 if leg[1] == "L" else -1


def load(harvest: Path, evid: Path, case: str):
    d = harvest / "diag/cases/seed_202" / case
    names = json.loads((d / "diag_meta.json").read_text(encoding="utf-8"))["joints"]["names"]
    root = {}
    with (d / "steps.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            root[(int(r["step"]), int(r["env_id"]))] = (float(r["root_x"]), float(r["root_y"]), float(r["root_z"]))
    with (evid / "EVENTS_A043_DIAG.csv").open(encoding="utf-8") as fh:
        ev = {int(r["env_id"]): float(r["onset_t"]) for r in csv.DictReader(fh) if r["case"] == case}
    with (evid / "SURVIVOR_CONTRAST.csv").open(encoding="utf-8") as fh:
        sv = {int(r["env_id"]): float(r["T_median_onset"]) for r in csv.DictReader(fh) if r["case"] == case}
    with (evid / "SUPPORT_ORDER.csv").open(encoding="utf-8") as fh:
        t0 = {int(r["env_id"]): (float(r["start_inward_hip_rel_onset_s"]) if r["start_inward_hip_rel_onset_s"] else None)
              for r in csv.DictReader(fh) if r["case"] == case}
    rows, zdiff = collections.defaultdict(list), []
    with gzip.open(d / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            step, e = int(r["step"]), int(r["env_id"])
            t = step * DT
            if e in ev and t >= ev[e]:
                continue
            rx, ry, rz = root[(step, e)]
            zdiff.append(abs(rz - float(r["root_z"])))
            q = tuple(float(r[k]) for k in ("quat_w", "quat_x", "quat_y", "quat_z"))
            yaw = yaw_of(q)
            x = {"t": t, "base": (rx, ry), "yaw": yaw}
            for i, L in enumerate(LEGS):
                p = (float(r[f"{L}_pos_x"]), float(r[f"{L}_pos_y"]), float(r[f"{L}_pos_z"]))
                rel = (p[0] - rx, p[1] - ry, p[2] - float(r["root_z"]))
                yb = rot_inv(q, rel)[1]
                yh = -math.sin(yaw) * rel[0] + math.cos(yaw) * rel[1]
                s = outward_sign(L)
                hip_i = names.index(f"{L}_hip_joint")
                target = DEFAULT_HIP[L[1]] + SCALE * float(r[f"action_{hip_i}"])
                qh = float(r[f"jpos_{L}_hip_joint"])
                x[L] = {"stance": float(r[f"{L}_force_z"]) > FORCE, "out_b": s * yb, "out_h": s * yh, "p": p,
                        "tgt_minus_q_in": -s * (target - qh)}  # 안쪽 부호: 왼다리 안쪽 = −, 오른다리 안쪽 = +
            rows[e].append(x)
    return ev, sv, t0, rows, max(zdiff)


def mean_or_blank(xs):
    return round(st.fmean(xs), 4) if xs else ""


def windows(case, ev, sv, rows):
    side, far = CASES[case]
    ref = {**ev, **sv}
    out = []
    for e in sorted(ref):
        rec = {"case": case, "env_id": e, "group": "fall" if e in ev else "survivor", "ref_onset_t": ref[e]}
        spans = {"early_1_3s": (1.0, 3.0), "pre_m3_m1s": (ref[e] - 3.0, ref[e] - 1.0), "last_1s": (ref[e] - 1.0, ref[e])}
        for w, (lo, hi) in spans.items():
            sel = [x for x in rows[e] if lo <= x["t"] < hi]
            rec[f"fall_side_stance_out_body_{w}"] = mean_or_blank([x[L]["out_b"] for x in sel for L in side if x[L]["stance"]])
            rec[f"fall_side_stance_out_horiz_{w}"] = mean_or_blank([x[L]["out_h"] for x in sel for L in side if x[L]["stance"]])
            rec[f"far_side_stance_out_horiz_{w}"] = mean_or_blank([x[L]["out_h"] for x in sel for L in far if x[L]["stance"]])
            rec[f"fall_side_tgt_minus_q_inward_{w}"] = mean_or_blank([x[L]["tgt_minus_q_in"] for x in sel for L in side])
        out.append(rec)
    return out


def events(case, ev, t0s, rows):
    side, _ = CASES[case]
    out = []
    for e, on in sorted(ev.items()):
        rel0 = t0s.get(e)
        for L in side:
            rec = {"case": case, "env_id": e, "leg": L, "onset_t": on, "t0_rel_onset_s": "" if rel0 is None else rel0}
            if rel0 is None:
                rec["verdict"] = "UNRESOLVED"
                out.append(rec)
                continue
            seg = [x for x in rows[e] if on + rel0 <= x["t"] < on]
            pre = [x for x in rows[e] if on + rel0 - PRE_T0_S <= x["t"] < on + rel0]
            st_flags = [x[L]["stance"] for x in seg]
            rec["stance_state"] = ("always_stance" if all(st_flags) else "no_stance" if not any(st_flags)
                                   else "touchdown_in_interval" if any(not a and b for a, b in zip(st_flags, st_flags[1:]))
                                   else "lift_off_only")
            stance = [x for x in seg if x[L]["stance"]]
            if not seg or not stance:
                rec["verdict"] = "UNRESOLVED"
                out.append(rec)
                continue
            a, b = seg[0], stance[-1]
            n = (-math.sin(a["yaw"]), math.cos(a["yaw"]))  # t0 heading 의 왼쪽 옆 축
            s = outward_sign(L)
            foot_c = s * ((b[L]["p"][0] - a[L]["p"][0]) * n[0] + (b[L]["p"][1] - a[L]["p"][1]) * n[1])
            base_c = -s * ((b["base"][0] - a["base"][0]) * n[0] + (b["base"][1] - a["base"][1]) * n[1])
            d_out = b[L]["out_h"] - a[L]["out_h"]
            rec.update({"out_horiz_start": round(a[L]["out_h"], 4), "out_horiz_end_last_stance": round(b[L]["out_h"], 4),
                        "d_out_horiz": round(d_out, 4), "foot_world_contrib": round(foot_c, 4), "base_contrib": round(base_c, 4),
                        "out_body_start": round(a[L]["out_b"], 4), "out_body_end_last_stance": round(b[L]["out_b"], 4),
                        "tgt_minus_q_inward_pre": mean_or_blank([x[L]["tgt_minus_q_in"] for x in pre]),
                        "tgt_minus_q_inward_interval": mean_or_blank([x[L]["tgt_minus_q_in"] for x in seg])})
            if d_out >= 0:
                rec["verdict"] = "NOT_INWARD"
            elif abs(foot_c) > abs(base_c) and foot_c < 0:
                rec["verdict"] = "LEG_MOVED_INWARD"
            elif base_c < 0 and abs(base_c) >= abs(foot_c):
                rec["verdict"] = "BODY_OVER_PLANTED_FOOT"
            else:
                rec["verdict"] = "UNRESOLVED"
            out.append(rec)
    return out


def touchdowns(case, ev, sv, rows):
    side, _ = CASES[case]
    ref = {**ev, **sv}
    out = []
    for e in sorted(ref):
        seq = [x for x in rows[e] if ref[e] - 3.0 <= x["t"] < ref[e]]
        for L in side:
            for a, b in zip(seq, seq[1:]):
                if not a[L]["stance"] and b[L]["stance"]:
                    out.append({"case": case, "env_id": e, "group": "fall" if e in ev else "survivor", "leg": L,
                                "t_rel_ref_s": round(b["t"] - ref[e], 2), "out_horiz": round(b[L]["out_h"], 4),
                                "out_body": round(b[L]["out_b"], 4)})
    return out


def write(path: Path, rows: list[dict]) -> None:
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("harvest", nargs="?", default=str(HARVEST))
    ap.add_argument("--out", default=str(EVID))
    a = ap.parse_args(argv)
    out = Path(a.out)
    win, evs, tds, zmax = [], [], [], {}
    for case in CASES:
        ev, sv, t0s, rows, zd = load(Path(a.harvest), out, case)
        zmax[case] = zd
        win += windows(case, ev, sv, rows)
        evs += events(case, ev, t0s, rows)
        tds += touchdowns(case, ev, sv, rows)
    write(out / "FOOT_WINDOWS.csv", win)
    write(out / "FOOT_EVENTS.csv", evs)
    write(out / "TOUCHDOWNS.csv", tds)
    print(json.dumps({"window_rows": len(win), "event_rows": len(evs), "root_z_max_abs_diff_steps_vs_diag": zmax}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
