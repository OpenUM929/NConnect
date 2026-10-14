#!/usr/bin/env python3
"""Build G-A082: one yaw-tracking change from the PC2 G-A077 policy (PC2, 3000 iter).

Scientific baseline: the PC2 G-A077 realization (seed 42, 3000 iter, iter-2400
checkpoint 23c08ab1...) and its stored 69-case evaluation + 10 videos.  Same
machine, same seed, same length -> matched comparison at iter 2400.
Single change: track_ang_vel_z_exp 0.30 -> 0.75 (Isaac Lab Go2 rough default and
the value every A033..A048 policy trained with).  Everything else is G-A077.
Runtime code is the G-A077 package's (via build_go2_g_a077_package); only the
baseline identity, the one reward and names are replaced.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as a033  # noqa: E402,F401
import build_go2_g_a057_sweep_package as a057  # noqa: E402
import build_go2_g_a076_report_policy_retry_package as a076  # noqa: E402
import build_go2_g_a077_package as a077  # noqa: E402

Entry, sha_path, render = a077.Entry, a077.sha_path, a077.render

WORK_ID = "G-A082"
SLUG = "go2_g_a082_track_ang_vel_z_p0p75"
PREFIX = SLUG + "/"
RELEASE = "GO2_G_A082_TRACK_ANG_VEL_Z_P0P75_v1"
RESULT_ZIP = "GO2_G_A082_TRACK_ANG_VEL_Z_P0P75_RESULT.zip"
KEY = "track_ang_vel_z_exp_p0p75"
FIXED_TIME = (2026, 10, 14, 0, 0, 0)
PART_SIZE = 95 * 1024 * 1024

BASE_KEEP = Path(os.environ.get("GO2_G_A077_PC2_KEEP", str(ROOT / "workspace/_keep/go2_g_a077_flat_orientation_m0p225")))
B_MODEL = BASE_KEEP / "training/model_best.pt"
B_ENV = BASE_KEEP / "training/env.yaml"
B_EVAL = BASE_KEEP / "evaluation/candidate"
B_REPORT = BASE_KEEP / "exported/report.html"
B_REPORT_SHA = BASE_KEEP / "exported/report.html.sha256"
B_REPORT_STATUS = BASE_KEEP / "exported/REPORT_STATUS.txt"
B_SOURCE = BASE_KEEP / "training/source"
B_SOURCE_MANIFEST = BASE_KEEP / "training/candidate_source.sha256"
B_MODEL_SHA = "23c08ab15617b0001ee90d20c2682cf78041d80058bd83c1d090fdf94d756ca1"
B_ENV_SHA = "825fdc698328e1d886c8c7ae9f9d0cfdcc24e818851ed2b1b6484b2b836fd88d"
EVALUATOR_SHA = a077.EVALUATOR_SHA
REGISTRY_SHA = a077.REGISTRY_SHA
VIDEOS = ("G2:combined_yaw_left:101 G2:combined_yaw_right:101 G3:rough_forward:101 G3:rough_lateral:101 "
          "G5:stairs_10_down:101 G5:stairs_15_down:101 G6:push_pos_x:101 G6:push_neg_x:101 "
          "G6:push_pos_y:101 G6:push_neg_y:101")

BASE = dict(a077.CANDIDATE)  # G-A077: flat -0.225, track_ang_vel_z 0.30
CANDIDATE = {**BASE, "track_ang_vel_z_exp": 0.75}

IDENTITY_GREP_LINES = a077.IDENTITY_GREP_LINES.replace("G-A077 stored baseline", "G-A082 stored G-A077 baseline")


def validate_baseline() -> None:
    required = (B_MODEL, B_ENV, B_REPORT, B_REPORT_SHA, B_REPORT_STATUS, B_SOURCE_MANIFEST, B_EVAL / "identity.json")
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("missing PC2 G-A077 baseline file: " + ", ".join(missing))
    if sha_path(B_MODEL) != B_MODEL_SHA or sha_path(B_ENV) != B_ENV_SHA:
        raise ValueError("PC2 G-A077 model/env SHA mismatch")
    identity = json.loads((B_EVAL / "identity.json").read_text(encoding="utf-8"))
    for key, value in {"model_sha256": B_MODEL_SHA, "env_sha256": B_ENV_SHA,
                       "evaluator_sha256": EVALUATOR_SHA, "registry_sha256": REGISTRY_SHA}.items():
        if identity.get(key) != value:
            raise ValueError(f"PC2 G-A077 identity {key}={identity.get(key)!r}, expected {value}")
    if len(list((B_EVAL / "cases").rglob("summary.json"))) != 69:
        raise ValueError("PC2 G-A077 baseline is not a complete 69-case evaluation")
    if len(list((B_EVAL / "videos").rglob("*.mp4"))) != 10:
        raise ValueError("PC2 G-A077 baseline does not contain the 10 required videos")


def validate_deployment_source(source: dict[str, bytes], baseline_source: bytes) -> None:
    manifest: dict[str, str] = {}
    for line in B_SOURCE_MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        manifest[relative.lstrip("* ")] = digest
    for name in ("train.py", "play.py", "go2_task/__init__.py", "go2_task/_finalize.py",
                 "go2_task/agent_cfg.py", "go2_task/env_cfg.py"):
        packaged = source[f"candidate/{name}"]
        if (B_SOURCE / name).read_bytes() != packaged or a077.hashlib.sha256(packaged).hexdigest() != manifest[name]:
            raise ValueError(f"deployment source differs from PC2 G-A077: {name}")
    if baseline_source != (B_SOURCE / "quadruped_rewards.py").read_bytes():
        raise ValueError("rendered baseline rewards differ from PC2 G-A077")


def run_config(template: str) -> str:
    replacements = {
        "WORK_ID": WORK_ID,
        "RUN_ID": "train_G-A082-Go2_track_ang_vel_z_p0p75_3000",
        "EXPERIMENT_SLUG": SLUG,
        "KEEP_DIR_NAME": SLUG,
        "RESULT_ZIP_NAME": RESULT_ZIP,
        "DONE_MARKER": f"'[DONE] {RESULT_ZIP[:-4]}_READY'",
        "TMUX_NAME": SLUG,
        "TRAIN_SEED": "42",
        "NUM_ENVS": "4096",
        "MAX_ITERATIONS": "3000",
        "SINGLE_CHANGE_NAME": "track_ang_vel_z_exp",
        "SINGLE_CHANGE_FROM": "0.3",
        "SINGLE_CHANGE_TO": "0.75",
        "BASELINE_NAME": "G_A077_PC2_VERIFIED",
        "BASELINE_LABEL": "g_a077_pc2",
        "BASELINE_MODEL_SHA": B_MODEL_SHA,
        "BASELINE_ENV_SHA": B_ENV_SHA,
        "EXPECTED_EVALUATOR_SHA": EVALUATOR_SHA,
        "EXPECTED_REGISTRY_SHA": REGISTRY_SHA,
        "EVAL_CHECKPOINT_ITER": "2400",
        "COLLECT_REQUIRED_ON_STATIONARY": "1",
        # The stored baseline arm already holds these ten; counting them removes G-A077's rc31.
        "BASELINE_VIDEOS": f"({VIDEOS})",
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
    text = a077.patched_runner(source).decode("utf-8")
    text = text.replace("G-A077: fail before training", "G-A082: fail before training")
    text = text.replace("G-A077 evaluator/registry differs from the verified G-A074 baseline",
                        "G-A082 evaluator/registry differs from the verified PC2 G-A077 baseline")
    text = text.replace("G-A077 stored G-A074", "G-A082 stored PC2 G-A077")
    text = text.replace("G-A077 matched G-A074 report", "G-A082 matched PC2 G-A077 report")
    text = text.replace("materialized G-A074 baseline", "materialized PC2 G-A077 baseline")
    text = text.replace("reuse identity-pinned G-A074 baseline", "reuse identity-pinned PC2 G-A077 baseline")
    text = text.replace("REUSED_G_A074_FULL_NO_RERUN", "REUSED_G_A077_PC2_FULL_NO_RERUN")
    text = text.replace("G-A077 reuses the ten identity-pinned G-A074 videos",
                        "G-A082 reuses the ten identity-pinned PC2 G-A077 videos")
    text = text.replace("[FAIL] G-A077 stored baseline identity mismatch", "[FAIL] G-A082 stored G-A077 baseline identity mismatch")
    return text.encode("utf-8")


def experiment() -> dict:
    return {
        "schema": "go2_g_a082_single_change_v1",
        "work_id": WORK_ID,
        "device": "PC2",
        "run_key": KEY,
        "purpose": "Stop the uncorrected slow body yaw on slope-up and stair-down cases while keeping G-A077 stair and rough-terrain behaviour.",
        "promotion": "exploratory_single_seed_no_automatic_followup",
        "baseline": {
            "work_id": "G-A077 (PC2 realization)",
            "checkpoint_iter": 2400,
            "model_sha256": B_MODEL_SHA,
            "env_sha256": B_ENV_SHA,
            "evaluation": "stored posture_gate_v2 full 69 cases and 10 videos, same PC2, seed 42, 3000 iter",
            "internal_proxy_points_70": 63.005493,
        },
        "single_change": {
            "name": "track_ang_vel_z_exp",
            "from": 0.30,
            "to": 0.75,
            "value_design": ("0.75 is the Isaac Lab Go2 rough default and the value A033/A042/A043/A048 trained with; "
                             "1.0 collapsed posture on A043 (G-A062 Q1) so 0.75 is the upper bound with evidence. "
                             "Ratio to track_lin 2.0 is 0.375, below A033's 0.5."),
        },
        "evidence_basis": {
            "observation": "workspace/training/quadruped/reports/GO2_G_A077_WEAKNESS_20261014.md sections 4-5",
            "failure_mode": ("UNDER-correction: yaw-rate peaks keep 35-53% of their value 1.2 s later with no overshoot; "
                             "heading change median 106-156 deg on slope_plus_20, stairs_10_down, stairs_15_down with cmd_wz=0"),
            "comparison": "A033/A042 (0.75) heading change median 7-22 deg on the same cases; confounded by five other rewards",
            "reward_formula": "exp(-(wz_cmd - wz)^2 / sigma^2) rewards holding wz=0 when commanded 0",
            "lecture": "no direct lecture prediction for zero-command heading drift (GO2_LECTURE_REWARD_REFERENCE.md 7-7)",
            "trial_history": "GO2_REWARD_TRIAL_REFERENCE.md 3-7: only 0.75->1.0 tested (collapse); 0.3->0.75 untested",
        },
        "rewards": CANDIDATE,
        "training": {"seed": 42, "num_envs": 4096, "max_iterations": 3000, "from_scratch": True},
        "evaluation": {"checkpoint_iter": 2400, "seeds": [101, 202, 303], "case_count": 69},
        "hypothesis": {
            "direction": "A larger yaw-tracking reward makes the policy hold zero yaw rate on slope and stair-down terrain.",
            "competing": "The yaw drift is the policy turning to traverse terrain; suppressing it may cost stair progress or survival.",
            "not_expected_to_change": "stairs_15_up and rough_lateral drift (A033/A042 at 0.75 drifted 37-49 deg there too)",
        },
        "preregistered_predictions": {
            "primary": {
                "metric": "per-robot |heading change| median, deg (tools/go2_yaw_oscillation_response.py method)",
                "cases": {"slope_plus_20": 108.4, "stairs_10_down": 105.5, "stairs_15_down": 156.1},
                "supported_if": "all three medians fall below half of the baseline value",
                "refuted_if": "none of the three falls below 0.8 x baseline",
                "otherwise": "INCONCLUSIVE",
            },
            "protection": {
                "stairs_15_full_count_each_seed_baseline": "read from stored baseline, candidate must not be lower in sum",
                "G3_survival": "candidate G3 survival_proxy sum over cases/seeds not lower than baseline by more than 1 robot-episode per case",
                "terrain_along_command_speed": "mean along-command speed on rough/slope/stairs not lower than baseline by more than 0.03 m/s",
                "G2_combined_yaw": "survival 1.0 and yaw tracking not worse than baseline",
                "all_69_case_protection": "reported, not used as a single veto (same as G-A077)",
            },
            "score_model": "H1 official-fit formula (workspace/calibration/h1_official_20260910/formula_fit_20261014) reported beside internal proxy",
            "result_use": "One exploratory result; do not automatically try another track_ang_vel_z_exp value.",
        },
        "divergence_plan": {
            "pinned_checkpoint": "model_2400 is copied during training (runner CHECKPOINT PIN) and kept in the result even if training later fails",
            "if_train_rc_nonzero_after_2400": "collect the PARTIAL result; the author issues an evaluation-only package for the pinned iter-2400 checkpoint; divergence alone does not reject the setting",
            "if_diverged_before_2400": "record DIVERGED_BEFORE_PIN; no automatic retry, no seed change, no further raise of this weight",
        },
        "decision_authority": {
            "legacy_runner_gate": "NON_AUTHORITATIVE; execution-safety/collection status only",
            "preregistered_threshold_enforcement": "POSTHOC_AUTHOR_CHECKER_REQUIRED",
        },
        "asset_preflight": {"url": a077.GO2_USD_URL, "must_pass_before_training": True},
    }


def entries() -> dict[str, Entry]:
    validate_baseline()
    source = a076.source_payload()
    shared_bytes = a057.shared_files(source)
    template = source["candidate/quadruped_rewards.py"].decode("utf-8")
    baseline_source = render(template, BASE).encode("utf-8")
    candidate_source = render(template, CANDIDATE).encode("utf-8")
    validate_deployment_source(source, baseline_source)
    shared_bytes["candidate/quadruped_rewards.py"] = candidate_source
    shared_bytes["baseline/quadruped_rewards.py"] = baseline_source
    shared_bytes.pop("baseline/exported/model_best.pt", None)
    shared_bytes.pop("baseline/exported/env.yaml", None)
    shared_bytes["server_run_go2_candidate_iter_pinned.sh"] = patched_runner(source["server_run_go2_candidate_iter_pinned.sh"])

    arm = {
        "candidate/quadruped_rewards.py": candidate_source,
        "reference/baseline_quadruped_rewards.py": baseline_source,
        "reference/reward_base_quadruped_rewards.py": baseline_source,
        "expected_rewards.json": (json.dumps({"baseline": BASE, "candidate": CANDIDATE}, indent=2) + "\n").encode(),
        "run_config.env": run_config(source["run_config.env"].decode("utf-8")).encode(),
        "experiment.json": (json.dumps(experiment(), ensure_ascii=False, indent=2) + "\n").encode(),
        "README.txt": (
            "G-A082 starts from the PC2 G-A077 realization and changes only "
            "track_ang_vel_z_exp 0.3 -> 0.75.\nThe embedded baseline contains the iter-2400 model/env, "
            "all 69 stored cases and 10 videos. No automatic next value is authorized.\n"
        ).encode(),
    }
    baseline_files = {
        "baseline/exported/model_best.pt": Entry(path=B_MODEL),
        "baseline/exported/env.yaml": Entry(path=B_ENV),
        "baseline/exported/report.html": Entry(path=B_REPORT),
        "baseline/exported/report.html.sha256": Entry(path=B_REPORT_SHA),
        "baseline/exported/REPORT_STATUS.txt": Entry(path=B_REPORT_STATUS),
    }
    for path in sorted(B_EVAL.rglob("*")):
        if path.is_file():
            baseline_files[f"baseline/stored_evaluation/{path.relative_to(B_EVAL).as_posix()}"] = Entry(path=path)

    materialized: dict[str, Entry] = {k: Entry(data=v) for k, v in shared_bytes.items()}
    materialized.update(baseline_files)
    materialized.update({k: Entry(data=v) for k, v in arm.items()})
    arm["PACKAGE_SHA256SUMS.txt"] = "".join(
        f"{materialized[k].digest()}  {k}\n" for k in sorted(materialized)).encode()

    outer: dict[str, Entry] = {f"shared/{k}": Entry(data=v) for k, v in shared_bytes.items()}
    outer.update({f"shared/{k}": v for k, v in baseline_files.items()})
    outer.update({f"runs/{KEY}/{k}": Entry(data=v) for k, v in arm.items()})
    outer["points.txt"] = Entry(data=f"{KEY} {SLUG} {RESULT_ZIP}\n".encode())
    outer["point_config.env"] = Entry(data=(
        f"POINT_WORK_ID={WORK_ID}\nPOINT_STATUS_DIR_NAME={SLUG}\n"
        f"POINT_WORK_DIR=/workspace/{SLUG}_work\nPOINT_TMUX_NAME={SLUG}\n").encode())
    outer["run_point.sh"] = Entry(data=(ROOT / "tools/go2_pc2_run_point.sh").read_bytes().replace(b"\r\n", b"\n"))
    outer["run_all.sh"] = Entry(data=(
        "#!/usr/bin/env bash\nset -euo pipefail\nROOT_DIR=$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\n"
        f"bash \"$ROOT_DIR/run_point.sh\" --inner {KEY}\n").encode())
    outer["README.txt"] = Entry(data=(
        f"G-A082 PC2 execution\nunzip -oq /workspace/{RELEASE}.zip -d /workspace\n"
        f"bash /workspace/{SLUG}/run_all.sh\n"
        "The Go2 USD preflight runs before training; an unavailable asset exits without consuming iterations.\n").encode())
    outer["SHA256SUMS.txt"] = Entry(data="".join(f"{outer[k].digest()}  {k}\n" for k in sorted(outer)).encode())
    return outer


def write_zip(target: Path) -> dict[str, object]:
    files = entries()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", allowZip64=True) as archive:
        for name in sorted(files):
            entry = files[name]
            info = zipfile.ZipInfo(PREFIX + name, FIXED_TIME)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_STORED if Path(name).suffix.lower() in {".mp4", ".pt"} else zipfile.ZIP_DEFLATED
            if entry.data is not None:
                archive.writestr(info, entry.data)
            else:
                with entry.path.open("rb") as src, archive.open(info, "w", force_zip64=True) as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
    return {"files": files, "sha": sha_path(target), "bytes": target.stat().st_size}


def publish() -> tuple[Path, dict[str, object]]:
    out = GO2 / "upload" / WORK_ID / "current"
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise FileExistsError(f"refuse overwrite: {out}")
    with tempfile.TemporaryDirectory(dir=out) as temp_dir:
        temp_zip = Path(temp_dir) / f"{RELEASE}.zip"
        info = write_zip(temp_zip)
        (out / f"{RELEASE}.zip.sha256").write_text(f"{info['sha']}  {RELEASE}.zip\n", encoding="utf-8", newline="\n")
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
            info = write_zip(Path(temp_dir) / f"{RELEASE}.zip")
            print(f"work_id={WORK_ID} files={len(info['files'])} bytes={info['bytes']} sha256={info['sha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
