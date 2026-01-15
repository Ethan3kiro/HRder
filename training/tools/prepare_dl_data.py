#!/usr/bin/env python3
"""
深度学习数据准备脚本
从标注数据中提取数字图像并进行数据增强
"""

import json
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import albumentations as A
from collections import defaultdict
import shutil


class DLDataPreparator:
    """深度学习数据准备器"""
    
    def __init__(self, labels_dir="training_data", output_dir="training_data/dl_dataset"):
        self.labels_dir = Path(labels_dir)
        self.output_dir = Path(output_dir)
        
        # 创建输出目录
        self.train_dir = self.output_dir / "train"
        self.val_dir = self.output_dir / "val"
        
        # 清空并重新创建目录
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        self.train_dir.mkdir(parents=True, exist_ok=True)
        self.val_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据增强配置
        self.augmentation = A.Compose([
            A.Rotate(limit=15, p=0.7),
            A.GaussNoise(p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
            A.Blur(blur_limit=3, p=0.3),
            A.ElasticTransform(alpha=1, sigma=50, p=0.3),
        ])
        
        # 统计信息
        self.stats = defaultdict(int)
    
    def extract_digit_from_image(self, image, x, y, w, h, padding=5):
        """从图像中提取数字区域"""
        # 添加 padding
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(image.shape[1], x + w + padding)
        y2 = min(image.shape[0], y + h + padding)
        
        # 裁剪
        digit_img = image[y1:y2, x1:x2]
        
        if digit_img.size == 0:
            return None
        
        # 转换为灰度图
        if len(digit_img.shape) == 3:
            digit_img = cv2.cvtColor(digit_img, cv2.COLOR_BGR2GRAY)
        
        # 调整大小到固定尺寸 (28x28)
        digit_img = cv2.resize(digit_img, (28, 28), interpolation=cv2.INTER_AREA)
        
        # 二值化
        _, digit_img = cv2.threshold(digit_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return digit_img
    
    def get_cell_coordinates(self):
        """定义所有单元格的坐标（独立调整后的坐标）"""
        coords = {}

        # 格式: {cell_id: (x, y, width, height)}

        # COMBINER 区域 - 独立调整
        coords['AZ'] = (214, 223, 34, 23)
        coords['BZ'] = (262, 223, 34, 23)
        coords['CZ'] = (310, 223, 34, 23)
        coords['DZ'] = (358, 223, 34, 23)
        coords['AB'] = (406, 223, 34, 23)
        coords['CD'] = (454, 223, 34, 23)
        coords['ABCD'] = (504, 223, 34, 23)

        # Z-Plane 区域 - 独立调整
        # A-Current
        coords['Z-Plane A-Current-1'] = (42, 292, 38, 23)
        coords['Z-Plane A-Current-2'] = (42, 315, 38, 23)
        coords['Z-Plane A-Current-3'] = (42, 338, 38, 23)
        coords['Z-Plane A-Current-4'] = (42, 361, 38, 23)
        coords['Z-Plane A-Current-5'] = (42, 392, 38, 23)
        coords['Z-Plane A-Current-6'] = (42, 415, 38, 23)
        coords['Z-Plane A-Current-7'] = (42, 438, 38, 23)
        coords['Z-Plane A-Current-8'] = (42, 461, 38, 23)

        # A-ISO Temp
        coords['Z-Plane A-ISO Temp-1'] = (175, 292, 37, 23)
        coords['Z-Plane A-ISO Temp-2'] = (175, 315, 37, 23)
        coords['Z-Plane A-ISO Temp-3'] = (175, 338, 37, 23)
        coords['Z-Plane A-ISO Temp-4'] = (175, 361, 37, 23)
        coords['Z-Plane A-ISO Temp-5'] = (175, 392, 37, 23)
        coords['Z-Plane A-ISO Temp-6'] = (175, 415, 37, 23)
        coords['Z-Plane A-ISO Temp-7'] = (175, 438, 37, 23)
        coords['Z-Plane A-ISO Temp-8'] = (175, 461, 37, 23)

        # B-Current
        coords['Z-Plane B-Current-1'] = (234, 290, 38, 24)
        coords['Z-Plane B-Current-2'] = (234, 314, 38, 24)
        coords['Z-Plane B-Current-3'] = (234, 338, 38, 24)
        coords['Z-Plane B-Current-4'] = (234, 362, 38, 24)
        coords['Z-Plane B-Current-5'] = (234, 390, 38, 24)
        coords['Z-Plane B-Current-6'] = (234, 414, 38, 24)
        coords['Z-Plane B-Current-7'] = (234, 438, 38, 24)
        coords['Z-Plane B-Current-8'] = (234, 462, 38, 24)

        # B-ISO Temp
        coords['Z-Plane B-ISO Temp-1'] = (366, 290, 38, 24)
        coords['Z-Plane B-ISO Temp-2'] = (366, 314, 38, 24)
        coords['Z-Plane B-ISO Temp-3'] = (366, 338, 38, 24)
        coords['Z-Plane B-ISO Temp-4'] = (366, 362, 38, 24)
        coords['Z-Plane B-ISO Temp-5'] = (366, 390, 38, 24)
        coords['Z-Plane B-ISO Temp-6'] = (366, 414, 38, 24)
        coords['Z-Plane B-ISO Temp-7'] = (366, 438, 38, 24)
        coords['Z-Plane B-ISO Temp-8'] = (366, 462, 38, 24)

        # C-Current
        coords['Z-Plane C-Current-1'] = (426, 290, 39, 24)
        coords['Z-Plane C-Current-2'] = (426, 314, 39, 24)
        coords['Z-Plane C-Current-3'] = (426, 338, 39, 24)
        coords['Z-Plane C-Current-4'] = (426, 362, 39, 24)
        coords['Z-Plane C-Current-5'] = (426, 390, 39, 24)
        coords['Z-Plane C-Current-6'] = (426, 414, 39, 24)
        coords['Z-Plane C-Current-7'] = (426, 438, 39, 24)
        coords['Z-Plane C-Current-8'] = (426, 462, 39, 24)

        # C-ISO Temp
        coords['Z-Plane C-ISO Temp-1'] = (558, 290, 39, 24)
        coords['Z-Plane C-ISO Temp-2'] = (558, 314, 39, 24)
        coords['Z-Plane C-ISO Temp-3'] = (558, 338, 39, 24)
        coords['Z-Plane C-ISO Temp-4'] = (558, 362, 39, 24)
        coords['Z-Plane C-ISO Temp-5'] = (558, 389, 39, 24)
        coords['Z-Plane C-ISO Temp-6'] = (558, 413, 39, 24)
        coords['Z-Plane C-ISO Temp-7'] = (558, 437, 39, 24)
        coords['Z-Plane C-ISO Temp-8'] = (558, 461, 39, 24)

        # D-Current
        coords['Z-Plane D-Current-1'] = (618, 290, 38, 24)
        coords['Z-Plane D-Current-2'] = (618, 314, 38, 24)
        coords['Z-Plane D-Current-3'] = (618, 338, 38, 24)
        coords['Z-Plane D-Current-4'] = (618, 362, 38, 24)
        coords['Z-Plane D-Current-5'] = (618, 390, 38, 24)
        coords['Z-Plane D-Current-6'] = (618, 414, 38, 24)
        coords['Z-Plane D-Current-7'] = (618, 438, 38, 24)
        coords['Z-Plane D-Current-8'] = (618, 462, 38, 24)

        # D-ISO Temp
        coords['Z-Plane D-ISO Temp-1'] = (750, 290, 39, 24)
        coords['Z-Plane D-ISO Temp-2'] = (750, 314, 39, 24)
        coords['Z-Plane D-ISO Temp-3'] = (750, 338, 39, 24)
        coords['Z-Plane D-ISO Temp-4'] = (750, 362, 39, 24)
        coords['Z-Plane D-ISO Temp-5'] = (750, 389, 39, 24)
        coords['Z-Plane D-ISO Temp-6'] = (750, 413, 39, 24)
        coords['Z-Plane D-ISO Temp-7'] = (750, 437, 39, 24)
        coords['Z-Plane D-ISO Temp-8'] = (750, 461, 39, 24)

        return coords

    def value_to_label(self, value):
        """将数值转换为标签字符串"""
        # 将数值转换为字符串，保留小数点
        value_str = str(float(value))
        return value_str
    
    def prepare_dataset(self, augmentation_factor=10, val_split=0.2):
        """准备训练数据集"""
        print("=" * 60)
        print("深度学习数据准备")
        print("=" * 60)
        
        # 获取坐标
        coords = self.get_cell_coordinates()
        
        # 加载所有标注文件
        label_files = list(self.labels_dir.glob("*_labels.json"))
        if not label_files:
            print("❌ 没有找到标注文件")
            return False
        
        print(f"\n✓ 找到 {len(label_files)} 个标注文件")
        print(f"  数据增强因子: {augmentation_factor}x")
        print(f"  验证集比例: {val_split * 100}%")
        
        # 收集所有样本
        all_samples = []
        skipped_cells = set()
        
        print("\n📦 提取数字图像...")
        for label_file in tqdm(label_files, desc="处理图像"):
            with open(label_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            image_path = Path(data['image_path'])
            if not image_path.exists():
                continue
            
            # 加载图像
            image = cv2.imread(str(image_path))
            if image is None:
                continue
            
            # 提取每个数字（只处理已标注的单元格）
            for cell_id, value in data['labels'].items():
                if cell_id not in coords:
                    continue
                
                x, y, w, h = coords[cell_id]
                digit_img = self.extract_digit_from_image(image, x, y, w, h)
                
                if digit_img is not None:
                    label = self.value_to_label(value)
                    all_samples.append((digit_img, label, cell_id))
            
            # 记录未标注的单元格（用于统计）
            for cell_id in coords.keys():
                if cell_id not in data['labels']:
                    skipped_cells.add(cell_id)
        
        if not all_samples:
            print("❌ 没有提取到任何数字图像")
            print("   可能需要调整坐标定义")
            return False
        
        print(f"✓ 提取了 {len(all_samples)} 个原始样本")
        
        # 显示部分标注信息
        if skipped_cells:
            print(f"ℹ️  跳过了 {len(skipped_cells)} 个未标注的单元格")
            print(f"   这是正常的，支持部分标注（例如只标注 COMBINER + Temp 列）")
        
        # 分割训练集和验证集
        np.random.shuffle(all_samples)
        split_idx = int(len(all_samples) * (1 - val_split))
        train_samples = all_samples[:split_idx]
        val_samples = all_samples[split_idx:]
        
        print(f"\n📊 数据集划分:")
        print(f"  训练集: {len(train_samples)} 个样本")
        print(f"  验证集: {len(val_samples)} 个样本")
        
        # 保存训练集（带数据增强）
        print(f"\n🔄 生成训练数据（{augmentation_factor}x 增强）...")
        self.save_samples(train_samples, self.train_dir, augmentation_factor)
        
        # 保存验证集（不增强）
        print("\n💾 保存验证数据...")
        self.save_samples(val_samples, self.val_dir, augmentation_factor=1)
        
        # 保存元数据
        metadata = {
            'total_samples': len(all_samples),
            'train_samples': len(train_samples) * augmentation_factor,
            'val_samples': len(val_samples),
            'augmentation_factor': augmentation_factor,
            'image_size': [28, 28],
            'num_classes': len(set(label for _, label, _ in all_samples))
        }
        
        with open(self.output_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ 数据准备完成！")
        print("=" * 60)
        print(f"\n生成的数据:")
        print(f"  训练样本: {metadata['train_samples']}")
        print(f"  验证样本: {metadata['val_samples']}")
        print(f"  图像尺寸: 28x28")
        print(f"\n保存位置: {self.output_dir}")
        
        return True
    
    def save_samples(self, samples, output_dir, augmentation_factor):
        """保存样本（带可选的数据增强）"""
        for idx, (img, label, cell_id) in enumerate(tqdm(samples, desc="保存样本")):
            # 保存原始样本
            filename = f"{idx:05d}_{label.replace('.', '_')}_{cell_id.replace(' ', '_').replace('-', '_')}_orig.png"
            cv2.imwrite(str(output_dir / filename), img)
            
            # 数据增强
            for aug_idx in range(augmentation_factor - 1):
                augmented = self.augmentation(image=img)['image']
                filename = f"{idx:05d}_{label.replace('.', '_')}_{cell_id.replace(' ', '_').replace('-', '_')}_aug{aug_idx}.png"
                cv2.imwrite(str(output_dir / filename), augmented)


def main():
    """主函数"""
    preparator = DLDataPreparator()
    success = preparator.prepare_dataset(augmentation_factor=10, val_split=0.2)
    
    if not success:
        print("\n⚠️  数据准备失败")
        print("   可能需要调整 get_cell_coordinates() 中的坐标定义")
        print("   请查看图像并手动调整坐标")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
