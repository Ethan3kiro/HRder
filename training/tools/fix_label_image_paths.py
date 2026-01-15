#!/usr/bin/env python3
"""
修正标注文件中的图像路径
将 BMP 路径替换为实际存在的 JPG 路径
"""

import json
from pathlib import Path


def find_matching_image(label_filename, workspace_dir):
    """根据标注文件名查找匹配的图像"""
    # 从标注文件名提取基础名称
    # 例如: 1068-20250219_labels.json -> 1068-20250219
    base_name = label_filename.replace('_labels.json', '')
    
    # 尝试不同的图像文件名模式
    patterns = [
        f"{base_name}.jpg",
        f"{base_name}.bmp",
        f"885-{base_name.split('-')[-1]}.jpg" if '-' in base_name else None,
        f"921-{base_name.split('-')[-1]}.jpg" if '-' in base_name else None,
    ]
    
    # 如果文件名只是日期（如 20250219），尝试添加前缀
    if base_name.isdigit() or (len(base_name) == 8 and base_name.startswith('202')):
        patterns.extend([
            f"885-{base_name}.jpg",
            f"921-{base_name}.jpg",
            f"911-{base_name}.jpg",
            f"1068-{base_name}.jpg",
        ])
    
    # 查找存在的文件
    for pattern in patterns:
        if pattern is None:
            continue
        image_path = workspace_dir / pattern
        if image_path.exists():
            return image_path
    
    return None


def fix_label_file(label_file, workspace_dir):
    """修正单个标注文件的图像路径"""
    with open(label_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    old_path = Path(data['image_path'])
    
    # 检查路径是否已经正确
    if old_path.exists():
        return False, old_path
    
    # 查找匹配的图像
    new_path = find_matching_image(label_file.name, workspace_dir)
    
    if new_path is None:
        return None, old_path
    
    # 更新路径
    data['image_path'] = str(new_path)
    
    # 保存
    with open(label_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return True, new_path


def main():
    """主函数"""
    print("=" * 60)
    print("修正标注文件中的图像路径")
    print("=" * 60)
    
    workspace_dir = Path.cwd()
    labels_dir = workspace_dir / "training_data"
    
    # 查找所有标注文件
    label_files = sorted(labels_dir.glob("*_labels.json"))
    
    if not label_files:
        print("\n❌ 未找到标注文件")
        return 1
    
    print(f"\n✓ 找到 {len(label_files)} 个标注文件")
    print()
    
    # 处理每个文件
    updated = 0
    skipped = 0
    not_found = 0
    
    for label_file in label_files:
        print(f"处理: {label_file.name}")
        result, path = fix_label_file(label_file, workspace_dir)
        
        if result is True:
            print(f"  ✓ 已更新: {path.name}")
            updated += 1
        elif result is False:
            print(f"  ⚠️  路径已正确: {path.name}")
            skipped += 1
        else:
            print(f"  ❌ 未找到匹配的图像")
            not_found += 1
    
    print()
    print("=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"更新: {updated} 个文件")
    print(f"跳过: {skipped} 个文件（路径已正确）")
    print(f"未找到: {not_found} 个文件")
    
    if not_found > 0:
        print("\n⚠️  有些标注文件找不到对应的图像")
        print("   请检查图像文件是否存在")
    
    return 0


if __name__ == "__main__":
    exit(main())
