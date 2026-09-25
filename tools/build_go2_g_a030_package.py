"""Build (and optionally publish) the G-A030 candidate-suite server package.

One upload, one command, one result ZIP: one single-variable training run on
A017 (flat_orientation_l2 0.0 -> -1.0, seed 42, 1000 iter), then the 69-case
posture-gated suite on the trained candidate.
Plan: workspace/training/quadruped/upload/plan/GO2_G_A030_TUNING_PLAN_20260914.md.

Measurement path (나′, user decision 2026-09-14): the G-A027 full-suite runner
generalised to one trained arm (server_run_go2_candidate_suite.sh).  The deployed
training code and the evaluator ship byte-for-byte as they are in the working
tree; only the reward values are rendered, into the candidate's copy of
quadruped_rewards.py.  The tuning engine (go2_tuning_config.py) is used
read-only for its reward renderer and is not modified.

    python tools/build_go2_g_a030_package.py            # build and verify
    python tools/build_go2_g_a030_package.py --publish  # also publish upload/G-A030
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
sys.path.insert(0, str(GO2))

from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

SPEC = GO2 / "config" / "experiments" / "G_A030_a017_flat_orientation_m1.json"
A017_SOURCE = ROOT / "workspace" / "_keep" / "go2_g_a017_pilot_track_lin_vel_xy_140" / "training"
A027_IDENTITY = ROOT / "workspace" / "_keep" / "go2_a017_full_suite" / "evaluation" / "a017" / "identity.json"
MASTER = ROOT / "GO2_REWARD_EVIDENCE_MASTER.md"
REGISTRY = GO2 / "config" / "go2_self_eval_registry.json"
RUNNER = "server_run_go2_candidate_suite.sh"
ENGINE_RUNNER = "server_run_go2_tuning_engine_v1.sh"
HELPERS = ("package_go2_result.py", "posture_contract_check.py", "candidate_suite_checks.py")
PREFIX = Path("go2_g_a030")
ZIP_NAME = "GO2_G_A030_flat_orientation_m1.zip"
GUIDE_NAME = "GO2_G_A030_RUN_GUIDE.txt"
FIXED_TIMESTAMP = (2026, 9, 14, 0, 0, 0)
UPLOAD = GO2 / "upload" / "G-A030"
RELEASE_ID = "20260914_a017_flat_orientation_m1_candidate_suite_v1"
PUBLISHED_AT = "2026-09-14T00:00:00+00:00"
OUTPUT = UPLOAD / "history" / RELEASE_ID / ZIP_NAME
REPORT_BLOCK = re.compile(r"# BEGIN GO2_REPORT_RECOVERY\n.*?# END GO2_REPORT_RECOVERY\n", re.S)
ENTRY = re.compile(r"^G[1-7]:[a-z0-9_]+:(101|202|303)$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_spec(path: Path = SPEC) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_files() -> list[Path]:
    files = [GO2 / name for name in ("train.py", "play.py", "pyproject.toml", "go2_eval_telemetry.py",
                                     "go2_policy_lineage.py", "quadruped_rewards.py")]
    files.extend(sorted((GO2 / "go2_task").glob("*.py")))
    return files


def validate_spec(spec: dict) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"spec: {message}")

    need(spec.get("work_id") == "G-A030", "work_id must be G-A030")
    need(spec.get("runner") == RUNNER, f"runner must be {RUNNER}")
    base, cand = spec["rewards"]["baseline"], spec["rewards"]["candidate"]
    need(tuple(base) == REWARD_NAMES and tuple(cand) == REWARD_NAMES, f"reward keys/order must be {REWARD_NAMES}")
    changed = [name for name in REWARD_NAMES if float(base[name]) != float(cand[name])]
    need(changed == ["flat_orientation_l2"], f"candidate must change exactly flat_orientation_l2, got {changed}")
    single = spec["single_change"]
    need(single["name"] == "flat_orientation_l2" and float(single["from"]) == float(base["flat_orientation_l2"])
         and float(single["to"]) == float(cand["flat_orientation_l2"]), "single_change does not match the rewards")
    training = spec["training"]
    need(training == {"from_scratch": True, "seed": 42, "num_envs": 4096, "max_iterations": 1000},
         "training must be from scratch, seed 42, 4096 envs, 1000 iter (plan section 5)")
    history = MASTER.read_text(encoding="utf-8").split("## 1-a.", 1)[1].split("\n## ", 1)[0]
    need(spec.get("dial_history_ref", "") in history and spec.get("dial_history_ref"),
         "dial_history_ref must quote a row of GO2_REWARD_EVIDENCE_MASTER.md section 1-a")
    evaluation = spec["evaluation"]
    need(evaluation["seeds"] == [101, 202, 303] and evaluation["case_count"] == 69, "69 cases over 101/202/303")
    need(evaluation["num_envs"] == 32 and evaluation["steps"] == 1000, "evaluation must be 32 envs x 1000 steps")
    for entry in [evaluation["catastrophe_case"], *evaluation["sentinel_cases"],
                  *spec["videos"]["candidate"], *spec["videos"]["baseline"]]:
        need(bool(ENTRY.match(entry)), f"bad case entry {entry!r}")
    need(spec["videos"]["num_envs"] == 4 and spec["videos"]["steps"] == 500, "videos are 4 envs x 500 steps")
    need(len(spec["videos"]["candidate"]) == 12 and len(spec["videos"]["baseline"]) == 2, "12 + 2 videos (plan 7)")
    output = spec["output"]
    need(output["package_root"] == f"/workspace/{PREFIX.as_posix()}", "package_root must match the ZIP prefix")
    need(bool(re.fullmatch(r"\[DONE\] [A-Z0-9_]{3,100}", output["done_marker"])), "bad done_marker")


def rendered_rewards(spec: dict) -> tuple[str, str]:
    template = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
    candidate = render_reward_source(template, spec["rewards"]["candidate"])
    reference = render_reward_source(template, spec["rewards"]["baseline"])
    differing = [(a, b) for a, b in zip(reference.splitlines(), candidate.splitlines()) if a != b]
    if len(reference.splitlines()) != len(candidate.splitlines()) or len(differing) != 1 \
            or '"flat_orientation_l2"' not in differing[0][1]:
        raise RuntimeError(f"rendered reward files must differ in the flat_orientation_l2 line only: {differing}")
    return candidate, reference


def run_config(spec: dict) -> str:
    base, single, training = spec["baseline"], spec["single_change"], spec["training"]
    output, evaluation, videos = spec["output"], spec["evaluation"], spec["videos"]
    scalars = {
        "WORK_ID": spec["work_id"],
        "RUN_ID": spec["run_id"],
        "EXPERIMENT_SLUG": spec["experiment_slug"],
        "KEEP_DIR_NAME": output["keep_dir_name"],
        "RESULT_ZIP_NAME": output["result_zip"],
        "DONE_MARKER": output["done_marker"],
        "TMUX_NAME": output["tmux_name"],
        "TRAIN_SEED": training["seed"],
        "NUM_ENVS": training["num_envs"],
        "MAX_ITERATIONS": training["max_iterations"],
        "SINGLE_CHANGE_NAME": single["name"],
        "SINGLE_CHANGE_FROM": single["from"],
        "SINGLE_CHANGE_TO": single["to"],
        "BASELINE_NAME": base["name"],
        "BASELINE_LABEL": base["label"],
        "BASELINE_MODEL_SHA": base["model_sha256"],
        "BASELINE_ENV_SHA": base["env_sha256"],
        "EXPECTED_EVALUATOR_SHA": base["evaluator_sha256"],
        "EXPECTED_REGISTRY_SHA": base["registry_sha256"],
        "CATASTROPHE_CASE": evaluation["catastrophe_case"],
    }
    lines = [f"# generated by tools/build_go2_g_a030_package.py from {SPEC.name}; do not edit"]
    lines += [f"{key}={shlex.quote(str(value))}" for key, value in scalars.items()]
    for name, items in (("SENTINEL_CASES", evaluation["sentinel_cases"]),
                        ("CANDIDATE_VIDEOS", videos["candidate"]),
                        ("BASELINE_VIDEOS", videos["baseline"])):
        lines.append(f"{name}=(" + " ".join(shlex.quote(item) for item in items) + ")")
    return "\n".join(lines) + "\n"


def build_payload(spec: dict | None = None) -> dict[str, bytes]:
    spec = spec or load_spec()
    validate_spec(spec)
    base = spec["baseline"]

    model = (A017_SOURCE / "model_best.pt").read_bytes()
    env = (A017_SOURCE / "env.yaml").read_bytes()
    if sha(model) != base["model_sha256"] or sha(env) != base["env_sha256"]:
        raise RuntimeError("A017 model/env on disk do not match the frozen SHA")
    trained = A017_SOURCE / "source" / "quadruped_rewards.py"
    if trained.is_file() and reward_dict(trained.read_text(encoding="utf-8")) != spec["rewards"]["baseline"]:
        raise RuntimeError("spec baseline rewards differ from the rewards A017 was trained with")

    evaluator = (GO2 / "go2_eval_telemetry.py").read_bytes()
    registry = REGISTRY.read_bytes()
    if sha(evaluator) != base["evaluator_sha256"] or sha(registry) != base["registry_sha256"]:
        raise RuntimeError("working-tree evaluator/registry differ from the ruler of the stored baseline arm")
    if A027_IDENTITY.is_file():
        identity = json.loads(A027_IDENTITY.read_text(encoding="utf-8"))
        if (identity["evaluator_sha256"], identity["registry_sha256"], identity["model_sha256"]) != \
                (base["evaluator_sha256"], base["registry_sha256"], base["model_sha256"]):
            raise RuntimeError("spec baseline ruler differs from the stored G-A027 a017 identity")

    runner = (GO2 / RUNNER).read_bytes()
    if b"\r" in runner:
        raise RuntimeError("runner has CR bytes")
    engine = (GO2 / ENGINE_RUNNER).read_text(encoding="utf-8")
    ours = REPORT_BLOCK.search(runner.decode("utf-8"))
    theirs = REPORT_BLOCK.search(engine)
    if not ours or not theirs or ours.group(0) != theirs.group(0):
        raise RuntimeError("runner report-recovery block must equal the engine's")

    candidate_rewards, reference_rewards = rendered_rewards(spec)
    payload: dict[str, bytes] = {}
    # Both roles ship the working tree's files byte for byte, so the evaluator
    # and play.py cannot differ between the arms, and baseline/ is the same
    # tree the G-A027 a017 role shipped.  Only candidate/quadruped_rewards.py is
    # rendered: that file is the single variable.
    for role in ("candidate", "baseline"):
        for path in source_files():
            payload[f"{role}/{path.relative_to(GO2).as_posix()}"] = path.read_bytes()
    payload["candidate/quadruped_rewards.py"] = candidate_rewards.encode("utf-8")
    payload["reference/baseline_quadruped_rewards.py"] = reference_rewards.encode("utf-8")
    payload["baseline/exported/model_best.pt"] = model
    payload["baseline/exported/env.yaml"] = env
    payload["go2_self_eval_registry.json"] = registry
    for name in HELPERS:
        payload[name] = (GO2 / name).read_bytes()
    payload[RUNNER] = runner
    payload["run_config.env"] = run_config(spec).encode("utf-8")
    payload["experiment.json"] = SPEC.read_bytes()
    payload["expected_rewards.json"] = (json.dumps(spec["rewards"], indent=2) + "\n").encode("utf-8")
    payload["README.txt"] = readme(spec).encode("utf-8")
    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def readme(spec: dict) -> str:
    prereg = spec["preregistered"]
    return f"""GO2 {spec['work_id']} CANDIDATE SUITE — A017 + flat_orientation_l2 0.0 -> -1.0
==========================================================================

This package TRAINS one policy and then measures it.  status: exploratory.

WHAT CHANGES
  The baseline is A017 (Pilot-01 + track_lin_vel_xy_exp 1.4), 39.76/70 on the
  69-case internal proxy (G-A027).  The candidate changes one reward only:
  flat_orientation_l2 0.0 -> -1.0.  Deployed train/play/task code is unchanged
  (R-6); only candidate/quadruped_rewards.py carries the new value.

WHY (plan {Path(spec['plan']).name})
  A017 loses 9.03/70 on G3, and G3's floor is rough_lateral, whose survival
  loss is entirely base-contact terminations (17/14/17 of 32).  In the 0.5 s
  before a termination the body tilt q = 1 - g_z^2 is 23-46x that of surviving
  robots in the same window, and already 5-12x one window earlier.  That is a
  reason to target this behaviour, not an established cause: slipping first
  and tilting after (H-B) is not excluded.

PHASES
  1  training, seed {spec['training']['seed']}, {spec['training']['num_envs']} envs, {spec['training']['max_iterations']} iter; report.html kept
  2  catastrophe gate: non-finite training loss, or a stationary candidate on
     {spec['evaluation']['catastrophe_case']}, stops the run here (one witness video)
  3  candidate 69-case suite, seeds 101/202/303, posture_gate_v2
  4  baseline: 5 sentinel cases re-measured against the stored G-A027 arm, or
     all 69 with GO2_REMEASURE_BASELINE=1
  5  12 candidate videos + 2 baseline videos
  6  one-file result ZIP

RUN
  unzip {ZIP_NAME} -d /workspace
  bash /workspace/{PREFIX.as_posix()}/{RUNNER}
  Finish marker: {spec['output']['done_marker']}

DOWNLOAD
  /workspace/_keep/{spec['output']['result_zip']}
  /workspace/_keep/{spec['output']['result_zip']}.sha256

PRE-REGISTERED READING (plan section 6, fixed before the run)
  success needs all of:
   1 rough_lateral survival up >= {prereg['min_target_survival_delta_each_seed']} on EACH of seeds 101/202/303
     (termination count and posture-gate fall count are read separately;
      only fewer terminations counts as support for H-A)
   2 total internal proxy +{prereg['min_total_points_delta']}/70 or more, same evaluator
   3 no case loses more than {prereg['max_case_survival_drop']} survival or {prereg['max_case_tracking_drop']} tracking;
     slope_plus_20 posture falls rise by at most {prereg['max_watch_posture_fall_increase_each_seed']} per seed
   4 POLICY_LOCOMOTES and no more stationary cases than the baseline
   5 videos show normal four-legged walking (human reading)
  The expected weighted gain is NOT estimated.  +1.0/70 is a criterion, not a
  forecast.  A failure keeps A017 and does not retry -0.5 or -2.0 automatically.
  Official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def build(spec: dict | None = None) -> Path:
    payload = build_payload(spec)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo((PREFIX / name).as_posix(), date_time=FIXED_TIMESTAMP)
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
    if OUTPUT.exists() and OUTPUT.read_bytes() != built:
        raise RuntimeError(f"immutable release conflict: {OUTPUT} differs from this build")
    OUTPUT.write_bytes(built)
    OUTPUT.with_suffix(".zip.sha256").write_text(f"{sha(built)}  {ZIP_NAME}\n", encoding="utf-8", newline="\n")
    return OUTPUT


def run_guide(spec: dict, digest: str) -> str:
    output = spec["output"]
    keep = f"workspace/_keep/{output['keep_dir_name']}"
    return f"""GO2 {spec['work_id']} SERVER RUN GUIDE (candidate suite v1, posture_gate_v2, 학습 1회)

회차 {spec['work_id']}: A017 + `flat_orientation_l2` 0.0→-1.0 단일변수, seed 42, 1,000 iter.
계획서: {spec['plan']}
사용자 결정(2026-09-14): 후보 A, 측정 경로 (나′). C 보류는 로컬 패키지 범위에서만 해제됐다.
**서버 실행은 사용자 결정 사항이다.** 이 문서는 실행 절차이지 실행 승인이 아니다.

LOCAL FILE TO UPLOAD (딱 하나)
1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\G-A030\\current\\{ZIP_NAME}
   SHA256 {digest}
러너·evaluator·registry·A017 정책·렌더된 reward 파일이 모두 이 ZIP 안에 있다.

SERVER DESTINATION
/workspace/{ZIP_NAME}

접속 직후 먼저 (실행 전)
잔여 GPU 시간을 확인해 기록한다. 필요 시간은 약 2시간 10분, 여유 포함 약 2시간 35분이다.
그보다 적으면 실행하지 않는다(계약 3항 ③ 회수 불가).

ONE-LINE RUN (tmux 안에서 시작하고 즉시 리턴)
cd /workspace && echo '{digest}  {ZIP_NAME}' | sha256sum -c - && unzip -oq {ZIP_NAME} && bash {output['package_root']}/{RUNNER}

MONITOR
tmux attach -t {output['tmux_name']}

진행 단계
1) 학습 1,000 iter(약 57분). 끝나면 report.html을 평가 전에 보존한다.
2) 파국 게이트: 학습 손실 비유한값, 또는 {spec['evaluation']['catastrophe_case']} 정지 판정이면 평가를 생략하고 영상 1개와 함께 회수한다.
3) 후보 69 case(23 case × seed 101/202/303).
4) A017 표지 case 5건 재측정. G-A027 저장값과 대조하는 용도다.
5) 영상 14개(후보 12, A017 2). 4 env, 500 step.
6) 결과 ZIP 1개.

첫 10분에 볼 것
학습 로그의 reward 표에 `flat_orientation_l2` 가중치 -1.0이 찍히는지 본다.
iteration이 진행되는지, `_keep/{output['keep_dir_name']}/logs/candidate_training.log`가 커지는지 본다.

학습 직후에 볼 것
`[PHASE 2/6]` 뒤 `ENV_REWARDS_OK role=candidate ... flat_orientation_l2=-1.0` 줄이 있어야 한다.
`LOCOMOTION MOVING` 줄이 있어야 한다.

RESUME / RERUN 규칙
기본 재실행은 이전 결과를 지우지 않고 거부한다. 이어가려면 `GO2_RESUME=1`, 버리려면 `GO2_DISCARD_PREVIOUS=1`.
resume은 정책·case·seed·argv·step 수·evaluator SHA 지문으로 판정한다. 끊기면 `_keep`을 통째로 내려받는다.

기준 arm 재측정 (회수 검증이 요구할 때만)
회수 검증이 BASELINE_REMEASURE_REQUIRED를 내면 다음 세션에서 같은 ZIP으로 실행한다.
  GO2_RESUME=1 GO2_REMEASURE_BASELINE=1 bash {output['package_root']}/{RUNNER}
이미 잰 후보 case는 건너뛰고 A017 69 case를 같은 evaluator로 잰다(+약 50분).
재평가 자체는 지문 불일치를 해소하지 않는다. 두 arm이 같은 계측기로 재였을 때만 비교한다.

예산이 모자랄 때
먼저 접는 것은 영상이다. 영상을 생략하면 판정은 VIDEO_UNKNOWN으로 남고 후보 승급은 보류된다.
학습과 후보 69 case는 쪼갤 수 없다. 잔여 시간이 빠듯하면 끝까지 밀지 말고 중간 회수한다.

DONE MARKER
{output['done_marker']}

DOWNLOAD TO LOCAL workspace\\_keep
/workspace/_keep/{output['result_zip']}
/workspace/_keep/{output['result_zip']}.sha256
패키징이 실패할 수 있으니 `_keep/{output['keep_dir_name']}` 원시 파일도 함께 가져온다.

SERVER SHUTDOWN GATE
DONE 표시만으로 종료하지 않는다. 두 파일을 받은 뒤 로컬 검증을 통과해야 종료 판단을 보고한다.
확인 항목: outer SHA · ZIP CRC · 내부 SHA256SUMS · RUNNER_RC=0 · report.html(REPORT_ACQUIRED) · 학습 model/env · env reward 가중치 ·
후보 69건 telemetry · 표지 5건 · 영상 14건 · EVALUATOR_SHA · TELEMETRY_SCHEMA=6.

회수 검증 — 어떤 수치도 읽기 전에 (GPU 0)
python -B tools/verify_go2_g_a030_harvest.py --harvest {keep} --out {keep}/harvest_verification.json
INCONCLUSIVE면 점수를 읽지 않는다. 손상된 case를 빼고 68건으로 점수를 완성하지 않는다.

RESULT INTERPRETATION — 실행 전에 고정 (계획서 §6, 사후 재협상 금지)
성공은 다음을 모두 충족할 때다.
- rough_lateral 생존이 seed별로 각각 +.10 이상 오른다.
- 총 proxy가 +1.0/70 이상 오른다.
- 69 case 모두 생존 -1/32·추종 -.02 이내이고, slope_plus_20 게이트 낙상은 seed별 +1 이내다.
- POLICY_LOCOMOTES이고 정지 case가 기준 이하이다.
- 영상에서 정상 네발 보행이 보인다.
생존 +.10은 종료 4개 감소와 같지 않다. 종료 수와 자세 게이트 낙상 수는 따로 판독한다.
기대 가중 이득은 `미추정`이다. +1.0/70은 판정 기준이지 예측이 아니다.
실패하면 A017을 유지하고 -0.5·-2.0으로 자동 재탐색하지 않는다.
성공해도 `exploratory` 승자일 뿐이다. 승급 전에 seed 43 재현이 필요하다.
공식 evaluator·공식 점수는 OFFICIAL_RESULT_UNMEASURED다.

PARALLELISM
학습·평가·영상은 순차 실행이며 동시 작업을 띄우지 않는다.
"""


def publish(spec: dict, zip_path: Path) -> None:
    digest = sha(zip_path.read_bytes())
    history = UPLOAD / "history" / RELEASE_ID
    current = UPLOAD / "current"
    current.mkdir(parents=True, exist_ok=True)
    guide = run_guide(spec, digest)
    manifest = {
        "experiment_id": spec["work_id"],
        "note": "A017 + flat_orientation_l2 0.0->-1.0, 1,000 iter training + 69-case candidate suite "
                "(candidate suite runner v1, measurement path 나′). exploratory.",
        "published_at_utc": PUBLISHED_AT,
        "release_id": RELEASE_ID,
        "status": "ARTIFACT_VERIFIED",
        "support_files": [GUIDE_NAME],
        "upload_files": [{"name": ZIP_NAME, "server_path": f"/workspace/{ZIP_NAME}", "sha256": digest}],
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    current_text = (
        f"CURRENT GO2 UPLOAD — {spec['work_id']}\n\n"
        "UPLOAD ONLY THIS ONE FILE\n"
        f"1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\G-A030\\current\\{ZIP_NAME}\n"
        f"   SHA256 {digest}\n\n"
        "이 패키지는 A017 + flat_orientation_l2 -1.0을 1,000 iter 학습하고 후보 69 case를 잰다.\n"
        f"자세한 절차는 같은 폴더의 {GUIDE_NAME}. 서버 실행은 사용자 결정 사항이다.\n\n"
        f"RELEASE_ID {RELEASE_ID}\nSTATUS ARTIFACT_VERIFIED\n"
        "History is preserved under ../history and in ../UPLOAD_HISTORY.tsv.\n"
    )
    files = {
        GUIDE_NAME: guide.encode("utf-8"),
        "UPLOAD_MANIFEST.json": manifest_text.encode("utf-8"),
        "CURRENT_UPLOAD.txt": current_text.encode("utf-8"),
    }
    for name, data in files.items():
        target = history / name
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError(f"immutable release conflict: {target}")
        target.write_bytes(data)
    (history / f"{GUIDE_NAME}.sha256").write_text(f"{sha(files[GUIDE_NAME])}  {GUIDE_NAME}\n",
                                                  encoding="utf-8", newline="\n")
    for source in (zip_path, zip_path.with_suffix(".zip.sha256"), *(history / name for name in files),
                   history / f"{GUIDE_NAME}.sha256"):
        (current / source.name).write_bytes(source.read_bytes())
    ledger = UPLOAD / "UPLOAD_HISTORY.tsv"
    header = "published_at_utc\texperiment_id\trelease_id\tstatus\tengine_file\tengine_sha256\tspec_file\tspec_sha256\tnote\n"
    row = "\t".join([PUBLISHED_AT, spec["work_id"], RELEASE_ID, "ARTIFACT_VERIFIED", ZIP_NAME, digest,
                     "(none — self-contained)", "(none)", manifest["note"]]) + "\n"
    existing = ledger.read_text(encoding="utf-8") if ledger.exists() else header
    if row not in existing:
        ledger.write_text(existing + row, encoding="utf-8", newline="\n")
    print(f"published current={current}")
    print(f"published history={history}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    spec = load_spec()
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
