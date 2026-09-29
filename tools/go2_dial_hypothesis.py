#!/usr/bin/env python3
"""탐색 가설 판정 — 사양이 결과 전에 고정한 지표별 문턱으로 지지·미지지·불충분을 읽는다.

왜 따로 있는가.  채택 판정(`tools/verify_go2_basic_motion_harvest.py` 의 fact_rules_v1 + 계획 screening)은
"이 정책을 기준선 대신 쓸 것인가" 를 묻는다.  탐색 회차는 그와 별개로 "이 다이얼의 이 값에서 표적 행동이
나타났는가" 를 묻고, 그 답은 채택 실패와 섞이면 사라진다(2026-09-26 튜닝 정책 개정: 가설 판정과 채택 판정을
분리한다).  이 모듈은 앞의 질문만 답한다.  **채택·승급을 판정하지 않는다.**

문턱은 사양 `preregistered.hypothesis.indicators` 에서만 읽는다.  여기에 숫자를 두지 않는다 — 결과를 본 뒤
판독기를 고쳐 경계를 옮기는 길을 막기 위해서다.

지표 세 종류(계획 upload/plan/GO2_A043_YAW_RIGHT_AND_NEXT_20260926.md §4):
  climb_ge2_pooled      세 seed 합 계단 ≥2단 로봇 수 (tools/go2_climb_count.py, 계단 표와 같은 함수)
  posture_falls_pooled  세 seed 합 자세 낙상 env 수 (평가기 summary.json 의 posture_fall_env_count_*)
  posture_falls_seeds   자세 낙상이 1 이상인 seed 수

판정 이름:
  수치 지표  SUPPORTED / NOT_SUPPORTED / INSUFFICIENT
  비용 지표  PRESENT / ABSENT / INSUFFICIENT
  기록 결손  MISSING (그 지표만 — 다른 지표의 판정을 지우지 않는다)
경계 바로 안쪽의 값은 사양 문턱 그대로 INSUFFICIENT 다.  반증을 피한 것은 지지가 아니다.

이 모듈은 무결성 검증기가 아니다(2026-09-26 외부 검토).  그래서 --harvest 판독은 두 가지를 먼저 본다.
  ① 수확물의 `harvest_verification.json`(채택 검증기 `tools/verify_go2_basic_motion_harvest.py --out` 이 쓴다)이
     같은 회차이고 `combined_verdict.artifact == ARTIFACT_VERIFIED` 이며 `artifact_faults` 가 비었는가.
     아니면 판정 이름 대신 NOT_READ_UNVERIFIED_HARVEST 를 내고 수만 보여 준다 — 잘못된·잘린 수확물에
     확정적인 이름이 붙지 않게 한다.  순서: 채택 검증기 → 이 판독기.
  ② case·seed 마다 로봇이 사양 수(96/3 = 32)만큼 기록됐는가.  모자라면 그 지표만 MISSING 이다.
--stored-arms 는 판독기 자체의 셈을 확인하는 모드라 ①을 보지 않는다(저장 기준선에는 그 파일이 없을 수 있다).

    python -B tools/go2_dial_hypothesis.py G-A048 --harvest workspace/_keep/<keep_dir>
    python -B tools/go2_dial_hypothesis.py G-A048 --stored-arms   # 저장된 수확물로 판독기 자체를 확인
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))

import go2_climb_count as climb  # noqa: E402

SPECS = {"G-A048": QUAD / "config/experiments/G_A048_a033_lin_vel_z_m125.json",
         # 2026-09-27: 분기 B(upload/plan/GO2_NEXT_CANDIDATE_20260927.md §2).  두 지표를 판정하고 15cm 는
         # `recorded` 로 수만 적는다 — 판정 이름을 붙이지 않는다(기반 데이터 S5).
         "G-A049": QUAD / "config/experiments/G_A049_a033_lin_vel_z_m1.json",
         # 2026-09-27: G3 표적(사용자 결정 G-D-G3-FIRST-20260927).  지표는 G-A049 와 같은 두 개, 15cm 는
         # `recorded` — 계단은 채택 보호(g3_guard_margin_v1)에서 판정된다.
         "G-A050": QUAD / "config/experiments/G_A050_a033_lin_vel_z_m1375.json",
         # 2026-09-27: A048 보상 위 ang_vel_xy_l2 -0.06(G-D-A051-ANGVEL-20260927).  지표는 A048 대비 험지 옆걸음
         # 낙상(≤8 지지, ≥16 미지지)과 우회전 비용.  10cm·15cm ≥2단은 `recorded`.
         "G-A051": QUAD / "config/experiments/G_A051_a048_ang_vel_xy_m006.json",
         # 2026-09-28: A048 보상 위 dof_acc_l2 -3.0e-7(G-D-A053-DOFACC-20260928).  지표는 A048 대비 험지 옆걸음
         # 낙상(≤8 지지, ≥16 미지지) 하나.  10cm·15cm ≥2단은 `recorded`.
         "G-A053": QUAD / "config/experiments/G_A053_a048_dof_acc_m3e7.json",
         # 2026-09-29: A043 보상 위 ang_vel_xy_l2 -0.08(G-A055 사전등록).  지표는 A043 대비 험지 옆걸음 낙상
         # (≤12 지지, ≥24 미지지) 하나.  동반 조건 C·우회전·밀침은 tools/go2_g_a055_readout.py 가 읽는다.
         "G-A055": QUAD / "config/experiments/G_A055_a043_ang_vel_xy_m008.json"}
RECORDED = "RECORDED_NOT_JUDGED"
# 판독기 자체 확인용 저장 수확물.  이 다이얼의 세 관측값과, 같은 기준선 위의 다른 다이얼 하나.
STORED_ARMS = (
    ("G-A033", "lin_vel_z_l2 -2.0", "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150"),
    ("G-A044", "lin_vel_z_l2 -1.75", "workspace/_keep/go2_g_a044_a033_lin_vel_z_m175"),
    ("G-A043", "lin_vel_z_l2 -1.5", "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15"),
    ("G-A047", "flat_orientation_l2 -0.5", "workspace/_keep/go2_g_a047_a033_flat_orientation_m05"),
    ("G-A048", "lin_vel_z_l2 -1.25", "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125"),
    ("G-A049", "lin_vel_z_l2 -1.0", "workspace/_keep/go2_g_a049_a033_lin_vel_z_m1"),
)
OUT = QUAD / "reports/evidence/go2_lin_vel_z_hypothesis_20260926"


def load_spec(work_id: str) -> dict:
    return json.loads(SPECS[work_id].read_text(encoding="utf-8"))


def cases_dir(harvest: Path) -> Path:
    return harvest / "evaluation" / "candidate" / "cases"


def posture_falls(summary: Path, robots: int) -> int | None:
    """한 case·seed 의 자세 낙상 env 수.  판정이 모호하거나, 자세를 못 쟀거나, 로봇 수가 모자라면 None."""
    if not summary.is_file():
        return None
    data = json.loads(summary.read_text(encoding="utf-8"))
    if not data.get("posture_measured") or data.get("posture_fall_verdict_ambiguous"):
        return None
    if data.get("posture_envs_observed") != robots:
        return None
    low, high = data.get("posture_fall_env_count_optimistic"), data.get("posture_fall_env_count_pessimistic")
    if low is None or low != high:
        return None
    return int(high)


def per_seed(harvest: Path, indicator: dict) -> dict[str, int | None]:
    values: dict[str, int | None] = {}
    robots = int(indicator["robots"]) // len(indicator["seeds"])
    for seed in indicator["seeds"]:
        case = cases_dir(harvest) / f"seed_{seed}" / indicator["case"]
        if indicator["metric"] == "climb_ge2_pooled":
            result = climb.count(case / "steps.csv", float(indicator["step_height_m"])) \
                if (case / "steps.csv").is_file() else None
            complete = result is not None and int(result["robots"]) == robots
            values[str(seed)] = int(result["ge2"]) if complete else None
        else:
            values[str(seed)] = posture_falls(case / "summary.json", robots)
    return values


def judge(indicator: dict, values: dict[str, int | None]) -> tuple[str, int | None]:
    if any(v is None for v in values.values()) or len(values) != len(indicator["seeds"]):
        return "MISSING", None
    metric = indicator["metric"]
    if metric == "posture_falls_seeds":
        seeds = sum(1 for v in values.values() if v > 0)
        if seeds >= int(indicator["present_if_seeds_at_least"]):
            return "PRESENT", seeds
        if seeds <= int(indicator["absent_if_seeds_at_most"]):
            return "ABSENT", seeds
        return "INSUFFICIENT", seeds
    pooled = sum(values.values())
    if metric == "climb_ge2_pooled":          # 많을수록 지지
        if pooled >= int(indicator["supported_if_at_least"]):
            return "SUPPORTED", pooled
        if pooled <= int(indicator["not_supported_if_at_most"]):
            return "NOT_SUPPORTED", pooled
        return "INSUFFICIENT", pooled
    if metric == "posture_falls_pooled":      # 적을수록 지지
        if pooled <= int(indicator["supported_if_at_most"]):
            return "SUPPORTED", pooled
        if pooled >= int(indicator["not_supported_if_at_least"]):
            return "NOT_SUPPORTED", pooled
        return "INSUFFICIENT", pooled
    raise ValueError(f"unknown metric {metric}")


UNVERIFIED = "NOT_READ_UNVERIFIED_HARVEST"


def harvest_check(spec: dict, harvest: Path) -> tuple[bool, str]:
    """채택 검증기가 이 수확물을 같은 회차의 ARTIFACT_VERIFIED 로 남겼는가."""
    path = harvest / "harvest_verification.json"
    if not path.is_file():
        return False, "harvest_verification.json absent - run tools/verify_go2_basic_motion_harvest.py first"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("work_id") != spec["work_id"]:
        return False, f"harvest_verification.json is for {data.get('work_id')}, not {spec['work_id']}"
    artifact = (data.get("combined_verdict") or {}).get("artifact")
    if artifact != "ARTIFACT_VERIFIED" or data.get("artifact_faults"):
        return False, f"artifact {artifact}, faults {len(data.get('artifact_faults') or [])}"
    return True, "ARTIFACT_VERIFIED"


def read(spec: dict, harvest: Path, require_verified: bool = True) -> dict:
    block = spec["preregistered"]["hypothesis"]
    verified, reason = harvest_check(spec, harvest) if require_verified else (True, "not checked (stored-arms mode)")
    out = {"work_id": spec["work_id"], "harvest": str(harvest), "tier": "INTERNAL_HYPOTHESIS_READOUT",
           "adoption": "not judged here - tools/verify_go2_basic_motion_harvest.py",
           "harvest_check": {"verified": verified, "reason": reason}, "indicators": {}}
    for name, indicator in block["indicators"].items():
        values = per_seed(harvest, indicator)
        verdict, value = judge(indicator, values)
        if not verified:
            verdict = UNVERIFIED
        out["indicators"][name] = {"verdict": verdict, "value": value, "per_seed": values}
    # 기록만 하는 계수기: 판정 이름 대신 RECORDED_NOT_JUDGED.  기록이 모자라면 MISSING, 미검증이면 UNVERIFIED.
    for name, indicator in (block.get("recorded") or {}).items():
        values = per_seed(harvest, indicator)
        complete = all(v is not None for v in values.values())
        verdict = RECORDED if complete else "MISSING"
        if not verified:
            verdict = UNVERIFIED
        out.setdefault("recorded", {})[name] = {"verdict": verdict,
                                                "value": sum(values.values()) if complete else None,
                                                "per_seed": values}
    return out


def stored_arms(spec: dict) -> list[list[str]]:
    rows = [["arm", "change", "indicator", "per_seed", "value", "verdict"]]
    for arm, change, keep in STORED_ARMS:
        result = read(spec, ROOT / keep, require_verified=False)
        for name, item in {**result["indicators"], **result.get("recorded", {})}.items():
            seeds = "/".join("-" if v is None else str(v) for v in item["per_seed"].values())
            rows.append([arm, change, name, seeds, "" if item["value"] is None else str(item["value"]),
                         item["verdict"]])
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("work_id", choices=sorted(SPECS))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--harvest", type=Path)
    group.add_argument("--stored-arms", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    spec = load_spec(args.work_id)
    if args.stored_arms:
        rows = stored_arms(spec)
        OUT.mkdir(parents=True, exist_ok=True)
        # G-A048 의 표 이름은 그대로 둔다(발행 당시 증거).  다른 회차는 회차 이름을 붙여 덮어쓰지 않는다.
        name = "STORED_ARMS.csv" if args.work_id == "G-A048" else f"STORED_ARMS_{args.work_id}.csv"
        with (OUT / name).open("w", encoding="utf-8", newline="\n") as handle:
            csv.writer(handle, lineterminator="\n").writerows(rows)
        for row in rows:
            print(",".join(row))
        return 0
    result = read(spec, args.harvest)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(text)
    everything = {**result["indicators"], **result.get("recorded", {})}
    missing = [n for n, i in everything.items() if i["verdict"] in ("MISSING", UNVERIFIED)]
    if not result["harvest_check"]["verified"]:
        print(f"HARVEST NOT VERIFIED: {result['harvest_check']['reason']} - counts only, no verdict names")
    for name, item in result["indicators"].items():
        print(f"HYPOTHESIS {name}: {item['verdict']} ({item['value']})")
    for name, item in result.get("recorded", {}).items():
        print(f"RECORDED {name}: {item['verdict']} ({item['value']})")
    # exit 1 은 판독 불가(기록 결손 또는 미검증 수확물)일 뿐이다.  미지지는 판정을 한 것이므로 exit 0 이다.
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
