@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
chcp 65001 > nul

set "LOG_FILE=%~dp0auto_briefing_log.txt"

echo ======================================================= >> "%LOG_FILE%"
echo [%date% %time%] ThePathLab 일일 자동 브리핑 작업 시작 >> "%LOG_FILE%"
echo ======================================================= >> "%LOG_FILE%"

:: 1. Ollama 실행 확인 및 미실행 시 백그라운드 시작
curl -s http://localhost:11434 > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] Ollama 서비스가 꺼져 있어 실행합니다... >> "%LOG_FILE%"
    start "" /b ollama serve > nul 2>&1
    :: Ollama 서버 기동 대기 (5초)
    timeout /t 5 /nobreak > nul
) else (
    echo [%date% %time%] Ollama 서비스가 이미 정상 작동 중입니다. >> "%LOG_FILE%"
)

:: 2. 원자재 브리핑 생성 실행
echo [%date% %time%] metal_news_briefing.py 실행 중... >> "%LOG_FILE%"
python -u "%~dp0metal_news_briefing.py" >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo. >> "%LOG_FILE%"
    echo [경고] [%date% %time%] 브리핑 생성 중 오류가 발생했습니다! 디버깅을 위해 PC를 끄지 않습니다. >> "%LOG_FILE%"
    exit /b %ERRORLEVEL%
)

:: 3. GitHub 웹사이트로 자동 배포 (Push)
echo [%date% %time%] 브리핑 생성 완료. GitHub 배포 진행 중... >> "%LOG_FILE%"
git add index.html latest.json sitemap.xml resources/ >> "%LOG_FILE%" 2>&1
git commit -m "Auto daily metal briefing: %date%" >> "%LOG_FILE%" 2>&1
git push origin main >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [경고] [%date% %time%] Git Push 실패! 네트워크 확인 필요. >> "%LOG_FILE%"
    exit /b %ERRORLEVEL%
)

echo [%date% %time%] [배포 완료] 전 세계 배포 완료! (https://chicstory.github.io/metals/) >> "%LOG_FILE%"

:: 3-1. 메인 포털(chicstory.github.io) 자동 동기화 및 배포
set "PORTAL_DIR=%~dp0..\chicstory.github.io"
if exist "%PORTAL_DIR%\index.html" (
    echo [%date% %time%] 메인 포털(chicstory.github.io) 자동 배포 진행 중... >> "%LOG_FILE%"
    pushd "%PORTAL_DIR%"
    git add index.html >> "%LOG_FILE%" 2>&1
    git commit -m "Auto sync portal daily metal briefing: %date%" >> "%LOG_FILE%" 2>&1
    git push origin main >> "%LOG_FILE%" 2>&1
    popd
    echo [%date% %time%] [포털 배포 완료] 메인 포털 동기화 완료! (https://chicstory.github.io/) >> "%LOG_FILE%"
)

:: 4. 30분(1800초) 뒤 PC 종료 예약
:: (취소하고 싶을 때는 명령 프롬프트나 실행창(Win+R)에서 shutdown /a 입력)
echo [%date% %time%] 30분(1800초) 후 PC 자동 종료가 예약되었습니다. >> "%LOG_FILE%"
shutdown /s /t 1800 /c "ThePathLab 원자재 브리핑 배포 완료: 30분 뒤 PC가 종료됩니다. (취소: shutdown /a)"

exit /b 0
