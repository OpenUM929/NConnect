"""Pure-Python regression tests for the repaired Go2 evaluator primitives."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


telemetry = load_module("go2_eval_telemetry_v2", GO2 / "go2_eval_telemetry.py")


class Go2EvaluatorV2Contract(unittest.TestCase):
    def test_progress_uses_velocity_not_world_spawn_position(self) -> None:
        # Identical body-frame motion must produce identical progress even if
        # two environments were spawned on different terrain tiles.  World
        # coordinates deliberately are not an input to the v2 calculation.
        first = sum(
            telemetry._projected_displacement(0.4, 0.0, 0.5, 0.0, 0.02)
            for _ in range(100)
        )
        second = sum(
            telemetry._projected_displacement(0.4, 0.0, 0.5, 0.0, 0.02)
            for _ in range(100)
        )
        self.assertAlmostEqual(first, 0.8)
        self.assertEqual(first, second)

    def test_zero_command_has_no_progress_direction(self) -> None:
        self.assertIsNone(
            telemetry._projected_displacement(0.4, 0.0, 0.0, 0.0, 0.02)
        )

    def test_g7_has_explicit_distinct_randomization_switch(self) -> None:
        source = (GO2 / "go2_task" / "env_cfg.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("NCRC_EVAL_DR") == "1"', source)
        self.assertIn('material["static_friction_range"] = (0.6, 1.0)', source)
        self.assertIn('mass_distribution_params"] = (-2.0, 4.0)', source)
        self.assertIn('position_range"] = (0.9, 1.1)', source)


if __name__ == "__main__":
    unittest.main()
