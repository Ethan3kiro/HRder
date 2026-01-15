@echo off
REM Harris Reader - Windows Startup Script

echo ========================================
echo Harris Reader
echo ========================================
echo.

echo Starting application...
echo.

REM Start GUI using py launcher
py main_gui.py

REM If error occurs, pause to view error messages
if errorlevel 1 (
    echo.
    echo Startup failed, please check error messages above
    echo.
    pause
)
