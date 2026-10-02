"""성공을 가르는 로봇 상태 — 분별력(AUC) 기준으로 다시 고른 종목별 표 (2026-10-01, 읽기 전용).

이전 표(GO2_SUCCESS_STATE_TABLES)의 결함을 고친다.
  - 성공/실패 범위를 정책을 섞어 10~90분위로만 보여 겹치는 상태까지 목표처럼 보였다.
  - 밀침 실패 범위에 정지 정책(PC track 1.2)이 섞였고, 밀침을 이벤트 단위로 셌다.
방법
  - 로봇 단위. 정지 정책 PC_track12 는 모든 계산에서 뺀다. 밀침은 4방향 case 를 로봇 단위(그 case 에서 판정이 났는가)로 센다.
  - 분별력 AUC = 무작위로 고른 성공 로봇의 값이 실패 로봇보다 클 확률(같으면 1/2). 0.5 = 가르지 못함.
    정책을 섞은 AUC 와, 성공·실패가 각 5대 이상인 정책 안 AUC(정책별)를 함께 본다.
  - 가르는 상태 = 섞은 AUC 가 0.7 이상 또는 0.3 이하이고, 정책 안 AUC 의 방향(0.5 기준 위/아래)이 그 정책들의 2/3 이상에서 같다.
    정책 안 비교가 가능한 정책이 없으면 '정책 안 미확인'으로 따로 적는다.
  - 경계값 = 섞은 자료에서 (성공 중 경계 안쪽 비율 - 실패 중 경계 안쪽 비율)이 가장 큰 값. 그때의 두 비율을 함께 적는다.
  - 누수 표시: 판정 직전까지의 구간을 쓰는 값(출렁임·기울기 90분위·수직 속도)은 넘어지는 과정이 섞일 수 있다 →
    같은 의미의 초기 1~3 s 값(early_*)을 함께 본다. 계단 모서리 값은 과정 지표(성공 동작 자체)다.
    계단 모서리 값은 판정 전에 모서리 구간(d -0.3~0.3)을 끝까지 지난 로봇(edge_full=1)만 쓴다. 판정 시점에서 잘린 값은
    실패 로봇의 최댓값을 낮춰 성공·실패 차이를 부풀린다(15cm 실패 900대 중 845대가 잘림, 2026-10-01 확인).
입력: evidence/go2_robot_state_profile_20261001/PER_ENV.csv, evidence/go2_state_outcome_20261001/PER_ENV.csv·PER_PUSH_EVENT.csv,
      evidence/go2_foot_body_state_diag_20261001/PER_ENV.csv(A048·A043 진단 재생, 정책 안 비교만),
      evidence/go2_series_identity_20261001/SERIES_IDENTITY.csv(추세 비교가 보상 한 항 차이인지).
출력: evidence/go2_success_discrimination_20261001/DISCRIMINATION.csv, reports/GO2_SUCCESS_STATE_TABLES_20261001.md(덮어씀)
"""
from __future__ import annotations

import csv
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "workspace/training/quadruped/reports/evidence"
OUT = EV / "go2_success_discrimination_20261001"
REPORT = ROOT / "workspace/training/quadruped/reports/GO2_SUCCESS_STATE_TABLES_20261001.md"
EXCLUDE = {"PC_track12"}
CASES = {"stairs_15_down": "계단 15cm (G5)", "stairs_10_down": "계단 10cm (G5)", "rough_lateral": "험지 옆걸음 (G3)",
         "rough_forward": "험지 전진 (G3)", "combined_yaw_right": "복합 우회전 (G2)", "push": "밀침 4방향 (G6, 로봇 단위)"}
VARS = {  # key: (label, unit, digits, kind)  kind: early = 초기 1~3 s, pre = 판정 직전까지(누수 가능), edge = 계단 과정, push
    "early_h": ("초기 몸높이(스캐너 기준)", "m", 3, "early"), "early_tilt": ("초기 기울기", "°", 1, "early"),
    "early_along": ("초기 명령 방향 속도", "m/s", 2, "early"),
    "w_h": ("몸높이(스캐너 기준)", "m", 3, "win"), "w_h_std": ("상하 출렁임", "m", 3, "win"),
    "w_tilt_med": ("기울기 중앙값", "°", 1, "win"), "w_tilt_p90": ("기울기 90분위", "°", 1, "win"),
    "w_v_cmd": ("명령 방향 속도", "m/s", 2, "win"), "w_vz_p90": ("수직 속도 90분위", "m/s", 2, "win"),
    "h_std": ("상하 출렁임", "m", 3, "pre"), "tilt_p90": ("기울기 90분위", "°", 1, "pre"), "vz_p90": ("수직 속도 90분위", "m/s", 2, "pre"),
    "v_cmd": ("명령 방향 속도", "m/s", 2, "pre"), "wz_med": ("yaw 각속도", "rad/s", 2, "pre"),
    "edge_vz_max": ("모서리 최대 상승 속도", "m/s", 2, "edge"), "edge_tilt_max": ("모서리 최대 기울기", "°", 1, "edge"),
    "tread1_h": ("첫 디딤판 위 몸높이", "m", 3, "edge"), "approach_h": ("접근 몸높이(디딤판 기준)", "m", 3, "edge"),
    "edge_v": ("모서리 전진 속도", "m/s", 2, "edge"), "cross_s": ("첫 디딤판 통과 시간", "s", 2, "edge"),
    "pre_h": ("밀기 직전 1 s 몸높이(로봇 중앙값)", "m", 3, "push"), "pre_tilt": ("밀기 직전 1 s 기울기(로봇 중앙값)", "°", 1, "push"),
    "pre_speed": ("밀기 직전 1 s 속도(로봇 중앙값)", "m/s", 2, "push"),
    "peak_tilt": ("밀친 뒤 1.5 s 최대 기울기(로봇 최대)", "°", 1, "outcome"),
    "min_h": ("밀친 뒤 1.5 s 최저 몸높이(로봇 최소)", "m", 3, "outcome"),
    "front_width": ("앞발 좌우 간격", "m", 3, "diag"), "hind_width": ("뒷발 좌우 간격", "m", 3, "diag"),
    "duty": ("발 접지 비율", "", 2, "diag"), "roll_p90": ("roll 90분위", "°", 1, "diag"), "thigh": ("thigh 관절 각", "rad", 2, "diag"),
    "calf": ("calf 관절 각", "rad", 2, "diag"),
}
KIND_NOTE = {"early": "초기 1~3 s", "win": "1~4 s 고정(5 s 전 판정 로봇 제외)", "pre": "판정 직전까지(넘어지는 과정 섞임)",
             "edge": "계단 모서리 과정(모서리를 끝까지 지난 로봇만)", "push": "밀기 직전", "outcome": "밀친 뒤(넘어짐 결과)",
             "diag": "진단 재생 1~4 s 고정(A048·A043)"}
EDGE_NOTE = {"full": "모서리를 끝까지 지남", "judged_in_edge": "판정 직전 모서리 구간 안", "unjudged_not_crossed": "판정 없이 관측 종료까지 미통과",
             "judged_after_backing": "모서리에서 물러난 뒤 판정", "not_reached": "모서리 미도달", "no_data": "자료 부족(1 s 안팎 판정)"}
NOT_STATE = {"pre", "outcome"}  # reported for reference, never selected as a deciding state
SERIES = [
    ("lin_vel_z (A033 기준)", [("-2.0", "A033"), ("-1.75", "A044"), ("-1.5", "A043"), ("-1.375", "A050"), ("-1.25", "A048"), ("-1.0", "A049")]),
    ("ang_vel_xy (A033 기준)", [("-0.04", "A041"), ("-0.05", "A033"), ("-0.08", "A038")]),
    ("ang_vel_xy (A043 기준)", [("-0.05", "A043"), ("-0.08", "A055")]),
    ("flat_orientation (A033 기준)", [("0", "A033"), ("-0.5", "A047")]),
    ("track_lin_vel_xy (A033 기준)", [("1.5", "A033"), ("1.6", "A042")]),
]


def rd(p):
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def auc(s, f):
    if not s or not f:
        return None
    fs = sorted(f)
    import bisect
    tot = 0.0
    for x in s:
        lo, hi = bisect.bisect_left(fs, x), bisect.bisect_right(fs, x)
        tot += lo + 0.5 * (hi - lo)
    return tot / (len(s) * len(f))


def best_cut(s, f, higher):
    best = (None, -1, 0, 0)
    for c in sorted(set(s + f)):
        ts = sum((x >= c) if higher else (x <= c) for x in s) / len(s)
        tf = sum((x >= c) if higher else (x <= c) for x in f) / len(f)
        if ts - tf > best[1]:
            best = (c, ts - tf, ts, tf)
    return best


def fmt(x, d):
    return "—" if x is None else f"{x:.{d}f}"


def records():
    body = {(r["arm"], r["case"], r["seed"], r["env"]): r for r in rd(EV / "go2_robot_state_profile_20261001/PER_ENV.csv")}
    so = rd(EV / "go2_state_outcome_20261001/PER_ENV.csv")
    recs = []
    for r in so:
        if r["arm"] in EXCLUDE:
            continue
        k = (r["arm"], r["case"], r["seed"], r["env"])
        if r["case"] in CASES and k in body:
            b = body[k]
            rec = {"arm": r["arm"], "case": r["case"], "cell": (r["case"], r["seed"]), "success": int(b["success"]),
                   "edge_status": b.get("edge_status") or "no_data", "win_ok": b.get("w_h") not in (None, "")}
            for v in VARS:
                src = r if v.startswith("early_") else b
                if VARS[v][3] == "edge" and b.get("edge_full") != "1":
                    continue  # 모서리 구간을 끝까지 지나지 못한 로봇은 모서리 값이 관측 끝에서 잘려 있다 — 비교에서 뺀다
                if src.get(v) not in (None, ""):
                    rec[v] = float(src[v])
            recs.append(rec)
    # push: robot level over the 4 push cases (each case = separate robot run)
    ev = {}
    for e in rd(EV / "go2_state_outcome_20261001/PER_PUSH_EVENT.csv"):
        if e["arm"] in EXCLUDE or e["push_detected"] != "1" or e["pre_upright"] != "1":
            continue
        ev.setdefault((e["arm"], e["case"], e["seed"], e["env"]), []).append(e)
    for r in so:
        if r["arm"] in EXCLUDE or not r["case"].startswith("push"):
            continue
        es = ev.get((r["arm"], r["case"], r["seed"], r["env"]), [])
        rec = {"arm": r["arm"], "case": "push", "cell": (r["case"], r["seed"]), "success": int(r["fall"] == "0")}
        if es:
            rec["pre_h"] = st.median(float(e["pre_h"]) for e in es)
            rec["pre_tilt"] = st.median(float(e["pre_tilt"]) for e in es)
            rec["pre_speed"] = st.median(float(e["pre_speed"]) for e in es)
            rec["peak_tilt"] = max(float(e["peak_tilt_1p5"]) for e in es)
            rec["min_h"] = min(float(e["min_h_1p5"]) for e in es)
        recs.append(rec)
    for r in rd(EV / "go2_foot_body_state_diag_20261001/PER_ENV.csv"):
        rec = {"arm": r["arm"] + "_diag", "case": r["case"], "success": int(r["success"])}
        for v in ("front_width", "hind_width", "duty", "roll_p90", "thigh", "calf"):
            if r.get(v) not in (None, ""):
                rec[v] = float(r[v])
        recs.append(rec)
    return recs


def analyse(recs):
    rows = []
    for case in CASES:
        g = [r for r in recs if r["case"] == case]
        arms = sorted({r["arm"] for r in g})
        for v, (label, unit, d, kind) in VARS.items():
            have = [r for r in g if v in r]
            s = [r[v] for r in have if r["success"]]
            f = [r[v] for r in have if not r["success"]]
            if len(s) < 5 or len(f) < 5:
                continue
            a = auc(s, f)
            within = []
            for arm in arms:
                ss = [r[v] for r in have if r["arm"] == arm and r["success"]]
                ff = [r[v] for r in have if r["arm"] == arm and not r["success"]]
                if len(ss) >= 5 and len(ff) >= 5:
                    within.append((arm, auc(ss, ff), len(ss), len(ff)))
            higher = a >= 0.5
            agree = sum(1 for _, x, _, _ in within if (x >= 0.5) == higher)
            strong = (a >= 0.7 or a <= 0.3) and kind not in NOT_STATE
            if within:
                keep = strong and agree >= (2 / 3) * len(within)
            else:
                keep = strong
            cut, j, ts, tf = best_cut(s, f, higher)
            rows.append({"case": case, "var": v, "label": label, "unit": unit, "digits": d, "kind": kind,
                         "n_success": len(s), "n_fail": len(f), "success_med": st.median(s), "fail_med": st.median(f),
                         "auc_pooled": a, "within": "; ".join(f"{arm} {x:.2f} ({ns}/{nf})" for arm, x, ns, nf in within),
                         "within_agree": f"{agree}/{len(within)}", "keep": int(keep), "within_checked": int(bool(within)),
                         "cut": cut, "cut_dir": "이상" if higher else "이하", "cut_success_frac": ts, "cut_fail_frac": tf})
    return rows


def common_cells(g, arms):
    """보상 비교 정책들이 모두 가진 평가 칸(case, 평가 seed)의 교집합."""
    sets = [{r.get("cell") for r in g if r["arm"] == a} for a in arms]
    return set.intersection(*sets) if sets else set()


def cell_text(cells):
    by = {}
    for c, sd in sorted(cells):
        by.setdefault(c, []).append(sd)
    return ", ".join(f"{c} seed {'·'.join(v)}" for c, v in by.items())


def case_counts(recs, case):
    """전체 로봇 레코드 집계(지표별 측정 가능 대수와 분리)."""
    g = [r for r in recs if r["case"] == case and not r["arm"].endswith("_diag")]
    return sum(r["success"] for r in g), sum(1 for r in g if not r["success"])


def trend_rows(recs, case, keepvars, ident):
    out = []
    g = [r for r in recs if r["case"] == case]
    for title, series in SERIES:
        present = [(val, a) for val, a in series if any(r["arm"] == a for r in g)]
        if len(present) < 2:
            continue
        base = {"lin_vel_z (A033 기준)": "A033", "ang_vel_xy (A033 기준)": "A033", "ang_vel_xy (A043 기준)": "A043",
                "flat_orientation (A033 기준)": "A033", "track_lin_vel_xy (A033 기준)": "A033"}[title]
        checks = [ident.get((base, a), {}).get("verdict") for _, a in present if a != base]
        ok = all(c == "ONLY_ONE_REWARD" for c in checks)
        cells = common_cells(g, [a for _, a in present])
        gc = [r for r in g if r.get("cell") in cells]
        same_cfg = all({r.get("cell") for r in recs if r["case"] == case and r["arm"] == a} == cells for _, a in present)
        head = f"| {title} | " + " | ".join(f"{val} ({a})" for val, a in present) + " |"
        lines = [head, "|" + "---|" * (len(present) + 1)]
        cnt = [(sum(r["success"] for r in gc if r["arm"] == a), sum(1 for r in gc if r["arm"] == a)) for _, a in present]
        lines.append("| 성공 / 전체 (로봇) | " + " | ".join(f"{s}/{t}" for s, t in cnt) + " |")
        for v in keepvars:
            label, unit, d, kind = VARS[v]
            meds = []
            for _, a in present:
                xs = [r[v] for r in gc if r["arm"] == a and v in r]
                meds.append(st.median(xs) if xs else None)
            u = f" ({unit})" if unit else ""
            lines.append(f"| {label}{u} | " + " | ".join(fmt(x, d) for x in meds) + " |")
        cfg = (f"모든 정책이 같은 평가 구성({len(cells)}칸: case×평가 seed)" if same_cfg else
               f"정책마다 평가 구성이 달라 공통 {len(cells)}칸만 사용({cell_text(cells)})")
        out += [f"보상 설정: {'한 항만 다름(ONLY_ONE_REWARD)' if ok else '확인 필요'} / 평가 구성: {cfg}", ""] + lines + [""]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recs = records()
    rows = analyse(recs)
    with (OUT / "DISCRIMINATION.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    ident = {(r["base"], r["arm"]): r for r in rd(EV / "go2_series_identity_20261001/SERIES_IDENTITY.csv")}
    rewards = {r["arm"]: r for r in rd(EV / "go2_state_outcome_20261001/IDENTITY.csv")}
    md = ["# Go2 종목별 — 성공을 가르는 로봇 상태 (2026-10-01, 재작성)", "",
          "이전 판의 결함(겹치는 범위를 목표처럼 제시, 밀침에 정지 정책 포함·이벤트 단위 집계)을 고쳐 다시 만들었다. 도구 `tools/go2_success_discrimination.py`, 증거 `evidence/go2_success_discrimination_20261001/DISCRIMINATION.csv`.",
          "- 로봇 단위. 정지 정책(PC track 1.2)은 모든 계산에서 뺐다. 성공 = 내부 자세 게이트 판정 없음(계단은 ≥2단 + 판정 없음, 밀침은 그 방향 case 에서 판정 없음).",
          "- **분별력 AUC** = 무작위로 고른 성공 로봇의 값이 실패 로봇보다 클 확률. 0.5 = 가르지 못함, 1 또는 0 에 가까울수록 잘 가름.",
          "- **가르는 상태** = 정책을 섞은 AUC 가 0.7 이상(또는 0.3 이하)이고, 성공·실패가 각 5대 이상인 정책 안 AUC 의 방향이 그 정책들의 2/3 이상에서 같은 것. 아래 표에는 이것만 싣는다. 나머지 상태는 CSV 에 있다.",
          "- **경계값** = 성공 로봇 중 경계 쪽 비율 − 실패 로봇 중 경계 쪽 비율이 가장 큰 값. 관측 경계이며 목표값·인과 조건이 아니다.",
          "- 구간: **1~4 s 고정**(모든 로봇 같은 구간, 5 s 전에 판정된 로봇은 빼서 넘어지는 과정이 섞이지 않게) / 초기 1~3 s / 계단 모서리 과정(관측 구간 안에 모서리 구간 d −0.3~0.3 을 끝까지 지난 로봇만 — 못 지난 로봇의 값은 관측 끝에서 잘려 최댓값이 낮게 잡힌다) / 밀기 직전 1 s / 진단 재생(1~4 s 고정). '판정 직전까지' 값과 '밀친 뒤' 값은 넘어지는 과정·결과가 섞여 참고로만 적고 고르지 않는다.",
          "- 추세표: 보상 설정 일치(한 항만 다름, `tools/go2_series_identity_check.py`)와 평가 구성 일치(case×평가 seed)를 따로 적는다. 평가 구성이 다르면 비교 정책 모두가 가진 공통 칸만 센다. 칸 = 그 공통 칸 로봇 중앙값. 학습 1회씩이다.", ""]
    for case, title in CASES.items():
        cr = [r for r in rows if r["case"] == case]
        keep = [r for r in cr if r["keep"]]
        md += [f"## {title}", ""]
        n_s, n_f = case_counts(recs, case)
        md.append(f"전 정책(정지 정책 제외) 전체 로봇 성공 {n_s}대 / 실패 {n_f}대. 표의 대수는 상태별로 측정 가능한 로봇 수다.")
        g = [r for r in recs if r["case"] == case and not r["arm"].endswith("_diag")]
        if case != "push":
            ex = [r for r in g if not r["win_ok"]]
            md.append(f"- 1~4 s 고정 구간 제외(5 s 전 판정 또는 자료 부족): 성공 {sum(r['success'] for r in ex)}대 / 실패 {sum(1 for r in ex if not r['success'])}대.")
        if case.startswith("stairs"):
            from collections import Counter
            for lab, sel in (("성공", 1), ("실패", 0)):
                c = Counter(r["edge_status"] for r in g if r["success"] == sel)
                md.append(f"- 모서리 구간 상태({lab}): " + ", ".join(f"{EDGE_NOTE.get(k, k)} {v}대" for k, v in c.most_common()) + ".")
            md.append("- 모서리 값은 '모서리를 끝까지 지남' 로봇만 쓴다. 이 비교는 판정 전에 첫 모서리를 넘은 집단 안의 비교이며, 제외한 로봇의 동작을 복구한 것이 아니다.")
        if not keep:
            md += ["", "**가르는 상태 없음** — 기준을 넘는 상태값이 없다(CSV 참조).", ""]
        else:
            md += ["", "| 상태 | 구간 | 성공 중앙값 (대수) | 실패 중앙값 (대수) | 분별력 AUC (섞음) | 정책 안 AUC (성공/실패 대수) | 경계값 | 경계에서 성공·실패 비율 |",
                   "|---|---|---|---|---|---|---|---|"]
            for r in sorted(keep, key=lambda r: -abs(r["auc_pooled"] - 0.5)):
                d = r["digits"]
                u = f" ({r['unit']})" if r["unit"] else ""
                md.append(f"| {r['label']}{u} | {KIND_NOTE[r['kind']]} | {fmt(r['success_med'], d)} ({r['n_success']}) | {fmt(r['fail_med'], d)} ({r['n_fail']}) | "
                          f"{r['auc_pooled']:.2f} | {r['within'] or '정책 안 미확인'} | {r['cut_dir']} {fmt(r['cut'], d)} | 성공 {r['cut_success_frac']:.0%} / 실패 {r['cut_fail_frac']:.0%} |")
            md.append("")
        weak = [r for r in cr if not r["keep"] and r["kind"] not in NOT_STATE]
        if weak:
            md += ["가르지 못한 상태(AUC 0.3~0.7 또는 정책 안 방향 불일치, 표본 부족 포함): " + ", ".join(
                f"{r['label']}[{KIND_NOTE[r['kind']]}] {r['auc_pooled']:.2f}" for r in weak), ""]
        ref = [r for r in cr if r["kind"] in NOT_STATE]
        if ref:
            md += ["참고(상태가 아니라 넘어지는 과정·결과가 섞인 값이라 선택하지 않음): " + ", ".join(
                f"{r['label']}[{KIND_NOTE[r['kind']]}] AUC {r['auc_pooled']:.2f}" for r in ref), ""]
        succ_models = sorted({r["arm"] for r in recs if r["case"] == case and r["success"] and not r["arm"].endswith("_diag")},
                             key=lambda a: -sum(x["success"] for x in recs if x["case"] == case and x["arm"] == a))[:4]
        md += ["성공이 많은 정책과 보상 값 (모든 정책 공통: track 1.5·feet_air 0.2·action_rate −0.01·flat 0, 예외는 A042 track 1.6·A047 flat −0.5)", "",
               "| 정책 | 성공 / 전체 | lin_vel_z | ang_vel_xy |", "|---|---|---|---|"]
        for a in succ_models:
            s = sum(x["success"] for x in recs if x["case"] == case and x["arm"] == a)
            t = sum(1 for x in recs if x["case"] == case and x["arm"] == a)
            md.append(f"| {a} | {s}/{t} | {rewards[a]['lin_vel_z_l2']} | {rewards[a]['ang_vel_xy_l2']} |")
        md.append("")
        kv = [r["var"] for r in sorted(keep, key=lambda r: -abs(r["auc_pooled"] - 0.5)) if r["kind"] != "diag"][:4]
        md += ["보상 변수별 추세 (가르는 상태만)", ""] + trend_rows(recs, case, kv, ident)
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
