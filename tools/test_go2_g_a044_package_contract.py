"""Contract for the G-A044 full-collection release (G-A033 + lin_vel_z_l2 -2.0 -> -1.75).  Local only.

A package is not ready until the code that will read its harvest has run on one (memory rule
"준비 완료 = 판독 코드를 돌려봤다").  So besides what the builder writes, these tests run the local
verifier on a synthetic **69-case** harvest shaped like this runner's output, and run the screening
readers on the real G-A033 and G-A043 harvests.

What is new in this arm, and what these tests pin down:
  - It runs the whole 69-case evaluation in ONE pass: no target stage, no server gate.  The contract
    lives in `run_config.env` (`GO2_STAGE=full`), which the runner reads before it defaults STAGE to
    `target`.  G-A043's decisive loss sat outside its 23-case stage 1 and only showed after the full
    suite ran (defect C-11), and the stage-1 split saves ~16 minutes, not the ~58 of training.
  - The plan screening edition `post_a043_push4_v1` guards all four G6 push directions.  The two
    earlier editions keep judging byte for byte what they judged before.
  - Ten cases are filmed on both arms; six baseline videos are reused by SHA, including the first
    reuse of a push video, which needed the builder's fingerprint to model PUSH_X/PUSH_Y (defect C-13).
  - Every judgement threshold is G-A043's, number for number.  This run widens collection and
    protection, and relaxes nothing.

    python -m unittest tools.test_go2_g_a044_package_contract
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as reward  # noqa: E402
import build_go2_full_collection_release as release  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402
import go2_screening_gate as screening  # noqa: E402
import go2_tuning_base_data as base_data  # noqa: E402
import verify_go2_basic_motion_harvest as verifier  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict  # noqa: E402

WORK_ID = "G-A044"
SPEC = reward.load(WORK_ID)
A043 = reward.load("G-A043")
BASE = SPEC["baseline"]
TERM = SPEC["single_change"]["name"]
PROBE_TO = "-1.75"
STORED_ARM = ROOT / BASE["stored_arm"]
A043_KEEP = ROOT / "workspace" / "_keep" / "go2_g_a043_a033_lin_vel_z_m15"
A042_KEEP = ROOT / "workspace" / "_keep" / "go2_g_a042_a033_track_lin_vel_xy_160"
PAYLOAD = reward.build_payload(SPEC)
PREFIX = "go2_g_a044/"
BACKSLASH = chr(92)
# The outer launcher, taken from the shipped runner rather than restated here.
LAUNCH_BLOCK = r"^  \[\[ -f \"\$SELF\".*?^  tmux new-session[^\n]*$"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PackageTest(unittest.TestCase):
    def test_1_build_is_deterministic(self) -> None:
        self.assertEqual(reward.build_zip(SPEC), reward.build_zip(SPEC))
        written = reward.output_path(SPEC)
        if written.is_file():
            self.assertEqual(written.read_bytes(), reward.build_zip(SPEC),
                             "발행된 ZIP 이 재빌드와 다르다")

    def test_2_exactly_one_reward_number_moves(self) -> None:
        candidate = reward_dict(PAYLOAD["candidate/quadruped_rewards.py"].decode("utf-8"))
        reference = reward_dict(PAYLOAD["reference/baseline_quadruped_rewards.py"].decode("utf-8"))
        self.assertEqual(candidate, SPEC["rewards"]["candidate"])
        self.assertEqual(reference, SPEC["rewards"]["baseline"])
        moved = [name for name in REWARD_NAMES if candidate[name] != reference[name]]
        self.assertEqual(moved, [TERM])
        self.assertEqual((reference[TERM], candidate[TERM]), (-2.0, -1.75))
        a = PAYLOAD["reference/baseline_quadruped_rewards.py"].decode("utf-8").splitlines()
        b = PAYLOAD["candidate/quadruped_rewards.py"].decode("utf-8").splitlines()
        self.assertEqual(len(a), len(b))
        self.assertEqual([i for i, (x, y) in enumerate(zip(a, b)) if x != y].__len__(), 1)

    def test_3_the_full_collection_contract_is_in_the_package(self) -> None:
        """계약은 문서가 아니라 패키지 안에 있어야 한다 — 러너가 읽는 파일에."""
        config = PAYLOAD["run_config.env"].decode("utf-8")
        self.assertIn("GO2_STAGE=full\n", config)
        self.assertIn("COLLECT_REQUIRED_ON_STATIONARY=1\n", config)
        self.assertIn(f"WORK_ID={WORK_ID}\n", config)
        self.assertIn("EVAL_CHECKPOINT_ITER=900\n", config)
        runner = PAYLOAD[SPEC["runner"]].decode("utf-8")
        # 러너가 run_config.env 를 source 한 **뒤** STAGE 를 정해야 이 줄이 효력이 있다.
        self.assertLess(runner.index('source "$PACKAGE_ROOT/run_config.env"'),
                        runner.index("STAGE=${GO2_STAGE:-target}"))
        self.assertNotIn("go2_target_gate.py", set(PAYLOAD))
        self.assertFalse([n for n in PAYLOAD if n.startswith("stored_baseline/")],
                         "전수 회차에는 서버 게이트가 없으므로 저장 기준선 사본도 필요 없다")

    def test_4_the_spec_declares_what_the_package_does(self) -> None:
        self.assertEqual(length.collection_mode(SPEC), length.FULL_COLLECTION)
        self.assertEqual(set(SPEC["stages"]), {"full"})
        self.assertNotIn("required_target_cases", SPEC["preregistered"],
                         "전수 수집에서는 '1단계에서만 재는 필수 기록'이 성립하지 않는다")
        self.assertEqual(SPEC["evaluation"]["case_count"], 69)
        self.assertGreaterEqual(len(SPEC["collection"]["reason"]), 40)
        self.assertIn("C-11", SPEC["collection"]["reason"])

    def test_5_the_value_is_between_two_measured_points_and_says_so(self) -> None:
        self.assertEqual(base_data.spec_problems(SPEC), [])
        self.assertEqual(base_data.walking_values(TERM), [-2.0, -1.5],
                         "A043 이 기반 데이터에 들어와야 -1.75 가 관측 사이 값이 된다")
        declared = SPEC["base_data"]["terms"][TERM]
        self.assertEqual(declared["status"], "BETWEEN_OBSERVED")
        self.assertNotIn("out_of_range_reason", declared)
        probes = {(r["term"], r["to"]): r for r in _read_csv(
            GO2 / "reports/evidence/go2_reward_mechanism_20260917/PROBES.csv")}
        row = probes[(TERM, PROBE_TO)]
        self.assertEqual((row["zone"], row["range_status"]), ("WALK", "BETWEEN_OBSERVED"))
        self.assertGreater(float(row["margin"]), float(row["margin_from"]))
        self.assertIn(row["margin"], SPEC["value_derivation"]["walk_margin"])

    def test_6_the_forecast_is_carried_as_a_limit_not_as_support(self) -> None:
        """A043 이 네 상황 중 둘을 방향까지 틀렸다 — 그 사실이 사양 안에 있어야 한다."""
        check = _read_csv(GO2 / "reports/evidence/go2_g_a043_readout_20260922/FORECAST_CHECK.csv")
        wrong = [r for r in check if r["direction_agrees"] == "False"]
        self.assertGreaterEqual(len(wrong), 2, "이 주장의 근거 자체가 사라졌다")
        sources = [row["source"] for row in SPEC["inference"]["contradicting"]]
        self.assertIn("reports/evidence/go2_g_a043_readout_20260922/FORECAST_CHECK.csv", sources)
        self.assertEqual(SPEC["inference"]["predictions"]["sway"]["direction"], "up",
                         "산수는 down 을 적지만 실측은 up 이다 — 실측을 적는다")
        self.assertEqual(SPEC["inference"]["predictions"]["push"]["direction"], "same")
        self.assertEqual(SPEC["inference"]["status"], "INFORMATION_RUN")

    def test_7_ten_cases_are_filmed_on_both_arms(self) -> None:
        videos = SPEC["videos"]
        self.assertEqual(len(videos["candidate"]), 10)
        self.assertEqual(len(videos["baseline"]), 4)
        self.assertEqual(len(videos["baseline_reuse"]), 6)
        self.assertEqual(length.video_caps(SPEC), (10, 4))
        self.assertEqual(length.video_caps(A043), (6, 2), "선언하지 않은 회차의 상한은 그대로다")
        self.assertEqual(sorted(videos["baseline"]) + sorted(videos["baseline_reuse"]),
                         sorted(videos["baseline"]) + sorted(videos["baseline_reuse"]))
        self.assertEqual(set(videos["baseline"]) | set(videos["baseline_reuse"]),
                         set(videos["candidate"]),
                         "후보 영상마다 기준선 짝이 있어야 한다")
        self.assertEqual(length.reuse_problems(SPEC), [])
        for entry in ("G6:push_pos_x:101", "G6:push_neg_x:101"):
            self.assertIn(entry, videos["baseline_reuse"], "밀침 영상 재사용이 이 회차의 새 자리다")
            self.assertEqual(videos["baseline_reuse"][entry]["identity_sha256"],
                             length.video_fingerprint(SPEC, entry))
        for entry in ("G2:combined_yaw_left:101", "G2:combined_yaw_right:101"):
            self.assertIn(entry, videos["baseline"], "A043 이 한 편도 찍지 않은 축이다")

    def test_8_the_screening_edition_only_adds_the_y_directions(self) -> None:
        version = SPEC["preregistered"]["plan_screening"]["version"]
        self.assertEqual(version, "post_a043_push4_v1")
        new = set(screening.cases_for(version))
        old = set(screening.cases_for("post_a042_push_v1"))
        self.assertEqual(new - old, set(screening.PUSH_Y))
        self.assertEqual(old - new, set())
        self.assertEqual(set(screening.cases_for("forward_stairs_v1")), set(screening.CASES))

    def test_9_every_threshold_is_the_one_g_a043_used(self) -> None:
        mine, theirs = SPEC["preregistered"], A043["preregistered"]
        for key in ("min_target_mean_proxy_delta", "min_target_groups_improved", "min_total_points_delta",
                    "flat_scenarios", "max_flat_scenario_proxy_drop", "max_flat_case_survival_drop",
                    "max_scenario_weighted_loss_70", "max_scenario_weighted_loss_70_by_scenario",
                    "target_groups", "target_group_floor", "climb_guard", "rule_version",
                    "target_axes", "guard_axes", "stationary_guard_scenarios",
                    "max_new_stationary_cases_in_guard"):
            with self.subTest(key=key):
                self.assertEqual(mine[key], theirs[key], f"{key} 가 앞 회차와 다르다 — 완화 금지")
        self.assertEqual(SPEC["training"], A043["training"])
        self.assertEqual(SPEC["evaluation"]["seeds"], [101, 202, 303])
        self.assertEqual(SPEC["evaluation"]["checkpoint_iter"], 900)

    def test_10_the_criteria_changes_document_exists_and_is_named(self) -> None:
        path = GO2 / SPEC["criteria_changes"].split(" ", 1)[0]
        self.assertTrue(path.is_file(), f"{path} 가 없다")
        text = path.read_text(encoding="utf-8")
        for needle in ("full_69_single_stage", "post_a043_push4_v1", "C-11", "C-12", "C-13",
                       "GO2_STAGE=full", TERM):
            self.assertIn(needle, text, f"근거 문서가 {needle} 를 적지 않았다")
        self.assertIn("실행 준비 완료로 보고하지 않는다", text)
        self.assertRegex(text, r"\*\*미실행\*\*")

    def test_11_the_earlier_releases_are_untouched(self) -> None:
        """이 회차의 빌더 변경이 이미 발행된 회차의 바이트를 건드리지 않았는가."""
        for work in ("G-A041", "G-A042", "G-A043"):
            with self.subTest(work=work):
                spec = reward.load(work)
                written = reward.output_path(spec)
                if not written.is_file():
                    self.skipTest(f"{work} 발행본이 없다")
                self.assertEqual(written.read_bytes(), reward.build_zip(spec))

    def test_12_the_published_files_say_one_file_one_command(self) -> None:
        current = GO2 / "upload" / WORK_ID / "current"
        if not current.is_dir():
            self.skipTest("아직 발행하지 않았다")
        name = SPEC["output"]["upload_zip"]
        data = (current / name).read_bytes()
        self.assertEqual(data, reward.build_zip(SPEC))
        manifest = json.loads((current / "UPLOAD_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["upload_files"][0]["sha256"], sha(data))
        self.assertEqual(manifest["release_id"], SPEC["output"]["release_id"])
        guide = (current / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn(f"bash {SPEC['output']['package_root']}/{SPEC['runner']}", guide)
        self.assertIn("1단계도 서버 게이트도 없다", guide)
        self.assertIn(SPEC["output"]["done_marker"], guide)
        self.assertIn(sha(data), guide)
        self.assertIn("69 case 전부", guide)

    def test_13_the_runner_relaunches_a_file_the_package_actually_ships(self) -> None:
        """Defect C-14.  Every earlier arm ran through the campaign wrapper, which calls the
        runner with --inner and never reaches this block.  Here the runner is the entry point,
        so the name it re-enters decides whether anything runs at all.  Executed, not read:
        the launcher's own lines run with a stub tmux, and the path handed to tmux must be a
        file this package ships."""
        runner_name = SPEC["runner"]
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "pkg"
            pkg.mkdir()
            for name, data in PAYLOAD.items():
                target = pkg / name[len(PREFIX):] if name.startswith(PREFIX) else pkg / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            text = (pkg / runner_name).read_text(encoding="utf-8")
            block = re.search(LAUNCH_BLOCK, text, re.M | re.S)
            self.assertIsNotNone(block, "launcher block not found in the runner")
            script = "\n".join([
                "set -euo pipefail",
                'tmux() { printf "%s" "${!#}"; }',
                "PACKAGE_ROOT=" + shlex.quote(str(pkg)),
                'SELF="$PACKAGE_ROOT/' + runner_name + '"',
                "RESUME=0; REMEASURE=0; STAGE=full",
                "ISAACLAB_SH=/opt/isaaclab.sh; TMUX_NAME=t",
                block.group(0),
                "",
            ])
            done = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            entered = re.search(r"bash (\S+) --inner", done.stdout)
            self.assertIsNotNone(entered, done.stdout)
            target = Path(entered.group(1).strip("'"))
            self.assertTrue(target.is_file(), "러너가 없는 파일로 재진입한다: %s" % target)
            self.assertEqual(target.name, runner_name)

    def test_14_every_shipped_recovery_command_runs_against_the_real_cli(self) -> None:
        """Defect C-15, 그리고 2026-09-23 사용자 검토가 찾은 그 나머지 절반.  안내문의 판독 명령은
        서버가 아직 예산을 쓰는 바로 그 순간 사용자가 치는 줄이다 — CLI 에 없는 선택지는 거기서
        argparse exit 2 를 낸다.  C-15 를 안내문에서만 고쳤더니 **같은 오타가 사양에 남았고, 사양은
        ZIP 안에 실려 서버로 간다**(`experiment.json` 의 readout, `--keep`).  그래서 여기서는 안내문과
        **발행된 ZIP 안의 사양** 양쪽에서 판독 명령을 뽑아 전부 실행한다."""
        current = GO2 / "upload" / WORK_ID / "current"
        if not current.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (current / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        with zipfile.ZipFile(current / SPEC["output"]["upload_zip"]) as archive:
            shipped = json.loads(archive.read(PREFIX + "experiment.json").decode("utf-8"))

        def commands_in(text: str) -> list[str]:
            joined = text.replace(BACKSLASH + "\n", " ")
            return [line.strip() for line in joined.splitlines()
                    if line.strip().startswith("python -B tools/")]

        def strings(node):
            if isinstance(node, dict):
                for value in node.values():
                    yield from strings(value)
            elif isinstance(node, list):
                for value in node:
                    yield from strings(value)
            elif isinstance(node, str):
                yield node

        commands = commands_in(guide)
        self.assertGreaterEqual(len(commands), 2, commands)
        inside = [command for text in strings(shipped) for command in commands_in(text)]
        self.assertTrue(inside, "발행된 사양에 판독 명령이 하나도 없다 — 뽑는 방법이 틀렸을 수 있다")
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        # 2026-09-24: 이 검사가 보는 것은 **CLI 가 이 줄을 받아들이는가** 이지 수확물의 내용이 아니다.
        # G-A044 가 실제로 회수된 뒤로는 같은 명령이 69 case 의 steps.csv 를 통째로 읽게 되어 한 번에
        # 수십 분이 걸렸고(관문 전체가 38분), 그렇게 느린 관문은 아무도 돌리지 않는다.  그래서 경로만
        # **없는 폴더**로 바꿔 배선을 잰다 — 수확물 전체 판독은 VerifierOnAFullHarvestTest 의 몫이다.
        # 시간 상한도 함께 건다: 다시 느려지면 여기서 떨어져 알게 된다.
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "no_harvest")
            for command in commands + inside:
                with self.subTest(command=command):
                    argv = [missing if part.startswith("workspace/_keep/") else part
                            for part in command.split()[1:]]
                    done = subprocess.run([sys.executable, *argv], cwd=str(ROOT), env=env,
                                          capture_output=True, text=True, timeout=180)
                    self.assertNotEqual(done.returncode, 2, command + "\n" + done.stderr)
                    for bad in ("unrecognized arguments", "the following arguments are required"):
                        self.assertNotIn(bad, done.stderr, command)

    def test_15_the_guide_does_not_let_sha_alone_close_the_server(self) -> None:
        """Defect C-16.  루트 AGENTS.md 「학습 종료 후 영상 증거 게이트」 §5·§7 은 종료 보고에
        영상·report·telemetry·로컬 검증을 각각 요구한다.  이전 판의 종료 절은 SHA 일치 한 줄뿐이라
        그 다섯 줄을 건너뛰어도 되는 것처럼 읽혔다."""
        current = GO2 / "upload" / WORK_ID / "current"
        if not current.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (current / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        _, _, gate = guide.partition("SERVER SHUTDOWN GATE")
        self.assertTrue(gate, "종료 게이트 절이 없다")
        self.assertIn("SHA 일치만으로 끄지 않는다", guide)
        for required in ("REPORT_ACQUIRED", "telemetry", "영상", "하나라도 비면 종료 불가"):
            self.assertIn(required, gate, required)

    def test_16_the_uploaded_file_name_says_which_edition_it_is(self) -> None:
        """Defect C-18 (사용자 지적 2026-09-22).  history 에 같은 이름의 ZIP 이 넷 있었고 그중 v3 는
        올리면 아무것도 돌지 않는 판이다(C-14).  그 상태에서 올릴 파일을 고르는 근거는 SHA 손대조
        한 줄뿐이었다.  이름이 판을 말하면 대조 없이도 틀린 파일을 집을 수 없다.  발행된 이름과
        안내문·manifest 가 모두 같은 판을 가리키는지 본다 — 셋 중 하나만 어긋나도 틀린 파일을
        올리게 된다."""
        version = SPEC["output"]["release_id"].rsplit("_", 1)[-1]
        self.assertRegex(version, r"^v\d+$")
        zip_name = SPEC["output"]["upload_zip"]
        self.assertTrue(zip_name.endswith("_%s.zip" % version), zip_name)
        current = GO2 / "upload" / WORK_ID / "current"
        if not current.is_dir():
            self.skipTest("아직 발행하지 않았다")
        published = sorted(current.glob("*.zip"))
        self.assertEqual([path.name for path in published], [zip_name],
                         "current 에는 올릴 ZIP 하나만, 그 이름으로만 있어야 한다")
        guide = (current / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn(zip_name, guide)
        manifest = json.loads((current / "UPLOAD_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual([entry["name"] for entry in manifest["upload_files"]], [zip_name])
        self.assertEqual(manifest["release_id"], SPEC["output"]["release_id"])

    def test_17_the_plan_is_kept_where_a_list_cannot_miss_it(self) -> None:
        """2026-09-22 사용자 질문("계획서를 제대로 따른 거야?")에서 나왔다.  test_9 는 대조할 키를
        **손으로 적어 둔다** — 목록 밖에 새 문턱이 생기면 조용히 지나간다.  여기서는 열거하지 않고
        `preregistered` 의 **숫자를 전부** 훑어 G-A043 과 대조한다.  계획 §6·§9 의 약속은 "문턱을
        하나도 바꾸지 않는다" 이므로, 어떤 숫자가 새로 생기거나 사라지는 것도 위반이다."""
        def numbers(node, path=""):
            found = {}
            for key, value in sorted(node.items()):
                if isinstance(value, dict):
                    found.update(numbers(value, path + key + "."))
                elif isinstance(value, bool):
                    continue
                elif isinstance(value, (int, float)):
                    found[path + key] = value
            return found

        mine, theirs = numbers(SPEC["preregistered"]), numbers(A043["preregistered"])
        self.assertEqual(sorted(mine), sorted(theirs),
                         "사전등록 숫자 항목의 집합이 앞 회차와 다르다 — 추가도 삭제도 완화다")
        self.assertEqual(mine, theirs, "사전등록 숫자가 앞 회차와 다르다 — 사후 완화 금지")
        self.assertGreaterEqual(len(mine), 19, mine)

    def test_18_the_comparison_arm_is_pinned_to_the_artifact_it_came_from(self) -> None:
        """계획 §1 은 비교 관측으로 G-A043 iter900 을 지목한다.  사양은 G-A043 을 수십 번 인용하면서
        그 정책이 **어느 정책인지**는 적지 않았다.  여기서는 사양의 값을 시험 안에 다시 적지 않고
        회수 산출물에서 읽어 대조한다 — 시험이 사양을 베끼면 둘이 함께 틀린다."""
        arm = SPEC["comparison_arm"]
        self.assertEqual(arm["name"], "G-A043")
        verify = ROOT / "workspace" / "server_returns" / "G-A043_LOCAL_VERIFY.json"
        if not verify.is_file():
            self.skipTest("G-A043 회수 산출물이 없다")
        facts = json.loads(verify.read_text(encoding="utf-8"))
        found = set(re.findall(r'"(?:CANDIDATE_MODEL_SHA|candidate_model_sha256)":\s*"([0-9a-f]{64})"',
                               json.dumps(facts, ensure_ascii=False)))
        self.assertEqual(found, {arm["model_sha256"]},
                         "사양이 고정한 G-A043 의 model SHA 가 회수 산출물과 다르다")

    def test_19_the_guide_carries_the_session_budget_not_just_the_runtime(self) -> None:
        """계획 §7 은 회수 여유를 포함해 **120~150분 세션 계획치**를 잡으라고 적는다.  안내문은 서버가
        도는 110분만 적고 있었다.  사용자가 읽는 것은 안내문이고, 실행 시간으로 TTL 을 잡으면 회수
        도중에 끊긴다 — 그때 잃는 것이 영상과 report 다(루트 AGENTS.md 「휘발성 서버 회수」)."""
        current = GO2 / "upload" / WORK_ID / "current"
        if not current.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (current / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        plan = (GO2 / "upload" / "plan" / "GO2_POST_A043_PLAN_20260922.md").read_text(encoding="utf-8")
        budget = re.search(r"(\d{2,3})~(\d{2,3})분 세션 계획치", plan)
        self.assertIsNotNone(budget, "계획서에서 세션 계획치를 찾지 못했다")
        self.assertIn("%s~%s분" % budget.groups(), guide,
                      "안내문이 계획 §7 의 세션 계획치를 옮기지 않았다")

    def test_20_the_guide_does_not_read_exit_1_as_a_performance_verdict(self) -> None:
        """Defect C-20 (사용자 검토 2026-09-23).  안내문 §5 는 **서버 종료 게이트**다.  이전 판은
        "두 명령의 exit 1 은 성능 기준 미충족" 이라고 적었는데 두 번 틀렸다.  ① 첫 명령은 성능 FAIL
        에 exit 0 을 낸다 — FAIL 이 PASS_VERDICTS 안에 있다.  exit 1 은 판정을 **못 했다**는 뜻이다.
        ② 둘째 명령은 FAIL 과 INCONCLUSIVE 를 같은 exit 1 에 담는다.  옛 문장대로 읽으면 서버가
        살아 있을 때만 메울 수 있는 결손을 성능 실패로 읽고 서버를 끈다.  그래서 여기서는 두 판독기를
        **빈 수확물로 실행**해 exit 1 이 성능 판정이 아님을 보이고, 판독기가 낼 수 있는 비통과 판정
        이름을 판독기 소스에서 읽어 안내문이 그것을 담는지 본다 — 시험이 이름을 다시 적지 않는다."""
        current = GO2 / "upload" / WORK_ID / "current"
        if not current.is_dir():
            self.skipTest("아직 발행하지 않았다")
        guide = (current / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn("FAIL", verifier.PASS_VERDICTS,
                      "검증기가 성능 FAIL 에 exit 0 을 내지 않는다면 안내문을 다시 써야 한다")
        source = Path(verifier.__file__).read_text(encoding="utf-8")
        assigned = set(re.findall(r'verdict"\]\s*=\s*"([A-Z_]+)"', source))
        unresolved = sorted(assigned - set(verifier.PASS_VERDICTS))
        self.assertTrue(unresolved, "판독기 소스에서 비통과 판정을 찾지 못했다")
        for verdict in unresolved:
            self.assertIn(verdict, guide, "exit 1 로 나오는 상태인데 안내문에 없다: %s" % verdict)

        joined = guide.replace(BACKSLASH + "\n", " ")
        commands = [line.strip() for line in joined.splitlines()
                    if line.strip().startswith("python -B tools/")]
        self.assertGreaterEqual(len(commands), 2, commands)
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        with tempfile.TemporaryDirectory() as tmp:
            for command in commands:
                tokens, argv, drop = command.split()[1:], [], 0
                for index, token in enumerate(tokens):
                    if drop:
                        drop -= 1
                        continue
                    if token in ("--harvest", "--candidate"):
                        argv += [token, tmp]
                        drop = 1
                    elif token == "--out":
                        drop = 1
                    else:
                        argv.append(token)
                done = subprocess.run([sys.executable, *argv], cwd=str(ROOT), env=env,
                                      capture_output=True, text=True)
                self.assertEqual(done.returncode, 1, command + "\n" + done.stdout[-400:])
                spoken = re.findall(r"^(?:VERDICT|SCREENING) (\S+)$", done.stdout, re.M)
                self.assertTrue(spoken, done.stdout[-400:])
                for verdict in spoken:
                    self.assertNotIn(verdict, (*verifier.PASS_VERDICTS, screening.PASS))
                    self.assertIn(verdict.replace("INTERNAL_GATE_", ""), guide,
                                  "빈 수확물이 내는 판정이 안내문에 없다: %s" % verdict)

    def test_21_a_stopped_run_cannot_report_itself_as_a_full_harvest(self) -> None:
        """Defect C-21 (사용자 검토 2026-09-23).  `finish` 는 두 경로에서 불린다: 목록을 다 잰 실행과,
        파국 게이트가 **아무것도 재지 않고** 멈춘 실행(:689 `finish "$DECISION" NOT_MEASURED`).  둘 다
        결과 ZIP 을 만들고 같은 `[DONE]` 표식을 찍었으므로, 표식만 보는 사람에게 두 상태는 구분되지
        않았다 — 회수 결손을 전수 완료로 읽고 휘발 서버를 끄면 그 결손은 영구가 된다.  정상 경로만
        시험하면 이 결함은 보이지 않는다.  그래서 발행된 러너의 `finish` 를 **실행**해 세 경우를 본다:
        조기 종료, 전수 완료, 그리고 수집이 조용히 잘린 경우(69 중 68)."""
        runner_name = SPEC["runner"]
        cases = [
            ("CATASTROPHE_NONFINITE", 0, 0, 0, 0, "INCOMPLETE_EARLY_STOP", True),
            ("SUITE_COMPLETE", 69, 5, 10, 4, "FULL_69_COMPLETE", False),
            ("SUITE_COMPLETE", 68, 5, 10, 4, "INCOMPLETE_COLLECTION", True),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "pkg"
            pkg.mkdir()
            for name, data in PAYLOAD.items():
                target = pkg / name[len(PREFIX):] if name.startswith(PREFIX) else pkg / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            runner = (pkg / runner_name).read_text(encoding="utf-8")
            bodies = []
            for func in ("count_files", "package_result", "finish"):
                found = re.search(r"^%s\(\) \{\n.*?^\}\n" % func, runner, re.M | re.S)
                self.assertIsNotNone(found, func)
                bodies.append(found.group(0))
            stub = Path(tmp) / "isaaclab_stub.sh"
            stub.write_text('#!/usr/bin/env bash\necho stub >"${@: -1}"\n', encoding="utf-8", newline="\n")
            label = re.search(r"^BASELINE_LABEL=(\S+)$", (pkg / "run_config.env").read_text(encoding="utf-8"),
                              re.M).group(1)
            for decision, cand, sent, videos, base_videos, expected, warns in cases:
                with self.subTest(decision=decision, cases=cand):
                    keep = Path(tmp) / ("keep_%s_%s" % (decision, cand))
                    (keep / "training").mkdir(parents=True)
                    (keep / "training" / "CHECKPOINT_PIN.txt").write_text(
                        "EVAL_CHECKPOINT_ITER=900\nREWARD_BEST_MODEL_ITER=900\n", encoding="utf-8")
                    for index in range(cand):
                        one = keep / "evaluation" / "candidate" / "cases" / ("case_%02d" % index)
                        one.mkdir(parents=True)
                        (one / "summary.json").write_text("{}", encoding="utf-8")
                    for index in range(sent):
                        one = keep / "evaluation" / ("%s_sentinel" % label) / "cases" / ("case_%02d" % index)
                        one.mkdir(parents=True)
                        (one / "summary.json").write_text("{}", encoding="utf-8")
                    for count, where in ((videos, keep / "evaluation" / "candidate" / "videos"),
                                         (base_videos, keep / "evaluation" / ("%s_videos" % label) / "videos")):
                        where.mkdir(parents=True, exist_ok=True)
                        for index in range(count):
                            (where / ("clip_%02d.mp4" % index)).write_bytes(b"mp4")
                    script = "\n".join([
                        "set -euo pipefail",
                        "PATH=/usr/bin:/bin:$PATH",
                        "PACKAGE_ROOT=" + shlex.quote(str(pkg)),
                        'source "$PACKAGE_ROOT/run_config.env"',
                        "KEEP=" + shlex.quote(str(keep)),
                        "RESULT_ZIP=" + shlex.quote(str(keep) + ".zip"),
                        "ISAACLAB_SH=" + shlex.quote(str(stub)),
                        "STAGE=full; REMEASURE=0",
                        "CANDIDATE_SHA=deadbeef; CANDIDATE_ENV=$PACKAGE_ROOT/run_config.env",
                        "EVALUATOR_SHA=e; REGISTRY_SHA=r",
                        *bodies,
                        'finish %s REUSED_STORED_WITH_SENTINEL' % decision,
                        "",
                    ])
                    done = subprocess.run(["bash", "-c", script], capture_output=True,
                                          encoding="utf-8", errors="replace")
                    self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                    status = (keep / "RUNNER_STATUS.txt").read_text(encoding="utf-8")
                    result = (keep / "RESULT_STATUS.txt").read_text(encoding="utf-8")
                    self.assertIn("COLLECTION_STATUS=%s" % expected, status, status)
                    self.assertIn("COLLECTION_STATUS=%s" % expected, result, result)
                    self.assertIn(SPEC["output"]["done_marker"], done.stdout,
                                  "finish 를 지나는 판이면 회수 준비 표식이 나와야 한다 "
                                  "(crash 경로는 finish 를 지나지 않는다 — test_22)")
                    if warns:
                        self.assertIn("[INCOMPLETE COLLECTION]", done.stdout, done.stdout)
                        self.assertNotIn("COLLECTION_STATUS=FULL_69_COMPLETE", status)
                    else:
                        self.assertNotIn("[INCOMPLETE COLLECTION]", done.stdout, done.stdout)

    def test_22_the_guide_tells_the_truth_about_the_marker_and_about_filling_in(self) -> None:
        """Defect C-24 (사용자 검토 2026-09-23 3회차).  안내문 §4 는 표식이 어느 판에서나 나온다고
        읽혔지만 러너의 `on_exit` crash 경로는 부분 ZIP 만 만들고 표식 없이 끝난다 — 오지 않을 줄을
        기다리는 사용자는 휘발 서버의 예산을 태운다.  그리고 「불완전하면 메운 뒤 종료」는 복구 가능한
        누락에만 맞는 말이다: 파국 게이트가 멈춘 판은 정책이 실행되지 않은 판이라 69 를 채우는 것이
        오히려 계약 위반이다.  여기서는 **발행된 러너의 crash 경로를 실행**해 표식이 없음을 보이고,
        안내문이 세 상태를 그대로 싣는지 본다."""
        current = GO2 / "upload" / WORK_ID / "current"
        if not current.is_dir():
            self.skipTest("아직 발행하지 않았다")
        runner_name = SPEC["runner"]
        marker = SPEC["output"]["done_marker"]
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "pkg"
            pkg.mkdir()
            for name, data in PAYLOAD.items():
                target = pkg / name[len(PREFIX):] if name.startswith(PREFIX) else pkg / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            runner = (pkg / runner_name).read_text(encoding="utf-8")
            bodies = []
            for func in ("package_result", "on_exit"):
                found = re.search(r"^%s\(\) \{\n.*?^\}\n" % func, runner, re.M | re.S)
                self.assertIsNotNone(found, func)
                bodies.append(found.group(0))
            stub = Path(tmp) / "isaaclab_stub.sh"
            stub.write_text('#!/usr/bin/env bash\necho stub >"${@: -1}"\n', encoding="utf-8", newline="\n")
            keep = Path(tmp) / "keep"
            (keep / "training").mkdir(parents=True)
            (keep / "launcher.log").write_text("[PHASE 1/6] training\n", encoding="utf-8")
            script = "\n".join([
                "set -euo pipefail",
                "PATH=/usr/bin:/bin:$PATH",
                "PACKAGE_ROOT=" + shlex.quote(str(pkg)),
                'source "$PACKAGE_ROOT/run_config.env"',
                "KEEP=" + shlex.quote(str(keep)),
                "RESULT_ZIP=" + shlex.quote(str(keep) + ".zip"),
                "ISAACLAB_SH=" + shlex.quote(str(stub)),
                *bodies,
                "trap on_exit EXIT",
                "exit 6",  # 학습이 죽은 판: 러너는 여기서 끝난다
                "",
            ])
            done = subprocess.run(["bash", "-c", script], capture_output=True,
                                  encoding="utf-8", errors="replace")
            self.assertEqual(done.returncode, 6, done.stdout + done.stderr)
            self.assertTrue((Path(str(keep) + ".zip")).is_file(), "crash 경로도 부분 ZIP 은 남긴다")
            for name in ("RUNNER_STATUS.txt", "RESULT_STATUS.txt"):
                self.assertIn("COLLECTION_STATUS=INCOMPLETE_CRASH",
                              (keep / name).read_text(encoding="utf-8"), name)
            self.assertNotIn(marker, done.stdout,
                             "crash 경로는 표식을 찍지 않는다 — 안내문이 그렇게 말해야 한다")

        guide = (current / release.RELEASES[WORK_ID]["guide"]).read_text(encoding="utf-8")
        self.assertIn("늘 나오는 것도 아니다", guide)
        for state in ("FULL_69_COMPLETE", "INCOMPLETE_COLLECTION", "INCOMPLETE_CRASH",
                      "INCOMPLETE_EARLY_STOP"):
            self.assertIn(state, guide, state)
        self.assertIn("69 를 채우지 않는다", guide)
        self.assertIn("개수 확인", guide)
        # 종료 게이트가 「FULL_69_COMPLETE 아니면 무조건 메운다」로 되돌아가면 여기서 떨어진다.
        section = guide[guide.index("5. SERVER SHUTDOWN GATE"):]
        self.assertIn("채우지 않는다", section)


def _read_csv(path: Path) -> list[dict]:
    import csv
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# 2026-09-24: 이 클래스는 69 case 의 steps.csv 를 통째로(약 600 MB) 세 번 읽는다 — 실측 34분이다.
# 그렇게 느린 관문은 일상 스윕에서 돌지 않게 되고, 돌지 않는 관문은 없는 것과 같다.  그래서 기본은
# **건너뛰되 이유를 말하고**, 회차를 발행하기 전에 `GO2_SLOW_TESTS=1` 로 한 번 돌린다.  돌 때는
# 스스로 시간을 재서 예산을 넘으면 **실패**한다 — 느려지는 것이 무한 대기가 아니라 붉은 관문이 되게.
SLOW_TESTS = os.environ.get("GO2_SLOW_TESTS") == "1"
SLOW_BUDGET_S = float(os.environ.get("GO2_SLOW_BUDGET_S", "3000"))


class SlowGateIsWiredTest(unittest.TestCase):
    """느린 관문을 **건너뛰는 것**이 조용한 삭제가 되지 않게 지킨다 (빠른 검사).

    전수 판독은 기본에서 건너뛴다.  그러면 누군가 클래스를 지우거나 검사를 비워도 스윕은 계속
    초록이다.  그래서 여기서 그 클래스가 아직 있고, 검사를 세 개 이상 들고 있고, 건너뜀이
    **명시적 옵트인**(`GO2_SLOW_TESTS=1`)으로 되어 있는지 본다.  이 검사는 1 초도 걸리지 않는다.
    """

    def test_the_full_harvest_gate_still_exists_and_is_opt_in(self) -> None:
        methods = [name for name in dir(VerifierOnAFullHarvestTest) if name.startswith("test_")]
        self.assertGreaterEqual(len(methods), 3, methods)
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertIn('os.environ.get("GO2_SLOW_TESTS") == "1"', source)
        self.assertIn("GO2_SLOW_BUDGET_S", source)
        self.assertEqual(SLOW_TESTS, os.environ.get("GO2_SLOW_TESTS") == "1")

    def test_the_harvest_reading_screens_are_opt_in_too(self) -> None:
        """실제 수확물을 읽는 screening 검사 다섯도 같은 스위치 뒤에 있어야 한다."""
        reading = [name for name in dir(PlanReadersTest)
                   if name.startswith("test_") and name != "test_4_the_y_block_fails_on_"
                   "degradation_that_the_old_edition_passes"]
        self.assertGreaterEqual(len(reading), 5, reading)
        source = Path(__file__).read_text(encoding="utf-8")
        body = source[source.index("\nclass PlanReadersTest(unittest.TestCase):"):]
        self.assertEqual(body.count("SLOW_TESTS, " + chr(34) + "실제 수확물 판독"), 5,
                         "수확물을 읽는 검사 다섯이 모두 옵트인이어야 한다")
        # 논리만 보는 검사는 **항상** 켜져 있어야 한다 — 합성 행이라 1초도 안 걸린다.
        logic = PlanReadersTest.test_4_the_y_block_fails_on_degradation_that_the_old_edition_passes
        self.assertFalse(getattr(logic, "__unittest_skip__", False),
                         "판정 논리 검사는 건너뛰면 안 된다")

    def test_the_same_harvest_is_not_read_twice(self) -> None:
        """같은 (수확물, 판) 을 두 번 읽지 않는다 — 한 번이 69 case x steps.csv 다."""
        self.assertTrue(hasattr(screened, "cache_info"), "screened 는 캐시되어야 한다")
        source = Path(__file__).read_text(encoding="utf-8")
        body = source[source.index("\nclass PlanReadersTest(unittest.TestCase):"):]
        self.assertNotIn("screening.screen(", body,
                         "PlanReadersTest 는 캐시된 screened() 로만 읽는다")


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir(),
                     "G-A033 harvest not present")
@unittest.skipUnless(SLOW_TESTS,
                     "느린 전수 판독 (실측 ~34분, 69 case x steps.csv). 발행 전에 "
                     "GO2_SLOW_TESTS=1 로 한 번 돌린다")
class VerifierOnAFullHarvestTest(unittest.TestCase):
    """이 회차가 낼 모양(69 case·STAGE=full)의 수확물을 판독기에 실제로 먹인다."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.started = time.monotonic()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def tearDown(self) -> None:
        spent = time.monotonic() - type(self).started
        self.assertLess(spent, SLOW_BUDGET_S,
                        f"전수 판독이 예산 {SLOW_BUDGET_S:.0f}초를 넘겼다 ({spent:.0f}초) — "
                        "느려진 원인을 찾거나 GO2_SLOW_BUDGET_S 로 예산을 명시적으로 올린다")

    @staticmethod
    def candidate_env() -> str:
        text = (STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8")
        patched, count = re.subn(rf"(\n  {TERM}:\n(?:    .*\n)*?    weight: )-2\.0\n", r"\g<1>-1.75\n", text)
        assert count == 1, f"{TERM} weight line not found exactly once"
        return patched

    def harvest(self, name: str) -> Path:
        keep = Path(self.tmp.name) / name
        model = b"synthetic G-A044 model"
        model_sha = sha(model)
        single = SPEC["single_change"]
        env_text = self.candidate_env()
        files = {
            "RESULT_STATUS.txt": "RESULT_STATE=FULL\n",
            "exported/report.html": "<html>synthetic</html>\n",
            "exported/REPORT_STATUS.txt": "REPORT_STATUS=REPORT_ACQUIRED\n",
            "training/TRAIN_STATUS.txt": (f"TRAIN_RC=0\nSEED=42\nNUM_ENVS=4096\nMAX_ITERATIONS=1000\n"
                                          f"SINGLE_CHANGE={single['name']}:{single['from']}->{single['to']}\n"),
            "training/env.yaml": env_text,
            "training/CHECKPOINT_PIN.txt": (f"EVAL_CHECKPOINT_ITER=900\nEVAL_CHECKPOINT_SHA={model_sha}\n"
                                            f"REWARD_BEST_MODEL_ITER=950\nREWARD_BEST_MODEL_SHA={'0' * 64}\n"),
            "meta/evaluator.sha256": f"{BASE['evaluator_sha256']}  go2_eval_telemetry.py\n",
            "meta/registry.sha256": f"{BASE['registry_sha256']}  go2_self_eval_registry.json\n",
        }
        for rel, content in files.items():
            (keep / rel).parent.mkdir(parents=True, exist_ok=True)
            (keep / rel).write_text(content, encoding="utf-8", newline="\n")
        (keep / "training" / "model_best.pt").write_bytes(model)
        report = (keep / "exported" / "report.html").read_bytes()
        (keep / "exported" / "report.html.sha256").write_text(f"{sha(report)}  report.html\n")
        (keep / "RUNNER_STATUS.txt").write_text(
            f"RUNNER_RC=0\nWORK_ID={WORK_ID}\nDECISION=SUITE_COMPLETE\nCANDIDATE_MODEL_SHA={model_sha}\n"
            f"STAGE=full\nCANDIDATE_EVAL_ITER=900\n", encoding="utf-8")
        stored = STORED_ARM / "evaluation" / BASE["stored_label"]
        out = keep / "evaluation" / "candidate"
        # 69 case 를 세 번 복사하면 수 GB 다 — 내용은 그대로 쓰고 하드링크만 건다.
        # 판정기는 파일을 읽기만 하고, case 를 지우는 검사는 링크만 지운다.
        shutil.copytree(stored / "cases", out / "cases", copy_function=os.link)
        (out / "identity.json").write_text(json.dumps({
            "model_sha256": model_sha, "env_sha256": sha(env_text.encode("utf-8")),
            "evaluator_sha256": BASE["evaluator_sha256"], "registry_sha256": BASE["registry_sha256"]}),
            encoding="utf-8")
        sentinel = keep / "evaluation" / f"{BASE['label']}_sentinel"
        for entry in SPEC["evaluation"]["sentinel_cases"]:
            _scenario, case_id, seed = entry.split(":")
            shutil.copytree(stored / "cases" / f"seed_{seed}" / case_id,
                            sentinel / "cases" / f"seed_{seed}" / case_id,
                            dirs_exist_ok=True, copy_function=os.link)
        (sentinel / "identity.json").write_text(json.dumps({
            "model_sha256": BASE["model_sha256"], "env_sha256": BASE["env_sha256"],
            "evaluator_sha256": BASE["evaluator_sha256"], "registry_sha256": BASE["registry_sha256"]}),
            encoding="utf-8")
        (keep / "SHA256SUMS.txt").write_text(f"{sha(report)}  ./exported/report.html\n")
        return keep

    def test_1_a_full_harvest_reads_cleanly_and_a_no_change_arm_fails(self) -> None:
        keep = self.harvest("same")
        measured = len(list((keep / "evaluation/candidate/cases").glob("seed_*/*/summary.json")))
        self.assertEqual(measured, 69, "전수 회차의 수확물은 69 case 다")
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["artifact_faults"], [])
        self.assertEqual(local["baseline_arm"], "STORED_G-A033")
        self.assertEqual(local["verdict"], "FAIL",
                         "기준선을 그대로 베낀 팔은 개선이 0 이므로 통과해서는 안 된다")

    def test_2_a_wrong_trained_weight_is_caught(self) -> None:
        keep = self.harvest("wrong_weight")
        (keep / "training" / "env.yaml").write_text(
            (STORED_ARM / "training" / "env.yaml").read_text(encoding="utf-8"),
            encoding="utf-8", newline="\n")
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["verdict"], "INCONCLUSIVE")
        self.assertTrue(any(f.startswith(f"env_reward_{TERM}") for f in local["artifact_faults"]),
                        local["artifact_faults"])

    def test_3_a_missing_case_is_never_a_verdict(self) -> None:
        keep = self.harvest("missing")
        shutil.rmtree(keep / "evaluation/candidate/cases/seed_202/combined_yaw_right")
        local = verifier.verify(keep, STORED_ARM, SPEC)
        self.assertEqual(local["verdict"], "INCONCLUSIVE",
                         "G2 한 case 가 빠진 수확물로 판정을 내리면 C-11 을 되풀이한다")


@functools.lru_cache(maxsize=None)
def screened(root: Path, edition: str | None) -> dict:
    """같은 (수확물, 판)을 두 번 읽지 않는다 — 한 번이 69 case x steps.csv 다.

    2026-09-24: 이 클래스는 같은 A033 수확물을 판만 바꿔 네 번 읽고 있었다.  `screen` 은 파일을
    읽기만 하는 순수 함수라 결과를 재사용해도 검사하는 내용이 달라지지 않는다.
    """
    if edition is None:
        return screening.screen(root)
    return screening.screen(root, cases=screening.cases_for(edition))


@unittest.skipUnless((STORED_ARM / "evaluation" / "candidate" / "cases").is_dir(),
                     "G-A033 harvest not present")
class PlanReadersTest(unittest.TestCase):
    """계획 §6 의 판독기를 실제 수확물에 돌려 본다.

    실제 수확물을 읽는 검사는 `GO2_SLOW_TESTS=1` 에서만 돈다 — 한 번에 수백 MB 의 steps.csv 를
    파싱하기 때문이다(위 VerifierOnAFullHarvestTest 와 같은 이유).  판정 논리 자체를 보는 검사
    (test_4)는 합성 행으로 돌아 늘 켜져 있고, 건너뛰는 검사들이 사라지지 않았는지는
    SlowGateIsWiredTest 가 본다.
    """

    VERSION = "post_a043_push4_v1"

    @unittest.skipUnless(SLOW_TESTS, "실제 수확물 판독 — GO2_SLOW_TESTS=1 에서만")
    def test_1_no_change_is_a_screening_fail_not_a_pass(self) -> None:
        report = screened(STORED_ARM, self.VERSION)
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertEqual(report["unreadable"], [])
        self.assertIn("post_a043_push4_v1", report["rule"])
        self.assertEqual(report["cases"], list(screening.cases_for(self.VERSION)))

    @unittest.skipUnless(SLOW_TESTS, "실제 수확물 판독 — GO2_SLOW_TESTS=1 에서만")
    def test_2_the_push_block_covers_four_directions(self) -> None:
        names = [c["check"] for c in screened(STORED_ARM, self.VERSION)["checks"]]
        for case_id in screening.PUSH_ALL:
            for suffix in ("pooled posture falls <= baseline", "survival median delta >= 0",
                           "tracking proxy median delta >= 0"):
                self.assertIn(f"{case_id} {suffix}", names)

    @unittest.skipUnless(SLOW_TESTS, "실제 수확물 판독 — GO2_SLOW_TESTS=1 에서만")
    def test_3_the_earlier_editions_judge_exactly_what_they_judged(self) -> None:
        old = screened(STORED_ARM, "post_a042_push_v1")
        self.assertNotIn("post_a043_push4_v1", old["rule"])
        old_names = {c["check"] for c in old["checks"]}
        new_names = {c["check"] for c in screened(STORED_ARM, self.VERSION)["checks"]}
        self.assertEqual(new_names - old_names,
                         {f"{case_id} {suffix}" for case_id in screening.PUSH_Y
                          for suffix in ("pooled posture falls <= baseline", "survival median delta >= 0",
                                         "tracking proxy median delta >= 0")})
        self.assertEqual(old_names - new_names, set())

    def test_4_the_y_block_fails_on_degradation_that_the_old_edition_passes(self) -> None:
        """새 판이 더하는 것이 실제로 무엇인지 — 결측이 아니라 **악화** 검출로 보인다."""
        cases = screening.cases_for(self.VERSION)

        def rows(**tweak):
            out = {}
            for case_id in cases:
                for seed in screening.SEEDS:
                    row = {"case": case_id, "seed": seed, "missing": [], "progress_m": 4.0,
                           "survival": 0.9, "tracking": 0.8, "posture_falls": 4,
                           "fingerprint": {"case": case_id, "seed": seed}}
                    if case_id in screening.STAIRS:
                        row.update(ge1=10, ge2=5, stall_share=0.5,
                                   first_step_time_median_s=1.0, arrival_rate=1.0)
                    row.update(tweak.get(case_id, {}))
                    out[(case_id, seed)] = row
            return out

        better = {case: {"progress_m": 5.0, "ge1": 11, "ge2": 6, "stall_share": 0.4}
                  for case in screening.STAIRS}
        self.assertEqual(screening.judge(rows(), rows(**better), cases)["verdict"], screening.PASS)

        worse_y = dict(better, push_neg_y={"posture_falls": 6, "survival": 0.8})
        report = screening.judge(rows(), rows(**worse_y), cases)
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertIn("push_neg_y pooled posture falls <= baseline", report["failed"])
        self.assertIn("push_neg_y survival median delta >= 0", report["failed"])
        self.assertEqual(report["unreadable"], [], "자료는 전부 있다 — 결측이 아니라 악화다")
        old = screening.judge(rows(), rows(**worse_y), screening.cases_for("post_a042_push_v1"))
        self.assertEqual(old["verdict"], screening.PASS,
                         "옛 판이 이 악화를 이미 잡았다면 새 판의 근거가 달라진다")

    @unittest.skipUnless(SLOW_TESTS, "실제 수확물 판독 — GO2_SLOW_TESTS=1 에서만")
    @unittest.skipUnless(A043_KEEP.is_dir(), "G-A043 harvest not present")
    def test_5_the_a043_harvest_still_screens_the_way_it_was_judged(self) -> None:
        report = screened(A043_KEEP, "post_a042_push_v1")
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertIn("push_pos_x tracking proxy median delta >= 0", report["failed"])
        self.assertIn("push_neg_x tracking proxy median delta >= 0", report["failed"])

    @unittest.skipUnless(SLOW_TESTS, "실제 수확물 판독 — GO2_SLOW_TESTS=1 에서만")
    @unittest.skipUnless(A042_KEEP.is_dir(), "G-A042 harvest not present")
    def test_6_the_a042_harvest_still_screens_the_way_it_was_judged(self) -> None:
        report = screened(A042_KEEP, None)
        self.assertEqual(report["verdict"], screening.FAIL)
        self.assertIn("stairs_10_down pooled ge2 >= baseline", report["failed"])


if __name__ == "__main__":
    unittest.main()
