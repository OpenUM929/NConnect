"""Contract tests for the staged basic-motion packages G-A031 / G-A032 (feet_air_time dose pair).

Local only: no simulator, no training.  Run from the repository root:
    python -m unittest tools.test_go2_basic_motion_package_contract
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
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

import build_go2_candidate_package as pkg  # noqa: E402
import build_go2_g_a030_package as a030  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_fixed_eval_report import build_policy  # noqa: E402
from go2_tuning_config import reward_dict  # noqa: E402
from tools.test_h1_report_recovery import BASH, shell_path  # noqa: E402

KEEP = ROOT / "workspace" / "_keep"
A027 = KEEP / "go2_a017_full_suite"
A017_TRAINING = KEEP / "go2_g_a017_pilot_track_lin_vel_xy_140" / "training"
# The feet_air_time dose pair.  G-A033 (track 1.5) is checked in test_go2_campaign_contract.
SPECS = {work: pkg.load(work) for work in ("G-A031", "G-A032")}
PAYLOADS = {work: pkg.build_payload(spec) for work, spec in SPECS.items()}
A030_PAYLOAD = a030.build_payload(a030.load_spec())
DOSE = {"G-A031": 0.01, "G-A032": 0.1}
STAGED = (GO2 / pkg.RUNNER).read_text(encoding="utf-8")
SUITE = (GO2 / pkg.SUITE_RUNNER).read_text(encoding="utf-8")
# 2026-09-17: the staged runner creates the video log directory (G-A038's stop); G-A030's suite
# runner and the executed G-A031/G-A032 copy do not.  That fix is the only difference.
VIDEO_FIX = (
    '  # The video label (<baseline>_videos) has no eval cases, so nothing else creates its log\n'
    '  # directory; without it tee fails and pipefail ends the run (G-A038, 2026-09-17).\n'
    '  mkdir -p exported "$KEEP/evaluation/$label/videos" "$KEEP/logs/$label"\n'
)
VIDEO_ORIGINAL = '  mkdir -p exported "$KEEP/evaluation/$label/videos"\n'
STAGED_BEFORE_FIX = STAGED.replace(VIDEO_FIX, VIDEO_ORIGINAL)


def extract(text: str, start: str, end: str) -> str:
    head = text.index(start)
    return text[head: text.index(end, head) + len(end)]


class PayloadTest(unittest.TestCase):
    def test_manifest_covers_every_member(self):
        for work, payload in PAYLOADS.items():
            lines = payload["PACKAGE_SHA256SUMS.txt"].decode("utf-8").splitlines()
            self.assertEqual(len(lines), len(payload) - 1, work)
            for line in lines:
                digest, name = line.split("  ", 1)
                self.assertEqual(hashlib.sha256(payload[name]).hexdigest(), digest, f"{work} {name}")

    def test_single_variable_is_feet_air_time_only(self):
        for work, payload in PAYLOADS.items():
            cand = reward_dict(payload["candidate/quadruped_rewards.py"].decode("utf-8"))
            ref = reward_dict(payload["reference/baseline_quadruped_rewards.py"].decode("utf-8"))
            self.assertEqual(ref, SPECS[work]["rewards"]["baseline"])
            self.assertEqual(cand, SPECS[work]["rewards"]["candidate"])
            self.assertEqual([k for k in cand if cand[k] != ref[k]], ["feet_air_time"])
            self.assertEqual((ref["feet_air_time"], cand["feet_air_time"]), (0.2, DOSE[work]))
            diff = [(a, b) for a, b in zip(payload["reference/baseline_quadruped_rewards.py"].splitlines(),
                                           payload["candidate/quadruped_rewards.py"].splitlines()) if a != b]
            self.assertEqual(len(diff), 1, f"{work}: text diff must be one line")

    def test_everything_else_is_the_g_a030_package(self):
        # Same evaluator, registry, helpers, deployed code, A017 baseline role and reference
        # reward file as G-A030; the runner is the staged copy (RunnerTest), and only the
        # dial and the run identity differ otherwise.
        expected = ["PACKAGE_SHA256SUMS.txt", "README.txt", "candidate/quadruped_rewards.py",
                    "expected_rewards.json", "experiment.json", "run_config.env"]
        theirs = set(A030_PAYLOAD) - {pkg.SUITE_RUNNER}
        for work, payload in PAYLOADS.items():
            self.assertEqual(set(payload) - {pkg.RUNNER}, theirs, work)
            self.assertEqual(sorted(n for n in theirs if payload[n] != A030_PAYLOAD[n]), expected, work)
            # both releases ran: they ship the runner bytes they ran with
            self.assertEqual(payload[pkg.RUNNER], pkg.runner_bytes(SPECS[work]))
            self.assertEqual(payload[pkg.RUNNER], STAGED_BEFORE_FIX.encode("utf-8"))

    def test_deployed_code_is_unchanged_r6(self):
        for work, payload in PAYLOADS.items():
            for name, data in payload.items():
                role, _, rel = name.partition("/")
                if role in ("candidate", "baseline") and not rel.startswith("exported/") \
                        and name != "candidate/quadruped_rewards.py":
                    self.assertEqual(data, (GO2 / rel).read_bytes(), f"{work} {name}")

    def test_baseline_rewards_are_what_a017_was_trained_with(self):
        trained = A017_TRAINING / "source" / "quadruped_rewards.py"
        if not trained.is_file():
            self.skipTest("A017 training source not present")
        for spec in SPECS.values():
            self.assertEqual(reward_dict(trained.read_text(encoding="utf-8")), spec["rewards"]["baseline"])

    def test_pair_differs_only_in_the_dose_and_identity(self):
        a, b = copy.deepcopy(SPECS["G-A031"]), copy.deepcopy(SPECS["G-A032"])
        for spec in (a, b):
            for key in ("work_id", "run_id", "experiment_slug", "pair", "output", "why", "single_change"):
                spec.pop(key)
            for key in ("candidate", "direction", "after_change_vs_go2_rough"):
                spec["external_reference"].pop(key)
            spec["rewards"]["candidate"].pop("feet_air_time")
        self.assertEqual(a, b)
        outputs = [SPECS[w]["output"] for w in SPECS]
        for key in ("package_root", "keep_dir_name", "result_zip", "done_marker", "tmux_name", "upload_zip"):
            self.assertNotEqual(outputs[0][key], outputs[1][key], key)

    def test_spec_tampering_is_refused(self):
        spec = SPECS["G-A031"]
        self.assertEqual(spec["external_reference"]["isaaclab_go2_rough"], spec["rewards"]["candidate"]["feet_air_time"])
        for mutate in (lambda s: s["external_reference"].__setitem__("isaaclab_go2_rough", 0.02),
                       lambda s: s.pop("external_reference"),
                       lambda s: s["rewards"]["candidate"].__setitem__("track_lin_vel_xy_exp", 1.5),
                       lambda s: s["baseline"].__setitem__("model_sha256", "0" * 64),
                       lambda s: s["videos"]["candidate"].append("G6:push_neg_y:202"),
                       lambda s: s["preregistered"]["target_groups"]["rough_forward"].append("G1:forward_nominal:101")):
            bad = copy.deepcopy(spec)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                pkg.validate_spec(bad)

    def test_videos_are_relevant_and_have_baseline_counterparts(self):
        for spec in SPECS.values():
            videos = spec["videos"]
            self.assertEqual(len(videos["candidate"]), 5)
            self.assertEqual(videos["baseline"], [])
            stored = A027 / "evaluation" / "a017" / "videos"
            if stored.is_dir():
                for entry in videos["candidate"]:
                    scenario, case_id, seed = entry.split(":")
                    self.assertTrue((stored / f"{scenario}_{case_id}_seed_{seed}.mp4").is_file(), entry)

    def test_run_config_is_the_spec(self):
        for work, payload in PAYLOADS.items():
            script = payload["run_config.env"].decode("utf-8") + (
                'printf "%s|" "$WORK_ID" "$SINGLE_CHANGE_NAME" "$SINGLE_CHANGE_TO" "$TRAIN_SEED" "$MAX_ITERATIONS" '
                '"$BASELINE_MODEL_SHA" "$EXPECTED_EVALUATOR_SHA" "$CATASTROPHE_CASE" "$DONE_MARKER" "$TMUX_NAME" '
                '"${#SENTINEL_CASES[@]}" "${#CANDIDATE_VIDEOS[@]}" "${#BASELINE_VIDEOS[@]}" "${#TARGET_CASES[@]}" '
                '"${TARGET_CASES[0]}" "${TARGET_CASES[8]}"\n')
            done = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            spec = SPECS[work]
            self.assertEqual(done.stdout.split("|")[:-1], [
                work, "feet_air_time", str(DOSE[work]), "42", "1000", spec["baseline"]["model_sha256"],
                spec["baseline"]["evaluator_sha256"], "G1:forward_nominal:101", spec["output"]["done_marker"],
                spec["output"]["tmux_name"], "5", "5", "0", "9", "G3:rough_forward:101", "G7:dr_seed_303:303"])

    def test_every_run_line_passes_package_root(self):
        for work, spec in SPECS.items():
            root = spec["output"]["package_root"]
            guide = pkg.run_guide(spec, "0" * 64)
            readme = PAYLOADS[work]["README.txt"].decode("utf-8")
            self.assertIn(f"PACKAGE_ROOT={root} bash {root}/{pkg.RUNNER}", guide)
            self.assertIn(f"GO2_STAGE=full GO2_RESUME=1 PACKAGE_ROOT={root} bash {root}/{pkg.RUNNER}", guide)
            for text in (guide, readme):
                for row in text.splitlines():
                    if f"bash /workspace/go2_g_a03" in row:
                        self.assertIn("PACKAGE_ROOT=", row, row)


class RunnerTest(unittest.TestCase):
    def test_runner_is_lf_and_parses(self):
        self.assertNotIn("\r", STAGED)
        done = subprocess.run([BASH, "-n", shell_path(GO2 / pkg.RUNNER)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_shared_code_is_the_g_a030_runner(self):
        for start, end in (("set_case() {", "\n}\n"), ("run_eval_case() {", "\n}\n"), ("stage_policy() {", "\n}\n"),
                           ("write_identity() {", "\nIDEOF\n}\n"), ("run_full_suite() {", "\n}\n"),
                           ("run_video() {", "\n}\n"), ("run_video_list() {", "\n}\n"),
                           ("# BEGIN GO2_REPORT_RECOVERY", "# END GO2_REPORT_RECOVERY\n"),
                           ('echo "[PHASE 1/6]', "CAND_OUT=\"$KEEP/evaluation/candidate\"\n"),
                           ('echo "[PHASE 2/6]', "\nfi\n")):
            self.assertEqual(extract(STAGED_BEFORE_FIX, start, end), extract(SUITE, start, end), start)
        self.assertEqual(STAGED.count(VIDEO_FIX), 1)
        self.assertEqual(STAGED_BEFORE_FIX, (pkg.RUNNER_HISTORY / "server_run_go2_candidate_staged.5ce14f1cdc1da54e.sh")
                         .read_text(encoding="utf-8"))

    def test_g_a030_runner_is_untouched(self):
        with zipfile.ZipFile(a030.OUTPUT) as archive:
            self.assertEqual(archive.read(f"go2_g_a030/{pkg.SUITE_RUNNER}").decode("utf-8"), SUITE)

    def test_stages(self):
        self.assertIn("STAGE=${GO2_STAGE:-target}", STAGED)
        self.assertIn('[[ "$STAGE" == target || "$STAGE" == full ]]', STAGED)
        self.assertIn("GO2_STAGE=%q", STAGED)
        self.assertIn("bash server_run_go2_candidate_staged.sh --inner", STAGED)
        self.assertIn('PACKAGE_ROOT=${PACKAGE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}', STAGED)
        self.assertNotIn("go2_g_a030", STAGED)
        order = ["-p train.py", "[PHASE 2/6]", "run_case_list candidate", "STAGE_DECISION=TARGET_STAGE_COMPLETE",
                 "run_full_suite candidate ", "STAGE_DECISION=SUITE_COMPLETE", "[PHASE 4/6]",
                 'run_video_list candidate "$CANDIDATE_ROOT" "$CANDIDATE_MODEL" "$CANDIDATE_ENV" "${CANDIDATE_VIDEOS',
                 'finish "$STAGE_DECISION"']
        positions = [STAGED.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions), order)
        self.assertIn("printf 'STAGE=%s\\n' \"$STAGE\" >>\"$KEEP/RUNNER_STATUS.txt\"", STAGED)
        self.assertEqual(STAGED.count("-p train.py"), 1)


@unittest.skipUnless((A027 / "evaluation" / "pilot" / "cases").is_dir(), "G-A027 harvest not present")
class JudgeTest(unittest.TestCase):
    """The pre-registered full-stage reading, exercised on real 69-case arms."""

    @classmethod
    def setUpClass(cls):
        reg = GO2 / "config" / "go2_self_eval_registry.json"
        cls.a017 = build_policy(A027 / "evaluation" / "a017", reg, {})
        cls.pilot = build_policy(A027 / "evaluation" / "pilot", reg, {})
        cls.prereg = SPECS["G-A031"]["preregistered"]
        assert cls.prereg == SPECS["G-A032"]["preregistered"]

    def test_no_change_is_not_success(self):
        result = verifier.judge(self.a017, self.a017, self.prereg)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["failed"], ["1_target_basic_motion"])

    def test_track_140_replay_passes(self):
        # Pilot -> A017 (track 1.2 -> 1.4, adopted G-D184).  Its three new stationary cases
        # are all stairs_15_down, outside the basic-motion guard.
        result = verifier.judge(self.pilot, self.a017, self.prereg)
        self.assertEqual(result["verdict"], "QUANT_SUCCESS_VIDEO_REVIEW_PENDING")
        self.assertAlmostEqual(result["target_mean_proxy_delta"], 0.0834, delta=0.001)
        self.assertEqual(result["target_groups_improved"], 3)
        self.assertAlmostEqual(result["points_70"]["delta"], 6.09, delta=0.01)
        self.assertEqual(result["locomotion"]["new_stationary_in_guard"], [])

    def test_reverse_replay_fails_on_target_total_and_flat(self):
        result = verifier.judge(self.a017, self.pilot, self.prereg)
        self.assertEqual(result["failed"], ["1_target_basic_motion", "2_total_points_delta", "3_non_inferiority"])

    def test_standing_in_basic_motion_fails(self):
        cand = copy.deepcopy(self.a017)
        cand["locomotion"]["stationary_cases"] = cand["locomotion"]["stationary_cases"] + ["G4/slope_plus_20/seed_202"]
        self.assertFalse(verifier.judge(self.a017, cand, self.prereg)["criteria"]["4_locomotion"])

    def test_flat_drop_is_caught(self):
        cand = copy.deepcopy(self.a017)
        cand["scenarios"]["G1"]["scenario_proxy"] -= 0.03
        self.assertFalse(verifier.judge(self.a017, cand, self.prereg)["criteria"]["3_non_inferiority"])


@unittest.skipUnless((A027 / "evaluation" / "pilot" / "cases").is_dir() and (A017_TRAINING / "env.yaml").is_file(),
                     "G-A027 harvest or A017 training not present")
class TargetStageHarvestTest(unittest.TestCase):
    """End to end on a synthetic target-stage harvest built from real G-A027 cases."""

    def make_harvest(self, keep: Path, spec: dict, candidate_arm: str) -> None:
        base = spec["baseline"]
        text = (A017_TRAINING / "env.yaml").read_text(encoding="utf-8")
        head = text.index("  feet_air_time:\n")
        cut = text.index("weight: 0.2", head)
        env = text[:cut] + f"weight: {spec['single_change']['to']}" + text[cut + len("weight: 0.2"):]
        model = b"synthetic candidate model"
        files = {
            "RESULT_STATUS.txt": "RESULT_STATE=FULL\n",
            "exported/report.html": "<html>synthetic</html>\n",
            "exported/REPORT_STATUS.txt": "REPORT_STATUS=REPORT_ACQUIRED\n",
            "training/TRAIN_STATUS.txt": "TRAIN_RC=0\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS=1000\n"
                                         f"SINGLE_CHANGE=feet_air_time:0.2->{spec['single_change']['to']}\n",
            "training/env.yaml": env,
            "meta/evaluator.sha256": f"{base['evaluator_sha256']}  go2_eval_telemetry.py\n",
            "meta/registry.sha256": f"{base['registry_sha256']}  go2_self_eval_registry.json\n",
        }
        for name, content in files.items():
            (keep / name).parent.mkdir(parents=True, exist_ok=True)
            (keep / name).write_text(content, encoding="utf-8", newline="\n")
        (keep / "training" / "model_best.pt").write_bytes(model)
        report = (keep / "exported" / "report.html").read_bytes()
        (keep / "exported" / "report.html.sha256").write_text(f"{hashlib.sha256(report).hexdigest()}  report.html\n")
        model_sha = hashlib.sha256(model).hexdigest()
        (keep / "RUNNER_STATUS.txt").write_text(
            f"RUNNER_RC=0\nWORK_ID={spec['work_id']}\nDECISION=TARGET_STAGE_COMPLETE\nCANDIDATE_MODEL_SHA={model_sha}\n"
            "STAGE=target\n", encoding="utf-8")
        self.copy_arm(keep / "evaluation" / "candidate", candidate_arm,
                      [spec["evaluation"]["catastrophe_case"], *pkg.targets(spec)], model_sha,
                      hashlib.sha256(env.encode("utf-8")).hexdigest())
        self.copy_arm(keep / "evaluation" / "a017_sentinel", "a017", spec["evaluation"]["sentinel_cases"],
                      base["model_sha256"])
        (keep / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(report).hexdigest()}  ./exported/report.html\n")

    def copy_arm(self, out: Path, arm: str, entries: list[str], model_sha: str,
                 env_sha: str | None = None) -> None:
        # 2026-09-24 (defect C-17): `env_sha256` 은 `go2_screening_gate.IDENTITY_FIELDS` 의 네 칸
        # 중 하나다.  이 하네스가 그 칸을 빼먹어서 screening 신원이 서지 않았고, 합쳐진 판정이
        # 결정적 FAIL/TARGET_PASS 자리에서 INCONCLUSIVE 로 덮였다(fail-closed 라 성공을 주장하는
        # 쪽으로는 틀리지 않으나, 판정을 잃는다).  진짜 수확물은 이 칸을 쓴다 — 자료만 채운다.
        base = SPECS["G-A031"]["baseline"]
        for entry in entries:
            _, case_id, seed = entry.split(":")
            shutil.copytree(A027 / "evaluation" / arm / "cases" / f"seed_{seed}" / case_id,
                            out / "cases" / f"seed_{seed}" / case_id)
        (out / "identity.json").write_text(json.dumps({
            "model_sha256": model_sha, "env_sha256": env_sha or base["env_sha256"],
            "evaluator_sha256": base["evaluator_sha256"],
            "registry_sha256": base["registry_sha256"]}), encoding="utf-8")

    def test_target_stage_readings(self):
        spec = SPECS["G-A031"]
        with tempfile.TemporaryDirectory() as tmp:
            keep = Path(tmp) / "harvest"
            # The candidate is A017 itself: no change, so criterion 1 fails and the arm ends.
            self.make_harvest(keep, spec, "a017")
            result = verifier.verify(keep, A027, spec)
            self.assertEqual(result["artifact_faults"], [])
            self.assertEqual(result["verdict"], "FAIL", result.get("stage_faults"))
            self.assertAlmostEqual(result["target_stage"]["target_mean_proxy_delta"], 0.0, places=9)
            self.assertTrue(result["sentinel"]["agrees"])

            # Same candidate against a same-run baseline that is Pilot: the Pilot -> A017
            # target gain (+.083, 3 groups) passes criterion 1 and asks for the full stage.
            self.copy_arm(keep / "evaluation" / "a017", "pilot",
                          [spec["evaluation"]["catastrophe_case"], *pkg.targets(spec)], spec["baseline"]["model_sha256"])
            result = verifier.verify(keep, A027, spec)
            self.assertEqual(result["verdict"], "TARGET_PASS_FULL_STAGE_REQUIRED", result.get("stage_faults"))
            self.assertEqual(result["baseline_arm"], "REMEASURED_SAME_RUN")
            self.assertAlmostEqual(result["target_stage"]["target_mean_proxy_delta"], 0.0834, delta=0.001)

            # A missing target case is missing data, never a verdict.
            shutil.rmtree(keep / "evaluation" / "candidate" / "cases" / "seed_202" / "slope_plus_20")
            self.assertEqual(verifier.verify(keep, A027, spec)["verdict"], "INCONCLUSIVE")


class ArchiveTest(unittest.TestCase):
    def test_archive_on_disk_matches_payload(self):
        for work, spec in SPECS.items():
            output = pkg.output_path(spec)
            if not output.is_file():
                self.skipTest(f"run tools/build_go2_candidate_package.py {work} first")
            root = pkg.prefix(spec).as_posix()
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(len(archive.namelist()), len(PAYLOADS[work]))
                for name, data in PAYLOADS[work].items():
                    self.assertEqual(archive.read(f"{root}/{name}"), data, name)
                self.assertTrue((archive.getinfo(f"{root}/{pkg.RUNNER}").external_attr >> 16) & 0o111)
            digest = hashlib.sha256(output.read_bytes()).hexdigest()
            self.assertIn(digest, output.with_suffix(".zip.sha256").read_text(encoding="utf-8"))
            current = pkg.upload_dir(spec) / "current"
            if (current / output.name).is_file():
                self.assertEqual(hashlib.sha256((current / output.name).read_bytes()).hexdigest(), digest)
                self.assertIn(digest, (current / pkg.guide_name(spec)).read_text(encoding="utf-8"))
                self.assertEqual(sorted(p.suffix for p in current.glob("*.zip")), [".zip"], "one ZIP in current/")


if __name__ == "__main__":
    unittest.main()
