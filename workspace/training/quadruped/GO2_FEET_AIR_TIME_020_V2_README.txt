Go2 feet_air_time=0.20 evaluation hotfix v2
============================================================

Purpose
- Reuse the completed 1,000-iteration candidate training artifact.
- Resume only missing G1-G7 telemetry and videos.
- Replace telemetry os._exit(0) with a graceful Isaac Lab loop stop so
  env.close() and simulation_app.close() run after every case.
- Retry a transient case/video startup failure up to three times with backoff.
- Package a stable launcher.snapshot.log instead of hashing a live tee log.

Upload
  C:\dev\Nconnect\workspace\training\quadruped\go2_feet_air_time_020_v2.zip

Server destination
  /workspace/go2_feet_air_time_020_v2.zip

This ZIP intentionally extracts over /workspace/go2_feet_air_time_020_v1.  It
also embeds the locally recovered candidate checkpoint and eight completed
cases, so a reset server can recover without retraining.

Run only after the old tmux process has ended:
  cd /workspace && unzip -oq go2_feet_air_time_020_v2.zip && cd /workspace/go2_feet_air_time_020_v1 && GO2_RESUME=1 GO2_RECOVERY_ONLY=1 bash server_run_go2_feet_air_time_020_v1.sh

Success marker
  [DONE] GO2_FEET_AIR_TIME_020_RESULT_READY

Result
  /workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip

The SHA companion is optional transfer evidence. Completion is determined by
RESULT_STATE=FULL, RUNNER_RC=0, 69 telemetry summaries, seven videos, policy.pt,
and POLICY_LINEAGE.json.
