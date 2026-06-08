#!/usr/bin/env python3
"""
调试工具：查看每个坐标区域的ROI图像和OCR结果
"""
import cv2
import numpy as np
import pytesseract
import json
from pathlib import Path

print("="*70)
print("ROI 调试查看器")
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

# 转灰度
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 自适应二值化
binary = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 11, 2
)

# Tesseract 配置
tesseract_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.'

# 创建输出目录
output_dir = Path('debug_rois')
output_dir.mkdir(exist_ok=True)

print(f"图像尺寸: {image.shape[1]} x {image.shape[0]}")
print(f"总共 {len(coords)} 个区域")
print(f"ROI图像将保存到: {output_dir}/")
print()
print("-"*70)

# 处理每个区域
for idx, (item_name, coord_list) in enumerate(coords.items(), 1):
    if isinstance(coord_list, list) and len(coord_list) == 4:
        x1, y1, x2, y2 = coord_list
        
        # 提取ROI
        roi_original = image[y1:y2, x1:x2]
        roi_gray = gray[y1:y2, x1:x2]
        roi_binary = binary[y1:y2, x1:x2]
        
        # 增强小区域
        if roi_binary.shape[0] < 30 or roi_binary.shape[1] < 50:
            scale = 2
            roi_binary_scaled = cv2.resize(roi_binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        else:
            roi_binary_scaled = roi_binary
        
        # OCR识别
        text_raw = pytesseract.image_to_string(roi_binary_scaled, config=tesseract_config)
        text_cleaned = text_raw.strip().replace(' ', '')
        
        # 清理文本
        replacements = {'O': '0', 'o': '0', 'I': '1', 'l': '1', 'S': '5', 'B': '8'}
        for old, new in replacements.items():
            text_cleaned = text_cleaned.replace(old, new)
        
        text_cleaned = ''.join(c for c in text_cleaned if c.isdigit() or c == '.')
        
        # 尝试转换为数字
        try:
            value = float(text_cleaned) if text_cleaned else None
        except:
            value = None
        
        # 保存ROI图像（拼接原图+灰度+二值化）
        h_max = max(roi_original.shape[0], roi_gray.shape[0], roi_binary_scaled.shape[0])
        
        # 调整高度一致
        def pad_height(img, target_h):
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            h, w = img.shape[:2]
            if h < target_h:
                pad = np.zeros((target_h - h, w, 3), dtype=np.uint8)
                img = np.vstack([img, pad])
            return img
        
        roi_original_padded = pad_height(roi_original, h_max)
        roi_gray_padded = pad_height(roi_gray, h_max)
        roi_binary_padded = pad_height(roi_binary_scaled, h_max)
        
        # 横向拼接
        combined = np.hstack([roi_original_padded, roi_gray_padded, roi_binary_padded])
        
        # 保存
        safe_name = item_name.replace('/', '_').replace('\\', '_')
        output_path = output_dir / f"{idx:02d}_{safe_name}.png"
        cv2.imwrite(str(output_path), combined)
        
        # 打印结果
        status = "✓" if value is not None else "✗"
        value_str = f"{value:6.1f}" if value is not None else "  N/A "
        
        print(f"{status} [{idx:2d}] {item_name:30s} | 坐标: {coord_list} | ROI: {roi_original.shape[1]}x{roi_original.shape[0]} | OCR: '{text_raw.strip()}' → {value_str}")

print("-"*70)
print()
print(f"✓ 所有ROI图像已保存到: {output_dir}/")
print()
print("💡 查看说明：")
print("  • 每张图片从左到右依次是：原图、灰度、二值化")
print("  • 如果识别失败，检查二值化图像是否清晰")
print("  • 如果坐标不准，需要重新标注")
print()
print("="*70)
