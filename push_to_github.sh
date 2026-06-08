#!/bin/bash
# 推送v2.0.0到GitHub

echo "================================"
echo "推送 HarrisReader v2.0.0"
echo "================================"
echo ""

echo "1. 推送代码到GitHub main分支..."
git push github main

if [ $? -eq 0 ]; then
    echo "✓ 代码推送成功"
else
    echo "✗ 代码推送失败"
    exit 1
fi

echo ""
echo "2. 推送标签v2.0.0..."
git push github v2.0.0

if [ $? -eq 0 ]; then
    echo "✓ 标签推送成功"
else
    echo "✗ 标签推送失败"
    exit 1
fi

echo ""
echo "================================"
echo "✅ 推送完成！"
echo "================================"
echo ""
echo "下一步："
echo "1. 访问 https://github.com/Ethan915025/HarrisReader/releases"
echo "2. 点击 'Draft a new release'"
echo "3. 选择标签 v2.0.0"
echo "4. 添加发布说明（参考PUSH_TO_GITHUB.md）"
echo "5. 发布Release"
echo ""
