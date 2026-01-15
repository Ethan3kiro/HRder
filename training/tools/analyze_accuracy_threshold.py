#!/usr/bin/env python3
"""
分析准确率阈值对结果的影响
检查如果将预测值四舍五入到整数，准确率会如何变化
"""

import json
import torch
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import sys

# 导入训练脚本中的模型定义
sys.path.insert(0, str(Path(__file__).parent))
from train_dl_model import DigitCNN


def analyze_threshold_impact():
    """分析不同阈值对准确率的影响"""
    
    # 加载模型
    model_path = Path("models/digit_ocr_model.pth")
    if not model_path.exists():
        print("❌ 模型文件不存在！")
        return
    
    # 检查设备
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    
    # 加载模型
    model = DigitCNN()
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    print("=" * 60)
    print("准确率阈值分析")
    print("=" * 60)
    
    # 获取坐标
    from test_dl_model import DLOCRTester
    tester = DLOCRTester(model_path)
    coords = tester.get_cell_coordinates()
    
    # 加载标注数据
    labels_dir = Path("training_data")
    label_files = list(labels_dir.glob("*_labels.json"))
    
    if not label_files:
        print("❌ 没有找到标注文件")
        return
    
    print(f"\n✓ 找到 {len(label_files)} 个标注文件")
    
    # 收集所有预测结果
    predictions = []
    
    print("\n🧪 收集预测数据...")
    for label_file in tqdm(label_files, desc="处理图像"):
        with open(label_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        image_path = Path(data['image_path'])
        if not image_path.exists():
            continue
        
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        
        for cell_id, true_value in data['labels'].items():
            if cell_id not in coords:
                continue
            
            x, y, w, h = coords[cell_id]
            image_tensor = tester.preprocess_image(image, x, y, w, h)
            
            if image_tensor is None:
                continue
            
            pred_value = tester.predict(image_tensor)
            predictions.append({
                'cell_id': cell_id,
                'true_value': true_value,
                'pred_value': pred_value,
                'pred_rounded': round(pred_value),
                'error': abs(pred_value - true_value),
                'error_rounded': abs(round(pred_value) - true_value)
            })
    
    if not predictions:
        print("❌ 没有收集到预测数据")
        return
    
    print(f"\n✓ 收集了 {len(predictions)} 个预测")
    
    # 分析不同阈值
    print("\n" + "=" * 60)
    print("不同阈值下的准确率")
    print("=" * 60)
    
    thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    print("\n使用原始预测值（浮点数）：")
    for threshold in thresholds:
        correct = sum(1 for p in predictions if p['error'] < threshold)
        accuracy = (correct / len(predictions)) * 100
        print(f"  阈值 < {threshold}: {correct}/{len(predictions)} = {accuracy:.1f}%")
    
    print("\n使用四舍五入后的预测值（整数）：")
    for threshold in thresholds:
        correct = sum(1 for p in predictions if p['error_rounded'] < threshold)
        accuracy = (correct / len(predictions)) * 100
        print(f"  阈值 < {threshold}: {correct}/{len(predictions)} = {accuracy:.1f}%")
    
    # 分析 COMBINER vs Z-Plane
    print("\n" + "=" * 60)
    print("按区域分析")
    print("=" * 60)
    
    combiner_preds = [p for p in predictions if not p['cell_id'].startswith('Z-Plane')]
    zplane_preds = [p for p in predictions if p['cell_id'].startswith('Z-Plane')]
    
    print(f"\nCOMBINER 区域 ({len(combiner_preds)} 个样本):")
    print("  原始预测值:")
    for threshold in [0.5, 1.0, 2.0]:
        correct = sum(1 for p in combiner_preds if p['error'] < threshold)
        accuracy = (correct / len(combiner_preds)) * 100 if combiner_preds else 0
        print(f"    阈值 < {threshold}: {accuracy:.1f}%")
    
    print("  四舍五入后:")
    for threshold in [0.5, 1.0, 2.0]:
        correct = sum(1 for p in combiner_preds if p['error_rounded'] < threshold)
        accuracy = (correct / len(combiner_preds)) * 100 if combiner_preds else 0
        print(f"    阈值 < {threshold}: {accuracy:.1f}%")
    
    print(f"\nZ-Plane 区域 ({len(zplane_preds)} 个样本):")
    print("  原始预测值:")
    for threshold in [0.5, 1.0, 2.0]:
        correct = sum(1 for p in zplane_preds if p['error'] < threshold)
        accuracy = (correct / len(zplane_preds)) * 100 if zplane_preds else 0
        print(f"    阈值 < {threshold}: {accuracy:.1f}%")
    
    print("  四舍五入后:")
    for threshold in [0.5, 1.0, 2.0]:
        correct = sum(1 for p in zplane_preds if p['error_rounded'] < threshold)
        accuracy = (correct / len(zplane_preds)) * 100 if zplane_preds else 0
        print(f"    阈值 < {threshold}: {accuracy:.1f}%")
    
    # 显示一些示例
    print("\n" + "=" * 60)
    print("预测示例（前10个）")
    print("=" * 60)
    
    for i, p in enumerate(predictions[:10]):
        print(f"\n{i+1}. {p['cell_id']}")
        print(f"   真实值: {p['true_value']}")
        print(f"   预测值: {p['pred_value']:.2f} (四舍五入: {p['pred_rounded']})")
        print(f"   误差: {p['error']:.2f} (四舍五入后: {p['error_rounded']})")
    
    # 建议
    print("\n" + "=" * 60)
    print("建议")
    print("=" * 60)
    
    # 计算使用四舍五入 + 阈值1.0的准确率
    correct_rounded_1 = sum(1 for p in predictions if p['error_rounded'] < 1.0)
    accuracy_rounded_1 = (correct_rounded_1 / len(predictions)) * 100
    
    correct_original_2 = sum(1 for p in predictions if p['error'] < 2.0)
    accuracy_original_2 = (correct_original_2 / len(predictions)) * 100
    
    print(f"\n当前方法（原始值 + 阈值2.0）: {accuracy_original_2:.1f}%")
    print(f"建议方法（四舍五入 + 阈值1.0）: {accuracy_rounded_1:.1f}%")
    
    if accuracy_rounded_1 > accuracy_original_2:
        improvement = accuracy_rounded_1 - accuracy_original_2
        print(f"\n✅ 使用四舍五入可以提升 {improvement:.1f}% 的准确率！")
        print("\n建议修改 test_dl_model.py:")
        print("  1. 将预测值四舍五入: pred_value = round(pred_value)")
        print("  2. 使用更严格的阈值: if error < 1.0")
    else:
        print("\n⚠️  四舍五入不会显著提升准确率")
        print("   问题可能在于模型本身或坐标定义")


if __name__ == "__main__":
    analyze_threshold_impact()
