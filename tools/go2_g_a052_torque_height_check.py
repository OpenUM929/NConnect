"""G-A052 보충 검산 — 실패 전 보상 비용의 시점과 자세 높이(읽기 전용, 사후 기술).

입력: A052 회수본 diag.csv.gz·steps.csv, 판독 정본 EVENTS_DIAG.csv(사건 시각 T).
출력(reports/evidence/go2_g_a052_diag_20260928/):
  COST_PHASES.csv       실패 로봇별 초기[1,3)·중간[T-3,T-1)·직전[T-1,T) 창의 보상 비용과 같은 시각 생존군 중앙값.
                        초기 창은 T-1 >= 3 s 일 때만 실패 이전 구간이다(valid=0 이면 비교에 쓰지 않는다).
  CASE_COST_SUMMARY.csv case·보상 항별 직전 창 실패 중앙값 / 같은 시각 생존 중앙값들의 중앙값.
  TORQUE_BY_HEIGHT.csv  험지 옆걸음 생존 로봇의 상대 높이 구간별 토크 비용 중앙값.
  TORQUE_HEIGHT_CHECK.txt 사람이 읽는 요약.
값은 가중 보상/초(RewardManager _step_reward), 생존군 = 첫 episode 가 시간 종료까지 간 로봇.
지형·보행 위상을 맞추지 않았고 생존군은 창마다 재사용되므로 독립 표본이 아니다.
"""
from __future__ import annotations

import csv
import gzip
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep/go2_g_a052_a048_diag_replay/diag/cases"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a052_diag_20260928"
CASES = (("rough_lateral", "202"), ("stairs_10_down", "101"), ("stairs_15_down", "101"))
TERMS = ("rew_dof_torques_l2", "rew_dof_acc_l2", "rew_action_rate_l2", "rew_ang_vel_xy_l2")
DT = 0.02


def load(case: str, seed: str):
    base = KEEP / f"seed_{seed}" / case
    diag: dict[int, dict[int, dict]] = {}
    with gzip.open(base / "diag.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            diag.setdefault(int(r["env_id"]), {})[int(r["step"])] = r
    steps: dict[int, dict[int, dict]] = {}
    with (base / "steps.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            steps.setdefault(int(r["env_id"]), {})[int(r["step"])] = r
    first_end = {e: min([s for s, r in v.items() if r["terminated"] == "1" or r["truncated"] == "1"] or [10**9])
                 for e, v in steps.items()}
    return diag, steps, first_end


def mean(diag, first_end, env, col, a, b):
    vals = [float(diag[env][s][col]) for s in range(round(a / DT), round(b / DT))
            if s in diag[env] and diag[env][s][col] != "" and s < first_end[env]]
    return st.mean(vals) if vals else None


def f5(x):
    return "" if x is None else f"{x:.5f}"


def main() -> int:
    events: dict[tuple[str, str], dict[int, float]] = {}
    with (OUT / "EVENTS_DIAG.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            events.setdefault((r["case"], r["eval_seed"]), {})[int(r["env_id"])] = float(r["T"])
    phases, summary, text = [], [], []
    for case, seed in CASES:
        diag, steps, first_end = load(case, seed)
        fails = events[(case, seed)]
        surv = [e for e in diag if e not in fails and first_end[e] >= 999]
        last_rows: dict[str, list[tuple[float, float]]] = {t: [] for t in TERMS}
        for env, T in sorted(fails.items()):
            windows = (("early", 1.0, 3.0, T - 1 >= 3.0),
                       ("mid", max(0.5, T - 3), T - 1, T - 1 > 0.5),
                       ("last", max(0.5, T - 1), T, T > 0.5))
            for term in TERMS:
                for phase, a, b, valid in windows:
                    f = mean(diag, first_end, env, term, a, b) if valid else None
                    cs = [x for x in (mean(diag, first_end, s, term, a, b) for s in surv) if x is not None] if valid else []
                    c = st.median(cs) if cs else None
                    ok = int(valid and f is not None and c is not None)
                    phases.append({"key": f"{case}|{env}|{term}|{phase}", "case": case, "eval_seed": seed,
                                   "env_id": str(env), "T": f"{T:.2f}", "term": term, "phase": phase,
                                   "start": f"{a:.2f}", "end": f"{b:.2f}", "valid": str(ok),
                                   "fail_mean": f5(f) if ok else "", "survivor_median": f5(c) if ok else "",
                                   "survivors_n": str(len(cs)) if ok else "",
                                   "fail_more_costly": ("1" if f < c else "0") if ok else ""})
                    if phase == "last" and ok:
                        last_rows[term].append((f, c))
        for term in TERMS:
            rows = last_rows[term]
            if not rows:
                continue
            summary.append({"key": f"{case}|{term}", "case": case, "eval_seed": seed, "term": term,
                            "events": str(len(rows)), "survivors": str(len(surv)),
                            "fail_median": f5(st.median(r[0] for r in rows)),
                            "survivor_median_of_medians": f5(st.median(r[1] for r in rows)),
                            "fail_more_costly": str(sum(r[0] < r[1] for r in rows))})
        if case == "rough_lateral":
            bins: dict[str, list[float]] = {}
            for e in surv:
                for s, r in diag[e].items():
                    h = steps[e][s]["height_rel"] if s in steps[e] else ""
                    if 50 <= s < 999 and r["rew_dof_torques_l2"] != "" and h != "":
                        bins.setdefault(f"{round(float(h) * 50) / 50:.2f}", []).append(float(r["rew_dof_torques_l2"]))
            height_rows = [{"key": f"rough_lateral|{k}", "height_rel_bin_m": k, "steps": str(len(v)),
                            "torque_cost_median": f5(st.median(v))} for k, v in sorted(bins.items()) if len(v) > 200]
    for name, rows in (("COST_PHASES.csv", phases), ("CASE_COST_SUMMARY.csv", summary),
                       ("TORQUE_BY_HEIGHT.csv", height_rows)):
        with (OUT / name).open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    text.append("험지 옆걸음 seed 202 — 실패 로봇별 창 [초기 1~3 s | 중간 T-3~T-1 | 직전 T-1~T], 실패 / 생존 중앙값 (valid=0 이면 -)")
    for term in TERMS:
        text.append(term)
        for env in sorted(events[("rough_lateral", "202")]):
            cells = []
            for phase in ("early", "mid", "last"):
                r = next(p for p in phases if p["key"] == f"rough_lateral|{env}|{term}|{phase}")
                cells.append(f"{r['fail_mean']}/{r['survivor_median']}" if r["valid"] == "1" else "-")
            text.append(f"  env{env:<3} T={events[('rough_lateral', '202')][env]:<6} " + " | ".join(cells))
    text.append("험지 옆걸음 생존 로봇: 상대 높이 구간별 토크 비용 중앙값")
    text += [f"  {r['height_rel_bin_m']} m  n={r['steps']}  {r['torque_cost_median']}" for r in height_rows]
    text.append("case별 직전 창: 실패 중앙값 / 생존 중앙값들의 중앙값, 실패가 더 큰 사건 수")
    text += [f"  {r['case']:<15} {r['term']:<20} {r['fail_median']} / {r['survivor_median_of_medians']}  "
             f"{r['fail_more_costly']}/{r['events']}" for r in summary]
    (OUT / "TORQUE_HEIGHT_CHECK.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"COST_PHASES {len(phases)} rows, CASE_COST_SUMMARY {len(summary)} rows, TORQUE_BY_HEIGHT {len(height_rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
