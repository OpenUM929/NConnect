"""Go2 변수별 영향도 전수 판독 — 한 항 변경 학습 회차를 모두 같은 방식으로 검수한다.

왜 있는가.  2026-09-17 사용자 지시: "track을 검수한 것처럼 모든 변수를 검수해서 영향도를 체크하고,
변수별로 어디에 영향을 주는지 특이점을 모아 분석하면 사실 근거가 된다."
track 검수에서 배운 것 세 가지를 모든 쌍에 똑같이 적용한다.
  1. 학습 env.yaml을 실제로 대조한다(`log_dir` 외 다른 줄 수).
  2. 평가 체크포인트를 모델 SHA → `model_N.pt`로 산출물에서 찾는다(이름·기록을 믿지 않는다).
  3. 기준 정책이 멈춰 있으면(험지 전진 속도 < 0.2) 그 쌍의 결과를 걷는 기준으로 옮기지 않는다.

지표는 계측 세대와 무관한 것만 쓴다.  `steps.csv` 원시 열(속도·오차·종료)에서 직접 계산한다.
옛 세대 `summary.json`의 `projected_progress_m`은 방법이 달라(멈춘 정책이 18 m) 쓰지 않는다.

기준 arm은 같은 모델 SHA의 전수 평가(seed 3개)를 쓴다.  평가는 결정론적이라 각 회차의
`baseline_tier1` 캐시와 값이 같다 — 이 도구가 매번 대조한다(`dr_seed_101` case는 회차마다
정의가 달라 제외).

산출 (reports/evidence/go2_variable_influence_20260917/):
  PAIRS.csv        쌍별 조건 대조(env 차이·체크포인트·걷기·중복)
  PAIR_METRICS.csv 쌍 × case × 지표: 기준·후보·차이·평가 seed 흔들림·신호
보고서: reports/GO2_VARIABLE_INFLUENCE.md  (이 도구가 CSV에서 생성)
사용: python tools/go2_variable_influence.py            (CSV·보고서 재생성)
      python tools/go2_variable_influence.py --report   (CSV에서 보고서만)
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep"
QUAD = ROOT / "workspace/training/quadruped"
OUT = QUAD / "reports/evidence/go2_variable_influence_20260917"
DOC = QUAD / "reports/GO2_VARIABLE_INFLUENCE.md"
DOC_REL = "workspace/training/quadruped/reports/GO2_VARIABLE_INFLUENCE.md"

SEEDS = ("101", "202", "303")
STEP_DT = 0.02
WALK_SPEED = 0.2          # 기반 데이터와 같은 걷기 경계(험지 전진 속도)
EXCLUDED_PREFIX = "dr_seed_"   # 무작위화 case는 회차마다 정의가 달라 제외
SIGNAL_SIGMA = 2.0        # 차이가 평가 seed 흔들림의 2배를 넘어야 신호

# 기준 정책: 이름 → (모델 SHA, 전수 평가 arm, 학습 env.yaml)
BASELINES = {
    "Default-01": ("99ceeaa1a3a1ebee", "go2_default_vs_pilot_v1/evaluation/default",
                   "go2_default_vs_pilot_v1/training/env.yaml"),
    "Pilot-01": ("c4d78adf3fbd9031", "go2_a017_full_suite/evaluation/pilot",
                 "go2_a017_full_suite/policy/pilot_env.yaml"),
    "chain01": ("143871e3f69514a4", "go2_chain01_baseline/evaluation/chain01",
                "go2_chain01_baseline/policy/chain01_env.yaml"),
    "A017": ("0563deffae52552c", "go2_a017_full_suite/evaluation/a017",
             "go2_g_a017_pilot_track_lin_vel_xy_140/training/env.yaml"),
    "G-A033": ("ccd60e192bf4ec90", "go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate",
               "go2_g_a033_a017_track_lin_vel_xy_150/training/env.yaml"),
}
# 한 항 변경 학습 회차: (작업 id, `_keep` 디렉터리, 기준 정책)
PAIRS = (
    ("G-A007", "go2_feet_air_time_020_v1", "Default-01"),
    ("G-A009", "go2_track_lin_vel_120_v1", "Default-01"),
    ("G-A010", "go2_g_a010_lin_vel_z_m2", "Default-01"),
    ("G-A013", "go2_g_a013_flat_orientation_m1", "Default-01"),
    ("G-A024", "go2_g_a024_ang_vel_xy_m015", "Default-01"),
    ("G-A025", "go2_g_a025_flat_orientation_m1", "Default-01"),
    ("G-A015", "go2_g_a015_pilot_feet_air_time_035", "Pilot-01"),
    ("G-A016", "go2_g_a016_pilot_ang_vel_xy_m015", "Pilot-01"),
    ("G-A017", "go2_g_a017_pilot_track_lin_vel_xy_140", "Pilot-01"),
    ("G-A018", "go2_g_a018_pilot_action_rate_m008", "Pilot-01"),
    ("G-A020", "go2_g_a020_chain01_lin_vel_z_m2", "chain01"),
    ("G-A021", "go2_g_a021_chain01_ang_vel_xy_m005", "chain01"),
    ("G-A022", "go2_g_a022_chain01_feet_air_time_020", "chain01"),
    ("G-A031", "go2_g_a031_a017_feet_air_time_001", "A017"),
    ("G-A032", "go2_g_a032_a017_feet_air_time_010", "A017"),
    ("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150", "A017"),
    # 2026-09-17: 표적 단계(10 case)까지 측정하고 러너 결함으로 판정 없이 끝난 회차(GO2_G_A038_READOUT.md).
    ("G-A038", "go2_g_a038_a033_ang_vel_xy_m008", "G-A033"),
    # 2026-09-22: 회수된 한 항 변경 회차는 규칙대로 전부 넣는다(`workspace/training/quadruped/AGENTS.md`
    # §4-9: "새 한 항 변경 회차를 회수하면 PAIRS 에 추가하고 재생성한다").  A041·A042 는 1단계에서
    # 멎어 case 가 적고, A043 은 전수 69 를 다 쟀다 — 조건 대조 등급이 그 차이를 그대로 드러낸다.
    ("G-A041", "go2_g_a041_a033_ang_vel_xy_m004", "G-A033"),
    ("G-A042", "go2_g_a042_a033_track_lin_vel_xy_160", "G-A033"),
    ("G-A043", "go2_g_a043_a033_lin_vel_z_m15", "G-A033"),
)
# 이름이 붙은 SHA256SUMS에 없는 체크포인트 — 원본 학습 파일을 직접 해시한다.
EXTRA_CHECKPOINTS = (
    "train_260831-Go2_5var_1000/train_260831-Go2_5var_1000_DOWNLOAD/quadruped/logs/rsl_rl/quadruped/"
    "2026-08-31_15-42-43/model_999.pt",
)
# 지표: (이름, 좋아지는 방향 +1/-1/0, 설명)
METRICS = (
    ("terminated", -1, "몸통 접촉 종료 로봇 수"),
    ("progress_m", +1, "명령 방향 전진 거리 중앙값(종료 전까지)"),
    ("speed", 0, "평균 수평 속도"),
    ("error_xy", -1, "평균 속도 추종 오차"),
    ("error_yaw", -1, "평균 회전 추종 오차"),
)
TERM_OF = {"feet_air_time": "feet_air_time", "track_lin_vel_xy_exp": "track_lin_vel_xy_exp",
           "lin_vel_z_l2": "lin_vel_z_l2", "flat_orientation_l2": "flat_orientation_l2",
           "ang_vel_xy_l2": "ang_vel_xy_l2", "action_rate_l2": "action_rate_l2"}
CASE_LABEL = {
    "forward_nominal": "평지 전진", "forward_slow": "평지 저속", "forward_fast": "평지 고속", "backward": "후진",
    "left": "평지 왼쪽 옆", "right": "평지 오른쪽 옆", "diagonal_left": "평지 왼쪽 대각", "diagonal_right": "평지 오른쪽 대각",
    "combined_yaw_left": "전진+왼쪽 회전", "combined_yaw_right": "전진+오른쪽 회전",
    "push_pos_x": "앞 밀침", "push_neg_x": "뒤 밀침", "push_pos_y": "왼쪽 밀침", "push_neg_y": "오른쪽 밀침",
    "rough_forward": "험지 전진", "rough_lateral": "험지 옆걸음",
    "slope_plus_20": "오르막 20°", "slope_minus_20": "내리막 20°",
    "stairs_10_down": "10cm 계단 오르기", "stairs_15_down": "15cm 계단 오르기",
    "stairs_10_up": "10cm 계단 내려가기", "stairs_15_up": "15cm 계단 내려가기",
}


# ─────────────────────────────────────────────────────────────────────────────
# 조건 대조
# ─────────────────────────────────────────────────────────────────────────────
def checkpoint_map() -> dict[str, str]:
    """모델 SHA(16자) → 반복 수.  `_keep`의 SHA256SUMS와 원본 학습 파일에서."""
    found: dict[str, str] = {}
    pattern = re.compile(r"^([0-9a-f]{64})\s+\S*model_(\d+)\.pt$")
    for sums in KEEP.glob("*/SHA256SUMS.txt"):
        for line in sums.read_text(encoding="utf-8", errors="replace").splitlines():
            match = pattern.match(line.strip())
            if match:
                found[match.group(1)[:16]] = match.group(2)
    for pin in KEEP.glob("*/training/CHECKPOINT_PIN.txt"):
        fields = dict(line.split("=", 1) for line in pin.read_text(encoding="utf-8").splitlines() if "=" in line)
        found[fields["EVAL_CHECKPOINT_SHA"][:16]] = fields["EVAL_CHECKPOINT_ITER"]
    for rel in EXTRA_CHECKPOINTS:
        path = KEEP / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        found[digest[:16]] = re.search(r"model_(\d+)\.pt$", rel).group(1)
    return found


def env_differences(left: Path, right: Path) -> list[str]:
    a = left.read_text(encoding="utf-8").splitlines()
    b = right.read_text(encoding="utf-8").splitlines()
    if len(a) != len(b):
        return [f"줄 수 {len(a)} != {len(b)}"]
    return [f"{i + 1}: {x.strip()} → {y.strip()}" for i, (x, y) in enumerate(zip(a, b))
            if x != y and not x.startswith("log_dir:")]


def single_change(run: str) -> tuple[str, str, str]:
    text = (KEEP / run / "training/TRAIN_STATUS.txt").read_text(encoding="utf-8")
    term, values = re.search(r"SINGLE_CHANGE=([a-z_0-9]+):(\S+)", text).groups()
    old, new = values.split("->")
    return term, old, new


def model_sha(arm: Path) -> str:
    return json.loads((arm / "identity.json").read_text(encoding="utf-8"))["model_sha256"][:16]


# ─────────────────────────────────────────────────────────────────────────────
# 원시 기록 지표
# ─────────────────────────────────────────────────────────────────────────────
_CACHE: dict[Path, dict[str, float]] = {}


def case_metrics(steps: Path) -> dict[str, float]:
    if steps in _CACHE:
        return _CACHE[steps]
    # 행을 쌓지 않고 누적만 한다(평가 파일 하나가 32,000행 — 전체 관문을 메모리 적게 돌린다).
    ended: set[str] = set()
    terminated: set[str] = set()
    robots: set[str] = set()
    along: dict[str, float] = {}
    command: dict[str, tuple[float, float, float]] = {}
    count = 0
    speed = error_xy = error_yaw = 0.0
    with steps.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            env = row["env_id"]
            robots.add(env)
            if env in ended:
                continue
            if row["term_base_contact"] == "1":
                terminated.add(env)
            if row["terminated"] == "1" or row["truncated"] == "1":
                ended.add(env)
                continue
            if env not in command:
                cx, cy = float(row["cmd_vx"]), float(row["cmd_vy"])
                command[env] = (cx, cy, math.hypot(cx, cy))
                along[env] = 0.0
            cx, cy, norm = command[env]
            if norm:
                along[env] += (float(row["actual_vx"]) * cx + float(row["actual_vy"]) * cy) / norm
            count += 1
            speed += float(row["speed_xy"])
            error_xy += float(row["error_xy"])
            error_yaw += float(row["error_yaw"])
    progress = sorted(along[env] * STEP_DT for env, (_x, _y, norm) in command.items() if norm)
    out = {
        "robots": float(len(robots)),
        "terminated": float(len(terminated)),
        "progress_m": progress[len(progress) // 2] if progress else float("nan"),
        "speed": speed / count,
        "error_xy": error_xy / count,
        "error_yaw": error_yaw / count,
    }
    _CACHE[steps] = out
    return out


def cases_of(arm: Path, seed: str) -> set[str]:
    folder = arm / "cases" / f"seed_{seed}"
    if not folder.is_dir():
        return set()
    return {p.name for p in folder.iterdir() if (p / "steps.csv").is_file() and not p.name.startswith(EXCLUDED_PREFIX)}


def cache_matches(run: str, base_arm: Path) -> tuple[int, int]:
    """회차 안의 기준 캐시(`baseline_tier1`/`a017_sentinel`) summary가 전수 평가와 같은 case 수."""
    fields = ("speed_xy_mean", "tracking_xy_rmse", "terminated_env_count")
    same = total = 0
    for cache in (KEEP / run / "evaluation").iterdir():
        if cache.name == "candidate" or not (cache / "cases").is_dir():
            continue
        for summary in cache.glob("cases/seed_*/*/summary.json"):
            if summary.parent.name.startswith(EXCLUDED_PREFIX):
                continue
            twin = base_arm / summary.relative_to(cache)
            if not twin.is_file():
                continue
            a = json.loads(summary.read_text(encoding="utf-8"))
            b = json.loads(twin.read_text(encoding="utf-8"))
            total += 1
            same += all(abs(float(a[f]) - float(b[f])) < 1e-9 for f in fields)
    return same, total


def sd(values: list[float]) -> float:
    if len(values) < 2:
        return float("nan")
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))


# ─────────────────────────────────────────────────────────────────────────────
# 표 만들기
# ─────────────────────────────────────────────────────────────────────────────
def fmt(value: float, places: int = 3) -> str:
    return "" if value != value else f"{value:.{places}f}"


def build(metrics_for: set[str] | None = None) -> tuple[list[list[str]], list[list[str]]]:
    """쌍 원장 전부와 지표 행.  `metrics_for`를 주면 그 작업의 지표 행만 계산한다(관문의 표본 재계산용)."""
    iters = checkpoint_map()
    pairs = [["work_id", "run", "term", "from", "to", "baseline", "env_diff_lines", "env_diff",
              "ckpt_base", "ckpt_cand", "same_ckpt", "base_walking", "cand_walking",
              "base_rough_speed", "cand_rough_speed", "duplicate_of", "cache_same", "cache_total",
              "cases", "seeds", "walk_case"]]
    metrics = [["work_id", "term", "case", "seeds", "metric", "base", "cand", "delta", "seed_sd",
                "threshold", "signal", "better"]]
    seen_models: dict[str, str] = {}
    for work_id, run, base_name in PAIRS:
        term, old, new = single_change(run)
        sha, base_rel, base_env = BASELINES[base_name]
        base_arm, cand_arm = KEEP / base_rel, KEEP / run / "evaluation/candidate"
        cand_sha = model_sha(cand_arm)
        duplicate = seen_models.get(cand_sha, "")
        seen_models.setdefault(cand_sha, work_id)
        diff = env_differences(KEEP / base_env, KEEP / run / "training/env.yaml")
        seeds_of: dict[str, list[str]] = collections.defaultdict(list)
        for s in SEEDS:
            for case in cases_of(cand_arm, s) & cases_of(base_arm, s):
                seeds_of[case].append(s)
        common = sorted(seeds_of)
        seeds = sorted({s for v in seeds_of.values() for s in v})
        # 걷기 판정은 seed 101 험지 전진이다.  험지 전진을 재지 않은 부분 평가(G-A038)는 평지 전진으로
        # 대신하고 그 사실을 walk_case 열에 남긴다 — 같은 속도 경계라 평지 쪽이 더 쉽게 넘는다.
        walk_case = "rough_forward" if (cand_arm / "cases/seed_101/rough_forward/steps.csv").is_file()             else "forward_nominal"
        base_speed = case_metrics(base_arm / f"cases/seed_101/{walk_case}/steps.csv")["speed"]
        cand_speed = case_metrics(cand_arm / f"cases/seed_101/{walk_case}/steps.csv")["speed"]
        same, total = cache_matches(run, base_arm)
        pairs.append([work_id, run, term, old, new, base_name, str(len(diff)), " | ".join(diff),
                      iters.get(sha, ""), iters.get(cand_sha, ""), str(iters.get(sha) == iters.get(cand_sha)),
                      str(base_speed >= WALK_SPEED), str(cand_speed >= WALK_SPEED),
                      fmt(base_speed), fmt(cand_speed), duplicate, str(same), str(total),
                      str(len(common)), "/".join(seeds), walk_case])
        for case in common if metrics_for is None or work_id in metrics_for else ():
            case_seeds = seeds_of[case]
            for name, better, _desc in METRICS:
                base_all = [case_metrics(base_arm / f"cases/seed_{s}/{case}/steps.csv")[name] for s in SEEDS]
                base_vals = [case_metrics(base_arm / f"cases/seed_{s}/{case}/steps.csv")[name] for s in case_seeds]
                cand_vals = [case_metrics(cand_arm / f"cases/seed_{s}/{case}/steps.csv")[name] for s in case_seeds]
                if any(v != v for v in base_vals + cand_vals):
                    continue
                b, c = sum(base_vals) / len(base_vals), sum(cand_vals) / len(cand_vals)
                spread = sd(base_all)
                if name == "terminated" and spread == 0:
                    robots = case_metrics(base_arm / f"cases/seed_101/{case}/steps.csv")["robots"]
                    p = (b + c) / (2 * robots)
                    spread = math.sqrt(robots * p * (1 - p))
                threshold = SIGNAL_SIGMA * spread * math.sqrt(2 / len(case_seeds))
                delta = c - b
                signal = 0 if abs(delta) <= threshold else (1 if delta > 0 else -1)
                verdict = "" if signal == 0 or better == 0 else ("better" if signal == better else "worse")
                metrics.append([work_id, term, case, str(len(case_seeds)), name, fmt(b), fmt(c), fmt(delta),
                                fmt(spread), fmt(threshold), str(signal), verdict])
    return pairs, metrics


def write(name: str, rows: list[list[str]]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    return path


def read(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# ─────────────────────────────────────────────────────────────────────────────
# 판독
# ─────────────────────────────────────────────────────────────────────────────
def validity(pair: dict[str, str]) -> str:
    """A 조건 같음·둘 다 걷기 / B 조건 같음·정지 포함 / C 체크포인트 다름 / D 중복 / E env 차이 ≠ 1줄."""
    if pair["duplicate_of"]:
        return "D"
    if pair["env_diff_lines"] != "1":
        return "E"
    if pair["same_ckpt"] != "True":
        return "C"
    if pair["base_walking"] == "True" and pair["cand_walking"] == "True":
        return "A"
    return "B"


CLASS_TEXT = {
    "A": "조건 같음 · 둘 다 걷기 — 걷는 기준의 영향으로 읽는다",
    "B": "조건 같음 · 멈춘 정책 포함 — 방향만 참고, 걷는 기준으로 옮기지 않는다",
    "C": "체크포인트 다름 — 변수 효과와 학습 시점 효과가 섞인다(시점 효과는 미측정)",
    "D": "앞 회차와 같은 모델(SHA 동일) — 독립 표본이 아니다",
    "E": "env.yaml 차이가 한 줄이 아니다",
}


def findings() -> dict:
    pairs = read("PAIRS.csv")
    metrics = read("PAIR_METRICS.csv")
    by_pair = collections.defaultdict(list)
    for m in metrics:
        by_pair[m["work_id"]].append(m)
    out = {"pairs": pairs, "by_pair": by_pair, "class": {p["work_id"]: validity(p) for p in pairs}}
    out["collapse"] = [p for p in pairs if p["base_walking"] == "True" and p["cand_walking"] == "False"]
    out["revive"] = [p for p in pairs if p["base_walking"] == "False" and p["cand_walking"] == "True"]
    terms = collections.OrderedDict()
    for p in pairs:
        terms.setdefault(p["term"], []).append(p)
    out["terms"] = terms
    out["no_walking_clean"] = [t for t, ps in terms.items() if not any(out["class"][p["work_id"]] == "A" for p in ps)]
    # 기준 정책 고유 특이점: 같은 기준에서 나온 서로 다른 모델이 전부 같은 방향으로 달라진 (case, 지표).
    # 변수가 제각각인데 방향이 같으면 변수가 아니라 기준 정책 쪽의 성질이다.
    shared = []
    for base in dict.fromkeys(p["baseline"] for p in pairs):
        ids = [p["work_id"] for p in pairs if p["baseline"] == base and out["class"][p["work_id"]] != "D"]
        if len(ids) < BASELINE_QUIRK_MIN:
            continue
        cells = collections.defaultdict(dict)
        for work_id in ids:
            for m in by_pair[work_id]:
                cells[(m["case"], m["metric"])][work_id] = m
        for (case, metric), ms in cells.items():
            signals = {m["signal"] for m in ms.values()}
            if len(ms) == len(ids) and len(signals) == 1 and signals != {"0"} and metric in BEHAVIOR:
                shared.append({"baseline": base, "case": case, "metric": metric, "pairs": ids,
                               "base": next(iter(ms.values()))["base"],
                               "cands": [ms[i]["cand"] for i in ids], "signal": signals.pop()})
    out["baseline_quirks"] = shared
    return out


BEHAVIOR = ("terminated", "progress_m")   # 동작 지표 — 특이점 요약은 이 둘만 쓴다
BEHAVIOR_SHORT = {"terminated": "종료", "progress_m": "전진"}
BASELINE_QUIRK_MIN = 3                    # 같은 기준에서 나온 서로 다른 모델이 이만큼 있어야 공통 방향을 본다


def behavior_line(ms: list[dict[str, str]]) -> str:
    parts = [f"{m['case']} {BEHAVIOR_SHORT[m['metric']]}{arrow(m)} {m['base']}→{m['cand']}"
             for m in ms if m["metric"] in BEHAVIOR and m["signal"] != "0"]
    return " · ".join(parts) or "동작 지표 신호 없음"


def walk_label(p: dict[str, str]) -> str:
    """걷기 판정 case.  부분 평가(G-A038)는 험지 전진 대신 평지 전진을 썼다(PAIRS.csv walk_case)."""
    return {"rough_forward": "험지", "forward_nominal": "평지(험지 전진 미측정)"}[p.get("walk_case") or "rough_forward"]


def stall_cases(ms: list[dict[str, str]]) -> list[str]:
    """종료 수가 줄었는데 전진도 줄어든 case — 넘어지지 않은 것이 아니라 멈춘 것일 수 있다."""
    by: dict[str, dict[str, dict[str, str]]] = {}
    for m in ms:
        by.setdefault(m["case"], {})[m["metric"]] = m
    return [case for case, mm in by.items()
            if mm.get("terminated", {}).get("better") == "better" and mm.get("progress_m", {}).get("better") == "worse"]


def arrow(m: dict[str, str]) -> str:
    if m["signal"] == "0":
        return "·"
    mark = "▲" if m["signal"] == "1" else "▼"
    return mark + ("✓" if m["better"] == "better" else "✗" if m["better"] == "worse" else "")


def render() -> str:
    f = findings()
    lines: list[str] = []
    add = lines.append
    add("# Go2 변수별 영향도 전수 판독")
    add("")
    add("> **생성 문서 — 손으로 고치지 않는다.** `python tools/go2_variable_influence.py`가 `_keep` 원시 기록에서 만든다.")
    add("> 증거: `reports/evidence/go2_variable_influence_20260917/` (`PAIRS.csv` · `PAIR_METRICS.csv`). 관문: `tools/test_go2_variable_influence_contract.py`.")
    add("> 짝 문서: `reports/GO2_TUNING_BASE_DATA.md`(회차 표·특이점). 이 문서는 **한 항 변경 쌍만** 같은 방식으로 검수한다.")
    add("")
    add("## 0. 방법 (2026-09-17 사용자 지시: track 검수와 같은 방식으로 모든 변수를 검수)")
    add("")
    add("1. 조건 대조: 기준·후보 학습 env.yaml을 줄 단위로 비교하고(`log_dir` 제외), 평가 모델 SHA를 `_keep` SHA256SUMS의 `model_N.pt`와 맞춰 체크포인트를 찾는다.")
    add("2. 기준 arm은 같은 모델의 전수 평가(seed 3개)다. 각 회차 안의 기준 캐시와 `summary.json`의 속도·추종 오차·종료 수가 같은지 매번 대조한다(`cache_same`/`cache_total`).")
    add("3. 지표는 `steps.csv` 원시 열에서 계산한다: 종료 수(`term_base_contact`), 명령 방향 전진 거리 중앙값, 평균 속도, 평균 속도·회전 추종 오차. 종료 뒤 행은 버린다.")
    add(f"4. 신호: \\|차이\\| > `{SIGNAL_SIGMA}` × (기준 정책의 seed 3개 표준편차) × √(2/비교 seed 수). 종료 수의 표준편차가 0이면 이항 표준편차를 쓴다."
        " 평가 seed 흔들림만 반영한다 — **학습 seed 흔들림은 미측정**(전 회차 seed 42)이라 신호도 한 번의 학습 결과다.")
    add("5. `dr_seed_*` case는 회차마다 정의가 달라 제외한다(기준 캐시와 전수 평가 값이 다르다). 걷기 판정 속도는 seed 101 `rough_forward` 기준이고, 그 case를 재지 않은 부분 평가는 `forward_nominal`로 대신한다(`walk_case` 열).")
    add("")
    add("표기: ▲ 증가 · ▼ 감소 · `·` 신호 없음 · ✓ 좋아짐 · ✗ 나빠짐(종료·오차는 감소가, 전진 거리는 증가가 좋음; 속도는 판정 없음).")
    add("")
    add("## 1. 쌍 원장 (`PAIRS.csv`)")
    add("")
    add("| 작업 | 변경 | 기준 | env 차이 줄 | 체크포인트 기준/후보 | 걷기 판정 속도 기준 → 후보 | 캐시 대조 | case × seed | 등급 |")
    add("|---|---|---|---|---|---|---|---|---|")
    for p in f["pairs"]:
        add(f"| {p['work_id']} | `{p['term']}` `{p['from']}` → `{p['to']}` | {p['baseline']} | {p['env_diff_lines']} | "
            f"{p['ckpt_base']} / {p['ckpt_cand']} | {walk_label(p)} {p['base_rough_speed']} → {p['cand_rough_speed']} | "
            f"{p['cache_same']}/{p['cache_total']} | {p['cases']} × {p['seeds']} | **{f['class'][p['work_id']]}**"
            + (f" (= {p['duplicate_of']})" if p["duplicate_of"] else "") + " |")
    add("")
    for key, text in CLASS_TEXT.items():
        n = sum(1 for c in f["class"].values() if c == key)
        add(f"- **{key}** ({n}쌍): {text}")
    add("")
    add("## 2. 변수별 영향 (`PAIR_METRICS.csv`)")
    add("")
    for term, ps in f["terms"].items():
        add(f"### `{term}`")
        add("")
        cases = []
        for p in ps:
            for m in f["by_pair"][p["work_id"]]:
                if m["case"] not in cases:
                    cases.append(m["case"])
        cases.sort(key=lambda c: list(CASE_LABEL).index(c) if c in CASE_LABEL else 99)
        header = " | ".join(f"{p['work_id']} `{p['from']}→{p['to']}` ({f['class'][p['work_id']]})" for p in ps)
        add(f"| case | {header} |")
        add("|---|" + "---|" * len(ps))
        for case in cases:
            cells = []
            for p in ps:
                ms = {m["metric"]: m for m in f["by_pair"][p["work_id"]] if m["case"] == case}
                if not ms:
                    cells.append("—")
                    continue
                parts = []
                for name, short in (("terminated", "종료"), ("progress_m", "전진"), ("error_xy", "추종오차"), ("error_yaw", "회전오차")):
                    if name in ms and ms[name]["signal"] != "0":
                        parts.append(f"{short}{arrow(ms[name])} {ms[name]['base']}→{ms[name]['cand']}")
                cells.append("<br>".join(parts) if parts else "·")
            add(f"| {case} ({CASE_LABEL.get(case, case)}) | " + " | ".join(cells) + " |")
        add("")
        for p in ps:
            ms = f["by_pair"][p["work_id"]]
            good = sum(1 for m in ms if m["better"] == "better")
            bad = sum(1 for m in ms if m["better"] == "worse")
            stalled = stall_cases(ms)
            add(f"- {p['work_id']} ({f['class'][p['work_id']]}): 좋아진 신호 `{good}` · 나빠진 신호 `{bad}` · 검사한 지표 `{len(ms)}`"
                f" · {walk_label(p)} 전진 속도 {p['base_rough_speed']} → {p['cand_rough_speed']}."
                + (f" **종료 감소가 전진 감소와 함께 나온 case: {', '.join(stalled)} — 넘어짐이 준 것이 아니라 멈춘 것일 수 있다.**"
                   if stalled else ""))
        add("")
    add("## 3. 특이점 (표에서 계산)")
    add("")
    add("- **걷던 정책을 멈추게 한 변경:** " + (" · ".join(
        f"{p['work_id']} `{p['term']}` `{p['from']}`→`{p['to']}` ({walk_label(p)} 속도 {p['base_rough_speed']} → {p['cand_rough_speed']}, 등급 {f['class'][p['work_id']]})"
        for p in f["collapse"]) or "없음") + ".")
    add("- **멈춘 정책을 걷게 한 변경:** " + (" · ".join(
        f"{p['work_id']} `{p['term']}`" for p in f["revive"]) or "없음 — 멈춘 기준(Default-01·chain01) 위의 한 항 변경은 어느 것도 걷기를 만들지 못했다") + ".")
    add("- **걷는 기준에서 조건이 같은 쌍(등급 A)이 하나도 없는 변수:** " + ", ".join(f"`{t}`" for t in f["no_walking_clean"]) + ".")
    add("- **기준 정책 고유 특이점** (같은 기준에서 나온 서로 다른 모델 전부가 같은 방향 — 변수가 아니라 기준 쪽 성질로 읽는다):")
    for q in f["baseline_quirks"]:
        add(f"  - {q['baseline']} `{q['case']}` {BEHAVIOR_SHORT[q['metric']]} {'▲' if q['signal'] == '1' else '▼'}: "
            f"기준 {q['base']} → " + " · ".join(f"{i} {c}" for i, c in zip(q["pairs"], q["cands"])) + ".")
    if not f["baseline_quirks"]:
        add("  - 없음.")
    add("")
    add("### 3-1. 변수별 동작 신호 (종료·전진만, 등급 병기)")
    add("")
    for term, ps in f["terms"].items():
        add(f"- **`{term}`**")
        for p in ps:
            add(f"  - {p['work_id']} `{p['from']}→{p['to']}` (등급 {f['class'][p['work_id']]}, 기준 {p['baseline']}): "
                + behavior_line(f["by_pair"][p["work_id"]]))
    add("")
    add("## 4. 이 표로 알 수 없는 것")
    add("")
    add("- 학습 seed 흔들림(전 회차 seed 42) — 등급 A 쌍도 한 번의 학습이다.")
    add("- 같은 회차의 체크포인트만 다른 비교는 없다 — 등급 C 쌍에서 시점 효과의 크기를 모른다.")
    add("- 7 case 평가(tier-1) 회차에는 계단 오르기·험지 옆걸음·경사 내리막이 없다 — 그 축의 영향은 등급과 무관하게 비어 있다.")
    add("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if "--report" not in argv:
        pairs, metrics = build()
        for name, rows in (("PAIRS.csv", pairs), ("PAIR_METRICS.csv", metrics)):
            print(f"{write(name, rows).relative_to(ROOT)}  rows={len(rows) - 1}")
    DOC.write_text(render(), encoding="utf-8")
    print(DOC.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
