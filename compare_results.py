#!/usr/bin/env python3
"""
对比历史测试结果和当前测试结果，找出差异原因
"""
import pandas as pd
from pathlib import Path


def main():
    print("\n" + "="*70)
    print("对比历史测试结果 vs 当前测试结果")
    print("="*70 + "\n")
    
    # 读取历史结果
    historical_file = Path('test_20251111_results.csv')
    if not historical_file.exists():
        print("❌ 历史结果文件不存在")
        return
    
    historical = pd.read_csv(historical_file)
    
    # 运行当前测试
    print("运行当前测试...")
    from src.template_ocr_extractor import TemplateOCRExtractor
    
    extractor = TemplateOCRExtractor()
    current = extractor.extract_from_image('911-20251111.jpg')
    
    print(f"\n历史结果: {len(historical)} 个项目")
    print(f"当前结果: {len(current)} 个项目")
    print(f"差异: {len(historical) - len(current)} 个项目\n")
    
    # 找出历史有但当前没有的项目
    historical_items = set(historical['item_name'])
    current_items = set(current['item_name'])
    
    missing = historical_items - current_items
    new = current_items - historical_items
    common = historical_items & current_items
    
    if missing:
        print(f"❌ 历史有但当前缺失的项目 ({len(missing)}):")
        for item in sorted(missing):
            hist_row = historical[historical['item_name'] == item].iloc[0]
            print(f"  - {item:35s} = {hist_row['value']} {hist_row['unit']}")
    
    if new:
        print(f"\n✨ 当前新增的项目 ({len(new)}):")
        for item in sorted(new):
            curr_row = current[current['item_name'] == item].iloc[0]
            print(f"  - {item:35s} = {curr_row['value']} {curr_row['unit']}")
    
    # 对比共同项目的数值差异
    print(f"\n📊 共同项目数值对比 ({len(common)}):")
    differences = []
    
    for item in sorted(common):
        hist_row = historical[historical['item_name'] == item].iloc[0]
        curr_row = current[current['item_name'] == item].iloc[0]
        
        hist_val = hist_row['value']
        curr_val = curr_row['value']
        
        if abs(hist_val - curr_val) > 0.01:
            differences.append({
                'item': item,
                'historical': hist_val,
                'current': curr_val,
                'diff': curr_val - hist_val
            })
    
    if differences:
        print(f"\n⚠️  发现 {len(differences)} 个数值差异:")
        for d in differences[:10]:  # 只显示前10个
            print(f"  {d['item']:35s} 历史: {d['historical']:6.1f} → 当前: {d['current']:6.1f} (差: {d['diff']:+.1f})")
        if len(differences) > 10:
            print(f"  ... 还有 {len(differences) - 10} 个差异项")
    else:
        print("  ✓ 所有共同项目数值一致")
    
    # 计算准确率
    print(f"\n{'='*70}")
    print("准确率对比")
    print(f"{'='*70}")
    
    historical_rate = len(historical) / 71 * 100
    current_rate = len(current) / 71 * 100
    
    print(f"历史准确率: {len(historical)}/71 = {historical_rate:.1f}%")
    print(f"当前准确率: {len(current)}/71 = {current_rate:.1f}%")
    print(f"差异: {current_rate - historical_rate:+.1f}%")
    
    # 分析可能原因
    print(f"\n{'='*70}")
    print("可能原因分析")
    print(f"{'='*70}\n")
    
    if len(missing) > 0:
        print("🔍 缺失项目分析:")
        
        # 按类型分组
        current_missing = []
        temp_missing = []
        
        for item in missing:
            if 'Current' in item or 'current' in item:
                current_missing.append(item)
            else:
                temp_missing.append(item)
        
        if current_missing:
            print(f"  - 电流字段缺失: {len(current_missing)} 个")
            for item in current_missing[:5]:
                print(f"    • {item}")
        
        if temp_missing:
            print(f"  - 温度字段缺失: {len(temp_missing)} 个")
            for item in temp_missing[:5]:
                print(f"    • {item}")
        
        print("\n可能原因:")
        print("  1. 范围验证过严 (valid_ranges 设置)")
        print("  2. OCR配置不同 (tesseract_config)")
        print("  3. 预处理方法改变 (preprocess_mode)")
        print("  4. Tesseract版本差异")
        print("  5. 图像加载方式不同")
    
    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    main()
