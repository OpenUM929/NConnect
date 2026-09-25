"""Go2 튜닝 기반 데이터 — 튜닝값은 이 표에서 도출한다.

왜 있는가.  2026-09-16 G-A037(`lin_vel_z_l2 -2.0 → -1.0`)은 보상 산수로 값을 정했고,
회차 표를 대 보지 않았다.  표를 대 보니 그 값은 걷는 회차에서 관측된 적이 없는 범위였고,
근거로 쓴 원리(오르기 벌점 몫이 크면 15cm를 못 오른다)는 Pilot 대 A033에서 반대로 나왔다.
사용자 지시: "데이터를 기반으로 특이점을 찾고 이를 기반으로 튜닝 값을 잡는다".

이 도구는 증거 CSV(`reports/evidence/go2_stairs_behavior_20260916/`, 생성기
`tools/go2_stairs_behavior.py`)만 읽어 기반 데이터 문서를 만들고, 새 튜닝 사양이 그 데이터의
어디에 있는지(관측 안/사이/밖)를 계산한다.  문서의 표 숫자는 CSV 칸을 글자 그대로 옮긴다.

산출: workspace/training/quadruped/reports/GO2_TUNING_BASE_DATA.md
사용: python tools/go2_tuning_base_data.py          (문서 재생성)
      python tools/go2_tuning_base_data.py --check  (문서가 CSV와 같은지만 검사)
"""
from __future__ import annotations

import ast
import collections
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
EVIDENCE = QUAD / "reports/evidence/go2_stairs_behavior_20260916"
DOC = QUAD / "reports/GO2_TUNING_BASE_DATA.md"
DOC_REL = "workspace/training/quadruped/reports/GO2_TUNING_BASE_DATA.md"
EXPERIMENTS = QUAD / "config/experiments"
SOURCES = ("WEIGHT_OUTCOME.csv", "LATERAL_BEHAVIOR.csv", "CLIMB_REWARD.csv", "TRAINING_TERMS.csv",
           "CASE_BEHAVIOR.csv", "STAIRS_CLIMB.csv")

TERMS = ("track_lin_vel_xy_exp", "lin_vel_z_l2", "ang_vel_xy_l2", "action_rate_l2",
         "feet_air_time", "flat_orientation_l2")
SHORT = {"track_lin_vel_xy_exp": "track", "lin_vel_z_l2": "lin_vel_z", "ang_vel_xy_l2": "ang_vel_xy",
         "action_rate_l2": "action_rate", "feet_air_time": "feet_air", "flat_orientation_l2": "flat_orient"}

# 걷는 회차 = 험지 전진 속도가 이 값 이상.  표에서 걷는 회차(0.242 이상)와 멈춘 회차(0.110 이하)
# 사이가 비어 있어 경계를 어디에 둬도 분류가 같다.
WALK_SPEED = 0.2

# 가중치 표 회차 → 옆걸음 표 (run, arm).  옆걸음을 잰 회차만 있다.
LATERAL_OF = {
    "Default-01": ("go2_default_vs_pilot_v1", "default"),
    "feet_air_time_020_v1": ("go2_feet_air_time_020_v1", "candidate"),
    "chain01": ("go2_chain01_baseline", "chain01"),
    "Pilot-01": ("go2_a017_full_suite", "pilot"),
    "A017": ("go2_a017_full_suite", "a017"),
    "G-A033": ("go2_g_a033_a017_track_lin_vel_xy_150", "candidate"),
}
# 가중치 표 회차 → 오르기 보상 표 arm.
CLIMB_OF = {"Pilot-01": ("go2_a017_full_suite", "pilot"), "A017": ("go2_a017_full_suite", "a017"),
            "G-A033": ("go2_g_a033_a017_track_lin_vel_xy_150", "candidate")}

# 가중치 표 회차 → 학습 로그(TRAINING_TERMS.csv) run.  Pilot-01 = G-A001 원본 회수본(tfevents).  Default-01 로그는 69case 쌍 회차 안에 있다.
TRAIN_OF = {
    "Pilot-01": "train_260831-Go2_5var_1000", "Default-01": "go2_default_vs_pilot_v1",
    "feet_air_time_020_v1": "go2_feet_air_time_020_v1", "track_120_v1": "go2_track_lin_vel_120_v1",
    "A022": "go2_g_a022_chain01_feet_air_time_020", "A015": "go2_g_a015_pilot_feet_air_time_035",
    "A016": "go2_g_a016_pilot_ang_vel_xy_m015", "A018": "go2_g_a018_pilot_action_rate_m008",
    "A017": "go2_g_a017_pilot_track_lin_vel_xy_140", "A031": "go2_g_a031_a017_feet_air_time_001",
    "A032": "go2_g_a032_a017_feet_air_time_010", "G-A033": "go2_g_a033_a017_track_lin_vel_xy_150",
}
# 가중치 표 회차 → 계단 평가 기록(CASE_BEHAVIOR.csv) (run, arm).
STAIRS_OF = {
    "Default-01": ("go2_default_vs_pilot_v1", "default"),
    "feet_air_time_020_v1": ("go2_feet_air_time_020_v1", "candidate"),
    "chain01": ("go2_chain01_baseline", "chain01"),
    "A022": ("go2_g_a022_chain01_feet_air_time_020", "candidate"),
    "Pilot-01": ("go2_a017_full_suite", "pilot"),
    "A015": ("go2_g_a015_pilot_feet_air_time_035", "candidate"),
    "A017": ("go2_a017_full_suite", "a017"),
    "A031": ("go2_basic_motion_pair_a031_a032", "a031"),
    "A032": ("go2_basic_motion_pair_a031_a032", "a032"),
    "G-A033": ("go2_g_a033_a017_track_lin_vel_xy_150", "candidate"),
}
TRACK_ANG = 0.75   # track_ang_vel_z_exp — 18회차 env.yaml 전부 같은 값(MASTER §1-b 표 84행)

MASTER = ROOT / "GO2_REWARD_EVIDENCE_MASTER.md"
MASTER_A017_CKPT = "대상 model_900.pt, reward-best step856"
MASTER_A032_ITER = "G-A032는 체크포인트 iter 700으로 평가돼"


def master_line(needle: str) -> int:
    """MASTER 인용 줄 번호 — 문서가 늘어도 인용이 어긋나지 않게 내용으로 찾는다."""
    lines = MASTER.read_text(encoding="utf-8").splitlines()
    return next(i for i, line in enumerate(lines, 1) if needle in line)


# 단일 변경 쌍을 대조할 회차의 학습 env.yaml(_keep) — 차이가 한 줄뿐인지 매번 다시 대조한다.
RUN_ENV = {
    "Default-01": "go2_default_vs_pilot_v1/training/env.yaml",
    "feet_air_time_020_v1": "go2_feet_air_time_020_v1/training/env.yaml",
    "chain01": "go2_chain01_baseline/policy/chain01_env.yaml",
    "Pilot-01": "go2_a017_full_suite/policy/pilot_env.yaml",
    "A017": "go2_g_a017_pilot_track_lin_vel_xy_140/training/env.yaml",
    "G-A033": "go2_g_a033_a017_track_lin_vel_xy_150/training/env.yaml",
}
# 평가 체크포인트 — 산출물 이름에 반복 수가 없어 기록에서 옮긴다(출처 병기).
RUN_CKPT = {
    "Default-01": ("800", "`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 294행: Default-01 iter 800, SHA `99ceeaa1…`"),
    "feet_air_time_020_v1": ("800", "`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 295행: step 829 → `model_800`, SHA `0dc8815f…`"),
    "chain01": ("900", "`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 297행: step 900 → `model_900`, SHA `143871e3…`"),
    "Pilot-01": ("999", "`GO2_OPUS_REAUDIT_INDEPENDENT_260907.md` 294행: best iter 972 → `model_999`, SHA `c4d78adf…`"),
    "A017": ("900", f"`GO2_REWARD_EVIDENCE_MASTER.md` {master_line(MASTER_A017_CKPT)}행: `model_900.pt`, SHA `0563deff…`"),
    "G-A033": ("900", "`_keep/go2_g_a033_a017_track_lin_vel_xy_150/training/CHECKPOINT_PIN.txt` `EVAL_CHECKPOINT_ITER`"),
}
# 학습 agent.yaml(학습기가 쓴 params) — 세 회차가 같은지 매번 대조한다.
AGENT_YAML = {
    "Pilot-01": "train_260831-Go2_5var_1000/train_260831-Go2_5var_1000_DOWNLOAD/quadruped/logs/rsl_rl/quadruped/2026-08-31_15-42-43/params/agent.yaml",
    "A017": "go2_g_a017_pilot_track_lin_vel_xy_140/training/logs/rsl_rl/quadruped/2026-09-04_22-24-51/params/agent.yaml",
    "G-A033": "go2_g_a033_a017_track_lin_vel_xy_150/training/logs/rsl_rl/quadruped/2026-09-15_21-29-57/params/agent.yaml",
}
# 평가 case 이름과 실제 동작 — 계단 case 이름의 up/down은 실제와 반대다(`GO2_NOW.md` 정정 2026-09-15).
CASE_LABEL = {
    "forward_nominal": "평지 전진", "rough_forward": "험지 전진", "rough_lateral": "험지 옆걸음",
    "slope_plus_20": "오르막 20°", "slope_minus_20": "내리막 20°",
    "stairs_10_down": "10cm 계단 오르기", "stairs_15_down": "15cm 계단 오르기",
    "stairs_10_up": "10cm 계단 내려가기", "stairs_15_up": "15cm 계단 내려가기",
}

# 산출물에서 읽을 수 없는 사실 — 출처를 함께 적는다.
FEET_AIR_NOTES = (
    "A032는 체크포인트 iter 700으로 평가됐고 A017은 iter 900이다. 두 행은 같은 시점 비교가 아니다"
    f" (`GO2_REWARD_EVIDENCE_MASTER.md` {master_line(MASTER_A032_ITER)}행).",
    "A031·A032 결과 묶음(`_keep/go2_basic_motion_pair_a031_a032`)의 계단 기록은 내려가기 case 영상 1개뿐이고 원격 측정이 없다.",
    "평가 기록에 발 위치·발 높이·접지 열이 없다(`steps.csv` 접촉 열은 몸통 접촉 `term_base_contact` 하나). 발이 계단 모서리에 걸리는지는 기록으로 볼 수 없다.",
    "생존 proxy는 계측 세대가 다르다. Default-01·`feet_air_time_020_v1`은 낙상을 세지 않던 계측이라 멈춰 있어도 `1.000`이고,"
    " chain01·A022는 낙상 검출 계측이라 몸을 낮춘 정지가 `0.000`이다. 두 세대의 생존 값을 서로 비교하지 않는다 (`GO2_NOW.md` §0 [확보]).",
    "IL v2.3.1 `feet_air_time` 식은 `Σ(체공 시간 − 0.5 s) × 첫 접지`이고 명령 속도가 작으면 0이다. 발 높이가 아니라 **체공 시간**을 본다.",
)

# 이 규칙이 생기기 전에 만든 사양.  기반 데이터 대조 기록은 이 문서 §7에 남긴다.
PRE_RULE_SPECS = {"G-A037"}
# 실행된 보상 사양의 결과 (§7).  수치는 각 판독 문서에 있고 여기에는 동작만 적는다.
SPEC_OUTCOME = {
    "G-A038": "실행(판정 없음, `reports/GO2_G_A038_READOUT.md`): 험지 옆걸음 종료 감소, 10cm 오르기 붕괴 — 승급 후보 아님",
}

# ─────────────────────────────────────────────────────────────────────────────
# 보상 항의 역할 — Isaac Lab v2.3.1 원문 (2026-09-17 사용자 지시: "기준 문서의 변수 역할 설명 없이
# 우리 결과로만 판단하지 마라").  원문 파일은 증거 폴더에 SHA와 함께 보관하고, 식은 그 파일에서 뽑는다.
# ─────────────────────────────────────────────────────────────────────────────
ROLES = QUAD / "reports/evidence/go2_reward_term_roles_20260917"
ROLE_ENV = "go2_g_a033_a017_track_lin_vel_xy_150/training/env.yaml"   # 현재 기준선 학습 env
ROLE_TRAIN_RUN = "go2_g_a033_a017_track_lin_vel_xy_150"
# env.yaml 항 이름 → env.yaml `func:` 값.  원문 파일은 func 모듈 경로로 고른다.
ROLE_FILES = {
    "isaaclab.envs.mdp.rewards": "isaaclab_envs_mdp_rewards.py",
    "isaaclab_tasks.manager_based.locomotion.velocity.mdp.rewards": "isaaclab_tasks_locomotion_velocity_mdp_rewards.py",
    "isaaclab.envs.mdp.terminations": "isaaclab_envs_mdp_terminations.py",
}
ROLE_TERMS = ("track_lin_vel_xy_exp", "track_ang_vel_z_exp", "lin_vel_z_l2", "ang_vel_xy_l2",
              "dof_torques_l2", "dof_acc_l2", "action_rate_l2", "feet_air_time", "flat_orientation_l2",
              "dof_pos_limits")
# 원문 식을 우리말로 옮긴 것(풀이) — 식에 없는 말은 넣지 않는다.  "영향 축"은 물리적으로 걸리는 평가 영역이다.
ROLE_READING = {
    "track_lin_vel_xy_exp": ("몸통 좌표의 앞뒤·좌우 속도가 명령과 가까울수록 커지는 보상(최대 1). 오차²/std²의 지수 감소",
                             "전 영역(G1~G7 추종)"),
    "track_ang_vel_z_exp": ("몸통 좌표의 회전(yaw) 속도가 명령과 가까울수록 커지는 보상(최대 1)", "G2 회전·전 영역 방향 유지"),
    "lin_vel_z_l2": ("몸통 좌표의 위아래 속도² 벌점 — 튀기·떨어지기·**올라서기** 모두 같은 벌점", "G5 계단·G4 경사·G3 험지"),
    "ang_vel_xy_l2": ("몸통의 좌우 구르기(roll)·앞뒤 끄덕임(pitch) **속도²** 벌점 — 기울어진 자세 자체가 아니라 기우는 빠르기",
                      "G3 옆 뒤집힘·G6 밀침·G5 턱 넘기"),
    "dof_torques_l2": ("관절 토크² 합 벌점 — 힘을 덜 쓰게 한다", "G5 오르기(큰 토크 필요)"),
    "dof_acc_l2": ("관절 가속도² 합 벌점 — 관절 움직임을 부드럽게 한다", "G5·G6 빠른 발 동작"),
    "action_rate_l2": ("이번 행동과 직전 행동의 차이² 합 벌점 — 행동을 매끄럽게 한다", "G6 밀침 대응·G5 발 올리기"),
    "feet_air_time": ("발이 땅에 닿는 순간 `(체공 시간 − threshold)`를 더한다. 명령 속도가 `0.1` 이하면 0. "
                      "체공이 threshold보다 짧으면 **음수(짧은 걸음 벌점)**", "걸음 형태 → G5 발 올리기·G4"),
    "flat_orientation_l2": ("몸통 좌표에서 본 중력 방향의 xy 성분² 벌점 — **기울어진 자세 자체**(roll·pitch 각)", "G3 옆 뒤집힘 · 단 G4 경사·G5 계단에서도 상시 부과"),
    "dof_pos_limits": ("관절 각도가 soft limit 밖으로 나간 양의 합 벌점", "관절 한계 근처 동작"),
}


def read(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def weights() -> list[dict[str, str]]:
    return read("WEIGHT_OUTCOME.csv")


def walking(row: dict[str, str]) -> bool:
    # 2026-09-22: 1단계만 잰 회차(A038)는 `rough_forward` 를 재지 않아 칸이 비어 있다.  빈 칸은
    # "걷지 않았다" 가 아니라 **미측정**이다 — 걷는 관측값 집합에서 빼되 멈춘 회차로도 세지
    # 않는다.  예전에는 이 칸이 항상 차 있었고, 표가 G-A033 에서 멈춰 있어 드러나지 않았다.
    speed = (row.get("rough_forward_speed") or "").strip()
    return bool(speed) and float(speed) >= WALK_SPEED


def lateral(run: str, arm: str, case: str = "rough_lateral") -> dict[str, str]:
    return next(r for r in read("LATERAL_BEHAVIOR.csv") if (r["run"], r["arm"], r["case"]) == (run, arm, case))


def climb(run: str, arm: str, case: str, group: str) -> dict[str, str] | None:
    return next((r for r in read("CLIMB_REWARD.csv")
                 if (r["run"], r["arm"], r["case"], r["group"]) == (run, arm, case, group)), None)


# ─────────────────────────────────────────────────────────────────────────────
# 관측 범위 — 새 값이 데이터의 어디에 있는가
# ─────────────────────────────────────────────────────────────────────────────
def walking_values(term: str) -> list[float]:
    rows = weights()
    if rows and term not in rows[0]:
        # 배포 `REWARD_WEIGHTS` 6개 목록 밖의 항은 §1 표에 칸이 없다.  회차별 실제 가중치는 학습 로그에서
        # 읽은 기전 증거 TERM_VALUES.csv 에 있다(2026-09-18).
        import go2_reward_mechanism as mechanism  # 순환 import 방지 — 이 분기에서만 쓴다
        return sorted({float(r["weight"]) for r in mechanism.read("TERM_VALUES.csv")
                       if r["term"] == term and r["walking"] == "True"})
    return sorted({float(r[term]) for r in rows if walking(r)})


def range_status(term: str, value: float) -> str:
    seen = walking_values(term)
    if value in seen:
        return "OBSERVED"
    if seen and min(seen) < value < max(seen):
        return "BETWEEN_OBSERVED"
    return "OUT_OF_RANGE"


def spec_changes(spec: dict) -> dict[str, float]:
    rewards = spec.get("rewards") or {}
    base, cand = rewards.get("baseline") or {}, rewards.get("candidate") or {}
    changed = {k: float(v) for k, v in cand.items() if k in base and float(base[k]) != float(v)}
    # 2026-09-18: 배포 `REWARD_WEIGHTS` 6개 목록 밖의 env 보상 항(change_class `env_reward_weight`)은
    # 기준선 표에 없고 후보에만 적힌다.  대조를 건너뛰지 않도록 여기서 함께 센다.
    changed.update({k: float(v) for k, v in (rewards.get("candidate_env_extra") or {}).items() if k not in base})
    return changed


def expected_base_data(spec: dict) -> dict:
    """`role`은 바꾸는 항의 Isaac Lab 원문 설명(§0-1) — 역할을 읽지 않고 값을 정하지 못하게 한다."""
    import go2_reward_mechanism as mechanism   # 순환 import 방지 — 이 함수에서만 쓴다
    roles = {r["term"]: f"{r['doc']} [{r['file']}:{r['line']}]" for r in role_rows()}
    return {"source": DOC_REL, "terms": {
        term: {"value": value, "walking_values": walking_values(term), "status": range_status(term, value),
               "role": roles.get(term, "")}
        for term, value in sorted(spec_changes(spec).items())},
        # 네 구간 예측(GO2_REWARD_MECHANISM_FORECAST.md §6-0·§8-2) — 걷기 구간이 아니거나 계단·흔들림·밀침이 나빠지면 이유 필수
        "walk_margin": mechanism.spec_margin({**((spec.get("rewards") or {}).get("candidate") or {}),
                                              **((spec.get("rewards") or {}).get("candidate_env_extra") or {})})}


# 발행되어 **실행된** 사양.  사양 JSON 은 발행 ZIP 안에 그대로 들어가므로(빌더가 재빌드 바이트를
# 대조한다) 나중에 고칠 수 없다 — 그런데 그 회차의 결과가 기반 데이터 표에 들어오면 자기 값의 관측
# 위치가 `OUT_OF_RANGE` → `OBSERVED` 로 바뀐다.  `base_data` 는 **발행 시점의 스냅샷**이라는 뜻이다.
# 그래서 이 목록의 사양은 '자기 항의 관측 위치' 한 가지만 어긋나는 것을 허용하고, 역할·값·다른 항·
# margin 은 그대로 검사한다.  미실행 사양은 여기에 들어갈 수 없다 — 들어가려면 사람이 이 줄을 고쳐야
# 하고, 그 순간 검토에 걸린다.  (2026-09-22, 결함 C-12)
EXECUTED_SPECS = {"G-A043"}
# 관측 위치만 움직였는가.  값·역할이 다르면 스냅샷 예외를 주지 않는다.
_RANGE_KEYS = ("walking_values", "status")


def _only_own_range_shift(got: dict, want: dict) -> bool:
    same = all(got.get(k) == want[k] for k in want if k not in _RANGE_KEYS)
    moved = any(got.get(k) != want[k] for k in _RANGE_KEYS)
    return same and moved


def spec_problems(spec: dict) -> list[str]:
    """새 reward 사양은 `base_data`에 기반 데이터 대조를 적어야 하고, 적힌 값은 계산과 같아야 한다.
    관측 밖 값은 `out_of_range_reason`에 이유를 적어야 한다(금지가 아니라 표시 의무)."""
    if not spec_changes(spec):
        return []
    declared = spec.get("base_data")
    if not isinstance(declared, dict):
        return ["base_data 없음"]
    problems = []
    expected = expected_base_data(spec)
    if declared.get("source") != expected["source"]:
        problems.append("base_data.source")
    published = spec.get("work_id") in EXECUTED_SPECS
    for term, want in expected["terms"].items():
        got = (declared.get("terms") or {}).get(term)
        if published and isinstance(got, dict) and _only_own_range_shift(got, want):
            # 이 회차가 표에 들어오면서 자기 값의 관측 위치가 바뀐 것뿐이다 — 아래 EXECUTED_SPECS 참고.
            continue
        if not isinstance(got, dict) or any(got.get(k) != want[k] for k in want):
            problems.append(f"base_data.terms.{term} != {want}")
        elif want["status"] == "OUT_OF_RANGE" and len(str(got.get("out_of_range_reason", "")).strip()) < 20:
            problems.append(f"base_data.terms.{term}.out_of_range_reason")
    margin = declared.get("walk_margin")
    want_margin = expected["walk_margin"]
    if not isinstance(margin, dict) or any(margin.get(k) != want_margin[k] for k in want_margin):
        problems.append(f"base_data.walk_margin != {want_margin}")
    elif (want_margin["zone"] != "WALK" or want_margin["worse"]) and len(str(margin.get("reason", "")).strip()) < 20:
        problems.append("base_data.walk_margin.reason")
    return problems


def reward_specs() -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(EXPERIMENTS.glob("G_A*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        if spec.get("change_class") == "reward_weight":
            out.append((path, spec))
    return out


def role_sources() -> list[dict[str, str]]:
    with (ROLES / "SOURCES.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def env_terms(rel: str = ROLE_ENV) -> dict[str, dict[str, str]]:
    """학습 env.yaml의 rewards/terminations 블록에서 항별 func·weight·std·threshold·body_names."""
    lines = (ROOT / "workspace/_keep" / rel).read_text(encoding="utf-8").splitlines()
    out: dict[str, dict[str, str]] = {}
    section, name = None, None
    for line in lines:
        top = re.match(r"^(\w+):", line)
        if top:
            section, name = top.group(1), None
            continue
        if section not in ("rewards", "terminations"):
            continue
        head = re.match(r"^  (\w+):\s*(.*)$", line)
        if head:
            name = f"{section}.{head.group(1)}"
            out[name] = {"null": "true"} if head.group(2) == "null" else {}
            continue
        field = re.match(r"^\s+(func|weight|std|threshold|body_names): (.*)$", line)
        if name and field and field.group(1) not in out[name]:
            out[name][field.group(1)] = field.group(2).strip()
    return out


def il_function(func: str) -> dict[str, str]:
    """`모듈:함수` → 원문 파일의 docstring 첫 문단과 계산 줄(주석·타입 힌트용 대입 제외)."""
    module, fname = func.split(":")
    path = ROLES / ROLE_FILES[module]
    text = path.read_text(encoding="utf-8")
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == fname)
    doc = (ast.get_docstring(node) or "").split("\n\n")[0].replace("\n", " ")
    body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant))]
    steps = []
    for stmt in body:
        if isinstance(stmt, ast.AnnAssign) or (isinstance(stmt, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in ("asset", "contact_sensor") for t in stmt.targets)):
            continue
        steps.append(" ".join(ast.get_source_segment(text, stmt).split()))
    return {"file": path.name, "line": str(node.lineno), "doc": doc, "code": " ; ".join(steps)}


def role_rows() -> list[dict[str, str]]:
    env = env_terms()
    train = next(r for r in read("TRAINING_TERMS.csv") if r["run"] == ROLE_TRAIN_RUN)
    rows = []
    for term in ROLE_TERMS:
        cfg = env[f"rewards.{term}"]
        fn = il_function(cfg["func"])
        logged = train.get(term, "")
        weight = float(cfg["weight"])
        raw = f"{float(logged) / weight:.3f}" if logged and weight else ""
        rows.append({"term": term, "func": cfg["func"], "weight": cfg["weight"], "std": cfg.get("std", ""),
                     "threshold": cfg.get("threshold", ""), "logged": logged, "raw": raw,
                     "reading": ROLE_READING[term][0], "axes": ROLE_READING[term][1], **fn})
    return rows


def influence_grades() -> dict[str, str]:
    """변수 영향 문서(PAIRS.csv)의 항별 쌍 등급 — `A 2 · C 1` 꼴."""
    import go2_variable_influence as vi
    grades: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for pair in vi.read("PAIRS.csv"):
        grades[pair["term"]][vi.validity(pair)] += 1
    return {t: " · ".join(f"{g} {c[g]}" for g in "ABCDE" if c[g]) for t, c in grades.items()}


def stall_track_reward(speed: float, std: float) -> float:
    """제자리에 선 로봇이 명령 속도 speed에서 받는 추종 보상(가중치 곱 전) = exp(−speed²/std²)."""
    return math.exp(-speed ** 2 / std ** 2)


# ─────────────────────────────────────────────────────────────────────────────
# 특이점 — 전부 표에서 계산한다
# ─────────────────────────────────────────────────────────────────────────────
def vertical_share(run: str, arm: str) -> tuple[float, str] | None:
    """10cm 오른 로봇의 수직 벌점 증가 / 추종 보상 증가 (15cm 정지 대비)."""
    up, stall = climb(run, arm, "stairs_10_down", "climb"), climb(run, arm, "stairs_15_down", "stall")
    if not up or not stall:
        return None
    gain = float(up["track_rate"]) - float(stall["track_rate"])
    cost = float(stall["lin_vel_z_rate"]) - float(up["lin_vel_z_rate"])
    return cost / gain, up["robots"]


WEIGHT_COLUMNS = ("track_lin_vel_xy_exp", "lin_vel_z_l2", "ang_vel_xy_l2", "action_rate_l2",
                  "feet_air_time", "flat_orientation_l2")


def one_dial_line(rows: dict[str, dict[str, str]], walk: list[dict[str, str]],
                  term: str, reference: str) -> list[dict[str, str]]:
    """기준 회차와 `term` 하나만 다른 걷는 회차들, 그 항의 오름차순."""
    ref = rows[reference]
    others = [t for t in WEIGHT_COLUMNS if t != term]
    return sorted((r for r in walk if all(r[t] == ref[t] for t in others)), key=lambda r: float(r[term]))


def singularities() -> dict:
    rows = {r["name"]: r for r in weights()}
    walk = [r for r in rows.values() if walking(r)]
    pair = {(r["lin_vel_z_l2"], r["ang_vel_xy_l2"]) for r in walk}
    # 2026-09-22: 이 쌍은 2026-09-16 에 **하나**였고 코드가 `next(iter(pair))` 로 그 하나를 꺼냈다.
    # A043 이 `lin_vel_z -1.5` 로 걸으면서 쌍이 둘이 됐다 — 집합에서 아무거나 꺼내면 문장이 회차마다
    # 달라진다.  기준은 동결 기준선 G-A033 의 쌍으로 고정하고, 그 쌍이 아닌 걷는 회차는 **반례**로
    # 따로 센다.  "이 쌍이 아니면 멈춘다" 는 옛 읽기가 반증된 사실이 S1 에 그대로 드러나야 한다.
    reference_pair = (rows["G-A033"]["lin_vel_z_l2"], rows["G-A033"]["ang_vel_xy_l2"])
    walk_other_pair = [r for r in walk if (r["lin_vel_z_l2"], r["ang_vel_xy_l2"]) != reference_pair]
    same_pair_stalled = [r for r in rows.values() if not walking(r)
                         and (r["lin_vel_z_l2"], r["ang_vel_xy_l2"]) in pair]
    one_only = [r for r in rows.values() if not walking(r)
                and ((r["lin_vel_z_l2"], r["ang_vel_xy_l2"]) != reference_pair)
                and (r["lin_vel_z_l2"] == reference_pair[0] or r["ang_vel_xy_l2"] == reference_pair[1])]
    # 2026-09-22: 두 줄은 **한 항만 다른** 회차의 나열이라야 그 항의 기울기를 말할 수 있다.  예전 필터는
    # `feet_air_time == 0.2` 하나였고, 표가 G-A033 에서 멈춰 있는 동안에는 그것으로 충분했다.  A041
    # (`ang_vel_xy_l2 -0.04`)·A043(`lin_vel_z_l2 -1.5`)이 표에 들어오면서 같은 track 값에 다른 항이
    # 섞이므로, 기준 회차와 나머지 다섯 항이 모두 같은 행만 남긴다.  A042(track 1.6)는 이 조건을
    # 만족해 track 줄을 실제로 연장한다.
    track_line = one_dial_line(rows, walk, "track_lin_vel_xy_exp", "G-A033")
    fat_line = one_dial_line(rows, walk, "feet_air_time", "A017")
    # 1단계만 잰 회차는 15cm 칸이 비어 있다(미측정).  없는 값을 0 으로 세지 않는다.
    climb15 = [int(r["climb15_ge1"]) for r in track_line if (r["climb15_ge1"] or "").strip()]
    shares = {r["name"]: vertical_share(*CLIMB_OF[r["name"]]) for r in track_line if r["name"] in CLIMB_OF}
    ordered = sorted((n for n in shares if shares[n]), key=lambda n: shares[n][0])
    by_share_climb = [int(rows[n]["climb15_ge1"]) for n in ordered]
    return {
        "walk": walk, "pair": pair, "reference_pair": reference_pair,
        "walk_other_pair": walk_other_pair,
        "same_pair_stalled": same_pair_stalled, "one_only": one_only,
        "track_line": track_line, "fat_line": fat_line,
        "climb15_monotone_in_track": climb15 == sorted(climb15) or climb15 == sorted(climb15, reverse=True),
        "shares": shares,
        # 수직 벌점 몫이 작을수록 15cm를 더 오른다면 몫 오름차순에서 오름 수는 내림차순이어야 한다.
        "share_explains_climb15": by_share_climb == sorted(by_share_climb, reverse=True),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 문서
# ─────────────────────────────────────────────────────────────────────────────
def env_differences(a: str, b: str) -> list[str]:
    """두 env.yaml에서 log_dir 외에 달라진 줄(b 쪽)."""
    keep = ROOT / "workspace/_keep"
    left = (keep / RUN_ENV[a]).read_text(encoding="utf-8").splitlines()
    right = (keep / RUN_ENV[b]).read_text(encoding="utf-8").splitlines()
    if len(left) != len(right):
        return [f"줄 수 {len(left)} != {len(right)}"]
    return [f"{i + 1}: {x.strip()} → {y.strip()}" for i, (x, y) in enumerate(zip(left, right))
            if x != y and not x.startswith("log_dir:")]


# 옆걸음 기록이 있는 회차 사이의 한 항 변경 쌍 (앞 → 뒤).
LATERAL_PAIRS = (("Default-01", "feet_air_time_020_v1"), ("Default-01", "chain01"),
                 ("Pilot-01", "A017"), ("A017", "G-A033"))


def lateral_pairs() -> list[dict]:
    """옆걸음 한 항 변경 쌍: 바뀐 가중치, env.yaml 차이, 체크포인트 같음 여부, seed별 종료 수."""
    by_name = {r["name"]: r for r in weights()}
    cases = read("CASE_BEHAVIOR.csv")

    def seeds(name: str) -> list[str]:
        return [c["terminated_env_count"] for c in sorted(
            (c for c in cases if (c["run"], c["arm"]) == LATERAL_OF[name] and c["case"] == "rough_lateral"),
            key=lambda c: c["seed"])]

    out = []
    for a, b in LATERAL_PAIRS:
        changed = [t for t in TERMS if float(by_name[a][t]) != float(by_name[b][t])]
        la, lb = lateral(*LATERAL_OF[a]), lateral(*LATERAL_OF[b])
        out.append({"a": a, "b": b, "changed": changed, "diff": env_differences(a, b),
                    "same_ckpt": RUN_CKPT[a][0] == RUN_CKPT[b][0], "walking": walking(by_name[a]) and walking(by_name[b]),
                    "seeds": (seeds(a), seeds(b)), "lat": (la, lb)})
    return out


# 옆걸음 기록이 없는 가중치 변경 — 옆 넘어짐과 물리적으로 가까운 항인데 옆걸음을 재지 않았다.
LATERAL_UNMEASURED = (
    ("ang_vel_xy_l2", "A016(`-0.15`, Pilot 위)·A021(`-0.05`, chain01 위)·A024(`-0.15`, Default 위) — 셋 다 7 case 평가라 험지 옆걸음 기록이 없다"),
    ("flat_orientation_l2", "A013(`-1`, Default 위) 하나, 7 case 평가라 옆걸음 기록이 없다. 걷는 회차는 전부 `0`"),
    ("lin_vel_z_l2 · action_rate_l2", "A010·A020·A018 모두 7 case 평가라 옆걸음 기록이 없다"),
)
# 위 회차들의 7 case에는 평지 `diagonal_left`가 있지만 후보가 멈춰 옆으로 가지 않았다(실제 vy가 이 값 미만).
UNMEASURED_DIAGONAL = {"A016": "go2_g_a016_pilot_ang_vel_xy_m015", "A021": "go2_g_a021_chain01_ang_vel_xy_m005",
                       "A024": "go2_g_a024_ang_vel_xy_m015", "A013": "go2_g_a013_flat_orientation_m1",
                       "A010": "go2_g_a010_lin_vel_z_m2", "A020": "go2_g_a020_chain01_lin_vel_z_m2",
                       "A018": "go2_g_a018_pilot_action_rate_m008"}
STOPPED_VY = 0.01


def diagonal_vy(run: str) -> float:
    path = ROOT / "workspace/_keep" / run / "evaluation/candidate/cases/seed_101/diagonal_left/steps.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        values = [float(r["actual_vy"]) for r in csv.DictReader(handle)]
    return sum(values) / len(values)


def track_pairs() -> dict:
    """track 선 세 회차의 case별 이동 거리(seed 3개 평균)와 쌍별 증감."""
    names = ("Pilot-01", "A017", "G-A033")
    cases = read("CASE_BEHAVIOR.csv")
    progress = {}
    for case in CASE_LABEL:
        values = []
        for n in names:
            v = [float(c["projected_progress_m"]) for c in cases
                 if (c["run"], c["arm"]) == STAIRS_OF[n] and c["case"] == case]
            values.append(sum(v) / len(v))
        progress[case] = values
    up = {pair: sum(1 for v in progress.values() if v[j] > v[i]) for pair, (i, j) in
          {"Pilot-01→A017": (0, 1), "A017→G-A033": (1, 2)}.items()}
    return {"names": names, "progress": progress, "up": up,
            "diff": {"Pilot-01→A017": env_differences("Pilot-01", "A017"),
                     "A017→G-A033": env_differences("A017", "G-A033")}}


def _w(row: dict[str, str], term: str) -> str:
    return row[term]


def render_roles() -> list[str]:
    rows = role_rows()
    by = {r["term"]: r for r in rows}
    env = env_terms()
    grades = influence_grades()
    climb_rows = {(r["group"], r["case"]): r for r in read("CLIMB_REWARD.csv")
                  if (r["run"], r["arm"]) == CLIMB_OF["G-A033"]}
    walk_train = {TRAIN_OF[n]: n for n in TRAIN_OF if any(w["name"] == n and walking(w) for w in weights())}
    train = [r for r in read("TRAINING_TERMS.csv") if r["run"] in walk_train]
    std = float(by["track_lin_vel_xy_exp"]["std"])
    penalties = sorted((r for r in rows if r["logged"] and float(r["logged"]) < 0), key=lambda r: float(r["logged"]))
    positive = sum(float(r["logged"]) for r in rows if r["logged"] and float(r["logged"]) > 0)
    stop = env["terminations.base_contact"]
    stop_fn = il_function(stop["func"])
    L = []
    add = L.append
    add("## 0-1. 보상 항의 역할 — Isaac Lab v2.3.1 원문 (2026-09-17 사용자 지시)")
    add("")
    add("> \"기준 문서에서 변수가 어떤 역할을 하는지 설명 없이 우리 결과로만 판단하지 마라.\" 각 항을 먼저 원문 식으로 읽고, 우리 결과는 그 역할과 맞는지 대조한다.")
    add(f"> 원문: `reports/evidence/{ROLES.name}/` (`SOURCES.csv`에 URL·SHA256). 식 칸은 그 파일의 함수 본문을 생성기가 그대로 뽑은 것이다(타입 힌트용 대입 제외).")
    add(f"> 가중치·파라미터는 현재 기준선 G-A033 학습 `env.yaml`(`_keep/{ROLE_ENV}`)에서 읽는다. 로그 칸은 `TRAINING_TERMS.csv` 마지막 10 iter 평균이다.")
    add("")
    add("| 항 | 원문 설명 | 원문 식 (파일:줄) | 풀이 | 걸리는 영역 [추정] | G-A033 가중치 | 로그(초당) | 로그÷가중치 | 우리 한 항 변경 쌍 등급 |")
    add("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        params = ", ".join(p for p in (f"std `{r['std']}`" if r["std"] else "", f"threshold `{r['threshold']}`" if r["threshold"] else "") if p)
        weight = f"`{r['weight']}`" + (f" ({params})" if params else "")
        add(f"| `{r['term']}` | {r['doc']} | `{r['code']}` ({r['file']}:{r['line']}) | {r['reading']} | {r['axes']} | {weight} "
            f"| `{r['logged'] or '—'}` | `{r['raw'] or '—'}` | {grades.get(r['term'], '**없음**')} |")
    add("")
    add("로그 기록 방식(원문 `isaaclab_managers_reward_manager.py`): 매 step `식 × 가중치 × dt`를 에피소드 동안 더하고, "
        "`Episode_Reward/항` = 그 합의 평균 ÷ `max_episode_length_s`다. 그래서 로그 칸은 **항끼리 같은 단위(초당 보상)**로 비교된다. "
        "로그가 소수 3자리라 로그÷가중치는 반올림 오차를 포함한다.")
    add("")
    add("**원문에서 바로 읽히는 사실**")
    add("")
    add(f"- **멈춰도 추종 보상이 남는다.** 제자리 로봇의 추종 항 = exp(−v²/std²), std `{by['track_lin_vel_xy_exp']['std']}`: "
        f"명령 `0.5` m/s면 `{stall_track_reward(0.5, std):.3f}`, `1.0` m/s면 `{stall_track_reward(1.0, std):.3f}`(가중치 곱 전). "
        f"그래서 G-A033 15cm 오르기 앞에서 멈춘 로봇도 추종 보상률 `{climb_rows[('stall', 'stairs_15_down')]['track_rate']}`(§3, 가중치 곱 후)를 받는다. "
        "평가 추종 proxy도 같은 std를 쓴다(registry `tracking_proxy_std`).")
    add(f"- **`lin_vel_z_l2`는 올라서는 동작 자체를 벌한다.** 식에 방향 구분이 없다. G-A033 10cm 오른 로봇의 수직 벌점률 "
        f"`{climb_rows[('climb', 'stairs_10_down')]['lin_vel_z_rate']}` 대 15cm 정지 로봇 `{climb_rows[('stall', 'stairs_15_down')]['lin_vel_z_rate']}`(§3). "
        "단 벌점 몫과 15cm 오르기는 회차 사이에서 맞지 않았다(§5 S5).")
    add("- **`ang_vel_xy_l2`와 `flat_orientation_l2`는 다른 것을 본다.** 앞은 기우는 **속도**, 뒤는 기운 **각도**다. "
        f"G-A033의 구르기·끄덕임 속도² 평균은 로그÷가중치 `{by['ang_vel_xy_l2']['raw']}` (rms 약 `{math.sqrt(float(by['ang_vel_xy_l2']['raw'])):.2f}` rad/s)이다. 20 s보다 일찍 끝난 에피소드도 20 s로 나누므로 실제보다 작게 잡힌 값이다.")
    add(f"- **`flat_orientation_l2`는 경사·계단에서도 벌점을 낸다.** 몸통이 20° 기울면 식 값은 sin²(20°) = `{math.sin(math.radians(20)) ** 2:.3f}`다. "
        "Isaac Lab은 이 항을 Go2 **평지** 설정에서만 `-2.5`로 켜고 험지 설정에서는 `0`으로 둔다(MASTER §1-b 표). 험지에서 끈 이유는 원문에 적혀 있지 않다 [모름].")
    add(f"- **`feet_air_time`은 threshold `{by['feet_air_time']['threshold']}` s보다 짧은 체공을 벌한다.** 걷는 회차 로그가 모두 음수다(§6-1). "
        "발 높이가 아니라 체공 시간을 본다.")
    add(f"- **G-A033에서 가장 큰 벌점 순서(로그):** " + " · ".join(f"`{r['term']}` `{r['logged']}`" for r in penalties)
        + f". 양수 항 합 `{positive:.3f}`. 가장 큰 벌점 `{penalties[0]['term']}`은 **한 번도 바꾼 적이 없다**.")
    never = [r["term"] for r in rows if r["term"] not in grades]
    add(f"- **한 항 변경 쌍이 하나도 없는 항:** " + ", ".join(f"`{t}`" for t in never)
        + ". 이 항들은 역할(원문)만 있고 우리 측정은 없다.")
    add(f"- **`undesired_contacts`**: Isaac Lab 기본은 허벅지 접촉 벌점(`-1.0`, 원문 `isaaclab_tasks_locomotion_velocity_env_cfg.py`)이고, "
        f"Go2 험지 설정이 `None`으로 지운다(원문 `isaaclab_tasks_go2_rough_env_cfg.py`). 우리 env도 `{'null' if env['rewards.undesired_contacts'].get('null') else '있음'}`이다.")
    add(f"- **종료 조건 `base_contact`**: {stop_fn['doc']} 식 `{stop_fn['code']}` ({stop_fn['file']}:{stop_fn['line']}). "
        f"우리 env는 몸통(`{stop['body_names']}`) 접촉력 > `{stop['threshold']}` N이면 끝난다 — G3 험지 옆걸음의 '종료'가 이것이다.")
    add("")
    add("걷는 회차 학습 로그의 항 범위(`TRAINING_TERMS.csv`, " + ", ".join(sorted(walk_train[r["run"]] for r in train)) + "):")
    add("")
    add("| 항 | 최소 | 최대 |")
    add("|---|---|---|")
    for term in ROLE_TERMS:
        values = [float(r[term]) for r in train if r.get(term)]
        if values:
            add(f"| `{term}` | `{min(values):.3f}` | `{max(values):.3f}` |")
    return L


def render() -> str:
    s = singularities()
    rows = weights()
    L = []
    add = L.append
    add("# Go2 튜닝 기반 데이터")
    add("")
    add("> **생성 문서 — 손으로 고치지 않는다.** `python tools/go2_tuning_base_data.py`가 증거 CSV에서 만든다.")
    add("> 원본: `reports/evidence/go2_stairs_behavior_20260916/` (`WEIGHT_OUTCOME.csv` · `LATERAL_BEHAVIOR.csv` · `CLIMB_REWARD.csv`, 생성기 `tools/go2_stairs_behavior.py`).")
    add("> 변수별 한 항 변경 쌍의 조건 대조·영향 표: `reports/GO2_VARIABLE_INFLUENCE.md`(생성기 `tools/go2_variable_influence.py`).")
    add("> 관문: `tools/test_go2_tuning_base_data_contract.py`. 분석 서술은 `reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md` §8·§9.")
    add("")
    add("## 0. 사용 규칙 (2026-09-16 사용자 지시)")
    add("")
    add("1. 튜닝값은 이 문서의 표와 특이점에서 도출한다. 보상 산수·항 크기·외부 기준값은 보조 근거이고 단독 근거가 아니다.")
    add("2. 튜닝을 제안하거나 판독할 때 답에 **해당 표의 행(원자료)을 먼저 보여주고**, 그 다음 특이점, 그 다음 값을 말한다.")
    add("3. 바꾸는 가중치마다 걷는 회차에서 관측된 값 대비 위치를 적는다: `OBSERVED` · `BETWEEN_OBSERVED` · `OUT_OF_RANGE`.")
    add("   새 reward 사양은 `base_data` 필드에 이 계산을 그대로 적고, `OUT_OF_RANGE`면 `out_of_range_reason`을 적는다(관문이 검사).")
    add("4. 도출 원리가 표의 다른 회차와 반대로 나오면 그 원리로 값을 정하지 않는다(§5 S5가 그 예).")
    add("5. 학습 seed는 전 회차 42 하나다. 회차 간 차이는 seed 운과 가를 수 없다 — 특이점은 **방향 후보**이지 인과가 아니다.")
    add("")
    add(f"걷는 회차 정의: `rough_forward_speed >= {WALK_SPEED}` (표의 걷는 회차와 멈춘 회차 사이가 비어 있어 경계 위치에 결과가 흔들리지 않는다).")
    add("")
    L.extend(render_roles())
    add("")
    add("## 1. 회차별 가중치와 결과 (`WEIGHT_OUTCOME.csv`)")
    add("")
    add("| 회차 | " + " | ".join(SHORT[t] for t in TERMS) + " | 험지 전진 속도 | 경사 전진 m | 10cm 2단 이상 | 15cm 1단 이상 | 걷기 |")
    add("|---|" + "---|" * len(TERMS) + "---|---|---|---|---|")
    for r in rows:
        add(f"| {r['name']} | " + " | ".join(_w(r, t) for t in TERMS)
            + f" | {r['rough_forward_speed']} | {r['slope_plus_20_progress_m']} | {r['climb10_ge2'] or '—'} | {r['climb15_ge1'] or '—'} | {'걷기' if walking(r) else '정지'} |")
    add("")
    add("빈칸(—)은 오르기를 재지 않은 회차다.")
    add("")
    add("## 2. 험지 옆걸음 (`LATERAL_BEHAVIOR.csv`, 로봇 96대)")
    add("")
    add("| 회차 | track | 종료 | 무거운 로봇 종료 | 가벼운 로봇 종료 | 질량 AUC | \\|wz\\| | 종료 전 기울기 cos "
        "| 처음 2초 \\|wz\\| AUC | 방향 이탈 rad (종료 / 생존) |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for name, (run, arm) in LATERAL_OF.items():
        lat, w = lateral(run, arm), next(r for r in rows if r["name"] == name)
        add(f"| {name} | {w['track_lin_vel_xy_exp']} | {lat['terminated']} | {lat['heavy_terminated']}/{lat['heavy_robots']} | "
            f"{lat['light_terminated']}/{lat['light_robots']} | {lat['mass_auc']} | {lat['abs_wz_mean']} | {lat['tilt_cos_min_median'] or '—'} | "
            f"{lat['early_abs_wz_auc']} | {lat['heading_drift_terminated_median_rad']} / {lat['heading_drift_survived_median_rad']} |")
    add("")
    add("무거운 로봇 = 몸통 질량 `>= 8.5 kg`, 가벼운 로봇 = `< 7 kg`. 기울기 cos가 음수면 뒤집힌 채 끝났다. 옛 로그는 기울기가 없다(—).")
    add("옆걸음 명령의 회전은 0이다(`steps.csv` `cmd_wz`). 그래서 \\|wz\\|는 회전 추종 오차이고, 방향 이탈은 끝날 때까지 누적 회전의 크기다."
        " AUC는 종료 로봇의 값이 생존 로봇보다 클 확률이다(`0.5` = 무관).")
    add("")
    add("| 회차 | case | 옆 명령 vy | 실제 vy | 종료 | 무거운 로봇 종료 | 가벼운 로봇 종료 | 질량 AUC | 처음 2초 vy AUC |")
    add("|---|---|---|---|---|---|---|---|---|")
    for name in ("Pilot-01", "A017", "G-A033"):
        run, arm = LATERAL_OF[name]
        for case in ("rough_lateral", "left", "right", "diagonal_left", "diagonal_right", "rough_forward"):
            lat = lateral(run, arm, case)
            add(f"| {name} | {case} | `{lat['cmd_vy']}` | {lat['vy_mean']} | {lat['terminated']} | {lat['heavy_terminated']}/{lat['heavy_robots']} | "
                f"{lat['light_terminated']}/{lat['light_robots']} | {lat['mass_auc'] or '—'} | {lat['early_vy_auc'] or '—'} |")
    add("")
    add("실제 vy = 종료 전 구간(처음 정착 구간 제외) 평균. 평지 옆걸음(left·right·diagonal)은 `0.30`~`0.35` 명령, 험지 옆걸음은 `0.30` 명령이다."
        " vy AUC는 종료 로봇이 명령 방향으로 더 빨리 움직였을 확률이다.")
    add("")
    add("### 2-1. 옆걸음 기록이 있는 한 항 변경 쌍 (종료 수는 `CASE_BEHAVIOR.csv` seed 101/202/303)")
    add("")
    add("| 쌍 | 바뀐 가중치 | env.yaml 차이(`log_dir` 제외) | 체크포인트 같음 | 둘 다 걷기 | seed별 종료 | 종료 합 | 옆 속도 vy | 무거운 로봇 종료 | 종료 전 기울기 cos |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for p in lateral_pairs():
        la, lb = p["lat"]
        add(f"| {p['a']} → {p['b']} | {', '.join(SHORT[t] for t in p['changed'])} | "
            + " · ".join(f"`{d}`" for d in p["diff"])
            + f" | {'예' if p['same_ckpt'] else '아니오 (' + RUN_CKPT[p['a']][0] + ' 대 ' + RUN_CKPT[p['b']][0] + ')'} | {'예' if p['walking'] else '아니오'} | "
            f"{'/'.join(p['seeds'][0])} → {'/'.join(p['seeds'][1])} | {la['terminated']} → {lb['terminated']} | {la['vy_mean']} → {lb['vy_mean']} | "
            f"{la['heavy_terminated']} → {lb['heavy_terminated']} | {la['tilt_cos_min_median'] or '—'} → {lb['tilt_cos_min_median'] or '—'} |")
    add("")
    add("- 종료 수는 계측 세대와 무관하다: 같은 Pilot-01 체크포인트를 낙상 미검출 세대(`go2_default_vs_pilot_v1`)와 검출 세대(`go2_a017_full_suite`)로 잰 seed별 종료가 같다(CSV 두 행).")
    lp = {(p["a"], p["b"]): p for p in lateral_pairs()}
    clean = lp[("A017", "G-A033")]
    seeds_up = all(int(y) > int(x) for x, y in zip(*clean["seeds"]))
    flat = {c: (lateral(*LATERAL_OF["A017"], c), lateral(*LATERAL_OF["G-A033"], c)) for c in ("left", "right", "diagonal_left", "diagonal_right")}
    add(f"- **A017 → G-A033(track 한 항, 체크포인트 같음): 험지 옆걸음 종료가 seed 셋 모두에서 늘었다(`{seeds_up}`).** 평지 옆걸음 종료는 "
        + " · ".join(f"{c} {a['terminated']} → {b['terminated']}" for c, (a, b) in flat.items())
        + ", 실제 vy는 " + " · ".join(f"{c} {a['vy_mean']} → {b['vy_mean']}" for c, (a, b) in flat.items())
        + " — 왼쪽 옆 속도가 줄었다.")
    fa = lp[("Default-01", "feet_air_time_020_v1")]
    add(f"- Default-01 → `feet_air_time_020_v1`(feet_air 한 항, 체크포인트 같음)은 종료 {fa['lat'][0]['terminated']} → {fa['lat'][1]['terminated']}이지만 두 정책 모두 걷지 않는다"
        f"(험지 옆 vy {fa['lat'][0]['vy_mean']} → {fa['lat'][1]['vy_mean']}). 옆으로 가지 않아서 덜 넘어진 것과 가를 수 없다 — 걷는 기준으로 옮기지 않는다.")
    walk3 = [lateral(*LATERAL_OF[n]) for n in ("Pilot-01", "A017", "G-A033")]
    add("- 로봇별로 처음 2초 옆 속도는 험지 옆걸음 종료를 설명하지 않는다: vy AUC " + " · ".join(l["early_vy_auc"] for l in walk3)
        + f". 로봇별로 가장 강한 것은 G-A033의 몸통 질량(AUC {walk3[-1]['mass_auc']})이고, 질량은 보상 항이 아니다.")
    add("- 옆걸음 기록이 없는 가중치 변경: " + " · ".join(f"`{t}` — {why}" for t, why in LATERAL_UNMEASURED) + ".")
    stopped = all(abs(diagonal_vy(run)) < STOPPED_VY for run in UNMEASURED_DIAGONAL.values())
    add(f"  이 회차들의 7 case에 평지 `diagonal_left`(옆 명령 `0.30`)가 있지만, 후보 실제 vy가 전부 `{STOPPED_VY}` 미만이다(`{stopped}`, seed 101 `steps.csv` 전 행 평균)."
        " 옆으로 가지 않은 정책이라 옆 넘어짐 정보가 없다. 기울기 벌점 두 항은 G-A033 종료 로봇이 뒤집혀 끝난다는 점(기울기 cos)에서 물리적으로 가깝지만, 값을 정할 데이터가 없다.")
    add("")
    add("## 3. 오르기 구간 보상률 (`CLIMB_REWARD.csv`, G-A033 가중치로 계산)")
    add("")
    add("| arm | case | 구간 | 로봇 | 추종 보상률 | 수직 벌점률 | 합 |")
    add("|---|---|---|---|---|---|---|")
    for r in read("CLIMB_REWARD.csv"):
        add(f"| {r['arm']} | {r['case']} | {r['group']} | {r['robots']} | {r['track_rate']} | {r['lin_vel_z_rate']} | {r['sum_rate']} |")
    add("")
    add("case 이름은 지형과 반대다: `stairs_*_down` = 오르기(역피라미드).")
    add("")
    add("## 4. 가중치별 관측 범위 (걷는 회차)")
    add("")
    add("| 가중치 | 전 회차 관측값 | 걷는 회차 관측값 |")
    add("|---|---|---|")
    for t in TERMS:
        allv = sorted({r[t] for r in rows}, key=float)
        add(f"| `{t}` | " + ", ".join(allv) + " | " + ", ".join(sorted({r[t] for r in s['walk']}, key=float)) + " |")
    add("")
    add("걷는 회차에서 값이 하나뿐인 가중치는 기울기를 잴 수 없다. 그 가중치를 움직이는 값은 전부 `OUT_OF_RANGE`다.")
    add("")
    add("## 5. 특이점 (표에서 계산)")
    add("")
    pair = s["reference_pair"]
    if s["walk_other_pair"]:
        counter = ", ".join(f"{r['name']}(`lin_vel_z {r['lin_vel_z_l2']}` · `ang_vel_xy {r['ang_vel_xy_l2']}`)"
                            for r in s["walk_other_pair"])
        head = (f"- **S1 걷기 조건 — 반례가 나왔다.** 걷는 회차 {len(s['walk'])}개 중 "
                f"{len(s['walk']) - len(s['walk_other_pair'])}개가 `lin_vel_z {pair[0]}` · `ang_vel_xy {pair[1]}`를 "
                f"함께 가진다. **예외: {counter}** — '이 쌍이 아니면 멈춘다'는 옛 읽기는 이 행으로 반증됐다. ")
    else:
        head = (f"- **S1 걷기 조건.** 걷는 회차 {len(s['walk'])}개는 전부 `lin_vel_z {pair[0]}` · "
                f"`ang_vel_xy {pair[1]}`를 함께 가진다. ")
    add(head +
        "둘 중 하나만 같은 회차: " + ", ".join(r["name"] for r in s["one_only"]) + " — 전부 정지. "
        "같은 쌍인데 정지한 회차: " + ", ".join(
            f"{r['name']}(" + ", ".join(f"{SHORT[t]} {r[t]}" for t in TERMS
                                       if r[t] not in {w[t] for w in s['walk']}) + ")"
            for r in s["same_pair_stalled"]) + " — 걷는 회차에 없는 값이 하나씩 있다.")
    add("- **S2 track 선 (feet_air 0.2, 걷는 회차).** " + " → ".join(
        f"{r['name']} track {r['track_lin_vel_xy_exp']}: 경사 {r['slope_plus_20_progress_m']} m · 10cm {r['climb10_ge2']} · 15cm {r['climb15_ge1']}"
        for r in s["track_line"]) + ".")
    lat_line = [(r["name"], lateral(*LATERAL_OF[r["name"]])) for r in s["track_line"]]
    add("  같은 선의 옆걸음: " + " → ".join(
        f"{n} 종료 {l['terminated']} (무거운 {l['heavy_terminated']} · 가벼운 {l['light_terminated']}, AUC {l['mass_auc']})"
        for n, l in lat_line) + ". 무게 민감(AUC)은 마지막 값에서만 나타난다.")
    add(f"- **S3 15cm 오르기는 track과 한 방향으로 움직이지 않는다** (단조: `{s['climb15_monotone_in_track']}`). "
        "10cm도 " + " → ".join(r["climb10_ge2"] for r in s["track_line"]) + "로 튄다 — 줄어든 Pilot-01→A017 쌍은 평가 체크포인트도 달라(§5-2) track 한 항의 비교가 아니다.")
    add("- **S4 feet_air 선 (track 1.4, 걷는 회차).** " + " → ".join(
        f"{r['name']} {r['feet_air_time']}: 경사 {r['slope_plus_20_progress_m']} m · 험지 속도 {r['rough_forward_speed']}"
        for r in s["fat_line"]) + ". 걷는 회차 밖 값: A015 feet_air 0.35는 정지.")
    share_text = " · ".join(f"{n} `{v[0]:.0%}` (오른 로봇 {v[1]}대) · 15cm {next(r for r in rows if r['name'] == n)['climb15_ge1']}"
                            for n, v in s["shares"].items() if v)
    add(f"- **S5 오르기 수직 벌점 몫 대 15cm 오르기.** 몫 = (15cm 정지 수직 벌점률 − 10cm 오름 수직 벌점률) / (10cm 오름 추종률 − 15cm 정지 추종률). {share_text}. "
        f"'몫이 작을수록 15cm를 더 오른다'가 성립하는가: `{s['share_explains_climb15']}`.")
    add("")
    add("## 5-1. track 기준 비율 (벌점 ÷ track)")
    add("")
    add("근거: 학습기 rsl_rl(설치본 `>= 4.0`, `launcher.log`)은 `normalize_advantage_per_mini_batch: false`(학습 `agent.yaml`)일 때"
        " 배치 전체의 advantage를 평균 0·표준편차 1로 바꾼 뒤 정책을 갱신한다"
        " (rsl_rl main `algorithms/ppo.py`: `advantages = (advantages - mean) / (std + 1e-8)`, 2026-09-16 원문 확인)."
        " 그래서 보상 전체에 같은 배수를 곱해도 정책 갱신 크기는 같고, 항 사이의 비율이 방향을 정한다."
        " 단 가치 함수 손실은 정규화하지 않으므로 완전히 무관하지는 않다. track은 양수 항이라 올리면 모든 벌점의 비율이 함께 줄어든다.")
    add("")
    add("| 회차 | track | lin_vel_z ÷ track | ang_vel_xy ÷ track | feet_air ÷ track | 회전 추종(`0.75`) ÷ track | 걷기 | 10cm 2단 이상 | 학습 지형 레벨 |")
    add("|---|---|---|---|---|---|---|---|---|")
    terms_by_run = {r["run"]: r for r in read("TRAINING_TERMS.csv")}
    for r in rows:
        t = float(r["track_lin_vel_xy_exp"])
        level = terms_by_run[TRAIN_OF[r["name"]]]["terrain_level"] if r["name"] in TRAIN_OF else "—"
        add(f"| {r['name']} | `{r['track_lin_vel_xy_exp']}` | `{float(r['lin_vel_z_l2']) / t:.3f}` | `{float(r['ang_vel_xy_l2']) / t:.4f}` | "
            f"`{float(r['feet_air_time']) / t:.4f}` | `{TRACK_ANG / t:.3f}` | {'걷기' if walking(r) else '정지'} | {r['climb10_ge2'] or '—'} | {level} |")
    add("")
    line = [next(r for r in rows if r["name"] == n) for n in ("Pilot-01", "A017", "G-A033")]
    steps = [1 - float(a["track_lin_vel_xy_exp"]) / float(b["track_lin_vel_xy_exp"]) for a, b in zip(line, line[1:])]
    add(f"- 걷는 기준에서 track을 올린 두 단계(Pilot→A017 `{-steps[0]:.0%}`, A017→G-A033 `{-steps[1]:.0%}`)는 벌점 비율을 한 방향으로 줄였다."
        " 10cm 오르기는 " + " → ".join(r["climb10_ge2"] for r in line) + "로 줄었다가 늘었다(S3). 줄어든 쌍은 평가 체크포인트가 달라, 체크포인트가 같은 A017→G-A033만 보면 비율이 줄 때 오르기가 늘었다(§5-2).")
    lats = [lateral(*LATERAL_OF[r["name"]]) for r in line]
    early = [float(l["early_abs_wz_auc"]) for l in lats]
    survivors_drift_more = all(float(l["heading_drift_survived_median_rad"]) > float(l["heading_drift_terminated_median_rad"]) for l in lats)
    add("- 회전 추종 비율도 track과 함께 줄었고 옆걸음 평균 \\|wz\\|는 " + " → ".join(l["abs_wz_mean"] for l in lats) + "로 늘었다(§2)."
        f" **그러나 로봇별로는 회전이 종료를 설명하지 않는다:** 처음 2초 \\|wz\\| AUC는 걷는 세 회차에서 `{min(early):.3f}`~`{max(early):.3f}`로"
        f" 약하고(질량 AUC G-A033 `{float(lats[-1]['mass_auc']):.3f}`보다 낮다), 방향 이탈이 생존 로봇에서 더 큰가: `{survivors_drift_more}`(§2 마지막 열)."
        " 회전 추종 가중치를 올리는 후보는 이 표로 뒷받침되지 않는다.")
    add("")
    add("## 5-2. track 한 항만 다른 쌍 — case별 이동 거리 (`CASE_BEHAVIOR.csv` `projected_progress_m`, seed 3개 평균)")
    add("")
    tp = track_pairs()
    for pair, lines in tp["diff"].items():
        add(f"- 학습 env.yaml 대조 {pair}: `log_dir` 외 다른 줄 = " + " · ".join(f"`{d}`" for d in lines) + ".")
    add("- 평가 체크포인트: " + " · ".join(f"{n} iter `{it}` ({src})" for n, (it, src) in RUN_CKPT.items()) + ".")
    agents = {n: (ROOT / "workspace/_keep" / rel).read_text(encoding="utf-8").splitlines() for n, rel in AGENT_YAML.items()}
    add(f"- 학습 `agent.yaml` 세 회차 동일: `{agents['Pilot-01'] == agents['A017'] == agents['G-A033']}`"
        " (Pilot-01은 G-A001 원본 회수본 `params/agent.yaml`). 학습 seed는 셋 다 `42`, 반복 `1000`이다."
        " Pilot-01의 학습 소스 코드는 보관되지 않아 대조하지 못했다.")
    add("")
    add("| case | 실제 동작 | Pilot-01 (track `1.2`, iter `999`) | A017 (`1.4`, iter `900`) | G-A033 (`1.5`, iter `900`) |")
    add("|---|---|---|---|---|")
    for case, v in tp["progress"].items():
        add(f"| {case} | {CASE_LABEL[case]} | `{v[0]:.3f}` | `{v[1]:.3f}` | `{v[2]:.3f}` |")
    add("")
    total = len(tp["progress"])
    add(f"- **A017→G-A033 (학습 설정 차이 = track 한 줄, 체크포인트 같음): 이동 거리가 늘어난 case `{tp['up']['A017→G-A033']}`/`{total}`.**"
        " 계단 오르기 로봇 수(§1 10cm 2단 이상)도 " + " → ".join(r["climb10_ge2"] for r in line[1:]) + "로 늘었다."
        " 같은 설정·같은 seed 학습과 평가는 결정론적이므로(`GO2_NOW.md` §0 [회차 실측]) 이 차이는 track 변경의 결과다 [확인].")
    add(f"- Pilot-01→A017: 늘어난 case `{tp['up']['Pilot-01→A017']}`/`{total}`. 학습 env.yaml·agent.yaml은 track 한 줄만 다르지만 평가 체크포인트가 iter `999` 대 `900`으로 다르다."
        " 이 쌍의 감소를 track 효과로만 읽지 않는다. S3의 '줄었다가 늘었다'는 이 쌍에서 나온다.")
    add("- 남는 한계: 학습 seed가 `42` 하나라 다른 seed에서도 같은 방향인지는 모른다 [모름]. 정지 계열(Default-01 track `1` → track_120_v1 `1.2`)은 §1에서 경사 전진이 줄었지만 체크포인트가 `800` 대 `900`이다(`GO2_VARIABLE_INFLUENCE.md` G-A009) — 걷는 기준에서의 결과를 정지 기준으로 옮기지 않는다.")
    add("")
    add("## 6. 발 들기(`feet_air_time`)와 계단")
    add("")
    add("### 6-1. 학습 로그의 발 들기 항 (`TRAINING_TERMS.csv`, 마지막 10 iter 평균)")
    add("")
    add("| 회차 | 가중치 | 걷기 | 학습 로그 항 | 항 ÷ 가중치 | 학습 지형 레벨 | 몸통 접촉 종료 |")
    add("|---|---|---|---|---|---|---|")
    terms = {r["run"]: r for r in read("TRAINING_TERMS.csv")}
    raw = []
    for r in sorted((r for r in rows if r["name"] in TRAIN_OF), key=lambda r: (float(r["feet_air_time"]), r["name"])):
        t = terms[TRAIN_OF[r["name"]]]
        ratio = float(t["feet_air_time"]) / float(r["feet_air_time"])
        if walking(r):
            raw.append(ratio)
        add(f"| {r['name']} | `{r['feet_air_time']}` | {'걷기' if walking(r) else '정지'} | {t['feet_air_time']} | `{ratio:.2f}` | {t['terrain_level']} | {t['base_contact']} |")
    add("")
    negative = all(float(terms[run]["feet_air_time"]) < 0 for run in TRAIN_OF.values())
    add(f"- 표의 모든 회차에서 항이 음수다(`{negative}`). 로봇의 평균 체공이 `0.5 s`보다 짧아서, 이 항은 실제로는 **짧은 걸음 벌점**으로 작동한다.")
    add(f"- 걷는 회차의 항 ÷ 가중치는 `{min(raw):.2f}` ~ `{max(raw):.2f}`로, 가중치가 `0.01`에서 `0.35`까지 변해도 크게 움직이지 않는다."
        " 가중치는 체공 시간 자체보다 벌점 크기를 바꾼다 [추정: 로그가 가중치 × 원값이라는 IL 기록 방식 가정]."
        " 가중치 `0.01` 행은 로그가 소수 3자리라 비율의 오차가 크다.")
    add("")
    add("### 6-2. 계단 기록이 있는 발 들기 값")
    add("")
    add("| 회차 | 가중치 | 걷기 | 계단 case | seed 수 | 속도 | 종료 로봇 | 생존 proxy |")
    add("|---|---|---|---|---|---|---|---|")
    cases = read("CASE_BEHAVIOR.csv")
    for r in sorted((r for r in rows if r["name"] in STAIRS_OF), key=lambda r: (float(r["feet_air_time"]), r["name"])):
        run, arm = STAIRS_OF[r["name"]]
        mine = [c for c in cases if (c["run"], c["arm"]) == (run, arm) and c["case"].startswith("stairs")]
        if not mine:
            add(f"| {r['name']} | `{r['feet_air_time']}` | {'걷기' if walking(r) else '정지'} | 원격 측정 없음 | 0 | — | — | — |")
            continue
        for case in sorted({c["case"] for c in mine}):
            got = [c for c in mine if c["case"] == case]
            kind = "오르기" if case.endswith("_down") else "내려가기"
            add(f"| {r['name']} | `{r['feet_air_time']}` | {'걷기' if walking(r) else '정지'} | {case} ({kind}) | {len(got)} | "
                + " / ".join(c["speed_xy_mean"] for c in got) + " | "
                + " / ".join(c["terminated_env_count"] for c in got) + " | "
                + " / ".join(c["survival_proxy"] for c in got) + " |")
    base15 = [c for c in cases if c["run"] == STAIRS_OF["A015"][0] and c["arm"] == "baseline_tier1"
              and c["case"].startswith("stairs")]
    for c in base15:
        add(f"| A015 기준(Pilot 재평가) | `0.2` | 걷기 | {c['case']} (내려가기) | 1 | {c['speed_xy_mean']} | {c['terminated_env_count']} | {c['survival_proxy']} |")
    add("")
    climbed = sorted({r["feet_air_time"] for r in rows if walking(r) and r["climb10_ge2"]})
    add(f"- **걷는 기준에서 오르기를 잰 발 들기 값은 {', '.join(f'`{v}`' for v in climbed)} 하나뿐이다.** 발 들기 값에 따른 오르기 변화는 데이터가 없다.")
    add("- 걷는 기준에서 다른 값으로 계단을 잰 것은 A015(`0.35`) 내려가기 seed 1개뿐이다. 같은 날 잰 Pilot 기준보다 빨라졌지만 대부분 종료됐다.")
    add("- 정지 기준(Default-01 대 `feet_air_time_020_v1`, chain01 대 A022)에서는 두 값 모두 계단에서 움직이지 않아 비교 정보가 없다.")
    for note in FEET_AIR_NOTES:
        add(f"- {note}")
    add("")
    add("## 7. 기존 사양 대조")
    add("")
    add("| 사양 | 바꾼 가중치 | 값 | 걷는 회차 관측값 | 위치 | 비고 |")
    add("|---|---|---|---|---|---|")
    for path, spec in reward_specs():
        if int(spec["work_id"].split("-A")[1]) < 37:
            continue
        for term, value in spec_changes(spec).items():
            note = ("도출 원리가 S5와 반대, 업로드 보류" if term == "lin_vel_z_l2" and not s["share_explains_climb15"] else "")
            note = " · ".join(filter(None, (note, SPEC_OUTCOME.get(spec["work_id"], ""),
                                            (spec.get("inference") or {}).get("status", ""))))
            add(f"| {spec['work_id']} | `{term}` | `{value}` | " + ", ".join(f"`{v}`" for v in walking_values(term))
                + f" | `{range_status(term, value)}` | {note} |")
    add("")
    return "\n".join(L)


def main(argv: list[str]) -> int:
    text = render()
    if "--check" in argv:
        same = DOC.is_file() and DOC.read_text(encoding="utf-8") == text
        print("기반 데이터 문서가 CSV와 같다" if same else "기반 데이터 문서가 낡았다 — 재생성하라")
        bad = [(p.name, spec_problems(s)) for p, s in reward_specs() if s["work_id"] not in PRE_RULE_SPECS and spec_problems(s)]
        for name, problems in bad:
            print(name, problems)
        return 0 if same and not bad else 1
    DOC.write_text(text, encoding="utf-8", newline="\n")
    print(DOC)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
