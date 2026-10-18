#!/usr/bin/env python3
"""Build G-A092: feet_air_time 0.01 -> 0.05 alone on the verified PC2 G-A083 policy (PC2, 3000 iter).

Next lever after the track_ang 0.1-step points (G-A090 worse, G-A091 diverged at iter 2594 without evaluation); user decision 2026-10-18.  Baseline, runtime chain and
stored-evaluation reuse are the G-A086 ones (tools/build_go2_g_a086_package.py).
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

WORK_ID = "G-A092"
SLUG = "go2_g_a092_feet_air_p0p05"
PREFIX = SLUG + "/"
RELEASE = "GO2_G_A092_FEET_AIR_P0P05_v1"
RESULT_ZIP = "GO2_G_A092_FEET_AIR_P0P05_RESULT.zip"
KEY = "feet_air_p0p05"
FIXED_TIME = (2026, 10, 16, 0, 0, 0)
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
CANDIDATE = {**a083.CANDIDATE, "feet_air_time": 0.05}
CHANGES = {"feet_air_time": (0.01, 0.05)}

IDENTITY_GREP_LINES = a083.IDENTITY_GREP_LINES.replace("G-A083 stored G-A082 baseline", "G-A092 stored G-A083 baseline")


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
        "RUN_ID": "train_G-A092-Go2_feet_air_p0p05_3000",
        "EXPERIMENT_SLUG": SLUG,
        "KEEP_DIR_NAME": SLUG,
        "RESULT_ZIP_NAME": RESULT_ZIP,
        "DONE_MARKER": f"'[DONE] {RESULT_ZIP[:-4]}_READY'",
        "TMUX_NAME": SLUG,
        "TRAIN_SEED": "42",
        "NUM_ENVS": "4096",
        "MAX_ITERATIONS": "3000",
        # Label only (the env-rewards check reads expected_rewards.json).
        "SINGLE_CHANGE_NAME": "feet_air_time",
        "SINGLE_CHANGE_FROM": "0.01",
        "SINGLE_CHANGE_TO": "0.05",
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
        ("G-A083: fail before training", "G-A092: fail before training"),
        ("G-A083 evaluator/registry differs from the verified PC2 G-A082 baseline",
         "G-A092 evaluator/registry differs from the verified PC2 G-A083 baseline"),
        ("G-A083 stored PC2 G-A082", "G-A092 stored PC2 G-A083"),
        ("G-A083 matched PC2 G-A082 report", "G-A092 matched PC2 G-A083 report"),
        ("materialized PC2 G-A082 baseline", "materialized PC2 G-A083 baseline"),
        ("reuse identity-pinned PC2 G-A082 baseline", "reuse identity-pinned PC2 G-A083 baseline"),
        ("REUSED_G_A082_PC2_FULL_NO_RERUN", "REUSED_G_A083_PC2_FULL_NO_RERUN"),
        ("G-A083 reuses the ten identity-pinned PC2 G-A082 videos",
         "G-A092 reuses the ten identity-pinned PC2 G-A083 videos"),
        ("[FAIL] G-A083 stored G-A082 baseline identity mismatch",
         "[FAIL] G-A092 stored G-A083 baseline identity mismatch"),
    ):
        text = text.replace(old, new)
    return text.encode("utf-8")


def experiment() -> dict:
    return {
        "schema": "go2_g_a092_single_change_v1",
        "work_id": WORK_ID,
        "device": "PC2",
        "run_key": KEY,
        "purpose": "feet_air_time 0.01 -> 0.05 alone on G-A083 rewards. G-A091 (track_ang 0.65) gave no score (diverged, no evaluation), so the base stays G-A083 (user decision 2026-10-18).",
        "promotion": "exploratory_single_seed_no_automatic_followup",
        "user_decision": "2026-10-18: if G-A091 is good apply its rewards with the recommended change, otherwise apply the recommended change (feet_air_time 0.01 -> 0.05) to the existing rewards; then build G-A092.",
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
        "changes": {
            "feet_air_time": {
                "from": 0.01, "to": 0.05,
                "value_design": "0.05 is untested on any line. It stays well below 0.1-0.5 where the A048 line traded stairs/push for rough lateral (G-A063 s06-s08) and below 0.35 which collapsed body height on Pilot-01 (G-A015).",
            },
        },
        "evidence_basis": {
            "observation": "G-A083 loss: survival 0.82, tracking 11.59 (xy 6.92, yaw 4.67). Largest cases rough_lateral 1.52, rough_forward 1.42, slope +-20 0.9/0.84, stairs 15 about 0.6 each. Mean speeds match commands, so xy loss is fluctuation/drift on terrain. Posture-gate falls 26 low-type (mostly stairs_15 climb) / 10 tilt.",
            "push": "A048 line (feet 0.2 base): 0.35 rough lateral falls 41 -> 16 but push falls 0 -> 6 and 15cm >=1 step 52 -> 32; 0.5 push falls 0 -> 37, 15cm 52 -> 1; 0.01 15cm 52 -> 8 (G-A063 s05-s08). G-A091 note: track_ang 0.65 diverged (non-finite std) at iter 2594.",
            "lecture": "Lecture: feet_air_time up = higher foot lift, better for climbing and rough terrain; down = dragging feet, weak climbing (reports/GO2_LECTURE_REWARD_REFERENCE.md).",
            "against": "On the A048 line every increase raised push falls and lowered 15cm stair progress; foot height was never measured, so the lecture effect is unconfirmed. Body lowering at 0.35 (G-A015) matches the stair failure path.",
            "noise": 'Realization noise reference: G-A077 PC2 vs server, identical rewards, formula 55.29 vs 55.94 (0.65) and fallen robots 15 vs 6. A formula difference below 0.65 is INCONCLUSIVE; fall counts alone are not decisive.',
        },
        "rewards": CANDIDATE,
        "training": {"seed": 42, "num_envs": 4096, "max_iterations": 3000, "from_scratch": True},
        "evaluation": {"checkpoint_iter": 2400, "seeds": [101, 202, 303], "case_count": 69, "baseline": "reused G-A083 PC2 stored evaluation"},
        "hypothesis": {
            "direction": "A small foot-lift incentive reduces toe stubbing and drift on rough/stairs, lowering xy loss and low-type stair falls, so the score is >= G-A083.",
            "competing": "Longer swing phases cost support after push and on stairs (A048-line side effects) so push falls rise and 15cm stair survival drops, and the score falls below G-A083.",
        },
        "preregistered_predictions": {
            "primary": {
                "metric": "tools/go2_weakness_breakdown.py formula score /70 (plan section 5 target 58.0) and legacy proxy; xy part of the tracking loss (G-A083 6.92)",
                "candidate_review_if": ">= 58.0, protection held, xy error and terrain speed not worse than G-A083",
                "improvement_signal_if": "57.59 < formula < 58.0 with direction metrics on the same side",
                "worse_if": "< 57.59 (record the size)",
            },
            "secondary": {
                "push_falls": {"metric": "fallen_envs summed over the 12 G6 rows", "reference": "G-A083=4, G-A082 (0.75 on action_rate -0.005)=0"},
                "total_falls": {"metric": "fallen_envs summed over 69 rows", "reference": "G-A083=12, G-A086=16"},
                "stairs_15_climb_falls": {"metric": "fallen_envs summed over the 3 stairs_15_down rows", "reference": "G-A083=2, G-A086=6"},
                "low_type_robots": {"metric": "posture-gate robots with height_rel < 0.18 at the first non-upright step (tools/go2_g_a086_fall_cause.py)", "reference": "G-A083=26, G-A086=63"},
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
            "candidate_review": "Review against G-A083 as a candidate.",
            "worse": "Record the size; no automatic next value. Falsifiers: score < 57.59, push falls above G-A083 4, 15cm stair survival < 0.92.",
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
            "G-A092 starts from the PC2 G-A083 realization and changes one reward: feet_air_time 0.01 -> 0.05.\n"
            "The embedded baseline contains the iter-2400 model/env, "
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
        f"G-A092 PC2 execution\nunzip -oq /workspace/{RELEASE}.zip -d /workspace\n"
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


