# G-A006 Go2 Default-vs-Pilot FULL result verification

- Received: 2026-09-01
- Local inbox ZIP: `workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip`
- ZIP bytes: `416205363`
- ZIP SHA-256: `af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b`
- Companion SHA match: `true`
- ZIP entries: `925`
- Unsafe paths: `0`
- `RESULT_STATE=FULL`
- `RUNNER_RC=0`
- Telemetry: Default `69/69`, Pilot `69/69`
- Videos: Default `7/7`, Pilot `7/7`; all 14 files are non-empty
- Video evidence layer: `VIDEO_UNKNOWN` until human observation
- Inner manifest: `923` content files matched, `0` missing, `1` mismatch
- Inner mismatch: `launcher.log` only. Packaging appended the final completion line after the inner manifest was generated. The downloaded ZIP itself is protected by the matching external SHA; all other inner-manifest files matched.
- Artifact verdict: `ARTIFACT_VERIFIED`
- Server shutdown verdict: `ALLOWED`
- Merge verdict: `NOT_PERFORMED`; keep the FULL result isolated until analysis and selective merge.

## Internal evaluator snapshot

- Default: `INTERNAL_GATE_FAIL`, internal simulation proxy `17.90699218052112/70`
- Pilot: `INTERNAL_GATE_FAIL`, internal simulation proxy `41.97989846355527/70`
- Pilot minus Default fraction: `+0.34389866118620216` (about `+24.07/70`)
- Paired decision: `SHARED_WEAKNESS_FOUND`
- Official result: not measured
