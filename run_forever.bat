@echo off
cls
echo Starting Dormant Bitcoin Hunter loop...
echo Press [q] or [Ctrl+C] to stop.
echo.

:loop
python hunt.py
if errorlevel 1 (
    echo.
    echo Hunter stopped by user.
    exit /b 0
)
timeout /t 1 /nobreak >nul 2>&1
goto loop
