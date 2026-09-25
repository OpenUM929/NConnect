"""Build (and optionally publish) a one-reward-change arm package on the frozen baseline G-A033.

G-A037 is the first reward change on G-A033.  Neither existing builder can express it:
  tools/build_go2_candidate_package.py asserts G-A030's A017 baseline;
  tools/build_go2_training_length_package.py asserts that no reward moves.
Both have released output, so neither is loosened.  This module keeps its own validation (exactly
one reward differs, it is the single_change, the value derivation and the rejected alternatives
are written down) and reuses everything else from the training-length builder byte for byte: the
iteration-pinned runner, the deployed source files, the evaluator, the registry and the stored
G-A033 model/env.

    python tools/build_go2_a033_reward_package.py G-A037            # build and verify
"""

from __future__ import annotations

import argparse
import ast
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
import build_go2_training_length_package as length  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

EXPERIMENTS = length.EXPERIMENTS
SPECS = {"G-A037": EXPERIMENTS / "G_A037_a033_lin_vel_z_m1.json",
         "G-A038": EXPERIMENTS / "G_A038_a033_ang_vel_xy_m008.json",
         "G-A039": EXPERIMENTS / "G_A039_a033_dof_acc_m125e7.json",
         # 2026-09-19: flat_orientation_l2 0.0 -> -0.5.  Unlike G-A039 this is one of the six names in the
         # deployed REWARD_WEIGHTS list, so change_class is reward_weight and no open decision is involved.
         "G-A040": EXPERIMENTS / "G_A040_a033_flat_orientation_m05.json",
         # 2026-09-20: ang_vel_xy_l2 -0.05 -> -0.04, the relaxation side of the one dial whose
         # strengthening was measured against the climbed-robot counter (90 -> 5 at G-A038).  Also one
         # of the six deployed names, so change_class is reward_weight and no open decision applies.
         "G-A041": EXPERIMENTS / "G_A041_a033_ang_vel_xy_m004.json",
         # 2026-09-21: track_lin_vel_xy_exp 1.5 -> 1.6, the first arm built from a user plan
         # (upload/plan/GO2_FORWARD_STAIRS_POLICY_20260921.md, G-D-FORWARD-STAIRS-20260921).  It is
         # also the first spec to carry preregistered.required_target_cases: the 15 cm stairs are
         # measured in stage 1 whatever the gate decides, because G-A041 lost that height entirely
         # when its target stage failed.
         "G-A042": EXPERIMENTS / "G_A042_a033_track_lin_vel_xy_160.json",
         # 2026-09-22: lin_vel_z_l2 -2.0 -> -1.5, the arm the plan after G-A042 selected
         # (upload/plan/GO2_POST_A042_PLAN_20260922.md).  Same dial as the held G-A037 (-1.0) at half
         # the step, and the first spec whose plan screening guards both G6 x directions, which is why
         # push_neg_x sits at three seeds in required_target_cases and both push cases are filmed.
         "G-A043": EXPERIMENTS / "G_A043_a033_lin_vel_z_m15.json",
         # 2026-09-22: lin_vel_z_l2 -2.0 -> -1.75, the arm the plan written after G-A043's failure
         # selected (upload/plan/GO2_POST_A043_PLAN_20260922.md sections 1-2).  Same dial as G-A043 at
         # half its step.  Two things are new: the run collects all 69 cases in ONE pass with no
         # target stage and no server gate (collection.mode full_69_single_stage, plan section 5),
         # and the plan screening edition post_a043_push4_v1 guards all four G6 push directions
         # (plan section 6).  Both come from G-A043's readout: its decisive loss sat outside the
         # 23-case stage 1 and was only visible after the full suite ran (defect C-11).
         "G-A044": EXPERIMENTS / "G_A044_a033_lin_vel_z_m175.json"}
# 2026-09-18: a reward term that is NOT one of the six names in the deployed REWARD_WEIGHTS list.
# go2_tuning_config.REWARD_NAMES is read-only and holds those six, so such an arm cannot be rendered
# by replacing a number; it adds one line to the deployed dict.  go2_task/env_cfg.py applies any name
# that is a RewTerm of the env, so the server proves it with '[OK] <name>.weight = <value>'.
# 배포 REWARD_WEIGHTS 6개 목록 밖의 env RewTerm 보상 항.  이 분류를 R-6 안으로 보는 해석은
# 우리가 내린 것이고 사용자 승인 전이다 — 열린 결정 U1-R6-ENV-REWARD-20260918
# (workspace/training/quadruped/reports/GO2_OPEN_DECISIONS.md).
# 2026-09-22 (G-A043): 이 상한은 규정이 아니라 우리 구현이고, 21 은 근거 없는 수였다.  지키려는
# 것은 "1단계가 2단계 몫까지 삼키지 않는다"이므로 평가 전체(69 case)의 1/3 로 묶는다.  수는 시간·
# 비용의 적절성을 증명하지 않는다 — 1단계가 전체의 3분의 1을 넘지 않는다는 **운영 선택**이고,
# 실제 소요는 회차 사양의 `stages.target.estimate_minutes` 와 회수 기록으로 따로 본다.
# 세는 범위는 1단계가 실제로 재는 목록과 같다: 파국 case 1 + 채점 표적 + 필수 기록
# (verify_go2_basic_motion_harvest.target_stage_entries).  G-A043 이 파국 1 + 12 + 10 = 23 을 재는
# 이유는 그 회차 사양과 `reports/GO2_G_A043_CRITERIA_CHANGES_20260922.md` §2 에 있다 — 밀침 예측은
# 네 방향(`go2_reward_mechanism.PUSH_CASES`)에서 계산되므로 ±y 표지를 빼고 ±x 만 재는 것은 근거와
# 측정 범위가 어긋난다.  회차별로 이 수를 덮어쓰는 필드는 두지 않는다(공통 상한 + 회차별 고정
# 목록은 함께 성립하고, 지금 구조가 그것이다).
MAX_STAGE1_CASES = 23
ENV_REWARD_CLASS = "env_reward_weight"
CHANGE_CLASSES = ("reward_weight", ENV_REWARD_CLASS)
RUNNER = length.RUNNER
BASELINE_SOURCE = length.BASELINE_SOURCE
SAVE_INTERVAL = length.SAVE_INTERVAL
FIXED_TIMESTAMP = length.FIXED_TIMESTAMP
PUBLISHED_AT = length.PUBLISHED_AT
ENTRY = length.ENTRY
EVIDENCE = GO2 / "reports" / "evidence" / "go2_stairs_behavior_20260916"
MECHANISM = GO2 / "reports" / "evidence" / "go2_reward_mechanism_20260917"
# Each arm says where its value came from in its own terms, and names the levers its analysis looked
# at but did not move.  G-A037 derived its value from the climb table (stairs analysis 8-2); G-A038
# from the reward-mechanism forecast (walk margin and the three situation margins, 2026-09-17).
DERIVATION = {
    "G-A037": (("source", "measured_10cm_share", "estimated_15cm_share", "rule", "not_claimed"),
               (EVIDENCE / "CLIMB_REWARD.csv",),
               {"ang_vel_xy_l2", "track_lin_vel_xy_exp", "feet_air_time"}),
    "G-A038": (("source", "role", "walk_margin", "situations", "rule", "not_claimed"),
               (MECHANISM / "RUN_MARGIN.csv", MECHANISM / "SITUATIONS.csv", MECHANISM / "PROBE_SITUATIONS.csv"),
               {"lin_vel_z_l2", "flat_orientation_l2", "track_lin_vel_xy_exp", "feet_air_time", "dof_acc_l2"}),
    # G-A039 derives its value from the probe grid and from the raw joint acceleration of every run;
    # it must also say why each of the six deployed names stayed put, since it reaches past that list.
    "G-A039": (("source", "role", "walk_margin", "situations", "rule", "not_claimed"),
               (MECHANISM / "PROBES.csv", MECHANISM / "TERM_VALUES.csv"),
               {"lin_vel_z_l2", "flat_orientation_l2", "track_lin_vel_xy_exp", "feet_air_time",
                "ang_vel_xy_l2", "action_rate_l2"}),
    # G-A040 derives its value from the fall-channel split of the 2026-09-19 re-read (which channel of
    # the posture gate ends G3), from the term's own formula values in TILT.csv, and from the situation
    # probe grid.  It must also say why every other analysed lever stayed put, including dof_acc_l2,
    # because it overtakes G-A039 in order.
    "G-A040": (("source", "role", "walk_margin", "situations", "rule", "not_claimed"),
               (GO2 / "reports/evidence/go2_a038_reread_20260919/FALL_CHANNEL_ROLLUP.csv",
                GO2 / "reports/evidence/go2_a038_reread_20260919/ROUGH_LATERAL_ROLLUP.csv",
                MECHANISM / "TILT.csv", MECHANISM / "SITUATIONS.csv", MECHANISM / "PROBE_SITUATIONS.csv"),
               {"lin_vel_z_l2", "ang_vel_xy_l2", "track_lin_vel_xy_exp", "feet_air_time",
                "action_rate_l2", "dof_acc_l2"}),
    # G-A041 derives its value from the climbed-robot counter that measured this dial once (CLIMB_COUNT.csv),
    # from the stall behaviour behind that count (STAIRS10_ROLLUP.csv) and from the probe grid extended to the
    # relaxation side on 2026-09-20 (PROBES.csv, PROBE_SITUATIONS.csv).  It must also say why every other
    # analysed lever stayed put, including flat_orientation_l2, because G-A040 aims the axis with the larger
    # recoverable deduction and this arm does not overtake it on points.
    "G-A041": (("source", "role", "walk_margin", "situations", "rule", "not_claimed"),
               (GO2 / "reports/evidence/go2_a038_reread_20260919/CLIMB_COUNT.csv",
                GO2 / "reports/evidence/go2_a038_reread_20260919/STAIRS10_ROLLUP.csv",
                MECHANISM / "PROBES.csv", MECHANISM / "PROBE_SITUATIONS.csv"),
               {"lin_vel_z_l2", "flat_orientation_l2", "track_lin_vel_xy_exp", "feet_air_time",
                "action_rate_l2", "dof_acc_l2"}),
    # G-A042 uses one equal-checkpoint comparison and an unequal-checkpoint supporting observation:
    # A017->A033 is 900/900; Pilot->A017 is 999/900, not a replication. The climbed-robot
    # counts of the stairs analysis (STAIRS_CLIMB.csv) and the per-case behaviour of the same harvest
    # (CASE_BEHAVIOR.csv, which carries both the rough forward gain and the side-step loss), plus the
    # probe grid at 1.6.  It must also say why every other analysed lever stayed put, including
    # ang_vel_xy_l2, because G-A041 measured that dial's relaxation and it did not move the stairs.
    "G-A042": (("source", "role", "walk_margin", "situations", "rule", "not_claimed"),
               (EVIDENCE / "STAIRS_CLIMB.csv", EVIDENCE / "CASE_BEHAVIOR.csv",
                MECHANISM / "PROBES.csv", MECHANISM / "PROBE_SITUATIONS.csv"),
               {"lin_vel_z_l2", "flat_orientation_l2", "ang_vel_xy_l2", "feet_air_time",
                "action_rate_l2", "dof_acc_l2"}),
    # G-A043 derives its value from the per-group penalty shares of G-A033's own climb records
    # (CLIMB_REWARD.csv, which carries both the supporting gap and the contradicting 15 cm row), from the
    # climbed-robot counts it must protect (STAIRS_CLIMB.csv) and from the probe grid extended to -1.5 on
    # 2026-09-22.  It must also say why every other analysed lever stayed put, including
    # track_lin_vel_xy_exp, because G-A042 just measured that dial and failed.
    "G-A043": (("source", "role", "walk_margin", "situations", "rule", "not_claimed"),
               (EVIDENCE / "CLIMB_REWARD.csv", EVIDENCE / "STAIRS_CLIMB.csv",
                MECHANISM / "PROBES.csv", MECHANISM / "PROBE_SITUATIONS.csv"),
               {"track_lin_vel_xy_exp", "flat_orientation_l2", "ang_vel_xy_l2", "feet_air_time",
                "action_rate_l2", "dof_acc_l2"}),
    # G-A044 is the first arm on this dial whose baseline data has TWO walking observations
    # (-2.0 from every earlier run, -1.5 from G-A043), so its value derivation rests on the
    # scenario split of G-A043's own harvest as well as the climb table and the probe grid.
    "G-A044": (("source", "role", "walk_margin", "situations", "rule", "not_claimed"),
               (GO2 / "reports/evidence/go2_a043_scenario_split_20260922/SCENARIO_SPLIT.csv",
                GO2 / "reports/evidence/go2_a043_scenario_split_20260922/CASE_DELTAS.csv",
                EVIDENCE / "STAIRS_CLIMB.csv", MECHANISM / "PROBES.csv",
                MECHANISM / "PROBE_SITUATIONS.csv"),
               {"track_lin_vel_xy_exp", "flat_orientation_l2", "ang_vel_xy_l2", "feet_air_time",
                "action_rate_l2", "dof_acc_l2"}),
}
sha = length.sha
prefix = length.prefix


def targets(spec: dict) -> list[str]:
    """The cases the target stage measures: the scored groups, then the required records.

    2026-09-21 (G-A042).  G-A041 came back with recovery PARTIAL: its spec required the 15 cm stairs
    records, its target stage failed, the full stage never ran, and the height was never measured.
    The server gate and the local verifier score `preregistered.target_groups`; the runner measures
    whatever `run_config.env` lists.  So a case that must be recorded whatever the verdict goes in
    `preregistered.required_target_cases`: measured in stage 1, scored by no gate.  A spec without
    the key behaves exactly as before, which is why the released arms rebuild byte for byte.
    """
    return [*length.targets(spec), *(spec["preregistered"].get("required_target_cases") or [])]


def load(work_id: str) -> dict:
    return json.loads(SPECS[work_id].read_text(encoding="utf-8"))


def output_path(spec: dict) -> Path:
    out = spec["output"]
    return GO2 / "upload" / spec["work_id"] / "history" / out["release_id"] / out["upload_zip"]


def validate_spec(spec: dict) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"spec {spec.get('work_id')}: {message}")

    need(spec.get("work_id") in SPECS, f"work_id must be one of {sorted(SPECS)}")
    need(spec.get("change_class") in CHANGE_CLASSES, f"change_class must be one of {CHANGE_CLASSES}")

    base, cand_rewards = spec["rewards"]["baseline"], spec["rewards"]["candidate"]
    need(tuple(base) == REWARD_NAMES and tuple(cand_rewards) == REWARD_NAMES,
         f"reward keys/order must be {REWARD_NAMES}")
    changed = [name for name in REWARD_NAMES if float(base[name]) != float(cand_rewards[name])]
    single = spec["single_change"]
    if spec["change_class"] == ENV_REWARD_CLASS:
        # The six listed names do not move; exactly one env term outside the list does.  Its baseline
        # value is whatever Isaac Lab Go2 rough applies, checked against the reference JSON below.
        extra = spec["rewards"].get("candidate_env_extra") or {}
        need(changed == [], f"an env reward arm must not move a listed name, got {changed}")
        need(not (spec["rewards"].get("baseline_env_extra") or {}),
             "baseline_env_extra must be empty: the baseline is the deployed six plus Isaac Lab defaults")
        need(list(extra) == [single["name"]], f"candidate_env_extra must hold exactly {single['name']}")
        need(single["name"] not in REWARD_NAMES,
             f"{single['name']} is a listed name; use change_class reward_weight for it")
        need(float(extra[single["name"]]) == float(single["to"]),
             "candidate_env_extra value must equal single_change.to")
        need("go2_task/env_cfg.py" in str(single.get("applied_by", "")),
             "single_change.applied_by must name the env override path that applies the weight")
    else:
        need(changed == [single["name"]], f"exactly the single_change reward must differ, got {changed}")
        need(float(base[single["name"]]) == float(single["from"]) and float(cand_rewards[single["name"]]) == float(single["to"]),
             "single_change from/to must match the reward table")

    # The baseline rewards are G-A033's, read from the file it was trained with -- not typed here.
    trained = BASELINE_SOURCE / "source" / "quadruped_rewards.py"
    if trained.is_file():
        need(reward_dict(trained.read_text(encoding="utf-8")) == base,
             "baseline rewards must be the rewards G-A033 was trained with")

    training = spec["training"]
    need(training == {"from_scratch": True, "seed": 42, "num_envs": 4096, "max_iterations": 1000},
         "training must be G-A033's: from scratch, seed 42, 4096 envs, 1000 iterations")
    need(spec["evaluation"].get("checkpoint_iter") == 900,
         "evaluation.checkpoint_iter must be 900, the iteration G-A033 was evaluated at")

    # Everything the training-length builder checks about the baseline, the readers' keys, the
    # cases, videos, thresholds and output names applies unchanged.  It is run on a copy whose
    # reward and training blocks are the ones it accepts, so no check is duplicated here.
    shaped = json.loads(json.dumps(spec))
    shaped["work_id"] = "G-A035"
    shaped["change_class"] = "training_length"
    shaped["rewards"] = {"baseline": dict(base), "candidate": dict(base)}
    shaped["single_change"] = {"name": "max_iterations", "from": 1000, "to": 1050}
    shaped["training"] = {**training, "max_iterations": 1050}
    shaped["evaluation"] = {**spec["evaluation"], "checkpoint_iter": 1000}
    shaped["external_reference"] = {"term": "max_iterations", "isaaclab_go2_rough": 1500,
                                    "isaaclab_go2_flat": 300, "candidate": 1050}
    shaped["output"] = {**spec["output"], "package_root": "/workspace/go2_g_a035", "tmux_name": "go2_g_a035"}
    length.validate_spec(shaped)
    out = spec["output"]
    need(out["package_root"] == f"/workspace/{prefix(spec).as_posix()}", "package_root must match the ZIP prefix")
    need(out["tmux_name"] == prefix(spec).as_posix(), "tmux_name must be the prefix")

    # G-D-EXTREF-20260915: the external comparison agrees with the reference JSON, and a departure
    # from Isaac Lab carries its reason.
    ext = spec.get("external_reference") or {}
    rough = json.loads(length.EXTREF.read_text(encoding="utf-8"))["isaaclab"]["rewards"]["go2_rough"]
    need(ext.get("term") == single["name"], "external_reference.term must be the single_change")
    need(float(ext.get("isaaclab_go2_rough")) == float(rough[single["name"]]),
         "external_reference.isaaclab_go2_rough must equal the reference JSON")
    need(float(ext.get("baseline")) == float(single["from"]) and float(ext.get("candidate")) == float(single["to"]),
         "external_reference baseline/candidate must equal the single_change")
    if float(single["to"]) != float(rough[single["name"]]):
        need(bool(str(ext.get("departure_reason", "")).strip()), "a departure from Isaac Lab needs departure_reason")
    if spec["change_class"] == ENV_REWARD_CLASS:
        # A term the deployed list never carried has never been overridden, so its baseline is the
        # Isaac Lab Go2 rough value itself -- not a number we may type freely.
        need(float(single["from"]) == float(rough[single["name"]]),
             "an unlisted term starts at its Isaac Lab Go2 rough value")

    # The value must say where it came from, and the evidence it cites must exist.
    derivation = spec.get("value_derivation") or {}
    keys, cited, analysed = DERIVATION[spec["work_id"]]
    for key in keys:
        need(bool(str(derivation.get(key, "")).strip()), f"value_derivation.{key} is required")
    for path in cited:
        need(path.is_file(), f"value_derivation cites {path.name}, which is absent")
    need(set(spec.get("rejected_alternatives", {})) >= analysed,
         "rejected_alternatives must say why the other analysed levers were not moved")

    prereg = spec["preregistered"]
    by_scenario = prereg.get("max_scenario_weighted_loss_70_by_scenario") or {}
    need(set(by_scenario) == {"G3", "G4", "G5", "G6", "G7"},
         "max_scenario_weighted_loss_70_by_scenario must cover every non-flat scenario")
    need(all(float(v) > 0 for v in by_scenario.values()), "per-scenario limits must be positive")

    # Cases measured in stage 1 but scored by no gate (see targets()).  They are only worth having
    # if they are real cases, distinct from the scored ones, readable against the stored baseline,
    # and accompanied by the reason they are not a group -- otherwise a gate has been dropped
    # silently, which is the thing defect S-2 was about.
    required = prereg.get("required_target_cases") or []
    # 2026-09-22 (G-A044, 계획 §5).  전수 수집 회차는 1단계 분기 자체가 없다 — 그러면 "1단계에서만 재는
    # 필수 기록" 이라는 개념이 성립하지 않고, `stages.target` 도 있어서는 안 된다.  두 가지가 함께
    # 선언되면 사람이 읽는 문서와 서버가 하는 일이 갈라진다.
    if length.collection_mode(spec) == length.FULL_COLLECTION:
        need(not required,
             "a full-collection run measures all 69 cases, so required_target_cases is meaningless")
        need(set(spec.get("stages") or {}) == {"full"},
             "a full-collection run declares stages.full only: there is no target stage to gate")
        need(len(str((spec.get("collection") or {}).get("reason", "")).strip()) >= 40,
             "collection.reason must say why this run gives up the stage-1 cost split")
    else:
        need(set(spec.get("stages") or {}) == {"target", "full"},
             "a staged run declares stages.target and stages.full")
    if required:
        scored = length.targets(spec)
        need(len(set(required)) == len(required), "required_target_cases must be distinct")
        need(not set(required) & set(scored), "a required case must not also be a scored target")
        need(spec["evaluation"]["catastrophe_case"] not in required,
             "the catastrophe case must not be a required case")
        need(all(ENTRY.match(entry) for entry in required), f"bad required case entry in {required}")
        # 2026-09-22 검토: 이 식은 표적·기록만 셌고 파국 case 는 빼고 있었다.  그러면 "1단계가 재는 수" 와
        # 상한의 수가 다른 것을 가리켜, 23 을 69 의 1/3 이라고 부르면서 실제로는 24 를 허용했다.
        # 1단계가 실제로 재는 목록(verify_go2_basic_motion_harvest.target_stage_entries)과 같게 센다.
        need(1 + len(scored) + len(required) <= MAX_STAGE1_CASES,
             f"stage 1 must not swallow the full stage: at most {MAX_STAGE1_CASES} measured cases "
             f"(the catastrophe case counts, as it does in target_stage_entries)")
        need(len(str(prereg.get("required_target_cases_reason", "")).strip()) >= 40,
             "required_target_cases_reason must say why these are records and not a target group")
        cases = ROOT / spec["baseline"]["stored_arm"] / "evaluation" / spec["baseline"]["stored_label"] / "cases"
        if cases.is_dir():
            for entry in required:
                _scenario, case_id, seed = entry.split(":")
                need((cases / f"seed_{seed}" / case_id / "summary.json").is_file(),
                     f"stored baseline arm has no {entry} to read the required record against")


def add_env_reward_line(source: str, name: str, value: float) -> str:
    """Add one entry to the deployed REWARD_WEIGHTS dict, just before its closing brace.

    The deployed file invites this ("줄 추가/삭제/주석(#) 자유") and go2_task/env_cfg.py applies any
    name that is a RewTerm of the env.  The line is placed by parsing the dict, not by matching text,
    so a reformatting of the deployed file cannot silently put it somewhere else.
    """
    tree = ast.parse(source)
    node = next((n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "REWARD_WEIGHTS" for t in n.targets)), None)
    if node is None or not isinstance(node.value, ast.Dict):
        raise RuntimeError("deployed file has no REWARD_WEIGHTS dict")
    lines = source.splitlines(keepends=True)
    close = node.value.end_lineno - 1  # the line carrying '}'
    if lines[close].strip() != "}":
        raise RuntimeError(f"REWARD_WEIGHTS must close on its own line, got {lines[close]!r}")
    block = (f'\n'
             f'    # [{name}] 배포 목록에 없던 env 보상 항 — Isaac Lab Go2 rough 기본값에서 바꾼다.\n'
             f'    #   이름이 env 의 RewTerm 이면 go2_task/env_cfg.py 가 그대로 적용한다.\n'
             f'    "{name}": {value},\n')
    rendered = "".join(lines[:close]) + block + "".join(lines[close:])
    if reward_dict(rendered).get(name) != value:
        raise RuntimeError(f"added {name} does not read back as {value}")
    return rendered


def rendered_rewards(spec: dict) -> tuple[str, str]:
    """Render candidate and reference reward files; they differ in the single_change line only."""
    template = (GO2 / "quadruped_rewards.py").read_text(encoding="utf-8")
    candidate = render_reward_source(template, spec["rewards"]["candidate"])
    reference = render_reward_source(template, spec["rewards"]["baseline"])
    if spec["change_class"] == ENV_REWARD_CLASS:
        single = spec["single_change"]
        candidate = add_env_reward_line(candidate, single["name"], float(single["to"]))
        added = [line for line in candidate.splitlines() if line not in reference.splitlines()]
        weight_lines = [line for line in added if line.strip().startswith('"')]
        if len(weight_lines) != 1 or f'"{single["name"]}"' not in weight_lines[0]:
            raise RuntimeError(f"exactly one weight line may be added, got {weight_lines}")
        expected = {**spec["rewards"]["candidate"], single["name"]: float(single["to"])}
        if reward_dict(candidate) != expected or reward_dict(reference) != spec["rewards"]["baseline"]:
            raise RuntimeError("rendered reward files do not read back as the spec")
        return candidate, reference
    differing = [(a, b) for a, b in zip(reference.splitlines(), candidate.splitlines()) if a != b]
    name = spec["single_change"]["name"]
    if len(reference.splitlines()) != len(candidate.splitlines()) or len(differing) != 1 \
            or f'"{name}"' not in differing[0][1]:
        raise RuntimeError(f"rendered reward files must differ in the {name} line only: {differing}")
    if reward_dict(candidate) != spec["rewards"]["candidate"]:
        raise RuntimeError("rendered reward file does not read back as the spec")
    return candidate, reference


def run_config(spec: dict) -> str:
    text = a030.run_config(spec)
    text = text.replace(f"# generated by tools/build_go2_g_a030_package.py from {a030.SPEC.name}; do not edit",
                        f"# generated by tools/build_go2_a033_reward_package.py "
                        f"from {SPECS[spec['work_id']].name}; do not edit")
    text += "TARGET_CASES=(" + " ".join(shlex.quote(item) for item in targets(spec)) + ")\n"
    text += f"EVAL_CHECKPOINT_ITER={int(spec['evaluation']['checkpoint_iter'])}\n"
    if spec['preregistered'].get('plan_screening'):
        text += "COLLECT_REQUIRED_ON_STATIONARY=1\n"
    # 전수 수집 회차는 1단계 분기를 쓰지 않는다.  러너는 `run_config.env` 를 **읽은 뒤** STAGE 를
    # 정하므로(`STAGE=${GO2_STAGE:-target}` 이 source 다음 줄에 온다), 여기서 쓰면 명령줄 선택이
    # 아니라 패키지의 계약이 된다 — 계획 §5 가 요구한 것이 그것이다.  선언하지 않은 사양은 이 줄이
    # 없으므로 발행된 회차의 바이트는 그대로다.
    if length.collection_mode(spec) == length.FULL_COLLECTION:
        text += "GO2_STAGE=full\n"
    return text


def build_payload(spec: dict) -> dict[str, bytes]:
    validate_spec(spec)
    base = spec["baseline"]
    model = (BASELINE_SOURCE / "model_best.pt").read_bytes()
    env = (BASELINE_SOURCE / "env.yaml").read_bytes()
    if sha(model) != base["model_sha256"] or sha(env) != base["env_sha256"]:
        raise RuntimeError("G-A033 model/env on disk do not match the frozen SHA")
    evaluator = (GO2 / "go2_eval_telemetry.py").read_bytes()
    registry = a030.REGISTRY.read_bytes()
    if sha(evaluator) != base["evaluator_sha256"] or sha(registry) != base["registry_sha256"]:
        raise RuntimeError("working-tree evaluator/registry differ from the ruler of the stored baseline arm")
    runner = length.cand.runner_bytes(spec)
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
    # 결함 C-8 (2026-09-21 검토): 위 루프가 `baseline/` 에도 **작업본** 파일을 그대로 싣는다.
    # 학습에는 쓰이지 않지만(기준선은 SHA 고정 model/env 재생이다) 패키지를 열어 보는 사람에게는
    # 없는 두 번째 차이가 보인다.  발행된 arm 의 바이트를 지키기 위해 사양이 켜는 방식으로 고친다:
    # 키가 없는 사양은 예전과 똑같이 만들어진다.
    if spec["output"].get("baseline_reward_file") == "rendered_reference":
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
    payload["README.txt"] = readme(spec).encode("utf-8")
    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def readme(spec: dict) -> str:
    out, evaluation, single = spec["output"], spec["evaluation"], spec["single_change"]
    title = f"GO2 {spec['work_id']} REWARD CHANGE ON G-A033 — {single['name']} {single['from']} -> {single['to']}"
    why = "\n".join("  " + line for line in spec["why"])
    derivation = "\n".join(f"  {key}: {value}" for key, value in spec["value_derivation"].items())
    rejected = "\n".join(f"  {key}: {value}" for key, value in spec["rejected_alternatives"].items())
    videos = "\n".join(f"  {entry:26s} {spec['videos']['reasons'][entry]}" for entry in spec["videos"]["candidate"])
    limits = ", ".join(f"{k} {v}" for k, v in spec["preregistered"]["max_scenario_weighted_loss_70_by_scenario"].items())
    root = out["package_root"]
    # 전수 수집 회차는 campaign 껍데기를 쓰지 않는다 — 1단계도 게이트도 없으므로 이 ZIP 하나가 곧
    # 실행 단위다.  그 회차의 README 는 "혼자 돌리지 마라" 대신 실제 한 줄을 적는다.
    how = ("This package TRAINS one policy and then measures it.  status: %s.\n"
           "One upload, one command, one result ZIP: the whole %d-case evaluation runs in a single\n"
           "pass (run_config.env pins GO2_STAGE=full), so there is no target stage and no server gate.\n"
           "  unzip -oq <this zip> -d /workspace\n"
           "  bash %s/%s\n"
           "  Resume after an interruption: GO2_RESUME=1 bash %s/%s\n"
           % (spec['status'], int(evaluation['case_count']), root, spec['runner'], root, spec['runner'])
           if length.collection_mode(spec) == length.FULL_COLLECTION else
           "This package TRAINS one policy and then measures it.  status: %s.\n"
           "It is one arm of a campaign; do not run it on its own (see the campaign guide).\n"
           % spec['status'])
    return f"""{title}
{'=' * len(title)}

{how}
WHAT CHANGES
  Exactly one reward weight: {single['name']} {single['from']} -> {single['to']}.
  candidate/quadruped_rewards.py and reference/baseline_quadruped_rewards.py differ in that line only.
  Training length, seed, env count and every other weight are G-A033's.

WHY (analysis {Path(spec['plan']).name})
{why}

HOW THE VALUE WAS CHOSEN
{derivation}

LEVERS NOT MOVED
{rejected}

WHAT IS AND IS NOT PROMISED
  Not promised: a higher score.  No gain estimate exists and one training seed cannot
  separate the lever from seed luck.
  Pre-registered: all other axes held -- per-scenario weighted loss at most twice its own
  evaluation sd ({limits}), flat G1/G2 guards unchanged.

CHECKPOINT
  Evaluated at iter {evaluation['checkpoint_iter']} of {spec['training']['max_iterations']}, the iteration G-A033 was evaluated at.

VIDEOS (4 env x 500 steps)
{videos}

BASELINE ARM
  {spec['baseline']['stored_arm']} ({spec['baseline']['name']}, 42.52861/70 on the 69-case
  internal proxy).  Frozen baseline by G-D-BASELINE-A033-20260916.
  Its model and env ship here so the server can verify it is the same bytes.
"""


def build_zip(spec: dict) -> bytes:
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


guide = length.guide   # the campaign builder named there also builds this arm's campaign


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_id", choices=sorted(SPECS))
    args = parser.parse_args(argv)
    spec = load(args.work_id)
    data = build_zip(spec)
    print(f"{args.work_id}: ZIP {len(data)} bytes sha256 {sha(data)}")
    print(f"  reward change: {spec['single_change']['name']} {spec['single_change']['from']} -> {spec['single_change']['to']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
