@echo off
setlocal EnableExtensions EnableDelayedExpansion
title OMX Clean Reinstall - Windows

set "PROJECT=%CD%"
set "NPM_PREFIX=%APPDATA%\npm"
set "NPM_ROOT=%NPM_PREFIX%\node_modules"
set "OMX_DIR=%NPM_ROOT%\oh-my-codex"
set "CACHE_DIR=%LOCALAPPDATA%\npm-cache"
set "NPM_OMX=%NPM_PREFIX%\omx.cmd"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%I"
set "LOG=%USERPROFILE%\omx-clean-reinstall-%TS%.log"

echo ============================================================
echo OMX CLEAN REINSTALL - WINDOWS
echo ============================================================
echo Project : %PROJECT%
echo Log     : %LOG%
echo.
echo IMPORTANT:
echo Close all OMX / Codex CLI windows before continuing.
echo This script does NOT kill processes automatically.
echo ============================================================
echo.

echo [1/8] Checking for running node.exe processes...
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /I "node.exe" >nul
if not errorlevel 1 (
    echo [WARN] One or more node.exe processes are running.
    echo.
    tasklist /FI "IMAGENAME eq node.exe"
    echo.
    echo OMX/Codex may be using one of these processes and locking files.
    echo Close OMX/Codex CLI windows, then press any key to continue.
    pause >nul
) else (
    echo [OK] No node.exe process detected.
)
echo.

echo [2/8] Recording current npm configuration...
(
    echo ==== OMX CLEAN REINSTALL ====
    echo Started: %DATE% %TIME%
    echo Project: %PROJECT%
    echo.
    echo ==== BEFORE ====
    where node
    where npm
    where omx
    where codex
    node --version
    call npm.cmd --version
    call npm.cmd prefix -g
    call npm.cmd root -g
) > "%LOG%" 2>&1
echo [OK] Diagnostics recorded.
echo.

echo [3/8] Removing npm OMX package registration...
call npm.cmd uninstall -g oh-my-codex >>"%LOG%" 2>&1
call npm.cmd uninstall -g omx >>"%LOG%" 2>&1
echo [OK] npm uninstall attempted.
echo.

echo [4/8] Removing leftover OMX files...
if exist "%OMX_DIR%" (
    echo Removing:
    echo   %OMX_DIR%
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Remove-Item -LiteralPath '%OMX_DIR%' -Recurse -Force -ErrorAction Stop" >>"%LOG%" 2>&1
    if errorlevel 1 (
        echo.
        echo [ERROR] Could not delete the OMX package folder.
        echo A process, antivirus scanner, or permissions are still locking it.
        echo.
        echo Close OMX/Codex/Node processes and run this BAT again.
        echo Log: %LOG%
        echo.
        pause
        exit /b 10
    )
)

for %%F in ("%NPM_PREFIX%\omx.cmd" "%NPM_PREFIX%\omx.ps1" "%NPM_PREFIX%\omx") do (
    if exist "%%~F" del /F /Q "%%~F" >>"%LOG%" 2>&1
)
echo [OK] OMX leftovers removed.
echo.

echo [5/8] Resetting npm download cache...
call npm.cmd cache clean --force
if errorlevel 1 (
    echo [WARN] npm cache clean returned an error.
    echo Trying direct _cacache cleanup...
)

if exist "%CACHE_DIR%\_cacache" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Remove-Item -LiteralPath '%CACHE_DIR%\_cacache' -Recurse -Force -ErrorAction Stop" >>"%LOG%" 2>&1
    if errorlevel 1 (
        echo.
        echo [ERROR] npm cache directory is still locked:
        echo   %CACHE_DIR%\_cacache
        echo.
        echo Close all npm/node processes or reboot Windows and rerun this BAT.
        echo Log: %LOG%
        echo.
        pause
        exit /b 11
    )
)

call npm.cmd cache verify
if errorlevel 1 (
    echo [WARN] npm cache verify still reports an issue.
) else (
    echo [OK] npm cache rebuilt and verified.
)
echo.

echo [6/8] Installing fresh OMX 0.21.5...
call npm.cmd install -g oh-my-codex@0.21.5 --force
if errorlevel 1 (
    echo.
    echo [ERROR] Fresh npm installation failed.
    echo Log: %LOG%
    echo.
    pause
    exit /b 12
)

if not exist "%NPM_OMX%" (
    echo.
    echo [ERROR] Installation finished but omx.cmd is missing:
    echo   %NPM_OMX%
    echo.
    pause
    exit /b 13
)

echo [OK] Installed:
echo   %NPM_OMX%
echo.

echo [7/8] Repairing ONLY current project's stale session pointer...
set "SESSION=%PROJECT%\.omx\state\session.json"
if exist "%SESSION%" (
    copy /Y "%SESSION%" "%SESSION%.bak-%TS%" >nul
    del /F /Q "%SESSION%"
    if exist "%SESSION%" (
        echo [WARN] Could not remove current project session.json.
    ) else (
        echo [OK] Removed stale session pointer.
    )
) else (
    echo [INFO] No current project session.json found.
)
echo.

echo [8/8] Verifying fresh OMX...
echo ------------------------------------------------------------
call "%NPM_OMX%" --version
echo.
call "%NPM_OMX%" doctor
set "RC=!ERRORLEVEL!"
echo ------------------------------------------------------------
echo.

(
    echo.
    echo ==== AFTER ====
    where omx
    call "%NPM_OMX%" --version
    echo Doctor RC=!RC!
) >> "%LOG%" 2>&1

echo PATH result:
where omx
echo.
echo Exact npm OMX:
echo   %NPM_OMX%
echo.

if "!RC!"=="0" (
    echo [SUCCESS] OMX installation and doctor are healthy.
    echo You can now run:
    echo   omx
) else (
    echo [WARN] OMX was reinstalled, but doctor still reports a problem.
    echo Please send the final doctor output and this log:
    echo   %LOG%
)

echo.
pause
exit /b !RC!
