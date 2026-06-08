#!/usr/bin/env python3
"""
快速修复失败坐标的标注工具
只需要重新标注5个失败的区域
"""
import cv2
import json
from pathlib import Path

print("="*70)
print("快速修复失败坐标")
print("="*70)
print()

# 失败的区域列表
failed_items = {
    'AZ': [218, 227, 244, 243],
    'CZ': [313, 227, 341, 244],
    'CD': [456, 227, 486, 244],
    'Z-Plane-A-Current-1': [43, 292, 81, 310],
    'Z-Plane-A-Current-2': [43, 316, 80, 333],
}

# 加载图像
image_path = Path('911-20251016.jpg')
image = cv2.imread(str(image_path))
if image is None:
    print(f"✗ 无法读取图像: {image_path}")
    exit(1)

print(f"图像: {image_path}")
print(f"尺寸: {image.shape[1]} x {image.shape[0]}")
print()
print("需要修复的区域：")
for idx, (name, coords) in enumerate(failed_items.items(), 1):
    print(f"  {idx}. {name:30s} - 当前坐标: {coords}")
print()
print("-"*70)
print()
print("📝 操作说明：")
print()
print("1. 程序会依次显示每个失败区域的放大图")
print("2. 你可以看到当前标注的区域（红色框）")
print("3. 检查数字是否在框内，是否需要调整")
print("4. 按任意键继续下一个")
print()
print("⚠️  提示：")
print("  • 如果当前坐标看起来正确，可能是OCR参数问题")
print("  • 如果数字不在框内，需要重新标注")
print("  • 建议使用 tools/coordinate_calibrator.py 重新标注")
print()
print("-"*70)
print()

input("按回车键开始查看失败区域...")
print()

# 逐个显示失败区域
for idx, (name, coords) in enumerate(failed_items.items(), 1):
    x1, y1, x2, y2 = coords
    
    # 提取区域并放大
    margin = 20
    x1_exp = max(0, x1 - margin)
    y1_exp = max(0, y1 - margin)
    x2_exp = min(image.shape[1], x2 + margin)
    y2_exp = min(image.shape[0], y2 + margin)
    
    region = image[y1_exp:y2_exp, x1_exp:x2_exp].copy()
    
    # 在区域上绘制当前标注框（相对坐标）
    rel_x1 = x1 - x1_exp
    rel_y1 = y1 - y1_exp
    rel_x2 = x2 - x1_exp
    rel_y2 = y2 - y1_exp
    
    cv2.rectangle(region, (rel_x1, rel_y1), (rel_x2, rel_y2), (0, 0, 255), 2)
    
    # 放大显示
    scale = 3
    region_large = cv2.resize(region, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 添加标题
    title = f"[{idx}/5] {name}"
    cv2.putText(region_large, title, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # 添加坐标信息
    coord_text = f"Coords: {coords}"
    cv2.putText(region_large, coord_text, (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # 显示
    cv2.imshow('Failed Region', region_large)
    
    print(f"[{idx}/5] {name}")
    print(f"      当前坐标: {coords}")
    print(f"      → 检查红色框是否准确包含数字")
    print()
    
    key = cv2.waitKey(0)
    
    # ESC键退出
    if key == 27:
        break

cv2.destroyAllWindows()

print()
print("-"*70)
print()
print("📋 总结：")
print()
print("如果发现坐标不准确，请使用坐标标定工具重新标注：")
print()
print("  python3 tools/coordinate_calibrator.py 911-20251016.jpg")
print()
print("重新标注时：")
print("  1. 按 'L' 键加载现有坐标")
print("  2. 找到失败的项目，重新框选")
print("  3. 按 'S' 保存更新后的坐标")
print("  4. 运行 test_partial_recognition.py 验证")
print()
print("如果坐标看起来正确但仍识别失败，可能需要：")
print("  • 调整Tesseract参数")
print("  • 使用不同的预处理方法")
print("  • 增加字符白名单")
print()
print("="*70)
