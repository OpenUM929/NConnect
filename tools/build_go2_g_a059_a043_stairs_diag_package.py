"""G-A059 A043 계단 진단 재생 패키지 빌더 (2026-10-01).  학습 없음 · 보상 변경 없음.

G-A056 빌더(tools/build_go2_a043_diag_replay_package.py)의 입력 검사·파일 배치·ZIP 규칙을 그대로 쓰고
case·영상·문구만 바꿨다. G-A052·G-A056 빌더와 발행물은 건드리지 않는다.
목적: 15cm 계단을 가장 많이 오르는 A043(판정 없이 ≥2단 46/96)에서 성공 로봇의 발 들기 높이와 몸높이를 처음 잰다.
계획 upload/plan/GO2_G_A059_A043_STAIRS_DIAG_PLAN_20261001.md.

입력  G-A056 빌더의 a043_source()(G-A043 서버 평가 바이트), G-A043 iter 900 정책·env.yaml, 계측 v2·카메라 모듈.
러너  workspace/training/quadruped/server_run_go2_a043_stairs_diag_replay.sh
출력  upload/G-A059/current/ 의 ZIP·SHA·실행 안내·CURRENT_UPLOAD·UPLOAD_MANIFEST, history/<RELEASE_ID>/ 사본,
      UPLOAD_HISTORY.tsv 한 줄.  같은 입력이면 ZIP 바이트가 같다(고정 시각·정렬).

    python -B tools/build_go2_g_a059_a043_stairs_diag_package.py            # 빌드·발행
    python -B tools/build_go2_g_a059_a043_stairs_diag_package.py --check    # 다시 빌드해 발행본과 바이트 비교만
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_go2_a043_diag_replay_package as base  # noqa: E402

ROOT = base.ROOT
GO2 = base.GO2
A043_KEEP = base.A043_KEEP
MODEL_SHA, ENV_SHA, EVALUATOR_SHA = base.MODEL_SHA, base.ENV_SHA, base.EVALUATOR_SHA
WORK_ID = "G-A059"
EDITION = "v1"
ZIP_NAME = f"GO2_G_A059_a043_stairs_diag_replay_{EDITION}.zip"
RELEASE_ID = f"20261001_a043_stairs_diag_replay_{EDITION}"
PKG = "go2_g_a059"
KEEP_DIR_NAME = "go2_g_a059_a043_stairs_diag_replay"
RESULT_ZIP_NAME = "GO2_G_A059_RESULT.zip"
DONE_MARKER = "[DONE] GO2_G_A059_RESULT_READY"
GUIDE_NAME = "GO2_G_A059_ONE_COMMAND_RUN_GUIDE.txt"
UPLOAD = GO2 / "upload" / WORK_ID
PLAN = "workspace/training/quadruped/upload/plan/GO2_G_A059_A043_STAIRS_DIAG_PLAN_20261001.md"
RUNNER = "server_run_go2_a043_stairs_diag_replay.sh"
FIXED = (2026, 10, 1, 0, 0, 0)
SEED = 101
CASES = ("stairs_15_down", "stairs_10_down")
# seed 101 15cm, smallest env id in each internal-judgement group (tools/go2_stairs_tread_height.py PER_ENV):
# clean climb 1, judged before 2 steps 0, judged after 2 steps 4, judged under 2 steps 12
VIDEOS = (("stairs_15_down", 1), ("stairs_15_down", 0), ("stairs_15_down", 4), ("stairs_15_down", 12))

sha, need, lf = base.sha, base.need, base.lf


G_A056_ZIP = GO2 / "upload/G-A056/current/GO2_G_A056_a043_diag_replay_v2.zip"


def same_as_g_a056(name: str, inner: str) -> bytes:
    """Measurement module bytes: the working copy with CRLF undone (git core.autocrlf rewrites the
    checkout), required to equal the bytes G-A056 v2 shipped, so the ruler is the one already used."""
    b = (GO2 / name).read_bytes().replace(b"\r\n", b"\n")
    with zipfile.ZipFile(G_A056_ZIP) as z:
        shipped = z.read(f"go2_g_a056/{inner}")
    need(b == shipped, f"{name} differs from the bytes shipped in G-A056 v2")
    return lf(b, name)


def payload() -> dict[str, tuple[bytes, int]]:
    src = base.a043_source()
    helper = src.pop("_package_go2_result.py")
    model = (A043_KEEP / "training/model_iter900.pt").read_bytes()
    env = (A043_KEEP / "training/env.yaml").read_bytes()
    # The working copy of this env.yaml was found with CRLF line ends (2026-10-01); converting back to LF
    # gives exactly the recorded SHA, so the original bytes are restored here and checked, not edited on disk.
    env = env.replace(b"\r\n", b"\n")
    need(sha(model) == MODEL_SHA and sha(env) == ENV_SHA, "G-A043 iter 900 policy/env SHA mismatch")
    pin = (A043_KEEP / "training/CHECKPOINT_PIN.txt").read_text(encoding="utf-8")
    need(f"EVAL_CHECKPOINT_SHA={MODEL_SHA}" in pin and "EVAL_CHECKPOINT_ITER=900" in pin, "CHECKPOINT_PIN mismatch")
    ident = json.loads((A043_KEEP / "evaluation/candidate/identity.json").read_text(encoding="utf-8"))
    need(ident["model_sha256"] == MODEL_SHA and ident["env_sha256"] == ENV_SHA
         and ident["evaluator_sha256"] == EVALUATOR_SHA, "G-A043 evaluation identity does not match")
    mods = {n: same_as_g_a056(n, where) for n, where in (
        ("go2_eval_diag_v2.py", "diag/go2_eval_diag_v2.py"),
        ("go2_eval_telemetry_diag_wrapper_v2.py", "diag/go2_eval_telemetry.py"),
        ("go2_eval_camera_probe.py", "video/go2_eval_camera_probe.py"),
        ("go2_eval_telemetry_camera_wrapper.py", "video/go2_eval_telemetry.py"))}
    runner = lf((GO2 / RUNNER).read_bytes().replace(b"\r\n", b"\n"), "runner")
    files: dict[str, tuple[bytes, int]] = {}
    for rel, b in src.items():
        files[f"plain/{rel}"] = (b, 0o644)
        if rel != "go2_eval_telemetry.py":
            files[f"diag/{rel}"] = (b, 0o644)
            files[f"video/{rel}"] = (b, 0o644)
    for root in ("diag", "video"):
        files[f"{root}/go2_eval_telemetry_v6.py"] = (src["go2_eval_telemetry.py"], 0o644)
    files["diag/go2_eval_telemetry.py"] = (mods["go2_eval_telemetry_diag_wrapper_v2.py"], 0o644)
    files["diag/go2_eval_diag_v2.py"] = (mods["go2_eval_diag_v2.py"], 0o644)
    files["video/go2_eval_telemetry.py"] = (mods["go2_eval_telemetry_camera_wrapper.py"], 0o644)
    files["video/go2_eval_camera_probe.py"] = (mods["go2_eval_camera_probe.py"], 0o644)
    files["policy/model_best.pt"] = (model, 0o644)
    files["policy/env.yaml"] = (env, 0o644)
    files[RUNNER] = (runner, 0o755)
    files["package_go2_result.py"] = (helper, 0o644)
    run_config = (
        f"WORK_ID={WORK_ID}\nKEEP_DIR_NAME={KEEP_DIR_NAME}\nRESULT_ZIP_NAME={RESULT_ZIP_NAME}\n"
        f"TMUX_NAME={PKG}\nDONE_MARKER='{DONE_MARKER}'\nMODEL_SHA={MODEL_SHA}\nENV_SHA={ENV_SHA}\n"
        f"EXPECTED_EVALUATOR_SHA={EVALUATOR_SHA}\n")
    files["run_config.env"] = (run_config.encode(), 0o644)
    experiment = {
        "work_id": WORK_ID, "kind": "diagnostic_replay_no_training", "edition": EDITION, "plan": PLAN,
        "request": "사용자 2026-10-01: 계단 성공 상태(발 들기 높이·몸높이) 기준을 정의하기 위한 진단 재생",
        "policy": {"source_run": "G-A043", "checkpoint": "iter 900", "model_sha256": MODEL_SHA, "env_sha256": ENV_SHA},
        "reward_change": None, "training": None,
        "evaluator": {"schema": 6, "sha256": EVALUATOR_SHA,
                      "diag_module_sha256": sha(mods["go2_eval_diag_v2.py"]),
                      "diag_wrapper_sha256": sha(mods["go2_eval_telemetry_diag_wrapper_v2.py"]),
                      "camera_probe_sha256": sha(mods["go2_eval_camera_probe.py"]),
                      "camera_wrapper_sha256": sha(mods["go2_eval_telemetry_camera_wrapper.py"])},
        "runs": [{"label": label, "case": c, "seed": SEED} for c in CASES for label in ("plain", "diag")],
        "videos": [{"case": c, "seed": SEED, "env_index": e, "video_steps": 1000} for c, e in VIDEOS],
        "interpretation_limits": [
            "identical steps.csv means no difference in stored channels at stored precision, not proof of no interference",
            "foot height above a tread = foot pos_z - lowest platform - foot radius; the nearest scanner ray can be ~0.07 m away at an edge",
            "groups are internal posture-gate judgements (stored seed 101 run), not video-confirmed falls; one policy, one evaluation seed",
            "values of successful robots describe success; they are not shown to be a causal requirement",
            "a camera probe on target shows the recording camera's pose followed the env; other robots can appear in frame"],
        "readers": ["tools/verify_go2_g_a059_harvest.py", "tools/go2_g_a059_stairs_foot_readout.py"],
        "decides": "nothing automatically; defines the observed foot-lift and body-height reference used to read later runs",
    }
    files["experiment.json"] = ((json.dumps(experiment, indent=1, ensure_ascii=False) + "\n").encode(), 0o644)
    readme = (f"G-A059 A043 stairs diagnostic replay — no training, no reward change.\n"
              f"Replays G-A043 iter 900 on stairs_15_down and stairs_10_down seed {SEED} (plain and diag), then films\n"
              f"four robots on stairs_15_down with the viewer pinned to their env index.\n"
              f"Run: bash /workspace/{PKG}/{RUNNER}\nPlan: {PLAN}\n")
    files["README.txt"] = (readme.encode(), 0o644)
    sums = "".join(f"{sha(b)}  {name}\n" for name, (b, _) in sorted(files.items()))
    files["PACKAGE_SHA256SUMS.txt"] = (sums.encode(), 0o644)
    return files


def build_zip(files: dict[str, tuple[bytes, int]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, (b, mode) in sorted(files.items()):
            info = zipfile.ZipInfo(f"{PKG}/{name}", date_time=FIXED)
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, b)
    data = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        need(z.testzip() is None, "ZIP CRC failure")
    return data


def guide(zip_sha: str) -> str:
    return f"""GO2 G-A059 실행 안내 — A043 계단 진단 재생 · 한 파일 · 한 명령 · 결과 ZIP 하나
============================================================

학습하지 않는다. 보상을 바꾸지 않는다. G-A043 iter 900 정책(model {MODEL_SHA[:12]}…)을
G-A043을 잰 평가기(schema 6, {EVALUATOR_SHA[:12]}…)로 계단 두 case 다시 재생하고, 같은 재생에 읽기 전용 진단 채널
(몸통·발 위치/속도/접촉력·발 아래 지형·action·보상 항·관절)을 붙인 뒤, 미리 고른 로봇 네 대를 영상으로 찍는다.
목적: 계단을 오르는 로봇이 모서리에서 발을 얼마나 들고 몸을 얼마나 유지하는지 처음 잰다.
계획 {PLAN}
실행 위치(서버 또는 다른 PC)와 실행 여부는 사용자 결정이다.

1. 업로드 — 이 파일 하나만 올린다
   {ZIP_NAME}
   SHA256 {zip_sha}
   경로 /workspace/{ZIP_NAME}

2. 실행 — 한 줄
   unzip -oq /workspace/{ZIP_NAME} -d /workspace && bash /workspace/{PKG}/{RUNNER}

   진행 보기: tmux attach -t {PKG}
   이전 결과가 남아 있으면 멈춘다. 내려받은 뒤라면 GO2_DISCARD_PREVIOUS=1 을 앞에 붙인다.
   다른 PC(Windows)에서는 G-A058 때와 같은 방식(/workspace 마운트·isaaclab.sh 래퍼)으로 돌린다. 러너 바이트는 바꾸지 않는다.

3. 무엇이 도는가 — play.py 여덟 번
   ① plain stairs_15_down seed {SEED}   ② diag stairs_15_down seed {SEED}
   ③ plain stairs_10_down seed {SEED}   ④ diag stairs_10_down seed {SEED}
   (case 이름은 down 이지만 실제로는 오른다)
   ⑤~⑧ 영상: stairs_15_down env 1(판정 없이 오름)·0(≥2단 전 판정)·4(≥2단 후 판정)·12(못 오르고 판정)
      (32 env, 같은 명령 + --video --video_length 1000 --enable_cameras + env.viewer.env_index=<env>)
   시간 [추정]: 서버 기준 ①~④ 약 2~3분, ⑤~⑧ 4~8분, 패키징 1분 이내. 다른 PC는 실측 없음(학습 없음).

4. 완료 표식과 내려받을 것
   {DONE_MARKER}
   /workspace/_keep/{RESULT_ZIP_NAME}
   /workspace/_keep/{RESULT_ZIP_NAME}.sha256
   러너가 도중에 죽으면 표식 없이 부분 ZIP(COLLECTION_STATUS=INCOMPLETE_CRASH)이 남는다 —
   표식을 기다리지 말고 launcher.log 와 RUNNER_STATUS.txt 를 읽는다.

5. SHUTDOWN GATE — 로컬 검증기 하나가 아래를 모두 본다. 종료코드 하나로 끄지 않는다.
   a. 결과 ZIP 과 .sha256 을 로컬로 내려받는다.
   b. python -B tools/verify_go2_g_a059_harvest.py <내려받은 {RESULT_ZIP_NAME}>
      종료코드 0 / shutdown=OK — ZIP·artifact·채널·영상 모두 통과. 끈다.
      종료코드 3 / shutdown=EXCEPTION_DECISION_REQUIRED — ZIP·artifact 는 통과, 채널 또는 영상 미완료.
                   끄지 않는다. 같은 장비에서 같은 case 재실행으로 채울 수 있는지 판단하고, 못 채우면
                   ARTIFACT_MANAGEMENT.md 의 G-A059 항목에 예외 종료 결정을 적고 끈다. '회수 완결'로 쓰지 않는다.
      종료코드 1 / shutdown=DO_NOT_SHUTDOWN — ZIP SHA 또는 artifact 실패. 끄지 않는다. 다시 회수한다.
   c. 판독: python -B tools/go2_g_a059_stairs_foot_readout.py <압축 해제한 {KEEP_DIR_NAME} 폴더>
   d. 영상 판정: 필수(높이 채널만 걸린 판정이 실제 엎드림인지 보는 유일한 자료). 학습 report: 비해당(학습 없음).
   e. 미측정: G1~G7 점수, 다른 seed, 다른 정책, 보상 변경 효과.
"""


def publish(data: bytes) -> str:
    zsha = sha(data)
    cur, hist = UPLOAD / "current", UPLOAD / "history" / RELEASE_ID
    hist.mkdir(parents=True, exist_ok=True)
    cur.mkdir(parents=True, exist_ok=True)
    g = guide(zsha).encode()
    for name, b in ((ZIP_NAME, data), (GUIDE_NAME, g)):
        p = hist / name
        need(not p.exists() or p.read_bytes() == b, f"immutable history conflict: {p}")
    for d in (cur, hist):
        for name, b in ((ZIP_NAME, data), (GUIDE_NAME, g)):
            (d / name).write_bytes(b)
            (d / f"{name}.sha256").write_text(f"{sha(b)}  {name}\n", encoding="utf-8", newline="\n")
    (cur / "CURRENT_UPLOAD.txt").write_text(
        f"CURRENT GO2 UPLOAD — {WORK_ID} (A043 stairs diagnostic replay, no training)\n\nUPLOAD ONLY THIS ONE FILE\n"
        f"1. {cur / ZIP_NAME}\n   SHA256 {zsha}\n\n절차는 같은 폴더의 {GUIDE_NAME}.\n"
        f"실행 위치와 실행 여부는 사용자 결정 사항이다(승인 전 실행 금지).\n\nRELEASE_ID {RELEASE_ID}\nSTATUS ARTIFACT_VERIFIED\n",
        encoding="utf-8", newline="\n")
    manifest = {"experiment_id": WORK_ID, "release_id": RELEASE_ID, "status": "ARTIFACT_VERIFIED",
                "published_at_utc": "2026-10-01T00:00:00+00:00",
                "note": "G-A043 iter 900 stairs diagnostic replay, 4 evaluation + 4 video play.py runs, no training, no reward change.",
                "support_files": [GUIDE_NAME],
                "upload_files": [{"name": ZIP_NAME, "server_path": f"/workspace/{ZIP_NAME}", "sha256": zsha}]}
    (cur / "UPLOAD_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")
    tsv = UPLOAD / "UPLOAD_HISTORY.tsv"
    row = "\t".join(["2026-10-01T00:00:00+00:00", WORK_ID, RELEASE_ID, "ARTIFACT_VERIFIED", ZIP_NAME, zsha,
                     "experiment.json(in ZIP)", "", "A043 stairs diagnostic replay, no training"]) + "\n"
    head = "published_at_utc\texperiment_id\trelease_id\tstatus\tengine_file\tengine_sha256\tspec_file\tspec_sha256\tnote\n"
    old = tsv.read_text(encoding="utf-8") if tsv.exists() else head
    if row not in old:
        tsv.write_text(old + row, encoding="utf-8", newline="\n")
    return zsha


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    data = build_zip(payload())
    if a.check:
        cur = UPLOAD / "current" / ZIP_NAME
        same = cur.is_file() and cur.read_bytes() == data
        print(f"{'REBUILD_IDENTICAL' if same else 'REBUILD_DIFFERENT'} {sha(data)}")
        return 0 if same else 1
    print(ZIP_NAME, publish(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
