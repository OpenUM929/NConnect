#!/usr/bin/env python3
"""A043(lin_vel_z_l2 −1.5) 감점 요소 증거 모음 (2026-09-28 사용자 지시: "해당 정보들을 모두 수집하여 정리해서 문건으로").

만드는 것 (`reports/evidence/go2_a043_deductions_20260928/`):
  AXIS_DEDUCTIONS.csv   A033·A043·A048·A050 축별 점수·감점·최약 case·묶는 인수
                        (tools/go2_axis_bottleneck.py `case_row`와 같은 식. 총점이 판정 기록과 같아야 한다)
  EVENTS.csv 등         A043 험지 옆걸음 사건표. tools/go2_failure_events.py를 **정의·편의값 그대로** A043에만 적용한다
                        (A048·A033·A038 사건표는 go2_failure_data_20260928/에 이미 있다 — 다시 만들지 않는다)

새 문턱은 없다. 판독 문서: reports/GO2_A043_DEDUCTIONS_20260928.md

    python -B tools/go2_a043_deduction_evidence.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_axis_bottleneck as ab  # noqa: E402
import go2_failure_events as fe  # noqa: E402

KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a043_deductions_20260928"
ARMS = (("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150"),
        ("G-A043", "go2_g_a043_a033_lin_vel_z_m15"),
        ("G-A050", "go2_g_a050_a033_lin_vel_z_m1375"),
        ("G-A048", "go2_g_a048_a033_lin_vel_z_m125"))
RECORDED_TOTAL = {"G-A033": 42.52861, "G-A043": 44.62454, "G-A050": 47.25452, "G-A048": 50.15656}


def axis_rows() -> list[dict]:
    reg = ab.registry()
    std = float(reg["score"]["tracking_proxy_std"])
    out = []
    for arm, run in ARMS:
        total = 0.0
        for sc in reg["scenarios"]:
            cases = sc.get("cases") or sc.get("internal_cases") or []
            rows = []
            for seed in ab.SEEDS:
                for c in cases:
                    cc = f"dr_seed_{seed}" if c.startswith("dr_seed_") else c
                    p = KEEP / run / f"evaluation/candidate/cases/seed_{seed}/{cc}/summary.json"
                    if p.is_file():
                        rows.append(ab.case_row(sc["id"], cc, seed, json.loads(p.read_text(encoding="utf-8")), std))
            rows = [r for r in rows if r["proxy"] is not None]
            worst = min(rows, key=lambda r: r["proxy"])
            full = float(sc["weight"]) * float(reg["score"]["simulation_points"])
            score = worst["proxy"] * full
            total += score
            out.append({"arm": arm, "axis": sc["id"], "points": f"{score:.4f}", "full": f"{full:.2f}",
                        "deduction": f"{full - score:.4f}", "worst_case": worst["case"], "worst_seed": worst["seed"],
                        "survival": f"{worst['survival']:.4f}", "tracking": f"{worst['tracking']:.4f}",
                        "binding_factor": worst["binding_factor"]})
        if abs(total - RECORDED_TOTAL[arm]) > 1e-3:
            raise RuntimeError(f"{arm}: recomputed total {total:.5f} != recorded {RECORDED_TOTAL[arm]}")
        out.append({"arm": arm, "axis": "TOTAL", "points": f"{total:.4f}", "full": "70.00",
                    "deduction": f"{70 - total:.4f}"})
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = axis_rows()
    cols: list[str] = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with (OUT / "AXIS_DEDUCTIONS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    fe.ARMS = (("G-A043", "lin_vel_z_l2 -1.5", "go2_g_a043_a033_lin_vel_z_m15"),)
    fe.OUT = OUT
    return fe.main()


if __name__ == "__main__":
    sys.exit(main())
