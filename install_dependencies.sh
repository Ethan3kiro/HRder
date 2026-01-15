#!/bin/bash
# 自动安装依赖 - macOS/Linux Shell 脚本

echo "========================================"
echo "发射机数据分析器 - 自动安装依赖"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    echo "请先安装 Python 3.9 或更高版本"
    exit 1
fi

echo "正在安装依赖..."
echo ""

# 运行 Python 安装脚本
python3 install_dependencies.py

# 检查返回值
if [ $? -ne 0 ]; then
    echo ""
    echo "安装过程中出现错误"
    exit 1
fi

echo ""
echo "安装完成！"
