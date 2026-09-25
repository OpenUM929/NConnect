"""Build (and optionally publish) a one-file Go2 training-length package.

G-A035 is the first run that changes no reward weight at all.  It trains the
promoted baseline G-A033's exact reward file for the Isaac Lab go2_rough length
(1500 iterations instead of 1000) and measures the same 69 cases.

tools/build_go2_candidate_package.py cannot express it: that builder asserts
exactly one reward differs, a 1000-iteration training block, and G-A030's A017
baseline.  Rather than loosen a builder whose output is already released, this
module keeps its own validation and reuses everything else byte for byte --
the same runner (server_run_go2_candidate_iter_pinned.sh already reads
MAX_ITERATIONS and EVAL_CHECKPOINT_ITER from run_config.env), the same deployed
source files, the same evaluator and registry.

    python tools/build_go2_training_length_package.py G-A035            # build and verify
    python tools/build_go2_training_length_package.py G-A035 --publish  # also publish upload/G-A035
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
import build_go2_candidate_package as cand  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

EXPERIMENTS = GO2 / "config" / "experiments"
SPECS = {"G-A035": EXPERIMENTS / "G_A035_a033_iter1500.json"}
EXTREF = GO2 / "config" / "go2_external_reference.json"
RUNNER = cand.PINNED_RUNNER
# The promoted frozen baseline (G-D-BASELINE-A033-20260916).  Its training folder holds the
# model this run is compared against and the reward file it must reproduce exactly.
BASELINE_SOURCE = ROOT / "workspace" / "_keep" / "go2_g_a033_a017_track_lin_vel_xy_150" / "training"
# save_interval is 50 (go2_external_reference.json), so the last guaranteed checkpoint of a
# max_iterations=N run (learning iterations 0..N-1) is the largest multiple of 50 below N.
SAVE_INTERVAL = 50
FIXED_TIMESTAMP = (2026, 9, 16, 0, 0, 0)
PUBLISHED_AT = "2026-09-16T00:00:00+00:00"
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


# 러너 `set_case` 가 영상 한 편에 넘기는 재생 환경 중 지문에 들어가는 셋: DR_MODE · PUSH_X · PUSH_Y.
# 2026-09-22 (결함 C-13): 아래 `video_fingerprint` 는 이 셋을 "0", "", "" 로 **박아** 두고 있었다.
# 그동안 재사용한 기준선 영상이 전부 밀침도 DR 도 아니어서 드러나지 않았지만, G-A044 가 A043 이 찍은
# 밀침 ±x 기준선 영상을 재사용하려 하자 지문이 맞지 않았다.  fail-closed 라 잘못된 파일을 받아들인
# 적은 없고 **맞는 파일을 거부**하고 있었다.  값은 러너의 `set_case` 와 같아야 하며,
# `tools/test_go2_video_fingerprint_contract.py` 가 러너 원문과 이 표를 대조한다.
CASE_PLAY_ENV = {
    "push_pos_x": ("0", "0.50", ""), "push_neg_x": ("0", "-0.50", ""),
    "push_pos_y": ("0", "", "0.50"), "push_neg_y": ("0", "", "-0.50"),
}


def play_env(case_id: str) -> tuple[str, str, str]:
    """(DR_MODE, PUSH_X, PUSH_Y) — 러너 `set_case` 가 그 case 에 쓰는 값."""
    if case_id.startswith("dr_seed_"):
        return ("1", "", "")
    return CASE_PLAY_ENV.get(case_id, ("0", "", ""))


def video_fingerprint(spec: dict, entry: str) -> str:
    """The fingerprint the arm runner writes beside a rendered video (run_video, `vfingerprint`).

    2026-09-21 (G-A042): a candidate video needs a baseline counterpart at the same settings, and
    the run renders at most two.  A counterpart that already exists may be reused -- but only if it
    can be shown to BE the baseline policy under these conditions, which is what this recomputes:
    the model, env and evaluator SHAs this spec pins, the case, the seed and the video length.  A
    file whose fingerprint does not come back is a different measurement, whatever its name says.
    """
    scenario, case_id, seed = entry.split(":")
    base = spec["baseline"]
    dr, push_x, push_y = play_env(case_id)
    parts = [base["model_sha256"], base["env_sha256"], scenario, case_id, seed,
             str(int(spec["videos"]["steps"])), base["evaluator_sha256"], dr, push_x, push_y]
    return hashlib.sha256(b"".join(part.encode("utf-8") + b"\x00" for part in parts)).hexdigest()


def reuse_problems(spec: dict) -> list[str]:
    """Every declared baseline-video reuse must be on disk, unchanged, and provably the baseline."""
    problems = []
    for entry, row in (spec["videos"].get("baseline_reuse") or {}).items():
        if entry in spec["videos"]["baseline"]:
            problems.append(f"{entry} is both reused and rendered")
            continue
        if entry not in spec["videos"]["candidate"]:
            problems.append(f"{entry} is reused but not filmed on the candidate")
            continue
        path = ROOT / str(row.get("path", ""))
        if not path.is_file():
            problems.append(f"{entry} path {row.get('path')!r} is not on disk")
            continue
        if sha(path.read_bytes()) != row.get("sha256"):
            problems.append(f"{entry} sha256 changed")
        fingerprint = (path.parent / (path.stem + ".identity.sha256"))
        written = fingerprint.read_text(encoding="utf-8").strip() if fingerprint.is_file() else None
        if written != row.get("identity_sha256"):
            problems.append(f"{entry} identity file {written!r} != spec {row.get('identity_sha256')!r}")
        elif written != video_fingerprint(spec, entry):
            problems.append(f"{entry} identity does not recompute from this spec's baseline SHAs")
    return problems


# 2026-09-22 (G-A044).  A043 의 결정적 손실(G2 `combined_yaw_right`, 3 seed 전부)은 1단계 23 case
# 밖에 있었고 전수 69 를 돌린 뒤에야 보였다(결함 C-11).  계획
# `upload/plan/GO2_POST_A043_PLAN_20260922.md` §5 는 그래서 다음 회차를 **1단계 분기 없이 전수 수집**
# 으로 정했다.  그 회차는 영상도 한 번에 찍으므로 상한이 다르다 — 상한을 그냥 올리는 것이 아니라
# **전수 수집을 선언한 사양에만** 올린다.  선언하지 않은 사양은 예전 상한(6/2) 그대로다.
FULL_COLLECTION = "full_69_single_stage"
VIDEO_CAPS = {FULL_COLLECTION: (10, 4), None: (6, 2)}


def collection_mode(spec: dict) -> str | None:
    return (spec.get("collection") or {}).get("mode")


def video_caps(spec: dict) -> tuple[int, int]:
    mode = collection_mode(spec)
    if mode not in VIDEO_CAPS:
        raise RuntimeError(f"unknown collection.mode {mode!r}")
    return VIDEO_CAPS[mode]


def targets(spec: dict) -> list[str]:
    return [entry for entries in spec["preregistered"]["target_groups"].values() for entry in entries]


def validate_spec(spec: dict) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"spec {spec.get('work_id')}: {message}")

    need(spec.get("work_id") in SPECS, f"work_id must be one of {sorted(SPECS)}")
    need(spec.get("runner") == RUNNER, f"runner must be {RUNNER}")
    need(spec.get("change_class") == "training_length", "change_class must be training_length")

    # The defining property: no reward weight moves.  This is what separates this builder from
    # tools/build_go2_candidate_package.py, and it is checked, not assumed.
    base, cand_rewards = spec["rewards"]["baseline"], spec["rewards"]["candidate"]
    need(tuple(base) == REWARD_NAMES and tuple(cand_rewards) == REWARD_NAMES,
         f"reward keys/order must be {REWARD_NAMES}")
    changed = [name for name in REWARD_NAMES if float(base[name]) != float(cand_rewards[name])]
    need(changed == [], f"a training-length run must change no reward, got {changed}")

    single, training = spec["single_change"], spec["training"]
    need(single["name"] == "max_iterations", "single_change must be max_iterations")
    need(int(single["from"]) == 1000 and int(single["to"]) == int(training["max_iterations"]),
         "single_change must go from the 1000-iteration baseline to training.max_iterations")
    need(training["from_scratch"] is True and training["seed"] == 42 and training["num_envs"] == 4096,
         "training must be from scratch, seed 42, 4096 envs")
    need(int(training["max_iterations"]) > 1000, "a training-length run must train longer than the baseline")

    # The evaluated checkpoint must be one the run actually writes.
    pinned = spec["evaluation"].get("checkpoint_iter")
    last_saved = ((int(training["max_iterations"]) - 1) // SAVE_INTERVAL) * SAVE_INTERVAL
    need(pinned == last_saved,
         f"evaluation.checkpoint_iter must be {last_saved}, the last checkpoint save_interval "
         f"{SAVE_INTERVAL} guarantees for max_iterations {training['max_iterations']}")

    baseline = spec["baseline"]
    need(baseline["name"] == "G-A033", "baseline must be the promoted G-A033 arm")
    # The label names the baseline arm inside THIS run's harvest.  It can never be "candidate":
    # the gate and the local verifier read evaluation/<label>/cases as "the baseline was remeasured
    # in this run", and evaluation/candidate/cases always exists, so the candidate would be compared
    # with itself (2026-09-16: the first G-A035 package shipped exactly that).  Where the baseline
    # sits inside the stored arm is a separate field, because G-A033 was itself a candidate.
    need(baseline["label"] == "g_a033" and baseline["label"] != "candidate",
         "baseline.label must be g_a033, never candidate")
    need(baseline.get("stored_label") == "candidate",
         "baseline.stored_label must name G-A033's folder inside its stored arm")
    need((ROOT / baseline["stored_arm"]).is_dir(), f"stored_arm {baseline['stored_arm']} not on disk")
    now = (ROOT / "GO2_NOW.md").read_text(encoding="utf-8")
    for key, field in (("model_sha256", "BASELINE_MODEL_SHA256"), ("env_sha256", "BASELINE_ENV_SHA256"),
                       ("registry_sha256", "REGISTRY_SHA256")):
        need(re.search(rf"^{field}: {baseline[key]}$", now, re.M) is not None,
             f"baseline.{key} must equal GO2_NOW.md {field} (the frozen baseline is canonical)")

    history = a030.MASTER.read_text(encoding="utf-8").split("## 1-a.", 1)[1].split("\n## ", 1)[0]
    need(bool(spec.get("dial_history_ref")) and spec["dial_history_ref"] in history,
         "dial_history_ref must quote a row of GO2_REWARD_EVIDENCE_MASTER.md section 1-a")

    # G-D-EXTREF-20260915: the external comparison must agree with the reference JSON.  For a
    # training-length run the anchor is the runner block, not the reward table.
    ext = spec.get("external_reference") or {}
    runner_ref = json.loads(EXTREF.read_text(encoding="utf-8"))["isaaclab"]["runner"]
    need(ext.get("term") == "max_iterations", "external_reference.term must be max_iterations")
    need(int(ext.get("isaaclab_go2_rough", -1)) == int(runner_ref["go2_rough_max_iterations"]),
         "external_reference.isaaclab_go2_rough must equal the reference go2_rough_max_iterations")
    need(int(ext.get("isaaclab_go2_flat", -1)) == int(runner_ref["go2_flat_max_iterations"]),
         "external_reference.isaaclab_go2_flat must equal the reference go2_flat_max_iterations")
    need(int(ext.get("candidate", -1)) == int(training["max_iterations"]),
         "external_reference.candidate must equal training.max_iterations")

    evaluation = spec["evaluation"]
    # The gate and the verifiers read these blocks by key.  A missing key is not a validation
    # failure there, it is a KeyError on the server after training (v1 lacked sentinel_tolerance).
    # So the spec must carry every key the last staged spec that ran end to end carried.
    ran = json.loads((EXPERIMENTS / "G_A033_a017_track_lin_vel_xy_150.json").read_text(encoding="utf-8"))
    for block in ("evaluation", "preregistered", "baseline", "videos", "output"):
        missing = sorted(set(ran[block]) - set(spec[block]))
        need(not missing, f"{block} lacks keys the gate/verifier read in G-A033: {missing}")
    need(set(evaluation["sentinel_tolerance"]) >= {"survival_abs", "tracking_proxy_abs"},
         "evaluation.sentinel_tolerance needs survival_abs and tracking_proxy_abs")
    need(evaluation["seeds"] == [101, 202, 303] and evaluation["case_count"] == 69, "69 cases over 101/202/303")
    need(evaluation["num_envs"] == 32 and evaluation["steps"] == 1000, "evaluation must be 32 envs x 1000 steps")
    target = targets(spec)
    groups = spec["preregistered"]["target_groups"]
    # 2026-09-19: v1 은 "세 묶음 × 정확히 3 case" 로 고정돼 있었다.  그 고정이, G-A038 을 판정 불가로
    # 만든 구조를 사양이 스스로 고치지 못하게 막고 있었다: 축 점수는 (case, seed) 쌍이 하나라도 빠지면
    # 그 축을 가중합에서 통째로 뺀다(go2_fixed_eval_report.py:106-141).  그러므로 목표 축을 1단계에서
    # 채점하려면 그 축의 모든 쌍이 표적이어야 하고, G3 는 case 2개 × seed 3개 = 6 쌍이다.
    # 묶음 수 셋은 그대로 두고 묶음 크기의 하한만 남긴다.  상한 12 는 1단계가 2단계 몫까지 삼키지
    # 않도록 두는 것이다(69 case 중 표적 12 + 파국 1).
    need(len(groups) == 3 and all(len(entries) >= 3 for entries in groups.values()),
         "three target groups of at least three cases each")
    need(3 <= len(target) <= 12 and len(set(target)) == len(target),
         "target cases must be distinct and at most 12")
    need(evaluation["catastrophe_case"] not in target, "the catastrophe case must not be a target case")

    videos = spec["videos"]
    for entry in [evaluation["catastrophe_case"], *evaluation["sentinel_cases"], *target,
                  *videos["candidate"], *videos["baseline"]]:
        need(bool(ENTRY.match(entry)), f"bad case entry {entry!r}")
    need(videos["num_envs"] == 4 and videos["steps"] == 500, "videos are 4 envs x 500 steps")
    max_candidate, max_baseline = video_caps(spec)
    need(1 <= len(videos["candidate"]) <= max_candidate and len(videos["baseline"]) <= max_baseline,
         f"at most {max_candidate} candidate and {max_baseline} baseline videos")
    need(set(videos.get("reasons", {})) == set(videos["candidate"]), "every candidate video needs a reason")
    stored = ROOT / baseline["stored_arm"] / "evaluation" / baseline["stored_label"] / "videos"
    if stored.is_dir():
        reused = reuse_problems(spec)
        need(reused == [], f"videos.baseline_reuse does not verify: {reused}")
        for entry in videos["candidate"]:
            scenario, case_id, seed = entry.split(":")
            need((stored / f"{scenario}_{case_id}_seed_{seed}.mp4").is_file() or entry in videos["baseline"]
                 or entry in (videos.get("baseline_reuse") or {}),
                 f"candidate video {entry} has no baseline counterpart and is not rendered here")

    # Thresholds must cite a measurement, and the sentinel/target cases must exist in the stored arm
    # we will compare against -- otherwise the run produces numbers with nothing to read them against.
    need(bool(str(spec["preregistered"].get("threshold_basis", "")).strip()),
         "preregistered.threshold_basis must cite the measurement the limits come from")
    cases = ROOT / baseline["stored_arm"] / "evaluation" / baseline["stored_label"] / "cases"
    if cases.is_dir():
        for entry in [*target, *evaluation["sentinel_cases"], evaluation["catastrophe_case"]]:
            _scenario, case_id, seed = entry.split(":")
            need((cases / f"seed_{seed}" / case_id / "summary.json").is_file(),
                 f"stored baseline arm has no {entry} to compare against")

    # 2026-09-22 (G-A044): 전수 수집 회차는 1단계가 없으므로 `stages.full` 하나만 선언한다.
    # 어느 쪽이든 **선언한 것과 실제가 같아야 한다**는 검사는 그대로다 — 모드에 따라 기대하는
    # 집합이 달라질 뿐이고, 모드를 선언하지 않은 사양은 예전과 똑같이 두 단계를 요구한다.
    expected_stages = {"full"} if collection_mode(spec) == FULL_COLLECTION else {"target", "full"}
    need(set(spec.get("stages", {})) == expected_stages,
         f"stages must be {sorted(expected_stages)}")
    output = spec["output"]
    need(output["package_root"] == f"/workspace/{prefix(spec).as_posix()}", "package_root must match the ZIP prefix")
    need(output["tmux_name"] == prefix(spec).as_posix(), "tmux_name must be the prefix")
    need(bool(re.fullmatch(r"\[DONE\] [A-Z0-9_]{3,100}", output["done_marker"])), "bad done_marker")
    need(bool(re.fullmatch(r"GO2_G_A\d{3}_[a-z0-9_]+\.zip", output["upload_zip"])), "bad upload_zip")
    cand.check_release_version_in_zip_name(output, need)


def rendered_rewards(spec: dict) -> tuple[str, str]:
    """Render the candidate and reference reward files.  They must come out identical."""
    template = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
    candidate = render_reward_source(template, spec["rewards"]["candidate"])
    reference = render_reward_source(template, spec["rewards"]["baseline"])
    if candidate != reference:
        raise RuntimeError("a training-length run must render identical reward files")
    if reward_dict(candidate) != spec["rewards"]["candidate"]:
        raise RuntimeError("rendered reward file does not read back as the spec")
    return candidate, reference


def run_config(spec: dict) -> str:
    text = a030.run_config(spec)
    text = text.replace(f"# generated by tools/build_go2_g_a030_package.py from {a030.SPEC.name}; do not edit",
                        f"# generated by tools/build_go2_training_length_package.py "
                        f"from {SPECS[spec['work_id']].name}; do not edit")
    text += "TARGET_CASES=(" + " ".join(shlex.quote(item) for item in targets(spec)) + ")\n"
    text += f"EVAL_CHECKPOINT_ITER={int(spec['evaluation']['checkpoint_iter'])}\n"
    return text


def build_payload(spec: dict) -> dict[str, bytes]:
    validate_spec(spec)
    base = spec["baseline"]
    model = (BASELINE_SOURCE / "model_best.pt").read_bytes()
    env = (BASELINE_SOURCE / "env.yaml").read_bytes()
    if sha(model) != base["model_sha256"] or sha(env) != base["env_sha256"]:
        raise RuntimeError("G-A033 model/env on disk do not match the frozen SHA")
    trained = BASELINE_SOURCE / "source" / "quadruped_rewards.py"
    if trained.is_file() and reward_dict(trained.read_text(encoding="utf-8")) != spec["rewards"]["baseline"]:
        raise RuntimeError("spec baseline rewards differ from the rewards G-A033 was trained with")
    evaluator = (GO2 / "go2_eval_telemetry.py").read_bytes()
    registry = a030.REGISTRY.read_bytes()
    if sha(evaluator) != base["evaluator_sha256"] or sha(registry) != base["registry_sha256"]:
        raise RuntimeError("working-tree evaluator/registry differ from the ruler of the stored baseline arm")
    runner = cand.runner_bytes(spec)
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
    out, training, evaluation = spec["output"], spec["training"], spec["evaluation"]
    title = f"GO2 {spec['work_id']} TRAINING LENGTH — G-A033 rewards, {training['max_iterations']} iterations"
    why = "\n".join("  " + line for line in spec["why"])
    root = out["package_root"]
    videos = "\n".join(f"  {entry:26s} {spec['videos']['reasons'][entry]}" for entry in spec["videos"]["candidate"])
    stages = spec["stages"]
    return f"""{title}
{'=' * len(title)}

This package TRAINS one policy and then measures it.  status: exploratory.

WHAT CHANGES
  NO REWARD WEIGHT CHANGES.  candidate/quadruped_rewards.py and
  reference/baseline_quadruped_rewards.py are byte-identical, on purpose.
  The single change is training length: {spec['single_change']['from']} -> {spec['single_change']['to']} iterations,
  the Isaac Lab v2.3.1 go2_rough value.  Deployed train/play/task code is unchanged.

WHY (plan {Path(spec['plan']).name})
{why}

WHAT IS AND IS NOT PROMISED
  Not promised: a higher score.  More training may not help.
  Observed: the training log records the terrain curriculum level every
  iteration.  It is the MEAN over all robots and all sub-terrain types, so it
  does not say how far the stair columns went.
  Not available: a determinism check.  The runner keeps iter {evaluation['checkpoint_iter']} and finalize's
  pick, not model_900.pt.  Training-seed noise is unmeasured (all runs seed 42).

CHECKPOINT
  Evaluated at iter {evaluation['checkpoint_iter']} of {training['max_iterations']} (save_interval {SAVE_INTERVAL}); the baseline
  G-A033 was evaluated at 900 of 1000.  Both are near-final checkpoints of their
  own run.  The iteration differs because training length IS the variable here.
  finalize's reward pick is kept as training/model_best_by_reward.pt, not evaluated.

STAGES (run the target stage first)
  target (default, ~{stages['target']['estimate_minutes']}m): training, catastrophe gate, the 9 target cases,
     {len(evaluation['sentinel_cases'])} sentinel cases, {len(spec['videos']['candidate'])} videos, result ZIP.  Criterion 1 is decided on
     the target cases alone, so a target-stage FAIL is final for this arm.
  full (~{stages['full']['estimate_minutes']}m, only after a target pass): {stages['full']['env']}

ONE COMMAND
  cd /workspace && unzip -o {out['upload_zip']} && cd {root} && \\
    tmux new -s {out['tmux_name']} -d 'bash {spec['runner']} 2>&1 | tee runner.log'
  Done marker: {out['done_marker']}
  Result:      {root}/{out['result_zip']}

VIDEOS (4 env x 500 steps)
{videos}

BASELINE ARM
  {spec['baseline']['stored_arm']} ({spec['baseline']['name']}, 42.52861/70 on the 69-case
  internal proxy).  Promoted to the frozen baseline by G-D-BASELINE-A033-20260916.
  Its model and env ship here so the server can verify it is the same bytes.
"""


def build_zip(spec: dict) -> bytes:
    import io
    payload = build_payload(spec)
    root = prefix(spec)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(payload):
            info = zipfile.ZipInfo((root / name).as_posix(), date_time=FIXED_TIMESTAMP)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload[name])
    return buffer.getvalue()


def guide(spec: dict, zip_sha: str) -> str:
    """The arm ZIP is not run on its own.  It says so, and names what to upload instead.

    The v1 guide told the operator to run the arm runner directly and promised that the runner
    prints TARGET_PASS_FULL_STAGE_REQUIRED.  Both were false: the runner's outer path launches a
    script this ZIP does not carry, and only the local verifier prints that verdict.
    """
    out = spec["output"]
    return f"""GO2 {spec['work_id']} ARM PACKAGE — DO NOT RUN THIS ZIP ON ITS OWN
{'=' * 56}

ARM ZIP  {out['upload_zip']}
SHA256   {zip_sha}

This ZIP is one arm of the campaign package built by
  python tools/build_go2_training_length_campaign.py {spec['work_id']}
The campaign ZIP carries this file byte for byte, runs its target stage, reads the server
gate, runs the full stage only if the gate passes, and returns one result ZIP.

Upload the campaign ZIP named in upload/{spec['work_id']}/current/CURRENT_UPLOAD.txt.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_id", choices=sorted(SPECS))
    parser.add_argument("--publish", action="store_true", help="also write upload/<work_id>/current")
    args = parser.parse_args(argv)

    spec = load(args.work_id)
    data = build_zip(spec)
    zip_sha = sha(data)
    target = output_path(spec)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    (target.parent / (target.name + ".sha256")).write_text(f"{zip_sha}  {target.name}\n", encoding="utf-8")
    (target.parent / guide_name(spec)).write_text(guide(spec, zip_sha), encoding="utf-8")

    if args.publish:
        current = upload_dir(spec) / "current"
        current.mkdir(parents=True, exist_ok=True)
        for name in (target.name, target.name + ".sha256", guide_name(spec)):
            (current / name).write_bytes((target.parent / name).read_bytes())
        (current / "PUBLISHED_AT.txt").write_text(PUBLISHED_AT + "\n", encoding="utf-8")

    payload = build_payload(spec)
    print(f"{args.work_id}: {len(payload)} files, ZIP {len(data)} bytes")
    print(f"  {target.relative_to(ROOT).as_posix()}")
    print(f"  sha256 {zip_sha}")
    print(f"  reward change: none (training length {spec['single_change']['from']} -> {spec['single_change']['to']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
