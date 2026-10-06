#!/usr/bin/env python3
"""PC2 단일 점 판독 (2026-10-02).

설계: workspace/training/quadruped/upload/plan/GO2_PC2_DENSE_SWEEP_PROPOSAL_20261002.md §13-2 판독 순서 + §14-2 정정.
판독은 분류와 seed별 원값을 남길 뿐, 다음 점을 고르지 않는다(§13-1: 다음 점은 Codex 가 정한다).

순서
  1. 실행·자료 상태  — 보상 snapshot(B1 = A048 과 0항, 점 = 의도한 1항만 다름)과 유지 조건(학습 seed·env 수·iteration·
     평가 checkpoint·학습 코드·평가기·registry)을 따로 본다. 전체 env/config 해시 일치는 요구하지 않는다(§14-2-3).
     report·영상·telemetry 공백은 각각 기록한다. 공백이 있으면 overall=INVALID_OR_INCOMPLETE 이지만 부분 관측은 지우지 않는다.
     sentinel 이 과거 서버·PC1 관측 범위 밖이면 EVAL_LAYER_DIFFERS 표시만 한다(무효·추가 평가로 자동 연결하지 않음, §14-2-1).
  2. 정지 — moving gate(forward_nominal seed 101, 러너와 같은 규칙).
  3. 표적 — 험지 옆걸음 자세 낙상 seed별(32대). 세 seed 모두 감소 = TARGET_IMPROVED, 모두 증가 = TARGET_WORSENED, 그 밖 MIXED.
     동률·결측·B1 이 0 인 seed(더 줄 수 없음)를 따로 표시한다.
  4. 이동·추종 — 명령 방향 속도와 명령의 차(부호 있음), 추종 RMSE. 속도 증가 자체가 아니라 명령과의 오차로 읽고, 과속은 개선이 아니다
     (§14-2-2). 표적 분류와 별도 필드로 둔다. 한두 seed 손실도 경고로 남긴다.
  5. 보호 — 항목마다 세 seed 모두 B1 보다 나쁘면 COMMON_LOSS_OBSERVED, 아니면 COMMON_LOSS_NOT_OBSERVED(비열등 아님).
     나빠진 seed 와 결측을 함께 적는다. 서로 다른 행동을 합산·상쇄하지 않는다.
  6. 조합 분류(§13-2 표) — 확장·방향 전환·조합을 자동으로 열지 않는다.

    python -B tools/go2_pc2_point_readout.py --key <point key> --point <harvest dir> [--base <B1 harvest dir>] [--out DIR]
"""
from __future__ import annotations

import argparse
import csv
import functools
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(QUAD))
import go2_climb_count as climb  # noqa: E402
import go2_g_a057_sweep_compare as compare  # noqa: E402  (stall 정의 재사용)
import go2_state_channel_split as channels  # noqa: E402  (판정 채널 재사용)
import go2_state_outcome as outcome  # noqa: E402  (steps 로더 재사용)
from candidate_suite_checks import reward_weights  # noqa: E402

CHECKS = QUAD / "candidate_suite_checks.py"
SEEDS = ("101", "202", "303")
ROBOTS = 32
REWARD_TERMS = ("track_lin_vel_xy_exp", "ang_vel_xy_l2", "feet_air_time", "lin_vel_z_l2",
                "action_rate_l2", "flat_orientation_l2")
A048_REWARDS = {"track_lin_vel_xy_exp": 1.5, "ang_vel_xy_l2": -0.05, "feet_air_time": 0.2,
                "lin_vel_z_l2": -1.25, "action_rate_l2": -0.01, "flat_orientation_l2": 0.0}
HELD_KEYS = ("TRAIN_SEED", "NUM_ENVS", "MAX_ITERATIONS", "EVAL_CHECKPOINT_ITER", "GO2_STAGE",
             "EXPECTED_EVALUATOR_SHA", "EXPECTED_REGISTRY_SHA", "BASELINE_MODEL_SHA")
REWARD_FILES = ("candidate/quadruped_rewards.py", "reference/baseline_quadruped_rewards.py",
                "reference/reward_base_quadruped_rewards.py", "expected_rewards.json", "run_config.env",
                "experiment.json", "README.txt")
# 과거 관측(서버 10 run, PC1 3 run)의 G-A033 sentinel 자세 낙상 — 허용구간이 아니라 비교용 관측값(§14-2-1).
SENTINEL_OBSERVED = {("101", "rough_lateral"): (19, 20), ("101", "rough_forward"): (1, 2),
                     ("101", "forward_nominal"): (0, 0), ("202", "slope_plus_20"): (0, 0),
                     ("202", "dr_seed_202"): (1, 1)}
TARGET_CASE = "rough_lateral"
# 보호 항목: (이름, 종류, case, 나빠지는 방향, 계단 높이)
PROTECTION = (
    ("stairs_10_ge2", "climb_ge2", "stairs_10_down", "down", 0.10),
    ("stairs_15_ge2", "climb_ge2", "stairs_15_down", "down", 0.15),
    ("yaw_right_falls", "falls", "combined_yaw_right", "up", None),
    ("push_pos_x_falls", "falls", "push_pos_x", "up", None),
    ("push_neg_x_falls", "falls", "push_neg_x", "up", None),
    ("push_pos_y_falls", "falls", "push_pos_y", "up", None),
    ("push_neg_y_falls", "falls", "push_neg_y", "up", None),
    ("rough_forward_falls", "falls", "rough_forward", "up", None),
    ("rough_forward_cmd_error", "cmd_error", "rough_forward", "up", None),
    ("forward_nominal_cmd_error", "cmd_error", "forward_nominal", "up", None),
)
SETTLE_S = 1.0
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
B1_KEY = "a048_seed42"
# 판독에 쓰는 case — 세 seed 모두 summary·steps 가 있어야 한다(§16 R1).
REQUIRED_CASES = tuple(sorted({TARGET_CASE, "forward_nominal"} | {it[2] for it in PROTECTION}))


def cases(h: Path) -> Path:
    return h / "evaluation" / "candidate" / "cases"


def load_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def env_file(p: Path) -> dict[str, str]:
    out = {}
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def fnum(x) -> float | None:
    """유한한 수만 값으로 인정한다. None·NaN·Infinity·bool 은 결측(§16 R3). 측정된 0 은 유효값이다."""
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        return None
    return float(x)


def sha_file(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def first_token(p: Path) -> str | None:
    if not p.is_file():
        return None
    t = p.read_text(encoding="utf-8").split()
    return t[0].lstrip("*") if t else None


def rewards_of(h: Path) -> dict | None:
    p = h / "training" / "env.yaml"
    if not p.is_file():
        return None
    w = reward_weights(p.read_text(encoding="utf-8"))
    return {k: w.get(k) for k in REWARD_TERMS}


def code_identity(h: Path) -> dict[str, str]:
    """PACKAGE_SHA256SUMS 중 보상·설정 파일을 뺀 줄 = 학습 코드·평가기 등 유지 파일의 해시."""
    p = h / "meta" / "PACKAGE_SHA256SUMS.txt"
    out = {}
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "  " in line:
                digest, name = line.split("  ", 1)
                if name not in REWARD_FILES:
                    out[name] = digest
    return out


def gpu_name(h: Path) -> str | None:
    p = h / "meta" / "gpu.csv"
    if not p.is_file():
        return None
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return None
    return lines[0].split(",")[0].strip() or None


# ---------- 1. 실행·자료 상태 ----------
def identity(h: Path, key: str) -> tuple[list[str], dict]:
    """기존 회수 증거로 run 대응을 잇는다(§16 R2): RUNNER_STATUS ↔ CHECKPOINT_PIN ↔ checkpoint·env.yaml 파일 해시 ↔
    평가 identity.json ↔ report(REPORT_STATUS 출처 경로·report 해시). 빈 값끼리 같다는 것은 근거가 아니다."""
    gaps: list[str] = []
    rs = env_file(h / "RUNNER_STATUS.txt")
    if not rs:
        return ["identity: RUNNER_STATUS.txt 없음"], {}
    if rs.get("RUNNER_RC") != "0":
        gaps.append(f"identity: RUNNER_RC={rs.get('RUNNER_RC')}")
    if not re.search(rf"_{re.escape(key)}_", rs.get("RUN_ID", "")):
        gaps.append(f"identity: RUN_ID({rs.get('RUN_ID')}) 가 key {key} 와 대응하지 않음")
    model, envsha = rs.get("CANDIDATE_MODEL_SHA", ""), rs.get("CANDIDATE_ENV_SHA", "")
    ev, rg = rs.get("EVALUATOR_SHA", ""), rs.get("REGISTRY_SHA", "")
    for name, v in (("CANDIDATE_MODEL_SHA", model), ("CANDIDATE_ENV_SHA", envsha), ("EVALUATOR_SHA", ev),
                    ("REGISTRY_SHA", rg)):
        if not SHA_RE.match(v):
            gaps.append(f"identity: {name} 없음 또는 형식 아님")
    pin = env_file(h / "training" / "CHECKPOINT_PIN.txt")
    if pin.get("EVAL_CHECKPOINT_ITER") != "900":
        gaps.append(f"identity: 평가 checkpoint iter={pin.get('EVAL_CHECKPOINT_ITER')}")
    if not SHA_RE.match(model) or pin.get("EVAL_CHECKPOINT_SHA") != model:
        gaps.append("identity: CHECKPOINT_PIN 의 평가 checkpoint 해시가 RUNNER 모델 해시와 다름")
    if not SHA_RE.match(model) or sha_file(h / "training" / "model_best.pt") != model:
        gaps.append("identity: training/model_best.pt 해시가 RUNNER 모델 해시와 다름 또는 파일 없음")
    if not SHA_RE.match(envsha) or sha_file(h / "training" / "env.yaml") != envsha:
        gaps.append("identity: training/env.yaml 해시가 RUNNER env 해시와 다름 또는 파일 없음")
    idj = load_json(h / "evaluation" / "candidate" / "identity.json") or {}
    for field, want in (("model_sha256", model), ("env_sha256", envsha), ("evaluator_sha256", ev),
                        ("registry_sha256", rg)):
        if not SHA_RE.match(want) or idj.get(field) != want:
            gaps.append(f"identity: 평가 identity.json {field} 불일치 또는 없음")
    rstat = env_file(h / "exported" / "REPORT_STATUS.txt")
    report = h / "exported" / "report.html"
    if rstat.get("REPORT_STATUS") != "REPORT_ACQUIRED":
        gaps.append(f"report: REPORT_STATUS={rstat.get('REPORT_STATUS')} (REPORT_REQUIRED_NOT_ACQUIRED)")
    elif f"/{key}/" not in rstat.get("SOURCE", ""):
        gaps.append(f"report: 출처 경로({rstat.get('SOURCE')})가 key {key} 의 run 과 대응하지 않음")
    if not report.is_file() or report.stat().st_size == 0:
        gaps.append("report: exported/report.html 없음 또는 빈 파일")
    elif first_token(h / "exported" / "report.html.sha256") != sha_file(report):
        gaps.append("report: report.html 해시가 report.html.sha256 과 다름 또는 없음")
    # 실제 값(RUNNER·평가 identity) ↔ 기대 값(run_config) ↔ meta 해시 파일을 잇는다(§18 R2).
    cfg = env_file(h / "meta" / "run_config.env")
    for name, actual, expect_key, meta_file in (("evaluator", ev, "EXPECTED_EVALUATOR_SHA", "evaluator.sha256"),
                                                ("registry", rg, "EXPECTED_REGISTRY_SHA", "registry.sha256")):
        if not SHA_RE.match(actual) or cfg.get(expect_key) != actual:
            gaps.append(f"identity: 실제 {name} 해시가 run_config {expect_key} 와 다름 또는 없음")
        if not SHA_RE.match(actual) or first_token(h / "meta" / meta_file) != actual:
            gaps.append(f"identity: 실제 {name} 해시가 meta/{meta_file} 와 다름 또는 없음")
    seed = rs.get("TRAIN_SEED", "")
    if not seed.isdigit() or cfg.get("TRAIN_SEED") != seed:
        gaps.append(f"identity: 실제 학습 seed({seed}) 가 run_config TRAIN_SEED({cfg.get('TRAIN_SEED')}) 와 다름 또는 없음")
    gpu = gpu_name(h)
    if not gpu:
        gaps.append("identity: meta/gpu.csv 장비 기록 없음")
    return gaps, {"run_id": rs.get("RUN_ID"), "model_sha": model, "env_sha": envsha, "evaluator_sha": ev,
                  "registry_sha": rg, "gpu_model": gpu, "train_seed": seed}


STEP_COLS = ("env_id", "time_s", "cmd_vx", "cmd_vy", "actual_vx", "actual_vy", "root_x", "root_y", "root_z",
             "terrain_z", "proj_grav_z", "height_rel", "terminated", "truncated")


@functools.lru_cache(maxsize=None)
def steps_problem(path: str) -> str | None:
    """steps.csv 가 판독에 쓸 수 있는지(§18 R1). None 이면 사용 가능, 아니면 구체적 사유.
    기준은 같은 case 의 summary·metadata 다: env 집합 = 0..num_envs-1, env 마다 행 수 = steps, 전체 행 = rows.
    조기 종료한 로봇도 종료 행 뒤 기록이 이어지므로(실측: 32대 x 1000행) 행이 빠진 것은 회수 누락이다.
    필수 열이 없거나, 수가 아니거나, 비유한 값이면 사용하지 않는다. 0 으로 대체하지 않는다."""
    p = Path(path)
    s, m = load_json(p.parent / "summary.json") or {}, load_json(p.parent / "metadata.json") or {}
    n_env, steps, rows = m.get("num_envs"), s.get("steps"), s.get("rows")
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in (n_env, steps, rows)):
        return "기대 env 수·행 수(metadata num_envs, summary steps·rows) 없음"
    counts: dict[int, int] = {}
    total = 0
    try:
        with p.open(encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            missing_cols = [c for c in STEP_COLS if c not in (rd.fieldnames or [])]
            if missing_cols:
                return f"필수 열 없음 {missing_cols}"
            for i, r in enumerate(rd, start=2):
                for c in STEP_COLS:
                    try:
                        v = float(r[c])
                    except (TypeError, ValueError):
                        return f"{i}행 {c}={r[c]!r} 수 아님"
                    if not math.isfinite(v):
                        return f"{i}행 {c} 비유한 값"
                e = int(float(r["env_id"]))
                counts[e] = counts.get(e, 0) + 1
                total += 1
    except (OSError, UnicodeDecodeError, csv.Error) as err:
        return f"읽기 실패 {type(err).__name__}"
    if set(counts) != set(range(n_env)):
        return f"env coverage {len(counts)}/{n_env}"
    short = sorted(e for e, k in counts.items() if k != steps)
    if short:
        return f"env {short[:5]} 행 수가 steps {steps} 와 다름"
    if total != rows:
        return f"전체 행 {total} != rows {rows}"
    return None


# 도달 후 판독(stairs_post_reach)은 go2_state_outcome.load 를 재사용한다. 그 로더는 아래 열이 모두 있어야 하고
# 빈 칸이 아닌 값은 float 로 읽는다(§20 R1 잔여). 판정에 실제로 쓰는 열(time_s·actual_vx/vy·root_*·proj_grav_z·
# height_rel·terminated·truncated)은 STEP_COLS 에서 이미 수치 검사한다. 나머지는 로더가 읽는 형식만 맞으면 된다.
POST_REACH_COLS = tuple(dict.fromkeys(outcome.COLS + ("env_id", "upright", "terminated", "truncated")))
POST_REACH_CASES = frozenset(it[2] for it in PROTECTION if it[1] == "climb_ge2")


@functools.lru_cache(maxsize=None)
def post_reach_problem(path: str) -> str | None:
    """steps.csv 를 go2_state_outcome.load 가 예외 없이 읽을 수 있는지. None 이면 가능, 아니면 구체적 사유.
    선택 입력을 필수로 늘리지 않는다: 로더가 실제로 요구하는 열의 존재와 읽기 형식(빈 칸 또는 수)만 본다."""
    p = Path(path)
    try:
        with p.open(encoding="utf-8", newline="") as fh:
            rd = csv.reader(fh)
            head = next(rd, None) or []
            missing_cols = [c for c in POST_REACH_COLS if c not in head]
            if missing_cols:
                return f"도달 후 판독 필수 열 없음 {missing_cols}"
            ix = {c: head.index(c) for c in outcome.COLS}
            ie = head.index("env_id")
            for i, row in enumerate(rd, start=2):
                if len(row) != len(head):
                    return f"도달 후 판독 {i}행 칸 수 {len(row)} != 열 수 {len(head)}"
                try:
                    int(row[ie])  # 로더는 int(env_id) 로 읽는다 — '0.0' 은 STEP_COLS 수치 검사는 통과해도 여기서 막는다
                except ValueError:
                    return f"도달 후 판독 {i}행 env_id={row[ie]!r} 정수 아님"
                for c, j in ix.items():
                    if row[j] == "":
                        continue
                    try:
                        float(row[j])
                    except ValueError:
                        return f"도달 후 판독 {i}행 {c}={row[j]!r} 수 아님"
    except (OSError, UnicodeDecodeError, csv.Error) as err:
        return f"도달 후 판독 읽기 실패 {type(err).__name__}"
    return None


def steps_ok(h: Path, seed: str, case: str) -> Path | None:
    p = cases(h) / f"seed_{seed}" / case / "steps.csv"
    return p if p.is_file() and steps_problem(str(p)) is None else None


def required_present(h: Path) -> list[str]:
    """판독에 쓰는 case·seed 의 summary·steps 가 실제로 있는지(§16 R1). 개수만 세지 않는다."""
    miss = []
    need = {(s, c) for s in SEEDS for c in REQUIRED_CASES}
    for s, c in sorted(need):
        d = cases(h) / f"seed_{s}" / c
        for f in ("summary.json", "steps.csv"):
            if not (d / f).is_file():
                miss.append(f"{s}/{c}/{f}")
        if (d / "steps.csv").is_file():
            why = steps_problem(str(d / "steps.csv"))
            if why:
                miss.append(f"{s}/{c}/steps.csv: {why}")
            elif c in POST_REACH_CASES:
                why = post_reach_problem(str(d / "steps.csv"))
                if why:
                    miss.append(f"{s}/{c}/steps.csv: {why}")
    return miss


def state(h: Path, key: str, ref_rewards: dict | None, expected_change: tuple[str, float] | None) -> dict:
    """한 수확물 자체의 상태. ref_rewards 는 B1 이면 A048 정본, 점이면 B1 의 학습 보상."""
    gaps: list[str] = []
    rs = env_file(h / "RESULT_STATUS.txt")
    if not (rs.get("RESULT_STATE") == "FULL" and rs.get("COLLECTION_STATUS") == "FULL_69_COMPLETE"):
        gaps.append(f"run: RESULT_STATE={rs.get('RESULT_STATE')} COLLECTION_STATUS={rs.get('COLLECTION_STATUS')}")
    videos = sorted((h / "evaluation" / "candidate" / "videos").glob("*.mp4"))
    if len(videos) != 10:
        gaps.append(f"video: {len(videos)}/10")
    summaries = list(cases(h).glob("seed_*/*/summary.json"))
    if len(summaries) != 69:
        gaps.append(f"telemetry: summary {len(summaries)}/69")
    miss = required_present(h)
    if miss:
        gaps.append(f"telemetry: 필수 자료 결측·손상 {len(miss)}건 (예: {miss[:3]})")
    id_gaps, info = identity(h, key)
    gaps += id_gaps
    rw = rewards_of(h)
    reward_check = "MISSING"
    if rw is None:
        gaps.append("reward snapshot: training/env.yaml 없음")
    elif ref_rewards is None:
        gaps.append("reward snapshot: 비교 기준 보상 없음")
    else:
        diff = sorted(k for k in REWARD_TERMS if rw.get(k) != ref_rewards.get(k))
        want = [expected_change[0]] if expected_change else []
        ok = diff == want and (not expected_change or math.isclose(rw[expected_change[0]], expected_change[1]))
        reward_check = "OK" if ok else f"MISMATCH diff={diff} want={want}"
        if not ok:
            gaps.append("reward snapshot: " + reward_check)
    return {"overall": "COMPLETE" if not gaps else "INVALID_OR_INCOMPLETE", "gaps": gaps,
            "reward_snapshot": reward_check, "identity": info, "partial_observations_kept": True}


def held_value_ok(k: str, v: str | None) -> bool:
    if not v:
        return False
    if k.endswith("_SHA"):
        return bool(SHA_RE.match(v))
    if k in ("TRAIN_SEED", "NUM_ENVS", "MAX_ITERATIONS", "EVAL_CHECKPOINT_ITER"):
        return v.isdigit()
    return True


def comparison(point: Path, base: Path) -> dict:
    """의도한 보상 한 항을 뺀 유지 조건(§14-2-3) + 같은 장비 경계(§16 R2). 양쪽 값의 존재·형식을 먼저 본다."""
    bad: list[str] = []
    pc, bc = env_file(point / "meta" / "run_config.env"), env_file(base / "meta" / "run_config.env")
    for k in HELD_KEYS:
        a, b = pc.get(k), bc.get(k)
        if not (held_value_ok(k, a) and held_value_ok(k, b)):
            bad.append(f"{k} 없음 또는 형식 아님")
        elif a != b:
            bad.append(f"{k} 다름({a} vs {b})")
    ci, cb = code_identity(point), code_identity(base)
    if not ci or not cb:
        bad.append("학습 코드 해시 목록 없음")
    elif ci != cb:
        bad.append("학습·평가 코드 해시 다름")
    for f in ("evaluator.sha256", "registry.sha256"):
        a, b = first_token(point / "meta" / f), first_token(base / "meta" / f)
        if not (a and b and SHA_RE.match(a) and SHA_RE.match(b)):
            bad.append(f"{f} 없음 또는 형식 아님")
        elif a != b:
            bad.append(f"{f} 다름")
    ra, rb = env_file(point / "RUNNER_STATUS.txt"), env_file(base / "RUNNER_STATUS.txt")
    for k in ("EVALUATOR_SHA", "REGISTRY_SHA", "TRAIN_SEED"):
        a, b = ra.get(k), rb.get(k)
        if not (a and b):
            bad.append(f"실제 {k} 없음")
        elif a != b:
            bad.append(f"실제 {k} 다름")
    ga, gb = gpu_name(point), gpu_name(base)
    if not (ga and gb):
        bad.append("GPU 기록 없음")
    elif ga != gb:
        bad.append(f"다른 GPU 모델({ga} vs {gb}) — 장비 간 비교 금지")
    return {"label": "OK" if not bad else "MISMATCH", "problems": bad, "gpu_model": ga,
            "note": "GPU 모델이 같다는 확인이지 같은 PC·환경의 증명이 아니다(§18-3 WATCH)."}


def sentinel(point: Path) -> dict:
    out, differs = {}, []
    for (seed, case), (lo, hi) in SENTINEL_OBSERVED.items():
        s = load_json(point / "evaluation" / "g_a033_sentinel" / "cases" / f"seed_{seed}" / case / "summary.json")
        v = None if s is None else s.get("posture_fall_env_count_pessimistic")
        out[f"{seed}/{case}"] = {"value": v, "observed_server_pc1": [lo, hi]}
        if v is None or not lo <= v <= hi:
            differs.append(f"{seed}/{case}")
    return {"label": "EVAL_LAYER_DIFFERS" if differs else "WITHIN_PAST_OBSERVATION", "outside": differs,
            "values": out, "note": "과거 관측 범위이며 허용구간이 아니다. 무효·추가 평가로 자동 연결하지 않는다."}


# ---------- 2. 정지 ----------
def moving(h: Path) -> str:
    p = cases(h) / "seed_101" / "forward_nominal" / "summary.json"
    if not p.is_file():
        return "MISSING"
    rc = subprocess.run([sys.executable, "-B", str(CHECKS), "moving", str(p)], capture_output=True).returncode
    return {0: "MOVING", 1: "STATIONARY"}.get(rc, "MISSING")


# ---------- 공통 지표 ----------
def falls(h: Path, seed: str, case: str) -> int | None:
    s = load_json(cases(h) / f"seed_{seed}" / case / "summary.json")
    if not s or s.get("posture_measured") is not True or s.get("posture_fall_verdict_ambiguous") is not False:
        return None
    if s.get("posture_envs_observed") != ROBOTS:
        return None
    lo, hi = s.get("posture_fall_env_count_optimistic"), s.get("posture_fall_env_count_pessimistic")
    return int(hi) if isinstance(hi, int) and lo == hi else None


def climb_ge2(h: Path, seed: str, case: str, height: float) -> int | None:
    p = steps_ok(h, seed, case)
    if p is None:
        return None
    r = climb.count(p, height)
    return int(r["ge2"]) if r and int(r["robots"]) == ROBOTS else None


def stairs_post_reach(h: Path, seed: str, case: str, height: float) -> dict | None:
    """≥2단에 도달한 로봇의 도달 뒤 상태(§13-2-5, §16 R4, §18 R4). 도달 판정은 go2_climb_count 와 같은 식,
    정체는 go2_g_a057_sweep_compare.stall(1 s 연속 < 0.05 m/s), 판정 채널은 go2_state_channel_split.channel.
    post_channel_* 는 첫 도달 행부터 그 episode 의 끝(첫 종료·절단 행 포함, 그 뒤 reset 행 제외)만 읽는다.
    run_channel_* 는 같은 로봇의 전체 run 채널이며 이름을 나눠 보존한다. 새 문턱 없음. 자료가 부족·손상이면 None."""
    p = steps_ok(h, seed, case)
    if p is None or post_reach_problem(str(p)) is not None:
        return None
    c = climb.count(p, height)
    if not c or int(c["robots"]) != ROBOTS:
        return None
    envs = outcome.load(p)
    out = {"reached_ge2": 0, "stalled_after_reach": 0, **{f"post_channel_{ch}": 0 for ch in channels.CHANNELS},
           **{f"run_channel_{ch}": 0 for ch in channels.CHANNELS}}
    for rows in envs.values():
        ep = outcome.first_episode(rows)
        if not ep or any(r["root_z"] is None or r["root_x"] is None or r["root_y"] is None for r in ep):
            continue
        z0 = ep[min(climb.SETTLE_ROW, len(ep) - 1)]["root_z"]
        x0, y0 = ep[0]["root_x"], ep[0]["root_y"]
        best, reach = 0.0, None
        for i, r in enumerate(ep):
            if (r["root_x"] - x0) ** 2 + (r["root_y"] - y0) ** 2 < climb.MIN_TRAVEL_M ** 2:
                continue
            best = max(best, r["root_z"] - z0 if c["direction"] == "climb" else z0 - r["root_z"])
            if (best + climb.STEP_TOLERANCE * height) // height >= 2:
                reach = i
                break
        if reach is None:
            continue
        end = rows[len(ep)] if len(ep) < len(rows) else None  # 그 episode 를 끝낸 종료·절단 행
        post = ep[reach:] + ([end] if end is not None else [])
        out["reached_ge2"] += 1
        out["stalled_after_reach"] += int(compare.stall(ep[reach:]))
        out[f"post_channel_{channels.channel(post)}"] += 1
        out[f"run_channel_{channels.channel(rows)}"] += 1
    if out["reached_ge2"] != int(c["ge2"]):
        return None  # 도달 수가 계수기와 다르면 쓰지 않는다
    return out


def command_motion(h: Path, seed: str, case: str) -> dict | None:
    """명령 방향 속도(부호 있음)와 명령 크기. 종료 전·1 s 이후 행만 쓴다.
    steps 가 coverage·수치 검사(steps_problem)를 통과하지 못하면 결측 — 남은 일부 로봇만으로 평균내지 않는다(§18 R1)."""
    p = steps_ok(h, seed, case)
    if p is None:
        return None
    par, mag = [], []
    for env_rows in climb.alive_rows(p).values():
        for r in env_rows:
            if float(r["time_s"]) < SETTLE_S:
                continue
            cx, cy, ax, ay = (float(r[k]) for k in ("cmd_vx", "cmd_vy", "actual_vx", "actual_vy"))
            m = math.hypot(cx, cy)
            if m == 0:
                continue
            par.append((ax * cx + ay * cy) / m)
            mag.append(m)
    s = load_json(cases(h) / f"seed_{seed}" / case / "summary.json") or {}
    rmse = fnum(s.get("tracking_xy_rmse"))
    if not par or rmse is None:
        return None
    v, c = sum(par) / len(par), sum(mag) / len(mag)
    return {"v_cmd_axis": v, "cmd": c, "signed_error": v - c, "abs_error": abs(v - c),
            "overspeed": v > c, "tracking_xy_rmse": rmse}


# ---------- 3. 표적 ----------
def target(point: Path, base: Path | None) -> dict:
    rows = {}
    for s in SEEDS:
        p, b = falls(point, s, TARGET_CASE), (falls(base, s, TARGET_CASE) if base else None)
        rows[s] = {"b1": b, "point": p, "delta": None if p is None or b is None else p - b,
                   "floor_b1_zero": b == 0}
    if base is None:
        return {"class": "NO_BASE", "seeds": rows}
    deltas = [r["delta"] for r in rows.values()]
    missing = [s for s, r in rows.items() if r["delta"] is None]
    ties = [s for s, r in rows.items() if r["delta"] == 0]
    if missing:
        cls = "MISSING"
    elif all(d < 0 for d in deltas):
        cls = "TARGET_IMPROVED"
    elif all(d > 0 for d in deltas):
        cls = "TARGET_WORSENED"
    else:
        cls = "MIXED"
    floor = [s for s, r in rows.items() if r["floor_b1_zero"]]
    note = f"B1 낙상 0 인 seed {floor} 는 더 줄 수 없어 '세 seed 감소'를 충족할 수 없다" if floor else ""
    return {"class": cls, "seeds": rows, "tie_seeds": ties, "missing_seeds": missing, "floor_note": note,
            "pooled_b1": sum(r["b1"] for r in rows.values() if r["b1"] is not None),
            "pooled_point": sum(r["point"] for r in rows.values() if r["point"] is not None)}


# ---------- 4. 이동·추종 ----------
def motion(point: Path, base: Path | None, case: str = TARGET_CASE) -> dict:
    rows, worse = {}, []
    for s in SEEDS:
        p, b = command_motion(point, s, case), (command_motion(base, s, case) if base else None)
        w = None
        if p and b:
            w = p["abs_error"] > b["abs_error"] or p["tracking_xy_rmse"] > b["tracking_xy_rmse"]
            if w:
                worse.append(s)
        rows[s] = {"b1": b, "point": p, "worse": w}
    if base is None:
        label = "NO_BASE"
    elif any(r["worse"] is None for r in rows.values()):
        label = "MISSING"
    elif len(worse) == len(SEEDS):
        label = "ALL_SEEDS_WORSE"
    elif worse:
        label = "SOME_SEEDS_WORSE"
    else:
        label = "NONE_WORSE"
    over = [s for s, r in rows.items() if r["point"] and r["point"]["overspeed"]]
    return {"case": case, "label": label, "worse_seeds": worse, "overspeed_seeds": over, "seeds": rows,
            "rule": "명령 방향 속도와 명령의 오차·추종 RMSE 가 커지면 나쁨. 명령보다 빠른 것(과속)은 개선이 아니다. "
                    "RMSE·속도 결측·비유한 값은 결측으로 전파한다."}


# ---------- 5. 보호 ----------
def protection_item(point: Path, base: Path, item: tuple) -> dict:
    name, kind, case, worse_dir, height = item
    rows = {}
    for s in SEEDS:
        if kind == "climb_ge2":
            p, b = climb_ge2(point, s, case, height), climb_ge2(base, s, case, height)
        elif kind == "falls":
            p, b = falls(point, s, case), falls(base, s, case)
        else:
            mp, mb = command_motion(point, s, case), command_motion(base, s, case)
            p, b = (mp["abs_error"] if mp else None), (mb["abs_error"] if mb else None)
        delta = None if p is None or b is None else p - b
        bad = None if delta is None else (delta < 0 if worse_dir == "down" else delta > 0)
        rows[s] = {"b1": b, "point": p, "delta": delta, "worse": bad}
        if kind == "climb_ge2":
            rows[s]["post_reach"] = {"b1": stairs_post_reach(base, s, case, height),
                                     "point": stairs_post_reach(point, s, case, height)}
    missing = [s for s, r in rows.items() if r["worse"] is None]
    worse = [s for s, r in rows.items() if r["worse"]]
    if missing:
        label = "MISSING"
    elif len(worse) == len(SEEDS):
        label = "COMMON_LOSS_OBSERVED"
    else:
        label = "COMMON_LOSS_NOT_OBSERVED"
    post_missing = [s for s, r in rows.items() if "post_reach" in r and None in r["post_reach"].values()]
    return {"item": name, "case": case, "label": label, "worse_seeds": worse, "missing_seeds": missing,
            "post_reach_missing_seeds": post_missing, "seeds": rows,
            "note": "COMMON_LOSS_NOT_OBSERVED 는 비열등의 증명이 아니다. 나빠진 seed 는 값과 함께 본다. "
                    "계단 post_reach 는 ≥2단 도달 뒤 정체·판정 채널(문턱 없음)."}


def protection(point: Path, base: Path | None) -> list[dict]:
    return [] if base is None else [protection_item(point, base, it) for it in PROTECTION]


# ---------- 6. 조합 분류 ----------
def combined(point_state: dict, base_state: dict | None, comp: dict | None, gate: str, tgt: dict, mot: dict,
             prot: list[dict]) -> dict:
    common = [p["item"] for p in prot if p["label"] == "COMMON_LOSS_OBSERVED"]
    partial = [p["item"] for p in prot if p["label"] == "COMMON_LOSS_NOT_OBSERVED" and p["worse_seeds"]]
    missing = ([] if gate in ("MOVING", "STATIONARY") else ["moving_gate"]) \
        + ([] if tgt["class"] not in ("MISSING", "NO_BASE") else ["target"]) \
        + ([] if mot["label"] not in ("MISSING", "NO_BASE") else ["motion_tracking"]) \
        + [p["item"] for p in prot if p["label"] == "MISSING" or p.get("post_reach_missing_seeds")] \
        + ([] if prot else ["protection"])
    # B1 이 먼저다: B1 이 틀리면 점의 보상 대조도 그 B1 기준이라 함께 깨지므로 근본 원인을 이름으로 낸다.
    if base_state is None or base_state["overall"] != "COMPLETE":
        cls = "HOLD_BASE_INVALID"
    elif point_state["overall"] != "COMPLETE":
        cls = "HOLD_INVALID_OR_INCOMPLETE"
    elif comp is None or comp["label"] != "OK":
        cls = "HOLD_COMPARISON_INVALID"
    elif gate == "STATIONARY":
        cls = "STATIONARY"
    elif missing:
        cls = "HOLD_MISSING"
    elif tgt["class"] == "TARGET_IMPROVED" and mot["label"] in ("ALL_SEEDS_WORSE", "SOME_SEEDS_WORSE"):
        cls = "FALLS_DOWN_MOTION_TRACKING_LOSS"
    elif tgt["class"] == "TARGET_IMPROVED":
        cls = "PROMISING_SINGLE_POINT" if not common else "TRADE_OFF_POINT"
    elif tgt["class"] == "MIXED":
        cls = "MIXED_COST_HOLD" if common else "MIXED_KEPT"
    else:
        cls = "TARGET_WORSENED"
    meaning = {
        "HOLD_INVALID_OR_INCOMPLETE": "점 수확물 공백 — 성능 분류 보류(부분 관측은 보존).",
        "HOLD_BASE_INVALID": "B1 자체가 A048 대응·완결·identity 를 충족하지 않음 — 비교 보류.",
        "HOLD_COMPARISON_INVALID": "유지 조건 또는 장비가 B1 과 다름 — 비교 보류.",
        "STATIONARY": "정지. 바깥 점 미실행은 비용 결정이며 기각이 아니다.",
        "HOLD_MISSING": "필수 지표 결측으로 분류 보류(부분 관측은 보존).",
        "FALLS_DOWN_MOTION_TRACKING_LOSS": "낙상 감소 / 이동·추종 손실 — 깨끗한 표적 개선이 아니다.",
        "PROMISING_SINGLE_POINT": "유망 단일점으로 보존. 확장은 자동이 아니다.",
        "TRADE_OFF_POINT": "교환점으로 보존(ang 이면 −0.06 검토 자격, 자동 실행 아님).",
        "MIXED_COST_HOLD": "비용상 보류.",
        "MIXED_KEPT": "혼재로 보존. 확장 근거가 아니다.",
        "TARGET_WORSENED": "그 방향의 바깥 점은 열지 않는다(영구 기각 아님).",
    }[cls]
    return {"class": cls, "meaning": meaning, "missing_parts": missing, "common_loss_items": common,
            "partial_loss_items": partial,
            "next_point": "자동 선택 없음 — 표적·보호 결과와 남은 비용으로 Codex 가 정한다."}


def read(key: str, point: Path, base: Path | None, expected_change: tuple[str, float] | None,
         base_key: str = B1_KEY) -> dict:
    """점 판독. base=None 이면 B1 자체 판독(보상은 A048 정본과 대조)."""
    if base is None:
        st_point = state(point, key, dict(A048_REWARDS), None)
        st_base = comp = None
    else:
        st_base = state(base, base_key, dict(A048_REWARDS), None)
        st_point = state(point, key, rewards_of(base), expected_change)
        comp = comparison(point, base)
    gate = moving(point)
    tgt = target(point, base)
    mot = motion(point, base)
    prot = protection(point, base)
    return {"key": key, "point": str(point), "base": None if base is None else str(base), "state": st_point,
            "base_state": st_base, "comparison": comp, "sentinel": sentinel(point), "moving_gate": gate,
            "target": tgt, "motion_tracking": mot, "protection": prot,
            "combined": combined(st_point, st_base, comp, gate, tgt, mot, prot) if base is not None else
            {"class": "B1_SELF_READ", "meaning": "B1 자체 판독(비교 없음).", "missing_parts": [],
             "common_loss_items": [], "partial_loss_items": [], "next_point": "자동 선택 없음"}}


def to_md(r: dict) -> str:
    st = r["state"]
    L = [f"# PC2 점 판독 — {r['key']}", "", f"- 점: `{r['point']}`", f"- 직접 대조군(B1): `{r['base']}`",
         f"- 점 자료 상태: {st['overall']} (보상 snapshot {st['reward_snapshot']}, GPU 모델 {st['identity'].get('gpu_model')})"]
    L += [f"  - 공백: {g}" for g in st["gaps"]]
    if r["base_state"] is not None:
        L.append(f"- B1 자료 상태: {r['base_state']['overall']} (A048 대조 {r['base_state']['reward_snapshot']})")
        L += [f"  - 공백: {g}" for g in r["base_state"]["gaps"]]
    if r["comparison"] is not None:
        L.append(f"- 유지 조건·GPU 모델 비교: {r['comparison']['label']} {r['comparison']['problems']} ({r['comparison']['note']})")
    L += [f"- sentinel: {r['sentinel']['label']} {r['sentinel']['outside']}", f"- 정지 판정: {r['moving_gate']}",
          f"- 표적(험지 옆걸음 자세 낙상): {r['target']['class']} {r['target'].get('floor_note', '')}"]
    for s, v in r["target"]["seeds"].items():
        L.append(f"  - seed {s}: B1 {v['b1']} → 점 {v['point']} (차 {v['delta']})")
    L.append(f"- 이동·추종({r['motion_tracking']['case']}): {r['motion_tracking']['label']}, 나빠진 seed {r['motion_tracking']['worse_seeds']}, 과속 seed {r['motion_tracking']['overspeed_seeds']}")
    for p in r["protection"]:
        vals = ", ".join(f"{s}: {v['b1']}→{v['point']}" for s, v in p["seeds"].items())
        L.append(f"- 보호 {p['item']}: {p['label']} (나빠진 seed {p['worse_seeds']}; {vals})")
        for sd, v in p["seeds"].items():
            if "post_reach" in v:
                L.append(f"  - seed {sd} ≥2단 도달 뒤: B1 {v['post_reach']['b1']} / 점 {v['post_reach']['point']}")
    c = r["combined"]
    L += ["", f"**조합 분류: {c['class']}** — {c['meaning']}", f"- 결측 부분: {c['missing_parts']}",
          f"- 세 seed 공통 손실 항목: {c['common_loss_items']}",
          f"- 일부 seed 손실 항목: {c['partial_loss_items']}", f"- 다음 점: {c['next_point']}"]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    import build_go2_pc2_point_package as pkg  # noqa: E402
    points = {k: (v, x) for k, v, x, _ in pkg.POINTS}
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key", required=True, choices=sorted(points))
    ap.add_argument("--point", required=True, type=Path)
    ap.add_argument("--base", type=Path, help="PC2 B1 harvest (점 판독에 필수, B1 자체 판독에는 생략)")
    ap.add_argument("--out", type=Path, default=QUAD / "reports/evidence/go2_pc2_point_readout")
    args = ap.parse_args(argv)
    var, val = points[args.key]
    if var is not None and args.base is None:
        ap.error("한 항 변경 점은 --base(PC2 B1) 가 필요하다")
    r = read(args.key, args.point, args.base, None if var is None else (var, val))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.key}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (args.out / f"{args.key}.md").write_text(to_md(r), encoding="utf-8")
    print(f"{args.key}: state={r['state']['overall']} gate={r['moving_gate']} target={r['target']['class']} "
          f"combined={r['combined']['class']} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
