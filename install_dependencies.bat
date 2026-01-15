@echo off
chcp 65001 >nul
REM 自动安装依赖 - Windows 批处理脚本

echo ========================================
echo 发射机数据分析器 - 自动安装依赖
echo ========================================
echo.

REM 尝试多种方式查找 Python
set PYTHON_CMD=

REM 方法1: 尝试 python 命令
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :found_python
)

REM 方法2: 尝试 python3 命令
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :found_python
)

REM 方法3: 尝试 py 启动器
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto :found_python
)

REM 方法4: 检查常见安装路径
if exist "C:\Python39\python.exe" (
    set PYTHON_CMD=C:\Python39\python.exe
    goto :found_python
)
if exist "C:\Python310\python.exe" (
    set PYTHON_CMD=C:\Python310\python.exe
    goto :found_python
)
if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    goto :found_python
)
if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    goto :found_python
)

REM 方法5: 检查用户 AppData 路径
if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python39\python.exe
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    goto :found_python
)

REM 未找到 Python
echo 错误: 未找到 Python
echo.
echo 请先安装 Python 3.9 或更高版本
echo 下载地址: https://www.python.org/downloads/
echo.
echo 安装时请勾选 "Add Python to PATH" 选项
pause
exit /b 1

:found_python
echo 找到 Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

echo 正在安装依赖...
echo.

REM 运行 Python 安装脚本
%PYTHON_CMD% install_dependencies.py

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
