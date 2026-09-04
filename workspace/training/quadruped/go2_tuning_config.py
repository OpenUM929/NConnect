"""Validate a Go2 tuning experiment and materialize immutable engine inputs."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import shlex
import shutil
from pathlib import Path
from typing import Any


ENGINE_VERSION = "1.2.0"
DEFAULT_BASELINE_MODEL_SHA = "99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676"
DEFAULT_BASELINE_ENV_SHA = "4d1d294b63dafeceb223fb48226cbe6a533157bc54f97ce486f644bd1bda262c"
PILOT_BASELINE_MODEL_SHA = "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d"
PILOT_BASELINE_ENV_SHA = "f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d"
REWARD_NAMES = (
    "track_lin_vel_xy_exp",
    "feet_air_time",
    "lin_vel_z_l2",
    "ang_vel_xy_l2",
    "action_rate_l2",
    "flat_orientation_l2",
)
DEFAULT_REWARDS = {
    "track_lin_vel_xy_exp": 1.0,
    "feet_air_time": 0.01,
    "lin_vel_z_l2": -3.0,
    "ang_vel_xy_l2": -0.08,
    "action_rate_l2": -0.01,
    "flat_orientation_l2": 0.0,
}
# Frozen baselines a candidate may be screened against. Engine 1.1.0 hard-coded
# Default-01; Pilot-01 was added in 1.2.0 because the 69-case posture_gate_v2
# measurement puts Pilot-01 at 33.79311/70 against Default-01's 17.90697/70, so
# screening against Default-01 optimises a policy we would never submit.
FROZEN_BASELINES = {
    "Default-01": {
        "slug": "default",
        "checkpoint_iter": 800,
        "model_sha256": DEFAULT_BASELINE_MODEL_SHA,
        "env_sha256": DEFAULT_BASELINE_ENV_SHA,
        "rewards": {
            "track_lin_vel_xy_exp": 1.0,
            "feet_air_time": 0.01,
            "lin_vel_z_l2": -3.0,
            "ang_vel_xy_l2": -0.08,
            "action_rate_l2": -0.01,
            "flat_orientation_l2": 0.0,
        },
    },
    "Pilot-01": {
        "slug": "pilot",
        "checkpoint_iter": 1000,
        "model_sha256": PILOT_BASELINE_MODEL_SHA,
        "env_sha256": PILOT_BASELINE_ENV_SHA,
        "rewards": {
            "track_lin_vel_xy_exp": 1.2,
            "feet_air_time": 0.2,
            "lin_vel_z_l2": -2.0,
            "ang_vel_xy_l2": -0.05,
            "action_rate_l2": -0.01,
            "flat_orientation_l2": 0.0,
        },
    },
}
CANONICAL_CASES = {
    "G1": "forward_fast",
    "G2": "diagonal_left",
    "G3": "rough_forward",
    "G4": "slope_plus_20",
    "G5": "stairs_15_up",
    "G6": "push_pos_x",
    "G7": "dr_seed_{seed}",
}
SOURCE_FILES = (
    "train.py",
    "play.py",
    "pyproject.toml",
    "go2_eval_telemetry.py",
    "go2_policy_lineage.py",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def reward_dict(source: str) -> dict[str, float]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "REWARD_WEIGHTS"
            for target in node.targets
        ):
            return {
                str(key): float(value)
                for key, value in ast.literal_eval(node.value).items()
            }
    raise ValueError("REWARD_WEIGHTS not found")


def render_reward_source(template: str, weights: dict[str, float]) -> str:
    if tuple(weights) != REWARD_NAMES:
        raise ValueError(f"reward keys/order must be {REWARD_NAMES}")
    rendered = template
    for name, value in weights.items():
        pattern = rf'("{re.escape(name)}"\s*:\s*)[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
        rendered, count = re.subn(pattern, rf"\g<1>{value}", rendered, count=1)
        if count != 1:
            raise ValueError(f"unable to render reward: {name}")
    if reward_dict(rendered) != weights:
        raise ValueError(f"rendered rewards differ: {reward_dict(rendered)}")
    return rendered


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_experiment(experiment: dict[str, Any]) -> dict[str, Any]:
    _require(experiment.get("schema_version") == "1.0", "schema_version must be 1.0")
    _require(experiment.get("engine_version") == ENGINE_VERSION, "engine_version mismatch")
    for field in ("work_id", "run_id", "experiment_slug"):
        _require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,79}", str(experiment.get(field, "")))), f"invalid {field}")

    baseline = experiment.get("baseline", {})
    _require(baseline.get("name") in FROZEN_BASELINES, f"baseline must be one of {sorted(FROZEN_BASELINES)}")
    frozen = FROZEN_BASELINES[baseline["name"]]
    _require(baseline.get("checkpoint_iter") == frozen["checkpoint_iter"], "baseline checkpoint iteration mismatch")
    _require(baseline.get("model_sha256") == frozen["model_sha256"], "baseline model SHA mismatch")
    _require(baseline.get("env_sha256") == frozen["env_sha256"], "baseline env SHA mismatch")

    rewards = experiment.get("rewards", {})
    base_rewards = rewards.get("baseline", {})
    candidate_rewards = rewards.get("candidate", {})
    _require(tuple(base_rewards) == REWARD_NAMES, f"baseline reward keys/order must be {REWARD_NAMES}")
    _require(tuple(candidate_rewards) == REWARD_NAMES, f"candidate reward keys/order must be {REWARD_NAMES}")
    _require(all(isinstance(value, (int, float)) for value in base_rewards.values()), "baseline reward values must be numeric")
    _require(all(isinstance(value, (int, float)) for value in candidate_rewards.values()), "candidate reward values must be numeric")
    _require(base_rewards == frozen["rewards"], f"baseline rewards must match frozen {baseline['name']}")
    changed = [name for name in REWARD_NAMES if float(base_rewards[name]) != float(candidate_rewards[name])]
    _require(len(changed) == 1, "candidate must change exactly one reward")
    single = experiment.get("single_change", {})
    _require(single.get("name") == changed[0], "single_change name mismatch")
    _require(float(single.get("from")) == float(base_rewards[changed[0]]), "single_change from mismatch")
    _require(float(single.get("to")) == float(candidate_rewards[changed[0]]), "single_change to mismatch")

    training = experiment.get("training", {})
    _require(training.get("from_scratch") is True, "training must be from_scratch")
    _require(isinstance(training.get("seed"), int) and training["seed"] >= 0, "invalid training seed")
    _require(isinstance(training.get("num_envs"), int) and 1 <= training["num_envs"] <= 4096, "invalid num_envs")
    _require(isinstance(training.get("max_iterations"), int) and 1 <= training["max_iterations"] <= 5000, "invalid max_iterations")

    evaluation = experiment.get("evaluation", {})
    _require(evaluation.get("tier1_seed") == 101, "tier1_seed must be 101")
    _require(evaluation.get("representative_seeds") == [101, 202, 303], "representative seeds mismatch")
    _require(evaluation.get("cases") == CANONICAL_CASES, "canonical 7-case mapping mismatch")
    for key in ("steps", "case_attempts", "case_retry_delay_seconds"):
        _require(isinstance(evaluation.get(key), int) and evaluation[key] > 0, f"invalid evaluation {key}")
    gates = evaluation.get("gates", {})
    # target_scenario is optional and informational since engine 1.2.0; the tier-1
    # promotion gate is the weighted total (min_total_points_delta) plus the
    # per-scenario survival guard.
    if "target_scenario" in gates:
        _require(gates.get("target_scenario") in CANONICAL_CASES, "target scenario must be one of G1..G7")
        _require(isinstance(gates.get("target_min_proxy_delta"), (int, float)), "invalid gate target_min_proxy_delta")
    for key in (
        "min_total_points_delta",
        "max_survival_regression",
        "minimum_points_70",
        "required_survival_proxy",
        "required_tracking_proxy",
    ):
        _require(isinstance(gates.get(key), (int, float)), f"invalid gate {key}")
    _require(float(gates["min_total_points_delta"]) > 0.0, "min_total_points_delta must be positive")

    video = experiment.get("video", {})
    _require(video.get("required") is True, "video must be required")
    _require(video.get("scenario") == "G1" and video.get("case") == "forward_fast", "video target mismatch")
    _require(video.get("seed") == 101 and video.get("num_envs") == 4, "video seed/env mismatch")
    _require(isinstance(video.get("steps"), int) and video["steps"] > 0, "invalid video steps")

    output = experiment.get("output", {})
    _require(bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,79}", str(output.get("keep_dir_name", "")))), "invalid keep_dir_name")
    _require(bool(re.fullmatch(r"[A-Z0-9][A-Z0-9_]{2,79}_RESULT\.zip", str(output.get("result_zip", "")))), "invalid result_zip")
    _require(str(output.get("done_marker", "")).startswith("[DONE] "), "invalid done_marker")
    _require(bool(re.fullmatch(r"\[DONE\] [A-Z0-9_]{3,100}", str(output.get("done_marker", "")))), "invalid done_marker")
    _require(bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", str(output.get("tmux_name", "")))), "invalid tmux_name")
    return experiment


def load_and_validate(path: Path) -> dict[str, Any]:
    return validate_experiment(json.loads(path.read_text(encoding="utf-8")))


def registry_payload(base_registry: Path, seeds: list[int], experiment: dict[str, Any]) -> dict[str, Any]:
    registry = copy.deepcopy(json.loads(base_registry.read_text(encoding="utf-8")))
    registry["schema_version"] = "1.2.0"
    registry["status"] = "INTERNAL_PROXY_SPEC_REPAIRED_V2_TUNING_ENGINE"
    registry["score"]["internal_gates"]["required_evaluation_seeds"] = seeds
    registry["experiment_identity"] = {
        "work_id": experiment["work_id"],
        "run_id": experiment["run_id"],
        "experiment_sha256": experiment["_sha256"],
        "official_equivalence": False,
    }
    cases = experiment["evaluation"]["cases"]
    for scenario in registry["scenarios"]:
        case = cases[scenario["id"]]
        scenario["internal_cases"] = [
            case.format(seed=seed) for seed in seeds
        ] if scenario["id"] == "G7" else [case]
    return registry


def _copy_source(source_root: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name in SOURCE_FILES:
        shutil.copy2(source_root / name, target / name)
    shutil.copytree(source_root / "go2_task", target / "go2_task", dirs_exist_ok=True)


def materialize_runtime(
    *,
    engine_root: Path,
    experiment_path: Path,
    runtime_root: Path,
    source_root: Path | None = None,
    baseline_root: Path | None = None,
) -> dict[str, Any]:
    experiment = load_and_validate(experiment_path)
    experiment = copy.deepcopy(experiment)
    experiment["_sha256"] = sha256_file(experiment_path)
    source_root = source_root or engine_root / "source_template"
    baseline_root = baseline_root or engine_root / "baseline"
    if runtime_root.exists():
        shutil.rmtree(runtime_root)
    candidate = runtime_root / "candidate"
    default = runtime_root / "default"
    meta = runtime_root / "meta"
    _copy_source(source_root, candidate)
    _copy_source(source_root, default)
    template = (source_root / "quadruped_rewards.py").read_text(encoding="utf-8")
    (candidate / "quadruped_rewards.py").write_text(
        render_reward_source(template, experiment["rewards"]["candidate"]), encoding="utf-8", newline="\n"
    )
    (default / "quadruped_rewards.py").write_text(
        render_reward_source(template, experiment["rewards"]["baseline"]), encoding="utf-8", newline="\n"
    )
    frozen = FROZEN_BASELINES[experiment["baseline"]["name"]]
    slug = frozen["slug"]
    baseline_model = baseline_root / slug / "model_best.pt"
    baseline_env = baseline_root / slug / "env.yaml"
    if sha256_file(baseline_model) != frozen["model_sha256"]:
        raise ValueError("embedded baseline model SHA mismatch")
    if sha256_file(baseline_env) != frozen["env_sha256"]:
        raise ValueError("embedded baseline env SHA mismatch")
    shutil.copy2(baseline_model, default / "model_best.pt")
    shutil.copy2(baseline_env, default / "env.yaml")
    shutil.copytree(baseline_root / slug / "baseline_seed", runtime_root / "baseline_seed")
    meta.mkdir(parents=True, exist_ok=True)
    shutil.copy2(experiment_path, meta / "experiment.json")
    (meta / "experiment.sha256").write_text(
        f'{experiment["_sha256"]}  experiment.json\n', encoding="utf-8", newline="\n"
    )
    base_registry = engine_root / "config" / "go2_self_eval_registry.json"
    (runtime_root / "tier1_registry.json").write_text(
        json.dumps(registry_payload(base_registry, [101], experiment), indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8", newline="\n",
    )
    (runtime_root / "representative_registry.json").write_text(
        json.dumps(registry_payload(base_registry, [101, 202, 303], experiment), indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8", newline="\n",
    )
    return experiment


def shell_environment(experiment_path: Path) -> str:
    experiment = load_and_validate(experiment_path)
    training = experiment["training"]
    evaluation = experiment["evaluation"]
    video = experiment["video"]
    output = experiment["output"]
    single = experiment["single_change"]
    values = {
        "ENGINE_VERSION": ENGINE_VERSION,
        "WORK_ID": experiment["work_id"],
        "RUN_ID": experiment["run_id"],
        "EXPERIMENT_SLUG": experiment["experiment_slug"],
        "EXPERIMENT_SHA256": sha256_file(experiment_path),
        "TRAIN_SEED": training["seed"],
        "NUM_ENVS": training["num_envs"],
        "MAX_ITERATIONS": training["max_iterations"],
        "SINGLE_CHANGE_NAME": single["name"],
        "SINGLE_CHANGE_FROM": single["from"],
        "SINGLE_CHANGE_TO": single["to"],
        "EVAL_STEPS": evaluation["steps"],
        "CASE_ATTEMPTS": evaluation["case_attempts"],
        "CASE_RETRY_DELAY": evaluation["case_retry_delay_seconds"],
        "VIDEO_STEPS": video["steps"],
        "VIDEO_SEED": video["seed"],
        "VIDEO_NUM_ENVS": video["num_envs"],
        "KEEP_DIR_NAME": output["keep_dir_name"],
        "RESULT_ZIP_NAME": output["result_zip"],
        "DONE_MARKER": output["done_marker"],
        "TMUX_NAME": output["tmux_name"],
    }
    return "".join(f"{key}={shlex.quote(str(value))}\n" for key, value in values.items())


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--experiment", required=True, type=Path)
    shell = sub.add_parser("shell-env")
    shell.add_argument("--experiment", required=True, type=Path)
    shell.add_argument("--out", type=Path)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--engine-root", required=True, type=Path)
    materialize.add_argument("--experiment", required=True, type=Path)
    materialize.add_argument("--runtime-root", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        experiment = load_and_validate(args.experiment)
        print(json.dumps({"status": "VALID", "work_id": experiment["work_id"], "sha256": sha256_file(args.experiment)}, sort_keys=True))
    elif args.command == "shell-env":
        payload = shell_environment(args.experiment)
        if args.out is None:
            print(payload, end="")
        else:
            args.out.write_text(payload, encoding="utf-8", newline="\n")
    else:
        experiment = materialize_runtime(engine_root=args.engine_root, experiment_path=args.experiment, runtime_root=args.runtime_root)
        print(json.dumps({"status": "MATERIALIZED", "work_id": experiment["work_id"], "runtime_root": str(args.runtime_root)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
