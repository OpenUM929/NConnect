"""Mock-only tests for the Gemini finals practice selector."""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finals_practice_core as core  # noqa: E402
import finals_practice_gemini as gemini  # noqa: E402


def response_body(decision_text: str) -> bytes:
    return json.dumps({"candidates": [{"content": {"parts": [{"text": decision_text}]}}]}).encode()


class CaptureTransport:
    def __init__(self, decision_text: str):
        self.decision_text = decision_text
        self.calls = []

    def __call__(self, url, headers, body, timeout):
        self.calls.append((url, headers, json.loads(body), timeout))
        return 200, response_body(self.decision_text)


class GeminiSelectorTests(unittest.TestCase):
    def setUp(self):
        self.arena = core.generate_map(11)
        self.position = self.arena["starts"]["blue"][:2]

    def test_key_loader_matches_lecture_xor_base64(self):
        secret = "lecture-test-key"
        encoded = base64.b64encode(bytes(
            value ^ gemini._KEY_SALT[i % len(gemini._KEY_SALT)]
            for i, value in enumerate(secret.encode())
        ))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "practice_key.bin"
            path.write_bytes(encoded)
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(gemini.load_gemini_key(path), secret)

    def test_valid_selection_uses_required_rest_contract_once(self):
        transport = CaptureTransport('{"target_id":"F01"}')
        selector = gemini.GeminiSelector("평지에서 가까운 큐브 우선", api_key="secret", transport=transport)
        choice = selector.select(self.arena, self.position, elapsed_s=12)
        self.assertEqual(choice["target"]["id"], "F01")
        self.assertEqual(choice["strategy"], "gemini_prompt")
        self.assertEqual(len(transport.calls), 1)
        url, headers, payload, timeout = transport.calls[0]
        self.assertIn("gemini-3.1-flash-lite:generateContent", url)
        self.assertEqual(headers["x-goog-api-key"], "secret")
        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")
        self.assertIn("remaining_s", payload["contents"][0]["parts"][0]["text"])
        self.assertNotIn("secret", choice["request"]["prompt"])

    def test_tactical_context_is_transmitted_without_hidden_target(self):
        transport = CaptureTransport('{"target_id":"F01"}')
        selector = gemini.GeminiSelector("public observations only", api_key="secret", transport=transport)
        context = gemini.build_tactical_context(
            self.arena,
            self.position,
            [{"time_s": 1, "x": 0, "y": -2}, {"time_s": 2, "x": 1, "y": -2}],
            current_target="F01",
        )
        selector.select(self.arena, self.position, tactical_context=context)
        prompt = transport.calls[0][2]["contents"][0]["parts"][0]["text"]
        self.assertIn("tactical_context:", prompt)
        self.assertIn('"current_target":"F01"', prompt)
        self.assertNotIn("opponent_target", prompt)
        self.assertNotIn("hidden_target", prompt)

    def test_opponent_direction_alignment_distinguishes_ahead_and_behind(self):
        context = gemini.build_tactical_context(
            self.arena,
            self.position,
            [{"time_s": 0, "x": 0, "y": -3}, {"time_s": 2, "x": 1, "y": -3}],
        )
        by_id = {item["id"]: item for item in context["opponent"]["candidates"]}
        self.assertGreater(by_id["F03"]["direction_alignment"], 0)
        self.assertLess(by_id["F01"]["direction_alignment"], 0)
        self.assertEqual(context["opponent"]["motion"]["status"], "observed_moving")

    def test_empty_and_stationary_history_leave_motion_unknown(self):
        empty = gemini.build_tactical_context(self.arena, self.position, [])
        stationary = gemini.build_tactical_context(
            self.arena,
            self.position,
            [{"time_s": 0, "x": 2, "y": 2}, {"time_s": 2, "x": 2, "y": 2}],
        )
        self.assertEqual(empty["opponent"]["motion"], {"status": "unknown"})
        self.assertIsNone(empty["opponent"]["latest_position"])
        self.assertEqual(stationary["opponent"]["motion"], {"status": "unknown"})
        self.assertTrue(all(item["direction_alignment"] is None for item in stationary["opponent"]["candidates"]))

    def test_claimed_cubes_are_excluded_from_candidates_and_pair_routes(self):
        context = gemini.build_tactical_context(
            self.arena,
            self.position,
            [{"time_s": 0, "x": 8, "y": -8}],
            ["F01", "F02"],
        )
        serialized = json.dumps(context)
        self.assertEqual(context["claimed_ids"], ["F01", "F02"])
        self.assertNotIn('"id": "F01"', serialized)
        self.assertNotIn('"first_id": "F02"', serialized)
        self.assertNotIn('"second_id": "F02"', serialized)

    def test_two_target_routes_supply_pair_distance_and_constant_speed_eta(self):
        context = gemini.build_tactical_context(self.arena, self.position, [], speed=0.5)
        pair = next(item for item in context["two_target_routes"] if item["first_id"] == "F01" and item["second_id"] == "F02")
        self.assertGreater(pair["between_distance_m"], 0)
        self.assertAlmostEqual(pair["between_eta_s"], pair["between_distance_m"] / 0.5, places=3)
        self.assertEqual(context["assumptions"]["eta_model"], "constant_0.5_mps_ignores_turns")

    def test_invalid_json_has_no_rule_fallback(self):
        selector = gemini.GeminiSelector("가까운 큐브", api_key="k", transport=CaptureTransport("F01"))
        with self.assertRaisesRegex(gemini.GeminiResponseError, "not a valid JSON"):
            selector.select(self.arena, self.position)

    def test_unknown_target_has_no_rule_fallback(self):
        selector = gemini.GeminiSelector("가까운 큐브", api_key="k", transport=CaptureTransport('{"target_id":"NOPE"}'))
        with self.assertRaisesRegex(gemini.GeminiResponseError, "unknown target_id"):
            selector.select(self.arena, self.position)

    def test_unreachable_target_has_no_rule_fallback(self):
        selector = gemini.GeminiSelector("언덕 우선", api_key="k", transport=CaptureTransport('{"target_id":"H01"}'))
        with self.assertRaisesRegex(gemini.GeminiResponseError, "unreachable target_id"):
            selector.select(self.arena, self.position)

    def test_network_error_never_leaks_key(self):
        secret = "do-not-print-this-key"

        def fail(url, headers, body, timeout):
            raise RuntimeError(f"upstream echoed {secret}")

        selector = gemini.GeminiSelector("평지 우선", api_key=secret, transport=fail)
        with self.assertRaises(gemini.GeminiSelectorError) as raised:
            selector.select(self.arena, self.position)
        self.assertNotIn(secret, str(raised.exception))
        self.assertIn("[REDACTED]", str(raised.exception))

    def test_strategy_validation(self):
        with self.assertRaises(ValueError):
            gemini.GeminiSelector("가" * 301, api_key="k")
        with self.assertRaises(ValueError):
            gemini.GeminiSelector("  ", api_key="k")


if __name__ == "__main__":
    unittest.main()
