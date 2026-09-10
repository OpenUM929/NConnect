"""Build deterministic reusable Go2 tuning engine v1 without an experiment spec."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
OUTPUT = GO2 / "go2_tuning_engine_v1_4.zip"
PREFIX = Path("go2_tuning_engine_v1_4")
FIXED_TIMESTAMP = (2026, 9, 4, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_old_builder():
    path = ROOT / "tools" / "build_go2_track_lin_vel_120_package.py"
    spec = importlib.util.spec_from_file_location("go2_g_a009_builder_for_baseline", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# Pilot-01, verified in G-A012 at 33.79311/70 over the 69-case posture_gate_v2
# suite. Engine 1.2.0 ships it alongside Default-01 so an experiment can screen a
# single variable against the better of the two frozen policies.
# 260905: 원본 `GO2_PILOT_V2_BASELINE_RESULT.zip`이 로컬에 없다(G-F94 계열과 같은
# 종류의 기존 결손). 이미 검증된 압축 해제본을 대신 읽는다 — model SHA는
# byte-identical(`c4d78adf…`)로 일치했고, env.yaml은 바이트 해시만 다르며(재직렬화)
# 6개 reward 가중치(1.2/0.2/-2.0/-0.05/-0.01/0.0)가 Pilot-01 정의와 정확히 일치함을
# 직접 확인했다(GO2_PROJECT_STATE.md G-F143 계열, tools/build_go2_track_lin_vel_120_package.py의
# 같은 처리와 동일 근거).
PILOT_RESULT_DIR = ROOT / "workspace" / "_keep" / "go2_pilot_v2_baseline"
PILOT_PREFIX = "go2_pilot_v2_baseline"
PILOT_MODEL_SHA = "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d"
# 260908: all three frozen baselines pinned an env.yaml hash that matches no file
# on disk, so every engine package build died on an identity mismatch. In each
# case the model SHA matches byte for byte and only env.yaml was re-serialized;
# the six reward weights in this file were verified against Pilot-01's row in
# go2_tuning_config.FROZEN_BASELINES before repinning.
PILOT_ENV_SHA = "f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d"
TIER1_CASES = {
    "G1": "forward_fast",
    "G2": "diagonal_left",
    "G3": "rough_forward",
    "G4": "slope_plus_20",
    "G5": "stairs_15_up",
    "G6": "push_pos_x",
    "G7": "dr_seed_101",
}


def _default_baseline_payload() -> dict[str, bytes]:
    old = _load_old_builder()
    return old.baseline_payload()


def _pilot_baseline_payload() -> dict[str, bytes]:
    model = (PILOT_RESULT_DIR / "policy" / "pilot_model_best.pt").read_bytes()
    env_yaml = (PILOT_RESULT_DIR / "policy" / "pilot_env.yaml").read_bytes()
    if sha(model) != PILOT_MODEL_SHA or sha(env_yaml) != PILOT_ENV_SHA:
        raise RuntimeError("Pilot-01 model/env identity mismatch")
    payload: dict[str, bytes] = {"model_best.pt": model, "env.yaml": env_yaml}
    for case_id in TIER1_CASES.values():
        base = PILOT_RESULT_DIR / "evaluation" / "pilot_v2" / "cases" / "seed_101" / case_id
        prefix = f"baseline_seed/cases/seed_101/{case_id}"
        payload[f"{prefix}/summary.json"] = (base / "summary.json").read_bytes()
        payload[f"{prefix}/STATUS.txt"] = b"EVAL_RC=0\nSOURCE=VERIFIED_G_A012\n"
    return payload


# Chain-01: Default-01 + track_lin_vel_xy_exp 1.0->1.2 (G-A011), verified
# +3.0902846/70 over Default-01 with zero survival regression. Read from the
# locally-verified extracted result directory (the original result ZIP was
# already unpacked and removed) rather than a ZIP, unlike the Pilot-01 loader.
CHAIN01_RESULT_DIR = ROOT / "workspace" / "_keep" / "go2_track_lin_vel_120_v1"
CHAIN01_MODEL_SHA = "143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4"
# 260908: repinned to the on-disk artifact, same reason as PILOT_ENV_SHA above.
# Chain-01's env.yaml carries track_lin_vel_xy_exp 1.2 with the other five weights
# at Default values, matching its FROZEN_BASELINES row.
CHAIN01_ENV_SHA = "903d437e47aaf7c73c9e0a2f1a1835d1fe1432e66a0a2576282d02cc3cd7c2f2"


def _chain01_baseline_payload() -> dict[str, bytes]:
    model = (CHAIN01_RESULT_DIR / "training" / "model_best.pt").read_bytes()
    env_yaml = (CHAIN01_RESULT_DIR / "training" / "env.yaml").read_bytes()
    if sha(model) != CHAIN01_MODEL_SHA or sha(env_yaml) != CHAIN01_ENV_SHA:
        raise RuntimeError("Chain-01 model/env identity mismatch")
    payload: dict[str, bytes] = {"model_best.pt": model, "env.yaml": env_yaml}
    for case_id in TIER1_CASES.values():
        summary = (
            CHAIN01_RESULT_DIR
            / "evaluation" / "candidate" / "cases" / "seed_101" / case_id / "summary.json"
        ).read_bytes()
        prefix = f"baseline_seed/cases/seed_101/{case_id}"
        payload[f"{prefix}/summary.json"] = summary
        payload[f"{prefix}/STATUS.txt"] = b"EVAL_RC=0\nSOURCE=VERIFIED_G_A011\n"
    return payload


def baseline_payload() -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    for name, data in _default_baseline_payload().items():
        # 1.1.0 laid the Default-01 cache out flat; 1.2.0 nests it per baseline.
        if name.startswith("default/"):
            payload[f"baseline/{name}"] = data
        else:
            payload[f"baseline/default/{name}"] = data
    for name, data in _pilot_baseline_payload().items():
        payload[f"baseline/pilot/{name}"] = data
    for name, data in _chain01_baseline_payload().items():
        payload[f"baseline/chain01/{name}"] = data
    return payload


def baseline_fixture_root() -> Path:
    root = Path(tempfile.gettempdir()) / "nconnect_go2_tuning_engine_baseline_fixture"
    if root.exists():
        shutil.rmtree(root)
    for name, data in baseline_payload().items():
        path = root / Path(name).relative_to("baseline")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def source_files() -> list[Path]:
    files = [
        GO2 / "train.py",
        GO2 / "play.py",
        GO2 / "pyproject.toml",
        GO2 / "quadruped_rewards.py",
        GO2 / "go2_eval_telemetry.py",
        GO2 / "go2_policy_lineage.py",
    ]
    files.extend(sorted((GO2 / "go2_task").glob("*.py")))
    return files


def build_payload() -> dict[str, bytes]:
    fixed = [
        GO2 / "go2_tuning_config.py",
        GO2 / "go2_tuning_eval_report.py",
        GO2 / "go2_fixed_eval_report.py",
        GO2 / "package_go2_result.py",
        GO2 / "server_run_go2_tuning_engine_v1.sh",
        GO2 / "GO2_TUNING_ENGINE_V1_README.txt",
        GO2 / "config" / "go2_tuning_experiment_schema.json",
        GO2 / "config" / "go2_self_eval_registry.json",
    ]
    required = fixed + source_files()
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing engine input: {missing}")
    payload = baseline_payload()
    for path in source_files():
        payload[f"source_template/{path.relative_to(GO2).as_posix()}"] = path.read_bytes()
    for path in fixed:
        if path.parent.name == "config":
            name = f"config/{path.name}"
        else:
            name = path.name
        payload[name] = path.read_bytes()
    payload["ENGINE_METADATA.json"] = json.dumps(
        {
            "engine_version": "1.3.0",
            "experiment_embedded": False,
            "baselines": {
                "Default-01 iter 800": "99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676",
                "Pilot-01 iter 1000": PILOT_MODEL_SHA,
                "Chain-01 iter 1000": CHAIN01_MODEL_SHA,
            },
            "official_equivalence": False,
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    manifest = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = manifest.encode("utf-8")
    return payload


def build() -> None:
    payload = build_payload()
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo((PREFIX / name).as_posix(), date_time=FIXED_TIMESTAMP)
            info.create_system = 3
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("engine ZIP CRC failure")
        if len(archive.namelist()) != len(payload):
            raise RuntimeError("engine ZIP member count mismatch")
        if any(Path(name).is_absolute() or ".." in Path(name).parts for name in archive.namelist()):
            raise RuntimeError("unsafe engine ZIP member")
        if any(f"{PREFIX.as_posix()}/config/experiments/" in name for name in archive.namelist()):
            raise RuntimeError("experiment spec must not be embedded in fixed engine")
    digest = sha(OUTPUT.read_bytes())
    OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="utf-8", newline="\n"
    )
    print(f"engine={OUTPUT}")
    print(f"sha256={digest}")
    print(f"members={len(payload)}")


if __name__ == "__main__":
    build()
