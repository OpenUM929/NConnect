"""험지 옆걸음 낙상 직전 사건표 (2026-09-28, Codex 계획 upload/plan/GO2_FAILURE_DATA_REQUEST_CODEX_20260928.md §4).

저장된 평가 기록(steps.csv)만 읽는다.  재생·계측·판정을 하지 않는다 — 로봇 한 대당 한 행을 만든다.

대상: rough_lateral(명령 vy = +0.3 m/s), 평가 seed 101·202·303 × 32대.
  G-A048  핵심 (현재 최고 정책)
  G-A033  비교 (채택 기준선)
  G-A038  조건부 비교 — ang_vel_xy_l2 −0.08.  회전 벌점 가설이 어떤 낙상 유형을 줄였는지 보려고 넣었다.
계단 10/15cm 는 여기서 다시 세지 않는다.  reports/evidence/go2_stairs_process_20260927/ENV_TIMELINE.csv 를 재사용한다.

정의 (tools/go2_next_lever_evidence.py 의 channels() 와 같은 자세 게이트):
  tilt 불량   proj_grav_z > −0.5     height 불량  height_rel < 0.18 (빈 칸도 불량)
  0.5 s 유예 뒤 한 채널 또는 두 채널 합의 불량이 0.5 s 연속이면 자세 낙상, 종료(terminated)된 로봇도 낙상.
  fall_channel 은 FALL_CHANNELS.csv 와 같은 다섯 경로로 나눈다.  합계를 그 파일과 대조한다(EVENTS_COUNT_CHECK.csv).
  terminated=1 또는 truncated=1 인 행은 이미 reset 된 다음 episode 의 첫 상태다(root_z ≈ 0.5).  episode 는 그 앞 행에서 끝낸다.
  step 1000 은 모든 로봇이 time_out(truncated)이다.

사건:
  event_t      자세 낙상이 먼저면 그 0.5 s 불량 구간의 시작, 종료가 먼저면 종료 직전 행의 시각.
  first_bad_t  사건 앞 마지막 '두 채널 모두 정상' 행 다음 행 — 사건의 시작점.
  event_order  그 시작점부터 어느 채널이 먼저 불량이 됐나(tilt_first / height_first / same_step).
직전 창(pre_*): first_bad_t 앞 1.0 s(유예 구간 제외, 짧아지면 pre_window_s 에 실제 길이).
  tilt 가 먼저인 사건은 이 창 끝에 이미 넘어가는 동작이 들어 있다(pre_grav_z_end ≈ −0.5).
기울기 전 창(pretip_*): tilt 사건만, 첫 tilt 불량 앞 마지막 proj_grav_z ≤ −0.9 행까지(그 행 포함) 1.0 s.
생존 로봇의 pre_*: 같은 arm·seed 낙상 로봇 pre_anchor_t 중앙값 앞 1.0 s(control_kind).  같은 시각이지 같은 지형·상황이 아니다.

원 채널: 몸통 좌표 vx·vy·wz(root_lin_vel_b, root_ang_vel_b — go2_eval_telemetry.py:247-262), proj_grav_z,
         height_rel, terrain_z(높이 스캐너 평균), root_x·y, 명령, 종료 사유.
대리값(이름에 _derived):
  tilt_descent_s_derived     첫 tilt 불량 행 앞 마지막 proj_grav_z ≤ −0.9 행부터의 시간.
  pre_terrain_z_range_derived 직전 창 terrain_z 최대−최소.
몸통 roll·pitch 각속도(ang_vel_xy_l2 의 입력)·발·접촉·action·보상 항은 저장되지 않았다.  위 값은 그것을 대신하지 않는다.

    python -B tools/go2_failure_events.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace/_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_failure_data_20260928"
FALL_CHANNELS = ROOT / "workspace/training/quadruped/reports/evidence/go2_next_lever_20260927/FALL_CHANNELS.csv"
ARMS = (
    ("G-A048", "lin_vel_z_l2 -1.25", "go2_g_a048_a033_lin_vel_z_m125"),
    ("G-A033", "baseline", "go2_g_a033_a017_track_lin_vel_xy_150"),
    ("G-A038", "ang_vel_xy_l2 -0.08", "go2_g_a038_a033_ang_vel_xy_m008"),
)
CASE = "rough_lateral"
SEEDS = (101, 202, 303)
GRACE_S, HOLD_S, TILT_COS, HEIGHT_MIN, DT = 0.5, 0.5, 0.5, 0.18, 0.02
WINDOW_S = 1.0
WZ_MARK = 0.6  # rad/s. 생존 로봇 같은 시각 창 |wz| 최대의 3사분위(0.44~0.48)보다 위 — 분석 편의값, 문턱 아님
KEEP_COLS = ("time_s", "cmd_vx", "cmd_vy", "cmd_wz", "actual_vx", "actual_vy", "actual_wz", "error_xy",
             "speed_xy", "root_x", "root_y", "root_z", "proj_grav_z", "terrain_z", "height_rel")


def _f(v: str) -> float | None:
    return float(v) if v not in ("", None) else None


def load(path: Path) -> dict[int, list[dict]]:
    envs: dict[int, list[dict]] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            r = {k: _f(row[k]) for k in KEEP_COLS}
            r["term"] = row["terminated"] == "1"
            r["trunc"] = row.get("truncated") == "1"
            r["bc"] = row.get("term_base_contact") == "1"
            r["to"] = row.get("term_time_out") == "1"
            envs.setdefault(int(row["env_id"]), []).append(r)
    return envs


def along(r: dict) -> float | None:
    """명령 방향으로 투영한 몸통 좌표 속도(부호 있음)."""
    n = math.hypot(r["cmd_vx"], r["cmd_vy"])
    return None if n == 0 else (r["actual_vx"] * r["cmd_vx"] + r["actual_vy"] * r["cmd_vy"]) / n


def _bad(r: dict) -> tuple[bool, bool]:
    return (not r["proj_grav_z"] <= -TILT_COS,
            not (r["height_rel"] is not None and r["height_rel"] >= HEIGHT_MIN))


def classify(rows: list[dict]) -> dict:
    """channels() 와 같은 타이머 — 종료 뒤에도 타이머를 끊지 않는 점까지 같게 한다(합계 대조용)."""
    rt = rh = ru = 0.0
    ft = fh = fu = False
    term = False
    union_fall_start = None
    for i, r in enumerate(rows):
        term = term or r["term"]
        if r["time_s"] < GRACE_S:
            continue
        tilt_bad, height_bad = _bad(r)
        rt = rt + DT if tilt_bad else 0.0
        rh = rh + DT if height_bad else 0.0
        ru = ru + DT if (tilt_bad or height_bad) else 0.0
        ft = ft or rt >= HOLD_S - 1e-9
        fh = fh or rh >= HOLD_S - 1e-9
        if ru >= HOLD_S - 1e-9 and not fu:
            fu = True
            union_fall_start = i - round(ru / DT) + 1
    channel = ""
    if fu or term:
        channel = ("both" if ft and fh else "tilt_only" if ft else "height_only" if fh else
                   "union_only" if fu else "terminated_only")
    return {"channel": channel, "fu": fu, "union_fall_start": union_fall_start}


def window_stats(win: list[dict], prefix: str) -> dict:
    """창 하나의 원 채널 요약.  빈 창이면 None."""
    keys = ("along_v_mean", "along_v_last02", "speed_xy_mean", "error_xy_mean", "abs_wz_max", "abs_wz_mean",
            "grav_z_start", "grav_z_end", "height_rel_start", "height_rel_end")
    if not win:
        return {prefix + k: None for k in keys}
    al = [a for a in (along(r) for r in win) if a is not None]
    h0, h1 = win[0]["height_rel"], win[-1]["height_rel"]
    return {prefix + "along_v_mean": round(statistics.fmean(al), 4) if al else None,
            prefix + "along_v_last02": round(statistics.fmean(al[-10:]), 4) if al else None,
            prefix + "speed_xy_mean": round(statistics.fmean(r["speed_xy"] for r in win), 4),
            prefix + "error_xy_mean": round(statistics.fmean(r["error_xy"] for r in win), 4),
            prefix + "abs_wz_max": round(max(abs(r["actual_wz"]) for r in win), 4),
            prefix + "abs_wz_mean": round(statistics.fmean(abs(r["actual_wz"]) for r in win), 4),
            prefix + "grav_z_start": round(win[0]["proj_grav_z"], 4),
            prefix + "grav_z_end": round(win[-1]["proj_grav_z"], 4),
            prefix + "height_rel_start": None if h0 is None else round(h0, 4),
            prefix + "height_rel_end": None if h1 is None else round(h1, 4)}


def span(episode: list[dict], end_idx: int) -> list[dict]:
    """end_idx 행을 포함하지 않는, 그 앞 WINDOW_S 초(유예 구간 제외)."""
    lo = max(0, end_idx - round(WINDOW_S / DT))
    return [r for r in episode[lo:end_idx] if r["time_s"] >= GRACE_S]


def event_row(arm: str, seed: int, env: int, rows: list[dict], c: dict) -> dict:
    out: dict = {"arm": arm, "case": CASE, "eval_seed": seed, "env_id": env}
    end = next((i for i, r in enumerate(rows) if r["term"] or r["trunc"]), len(rows))
    episode = rows[:end]
    ended = end < len(rows)
    fallen = bool(c["channel"])
    posture_first = c["fu"] and c["union_fall_start"] is not None and c["union_fall_start"] < end
    if not fallen:
        idx = None
        out.update(outcome="SURVIVE", fall_channel="", event_kind="", event_t=None)
    elif posture_first:
        idx = c["union_fall_start"]
        out.update(outcome="FALL", fall_channel=c["channel"], event_kind="posture_first", event_t=rows[idx]["time_s"])
    else:
        idx = end - 1
        out.update(outcome="FALL", fall_channel=c["channel"], event_kind="termination_first",
                   event_t=rows[idx]["time_s"])
    out["termination_t"] = rows[end - 1]["time_s"] if ended else None
    out["termination_reason"] = ("" if not ended else "base_contact" if rows[end]["bc"] else
                                 "time_out" if rows[end]["to"] or rows[end]["trunc"] else "other")
    out["valid_rows"] = len(episode)
    none_keys = ("first_bad_t", "first_tilt_bad_t", "first_height_bad_t", "event_order", "bad_to_termination_s",
                 "tilt_descent_s_derived", "pre_anchor_t", "pre_window_s", "pre_terrain_z_range_derived",
                 "progress_to_anchor_m")
    out.update({k: None for k in none_keys})
    out.update(window_stats([], "pre_"))
    out["pretip_window_s"] = None
    out.update(wz_mark_onset_t=None, grav_095_cross_t=None, yaw_vs_tilt_order=None)
    out.update(window_stats([], "pretip_"))
    e = episode[-1]
    if fallen:
        tail_end = min(end, idx + round(HOLD_S / DT) + 1)
        last_ok = next((i for i in range(min(idx, end - 1), -1, -1) if not any(_bad(episode[i]))), None)
        first_bad = last_ok + 1 if last_ok is not None and last_ok + 1 < tail_end else None
        if first_bad is not None:
            ft = next((i for i in range(first_bad, tail_end) if _bad(episode[i])[0]), None)
            fh = next((i for i in range(first_bad, tail_end) if _bad(episode[i])[1]), None)
            out["first_bad_t"] = episode[first_bad]["time_s"]
            out["first_tilt_bad_t"] = None if ft is None else episode[ft]["time_s"]
            out["first_height_bad_t"] = None if fh is None else episode[fh]["time_s"]
            out["event_order"] = ("tilt_first" if fh is None or (ft is not None and ft < fh) else
                                  "height_first" if ft is None or fh < ft else "same_step")
            if ended and not rows[end]["trunc"]:
                out["bad_to_termination_s"] = round((end - first_bad) * DT, 2)
            if ft is not None:
                level = next((i for i in range(ft, -1, -1) if episode[i]["proj_grav_z"] <= -0.9), None)
                out["tilt_descent_s_derived"] = None if level is None else round((ft - level) * DT, 2)
                # 선후: 첫 tilt 불량 앞 2 초 안에서 (a) |wz| > WZ_MARK 가 시작된 마지막 시각,
                #       (b) proj_grav_z 가 −0.95 를 마지막으로 넘은 시각.  WZ_MARK 는 분석 편의값이다.
                lo2 = max(0, ft - round(2.0 / DT))
                t_wz = t_g = None
                for i in range(ft, lo2, -1):
                    if t_wz is None and abs(episode[i]["actual_wz"]) > WZ_MARK and abs(episode[i - 1]["actual_wz"]) <= WZ_MARK:
                        t_wz = episode[i]["time_s"]
                    if t_g is None and episode[i]["proj_grav_z"] > -0.95 and episode[i - 1]["proj_grav_z"] <= -0.95:
                        t_g = episode[i]["time_s"]
                out["wz_mark_onset_t"] = t_wz
                out["grav_095_cross_t"] = t_g
                out["yaw_vs_tilt_order"] = ("no_wz_mark" if t_wz is None else "no_grav_cross" if t_g is None else
                                            "yaw_first" if t_wz < t_g else "tilt_first" if t_g < t_wz else "same_step")
                if level is not None:  # 기울기 시작 전 1 초 — 넘어지는 동작 자체가 섞이지 않는 창
                    pretip = span(episode, level + 1)
                    out["pretip_window_s"] = round(len(pretip) * DT, 2)
                    out.update(window_stats(pretip, "pretip_"))
        else:
            out["event_order"] = "no_posture_violation_before_termination"
        anchor = first_bad if first_bad is not None else idx
        pre = span(episode, anchor)
        e = episode[min(anchor, end - 1)]
        out["pre_anchor_t"] = e["time_s"]
        out["pre_window_s"] = round(len(pre) * DT, 2)
        out.update(window_stats(pre, "pre_"))
        tz = [r["terrain_z"] for r in pre if r["terrain_z"] is not None]
        out["pre_terrain_z_range_derived"] = round(max(tz) - min(tz), 4) if tz else None
        out["progress_to_anchor_m"] = round(sum((along(r) or 0.0) * DT for r in episode[:anchor]), 4)
    out.update(cmd_vx=e["cmd_vx"], cmd_vy=e["cmd_vy"], cmd_wz=e["cmd_wz"],
               anchor_root_x=round(e["root_x"], 3), anchor_root_y=round(e["root_y"], 3),
               anchor_terrain_z=None if e["terrain_z"] is None else round(e["terrain_z"], 4))
    body = [r for r in episode if r["time_s"] >= GRACE_S]
    out["episode_max_grav_z"] = round(max(r["proj_grav_z"] for r in body), 4) if body else None
    hr = [r["height_rel"] for r in body if r["height_rel"] is not None]
    out["episode_min_height_rel"] = round(min(hr), 4) if hr else None
    out["episode_frac_grav_gt_m08"] = (round(sum(1 for r in body if r["proj_grav_z"] > -0.8) / len(body), 4)
                                       if body else None)
    runs = cur = 0
    for r in body:  # 0.5 s 를 못 채우고 회복한 tilt 불량 구간 수
        if _bad(r)[0]:
            cur += 1
        else:
            runs += 1 if 0 < cur < round(HOLD_S / DT) else 0
            cur = 0
    out["transient_tilt_runs"] = runs
    out["control_kind"] = ""
    out["missing_reason"] = "" if episode else "empty_episode"
    out["_episode"] = episode
    return out


def matched_control(events: list[dict]) -> None:
    """생존 로봇의 비교 창: 같은 arm·seed 낙상 로봇 pre_anchor_t 중앙값 앞 1 초(계획 §4-2의 한계 그대로)."""
    groups: dict[tuple, list[dict]] = {}
    for r in events:
        groups.setdefault((r["arm"], r["eval_seed"]), []).append(r)
    for rs in groups.values():
        times = [r["pre_anchor_t"] for r in rs if r["outcome"] == "FALL" and r["pre_anchor_t"] is not None]
        t0 = statistics.median(times) if times else None
        for r in rs:
            if r["outcome"] != "SURVIVE":
                continue
            r["control_kind"] = "same_seed_median_fall_time" if t0 is not None else "no_fall_in_seed"
            if t0 is None:
                continue
            ep = r["_episode"]
            anchor = min(range(len(ep)), key=lambda i: abs(ep[i]["time_s"] - t0))
            pre = span(ep, anchor)
            r["pre_anchor_t"] = ep[anchor]["time_s"]
            r["pre_window_s"] = round(len(pre) * DT, 2)
            r.update(window_stats(pre, "pre_"))


EARLY_S = 2.0  # 시작 직후 사건: first_bad_t < 2.0 s (유예 0.5 s 뒤 1.5 s 안).  분석 편의 구분, 문턱 아님.
# 계획 §5 채널 묶음 → 저장 기록의 열 이름.  열이 없으면 NOT_STORED.  발·접촉·action·보상은 평가 기록에 열이 없다.
CHANNELS = (
    ("identity", "sim time / step / env id / reset·termination", ("time_s", "step", "env_id", "terminated", "truncated",
                                                                 "term_base_contact", "term_time_out")),
    ("body", "body-frame linear velocity x,y", ("actual_vx", "actual_vy")),
    ("body", "body-frame yaw rate (track_ang_vel_z_exp input)", ("actual_wz",)),
    ("body", "body-frame vertical velocity (lin_vel_z_l2 input)", ("actual_vz",)),
    ("body", "body-frame roll/pitch rate (ang_vel_xy_l2 input)", ("actual_wx", "actual_wy")),
    ("body", "projected gravity z", ("proj_grav_z",)),
    ("body", "projected gravity x,y (flat_orientation_l2 input)", ("proj_grav_x", "proj_grav_y")),
    ("body", "world position", ("root_x", "root_y", "root_z")),
    ("body", "world orientation quaternion", ("root_qw",)),
    ("terrain", "terrain height under base (height scanner mean)", ("terrain_z", "height_rel")),
    ("terrain", "terrain type / level / origin per env", ("terrain_level",)),
    ("feet", "foot world position / velocity", ("foot_fl_x",)),
    ("feet", "foot contact force / state", ("contact_fl",)),
    ("feet", "air time / first contact (feet_air_time input)", ("air_time_fl",)),
    ("action", "policy action / previous action (action_rate_l2 input)", ("action_0",)),
    ("action", "joint position / velocity / torque / limit hit", ("q_0",)),
    ("reward", "per-term reward value (raw / weighted)", ("rew_track_lin_vel_xy_exp",)),
    ("command", "velocity command", ("cmd_vx", "cmd_vy", "cmd_wz")),
    ("outcome", "tracking error / speed", ("error_xy", "error_yaw", "speed_xy")),
)


def channel_availability(header: list[str]) -> list[dict]:
    out = []
    for group, what, cols in CHANNELS:
        present = [c for c in cols if c in header]
        out.append({"group": group, "channel": what, "columns_looked_for": " ".join(cols),
                    "status": "STORED" if len(present) == len(cols) else "PARTIAL" if present else "NOT_STORED"})
    return out


def family(r: dict) -> str:
    if r["outcome"] != "FALL":
        return "survive"
    if r["event_order"] == "height_first":
        return "height_first"
    if r["first_bad_t"] is not None and r["first_bad_t"] < EARLY_S:
        return "tilt_early"
    return "tilt_mid_late" if r["event_order"] == "tilt_first" else r["event_order"] or "other"


def summarize(events: list[dict]) -> list[dict]:
    out = []
    for arm, _, _ in ARMS:
        rows = [r for r in events if r["arm"] == arm]
        surv = [r for r in rows if r["outcome"] == "SURVIVE"]
        for fam in ("tilt_early", "tilt_mid_late", "height_first", "survive"):
            g = [r for r in rows if family(r) == fam]

            def med(key: str, pool: list[dict] = g) -> float | None:
                v = [r[key] for r in pool if r.get(key) is not None]
                return round(statistics.median(v), 4) if v else None
            tip = [r for r in g if r.get("grav_095_cross_t") is not None and r.get("first_tilt_bad_t") is not None]
            out.append({
                "arm": arm, "family": fam, "n": len(g), "envs": len(rows),
                "yaw_first_n": sum(1 for r in g if r.get("yaw_vs_tilt_order") == "yaw_first"),
                "tilt_before_yaw_n": sum(1 for r in g if r.get("yaw_vs_tilt_order") == "tilt_first"),
                "tilt_18_to_60deg_s_median": (round(statistics.median(r["first_tilt_bad_t"] - r["grav_095_cross_t"]
                                                                     for r in tip), 2) if tip else None),
                "bad_to_termination_s_median": med("bad_to_termination_s"),
                "pre_anchor_t_median": med("pre_anchor_t"),
                "pre_along_v_mean_median": med("pre_along_v_mean"),
                "pre_error_xy_mean_median": med("pre_error_xy_mean"),
                "pre_abs_wz_max_median": med("pre_abs_wz_max"),
                "pretip_abs_wz_max_median": med("pretip_abs_wz_max"),
                "pretip_grav_z_start_median": med("pretip_grav_z_start"),
                "pre_height_rel_start_median": med("pre_height_rel_start"),
                "episode_min_height_rel_median": med("episode_min_height_rel"),
                "survivor_pre_abs_wz_max_median": med("pre_abs_wz_max", surv),
                "survivor_pre_along_v_mean_median": med("pre_along_v_mean", surv),
                "survivor_pre_height_rel_start_median": med("pre_height_rel_start", surv),
            })
    return out


def write_csv(path: Path, data: list[dict]) -> None:
    cols: list[str] = []
    for r in data:
        cols += [k for k in r if k not in cols]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(data)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    events, check, sources = [], [], []
    ref = {}
    with FALL_CHANNELS.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ref[(r["arm"], r["case"], r["seed"])] = r
    for arm, change, keep in ARMS:
        for seed in SEEDS:
            path = KEEP / keep / "evaluation/candidate/cases" / f"seed_{seed}" / CASE / "steps.csv"
            if not path.is_file():
                print(f"MISSING {path}")
                continue
            sources.append({"arm": arm, "seed": seed, "path": path.relative_to(ROOT).as_posix(),
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            envs = load(path)
            counts: dict[str, int] = {}
            for env, rows in sorted(envs.items()):
                c = classify(rows)
                if c["channel"]:
                    counts[c["channel"]] = counts.get(c["channel"], 0) + 1
                row = event_row(arm, seed, env, rows, c)
                row["change"] = change
                events.append(row)
            want = ref.get((arm, CASE, str(seed)))
            mine = {k: counts.get(k, 0) for k in ("height_only", "tilt_only", "both", "union_only", "terminated_only")}
            same = want is not None and all(int(want[k]) == v for k, v in mine.items())
            check.append({"arm": arm, "seed": seed, **mine, "fallen_total": sum(mine.values()),
                          "fall_channels_csv_match": same})
            print(arm, seed, mine, "match" if same else "MISMATCH")
    matched_control(events)
    for r in events:
        r.pop("_episode", None)
    write_csv(OUT / "EVENTS.csv", events)
    write_csv(OUT / "EVENTS_COUNT_CHECK.csv", check)
    write_csv(OUT / "FAMILY_SUMMARY.csv", summarize(events))
    with (ROOT / sources[0]["path"]).open(encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))
    write_csv(OUT / "CHANNEL_AVAILABILITY.csv", channel_availability(header))
    provenance = {
        "tool": "tools/go2_failure_events.py",
        "plan": "workspace/training/quadruped/upload/plan/GO2_FAILURE_DATA_REQUEST_CODEX_20260928.md",
        "case": CASE, "eval_seeds": list(SEEDS),
        "posture_gate": {"grace_s": GRACE_S, "hold_s": HOLD_S, "tilt_cos": TILT_COS, "height_rel_min_m": HEIGHT_MIN},
        "analysis_marks_not_thresholds": {"window_s": WINDOW_S, "wz_mark_rad_s": WZ_MARK, "early_s": EARLY_S,
                                          "grav_cross": -0.95, "pretip_level": -0.9},
        "steps_csv_header": header,
        "sources": sources,
        "reused_not_recomputed": [
            "workspace/training/quadruped/reports/evidence/go2_stairs_process_20260927/ENV_TIMELINE.csv",
            "workspace/training/quadruped/reports/GO2_STAIRS_PROCESS_A043_A048_A050_20260927.md",
            "workspace/training/quadruped/reports/evidence/go2_next_lever_20260927/CASE_ROWS.csv"],
    }
    (OUT / "PROVENANCE.json").write_text(json.dumps(provenance, indent=1) + "\n", encoding="utf-8")
    print(OUT / "EVENTS.csv", len(events))
    return 0 if all(c["fall_channels_csv_match"] for c in check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
