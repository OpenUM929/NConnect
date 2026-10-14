"""Focused tests for the dependency-free finals practice core."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finals_practice_core as core  # noqa: E402


class FinalsPracticeCoreTests(unittest.TestCase):
    def test_map_is_deterministic_json_and_seed_changes_cube_layout(self):
        first = core.generate_map(17)
        second = core.generate_map(17)
        other = core.generate_map(18)
        self.assertEqual(first, second)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertNotEqual(first["cubes"], other["cubes"])
        self.assertEqual(first["bounds"], {"xmin": -12.0, "xmax": 12.0, "ymin": -10.0, "ymax": 10.0})
        self.assertEqual(first["rules"]["duration_s"], 180)
        self.assertEqual({c["value"] for c in first["cubes"] if c["zone"] == "box_hill"}, {150})

    def test_astar_path_maintains_clearance_from_solid_obstacles(self):
        arena = core.generate_map(1)
        path = core.astar_path(arena, arena["starts"]["blue"], (2.0, 2.0))
        self.assertTrue(path)
        solids = [o for o in arena["obstacles"] if o["kind"] in {"wall", "maze_wall"}]
        for x, y in path:
            self.assertTrue(all(not core._point_in_box(x, y, obstacle, 0.35) for obstacle in solids))

    def test_raised_targets_require_declared_capability(self):
        arena = core.generate_map(3)
        hill = next(c for c in arena["cubes"] if c["id"] == "H01")
        start = arena["starts"]["blue"]
        self.assertEqual(core.astar_path(arena, start, (hill["x"], hill["y"])), [])
        self.assertTrue(core.astar_path(arena, start, (hill["x"], hill["y"]), {"hill": True}))

    def test_all_cubes_are_reachable_with_matching_capabilities(self):
        arena = core.generate_map(4)
        capabilities = {"hill", "stairs", "ramp"}
        for cube in arena["cubes"]:
            with self.subTest(cube=cube["id"]):
                self.assertTrue(core.astar_path(arena, arena["starts"]["blue"],
                                                (cube["x"], cube["y"]), capabilities))

    def test_flat_safe_selector_avoids_raised_and_track_targets(self):
        arena = core.generate_map(5)
        choice = core.choose_target(arena, arena["starts"]["blue"], strategy="flat_safe")
        self.assertIsNotNone(choice)
        self.assertIn(choice["target"]["zone"], {"flat", "maze"})
        self.assertNotEqual(choice["target"]["zone"], "car_track")

    def test_shared_cube_timing_and_score_invariants(self):
        tracker = core.ScoreTracker(core.generate_map(0))
        self.assertTrue(tracker.collect("blue", "F01", 4.0))
        self.assertFalse(tracker.collect("red", "F01", 4.1))
        self.assertTrue(tracker.collect("red", "H01", 5.0))
        tracker.fall("red", 20.0)
        tracker.collision("blue", 30.0)
        self.assertEqual(tracker.record("blue")["score"], 70)
        self.assertEqual(tracker.record("red")["score"], 100)
        self.assertEqual(tracker.result()["winner"], "red")
        with self.assertRaises(ValueError):
            tracker.fall("blue", 180.001)
        with self.assertRaises(ValueError):
            tracker.collect("blue", "F02", -0.01)

    def test_tie_break_order_and_replay(self):
        base = {"score": 100, "cube_count": 2, "falls": 2, "collisions": 0,
                "first_cube_time": 10.0, "last_cube_time": 40.0}
        self.assertEqual(core.compare_team_records(base, dict(base, cube_count=1)), 1)
        self.assertEqual(core.compare_team_records(base, dict(base, falls=3)), 1)
        self.assertEqual(core.compare_team_records(base, dict(base, collisions=1)), 1)
        self.assertEqual(core.compare_team_records(base, dict(base, first_cube_time=11.0)), 1)
        self.assertEqual(core.compare_team_records(base, dict(base, last_cube_time=41.0)), 1)
        self.assertEqual(core.compare_team_records(base, dict(base)), 0)

    def test_strategy_selector_is_deterministic_and_skips_collected(self):
        arena = core.generate_map(9)
        first = core.choose_target(arena, arena["starts"]["blue"], strategy="score_rate", capabilities={"hill"})
        repeat = core.choose_target(arena, arena["starts"]["blue"], strategy="score_rate", capabilities={"hill"})
        self.assertEqual(first, repeat)
        second = core.choose_target(arena, arena["starts"]["blue"], [first["target"]["id"]], "score_rate", {"hill"})
        self.assertIsNotNone(second)
        self.assertNotEqual(second["target"]["id"], first["target"]["id"])


if __name__ == "__main__":
    unittest.main()
