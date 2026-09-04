# `go2_tuning_engine_v1_1` hotfix verification

- engine version: `1.0.1`
- engine ZIP: `workspace/training/quadruped/go2_tuning_engine_v1_1.zip`
- engine SHA-256: `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`
- size: 6,416,160 bytes
- colocated experiment: `workspace/training/quadruped/G_A010_lin_vel_z_m2.json`
- experiment SHA-256: `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`
- canonical↔colocated JSON bytes: identical
- root cause removed: bare `python3` references 0
- launcher: `/workspace/IsaacLab/isaaclab.sh -p`
- runner CRLF: 0
- Git Bash `bash -n`: OK
- Python compile: OK
- ZIP CRC: OK
- unsafe paths: 0
- members: 34
- internal manifest: 33/33 matched
- deterministic rebuild: identical SHA across contract-triggered builds
- contract tests: 8/8
- extracted-engine runtime materialization: OK

## Evidence boundary

The v1.0 server attempt failed before tmux/training and consumed zero iterations. V1.1 is locally
`ARTIFACT_VERIFIED`; G-A010 checkpoint, telemetry, video, internal performance, and official result
remain unmeasured until the server run completes.
