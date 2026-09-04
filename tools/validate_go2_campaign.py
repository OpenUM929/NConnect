"""Validate the static Go2 campaign contract without third-party dependencies."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "workspace/training/quadruped/config/go2_self_eval_registry.json"

EXPECTED_IDS = [f"G{i}" for i in range(1, 8)]
EXPECTED_WEIGHTS = [0.15, 0.15, 0.20, 0.15, 0.15, 0.10, 0.10]
EXPECTED_MODEL_SHA = "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d"
EXPECTED_ENV_SHA = "f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d"

REQUIRED_FILES = [
    ROOT / "GO2_PROJECT_STATE.md",
    ROOT / "GO2_CAMPAIGN_SCHEDULE.md",
    ROOT / "GO2_REWARD_EVIDENCE_MASTER.md",
    ROOT / "workspace/training/quadruped/AGENTS.md",
    ROOT / ".codex/agents/go2-campaign-manager.md",
    ROOT / ".codex/agents/go2-test-planner.md",
    ROOT / ".codex/agents/go2-report-writer.md",
    ROOT / ".codex/agents/go2-evaluation-auditor.md",
    ROOT / "workspace/training/quadruped/reports/GO2_EVALUATION_PROTOCOL.md",
    ROOT / "workspace/training/quadruped/reports/NEW_SESSION_HANDOFF.md",
    ROOT / "workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md",
    ROOT / ".omx/plans/go2-default-baseline-experiment-plan.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.is_file()]
    assert not missing, f"missing required files: {missing}"

    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    ids = [scenario["id"] for scenario in scenarios]
    weights = [scenario["weight"] for scenario in scenarios]
    assert ids == EXPECTED_IDS, f"scenario ids mismatch: {ids}"
    assert weights == EXPECTED_WEIGHTS, f"scenario weights mismatch: {weights}"
    assert math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-12)
    assert all(scenario["required_video"] for scenario in scenarios)

    submission = data["submission"]
    assert submission["required_uploads"] == ["policy.pt", "env.yaml"]
    assert submission["technical_report"]["minimum_characters"] == 30
    assert submission["technical_report"]["maximum_characters"] == 200
    assert "any team member" in submission["team_permissions"]
    assert submission["edit_window"] == "submission can be modified until judging starts"
    assert submission["judging_started_state"] == "UNMEASURED"
    assert data["legacy_invalid_runner"].endswith("server_run_Go2_videos.sh")

    project_state = (ROOT / "GO2_PROJECT_STATE.md").read_text(encoding="utf-8")
    schedule = (ROOT / "GO2_CAMPAIGN_SCHEDULE.md").read_text(encoding="utf-8")
    reward_master = (ROOT / "GO2_REWARD_EVIDENCE_MASTER.md").read_text(encoding="utf-8")
    test_prd = (
        ROOT / "workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md"
    ).read_text(encoding="utf-8")
    detailed_plan = (ROOT / ".omx/plans/go2-default-baseline-experiment-plan.md").read_text(
        encoding="utf-8"
    )
    for label, text in {
        "project state": project_state,
        "schedule": schedule,
        "reward master": reward_master,
        "test PRD": test_prd,
        "detailed plan": detailed_plan,
    }.items():
        assert "Default-01" in text, f"{label} missing Default-01 contract"
    assert "G-D09" in project_state and "G-D10" in project_state
    assert "조건부가 아니라" in schedule
    assert "Train/mean_reward" in test_prd
    assert "정책당 69" in detailed_plan
    assert "## 10. 살아있는 PRD 운영 계약" in test_prd
    assert "PRD_CHANGE=NONE|UPDATED" in detailed_plan
    for agent_name in ["go2-campaign-manager.md", "go2-test-planner.md"]:
        agent_text = (ROOT / ".codex/agents" / agent_name).read_text(encoding="utf-8")
        assert "GO2_DEFAULT_BASELINE_TEST_PRD.md" in agent_text
        assert "PRD_CHANGE=NONE|UPDATED" in agent_text
        assert "LEDGER_SYNC=PASS|FAIL" in agent_text

    model = ROOT / "workspace/training/quadruped/exported/model_best.pt"
    env = ROOT / "workspace/training/quadruped/exported/env.yaml"
    assert sha256(model) == EXPECTED_MODEL_SHA, "Pilot-01 model hash drift"
    assert sha256(env) == EXPECTED_ENV_SHA, "Pilot-01 env hash drift"

    print("GO2_CAMPAIGN_CONTRACT_OK")
    print(f"registry={REGISTRY.relative_to(ROOT)}")
    print(f"scenarios={len(scenarios)} weight_sum={sum(weights):.2f}")
    print(f"model_sha256={EXPECTED_MODEL_SHA}")
    print(f"env_sha256={EXPECTED_ENV_SHA}")


if __name__ == "__main__":
    main()
