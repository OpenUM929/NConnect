"""Contract tests for the one-file campaign package G-A033 (A017 + track_lin_vel_xy_exp 1.4 -> 1.5).

Local only: no simulator, no training.  Run from the repository root:
    python -m unittest tools.test_go2_campaign_contract
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_basic_motion_pair as pair  # noqa: E402
import build_go2_campaign_package as campaign  # noqa: E402
import build_go2_candidate_package as pkg  # noqa: E402
import go2_target_gate as gate  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
import verify_go2_g_a030_harvest as a030v  # noqa: E402
import tools.test_go2_basic_motion_package_contract as staged  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402
from tools.test_h1_report_recovery import BASH, shell_path  # noqa: E402

A027 = staged.A027
CAMPAIGN_ID = "G-A033"
CAMPAIGN = campaign.CAMPAIGNS[CAMPAIGN_ID]
SPEC = pkg.load("G-A033")
A031 = pkg.load("G-A031")
ARM = pkg.build_payload(SPEC)
PAYLOAD = campaign.build_payload(CAMPAIGN_ID)
RUNNER = (GO2 / campaign.RUNNER).read_text(encoding="utf-8")
PAIR_RUNNER = (GO2 / pair.RUNNER).read_text(encoding="utf-8")
# The runner G-A033 shipped and ran with (kept in runner_history after the 2026-09-17 fix).
ARM_RUNNER = pkg.runner_bytes(SPEC).decode("utf-8")
STAGED_RUNNER = (GO2 / pkg.RUNNER).read_text(encoding="utf-8")
EXTREF = json.loads(pkg.EXTREF.read_text(encoding="utf-8"))
PAIR_RELEASE_SHA = "e714d9484c7fe5ea5a326a6d17f0361f74b93048e7929a5eed59f6743a2c7e6c"


def function(text: str, name: str) -> str:
    head = text.index(f"{name}() ")
    return text[head: text.index("\n}\n", head) + 3]


def bash_gate_reading(json_text: str | None, rc: int) -> str:
    """Run the runner's own run_gate/gate_verdict with a fake gate that writes json_text and exits rc."""
    with tempfile.TemporaryDirectory() as tmp:
        keep = shell_path(Path(tmp))
        script = "\n".join([
            "set -euo pipefail",
            f"CAMPAIGN_KEEP={keep}; LOG={keep}/log.txt; GATE=gate.py; STORED=stored",
            "mkdir -p \"$CAMPAIGN_KEEP/gate\"",
            "arm_var() { printf G-A033; }",
            "arm_keep() { printf /nonexistent; }",
            "fake() { local out=; while [[ $# -gt 0 ]]; do [[ \"$1\" != --out ]] || out=$2; shift; done;",
            "  [[ -z \"${FAKE_JSON:-}\" ]] || printf '%s\\n' \"$FAKE_JSON\" >\"$out\"; return \"$FAKE_RC\"; }",
            "PY=(fake)",
            function(RUNNER, "gate_verdict"),
            function(RUNNER, "run_gate"),
            "run_gate root target",
        ])
        env = dict(os.environ, FAKE_RC=str(rc))
        if json_text is not None:
            env["FAKE_JSON"] = json_text
        done = subprocess.run([BASH, "-c", script], capture_output=True, text=True, env=env)
    if done.returncode != 0:
        raise AssertionError(done.stderr)
    return done.stdout.strip()


def pin_harvest(keep: Path, iteration: int = 900) -> None:
    """What server_run_go2_candidate_iter_pinned.sh leaves: the pin record and the status lines."""
    model_sha = hashlib.sha256((keep / "training" / "model_best.pt").read_bytes()).hexdigest()
    lines = [f"EVAL_CHECKPOINT_ITER={iteration}", f"EVAL_CHECKPOINT_SHA={model_sha}",
             "REWARD_BEST_MODEL_ITER=700", "REWARD_BEST_MODEL_SHA=" + "0" * 64]
    (keep / "training" / "CHECKPOINT_PIN.txt").write_text("".join(line + "\n" for line in lines),
                                                          encoding="utf-8", newline="\n")
    with (keep / "RUNNER_STATUS.txt").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"CANDIDATE_EVAL_ITER={iteration}\n" + "REWARD_BEST_MODEL_ITER=700\n")


def gate_json(report: dict) -> str:
    # The exact serialisation go2_target_gate.main() writes.
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, default=str)


class ArmSpecTest(unittest.TestCase):
    def test_single_variable_is_track_only(self):
        cand = reward_dict(ARM["candidate/quadruped_rewards.py"].decode("utf-8"))
        ref = reward_dict(ARM["reference/baseline_quadruped_rewards.py"].decode("utf-8"))
        self.assertEqual(ref, SPEC["rewards"]["baseline"])
        self.assertEqual(cand, SPEC["rewards"]["candidate"])
        self.assertEqual([k for k in cand if cand[k] != ref[k]], ["track_lin_vel_xy_exp"])
        self.assertEqual((ref["track_lin_vel_xy_exp"], cand["track_lin_vel_xy_exp"]), (1.4, 1.5))
        self.assertEqual(cand["feet_air_time"], 0.2, "plan 6-3 keeps feet_air_time at 0.2")
        diff = [(a, b) for a, b in zip(ARM["reference/baseline_quadruped_rewards.py"].splitlines(),
                                       ARM["candidate/quadruped_rewards.py"].splitlines()) if a != b]
        self.assertEqual(len(diff), 1)

    def test_everything_else_is_the_g_a030_package(self):
        expected = ["PACKAGE_SHA256SUMS.txt", "README.txt", "candidate/quadruped_rewards.py",
                    "expected_rewards.json", "experiment.json", "run_config.env"]
        theirs = set(staged.A030_PAYLOAD) - {pkg.SUITE_RUNNER}
        self.assertEqual(SPEC["runner"], pkg.PINNED_RUNNER)
        self.assertEqual(set(ARM) - {pkg.PINNED_RUNNER}, theirs)
        self.assertEqual(sorted(n for n in theirs if ARM[n] != staged.A030_PAYLOAD[n]), expected)
        self.assertEqual(ARM[pkg.PINNED_RUNNER], ARM_RUNNER.encode("utf-8"))

    def test_deployed_code_is_unchanged_r6(self):
        for name, data in ARM.items():
            role, _, rel = name.partition("/")
            if role in ("candidate", "baseline") and not rel.startswith("exported/") \
                    and name != "candidate/quadruped_rewards.py":
                self.assertEqual(data, (GO2 / rel).read_bytes(), name)

    def test_ruler_and_reading_are_the_feet_pair_s(self):
        # Plan 12-2: same baseline, cases, sentinel, stages, videos, training and pass marks as G-A031.
        # v2 adds only the checkpoint pin to the evaluation block.
        for key in ("baseline", "stages", "training"):
            self.assertEqual(SPEC[key], A031[key], key)
        evaluation = copy.deepcopy(SPEC["evaluation"])
        self.assertEqual((evaluation.pop("checkpoint_iter"), bool(evaluation.pop("checkpoint_rule"))), (900, True))
        self.assertEqual(evaluation, A031["evaluation"])
        ours, theirs = copy.deepcopy(SPEC["preregistered"]), copy.deepcopy(A031["preregistered"])
        ours.pop("source"), theirs.pop("source")
        self.assertEqual(ours, theirs)
        self.assertEqual(SPEC["videos"]["candidate"], A031["videos"]["candidate"])
        self.assertEqual(set(SPEC["videos"]["reasons"]), set(SPEC["videos"]["candidate"]))

    def test_external_reference_is_isaaclab_go2_rough(self):
        rough = EXTREF["isaaclab"]["rewards"]["go2_rough"]
        self.assertEqual(SPEC["external_reference"]["candidate"], rough["track_lin_vel_xy_exp"])
        # After the change A017 differs from Isaac Lab Go2 rough in feet_air_time only.
        cand = SPEC["rewards"]["candidate"]
        self.assertEqual([k for k in cand if float(cand[k]) != float(rough[k])], ["feet_air_time"])
        for mutate in (lambda s: s["rewards"]["candidate"].__setitem__("track_lin_vel_xy_exp", 1.6),
                       lambda s: s["rewards"]["candidate"].__setitem__("feet_air_time", 0.01),
                       lambda s: s["external_reference"].__setitem__("isaaclab_go2_rough", 1.4),
                       lambda s: s.__setitem__("dial_history_ref", "`track_lin_vel_xy_exp` | 기각")):
            bad = copy.deepcopy(SPEC)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                pkg.validate_spec(bad)

    def test_run_config_is_the_spec(self):
        script = ARM["run_config.env"].decode("utf-8") + (
            'printf "%s|" "$WORK_ID" "$SINGLE_CHANGE_NAME" "$SINGLE_CHANGE_TO" "$TRAIN_SEED" "$MAX_ITERATIONS" '
            '"$DONE_MARKER" "$TMUX_NAME" "${#TARGET_CASES[@]}" "${#CANDIDATE_VIDEOS[@]}"\n')
        done = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.split("|")[:-1], [
            "G-A033", "track_lin_vel_xy_exp", "1.5", "42", "1000", SPEC["output"]["done_marker"],
            SPEC["output"]["tmux_name"], "9", "5"])

    def test_readme_names_no_dose_pair(self):
        text = ARM["README.txt"].decode("utf-8")
        self.assertNotIn("dose pair", text)
        self.assertIn("track_lin_vel_xy_exp 1.4 -> 1.5", text)

    def test_feet_pair_arms_still_rebuild_byte_identical(self):
        for work in ("G-A031", "G-A032"):
            spec = pkg.load(work)
            current = pkg.upload_dir(spec) / "current" / spec["output"]["upload_zip"]
            if not current.is_file():
                self.skipTest(f"{work} not published")
            self.assertEqual(pkg.build(spec).read_bytes(), current.read_bytes(), work)


class CampaignPayloadTest(unittest.TestCase):
    def test_arm_is_the_builder_output(self):
        config = PAYLOAD["campaign_config.env"].decode("utf-8")
        name = SPEC["output"]["upload_zip"]
        data = PAYLOAD[f"arms/{name}"]
        self.assertEqual(data, pkg.output_path(SPEC).read_bytes())
        self.assertIn(hashlib.sha256(data).hexdigest(), config)
        self.assertEqual([n for n in PAYLOAD if n.startswith("arms/")], [f"arms/{name}"])

    def test_gate_files_are_the_repository_files(self):
        # 2026-09-17: this release ran; its gate is the frozen copy in runner_history (the working tree
        # gate now reads fact_rules_v1).  The two dependencies are unchanged.
        for name, path in campaign.GATE_FILES.items():
            expected = pair.EXECUTED_GATE if name == "go2_target_gate.py" else path
            self.assertEqual(PAYLOAD[name], expected.read_bytes(), name)
        self.assertNotIn("go2_fact_rules.py", PAYLOAD)
        # 2026-09-24: 러너도 같은 모양이 됐다.  C-27·C-28 이 작업본 캠페인 러너를 고쳤으므로
        # 이미 실행된 이 발행본은 **자기가 돌았던 바이트**를 유지한다(campaign.EXECUTED_RUNNERS).
        self.assertEqual(PAYLOAD[campaign.RUNNER], campaign.runner_bytes(CAMPAIGN_ID))
        self.assertIn(CAMPAIGN_ID, campaign.PUBLISHED_RUNNERS,
                      "발행된 회차의 러너 핀이 사라지면 발행 ZIP 이 재빌드되지 않는다")

    @unittest.skipUnless((A027 / "evaluation" / "a017" / "cases").is_dir(), "G-A027 harvest not present")
    def test_stored_summaries_are_the_g_a027_arm(self):
        stored = {name: data for name, data in PAYLOAD.items() if name.startswith("stored_baseline/")}
        self.assertEqual(len(stored), len(pair.stored_entries(SPEC)) + 1)
        for name, data in stored.items():
            self.assertEqual(data, (A027 / name.split("/", 1)[1]).read_bytes(), name)

    def test_manifest_covers_every_member(self):
        lines = PAYLOAD["CAMPAIGN_SHA256SUMS.txt"].decode("utf-8").splitlines()
        listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in lines}
        self.assertEqual(set(listed), set(PAYLOAD) - {"CAMPAIGN_SHA256SUMS.txt"})
        for name, digest in listed.items():
            self.assertEqual(hashlib.sha256(PAYLOAD[name]).hexdigest(), digest, name)

    def test_campaign_config_reads_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "campaign_config.env"
            path.write_bytes(PAYLOAD["campaign_config.env"])
            script = (f"source {shell_path(path)}; printf '%s|' \"$CAMPAIGN_ID\" \"$CAMPAIGN_TMUX\" "
                      "\"$CAMPAIGN_DONE_MARKER\" \"$CAMPAIGN_RESULT_ZIP\" \"${ARM_WORK[@]}\" \"${ARM_ROOT[@]}\" "
                      "\"${#ARM_ZIP_SHA[@]}\"")
            done = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.split("|")[:-1], [
            "G-A033", CAMPAIGN["tmux"], CAMPAIGN["done_marker"], CAMPAIGN["result_zip"], "G-A033",
            SPEC["output"]["package_root"], "1"])

    def test_names_do_not_collide_with_the_arm(self):
        out = SPEC["output"]
        self.assertNotEqual(CAMPAIGN["tmux"], out["tmux_name"])
        self.assertNotEqual(CAMPAIGN["keep_name"], out["keep_dir_name"])
        self.assertNotEqual(CAMPAIGN["result_zip"], out["result_zip"])
        self.assertNotEqual(campaign.package_root(CAMPAIGN), out["package_root"])

    def test_pair_release_is_untouched(self):
        output = pair.output_path()
        if not output.is_file():
            self.skipTest("pair release not present")
        self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), PAIR_RELEASE_SHA)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read(f"{pair.PREFIX.as_posix()}/{pair.RUNNER}").decode("utf-8"), PAIR_RUNNER)


class CampaignRunnerTest(unittest.TestCase):
    def test_runner_is_lf_and_parses(self):
        self.assertNotIn("\r", RUNNER)
        done = subprocess.run([BASH, "-n", shell_path(GO2 / campaign.RUNNER)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_gpu_work_goes_through_the_arm_runner_only(self):
        self.assertNotIn("-p train.py", RUNNER)
        self.assertNotIn("play.py --task", RUNNER)
        stage = function(RUNNER, "run_stage")
        for text in ('PACKAGE_ROOT="$root"', 'GO2_STAGE="$stage"', 'GO2_RESUME="$resume"',
                     'GO2_REMEASURE_BASELINE="$remeasure"', 'bash "$ARM_RUNNER" --inner'):
            self.assertIn(text, stage)
        self.assertIn("server_run_go2_candidate_staged.sh|server_run_go2_candidate_iter_pinned.sh) ;;", RUNNER)
        config = PAYLOAD["campaign_config.env"].decode("utf-8").splitlines()
        self.assertIn(f"ARM_RUNNER={pkg.PINNED_RUNNER}", config)
        self.assertIn("bash server_run_go2_campaign.sh --inner", RUNNER)

    def test_order_and_gating(self):
        order = ['target_phase "$root"', 'full_phase "$root"', "package_campaign CAMPAIGN_COMPLETE 0",
                 'echo "$CAMPAIGN_DONE_MARKER"']
        main = RUNNER[RUNNER.index('log "[START]'):]
        positions = [main.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('[[ "${STATE[$work]:-}" == TARGET_PASS ]] || return 0', function(RUNNER, "full_phase"))
        self.assertEqual(RUNNER.count("run_stage \"$root\" full"), 1)
        target = function(RUNNER, "target_phase")
        self.assertLess(target.index('run_gate "$root" target)'), target.index("TARGET_PASS) STATE[$work]=TARGET_PASS"))
        self.assertIn('"$verdict" == REMEASURE_BASELINE && "$remeasure" == 0', target)

    def test_unchanged_helpers_are_the_pair_runner_s(self):
        # `full_complete` 와 그 호출부 `full_phase` 는 2026-09-24 에 갈라졌다(결함 C-28):
        # 캠페인 러너 둘은 수집 상태와
        # 결과 ZIP·SHA 까지 보고 건너뛰지만, pair 러너는 **이미 실행이 끝난** G-A031+G-A032 의
        # 발행본이고 빌더가 생성하는 파일이라 그 바이트를 고치지 않는다.  새 회차가 그 러너를
        # 다시 쓰면 같은 수정을 함께 옮긴다 — 그때 이 목록에 되돌려 넣는다.
        for name in ("status_of", "target_complete", "baseline_remeasured", "run_stage",
                     "sha_or_none", "on_exit"):
            ours = function(RUNNER, name)
            theirs = function(PAIR_RUNNER, name)
            if name == "on_exit":
                theirs = theirs.replace("pair runner", "campaign runner").replace("package_pair", "package_campaign")
            self.assertEqual(ours, theirs, name)
        mine = function(RUNNER, "full_complete")
        self.assertIn("COLLECTION_STATUS", mine, "C-28: 건너뛰기는 수집 상태를 본다")
        self.assertIn("sha256sum -c", mine, "C-28: 건너뛰기는 내려받을 것이 있는지 본다")
        self.assertNotIn("COLLECTION_STATUS", function(PAIR_RUNNER, "full_complete"),
                         "pair 러너는 실행이 끝난 발행본이라 그대로 둔다")
        # 호출부도 같이 갈라진다 — 고친 함수는 인자가 둘이다.  둘을 함께 빼지 않으면
        # 검사가 「같아야 한다」와 「달라야 한다」를 동시에 요구하게 된다.
        self.assertIn('full_complete "$keep" "$(arm_result "$root")"',
                      function(RUNNER, "full_phase"))
        self.assertIn('full_complete "$keep"', function(PAIR_RUNNER, "full_phase"))

    def test_verdict_comes_from_the_gate_json(self):
        body = function(RUNNER, "run_gate")
        self.assertNotIn('case "$rc"', body)
        self.assertIn('verdict=$(gate_verdict "$out")', body)
        self.assertIn('rm -f -- "$out"', body, "a stale JSON must not answer for a new gate run")

    def test_gate_reading_survives_a_wrapper_that_changes_the_exit_code(self):
        # G-A031/G-A032 (2026-09-15): isaaclab.sh -p returned 1 for the gate's FAIL (10).
        report = {"faults": [], "target_stage": {"passed": False, "target_mean_proxy_delta": -0.02},
                  "work_id": "G-A033"}
        for verdict in ("TARGET_PASS", "FAIL", "REMEASURE_BASELINE", "UNDECIDED"):
            for rc in (1, gate.EXIT[verdict]):
                self.assertEqual(bash_gate_reading(gate_json({**report, "verdict": verdict}), rc), verdict,
                                 f"{verdict} rc={rc}")
        self.assertEqual(bash_gate_reading(None, 0), "UNDECIDED", "no JSON is never a pass")
        self.assertEqual(bash_gate_reading(gate_json({"target_stage": {"verdict": "TARGET_PASS"}}), 0), "UNDECIDED",
                         "only the top-level verdict counts")
        self.assertEqual(bash_gate_reading("not json", 0), "UNDECIDED")

    def test_preflight_mirrors_the_arm_runner(self):
        outer = ARM_RUNNER[ARM_RUNNER.index('if [[ "${1:-}" != "--inner" ]]'):ARM_RUNNER.index("printf -v INNER_COMMAND")]
        for token in ("EXPECTED_EVALUATOR_SHA", "EXPECTED_REGISTRY_SHA", "BASELINE_MODEL_SHA", "BASELINE_ENV_SHA",
                      "TARGET_CASES", "pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py'",
                      "GO2_DISCARD_PREVIOUS", "tmux has-session"):
            self.assertIn(token, outer)
            self.assertIn(token, RUNNER)
        self.assertIn('CAMPAIGN_ROOT=${CAMPAIGN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}', RUNNER)


def pin_script(body: str) -> str:
    """The pinned runner's checkpoint functions, with a KEEP/CANDIDATE_ROOT in a temp folder."""
    return "\n".join([
        "set -euo pipefail",
        function(ARM_RUNNER, "snapshot_checkpoint"),
        function(ARM_RUNNER, "stop_checkpoint_copier"),
        function(ARM_RUNNER, "settle_checkpoint_pin"),
        body,
    ])


class CheckpointPinTest(unittest.TestCase):
    """G-A033 v2: the candidate is evaluated at A017's checkpoint iteration (900), not finalize's pick."""

    def run_bash(self, body: str, env: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run([BASH, "-c", pin_script(body)], capture_output=True, text=True,
                              env=dict(os.environ, GO2_PIN_POLL_S="0.2", **env), timeout=120)

    # "pinned == staged + CHECKPOINT PIN blocks" held until 2026-09-22.  The C-14 fix
    # (re-enter by path, not by the ancestor's file name) and the mandatory-collection
    # opt-in landed in the pinned runner only, on purpose: the staged runner re-enters
    # itself by its own name, so C-14 never applied to it, and no package ships it with
    # COLLECT_REQUIRED_ON_STATIONARY.  The equality could not express that and stayed red
    # (defect C-23) — and a red gate hides the next regression, which is exactly the one
    # this pair exists to catch: an edit that lands in one runner and not the other.
    # So the comparison is narrowed, not deleted.  Every remaining difference must belong
    # to a contract named here, every contract named here must actually be used, and each
    # contract is separately proven by running the runner's own lines.
    DIVERGENCE = {
        "C-14 재진입은 이름이 아니라 경로로": (
            "SELF=", '"$SELF"', "server_run_go2_candidate_staged.sh", "Re-enter by path"),
        "C-27 중단된 학습은 보존하고 멈춘다": (
            "INTERRUPTED TRAINING GUARD", "restart_would_destroy",
            "preserve_interrupted_training", "GO2_RESTART_TRAINING",
            "INTERRUPTED_TRAINING_PRESERVED"),
        "정지 정책의 필수 수집 옵트인": (
            "COLLECT_REQUIRED_ON_STATIONARY", "catastrophe_action", "COLLECTION_ACTION",
            "collect_candidate_target_cases", "collect_configured_videos",
            "MANDATORY COLLECTION", "EARLY STOP", "STOP_WITH_WITNESS"),
    }
    LAUNCH_BLOCK = r'^(?:  \[\[ -f "\$SELF".*?\n)?  printf -v INNER_COMMAND.*?^  tmux new-session[^\n]*$'

    def stripped(self, pinned: str) -> str:
        head = "# The staged runner's own header follows.\n#\n"
        text = pinned[:pinned.index("#\n") + 2] + pinned[pinned.index(head) + len(head):]
        text = re.sub(r"[ ]*# BEGIN CHECKPOINT PIN: [a-z ]+\n.*?[ ]*# END CHECKPOINT PIN: [a-z ]+\n", "",
                      text, flags=re.S)
        return text.replace(
            "# Staged candidate runner with a pinned evaluation checkpoint (first used by G-A033 v2).\n#\n", "")

    def assert_shape(self, pinned: str) -> None:
        for block in ("config", "functions", "resume", "start copier", "stop copier", "settle", "status"):
            for edge in ("BEGIN", "END"):
                self.assertEqual(pinned.count(f"# {edge} CHECKPOINT PIN: {block}\n"), 1, (edge, block))
        self.assertNotIn("# BEGIN CHECKPOINT PIN", STAGED_RUNNER)
        self.assertNotIn("\r", pinned + STAGED_RUNNER)
        for text in (pinned, STAGED_RUNNER):
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            done = subprocess.run([BASH, "-n", shell_path(Path(handle.name))], capture_output=True, text=True)
            Path(handle.name).unlink()
            self.assertEqual(done.returncode, 0, done.stderr)

    def test_published_bytes_keep_the_original_pin_relation(self):
        """무엇이 실제로 돌았는가.  G-A031 이 실은 staged 러너와 G-A033 이 실은 pinned 러너는
        pin 블록만큼만 다르다.  발행된 바이트는 불변이므로 이 등식은 앞으로도 성립해야 한다."""
        executed_staged = pkg.runner_bytes(pkg.load("G-A031")).decode("utf-8")
        self.assertEqual(self.stripped(ARM_RUNNER), executed_staged)

    def test_working_runners_differ_only_where_a_named_contract_says_so(self):
        """작업본 두 러너는 더 이상 같지 않다 — C-14 와 필수 수집이 pinned 에만 들어갔기 때문이다.
        남은 차이는 위 DIVERGENCE 가 이름 붙인 두 계약의 것이어야 하고, 그 둘 다 실제로 쓰여야
        한다.  이름 없는 차이 — 한쪽 러너에만 들어간 편집 — 는 여기서 떨어진다."""
        working_pinned = (GO2 / pkg.PINNED_RUNNER).read_text(encoding="utf-8")
        left, right = STAGED_RUNNER.splitlines(), self.stripped(working_pinned).splitlines()
        used = set()
        for group in difflib.SequenceMatcher(None, left, right).get_grouped_opcodes(0):
            lines = [line for tag, i1, i2, j1, j2 in group if tag != "equal"
                     for line in left[i1:i2] + right[j1:j2]]
            if not lines:
                continue
            owners = sorted(name for name, tokens in self.DIVERGENCE.items()
                            if any(token in line for line in lines for token in tokens))
            self.assertEqual(len(owners), 1,
                             "이 차이를 설명하는 계약이 %d 개다:\n%s" % (len(owners), "\n".join(lines)))
            used.add(owners[0])
        self.assertEqual(used, set(self.DIVERGENCE), "쓰이지 않는 계약 — 관문이 비어 간다")
        self.assert_shape(working_pinned)

    def test_each_runner_re_enters_its_own_file(self):
        """C-14 는 양쪽에 같은 줄을 넣어 고치는 결함이 아니다 — staged 러너는 자기 이름으로,
        pinned 러너는 자기 경로로 자신에게 재진입한다.  읽지 않고 **실행해서** 확인한다:
        스텁 tmux 가 받은 명령이 가리키는 파일이 그 러너 자신이어야 한다."""
        for name in (pkg.RUNNER, pkg.PINNED_RUNNER):
            with self.subTest(runner=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                text = (GO2 / name).read_text(encoding="utf-8")
                (root / name).write_text(text, encoding="utf-8", newline="\n")
                block = re.search(self.LAUNCH_BLOCK, text, re.M | re.S)
                self.assertIsNotNone(block, name)
                script = "\n".join([
                    "set -euo pipefail",
                    'tmux() { printf "%s" "${!#}"; }',
                    f"PACKAGE_ROOT={shell_path(root)}",
                    f'SELF="$PACKAGE_ROOT/{name}"',
                    "RESUME=0; REMEASURE=0; STAGE=full",
                    "ISAACLAB_SH=/opt/isaaclab.sh; TMUX_NAME=t",
                    block.group(0), ""])
                done = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stderr)
                entered = re.search(r"cd (\S+) &&.* bash (\S+) --inner", done.stdout)
                self.assertIsNotNone(entered, done.stdout)
                # The runner speaks shell paths; resolve the re-entry against the package
                # root it just cd'd into and require the file to be one this package ships.
                cd_to, relaunch = (entered.group(index).strip("'") for index in (1, 2))
                self.assertEqual(cd_to, shell_path(root))
                self.assertIn(relaunch, (name, f"{shell_path(root)}/{name}"), done.stdout)
                self.assertTrue((root / Path(relaunch).name).is_file(), f"없는 파일로 재진입한다: {relaunch}")

    def test_mandatory_collection_is_the_pinned_runners_own_contract(self):
        """필수 수집은 pinned 러너만의 계약이다.  분기를 읽지 않고 그 함수를 **실행**한다 —
        비유한 학습은 옵트인과 무관하게 STOP_UNSAFE 여야 한다(자료를 위해 시뮬레이터를 한 번 더
        띄우지 않는다).  staged 러너에는 이 옵트인이 없어야 하고, 그 조기 종료 경로는 역사적
        동작(무조건 목격 영상 한 편) 그대로여야 한다."""
        pinned = (GO2 / pkg.PINNED_RUNNER).read_text(encoding="utf-8")
        body = function(pinned, "catastrophe_action")
        cases = (("SUITE_COMPLETE", 0, "CONTINUE"), ("SUITE_COMPLETE", 1, "CONTINUE"),
                 ("CATASTROPHE_STATIONARY", 0, "STOP_WITH_WITNESS"),
                 ("CATASTROPHE_STATIONARY", 1, "CONTINUE_REQUIRED"),
                 ("CATASTROPHE_NONFINITE", 0, "STOP_UNSAFE"),
                 ("CATASTROPHE_NONFINITE", 1, "STOP_UNSAFE"))
        for decision, optin, expected in cases:
            with self.subTest(decision=decision, opt_in=optin):
                done = subprocess.run(
                    [BASH, "-c", f"set -euo pipefail\nCOLLECT_REQUIRED_ON_STATIONARY={optin}\n{body}\n"
                                 f"catastrophe_action {decision}"], capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(done.stdout.strip(), expected)
        self.assertNotIn("COLLECT_REQUIRED_ON_STATIONARY", STAGED_RUNNER)
        self.assertNotIn("catastrophe_action", STAGED_RUNNER)
        self.assertIn('if [[ "$DECISION" != SUITE_COMPLETE ]]; then', STAGED_RUNNER)

    def test_order_in_the_training_phase(self):
        phase = ARM_RUNNER[ARM_RUNNER.index('echo "[PHASE 1/6]'):ARM_RUNNER.index('echo "[PHASE 2/6]')]
        order = ["snapshot_checkpoint &", '"$ISAACLAB_SH" -p train.py', "stop_checkpoint_copier",
                 "recover_training_report || exit 4", 'cp -a exported/model_best.pt exported/env.yaml "$KEEP/training/"',
                 "settle_checkpoint_pin || exit 3", 'CANDIDATE_MODEL="$KEEP/training/model_best.pt"']
        positions = [phase.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('grep -qx "EVAL_CHECKPOINT_ITER=$EVAL_CHECKPOINT_ITER" "$PIN_RECORD"', phase)

    def test_copier_takes_the_checkpoint_before_finalize_deletes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, keep = Path(tmp) / "candidate", Path(tmp) / "keep"
            (keep / "training").mkdir(parents=True)
            run = root / "logs" / "rsl_rl" / "quadruped" / "2026-09-15_00-00-00"
            body = "\n".join([
                f"CANDIDATE_ROOT={shell_path(root)}; KEEP={shell_path(keep)}; EVAL_CHECKPOINT_ITER=900",
                'PIN_MODEL="$KEEP/training/model_iter900.pt"; PIN_RECORD="$KEEP/training/CHECKPOINT_PIN.txt"',
                # logs/ does not exist when the copier starts (the errexit/pipefail trap this guards).
                "snapshot_checkpoint & SNAPSHOT_PID=$!",
                "sleep 1",
                f"mkdir -p {shell_path(run)}",
                f"printf 'iter-700-weights' >{shell_path(run)}/model_700.pt",
                f"printf 'iter-900-weights' >{shell_path(run)}/model_900.pt",
                # On the server finalize comes ~100 iterations (~6 min) after iter 900; a few
                # seconds is enough here, where one look costs ~0.5 s of process start-up.
                "for _ in $(seq 60); do [[ -s \"$PIN_MODEL\" ]] && break; sleep 0.5; done",
                # finalize: keep the reward pick (700), delete the rest.
                f"rm -f {shell_path(run)}/model_900.pt",
                f"printf 'iter-700-weights' >{shell_path(keep)}/training/model_best.pt",
                "stop_checkpoint_copier",
                "settle_checkpoint_pin",
            ])
            done = self.run_bash(body, {})
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertEqual((keep / "training" / "model_best.pt").read_text(), "iter-900-weights")
            self.assertEqual((keep / "training" / "model_best_by_reward.pt").read_text(), "iter-700-weights")
            record = a030v.read_kv(keep / "training" / "CHECKPOINT_PIN.txt")
            self.assertEqual(record["EVAL_CHECKPOINT_ITER"], "900")
            self.assertEqual(record["REWARD_BEST_MODEL_ITER"], "700")
            self.assertEqual(record["EVAL_CHECKPOINT_SHA"], hashlib.sha256(b"iter-900-weights").hexdigest())

    def test_reward_pick_at_the_pinned_iteration_is_taken_after_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, keep = Path(tmp) / "candidate", Path(tmp) / "keep"
            (keep / "training").mkdir(parents=True)
            run = root / "logs" / "rsl_rl" / "quadruped" / "r"
            run.mkdir(parents=True)
            (run / "model_900.pt").write_text("iter-900-weights")
            (keep / "training" / "model_best.pt").write_text("iter-900-weights")
            body = "\n".join([
                f"CANDIDATE_ROOT={shell_path(root)}; KEEP={shell_path(keep)}; EVAL_CHECKPOINT_ITER=900",
                'PIN_MODEL="$KEEP/training/model_iter900.pt"; PIN_RECORD="$KEEP/training/CHECKPOINT_PIN.txt"',
                "sleep 30 & SNAPSHOT_PID=$!",  # a copier that never got to copy
                "stop_checkpoint_copier",
                "settle_checkpoint_pin",
            ])
            done = self.run_bash(body, {})
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            record = a030v.read_kv(keep / "training" / "CHECKPOINT_PIN.txt")
            self.assertEqual((record["EVAL_CHECKPOINT_ITER"], record["REWARD_BEST_MODEL_ITER"]), ("900", "900"))

    def test_missing_checkpoint_stops_before_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, keep = Path(tmp) / "candidate", Path(tmp) / "keep"
            (keep / "training").mkdir(parents=True)
            (root / "logs").mkdir(parents=True)
            (keep / "training" / "model_best.pt").write_text("iter-700-weights")
            body = "\n".join([
                f"CANDIDATE_ROOT={shell_path(root)}; KEEP={shell_path(keep)}; EVAL_CHECKPOINT_ITER=900",
                'PIN_MODEL="$KEEP/training/model_iter900.pt"; PIN_RECORD="$KEEP/training/CHECKPOINT_PIN.txt"',
                "sleep 30 & SNAPSHOT_PID=$!",
                "stop_checkpoint_copier",
                "settle_checkpoint_pin || exit $?",
            ])
            done = self.run_bash(body, {})
            self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
            self.assertIn("was not captured", done.stdout)
            self.assertEqual((keep / "training" / "model_best.pt").read_text(), "iter-700-weights")

    def test_run_config_carries_the_iteration_and_the_runner_requires_it(self):
        self.assertIn("EVAL_CHECKPOINT_ITER=900", ARM["run_config.env"].decode("utf-8").splitlines())
        block = ARM_RUNNER[ARM_RUNNER.index("# BEGIN CHECKPOINT PIN: config"):ARM_RUNNER.index("# END CHECKPOINT PIN: config")]
        for value, rc in (("", 2), ("abc", 2), ("900", 0)):
            done = subprocess.run([BASH, "-c", f"EVAL_CHECKPOINT_ITER={value}\n{block}\necho ok"],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, rc, value)
        for work in ("G-A031", "G-A032"):
            self.assertNotIn("EVAL_CHECKPOINT_ITER", pkg.run_config(pkg.load(work)))

    def test_spec_validation_ties_the_runner_to_the_iteration(self):
        for mutate in (lambda s: s["evaluation"].__setitem__("checkpoint_iter", 700),
                       lambda s: s["evaluation"].pop("checkpoint_iter"),
                       lambda s: s.__setitem__("runner", pkg.RUNNER)):
            bad = copy.deepcopy(SPEC)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                pkg.validate_spec(bad)

    def test_baseline_iteration_is_read_from_the_a017_checkpoint(self):
        model = staged.A017_TRAINING / "model_best.pt"
        if not model.is_file():
            self.skipTest("A017 training artifact not present")
        import pickletools
        with zipfile.ZipFile(model) as archive:
            data = archive.read(next(n for n in archive.namelist() if n.endswith("data.pkl")))
        previous, found = None, None
        for op, arg, _ in pickletools.genops(data):
            if previous == "iter" and op.name in ("BININT", "BININT1", "BININT2"):
                found = arg
                break
            previous = arg if op.name in ("SHORT_BINUNICODE", "BINUNICODE") else (
                previous if op.name in ("MEMOIZE", "BINPUT", "LONG_BINPUT") else None)
        self.assertEqual(found, SPEC["evaluation"]["checkpoint_iter"])
        self.assertEqual(pkg.BASELINE_CHECKPOINT_ITER["A017"], found)


@unittest.skipUnless((A027 / "evaluation" / "pilot" / "cases").is_dir() and (staged.A017_TRAINING / "env.yaml").is_file(),
                     "G-A027 harvest or A017 training not present")
class GateParityTest(unittest.TestCase):
    """Server gate, the runner's JSON reading and the local verifier agree on a G-A033 target harvest."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "campaign"
        for name, data in PAYLOAD.items():
            if not name.startswith("arms/"):
                (cls.root / name).parent.mkdir(parents=True, exist_ok=True)
                (cls.root / name).write_bytes(data)
        cls.package = Path(cls.tmp.name) / "arm"
        cls.package.mkdir()
        for name in ("experiment.json", "go2_self_eval_registry.json"):
            (cls.package / name).write_bytes(ARM[name])
        cls.stored = cls.root / "stored_baseline"
        cls.maker = staged.TargetStageHarvestTest("test_target_stage_readings")
        cls.registry = json.loads(a030v.REGISTRY.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def harvest(self, name: str, candidate_arm: str) -> Path:
        keep = Path(self.tmp.name) / name
        self.maker.make_harvest(keep, SPEC, candidate_arm)
        # make_harvest edits the feet_air_time weight; G-A033 changes the tracking weight instead.
        text = (staged.A017_TRAINING / "env.yaml").read_text(encoding="utf-8")
        head = text.index("  track_lin_vel_xy_exp:\n")
        cut = text.index("weight: 1.4", head)
        (keep / "training" / "env.yaml").write_text(text[:cut] + "weight: 1.5" + text[cut + len("weight: 1.4"):],
                                                    encoding="utf-8", newline="\n")
        status = (keep / "training" / "TRAIN_STATUS.txt").read_text(encoding="utf-8")
        (keep / "training" / "TRAIN_STATUS.txt").write_text(
            re.sub(r"SINGLE_CHANGE=.*", "SINGLE_CHANGE=track_lin_vel_xy_exp:1.4->1.5", status),
            encoding="utf-8", newline="\n")
        # 2026-09-24 (defect C-17): 이 회차는 make_harvest 가 쓴 env.yaml 을 **덮어썼다**.  후보
        # 신원의 `env_sha256` 은 학습된 env 의 해시여야 하므로, 덮어쓴 뒤의 파일로 다시 찍는다.
        identity = keep / "evaluation" / "candidate" / "identity.json"
        record = json.loads(identity.read_text(encoding="utf-8"))
        record["env_sha256"] = hashlib.sha256(
            (keep / "training" / "env.yaml").read_bytes()).hexdigest()
        identity.write_text(json.dumps(record), encoding="utf-8")
        pin_harvest(keep)
        return keep

    def standalone(self, keep: Path) -> tuple[int, str]:
        out = keep / "gate.json"
        done = subprocess.run([sys.executable, "-B", str(self.root / "go2_target_gate.py"), "--keep", str(keep),
                               "--package", str(self.package), "--stored", str(self.stored), "--out", str(out)],
                              capture_output=True, text=True, cwd=self.tmp.name)
        return done.returncode, bash_gate_reading(out.read_text(encoding="utf-8"), 1)

    def test_no_change_fails_everywhere(self):
        keep = self.harvest("same", "a017")
        server = gate.gate(keep, self.stored, SPEC, self.registry)
        local = verifier.verify(keep, A027, SPEC)
        self.assertEqual(local["artifact_faults"], [])
        self.assertEqual((server["verdict"], local["verdict"]), ("FAIL", "FAIL"))
        self.assertEqual(self.standalone(keep), (gate.EXIT["FAIL"], "FAIL"))

    def test_gain_passes_everywhere(self):
        keep = self.harvest("gain", "a017")
        self.maker.copy_arm(keep / "evaluation" / "a017", "pilot",
                            [SPEC["evaluation"]["catastrophe_case"], *pkg.targets(SPEC)], SPEC["baseline"]["model_sha256"])
        server = gate.gate(keep, self.stored, SPEC, self.registry)
        local = verifier.verify(keep, A027, SPEC)
        self.assertEqual((server["verdict"], local["verdict"]), ("TARGET_PASS", "TARGET_PASS_FULL_STAGE_REQUIRED"))
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0834, delta=0.001)
        self.assertEqual(self.standalone(keep), (gate.EXIT["TARGET_PASS"], "TARGET_PASS"))

    def test_unpinned_or_wrong_iteration_harvest_is_inconclusive(self):
        # A harvest evaluated at another checkpoint iteration is not comparable with A017's iter 900.
        keep = self.harvest("wrong_iter", "a017")
        pin = keep / "training" / "CHECKPOINT_PIN.txt"
        pin.write_text(pin.read_text(encoding="utf-8").replace("EVAL_CHECKPOINT_ITER=900", "EVAL_CHECKPOINT_ITER=700"),
                       encoding="utf-8", newline="\n")
        report = verifier.verify(keep, A027, SPEC)
        self.assertEqual(report["verdict"], "INCONCLUSIVE")
        self.assertTrue(any(f.startswith("candidate_eval_iter=") for f in report["artifact_faults"]))
        keep = self.harvest("no_pin", "a017")
        (keep / "training" / "CHECKPOINT_PIN.txt").unlink()
        self.assertEqual(verifier.verify(keep, A027, SPEC)["verdict"], "INCONCLUSIVE")

    def test_feet_harvest_is_refused_for_this_arm(self):
        # A harvest whose env carries another arm's change must not be read as G-A033.
        keep = self.harvest("wrong", "a017")
        (keep / "training" / "env.yaml").write_text((staged.A017_TRAINING / "env.yaml").read_text(encoding="utf-8"),
                                                    encoding="utf-8", newline="\n")
        self.assertEqual(verifier.verify(keep, A027, SPEC)["verdict"], "INCONCLUSIVE")


class ArchiveTest(unittest.TestCase):
    def test_archive_on_disk_matches_payload(self):
        output = campaign.output_path(CAMPAIGN)
        if not output.is_file():
            self.skipTest("run tools/build_go2_campaign_package.py G-A033 first")
        with zipfile.ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.namelist()), len(PAYLOAD))
            for name, data in PAYLOAD.items():
                self.assertEqual(archive.read(f"{CAMPAIGN['prefix']}/{name}"), data, name)
            self.assertTrue((archive.getinfo(f"{CAMPAIGN['prefix']}/{campaign.RUNNER}").external_attr >> 16) & 0o111)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        self.assertIn(digest, output.with_suffix(".zip.sha256").read_text(encoding="utf-8"))
        current = GO2 / "upload" / CAMPAIGN["upload_id"] / "current"
        if (current / output.name).is_file():
            self.assertEqual(hashlib.sha256((current / output.name).read_bytes()).hexdigest(), digest)
            self.assertIn(digest, (current / CAMPAIGN["guide"]).read_text(encoding="utf-8"))
            self.assertEqual([p.name for p in current.glob("*.zip")], [output.name])


if __name__ == "__main__":
    unittest.main()
