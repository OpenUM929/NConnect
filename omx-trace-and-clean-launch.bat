@echo off
rem ============================================================
rem OMX ROOT SOURCE TRACE + CLEAN LAUNCH
rem Windows CMD / OMX 0.21.x
rem
rem Purpose:
rem   - Find where an unexpected OMX_ROOT is being injected
rem   - Remove current/user-scoped OMX binding variables safely
rem   - Bypass a DOSKEY "omx" macro
rem   - Call the real npm omx.cmd directly
rem   - Never delete session.json
rem   - Never kill a PID
rem ============================================================

title OMX ROOT SOURCE TRACE + CLEAN LAUNCH

echo.
echo ============================================================
echo OMX ROOT SOURCE TRACE + CLEAN LAUNCH
echo ============================================================
echo Current project: %CD%
echo.

where omx >nul 2>&1
if errorlevel 1 (
    echo [ERROR] omx was not found in PATH.
    exit /b 10
)

rem ---- timestamp / log ----------------------------------------
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "OMX_TS=%%I"
set "OMX_LOG=%USERPROFILE%\omx-root-trace-%OMX_TS%.txt"
set "OMX_DOCTOR_TMP=%TEMP%\omx-doctor-%RANDOM%-%RANDOM%.txt"
set "OMX_MACRO_TMP=%TEMP%\omx-macros-%RANDOM%-%RANDOM%.txt"

echo [INFO] Trace log:
echo        %OMX_LOG%
echo.

rem ---- current environment -----------------------------------
echo [1] Current CMD environment
echo ------------------------------------------------------------
echo OMX_ROOT=%OMX_ROOT%
echo OMX_STATE_ROOT=%OMX_STATE_ROOT%
echo OMX_TEAM_STATE_ROOT=%OMX_TEAM_STATE_ROOT%
echo OMX_SOURCE_CWD=%OMX_SOURCE_CWD%
echo.

(
  echo ============================================================
  echo OMX ROOT TRACE
  echo Date: %DATE% %TIME%
  echo Project: %CD%
  echo ============================================================
  echo.
  echo [CURRENT PROCESS]
  set OMX_ 2^>nul
  echo.
) > "%OMX_LOG%"

rem ---- persistent environment using PowerShell ----------------
echo [2] Persistent Windows environment
echo ------------------------------------------------------------
powershell -NoProfile -Command ^
  "$names='OMX_ROOT','OMX_STATE_ROOT','OMX_TEAM_STATE_ROOT','OMX_SOURCE_CWD','OMX_SESSION_ID','OMX_TEAM_LEADER_CWD';" ^
  "foreach($scope in 'User','Machine'){ Write-Host ('['+$scope+']'); foreach($n in $names){ $v=[Environment]::GetEnvironmentVariable($n,$scope); if($null -ne $v -and $v -ne ''){ Write-Host ($n+'='+$v) } }; Write-Host '' }"
echo.

powershell -NoProfile -Command ^
  "$names='OMX_ROOT','OMX_STATE_ROOT','OMX_TEAM_STATE_ROOT','OMX_SOURCE_CWD','OMX_SESSION_ID','OMX_TEAM_LEADER_CWD';" ^
  "Add-Content -LiteralPath '%OMX_LOG%' -Value '[PERSISTENT ENVIRONMENT]';" ^
  "foreach($scope in 'User','Machine'){ Add-Content -LiteralPath '%OMX_LOG%' -Value ('['+$scope+']'); foreach($n in $names){ $v=[Environment]::GetEnvironmentVariable($n,$scope); if($null -ne $v -and $v -ne ''){ Add-Content -LiteralPath '%OMX_LOG%' -Value ($n+'='+$v) } }; Add-Content -LiteralPath '%OMX_LOG%' -Value '' }"

rem ---- DOSKEY macro ------------------------------------------
echo [3] DOSKEY macro check
echo ------------------------------------------------------------
doskey /macros > "%OMX_MACRO_TMP%" 2>nul
findstr /I /B /C:"omx=" "%OMX_MACRO_TMP%"
if errorlevel 1 (
    echo [OK] No interactive DOSKEY macro named "omx" was found.
) else (
    echo [WARN] An interactive DOSKEY macro named "omx" exists.
    echo        It can behave differently from OMX calls inside BAT files.
    echo        The macro is backed up in the trace log and will be
    echo        disabled in this CMD console only.
    type "%OMX_MACRO_TMP%" >> "%OMX_LOG%"
    doskey omx=
)
echo.

rem ---- CMD AutoRun -------------------------------------------
echo [4] Command Processor AutoRun check
echo ------------------------------------------------------------
powershell -NoProfile -Command ^
  "$paths=@('HKCU:\Software\Microsoft\Command Processor','HKLM:\Software\Microsoft\Command Processor');" ^
  "foreach($p in $paths){ try{$v=(Get-ItemProperty -Path $p -Name AutoRun -ErrorAction Stop).AutoRun; if($v){Write-Host ($p+' AutoRun='+$v)}}catch{} }"
echo.

powershell -NoProfile -Command ^
  "$paths=@('HKCU:\Software\Microsoft\Command Processor','HKLM:\Software\Microsoft\Command Processor');" ^
  "foreach($p in $paths){ try{$v=(Get-ItemProperty -Path $p -Name AutoRun -ErrorAction Stop).AutoRun; if($v){Add-Content -LiteralPath '%OMX_LOG%' -Value ($p+' AutoRun='+$v)}}catch{} }"

rem ---- resolve real omx.cmd ----------------------------------
echo [5] Resolve real OMX launcher
echo ------------------------------------------------------------
set "OMX_CMD="
for /f "delims=" %%I in ('where omx.cmd 2^>nul') do if not defined OMX_CMD set "OMX_CMD=%%I"

if not defined OMX_CMD (
    echo [ERROR] Could not resolve omx.cmd.
    echo.
    where omx
    del /q "%OMX_MACRO_TMP%" >nul 2>&1
    exit /b 20
)

echo [OK] Real launcher:
echo      %OMX_CMD%
echo.
echo [INFO] Lines in omx.cmd mentioning OMX_ROOT/state/instances:
findstr /I /N /C:"OMX_ROOT" /C:"OMX_STATE_ROOT" /C:"OMX_SOURCE_CWD" /C:"instances" "%OMX_CMD%" 2>nul
if errorlevel 1 echo      (none)
echo.

(
  echo [WHERE OMX]
  where omx 2^>nul
  echo.
  echo [REAL OMX CMD]
  echo %OMX_CMD%
  echo.
  echo [OMX.CMD MATCHES]
  findstr /I /N /C:"OMX_ROOT" /C:"OMX_STATE_ROOT" /C:"OMX_SOURCE_CWD" /C:"instances" "%OMX_CMD%" 2^>nul
  echo.
) >> "%OMX_LOG%"

rem ---- clear current process bindings ------------------------
echo [6] Clear project/session binding variables
echo ------------------------------------------------------------
set "OMX_ROOT="
set "OMX_STATE_ROOT="
set "OMX_TEAM_STATE_ROOT="
set "OMX_SOURCE_CWD="
set "OMX_SESSION_ID="
set "OMX_TEAM_LEADER_CWD="

rem Remove USER-scoped persistent values only.
powershell -NoProfile -Command ^
  "$names='OMX_ROOT','OMX_STATE_ROOT','OMX_TEAM_STATE_ROOT','OMX_SOURCE_CWD','OMX_SESSION_ID','OMX_TEAM_LEADER_CWD';" ^
  "foreach($n in $names){ [Environment]::SetEnvironmentVariable($n,$null,'User') }"

echo [OK] Current CMD variables cleared.
echo [OK] User-scoped persistent OMX binding variables cleared.
echo [INFO] Machine-scoped variables were NOT modified.
echo.

rem ---- direct doctor: bypass DOSKEY macro --------------------
echo [7] Direct doctor using the real omx.cmd
echo ------------------------------------------------------------
call "%OMX_CMD%" doctor > "%OMX_DOCTOR_TMP%" 2>&1
set "OMX_DOCTOR_RC=%ERRORLEVEL%"
type "%OMX_DOCTOR_TMP%"
echo.
type "%OMX_DOCTOR_TMP%" >> "%OMX_LOG%"

findstr /I /C:"src=omx-root-env" /C:"ptr=foreign" /C:"foreign-cwd" "%OMX_DOCTOR_TMP%" >nul 2>&1
if not errorlevel 1 (
    echo ============================================================
    echo [STILL FOREIGN]
    echo ============================================================
    echo The real omx.cmd still receives/injects an external OMX root.
    echo This is NOT a stale session.json problem.
    echo.
    echo Trace saved to:
    echo   %OMX_LOG%
    echo.
    echo Please use that trace to identify the remaining injector.
    echo No session file was deleted and no process was killed.
    del /q "%OMX_DOCTOR_TMP%" "%OMX_MACRO_TMP%" >nul 2>&1
    exit /b 30
)

echo ============================================================
echo [SUCCESS]
echo The real OMX launcher no longer reports foreign-cwd.
echo ============================================================
echo.
echo Trace saved to:
echo   %OMX_LOG%
echo.
echo Launching the REAL OMX command directly, bypassing DOSKEY...
echo.

del /q "%OMX_DOCTOR_TMP%" "%OMX_MACRO_TMP%" >nul 2>&1
call "%OMX_CMD%"
exit /b %ERRORLEVEL%
