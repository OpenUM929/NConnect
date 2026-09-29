"""G-A052 계단 오르기 — 실패 전에 앞발이 첫 단 위에 섰는가(읽기 전용, 사후 기술).

입력: A052 회수본 diag.csv.gz(seed 101, stairs_10_down·stairs_15_down — 이름과 달리 실제로는 오르기),
      판독 정본 EVENTS_DIAG.csv(실패 로봇의 사건 시각 T).
출력(reports/evidence/go2_a052_stairs_foot_on_step_20260928/):
  FOOT_ON_STEP.csv  로봇별 발마다 '단 위에 선' 첫 시각(두 정의)과 출발 지면 대비 최고 발 높이.
  SUMMARY.txt       case·결과 묶음별 집계.
정의(발 f, 시각 t = step x 0.02 s — EVENTS_DIAG 의 T 와 같은 원점, 실패 로봇은 t <= T, 생존 로봇은 t <= 20 s):
  z0 = 첫 행 네 발 아래 지형 높이(*_terrain_z_near_derived)의 최솟값.
  loose : f_force_z > 5 N  그리고  f 아래 지형 - z0 > 단 높이 x 0.5
  strict: loose 그리고 f_pos_z - z0 > 단 높이 x 0.8
  loose 이지만 strict 아닌 앞발 = 모서리 턱에 걸치거나 밀착한 상태로 '보이는' 경우(판정 아님, 발 걸림 확인 아님).
  *_on_*_s 는 조건을 '처음 한 번' 충족한 시각이다. 지속 지지가 아니다. *_strict_rows 는 조건을 충족한 행 수(x 0.02 s)다.
  '앞발이 섰다' 집계는 앞발 중 하나 이상이다. 양쪽 앞발은 front_both_strict 로 따로 센다.
한계: 발 아래 지형은 파생 채널이라 모서리 근처 값이 불확실하다. 하중을 받은 발의 높이는 지면보다 약 0.023 m
높게 기록된다(발 반지름, 평지 1~2 s 접촉력 > 5 N 행 중앙값). 초판의 '약 0.07 m'는 착지 전 첫 행 값이라 틀렸다(2026-09-28 정정). 정책 하나(A048)·평가 seed 하나·첫 episode. 시간 순서는 인과가 아니다.
"""
from __future__ import annotations

import csv
import gzip
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases/seed_101"
EVENTS = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a052_diag_20260928/EVENTS_DIAG.csv"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a052_stairs_foot_on_step_20260928"
CASES = (("stairs_10_down", 0.10), ("stairs_15_down", 0.15))
FEET = ("FL", "FR", "RL", "RR")
DT = 0.02
FORCE_N = 5.0
HORIZON_S = 20.0


def events() -> dict[tuple[str, int], float]:
    with EVENTS.open(encoding="utf-8") as fh:
        return {(r["case"], int(r["env_id"])): float(r["T"]) for r in csv.DictReader(fh)}


def analyse(case: str, h: float, ev: dict) -> list[dict]:
    rows: dict[int, list[dict]] = {}
    with gzip.open(KEEP / case / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(int(r["env_id"]), []).append(r)
    out = []
    for env, rs in sorted(rows.items()):
        rs.sort(key=lambda r: int(r["step"]))
        T = ev.get((case, env))
        z0 = min(float(rs[0][f + "_terrain_z_near_derived"]) for f in FEET)
        rec = {"case": case, "step_m": h, "env_id": env, "fail": int(T is not None), "T": "" if T is None else T}
        for f in FEET:
            loose = strict = None
            n_strict = 0
            maxz = float("-inf")
            for r in rs:
                t = int(r["step"]) * DT
                if t > (T if T is not None else HORIZON_S):
                    break
                foot_z = float(r[f + "_pos_z"]) - z0
                maxz = max(maxz, foot_z)
                if float(r[f + "_force_z"]) > FORCE_N and float(r[f + "_terrain_z_near_derived"]) - z0 > 0.5 * h:
                    if loose is None:
                        loose = round(t, 2)
                    if foot_z > 0.8 * h:
                        n_strict += 1
                        if strict is None:
                            strict = round(t, 2)
            rec[f + "_on_loose_s"] = "" if loose is None else loose
            rec[f + "_on_strict_s"] = "" if strict is None else strict
            rec[f + "_strict_rows"] = n_strict
            rec[f + "_max_z_m"] = round(maxz, 3)
        out.append(rec)
    return out


def first(rec: dict, feet: tuple[str, ...], kind: str):
    vals = [rec[f"{f}_on_{kind}_s"] for f in feet if rec[f"{f}_on_{kind}_s"] != ""]
    return min(vals) if vals else None


def summary(recs: list[dict]) -> list[str]:
    lines = []
    for case, _h in CASES:
        for label, flag in (("FAIL", 1), ("SURV", 0)):
            g = [r for r in recs if r["case"] == case and r["fail"] == flag]
            if not g:
                continue
            fl = sum(first(r, ("FL", "FR"), "loose") is not None for r in g)
            fs = sum(first(r, ("FL", "FR"), "strict") is not None for r in g)
            rs_ = sum(first(r, ("RL", "RR"), "strict") is not None for r in g)
            both = sum(r["FL_on_strict_s"] != "" and r["FR_on_strict_s"] != "" for r in g)
            front_rows = [max(r["FL_strict_rows"], r["FR_strict_rows"]) * DT for r in g
                          if first(r, ("FL", "FR"), "strict") is not None]
            maxf = st.median(max(r["FL_max_z_m"], r["FR_max_z_m"]) for r in g)
            lines.append(f"{case} {label} n={len(g)} front_on_strict={fs} front_on_loose={fl} "
                         f"front_loose_not_strict={fl - fs} front_both_strict={both} rear_on_strict={rs_} median_max_front_z={maxf:.3f}")
            if front_rows:
                lines.append(f"  front strict time (longer foot, s): median {st.median(front_rows):.2f}, "
                             f"min {min(front_rows):.2f}, max {max(front_rows):.2f}")
            lag = [r["T"] - first(r, ("FL", "FR"), "strict") for r in g
                   if flag == 1 and first(r, ("FL", "FR"), "strict") is not None]
            if lag:
                lines.append(f"  T - first front strict: median {st.median(lag):.2f} s, min {min(lag):.2f}, max {max(lag):.2f}")
    return lines


def main() -> None:
    ev = events()
    recs = [r for case, h in CASES for r in analyse(case, h, ev)]
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "FOOT_ON_STEP.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(recs)
    lines = summary(recs)
    (OUT / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
