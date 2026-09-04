# `go2_tuning_engine_v1` local verification

> `BUGGY_DO_NOT_REUSE`: server preflight proved that v1.0 incorrectly called bare `python3`.
> Training never started. Replaced by `go2_tuning_engine_v1_1.zip` using IsaacLab's Python launcher.

- engine ZIP: `workspace/training/quadruped/go2_tuning_engine_v1.zip`
- engine SHA-256: `4489bef429a38a145763b5af8c4d55081c0a10f501a9b552194f111116f98a5a`
- size: 6,415,805 bytes
- members: 34
- ZIP CRC: OK
- unsafe paths: 0
- internal manifest: 33/33 matched
- deterministic rebuild: 2/2 identical SHA
- experiment embedded in engine: no
- schema: `config/go2_tuning_experiment_schema.json`
- G-A010 JSON: `config/experiments/G_A010_lin_vel_z_m2.json`
- G-A010 JSON SHA-256: `fa0bb3b749aa4412cb5023807cc895db08f416e626730ee34477c516bc6ec425`
- contract tests: 14/14 (`go2_tuning_engine` 8 + G-A009 regression 6)
- extracted-engine materialization: OK
- invalid second reward change rejection: OK
- frozen Default-01 reward/model/env identity: OK
- Python compile: OK
- runner CRLF: 0
- Git Bash `bash -n`: OK

## Evidence boundary

This verifies package integrity, schema enforcement, source materialization, and static result contracts.
It is `ARTIFACT_VERIFIED` for the upload package only. No G-A010 server run, checkpoint, telemetry,
video, internal performance decision, or official result exists yet.
