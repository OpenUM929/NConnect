"""Runner regression: performance failure must not erase mandatory A042 evidence.

The simulator is intentionally mocked.  These tests execute the runner's actual
decision/collection shell functions with fake case and video producers, so they
cover control flow without touching a deployed train/task/play file or a release.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.test_h1_report_recovery import BASH, shell_path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "workspace/training/quadruped/server_run_go2_candidate_iter_pinned.sh"
TEXT = RUNNER.read_text(encoding="utf-8")


def between(start: str, end: str) -> str:
    left = TEXT.index(start)
    right = TEXT.index(end, left)
    return TEXT[left:right]


FUNCTIONS = "\n".join(
    (
        between("catastrophe_action() {", "finish() {"),
        between("collect_candidate_target_cases() {", "collect_configured_videos() {"),
        between("collect_configured_videos() {", '\nif [[ "$STAGE" == target ]]'),
    )
)

# Includes both stair heights and the A042 non-scored protection records.  The
# production run_config has more scored cases; this mock is the minimal set that
# detects the audit's catastrophic loss mode.
MANDATORY = [
    "G5:stairs_10_down:101",
    "G5:stairs_15_down:101",
    "G5:stairs_15_down:202",
    "G5:stairs_15_down:303",
    "G2:left:101",
    "G2:right:101",
    "G6:push_neg_x:101",
    "G6:push_pos_y:101",
    "G6:push_neg_y:101",
]
CANDIDATE_VIDEOS = [
    "G5:stairs_10_down:101",
    "G5:stairs_15_down:101",
    "G3:rough_forward:101",
    "G3:rough_lateral:101",
]
BASELINE_VIDEOS = ["G5:stairs_15_down:101"]


def array(name: str, values: list[str]) -> str:
    return f"{name}=(" + " ".join(f"'{value}'" for value in values) + ")"


def run_mock(decision: str, collect_stationary: int, performance_verdict: str) -> list[str]:
    # Keep the mocked harvest inside the writable repository.  The host's
    # system TEMP may be outside the Git-Bash sandbox used by these tests.
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        root = Path(tmp)
        script = root / "mock.sh"
        script.write_text(
            f"""#!/usr/bin/env bash
set -euo pipefail
COLLECT_REQUIRED_ON_STATIONARY={collect_stationary}
{FUNCTIONS}
CANDIDATE_ROOT=candidate-root
CANDIDATE_MODEL=candidate-model
CANDIDATE_ENV=candidate-env
CANDIDATE_SHA=candidate-sha
CAND_OUT={shell_path(root / 'candidate-out')}
BASELINE_LABEL=baseline
BASELINE_ROOT=baseline-root
BASELINE_MODEL=baseline-model
BASELINE_ENV=baseline-env
{array('TARGET_CASES', MANDATORY)}
{array('CANDIDATE_VIDEOS', CANDIDATE_VIDEOS)}
{array('BASELINE_VIDEOS', BASELINE_VIDEOS)}
mkdir -p "$CAND_OUT/cases/seed_101/forward_nominal"
: >"$CAND_OUT/cases/seed_101/forward_nominal/summary.json"
run_case_list() {{
  shift 6
  local entry scenario case_id seed
  for entry in "$@"; do
    IFS=: read -r scenario case_id seed <<<"$entry"
    mkdir -p "$CAND_OUT/cases/seed_${{seed}}/${{case_id}}"
    : >"$CAND_OUT/cases/seed_${{seed}}/${{case_id}}/summary.json"
    printf 'CASE:%s\n' "$entry"
  done
}}
run_video_list() {{
  local label=$1
  shift 4
  local entry
  for entry in "$@"; do printf 'VIDEO:%s:%s\n' "$label" "$entry"; done
}}
DECISION={decision}
PERFORMANCE_VERDICT={performance_verdict}
ACTION=$(catastrophe_action "$DECISION")
printf 'ACTION:%s\n' "$ACTION"
if [[ "$ACTION" == CONTINUE || "$ACTION" == CONTINUE_REQUIRED ]]; then
  # TARGET_FAIL is deliberately not a condition around evidence collection.
  collect_candidate_target_cases
  collect_configured_videos
fi
""",
            encoding="utf-8",
            newline="\n",
        )
        completed = subprocess.run(
            [BASH, shell_path(script)], cwd=ROOT, check=False,
            text=True, encoding="utf-8", errors="replace", capture_output=True,
            env={**os.environ, "MSYS2_ARG_CONV_EXCL": "*"},
        )
        if completed.returncode != 0:
            raise AssertionError(f"mock rc={completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}")
        return completed.stdout.splitlines()


class MandatoryCollectionRunnerTest(unittest.TestCase):
    def assert_evidence_complete(self, lines: list[str]) -> None:
        cases = [line.removeprefix("CASE:") for line in lines if line.startswith("CASE:")]
        self.assertEqual(cases, MANDATORY)
        candidate = [line.split(":", 2)[2] for line in lines if line.startswith("VIDEO:candidate:")]
        baseline = [line.split(":", 2)[2] for line in lines if line.startswith("VIDEO:baseline_videos:")]
        self.assertEqual(candidate, CANDIDATE_VIDEOS)
        self.assertEqual(baseline, BASELINE_VIDEOS)

    def test_stationary_valid_policy_collects_all_mandatory_cases_and_videos(self) -> None:
        lines = run_mock("CATASTROPHE_STATIONARY", 1, "TARGET_FAIL")
        self.assertIn("ACTION:CONTINUE_REQUIRED", lines)
        self.assert_evidence_complete(lines)

    def test_ordinary_target_fail_does_not_gate_collection(self) -> None:
        lines = run_mock("SUITE_COMPLETE", 1, "TARGET_FAIL")
        self.assertIn("ACTION:CONTINUE", lines)
        self.assert_evidence_complete(lines)

    def test_nonfinite_or_unexecutable_path_stops_without_more_simulator_work(self) -> None:
        lines = run_mock("CATASTROPHE_TRAINING_NONFINITE", 1, "UNDECIDED")
        self.assertEqual(lines, ["ACTION:STOP_UNSAFE"])

    def test_stationary_collection_is_opt_in_for_older_campaigns(self) -> None:
        lines = run_mock("CATASTROPHE_STATIONARY", 0, "TARGET_FAIL")
        self.assertEqual(lines, ["ACTION:STOP_WITH_WITNESS"])

    def test_production_flow_uses_the_tested_helpers_after_the_catastrophe_gate(self) -> None:
        action = TEXT.index('COLLECTION_ACTION=$(catastrophe_action "$DECISION")')
        targets = TEXT.index("  collect_candidate_target_cases || exit $?", action)
        videos = TEXT.index("collect_configured_videos", targets)
        finish = TEXT.index('finish "$STAGE_DECISION" "$BASELINE_ARM"', videos)
        self.assertLess(action, targets)
        self.assertLess(targets, videos)
        self.assertLess(videos, finish)
        self.assertNotIn("TARGET_FAIL", TEXT[action:finish],
                         "a performance verdict must not wrap mandatory collection")

    def test_runner_is_valid_bash(self) -> None:
        completed = subprocess.run([BASH, "-n", shell_path(RUNNER)], cwd=ROOT, check=False,
                                   text=True, encoding="utf-8", errors="replace", capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
