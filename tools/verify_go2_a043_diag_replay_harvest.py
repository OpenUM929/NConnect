"""G-A056 A043 진단 재생 회수 검증 (2026-09-28).  성능·원인을 판정하지 않는다.

A052 검증기(tools/verify_go2_diag_replay_harvest.py)를 바탕으로, 서버 종료 판단에 필요한 네 판정을 따로 낸다.
  zip       ZIP_SHA_VERIFIED | ZIP_SHA_MISMATCH | ZIP_NOT_CHECKED(폴더를 준 경우)
            결과 ZIP 과 sidecar(.sha256)의 SHA256 이 같다 · 안전한 경로만 들어 있다
  artifact  ARTIFACT_VERIFIED | ARTIFACT_NOT_VERIFIED
            필수 파일이 모두 있고 SHA256SUMS 에 올라 있으며 해시가 맞다 · 수집 완료 표시 · 정책·평가기 식별자 ·
            네 평가 실행의 평가기 완료 · 재현 비교에 쓸 steps.csv · 진단 CSV 키가 1..1000 × 0..31 로 중복·누락 없음
  channels  DIAG_CHANNELS_COMPLETE | DIAG_CHANNELS_INCOMPLETE
            필수 채널 묶음 7개(body·feet·contact·terrain·action·reward·joints)가 diag_meta 에서 UNAVAILABLE 이 아니고,
            판독기가 읽는 열 전부(관절 12개 × 위치·속도·계산 토크·적용 토크 포함)가 헤더에 있고,
            종료·시간초과가 아닌 모든 행에서 빈칸·NaN·Infinity 가 없고, 접촉 버퍼가 그 step 에 갱신됐다.
            채널이 실패한 뒤에도 재생이 계속된 것은 회수 안전장치이지 채널 확보가 아니다 — 여기서 미확보로 센다.
  video     영상마다 VIDEO_ENV_MATCHED | VIDEO_ENV_OWN_RUN_ONLY | VIDEO_CAMERA_UNVERIFIED | VIDEO_NOT_ACQUIRED
            파일·식별자·프레임 수 → 카메라 계측이 지정 env 를 따라갔나(아래) → 영상 실행 steps.csv 가 plain 과 같은가
카메라 판정(결과 전 고정, 분석 편의값): step ≥ 10 이고 그 행과 앞 행에서 대상 env 가 reset 되지 않은 행만 본다.
  행 통과 = cfg_env_index 가 지정값이고, 카메라 prim 위치 − eye 로 되짚은 원점과 대상 로봇 몸통의 수평 거리가
  이 행 또는 앞 행 기준으로 ≤ 0.10 m.  통과 행이 95 % 이상이면 카메라가 지정 env 를 따라간 것으로 본다.
  다른 로봇이 0.30 m 안에 있던 행의 비율은 기록만 한다(험지 칸 하나에 로봇이 여러 대라 화면에 함께 보일 수 있다).
  프레임 수는 995~1001 을 요구한다(기존 A043 영상: 500 step → 499 프레임, 50 fps).

종료코드  0 = zip·artifact·channels 통과, 영상 네 개 모두 MATCHED 또는 OWN_RUN_ONLY → shutdown=OK
          3 = zip·artifact 통과, 채널 또는 영상 미완료(또는 폴더를 줘서 zip 미검사) → shutdown=EXCEPTION_DECISION_REQUIRED
              서버를 켠 채 복구 가능성을 판단한다. 복구 불가면 exception_evidence 로 진단 데이터·checkpoint 식별 정보·
              실패 로그가 받은 ZIP 안에 있는지 확인하고 예외 종료를 기록한다. '회수 완결'·'진단 성공'이 아니다.
          1 = zip 또는 artifact 실패 → shutdown=DO_NOT_SHUTDOWN.  다시 회수한다
재현 비교(REPRO.csv)는 판정에 넣지 않는다(영상 대응 판정에만 쓴다).  steps.csv 가 같다는 것은 저장 채널·정밀도에서
차이가 없었다는 뜻이지 모든 내부 상태에 개입이 없었다는 증명이 아니다.

    python -B tools/verify_go2_a043_diag_replay_harvest.py <GO2_G_A056_RESULT.zip | 압축 푼 폴더> [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORED = ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15/evaluation/candidate/cases"
MODEL_SHA = "4d9236818f998bdb87efaea4acfa1e4c861b0d87947229e88f9175495066bd6b"
ENV_SHA = "9af8f18a084f3008d6a6a3563a3c56091d9eb8236d42db6abbb06c0fe926a06d"
EVALUATOR_SHA = "353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84"
KEEP_DIR_NAME = "go2_g_a056_a043_diag_replay"
SEED = 202
CASES = ("rough_lateral", "combined_yaw_right")
RUNS = tuple((label, SEED, c) for c in CASES for label in ("plain", "diag"))
VIDEOS = (("rough_lateral", 5), ("rough_lateral", 11), ("combined_yaw_right", 3), ("combined_yaw_right", 16))
STEPS, ENVS, JOINTS = 1000, 32, 12
REQUIRED_GROUPS = ("body", "feet", "contact", "terrain", "action", "reward", "joints")
FEET = ("FL", "FR", "RL", "RR")
ACTION_DIM = 12
REQUIRED_COLUMNS = (("ang_vel_b_x", "ang_vel_b_y", "lin_vel_b_y", "contact_fresh")
                    + tuple(f"{f}_{k}" for f in FEET
                            for k in ("contact_time", "vel_x", "vel_y", "pos_z", "terrain_zmax015_derived"))
                    + tuple(f"action_{i}" for i in range(ACTION_DIM))
                    + tuple(f"prev_action_{i}" for i in range(ACTION_DIM)))
JOINT_KINDS = ("jpos", "jvel", "jtau_cmd", "jtau_app")
LOCATIONS_KEPT = 5
TOP_FILES = ("RESULT_STATUS.txt", "RUNNER_STATUS.txt", "launcher.snapshot.log", "meta/identity.json",
             "meta/RUN_TIMES.txt", "meta/REPRO_STATUS.txt", "meta/run_config.env", "meta/experiment.json",
             "video/VIDEO_STATUS.txt")
RUN_FILES = ("steps.csv", "summary.json", "STATUS.txt")
DIAG_FILES = ("diag.csv.gz", "diag_meta.json", "DIAG_STATUS.txt")
VIDEO_FILES = ("video.mp4", "steps.csv", "STATUS.txt", "camera.csv", "camera_meta.json", "CAMERA_STATUS.txt",
               "video_identity.json")
CAM_SKIP_STEPS, CAM_DIST_M, CAM_PASS_FRAC, OTHER_NEAR_M = 10, 0.10, 0.95, 0.30
FRAMES_MIN, FRAMES_MAX = 995, 1001
VIDEO_OK = ("VIDEO_ENV_MATCHED", "VIDEO_ENV_OWN_RUN_ONLY")
DEFAULT_OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a056_diag_20260928"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_dir(h: Path, label: str, seed: int, case: str) -> Path:
    return h / label / "cases" / f"seed_{seed}" / case


def video_dir(h: Path, case: str, env: int) -> Path:
    return h / "video" / "cases" / f"seed_{SEED}" / f"{case}_env{env}"


def required_files() -> list[str]:
    out = list(TOP_FILES)
    for label, seed, case in RUNS:
        base = f"{label}/cases/seed_{seed}/{case}"
        out += [f"{base}/{f}" for f in RUN_FILES]
        out.append(f"logs/{label}_seed_{seed}_{case}.log")
        if label == "diag":
            out += [f"{base}/{f}" for f in DIAG_FILES]
    return out


def compare_steps(a: Path, b: Path) -> dict:
    with a.open(encoding="utf-8", newline="") as fa, b.open(encoding="utf-8", newline="") as fb:
        ra, rb = list(csv.reader(fa)), list(csv.reader(fb))
    if ra[:1] != rb[:1]:
        return {"status": "HEADER_DIFFERENT", "rows_a": len(ra), "rows_b": len(rb)}
    diff_envs: dict[str, int] = {}
    first = None
    for x, y in zip(ra[1:], rb[1:]):
        if x != y:
            diff_envs.setdefault(x[2], int(x[0]))
            first = int(x[0]) if first is None else min(first, int(x[0]))
    status = "NO_DIFFERENCE_IN_STORED_CHANNELS" if len(ra) == len(rb) and not diff_envs else "DIVERGED"
    return {"status": status, "rows_a": len(ra) - 1, "rows_b": len(rb) - 1, "first_diff_step": first,
            "envs_diverged": len(diff_envs), "envs_diverged_first_step": json.dumps(diff_envs, sort_keys=True)}


def reset_rows(steps_csv: Path) -> set[tuple[int, int]]:
    out = set()
    with steps_csv.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["terminated"] == "1" or r["truncated"] == "1":
                out.add((int(r["step"]), int(r["env_id"])))
    return out


def _finite(v: str | None) -> bool:
    try:
        return v not in ("", None) and math.isfinite(float(v))
    except ValueError:
        return False


def check_diag(d: Path, case: str, problems: list[str], chan: list[str], channels: list[dict]) -> None:
    meta = json.loads((d / "diag_meta.json").read_text(encoding="utf-8"))
    unavailable = meta.get("unavailable", {})
    for g in REQUIRED_GROUPS:
        channels.append({"case": case, "item": f"group:{g}", "status": "UNAVAILABLE" if g in unavailable else "RECORDED",
                         "detail": unavailable.get(g, "")})
        if g in unavailable:
            chan.append(f"{case}: channel group {g} unavailable ({unavailable[g]}) — replay continued, channel not acquired")
    names = (meta.get("joints") or {}).get("names") or []
    if len(names) != JOINTS:
        chan.append(f"{case}: diag_meta joints.names has {len(names)} entries, expected {JOINTS}")
    joint_cols = tuple(f"{k}_{j}" for k in JOINT_KINDS for j in names)
    resets = reset_rows(d / "steps.csv")
    keys: set[tuple[int, int]] = set()
    dup = 0
    with gzip.open(d / "diag.csv.gz", "rt", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        want_cols = REQUIRED_COLUMNS + joint_cols
        required = [c for c in want_cols if c in header] + [c for c in header if c.startswith("rew_")]
        bad = {c: 0 for c in required}
        where: dict[str, list[str]] = {c: [] for c in required}
        stale = 0
        for r in reader:
            k = (int(r["step"]), int(r["env_id"]))
            dup += k in keys
            keys.add(k)
            if k in resets:  # reset 행은 다음 episode 첫 상태다 — 결측 검사 밖
                continue
            for c in required:
                v = r.get(c)
                if not _finite(v):
                    bad[c] += 1
                    if len(where[c]) < LOCATIONS_KEPT:
                        where[c].append(f"step={k[0]} env={k[1]} value={v!r}")
            if r.get("contact_fresh") != "1":
                stale += 1
    want = {(s, e) for s in range(1, STEPS + 1) for e in range(ENVS)}
    missing_keys, extra_keys = len(want - keys), len(keys - want)
    if dup or missing_keys or extra_keys:
        problems.append(f"diag {case}: keys duplicate={dup} missing={missing_keys} unexpected={extra_keys}")
    for c in want_cols:
        if c not in header:
            chan.append(f"{case}: required column {c} absent")
    weights = meta.get("reward_weights") or {}
    if not weights:
        chan.append(f"{case}: diag_meta.json has no reward_weights (reward terms cannot be checked)")
    for name in weights:
        if f"rew_{name}" not in header:
            chan.append(f"{case}: reward column rew_{name} absent (registered in diag_meta reward_weights)")
    rows_checked = len(keys - resets)
    for c, n in bad.items():
        if n:
            chan.append(f"{case}: required column {c} missing or non-finite in {n}/{rows_checked} non-reset rows"
                        f" (first: {'; '.join(where[c])})")
        channels.append({"case": case, "item": f"column:{c}", "status": "COMPLETE" if not n else "MISSING_OR_NONFINITE",
                         "detail": f"bad_rows={n} first={' | '.join(where[c])}"})
    if stale:
        chan.append(f"{case}: {stale} non-reset rows with contact_fresh != 1 (contact buffer not proven current)")
    channels.append({"case": case, "item": "keys", "status": f"{len(keys)}/{len(want)}",
                     "detail": f"duplicate={dup} missing={missing_keys} unexpected={extra_keys}"})
    channels.append({"case": case, "item": "contact_fresh", "status": "ALL_NON_RESET_ROWS" if not stale else "STALE",
                     "detail": f"stale_non_reset_rows={stale} reset_rows={len(resets)}"})


def count_frames(p: Path) -> int | None:
    try:
        import cv2
    except ImportError:
        return None
    cap = cv2.VideoCapture(str(p))
    n = 0
    while True:
        ok, _ = cap.read()
        if not ok:
            break
        n += 1
    cap.release()
    return n


def camera_check(d: Path, env: int) -> dict:
    meta = json.loads((d / "camera_meta.json").read_text(encoding="utf-8"))
    out = {"camera_unavailable": json.dumps(meta.get("unavailable", {}), sort_keys=True),
           "camera_expected_env": meta.get("expected_env_index")}
    if meta.get("unavailable") or meta.get("expected_env_index") != env:
        out["camera"] = "CAMERA_PROBE_UNAVAILABLE_OR_WRONG_TARGET"
        return out
    resets = {s for s, e in reset_rows(d / "steps.csv") if e == env}
    with (d / "camera.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    evaluated = passed = near = 0
    prev = None
    for r in rows:
        s = int(r["step"])
        cur = r
        if s >= CAM_SKIP_STEPS and s not in resets and (s - 1) not in resets and prev is not None:
            evaluated += 1
            ok = False
            if r["cfg_env_index"] == str(env) and _finite(r["implied_origin_x"]):
                ox, oy = float(r["implied_origin_x"]), float(r["implied_origin_y"])
                for ref in (r, prev):
                    if _finite(ref["target_root_x"]) and \
                            math.hypot(float(ref["target_root_x"]) - ox, float(ref["target_root_y"]) - oy) <= CAM_DIST_M:
                        ok = True
            passed += ok
            if _finite(r["other_near_dist_xy"]) and float(r["other_near_dist_xy"]) <= OTHER_NEAR_M:
                near += 1
        prev = cur
    frac = passed / evaluated if evaluated else 0.0
    out.update(camera_rows=len(rows), camera_rows_evaluated=evaluated, camera_rows_on_target=passed,
               camera_on_target_frac=round(frac, 4),
               other_robot_within_030m_frac=round(near / evaluated, 4) if evaluated else None,
               camera="CAMERA_ON_TARGET" if evaluated and frac >= CAM_PASS_FRAC else "CAMERA_NOT_ON_TARGET")
    return out


def check_video(h: Path, case: str, env: int, listed: set[str]) -> dict:
    d = video_dir(h, case, env)
    rel = d.relative_to(h).as_posix()
    rec: dict = {"case": case, "env_index": env}
    status_line = ""
    vs = h / "video/VIDEO_STATUS.txt"
    if vs.is_file():
        status_line = next((l for l in vs.read_text(encoding="utf-8").splitlines()
                            if l.startswith(f"{case} env{env} ")), "")
    rec["runner_status"] = status_line
    missing = [f for f in VIDEO_FILES if not (d / f).is_file() or f"{rel}/{f}" not in listed]
    if missing:
        rec.update(video="VIDEO_NOT_ACQUIRED", reason=f"missing or unlisted: {', '.join(missing)}")
        return rec
    ident = json.loads((d / "video_identity.json").read_text(encoding="utf-8"))
    if ident.get("model_sha256") != MODEL_SHA or ident.get("env_sha256") != ENV_SHA or ident.get("env_index") != env:
        rec.update(video="VIDEO_NOT_ACQUIRED", reason=f"video identity mismatch {ident}")
        return rec
    if "EVAL_RC=0" not in (d / "STATUS.txt").read_text(encoding="utf-8"):
        rec.update(video="VIDEO_NOT_ACQUIRED", reason="video run evaluator did not complete")
        return rec
    frames = count_frames(d / "video.mp4")
    rec["frames"] = frames
    if frames is None:
        rec.update(video="VIDEO_CAMERA_UNVERIFIED", reason="cv2 unavailable: frame count not checked")
        return rec
    if not FRAMES_MIN <= frames <= FRAMES_MAX:
        rec.update(video="VIDEO_NOT_ACQUIRED", reason=f"frames {frames} outside {FRAMES_MIN}-{FRAMES_MAX}")
        return rec
    rec.update(camera_check(d, env))
    if rec["camera"] != "CAMERA_ON_TARGET":
        rec.update(video="VIDEO_CAMERA_UNVERIFIED", reason=rec["camera"])
        return rec
    plain = run_dir(h, "plain", SEED, case) / "steps.csv"
    cmp = compare_steps(d / "steps.csv", plain) if plain.is_file() else {"status": "PLAIN_MISSING"}
    rec["steps_vs_plain"] = cmp["status"]
    rec["video"] = "VIDEO_ENV_MATCHED" if cmp["status"] == "NO_DIFFERENCE_IN_STORED_CHANNELS" else "VIDEO_ENV_OWN_RUN_ONLY"
    rec["reason"] = ("filmed robot is the same env of the diag replay" if rec["video"] == "VIDEO_ENV_MATCHED"
                     else "video rollout differs from plain: tie the video only to its own steps.csv")
    return rec


def open_target(target: Path, out: Path) -> tuple[Path | None, str, list[str]]:
    """ZIP 이면 sidecar SHA 대조 후 풀어서 KEEP 폴더를 돌려준다.  폴더면 그대로(zip 미검사)."""
    if target.is_dir():
        return target, "ZIP_NOT_CHECKED", []
    probs: list[str] = []
    side = target.with_name(target.name + ".sha256")
    if not target.is_file():
        return None, "ZIP_MISSING", [f"result ZIP missing: {target}"]
    if not side.is_file():
        return None, "ZIP_SIDECAR_MISSING", [f"sidecar missing: {side}"]
    want = side.read_text(encoding="utf-8").split()[0].lower()
    if sha(target) != want:
        return None, "ZIP_SHA_MISMATCH", [f"result ZIP SHA {sha(target)} != sidecar {want}"]
    dest = out / "extracted"
    if dest.exists():
        shutil.rmtree(dest)
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None:
            return None, "ZIP_CRC_FAILURE", ["result ZIP CRC failure"]
        for n in z.namelist():
            if n.startswith("/") or ".." in Path(n).parts or not n.startswith(KEEP_DIR_NAME + "/"):
                probs.append(f"unsafe or foreign ZIP entry: {n}")
        if probs:
            return None, "ZIP_UNSAFE", probs
        z.extractall(dest)
    return dest / KEEP_DIR_NAME, "ZIP_SHA_VERIFIED", []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--stored", default=str(STORED))
    a = ap.parse_args(argv)
    out, stored = Path(a.out), Path(a.stored)
    out.mkdir(parents=True, exist_ok=True)
    h, zip_state, problems = open_target(Path(a.target), out)
    chan: list[str] = []
    channels: list[dict] = []
    videos: list[dict] = []
    repro: list[dict] = []
    listed: set[str] = set()
    if h is not None:
        sums = h / "SHA256SUMS.txt"
        if not sums.is_file():
            problems.append("SHA256SUMS.txt missing")
        else:
            for line in sums.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                digest, name = line.split(None, 1)
                name = name.lstrip("*").removeprefix("./")
                listed.add(name)
                p = h / name
                if not p.is_file() or sha(p) != digest:
                    problems.append(f"sha mismatch or missing: {name}")
        for name in required_files():
            if not (h / name).is_file():
                problems.append(f"required file missing: {name}")
            elif name not in listed:
                problems.append(f"required file not in SHA256SUMS: {name}")
        status = (h / "RESULT_STATUS.txt").read_text(encoding="utf-8") if (h / "RESULT_STATUS.txt").is_file() else ""
        if "COLLECTION_STATUS=COMPLETE_4_OF_4" not in status:
            problems.append(f"collection not complete: {status.strip()!r}")
        ident_p = h / "meta/identity.json"
        ident = json.loads(ident_p.read_text(encoding="utf-8")) if ident_p.is_file() else {}
        for key, want in (("model_sha256", MODEL_SHA), ("env_sha256", ENV_SHA), ("evaluator_sha256", EVALUATOR_SHA)):
            if ident.get(key) != want:
                problems.append(f"identity {key}={ident.get(key)!r} != {want}")
        for label, seed, case in RUNS:
            d = run_dir(h, label, seed, case)
            st = (d / "STATUS.txt").read_text(encoding="utf-8") if (d / "STATUS.txt").is_file() else ""
            if "EVAL_RC=0" not in st:
                problems.append(f"{label} {case}: evaluator STATUS {st.strip()!r}")
            if label == "diag" and all((d / f).is_file() for f in DIAG_FILES + ("steps.csv",)):
                check_diag(d, case, problems, chan, channels)
        pairs = []
        for case in CASES:
            pairs += [(f"plain_vs_stored:{case}", run_dir(h, "plain", SEED, case) / "steps.csv",
                       stored / f"seed_{SEED}" / case / "steps.csv", True),
                      (f"diag_vs_plain:{case}", run_dir(h, "diag", SEED, case) / "steps.csv",
                       run_dir(h, "plain", SEED, case) / "steps.csv", True)]
        for case, env in VIDEOS:
            pairs.append((f"video_vs_plain:{case}_env{env}", video_dir(h, case, env) / "steps.csv",
                          run_dir(h, "plain", SEED, case) / "steps.csv", False))
        for name, x, y, needed in pairs:
            if x.is_file() and y.is_file():
                repro.append({"pair": name, **compare_steps(x, y)})
            else:
                repro.append({"pair": name, "status": "MISSING"})
                if needed:
                    problems.append(f"repro input missing: {name}")
        for case, env in VIDEOS:
            videos.append(check_video(h, case, env, listed))
    artifact = "ARTIFACT_VERIFIED" if not problems else "ARTIFACT_NOT_VERIFIED"
    channel_state = "DIAG_CHANNELS_COMPLETE" if not chan else "DIAG_CHANNELS_INCOMPLETE"
    videos_ok = bool(videos) and all(v["video"] in VIDEO_OK for v in videos)
    if problems:
        code, shutdown = 1, "DO_NOT_SHUTDOWN"
    elif chan or not videos_ok or zip_state != "ZIP_SHA_VERIFIED":
        code, shutdown = 3, "EXCEPTION_DECISION_REQUIRED"
    else:
        code, shutdown = 0, "OK"
    evidence = {}
    if h is not None:
        evidence = {
            "diag_csv": {c: (run_dir(h, "diag", SEED, c) / "diag.csv.gz").is_file() for c in CASES},
            "identity_json": (h / "meta/identity.json").is_file(),
            "launcher_snapshot": (h / "launcher.snapshot.log").is_file(),
            "logs": sorted(p.name for p in (h / "logs").glob("*.log")) if (h / "logs").is_dir() else []}
    verdict = {"zip": zip_state, "artifact": artifact, "problems": problems, "channels": channel_state,
               "channel_problems": chan,
               "video": {f"{v['case']}_env{v['env_index']}": v["video"] for v in videos},
               "shutdown": shutdown,
               "collection": "COMPLETE" if code == 0 else "PARTIAL_NOT_COMPLETE — do not report as complete collection or diagnostic success",
               "exception_evidence": evidence,
               "repro": {r["pair"]: r["status"] for r in repro},
               "repro_meaning": "no difference in stored channels at stored precision; not a proof of no interference"}
    for name, data in (("REPRO.csv", repro), ("CHANNELS_RECORDED.csv", channels), ("VIDEO_CHECK.csv", videos)):
        cols: list[str] = []
        for r in data:
            cols += [k for k in r if k not in cols]
        with (out / name).open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols or ["empty"], lineterminator="\n")
            w.writeheader()
            w.writerows(data)
    (out / "HARVEST_VERDICT.json").write_text(json.dumps(verdict, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: verdict[k] for k in ("zip", "artifact", "channels", "video", "shutdown")}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
