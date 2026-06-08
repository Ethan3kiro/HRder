#!/usr/bin/env python3
"""
测试不同预处理模式对Current字段的识别效果
"""
import cv2
import numpy as np
import pytesseract
import json
from pathlib import Path

print("="*70)
print("测试不同预处理模式")
print("="*70)
print()

# 加载坐标 - 只测试Current字段
coords_file = Path('config/template_coordinates.json')
with open(coords_file, 'r', encoding='utf-8') as f:
    all_coords = json.load(f)

# 筛选Current字段
current_coords = {k: v for k, v in all_coords.items() if 'Current' in k}

print(f"测试 {len(current_coords)} 个Current字段")
print()

# 加载图像
image_path = Path('911-20251016.jpg')
image = cv2.imread(str(image_path))

# Tesseract 配置
tesseract_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.'

# 测试不同的预处理方法
def test_preprocessing(roi, method_name, params):
    """测试单个预处理方法"""
    try:
        if method_name == "原图":
            processed = roi
        
        elif method_name == "灰度":
            processed = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        elif method_name == "Otsu二值化":
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        elif method_name == "自适应二值化":
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        
        elif method_name == "反色Otsu":
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        elif method_name == "反色自适应":
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            temp = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            processed = cv2.bitwise_not(temp)
        
        elif method_name == "形态学增强":
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        else:
            return None
        
        # 放大小区域
        if processed.shape[0] < 30 or processed.shape[1] < 50:
            scale = 2
            processed = cv2.resize(processed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # OCR
        text = pytesseract.image_to_string(processed, config=tesseract_config)
        text = text.strip().replace(' ', '')
        
        # 清理
        replacements = {'O': '0', 'o': '0', 'I': '1', 'l': '1', 'S': '5', 'B': '8'}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = ''.join(c for c in text if c.isdigit() or c == '.')
        
        try:
            value = float(text) if text else None
        except:
            value = None
        
        return value
    
    except Exception as e:
        return None

# 预处理方法列表
methods = [
    "原图",
    "灰度",
    "Otsu二值化",
    "自适应二值化",
    "反色Otsu",
    "反色自适应",
    "形态学增强"
]

# 测试每个字段
print("-"*70)
for item_name, coord_list in current_coords.items():
    x1, y1, x2, y2 = coord_list
    roi = image[y1:y2, x1:x2]
    
    print(f"\n{item_name}:")
    print(f"  坐标: {coord_list}, ROI: {roi.shape[1]}x{roi.shape[0]}")
    
    best_method = None
    best_value = None
    
    for method in methods:
        value = test_preprocessing(roi, method, {})
        
        if value is not None:
            status = "✓"
            # 检查是否在合理范围内
            if 5.0 <= value <= 10.0:
                status = "✓✓"
                if best_value is None:
                    best_value = value
                    best_method = method
        else:
            status = "✗"
            value = "N/A"
        
        print(f"    {status} {method:20s}: {value}")
    
    if best_method:
        print(f"  → 推荐方法: {best_method} = {best_value:.1f}A")

print("-"*70)
print()
print("💡 说明：")
print("  ✓✓ = 识别成功且在合理范围内 (5.0-10.0A)")
print("  ✓  = 识别成功但超出合理范围")
print("  ✗  = 识别失败")
print()
print("="*70)
