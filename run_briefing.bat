@echo off
setlocal
cd /d "%~dp0"
chcp 65001 > nul

echo =======================================================
echo   🏭 ThePathLab 7대 금속원자재 일일 통합 브리핑 실행
echo =======================================================
python -u "%~dp0metal_news_briefing.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [경고] 브리핑 생성 중 오류가 발생했습니다.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =======================================================
echo   🌐 로컬 대시보드 및 리포트 생성이 완료되었습니다.
echo =======================================================
set /p "AUTO_PUSH=>> GitHub 웹사이트에 지금 바로 배포(Push)하시겠습니까? (Y/n, 기본: Y): "
if /i "%AUTO_PUSH%"=="n" (
    echo.
    echo 배포를 건너뛰었습니다. 로컬 파일(index.html)을 먼저 확인하시고,
    echo 준비되셨을 때 push.bat 을 실행하시면 언제든 사이트에 반영됩니다.
) else (
    echo.
    echo >> GitHub 웹사이트로 배포(Push) 진행 중...
    git add -A
    git commit -m "Auto update daily briefing" > nul 2>&1
    git push origin main
    echo.
    echo =======================================================
    echo   ✨ 전 세계 배포 완료!
    echo   🌐 공식 사이트: https://chicstory.github.io/metals/
    echo =======================================================
)
echo.
pause
