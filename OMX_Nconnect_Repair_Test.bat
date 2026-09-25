@echo off
setlocal
title OMX Repair and Test - Nconnect

echo ==========================================
echo   OMX Repair and Test - C:\dev\Nconnect
echo ==========================================
echo.

cd /d C:\dev\Nconnect
if errorlevel 1 (
    echo [ERROR] C:\dev\Nconnect 폴더로 이동하지 못했습니다.
    echo 경로를 확인해 주세요.
    pause
    exit /b 1
)

echo [1/4] OMX setup 갱신...
echo.
call omx setup --force
if errorlevel 1 (
    echo.
    echo [ERROR] omx setup --force 실행 실패
    pause
    exit /b 1
)

echo.
echo [2/4] OMX doctor 검사...
echo.
call omx doctor
if errorlevel 1 (
    echo.
    echo [WARNING] omx doctor가 오류 코드를 반환했습니다.
    echo 위 출력 내용을 확인해 주세요.
)

echo.
echo [3/4] Codex 로그인 상태 확인...
echo.
call codex login status
if errorlevel 1 (
    echo.
    echo [WARNING] Codex 로그인 상태 확인에 실패했습니다.
    echo 필요하면 codex login 을 실행해 주세요.
)

echo.
echo [4/4] OMX 실제 실행 테스트...
echo.
call omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"
if errorlevel 1 (
    echo.
    echo [ERROR] OMX 실제 실행 테스트 실패
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   모든 작업이 완료되었습니다.
echo   마지막 출력에 OMX-EXEC-OK 가 보이면 정상입니다.
echo ==========================================
echo.
pause
endlocal
