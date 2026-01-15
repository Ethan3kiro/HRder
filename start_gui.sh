#!/bin/bash
# 发射机数据分析器 - macOS/Linux 启动脚本

echo "========================================"
echo "发射机数据分析器"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    echo "请先安装 Python 3.9 或更高版本"
    exit 1
fi

echo "正在启动应用..."
echo ""

# 启动 GUI
python3 main_gui.py

# 如果出错，显示错误信息
if [ $? -ne 0 ]; then
    echo ""
    echo "启动失败，请检查错误信息"
    read -p "按 Enter 键退出..."
fi
