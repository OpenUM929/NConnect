"""축 점수를 원본 평가 기록에서 다시 계산해 **무엇이 점수를 묶고 있는지** 적는다.

이 도구가 존재하는 이유.  2026-09-18~19 동안 판독·기획·감사 셋이 모두 G5 를 "계단을 오른
로봇 수"로 이야기했다.  `body_rise_ge1` 은 우리가 만든 지표이고 **채점식에 들어가지 않는다**.
축 점수는 `go2_fixed_eval_report.py:29-60` 이 정하고, 계단 case 는 전진거리로 한 번 더 깎인다:

    tracking_xy = exp(-(xy_rmse / std)^2)                      std = registry.tracking_proxy_std
    completion  = min(1, projected_progress_m / (0.5 * steps * step_dt))   # stairs_* 만
    tracking    = min(tracking_xy, completion)                             # stairs_*
                = min(post_push_tracking, recovery_rate_upright)           # push_*
                = min(xy, yaw)                                            # combined_yaw_*
    proxy       = survival_proxy * tracking
    축 점수      = weight * 70 * min(case 별 proxy)                          # 최솟값 집계

`binding_factor` 열이 그 case 에서 최솟값을 만든 인수를 적는다.  `axis` 요약 행의
`counterfactual_survival_1` 은 **생존을 전부 1.0 으로 놓았을 때의 축 점수**다 — 자세 게이트를
완벽히 고쳤을 때의 상한이고, **측정이 아니라 반사실 계산이다**(성격 열에 그렇게 적는다).

2026-09-19 감사 D2: 이 산술이 대화에만 있고 저장소에 없었다 — 아무도 재검증할 수 없었다.
D3·D5 도 같은 뿌리다(사람이 손으로 센 값이 원자료와 어긋났다).  그래서 숫자를 사람이 아니라
이 도구가 만든다.
"""
from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
REGISTRY = QUAD / "config/go2_self_eval_registry.json"
OUT_DIR = QUAD / "reports/evidence/go2_axis_bottleneck_20260919"
OUT_CSV = OUT_DIR / "AXIS_BOTTLENECK.csv"
OUT_DOC = QUAD / "reports/GO2_AXIS_BOTTLENECK.md"

# 판독 대상 arm.  기준선이 바뀌면 여기 한 줄을 고치고 다시 돌린다.
ARM = QUAD.parent.parent / "_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
ARM_LABEL = "G-A033 evaluation/candidate"
SEEDS = (101, 202, 303)

FIELDS = ("axis", "case", "seed", "survival_v1", "survival_v2", "survival",
          "xy_rmse", "tracking_xy", "progress_m", "expected_m", "completion",
          "tracking", "proxy", "binding_factor", "terminated", "posture_fall",
          "height_rel_median", "kind")


def registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def track(rmse: float | None, std: float) -> float | None:
    """go2_fixed_eval_report.py `_track` 와 같은 식."""
    if rmse is None:
        return None
    return math.exp(-((float(rmse) / std) ** 2))


def case_row(axis: str, case: str, seed: int, summary: dict, std: float) -> dict:
    """한 case 의 proxy 와 **그 proxy 를 묶은 인수**를 낸다."""
    survival = summary.get("survival_proxy")
    xy = track(summary.get("tracking_xy_rmse"), std)
    tracking, completion, expected, progress = xy, None, None, None
    binding = "tracking_xy"
    if case.startswith("stairs_"):
        duration = float(summary.get("steps", 0)) * float(summary.get("step_dt", 0.02))
        expected = 0.5 * duration
        progress = float(summary.get("projected_progress_m") or 0.0)
        completion = min(1.0, progress / expected) if expected else None
        if completion is not None and xy is not None and completion < xy:
            tracking, binding = completion, "completion"
    elif case.startswith("combined_yaw"):
        yaw = track(summary.get("tracking_yaw_rmse"), std)
        if yaw is not None and xy is not None and yaw < xy:
            tracking, binding = yaw, "tracking_yaw"
    elif case.startswith("push_"):
        tracking = track(summary.get("post_push_tracking_xy_rmse"), std)
        binding = "post_push_tracking"
        recovery = (summary.get("recovery") or {}).get("recovery_rate_upright")
        if recovery is not None and tracking is not None and recovery < tracking:
            tracking, binding = recovery, "recovery_rate_upright"
    proxy = survival * tracking if survival is not None and tracking is not None else None
    # 생존이 tracking 보다 더 깎으면 점수를 묶는 것은 생존이다.
    if survival is not None and tracking is not None and survival < tracking:
        binding = "survival"
    return {
        "axis": axis, "case": case, "seed": seed,
        "survival_v1": summary.get("survival_proxy_v1"),
        "survival_v2": summary.get("survival_proxy_v2"),
        "survival": survival,
        "xy_rmse": summary.get("tracking_xy_rmse"),
        "tracking_xy": xy,
        "progress_m": progress, "expected_m": expected, "completion": completion,
        "tracking": tracking, "proxy": proxy, "binding_factor": binding,
        "terminated": summary.get("terminated_env_count"),
        "posture_fall": summary.get("posture_fall_env_count_pessimistic"),
        "height_rel_median": summary.get("height_rel_median"),
        "kind": "측정",
    }


def rows() -> tuple[list[dict], list[dict]]:
    reg = registry()
    std = float(reg["score"]["tracking_proxy_std"])
    points = float(reg["score"]["simulation_points"])
    detail: list[dict] = []
    summary_rows: list[dict] = []
    for scenario in reg["scenarios"]:
        axis, weight = scenario["id"], float(scenario["weight"])
        got: list[dict] = []
        for case in scenario["internal_cases"]:
            for seed in SEEDS:
                name = case.replace("{seed}", str(seed))
                path = ARM / "cases" / f"seed_{seed}" / name / "summary.json"
                if not path.is_file():
                    continue
                row = case_row(axis, name, seed, json.loads(path.read_text(encoding="utf-8")), std)
                detail.append(row)
                got.append(row)
        scored = [r for r in got if r["proxy"] is not None]
        if not scored:
            continue
        worst = min(scored, key=lambda r: r["proxy"])
        # 반사실: 생존을 전부 1.0 으로 놓는다 = 자세 게이트를 완벽히 고쳤을 때의 상한.
        ceiling = min(r["tracking"] for r in scored if r["tracking"] is not None)
        summary_rows.append({
            "axis": axis, "case": worst["case"], "seed": worst["seed"],
            # 문서는 5자리로 적는다.  CSV 에 원값을 넣으면 문서의 반올림 값이 아티팩트에 없어
            # 주장 검사가 '근거 없음'으로 잡는다 — 두 곳의 자릿수를 여기서 맞춘다(2026-09-19).
            "survival": round(worst["survival"], 5), "tracking": round(worst["tracking"], 5),
            "proxy": round(worst["proxy"], 5),
            "score_70": round(worst["proxy"] * weight * points, 5),
            "counterfactual_survival_1": round(ceiling * weight * points, 5),
            "binding_factor": worst["binding_factor"],
            "max_70": round(weight * points, 5),
            "kind": "측정 / counterfactual_survival_1 만 예측(반사실)",
        })
    return detail, summary_rows


def write_csv(stream: io.StringIO, detail: list[dict], summary_rows: list[dict]) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("section",) + FIELDS)
    for row in detail:
        writer.writerow(("case",) + tuple("" if row[f] is None else row[f] for f in FIELDS))
    head = ("axis", "case", "seed", "survival", "tracking", "proxy", "score_70",
            "counterfactual_survival_1", "binding_factor", "max_70", "kind")
    writer.writerow(())
    writer.writerow(("section",) + head)
    for row in summary_rows:
        writer.writerow(("axis",) + tuple("" if row[k] is None else row[k] for k in head))


def document(summary_rows: list[dict]) -> str:
    lines = [
        "# Go2 축 병목 판독 — 무엇이 점수를 묶는가 (2026-09-19)",
        "",
        f"대상 arm: `{ARM_LABEL}`. 생성 `tools/go2_axis_bottleneck.py`,",
        f"증거 `{OUT_CSV.relative_to(QUAD).as_posix()}`, 관문 `tools/test_go2_axis_bottleneck_contract.py`.",
        "",
        "채점식은 `workspace/training/quadruped/go2_fixed_eval_report.py:29-60` 이다. 축 점수는",
        "**case 별 proxy 의 최솟값**이고, 계단 case 는 `completion`(전진거리/기대거리)으로 한 번 더 깎인다.",
        "`body_rise_ge1` 같은 오르기 수는 **채점식에 들어가지 않는다** — 2026-09-18~19 에 판독·기획·감사가",
        "모두 그 지표로 G5 를 이야기했고, 그것이 이 문서를 만든 이유다.",
        "",
        "| 축 | 최솟값 case | 생존 | tracking | 축 점수 | 만점 | 묶는 인수 | 생존 1.0 반사실 |",
        "|---|---|---:|---:|---:|---:|---|---:|",
    ]
    for row in summary_rows:
        lines.append(
            # 자릿수를 CSV 와 같게: `:.5f` 로 늘려 적으면 그 철자가 아티팩트에 없어 주장 검사에 걸린다.
            f"| {row['axis']} | `{row['case']}`@{row['seed']} | {row['survival']} |"
            f" {row['tracking']} | **{row['score_70']}** | {row['max_70']} |"
            f" `{row['binding_factor']}` | {row['counterfactual_survival_1']} |")
    lines += [
        "",
        "`생존 1.0 반사실` 은 **측정이 아니라 반사실 계산**이다 — 자세 게이트를 완벽히 고쳤을 때의 상한이고,",
        "그 차이가 이득구간 밖인지는 이 표가 말하지 않는다(`reports/runs/BASELINE_MARGIN.csv` 의",
        "`delta_resample_sd` 는 **같은 계측으로 잰 두 arm 의 차이**에 대한 값이라 계측 자체를 바꾸는",
        "반사실에 그대로 적용할 수 없다 — 2026-09-19 감사 D4).",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    detail, summary_rows = rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    write_csv(buffer, detail, summary_rows)
    OUT_CSV.write_text(buffer.getvalue(), encoding="utf-8", newline="")
    OUT_DOC.write_text(document(summary_rows), encoding="utf-8", newline="")
    print(OUT_CSV.relative_to(ROOT).as_posix())
    print(OUT_DOC.relative_to(ROOT).as_posix())
    print(f"case {len(detail)}행, 축 {len(summary_rows)}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
