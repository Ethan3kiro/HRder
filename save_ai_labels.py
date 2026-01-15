#!/usr/bin/env python3
"""
保存 AI 标注数据的便捷脚本
使用方法：编辑此文件，填入 AI 返回的标注数据，然后运行
"""

from tools.ai_assisted_labeling import save_labels

# ============================================================
# 配置区域 - 请修改以下内容
# ============================================================

# 图像文件路径（相对路径或绝对路径）
IMAGE_PATH = "911-20251111.jpg"

# AI 返回的标注数据 - 请将 AI 返回的 JSON 数据粘贴到这里
LABELS = {
    # COMBINER 区域 (7 项) - 整数
    "AZ": 42,
    "BZ": 50,
    "CZ": 51,
    "DZ": 56,
    "AB": 30,
    "CD": 40,
    "ABCD": 28,
    
    # Z-Plane 模块 A (16 项)
    "Z-Plane A-Current-1": 7.2,
    "Z-Plane A-ISO Temp-1": 48,
    "Z-Plane A-Current-2": 7.7,
    "Z-Plane A-ISO Temp-2": 47,
    "Z-Plane A-Current-3": 7.8,
    "Z-Plane A-ISO Temp-3": 46,
    "Z-Plane A-Current-4": 7.2,
    "Z-Plane A-ISO Temp-4": 42,
    "Z-Plane A-Current-5": 7.3,
    "Z-Plane A-ISO Temp-5": 46,
    "Z-Plane A-Current-6": 7.8,
    "Z-Plane A-ISO Temp-6": 46,
    "Z-Plane A-Current-7": 7.8,
    "Z-Plane A-ISO Temp-7": 45,
    "Z-Plane A-Current-8": 7.2,
    "Z-Plane A-ISO Temp-8": 47,
    
    # Z-Plane 模块 B (16 项)
    "Z-Plane B-Current-1": 7.2,
    "Z-Plane B-ISO Temp-1": 49,
    "Z-Plane B-Current-2": 7.8,
    "Z-Plane B-ISO Temp-2": 51,
    "Z-Plane B-Current-3": 7.9,
    "Z-Plane B-ISO Temp-3": 49,
    "Z-Plane B-Current-4": 7.7,
    "Z-Plane B-ISO Temp-4": 43,
    "Z-Plane B-Current-5": 7.4,
    "Z-Plane B-ISO Temp-5": 47,
    "Z-Plane B-Current-6": 7.6,
    "Z-Plane B-ISO Temp-6": 50,
    "Z-Plane B-Current-7": 7.4,
    "Z-Plane B-ISO Temp-7": 47,
    "Z-Plane B-Current-8": 7.5,
    "Z-Plane B-ISO Temp-8": 47,
    
    # Z-Plane 模块 C (16 项)
    "Z-Plane C-Current-1": 7.8,
    "Z-Plane C-ISO Temp-1": 49,
    "Z-Plane C-Current-2": 8.1,
    "Z-Plane C-ISO Temp-2": 45,
    "Z-Plane C-Current-3": 8.0,
    "Z-Plane C-ISO Temp-3": 46,
    "Z-Plane C-Current-4": 7.6,
    "Z-Plane C-ISO Temp-4": 45,
    "Z-Plane C-Current-5": 7.6,
    "Z-Plane C-ISO Temp-5": 49,
    "Z-Plane C-Current-6": 8.1,
    "Z-Plane C-ISO Temp-6": 48,
    "Z-Plane C-Current-7": 8.1,
    "Z-Plane C-ISO Temp-7": 46,
    "Z-Plane C-Current-8": 8.2,
    "Z-Plane C-ISO Temp-8": 45,
    
    # Z-Plane 模块 D (16 项)
    "Z-Plane D-Current-1": 8.1,
    "Z-Plane D-ISO Temp-1": 46,
    "Z-Plane D-Current-2": 7.8,
    "Z-Plane D-ISO Temp-2": 43,
    "Z-Plane D-Current-3": 8.1,
    "Z-Plane D-ISO Temp-3": 47,
    "Z-Plane D-Current-4": 7.5,
    "Z-Plane D-ISO Temp-4": 44,
    "Z-Plane D-Current-5": 7.6,
    "Z-Plane D-ISO Temp-5": 48,
    "Z-Plane D-Current-6": 7.8,
    "Z-Plane D-ISO Temp-6": 43,
    "Z-Plane D-Current-7": 7.7,
    "Z-Plane D-ISO Temp-7": 43,
    "Z-Plane D-Current-8": 7.7,
    "Z-Plane D-ISO Temp-8": 43,
}

# ============================================================
# 主程序 - 无需修改
# ============================================================

def main():
    """主函数"""
    print("=" * 60)
    print("保存 AI 标注数据")
    print("=" * 60)
    
    print(f"\n图像路径: {IMAGE_PATH}")
    print(f"标注数据项: {len(LABELS)} / 71")
    
    # 验证数据完整性
    if len(LABELS) != 71:
        print(f"\n⚠️  警告：标注数据不完整！")
        print(f"   预期: 71 项")
        print(f"   实际: {len(LABELS)} 项")
        print(f"   缺失: {71 - len(LABELS)} 项")
        
        response = input("\n是否继续保存？(y/n): ").strip().lower()
        if response != 'y':
            print("❌ 取消保存")
            return 1
    
    # 保存标注数据
    success = save_labels(IMAGE_PATH, LABELS)
    
    if success:
        print("\n✅ 保存成功！")
        print("\n下一步:")
        print("  1. 继续标注更多图像")
        print("  2. 标注 5-10 张后运行: python3 tools/prepare_dl_data.py")
        print("  3. 然后训练模型: bash train_dl_ocr.sh")
        return 0
    else:
        print("\n❌ 保存失败")
        return 1


if __name__ == "__main__":
    exit(main())
