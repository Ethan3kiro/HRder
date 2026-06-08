#!/usr/bin/env python3
"""
可视化坐标标注：在图像上绘制所有标注的区域
"""
import cv2
import json
from pathlib import Path

print("="*70)
print("可视化坐标标注")
print("="*70)
print()

# 加载坐标
coords_file = Path('config/template_coordinates.json')
with open(coords_file, 'r', encoding='utf-8') as f:
    coords = json.load(f)

# 加载图像
image_path = Path('911-20251016.jpg')
image = cv2.imread(str(image_path))
if image is None:
    print(f"✗ 无法读取图像: {image_path}")
    exit(1)

# 创建副本用于绘制
vis_image = image.copy()

# 颜色定义
COLOR_SUCCESS = (0, 255, 0)  # 绿色 - 识别成功
COLOR_FAIL = (0, 0, 255)     # 红色 - 识别失败
COLOR_TEXT = (255, 255, 255)  # 白色文字

# 从上一次测试结果确定成功的项
successful_items = {
    'BZ', 'DZ', 'AB', 'ABCD',
    'Z-Plane-A-Current-3', 'Z-Plane-A-Current-4',
    'Z-Plane-A-Current-5', 'Z-Plane-A-Current-6',
    'Z-Plane-A-Current-7', 'Z-Plane-A-Current-8',
    'Z-Plane-A-ISOTemp-1'
}

# 绘制每个区域
for idx, (item_name, coord_list) in enumerate(coords.items(), 1):
    if isinstance(coord_list, list) and len(coord_list) == 4:
        x1, y1, x2, y2 = coord_list
        
        # 选择颜色
        color = COLOR_SUCCESS if item_name in successful_items else COLOR_FAIL
        
        # 绘制矩形
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
        
        # 绘制序号
        label = f"{idx}"
        font_scale = 0.4
        thickness = 1
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # 绘制文字背景
        cv2.rectangle(vis_image, (x1, y1 - th - 4), (x1 + tw + 4, y1), color, -1)
        
        # 绘制文字
        cv2.putText(vis_image, label, (x1 + 2, y1 - 2),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLOR_TEXT, thickness)

# 添加图例
legend_y = 20
cv2.putText(vis_image, "Green = Success, Red = Failed", (10, legend_y),
           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

# 保存结果
output_path = Path('coordinate_visualization.png')
cv2.imwrite(str(output_path), vis_image)

print(f"✓ 可视化图像已保存: {output_path}")
print()
print("图例：")
print("  🟢 绿色边框 = 识别成功")
print("  🔴 红色边框 = 识别失败")
print()
print("失败的区域：")
for idx, (item_name, coord_list) in enumerate(coords.items(), 1):
    if item_name not in successful_items:
        print(f"  {idx:2d}. {item_name:30s} - 坐标: {coord_list}")

print()
print("💡 建议：")
print("  1. 打开 coordinate_visualization.png 查看标注区域")
print("  2. 对于红色区域，检查坐标是否准确框选了数据")
print("  3. 使用坐标标定工具重新标注失败的区域")
print()
print("="*70)
