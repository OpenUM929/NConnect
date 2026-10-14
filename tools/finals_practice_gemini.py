"""Gemini target selector for the unofficial H1 finals practice arena.

The selector makes one request per :meth:`GeminiSelector.select` call and
never falls back to a rules-based choice.  Network use occurs only when a
caller invokes ``select`` (or explicitly runs the CLI with ``--probe``).
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from finals_practice_core import GRID_SIZE, astar_path, generate_map, path_cost


DEFAULT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_KEY_FILE = Path(__file__).resolve().parents[1] / "workspace" / "examples" / "19" / "practice_key.bin"
_KEY_SALT = b"NCRC2026-practice-v1"
_MODEL_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class GeminiSelectorError(RuntimeError):
    """A safe-to-report Gemini selection failure."""


class GeminiResponseError(GeminiSelectorError):
    """Gemini returned data that cannot select a supplied reachable target."""


def load_gemini_key(key_file: str | Path | None = None) -> str:
    """Load the lecture key from the environment, then its XOR/base64 file."""

    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    path = Path(key_file) if key_file is not None else DEFAULT_KEY_FILE
    if not path.is_file():
        return ""
    try:
        blob = base64.b64decode(path.read_bytes())
        return bytes(value ^ _KEY_SALT[i % len(_KEY_SALT)] for i, value in enumerate(blob)).decode("utf-8").strip()
    except (OSError, ValueError, UnicodeError):
        return ""


def _sanitize(value: object, secret: str = "", limit: int = 500) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    if secret:
        text = text.replace(secret, "[REDACTED]")
    return text[:limit]


def _extract_response_text(payload: Mapping) -> str:
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiResponseError("Gemini response is missing candidates[0].content.parts[0].text") from exc
    if not isinstance(text, str) or not text.strip():
        raise GeminiResponseError("Gemini response text is empty")
    return text.strip()


Transport = Callable[[str, Mapping[str, str], bytes, float], tuple[int, bytes]]


def build_tactical_context(
    arena: Mapping,
    position: Sequence[float],
    opponent_history: Sequence[Mapping[str, float]],
    collected_ids: Iterable[str] = (),
    *,
    speed: float = 0.6,
    current_target: str | None = None,
) -> dict:
    """Build public, observation-only context for competitive target choice.

    The map snapshot and all cube positions are assumed fully visible in this
    practice environment. ETAs use constant ``speed`` and ignore turns. The
    opponent heading is an observation, not a claim about intent or a target.
    """

    if not math.isfinite(float(speed)) or speed <= 0:
        raise ValueError("speed must be a positive finite number")
    if len(position) < 2 or not all(math.isfinite(float(value)) for value in position[:2]):
        raise ValueError("position must contain two finite coordinates")

    claimed = {str(cube_id) for cube_id in collected_ids}
    cubes = [cube for cube in arena["cubes"] if str(cube["id"]) not in claimed]
    cube_by_id = {str(cube["id"]): cube for cube in cubes}

    observations = []
    for item in opponent_history:
        try:
            sample = {key: float(item[key]) for key in ("time_s", "x", "y")}
        except (KeyError, TypeError, ValueError):
            continue
        if all(math.isfinite(value) for value in sample.values()):
            observations.append(sample)
    observations.sort(key=lambda item: item["time_s"])

    motion: dict[str, object] = {"status": "unknown"}
    opponent_position: tuple[float, float] | None = None
    if observations:
        opponent_position = (observations[-1]["x"], observations[-1]["y"])
    if len(observations) >= 2:
        first, last = observations[0], observations[-1]
        dt = last["time_s"] - first["time_s"]
        dx, dy = last["x"] - first["x"], last["y"] - first["y"]
        distance = math.hypot(dx, dy)
        if dt > 0 and distance > 1e-6:
            motion = {
                "status": "observed_moving",
                "window_s": round(dt, 3),
                "observed_speed_mps": round(distance / dt, 3),
                "direction_unit": [round(dx / distance, 6), round(dy / distance, 6)],
            }

    def route(start: Sequence[float], cube: Mapping) -> tuple[float, float] | None:
        path = astar_path(arena, start, (cube["x"], cube["y"]), capabilities=())
        if not path:
            return None
        distance = path_cost(path)
        return round(distance, 3), round(distance / speed, 3)

    self_candidates = []
    opponent_candidates = []
    for cube in cubes:
        own_route = route(position, cube)
        if own_route is not None:
            self_candidates.append({"id": str(cube["id"]), "distance_m": own_route[0], "eta_s": own_route[1]})
        if opponent_position is None:
            continue
        opponent_route = route(opponent_position, cube)
        if opponent_route is None:
            continue
        candidate = {
            "id": str(cube["id"]),
            "distance_m": opponent_route[0],
            "eta_s": opponent_route[1],
            "direction_alignment": None,
        }
        if motion["status"] == "observed_moving":
            tx, ty = float(cube["x"]) - opponent_position[0], float(cube["y"]) - opponent_position[1]
            magnitude = math.hypot(tx, ty)
            if magnitude > 1e-6:
                unit = motion["direction_unit"]
                candidate["direction_alignment"] = round((tx / magnitude) * unit[0] + (ty / magnitude) * unit[1], 6)
        opponent_candidates.append(candidate)

    pair_cache: dict[tuple[str, str], tuple[float, float] | None] = {}
    two_target_routes = []
    reachable_ids = {candidate["id"] for candidate in self_candidates}
    for first_id in sorted(reachable_ids):
        first = cube_by_id[first_id]
        for second_id in sorted(reachable_ids - {first_id}):
            key = (first_id, second_id)
            if key not in pair_cache:
                pair_cache[key] = route((first["x"], first["y"]), cube_by_id[second_id])
            pair_route = pair_cache[key]
            if pair_route is not None:
                two_target_routes.append({
                    "first_id": first_id,
                    "second_id": second_id,
                    "between_distance_m": pair_route[0],
                    "between_eta_s": pair_route[1],
                })

    return {
        "assumptions": {
            "map_snapshot": "full_visibility_practice_assumption",
            "eta_model": f"constant_{float(speed):g}_mps_ignores_turns",
            "opponent_motion": "derived_from_observed_positions_only; intent_and_target_unknown",
        },
        "claimed_ids": sorted(claimed),
        "self": {
            "position": [round(float(position[0]), 3), round(float(position[1]), 3)],
            "current_target": current_target,
            "candidates": self_candidates,
        },
        "opponent": {
            "observed_history": observations,
            "latest_position": ([round(opponent_position[0], 3), round(opponent_position[1], 3)]
                                if opponent_position is not None else None),
            "motion": motion,
            "candidates": opponent_candidates,
        },
        "two_target_routes": two_target_routes,
    }


class GeminiSelector:
    """Ask Gemini to choose one currently reachable cube from explicit options."""

    def __init__(
        self,
        strategy_text: str,
        model: str = DEFAULT_MODEL,
        *,
        api_key: str | None = None,
        key_file: str | Path | None = None,
        timeout_s: float = 30.0,
        transport: Transport | None = None,
    ):
        if not isinstance(strategy_text, str) or not strategy_text.strip():
            raise ValueError("strategy_text must be a non-empty string")
        if len(strategy_text) > 300:
            raise ValueError("strategy_text must be at most 300 characters")
        if not isinstance(model, str) or not _MODEL_RE.fullmatch(model):
            raise ValueError("model contains unsupported characters")
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        self.strategy_text = strategy_text.strip()
        self.model = model
        self.api_key = api_key.strip() if api_key is not None else load_gemini_key(key_file)
        self.timeout_s = float(timeout_s)
        self._transport = transport or self._urllib_transport

    @property
    def url(self) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    @staticmethod
    def _urllib_transport(url: str, headers: Mapping[str, str], body: bytes, timeout_s: float) -> tuple[int, bytes]:
        request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return int(response.status), response.read()

    @staticmethod
    def _route_risk(arena: Mapping, path: Sequence[Sequence[float]]) -> float:
        grid = float(arena.get("grid_size", GRID_SIZE))
        cells = 0
        for point in path:
            if any(
                obstacle["kind"] == "car_track"
                and abs(point[0] - obstacle["cx"]) <= obstacle["sx"] / 2
                and abs(point[1] - obstacle["cy"]) <= obstacle["sy"] / 2
                for obstacle in arena["obstacles"]
            ):
                cells += 1
        return round(cells * grid, 3)

    def _reachable_options(self, arena: Mapping, position: Sequence[float], collected_ids: Iterable[str]) -> list[dict]:
        collected = set(collected_ids)
        options = []
        for cube in arena["cubes"]:
            if cube["id"] in collected:
                continue
            # Empty capabilities intentionally model the flat-safe H1 profile.
            path = astar_path(arena, position, (cube["x"], cube["y"]), capabilities=())
            if not path:
                continue
            options.append({
                "id": cube["id"],
                "zone": cube["zone"],
                "value": int(cube["value"]),
                "distance_m": round(path_cost(path), 3),
                "route_risk_m": self._route_risk(arena, path),
                "path": path,
                "cube": cube,
            })
        return options

    def _prompt(
        self,
        options: Sequence[Mapping],
        elapsed_s: float | None,
        remaining_s: float | None,
        tactical_context: Mapping | None = None,
    ) -> str:
        public_options = [
            {key: option[key] for key in ("id", "zone", "value", "distance_m", "route_risk_m")}
            for option in options
        ]
        timing = {}
        if elapsed_s is not None:
            timing["elapsed_s"] = round(float(elapsed_s), 3)
        if remaining_s is not None:
            timing["remaining_s"] = round(float(remaining_s), 3)
        tactical = ""
        if tactical_context is not None:
            tactical = (
                "\ntactical_context: "
                + json.dumps(dict(tactical_context), ensure_ascii=False, separators=(",", ":"))
            )
        return (
            f"너는 {getattr(self, 'robot_description', '2족보행 H1')} 로봇의 다음 큐브 목표만 선택한다. 사용자의 300자 전략을 따르되 "
            "목록에 있는 도달 가능 ID 하나만 고른다. 거리, 점수, 차량 경로 위험, 남은 시간을 고려한다. "
            "반드시 {\"target_id\":\"ID\"} 형식의 JSON 객체만 답하라.\n"
            f"전략: {self.strategy_text}\n"
            f"시간: {json.dumps(timing, ensure_ascii=False, separators=(',', ':'))}\n"
            f"도달 가능 선택지: {json.dumps(public_options, ensure_ascii=False, separators=(',', ':'))}"
            f"{tactical}"
        )

    def select(
        self,
        arena: Mapping,
        position: Sequence[float],
        collected_ids: Iterable[str] = (),
        *,
        elapsed_s: float | None = None,
        remaining_s: float | None = None,
        tactical_context: Mapping | None = None,
    ) -> dict:
        """Return a core-compatible choice plus sanitized request evidence."""

        if not self.api_key:
            raise GeminiSelectorError("Gemini API key was not found")
        if elapsed_s is not None and remaining_s is None:
            remaining_s = max(0.0, float(arena.get("rules", {}).get("duration_s", 180)) - float(elapsed_s))
        options = self._reachable_options(arena, position, collected_ids)
        if not options:
            raise GeminiSelectorError("no reachable uncollected cubes were supplied")
        if tactical_context is not None and not isinstance(tactical_context, Mapping):
            raise ValueError("tactical_context must be a mapping or None")
        prompt = self._prompt(options, elapsed_s, remaining_s, tactical_context)
        request_payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
        started = time.perf_counter()
        try:
            status, raw_body = self._transport(
                self.url,
                {"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                body,
                self.timeout_s,
            )
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read(2048).decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            raise GeminiSelectorError(
                f"Gemini HTTP error {exc.code}: {_sanitize(detail, self.api_key)}"
            ) from None
        except Exception as exc:
            raise GeminiSelectorError(
                f"Gemini request failed ({type(exc).__name__}): {_sanitize(exc, self.api_key)}"
            ) from None
        latency = time.perf_counter() - started
        if not 200 <= int(status) < 300:
            raise GeminiSelectorError(
                f"Gemini HTTP status {status}: {_sanitize(raw_body.decode('utf-8', errors='replace'), self.api_key)}"
            )
        try:
            envelope = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GeminiResponseError(f"Gemini envelope is not valid JSON: {type(exc).__name__}") from None
        response_text = _extract_response_text(envelope)
        try:
            decision = json.loads(response_text)
        except json.JSONDecodeError:
            raise GeminiResponseError("Gemini decision text is not a valid JSON object") from None
        if not isinstance(decision, dict) or set(decision) != {"target_id"} or not isinstance(decision["target_id"], str):
            raise GeminiResponseError("Gemini decision must contain only a string target_id")
        target_id = decision["target_id"]
        by_id = {option["id"]: option for option in options}
        if target_id not in by_id:
            all_ids = {str(cube["id"]) for cube in arena["cubes"]}
            if target_id in all_ids:
                raise GeminiResponseError(f"Gemini selected unreachable target_id: {target_id}")
            raise GeminiResponseError(f"Gemini selected unknown target_id: {_sanitize(target_id)}")
        selected = by_id[target_id]
        return {
            "target": dict(selected["cube"]),
            "path": selected["path"],
            "path_cost": selected["distance_m"],
            "strategy": "gemini_prompt",
            "latency_s": round(latency, 6),
            "model": self.model,
            "request": {"prompt": prompt, "reachable_ids": [option["id"] for option in options]},
            "response": {"target_id": target_id, "text": _sanitize(response_text, self.api_key, 4000)},
            "http_status": int(status),
        }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one explicit Gemini target-selection probe")
    parser.add_argument("--probe", action="store_true", help="make exactly one live generateContent request")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strategy-text", default="가까운 평지 큐브를 우선하고 차량 경로 위험이 낮은 목표를 선택해.")
    parser.add_argument("--map-seed", type=int, default=42)
    parser.add_argument("--position", nargs=2, type=float, default=(-10.0, -8.0), metavar=("X", "Y"))
    parser.add_argument("--collected", default="", help="comma-separated cube IDs")
    parser.add_argument("--elapsed", type=float, default=0.0)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if not args.probe:
        output.write_text(json.dumps({"ok": False, "request_sent": False, "error": "--probe is required"}, indent=2), encoding="utf-8")
        return 2
    selector = None
    try:
        selector = GeminiSelector(args.strategy_text)
        result = selector.select(
            generate_map(args.map_seed),
            args.position,
            [item.strip() for item in args.collected.split(",") if item.strip()],
            elapsed_s=args.elapsed,
        )
        document = {"ok": True, "request_sent": True, "result": result}
        exit_code = 0
    except Exception as exc:
        secret = selector.api_key if selector is not None else load_gemini_key()
        document = {"ok": False, "request_sent": selector is not None, "error": _sanitize(exc, secret)}
        exit_code = 1
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
