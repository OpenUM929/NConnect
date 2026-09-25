"""Build (and optionally publish) a staged Go2 candidate package from an experiment spec.

Used by the basic-motion plan (G-D-BASIC-MOTION-20260915): G-A031 and G-A032, a
feet_air_time dose pair on A017.  Same measurement path as G-A030 (나′): the
deployed training code and the evaluator ship byte for byte, and only
candidate/quadruped_rewards.py is rendered (R-6).

The runner is server_run_go2_candidate_staged.sh, a copy of G-A030's runner that
adds a short target stage (training + the plan's target cases + relevant videos)
and a full stage run only after a target-stage pass.  G-A030 keeps its own
runner and builder so its published ZIP stays reproducible.
Plan: workspace/training/quadruped/upload/plan/GO2_BASIC_MOTION_TUNING_PLAN_20260915.md.

    python tools/build_go2_candidate_package.py G-A031            # build and verify
    python tools/build_go2_candidate_package.py G-A031 --publish  # also publish upload/G-A031
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_g_a030_package as a030  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

EXPERIMENTS = GO2 / "config" / "experiments"
SPECS = {
    "G-A031": EXPERIMENTS / "G_A031_a017_feet_air_time_001.json",
    "G-A032": EXPERIMENTS / "G_A032_a017_feet_air_time_010.json",
    "G-A033": EXPERIMENTS / "G_A033_a017_track_lin_vel_xy_150.json",
}
EXTREF = GO2 / "config" / "go2_external_reference.json"
RUNNER = "server_run_go2_candidate_staged.sh"
# G-A033 v2 on: the candidate is evaluated at the baseline's checkpoint iteration
# (evaluation.checkpoint_iter), not at finalize's reward pick (plan
# GO2_FALL_POSTURE_CANDIDATES_20260915.md section 5).  G-A031/G-A032 keep RUNNER.
PINNED_RUNNER = "server_run_go2_candidate_iter_pinned.sh"
RUNNERS = (RUNNER, PINNED_RUNNER)
# A017's evaluated model_best.pt is the iter-900 checkpoint (the "iter" key inside the file).
BASELINE_CHECKPOINT_ITER = {"A017": 900}
SUITE_RUNNER = a030.RUNNER
# A release that ran on the server keeps the runner bytes it ran with, so its published ZIP
# stays reproducible after a runner fix.  (work_id, arm release_id) -> copy under RUNNER_HISTORY,
# named <runner stem>.<first 16 hex of its sha256>.sh.
RUNNER_HISTORY = GO2 / "runner_history"
EXECUTED_RUNNERS = {
    ("G-A031", "20260915_a017_feet_air_time_001_candidate_staged_v2"):
        "server_run_go2_candidate_staged.5ce14f1cdc1da54e.sh",
    ("G-A032", "20260915_a017_feet_air_time_010_candidate_staged_v2"):
        "server_run_go2_candidate_staged.5ce14f1cdc1da54e.sh",
    ("G-A033", "20260915_a017_track_lin_vel_xy_150_iter900_staged_v2"):
        "server_run_go2_candidate_iter_pinned.47a5c5c6840e2331.sh",
    ("G-A038", "20260917_a033_ang_vel_xy_m008_staged_v1"):
        "server_run_go2_candidate_iter_pinned.47a5c5c6840e2331.sh",
    ("G-A041", "20260920_a033_ang_vel_xy_m004_staged_v3"):
        "server_run_go2_candidate_iter_pinned.1cd87f425d5b89f5.sh",
    # Pinned 2026-09-22 with defect C-14.  Both arms ran on the server with this
    # copy; the fix for C-14 changes the working tree, so without the pin their
    # published ZIPs would stop rebuilding (that is exactly how C-2 arose for
    # G-A035/G-A037/G-A039, which still embed 1cd87f425d5b89f5).
    ("G-A042", "20260921_a033_track_lin_vel_xy_160_staged_v4"):
        "server_run_go2_candidate_iter_pinned.6fd78eeb8eac5342.sh",
    ("G-A043", "20260922_a033_lin_vel_z_m15_staged_v3"):
        "server_run_go2_candidate_iter_pinned.6fd78eeb8eac5342.sh",
    # Pinned 2026-09-24 with defects C-27/C-28.  G-A044 ran on the server with this copy
    # (its published v9 carries these bytes); the interrupted-training guard and the
    # completion check changed the working tree, so without the pin its ZIP would stop
    # rebuilding.  The round is finished - the fix travels to the next round, not this one.
    ("G-A044", "20260922_a033_lin_vel_z_m175_full69_v9"):
        "server_run_go2_candidate_iter_pinned.3e4dd15257f2b2af.sh",
}
FIXED_TIMESTAMP = (2026, 9, 15, 0, 0, 0)
PUBLISHED_AT = "2026-09-15T00:00:00+00:00"
ENTRY = a030.ENTRY


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(work_id: str) -> dict:
    return json.loads(SPECS[work_id].read_text(encoding="utf-8"))


def prefix(spec: dict) -> Path:
    return Path("go2_" + spec["work_id"].lower().replace("-", "_"))


def upload_dir(spec: dict) -> Path:
    return GO2 / "upload" / spec["work_id"]


def output_path(spec: dict) -> Path:
    out = spec["output"]
    return upload_dir(spec) / "history" / out["release_id"] / out["upload_zip"]


def guide_name(spec: dict) -> str:
    return "GO2_%s_RUN_GUIDE.txt" % spec["work_id"].replace("-", "_")


def targets(spec: dict) -> list[str]:
    return [entry for entries in spec["preregistered"]["target_groups"].values() for entry in entries]


# 2026-09-22 이전에 발행된 회차의 ZIP 이름 — 판 번호가 없다(결함 C-18, validate_spec 참조).
LEGACY_UNVERSIONED_ZIPS = frozenset({
    "GO2_G_A031_feet_air_time_001_staged.zip",
    "GO2_G_A032_feet_air_time_010_staged.zip",
    "GO2_G_A033_track_lin_vel_xy_150_iter900_staged.zip",
    "GO2_G_A035_a033_iter1500_staged.zip",
    "GO2_G_A037_a033_lin_vel_z_m1_staged.zip",
    "GO2_G_A038_a033_ang_vel_xy_m008_staged.zip",
    "GO2_G_A039_a033_dof_acc_m125e7_staged.zip",
    "GO2_G_A040_a033_flat_orientation_m05_staged.zip",
    "GO2_G_A041_a033_ang_vel_xy_m004_staged.zip",
    "GO2_G_A042_a033_track_lin_vel_xy_160_staged.zip",
    "GO2_G_A043_a033_lin_vel_z_m15_staged.zip",
})


def check_release_version_in_zip_name(output: dict, need) -> None:
    """2026-09-22 사용자 결정 (결함 C-18) — 올릴 파일의 이름이 판을 말하게 한다.

    release_id 는 판마다 `_v<N>` 이 붙는데 ZIP 이름에는 붙지 않아, history 에 **같은 이름의 ZIP 이
    여러 개** 쌓였다.  A044 는 넷이고 그중 v3 는 올리면 아무것도 돌지 않는 판이다(결함 C-14).  그
    상태에서 올릴 파일을 고르는 근거는 SHA 한 줄뿐이었고, 그것은 사람이 손으로 대조해야 하는
    근거다.  이름에 판이 들어가면 대조 없이도 틀린 파일을 집을 수 없다.

    LEGACY 는 이 규칙 이전에 발행된 회차다.  발행물은 바이트도 이름도 고치지 않으므로 그대로
    두고, 새 사양은 규칙을 지켜야 하므로 이 집합은 자라지 않는다.
    """
    if output["upload_zip"] in LEGACY_UNVERSIONED_ZIPS:
        return
    version = output["release_id"].rsplit("_", 1)[-1]
    need(bool(re.fullmatch(r"v\d+", version)),
         f"release_id must end with _v<N>: {output['release_id']}")
    need(output["upload_zip"].endswith(f"_{version}.zip"),
         f"upload_zip must carry the release version {version}: {output['upload_zip']}")


def validate_spec(spec: dict) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"spec {spec.get('work_id')}: {message}")

    need(spec.get("work_id") in SPECS, f"work_id must be one of {sorted(SPECS)}")
    need(spec.get("runner") in RUNNERS, f"runner must be one of {RUNNERS}")
    pinned = spec["evaluation"].get("checkpoint_iter")
    if spec["runner"] == PINNED_RUNNER:
        need(pinned == BASELINE_CHECKPOINT_ITER.get(spec["baseline"]["name"]),
             "evaluation.checkpoint_iter must be the baseline's evaluated checkpoint iteration")
    else:
        need(pinned is None, "evaluation.checkpoint_iter needs the pinned runner")
    # The baseline and its ruler are G-A030's: same frozen A017, same stored G-A027 arm.
    need(spec["baseline"] == a030.load_spec()["baseline"], "baseline block must equal G-A030's")
    base, cand = spec["rewards"]["baseline"], spec["rewards"]["candidate"]
    need(tuple(base) == REWARD_NAMES and tuple(cand) == REWARD_NAMES, f"reward keys/order must be {REWARD_NAMES}")
    single = spec["single_change"]
    changed = [name for name in REWARD_NAMES if float(base[name]) != float(cand[name])]
    need(changed == [single["name"]], f"candidate must change exactly {single['name']}, got {changed}")
    need(float(single["from"]) == float(base[single["name"]]) and float(single["to"]) == float(cand[single["name"]]),
         "single_change does not match the rewards")
    need(spec["training"] == {"from_scratch": True, "seed": 42, "num_envs": 4096, "max_iterations": 1000},
         "training must be from scratch, seed 42, 4096 envs, 1000 iter")
    history = a030.MASTER.read_text(encoding="utf-8").split("## 1-a.", 1)[1].split("\n## ", 1)[0]
    need(bool(spec.get("dial_history_ref")) and spec["dial_history_ref"] in history,
         "dial_history_ref must quote a row of GO2_REWARD_EVIDENCE_MASTER.md section 1-a")

    # G-D-EXTREF-20260915: the external comparison must agree with the reference JSON.
    ext, ref = spec.get("external_reference") or {}, json.loads(EXTREF.read_text(encoding="utf-8"))
    rewards = ref["isaaclab"]["rewards"]
    term = single["name"]
    need(ext.get("term") == term, "external_reference.term must be the changed term")
    for key, value in (("isaaclab_base", rewards["base"][term]), ("isaaclab_go2_rough", rewards["go2_rough"][term]),
                       ("isaaclab_go2_flat", rewards["go2_flat"][term]),
                       ("deployed_start", ref["deployed_start"]["rewards"].get(term, rewards["go2_rough"][term])),
                       ("baseline", base[term]), ("candidate", cand[term])):
        need(ext.get(key) is not None and float(ext[key]) == float(value), f"external_reference.{key} must be {value}")

    evaluation = spec["evaluation"]
    need(evaluation["seeds"] == [101, 202, 303] and evaluation["case_count"] == 69, "69 cases over 101/202/303")
    need(evaluation["num_envs"] == 32 and evaluation["steps"] == 1000, "evaluation must be 32 envs x 1000 steps")
    target = targets(spec)
    need(len(spec["preregistered"]["target_groups"]) == 3 and len(target) == 9 and len(set(target)) == 9,
         "three target groups of three distinct cases")
    need(evaluation["catastrophe_case"] not in target, "the catastrophe case must not be a target case")
    videos = spec["videos"]
    for entry in [evaluation["catastrophe_case"], *evaluation["sentinel_cases"], *target,
                  *videos["candidate"], *videos["baseline"]]:
        need(bool(ENTRY.match(entry)), f"bad case entry {entry!r}")
    need(videos["num_envs"] == 4 and videos["steps"] == 500, "videos are 4 envs x 500 steps")
    # Relevant videos only (user request 2026-09-15): a short list, each with its reason.
    need(1 <= len(videos["candidate"]) <= 6 and len(videos["baseline"]) <= 2, "at most 6 candidate and 2 baseline videos")
    need(set(videos.get("reasons", {})) == set(videos["candidate"]), "every candidate video needs a reason")
    stored = ROOT / spec["baseline"]["stored_arm"] / "evaluation" / spec["baseline"]["label"] / "videos"
    if stored.is_dir():
        for entry in videos["candidate"]:
            scenario, case_id, seed = entry.split(":")
            need((stored / f"{scenario}_{case_id}_seed_{seed}.mp4").is_file() or entry in videos["baseline"],
                 f"candidate video {entry} has no baseline counterpart")
    need(set(spec.get("stages", {})) == {"target", "full"}, "stages must be target and full")
    output = spec["output"]
    need(output["package_root"] == f"/workspace/{prefix(spec).as_posix()}", "package_root must match the ZIP prefix")
    need(output["tmux_name"] == prefix(spec).as_posix(), "tmux_name must be the prefix")
    need(bool(re.fullmatch(r"\[DONE\] [A-Z0-9_]{3,100}", output["done_marker"])), "bad done_marker")
    need(bool(re.fullmatch(r"GO2_G_A\d{3}_[a-z0-9_]+\.zip", output["upload_zip"])), "bad upload_zip")
    check_release_version_in_zip_name(output, need)


def rendered_rewards(spec: dict) -> tuple[str, str]:
    template = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
    candidate = render_reward_source(template, spec["rewards"]["candidate"])
    reference = render_reward_source(template, spec["rewards"]["baseline"])
    differing = [(a, b) for a, b in zip(reference.splitlines(), candidate.splitlines()) if a != b]
    name = spec["single_change"]["name"]
    if len(reference.splitlines()) != len(candidate.splitlines()) or len(differing) != 1 \
            or f'"{name}"' not in differing[0][1]:
        raise RuntimeError(f"rendered reward files must differ in the {name} line only: {differing}")
    if reward_dict(candidate) != spec["rewards"]["candidate"] or reward_dict(reference) != spec["rewards"]["baseline"]:
        raise RuntimeError("rendered reward files do not read back as the spec")
    return candidate, reference


def run_config(spec: dict) -> str:
    text = a030.run_config(spec)
    text = text.replace(f"# generated by tools/build_go2_g_a030_package.py from {a030.SPEC.name}; do not edit",
                        f"# generated by tools/build_go2_candidate_package.py from {SPECS[spec['work_id']].name}; do not edit")
    text += "TARGET_CASES=(" + " ".join(shlex.quote(item) for item in targets(spec)) + ")\n"
    if spec["runner"] == PINNED_RUNNER:
        text += f"EVAL_CHECKPOINT_ITER={int(spec['evaluation']['checkpoint_iter'])}\n"
    return text


def video_log_dir_faults(runner: str) -> list[str]:
    """Every function that tees into $KEEP/logs/$label/ must create that directory first.

    G-A038 (2026-09-17): run_video wrote the <baseline>_videos log with no mkdir; tee failed,
    pipefail ended the run after every measurement was done, and nothing was adjudicable.
    """
    faults = []
    for match in re.finditer(r"^(\w+)\(\) \{\n(.*?)^\}\n", runner, re.M | re.S):
        name, body = match.group(1), match.group(2)
        tee = body.find('tee "$KEEP/logs/$label/')
        if tee < 0:
            continue
        made = [m.start() for m in re.finditer(r'^\s*mkdir -p [^\n]*"\$KEEP/logs/\$label"', body, re.M)]
        if not any(start < tee for start in made):
            faults.append(f"{name} tees into $KEEP/logs/$label without creating it")
    return faults


def runner_bytes(spec: dict) -> bytes:
    """The arm runner: the executed copy for a release that ran, the working tree otherwise."""
    key = (spec["work_id"], spec["output"]["release_id"])
    if key in EXECUTED_RUNNERS:
        path = RUNNER_HISTORY / EXECUTED_RUNNERS[key]
        runner = path.read_bytes()
        if path.name.rsplit(".", 2)[1] != sha(runner)[:16] or not path.name.startswith(Path(spec["runner"]).stem + "."):
            raise RuntimeError(f"{path.name} is not the executed {spec['runner']} it names")
    else:
        runner = (GO2 / spec["runner"]).read_bytes()
        faults = video_log_dir_faults(runner.decode("utf-8"))
        if faults:
            raise RuntimeError(f"{spec['runner']}: {faults}")
    if b"\r" in runner:
        raise RuntimeError("runner has CR bytes")
    return runner


def build_payload(spec: dict) -> dict[str, bytes]:
    validate_spec(spec)
    base = spec["baseline"]
    model = (a030.A017_SOURCE / "model_best.pt").read_bytes()
    env = (a030.A017_SOURCE / "env.yaml").read_bytes()
    if sha(model) != base["model_sha256"] or sha(env) != base["env_sha256"]:
        raise RuntimeError("A017 model/env on disk do not match the frozen SHA")
    trained = a030.A017_SOURCE / "source" / "quadruped_rewards.py"
    if trained.is_file() and reward_dict(trained.read_text(encoding="utf-8")) != spec["rewards"]["baseline"]:
        raise RuntimeError("spec baseline rewards differ from the rewards A017 was trained with")
    evaluator = (GO2 / "go2_eval_telemetry.py").read_bytes()
    registry = a030.REGISTRY.read_bytes()
    if sha(evaluator) != base["evaluator_sha256"] or sha(registry) != base["registry_sha256"]:
        raise RuntimeError("working-tree evaluator/registry differ from the ruler of the stored baseline arm")
    runner = runner_bytes(spec)
    ours = a030.REPORT_BLOCK.search(runner.decode("utf-8"))
    theirs = a030.REPORT_BLOCK.search((GO2 / a030.ENGINE_RUNNER).read_text(encoding="utf-8"))
    if not ours or not theirs or ours.group(0) != theirs.group(0):
        raise RuntimeError("runner report-recovery block must equal the engine's")

    candidate_rewards, reference_rewards = rendered_rewards(spec)
    payload: dict[str, bytes] = {}
    for role in ("candidate", "baseline"):
        for path in a030.source_files():
            payload[f"{role}/{path.relative_to(GO2).as_posix()}"] = path.read_bytes()
    payload["candidate/quadruped_rewards.py"] = candidate_rewards.encode("utf-8")
    payload["reference/baseline_quadruped_rewards.py"] = reference_rewards.encode("utf-8")
    payload["baseline/exported/model_best.pt"] = model
    payload["baseline/exported/env.yaml"] = env
    payload["go2_self_eval_registry.json"] = registry
    for name in a030.HELPERS:
        payload[name] = (GO2 / name).read_bytes()
    payload[spec["runner"]] = runner
    payload["run_config.env"] = run_config(spec).encode("utf-8")
    payload["experiment.json"] = SPECS[spec["work_id"]].read_bytes()
    payload["expected_rewards.json"] = (json.dumps(spec["rewards"], indent=2) + "\n").encode("utf-8")
    payload["README.txt"] = readme(spec).encode("utf-8")
    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def readme(spec: dict) -> str:
    single, prereg, out = spec["single_change"], spec["preregistered"], spec["output"]
    title = f"GO2 {spec['work_id']} STAGED CANDIDATE — A017 + {single['name']} {single['from']} -> {single['to']}"
    why = "\n".join("  " + line for line in spec["why"])
    root = out["package_root"]
    videos = "\n".join(f"  {entry:24s} {spec['videos']['reasons'][entry]}" for entry in spec["videos"]["candidate"])
    pair = spec.get("pair")
    pairing = (f"It is one arm of a dose pair ({spec['work_id']} {single['to']}, {pair['other_work_id']} "
               f"{pair['other_value']}).\n" if pair else "")
    pinned = spec["evaluation"].get("checkpoint_iter")
    pinning = (f"The candidate is evaluated at the iter-{pinned} checkpoint, the iteration the baseline was\n"
               f"evaluated at, not at finalize's reward pick; training/CHECKPOINT_PIN.txt records both.\n"
               if spec["runner"] == PINNED_RUNNER else "")
    return f"""{title}
{'=' * len(title)}

This package TRAINS one policy and then measures it.  status: exploratory.
{pairing}{pinning}
WHAT CHANGES
  The baseline is A017 (Pilot-01 + track_lin_vel_xy_exp 1.4), 39.76/70 on the
  69-case internal proxy (G-A027).  The candidate changes one reward only:
  {single['name']} {single['from']} -> {single['to']}.  Deployed train/play/task code is unchanged
  (R-6); only candidate/quadruped_rewards.py carries the new value.

WHY (plan {Path(spec['plan']).name})
{why}

STAGES (run the target stage first)
  target (default, ~1h25m): training, catastrophe gate, the 9 target cases,
     {len(spec['evaluation']['sentinel_cases'])} sentinel cases, {len(spec['videos']['candidate'])} videos, result ZIP.  Criterion 1 is decided
     on the target cases alone, so a target-stage FAIL is final for this arm.
  full (~55m more, only after the local verifier says TARGET_PASS_FULL_STAGE_REQUIRED):
     the other cases of the 69, the target stage kept, result ZIP again; criteria 2-4.

RUN
  unzip {out['upload_zip']} -d /workspace
  PACKAGE_ROOT={root} bash {root}/{spec['runner']}
  GO2_STAGE=full GO2_RESUME=1 PACKAGE_ROOT={root} bash {root}/{spec['runner']}
  Finish marker (both stages): {out['done_marker']}; RUNNER_STATUS.txt carries STAGE and DECISION.

VIDEOS (relevant cases only; the A017 counterparts are in the G-A027 harvest)
{videos}

DOWNLOAD
  /workspace/_keep/{out['result_zip']}
  /workspace/_keep/{out['result_zip']}.sha256

PRE-REGISTERED READING (plan section 6-1, fixed before the run)
  success needs all of:
   1 basic motion off flat ground: the mean case proxy (survival x tracking) over
     rough_forward, slope_plus_20 and the three DR cases (9 case-seeds) rises by
     >= {prereg['min_target_mean_proxy_delta']}, and at least {prereg['min_target_groups_improved']} of the 3 groups improve   [target stage]
   2 total internal proxy delta >= {prereg['min_total_points_delta']}/70, same evaluator                 [full stage]
   3 flat ground holds: G1/G2 scenario proxy drop <= {prereg['max_flat_scenario_proxy_drop']}, no G1/G2 case loses
     more than {prereg['max_flat_case_survival_drop']} survival; no other scenario loses more than
     {prereg['max_scenario_weighted_loss_70']}/70 weighted                                         [full stage]
   4 POLICY_LOCOMOTES and no new stationary case outside the stairs (G5)   [full stage]
   5 videos show normal four-legged walking with the feet lifted (human reading)
  Height and posture-gate falls on the target cases are read as the mechanism,
  not as a criterion.  The expected weighted gain is NOT estimated.
  Official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def build(spec: dict) -> Path:
    payload = build_payload(spec)
    output, root = output_path(spec), prefix(spec)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo((root / name).as_posix(), date_time=FIXED_TIMESTAMP)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        names = archive.namelist()
        if len(names) != len(payload):
            raise RuntimeError("member count mismatch")
        if any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise RuntimeError("unsafe member")
    built = temporary.read_bytes()
    temporary.unlink()
    if output.exists() and output.read_bytes() != built:
        raise RuntimeError(f"immutable release conflict: {output} differs from this build")
    output.write_bytes(built)
    output.with_suffix(".zip.sha256").write_text(f"{sha(built)}  {output.name}\n", encoding="utf-8", newline="\n")
    return output


def run_guide(spec: dict, digest: str) -> str:
    out, single, pair = spec["output"], spec["single_change"], spec["pair"]
    keep = f"workspace/_keep/{out['keep_dir_name']}"
    zip_name, root = out["upload_zip"], out["package_root"]
    other = pair["other_work_id"]
    other_root = "/workspace/go2_" + other.lower().replace("-", "_")
    videos = "\n".join(f"- {entry}: {spec['videos']['reasons'][entry]}" for entry in spec["videos"]["candidate"])
    return f"""GO2 {spec['work_id']} SERVER RUN GUIDE (staged candidate v2, posture_gate_v2, 학습 1회)

회차 {spec['work_id']}: A017 + `{single['name']}` {single['from']}→{single['to']} 단일변수, seed 42, 1,000 iter.
짝 실험: {other} (`{single['name']}` {pair['other_value']}). 두 회차는 서로 독립이고 순서는 상관없다.
계획서: {spec['plan']}
이 판(v2)은 {out['supersedes']}을 대체한다. 달라진 점은 두 가지다. 짧은 1단계로 먼저 판정하고, 영상은 관련 {len(spec['videos']['candidate'])}개만 뽑는다.
서버 실행은 사용자 결정 사항이다. 이 문서는 실행 절차이지 실행 승인이 아니다.

LOCAL FILE TO UPLOAD (이 회차는 딱 하나)
1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{spec['work_id']}\\current\\{zip_name}
   SHA256 {digest}

SERVER DESTINATION
/workspace/{zip_name}

단계와 시간 (한 GPU에서 두 회차를 동시에 돌리지 않는다. 러너가 거부한다)
1단계 target(기본): 학습 1,000 iter → 파국 게이트 → 표적 9 case → A017 표지 {len(spec['evaluation']['sentinel_cases'])} case → 영상 {len(spec['videos']['candidate'])}개 → 결과 ZIP.
  약 1시간 25분(여유 포함 1시간 40분). 판정 1항은 이 9 case만으로 정해지므로 1단계 FAIL은 이 회차의 최종 판정이다.
2단계 full(1단계 통과 회차만): 나머지 59 case → 결과 ZIP 다시. 판정 2~4항. 약 55분.
두 회차 1단계만: 약 2시간 50분. 두 회차 모두 통과하면 2단계 두 번이 더해져 약 4시간 40분.
접속 직후 잔여 GPU 시간을 실측해 기록한다.

1단계 ONE-LINE RUN (tmux 안에서 시작하고 즉시 리턴)
cd /workspace && echo '{digest}  {zip_name}' | sha256sum -c - && unzip -oq {zip_name} && PACKAGE_ROOT={root} bash {root}/{RUNNER}

짝 실험 1단계를 이어서 (선택)
두 ZIP을 모두 풀어 둔 뒤, 첫 회차 1단계를 시작하고 아래 줄로 대기열을 건다. 첫 회차의 tmux가 끝나면 다음 회차 1단계가 시작된다.
tmux new-session -d -s go2_basic_chain "while tmux has-session -t {out['tmux_name']} 2>/dev/null; do sleep 60; done; PACKAGE_ROOT={other_root} bash {other_root}/{RUNNER}"

1단계 결과를 받은 뒤 (로컬, GPU 0)
python -B tools/verify_go2_basic_motion_harvest.py {spec['work_id']} --harvest {keep} --out {keep}/harvest_verification.json
- FAIL: 이 회차는 끝이다. 2단계를 돌리지 않는다.
- TARGET_PASS_FULL_STAGE_REQUIRED: 2단계를 돌린다.
- BASELINE_REMEASURE_REQUIRED: 표지 case가 저장값과 어긋났다. 1단계를 `GO2_RESUME=1 GO2_REMEASURE_BASELINE=1 PACKAGE_ROOT={root} bash {root}/{RUNNER}`로 다시 돌린다(A017 10 case, +약 8분). 2단계에서도 같은 변수를 준다.
- INCONCLUSIVE: 결측만 보완한다. 점수를 읽지 않는다.

2단계 실행 (1단계 결과 폴더가 서버에 남아 있어야 한다)
GO2_STAGE=full GO2_RESUME=1 PACKAGE_ROOT={root} bash {root}/{RUNNER}
학습·1단계 case·영상은 지문으로 건너뛰고 나머지만 잰다. 결과 ZIP이 다시 만들어진다. 같은 검증기로 다시 판정한다.

MONITOR
tmux attach -t {out['tmux_name']}

첫 10분에 볼 것
학습 로그의 reward 표에 `{single['name']}` 가중치 {single['to']}이 찍히는지 본다.

학습 직후에 볼 것
`[PHASE 2/6]` 뒤 `ENV_REWARDS_OK role=candidate ... {single['name']}={single['to']}` 줄과 `LOCOMOTION MOVING` 줄.
정지면 파국 게이트가 평가를 건너뛴다. 이것도 결과다(계획 §6-3).

영상 (관련 {len(spec['videos']['candidate'])}개만, 4 env·500 step. A017 대응 영상은 G-A027 회수본에 이미 있다)
{videos}

RESUME / RERUN 규칙
기본 재실행은 이전 결과를 지우지 않고 거부한다. 이어가려면 `GO2_RESUME=1`, 버리려면 `GO2_DISCARD_PREVIOUS=1`.

DONE MARKER (두 단계 공통)
{out['done_marker']}
RUNNER_STATUS.txt의 STAGE(target/full)와 DECISION(TARGET_STAGE_COMPLETE/SUITE_COMPLETE)으로 구분한다.

DOWNLOAD TO LOCAL workspace\\_keep
/workspace/_keep/{out['result_zip']}
/workspace/_keep/{out['result_zip']}.sha256
패키징이 실패할 수 있으니 `_keep/{out['keep_dir_name']}` 원시 파일도 함께 가져온다.

SERVER SHUTDOWN GATE
DONE 표시만으로 종료하지 않는다. 결과를 받아 로컬 검증을 통과해야 종료 판단을 보고한다.
2단계가 남은 회차가 있으면 `_keep/{out['keep_dir_name']}`을 지우지 않는다.

RESULT INTERPRETATION — 실행 전에 고정 (계획서 §6, 사후 재협상 금지)
성공은 다음을 모두 충족할 때다.
- [1단계] 험지 전진·20° 오르막·DR 9 case-seed의 case proxy(생존×추종) 평균이 +0.05 이상 오르고, 세 묶음 중 둘 이상이 오른다.
- [2단계] 총 proxy가 떨어지지 않는다(Δ ≥ 0/70).
- [2단계] 평지(G1·G2) 시나리오 proxy 하락 ≤ .02, 평지 case 생존 하락 ≤ 1/32. 나머지 시나리오 가중 손실 ≤ 0.5/70.
- [2단계] POLICY_LOCOMOTES이고 계단(G5) 밖 시나리오에 새 정지 case가 없다.
- 영상에서 발을 들고 걷는 정상 네발 보행이 보인다.
높이·자세 게이트 낙상은 기전 판독용이지 판정 조건이 아니다.
두 회차의 결과를 합친 방향 판정은 계획서 §6-3 표를 따른다.
공식 evaluator·공식 점수는 OFFICIAL_RESULT_UNMEASURED다.
"""


def publish(spec: dict, zip_path: Path) -> None:
    digest = sha(zip_path.read_bytes())
    out, single = spec["output"], spec["single_change"]
    upload = upload_dir(spec)
    history, current = upload / "history" / out["release_id"], upload / "current"
    current.mkdir(parents=True, exist_ok=True)
    guide = guide_name(spec)
    note = (f"A017 + {single['name']} {single['from']}->{single['to']}, staged: target stage (training + 9 target cases "
            f"+ {len(spec['videos']['candidate'])} videos) then full stage; dose pair with {spec['pair']['other_work_id']}. "
            f"Supersedes {out['supersedes']}. exploratory.")
    manifest = {
        "experiment_id": spec["work_id"],
        "note": note,
        "published_at_utc": PUBLISHED_AT,
        "release_id": out["release_id"],
        "status": "ARTIFACT_VERIFIED",
        "support_files": [guide],
        "upload_files": [{"name": out["upload_zip"], "server_path": f"/workspace/{out['upload_zip']}", "sha256": digest}],
    }
    current_text = (
        f"CURRENT GO2 UPLOAD — {spec['work_id']}\n\n"
        "UPLOAD ONLY THIS ONE FILE\n"
        f"1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{spec['work_id']}\\current\\{out['upload_zip']}\n"
        f"   SHA256 {digest}\n\n"
        f"이 패키지는 A017 + {single['name']} {single['to']}을 1,000 iter 학습하고, 1단계에서 표적 9 case만 잰다.\n"
        f"1단계를 통과한 회차만 2단계(나머지 59 case)를 돌린다. 절차는 같은 폴더의 {guide}. 서버 실행은 사용자 결정 사항이다.\n\n"
        f"RELEASE_ID {out['release_id']}\nSTATUS ARTIFACT_VERIFIED\n"
        "History is preserved under ../history and in ../UPLOAD_HISTORY.tsv.\n"
    )
    files = {
        guide: run_guide(spec, digest).encode("utf-8"),
        "UPLOAD_MANIFEST.json": (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "CURRENT_UPLOAD.txt": current_text.encode("utf-8"),
    }
    for name, data in files.items():
        target = history / name
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError(f"immutable release conflict: {target}")
        target.write_bytes(data)
    (history / f"{guide}.sha256").write_text(f"{sha(files[guide])}  {guide}\n", encoding="utf-8", newline="\n")
    published = [zip_path, zip_path.with_suffix(".zip.sha256"), *(history / name for name in files),
                 history / f"{guide}.sha256"]
    # current/ holds one release.  A superseded file leaves it only when a
    # byte-identical copy is preserved under history/.
    names = {path.name for path in published}
    for stale in sorted(current.iterdir()):
        if stale.name in names:
            continue
        data = stale.read_bytes()
        if not any(copy.read_bytes() == data for copy in (upload / "history").rglob(stale.name)):
            raise RuntimeError(f"{stale} is not preserved under history/; refusing to remove it")
        stale.unlink()
    for source in published:
        (current / source.name).write_bytes(source.read_bytes())
    ledger = upload / "UPLOAD_HISTORY.tsv"
    header = "published_at_utc\texperiment_id\trelease_id\tstatus\tengine_file\tengine_sha256\tspec_file\tspec_sha256\tnote\n"
    row = "\t".join([PUBLISHED_AT, spec["work_id"], out["release_id"], "ARTIFACT_VERIFIED", out["upload_zip"], digest,
                     SPECS[spec["work_id"]].name, sha(SPECS[spec["work_id"]].read_bytes()), note]) + "\n"
    existing = ledger.read_text(encoding="utf-8") if ledger.exists() else header
    if row not in existing:
        ledger.write_text(existing + row, encoding="utf-8", newline="\n")
    print(f"published current={current}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_id", choices=sorted(SPECS))
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    spec = load(args.work_id)
    path = build(spec)
    digest = sha(path.read_bytes())
    print(f"built   {path}")
    print(f"size    {path.stat().st_size / 1_048_576:.1f} MB")
    print(f"sha256  {digest}")
    if args.publish:
        publish(spec, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
