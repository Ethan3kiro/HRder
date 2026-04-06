@echo off
REM HarrisReader Windows 打包脚本
REM 用于在本地打包成 .exe 文件

echo ========================================
echo HarrisReader Windows 打包工具
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [1/5] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [安装] PyInstaller 未安装，正在安装...
    pip install pyinstaller
)

echo.
echo [2/5] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo [3/5] 开始打包...
pyinstaller --name="HarrisReader" ^
    --windowed ^
    --onefile ^
    --add-data="config;config" ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.QtCharts ^
    --hidden-import=pandas ^
    --hidden-import=numpy ^
    --hidden-import=matplotlib ^
    --hidden-import=PIL ^
    --hidden-import=pytesseract ^
    --hidden-import=openpyxl ^
    --hidden-import=xlsxwriter ^
    --hidden-import=requests ^
    --collect-all=PyQt6 ^
    --collect-all=matplotlib ^
    --exclude-module=pytest ^
    --exclude-module=hypothesis ^
    --exclude-module=tkinter ^
    --clean ^
    --noconfirm ^
    main_gui.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo [4/5] 创建发布包...
if not exist release mkdir release
copy dist\HarrisReader.exe release\
copy README.md release\
copy "如何使用API识别.md" release\ 2>nul
copy "API密钥配置快速参考.txt" release\ 2>nul
if exist config xcopy /E /I /Y config release\config
if exist examples xcopy /E /I /Y examples release\examples

echo.
echo [5/5] 创建 ZIP 压缩包...
powershell -Command "Compress-Archive -Path release\* -DestinationPath HarrisReader-Windows.zip -Force"

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置: dist\HarrisReader.exe
echo 发布包位置: release\
echo ZIP 压缩包: HarrisReader-Windows.zip
echo.
echo 文件大小:
dir /s dist\HarrisReader.exe | find "HarrisReader.exe"
echo.
pause
