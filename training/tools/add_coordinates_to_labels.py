#!/usr/bin/env python3
"""
为标注文件添加坐标信息
将坐标定义与标签值合并
"""

import json
from pathlib import Path


def load_coordinates(coord_file):
    """加载坐标定义"""
    with open(coord_file) as f:
        coords = json.load(f)
    
    # 转换格式：[x, y, w, h] -> {x, y, width, height}
    formatted_coords = {}
    for key, value in coords.items():
        formatted_coords[key] = {
            "x": value[0],
            "y": value[1],
            "width": value[2],
            "height": value[3]
        }
    
    return formatted_coords


def add_coordinates_to_label_file(label_file, coordinates):
    """为标注文件添加坐标信息"""
    # 加载标注数据
    with open(label_file) as f:
        label_data = json.load(f)
    
    # 检查是否已有坐标
    if 'coordinates' in label_data and label_data['coordinates']:
        print(f"  ⚠️  已有坐标，跳过")
        return False
    
    # 添加坐标
    label_data['coordinates'] = coordinates
    
    # 保存
    with open(label_file, 'w') as f:
        json.dump(label_data, f, indent=2, ensure_ascii=False)
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("为标注文件添加坐标信息")
    print("=" * 60)
    
    # 加载坐标定义
    coord_file = Path("tools/version_C_coordinates.json")
    if not coord_file.exists():
        print(f"❌ 坐标文件不存在: {coord_file}")
        return 1
    
    print(f"\n📍 加载坐标定义: {coord_file.name}")
    coordinates = load_coordinates(coord_file)
    print(f"   ✓ 加载了 {len(coordinates)} 个坐标")
    
    # 查找所有标注文件
    labels_dir = Path("training_data")
    label_files = sorted(labels_dir.glob("*_labels.json"))
    
    if not label_files:
        print(f"\n❌ 未找到标注文件")
        return 1
    
    print(f"\n📦 找到 {len(label_files)} 个标注文件")
    print()
    
    # 处理每个文件
    updated = 0
    skipped = 0
    
    for label_file in label_files:
        print(f"处理: {label_file.name}")
        if add_coordinates_to_label_file(label_file, coordinates):
            print(f"  ✓ 已添加坐标")
            updated += 1
        else:
            skipped += 1
    
    print()
    print("=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"更新: {updated} 个文件")
    print(f"跳过: {skipped} 个文件")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())
