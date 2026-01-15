#!/usr/bin/env python3
"""
深度学习模型测试脚本
测试训练好的模型在真实图像上的表现
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


class DLOCRTester:
    """深度学习 OCR 测试器"""
    
    def __init__(self, model_path="models/digit_ocr_model.pth"):
        self.model_path = Path(model_path)
        
        # 检查设备
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        
        # 加载模型
        self.model = self.load_model()
    
    def load_model(self):
        """加载训练好的模型"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        model = DigitCNN()
        checkpoint = torch.load(self.model_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()
        
        print(f"✓ 模型已加载: {self.model_path}")
        print(f"  设备: {self.device}")
        print(f"  验证损失: {checkpoint.get('val_loss', 'N/A')}")
        print(f"  验证 MAE: {checkpoint.get('val_mae', 'N/A')}")
        
        return model
    
    def preprocess_image(self, image, x, y, w, h, padding=5):
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
    
    def predict(self, image_tensor):
        """预测数值"""
        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            output = self.model(image_tensor)
            value = output.item()
        
        return value
    
    def get_cell_coordinates(self):
        """获取当前定义的坐标"""
        coords = {}
        
        # COMBINER 区域 - 横向排列
        combiner_base_x = 214
        combiner_base_y = 223
        combiner_spacing = 48
        combiner_width = 34
        combiner_height = 23
        
        for i, item in enumerate(['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']):
            x = combiner_base_x + i * combiner_spacing
            # ABCD 项单独向右移动 2 像素
            if item == 'ABCD':
                x += 2
            coords[item] = (x, combiner_base_y, combiner_width, combiner_height)
        
        # Z-Plane 区域 - 每个模块的每一列都有独立坐标
        # 模块 A - Current
        A_current_x = 42
        A_current_y = 292
        A_current_width = 38
        A_current_height = 23
        A_current_middle_gap = 8  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = A_current_y + (row - 1) * A_current_height
            else:
                row_y = A_current_y + (row - 1) * A_current_height + A_current_middle_gap
            key = f'Z-Plane A-Current-{row}'
            coords[key] = (A_current_x, row_y, A_current_width, A_current_height)
        
        # 模块 A - ISO Temp
        A_iso_temp_x = 175
        A_iso_temp_y = 292
        A_iso_temp_width = 37
        A_iso_temp_height = 23
        A_iso_temp_middle_gap = 8  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = A_iso_temp_y + (row - 1) * A_iso_temp_height
            else:
                row_y = A_iso_temp_y + (row - 1) * A_iso_temp_height + A_iso_temp_middle_gap
            key = f'Z-Plane A-ISO Temp-{row}'
            coords[key] = (A_iso_temp_x, row_y, A_iso_temp_width, A_iso_temp_height)
        
        # 模块 B - Current
        B_current_x = 234
        B_current_y = 290
        B_current_width = 38
        B_current_height = 24
        B_current_middle_gap = 4  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = B_current_y + (row - 1) * B_current_height
            else:
                row_y = B_current_y + (row - 1) * B_current_height + B_current_middle_gap
            key = f'Z-Plane B-Current-{row}'
            coords[key] = (B_current_x, row_y, B_current_width, B_current_height)
        
        # 模块 B - ISO Temp
        B_iso_temp_x = 366
        B_iso_temp_y = 290
        B_iso_temp_width = 38
        B_iso_temp_height = 24
        B_iso_temp_middle_gap = 4  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = B_iso_temp_y + (row - 1) * B_iso_temp_height
            else:
                row_y = B_iso_temp_y + (row - 1) * B_iso_temp_height + B_iso_temp_middle_gap
            key = f'Z-Plane B-ISO Temp-{row}'
            coords[key] = (B_iso_temp_x, row_y, B_iso_temp_width, B_iso_temp_height)
        
        # 模块 C - Current
        C_current_x = 426
        C_current_y = 290
        C_current_width = 39
        C_current_height = 24
        C_current_middle_gap = 4  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = C_current_y + (row - 1) * C_current_height
            else:
                row_y = C_current_y + (row - 1) * C_current_height + C_current_middle_gap
            key = f'Z-Plane C-Current-{row}'
            coords[key] = (C_current_x, row_y, C_current_width, C_current_height)
        
        # 模块 C - ISO Temp
        C_iso_temp_x = 558
        C_iso_temp_y = 290
        C_iso_temp_width = 39
        C_iso_temp_height = 24
        C_iso_temp_middle_gap = 3  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = C_iso_temp_y + (row - 1) * C_iso_temp_height
            else:
                row_y = C_iso_temp_y + (row - 1) * C_iso_temp_height + C_iso_temp_middle_gap
            key = f'Z-Plane C-ISO Temp-{row}'
            coords[key] = (C_iso_temp_x, row_y, C_iso_temp_width, C_iso_temp_height)
        
        # 模块 D - Current
        D_current_x = 618
        D_current_y = 290
        D_current_width = 38
        D_current_height = 24
        D_current_middle_gap = 4  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = D_current_y + (row - 1) * D_current_height
            else:
                row_y = D_current_y + (row - 1) * D_current_height + D_current_middle_gap
            key = f'Z-Plane D-Current-{row}'
            coords[key] = (D_current_x, row_y, D_current_width, D_current_height)
        
        # 模块 D - ISO Temp
        D_iso_temp_x = 750
        D_iso_temp_y = 290
        D_iso_temp_width = 39
        D_iso_temp_height = 24
        D_iso_temp_middle_gap = 3  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = D_iso_temp_y + (row - 1) * D_iso_temp_height
            else:
                row_y = D_iso_temp_y + (row - 1) * D_iso_temp_height + D_iso_temp_middle_gap
            key = f'Z-Plane D-ISO Temp-{row}'
            coords[key] = (D_iso_temp_x, row_y, D_iso_temp_width, D_iso_temp_height)
        
        return coords
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def test_on_labeled_data(self, labels_dir="training_data"):
        """在标注数据上测试模型"""
        print("\n" + "=" * 60)
        print("测试深度学习 OCR 模型")
        print("=" * 60)
        
        labels_dir = Path(labels_dir)
        label_files = list(labels_dir.glob("*_labels.json"))
        
        if not label_files:
            print("\n❌ 没有找到标注文件")
            return
        
        print(f"\n✓ 找到 {len(label_files)} 个标注文件")
        
        # 获取坐标
        coords = self.get_cell_coordinates()
        
        # 统计结果
        total_predictions = 0
        correct_predictions = 0
        total_error = 0
        errors = []
        
        print("\n🧪 开始测试...")
        for label_file in tqdm(label_files, desc="测试图像"):
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
                
                x, y, w, h = coords[cell_id]
                
                # 预处理
                image_tensor = self.preprocess_image(image, x, y, w, h)
                if image_tensor is None:
                    continue
                
                # 预测
                pred_value = self.predict(image_tensor)
                
                # 统计
                total_predictions += 1
                error = abs(pred_value - true_value)
                total_error += error
                errors.append(error)
                
                # 判断是否正确（误差 < 2.0）
                if error < 2.0:
                    correct_predictions += 1
        
        # 计算指标
        if total_predictions > 0:
            accuracy = (correct_predictions / total_predictions) * 100
            mae = total_error / total_predictions
            
            # 计算百分位数
            errors.sort()
            p50 = errors[len(errors) // 2] if errors else 0
            p90 = errors[int(len(errors) * 0.9)] if errors else 0
            p95 = errors[int(len(errors) * 0.95)] if errors else 0
            
            print("\n" + "=" * 60)
            print("测试结果")
            print("=" * 60)
            print(f"\n总预测数: {total_predictions}")
            print(f"正确预测: {correct_predictions} (误差 < 2.0)")
            print(f"准确率: {accuracy:.1f}%")
            print(f"\n平均绝对误差 (MAE): {mae:.2f}")
            print(f"中位数误差 (P50): {p50:.2f}")
            print(f"90% 误差 (P90): {p90:.2f}")
            print(f"95% 误差 (P95): {p95:.2f}")
            
            # 评估结果
            print("\n" + "=" * 60)
            if accuracy >= 90:
                print("✅ 模型表现优秀！可以集成到主程序")
            elif accuracy >= 80:
                print("⚠️  模型表现良好，但可能需要更多训练")
            else:
                print("❌ 模型表现不佳，建议:")
                print("   1. 检查坐标定义是否正确")
                print("   2. 增加更多标注数据")
                print("   3. 调整模型架构或训练参数")
            
            # 保存测试结果
            results = {
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'accuracy': accuracy,
                'mae': mae,
                'p50': p50,
                'p90': p90,
                'p95': p95
            }
            
            results_path = Path("models/test_results.json")
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📝 测试结果已保存: {results_path}")
        else:
            print("\n❌ 没有成功预测任何数据")
            print("   可能需要调整坐标定义")


def main():
    """主函数"""
    # 检查模型是否存在
    model_path = Path("models/digit_ocr_model.pth")
    if not model_path.exists():
        print("❌ 模型文件不存在！")
        print("   请先运行: python3 tools/train_dl_model.py")
        return 1
    
    # 创建测试器
    tester = DLOCRTester(model_path)
    
    # 测试模型
    tester.test_on_labeled_data()
    
    return 0


if __name__ == "__main__":
    exit(main())
