"""G-A052 진단 재생 패키지 빌더 (2026-09-28).  학습 없음 · 보상 변경 없음.

입력
  G-A048 실행 ZIP의 candidate/ 소스 바이트(서버에 올라가 평가를 만든 바로 그 바이트, train.py 제외)
  G-A048 iter 900 정책 model_iter900.pt · env.yaml (_keep 원본, 평가 identity.json 의 SHA 와 대조)
  계측: workspace/training/quadruped/go2_eval_diag.py, go2_eval_telemetry_diag_wrapper.py
  러너: workspace/training/quadruped/server_run_go2_diag_replay.sh
출력  upload/G-A052/current/ 의 ZIP·SHA·실행 안내·CURRENT_UPLOAD·UPLOAD_MANIFEST, history/<RELEASE_ID>/ 사본,
      UPLOAD_HISTORY.tsv 한 줄.  같은 입력이면 ZIP 바이트가 같다(고정 시각·정렬).

    python -B tools/build_go2_diag_replay_package.py            # 빌드·발행
    python -B tools/build_go2_diag_replay_package.py --check    # 다시 빌드해 발행본과 바이트 비교만
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
A048_ZIP = GO2 / "upload/G-A048/current/GO2_G_A048_a033_lin_vel_z_m125_full69_v1.zip"
A048_ZIP_SHA = "bbbfbb258f4101a01e65f51dd6092df7866ff81a39cc9809c8f602efc659f3bc"
A048_KEEP = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125"
MODEL_SHA = "984e614933f3aae037df260cbf7ee72e7549337435a602ce116d6fc39e7f5ad7"
ENV_SHA = "a19077a984f829f23f1ca87405b9b4fa94ae6c618fedf95ea6bb640992f33a35"
EVALUATOR_SHA = "353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84"
WORK_ID = "G-A052"
EDITION = "v2"
SUPERSEDES = ("v1", "09973af1a5b9e63d6f6679bc6a50eddc0071ead696174bd42f942a4f29c8465f")
ZIP_NAME = f"GO2_G_A052_a048_diag_replay_{EDITION}.zip"
RELEASE_ID = f"20260928_a048_diag_replay_{EDITION}"
PKG = "go2_g_a052"
KEEP_DIR_NAME = "go2_g_a052_a048_diag_replay"
RESULT_ZIP_NAME = "GO2_G_A052_RESULT.zip"
DONE_MARKER = "[DONE] GO2_G_A052_RESULT_READY"
UPLOAD = GO2 / "upload" / WORK_ID
PLAN = "workspace/training/quadruped/upload/plan/GO2_G_A052_DIAG_REPLAY_PLAN_20260928.md"
FIXED = (2026, 9, 28, 0, 0, 0)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise SystemExit(f"[FAIL] {msg}")


def a048_source() -> dict[str, bytes]:
    need(sha(A048_ZIP.read_bytes()) == A048_ZIP_SHA, "G-A048 release ZIP SHA changed")
    out = {}
    with zipfile.ZipFile(A048_ZIP) as z:
        for n in z.namelist():
            pre = "go2_g_a048/candidate/"
            if n.startswith(pre) and not n.endswith("/") and not n.endswith("train.py"):
                out[n[len(pre):]] = z.read(n)
        out["_package_go2_result.py"] = z.read("go2_g_a048/package_go2_result.py")
    need(sha(out["go2_eval_telemetry.py"]) == EVALUATOR_SHA, "G-A048 evaluator bytes are not the measured ruler")
    return out


def lf(b: bytes, name: str) -> bytes:
    need(b"\r" not in b, f"{name} has CR bytes")
    return b


def payload() -> dict[str, tuple[bytes, int]]:
    src = a048_source()
    helper = src.pop("_package_go2_result.py")
    model = (A048_KEEP / "training/model_iter900.pt").read_bytes()
    env = (A048_KEEP / "training/env.yaml").read_bytes()
    need(sha(model) == MODEL_SHA and sha(env) == ENV_SHA, "G-A048 iter 900 policy/env SHA mismatch")
    ident = json.loads((A048_KEEP / "evaluation/candidate/identity.json").read_text(encoding="utf-8"))
    need(ident["model_sha256"] == MODEL_SHA and ident["env_sha256"] == ENV_SHA
         and ident["evaluator_sha256"] == EVALUATOR_SHA, "G-A048 evaluation identity does not match")
    diag_mod = lf((GO2 / "go2_eval_diag.py").read_bytes(), "go2_eval_diag.py")
    wrapper = lf((GO2 / "go2_eval_telemetry_diag_wrapper.py").read_bytes(), "wrapper")
    runner = lf((GO2 / "server_run_go2_diag_replay.sh").read_bytes(), "runner")
    files: dict[str, tuple[bytes, int]] = {}
    for rel, b in src.items():
        files[f"plain/{rel}"] = (b, 0o644)
        if rel != "go2_eval_telemetry.py":
            files[f"diag/{rel}"] = (b, 0o644)
    files["diag/go2_eval_telemetry_v6.py"] = (src["go2_eval_telemetry.py"], 0o644)
    files["diag/go2_eval_telemetry.py"] = (wrapper, 0o644)
    files["diag/go2_eval_diag.py"] = (diag_mod, 0o644)
    files["policy/model_best.pt"] = (model, 0o644)
    files["policy/env.yaml"] = (env, 0o644)
    files["server_run_go2_diag_replay.sh"] = (runner, 0o755)
    files["package_go2_result.py"] = (helper, 0o644)
    run_config = (
        f"WORK_ID={WORK_ID}\nKEEP_DIR_NAME={KEEP_DIR_NAME}\nRESULT_ZIP_NAME={RESULT_ZIP_NAME}\n"
        f"TMUX_NAME=go2_g_a052\nDONE_MARKER='{DONE_MARKER}'\nMODEL_SHA={MODEL_SHA}\nENV_SHA={ENV_SHA}\n"
        f"EXPECTED_EVALUATOR_SHA={EVALUATOR_SHA}\n")
    files["run_config.env"] = (run_config.encode(), 0o644)
    experiment = {
        "work_id": WORK_ID, "kind": "diagnostic_replay_no_training", "edition": EDITION,
        "plan": PLAN, "request": "workspace/training/quadruped/upload/plan/GO2_FAILURE_DATA_REQUEST_CODEX_20260928.md",
        "policy": {"source_run": "G-A048", "checkpoint": "iter 900", "model_sha256": MODEL_SHA, "env_sha256": ENV_SHA},
        "reward_change": None, "training": None,
        "evaluator": {"schema": 6, "sha256": EVALUATOR_SHA, "diag_module_sha256": sha(diag_mod),
                      "diag_wrapper_sha256": sha(wrapper)},
        "runs": [{"label": "plain", "case": "rough_lateral", "seed": 202},
                 {"label": "diag", "case": "rough_lateral", "seed": 202},
                 {"label": "diag", "case": "stairs_10_down", "seed": 101},
                 {"label": "diag", "case": "stairs_15_down", "seed": 101}],
        "video": "NOT_RECORDED — this diagnosis is limited to numeric channels; the recorder follows one env of a "
                 "separate 4-env run, which is not the same condition as this 32-env rollout and cannot be tied to its "
                 "env_id. Contact geometry (where a foot touched a step edge) stays undetermined.",
        "supersedes": {"edition": SUPERSEDES[0], "sha256": SUPERSEDES[1], "never_run": True,
                       "why": "Codex review 2026-09-28: readout read missing contact as zero support; harvest "
                              "verifier exit 0 did not guarantee required files, key completeness or channels; "
                              "contact buffer freshness was not recorded"},
        "interpretation_limits": [
            "reading sensor._data avoids a lazy update but does not prove the buffer is current; contact_fresh records it per row",
            "high_terrain_near_stopped_stance_foot_derived is a combination of nearby higher terrain and a stopped stance foot, not evidence of a step-edge collision",
            "identical steps.csv between plain and diag runs means no difference in stored channels at stored precision, not proof of no interference with every internal state"],
        "readers": ["tools/verify_go2_diag_replay_harvest.py", "tools/go2_diag_replay_readout.py"],
        "decides": "nothing automatically; per-event order (rotation_first/contact_first/simultaneous/"
                   "rotation_only/contact_only/not_observed/unknown) returned to Codex",
    }
    files["experiment.json"] = ((json.dumps(experiment, indent=1, ensure_ascii=False) + "\n").encode(), 0o644)
    readme = (f"G-A052 diagnostic replay — no training, no reward change.\n"
              f"Replays G-A048 iter 900 on rough_lateral seed 202 (plain and diag), stairs_10_down and "
              f"stairs_15_down seed 101 (diag).\nRun: bash /workspace/{PKG}/server_run_go2_diag_replay.sh\n"
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
    return f"""GO2 G-A052 실행 안내 — 진단 재생 · 한 파일 · 한 명령 · 결과 ZIP 하나
============================================================

학습하지 않는다. 보상을 바꾸지 않는다. G-A048 iter 900 정책(model {MODEL_SHA[:12]}…)을
G-A048을 잰 평가기(schema 6, {EVALUATOR_SHA[:12]}…)로 세 case 다시 재생하고,
같은 재생에 읽기 전용 진단 채널(몸통 각속도·발 위치·접촉·체공시간·action·보상 항)을 붙인다.
계획 {PLAN}
서버 실행은 사용자 결정이다.

1. 업로드 — 이 파일 하나만 올린다
   {ZIP_NAME}
   SHA256 {zip_sha}
   서버 경로 /workspace/{ZIP_NAME}

2. 실행 — 한 줄
   unzip -oq /workspace/{ZIP_NAME} -d /workspace && bash /workspace/{PKG}/server_run_go2_diag_replay.sh

   진행 보기: tmux attach -t go2_g_a052
   이전 결과가 서버에 남아 있으면 멈춘다. 내려받은 뒤라면 GO2_DISCARD_PREVIOUS=1 을 앞에 붙인다.

3. 무엇이 도는가 — play.py 네 번
   ① plain rough_lateral seed 202 (평가기만, 재현 확인용)
   ② diag  rough_lateral seed 202 (평가기 + 진단 채널)
   ③ diag  stairs_10_down seed 101
   ④ diag  stairs_15_down seed 101
   G-A048 스위트는 case 하나가 기동 포함 약 0.5분이었다(launcher.log 시각). 진단 CSV 쓰기 부담은
   아직 잰 적이 없다. 서버 세션은 30분으로 잡는다(실행 15분 이내 예상 + 회수).
   영상은 찍지 않는다 — 이번 진단은 수치 계측으로 제한한다. 녹화기는 별도 4 env 재생의 한 대만
   따라가므로 이 32 env 재생과 같은 조건이 아니고 env_id와 묶을 수도 없다. 발이 단 모서리의
   어디에 닿았는지 같은 충돌 형상은 이번 자료로 확정하지 않는다.

4. 완료 표식과 내려받을 것
   {DONE_MARKER}
   /workspace/_keep/{RESULT_ZIP_NAME}
   /workspace/_keep/{RESULT_ZIP_NAME}.sha256
   정상 완료는 _keep/{KEEP_DIR_NAME}/RESULT_STATUS.txt 의 COLLECTION_STATUS=COMPLETE_4_OF_4 다.
   러너가 도중에 죽으면 표식 없이 부분 ZIP(COLLECTION_STATUS=INCOMPLETE_CRASH)이 남는다 —
   표식을 기다리지 말고 launcher.log 와 RUNNER_STATUS.txt 를 읽는다.
   meta/REPRO_STATUS.txt 의 PLAIN_VS_DIAG 가 DIFFERENT 여도 실패가 아니다 — 로컬 판독에서 다룬다.
   IDENTICAL 도 저장된 채널·정밀도에서 차이가 없었다는 뜻이지 계측이 내부 상태에 전혀 개입하지
   않았다는 증명이 아니다.

5. SERVER SHUTDOWN GATE
   a. 결과 ZIP 과 .sha256 이 로컬에 도착했고 SHA 가 맞는다.
   b. 로컬에서 python -B tools/verify_go2_diag_replay_harvest.py <압축 푼 _keep 폴더> 를 돌린다.
      검증기는 두 판정을 따로 낸다: artifact(필수 파일·SHA 목록 포함·식별자·진단 키 완결)와
      channels(필수 채널 묶음·필수 열·접촉 버퍼 갱신).
      종료코드 0 — 둘 다 통과. 이 줄은 채워졌다.
      종료코드 3 — artifact 는 통과했지만 필수 채널이 비었다. **서버를 끄지 않는다.**
                   HARVEST_VERDICT.json 의 channel_problems 를 읽고, 서버에서 복구할 수 있는지
                   (같은 case 재실행으로 채워지는 결측인가) 판단한다. 복구하면 다시 회수·검증한다.
                   복구할 수 없다고 판단하면 **예외 종료 결정**을 ARTIFACT_MANAGEMENT.md 의
                   G-A052 항목에 한 줄로 남긴 뒤 끈다: 결측 채널·case, 복구 불가 사유,
                   부분 회수로 받은 것, 판독에서 unknown 으로 남을 질문.
      종료코드 1 — artifact 실패. **끄지 않는다.** problems 를 읽고 다시 회수한다.
   c. 영상 판정: NOT_RECORDED(위 3, 수치 계측 한정). 학습 report: 비해당(학습 없음, G-A048 원 report는 로컬 보존본을 참조).
   d. 미측정: G1~G7 점수는 이 재생의 목적이 아니다. 판정·변수 선택 없음.
   네 줄이 채워지면 끈다.
"""


def publish(data: bytes) -> str:
    zsha = sha(data)
    cur, hist = UPLOAD / "current", UPLOAD / "history" / RELEASE_ID
    hist.mkdir(parents=True, exist_ok=True)
    cur.mkdir(parents=True, exist_ok=True)
    g = guide(zsha).encode()
    for d in (cur, hist):
        for name, b in ((ZIP_NAME, data), (f"GO2_G_A052_ONE_COMMAND_RUN_GUIDE.txt", g)):
            p = d / name
            if d == hist and p.exists():
                need(p.read_bytes() == b, f"immutable history conflict: {p}")
            p.write_bytes(b)
            (d / f"{name}.sha256").write_text(f"{sha(b)}  {name}\n", encoding="utf-8", newline="\n")
    (cur / "CURRENT_UPLOAD.txt").write_text(
        f"CURRENT GO2 UPLOAD — {WORK_ID} (diagnostic replay, no training)\n\nUPLOAD ONLY THIS ONE FILE\n"
        f"1. {cur / ZIP_NAME}\n   SHA256 {zsha}\n\n절차는 같은 폴더의 GO2_G_A052_ONE_COMMAND_RUN_GUIDE.txt.\n"
        f"서버 실행은 사용자 결정 사항이다.\n\nRELEASE_ID {RELEASE_ID}\nSTATUS ARTIFACT_VERIFIED\n"
        f"이전 판 {SUPERSEDES[0]}(SHA {SUPERSEDES[1][:12]}…)은 실행 전에 대체됐다 — history 에 불변 보존, 서버에 올리지 않는다.\n",
        encoding="utf-8", newline="\n")
    manifest = {"experiment_id": WORK_ID, "release_id": RELEASE_ID, "status": "ARTIFACT_VERIFIED",
                "published_at_utc": "2026-09-28T00:00:00+00:00",
                "note": f"G-A048 iter 900 diagnostic replay, 4 play.py runs, no training, no reward change. Supersedes {SUPERSEDES[0]} (never run).",
                "support_files": ["GO2_G_A052_ONE_COMMAND_RUN_GUIDE.txt"],
                "upload_files": [{"name": ZIP_NAME, "server_path": f"/workspace/{ZIP_NAME}", "sha256": zsha}]}
    (cur / "UPLOAD_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")
    tsv = UPLOAD / "UPLOAD_HISTORY.tsv"
    row = "\t".join(["2026-09-28T00:00:00+00:00", WORK_ID, RELEASE_ID, "ARTIFACT_VERIFIED", ZIP_NAME, zsha,
                     "experiment.json(in ZIP)", "", "diagnostic replay, no training"]) + "\n"
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
