"""Publish verified Go2 server inputs into a current folder and immutable history."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
UPLOAD_ROOT = GO2 / "upload"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_verified(source: Path, destination: Path, *, immutable: bool = False) -> str:
    digest = file_sha256(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing_digest = file_sha256(destination)
        if immutable and existing_digest != digest:
            raise RuntimeError(f"immutable release conflict: {destination}")
        if existing_digest != digest:
            shutil.copy2(source, destination)
    else:
        shutil.copy2(source, destination)
    copied_digest = file_sha256(destination)
    if copied_digest != digest:
        raise RuntimeError(f"copy verification failed: {destination}")
    destination.with_suffix(destination.suffix + ".sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="utf-8", newline="\n"
    )
    return digest


def append_history(history: Path, row: list[str]) -> None:
    header = [
        "published_at_utc",
        "experiment_id",
        "release_id",
        "status",
        "engine_file",
        "engine_sha256",
        "spec_file",
        "spec_sha256",
        "note",
    ]
    history.parent.mkdir(parents=True, exist_ok=True)
    existing = history.read_text(encoding="utf-8") if history.exists() else ""
    line = "\t".join(row)
    identity = tuple(row[1:8])
    recorded_identities = {
        tuple(recorded.split("\t")[1:8])
        for recorded in existing.splitlines()[1:]
        if len(recorded.split("\t")) >= 8
    }
    if identity not in recorded_identities:
        with history.open("a", encoding="utf-8", newline="\n") as stream:
            if not existing:
                stream.write("\t".join(header) + "\n")
            stream.write(line + "\n")


def publish(args: argparse.Namespace) -> None:
    engine = Path(args.engine).resolve()
    spec = Path(args.spec).resolve()
    for path in (engine, spec):
        if not path.is_file():
            raise FileNotFoundError(path)

    experiment_root = UPLOAD_ROOT / args.experiment_id
    current = experiment_root / "current"
    archive = experiment_root / "history" / args.release_id

    engine_sha = copy_verified(engine, archive / engine.name, immutable=True)
    spec_sha = copy_verified(spec, archive / spec.name, immutable=True)
    copy_verified(engine, current / engine.name)
    copy_verified(spec, current / spec.name)

    optional_files: list[Path] = []
    for value in (args.run_guide, args.verification):
        if value:
            path = Path(value).resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            optional_files.append(path)
            copy_verified(path, archive / path.name, immutable=True)
            copy_verified(path, current / path.name)

    archive_manifest = archive / "UPLOAD_MANIFEST.json"
    if archive_manifest.exists():
        published_at = json.loads(archive_manifest.read_text(encoding="utf-8"))["published_at_utc"]
    else:
        published_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "published_at_utc": published_at,
        "experiment_id": args.experiment_id,
        "release_id": args.release_id,
        "status": args.status,
        "upload_files": [
            {"name": engine.name, "sha256": engine_sha, "server_path": f"/workspace/{engine.name}"},
            {"name": spec.name, "sha256": spec_sha, "server_path": f"/workspace/{spec.name}"},
        ],
        "support_files": [path.name for path in optional_files],
        "note": args.note,
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if archive_manifest.exists():
        if archive_manifest.read_text(encoding="utf-8") != manifest_text:
            raise RuntimeError(f"immutable release manifest conflict: {archive_manifest}")
    else:
        archive_manifest.write_text(manifest_text, encoding="utf-8", newline="\n")
    (current / "UPLOAD_MANIFEST.json").write_text(manifest_text, encoding="utf-8", newline="\n")

    current_guide = (
        f"CURRENT GO2 UPLOAD — {args.experiment_id}\n\n"
        "UPLOAD ONLY THESE TWO FILES\n"
        f"1. {current / engine.name}\n"
        f"   SHA256 {engine_sha}\n"
        f"2. {current / spec.name}\n"
        f"   SHA256 {spec_sha}\n\n"
        f"RELEASE_ID {args.release_id}\n"
        f"STATUS {args.status}\n"
        "History is preserved under ../history and in ../UPLOAD_HISTORY.tsv.\n"
    )
    (current / "CURRENT_UPLOAD.txt").write_text(current_guide, encoding="utf-8", newline="\n")

    append_history(
        experiment_root / "UPLOAD_HISTORY.tsv",
        [
            published_at,
            args.experiment_id,
            args.release_id,
            args.status,
            engine.name,
            engine_sha,
            spec.name,
            spec_sha,
            args.note.replace("\t", " ").replace("\n", " "),
        ],
    )
    print(f"current={current}")
    print(f"history={archive}")
    print(f"engine_sha256={engine_sha}")
    print(f"spec_sha256={spec_sha}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--run-guide")
    parser.add_argument("--verification")
    parser.add_argument("--status", default="ACTIVE")
    parser.add_argument("--note", default="")
    return parser.parse_args()


if __name__ == "__main__":
    publish(parse_args())
