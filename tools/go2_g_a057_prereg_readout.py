#!/usr/bin/env python3
"""G-A057 사전등록 판독 — config/experiments/G_A057_preregistration.json 만 읽고 판정한다 (2026-09-29).

문턱은 JSON 에 있다.  여기에 숫자를 두지 않는다(결과를 본 뒤 판독기를 고쳐 경계를 옮기는 길을 막는다).
실행 상태와 평가 판정을 섞지 않는다.
  run_state   COMPLETE           RESULT_STATUS FULL / FULL_69_COMPLETE
              UNREADABLE_RUN     그 외(회수 실패·안전 중단·실행 오류) — 지표를 판정하지 않는다
  지표        SUPPORTED / NOT_SUPPORTED / INSUFFICIENT / MISSING
  보호        WORSE_ALL_SEEDS(3 seed 일치 악화) / NOT_CONSISTENT / MISSING — 기록, 판정 이름 아님
  후보 제외   EXCLUDED_STATIONARY / EXCLUDED_NO_TARGET_SUPPORT / KEPT_FOR_REVIEW (평가 후 판정, 실행 중단 아님)

    python -B tools/go2_g_a057_prereg_readout.py <row_key> --harvest workspace/_keep/go2_g_a057_<row_key>
    python -B tools/go2_g_a057_prereg_readout.py --all        # 회수된 행 전부 → evidence/go2_g_a057_prereg_readout/
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
import go2_dial_hypothesis as dial  # noqa: E402

PREREG = QUAD / "config/experiments/G_A057_preregistration.json"
CHECKS = QUAD / "candidate_suite_checks.py"
KEEP = ROOT / "workspace/_keep"
OUT = QUAD / "reports/evidence/go2_g_a057_prereg_readout"


def load() -> dict:
    return json.loads(PREREG.read_text(encoding="utf-8"))


def run_state(harvest: Path) -> tuple[str, str]:
    p = harvest / "RESULT_STATUS.txt"
    if not p.is_file():
        return "UNREADABLE_RUN", "RESULT_STATUS.txt absent"
    lines = set(p.read_text(encoding="utf-8").split())
    if "RESULT_STATE=FULL" in lines and "COLLECTION_STATUS=FULL_69_COMPLETE" in lines:
        return "COMPLETE", "FULL / FULL_69_COMPLETE"
    return "UNREADABLE_RUN", "RESULT_STATUS is not FULL / FULL_69_COMPLETE"


def values(harvest: Path, ind: dict) -> dict[str, float | int | None]:
    if ind["kind"] == "count":
        return dial.per_seed(harvest, ind)
    out = {}
    for s in ind["seeds"]:
        p = dial.cases_dir(harvest) / f"seed_{s}" / ind["case"] / "summary.json"
        out[str(s)] = json.loads(p.read_text(encoding="utf-8")).get(ind["field"]) if p.is_file() else None
    return out


def judge_count(ind: dict, vals: dict) -> tuple[str, int | None]:
    if any(v is None for v in vals.values()):
        return "MISSING", None
    pooled = sum(vals.values())
    if ind["direction"] == "down":
        if pooled <= ind["supported_if_at_most"]:
            return "SUPPORTED", pooled
        if pooled >= ind["not_supported_if_at_least"]:
            return "NOT_SUPPORTED", pooled
    else:
        if pooled >= ind["supported_if_at_least"]:
            return "SUPPORTED", pooled
        if pooled <= ind["not_supported_if_at_most"]:
            return "NOT_SUPPORTED", pooled
    return "INSUFFICIENT", pooled


def judge_direction(ind: dict, vals: dict) -> tuple[str, int | None]:
    if any(v is None for v in vals.values()):
        return "MISSING", None
    sign = 1 if ind["direction"] == "up" else -1
    moved = [sign * (vals[s] - ind["a048_per_seed"][s]) for s in vals]
    pred = sum(1 for m in moved if m > 0)
    if pred == len(moved):
        return "SUPPORTED", pred
    if pred == 0:
        return "NOT_SUPPORTED", pred
    return "INSUFFICIENT", pred


def judge(ind: dict, vals: dict) -> tuple[str, int | None]:
    return judge_count(ind, vals) if ind["kind"] == "count" else judge_direction(ind, vals)


def protection_state(ind: dict, vals: dict) -> str:
    """보호 항목: 세 seed 모두 A048 같은 seed 보다 나쁜 쪽이면 WORSE_ALL_SEEDS.  판정 이름이 아니다."""
    if any(v is None for v in vals.values()):
        return "MISSING"
    sign = 1 if ind["direction"] == "up" else -1  # 보호 항목의 direction 은 '나빠지는 쪽'
    worse = [sign * (vals[s] - ind["a048_per_seed"][s]) > 0 for s in vals]
    return "WORSE_ALL_SEEDS" if all(worse) else "NOT_CONSISTENT"


def moving(harvest: Path, gate: dict) -> str:
    p = dial.cases_dir(harvest) / f"seed_{gate['seed']}" / gate["case"] / "summary.json"
    if not p.is_file():
        return "MISSING"
    rc = subprocess.run([sys.executable, "-B", str(CHECKS), "moving", str(p)], capture_output=True).returncode
    return {0: "MOVING", 1: "STATIONARY"}.get(rc, "MISSING")


def read(key: str, harvest: Path, pre: dict | None = None) -> dict:
    pre = pre or load()
    row = pre["rows"][key]
    state, why = run_state(harvest)
    out = {"work_id": "G-A057", "row": key, "harvest": str(harvest), "tier": "INTERNAL_HYPOTHESIS_READOUT",
           "adoption": "not judged — G-A057 is sweep data only", "run_state": state, "run_state_reason": why,
           "change": row["change"], "targets": {}, "protection": {}}
    if state != "COMPLETE":
        out["exclusion"] = "NOT_JUDGED_UNREADABLE_RUN"
        return out
    for name, ind in row["targets"].items():
        vals = values(harvest, ind)
        verdict, value = judge(ind, vals)
        out["targets"][name] = {"verdict": verdict, "value": value, "per_seed": vals,
                                "a048_per_seed": ind["a048_per_seed"], "cost": name.endswith(("_cost", "_risk"))}
    for name, ind in pre["protection"].items():
        if ind["kind"] == "moving":
            out["protection"][name] = {"state": moving(harvest, ind)}
        elif ind["kind"] in ("count", "seed_direction"):
            vals = values(harvest, ind)
            out["protection"][name] = {"state": protection_state(ind, vals), "per_seed": vals,
                                       "a048_per_seed": ind["a048_per_seed"]}
    improve = [t for t in out["targets"].values() if not t["cost"]]
    if out["protection"]["moving_gate"]["state"] == "STATIONARY":
        out["exclusion"] = "EXCLUDED_STATIONARY"
    elif improve and all(t["verdict"] == "NOT_SUPPORTED" for t in improve):
        out["exclusion"] = "EXCLUDED_NO_TARGET_SUPPORT"
    else:
        out["exclusion"] = "KEPT_FOR_REVIEW"
    return out


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("key", nargs="?")
    ap.add_argument("--harvest")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    pre = load()
    if a.all:
        OUT.mkdir(parents=True, exist_ok=True)
        got = {}
        for key in pre["rows"]:
            h = KEEP / f"go2_g_a057_{key}"
            got[key] = read(key, h, pre) if h.is_dir() else {"row": key, "run_state": "NOT_RECOVERED"}
        (OUT / "PREREG_READOUT.json").write_text(json.dumps(got, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: v.get("exclusion", v["run_state"]) for k, v in got.items()}, ensure_ascii=False, indent=1))
        return 0
    if not a.key or not a.harvest:
        ap.error("row key and --harvest, or --all")
    print(json.dumps(read(a.key, ROOT / a.harvest, pre), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
