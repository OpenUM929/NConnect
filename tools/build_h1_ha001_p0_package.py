"""Build the H-A001 P0 speed-grid server package (no training, no reward change).

Output: workspace/training/humanoid/upload/H-A001/current/H_A001_P0_SPEED_GRID_v1.zip (+ .sha256)
Unzip into /workspace/training/humanoid: only the h1_ha001/ folder is added. No distributed file is shipped.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
H1 = REPO / "workspace/training/humanoid"
EDITION = 2  # v2: H1_ROOT / ISAACLAB_SH / NO_TMUX for PC2 (Git Bash)
NAME = f"H_A001_P0_SPEED_GRID_v{EDITION}.zip"
OUT_DIR = H1 / "upload/H-A001/current"
MODELS = {  # published path -> (source, sha256)
    "h1_ha001/models/run06/model_9900.pt": (
        H1 / "_eval_run06/model_best.pt",
        "8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636"),
    "h1_ha001/models/run05/model_2700.pt": (
        H1 / "logs/rsl_rl/humanoid/2026-08-29_16-22-32/model_2700.pt",
        "2775a61e5294f37ec99a1454cdf200b2b0d9cd233022f68c6f293715690e9abc"),
}
TEXT = {
    "h1_ha001/h1_eval_entry.py": H1 / "h1_ha001/h1_eval_entry.py",
    "h1_ha001/server_run_h1_ha001_p0.sh": H1 / "h1_ha001/server_run_h1_ha001_p0.sh",
    "h1_ha001/eval_telemetry.py": H1 / "eval_telemetry.py",
}
FORBIDDEN_PREFIXES = ("play.py", "train.py", "h1_task/", "humanoid_rewards.py", "exported/", "logs/")
RUN_LINE = ("cd /workspace/training/humanoid && unzip -o " + NAME +
            " && bash h1_ha001/server_run_h1_ha001_p0.sh")
README = f"""H-A001 P0 — Run06 / Run05 speed grid (no training)
Plan: workspace/training/humanoid/upload/plan/H1_STABLE_SPEED_TUNING_DEBATE_20261008.md §12, §14
Adds only h1_ha001/. play.py, train.py, h1_task/, humanoid_rewards.py, exported/ are not touched (R-6).
The runner refuses to start unless play.py matches the distributed original SHA.

Run on the cloud server (upload the ZIP to /workspace/training/humanoid first):
  {RUN_LINE}
Monitor: tmux attach -t h1_ha001_p0
Run on PC2 (Git Bash, no tmux): see HANDOFF_H_A001_PC2.md §2 (NO_TMUX=1, ISAACLAB_SH, nohup).
Expected time: about 30-45 min (2 policies x 9 cases x 3 seeds, 32 env x 1000 steps each).
Resume after a failure: EVAL_RESUME=1 bash h1_ha001/server_run_h1_ha001_p0.sh

Download only after [DONE]:
  /workspace/_keep/H_A001_P0_SPEED_GRID_FULL.tar.gz
  /workspace/_keep/H_A001_P0_SPEED_GRID_FULL.tar.gz.sha256
Server shutdown gate: both FULL files downloaded and sha256 verified locally. PARTIAL is not complete.
Video: NOT_REQUIRED (fixed-policy telemetry only; policies already have Run06/Run05 videos).
report.html: NOT_APPLICABLE (no training in this package).
Local readout: python -I tools/h1_ha001_p0_readout.py <extracted>/H_A001_P0_SPEED_GRID
"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lf(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def build(out_dir: Path = OUT_DIR) -> Path:
    files: dict[str, bytes] = {k: lf(v) for k, v in TEXT.items()}
    for k, (src, want) in MODELS.items():
        data = src.read_bytes()
        if sha(data) != want:
            raise SystemExit(f"model SHA mismatch: {src}")
        files[k] = data
    files["h1_ha001/README_H_A001.txt"] = README.encode("utf-8")
    sums = "".join(f"{sha(v)}  {k}\n" for k, v in sorted(files.items()))
    files["h1_ha001/SHA256SUMS.txt"] = sums.encode("utf-8")
    bad = [k for k in files if k.startswith(FORBIDDEN_PREFIXES)]
    if bad:
        raise SystemExit(f"distributed files must not be shipped: {bad}")
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / NAME
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in sorted(files.items()):
            info = zipfile.ZipInfo(k, date_time=(2026, 10, 8, 0, 0, 0))
            info.external_attr = (0o755 if k.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, v)
    # bytes, not write_text: Windows text mode would write CRLF and break `sha256sum -c`
    (out_dir / (NAME + ".sha256")).write_bytes(f"{sha(zpath.read_bytes())}  {NAME}\n".encode())
    return zpath


if __name__ == "__main__":
    p = build(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DIR)
    print(p, sha(p.read_bytes()))
    print("RUN:", RUN_LINE)
