#!/usr/bin/env python3
"""
数据准备脚本 - 从标注数据中提取数字图像
"""

import json
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import shutil
from tqdm import tqdm


class DataPreparator:
    """数据准备器"""
    
    def __init__(self, labels_dir="training_data", output_dir="training_data/digits"):
        self.labels_dir = Path(labels_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 单元格坐标（基于之前的分析）
        self.cell_coords = self._define_cell_coordinates()
    
    def _define_cell_coordinates(self):
        """定义所有单元格的坐标"""
        coords = {}
        
        # COMBINER 区域坐标（需要根据实际图像调整）
        combiner_items = {
            'AZ': (100, 150, 200, 180),      # (x, y, width, height)
            'BZ': (100, 190, 200, 180),
            'CZ': (100, 230, 200, 180),
            'DZ': (100, 270, 200, 180),
            'AB': (100, 310, 200, 180),
            'CD': (100, 350, 200, 180),
            'ABCD': (100, 390, 200, 180),
        }
        coords.update(combiner_items)
        
        # Z-Plane 区域坐标（需要根据实际图像调整）
        # 这里使用占位符坐标，实际需要根据图像调整
        base_x = 400
        base_y = 150
        cell_width = 80
        cell_height = 25
        
        for module_idx, module in enumerate(['A', 'B', 'C', 'D']):
            for row in range(1, 9):
                # Current
                key = f'Z-Plane {module}-Current-{row}'
                x = base_x + module_idx * 200
                y = base_y + (row - 1) * cell_height
                coords[key] = (x, y, cell_width, cell_height)
                
                # ISO Temp
                key = f'Z-Plane {module}-ISO Temp-{row}'
                x = base_x + module_idx * 200 + cell_width + 10
                y = base_y + (row - 1) * cell_height
                coords[key] = (x, y, cell_width, cell_height)
        
        return coords
    
    def extract_digit_images(self):
        """从标注数据中提取数字图像"""
        print("🔍 扫描标注文件...")
        label_files = list(self.labels_dir.glob("*_labels.json"))
        
        if not label_files:
            print("❌ 没有找到标注文件")
            return
        
        print(f"✓ 找到 {len(label_files)} 个标注文件")
        
        total_extracted = 0
        
        for label_file in tqdm(label_files, desc="提取数字图像"):
            with open(label_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            image_path = Path(data['image_path'])
            if not image_path.exists():
                print(f"⚠️  图像不存在: {image_path}")
                continue
            
            # 加载图像
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"⚠️  无法加载图像: {image_path}")
                continue
            
            # 提取每个标注的数字
            for cell_id, value in data['labels'].items():
                if cell_id not in self.cell_coords:
                    continue
                
                x, y, w, h = self.cell_coords[cell_id]
                
                # 裁剪数字区域
                digit_img = image[y:y+h, x:x+w]
                
                if digit_img.size == 0:
                    continue
                
                # 保存数字图像
                digit_str = str(value).replace('.', '_')
                output_file = self.output_dir / f"{image_path.stem}_{cell_id.replace(' ', '_')}_{digit_str}.png"
                cv2.imwrite(str(output_file), digit_img)
                total_extracted += 1
        
        print(f"\n✓ 提取完成！共提取 {total_extracted} 个数字图像")
        print(f"  保存位置: {self.output_dir}")
    
    def analyze_coordinates(self):
        """分析并显示第一张图像的坐标信息（用于调整坐标）"""
        label_files = list(self.labels_dir.glob("*_labels.json"))
        if not label_files:
            print("❌ 没有找到标注文件")
            return
        
        # 加载第一个标注文件
        with open(label_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        image_path = Path(data['image_path'])
        if not image_path.exists():
            print(f"❌ 图像不存在: {image_path}")
            return
        
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"❌ 无法加载图像: {image_path}")
            return
        
        print(f"图像尺寸: {image.shape[1]} x {image.shape[0]}")
        print(f"标注数量: {len(data['labels'])}")
        print("\n前 5 个标注:")
        for i, (cell_id, value) in enumerate(list(data['labels'].items())[:5]):
            print(f"  {cell_id}: {value}")
        
        # 保存带标记的图像用于验证坐标
        output_path = self.output_dir.parent / "coordinate_analysis.png"
        annotated = image.copy()
        
        for cell_id in list(data['labels'].keys())[:10]:  # 只标记前 10 个
            if cell_id in self.cell_coords:
                x, y, w, h = self.cell_coords[cell_id]
                cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(annotated, cell_id[:10], (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        cv2.imwrite(str(output_path), annotated)
        print(f"\n✓ 坐标分析图像已保存: {output_path}")
        print("  请检查绿色框是否正确标记了数字位置")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="准备训练数据")
    parser.add_argument('--analyze', action='store_true', 
                       help='分析坐标（用于调整坐标定义）')
    parser.add_argument('--extract', action='store_true',
                       help='提取数字图像')
    
    args = parser.parse_args()
    
    preparator = DataPreparator()
    
    if args.analyze:
        print("📊 分析坐标...")
        preparator.analyze_coordinates()
    elif args.extract:
        print("📦 提取数字图像...")
        preparator.extract_digit_images()
    else:
        print("请指定操作:")
        print("  --analyze  分析坐标")
        print("  --extract  提取数字图像")


if __name__ == "__main__":
    main()
