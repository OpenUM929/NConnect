#!/usr/bin/env python3
"""G-A043 복합 우회전 손실 판독 — 같은 case·같은 평가 seed 의 로봇별 낙상 시점과 직전 상태 (로컬, 표준 라이브러리만).

왜 있는가 (2026-09-26 검토 지시).  G-A043(`lin_vel_z_l2 -2.0→-1.5`)은 계단·험지 옆걸음을 올렸지만 G2
`combined_yaw_right` 생존이 세 평가 seed 모두 떨어져 INTERNAL_GATE_FAIL 이었다.  다음 한 번의 학습을 고르기 전에
그 손실이 어떤 양상인지 원자료로 가른다.  G-A044·G-A047 은 반례·대조로만 싣는다.

무엇을 읽는가.  각 case 의 `steps.csv`(명령·실제 속도, 추종 오차, 중력 투영 z, 지면 대비 높이, 종료 플래그).
낙상 판정은 평가기와 같은 규칙을 다시 적용한다 — 0.5 s 유예 뒤, (proj_grav_z > -0.5) 또는 (height_rel < 0.18)
이 0.5 s 연속이면 자세 낙상(`go2_eval_telemetry.py`, 재생 규칙은 `tools/go2_a038_reread.py`와 같다).
직전 상태 = 낙상 판정 시각 기준 −1.0 ~ −0.5 s 창의 평균(`tools/go2_reward_mechanism.py` PRE_TERM 과 같은 창).
없는 채널: 관절·발 접촉·발 미끄러짐·행동 출력·롤/피치 분리·몸통 좌표 z 속도. 이것들은 추측으로 채우지 않는다.
자세 낙상은 기울기·높이 조건의 판정이지 바닥 접촉 확인이 아니다 — 종료 칸(`terminated`, `term_base_contact`)은 따로 싣는다.

산출 `reports/evidence/go2_a043_yaw_right_20260926/`:
  YAW_ENVS.csv     로봇 하나당 한 줄 (arm·case·seed·env·낙상 여부·채널·시각·직전/전체 평균)
  YAW_SUMMARY.csv  arm·case·seed 별 요약

    python -B tools/go2_a043_yaw_right_split.py
"""
from __future__ import annotations

import csv
import io
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_a043_yaw_right_20260926"
ARMS = (("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150"),
        ("G-A043", "go2_g_a043_a033_lin_vel_z_m15"),
        ("G-A044", "go2_g_a044_a033_lin_vel_z_m175"),
        ("G-A047", "go2_g_a047_a033_flat_orientation_m05"))
CASES = ("combined_yaw_right", "combined_yaw_left")
SEEDS = ("101", "202", "303")
DT, GRACE, HOLD = 0.02, 0.5, 0.5
TILT_COS, HEIGHT_MIN = 0.5, 0.18
PRE = (1.0, 0.5)
FIELDS = ("error_xy", "error_yaw", "actual_wz", "speed_xy", "actual_vx", "actual_vy", "proj_grav_z", "height_rel",
          "world_vz", "world_vz2")
RAW = ("error_xy", "error_yaw", "actual_wz", "speed_xy", "actual_vx", "actual_vy", "proj_grav_z", "height_rel", "root_z")


def env_rows(path: Path) -> dict[int, list[dict[str, float]]]:
    by: dict[int, list[dict[str, float]]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for r in csv.DictReader(handle):
            by.setdefault(int(r["env_id"]), []).append(
                {k: float(r[k]) for k in ("time_s", "terminated", "term_base_contact", *RAW)})
    # 세계 좌표 수직 속도 — root_z(높이)의 차분.  **`lin_vel_z_l2` 가 벌하는 양이 아니다.**  그 항의 원문 식은
    # `root_lin_vel_b[:, 2]`, 곧 몸통 좌표계의 z 속도다(기반 데이터 §0-1).  평지여도 몸통이 기울면 둘은 다르고,
    # 넘어지는 구간에서 특히 다르다.  기록에 몸통 좌표 속도 z 칸이 없어 이 값으로 그 항을 대신하지 않는다
    # (2026-09-26 검토 정정: 처음 판은 이 차분을 보상 항의 양으로 적었다).
    for rows in by.values():
        prev = None
        for r in rows:
            r["world_vz"] = 0.0 if prev is None else (r["root_z"] - prev) / DT
            r["world_vz2"] = r["world_vz"] ** 2
            prev = r["root_z"]
    return by


def fall(rows: list[dict[str, float]]) -> tuple[float | None, str]:
    """평가기 규칙으로 첫 자세 낙상 시각과 그 순간 어느 채널이 참이었는지."""
    run = 0.0
    for r in rows:
        if r["time_s"] < GRACE:
            continue
        tilt = r["proj_grav_z"] > -TILT_COS
        low = r["height_rel"] < HEIGHT_MIN
        run = run + DT if (tilt or low) else 0.0
        if run >= HOLD - 1e-9:
            return r["time_s"], "both" if tilt and low else "tilt" if tilt else "height"
    return None, ""


def mean(rows: list[dict[str, float]], key: str) -> float | None:
    values = [r[key] for r in rows]
    return statistics.fmean(values) if values else None


def tables() -> dict[str, list[list[str]]]:
    env_out = [["arm", "case", "seed", "env", "fell", "channel", "fall_time_s", "terminated", "base_contact_termination",
                *[f"pre_{f}" for f in FIELDS], *[f"all_{f}" for f in FIELDS]]]
    summary = [["arm", "case", "seed", "robots", "falls", "tilt", "height", "both", "fall_time_median_s",
                "all_error_yaw", "all_actual_wz", "all_speed_xy", "pre_error_yaw_fallers", "pre_actual_wz_fallers",
                "pre_proj_grav_z_fallers", "pre_height_rel_fallers", "all_world_vz2", "pre_world_vz2_fallers"]]
    fmt = lambda v: "" if v is None else f"{v:.4f}"  # noqa: E731
    for arm, run in ARMS:
        for case in CASES:
            for seed in SEEDS:
                path = KEEP / run / "evaluation/candidate/cases" / f"seed_{seed}" / case / "steps.csv"
                if not path.is_file():
                    continue
                falls, fallers_pre = [], []
                by = env_rows(path)
                all_rows = []
                for env, rows in sorted(by.items()):
                    t, channel = fall(rows)
                    live = [r for r in rows if r["time_s"] >= GRACE and (t is None or r["time_s"] <= t)]
                    all_rows.extend(live)
                    pre = [r for r in rows if t is not None and t - PRE[0] <= r["time_s"] < t - PRE[1]]
                    if t is not None:
                        falls.append((t, channel))
                        fallers_pre.extend(pre)
                    env_out.append([arm, case, seed, str(env), str(int(t is not None)), channel, fmt(t),
                                    str(int(any(r["terminated"] for r in rows))),
                                    str(int(any(r["term_base_contact"] for r in rows))),
                                    *[fmt(mean(pre, f)) for f in FIELDS], *[fmt(mean(live, f)) for f in FIELDS]])
                channels = [c for _t, c in falls]
                summary.append([arm, case, seed, str(len(by)), str(len(falls)), str(channels.count("tilt")),
                                str(channels.count("height")), str(channels.count("both")),
                                fmt(statistics.median(t for t, _c in falls) if falls else None),
                                fmt(mean(all_rows, "error_yaw")), fmt(mean(all_rows, "actual_wz")),
                                fmt(mean(all_rows, "speed_xy")),
                                fmt(mean(fallers_pre, "error_yaw")), fmt(mean(fallers_pre, "actual_wz")),
                                fmt(mean(fallers_pre, "proj_grav_z")), fmt(mean(fallers_pre, "height_rel")),
                                fmt(mean(all_rows, "world_vz2")), fmt(mean(fallers_pre, "world_vz2"))])
    return {"YAW_ENVS.csv": env_out, "YAW_SUMMARY.csv": summary, "YAW_PROFILE.csv": profile()}


PROFILE_BINS = [(-3.0 + 0.25 * i, -2.75 + 0.25 * i) for i in range(12)]   # 낙상 판정 기준 −3.0 s ~ 0 s


def profile() -> list[list[str]]:
    """G-A043 우회전 낙상 로봇의 판정 전 3 초, 0.25 s 칸 평균.  같은 시각 같은 seed 의 생존 로봇을 옆에 둔다.

    낙상 판정은 비정상 자세가 0.5 s 이어진 끝이다 — 무너짐의 시작은 판정 −0.5 s 부근이다.  그 앞의 칸이
    '무너지기 전' 상태다."""
    out = [["seed", "bin_start_s", "bin_end_s", "group", "robots", *FIELDS]]
    run = dict(ARMS)["G-A043"]
    for seed in SEEDS:
        by = env_rows(KEEP / run / "evaluation/candidate/cases" / f"seed_{seed}" / "combined_yaw_right" / "steps.csv")
        times = {env: fall(rows)[0] for env, rows in by.items()}
        fallers = {env: t for env, t in times.items() if t is not None}
        survivors = [env for env, t in times.items() if t is None]
        for lo, hi in PROFILE_BINS:
            groups = {"faller": [r for env, t in fallers.items() for r in by[env] if t + lo <= r["time_s"] < t + hi],
                      # 생존 로봇은 낙상 로봇의 판정 시각과 같은 절대 시각 창에서 잰다.
                      "survivor_same_clock": [r for env in survivors for t in fallers.values()
                                              for r in by[env] if t + lo <= r["time_s"] < t + hi]}
            for group, rows in groups.items():
                out.append([seed, f"{lo:.2f}", f"{hi:.2f}", group,
                            str(len(fallers) if group == "faller" else len(survivors)),
                            *["" if not rows else f"{statistics.fmean(r[f] for r in rows):.4f}" for f in FIELDS]])
    return out


def render(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in tables().items():
        (OUT / name).write_text(render(rows), encoding="utf-8", newline="\n")
        print(f"{OUT / name}  rows={len(rows) - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
