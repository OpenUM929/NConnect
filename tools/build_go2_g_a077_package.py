#!/usr/bin/env python3
"""Build G-A077: one flat-orientation rollback from the verified G-A074 policy.

The scientific baseline is the completed G-A074 iter-2400 checkpoint and its
stored 69-case evaluation, not the older A033 arm bundled by the ancestor
runner.  Runtime code is reused from G-A076; only orchestration guards and the
one allowed reward weight are overlaid.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as a033  # noqa: E402
import build_go2_g_a057_sweep_package as a057  # noqa: E402
import build_go2_g_a076_report_policy_retry_package as a076  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

WORK_ID = "G-A077"
PREFIX = "go2_g_a077_flat_orientation_m0p225/"
RELEASE = "GO2_G_A077_FLAT_ORIENTATION_M0P225_v1"
KEY = "flat_orientation_l2_m0p225"
FIXED_TIME = (2026, 10, 10, 0, 0, 0)
PART_SIZE = 95 * 1024 * 1024

G074 = Path(os.environ.get("GO2_G_A074_KEEP", r"C:\workspace\_keep\go2_g_a074_report_policy"))
G074_MODEL = G074 / "training/model_best.pt"
G074_ENV = G074 / "training/env.yaml"
G074_EVAL = G074 / "evaluation/candidate"
G074_REPORT = G074 / "exported/report.html"
G074_REPORT_SHA = G074 / "exported/report.html.sha256"
G074_REPORT_STATUS = G074 / "exported/REPORT_STATUS.txt"
G074_SOURCE = G074 / "training/source"
G074_SOURCE_MANIFEST = G074 / "training/candidate_source.sha256"
G074_MODEL_SHA = "d39b88e9a6b06fd08498c90bbba334a3aaaca1cc8e540102c7d0e284bac72211"
G074_ENV_SHA = "992cdec9a322d7e8a5cfff8048d803116ce010ba4d0d4820cf95b49db9987005"
EVALUATOR_SHA = "e1a988bd770cf915f5d7b88f50b34e2d42cceb7d827e1363bebe9218b5e975ae"
REGISTRY_SHA = "8d8c34caf66813e2c18070fb9a85ed7c843c379cb3a5ffb3d0a73923b9349ba6"
GO2_USD_URL = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/"
    "IsaacLab/Robots/Unitree/Go2/go2.usd"
)

BASE = {
    "track_lin_vel_xy_exp": 2.0,
    "feet_air_time": 0.01,
    "lin_vel_z_l2": -3.0,
    "ang_vel_xy_l2": -0.05,
    "action_rate_l2": -0.005,
    "flat_orientation_l2": -0.25,
    "track_ang_vel_z_exp": 0.30,
}
CANDIDATE = {**BASE, "flat_orientation_l2": -0.225}

IDENTITY_GREP_LINES = r'''grep -Fq '"model_sha256":"'"$BASELINE_MODEL_SHA"'"' "$STORED_BASELINE/identity.json" &&
grep -Fq '"env_sha256":"'"$BASELINE_ENV_SHA"'"' "$STORED_BASELINE/identity.json" &&
grep -Fq '"evaluator_sha256":"'"$EXPECTED_EVALUATOR_SHA"'"' "$STORED_BASELINE/identity.json" &&
grep -Fq '"registry_sha256":"'"$EXPECTED_REGISTRY_SHA"'"' "$STORED_BASELINE/identity.json" || {
  echo '[FAIL] G-A077 stored baseline identity mismatch'; exit 23;
}'''


@dataclass(frozen=True)
class Entry:
    data: bytes | None = None
    path: Path | None = None

    def digest(self) -> str:
        h = hashlib.sha256()
        if self.data is not None:
            h.update(self.data)
        else:
            assert self.path is not None
            with self.path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    h.update(block)
        return h.hexdigest()


def sha_path(path: Path) -> str:
    return Entry(path=path).digest()


def render(template: str, values: dict[str, float]) -> str:
    src = render_reward_source(template, {k: values[k] for k in REWARD_NAMES})
    src = a033.add_env_reward_line(src, "track_ang_vel_z_exp", values["track_ang_vel_z_exp"])
    if reward_dict(src) != values:
        raise ValueError("rendered reward source does not parse back to the requested values")
    return src


def validate_g074() -> None:
    required = (
        G074_MODEL,
        G074_ENV,
        G074_REPORT,
        G074_REPORT_SHA,
        G074_REPORT_STATUS,
        G074_SOURCE_MANIFEST,
        G074_EVAL / "identity.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing verified G-A074 source: " + ", ".join(missing))
    if sha_path(G074_MODEL) != G074_MODEL_SHA or sha_path(G074_ENV) != G074_ENV_SHA:
        raise ValueError("G-A074 model/env SHA mismatch")
    identity = json.loads((G074_EVAL / "identity.json").read_text(encoding="utf-8"))
    expected = {
        "model_sha256": G074_MODEL_SHA,
        "env_sha256": G074_ENV_SHA,
        "evaluator_sha256": EVALUATOR_SHA,
        "registry_sha256": REGISTRY_SHA,
    }
    for key, value in expected.items():
        if identity.get(key) != value:
            raise ValueError(f"G-A074 identity {key}={identity.get(key)!r}, expected {value}")
    if len(list((G074_EVAL / "cases").rglob("summary.json"))) != 69:
        raise ValueError("G-A074 baseline is not a complete 69-case evaluation")
    if len(list((G074_EVAL / "videos").rglob("*.mp4"))) != 10:
        raise ValueError("G-A074 baseline does not contain the required 10 videos")


def validate_deployment_source(source: dict[str, bytes], baseline_source: bytes) -> None:
    manifest: dict[str, str] = {}
    for line in G074_SOURCE_MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        manifest[relative.lstrip("* ")] = digest
    names = (
        "train.py",
        "play.py",
        "go2_task/__init__.py",
        "go2_task/_finalize.py",
        "go2_task/agent_cfg.py",
        "go2_task/env_cfg.py",
    )
    for name in names:
        actual = (G074_SOURCE / name).read_bytes()
        packaged = source[f"candidate/{name}"]
        if actual != packaged or hashlib.sha256(packaged).hexdigest() != manifest[name]:
            raise ValueError(f"deployment source differs from verified G-A074: {name}")
    if baseline_source != (G074_SOURCE / "quadruped_rewards.py").read_bytes():
        raise ValueError("rendered baseline rewards differ from verified G-A074")
    if hashlib.sha256(baseline_source).hexdigest() != manifest["quadruped_rewards.py"]:
        raise ValueError("rendered baseline rewards differ from G-A074 candidate_source.sha256")


def run_config(template: str) -> str:
    replacements = {
        "WORK_ID": WORK_ID,
        "RUN_ID": "train_G-A077-Go2_flat_orientation_m0p225_3000",
        "EXPERIMENT_SLUG": "go2_g_a077_flat_orientation_m0p225",
        "KEEP_DIR_NAME": "go2_g_a077_flat_orientation_m0p225",
        "RESULT_ZIP_NAME": "GO2_G_A077_FLAT_ORIENTATION_M0P225_RESULT.zip",
        "DONE_MARKER": "'[DONE] GO2_G_A077_FLAT_ORIENTATION_M0P225_RESULT_READY'",
        "TMUX_NAME": "go2_g_a077_flat_orientation_m0p225",
        "TRAIN_SEED": "42",
        "NUM_ENVS": "4096",
        "MAX_ITERATIONS": "3000",
        "SINGLE_CHANGE_NAME": "flat_orientation_l2",
        "SINGLE_CHANGE_FROM": "-0.25",
        "SINGLE_CHANGE_TO": "-0.225",
        "BASELINE_NAME": "G_A074_VERIFIED",
        "BASELINE_LABEL": "g_a074",
        "BASELINE_MODEL_SHA": G074_MODEL_SHA,
        "BASELINE_ENV_SHA": G074_ENV_SHA,
        "EXPECTED_EVALUATOR_SHA": EVALUATOR_SHA,
        "EXPECTED_REGISTRY_SHA": REGISTRY_SHA,
        "EVAL_CHECKPOINT_ITER": "2400",
        "COLLECT_REQUIRED_ON_STATIONARY": "1",
    }
    lines: list[str] = []
    for line in template.splitlines():
        match = re.match(r"^([A-Z_]+)=", line)
        if match and match.group(1) in replacements:
            lines.append(f"{match.group(1)}={replacements.pop(match.group(1))}")
        else:
            lines.append(line)
    if replacements:
        raise ValueError(f"source run_config lacks {sorted(replacements)}")
    return "\n".join(lines) + "\n"


def patched_runner(source: bytes) -> bytes:
    text = source.decode("utf-8")
    marker = 'echo "[START] $WORK_ID $RUN_ID resume=$RESUME remeasure_baseline=$REMEASURE at $(date -Is)"\n'
    if text.count(marker) != 1:
        raise ValueError("runner start marker changed")
    preflight = f'''{marker}# G-A077: fail before training if the exact stored baseline or Go2 asset is unavailable.
[[ "$EVALUATOR_SHA" == "$EXPECTED_EVALUATOR_SHA" && "$REGISTRY_SHA" == "$EXPECTED_REGISTRY_SHA" ]] || {{
  echo '[FAIL] G-A077 evaluator/registry differs from the verified G-A074 baseline'; exit 23;
}}
[[ "$(sha256sum "$BASELINE_ROOT/exported/model_best.pt" | awk '{{print $1}}')" == "$BASELINE_MODEL_SHA" &&
   "$(sha256sum "$BASELINE_ROOT/exported/env.yaml" | awk '{{print $1}}')" == "$BASELINE_ENV_SHA" ]] || {{
  echo '[FAIL] G-A077 stored G-A074 model/env SHA mismatch'; exit 23;
}}
STORED_BASELINE="$BASELINE_ROOT/stored_evaluation"
[[ "$(find "$STORED_BASELINE/cases" -name summary.json | wc -l)" == 69 &&
   "$(find "$STORED_BASELINE/videos" -name '*.mp4' | wc -l)" == 10 ]] || {{
  echo '[FAIL] G-A077 stored G-A074 baseline must contain 69 cases and 10 videos'; exit 23;
}}
{IDENTITY_GREP_LINES}
[[ -s "$BASELINE_ROOT/exported/report.html" && -s "$BASELINE_ROOT/exported/report.html.sha256" &&
   -s "$BASELINE_ROOT/exported/REPORT_STATUS.txt" ]] || {{
  echo '[FAIL] G-A077 matched G-A074 report evidence is missing'; exit 23;
}}
GO2_USD_URL={GO2_USD_URL!r}
if command -v curl >/dev/null 2>&1; then
  curl --fail --silent --show-error --location --head --connect-timeout 10 --max-time 45 "$GO2_USD_URL" >/dev/null || {{
    echo '[FAIL] Go2 USD asset is unavailable; training was not started'; exit 23;
  }}
else
  "$ISAACLAB_SH" -p - "$GO2_USD_URL" <<'PY'
import sys, urllib.request
request = urllib.request.Request(sys.argv[1], method="HEAD")
with urllib.request.urlopen(request, timeout=45) as response:
    if response.status >= 400:
        raise SystemExit(1)
PY
fi
mkdir -p "$KEEP/evaluation"
if [[ ! -d "$KEEP/evaluation/$BASELINE_LABEL" ]]; then
  cp -a "$STORED_BASELINE" "$KEEP/evaluation/$BASELINE_LABEL"
fi
[[ "$(find "$KEEP/evaluation/$BASELINE_LABEL/cases" -name summary.json | wc -l)" == 69 ]] || {{
  echo '[FAIL] materialized G-A074 baseline is incomplete'; exit 23;
}}
'''
    text = text.replace(marker, preflight)
    old = "    exp_base=0; exp_sent=${#SENTINEL_CASES[@]}"
    new = "    exp_base=69; exp_sent=0"
    if text.count(old) != 1:
        raise ValueError("runner baseline count contract changed")
    text = text.replace(old, new)
    old_videos = '''  if [[ ${#BASELINE_VIDEOS[@]} -gt 0 ]]; then
    run_video_list "${BASELINE_LABEL}_videos" "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV" "${BASELINE_VIDEOS[@]}"
  fi'''
    if text.count(old_videos) != 1:
        raise ValueError("runner baseline video collection contract changed")
    text = text.replace(old_videos, "  # G-A077 reuses the ten identity-pinned G-A074 videos; do not rerun the baseline.")
    old_sentinel = '''else
  echo "[PHASE 4/6] baseline $BASELINE_NAME sentinel: ${#SENTINEL_CASES[@]} cases re-measured against the stored arm"
  SENT_OUT="$KEEP/evaluation/${BASELINE_LABEL}_sentinel"
  stage_policy "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV"
  [[ "$ACTIVE_MODEL_SHA" == "$BASELINE_MODEL_SHA" ]] || {
    echo "[FAIL] baseline model SHA mismatch: $ACTIVE_MODEL_SHA"; exit 7;
  }
  write_identity "${BASELINE_LABEL}_sentinel" "$BASELINE_ROOT" "$BASELINE_MODEL" "$BASELINE_ENV" "$SENT_OUT"
  for entry in "${SENTINEL_CASES[@]}"; do
    IFS=: read -r scenario case_id seed <<<"$entry"
    run_eval_case "${BASELINE_LABEL}_sentinel" "$BASELINE_ROOT" "$seed" "$scenario" "$case_id" "$SENT_OUT"
  done
  [[ "$(find "$SENT_OUT/cases" -name summary.json | wc -l)" == "${#SENTINEL_CASES[@]}" ]] || {
    echo '[FAIL] sentinel telemetry count mismatch'; exit 6;
  }
  BASELINE_ARM=REUSED_STORED_WITH_SENTINEL
fi'''
    new_stored = '''else
  echo "[PHASE 4/6] reuse identity-pinned G-A074 baseline: 69 cases and 10 videos; no baseline execution"
  BASELINE_ARM=REUSED_G_A074_FULL_NO_RERUN
fi'''
    if text.count(old_sentinel) != 1:
        raise ValueError("runner stored baseline branch changed")
    text = text.replace(old_sentinel, new_stored)
    text = text.replace(
        'base_videos=$(count_files "$KEEP/evaluation/${BASELINE_LABEL}_videos/videos" \'*.mp4\')',
        'base_videos=$(count_files "$KEEP/evaluation/$BASELINE_LABEL/videos" \'*.mp4\')',
    )
    status_line = "  printf 'STAGE=%s\\nCOLLECTION_STATUS=%s\\n' \"$STAGE\" \"$collection\" >>\"$KEEP/RUNNER_STATUS.txt\""
    status_extra = status_line + '''
  printf 'LEGACY_GATE_AUTHORITY=NON_AUTHORITATIVE_EXECUTION_SAFETY_ONLY\\nPREREG_DECISION=POSTHOC_AUTHOR_CHECKER_REQUIRED\\n' >>"$KEEP/RUNNER_STATUS.txt"'''
    if text.count(status_line) != 1:
        raise ValueError("runner status contract changed")
    text = text.replace(status_line, status_extra)
    return text.encode("utf-8")


def experiment() -> dict:
    return {
        "schema": "go2_g_a077_single_change_v1",
        "work_id": WORK_ID,
        "device": "PC2",
        "run_key": KEY,
        "purpose": "Recover 15 cm stair completion while preserving G-A074 rough-terrain stability.",
        "promotion": "exploratory_single_seed_no_automatic_followup",
        "baseline": {
            "work_id": "G-A074",
            "checkpoint_iter": 2400,
            "model_sha256": G074_MODEL_SHA,
            "env_sha256": G074_ENV_SHA,
            "evaluation": "stored posture_gate_v2 full 69 cases and 10 videos",
            "internal_proxy_points_70": 60.82974642426652,
        },
        "single_change": {
            "name": "flat_orientation_l2",
            "from": -0.25,
            "to": -0.225,
            "value_design": "halfway rollback of the prior 0.05 change; not an interpolated performance claim",
            "matched_series_classification": "OUT_OF_RANGE: G-A074 has measured only -0.25 in this matched series",
        },
        "evidence_basis": {
            "base_data": "workspace/training/quadruped/reports/GO2_TUNING_BASE_DATA.md section 4, read with the verified G-A074 identity",
            "external_reference": "GO2_REWARD_EVIDENCE_MASTER.md section 1-b: Isaac Lab v2.3.1 rough flat=0 and flat-task=-2.5 are reference conventions, not an optimum",
            "dial_history_ref": "workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md section 3-6 and MASTER section 1-a (A047)",
            "inference": "A033 fixed-action margin is NOT_APPLICABLE because A033 and G-A074 differ in multiple rewards and training length",
        },
        "rewards": CANDIDATE,
        "training": {"seed": 42, "num_envs": 4096, "max_iterations": 3000, "from_scratch": True},
        "evaluation": {"checkpoint_iter": 2400, "seeds": [101, 202, 303], "case_count": 69},
        "hypothesis": {
            "direction": "A smaller flat-orientation penalty permits more terrain-relative posture freedom and may improve 15 cm climbing.",
            "competing": "The same relaxation may reduce the G-A074 posture stability observed on rough terrain and domain randomization.",
            "limitations": "The direction is qualitative; -0.225 is an exploratory design value, not a predicted optimum.",
        },
        "preregistered_thresholds": {
            "stairs_15_down": {
                "full_count_each_seed": {"101": ">0", "202": ">0", "303": ">0"},
                "ge2_min_each_seed": {"101": 17, "202": 19, "303": 14},
                "survival_proxy_min_each_seed": {"101": 0.84375, "202": 0.9375, "303": 0.96875},
            },
            "stairs_10_down_ge2_min_each_seed": {"101": 32, "202": 30, "303": 28},
            "all_69_case_protection": {
                "rule": "For each aligned case and evaluation seed, candidate survival_proxy and tracking factor must be no lower than G-A074.",
                "absolute_tolerance": 1e-9,
                "role": "adoption_noninferiority; a minor protection loss does not by itself refute the directional 15 cm hypothesis",
            },
            "result_use": "One exploratory result only; do not automatically try another flat_orientation_l2 value.",
        },
        "decision_authority": {
            "legacy_runner_gate": "NON_AUTHORITATIVE_FOR_G_A077_PROMOTION; execution-safety/collection status only",
            "preregistered_threshold_enforcement": "POSTHOC_AUTHOR_CHECKER_REQUIRED",
            "claim_limit": "Package metadata records thresholds but runtime does not adjudicate the G-A077 promotion decision.",
        },
        "asset_preflight": {"url": GO2_USD_URL, "must_pass_before_training": True},
        "design": "workspace/training/quadruped/upload/plan/GO2_G_A077_PLAN_20261010.md",
    }


def entries() -> dict[str, Entry]:
    validate_g074()
    source = a076.source_payload()
    shared_bytes = a057.shared_files(source)
    template = source["candidate/quadruped_rewards.py"].decode("utf-8")
    baseline_source = render(template, BASE).encode("utf-8")
    candidate_source = render(template, CANDIDATE).encode("utf-8")
    validate_deployment_source(source, baseline_source)
    shared_bytes["candidate/quadruped_rewards.py"] = candidate_source
    shared_bytes["baseline/quadruped_rewards.py"] = baseline_source
    shared_bytes["baseline/exported/model_best.pt"] = b""  # replaced by a streamed file below
    shared_bytes["baseline/exported/env.yaml"] = b""       # replaced by a streamed file below
    shared_bytes["server_run_go2_candidate_iter_pinned.sh"] = patched_runner(
        source["server_run_go2_candidate_iter_pinned.sh"]
    )

    expected = {"baseline": BASE, "candidate": CANDIDATE}
    arm = {
        "candidate/quadruped_rewards.py": candidate_source,
        "reference/baseline_quadruped_rewards.py": baseline_source,
        "reference/reward_base_quadruped_rewards.py": baseline_source,
        "expected_rewards.json": (json.dumps(expected, indent=2) + "\n").encode(),
        "run_config.env": run_config(source["run_config.env"].decode("utf-8")).encode(),
        "experiment.json": (json.dumps(experiment(), ensure_ascii=False, indent=2) + "\n").encode(),
        "README.txt": (
            "G-A077 starts from the verified G-A074 scientific baseline and changes only "
            "flat_orientation_l2 -0.25 -> -0.225.\nThe embedded baseline contains the iter-2400 "
            "model/env, all 69 stored cases, and 10 videos. No automatic next value is authorized.\n"
        ).encode(),
    }

    materialized: dict[str, Entry] = {key: Entry(data=value) for key, value in shared_bytes.items()}
    materialized["baseline/exported/model_best.pt"] = Entry(path=G074_MODEL)
    materialized["baseline/exported/env.yaml"] = Entry(path=G074_ENV)
    materialized["baseline/exported/report.html"] = Entry(path=G074_REPORT)
    materialized["baseline/exported/report.html.sha256"] = Entry(path=G074_REPORT_SHA)
    materialized["baseline/exported/REPORT_STATUS.txt"] = Entry(path=G074_REPORT_STATUS)
    for path in sorted(G074_EVAL.rglob("*")):
        if path.is_file():
            rel = path.relative_to(G074_EVAL).as_posix()
            materialized[f"baseline/stored_evaluation/{rel}"] = Entry(path=path)
    materialized.update({key: Entry(data=value) for key, value in arm.items()})
    manifest = "".join(f"{materialized[key].digest()}  {key}\n" for key in sorted(materialized)).encode()
    arm["PACKAGE_SHA256SUMS.txt"] = manifest

    outer: dict[str, Entry] = {}
    for key, value in shared_bytes.items():
        if key == "baseline/exported/model_best.pt":
            outer[f"shared/{key}"] = Entry(path=G074_MODEL)
        elif key == "baseline/exported/env.yaml":
            outer[f"shared/{key}"] = Entry(path=G074_ENV)
        else:
            outer[f"shared/{key}"] = Entry(data=value)
    outer["shared/baseline/exported/report.html"] = Entry(path=G074_REPORT)
    outer["shared/baseline/exported/report.html.sha256"] = Entry(path=G074_REPORT_SHA)
    outer["shared/baseline/exported/REPORT_STATUS.txt"] = Entry(path=G074_REPORT_STATUS)
    for path in sorted(G074_EVAL.rglob("*")):
        if path.is_file():
            rel = path.relative_to(G074_EVAL).as_posix()
            outer[f"shared/baseline/stored_evaluation/{rel}"] = Entry(path=path)
    outer.update({f"runs/{KEY}/{key}": Entry(data=value) for key, value in arm.items()})
    outer["points.txt"] = Entry(data=f"{KEY} go2_g_a077_flat_orientation_m0p225 GO2_G_A077_FLAT_ORIENTATION_M0P225_RESULT.zip\n".encode())
    outer["point_config.env"] = Entry(data=(
        "POINT_WORK_ID=G-A077\nPOINT_STATUS_DIR_NAME=go2_g_a077_flat_orientation_m0p225\n"
        "POINT_WORK_DIR=/workspace/go2_g_a077_flat_orientation_m0p225_work\n"
        "POINT_TMUX_NAME=go2_g_a077_flat_orientation_m0p225\n"
    ).encode())
    outer["run_point.sh"] = Entry(data=(ROOT / "tools/go2_pc2_run_point.sh").read_bytes().replace(b"\r\n", b"\n"))
    outer["run_all.sh"] = Entry(data=(
        "#!/usr/bin/env bash\nset -euo pipefail\nROOT_DIR=$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\n"
        f"bash \"$ROOT_DIR/run_point.sh\" --inner {KEY}\n"
    ).encode())
    outer["README.txt"] = Entry(data=(
        "G-A077 PC2 execution\n"
        f"unzip -oq /workspace/{RELEASE}.zip -d /workspace\n"
        f"bash /workspace/{PREFIX.rstrip('/')}/run_all.sh\n"
        "The Go2 USD preflight runs before training; an unavailable asset exits without consuming iterations.\n"
    ).encode())
    top_manifest = "".join(f"{outer[key].digest()}  {key}\n" for key in sorted(outer)).encode()
    outer["SHA256SUMS.txt"] = Entry(data=top_manifest)
    return outer


def write_zip(target: Path) -> dict[str, object]:
    files = entries()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", allowZip64=True) as archive:
        for name in sorted(files):
            entry = files[name]
            info = zipfile.ZipInfo(PREFIX + name, FIXED_TIME)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            suffix = Path(name).suffix.lower()
            info.compress_type = zipfile.ZIP_STORED if suffix in {".mp4", ".pt"} else zipfile.ZIP_DEFLATED
            if entry.data is not None:
                archive.writestr(info, entry.data)
            else:
                assert entry.path is not None
                with entry.path.open("rb") as source_handle, archive.open(info, "w", force_zip64=True) as dest:
                    shutil.copyfileobj(source_handle, dest, 1024 * 1024)
    return {"files": files, "sha": sha_path(target), "bytes": target.stat().st_size}


def publish() -> tuple[Path, dict[str, object]]:
    out = GO2 / "upload" / WORK_ID / "current"
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise FileExistsError(f"refuse overwrite: {out}")
    with tempfile.TemporaryDirectory(dir=out) as temp_dir:
        temp_zip = Path(temp_dir) / f"{RELEASE}.zip"
        info = write_zip(temp_zip)
        sidecar = out / f"{RELEASE}.zip.sha256"
        sidecar.write_text(f"{info['sha']}  {RELEASE}.zip\n", encoding="utf-8", newline="\n")
        if temp_zip.stat().st_size <= 100_000_000:
            final = out / temp_zip.name
            temp_zip.replace(final)
        else:
            with temp_zip.open("rb") as handle:
                index = 1
                while block := handle.read(PART_SIZE):
                    (out / f"{RELEASE}.zip.{index:03d}").write_bytes(block)
                    index += 1
            final = out / f"{RELEASE}.zip.001"
    return final, info


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.publish:
        path, info = publish()
        print(f"published={path.parent} bytes={info['bytes']} sha256={info['sha']}")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / f"{RELEASE}.zip"
            info = write_zip(target)
            print(f"work_id={WORK_ID} files={len(info['files'])} bytes={info['bytes']} sha256={info['sha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
