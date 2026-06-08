@echo off
REM HarrisReader v2.0.0 - 简化打包脚本
REM 在Windows 10系统上运行此脚本

echo ================================================
echo  HarrisReader v2.0.0 Windows EXE 打包工具
echo ================================================
echo.

REM 检查Python
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python！
    echo.
    echo 请先安装Python 3.9-3.11：
    echo https://www.python.org/downloads/
    echo.
    echo 安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

python --version
echo ✓ Python已安装
echo.

REM 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] pip未找到
    pause
    exit /b 1
)
echo ✓ pip已安装
echo.

REM 安装/更新依赖
echo [2/6] 安装项目依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo ✓ 依赖安装完成
echo.

REM 安装PyInstaller
echo [3/6] 安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller安装失败
    pause
    exit /b 1
)
echo ✓ PyInstaller已安装
echo.

REM 检查Tesseract
echo [4/6] 检查Tesseract OCR...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo ✓ Tesseract已安装
) else (
    echo [警告] 未找到Tesseract OCR
    echo.
    echo 请从以下地址下载安装：
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo 安装后程序才能使用模板OCR识别功能
    echo.
    pause
)
echo.

REM 清理旧文件
echo [5/6] 清理旧的构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "HarrisReader.spec" del HarrisReader.spec
echo ✓ 清理完成
echo.

REM 生成spec文件
echo [6/6] 生成打包配置...
python build_spec.py
if errorlevel 1 (
    echo [错误] 配置生成失败
    pause
    exit /b 1
)
echo ✓ 配置已生成
echo.

REM 开始打包
echo ================================================
echo  开始打包（这可能需要5-10分钟）...
echo ================================================
echo.
pyinstaller HarrisReader.spec
if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    echo.
    echo 请检查错误信息并解决后重试
    pause
    exit /b 1
)

echo.
echo ================================================
echo  检查打包结果...
echo ================================================
echo.

if exist "dist\HarrisReader\HarrisReader.exe" (
    echo ✓ 打包成功！
    echo.
    echo 输出位置: dist\HarrisReader\
    echo 主程序: HarrisReader.exe
    echo.
    echo ================================================
    echo  下一步操作：
    echo ================================================
    echo.
    echo 1. 测试程序：
    echo    cd dist\HarrisReader
    echo    HarrisReader.exe
    echo.
    echo 2. 如果程序正常运行，可以压缩发布：
    echo    - 右键 dist\HarrisReader 文件夹
    echo    - 发送到 → 压缩(zipped)文件夹
    echo    - 重命名为 HarrisReader-v2.0.0-Windows.zip
    echo.
    echo 3. 复制到目标电脑使用
    echo.
) else (
    echo [错误] 未找到打包后的EXE文件
    echo.
    echo 请检查打包过程中的错误信息
    echo.
)

pause
