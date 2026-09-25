"""회차 보고서를 산출물에서 생성한다 — 시간 순으로 한 회차에 한 파일.

`tools/go2_run_ledger.py`가 읽은 것만 쓴다. 손으로 고칠 곳은 없다.
다시 돌리면 같은 파일이 나온다. 산출물이 바뀌면 보고서가 바뀐다.

    python tools/build_go2_run_reports.py

기존 판정을 옮겨 적지 않는다. 이 보고서는 "무엇이 측정됐는가"만 적는다.
"채택/기각"은 사람이 종합 보고서에서 내린다.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from go2_run_ledger import PIN_ITERATIONS, harvest, occurred, terrain_at  # noqa: E402

OUT = ROOT / "workspace/training/quadruped/reports/runs"
SCENARIOS = ("G1", "G2", "G3", "G4", "G5", "G6", "G7")
# 계측 세대별로 무엇을 믿을 수 있는지. 세대가 다르면 70점을 나란히 놓을 수 없다.
INSTRUMENT_NOTE = {
    "no_fall_detection": "낙상을 세지 않는다. 생존 proxy가 종료 수만 본다 → 점수가 위로 치우친다.",
    "posture_gate_v1": "자세 기반 낙상 검출 도입. 측정 계약 필드는 아직 없다.",
    "posture_gate_v2": "낙상 검출 + 측정 계약 고정(양 채널 필수·v1 대체 금지·커버리지 0.99).",
}


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}".rstrip("0").rstrip(".") or "0"
    return str(value)


def reward_table(rewards: dict[str, float]) -> list[str]:
    if not rewards:
        return ["학습 `env.yaml`이 회수되지 않았다. reward 가중치 **모름**.", ""]
    lines = ["| reward 항 | 가중치 |", "|---|---|"]
    lines += [f"| `{k}` | {fmt(v)} |" for k, v in rewards.items()]
    return lines + [""]


def curve_table(training: dict[str, Any]) -> list[str]:
    curve = training.get("curve", {})
    if not curve:
        return []
    cols = ["terrain", "track_lin_vel", "episode_length", "base_contact", "time_out",
            "reward", "action_std", "entropy_loss"]
    head = ["| iter | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    rows = []
    for it in sorted(curve, key=int):
        rows.append("| " + str(it) + " | " + " | ".join(fmt(curve[it].get(c)) for c in cols) + " |")
    return head + rows + [""]


def arm_table(arms: dict[str, Any]) -> list[str]:
    if not arms:
        return ["평가 case가 회수되지 않았다. 70점 **미측정**.", ""]
    lines = ["| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |",
             "|---|---|---|---|---|---|"]
    for name, body in arms.items():
        recorded = f"{body['as_recorded_70']:.5f}" if body.get("as_recorded_70") is not None else "보고서 없음"
        lines.append(
            f"| `{name}` | {body['total_70']:.5f} | {recorded} | {body['observed_cases']} | "
            f"`{body['instrument']}` | {body['locomotion']} |"
        )
    lines.append("")
    if any(b.get("as_recorded_70") is None for b in arms.values()):
        lines += ["> 이 arm은 표준 평가 보고서(`SELF_EVAL_REPORT.json`)가 생성되지 않았다. "
                  "당시 판정이 쓴 숫자를 산출물에서 확인할 수 없고, 위 재채점값만 근거로 남는다.", ""]
    partial = [name for name, b in arms.items() if (b["observed_cases"] or 0) < 69]
    if partial:
        names = " · ".join(f"`{name}`" for name in partial)
        lines += [
            f"> {names}: 69 case 전수가 아니다. 빠진 시나리오는 0점으로 합산되므로 **그 arm의 70점은 "
            "전수 평가본과 같은 축에 놓을 수 없다.** 같은 부분 평가끼리만 비교한다.", ""]
    for name, body in arms.items():
        if (body["observed_cases"] or 0) == 69:
            lines += [f"`{name}` 시나리오별 배점:", "",
                      "| " + " | ".join(SCENARIOS) + " |", "|" + "---|" * len(SCENARIOS),
                      "| " + " | ".join(f"{body['scenarios_70'].get(s, 0):.2f}" for s in SCENARIOS) + " |", ""]
    return lines


def render(index: int, record: dict[str, Any]) -> str:  # noqa: C901
    training = record.get("training", {})
    arms = record.get("arms", {})
    when = occurred(record) or "시각 미회수"
    lines = [
        f"# {index:02d}. {record['run']}",
        "",
        f"- 시각: `{when}` ({'학습 로그' if training else ('평가 로그' if record.get('evaluated') else '학습기 run 폴더')} 내장값)",
        f"- 산출물: `{record['path']}`",
    ]
    if record.get("replicate_of"):
        lines.append(
            f"- **재현 회차**: `{record['replicate_of']}`와 학습 지표 "
            f"{training.get('metric_line_count')}줄이 **완전히 일치**한다. 같은 학습이 두 번 나온 것이다."
        )
    if training:
        lines.append(f"- 학습: {training['iterations_logged']}/{training['max_iterations']} iter, "
                     f"로그 `{training['log']}`")
    if record.get("training_log_missing"):
        missing = record["training_log_missing"]
        lines.append(f"- 학습 산출물: 체크포인트 {', '.join(missing['checkpoints'])} — **{missing['note']}**")
    if record.get("training_tfevents"):
        tf = record["training_tfevents"]
        lines.append(f"- 텐서보드 기록: `{tf['source']}` ({tf['iterations_logged']} iter)")
    if record.get("robot_evidence"):
        lines.append(f"- 4족 판별 근거: `{Path(record['robot_evidence'][0]).name}` 외 "
                     f"{len(record['robot_evidence']) - 1}건 (이름이 아니라 산출물 경로로 가렸다)")
    lines += ["", "## reward 설정", ""] + reward_table(record.get("rewards", {}))
    if training or record.get("training_tfevents"):
        lines += ["## 학습 곡선", "",
                  "`terrain`은 `terrain_levels_vel` 커리큘럼 도달 레벨(만점 10)이다. "
                  "이 커리큘럼은 **이동 거리로 승급**한다.", ""]
        if not training:
            lines += ["텍스트 로그가 없어 텐서보드 기록에서 같은 태그를 읽었다.", ""]
        lines += curve_table(training or record["training_tfevents"])
    lines += ["## 평가 — 정본 registry로 재채점", "",
              "당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.", ""]
    lines += arm_table(arms)
    if record.get("instrument_symmetric") is False:
        lines += ["> **계측 비대칭.** 이 묶음의 두 arm이 서로 다른 계측 세대로 측정됐다. "
                  "둘의 차이는 정책 차이와 계측 차이가 섞인 값이라 **단일 변수 비교로 쓸 수 없다.**", ""]
    generations = {b["instrument"] for b in arms.values() if b.get("instrument")}
    if generations:
        lines += ["## 계측 한계", ""]
        lines += [f"- `{g}` — {INSTRUMENT_NOTE[g]}" for g in sorted(generations)]
        lines.append("")
    lines += ["---", "",
              "이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.", ""]
    return "\n".join(lines)


def index_page(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Go2 회차 보고서 — 시간 순",
        "",
        "`workspace/_keep` 산출물에서 생성했다. 판정은 담지 않는다 — 측정만 담는다.",
        "종합·기준선 결정은 `../GO2_RUN_SYNTHESIS_20260916.md`에 있다.",
        "",
        "| # | 시각 | 회차 | 학습 | 대표 arm 70점 | case | 계측 세대 | 양팔 계측 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, record in enumerate(records, 1):
        arms = record.get("arms", {})
        # 대표 arm은 후보 쪽이다. 같은 묶음의 baseline arm이 더 낡은 계측일 수 있어
        # 점수만으로 고르면 계측 세대 칸이 엉뚱한 arm을 가리킨다.
        best = max(arms.values(), key=lambda a: (a["observed_cases"] or 0, a["total_70"])) if arms else None
        note = " (재현)" if record.get("replicate_of") else ""
        link = f"[{record['run']}]({i:02d}_{record['run']}.md){note}"
        kind = "1000 iter" if record.get("training") else "평가 전용"
        score = f"{best['total_70']:.5f}" if best else "—"
        cases = str(best["observed_cases"]) if best else "—"
        gen = f"`{best['instrument']}`" if best else "—"
        symmetric = record.get("instrument_symmetric")
        pair = "—" if symmetric is None else ("대칭" if symmetric else "**비대칭**")
        lines.append(
            f"| {i:02d} | `{occurred(record) or '—'}` | {link} | {kind} | {score} | {cases} | {gen} | {pair} |")
    lines += ["", "기계 판독본은 `LEDGER.csv`(회차 × arm 한 행). 생성: `python tools/build_go2_run_reports.py`", ""]
    return "\n".join(lines)


CSV_COLUMNS = (
    "seq", "occurred", "run", "kind", "track_lin_vel_xy_exp", "feet_air_time", "lin_vel_z_l2",
    "ang_vel_xy_l2", "action_rate_l2", "flat_orientation_l2", "iterations",
    "terrain_999", "track_lin_vel_999", "episode_length_999", "base_contact_999",
    "arm", "total_70", "as_recorded_70", "cases", "instrument", "instrument_symmetric",
    "locomotion", "replicate_of", "hypothesis_registered",
)


def csv_rows(records: list[dict[str, Any]]) -> list[list[str]]:
    """회차 원장의 기계 판독본. `hypothesis_registered`는 사전등록 여부만 적는다.

    사전에 등록되지 않은 가설을 사후에 채우면 그건 기록이 아니라 창작이다.
    현재 사전등록 블록을 가진 spec은 G-A030·031·032·033·035뿐이고, 그중 어느 것도
    숫자로 된 기대 이득을 담고 있지 않다. 그래서 전 회차가 NOT_REGISTERED다.
    """
    rows = []
    for seq, record in enumerate(records, 1):
        training = record.get("training", {})
        last = (training.get("curve") or {}).get("999", {})
        arms = record.get("arms") or {"—": {}}
        for arm, body in arms.items():
            # 그 arm 정책을 학습한 reward만 적는다(go2_run_ledger.arm_rewards). 모르면 비운다.
            rewards = body.get("rewards") or {}
            # 학습 곡선도 그 회차에서 학습된 arm의 것이다. baseline arm 행에 붙이지 않는다.
            curve = last if arm in ("candidate", "—") else {}
            rows.append([str(x) if x is not None else "" for x in (
                seq, occurred(record), record["run"],
                "train" if training else "eval",
                rewards.get("track_lin_vel_xy_exp"), rewards.get("feet_air_time"),
                rewards.get("lin_vel_z_l2"), rewards.get("ang_vel_xy_l2"),
                rewards.get("action_rate_l2"), rewards.get("flat_orientation_l2"),
                training.get("max_iterations") if curve or arm in ("candidate", "—") else None,
                curve.get("terrain"), curve.get("track_lin_vel"),
                curve.get("episode_length"), curve.get("base_contact"),
                arm, body.get("total_70"), body.get("as_recorded_70"),
                body.get("observed_cases"), body.get("instrument"),
                record.get("instrument_symmetric"), body.get("locomotion"),
                record.get("replicate_of"), "NOT_REGISTERED",
            )])
    return rows


def _weights() -> dict[str, float]:
    """가중치는 정본 registry 에서 읽는다. 손으로 적으면 registry 가 바뀌어도 안 따라간다."""
    registry = json.loads(
        (ROOT / "workspace/training/quadruped/config/go2_self_eval_registry.json")
        .read_text(encoding="utf-8"))
    return {s["id"]: float(s["weight"]) for s in registry["scenarios"]}


WEIGHTS = _weights()


def scenario_rows(records: list[dict[str, Any]]) -> list[list[str]]:
    """G축별 점수를 산출물로 내보낸다.

    `rescore()`는 `scenarios_70`을 진작 반환하고 있었는데 아무 파일에도 쓰지 않았다.
    그래서 종합 §7의 축별 표는 내가 화면에서 손으로 옮겨 적은 숫자였다 — 아티팩트가
    아니라 필사본이다. `go2_claim_check`가 그걸 근거 없음으로 잡아냈다. 여기서 끊는다.
    """
    axes = sorted({sid for record in records
                   for body in (record.get("arms") or {}).values()
                   for sid in (body.get("scenarios_70") or {})})
    rows = []
    for record in records:
        for arm, body in (record.get("arms") or {}).items():
            scenarios = body.get("scenarios_70") or {}
            if not scenarios:
                continue
            rows.append([record["run"], arm, str(body.get("instrument") or ""),
                         *[fmt(scenarios.get(axis), 5) for axis in axes],
                         fmt(body.get("total_70"), 5),
                         fmt(body.get("tracking_xy_rmse_mean"), 5),
                         # 감점 = 그 축의 만점 − 관측. GO2_NOW 의 "최대 감점" 이 이 값이다.
                         *[fmt(70 * WEIGHTS[axis] - scenarios[axis], 5) if axis in scenarios else "—"
                           for axis in axes]])
    return [["run", "arm", "instrument", *axes, "total_70", "tracking_xy_rmse_mean",
             *[f"{axis}_deduction" for axis in axes]], *rows]


def delta_rows(records: list[dict[str, Any]]) -> list[list[str]]:
    """arm 사이의 점수 차이를 산출물로 낸다.

    두 종류를 낸다.
      * 같은 묶음 안의 두 arm — 계측이 같으므로 대칭 비교다(종합 §5).
      * 여러 묶음에 걸친 같은 모델(`pilot`) — 계측 세대가 바뀌었을 때의 이동이다(§4).
        같은 정책인데 점수가 움직였다면 그건 정책이 아니라 계측이 움직인 것이다.
    """
    scored = []
    for record in records:
        for arm, body in (record.get("arms") or {}).items():
            if body.get("total_70") is not None and body.get("observed_cases"):
                scored.append((record["run"], arm, body["total_70"],
                               body.get("instrument"), body.get("observed_cases")))

    rows = [["kind", "from", "to", "cases", "instrument_from", "instrument_to", "delta_70"]]
    for run in dict.fromkeys(r for r, *_ in scored):
        arms = [s for s in scored if s[0] == run]
        for i, a in enumerate(arms):
            for b in arms[i + 1:]:
                if a[4] != b[4]:
                    continue  # case 수가 다르면 축이 다르다. 빼지 않는다.
                # 양방향을 모두 낸다. 문서가 어느 쪽을 기준으로 잡았는지에 따라 부호가
                # 뒤집히는데, 부호는 주장의 일부다 — 한쪽만 내면 반대 방향 주장이
                # 검증 없이 통과하거나, 맞는 주장이 틀렸다고 잡힌다.
                rows.append(["within_package", f"{run}:{a[1]}", f"{run}:{b[1]}",
                             str(a[4]), str(a[3]), str(b[3]), f"{b[2] - a[2]:+.5f}"])
                rows.append(["within_package", f"{run}:{b[1]}", f"{run}:{a[1]}",
                             str(b[4]), str(b[3]), str(a[3]), f"{a[2] - b[2]:+.5f}"])

    pilots = [s for s in scored if s[1].startswith("pilot")]
    for i, a in enumerate(pilots):
        for b in pilots[i + 1:]:
            if a[4] != b[4]:
                continue
            rows.append(["same_model_across_instruments", f"{a[0]}:{a[1]}", f"{b[0]}:{b[1]}",
                         str(a[4]), str(a[3]), str(b[3]), f"{b[2] - a[2]:+.5f}"])
            rows.append(["same_model_across_instruments", f"{b[0]}:{b[1]}", f"{a[0]}:{a[1]}",
                         str(b[4]), str(b[3]), str(a[3]), f"{a[2] - b[2]:+.5f}"])
    return rows


INSTRUMENT_SHORT = {"no_fall_detection": "blind", "posture_gate_v1": "v1", "posture_gate_v2": "v2"}
DIAL_ORDER = ("track_lin_vel_xy_exp", "feet_air_time", "lin_vel_z_l2",
              "ang_vel_xy_l2", "action_rate_l2", "flat_orientation_l2")


def chronology_page(records: list[dict[str, Any]]) -> str:
    """종합 보고서가 인용하는 연대표. 손으로 옮겨 적지 않도록 여기서 만든다."""
    lines = [
        "# Go2 연대표 — 학습 설정 · 커리큘럼 · 재채점 점수",
        "",
        "`tools/build_go2_run_reports.py`가 산출물에서 생성한다. 사람이 고치지 않는다.",
        "`terrain`은 `terrain_levels_vel` 도달 레벨(만점 10)이고 **이동 거리로 승급**한다.",
        "`계측`: `blind` 낙상 미검출 · `v1` 자세 낙상 검출 · `v2` 검출 + 측정 계약. "
        "`a/b`는 두 arm을 다른 세대로 잰 회차다.",
        "",
        "| # | 날짜 | 회차 | trk / air / lin_z / ang / a_rate / flat | terrain@999 | trk@999 | 낙상@999 | 재채점 70점 | case | 계측 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, record in enumerate(records, 1):
        rewards = record.get("rewards", {})
        source = record.get("training") or record.get("training_tfevents") or {}
        curve = (source.get("curve") or {}).get("999", {})
        arms = record.get("arms", {})
        full = {name: body for name, body in arms.items() if body["observed_cases"] == 69}
        if len(full) > 1:
            score = " / ".join(f"**{b['total_70']:.3f}**({n})" for n, b in full.items())
        elif full:
            score = f"**{next(iter(full.values()))['total_70']:.3f}**"
        else:
            score = "—"
        cases = "69" if full else (str(max((b["observed_cases"] or 0) for b in arms.values())) if arms else "—")
        generations = sorted({INSTRUMENT_SHORT.get(b["instrument"], "?") for b in arms.values()})
        note = (" **(재현)**" if record.get("replicate_of")
                else ("  *(텍스트 로그 없음·tfevents)*" if record.get("training_tfevents")
                      else ("  *(학습 로그 미회수)*" if record.get("training_log_missing") else "")))
        dial = " / ".join(fmt(rewards.get(k)) for k in DIAL_ORDER) if rewards else "—"
        fall = "—" if curve.get("base_contact") is None else f"{curve['base_contact'] * 100:.1f}%"
        lines.append(
            f"| {i:02d} | {(occurred(record) or '—')[5:10]} | {record['run'].replace('go2_', '')}{note} "
            f"| {dial} | {fmt(curve.get('terrain'))} | {fmt(curve.get('track_lin_vel'))} | {fall} "
            f"| {score} | {cases} | {'/'.join(generations) or '—'} |")
    lines += ["", "부분 평가(7·10 case)의 재채점 70점은 비웠다 — 빠진 시나리오가 0점으로 합산되어 "
              "전수 평가와 같은 축이 아니다. 그 회차의 판정이 실제로 쓴 숫자는 회차 보고서에 있다.", ""]
    return "\n".join(lines)


def terrain_rows(records: list[dict[str, Any]]) -> list[list[str]]:
    """회차 × 핀 iteration의 도달 지형 레벨.

    문서가 "도달 3.38~4.50"처럼 소수 2자리로 적던 값이다.  2자리는 존재 게이트의 맹점이라
    (무작위 숫자 55% 통과) 틀려도 잡히지 않았다 — 실제로 A017 @900은 3.4268이었다.
    """
    # 두 정의를 같이 낸다.  계획 문서는 "iter 891~900 평균"을 썼고 재평가 빌더는 단일값을
    # 쓴다.  하나만 내면 다른 정의로 적힌 값을 틀렸다고 판정하게 된다 — 2026-09-16에 내가 그랬다.
    rows = [["run", "iteration", "terrain", "terrain_mean_last10"]]
    for record in records:
        log = record.get("training", {}).get("log")
        if not log:
            continue
        for iteration in PIN_ITERATIONS:
            value = terrain_at(ROOT / log, iteration)
            if value is None:
                continue
            window = [terrain_at(ROOT / log, i) for i in range(iteration - 9, iteration + 1)]
            mean = (f"{sum(window) / len(window):.4f}"
                    if all(v is not None for v in window) else "")
            rows.append([record["run"], str(iteration), f"{value:.4f}", mean])
    return rows


def main() -> int:
    records = harvest()
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.md"):
        stale.unlink()
    for i, record in enumerate(records, 1):
        (OUT / f"{i:02d}_{record['run']}.md").write_text(render(i, record), encoding="utf-8")
    (OUT / "INDEX.md").write_text(index_page(records), encoding="utf-8")
    (OUT / "CHRONOLOGY.md").write_text(chronology_page(records), encoding="utf-8")
    with (OUT / "LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(csv_rows(records))
    with (OUT / "SCENARIO_SCORES.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(scenario_rows(records))
    with (OUT / "ARM_DELTAS.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(delta_rows(records))
    with (OUT / "TERRAIN_AT_PIN.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(terrain_rows(records))
    print(f"{len(records)} 회차 -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
