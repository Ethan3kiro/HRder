#!/usr/bin/env python3
"""
保存 20251210 图像的 AI 标注数据
由 AI 助手自动生成
"""

from tools.ai_assisted_labeling import save_labels
from pathlib import Path

# 图像路径 - 请根据实际情况修改
IMAGE_PATH = "885-20251210.jpg"  # 或者使用完整路径

# AI 标注的数据 (71 项)
LABELS = {
    # COMBINER 区域 (7 项) - 整数
    "AZ": 40,
    "BZ": 48,
    "CZ": 48,
    "DZ": 54,
    "AB": 28,
    "CD": 39,
    "ABCD": 27,
    
    # Z-Plane 模块 A (16 项)
    "Z-Plane A-Current-1": 7.2,    # 小数
    "Z-Plane A-ISO Temp-1": 47,    # 整数
    "Z-Plane A-Current-2": 7.7,
    "Z-Plane A-ISO Temp-2": 46,
    "Z-Plane A-Current-3": 7.8,
    "Z-Plane A-ISO Temp-3": 45,
    "Z-Plane A-Current-4": 7.2,
    "Z-Plane A-ISO Temp-4": 41,
    "Z-Plane A-Current-5": 7.3,
    "Z-Plane A-ISO Temp-5": 45,
    "Z-Plane A-Current-6": 7.8,
    "Z-Plane A-ISO Temp-6": 44,
    "Z-Plane A-Current-7": 7.8,
    "Z-Plane A-ISO Temp-7": 44,
    "Z-Plane A-Current-8": 7.1,
    "Z-Plane A-ISO Temp-8": 46,
    
    # Z-Plane 模块 B (16 项)
    "Z-Plane B-Current-1": 7.8,
    "Z-Plane B-ISO Temp-1": 48,
    "Z-Plane B-Current-2": 7.8,
    "Z-Plane B-ISO Temp-2": 50,
    "Z-Plane B-Current-3": 8.0,
    "Z-Plane B-ISO Temp-3": 48,
    "Z-Plane B-Current-4": 7.8,
    "Z-Plane B-ISO Temp-4": 42,
    "Z-Plane B-Current-5": 7.4,
    "Z-Plane B-ISO Temp-5": 46,
    "Z-Plane B-Current-6": 7.6,
    "Z-Plane B-ISO Temp-6": 48,
    "Z-Plane B-Current-7": 7.5,
    "Z-Plane B-ISO Temp-7": 46,
    "Z-Plane B-Current-8": 7.5,
    "Z-Plane B-ISO Temp-8": 47,
    
    # Z-Plane 模块 C (16 项)
    "Z-Plane C-Current-1": 7.8,
    "Z-Plane C-ISO Temp-1": 48,
    "Z-Plane C-Current-2": 8.1,
    "Z-Plane C-ISO Temp-2": 44,
    "Z-Plane C-Current-3": 8.0,
    "Z-Plane C-ISO Temp-3": 46,
    "Z-Plane C-Current-4": 7.6,
    "Z-Plane C-ISO Temp-4": 45,
    "Z-Plane C-Current-5": 7.5,
    "Z-Plane C-ISO Temp-5": 43,
    "Z-Plane C-Current-6": 8.1,
    "Z-Plane C-ISO Temp-6": 47,
    "Z-Plane C-Current-7": 8.2,
    "Z-Plane C-ISO Temp-7": 45,
    "Z-Plane C-Current-8": 8.2,
    "Z-Plane C-ISO Temp-8": 45,
    
    # Z-Plane 模块 D (16 项)
    "Z-Plane D-Current-1": 8.1,
    "Z-Plane D-ISO Temp-1": 45,
    "Z-Plane D-Current-2": 7.7,
    "Z-Plane D-ISO Temp-2": 41,
    "Z-Plane D-Current-3": 8.1,
    "Z-Plane D-ISO Temp-3": 45,
    "Z-Plane D-Current-4": 7.5,
    "Z-Plane D-ISO Temp-4": 43,
    "Z-Plane D-Current-5": 7.5,
    "Z-Plane D-ISO Temp-5": 47,
    "Z-Plane D-Current-6": 7.8,
    "Z-Plane D-ISO Temp-6": 42,
    "Z-Plane D-Current-7": 7.7,
    "Z-Plane D-ISO Temp-7": 41,
    "Z-Plane D-Current-8": 7.6,
    "Z-Plane D-ISO Temp-8": 41,
}


def main():
    """主函数"""
    print("=" * 60)
    print("保存 20251210 图像的 AI 标注数据")
    print("=" * 60)
    
    # 检查图像文件是否存在
    image_path = Path(IMAGE_PATH)
    if not image_path.exists():
        print(f"\n⚠️  警告：图像文件不存在: {IMAGE_PATH}")
        print("\n请修改脚本中的 IMAGE_PATH 变量为正确的路径")
        print("例如：")
        print('  IMAGE_PATH = "885-20251210.jpg"')
        print('  或')
        print('  IMAGE_PATH = "/完整/路径/到/图像.jpg"')
        return 1
    
    print(f"\n图像路径: {IMAGE_PATH}")
    print(f"标注数据项: {len(LABELS)} / 71")
    
    # 验证数据完整性
    if len(LABELS) != 71:
        print(f"\n⚠️  警告：标注数据不完整！")
        print(f"   预期: 71 项")
        print(f"   实际: {len(LABELS)} 项")
        return 1
    
    # 保存标注数据
    success = save_labels(IMAGE_PATH, LABELS)
    
    if success:
        print("\n✅ 保存成功！")
        print("\n📊 标注进度:")
        print("   已标注图像: 12 张 (包括这一张)")
        print("   目标: 16-20 张")
        print("   还需要: 4-8 张")
        print("\n下一步:")
        print("  1. 继续标注更多图像")
        print("  2. 标注完成后运行: python3 tools/prepare_dl_data.py")
        print("  3. 然后训练模型: bash train_dl_ocr.sh")
        return 0
    else:
        print("\n❌ 保存失败")
        return 1


if __name__ == "__main__":
    exit(main())
