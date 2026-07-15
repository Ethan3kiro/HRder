#!/usr/bin/env python3
"""
OCR识别准确率测试
对两张测试图片进行识别，并统计准确率
"""
import cv2
import numpy as np
import pytesseract
import json
from pathlib import Path
from collections import defaultdict


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


def test_image(image_path):
    """测试单张图片"""
    print(f"\n{'='*70}")
    print(f"测试图片: {image_path}")
    print(f"{'='*70}\n")
    
    # 加载坐标
    coords_file = Path('config/template_coordinates.json')
    with open(coords_file, 'r', encoding='utf-8') as f:
        coords = json.load(f)
    
    # 加载图像
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ 无法加载图片: {image_path}")
        return None
    
    # Tesseract 配置
    tesseract_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.'
    
    # 验证范围
    valid_ranges = {
        'current': (5.0, 10.0),
        'temperature': (20.0, 80.0),
    }
    
    # 统计信息
    stats = {
        'total': 0,
        'ocr_success': 0,
        'in_range': 0,
        'out_of_range': 0,
        'ocr_failed': 0,
        'by_type': defaultdict(lambda: {'total': 0, 'success': 0, 'in_range': 0})
    }
    
    failed_items = []
    out_of_range_items = []
    
    # 处理每个区域
    for item_name, coord_list in coords.items():
        if isinstance(coord_list, list) and len(coord_list) == 4:
            stats['total'] += 1
            
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
            
            stats['by_type'][field_type]['total'] += 1
            
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
                processed = cv2.resize(processed, None, fx=scale, fy=scale, 
                                      interpolation=cv2.INTER_CUBIC)
            
            # OCR
            text_raw = pytesseract.image_to_string(processed, config=tesseract_config)
            text_cleaned = clean_text(text_raw)
            
            # 转换为数字
            try:
                value = float(text_cleaned) if text_cleaned else None
            except:
                value = None
            
            # 统计
            if value is not None:
                stats['ocr_success'] += 1
                stats['by_type'][field_type]['success'] += 1
                
                # 验证范围
                min_val, max_val = valid_ranges[field_type]
                if min_val <= value <= max_val:
                    stats['in_range'] += 1
                    stats['by_type'][field_type]['in_range'] += 1
                else:
                    stats['out_of_range'] += 1
                    out_of_range_items.append({
                        'name': item_name,
                        'value': value,
                        'unit': unit,
                        'range': f"{min_val}-{max_val}",
                        'ocr_text': text_raw.strip()
                    })
            else:
                stats['ocr_failed'] += 1
                failed_items.append({
                    'name': item_name,
                    'type': field_type,
                    'ocr_text': text_raw.strip()
                })
    
    # 打印结果
    print(f"总计区域: {stats['total']}")
    print(f"OCR识别成功: {stats['ocr_success']} ({stats['ocr_success']/stats['total']*100:.1f}%)")
    print(f"  - 范围内: {stats['in_range']} ({stats['in_range']/stats['total']*100:.1f}%)")
    print(f"  - 超出范围: {stats['out_of_range']} ({stats['out_of_range']/stats['total']*100:.1f}%)")
    print(f"OCR识别失败: {stats['ocr_failed']} ({stats['ocr_failed']/stats['total']*100:.1f}%)")
    print()
    
    print("按类型统计:")
    for ftype, data in sorted(stats['by_type'].items()):
        print(f"  {ftype}:")
        print(f"    总计: {data['total']}")
        print(f"    识别成功: {data['success']} ({data['success']/data['total']*100:.1f}%)")
        print(f"    范围内: {data['in_range']} ({data['in_range']/data['total']*100:.1f}%)")
    
    if failed_items:
        print(f"\n❌ OCR识别失败的项目 ({len(failed_items)}):")
        for item in failed_items:
            print(f"  - {item['name']:30s} [{item['type']}] OCR原文: '{item['ocr_text']}'")
    
    if out_of_range_items:
        print(f"\n⚠️  超出范围的项目 ({len(out_of_range_items)}):")
        for item in out_of_range_items:
            print(f"  - {item['name']:30s} = {item['value']} {item['unit']} "
                  f"(期望: {item['range']}) OCR: '{item['ocr_text']}'")
    
    return stats


def main():
    """主函数"""
    print("\n" + "="*70)
    print("OCR识别准确率测试")
    print("="*70)
    
    # 测试图片列表
    test_images = [
        '911-20251016.jpg',
        '911-20251111.jpg',
    ]
    
    all_stats = []
    
    for img_path in test_images:
        if Path(img_path).exists():
            stats = test_image(img_path)
            if stats:
                all_stats.append((img_path, stats))
        else:
            print(f"\n⚠️  图片不存在: {img_path}")
    
    # 总体统计
    if len(all_stats) > 1:
        print(f"\n{'='*70}")
        print("总体统计")
        print(f"{'='*70}\n")
        
        total_regions = sum(s['total'] for _, s in all_stats)
        total_success = sum(s['ocr_success'] for _, s in all_stats)
        total_in_range = sum(s['in_range'] for _, s in all_stats)
        total_out_range = sum(s['out_of_range'] for _, s in all_stats)
        total_failed = sum(s['ocr_failed'] for _, s in all_stats)
        
        print(f"测试图片数: {len(all_stats)}")
        print(f"总识别区域: {total_regions}")
        print(f"OCR识别成功率: {total_success}/{total_regions} ({total_success/total_regions*100:.1f}%)")
        print(f"  - 有效数据(范围内): {total_in_range}/{total_regions} ({total_in_range/total_regions*100:.1f}%)")
        print(f"  - 超出范围: {total_out_range}/{total_regions} ({total_out_range/total_regions*100:.1f}%)")
        print(f"OCR识别失败率: {total_failed}/{total_regions} ({total_failed/total_regions*100:.1f}%)")
        
        # 计算准确率评分
        print(f"\n{'='*70}")
        print("准确率评分")
        print(f"{'='*70}")
        
        ocr_success_rate = total_success / total_regions * 100
        valid_data_rate = total_in_range / total_regions * 100
        
        print(f"✓ OCR识别成功率: {ocr_success_rate:.1f}%")
        print(f"✓ 有效数据率: {valid_data_rate:.1f}%")
        
        if valid_data_rate >= 85:
            grade = "优秀 🌟🌟🌟"
        elif valid_data_rate >= 70:
            grade = "良好 🌟🌟"
        elif valid_data_rate >= 60:
            grade = "及格 🌟"
        else:
            grade = "需要改进"
        
        print(f"\n综合评级: {grade}")
        
        if total_out_range > 0:
            print(f"\n💡 提示: 有 {total_out_range} 个项目超出范围，可能是:")
            print(f"   1. OCR误识别（如7.7识别成77）")
            print(f"   2. 范围设置过于严格")
            print(f"   3. 实际数据确实异常")
    
    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    main()
