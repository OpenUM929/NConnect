from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import go2_stall_diagnostics as stall


HEADER = [
    "step", "time_s", "env_id", "cmd_vx", "cmd_vy", "actual_vx", "actual_vy",
    "root_x", "root_y", "root_z", "terrain_z", "terminated", "truncated",
]


def row(step: int, env_id: int, *, vx: float = 0.0, root_x: float = 0.0,
        root_z: float = 0.0, cmd_vx: float = 0.5) -> dict[str, object]:
    return {
        "step": step, "time_s": step * 0.1, "env_id": env_id,
        "cmd_vx": cmd_vx, "cmd_vy": 0.0, "actual_vx": vx, "actual_vy": 0.0,
        "root_x": root_x, "root_y": 0.0, "root_z": root_z,
        "terrain_z": -0.1, "terminated": 0, "truncated": 0,
    }


def write_steps(path: Path, rows: list[dict[str, object]], num_envs: int = 32) -> None:
    path.parent.mkdir(parents=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (path.parent / "metadata.json").write_text(
        json.dumps({"case_id": path.parent.name, "evaluation_seed": "101", "num_envs": num_envs}),
        encoding="utf-8",
    )


class StallDiagnosticsContract(unittest.TestCase):
    def test_partial_coverage_fails_closed_but_keeps_each_valid_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            steps = Path(tmp) / "stairs_10_down" / "steps.csv"
            rows: list[dict[str, object]] = []
            for env_id in range(31):  # env 31 is deliberately absent
                for step in range(1, 72):
                    rows.append(row(
                        step, env_id, vx=0.0,
                        root_x=1.1 if step >= 60 else 0.0,
                        root_z=0.11 if env_id == 0 and step >= 60 else 0.0,
                        cmd_vx=0.0 if env_id == 1 else 0.5,
                    ))
            write_steps(steps, rows)

            reading = stall.case_reading(steps, "stairs_10_down")

            self.assertFalse(reading["coverage_complete"])
            self.assertEqual(reading["expected_robots"], 32)
            self.assertEqual(reading["robots"], 31)
            self.assertEqual(reading["valid_robots"], 30)
            self.assertEqual(reading["missing_robots"], 2)  # one absent, one null stall denominator
            self.assertIn("expected 32", reading["reason"])
            self.assertIsNotNone(reading["stall_share"])

            envs = {item["env_id"]: item for item in reading["environment_readings"]}
            self.assertEqual(len(envs), 32)
            self.assertIsNotNone(envs["0"]["first_step_time_s"])
            self.assertFalse(envs["0"]["censored"])
            self.assertIsNone(envs["2"]["first_step_time_s"])
            self.assertTrue(envs["2"]["censored"])
            self.assertIsNone(envs["1"]["stall_share"])
            self.assertIn("command", envs["1"]["reason"])
            self.assertIsNone(envs["31"]["first_step_time_s"])
            self.assertIsNone(envs["31"]["censored"])
            self.assertEqual(envs["31"]["reason"], "environment absent from steps.csv")

    def test_complete_coverage_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            steps = Path(tmp) / "stairs_10_down" / "steps.csv"
            rows = [row(step, env_id, vx=0.1) for env_id in range(32) for step in range(1, 22)]
            write_steps(steps, rows)
            reading = stall.case_reading(steps, "stairs_10_down")
            self.assertTrue(reading["coverage_complete"])
            self.assertEqual(reading["reason"], "")
            self.assertEqual(reading["valid_robots"], 32)
            self.assertEqual(reading["missing_robots"], 0)

    def test_provenance_reads_identity_and_pin_sources_without_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            arm = root / "evaluation" / "candidate"
            arm.mkdir(parents=True)
            (arm / "identity.json").write_text(json.dumps({
                "model_sha256": "model", "evaluator_sha256": "evaluator",
                "registry_sha256": "registry",
            }), encoding="utf-8")
            (root / "RUNNER_STATUS.txt").write_text(
                "RUN_ID=run-42\nTRAIN_SEED=42\nCANDIDATE_EVAL_ITER=900\nEVALUATOR=posture_gate_v2\n",
                encoding="utf-8",
            )
            (root / "meta").mkdir()
            (root / "meta" / "experiment.json").write_text(json.dumps({
                "run_id": "run-42", "training": {"seed": 42},
                "evaluation": {"checkpoint_iter": 900},
            }), encoding="utf-8")
            for seed in ("101", "202"):
                case = arm / "cases" / f"seed_{seed}" / "stairs_10_down"
                case.mkdir(parents=True)
                (case / "metadata.json").write_text(
                    json.dumps({"evaluation_seed": seed, "num_envs": 32}), encoding="utf-8"
                )

            provenance = stall.arm_provenance(arm, evaluation_seeds=("101", "202"))
            self.assertEqual(provenance["run_id"], "run-42")
            self.assertEqual(provenance["model_sha256"], "model")
            self.assertEqual(provenance["checkpoint_iter"], 900)
            self.assertEqual(provenance["evaluator"], "posture_gate_v2")
            self.assertEqual(provenance["evaluator_sha256"], "evaluator")
            self.assertEqual(provenance["registry_sha256"], "registry")
            self.assertEqual(provenance["training_seed"], 42)
            self.assertEqual(provenance["evaluation_seeds"], ["101", "202"])
            self.assertTrue(provenance["provenance_complete"])

            missing = stall.arm_provenance(root / "evaluation" / "missing", evaluation_seeds=("101",))
            self.assertIsNone(missing["model_sha256"])
            self.assertFalse(missing["provenance_complete"])
            self.assertIn("model_sha256", missing["reason"])

    def test_writer_emits_case_env_and_provenance_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            rows = [{
                "arm": "candidate", "case": "stairs_10_down", "seed": "101",
                "robots": 0, "expected_robots": 32, "valid_robots": 0,
                "missing_robots": 32, "coverage_complete": False,
                "environment_readings": [], "reason": "steps.csv absent",
            }]
            stall.write_outputs(rows, out, {"schema_version": stall.SCHEMA_VERSION})
            self.assertTrue((out / "STALL_DIAGNOSTICS.csv").is_file())
            self.assertTrue((out / "STALL_DIAGNOSTICS_ENV.csv").is_file())
            sidecar = json.loads((out / "STALL_DIAGNOSTICS_PROVENANCE.json").read_text(encoding="utf-8"))
            self.assertEqual(sidecar["schema_version"], stall.SCHEMA_VERSION)
            self.assertEqual(sidecar["specification"]["coordinate_frame"], "body frame")
            self.assertEqual(sidecar["specification"]["window"]["initial_grace_s"], 0.5)


if __name__ == "__main__":
    unittest.main()
