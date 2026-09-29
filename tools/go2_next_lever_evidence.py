"""다음 보상 레버를 고르기 위한 원자료 표 (2026-09-27, G-A050 이후).

lin_vel_z_l2 다섯 점(A033·A044·A043·A048·A049·A050)과 다른 레버의 걷는 기준선 측정(A038·A041·A042·A047)에서
표적 행동의 원값만 모은다.  판정하지 않고 값을 고르지 않는다 — 고르는 것은 계획서다.

  CASE_ROWS.csv    arm·case·seed 별 요약값(summary.json): 생존·자세 낙상·몸 높이 p10·속도·전진거리
  FALL_CHANNELS.csv 험지 옆걸음·10cm·15cm 오르기 낙상을 로봇마다 한 경로로 나눈다 — 높이만/기울기만/둘 다/
                    합쳐서만/종료로만.  fallen_total 은 판정기 낙상(자세 0.5 s ∪ 종료)을 재생한 수이고
                    summary.json 의 pessimistic 수와 대조한다(누락 행 처리 차이로 어긋날 수 있다).
  AXIS.csv         축 점수(case·seed 최솟값)와 묶는 인수 (tools/go2_axis_bottleneck.py 재사용)

    python -B tools/go2_next_lever_evidence.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_axis_bottleneck as bottleneck  # noqa: E402

KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_next_lever_20260927"
ARMS = (
    ("G-A033", "baseline", "go2_g_a033_a017_track_lin_vel_xy_150"),
    ("G-A044", "lin_vel_z_l2 -1.75", "go2_g_a044_a033_lin_vel_z_m175"),
    ("G-A043", "lin_vel_z_l2 -1.5", "go2_g_a043_a033_lin_vel_z_m15"),
    ("G-A050", "lin_vel_z_l2 -1.375", "go2_g_a050_a033_lin_vel_z_m1375"),
    ("G-A048", "lin_vel_z_l2 -1.25", "go2_g_a048_a033_lin_vel_z_m125"),
    ("G-A049", "lin_vel_z_l2 -1.0", "go2_g_a049_a033_lin_vel_z_m1"),
    ("G-A038", "ang_vel_xy_l2 -0.08", "go2_g_a038_a033_ang_vel_xy_m008"),
    ("G-A041", "ang_vel_xy_l2 -0.04", "go2_g_a041_a033_ang_vel_xy_m004"),
    ("G-A042", "track_lin_vel_xy_exp 1.6", "go2_g_a042_a033_track_lin_vel_xy_160"),
    ("G-A047", "flat_orientation_l2 -0.5", "go2_g_a047_a033_flat_orientation_m05"),
)
CASES = ("rough_lateral", "rough_forward", "stairs_10_down", "stairs_15_down", "forward_nominal", "dr_seed_101")
SEEDS = (101, 202, 303)
FIELDS = ("survival_proxy", "posture_fall_env_count_pessimistic", "height_rel_p10", "height_rel_median",
          "speed_xy_mean", "projected_progress_m", "tracking_xy_rmse")
# go2_eval_telemetry.py:295-330 의 자세 게이트: upright = proj_grav_z <= -0.5 AND height_rel >= 0.18,
# 0.5 s 유예 뒤 0.5 s 연속이면 낙상.  채널별로 같은 타이머를 따로 돌린다(go2_a038_reread.py:285).
GRACE_S, HOLD_S, TILT_COS, HEIGHT_MIN, DT = 0.5, 0.5, 0.5, 0.18, 0.02


def case_dir(keep: str, seed: int, case: str) -> Path:
    return KEEP / keep / "evaluation/candidate/cases" / f"seed_{seed}" / case


def channels(path: Path) -> dict[str, int]:
    """판정기의 낙상 = (자세 불량 0.5 s 연속) ∪ (종료된 로봇)이다(go2_eval_telemetry.py:448-449).
    채널별 타이머만으로는 종료로만 잡힌 로봇과 두 채널이 번갈아 켜진 로봇이 빠지므로, 로봇마다 한 경로로 나눈다:
      height_only / tilt_only / both   각 채널이 따로 0.5 s 이상 이어졌다
      union_only    어느 채널도 혼자 0.5 s를 못 채웠지만 둘을 합친 불량이 0.5 s 이어졌다
      terminated_only 자세 타이머는 안 켜졌고 종료(term_base_contact 등)로만 낙상이 됐다
    terminated_base_contact 는 종료된 로봇 중 base_contact 종료 수(겹쳐 셀 수 있음, 참고)."""
    state: dict[int, dict[str, float]] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            e = state.setdefault(int(row["env_id"]), {"rt": 0.0, "rh": 0.0, "ru": 0.0, "ft": 0, "fh": 0, "fu": 0,
                                                      "term": 0, "bc": 0})
            if row.get("terminated") == "1":
                e["term"] = 1
                if row.get("term_base_contact") == "1":
                    e["bc"] = 1
            if float(row["time_s"]) < GRACE_S:
                continue
            tilt_bad = not float(row["proj_grav_z"]) <= -TILT_COS
            height_bad = not (row["height_rel"] != "" and float(row["height_rel"]) >= HEIGHT_MIN)
            for tag, bad in (("t", tilt_bad), ("h", height_bad), ("u", tilt_bad or height_bad)):
                if bad:
                    e["r" + tag] += DT
                    if e["r" + tag] >= HOLD_S:
                        e["f" + tag] = 1
                else:
                    e["r" + tag] = 0.0
    envs = list(state.values())
    return {"height_only": sum(1 for e in envs if e["fh"] and not e["ft"]),
            "tilt_only": sum(1 for e in envs if e["ft"] and not e["fh"]),
            "both": sum(1 for e in envs if e["ft"] and e["fh"]),
            "union_only": sum(1 for e in envs if e["fu"] and not e["ft"] and not e["fh"]),
            "terminated_only": sum(1 for e in envs if e["term"] and not e["fu"]),
            "fallen_total": sum(1 for e in envs if e["fu"] or e["term"]),
            "terminated_base_contact": sum(1 for e in envs if e["bc"]),
            "envs": len(envs)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, chans, axes = [], [], []
    for arm, change, keep in ARMS:
        for case in CASES:
            for seed in SEEDS:
                p = case_dir(keep, seed, case) / "summary.json"
                if not p.is_file():
                    continue
                s = json.loads(p.read_text(encoding="utf-8"))
                rows.append({"arm": arm, "change": change, "case": case, "seed": seed,
                             **{f: s.get(f) for f in FIELDS}})
                if case in ("rough_lateral", "stairs_10_down", "stairs_15_down"):
                    steps = p.parent / "steps.csv"
                    if steps.is_file():
                        chans.append({"arm": arm, "change": change, "case": case, "seed": seed, **channels(steps),
                                      "gate_falls_pessimistic": s.get("posture_fall_env_count_pessimistic")})
        bottleneck.ARM = KEEP / keep / "evaluation/candidate"
        try:
            _, summary = bottleneck.rows()
        except Exception as exc:  # 부분 수집 arm(A038·A041·A042)은 축 일부가 없다
            summary = []
            print(f"{arm}: axis table skipped ({type(exc).__name__})")
        for r in summary:
            axes.append({"arm": arm, "change": change, **{k: r[k] for k in (
                "axis", "case", "seed", "survival", "tracking", "score_70", "max_70", "binding_factor",
                "counterfactual_survival_1")}})
    for name, data in (("CASE_ROWS.csv", rows), ("FALL_CHANNELS.csv", chans), ("AXIS.csv", axes)):
        with (OUT / name).open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(data)
        print(OUT / name, len(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
