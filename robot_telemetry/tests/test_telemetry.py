import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from telemetry import TelemetryRecorder, evaluate_phase, export_artifacts, read_events

def sample(distance=1.0):
    return {"pose":{"position_m":[0,0,.3],"rpy_deg":[1,2,0]},"velocity":{"linear_mps":[.2,0,0],"angular_rps":[0,0,0]},"command":{"linear_mps":[.2,0,0],"yaw_rate_rps":0,"source":"test"},"target":{"distance_m":distance,"heading_error_deg":0,"altitude_error_m":0},"stability":{"base_height_m":.3,"is_upright":True,"contact_count":4}}

class TelemetryTest(unittest.TestCase):
    def test_export_preserves_progress_and_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "run.jsonl"; r = TelemetryRecorder(log, "Go2", {})
            r.start_phase("forward", 1, difficulty=2, config={}, expected="reach target")
            r.sample("forward", 1, sample(2)); r.sample("forward", 1, sample(.2))
            r.complete_phase("forward", 1, predicted="reach target", actual="reached", passed=True, reason="pass", metrics={})
            r.complete_run(passed=True, summary={})
            rows = export_artifacts(log, Path(tmp) / "report")
            self.assertEqual(len(read_events(log)), 6); self.assertAlmostEqual(rows[0]["distance_progress_m"], 1.8); self.assertTrue(rows[0]["passed"])
    def test_missing_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = TelemetryRecorder(Path(tmp) / "run.jsonl", "Go2", {})
            bad = sample(); del bad["target"]["distance_m"]
            with self.assertRaises(ValueError): r.sample("stand", 1, bad)
    def test_hill_gate_requires_altitude_gain(self):
        verdict = evaluate_phase([sample(.2), sample(.1)], [], {"max_distance_m": .3, "min_altitude_gain_m": .4}, {"min_base_height_m": .18, "max_abs_roll_pitch_deg": 35})
        self.assertFalse(verdict["passed"]); self.assertEqual(verdict["reason"], "insufficient_altitude_gain")

if __name__ == "__main__": unittest.main()
