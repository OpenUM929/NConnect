"""Build the one-upload Go2 Default-01 vs Pilot-01 server package."""

from __future__ import annotations

import ast
import hashlib
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
OUTPUT = GO2 / "go2_default_vs_pilot_v1.zip"
PREFIX = Path("go2_default_vs_pilot_v1")
PILOT_MODEL_SHA = "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d"
DEFAULT_REWARDS = {
    "track_lin_vel_xy_exp": 1.0,
    "feet_air_time": 0.01,
    "lin_vel_z_l2": -3.0,
    "ang_vel_xy_l2": -0.08,
    "action_rate_l2": -0.01,
    # 260903: quadruped_rewards.py 가 flat_orientation_l2 를 활성 다이얼로 승격했다.
    # 이 완료된 package 의 default 값(=0.0, IsaacLab Go2 rough 기본)과 동일하므로
    # 산출물의 학습 조건은 변하지 않는다. 키를 추가하지 않으면 렌더 검증이 실패한다.
    "flat_orientation_l2": 0.0,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reward_dict(source: str) -> dict[str, float]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "REWARD_WEIGHTS" for target in node.targets):
            return {str(key): float(value) for key, value in ast.literal_eval(node.value).items()}
    raise RuntimeError("REWARD_WEIGHTS not found")


def default_reward_source() -> bytes:
    source = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
    replacements = {
        "track_lin_vel_xy_exp": "1.0",
        "feet_air_time": "0.01",
        "lin_vel_z_l2": "-3.0",
        "ang_vel_xy_l2": "-0.08",
        "action_rate_l2": "-0.01",
    }
    for name, value in replacements.items():
        pattern = rf'("{re.escape(name)}"\s*:\s*)[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
        source, count = re.subn(pattern, rf"\g<1>{value}", source, count=1)
        if count != 1:
            raise RuntimeError(f"unable to freeze default reward: {name}")
    if reward_dict(source) != DEFAULT_REWARDS:
        raise RuntimeError(f"default reward mismatch: {reward_dict(source)}")
    return source.encode("utf-8")


def source_files() -> list[Path]:
    files = [GO2 / "train.py", GO2 / "play.py", GO2 / "pyproject.toml", GO2 / "go2_eval_telemetry.py", GO2 / "go2_policy_lineage.py"]
    files.extend(sorted((GO2 / "go2_task").glob("*.py")))
    return files


def build_payload() -> dict[str, bytes]:
    required = source_files() + [
        GO2 / "quadruped_rewards.py",
        GO2 / "go2_fixed_eval_report.py",
        GO2 / "package_go2_result.py",
        GO2 / "server_run_go2_default_vs_pilot_v1.sh",
        GO2 / "GO2_DEFAULT_VS_PILOT_README.txt",
        GO2 / "config" / "go2_self_eval_registry.json",
        GO2 / "exported" / "model_best.pt",
        GO2 / "exported" / "env.yaml",
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing package input: {missing}")
    model = GO2 / "exported" / "model_best.pt"
    if sha(model.read_bytes()) != PILOT_MODEL_SHA:
        raise RuntimeError("Pilot-01 model SHA mismatch")

    payload: dict[str, bytes] = {}
    for label in ("default", "pilot"):
        for path in source_files():
            rel = path.relative_to(GO2).as_posix()
            payload[f"{label}/{rel}"] = path.read_bytes()
    payload["default/quadruped_rewards.py"] = default_reward_source()
    payload["pilot/quadruped_rewards.py"] = (GO2 / "quadruped_rewards.py").read_bytes()
    payload["pilot/exported/model_best.pt"] = model.read_bytes()
    payload["pilot/exported/env.yaml"] = (GO2 / "exported" / "env.yaml").read_bytes()
    payload["go2_self_eval_registry.json"] = (GO2 / "config" / "go2_self_eval_registry.json").read_bytes()
    for name in (
        "go2_fixed_eval_report.py", "package_go2_result.py",
        "server_run_go2_default_vs_pilot_v1.sh", "GO2_DEFAULT_VS_PILOT_README.txt",
    ):
        payload[name] = (GO2 / name).read_bytes()
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
    (OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")).write_text(f"{digest}  {OUTPUT.name}\n", encoding="utf-8")
    print(f"package={OUTPUT}")
    print(f"sha256={digest}")
    print(f"members={len(payload)}")


if __name__ == "__main__":
    build()

