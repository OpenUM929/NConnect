#!/usr/bin/env python3
"""G-A057 변수별 추세에 서버 A048 과 이 PC A048 중 어느 기준점이 더 일관되게 놓이는가 (2026-10-01, 사용자 지시).

배경: G-A057 계획은 각 변수의 기준값(track 1.5, ang_vel −0.05, feet_air_time 0.2, action_rate −0.01,
flat_orientation 0)을 서버 A048 결과로 공유하고, 새 값 행은 실행 PC(RTX 3050)에서 학습한다.
서버 A048 과 이 PC A048(G-A058 행 1, 같은 보상·seed 42)은 평가 행동이 크게 다르다(험지 옆걸음 낙상 16 대 68).

사전등록(데이터 도착 전 고정, 결과를 본 뒤 바꾸지 않는다):
  대상     기준값이 이웃 두 값 사이에 있는 변수 — track(1.4, 1.6), ang_vel_xy(−0.04, −0.08),
           feet_air_time(0.1, 0.35), action_rate(−0.008, −0.012).  flat_orientation 은 기준이 끝점이라 제외.
  잔차     이웃 두 점을 값 축에서 직선 보간한 값과 기준점의 차 |r|.  기준점만 서버/이 PC 로 바꿔 두 번 잰다.
  지표     METRICS (총점·G3·낙상·계단·몸높이).  지표별·변수별 비교 1개.
  제외     이웃 행이 미회수면 그 변수는 비교하지 않는다.  정지 정책(EXCLUDED_STATIONARY)은 채택 후보에서만
           빠지는 표지이고 추세 점으로는 그대로 쓴다(2026-10-01 사용자 정정: 누적 학습 자료다).
  판정     결정된 비교(동률 제외) ≥ 12 이고 한쪽이 ≥ 2/3 이기면 LOCAL_BASE_MORE_COHERENT /
           SERVER_BASE_MORE_COHERENT, 아니면 INCONCLUSIVE.  12 미만이면 INSUFFICIENT.
  한계     이웃 점이 이 PC 학습이라 이 PC 기준점에 구조적 이점이 있다.  이 판정은 '서버 A048 이 이 PC 자료와
           한 줄에 놓이는가'를 답하며, 어느 PC 가 본질적으로 더 일관적인지는 답하지 않는다.
  보조     같은 PC 안 seed 흔들림: G-A058 a043_seed43 대 a043_seed44 의 지표 차 |d|.  잔차가 이 흔들림보다
           큰지 함께 적는다(문턱으로 쓰지 않는다).

    python -B tools/go2_base_coherence.py
출력: workspace/training/quadruped/reports/evidence/go2_base_coherence/BASE_COHERENCE.{csv,md}
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_base_coherence"
SERVER_BASE = "go2_g_a048_a033_lin_vel_z_m125"
LOCAL_BASE = "go2_g_a058_a048_seed42"
SEED_PAIR = ("go2_g_a058_a043_seed43", "go2_g_a058_a043_seed44")
VARIABLES = {  # 변수: (기준값, (아래 이웃 값, 행 키), (위 이웃 값, 행 키))
    "track_lin_vel_xy_exp": (1.5, (1.4, "track_lin_vel_xy_exp_p1p4"), (1.6, "track_lin_vel_xy_exp_p1p6")),
    "ang_vel_xy_l2": (-0.05, (-0.04, "ang_vel_xy_l2_m0p04"), (-0.08, "ang_vel_xy_l2_m0p08")),
    "feet_air_time": (0.2, (0.1, "feet_air_time_p0p1"), (0.35, "feet_air_time_p0p35")),
    "action_rate_l2": (-0.01, (-0.008, "action_rate_l2_m0p008"), (-0.012, "action_rate_l2_m0p012")),
}
METRICS = ("total_70", "G3_score", "rough_lateral_falls", "rough_forward_falls", "combined_yaw_right_falls",
           "push_falls_sum", "stairs_10_down_ge2", "stairs_15_down_ge2", "rough_lateral_height_rel")
MIN_DECIDED = 12
WIN_SHARE = 2 / 3


def interp(x: float, x0: float, y0: float, x1: float, y1: float) -> float:
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def residual(x: float, lo: tuple[float, float], hi: tuple[float, float], base: float) -> float:
    return abs(base - interp(x, lo[0], lo[1], hi[0], hi[1]))


def verdict(local_wins: int, server_wins: int) -> str:
    decided = local_wins + server_wins
    if decided < MIN_DECIDED:
        return "INSUFFICIENT"
    if local_wins >= WIN_SHARE * decided:
        return "LOCAL_BASE_MORE_COHERENT"
    if server_wins >= WIN_SHARE * decided:
        return "SERVER_BASE_MORE_COHERENT"
    return "INCONCLUSIVE"


def arm_metrics(name: str) -> dict | None:
    import go2_axis_bottleneck as axis
    import go2_g_a057_sweep_compare as cmp
    arm = KEEP / name
    if not (arm / "evaluation/candidate/cases").is_dir():
        return None
    std = float(axis.registry()["score"]["tracking_proxy_std"])
    rec = {"present": True, "axes": cmp.axis_scores(arm), "gpu": cmp.gpu(arm),
           "variable": "-", "value": "-", "status": "-", "arm": name}
    for c in (*cmp.FALL_CASES, *cmp.STAIRS):
        rec[c] = cmp.case_metrics(arm, c, std)
    row = cmp.flat(rec)
    return {m: row.get(m) for m in METRICS}


def stationary(key: str) -> bool:
    import go2_g_a057_prereg_readout as pre
    harvest = KEEP / f"go2_g_a057_{key}"
    try:
        return pre.read(key, harvest).get("exclusion") == "EXCLUDED_STATIONARY"
    except Exception:  # noqa: BLE001 — 판독 불가 행은 추세 점에서 뺀다
        return True


def trend_rows() -> list[dict]:
    """누적 추세표: G-A057 계획의 모든 (변수, 값)을 한 줄씩, 실제 학습한 PC 와 정지 표지를 붙여 쌓는다.

    기준값 줄은 서버 A048 과 이 PC A048 두 줄로 나눠 넣는다.  미회수 행은 '미회수'로 남긴다(빼지 않는다).
    """
    import go2_g_a057_sweep_plan as planmod
    out = []
    for r in planmod.plan()["runs"]:
        if r["status"] == "BASE_SHARED" or (r["status"] == "REUSE" and r["arm"] == SERVER_BASE):
            arms = [(SERVER_BASE, "서버 A048"), (LOCAL_BASE, "이 PC A048")]
        elif r["status"] == "REUSE":
            arms = [(r["arm"], "재사용")]
        else:
            arms = [(f"go2_g_a057_{r['key']}", "새 학습")]
        for name, role in arms:
            m = arm_metrics(name)
            gpu = ""
            if m is not None:
                import go2_g_a057_sweep_compare as cmp
                gpu = "서버" if cmp.gpu(KEEP / name).startswith(cmp.SERVER_GPU) else "이 PC"
            key = name.removeprefix("go2_g_a057_")
            flag = "정지" if name.startswith("go2_g_a057_") and m is not None and stationary(key) else ""
            out.append({"variable": r["variable"], "value": r["value"], "role": role, "arm": name,
                        "pc": gpu or "미회수", "stationary": flag, **(m or {})})
    return out


def trend_markdown(rows: list[dict]) -> list[str]:
    head = ["변수", "값", "출처", "PC", "정지", *METRICS]
    lines = ["", "## 누적 추세표 (모든 값, 정지 결과 포함)", "",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in
                                         ("variable", "value", "role", "pc", "stationary", *METRICS)) + " |")
    lines += ["", "- PC 열이 다른 점끼리의 차이는 보상 효과와 PC·seed 차이가 섞여 있다."]
    return lines


def num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) else None


def main() -> int:
    server, local = arm_metrics(SERVER_BASE), arm_metrics(LOCAL_BASE)
    rows, lw, sw = [], 0, 0
    for var, (x, lo, hi) in VARIABLES.items():
        ends = {}
        for val, key in (lo, hi):
            ends[val] = arm_metrics(f"go2_g_a057_{key}")
            if ends[val] is None:
                ends = None
                break
        for m in METRICS:
            row = {"variable": var, "metric": m, "state": "NOT_YET"}
            if ends and server and local:
                y0, y1 = num(ends[lo[0]][m]), num(ends[hi[0]][m])
                bs, bl = num(server[m]), num(local[m])
                if None not in (y0, y1, bs, bl):
                    rs = residual(x, (lo[0], y0), (hi[0], y1), bs)
                    rl = residual(x, (lo[0], y0), (hi[0], y1), bl)
                    win = "LOCAL" if rl < rs else "SERVER" if rs < rl else "TIE"
                    lw += win == "LOCAL"
                    sw += win == "SERVER"
                    row.update(state="OK", lo=y0, hi=y1, line=round(interp(x, lo[0], y0, hi[0], y1), 4),
                               server_base=bs, local_base=bl, r_server=round(rs, 4), r_local=round(rl, 4), win=win)
            rows.append(row)
    pair = [arm_metrics(a) for a in SEED_PAIR]
    seed_spread = {m: (abs(num(pair[0][m]) - num(pair[1][m])) if all(p and num(p[m]) is not None for p in pair) else None)
                   for m in METRICS}
    v = verdict(lw, sw)
    OUT.mkdir(parents=True, exist_ok=True)
    keys = ["variable", "metric", "state", "lo", "hi", "line", "server_base", "local_base", "r_server", "r_local", "win"]
    with open(OUT / "BASE_COHERENCE.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    lines = ["# 기준점 일관성 — 서버 A048 대 이 PC A048 (자동, 사전등록 규칙은 도구 머리말)", "",
             f"판정: **{v}** (이 PC 기준점 우세 {lw} / 서버 기준점 우세 {sw}, 결정 {lw + sw}건, 최소 {MIN_DECIDED})", "",
             "| 변수 | 지표 | 상태 | 이웃 아래 | 이웃 위 | 직선 | 서버 A048 | 이 PC A048 | 잔차 서버 | 잔차 이 PC | 우세 | 같은 PC seed 흔들림 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + f" | {seed_spread[r['metric']] if seed_spread[r['metric']] is not None else '미측정'} |")
    lines += ["", "- 이웃 점은 이 PC 학습이라 이 PC 기준점에 구조적 이점이 있다. 이 판정은 서버 A048 이 이 PC 자료와 한 줄에 놓이는지만 답한다.",
              "- 미회수 이웃이 있는 변수는 비교하지 않는다. 정지 정책도 추세 점으로 쓴다(채택 후보 제외 표지일 뿐이다)."]
    lines += trend_markdown(trend_rows())
    (OUT / "BASE_COHERENCE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(v, lw, sw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
