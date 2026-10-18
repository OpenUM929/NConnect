#!/usr/bin/env python3
"""Build G-A093: the final official-server submission training (Go2, 5,000 iterations).

User decision (2026-10-18): train the submission policy on the official server at the lecture's
"full training" length (13강 "5000(본격 학습)", agent_cfg.py max_iterations = 5000).  The rewards
depend on the G-A092 readout: improved -> G-A092 rewards (feet_air_time 0.05), otherwise the
G-A083 rewards.  Both editions are built here so the right ZIP is ready either way.

Base: the G-A079 v3 server package (tools/build_go2_g_a079_v3_package.py), which already ran on the
official server: every checkpoint is mirrored, a server stop continues from the newest one, a
non-finite collapse is not continued and the newest checkpoint before it is evaluated.  G-A079 v3
lost its evaluation to an Isaac Sim crash on case 61/69 (rc 5), so this build adds one change to our
runner: an evaluation case or video that fails is retried (3 attempts, logged in
logs/EVAL_RETRIES.txt).  Deployed train.py/play.py/go2_task stay byte-identical (R-6); only the
reward values, our runner and the config differ.

    python tools/build_go2_g_a093_final_server_package.py --check     build both in memory, validate, print SHA
    python tools/build_go2_g_a093_final_server_package.py --publish   also write the ZIPs (never overwrites)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))
import build_go2_g_a079_v3_package as v3  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402

WORK_ID = "G-A093"
OUT = GO2 / "upload/G-A093/current"
RUNNER = v3.RUNNER
BASH = v3.BASH
MAX_ITERATIONS = v3.MAX_ITERATIONS
EVAL_ITER = v3.EVAL_ITER
EVAL_ATTEMPTS = 3
FIXED_TIME = (2026, 10, 18, 0, 0, 0)

A083 = {
    "track_lin_vel_xy_exp": 2.0,
    "track_ang_vel_z_exp": 0.75,
    "feet_air_time": 0.01,
    "lin_vel_z_l2": -3.0,
    "ang_vel_xy_l2": -0.05,
    "action_rate_l2": -0.01,
    "flat_orientation_l2": -0.225,
}
EDITIONS = {
    "a083": {
        "key": "final_a083",
        "slug": "go2_g_a093_final_a083_5000",
        "release": "GO2_G_A093_FINAL_A083_5000_v1",
        "result": "GO2_G_A093_FINAL_A083_5000_RESULT.zip",
        "rewards": dict(A083),
        "source": "G-A083 (PC2 iter 2400: formula 57.59/70, legacy 63.48)",
        "when": "G-A092 is not an improvement over G-A083 (formula <= 57.59 or protection failed)",
    },
    "a092": {
        "key": "final_a092_feet0p05",
        "slug": "go2_g_a093_final_feet0p05_5000",
        "release": "GO2_G_A093_FINAL_FEET0P05_5000_v1",
        "result": "GO2_G_A093_FINAL_FEET0P05_5000_RESULT.zip",
        "rewards": {**A083, "feet_air_time": 0.05},
        "source": "G-A092 (G-A083 rewards with feet_air_time 0.01 -> 0.05)",
        "when": "G-A092 improves on G-A083 (formula > 57.59 with protection held)",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def once(data: str, old: str, new: str, what: str) -> str:
    assert data.count(old) == 1, f"anchor not unique/absent: {what} ({data.count(old)})"
    return data.replace(old, new)


def patch_eval_retry(runner: str) -> str:
    """Retry a failed evaluation case or video (Isaac Sim crashed on G-A079 v3 case 61/69)."""
    head = '  rm -rf -- "$out"\n  mkdir -p "$out"\n  printf \'COMMAND: \''
    tail = 'echo "[FAIL] eval $label $scenario/$case_id seed=$seed rc=$rc"; exit 5;\n  }\n'
    start = runner.index(head)
    assert runner.count(head) == 1
    end = runner.index(tail, start) + len(tail)
    block = runner[start:end]
    body = block[len('  rm -rf -- "$out"\n  mkdir -p "$out"\n'):block.index("  [[ \"$rc\" == 0 && -s \"$out/summary.json\" ]]")]
    body = once(body, "  local rc=${PIPESTATUS[0]}\n", "  rc=${PIPESTATUS[0]}\n", "case rc")
    body = once(body, '| tee "$KEEP/logs/$label/seed_${seed}_${case_id}.log"',
                '| tee -a "$KEEP/logs/$label/seed_${seed}_${case_id}.log"', "case log append")
    body = "".join("  " + line if line.strip() else line for line in body.splitlines(keepends=True))
    new = (
        f"  # G-A093: retry a failed case ({EVAL_ATTEMPTS} attempts); same seed and inputs, so a retry repeats the measurement.\n"
        "  local attempt rc=1\n"
        f"  for attempt in $(seq 1 {EVAL_ATTEMPTS}); do\n"
        '    rm -rf -- "$out"\n'
        '    mkdir -p "$out"\n'
        + body +
        '    if [[ "$rc" == 0 && -s "$out/summary.json" ]] && grep -qx \'EVAL_RC=0\' "$out/STATUS.txt"; then break; fi\n'
        '    echo "[RETRY] eval $label $scenario/$case_id seed=$seed attempt $attempt rc=$rc" | tee -a "$KEEP/logs/EVAL_RETRIES.txt"\n'
        f'    if [[ "$attempt" == {EVAL_ATTEMPTS} ]]; then\n'
        '      echo "[FAIL] eval $label $scenario/$case_id seed=$seed rc=$rc"; exit 5\n'
        "    fi\n"
        '    sleep "${GO2_EVAL_RETRY_SLEEP_S:-15}"\n'
        "  done\n"
    )
    runner = runner[:start] + new + runner[end:]

    vold = ('  "${push_env[@]}" "${cmd[@]}" \\\n'
            '    2>&1 | tee "$KEEP/logs/$label/video_${scenario}_${case_id}_seed_${seed}.log"\n'
            '  [[ -s exported/play_video.mp4 ]] || { echo "[FAIL] video missing: $label $scenario"; exit 8; }\n')
    vnew = (f"  # G-A093: retry a failed video ({EVAL_ATTEMPTS} attempts).\n"
            "  local vtry vrc=1\n"
            f"  for vtry in $(seq 1 {EVAL_ATTEMPTS}); do\n"
            "    rm -f exported/play_video.mp4\n"
            "    set +e\n"
            '    "${push_env[@]}" "${cmd[@]}" \\\n'
            '      2>&1 | tee -a "$KEEP/logs/$label/video_${scenario}_${case_id}_seed_${seed}.log"\n'
            "    vrc=${PIPESTATUS[0]}\n"
            "    set -e\n"
            "    [[ ! -s exported/play_video.mp4 ]] || break\n"
            '    echo "[RETRY] video $label $scenario/$case_id seed=$seed attempt $vtry rc=$vrc" | tee -a "$KEEP/logs/EVAL_RETRIES.txt"\n'
            f'    [[ "$vtry" != {EVAL_ATTEMPTS} ]] || {{ echo "[FAIL] video missing: $label $scenario"; exit 8; }}\n'
            '    sleep "${GO2_EVAL_RETRY_SLEEP_S:-15}"\n'
            "  done\n")
    return once(runner, vold, vnew, "video retry")


def set_rewards(source: str, rewards: dict[str, float]) -> str:
    for name, value in rewards.items():
        # Active entries only: the deployed file also carries commented-out examples of the same keys.
        source, count = re.subn(r'^(\s*"' + re.escape(name) + r'"\s*:\s*)-?[0-9.]+', lambda m: m.group(1) + repr(value),
                                source, flags=re.M)
        assert count == 1, name
    assert reward_dict(source) == rewards, reward_dict(source)
    return source


def readme(ed: dict) -> str:
    r = ed["rewards"]
    return f"""G-A093 final official-server training ({ed['release']}).
Rewards: {ed['source']}.
  track_lin_vel_xy_exp {r['track_lin_vel_xy_exp']}, track_ang_vel_z_exp {r['track_ang_vel_z_exp']}, feet_air_time {r['feet_air_time']},
  lin_vel_z_l2 {r['lin_vel_z_l2']}, ang_vel_xy_l2 {r['ang_vel_xy_l2']}, action_rate_l2 {r['action_rate_l2']}, flat_orientation_l2 {r['flat_orientation_l2']}
Use this edition when: {ed['when']}.

Fresh training, seed 42, 4096 envs, {MAX_ITERATIONS} iterations (lecture 13: "5000 = full training").
Then 69 evaluation cases + 10 videos on checkpoint {EVAL_ITER}; play.py exports policy.pt from it.
Deployed train.py/play.py/go2_task are unchanged; only our runner and the reward values differ.

Start in tmux (closing the browser does not stop it), and continue after any stop, with the same line:
  ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh bash /workspace/{ed['slug']}/run_point.sh --only {ed['key']}
Progress:  tmux attach -t {ed['slug']}     (leave with Ctrl+b then d)

- Every saved checkpoint is copied to /workspace/_keep/{ed['slug']}_all_checkpoints.
- Value loss goes non-finite (our seed-42 server runs did at 2584 and 2836): training is not continued;
  the newest checkpoint saved before the run-up is evaluated (training/EVAL_CHECKPOINT_OVERRIDE.txt).
- An evaluation case or video that crashes is retried up to {EVAL_ATTEMPTS} times (logs/EVAL_RETRIES.txt).
- Download when done: /workspace/_keep/{ed['result']} and its .sha256.
  Submission files inside: evaluation/candidate/policy.pt, training/env.yaml, exported/report.html.
"""


def build(edition: str) -> tuple[dict[str, bytes], dict[str, bytes]]:
    ed = EDITIONS[edition]
    files, base = v3.build()
    src_arm, arm, key = v3.ARM, f"runs/{ed['key']}/", ed["key"]
    files = {(arm + n[len(src_arm):] if n.startswith(src_arm) else n): b for n, b in files.items()}
    files.pop("root_report.html", None)
    files.pop(arm + "PACKAGE_SHA256SUMS.txt")
    files.pop("SHA256SUMS.txt")

    reward_path = arm + "candidate/quadruped_rewards.py"
    files[reward_path] = set_rewards(files[reward_path].decode("utf-8"), ed["rewards"]).encode()
    expected = json.loads(files[arm + "expected_rewards.json"])
    expected["candidate"] = dict(ed["rewards"])
    files[arm + "expected_rewards.json"] = (json.dumps(expected, indent=2) + "\n").encode()

    cfg = files[arm + "run_config.env"].decode()
    for name, value in {
        "WORK_ID": WORK_ID,
        "RUN_ID": f"train_{WORK_ID}-Go2_{key}_{MAX_ITERATIONS}_server",
        "EXPERIMENT_SLUG": ed["slug"], "KEEP_DIR_NAME": ed["slug"], "TMUX_NAME": ed["slug"],
        "RESULT_ZIP_NAME": ed["result"], "DONE_MARKER": f"'[DONE] {ed['result'][:-4]}_READY'",
        "SINGLE_CHANGE_NAME": "final_rewards", "SINGLE_CHANGE_FROM": "G-A077-server", "SINGLE_CHANGE_TO": edition,
        "MAX_ITERATIONS": str(MAX_ITERATIONS), "EVAL_CHECKPOINT_ITER": str(EVAL_ITER),
    }.items():
        cfg, count = re.subn(r"^" + name + r"=.*$", lambda _m: f"{name}={value}", cfg, flags=re.M)
        assert count == 1, name
    files[arm + "run_config.env"] = cfg.encode()

    exp = json.loads(files[arm + "experiment.json"])
    exp.update(schema="go2_g_a093_final_server_5000_v1", work_id=WORK_ID, device="official server",
               edition=edition, rewards=dict(ed["rewards"]), reward_source=ed["source"], use_when=ed["when"])
    exp.pop("single_change", None)
    exp.pop("source_report", None)
    exp["purpose"] = ("Final submission training on the official server (R-6/Article 14: the submitted policy must come "
                      "from the server training history). Lecture 13: '5000(본격 학습)'.")
    exp["user_decision"] = ("2026-10-18: after the G-A092 result, train the final policy on the official server at the lecture's "
                            "full length; improved -> G-A092 rewards, otherwise the existing (G-A083) rewards.")
    exp["evaluation"]["checkpoint_reason"] = (
        f"Policy at the end of training ({EVAL_ITER}); after a collapse the newest checkpoint before it (recorded override). "
        "The stored baseline arm is the A077 server policy at 2400 and is a reference only.")
    exp["evaluation"]["retry"] = f"{EVAL_ATTEMPTS} attempts per case/video; logs/EVAL_RETRIES.txt"
    exp["divergence_prior"] = ("Our official-server seed-42 runs of this lineage went non-finite at 2584 (G-A077, twice, "
                               "bit-identical) and 2836 (G-A079); PC2 G-A091 at 2594. A collapse before 3000 is likely; "
                               "then about the 2500-2700 checkpoint is evaluated.")
    exp["decision"] = {"mode": "final_submission_training",
                       "adoption": "Read the 69-case formula score and protection checks before submitting; no automatic submission."}
    files[arm + "experiment.json"] = (json.dumps(exp, ensure_ascii=False, indent=2) + "\n").encode()

    text = readme(ed)
    files["README.txt"] = files[arm + "README.txt"] = text.encode()
    files["points.txt"] = f"{key} {ed['slug']} {ed['result']}\n".encode()
    files["point_config.env"] = (f"POINT_WORK_ID={WORK_ID}\nPOINT_STATUS_DIR_NAME={ed['slug']}\n"
                                 f"POINT_WORK_DIR=/workspace/{ed['slug']}_work\nPOINT_TMUX_NAME={ed['slug']}\n").encode()
    files["run_all.sh"] = once(files["run_all.sh"].decode(), f"--inner {v3.KEY}", f"--inner {key}", "run_all key").encode()
    files[RUNNER] = patch_eval_retry(files[RUNNER].decode()).encode()

    work = {n[7:]: b for n, b in files.items() if n.startswith("shared/")}
    work.update({n[len(arm):]: b for n, b in files.items() if n.startswith(arm)})
    files[arm + "PACKAGE_SHA256SUMS.txt"] = "".join(f"{sha(b)}  {n}\n" for n, b in sorted(work.items())).encode()
    files["SHA256SUMS.txt"] = "".join(f"{sha(b)}  {n}\n" for n, b in sorted(files.items())).encode()
    base = {(arm + n[len(src_arm):] if n.startswith(src_arm) else n): b for n, b in base.items()}
    return files, base


def validate(edition: str, files: dict[str, bytes], base: dict[str, bytes]) -> None:
    ed = EDITIONS[edition]
    arm = f"runs/{ed['key']}/"
    deployed = tuple(n.replace(v3.ARM, arm) for n in v3.DEPLOYED if not n.endswith("candidate/quadruped_rewards.py"))
    for name in deployed:
        assert files[name] == base[name], f"deployed file changed: {name}"
    changed = sorted(n for n in files if files.get(n) != base.get(n))
    allowed = {RUNNER, "README.txt", "SHA256SUMS.txt", "points.txt", "point_config.env", "run_all.sh"} | {
        arm + n for n in ("run_config.env", "experiment.json", "README.txt", "PACKAGE_SHA256SUMS.txt",
                          "expected_rewards.json", "candidate/quadruped_rewards.py")} | {"shared/" + h for h in v3.HELPERS}
    assert set(changed) <= allowed, set(changed) - allowed
    assert "root_report.html" not in files and not any(v3.ARM in n for n in files)
    cand = reward_dict(files[arm + "candidate/quadruped_rewards.py"].decode())
    assert cand == ed["rewards"] == json.loads(files[arm + "expected_rewards.json"])["candidate"]
    cfg = files[arm + "run_config.env"].decode()
    for line in (f"WORK_ID={WORK_ID}", f"MAX_ITERATIONS={MAX_ITERATIONS}", f"EVAL_CHECKPOINT_ITER={EVAL_ITER}",
                 "MAX_RECOVERIES=0", "TRAIN_SEED=42", "NUM_ENVS=4096", f"KEEP_DIR_NAME={ed['slug']}",
                 f"RESULT_ZIP_NAME={ed['result']}", f"TMUX_NAME={ed['slug']}"):
        assert "\n" + line + "\n" in "\n" + cfg, line
    runner = files[RUNNER].decode()
    assert runner.count("[RETRY] eval") == 1 and runner.count("[RETRY] video") == 1
    assert files["points.txt"].decode() == f"{ed['key']} {ed['slug']} {ed['result']}\n"
    assert f"--inner {ed['key']}" in files["run_all.sh"].decode()
    for name, data in files.items():
        if name.endswith((".sh", ".env", ".py")) and "stored_evaluation" not in name:
            assert b"\r" not in data, name
    with tempfile.TemporaryDirectory() as tmp:
        for name, data in files.items():
            if name.endswith(".sh"):
                script = Path(tmp) / Path(name).name
                script.write_bytes(data)
                subprocess.run([BASH, "-n", str(script)], check=True)
    for line in files["SHA256SUMS.txt"].decode().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(files[name]) == digest, name
    work = {n[7:]: b for n, b in files.items() if n.startswith("shared/")}
    work.update({n[len(arm):]: b for n, b in files.items() if n.startswith(arm)})
    for line in work["PACKAGE_SHA256SUMS.txt"].decode().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(work[name]) == digest, name


def zip_bytes(edition: str, files: dict[str, bytes]) -> bytes:
    import io
    slug = EDITIONS[edition]["slug"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(slug + "/" + name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_STORED if name.endswith((".pt", ".mp4")) else zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            archive.writestr(info, data)
    data = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
        assert {n[len(slug) + 1:]: archive.read(n) for n in archive.namelist()} == files
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    for edition, ed in EDITIONS.items():
        files, base = build(edition)
        validate(edition, files, base)
        data = zip_bytes(edition, files)
        digest = sha(data)
        if args.publish:
            OUT.mkdir(parents=True, exist_ok=True)
            target = OUT / (ed["release"] + ".zip")
            assert not target.exists(), f"issued release is immutable: {target}"
            target.write_bytes(data)
            target.with_suffix(".zip.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8", newline="\n")
        print(f"edition={edition} release={ed['release']} files={len(files)} bytes={len(data)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
