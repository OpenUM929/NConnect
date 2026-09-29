"""보상 기준 arm 대비 효과 판독 — 채택 판정과 분리한다 (2026-09-27, G-A051 부터).

G-A051 은 G-A048 의 보상 위에서 한 항을 바꾼다.  채택은 여전히 G-A033 저장 arm 대비
(`tools/verify_go2_basic_motion_harvest.py`, fact_rules_v1 + 계획 screening) 이고, **효과**는
후보 − G-A048 로 읽는다.  이 도구는 두 번째만 한다.  채택 문턱을 바꾸지 않고, 채택 판정을 대신하지 않는다.

사양 `preregistered.reward_base_comparison` 이 규칙을 고정한다(결과를 본 뒤 바꾸지 않는다):
  review_requires    정량 후보 검토 대상(REVIEW_CANDIDATE)이 될 조건 — 모두 만족해야 한다
     adoption           채택 검증기의 combined_verdict.verdict 가 이 값(QUANT_SUCCESS_VIDEO_REVIEW_PENDING =
                        영상 검토 전 정량 조건 충족.  "채택 PASS" 가 아니다)
     hypothesis         go2_dial_hypothesis 지표 이름 → 요구 판정
     min_total_delta_70 후보 70점 proxy 총점 − 기준 arm 총점 의 하한
     min_speed          험지 옆걸음 이동 속도 크기(3 seed 평균)의 사전등록 하한.  충족해도 "감속하지 않았다" 는 뜻이 아니고
                        (방향 없는 크기다) 큰 감속을 제한하는 보조 조건이다 — 같은 case 의 추종·전진거리와 함께 읽는다
  disclosed_cases    후보·기준 arm·차이를 공개할 case 목록 (판정에 쓰지 않는다)
판정: REVIEW_CANDIDATE / NOT_REVIEW_CANDIDATE(실패 항목 나열) / INCONCLUSIVE(수확물 미검증·자료 결측).
REVIEW_CANDIDATE 는 **최종 진보 판정이 아니다.**  기준 arm 대비 보호 case(계단·밀침·복합 회전)의 허용 손실이 사전등록되지
않았으므로, 다른 축의 상승이 특정 손실을 덮을 수 있다.  그 차이는 공개하고 사람이 후보 검토에서 읽는다.

    python -B tools/go2_reward_base_comparison.py G-A051 --harvest workspace/_keep/<keep_dir>
    python -B tools/go2_reward_base_comparison.py G-A051 --harvest <다른 arm> --no-verify   (판독기 자체 확인)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_axis_bottleneck as bottleneck  # noqa: E402
import go2_dial_hypothesis as hypothesis  # noqa: E402

SEEDS = (101, 202, 303)
FIELDS = ("posture_fall_env_count_pessimistic", "survival_proxy", "tracking_xy_rmse", "speed_xy_mean",
          "projected_progress_m")


def axes(harvest: Path) -> dict[str, float]:
    bottleneck.ARM = harvest / "evaluation" / "candidate"
    _detail, summary = bottleneck.rows()
    return {r["axis"]: float(r["score_70"]) for r in summary}


def case_values(harvest: Path, case: str) -> dict[str, float | None]:
    per: dict[str, list[float]] = {f: [] for f in FIELDS}
    for seed in SEEDS:
        path = harvest / "evaluation/candidate/cases" / f"seed_{seed}" / case / "summary.json"
        if not path.is_file():
            return {f: None for f in FIELDS}
        data = json.loads(path.read_text(encoding="utf-8"))
        for f in FIELDS:
            if data.get(f) is None:
                return {f: None for f in FIELDS}
            per[f].append(float(data[f]))
    out: dict[str, float | None] = {}
    for f, vs in per.items():
        out[f] = float(sum(vs)) if f == "posture_fall_env_count_pessimistic" else round(statistics.fmean(vs), 5)
    return out


def adoption(harvest: Path, work_id: str) -> str | None:
    path = harvest / "harvest_verification.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("work_id") != work_id:
        return None
    return (data.get("combined_verdict") or {}).get("verdict")


def compare(spec: dict, harvest: Path, verify: bool = True) -> dict:
    block = spec["preregistered"]["reward_base_comparison"]
    base = ROOT / block["base_arm"]
    need = block["review_requires"]
    out = {"work_id": spec["work_id"], "tier": "INTERNAL_EFFECT_READOUT",
           "effect": f"candidate - {block['base_name']}", "adoption_baseline": spec["baseline"]["name"],
           "harvest": str(harvest), "base_arm": block["base_arm"]}
    cand_axes, base_axes = axes(harvest), axes(base)
    missing = sorted(set(base_axes) - set(cand_axes))
    out["axes"] = {a: {"candidate": cand_axes.get(a), "base": base_axes[a],
                       "delta": None if a not in cand_axes else round(cand_axes[a] - base_axes[a], 5)}
                   for a in sorted(base_axes)}
    total_c, total_b = round(sum(cand_axes.values()), 5), round(sum(base_axes.values()), 5)
    out["total_70"] = {"candidate": total_c, "base": total_b, "delta": round(total_c - total_b, 5)}
    out["cases"] = {}
    for case in block["disclosed_cases"]:
        c, b = case_values(harvest, case), case_values(base, case)
        out["cases"][case] = {f: {"candidate": c[f], "base": b[f],
                                  "delta": None if c[f] is None or b[f] is None else round(c[f] - b[f], 5)}
                              for f in FIELDS}
    hyp = hypothesis.read(spec, harvest, require_verified=verify)
    out["hypothesis"] = {k: v["verdict"] for k, v in hyp["indicators"].items()}
    adopt = adoption(harvest, spec["work_id"]) if verify else need["adoption"]
    out["adoption_verdict"] = adopt if verify else "not checked (--no-verify)"
    speed = out["cases"].get("rough_lateral", {}).get("speed_xy_mean", {}).get("candidate")
    floor = float(need["min_speed"]["rough_lateral_speed_below"])
    below = speed is None or speed < floor
    out["min_speed"] = {"rough_lateral_speed_mean": speed, "floor": floor, "below_floor": below,
                        "note": "auxiliary: meeting the floor does not show the policy did not slow down; read with tracking and progress"}
    rough = out["cases"].get("rough_lateral", {}).get("posture_fall_env_count_pessimistic", {})
    out["rough_reading"] = ("REDUCED_BELOW_TARGET" if out["hypothesis"].get("rough_lateral_posture_falls") == "INSUFFICIENT"
                            else out["hypothesis"].get("rough_lateral_posture_falls"))
    out["rough_falls"] = rough
    out["not_judged"] = block.get("not_judged", "")
    if missing or adopt is None or speed is None or any(v in ("MISSING", hypothesis.UNVERIFIED)
                                                         for v in out["hypothesis"].values()):
        out["verdict"], out["failed"] = "INCONCLUSIVE", [f"missing axes {missing}" if missing else "data or verification missing"]
        return out
    failed = []
    if adopt != need["adoption"]:
        failed.append(f"adoption {adopt} != {need['adoption']}")
    for name, want in need["hypothesis"].items():
        if out["hypothesis"].get(name) != want:
            failed.append(f"hypothesis {name} {out['hypothesis'].get(name)} != {want}")
    if out["total_70"]["delta"] < float(need["min_total_delta_70"]):
        failed.append(f"total delta {out['total_70']['delta']} < {need['min_total_delta_70']}")
    if below:
        failed.append(f"rough_lateral speed {speed} < preregistered floor {floor}")
    out["verdict"], out["failed"] = ("REVIEW_CANDIDATE" if not failed else "NOT_REVIEW_CANDIDATE"), failed
    out["verdict_scope"] = "quantitative review candidate only; not a final progress verdict"
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("work_id", choices=sorted(hypothesis.SPECS))
    parser.add_argument("--harvest", type=Path, required=True)
    parser.add_argument("--no-verify", action="store_true", help="판독기 자체 확인용: 채택 검증 없이 읽는다")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    spec = hypothesis.load_spec(args.work_id)
    if "reward_base_comparison" not in spec["preregistered"]:
        parser.error(f"{args.work_id} has no preregistered.reward_base_comparison")
    harvest = args.harvest if args.harvest.is_absolute() else ROOT / args.harvest
    result = compare(spec, harvest, verify=not args.no_verify)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
