"""Deterministic, dependency-free practice core for the 2026 H1 finals.

This module is a planning surrogate, not the organizer's simulator or Gemini
runtime.  Geometry below is an explicit practice assumption derived from the
published zone descriptions; it does not claim to reproduce the official map.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence


MATCH_SECONDS = 180.0
GRID_SIZE = 0.5
WORLD_BOUNDS = {"xmin": -12.0, "xmax": 12.0, "ymin": -10.0, "ymax": 10.0}

_SOLID_KINDS = {"wall", "maze_wall"}
_CAPABILITY_FOR_KIND = {
    "box_hill": "hill",
    "stairs": "stairs",
    "stairs_platform": "stairs",
    "ramp": "ramp",
    "ramp_platform": "ramp",
}
_TERRAIN_COST = {
    "box_hill": 2.8,
    "stairs": 3.5,
    "stairs_platform": 2.0,
    "ramp": 2.2,
    "ramp_platform": 1.7,
    "car_track": 7.0,
}


def _box(cx: float, cy: float, cz: float, sx: float, sy: float, sz: float, kind: str) -> dict:
    return {"cx": cx, "cy": cy, "cz": cz, "sx": sx, "sy": sy, "sz": sz, "kind": kind}


def _cube(cube_id: str, x: float, y: float, z: float, zone: str, value: int = 100) -> dict:
    return {"id": cube_id, "x": x, "y": y, "z": z, "zone": zone, "value": value}


def generate_map(seed: int = 0) -> dict:
    """Return a deterministic JSON-serializable practice arena.

    The seed only jitters safe cube positions by one quarter-grid cell.  Static
    structures remain fixed so results across strategies stay comparable.
    """

    rng = random.Random(seed)

    def jitter(value: float) -> float:
        return round(value + rng.choice((-0.125, 0.0, 0.125)), 3)

    obstacles = [
        # 20 cm thick, 1 m tall assumed arena boundary.
        _box(0, -9.9, 0.5, 24, 0.2, 1.0, "wall"),
        _box(0, 9.9, 0.5, 24, 0.2, 1.0, "wall"),
        _box(-11.9, 0, 0.5, 0.2, 20, 1.0, "wall"),
        _box(11.9, 0, 0.5, 0.2, 20, 1.0, "wall"),
        # Raised practice surfaces. Their footprint is capability-gated by A*.
        _box(-7.0, 5.5, 0.3, 3.0, 3.0, 0.6, "box_hill"),
        _box(-1.0, 7.0, 0.4, 4.0, 2.0, 0.8, "stairs_platform"),
        # Four 30 cm treads rise 20 cm each to the 80 cm platform.
        _box(-1.0, 4.95, 0.1, 1.2, 0.3, 0.2, "stairs"),
        _box(-1.0, 5.25, 0.2, 1.2, 0.3, 0.4, "stairs"),
        _box(-1.0, 5.55, 0.3, 1.2, 0.3, 0.6, "stairs"),
        _box(-1.0, 5.85, 0.4, 1.2, 0.3, 0.8, "stairs"),
        _box(5.5, 6.5, 0.35, 3.0, 2.5, 0.7, "ramp_platform"),
        # Ramp footprint runs north from y=2.75 to the platform's south edge 5.25.
        # Runtime mesh builders interpret this record as a wedge rising to sz.
        _box(5.5, 4.0, 0.35, 1.5, 2.5, 0.7, "ramp"),
        # Southwest maze: 0.25 m thick and 1 m tall assumed walls.
        _box(-10.15, -3.8, 0.5, 0.7, 0.25, 1.0, "maze_wall"),
        _box(-5.9, -3.8, 0.5, 4.8, 0.25, 1.0, "maze_wall"),
        _box(-7.0, 1.8, 0.5, 7.0, 0.25, 1.0, "maze_wall"),
        _box(-10.4, -1.0, 0.5, 0.25, 5.8, 1.0, "maze_wall"),
        _box(-3.6, -1.0, 0.5, 0.25, 5.8, 1.0, "maze_wall"),
        _box(-8.1, -2.0, 0.5, 0.25, 3.6, 1.0, "maze_wall"),
        _box(-5.9, 0.0, 0.5, 0.25, 3.6, 1.0, "maze_wall"),
        # East-side closed vehicle loop, represented as traversable high risk.
        _box(8.1, -5.8, 0.01, 6.0, 0.8, 0.02, "car_track"),
        _box(8.1, 0.2, 0.01, 6.0, 0.8, 0.02, "car_track"),
        _box(5.1, -2.8, 0.01, 0.8, 6.0, 0.02, "car_track"),
        _box(11.1, -2.8, 0.01, 0.8, 6.0, 0.02, "car_track"),
    ]

    cubes = [
        _cube("F01", jitter(-8.8), jitter(-7.6), 0.15, "flat"),
        _cube("F02", jitter(-2.0), jitter(-7.0), 0.15, "flat"),
        _cube("F03", jitter(2.0), jitter(-3.0), 0.15, "flat"),
        _cube("F04", jitter(1.0), jitter(2.0), 0.15, "flat"),
        _cube("F05", jitter(8.2), jitter(2.5), 0.15, "flat"),
        _cube("M01", -6.9, -2.8, 0.15, "maze"),
        _cube("M02", -4.8, 0.8, 0.15, "maze"),
        _cube("H01", -7.0, 5.5, 0.75, "box_hill", 150),
        _cube("S01", -1.0, 7.0, 0.95, "stairs", 100),
        _cube("R01", 5.5, 6.5, 0.85, "ramp", 100),
        _cube("C01", 8.1, -2.8, 0.15, "car_track", 100),
    ]

    return {
        "schema": "nconnect-finals-practice-map-v1",
        "seed": seed,
        "assumptions": {
            "status": "unofficial practice geometry; official regulations define zones but not these dimensions",
            "world_m": [24.0, 20.0],
            "grid_m": GRID_SIZE,
            "robot_clearance_radius_m": 0.35,
            "boundary_wall_m": [0.2, 1.0],
            "box_hill_m": [3.0, 3.0, 0.6],
            "stairs_platform_m": [4.0, 2.0, 0.8],
            "stairs_tread_m": [1.2, 0.3, 0.2],
            "ramp_platform_m": [3.0, 2.5, 0.7],
            "ramp_wedge_m": [1.5, 2.5, 0.7],
            "maze_wall_m": [0.25, 1.0],
            "car_track_width_m": 0.8,
        },
        "rules": {
            "duration_s": 180,
            "ordinary_cube_points": 100,
            "box_hill_cube_points": 150,
            "fall_points": -50,
            "car_collision_points": -30,
            "tie_break_order": ["cube_count", "fewer_falls", "fewer_collisions", "earlier_first_cube", "earlier_last_cube"],
        },
        "bounds": dict(WORLD_BOUNDS),
        "grid_size": GRID_SIZE,
        "starts": {"blue": [-10.0, -8.0, 0.0], "red": [10.0, -8.0, 0.0]},
        "obstacles": obstacles,
        "cubes": cubes,
        "car": {
            "kind": "closed_track",
            "assumed_speed_mps": 1.2,
            "route": [[5.1, -5.8], [11.1, -5.8], [11.1, 0.2], [5.1, 0.2], [5.1, -5.8]],
        },
    }


def _point_in_box(x: float, y: float, box: Mapping[str, float], padding: float = 0.0) -> bool:
    return (abs(x - box["cx"]) <= box["sx"] / 2 + padding and
            abs(y - box["cy"]) <= box["sy"] / 2 + padding)


def _capability_set(capabilities: Mapping[str, bool] | Iterable[str] | None) -> set[str]:
    if capabilities is None:
        return set()
    if isinstance(capabilities, Mapping):
        return {name for name, enabled in capabilities.items() if enabled}
    return set(capabilities)


def _snap(value: float, origin: float, grid: float) -> int:
    return int(round((value - origin) / grid))


def _xy(node: tuple[int, int], bounds: Mapping[str, float], grid: float) -> tuple[float, float]:
    return (round(bounds["xmin"] + node[0] * grid, 6), round(bounds["ymin"] + node[1] * grid, 6))


def astar_path(
    map_data: Mapping,
    start: Sequence[float],
    goal: Sequence[float],
    capabilities: Mapping[str, bool] | Iterable[str] | None = None,
    *,
    robot_radius: float = 0.35,
) -> list[list[float]]:
    """Find a cost-aware four-connected path, or return ``[]`` if unreachable."""

    bounds = map_data["bounds"]
    grid = float(map_data.get("grid_size", GRID_SIZE))
    caps = _capability_set(capabilities)
    width = _snap(bounds["xmax"], bounds["xmin"], grid) + 1
    height = _snap(bounds["ymax"], bounds["ymin"], grid) + 1
    start_node = (_snap(float(start[0]), bounds["xmin"], grid), _snap(float(start[1]), bounds["ymin"], grid))
    goal_node = (_snap(float(goal[0]), bounds["xmin"], grid), _snap(float(goal[1]), bounds["ymin"], grid))

    def cell_cost(node: tuple[int, int]) -> float | None:
        if not (0 <= node[0] < width and 0 <= node[1] < height):
            return None
        x, y = _xy(node, bounds, grid)
        cost = 1.0
        for obstacle in map_data["obstacles"]:
            kind = obstacle["kind"]
            padding = robot_radius if kind in _SOLID_KINDS else 0.0
            if not _point_in_box(x, y, obstacle, padding):
                continue
            if kind in _SOLID_KINDS:
                return None
            required = _CAPABILITY_FOR_KIND.get(kind)
            if required and required not in caps:
                return None
            cost = max(cost, _TERRAIN_COST.get(kind, 1.0))
        return cost

    if cell_cost(start_node) is None or cell_cost(goal_node) is None:
        return []

    frontier: list[tuple[float, float, tuple[int, int]]] = [(0.0, 0.0, start_node)]
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start_node: None}
    best = {start_node: 0.0}
    while frontier:
        _, current_cost, current = heapq.heappop(frontier)
        if current == goal_node:
            break
        if current_cost > best[current] + 1e-12:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (current[0] + dx, current[1] + dy)
            multiplier = cell_cost(nxt)
            if multiplier is None:
                continue
            candidate = current_cost + grid * multiplier
            if candidate >= best.get(nxt, math.inf):
                continue
            best[nxt] = candidate
            came_from[nxt] = current
            heuristic = grid * (abs(nxt[0] - goal_node[0]) + abs(nxt[1] - goal_node[1]))
            heapq.heappush(frontier, (candidate + heuristic, candidate, nxt))

    if goal_node not in came_from:
        return []
    nodes = []
    current = goal_node
    while current is not None:
        nodes.append(current)
        current = came_from[current]
    nodes.reverse()
    return [[x, y] for x, y in (_xy(node, bounds, grid) for node in nodes)]


def path_cost(path: Sequence[Sequence[float]]) -> float:
    return sum(math.dist(a[:2], b[:2]) for a, b in zip(path, path[1:]))


def choose_target(
    map_data: Mapping,
    position: Sequence[float],
    collected_ids: Iterable[str] = (),
    strategy: str = "flat_safe",
    capabilities: Mapping[str, bool] | Iterable[str] | None = None,
) -> dict | None:
    """Select a cube with a deterministic strategy surrogate.

    ``nearest`` minimizes route length, ``flat_safe`` considers only flat/maze
    cubes and penalizes car-track exposure, and ``score_rate`` maximizes points
    per estimated path metre.  These selectors approximate prompt intent; they
    do not execute or emulate natural-language Gemini behavior.
    """

    if strategy not in {"nearest", "flat_safe", "score_rate"}:
        raise ValueError(f"unknown strategy: {strategy}")
    collected = set(collected_ids)
    candidates = []
    for cube in map_data["cubes"]:
        if cube["id"] in collected:
            continue
        if strategy == "flat_safe" and cube["zone"] not in {"flat", "maze"}:
            continue
        path = astar_path(map_data, position, (cube["x"], cube["y"]), capabilities)
        if not path:
            continue
        distance = path_cost(path)
        track_cells = sum(
            any(o["kind"] == "car_track" and _point_in_box(p[0], p[1], o) for o in map_data["obstacles"])
            for p in path
        )
        risk = track_cells * float(map_data.get("grid_size", GRID_SIZE))
        effective = distance + (3.0 * risk if strategy == "flat_safe" else risk)
        if strategy in {"nearest", "flat_safe"}:
            rank = (effective, -cube["value"], cube["id"])
        else:
            rate = cube["value"] / max(effective, 0.25)
            rank = (-rate, effective, cube["id"])
        candidates.append((rank, cube, path, effective))
    if not candidates:
        return None
    _, cube, path, effective = min(candidates, key=lambda item: item[0])
    return {"target": dict(cube), "path": path, "path_cost": round(effective, 6), "strategy": strategy}


def _record_key(record: Mapping) -> tuple:
    first = record.get("first_cube_time")
    last = record.get("last_cube_time")
    return (
        record["score"],
        record["cube_count"],
        -record["falls"],
        -record["collisions"],
        -(math.inf if first is None else first),
        -(math.inf if last is None else last),
    )


def compare_team_records(a: Mapping, b: Mapping) -> int:
    """Return 1 if *a* wins, -1 if *b* wins, or 0 when a replay is needed."""

    ka, kb = _record_key(a), _record_key(b)
    return (ka > kb) - (ka < kb)


@dataclass
class _TeamState:
    cube_ids: list[str] = field(default_factory=list)
    cube_points: int = 0
    falls: int = 0
    collisions: int = 0
    collection_times: list[float] = field(default_factory=list)


class ScoreTracker:
    """Track shared-cube ownership and official scoring within 180 seconds."""

    def __init__(self, map_or_cubes: Mapping | Sequence[Mapping] | None = None):
        if map_or_cubes is None:
            cubes: Sequence[Mapping] = ()
        elif isinstance(map_or_cubes, Mapping):
            cubes = map_or_cubes.get("cubes", ())
        else:
            cubes = map_or_cubes
        self.cube_values = {str(c["id"]): int(c.get("value", 100)) for c in cubes}
        self.teams = {"blue": _TeamState(), "red": _TeamState()}
        self.cube_owner: dict[str, str] = {}
        self.events: list[dict] = []

    @staticmethod
    def _valid_time(time_s: float) -> float:
        value = float(time_s)
        if not 0.0 <= value <= MATCH_SECONDS:
            raise ValueError(f"event time {value} is outside the 0..180 second match")
        return value

    def _team(self, team: str) -> _TeamState:
        if team not in self.teams:
            raise ValueError(f"unknown team: {team}")
        return self.teams[team]

    def collect(self, team: str, cube_id: str, time_s: float, value: int | None = None) -> bool:
        """Award an unowned cube; return False if the opponent already owns it."""

        state = self._team(team)
        timestamp = self._valid_time(time_s)
        cube_id = str(cube_id)
        if cube_id in self.cube_owner:
            return False
        if value is None:
            if self.cube_values and cube_id not in self.cube_values:
                raise KeyError(f"unknown cube: {cube_id}")
            value = self.cube_values.get(cube_id, 100)
        self.cube_owner[cube_id] = team
        state.cube_ids.append(cube_id)
        state.cube_points += int(value)
        state.collection_times.append(timestamp)
        self.events.append({"time_s": timestamp, "team": team, "event": "cube", "cube_id": cube_id, "value": int(value)})
        return True

    def fall(self, team: str, time_s: float) -> None:
        timestamp = self._valid_time(time_s)
        self._team(team).falls += 1
        self.events.append({"time_s": timestamp, "team": team, "event": "fall", "value": -50})

    def collision(self, team: str, time_s: float) -> None:
        timestamp = self._valid_time(time_s)
        self._team(team).collisions += 1
        self.events.append({"time_s": timestamp, "team": team, "event": "car_collision", "value": -30})

    def record(self, team: str) -> dict:
        state = self._team(team)
        return {
            "team": team,
            "score": state.cube_points - 50 * state.falls - 30 * state.collisions,
            "cube_points": state.cube_points,
            "cube_count": len(state.cube_ids),
            "cube_ids": list(state.cube_ids),
            "falls": state.falls,
            "collisions": state.collisions,
            "first_cube_time": min(state.collection_times) if state.collection_times else None,
            "last_cube_time": max(state.collection_times) if state.collection_times else None,
        }

    def result(self) -> dict:
        blue, red = self.record("blue"), self.record("red")
        comparison = compare_team_records(blue, red)
        return {"blue": blue, "red": red, "winner": "blue" if comparison > 0 else "red" if comparison < 0 else None,
                "replay_required": comparison == 0}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an unofficial deterministic H1 finals practice map JSON")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, help="write JSON to this path; stdout when omitted")
    args = parser.parse_args(argv)
    rendered = json.dumps(generate_map(args.seed), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
