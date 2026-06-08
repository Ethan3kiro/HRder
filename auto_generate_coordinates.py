#!/usr/bin/env python3
"""
自动生成完整的71项坐标
基于已标注的成功数据，推算规律并生成剩余坐标
"""
import json
from pathlib import Path

print("="*70)
print("自动生成完整坐标")
print("="*70)
print()

# 读取当前已标注的坐标
current_file = Path('config/template_coordinates.json')
with open(current_file, 'r', encoding='utf-8') as f:
    current_coords = json.load(f)

print(f"当前已标注: {len(current_coords)} 项")
print()

# 分析已有的坐标规律
# Z-Plane A 的Current（已有8个）
a_current_coords = {
    1: [43, 292, 81, 310],
    2: [43, 316, 80, 333],
    3: [41, 340, 80, 357],
    4: [42, 364, 80, 381],
    5: [42, 393, 81, 413],
    6: [41, 416, 80, 434],
    7: [42, 440, 80, 459],
    8: [42, 464, 81, 482]
}

# Z-Plane A 的ISOTemp（已有8个）
a_temp_coords = {
    1: [174, 293, 213, 311],
    2: [173, 314, 212, 333],
    3: [174, 339, 213, 358],
    4: [173, 362, 213, 383],
    5: [173, 391, 213, 412],
    6: [174, 415, 213, 436],
    7: [172, 438, 213, 460],
    8: [173, 463, 213, 484]
}

# Z-Plane B 的Current（已有8个）
b_current_coords = {
    1: [234, 291, 274, 312],
    2: [234, 315, 274, 336],
    3: [234, 339, 274, 360],
    4: [232, 363, 273, 383],
    5: [233, 391, 273, 411],
    6: [234, 414, 274, 436],
    7: [233, 439, 274, 460],
    8: [234, 463, 273, 484]
}

# 分析规律：
# - Current列: x约43, 234, 425(C), 616(D)
# - Temp列: x约174, 365(B), 556(C), 747(D)
# - y坐标相同，间隔约23-24像素

# 计算列间距
current_col_gap = 234 - 43  # B和A的Current列间距 = 191
temp_col_gap = 365 - 174    # 预估B和A的Temp列间距

print("分析已有坐标规律：")
print(f"  Current列间距: {current_col_gap} 像素")
print(f"  行间距: 约23-24像素")
print()

# 生成完整的71项坐标
all_coords = {}

# 1. COMBINER（7项）- 保留已有的
combiner_names = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
for name in combiner_names:
    if name in current_coords:
        all_coords[name] = current_coords[name]

# 2. Z-Plane A（16项）- 保留已有的
for i in range(1, 9):
    all_coords[f'Z-Plane-A-Current-{i}'] = a_current_coords[i]
    all_coords[f'Z-Plane-A-ISOTemp-{i}'] = a_temp_coords[i]

# 3. Z-Plane B（16项）
# Current已有，需要生成Temp
for i in range(1, 9):
    all_coords[f'Z-Plane-B-Current-{i}'] = b_current_coords[i]
    # B的Temp坐标 = A的Temp坐标 + current_col_gap
    a_temp = a_temp_coords[i]
    all_coords[f'Z-Plane-B-ISOTemp-{i}'] = [
        a_temp[0] + current_col_gap,
        a_temp[1],
        a_temp[2] + current_col_gap,
        a_temp[3]
    ]

# 4. Z-Plane C（16项）
for i in range(1, 9):
    # C的Current = B的Current + current_col_gap
    b_curr = b_current_coords[i]
    all_coords[f'Z-Plane-C-Current-{i}'] = [
        b_curr[0] + current_col_gap,
        b_curr[1],
        b_curr[2] + current_col_gap,
        b_curr[3]
    ]
    
    # C的Temp = B的Temp + current_col_gap
    b_temp_x1 = a_temp_coords[i][0] + current_col_gap
    all_coords[f'Z-Plane-C-ISOTemp-{i}'] = [
        b_temp_x1 + current_col_gap,
        a_temp_coords[i][1],
        a_temp_coords[i][2] + current_col_gap * 2,
        a_temp_coords[i][3]
    ]

# 5. Z-Plane D（16项）
for i in range(1, 9):
    # D的Current = C的Current + current_col_gap
    c_curr_x1 = b_current_coords[i][0] + current_col_gap
    all_coords[f'Z-Plane-D-Current-{i}'] = [
        c_curr_x1 + current_col_gap,
        b_current_coords[i][1],
        b_current_coords[i][2] + current_col_gap * 2,
        b_current_coords[i][3]
    ]
    
    # D的Temp = C的Temp + current_col_gap
    c_temp_x1 = a_temp_coords[i][0] + current_col_gap * 2
    all_coords[f'Z-Plane-D-ISOTemp-{i}'] = [
        c_temp_x1 + current_col_gap,
        a_temp_coords[i][1],
        a_temp_coords[i][2] + current_col_gap * 3,
        a_temp_coords[i][3]
    ]

print(f"生成完成！总计: {len(all_coords)} 项")
print()

# 统计
combiner_count = len([k for k in all_coords.keys() if 'Z-Plane' not in k])
a_count = len([k for k in all_coords.keys() if 'Z-Plane-A' in k])
b_count = len([k for k in all_coords.keys() if 'Z-Plane-B' in k])
c_count = len([k for k in all_coords.keys() if 'Z-Plane-C' in k])
d_count = len([k for k in all_coords.keys() if 'Z-Plane-D' in k])

print("分类统计：")
print(f"  COMBINER: {combiner_count} 项")
print(f"  Z-Plane A: {a_count} 项")
print(f"  Z-Plane B: {b_count} 项")
print(f"  Z-Plane C: {c_count} 项")
print(f"  Z-Plane D: {d_count} 项")
print()

# 保存备份
backup_file = Path('config/template_coordinates_backup_before_auto.json')
with open(current_file, 'r', encoding='utf-8') as f:
    backup_data = f.read()
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(backup_data)
print(f"✓ 已备份当前坐标到: {backup_file}")

# 保存完整坐标
with open(current_file, 'w', encoding='utf-8') as f:
    json.dump(all_coords, f, indent=2, ensure_ascii=False)

print(f"✓ 已保存完整坐标到: {current_file}")
print()
print("="*70)
print()
print("下一步：运行测试验证自动生成的坐标")
print("  python3 test_partial_recognition.py")
print()
print("如果识别率不理想，可以恢复备份：")
print(f"  cp {backup_file} {current_file}")
print()
print("="*70)
