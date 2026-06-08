@echo off
chcp 65001 >nul
setlocal

REM ============================================================
REM MESTIS 자동실행 프로그램
REM - 이 파일만 더블클릭하세요.
REM - 관리자 권한이 아니면 자동으로 관리자 권한 창을 다시 띄웁니다.
REM - mestis_auto.py는 이 파일과 같은 폴더에 있어야 합니다.
REM ============================================================

cd /d "%~dp0"
set "SCRIPT_PATH=%~dp0mestis_auto.py"

if not exist "%SCRIPT_PATH%" (
    echo.
    echo [실패] mestis_auto.py 파일을 찾지 못했습니다.
    echo [확인] MESTIS_자동실행.bat 파일과 mestis_auto.py 파일을 같은 폴더에 두세요.
    echo [현재 폴더] %~dp0
    echo.
    pause
    exit /b 1
)

net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo.
    echo [안내] 관리자 권한으로 자동 실행합니다.
    echo [안내] 잠시 후 뜨는 Windows 확인 창에서 '예'를 눌러주세요.
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ========================================
echo   MESTIS 자동화 시작
echo ========================================
echo [상태] 관리자 권한 확인 완료
echo [상태] 자동화 파일: %SCRIPT_PATH%
echo.

where python >nul 2>&1
if "%errorlevel%"=="0" (
    python "%SCRIPT_PATH%"
) else (
    where py >nul 2>&1
    if "%errorlevel%"=="0" (
        py -3 "%SCRIPT_PATH%"
    ) else (
        echo [실패] Python을 찾지 못했습니다.
        echo [확인] Python 설치 후 다시 실행해주세요.
        pause
        exit /b 1
    )
)

set "RUN_RESULT=%errorlevel%"
echo.
if "%RUN_RESULT%"=="0" (
    echo [완료] MESTIS 자동화가 종료되었습니다.
) else (
    echo [실패] MESTIS 자동화 중 오류가 발생했습니다.
    echo [확인] 위에 표시된 오류 내용을 확인해주세요.
)
echo.
pause
exit /b %RUN_RESULT%
