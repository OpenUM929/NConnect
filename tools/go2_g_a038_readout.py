#!/usr/bin/env python3
"""G-A038 판독 — 러너가 끝나지 못한 수확물을 판정 없이 읽는다.

G-A038(G-A033 + `ang_vel_xy_l2` -0.05→-0.08)은 학습·표적 9 case·평지 기준 case·G-A033 표지 5 case·
후보 영상 4개까지 마친 뒤, 첫 G-A033 영상에서 러너 결함으로 멈췄다(RUNNER_RC=1, 로그 폴더 미생성,
`tools/test_go2_runner_video_log_contract.py`).  RUNNER_STATUS.txt에 판정 필드가 없어 서버 게이트와
로컬 검증기는 둘 다 판정을 거부했다(INCONCLUSIVE).  서버는 2026-09-17 종료돼 재개하지 않는다.

이 도구는 판정을 만들지 않는다.  게이트·검증기와 같은 함수(verify_case, _case_proxy,
target_reading, build_policy)를 RUNNER_STATUS 검사 없이 불러, 측정된 것만 증거 CSV로 남긴다.

    python -B tools/go2_g_a038_readout.py      # 증거 CSV 재생성(원시 기록에서만)
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import build_go2_a033_reward_package as reward  # noqa: E402
import go2_reward_mechanism as mech  # noqa: E402
import verify_go2_a027_harvest as harvest  # noqa: E402
from go2_fixed_eval_report import _case_proxy, build_policy  # noqa: E402
from go2_target_gate import target_reading  # noqa: E402

KEEP = ROOT / "workspace/_keep"
CAND = KEEP / "go2_g_a038_a033_ang_vel_xy_m008"
BASE = KEEP / "go2_g_a033_a017_track_lin_vel_xy_150"   # G-A033 수확물: 저장 arm의 원본(69 case·steps.csv)
OUT = QUAD / "reports/evidence/go2_g_a038_readout_20260917"
SPEC = json.loads(reward.SPECS["G-A038"].read_text(encoding="utf-8"))
FAILED_LINE = "tee: /workspace/_keep/go2_g_a038_a033_ang_vel_xy_m008/logs/g_a033_videos/"
TIMELINE_CASE = "stairs_10_down"   # 이름과 달리 실제 10 cm 오르기(STAIRS_CLIMB.csv)
BIN_S = 2
# 예측 표(PROBE_SITUATIONS.csv)의 상황 ↔ 표적 묶음
ZONES = (("sway", "rough_lateral"), ("push", "push_pos_x"), ("climb", "stairs_10_climb"))


def fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def kv(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


def registry_path() -> Path:
    return CAND / "meta/go2_self_eval_registry.json"


def std() -> float:
    return float(load(registry_path())["score"].get("tracking_proxy_std", 0.5))


def case_dir(root: Path, seed: str, case_id: str) -> Path:
    return root / "cases" / f"seed_{seed}" / case_id


def fingerprint_rows() -> list[list[str]]:
    base = SPEC["baseline"]
    single = SPEC["single_change"]
    rows = [["check", "expected", "observed", "ok"]]

    def add(check: str, expected, observed) -> None:
        rows.append([check, fmt(expected), fmt(observed), fmt(expected == observed)])

    env_line = next(line for line in (CAND / "training/ENV_REWARD_CHECK.txt").read_text(encoding="utf-8").splitlines()
                    if line.startswith("ENV_REWARDS_OK"))
    observed = dict(item.split("=", 1) for item in env_line.split()[2:])
    for name, value in SPEC["rewards"]["candidate"].items():
        add(f"env_reward:{name}", float(value), float(observed[name]))
    add("single_change", f"{single['name']}:{single['from']}->{single['to']}",
        kv(CAND / "training/TRAIN_STATUS.txt")["SINGLE_CHANGE"])
    train = kv(CAND / "training/TRAIN_STATUS.txt")
    for key, value in (("TRAIN_RC", "0"), ("SEED", str(SPEC["training"]["seed"])),
                       ("NUM_ENVS", str(SPEC["training"]["num_envs"])),
                       ("MAX_ITERATIONS", str(SPEC["training"]["max_iterations"]))):
        add(f"train:{key}", value, train[key])
    pin = kv(CAND / "training/CHECKPOINT_PIN.txt")
    add("eval_checkpoint_iter", str(SPEC["evaluation"]["checkpoint_iter"]), pin["EVAL_CHECKPOINT_ITER"])
    model_sha = hashlib.sha256((CAND / "training/model_best.pt").read_bytes()).hexdigest()
    add("model_best_is_pinned_checkpoint", pin["EVAL_CHECKPOINT_SHA"], model_sha)
    for arm, expected_model in (("candidate", model_sha), ("g_a033_sentinel", base["model_sha256"])):
        identity = load(CAND / "evaluation" / arm / "identity.json")
        add(f"{arm}:model_sha256", expected_model, identity["model_sha256"])
        add(f"{arm}:evaluator_sha256", base["evaluator_sha256"], identity["evaluator_sha256"])
        add(f"{arm}:registry_sha256", base["registry_sha256"], identity["registry_sha256"])
    status = kv(CAND / "RUNNER_STATUS.txt")
    rows.append(["runner_rc", "0", status.get("RUNNER_RC", ""), "False"])
    rows.append(["runner_decision", "TARGET_STAGE_COMPLETE", status.get("DECISION", ""), "False"])
    log = (CAND / "launcher.log").read_bytes().decode("utf-8", errors="replace")
    # Numbered by "\n" as an editor shows it; the progress bars inside use bare "\r".
    line = next((i + 1 for i, text in enumerate(log.split("\n")) if text.startswith(FAILED_LINE)), None)
    rows.append(["runner_stop", "none", f"launcher.log:{line} tee into missing logs/g_a033_videos", "False"])
    verdict = load(CAND / "harvest_verification.json")["verdict"]
    rows.append(["verifier_verdict", "any verdict", verdict, fmt(verdict == "INCONCLUSIVE")])
    return rows


def target_rows() -> tuple[list[list[str]], dict]:
    s = std()
    records: dict[tuple[str, str], dict] = {}
    faults = {}
    entries = [e for group in SPEC["preregistered"]["target_groups"].values() for e in group]
    for entry in [SPEC["evaluation"]["catastrophe_case"], *entries]:
        scenario, case_id, seed = entry.split(":")
        for arm, root in (("candidate", CAND / "evaluation/candidate"), ("baseline", BASE / "evaluation/candidate")):
            folder = case_dir(root, seed, case_id)
            faults[(arm, entry)] = harvest.verify_case(folder, scenario, case_id, int(seed))["faults"]
            summary = load(folder / "summary.json")
            records[(arm, entry)] = {"proxy": _case_proxy(case_id, summary, s), "raw": summary}
    reading = target_reading(lambda e: records[("baseline", e)], lambda e: records[("candidate", e)],
                             SPEC["preregistered"])
    header = ["group", "case", "proxy_g_a033", "proxy_g_a038", "delta", "survival_g_a033", "survival_g_a038",
              "tracking_g_a033", "tracking_g_a038", "posture_falls_g_a033", "posture_falls_g_a038",
              "terminated_g_a033", "terminated_g_a038", "speed_g_a033", "speed_g_a038",
              "height_p10_g_a033", "height_p10_g_a038", "case_faults"]
    rows = [header]
    for group in reading["target_groups"]:
        for r in group["rows"]:
            rows.append([group["group"], r["case"], *(fmt(r[k]) for k in (
                "proxy_baseline", "proxy_candidate", "delta", "survival_baseline", "survival_candidate",
                "tracking_baseline", "tracking_candidate", "posture_falls_baseline", "posture_falls_candidate",
                "terminated_baseline", "terminated_candidate", "speed_baseline", "speed_candidate",
                "height_p10_baseline", "height_p10_candidate")),
                ";".join(map(str, faults[("candidate", r["case"])] + faults[("baseline", r["case"])]))])
    gate = SPEC["preregistered"]
    summary = {"target_mean_proxy_delta": reading["target_mean_proxy_delta"],
               "target_groups_improved": reading["target_groups_improved"],
               "criterion_1_passed": reading["passed"],
               "min_target_mean_proxy_delta": gate["min_target_mean_proxy_delta"],
               "min_target_groups_improved": gate["min_target_groups_improved"],
               "groups": {g["group"]: g["mean_delta"] for g in reading["target_groups"]},
               "records": records}
    return rows, summary


def sentinel_rows() -> list[list[str]]:
    s = std()
    tol = SPEC["evaluation"]["sentinel_tolerance"]
    rows = [["case", "survival_now", "survival_stored", "tracking_now", "tracking_stored", "ruler_fields_differ",
             "case_faults", "agrees"]]
    for entry in SPEC["evaluation"]["sentinel_cases"]:
        scenario, case_id, seed = entry.split(":")
        here = case_dir(CAND / "evaluation/g_a033_sentinel", seed, case_id)
        there = case_dir(BASE / "evaluation/candidate", seed, case_id)
        case_faults = harvest.verify_case(here, scenario, case_id, int(seed))["faults"]
        a, b = load(here / "summary.json"), load(there / "summary.json")
        ruler = [key for key in harvest.CASE_IDENTITY_FIELDS if a.get(key) != b.get(key)]
        pa, pb = _case_proxy(case_id, a, s), _case_proxy(case_id, b, s)
        agree = (not ruler and not case_faults
                 and abs(pa["survival_proxy"] - pb["survival_proxy"]) <= tol["survival_abs"] + 1e-9
                 and abs(pa["tracking_proxy"] - pb["tracking_proxy"]) <= tol["tracking_proxy_abs"] + 1e-9)
        rows.append([entry, fmt(pa["survival_proxy"]), fmt(pb["survival_proxy"]), fmt(pa["tracking_proxy"]),
                     fmt(pb["tracking_proxy"]), ";".join(ruler), ";".join(map(str, case_faults)), fmt(agree)])
    return rows


def timeline_rows() -> list[list[str]]:
    rows = [["arm", "seed", "t_from_s", "t_to_s", "upright_fraction", "height_rel_mean", "speed_xy_mean",
             "proj_grav_z_mean", "rows"]]
    for arm, root in (("G-A033", BASE / "evaluation/candidate"), ("G-A038", CAND / "evaluation/candidate")):
        for seed in ("101", "202", "303"):
            bins: dict[int, list[float]] = defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0.0])
            with (case_dir(root, seed, TIMELINE_CASE) / "steps.csv").open(encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    b = bins[int(float(row["time_s"]) // BIN_S)]
                    b[0] += 1
                    b[1] += int(row["upright"])
                    b[2] += float(row["height_rel"])
                    b[3] += float(row["speed_xy"])
                    b[4] += float(row["proj_grav_z"])
            for k in sorted(bins):
                n, up, h, v, g = bins[k]
                rows.append([arm, seed, str(k * BIN_S), str((k + 1) * BIN_S), f"{up / n:.6f}", f"{h / n:.6f}",
                             f"{v / n:.6f}", f"{g / n:.6f}", str(int(n))])
    return rows


def curriculum_rows() -> list[list[str]]:
    """평가 고정 iter에서 두 팔의 커리큘럼 도달 레벨 차이 (2026-09-18 신설).

    두 팔 모두 iter 900에서 평가했다.  그 시점의 지형 레벨이 다르면 계단 결과의 차이에는 레버 효과와
    학습 진도 차이가 섞인다.  값은 산출물에서 생성된 원장 `reports/runs/TERRAIN_AT_PIN.csv`에서 읽는다
    (평균은 로봇 전체·지형 5종이라 계단 열이 어디까지 갔는지는 여전히 모른다).
    """
    pins: dict[str, dict[str, str]] = defaultdict(dict)
    with (QUAD / "reports/runs/TERRAIN_AT_PIN.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pins[row["run"]][row["iteration"]] = row["terrain"]
    base, cand = pins[BASE.name], pins[CAND.name]
    pin = str(SPEC["evaluation"]["checkpoint_iter"])
    rows = [["iteration", "g_a033_terrain", "g_a038_terrain", "delta", "is_eval_checkpoint"]]
    for iteration in sorted(set(base) & set(cand), key=int):
        delta = float(cand[iteration]) - float(base[iteration])
        rows.append([iteration, base[iteration], cand[iteration], f"{delta:+.4f}",
                     "True" if iteration == pin else "False"])
    return rows


def flat_rows() -> list[list[str]]:
    s = std()
    scenario, case_id, seed = SPEC["evaluation"]["catastrophe_case"].split(":")
    rows = [["arm", "case", "survival_proxy", "tracking_proxy", "scenario_proxy", "tracking_xy_rmse",
             "speed_xy_mean", "height_rel_mean", "posture_falls", "terminated"]]
    for arm, root in (("G-A033", BASE / "evaluation/candidate"), ("G-A038", CAND / "evaluation/candidate")):
        summary = load(case_dir(root, seed, case_id) / "summary.json")
        proxy = _case_proxy(case_id, summary, s)
        rows.append([arm, f"{scenario}:{case_id}:{seed}", fmt(proxy["survival_proxy"]), fmt(proxy["tracking_proxy"]),
                     fmt(proxy["scenario_proxy"]), fmt(summary["tracking_xy_rmse"]), fmt(summary["speed_xy_mean"]),
                     fmt(summary["height_rel_mean"]), fmt(summary["posture_fall_env_count_pessimistic"]),
                     fmt(summary["terminated_env_count"])])
    return rows


def guard_rows(records: dict) -> list[list[str]]:
    """What the full-stage guards (criterion 3) can already be bounded by.

    A scenario scores the minimum over its cases and seeds (build_policy), so the measured
    G-A038 cases give an upper bound on its G1 and G5 scores and a lower bound on their losses.
    """
    base = build_policy(BASE / "evaluation/candidate", registry_path())
    prereg = SPEC["preregistered"]
    rows = [["scenario", "g_a033_scenario_proxy", "g_a033_worst_case", "weight", "g_a038_measured_cases",
             "g_a038_scenario_proxy_upper_bound", "loss_lower_bound", "loss_unit", "limit", "exceeds_limit"]]
    for sid in ("G1", "G5"):
        scenario = base["scenarios"][sid]
        worst = min((c for c in base["cases"].values() if c["scenario_id"] == sid),
                    key=lambda c: c["proxy"]["scenario_proxy"])
        cand = sorted((entry, rec["proxy"]["scenario_proxy"]) for (arm, entry), rec in records.items()
                      if arm == "candidate" and entry.startswith(sid + ":"))
        upper = min(value for _, value in cand)
        drop = max(0.0, scenario["scenario_proxy"] - upper)
        if sid in prereg["flat_scenarios"]:
            loss, unit, limit = drop, "scenario_proxy", float(prereg["max_flat_scenario_proxy_drop"])
        else:
            loss, unit = drop * float(scenario["weight"]) * 70.0, "weighted_70"
            limit = float(prereg["max_scenario_weighted_loss_70_by_scenario"][sid])
        rows.append([sid, fmt(scenario["scenario_proxy"]), f"{worst['case_id']}@{worst['seed']}",
                     fmt(float(scenario["weight"])), ";".join(f"{e}={v:.6f}" for e, v in cand), fmt(upper),
                     fmt(loss), unit, fmt(limit), fmt(loss > limit + 1e-9)])
    return rows


def forecast_rows(groups: dict[str, float]) -> list[list[str]]:
    probe = {(r["term"], r["to"]): r for r in mech.read("PROBE_SITUATIONS.csv")}[("ang_vel_xy_l2", "-0.08")]
    rows = [["zone", "forecast_partial_margin_delta", "target_group", "observed_mean_proxy_delta",
             "direction_agrees"]]
    for zone, group in ZONES:
        forecast = float(probe[f"{zone}_delta"])
        observed = groups[group]
        rows.append([zone, probe[f"{zone}_delta"], group, fmt(observed),
                     fmt((forecast > 0) == (observed > 0))])
    return rows


def signed(value: float, places: int) -> str:
    return f"{value:+.{places}f}"   # ASCII sign: the claim check strips it before matching


def report_value_rows(targets: list[list[str]], summary: dict, timeline: list[list[str]],
                      flat: list[list[str]], guard: list[list[str]]) -> list[list[str]]:
    """The numbers GO2_G_A038_READOUT.md prints, as it prints them (claim check matches them by text)."""
    out = [["key", "shown"]]
    out.append(["target_mean_proxy_delta", signed(summary["target_mean_proxy_delta"], 3)])
    for group, value in summary["groups"].items():
        out.append([f"group_mean_delta:{group}", signed(value, 3)])
    head = targets[0]
    for row in targets[1:]:
        r = dict(zip(head, row))
        out.append([f"speed_g_a033:{r['case']}", f"{float(r['speed_g_a033']):.2f}"])
        out.append([f"speed_g_a038:{r['case']}", f"{float(r['speed_g_a038']):.2f}"])
    head = timeline[0]
    for row in timeline[1:]:
        r = dict(zip(head, row))
        for key in ("upright_fraction", "height_rel_mean"):
            out.append([f"{key}:{r['arm']}:{r['seed']}:{r['t_from_s']}", f"{float(r[key]):.3f}"])
    head = flat[0]
    for row in flat[1:]:
        r = dict(zip(head, row))
        for key in ("survival_proxy", "tracking_proxy", "speed_xy_mean", "height_rel_mean"):
            out.append([f"{key}:{r['arm']}", f"{float(r[key]):.3f}"])
    head = guard[0]
    for row in guard[1:]:
        r = dict(zip(head, row))
        places = 4 if r["scenario"] == "G5" else 3
        out.append([f"g_a033_scenario_proxy:{r['scenario']}", f"{float(r['g_a033_scenario_proxy']):.{places}f}"])
        out.append([f"g_a038_upper_bound:{r['scenario']}", f"{float(r['g_a038_scenario_proxy_upper_bound']):.3f}"])
        out.append([f"loss_lower_bound:{r['scenario']}", f"{float(r['loss_lower_bound']):.3f}"])
        out.append([f"limit:{r['scenario']}", f"{float(r['limit']):.3f}"])
    return out


def write(name: str, rows: list[list[str]]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    return path


def main() -> int:
    targets, summary = target_rows()
    timeline, flat, guard = timeline_rows(), flat_rows(), guard_rows(summary["records"])
    written = [
        write("FINGERPRINT.csv", fingerprint_rows()),
        write("TARGET_CASES.csv", targets),
        write("TARGET_SUMMARY.csv", [["item", "value"]] + [[k, fmt(v)] for k, v in summary.items()
                                                           if k not in ("records", "groups")]
              + [[f"group_mean_delta:{g}", fmt(v)] for g, v in summary["groups"].items()]),
        write("SENTINEL.csv", sentinel_rows()),
        write("STAIRS_10_CLIMB_TIMELINE.csv", timeline),
        write("FLAT_NOMINAL.csv", flat),
        write("GUARD_BOUNDS.csv", guard),
        write("FORECAST_CHECK.csv", forecast_rows(summary["groups"])),
        write("CURRICULUM_LAG.csv", curriculum_rows()),
        write("REPORT_VALUES.csv", report_value_rows(targets, summary, timeline, flat, guard)),
    ]
    for path in written:
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
