"""Go2 계단·실패 동작 판독 — `_keep` 원시 기록에서만 계산한다.

왜 있는가.  계단 진단이 세 번 틀렸다.  case 이름을 믿었고(“down”은 실제로 오르기),
높이 게이트의 “낙상”을 동작으로 읽었고, seed 하나짜리 한 쌍을 레버 방향으로 썼다.
세 번 모두 로봇별 궤적을 보지 않고 이름·집계에서 결론을 냈다.  이 도구는 그 궤적을
파일로 남겨, 다음 진단이 같은 자리에서 시작하게 한다.

산출 (reports/evidence/go2_stairs_behavior_20260916/):
  전역 진실 집합(reports/runs)에 넣지 않는다.  3자리 소수 수백 개가 들어가면 다른 문서의
  근거 없는 숫자가 우연히 통과한다(2026-09-16 실측 11건).  이 CSV는 분석 문서 하나에만
  `go2_claim_check.DOC_SOURCES` 로 묶는다.
  STAIRS_CLIMB.csv     case × seed 별 지형 방향과 몸통 상승 계단 수 분포
  CASE_BEHAVIOR.csv    case × seed 별 속도·몸 높이·종료·자세 낙상·전진 거리
  TRAINING_TERMS.csv   학습 로그 마지막 10 iter 평균 (보상 항·종료·레벨·속도 오차)
  CLIMB_REWARD.csv     오르기·정지·평지 구간의 추종 보상률과 수직 속도 벌점률 (A033 가중치)
  WEIGHT_OUTCOME.csv   회차별 reward 가중치 대 험지 속도·경사 전진·오르기 수
  LATERAL_BEHAVIOR.csv 험지 옆걸음·험지 전진·평지 옆걸음의 종료 시점·기울기·질량·속도

방향 판정은 이름이 아니라 데이터다: 출발 지형 높이가 양수면 꼭대기 출발(내려가기),
음수면 구덩이 출발(오르기).  Isaac Lab v2.3.1 `mesh_terrains.py` 145행(피라미드
origin z = +(n+1)h)과 245행(역피라미드 origin z = -(n+1)h)과 같은 규칙이다.

사용: python tools/go2_stairs_behavior.py
"""
from __future__ import annotations

import collections
import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_stairs_behavior_20260916"
sys.path.insert(0, str(ROOT / "tools"))

import go2_climb_count as climb  # noqa: E402
import tfcurve  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "candidate_suite_checks", ROOT / "workspace/training/quadruped/candidate_suite_checks.py")
_checks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_checks)


def reward_weights(path: Path) -> dict:
    return _checks.reward_weights(path.read_text(encoding="utf-8"))


A033_ENV = KEEP / "go2_g_a033_a017_track_lin_vel_xy_150/training/env.yaml"
CLIMB_POLICIES = (("go2_a017_full_suite", "pilot"), ("go2_a017_full_suite", "a017"),
                  ("go2_g_a033_a017_track_lin_vel_xy_150", "candidate"))
TRACK_STD = 0.5         # A033 env.yaml track_lin_vel_xy_exp params.std
STEP_DT = 0.02          # 평가 steps.csv time_s 간격

SEEDS = ("101", "202", "303")
STAIR_CASES = climb.STAIR_HEIGHTS
BEHAVIOR_CASES = ("forward_nominal", "rough_forward", "rough_lateral", "slope_plus_20",
                  "slope_minus_20", "stairs_10_up", "stairs_10_down", "stairs_15_up",
                  "stairs_15_down")
# 계단 수 세기 규칙은 서버 게이트·로컬 검증기와 한 곳에서 공유한다(tools/go2_climb_count.py).
FULL_STEPS = climb.FULL_STEPS
SETTLE_ROW = climb.SETTLE_ROW
alive_rows = climb.alive_rows
gained_steps = climb.gained_steps
travelled = climb.travelled
TAGS = (
    ("terrain_level", "Curriculum/terrain_levels"),
    ("track_lin_vel_xy_exp", "Episode_Reward/track_lin_vel_xy_exp"),
    ("track_ang_vel_z_exp", "Episode_Reward/track_ang_vel_z_exp"),
    ("feet_air_time", "Episode_Reward/feet_air_time"),
    ("lin_vel_z_l2", "Episode_Reward/lin_vel_z_l2"),
    ("ang_vel_xy_l2", "Episode_Reward/ang_vel_xy_l2"),
    ("flat_orientation_l2", "Episode_Reward/flat_orientation_l2"),
    ("action_rate_l2", "Episode_Reward/action_rate_l2"),
    ("dof_torques_l2", "Episode_Reward/dof_torques_l2"),
    ("dof_acc_l2", "Episode_Reward/dof_acc_l2"),
    ("base_contact", "Episode_Termination/base_contact"),
    ("episode_length", "Train/mean_episode_length"),
    ("error_vel_xy", "Metrics/base_velocity/error_vel_xy"),
    ("mean_std", "Policy/mean_std"),
)


def run_of(path: Path) -> str:
    """`_keep` 바로 아래 디렉터리 이름.  재현 회차가 원본 이름을 안에 품고 있어서다."""
    return path.relative_to(KEEP).parts[0]


def arms() -> list[Path]:
    found = []
    for evaluation in sorted(KEEP.glob("**/evaluation")):
        for arm in sorted(p for p in evaluation.iterdir() if (p / "cases").is_dir()):
            found.append(arm)
    return found


def stairs_rows() -> list[list[str]]:
    rows = [["run", "arm", "case", "seed", "height_key", "terrain_start_m", "direction",
             "step_height_m", "robots", "body_rise_ge1", "body_rise_ge2", "body_rise_full"]]
    for arm in arms():
        for case, height in STAIR_CASES.items():
            for seed in SEEDS:
                steps = arm / "cases" / f"seed_{seed}" / case / "steps.csv"
                if not steps.is_file():
                    continue
                got = climb.count(steps, height)
                if got is None:
                    continue
                rows.append([run_of(arm), arm.name, case, seed, got["height_key"],
                             f"{got['terrain_start_m']:.3f}", got["direction"], f"{height:.2f}",
                             str(got["robots"]), str(got["ge1"]), str(got["ge2"]), str(got["full"])])
    return rows


def climb_reward_rows() -> list[list[str]]:
    """오르기 대 정지의 보상률 — 평가 궤적에서 잴 수 있는 두 항만, A033 가중치로.

    추종: `track_lin_vel_xy_exp` = exp(-error_xy²/std²), A033 env.yaml std 0.5.
    수직: `lin_vel_z_l2` = vz², vz 는 root_z 차분(월드 좌표, 원 항은 몸체 좌표) — 근사다.
    오르기 = 2단 이상 오른 로봇의 [출발 1m 이후 ~ 최고점] 구간.  정지 = 1단도 못 오른 로봇의
    1초 이후 전 구간.  평지 = `forward_nominal` 1초 이후 전 구간.  나머지 항(자세·관절)은
    평가 기록에 없어서 재지 않는다.
    """
    weights = reward_weights(A033_ENV)
    w_track, w_z = weights["track_lin_vel_xy_exp"], weights["lin_vel_z_l2"]
    rows = [["run", "arm", "case", "group", "robots", "seconds_mean",
             "track_rate", "lin_vel_z_rate", "sum_rate"]]
    for run, arm in CLIMB_POLICIES:
        for case, height in (("forward_nominal", 0.0), ("stairs_10_down", 0.10),
                             ("stairs_15_down", 0.15)):
            groups: dict[str, list[tuple[float, float, float]]] = collections.defaultdict(list)
            for seed in SEEDS:
                steps = KEEP / run / "evaluation" / arm / "cases" / f"seed_{seed}" / case / "steps.csv"
                for env_rows in alive_rows(steps).values():
                    x0, y0 = float(env_rows[0]["root_x"]), float(env_rows[0]["root_y"])
                    z = [float(r["root_z"]) for r in env_rows]
                    if not height:
                        group, window = "walk", range(SETTLE_ROW, len(env_rows))
                    else:
                        gained = gained_steps(env_rows, "climb", height)
                        if gained >= 2:
                            top = max(range(len(z)), key=z.__getitem__)
                            group = "climb"
                            window = [i for i in range(SETTLE_ROW, top + 1)
                                      if travelled(env_rows[i], x0, y0)]
                        elif gained < 1:
                            group, window = "stall", range(SETTLE_ROW, len(env_rows))
                        else:
                            continue
                    window = [i for i in window if i >= 1]
                    if not window:
                        continue
                    track = sum(math.exp(-float(env_rows[i]["error_xy"]) ** 2 / TRACK_STD ** 2)
                                for i in window) / len(window)
                    vz2 = sum(((z[i] - z[i - 1]) / STEP_DT) ** 2 for i in window) / len(window)
                    groups[group].append((w_track * track, w_z * vz2, len(window) * STEP_DT))
            for group, values in groups.items():
                n = len(values)
                track = sum(v[0] for v in values) / n
                vert = sum(v[1] for v in values) / n
                rows.append([run, arm, case, group, str(n), f"{sum(v[2] for v in values) / n:.1f}",
                             f"{track:.3f}", f"{vert:.3f}", f"{track + vert:.3f}"])
    return rows


# 가중치 조합 대 결과.  (이름, 학습 env.yaml, 평가 run, 평가 arm).  모든 회차가 공통으로 가진
# 평가 case 는 rough_forward·slope_plus_20 둘뿐이라 걷기는 이 둘로 본다.
WEIGHT_RUNS = (
    ("Default-01", "go2_default_vs_pilot_v1/training/env.yaml", "go2_default_vs_pilot_v1", "default"),
    ("feet_air_time_020_v1", "go2_feet_air_time_020_v1/training/env.yaml", "go2_feet_air_time_020_v1", "candidate"),
    ("A010", "go2_g_a010_lin_vel_z_m2/training/env.yaml", "go2_g_a010_lin_vel_z_m2", "candidate"),
    ("A013", "go2_g_a013_flat_orientation_m1/training/env.yaml", "go2_g_a013_flat_orientation_m1", "candidate"),
    ("A024", "go2_g_a024_ang_vel_xy_m015/training/env.yaml", "go2_g_a024_ang_vel_xy_m015", "candidate"),
    ("track_120_v1", "go2_track_lin_vel_120_v1/training/env.yaml", "go2_track_lin_vel_120_v1", "candidate"),
    ("chain01", "go2_chain01_baseline/policy/chain01_env.yaml", "go2_chain01_baseline", "chain01"),
    ("A020", "go2_g_a020_chain01_lin_vel_z_m2/training/env.yaml", "go2_g_a020_chain01_lin_vel_z_m2", "candidate"),
    ("A021", "go2_g_a021_chain01_ang_vel_xy_m005/training/env.yaml", "go2_g_a021_chain01_ang_vel_xy_m005", "candidate"),
    ("A022", "go2_g_a022_chain01_feet_air_time_020/training/env.yaml", "go2_g_a022_chain01_feet_air_time_020", "candidate"),
    ("Pilot-01", "go2_a017_full_suite/policy/pilot_env.yaml", "go2_a017_full_suite", "pilot"),
    ("A015", "go2_g_a015_pilot_feet_air_time_035/training/env.yaml", "go2_g_a015_pilot_feet_air_time_035", "candidate"),
    ("A016", "go2_g_a016_pilot_ang_vel_xy_m015/training/env.yaml", "go2_g_a016_pilot_ang_vel_xy_m015", "candidate"),
    ("A018", "go2_g_a018_pilot_action_rate_m008/training/env.yaml", "go2_g_a018_pilot_action_rate_m008", "candidate"),
    ("A017", "go2_g_a017_pilot_track_lin_vel_xy_140/training/env.yaml", "go2_a017_full_suite", "a017"),
    ("A031", "go2_g_a031_a017_feet_air_time_001/training/env.yaml", "go2_g_a031_a017_feet_air_time_001", "candidate"),
    ("A032", "go2_g_a032_a017_feet_air_time_010/training/env.yaml", "go2_g_a032_a017_feet_air_time_010", "candidate"),
    ("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150/training/env.yaml", "go2_g_a033_a017_track_lin_vel_xy_150", "candidate"),
    # 2026-09-22 (결함 C-12): 이 표가 G-A033 에서 멈춰 있는 동안, A043 이 이미 `lin_vel_z_l2 -1.5`
    # 에서 걷는 정책을 만들어 전수 69 case 를 남겼는데도 그 다이얼의 모든 값이 `OUT_OF_RANGE` 로
    # 계산됐다.  회수된 회차는 성패와 무관하게 표에 들어간다 — 표는 관측이고 판정은 판독문이 한다.
    ("A043", "go2_g_a043_a033_lin_vel_z_m15/training/env.yaml", "go2_g_a043_a033_lin_vel_z_m15", "candidate"),
    # A038·A041·A042 는 아직 넣지 않았다: 세 회차 모두 1단계만 재고 끝나 이 표의 칸(rough_forward
    # 속도·경사 전진·15cm 오르기) 중 일부가 **미측정**이다.  빈 칸을 0 이나 "없음" 으로 읽히게 두는
    # 것이 기울기 판독을 조용히 망가뜨리므로, 부분 행을 넣기 전에 미측정 칸의 표기를 정한다
    # (결함 C-12, `reports/GO2_DEFECT_LEDGER.md`).
)
WEIGHT_TERMS = ("track_lin_vel_xy_exp", "lin_vel_z_l2", "ang_vel_xy_l2", "action_rate_l2",
                "feet_air_time", "flat_orientation_l2")


def weight_outcome_rows(behavior: list[list[str]], climb: list[list[str]]) -> list[list[str]]:
    """회차별 가중치와 평가 결과를 한 줄로.  두 표는 이 도구가 만든 것을 그대로 받는다."""
    head, *body = behavior
    col = {name: i for i, name in enumerate(head)}
    chead, *cbody = climb
    ccol = {name: i for i, name in enumerate(chead)}
    rows = [["name", *WEIGHT_TERMS, "rough_forward_speed", "slope_plus_20_progress_m",
             "climb10_ge2", "climb15_ge1"]]
    for name, env, run, arm in WEIGHT_RUNS:
        weights = reward_weights(KEEP / env)

        def mean(case: str, field: str) -> str:
            values = [float(r[col[field]]) for r in body
                      if r[col["run"]] == run and r[col["arm"]] == arm and r[col["case"]] == case]
            return f"{sum(values) / len(values):.3f}" if values else ""

        def climbed(case: str, field: str) -> str:
            values = [int(r[ccol[field]]) for r in cbody
                      if r[ccol["run"]] == run and r[ccol["arm"]] == arm and r[ccol["case"]] == case]
            return str(sum(values)) if values else ""

        rows.append([name, *[f"{weights[t]:g}" for t in WEIGHT_TERMS],
                     mean("rough_forward", "speed_xy_mean"),
                     mean("slope_plus_20", "projected_progress_m"),
                     climbed("stairs_10_down", "body_rise_ge2"),
                     climbed("stairs_15_down", "body_rise_ge1")])
    return rows


LATERAL_POLICIES = (
    ("go2_default_vs_pilot_v1", "default"), ("go2_feet_air_time_020_v1", "candidate"),
    ("go2_chain01_baseline", "chain01"), ("go2_a017_full_suite", "pilot"),
    ("go2_a017_full_suite", "a017"), ("go2_g_a033_a017_track_lin_vel_xy_150", "candidate"),
)
LATERAL_CASES = ("rough_lateral", "rough_forward", "left", "right", "diagonal_left", "diagonal_right")
PRE_TERMINATION_ROWS = 25   # 종료 직전 0.5 초
EARLY_ROWS = 100            # 처음 2 초 — 종료 중앙값(5.7~9.6 s)보다 앞선 구간
HEAVY_KG, LIGHT_KG = 8.5, 7.0


def lateral_rows() -> list[list[str]]:
    """험지 옆걸음(G3 최솟값 case) 종료의 모양.  같은 정책의 평지 옆걸음·험지 전진과 나란히 둔다.

    tilt_cos_min: 종료 직전 0.5 초 동안 -proj_grav_z 의 최솟값.  1 = 수평, 0 = 옆으로 90°,
    음수 = 뒤집힘.  옛 계측(열 없음)은 빈칸.  base_mass: metadata.json 의 env 별 몸통 질량
    (학습과 같은 `add_base_mass (-1, 3)` 무작위).
    """
    def median(values: list[float], places: int = 3) -> str:
        if not values:
            return ""
        ordered = sorted(values)
        mid = len(ordered) // 2
        value = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
        return f"{value:.{places}f}"

    rows = [["run", "arm", "case", "robots", "terminated", "term_time_median_s",
             "tilt_cos_min_median", "base_mass_terminated_median", "base_mass_survived_median",
             "vy_mean", "abs_wz_mean", "mass_auc", "heavy_terminated", "heavy_robots",
             "light_terminated", "light_robots",
             "early_abs_wz_auc", "heading_drift_terminated_median_rad", "heading_drift_survived_median_rad",
             "cmd_vy", "early_vy_auc"]]
    for run, arm in LATERAL_POLICIES:
        for case in LATERAL_CASES:
            robots = 0
            times: list[float] = []
            tilts: list[float] = []
            mass_term: list[float] = []
            mass_surv: list[float] = []
            vy: list[float] = []
            wz: list[float] = []
            early_term: list[float] = []
            early_surv: list[float] = []
            drift_term: list[float] = []
            drift_surv: list[float] = []
            vy_term: list[float] = []
            vy_surv: list[float] = []
            cmd_vy = ""
            for seed in SEEDS:
                folder = KEEP / run / "evaluation" / arm / "cases" / f"seed_{seed}" / case
                meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
                masses = meta["realized_randomization_values"]["robot_body_masses"]
                by: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
                with (folder / "steps.csv").open(encoding="utf-8", newline="") as handle:
                    for row in csv.DictReader(handle):
                        by[row["env_id"]].append(row)
                        cmd_vy = cmd_vy or f"{float(row['cmd_vy']):.2f}"
                for env, env_rows in by.items():
                    robots += 1
                    end = next((i for i, r in enumerate(env_rows) if r["term_base_contact"] == "1"), None)
                    alive = env_rows[:end] if end is not None else env_rows
                    settled = alive[SETTLE_ROW:] or alive
                    vy.append(sum(float(r["actual_vy"]) for r in settled) / len(settled))
                    wz.append(sum(abs(float(r["actual_wz"])) for r in settled) / len(settled))
                    mass = float(masses[int(env)][0])
                    # 옆걸음 명령의 회전은 0 이다(cmd_wz).  |wz| 는 곧 회전 추종 오차, 누적은 방향 이탈.
                    early = sum(abs(float(r["actual_wz"])) for r in env_rows[:EARLY_ROWS]) / len(env_rows[:EARLY_ROWS])
                    drift = abs(sum(float(r["actual_wz"]) for r in env_rows[:len(alive) + 1]) * STEP_DT)
                    # 처음 2 초 옆 속도(명령 방향 부호) — 옆으로 빨리 가는 로봇이 넘어지는가.
                    early_vy = sum(float(r["actual_vy"]) for r in env_rows[:EARLY_ROWS]) / len(env_rows[:EARLY_ROWS])
                    if end is None:
                        mass_surv.append(mass)
                        early_surv.append(early)
                        drift_surv.append(drift)
                        vy_surv.append(early_vy)
                        continue
                    mass_term.append(mass)
                    early_term.append(early)
                    drift_term.append(drift)
                    vy_term.append(early_vy)
                    times.append(float(env_rows[end]["time_s"]))
                    before = env_rows[max(0, end - PRE_TERMINATION_ROWS):end]
                    if before and before[0].get("proj_grav_z"):
                        tilts.append(min(-float(r["proj_grav_z"]) for r in before))
            # 종료 로봇이 생존 로봇보다 무거울 확률(AUC, 0.5 = 무관).  무거움·가벼움은 add_base_mass
            # 범위의 위·아래 끝(몸통 질량 8.5 kg 이상, 7.0 kg 미만).
            auc = ""
            if mass_term and mass_surv:
                wins = sum((a > b) + 0.5 * (a == b) for a in mass_term for b in mass_surv)
                auc = f"{wins / (len(mass_term) * len(mass_surv)):.3f}"
            early_auc = ""
            if early_term and early_surv:
                wins = sum((a > b) + 0.5 * (a == b) for a in early_term for b in early_surv)
                early_auc = f"{wins / (len(early_term) * len(early_surv)):.3f}"
            vy_auc = ""
            if vy_term and vy_surv:
                sign = -1.0 if cmd_vy.startswith("-") else 1.0
                wins = sum((sign * a > sign * b) + 0.5 * (a == b) for a in vy_term for b in vy_surv)
                vy_auc = f"{wins / (len(vy_term) * len(vy_surv)):.3f}"
            everyone = mass_term + mass_surv
            rows.append([run, arm, case, str(robots), str(len(times)), median(times, 2),
                         median(tilts), median(mass_term), median(mass_surv),
                         f"{sum(vy) / len(vy):.3f}", f"{sum(wz) / len(wz):.3f}", auc,
                         str(sum(m >= HEAVY_KG for m in mass_term)), str(sum(m >= HEAVY_KG for m in everyone)),
                         str(sum(m < LIGHT_KG for m in mass_term)), str(sum(m < LIGHT_KG for m in everyone)),
                         early_auc, median(drift_term), median(drift_surv), cmd_vy, vy_auc])
    return rows


def behavior_rows() -> list[list[str]]:
    fields = ("speed_xy_mean", "height_rel_median", "projected_progress_m", "survival_proxy",
              "tracking_xy_rmse", "terminated_env_count", "fallen_env_count")
    rows = [["run", "arm", "case", "seed", *fields]]
    for arm in arms():
        for case in BEHAVIOR_CASES:
            for seed in SEEDS:
                summary = arm / "cases" / f"seed_{seed}" / case / "summary.json"
                if not summary.is_file():
                    continue
                body = json.loads(summary.read_text(encoding="utf-8"))
                cells = []
                for field in fields:
                    value = body.get(field)
                    if isinstance(value, bool) or value is None:
                        cells.append("")
                    elif isinstance(value, int):
                        cells.append(str(value))
                    else:
                        cells.append(f"{float(value):.3f}")
                rows.append([run_of(arm), arm.name, case, seed, *cells])
    return rows


def training_rows() -> list[list[str]]:
    rows = [["run", "iterations", *[name for name, _tag in TAGS]]]
    # 최근 회차는 `training/logs/`, 08-31 Pilot-01 원본 회수본은 `<run>/.../logs/rsl_rl/`에 있다.
    found = set(KEEP.glob("**/training/logs/**/events.out.tfevents*")) | set(KEEP.glob("**/logs/rsl_rl/**/events.out.tfevents*"))
    for events in sorted(found):
        series: dict[str, list[float]] = collections.defaultdict(list)
        for tag, value in tfcurve.scalars(events):
            series[tag].append(value)
        levels = series.get("Curriculum/terrain_levels", [])
        cells = []
        for _name, tag in TAGS:
            tail = series.get(tag, [])[-10:]
            cells.append(f"{sum(tail) / len(tail):.3f}" if tail else "")
        rows.append([run_of(events), str(len(levels)), *cells])
    return rows


def write(name: str, rows: list[list[str]]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    return path


def main() -> int:
    climb, behavior = stairs_rows(), behavior_rows()
    for name, rows in (("STAIRS_CLIMB.csv", climb),
                       ("CASE_BEHAVIOR.csv", behavior),
                       ("TRAINING_TERMS.csv", training_rows()),
                       ("CLIMB_REWARD.csv", climb_reward_rows()),
                       ("WEIGHT_OUTCOME.csv", weight_outcome_rows(behavior, climb)),
                       ("LATERAL_BEHAVIOR.csv", lateral_rows())):
        print(f"{write(name, rows).relative_to(ROOT)}  rows={len(rows) - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
