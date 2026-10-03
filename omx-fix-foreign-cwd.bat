@echo off
rem ============================================================
rem OMX foreign-cwd permanent cleanup for Windows CMD
rem
rem What it does:
rem   1) Shows current OMX control-plane variables
rem   2) Backs up user-level environment values
rem   3) Removes only project/session-root binding variables
rem      from the CURRENT CMD and HKCU user environment
rem   4) Does NOT delete session.json
rem   5) Does NOT kill any PID
rem   6) Runs omx doctor
rem   7) Launches omx if foreign-cwd is gone
rem
rem Run this from the project directory, e.g.:
rem   C:\dev\NConnect> C:\path\omx-fix-foreign-cwd.bat
rem ============================================================

title OMX foreign-cwd permanent cleanup

echo.
echo ============================================================
echo OMX foreign-cwd permanent cleanup
echo ============================================================
echo Project directory: %CD%
echo.

where omx >nul 2>&1
if errorlevel 1 (
    echo [ERROR] omx was not found in PATH.
    exit /b 10
)

rem ------------------------------------------------------------
rem Timestamp for backup
rem ------------------------------------------------------------
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "OMX_TS=%%I"
set "OMX_BACKUP=%USERPROFILE%\omx-env-backup-%OMX_TS%.txt"

echo [INFO] Backup file:
echo        %OMX_BACKUP%
echo.

(
    echo OMX environment backup
    echo Date: %DATE% %TIME%
    echo Project: %CD%
    echo.
    echo === Current process values ===
    set OMX_ 2^>nul
    echo.
    echo === User environment registry values ===
    reg query HKCU\Environment /v OMX_ROOT 2^>nul
    reg query HKCU\Environment /v OMX_STATE_ROOT 2^>nul
    reg query HKCU\Environment /v OMX_TEAM_STATE_ROOT 2^>nul
    reg query HKCU\Environment /v OMX_SOURCE_CWD 2^>nul
    echo.
    echo === Machine environment registry values ===
    reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v OMX_ROOT 2^>nul
    reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v OMX_STATE_ROOT 2^>nul
    reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v OMX_TEAM_STATE_ROOT 2^>nul
    reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v OMX_SOURCE_CWD 2^>nul
) > "%OMX_BACKUP%"

echo [BEFORE] Current OMX variables:
set OMX_ 2>nul
if errorlevel 1 echo   (none)
echo.

rem ------------------------------------------------------------
rem Clear CURRENT CMD variables.
rem Because this BAT does not use SETLOCAL, these changes remain
rem in the CMD window that called the BAT.
rem ------------------------------------------------------------
set "OMX_ROOT="
set "OMX_STATE_ROOT="
set "OMX_TEAM_STATE_ROOT="
set "OMX_SOURCE_CWD="

echo [OK] Cleared current CMD values:
echo      OMX_ROOT
echo      OMX_STATE_ROOT
echo      OMX_TEAM_STATE_ROOT
echo      OMX_SOURCE_CWD
echo.

rem ------------------------------------------------------------
rem Remove same variables from USER environment only.
rem Do not touch machine-level values automatically.
rem ------------------------------------------------------------
for %%V in (OMX_ROOT OMX_STATE_ROOT OMX_TEAM_STATE_ROOT OMX_SOURCE_CWD) do (
    reg query HKCU\Environment /v %%V >nul 2>&1
    if not errorlevel 1 (
        reg delete HKCU\Environment /v %%V /f >nul 2>&1
        if errorlevel 1 (
            echo [WARN] Could not remove user environment variable %%V
        ) else (
            echo [OK] Removed persistent user variable: %%V
        )
    )
)

echo.

rem ------------------------------------------------------------
rem Warn about machine-level variables if any exist.
rem ------------------------------------------------------------
set "OMX_MACHINE_FOUND="
for %%V in (OMX_ROOT OMX_STATE_ROOT OMX_TEAM_STATE_ROOT OMX_SOURCE_CWD) do (
    reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v %%V >nul 2>&1
    if not errorlevel 1 (
        echo [WARN] Machine-level variable exists: %%V
        set "OMX_MACHINE_FOUND=1"
    )
)

if defined OMX_MACHINE_FOUND (
    echo.
    echo [WARN] One or more OMX binding variables exist at MACHINE scope.
    echo        This BAT intentionally did NOT remove them.
    echo        If foreign-cwd remains, run an elevated diagnostic.
    echo.
)

rem ------------------------------------------------------------
rem Show after state
rem ------------------------------------------------------------
echo [AFTER] Current CMD OMX variables:
set OMX_ 2>nul
if errorlevel 1 echo   (none)
echo.

rem ------------------------------------------------------------
rem Diagnose with clean environment
rem ------------------------------------------------------------
set "OMX_DOCTOR_TMP=%TEMP%\omx_doctor_foreign_fix_%RANDOM%_%RANDOM%.txt"

echo ============================================================
echo Running: omx doctor
echo ============================================================
omx doctor > "%OMX_DOCTOR_TMP%" 2>&1
set "OMX_DOCTOR_RC=%ERRORLEVEL%"
type "%OMX_DOCTOR_TMP%"
echo.

findstr /I /C:"foreign-cwd" "%OMX_DOCTOR_TMP%" >nul 2>&1
if not errorlevel 1 (
    echo ============================================================
    echo [NOT FIXED] foreign-cwd is still reported.
    echo ============================================================
    echo.
    echo No session files were deleted.
    echo Backup:
    echo   %OMX_BACKUP%
    echo.
    echo Check whether a machine-level variable or startup script
    echo is recreating OMX_ROOT / OMX_STATE_ROOT / OMX_SOURCE_CWD.
    del /q "%OMX_DOCTOR_TMP%" >nul 2>&1
    exit /b 20
)

echo ============================================================
echo [SUCCESS] foreign-cwd is no longer reported by omx doctor.
echo ============================================================
echo.
echo Environment backup:
echo   %OMX_BACKUP%
echo.
echo Launching OMX from:
echo   %CD%
echo.

del /q "%OMX_DOCTOR_TMP%" >nul 2>&1
omx
exit /b %ERRORLEVEL%
