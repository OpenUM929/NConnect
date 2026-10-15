#!/usr/bin/env python3
"""Build G-A084: one ang_vel_xy change from the verified PC2 G-A083 policy (PC2, 3000 iter).

Scientific baseline: the PC2 G-A083 realization (seed 42, 3000 iter, iter-2400
checkpoint bbbc04f4...) and its stored 69-case evaluation + 10 videos.  Same
machine, same seed, same length -> matched comparison at iter 2400.
Single change: ang_vel_xy_l2 -0.05 -> -0.065. All other rewards and runtime
files remain unchanged. The stored G-A083 evaluation is reused without rerun.
The runtime chain is the G-A083 one (a082 -> a076 source payload, a057 shared files).
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
import build_go2_g_a083_package as a083  # noqa: E402

a082 = a083.a082

Entry, sha_path, render = a082.Entry, a082.sha_path, a082.render

WORK_ID = "G-A084"
SLUG = "go2_g_a084_ang_vel_xy_m0p065"
PREFIX = SLUG + "/"
RELEASE = "GO2_G_A084_ANG_VEL_XY_M0P065_v1"
RESULT_ZIP = "GO2_G_A084_ANG_VEL_XY_M0P065_RESULT.zip"
KEY = "ang_vel_xy_l2_m0p065"
FIXED_TIME = (2026, 10, 15, 0, 0, 0)
PART_SIZE = 95 * 1024 * 1024

BASE_KEEP = Path(os.environ.get("GO2_G_A083_PC2_KEEP", str(ROOT / "workspace/_keep/go2_g_a083_action_rate_m0p01")))
B_MODEL = BASE_KEEP / "training/model_best.pt"
B_ENV = BASE_KEEP / "training/env.yaml"
B_EVAL = BASE_KEEP / "evaluation/candidate"
B_REPORT = BASE_KEEP / "exported/report.html"
B_REPORT_SHA = BASE_KEEP / "exported/report.html.sha256"
B_REPORT_STATUS = BASE_KEEP / "exported/REPORT_STATUS.txt"
B_SOURCE = BASE_KEEP / "training/source"
B_SOURCE_MANIFEST = BASE_KEEP / "training/candidate_source.sha256"
B_MODEL_SHA = "bbbc04f4624f6c1401f20b7937a3f8ed82427a288b0158525efb48091e07b27a"
B_ENV_SHA = "8bf58925f6de58206967d12d556d1e0cf4de76de5218195a14e5f3e25011e513"
EVALUATOR_SHA = a082.EVALUATOR_SHA
REGISTRY_SHA = a082.REGISTRY_SHA
VIDEOS = ("G2:combined_yaw_left:101 G2:combined_yaw_right:101 G3:rough_forward:101 G3:rough_lateral:101 "
          "G5:stairs_10_down:101 G5:stairs_15_down:101 G6:push_pos_x:101 G6:push_neg_x:101 "
          "G6:push_pos_y:101 G6:push_neg_y:101")

BASE = dict(a083.CANDIDATE)  # G-A083: ang_vel_xy -0.05, action_rate -0.01
CANDIDATE = {**a083.CANDIDATE, "ang_vel_xy_l2": -0.065}

IDENTITY_GREP_LINES = a083.IDENTITY_GREP_LINES.replace("G-A083 stored G-A082 baseline", "G-A084 stored G-A083 baseline")


def validate_baseline() -> None:
    required = (B_MODEL, B_ENV, B_REPORT, B_REPORT_SHA, B_REPORT_STATUS, B_SOURCE_MANIFEST, B_EVAL / "identity.json")
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("missing PC2 G-A083 baseline file: " + ", ".join(missing))
    if sha_path(B_MODEL) != B_MODEL_SHA or sha_path(B_ENV) != B_ENV_SHA:
        raise ValueError("PC2 G-A083 model/env SHA mismatch")
    identity = json.loads((B_EVAL / "identity.json").read_text(encoding="utf-8"))
    for key, value in {"model_sha256": B_MODEL_SHA, "env_sha256": B_ENV_SHA,
                       "evaluator_sha256": EVALUATOR_SHA, "registry_sha256": REGISTRY_SHA}.items():
        if identity.get(key) != value:
            raise ValueError(f"PC2 G-A083 identity {key}={identity.get(key)!r}, expected {value}")
    if len(list((B_EVAL / "cases").rglob("summary.json"))) != 69:
        raise ValueError("PC2 G-A083 baseline is not a complete 69-case evaluation")
    if len(list((B_EVAL / "videos").rglob("*.mp4"))) != 10:
        raise ValueError("PC2 G-A083 baseline does not contain the 10 required videos")


def validate_deployment_source(source: dict[str, bytes], baseline_source: bytes) -> None:
    manifest: dict[str, str] = {}
    for line in B_SOURCE_MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        manifest[relative.lstrip("* ")] = digest
    for name in ("train.py", "play.py", "go2_task/__init__.py", "go2_task/_finalize.py",
                 "go2_task/agent_cfg.py", "go2_task/env_cfg.py"):
        packaged = source[f"candidate/{name}"]
        if (B_SOURCE / name).read_bytes() != packaged or hashlib.sha256(packaged).hexdigest() != manifest[name]:
            raise ValueError(f"deployment source differs from PC2 G-A083: {name}")
    if baseline_source != (B_SOURCE / "quadruped_rewards.py").read_bytes():
        raise ValueError("rendered baseline rewards differ from PC2 G-A083")


def run_config(template: str) -> str:
    replacements = {
        "WORK_ID": WORK_ID,
        "RUN_ID": "train_G-A084-Go2_ang_vel_xy_m0p065_3000",
        "EXPERIMENT_SLUG": SLUG,
        "KEEP_DIR_NAME": SLUG,
        "RESULT_ZIP_NAME": RESULT_ZIP,
        "DONE_MARKER": f"'[DONE] {RESULT_ZIP[:-4]}_READY'",
        "TMUX_NAME": SLUG,
        "TRAIN_SEED": "42",
        "NUM_ENVS": "4096",
        "MAX_ITERATIONS": "3000",
        "SINGLE_CHANGE_NAME": "ang_vel_xy_l2",
        "SINGLE_CHANGE_FROM": "-0.05",
        "SINGLE_CHANGE_TO": "-0.065",
        "BASELINE_NAME": "G_A083_PC2_VERIFIED",
        "BASELINE_LABEL": "g_a083_pc2",
        "BASELINE_MODEL_SHA": B_MODEL_SHA,
        "BASELINE_ENV_SHA": B_ENV_SHA,
        "EXPECTED_EVALUATOR_SHA": EVALUATOR_SHA,
        "EXPECTED_REGISTRY_SHA": REGISTRY_SHA,
        "EVAL_CHECKPOINT_ITER": "2400",
        "COLLECT_REQUIRED_ON_STATIONARY": "1",
        # The stored baseline arm already holds these ten; same list as G-A082 and G-A083.
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
    text = a083.patched_runner(source).decode("utf-8")
    for old, new in (
        ("G-A083: fail before training", "G-A084: fail before training"),
        ("G-A083 evaluator/registry differs from the verified PC2 G-A082 baseline",
         "G-A084 evaluator/registry differs from the verified PC2 G-A083 baseline"),
        ("G-A083 stored PC2 G-A082", "G-A084 stored PC2 G-A083"),
        ("G-A083 matched PC2 G-A082 report", "G-A084 matched PC2 G-A083 report"),
        ("materialized PC2 G-A082 baseline", "materialized PC2 G-A083 baseline"),
        ("reuse identity-pinned PC2 G-A082 baseline", "reuse identity-pinned PC2 G-A083 baseline"),
        ("REUSED_G_A082_PC2_FULL_NO_RERUN", "REUSED_G_A083_PC2_FULL_NO_RERUN"),
        ("G-A083 reuses the ten identity-pinned PC2 G-A082 videos",
         "G-A084 reuses the ten identity-pinned PC2 G-A083 videos"),
        ("[FAIL] G-A083 stored G-A082 baseline identity mismatch",
         "[FAIL] G-A084 stored G-A083 baseline identity mismatch"),
    ):
        text = text.replace(old, new)
    return text.encode("utf-8")


def experiment() -> dict:
    return {
        "schema": "go2_g_a084_single_change_v1",
        "work_id": WORK_ID,
        "device": "PC2",
        "run_key": KEY,
        "purpose": "Test whether a stronger roll/pitch angular-rate penalty reduces the remaining tilt-type falls on rough terrain and under push, and the post-push xy drift, while keeping the G-A083 stair, heading and speed gains.",
        "promotion": "exploratory_single_seed_no_automatic_followup",
        "baseline": {
            "work_id": "G-A083 (PC2 realization)",
            "checkpoint_iter": 2400,
            "model_sha256": B_MODEL_SHA,
            "env_sha256": B_ENV_SHA,
            "evaluation": "reused stored full 69-case evaluation and 10 videos; no baseline training or evaluation rerun",
            "internal_proxy_points_70": 57.59,
            "legacy_worst_case_proxy_70": 63.48,
            "baseline_label": "G_A083_PC2_VERIFIED",
        },
        "single_change": {
            "name": "ang_vel_xy_l2",
            "from": -0.05,
            "to": -0.065,
            "value_design": "Toward the deployment start value -0.08 by about half of the gap. -0.08 itself was tested twice (G-A038 on A033, G-A055 on A043) and both times broke stair climbing; -0.06 (G-A062 Q2 on A043 rewards) cut rough-lateral falls 76->41 without breaking 15cm stairs. -0.065 is untested on any baseline. All other six rewards remain identical to G-A083.",
        },
        "evidence_basis": {
            "observation": "G-A083 iter 2400: 12 fallen robots over 69 cases; 7 are tilt-type (rough_forward 2, rough_lateral 1, push 4), the rest low-type on stairs/DR. G6 push xy error mean 0.072 missed the preregistered 0.065 (G-A077 PC2 0.049). Training base_contact at iter 2380-2420 is 0.198 and report.html shows a 15.2% final training fall rate. Score losses are mostly tracking (11.59 of 12.41 points); G3 rough is the largest scenario loss (2.94 points incl. 0.44 survival).",
            "report_html": "The G-A083 report marks the policy as aggressive: track_lin_vel_xy +1 over the deployment start and ang_vel_xy_l2 relaxed from -0.08 to -0.05 (labelled 'wobble allowed').",
            "lecture": "GO2_LECTURE_REWARD_REFERENCE.md 6-4: ang_vel_xy_l2 strong gives less wobble (stable), weak allows wobble (room to adapt to rough terrain); report generator: strengthening = wobble suppression up, stable.",
            "trial_history": "Stronger direction reduced rough-lateral falls in G-A038 (59->18, A033) and G-A062 Q2 (76->41, A043 rewards); weaker -0.035 (G-A064 c6) raised rough flips 7->31 and push 6->43. Against: G-A055 (-0.08 on A043) rough lateral 24->50 and 15cm >=2 stairs 77->0; G-A038 10cm >=2 stairs 43->0. Not tested in the G-A074..G-A083 line (lin_vel_z -3, flat_orientation -0.225, track_lin 2.0, track_ang 0.75).",
            "unknown": "Whether the tilt falls start from roll or pitch is not measured (steps.csv has only gravity z). The few falls (7 tilt) are within what a single seed could move by chance. Whether a roll/pitch-rate penalty changes post-push xy drift is a prediction, not an observation.",
        },
        "rewards": CANDIDATE,
        "training": {"seed": 42, "num_envs": 4096, "max_iterations": 3000, "from_scratch": True},
        "evaluation": {"checkpoint_iter": 2400, "seeds": [101, 202, 303], "case_count": 69, "baseline": "reused G-A083 PC2 stored evaluation"},
        "hypothesis": {
            "direction": "ang_vel_xy_l2 -0.05 -> -0.065 reduces tilt-type falls on G3/G6 and the post-push xy drift.",
            "competing": "The remaining tilt falls are chance-level for one seed and the G6 drift comes from the yaw/xy tracking balance set by track_ang_vel_z 0.75 (G-A082 raised it 0.049->0.081), so ang_vel_xy will not move them.",
            "mechanism": "ang_vel_xy_l2 penalizes squared base roll and pitch rates; a larger negative weight raises the cost of fast body tilting during rough footholds and push recovery.",
            "lecture_prediction": "Stronger gives less wobble and more stability; the cost is less room to adapt on rough terrain and, in our history, stair climbing.",
            "unknown": "The trade-off size on stairs in this lineage is unknown; earlier stair collapses were at -0.08 on different baselines.",
        },
        "preregistered_predictions": {
            "primary": {
                "metric": "tools/go2_weakness_breakdown.py exy_mean over the 12 G6 push rows",
                "supported_if": "<= 0.065",
                "refuted_if": ">= 0.075",
                "otherwise": "INCONCLUSIVE",
                "reference": "G-A083=0.072",
            },
            "secondary": {
                "tilt_falls_G3_G6": {
                    "metric": "sum of fall_tilt over the 6 G3 rows and 12 G6 rows (go2_weakness_breakdown)",
                    "supported_if": "<= 3",
                    "reference": "G-A083=7",
                },
                "training_base_contact": {
                    "metric": "Episode_Termination/base_contact mean over iter 2380-2420",
                    "supported_if": "<= 0.17",
                    "reference": "G-A083=0.198",
                },
            },
            "protection": {
                "stairs_full_proxy": "stairs_10_down and stairs_15_down full proxy sums each >= 85 (G-A083 96 and 95)",
                "stairs_15_survival_mean": ">= 0.92 over stairs_15_up/down x 3 seeds (G-A083 0.974)",
                "head_direction_change_median": "slope_plus_20, stairs_10_down, stairs_15_down each <= 40 degrees (G-A083 13.5/11.2/20.1)",
                "G3_survival_sum": ">= 5.75 (G-A083 5.8125)",
                "terrain_command_direction_speed_mean": ">= 0.425 m/s for G3/G4/G5 (G-A083 0.470)",
                "G2_combined_yaw": "all 6 rows survival=1.0",
                "policy_std": "Policy/mean_std mean over iter 2380-2420 <= 0.98 (G-A083 0.798)",
                "all_69_cases": "report only; not a single veto",
            },
        },
        "score_model": "Report the H1 official-fit inverse formula (G-A083 57.59) and the legacy worst-case proxy (G-A083 63.48); neither is an official Go2 score.",
        "divergence_plan": {
            "pinned_checkpoint": "iter 2400 is the evaluation checkpoint and must be retained.",
            "if_train_rc_nonzero_after_2400": "Retain the partial result and evaluate the pinned iter-2400 checkpoint; divergence alone does not reject the setting.",
            "if_diverged_before_2400": "Record DIVERGED_BEFORE_PIN; do not change seed or automatically retry.",
        },
        "result_use": {
            "supported_and_protected": "Review as a candidate instead of G-A083.",
            "supported_but_protection_lost": "Keep G-A083; name the lost axis (stairs first) and do not go stronger than -0.065.",
            "inconclusive_or_refuted": "Keep G-A083; treat the G6 drift as a yaw/xy tracking-balance question rather than an ang_vel_xy one.",
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
    # Same runtime source chain as G-A082/G-A083 (a076 adds the Isaac-Lab-first python pick;
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
            "G-A084 starts from the PC2 G-A083 realization and changes only "
            "ang_vel_xy_l2 -0.05 -> -0.065.\nThe embedded baseline contains the iter-2400 model/env, "
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
        f"G-A084 PC2 execution\nunzip -oq /workspace/{RELEASE}.zip -d /workspace\n"
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


