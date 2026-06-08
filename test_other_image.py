#!/usr/bin/env python3
"""
测试其他图片的识别效果
"""
from pathlib import Path
from src.template_ocr_extractor import TemplateOCRExtractor
import pandas as pd

print("="*70)
print("测试新图片识别效果")
print("="*70)
print()

# 创建提取器
extractor = TemplateOCRExtractor()

# 测试图像
image_path = Path('911-20251111.jpg')

if not image_path.exists():
    print(f"✗ 图像不存在: {image_path}")
    exit(1)

print(f"测试图像: {image_path}")
print()

# 识别
try:
    results = extractor.extract_from_image(image_path)
    
    print(f"✓ 识别完成！")
    print(f"  识别到 {len(results)} 个数据项")
    print()
    
    if len(results) > 0:
        print("识别结果：")
        print("-"*70)
        
        # 按顺序显示
        for idx, row in results.iterrows():
            item_name = row['item_name']
            value = row['value']
            unit = row['unit']
            print(f"{idx+1:2d}. {item_name:30s} = {value:6.1f} {unit}")
        
        print("-"*70)
        print()
        
        # 保存结果
        output_file = 'test_20251111_results.csv'
        results.to_csv(output_file, index=False)
        print(f"✓ 结果已保存到: {output_file}")
        print()
        
        # 统计信息
        print("统计信息：")
        print(f"  总数: {len(results)} / 71")
        print(f"  识别率: {len(results)/71*100:.1f}%")
        print(f"  COMBINER: {len([r for r in results['item_name'] if 'Z-Plane' not in r])} 项")
        print(f"  Z-Plane: {len([r for r in results['item_name'] if 'Z-Plane' in r])} 项")
        
        # 按模块统计
        print()
        print("各模块识别情况：")
        for module in ['A', 'B', 'C', 'D']:
            module_items = [r for r in results['item_name'] if f'Z-Plane-{module}' in r]
            print(f"  Z-Plane {module}: {len(module_items)}/16 项")
        
    else:
        print("✗ 未识别到任何数据")
        print()
        print("可能的原因：")
        print("  1. 图片布局与标注图片不同")
        print("  2. 图片尺寸不一致")
        print("  3. 坐标不适用于这张图片")

except Exception as e:
    print(f"✗ 识别失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
