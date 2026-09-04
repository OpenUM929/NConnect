"""Re-score already-downloaded Go2 evaluations with the posture gate. 0 GPU.

Scope limit, stated up front: archived ``steps.csv`` files carry ``root_z`` but
no orientation and no terrain height, so this can only be applied where the
terrain is flat and world z equals height above ground -- G1, G2 and G6.  On
stairs and slopes absolute root_z is meaningless (a descending-stairs case
measured -0.771 m while walking normally), so those cases are reported as
NOT_RESCORABLE rather than guessed at.

Height-only means this UNDER-detects falls: a robot tipped over at normal
height is missed.  Every number here is therefore a lower bound on the
correction.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace" / "_keep"

FALL_HEIGHT_M = 0.18
FALL_HOLD_S = 0.5
FALL_GRACE_S = 0.5

FLAT_CASES = {
    "forward_slow": "G1", "forward_nominal": "G1", "forward_fast": "G1",
    "backward": "G2", "left": "G2", "right": "G2",
    "diagonal_left": "G2", "diagonal_right": "G2",
    "combined_yaw_left": "G2", "combined_yaw_right": "G2",
    "push_pos_x": "G6", "push_neg_x": "G6", "push_pos_y": "G6", "push_neg_y": "G6",
}


def rescore(case_dir: Path) -> dict | None:
    steps = case_dir / "steps.csv"
    summary_path = case_dir / "summary.json"
    if not steps.exists() or not summary_path.exists():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    step_dt = float(summary.get("step_dt") or 0.02)

    run_s: dict[int, float] = defaultdict(float)
    fallen: set[int] = set()
    envs: set[int] = set()
    with steps.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            env_id = int(row["env_id"])
            envs.add(env_id)
            if float(row["time_s"]) < FALL_GRACE_S:
                continue
            if float(row["root_z"]) >= FALL_HEIGHT_M:
                run_s[env_id] = 0.0
            else:
                run_s[env_id] += step_dt
                if run_s[env_id] >= FALL_HOLD_S:
                    fallen.add(env_id)
    n = len(envs) or 1
    v1 = summary.get("survival_proxy_v1", summary.get("survival_proxy"))
    return {
        "survival_v1": v1,
        "survival_v2_lower_bound": 1.0 - len(fallen) / n,
        "fallen": len(fallen),
        "num_envs": n,
        "recovery_rate_v1": (summary.get("recovery") or {}).get("recovery_rate"),
    }


def main() -> int:
    roots = []
    for pkg in sorted(KEEP.glob("go2_*")):
        for evaluation in pkg.rglob("cases"):
            label = evaluation.relative_to(KEEP).as_posix()
            roots.append((label, evaluation))
    if not roots:
        print("no evaluation case trees found")
        return 1

    print(f"{'policy / seed':<58} {'G':<3} {'case':<20} {'v1':>6} {'v2>=':>6} {'fallen':>7}")
    print("-" * 108)
    agg: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    skipped = 0
    for label, cases_root in roots:
        for seed_dir in sorted(cases_root.iterdir()):
            if not seed_dir.is_dir():
                continue
            for case_dir in sorted(seed_dir.iterdir()):
                if not case_dir.is_dir():
                    continue
                scenario = FLAT_CASES.get(case_dir.name)
                if scenario is None:
                    skipped += 1
                    continue
                res = rescore(case_dir)
                if res is None:
                    continue
                policy = label.split("/cases")[0]
                key = (policy, scenario)
                agg[key].append((res["survival_v1"] or 0.0, res["survival_v2_lower_bound"]))
                if res["survival_v1"] != res["survival_v2_lower_bound"]:
                    print(f"{policy + '/' + seed_dir.name:<58} {scenario:<3} {case_dir.name:<20}"
                          f" {res['survival_v1']:>6.3f} {res['survival_v2_lower_bound']:>6.3f}"
                          f" {res['fallen']:>4}/{res['num_envs']:<3}")

    print()
    print("=== worst-case survival per policy x scenario (internal aggregation rule) ===")
    print(f"{'policy':<58} {'G':<3} {'v1 min':>8} {'v2 min':>8} {'delta':>8}  cases")
    print("-" * 100)
    for (policy, scenario), rows in sorted(agg.items()):
        v1 = min(r[0] for r in rows)
        v2 = min(r[1] for r in rows)
        flag = "  <-- ARTIFACT" if v1 - v2 > 0.001 else ""
        print(f"{policy:<58} {scenario:<3} {v1:>8.3f} {v2:>8.3f} {v1 - v2:>8.3f}  {len(rows)}{flag}")
    print()
    print(f"NOT_RESCORABLE (non-flat terrain, no orientation column): {skipped} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
