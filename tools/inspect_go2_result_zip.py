from __future__ import annotations

import hashlib
import json
import os
import posixpath
import sys
import zipfile
from collections import Counter
from pathlib import Path


def unsafe(name: str) -> bool:
    normalized = posixpath.normpath(name.replace("\\", "/"))
    return (
        normalized.startswith("/")
        or normalized == ".."
        or normalized.startswith("../")
        or ":" in normalized.split("/", 1)[0]
    )


def main() -> int:
    archive = Path(sys.argv[1])
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        bad_crc = zf.testzip()
        unsafe_names = [name for name in names if unsafe(name)]
        basenames = Counter(Path(name).name for name in names if not name.endswith("/"))
        status_files = [name for name in names if Path(name).name in {"STATUS.txt", "RESULT_STATUS.txt"}]
        status = {}
        for name in status_files:
            text = zf.read(name).decode("utf-8", errors="replace")
            status[name] = text
        telemetry = [
            name
            for name in names
            if not name.endswith("/")
            and "/telemetry/" in name.replace("\\", "/").lower()
            and name.lower().endswith(".json")
        ]
        videos = [name for name in names if name.lower().endswith(".mp4")]
        important = {
            base: [name for name in names if Path(name).name == base]
            for base in (
                "policy.pt",
                "POLICY_LINEAGE.json",
                "model_best.pt",
                "env.yaml",
                "MANIFEST.sha256",
                "SHA256SUMS.txt",
                "launcher.snapshot.log",
                "launcher.log",
            )
        }
        print(json.dumps({
            "archive": str(archive.resolve()),
            "bytes": archive.stat().st_size,
            "sha256": digest,
            "members": len(names),
            "files": sum(not name.endswith("/") for name in names),
            "bad_crc": bad_crc,
            "unsafe_paths": unsafe_names,
            "status": status,
            "telemetry_json_count": len(telemetry),
            "video_count": len(videos),
            "video_members": videos,
            "important": important,
            "duplicate_basenames": {k: v for k, v in basenames.items() if v > 1},
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
