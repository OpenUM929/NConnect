#!/usr/bin/env python3
"""G-A060 PC2 세 점 분석 자료 (2026-10-03) — 기존 계산식을 그대로 재사용해 Codex 판단용 자료를 만든다.

새 정의를 만들지 않는다. 쓰는 계산식:
  - G1~G7 내부 proxy·case 지표: tools/go2_g_a057_sweep_compare.axis_scores / case_metrics
  - 상태 → 결과 표(초기 몸높이·기울기·속도, 계단 모서리, 밀침 사건): tools/go2_state_outcome.run
  - 험지 옆걸음 낙상 직전 사건표(채널 순서·직전 1초 상태): tools/go2_failure_events
입력은 회수 압축 해제본 workspace/server_returns/G-A060/extracted/ 만 읽는다. 학습 seed 42 한 개, PC2(RTX 5070) 자료이므로
서버·PC1 수치와 한 표에서 효과로 비교하지 않는다(HANDOFF_G_A060_PC2.md §5). 보상 값·다음 점은 고르지 않는다.

    python -B tools/go2_g_a060_pc2_analysis.py
출력: workspace/training/quadruped/reports/evidence/go2_g_a060_pc2_analysis_20261003/
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_axis_bottleneck as axis  # noqa: E402
import go2_failure_events as fe  # noqa: E402
import go2_g_a057_sweep_compare as cmp  # noqa: E402
import go2_state_outcome as so  # noqa: E402

SRC = ROOT / "workspace/server_returns/G-A060/extracted"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a060_pc2_analysis_20261003"
ARMS = (  # (짧은 이름, 변경, 회수 폴더)
    ("PC2_B1", "A048 그대로 (기준)", "go2_g_a060_pc2_a048_seed42"),
    ("PC2_ang008", "ang_vel_xy_l2 -0.05->-0.08", "go2_g_a060_pc2_ang_vel_xy_l2_m0p08"),
    ("PC2_track14", "track_lin_vel_xy_exp 1.5->1.4", "go2_g_a060_pc2_track_lin_vel_xy_exp_p1p4"),
)
CASES = (*cmp.FALL_CASES, *cmp.STAIRS, "combined_yaw_left")
LOG_KEYS = ("Mean reward", "Curriculum/terrain_levels", "Episode_Termination/base_contact",
            "Episode_Termination/time_out", "Mean action noise std")


def write_csv(path: Path, data: list[dict]) -> None:
    cols: list[str] = []
    for r in data:
        cols += [k for k in r if k not in cols]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(data)


def training_curve(arm: Path) -> list[dict]:
    """candidate_training.log 에서 100 iter 마다 RSL-RL 요약값을 읽는다(마지막 iter 포함)."""
    text = (arm / "logs/candidate_training.log").read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"Learning iteration (\d+)/\d+", text)
    out = []
    for i in range(1, len(blocks) - 1, 2):
        it = int(blocks[i])
        if it % 100 and it != 999:
            continue
        row = {"iter": it}
        for k in LOG_KEYS:
            m = re.search(re.escape(k) + r":\s*(-?[\d.]+)", blocks[i + 1])
            row[k] = float(m.group(1)) if m else None
        out.append(row)
    return out


def axis_and_cases() -> tuple[list[dict], list[dict]]:
    std = float(axis.registry()["score"]["tracking_proxy_std"])
    axes, case_rows = [], []
    for name, change, folder in ARMS:
        arm = SRC / folder
        a = cmp.axis_scores(arm)
        row = {"arm": name, "change": change, "total_70": a["total"]}
        for ax in ("G1", "G2", "G3", "G4", "G5", "G6", "G7"):
            g = a.get(ax, {})
            row.update({f"{ax}_score": g.get("score"), f"{ax}_worst_survival": g.get("survival"),
                        f"{ax}_worst_tracking": g.get("tracking"), f"{ax}_worst_case": g.get("worst")})
        axes.append(row)
        for c in CASES:
            if c == "combined_yaw_left":
                continue  # FALL_CASES 밖 — 상태표(go2_state_outcome)에서만 본다
            m = cmp.case_metrics(arm, c, std)
            case_rows.append({"arm": name, "case": c, **m})
    return axes, case_rows


def state_tables() -> dict:
    so.KEEP = SRC
    so.OUT = OUT / "state_outcome"
    so.ARMS = {name: (folder, "pc2") for name, _, folder in ARMS}
    so.STATIONARY = set()
    so.PAIRS = [("PC2_B1", "PC2_ang008", "ang_vel_xy -0.05->-0.08 (A048 base, PC2)"),
                ("PC2_B1", "PC2_track14", "track 1.5->1.4 (A048 base, PC2)")]
    so.run()  # 낙상 수를 summary.json 과 대조(FALL_COUNT_CHECK.csv), 높이 산술 오차 assert
    return json.loads((so.OUT / "CHECKS.json").read_text(encoding="utf-8"))


def failure_events() -> list[dict]:
    """go2_failure_events 의 사건 정의 그대로. 원 도구의 FALL_CHANNELS.csv 대조 대신 summary.json 낙상 수와 대조한다."""
    fe.KEEP = SRC
    fe.ARMS = tuple((n, c, f) for n, c, f in ARMS)
    out_dir = OUT / "rough_lateral_events"
    out_dir.mkdir(parents=True, exist_ok=True)
    events, check = [], []
    for name, change, folder in ARMS:
        for seed in fe.SEEDS:
            cdir = SRC / folder / "evaluation/candidate/cases" / f"seed_{seed}" / fe.CASE
            envs = fe.load(cdir / "steps.csv")
            n_fall = 0
            for env, rows in sorted(envs.items()):
                c = fe.classify(rows)
                n_fall += bool(c["channel"])
                r = fe.event_row(name, seed, env, rows, c)
                r["change"] = change
                events.append(r)
            s = json.loads((cdir / "summary.json").read_text(encoding="utf-8"))
            want = s.get("posture_fall_env_count_optimistic")
            check.append({"arm": name, "seed": seed, "my_falls": n_fall, "summary_falls": want, "match": want == n_fall})
    fe.matched_control(events)
    for r in events:
        r.pop("_episode", None)
    write_csv(out_dir / "EVENTS.csv", events)
    write_csv(out_dir / "FAMILY_SUMMARY.csv", fe.summarize(events))
    write_csv(out_dir / "EVENTS_COUNT_CHECK.csv", check)
    return check


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    axes, case_rows = axis_and_cases()
    write_csv(OUT / "AXIS_SCORES.csv", axes)
    write_csv(OUT / "CASE_METRICS.csv", case_rows)
    curves = []
    for name, _, folder in ARMS:
        curves += [{"arm": name, **r} for r in training_curve(SRC / folder)]
    write_csv(OUT / "TRAINING_CURVE.csv", curves)
    checks = state_tables()
    ev_check = failure_events()
    prov = {
        "tool": "tools/go2_g_a060_pc2_analysis.py",
        "source": SRC.relative_to(ROOT).as_posix(),
        "arms": [{"arm": n, "change": c, "folder": f,
                  "result_status": (SRC / f / "RESULT_STATUS.txt").read_text(encoding="utf-8").split()} for n, c, f in ARMS],
        "state_outcome_checks": {k: (len(v) if isinstance(v, list) else v) for k, v in checks.items()},
        "rough_lateral_fall_count_match": all(c["match"] for c in ev_check),
        "limits": ["학습 seed 42 한 개", "PC2 RTX 5070 · Isaac Lab 2.3.2 — 서버·PC1과 효과 비교 금지",
                   "steps.csv 에 발 위치·접촉 채널 없음 — 발 새로 딛기(지지 갱신) 단계는 이 자료로 볼 수 없다",
                   "roll·pitch 구분 없음(proj_grav_z 만)", "영상 미시청(VIDEO_UNKNOWN)", "내부 proxy — 공식 점수 아님"],
    }
    (OUT / "PROVENANCE.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"fall_match": prov["rough_lateral_fall_count_match"], **prov["state_outcome_checks"]}, ensure_ascii=False))
    return 0 if prov["rough_lateral_fall_count_match"] and not checks.get("fall_check_mismatch") else 1


if __name__ == "__main__":
    raise SystemExit(main())
