#!/usr/bin/env python3
"""학습 seed 대칭 쌍의 발행 — 한 파일 · 한 명령 · 결과 ZIP 하나, 팔 둘, 게이트 없음.

왜 또 새 모듈인가.  기존 빌더 둘은 각각 이 회차를 **표현할 수 없다**:
  `tools/build_go2_a033_reward_package.py` 는 `training == {seed 42, ...}` 를 단언한다.
  `tools/build_go2_training_length_package.py` 는 보상이 하나도 안 바뀌는 것까지는 허용하지만
  `single_change` 가 `max_iterations` 여야 하고 역시 seed 42 를 단언한다.
둘 다 이미 발행된 출력이 있고, 발행물은 재빌드로 대조된다 — 그래서 느슨하게 만들지 않는다
(`build_go2_a033_reward_package.py` 가 2026-09-18 에 같은 이유로 갈라져 나온 모듈이다).
이 모듈은 자기 검증만 새로 쓰고 나머지는 전부 바이트로 물려받는다: 반복 고정 러너, 배포 소스,
평가기, registry, 저장 G-A033 의 model/env.

이 회차는 **승급을 만들지 않는다.**  두 팔 다 학습 seed 43 이므로 `change_class` 가
`training_seed` 이고, 사양은 `promotion: forbidden_not_a_reward_change` 를 적어야만 지나간다.
R-6 해석은 열린 결정 **U2-SEED-REPLICATE-20260918** 이며 사용자 결정 대기다 — 이 모듈이 만드는
어떤 산출물도 그 결정을 기성사실로 쓰지 않는다.

발행은 산출물 무결성(ARTIFACT_VERIFIED)이고 성능 판정이 아니다.  서버 실행은 사용자 결정이다.

    python -B tools/build_go2_seed_pair_package.py G-A045_A046            # 만들고 검증만
    python -B tools/build_go2_seed_pair_package.py G-A045_A046 --publish  # upload/<ID>/current 까지
"""

from __future__ import annotations

import argparse
import hashlib
import io
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
import build_go2_training_length_package as length  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

EXPERIMENTS = GO2 / "config" / "experiments"
SPECS = {
    # 자(ruler): G-A033 의 보상 파일 그대로, 학습 seed 만 43.
    "G-A045": EXPERIMENTS / "G_A045_seed43_a033_rewards.json",
    # 재현: G-A043 과 같은 값(-1.5)을 같은 seed 43 위에서.
    "G-A046": EXPERIMENTS / "G_A046_seed43_lin_vel_z_m15.json",
}
RUNNER = "server_run_go2_full69_campaign.sh"
ARM_RUNNER = cand.PINNED_RUNNER
BASELINE_SOURCE = length.BASELINE_SOURCE
FIXED_TIMESTAMP = (2026, 9, 24, 0, 0, 0)
PUBLISHED_AT = "2026-09-24T00:00:00+00:00"
DECISION = "U2-SEED-REPLICATE-20260918"
CHANGE_CLASS = "training_seed"
PROMOTION = "forbidden_not_a_reward_change"

PAIRS = {
    "G-A045_A046": {
        # v8 (2026-09-24): 독립 검토 6차 — 중단·재개 경로의 결함 둘(C-27·C-28).  ① 재개가
        # 미완료 학습을 말없이 지우고 재학습하던 경로를 막고 보존·정지·명시 재시작으로
        # 갈랐다.  ② 완료 판단이 COLLECTION_STATUS 와 결과 ZIP·SHA 를 보지 않아
        # INCOMPLETE_COLLECTION 도 건너뛰던 것을 고쳤다.  값·문턱·평가 계약은 그대로다.
        # v7 (2026-09-24): 검토 5차 — ① 「최악이라도 GPU 시간만 잃는다」로 **손실 상한을 긋지**
        # 않는다: 서버 실행 자체가 허용되지 않는 행위로 판정되면 제재 범위는 미확정이고, 실행
        # 결정만으로 열린 해석이 닫히지도 않는다. ② A043 기각을 G2 하나로 좁히지 않는다 —
        # 총점 +2.09593 이 +2.53 에 미달했고 비열등 4건·screening 3건이 함께 있었다.
        # v6 (2026-09-24): 검토 4차 — 잔차 비율의 **분모**를 갈라 적었다.  |교차항|/|순변화|
        # 는 큰 반대 몫들이 상쇄되면 튀므로 인과적 기여율도 설명 실패율도 아니다.  크기합을
        # 분모로 한 값을 함께 싣고(A044 0.04%/0.03%, A043 79.89%/30.75%), 두 수가 벌어지는
        # 것 자체를 "상쇄가 심하다" 는 신호로 읽는다.  값·문턱·러너는 그대로다.
        # v5 (2026-09-24): 검토 3차 — 점수 분해를 **기여 분해**로 고쳐 적었다.  세 항의 합이
        # 총점 차이와 같은 것은 교차항을 잔차로 두기 때문이라 검증이 아니라 정의이고, 읽을
        # 것은 교차항의 크기다(A044 0.04% 대 A043 79.89%).  어느 쪽이든 "보상 변경이 낙상을
        # 일으켰다" 는 인과는 여기서 나오지 않는다.  값·문턱·러너는 그대로, 사양 산문만 바뀐다.
        # v4 (2026-09-24): 독립 검토가 사전등록 **해석**의 오류 넷을 잡았다(결함 C-26) — 계단
        # 재현을 B 의 절대값만으로 판정한 것, 작은 seed 차이를 "다이얼 탓" 의 근거로 쓴 것,
        # 큰 차이에서 승급 규칙 폐기·장기 학습으로 가겠다고 적은 것, 그리고 R-6 을 닫힌 것처럼
        # 적은 것.  값·문턱·러너·수집 계약은 그대로이고 바뀐 것은 **읽는 법**이다.  사양과
        # 안내문이 바뀌므로 팔은 v3, 쌍은 v4 로 낸다.
        # v3 (2026-09-24): 사양이 "학습 18회" 라는 세지 않은 수를 적고 있었다 — 회차 원장은
        # 학습 iteration 이 적힌 회차 22건을 싣고, seed 칸이 기록된 회수물은 21건이다.  숫자를
        # 원장에서 다시 세어 고치면서 팔 사양이 바뀌었고, 그래서 팔 ZIP 도 v2 로 다시 낸다.
        # v2 (2026-09-24): v1 은 같은 날 만든 **로컬 초안**이고 발행된 적이 없다 — 러너 머리말에
        # 열린 결정 U2-SEED-REPLICATE-20260918 을 적기 전 바이트였다.  history 의 바이트는
        # 고치지 않는 것이 이 저장소의 규칙이므로 초안을 덮어쓰지 않고 다음 판으로 낸다.
        # 팔 ZIP 두 개의 바이트는 v1 과 같다(러너는 쌍 ZIP 에만 들어간다) — 그래서 팔 이름은 v1 이다.
        "arms": ("G-A045", "G-A046"),
        "upload_id": "G-A045_A046",
        "release_id": "20260924_seed43_pair_full69_v8",
        "prefix": "go2_g_a045_a046",
        "upload_zip": "GO2_G_A045_A046_seed43_pair_full69_v8.zip",
        "tmux": "go2_seed_pair",
        "keep_name": "go2_seed_pair_a045_a046",
        "result_zip": "GO2_SEED_PAIR_RESULT.zip",
        "done_marker": "[DONE] GO2_SEED_PAIR_RESULT_READY",
        "guide": "GO2_G_A045_A046_ONE_COMMAND_RUN_GUIDE.txt",
        "plan": "workspace/training/quadruped/upload/plan/GO2_A045_SEED_PAIR_PLAN_20260924.md",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(work_id: str) -> dict:
    return json.loads(SPECS[work_id].read_text(encoding="utf-8"))


def prefix(spec: dict) -> Path:
    return Path("go2_" + spec["work_id"].lower().replace("-", "_"))


def upload_dir(pair: dict) -> Path:
    return GO2 / "upload" / pair["upload_id"]


def arm_output_path(pair: dict, spec: dict) -> Path:
    """팔 ZIP 도 발행물이다 — 쌍 ZIP 안에 실리고 history 에도 남는다."""
    return (upload_dir(pair) / "history" / pair["release_id"] / "arms"
            / spec["output"]["upload_zip"])


def output_path(pair: dict) -> Path:
    return upload_dir(pair) / "history" / pair["release_id"] / pair["upload_zip"]


def targets(spec: dict) -> list[str]:
    return length.targets(spec)


# ─────────────────────────────────────────────────────────────── 팔 검증

def validate_arm(spec: dict, pair: dict) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"spec {spec.get('work_id')}: {message}")

    need(spec.get("work_id") in SPECS, f"work_id must be one of {sorted(SPECS)}")
    need(spec.get("runner") == ARM_RUNNER, f"runner must be {ARM_RUNNER}")
    need(spec.get("change_class") == CHANGE_CLASS, f"change_class must be {CHANGE_CLASS}")
    # 승급 금지는 산문이 아니라 필드다.  `tools/test_go2_detectability_gate.py::test_11b` 가
    # 같은 것을 사양 쪽에서 검사하고, 여기서는 패키지가 나가기 전에 한 번 더 막는다.
    need(spec.get("promotion") == PROMOTION, f"promotion must be {PROMOTION}")
    need(bool(str(spec.get("promotion_reason", "")).strip()), "promotion_reason must be written")
    need(DECISION in (spec.get("open_decisions") or []),
         f"open_decisions must name {DECISION} — this round leans on that open reading")
    need(spec.get("plan") == pair["plan"], "plan must be the pair's plan")

    training = spec["training"]
    need(training == {"from_scratch": True, "seed": 43, "num_envs": 4096, "max_iterations": 1000},
         "training must be from scratch, seed 43, 4096 envs, 1000 iterations")
    baseline_training = json.loads(
        (EXPERIMENTS / "G_A044_a033_lin_vel_z_m175.json").read_text(encoding="utf-8"))["training"]
    need(training["seed"] != baseline_training["seed"],
         "the whole point is a seed the project has not trained at")
    need({key: value for key, value in training.items() if key != "seed"}
         == {key: value for key, value in baseline_training.items() if key != "seed"},
         "everything except the seed must equal the measured rounds' training block")

    base, cand_rewards = spec["rewards"]["baseline"], spec["rewards"]["candidate"]
    need(tuple(base) == REWARD_NAMES and tuple(cand_rewards) == REWARD_NAMES,
         f"reward keys/order must be {REWARD_NAMES}")
    changed = [name for name in REWARD_NAMES if float(base[name]) != float(cand_rewards[name])]
    single = spec["single_change"]
    role = spec["pair"]["role"]
    if role == "ruler":
        need(changed == [], f"the ruler arm must change no reward, got {changed}")
        need(single["name"] == "train_seed" and int(single["from"]) == baseline_training["seed"]
             and int(single["to"]) == training["seed"],
             "the ruler arm's single_change is the seed, 42 -> 43")
    else:
        need(changed == [single["name"]], f"exactly the single_change reward must differ, got {changed}")
        need(float(base[single["name"]]) == float(single["from"])
             and float(cand_rewards[single["name"]]) == float(single["to"]),
             "single_change from/to must match the reward table")
    need(bool(str(single.get("applied_by", "")).strip()), "single_change.applied_by must be written")

    # 기준선 블록은 저장된 G-A033 그대로여야 한다 — sentinel 과 영상 재사용이 그 위에 선다.
    baseline = spec["baseline"]
    need(baseline["name"] == "G-A033", "baseline must be the frozen G-A033 arm")
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

    # 평가·사전등록은 측정된 회차의 것을 그대로 쓴다.  이 회차는 자를 재는 회차이므로 자를 바꾸면 안 된다.
    ran = json.loads((EXPERIMENTS / "G_A033_a017_track_lin_vel_xy_150.json").read_text(encoding="utf-8"))
    for block in ("evaluation", "preregistered", "baseline", "videos", "output"):
        missing = sorted(set(ran[block]) - set(spec[block]))
        need(not missing, f"{block} lacks keys the verifier reads in G-A033: {missing}")
    a044 = json.loads((EXPERIMENTS / "G_A044_a033_lin_vel_z_m175.json").read_text(encoding="utf-8"))
    for key in ("min_total_points_delta", "max_flat_scenario_proxy_drop", "max_flat_case_survival_drop",
                "max_scenario_weighted_loss_70_by_scenario", "target_group_floor", "climb_guard",
                "target_groups", "rule_version", "target_axes", "guard_axes"):
        need(spec["preregistered"][key] == a044["preregistered"][key],
             f"preregistered.{key} must be G-A044's, unchanged — this round measures the ruler")
    need(spec["preregistered"]["plan_screening"]["version"]
         == a044["preregistered"]["plan_screening"]["version"],
         "the screening edition must be the one the measured rounds used")
    evaluation = spec["evaluation"]
    for key in ("seeds", "case_count", "num_envs", "steps", "checkpoint_iter", "catastrophe_case",
                "sentinel_cases", "sentinel_tolerance"):
        need(evaluation[key] == a044["evaluation"][key],
             f"evaluation.{key} must equal the measured rounds' — same ruler, different seed")

    need(length.collection_mode(spec) == length.FULL_COLLECTION,
         "this round collects all 69 in one pass (no stage 1, no gate)")
    need(set(spec.get("stages", {})) == {"full"}, "stages must be ['full']")

    videos = spec["videos"]
    for entry in [evaluation["catastrophe_case"], *evaluation["sentinel_cases"], *targets(spec),
                  *videos["candidate"], *videos["baseline"]]:
        need(bool(a030.ENTRY.match(entry)), f"bad case entry {entry!r}")
    need(videos["num_envs"] == 4 and videos["steps"] == 500, "videos are 4 envs x 500 steps")
    max_candidate, max_baseline = length.video_caps(spec)
    need(1 <= len(videos["candidate"]) <= max_candidate and len(videos["baseline"]) <= max_baseline,
         f"at most {max_candidate} candidate and {max_baseline} baseline videos")
    need(set(videos.get("reasons", {})) == set(videos["candidate"]),
         "every candidate video needs a reason")
    problems = length.reuse_problems(spec)
    need(problems == [], f"videos.baseline_reuse does not verify: {problems}")
    # 기준선 대응: 저장 팔에 있거나 · 여기서 찍거나 · 선언한 재사용이거나 · **짝 팔이 찍는다.**
    # 마지막 갈래가 이 모듈에만 있는 것이다 — 쌍 회차에서 같은 정책을 두 번 찍는 것은 GPU 낭비다.
    stored = ROOT / baseline["stored_arm"] / "evaluation" / baseline["stored_label"] / "videos"
    counterpart = videos.get("counterpart_arm")
    for entry in videos["candidate"]:
        scenario, case_id, seed = entry.split(":")
        covered = ((stored / f"{scenario}_{case_id}_seed_{seed}.mp4").is_file()
                   or entry in videos["baseline"]
                   or entry in (videos.get("baseline_reuse") or {}))
        need(covered or bool(counterpart),
             f"candidate video {entry} has no baseline counterpart and no counterpart arm")

    output = spec["output"]
    need(output["package_root"] == f"/workspace/{prefix(spec).as_posix()}",
         "package_root must match the ZIP prefix")
    need(output["tmux_name"] == prefix(spec).as_posix(), "tmux_name must be the prefix")
    need(bool(re.fullmatch(r"\[DONE\] [A-Z0-9_]{3,100}", output["done_marker"])), "bad done_marker")
    need(bool(re.fullmatch(r"GO2_G_A\d{3}_[a-z0-9_]+\.zip", output["upload_zip"])), "bad upload_zip")
    cand.check_release_version_in_zip_name(output, need)


# ─────────────────────────────────────────────────────────────── 팔 페이로드

def rendered_rewards(spec: dict) -> tuple[str, str]:
    """후보·기준선 보상 파일.  자 팔은 **같아야** 하고, 재현 팔은 한 줄만 달라야 한다."""
    template = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
    candidate = render_reward_source(template, spec["rewards"]["candidate"])
    reference = render_reward_source(template, spec["rewards"]["baseline"])
    if reward_dict(candidate) != spec["rewards"]["candidate"] \
            or reward_dict(reference) != spec["rewards"]["baseline"]:
        raise RuntimeError("rendered reward files do not read back as the spec")
    if spec["pair"]["role"] == "ruler":
        if candidate != reference:
            raise RuntimeError("the ruler arm must render a reward file identical to the baseline's")
        return candidate, reference
    differing = [(a, b) for a, b in zip(reference.splitlines(), candidate.splitlines()) if a != b]
    name = spec["single_change"]["name"]
    if len(reference.splitlines()) != len(candidate.splitlines()) or len(differing) != 1 \
            or f'"{name}"' not in differing[0][1]:
        raise RuntimeError(f"rendered reward files must differ in the {name} line only: {differing}")
    return candidate, reference


def run_config(spec: dict) -> str:
    text = a030.run_config(spec)
    text = text.replace(f"# generated by tools/build_go2_g_a030_package.py from {a030.SPEC.name}; do not edit",
                        f"# generated by tools/build_go2_seed_pair_package.py "
                        f"from {SPECS[spec['work_id']].name}; do not edit")
    text += "TARGET_CASES=(" + " ".join(shlex.quote(item) for item in targets(spec)) + ")\n"
    text += f"EVAL_CHECKPOINT_ITER={int(spec['evaluation']['checkpoint_iter'])}\n"
    if spec["preregistered"].get("plan_screening"):
        text += "COLLECT_REQUIRED_ON_STATIONARY=1\n"
    if length.collection_mode(spec) == length.FULL_COLLECTION:
        text += "GO2_STAGE=full\n"
    return text


def arm_payload(spec: dict, pair: dict) -> dict[str, bytes]:
    validate_arm(spec, pair)
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
    payload["baseline/quadruped_rewards.py"] = reference_rewards.encode("utf-8")
    payload["baseline/exported/model_best.pt"] = model
    payload["baseline/exported/env.yaml"] = env
    payload["go2_self_eval_registry.json"] = registry
    for name in a030.HELPERS:
        payload[name] = (GO2 / name).read_bytes()
    payload[spec["runner"]] = runner
    payload["run_config.env"] = run_config(spec).encode("utf-8")
    payload["experiment.json"] = SPECS[spec["work_id"]].read_bytes()
    payload["expected_rewards.json"] = (json.dumps(spec["rewards"], indent=2) + "\n").encode("utf-8")
    payload["README.txt"] = arm_readme(spec, pair).encode("utf-8")
    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def arm_readme(spec: dict, pair: dict) -> str:
    out, single, role = spec["output"], spec["single_change"], spec["pair"]["role"]
    videos = "\n".join(f"  {entry:26s} {spec['videos']['reasons'][entry]}"
                       for entry in spec["videos"]["candidate"])
    title = (f"GO2 {spec['work_id']} — seed 43 {role} arm of the pair {pair['upload_id']}")
    changes = ("NO REWARD WEIGHT CHANGES.  candidate/quadruped_rewards.py and\n"
               "  reference/baseline_quadruped_rewards.py are byte-identical, on purpose:\n"
               "  this arm is G-A033's reward file trained again at seed 43, so that the\n"
               "  difference from the stored G-A033 record is the training path alone."
               if role == "ruler" else
               f"  ONE reward weight: {single['name']} {single['from']} -> {single['to']},\n"
               f"  the value G-A043 measured at seed 42.  Inside this campaign the control is\n"
               f"  {spec['pair']['counterpart']}, which carries {single['from']} at the same seed 43.")
    return f"""{title}
{'=' * len(title)}

This package TRAINS one policy and then measures it over all 69 cases.  status: exploratory.

WHAT CHANGES
  TRAINING SEED 42 -> 43.  Deployed train/play/task code is unchanged; the seed is the
  CLI argument the deployed train.py forwards to Isaac Lab's rsl_rl train.py.
  {changes}

WHAT THIS ARM MAY NOT BECOME
  A submission candidate.  promotion: {spec['promotion']}.
  A training seed is not a reward weight, so nothing measured here can be promoted,
  whatever it scores.  The open reading is {DECISION} and it is the user's to close.

WHY (plan {Path(spec['plan']).name})
{chr(10).join('  ' + line for line in spec['why'])}

CHECKPOINT
  Evaluated at iter {spec['evaluation']['checkpoint_iter']} of {spec['training']['max_iterations']},
  the iteration G-A033 and G-A044 were evaluated at.  finalize's reward pick is kept as
  training/model_best_by_reward.pt and is not evaluated.

STAGES
  full only (~{spec['stages']['full']['estimate_minutes']}m): training, catastrophe gate, all 69 cases,
  {len(spec['evaluation']['sentinel_cases'])} sentinel cases, {len(spec['videos']['candidate'])} candidate videos,
  {len(spec['videos']['baseline'])} baseline videos, result ZIP.  There is no stage 1 and no server gate.

THIS ARM IS RUN BY THE PAIR RUNNER
  The campaign package {pair['upload_zip']} carries this ZIP and runs it with
  {RUNNER}.  Running this arm alone also works:
    bash {out['package_root']}/{spec['runner']}
  Done marker: {out['done_marker']}
  Result:      /workspace/_keep/{out['result_zip']}

VIDEOS (4 env x 500 steps)
{videos}

BASELINE ARM
  {spec['baseline']['stored_arm']} ({spec['baseline']['name']}, 42.52861/70 over 69 cases,
  trained at seed 42).  Its model and env ship here so the server can verify the sentinel
  cases re-measure the same policy with the same ruler.
"""


def arm_zip(spec: dict, pair: dict) -> bytes:
    payload = arm_payload(spec, pair)
    root = prefix(spec)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(payload):
            info = zipfile.ZipInfo((root / name).as_posix(), date_time=FIXED_TIMESTAMP)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload[name])
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────── 쌍 검증·페이로드

def validate_pair(pair: dict, specs: list[dict]) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"pair {pair['upload_id']}: {message}")

    need(len(specs) == 2, "a seed pair has exactly two arms")
    need(len({spec["work_id"] for spec in specs}) == 2, "arms must be distinct")
    ruler, replication = specs
    need(ruler["pair"]["role"] == "ruler" and replication["pair"]["role"] == "replication",
         "the ruler arm runs first: it is the one that can be compared with a stored record")
    need(ruler["pair"]["counterpart"] == replication["work_id"]
         and replication["pair"]["counterpart"] == ruler["work_id"],
         "each arm must name the other as its counterpart")
    for key in ("runner", "baseline", "evaluation", "preregistered", "stages", "training"):
        need(ruler[key] == replication[key], f"{key} must be identical across the arms")
    need(ruler["training"]["seed"] == replication["training"]["seed"],
         "both arms must train at the SAME new seed — that is what makes the pair symmetric")
    # 한 다이얼만 다르다.  이것이 쌍의 전부다.
    changed = [name for name in REWARD_NAMES
               if float(ruler["rewards"]["candidate"][name])
               != float(replication["rewards"]["candidate"][name])]
    need(changed == [replication["single_change"]["name"]],
         f"the two arms must differ in exactly the replication arm's dial, got {changed}")
    # 같은 목록을 찍어야 짝이 된다.  기준선 대응은 자 팔이 채운다.
    need(ruler["videos"]["candidate"] == replication["videos"]["candidate"],
         "both arms must film the identical case list, or the films are not a pair")
    need(not replication["videos"]["baseline"],
         "only the ruler arm films the stored baseline; filming it twice buys nothing")
    need(replication["videos"].get("counterpart_arm") == ruler["work_id"],
         "the replication arm must name which arm films its baseline counterparts")
    stored = ROOT / ruler["baseline"]["stored_arm"] / "evaluation" / ruler["baseline"]["stored_label"] / "videos"
    for entry in replication["videos"]["candidate"]:
        scenario, case_id, seed = entry.split(":")
        need((stored / f"{scenario}_{case_id}_seed_{seed}.mp4").is_file()
             or entry in ruler["videos"]["baseline"]
             or entry in (ruler["videos"].get("baseline_reuse") or {}),
             f"{entry} has no baseline counterpart anywhere in the pair")
    for key in ("package_root", "keep_dir_name", "result_zip", "tmux_name", "upload_zip", "done_marker"):
        values = [spec["output"][key] for spec in specs]
        need(len(set(values)) == len(values), f"output.{key} must differ between the arms")
    need("/workspace/" + pair["prefix"] not in [spec["output"]["package_root"] for spec in specs],
         "the campaign folder must not be an arm folder")
    for name, key in (("tmux", "tmux_name"), ("keep_name", "keep_dir_name"), ("result_zip", "result_zip")):
        need(pair[name] not in [spec["output"][key] for spec in specs],
             f"campaign {name} must not be an arm's")
    need((ROOT / pair["plan"]).is_file(), f"plan {pair['plan']} is not on disk")


def campaign_config(pair: dict, specs: list[dict], zips: dict[str, bytes]) -> str:
    names = [spec["output"]["upload_zip"] for spec in specs]

    def array(values: list[str]) -> str:
        return "(" + " ".join(shlex.quote(value) for value in values) + ")"

    return "".join([
        "# generated by tools/build_go2_seed_pair_package.py; do not edit\n",
        f"CAMPAIGN_ID={shlex.quote('+'.join(pair['arms']))}\n",
        f"CAMPAIGN_RELEASE_ID={pair['release_id']}\n",
        f"CAMPAIGN_TMUX={pair['tmux']}\n",
        f"CAMPAIGN_KEEP_NAME={pair['keep_name']}\n",
        f"CAMPAIGN_RESULT_ZIP={pair['result_zip']}\n",
        f"CAMPAIGN_DONE_MARKER={shlex.quote(pair['done_marker'])}\n",
        f"ARM_RUNNER={specs[0]['runner']}\n",
        f"ARM_WORK={array([spec['work_id'] for spec in specs])}\n",
        f"ARM_ZIP={array(names)}\n",
        f"ARM_ZIP_SHA={array([sha(zips[name]) for name in names])}\n",
        f"ARM_ROOT={array([spec['output']['package_root'] for spec in specs])}\n",
    ])


def readme(pair: dict, specs: list[dict], zips: dict[str, bytes]) -> str:
    arms = "\n".join(
        f"  {spec['work_id']}  {spec['pair']['role']:12s} lin_vel_z_l2 "
        f"{spec['rewards']['candidate']['lin_vel_z_l2']}  seed {spec['training']['seed']}   "
        f"arms/{spec['output']['upload_zip']}\n"
        f"           sha256 {sha(zips[spec['output']['upload_zip']])}"
        for spec in specs)
    root = "/workspace/" + pair["prefix"]
    title = f"GO2 {' + '.join(pair['arms'])} SEED PAIR — one upload, one command, one result"
    return f"""{title}
{'=' * len(title)}

This package TRAINS TWO policies, one after the other on one GPU, and measures each over
all 69 cases.  status: exploratory.  Plan: {Path(pair['plan']).name}.

WHAT IT MEASURES
  Both arms train at seed 43, a seed this project has never used:
  in every training this project has recovered the seed cell reads 42 (21 harvests record TRAIN_STATUS SEED=42; four older evaluation-only harvests record none, and no harvest anywhere records a different one).
    {specs[0]['work_id']} carries G-A033's reward file unchanged, so its distance from the stored
          G-A033 record is ONE sample of the seed difference AT THAT WEIGHT.
    {specs[1]['work_id']} carries lin_vel_z_l2 -1.5, the value G-A043 measured at seed 42, so
          (B - A) at the same seed is the dial's effect on a second training path.
  The two comparisons are symmetric with G-A033 <-> G-A043 at seed 42, which is what makes
  "did the effect repeat?" answerable.  It does NOT make "was G-A044's non-monotonic fall
  count caused by the dial or by the path?" answerable: this pair does not repeat -1.75.

HOW TO READ IT (plan section 4-2)
  Absolute level and paired difference are separate questions.  An arm reaching 50 of 96
  robots up two 15 cm steps says the behaviour appeared; only (B - A) at the same seed says
  the dial did it.  If A is already high and B is lower, the dial did not help there.

NEITHER ARM MAY BE PROMOTED
  promotion: {specs[0]['promotion']} (both arms).
  A training seed is not a reward weight, so this campaign cannot produce a submission
  candidate and the frozen baseline stays G-A033 whatever these arms score.
  That ban is OURS and conservative.  What is established is only that no deployed file is
  edited; that a CLI argument is passed through is not evidence that the rules permit the
  round, and we equally do not claim the rules forbid submitting a seed-43 policy.
  Open reading: {DECISION} - best closed by an organiser's answer or an explicit official
  basis, not by our reading alone.

WHAT WE CANNOT BOUND
  We cannot bound the downside ourselves.  If the organisers were to judge the server run itself as not permitted, whether the consequence stays inside this round is UNVERIFIED.  What is certain is only that the G-A033 artifacts are preserved; the scope of any sanction is undetermined.  This package does not claim the round is a violation - it claims that neither permission nor the size of the loss is established, and that a decision to run does not close the open reading.

ARMS (byte for byte what tools/build_go2_seed_pair_package.py builds)
{arms}

RUN
  unzip -oq {pair['upload_zip']} -d /workspace
  bash {root}/{RUNNER}
  Resume after an interruption: GO2_RESUME=1 bash {root}/{RUNNER}
  A resume never retrains over a half-finished training.  If it finds one it copies the
  logs, the pinned checkpoint and the training log into _keep/<arm>/training/interrupted_*
  and stops with TRAINING_STATE=INTERRUPTED_TRAINING_PRESERVED (rc 9).  Retraining from
  scratch over that copy is a separate, named choice: GO2_RESTART_TRAINING=1.
  A resume also re-runs any arm whose collection is not FULL_69_COMPLETE or whose result
  ZIP is missing or fails its checksum; only a verified, complete arm is skipped.

WHAT HAPPENS
  1 {specs[0]['work_id']} full stage (~95m): training 1000 iter, catastrophe gate, all 69 cases,
    the sentinel, {len(specs[0]['videos']['candidate'])} candidate videos and {len(specs[0]['videos']['baseline'])} baseline videos, its result ZIP.
  2 {specs[1]['work_id']} full stage (~95m): the same, with {len(specs[1]['videos']['candidate'])} candidate videos and no baseline
    videos - its counterparts were filmed in step 1 from the same stored policy.
  3 one result ZIP holding both arm result ZIPs and CAMPAIGN_STATUS.txt.
  There is no target gate and no arm gates the other: a failed arm is packaged with what
  it collected and the next arm runs.  Every verdict is read locally after recovery.

DOWNLOAD
  /workspace/_keep/{pair['result_zip']}
  /workspace/_keep/{pair['result_zip']}.sha256
  Finish marker: {pair['done_marker']}  (it is NOT printed on the crash path - see the guide)
  Official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def build_payload(pair_id: str) -> dict[str, bytes]:
    pair = PAIRS[pair_id]
    specs = [load(work) for work in pair["arms"]]
    for spec in specs:
        validate_arm(spec, pair)
    validate_pair(pair, specs)
    runner = (GO2 / RUNNER).read_bytes()
    if b"\r" in runner:
        raise RuntimeError("pair runner has CR bytes")
    zips = {spec["output"]["upload_zip"]: arm_zip(spec, pair) for spec in specs}
    payload: dict[str, bytes] = {RUNNER: runner}
    for name, data in zips.items():
        payload[f"arms/{name}"] = data
    payload["campaign_config.env"] = campaign_config(pair, specs, zips).encode("utf-8")
    payload["README.txt"] = readme(pair, specs, zips).encode("utf-8")
    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["CAMPAIGN_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def write_zip(path: Path, members: dict[str, bytes], root: str) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(f"{root}/{name}", date_time=FIXED_TIMESTAMP)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        names = archive.namelist()
        if len(names) != len(members):
            raise RuntimeError("member count mismatch")
        if any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise RuntimeError("unsafe member")
    built = temporary.read_bytes()
    temporary.unlink()
    # 발행물은 고치지 않는다 — 같은 release_id 로 다른 바이트가 나오면 다음 판으로 낸다.
    if path.exists() and path.read_bytes() != built:
        raise RuntimeError(f"immutable release conflict: {path} differs from this build")
    path.write_bytes(built)
    path.with_suffix(".zip.sha256").write_text(f"{sha(built)}  {path.name}\n",
                                               encoding="utf-8", newline="\n")
    return built


def keep_bytes(path: Path, data: bytes) -> None:
    """팔 ZIP 도 history 에 그대로 남긴다.  이미 있으면 바이트가 같아야 한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise RuntimeError(f"immutable release conflict: {path} differs from this build")
    path.write_bytes(data)
    path.with_suffix(".zip.sha256").write_text(f"{sha(data)}  {path.name}\n",
                                               encoding="utf-8", newline="\n")


def build(pair_id: str) -> Path:
    pair = PAIRS[pair_id]
    specs = [load(work) for work in pair["arms"]]
    payload = build_payload(pair_id)
    for spec in specs:
        name = spec["output"]["upload_zip"]
        keep_bytes(arm_output_path(pair, spec), payload[f"arms/{name}"])
    return output_path(pair) if write_zip(output_path(pair), payload, pair["prefix"]) else output_path(pair)


def run_guide(pair_id: str, digest: str) -> str:
    pair = PAIRS[pair_id]
    specs = [load(work) for work in pair["arms"]]
    root = "/workspace/" + pair["prefix"]
    upload_zip = pair["upload_zip"]
    keeps = [spec["output"]["keep_dir_name"] for spec in specs]
    works = [spec["work_id"] for spec in specs]
    readers = "\n".join(
        f"     python -B tools/verify_go2_basic_motion_harvest.py {spec['work_id']} \\\n"
        f"         --harvest workspace/_keep/{spec['output']['keep_dir_name']} \\\n"
        f"         --out workspace/_keep/{spec['output']['keep_dir_name']}/harvest_verification.json\n"
        f"     python -B tools/go2_screening_gate.py "
        f"--candidate workspace/_keep/{spec['output']['keep_dir_name']} \\\n"
        f"         --rule-version {spec['preregistered']['plan_screening']['version']}"
        for spec in specs)
    videos = ", ".join(entry.split(":")[1] for entry in specs[0]["videos"]["candidate"])
    return f"""GO2 {' + '.join(works)} 실행 안내 — 한 파일 · 한 명령 · 결과 ZIP 하나 (팔 둘)

이 회차는 점수를 올리려는 회차가 **아니다.** 같은 개선·부작용이 **두 번째 학습 seed 에서도
반복되는지**를 본다 — 원인을 확정하는 회차가 아니다.
두 팔 모두 학습 seed 43 으로 학습한다 — 이 프로젝트가 회수한 학습은 seed 칸이 전부 42 다 — 21건이 `TRAIN_STATUS.txt` 에 `SEED=42` 를 적고 있고, 기록이 없는 4건은 평가 전용·초기 suite 다. 42 아닌 학습 seed 기록은 0건.
  {works[0]}: G-A033 의 보상 파일 **그대로**. 저장된 G-A033(seed 42)과의 차이 = **그 값에서의** seed 차이 한 표본.
  {works[1]}: `lin_vel_z_l2 -1.5`(G-A043 과 같은 값). **같은 seed 의 {works[0]} 과의 차이(B−A)** = 다이얼 효과.
판독은 **절대 수준과 쌍 차이를 따로** 읽는다 — B 가 50/96 이상이면 그 행동이 나타난 것이고,
다이얼이 올렸다고 말하려면 **같은 seed 의 B−A** 가 seed 42 의 (A043−A033)과 같은 방향이어야 한다(계획 §4-2).
이 쌍은 `-1.75` 를 반복하지 않으므로 **A044 의 비단조 원인은 이 회차로 확정되지 않는다.**
**두 팔 다 승급 대상이 아니다**(promotion: {specs[0]['promotion']}) — 기준선은 G-A033 그대로다.
이 금지는 **우리 내부의 보수 규칙**이다. 확인된 것은 배포 파일이 바뀌지 않는다는 사실뿐이고,
CLI 인자가 전달된다는 것이 규정 허용의 증거는 아니며, 반대로 seed 43 정책이 공식적으로 제출 불가라고
단정하지도 않는다. R-6 해석은 열린 결정 {DECISION} 이고 **사용자 해석보다 운영진 답변·공식 근거로
닫는 것이 안전하다.** 서버 실행도 사용자 결정이다.
**손실 상한도 우리가 정할 수 없다** — 서버 실행 자체가 허용되지 않는 행위로 판정될 경우 그 영향이
이 회차에만 머무는지는 확인되지 않았다. 확실한 것은 G-A033 산출물이 보존된다는 것뿐이고 제재 범위는
**미확정**이다. 실행 결정만으로 이 해석이 닫히지도 않는다.
계획서: {pair['plan']}

1. 업로드 — 이 파일 하나만 올린다
   {upload_zip}
   SHA256 {digest}
   서버 경로 /workspace/{upload_zip}

2. 실행 — 한 줄
   unzip -oq /workspace/{upload_zip} -d /workspace && bash {root}/{RUNNER}

   끊겼을 때 이어서: GO2_RESUME=1 bash {root}/{RUNNER}
   **이어서 실행은 미완료 학습을 절대 덮어쓰지 않는다.** 미완료 학습을 만나면 로그·고정
   checkpoint·학습 로그를 `_keep/<팔>/training/interrupted_*` 로 복사하고
   `TRAINING_STATE=INTERRUPTED_TRAINING_PRESERVED`(rc 9)로 **멈춘다**. 그 위에 처음부터
   다시 학습하는 것은 별도 선택이다: `GO2_RESTART_TRAINING=1 GO2_RESUME=1 bash ...`
   수집이 `FULL_69_COMPLETE` 가 아니거나 결과 ZIP 이 없거나 SHA 가 안 맞는 팔은
   **건너뛰지 않고 다시 돈다**(결함 C-28).
   진행 보기:       tmux attach -t {pair['tmux']}
   진행 기록:       /workspace/_keep/{pair['keep_name']}/CAMPAIGN_LOG.txt

3. 무엇이 도는가 — 1단계도 서버 게이트도 없고, 팔이 팔을 막지도 않는다
   {works[0]} 학습 1000 iter -> 파국 게이트 -> 69 case 전부 -> sentinel 5 -> 영상 {len(specs[0]['videos']['candidate'])}+{len(specs[0]['videos']['baseline'])} -> 팔 결과 ZIP
   {works[1]} 같은 순서, 영상 {len(specs[1]['videos']['candidate'])}편(기준선 대응은 {works[0]} 이 이미 찍었다)
   -> 두 팔 결과를 묶은 결과 ZIP 하나.
   영상 case: {videos}
   **팔당 약 95분, 합쳐 약 190분**으로 본다(A044 실측 94분/1팔·학습 58분 21초 기준).
   **서버 세션은 240~300분으로 잡는다** — 위는 도는 시간이고 회수는 그 뒤에 온다(계획 §7).
   한 팔이 실패해도 그 팔이 모은 것은 포장되고 다음 팔이 돈다. 고를 승자가 없으므로 게이트가 없다.

4. 완료 표식과 내려받을 것 — 표식은 「회수 준비」이지 「전수 완료」가 아니다
   [DONE] 표식: {pair['done_marker']}
   /workspace/_keep/{pair['result_zip']}
   /workspace/_keep/{pair['result_zip']}.sha256
   **[DONE] 은 결과 ZIP 이 만들어졌다는 뜻뿐이고, 늘 나오는 것도 아니다.** 러너가 도중에 죽으면
   `on_exit` 가 부분 ZIP 을 만들고 끝난다 — **그 판에는 [DONE] 이 없다.** 표식 하나를 기다리지 말고
   팔마다 아래 세 상태를 구분한다. 팔의 상태는
   `_keep/{pair['keep_name']}/CAMPAIGN_STATUS.txt` 의 `<팔>_STATE`·`<팔>_COLLECTION` 과
   각 팔의 `_keep/<팔 폴더>/RESULT_STATUS.txt`·`RUNNER_STATUS.txt` 의 `COLLECTION_STATUS` 에 적힌다.

   ① 정상 완료 — COLLECTION_STATUS=FULL_69_COMPLETE
      **이것은 개수 확인이다.** SHA · 지문 · identity · report 검사를 대신하지 않는다.
   ② 복구 가능한 수집 누락 — COLLECTION_STATUS=INCOMPLETE_COLLECTION
      로그에 `[INCOMPLETE COLLECTION]` 두 줄이 함께 찍힌다. 서버가 살아 있을 때만 메울 수 있다.
   ③ crash · 안전상 평가 불가 — INCOMPLETE_CRASH(표식 없음) 또는 INCOMPLETE_EARLY_STOP
      **여기서는 69 를 채우지 않는다.** 파국 게이트가 멈춘 판은 정책이 실행되지 않은 판이고,
      자료를 얻자고 시뮬레이터를 다시 띄우지 않는 것이 러너의 계약이다. 회수 가능한 것
      (학습 로그 · checkpoint · env.yaml · exported/report.html · 거기까지의 telemetry)을 보존하고
      결측을 적은 뒤 종료를 판단한다. 이 판은 「성능 실패」가 아니라 「판정 불가」다.
   ④ 학습이 끊긴 채 재개됨 — TRAINING_STATE=INTERRUPTED_TRAINING_PRESERVED (rc 9)
      `_keep/<팔>/training/TRAINING_RESUME_STATUS.txt` 와 `interrupted_<시각>/` 이 남는다.
      **자료는 그대로 있고 GPU 시간도 더 쓰지 않았다.** 그 팔을 지금 상태로 내려받든지,
      `GO2_RESTART_TRAINING=1` 로 재학습을 **명시적으로** 지시한다. 둘 다 사용자 결정이다.
   **한 팔이 ③ 이어도 다른 팔의 상태는 따로 읽는다.** 한 팔만 성공하면 그 팔의 자료는 그대로
   회수하되, 쌍 비교는 성립하지 않는다 — 그 사실을 결측으로 적는다.

5. SERVER SHUTDOWN GATE — SHA 일치만으로 끄지 않는다
   아래 다섯 줄이 **두 팔 모두** 채워진 뒤에 끈다(루트 AGENTS.md 「학습 종료 후 영상 증거 게이트」).
   a. 결과 ZIP {pair['result_zip']} 과 .sha256 로컬 도착 · SHA 일치, 그리고 팔마다
      `COLLECTION_STATUS` 를 §4 의 세 상태 중 하나로 읽었다.
   b. 팔마다 원 학습 report.html = REPORT_ACQUIRED, 그리고 같은 학습의 env.yaml · 로그 · checkpoint
   c. 팔마다 69 case telemetry 전부와 sentinel 5 case
   d. 영상: {works[0]} {len(specs[0]['videos']['candidate'])}+{len(specs[0]['videos']['baseline'])}편 · {works[1]} {len(specs[1]['videos']['candidate'])}편의 파일과 지문 도착,
      SHA 로 재사용하는 저장본 {len(specs[0]['videos'].get('baseline_reuse') or {{}})}편의 대조 성공
   e. 아래 로컬 판독 네 줄을 실제로 실행하고 그 verdict 를 기록했다
   하나라도 비면 종료 불가다 — 단 §4 ③ 은 예외다. 거기서는 없는 자료를 만들 수 없으므로
   게이트는 「전부 채웠다」가 아니라 「무엇이 없고 왜 없는지 적었다」로 닫는다.

   로컬 판독 (GPU 0):
{readers}
   **exit code 만으로 성능도 서버 종료 여부도 판단하지 않는다.** 첫 명령은 성능 FAIL 에도 exit 0 이고
   (판정을 했다는 뜻), exit 1 은 INCONCLUSIVE·BASELINE_REMEASURE_REQUIRED — 즉 **판정을 못 했다**는
   뜻이다. 그때 볼 것은 성능이 아니라 `artifact_faults`·`ruler_mismatches` 이고, 그 결손은 서버가
   살아 있을 때만 메운다. 둘째 명령은 FAIL 과 INCONCLUSIVE 가 같은 exit 1 이므로 이름으로 구분한다.
   **이 회차에서 screening 판정은 「자」에 대한 증거이지 후보 채택·기각의 근거가 아니다**
   (기준 문서 reports/GO2_A045_CRITERIA_CHANGES_20260924.md §2-4).

6. 이 패키지가 보장하지 않는 것
   점수 이득을 약속하지 않는다. seed 두 개는 분포가 아니다 — 이 회차가 주는 것은 **표본 하나**이고,
   그것으로 분산을 추정했다고 쓰지 않는다.
   **A044 의 비단조 원인을 확정하지 않는다** — 이 쌍은 `-1.75` 를 반복하지 않는다.
   **기존 판정을 무효로 만들지 않는다** — A042·A043·A044 의 INTERNAL_GATE_FAIL 은 그 조건의 관측이다.
   차이가 크게 나와도 승급 규칙을 폐기하거나 자동으로 장기 학습에 들어가지 않는다(계획 §4-1).
   승급은 두 팔 모두 금지다. 공식 결과는 OFFICIAL_RESULT_UNMEASURED 다.
"""


def publish(pair_id: str, zip_path: Path) -> None:
    pair = PAIRS[pair_id]
    digest = sha(zip_path.read_bytes())
    current = upload_dir(pair) / "current"
    current.mkdir(parents=True, exist_ok=True)
    for stale in current.glob("*"):
        if stale.is_file():
            stale.unlink()
    (current / zip_path.name).write_bytes(zip_path.read_bytes())
    (current / (zip_path.name + ".sha256")).write_text(f"{digest}  {zip_path.name}\n",
                                                       encoding="utf-8", newline="\n")
    (current / pair["guide"]).write_text(run_guide(pair_id, digest), encoding="utf-8", newline="\n")
    # 발행 이력은 다른 빌더와 같은 표에 같은 모양으로 남긴다 — 나중에 어느 판을 올렸는지 읽는 자리다.
    ledger = upload_dir(pair) / "UPLOAD_HISTORY.tsv"
    header = ("published_at_utc\texperiment_id\trelease_id\tstatus\tengine_file\tengine_sha256\tnote\n")
    note = ("seed 43 pair; both arms promotion-forbidden (training_seed); "
            f"open decision {DECISION}; no server run")
    row = "\t".join([PUBLISHED_AT, "+".join(pair["arms"]), pair["release_id"], "ARTIFACT_VERIFIED",
                     pair["upload_zip"], digest, note]) + "\n"
    existing = ledger.read_text(encoding="utf-8") if ledger.exists() else header
    if row not in existing:
        ledger.write_text(existing + row, encoding="utf-8", newline="\n")
    print(f"  published  {current.relative_to(ROOT)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pair_id", choices=sorted(PAIRS))
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args(argv)

    pair = PAIRS[args.pair_id]
    zip_path = build(args.pair_id)
    digest = sha(zip_path.read_bytes())
    print(f"{args.pair_id}: {' + '.join(pair['arms'])}")
    for work in pair["arms"]:
        spec = load(work)
        print(f"  arm {work}  seed {spec['training']['seed']}  "
              f"lin_vel_z_l2 {spec['rewards']['candidate']['lin_vel_z_l2']}  "
              f"promotion {spec['promotion']}")
    print(f"  {zip_path.relative_to(ROOT)}")
    print(f"  sha256 {digest}  ({zip_path.stat().st_size} bytes)")
    if args.publish:
        publish(args.pair_id, zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
