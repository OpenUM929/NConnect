#!/usr/bin/env python3
"""Build G-A085: precision evaluation of G-A082/G-A083/G-A084 iter-2400 policies (PC2, no training).

Approved by the user on 2026-10-15 (design in upload/plan/GO2_G_A085_PLAN_20261015.md):
  - six new evaluation seeds per policy as two 69-case suites (404/505/606, 707/808/909)
  - diagnostic replay (roll/pitch, foot contact) of the fall cases for A083 and A084
  - standard-library analysis on PC2 (tools/go2_g_a085_precision_analysis.py)
  - no reward change, no training, no video

The evaluation functions are cut byte-for-byte out of the G-A084 runner and pasted into
tools/go2_g_a085_eval_template.sh; deployed play/eval files come from the same source chain
(a082 -> a076 source payload, a057 shared files), so the ruler is the G-A082..G-A084 one.

    python tools/build_go2_g_a085_package.py --check
    python tools/build_go2_g_a085_package.py --publish     (never overwrites)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_g_a084_package as b84  # noqa: E402

WORK_ID = "G-A085"
SLUG = "go2_g_a085_precision_eval"
PREFIX = SLUG + "/"
RELEASE = "GO2_G_A085_PRECISION_EVAL_v1"
FIXED_TIME = (2026, 10, 15, 0, 0, 0)
EVALUATOR_SHA = "e1a988bd770cf915f5d7b88f50b34e2d42cceb7d827e1363bebe9218b5e975ae"
DIAG_MODULE_SHA = "8d5181804807e7023817991d36d4de26da657544f2dee7f55474d075e0658ce0"
DIAG_WRAPPER_SHA = "af333430d3ebafdd19a9f59ec3981681a60e94799352eb7a814bb63a16571d1b"
KEEP = ROOT / "workspace/_keep"
POLICIES = {
    "a082": (KEEP / "go2_g_a082_track_ang_vel_z_p0p75",
             "df214dc9aa1fa13acff0e13987943580c3d7d181b60dde282a463e8080bb2f04",
             "862a59adb8b60ac9caa3b5f9e46df3a801bb056198c0bd36a9dfbcf1d4f6dce2"),
    "a083": (KEEP / "go2_g_a083_action_rate_m0p01",
             "bbbc04f4624f6c1401f20b7937a3f8ed82427a288b0158525efb48091e07b27a",
             "8bf58925f6de58206967d12d556d1e0cf4de76de5218195a14e5f3e25011e513"),
}
EVAL_ROOT_FILES = ("play.py", "pyproject.toml", "go2_eval_telemetry.py", "go2_policy_lineage.py",
                   "go2_task/__init__.py", "go2_task/_finalize.py", "go2_task/agent_cfg.py", "go2_task/env_cfg.py")
FUNC_START, FUNC_END = b"PLANE=(\n", b"run_video() {"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise SystemExit(f"[FAIL] {msg}")


def lf(data: bytes, name: str) -> bytes:
    data = data.replace(b"\r\n", b"\n")
    need(b"\r" not in data, f"{name} has CR bytes")
    return data


def runner_functions(runner: bytes) -> bytes:
    i, j = runner.index(FUNC_START), runner.index(FUNC_END)
    block = runner[i:j]
    for name in (b"set_case() {", b"run_eval_case() {", b"stage_policy() {", b"write_identity() {", b"run_full_suite() {"):
        need(block.count(name) == 1, f"runner block lacks {name!r}")
    need(b"train.py" not in block, "training command inside the evaluation block")
    return block.rstrip(b"\n")


def experiment() -> dict:
    return {
        "schema": "go2_g_a085_precision_eval_v1",
        "work_id": WORK_ID,
        "device": "PC2",
        "kind": "evaluation_only_no_training_no_reward_change",
        "purpose": "Measure evaluation noise (sd over evaluation seeds) so that G-A082/G-A083/G-A084 differences can be judged against it, and record roll/pitch and foot contact on the fall cases.",
        "user_approval": "2026-10-15: design approved ('안대로 진행'), build now and run after G-A084",
        "policies": {
            "a082": {"model_sha256": POLICIES["a082"][1], "env_sha256": POLICIES["a082"][2], "source": "shipped"},
            "a083": {"model_sha256": POLICIES["a083"][1], "env_sha256": POLICIES["a083"][2], "source": "shipped"},
            "a084": {"source": "PC2 /workspace/_keep/go2_g_a084_ang_vel_xy_m0p065, RUNNER_RC=0 and model SHA == CHECKPOINT_PIN EVAL_CHECKPOINT_SHA"},
        },
        "evaluation": {"new_seed_sets": [[404, 505, 606], [707, 808, 909]], "cases_per_set": 69,
                       "original_seed_set": [101, 202, 303], "evaluator_sha256": EVALUATOR_SHA,
                       "episode_steps": 1000, "robots_per_case": 32},
        "diag_replay": {"policies": ["a083", "a084"], "seeds": [101, 202, 303],
                        "cases": ["rough_forward", "rough_lateral", "push_pos_x", "push_neg_x", "push_pos_y"],
                        "extra": "dr_seed_101 at seed 101",
                        "diag_module_sha256": DIAG_MODULE_SHA, "diag_wrapper_sha256": DIAG_WRAPPER_SHA,
                        "validity": "a diag run is used only where its steps.csv is byte-identical to the stored original (PLAIN_VS_DIAG)"},
        "preregistered_rules": {
            "noise": "per-case sd of case_score / survival / exy over the 9 evaluation seeds; formula-score sd over the three seed sets",
            "real_difference": "a policy difference counts as real only when it exceeds twice the evaluation sd of that metric",
            "metrics": ["formula score (H1 official-fit, internal)", "G6 exy_mean", "tilt-type first departures on G3+G6",
                        "15cm stair survival", "stairs full proxy", "heading-change medians", "G3 survival", "terrain along speed"],
            "use": "decide which of G-A083 / G-A084 is the candidate and set future preregistration thresholds from the measured sd",
        },
        "correction_g_a084_prereg": "G-A084 experiment.json gives the G-A083 reference for tilt_falls_G3_G6 as 7; counted the same way as the metric (fall_tilt over all 18 rows, including robots that recovered) it is 9. The threshold <=3 is unchanged; the published package is not edited.",
        "limits": ["evaluation seeds do not measure training-seed variation",
                   "internal proxy only; OFFICIAL_RESULT_UNMEASURED",
                   "a replay compares behaviour of stored policies; it does not prove a reward's causal effect"],
    }


def entries() -> dict[str, bytes]:
    src = b84.a082.a076.source_payload()
    shared = b84.a082.a057.shared_files(src)
    runner = b84.patched_runner(src["server_run_go2_candidate_iter_pinned.sh"])
    out: dict[str, bytes] = {}
    for rel in EVAL_ROOT_FILES:
        out[f"shared/eval_root/{rel}"] = shared[f"candidate/{rel}"]
    need(sha(out["shared/eval_root/go2_eval_telemetry.py"]) == EVALUATOR_SHA, "evaluator is not e1a988bd")
    for rel in ("posture_contract_check.py", "package_go2_result.py", "go2_self_eval_registry.json"):
        out[f"shared/{rel}"] = shared[rel]
    need(sha(out["shared/go2_self_eval_registry.json"]) == b84.REGISTRY_SHA, "registry differs from G-A084")
    diag = {"go2_eval_diag_v2.py": DIAG_MODULE_SHA, "go2_eval_telemetry_diag_wrapper_v2.py": DIAG_WRAPPER_SHA}
    for name, digest in diag.items():
        data = (GO2 / name).read_bytes()
        need(sha(data) == digest, f"{name} changed")
        out[f"shared/diag/{name}"] = data
    out["shared/go2_g_a085_precision_analysis.py"] = lf((ROOT / "tools/go2_g_a085_precision_analysis.py").read_bytes(), "analysis")
    out["shared/go2_climb_count.py"] = lf((ROOT / "tools/go2_climb_count.py").read_bytes(), "climb")
    for key, (keep, msha, esha) in POLICIES.items():
        model = (keep / "training/model_best.pt").read_bytes()
        env = (keep / "training/env.yaml").read_bytes()
        need(sha(model) == msha and sha(env) == esha, f"{key} model/env SHA")
        ident = json.loads((keep / "evaluation/candidate/identity.json").read_text(encoding="utf-8"))
        need(ident["model_sha256"] == msha and ident["env_sha256"] == esha and ident["evaluator_sha256"] == EVALUATOR_SHA,
             f"{key} stored identity")
        out[f"policies/{key}/model_best.pt"] = model
        out[f"policies/{key}/env.yaml"] = env
        out[f"policies/{key}/quadruped_rewards.py"] = (keep / "training/source/quadruped_rewards.py").read_bytes()
    template = lf((ROOT / "tools/go2_g_a085_eval_template.sh").read_bytes(), "template")
    script = template.replace(b"@EVAL_FUNCTIONS@", runner_functions(runner))
    for k, v in {"EVALUATOR_SHA": EVALUATOR_SHA, "A082_MODEL_SHA": POLICIES["a082"][1], "A082_ENV_SHA": POLICIES["a082"][2],
                 "A083_MODEL_SHA": POLICIES["a083"][1], "A083_ENV_SHA": POLICIES["a083"][2]}.items():
        need(script.count(f"@{k}@".encode()) == 1, f"template placeholder {k}")
        script = script.replace(f"@{k}@".encode(), v.encode())
    need(b"@" + b"EVAL_FUNCTIONS@" not in script, "function block not inserted")
    out["go2_g_a085_eval.sh"] = script
    out["run_all.sh"] = (b"#!/usr/bin/env bash\nset -euo pipefail\nROOT_DIR=$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\n"
                         b"bash \"$ROOT_DIR/go2_g_a085_eval.sh\" \"$@\"\n")
    out["experiment.json"] = (json.dumps(experiment(), ensure_ascii=False, indent=2) + "\n").encode()
    out["README.txt"] = (f"G-A085 PC2 precision evaluation (no training)\nunzip -oq /workspace/{RELEASE}.zip -d /workspace\n"
                         f"bash /workspace/{SLUG}/run_all.sh\nStarts only after G-A084 finished with RUNNER_RC=0 (else rc 26, nothing started).\n"
                         "Progress: cat /workspace/_keep/GO2_G_A085_STATUS.txt\n").encode()
    out["SHA256SUMS.txt"] = "".join(f"{sha(v)}  {k}\n" for k, v in sorted(out.items())).encode()
    return out


def write_zip(target: Path) -> dict[str, object]:
    files = entries()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w") as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(PREFIX + name, FIXED_TIME)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_STORED if name.endswith(".pt") else zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name])
    data = target.read_bytes()
    return {"files": files, "sha": sha(data), "bytes": len(data)}


def publish() -> tuple[Path, dict[str, object]]:
    out = GO2 / "upload" / WORK_ID / "current"
    out.mkdir(parents=True, exist_ok=True)
    need(not any(out.iterdir()), f"refuse overwrite: {out}")
    final = out / f"{RELEASE}.zip"
    info = write_zip(final)
    need(info["bytes"] < 95 * 1024 * 1024, "package unexpectedly large; parts logic not implemented")
    (out / f"{RELEASE}.zip.sha256").write_text(f"{info['sha']}  {RELEASE}.zip\n", encoding="utf-8", newline="\n")
    return final, info


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.publish:
        path, info = publish()
        print(f"published={path} bytes={info['bytes']} sha256={info['sha']}")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            info = write_zip(Path(temp_dir) / f"{RELEASE}.zip")
            print(f"work_id={WORK_ID} files={len(info['files'])} bytes={info['bytes']} sha256={info['sha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
