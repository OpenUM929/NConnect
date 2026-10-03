@echo off
rem Shows the RSL-RL Iteration-time/Time-elapsed/ETA block we use to judge
rem training speed, from the most recently written candidate_training.log
rem under the G-A060 PC2 work tree.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0go2_g_a060_pc2_check_speed.ps1"
