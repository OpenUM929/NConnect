@echo off
setlocal EnableExtensions EnableDelayedExpansion

title OMX Force Repair - Current Project
set "PROJECT=%CD%"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%I"
set "LOG=%USERPROFILE%\omx-force-repair-%TS%.log"

echo ============================================================
echo OMX FORCE REPAIR
echo Current project: %PROJECT%
echo Log: %LOG%
echo ============================================================
echo.

(
echo OMX FORCE REPAIR LOG
echo Started: %DATE% %TIME%
echo Project: %PROJECT%
) > "%LOG%"

echo [1/9] Checking Node and npm...
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

echo [2/9] Recording current paths...
echo ==== BEFORE ====>>"%LOG%"
where.exe node >>"%LOG%" 2>&1
where.exe npm >>"%LOG%" 2>&1
where.exe omx >>"%LOG%" 2>&1
where.exe codex >>"%LOG%" 2>&1
node --version >>"%LOG%" 2>&1
call npm.cmd --version >>"%LOG%" 2>&1
codex --version >>"%LOG%" 2>&1
omx --version >>"%LOG%" 2>&1
echo [OK] Diagnostics saved.
echo.

echo [3/9] Backing up CURRENT project OMX state...
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

echo [4/9] Removing duplicate Bun OMX package if present...
where.exe bun >nul 2>&1
if errorlevel 1 (
    echo [OK] Bun not found in PATH.
) else (
    bun remove -g oh-my-codex >>"%LOG%" 2>&1
    bun remove -g omx >>"%LOG%" 2>&1
    echo [OK] Bun itself was not removed.
)
echo.

echo [5/9] Removing npm OMX packages...
call npm.cmd uninstall -g oh-my-codex >>"%LOG%" 2>&1
call npm.cmd uninstall -g omx >>"%LOG%" 2>&1

if exist "%NPM_PACKAGE%" rmdir /S /Q "%NPM_PACKAGE%" >>"%LOG%" 2>&1
if exist "%NPM_PREFIX%\omx.cmd" del /F /Q "%NPM_PREFIX%\omx.cmd" >>"%LOG%" 2>&1
if exist "%NPM_PREFIX%\omx.ps1" del /F /Q "%NPM_PREFIX%\omx.ps1" >>"%LOG%" 2>&1
if exist "%NPM_PREFIX%\omx" del /F /Q "%NPM_PREFIX%\omx" >>"%LOG%" 2>&1
echo [OK] npm OMX cleanup complete.
echo.

echo [6/9] Installing oh-my-codex 0.21.5 through npm...
call npm.cmd cache verify >>"%LOG%" 2>&1
call npm.cmd install -g oh-my-codex@0.21.5 --force
if errorlevel 1 goto :INSTALL_FAIL

if not exist "%NPM_OMX%" goto :OMX_MISSING
echo [OK] npm-owned OMX: %NPM_OMX%
echo.

echo [7/9] Verifying exact npm-owned OMX...
call "%NPM_OMX%" --version
if errorlevel 1 goto :OMX_RUN_FAIL
echo.

echo [8/9] Removing ONLY current project's stale session pointer...
if exist "%SESSION%" (
    type "%SESSION%" >>"%LOG%" 2>&1
    del /F /Q "%SESSION%"
    if exist "%SESSION%" goto :SESSION_FAIL
    echo [OK] Removed: %SESSION%
) else (
    echo [INFO] session.json does not exist.
)
echo.

echo [9/9] Running doctor through exact npm-owned OMX...
echo ============================================================
call "%NPM_OMX%" doctor
set "DOCTOR_RC=!ERRORLEVEL!"
echo ============================================================
echo.

echo ==== AFTER ====>>"%LOG%"
where.exe omx >>"%LOG%" 2>&1
call "%NPM_OMX%" --version >>"%LOG%" 2>&1
echo Doctor RC=!DOCTOR_RC!>>"%LOG%"

echo Current PATH resolution:
where.exe omx
echo.
echo Exact repaired OMX:
echo %NPM_OMX%
echo.

if "!DOCTOR_RC!"=="0" (
    echo [SUCCESS] Exact npm-owned OMX passed doctor.
) else (
    echo [WARN] Doctor still reports a problem.
    echo Check the log: %LOG%
)

echo.
echo If plain "omx" still behaves differently from the exact path above,
echo PATH contains another OMX installation before the npm-owned one.
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
echo [ERROR] npm install finished but this file is missing:
echo %NPM_OMX%
goto :FAIL

:OMX_RUN_FAIL
echo [ERROR] Exact npm-owned OMX could not run.
goto :FAIL

:SESSION_FAIL
echo [ERROR] Could not remove:
echo %SESSION%
goto :FAIL

:FAIL
echo.
echo Repair stopped. No other project .omx folder was intentionally modified.
echo Log: %LOG%
echo.
pause
exit /b 1
