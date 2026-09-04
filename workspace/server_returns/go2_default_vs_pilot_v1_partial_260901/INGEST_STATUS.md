# Go2 Default-vs-Pilot partial result ingest

- Work ID: `G-A006`
- Lifecycle: `RECEIVED`
- Source server path: `/workspace/_keep/go2_default_vs_pilot_v1/`
- Original local inbox: `workspace/_keep/go2_default_vs_pilot_v1/`
- Isolated path: `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/`
- Files/bytes: `461` / `519957865`
- Directory manifest SHA-256: `2b7867626065552ee1fe1a73a07a79a8ac577cb3ef0a03e481b6b0607e00b8a4`
- Result evidence: `RESULT_STATE=PARTIAL`, `RUNNER_RC=1`
- Complete evidence: Default telemetry `69/69`; Pilot telemetry `0/69`; videos `0/14`
- Final ZIP: missing; downloaded `.sha256` was 0 bytes and is invalid
- Inner SHA check: 459 stable files matched; `launcher.log` changed after manifest creation because the failure handler appended the packaging error
- Root cause: Pilot `exported/` was deleted before copying its checkpoint; partial packaging called unavailable bare `python3`
- Merge status: `NOT_PERFORMED`
- Server shutdown: `NOT_ALLOWED` until the complete ZIP and SHA companion are locally verified
- Recovery package: `workspace/training/quadruped/go2_default_vs_pilot_v1_hotfix.zip`
- Recovery package SHA-256: `b2fa2d57aee9ab55ea9765171d8230c8aeac8c38bbe46285548c864b4eee2d39`
