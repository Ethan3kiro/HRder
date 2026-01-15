#!/usr/bin/env python3
"""
自动坐标提取工具
使用 OCR 自动检测文本位置，推算单元格坐标
"""

import cv2
import numpy as np
from pathlib import Path
import json
import pytesseract


def find_text_positions(image, texts):
    """在图像中查找文本位置"""
    # 使用 Tesseract OCR
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='eng')
    
    positions = {}
    for i, text in enumerate(data['text']):
        text = text.strip()
        if text in texts:
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            positions[text] = (x, y, w, h)
    
    return positions


def extract_coordinates_from_image(image_path):
    """从图像中自动提取坐标"""
    print("=" * 60)
    print("自动坐标提取")
    print("=" * 60)
    
    # 加载图像
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ 无法加载图像: {image_path}")
        return None
    
    print(f"\n✓ 图像已加载: {image_path.name}")
    print(f"  尺寸: {image.shape[1]} x {image.shape[0]}")
    
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 查找关键文本
    print("\n🔍 查找关键文本位置...")
    key_texts = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    try:
        positions = find_text_positions(gray, key_texts)
        
        if not positions:
            print("❌ 未找到关键文本")
            print("   可能需要手动标记坐标")
            return None
        
        print(f"✓ 找到 {len(positions)} 个文本位置")
        
        # 计算参数
        params = calculate_parameters_from_positions(positions)
        
        return params
        
    except Exception as e:
        print(f"❌ OCR 失败: {e}")
        print("   请使用交互式工具手动标记")
        return None


def calculate_parameters_from_positions(positions):
    """从文本位置计算坐标参数"""
    params = {}
    
    # COMBINER 区域
    if 'AZ' in positions and 'BZ' in positions:
        az_x, az_y, az_w, az_h = positions['AZ']
        bz_x, bz_y, bz_w, bz_h = positions['BZ']
        
        params["combiner"] = {
            "base_x": az_x,
            "base_y": az_y,
            "spacing": bz_y - az_y,
            "width": az_w + 20,  # 添加一些边距
            "height": az_h + 10
        }
    
    return params


def main():
    """主函数"""
    # 查找标注文件
    labels_dir = Path("training_data")
    label_files = list(labels_dir.glob("*_labels.json"))
    
    if not label_files:
        print("❌ 没有找到标注文件")
        return 1
    
    # 使用第一个标注文件
    label_file = label_files[0]
    with open(label_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_path = Path(data['image_path'])
    if not image_path.exists():
        print(f"❌ 图像文件不存在: {image_path}")
        return 1
    
    # 提取坐标
    params = extract_coordinates_from_image(image_path)
    
    if params:
        print("\n" + "=" * 60)
        print("提取结果")
        print("=" * 60)
        print(json.dumps(params, indent=2, ensure_ascii=False))
        
        # 保存结果
        output_path = Path("coordinate_parameters.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 参数已保存: {output_path}")
    else:
        print("\n⚠️  自动提取失败")
        print("   请使用交互式工具: python3 tools/extract_coordinates_interactive.py")
    
    return 0


if __name__ == "__main__":
    exit(main())
