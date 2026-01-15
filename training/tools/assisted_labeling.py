#!/usr/bin/env python3
"""
辅助标注工具 - 使用现有OCR提取器预填充数据，用户只需确认/修正
"""

import json
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ocr_extractor_v11 import OCRExtractorV11


def assisted_label_image(image_path, output_dir="training_data"):
    """使用OCR辅助标注单张图像"""
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"辅助标注: {image_path.name}")
    print(f"{'='*60}")
    
    # 使用OCR提取数据
    print("\n🔍 使用OCR提取数据...")
    extractor = OCRExtractorV11()
    
    try:
        data = extractor.extract_from_image(str(image_path))
        
        if not data:
            print("❌ OCR提取失败")
            return False
        
        # 显示提取的数据
        print("\n✓ OCR提取完成！")
        print("\n📊 提取的数据:")
        
        # COMBINER区域
        print("\nCOMBINER 区域:")
        combiner_keys = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
        for key in combiner_keys:
            value = data.get(key, 'N/A')
            print(f"  {key:6s}: {value}")
        
        # Z-Plane区域（只显示前几个）
        print("\nZ-Plane 区域（示例）:")
        zplane_sample = [
            'Z-Plane A-Current-1', 'Z-Plane A-ISO Temp-1',
            'Z-Plane B-Current-1', 'Z-Plane B-ISO Temp-1',
        ]
        for key in zplane_sample:
            value = data.get(key, 'N/A')
            print(f"  {key:30s}: {value}")
        print(f"  ... (共 {len([k for k in data.keys() if k.startswith('Z-Plane')])} 个Z-Plane数据)")
        
        # 询问用户
        print(f"\n{'='*60}")
        response = input("数据看起来正确吗？(y=保存, n=跳过, e=编辑): ").strip().lower()
        
        if response == 'y':
            # 保存标注
            output_file = output_dir / f"{image_path.stem}_labels.json"
            
            # 转换为标注格式
            labels = {}
            for key, value in data.items():
                if key in combiner_keys or key.startswith('Z-Plane'):
                    try:
                        labels[key] = float(value)
                    except (ValueError, TypeError):
                        print(f"⚠️  跳过无效值: {key} = {value}")
            
            label_data = {
                "image_path": str(image_path.absolute()),
                "labels": labels,
                "total_cells": 71,
                "labeled_cells": len(labels)
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(label_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ 已保存: {output_file}")
            print(f"   标注了 {len(labels)}/71 个数据点")
            return True
            
        elif response == 'e':
            print("\n💡 提示: 请使用标注工具手动编辑")
            print(f"   python3 tools/data_labeling_tool.py")
            return False
        else:
            print("\n⏭️  跳过此图像")
            return False
            
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        return False


def batch_assisted_label(image_dir, output_dir="training_data"):
    """批量辅助标注"""
    image_dir = Path(image_dir)
    
    # 查找所有图像
    image_files = []
    for ext in ['*.bmp', '*.png', '*.jpg', '*.jpeg']:
        image_files.extend(image_dir.glob(ext))
    
    if not image_files:
        print(f"❌ 在 {image_dir} 中没有找到图像文件")
        return
    
    print("=" * 60)
    print("批量辅助标注")
    print("=" * 60)
    print(f"\n✓ 找到 {len(image_files)} 张图像")
    print("\n📝 工作流程:")
    print("   1. OCR自动提取数据")
    print("   2. 显示提取结果")
    print("   3. 你确认是否正确")
    print("   4. 自动保存标注文件")
    
    # 处理每张图像
    success_count = 0
    for i, image_path in enumerate(image_files, 1):
        print(f"\n\n{'='*60}")
        print(f"进度: {i}/{len(image_files)}")
        print(f"{'='*60}")
        
        if assisted_label_image(image_path, output_dir):
            success_count += 1
    
    # 总结
    print(f"\n\n{'='*60}")
    print("批量标注完成")
    print(f"{'='*60}")
    print(f"\n✅ 成功标注: {success_count}/{len(image_files)} 张图像")
    print(f"\n下一步:")
    print(f"   bash train_dl_ocr.sh")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("辅助标注工具")
        print("=" * 60)
        print("\n使用方法:")
        print("  单张图像:")
        print("    python3 tools/assisted_labeling.py <图像文件>")
        print("\n  批量处理:")
        print("    python3 tools/assisted_labeling.py <图像目录>")
        print("\n示例:")
        print("    python3 tools/assisted_labeling.py 885-20250219.jpg")
        print("    python3 tools/assisted_labeling.py /path/to/images/")
        return 1
    
    path = Path(sys.argv[1])
    
    if path.is_file():
        # 单张图像
        assisted_label_image(path)
    elif path.is_dir():
        # 批量处理
        batch_assisted_label(path)
    else:
        print(f"❌ 路径不存在: {path}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
