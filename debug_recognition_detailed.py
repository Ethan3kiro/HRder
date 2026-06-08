#!/usr/bin/env python3
"""
详细调试：查看每个字段的识别过程和过滤原因
"""
import cv2
import numpy as np
import pytesseract
import json
from pathlib import Path

print("="*70)
print("详细识别调试")
print("="*70)
print()

# 加载坐标
coords_file = Path('config/template_coordinates.json')
with open(coords_file, 'r', encoding='utf-8') as f:
    coords = json.load(f)

# 加载图像
image_path = Path('911-20251016.jpg')
image = cv2.imread(str(image_path))

# Tesseract 配置
tesseract_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.'

# 验证范围
valid_ranges = {
    'current': (5.0, 10.0),
    'temperature': (20.0, 80.0),
}

def preprocess_for_current(roi):
    """Current字段预处理"""
    if len(roi.shape) == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi.copy()
    return gray

def preprocess_for_temperature(roi):
    """Temperature字段预处理"""
    if len(roi.shape) == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi.copy()
    
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return binary

def clean_text(text):
    """清理文本"""
    text = text.strip().replace(' ', '')
    replacements = {'O': '0', 'o': '0', 'I': '1', 'l': '1', 'S': '5', 'B': '8'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = ''.join(c for c in text if c.isdigit() or c == '.')
    if text.count('.') > 1:
        parts = text.split('.')
        text = parts[0] + '.' + ''.join(parts[1:])
    return text

print(f"总共 {len(coords)} 个区域")
print()
print("-"*70)

# 处理每个区域
for idx, (item_name, coord_list) in enumerate(coords.items(), 1):
    if isinstance(coord_list, list) and len(coord_list) == 4:
        x1, y1, x2, y2 = coord_list
        
        # 判断类型
        if 'Current' in item_name or 'current' in item_name:
            field_type = 'current'
            unit = 'A'
        elif 'Temp' in item_name or 'temp' in item_name:
            field_type = 'temperature'
            unit = '°C'
        else:
            field_type = 'temperature'
            unit = '°C'
        
        # 提取ROI
        roi = image[y1:y2, x1:x2]
        
        # 预处理
        if field_type == 'current':
            processed = preprocess_for_current(roi)
        else:
            processed = preprocess_for_temperature(roi)
        
        # 增强小区域
        if processed.shape[0] < 30 or processed.shape[1] < 50:
            scale = 2
            processed = cv2.resize(processed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # OCR
        text_raw = pytesseract.image_to_string(processed, config=tesseract_config)
        text_cleaned = clean_text(text_raw)
        
        # 转换为数字
        try:
            value = float(text_cleaned) if text_cleaned else None
        except:
            value = None
        
        # 验证范围
        in_range = False
        if value is not None:
            min_val, max_val = valid_ranges[field_type]
            in_range = min_val <= value <= max_val
        
        # 打印结果
        status = "✓✓" if (value is not None and in_range) else ("✓" if value is not None else "✗")
        value_str = f"{value:6.1f}" if value is not None else "  N/A "
        
        print(f"{status} [{idx:2d}] {item_name:30s}")
        print(f"      类型: {field_type:11s} | ROI: {roi.shape[1]:3d}x{roi.shape[0]:2d} | OCR原文: '{text_raw.strip()}'")
        print(f"      清理后: '{text_cleaned}' | 数值: {value_str} {unit} | 范围检查: {'✓ PASS' if in_range else '✗ FAIL' if value is not None else 'N/A'}")
        
        if value is not None and not in_range:
            min_val, max_val = valid_ranges[field_type]
            print(f"      ⚠️  超出合理范围 ({min_val}-{max_val})")
        
        print()

print("-"*70)
print()
print("说明：")
print("  ✓✓ = 识别成功且在合理范围内")
print("  ✓  = 识别成功但超出范围（被过滤）")
print("  ✗  = OCR识别失败")
print()
print("="*70)
