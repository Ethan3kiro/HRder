#!/usr/bin/env python3
"""
使用实际的TemplateOCRExtractor（包含纠偏逻辑）测试OCR识别准确率
"""
import sys
from pathlib import Path
from collections import defaultdict


def test_image_with_extractor(image_path):
    """使用TemplateOCRExtractor测试单张图片"""
    print(f"\n{'='*70}")
    print(f"测试图片: {image_path}")
    print(f"{'='*70}\n")
    
    try:
        from src.template_ocr_extractor import TemplateOCRExtractor
    except ImportError as e:
        print(f"❌ 无法导入TemplateOCRExtractor: {e}")
        return None
    
    # 初始化提取器
    try:
        extractor = TemplateOCRExtractor()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return None
    
    # 执行识别
    try:
        import time
        start_time = time.time()
        results = extractor.extract_from_image(image_path)
        elapsed = time.time() - start_time
    except Exception as e:
        print(f"❌ 识别失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # 统计信息
    stats = {
        'total_regions': 71,  # 总共71个区域
        'recognized': len(results),
        'failed': 71 - len(results),
        'by_type': defaultdict(lambda: {'total': 0, 'recognized': 0}),
        'elapsed': elapsed
    }
    
    # 按类型统计
    for _, row in results.iterrows():
        item_name = row['item_name']
        
        # 判断类型
        if 'Current' in item_name or 'current' in item_name:
            field_type = 'current'
        elif 'Temp' in item_name or 'temp' in item_name:
            field_type = 'temperature'
        else:
            field_type = 'temperature'
        
        stats['by_type'][field_type]['recognized'] += 1
    
    # 设置总数
    stats['by_type']['current']['total'] = 32
    stats['by_type']['temperature']['total'] = 39
    
    # 打印结果
    print(f"识别耗时: {elapsed:.2f} 秒")
    print(f"总计区域: {stats['total_regions']}")
    print(f"识别成功: {stats['recognized']} ({stats['recognized']/stats['total_regions']*100:.1f}%)")
    print(f"识别失败: {stats['failed']} ({stats['failed']/stats['total_regions']*100:.1f}%)")
    print()
    
    print("按类型统计:")
    for ftype, data in sorted(stats['by_type'].items()):
        total = data['total']
        recognized = data['recognized']
        print(f"  {ftype}:")
        print(f"    总计: {total}")
        print(f"    识别成功: {recognized} ({recognized/total*100:.1f}%)")
        print(f"    识别失败: {total - recognized}")
    print()
    
    # 显示前10个识别结果
    if len(results) > 0:
        print("前10个识别结果:")
        for idx, row in results.head(10).iterrows():
            value_str = f"{row['value']:.1f}" if isinstance(row['value'], (int, float)) else str(row['value'])
            print(f"  {row['item_name']:35s} = {value_str:>6s} {row['unit']}")
    
    # 检查是否有特定的纠偏案例
    print("\n纠偏案例检查 (电流字段):")
    current_items = results[results['item_name'].str.contains('Current|current', na=False)]
    
    corrected_count = 0
    for _, row in current_items.iterrows():
        value = row['value']
        # 检查是否在正常范围内 (5.0-10.0)
        if 5.0 <= value <= 10.0:
            # 检查是否可能是纠偏的结果（有一位小数且个位数）
            if isinstance(value, float) and value < 10 and '.' in str(value):
                print(f"  ✓ {row['item_name']:35s} = {value:.1f} A (可能经过纠偏)")
                corrected_count += 1
    
    if corrected_count > 0:
        print(f"\n✨ 发现 {corrected_count} 个可能经过小数点纠偏的电流数据")
    else:
        print(f"\n⚠️  未发现明显的小数点纠偏案例")
    
    return stats


def main():
    """主函数"""
    print("\n" + "="*70)
    print("OCR识别准确率测试 (使用纠偏逻辑)")
    print("="*70)
    
    # 测试图片列表
    test_images = [
        '911-20251016.jpg',
        '911-20251111.jpg',
    ]
    
    all_stats = []
    
    for img_path in test_images:
        if Path(img_path).exists():
            stats = test_image_with_extractor(img_path)
            if stats:
                all_stats.append((img_path, stats))
        else:
            print(f"\n⚠️  图片不存在: {img_path}")
    
    # 总体统计
    if len(all_stats) > 1:
        print(f"\n{'='*70}")
        print("总体统计")
        print(f"{'='*70}\n")
        
        total_regions = sum(s['total_regions'] for _, s in all_stats)
        total_recognized = sum(s['recognized'] for _, s in all_stats)
        total_failed = sum(s['failed'] for _, s in all_stats)
        avg_time = sum(s['elapsed'] for _, s in all_stats) / len(all_stats)
        
        print(f"测试图片数: {len(all_stats)}")
        print(f"总识别区域: {total_regions}")
        print(f"总识别成功: {total_recognized}/{total_regions} ({total_recognized/total_regions*100:.1f}%)")
        print(f"总识别失败: {total_failed}/{total_regions} ({total_failed/total_regions*100:.1f}%)")
        print(f"平均耗时: {avg_time:.2f} 秒/图片")
        
        # 按类型汇总
        print("\n按类型汇总:")
        type_stats = defaultdict(lambda: {'total': 0, 'recognized': 0})
        for _, stats in all_stats:
            for ftype, data in stats['by_type'].items():
                type_stats[ftype]['total'] += data['total']
                type_stats[ftype]['recognized'] += data['recognized']
        
        for ftype in sorted(type_stats.keys()):
            data = type_stats[ftype]
            total = data['total']
            recognized = data['recognized']
            print(f"  {ftype}:")
            print(f"    总计: {total}")
            print(f"    识别成功: {recognized}/{total} ({recognized/total*100:.1f}%)")
            print(f"    识别失败: {total - recognized}")
        
        # 计算准确率评分
        print(f"\n{'='*70}")
        print("准确率评分")
        print(f"{'='*70}")
        
        success_rate = total_recognized / total_regions * 100
        
        print(f"✓ 识别成功率: {success_rate:.1f}%")
        
        if success_rate >= 95:
            grade = "优秀 🌟🌟🌟"
        elif success_rate >= 85:
            grade = "良好 🌟🌟"
        elif success_rate >= 70:
            grade = "及格 🌟"
        else:
            grade = "需要改进"
        
        print(f"\n综合评级: {grade}")
        
        print("\n说明:")
        print("  ✓ 识别成功 = 已通过OCR识别 + 纠偏处理 + 范围验证")
        print("  ✓ 纠偏逻辑已自动应用（电流字段两位数自动添加小数点）")
        print("  ✓ 超出范围的数据已被自动过滤")
    
    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    main()
