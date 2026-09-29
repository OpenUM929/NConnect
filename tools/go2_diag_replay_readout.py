"""G-A052 진단 재생 판독 (2026-09-28).  정의는 결과 전에 upload/plan/GO2_G_A052_DIAG_REPLAY_PLAN_20260928.md §4에 고정했다.

변수를 고르지 않는다.  사건마다 '무엇이 먼저 나타났나'를 네 값 중 하나로 적고, 같은 재생의 생존 로봇과 비교할 뿐이다.

입력: 결과 폴더(go2_g_a052_a048_diag_replay/)의 diag/cases/seed_<s>/<case>/{steps.csv, diag.csv.gz, diag_meta.json}.
사건 선택은 1단계와 같은 판정(tools/go2_failure_events.py 의 classify·event_row)을 이 재생의 steps.csv 에 적용한다.

기준 시각 T
  tilt_first     proj_grav_z 가 −0.95 를 마지막으로 넘은 시각(1단계 grav_095_cross_t)
  height_first   첫 자세 불량 시각(height_rel < 0.18)
  그 밖          첫 자세 불량 시각, 없으면 종료 직전 행
창: [T − 1.0 s, T).

같은 재생 생존 로봇으로 정하는 기준(분석 편의값, 문턱 아님 — 재생마다 다시 계산하고 CALIBRATION.json 에 남긴다)
  R  |ω_xy| = sqrt(ang_vel_b_x² + ang_vel_b_y²)의 생존 로봇 p95
  S  지지 중(contact_time > 0) 발 수평 속도의 생존 로봇 p95
  D  지지 발 수 ≤ 1 인 연속 구간 길이의 생존 로봇 p95
창 안의 시작 시각
  t_rot      |ω_xy| > R 가 3행(0.06 s) 이상 이어진 첫 구간의 시작
  t_slip     지지 중 발 수평 속도 > S 가 2행 이상 이어진 첫 구간의 시작(어느 발인지 기록)
  t_support  지지 발 수 ≤ 1 구간이 D 보다 길어진 첫 구간의 시작
  t_contact  min(t_slip, t_support)
판정 order: rotation_first(t_rot < t_contact − 0.04) / contact_first(t_contact < t_rot − 0.04) /
            simultaneous(차이 ≤ 0.04) / rotation_only / contact_only / not_observed / unknown(채널 결측).
유효성(2026-09-28 Codex 검토로 추가): 회전은 |ω_xy| 가 창 전 행에 있어야, 접촉 변화는 창 전 행에서 네 발 접촉 시간·발 속도가
  있고 contact_fresh = 1(센서 버퍼가 그 step에 갱신됨)이어야 잰다.  결측은 0 지지로 세지 않는다.  비교에 필요한 한쪽이라도
  유효하지 않으면 order = unknown 이고, 회전 쪽 관측(rotation_valid·t_rot·omega_xy_max)은 따로 남긴다.
계단 보조(파생): high_terrain_near_stopped_stance_foot_derived_t — 지지 중인 발의 수평 속도 < 0.05 이고
  terrain_zmax015_derived − 발 z > 0.04(발 주변 15 cm 안에 발보다 4 cm 이상 높은 면)인 행의 첫 시각.
  주변 높은 지형과 멈춘 지지 발의 조합일 뿐 단 모서리 충돌의 증거가 아니다.

    python -B tools/go2_diag_replay_readout.py <harvest_dir> [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import go2_failure_events as fe  # noqa: E402

WINDOW_S, DT, GAP_S = 1.0, 0.02, 0.04
ROT_ROWS, SLIP_ROWS = 3, 2
RISER_SPEED, RISER_DZ = 0.05, 0.04
CASES = (("rough_lateral", 202), ("stairs_10_down", 101), ("stairs_15_down", 101))
DEFAULT_OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a052_diag_20260928"


def _f(v: str) -> float | None:
    if v in ("", None):
        return None
    x = float(v)
    return x if math.isfinite(x) else None


def load_diag(path: Path) -> tuple[list[str], dict[int, list[dict]]]:
    envs: dict[int, list[dict]] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        for row in reader:
            envs.setdefault(int(row["env_id"]), []).append({k: _f(v) for k, v in row.items()})
    return fields, envs


def feet_of(fields: list[str]) -> list[str]:
    return [f[: -len("_contact_time")] for f in fields if f.endswith("_contact_time")]


def omega_xy(d: dict) -> float | None:
    x, y = d.get("ang_vel_b_x"), d.get("ang_vel_b_y")
    return None if x is None or y is None else math.hypot(x, y)


def contact_ok(d: dict, feet: list[str]) -> bool:
    """이 행의 접촉 채널이 쓸 수 있나: 네 발 접촉 시간이 모두 있고, 센서 버퍼가 이 step에 갱신됐다(contact_fresh=1)."""
    return bool(feet) and d.get("contact_fresh") == 1.0 and all(d.get(f"{f}_contact_time") is not None for f in feet)


def slip_ok(d: dict, feet: list[str]) -> bool:
    return contact_ok(d, feet) and all(d.get(f"{f}_vel_x") is not None and d.get(f"{f}_vel_y") is not None
                                       for f in feet)


def stance_speeds(d: dict, feet: list[str]) -> list[tuple[str, float]]:
    """지지 중 발의 수평 속도.  slip_ok 인 행에서만 부른다."""
    return [(f, math.hypot(d[f"{f}_vel_x"], d[f"{f}_vel_y"])) for f in feet if d[f"{f}_contact_time"] > 0]


def support(d: dict, feet: list[str]) -> int | None:
    """지지 발 수.  접촉 채널을 쓸 수 없으면 None — 0 과 다르다."""
    return sum(1 for f in feet if d[f"{f}_contact_time"] > 0) if contact_ok(d, feet) else None


def p95(values: list[float]) -> float | None:
    v = sorted(values)
    return v[min(len(v) - 1, int(0.95 * len(v)))] if v else None


def calibrate(diag: dict[int, list[dict]], episodes: dict[int, int], survivors: list[int], feet: list[str]) -> dict:
    """생존 로봇의 유효 행만 쓴다.  결측 행은 지지 구간을 끊는다(0 으로 세지 않는다)."""
    om, sp, runs = [], [], []
    rows_total = rows_contact = 0
    for e in survivors:
        cur = 0
        for i, d in enumerate(diag[e][: episodes[e]]):
            if (i + 1) * DT < fe.GRACE_S:
                continue
            rows_total += 1
            w = omega_xy(d)
            if w is not None:
                om.append(w)
            if slip_ok(d, feet):
                sp += [s for _, s in stance_speeds(d, feet)]
            n = support(d, feet)
            if n is not None:
                rows_contact += 1
            if n is not None and n <= 1:
                cur += 1
            else:
                if cur:
                    runs.append(cur * DT)
                cur = 0
        if cur:
            runs.append(cur * DT)
    return {"R_omega_xy_p95": p95(om), "S_stance_speed_p95": p95(sp), "D_low_support_run_p95_s": p95(runs),
            "survivors": len(survivors), "rows_total": rows_total, "rows_omega": len(om),
            "rows_contact_valid": rows_contact, "rows_stance": len(sp), "low_support_runs": len(runs)}


def first_run(flags: list[bool], min_rows: int) -> int | None:
    cur = 0
    for i, f in enumerate(flags):
        cur = cur + 1 if f else 0
        if cur >= min_rows:
            return i - min_rows + 1
    return None


def window_readout(rows: list[dict], lo: int, hi: int, feet: list[str], cal: dict) -> dict:
    """회전과 접촉 변화를 각각 유효할 때만 잰다.  비교에 필요한 한쪽이라도 결측이면 order 는 unknown 이다.
    회전 쪽은 접촉이 결측이어도 rotation_* 필드에 남긴다(관측한 것은 버리지 않는다)."""
    win = rows[lo:hi]
    t0 = (lo + 1) * DT
    t = lambda i: None if i is None else round(t0 + i * DT, 3)  # noqa: E731
    out: dict = {"window_rows": len(win)}
    om = [omega_xy(d) for d in win]
    rot_reason = ("empty_window" if not win else "calibration_missing" if cal["R_omega_xy_p95"] is None
                  else "omega_missing" if any(w is None for w in om) else "")
    i_rot = None if rot_reason else first_run([w > cal["R_omega_xy_p95"] for w in om], ROT_ROWS)
    out.update(rotation_valid=int(not rot_reason), rotation_invalid_reason=rot_reason, t_rot=t(i_rot),
               omega_xy_max=None if rot_reason else round(max(om), 4))
    stale = sum(1 for d in win if d.get("contact_fresh") != 1.0)
    missing = sum(1 for d in win if not slip_ok(d, feet)) - stale
    con_reason = ("empty_window" if not win else "no_feet_columns" if not feet
                  else "contact_stale" if stale else "contact_or_foot_velocity_missing" if missing > 0
                  else "calibration_missing" if cal["S_stance_speed_p95"] is None or cal["D_low_support_run_p95_s"] is None
                  else "")
    out.update(contact_valid=int(not con_reason), contact_invalid_reason=con_reason,
               contact_stale_rows=stale, t_slip=None, slip_foot="", t_support=None, t_contact=None, mean_support=None)
    i_con = None
    if not con_reason:
        i_slip, slip_foot = None, ""
        for f in feet:
            flags = [dict(stance_speeds(d, feet)).get(f, 0.0) > cal["S_stance_speed_p95"] for d in win]
            j = first_run(flags, SLIP_ROWS)
            if j is not None and (i_slip is None or j < i_slip):
                i_slip, slip_foot = j, f
        need = int(round(cal["D_low_support_run_p95_s"] / DT)) + 1
        i_sup = first_run([support(d, feet) <= 1 for d in win], need)
        cands = [i for i in (i_slip, i_sup) if i is not None]
        i_con = min(cands) if cands else None
        out.update(t_slip=t(i_slip), slip_foot=slip_foot, t_support=t(i_sup), t_contact=t(i_con),
                   mean_support=round(statistics.fmean(support(d, feet) for d in win), 3))
    if rot_reason or con_reason:
        order = "unknown"
    elif i_rot is None and i_con is None:
        order = "not_observed"
    elif i_con is None:
        order = "rotation_only"
    elif i_rot is None:
        order = "contact_only"
    elif (i_con - i_rot) * DT > GAP_S:
        order = "rotation_first"
    elif (i_rot - i_con) * DT > GAP_S:
        order = "contact_first"
    else:
        order = "simultaneous"
    out["order"] = order
    # 0.1 s 칸의 발별 접촉 순서(1=지지, 0=공중, ?=결측·낡은 버퍼): 어느 발이 언제 떨어졌는지
    for f in feet:
        bins = []
        for b in range(0, len(win), 5):
            chunk = win[b:b + 5]
            bins.append("?" if any(not contact_ok(d, feet) for d in chunk)
                        else ("1" if sum(d[f"{f}_contact_time"] > 0 for d in chunk) >= 3 else "0"))
        out[f"{f}_contact_bins"] = "".join(bins)
    act = [d for d in win if d.get("action_0") is not None and d.get("prev_action_0") is not None]
    if act:
        n = sum(1 for k in act[0] if k.startswith("action_"))
        out["action_rate_mean"] = round(statistics.fmean(
            math.sqrt(sum((d[f"action_{i}"] - d[f"prev_action_{i}"]) ** 2 for i in range(n))) for d in act), 4)
    # 주변 높은 지형 + 멈춘 지지 발의 조합.  모서리 충돌의 증거가 아니다.
    riser = None
    if not con_reason:
        riser = next((i for i, d in enumerate(win) for f in feet
                      if d[f"{f}_contact_time"] > 0
                      and math.hypot(d[f"{f}_vel_x"], d[f"{f}_vel_y"]) < RISER_SPEED
                      and d.get(f"{f}_terrain_zmax015_derived") is not None and d.get(f"{f}_pos_z") is not None
                      and d[f"{f}_terrain_zmax015_derived"] - d[f"{f}_pos_z"] > RISER_DZ), None)
    out["high_terrain_near_stopped_stance_foot_derived_t"] = t(riser)
    return out


def reward_means(rows: list[dict], lo: int, hi: int) -> dict:
    win = rows[lo:hi]
    keys = [k for k in (win[0] if win else {}) if k.startswith("rew_")]
    return {k: round(statistics.fmean(d[k] for d in win if d[k] is not None), 5) for k in keys
            if any(d[k] is not None for d in win)}


def read_case(case_dir: Path, case: str, seed: int) -> tuple[list[dict], dict, dict]:
    envs = fe.load(case_dir / "steps.csv")
    fields, diag = load_diag(case_dir / "diag.csv.gz")
    feet = feet_of(fields)
    meta = json.loads((case_dir / "diag_meta.json").read_text(encoding="utf-8"))
    rows, episodes, outcome = {}, {}, {}
    for env, steps in sorted(envs.items()):
        c = fe.classify(steps)
        rows[env] = fe.event_row("G-A052-diag", seed, env, steps, c)
        rows[env].pop("_episode", None)
        episodes[env] = rows[env]["valid_rows"]
        outcome[env] = rows[env]["outcome"]
    survivors = [e for e, o in outcome.items() if o == "SURVIVE"]
    cal = calibrate(diag, episodes, survivors, feet)
    fall_t = []
    events = []
    for env, r in rows.items():
        if r["outcome"] != "FALL":
            continue
        if r["event_order"] == "tilt_first" and r.get("grav_095_cross_t") is not None:
            T, anchor = r["grav_095_cross_t"], "grav_-0.95_last_cross"
        elif r.get("first_bad_t") is not None:
            T, anchor = r["first_bad_t"], "first_posture_bad"
        else:
            T, anchor = (episodes[env]) * DT, "last_row_before_termination"
        hi = int(round(T / DT)) - 1
        lo = max(0, hi - int(round(WINDOW_S / DT)))
        fall_t.append(T)
        ev = {"case": case, "eval_seed": seed, "env_id": env, "fall_channel": r["fall_channel"],
              "event_order_stage1_def": r["event_order"], "anchor": anchor, "T": round(T, 3),
              **window_readout(diag[env], lo, hi, feet, cal), **reward_means(diag[env], lo, hi)}
        events.append(ev)
    # 같은 시각 생존 대조(같은 지형·상황의 대조가 아니다)
    contrast = []
    if fall_t and survivors:
        T = statistics.median(fall_t)
        hi = int(round(T / DT)) - 1
        lo = max(0, hi - int(round(WINDOW_S / DT)))
        for env in survivors:
            contrast.append({"case": case, "eval_seed": seed, "env_id": env, "T_median_fall": round(T, 3),
                             **window_readout(diag[env], lo, hi, feet, cal), **reward_means(diag[env], lo, hi)})
    cal.update(case=case, eval_seed=seed, feet=feet, unavailable=meta.get("unavailable", {}),
               fallen=len(events), envs=len(rows))
    return events, cal, {"contrast": contrast}


def write_csv(path: Path, data: list[dict]) -> None:
    cols: list[str] = []
    for r in data:
        cols += [k for k in r if k not in cols]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols or ["empty"], lineterminator="\n")
        w.writeheader()
        w.writerows(data)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("harvest")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    harvest, out = Path(a.harvest), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    events, cals, contrast = [], [], []
    for case, seed in CASES:
        d = harvest / "diag/cases" / f"seed_{seed}" / case
        if not (d / "diag.csv.gz").is_file():
            print(f"MISSING {d}")
            cals.append({"case": case, "eval_seed": seed, "status": "MISSING"})
            continue
        ev, cal, extra = read_case(d, case, seed)
        events += ev
        cals.append(cal)
        contrast += extra["contrast"]
    write_csv(out / "EVENTS_DIAG.csv", events)
    write_csv(out / "SURVIVOR_CONTRAST.csv", contrast)
    (out / "CALIBRATION.json").write_text(json.dumps(cals, indent=1) + "\n", encoding="utf-8")
    orders: dict[str, int] = {}
    for e in events:
        orders[f"{e['case']}:{e['order']}"] = orders.get(f"{e['case']}:{e['order']}", 0) + 1
    print(json.dumps({"events": len(events), "orders": orders}, ensure_ascii=False))
    return 0 if all(c.get("status") != "MISSING" for c in cals) else 1


if __name__ == "__main__":
    raise SystemExit(main())
