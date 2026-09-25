"""Go2 seed 흔들림과 보상 항의 관계 — 이미 있는 원자료에서만 계산한다 (GPU 0).

왜 있는가 (2026-09-17 사용자 지시: "SEED 흔들림과 관련된 보상을 찾고, 잡았을 때 혜택을 잡아줘").
학습 seed는 전 회차 42 하나라 학습 seed 흔들림은 **측정된 적이 없다**.  그래서 이 도구는 흔들림의 크기를
만들어 내지 않는다.  대신 이미 측정된 네 가지를 한 곳에 모은다.
  SAME_SEED_REPEAT.csv   같은 설정·같은 seed 재학습 쌍의 지형 레벨 (결정론 확인)
  ONE_CHANGE_DRIFT.csv   같은 seed에서 한 항만 바꾼 쌍의 걷기 margin 변화 대 지형 레벨·10cm 오르기 변화
  TERM_HEADROOM.csv      G-A033 가중치에서 걷기 구간 경계까지의 거리 (경계대 = seed 운이 가르는 구간, 추정)
  BAND_RUNS.csv          margin 경계대 안의 회차와 실제 결과 (같은 구간에서 걷기·정지가 갈렸다)
  EVAL_SEED_SPREAD.csv   G-A033 69 case의 평가 seed 101/202/303 사이 생존 로봇 수 폭 (평가 seed 흔들림, 측정됨)
생성 보고서: `workspace/training/quadruped/reports/GO2_SEED_SENSITIVITY.md` (손으로 고치지 않는다).

    python -B tools/go2_seed_sensitivity.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(QUAD))

from go2_fixed_eval_report import _case_proxy  # noqa: E402

RUNS = QUAD / "reports/runs"
MECH = QUAD / "reports/evidence/go2_reward_mechanism_20260917"
STAIRS = QUAD / "reports/evidence/go2_stairs_behavior_20260916/STAIRS_CLIMB.csv"
OUT = QUAD / "reports/evidence/go2_seed_sensitivity_20260917"
REPORT = QUAD / "reports/GO2_SEED_SENSITIVITY.md"
REGISTRY = QUAD / "config/go2_self_eval_registry.json"
BASE = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"
DEPLOYED = ROOT / "workspace/server_returns/G-A027/approved/go2_a017_full_suite/a017/quadruped_rewards.py"

# 같은 설정·같은 seed 42로 다시 학습한 쌍 (GO2_NOW.md §0, test_go2_run_ledger_contract test_13)
REPEATS = (("go2_g_a010_lin_vel_z_m2", "go2_g_a010_lin_vel_z_m2_v2_260906"),
           ("go2_g_a013_flat_orientation_m1", "go2_g_a025_flat_orientation_m1"))
# 같은 seed 42, 한 항 변경, 둘 다 걷는 쌍 (등급 A: GO2_VARIABLE_INFLUENCE.md)과 G-A038
PAIRS = (
    ("A017", "go2_g_a017_pilot_track_lin_vel_xy_140", "A031", "go2_g_a031_a017_feet_air_time_001",
     "feet_air_time 0.2->0.01", None),
    ("A017", "go2_g_a017_pilot_track_lin_vel_xy_140", "A032", "go2_g_a032_a017_feet_air_time_010",
     "feet_air_time 0.2->0.1", None),
    ("A017", "go2_g_a017_pilot_track_lin_vel_xy_140", "G-A033", "go2_g_a033_a017_track_lin_vel_xy_150",
     "track_lin_vel_xy_exp 1.4->1.5", ("a017", "candidate")),
    ("G-A033", "go2_g_a033_a017_track_lin_vel_xy_150", "G-A038", "go2_g_a038_a033_ang_vel_xy_m008",
     "ang_vel_xy_l2 -0.05->-0.08", ("candidate", "candidate")),
)
# 평가 기록에 있는 상황과, 세 정책에서 (원하는 − 실패) 부호가 일치한 항 (FORECAST §5-1)
SITUATION_OF = {"stairs_10_down": "climb", "stairs_15_down": "climb", "rough_lateral": "sway",
                "push_pos_x": "push", "push_neg_x": "push", "push_pos_y": "push", "push_neg_y": "push"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write(name: str, table: list[list[str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(table)


def terrain999() -> dict[str, str]:
    return {r["run"]: r["terrain"] for r in rows(RUNS / "TERRAIN_AT_PIN.csv") if r["iteration"] == "999"}


def margins() -> dict[str, dict[str, str]]:
    return {r["name"]: r for r in rows(MECH / "RUN_MARGIN.csv")}


def g_a038_margin() -> str:
    for r in rows(MECH / "PROBES.csv"):
        if r["term"] == "ang_vel_xy_l2" and r["to"] == "-0.08":
            return r["margin"]
    raise RuntimeError("PROBES.csv lost the ang_vel_xy_l2 -0.08 row")


def climb10() -> dict[tuple[str, str], tuple[int, int]]:
    out: dict[tuple[str, str], list[int]] = {}
    for r in rows(STAIRS):
        if r["case"] == "stairs_10_down":
            got = out.setdefault((r["run"], r["arm"]), [0, 0])
            got[0] += int(r["body_rise_ge1"])
            got[1] += int(r["body_rise_ge2"])
    return {k: (v[0], v[1]) for k, v in out.items()}


def same_seed_repeat() -> list[list[str]]:
    level = terrain999()
    table = [["first", "repeat", "terrain_999_first", "terrain_999_repeat", "identical"]]
    for a, b in REPEATS:
        table.append([a, b, level[a], level[b], str(level[a] == level[b])])
    return table


def one_change_drift() -> list[list[str]]:
    level, margin, climbs = terrain999(), margins(), climb10()
    margin["G-A038"] = {"margin": g_a038_margin()}
    table = [["from", "to", "change", "margin_from", "margin_to", "margin_delta", "terrain_999_from",
              "terrain_999_to", "terrain_delta", "climb10_ge1_from", "climb10_ge1_to", "climb10_ge2_from",
              "climb10_ge2_to"]]
    for a, run_a, b, run_b, change, arms in PAIRS:
        ma, mb = float(margin[a]["margin"]), float(margin[b]["margin"])
        ta, tb = float(level[run_a]), float(level[run_b])
        cell = ["", "", "", ""]
        if arms:
            ca = climbs[("go2_a017_full_suite", arms[0])] if a == "A017" else climbs[(run_a, arms[0])]
            cb = climbs[(run_b, arms[1])]
            cell = [str(ca[0]), str(cb[0]), str(ca[1]), str(cb[1])]
        table.append([a, b, change, f"{ma:+.4f}", f"{mb:+.4f}", f"{mb - ma:+.4f}", f"{ta:.4f}", f"{tb:.4f}",
                      f"{tb - ta:+.4f}", *cell])
    return table


def term_headroom() -> list[list[str]]:
    table = [["term", "g_a033_value", "walk_zone_edge", "edge_over_value", "side"]]
    seen = set()
    for r in rows(MECH / "PROBES.csv"):
        if r["term"] in seen:
            continue
        seen.add(r["term"])
        value, edge = float(r["from"]), float(r["edge_weight"])
        ratio = edge / value
        side = "reward: edge below value" if value > 0 and edge < value else \
            "reward: edge above value" if value > 0 else "penalty: edge stronger than value"
        table.append([r["term"], r["from"], r["edge_weight"], f"{ratio:.3f}", side])
    return table


def band_runs() -> list[list[str]]:
    table = [["run", "margin", "margin_loo", "zone", "zone_loo", "walked"]]
    for name, r in margins().items():
        if r["zone"] == "BAND" or r["zone_loo"] == "BAND":
            table.append([name, r["margin"], r["margin_loo"], r["zone"], r["zone_loo"], r["walking"]])
    return table


def eval_seed_spread() -> list[list[str]]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    std = float(registry["score"].get("tracking_proxy_std", 0.5))
    table = [["scenario", "case", "situation", "upright_101", "upright_202", "upright_303", "robots", "spread"]]
    for scenario in registry["scenarios"]:
        for case_id in scenario["internal_cases"]:
            upright, n = [], 0
            for seed in ("101", "202", "303"):
                path = BASE / "cases" / f"seed_{seed}" / case_id / "summary.json"
                if not path.is_file():   # G7 dr_seed_<s> case는 평가 seed 하나에서만 돈다
                    continue
                summary = json.loads(path.read_text(encoding="utf-8"))
                n = int(summary["posture_envs_observed"])
                surv = _case_proxy(case_id, summary, std)["survival_proxy"]
                upright.append(round(surv * n))
            if len(upright) != 3:
                continue
            table.append([scenario["id"], case_id, SITUATION_OF.get(case_id, ""), *map(str, upright), str(n),
                          str(max(upright) - min(upright))])
    return table


def deployed_notes() -> list[tuple[int, str]]:
    lines = DEPLOYED.read_text(encoding="utf-8").splitlines()
    return [(i + 1, line.strip()) for i, line in enumerate(lines) if "실행마다" in line or "cudnn" in line]


def report(tables: dict[str, list[list[str]]]) -> str:
    repeat, drift, head, band, spread = (tables[k] for k in (
        "SAME_SEED_REPEAT.csv", "ONE_CHANGE_DRIFT.csv", "TERM_HEADROOM.csv", "BAND_RUNS.csv", "EVAL_SEED_SPREAD.csv"))

    def md(table: list[list[str]], cols: list[int] | None = None) -> str:
        cols = cols if cols is not None else list(range(len(table[0])))
        out = ["| " + " | ".join(table[0][c] for c in cols) + " |", "|" + "---|" * len(cols)]
        out += ["| " + " | ".join(f"`{r[c]}`" if r[c] else "—" for c in cols) + " |" for r in table[1:]]
        return "\n".join(out)

    wide = sorted(spread[1:], key=lambda r: -int(r[7]))
    top = [spread[0]] + [r for r in wide if int(r[7]) >= 4]
    notes = "\n".join(f"  - `{DEPLOYED.name}:{n}` — {text}" for n, text in deployed_notes())
    drift_body = {r[1]: r for r in drift[1:]}
    a038 = drift_body["G-A038"]
    return f"""# Go2 seed 흔들림과 보상 항 (2026-09-17)

> **생성 문서 — 손으로 고치지 않는다.** `python -B tools/go2_seed_sensitivity.py`가 만든다.
> 증거 `reports/evidence/go2_seed_sensitivity_20260917/`, 관문 `tools/test_go2_seed_sensitivity_contract.py`.
> 표기: [확인] 원자료에서 직접 · [추정] 확인된 사실에서 유추 · [모름] 근거 없음.

## 0. 세 가지 흔들림을 구분한다

| 종류 | 상태 | 근거 |
|---|---|---|
| 같은 설정·같은 seed 재학습 | **0** [확인] | §1 |
| 평가 seed(101·202·303) 사이 | **측정됨** [확인] | §4, `BASELINE_MARGIN.csv`(생존 이항 재표집) |
| 학습 seed 사이 | **측정된 적 없음** [확인] — 전 학습이 seed 42 | `GO2_NOW.md` §0 |

한 항을 바꾸면 seed가 같아도 학습 궤적 전체가 달라진다. 그래서 한 항 변경 회차의 차이에는 **레버 효과와 궤적 갈라짐이 섞여 있고**, 둘을 가를 대조군(같은 설정의 다른 seed)이 없다 [확인: 대조군 0건].

## 1. 같은 seed 재학습은 결정론이다 (`SAME_SEED_REPEAT.csv`)

{md(repeat)}

- [확인] 배포 주석 중 cudnn 비결정성 문장(아래 둘째 줄)은 이 스택에서 반례 2건이다. 첫째 줄(발 들기 경계)은 §3-2에서 쓴다.
{notes}

## 2. 같은 seed의 한 항 변경 — margin 변화 대 결과 변화 (`ONE_CHANGE_DRIFT.csv`)

{md(drift)}

- [확인] 걷기 margin 변화가 `{drift[1][5]}`(A031)·`{drift[3][5]}`(G-A033)처럼 같은 방향이어도 지형 레벨은 `{drift[1][8]}`·`{drift[3][8]}`로 크기 순서가 뒤집힌다.
- [확인] G-A038은 margin이 걷기 구간(`{a038[4]}`)에 남았고 실제로 걸었지만, 지형 레벨은 `{a038[8]}`, 10cm 오르기 ≥1단은 `{a038[9]}` → `{a038[10]}`대로 무너졌다.
- [추정] margin은 **걷기/정지**만 설명하고, 지형 레벨·계단은 margin 변화의 크기와 맞지 않는다. 이 어긋남이 레버 때문인지 궤적 갈라짐 때문인지는 학습 seed 대조군 없이는 가를 수 없다 [모름].

## 3. seed 운과 가까운 보상 항

### 3-1. margin 경계대의 회차 (`BAND_RUNS.csv`)

{md(band)}

- [확인] 경계대(margin `+0.0033`~`+0.0155`)에서 Pilot-01은 걸었고 A018은 멈췄다. margin 순서와 결과가 반대인 유일한 쌍이다.
- [추정] 경계대 안에서는 보상 식이 걷기·정지를 거의 같게 치므로, 결과를 가르는 것은 seed·궤적이다. A018에서 바꾼 항은 `action_rate_l2`다 — **margin으로 설명되지 않은 유일한 항**이다(FORECAST §3).

### 3-2. G-A033 가중치에서 걷기 구간 경계까지의 거리 (`TERM_HEADROOM.csv`)

{md(head)}

- 읽는 법: `edge_over_value`가 1에 가까울수록 작은 변경으로 경계대에 들어간다.
- [확인: 계산] `track_lin_vel_xy_exp`는 `{head[1][2]}`까지 내려가면 경계다(현재의 `{head[1][3]}`배). 벌점 항은 `dof_acc_l2`·`ang_vel_xy_l2`가 현재의 약 2배, `action_rate_l2`가 약 3배에서 경계다.
- [추정] 경계에 가까운 항일수록 그 항을 움직인 회차의 걷기/정지는 seed 운의 영향을 크게 받는다. G-A033 자체는 margin `+0.1359`로 경계대 최고값의 약 9배라, **G-A033의 걷기 자체는 seed에 강할 것**이다. 계단·옆걸음 결과에는 이 말이 해당하지 않는다(§2).
- [확인: 배포 주석] `feet_air_time`은 "정확한 경계는 실행마다 다름"이라고 배포 파일이 직접 적는다.

## 4. 평가 seed 흔들림이 큰 상황 (`EVAL_SEED_SPREAD.csv`, G-A033, 로봇 32대)

폭 = 세 평가 seed 사이 넘어지지 않은 로봇 수의 최대 − 최소. 폭 4대 이상만 적는다.

{md(top)}

- [확인] 폭 4대 이상은 {", ".join(f"`{r[1]}` {r[7]}대" for r in top[1:])}뿐이다. 가장 넓은 case가 G-A038이 무너진 10cm 오르기다. 험지 옆걸음(`rough_lateral`)은 {next(r[7] for r in spread[1:] if r[1] == "rough_lateral")}대로 좁다 — 옆걸음 종료는 평가 seed와 상관없이 일정하게 일어난다.
- [확인: FORECAST §5-1] `lin_vel_z_l2`·`ang_vel_xy_l2`는 비교 가능한 정책 전부(계단·밀침 2개, 흔들림 3개)에서 **계단(오르는 쪽이 값이 크다)과 흔들림·밀침(넘어지기 직전이 값이 크다)의 부호가 반대**다. 한쪽을 강하게 벌하면 다른 쪽을 돕는 맞교환 항이다. G-A038(`ang_vel_xy_l2` 강화)이 옆걸음을 얻고 10cm 오르기를 잃은 것과 같은 방향이다.
- [추정] 10cm 오르기는 평가 seed만 바꿔도 폭이 가장 넓은 상황이고, 위 두 항이 그 상황의 보상 균형을 직접 움직인다. 그래서 이 두 항을 바꾼 회차의 계단 결과가 학습 seed에도 가장 민감할 것이다. 측정은 없다 [모름].

## 5. 학습 seed 흔들림을 잡으면 풀리는 것

| # | 지금 가를 수 없는 것 | 원자료 | seed 대조군이 있으면 |
|---|---|---|---|
| 1 | 기준선 승급 근거 G4 `+3.65467`가 `track 1.5` 때문인가 | `BASELINE_MARGIN.csv` | G-A033 설정의 다른 seed가 같은 G4를 내는지로 판정 |
| 2 | G-A038의 10cm 오르기 붕괴가 `ang_vel_xy_l2` 때문인가 | §2 | G-A033 설정 다른 seed의 10cm ≥1단 수가 `{a038[9]}` 근처에 머물면 레버, 크게 흔들리면 판정 보류 |
| 3 | 경계대의 폭(Pilot 걷기·A018 정지) | §3-1 | 같은 설정의 걷기/정지 비율로 경계대를 측정값으로 바꿈 |
| 4 | 사전 등록 한도가 진짜 잡음보다 넓은가 | `reports/evidence/go2_fact_rules_20260917/` | 지금 한도는 평가 표집만 넣은 **하한**이다. 학습 seed 분산을 더하면 FAIL/PASS가 잡음인지 가려진다 |
| 5 | 10cm ≥2단이 한 항 변경마다 크게 흔들린 것 | `STAIRS_CLIMB.csv` | 흔들림 폭 안의 차이는 레버로 인용하지 않게 됨 |
| 6 | 학습 18회의 단일 seed 결과 중 어느 것이 흔들림 밖인가 | `reports/runs/INDEX.md` | 과거 결론을 흔들림 밖/안으로 다시 표시 |

- [확인] 이 표의 1~6은 지금 모두 [모름]이다. 풀리는 것은 **해석 가능성**이지 점수 상승이 아니다.
- [모름] seed 반복 회차가 R-6(보상 가중치만) 안인지는 사용자 결정 대기다 — 열린 결정
  `U2-SEED-REPLICATE-20260918`(`reports/GO2_OPEN_DECISIONS.md`). 2026-09-19: 이 번호를 생성
  문서에 손으로 적어 두었더니 다음 재생성이 지웠다. 생성 문서의 문구는 생성기에서 고친다.
"""


def main() -> int:
    tables = {
        "SAME_SEED_REPEAT.csv": same_seed_repeat(),
        "ONE_CHANGE_DRIFT.csv": one_change_drift(),
        "TERM_HEADROOM.csv": term_headroom(),
        "BAND_RUNS.csv": band_runs(),
        "EVAL_SEED_SPREAD.csv": eval_seed_spread(),
    }
    for name, table in tables.items():
        write(name, table)
    REPORT.write_bytes(report(tables).encode("utf-8"))
    print("wrote", OUT, "and", REPORT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
