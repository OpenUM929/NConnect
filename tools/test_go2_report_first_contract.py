"""Regression checks for the report-first instructions and research decision."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.update_go2_report_first_contract import (
    END, PLAN, ROLE_DUTIES, ROOT, START, append_block,
)


class ReportFirstContractTest(unittest.TestCase):
    def test_guidance_has_identity_and_missing_gates(self):
        for name in ("AGENTS.md", "workspace/training/quadruped/AGENTS.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            for required in ("READ_MATCHED", "READ_UNMATCHED", "MISSING",
                             "REPORT_REQUIRED_NOT_ACQUIRED", "SELF_EVAL_REPORT"):
                self.assertIn(required, text, name)

    def test_all_go2_roles_require_direct_read(self):
        for role in ROLE_DUTIES:
            text = (ROOT / ".codex/agents" / f"{role}.md").read_text(encoding="utf-8")
            block = text.split(START)[1].split(END)[0]
            for required in ("report.html", "REPORT_READ_STATUS", "DEFERRED_HYPOTHESIS"):
                self.assertIn(required, block, role)

    def test_ledgers_and_plan_share_decision(self):
        for name in ("GO2_PROJECT_STATE.md", "GO2_CAMPAIGN_SCHEDULE.md",
                     "GO2_REWARD_EVIDENCE_MASTER.md", "ARTIFACT_MANAGEMENT.md", PLAN,
                     "workspace/training/quadruped/upload/plan/PLANNER_BRIEF.md",
                     "workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("G-D-REPORT-FIRST-20260913", text, name)
            self.assertIn("DEFERRED_HYPOTHESIS", text, name)

    def test_spec_does_not_authorize_training(self):
        data = json.loads((ROOT / PLAN).with_suffix(".json").read_text(encoding="utf-8"))
        self.assertFalse(data["training_authorized"])
        self.assertFalse(data["package_ready"])
        self.assertEqual(data["cases_status"], "PROPOSED_NOT_FROZEN")
        self.assertEqual(data["report_gate"], {"a017": "MISSING", "pilot": "READ_UNMATCHED"})

    def test_report_is_not_a_replacement_for_raw_evidence(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("원 학습 로그 생략 허가가 아니다", text)
        review = ROOT / "workspace/training/quadruped/upload/plan/GO2_EVIDENCE_NECESSITY_REVIEW_20260913.md"
        self.assertIn("무조건 전량 재측정하지 않는다", review.read_text(encoding="utf-8"))

    def test_plan_directory_excludes_upload_packages(self):
        plan = ROOT / "workspace/training/quadruped/upload/plan"
        forbidden = (".zip", ".tar", ".tar.gz", ".sha256", ".sh", ".bat", ".ps1")
        misplaced = [str(p.relative_to(plan)) for p in plan.rglob("*")
                     if p.is_file() and p.name.lower().endswith(forbidden)]
        self.assertEqual(misplaced, [], "Upload packages must not be stored in plan/")
        for name in ("AGENTS.md", "workspace/training/quadruped/AGENTS.md"):
            self.assertIn("경로", (ROOT / name).read_text(encoding="utf-8"))

    def test_review_bundle_has_campaign_number(self):
        import hashlib
        upload = ROOT / "workspace/training/quadruped/upload"
        self.assertEqual(list(upload.glob("*.zip")), [])
        bundle = upload / "G-A028/review/GO2_G_A028_TUNING_REVIEW_MATERIALS_20260913.zip"
        sha, filename = bundle.with_suffix(".zip.sha256").read_text().split()
        self.assertEqual(filename, bundle.name)
        self.assertEqual(sha, hashlib.sha256(bundle.read_bytes()).hexdigest())

    def test_updater_preserves_history_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "doc.md"
            path.write_text("historical evidence\n", encoding="utf-8")
            append_block(path, "first")
            append_block(path, "second")
            expected = path.read_bytes()
            append_block(path, "second")
            self.assertEqual(expected, path.read_bytes())
            self.assertTrue(path.read_text().startswith("historical evidence\n"))
            self.assertEqual(path.read_text().count(START), 1)


if __name__ == "__main__":
    unittest.main()
