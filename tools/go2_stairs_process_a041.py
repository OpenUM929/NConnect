"""계단 실패 과정 비교 보충 — G-A041 10cm (Codex 결정 G-D-STAIRS-EDGE-COMPARE-20260928 범위 2, 읽기 전용).

G-A041(ang_vel_xy_l2 -0.05 -> -0.04, A033 위)은 표적 회차라 stairs_10_down 만 평가됐다(15cm 없음).
정의·함수는 tools/go2_stairs_process.py 그대로 쓴다(env_timeline·edge_window). 그 도구의 기존 산출물은 건드리지 않는다.
비교용 A033·A043·A048 10cm 값은 계산을 반복하지 않고 기존 ENV_TIMELINE.csv 에서 읽는다.
출력(reports/evidence/go2_stairs_process_a041_20260928/):
  ENV_TIMELINE_A041.csv  로봇 96대(seed 101/202/303 x 32).
  SUMMARY.txt            등반 결과·낙상·순서 분포, 모서리 창 중앙값(결과 묶음별), 기존 세 정책 같은 값.
한계: steps.csv 에는 기울기 방향·roll/pitch 각속도·발 채널이 없다. 회전 방향은 비교하지 않는다. 학습 seed 42 한 경로.

    python -B tools/go2_stairs_process_a041.py
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_stairs_process as sp  # noqa: E402

KEEP_A041 = "go2_g_a041_a033_ang_vel_xy_m004"
CASE, HEIGHT = "stairs_10_down", 0.10
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_stairs_process_a041_20260928"
EXISTING = sp.OUT / "ENV_TIMELINE.csv"
EDGE_KEYS = ("edge_root_rise_m", "edge_max_vz_up", "edge_max_tilt")


def med(vals: list[str | float | None]) -> str:
    v = [float(x) for x in vals if x not in (None, "")]
    return f"{statistics.median(v):.4f} (n={len(v)})" if v else "- (n=0)"


def describe(arm: str, rows: list[dict]) -> list[str]:
    out = [f"{arm} {CASE} n={len(rows)}"]
    oc = Counter(r["outcome"] for r in rows)
    out.append(f"  outcome ge2={oc['ge2']} ge1={oc['ge1']} none={oc['none']}  fell={sum(int(r['fell']) for r in rows)}")
    out.append("  order(not ge2): " + ", ".join(f"{k} {v}" for k, v in
                                               sorted(Counter(r['order_low_vs_stall'] for r in rows
                                                              if r['outcome'] != 'ge2').items())))
    for label in ("ge2", "none"):
        g = [r for r in rows if r["outcome"] == label]
        out.append(f"  edge {label}: " + "  ".join(f"{k} {med([r[k] for r in g])}" for k in EDGE_KEYS))
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in sp.SEEDS:
        path = sp.KEEP / KEEP_A041 / "evaluation/candidate/cases" / f"seed_{seed}" / CASE / "steps.csv"
        for env, rs in sorted(sp.read_envs(path).items(), key=lambda kv: int(kv[0])):
            line = {"arm": "G-A041", "ang_vel_xy_l2": -0.04, "case": CASE, "seed": seed, "env_id": env,
                    **sp.env_timeline(rs, HEIGHT)}
            line.update(sp.edge_window(rs, line["t_step1_s"]))
            rows.append(line)
    with (OUT / "ENV_TIMELINE_A041.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with EXISTING.open(encoding="utf-8") as fh:
        old = [r for r in csv.DictReader(fh) if r["case"] == CASE]
    lines = describe("G-A041", [{k: ("" if v is None else v) for k, v in r.items()} for r in rows])
    for arm in ("G-A033", "G-A043", "G-A048"):
        lines += describe(arm + " (existing)", [r for r in old if r["arm"] == arm])
    (OUT / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
