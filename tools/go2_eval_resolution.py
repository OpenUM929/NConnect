"""70점 축의 계측 해상도 추정 (서버 0시간, 회수본만 사용).

생존 proxy는 로봇 n대 중 넘어지지 않은 비율이다. 그래서 이항 표집 오차를 갖는다.
추종 proxy는 case-seed당 집계값만 남아 있어 재표집할 수 없다. 고정으로 둔다.
따라서 아래 값은 계측 흔들림의 **하한**이다.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

QUAD = Path("C:/dev/Nconnect/workspace/training/quadruped")
sys.path.insert(0, str(QUAD))
from go2_fixed_eval_report import _case_proxy  # noqa: E402

REGISTRY = json.loads((QUAD / "config/go2_self_eval_registry.json").read_text(encoding="utf-8"))
STD = float(REGISTRY["score"].get("tracking_proxy_std", 0.5))
SEEDS = [int(s) for s in REGISTRY["score"]["internal_gates"]["required_evaluation_seeds"]]

ARMS = {
    "A017": Path("C:/dev/Nconnect/workspace/_keep/go2_a017_full_suite/evaluation/a017"),
    "G-A033": Path("C:/dev/Nconnect/workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate"),
}


def load(root: Path):
    """[(scenario_id, weight, case_id, seed, survival, tracking, n_envs)] 을 돌려준다."""
    items = []
    for scenario in REGISTRY["scenarios"]:
        sid, weight = scenario["id"], float(scenario["weight"])
        for case_id in scenario["internal_cases"]:
            for seed in SEEDS:
                path = root / "cases" / f"seed_{seed}" / case_id / "summary.json"
                if not path.exists():
                    continue
                summary = json.loads(path.read_text(encoding="utf-8"))
                proxy = _case_proxy(case_id, summary, STD)
                if proxy["scenario_proxy"] is None:
                    continue
                n = int(summary.get("posture_envs_observed") or 0)
                surv = float(proxy["survival_proxy"])
                track = float(proxy["tracking_proxy"])
                # 생존 = (n - 넘어진 수)/n 인지 확인한다. 어긋나면 재표집 대상에서 뺀다.
                fallen = summary.get("posture_fall_env_count_pessimistic")
                ok = n > 0 and fallen is not None and abs(surv - (n - int(fallen)) / n) < 1e-9
                items.append((sid, weight, case_id, seed, surv, track, n if ok else 0))
    return items


def score(items, survivals) -> tuple[float, dict[str, float]]:
    per = {}
    for (sid, weight, _c, _s, _surv, track, _n), surv in zip(items, survivals):
        value = surv * track
        if sid not in per or value < per[sid][1]:
            per[sid] = (weight, value)
    total = sum(w * v for w, v in per.values()) * 70.0
    return total, {sid: w * v * 70.0 for sid, (w, v) in per.items()}


def main() -> int:
    rng = np.random.default_rng(20260916)
    boots = 4000
    out = {}
    for name, root in ARMS.items():
        items = load(root)
        base_surv = np.array([it[4] for it in items])
        n_env = np.array([it[6] for it in items])
        observed, per_obs = score(items, base_surv)

        draws = np.empty((boots, len(items)))
        for j, (surv, n) in enumerate(zip(base_surv, n_env)):
            draws[:, j] = surv if n == 0 else rng.binomial(n, surv, boots) / n
        totals = np.array([score(items, draws[b])[0] for b in range(boots)])
        per_rows = {}
        for b in range(boots):
            for sid, val in score(items, draws[b])[1].items():
                per_rows.setdefault(sid, []).append(val)

        out[name] = {
            "observed": observed,
            "totals": totals,
            "per_obs": per_obs,
            "per_sd": {sid: float(np.std(v, ddof=1)) for sid, v in per_rows.items()},
            "n_items": len(items),
            "n_resampled": int((n_env > 0).sum()),
        }
        print(f"== {name}: case-seed {len(items)}건, 재표집 가능 {int((n_env > 0).sum())}건")
        print(f"   관측 총점 {observed:.3f}/70   재표집 평균 {totals.mean():.3f}   표준편차 {totals.std(ddof=1):.3f}")
        lo, hi = np.percentile(totals, [2.5, 97.5])
        print(f"   95% 구간 [{lo:.3f}, {hi:.3f}]  폭 {hi - lo:.3f}")

    a, b = out["A017"], out["G-A033"]
    delta = b["totals"] - a["totals"]  # 두 arm은 독립 표집이다
    print("\n== 차이 (G-A033 − A017)")
    print(f"   관측 {b['observed'] - a['observed']:+.3f}/70   재표집 표준편차 {delta.std(ddof=1):.3f}")
    lo, hi = np.percentile(delta, [2.5, 97.5])
    print(f"   95% 구간 [{lo:+.3f}, {hi:+.3f}]")

    print("\n== 시나리오별 가중 점수의 표준편차 (하한) 과 §6-1 3항 한도 0.5/70")
    print(f"{'시나리오':<8}{'A017 관측':>10}{'A017 sd':>9}{'A033 관측':>10}{'A033 sd':>9}{'손실 sd':>9}")
    worst = {}
    for sid in sorted(a["per_obs"]):
        sd_pair = (a["per_sd"][sid] ** 2 + b["per_sd"][sid] ** 2) ** 0.5
        worst[sid] = sd_pair
        print(f"{sid:<8}{a['per_obs'][sid]:>10.3f}{a['per_sd'][sid]:>9.3f}"
              f"{b['per_obs'][sid]:>10.3f}{b['per_sd'][sid]:>9.3f}{sd_pair:>9.3f}")

    # (b) 검출 가능한 최소 효과와, 한도를 재려면 필요한 로봇 수.
    # 이항 오차는 1/sqrt(n)로 줄어든다. 현재 n=32.
    n_now = 32
    limit = 0.5  # §6-1 3항 한도(/70)
    sd_worst = max(worst.values())
    print("\n== (b) 검출력")
    print(f"   총점 차이의 표준편차 {delta.std(ddof=1):.3f}/70 → 2sigma 검출 한계 {2 * delta.std(ddof=1):.3f}/70")
    print(f"   가장 나쁜 시나리오 손실의 표준편차 {sd_worst:.3f}/70 (한도 {limit}/70)")
    need = n_now * (sd_worst / (limit / 2.0)) ** 2
    print(f"   한도를 2sigma로 재려면 case-seed당 로봇 {n_now} -> 약 {int(round(need / 32) * 32)}대 필요")
    for mult in (4, 8, 16):
        print(f"     로봇 {n_now * mult}대: 손실 sd {sd_worst / mult ** 0.5:.3f}/70, "
              f"총점 차이 sd {delta.std(ddof=1) / mult ** 0.5:.3f}/70")

    # 화면에만 찍으면 내가 손으로 옮겨 적게 되고, 옮겨 적은 숫자는 검증되지 않는다.
    # §7의 승급 근거가 전부 이 표에서 나오므로 파일로 내보낸다. `go2_claim_check`가 읽는다.
    rows = [["metric", "scenario", "value"]]
    for sid in sorted(a["per_obs"]):
        sd_pair = (a["per_sd"][sid] ** 2 + b["per_sd"][sid] ** 2) ** 0.5
        rows += [["a017_observed", sid, f"{a['per_obs'][sid]:.5f}"],
                 ["a033_observed", sid, f"{b['per_obs'][sid]:.5f}"],
                 ["delta_observed", sid, f"{b['per_obs'][sid] - a['per_obs'][sid]:+.5f}"],
                 ["delta_resample_sd", sid, f"{sd_pair:.5f}"]]
    d_lo, d_hi = np.percentile(delta, [2.5, 97.5])
    rows += [["delta_total_observed", "ALL", f"{b['observed'] - a['observed']:+.5f}"],
             ["delta_total_resample_sd", "ALL", f"{delta.std(ddof=1):.5f}"],
             ["delta_total_ci95_lo", "ALL", f"{d_lo:+.5f}"],
             ["delta_total_ci95_hi", "ALL", f"{d_hi:+.5f}"],
             ["detect_limit_2sigma", "ALL", f"{2 * delta.std(ddof=1):.5f}"]]
    out_csv = QUAD / "reports/runs/BASELINE_MARGIN.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    print(f"\n-> {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
