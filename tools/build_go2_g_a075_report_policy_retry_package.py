#!/usr/bin/env python3
"""Build the PC2 package for the report-derived Go2 stability policy retry.

This package keeps the seven values read from the root report and changes only
flat_orientation_l2 from -0.20 to -0.25.  It reuses the audited candidate
runner and source payload; no training/evaluation code is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))
import build_go2_a033_reward_package as a033  # noqa: E402
import build_go2_g_a057_sweep_package as a057  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

WORK_ID = "G-A075"
PREFIX = "go2_g_a075_report_policy/"
RELEASE = "GO2_G_A075_REPORT_POLICY_v1"
FIXED_TIME = (2026, 10, 9, 0, 0, 0)

# Values copied from report.html; the seventh term is an env reward term.
BASE = {
    "track_lin_vel_xy_exp": 2.0,
    "feet_air_time": 0.01,
    "lin_vel_z_l2": -3.0,
    "ang_vel_xy_l2": -0.05,
    "action_rate_l2": -0.005,
    "flat_orientation_l2": -0.20,
    "track_ang_vel_z_exp": 0.30,
}
CANDIDATE = {**BASE, "flat_orientation_l2": -0.25}
KEY = "report_policy_flat_orientation_l2_m0p25"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sums(files: dict[str, bytes]) -> bytes:
    return "".join(f"{sha(files[k])}  {k}\n" for k in sorted(files)).encode()


def source_payload() -> dict[str, bytes]:
    return a057.source_payload()


def render(template: str, values: dict[str, float]) -> str:
    core = {k: values[k] for k in REWARD_NAMES}
    src = render_reward_source(template, core)
    src = a033.add_env_reward_line(src, "track_ang_vel_z_exp", values["track_ang_vel_z_exp"])
    got = reward_dict(src)
    for k, v in values.items():
        if got.get(k) != v:
            raise ValueError(f"rendered {k}={got.get(k)} != {v}")
    return src


def run_config(template: str) -> str:
    repl = {
        "WORK_ID": WORK_ID,
        "RUN_ID": f"train_{WORK_ID}-Go2_report_policy_3000",
        "EXPERIMENT_SLUG": "go2_g_a075_report_policy",
        "KEEP_DIR_NAME": "go2_g_a075_report_policy",
        "RESULT_ZIP_NAME": "GO2_G_A075_REPORT_POLICY_RESULT.zip",
        "DONE_MARKER": "'[DONE] GO2_G_A075_REPORT_POLICY_RESULT_READY'",
        "TMUX_NAME": "go2_g_a075_report_policy",
        "TRAIN_SEED": "42",
        "NUM_ENVS": "4096",
        "MAX_ITERATIONS": "3000",
        "SINGLE_CHANGE_NAME": "flat_orientation_l2",
        "SINGLE_CHANGE_FROM": "-0.2",
        "SINGLE_CHANGE_TO": "-0.25",
        "BASELINE_NAME": "REPORT_POLICY",
        "BASELINE_LABEL": "report_policy",
        # The runner's stored baseline is still the audited frozen arm shipped
        # in the source payload; these names are descriptive only.
        "EVAL_CHECKPOINT_ITER": "2400",
        "COLLECT_REQUIRED_ON_STATIONARY": "1",
    }
    lines = []
    for line in template.splitlines():
        m = re.match(r"^([A-Z_]+)=", line)
        if m and m.group(1) in repl:
            lines.append(f"{m.group(1)}={repl.pop(m.group(1))}")
        else:
            lines.append(line)
    if repl:
        raise ValueError(f"source run_config lacks {sorted(repl)}")
    return "\n".join(lines) + "\n"


def build() -> tuple[bytes, dict]:
    src = source_payload()
    shared = a057.shared_files(src)
    cand = render(src["candidate/quadruped_rewards.py"].decode(), CANDIDATE)
    base = render(src["candidate/quadruped_rewards.py"].decode(), BASE)
    if [k for k in BASE if BASE[k] != CANDIDATE[k]] != ["flat_orientation_l2"]:
        raise ValueError("candidate must be a single-variable diff")
    expected = {"baseline": {k: float(v) for k, v in BASE.items()},
                "candidate": {k: float(v) for k, v in CANDIDATE.items()}}
    experiment = {
        "schema": "go2_report_policy_single_change_retry_v1",
        "work_id": WORK_ID,
        "device": "PC2",
        "run_key": KEY,
        "purpose": "Retrain the exact report policy and test one stability-only posture change.",
        "promotion": "exploratory_only_until_video_and_internal_gate",
        "report_read_status": "READ_UNMATCHED",
        "report_source": "report.html",
        "report_values": BASE,
        "single_change": {"name": "flat_orientation_l2", "from": -0.20, "to": -0.25},
        "training": {"seed": 42, "num_envs": 4096, "max_iterations": 3000, "from_scratch": True},
        "evaluation": {"checkpoint_iter": 2400, "seeds": [101, 202, 303], "case_count": 69},
        "decision": {
            "improve": "INTERNAL_GATE_PASS candidate only if G3/G5 stability improves and walking is retained",
            "worse": "INTERNAL_GATE_FAIL and retain the report policy",
            "unclear": "INTERNAL_GATE_INCONCLUSIVE; do not try -0.30/-0.50 automatically",
        },
        "design": "workspace/training/quadruped/upload/plan/GO2_G_A075_EXECUTION_RETRY_20261009.md",
    }
    arm = {
        "candidate/quadruped_rewards.py": cand.encode(),
        "reference/baseline_quadruped_rewards.py": base.encode(),
        "reference/reward_base_quadruped_rewards.py": base.encode(),
        "expected_rewards.json": (json.dumps(expected, indent=2) + "\n").encode(),
        "run_config.env": run_config(src["run_config.env"].decode()).encode(),
        "experiment.json": (json.dumps(experiment, ensure_ascii=False, indent=2) + "\n").encode(),
        "README.txt": ("G-A075 report-derived policy\n"
                       "Base: report.html seven values; candidate changes only flat_orientation_l2 -0.20 -> -0.25.\n"
                       "PC2: seed 42, 4096 envs, 3000 iterations, pinned checkpoint 2400, full 69-case collection.\n"
                       "Exploratory result; no automatic adoption or official-score claim.\n").encode(),
    }
    arm["PACKAGE_SHA256SUMS.txt"] = sums({**shared, **arm})
    files = {"shared/" + k: v for k, v in shared.items()}
    files.update({"runs/" + KEY + "/" + k: v for k, v in arm.items()})
    files["points.txt"] = f"{KEY} go2_g_a075_report_policy GO2_G_A075_REPORT_POLICY_RESULT.zip\n".encode()
    files["point_config.env"] = ("POINT_WORK_ID=G-A075\nPOINT_STATUS_DIR_NAME=go2_g_a075_report_policy\n"
                                  "POINT_WORK_DIR=/workspace/go2_g_a075_report_policy_work\n"
                                  "POINT_TMUX_NAME=go2_g_a075_report_policy\n").encode()
    files["run_point.sh"] = (ROOT / "tools/go2_pc2_run_point.sh").read_bytes().replace(b"\r\n", b"\n")
    files["run_all.sh"] = ("#!/usr/bin/env bash\nset -euo pipefail\nROOT_DIR=$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\n"
                           "bash \"$ROOT_DIR/run_point.sh\" --inner " + KEY + "\n").encode()
    files["README.txt"] = ("G-A075 PC2 execution\n"
                            "unzip -oq /workspace/GO2_G_A075_REPORT_POLICY_v1.zip -d /workspace\n"
                            "bash /workspace/go2_g_a075_report_policy/run_all.sh\n"
                            "Results: /workspace/_keep/go2_g_a075_report_policy and GO2_G_A075_REPORT_POLICY_RESULT.zip\n").encode()
    files["SHA256SUMS.txt"] = sums(files)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(PREFIX + name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            z.writestr(info, files[name])
    return buf.getvalue(), {"files": files, "sha": sha(buf.getvalue())}


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--publish", action="store_true")
    args = ap.parse_args()
    data, info = build()
    print(f"work_id={WORK_ID} files={len(info['files'])} bytes={len(data)} sha256={info['sha']}")
    if args.publish:
        out = GO2 / "upload" / WORK_ID / "current"
        out.mkdir(parents=True, exist_ok=True)
        z = out / f"{RELEASE}.zip"
        if z.exists():
            raise SystemExit(f"refuse overwrite: {z}")
        z.write_bytes(data)
        (out / f"{RELEASE}.zip.sha256").write_text(f"{info['sha']}  {z.name}\n", encoding="utf-8", newline="\n")
        print(f"published={z}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
