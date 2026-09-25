"""Canonical-document consistency checks for the Go2 campaign (2026-09-14 audit, remediation B3).

The campaign audit found that the must-read reward ledger disagreed with the decision ledger and that
canonical documents contradicted each other. These checks fail when that drift comes back.
"""
import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
KEEP = ROOT / "workspace/_keep"
NOW = ROOT / "GO2_NOW.md"
MASTER = ROOT / "GO2_REWARD_EVIDENCE_MASTER.md"
REGISTRY = GO2 / "config/go2_self_eval_registry.json"
EXTREF = GO2 / "config/go2_external_reference.json"
# Frozen screening baseline (G-D-BASELINE-A033-20260916). Point these at the promoted run;
# every identity check below follows from them, so a promotion touches one place.
BASELINE_TRAINING = KEEP / "go2_g_a033_a017_track_lin_vel_xy_150/training"
BASELINE_IDENTITY = KEEP / "go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate/identity.json"
A027_IDENTITY = KEEP / "go2_a017_full_suite/evaluation/a017/SELF_EVAL_REPORT.json"
ROLE_FILES = sorted((ROOT / ".codex/agents").glob("go2-*.md"))
DIALS = ("track_lin_vel_xy_exp", "feet_air_time", "lin_vel_z_l2",
         "ang_vel_xy_l2", "action_rate_l2", "flat_orientation_l2")
PIPE = re.compile(r"(?<!\\)\|")


def read(path):
    return path.read_text(encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(text, heading):
    start = text.index(heading)
    rest = text[start + len(heading):]
    stop = re.search(r"^## ", rest, re.M)
    return rest[: stop.start()] if stop else rest


def table_rows(block):
    for line in block.splitlines():
        if line.startswith("| `"):
            yield [cell.strip() for cell in PIPE.split(line)[1:-1]]


def now_field(key):
    match = re.search(rf"^{key}:\s*(\S+)\s*$", read(NOW), re.M)
    if not match:
        raise AssertionError(f"GO2_NOW.md missing field {key}")
    return match.group(1)


def go2_docs():
    yield from sorted(ROOT.glob("GO2_*.md"))
    yield ROOT / "ARTIFACT_MANAGEMENT.md"
    yield from sorted(GO2.rglob("*.md"))


def work_number(work_id):
    return int(re.fullmatch(r"G-A(\d+)", work_id).group(1))


class CanonicalConsistencyTest(unittest.TestCase):
    def test_1_dial_history_matches_reward_ledger(self):
        text = read(MASTER)
        summary_block = section(text, "## 1-a.").split("### 전체 시도")[0]
        summary = {row[0].strip("`"): row[1] for row in table_rows(summary_block)}
        self.assertEqual(set(summary), set(DIALS), "§1-a summary must list every tuned dial once")
        ledger = {row[0].strip("`"): row for row in table_rows(section(text, "## 2. reward 대장"))}
        for dial, state in summary.items():
            self.assertIn(dial, ledger, dial)
            self.assertIn(state, ledger[dial][5], f"{dial}: §2 status must start from §1-a state {state!r}")

    def test_1b_ledger_pilot_column_matches_engine(self):
        spec = importlib.util.spec_from_file_location("go2_tuning_config", GO2 / "go2_tuning_config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        pilot = config.FROZEN_BASELINES["Pilot-01"]["rewards"]
        ledger = {row[0].strip("`"): row for row in table_rows(section(read(MASTER), "## 2. reward 대장"))}
        for dial in DIALS:
            self.assertAlmostEqual(float(ledger[dial][2]), pilot[dial], msg=f"{dial} Pilot-01 column")

    def test_1c_role_docs_carry_the_ledger_first_rule(self):
        """2026-09-18: three of the four role docs never mentioned the 09-17 rules and none named the
        run ledger, which is how a recommendation got built on a stale draft instead of on
        reports/runs/TERRAIN_AT_PIN.csv. The rule lives in the docs and is checked here."""
        required = ("G-D-LEDGER-FIRST-20260918", "reports/runs/TERRAIN_AT_PIN.csv", "fact_rules_v1",
                    "tools/test_go2_detectability_gate.py", "go2_climb_count.py")
        for path in ROLE_FILES:
            text = read(path)
            for needle in required:
                with self.subTest(role=path.name, needle=needle):
                    self.assertIn(needle, text, f"{path.name} must carry {needle}")

    def test_1d_role_docs_only_point_at_files_that_exist(self):
        """2026-09-18: the auditor doc pointed at `evidence/.../isaaclab_tasks_go2_rough_env_cfg.py`
        and at a bare `SOURCES.csv` that names two different files. A role agent cannot open either,
        so the reference is a claim, not evidence. Every backticked path must resolve to one file.

        2026-09-18 audit D3: this only swept `.claude/agents`, while GO2_NOW.md names the four role
        docs under `.codex/agents`, and those four broke the same rule (eight abbreviated paths, a
        bare `env.yaml` that matches three files). Covering only the docs one has just fixed is not
        a gate — it moves the defect out of scope. Both directories are swept now."""
        agents = sorted((ROOT / ".claude/agents").glob("go2-*.md"))
        agents += sorted((ROOT / ".codex/agents").glob("go2-*.md"))
        self.assertTrue(agents, ".claude/agents/go2-*.md is missing")
        index = {}
        for candidate in list(GO2.rglob("*")) + list((ROOT / "tools").glob("*.py")):
            if candidate.is_file() and candidate.suffix in (".md", ".csv", ".py", ".json", ".yaml"):
                index.setdefault(candidate.name, []).append(candidate)
        for path in agents:
            text = read(path)
            for ref in sorted(set(re.findall(r"`([A-Za-z0-9_./\-]+\.(?:md|csv|py|json|yaml))`", text))):
                with self.subTest(role=path.name, ref=ref):
                    self.assertNotIn("...", ref, f"{path.name}: abbreviated path {ref}")
                    if any((base / ref).is_file() for base in (GO2, GO2 / "reports", ROOT)):
                        continue
                    hits = index.get(Path(ref).name, [])
                    self.assertTrue(hits, f"{path.name}: {ref} does not exist")
                    self.assertEqual(len(hits), 1,
                                     f"{path.name}: bare {ref} matches {len(hits)} files — write the full path")

    def test_1e_no_doc_may_claim_the_deployed_six_are_exhausted(self):
        """2026-09-18 분석가 판독: "6개 목록 안에는 남은 레버가 없다"는 거짓이었다.

        그 문장은 `GO2_NOW.md`, `GO2_OPEN_DECISIONS.md`, 그리고 그 생성기
        `tools/go2_open_decisions.py` 세 곳에 있었고, **U1(R-6 확장 해석)을 사용자에게 승인
        권고하는 전제**였다.  반증 원본은 우리 정본 원장 자신이다: `GO2_REWARD_EVIDENCE_MASTER.md`
        §1-a 가 `lin_vel_z_l2`·`flat_orientation_l2` 를 "미탐색", `ang_vel_xy_l2` 완화와
        `action_rate_l2` 강화를 "미탐색"으로 적는다.  양방향 유효 기각으로 닫힌 항은
        `feet_air_time` 하나뿐이다.

        규칙: 원장이 아직 "미탐색"을 적고 있는 한, 어떤 문서도 6항이 소진됐다고 주장할 수 없다.
        정정문("~는 거짓이었다")은 그 주장이 아니므로 부정·정정 맥락은 통과시킨다."""
        master = read(ROOT / "GO2_REWARD_EVIDENCE_MASTER.md")
        unexplored = [term for term in ("lin_vel_z_l2", "ang_vel_xy_l2",
                                        "action_rate_l2", "flat_orientation_l2")
                      if re.search(rf"`{re.escape(term)}`[^\n]*미탐색", master)]
        if not unexplored:
            self.skipTest("원장 §1-a 에 미탐색 항이 남아 있지 않다 — 주장이 참일 수 있다")
        # 2026-09-18 감사 D1: 첫 판은 한국어 "남은 레버가 없" 만, 그리고 문서 네 종류만 훑었다.
        # 같은 거짓 주장이 **영어로** 사양 JSON 두 필드(`decision_ref`, `why`)에, 그리고 역할
        # 시험지의 **Q12 정답지**에 그대로 살아 있었다 — 역할이 채점받는 모범답안이 반증된 문장이었다.
        # 관문이 표현과 파일 종류를 좁게 잡으면 규칙이 아니라 그 문장 하나를 지운 것일 뿐이다.
        claim = re.compile(r"남은 레버가 없"
                           r"|(?:six|6)[^\n]{0,60}(?:closed by a measured rejection|are exhausted)"
                           r"|each of the other six deployed names is closed")
        negated = re.compile(r"(거짓|아니다|틀렸|반증|철회|false|refuted)")
        targets = [ROOT / "GO2_NOW.md",
                   GO2 / "reports/GO2_OPEN_DECISIONS.md",
                   ROOT / "tools/go2_open_decisions.py",
                   ROOT / "tools/go2_role_situation_exam.py",
                   GO2 / "reports/GO2_ROLE_SITUATION_EXAM.md",
                   GO2 / "reports/evidence/go2_role_situation_exam_20260918/EXAM.csv"]
        targets += sorted((ROOT / ".claude/agents").glob("go2-*.md"))
        targets += sorted((ROOT / ".codex/agents").glob("go2-*.md"))
        targets += sorted((GO2 / "config/experiments").glob("*.json"))
        for path in targets:
            if not path.is_file():
                continue
            for number, line in enumerate(read(path).splitlines(), 1):
                for hit in claim.finditer(line):
                    window = line[max(0, hit.start() - 60):hit.end() + 60]
                    with self.subTest(doc=path.name, line=number):
                        self.assertTrue(
                            negated.search(window) or "정정" in window,
                            f"{path.name}:{number} 이 6항 소진을 주장하는데 원장 §1-a 는"
                            f" {', '.join(unexplored)} 를 아직 '미탐색'으로 적는다")

    def test_1f_every_doc_states_the_real_number_of_preserved_cases(self):
        """2026-09-19 감사 D8: 보존 사례가 CASES.csv 14건인데 GO2_NOW.md 는 13건,
        역할 문서 셋은 10건으로 적고 있었다.  사례를 늘릴 때마다 사람이 네 곳을 손으로 고쳐야
        했고, 그것을 세는 관문이 없어 셋 다 뒤처졌다.  건수는 CSV 에서 읽는다."""
        rows = read(GO2 / "reports/evidence/go2_role_regression_20260918/CASES.csv").splitlines()
        count = sum(1 for line in rows[1:] if re.match(r"^[CM]\d\d,", line))
        self.assertGreater(count, 0, "CASES.csv 에서 사례를 세지 못했다")
        targets = [ROOT / "GO2_NOW.md"]
        targets += sorted((ROOT / ".claude/agents").glob("go2-*.md"))
        for path in targets:
            text = read(path)
            for stated in re.findall(r"실수 (\d+)건", text):
                with self.subTest(doc=path.name):
                    self.assertEqual(int(stated), count,
                                     f"{path.name} 이 실수 {stated}건이라 적는데 CASES.csv 는 {count}건이다")

    def test_2_no_fixed_stage_or_baseline_in_role_guidance(self):
        for path in ROLE_FILES + [GO2 / "AGENTS.md"]:
            self.assertIsNone(re.search(r"현재는 단계\s*\*{0,2}\d/6", read(path)), path.name)
        planner = read(ROOT / ".codex/agents/go2-test-planner.md")
        self.assertIn("GO2_NOW.md", section(planner, "## 현재 기준선"))
        for path in [GO2 / "AGENTS.md"] + ROLE_FILES:
            self.assertIn("GO2_NOW.md", read(path), f"{path.name} must route to GO2_NOW.md")

    def test_3_report_limit_agrees_and_registry_fingerprint_is_frozen(self):
        self.assertRegex(read(ROOT / "AGENTS.md"), r"2라운드[^\n]{0,12}500자")
        self.assertIn("500자", section(read(GO2 / "AGENTS.md"), "## 7. 제출 계약"))
        self.assertNotIn("30~200자 입력", read(GO2 / "AGENTS.md"))
        self.assertEqual(sha256(REGISTRY), now_field("REGISTRY_SHA256"),
                         "registry bytes are part of the evaluator fingerprint; do not edit")
        if A027_IDENTITY.is_file():
            identity = json.loads(read(A027_IDENTITY))["identity"]
            self.assertEqual(identity["registry_sha256"], now_field("REGISTRY_SHA256"))

    def test_4_now_baseline_identity_matches_artifacts(self):
        if not BASELINE_TRAINING.is_dir():
            self.skipTest("baseline training artifacts not present locally")
        self.assertEqual(sha256(BASELINE_TRAINING / "model_best.pt"), now_field("BASELINE_MODEL_SHA256"))
        self.assertEqual(sha256(BASELINE_TRAINING / "env.yaml"), now_field("BASELINE_ENV_SHA256"))
        if BASELINE_IDENTITY.is_file():
            # The arm that produced the 69-case score must be the same bytes as the baseline.
            identity = json.loads(read(BASELINE_IDENTITY))
            self.assertEqual(identity["model_sha256"], now_field("BASELINE_MODEL_SHA256"))
            self.assertEqual(identity["env_sha256"], now_field("BASELINE_ENV_SHA256"))
            self.assertEqual(identity["registry_sha256"], now_field("REGISTRY_SHA256"))

    def test_5_new_specs_cite_dial_history(self):
        history = section(read(MASTER), "## 1-a.")
        for path in sorted((GO2 / "config/experiments").glob("G_A*.json")):
            match = re.match(r"G_A(\d+)", path.name)
            if not match or int(match.group(1)) < 30:
                continue
            spec = json.loads(read(path))
            ref = spec.get("dial_history_ref")
            self.assertTrue(ref, f"{path.name} must carry dial_history_ref")
            self.assertIn(str(ref), history, f"{path.name} dial_history_ref not found in §1-a")
            if int(match.group(1)) >= 31:
                # G-D-EXTREF-20260915: candidates from G-A031 on carry the external-reference comparison.
                self.assertTrue(spec.get("external_reference"), f"{path.name} must carry external_reference")

    def test_6_now_last_training_is_current(self):
        if not KEEP.is_dir():
            self.skipTest("_keep not present locally")
        latest = 0
        for decision in KEEP.glob("*/**/reports/TIER1_DECISION.json"):
            run_root = KEEP / decision.relative_to(KEEP).parts[0]
            if not any(run_root.rglob("model_best.pt")):
                continue
            work_id = json.loads(read(decision)).get("work_id") or ""
            if re.fullmatch(r"G-A\d+", work_id):
                latest = max(latest, work_number(work_id))
        self.assertGreaterEqual(work_number(now_field("LAST_TRAINING_WORK_ID")), latest,
                                "GO2_NOW.md last training is older than the newest trained result in _keep")

    def test_7_candidate_priority_rule_matches_user_decision(self):
        # 2026-09-14 plan-policy audit F12: candidate order is a comparison, not "largest-loss scenario
        # first". 2026-09-17 (G-D-FACT-RULES-20260917): the comparison is the fact-based inference
        # chain, not a point-gain estimate. Phrase guard only: it catches deleted or reverted rule
        # sentences, not a reworded rule with a different meaning.
        decisions = ("G-D-PRIORITY-20260914", "G-D-FACT-RULES-20260917")
        no_fall_prerequisite = "낙상 완치를 다른 개선의 선행조건으로 두지 않는다"
        chain = "사실 근거 추론 사슬·반증 조건·실험 비용"
        rule = section(read(MASTER), "## 5. 다음 후보 선정 규칙")
        for phrase in ("자동 1순위가 아니다", chain, "반대 행", no_fall_prerequisite, "민감도",
                       "이득 수치는 요구하지 않는다"):
            self.assertIn(phrase, rule, f"MASTER §5 lost {phrase!r}")
        self.assertNotIn("가장 큰 시나리오를 찾는다", rule)
        self.assertNotIn("기대 가중 이득은 **수치여야 한다.**", rule)
        planner = read(ROOT / ".codex/agents/go2-test-planner.md")
        for path, text in ((ROOT / "AGENTS.md", read(ROOT / "AGENTS.md")), (MASTER, rule),
                           (ROOT / ".codex/agents/go2-test-planner.md", planner)):
            self.assertIn(chain, text, f"{path.name} lost the inference-chain rule")
            self.assertNotIn("기대 가중 이득·실험 비용·원인 확실성", text, f"{path.name} kept the gain rule")
        self.assertIn(no_fall_prerequisite, read(ROOT / "AGENTS.md"))
        self.assertNotIn("최대 감점 G 시나리오의 약한 인수 하나로 정한다", planner)
        self.assertIn("자동 1순위가 아니다", planner)
        for path in (MASTER, ROOT / "AGENTS.md", ROOT / ".codex/agents/go2-test-planner.md", NOW):
            for decision in decisions:
                self.assertIn(decision, read(path), f"{path.name} must cite {decision}")

    def test_8_now_fits_one_page(self):
        # Remediation plan B1: GO2_NOW.md is a one-page entry point capped at 60 lines.
        self.assertLessEqual(len(read(NOW).splitlines()), 60, "GO2_NOW.md exceeds the B1 60-line cap")

    def test_9_encoding_damage_is_quarantined(self):
        # G-P-A029-REVISION-20260914 R5: text whose Korean was saved as "?" must not be re-cited.
        # Every damaged line must sit in a block (between clean headings) that carries a CORRUPTED marker.
        # Headings containing "??" are themselves damaged and do not end a block. Backtick quotes are ignored.
        unmarked = []
        for path in go2_docs():
            lines = read(path).splitlines()
            clean_heading = [i for i, line in enumerate(lines) if line.startswith("#") and "??" not in line]
            for i, line in enumerate(lines):
                if "???" not in re.sub(r"`[^`]*`", "", line):
                    continue
                start = max((h for h in clean_heading if h <= i), default=0)
                stop = min((h for h in clean_heading if h > i), default=len(lines))
                if not any("CORRUPTED" in block_line for block_line in lines[start:stop]):
                    unmarked.append(f"{path.relative_to(ROOT)}:{i + 1}")
        self.assertEqual(unmarked, [], "damaged lines outside a CORRUPTED block")

    def test_10_old_target_rule_is_marked_superseded(self):
        # G-P-A029-REVISION-20260914 R2: copies of "next target = G5 or G3 survival" must cite the decision
        # that replaced it. Phrase guard only.
        decision = "G-D-PRIORITY-20260914"
        for path in go2_docs():
            if "G5 또는 G3 생존" in read(path):
                self.assertIn(decision, read(path), f"{path.relative_to(ROOT)} repeats the old target rule")
        self.assertIn(decision, read(GO2 / "reports/GO2_G_A029_TUNING_AUDIT_20260914.md"))

    def test_11_external_reference_agrees(self):
        # G-D-EXTREF-20260915: MASTER §1-b table, the reference JSON and the trained baseline env must agree,
        # and every Go2 guide must route to §1-b.
        ref = json.loads(read(EXTREF))
        rewards = ref["isaaclab"]["rewards"]
        start = ref["deployed_start"]["rewards"]

        def cell(text):
            return None if text == "None" else float(text)

        table = section(read(MASTER), "## 1-b.").split("**B.")[0]
        rows = {row[0].strip("`"): row for row in table_rows(table)}
        self.assertEqual(set(rows), set(rewards["go2_rough"]), "§1-b table must list every reference term once")
        for term, row in rows.items():
            for column, expected in ((1, rewards["base"][term]), (2, rewards["go2_rough"][term]),
                                     (3, rewards["go2_flat"][term]), (4, start.get(term, rewards["go2_rough"][term]))):
                self.assertEqual(cell(row[column]), expected, f"§1-b {term} column {column}")
        if BASELINE_TRAINING.is_dir():
            spec = importlib.util.spec_from_file_location("candidate_suite_checks", GO2 / "candidate_suite_checks.py")
            checks = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(checks)
            trained = checks.reward_weights(read(BASELINE_TRAINING / "env.yaml"))
            for term, row in rows.items():
                self.assertEqual(cell(row[5]), trained.get(term), f"§1-b baseline column {term}")
                if term not in DIALS:
                    # Terms nobody tuned come from the server's Isaac Lab: they pin its version to the reference.
                    self.assertEqual(trained.get(term), rewards["go2_rough"][term], f"server Isaac Lab differs on {term}")
        for path in [GO2 / "AGENTS.md", ROOT / "AGENTS.md"] + ROLE_FILES:
            self.assertIn("§1-b", read(path), f"{path.name} must route to MASTER §1-b")
        for path in (MASTER, NOW, GO2 / "AGENTS.md", ROOT / "AGENTS.md"):
            self.assertIn("G-D-EXTREF-20260915", read(path), f"{path.name} must cite G-D-EXTREF-20260915")


if __name__ == "__main__":
    unittest.main()
