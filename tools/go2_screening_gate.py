"""계획 §4의 screening 판정 — 보수적 설계 기준이지 공식 기준이나 유의수준이 아니다 (로컬 전용).

`upload/plan/GO2_FORWARD_STAIRS_POLICY_20260921.md` §4가 정한 세 묶음을 그대로 옮긴 것이다.
서버 게이트(`tools/go2_target_gate.py`)는 GPU 시간만 배분하고, 최종 판정은 회수 뒤 로컬에서 한다
(`tools/verify_go2_basic_motion_harvest.py`가 `fact_rules_v1`을, 이 모듈이 계획 §4를 읽는다).
둘 다 통과해야 screening 통과다 — 이 모듈은 `fact_rules_v1`을 **약화시키지 않는다**.

  계단 개선   10·15cm 각각 seed별 전진거리 차이의 중앙값 > 0, 각 높이의 pooled ≥1단·≥2단이
              기준선 이상, 네 등반수 항 중 최소 하나가 엄격 증가.
  정체 감소   두 높이 모두 seed별 정체시간비율 차이의 중앙값 < 0 (`tools/go2_stall_diagnostics.py`).
              조기 낙상으로 정체가 짧아진 것을 성공으로 읽지 않도록 아래 보호를 함께 요구한다.
  표적 보호   네 case 각각 pooled 자세 낙상수 ≤ 기준선, seed별 survival 차이 중앙값 ≥ 0,
              험지 두 case는 tracking proxy 차이 중앙값 ≥ 0.
  밀침 보호   `post_a042_push_v1`(계획 `upload/plan/GO2_POST_A042_PLAN_20260922.md` §5)에서만.
              G6 `push_pos_x`·`push_neg_x` **각 방향**에 같은 세 검사를 건다. 나머지 검사·한도는
              `forward_stairs_v1`과 같은 코드이고, 판 이름을 주지 않으면 기본 판으로 판정한다.

판정: 필수 자료가 모두 있고 한 조건이라도 미달이면 `INTERNAL_GATE_FAIL`.  누락·지문 불일치·진단
불가는 `INTERNAL_GATE_INCONCLUSIVE`(0을 채워 넣지 않는다).  전부 충족이면 `INTERNAL_GATE_PASS` —
그것도 screening 통과일 뿐이고, 전수 69 case·보호축·영상·독립 학습 seed 대칭 반복이 남는다.

    python -B tools/go2_screening_gate.py --candidate workspace/_keep/<회차> [--out <파일>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))

import go2_climb_count as climb  # noqa: E402
import go2_stall_diagnostics as stall  # noqa: E402
import verify_go2_g_a030_harvest as a030  # noqa: E402
from go2_fixed_eval_report import _case_proxy  # noqa: E402

SEEDS = ("101", "202", "303")
STAIRS = ("stairs_10_down", "stairs_15_down")
ROUGH = ("rough_forward", "rough_lateral")
# 2026-09-22 (G-A043): 이 회차의 상황 계산은 밀침 칸이 음수다(push -0.0386).  계획
# `upload/plan/GO2_POST_A042_PLAN_20260922.md` §5 는 그래서 G6 ±x **각 방향**의 pooled 자세 낙상
# 비증가와 seed 중앙값 생존·추종 ≥0 을 요구한다.  규칙 판은 회차 사양이 고르고(`plan_screening.version`),
# 기본값은 G-A042 가 판정받은 `forward_stairs_v1` 그대로다 — 과거 판정은 바이트로 재현된다.
PUSH = ("push_pos_x", "push_neg_x")
# 2026-09-22 (G-A044): 계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md` §6 은 ±x 에만 걸려 있던 보호를
# **네 방향 전부**로 넓힌다.  상황 계산이 애초에 네 방향에서 나오고(`go2_reward_mechanism.PUSH_CASES`),
# A043 이 ±y 를 seed 101 관측으로만 두었기 때문이다.  기존 두 판은 글자 하나 건드리지 않는다 — 과거
# 판정은 바이트로 재현돼야 한다.  판을 고르는 것은 회차 사양(`plan_screening.version`)이다.
PUSH_Y = ("push_pos_y", "push_neg_y")
PUSH_ALL = (*PUSH, *PUSH_Y)
CASES = (*STAIRS, *ROUGH)
RULE_VERSIONS = {"forward_stairs_v1": CASES, "post_a042_push_v1": (*CASES, *PUSH),
                 "post_a043_push4_v1": (*CASES, *PUSH_ALL)}
SCENARIO = {"stairs_10_down": "G5", "stairs_15_down": "G5",
            "rough_forward": "G3", "rough_lateral": "G3",
            "push_pos_x": "G6", "push_neg_x": "G6",
            "push_pos_y": "G6", "push_neg_y": "G6"}
BASELINE_ARM = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
REGISTRY = QUAD / "config/go2_self_eval_registry.json"
PASS, FAIL, INCONCLUSIVE = "INTERNAL_GATE_PASS", "INTERNAL_GATE_FAIL", "INTERNAL_GATE_INCONCLUSIVE"
IDENTITY_FIELDS = ("model_sha256", "env_sha256", "evaluator_sha256", "registry_sha256")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _kv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return {key: value for line in path.read_text(encoding="utf-8").splitlines()
            if "=" in line for key, value in [line.split("=", 1)]}


def _harvest_root(arm: Path) -> Path | None:
    return arm.parents[1] if arm.parent.name == "evaluation" else None


def std() -> float:
    return float(json.loads(REGISTRY.read_text(encoding="utf-8"))["score"].get("tracking_proxy_std", 0.5))


def _identity(arm: Path) -> dict[str, Any]:
    path = arm / "identity.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value.get("identity", value) if isinstance(value, dict) else {}


def identity_faults(arm: Path, expected: dict[str, Any] | None = None,
                    reference: dict[str, Any] | None = None) -> list[str]:
    """Validate an arm identity before any screening number is interpreted.

    ``expected`` pins policy/checkpoint and instrument hashes when the caller has a campaign spec.
    ``reference`` pins the shared evaluator/registry for standalone comparisons.  Format validation
    remains active without either argument, so an identity made of placeholders can never pass.
    """
    identity = _identity(arm)
    faults: list[str] = []
    if not identity:
        return [f"identity_absent_or_unreadable:{arm}"]
    for key in IDENTITY_FIELDS:
        actual = identity.get(key)
        if not isinstance(actual, str) or not SHA256_RE.fullmatch(actual):
            faults.append(f"identity_{key}_invalid:{actual!r}")
        if expected is not None and expected.get(key) is not None and actual != expected[key]:
            faults.append(f"identity_{key}_mismatch:{actual!r}!={expected[key]!r}")
    for key in ("evaluator_sha256", "registry_sha256"):
        if reference is not None and reference.get(key) is not None and identity.get(key) != reference[key]:
            faults.append(f"identity_{key}_differs_from_baseline")
    # Standalone authority is local code plus the recovered files, never the other arm.  This also
    # catches a coordinated edit where both identity.json files contain the same well-formed lie.
    authorities = {
        "evaluator_sha256": _sha(QUAD / "go2_eval_telemetry.py"),
        "registry_sha256": _sha(REGISTRY),
    }
    for key, authoritative in authorities.items():
        if authoritative is not None and identity.get(key) != authoritative:
            faults.append(f"identity_{key}_differs_from_local_authority")
    root = _harvest_root(arm)
    if root is None and expected is None:
        faults.append("identity_has_no_expected_or_recovered_authority")
    if root is not None:
        candidate_arm = arm.name == "candidate"
        model_path = root / ("training/model_best.pt" if candidate_arm else "policy/baseline_model_best.pt")
        env_path = root / ("training/env.yaml" if candidate_arm else "policy/baseline_env.yaml")
        model_sha = _sha(model_path)
        env_sha = _sha(env_path)
        pin = _kv(root / "training" / "CHECKPOINT_PIN.txt") if candidate_arm else {}
        for key, actual in (("model_sha256", model_sha), ("env_sha256", env_sha)):
            if actual is None:
                faults.append(f"artifact_{key}_source_absent")
            elif identity.get(key) != actual:
                faults.append(f"identity_{key}_differs_from_recovered_artifact")
        if candidate_arm:
            if not pin:
                faults.append("checkpoint_pin_absent")
            else:
                if pin.get("EVAL_CHECKPOINT_SHA") != model_sha:
                    faults.append("checkpoint_pin_sha_differs_from_recovered_model")
                expected_iter = (expected or {}).get("checkpoint_iter", 900)
                if pin.get("EVAL_CHECKPOINT_ITER") != str(expected_iter):
                    faults.append("checkpoint_pin_iter_mismatch")
    return faults


def cases_for(version: str | None) -> tuple[str, ...]:
    """사양이 고른 규칙 판의 case 목록.  모르는 판은 기본 판으로 내려가지 않고 이름으로 막는다."""
    if version is None:
        return CASES
    if version not in RULE_VERSIONS:
        raise ValueError(f"unknown plan screening version {version!r}")
    return RULE_VERSIONS[version]


def case_rows(arm: Path, cases: tuple[str, ...] = CASES) -> dict[tuple[str, str], dict[str, Any]]:
    """case·seed 별 원값.  없는 칸은 None 이고 0 으로 채우지 않는다."""
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for case_id in cases:
        for seed in SEEDS:
            case_dir = arm / "cases" / f"seed_{seed}" / case_id
            summary_path = case_dir / "summary.json"
            row: dict[str, Any] = {"case": case_id, "seed": seed, "missing": []}
            if summary_path.is_file():
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                checked = a030.harvest.verify_case(case_dir, SCENARIO[case_id], case_id, int(seed))
                if checked["faults"]:
                    row["missing"].append("case_invalid:" + ",".join(map(str, checked["faults"][:3])))
                proxy = _case_proxy(case_id, summary, std())
                row.update(progress_m=summary.get("projected_progress_m"),
                           survival=proxy["survival_proxy"], tracking=proxy["tracking_proxy"],
                           posture_falls=summary.get("posture_fall_env_count_pessimistic"),
                           fingerprint={key: summary.get(key) for key in a030.harvest.CASE_IDENTITY_FIELDS})
            else:
                row["missing"].append("summary.json")
                row.update(progress_m=None, survival=None, tracking=None, posture_falls=None, fingerprint=None)
            steps = case_dir / "steps.csv"
            if case_id in STAIRS:
                counted = climb.count(steps, climb.STAIR_HEIGHTS[case_id]) if steps.is_file() else None
                if counted is None:
                    row["missing"].append("steps.csv")
                row.update(ge1=None if counted is None else counted["ge1"],
                           ge2=None if counted is None else counted["ge2"])
                reading = stall.case_reading(steps, case_id)
                row["stall_share"] = reading["stall_share"]
                row["first_step_time_median_s"] = reading["first_step_time_median_s"]
                row["arrival_rate"] = reading["arrival_rate"]
                coverage_complete = reading.get("coverage_complete")
                reason = reading.get("reason")
                if reading["stall_share"] is None or coverage_complete is not True:
                    row["missing"].append("stall_share:" + (reason or "coverage_incomplete"))
            rows[(case_id, seed)] = row
    return rows


def _median_delta(base: dict, cand: dict, case_id: str, key: str) -> float | None:
    deltas = []
    for seed in SEEDS:
        b, c = base[(case_id, seed)].get(key), cand[(case_id, seed)].get(key)
        if b is None or c is None:
            return None
        deltas.append(float(c) - float(b))
    return statistics.median(deltas)


def _pooled(rows: dict, case_id: str, key: str) -> int | None:
    values = [rows[(case_id, seed)].get(key) for seed in SEEDS]
    return None if any(v is None for v in values) else sum(int(v) for v in values)


def judge(base: dict, cand: dict, cases: tuple[str, ...] = CASES) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    unreadable = sorted({f"{case_id}:{seed}:{what}"
                         for (case_id, seed), row in cand.items() for what in row["missing"]}
                        | {f"baseline {case_id}:{seed}:{what}"
                           for (case_id, seed), row in base.items() for what in row["missing"]})
    for key in sorted(set(base) & set(cand)):
        if base[key].get("fingerprint") != cand[key].get("fingerprint"):
            unreadable.append(f"{key[0]}:{key[1]}:case_fingerprint_mismatch")
    unreadable = sorted(set(unreadable))

    def add(group: str, name: str, value: Any, ok: bool | None, note: str = "") -> None:
        checks.append({"group": group, "check": name, "value": value, "ok": ok, "note": note})

    strict_climb = []
    for case_id in STAIRS:
        delta = _median_delta(base, cand, case_id, "progress_m")
        add("stairs", f"{case_id} forward distance median delta > 0", delta,
            None if delta is None else delta > 0)
        for metric in ("ge1", "ge2"):
            b, c = _pooled(base, case_id, metric), _pooled(cand, case_id, metric)
            ok = None if b is None or c is None else c >= b
            add("stairs", f"{case_id} pooled {metric} >= baseline", f"{c} vs {b}", ok)
            strict_climb.append(None if b is None or c is None else c > b)
    add("stairs", "at least one climb count strictly up", strict_climb,
        None if any(v is None for v in strict_climb) else any(strict_climb))

    for case_id in STAIRS:
        delta = _median_delta(base, cand, case_id, "stall_share")
        add("stall", f"{case_id} stall share median delta < 0", delta,
            None if delta is None else delta < 0)

    for case_id in cases:
        b, c = _pooled(base, case_id, "posture_falls"), _pooled(cand, case_id, "posture_falls")
        ok = None if b is None or c is None else c <= b
        add("guard", f"{case_id} pooled posture falls <= baseline", f"{c} vs {b}", ok)
        delta = _median_delta(base, cand, case_id, "survival")
        add("guard", f"{case_id} survival median delta >= 0", delta,
            None if delta is None else delta >= 0)
    for case_id in (*ROUGH, *[c for c in cases if c in PUSH_ALL]):
        delta = _median_delta(base, cand, case_id, "tracking")
        add("guard", f"{case_id} tracking proxy median delta >= 0", delta,
            None if delta is None else delta >= 0)

    undecided = [c["check"] for c in checks if c["ok"] is None]
    failed = [c["check"] for c in checks if c["ok"] is False]
    if undecided or unreadable:
        verdict = INCONCLUSIVE
    else:
        verdict = FAIL if failed else PASS
    return {
        "verdict": verdict,
        "cases": list(cases),
        "rule": "upload/plan/GO2_FORWARD_STAIRS_POLICY_20260921.md section 4 (screening design "
                "criteria; not an official threshold and not a significance level)"
                + ("" if tuple(cases) == CASES else
                   "; extended by upload/plan/GO2_POST_A042_PLAN_20260922.md section 5, which adds both "
                   "G6 x-direction push cases to the protection block (post_a042_push_v1)")
                + ("; extended again by upload/plan/GO2_POST_A043_PLAN_20260922.md section 6, which adds "
                   "the two G6 y-direction push cases (post_a043_push4_v1)"
                   if set(PUSH_Y) <= set(cases) else ""),
        "not_claimed": "a PASS is a screening pass only: the full 69 cases, the guard axes, the "
                       "videos and a symmetric independent-seed pair are still required before any "
                       "promotion. fact_rules_v1 is judged separately by "
                       "tools/verify_go2_basic_motion_harvest.py and is not weakened here.",
        "unreadable": unreadable,
        "undecided": undecided,
        "failed": failed,
        "checks": checks,
    }


def screen(candidate: Path, baseline: Path = BASELINE_ARM,
           expected_candidate_identity: dict[str, Any] | None = None,
           expected_baseline_identity: dict[str, Any] | None = None,
           cases: tuple[str, ...] = CASES) -> dict[str, Any]:
    arm = candidate / "evaluation" / "candidate" if (candidate / "evaluation").is_dir() else candidate
    baseline_identity = _identity(baseline)
    identity_errors = [f"candidate:{fault}" for fault in
                       identity_faults(arm, expected_candidate_identity, baseline_identity)]
    identity_errors += [f"baseline:{fault}" for fault in
                        identity_faults(baseline, expected_baseline_identity)]
    try:
        report = judge(case_rows(baseline, cases), case_rows(arm, cases), cases)
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError) as error:
        report = {"verdict": INCONCLUSIVE, "checks": [], "failed": [], "undecided": [],
                  "unreadable": [f"diagnostic_unreadable:{type(error).__name__}:{error}"]}
    report["identity_faults"] = identity_errors
    if identity_errors:
        report["verdict"] = INCONCLUSIVE
    report["candidate"] = str(arm)
    report["baseline"] = str(baseline)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path, help="the run's _keep folder or its evaluation/candidate")
    parser.add_argument("--baseline", type=Path, default=BASELINE_ARM)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--rule-version", choices=sorted(RULE_VERSIONS), default="forward_stairs_v1",
                        help="the spec's preregistered.plan_screening.version")
    args = parser.parse_args(argv)
    report = screen(args.candidate, args.baseline, cases=cases_for(args.rule_version))
    text = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print("SCREENING %s" % report["verdict"])
    for check in report["checks"]:
        mark = {True: "ok  ", False: "FAIL", None: "??  "}[check["ok"]]
        print("  %s %-8s %-52s %s" % (mark, check["group"], check["check"], check["value"]))
    for name in report["unreadable"]:
        print("  missing: %s" % name)
    return 0 if report["verdict"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
