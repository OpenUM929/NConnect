"""Wiring checks only; these do not prove scientific correctness."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "workspace/training/quadruped/GO2_EVIDENCE_HANDOFF.md"


class EvidenceRoleContract(unittest.TestCase):
    def test_monitoring_is_required_at_each_semantic_boundary(self):
        text = (ROOT / CONTRACT).read_text(encoding="utf-8")
        for field in ("INPUT_REVIEW", "OUTPUT_REVIEW", "PM_REVIEW",
                      "handoff_id", "evidence_revision", "claim_revision",
                      "reviewed_revision", "ACCEPT_LIMITED", "REJECT", "UNKNOWN",
                      "REUSE_UNCHANGED", "MANUAL_PM_DISPATCH", "감사 독립성"):
            self.assertIn(field, text, field)
        guidance = (ROOT / "workspace/training/quadruped/AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("INPUT_REVIEW", guidance)
        self.assertIn("PM_REVIEW", guidance)

    def test_role_surfaces_share_contract_and_read_only_boundary(self):
        for surface in (".codex", ".claude"):
            text = (ROOT / surface / "agents/go2-evidence-manager.md").read_text(encoding="utf-8")
            self.assertIn(CONTRACT, text)
            self.assertIn("READ_ONLY", text)

    def test_all_consumers_link_contract(self):
        paths = [f".codex/agents/go2-{role}.md" for role in
                 ("campaign-manager", "test-planner", "evaluation-auditor", "report-writer")]
        paths += [f".claude/agents/go2-{role}.md" for role in ("analyst", "planner", "auditor")]
        paths += ["workspace/training/quadruped/AGENTS.md"]
        for path in paths:
            self.assertIn(CONTRACT, (ROOT / path).read_text(encoding="utf-8"), path)

    def test_handoff_preserves_measurement_and_document_context(self):
        text = (ROOT / CONTRACT).read_text(encoding="utf-8")
        for field in ("evidence_id", "source_locator", "policy_identity", "evaluator_identity",
                      "population", "seed", "aggregation", "evidence_kind", "document_ref",
                      "formula", "applicability", "counterevidence", "inference", "falsifier",
                      "REPORT_READ_STATUS", "decision_change"):
            self.assertIn(field, text)


if __name__ == "__main__":
    unittest.main()
