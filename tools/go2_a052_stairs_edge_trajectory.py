"""G-A052 계단 오르기 — 발이 첫 모서리에 접근할 때 '상승이 늦는가, 상승은 있는데 막히는가'(A048 한 정책 안, 읽기 전용).

Codex 결정(2026-09-28): 같은 발의 연속 궤적을 모서리 상대 위치·접촉과 함께 읽는다. 목적은 늦음을 입증하는 것이 아니라
늦음과 막힘 중 무엇이 관측에 맞는지 반증 가능하게 비교하는 것이다. 모서리 추정의 불확실성 안에서 두 설명이 겹치면
'구분 불가'로 남긴다. 임의의 새 높이 문턱은 만들지 않는다(높이 기준은 원 지형의 단 높이 h 와 발 반지름뿐).
지형 기하(원문 확인): isaaclab mesh_terrains.inverted_pyramid_stairs_terrain + A048 env.yaml pyramid_stairs_inv
  size 8.0, border_width 1.0, step_width 0.3, platform_width 3.0 -> num_steps = (8-2-3)//0.6 + 1 = 6,
  가운데 가장 낮은 판의 폭 = 6 - 2*6*0.3 = 2.4 m. 따라서 첫 모서리는 타일 중심에서 체비셰프 거리 R0 = 1.2 m,
  바깥으로 0.3 m 마다 한 단(h)씩 높아진다. 평가 실행은 num_cols 4 · difficulty 1.0 · 단 높이 고정.
  (R0 = 1.5 도 함께 맞춰 보고 불일치율을 적는다 — 기존 문서의 '중심 평지 반폭 1.5 m' 표기를 확인하기 위해서.)
정의(결과를 보기 전에 고정, 바꾸지 않는다):
  시각 t = step x 0.02 s, 끝 = 실패 T / 생존 20 s. z0 = 첫 행 네 발 아래 지형 최솟값(가장 낮은 판).
  관측 단 수 L_obs = round((발 아래 지형 - z0)/h), 0..6 로 자른다.
  타일 중심 맞춤: 로봇마다 첫 행 몸통 xy 주변 +-1.0 m 를 0.02 m 격자로, 최적점 주변 +-0.03 m 를 0.002 m 로 탐색해
    모델 단 수(체비셰프 거리 기반)와 L_obs 의 불일치 행 수가 최소인 중심을 고른다(끝까지의 네 발 행 전부).
    동률 중심들의 x·y 범위의 절반 최댓값 + 0.05 m(높이 스캐너 격자 0.1 m 의 절반) = 모서리 위치 불확실성 u.
  발 f 의 부호 거리 d = 체비셰프(발 xy - 중심) - R0 (음수 = 모서리 앞 낮은 판, 0~0.3 = 첫 단 디딤판).
  발바닥 높이 zf = 발 높이 - z0 - 0.023(발 반지름, 평지 하중 행 중앙값). 단 윗면 높이 = h.
  하중 = force_z > 1 N(센서 force_threshold). 단 위 표지 top = 기존 strict 조건.
  접근: d >= -u 가 처음 된 행(i_in). 끝 전에 없으면 no_entry.
  상승 시점 유형(발마다, 처음 맞는 것):
    early      i_in 에서 이미 zf >= h (모서리 불확실 구간에 들어올 때 이미 단 높이 이상).
    in_band    i_in 에서 zf < h, 그 뒤 -u<=d<=u 안에서 '하중·zf<h' 행 없이 zf >= h 에 도달 -> 늦음/제때 구분 불가.
    late       i_in 뒤 -u<=d<=u 에서 '하중·zf<h' 행이 먼저 나오고, 그 뒤 zf >= h (모서리에 낮게 닿은 뒤에야 듦).
    never      끝까지 zf >= h 없음(하중·낮음 접촉 여부는 열로 따로).
    passed_low zf < h 인 채 d > u 로 넘어감(모서리 추정과 모순 — 모서리 모퉁이·추정 오차 표지).
  결과: 접근 뒤 끝 전에 top 표지가 있는가(top_after_entry). 막힘 기술값:
    band_dwell_s   접근 뒤 처음 d > u 로 나가기 전까지 -u<=d<=u 에 머문 시간(끝에서 자름).
    low_contact_s  그 사이 '하중·zf<h' 행의 시간.
  읽는 법(판정 아님): 늦음에 맞는 관측 = late·never(낮은 접촉 있음). 막힘에 맞는 관측 = early·in_band 인데
    top 표지가 없거나 band_dwell 이 긺. in_band 와 passed_low 는 구분 불가로 둔다. 비교 기준은 10cm 생존 24대 분포.
한계: 발 아래 지형은 가장 가까운 광선(최대 약 0.07 m 떨어짐) 값이라 모서리 근처 L_obs 가 흔들린다(불일치율로 드러남).
  한 정책·평가 seed 101·첫 episode. 사건 시각 T 는 상대 높이 기준 시각이지 붕괴 시각이 아니다. 발 유형 수는 발 개수다.
  '보상 억제'나 '힘 부족'을 이 자료로 확정하지 않는다.
결과 확인 뒤 추가(기술 열, 유형 정의는 그대로): rise_t = 접근 뒤 zf >= h 가 처음 된 시각. never 발이 T 전에 가진 시간과
  생존 발의 상승 소요 시간을 대조하기 위한 것이다. 중심 맞춤 불일치율이 높은 로봇(10cm 생존 3대 36~44%)은 20 s 동안
  타일을 벗어나 한 중심으로 맞지 않은 것으로 보이며, 요약에 이들을 뺀 민감도 줄을 따로 적는다(사후 민감도, 판정 아님).

    python -B tools/go2_a052_stairs_edge_trajectory.py
"""
from __future__ import annotations

import csv
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a052_stairs_edge_process as edge  # noqa: E402
import go2_a052_stairs_foot_on_step as fos  # noqa: E402

OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a052_stairs_edge_trajectory_20260928"
DT = fos.DT
STEP_W = 0.3
N_STEPS = 6
R0_MAIN, R0_ALT = 1.2, 1.5
FOOT_R = 0.023
RAY_HALF = 0.05
FORCE_ON = 1.0
KINDS = ("early", "in_band", "late", "never", "passed_low", "no_entry")


def model_level(x: np.ndarray, y: np.ndarray, cx: np.ndarray, cy: np.ndarray, r0: float) -> np.ndarray:
    cheb = np.maximum(np.abs(x[None, :] - cx[:, None]), np.abs(y[None, :] - cy[:, None]))
    lv = np.floor((cheb - r0) / STEP_W) + 1
    return np.clip(np.where(cheb < r0, 0, lv), 0, N_STEPS)


def fit_center(x: np.ndarray, y: np.ndarray, lobs: np.ndarray, x0: float, y0: float, r0: float):
    def search(xs: np.ndarray, ys: np.ndarray):
        gx, gy = np.meshgrid(xs, ys, indexing="ij")
        cx, cy = gx.ravel(), gy.ravel()
        miss = np.empty(cx.size, dtype=np.int64)
        for a in range(0, cx.size, 400):
            miss[a:a + 400] = (model_level(x, y, cx[a:a + 400], cy[a:a + 400], r0) != lobs[None, :]).sum(axis=1)
        return cx, cy, miss
    cx, cy, miss = search(np.arange(x0 - 1.0, x0 + 1.0001, 0.02), np.arange(y0 - 1.0, y0 + 1.0001, 0.02))
    b = int(miss.argmin())
    cx, cy, miss = search(np.arange(cx[b] - 0.03, cx[b] + 0.0301, 0.002), np.arange(cy[b] - 0.03, cy[b] + 0.0301, 0.002))
    best = miss.min()
    tie = miss == best
    b = int(miss.argmin())
    spread = max(float(cx[tie].max() - cx[tie].min()), float(cy[tie].max() - cy[tie].min())) / 2
    return float(cx[b]), float(cy[b]), int(best), spread


def classify(t, d, zf, load, top, h, u, end):
    idx = [i for i in range(len(t)) if t[i] <= end + 1e-9]
    i_in = next((i for i in idx if d[i] >= -u), None)
    out = {"entry_t": "", "zf_at_entry": "", "kind": "no_entry", "top_after_entry": 0, "rise_t": "",
           "band_dwell_s": "", "low_contact_s": "", "low_contact_any": 0}
    if i_in is None:
        return out
    out["entry_t"], out["zf_at_entry"] = t[i_in], round(zf[i_in], 4)
    after = [i for i in idx if i >= i_in]
    out["top_after_entry"] = int(any(top[i] for i in after))
    dwell = low = 0
    for i in after:
        if d[i] > u:
            break
        dwell += 1
        if load[i] and zf[i] < h:
            low += 1
    out["band_dwell_s"], out["low_contact_s"] = round(dwell * DT, 2), round(low * DT, 2)
    out["low_contact_any"] = int(any(load[i] and zf[i] < h and -u <= d[i] <= u for i in after))
    out["rise_t"] = next((t[i] for i in after if zf[i] >= h), "")
    if zf[i_in] >= h:
        out["kind"] = "early"
        return out
    seen_low = False
    for i in after:
        if zf[i] >= h:
            out["kind"] = "late" if seen_low else ("in_band" if d[i] <= u else "passed_low")
            return out
        if d[i] > u:
            out["kind"] = "passed_low"
            return out
        if load[i] and -u <= d[i] <= u:
            seen_low = True
    out["kind"] = "never"
    return out


def main() -> None:
    ev = fos.events()
    OUT.mkdir(parents=True, exist_ok=True)
    fits, feet_rows = [], []
    for case, h in fos.CASES:
        for env, rs in sorted(edge.load(case).items()):
            T = ev.get((case, env))
            end = T if T is not None else fos.HORIZON_S
            rows = [r for r in rs if int(r["step"]) * DT <= end + 1e-9]
            z0 = min(float(rs[0][f + "_terrain_z_near_derived"]) for f in fos.FEET)
            xs, ys, ls = [], [], []
            for r in rows:
                for f in fos.FEET:
                    xs.append(float(r[f + "_pos_x"]))
                    ys.append(float(r[f + "_pos_y"]))
                    ls.append(min(max(round((float(r[f + "_terrain_z_near_derived"]) - z0) / h), 0), N_STEPS))
            x, y, lobs = np.array(xs), np.array(ys), np.array(ls)
            x0 = st.mean(float(rs[0][f + "_pos_x"]) for f in fos.FEET)
            y0 = st.mean(float(rs[0][f + "_pos_y"]) for f in fos.FEET)
            cx, cy, miss, spread = fit_center(x, y, lobs, x0, y0, R0_MAIN)
            _, _, miss_alt, _ = fit_center(x, y, lobs, x0, y0, R0_ALT)
            u = spread + RAY_HALF
            fits.append({"case": case, "env_id": env, "fail": int(T is not None), "rows": len(lobs),
                         "cx": round(cx, 3), "cy": round(cy, 3), "mismatch_rate_r12": round(miss / len(lobs), 4),
                         "mismatch_rate_r15": round(miss_alt / len(lobs), 4), "u_m": round(u, 3)})
            for f in fos.FEET:
                t, d, zf, load, top = [], [], [], [], []
                for r in rows:
                    fx, fy = float(r[f + "_pos_x"]), float(r[f + "_pos_y"])
                    fz = float(r[f + "_force_z"])
                    foot_z = float(r[f + "_pos_z"]) - z0
                    t.append(round(int(r["step"]) * DT, 2))
                    d.append(max(abs(fx - cx), abs(fy - cy)) - R0_MAIN)
                    zf.append(foot_z - FOOT_R)
                    load.append(fz > FORCE_ON)
                    top.append(fz > fos.FORCE_N and float(r[f + "_terrain_z_near_derived"]) - z0 > 0.5 * h
                               and foot_z > 0.8 * h)
                c = classify(t, d, zf, load, top, h, u, end)
                feet_rows.append({"case": case, "env_id": env, "fail": int(T is not None), "T": "" if T is None else T,
                                  "foot": f, "u_m": round(u, 3), **c})
    edge.write_csv(OUT / "CENTER_FIT.csv", fits)
    edge.write_csv(OUT / "FOOT_EDGE_APPROACH.csv", feet_rows)

    mr12 = [r["mismatch_rate_r12"] for r in fits]
    mr15 = [r["mismatch_rate_r15"] for r in fits]
    us = [r["u_m"] for r in fits]
    lines = [f"center fit: mismatch rate R0=1.2 median {st.median(mr12):.4f} (max {max(mr12):.4f}); "
             f"R0=1.5 median {st.median(mr15):.4f}",
             f"edge uncertainty u: median {st.median(us):.3f} m, max {max(us):.3f} m", ""]
    for case, _h in fos.CASES:
        for label, flag in (("FAIL", 1), ("SURV", 0)):
            for pair, feet in (("front", ("FL", "FR")), ("rear", ("RL", "RR"))):
                g = [r for r in feet_rows if r["case"] == case and r["fail"] == flag and r["foot"] in feet]
                if not g:
                    continue
                c = Counter(r["kind"] for r in g)
                lines.append(f"{case} {label} {pair} feet n={len(g)}: " + ", ".join(f"{k} {c[k]}" for k in KINDS))
                for k in KINDS[:-1]:
                    gk = [r for r in g if r["kind"] == k]
                    if not gk:
                        continue
                    dw = [r["band_dwell_s"] for r in gk]
                    lc = [r["low_contact_s"] for r in gk]
                    lines.append(f"  {k}: top_after_entry {sum(r['top_after_entry'] for r in gk)}/{len(gk)}, "
                                 f"low_contact_any {sum(r['low_contact_any'] for r in gk)}/{len(gk)}, "
                                 f"band_dwell median {st.median(dw):.2f} s, low_contact median {st.median(lc):.2f} s")
    bad = {(r["case"], r["env_id"]) for r in fits if r["mismatch_rate_r12"] > 0.30}
    lines += ["", f"post-hoc sensitivity: robots with center-fit mismatch > 0.30 excluded: {sorted(bad)}"]
    for pair, feet in (("front", ("FL", "FR")), ("rear", ("RL", "RR"))):
        g = [r for r in feet_rows if r["case"] == "stairs_10_down" and not r["fail"] and r["foot"] in feet
             and (r["case"], r["env_id"]) not in bad]
        c = Counter(r["kind"] for r in g)
        lines.append(f"  stairs_10_down SURV {pair} n={len(g)}: " + ", ".join(f"{k} {c[k]}" for k in KINDS)
                     + f"; top_after_entry {sum(r['top_after_entry'] for r in g)}/{len(g)}")
    lines += ["", "time scale (descriptive): survivors' rise delay (rise_t - entry_t) vs time a 'never' foot had (T - entry_t)"]
    for case, _h in fos.CASES:
        for pair, feet in (("front", ("FL", "FR")), ("rear", ("RL", "RR"))):
            sv = [r["rise_t"] - r["entry_t"] for r in feet_rows if r["case"] == case and not r["fail"]
                  and r["foot"] in feet and r["rise_t"] != "" and (r["case"], r["env_id"]) not in bad]
            nv = [r["T"] - r["entry_t"] for r in feet_rows if r["case"] == case and r["fail"]
                  and r["foot"] in feet and r["kind"] == "never"]
            if sv:
                q = sorted(sv)
                lines.append(f"  {case} SURV {pair} rise delay: median {st.median(q):.2f} s, "
                             f"p90 {q[int(len(q) * 0.9)]:.2f}, max {q[-1]:.2f}, n={len(q)}")
            if nv:
                q = sorted(nv)
                lines.append(f"  {case} FAIL {pair} never: time before T median {st.median(q):.2f} s, "
                             f"min {q[0]:.2f}, max {q[-1]:.2f}, n={len(q)}")
    (OUT / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
