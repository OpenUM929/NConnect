"""G-A052 계단 오르기 — 몸통 상승이 끊기는 동안 앞발·뒷발 수직 접촉력(A048 한 정책 안, 읽기 전용, 사후 기술).

Codex 범위(2026-09-28): 저장됐지만 쓰지 않은 접촉력 크기로 기존 설명을 검토한다. 질문:
  몸통 상승이 끊기는 동안 앞발·뒷발의 수직 접촉력은 어떻게 유지되거나 줄어드는가?
  -> 힘 감소가 하강보다 먼저인가 / 힘은 유지되는데 상승이 이어지지 않는가 / 섞여 구분되지 않는가 (판단은 Codex).
저장 방식(tools 가 아니라 기록기 workspace/training/quadruped/go2_eval_diag.py 와 diag_meta.json 에서 확인):
  *_force_z     contact sensor _data.net_forces_w 의 z 성분(월드 좌표, N). 센서 갱신 주기 0.005 s, 한 행(0.02 s)에는
                마지막 갱신값 하나만 담긴다(4 개 substep 평균 아님).
  *_force_hist_max  최근 3 회 갱신(약 15 ms)의 |힘| 최댓값. 이 도구는 쓰지 않는다(순간 충격이 섞인다).
  contact_fresh 0 인 행(리셋 행)은 버린다.
정의(결과를 보기 전에 고정, 바꾸지 않는다):
  시각 t = step x 0.02 s(T 와 같은 원점). 실패 로봇 t <= T, 생존 로봇 t <= 20 s.
  정규화 W0 = 로봇마다 평지 구간 [1.0, 2.0) s 네 발 force_z 합의 평균(평지 보행 평균 지지력, 몸무게의 대리값).
  front_n = (FL+FR force_z)/W0, rear_n = (RL+RR force_z)/W0, total_n = 합/W0.
  발 미끄럼 = 그 발 force_z > 1 N(센서 force_threshold 와 같은 값) 인 행의 발 월드 수평속도 크기. 앞발·뒷발 각각 평균.
  dz = root_z - 기준 시각 root_z.
  정렬 A: t_front(go2_a052_stairs_edge_process 와 같은 앞발 표지) 기준 0.2 s 칸 [-0.4, 2.0].
          묶음: 10cm 실패(표지 있음)·10cm 생존·15cm 실패(표지 있음)·15cm 생존(1대, 참고).
          10cm 생존 p10·p90 을 함께 적는다(기술 비교, 판정 아님).
  정렬 B: 사건 시각 T 기준 0.1 s 칸 [-1.0, 0.0). dz 기준은 T-1.0 s. 묶음: 10cm·15cm 실패 × 표지 있음/없음.
  힘이 크면 안정 지지, 작으면 지지 실패라는 문턱은 두지 않는다. 힘으로 '힘 부족'이나 '보상 억제'를 확정하지 않는다.
한계: 정책 하나·평가 seed 101·첫 episode. 한 행은 20 ms 중 한 순간의 힘이다. 접촉력은 발 하나의 합력이라
  단 윗면 지지인지 모서리 측면 접촉인지 구분하지 않는다. 15cm 생존은 1대다. 집단 칸 중앙값을 한 로봇의 순서로 잇지 않는다.

    python -B tools/go2_a052_stairs_contact_force.py
"""
from __future__ import annotations

import csv
import gzip
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a052_stairs_edge_process as edge  # noqa: E402
import go2_a052_stairs_foot_on_step as fos  # noqa: E402

OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a052_stairs_contact_force_20260928"
DT = fos.DT
FORCE_ON_N = 1.0
BINS_A = [round(-0.4 + 0.2 * k, 2) for k in range(13)]
BINS_B = [round(-1.0 + 0.1 * k, 2) for k in range(10)]
METRICS = ("front_n", "rear_n", "total_n", "dz", "front_slip", "rear_slip")


def rows_for(rs: list[dict], h: float, T: float | None) -> list[dict]:
    z0 = min(float(rs[0][f + "_terrain_z_near_derived"]) for f in fos.FEET)
    end = T if T is not None else fos.HORIZON_S
    out = []
    for r in rs:
        t = int(r["step"]) * DT
        if t > end + 1e-9:
            break
        if r["contact_fresh"] != "1":
            continue
        fz = {f: float(r[f + "_force_z"]) for f in fos.FEET}
        spd = {f: (float(r[f + "_vel_x"]) ** 2 + float(r[f + "_vel_y"]) ** 2) ** 0.5 for f in fos.FEET}
        mark = any(fz[f] > fos.FORCE_N and float(r[f + "_terrain_z_near_derived"]) - z0 > 0.5 * h
                   and float(r[f + "_pos_z"]) - z0 > 0.8 * h for f in ("FL", "FR"))
        out.append({"t": round(t, 2), "root_z": float(r["root_z"]), "fz": fz, "spd": spd, "front_mark": mark})
    return out


def binvals(rows: list[dict], w0: float, z_ref: float) -> dict[str, float | None]:
    def slip(feet: tuple[str, ...]) -> float | None:
        v = [x["spd"][f] for x in rows for f in feet if x["fz"][f] > FORCE_ON_N]
        return st.mean(v) if v else None
    return {"front_n": st.mean(x["fz"]["FL"] + x["fz"]["FR"] for x in rows) / w0,
            "rear_n": st.mean(x["fz"]["RL"] + x["fz"]["RR"] for x in rows) / w0,
            "total_n": st.mean(sum(x["fz"].values()) for x in rows) / w0,
            "dz": st.mean(x["root_z"] for x in rows) - z_ref,
            "front_slip": slip(("FL", "FR")), "rear_slip": slip(("RL", "RR"))}


def series(p: list[dict], w0: float, t_ref: float, z_ref: float, bins: list[float], width: float) -> dict:
    out = {}
    for b in bins:
        rows = [x for x in p if t_ref + b - 1e-9 <= x["t"] < t_ref + b + width - 1e-9]
        if rows:
            out[b] = binvals(rows, w0, z_ref)
    return out


def med(v: list[float]) -> float | str:
    return round(st.median(v), 4) if v else ""


def main() -> None:
    ev = fos.events()
    OUT.mkdir(parents=True, exist_ok=True)
    groups_a: dict[str, list[dict]] = {}
    groups_b: dict[str, list[dict]] = {}
    w0s: list[float] = []
    for case, h in fos.CASES:
        tag = "10" if case == "stairs_10_down" else "15"
        for env, rs in edge.load(case).items():
            T = ev.get((case, env))
            p = rows_for(rs, h, T)
            flat = [x for x in p if 1.0 - 1e-9 <= x["t"] < 2.0 - 1e-9]
            w0 = st.mean(sum(x["fz"].values()) for x in flat)
            w0s.append(w0)
            tf = next((x["t"] for x in p if x["front_mark"]), None)
            if tf is not None:
                z_ref = next(x["root_z"] for x in p if x["t"] >= tf)
                key = f"{tag}_{'fail' if T is not None else 'surv'}_marked"
                groups_a.setdefault(key, []).append(series(p, w0, tf, z_ref, BINS_A, 0.2))
            if T is not None:
                z_ref = next(x["root_z"] for x in p if x["t"] >= T - 1.0 - 1e-9)
                key = f"{tag}_fail_{'marked' if tf is not None else 'nomark'}"
                groups_b.setdefault(key, []).append(series(p, w0, T, z_ref, BINS_B, 0.1))

    ref = groups_a.get("10_surv_marked", [])
    rows_a = []
    for key, ss in sorted(groups_a.items()):
        for b in BINS_A:
            line: dict = {"group": key, "n_robots": len(ss), "bin_start_s": b}
            for m in METRICS:
                v = [s[b][m] for s in ss if b in s and s[b][m] is not None]
                line[m] = med(v)
                line[m + "_n"] = len(v)
                rv = [s[b][m] for s in ref if b in s and s[b][m] is not None]
                line[m + "_surv10_p10"] = round(edge.pct(rv, 0.10), 4) if rv else ""
                line[m + "_surv10_p90"] = round(edge.pct(rv, 0.90), 4) if rv else ""
            rows_a.append(line)
    rows_b = []
    for key, ss in sorted(groups_b.items()):
        for b in BINS_B:
            line = {"group": key, "n_robots": len(ss), "bin_start_s": b}
            for m in METRICS:
                v = [s[b][m] for s in ss if b in s and s[b][m] is not None]
                line[m] = med(v)
                line[m + "_n"] = len(v)
            rows_b.append(line)
    edge.write_csv(OUT / "FORCE_ALIGNED_FRONT.csv", rows_a)
    edge.write_csv(OUT / "FORCE_ALIGNED_T.csv", rows_b)

    lines = ["storage: force_z = world z of net contact force at the last 0.005 s sensor update of each 0.02 s row (N)",
             f"W0 (flat [1,2) s mean total force_z) over {len(w0s)} robots: median {st.median(w0s):.1f} N, "
             f"min {min(w0s):.1f}, max {max(w0s):.1f}", "",
             "A. aligned to t_front (0.2 s bins): group median of front_n / rear_n / total_n / dz / front_slip / rear_slip"]
    for key in sorted(groups_a):
        lines.append(f"  {key} (n={len(groups_a[key])})")
        for r in (x for x in rows_a if x["group"] == key):
            lines.append("    " + f"{r['bin_start_s']:+.1f}  " + "  ".join(f"{m} {r[m]}" for m in METRICS))
    lines += ["", "B. aligned to T (0.1 s bins, dz from T-1 s): group median"]
    for key in sorted(groups_b):
        lines.append(f"  {key} (n={len(groups_b[key])})")
        for r in (x for x in rows_b if x["group"] == key):
            lines.append("    " + f"{r['bin_start_s']:+.1f}  " + "  ".join(f"{m} {r[m]}" for m in METRICS))
    (OUT / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
