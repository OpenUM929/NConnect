@echo off
rem G-A060 PC2 3-point chain progress viewer.
rem Shows: per-attempt point status table, current point tail log, GPU status.

set "POINTS=C:\workspace\_keep\go2_g_a060_pc2_points"

echo ============================================================
echo G-A060 PC2 CHAIN STATUS  (%DATE% %TIME%)
echo ============================================================
echo.
echo [POINT_STATUS.tsv]
echo ------------------------------------------------------------
type "%POINTS%\POINT_STATUS.tsv"
echo.
echo [point.log - last 20 lines]
echo ------------------------------------------------------------
powershell -NoProfile -Command "Get-Content -LiteralPath '%POINTS%\point.log' -Tail 20"
echo.
echo [GPU status]
echo ------------------------------------------------------------
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,power.draw --format=csv
echo.
echo [Running training processes]
echo ------------------------------------------------------------
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'train.py' } | Select-Object ProcessId,CreationDate,CommandLine | Format-List"
echo ============================================================
