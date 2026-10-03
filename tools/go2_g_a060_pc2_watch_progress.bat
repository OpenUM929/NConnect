@echo off
rem Live-refreshing view of the G-A060 PC2 chain, as a Windows stand-in for
rem `tmux attach` (tmux is unavailable on this machine). Ctrl+C to stop.

:loop
cls
call "%~dp0go2_g_a060_pc2_check_progress.bat"
echo.
echo (refreshing every 10s — Ctrl+C to stop)
timeout /t 10 /nobreak >nul
goto loop
