@echo off
REM 改进的安装脚本 - 修复常见问题
REM 适用于 Windows 系统

REM 设置 UTF-8 编码，避免中文乱码
chcp 65001 >nul 2>&1

REM 切换到脚本所在目录
cd /d "%~dp0"

echo ==========================================
echo Harris Reader - 安装依赖
echo ==========================================
echo.

REM 检查 Python 是否可用
py --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 找不到 Python
    echo 请先安装 Python 3.9 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/4] 检查 Python 版本...
py --version
echo.

echo [2/4] 升级 pip (避免版本问题)...
py -m pip install --upgrade pip
if errorlevel 1 (
    echo [警告] pip 升级失败，继续使用当前版本
)
echo.

echo [3/4] 安装核心依赖...
echo 使用清华镜像源加速下载...
py -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=100
if errorlevel 1 (
    echo.
    echo [错误] 核心依赖安装失败
    echo 尝试使用官方源重新安装...
    py -m pip install -r requirements.txt --default-timeout=100
    if errorlevel 1 (
        echo.
        echo [错误] 安装失败，请检查网络连接
        echo.
        pause
        exit /b 1
    )
)
echo.

echo [4/4] 安装 GUI 依赖...
py -m pip install -r requirements-gui.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=100
if errorlevel 1 (
    echo.
    echo [错误] GUI 依赖安装失败
    echo 尝试使用官方源重新安装...
    py -m pip install -r requirements-gui.txt --default-timeout=100
    if errorlevel 1 (
        echo.
        echo [错误] 安装失败，请检查网络连接
        echo.
        pause
        exit /b 1
    )
)
echo.

echo ==========================================
echo 安装完成！
echo ==========================================
echo.
echo 验证安装:
py verify_dependencies.py
echo.
echo 启动应用:
echo   方式1: 双击 start_gui.bat
echo   方式2: 运行命令 py main_gui.py
echo.
pause
