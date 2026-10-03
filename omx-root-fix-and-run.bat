@echo off
rem ============================================================
rem OMX foreign-cwd ROOT FIX + launch
rem Run THIS BAT from the SAME CMD window where "omx" fails.
rem Example:
rem   C:\dev\NConnect>C:\Tools\omx-root-fix-and-run.bat
rem
rem No SETLOCAL on purpose:
rem current CMD environment changes must survive after this BAT ends.
rem ============================================================

title OMX ROOT FIX AND RUN

echo.
echo ============================================================
echo OMX ROOT FIX AND RUN
echo ============================================================
echo Current project : %CD%
echo.

where omx >nul 2>&1
if errorlevel 1 (
    echo [ERROR] omx is not in PATH.
    exit /b 10
)

echo [BEFORE]
echo OMX_ROOT=%OMX_ROOT%
echo OMX_STATE_ROOT=%OMX_STATE_ROOT%
echo OMX_TEAM_STATE_ROOT=%OMX_TEAM_STATE_ROOT%
echo OMX_SOURCE_CWD=%OMX_SOURCE_CWD%
echo.

rem ------------------------------------------------------------
rem Backup persistent values first
rem ------------------------------------------------------------
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "OMX_FIX_TS=%%I"
set "OMX_FIX_BACKUP=%USERPROFILE%\omx-env-backup-%OMX_FIX_TS%.txt"

(
  echo OMX environment backup
  echo Project=%CD%
  echo Date=%DATE% %TIME%
  echo.
  echo [CURRENT PROCESS]
  set OMX_ 2^>nul
  echo.
  echo [HKCU Environment]
  reg query HKCU\Environment 2^>nul ^| findstr /I "OMX_"
  echo.
  echo [HKLM Environment]
  reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" 2^>nul ^| findstr /I "OMX_"
) > "%OMX_FIX_BACKUP%"

echo [INFO] Backup saved:
echo        %OMX_FIX_BACKUP%
echo.

rem ------------------------------------------------------------
rem 1. Clear current CMD values.
rem ------------------------------------------------------------
set "OMX_ROOT="
set "OMX_STATE_ROOT="
set "OMX_TEAM_STATE_ROOT="
set "OMX_SOURCE_CWD="
set "OMX_SESSION_ID="
set "OMX_TEAM_LEADER_CWD="
set "OMX_TEAM_WORKER="
set "OMX_TEAM_INTERNAL_WORKER="

rem ------------------------------------------------------------
rem 2. Remove persistent USER-level binding variables.
rem    These are the values most likely to leak project A into B.
rem ------------------------------------------------------------
for %%V in (OMX_ROOT OMX_STATE_ROOT OMX_TEAM_STATE_ROOT OMX_SOURCE_CWD OMX_SESSION_ID OMX_TEAM_LEADER_CWD OMX_TEAM_WORKER OMX_TEAM_INTERNAL_WORKER) do (
    reg query HKCU\Environment /v %%V >nul 2>&1
    if not errorlevel 1 (
        reg delete HKCU\Environment /v %%V /f >nul 2>&1
        if errorlevel 1 (
            echo [WARN] Failed to remove user variable %%V
        ) else (
            echo [OK] Removed user variable %%V
        )
    )
)

echo.
echo [AFTER CURRENT CMD]
if defined OMX_ROOT (
    echo [ERROR] OMX_ROOT is STILL set:
    echo         %OMX_ROOT%
    exit /b 20
) else (
    echo [OK] OMX_ROOT is empty in this CMD.
)

if defined OMX_STATE_ROOT (
    echo [WARN] OMX_STATE_ROOT is still set: %OMX_STATE_ROOT%
) else (
    echo [OK] OMX_STATE_ROOT is empty.
)

if defined OMX_TEAM_STATE_ROOT (
    echo [WARN] OMX_TEAM_STATE_ROOT is still set: %OMX_TEAM_STATE_ROOT%
) else (
    echo [OK] OMX_TEAM_STATE_ROOT is empty.
)

if defined OMX_SOURCE_CWD (
    echo [WARN] OMX_SOURCE_CWD is still set: %OMX_SOURCE_CWD%
) else (
    echo [OK] OMX_SOURCE_CWD is empty.
)
echo.

rem ------------------------------------------------------------
rem 3. Detect machine-level leakage. Do not silently delete it.
rem ------------------------------------------------------------
set "OMX_MACHINE_LEAK="
for %%V in (OMX_ROOT OMX_STATE_ROOT OMX_TEAM_STATE_ROOT OMX_SOURCE_CWD OMX_SESSION_ID OMX_TEAM_LEADER_CWD OMX_TEAM_WORKER OMX_TEAM_INTERNAL_WORKER) do (
    reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v %%V >nul 2>&1
    if not errorlevel 1 (
        echo [WARN] Machine-level variable exists: %%V
        set "OMX_MACHINE_LEAK=1"
    )
)

if defined OMX_MACHINE_LEAK (
    echo.
    echo [WARN] A machine-level OMX variable exists.
    echo        It can be inherited again by NEW terminals.
    echo        This BAT will continue with the CLEAN current CMD,
    echo        but the machine-level setting should be removed separately.
    echo.
)

rem ------------------------------------------------------------
rem 4. Doctor in the now-clean CURRENT CMD.
rem ------------------------------------------------------------
set "OMX_FIX_DOCTOR=%TEMP%\omx_rootfix_%RANDOM%_%RANDOM%.txt"

echo ============================================================
echo Running clean: omx doctor
echo ============================================================
omx doctor > "%OMX_FIX_DOCTOR%" 2>&1
type "%OMX_FIX_DOCTOR%"
echo.

findstr /I /C:"src=omx-root-env" /C:"ptr=foreign" /C:"foreign-cwd" "%OMX_FIX_DOCTOR%" >nul 2>&1
if not errorlevel 1 (
    echo ============================================================
    echo [FAILED] OMX still selected an external/foreign root.
    echo ============================================================
    echo.
    echo The value is being injected from somewhere other than the
    echo current/user environment cleaned above.
    echo Backup: %OMX_FIX_BACKUP%
    echo.
    del /q "%OMX_FIX_DOCTOR%" >nul 2>&1
    exit /b 30
)

echo ============================================================
echo [SUCCESS] NConnect is no longer bound to study-2/foreign cwd.
echo ============================================================
echo.
echo Launching OMX in:
echo   %CD%
echo.

del /q "%OMX_FIX_DOCTOR%" >nul 2>&1

omx
set "OMX_LAUNCH_RC=%ERRORLEVEL%"

echo.
echo ============================================================
echo OMX exited with code %OMX_LAUNCH_RC%
echo.
echo IMPORTANT:
echo Because this BAT was run from the SAME CMD and intentionally
echo uses no SETLOCAL, OMX_ROOT remains cleared in this CMD.
echo You may now type:
echo.
echo   omx
echo.
echo directly in this same window.
echo ============================================================

exit /b %OMX_LAUNCH_RC%
