#!/usr/bin/env python3
"""
可视化提取的数字图像
查看模型实际看到的内容
"""

import json
import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


def load_coordinates(coord_file="tools/version_C_coordinates.json"):
    """加载坐标定义"""
    with open(coord_file) as f:
        coords = json.load(f)
    
    # 转换格式
    formatted_coords = {}
    for key, value in coords.items():
        formatted_coords[key] = {
            "x": value[0],
            "y": value[1],
            "width": value[2],
            "height": value[3]
        }
    
    return formatted_coords


def preprocess_digit(image, x, y, w, h, padding=5):
    """预处理数字图像（与训练时相同）"""
    # 添加 padding
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(image.shape[1], x + w + padding)
    y2 = min(image.shape[0], y + h + padding)
    
    # 裁剪
    digit_img = image[y1:y2, x1:x2]
    
    if digit_img.size == 0:
        return None, None
    
    # 保存原始裁剪
    original_crop = digit_img.copy()
    
    # 转换为灰度图
    if len(digit_img.shape) == 3:
        digit_img = cv2.cvtColor(digit_img, cv2.COLOR_BGR2GRAY)
    
    # 调整大小到 28x28
    digit_img = cv2.resize(digit_img, (28, 28), interpolation=cv2.INTER_AREA)
    
    # 二值化
    _, digit_img = cv2.threshold(digit_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return original_crop, digit_img


def visualize_sample_extractions(image_path, label_file, coords, num_samples=10):
    """可视化样本提取"""
    # 加载图像
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ 无法加载图像: {image_path}")
        return
    
    # 加载标注
    with open(label_file) as f:
        data = json.load(f)
    
    labels = data['labels']
    
    # 选择要可视化的单元格
    cell_ids = list(labels.keys())[:num_samples]
    
    # 创建图形
    fig, axes = plt.subplots(num_samples, 3, figsize=(12, num_samples * 2))
    if num_samples == 1:
        axes = axes.reshape(1, -1)
    
    for idx, cell_id in enumerate(cell_ids):
        if cell_id not in coords:
            continue
        
        coord = coords[cell_id]
        x, y, w, h = coord['x'], coord['y'], coord['width'], coord['height']
        true_value = labels[cell_id]
        
        # 提取并预处理
        original_crop, processed = preprocess_digit(image, x, y, w, h)
        
        if original_crop is None:
            continue
        
        # 在原图上标记位置
        marked_img = image.copy()
        cv2.rectangle(marked_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(marked_img, cell_id, (x, y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # 显示原图标记
        axes[idx, 0].imshow(cv2.cvtColor(marked_img[max(0, y-20):y+h+20, 
                                                     max(0, x-20):x+w+20], 
                                        cv2.COLOR_BGR2RGB))
        axes[idx, 0].set_title(f'{cell_id}\n真实值: {true_value}')
        axes[idx, 0].axis('off')
        
        # 显示原始裁剪
        if len(original_crop.shape) == 3:
            axes[idx, 1].imshow(cv2.cvtColor(original_crop, cv2.COLOR_BGR2RGB))
        else:
            axes[idx, 1].imshow(original_crop, cmap='gray')
        axes[idx, 1].set_title('原始裁剪')
        axes[idx, 1].axis('off')
        
        # 显示预处理后
        axes[idx, 2].imshow(processed, cmap='gray')
        axes[idx, 2].set_title('预处理后 (28x28)')
        axes[idx, 2].axis('off')
    
    plt.tight_layout()
    
    # 保存
    output_path = Path("models") / f"digit_extraction_{Path(image_path).stem}.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ 已保存: {output_path}")
    plt.close()


def visualize_combiner_region(image_path, coords):
    """专门可视化 COMBINER 区域"""
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ 无法加载图像: {image_path}")
        return
    
    # COMBINER 项
    combiner_items = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    fig, axes = plt.subplots(2, 7, figsize=(20, 6))
    
    for idx, item in enumerate(combiner_items):
        if item not in coords:
            continue
        
        coord = coords[item]
        x, y, w, h = coord['x'], coord['y'], coord['width'], coord['height']
        
        # 在原图上标记
        marked_img = image.copy()
        cv2.rectangle(marked_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 显示标记区域
        region = marked_img[max(0, y-10):y+h+10, max(0, x-10):x+w+10]
        axes[0, idx].imshow(cv2.cvtColor(region, cv2.COLOR_BGR2RGB))
        axes[0, idx].set_title(f'{item}\n坐标: ({x}, {y})')
        axes[0, idx].axis('off')
        
        # 显示预处理后
        _, processed = preprocess_digit(image, x, y, w, h)
        if processed is not None:
            axes[1, idx].imshow(processed, cmap='gray')
            axes[1, idx].set_title('预处理后')
            axes[1, idx].axis('off')
    
    plt.suptitle(f'COMBINER 区域提取 - {Path(image_path).stem}', fontsize=16)
    plt.tight_layout()
    
    # 保存
    output_path = Path("models") / f"combiner_extraction_{Path(image_path).stem}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ 已保存: {output_path}")
    plt.close()


def main():
    """主函数"""
    print("=" * 60)
    print("可视化提取的数字图像")
    print("=" * 60)
    
    # 加载坐标
    coords = load_coordinates()
    print(f"\n✓ 加载了 {len(coords)} 个坐标定义")
    
    # 查找标注文件
    labels_dir = Path("training_data")
    label_files = sorted(labels_dir.glob("*_labels.json"))
    
    if not label_files:
        print("\n❌ 未找到标注文件")
        return 1
    
    print(f"✓ 找到 {len(label_files)} 个标注文件")
    
    # 选择第一个文件进行可视化
    label_file = label_files[0]
    with open(label_file) as f:
        data = json.load(f)
    
    image_path = Path(data['image_path'])
    if not image_path.exists():
        print(f"\n❌ 图像不存在: {image_path}")
        return 1
    
    print(f"\n📸 可视化图像: {image_path.name}")
    
    # 可视化样本提取
    print("\n1. 生成样本提取可视化...")
    visualize_sample_extractions(image_path, label_file, coords, num_samples=15)
    
    # 可视化 COMBINER 区域
    print("\n2. 生成 COMBINER 区域可视化...")
    visualize_combiner_region(image_path, coords)
    
    print("\n" + "=" * 60)
    print("✅ 完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print(f"  1. models/digit_extraction_{image_path.stem}.png")
    print(f"  2. models/combiner_extraction_{image_path.stem}.png")
    print("\n请查看这些图像，确认:")
    print("  - 坐标框是否准确覆盖数字")
    print("  - 预处理后的图像是否清晰可辨")
    print("  - COMBINER 区域是否有问题")
    
    return 0


if __name__ == "__main__":
    exit(main())
