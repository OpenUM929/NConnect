"""G-A052 계단 오르기 — 앞발 접촉 이후 과정(A048 한 정책 안, 읽기 전용, 사후 기술).

Codex 결정 G-D-STAIRS-EDGE-COMPARE-20260928 범위 1. 질문 셋:
  Q1 앞발 접촉 표지 뒤 접촉이 유지되는가, 몸통 상승·전진이 시작되는가
  Q2 상승하지 못하거나 무너질 때 pitch·roll 방향과 높이 변화가 어떻게 이어지는가
  Q3 10cm 실패 8대가 생존 24대와 어느 동작부터 달라지는가
입력: A052 회수본 seed_101 stairs_10_down·stairs_15_down 의 diag.csv.gz(이름과 달리 오르기), EVENTS_DIAG.csv 의 T.
출력(reports/evidence/go2_a052_stairs_edge_process_20260928/):
  SIGN_CHECK.txt        pitch 부호 확인(아래 규칙). 통과하지 못하면 pitch 열은 원 부호로만 쓰고 방향을 해석하지 않는다.
  EDGE_PER_ENV.csv      로봇별 접촉 뒤 1 s 창·붕괴 전 1 s 창 값.
  EDGE_ALIGNED_BINS.csv 10cm, t_front 정렬 0.2 s 칸별 실패·생존 중앙값과 생존 p10·p90.
  SUMMARY.txt           요약.
정의(결과를 보기 전에 고정, 바꾸지 않는다):
  시각 t = step x 0.02 s(T 와 같은 원점). 실패 로봇은 t <= T, 생존 로봇은 t <= 20 s(첫 episode).
  같은 0.02 s 안의 선후는 가리지 않는다.
  앞발 접촉 표지: go2_a052_stairs_foot_on_step 의 strict 조건(접촉력 > 5 N, 발 아래 지형 > 단 0.5, 발 높이 > 단 0.8)을
    FL·FR 중 하나 이상이 만족. t_front = 처음 만족한 시각. 이것은 '안정적으로 올라섰다'가 아니다.
  접촉 뒤 창 W = [t_front, t_front + 1.0 s] (실패는 T 에서 자른다, 길이 W_len_s 기록).
    front_hold       W 안에서 앞발 표지(하나 이상)가 켜진 행 비율. front_both_hold 는 양쪽 모두.
    rise_max_m       W 안 root_z 최댓값 - t_front 의 root_z. rise_end_m 은 W 끝 값 - 시작 값.
    fwd_mps          W 안 lin_vel_b_x 평균(명령 +x 0.5 m/s).
    rear_on_after_s  뒷발(RL·RR) strict 첫 시각 - t_front(없으면 빈칸).
    pitch_up_*       = -grav_b_x (부호 확인 통과 시에만 '앞 들림 양수'로 해석). roll_abs_max = max|grav_b_y|.
  붕괴 창(실패만) C = [T - 1.0 s, T]: C_dz_m(root_z 끝-처음), C_dpitch_up(끝-처음), C_pitch_abs_T=|grav_b_x|(T),
    C_roll_abs_T=|grav_b_y|(T), C_front_hold. C_pitch_up_T(= -grav_b_x at T)는 결과 확인 뒤 추가한 기술 열이다(부호 확인용,
    판정 기준 아님).
  pitch 부호 확인: 10cm 생존 로봇의 W 행을 모아 (앞발 평균 높이 - 뒷발 평균 높이) 와 -grav_b_x 의 상관이 양수이고,
    로봇별 W 의 -grav_b_x 중앙값이 평지 구간 [1.0, 2.0) s 중앙값보다 큰 로봇이 24대 중 20대 이상이면 통과.
  기술 비교 기준(판정 아님): 10cm 생존 24대 분포의 p10·p90. 칸별 '갈라짐'은 실패 중앙값이 생존 [p10, p90] 밖에
    처음 놓인 칸.
  15cm 는 따로 쓴다. 생존 1대(env30)는 참고 사례이지 성공 기준이 아니다. 10cm 생존과의 차이에는 단 높이 차이도 들어 있다.
한계: 정책 하나·평가 seed 하나·첫 episode. 발·지형 채널은 파생값이 섞여 모서리 근처가 불확실하다. 몸체 기하는 쓰지 않는다
  (앞·뒤 몸통 높이는 계산하지 않고 발 높이 차만 부호 확인에 쓴다). pitch·높이로 '벌점 때문'과 '힘 부족'을 가리지 않는다.

    python -B tools/go2_a052_stairs_edge_process.py
"""
from __future__ import annotations

import csv
import gzip
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a052_stairs_foot_on_step as fos  # noqa: E402

OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a052_stairs_edge_process_20260928"
DT = fos.DT
WIN_S = 1.0
BIN_S = 0.2
BINS = [round(-0.4 + BIN_S * k, 2) for k in range(13)]  # -0.4 .. 2.0
METRICS = ("front", "rear_cum", "dz", "pitch_up", "vx")


def load(case: str) -> dict[int, list[dict]]:
    rows: dict[int, list[dict]] = {}
    with gzip.open(fos.KEEP / case / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(int(r["env_id"]), []).append(r)
    for rs in rows.values():
        rs.sort(key=lambda r: int(r["step"]))
    return rows


def prep(rs: list[dict], h: float, T: float | None) -> list[dict]:
    z0 = min(float(rs[0][f + "_terrain_z_near_derived"]) for f in fos.FEET)
    end = T if T is not None else fos.HORIZON_S
    out = []
    for r in rs:
        t = int(r["step"]) * DT
        if t > end + 1e-9:
            break
        on = {f: (float(r[f + "_force_z"]) > fos.FORCE_N
                  and float(r[f + "_terrain_z_near_derived"]) - z0 > 0.5 * h
                  and float(r[f + "_pos_z"]) - z0 > 0.8 * h) for f in fos.FEET}
        out.append({"t": round(t, 2), "root_z": float(r["root_z"]), "gx": float(r["grav_b_x"]),
                    "gy": float(r["grav_b_y"]), "vx": float(r["lin_vel_b_x"]),
                    "front": on["FL"] or on["FR"], "front_both": on["FL"] and on["FR"],
                    "rear": on["RL"] or on["RR"],
                    "dfoot": (float(r["FL_pos_z"]) + float(r["FR_pos_z"])
                              - float(r["RL_pos_z"]) - float(r["RR_pos_z"])) / 2})
    return out


def window(p: list[dict], a: float, b: float) -> list[dict]:
    return [x for x in p if a - 1e-9 <= x["t"] <= b + 1e-9]


def corr(xs: list[float], ys: list[float]) -> float:
    mx, my = st.mean(xs), st.mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return sxy / (sx * sy) if sx and sy else float("nan")


def pct(v: list[float], q: float) -> float:
    s = sorted(v)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def per_env(case: str, env: int, p: list[dict], T: float | None) -> dict:
    rec: dict = {"case": case, "env_id": env, "fail": int(T is not None), "T": "" if T is None else T}
    tf = next((x["t"] for x in p if x["front"]), None)
    rec["t_front"] = "" if tf is None else tf
    if tf is not None:
        W = window(p, tf, tf + WIN_S)
        z_start = W[0]["root_z"]
        rec.update({
            "W_len_s": round(W[-1]["t"] - tf, 2),
            "front_hold": round(sum(x["front"] for x in W) / len(W), 3),
            "front_both_hold": round(sum(x["front_both"] for x in W) / len(W), 3),
            "rise_max_m": round(max(x["root_z"] for x in W) - z_start, 4),
            "rise_end_m": round(W[-1]["root_z"] - z_start, 4),
            "fwd_mps": round(st.mean(x["vx"] for x in W), 4),
            "pitch_up_start": round(-W[0]["gx"], 4),
            "pitch_up_max": round(max(-x["gx"] for x in W), 4),
            "pitch_up_end": round(-W[-1]["gx"], 4),
            "roll_abs_max": round(max(abs(x["gy"]) for x in W), 4),
        })
        rear = next((x["t"] for x in p if x["rear"] and x["t"] >= tf), None)
        rec["rear_on_after_s"] = "" if rear is None else round(rear - tf, 2)
    if T is not None:
        C = window(p, T - WIN_S, T)
        rec.update({
            "C_dz_m": round(C[-1]["root_z"] - C[0]["root_z"], 4),
            "C_dpitch_up": round(-C[-1]["gx"] + C[0]["gx"], 4),
            "C_pitch_abs_T": round(abs(C[-1]["gx"]), 4),
            "C_pitch_up_T": round(-C[-1]["gx"], 4),
            "C_roll_abs_T": round(abs(C[-1]["gy"]), 4),
            "C_front_hold": round(sum(x["front"] for x in C) / len(C), 3),
        })
    return rec


def sign_check(surv: list[tuple[list[dict], float]]) -> tuple[bool, list[str]]:
    xs, ys, votes = [], [], 0
    for p, tf in surv:
        W = window(p, tf, tf + WIN_S)
        flat = window(p, 1.0, 2.0 - DT)
        xs += [x["dfoot"] for x in W]
        ys += [-x["gx"] for x in W]
        votes += st.median(-x["gx"] for x in W) > st.median(-x["gx"] for x in flat)
    c = corr(xs, ys)
    ok = c > 0 and votes >= 20
    return ok, [f"10cm survivors n={len(surv)} rows={len(xs)}",
                f"corr(front-rear foot height, -grav_b_x) in W = {c:.3f} (required > 0)",
                f"robots with median(-grav_b_x) in W > flat [1,2) s: {votes}/{len(surv)} (required >= 20)",
                f"PASS={ok} -> pitch_up = -grav_b_x read as 'nose up positive' only if PASS"]


def series(p: list[dict], tf: float) -> dict[float, dict[str, float]]:
    z_ref = next(x["root_z"] for x in p if x["t"] >= tf)
    rear_seen, out = False, {}
    for b in BINS:
        rows = window(p, tf + b, tf + b + BIN_S - DT)
        if not rows:
            continue
        rear_seen = rear_seen or any(x["rear"] and x["t"] >= tf for x in rows)
        out[b] = {"front": sum(x["front"] for x in rows) / len(rows), "rear_cum": float(rear_seen),
                  "dz": st.mean(x["root_z"] for x in rows) - z_ref,
                  "pitch_up": st.mean(-x["gx"] for x in rows), "vx": st.mean(x["vx"] for x in rows)}
    return out


def aligned_bins(fail: list[tuple[list[dict], float]], surv: list[tuple[list[dict], float]]) -> list[dict]:
    fs = [series(p, tf) for p, tf in fail]
    ss = [series(p, tf) for p, tf in surv]
    out = []
    for b in BINS:
        for m in METRICS:
            fv = [s[b][m] for s in fs if b in s]
            sv = [s[b][m] for s in ss if b in s]
            if not fv or not sv:
                continue
            lo, hi = pct(sv, 0.10), pct(sv, 0.90)
            fm = st.median(fv)
            out.append({"bin_start_s": b, "metric": m, "fail_n": len(fv), "fail_median": round(fm, 4),
                        "surv_n": len(sv), "surv_median": round(st.median(sv), 4), "surv_p10": round(lo, 4),
                        "surv_p90": round(hi, 4), "outside": int(fm < lo or fm > hi)})
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ev = fos.events()
    OUT.mkdir(parents=True, exist_ok=True)
    recs: list[dict] = []
    groups: dict[str, dict[str, list]] = {}
    for case, h in fos.CASES:
        g = groups.setdefault(case, {"fail": [], "surv": []})
        for env, rs in load(case).items():
            T = ev.get((case, env))
            p = prep(rs, h, T)
            recs.append(per_env(case, env, p, T))
            tf = recs[-1]["t_front"]
            if tf != "":
                g["fail" if T is not None else "surv"].append((p, tf))
    _ok, sign_lines = sign_check(groups["stairs_10_down"]["surv"])
    (OUT / "SIGN_CHECK.txt").write_text("\n".join(sign_lines) + "\n", encoding="utf-8")
    write_csv(OUT / "EDGE_PER_ENV.csv", recs)
    bins = aligned_bins(groups["stairs_10_down"]["fail"], groups["stairs_10_down"]["surv"])
    write_csv(OUT / "EDGE_ALIGNED_BINS.csv", bins)

    lines = sign_lines + [""]
    surv10 = [r for r in recs if r["case"] == "stairs_10_down" and not r["fail"] and r["t_front"] != ""]
    for case, _h in fos.CASES:
        for label, flag in (("FAIL", 1), ("SURV", 0)):
            g = [r for r in recs if r["case"] == case and r["fail"] == flag]
            withf = [r for r in g if r["t_front"] != ""]
            lines.append(f"{case} {label} n={len(g)} with_front_mark={len(withf)}")
            for k in ("W_len_s", "front_hold", "front_both_hold", "rise_max_m", "rise_end_m", "fwd_mps",
                      "pitch_up_start", "pitch_up_max", "pitch_up_end", "roll_abs_max"):
                v = [r[k] for r in withf]
                if v:
                    lines.append(f"  {k}: median {st.median(v):.4f}  min {min(v):.4f}  max {max(v):.4f}")
            rear = [r["rear_on_after_s"] for r in withf]
            lines.append(f"  rear_on within window: {sum(1 for x in rear if x != '' and x <= WIN_S)}/{len(withf)}")
            if flag:
                for k in ("C_dz_m", "C_dpitch_up", "C_pitch_abs_T", "C_roll_abs_T", "C_front_hold"):
                    v = [r[k] for r in g]
                    lines.append(f"  {k}: median {st.median(v):.4f}  min {min(v):.4f}  max {max(v):.4f}")
                n_pitch = sum(r["C_pitch_abs_T"] > r["C_roll_abs_T"] for r in g)
                lines.append(f"  pitch dominant at T (|gx|>|gy|): {n_pitch}/{len(g)}")
                for k in ("front_hold", "rise_max_m", "fwd_mps"):
                    lo = pct([r[k] for r in surv10], 0.10)
                    n = sum(1 for r in withf if r[k] < lo)
                    lines.append(f"  {k} below 10cm-survivor p10 ({lo:.4f}): {n}/{len(withf)}")
    lines += ["", "10cm aligned bins: first bin where fail median is outside survivor [p10,p90]"]
    for m in METRICS:
        first_out = next((b["bin_start_s"] for b in bins if b["metric"] == m and b["outside"]), None)
        lines.append(f"  {m}: {first_out}")
    (OUT / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
