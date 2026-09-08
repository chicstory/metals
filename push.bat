@echo off
cd /d "%~dp0"
echo ========================================================
echo   Pushing ThePathLab Metals to GitHub...
echo ========================================================
git push -u origin main
echo.
echo ========================================================
pause
