#!/usr/bin/env python3
"""
合并坐标文件 - 恢复被覆盖的坐标
"""
import json
from pathlib import Path

print("="*70)
print("坐标合并工具")
print("="*70)
print()

# 原来的16项完整数据（从之前的测试结果恢复）
original_16_items = {
    "AZ": [218, 227, 244, 243],
    "BZ": [264, 227, 295, 243],
    "CZ": [313, 227, 341, 244],
    "DZ": [361, 226, 390, 242],
    "AB": [408, 226, 439, 244],
    "CD": [456, 227, 486, 244],
    "ABCD": [509, 226, 539, 244],
    "Z-Plane-A-Current-1": [43, 292, 81, 310],
    "Z-Plane-A-Current-2": [43, 316, 80, 333],
    "Z-Plane-A-Current-3": [41, 340, 80, 357],
    "Z-Plane-A-Current-4": [42, 364, 80, 381],
    "Z-Plane-A-Current-5": [42, 393, 81, 413],
    "Z-Plane-A-Current-6": [41, 416, 80, 434],
    "Z-Plane-A-Current-7": [42, 440, 80, 459],
    "Z-Plane-A-Current-8": [42, 464, 81, 482],
    "Z-Plane-A-ISOTemp-1": [174, 293, 213, 311]
}

# 读取当前文件（你新标注的3项）
current_file = Path('config/template_coordinates.json')
with open(current_file, 'r', encoding='utf-8') as f:
    new_items = json.load(f)

print(f"原有数据: {len(original_16_items)} 项")
print(f"新标注数据: {len(new_items)} 项")
print()

# 合并：用新数据更新原数据
merged = original_16_items.copy()
for key, value in new_items.items():
    if key in merged:
        print(f"✓ 更新: {key}")
        print(f"    旧坐标: {merged[key]}")
        print(f"    新坐标: {value}")
    else:
        print(f"✓ 新增: {key} = {value}")
    merged[key] = value

print()
print(f"合并后总数: {len(merged)} 项")
print()

# 保存合并结果
with open(current_file, 'w', encoding='utf-8') as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)

print(f"✓ 已保存到: {current_file}")
print()

# 显示所有项
print("完整列表：")
for idx, (name, coords) in enumerate(merged.items(), 1):
    print(f"  {idx:2d}. {name:30s} - {coords}")

print()
print("="*70)
