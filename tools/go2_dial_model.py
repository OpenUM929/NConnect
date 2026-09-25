"""reward 다이얼 → 커리큘럼 도달(`terrain@999`) 모델.

왜 이 출력변수인가. 70점 축은 계측 세대가 세 번 바뀌어 전수 평가가 3건뿐이다(종합 §4·§5).
반면 학습 로그의 `Curriculum/terrain_levels`는 **17회 전부 같은 형식·같은 계측**으로 남아 있고,
학습 실행 인자도 전부 같다 — `--num_envs 4096 --max_iterations 1000 --seed 42`, resume 없음.
즉 이미 설계된 실험이 있었고, 다른 것은 reward 벡터 하나뿐이다.

모델은 두 줄이다.
  1. `ang_vel_xy_l2 <= -0.15` 이면 커리큘럼이 출발하지 못한다 (관측 2/2, 오차 0.0000).
  2. 그 밖에는 `track_lin_vel_xy_exp`의 수준평균. 1.2와 1.4 사이에 문턱이 있어 선형이 아니다.

교차검증(leave-one-out)으로만 성능을 말한다. 표본 안 r²는 n=15에서 의미가 없다 —
지난번에 r² 0.935를 예측력으로 인용했다가 유일한 성공 A017을 실패로 예측하는 모델을 믿을 뻔했다.

    python tools/go2_dial_model.py            # 설계·교차검증·규칙
    python tools/go2_dial_model.py 1.4 0.2    # track·feet_air를 주고 예측
"""
from __future__ import annotations

import csv
import statistics as st
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from go2_run_ledger import harvest  # noqa: E402

DIALS = ("track_lin_vel_xy_exp", "feet_air_time", "lin_vel_z_l2",
         "ang_vel_xy_l2", "action_rate_l2", "flat_orientation_l2")
KILL_DIAL = "ang_vel_xy_l2"
KILL_AT = -0.15
DRIVER = "track_lin_vel_xy_exp"
# 모델을 세운 뒤 들어온 표본 중 모델을 반박한 것.  여기 적힌 회차는 모델 적합·교차검증에서 빼고
# (09-16 종합이 인용한 15회차 수치를 그대로 재현하기 위해), 그 모델로 예측한 오차를 따로 기록한다.
# G-A038: track 1.5 그대로 ang_vel_xy만 -0.05 -> -0.08(사망 규칙 밖)인데 terrain@999가 G-A033보다
# 크게 낮다 — "살아 있는 회차는 track 수준이 정한다"는 규칙 2가 틀렸다.
REFUTING_RUNS = ("g_a038_a033_ang_vel_xy_m008",)
MODEL_STATUS = "REFUTED_BY_G_A038"   # 예측 근거로 쓰지 않는다


def design(records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """고유 학습 회차의 (reward 벡터, terrain@999). 재현 회차는 한 번만 센다."""
    rows = []
    for record in records if records is not None else harvest():
        training, rewards = record.get("training"), record.get("rewards")
        if not training or not rewards or record.get("replicate_of"):
            continue
        last = (training.get("curve") or {}).get("999", {})
        if last.get("terrain") is None:
            continue
        rows.append({
            "run": record["run"].replace("go2_", ""),
            "dials": {k: rewards.get(k) for k in DIALS},
            "terrain": last["terrain"],
            "track_lin_vel": last.get("track_lin_vel"),
            "base_contact": last.get("base_contact"),
        })
    return rows


def fit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """사망 규칙과 구동 다이얼 수준평균을 표본에서 읽는다."""
    dead = [r["terrain"] for r in rows if r["dials"][KILL_DIAL] <= KILL_AT]
    alive = [r for r in rows if r["dials"][KILL_DIAL] > KILL_AT]
    levels: dict[float, list[float]] = {}
    for row in alive:
        levels.setdefault(row["dials"][DRIVER], []).append(row["terrain"])
    return {
        "dead_mean": st.mean(dead) if dead else 0.0,
        "dead_n": len(dead),
        "levels": {k: {"mean": st.mean(v), "n": len(v), "min": min(v), "max": max(v)}
                   for k, v in sorted(levels.items())},
        "alive_mean": st.mean(r["terrain"] for r in alive) if alive else 0.0,
    }


def predict(model: dict[str, Any], dials: dict[str, float]) -> tuple[float, str]:
    """(예측값, 지지 근거). 지지 없는 수준은 그렇게 말한다."""
    if dials.get(KILL_DIAL) is not None and dials[KILL_DIAL] <= KILL_AT:
        return model["dead_mean"], f"사망 규칙 ({KILL_DIAL} <= {KILL_AT}), 관측 {model['dead_n']}건"
    level = model["levels"].get(dials.get(DRIVER))
    if level:
        return level["mean"], f"{DRIVER}={dials.get(DRIVER)} 수준평균, 관측 {level['n']}건"
    return model["alive_mean"], f"**지지 없음** — {DRIVER}={dials.get(DRIVER)}는 관측된 적 없는 수준이다"


def _linear(train: list[dict[str, Any]], held: dict[str, Any]) -> float:
    """대안 A: `track`에 직선 하나. '문턱이 아니라 기울기'라는 반대 가설이다."""
    xs = [r["dials"][DRIVER] for r in train]
    ys = [r["terrain"] for r in train]
    mx, my = st.mean(xs), st.mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom if denom else 0.0
    return my + slope * (held["dials"][DRIVER] - mx)


def _levels_only(train: list[dict[str, Any]], held: dict[str, Any]) -> float:
    """대안 B: 사망 규칙 없이 `track` 수준평균만. 사망 규칙의 기여를 분리한다."""
    groups: dict[float, list[float]] = {}
    for row in train:
        groups.setdefault(row["dials"][DRIVER], []).append(row["terrain"])
    bucket = groups.get(held["dials"][DRIVER])
    return st.mean(bucket) if bucket else st.mean(r["terrain"] for r in train)


def cross_validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """leave-one-out. 대조군은 '나머지의 평균으로 찍기'다.

    대안 모델 둘을 같은 LOO로 함께 잰다.  §11-3의 '문턱이지 기울기가 아니다'는
    주장이 선형 모델과의 비교에 통째로 기대고 있는데, 그 숫자를 만드는 코드가
    없어서 내가 손으로 계산해 적어두고 있었다.  여기서 만든다.
    """
    detail, errors, baseline_errors, unsupported = [], [], [], []
    linear_errors, levels_errors = [], []
    for i, held in enumerate(rows):
        train = [r for j, r in enumerate(rows) if j != i]
        yhat, basis = predict(fit(train), held["dials"])
        error = held["terrain"] - yhat
        errors.append(abs(error))
        linear_errors.append(abs(held["terrain"] - _linear(train, held)))
        levels_errors.append(abs(held["terrain"] - _levels_only(train, held)))
        baseline_errors.append(abs(held["terrain"] - st.mean(r["terrain"] for r in train)))
        if "지지 없음" in basis:
            unsupported.append(held["run"])
        detail.append({"run": held["run"], "actual": held["terrain"],
                       "predicted": yhat, "error": error, "basis": basis})
    supported = [d for d in detail if d["run"] not in unsupported]
    return {
        "n": len(rows),
        "mae": st.mean(errors),
        "mae_supported": st.mean(abs(d["error"]) for d in supported) if supported else None,
        "mae_baseline": st.mean(baseline_errors),
        "mae_linear": st.mean(linear_errors),
        "mae_levels_only": st.mean(levels_errors),
        "unsupported": unsupported,
        "detail": detail,
    }


def split(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(모델을 세운 표본, 모델을 반박한 표본)."""
    return ([r for r in rows if r["run"] not in REFUTING_RUNS],
            [r for r in rows if r["run"] in REFUTING_RUNS])


def refutation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """모델을 세운 표본으로 적합한 모델이 반박 회차를 얼마나 틀렸나."""
    built, refuting = split(rows)
    model = fit(built)
    out = []
    for held in refuting:
        yhat, basis = predict(model, held["dials"])
        out.append({"run": held["run"], "actual": held["terrain"], "predicted": yhat,
                    "error": held["terrain"] - yhat, "basis": basis})
    return out


def main() -> int:
    all_rows = design()
    rows, _refuting = split(all_rows)
    model, cv = fit(rows), cross_validate(rows)
    cv_all = cross_validate(all_rows)
    print(f"모델 상태: {MODEL_STATUS} — 예측 근거로 쓰지 않는다 (아래 '반박' 절)\n")

    print(f"고유 학습 {len(rows)}건 — 실행 인자 동일(4096 env / 1000 iter / seed 42 / resume 없음)\n")
    print("== 교차검증 (leave-one-out) ==")
    print(f"  평균으로 찍기        MAE {cv['mae_baseline']:.4f}")
    print(f"  track 선형           MAE {cv['mae_linear']:.4f}")
    print(f"  track 수준평균만     MAE {cv['mae_levels_only']:.4f}")
    print(f"  이 모델              MAE {cv['mae']:.4f}   "
          f"({100 * (1 - cv['mae'] / cv['mae_baseline']):.0f}% 감소)")
    print(f"  지지 구간 안         MAE {cv['mae_supported']:.4f}  "
          f"(지지 없는 회차 제외: {', '.join(cv['unsupported']) or '없음'})")

    print(f"\n== 규칙 1: {KILL_DIAL} <= {KILL_AT} 이면 커리큘럼 미출발 ==")
    print(f"  관측 {model['dead_n']}건, terrain 평균 {model['dead_mean']:.4f}")

    print(f"\n== 규칙 2: {DRIVER} 수준평균 ==")
    for value, body in model["levels"].items():
        print(f"  {value:>4} : n={body['n']}  평균 {body['mean']:.4f}  "
              f"범위 [{body['min']:.4f}, {body['max']:.4f}]" + ("   ← 지지 1건" if body["n"] == 1 else ""))

    print("\n== 회차별 ==")
    for d in cv["detail"]:
        print(f"  {d['run'][:38]:38s} 실제 {d['actual']:7.4f}  예측 {d['predicted']:7.4f}  "
              f"오차 {d['error']:+7.4f}   {d['basis']}")

    # 화면 출력만 두면 §11의 숫자는 필사본이 된다. 파일로 내보내 `go2_claim_check`가 읽게 한다.
    out_rows = [["metric", "key", "value"],
                ["loo_mae_baseline", "ALL", f"{cv['mae_baseline']:.4f}"],
                ["loo_mae_linear", "ALL", f"{cv['mae_linear']:.4f}"],
                ["loo_mae_levels_only", "ALL", f"{cv['mae_levels_only']:.4f}"],
                ["loo_mae_model", "ALL", f"{cv['mae']:.4f}"],
                ["loo_mae_supported", "ALL", f"{cv['mae_supported']:.4f}"],
                ["dead_mean", KILL_DIAL, f"{model['dead_mean']:.4f}"]]
    for value, body in model["levels"].items():
        out_rows += [["level_mean", f"{DRIVER}={value}", f"{body['mean']:.4f}"],
                     ["level_min", f"{DRIVER}={value}", f"{body['min']:.4f}"],
                     ["level_max", f"{DRIVER}={value}", f"{body['max']:.4f}"]]
    for d in cv["detail"]:
        out_rows += [["loo_actual", d["run"], f"{d['actual']:.4f}"],
                     ["loo_predicted", d["run"], f"{d['predicted']:.4f}"],
                     ["loo_error", d["run"], f"{d['error']:+.4f}"]]
    print("\n== 반박 (모델을 세운 뒤 들어온 표본) ==")
    for d in refutation(all_rows):
        print(f"  {d['run'][:38]:38s} 실제 {d['actual']:7.4f}  예측 {d['predicted']:7.4f}  "
              f"오차 {d['error']:+7.4f}   {d['basis']}")
        out_rows += [["refuting_actual", d["run"], f"{d['actual']:.4f}"],
                     ["refuting_predicted", d["run"], f"{d['predicted']:.4f}"],
                     ["refuting_error", d["run"], f"{d['error']:+.4f}"]]
    print(f"  반박 표본을 넣은 교차검증 MAE {cv_all['mae']:.4f} (지지 구간 {cv_all['mae_supported']:.4f})")
    out_rows += [["loo_mae_model_with_refuting", "ALL", f"{cv_all['mae']:.4f}"],
                 ["loo_mae_supported_with_refuting", "ALL", f"{cv_all['mae_supported']:.4f}"]]
    # 상태(MODEL_STATUS)는 CSV에 넣지 않는다 — 이 표의 value 칸은 숫자만 읽힌다(go2_table_audit).
    out_csv = ROOT / "workspace/training/quadruped/reports/runs/DIAL_MODEL.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(out_rows)
    print(f"\n-> {out_csv.relative_to(ROOT)}")

    if len(sys.argv) > 1:
        dials = dict(zip((DRIVER, "feet_air_time"), (float(a) for a in sys.argv[1:])))
        dials.setdefault(KILL_DIAL, -0.05)
        value, basis = predict(model, dials)
        print(f"\n== 예측 ({MODEL_STATUS}: 참고용, 근거로 쓰지 않는다) ==\n  {dials}\n  terrain@999 = {value:.4f} ± {cv['mae_supported']:.4f}\n  근거: {basis}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
