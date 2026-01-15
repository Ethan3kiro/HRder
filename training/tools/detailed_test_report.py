#!/usr/bin/env python3
"""
生成详细的测试报告
显示每个单元格的预测结果和误差
"""

import json
import torch
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict
import sys

# 导入训练脚本中的模型定义
sys.path.insert(0, str(Path(__file__).parent))
from train_dl_model import DigitCNN


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


def preprocess_image(image, x, y, w, h, padding=5):
    """预处理图像区域"""
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
    
    # 调整大小到 28x28
    digit_img = cv2.resize(digit_img, (28, 28), interpolation=cv2.INTER_AREA)
    
    # 二值化
    _, digit_img = cv2.threshold(digit_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 归一化
    digit_img = digit_img.astype(np.float32) / 255.0
    
    # 转换为 tensor
    digit_tensor = torch.from_numpy(digit_img).unsqueeze(0).unsqueeze(0)
    
    return digit_tensor


def main():
    """主函数"""
    print("=" * 80)
    print("详细测试报告")
    print("=" * 80)
    
    # 加载模型
    model_path = Path("models/digit_ocr_model.pth")
    if not model_path.exists():
        print("\n❌ 模型文件不存在！")
        return 1
    
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
    
    print(f"\n✓ 模型已加载 (设备: {device})")
    
    # 加载坐标
    coords = load_coordinates()
    print(f"✓ 加载了 {len(coords)} 个坐标定义")
    
    # 查找标注文件
    labels_dir = Path("training_data")
    label_files = sorted(labels_dir.glob("*_labels.json"))
    
    if not label_files:
        print("\n❌ 未找到标注文件")
        return 1
    
    print(f"✓ 找到 {len(label_files)} 个标注文件\n")
    
    # 按单元格统计
    cell_stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'errors': []})
    
    # 测试每个图像
    for label_file in label_files:
        with open(label_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        image_path = Path(data['image_path'])
        if not image_path.exists():
            continue
        
        # 加载图像
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        
        # 测试每个单元格
        for cell_id, true_value in data['labels'].items():
            if cell_id not in coords:
                continue
            
            coord = coords[cell_id]
            x, y, w, h = coord['x'], coord['y'], coord['width'], coord['height']
            
            # 预处理
            image_tensor = preprocess_image(image, x, y, w, h)
            if image_tensor is None:
                continue
            
            # 预测
            with torch.no_grad():
                image_tensor = image_tensor.to(device)
                output = model(image_tensor)
                pred_value = output.item()
            
            # 统计
            error = abs(pred_value - true_value)
            cell_stats[cell_id]['total'] += 1
            cell_stats[cell_id]['errors'].append(error)
            
            if error < 2.0:
                cell_stats[cell_id]['correct'] += 1
    
    # 生成报告
    print("=" * 80)
    print("按单元格统计")
    print("=" * 80)
    print()
    
    # 按区域分组
    combiner_cells = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    # COMBINER 区域
    print("COMBINER 区域:")
    print("-" * 80)
    print(f"{'单元格':<15} {'总数':>8} {'正确':>8} {'准确率':>10} {'平均误差':>12}")
    print("-" * 80)
    
    combiner_correct = 0
    combiner_total = 0
    
    for cell_id in combiner_cells:
        if cell_id in cell_stats:
            stats = cell_stats[cell_id]
            total = stats['total']
            correct = stats['correct']
            accuracy = (correct / total * 100) if total > 0 else 0
            avg_error = sum(stats['errors']) / len(stats['errors']) if stats['errors'] else 0
            
            combiner_correct += correct
            combiner_total += total
            
            status = "✓" if accuracy >= 80 else "⚠️" if accuracy >= 50 else "❌"
            print(f"{cell_id:<15} {total:>8} {correct:>8} {accuracy:>9.1f}% {avg_error:>11.2f} {status}")
    
    combiner_accuracy = (combiner_correct / combiner_total * 100) if combiner_total > 0 else 0
    print("-" * 80)
    print(f"{'总计':<15} {combiner_total:>8} {combiner_correct:>8} {combiner_accuracy:>9.1f}%")
    print()
    
    # Z-Plane 区域 - 按模块统计
    modules = ['A', 'B', 'C', 'D']
    columns = ['Current', 'ISO Temp']
    
    print("Z-Plane 区域 (按模块):")
    print("-" * 80)
    print(f"{'模块-列':<20} {'总数':>8} {'正确':>8} {'准确率':>10} {'平均误差':>12}")
    print("-" * 80)
    
    zplane_correct = 0
    zplane_total = 0
    
    for module in modules:
        for column in columns:
            module_correct = 0
            module_total = 0
            module_errors = []
            
            for row in range(1, 9):
                cell_id = f'Z-Plane {module}-{column}-{row}'
                if cell_id in cell_stats:
                    stats = cell_stats[cell_id]
                    module_correct += stats['correct']
                    module_total += stats['total']
                    module_errors.extend(stats['errors'])
            
            if module_total > 0:
                accuracy = (module_correct / module_total * 100)
                avg_error = sum(module_errors) / len(module_errors) if module_errors else 0
                
                zplane_correct += module_correct
                zplane_total += module_total
                
                status = "✓" if accuracy >= 80 else "⚠️" if accuracy >= 50 else "❌"
                print(f"{module}-{column:<18} {module_total:>8} {module_correct:>8} {accuracy:>9.1f}% {avg_error:>11.2f} {status}")
    
    zplane_accuracy = (zplane_correct / zplane_total * 100) if zplane_total > 0 else 0
    print("-" * 80)
    print(f"{'总计':<20} {zplane_total:>8} {zplane_correct:>8} {zplane_accuracy:>9.1f}%")
    print()
    
    # 总体统计
    total_correct = combiner_correct + zplane_correct
    total_total = combiner_total + zplane_total
    total_accuracy = (total_correct / total_total * 100) if total_total > 0 else 0
    
    print("=" * 80)
    print("总体统计")
    print("=" * 80)
    print(f"总预测数: {total_total}")
    print(f"正确预测: {total_correct}")
    print(f"总准确率: {total_accuracy:.1f}%")
    print()
    
    # 找出表现最差的单元格
    print("=" * 80)
    print("表现最差的 10 个单元格")
    print("=" * 80)
    print(f"{'单元格':<20} {'准确率':>10} {'平均误差':>12}")
    print("-" * 80)
    
    worst_cells = []
    for cell_id, stats in cell_stats.items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total'] * 100)
            avg_error = sum(stats['errors']) / len(stats['errors'])
            worst_cells.append((cell_id, accuracy, avg_error))
    
    worst_cells.sort(key=lambda x: x[1])  # 按准确率排序
    
    for cell_id, accuracy, avg_error in worst_cells[:10]:
        print(f"{cell_id:<20} {accuracy:>9.1f}% {avg_error:>11.2f}")
    
    print()
    print("=" * 80)
    
    # 保存详细报告
    report_path = Path("models/detailed_test_report.json")
    report_data = {
        'combiner': {
            'accuracy': combiner_accuracy,
            'correct': combiner_correct,
            'total': combiner_total
        },
        'zplane': {
            'accuracy': zplane_accuracy,
            'correct': zplane_correct,
            'total': zplane_total
        },
        'overall': {
            'accuracy': total_accuracy,
            'correct': total_correct,
            'total': total_total
        },
        'cell_stats': {
            cell_id: {
                'accuracy': (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0,
                'correct': stats['correct'],
                'total': stats['total'],
                'avg_error': sum(stats['errors']) / len(stats['errors']) if stats['errors'] else 0
            }
            for cell_id, stats in cell_stats.items()
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"📝 详细报告已保存: {report_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
