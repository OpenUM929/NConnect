Go2 G-A009 — track_lin_vel_xy_exp 1.0 -> 1.2 only

UPLOAD ZIP
  go2_track_lin_vel_120_v1.zip

SERVER DESTINATION
  /workspace/go2_track_lin_vel_120_v1.zip

ONE COMMAND
  cd /workspace && unzip -oq go2_track_lin_vel_120_v1.zip && cd /workspace/go2_track_lin_vel_120_v1 && bash server_run_go2_track_lin_vel_120_v1.sh

MONITOR
  tmux attach -t go2_track_lin_vel_120_v1

DONE MARKER
  [DONE] GO2_TRACK_LIN_VEL_120_RESULT_READY

DOWNLOAD BOTH
  /workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip
  /workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip.sha256

RESUME AFTER A RECOVERABLE INTERRUPTION
  cd /workspace/go2_track_lin_vel_120_v1 && GO2_RESUME=1 bash server_run_go2_track_lin_vel_120_v1.sh

The runner trains once, runs a repaired 7-case early-kill screen, records one
required video, and only then expands to 21 representative cases. It never
runs the 69-case full suite automatically. A single result ZIP is created for
both early-stop and representative outcomes. Official result remains unmeasured.
