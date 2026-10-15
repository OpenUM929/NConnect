#!/usr/bin/env python3
"""Build G-A083: one action-rate change from the verified PC2 G-A082 policy (PC2, 3000 iter).

Scientific baseline: the PC2 G-A082 realization (seed 42, 3000 iter, iter-2400
checkpoint 23c08ab1...) and its stored 69-case evaluation + 10 videos.  Same
machine, same seed, same length -> matched comparison at iter 2400.
Single change: action_rate_l2 -0.005 -> -0.01. All other rewards and runtime
files remain unchanged. The stored G-A082 evaluation is reused without rerun.
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

import hashlib
import build_go2_g_a082_package as a082  # noqa: E402

Entry, sha_path, render = a082.Entry, a082.sha_path, a082.render

WORK_ID = "G-A083"
SLUG = "go2_g_a083_action_rate_m0p01"
PREFIX = SLUG + "/"
RELEASE = "GO2_G_A083_ACTION_RATE_M0P01_v1"
RESULT_ZIP = "GO2_G_A083_ACTION_RATE_M0P01_RESULT.zip"
KEY = "action_rate_l2_m0p01"
FIXED_TIME = (2026, 10, 15, 0, 0, 0)
PART_SIZE = 95 * 1024 * 1024

BASE_KEEP = Path(os.environ.get("GO2_G_A082_PC2_KEEP", str(ROOT / "workspace/_keep/go2_g_a082_track_ang_vel_z_p0p75")))
B_MODEL = BASE_KEEP / "training/model_best.pt"
B_ENV = BASE_KEEP / "training/env.yaml"
B_EVAL = BASE_KEEP / "evaluation/candidate"
B_REPORT = BASE_KEEP / "exported/report.html"
B_REPORT_SHA = BASE_KEEP / "exported/report.html.sha256"
B_REPORT_STATUS = BASE_KEEP / "exported/REPORT_STATUS.txt"
B_SOURCE = BASE_KEEP / "training/source"
B_SOURCE_MANIFEST = BASE_KEEP / "training/candidate_source.sha256"
B_MODEL_SHA = "df214dc9aa1fa13acff0e13987943580c3d7d181b60dde282a463e8080bb2f04"
B_ENV_SHA = "862a59adb8b60ac9caa3b5f9e46df3a801bb056198c0bd36a9dfbcf1d4f6dce2"
EVALUATOR_SHA = a082.EVALUATOR_SHA
REGISTRY_SHA = a082.REGISTRY_SHA
VIDEOS = ("G2:combined_yaw_left:101 G2:combined_yaw_right:101 G3:rough_forward:101 G3:rough_lateral:101 "
          "G5:stairs_10_down:101 G5:stairs_15_down:101 G6:push_pos_x:101 G6:push_neg_x:101 "
          "G6:push_pos_y:101 G6:push_neg_y:101")

BASE = dict(a082.CANDIDATE)  # G-A082: action_rate -0.005
CANDIDATE = {**a082.CANDIDATE, "action_rate_l2": -0.01}

IDENTITY_GREP_LINES = a082.IDENTITY_GREP_LINES.replace("G-A077 stored baseline", "G-A083 stored G-A082 baseline")


def validate_baseline() -> None:
    required = (B_MODEL, B_ENV, B_REPORT, B_REPORT_SHA, B_REPORT_STATUS, B_SOURCE_MANIFEST, B_EVAL / "identity.json")
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("missing PC2 G-A082 baseline file: " + ", ".join(missing))
    if sha_path(B_MODEL) != B_MODEL_SHA or sha_path(B_ENV) != B_ENV_SHA:
        raise ValueError("PC2 G-A082 model/env SHA mismatch")
    identity = json.loads((B_EVAL / "identity.json").read_text(encoding="utf-8"))
    for key, value in {"model_sha256": B_MODEL_SHA, "env_sha256": B_ENV_SHA,
                       "evaluator_sha256": EVALUATOR_SHA, "registry_sha256": REGISTRY_SHA}.items():
        if identity.get(key) != value:
            raise ValueError(f"PC2 G-A082 identity {key}={identity.get(key)!r}, expected {value}")
    if len(list((B_EVAL / "cases").rglob("summary.json"))) != 69:
        raise ValueError("PC2 G-A082 baseline is not a complete 69-case evaluation")
    if len(list((B_EVAL / "videos").rglob("*.mp4"))) != 10:
        raise ValueError("PC2 G-A082 baseline does not contain the 10 required videos")


def validate_deployment_source(source: dict[str, bytes], baseline_source: bytes) -> None:
    manifest: dict[str, str] = {}
    for line in B_SOURCE_MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        manifest[relative.lstrip("* ")] = digest
    for name in ("train.py", "play.py", "go2_task/__init__.py", "go2_task/_finalize.py",
                 "go2_task/agent_cfg.py", "go2_task/env_cfg.py"):
        packaged = source[f"candidate/{name}"]
        if (B_SOURCE / name).read_bytes() != packaged or hashlib.sha256(packaged).hexdigest() != manifest[name]:
            raise ValueError(f"deployment source differs from PC2 G-A082: {name}")
    if baseline_source != (B_SOURCE / "quadruped_rewards.py").read_bytes():
        raise ValueError("rendered baseline rewards differ from PC2 G-A082")


def run_config(template: str) -> str:
    replacements = {
        "WORK_ID": WORK_ID,
        "RUN_ID": "train_G-A083-Go2_action_rate_m0p01_3000",
        "EXPERIMENT_SLUG": SLUG,
        "KEEP_DIR_NAME": SLUG,
        "RESULT_ZIP_NAME": RESULT_ZIP,
        "DONE_MARKER": f"'[DONE] {RESULT_ZIP[:-4]}_READY'",
        "TMUX_NAME": SLUG,
        "TRAIN_SEED": "42",
        "NUM_ENVS": "4096",
        "MAX_ITERATIONS": "3000",
        "SINGLE_CHANGE_NAME": "action_rate_l2",
        "SINGLE_CHANGE_FROM": "-0.005",
        "SINGLE_CHANGE_TO": "-0.01",
        "BASELINE_NAME": "G_A082_PC2_VERIFIED",
        "BASELINE_LABEL": "g_a082_pc2",
        "BASELINE_MODEL_SHA": B_MODEL_SHA,
        "BASELINE_ENV_SHA": B_ENV_SHA,
        "EXPECTED_EVALUATOR_SHA": EVALUATOR_SHA,
        "EXPECTED_REGISTRY_SHA": REGISTRY_SHA,
        "EVAL_CHECKPOINT_ITER": "2400",
        "COLLECT_REQUIRED_ON_STATIONARY": "1",
        # The stored baseline arm already holds these ten; counting them removes G-A082's rc31.
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
    text = a082.patched_runner(source).decode("utf-8")
    text = text.replace("G-A077: fail before training", "G-A083: fail before training")
    text = text.replace("G-A077 evaluator/registry differs from the verified G-A074 baseline",
                        "G-A083 evaluator/registry differs from the verified PC2 G-A082 baseline")
    text = text.replace("G-A077 stored G-A074", "G-A083 stored PC2 G-A082")
    text = text.replace("G-A077 matched G-A074 report", "G-A083 matched PC2 G-A082 report")
    text = text.replace("materialized G-A074 baseline", "materialized PC2 G-A082 baseline")
    text = text.replace("reuse identity-pinned G-A074 baseline", "reuse identity-pinned PC2 G-A082 baseline")
    text = text.replace("REUSED_G_A074_FULL_NO_RERUN", "REUSED_G_A082_PC2_FULL_NO_RERUN")
    text = text.replace("G-A077 reuses the ten identity-pinned G-A074 videos",
                        "G-A083 reuses the ten identity-pinned PC2 G-A082 videos")
    text = text.replace("[FAIL] G-A077 stored baseline identity mismatch", "[FAIL] G-A083 stored G-A082 baseline identity mismatch")
    text = text.replace("G-A082: fail before training", "G-A083: fail before training")
    text = text.replace("G-A082 evaluator/registry differs from the verified PC2 G-A077 baseline",
                        "G-A083 evaluator/registry differs from the verified PC2 G-A082 baseline")
    text = text.replace("G-A082 stored PC2 G-A077", "G-A083 stored PC2 G-A082")
    text = text.replace("G-A082 matched PC2 G-A077 report", "G-A083 matched PC2 G-A082 report")
    text = text.replace("materialized PC2 G-A077 baseline", "materialized PC2 G-A082 baseline")
    text = text.replace("reuse identity-pinned PC2 G-A077 baseline", "reuse identity-pinned PC2 G-A082 baseline")
    text = text.replace("REUSED_G_A077_PC2_FULL_NO_RERUN", "REUSED_G_A082_PC2_FULL_NO_RERUN")
    text = text.replace("G-A082 reuses the ten identity-pinned PC2 G-A077 videos",
                        "G-A083 reuses the ten identity-pinned PC2 G-A082 videos")
    text = text.replace("[FAIL] G-A082 stored G-A077 baseline identity mismatch",
                        "[FAIL] G-A083 stored G-A082 baseline identity mismatch")
    return text.encode("utf-8")


def experiment() -> dict:
    return {
        "schema": "go2_g_a083_single_change_v1",
        "work_id": WORK_ID,
        "device": "PC2",
        "run_key": KEY,
        "purpose": "Test whether strengthening action smoothness pressure lowers the unusually high exploration std while improving G6 push tracking and preserving G5 15cm stair survival.",
        "promotion": "exploratory_single_seed_no_automatic_followup",
        "baseline": {
            "work_id": "G-A082 (PC2 realization)",
            "checkpoint_iter": 2400,
            "model_sha256": B_MODEL_SHA,
            "env_sha256": B_ENV_SHA,
            "evaluation": "reused stored full 69-case evaluation and 10 videos; no baseline training or evaluation rerun",
            "internal_proxy_points_70": 56.85,
            "baseline_label": "G_A082_PC2_VERIFIED",
        },
        "single_change": {
            "name": "action_rate_l2",
            "from": -0.005,
            "to": -0.01,
            "value_design": "The deployment start value is fixed by the approved decision; no alternative value is proposed. All other six rewards remain identical to G-A082.",
        },
        "evidence_basis": {
            "observation": "Compared Policy/mean_std across prior trainings: action_rate -0.01 runs A010-A042 were 0.41-0.62 at iter 1000, while -0.005 runs G-A077/G-A079 were 0.79-0.86; G-A082 reached 1.03 at iter 2400 and 1.07 at the end. G-A082 base_contact was 0.25 at iter 2400 versus G-A077 PC2 0.16.",
            "remaining_target_losses": "G-A082 stairs_15_up=0.844 and stairs_15_down=0.906, mean 0.875, versus G-A077 PC2 0.958 and 0.979; G6 push xy error mean 0.081 versus 0.049.",
            "mechanism": "The policy adds independent per-step noise with standard deviation sigma; action_rate_l2 is ||a_t-a_(t-1)||^2, so its expectation contains a sigma^2 term. Moving the negative weight from -0.005 to -0.01 restores stronger pressure against noisy action changes.",
            "lecture": "GO2_LECTURE_REWARD_REFERENCE.md section 5-⑤: strong gives smooth but sluggish response; weak gives agile but leg trembling.",
            "trial_history": "G-A063 s13: -0.005 increased 15cm >=2-stair count 3->19 but worsened rough lateral falls 41->60, DR 8->19, and push falls 0->5. G-A063 s12 at -0.02 collapsed rough terrain and stairs; do not go stronger than -0.01.",
            "unknown": "The causal reason G-A082 exceeded std 1.0 is unknown. A competing explanation is that the other G-A082 changes (track_lin_vel_xy 2.0, lin_vel_z_l2 -3, feet_air_time 0.01) caused the rise; if so, reverting action_rate will not lower std.",
        },
        "rewards": CANDIDATE,
        "training": {"seed": 42, "num_envs": 4096, "max_iterations": 3000, "from_scratch": True},
        "evaluation": {"checkpoint_iter": 2400, "seeds": [101, 202, 303], "case_count": 69, "baseline": "reused G-A082 PC2 stored evaluation"},
        "hypothesis": {
            "direction": "Changing action_rate_l2 from -0.005 to -0.01 will reduce exploration std and may reduce G6 push xy tracking error.",
            "competing": "The high std is caused by the other G-A082 reward changes, so action_rate_l2 alone will not reduce it.",
            "mechanism": "Independent action noise contributes a sigma^2 term to expected action-rate cost; a more negative weight should increase pressure against rapid action changes.",
            "lecture_prediction": "The lecture predicts stronger action-rate pressure as smoother but potentially more sluggish, while weaker pressure is more agile but can tremble.",
            "unknown": "Why G-A082 std exceeded 1.0 is not established by the observations.",
        },
        "preregistered_predictions": {
            "primary": {
                "metric": "Policy/mean_std mean over iter 2380-2420",
                "supported_if": "<= 0.80",
                "refuted_if": ">= 0.98",
                "otherwise": "INCONCLUSIVE",
                "reference": "G-A082=1.03 at iter 2400",
            },
            "secondary": {
                "g6_push_xy_error_mean": {
                    "metric": "tools/go2_weakness_breakdown.py exy_mean over the 12 G6 push rows",
                    "supported_if": "<= 0.065",
                    "reference": "G-A082=0.081",
                },
                "stairs_15_survival_proxy_mean": {
                    "metric": "mean of stairs_15_up and stairs_15_down over seed 3",
                    "supported_if": ">= 0.92",
                    "reference": "G-A082=0.875",
                },
            },
            "protection": {
                "head_direction_change_median": "slope_plus_20, stairs_10_down, stairs_15_down each <= 40 degrees; G-A082=25.6/18.0/16.2",
                "stairs_15_down_full_proxy_sum": ">= 51, the G-A077 PC2 level; G-A082=92",
                "G3_survival_sum": ">= 5.75",
                "terrain_command_direction_speed_mean": ">= 0.425 m/s for G3/G4/G5",
                "G2_combined_yaw": "all 6 rows survival=1.0",
                "all_69_cases": "report only; not a single veto",
            },
        },
        "score_model": "Report the H1 official-fit inverse formula from go2_weakness_breakdown beside the internal proxy; G-A082 reference=56.85.",
        "divergence_plan": {
            "pinned_checkpoint": "iter 2400 is the evaluation checkpoint and must be retained.",
            "if_train_rc_nonzero_after_2400": "Retain the partial result and evaluate the pinned iter-2400 checkpoint; divergence alone does not reject the setting.",
            "if_diverged_before_2400": "Record DIVERGED_BEFORE_PIN; do not change seed or automatically retry.",
        },
        "result_use": {
            "supported_and_protected": "Review as a candidate instead of G-A082.",
            "supported_but_protection_lost": "Keep G-A082 and identify the lost protection axis.",
            "refuted": "Keep G-A082; do not treat action_rate_l2 as the std lever.",
            "diverged": "Judge after the pinned iter-2400 evaluation.",
        },
        "decision_authority": {
            "legacy_runner_gate": "NON_AUTHORITATIVE; execution safety and collection status only.",
            "preregistered_threshold_enforcement": "POSTHOC_AUTHOR_CHECKER_REQUIRED",
        },
        "asset_preflight": {"url": a082.a077.GO2_USD_URL, "must_pass_before_training": True},
    }
def entries() -> dict[str, Entry]:
    validate_baseline()
    # Same runtime source chain as G-A082 (a076 adds the Isaac-Lab-first python pick;
    # a057 reads the G-A055 package and adds package_go2_result.py and the checkers).
    source = a082.a076.source_payload()
    shared_bytes = a082.a057.shared_files(source)
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
            "G-A083 starts from the PC2 G-A082 realization and changes only "
            "action_rate_l2 -0.005 -> -0.01.\nThe embedded baseline contains the iter-2400 model/env, "
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
        f"G-A083 PC2 execution\nunzip -oq /workspace/{RELEASE}.zip -d /workspace\n"
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


