@echo off
cd /d "%~dp0"
chcp 65001 > nul

echo ========================================================
echo   ThePathLab 작업 스케줄러 등록 (평일 월-금 09:30)
echo ========================================================
powershell -ExecutionPolicy Bypass -File "%~dp0register_scheduler.ps1"
pause
