@echo off
REM 自动安装依赖 - Windows 批处理脚本

echo ========================================
echo 发射机数据分析器 - 自动安装依赖
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

echo 正在安装依赖...
echo.

REM 运行 Python 安装脚本
python install_dependencies.py

REM 检查返回值
if errorlevel 1 (
    echo.
    echo 安装过程中出现错误
    pause
    exit /b 1
)

echo.
echo 安装完成！
pause
