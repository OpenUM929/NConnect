"""계단 실패 과정 비교 — A043 · A048 · A050 (2026-09-27, 외부 검토가 정한 다음 작업 하나).

새 서버 실험 없이 저장된 평가 `steps.csv`(위치·속도·몸 높이·중력 투영·지형 높이)만 읽는다.
발 위치는 telemetry 에 없으므로 쓰지 않는다(미측정).  질문 셋:

  Q1 단에 닿기 전부터 몸이 낮은가, 닿은 뒤 낮아지는가
  Q2 전진이 먼저 멈추는가, 몸 높이가 먼저 내려가는가
  Q3 오른 로봇과 못 오른 로봇의 차이가 어느 시점부터 생기는가

정의(모두 이 파일에 고정, 결과를 본 뒤 바꾸지 않는다):
  단 위치       몸통 아래 지형 높이 `terrain_z`.  출발 지형보다 계단 높이의 절반 이상 높아지면 첫 단 위(t_step1).
                몸통 중심 기준이라 앞다리가 단에 먼저 닿는 시점보다 늦다.
  접근 구간     1.0 s(착지 안정) 뒤부터 t_step1 전까지.  첫 단에 못 간 로봇은 첫 사건(낮은 자세·정체·종료) 전까지.
  낮은 자세     height_rel < 0.18 m 가 0.5 s 연속(평가기 자세 게이트의 높이 채널, grace 0.5 s).
  정체          명령 방향 투영속도 < 0.05 m/s 가 1.0 s 연속(tools/go2_stall_diagnostics.py 와 같은 값).
  낙상          (자세 불량 0.5 s 연속) ∪ 종료 — 판정기 정의(go2_eval_telemetry.py:448-449).
  등반 결과     tools/go2_climb_count.gained_steps (검증기와 같은 함수): 0 / 1 / ≥2 단.
  모서리 창      t_step1 −0.5 s ~ +1.5 s (종료 전 행).  몸통 절대 높이 root_z 의 창 안 변화(끝−처음),
                0.1 s 차분 수직속도의 최댓값, 기울기 크기 1+proj_grav_z 의 최댓값(pitch·roll 구분 없음).

    python -B tools/go2_stairs_process.py
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_climb_count as climb  # noqa: E402

KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_stairs_process_20260927"
ARMS = (("G-A043", -1.5, "go2_g_a043_a033_lin_vel_z_m15"),
        ("G-A048", -1.25, "go2_g_a048_a033_lin_vel_z_m125"),
        ("G-A050", -1.375, "go2_g_a050_a033_lin_vel_z_m1375"),
        ("G-A033", -2.0, "go2_g_a033_a017_track_lin_vel_xy_150"))
CASES = (("stairs_10_down", 0.10), ("stairs_15_down", 0.15))
SEEDS = (101, 202, 303)
DT, GRACE_S, SETTLE_S = 0.02, 0.5, 1.0
LOW_M, LOW_HOLD_S = 0.18, 0.5
TILT_COS = 0.5
STALL_SPEED, STALL_HOLD_S = 0.05, 1.0
BIN_S = 1.0


def proj_speed(r: dict[str, str]) -> float:
    cx, cy = float(r["cmd_vx"]), float(r["cmd_vy"])
    n = (cx * cx + cy * cy) ** 0.5
    return (float(r["actual_vx"]) * cx + float(r["actual_vy"]) * cy) / n if n > 0 else 0.0


def read_envs(path: Path) -> dict[str, list[dict[str, str]]]:
    by: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            by[r["env_id"]].append(r)
    return by


def first_hold(rows: list[dict[str, str]], bad, hold_s: float, start_s: float) -> float | None:
    run = 0.0
    for r in rows:
        t = float(r["time_s"])
        if t < start_s:
            continue
        if bad(r):
            run += DT
            if run >= hold_s - 1e-9:
                return round(t - hold_s + DT, 3)       # 연속 구간이 시작된 시각
        else:
            run = 0.0
    return None


def env_timeline(rows: list[dict[str, str]], height: float) -> dict:
    alive, term_t = [], None
    for r in rows:
        if r.get("terminated") == "1" or r.get("truncated") == "1":
            if r.get("terminated") == "1":
                term_t = float(r["time_s"])
            break
        alive.append(r)
    tz0 = statistics.median(float(r["terrain_z"]) for r in alive[:50]) if alive else None
    t_step1 = None
    if alive:
        for r in alive:
            if float(r["terrain_z"]) - tz0 >= 0.5 * height:
                t_step1 = float(r["time_s"])
                break
    h_bad = lambda r: not (r["height_rel"] != "" and float(r["height_rel"]) >= LOW_M)
    posture_bad = lambda r: h_bad(r) or not float(r["proj_grav_z"]) <= -TILT_COS
    t_low = first_hold(alive, h_bad, LOW_HOLD_S, GRACE_S)
    t_posture = first_hold(alive, posture_bad, LOW_HOLD_S, GRACE_S)
    t_stall = first_hold(alive, lambda r: proj_speed(r) < STALL_SPEED, STALL_HOLD_S, GRACE_S)
    fall_t = min([t for t in (t_posture, term_t) if t is not None], default=None)
    # 접근 구간: 첫 단 위 전, 없으면 첫 사건 전.
    end = t_step1 if t_step1 is not None else min(
        [t for t in (t_low, t_stall, term_t) if t is not None], default=float(alive[-1]["time_s"]) if alive else 0.0)
    approach = [float(r["height_rel"]) for r in alive
                if SETTLE_S <= float(r["time_s"]) < end and r["height_rel"] != ""]
    gained = climb.gained_steps(alive, "climb", height) if alive else 0
    if t_low is None and t_stall is None:
        order = "neither"
    elif t_stall is None:
        order = "low_only"
    elif t_low is None:
        order = "stall_only"
    elif t_low < t_stall - 0.2:
        order = "low_first"
    elif t_stall < t_low - 0.2:
        order = "stall_first"
    else:
        order = "together"
    rel = lambda t: None if t is None or t_step1 is None else round(t - t_step1, 3)
    return {"gained_steps": gained,
            "outcome": "ge2" if gained >= 2 else ("ge1" if gained == 1 else "none"),
            "fell": int(fall_t is not None), "fall_time_s": fall_t,
            "t_step1_s": t_step1, "t_low_s": t_low, "t_stall_s": t_stall, "term_time_s": term_t,
            "low_minus_step1_s": rel(t_low), "stall_minus_step1_s": rel(t_stall),
            "order_low_vs_stall": order,
            "approach_rows": len(approach),
            "approach_height_median": round(statistics.median(approach), 4) if approach else None,
            "approach_height_p10": round(sorted(approach)[len(approach) // 10], 4) if approach else None}


def edge_window(rows: list[dict[str, str]], t_step1: float | None) -> dict:
    if t_step1 is None:
        return {"edge_root_rise_m": None, "edge_max_vz_up": None, "edge_max_tilt": None}
    w = []
    for r in rows:
        if r.get("terminated") == "1" or r.get("truncated") == "1":
            break
        if t_step1 - 0.5 <= float(r["time_s"]) <= t_step1 + 1.5:
            w.append(r)
    if len(w) < 6:
        return {"edge_root_rise_m": None, "edge_max_vz_up": None, "edge_max_tilt": None}
    z = [float(r["root_z"]) for r in w]
    vz = [(z[i + 5] - z[i]) / (5 * DT) for i in range(len(z) - 5)]
    return {"edge_root_rise_m": round(z[-1] - z[0], 4), "edge_max_vz_up": round(max(vz), 4),
            "edge_max_tilt": round(max(1 + float(r["proj_grav_z"]) for r in w), 4)}


def timecourse(rows: list[dict[str, str]], height: float) -> dict[int, dict[str, float]]:
    """1 s 칸마다 몸 높이 평균, 지형 상승(단 수), 투영속도 평균 — 종료 전 행만."""
    tz0 = statistics.median(float(r["terrain_z"]) for r in rows[:50])
    out: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
    for r in rows:
        if r.get("terminated") == "1" or r.get("truncated") == "1":
            break
        if r["height_rel"] == "":
            continue
        k = int(float(r["time_s"]) // BIN_S)
        out[k].append((float(r["height_rel"]), (float(r["terrain_z"]) - tz0) / height, proj_speed(r)))
    return {k: {"height": statistics.fmean(v[0] for v in vs), "steps_up": statistics.fmean(v[1] for v in vs),
                "speed": statistics.fmean(v[2] for v in vs)} for k, vs in out.items()}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    env_rows, tc = [], defaultdict(list)
    for arm, value, keep in ARMS:
        for case, height in CASES:
            for seed in SEEDS:
                path = KEEP / keep / "evaluation/candidate/cases" / f"seed_{seed}" / case / "steps.csv"
                if not path.is_file():
                    continue
                for env, rows in sorted(read_envs(path).items(), key=lambda kv: int(kv[0])):
                    line = {"arm": arm, "lin_vel_z_l2": value, "case": case, "seed": seed, "env_id": env,
                            **env_timeline(rows, height)}
                    line.update(edge_window(rows, line["t_step1_s"]))
                    env_rows.append(line)
                    for k, v in timecourse(rows, height).items():
                        tc[(arm, case, line["outcome"], k)].append(v)
    with (OUT / "ENV_TIMELINE.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(env_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(env_rows)
    with (OUT / "GROUP_TIMECOURSE.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["arm", "case", "outcome", "t_bin_s", "robots_alive", "height_mean", "steps_up_mean", "speed_mean"])
        for (arm, case, outcome, k), vs in sorted(tc.items()):
            w.writerow([arm, case, outcome, k, len(vs), round(statistics.fmean(v["height"] for v in vs), 4),
                        round(statistics.fmean(v["steps_up"] for v in vs), 3),
                        round(statistics.fmean(v["speed"] for v in vs), 4)])
    print(OUT, len(env_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
