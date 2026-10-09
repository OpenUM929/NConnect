#!/usr/bin/env python3
"""Build a fail-closed evaluation-only recovery package for completed G-A074.

The package resumes the preserved G-A074 keep directory.  It contains no
training command and refuses to evaluate unless TRAIN_RC=0 and the pinned
iter-2400 checkpoint hash match the completed run.
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
sys.path.insert(0, str(ROOT / "tools"))

import build_go2_g_a074_report_policy_retry_package as a074  # noqa: E402
import build_go2_g_a076_report_policy_retry_package as a076  # noqa: E402

PREFIX = "go2_g_a074_eval_recovery/"
RELEASE = "GO2_G_A074_EVAL_RECOVERY_v1"
PINNED_SHA = "d39b88e9a6b06fd08498c90bbba334a3aaaca1cc8e540102c7d0e284bac72211"
FIXED_TIME = (2026, 10, 9, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sums(files: dict[str, bytes]) -> bytes:
    return "".join(f"{sha(files[k])}  {k}\n" for k in sorted(files)).encode()


def fail_closed_runner() -> bytes:
    runner = a076.source_payload()["server_run_go2_candidate_iter_pinned.sh"]
    start = runner.index(b'else\n  if [[ "$RESUME" == 1 && "${GO2_RESTART_TRAINING:-0}" != 1 ]]')
    end_marker = b'fi\nmkdir -p "$KEEP/training/source"'
    end = runner.index(end_marker, start)
    replacement = (
        b"else\n"
        b"  echo '[FAIL] G-A074 evaluation recovery requires the completed preserved training artifact'\n"
        b"  echo '[FAIL] training fallback is disabled; restore G-A074 and retry evaluation only'\n"
        b"  exit 40\n"
        b"fi\nmkdir -p \"$KEEP/training/source\""
    )
    runner = runner[:start] + replacement + runner[end + len(end_marker):]
    if b'"$ISAACLAB_SH" -p train.py' in runner:
        raise ValueError("training path remains in recovery runner")
    return runner


def build() -> tuple[bytes, dict[str, object]]:
    original, _ = a074.build()
    files: dict[str, bytes] = {}
    old_prefix = a074.PREFIX
    run_prefix = old_prefix + "runs/" + a074.KEY + "/"
    shared_prefix = old_prefix + "shared/"
    with zipfile.ZipFile(io.BytesIO(original)) as zf:
        for name in zf.namelist():
            if name.startswith(shared_prefix):
                files[name[len(shared_prefix):]] = zf.read(name)
            elif name.startswith(run_prefix):
                files[name[len(run_prefix):]] = zf.read(name)

    text_suffixes = {".env", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
    for name, data in list(files.items()):
        if Path(name).suffix in text_suffixes:
            files[name] = data.replace(b"\r\n", b"\n")

    files["server_run_go2_candidate_iter_pinned.sh"] = fail_closed_runner()
    experiment = json.loads(files["experiment.json"])
    experiment["schema"] = "go2_g_a074_evaluation_recovery_v1"
    experiment["purpose"] = "Resume evaluation of the completed G-A074 iter-2400 checkpoint."
    experiment["training"] = {
        "state": "completed_preserved",
        "train_rc": 0,
        "checkpoint_iter": 2400,
        "checkpoint_sha256": PINNED_SHA,
        "fallback": "disabled",
    }
    experiment["design"] = "HANDOFF_G_A074_EVAL_PC2.md"
    files["experiment.json"] = (json.dumps(experiment, ensure_ascii=False, indent=2) + "\n").encode()
    files["README.txt"] = (
        "G-A074 evaluation-only recovery.\n"
        "Requires /workspace/_keep/go2_g_a074_report_policy with TRAIN_RC=0, "
        f"iter-2400 checkpoint {PINNED_SHA}.\n"
        "The runner contains no training command and fails closed if the preserved run is missing.\n"
    ).encode()
    files["run_eval_only.sh"] = f'''#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)
KEEP=/workspace/_keep/go2_g_a074_report_policy
PINNED_SHA={PINNED_SHA}
(cd "$ROOT_DIR" && sha256sum -c --quiet PACKAGE_SHA256SUMS.txt) || {{ echo '[FAIL] recovery package SHA mismatch'; exit 2; }}
[[ -s "$KEEP/training/TRAIN_STATUS.txt" ]] && grep -qx 'TRAIN_RC=0' "$KEEP/training/TRAIN_STATUS.txt" || {{
  echo '[FAIL] G-A074 TRAIN_RC=0 artifact is missing'; exit 40;
}}
[[ -s "$KEEP/training/model_best.pt" ]] || {{ echo '[FAIL] G-A074 pinned model missing'; exit 40; }}
[[ "$(sha256sum "$KEEP/training/model_best.pt" | awk '{{print $1}}')" == "$PINNED_SHA" ]] || {{
  echo '[FAIL] G-A074 pinned model SHA mismatch'; exit 40;
}}
grep -qx 'EVAL_CHECKPOINT_ITER=2400' "$KEEP/training/CHECKPOINT_PIN.txt" || {{ echo '[FAIL] checkpoint iter mismatch'; exit 40; }}
grep -qx "EVAL_CHECKPOINT_SHA=$PINNED_SHA" "$KEEP/training/CHECKPOINT_PIN.txt" || {{ echo '[FAIL] checkpoint pin SHA mismatch'; exit 40; }}
[[ -s "$KEEP/training/env.yaml" && -s "$KEEP/exported/report.html" ]] || {{ echo '[FAIL] G-A074 env/report missing'; exit 40; }}
grep -qx 'REPORT_STATUS=REPORT_ACQUIRED' "$KEEP/exported/REPORT_STATUS.txt" || {{ echo '[FAIL] report status invalid'; exit 40; }}
(cd "$KEEP/exported" && sha256sum -c --quiet report.html.sha256) || {{ echo '[FAIL] report SHA mismatch'; exit 40; }}
if [[ -s /workspace/_keep/GO2_G_A074_REPORT_POLICY_RESULT.zip ]]; then
  BACKUP_DIR=/workspace/_keep/g_a074_pre_eval_archives
  STAMP=$(date +%Y%m%d-%H%M%S)
  mkdir -p "$BACKUP_DIR"
  cp -a /workspace/_keep/GO2_G_A074_REPORT_POLICY_RESULT.zip "$BACKUP_DIR/GO2_G_A074_REPORT_POLICY_RESULT.pre_eval_${{STAMP}}.zip"
  sha256sum "$BACKUP_DIR/GO2_G_A074_REPORT_POLICY_RESULT.pre_eval_${{STAMP}}.zip" > "$BACKUP_DIR/GO2_G_A074_REPORT_POLICY_RESULT.pre_eval_${{STAMP}}.zip.sha256"
fi
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export PACKAGE_ROOT="$ROOT_DIR" GO2_RESUME=1 GO2_STAGE=full GO2_REMEASURE_BASELINE=0
exec bash "$ROOT_DIR/server_run_go2_candidate_iter_pinned.sh" --inner
'''.encode()

    files.pop("PACKAGE_SHA256SUMS.txt", None)
    files["PACKAGE_SHA256SUMS.txt"] = sums(files)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(PREFIX + name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            zf.writestr(info, files[name])
    data = buf.getvalue()
    return data, {"files": files, "sha": sha(data)}


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--publish", action="store_true")
    args = ap.parse_args()
    data, info = build()
    print(f"files={len(info['files'])} bytes={len(data)} sha256={info['sha']}")
    if args.publish:
        out = GO2 / "upload/G-A074/recovery/current"
        out.mkdir(parents=True, exist_ok=True)
        target = out / f"{RELEASE}.zip"
        if target.exists():
            raise SystemExit(f"refuse overwrite: {target}")
        target.write_bytes(data)
        (out / f"{RELEASE}.zip.sha256").write_text(
            f"{info['sha']}  {target.name}\n", encoding="utf-8", newline="\n"
        )
        print(f"published={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
