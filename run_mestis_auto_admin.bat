@echo off
chcp 65001 >nul
setlocal

REM 이 배치파일이 있는 폴더를 기준으로 mestis_auto.py를 실행합니다.
cd /d "%~dp0"
set "SCRIPT_PATH=%~dp0mestis_auto.py"

if not exist "%SCRIPT_PATH%" (
    echo [실패] mestis_auto.py를 찾지 못했습니다: "%SCRIPT_PATH%"
    pause
    exit /b 1
)

REM 관리자 권한이 아니면 UAC 창을 띄워 이 배치파일을 관리자 권한으로 다시 실행합니다.
net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo [안내] 관리자 권한으로 다시 실행합니다. UAC 창에서 '예'를 눌러주세요.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo [안내] 관리자 권한 확인 완료.
echo [안내] MESTIS 자동화를 시작합니다.
echo.

where python >nul 2>&1
if "%errorlevel%"=="0" (
    python "%SCRIPT_PATH%"
) else (
    py -3 "%SCRIPT_PATH%"
)

set "RUN_RESULT=%errorlevel%"
echo.
if not "%RUN_RESULT%"=="0" (
    echo [실패] 자동화 실행 중 오류가 발생했습니다. 위 로그를 확인해주세요.
) else (
    echo [완료] 자동화 실행이 종료되었습니다.
)

pause
exit /b %RUN_RESULT%
