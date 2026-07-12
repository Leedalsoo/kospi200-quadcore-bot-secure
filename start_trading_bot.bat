@echo off
:: [①사유]: 윈도우 환경에서의 시스템 자동 부팅 및 무결성 검증.
:: [②방어 기제 #102, #212]: 부팅 전 통합 테스트(pytest) 강제 수행.

SET PROJECT_ROOT=%~dp0
SET LOG_DIR=%PROJECT_ROOT%logs
SET PYTHON_CMD=python

:: 1. 필수 디렉토리 존재 확인
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: 2. [방어 기제 #102] 부팅 전 무결성 검증 (통합 테스트)
echo --- System Integrity Check: Running Integration Tests ---
%PYTHON_CMD% -m pytest "%PROJECT_ROOT%tests\integration_tests.py"

:: 테스트 결과가 0(성공)이 아니면 시스템 부팅 중단
if %ERRORLEVEL% NEQ 0 (
    echo CRITICAL: Integration tests failed. Bot will not start.
    pause
    exit /b 1
)

echo --- Integration Tests Passed: Booting Strategy Bot ---

:: 3. 부팅 (로그 파일에 리다이렉션)
:: %DATE%를 이용해 날짜별 로그 파일 생성
echo --- Bot started at %DATE% %TIME% ---
start /B %PYTHON_CMD% -u "%PROJECT_ROOT%main.py" > "%LOG_DIR%\system_%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%.log" 2>&1

echo Bot is running in background. Logs are directed to %LOG_DIR%
pause

