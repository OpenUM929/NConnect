"""Create a safe one-file ZIP from the server result directory."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: package_go2_result.py <result-dir> <output.zip>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    temporary = output.with_suffix(output.suffix + ".tmp")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(root.rglob("*")):
            # launcher.log is still being written by tee while packaging.  The
            # runner creates launcher.snapshot.log immediately before the
            # manifest so the packaged log and manifest remain immutable.
            if path.is_file() and path.name != "launcher.log":
                archive.write(path, (Path(root.name) / path.relative_to(root)).as_posix())
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("result ZIP CRC failure")
    temporary.replace(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
