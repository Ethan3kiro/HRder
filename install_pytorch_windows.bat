@echo off
REM Windows PyTorch 安装脚本
REM 适用于 CPU 版本的 PyTorch

echo ========================================
echo PyTorch 安装脚本 (Windows)
echo ========================================
echo.

echo 检测 Python 版本...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python
    echo 请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo.
echo 正在安装 PyTorch (CPU 版本)...
echo 这可能需要几分钟时间，请耐心等待...
echo.

REM 使用官方推荐的安装命令（CPU版本）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

if errorlevel 1 (
    echo.
    echo ========================================
    echo 安装失败！尝试备用方案...
    echo ========================================
    echo.
    
    REM 备用方案：使用清华镜像
    pip install torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    if errorlevel 1 (
        echo.
        echo ========================================
        echo 所有安装方案都失败了
        echo ========================================
        echo.
        echo 请手动访问 PyTorch 官网获取安装命令：
        echo https://pytorch.org/get-started/locally/
        echo.
        echo 选择：
        echo - PyTorch Build: Stable
        echo - Your OS: Windows
        echo - Package: Pip
        echo - Language: Python
        echo - Compute Platform: CPU
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo 验证安装...
echo ========================================
python -c "import torch; print('PyTorch 版本:', torch.__version__); print('CUDA 可用:', torch.cuda.is_available())"

if errorlevel 1 (
    echo 验证失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo PyTorch 安装成功！
echo ========================================
echo.
echo 现在可以使用辅助录入功能了
echo 但首先需要训练模型，请参考：
echo - QUICK_START_DL_TRAINING.md
echo.
pause
