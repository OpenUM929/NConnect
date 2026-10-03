#!/usr/bin/env python3
"""PC2 트랙 고정 탐색트리 판독·진행 규칙 (G-A061 예정, 2026-10-04).

설계: workspace/training/quadruped/upload/plan/GO2_TRACK_FIXED_SEARCH_TREE_20261003.md — 적용 순서는
§13(명시적 대체) → §12 → 대체되지 않은 이전 절(Codex §37-2). Codex §37 APPROVE.

이 도구가 하는 일
  1. 노드 대 비교 부모 판독(§12-3 지표, §13-1 도달 후 비정체, §13-2 같은 seed 비교, §12-4 분류 우선순위).
  2. 같은 변수 후보의 적격성·형제 비교(§12-5).
  3. 트리 진행(§12-7 + §13-3): 다음 노드, 변수 종료, 이력 제외 우회, 복구 불가 정지.
값을 고르지 않는다. 노드 목록과 값은 계획서에서 고정됐다. 새 수치 문턱을 만들지 않는다(세 seed 공통 방향만).

    python -B tools/go2_pc2_tree_readout.py read --node <key> --point <harvest> --parent <harvest> [--out DIR]
    python -B tools/go2_pc2_tree_readout.py next --tree-state <json>
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_climb_count as climb  # noqa: E402
import go2_g_a057_sweep_compare as cmp  # noqa: E402
import go2_pc2_point_readout as pr  # noqa: E402
from candidate_suite_checks import reward_weights  # noqa: E402

SEEDS = pr.SEEDS
ROBOTS = pr.ROBOTS
EXTRA_TERMS = ("dof_torques_l2", "dof_acc_l2")
TREE_TERMS = pr.REWARD_TERMS + EXTRA_TERMS

# 트리(§12-7·§13). 변수 순서와 노드 값은 계획서에서 고정. (변수, [(노드 key, 값), ...])
TREE: tuple[tuple[str, tuple[tuple[str, float], ...]], ...] = (
    ("dof_torques_l2", (("n3_dof_torques_l2_m1e_4", -1e-4), ("n4_dof_torques_l2_m5e_5", -5e-5))),
    ("dof_acc_l2", (("n5_dof_acc_l2_m1p25e_7", -1.25e-7), ("n6_dof_acc_l2_m6p25e_8", -6.25e-8))),
)
P0_REWARDS = {**pr.A048_REWARDS, "dof_torques_l2": -2e-4, "dof_acc_l2": -2.5e-7}

CLASSES = ("INSUFFICIENT", "WORSENED", "TRADEOFF", "IMPROVED", "NO_CONSISTENT_CHANGE")


# ---------- 지표 값 (seed 하나) ----------
def summary(h: Path, seed: str, case: str) -> dict | None:
    return pr.load_json(pr.cases(h) / f"seed_{seed}" / case / "summary.json")


def progress_ratio(s: dict | None) -> float | None:
    """obstacle_completion = min(1, projected_progress_m / (0.5 × duration)) — 명령 대비 진행 비율(§12-3 정정).
    출처 workspace/training/quadruped/go2_fixed_eval_report.py:35-39. 생존 완주가 아니다."""
    if not s:
        return None
    steps, dt, prog = pr.fnum(s.get("steps")), pr.fnum(s.get("step_dt")), pr.fnum(s.get("projected_progress_m"))
    if steps is None or dt is None or prog is None or steps * dt <= 0:
        return None
    return min(1.0, prog / (0.5 * steps * dt))


def climb_counts(h: Path, seed: str, case: str, height: float) -> dict | None:
    p = pr.steps_ok(h, seed, case)
    if p is None:
        return None
    r = climb.count(p, height)
    return r if r and int(r["robots"]) == ROBOTS else None


def nonstall(h: Path, seed: str, case: str, height: float) -> dict | None:
    """§13-1: 32대 기준 '≥2단 도달 후 정체하지 않은 개체 수'. 정체 수·조건부 정체율은 기술 지표(투표 안 함)."""
    pr_ = pr.stairs_post_reach(h, seed, case, height)
    if pr_ is None:
        return None
    reached, stalled = pr_["reached_ge2"], pr_["stalled_after_reach"]
    return {"value": reached - stalled, "reached_ge2": reached, "stalled_after_reach": stalled,
            "conditional_stall_rate": (stalled / reached) if reached else "NOT_APPLICABLE"}


def motion_pair(h: Path, seed: str, case: str) -> dict | None:
    m = pr.command_motion(h, seed, case)
    return None if m is None else {"abs_error": m["abs_error"], "rmse": m["tracking_xy_rmse"]}


def worst_case(parent: Path, axis_id: str) -> str | None:
    w = cmp.axis_scores(parent).get(axis_id, {})
    s = w.get("worst") if isinstance(w, dict) else None
    return s.split(":")[0] if s else None


def indicators(parent: Path) -> list[dict]:
    """(이름, 역할, 좋은 방향, 값 함수). 값 함수는 (harvest, seed) → 수 또는 dict(motion)."""
    out = []

    def add(name, role, good, fn):
        out.append({"name": name, "role": role, "good": good, "fn": fn})

    def sf(case, field):
        return lambda h, s: pr.fnum((summary(h, s, case) or {}).get(field))

    # 표적 T-G3
    add("T_G3_rough_lateral_falls", "target", "down", lambda h, s: pr.falls(h, s, "rough_lateral"))
    add("T_G3_rough_lateral_motion", "target", "motion", lambda h, s: motion_pair(h, s, "rough_lateral"))
    # 표적 T-G5 (15cm)
    add("T_G5_stairs15_ge1", "target", "up",
        lambda h, s: (lambda c: None if c is None else int(c["ge1"]))(climb_counts(h, s, "stairs_15_down", 0.15)))
    add("T_G5_stairs15_ge2", "target", "up",
        lambda h, s: (lambda c: None if c is None else int(c["ge2"]))(climb_counts(h, s, "stairs_15_down", 0.15)))
    add("T_G5_stairs15_nonstall_after_ge2", "target", "up",
        lambda h, s: (lambda n: None if n is None else n["value"])(nonstall(h, s, "stairs_15_down", 0.15)))
    add("T_G5_stairs15_progress_ratio", "target", "up", lambda h, s: progress_ratio(summary(h, s, "stairs_15_down")))
    add("T_G5_stairs15_survival", "target", "up", sf("stairs_15_down", "survival_proxy"))
    # 보호 S
    add("S_stairs10_ge2", "protect", "up",
        lambda h, s: (lambda c: None if c is None else int(c["ge2"]))(climb_counts(h, s, "stairs_10_down", 0.10)))
    add("S_stairs10_survival", "protect", "up", sf("stairs_10_down", "survival_proxy"))
    add("S_stairs10_progress_ratio", "protect", "up", lambda h, s: progress_ratio(summary(h, s, "stairs_10_down")))
    add("S_yaw_right_falls", "protect", "down", lambda h, s: pr.falls(h, s, "combined_yaw_right"))
    add("S_yaw_right_survival", "protect", "up", sf("combined_yaw_right", "survival_proxy"))
    add("S_yaw_right_yaw_rmse", "protect", "down", sf("combined_yaw_right", "tracking_yaw_rmse"))
    add("S_yaw_right_xy_rmse", "protect", "down", sf("combined_yaw_right", "tracking_xy_rmse"))
    for d in ("pos_x", "neg_x", "pos_y", "neg_y"):
        c = f"push_{d}"
        add(f"S_{c}_falls", "protect", "down", lambda h, s, c=c: pr.falls(h, s, c))
        add(f"S_{c}_survival", "protect", "up", sf(c, "survival_proxy"))
        add(f"S_{c}_post_push_rmse", "protect", "down", sf(c, "post_push_tracking_xy_rmse"))
        add(f"S_{c}_recovery_upright", "protect", "up",
            lambda h, s, c=c: pr.fnum(((summary(h, s, c) or {}).get("recovery") or {}).get("recovery_rate_upright")))
    add("S_rough_forward_falls", "protect", "down", lambda h, s: pr.falls(h, s, "rough_forward"))
    add("S_rough_forward_motion", "protect", "motion", lambda h, s: motion_pair(h, s, "rough_forward"))
    add("S_forward_nominal_cmd_error", "protect", "down",
        lambda h, s: (lambda m: None if m is None else m["abs_error"])(motion_pair(h, s, "forward_nominal")))
    g4 = worst_case(parent, "G4")
    if g4:
        add(f"S_G4_{g4}_survival", "protect", "up", sf(g4, "survival_proxy"))
        add(f"S_G4_{g4}_xy_rmse", "protect", "down", sf(g4, "tracking_xy_rmse"))
    add("S_G7_dr_survival", "protect", "up", lambda h, s: pr.fnum((summary(h, s, f"dr_seed_{s}") or {}).get("survival_proxy")))
    add("S_G7_dr_xy_rmse", "protect", "down", lambda h, s: pr.fnum((summary(h, s, f"dr_seed_{s}") or {}).get("tracking_xy_rmse")))
    return out


# ---------- 같은 seed 비교 (§13-2) ----------
def seed_dir(good: str, cand, ref) -> str | None:
    """seed 하나: 'better' | 'worse' | 'same' | None(결측). 크기 문턱 없음."""
    if cand is None or ref is None:
        return None
    if good == "motion":  # 오차·RMSE 중 하나라도 커지면 악화, 둘 다 작아지면 개선(판독기 motion() 규칙)
        if cand["abs_error"] > ref["abs_error"] or cand["rmse"] > ref["rmse"]:
            return "worse"
        if cand["abs_error"] < ref["abs_error"] and cand["rmse"] < ref["rmse"]:
            return "better"
        return "same"
    if cand == ref:
        return "same"
    up = cand > ref
    return "better" if (up and good == "up") or (not up and good == "down") else "worse"


def compare_indicator(cand_vals: dict, ref_vals: dict, good: str) -> dict:
    dirs = {s: seed_dir(good, cand_vals.get(s), ref_vals.get(s)) for s in SEEDS}
    if any(d is None for d in dirs.values()):
        label = "MISSING"
    elif all(d == "better" for d in dirs.values()):
        label = "COMMON_IMPROVEMENT"
    elif all(d == "worse" for d in dirs.values()):
        label = "COMMON_LOSS"
    else:
        label = "NO_COMMON_DIRECTION"
    return {"label": label, "seed_dirs": dirs, "worse_seeds": [s for s, d in dirs.items() if d == "worse"]}


# ---------- 분류 우선순위 (§12-4, 순수 함수) ----------
def classify(insufficient: list[str], gate: str, results: list[dict]) -> dict:
    """results: [{"name","role","label","worse_seeds"}]. 위에서 먼저 걸리는 것이 판정이다."""
    if insufficient or any(r["label"] == "MISSING" for r in results):
        miss = [r["name"] for r in results if r["label"] == "MISSING"]
        return {"class": "INSUFFICIENT", "why": insufficient + ([f"지표 결측 {miss}"] if miss else [])}
    if gate == "STATIONARY":
        return {"class": "WORSENED", "why": ["moving gate STATIONARY(표적 개선보다 우선)"]}
    if gate != "MOVING":
        return {"class": "INSUFFICIENT", "why": [f"moving gate {gate}"]}
    imp = [r["name"] for r in results if r["role"] == "target" and r["label"] == "COMMON_IMPROVEMENT"]
    loss = [r["name"] for r in results if r["label"] == "COMMON_LOSS"]
    partial = {r["name"]: r["worse_seeds"] for r in results if r["label"] != "COMMON_LOSS" and r["worse_seeds"]}
    base = {"target_improvements": imp, "common_losses": loss, "partial_seed_losses": partial}
    if imp and loss:
        return {"class": "TRADEOFF", **base}
    if loss:
        return {"class": "WORSENED", **base}
    if imp:
        return {"class": "IMPROVED", **base}
    return {"class": "NO_CONSISTENT_CHANGE", **base,
            "note": "동등성·무효과 증명이 아니다. 세 seed 방향이 엇갈린 혼합도 여기에 든다."}


# ---------- 상태 (보상 snapshot: 부모와 의도한 한 항만 다름) ----------
def rewards_all(h: Path) -> dict | None:
    p = h / "training" / "env.yaml"
    if not p.is_file():
        return None
    w = reward_weights(p.read_text(encoding="utf-8"))
    return {k: w.get(k) for k in TREE_TERMS}


def snapshot_problem(point: Path, parent: Path, changes: dict[str, float]) -> str | None:
    """노드 보상이 비교 부모와 changes 의 항만 다르고 그 값이어야 한다(P0 누적 판독은 여러 항)."""
    a, b = rewards_all(point), rewards_all(parent)
    if a is None or b is None:
        return "training/env.yaml 없음"
    if any(v is None for v in (*a.values(), *b.values())):
        return f"보상 항 결측 point={a} parent={b}"
    diff = sorted(k for k in TREE_TERMS if not math.isclose(a[k], b[k], rel_tol=1e-9, abs_tol=0.0))
    want = sorted(changes)
    if diff != want or any(not math.isclose(a[k], v, rel_tol=1e-9, abs_tol=0.0) for k, v in changes.items()):
        return f"MISMATCH diff={diff} want={want}"
    return None


def read(node: str, point: Path, parent: Path, changes: dict[str, float], parent_key: str) -> dict:
    """노드(또는 형제) 대 비교 부모 판독. parent 는 직접 부모·형제·P0 중 하나(§13-2)."""
    st_point = pr.state(point, node, None, None)
    st_parent = pr.state(parent, parent_key, None, None)
    insufficient = [g for g in st_point["gaps"] if not g.startswith("reward snapshot")]
    insufficient += [f"parent: {g}" for g in st_parent["gaps"] if not g.startswith("reward snapshot")]
    why = snapshot_problem(point, parent, changes)
    if why:
        insufficient.append(f"reward snapshot: {why}")
    comp = pr.comparison(point, parent)
    if comp["label"] != "OK":
        insufficient.append(f"comparison: {comp['problems']}")
    gate = pr.moving(point)
    results, values = [], {}
    for ind in indicators(parent):
        cv = {s: ind["fn"](point, s) for s in SEEDS}
        rv = {s: ind["fn"](parent, s) for s in SEEDS}
        c = compare_indicator(cv, rv, ind["good"])
        results.append({"name": ind["name"], "role": ind["role"], **c})
        values[ind["name"]] = {"point": cv, "parent": rv}
    descriptive = {s: {"point": nonstall(point, s, "stairs_15_down", 0.15),
                       "parent": nonstall(parent, s, "stairs_15_down", 0.15)} for s in SEEDS}
    verdict = classify(insufficient, gate, results)
    return {"node": node, "point": str(point), "parent": str(parent), "parent_key": parent_key, "changes": changes,
            "moving_gate": gate, "indicators": results, "values": values,
            "descriptive_stairs15_post_reach": descriptive, "verdict": verdict,
            "limits": "평가 seed 세 개 공통 방향 판정이며 독립 학습 재현·통계적 유의성·채택 증명이 아니다(§37-2)."}


# ---------- 상태 값 (§39-R2: 입구에서 enum 검사) ----------
PERFORMANCE = ("IMPROVED", "NO_CONSISTENT_CHANGE", "TRADEOFF", "WORSENED")  # 완료된 성능 분류
ERRORS = ("INSUFFICIENT", "INSUFFICIENT_UNRECOVERABLE")                    # 실행·판독 오류(복구 대상 / 복구 불가)
NODE_STATUSES = ("PENDING", "EXCLUDED_HISTORY") + PERFORMANCE + ERRORS
SIBLING_STATUSES = PERFORMANCE + ERRORS


class TreeStateError(ValueError):
    """미지원 key·상태·자료형. 다음 학습(RUN)이나 패키지 빌드로 이어지지 않는다."""


def validate_state(state) -> tuple[dict, dict]:
    if not isinstance(state, dict) or set(state) - {"nodes", "siblings"}:
        raise TreeStateError(f"tree state 는 nodes·siblings 만 갖는 dict 여야 한다: {state!r}")
    nodes, sibs = state.get("nodes", {}), state.get("siblings", {})
    if not isinstance(nodes, dict) or not isinstance(sibs, dict):
        raise TreeStateError("nodes·siblings 는 dict 여야 한다")
    keys = {k for _, pts in TREE for k, _ in pts}
    variables = {v for v, _ in TREE}
    for k, v in nodes.items():
        if k not in keys:
            raise TreeStateError(f"알 수 없는 노드 key {k!r}")
        if not isinstance(v, str) or v not in NODE_STATUSES:
            raise TreeStateError(f"노드 {k} 상태 {v!r} 는 지원하지 않는다 {NODE_STATUSES}")
    for k, v in sibs.items():
        if k not in variables:
            raise TreeStateError(f"알 수 없는 형제 변수 {k!r}")
        if not isinstance(v, str) or v not in SIBLING_STATUSES:
            raise TreeStateError(f"형제 {k} 상태 {v!r} 는 지원하지 않는다 {SIBLING_STATUSES}")
    return nodes, sibs


# ---------- 적격·형제 (§12-5, 순수 함수) ----------
def select_winner(parent_classes: dict[str, str | None], order: list[str], sibling_class: str | None) -> dict:
    """parent_classes: 노드 → 직접 부모 대비 분류(이력 제외는 None). order: [작은 값 노드, 큰 값 노드].
    sibling_class: 큰 값 노드를 작은 값 노드 대비 판독한 분류(둘 다 적격일 때만 쓴다).
    완료된 성능 분류일 때만 승자를 정한다(§39-R1). 형제 판독 오류는 승자·다음 학습 없이 복구/정지 상태를 낸다."""
    for n, c in parent_classes.items():
        if c is not None and c not in PERFORMANCE:
            raise TreeStateError(f"{n}: 성능 분류가 아닌 {c!r} 로 승자를 정할 수 없다")
    eligible = [n for n in order if parent_classes.get(n) == "IMPROVED"]
    if not eligible:
        return {"winner": None, "why": "적격 후보 없음 — 부모 유지"}
    if len(eligible) == 1:
        return {"winner": eligible[0], "why": "적격 후보 하나"}
    if sibling_class is None:
        return {"winner": None, "pending": "SIBLING_READ", "why": "두 후보 적격 — 형제 판독 필요(학습 아님)"}
    if sibling_class == "INSUFFICIENT":
        return {"winner": None, "pending": "RECOVER_SIBLING_READ",
                "why": "형제 판독 결측 — 기존 두 수확물로 판독만 복구(새 학습 아님)"}
    if sibling_class == "INSUFFICIENT_UNRECOVERABLE":
        return {"winner": None, "pending": "STOP", "why": "형제 판독 복구 불가 — 정지·보고(§13-3)"}
    if sibling_class not in PERFORMANCE:
        raise TreeStateError(f"형제 분류 {sibling_class!r} 는 지원하지 않는다")
    return {"winner": eligible[1] if sibling_class == "IMPROVED" else eligible[0],
            "why": f"형제 판독 {sibling_class}"}


# ---------- 트리 진행 (§12-7 + §13-3, 순수 함수) ----------
def _error_step(key: str, status: str, parent: dict) -> dict | None:
    if status == "INSUFFICIENT_UNRECOVERABLE":
        return {"action": "STOP", "node": key, "parent_changes": parent, "why": "복구 불가 — 새 학습 없이 정지·보고(§13-3)"}
    if status == "INSUFFICIENT":
        return {"action": "RECOVER_EVAL_ONLY", "node": key, "parent_changes": parent,
                "why": "학습 후 수집 실패 — checkpoint 보존, 재학습 없이 평가·회수만 복구"}
    return None


def next_step(state: dict) -> dict:
    """state: {"nodes": {key: status}, "siblings": {variable: class}}. 미지원 값은 TreeStateError(§39-R2).
    반환 action: RUN / RECOVER_EVAL_ONLY / SIBLING_READ / RECOVER_SIBLING_READ / STOP / END,
    parent_changes(현재 부모에 누적된 승자). RUN 만 새 학습이다."""
    nodes, sibs = validate_state(state)
    parent: dict[str, float] = {}
    for var, pts in TREE:
        (k1, v1), (k2, v2) = pts
        s1 = nodes.get(k1, "PENDING")
        err = _error_step(k1, s1, parent)
        if err:
            return err
        if s1 == "PENDING":
            if nodes.get(k2, "EXCLUDED_HISTORY") != "EXCLUDED_HISTORY" or var in sibs:
                raise TreeStateError(f"{k1} 미실행인데 {k2}·형제 결과가 있다(미리 기록할 수 있는 것은 이력 제외뿐)")
            return {"action": "RUN", "node": k1, "variable": var, "value": v1, "parent_changes": dict(parent)}
        if s1 in ("EXCLUDED_HISTORY", "TRADEOFF", "WORSENED"):
            if nodes.get(k2, "EXCLUDED_HISTORY") != "EXCLUDED_HISTORY" or var in sibs:
                raise TreeStateError(f"{k1}={s1} 이면 {k2} 를 열지 않는다 — 상태가 모순이다")
            continue  # 변수 종료, 의존 자식 미실행, 부모 유지
        if s1 not in ("IMPROVED", "NO_CONSISTENT_CHANGE"):  # validate_state 뒤에는 도달하지 않는다
            raise TreeStateError(f"{k1} 상태 {s1!r}")
        s2 = nodes.get(k2, "PENDING")
        err = _error_step(k2, s2, parent)
        if err:
            return err
        if s2 == "PENDING":
            if var in sibs:
                raise TreeStateError(f"{k2} 미실행인데 형제 상태가 있다")
            return {"action": "RUN", "node": k2, "variable": var, "value": v2, "parent_changes": dict(parent)}
        w = select_winner({k1: s1, k2: None if s2 == "EXCLUDED_HISTORY" else s2}, [k1, k2], sibs.get(var))
        pending = w.get("pending")
        if pending == "STOP":
            return {"action": "STOP", "variable": var, "parent_changes": parent, "why": w["why"]}
        if pending:
            return {"action": pending, "variable": var, "nodes": [k1, k2], "parent_changes": parent, "why": w["why"]}
        if w["winner"]:
            parent[var] = dict(pts)[w["winner"]]
    return {"action": "END", "parent_changes": parent,
            "why": "트리 종료 — 최종 부모와 P0 대비 누적 판독을 보고하고, X1·X2 해제 여부를 사용자 결정 사항으로 적는다"}


def to_md(r: dict) -> str:
    v = r["verdict"]
    L = [f"# PC2 탐색트리 판독 — {r['node']}", "", f"- 노드: `{r['point']}`",
         f"- 비교 부모({r['parent_key']}): `{r['parent']}`", f"- 비교 부모 대비 변경: {r['changes']}", f"- 정지 판정: {r['moving_gate']}",
         f"- **분류: {v['class']}**"]
    for k in ("why", "target_improvements", "common_losses", "partial_seed_losses", "note"):
        if v.get(k):
            L.append(f"  - {k}: {v[k]}")
    L += ["", "| 지표 | 역할 | 판정 | seed별 방향 | 부모 → 노드 |", "|---|---|---|---|---|"]
    for ind in r["indicators"]:
        vals = r["values"][ind["name"]]
        pv = "; ".join(f"{s}: {vals['parent'][s]}→{vals['point'][s]}" for s in SEEDS)
        L.append(f"| {ind['name']} | {ind['role']} | {ind['label']} | {ind['seed_dirs']} | {pv} |")
    L += ["", "도달 후 정체(기술 지표, 투표 안 함):"]
    for s, d in r["descriptive_stairs15_post_reach"].items():
        L.append(f"- seed {s}: 부모 {d['parent']} / 노드 {d['point']}")
    L += ["", r["limits"]]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    keys = {k: (var, v) for var, pts in TREE for k, v in pts}
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read")
    r.add_argument("--node", required=True, choices=sorted(keys))
    r.add_argument("--point", required=True, type=Path)
    r.add_argument("--parent", required=True, type=Path, help="비교 부모 수확물(직접 부모·형제·P0)")
    r.add_argument("--parent-key", default=pr.B1_KEY)
    r.add_argument("--sibling", action="store_true", help="형제 비교: 부모 자리에 작은 값 노드, 변경은 같은 항")
    r.add_argument("--cumulative", help="P0 누적 판독: 부모 자리에 P0, 'term=value,...' 로 누적 변경 전부")
    r.add_argument("--out", type=Path, default=pr.QUAD / "reports/evidence/go2_pc2_tree_readout")
    n = sub.add_parser("next")
    n.add_argument("--tree-state", required=True, type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "next":
        try:
            out = next_step(json.loads(a.tree_state.read_text(encoding="utf-8")))
        except TreeStateError as err:
            print(f"[TREE_STATE_ERROR] {err}", file=sys.stderr)
            return 2
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    var, val = keys[a.node]
    changes = {var: val}
    if a.cumulative:
        changes = {k: float(v) for k, v in (kv.split("=", 1) for kv in a.cumulative.split(","))}
    res = read(a.node, a.point, a.parent, changes, a.parent_key)
    a.out.mkdir(parents=True, exist_ok=True)
    stem = a.node + ("__vs_sibling" if a.sibling else "") + ("__vs_P0" if a.cumulative else "")
    (a.out / f"{stem}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    (a.out / f"{stem}.md").write_text(to_md(res), encoding="utf-8")
    print(f"{a.node}: {res['verdict']['class']} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
