"""Replay check for the G-A034 uphill-stall witness.  Standard library only.

usage: go2_slope_stuck_check.py <telemetry-root> --stored "4 18 20" [--out FILE]

<telemetry-root>/env_<E>/steps.csv is one full replay of slope_plus_20 whose
camera followed robot E.  For every replay this prints which robots fell by the
evaluator's own ``upright`` column (0.5 s grace, then 0.5 s continuously not
upright), whether that set equals the stored set, and a one-second timeline of
the followed robot so a video frame can be matched to its numbers.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

STEP_DT = 0.02
GRACE_STEPS = 25
HOLD_STEPS = 25


def read_rows(path: Path) -> dict[int, list[dict[str, str]]]:
    by_env: dict[int, list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_env[int(row["env_id"])].append(row)
    return by_env


def falls(by_env: dict[int, list[dict[str, str]]]) -> dict[int, float]:
    """Robot -> time the continuous not-upright run began, for runs >= HOLD_STEPS."""
    fallen: dict[int, float] = {}
    for env, rows in by_env.items():
        run = 0
        for row in rows:
            step = int(row["step"])
            if step <= GRACE_STEPS:
                continue
            if row["upright"] == "0":
                run += 1
                if run >= HOLD_STEPS:
                    fallen[env] = round((step - HOLD_STEPS + 1) * STEP_DT, 2)
                    break
            elif row["upright"] == "1":
                run = 0
    return fallen


def timeline(rows: list[dict[str, str]]) -> list[str]:
    """One line per second, up to the first reset row (its pose is the respawn)."""
    lines = ["    t(s)  cmd_vx  act_vx  speed  h_rel   grav_z  climb(m)  upright"]
    start_ground = float(rows[0]["terrain_z"])
    for row in rows:
        if row["terminated"] == "1" or row["truncated"] == "1":
            lines.append(f"    reset at t={float(row['time_s']):.1f}s (rows after this are the respawn)")
            break
        if int(row["step"]) % 50:
            continue
        lines.append(
            "    {t:5.1f}  {c:6.2f}  {a:6.2f}  {s:5.2f}  {h:5.3f}  {g:6.2f}  {cl:8.2f}  {u}".format(
                t=float(row["time_s"]), c=float(row["cmd_vx"]), a=float(row["actual_vx"]),
                s=float(row["speed_xy"]), h=float(row["height_rel"]), g=float(row["proj_grav_z"]),
                cl=float(row["terrain_z"]) - start_ground, u=row["upright"] or "-",
            )
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--stored", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    stored = sorted(int(x) for x in args.stored.split())
    lines: list[str] = [f"STORED_FALLS={' '.join(map(str, stored))}"]
    verdicts: list[bool] = []
    for folder in sorted(args.root.glob("env_*"), key=lambda p: int(p.name[4:])):
        target = int(folder.name[4:])
        steps = folder / "steps.csv"
        if not steps.is_file():
            lines.append(f"REPLAY robot={target} MISSING steps.csv")
            verdicts.append(False)
            continue
        by_env = read_rows(steps)
        fell = falls(by_env)
        match = sorted(fell) == stored
        verdicts.append(match)
        summary_count = None
        summary = folder / "summary.json"
        if summary.is_file():
            summary_count = json.loads(summary.read_text(encoding="utf-8")).get("fallen_env_count")
        state = f"fell at t={fell[target]:.1f}s" if target in fell else "did not fall"
        lines.append(
            f"REPLAY robot={target} {'MATCH' if match else 'DIFFERENT'} "
            f"falls={' '.join(map(str, sorted(fell))) or '-'} summary_fallen={summary_count} "
            f"followed robot {state}"
        )
        lines.extend(timeline(by_env[target]))
    overall = "REPRODUCED" if verdicts and all(verdicts) else "NOT_REPRODUCED"
    lines.append(f"OVERALL={overall}")
    text = "\n".join(lines) + "\n"
    print(text, end="")
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
