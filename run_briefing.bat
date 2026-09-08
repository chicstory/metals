@echo off
setlocal
cd /d "%~dp0"
python -u "%~dp0metal_news_briefing.py" %*
echo.
pause
