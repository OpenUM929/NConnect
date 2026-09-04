"""Build and verify the Run06 independent multi-seed evaluation package."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUMANOID = ROOT / "workspace" / "training" / "humanoid"
OUTPUT = HUMANOID / "run06_independent_eval_package.zip"
MODEL_SHA = "8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inputs() -> list[Path]:
    paths = [
        HUMANOID / "play.py",
        HUMANOID / "humanoid_rewards.py",
        HUMANOID / "eval_telemetry.py",
        HUMANOID / "fixed_eval_report.py",
        HUMANOID / "independent_eval_report.py",
        HUMANOID / "server_run06_independent_eval.sh",
        HUMANOID / "RUN06_INDEPENDENT_EVAL_README.txt",
        HUMANOID / "pyproject.toml",
        HUMANOID / "_eval_run06" / "model_best.pt",
        HUMANOID / "_eval_run06" / "env.yaml",
    ]
    paths.extend(sorted((HUMANOID / "h1_task").glob("*.py")))
    return paths


def build() -> None:
    files = inputs()
    missing = [path for path in files if not path.is_file()]
    if missing:
        raise SystemExit(f"missing package inputs: {missing}")
    model = HUMANOID / "_eval_run06" / "model_best.pt"
    if sha256(model.read_bytes()) != MODEL_SHA:
        raise SystemExit("staged model is not Run06 model_9900")

    payload = {path.relative_to(HUMANOID).as_posix(): path.read_bytes() for path in files}
    manifest = "".join(f"{sha256(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["RUN06_INDEPENDENT_EVAL_PACKAGE_SHA256SUMS.txt"] = manifest.encode("utf-8")

    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 31, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)

    with zipfile.ZipFile(OUTPUT) as archive:
        if set(archive.namelist()) != set(payload):
            raise SystemExit("zip member set mismatch")
        if archive.testzip() is not None:
            raise SystemExit("zip CRC failure")
        for name, expected in payload.items():
            if archive.read(name) != expected:
                raise SystemExit(f"zip content mismatch: {name}")
    print(f"package={OUTPUT}")
    print(f"bytes={OUTPUT.stat().st_size}")
    print(f"sha256={sha256(OUTPUT.read_bytes())}")
    print(f"members={len(payload)}")


if __name__ == "__main__":
    build()
