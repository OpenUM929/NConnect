"""Contract tests for the one-file pair package G-A031 + G-A032.

Local only: no simulator, no training.  Run from the repository root:
    python -m unittest tools.test_go2_basic_motion_pair_contract
"""

from __future__ import annotations

import hashlib
import json
import re
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

import build_go2_basic_motion_pair as pair  # noqa: E402
import build_go2_candidate_package as pkg  # noqa: E402
import go2_target_gate as gate  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
import verify_go2_g_a030_harvest as a030v  # noqa: E402
import tools.test_go2_basic_motion_package_contract as staged  # noqa: E402
from tools.test_h1_report_recovery import BASH, shell_path  # noqa: E402

A027 = staged.A027
SPECS = {work: pkg.load(work) for work in pair.ARMS}
PAYLOAD = pair.build_payload()
RUNNER = (GO2 / pair.RUNNER).read_text(encoding="utf-8")
# The runner the pair arms shipped and ran with (kept in runner_history after the 2026-09-17 fix).
ARM_RUNNER = pkg.runner_bytes(SPECS["G-A031"]).decode("utf-8")


def function(text: str, name: str) -> str:
    head = text.index(f"{name}() ")
    return text[head: text.index("\n}\n", head) + 3]


class PairPayloadTest(unittest.TestCase):
    def test_arms_are_the_published_arm_zips(self):
        config = PAYLOAD["pair_config.env"].decode("utf-8")
        for work, spec in SPECS.items():
            name = spec["output"]["upload_zip"]
            data = PAYLOAD[f"arms/{name}"]
            self.assertEqual(data, pkg.output_path(spec).read_bytes(), work)
            current = pkg.upload_dir(spec) / "current" / name
            if current.is_file():
                self.assertEqual(data, current.read_bytes(), work)
            self.assertIn(hashlib.sha256(data).hexdigest(), config)
            with zipfile.ZipFile(pkg.output_path(spec)) as archive:
                self.assertEqual(archive.read(f"{pkg.prefix(spec).as_posix()}/{pkg.RUNNER}").decode("utf-8"),
                                 ARM_RUNNER)

    def test_gate_files_are_the_repository_files(self):
        # 2026-09-17: this release ran; its gate is the frozen copy in runner_history (the working tree
        # gate now reads fact_rules_v1).  The two dependencies are unchanged.
        for name, path in pair.GATE_FILES.items():
            expected = pair.EXECUTED_GATE if name == "go2_target_gate.py" else path
            self.assertEqual(PAYLOAD[name], expected.read_bytes(), name)
        self.assertNotIn("go2_fact_rules.py", PAYLOAD)
        self.assertEqual(PAYLOAD[pair.RUNNER].decode("utf-8"), RUNNER)

    @unittest.skipUnless((A027 / "evaluation" / "a017" / "cases").is_dir(), "G-A027 harvest not present")
    def test_stored_summaries_are_the_g_a027_arm(self):
        spec = SPECS["G-A031"]
        stored = {name: data for name, data in PAYLOAD.items() if name.startswith("stored_baseline/")}
        entries = pair.stored_entries(spec)
        self.assertEqual(len(entries), 11)
        self.assertEqual(len(stored), len(entries) + 1)
        for name, data in stored.items():
            self.assertEqual(data, (A027 / name.split("/", 1)[1]).read_bytes(), name)
        for entry in [spec["evaluation"]["catastrophe_case"], *pkg.targets(spec), *spec["evaluation"]["sentinel_cases"]]:
            _, case_id, seed = entry.split(":")
            self.assertIn(f"stored_baseline/evaluation/a017/cases/seed_{seed}/{case_id}/summary.json", stored)

    def test_manifest_covers_every_member(self):
        lines = PAYLOAD["PAIR_SHA256SUMS.txt"].decode("utf-8").splitlines()
        listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in lines}
        self.assertEqual(set(listed), set(PAYLOAD) - {"PAIR_SHA256SUMS.txt"})
        for name, digest in listed.items():
            self.assertEqual(hashlib.sha256(PAYLOAD[name]).hexdigest(), digest, name)

    def test_pair_config_reads_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pair_config.env"
            path.write_bytes(PAYLOAD["pair_config.env"])
            script = (f"source {shell_path(path)}; printf '%s|' \"$PAIR_ID\" \"$PAIR_TMUX\" \"$PAIR_DONE_MARKER\" "
                      "\"${ARM_WORK[@]}\" \"${ARM_ROOT[@]}\" \"${#ARM_ZIP_SHA[@]}\"")
            done = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.split("|")[:-1], [
            pair.PAIR_ID, pair.TMUX, pair.DONE_MARKER, "G-A031", "G-A032",
            SPECS["G-A031"]["output"]["package_root"], SPECS["G-A032"]["output"]["package_root"], "2"])


class PairRunnerTest(unittest.TestCase):
    def test_runner_is_lf_and_parses(self):
        self.assertNotIn("\r", RUNNER)
        done = subprocess.run([BASH, "-n", shell_path(GO2 / pair.RUNNER)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_gpu_work_goes_through_the_arm_runner_only(self):
        self.assertNotIn("-p train.py", RUNNER)
        self.assertNotIn("play.py --task", RUNNER)
        stage = function(RUNNER, "run_stage")
        for text in ('PACKAGE_ROOT="$root"', 'GO2_STAGE="$stage"', 'GO2_RESUME="$resume"',
                     'GO2_REMEASURE_BASELINE="$remeasure"', 'bash "$ARM_RUNNER" --inner'):
            self.assertIn(text, stage)
        self.assertIn("ARM_RUNNER=server_run_go2_candidate_staged.sh", RUNNER)

    def test_order_and_gating(self):
        order = ['target_phase "$root"', 'full_phase "$root"', "package_pair PAIR_COMPLETE 0", 'echo "$PAIR_DONE_MARKER"']
        main = RUNNER[RUNNER.index('log "[START]'):]
        positions = [main.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        full = function(RUNNER, "full_phase")
        self.assertIn('[[ "${STATE[$work]:-}" == TARGET_PASS ]] || return 0', full)
        self.assertEqual(RUNNER.count("run_stage \"$root\" full"), 1)
        target = function(RUNNER, "target_phase")
        self.assertLess(target.index('run_gate "$root" target)'), target.index("TARGET_PASS) STATE[$work]=TARGET_PASS"))
        # The remeasure retry happens once, and only from the stored arm.
        self.assertIn('"$verdict" == REMEASURE_BASELINE && "$remeasure" == 0', target)

    def test_gate_exit_codes_match_the_runner(self):
        body = function(RUNNER, "run_gate")
        mapping = dict(re.findall(r"^\s+(\d+)\) echo (\w+) ;;$", body, re.M))
        self.assertEqual(mapping, {str(code): name for name, code in gate.EXIT.items() if name != "UNDECIDED"})
        self.assertIn("*) echo UNDECIDED ;;", body)

    def test_preflight_mirrors_the_arm_runner(self):
        outer = ARM_RUNNER[ARM_RUNNER.index('if [[ "${1:-}" != "--inner" ]]'):ARM_RUNNER.index("printf -v INNER_COMMAND")]
        for token in ("EXPECTED_EVALUATOR_SHA", "EXPECTED_REGISTRY_SHA", "BASELINE_MODEL_SHA", "BASELINE_ENV_SHA",
                      "TARGET_CASES", "pgrep -af 'train.py|isaaclab.sh.*train.py|play.py|isaaclab.sh.*play.py'",
                      "GO2_DISCARD_PREVIOUS", "tmux has-session"):
            self.assertIn(token, outer)
            self.assertIn(token, RUNNER)
        self.assertIn('PAIR_ROOT=${PAIR_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}', RUNNER)


@unittest.skipUnless((A027 / "evaluation" / "pilot" / "cases").is_dir() and (staged.A017_TRAINING / "env.yaml").is_file(),
                     "G-A027 harvest or A017 training not present")
class GateParityTest(unittest.TestCase):
    """The server gate and the local verifier read the same target-stage harvest the same way."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pair_root = Path(cls.tmp.name) / "pair"
        for name, data in PAYLOAD.items():
            if not name.startswith("arms/"):
                (cls.pair_root / name).parent.mkdir(parents=True, exist_ok=True)
                (cls.pair_root / name).write_bytes(data)
        cls.package = Path(cls.tmp.name) / "arm"
        cls.package.mkdir()
        arm = pkg.build_payload(SPECS["G-A031"])
        for name in ("experiment.json", "go2_self_eval_registry.json"):
            (cls.package / name).write_bytes(arm[name])
        cls.stored = cls.pair_root / "stored_baseline"
        cls.maker = staged.TargetStageHarvestTest("test_target_stage_readings")
        cls.registry = json.loads(a030v.REGISTRY.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def harvest(self, name: str, candidate_arm: str) -> Path:
        keep = Path(self.tmp.name) / name
        self.maker.make_harvest(keep, SPECS["G-A031"], candidate_arm)
        return keep

    def both(self, keep: Path) -> tuple[dict, dict]:
        spec = SPECS["G-A031"]
        return gate.gate(keep, self.stored, spec, self.registry), verifier.verify(keep, A027, spec)

    def standalone(self, keep: Path) -> int:
        done = subprocess.run([sys.executable, "-B", str(self.pair_root / "go2_target_gate.py"), "--keep", str(keep),
                               "--package", str(self.package), "--stored", str(self.stored)],
                              capture_output=True, text=True, cwd=self.tmp.name)
        return done.returncode

    def test_no_change_fails_on_both(self):
        keep = self.harvest("same", "a017")
        server, local = self.both(keep)
        self.assertEqual((server["verdict"], local["verdict"]), ("FAIL", "FAIL"))
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"],
                               local["target_stage"]["target_mean_proxy_delta"], places=12)
        self.assertEqual(server["sentinel"], local["sentinel"])
        self.assertEqual(self.standalone(keep), gate.EXIT["FAIL"])

    def test_gain_passes_on_both(self):
        keep = self.harvest("gain", "a017")
        spec = SPECS["G-A031"]
        self.maker.copy_arm(keep / "evaluation" / "a017", "pilot",
                            [spec["evaluation"]["catastrophe_case"], *pkg.targets(spec)], spec["baseline"]["model_sha256"])
        server, local = self.both(keep)
        self.assertEqual((server["verdict"], local["verdict"]), ("TARGET_PASS", "TARGET_PASS_FULL_STAGE_REQUIRED"))
        # 2026-09-24 (defect C-33) — **이름 붙인 발산**.  S-4(2026-09-19) 가 서버 게이트의 1단계에
        # `stationary_guard` 를 넣었으나 로컬 판독기의 1단계에는 그것이 없다(로컬은 전수 단계의
        # `4_locomotion` 으로만 본다).  그러므로 두 판독기는 1단계에서 **같은 것을 읽지 않는다** —
        # 서버가 더 엄하고, 방향은 fail-closed 다.  칸 대조에서 그 블록을 빼되, 빠진 사실 자체를
        # 여기서 단정해 조용히 사라지지 않게 한다.  C-33 이 닫히면 이 두 줄이 빨개져서 알려준다.
        self.assertEqual({k: v for k, v in server["target_stage"].items() if k != "stationary_guard"},
                         {k: v for k, v in local["target_stage"].items()
                          if k not in ("catastrophe_case", "note")})
        self.assertTrue(server["target_stage"]["stationary_guard"]["passed"])
        self.assertNotIn("stationary_guard", local["target_stage"],
                         "C-33 이 닫혔다 — 이 검사를 두 판독기의 대조로 되돌려라")
        self.assertAlmostEqual(server["target_stage"]["target_mean_proxy_delta"], 0.0834, delta=0.001)
        self.assertEqual(self.standalone(keep), gate.EXIT["TARGET_PASS"])

    def test_missing_case_is_undecided(self):
        keep = self.harvest("missing", "a017")
        shutil.rmtree(keep / "evaluation" / "candidate" / "cases" / "seed_202" / "slope_plus_20")
        server, local = self.both(keep)
        self.assertEqual((server["verdict"], local["verdict"]), ("UNDECIDED", "INCONCLUSIVE"))
        self.assertEqual(self.standalone(keep), gate.EXIT["UNDECIDED"])

    def test_sentinel_drift_asks_for_the_remeasure(self):
        keep = self.harvest("drift", "a017")
        target = keep / "evaluation" / "a017_sentinel" / "cases" / "seed_101" / "rough_lateral"
        shutil.rmtree(target)
        shutil.copytree(A027 / "evaluation" / "pilot" / "cases" / "seed_101" / "rough_lateral", target)
        server, local = self.both(keep)
        self.assertEqual((server["verdict"], local["verdict"]), ("REMEASURE_BASELINE", "BASELINE_REMEASURE_REQUIRED"))
        self.assertEqual(server["sentinel"], a030v.compare_sentinel(keep, A027, SPECS["G-A031"], self.registry))
        self.assertEqual(self.standalone(keep), gate.EXIT["REMEASURE_BASELINE"])

    def test_catastrophe_is_a_fail_and_a_crash_is_undecided(self):
        keep = self.harvest("stationary", "a017")
        status = (keep / "RUNNER_STATUS.txt").read_text(encoding="utf-8")
        (keep / "RUNNER_STATUS.txt").write_text(status.replace("TARGET_STAGE_COMPLETE", "CATASTROPHE_STATIONARY"),
                                                encoding="utf-8")
        self.assertEqual(gate.gate(keep, self.stored, SPECS["G-A031"], self.registry)["verdict"], "FAIL")
        (keep / "RUNNER_STATUS.txt").write_text(status.replace("RUNNER_RC=0", "RUNNER_RC=5"), encoding="utf-8")
        self.assertEqual(gate.gate(keep, self.stored, SPECS["G-A031"], self.registry)["verdict"], "UNDECIDED")
        self.assertEqual(self.standalone(Path(self.tmp.name) / "absent"), gate.EXIT["UNDECIDED"])


class ArchiveTest(unittest.TestCase):
    def test_archive_on_disk_matches_payload(self):
        output = pair.output_path()
        if not output.is_file():
            self.skipTest("run tools/build_go2_basic_motion_pair.py first")
        with zipfile.ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.namelist()), len(PAYLOAD))
            for name, data in PAYLOAD.items():
                self.assertEqual(archive.read(f"{pair.PREFIX.as_posix()}/{name}"), data, name)
            self.assertTrue((archive.getinfo(f"{pair.PREFIX.as_posix()}/{pair.RUNNER}").external_attr >> 16) & 0o111)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        self.assertIn(digest, output.with_suffix(".zip.sha256").read_text(encoding="utf-8"))
        current = GO2 / "upload" / pair.UPLOAD_ID / "current"
        if (current / output.name).is_file():
            self.assertEqual(hashlib.sha256((current / output.name).read_bytes()).hexdigest(), digest)
            self.assertIn(digest, (current / pair.GUIDE).read_text(encoding="utf-8"))
            self.assertEqual([p.name for p in current.glob("*.zip")], [output.name])


if __name__ == "__main__":
    unittest.main()
