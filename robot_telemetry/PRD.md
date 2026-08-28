# Robot Motion Telemetry PRD

## Goal

Provide an Isaac Lab/Isaac Sim robot experiment with repeatable, increasing-difficulty
motion checks and machine-readable evidence.  A person running the simulation should be
able to send the generated `jsonl` log alone for a later diagnosis.

## Scope and success criteria

The package records the **plan**, each sampled **actual state**, safety incidents, and the
final **result** for these phases.  Every run must have a unique ID and be exportable to
CSV/Markdown without an Isaac installation.

| Order | Phase | Goal | Minimum pass rule |
|---:|---|---|---|
| 1 | `stand` | remain upright at rest | no fall; roll/pitch and base height remain within configured limits |
| 2 | `forward` | move straight to a flat target | pass stand rule; reach position tolerance before timeout |
| 3 | `turn` | turn to a yaw target while stationary | pass stand rule; yaw error within tolerance |
| 4 | `turn_and_move` | turn then reach a flat target | reach target before timeout without fall |
| 5 | `hill_up` | climb a ramp/hill to the top target | reach target and configured altitude gain without fall |
| 6 | `hill_down` | descend safely | reach target without fall or excessive tilt |

Only promote a policy to the next phase after the previous phase passes for the configured
number of trials.  This prevents a fast but unstable policy from being evaluated as a
mission policy.

## Non-goals

This package does not replace the policy, reward function, navigation/LLM, or Isaac Lab
environment.  It observes them.  Coordinate axes, robot asset names, and contact sensor
names must be supplied by the host project.

## Standard log contract (JSON Lines)

One UTF-8 JSON object is written per line.  Never edit a completed log in place.  Required
top-level fields on every event are:

```text
schema_version, event_id, ts_utc, run_id, robot_model, phase, trial, event_type
```

Event types:

* `run_started`: software, asset, map, policy hashes/paths and all settings.
* `phase_started`: planned command, expected result, target, pass rules and difficulty.
* `sample`: current pose, velocity, command, contacts, target error and stability state.
* `incident`: fall, collision, timeout, policy error, or manual abort.
* `phase_completed`: predicted result before execution, actual result, measured metrics,
  and pass/fail reason.
* `run_completed`: aggregate result.

`phase_started.expected` answers **what should happen**. `sample.observed` answers
**what happened now**. `phase_completed.actual` answers **what really happened**.  This
separation makes later causal analysis possible.

## Required sample fields

The host must provide SI-unit values whenever available.

* `pose.position_m` (`x,y,z`) and `pose.rpy_deg` (`roll,pitch,yaw`)
* `velocity.linear_mps` and `velocity.angular_rps`
* `command.linear_mps`, `command.yaw_rate_rps`, and `command.source`
* `target.distance_m`, `target.heading_error_deg`, `target.altitude_error_m`
* `stability.base_height_m`, `stability.is_upright`, `stability.contact_count`

The recorder retains extra fields, so add robot-specific sensor data under `extra` instead
of changing the required names.

## Acceptance checks

1. A generated demo log has all event types and can be summarized.
2. The CSV has one row per `sample`, including phase/trial/run IDs.
3. The Markdown phase table shows planned versus actual outcome and key trend columns.
4. The unit tests verify missing required sample fields and summary calculations.

