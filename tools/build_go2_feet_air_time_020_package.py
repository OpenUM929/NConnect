"""Build the v2 Go2 package with graceful evaluation shutdown and retries."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
BASELINE_RESULT = (
    ROOT
    / "workspace"
    / "server_returns"
    / "go2_default_vs_pilot_v1_full_260901"
    / "original"
    / "GO2_DEFAULT_VS_PILOT_RESULT.zip"
)
BASELINE_RESULT_SHA = "af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b"
BASELINE_REPORT_MEMBER = "go2_default_vs_pilot_v1/evaluation/default/SELF_EVAL_REPORT.json"
BASELINE_MODEL_SHA = "99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676"
BASELINE_ENV_SHA = "4d1d294b63dafeceb223fb48226cbe6a533157bc54f97ce486f644bd1bda262c"
RECOVERY_RESULT_ROOT = (
    ROOT
    / "workspace"
    / "server_returns"
    / "go2_feet_air_time_020_v1_partial_260901"
    / "extracted"
    / "go2_feet_air_time_020_v1"
)
RECOVERY_CANDIDATE_SHA = "0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5"
OUTPUT = GO2 / "go2_feet_air_time_020_v2.zip"
PREFIX = Path("go2_feet_air_time_020_v1")
DEFAULT_REWARDS = {
    "track_lin_vel_xy_exp": 1.0,
    "feet_air_time": 0.01,
    "lin_vel_z_l2": -3.0,
    "ang_vel_xy_l2": -0.08,
    "action_rate_l2": -0.01,
    # 260903: quadruped_rewards.py 가 flat_orientation_l2 를 활성 다이얼로 승격했다.
    # 값이 default(0.0)와 같아 이 완료 실험의 학습 조건은 변하지 않는다.
    "flat_orientation_l2": 0.0,
}
CANDIDATE_REWARDS = {**DEFAULT_REWARDS, "feet_air_time": 0.20}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reward_dict(source: str) -> dict[str, float]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "REWARD_WEIGHTS" for target in node.targets
        ):
            return {str(key): float(value) for key, value in ast.literal_eval(node.value).items()}
    raise RuntimeError("REWARD_WEIGHTS not found")


def reward_source(weights: dict[str, float]) -> bytes:
    source = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
    for name, value in weights.items():
        pattern = rf'("{re.escape(name)}"\s*:\s*)[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
        source, count = re.subn(pattern, rf"\g<1>{value}", source, count=1)
        if count != 1:
            raise RuntimeError(f"unable to freeze reward: {name}")
    if reward_dict(source) != weights:
        raise RuntimeError(f"reward mismatch: {reward_dict(source)}")
    return source.encode("utf-8")


def source_files() -> list[Path]:
    files = [
        GO2 / "train.py",
        GO2 / "play.py",
        GO2 / "pyproject.toml",
        GO2 / "go2_eval_telemetry.py",
        GO2 / "go2_policy_lineage.py",
    ]
    files.extend(sorted((GO2 / "go2_task").glob("*.py")))
    return files


def baseline_report() -> bytes:
    if not BASELINE_RESULT.is_file():
        raise RuntimeError(f"missing verified baseline result: {BASELINE_RESULT}")
    if sha(BASELINE_RESULT.read_bytes()) != BASELINE_RESULT_SHA:
        raise RuntimeError("verified baseline result ZIP SHA mismatch")
    with zipfile.ZipFile(BASELINE_RESULT) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("baseline result ZIP CRC failure")
        data = archive.read(BASELINE_REPORT_MEMBER)
    report = json.loads(data)
    identity = report.get("identity", {})
    if identity.get("model_sha256") != BASELINE_MODEL_SHA:
        raise RuntimeError("Default-01 report model SHA mismatch")
    if identity.get("env_sha256") != BASELINE_ENV_SHA:
        raise RuntimeError("Default-01 report env SHA mismatch")
    if report.get("observed_telemetry_count") != report.get("expected_telemetry_count") or report.get(
        "observed_telemetry_count"
    ) != 69:
        raise RuntimeError("Default-01 report telemetry is incomplete")
    return data


def recovery_files() -> list[Path]:
    model = RECOVERY_RESULT_ROOT / "training" / "model_best.pt"
    status = RECOVERY_RESULT_ROOT / "training" / "TRAIN_STATUS.txt"
    if not model.is_file() or sha(model.read_bytes()) != RECOVERY_CANDIDATE_SHA:
        raise RuntimeError("recovery candidate model is missing or mismatched")
    if not status.is_file() or "TRAIN_RC=0" not in status.read_text(encoding="utf-8"):
        raise RuntimeError("recovery training status is not complete")
    roots = [
        RECOVERY_RESULT_ROOT / "training",
        RECOVERY_RESULT_ROOT / "evaluation" / "candidate" / "cases",
        RECOVERY_RESULT_ROOT / "logs" / "candidate",
    ]
    files = [path for root in roots for path in root.rglob("*") if path.is_file()]
    for path in (
        RECOVERY_RESULT_ROOT / "evaluation" / "candidate" / "identity.json",
        RECOVERY_RESULT_ROOT / "logs" / "candidate_training.log",
    ):
        if path.is_file():
            files.append(path)
    return sorted(set(files))


def build_payload() -> dict[str, bytes]:
    required = source_files() + [
        GO2 / "quadruped_rewards.py",
        GO2 / "go2_fixed_eval_report.py",
        GO2 / "go2_single_variable_report.py",
        GO2 / "package_go2_result.py",
        GO2 / "server_run_go2_feet_air_time_020_v1.sh",
        GO2 / "GO2_FEET_AIR_TIME_020_V2_README.txt",
        GO2 / "config" / "go2_self_eval_registry.json",
        GO2 / "reports" / "GO2_FEET_AIR_TIME_020_SCREENING_PRD.md",
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing package input: {missing}")

    default_source = reward_source(DEFAULT_REWARDS)
    candidate_source = reward_source(CANDIDATE_REWARDS)
    payload: dict[str, bytes] = {}
    for path in source_files():
        payload[f"candidate/{path.relative_to(GO2).as_posix()}"] = path.read_bytes()
    payload["candidate/quadruped_rewards.py"] = candidate_source
    payload["default_quadruped_rewards.py"] = default_source
    payload["baseline_DEFAULT_SELF_EVAL_REPORT.json"] = baseline_report()
    payload["baseline_provenance.json"] = json.dumps(
        {
            "artifact": BASELINE_RESULT.name,
            "artifact_sha256": BASELINE_RESULT_SHA,
            "member": BASELINE_REPORT_MEMBER,
            "default_checkpoint_iter": 800,
            "default_model_sha256": BASELINE_MODEL_SHA,
            "default_env_sha256": BASELINE_ENV_SHA,
            "reuse_reason": "same frozen registry and evaluator; avoid repeating one hour of baseline training and 69 evaluation cases",
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    payload["go2_self_eval_registry.json"] = (GO2 / "config" / "go2_self_eval_registry.json").read_bytes()
    payload["GO2_FEET_AIR_TIME_020_SCREENING_PRD.md"] = (
        GO2 / "reports" / "GO2_FEET_AIR_TIME_020_SCREENING_PRD.md"
    ).read_bytes()
    for name in (
        "go2_fixed_eval_report.py",
        "go2_single_variable_report.py",
        "package_go2_result.py",
        "server_run_go2_feet_air_time_020_v1.sh",
        "GO2_FEET_AIR_TIME_020_V2_README.txt",
    ):
        payload[name] = (GO2 / name).read_bytes()
    for path in recovery_files():
        relative = path.relative_to(RECOVERY_RESULT_ROOT).as_posix()
        payload[f"recovery_seed/{relative}"] = path.read_bytes()
    manifest = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = manifest.encode("utf-8")
    return payload


def build() -> None:
    payload = build_payload()
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            member = (PREFIX / name).as_posix()
            info = zipfile.ZipInfo(member, date_time=(2026, 9, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        if len(archive.namelist()) != len(payload):
            raise RuntimeError("ZIP member count mismatch")
        if any(Path(name).is_absolute() or ".." in Path(name).parts for name in archive.namelist()):
            raise RuntimeError("unsafe ZIP member")
    digest = sha(OUTPUT.read_bytes())
    OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="utf-8"
    )
    print(f"package={OUTPUT}")
    print(f"sha256={digest}")
    print(f"members={len(payload)}")


if __name__ == "__main__":
    build()
