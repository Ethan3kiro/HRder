#!/usr/bin/env python3
"""
AI 辅助标注工具
通过 AI 识别图像中的数字，生成标注文件
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def create_label_template():
    """创建标注模板"""
    # 定义 71 个数据项
    cell_ids = []
    
    # COMBINER (7 项)
    combiner_items = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    cell_ids.extend(combiner_items)
    
    # Z-Plane (64 项)
    for module in ['A', 'B', 'C', 'D']:
        for row in range(1, 9):
            cell_ids.append(f'Z-Plane {module}-Current-{row}')
            cell_ids.append(f'Z-Plane {module}-ISO Temp-{row}')
    
    return cell_ids


def save_labels(image_path, labels_dict, output_dir="training_data"):
    """
    保存标注数据到 JSON 文件
    
    Args:
        image_path: 图像文件路径
        labels_dict: 标注数据字典 {cell_id: value}
        output_dir: 输出目录
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    image_path = Path(image_path)
    output_file = output_dir / f"{image_path.stem}_labels.json"
    
    # 检查文件是否已存在
    if output_file.exists():
        print(f"⚠️  警告：标注文件已存在: {output_file}")
        response = input("是否覆盖？(y/n): ").strip().lower()
        if response != 'y':
            print("❌ 取消保存")
            return False
    
    # 创建标注数据
    data = {
        "image_path": str(image_path.absolute()),
        "labels": labels_dict,
        "total_cells": 71,
        "labeled_cells": len(labels_dict),
        "created_by": "AI Assistant",
        "created_at": datetime.now().isoformat()
    }
    
    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 标注文件已保存: {output_file}")
    print(f"   已标注: {len(labels_dict)} / 71")
    
    return True


def print_template():
    """打印标注模板供用户参考"""
    cell_ids = create_label_template()
    
    print("\n" + "=" * 60)
    print("标注模板 - 71 个数据项")
    print("=" * 60)
    
    print("\n【COMBINER 区域】(7 项)")
    for i, cell_id in enumerate(cell_ids[:7], 1):
        print(f"  {i}. {cell_id}")
    
    print("\n【Z-Plane 区域】(64 项)")
    print("  模块 A (16 项):")
    for i, cell_id in enumerate(cell_ids[7:23], 8):
        print(f"    {i}. {cell_id}")
    
    print("\n  模块 B (16 项):")
    for i, cell_id in enumerate(cell_ids[23:39], 24):
        print(f"    {i}. {cell_id}")
    
    print("\n  模块 C (16 项):")
    for i, cell_id in enumerate(cell_ids[39:55], 40):
        print(f"    {i}. {cell_id}")
    
    print("\n  模块 D (16 项):")
    for i, cell_id in enumerate(cell_ids[55:71], 56):
        print(f"    {i}. {cell_id}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("AI 辅助标注工具")
    print("=" * 60)
    
    print("\n📝 使用说明:")
    print("1. 将发射机截图发送给 AI 助手")
    print("2. AI 助手会识别图像中的所有数字")
    print("3. AI 助手会提供完整的标注数据")
    print("4. 运行此脚本保存标注数据")
    
    print("\n" + "=" * 60)
    print("标注数据格式示例")
    print("=" * 60)
    
    example = {
        "AZ": 47.0,
        "BZ": 44.0,
        "CZ": 44.0,
        "DZ": 42.0,
        "AB": 29.0,
        "CD": 30.0,
        "ABCD": 29.0,
        "Z-Plane A-Current-1": 6.9,
        "Z-Plane A-ISO Temp-1": 63.0,
        # ... 更多数据
    }
    
    print("\n```json")
    print(json.dumps(example, indent=2, ensure_ascii=False))
    print("```")
    
    print("\n" + "=" * 60)
    print("完整的 71 个数据项列表")
    print_template()
    
    print("\n💡 提示:")
    print("  - AI 助手可以准确识别图像中的所有数字")
    print("  - 避免了手动标注的人为误差")
    print("  - 大大提高了标注效率")
    
    print("\n🚀 下一步:")
    print("  1. 将截图发送给 AI 助手")
    print("  2. AI 助手会返回完整的标注数据")
    print("  3. 使用返回的数据调用 save_labels() 函数")


if __name__ == "__main__":
    main()
