#!/usr/bin/env python3
"""A048 걸음별 체공 시간 — feet_air_time 보상이 지금 어느 쪽으로 작용하는지 (2026-09-29, 사용자 요청).

입력 (새 서버 실행 없음): G-A052 A048 진단 재생
  workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases/seed_101/stairs_15_down  (15cm 오르기)
  workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases/seed_101/stairs_10_down  (10cm 오르기)
  workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases/seed_202/rough_lateral   (험지 옆걸음)
A048 학습 설정(training/env.yaml): feet_air_time weight 0.2, threshold 0.5, body_names .*_foot.
Isaac Lab 식: 보상 = Σ_발 (last_air_time − 0.5) · first_contact  (명령 크기 > 0.1일 때만).
  → 착지한 걸음의 체공이 0.5초보다 짧으면 그 걸음은 벌점, 길면 보상이다.

걸음 = 한 발의 착지(first_contact=1) 한 번.  그 걸음의 값:
  air_s   착지 순간의 {발}_last_air_time (센서가 보상에 넘기는 값 그대로)
  lift_m  그 체공 동안 발 z 최고점 − 들어 올린 순간의 발 z  (계단이면 들어 올린 단 기준 높이)
  term    air_s − 0.5 (그 걸음이 보상식에 더하는 값, 가중치 곱하기 전)
로봇마다 첫 episode만, 0.5초 이후, 낙상이면 낙상 시각 전까지. 낙상 정의는 tools/go2_a043_tilt_onset.py.
출력: reports/evidence/go2_a048_air_time_20260929/STEPS.csv, SUMMARY.csv, BINS.csv
한계: 정책 하나·평가 seed 하나씩. 체공 구간은 이 도구가 나눈 것이며(발 접촉 문턱 1.0 N), 관계는 상관이지 인과가 아니다.
"""
from __future__ import annotations

import csv
import gzip
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_a043_tilt_onset as onset_mod  # noqa: E402

KEEP = ROOT / "workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases"
CASES = {"stairs15_up": KEEP / "seed_101/stairs_15_down",
         "stairs10_up": KEEP / "seed_101/stairs_10_down",
         "rough_lateral": KEEP / "seed_202/rough_lateral"}
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a048_air_time_20260929"
FEET = ("FL", "FR", "RL", "RR")
DT, T0, THRESH = 0.02, 0.5, 0.5
BIN_EDGES = (0.1, 0.2, 0.3, 0.4, 0.5)  # 서술용 구간. 판정 문턱이 아니다(0.5는 보상식의 threshold).


def ends(case_dir: Path) -> dict[int, tuple[float, int]]:
    envs = onset_mod.load(case_dir / "steps.csv")
    out = {}
    for e, rows in envs.items():
        tf = onset_mod.fall_time(rows)
        out[e] = (tf if tf is not None else rows[-1]["time_s"] + 1e-9, int(tf is not None))
    return out


def case_steps(label: str, case_dir: Path) -> list[dict]:
    end = ends(case_dir)
    swing: dict[tuple[int, str], dict] = {}
    rows_out = []
    with gzip.open(case_dir / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            e, t = int(r["env_id"]), int(r["step"]) * DT
            t_end, fell = end.get(e, (-1, 0))
            if t >= t_end:
                continue
            for f in FEET:
                key = (e, f)
                z = float(r[f"{f}_pos_z"])
                in_contact = float(r[f"{f}_force_z"]) > 1.0
                if int(float(r[f"{f}_first_contact"])) == 1:
                    s = swing.pop(key, None)
                    if s is not None and t >= T0 and s["t_lift"] >= T0:
                        air = float(r[f"{f}_last_air_time"])
                        rows_out.append({"case": label, "env_id": e, "foot": f, "fell": fell, "t_s": round(t, 2),
                                         "air_s": round(air, 3), "lift_m": round(s["zmax"] - s["z0"], 4),
                                         "term": round(air - THRESH, 3)})
                elif not in_contact:
                    s = swing.get(key)
                    if s is None:
                        swing[key] = {"t_lift": t, "z0": z, "zmax": z}
                    else:
                        s["zmax"] = max(s["zmax"], z)
                else:
                    swing.pop(key, None)
    return rows_out


def summarize(rows: list[dict], group: str) -> dict:
    air = [r["air_s"] for r in rows]
    lift = [r["lift_m"] for r in rows]
    return {"group": group, "steps": len(rows),
            "air_median_s": round(st.median(air), 3) if air else "",
            "air_p90_s": round(sorted(air)[int(0.9 * (len(air) - 1))], 3) if air else "",
            "share_below_0.5": round(sum(a < THRESH for a in air) / len(air), 3) if air else "",
            "term_mean": round(st.fmean(a - THRESH for a in air), 3) if air else "",
            "lift_median_m": round(st.median(lift), 4) if lift else ""}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    steps = []
    for label, d in CASES.items():
        steps += case_steps(label, d)
    summary, bins = [], []
    for label in CASES:
        sel = [r for r in steps if r["case"] == label]
        for grp, cond in (("all", lambda r: True), ("fell", lambda r: r["fell"] == 1), ("survived", lambda r: r["fell"] == 0)):
            summary.append({"case": label, **summarize([r for r in sel if cond(r)], grp)})
        lo = 0.0
        for hi in BIN_EDGES + (99.0,):
            b = [r for r in sel if lo <= r["air_s"] < hi]
            lifts = [r["lift_m"] for r in b]
            bins.append({"case": label, "air_from_s": lo, "air_to_s": hi if hi < 99 else "", "steps": len(b),
                         "lift_median_m": round(st.median(lifts), 4) if lifts else "",
                         "lift_p90_m": round(sorted(lifts)[int(0.9 * (len(lifts) - 1))], 4) if lifts else ""})
            lo = hi
    for name, rows in (("STEPS.csv", steps), ("SUMMARY.csv", summary), ("BINS.csv", bins)):
        with (OUT / name).open("w", encoding="utf-8", newline="\n") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print(json.dumps({"steps": len(steps)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
