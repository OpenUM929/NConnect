"""G-A056 A043 진단 재생 패키지 빌더 (2026-09-28).  학습 없음 · 보상 변경 없음.

A052 빌더(tools/build_go2_diag_replay_package.py)와 발행물(upload/G-A052/)은 건드리지 않는다.

입력
  G-A043 캠페인 ZIP 안 staged ZIP 의 candidate/ 소스 바이트(서버에서 A043 을 평가한 바로 그 바이트, train.py 제외)
  G-A043 iter 900 정책 model_iter900.pt · env.yaml (_keep 원본, 평가 identity.json·CHECKPOINT_PIN 과 대조)
  계측: go2_eval_diag_v2.py + go2_eval_telemetry_diag_wrapper_v2.py (diag 루트),
        go2_eval_camera_probe.py + go2_eval_telemetry_camera_wrapper.py (video 루트)
  러너: workspace/training/quadruped/server_run_go2_a043_diag_replay.sh
출력  upload/G-A056/current/ 의 ZIP·SHA·실행 안내·CURRENT_UPLOAD·UPLOAD_MANIFEST, history/<RELEASE_ID>/ 사본,
      UPLOAD_HISTORY.tsv 한 줄.  같은 입력이면 ZIP 바이트가 같다(고정 시각·정렬).

    python -B tools/build_go2_a043_diag_replay_package.py            # 빌드·발행
    python -B tools/build_go2_a043_diag_replay_package.py --check    # 다시 빌드해 발행본과 바이트 비교만
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
A043_ZIP = GO2 / "upload/G-A043/current/GO2_G_A043_a033_lin_vel_z_m15_one_command.zip"
A043_ZIP_SHA = "68480a13f96bf7032462ce852238fcbbaaeb726e66638a9d7502cbc154dcda45"
A043_STAGED = "go2_campaign_g_a043/arms/GO2_G_A043_a033_lin_vel_z_m15_staged.zip"
A043_STAGED_SHA = "9b0b0d3a7bac9779374292dfd1a0c85281200179e7b3ef255f159231fb2afb03"
A043_KEEP = ROOT / "workspace/_keep/go2_g_a043_a033_lin_vel_z_m15"
MODEL_SHA = "4d9236818f998bdb87efaea4acfa1e4c861b0d87947229e88f9175495066bd6b"
ENV_SHA = "9af8f18a084f3008d6a6a3563a3c56091d9eb8236d42db6abbb06c0fe926a06d"
EVALUATOR_SHA = "353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84"
WORK_ID = "G-A056"
EDITION = "v2"
SUPERSEDES = ("v1", "7d4d6fe7a61cffd42b5fd02967cee7fd8c4a92553e0a40a519146d112bae8398")
ZIP_NAME = f"GO2_G_A056_a043_diag_replay_{EDITION}.zip"
RELEASE_ID = f"20260928_a043_diag_replay_{EDITION}"
PKG = "go2_g_a056"
KEEP_DIR_NAME = "go2_g_a056_a043_diag_replay"
RESULT_ZIP_NAME = "GO2_G_A056_RESULT.zip"
DONE_MARKER = "[DONE] GO2_G_A056_RESULT_READY"
GUIDE_NAME = "GO2_G_A056_ONE_COMMAND_RUN_GUIDE.txt"
UPLOAD = GO2 / "upload" / WORK_ID
PLAN = "workspace/training/quadruped/upload/plan/GO2_G_A056_A043_DIAG_REPLAY_PLAN_20260928.md"
RUNNER = "server_run_go2_a043_diag_replay.sh"
FIXED = (2026, 9, 28, 0, 0, 0)
VIDEOS = (("rough_lateral", 5), ("rough_lateral", 11), ("combined_yaw_right", 3), ("combined_yaw_right", 16))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise SystemExit(f"[FAIL] {msg}")


def a043_source() -> dict[str, bytes]:
    outer = A043_ZIP.read_bytes()
    need(sha(outer) == A043_ZIP_SHA, "G-A043 release ZIP SHA changed")
    with zipfile.ZipFile(io.BytesIO(outer)) as z:
        staged = z.read(A043_STAGED)
    need(sha(staged) == A043_STAGED_SHA, "G-A043 staged arm ZIP SHA changed")
    out = {}
    with zipfile.ZipFile(io.BytesIO(staged)) as z:
        for n in z.namelist():
            pre = "go2_g_a043/candidate/"
            if n.startswith(pre) and not n.endswith("/") and not n.endswith("train.py"):
                out[n[len(pre):]] = z.read(n)
        out["_package_go2_result.py"] = z.read("go2_g_a043/package_go2_result.py")
    need(sha(out["go2_eval_telemetry.py"]) == EVALUATOR_SHA, "G-A043 evaluator bytes are not the measured ruler")
    return out


def lf(b: bytes, name: str) -> bytes:
    need(b"\r" not in b, f"{name} has CR bytes")
    return b


def payload() -> dict[str, tuple[bytes, int]]:
    src = a043_source()
    helper = src.pop("_package_go2_result.py")
    model = (A043_KEEP / "training/model_iter900.pt").read_bytes()
    env = (A043_KEEP / "training/env.yaml").read_bytes()
    need(sha(model) == MODEL_SHA and sha(env) == ENV_SHA, "G-A043 iter 900 policy/env SHA mismatch")
    pin = (A043_KEEP / "training/CHECKPOINT_PIN.txt").read_text(encoding="utf-8")
    need(f"EVAL_CHECKPOINT_SHA={MODEL_SHA}" in pin and "EVAL_CHECKPOINT_ITER=900" in pin, "CHECKPOINT_PIN mismatch")
    ident = json.loads((A043_KEEP / "evaluation/candidate/identity.json").read_text(encoding="utf-8"))
    need(ident["model_sha256"] == MODEL_SHA and ident["env_sha256"] == ENV_SHA
         and ident["evaluator_sha256"] == EVALUATOR_SHA, "G-A043 evaluation identity does not match")
    mods = {n: lf((GO2 / n).read_bytes(), n) for n in (
        "go2_eval_diag_v2.py", "go2_eval_telemetry_diag_wrapper_v2.py",
        "go2_eval_camera_probe.py", "go2_eval_telemetry_camera_wrapper.py")}
    runner = lf((GO2 / RUNNER).read_bytes(), "runner")
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
        f"TMUX_NAME=go2_g_a056\nDONE_MARKER='{DONE_MARKER}'\nMODEL_SHA={MODEL_SHA}\nENV_SHA={ENV_SHA}\n"
        f"EXPECTED_EVALUATOR_SHA={EVALUATOR_SHA}\n")
    files["run_config.env"] = (run_config.encode(), 0o644)
    experiment = {
        "work_id": WORK_ID, "kind": "diagnostic_replay_no_training", "edition": EDITION, "plan": PLAN,
        "request": "Codex 2026-09-28 제작·검증 지시 (A043 진단 재생)",
        "policy": {"source_run": "G-A043", "checkpoint": "iter 900", "model_sha256": MODEL_SHA, "env_sha256": ENV_SHA},
        "reward_change": None, "training": None,
        "evaluator": {"schema": 6, "sha256": EVALUATOR_SHA,
                      "diag_module_sha256": sha(mods["go2_eval_diag_v2.py"]),
                      "diag_wrapper_sha256": sha(mods["go2_eval_telemetry_diag_wrapper_v2.py"]),
                      "camera_probe_sha256": sha(mods["go2_eval_camera_probe.py"]),
                      "camera_wrapper_sha256": sha(mods["go2_eval_telemetry_camera_wrapper.py"])},
        "runs": [{"label": "plain", "case": "rough_lateral", "seed": 202},
                 {"label": "diag", "case": "rough_lateral", "seed": 202},
                 {"label": "plain", "case": "combined_yaw_right", "seed": 202},
                 {"label": "diag", "case": "combined_yaw_right", "seed": 202}],
        "videos": [{"case": c, "seed": 202, "env_index": e, "video_steps": 1000} for c, e in VIDEOS],
        "interpretation_limits": [
            "identical steps.csv means no difference in stored channels at stored precision, not proof of no interference",
            "computed/applied torque rows are the last physics substep of each step; clipping in earlier substeps is not recorded",
            "contact_time > 0 marks contact, not load support; world foot velocity is not contact-point slip",
            "a camera probe on target shows the recording camera's pose followed the env; with 8 robots per rough tile other robots can appear in frame",
            "an earlier action change is not evidence that the policy caused the lateral acceleration",
            "survivors of the same replay are a comparison group, not a causal control (terrain and gait phase are not matched)"],
        "readers": ["tools/verify_go2_a043_diag_replay_harvest.py", "tools/go2_a043_diag_readout.py"],
        "decides": "nothing automatically; per-event axis A/B values and timings returned to Codex",
        "supersedes": {"edition": SUPERSEDES[0], "sha256": SUPERSEDES[1], "never_run": True,
                       "why": "local contract test: when one joint tensor was missing at attach, v1 also replaced the "
                              "joint names with placeholders; v2 reads names separately so the header keeps real names"},
    }
    files["experiment.json"] = ((json.dumps(experiment, indent=1, ensure_ascii=False) + "\n").encode(), 0o644)
    readme = (f"G-A056 A043 diagnostic replay — no training, no reward change.\n"
              f"Replays G-A043 iter 900 on rough_lateral and combined_yaw_right seed 202 (plain and diag), then films\n"
              f"four robots with the viewer pinned to their env index.\nRun: bash /workspace/{PKG}/{RUNNER}\n"
              f"Plan: {PLAN}\n")
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
    return f"""GO2 G-A056 실행 안내 — A043 진단 재생 · 한 파일 · 한 명령 · 결과 ZIP 하나
============================================================

학습하지 않는다. 보상을 바꾸지 않는다. G-A043 iter 900 정책(model {MODEL_SHA[:12]}…)을
G-A043을 잰 평가기(schema 6, {EVALUATOR_SHA[:12]}…)로 두 case 다시 재생하고, 같은 재생에 읽기 전용 진단 채널
(몸통·발·접촉·지형·action·보상 항·관절 위치/속도/계산 토크/적용 토크)을 붙인 뒤, 미리 고른 로봇 네 대를 영상으로 찍는다.
계획 {PLAN}
서버 실행은 사용자 결정이다.

1. 업로드 — 이 파일 하나만 올린다
   {ZIP_NAME}
   SHA256 {zip_sha}
   서버 경로 /workspace/{ZIP_NAME}

2. 실행 — 한 줄
   unzip -oq /workspace/{ZIP_NAME} -d /workspace && bash /workspace/{PKG}/{RUNNER}

   진행 보기: tmux attach -t go2_g_a056
   이전 결과가 서버에 남아 있으면 멈춘다. 내려받은 뒤라면 GO2_DISCARD_PREVIOUS=1 을 앞에 붙인다.

3. 무엇이 도는가 — play.py 여덟 번
   ① plain rough_lateral seed 202       ② diag rough_lateral seed 202
   ③ plain combined_yaw_right seed 202  ④ diag combined_yaw_right seed 202
   ⑤~⑧ 영상: rough_lateral env 5·11, combined_yaw_right env 3·16 (32 env, 같은 명령 + --video
      --video_length 1000 --enable_cameras + env.viewer.env_index=<env>, 평가기 steps.csv 와 카메라 계측을 함께 기록)
   시간 [추정]: ①~④ 약 2~3분(G-A052 실측 27~31초/회), ⑤~⑧ 4~8분(32 env·1000 step 카메라 실행은 잰 적 없음),
   패키징 1분 이내. 서버 켜진 시간 전체 추정 25~35분(업로드·다운로드·로컬 검증 포함), 계획 예산 45분.
   영상 실패는 러너를 멈추지 않는다(video/VIDEO_STATUS.txt 에 기록). ①~④ 실패는 멈추고 있는 것을 묶는다.

4. 완료 표식과 내려받을 것
   [DONE] GO2_G_A056_RESULT_READY
   /workspace/_keep/{RESULT_ZIP_NAME}
   /workspace/_keep/{RESULT_ZIP_NAME}.sha256
   러너가 도중에 죽으면 표식 없이 부분 ZIP(COLLECTION_STATUS=INCOMPLETE_CRASH)이 남는다 —
   표식을 기다리지 말고 launcher.log 와 RUNNER_STATUS.txt 를 읽는다.

5. SERVER SHUTDOWN GATE — 로컬 검증기 하나가 아래를 모두 본다. 종료코드 하나로 끄지 않는다.
   a. 결과 ZIP 과 .sha256 을 로컬로 내려받는다.
   b. python -B tools/verify_go2_a043_diag_replay_harvest.py <내려받은 {RESULT_ZIP_NAME}>
      검증기는 ZIP SHA(sidecar 대조) → 압축 해제 → artifact(필수 파일·SHA 목록·식별자·진단 키)
      → channels(필수 채널 묶음 7개·필수 열·접촉 갱신; 채널 실패 뒤 재생이 계속된 것은 확보가 아니다)
      → video(영상 네 개: 파일·프레임 수·카메라 계측이 지정 로봇을 따라갔는지·steps.csv 대응)를 따로 판정하고
      HARVEST_VERDICT.json 의 shutdown 에 결론을 적는다.
      종료코드 0 / shutdown=OK — 네 판정 모두 통과. 끈다.
      종료코드 3 / shutdown=EXCEPTION_DECISION_REQUIRED — ZIP·artifact 는 통과, 채널 또는 영상 미완료.
                   **서버를 끄지 않는다.** channel_problems·video 를 읽고 같은 서버에서 복구할 수 있는지 판단한다
                   (같은 case 재실행으로 채워지는가). 복구할 수 없으면 진단 데이터·checkpoint 식별 정보·실패 로그가
                   이미 받은 ZIP 안에 있는지 검증기 출력으로 확인한 뒤, ARTIFACT_MANAGEMENT.md 의 G-A056 항목에
                   예외 종료 결정(미완료 항목·사유·받은 것·unknown 으로 남을 질문)을 적고 끈다.
                   이 경우 '회수 완결'·'진단 성공'으로 쓰지 않는다.
      종료코드 1 / shutdown=DO_NOT_SHUTDOWN — ZIP SHA 또는 artifact 실패. **끄지 않는다.** 다시 회수한다.
   c. 영상 판정: 조건부(Codex 지시 "가능하면"). 학습 report: 비해당(학습 없음, G-A043 원 report 는 로컬 보존본).
   d. 미측정: G1~G7 점수, 다른 seed, 밀침·좌회전·계단, 보상 변경 효과.
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
            p = d / name
            if d == hist and p.exists():
                need(p.read_bytes() == b, f"immutable history conflict: {p}")
            p.write_bytes(b)
            (d / f"{name}.sha256").write_text(f"{sha(b)}  {name}\n", encoding="utf-8", newline="\n")
    (cur / "CURRENT_UPLOAD.txt").write_text(
        f"CURRENT GO2 UPLOAD — {WORK_ID} (A043 diagnostic replay, no training)\n\nUPLOAD ONLY THIS ONE FILE\n"
        f"1. {cur / ZIP_NAME}\n   SHA256 {zsha}\n\n절차는 같은 폴더의 {GUIDE_NAME}.\n"
        f"서버 실행은 사용자 결정 사항이다(승인 전 실행 금지).\n\nRELEASE_ID {RELEASE_ID}\nSTATUS ARTIFACT_VERIFIED\n"
        f"이전 판 {SUPERSEDES[0]}(SHA {SUPERSEDES[1][:12]}…)은 실행 전에 대체됐다 — history 에 불변 보존, 서버에 올리지 않는다.\n",
        encoding="utf-8", newline="\n")
    manifest = {"experiment_id": WORK_ID, "release_id": RELEASE_ID, "status": "ARTIFACT_VERIFIED",
                "published_at_utc": "2026-09-28T00:00:00+00:00",
                "note": f"G-A043 iter 900 diagnostic replay, 4 evaluation + 4 video play.py runs, no training, no reward change. Supersedes {SUPERSEDES[0]} (never run).",
                "support_files": [GUIDE_NAME],
                "upload_files": [{"name": ZIP_NAME, "server_path": f"/workspace/{ZIP_NAME}", "sha256": zsha}]}
    (cur / "UPLOAD_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")
    tsv = UPLOAD / "UPLOAD_HISTORY.tsv"
    row = "\t".join(["2026-09-28T00:00:00+00:00", WORK_ID, RELEASE_ID, "ARTIFACT_VERIFIED", ZIP_NAME, zsha,
                     "experiment.json(in ZIP)", "", "A043 diagnostic replay, no training"]) + "\n"
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
