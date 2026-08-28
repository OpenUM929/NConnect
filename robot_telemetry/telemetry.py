"""Dependency-free structured telemetry for Isaac Sim/Isaac Lab motion tests."""
from __future__ import annotations

import csv
import json
import math
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SCHEMA_VERSION = "1.0"
REQUIRED_SAMPLE_PATHS = (
    "pose.position_m", "pose.rpy_deg", "velocity.linear_mps", "velocity.angular_rps",
    "command.linear_mps", "command.yaw_rate_rps", "target.distance_m",
    "target.heading_error_deg", "target.altitude_error_m", "stability.base_height_m",
    "stability.is_upright", "stability.contact_count",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _get(data: Dict[str, Any], dotted: str) -> Any:
    value: Any = data
    for key in dotted.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _flatten(data: Any, prefix: str = "") -> Dict[str, Any]:
    if isinstance(data, dict):
        result: Dict[str, Any] = {}
        for key, value in data.items():
            result.update(_flatten(value, f"{prefix}{key}_"))
        return result
    if isinstance(data, (list, tuple)):
        return {prefix[:-1]: json.dumps(data, ensure_ascii=False)}
    return {prefix[:-1]: data}


@dataclass
class TelemetryRecorder:
    path: Path
    robot_model: str
    run_metadata: Dict[str, Any]
    run_id: str = field(default_factory=lambda: f"run-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._closed = False
        self._write("run_started", phase="setup", trial=0, metadata=self.run_metadata)

    def _write(self, event_type: str, *, phase: str, trial: int, **payload: Any) -> None:
        if self._closed:
            raise RuntimeError("Cannot write to a completed telemetry run")
        record = {
            "schema_version": SCHEMA_VERSION, "event_id": uuid.uuid4().hex,
            "ts_utc": utc_now(), "run_id": self.run_id, "robot_model": self.robot_model,
            "phase": phase, "trial": trial, "event_type": event_type, **payload,
        }
        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    def start_phase(self, phase: str, trial: int, *, difficulty: int, config: Dict[str, Any], expected: str) -> None:
        self._write("phase_started", phase=phase, trial=trial, difficulty=difficulty,
                    config=config, expected=expected)

    def sample(self, phase: str, trial: int, observed: Dict[str, Any]) -> None:
        missing = [path for path in REQUIRED_SAMPLE_PATHS if _get(observed, path) is None]
        if missing:
            raise ValueError(f"sample is missing required fields: {', '.join(missing)}")
        self._write("sample", phase=phase, trial=trial, observed=observed)

    def incident(self, phase: str, trial: int, kind: str, *, severity: str, details: Dict[str, Any]) -> None:
        self._write("incident", phase=phase, trial=trial, incident={"kind": kind, "severity": severity, "details": details})

    def complete_phase(self, phase: str, trial: int, *, predicted: str, actual: str,
                       passed: bool, reason: str, metrics: Dict[str, Any]) -> None:
        self._write("phase_completed", phase=phase, trial=trial, predicted=predicted,
                    actual=actual, passed=passed, reason=reason, metrics=metrics)

    def complete_run(self, *, passed: bool, summary: Dict[str, Any]) -> None:
        self._write("run_completed", phase="complete", trial=0, passed=passed, summary=summary)
        self._closed = True


def read_events(path: Path) -> List[Dict[str, Any]]:
    events = []
    with Path(path).open(encoding="utf-8") as fp:
        for line_no, line in enumerate(fp, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_no}: {exc.msg}") from exc
            missing = [k for k in ("schema_version", "run_id", "phase", "trial", "event_type") if k not in event]
            if missing:
                raise ValueError(f"line {line_no} missing event fields: {', '.join(missing)}")
            events.append(event)
    return events


def summarize(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, Dict[str, Any]] = {}
    for event in events:
        if event["event_type"] in {"run_started", "run_completed"}:
            continue
        key = (event["run_id"], event["phase"], event["trial"])
        group = groups.setdefault(key, {"run_id": key[0], "phase": key[1], "trial": key[2], "samples": [], "incidents": []})
        if event["event_type"] == "sample":
            group["samples"].append(event["observed"])
        elif event["event_type"] == "incident":
            group["incidents"].append(event["incident"])
        elif event["event_type"] == "phase_completed":
            group["result"] = event
            group["difficulty"] = event.get("difficulty")
    rows = []
    for group in groups.values():
        samples = group["samples"]
        distances = [_get(s, "target.distance_m") for s in samples]
        tilts = [max(abs(_get(s, "pose.rpy_deg")[0]), abs(_get(s, "pose.rpy_deg")[1])) for s in samples]
        heights = [_get(s, "stability.base_height_m") for s in samples]
        result = group.get("result", {})
        rows.append({
            "run_id": group["run_id"], "phase": group["phase"], "trial": group["trial"],
            "sample_count": len(samples), "start_distance_m": distances[0] if distances else None,
            "end_distance_m": distances[-1] if distances else None,
            "distance_progress_m": (distances[0] - distances[-1]) if distances else None,
            "max_tilt_deg": max(tilts) if tilts else None,
            "min_base_height_m": min(heights) if heights else None,
            "fall_incidents": sum(1 for i in group["incidents"] if i.get("kind") == "fall"),
            "incident_count": len(group["incidents"]), "passed": result.get("passed"),
            "reason": result.get("reason"), "predicted": result.get("predicted"), "actual": result.get("actual"),
        })
    return sorted(rows, key=lambda x: (x["phase"], x["trial"]))


def evaluate_phase(samples: List[Dict[str, Any]], incidents: List[Dict[str, Any]],
                   pass_rule: Dict[str, Any], safety: Dict[str, float]) -> Dict[str, Any]:
    """Apply the configured gate to recorded states before resetting the environment.

    Call this only with observations from one phase/trial.  Its result is deliberately
    explicit so the value placed in `phase_completed` can be reproduced from raw samples.
    """
    if not samples:
        return {"passed": False, "reason": "no_samples", "metrics": {}}
    falls = sum(1 for incident in incidents if incident.get("kind") == "fall")
    heights = [_get(s, "stability.base_height_m") for s in samples]
    tilts = [max(abs(_get(s, "pose.rpy_deg")[0]), abs(_get(s, "pose.rpy_deg")[1])) for s in samples]
    final = samples[-1]
    metrics = {
        "end_distance_m": _get(final, "target.distance_m"),
        "end_heading_error_deg": abs(_get(final, "target.heading_error_deg")),
        "min_base_height_m": min(heights), "max_tilt_deg": max(tilts), "fall_incidents": falls,
        "altitude_gain_m": _get(final, "pose.position_m")[2] - _get(samples[0], "pose.position_m")[2],
    }
    if falls:
        return {"passed": False, "reason": "fall", "metrics": metrics}
    if not all(_get(s, "stability.is_upright") for s in samples):
        return {"passed": False, "reason": "not_upright", "metrics": metrics}
    if metrics["min_base_height_m"] < safety["min_base_height_m"]:
        return {"passed": False, "reason": "base_too_low", "metrics": metrics}
    if metrics["max_tilt_deg"] > safety["max_abs_roll_pitch_deg"]:
        return {"passed": False, "reason": "excessive_tilt", "metrics": metrics}
    if metrics["end_distance_m"] > pass_rule.get("max_distance_m", float("inf")):
        return {"passed": False, "reason": "target_not_reached", "metrics": metrics}
    if metrics["end_heading_error_deg"] > pass_rule.get("max_heading_error_deg", float("inf")):
        return {"passed": False, "reason": "heading_error", "metrics": metrics}
    if metrics["altitude_gain_m"] < pass_rule.get("min_altitude_gain_m", -float("inf")):
        return {"passed": False, "reason": "insufficient_altitude_gain", "metrics": metrics}
    return {"passed": True, "reason": "pass", "metrics": metrics}


def export_artifacts(log_path: Path, output_dir: Path) -> List[Dict[str, Any]]:
    events = read_events(log_path)
    rows = summarize(events)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = [_flatten(e) for e in events if e["event_type"] == "sample"]
    for filename, data in (("phase_summary.csv", rows), ("samples.csv", samples)):
        fields = sorted({key for row in data for key in row})
        with (output_dir / filename).open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fields)
            writer.writeheader(); writer.writerows(data)
    with (output_dir / "phase_summary.md").open("w", encoding="utf-8") as fp:
        fp.write("# Motion phase summary\n\n")
        fp.write("| phase | trial | progress (m) | max tilt (°) | min height (m) | falls | pass | reason |\n|---|---:|---:|---:|---:|---:|---|---|\n")
        for row in rows:
            val = lambda k: "—" if row[k] is None else (f"{row[k]:.3f}" if isinstance(row[k], float) else str(row[k]))
            fp.write(f"| {row['phase']} | {row['trial']} | {val('distance_progress_m')} | {val('max_tilt_deg')} | {val('min_base_height_m')} | {row['fall_incidents']} | {val('passed')} | {val('reason')} |\n")
    return rows
