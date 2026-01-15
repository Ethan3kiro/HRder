#!/usr/bin/env python3
"""
可视化预测结果
显示每个单元格的预测值和真实值，帮助识别坐标问题
"""

import json
import cv2
import numpy as np
from pathlib import Path
import sys
import torch
import torch.nn as nn

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from prepare_dl_data import DLDataPreparator


# 定义模型（与 train_dl_model.py 中相同）
class DigitOCRModel(nn.Module):
    """数字识别 CNN 模型"""
    
    def __init__(self):
        super(DigitOCRModel, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        # 池化层
        self.pool = nn.MaxPool2d(2, 2)
        
        # Dropout
        self.dropout = nn.Dropout(0.5)
        
        # 全连接层
        # 输入: 28x28 -> conv1+pool -> 14x14 -> conv2+pool -> 7x7 -> conv3+pool -> 3x3
        self.fc1 = nn.Linear(128 * 3 * 3, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 1)  # 输出单个数值
        
        # 激活函数
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # 卷积层 1
        x = self.pool(self.relu(self.conv1(x)))
        
        # 卷积层 2
        x = self.pool(self.relu(self.conv2(x)))
        
        # 卷积层 3
        x = self.pool(self.relu(self.conv3(x)))
        
        # 展平
        x = x.view(-1, 128 * 3 * 3)
        
        # 全连接层
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x.squeeze()


def visualize_predictions(image_path, label_path, model_path):
    """可视化单张图像的预测结果"""
    
    # 加载模型
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    model = DigitOCRModel().to(device)
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # 加载图像和标注
    image = cv2.imread(str(image_path))
    with open(label_path, 'r', encoding='utf-8') as f:
        label_data = json.load(f)
    
    # 准备数据
    prep = DLDataPreparator()
    coords = prep.get_cell_coordinates()
    
    # 创建显示图像
    display = image.copy()
    
    results = []
    
    for cell_id, (x, y, w, h) in coords.items():
        if cell_id not in label_data['labels']:
            continue
        
        true_value = label_data['labels'][cell_id]
        
        # 提取图像区域
        cell_img = image[y:y+h, x:x+w]
        if cell_img.size == 0:
            continue
        
        # 预处理
        gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (28, 28))
        normalized = resized.astype(np.float32) / 255.0
        tensor = torch.from_numpy(normalized).unsqueeze(0).unsqueeze(0).to(device)
        
        # 预测
        with torch.no_grad():
            pred_value = model(tensor).item()
        
        # 计算误差
        error = abs(pred_value - true_value)
        
        # 根据误差选择颜色
        if error < 2.0:
            color = (0, 255, 0)  # 绿色 - 正确
        elif error < 5.0:
            color = (0, 165, 255)  # 橙色 - 接近
        else:
            color = (0, 0, 255)  # 红色 - 错误
        
        # 绘制边界框
        cv2.rectangle(display, (x, y), (x+w, y+h), color, 2)
        
        # 显示预测值和真实值
        text = f"P:{pred_value:.1f} T:{true_value:.1f}"
        cv2.putText(display, text, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        results.append({
            'cell_id': cell_id,
            'true': true_value,
            'pred': pred_value,
            'error': error,
            'coords': (x, y, w, h)
        })
    
    return display, results


def main():
    """主函数"""
    model_path = Path("models/digit_ocr_model.pth")
    labels_dir = Path("training_data")
    output_dir = Path("models/predictions")
    output_dir.mkdir(exist_ok=True)
    
    if not model_path.exists():
        print("❌ 模型文件不存在")
        return 1
    
    label_files = list(labels_dir.glob("*_labels.json"))
    if not label_files:
        print("❌ 没有找到标注文件")
        return 1
    
    print(f"\n找到 {len(label_files)} 个标注文件")
    print("\n生成预测可视化...")
    
    all_results = []
    
    for label_file in label_files:
        with open(label_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        image_path = Path(data['image_path'])
        if not image_path.exists():
            print(f"⚠️  图像不存在: {image_path}")
            continue
        
        print(f"\n处理: {image_path.name}")
        
        # 生成可视化
        display, results = visualize_predictions(image_path, label_file, model_path)
        
        # 保存可视化图像
        output_path = output_dir / f"pred_{image_path.stem}.png"
        cv2.imwrite(str(output_path), display)
        print(f"  ✓ 保存到: {output_path}")
        
        # 统计结果
        correct = sum(1 for r in results if r['error'] < 2.0)
        print(f"  准确率: {correct}/{len(results)} ({100*correct/len(results):.1f}%)")
        print(f"  平均误差: {np.mean([r['error'] for r in results]):.2f}")
        
        # 显示最大误差的单元格
        results.sort(key=lambda x: x['error'], reverse=True)
        print(f"\n  最大误差的 5 个单元格:")
        for r in results[:5]:
            print(f"    {r['cell_id']}: 真实={r['true']:.1f}, 预测={r['pred']:.1f}, 误差={r['error']:.1f}")
        
        all_results.extend(results)
    
    # 总体统计
    print("\n" + "=" * 60)
    print("总体统计")
    print("=" * 60)
    total = len(all_results)
    correct = sum(1 for r in all_results if r['error'] < 2.0)
    print(f"总预测数: {total}")
    print(f"正确预测: {correct} ({100*correct/total:.1f}%)")
    print(f"平均误差: {np.mean([r['error'] for r in all_results]):.2f}")
    
    # 按单元格类型统计
    print("\n按单元格类型统计:")
    cell_types = {}
    for r in all_results:
        cell_type = r['cell_id'].split('-')[0] if '-' in r['cell_id'] else r['cell_id']
        if cell_type not in cell_types:
            cell_types[cell_type] = []
        cell_types[cell_type].append(r['error'])
    
    for cell_type, errors in sorted(cell_types.items()):
        avg_error = np.mean(errors)
        correct_count = sum(1 for e in errors if e < 2.0)
        print(f"  {cell_type}: {correct_count}/{len(errors)} ({100*correct_count/len(errors):.1f}%), 平均误差={avg_error:.2f}")
    
    print(f"\n✅ 可视化图像已保存到: {output_dir}/")
    print("\n提示: 查看红色和橙色的框，这些是需要调整坐标的区域")
    
    return 0


if __name__ == "__main__":
    exit(main())
