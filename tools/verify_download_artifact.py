#!/usr/bin/env python3
"""Deterministically verify downloaded NConnect tar artifacts.

This tool checks transport/package integrity only. It never decides robot behavior,
competition readiness, or whether a policy should be adopted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path, PurePosixPath


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tar", required=True, type=Path)
    parser.add_argument("--sha-file", required=True, type=Path)
    parser.add_argument("--profile", choices=("video", "generic"), default="video")
    parser.add_argument("--work-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-model-sha", default="")
    parser.add_argument("--expected-scenarios", default="")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected_scenarios = [item for item in args.expected_scenarios.split(",") if item]
    result: dict[str, object] = {
        "status": "FAIL",
        "work_id": args.work_id,
        "run_id": args.run_id,
        "profile": args.profile,
        "checks": {},
        "observed": {},
        "missing": [],
        "mismatches": [],
        "behavior_assessment": "UNMEASURED",
        "final_authority": "main_agent",
    }
    checks = result["checks"]
    observed = result["observed"]
    missing = result["missing"]
    mismatches = result["mismatches"]

    if not args.tar.is_file() or not args.sha_file.is_file():
        if not args.tar.is_file():
            missing.append(str(args.tar))
        if not args.sha_file.is_file():
            missing.append(str(args.sha_file))
        checks["files_exist"] = "FAIL"
        return emit(result, args.json_out, 1)
    checks["files_exist"] = "PASS"

    sha_text = args.sha_file.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"\b([0-9a-fA-F]{64})\b", sha_text)
    actual_tar_sha = sha256_file(args.tar)
    observed["tar_sha256"] = actual_tar_sha
    if not match or match.group(1).lower() != actual_tar_sha:
        checks["tar_sha256"] = "FAIL"
        mismatches.append("outer tar SHA256")
        return emit(result, args.json_out, 1)
    checks["tar_sha256"] = "PASS"

    try:
        with tarfile.open(args.tar, "r:gz") as archive:
            members = archive.getmembers()
            unsafe = [member.name for member in members if is_unsafe(member.name)]
            if unsafe:
                checks["safe_paths"] = "FAIL"
                mismatches.extend(f"unsafe tar path: {name}" for name in unsafe)
                return emit(result, args.json_out, 1)
            checks["safe_paths"] = "PASS"
            files = {member.name: member for member in members if member.isfile()}
            observed["tar_file_count"] = len(files)
            checks["tar_readable"] = "PASS"

            manifest_name = suffix_match(files, "/SHA256SUMS.txt")
            if not manifest_name:
                checks["manifest_present"] = "FAIL"
                missing.append("SHA256SUMS.txt")
                return emit(result, args.json_out, 1)
            checks["manifest_present"] = "PASS"
            manifest = read_member(archive, files[manifest_name]).decode("utf-8", "replace")
            internal_ok = 0
            internal_bad: list[str] = []
            for line in manifest.splitlines():
                item = re.match(r"^([0-9a-f]{64})\s+(.+)$", line)
                if not item:
                    continue
                expected_sha, recorded_path = item.groups()
                member_name = resolve_recorded_path(files, recorded_path, args.run_id)
                if not member_name:
                    internal_bad.append(recorded_path)
                    continue
                if sha256_bytes(read_member(archive, files[member_name])) != expected_sha:
                    internal_bad.append(recorded_path)
                else:
                    internal_ok += 1
            observed["internal_sha_ok"] = internal_ok
            observed["internal_sha_bad"] = internal_bad
            checks["manifest_sha256"] = "PASS" if not internal_bad else "FAIL"
            if internal_bad:
                mismatches.extend(f"internal SHA256: {item}" for item in internal_bad)
                return emit(result, args.json_out, 1)

            if args.profile == "video":
                verify_video(archive, files, args, result, expected_scenarios)
    except (tarfile.TarError, OSError) as error:
        checks["tar_readable"] = "FAIL"
        mismatches.append(f"tar read error: {error}")
        return emit(result, args.json_out, 1)

    has_integrity_failure = any(value == "FAIL" for key, value in checks.items() if key not in {"scenario_coverage"})
    incomplete = bool(missing) or checks.get("scenario_coverage") == "PARTIAL"
    if has_integrity_failure:
        result["status"] = "FAIL"
        exit_code = 1
    elif incomplete and args.allow_partial:
        result["status"] = "PARTIAL"
        exit_code = 2
    elif incomplete:
        result["status"] = "FAIL"
        exit_code = 1
    else:
        result["status"] = "PASS"
        exit_code = 0
    return emit(result, args.json_out, exit_code)


def verify_video(archive, files, args, result, expected_scenarios) -> None:
    checks = result["checks"]
    observed = result["observed"]
    missing = result["missing"]
    mismatches = result["mismatches"]

    status_name = suffix_match(files, "/VIDEO_STATUS.tsv")
    if not status_name:
        checks["video_status"] = "FAIL"
        missing.append("VIDEO_STATUS.tsv")
        return
    rows = list(csv.DictReader(io.StringIO(read_member(archive, files[status_name]).decode("utf-8", "replace")), delimiter="\t"))
    latest = {row.get("scenario", ""): row for row in rows}
    successful = sorted(
        scenario
        for scenario, row in latest.items()
        if scenario and row.get("play_rc") == "0" and int(row.get("mp4_bytes") or 0) > 0 and int(row.get("policy_bytes") or 0) > 0
    )
    observed["successful_scenarios"] = successful
    observed["video_count"] = sum(name.endswith(".mp4") for name in files)
    observed["policy_count"] = sum("/policies/" in name and name.endswith(".pt") for name in files)
    checks["video_status"] = "PASS"

    missing_scenarios = sorted(set(expected_scenarios) - set(successful))
    observed["expected_scenarios"] = expected_scenarios
    observed["missing_scenarios"] = missing_scenarios
    if missing_scenarios:
        checks["scenario_coverage"] = "PARTIAL"
        missing.extend(f"scenario:{scenario}" for scenario in missing_scenarios)
    else:
        checks["scenario_coverage"] = "PASS"

    if args.expected_model_sha:
        model_name = suffix_match(files, "/meta/model_best.pt")
        if not model_name:
            checks["checkpoint_match"] = "FAIL"
            missing.append("meta/model_best.pt")
        else:
            actual_model_sha = sha256_bytes(read_member(archive, files[model_name]))
            observed["model_sha256"] = actual_model_sha
            if actual_model_sha == args.expected_model_sha.lower():
                checks["checkpoint_match"] = "PASS"
            else:
                checks["checkpoint_match"] = "FAIL"
                mismatches.append("model_best.pt SHA256")


def read_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    stream = archive.extractfile(member)
    if stream is None:
        raise OSError(f"cannot read member: {member.name}")
    return stream.read()


def suffix_match(files: dict[str, tarfile.TarInfo], suffix: str) -> str | None:
    matches = [name for name in files if name.endswith(suffix) or name == suffix.lstrip("/")]
    return matches[0] if len(matches) == 1 else None


def resolve_recorded_path(files: dict[str, tarfile.TarInfo], recorded: str, run_id: str) -> str | None:
    normalized = recorded.replace("\\", "/")
    marker = f"/{run_id}_videos/"
    if marker in normalized:
        relative = normalized.split(marker, 1)[1]
        return suffix_match(files, f"/{relative}")
    return suffix_match(files, f"/{PurePosixPath(normalized).name}")


def is_unsafe(name: str) -> bool:
    path = PurePosixPath(name)
    return path.is_absolute() or ".." in path.parts


def emit(result: dict[str, object], json_out: Path | None, code: int) -> int:
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(payload)
    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(payload + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
