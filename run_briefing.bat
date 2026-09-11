@echo off
setlocal
cd /d "%~dp0"
chcp 65001 > nul

echo =======================================================
echo   [ThePathLab] 9대 금속원자재 일일 통합 브리핑 실행
echo =======================================================
python -u "%~dp0metal_news_briefing.py" %*

if %ERRORLEVEL% NEQ 0 goto ERROR_HANDLER

echo.
echo =======================================================
echo   [완료] 로컬 대시보드 및 리포트 생성이 완료되었습니다.
echo =======================================================
set /p "AUTO_PUSH=GitHub 웹사이트에 지금 바로 배포하시겠습니까? (Y/n, 기본: Y): "
if /i "%AUTO_PUSH%"=="n" goto SKIP_PUSH

echo.
echo [안내] metals GitHub 웹사이트로 배포 진행 중...
git add index.html latest.json sitemap.xml rss.xml robots.txt resources/
git commit -m "Auto update daily briefing" > nul 2>&1
git push origin main
echo.
echo =======================================================
echo   [metals 배포 완료] https://chicstory.github.io/metals/
echo =======================================================

:: 메인 포털(chicstory.github.io) 자동 동기화 및 배포
set "PORTAL_DIR=%~dp0..\chicstory.github.io"
if exist "%PORTAL_DIR%\index.html" (
    echo.
    echo [안내] 메인 포털(chicstory.github.io) 배포 진행 중...
    pushd "%PORTAL_DIR%"
    git add index.html sitemap.xml rss.xml robots.txt
    git commit -m "Auto sync portal daily metal briefing & SEO: %date%" > nul 2>&1
    git push origin main
    popd
    echo =======================================================
    echo   [포털 배포 완료] https://chicstory.github.io/
    echo =======================================================
)

:: 자동차 이슈(autoissue) SEO 피드 자동 배포 (피드 변경 시)
set "AUTOISSUE_DIR=%~dp0..\autoissue"
if exist "%AUTOISSUE_DIR%\index.html" (
    pushd "%AUTOISSUE_DIR%"
    git status --porcelain | findstr /R "sitemap.xml rss.xml robots.txt" > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [안내] autoissue SEO 피드 배포 진행 중...
        git add sitemap.xml rss.xml robots.txt
        git commit -m "Auto sync autoissue SEO feeds: %date%" > nul 2>&1
        git push origin main
        echo =======================================================
        echo   [autoissue 배포 완료] https://chicstory.github.io/autoissue/
        echo =======================================================
    )
    popd
)
goto END

:SKIP_PUSH
echo.
echo 배포를 건너뛰었습니다. 로컬 파일(index.html)을 먼저 확인하시고,
echo 준비되셨을 때 push.bat 을 실행하시면 언제든 사이트에 반영됩니다.
goto END

:ERROR_HANDLER
echo.
echo [경고] 브리핑 생성 중 오류가 발생했습니다.
pause
exit /b %ERRORLEVEL%

:END
echo.
pause
