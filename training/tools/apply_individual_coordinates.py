#!/usr/bin/env python3
"""
自动应用独立调整的坐标到 prepare_dl_data.py
"""

import json
from pathlib import Path
import shutil


def backup_original():
    """备份原始文件"""
    original = Path("tools/prepare_dl_data.py")
    backup = Path("tools/prepare_dl_data.py.backup")
    
    if not backup.exists():
        shutil.copy(original, backup)
        print(f"✓ 已备份原始文件: {backup}")
    else:
        print(f"ℹ 备份文件已存在: {backup}")


def load_individual_coordinates():
    """加载独立调整的坐标"""
    coord_file = Path("tools/individual_coordinates.json")
    
    if not coord_file.exists():
        print(f"❌ 找不到坐标文件: {coord_file}")
        print("   请先运行 individual_coordinate_adjuster.py 并保存坐标")
        return None
    
    with open(coord_file, 'r', encoding='utf-8') as f:
        coords = json.load(f)
    
    print(f"✓ 加载了 {len(coords)} 个框的坐标")
    return coords


def generate_new_get_cell_coordinates(coords):
    """生成新的 get_cell_coordinates 函数代码"""
    code_lines = []
    
    code_lines.append("    def get_cell_coordinates(self):")
    code_lines.append('        """定义所有单元格的坐标（独立调整后的坐标）"""')
    code_lines.append("        coords = {}")
    code_lines.append("")
    code_lines.append("        # 格式: {cell_id: (x, y, width, height)}")
    code_lines.append("")
    
    # COMBINER 区域
    code_lines.append("        # COMBINER 区域 - 独立调整")
    for item in ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']:
        if item in coords:
            x, y, w, h = coords[item]
            code_lines.append(f"        coords['{item}'] = ({x}, {y}, {w}, {h})")
    
    code_lines.append("")
    
    # Z-Plane 区域
    code_lines.append("        # Z-Plane 区域 - 独立调整")
    modules = ['A-Current', 'A-ISO Temp', 'B-Current', 'B-ISO Temp',
               'C-Current', 'C-ISO Temp', 'D-Current', 'D-ISO Temp']
    
    for module in modules:
        code_lines.append(f"        # {module}")
        for row in range(1, 9):
            key = f'Z-Plane {module}-{row}'
            if key in coords:
                x, y, w, h = coords[key]
                code_lines.append(f"        coords['{key}'] = ({x}, {y}, {w}, {h})")
        code_lines.append("")
    
    code_lines.append("        return coords")
    
    return '\n'.join(code_lines)


def update_prepare_dl_data(coords):
    """更新 prepare_dl_data.py 文件"""
    file_path = Path("tools/prepare_dl_data.py")
    
    # 读取原始文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到 get_cell_coordinates 函数的开始和结束
    start_idx = None
    end_idx = None
    indent_level = 0
    
    for i, line in enumerate(lines):
        if 'def get_cell_coordinates(self):' in line:
            start_idx = i
            indent_level = len(line) - len(line.lstrip())
        elif start_idx is not None and end_idx is None:
            # 检查是否是下一个函数或类方法
            if line.strip() and not line.strip().startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and line.strip().startswith('def '):
                    end_idx = i
                    break
    
    if start_idx is None:
        print("❌ 找不到 get_cell_coordinates 函数")
        return False
    
    if end_idx is None:
        # 如果没有找到下一个函数，找到文件末尾
        end_idx = len(lines)
    
    # 生成新的函数代码
    new_function = generate_new_get_cell_coordinates(coords)
    
    # 替换函数
    new_lines = lines[:start_idx] + [new_function + '\n\n'] + lines[end_idx:]
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ 已更新 {file_path}")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("应用独立调整的坐标")
    print("=" * 60)
    
    # 1. 备份原始文件
    print("\n步骤 1: 备份原始文件")
    backup_original()
    
    # 2. 加载独立坐标
    print("\n步骤 2: 加载独立调整的坐标")
    coords = load_individual_coordinates()
    if coords is None:
        return 1
    
    # 3. 更新 prepare_dl_data.py
    print("\n步骤 3: 更新 prepare_dl_data.py")
    if not update_prepare_dl_data(coords):
        return 1
    
    print("\n" + "=" * 60)
    print("✅ 坐标应用完成！")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 运行训练: bash train_dl_ocr.sh")
    print("  2. 查看结果: 检查准确率是否提升")
    print("\n如果需要恢复原始坐标:")
    print("  cp tools/prepare_dl_data.py.backup tools/prepare_dl_data.py")
    
    return 0


if __name__ == "__main__":
    exit(main())
