"""시험 종목별 성공 상태표 (2026-10-01, 읽기 전용).

종목마다: 상태 항목(행) × 성공 모델별 성공 로봇 중앙값 · 성공 예상 최소/최대 · 실패 로봇 범위, 그리고 성공 모델의 보상 변수 값.
- 성공 모델: 그 종목에서 성공 로봇이 가장 많은 정책(아래 MODELS, 서버 run 기준 상위 + 성공이 있는 정책). 괄호는 성공 대수.
- 성공 예상 최소/최대 = 성공 모델들의 성공 로봇 값을 모두 모은 분포의 10분위·90분위. 실패 범위 = 전 정책 실패 로봇의 10~90분위.
  관측 범위이지 인과 조건·최적값이 아니다. 학습 1회씩이다.
입력: evidence/go2_robot_state_profile_20261001/PER_ENV.csv(몸통 상태, 전 정책),
      evidence/go2_foot_body_state_diag_20261001/PER_ENV.csv(발·관절, A048·A043 진단 재생),
      evidence/go2_g_a059_readout_on_a052_a048/PER_ENV.csv·PER_FOOT.csv(A048 계단 앞발 들기·앞 들기),
      evidence/go2_state_outcome_20261001/PER_PUSH_EVENT.csv(밀침), go2_state_outcome_20261001/IDENTITY.csv(보상 값).
출력: evidence/go2_success_state_tables_20261001/SUCCESS_STATE_TABLES.md
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "workspace/training/quadruped/reports/evidence"
OUT = EV / "go2_success_state_tables_20261001"
REWARDS = (("track_lin_vel_xy_exp", "track"), ("feet_air_time", "feet_air"), ("lin_vel_z_l2", "lin_vel_z"),
           ("ang_vel_xy_l2", "ang_vel_xy"), ("action_rate_l2", "action_rate"), ("flat_orientation_l2", "flat"))
MODELS = {
    "stairs_15_down": ("A043", "PC_A048", "A048"),
    "stairs_10_down": ("A043", "A048", "PC_A048", "A049"),
    "rough_lateral": ("A048", "A038", "A050", "A043"),
    "rough_forward": ("A049", "A048", "A044"),
    "combined_yaw_right": ("A048", "A049", "PC_A048", "A044"),
    "push": ("A048", "A055", "A043", "PC_A048"),
}
TITLE = {"stairs_15_down": "계단 15cm 오르기 (G5)", "stairs_10_down": "계단 10cm 오르기 (G5)",
         "rough_lateral": "험지 옆걸음 (G3)", "rough_forward": "험지 전진 (G3)",
         "combined_yaw_right": "복합 우회전 (G2)", "push": "밀침 4방향 (G6)"}
BODY = {  # key, label, unit, digits
    "stairs": [("edge_vz_max", "모서리 몸통 최대 상승 속도", "m/s", 2), ("edge_tilt_max", "모서리 몸통 최대 기울기", "°", 1),
               ("tread1_h", "첫 디딤판 위 몸높이", "m", 3), ("approach_h", "접근 몸높이(평지, 디딤판 기준)", "m", 3),
               ("edge_v", "모서리 전진 속도", "m/s", 2), ("cross_s", "첫 디딤판 통과 시간", "s", 2)],
    "walk": [("h_med", "몸높이(스캐너 기준)", "m", 3), ("h_std", "상하 출렁임(몸높이 표준편차)", "m", 3),
             ("tilt_med", "몸통 기울기 중앙값", "°", 1), ("tilt_p90", "몸통 기울기 90분위", "°", 1),
             ("v_cmd", "명령 방향 속도", "m/s", 2), ("v_side", "명령 수직 방향 새는 속도", "m/s", 2),
             ("wz_med", "yaw 각속도", "rad/s", 2), ("vz_p90", "수직 속도 90분위", "m/s", 2)],
    "diag": [("front_width", "앞발 좌우 간격", "m", 3), ("hind_width", "뒷발 좌우 간격", "m", 3),
             ("duty", "발 접지 비율", "", 2), ("roll_p90", "roll 90분위", "°", 1), ("pitch_med", "pitch(앞 들림 +)", "°", 1),
             ("thigh", "thigh 관절 각", "rad", 2), ("calf", "calf 관절 각", "rad", 2)],
    "push": [("pre_h", "밀침 직전 몸높이", "m", 3), ("peak_tilt_1p5", "밀친 뒤 1.5 s 최대 기울기", "°", 1),
             ("min_h_1p5", "밀친 뒤 1.5 s 최저 몸높이", "m", 3)],
}


def rd(p):
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def med(v):
    return pct(v, .5) if v else None


def fmt(x, d):
    return "—" if x is None else f"{x:.{d}f}"


def vals(rows, k, cond):
    return [float(r[k]) for r in rows if cond(r) and r.get(k) not in ("", None)]


def table(case, rows, items, models, succ_key, arm_key="arm", note=""):
    def cnt(m, ok):
        return sum(1 for r in rows if r[arm_key] == m and bool(succ_key(r)) == ok)
    head = ("| 상태 | " + " | ".join(f"{m} (성공 {cnt(m, True)} / 실패 {cnt(m, False)})" for m in models)
            + " | **성공 예상 최소** | **성공 예상 최대** | 성공 대수 | 실패 로봇 범위 | 실패 대수 |")
    lines = [head, "|" + "---|" * (len(models) + 6)]
    for k, label, unit, d in items:
        per = [med(vals(rows, k, lambda r, m=m: r[arm_key] == m and succ_key(r))) for m in models]
        pool = vals(rows, k, lambda r: r[arm_key] in models and succ_key(r))
        fail = vals(rows, k, lambda r: not succ_key(r))
        if not pool:
            continue
        u = f" ({unit})" if unit else ""
        lines.append(f"| {label}{u} | " + " | ".join(fmt(x, d) for x in per)
                     + f" | **{fmt(pct(pool, .1), d)}** | **{fmt(pct(pool, .9), d)}** | {len(pool)} | "
                     + (f"{fmt(pct(fail, .1), d)} ~ {fmt(pct(fail, .9), d)}" if fail else "—") + f" | {len(fail)} |")
    return lines + ([note] if note else [])


SERIES = [  # (label, [(value, arm), ...]) — same base policy, one reward term changed
    ("lin_vel_z (A033 기준)", [("-2.0", "A033"), ("-1.75", "A044"), ("-1.5", "A043"), ("-1.375", "A050"),
                              ("-1.25", "A048"), ("-1.0", "A049")]),
    ("ang_vel_xy (A033 기준)", [("-0.04", "A041"), ("-0.05", "A033"), ("-0.08", "A038")]),
    ("ang_vel_xy (A043 기준)", [("-0.05", "A043"), ("-0.08", "A055")]),
    ("flat_orientation (A033 기준)", [("0", "A033"), ("-0.5", "A047")]),
    ("track_lin_vel_xy (A033 기준)", [("1.5", "A033"), ("1.6", "A042")]),
]
TREND_KEYS = {
    "stairs": ["edge_vz_max", "edge_tilt_max", "tread1_h", "edge_v"],
    "walk": ["h_med", "h_std", "tilt_p90", "v_cmd", "vz_p90"],
    "push": ["pre_h", "peak_tilt_1p5", "min_h_1p5"],
}


def direction(xs, digits=0):
    """Order of the values left to right. Differences below half the display precision count as no change."""
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return "—"
    tol = 0.5 * 10 ** (-digits)
    d = [0 if abs(b - a) < tol else (1 if b > a else -1) for a, b in zip(xs, xs[1:])]
    if all(x == 0 for x in d):
        return "변화 없음"
    if all(x >= 0 for x in d) and any(x > 0 for x in d):
        return "↑ 단조" if all(x > 0 for x in d) else "↑ (일부 같음)"
    if all(x <= 0 for x in d) and any(x < 0 for x in d):
        return "↓ 단조" if all(x < 0 for x in d) else "↓ (일부 같음)"
    return "비단조"


def trend_tables(rows, items, succ_key, arm_key="arm", unit_label="성공 대수"):
    """rows: per-robot (or per-event) records of one scenario. Values = all-robot medians."""
    out = []
    lab = {k: (label, unit, d) for k, label, unit, d in items}
    for title, series in SERIES:
        arms = [a for _, a in series]
        if not any(r[arm_key] in arms for r in rows):
            continue
        present = [(v, a) for v, a in series if any(r[arm_key] == a for r in rows)]
        if len(present) < 2:
            continue
        head = f"| {title} | " + " | ".join(f"{v} ({a})" for v, a in present) + " | 추세 |"
        lines = [head, "|" + "---|" * (len(present) + 2)]
        succ = [sum(1 for r in rows if r[arm_key] == a and succ_key(r)) for _, a in present]
        tot = [sum(1 for r in rows if r[arm_key] == a) for _, a in present]
        lines.append(f"| {unit_label} (비율로 추세 판정) | " + " | ".join(f"{s}/{t}" for s, t in zip(succ, tot)) + f" | {direction([x / y for x, y in zip(succ, tot)], 2)} |")
        for k in TREND_KEYS[KIND]:
            if k not in lab:
                continue
            label, unit, d = lab[k]
            xs = [med(vals(rows, k, lambda r, a=a: r[arm_key] == a)) for _, a in present]
            u = f" ({unit})" if unit else ""
            lines.append(f"| {label}{u} — 전체 중앙값 | " + " | ".join(fmt(x, d) for x in xs) + f" | {direction(xs, d)} |")
        out += lines + [""]
    return out


KIND = "walk"


def reward_table(models, ident):
    lines = ["| 보상 변수 | " + " | ".join(models) + " |", "|" + "---|" * (len(models) + 1)]
    for key, label in REWARDS:
        lines.append(f"| {label} | " + " | ".join(ident.get(m, {}).get(key, "—") for m in models) + " |")
    return lines


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    body = rd(EV / "go2_robot_state_profile_20261001/PER_ENV.csv")
    diag = rd(EV / "go2_foot_body_state_diag_20261001/PER_ENV.csv")
    push = rd(EV / "go2_state_outcome_20261001/PER_PUSH_EVENT.csv")
    ident = {r["arm"]: r for r in rd(EV / "go2_state_outcome_20261001/IDENTITY.csv")}
    a052_env = rd(EV / "go2_g_a059_readout_on_a052_a048/PER_ENV.csv")
    ident_pairs = {(r["base"], r["arm"]): r for r in rd(EV / "go2_series_identity_20261001/SERIES_IDENTITY.csv")}
    global IDENT
    IDENT = ident_pairs
    a052_foot = rd(EV / "go2_g_a059_readout_on_a052_a048/PER_FOOT.csv")
    out = ["# Go2 시험 종목별 성공 상태표 (2026-10-01)", "",
           "성공 = 내부 자세 게이트 판정 없음(계단은 ≥2단 + 판정 없음). 성공 모델 열의 값 = 그 정책 성공 로봇의 중앙값, 괄호 = 그 정책의 성공/실패 대수(96대 중, 밀침은 밀침 이벤트 수). 성공 대수·실패 대수 열 = 그 행의 범위를 계산한 로봇 수(성공 = 성공 모델들의 성공 로봇 합계, 실패 = 전 정책의 실패 로봇 합계; 그 구간에 들어가지 못한 로봇은 빠지므로 행마다 다를 수 있다).",
           "**성공 예상 최소/최대 = 성공 모델들의 성공 로봇 값을 모은 분포의 10~90분위**. 실패 로봇 범위 = 전 정책 실패 로봇의 10~90분위. 관측 범위이며 인과 조건·최적값이 아니다(정책마다 학습 1회).",
           "각 종목 끝의 **보상 변수별 추세표**: 같은 기준 정책에서 한 항만 바꾼 정책들을 값 순서로 놓고, 칸에 그 정책 전체 로봇의 중앙값(성공·실패 합)을 적는다. 추세 열은 값 순서대로 모두 같은 방향이면 단조, 아니면 비단조. 학습 1회씩이며 같은 보상의 서버→PC 차이도 크다(예: 계단 15cm 상승 속도 0.21→0.51).",
           "",
           "## 추세 비교의 동일 조건 확인 (`tools/go2_series_identity_check.py`, `evidence/go2_series_identity_20261001/SERIES_IDENTITY.csv`)",
           "각 쌍의 회수물 학습 기록을 직접 비교했다. 보상 = `training/env.yaml` rewards 블록 전체(모든 항의 weight·params). 환경 = rewards 밖 env.yaml 전체(지형·명령·관측·이벤트·종료·seed, 경로·로그 위치 행 제외, 948행). PPO 설정 = agent.yaml(55행). 학습 코드 = 보상 파일을 뺀 학습 소스 6개 파일 해시. 조건 = 학습 seed·iter·env 수·평가 checkpoint iter·평가기·registry SHA·실행 장비.",
           "대조 검사: A033 대 A055(두 항 변경)는 두 항 차이로 잡힌다.",
           "",
           "| 추세 계열 | 값 | 기준 → 비교 | 다른 보상 항 (전 → 후) | 환경 차이 행 | PPO 설정 차이 행 | 학습 코드 차이 | 학습 seed / iter / env 수 / 평가 iter | 판정 |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rd(EV / "go2_series_identity_20261001/SERIES_IDENTITY.csv"):
        out.append(f"| {r['series']} | {r['value']} | {r['base']} → {r['arm']} | {r['reward_diff']} | {r['env_lines_diff']} | "
                   f"{r['agent_lines_diff']} | {r['train_code_files_diff']} | {r['seed_iter_envs_ckpt']} | **{r['verdict']}**"
                   + (f" ({r['condition_diff']})" if r['condition_diff'] != '없음' else "") + " |")
    out += ["", "판정: 아래 추세표의 모든 비교 정책은 기준 정책과 **보상 한 항만 다르고**, 환경·PPO 설정·학습 코드·학습 seed·iter·평가 조건이 같다(ONLY_ONE_REWARD). 학습 기록에 남지 않은 것은 확인하지 못했다: 서버의 Isaac Lab·torch 버전(미기록, run 날짜 09-15~09-29), GPU 학습 비결정성. 학습 비결정성의 크기는 같은 보상의 서버→PC 쌍이 참고값이다.", ""]
    out += [
           "몸통 상태는 전 정책 평가 기록, 발·관절은 진단 재생(A048·A043)에만 있다(성공 로봇 5대 미만이면 표를 싣지 않는다). 상태는 판정 시작 전 구간만 쓴다. 우회전 실패 범위는 A043 실패 29대뿐이다.", ""]
    for case, models in MODELS.items():
        out += [f"## {TITLE[case]}", ""]
        if case == "push":
            ok = lambda r: r["push_detected"] == "1" and r["pre_upright"] == "1" and r["fell_after"] == "0"  # noqa: E731
            ev = [r for r in push if r["push_detected"] == "1" and r["pre_upright"] == "1"]
            out += table(case, ev, BODY["push"], models, ok)
        else:
            rows = [r for r in body if r["case"] == case]
            ok = lambda r: r["success"] == "1"  # noqa: E731
            out += table(case, rows, BODY["stairs" if case.startswith("stairs") else "walk"], models, ok)
            if case.startswith("stairs"):
                out += ["", "_전체 구간 몸통 값(몸높이·속도 등)은 계단 꼭대기 정지 구간이 섞여 계단 표에서 뺐다._"]
            d = [r for r in diag if r["case"] == case]
            if d and sum(1 for r in d if ok(r)) >= 5:  # fewer than 5 successful robots: no range
                dm = [m for m in models if any(r["arm"] == m for r in d)] or sorted({r["arm"] for r in d})
                out += ["", f"발·자세·관절 (진단 재생: {', '.join(sorted({r['arm'] for r in d}))}, 평가 seed 하나)", ""]
                out += table(case, d, BODY["diag"], dm, ok)
            if case == "stairs_15_down":
                okg = {"clean", "ge2_then_judged"}
                e = [r for r in a052_env if r["case"] == case]
                f = [r for r in a052_foot if r["case"] == case and r["pair"] == "front"]
                lift_s = [float(r["edge_lift"]) for r in f if r["group"] in okg and r["edge_lift"]]
                lift_f = [float(r["edge_lift"]) for r in f if r["group"] not in okg and r["edge_lift"]]
                nose_s = [float(r["nose_up_max_deg"]) for r in e if r["group"] in okg and r["nose_up_max_deg"]]
                nose_f = [float(r["nose_up_max_deg"]) for r in e if r["group"] not in okg and r["nose_up_max_deg"]]
                out += ["", "앞발·앞 들기 (A048 진단 재생 seed 101, ≥2단 로봇 5대 — 판정 없음 1 + 오른 뒤 판정 4; A043 미측정)", "",
                        "| 상태 | A048 오른 로봇 중앙값 | 성공 예상 최소 | 성공 예상 최대 | 오른 쪽 수 | 못 오른 로봇 범위 | 못 오른 쪽 수 |", "|---|---|---|---|---|---|---|",
                        f"| 모서리 전 앞발 들기 높이 (m, 발바닥 기준) | {fmt(med(lift_s), 3)} | {fmt(pct(lift_s, .1), 3)} | {fmt(pct(lift_s, .9), 3)} | 앞발 {len(lift_s)}개 (로봇 5) | {fmt(pct(lift_f, .1), 3)} ~ {fmt(pct(lift_f, .9), 3)} | 앞발 {len(lift_f)}개 |",
                        f"| 모서리 앞 들기 최대 (°) | {fmt(med(nose_s), 1)} | {fmt(pct(nose_s, .1), 1)} | {fmt(pct(nose_s, .9), 1)} | 로봇 {len(nose_s)} | {fmt(pct(nose_f, .1), 1)} ~ {fmt(pct(nose_f, .9), 1)} | 로봇 {len(nose_f)} |"]
        out += ["", "성공 모델의 보상 변수 값", ""] + reward_table(models, ident) + [""]
        global KIND
        if case == "push":
            KIND = "push"
            out += ["보상 변수별 추세 (칸 = 그 정책 전체 이벤트 중앙값, 첫 행 = 넘어지지 않은 밀침 / 전체 밀침)", ""]
            out += trend_tables(ev, BODY["push"], ok, unit_label="성공 밀침")
        else:
            KIND = "stairs" if case.startswith("stairs") else "walk"
            out += ["보상 변수별 추세 (칸 = 그 정책 전체 로봇 중앙값, 첫 행 = 성공 대수 / 전체 96대)", ""]
            out += trend_tables(rows, BODY[KIND], ok)
    (OUT / "SUCCESS_STATE_TABLES.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
