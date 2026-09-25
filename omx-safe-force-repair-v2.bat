@echo off
setlocal EnableExtensions EnableDelayedExpansion

title OMX Safe Force Repair - No Preflight OMX Execution
set "PROJECT=%CD%"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%I"
set "LOG=%USERPROFILE%\omx-safe-repair-%TS%.log"

echo ============================================================
echo OMX SAFE FORCE REPAIR
echo Current project: %PROJECT%
echo Log: %LOG%
echo ============================================================
echo.

(
echo OMX SAFE FORCE REPAIR LOG
echo Started: %DATE% %TIME%
echo Project: %PROJECT%
) > "%LOG%"

echo [1/8] Checking Node and npm...
where.exe node >nul 2>&1 || goto :NO_NODE
where.exe npm.cmd >nul 2>&1 || goto :NO_NPM

for /f "delims=" %%I in ('call npm.cmd prefix -g 2^>nul') do set "NPM_PREFIX=%%I"
for /f "delims=" %%I in ('call npm.cmd root -g 2^>nul') do set "NPM_ROOT=%%I"

if not defined NPM_PREFIX goto :NO_PREFIX
if not defined NPM_ROOT goto :NO_ROOT

set "NPM_OMX=%NPM_PREFIX%\omx.cmd"
set "NPM_PACKAGE=%NPM_ROOT%\oh-my-codex"

echo [OK] npm prefix: %NPM_PREFIX%
echo [OK] npm root  : %NPM_ROOT%
echo npm prefix: %NPM_PREFIX%>>"%LOG%"
echo npm root: %NPM_ROOT%>>"%LOG%"
echo.

echo [2/8] Recording PATH only - not launching old OMX...
echo ==== BEFORE PATHS ====>>"%LOG%"

echo [2.1] where node
where.exe node
where.exe node >>"%LOG%" 2>&1

echo [2.2] where npm
where.exe npm
where.exe npm >>"%LOG%" 2>&1

echo [2.3] where omx
where.exe omx
where.exe omx >>"%LOG%" 2>&1

echo [2.4] where codex
where.exe codex
where.exe codex >>"%LOG%" 2>&1

echo [OK] No old OMX executable was launched.
echo.

echo [3/8] Backing up CURRENT project OMX state...
set "OMXDIR=%PROJECT%\.omx"
set "STATE=%OMXDIR%\state"
set "SESSION=%STATE%\session.json"
set "BACKUP=%OMXDIR%\state-backup-%TS%"

if exist "%STATE%" (
    xcopy "%STATE%" "%BACKUP%\" /E /I /H /Y >nul
    if errorlevel 1 goto :BACKUP_FAIL
    echo [OK] Backup: %BACKUP%
) else (
    echo [INFO] No current project .omx\state folder.
)
echo.

echo [4/8] Removing duplicate Bun OMX package if Bun exists...
where.exe bun >nul 2>&1
if errorlevel 1 (
    echo [OK] Bun not found in PATH.
) else (
    echo [INFO] Bun found. Removing only Bun global OMX packages...
    bun remove -g oh-my-codex >>"%LOG%" 2>&1
    bun remove -g omx >>"%LOG%" 2>&1
    echo [OK] Bun itself was NOT removed.
)
echo.

echo [5/8] Removing npm OMX packages and leftovers...
call npm.cmd uninstall -g oh-my-codex
call npm.cmd uninstall -g omx

if exist "%NPM_PACKAGE%" (
    echo [INFO] Removing leftover package directory...
    rmdir /S /Q "%NPM_PACKAGE%" >>"%LOG%" 2>&1
)

if exist "%NPM_PREFIX%\omx.cmd" del /F /Q "%NPM_PREFIX%\omx.cmd" >>"%LOG%" 2>&1
if exist "%NPM_PREFIX%\omx.ps1" del /F /Q "%NPM_PREFIX%\omx.ps1" >>"%LOG%" 2>&1
if exist "%NPM_PREFIX%\omx" del /F /Q "%NPM_PREFIX%\omx" >>"%LOG%" 2>&1

echo [OK] Old npm OMX removed.
echo.

echo [6/8] Installing oh-my-codex@0.21.5 through npm...
call npm.cmd cache verify
call npm.cmd install -g oh-my-codex@0.21.5 --force
if errorlevel 1 goto :INSTALL_FAIL

if not exist "%NPM_OMX%" goto :OMX_MISSING

echo [OK] Installed npm-owned OMX:
echo      %NPM_OMX%
echo.

echo [7/8] Removing ONLY current project's stale session pointer...
if exist "%SESSION%" (
    type "%SESSION%" >>"%LOG%" 2>&1
    del /F /Q "%SESSION%"
    if exist "%SESSION%" goto :SESSION_FAIL
    echo [OK] Removed: %SESSION%
) else (
    echo [INFO] session.json does not exist.
)
echo.

echo [8/8] Testing ONLY the newly installed npm-owned OMX...
echo ------------------------------------------------------------

call "%NPM_OMX%" --version
if errorlevel 1 goto :OMX_RUN_FAIL

echo.
call "%NPM_OMX%" doctor
set "DOCTOR_RC=!ERRORLEVEL!"

echo ------------------------------------------------------------
echo.

echo ==== AFTER PATHS ====>>"%LOG%"
where.exe omx >>"%LOG%" 2>&1
call "%NPM_OMX%" --version >>"%LOG%" 2>&1
echo Doctor RC=!DOCTOR_RC!>>"%LOG%"

echo Current PATH resolution:
where.exe omx
echo.
echo Exact npm-owned OMX:
echo %NPM_OMX%
echo.

if "!DOCTOR_RC!"=="0" (
    echo [SUCCESS] Newly installed npm-owned OMX passed doctor.
) else (
    echo [WARN] Newly installed npm-owned OMX still reports a problem.
    echo Log: %LOG%
)

echo.
echo IMPORTANT:
echo If the exact npm-owned OMX works but plain "omx" does not,
echo PATH is pointing to another OMX installation first.
echo.
pause
exit /b !DOCTOR_RC!

:NO_NODE
echo [ERROR] node.exe not found in PATH.
goto :FAIL

:NO_NPM
echo [ERROR] npm.cmd not found in PATH.
goto :FAIL

:NO_PREFIX
echo [ERROR] Could not determine npm global prefix.
goto :FAIL

:NO_ROOT
echo [ERROR] Could not determine npm global root.
goto :FAIL

:BACKUP_FAIL
echo [ERROR] Could not back up current project state.
goto :FAIL

:INSTALL_FAIL
echo [ERROR] npm install failed.
goto :FAIL

:OMX_MISSING
echo [ERROR] npm install finished but omx.cmd is missing:
echo %NPM_OMX%
goto :FAIL

:SESSION_FAIL
echo [ERROR] Could not remove:
echo %SESSION%
goto :FAIL

:OMX_RUN_FAIL
echo [ERROR] Newly installed npm-owned OMX could not run.
goto :FAIL

:FAIL
echo.
echo Repair stopped.
echo Log: %LOG%
echo No other project .omx folder was intentionally modified.
echo.
pause
exit /b 1
