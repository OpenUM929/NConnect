"""G-A045 · G-A046 (학습 seed 43 대칭 쌍) 패키지 계약.

로컬 전용 — 시뮬레이터도 학습도 없다.  저장소 루트에서:
    python -m unittest tools.test_go2_g_a045_package_contract

이 관문이 지키는 것 셋.
 1) **새 러너는 게이트만 빠진 campaign 러너다.**  공유 헬퍼는 바이트가 같아야 하고, 남은 차이는
    아래 `DIVERGENCE` 가 이름 붙인 계약의 것이어야 한다.  이름 없는 차이 — 한쪽에만 들어간 편집 —
    는 여기서 떨어진다(결함 C-23 에서 배운 모양: 비교를 지우지 않고 좁힌다).
 2) **자를 바꾸지 않았다.**  판정 문턱·평가 조건·screening 판은 G-A044 의 것과 글자까지 같아야
    한다.  이 회차의 질문이 "같은 자로 다시 재면 무엇이 나오는가" 이기 때문이다.
 3) **승급할 수 없다.**  두 팔 다 `change_class: training_seed` 이고 사양·README·안내문이
    승급 금지를 글자로 적어야 한다.  열린 결정 U2-SEED-REPLICATE-20260918 이 열어 준 것은
    측정이지 승급이 아니다.
"""

from __future__ import annotations

import difflib
import hashlib
import io
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

import build_go2_campaign_package as campaign  # noqa: E402
import build_go2_candidate_package as cand  # noqa: E402
import build_go2_seed_pair_package as pair  # noqa: E402
from go2_tuning_config import REWARD_NAMES  # noqa: E402
from tools.test_h1_report_recovery import BASH, shell_path  # noqa: E402

PAIR_ID = "G-A045_A046"
PAIR = pair.PAIRS[PAIR_ID]
SPECS = [pair.load(work) for work in PAIR["arms"]]
RULER, REPLICATION = SPECS
PAYLOAD = pair.build_payload(PAIR_ID)
RUNNER = (GO2 / pair.RUNNER).read_text(encoding="utf-8")
CAMPAIGN_RUNNER = (GO2 / campaign.RUNNER).read_text(encoding="utf-8")
ARM_RUNNER = cand.runner_bytes(RULER).decode("utf-8")
A044 = json.loads((pair.EXPERIMENTS / "G_A044_a033_lin_vel_z_m175.json").read_text(encoding="utf-8"))
DECISION = pair.DECISION


def function(text: str, name: str) -> str:
    head = text.index(f"{name}() ")
    return text[head: text.index("\n}\n", head) + 3]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def arm_archive(spec: dict) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(PAYLOAD[f"arms/{spec['output']['upload_zip']}"]))


def arm_file(spec: dict, name: str) -> bytes:
    prefix = pair.prefix(spec).as_posix()
    with arm_archive(spec) as archive:
        return archive.read(f"{prefix}/{name}")


class PairRunnerTest(unittest.TestCase):
    """새 러너가 gated campaign 러너와 어디서 갈라지는지, 이름 붙인 만큼만."""

    DIVERGENCE = {
        "게이트가 없다": (
            "GATE", "STORED", "gate_verdict", "run_gate", "go2_target_gate", "TARGET_PASS",
            "target_phase", "target_complete", "baseline_remeasured", "REMEASURE_BASELINE",
            "VERDICT", "GATE_ROLE", "PY=(", "PY=()", "${#PY[@]}", "no python interpreter",
            "PHASE 1/3", "PHASE 2/3", "PHASE 3/3", "elif [[ -x", "elif command -v python",
            "  PY=(python)", "fi", "/gate"),
        "팔마다 전수 단계로 직행한다": (
            "arm_phase", "full_phase", "already collected the full 69", "PHASE 1/2", "PHASE 2/2",
            "full 69-case collection", "COLLECTION", "collection=", "FULL_RUNNER_FAILED",
            "the next arm goes on", "resume=1", "run_stage"),
        "C-14 재진입은 이름이 아니라 경로로": (
            "SELF=", '"$SELF"', "server_run_go2_campaign.sh", "cannot find myself"),
        "소요 시간 안내": ("ESTIMATE", "REMEASURE_BASELINE retry", "~95m per arm", "G-A044"),
        "머리말": ("#", ),
    }

    def test_1_runner_is_lf_and_parses(self) -> None:
        self.assertNotIn("\r", RUNNER)
        done = subprocess.run([BASH, "-n", shell_path(GO2 / pair.RUNNER)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_2_shared_helpers_are_the_campaign_runners_own_bytes(self) -> None:
        """공유 헬퍼는 한 글자도 다르지 않아야 한다 — 다르면 둘 중 하나만 고쳐진 것이다."""
        for name in ("arm_var", "arm_keep", "arm_result", "status_of", "full_complete",
                     "preflight_arm", "previous_results", "sha_or_none", "package_campaign",
                     "on_exit", "run_stage"):
            with self.subTest(helper=name):
                ours, theirs = function(RUNNER, name), function(CAMPAIGN_RUNNER, name)
                self.assertEqual(ours, theirs, f"{name} drifted from the campaign runner")

    def test_3_the_only_differences_are_named_contracts(self) -> None:
        left, right = CAMPAIGN_RUNNER.splitlines(), RUNNER.splitlines()
        used = set()
        for group in difflib.SequenceMatcher(None, left, right).get_grouped_opcodes(0):
            lines = [line for tag, i1, i2, j1, j2 in group if tag != "equal"
                     for line in left[i1:i2] + right[j1:j2]]
            if not lines:
                continue
            owners = sorted(name for name, tokens in self.DIVERGENCE.items()
                            if any(token in line for line in lines for token in tokens))
            self.assertTrue(owners, "이 차이를 설명하는 계약이 없다:\n" + "\n".join(lines))
            used.update(owners)
        self.assertEqual(used, set(self.DIVERGENCE), "쓰이지 않는 계약 — 관문이 비어 간다")

    def test_4_no_gate_survives_anywhere_in_the_runner(self) -> None:
        # 머리말은 자매 스크립트를 설명하느라 게이트의 이름을 부른다.  검사는 **코드**에 건다.
        body = RUNNER[RUNNER.index("set -euo pipefail"):]
        for token in ("go2_target_gate", "run_gate", "gate_verdict", "TARGET_PASS",
                      "REMEASURE_BASELINE=1", "stored_baseline", "target_phase"):
            self.assertNotIn(token, body, f"{token} is a gate leftover (see the diff, not this dump)")
        # 공유 헬퍼 `run_stage` 는 기준선 재측정 인자를 그대로 받는다 — 이 판은 **항상 0** 을 준다.
        self.assertIn('run_stage "$root" full "$resume" 0', body)
        self.assertEqual(RUNNER.count('run_stage "$root" full'), 1)
        self.assertNotIn("-p train.py", RUNNER)
        self.assertNotIn("play.py --task", RUNNER)
        self.assertIn('bash "$ARM_RUNNER" --inner', function(RUNNER, "run_stage"))

    def test_5_every_arm_runs_and_no_arm_gates_another(self) -> None:
        main = RUNNER[RUNNER.index('log "[START] campaign'):]
        self.assertIn('for root in "${ARM_ROOT[@]}"; do\n  arm_phase "$root"\ndone', main)
        body = function(RUNNER, "arm_phase")
        self.assertNotIn("STATE[", body.split("arm_phase() {")[1].split("keep=")[0],
                         "arm_phase must not read another arm's state")
        self.assertNotIn('|| return 0\n  if [[ -d "$keep" ]]', body.replace(
            'log "[SKIP] $work already collected the full 69"\n    return 0', ""))
        self.assertIn("package_campaign CAMPAIGN_COMPLETE 0", main)

    def test_6_the_runner_re_enters_itself_by_path(self) -> None:
        """읽지 않고 **실행해서** 본다: 스텁 tmux 가 받은 명령이 가리키는 파일이 이 러너 자신인가."""
        block = re.search(r'^  \[\[ -f "\$SELF".*?^  tmux new-session[^\n]*$', RUNNER, re.M | re.S)
        self.assertIsNotNone(block)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / pair.RUNNER).write_text(RUNNER, encoding="utf-8", newline="\n")
            script = "\n".join([
                "set -euo pipefail",
                'tmux() { printf "%s" "${!#}"; }',
                f"CAMPAIGN_ROOT={shell_path(root)}",
                f'SELF="$CAMPAIGN_ROOT/{pair.RUNNER}"',
                "RESUME=0; ISAACLAB_SH=/opt/isaaclab.sh; CAMPAIGN_TMUX=t",
                'CAMPAIGN_ID=x; CAMPAIGN_RESULT=/r; CAMPAIGN_DONE_MARKER=m; ARM_WORK=(A B)',
                block.group(0), ""])
            done = subprocess.run([BASH, "-c", script], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            entered = re.search(r"cd (\S+) &&.* bash (\S+) --inner", done.stdout)
            self.assertIsNotNone(entered, done.stdout)
            cd_to, relaunch = (entered.group(index).strip("'") for index in (1, 2))
            self.assertEqual(cd_to, shell_path(root))
            self.assertEqual(relaunch, f"{shell_path(root)}/{pair.RUNNER}")
            self.assertTrue((root / Path(relaunch).name).is_file(), f"없는 파일로 재진입한다: {relaunch}")


class SpecTest(unittest.TestCase):
    def test_7_both_arms_train_at_a_seed_the_project_has_never_used(self) -> None:
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                self.assertEqual(spec["training"]["seed"], 43)
                self.assertNotEqual(spec["training"]["seed"], A044["training"]["seed"])
                for key in ("from_scratch", "num_envs", "max_iterations"):
                    self.assertEqual(spec["training"][key], A044["training"][key], key)

    def test_8_the_ruler_arm_changes_no_reward_at_all(self) -> None:
        self.assertEqual(RULER["rewards"]["candidate"], RULER["rewards"]["baseline"])
        self.assertEqual(RULER["single_change"]["name"], "train_seed")
        changed = [name for name in REWARD_NAMES
                   if float(REPLICATION["rewards"]["candidate"][name])
                   != float(RULER["rewards"]["candidate"][name])]
        self.assertEqual(changed, ["lin_vel_z_l2"], "the pair must differ in exactly one dial")
        self.assertEqual(REPLICATION["rewards"]["candidate"]["lin_vel_z_l2"], -1.5,
                         "the replication arm repeats G-A043's value, it does not pick a new one")

    def test_9_no_threshold_moved(self) -> None:
        """자를 재는 회차가 자를 바꾸면 아무것도 읽을 수 없다."""
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                for key in ("min_total_points_delta", "max_flat_scenario_proxy_drop",
                            "max_flat_case_survival_drop", "max_scenario_weighted_loss_70_by_scenario",
                            "target_group_floor", "climb_guard", "target_groups", "rule_version",
                            "target_axes", "guard_axes", "min_target_mean_proxy_delta",
                            "min_target_groups_improved"):
                    self.assertEqual(spec["preregistered"][key], A044["preregistered"][key], key)
                self.assertEqual(spec["preregistered"]["plan_screening"]["version"],
                                 A044["preregistered"]["plan_screening"]["version"])
                for key in ("seeds", "case_count", "num_envs", "steps", "checkpoint_iter",
                            "catastrophe_case", "sentinel_cases", "sentinel_tolerance"):
                    self.assertEqual(spec["evaluation"][key], A044["evaluation"][key], key)

    def test_10_neither_arm_can_be_promoted(self) -> None:
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                self.assertEqual(spec["change_class"], "training_seed")
                self.assertEqual(spec["promotion"], "forbidden_not_a_reward_change")
                self.assertTrue(spec["promotion_reason"].strip())
                self.assertIn(DECISION, spec["open_decisions"])
                self.assertEqual(spec["inference"]["status"], "INFORMATION_RUN")

    def test_11_the_films_are_a_matched_pair(self) -> None:
        self.assertEqual(RULER["videos"]["candidate"], REPLICATION["videos"]["candidate"])
        self.assertEqual(REPLICATION["videos"]["baseline"], [],
                         "filming the same stored policy twice in one campaign buys nothing")
        self.assertEqual(REPLICATION["videos"]["counterpart_arm"], RULER["work_id"])
        stored = (ROOT / RULER["baseline"]["stored_arm"] / "evaluation"
                  / RULER["baseline"]["stored_label"] / "videos")
        for entry in RULER["videos"]["candidate"]:
            scenario, case_id, seed = entry.split(":")
            with self.subTest(video=entry):
                self.assertTrue((stored / f"{scenario}_{case_id}_seed_{seed}.mp4").is_file()
                                or entry in RULER["videos"]["baseline"]
                                or entry in RULER["videos"]["baseline_reuse"],
                                "a candidate film with no baseline counterpart anywhere")

    def test_12_reused_baseline_videos_recompute_from_this_specs_baseline(self) -> None:
        """재사용은 이름이 아니라 지문으로 한다 (결함 C-13 이후)."""
        import build_go2_training_length_package as length
        self.assertEqual(length.reuse_problems(RULER), [])
        for entry, row in RULER["videos"]["baseline_reuse"].items():
            with self.subTest(video=entry):
                self.assertEqual(row["identity_sha256"], length.video_fingerprint(RULER, entry))
                self.assertEqual(sha((ROOT / row["path"]).read_bytes()), row["sha256"])


class PackageTest(unittest.TestCase):
    def test_13_the_pair_zip_holds_exactly_what_it_should(self) -> None:
        expected = {pair.RUNNER, "campaign_config.env", "README.txt", "CAMPAIGN_SHA256SUMS.txt"}
        expected |= {f"arms/{spec['output']['upload_zip']}" for spec in SPECS}
        self.assertEqual(set(PAYLOAD), expected)
        manifest = PAYLOAD["CAMPAIGN_SHA256SUMS.txt"].decode("utf-8").splitlines()
        listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in manifest}
        self.assertEqual(set(listed), expected - {"CAMPAIGN_SHA256SUMS.txt"})
        for name, digest in listed.items():
            self.assertEqual(sha(PAYLOAD[name]), digest, name)

    def test_14_campaign_config_names_the_arms_and_their_bytes(self) -> None:
        config = PAYLOAD["campaign_config.env"].decode("utf-8")
        self.assertIn(f"ARM_RUNNER={cand.PINNED_RUNNER}\n", config)
        self.assertIn("ARM_WORK=(G-A045 G-A046)\n", config)
        for spec in SPECS:
            name = spec["output"]["upload_zip"]
            self.assertIn(name, config)
            self.assertIn(sha(PAYLOAD[f"arms/{name}"]), config)
            self.assertIn(spec["output"]["package_root"], config)
        self.assertIn(f"CAMPAIGN_KEEP_NAME={PAIR['keep_name']}\n", config)
        for spec in SPECS:
            self.assertNotEqual(PAIR["keep_name"], spec["output"]["keep_dir_name"])
            self.assertNotEqual(PAIR["tmux"], spec["output"]["tmux_name"])
            self.assertNotEqual(PAIR["result_zip"], spec["output"]["result_zip"])

    def test_15_each_arm_ships_the_seed_and_the_full_stage(self) -> None:
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                config = arm_file(spec, "run_config.env").decode("utf-8")
                self.assertIn("TRAIN_SEED=43\n", config)
                self.assertIn("GO2_STAGE=full\n", config)
                self.assertIn("COLLECT_REQUIRED_ON_STATIONARY=1\n", config)
                self.assertIn("EVAL_CHECKPOINT_ITER=900\n", config)
                self.assertIn(f"WORK_ID={spec['work_id']}\n", config)

    def test_16_the_reward_files_say_what_the_arms_are(self) -> None:
        """자 팔은 기준선과 **바이트가 같고**, 재현 팔은 한 줄만 다르다 — ZIP 안에서 확인한다."""
        for spec, expected in ((RULER, 0), (REPLICATION, 1)):
            with self.subTest(arm=spec["work_id"]):
                candidate = arm_file(spec, "candidate/quadruped_rewards.py").decode("utf-8")
                reference = arm_file(spec, "reference/baseline_quadruped_rewards.py").decode("utf-8")
                differing = [(a, b) for a, b in zip(reference.splitlines(), candidate.splitlines())
                             if a != b]
                self.assertEqual(len(differing), expected)
                if expected:
                    self.assertIn('"lin_vel_z_l2"', differing[0][1])
                    self.assertIn("-1.5", differing[0][1])
                self.assertEqual(arm_file(spec, "baseline/quadruped_rewards.py"),
                                 reference.encode("utf-8"))

    def test_17_arm_zips_carry_the_pinned_runner_and_their_own_spec(self) -> None:
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                self.assertEqual(arm_file(spec, cand.PINNED_RUNNER), ARM_RUNNER.encode("utf-8"))
                shipped = json.loads(arm_file(spec, "experiment.json"))
                self.assertEqual(shipped["work_id"], spec["work_id"])
                self.assertEqual(shipped["promotion"], "forbidden_not_a_reward_change")
                manifest = arm_file(spec, "PACKAGE_SHA256SUMS.txt").decode("utf-8").splitlines()
                prefix = pair.prefix(spec).as_posix()
                with arm_archive(spec) as archive:
                    members = {name[len(prefix) + 1:] for name in archive.namelist()}
                listed = {line.split("  ", 1)[1] for line in manifest}
                self.assertEqual(listed, members - {"PACKAGE_SHA256SUMS.txt"})

    def test_18_the_build_is_deterministic(self) -> None:
        self.assertEqual(pair.build_payload(PAIR_ID), PAYLOAD,
                         "two builds of the same bytes must agree, or the release is not reproducible")


class GuideTest(unittest.TestCase):
    """안내문이 실패 경로와 승급 금지를 **사실대로** 적는가 (결함 C-24 에서 배운 모양)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = pair.run_guide(PAIR_ID, "0" * 64)
        cls.readme = PAYLOAD["README.txt"].decode("utf-8")

    def test_19_the_crash_path_prints_no_marker_and_the_guide_says_so(self) -> None:
        """발행된 팔 러너의 crash 경로를 **실행해서** 표식이 없음을 보이고 안내문과 대조한다."""
        # 표식은 run_config.env 에서 온다.  러너가 그것을 찍는 자리는 finish 뿐이어야 한다.
        self.assertIn('echo "$DONE_MARKER"', ARM_RUNNER, "the arm runner prints the marker somewhere")
        self.assertEqual(ARM_RUNNER.count('echo "$DONE_MARKER"'), 1,
                         "the marker must have exactly one printing site")
        on_exit = ARM_RUNNER[ARM_RUNNER.index("on_exit() {"):ARM_RUNNER.index("trap on_exit EXIT")]
        self.assertNotIn("DONE_MARKER", on_exit,
                         "the crash path must not print the finish marker — the guide says it does not")
        for phrase in ("늘 나오는 것도 아니다", "FULL_69_COMPLETE", "INCOMPLETE_COLLECTION",
                       "INCOMPLETE_CRASH", "INCOMPLETE_EARLY_STOP", "69 를 채우지 않는다",
                       "개수 확인"):
            self.assertIn(phrase, self.guide, phrase)

    def test_20_the_guide_and_readme_forbid_promotion_in_words(self) -> None:
        for text, label in ((self.guide, "guide"), (self.readme, "README")):
            with self.subTest(document=label):
                self.assertIn("forbidden_not_a_reward_change", text)
                self.assertIn(DECISION, text)
        self.assertIn("승급 대상이 아니다", self.guide)
        self.assertIn("사용자 결정", self.guide)

    def test_21_the_guide_reads_both_arms(self) -> None:
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                self.assertIn(spec["work_id"], self.guide)
                self.assertIn(spec["output"]["keep_dir_name"], self.guide)
        self.assertIn(PAIR["result_zip"], self.guide)
        self.assertIn(PAIR["done_marker"], self.guide)
        self.assertIn("240~300분", self.guide, "the session budget must be the plan's, not the run time")

    def test_22_the_guide_commands_actually_run(self) -> None:
        """안내문이 시키는 판독 명령을 **실행한다**.

        파일이 있는지만 보면 결함 C-15 를 다시 만든다 — 그때 안내문의 `--keep` 은 실존하지 않는
        선택지였고 명령은 argparse 에서 죽었다.  실제로 이 회차에서도 한 번 그럴 뻔했다:
        `verify_go2_basic_motion_harvest.py` 의 `SPECS` 에 이 쌍의 빌더가 없어 `G-A045` 는
        선택지 밖이었다.  여기서는 없는 수확물을 주고 돌려, 인자 오류(exit 2)가 아니라
        **판정 불가**까지 가는지 본다.  성능이 아니라 배선을 보는 검사다.
        """
        commands, buffer = [], ""
        for line in self.guide.splitlines():
            stripped = line.strip()
            if not buffer and not stripped.startswith("python -B tools/"):
                continue
            continued = stripped.endswith("\\")
            buffer += (stripped[:-1].strip() + " ") if continued else stripped
            if not continued:
                commands.append(buffer)
                buffer = ""
        self.assertEqual(len(commands), 2 * len(SPECS), commands)
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "no_harvest"
            for command in commands:
                with self.subTest(command=command[:70]):
                    argv = command.split()
                    self.assertTrue((ROOT / argv[2]).is_file(), argv[2])
                    swapped = [str(missing) if arg.startswith("workspace/_keep/") else arg
                               for arg in argv[1:]]
                    done = subprocess.run([sys.executable, *swapped], capture_output=True,
                                          text=True, cwd=ROOT, timeout=300,
                                          env=dict(os.environ, PYTHONIOENCODING="utf-8"))
                    self.assertNotEqual(done.returncode, 2,
                                        "명령이 인자에서 죽는다:\n" + done.stderr[-400:])
                    self.assertRegex(done.stdout, r"(VERDICT|SCREENING)\s+[A-Z_]+",
                                     done.stdout[-300:] + done.stderr[-300:])
        self.assertIn("--rule-version post_a043_push4_v1", self.guide)
        for spec in SPECS:
            self.assertIn(f"verify_go2_basic_motion_harvest.py {spec['work_id']}", self.guide)


class InnerRunTest(unittest.TestCase):
    """러너를 **실행한다** — 스텁 팔로 `--inner` 경로를 끝까지 돌려 배선을 본다.

    읽어서 통과시키는 검사는 "팔이 둘 다 돈다" 를 증명하지 못한다.  여기서는 가짜 팔 둘과 가짜
    isaaclab.sh 로 러너를 실제로 돌리고, 두 팔이 모두 실행됐는지 · 상태 파일이 팔마다 쓰였는지 ·
    끝 표식이 나왔는지를 stdout 과 디스크에서 확인한다.  서버 경로 `/workspace` 는 로컬에서 쓸 수
    없으므로 **그 한 줄만** 임시 폴더로 바꾼다(다른 바이트는 발행본 그대로다).
    """

    ARM_STUB = 'set -euo pipefail\nsource "$PACKAGE_ROOT/run_config.env"\nkeep="$WS/_keep/$KEEP_DIR_NAME"\nmkdir -p "$keep"\nif [[ "${FAIL_WORK:-}" == "$WORK_ID" ]]; then\n  printf \'RUNNER_RC=1\\nSTAGE=full\\nDECISION=CATASTROPHE_STATIONARY\\nCOLLECTION_STATUS=INCOMPLETE_EARLY_STOP\\n\' >"$keep/RUNNER_STATUS.txt"\n  exit 5\nfi\nprintf \'RUNNER_RC=0\\nSTAGE=%s\\nDECISION=SUITE_COMPLETE\\nCOLLECTION_STATUS=FULL_69_COMPLETE\\n\' "$GO2_STAGE" >"$keep/RUNNER_STATUS.txt"\necho result >"$WS/_keep/$RESULT_ZIP_NAME"\n( cd "$WS/_keep" && sha256sum "$RESULT_ZIP_NAME" >"$RESULT_ZIP_NAME.sha256" )\n'
    ISAAC_STUB = 'set -euo pipefail\nshift 2\necho packaged >"$2"\n'

    def build_tree(self, tmp: Path) -> dict:
        workspace = tmp / "workspace"
        (workspace / "_keep").mkdir(parents=True)
        root = tmp / "campaign"
        root.mkdir()
        arms = []
        for spec in SPECS:
            arm = workspace / pair.prefix(spec).as_posix()
            arm.mkdir(parents=True)
            (arm / "run_config.env").write_text(
                "".join(f"{key}={value}\n" for key, value in (
                    ("WORK_ID", spec["work_id"]),
                    ("KEEP_DIR_NAME", spec["output"]["keep_dir_name"]),
                    ("RESULT_ZIP_NAME", spec["output"]["result_zip"]),
                    ("TMUX_NAME", spec["output"]["tmux_name"]))),
                encoding="utf-8", newline="\n")
            # 스텁도 러너가 아는 이름이어야 한다 — `ARM_RUNNER` 는 두 이름만 받는다(공유 계약).
            (arm / cand.PINNED_RUNNER).write_text(self.ARM_STUB, encoding="utf-8", newline="\n")
            arms.append(arm)
        isaac = workspace / "isaaclab.sh"
        isaac.write_text(self.ISAAC_STUB, encoding="utf-8", newline="\n")
        isaac.chmod(0o755)
        text = RUNNER.replace("WORKSPACE=/workspace", f"WORKSPACE={shell_path(workspace)}")
        self.assertIn(f"WORKSPACE={shell_path(workspace)}", text, "the only surgery is the root path")
        (root / pair.RUNNER).write_text(text, encoding="utf-8", newline="\n")
        config = PAYLOAD["campaign_config.env"].decode("utf-8")
        config = re.sub(r"^ARM_ROOT=.*$", "ARM_ROOT=(" + " ".join(
            shell_path(arm) for arm in arms) + ")", config, flags=re.M)
        (root / "campaign_config.env").write_text(config, encoding="utf-8", newline="\n")
        # 러너는 비어 있지 않은 manifest 를 요구하고 그것을 `sha256sum -c` 로 검사한다.
        manifest = "".join(f"{sha((root / name).read_bytes())}  {name}\n"
                           for name in (pair.RUNNER, "campaign_config.env"))
        (root / "CAMPAIGN_SHA256SUMS.txt").write_text(manifest, encoding="utf-8", newline="\n")
        return {"root": root, "workspace": workspace}

    def run_inner(self, tree: dict, fail_work: str = "") -> subprocess.CompletedProcess:
        env = dict(os.environ, FAIL_WORK=fail_work, WS=shell_path(tree["workspace"]),
                   CAMPAIGN_ROOT=shell_path(tree["root"]),
                   ISAACLAB_SH=shell_path(tree["workspace"] / "isaaclab.sh"))
        return subprocess.run([BASH, shell_path(tree["root"] / pair.RUNNER), "--inner"],
                              capture_output=True, text=True, env=env, timeout=120)

    def test_23_both_arms_run_and_the_result_is_packaged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build_tree(Path(tmp))
            done = self.run_inner(tree)
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            self.assertIn(PAIR["done_marker"], done.stdout)
            keep = tree["workspace"] / "_keep" / PAIR["keep_name"]
            status = (keep / "CAMPAIGN_STATUS.txt").read_text(encoding="utf-8")
            for spec in SPECS:
                key = spec["work_id"].replace("-", "_")
                self.assertIn(f"{key}_STATE=FULL_DONE", status)
                self.assertIn(f"{key}_COLLECTION=FULL_69_COMPLETE", status)
                self.assertTrue((keep / "arm_results" / spec["output"]["result_zip"]).is_file(),
                                spec["work_id"])
            self.assertIn("RESULT_STATE=CAMPAIGN_COMPLETE", status)
            self.assertIn("GATE_ROLE=none", status)
            self.assertIn("OFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED", status)
            self.assertTrue((tree["workspace"] / "_keep" / PAIR["result_zip"]).is_file())

    def test_24_a_failed_arm_does_not_stop_the_other(self) -> None:
        """자 팔이 죽어도 재현 팔은 돈다 — 고를 승자가 없으므로 팔이 팔을 막지 않는다."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build_tree(Path(tmp))
            done = self.run_inner(tree, fail_work=RULER["work_id"])
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            self.assertIn(PAIR["done_marker"], done.stdout)
            status = (tree["workspace"] / "_keep" / PAIR["keep_name"]
                      / "CAMPAIGN_STATUS.txt").read_text(encoding="utf-8")
            ruler, other = (work["work_id"].replace("-", "_") for work in (RULER, REPLICATION))
            self.assertIn(f"{ruler}_STATE=FULL_RUNNER_FAILED", status)
            self.assertIn(f"{ruler}_COLLECTION=INCOMPLETE_EARLY_STOP", status)
            self.assertIn(f"{other}_STATE=FULL_DONE", status)


class ReviewCorrectionsTest(unittest.TestCase):
    """2026-09-24 독립 검토가 잡은 사전등록 **해석**의 오류 넷(결함 C-26)을 고정한다.

    값·문턱이 아니라 *읽는 법*을 지키는 관문이다.  초판은 ① 계단 재현을 B 의 절대값만으로 판정하고
    ② 작은 seed 차이를 "다이얼 탓" 의 근거로 쓰고 ③ 큰 차이에서 승급 규칙 폐기·장기 학습을 적고
    ④ R-6 을 닫힌 것처럼 적었다.  넷 다 산문이라 관문이 없으면 다음 판에서 조용히 되살아난다.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = (ROOT / PAIR["plan"]).read_text(encoding="utf-8")
        cls.criteria = (GO2 / "reports" / "GO2_A045_CRITERIA_CHANGES_20260924.md").read_text(
            encoding="utf-8")
        cls.guide = pair.run_guide(PAIR_ID, "0" * 64)
        cls.readme = PAYLOAD["README.txt"].decode("utf-8")

    def test_25_the_threshold_is_quoted_as_one_number_everywhere(self) -> None:
        """사전등록 경계값은 한 숫자다 — 초판은 계획서에 2.5, 기준 문서에 2.53 을 적었다."""
        threshold = A044["preregistered"]["min_total_points_delta"]
        self.assertEqual(threshold, 2.53)
        for spec in SPECS:
            self.assertEqual(spec["preregistered"]["min_total_points_delta"], threshold)
        for text, label in ((self.plan, "plan"), (self.criteria, "criteria")):
            with self.subTest(document=label):
                self.assertIn("2.53", text)
                self.assertNotRegex(text, r"문턱은 총점 `?\+?2\.5`?/70",
                                    "2.5 로 적으면 다른 정본과 어긋난다")

    def test_26_reproduction_is_read_as_a_paired_difference(self) -> None:
        """절대값만으로 "재현" 을 말하지 않는다 — 같은 seed 의 B - A 가 함께 있어야 한다."""
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                falsified = spec["inference"]["falsified_if"]
                self.assertIn("(B - A)", falsified)
                self.assertIn("SAME seed", falsified)
                self.assertIn("BEHAVIOUR LEVEL", falsified)
                self.assertIn("REWARD EFFECT", falsified)
        self.assertIn("B − A", self.plan)
        self.assertIn("절대 수준과 쌍 차이를 따로", self.plan)
        for text, label in ((self.guide, "guide"), (self.readme, "README")):
            with self.subTest(document=label):
                self.assertIn("B - A" if label == "README" else "B−A", text)

    def test_27_a_small_seed_difference_does_not_name_a_cause(self) -> None:
        """`-1.75` 를 반복하지 않으므로 A044 의 비단조 원인은 이 회차로 확정되지 않는다."""
        self.assertNotIn("다이얼 탓이다", self.plan)
        self.assertIn("미확정", self.plan)
        self.assertIn("`−1.75` 를 반복하지 않는다", self.plan)
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                self.assertIn("not -1.75", spec["inference"]["seed_limit"])
                self.assertIn("not exclusive", spec["inference"]["seed_limit"])
        self.assertIn("확정되지 않는다", self.guide)

    def test_28_a_large_difference_does_not_retire_the_rule(self) -> None:
        """한 표본은 승급 규칙 폐기나 자동 장기 학습의 근거가 아니다."""
        self.assertIn("폐기하지 않는다", self.plan)
        self.assertIn("자동 장기 학습은 하지 않는다", self.plan)
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                falsified = spec["inference"]["falsified_if"]
                self.assertIn("does NOT retire the promotion rule", falsified)
                self.assertIn("does NOT invalidate", falsified)
                self.assertIn("automatic long training", falsified)

    def test_29_r6_is_written_as_an_open_reading_both_ways(self) -> None:
        """파일 무수정은 허용의 증거가 아니고, 공식 제출 불가도 우리가 단정하지 않는다."""
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                reason = spec["promotion_reason"]
                self.assertIn("What is NOT established", reason)
                self.assertIn("permitted by the rules", reason)
                self.assertIn("not a finding that the rules forbid", reason)
                self.assertIn("INTERNAL", reason)
                self.assertIn("organiser", reason)
                self.assertIn(DECISION, reason)
        self.assertIn("규정상 허용된다는 증거가 아니다", self.plan)
        self.assertIn("운영진", self.plan)
        self.assertIn("운영진", self.guide)
        self.assertIn("우리 내부의 보수 규칙", self.guide)

    def test_33_the_downside_is_not_bounded_by_us(self) -> None:
        """「최악이라도 GPU 시간만 잃는다」로 손실 상한을 긋지 않는다 (검토 5차).

        A033 산출물이 보존된다는 사실과 팀 제출 자격에 영향이 없다는 판단은 **별개**다. 서버 실행
        자체가 허용되지 않는 행위로 판정될 경우 제재 범위는 미확정이고, 실행 결정만으로 열린 해석이
        닫히지도 않는다.
        """
        flat = " ".join(self.plan.split())
        self.assertIn("제재 범위는 미확정", flat)
        self.assertIn("손실 상한", flat)
        self.assertIn("사용자의 실행 결정만으로 U2 가 해결되지는 않는다", flat)
        self.assertNotIn("GPU 시간만 잃는다고 보면 된다", flat)
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                reason = spec["promotion_reason"]
                self.assertIn("Nor do we bound the downside", reason)
                self.assertIn("scope of any sanction is undetermined", reason)
        guide = " ".join(self.guide.split())
        self.assertIn("제재 범위는 **미확정**", guide)
        readme = " ".join(self.readme.split())
        self.assertIn("scope of any sanction is undetermined", readme)

    def test_34_a043_rejection_is_not_narrowed_to_one_axis(self) -> None:
        """A043 은 G2 하나로 막힌 것이 아니다 — 총점 미달과 다른 위반도 함께 적는다 (검토 5차)."""
        flat = " ".join(self.plan.split())
        for fragment in ("+2.09593", "+2.53", "rough_forward", "push_pos_x", "−0.44161"):
            self.assertIn(fragment, flat, fragment)
        self.assertIn("유망한 계단 신호와 후보 채택 자격은 분리해서 읽는다", flat)
        blob = json.dumps(REPLICATION, ensure_ascii=False)
        self.assertNotIn("failed its screening on G2", blob,
                         "한 축으로 좁힌 문장이 사양에 남아 있다")
        self.assertIn("did not fail on G2 alone", blob)
        criteria = " ".join((GO2 / "reports" / "GO2_A045_CRITERIA_CHANGES_20260924.md")
                            .read_text(encoding="utf-8").split())
        self.assertIn("A043 기각 사유를 한 축으로 좁히지 않는다", criteria)

    def test_30_the_stairs_cases_are_called_climbs(self) -> None:
        """`stairs_*_down` 은 오르기다 — 이름대로 "하강" 이라고 적지 않는다."""
        self.assertIn("오르기", self.plan)
        self.assertNotIn("하강 ≥", self.plan)
        source = (GO2 / "reports" / "evidence" / "go2_stairs_behavior_20260916"
                  / "STAIRS_CLIMB.csv").read_text(encoding="utf-8")
        rows = [line.split(",") for line in source.splitlines()[1:] if line]
        header = source.splitlines()[0].split(",")
        case_at, direction_at = header.index("case"), header.index("direction")
        directions = {row[case_at]: row[direction_at] for row in rows}
        self.assertEqual(directions["stairs_10_down"], "climb")
        self.assertEqual(directions["stairs_15_down"], "climb")

    def test_31_the_score_split_is_measured_not_asserted(self) -> None:
        """총점이 어디로 갔는지는 산문이 아니라 같은 채점기의 반사실이어야 한다."""
        path = GO2 / "reports" / "evidence" / "go2_seed_pair_20260924" / "SCORE_SPLIT.csv"
        self.assertTrue(path.is_file(), "SCORE_SPLIT.csv 가 없다 — tools/go2_score_decomposition.py")
        text = path.read_text(encoding="utf-8")
        for column in ("delta_from_survival_70", "interaction_70", "interaction_share_pct"):
            self.assertIn(column, text, column)
        self.assertIn("-4.62775", text)
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                sources = [row["source"] for row in spec["inference"]["rows"]]
                self.assertIn("reports/evidence/go2_seed_pair_20260924/SCORE_SPLIT.csv", sources)
        self.assertIn("반사실", self.plan)

    def test_32_the_split_is_an_attribution_not_a_cause(self) -> None:
        """기여 분해를 인과로 되읽지 않는다 (검토 3차).

        세 항의 합이 총점 차이와 같은 것은 **정의**다 — 교차항을 잔차로 두기 때문이다. 그러니
        "합이 맞으니 설명이 맞다" 로 읽으면 안 되고, 읽을 것은 교차항의 **크기**다(A044 0.04% 대
        A043 79.89%). 그리고 어느 쪽이든 「보상 변경이 낙상을 일으켰다」는 명제는 나오지 않는다.
        """
        for spec in SPECS:
            with self.subTest(arm=spec["work_id"]):
                singular = spec["inference"]["singularity"]
                self.assertIn("ARITHMETIC ATTRIBUTION", singular)
                self.assertIn("NOT that the weight change caused the falls", singular)
                self.assertIn("residual by construction", singular)
                self.assertIn("79.89", singular, "교차항이 큰 반례도 함께 적는다")
                # 2026-09-24 검토 4차: 순변화 대비 비율은 불안정하다 — 분모를 갈라 적어야 한다.
                self.assertIn("two denominators", singular)
                self.assertIn("30.75", singular, "크기합 분모의 값도 함께 적는다")
                self.assertIn("neither a causal contribution nor an explanation-failure rate",
                              singular)
                row = next(r for r in spec["inference"]["rows"]
                           if r["source"].endswith("SCORE_SPLIT.csv"))
                self.assertIn("not a cause", row["reads"])
        # 문서는 줄바꿈이 들어가므로 공백을 눌러서 본다.
        flat = " ".join(self.plan.split())
        self.assertIn("기여 분해이지 인과가 아니다", flat)
        self.assertIn("합이 맞는 것은 검증이 아니라 정의다", flat)
        self.assertIn("79.89%", flat)
        self.assertIn("30.75%", flat, "크기합 분모의 값도 함께 적는다")
        self.assertIn("인과적 기여율도 설명 실패율도 아니다", flat)
        self.assertNotIn("정확히 더해지지 않는다", flat,
                         "교차항을 잔차로 두면 세 항은 언제나 더해진다")
        tool = " ".join((ROOT / "tools" / "go2_score_decomposition.py")
                        .read_text(encoding="utf-8").split())
        self.assertIn("인과 증명이 아니다", tool)
        self.assertIn("합이 맞는 것은 검증이 아니라 정의다", tool)
        self.assertIn("인과적 기여율도, 설명 실패율도 아니다", tool)
        split = (GO2 / "reports" / "evidence" / "go2_seed_pair_20260924"
                 / "SCORE_SPLIT.csv").read_text(encoding="utf-8")
        for column in ("interaction_share_of_magnitude_pct", "net_change_share_of_magnitude_pct"):
            self.assertIn(column, split, column)


class RecoveryPathTest(unittest.TestCase):
    """중단·재개 경로 — 정상 경로 검사가 한 번도 건드리지 않던 두 자리 (결함 C-27·C-28).

    독립 검토가 발행된 v7 바이트에서 찾은 것 둘.  ① `GO2_RESUME=1` 로 들어왔는데 보존 학습이
    완료 상태가 아니면 러너가 말없이 `logs`·`exported`·고정 checkpoint·학습 로그를 지우고 처음부터
    다시 학습했다 — 「이어 하기」가 증거와 GPU 시간을 함께 태웠다.  ② 캠페인의 완료 판단이
    `RUNNER_RC`·`STAGE`·`DECISION` 만 보아서 `COLLECTION_STATUS=INCOMPLETE_COLLECTION` 인 팔도,
    결과 ZIP 이 아예 없는 팔도 「완료」로 건너뛰었다.

    둘 다 **읽어서** 알아낼 수 없던 것이 아니라 **읽기만 해서** 놓친 것이므로, 여기서는 러너에서
    바이트를 떼어 실제로 실행한다.  기댓값은 상태 이름이 아니라 디스크에 남은 것으로 확인한다.
    """

    @staticmethod
    def block(text: str, start: str, end: str) -> str:
        i = text.index(start)
        return text[i:text.index(end, i) + len(end)]

    def bash(self, script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
        path = cwd / "case.sh"
        path.write_text(script, encoding="utf-8", newline="\n")
        return subprocess.run([BASH, shell_path(path), *args], capture_output=True,
                              text=True, timeout=120)

    def test_35_a_resume_preserves_an_interrupted_training_instead_of_retraining(self) -> None:
        helpers = self.block(ARM_RUNNER, "restart_would_destroy() {",
                             "# END INTERRUPTED TRAINING GUARD")
        guard = self.block(ARM_RUNNER, '  if [[ "$RESUME" == 1 && "${GO2_RESTART_TRAINING:-0}" != 1 ]]',
                           "  rm -rf -- logs exported")
        guard = guard.replace("  rm -rf -- logs exported", "  echo DESTROYED_AND_RETRAINED")
        harness = ('set -u\nKEEP=$1; CANDIDATE_ROOT=$2; RESUME=$3; GO2_RESTART_TRAINING=${4:-0}\n'
                   'PIN_MODEL="$KEEP/training/model_iter900.pt"\n'
                   'PIN_RECORD="$KEEP/training/CHECKPOINT_PIN.txt"\n' + helpers + "\n" + guard + "\n")
        cases = (
            ("중단된 학습 + 재개", "1", "0", True, False),
            ("중단된 학습 + 명시 재시작", "1", "1", True, True),
            ("보존할 것이 없는 재개", "1", "0", False, True),
            ("신규 실행", "0", "0", True, True),
        )
        for label, resume, restart, evidence, retrains in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                case = Path(tmp)
                keep, root = case / "_keep", case / "cand"
                for part in ((keep / "training"), (keep / "logs"),
                             (root / "logs" / "run"), (root / "exported")):
                    part.mkdir(parents=True)
                if evidence:
                    (keep / "logs" / "candidate_training.log").write_text(
                        "iteration 812\n", encoding="utf-8")
                    (keep / "training" / "model_iter900.pt").write_bytes(b"pinned")
                    (root / "logs" / "run" / "model_800.pt").write_bytes(b"ckpt800")
                    (root / "exported" / "env.yaml").write_text("seed: 43\n", encoding="utf-8")
                done = self.bash(harness, shell_path(keep), shell_path(root), resume, restart,
                                 cwd=case)
                if retrains:
                    self.assertIn("DESTROYED_AND_RETRAINED", done.stdout, done.stderr)
                    continue
                self.assertEqual(done.returncode, 9, done.stdout + done.stderr)
                self.assertNotIn("DESTROYED_AND_RETRAINED", done.stdout)
                kept = {path.name for folder in (keep / "training").glob("interrupted_*")
                        for path in folder.iterdir()}
                self.assertLessEqual({"candidate_training.log", "model_iter900.pt", "env.yaml",
                                      "logs", "SHA256SUMS.txt"}, kept, kept)
                state = (keep / "training" / "TRAINING_RESUME_STATUS.txt").read_text(
                    encoding="utf-8")
                self.assertIn("TRAINING_STATE=INTERRUPTED_TRAINING_PRESERVED", state)
                self.assertIn("GO2_RESTART_TRAINING=1", state)

    def test_36_an_arm_is_skipped_only_when_its_collection_and_its_zip_are_both_good(self) -> None:
        end = chr(10) + "}"
        harness = ("set -u\n" + function(RUNNER, "status_of") + "\n"
                   + self.block(RUNNER, "full_complete() {", end) + "\n"
                   + 'if full_complete "$1" "$2"; then echo SKIP; else echo RESUME; fi\n')
        cases = (
            ("INCOMPLETE_COLLECTION", "good", "RESUME"),
            ("INCOMPLETE_EARLY_STOP", "good", "RESUME"),
            ("INCOMPLETE_CRASH", "good", "RESUME"),
            ("FULL_69_COMPLETE", "missing", "RESUME"),
            ("FULL_69_COMPLETE", "corrupt", "RESUME"),
            ("FULL_69_COMPLETE", "good", "SKIP"),
        )
        for collection, zip_state, expect in cases:
            with self.subTest(collection=collection, zip=zip_state), \
                    tempfile.TemporaryDirectory() as tmp:
                case = Path(tmp)
                keep = case / "arm"
                keep.mkdir()
                (keep / "RUNNER_STATUS.txt").write_text(
                    "RUNNER_RC=0\nDECISION=SUITE_COMPLETE\nSTAGE=full\n"
                    f"COLLECTION_STATUS={collection}\n", encoding="utf-8", newline="\n")
                result = case / "arm_result.zip"
                if zip_state != "missing":
                    result.write_bytes(b"PK\x03\x04result")
                    digest = sha(result.read_bytes())
                    result.with_suffix(".zip.sha256").write_text(
                        f"{digest}  {result.name}\n", encoding="utf-8", newline="\n")
                    if zip_state == "corrupt":
                        result.write_bytes(b"PK\x03\x04tampered")
                done = self.bash(harness, shell_path(keep), shell_path(result), cwd=case)
                self.assertEqual(done.stdout.strip(), expect, done.stderr)

    def test_37_the_guide_names_the_preserved_state_and_the_restart_switch(self) -> None:
        """자료를 살리는 동작은 코드에만 있으면 안 된다 — 읽는 사람이 알아야 고를 수 있다."""
        documents = ((pair.run_guide(PAIR_ID, "0" * 64), "guide"),
                     (PAYLOAD["README.txt"].decode("utf-8"), "README"))
        for text, label in documents:
            with self.subTest(document=label):
                flat = " ".join(text.split())
                self.assertIn("INTERRUPTED_TRAINING_PRESERVED", flat)
                self.assertIn("GO2_RESTART_TRAINING=1", flat)
        flat = " ".join(documents[0][0].split())
        self.assertIn("미완료 학습을 절대 덮어쓰지 않는다", flat)
        self.assertIn("건너뛰지 않고 다시 돈다", flat)


if __name__ == "__main__":
    unittest.main()
