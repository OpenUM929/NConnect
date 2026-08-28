# Isaac motion telemetry

## Files

* `PRD.md` — staged-motion requirements and exact JSONL contract.
* `config/motion_plan.json` — editable phase order, targets, thresholds, and timeouts.
* `telemetry.py` — recorder plus CSV/Markdown exporter; Python standard library only.
* `demo.py` — generates a valid synthetic log and report.

## Quick verification

```powershell
cd C:\dev\Nconnect\robot_telemetry
python -m unittest discover -s tests -v
python demo.py
```

The demo writes to `%TEMP%\\robot_telemetry_demo` by default so it also works from a
read-only source checkout. Set `ROBOT_TELEMETRY_OUTPUT` to change this location.
Generated artifacts:

* `demo.jsonl`: raw, append-only diagnosis source.
* `demo_report/samples.csv`: one row per simulation observation, suitable for charts.
* `demo_report/phase_summary.csv` and `.md`: phase-level trend table.

## Isaac Lab insertion point

Create one recorder immediately after an environment/policy is loaded. Call `start_phase`
before a phase, call `sample` once every `sample_period_s` from the physics/control loop,
call `incident` immediately on a fall/collision/timeout, and call `complete_phase` before
resetting. Do **not** invent timestamps or estimate a fall after reset: log the measured
state first.

```python
recorder = TelemetryRecorder("logs/run.jsonl", "Go2", {
    "policy_path": str(policy_path), "map": "practice_map", "isaac_version": "..."
})
# In each control-loop sample, translate Isaac tensors to this stable schema:
recorder.sample(phase_name, trial, observed={
    "pose": {"position_m": [x, y, z], "rpy_deg": [roll, pitch, yaw]},
    "velocity": {"linear_mps": [vx, vy, vz], "angular_rps": [wx, wy, wz]},
    "command": {"linear_mps": [cmd_vx, cmd_vy, cmd_vz], "yaw_rate_rps": cmd_wz, "source": "policy"},
    "target": {"distance_m": distance, "heading_error_deg": yaw_error, "altitude_error_m": dz},
    "stability": {"base_height_m": z, "is_upright": upright, "contact_count": contacts},
    "extra": {"terrain": terrain_name, "policy_action": action.tolist()},
})
```

Collect the samples and incidents for a phase, then apply the configured gate before
calling `complete_phase`:

```python
verdict = evaluate_phase(phase_samples, phase_incidents, phase_config["pass"], plan["safety"])
recorder.complete_phase(phase_name, trial, predicted=phase_config["expected"],
                        actual=human_readable_result, **verdict)
```

When sharing a log later, send the raw `.jsonl` and the exact `motion_plan.json` used for
that run.  The raw log retains enough context to distinguish a policy failure, unsuitable
target, fall, collision, or command-tracking failure.
