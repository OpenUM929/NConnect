"""Creates a valid example log; replace synthetic samples with Isaac callbacks."""
import json
import os
import tempfile
from pathlib import Path
from telemetry import TelemetryRecorder, evaluate_phase, export_artifacts

ROOT = Path(__file__).parent
PLAN = json.loads((ROOT / "config" / "motion_plan.json").read_text(encoding="utf-8"))

def observation(distance, roll=1.0, pitch=1.5, height=0.29):
    return {"pose": {"position_m": [0, 0, height], "rpy_deg": [roll, pitch, 0]},
            "velocity": {"linear_mps": [0.3, 0, 0], "angular_rps": [0, 0, 0]},
            "command": {"linear_mps": [0.3, 0, 0], "yaw_rate_rps": 0, "source": "motion_plan"},
            "target": {"distance_m": distance, "heading_error_deg": 0, "altitude_error_m": 0},
            "stability": {"base_height_m": height, "is_upright": True, "contact_count": 4}, "extra": {"terrain": "flat"}}

if __name__ == "__main__":
    # The output is configurable for read-only source checkouts.
    output = Path(os.environ.get("ROBOT_TELEMETRY_OUTPUT", Path(tempfile.gettempdir()) / "robot_telemetry_demo"))
    log = output / "demo.jsonl"
    if log.exists(): log.unlink()
    recorder = TelemetryRecorder(log, PLAN["robot_model"], {"policy_path": "example_policy.pt", "map": "demo_flat_ramp", "plan": PLAN})
    for trial, phase in enumerate(PLAN["phases"][:2], 1):
        recorder.start_phase(phase["name"], trial, difficulty=phase["difficulty"], config=phase, expected=phase["expected"])
        samples = [observation(distance) for distance in ((2.0, 1.0, 0.2) if phase["name"] == "forward" else (0.0, 0.0, 0.0))]
        for item in samples: recorder.sample(phase["name"], trial, item)
        verdict = evaluate_phase(samples, [], phase["pass"], PLAN["safety"])
        recorder.complete_phase(phase["name"], trial, predicted=phase["expected"], actual="Stable and completed target.", **verdict)
    recorder.complete_run(passed=True, summary={"completed_phases": 2})
    print(export_artifacts(log, output / "demo_report"))
