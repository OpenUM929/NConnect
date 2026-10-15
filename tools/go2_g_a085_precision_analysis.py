#!/usr/bin/env python3
"""G-A085 precision analysis (standard library only; runs on PC2 after the evaluation).

For every policy it reads the 69-case evaluations of each seed set (the stored original
101/202/303 set when present, plus the new 404/505/606 and 707/808/909 sets) and writes

  ROWS.csv      one row per policy x seed x case: survival, tracking (H1 official-fit
                formula), exy/eyaw means, along speed, falls by kind, stairs full count
  SUMMARY.json  per policy: score per seed set, mean and sd over seed sets, per-case
                mean/sd over seeds, the G-A084 preregistered metrics on all seeds

The per-row numbers reproduce tools/go2_weakness_breakdown.py (pandas) on the same
steps.csv; tools/test_go2_g_a085_package.py checks that on the stored G-A083 evaluation.

    python go2_g_a085_precision_analysis.py --arm KEY=DIR [--arm KEY=DIR ...] --out OUTDIR
    (DIR is an evaluation folder that holds cases/seed_*/<case>/)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import go2_climb_count as climb  # noqa: E402

SCALE, SKIP = 0.70, 50
W = {"G1": .15, "G2": .15, "G3": .20, "G4": .15, "G5": .15, "G6": .10, "G7": .10}
CASES = {
    "G1": ("forward_slow", "forward_nominal", "forward_fast"),
    "G2": ("backward", "left", "right", "diagonal_left", "diagonal_right", "combined_yaw_left", "combined_yaw_right"),
    "G3": ("rough_forward", "rough_lateral"),
    "G4": ("slope_plus_20", "slope_minus_20"),
    "G5": ("stairs_10_up", "stairs_10_down", "stairs_15_up", "stairs_15_down"),
    "G6": ("push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y"),
}
HEADING = ("slope_plus_20", "stairs_10_down", "stairs_15_down")


def fnum(v: str) -> float:
    return float(v) if v not in ("", "nan", "None") else math.nan


def case_row(d: Path) -> dict:
    s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    track = track_noyaw = exy = eyaw = 0.0
    n = 0
    along: list[float] = []
    first_bad: dict[str, tuple[int, float, float]] = {}
    head: dict[str, float] = {}
    with (d / "steps.csv").open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            step = int(float(r["step"]))
            env = r["env_id"]
            if step > 25 and env not in first_bad and fnum(r["upright"]) == 0:
                first_bad[env] = (step, fnum(r["proj_grav_z"]), fnum(r["height_rel"]))
            if step <= SKIP:
                continue
            ex, ey = fnum(r["error_xy"]), fnum(r["error_yaw"])
            track += math.exp(-math.sqrt(ex * ex + ey * ey) / SCALE)
            track_noyaw += math.exp(-ex / SCALE)
            exy += ex
            eyaw += ey
            n += 1
            cvx, cvy = fnum(r["cmd_vx"]), fnum(r["cmd_vy"])
            cn = math.hypot(cvx, cvy)
            if cn > 1e-6:
                along.append((fnum(r["actual_vx"]) * cvx + fnum(r["actual_vy"]) * cvy) / cn)
            head[env] = head.get(env, 0.0) + (fnum(r["actual_wz"]) - fnum(r["cmd_wz"])) * 0.02
    tilt = sum(1 for _, pg, _ in first_bad.values() if pg > -0.5)
    low_only = sum(1 for _, pg, h in first_bad.values() if pg <= -0.5 and h < 0.18)
    surv = float(s["survival_proxy"])
    t = track / n
    return {"survival": surv, "tracking": t, "case_score": surv * t, "tracking_if_no_yaw": track_noyaw / n,
            "exy_mean": exy / n, "eyaw_mean": eyaw / n,
            "along_speed": st.fmean(along) if along else math.nan,
            "fallen_envs": int(s.get("fallen_env_count", 0)), "fall_tilt": tilt, "fall_low_only": low_only,
            "heading_deg": [abs(v) * 180 / math.pi for v in head.values()]}


def seed_dirs(arm: Path) -> list[str]:
    return sorted(p.name[len("seed_"):] for p in (arm / "cases").glob("seed_*") if p.is_dir())


def read_arm(key: str, arm: Path) -> list[dict]:
    rows = []
    for seed in seed_dirs(arm):
        base = arm / "cases" / f"seed_{seed}"
        for scen, cases in list(CASES.items()) + [("G7", (f"dr_seed_{seed}",))]:
            for case in cases:
                d = base / case
                if not (d / "summary.json").is_file():
                    raise SystemExit(f"[FAIL] missing {d}")
                r = case_row(d)
                full = None
                if case in climb.STAIR_HEIGHTS:
                    got = climb.count(d / "steps.csv", climb.STAIR_HEIGHTS[case])
                    full = None if got is None else int(got["full"])
                r.update({"policy": key, "arm": str(arm), "seed": seed, "scenario": scen,
                          "case": "dr" if scen == "G7" else case, "stairs_full": full})
                rows.append(r)
    return rows


def set_score(rows: list[dict]) -> float:
    total = 0.0
    for scen, w in W.items():
        vals = [r["case_score"] for r in rows if r["scenario"] == scen]
        total += 70 * w * st.fmean(vals)
    return total


def sd(vals: list[float]) -> float | None:
    return st.stdev(vals) if len(vals) > 1 else None


def summarize(key: str, rows: list[dict]) -> dict:
    seeds = sorted({r["seed"] for r in rows}, key=int)
    triples = [seeds[i:i + 3] for i in range(0, len(seeds), 3)]
    by_set = {"/".join(t): set_score([r for r in rows if r["seed"] in t]) for t in triples}
    cases = {}
    for scen_case in sorted({(r["scenario"], r["case"]) for r in rows}):
        sel = [r for r in rows if (r["scenario"], r["case"]) == scen_case]
        cases["/".join(scen_case)] = {
            "n_seeds": len(sel),
            "case_score_mean": st.fmean(r["case_score"] for r in sel), "case_score_sd": sd([r["case_score"] for r in sel]),
            "survival_mean": st.fmean(r["survival"] for r in sel), "survival_sd": sd([r["survival"] for r in sel]),
            "exy_mean": st.fmean(r["exy_mean"] for r in sel), "exy_sd": sd([r["exy_mean"] for r in sel]),
            "fallen_envs_sum": sum(r["fallen_envs"] for r in sel), "fall_tilt_sum": sum(r["fall_tilt"] for r in sel),
        }
    g6 = [r for r in rows if r["scenario"] == "G6"]
    s15 = [r for r in rows if r["case"] in ("stairs_15_up", "stairs_15_down")]
    heading = {}
    for c in HEADING:
        hs = sorted(h for r in rows if r["case"] == c for h in r["heading_deg"])
        heading[c] = st.median(hs) if hs else None
    per_seed_g6 = [st.fmean(r["exy_mean"] for r in g6 if r["seed"] == s) for s in seeds]
    return {
        "policy": key, "seeds": seeds, "n_rows": len(rows),
        "formula_score_by_seed_set": by_set,
        "formula_score_mean": st.fmean(by_set.values()), "formula_score_sd_over_sets": sd(list(by_set.values())),
        "g6_exy_mean": st.fmean(r["exy_mean"] for r in g6), "g6_exy_sd_over_seeds": sd(per_seed_g6),
        "tilt_falls_G3_G6_per_3_seeds": 3 * sum(r["fall_tilt"] for r in rows if r["scenario"] in ("G3", "G6")) / len(seeds),
        "fallen_envs_total_per_3_seeds": 3 * sum(r["fallen_envs"] for r in rows) / len(seeds),
        "stairs15_survival_mean": st.fmean(r["survival"] for r in s15),
        "stairs_full_per_3_seeds": {c: 3 * sum(r["stairs_full"] or 0 for r in rows if r["case"] == c) / len(seeds)
                                    for c in climb.STAIR_HEIGHTS},
        "G3_survival_sum_per_3_seeds": 3 * sum(r["survival"] for r in rows if r["scenario"] == "G3") / len(seeds),
        "terrain_along_speed_mean": st.fmean(r["along_speed"] for r in rows
                                             if r["scenario"] in ("G3", "G4", "G5") and not math.isnan(r["along_speed"])),
        "heading_median_deg": heading,
        "cases": cases,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", required=True, help="POLICY=EVALUATION_DIR (repeatable)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows: list[dict] = []
    for spec in a.arm:
        key, _, path = spec.partition("=")
        rows += read_arm(key, Path(path))
    a.out.mkdir(parents=True, exist_ok=True)
    cols = ["policy", "seed", "scenario", "case", "survival", "tracking", "case_score", "tracking_if_no_yaw",
            "exy_mean", "eyaw_mean", "along_speed", "fallen_envs", "fall_tilt", "fall_low_only", "stairs_full", "arm"]
    with (a.out / "ROWS.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    summary = {k: summarize(k, [r for r in rows if r["policy"] == k]) for k in dict.fromkeys(r["policy"] for r in rows)}
    (a.out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in summary.items():
        print(k, "seeds", len(v["seeds"]), "score", round(v["formula_score_mean"], 3), "sd", v["formula_score_sd_over_sets"],
              "g6_exy", round(v["g6_exy_mean"], 4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
