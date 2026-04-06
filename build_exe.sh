#!/bin/bash
# HarrisReader 打包脚本（Linux/macOS）

echo "========================================"
echo "HarrisReader 打包工具"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3"
    exit 1
fi

echo "[1/5] 检查依赖..."
if ! python3 -m pip show pyinstaller &> /dev/null; then
    echo "[安装] PyInstaller 未安装，正在安装..."
    python3 -m pip install pyinstaller
fi

echo ""
echo "[2/5] 清理旧文件..."
rm -rf build dist *.spec

echo ""
echo "[3/5] 开始打包..."
python3 -m PyInstaller \
    --name="HarrisReader" \
    --windowed \
    --onefile \
    --add-data="config:config" \
    --hidden-import=PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=PyQt6.QtCharts \
    --hidden-import=pandas \
    --hidden-import=numpy \
    --hidden-import=matplotlib \
    --hidden-import=PIL \
    --hidden-import=pytesseract \
    --hidden-import=openpyxl \
    --hidden-import=xlsxwriter \
    --hidden-import=requests \
    --collect-all=PyQt6 \
    --collect-all=matplotlib \
    --exclude-module=pytest \
    --exclude-module=hypothesis \
    --exclude-module=tkinter \
    --clean \
    --noconfirm \
    main_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 打包失败！"
    exit 1
fi

echo ""
echo "[4/5] 创建发布包..."
mkdir -p release
cp dist/HarrisReader release/
cp README.md release/
cp "如何使用API识别.md" release/ 2>/dev/null || true
cp "API密钥配置快速参考.txt" release/ 2>/dev/null || true
[ -d config ] && cp -r config release/
[ -d examples ] && cp -r examples release/

echo ""
echo "[5/5] 创建压缩包..."
cd release
tar -czf ../HarrisReader-$(uname -s)-$(uname -m).tar.gz *
cd ..

echo ""
echo "========================================"
echo "打包完成！"
echo "========================================"
echo ""
echo "可执行文件: dist/HarrisReader"
echo "发布包: release/"
echo "压缩包: HarrisReader-$(uname -s)-$(uname -m).tar.gz"
echo ""
ls -lh dist/HarrisReader
echo ""
