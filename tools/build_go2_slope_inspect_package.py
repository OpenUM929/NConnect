"""Build the G-A034 one-file package: A017 uphill-stall witness (no training).

The frozen A017 policy, play.py, evaluator and task source are taken byte for
byte from the G-A027 package that produced the stored falls, so the replay runs
the same code on the same weights.
"""

from __future__ import annotations

import hashlib
import io
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
QUAD = REPO / "workspace" / "training" / "quadruped"
SOURCE_ZIP = QUAD / "upload" / "G-A027" / "current" / "go2_a017_full_suite.zip"
SOURCE_PREFIX = "go2_a017_full_suite/"
PREFIX = "go2_slope_inspect/"
ZIP_NAME = "GO2_G_A034_slope_inspect.zip"
OUT_DIR = QUAD / "upload" / "G-A034" / "current"
RUNNER = QUAD / "server_run_go2_slope_inspect.sh"
CHECK = QUAD / "go2_slope_stuck_check.py"
A017_SHA = "0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4"
FIXED_TIME = (2026, 9, 15, 0, 0, 0)

README = """GO2 G-A034  A017 uphill stall witness   (NO TRAINING)
======================================================

The stored A017 suite marks 7 of 32 robots on slope_plus_20 seed 101 as fallen
(envs 4 18 20 22 24 27 31).  Their numbers are level, low and nearly stopped;
no video has ever shown one of them.  This replays that case with the camera
following robots 22, 24, 4 (fallen) and 0 (walked), one replay each, and
re-records the telemetry so STUCK_CHECK.txt shows whether the replay matches.

Run:     bash /workspace/go2_slope_inspect/server_run_go2_slope_inspect.sh
Result:  /workspace/_keep/GO2_SLOPE_INSPECT_RESULT.zip  (+ .sha256)
Options: GO2_INSPECT_ENVS="22 31"   GO2_INSPECT_EYE="[-4.0,-4.0,4.0]"
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if b"\r" in data:
        raise SystemExit(f"CRLF in {path}")
    return data


def build() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(SOURCE_ZIP) as src:
        for info in src.infolist():
            name = info.filename
            if info.is_dir():
                continue
            if name.startswith(SOURCE_PREFIX + "a017/") or name == SOURCE_PREFIX + "package_go2_result.py":
                files[name[len(SOURCE_PREFIX):]] = src.read(name)
    if sha(files["a017/exported/model_best.pt"]) != A017_SHA:
        raise SystemExit("A017 model SHA mismatch in the G-A027 package")
    files["server_run_go2_slope_inspect.sh"] = text_bytes(RUNNER)
    files["go2_slope_stuck_check.py"] = text_bytes(CHECK)
    files["README.txt"] = README.encode("utf-8")
    sums = "".join(f"{sha(files[n])}  {n}\n" for n in sorted(files))
    files["PACKAGE_SHA256SUMS.txt"] = sums.encode("utf-8")
    return files


def write_zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(PREFIX + name, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            archive.writestr(info, files[name])
    data = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as check:
        if check.testzip() is not None:
            raise SystemExit("CRC failure")
    return data


def main() -> int:
    data = write_zip(build())
    digest = sha(data)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / ZIP_NAME).write_bytes(data)
    (OUT_DIR / (ZIP_NAME + ".sha256")).write_text(f"{digest}  {ZIP_NAME}\n", encoding="utf-8")
    command = (
        f"cd /workspace && echo '{digest}  {ZIP_NAME}' | sha256sum -c - && "
        f"unzip -oq {ZIP_NAME} && bash /workspace/go2_slope_inspect/server_run_go2_slope_inspect.sh"
    )
    (OUT_DIR / "CURRENT_UPLOAD.txt").write_text(
        "CURRENT GO2 UPLOAD - G-A034 (A017 uphill stall witness, no training)\n\n"
        f"UPLOAD ONLY THIS ONE FILE\n1. {OUT_DIR / ZIP_NAME}\n   SHA256 {digest}\n\n"
        f"RUN (server, one line)\n{command}\n\n"
        "RESULT\n/workspace/_keep/GO2_SLOPE_INSPECT_RESULT.zip and .sha256\n",
        encoding="utf-8",
    )
    print(f"{ZIP_NAME} {len(data)} bytes sha256 {digest}")
    print(command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
