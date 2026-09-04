# Go2 evaluator hotfix v2 verification

## Root cause

- G-A007 completed training, then produced eight telemetry cases before Isaac Sim 5.1 crashed at startup for `G2/combined_yaw_left`, seed 101.
- The v1 telemetry hook called a hard process exit inside `env.step()` at the fixed horizon.
- Isaac Lab v2.3.1 upstream `play.py` normally exits its loop and then calls `env.close()` and `simulation_app.close()`.
- Therefore v1 bypassed the upstream cleanup path after every successful case; the next startup was exposed to an unclean Kit/GPU shutdown. The exact NVIDIA C++ `XOpenDisplay` crash remains external, but the repo-controlled trigger and fail-fast behavior are removed.

Upstream reference:
`https://github.com/isaac-sim/IsaacLab/blob/v2.3.1/scripts/reinforcement_learning/rsl_rl/play.py#L163-L189`

## Corrections

1. `go2_eval_telemetry.py` marks collection complete and makes `simulation_app.is_running()` return false.
2. Upstream `env.close()` and `simulation_app.close()` now run normally.
3. Telemetry and video cases receive three bounded attempts with increasing backoff.
4. The package embeds the verified candidate model/env and eight completed case fingerprints; `GO2_RESUME=1 GO2_RECOVERY_ONLY=1` refuses retraining on both the same server and a reset server.
5. The active tee log is replaced in the package by an immutable `launcher.snapshot.log`, eliminating the known internal-manifest race.

## Package

- Path: `workspace/training/quadruped/go2_feet_air_time_020_v2.zip`
- SHA-256: `73c6ba1f9cc29b22889d146e4c949ff54b7a9e2b4638199f61c9961dc9f88dbc`
- ZIP members: 95
- Internal manifest: 94/94
- CRC: OK
- Unsafe paths: 0
- Deterministic rebuild: identical SHA
- Embedded recovery model SHA: `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5`
- Embedded completed telemetry cases: 8
- Recovery-only guard: refuses training when the embedded or existing candidate does not match

## Tests

- Python compilation: OK
- Contract tests: 6/6
- AST hard-exit calls in packaged telemetry: 0
- Retry contract in packaged runner: present
- Stable launcher snapshot contract: present
- Git Bash `bash -n`: OK

## Validation limit

Isaac Sim is unavailable locally, so the real Kit startup and graceful close path require one server execution. This package removes the proven repo-controlled hard-exit path and bounds the remaining external startup failure; it does not claim to patch NVIDIA's closed-source segmentation fault.
