@echo off
REM 发射机数据分析器 - Windows 启动脚本

echo ========================================
echo 发射机数据分析器
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    echo 请先安装 Python 3.9 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 正在启动应用...
echo.

REM 启动 GUI
python main_gui.py

REM 如果出错，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo 启动失败，请检查错误信息
    pause
)
