"""G-A056 A043 진단 재생 판독 (2026-09-28).  정의는 결과 전에 upload/plan/GO2_G_A056_A043_DIAG_REPLAY_PLAN_20260928.md §5에 고정했다.

변수를 고르지 않는다.  사건마다 무엇이 먼저 나타났는지를 사전 고정 값으로 적고, 같은 재생의 생존 로봇과 비교할 뿐이다.
생존 로봇은 비교군이지 인과 대조군이 아니다(지형·보행 위상이 통제되지 않았다).  action 변화가 먼저라는 값은
'정책이 가속을 일으켰다'는 판정이 아니다 — t_act 와 t_vy 의 시간차를 숫자로만 남긴다.

입력: 압축 푼 결과 폴더(go2_g_a056_a043_diag_replay/)의 diag/cases/seed_202/<case>/{steps.csv, diag.csv.gz, diag_meta.json}.

첫 episode 만 쓴다(C-39 해소).  로봇마다 첫 terminated/truncated 행에서 자르고 그 행도 뺀다(그 행의 로봇·센서 값은
reset 뒤 상태).  낙상은 평가기와 같은 규칙(0.5 s 유예 뒤 proj_grav_z > −0.5 또는 height_rel < 0.18 이 0.5 s,
또는 자세 판정 전에 몸통 접촉으로 종료)을 첫 episode 에만 적용한다 — tools/go2_a043_tilt_onset.py 와 같다.

기준 시각 onset: 낙상 이전에 기울기가 18°를 마지막으로 위로 넘은 시각(tilt_onset 과 같다; A052 의 −0.95 교차는 약 18.2°).
판독 창 W = [onset − 1.0 s, onset).
축 A(A052 와 같음): tools/go2_diag_replay_readout.window_readout 을 W 에 그대로 적용 — 회전 t_rot 대 접촉 변화
  t_contact = min(t_slip, t_support), 생존 기준 R·S·D 는 같은 재생 생존 로봇의 첫 episode 유효 행 p95.
  값: rotation_first / contact_first / simultaneous / rotation_only / contact_only / not_observed / unknown.
축 B(새): 옆 속도 이탈 대 접촉 변화.
  t_vy_full: onset 전 3 s 안에서, 명령 방향 옆 속도 초과량(steps.csv actual_vy − cmd_vy, 0.1 s 이동평균)이
    자기 정상 보행 창(2 s ~ min(8 s, onset − 1.5 s)) 평균 + 2σ 를 넘은 상태가 onset 까지 끊김 없이 이어진 구간의 시작
    (tilt_onset.lead_lag 과 같은 정의).  정상 보행 창이 20행 미만이면 무효(unknown).
  t_vy_w = max(t_vy_full, W 시작).  W 보다 먼저 시작했으면 vy_departure_before_window = 1.
  비교는 W 안의 t_vy_w 와 축 A 의 t_contact 로 한다.  차이 ≤ 0.04 s 이면 simultaneous.
  값: lateral_first / contact_first / simultaneous / lateral_only / contact_only / not_observed / unknown.
  (둘 다 W 시작에서 잡히면 simultaneous 다 — 창 밖 선후는 이 판독이 가르지 않는다.)
t_act: W 안에서 |a − a_prev|(12차원 L2)가 같은 재생 생존 로봇 첫 episode 유효 행의 p95 를 2행 이상 넘은 첫 시각.
  action 결측 행이 W 에 있으면 무효.  t_act_minus_t_vy = t_act − t_vy_w (숫자만).
관절(W 안, 기록만): 적용 토크/모터 effort 한계의 최댓값(분모는 actuator cfg 의 effort_limit.  PhysX 관절 한계는
  명시 actuator 에서 1e9 로 기록되므로 쓰지 않는다 — 2026-09-29 회수물에서 확인, 판독 전 정의 오류 수정), 계산 토크 ≠ 적용 토크(|차| > 1e-4 N·m)인 행 수
  (마지막 물리 substep 만 기록되므로 그보다 앞 substep 의 clip 은 보이지 않는다), soft 관절 한계 0.05 rad 안 행 수.
재현 대응: plain ↔ 저장 A043 steps.csv 가 같을 때만 기존 사건표(go2_a043_tilt_onset ROBOTS.csv)의 onset 을 붙인다.
  다르면 stored_table_env_match = 0 이고 붙이지 않는다(새 재생 표본으로 판독).
영상 대응: 검증기 check_video 가 VIDEO_ENV_MATCHED 인 로봇만 video 경로를 붙인다.

    python -B tools/go2_a043_diag_readout.py <압축 푼 결과 폴더> [--out <dir>]
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
import go2_a043_tilt_onset as onset_mod  # noqa: E402
import go2_diag_replay_readout as a052  # noqa: E402
import verify_go2_a043_diag_replay_harvest as verifier  # noqa: E402

DT, WINDOW_S, GAP_S = 0.02, 1.0, 0.04
ACT_ROWS = 2
CLIP_EPS, SOFT_MARGIN = 1e-4, 0.05
SEED = verifier.SEED
CASES = verifier.CASES
STORED_EVENTS = ROOT / "workspace/training/quadruped/reports/evidence/go2_a043_tilt_onset_20260928/ROBOTS.csv"
DEFAULT_OUT = verifier.DEFAULT_OUT
STEP_F = onset_mod.F


def load_steps_first_episode(path: Path) -> dict[int, list[dict]]:
    """첫 episode 행만(종료 행 제외).  tilt_onset.load 와 같은 규칙에 step 번호를 보탠다."""
    envs: dict[int, list[dict]] = {}
    stopped: set[int] = set()
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            e = int(r["env_id"])
            if e in stopped:
                continue
            if r["terminated"] == "1" or r["truncated"] == "1":
                stopped.add(e)
                if r["terminated"] == "1" and r.get("term_base_contact") == "1" and envs.get(e):
                    envs[e][-1]["base_contact_end"] = True
                continue
            row = {k: float(r[k]) for k in STEP_F}
            row["step"] = int(r["step"])
            row["tilt"] = math.degrees(math.acos(max(-1.0, min(1.0, -row["proj_grav_z"]))))
            envs.setdefault(e, []).append(row)
    return envs


def load_diag_first_episode(path: Path, lengths: dict[int, int]) -> tuple[list[str], dict[int, list[dict]]]:
    fields, diag = a052.load_diag(path)
    out = {}
    for e, rows in diag.items():
        rows = sorted(rows, key=lambda d: d["step"])
        out[e] = rows[: lengths.get(e, 0)]
    return fields, out


def action_delta(d: dict) -> float | None:
    vals = []
    for i in range(12):
        a, p = d.get(f"action_{i}"), d.get(f"prev_action_{i}")
        if a is None or p is None:
            return None
        vals.append((a - p) ** 2)
    return math.sqrt(sum(vals))


def act_p95(diag: dict[int, list[dict]], survivors: list[int]) -> float | None:
    v = []
    for e in survivors:
        for i, d in enumerate(diag[e]):
            if (i + 1) * DT < onset_mod.GRACE:
                continue
            x = action_delta(d)
            if x is not None:
                v.append(x)
    return a052.p95(v)


def t_act_in(win: list[dict], thr: float | None) -> tuple[int | None, str]:
    if thr is None:
        return None, "calibration_missing"
    deltas = [action_delta(d) for d in win]
    if not win or any(x is None for x in deltas):
        return None, "action_missing"
    return a052.first_run([x > thr for x in deltas], ACT_ROWS), ""


def effort_limits(j: dict, n: int) -> list[float]:
    """모터 토크 한계.  actuator 묶음이 하나면 그 effort_limit, 아니면 PhysX 관절 한계 중 실제 값(< 1e6)만."""
    acts = [a for a in (j.get("actuators") or {}).values() if isinstance(a, dict) and a.get("effort_limit")]
    if len(acts) == 1:
        return [float(acts[0]["effort_limit"])] * n
    return [float(x) if x and float(x) < 1e6 else 0.0 for x in (j.get("joint_effort_limits_env0") or [])]


def joint_summary(win: list[dict], meta: dict) -> dict:
    j = meta.get("joints") or {}
    names = j.get("names") or []
    lim = effort_limits(j, len(names))
    soft = j.get("soft_joint_pos_limits_env0") or []
    if not names or not win:
        return {"joint_valid": 0}
    ratio, clip_rows, near_rows = 0.0, 0, 0
    for d in win:
        clip = near = False
        for k, n in enumerate(names):
            app, cmd, pos = d.get(f"jtau_app_{n}"), d.get(f"jtau_cmd_{n}"), d.get(f"jpos_{n}")
            if app is None or cmd is None or pos is None:
                return {"joint_valid": 0}
            if k < len(lim) and lim[k]:
                ratio = max(ratio, abs(app) / lim[k])
            clip |= abs(cmd - app) > CLIP_EPS
            if k < len(soft):
                near |= pos <= soft[k][0] + SOFT_MARGIN or pos >= soft[k][1] - SOFT_MARGIN
        clip_rows += clip
        near_rows += near
    return {"joint_valid": 1, "tau_app_over_effort_limit_max": round(ratio, 4),
            "rows_cmd_ne_app_torque": clip_rows, "rows_near_soft_joint_limit": near_rows}


def order_b(i_vy: int | None, i_con: int | None, vy_reason: str, con_reason: str) -> str:
    if vy_reason or con_reason:
        return "unknown"
    if i_vy is None and i_con is None:
        return "not_observed"
    if i_con is None:
        return "lateral_only"
    if i_vy is None:
        return "contact_only"
    if (i_con - i_vy) * DT > GAP_S:
        return "lateral_first"
    if (i_vy - i_con) * DT > GAP_S:
        return "contact_first"
    return "simultaneous"


def stored_onsets(case: str) -> dict[int, dict]:
    if not STORED_EVENTS.is_file():
        return {}
    with STORED_EVENTS.open(encoding="utf-8", newline="") as fh:
        return {int(r["env"]): r for r in csv.DictReader(fh)
                if r["arm"] == "A043" and r["case"] == case and r["seed"] == str(SEED)}


def read_case(h: Path, case: str, stored_match: bool, video_map: dict) -> tuple[list[dict], dict, list[dict]]:
    d = verifier.run_dir(h, "diag", SEED, case)
    steps = load_steps_first_episode(d / "steps.csv")
    lengths = {e: len(r) for e, r in steps.items()}
    fields, diag = load_diag_first_episode(d / "diag.csv.gz", lengths)
    meta = json.loads((d / "diag_meta.json").read_text(encoding="utf-8"))
    feet = a052.feet_of(fields)
    outcome, onsets = {}, {}
    for e, rows in steps.items():
        tf = onset_mod.fall_time(rows)
        outcome[e] = ("FALL", tf) if tf is not None else ("SURVIVE", None)
        onsets[e] = onset_mod.onset_time(rows, tf) if tf is not None else None
    survivors = [e for e, (o, _) in outcome.items() if o == "SURVIVE"]
    cal = a052.calibrate(diag, lengths, survivors, feet)
    thr_act = act_p95(diag, survivors)
    cal.update(case=case, eval_seed=SEED, feet=feet, action_delta_p95=thr_act, first_episode_only=True,
               unavailable=meta.get("unavailable", {}), envs=len(steps),
               fallen=sum(1 for o, _ in outcome.values() if o == "FALL"))
    old = stored_onsets(case) if stored_match else {}
    events = []
    for e, (o, tf) in sorted(outcome.items()):
        if o != "FALL":
            continue
        rows, ton = steps[e], onsets[e]
        ev = {"case": case, "eval_seed": SEED, "env_id": e, "fall_t": tf, "onset_t": ton,
              "fall_kind": "base_contact_before_posture_hold" if rows and rows[-1].get("base_contact_end")
              and tf == rows[-1]["time_s"] else "posture_gate",
              "stored_table_env_match": int(stored_match)}
        if stored_match and e in old:
            ev["stored_onset_t"] = old[e]["onset_t"]
        vm = video_map.get((case, e))
        if vm:
            ev["video"] = vm["video"]
            if vm["video"] == "VIDEO_ENV_MATCHED":
                ev["video_file"] = f"video/cases/seed_{SEED}/{case}_env{e}/video.mp4"
        if ton is None:
            ev.update(order="unknown", order_b="unknown", invalid_reason="no_18deg_crossing_before_fall")
            events.append(ev)
            continue
        hi = int(round(ton / DT)) - 1
        lo = max(0, hi - int(round(WINDOW_S / DT)))
        a = a052.window_readout(diag[e], lo, hi, feet, cal)
        ev.update(a)
        # 축 B
        steady_hi = min(8.0, ton - 1.5)
        steady = onset_mod.window(rows, 2.0, steady_hi)
        lat = -1 if rows[0]["cmd_vy"] < 0 else 1
        ll = onset_mod.lead_lag(rows, ton, steady, lat)
        vy_reason = "" if ll else "steady_window_too_short"
        t_w0 = round((lo + 1) * DT, 3)
        t_vy_full = ll.get("lead_vy_start")
        i_vy = None
        if t_vy_full is not None:
            i_vy = max(0, int(round((t_vy_full - t_w0) / DT)))
            if i_vy >= hi - lo:
                i_vy = None
        i_con = None if a["t_contact"] is None else int(round((a["t_contact"] - t_w0) / DT))
        ev.update(t_vy_full=t_vy_full, t_vy_w=None if i_vy is None else round(t_w0 + i_vy * DT, 3),
                  vy_departure_before_window=int(t_vy_full is not None and t_vy_full < t_w0),
                  vy_invalid_reason=vy_reason,
                  order_b=order_b(i_vy, i_con, vy_reason, a["contact_invalid_reason"]))
        i_act, act_reason = t_act_in(diag[e][lo:hi], thr_act)
        ev.update(t_act=None if i_act is None else round(t_w0 + i_act * DT, 3), act_invalid_reason=act_reason,
                  t_act_minus_t_vy=None if (i_act is None or i_vy is None) else round((i_act - i_vy) * DT, 3))
        ev.update(joint_summary(diag[e][lo:hi], meta))
        ev.update(a052.reward_means(diag[e], lo, hi))
        events.append(ev)
    contrast = []
    fall_on = [onsets[e] for e in onsets if onsets[e] is not None]
    if fall_on and survivors:
        T = statistics.median(fall_on)
        hi = int(round(T / DT)) - 1
        lo = max(0, hi - int(round(WINDOW_S / DT)))
        for e in survivors:
            c = {"case": case, "eval_seed": SEED, "env_id": e, "T_median_onset": round(T, 3),
                 **a052.window_readout(diag[e], lo, hi, feet, cal)}
            i_act, act_reason = t_act_in(diag[e][lo:hi], thr_act)
            c.update(t_act=None if i_act is None else round((lo + 1) * DT + i_act * DT, 3),
                     act_invalid_reason=act_reason, **joint_summary(diag[e][lo:hi], meta))
            win = [r for r in steps[e] if T - WINDOW_S <= r["time_s"] < T]
            if win:
                c["vy_excess_mean"] = round(statistics.fmean(lat_sign(r) * (r["actual_vy"] - r["cmd_vy"]) for r in win), 4)
            contrast.append(c)
    return events, cal, contrast


def lat_sign(r: dict) -> int:
    return -1 if r["cmd_vy"] < 0 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("harvest")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--stored", default=str(verifier.STORED))
    a = ap.parse_args(argv)
    h, out, stored = Path(a.harvest), Path(a.out), Path(a.stored)
    out.mkdir(parents=True, exist_ok=True)
    listed = set()
    if (h / "SHA256SUMS.txt").is_file():
        listed = {l.split(None, 1)[1].lstrip("*").removeprefix("./")
                  for l in (h / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if l.strip()}
    video_map = {(c, e): verifier.check_video(h, c, e, listed) for c, e in verifier.VIDEOS}
    events, cals, contrast, repro = [], [], [], {}
    for case in CASES:
        d = verifier.run_dir(h, "diag", SEED, case)
        if not (d / "diag.csv.gz").is_file():
            cals.append({"case": case, "status": "MISSING"})
            continue
        plain = verifier.run_dir(h, "plain", SEED, case) / "steps.csv"
        ref = stored / f"seed_{SEED}" / case / "steps.csv"
        st = verifier.compare_steps(plain, ref)["status"] if plain.is_file() and ref.is_file() else "MISSING"
        repro[case] = st
        ev, cal, con = read_case(h, case, st == "NO_DIFFERENCE_IN_STORED_CHANNELS", video_map)
        cal["plain_vs_stored"] = st
        events += ev
        cals.append(cal)
        contrast += con
    a052.write_csv(out / "EVENTS_A043_DIAG.csv", events)
    a052.write_csv(out / "SURVIVOR_CONTRAST.csv", contrast)
    (out / "CALIBRATION.json").write_text(json.dumps(cals, indent=1) + "\n", encoding="utf-8")
    summary: dict[str, int] = {}
    for e in events:
        for k in ("order", "order_b"):
            key = f"{e['case']}:{k}:{e.get(k)}"
            summary[key] = summary.get(key, 0) + 1
    (out / "READOUT_SUMMARY.json").write_text(json.dumps({
        "events": len(events), "counts": summary, "plain_vs_stored": repro,
        "limits": ["time order is not causation", "t_act before t_vy is not a finding that the policy caused the acceleration",
                   "survivors are a comparison group, not a causal control",
                   "torque clip is recorded for the last physics substep of each step only"]},
        indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"events": len(events), "counts": summary, "plain_vs_stored": repro}, ensure_ascii=False))
    return 0 if all(c.get("status") != "MISSING" for c in cals) else 1


if __name__ == "__main__":
    raise SystemExit(main())
