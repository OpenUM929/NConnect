#!/usr/bin/env python3
"""G-A067 — G-A066 진단 재생 기록의 행동 판독 (읽기 전용, GPU 없음, 2026-10-06).

합의: workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md §5·§7-5·§10,
      GO2_STAIRS_ROUGH_INVESTIGATION_DISCUSSION_20261006.md §3-6 T3·§3-7.
판정할 예측: P1~P4(Claude), SX1-M~SX3-M·SX4(Codex) — 이 스크립트는 값을 내기만 한다. 판정은 작성 PC가 한다.

고정 정의
- 첫 episode만: 첫 terminated/truncated 행 **직전**까지가 궤적이다. 그 행은 자동 리셋 뒤 상태라(작성 PC 확인: 100%) 궤적에서 빼고
  종료 사건으로만 센다. terminated(몸 접촉)와 truncated(시간 제한)를 구분한다.
- 기준: t = 1.0초 행(50번째 행)의 몸통·발 높이. 그 전에 끝난 개체는 BASELINE_MISSING으로 남기고 분모에서 빼지 않는다.
- 계단(stairs_15_down = 15cm 오르기): 최대 몸통 상승 m(기준 대비).
  미달 m < 0.105 / 도달 m ≥ 0.105. 도달 중 잔존 = 마지막 1초 평균 ≥ HOLD·m, 아니면 손실. HOLD 0.7(주), 0.5(민감도).
  손실 시각 = 최고점 뒤 처음으로 상승이 HOLD·m 아래로 내려간 행.
  발 '윗면 하중' = 발 높이 기준 대비 ≥ 0.10m 그리고 수직 접촉력 ≥ F 가 연속 3행. F = 15N(주), 10·20N(민감도).
  손실 경로 = 손실 시각 기준으로 (a) 앞발 윗면 하중 전 손실 (b) 앞발 하중 뒤·뒷발 윗면 하중 전 손실 (c) 뒷발 하중 뒤 손실.
  끝나는 모습 = 몸 접촉 종료면 종료 전 1초 최대 기울기(직립 <60° / 60~90° / 뒤집힘 >90°), 아니면 자세 판정만 / 판정 없음.
  손실 구간 몸체 전후 이동 = 최고점→손실 시각+1초의 lin_vel_b_x 적분.
- 험지(rough_lateral): 사건 = 몸 접촉 종료(종료 행 직전 시각) 또는 첫 0.5초 비직립(steps.csv upright=0 연속 25행) 시작.
  사건 전 2초에서 onset: |roll 속도|(ang_vel_b_x) > P0 생존 개체 첫 episode 분포 Q(99 주 / 95 민감도), 연속 K행(3 주 / 5 민감도).
  지지 onset: 하중 받는 발(수직력 ≥ 15N) 수 ≤ 1 이 연속 K행. 둘 차이 ≤ 0.06초면 동시(0.02초 민감도).
- 모든 비율의 분모는 전체 96대(정책·case)이고 seed별 값도 낸다. 문턱 의존 여부는 민감도 열로 보인다.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

POLICIES = ("p0", "s04", "s07", "s11", "s13")
SEEDS = ("101", "202", "303")
FEET = ("FL", "FR", "RL", "RR")
FRONT, HIND = ("FL", "FR"), ("RL", "RR")
DT = 0.02
BASE_ROW = 50
REACH = 0.105
FOOT_UP = 0.10
DIAG_COLS = ["root_z", "lin_vel_b_x", "ang_vel_b_x", "ang_vel_b_y", "grav_b_z"] + \
    [f"{f}_{k}" for f in FEET for k in ("pos_z", "force_z")]


def read_case(case_dir: Path):
    steps: dict[int, list[dict]] = defaultdict(list)
    with open(case_dir / "steps.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            steps[int(r["env_id"])].append({k: r[k] for k in ("terminated", "truncated", "upright", "proj_grav_z")})
    diag: dict[int, list[dict]] = defaultdict(list)
    with gzip.open(case_dir / "diag.csv.gz", "rt", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            diag[int(r["env_id"])].append({k: float(r[k]) for k in DIAG_COLS})
    out = {}
    for env, srows in steps.items():
        drows = diag.get(env, [])
        end = next((i for i, r in enumerate(srows) if r["terminated"] == "1" or r["truncated"] == "1"), None)
        reason = "none" if end is None else ("terminated" if srows[end]["terminated"] == "1" else "truncated")
        cut = len(srows) if end is None else end          # 종료 행(리셋 뒤 상태)은 궤적에서 뺀다
        out[env] = {"s": srows[:cut], "d": drows[:cut], "reason": reason}
    return out


def run_of(flags, k):
    run = 0
    for i, f in enumerate(flags):
        run = run + 1 if f else 0
        if run >= k:
            return i - k + 1
    return None


def stairs_env(ep, force_n, hold):
    d, s = ep["d"], ep["s"]
    if len(d) <= BASE_ROW + 5:
        return {"lift": "BASELINE_MISSING", "end": end_kind(ep)}
    z0 = d[BASE_ROW]["root_z"]
    f0 = {f: d[BASE_ROW][f"{f}_pos_z"] for f in FEET}
    rise = [r["root_z"] - z0 for r in d]
    tail = rise[BASE_ROW:]
    m = max(tail)
    ip = BASE_ROW + tail.index(m)
    last = st.mean(rise[-50:])
    res = {"max_rise": round(m, 4), "end": end_kind(ep)}

    def loaded_up(feet):
        flags = [any(r[f"{f}_pos_z"] - f0[f] >= FOOT_UP and r[f"{f}_force_z"] >= force_n for f in feet) for r in d]
        return run_of(flags, 3)
    t_front, t_hind = loaded_up(FRONT), loaded_up(HIND)
    res["t_front_loaded_s"] = None if t_front is None else round(t_front * DT, 2)
    res["t_hind_loaded_s"] = None if t_hind is None else round(t_hind * DT, 2)
    if m < REACH:
        res["lift"] = "미달"
        return res
    if last >= hold * m:
        res["lift"] = "잔존"
        return res
    res["lift"] = "손실"
    t_loss = next((k for k in range(ip, len(rise)) if rise[k] < hold * m), len(rise) - 1)
    res["t_loss_s"] = round(t_loss * DT, 2)
    if t_front is None or t_front > t_loss:
        res["loss_path"] = "a_앞발하중전"
    elif t_hind is None or t_hind > t_loss:
        res["loss_path"] = "b_앞발하중뒤_뒷발전환전"
    else:
        res["loss_path"] = "c_뒷발하중뒤"
    j = min(len(d) - 1, t_loss + 50)
    res["loss_dx_m"] = round(sum(r["lin_vel_b_x"] for r in d[ip:j + 1]) * DT, 3)
    return res


def end_kind(ep):
    if ep["reason"] == "terminated":
        g = [-float(r["proj_grav_z"]) for r in ep["s"][-50:]] or [1.0]
        c = min(g)
        return "몸접촉종료_뒤집힘(>90°)" if c < 0 else ("몸접촉종료_60~90°" if c < 0.5 else "몸접촉종료_직립(<60°)")
    up = [r["upright"] == "1" for r in ep["s"]]
    return "자세판정만" if run_of([not u for u in up[25:]], 25) is not None else "판정없음(끝까지)"


def rough_event(ep):
    """사건 행 번호와 종류. 몸 접촉 종료면 마지막 궤적 행, 아니면 첫 0.5초 비직립 시작."""
    up = [r["upright"] == "1" for r in ep["s"]]
    pf = run_of([not u for u in up[25:]], 25)
    pf = None if pf is None else pf + 25
    if ep["reason"] == "terminated":
        t_end = len(ep["s"]) - 1
        return (min(pf, t_end) if pf is not None else t_end), "몸접촉종료"
    if pf is not None:
        return pf, "자세판정만"
    return None, "판정없음"


def rough_paths(eps, base, q, k, simul_s):
    c = Counter()
    for ep in eps:
        at, kind = rough_event(ep)
        if at is None or at < BASE_ROW:
            continue
        d = ep["d"]
        lo = max(BASE_ROW, at - 100)
        roll = [abs(r["ang_vel_b_x"]) > base[f"roll{q}"] for r in d[lo:at + 1]]
        supp = [sum(1 for f in FEET if r[f"{f}_force_z"] >= 15.0) <= 1 for r in d[lo:at + 1]]
        tr, ts = run_of(roll, k), run_of(supp, k)
        if tr is None and ts is None:
            p = "판독불가"
        elif ts is None:
            p = "roll선행(지지저하없음)"
        elif tr is None:
            p = "지지선행(roll초과없음)"
        elif abs(tr - ts) * DT <= simul_s:
            p = "동시"
        else:
            p = "지지선행" if ts < tr else "roll선행"
        c[(kind, p)] += 1
    return c


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", default="workspace/_keep")
    ap.add_argument("--out", default="workspace/_keep/go2_g_a067_analysis")
    ap.add_argument("--policies", default=",".join(POLICIES))
    ap.add_argument("--seeds", default=",".join(SEEDS))
    a = ap.parse_args(argv)
    keep, out = Path(a.keep), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pols, seeds = a.policies.split(","), a.seeds.split(",")
    summary = {"definitions": __doc__.split("고정 정의")[1].strip(), "stairs": {}, "rough": {}}
    rows = []
    # 험지 기준 분포: P0 생존 개체 첫 episode(사건 없는 개체)
    base = None
    for pol in pols:
        # ---- 계단
        st_sum = {}
        for force_n, hold, tag in ((15.0, 0.7, "주(15N,70%)"), (10.0, 0.7, "민감도(10N,70%)"),
                                   (20.0, 0.7, "민감도(20N,70%)"), (15.0, 0.5, "민감도(15N,50%)")):
            cnt, by_seed, paths, ends, dx = Counter(), {}, Counter(), Counter(), []
            for seed in seeds:
                eps = read_case(keep / f"go2_g_a066_pc2_{pol}/diag/cases/seed_{seed}/stairs_15_down")
                sc = Counter()
                for env, ep in sorted(eps.items()):
                    r = stairs_env(ep, force_n, hold)
                    cnt[r["lift"]] += 1
                    sc[r["lift"]] += 1
                    ends[(r["lift"], r["end"])] += 1
                    if r["lift"] == "손실":
                        paths[r["loss_path"]] += 1
                        dx.append(r["loss_dx_m"])
                    if tag.startswith("주"):
                        rows.append({"policy": pol, "case": "stairs_15_down", "seed": seed, "env": env, **r})
                by_seed[seed] = dict(sc)
            st_sum[tag] = {"lift": dict(cnt), "lift_by_seed": by_seed, "loss_path": dict(paths),
                           "end_by_lift": {f"{k1}|{k2}": v for (k1, k2), v in ends.items()},
                           "loss_dx_median_m": round(st.median(dx), 3) if dx else None,
                           "loss_back_over_0p3m": sum(1 for v in dx if v < -0.3)}
        summary["stairs"][pol] = st_sum
        # ---- 험지
        all_eps = []
        ev_by_seed = {}
        for seed in seeds:
            eps = read_case(keep / f"go2_g_a066_pc2_{pol}/diag/cases/seed_{seed}/rough_lateral")
            sc = Counter()
            for env, ep in sorted(eps.items()):
                at, kind = rough_event(ep)
                sc[kind] += 1
                rows.append({"policy": pol, "case": "rough_lateral", "seed": seed, "env": env,
                             "event": kind, "end": end_kind(ep)})
                all_eps.append(ep)
            ev_by_seed[seed] = dict(sc)
        if base is None:
            alive = [ep for ep in all_eps if rough_event(ep)[1] == "판정없음"]
            rv = sorted(abs(r["ang_vel_b_x"]) for ep in alive for r in ep["d"][BASE_ROW:])
            base = {"roll99": rv[int(0.99 * len(rv))], "roll95": rv[int(0.95 * len(rv))],
                    "n_alive_envs": len(alive), "policy": pol}
            summary["rough_baseline"] = base
        paths = {}
        for q, k, sim, tag in ((99, 3, 0.06, "주(99%,3행,0.06s)"), (95, 3, 0.06, "민감도(95%)"),
                               (99, 5, 0.06, "민감도(5행)"), (99, 3, 0.02, "민감도(동시0.02s)")):
            paths[tag] = {f"{a}|{b}": v for (a, b), v in rough_paths(all_eps, base, q, k, sim).items()}
        summary["rough"][pol] = {"event_by_seed": ev_by_seed,
                                 "event": dict(Counter(rough_event(ep)[1] for ep in all_eps)),
                                 "end": dict(Counter(end_kind(ep) for ep in all_eps)), "paths": paths}
        print(f"[done] {pol}", flush=True)
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    keys = sorted({k for r in rows for k in r})
    with open(out / "PER_ENV.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    (out / "STATUS.txt").write_text("G_A067_ANALYSIS=COMPLETE\n", encoding="utf-8")
    print("[G-A067 END] COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
