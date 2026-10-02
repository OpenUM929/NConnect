"""Go2 성공 지표 수집 → 보상 한 항 변경에 따른 지표 변화 → 성공 사례 정리 (2026-10-01, 읽기 전용).

사용자 요구(2026-10-01): 성공을 위한 지표를 시나리오 전체에서 모으고, 그 지표가 어떤 보상 변수를 바꿀 때
변하는지 추출하고, 성공한 사례를 정리한다. 새 실행 없이 기존 증거 CSV와 summary.json만 읽는다.

입력(모두 같은 회수물 steps.csv에서 만든 기존 증거)
  go2_state_outcome_20261001/PER_ENV.csv       판정·초기 높이/기울기/속도·추종·계단 ≥2단·모서리 뒤 상승
  go2_state_channel_split_20261001/PER_ENV.csv 판정 채널(종료·높이만·기울기·합집합)
  go2_stairs_tread_height_20261001/PER_ENV.csv 계단 집단(깨끗한 등반 등)·첫 디딤판 위 몸높이
  각 회수물 밀침 summary.json                   recovery.median_recovery_s
지표 정의(시나리오별, 96대 = 평가 seed 3 x 32대; 밀침은 4방향 합 384대)
  success      판정 없음(계단은 ≥2단 + 판정 없음). 내부 자세 게이트 기준이며 영상 확인 아님.
  judged / term / height_only / tilt  판정 수와 채널(계단·험지·우회전만 채널 분리)
  trk          판정 없는 로봇의 추종 RMS 중앙값(우회전·좌회전은 yaw 추종도)
  h / tilt / speed  초기 1~3초 몸높이(스캐너 기준)·기울기(도)·명령 방향 속도 중앙값
  stairs: ge2, tread1_all(첫 디딤판 위 몸높이 중앙값, 첫 디딤판에 들어간 로봇 전부), tread1_ok(그 값 >= 0.30 인 로봇 수),
          rise(모서리 뒤 1.5초 최대 몸통 상승 중앙값)
  push: recovery(복구 시간 중앙값의 평균, s)
보상 쌍: 같은 기준에서 한 항만 다른 서버 run 쌍. 서버 A048 → PC A048(보상 같음)은 '보상 변경 없이 생긴 차이'의 참고값.
"""
from __future__ import annotations

import csv
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "workspace/training/quadruped/reports/evidence"
OUT = EV / "go2_success_indicators_20261001"
KEEP = ROOT / "workspace/_keep"
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "tools"))
from go2_state_outcome import ARMS, SEEDS, STATIONARY  # noqa: E402

ARM_LIST = [a for a in ARMS if a not in STATIONARY]
SCEN = ("stairs_15_down", "stairs_10_down", "rough_lateral", "rough_forward", "combined_yaw_right",
        "combined_yaw_left", "push_all")
PUSH = ("push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y")
PAIRS = [
    ("lin_vel_z_l2", "A033", "A044", -2.0, -1.75), ("lin_vel_z_l2", "A033", "A043", -2.0, -1.5),
    ("lin_vel_z_l2", "A033", "A050", -2.0, -1.375), ("lin_vel_z_l2", "A033", "A048", -2.0, -1.25),
    ("lin_vel_z_l2", "A033", "A049", -2.0, -1.0),
    ("ang_vel_xy_l2", "A033", "A038", -0.05, -0.08), ("ang_vel_xy_l2", "A033", "A041", -0.05, -0.04),
    ("ang_vel_xy_l2", "A043", "A055", -0.05, -0.08),
    ("flat_orientation_l2", "A033", "A047", 0.0, -0.5),
    ("track_lin_vel_xy_exp", "A033", "A042", 1.5, 1.6),
    ("(none) server->PC", "A048", "PC_A048", "", ""),
]
KEYS = ("success", "judged", "term", "height_only", "tilt", "trk", "trk_yaw", "h", "tilt_deg", "speed",
        "ge2", "tread1_all", "tread1_ok", "rise", "recovery")


def rd(p):
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def med(v):
    v = [float(x) for x in v if x not in ("", None)]
    return st.median(v) if v else None


def indicators():
    so = rd(EV / "go2_state_outcome_20261001/PER_ENV.csv")
    ch = {(r["arm"], r["case"], r["seed"], r["env"]): r["channel"] for r in rd(EV / "go2_state_channel_split_20261001/PER_ENV.csv")}
    tr = {(r["arm"], r["case"], r["seed"], r["env"]): r for r in rd(EV / "go2_stairs_tread_height_20261001/PER_ENV.csv")}
    rows = []
    for arm in ARM_LIST:
        for scen in SCEN:
            cases = PUSH if scen == "push_all" else (scen,)
            g = [r for r in so if r["arm"] == arm and r["case"] in cases]
            if not g or (scen == "push_all" and len(g) != 384):
                continue
            key = lambda r: (r["arm"], r["case"], r["seed"], r["env"])  # noqa: E731
            chans = [ch.get(key(r)) for r in g]
            ok = [r for r in g if r["fall"] == "0"]
            out = {"arm": arm, "layer": ARMS[arm][1], "scenario": scen, "robots": len(g),
                   "judged": sum(r["fall"] == "1" for r in g),
                   "trk": med(r["trk_xy_rms"] for r in ok), "trk_yaw": med(r["trk_yaw_rms"] for r in ok),
                   "h": med(r["early_h"] for r in g), "tilt_deg": med(r["early_tilt"] for r in g),
                   "speed": med(r["early_along"] for r in g)}
            if all(c is not None for c in chans):
                out.update(term=chans.count("terminated"), height_only=chans.count("height_only"),
                           tilt=chans.count("tilt_or_both"))
            if scen.startswith("stairs"):
                t = [tr[key(r)] for r in g if key(r) in tr]
                out["success"] = sum(1 for x in t if x["group"] == "clean")
                out["ge2"] = sum(r["ge2"] == "1" for r in g)
                t1 = [float(x["tread1"]) for x in t if x["tread1"] not in ("", None)]
                out["tread1_all"] = st.median(t1) if t1 else None
                out["tread1_ok"] = sum(v >= 0.30 for v in t1)
                out["rise"] = med(r["post_max_rise"] for r in g)
            else:
                out["success"] = len(ok)
            if scen == "push_all":
                rec = []
                for c in PUSH:
                    for s in SEEDS:
                        p = KEEP / ARMS[arm][0] / "evaluation/candidate/cases" / f"seed_{s}" / c / "summary.json"
                        if p.exists():
                            v = json.loads(p.read_text(encoding="utf-8")).get("recovery", {}).get("median_recovery_s")
                            if v is not None:
                                rec.append(v)
                out["recovery"] = st.mean(rec) if rec else None
            rows.append(out)
    return rows


def deltas(ind):
    idx = {(r["arm"], r["scenario"]): r for r in ind}
    out = []
    for var, base, arm, v0, v1 in PAIRS:
        for scen in SCEN:
            b, a = idx.get((base, scen)), idx.get((arm, scen))
            if not b or not a:
                continue
            row = {"variable": var, "base": base, "arm": arm, "from": v0, "to": v1, "scenario": scen}
            for k in KEYS:
                if b.get(k) is not None and a.get(k) is not None:
                    row[f"d_{k}"] = a[k] - b[k]
            out.append(row)
    return out


def write(name, data):
    keys = list(dict.fromkeys(k for d in data for k in d))
    with (OUT / name).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ind = indicators()
    write("INDICATORS.csv", ind)
    write("REWARD_DELTAS.csv", deltas(ind))
    print(len(ind), "indicator rows")


if __name__ == "__main__":
    main()
