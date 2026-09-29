"""G-A052 계단 오르기 — 발마다 '늦게 들었나, 일찍 들었지만 막혔나'(A048 한 정책 안, 읽기 전용, 사후 기술).

배경: Codex 확인(2026-09-28) — 앞발 표지 뒤 0.8 s를 온전히 관측한 로봇에서, 처음 0.4 s 뒷발 상승속도(두 뒷발 중 큰 값의
구간 평균)가 10cm 실패 3대 0.153 대 생존 24대 0.314 m/s, 15cm 실패 12대 0.316 m/s. 사용자 가설 '전진에 비해 등반 동작이
늦다'의 단서다. 평균 속도는 '늦게 시작'과 '일찍 시작했지만 막힘'을 가르지 못하므로 로봇·발별 사건으로 연결한다.
입력: A052 회수본 seed_101 stairs_10_down·stairs_15_down diag.csv.gz(이름과 달리 오르기), EVENTS_DIAG.csv 의 T.
출력(reports/evidence/go2_a052_stairs_foot_timing_20260928/): FOOT_EVENTS.csv(로봇 x 발), SUMMARY.txt.
정의(결과를 보기 전에 고정, 바꾸지 않는다). 발 f, 시각 t = step x 0.02 s, z0 = 첫 행 네 발 아래 지형 최솟값, 단 높이 h:
  끝 end   실패 로봇 T, 생존 로봇 20 s(첫 episode).
  near_t   f 반경 0.15 m 안 최고 지형(*_terrain_zmax015_derived) - z0 > 0.5h 가 처음 된 시각 = 발이 첫 단 모서리 근처에 옴.
  lift_t   near_t 이후 f 높이(*_pos_z) - z0 > 0.8h 가 처음 된 시각 = 발을 단 높이까지 들어 올림(공중·접촉 무관).
  edge_t   near_t 이후 f 접촉력 > 5 N 이고 f 바로 아래 지형(*_terrain_z_near_derived) - z0 > 0.5h 이며
           f 높이 - z0 <= 0.8h 인 첫 시각 = 발이 단 높이보다 낮은 채 모서리(턱·옆면)에 힘을 받음. 걸림 확인은 아니다.
  top_t    f 접촉력 > 5 N, 바로 아래 지형 - z0 > 0.5h, f 높이 - z0 > 0.8h 인 첫 시각(기존 strict 표지와 같음).
  lift_delay_s = lift_t - near_t.  near 에서 발이 단 높이까지 올라가는 데 걸린 시간.
  발별 유형(순서대로 처음 맞는 것):
    no_near         end 전에 near_t 없음(모서리 근처에 오지 않음).
    near_no_lift    near_t 는 있으나 end 전에 lift_t 없음(모서리 근처에서 단 높이로 들지 않음).
    edge_before_top edge_t 가 있고 top_t 가 없거나 edge_t < top_t (낮은 채 모서리에 먼저 힘을 받음).
    lift_no_top     lift_t 는 있으나 top_t 없음(들었지만 단 위 지지 표지 없음).
    top             위 어디에도 해당하지 않고 top_t 있음.
  기술 비교(판정 아님): 10cm 생존 24대의 발별 분포. 15cm 생존 1대는 참고.
한계: 지형은 높이 스캐너 격자(0.1 m) 파생값이라 모서리 위치가 약 +-0.05 m 불확실하다. 한 정책·평가 seed 하나·첫 episode.
  T 에서 자르므로 일찍 끝난 실패 로봇은 뒷발이 모서리에 오기 전에 끝날 수 있다(no_near 는 '늦음'의 증거가 아니다).
  발 사건의 순서가 원인은 아니다. '보상 억제'나 '힘 부족'을 이 자료로 확정하지 않는다.

    python -B tools/go2_a052_stairs_foot_timing.py
"""
from __future__ import annotations

import csv
import gzip
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a052_stairs_foot_on_step as fos  # noqa: E402

OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a052_stairs_foot_timing_20260928"
DT = fos.DT
TYPES = ("no_near", "near_no_lift", "edge_before_top", "lift_no_top", "top")


def load(case: str) -> dict[int, list[dict]]:
    rows: dict[int, list[dict]] = {}
    with gzip.open(fos.KEEP / case / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(int(r["env_id"]), []).append(r)
    for rs in rows.values():
        rs.sort(key=lambda r: int(r["step"]))
    return rows


def foot_events(rs: list[dict], f: str, h: float, end: float, z0: float) -> dict:
    near = lift = edge = top = None
    for r in rs:
        t = round(int(r["step"]) * DT, 2)
        if t > end + 1e-9:
            break
        fz = float(r[f + "_force_z"])
        foot_z = float(r[f + "_pos_z"]) - z0
        under = float(r[f + "_terrain_z_near_derived"]) - z0
        zmax = float(r[f + "_terrain_zmax015_derived"]) - z0
        if top is None and fz > fos.FORCE_N and under > 0.5 * h and foot_z > 0.8 * h:
            top = t
        if near is None and zmax > 0.5 * h:
            near = t
        if near is not None:
            if lift is None and foot_z > 0.8 * h:
                lift = t
            if edge is None and fz > fos.FORCE_N and under > 0.5 * h and foot_z <= 0.8 * h:
                edge = t
    if near is None:
        kind = "no_near"
    elif lift is None:
        kind = "near_no_lift"
    elif edge is not None and (top is None or edge < top):
        kind = "edge_before_top"
    elif top is None:
        kind = "lift_no_top"
    else:
        kind = "top"
    return {"near_t": near, "lift_t": lift, "edge_t": edge, "top_t": top,
            "lift_delay_s": None if near is None or lift is None else round(lift - near, 2), "type": kind}


def main() -> None:
    ev = fos.events()
    OUT.mkdir(parents=True, exist_ok=True)
    recs: list[dict] = []
    for case, h in fos.CASES:
        for env, rs in sorted(load(case).items()):
            T = ev.get((case, env))
            end = T if T is not None else fos.HORIZON_S
            z0 = min(float(rs[0][f + "_terrain_z_near_derived"]) for f in fos.FEET)
            for f in fos.FEET:
                e = foot_events(rs, f, h, end, z0)
                recs.append({"case": case, "env_id": env, "fail": int(T is not None), "T": "" if T is None else T,
                             "foot": f, **{k: ("" if v is None else v) for k, v in e.items()}})
    with (OUT / "FOOT_EVENTS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(recs)

    lines: list[str] = []
    for case, _h in fos.CASES:
        for label, flag in (("FAIL", 1), ("SURV", 0)):
            for pair, feet in (("front", ("FL", "FR")), ("rear", ("RL", "RR"))):
                g = [r for r in recs if r["case"] == case and r["fail"] == flag and r["foot"] in feet]
                if not g:
                    continue
                c = Counter(r["type"] for r in g)
                d = [r["lift_delay_s"] for r in g if r["lift_delay_s"] != ""]
                ds = f"median {st.median(d):.2f} s, p10 {sorted(d)[len(d) // 10]:.2f}, p90 {sorted(d)[len(d) * 9 // 10]:.2f}, n={len(d)}" if d else "n=0"
                lines.append(f"{case} {label} {pair} feet n={len(g)}: " + ", ".join(f"{k} {c[k]}" for k in TYPES))
                lines.append(f"  lift_delay_s (near -> step height): {ds}")
                if flag:
                    after_near = [r for r in g if r["near_t"] != ""]
                    lines.append(f"  feet that reached the edge region before T: {len(after_near)}/{len(g)}; "
                                 f"T - near_t median {st.median(r['T'] - r['near_t'] for r in after_near):.2f} s"
                                 if after_near else "  no foot reached the edge region before T")
    (OUT / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
