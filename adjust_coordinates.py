#!/usr/bin/env python3
"""
坐标调整工具 - 帮助可视化和调整提取区域的坐标

使用说明：
1. 运行此脚本：python adjust_coordinates.py <图片路径>
2. 脚本会在图像上绘制当前的提取区域
3. 根据显示的区域调整 src/ocr_extractor_v3.py 中的坐标配置
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def draw_regions(image_path: str):
    """在图像上绘制提取区域"""
    print("=" * 80)
    print("坐标调整工具")
    print("=" * 80)
    
    image_file = Path(image_path)
    
    if not image_file.exists():
        print(f"\n✗ 错误：图像文件不存在: {image_file}")
        return
    
    print(f"\n图像文件: {image_file}")
    
    # 加载图像
    image = Image.open(image_file)
    width, height = image.size
    
    print(f"图像尺寸: {width} x {height}")
    
    # 创建绘图对象
    draw = ImageDraw.Draw(image)
    
    # COMBINER 区域配置
    combiner_region = {
        'x': 0.25,
        'y': 0.25,
        'width': 0.50,
        'height': 0.08
    }
    
    # Z-Plane 区域配置
    zplane_regions = {
        'A': {'x': 0.02, 'y': 0.52, 'width': 0.23, 'height': 0.35},
        'B': {'x': 0.27, 'y': 0.52, 'width': 0.23, 'height': 0.35},
        'C': {'x': 0.52, 'y': 0.52, 'width': 0.23, 'height': 0.35},
        'D': {'x': 0.77, 'y': 0.52, 'width': 0.23, 'height': 0.35}
    }
    
    # 绘制 COMBINER 区域
    x1 = int(width * combiner_region['x'])
    y1 = int(height * combiner_region['y'])
    x2 = int(width * (combiner_region['x'] + combiner_region['width']))
    y2 = int(height * (combiner_region['y'] + combiner_region['height']))
    
    draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
    draw.text((x1 + 10, y1 + 10), "COMBINER", fill='red')
    
    print(f"\nCOMBINER 区域:")
    print(f"  左上角: ({x1}, {y1})")
    print(f"  右下角: ({x2}, {y2})")
    print(f"  尺寸: {x2-x1} x {y2-y1}")
    
    # 绘制 Z-Plane 区域
    colors = {'A': 'blue', 'B': 'green', 'C': 'orange', 'D': 'purple'}
    
    for module, region in zplane_regions.items():
        x1 = int(width * region['x'])
        y1 = int(height * region['y'])
        x2 = int(width * (region['x'] + region['width']))
        y2 = int(height * (region['y'] + region['height']))
        
        color = colors[module]
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        draw.text((x1 + 10, y1 + 10), f"Z-Plane {module}", fill=color)
        
        print(f"\nZ-Plane {module} 区域:")
        print(f"  左上角: ({x1}, {y1})")
        print(f"  右下角: ({x2}, {y2})")
        print(f"  尺寸: {x2-x1} x {y2-y1}")
    
    # 保存标注后的图像
    output_file = f"annotated_{image_file.name}"
    image.save(output_file)
    
    print(f"\n标注后的图像已保存到: {output_file}")
    print("\n请打开图像查看标注的区域是否正确。")
    print("如果区域不正确，请修改 src/ocr_extractor_v3.py 中的坐标配置。")
    
    print("\n" + "=" * 80)
    print("坐标配置说明:")
    print("=" * 80)
    print("""
坐标使用相对值（0.0 到 1.0），表示图像宽度/高度的百分比。

例如：
- x: 0.25 表示从图像左边界开始 25% 的位置
- y: 0.50 表示从图像上边界开始 50% 的位置
- width: 0.30 表示区域宽度为图像宽度的 30%
- height: 0.10 表示区域高度为图像高度的 10%

修改 src/ocr_extractor_v3.py 中的以下配置：

COMBINER_REGION = {
    'x': 0.25,      # 调整这个值
    'y': 0.25,      # 调整这个值
    'width': 0.50,  # 调整这个值
    'height': 0.08  # 调整这个值
}

ZPLANE_REGIONS = {
    'A': {'x': 0.02, 'y': 0.52, 'width': 0.23, 'height': 0.35},
    'B': {'x': 0.27, 'y': 0.52, 'width': 0.23, 'height': 0.35},
    'C': {'x': 0.52, 'y': 0.52, 'width': 0.23, 'height': 0.35},
    'D': {'x': 0.77, 'y': 0.52, 'width': 0.23, 'height': 0.35}
}
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python adjust_coordinates.py <图片路径>")
        print("\n示例:")
        print("  python adjust_coordinates.py screenshot.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    draw_regions(image_path)
