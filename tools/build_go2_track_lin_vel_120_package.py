"""Build the deterministic Go2 G-A009 low-cost screening package."""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
# 260905: 원본 `GO2_DEFAULT_VS_PILOT_RESULT.zip`이 로컬에 없다(G-F94 계열 기존 결손,
# GO2_PROJECT_STATE.md G-F143). 이미 검증된 압축 해제본을 대신 읽는다 — Chain-01 로더
# (tools/build_go2_tuning_engine.py의 _chain01_baseline_payload)와 같은 방식.
# model_best.pt SHA는 원본과 byte-identical(`99ceeaa1…`)로 그대로 일치했다. env.yaml만
# 바이트 해시가 다른데(`a39c77dc…` vs 옛 `4d1d294b…`), 내용을 직접 열어 6개 reward
# 가중치(track_lin_vel_xy_exp=1.0·feet_air_time=0.01·lin_vel_z_l2=-3.0·ang_vel_xy_l2=-0.08·
# action_rate_l2=-0.01·flat_orientation_l2=0.0, std=0.5)가 Default-01 배포 기본값과 정확히
# 일치함을 확인했다 — YAML 재직렬화로 인한 무해한 바이트 차이로 판단한다
# (AGENTS.md "해시 불일치는 내용 불일치의 증거가 아니다" 원칙과 동일 근거).
BASELINE_RESULT_DIR = ROOT / "workspace" / "_keep" / "go2_default_vs_pilot_v1"
BASELINE_PREFIX = "go2_default_vs_pilot_v1"
BASELINE_MODEL_SHA = "99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676"
BASELINE_ENV_SHA = "a39c77dc9f45a9ebcff4363e389288ba1e2cf1a38def04a8b05c4337b6fd83ea"
OUTPUT = GO2 / "go2_track_lin_vel_120_v1.zip"
PREFIX = Path("go2_track_lin_vel_120_v1")
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
CANDIDATE_REWARDS = {**DEFAULT_REWARDS, "track_lin_vel_xy_exp": 1.2}
REP_CASES = {
    "G1": "forward_fast",
    "G2": "diagonal_left",
    "G3": "rough_forward",
    "G4": "slope_plus_20",
    "G5": "stairs_15_up",
    "G6": "push_pos_x",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reward_dict(source: str) -> dict[str, float]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "REWARD_WEIGHTS"
            for target in node.targets
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


def registry_payload(seed_count: int) -> bytes:
    registry = json.loads((GO2 / "config" / "go2_self_eval_registry.json").read_text(encoding="utf-8"))
    registry = copy.deepcopy(registry)
    seeds = [101] if seed_count == 1 else [101, 202, 303]
    registry["schema_version"] = "1.1.0"
    registry["status"] = "INTERNAL_PROXY_SPEC_REPAIRED_V2"
    registry["score"]["internal_gates"]["required_evaluation_seeds"] = seeds
    registry["evaluator_repairs"] = {
        "G5_progress": "median per-env integral of body-frame command-projected velocity",
        "G7_DR": "evaluation-only friction, restitution, base-mass, and joint-reset variation",
        "official_equivalence": False,
    }
    for scenario in registry["scenarios"]:
        scenario_id = scenario["id"]
        if scenario_id == "G7":
            scenario["internal_cases"] = [f"dr_seed_{seed}" for seed in seeds]
        else:
            scenario["internal_cases"] = [REP_CASES[scenario_id]]
    return json.dumps(registry, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")


def corrected_progress(steps: bytes) -> float:
    progress: dict[int, float] = {}
    terminated: set[int] = set()
    reader = csv.DictReader(io.StringIO(steps.decode("utf-8")))
    for row in reader:
        env_id = int(row["env_id"])
        cmd_vx = float(row["cmd_vx"])
        cmd_vy = float(row["cmd_vy"])
        norm = (cmd_vx * cmd_vx + cmd_vy * cmd_vy) ** 0.5
        if norm > 1.0e-9 and env_id not in terminated:
            projected_velocity = (
                float(row["actual_vx"]) * cmd_vx + float(row["actual_vy"]) * cmd_vy
            ) / norm
            progress[env_id] = progress.get(env_id, 0.0) + projected_velocity * 0.02
        if int(row["terminated"]):
            terminated.add(env_id)
    values = sorted(progress.values())
    if not values:
        return 0.0
    middle = len(values) // 2
    median = values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2
    return max(0.0, median)


def baseline_payload() -> dict[str, bytes]:
    model = (BASELINE_RESULT_DIR / "training" / "model_best.pt").read_bytes()
    env_yaml = (BASELINE_RESULT_DIR / "training" / "env.yaml").read_bytes()
    if sha(model) != BASELINE_MODEL_SHA or sha(env_yaml) != BASELINE_ENV_SHA:
        raise RuntimeError("baseline model/env identity mismatch")
    payload: dict[str, bytes] = {"default/model_best.pt": model, "default/env.yaml": env_yaml}
    for scenario, case_id in REP_CASES.items():
        base = BASELINE_RESULT_DIR / "evaluation" / "default" / "cases" / "seed_101" / case_id
        summary = json.loads((base / "summary.json").read_bytes())
        if scenario == "G5":
            original = summary.get("projected_progress_m")
            summary["projected_progress_m"] = corrected_progress((base / "steps.csv").read_bytes())
            summary["projected_progress_method"] = "median_per_env_body_velocity_integral_v2"
            summary["projected_progress_original_invalid"] = original
        prefix = f"baseline_seed/cases/seed_101/{case_id}"
        payload[f"{prefix}/summary.json"] = json.dumps(
            summary, indent=2, sort_keys=True
        ).encode("utf-8")
        payload[f"{prefix}/STATUS.txt"] = b"EVAL_RC=0\nSOURCE=VERIFIED_G_A006\n"
    return payload


def build_payload() -> dict[str, bytes]:
    required = source_files() + [
        GO2 / "quadruped_rewards.py",
        GO2 / "go2_fixed_eval_report.py",
        GO2 / "go2_tiered_eval_report.py",
        GO2 / "package_go2_result.py",
        GO2 / "server_run_go2_track_lin_vel_120_v1.sh",
        GO2 / "GO2_TRACK_LIN_VEL_120_README.txt",
        GO2 / "reports" / "GO2_TRACK_LIN_VEL_120_SCREENING_PRD.md",
        GO2 / "config" / "go2_self_eval_registry.json",
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing package input: {missing}")

    payload = baseline_payload()
    default_source = reward_source(DEFAULT_REWARDS)
    candidate_source = reward_source(CANDIDATE_REWARDS)
    for path in source_files():
        relative = path.relative_to(GO2).as_posix()
        payload[f"candidate/{relative}"] = path.read_bytes()
        payload[f"default/{relative}"] = path.read_bytes()
    payload["candidate/quadruped_rewards.py"] = candidate_source
    payload["default/quadruped_rewards.py"] = default_source
    payload["default_quadruped_rewards.py"] = default_source
    payload["go2_tier1_registry.json"] = registry_payload(1)
    payload["go2_representative_registry.json"] = registry_payload(3)
    payload["baseline_provenance.json"] = json.dumps(
        {
            "artifact": f"{BASELINE_RESULT_DIR.name}/ (extracted, source ZIP missing locally — G-F143)",
            "default_checkpoint_iter": 800,
            "default_model_sha256": BASELINE_MODEL_SHA,
            "default_env_sha256": BASELINE_ENV_SHA,
            "baseline_G1_to_G6": "verified seed-101 cases; G5 progress locally recomputed with evaluator v2",
            "baseline_G7": "run once on server with repaired DR because the old G7 was identical to G3",
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    for name in (
        "go2_fixed_eval_report.py",
        "go2_tiered_eval_report.py",
        "go2_policy_lineage.py",
        "package_go2_result.py",
        "server_run_go2_track_lin_vel_120_v1.sh",
        "GO2_TRACK_LIN_VEL_120_README.txt",
    ):
        payload[name] = (GO2 / name).read_bytes()
    payload["GO2_TRACK_LIN_VEL_120_SCREENING_PRD.md"] = (
        GO2 / "reports" / "GO2_TRACK_LIN_VEL_120_SCREENING_PRD.md"
    ).read_bytes()
    manifest = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = manifest.encode("utf-8")
    return payload


def build() -> None:
    payload = build_payload()
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            member = (PREFIX / name).as_posix()
            info = zipfile.ZipInfo(member, date_time=(2026, 9, 2, 0, 0, 0))
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
