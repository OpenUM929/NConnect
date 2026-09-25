"""Go2 보상 기전 예측 — 원문 식(역할) × 학습 로그로 걷기/멈춤과 변수 변경 결과를 유추한다.

왜 있는가.  2026-09-17 사용자 지시: "원문 역할이 사실 기반 추론이다. 이것을 기반으로 현재 상황을 예측하고
track 또는 변수에 따른 결과를 예측해야 한다. 이전에 실패한 것과 A033 기준값을 근거 자료로 비교해 유추하고
향후 튜닝 정책을 잡아라."

기전 (Isaac Lab v2.3.1 원문, `reports/evidence/go2_reward_term_roles_20260917/`):
  * 보상 관리자는 매 step `식 × 가중치 × dt`를 에피소드 동안 더하고, 로그 = 합의 평균 ÷ 20 s다.
    그래서 `로그 ÷ 가중치` = 그 정책이 만든 식 값(초당)이고, 가중치와 분리된 **행동의 값**이다.
  * 제자리에 서면 추종 항은 exp(−|명령|²/std²)만 남고, 움직임 벌점은 작아진다.
  * 그러므로 가중치 w에서 "걷는 행동"과 "멈춘 행동"이 받는 초당 보상의 차이는
        margin(w) = Σ_항 w_항 × (걷는 행동의 식 값 − 멈춘 행동의 식 값)
    이다.  margin이 음수면 멈춤이 보상상 더 낫다 — PPO가 멈춤으로 수렴할 이유가 식에 있다.
  * 걷는 행동의 식 값 = 걷는 회차 학습 로그 ÷ 가중치의 평균, 멈춘 행동 = 지형 레벨 0 회차의 평균.
    로그가 소수 3자리라 |로그| < `MIN_LOG`인 칸은 쓰지 않는다(반올림 오차 10% 초과).
  * `flat_orientation_l2`는 걷는 회차 가중치가 전부 0이라 걷는 행동의 식 값을 로그에서 얻을 수 없다.
    멈춘 행동은 이 항을 켠 A013(정지)의 로그에서, 걷는 행동은 평가 `steps.csv`의 `proj_grav_z`로
    계산한 식 값(1 − gz²)으로 대신한다(평가 조건 — 학습과 다르다).

검증: 모든 학습 회차의 margin을 계산해 실제 걷기/정지와 대조한다(사후 대조).  식 값 평균에서
그 회차를 빼고 다시 계산한 값(LOO)도 함께 적는다 — 자기 자신으로 맞춘 결과가 아닌지 본다.

산출 (reports/evidence/go2_reward_mechanism_20260917/):
  TERM_VALUES.csv   회차 × 항: 가중치·로그·식 값
  RUN_MARGIN.csv    회차별 margin(전체·LOO)·항별 기여·실제 걷기·구간
  PROBES.csv        G-A033에서 한 항만 바꿀 때의 예측 margin·구간·걷기 경계 가중치
  TILT.csv          평가 case별 기울기 식 값(1 − gz²)과 종료 직전 기울기
보고서: reports/GO2_REWARD_MECHANISM_FORECAST.md
사용: python tools/go2_reward_mechanism.py            (CSV·보고서 재생성, 평가 기록 판독 포함)
      python tools/go2_reward_mechanism.py --report   (CSV에서 보고서만)
"""
from __future__ import annotations

import collections
import csv
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_tuning_base_data as base  # noqa: E402

KEEP = ROOT / "workspace/_keep"
QUAD = ROOT / "workspace/training/quadruped"
OUT = QUAD / "reports/evidence/go2_reward_mechanism_20260917"
DOC = QUAD / "reports/GO2_REWARD_MECHANISM_FORECAST.md"
DOC_REL = "workspace/training/quadruped/reports/GO2_REWARD_MECHANISM_FORECAST.md"

# margin에 넣는 항 — 걷는 회차 로그에서 식 값을 얻을 수 있는 항 전부.
MARGIN_TERMS = ("track_lin_vel_xy_exp", "track_ang_vel_z_exp", "lin_vel_z_l2", "ang_vel_xy_l2",
                "action_rate_l2", "dof_torques_l2", "dof_acc_l2", "feet_air_time")
# WEIGHT_OUTCOME.csv에 없는 항 — 모든 학습 env.yaml에서 같은 값(관문이 전수 대조).
FIXED_TERMS = ("track_ang_vel_z_exp", "dof_torques_l2", "dof_acc_l2")
MIN_LOG = 0.010
BASELINE = "G-A033"
# 기반 데이터 TRAIN_OF에 없는 한 항 변경 회차의 학습 로그 run.
TRAIN_EXTRA = {
    "A010": "go2_g_a010_lin_vel_z_m2", "A013": "go2_g_a013_flat_orientation_m1",
    "A020": "go2_g_a020_chain01_lin_vel_z_m2", "A021": "go2_g_a021_chain01_ang_vel_xy_m005",
    "A024": "go2_g_a024_ang_vel_xy_m015",
}
# G-A033에서 한 항만 바꾸는 예측 지점.  과거 회차에서 쓴 값과 사양·배포 안내 범위의 끝값이다.
PROBES = (
    ("track_lin_vel_xy_exp", 1.4), ("track_lin_vel_xy_exp", 1.6), ("track_lin_vel_xy_exp", 2.0),
    # 2026-09-22 (G-A043): -1.5 는 계획 `upload/plan/GO2_POST_A042_PLAN_20260922.md` §2 가 고른 값이다.
    # 새 값이면 이 생성기로 계산한다(§8-1).  -1.0 은 G-A037 의 값이라 그대로 둔다.
    # 2026-09-22 (G-A044): -1.75 는 계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md` §1 이 고른 값이다.
    # A043 이 -1.5 에서 걸었으므로 이 다이얼의 걷는 관측값은 둘이고, -1.75 는 그 사이다.
    ("lin_vel_z_l2", -3.0), ("lin_vel_z_l2", -1.75), ("lin_vel_z_l2", -1.5),
    ("lin_vel_z_l2", -1.0), ("lin_vel_z_l2", -0.5),
    ("ang_vel_xy_l2", -0.08), ("ang_vel_xy_l2", -0.1), ("ang_vel_xy_l2", -0.15), ("ang_vel_xy_l2", -0.02),
    # 2026-09-20: 완화 방향의 작은 값.  PM 1안이 제안한 -0.04 를 표에 넣어야 §8-1(새 값이면 이
    # 생성기로 계산한다)을 지킨 채 비교할 수 있다.  -0.03 은 그 사이 기울기를 보기 위한 점이다.
    ("ang_vel_xy_l2", -0.04), ("ang_vel_xy_l2", -0.03),
    ("action_rate_l2", -0.02), ("action_rate_l2", -0.005),
    ("dof_acc_l2", -1.25e-07), ("dof_acc_l2", -5e-07),
    ("dof_torques_l2", -0.0001), ("dof_torques_l2", -0.0004),
    ("feet_air_time", 0.01), ("feet_air_time", 0.35),
)
# 멈춘 기준(Default-01·chain01) 위의 한 항 변경 회차.
STOPPED_CHILDREN = ("A010", "A013", "A024", "feet_air_time_020_v1", "A020", "A021", "A022")
# 이 예측을 쓴 뒤에 학습한 회차.  계수(식 값 평균)에 넣지 않고 §9 사후 대조에만 쓴다 — 예측을 맞춘 회차로
# 계수를 다시 맞추면 예측력 검사가 사라진다.  (work, term, to, readout 증거 폴더)
HELD_OUT = (("G-A038", "ang_vel_xy_l2", "-0.08", "reports/evidence/go2_g_a038_readout_20260917"),
            # 2026-09-22: A043 은 회수됐는데 §9 대조가 없었다.  계획 §7 첫 줄이 요구한 대조다.
            # 표는 `tools/go2_a043_forecast_check.py` 가 원자료에서 만든다.
            ("G-A043", "lin_vel_z_l2", "-1.5", "reports/evidence/go2_g_a043_readout_20260922"))
ENV_CFG = "workspace/training/quadruped/go2_task/env_cfg.py"
REWARDS_PY = "workspace/training/quadruped/quadruped_rewards.py"
# 기울기 판독 — 평가 기록 (run 폴더, arm, 이름).  chain01은 낙상 검출 세대의 멈춘 정책이다.
TILT_ARMS = (("go2_g_a033_a017_track_lin_vel_xy_150", "candidate", "G-A033"),
             ("go2_chain01_baseline", "chain01", "chain01"))
TILT_CASES = ("forward_nominal", "rough_forward", "rough_lateral", "left", "slope_plus_20", "slope_minus_20",
              "stairs_10_down", "stairs_15_down", "stairs_10_up", "stairs_15_up", "push_pos_y")
STAND_CASES = ("forward_nominal", "rough_forward")   # 걷기/멈춤 기울기 차이를 잴 case (두 arm 모두 있는 것)
SEEDS = ("101", "202", "303")
PRE_TERM = (1.0, 0.5)   # 종료 직전 창: 종료 시각 − 1.0 s ~ − 0.5 s
CASE_LABEL = dict(base.CASE_LABEL, left="평지 왼쪽 옆", push_pos_y="왼쪽 밀침")


# ─────────────────────────────────────────────────────────────────────────────
# 식 값과 margin
# ─────────────────────────────────────────────────────────────────────────────
def train_runs() -> dict[str, str]:
    return {**base.TRAIN_OF, **TRAIN_EXTRA}


def fixed_weights() -> dict[str, float]:
    env = base.env_terms()
    return {t: float(env[f"rewards.{t}"]["weight"]) for t in FIXED_TERMS}


def weights_of(row: dict[str, str]) -> dict[str, float]:
    fixed = fixed_weights()
    return {t: fixed[t] if t in fixed else float(row[t]) for t in (*MARGIN_TERMS, "flat_orientation_l2")}


def term_values() -> list[dict[str, str]]:
    runs = train_runs()
    logs = {r["run"]: r for r in base.read("TRAINING_TERMS.csv")}
    out = []
    for row in base.weights():
        run = runs.get(row["name"])
        if run is None:
            continue
        w = weights_of(row)
        for term in MARGIN_TERMS:
            logged = logs[run][term]
            usable = abs(float(logged)) >= MIN_LOG and w[term] != 0
            out.append({"name": row["name"], "run": run, "term": term, "weight": repr(w[term]), "logged": logged,
                        "value": f"{float(logged) / w[term]:.6g}" if usable else "",
                        "walking": str(base.walking(row)), "terrain_level": logs[run]["terrain_level"]})
    return out


def pool_members(values: list[dict[str, str]], leave_out: str = "") -> tuple[dict, dict]:
    """항별 (걷는 행동 [(회차, 식 값)], 멈춘 행동 [...]) — 멈춘 행동은 학습 지형 레벨 0 회차.
    leave_out을 빼면 비는 항은 빼지 않는다(그 항의 표본이 그 회차 하나뿐이다)."""
    walk: dict[str, list[tuple[str, float]]] = {t: [] for t in MARGIN_TERMS}
    stand: dict[str, list[tuple[str, float]]] = {t: [] for t in MARGIN_TERMS}
    for v in values:
        if not v["value"]:
            continue
        if v["walking"] == "True":
            walk[v["term"]].append((v["name"], float(v["value"])))
        elif float(v["terrain_level"]) == 0.0:
            stand[v["term"]].append((v["name"], float(v["value"])))
    for group in (walk, stand):
        for t, items in group.items():
            kept = [x for x in items if x[0] != leave_out]
            group[t] = kept or items
    return walk, stand


def pools(values: list[dict[str, str]], leave_out: str = "") -> tuple[dict[str, float], dict[str, float]]:
    """(걷는 행동 식 값, 멈춘 행동 식 값) 평균."""
    walk, stand = pool_members(values, leave_out)
    return ({t: statistics.mean(v for _n, v in x) for t, x in walk.items()},
            {t: statistics.mean(v for _n, v in x) for t, x in stand.items()})


def contributions(w: dict[str, float], walk: dict[str, float], stand: dict[str, float]) -> dict[str, float]:
    return {t: w[t] * (walk[t] - stand[t]) for t in MARGIN_TERMS}


def zone(margin: float, walk_min: float, stop_max: float) -> str:
    if margin > stop_max:
        return "WALK"
    if margin < walk_min:
        return "STOP"
    return "BAND"


def run_margins(values: list[dict[str, str]]) -> list[dict[str, str]]:
    walk, stand = pools(values)
    rows = []
    for row in base.weights():
        w = weights_of(row)
        part = contributions(w, walk, stand)
        lw, ls = pools(values, leave_out=row["name"])
        rows.append({"name": row["name"], "walking": str(base.walking(row)),
                     "rough_forward_speed": row["rough_forward_speed"],
                     "margin": f"{sum(part.values()):.4f}",
                     "margin_loo": f"{sum(contributions(w, lw, ls).values()):.4f}",
                     **{f"part_{t}": f"{v:.4f}" for t, v in part.items()}})
    walkers = [float(r["margin"]) for r in rows if r["walking"] == "True"]
    stoppers = [float(r["margin"]) for r in rows if r["walking"] != "True"]
    walkers_loo = [float(r["margin_loo"]) for r in rows if r["walking"] == "True"]
    stoppers_loo = [float(r["margin_loo"]) for r in rows if r["walking"] != "True"]
    for r in rows:
        r["zone"] = zone(float(r["margin"]), min(walkers), max(stoppers))
        r["zone_loo"] = zone(float(r["margin_loo"]), min(walkers_loo), max(stoppers_loo))
    return rows


def spec_margin(candidate: dict[str, float]) -> dict[str, object]:
    """reward 사양의 후보 가중치 → 예측 걷기 margin·구간.  사양에 없는 항은 G-A033 값이다.
    기반 데이터 관문(`go2_tuning_base_data.spec_problems`)이 부른다."""
    values = term_values()
    walk, stand = pools(values)
    walk_min, stop_max = band(run_margins(values))
    ref = weights_of(next(r for r in base.weights() if r["name"] == BASELINE))
    w = dict(ref, **{t: float(v) for t, v in candidate.items() if t in ref})
    # 기울기 벌점의 걷기 변화는 평가 기울기로 대신한 [추정] 값이다(§5).
    flat = (w["flat_orientation_l2"] - ref["flat_orientation_l2"]) * flat_walk_slope(read("TILT.csv"))
    margin = round(sum(contributions(w, walk, stand).values()) + flat, 4)
    diffs = situation_diffs(read("SITUATIONS.csv"))
    changed = [t for t in w if w[t] != ref[t]]
    situations = {s: round(situation_margin(w, d) - situation_margin(ref, d), 4) for s, d in diffs.items()}
    return {"source": DOC_REL, "margin": margin, "zone": zone(margin, walk_min, stop_max),
            "stop_max": round(stop_max, 4), "situations": situations,
            "worse": sorted(s for s, v in situations.items() if v < 0),
            "unmeasured_in_situations": sorted(t for t in changed if t in UNMEASURED_IN_EVAL)}


def band(rows: list[dict[str, str]], column: str = "margin") -> tuple[float, float]:
    """(걷는 회차 최저 margin, 멈춘 회차 최고 margin)."""
    return (min(float(r[column]) for r in rows if r["walking"] == "True"),
            max(float(r[column]) for r in rows if r["walking"] != "True"))


def probes(values: list[dict[str, str]], rows: list[dict[str, str]]) -> list[dict[str, str]]:
    walk, stand = pools(values)
    walk_min, stop_max = band(rows)
    ref = next(r for r in base.weights() if r["name"] == BASELINE)
    w0 = weights_of(ref)
    m0 = sum(contributions(w0, walk, stand).values())
    out = []
    for term, value in PROBES:
        w = dict(w0, **{term: value})
        m = sum(contributions(w, walk, stand).values())
        slope = walk[term] - stand[term]
        edge = w0[term] + (stop_max - m0) / slope   # margin이 멈춘 회차 최고값에 닿는 가중치
        out.append({"term": term, "from": repr(w0[term]), "to": repr(value), "margin_from": f"{m0:.4f}",
                    "margin": f"{m:.4f}", "delta": f"{m - m0:+.4f}", "zone": zone(m, walk_min, stop_max),
                    "per_unit": f"{slope:.6g}", "edge_weight": f"{edge:.6g}",
                    "range_status": base.range_status(term, value) if term in base.TERMS else "NEVER_CHANGED"})
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 기울기 (평가 기록)
# ─────────────────────────────────────────────────────────────────────────────
def tilt_case(steps: Path) -> dict[str, str]:
    """로봇별 종료 전 기울기 식 값(1 − gz²) 평균, 종료 로봇의 종료 직전 창 평균."""
    ended: set[str] = set()
    total: dict[str, float] = {}
    count: dict[str, int] = {}
    history: dict[str, list[tuple[float, float]]] = {}
    end_time: dict[str, float] = {}
    terminated: set[str] = set()
    with steps.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            env = row["env_id"]
            if env in ended:
                continue
            t = float(row["time_s"])
            if row["term_base_contact"] == "1":
                terminated.add(env)
            if row["terminated"] == "1" or row["truncated"] == "1":
                ended.add(env)
                end_time[env] = t
                continue
            tilt = 1.0 - float(row["proj_grav_z"]) ** 2
            total[env] = total.get(env, 0.0) + tilt
            count[env] = count.get(env, 0) + 1
            window = history.setdefault(env, [])
            window.append((t, tilt))
            if len(window) > 60:        # 종료 직전 창에 필요한 1.2 s 분만 들고 다닌다
                window.pop(0)
    per_robot = {e: total[e] / count[e] for e in total}
    pre = {}
    for env in terminated:
        stop = end_time.get(env)
        rows = [v for t, v in history.get(env, []) if stop is not None and stop - PRE_TERM[0] <= t < stop - PRE_TERM[1]]
        if rows:
            pre[env] = statistics.mean(rows)
    survivors = [per_robot[e] for e in per_robot if e not in terminated]
    auc = ""
    if pre and survivors:
        wins = sum((a > b) + 0.5 * (a == b) for a in pre.values() for b in survivors)
        auc = f"{wins / (len(pre) * len(survivors)):.3f}"
    return {"robots": str(len(per_robot)), "terminated": str(len(terminated)),
            "tilt_mean": f"{statistics.mean(per_robot.values()):.5f}",
            "tilt_survivors": f"{statistics.mean(survivors):.5f}" if survivors else "",
            "tilt_pre_term": f"{statistics.mean(pre.values()):.5f}" if pre else "",
            "pre_term_auc": auc}


def tilt_rows() -> list[dict[str, str]]:
    out = []
    for folder, arm, name in TILT_ARMS:
        for case in TILT_CASES:
            for seed in SEEDS:
                steps = KEEP / folder / "evaluation" / arm / "cases" / f"seed_{seed}" / case / "steps.csv"
                if steps.is_file():
                    out.append({"name": name, "case": case, "seed": seed, **tilt_case(steps)})
    return out


def tilt_means(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, float]]:
    out: dict[tuple[str, str], dict[str, float]] = {}
    for key in {(r["name"], r["case"]) for r in rows}:
        group = [r for r in rows if (r["name"], r["case"]) == key]
        out[key] = {"tilt_mean": statistics.mean(float(r["tilt_mean"]) for r in group),
                    "terminated": sum(int(r["terminated"]) for r in group),
                    "robots": sum(int(r["robots"]) for r in group),
                    "seeds": len(group)}
        pre = [float(r["tilt_pre_term"]) for r in group if r["tilt_pre_term"]]
        surv = [float(r["tilt_survivors"]) for r in group if r["tilt_survivors"]]
        auc = [float(r["pre_term_auc"]) for r in group if r["pre_term_auc"]]
        if pre:
            out[key]["tilt_pre_term"] = statistics.mean(pre)
        if surv:
            out[key]["tilt_survivors"] = statistics.mean(surv)
        if auc:
            out[key]["pre_term_auc"] = statistics.mean(auc)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 상황별 구간 (2026-09-17 사용자 지시: "구간을 걷기로만 하지 말고 계단과 흔들림도 염두에 둬야 한다")
#   상황마다 '원하는 상태'와 '실패 상태'의 식 값을 평가 기록에서 직접 잰다.
#   평가 기록으로 잴 수 있는 항: 추종·회전 추종(오차 열, 원문 식 그대로), 수직 속도(root_z 차분 —
#   원문은 몸체 좌표라 근사), 기울기(proj_grav_z — 원문 식 그대로).  구르기 속도는 기울기 각의
#   변화 속도²로 **하한**만 잡는다(기울기 크기를 바꾸지 않는 회전은 빠진다).  관절·행동 항은 기록에 없다.
# ─────────────────────────────────────────────────────────────────────────────
SITUATION_POLICIES = (("Pilot-01", "go2_a017_full_suite", "pilot"), ("A017", "go2_a017_full_suite", "a017"),
                      ("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150", "candidate"))
SITUATION_TERMS = ("track_lin_vel_xy_exp", "track_ang_vel_z_exp", "lin_vel_z_l2", "flat_orientation_l2", "ang_vel_xy_l2")
UNMEASURED_IN_EVAL = ("action_rate_l2", "dof_torques_l2", "dof_acc_l2", "feet_air_time")
# 상황 → (원하는 상태, 실패 상태, 설명, 평가 영역)
SITUATIONS = {
    "climb": ("climb", "stall", "10cm 2단 이상 오른 구간 대 15cm 1단도 못 오르고 머문 구간", "G5 계단"),
    "sway": ("upright", "prefall", "험지 옆걸음 생존 로봇 대 넘어지기 `0.5~1.0` s 전", "G3 험지"),
    "push": ("upright", "prefall", "밀침 4 case 생존 로봇 대 넘어지기 `0.5~1.0` s 전", "G6 밀침"),
}
PUSH_CASES = ("push_pos_x", "push_neg_x", "push_pos_y", "push_neg_y")


def robot_tracks(steps: Path) -> dict[str, tuple[list[dict[str, str]], bool, float]]:
    """env → (종료·절단 전 행, 몸통 접촉 종료 여부, 끝난 시각)."""
    rows: dict[str, list[dict[str, str]]] = {}
    done: dict[str, tuple[bool, float]] = {}
    with steps.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            env = row["env_id"]
            if env in done:
                continue
            if row["terminated"] == "1" or row["truncated"] == "1":
                done[env] = (row["term_base_contact"] == "1", float(row["time_s"]))
                continue
            rows.setdefault(env, []).append(row)
    return {e: (r, *done.get(e, (False, float(r[-1]["time_s"])))) for e, r in rows.items()}


def window_values(rows: list[dict[str, str]], window: list[int]) -> dict[str, float]:
    """행 구간의 식 값 평균 (항 → 값)."""
    import go2_stairs_behavior as sb
    total = dict.fromkeys(SITUATION_TERMS, 0.0)
    for i in window:
        now, before = rows[i], rows[i - 1]
        gz, gz0 = float(now["proj_grav_z"]), float(before["proj_grav_z"])
        tilt, tilt0 = math.acos(max(-1.0, min(1.0, -gz))), math.acos(max(-1.0, min(1.0, -gz0)))
        total["track_lin_vel_xy_exp"] += math.exp(-float(now["error_xy"]) ** 2 / sb.TRACK_STD ** 2)
        total["track_ang_vel_z_exp"] += math.exp(-float(now["error_yaw"]) ** 2 / sb.TRACK_STD ** 2)
        total["lin_vel_z_l2"] += ((float(now["root_z"]) - float(before["root_z"])) / sb.STEP_DT) ** 2
        total["flat_orientation_l2"] += 1.0 - gz * gz
        total["ang_vel_xy_l2"] += ((tilt - tilt0) / sb.STEP_DT) ** 2
    return {t: v / len(window) for t, v in total.items()}


def situation_groups(folder: str, arm: str) -> dict[tuple[str, str], list[dict[str, float]]]:
    import go2_stairs_behavior as sb
    out: dict[tuple[str, str], list[dict[str, float]]] = collections.defaultdict(list)
    cases = {"stairs_10_down": 0.10, "stairs_15_down": 0.15, "rough_lateral": None,
             **dict.fromkeys(PUSH_CASES, None)}
    for case, height in cases.items():
        for seed in SEEDS:
            steps = KEEP / folder / "evaluation" / arm / "cases" / f"seed_{seed}" / case / "steps.csv"
            if not steps.is_file():
                continue
            for rows, fell, end in robot_tracks(steps).values():
                if len(rows) <= sb.SETTLE_ROW:
                    continue
                if height is not None:
                    x0, y0 = float(rows[0]["root_x"]), float(rows[0]["root_y"])
                    gained = sb.gained_steps(rows, "climb", height)
                    if case == "stairs_10_down" and gained >= 2:
                        z = [float(r["root_z"]) for r in rows]
                        top = max(range(len(z)), key=z.__getitem__)
                        window = [i for i in range(sb.SETTLE_ROW, top + 1) if sb.travelled(rows[i], x0, y0)]
                        key = ("climb", "climb")
                    elif case == "stairs_15_down" and gained < 1:
                        window, key = list(range(sb.SETTLE_ROW, len(rows))), ("climb", "stall")
                    else:
                        continue
                else:
                    situation = "sway" if case == "rough_lateral" else "push"
                    if fell:
                        window = [i for i, r in enumerate(rows) if i >= 1
                                  and end - PRE_TERM[0] <= float(r["time_s"]) < end - PRE_TERM[1]]
                        key = (situation, "prefall")
                    else:
                        window, key = list(range(sb.SETTLE_ROW, len(rows))), (situation, "upright")
                if window:
                    out[key].append(window_values(rows, window))
    return out


def situation_rows() -> list[dict[str, str]]:
    out = []
    for name, folder, arm in SITUATION_POLICIES:
        for (situation, group), robots in sorted(situation_groups(folder, arm).items()):
            out.append({"policy": name, "situation": situation, "group": group, "robots": str(len(robots)),
                        **{t: f"{statistics.mean(r[t] for r in robots):.6g}" for t in SITUATION_TERMS}})
    return out


def situation_diffs(rows: list[dict[str, str]], policy: str = BASELINE) -> dict[str, dict[str, float]]:
    """상황 → 항 → (원하는 상태 식 값 − 실패 상태 식 값)."""
    by = {(r["situation"], r["group"]): r for r in rows if r["policy"] == policy}
    out = {}
    for situation, (want, fail, _text, _axis) in SITUATIONS.items():
        if (situation, want) in by and (situation, fail) in by:
            out[situation] = {t: float(by[(situation, want)][t]) - float(by[(situation, fail)][t])
                              for t in SITUATION_TERMS}
    return out


def situation_margin(w: dict[str, float], diffs: dict[str, float]) -> float:
    """잴 수 있는 항만의 부분 margin — 양수면 보상 식이 원하는 상태를 더 높게 친다."""
    return sum(w[t] * diffs[t] for t in SITUATION_TERMS)


def flat_walk_slope(tilt: list[dict[str, str]]) -> float:
    """기울기 벌점 가중치 1당 걷기 margin 변화 [추정: 걷는 행동 값은 평가 기록]."""
    tm = tilt_means(tilt)
    walk = statistics.mean(tm[(BASELINE, c)]["tilt_mean"] for c in STAND_CASES)
    return walk - flat_stand_value()


MIN_GROUP_ROBOTS = 5   # 상황 방향 일치 판정에 넣을 최소 로봇 수(두 상태 모두)


def sign_agreement(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    """(상황, 항) → 세 정책에서 (원하는 − 실패) 부호가 같은가.  로봇이 적은 정책은 뺀다."""
    out = {}
    for situation, (want, fail, _text, _axis) in SITUATIONS.items():
        used = []
        for name, _folder, _arm in SITUATION_POLICIES:
            by = {r["group"]: r for r in rows if r["policy"] == name and r["situation"] == situation}
            if want in by and fail in by and min(int(by[want]["robots"]), int(by[fail]["robots"])) >= MIN_GROUP_ROBOTS:
                used.append(name)
        for term in SITUATION_TERMS:
            signs = {situation_diffs(rows, n)[situation][term] > 0 for n in used}
            label = "일치(+)" if signs == {True} else "일치(−)" if signs == {False} else "불일치"
            out[(situation, term)] = f"{label} {len(used)}정책"
    return out


FLAT_PROBES = (-0.5, -1.0, -2.5)


def probe_situations(probe_rows: list[dict[str, str]], sit_rows: list[dict[str, str]],
                     tilt: list[dict[str, str]]) -> list[dict[str, str]]:
    """PROBES 각 행 + 기울기 벌점 탐침 → 상황별 부분 margin 변화."""
    diffs = situation_diffs(sit_rows)
    ref = weights_of(next(r for r in base.weights() if r["name"] == BASELINE))
    ref_margins = {s: situation_margin(ref, d) for s, d in diffs.items()}
    out = []
    points = [(p["term"], float(p["to"]), float(p["delta"])) for p in probe_rows]
    points += [("flat_orientation_l2", v, (v - ref["flat_orientation_l2"]) * flat_walk_slope(tilt)) for v in FLAT_PROBES]
    for term, value, walk_delta in points:
        w = dict(ref, **{term: value})
        row = {"term": term, "to": repr(value), "walk_delta": f"{walk_delta:+.4f}"}
        for s, d in diffs.items():
            if term in UNMEASURED_IN_EVAL:
                row[f"{s}_delta"] = ""
            else:
                row[f"{s}_delta"] = f"{situation_margin(w, d) - ref_margins[s]:+.4f}"
        out.append(row)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 입출력
# ─────────────────────────────────────────────────────────────────────────────
def write(name: str, rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build(with_eval: bool = True) -> dict[str, list[dict[str, str]]]:
    """with_eval=False면 평가 기록(느림)은 다시 읽지 않고 저장된 TILT·SITUATIONS를 쓴다."""
    values = term_values()
    rows = run_margins(values)
    probe_rows = probes(values, rows)
    out = {"TERM_VALUES.csv": values, "RUN_MARGIN.csv": rows, "PROBES.csv": probe_rows}
    if with_eval:
        out["TILT.csv"] = tilt_rows()
        out["SITUATIONS.csv"] = situation_rows()
    tilt = out.get("TILT.csv") or read("TILT.csv")
    sit = out.get("SITUATIONS.csv") or read("SITUATIONS.csv")
    out["PROBE_SITUATIONS.csv"] = probe_situations(probe_rows, sit, tilt)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 보고서
# ─────────────────────────────────────────────────────────────────────────────
SHORT = {"track_lin_vel_xy_exp": "track", "track_ang_vel_z_exp": "track_ang", "lin_vel_z_l2": "lin_vel_z",
         "ang_vel_xy_l2": "ang_vel_xy", "action_rate_l2": "action_rate", "dof_torques_l2": "dof_torques",
         "dof_acc_l2": "dof_acc", "feet_air_time": "feet_air", "flat_orientation_l2": "flat_orient"}
ZONE_TEXT = {"WALK": "걷기 구간", "STOP": "정지 구간", "BAND": "경계대"}


def line_of(rel: str, needle: str) -> int:
    """인용하는 배포 파일 줄 번호 — 손으로 적지 않고 찾는다."""
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return next(i for i, line in enumerate(lines, 1) if needle in line)


def env_scalar(key: str) -> float:
    text = (KEEP / base.ROLE_ENV).read_text(encoding="utf-8")
    return float(next(line.split(":", 1)[1] for line in text.splitlines() if line.strip().startswith(key + ":")))


FLAT_STAND_RUN = "A013"   # 기울기 벌점을 켠 유일한 학습 회차(멈춤) — 멈춘 행동의 기울기 식 값을 로그에서 얻는다


def flat_stand_value() -> float:
    logs = {r["run"]: r for r in base.read("TRAINING_TERMS.csv")}
    row = next(r for r in base.weights() if r["name"] == FLAT_STAND_RUN)
    return float(logs[TRAIN_EXTRA[FLAT_STAND_RUN]]["flat_orientation_l2"]) / float(row["flat_orientation_l2"])


def stand_track_value(std: float, standing: float) -> float:
    """멈춘 로봇의 추종 식 기대값 — 명령 x∈U[−1,2], y∈U[−0.6,0.6](env.yaml), 정지 명령 비율 standing은 값 1."""
    def mean_exp(lo: float, hi: float) -> float:
        half = math.sqrt(math.pi) / 2 * std
        return half * (math.erf(hi / std) - math.erf(lo / std)) / (hi - lo)
    return (1 - standing) * mean_exp(-1.0, 2.0) * mean_exp(-0.6, 0.6) + standing


def findings(values, rows, probe_rows, tilt) -> dict:
    walk, stand = pools(values)
    walk_min, stop_max = band(rows)
    loo_min, loo_max = band(rows, "margin_loo")
    by = {r["name"]: r for r in rows}
    consistent = [r for r in rows if (r["zone"] == "WALK") == (r["walking"] == "True") and r["zone"] != "BAND"]
    band_rows = [r for r in rows if r["zone"] == "BAND"]
    wrong = [r for r in rows if r["zone"] != "BAND" and (r["zone"] == "WALK") != (r["walking"] == "True")]
    wrong_loo = [r for r in rows if r["zone_loo"] != "BAND" and (r["zone_loo"] == "WALK") != (r["walking"] == "True")]
    tm = tilt_means(tilt) if tilt else {}
    return {"walk": walk, "stand": stand, "walk_min": walk_min, "stop_max": stop_max,
            "loo_min": loo_min, "loo_max": loo_max, "by": by, "consistent": consistent,
            "band_rows": band_rows, "wrong": wrong, "wrong_loo": wrong_loo, "tilt": tm,
            "probes": probe_rows}


def f3(x: float) -> str:
    return f"{x:+.3f}"


def render(values=None, rows=None, probe_rows=None, tilt=None, sit=None, probe_sit=None) -> str:
    sit = sit if sit is not None else read("SITUATIONS.csv")
    probe_sit = probe_sit if probe_sit is not None else read("PROBE_SITUATIONS.csv")
    values = values if values is not None else read("TERM_VALUES.csv")
    rows = rows if rows is not None else read("RUN_MARGIN.csv")
    probe_rows = probe_rows if probe_rows is not None else read("PROBES.csv")
    tilt = tilt if tilt is not None else read("TILT.csv")
    F = findings(values, rows, probe_rows, tilt)
    walk, stand, by, tm = F["walk"], F["stand"], F["by"], F["tilt"]
    base_row = by[BASELINE]
    env = base.env_terms()
    std = float(env["rewards.track_lin_vel_xy_exp"]["std"])
    standing = env_scalar("rel_standing_envs")
    L: list[str] = []
    add = L.append
    add("# Go2 보상 기전으로 본 현재 상황과 변수 변경 예측")
    add("")
    add("> **생성 문서 — 손으로 고치지 않는다.** `python tools/go2_reward_mechanism.py`가 만든다.")
    add(f"> 증거: `reports/evidence/{OUT.name}/` (`TERM_VALUES.csv` · `RUN_MARGIN.csv` · `PROBES.csv` · `TILT.csv`). 관문: `tools/test_go2_reward_mechanism_contract.py`.")
    add("> 역할(원문 식): `reports/GO2_TUNING_BASE_DATA.md` §0-1. 한 항 변경 쌍의 등급: `reports/GO2_VARIABLE_INFLUENCE.md`.")
    add("")
    add("## 0. 추론 방법 (2026-09-17 사용자 지시: 원문 역할에 기반한 사실 추론으로 현재와 변경 결과를 예측한다)")
    add("")
    add("표기: [확인] 원문·산출물에서 직접 계산 · [추정] 확인된 사실에서 유추 · [모름] 근거 없음.")
    add("")
    add("1. [확인] 원문 보상 관리자는 매 step `식 × 가중치 × dt`를 더하고 로그 = 합의 평균 ÷ 20 s다. 그래서 **로그 ÷ 가중치 = 그 정책의 행동이 만든 식 값(초당)**이다.")
    add("2. [확인] 원문 식에서 제자리 로봇은 추종 항이 exp(−|명령|²/std²)로 줄고, 움직임 벌점(수직 속도·구르기 속도·행동 변화·관절 가속도·토크)이 작아진다.")
    add("3. 그러므로 가중치 w에서 **걷기 대 멈춤의 초당 보상 차이** `margin(w) = Σ w × (걷는 행동 식 값 − 멈춘 행동 식 값)`이다. "
        "음수면 보상 식이 멈춤을 더 높게 친다 — 정책이 멈춤으로 수렴할 이유가 식 안에 있다.")
    add(f"4. 걷는 행동 식 값 = 걷는 회차 학습 로그 ÷ 가중치의 평균, 멈춘 행동 = 학습 지형 레벨 0 회차의 평균. |로그| < `{MIN_LOG}`인 칸은 반올림 오차가 커서 뺀다.")
    add("5. [확인] 이 margin은 **가중치만의 1차식**이다. 계수(식 값 차이)는 로그에서 오고, 걷기/정지 결과에 맞춰 조정한 값이 없다. "
        "그래도 계수가 같은 회차들에서 나왔으므로, 그 회차를 빼고 다시 계산한 LOO margin을 함께 본다.")
    add("6. [추정] 걷기 margin은 **걷기가 보상상 유리한지**만 말한다. 계단·흔들림·밀침은 같은 방식의 **상황 margin**을 평가 기록에서 따로 잰다(§5-1). "
        "상황 margin = Σ w × (원하는 상태 식 값 − 실패 상태 식 값)이고, 평가 기록에 있는 항만 들어가는 **부분 margin**이다.")
    add("")
    add("### 0-1. 방법 검산 — 멈춘 로봇의 추종 식 값")
    add("")
    calc = stand_track_value(std, standing)
    add(f"원문 식과 env.yaml 명령 분포(x `−1~2`, y `−0.6~0.6` 균등, 정지 명령 비율 `{standing}`, std `{std}`)로 계산한 제자리 로봇의 추종 식 기대값은 "
        f"`{calc:.4f}`이다. 지형 레벨 0 회차들의 로그 ÷ 가중치 평균은 `{stand['track_lin_vel_xy_exp']:.4f}`다. "
        f"차이 `{stand['track_lin_vel_xy_exp'] - calc:+.4f}` — **로그 ÷ 가중치가 식 값으로 읽힌다는 것을 원문 식으로 확인했다** [확인].")
    add("")
    add("## 1. 행동별 식 값 (`TERM_VALUES.csv`)")
    add("")
    add("| 항 | 걷는 행동 식 값 | 멈춘 행동 식 값 | 차이 (가중치 1당 margin) | G-A033 가중치 | G-A033 기여 |")
    add("|---|---|---|---|---|---|")
    w33 = weights_of(next(r for r in base.weights() if r["name"] == BASELINE))
    for t in MARGIN_TERMS:
        add(f"| `{t}` | `{walk[t]:.6g}` | `{stand[t]:.6g}` | `{walk[t] - stand[t]:.6g}` | `{w33[t]!r}` | `{f3(float(base_row['part_' + t]))}` |")
    add("")
    add(f"G-A033 margin = `{float(base_row['margin']):+.4f}` (걷기 쪽 추종 이득 `{f3(float(base_row['part_track_lin_vel_xy_exp']))}`에서 벌점 증가분을 뺀 값).")
    add("")
    add("- [확인] 걷기로 **늘어나는** 보상은 `track` 하나뿐이다. 회전 추종(`track_ang`)은 걸을 때 오히려 줄고, 나머지 벌점은 모두 걸을 때 커진다.")
    parts = sorted(((t, float(base_row["part_" + t])) for t in MARGIN_TERMS if t != "track_lin_vel_xy_exp"), key=lambda x: x[1])
    add("- [확인] G-A033에서 걷기의 비용 순서: " + " · ".join(f"`{SHORT[t]}` `{f3(v)}`" for t, v in parts) + ".")
    add("")
    add("## 2. 걷기/정지 사후 대조 (`RUN_MARGIN.csv`, 학습 회차 전부)")
    add("")
    add("| 회차 | track | lin_vel_z | ang_vel_xy | action_rate | feet_air | flat_orient | margin | LOO margin | 구간 | 실제 | 험지 속도 |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    w_rows = {r["name"]: r for r in base.weights()}
    for r in sorted(rows, key=lambda r: float(r["margin"])):
        w = w_rows[r["name"]]
        add(f"| {r['name']} | " + " | ".join(f"`{w[t]}`" for t in base.TERMS)
            + f" | `{float(r['margin']):+.4f}` | `{float(r['margin_loo']):+.4f}` | {ZONE_TEXT[r['zone']]} | {'걷기' if r['walking'] == 'True' else '정지'} | {r['rough_forward_speed']} |")
    add("")
    add(f"- 구간 경계: 걷는 회차 최저 margin `{F['walk_min']:+.4f}`, 멈춘 회차 최고 margin `{F['stop_max']:+.4f}`. 그 사이가 경계대다.")
    add(f"- [확인] 경계대 밖 회차 {len(F['consistent']) + len(F['wrong'])}개 중 margin과 실제가 어긋난 회차: **{len(F['wrong'])}개**. "
        f"경계대 안 회차: " + ", ".join(f"{r['name']}({'걷기' if r['walking'] == 'True' else '정지'})" for r in F["band_rows"]) + ".")
    add(f"- [확인] LOO(그 회차를 빼고 식 값 평균을 다시 낸 것)로 해도 어긋난 회차는 **{len(F['wrong_loo'])}개**다. 경계대는 `{F['loo_min']:+.4f}` ~ `{F['loo_max']:+.4f}`로 넓어지고, "
        "그 안에 " + ", ".join(f"{r['name']}({'걷기' if r['walking'] == 'True' else '정지'})" for r in rows if r["zone_loo"] == "BAND")
        + "가 든다. Pilot-01의 LOO margin이 크게 내려가는 것은 Pilot이 걷는 행동 식 값 평균에서 빠지기 때문이다.")
    add("- [추정] 경계대의 폭은 **학습 seed 운**이 결과를 가르는 구간으로 읽는다. Pilot-01은 이 구간에서 걸었고, 같은 구간의 A018은 멈췄다.")
    add("- [모름] 이 대조는 이미 아는 결과에 대한 사후 대조다. 새 가중치에 대한 예측력은 새 회차로만 확인된다.")
    add("")
    add("## 3. 이전 실패의 기전")
    add("")
    add(f"기준 Pilot-01 margin `{float(by['Pilot-01']['margin']):+.4f}` — **걸은 회차 중 가장 낮다**. Pilot 위의 한 항 변경이 모두 무너진 이유가 여기서 읽힌다 [추정].")
    add("")
    add("| 회차 | 바꾼 것 | margin 변화 (Pilot 대비) | 가장 크게 움직인 항 | 구간 | 실제 |")
    add("|---|---|---|---|---|---|")
    pilot = by["Pilot-01"]
    for name, change in (("A015", "`feet_air` `0.2→0.35`"), ("A016", "`ang_vel_xy` `−0.05→−0.15`"),
                         ("A018", "`action_rate` `−0.01→−0.008`"), ("A017", "`track` `1.2→1.4`")):
        r = by[name]
        moved = max(MARGIN_TERMS, key=lambda t: abs(float(r["part_" + t]) - float(pilot["part_" + t])))
        add(f"| {name} | {change} | `{float(r['margin']) - float(pilot['margin']):+.4f}` | `{SHORT[moved]}` "
            f"`{float(r['part_' + moved]) - float(pilot['part_' + moved]):+.4f}` | {ZONE_TEXT[r['zone']]} | {'걷기' if r['walking'] == 'True' else '정지'} |")
    add("")
    add("- [확인] A016: 구르기 속도 벌점 3배 → 걷기 비용이 커져 margin이 정지 구간으로 내려갔다. 원문 식상 이 벌점은 걷는 동안의 몸통 흔들림에 걸리고 멈추면 거의 0이다.")
    add("- [확인] A015: 체공 threshold `0.5` s보다 짧은 걸음이 음수라 가중치를 올리면 걷는 쪽 벌점이 커진다. margin이 경계대 아래로 내려갔다.")
    add("- [추정] A018: 벌점을 **약하게** 했는데 margin은 올랐고 결과는 정지다. margin으로 설명되지 않는다 — 경계대 안의 seed 운 또는 체크포인트 차이(등급 C)로 읽는다.")
    stopped_children = [n for n in STOPPED_CHILDREN if by[n]["zone"] == "STOP"]
    add("- [확인] Default-01(배포 시작값 `lin_vel_z −3`·`ang_vel_xy −0.08`·`track 1.0`)과 chain01은 margin이 정지 구간이다. 그 위에서 한 항만 바꾼 "
        + "·".join(STOPPED_CHILDREN) + " 중 정지 구간에 남은 회차: " + ("·".join(stopped_children) or "없음")
        + " — 멈춘 기준에서 한 항 변경이 걷기를 만들지 못한 이유가 식에서 읽힌다.")
    add("- [확인] 배포 파일 주석도 같은 기전을 적고 있다: 명령 범위를 넓혔을 때 '추종 보상 ≈ 0 → 전진 포기 + 제자리 회전 국소최적'"
        f"(`go2_task/env_cfg.py` {line_of(ENV_CFG, '국소최적')}행).")
    add("")
    add("## 4. A033 기준값과 비교")
    add("")
    add("| 회차 | margin | 구간 | 험지 속도 | 경사 전진 m | 10cm 2단 이상 | 15cm 1단 이상 |")
    add("|---|---|---|---|---|---|---|")
    for name in ("Pilot-01", "A017", "A031", "A032", BASELINE):
        w = w_rows[name]
        add(f"| {name} | `{float(by[name]['margin']):+.4f}` | {ZONE_TEXT[by[name]['zone']]} | {w['rough_forward_speed']} | {w['slope_plus_20_progress_m']} | {w['climb10_ge2'] or '—'} | {w['climb15_ge1'] or '—'} |")
    add("")
    add(f"- [확인] G-A033은 **margin이 가장 큰 회차**다. margin을 올린 것은 `track` 하나이고(가중치 `0.1`당 `{(walk['track_lin_vel_xy_exp'] - stand['track_lin_vel_xy_exp']) * 0.1:+.4f}`), 걷는 회차에서 margin과 험지 속도가 같은 순서로 오른다.")
    add("- [추정] 그래서 A033은 걷기가 가장 안정적인 기준이다. 그러나 margin은 **어디서 넘어지는지**를 말하지 않는다. A033에서 track을 올린 대가로 험지 옆걸음 종료가 늘었다(`GO2_TUNING_BASE_DATA.md` §2-1, 등급 A).")
    add("")
    add("## 5. 기울기 식 값 — `flat_orientation_l2`의 예측 근거 (`TILT.csv`, 평가 `proj_grav_z`)")
    add("")
    add("| 정책 | case | seed | 로봇 | 종료 | 기울기 식 값 평균 (1 − gz²) | 생존 로봇 평균 | 종료 로봇의 종료 전 `0.5~1.0` s | AUC (종료 직전 > 생존 평균) |")
    add("|---|---|---|---|---|---|---|---|---|")
    for (name, case), v in sorted(tm.items(), key=lambda kv: (kv[0][0] != BASELINE, TILT_CASES.index(kv[0][1]))):
        add(f"| {name} | {case} ({CASE_LABEL.get(case, case)}) | {v['seeds']} | {v['robots']} | {v['terminated']} | `{v['tilt_mean']:.4f}` "
            f"| `{v.get('tilt_survivors', float('nan')):.4f}` | " + (f"`{v['tilt_pre_term']:.4f}`" if "tilt_pre_term" in v else "—")
            + " | " + (f"`{v['pre_term_auc']:.3f}`" if "pre_term_auc" in v else "—") + " |")
    add("")
    if tm:
        walk_tilt = statistics.mean(tm[(BASELINE, c)]["tilt_mean"] for c in STAND_CASES)
        eval_stand_tilt = statistics.mean(tm[("chain01", c)]["tilt_mean"] for c in STAND_CASES)
        train_stand_tilt = flat_stand_value()
        slope = tm[(BASELINE, "slope_plus_20")]["tilt_mean"]
        lateral = tm[(BASELINE, "rough_lateral")]
        stairs15 = tm[(BASELINE, "stairs_15_down")]
        add(f"- [확인] 멈춘 행동의 기울기 식 값: 학습 로그 {FLAT_STAND_RUN}(기울기 벌점 `−1`, 정지) `{train_stand_tilt:.3f}`. "
            f"평가의 멈춘 chain01은 `{eval_stand_tilt:.4f}`로 훨씬 크다 — 평가에서는 몸을 낮춰 기운 채 멈추기 때문이다. 학습 조건 값인 {FLAT_STAND_RUN}을 쓴다.")
        add(f"- [추정] 걷는 행동의 기울기 식 값은 학습 로그에 없다(걷는 회차 가중치가 모두 0). 평가 G-A033 평지·험지 전진 값 `{walk_tilt:.4f}`로 대신하면 "
            f"기울기 벌점 가중치 −1당 margin 변화는 `{-(walk_tilt - train_stand_tilt):+.4f}`다 — **걷기/정지 판단을 크게 흔들지 않는다**.")
        add(f"- [확인] 오르막 20°의 기울기 식 값은 `{slope:.4f}`이다. 가중치 w면 그 case에서 초당 `{slope:.4f}`×|w|의 상시 벌점이고, track `1.5` 최대 보상 대비 `{slope / 1.5:.1%}`×|w|다 [확인: 산수].")
        add(f"- [확인] 험지 옆걸음: 종료 로봇의 종료 전 `0.5~1.0` s 기울기 식 값 `{lateral['tilt_pre_term']:.4f}` 대 생존 로봇 평균 `{lateral['tilt_survivors']:.4f}`, AUC `{lateral['pre_term_auc']:.3f}`. "
            "**옆으로 넘어지기 `0.5` s 전에 이미 기울어 있다** — 기울기 벌점은 뒤집힘 앞 단계에 걸리는 식이다.")
        add(f"- [확인] 반면 15cm 오르기 종료 로봇은 종료 전 기울기 `{stairs15['tilt_pre_term']:.4f}`로 생존 로봇 `{stairs15['tilt_survivors']:.4f}`보다 크지 않다(AUC `{stairs15['pre_term_auc']:.3f}`, 종료 {stairs15['terminated']}대). "
            "G5의 손실은 넘어짐이 아니라 멈춤이다(기반 데이터 §6-2) — 기울기 벌점은 G5를 겨냥하지 않는다.")
        add("- [추정] G-A033만 보면 `flat_orientation_l2`는 옆 뒤집힘 앞 단계에 걸리고 걷기 margin을 크게 흔들지 않는다. 그러나 세 정책을 함께 보면 흔들림에서 부호가 엇갈린다(§5-1) — "
            "G3 레버로서의 근거는 구르기 속도 벌점보다 약하다. 대가는 경사·계단에서의 상시 벌점이다. Isaac Lab이 험지 설정에서 끈 이유는 원문에 적혀 있지 않다 [모름].")
    add("")
    add("## 5-1. 상황별 구간 — 계단·흔들림·밀침 (`SITUATIONS.csv`, 2026-09-17 사용자 지시: 걷기만이 아니라 계단과 흔들림도 본다)")
    add("")
    add("평가 기록(seed 101/202/303)에서 상황마다 **원하는 상태**와 **실패 상태**의 식 값을 잰다. 잴 수 있는 항은 다음과 같다.")
    add("- 원문 식 그대로: 추종(`error_xy`), 회전 추종(`error_yaw`), 기울기(`proj_grav_z`)")
    add("- 근사: 수직 속도 — `root_z` 차분(월드 좌표). 원문은 몸체 좌표다.")
    add("- 하한: 구르기 속도 — 기울기 각의 변화 속도². 기울기 크기를 바꾸지 않는 회전은 빠진다.")
    add("- **잴 수 없음:** " + ", ".join(f"`{t}`" for t in UNMEASURED_IN_EVAL) + " — 평가 기록에 관절·행동·접지 열이 없다.")
    add("")
    add("| 상황 | 원하는 상태 | 실패 상태 | 평가 영역 |")
    add("|---|---|---|---|")
    for situation, (want, fail, text, axis) in SITUATIONS.items():
        add(f"| {situation} | {want} | {fail} | {axis} — {text} |")
    add("")
    add("| 정책 | 상황 | 상태 | 로봇 | " + " | ".join(f"`{SHORT[t]}`" for t in SITUATION_TERMS) + " |")
    add("|---|---|---|---|" + "---|" * len(SITUATION_TERMS))
    for r in sit:
        add(f"| {r['policy']} | {r['situation']} | {r['group']} | {r['robots']} | " + " | ".join(f"`{float(r[t]):.4f}`" for t in SITUATION_TERMS) + " |")
    add("")
    diffs = situation_diffs(sit)
    agree = sign_agreement(sit)
    w_ref = weights_of(next(r for r in base.weights() if r["name"] == BASELINE))
    add(f"G-A033의 (원하는 − 실패) 식 값 차이와 세 정책의 부호 일치(두 상태 모두 로봇 `{MIN_GROUP_ROBOTS}`대 이상인 정책만):")
    add("")
    add("| 항 | " + " | ".join(f"{s} 차이 | {s} 일치" for s in diffs) + " |")
    add("|---|" + "---|---|" * len(diffs))
    for term in SITUATION_TERMS:
        add(f"| `{SHORT[term]}` | " + " | ".join(f"`{diffs[s][term]:+.4f}` | {agree[(s, term)]}" for s in diffs) + " |")
    add("")
    add("G-A033 가중치의 상황 부분 margin: " + " · ".join(f"{s} `{situation_margin(w_ref, d):+.4f}`" for s, d in diffs.items())
        + " (양수 = 보상 식이 원하는 상태를 더 높게 친다).")
    add("")
    c, s_, pu = diffs["climb"], diffs["sway"], diffs["push"]
    add(f"- [확인] **계단:** 오르는 로봇이 추종을 더 받고(`{c['track_lin_vel_xy_exp']:+.4f}`) 수직 속도·기울기 변화가 크다"
        f"(`{c['lin_vel_z_l2']:+.4f}`, `{c['ang_vel_xy_l2']:+.4f}`). 잴 수 있는 항만으로는 G-A033이 오르기를 `{situation_margin(w_ref, c):+.4f}` 더 높게 친다. "
        "그런데도 15cm 앞에서 멈춘다 — [추정] 멈춤의 원인은 잴 수 없는 항(관절 가속도·토크·행동 변화)이나 커리큘럼 쪽에 있다.")
    add(f"- [확인] **계단의 기울기:** G-A033에서는 멈춘 로봇이 더 기울어 있다(차이 `{c['flat_orientation_l2']:+.4f}`). 그러나 부호가 **{agree[('climb', 'flat_orientation_l2')]}** — "
        "기울기 벌점이 오르기를 돕는다고 말할 근거가 되지 않는다.")
    add(f"- [확인] **흔들림(험지 옆걸음):** 넘어지기 직전 상태는 기울기(`{s_['flat_orientation_l2']:+.4f}`)·구르기 속도 하한(`{s_['ang_vel_xy_l2']:+.4f}`)·수직 속도(`{s_['lin_vel_z_l2']:+.4f}`)가 모두 크다. "
        f"세 항의 부호 일치: {agree[('sway', 'flat_orientation_l2')]} · {agree[('sway', 'ang_vel_xy_l2')]} · {agree[('sway', 'lin_vel_z_l2')]}. "
        f"추종은 {agree[('sway', 'track_lin_vel_xy_exp')]} — track이 흔들림을 막는지는 정책마다 다르다.")
    add(f"- [확인] **밀침:** 넘어지기 직전 상태의 기울기(`{pu['flat_orientation_l2']:+.4f}`)·구르기 속도 하한(`{pu['ang_vel_xy_l2']:+.4f}`)이 크다. 부호 일치: "
        f"{agree[('push', 'flat_orientation_l2')]} · {agree[('push', 'ang_vel_xy_l2')]}.")
    add("- [추정] 넘어지기 직전 창은 넘어지는 동작 자체를 포함한다. 벌점이 그 상태를 싫어하게 만드는 것은 식에서 확인되지만, 그것으로 넘어짐이 줄어드는지는 학습 결과로만 확인된다.")
    add("")
    add("## 6. 변수 변경 예측 — G-A033에서 한 항만 바꿀 때 (`PROBES.csv`)")
    add("")
    add("| 항 | G-A033 값 → 바꾼 값 | 관측 위치 | margin | 변화 | 구간 | 걷기 구간을 벗어나는 가중치 |")
    add("|---|---|---|---|---|---|---|")
    for p in probe_rows:
        add(f"| `{p['term']}` | `{p['from']}` → `{p['to']}` | `{p['range_status']}` | `{float(p['margin']):+.4f}` | `{p['delta']}` | {ZONE_TEXT[p['zone']]} | `{p['edge_weight']}` |")
    add("")
    add("- 걷기 구간을 벗어나는 가중치 = G-A033 margin이 멈춘 회차 최고 margin까지 내려가는 값(1차식). 이 값보다 벌점을 강하게(또는 track을 낮게) 하면 경계대에 들어간다 [추정].")
    add("- [확인] A017(`track 1.4`)은 이 표에서 걷기 구간이고 실제로 걸었다. `ang_vel_xy −0.15`는 정지 구간이고, Pilot 위의 같은 값(A016)은 실제로 멈췄다.")
    add("")
    add("### 6-0. 네 구간 함께 보기 (`PROBE_SITUATIONS.csv`)")
    add("")
    add("걷기는 학습 로그 margin 변화, 계단·흔들림·밀침은 §5-1 부분 margin 변화다(G-A033 대비, 양수 = 원하는 상태 쪽). 빈칸은 평가 기록으로 잴 수 없는 항이다. "
        "`flat_orientation_l2`의 걷기 변화는 평가 기울기로 대신한 [추정]이다.")
    add("")
    add("| 항 | 바꾼 값 | 걷기 | 계단 | 흔들림 | 밀침 | 나빠지는 구간 |")
    add("|---|---|---|---|---|---|---|")
    walk_zone = {(p["term"], p["to"]): p["zone"] for p in probe_rows}
    for q in probe_sit:
        cells = [q["walk_delta"], q["climb_delta"], q["sway_delta"], q["push_delta"]]
        worse = [n for n, v in zip(("걷기", "계단", "흔들림", "밀침"), cells) if v and float(v) < 0]
        zone_here = walk_zone.get((q["term"], q["to"]), "WALK")
        if zone_here != "WALK":
            worse = [f"걷기({ZONE_TEXT[zone_here]})"] + [n for n in worse if n != "걷기"]
        shown = [f"`{cells[0]}`"]
        for s, v in zip(("climb", "sway", "push"), cells[1:]):
            mark = "†" if v and agree.get((s, q["term"]), "").startswith("불일치") else ""
            shown.append(f"`{v}`{mark}" if v else "측정 없음")
        add(f"| `{q['term']}` | `{q['to']}` | " + " | ".join(shown) + f" | {'·'.join(worse) or '없음'} |")
    add("")
    add("† 그 항의 (원하는 − 실패) 부호가 세 정책에서 엇갈린다(§5-1). G-A033 한 정책의 행동으로 계산한 값이라 예측 근거로 쓰지 않는다. "
        "특히 `track`의 흔들림 칸은 등급 A 쌍의 실측(`1.4→1.5`에서 험지 옆걸음 종료 증가, 기반 데이터 §2-1)과 **반대 방향**이다 — 실측을 따른다.")
    add("")
    add("### 6-1. 항별 예측 (역할 → 걷기 margin → 평가 영역)")
    add("")
    pr = {(p["term"], p["to"]): p for p in probe_rows}
    climb_src = {(r["group"], r["case"]): r for r in base.read("CLIMB_REWARD.csv") if (r["run"], r["arm"]) == base.CLIMB_OF[BASELINE]}
    climb = {"climb": climb_src[("climb", "stairs_10_down")], "stall": climb_src[("stall", "stairs_15_down")]}
    climb_net = float(climb["climb"]["sum_rate"]) - float(climb["stall"]["sum_rate"])
    add(f"- **`track_lin_vel_xy_exp`** — 역할: 명령 속도 추종 보상. margin `1.6`에서 `{float(pr[('track_lin_vel_xy_exp', '1.6')]['margin']):+.4f}`(걷기 더 안정). "
        "평가 영역: 등급 A 쌍에서 `1.4→1.5`가 평지·경사·험지 전진을 올리고 옆걸음·밀침·10cm 오르기 종료를 늘렸다. [추정] `1.6`은 같은 방향이 이어진다 — G3 손실이 커질 쪽이다. Isaac Lab Go2 rough 값이 `1.5`다.")
    add(f"- **`lin_vel_z_l2`** — 역할: 수직 속도 벌점(올라서기 포함). `−1.0`에서 margin `{float(pr[('lin_vel_z_l2', '-1.0')]['margin']):+.4f}`(걷기 구간 유지). "
        f"평가 영역: 계단 오르기 비용이 줄어든다[확인: 식]. 그러나 기반 데이터 §3 오르기 보상률에서 G-A033 10cm 오른 로봇은 추종 `{climb['climb']['track_rate']}` 대 15cm 정지 `{climb['stall']['track_rate']}`, "
        f"수직 벌점 `{climb['climb']['lin_vel_z_rate']}` 대 `{climb['stall']['lin_vel_z_rate']}` — 오르는 쪽이 이 두 항 합으로 이미 `{climb_net:+.3f}` 유리하다. "
        "[추정] 15cm 정지를 푸는 주 레버라는 근거는 약하다. "
        "`−3.0`은 margin을 낮춘다(배포 시작값 계열이 전부 정지).")
    add(f"- **`ang_vel_xy_l2`** — 역할: 구르기·끄덕임 **속도** 벌점. `−0.08`에서 margin `{float(pr[('ang_vel_xy_l2', '-0.08')]['margin']):+.4f}`, `−0.1`에서 `{float(pr[('ang_vel_xy_l2', '-0.1')]['margin']):+.4f}`, "
        f"걷기 구간 경계 `{pr[('ang_vel_xy_l2', '-0.08')]['edge_weight']}`. [추정] 옆으로 뒤집히는 **속도**를 줄일 수 있으나 걷기 비용 둘째 항이라 강화 여유가 작다.")
    add(f"- **`dof_acc_l2`** — 역할: 관절 가속도 벌점. **G-A033 걷기 비용 1위이고 한 번도 바꾼 적이 없다.** 절반(`−1.25e-07`)이면 margin `{float(pr[('dof_acc_l2', '-1.25e-07')]['margin']):+.4f}`, 두 배(`−5e-07`)면 `{float(pr[('dof_acc_l2', '-5e-07')]['margin']):+.4f}`. "
        "[추정] 약하게 하면 빠른 다리 동작(계단 턱에서 발 올리기)이 싸진다. 평가 영역 효과는 [모름] — 측정 없음. "
        f"배포 파일의 `REWARD_WEIGHTS`는 env에 있는 항이면 이름으로 가중치를 바꾼다(`go2_task/env_cfg.py` {line_of(ENV_CFG, 'attr.weight = float(weight)')}행) [확인]. "
        "단 배포 안내 목록(`quadruped_rewards.py`)에는 없는 항이라 R-6 해석은 사용자 결정이다 [모름].")
    add(f"- **`dof_torques_l2`** — 역할: 관절 토크 벌점. 절반이면 margin `{float(pr[('dof_torques_l2', '-0.0001')]['margin']):+.4f}`. [추정] 오르기의 큰 토크가 싸진다. 측정 없음 [모름].")
    add(f"- **`action_rate_l2`** — 역할: 행동 변화 벌점. `−0.02`면 margin `{float(pr[('action_rate_l2', '-0.02')]['margin']):+.4f}`. A018(약화)은 margin과 반대로 멈췄다 — 이 항은 margin 예측을 믿기 어렵다 [추정].")
    add(f"- **`feet_air_time`** — 역할: 체공 `0.5` s 기준의 짧은 걸음 벌점(발 높이 아님). `0.35`면 margin `{float(pr[('feet_air_time', '0.35')]['margin']):+.4f}`. "
        "배포 안내의 '발을 높이 들어 험지 돌파'는 원문 식과 다르다 [확인: 식]. 등급 A 쌍에서 `0.01`로 내리면 오르막 전진이 크게 줄었다.")
    add("- **`flat_orientation_l2`** — 역할: 기울어진 **각도** 벌점. 걷기 margin 영향 작음(§5), 밀침에서는 넘어지기 직전 상태를 일관되게 더 벌하지만 흔들림·계단에서는 정책마다 방향이 다름(§5-1), 경사에서 상시 벌점 [추정].")
    add("")
    add("## 7. 이 추론의 한계")
    add("")
    add("- 식 값은 정책이 가중치에 맞춰 바꾼 **결과**다. 가중치를 바꾸면 걷는 행동의 식 값도 바뀐다 — margin 1차식은 작은 변경에서만 근사다 [추정].")
    add("- 학습 로그는 소수 3자리이고, 지형 레벨 평균이 회차마다 달라 식 값에 지형 차이가 섞인다.")
    add("- 걷기 margin은 필요조건에 가깝다. 경계대 위라도 커리큘럼·seed에 따라 멈출 수 있고(A018), 걷기 구간이어도 계단·옆걸음 성공은 보장하지 않는다.")
    add("- 기울기 식 값은 평가 조건(고정 지형·명령)에서 잰 값이다. 학습 중 값과 다르다.")
    add("- 상황 margin은 평가 기록에 있는 항만 넣은 부분 margin이다. 계단 오르기의 관절 비용(가장 큰 걷기 비용 항)이 빠져 있어, 계단 부분 margin이 양수여도 오르기가 보상상 유리하다고 결론 내리지 않는다.")
    add("- 상황 식 값은 G-A033 한 정책의 행동이다. 부호가 세 정책에서 불일치하는 항은 예측 근거로 쓰지 않는다.")
    add(f"- 학습 seed는 전 회차 42다. 배포 파일은 '같은 seed라도 cudnn 비결정성으로 매번 조금씩 다르다'고 적지만(`quadruped_rewards.py` {line_of(REWARDS_PY, 'cudnn')}행), "
        "이 스택에서 같은 설정·같은 seed 재학습 2쌍은 결과가 같았다 — 흔들림의 원천은 학습 seed와 한 항 변경의 궤적 갈라짐이고, 둘 다 측정된 적이 없다(`reports/GO2_SEED_SENSITIVITY.md`).")
    add("- **계단 부분 margin은 크기를 예측하지 못한다(§9, G-A038).** 방향만 쓴다.")
    add("")
    add("## 8. 향후 튜닝 정책")
    add("")
    add("1. **변수를 고르기 전에 세 가지를 적는다:** 원문 역할(기반 데이터 §0-1) → 네 구간 예측(걷기·계단·흔들림·밀침, 이 문서 §6-0; 새 값이면 `tools/go2_reward_mechanism.py`로 계산) → 겨냥 영역의 원자료 행.")
    add(f"2. **네 구간 관문:** G-A033 위의 후보는 예측 걷기 margin이 멈춘 회차 최고값 `{F['stop_max']:+.4f}`보다 커야 한다(걷기 구간). "
        "계단·흔들림·밀침 부분 margin이 나빠지는 후보는 그 구간을 사양에 적고 이유를 적어야 한다(`base_data.walk_margin.worse`·`reason`, 관문 검사). "
        "경계대·정지 구간이나 이유 없는 악화 후보는 만들지 않는다.")
    add("3. **track은 `1.5`에서 멈춘다.** margin은 더 오르지만 등급 A 쌍에서 G3·G6 종료가 늘었고, G3는 이미 G5와 함께 가장 큰 손실 영역이다(`GO2_NOW.md` §1 최대 손실).")
    penalties = ("lin_vel_z_l2", "ang_vel_xy_l2", "flat_orientation_l2")
    steady = [t for t in penalties if agree[("sway", t)].startswith("일치(−)")]
    shaky = [t for t in penalties if agree[("sway", t)].startswith("불일치")]
    pa = {(q["term"], q["to"]): q for q in probe_sit}
    ang = pa[("ang_vel_xy_l2", "-0.08")]
    add("4. **G3(험지 옆 뒤집힘)·G6(밀침) 후보 — 세 정책에서 부호가 일치하는 벌점부터.** 흔들림에서 넘어지기 직전 상태를 일관되게 더 벌하는 항: "
        + ", ".join(f"`{t}`" for t in steady) + "; 부호가 엇갈리는 항: " + (", ".join(f"`{t}`" for t in shaky) or "없음") + "(§5-1).")
    add(f"   - **`ang_vel_xy_l2` `−0.08`은 G-A038로 실행됐고, 단독 레버로 다시 쓰지 않는다(2026-09-17).** 예측은 걷기 유지(margin 변화 `{ang['walk_delta']}`)·흔들림 `{ang['sway_delta']}`·밀침 `{ang['push_delta']}` 상승·계단 `{ang['climb_delta']}`였다. "
        "방향은 셋 다 맞았지만 10cm 오르기가 무너졌다(§9). 이 항과 `lin_vel_z_l2`는 계단과 흔들림·밀침의 부호가 반대인 **맞교환 항**이라, 계단 부분 margin의 작은 값으로 계단 비용을 판단하지 않는다.")
    add("   - `lin_vel_z_l2` 강화도 흔들림·밀침을 돕지만 걷기·계단을 함께 낮춘다 — G5를 목표에서 빼지 않는 한 쓰지 않는다.")
    add("   - `flat_orientation_l2`는 밀침에서만 부호가 일치하고 흔들림·계단은 엇갈린다. 경사 G4 상시 벌점(§5)도 있어 2순위다.")
    add("5. **G5(15cm 오르기) 후보:** 한 번도 바꾸지 않은 최대 비용 항 `dof_acc_l2`를 약하게 하는 것이 역할상 가장 직접적이다(빠른 발 올리기 비용). 단 계단·흔들림·밀침 구간 효과는 **측정 없음**이다 — 걷기 구간 안에서 정보 측정으로 한다. "
        "`lin_vel_z_l2` 약화(G-A037)는 계단 부분 margin을 올리지만 **흔들림·밀침 부분 margin을 낮춘다**(§6-0) — 넘어지기 직전의 튀는 움직임 벌점이 줄어서다. G3·G6 보호 판정 없이 올리지 않는다.")
    add("6. **하지 않는 것:** `feet_air_time` 인상(짧은 걸음 벌점 강화, margin 하락), `ang_vel_xy_l2` 경계 밖 강화, 배포 시작값(`lin_vel_z −3`·`ang_vel_xy −0.08`) 복귀, track `1.5` 초과.")
    add("7. **대조군:** 후보와 같은 묶음에 G-A033 seed 반복을 넣는다. margin 경계대의 폭이 seed 운이라는 [추정]을 여기서 확인한다.")
    add("8. **결과 회수 후:** 새 회차는 먼저 `HELD_OUT`에 넣어 §9에서 예측과 대조한다. 대조를 기록한 뒤에만 계수(`TRAIN_EXTRA`)에 합친다. 예측과 실제가 어긋나면 이 정책부터 고친다.")
    add("9. **판정과 후보 선정은 이 문서 밖의 규칙을 따른다(2026-09-17, G-D-FACT-RULES-20260917):** 판정 `fact_rules_v1`(`tools/go2_fact_rules.py`), 후보는 사실 근거 추론 사슬(MASTER §5-3). 이 문서의 margin은 사슬의 한 고리(방향)일 뿐 이득 추정이 아니다.")
    add("")
    render_held_out(add, probe_sit, pr)
    return "\n".join(L)


def render_held_out(add, probe_sit, pr) -> None:
    """§9 사후 대조 — 예측을 쓴 뒤 학습한 회차의 결과."""
    add("## 9. 사후 대조 — 예측 뒤에 학습한 회차 (계수에 넣지 않음)")
    add("")
    add("| 회차 | 바꾼 값 | 예측 걷기 구간 | 평지 전진 속도 (G-A033 → 회차) | 상황 | 예측 부분 margin 변화 | 관측 표적 묶음 proxy 변화 | 방향 |")
    add("|---|---|---|---|---|---|---|---|")
    for work, term, to, folder in HELD_OUT:
        ev = QUAD / folder
        with (ev / "FORECAST_CHECK.csv").open(encoding="utf-8", newline="") as handle:
            check = list(csv.DictReader(handle))
        with (ev / "FLAT_NOMINAL.csv").open(encoding="utf-8", newline="") as handle:
            flat = {r["arm"]: r for r in csv.DictReader(handle)}
        speed = f"`{float(flat['G-A033']['speed_xy_mean']):.3f}` → `{float(flat[work]['speed_xy_mean']):.3f}`"
        for i, r in enumerate(check):
            head = (f"| {work} | `{term}` `{to}` | {ZONE_TEXT[pr[(term, to)]['zone']]} | {speed} |" if i == 0
                    else "| | | | |")
            add(f"{head} {r['zone']} | `{r['forecast_partial_margin_delta']}` | `{float(r['observed_mean_proxy_delta']):+.3f}` | "
                + ("같음" if r["direction_agrees"] == "True" else "반대") + " |")
    add("")
    add("- [확인] G-A038은 예측대로 걸었고(걷기 구간), 세 상황의 방향도 맞았다.")
    add("- [확인] 계단은 크기가 틀렸다. 예측은 작은 하락이었고, 실제는 10cm 오르기에서 세 seed 모두 32대 전부가 자세 낙상으로 잡혔고, 한 단 이상 오른 로봇은 G-A033 `90`대에서 `5`대로 줄었다(`reports/GO2_G_A038_READOUT.md` §3, `reports/evidence/go2_seed_sensitivity_20260917/ONE_CHANGE_DRIFT.csv`).")
    add("- [추정] 부분 margin은 평가 기록에 있는 항만 넣은 값이고 구르기 속도는 하한이다(§5-1). 오르기에 필요한 몸통 회전의 비용이 과소평가됐다.")
    add("- [확인] G-A038은 지형 레벨도 G-A033보다 크게 낮았다. 같은 `track`에서 지형 레벨이 갈렸으므로 다이얼 모델은 반박됐다(`tools/go2_dial_model.py`).")
    add("- [확인] **G-A043에서는 네 상황 중 둘이 방향까지 틀렸다.** 산수는 흔들림 `-0.0470`·밀침 `-0.0386`으로 악화를 예측했는데, 실제 험지 옆걸음 proxy는 `+0.296`, 밀침 네 방향은 `+0.056`·`+0.013`·`+0.037`·`-0.010`이었다(`reports/evidence/go2_g_a043_readout_20260922/FORECAST_CHECK.csv`). 걷기·계단 방향만 맞았다.")
    add("- [확인] G-A043의 실제 손실은 이 표에 **칸이 없다** — 평지 복합 우회전(G2 `combined_yaw_right`, 세 seed 전부 생존 하락)이고, 네 구간은 그 상황을 모형화하지 않는다(`reports/evidence/go2_a043_scenario_split_20260922/CASE_DELTAS.csv`).")
    add("- [추정] 두 사실을 합치면, 부분 margin은 **크기뿐 아니라 방향도** 이 다이얼에서는 근거가 되지 못한다. `lin_vel_z_l2`의 다음 값은 부분 margin이 아니라 관측된 두 끝점(`-2.0`·`-1.5`)으로 고른다(§8).")
    add("")


def main(argv: list[str]) -> int:
    if "--report" not in argv:
        for name, rows in build().items():
            write(name, rows)
    DOC.write_text(render(), encoding="utf-8", newline="\n")
    print(DOC)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
