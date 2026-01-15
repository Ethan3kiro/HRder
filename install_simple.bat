@echo off
REM Simple installation script using py launcher

REM Change to script directory
cd /d "%~dp0"

echo ========================================
echo Harris Reader - Installing Dependencies
echo ========================================
echo.

echo Installing core dependencies...
py -m pip install -r requirements.txt

echo.
echo Installing GUI dependencies...
py -m pip install -r requirements-gui.txt

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To start the application, run:
echo   py main_gui.py
echo.
echo Or double-click: start_gui.bat
echo.
pause
