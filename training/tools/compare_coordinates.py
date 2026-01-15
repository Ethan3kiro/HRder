#!/usr/bin/env python3
"""
比较不同版本的坐标
帮助用户理解坐标变化
"""

import json
import sys
from pathlib import Path


def extract_coords_from_backup():
    """从备份文件中提取坐标（69.6%准确率版本）"""
    backup_file = Path("tools/prepare_dl_data.py.backup")
    
    if not backup_file.exists():
        print(f"❌ 备份文件不存在: {backup_file}")
        return None
    
    coords = {}
    
    # COMBINER 区域 - 从备份中提取
    combiner_base_x = 214
    combiner_base_y = 223
    combiner_spacing = 48
    combiner_width = 34
    combiner_height = 23
    
    for i, item in enumerate(['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']):
        x = combiner_base_x + i * combiner_spacing
        if item == 'ABCD':
            x += 2
        coords[item] = [x, combiner_base_y, combiner_width, combiner_height]
    
    # Z-Plane 区域配置
    zplane_configs = [
        ('A-Current', 42, 292, 38, 23, 8),
        ('A-ISO Temp', 175, 292, 37, 23, 8),
        ('B-Current', 234, 290, 38, 24, 4),
        ('B-ISO Temp', 366, 290, 38, 24, 4),
        ('C-Current', 426, 290, 39, 24, 4),
        ('C-ISO Temp', 558, 290, 39, 24, 3),
        ('D-Current', 618, 290, 38, 24, 4),
        ('D-ISO Temp', 750, 290, 39, 24, 3),
    ]
    
    for module, base_x, base_y, width, height, middle_gap in zplane_configs:
        for row in range(1, 9):
            if row <= 4:
                row_y = base_y + (row - 1) * height
            else:
                row_y = base_y + (row - 1) * height + middle_gap
            
            key = f'Z-Plane {module}-{row}'
            coords[key] = [base_x, row_y, width, height]
    
    return coords


def load_current_coords():
    """加载当前坐标（5.4%准确率版本）"""
    coord_file = Path("tools/individual_coordinates.json")
    
    if not coord_file.exists():
        print(f"❌ 当前坐标文件不存在: {coord_file}")
        return None
    
    with open(coord_file, 'r', encoding='utf-8') as f:
        coords = json.load(f)
    
    # 转换为列表格式
    return {k: list(v) for k, v in coords.items()}


def compare_coords(backup_coords, current_coords):
    """比较两个版本的坐标"""
    print("\n" + "=" * 80)
    print("坐标对比分析")
    print("=" * 80)
    
    differences = []
    
    for key in sorted(backup_coords.keys()):
        backup = backup_coords[key]
        current = current_coords.get(key, [0, 0, 0, 0])
        
        # 计算差异
        dx = current[0] - backup[0]
        dy = current[1] - backup[1]
        dw = current[2] - backup[2]
        dh = current[3] - backup[3]
        
        # 计算总位移
        displacement = (dx**2 + dy**2)**0.5
        
        if dx != 0 or dy != 0 or dw != 0 or dh != 0:
            differences.append({
                'key': key,
                'backup': backup,
                'current': current,
                'dx': dx,
                'dy': dy,
                'dw': dw,
                'dh': dh,
                'displacement': displacement
            })
    
    print(f"\n总共 {len(backup_coords)} 个框")
    print(f"有变化的框: {len(differences)} 个")
    print(f"未变化的框: {len(backup_coords) - len(differences)} 个")
    
    if differences:
        print("\n" + "=" * 80)
        print("变化详情（按位移大小排序）")
        print("=" * 80)
        
        # 按位移大小排序
        differences.sort(key=lambda x: x['displacement'], reverse=True)
        
        print(f"\n{'框ID':<30} {'位移':<8} {'ΔX':<6} {'ΔY':<6} {'ΔW':<6} {'ΔH':<6}")
        print("-" * 80)
        
        for diff in differences[:20]:  # 只显示前20个最大变化
            print(f"{diff['key']:<30} {diff['displacement']:>6.1f}px "
                  f"{diff['dx']:>5} {diff['dy']:>5} "
                  f"{diff['dw']:>5} {diff['dh']:>5}")
        
        if len(differences) > 20:
            print(f"\n... 还有 {len(differences) - 20} 个框有变化")
        
        # 统计分析
        print("\n" + "=" * 80)
        print("统计分析")
        print("=" * 80)
        
        avg_dx = sum(d['dx'] for d in differences) / len(differences)
        avg_dy = sum(d['dy'] for d in differences) / len(differences)
        avg_displacement = sum(d['displacement'] for d in differences) / len(differences)
        max_displacement = max(d['displacement'] for d in differences)
        
        print(f"平均X偏移: {avg_dx:+.1f} 像素")
        print(f"平均Y偏移: {avg_dy:+.1f} 像素")
        print(f"平均位移: {avg_displacement:.1f} 像素")
        print(f"最大位移: {max_displacement:.1f} 像素")
        
        # 分析COMBINER区域
        combiner_diffs = [d for d in differences if not d['key'].startswith('Z-Plane')]
        if combiner_diffs:
            print(f"\nCOMBINER区域变化: {len(combiner_diffs)} 个框")
            for diff in combiner_diffs:
                print(f"  {diff['key']}: 位移 {diff['displacement']:.1f}px "
                      f"(ΔX={diff['dx']:+d}, ΔY={diff['dy']:+d})")
    
    return differences


def save_backup_coords_to_json(backup_coords):
    """将备份坐标保存为JSON格式"""
    output_file = Path("tools/backup_coordinates.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(backup_coords, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 备份坐标已保存到: {output_file}")
    print("  可以用这个文件恢复到 69.6% 准确率的坐标")


def main():
    """主函数"""
    print("=" * 80)
    print("坐标版本对比工具")
    print("=" * 80)
    
    # 加载备份坐标（69.6%准确率）
    print("\n加载备份坐标（69.6%准确率版本）...")
    backup_coords = extract_coords_from_backup()
    if backup_coords is None:
        return 1
    print(f"✓ 加载了 {len(backup_coords)} 个坐标")
    
    # 加载当前坐标（5.4%准确率）
    print("\n加载当前坐标（5.4%准确率版本）...")
    current_coords = load_current_coords()
    if current_coords is None:
        return 1
    print(f"✓ 加载了 {len(current_coords)} 个坐标")
    
    # 比较坐标
    differences = compare_coords(backup_coords, current_coords)
    
    # 保存备份坐标为JSON
    save_backup_coords_to_json(backup_coords)
    
    # 提供恢复选项
    print("\n" + "=" * 80)
    print("恢复选项")
    print("=" * 80)
    print("\n如果要恢复到 69.6% 准确率的坐标，运行：")
    print("  cp tools/backup_coordinates.json tools/individual_coordinates.json")
    print("  python3 tools/apply_individual_coordinates.py")
    print("  bash train_dl_ocr.sh")
    
    return 0


if __name__ == "__main__":
    exit(main())
