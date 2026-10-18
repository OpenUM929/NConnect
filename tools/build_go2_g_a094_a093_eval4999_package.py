#!/usr/bin/env python3
"""Build G-A094: evaluation only of the G-A093 official-server policy at its reward-best checkpoint (iter 4999).

G-A093 (G-A083 rewards, seed 42, 5,000 iterations on the official server) finished without a
non-finite value and was evaluated at the pre-registered checkpoint 4900 (formula 57.18).  The
deployed finalize picked iteration 4999 as reward-best; user decision 2026-10-18 "제일 좋은걸로 해주고":
evaluate 4999 the same way (69 cases + 10 videos, same evaluator, play.py exports policy.pt from it).

Built from the G-A081 evaluation-only package (tools/build_go2_g_a081_a079_eval_package.py): the
G-A093 runner with its training branch replaced by a fail-closed exit 40; the checkpoint, env.yaml,
training log and report come from the downloaded G-A093 result ZIP with their SHA.  No training, so
it may run on PC2 (`server_run.sh --inner`) or on the official server (`server_run.sh`, tmux).
Deployed files are byte-identical to the G-A093 package (R-6).

    python tools/build_go2_g_a094_a093_eval4999_package.py --check
    python tools/build_go2_g_a094_a093_eval4999_package.py --publish     (never overwrites)
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_g_a081_a079_eval_package as a081  # noqa: E402

GO2 = ROOT / "workspace/training/quadruped"
SRC_ZIP = GO2 / "upload/G-A093/current/GO2_G_A093_FINAL_A083_5000_v1.zip"
SRC_SHA = "5b77bf78f766e4ae8b235cc924a82ace43a5b571fee98f514af8e4b1c2d79c39"
SRC_PREFIX = "go2_g_a093_final_a083_5000/"
SRC_KEY = "final_a083"
RESULT_ZIP = ROOT / "workspace/_keep/GO2_G_A093_FINAL_A083_5000_RESULT.zip"
RESULT_SHA = "775773b4d34d9b6bce385d5c08f9df3ae46a98c7f7c192cbd62aeb7281bb84f0"
ENV_SHA = "8c2215cea14d665df8caf06af097028e006e796ec5147ccb0963a6ff060edc9e"
EVALUATED_4900 = "68594d4a10b81c444491fd04d71eb18e68cd1e526a0620e5c325d9df1e7f429c"
WORK_ID = "G-A094"
RELEASE = "GO2_G_A094_A093_EVAL4999_v1"
PREFIX = "go2_g_a094_a093_eval/"
OUT = GO2 / "upload/G-A094/current"
FINAL_RESULT = "GO2_G_A094_A093_EVAL_RESULT.zip"
REWARD_BEST = (4999, "4466db85c4b000c79db1f6f84725059582da0e8e935a686aae391473846283e0")
POINTS = ((4999, REWARD_BEST[1], "reward-best checkpoint of the G-A093 server training (finalize pick)"),)


def keep_name(it: int) -> str:
    return f"go2_g_a094_a093_eval{it}"


def result_name(it: int) -> str:
    return f"GO2_G_A094_A093_EVAL{it}_RESULT.zip"


def patch_config(cfg: bytes, it: int) -> bytes:
    text = cfg.decode()
    for old, new in (
        ("WORK_ID=G-A093\n", f"WORK_ID={WORK_ID}\n"),
        ("RUN_ID=train_G-A093-Go2_final_a083_5000_server\n", f"RUN_ID=eval_G-A094-A093_iter{it}\n"),
        ("EXPERIMENT_SLUG=go2_g_a093_final_a083_5000\n", f"EXPERIMENT_SLUG={keep_name(it)}\n"),
        ("KEEP_DIR_NAME=go2_g_a093_final_a083_5000\n", f"KEEP_DIR_NAME={keep_name(it)}\n"),
        ("RESULT_ZIP_NAME=GO2_G_A093_FINAL_A083_5000_RESULT.zip\n", f"RESULT_ZIP_NAME={result_name(it)}\n"),
        ("DONE_MARKER='[DONE] GO2_G_A093_FINAL_A083_5000_RESULT_READY'\n",
         f"DONE_MARKER='[DONE] {result_name(it)[:-4]}_READY'\n"),
        ("TMUX_NAME=go2_g_a093_final_a083_5000\n", f"TMUX_NAME={keep_name(it)}_runner\n"),
        ("EVAL_CHECKPOINT_ITER=4900\n", f"EVAL_CHECKPOINT_ITER={it}\n"),
    ):
        assert text.count(old) == 1, f"run_config anchor: {old!r}"
        text = text.replace(old, new)
    return text.encode()


def a093_files() -> dict[str, bytes]:
    src = a081.read_zip(RESULT_ZIP, RESULT_SHA, SRC_PREFIX)
    manifest = {}
    for line in src["SHA256SUMS.txt"].decode().splitlines():
        checksum, name = line.split(maxsplit=1)
        manifest[name.lstrip("*").removeprefix("./")] = checksum
    picks = {f"model_{it}.pt": f"training/checkpoints/model_{it}.pt" for it, _, _ in POINTS}
    picks.update({
        "env.yaml": "training/env.yaml",
        "TRAIN_STATUS.txt": "training/TRAIN_STATUS.txt",
        "CHECKPOINT_PIN.txt": "training/CHECKPOINT_PIN.txt",
        "TRAINING_HEALTH.txt": "training/TRAINING_HEALTH.txt",
        "candidate_training.log": "logs/candidate_training.log",
        "report.html": "exported/report.html",
        "report.html.sha256": "exported/report.html.sha256",
        "REPORT_STATUS.txt": "exported/REPORT_STATUS.txt",
        "RESULT_STATUS.txt": "RESULT_STATUS.txt",
        "RUNNER_STATUS.txt": "RUNNER_STATUS.txt",
    })
    files = {}
    for name, member in picks.items():
        files[name] = src[member]
        assert a081.sha(src[member]) == manifest[member], f"G-A093 manifest mismatch: {member}"
    for it, ckpt_sha, _ in POINTS:
        assert a081.sha(files[f"model_{it}.pt"]) == ckpt_sha, f"checkpoint {it} SHA"
    assert a081.sha(src["training/model_best.pt"]) == EVALUATED_4900, "G-A093 evaluated checkpoint is not 4900"
    assert a081.sha(src["training/model_best_by_reward.pt"]) == REWARD_BEST[1], "reward-best is not 4999"
    assert a081.sha(files["env.yaml"]) == ENV_SHA
    status = files["TRAIN_STATUS.txt"].decode()
    for line in ("TRAIN_RC=0", "LAST_SEGMENT_NONFINITE_ITER=NONE", "TRAINING_END=COMPLETE",
                 "EVALUATED_CHECKPOINT_ITER=4900", "TRAINING_PHASE=SETTLED"):
        assert line + "\n" in status, line
    assert b"RUNNER_RC=0\n" in files["RUNNER_STATUS.txt"]
    for it, _, _ in POINTS:
        assert f"Learning iteration {it}/5000".encode() in files["candidate_training.log"]
    source = {"result_zip": RESULT_ZIP.name, "result_zip_sha256": RESULT_SHA,
              "members": {name: {"from": member, "sha256": a081.sha(files[name])} for name, member in picks.items()}}
    files["A093_SOURCE.json"] = (json.dumps(source, indent=2) + "\n").encode()
    files["A093_SHA256SUMS.txt"] = "".join(f"{a081.sha(files[n])}  {n}\n" for n in sorted(files)).encode()
    return files


def wrapper() -> str:
    text = a081.SERVER_RUN
    reps = [
        ("# G-A081: evaluation-only recovery of the G-A079 server run (training stopped non-finite at 2836;\n"
         "# the 2700 evaluation crashed in Isaac Sim at case 61/69; the server was stopped).\n",
         "# G-A094: evaluation only of the G-A093 server run at its reward-best checkpoint 4999\n"
         "# (training finished 5000/5000 without non-finite values; 4900 was evaluated as pre-registered).\n"),
        ("#   - checkpoints 2700 then 2400, each: 69 cases + 10 videos, stored G-A077 arm, same evaluator\n",
         "#   - checkpoint 4999: 69 cases + 10 videos, stored G-A077 arm, same evaluator as G-A093\n"),
        ("#   - checkpoints/env/log/report travel in a079/ with their SHA from the downloaded result ZIP\n",
         "#   - checkpoint/env/log/report travel in a093/ with their SHA from the downloaded result ZIP\n"),
        ('grep -q "Learning iteration $((it + 1))/5000" "$ROOT_DIR/a079/candidate_training.log" || {\n'
         '    write_status FAILED 41 "A079 log does not continue past iteration $it"; exit 41; }',
         'grep -aq "Learning iteration $it/5000" "$ROOT_DIR/a093/candidate_training.log" || {\n'
         '    write_status FAILED 41 "G-A093 log does not reach iteration $it"; exit 41; }'),
        ("printf 'EVAL_ONLY_RECOVERY=G-A081\\nEVAL_ONLY_EVALUATED_CHECKPOINT_ITER=%s\\n'",
         "printf 'EVAL_ONLY_RECOVERY=G-A094\\nEVAL_ONLY_EVALUATED_CHECKPOINT_ITER=%s\\n'"),
        ("RULE=G-A081 eval-only recovery of G-A079; model_best.pt is the saved iteration-%s checkpoint",
         "RULE=G-A094 eval-only of G-A093; model_best.pt is the saved iteration-%s checkpoint"),
        ("PLANNED_EVAL_CHECKPOINT_ITER=4900\\nREASON=G-A081 eval-only recovery; A079 stopped non-finite at 2836\\n",
         "PLANNED_EVAL_CHECKPOINT_ITER=4900\\nREASON=G-A094 eval-only: reward-best checkpoint of G-A093 (user decision 2026-10-18)\\n"),
        ("SOURCE_RESULT_ZIP=GO2_G_A079_ROOT_REPORT_5000_RESULT.zip (server, 2026-10-13)",
         "SOURCE_RESULT_ZIP=GO2_G_A093_FINAL_A083_5000_RESULT.zip (official server, 2026-10-18)"),
        ("SOURCE_TRAIN_RC=1\\nSOURCE_NONFINITE_ITER=2836\\n", "SOURCE_TRAIN_RC=0\\nSOURCE_NONFINITE_ITER=NONE\\n"),
        ("NOTE=not a 5000-iteration result; A079 training stopped non-finite at 2836\\n",
         "NOTE=G-A093 5000-iteration server training; this checkpoint is its reward-best pick\\n"),
        ("$ROOT_DIR/a079/TRAINING_HEALTH.txt\" \"$KEEP/training/A079_TRAINING_HEALTH.txt\"",
         "$ROOT_DIR/a079/TRAINING_HEALTH.txt\" \"$KEEP/training/A093_TRAINING_HEALTH.txt\""),
        ("$ROOT_DIR/a079/CHECKPOINT_PIN.txt\" \"$KEEP/training/A079_CHECKPOINT_PIN.txt\"",
         "$ROOT_DIR/a079/CHECKPOINT_PIN.txt\" \"$KEEP/training/A093_CHECKPOINT_PIN.txt\""),
        ("$ROOT_DIR/a079/RUNNER_STATUS.txt\" \"$KEEP/training/A079_RUNNER_STATUS.txt\"",
         "$ROOT_DIR/a079/RUNNER_STATUS.txt\" \"$KEEP/training/A093_RUNNER_STATUS.txt\""),
        ('(cd "$ROOT_DIR/a079" && sha256sum -c --quiet A079_SHA256SUMS.txt) || {\n'
         "  write_status FAILED 41 'a079 artifacts do not match their SHA'; exit 41; }",
         '(cd "$ROOT_DIR/a093" && sha256sum -c --quiet A093_SHA256SUMS.txt) || {\n'
         "  write_status FAILED 41 'a093 artifacts do not match their SHA'; exit 41; }"),
        ("'env.yaml SHA differs from the A079 result ZIP'", "'env.yaml SHA differs from the G-A093 result ZIP'"),
        ('"checkpoint $it SHA differs from the A079 result ZIP"', '"checkpoint $it SHA differs from the G-A093 result ZIP"'),
    ]
    for old, new in reps:
        assert text.count(old) == 1, f"wrapper anchor: {old[:70]!r}"
        text = text.replace(old, new)
    text = text.replace("$ROOT_DIR/a079/", "$ROOT_DIR/a093/")
    text = text.replace("go2_g_a081_a079_eval", "go2_g_a094_a093_eval").replace("GO2_G_A081_A079_EVAL", "GO2_G_A094_A093_EVAL")
    text = text.replace("go2_a081_a079_eval", "go2_a094_a093_eval")
    assert "a079" not in text.lower() and "A081" not in text and "2836" not in text, "stale G-A081/A079 text"
    return text


ONE_LINE = (f"cd /workspace && sha256sum -c {RELEASE}.zip.sha256 && unzip -oq {RELEASE}.zip -d /workspace && "
            f"bash /workspace/{PREFIX}server_run.sh")
PC2_LINE = (f"cd /workspace && unzip -oq {RELEASE}.zip -d /workspace && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 "
            f"PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/{PREFIX}server_run.sh --inner")

GUIDE = f"""# G-A094 — G-A093 서버 정책의 보상 최고 checkpoint(4999) 평가 (학습 없음)

- G-A093(G-A083 보상, seed 42, 공식 서버 5,000회)은 비유한값 없이 끝났다. 사전등록한 4900회로 평가해 57.18점이었다.
- 배포 finalize가 고른 보상 최고 checkpoint는 4999회(`{REWARD_BEST[1][:8]}…`)다. 이 패키지가 그 checkpoint를 같은 평가기로 잰다(69건, 영상 10편).
- play.py가 이 checkpoint에서 policy.pt를 export한다. runner의 학습 경로는 rc 40으로 막혀 있다.
- 학습이 없으므로 PC2에서 돌려도 제출 정책의 출처는 서버 학습 그대로다.

## 실행
- PC2 (tmux 없음):
  - `{PC2_LINE}`
- 공식 서버 (tmux):
  - `{ONE_LINE}`

## 회수
- `/workspace/_keep/{FINAL_RESULT}`과 `.sha256`

## 해석 한계
- 내부 proxy이며 공식 결과가 아니다. 학습 실현은 하나다.
"""


def build() -> tuple[bytes, dict]:
    src = a081.read_zip(SRC_ZIP, SRC_SHA, SRC_PREFIX)
    files = {k: v for k, v in src.items() if k.startswith("shared/")}
    files[a081.RUNNER] = a081.patch_runner(files[a081.RUNNER])
    src_run = {k[len(f"runs/{SRC_KEY}/"):]: v for k, v in src.items() if k.startswith(f"runs/{SRC_KEY}/")}
    for it, ckpt_sha, purpose in POINTS:
        run = {n: c for n, c in src_run.items() if n not in ("PACKAGE_SHA256SUMS.txt", "README.txt")}
        run["run_config.env"] = patch_config(run["run_config.env"], it)
        experiment = json.loads(run["experiment.json"])
        experiment["evaluation_only"] = {
            "work_id": WORK_ID, "source_result_zip_sha256": RESULT_SHA,
            "evaluated_checkpoint": {"iter": it, "sha256": ckpt_sha, "purpose": purpose},
            "preregistered_checkpoint_iter": 4900, "preregistered_result": "formula 57.18 (checkpoint 4900)",
            "user_decision": "2026-10-18: evaluate the best (reward-best) checkpoint",
        }
        experiment.setdefault("evaluation", {})["checkpoint_iter"] = it
        run["experiment.json"] = (json.dumps(experiment, ensure_ascii=False, indent=2) + "\n").encode()
        run["README.txt"] = f"G-A094 eval-only: G-A093 checkpoint {it} ({purpose}). No training.\n".encode()
        for n, c in run.items():
            files[f"runs/eval{it}/{n}"] = c
        materialized = a081.materialize(files, f"eval{it}")
        files[f"runs/eval{it}/PACKAGE_SHA256SUMS.txt"] = "".join(
            f"{a081.sha(c)}  {n}\n" for n, c in sorted(materialized.items())).encode()
    for n, c in a093_files().items():
        files["a093/" + n] = c
    files["check_checkpoint.py"] = a081.CHECK_CHECKPOINT.read_bytes().replace(b"\r\n", b"\n")
    text = wrapper()
    for marker, value in (("@FINAL_RESULT@", FINAL_RESULT), ("@ENV_SHA@", ENV_SHA), ("@SOURCE_ZIP_SHA@", RESULT_SHA),
                          ("@POINTS@", " ".join(f"{it}:{s}" for it, s, _ in POINTS)),
                          ("@RB_ITER@", str(REWARD_BEST[0])), ("@RB_SHA@", REWARD_BEST[1])):
        assert text.count(marker) == 1, marker
        text = text.replace(marker, value)
    files["server_run.sh"] = text.encode()
    files["SERVER_GUIDE.md"] = GUIDE.encode()
    files["SERVER_PROVENANCE.json"] = (json.dumps({
        "release": RELEASE, "work_id": WORK_ID, "built_from_zip_sha256": SRC_SHA,
        "a093_result_zip_sha256": RESULT_SHA, "deployed_files_identical_to_g_a093": list(a081.DEPLOYED),
        "training": None, "evaluated_checkpoints": [{"iter": it, "sha256": s} for it, s, _ in POINTS],
        "final_result": FINAL_RESULT,
    }, indent=2) + "\n").encode()
    files["SHA256SUMS.txt"] = "".join(f"{a081.sha(c)}  {n}\n" for n, c in sorted(files.items())).encode()
    files["SERVER_SHA256SUMS.txt"] = "".join(f"{a081.sha(c)}  {n}\n" for n, c in sorted(files.items())).encode()
    for name in a081.DEPLOYED:
        assert files[name] == src[name], f"deployed file changed: {name}"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(PREFIX + name, (2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if name.endswith((".mp4", ".pt")) else zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            archive.writestr(info, files[name])
    data = buffer.getvalue()
    validate(data)
    return data, {"sha256": a081.sha(data), "bytes": len(data), "members": len(files)}


def validate(data: bytes) -> None:
    import subprocess
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        rel = {n[len(PREFIX):]: archive.read(n) for n in names}
        for manifest in ("SHA256SUMS.txt", "SERVER_SHA256SUMS.txt"):
            for line in rel[manifest].decode().splitlines():
                checksum, name = line.split("  ", 1)
                assert a081.sha(rel[name]) == checksum, (manifest, name)
        for it, _, _ in POINTS:
            materialized = a081.materialize(rel, f"eval{it}")
            for line in rel[f"runs/eval{it}/PACKAGE_SHA256SUMS.txt"].decode().splitlines():
                checksum, r = line.split("  ", 1)
                assert a081.sha(materialized[r]) == checksum, r
            cfg = rel[f"runs/eval{it}/run_config.env"].decode()
            for line in ("TRAIN_SEED=42", "NUM_ENVS=4096", f"EVAL_CHECKPOINT_ITER={it}", f"KEEP_DIR_NAME={keep_name(it)}",
                         f"RESULT_ZIP_NAME={result_name(it)}", f"WORK_ID={WORK_ID}"):
                assert line + "\n" in cfg, line
            expected = json.loads(rel[f"runs/eval{it}/expected_rewards.json"])["candidate"]
            assert expected["track_ang_vel_z_exp"] == 0.75 and expected["action_rate_l2"] == -0.01
        assert b"-p train.py" not in rel[a081.RUNNER] and b"exit 40" in rel[a081.RUNNER]
        assert b"[RETRY] eval" in rel[a081.RUNNER]
        for n, c in rel.items():
            if n.endswith(".sh"):
                assert b"\r" not in c, n
                r = subprocess.run([a081.BASH, "-n"], input=c, capture_output=True)
                assert r.returncode == 0, (n, r.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    data, info = build()
    print(json.dumps({"release": RELEASE, **info}))
    if args.publish:
        OUT.mkdir(parents=True, exist_ok=True)
        target = OUT / f"{RELEASE}.zip"
        if target.exists():
            raise SystemExit(f"refuse overwrite: {target}")
        target.write_bytes(data)
        (OUT / f"{RELEASE}.zip.sha256").write_text(f"{info['sha256']}  {target.name}\n", encoding="utf-8", newline="\n")
        (OUT / "SERVER_GUIDE.md").write_bytes(GUIDE.encode())
        print(f"published={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
