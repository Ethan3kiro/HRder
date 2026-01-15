#!/usr/bin/env python3
"""
测试自定义 OCR 识别器
"""

import json
import pickle
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ocr_extractor_v8 import OCRExtractorV8


class CustomOCRTester:
    """自定义 OCR 测试器"""
    
    def __init__(self, model_dir="models", labels_dir="training_data"):
        self.model_dir = Path(model_dir)
        self.labels_dir = Path(labels_dir)
        
        # 加载验证规则
        rules_file = self.model_dir / "validation_rules.pkl"
        if not rules_file.exists():
            print(f"❌ 验证规则文件不存在: {rules_file}")
            print("   请先运行: python3 tools/train_custom_ocr.py")
            sys.exit(1)
        
        with open(rules_file, 'rb') as f:
            self.validation_rules = pickle.load(f)
        
        print(f"✓ 加载了 {len(self.validation_rules)} 条验证规则")
        
        # 初始化 OCR 提取器
        self.extractor = OCRExtractorV8()
    
    def validate_value(self, cell_id, value):
        """验证识别值是否在合理范围内"""
        if cell_id not in self.validation_rules:
            return True, "无规则"
        
        rules = self.validation_rules[cell_id]
        
        if rules['min'] <= value <= rules['max']:
            return True, "正常"
        else:
            return False, f"超出范围 [{rules['min']:.1f}, {rules['max']:.1f}]"
    
    def test_on_labeled_data(self):
        """在标注数据上测试"""
        print("\n" + "=" * 60)
        print("测试自定义 OCR 识别器")
        print("=" * 60)
        
        label_files = list(self.labels_dir.glob("*_labels.json"))
        if not label_files:
            print("❌ 没有找到标注文件")
            return
        
        print(f"\n测试 {len(label_files)} 张图像...")
        
        total_cells = 0
        correct_cells = 0
        validated_cells = 0
        
        for label_file in label_files:
            with open(label_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            image_path = Path(data['image_path'])
            if not image_path.exists():
                print(f"⚠️  图像不存在: {image_path}")
                continue
            
            print(f"\n测试: {image_path.name}")
            
            # 使用 OCR 提取数据
            try:
                extracted_df = self.extractor.extract_from_image(Path(image_path))
                
                # 转换为字典格式以便查找
                extracted_dict = {}
                
                for _, row in extracted_df.iterrows():
                    item_name = row.get('item_name', '')
                    value = row.get('value')
                    
                    if value is not None:
                        extracted_dict[item_name] = value
                
            except Exception as e:
                print(f"  ❌ OCR 提取失败: {e}")
                continue
            
            # 比较结果
            image_correct = 0
            image_total = 0
            image_validated = 0
            
            for cell_id, true_value in data['labels'].items():
                image_total += 1
                
                # 直接从字典中查找
                extracted_value = extracted_dict.get(cell_id)
                
                if extracted_value is not None:
                    # 检查是否匹配
                    if abs(extracted_value - true_value) < 0.1:
                        image_correct += 1
                    
                    # 验证是否在合理范围
                    is_valid, reason = self.validate_value(cell_id, extracted_value)
                    if is_valid:
                        image_validated += 1
            
            accuracy = (image_correct / image_total * 100) if image_total > 0 else 0
            validation_rate = (image_validated / image_total * 100) if image_total > 0 else 0
            
            print(f"  准确率: {image_correct}/{image_total} ({accuracy:.1f}%)")
            print(f"  验证通过率: {image_validated}/{image_total} ({validation_rate:.1f}%)")
            
            total_cells += image_total
            correct_cells += image_correct
            validated_cells += image_validated
        
        # 总体统计
        print("\n" + "=" * 60)
        print("总体结果")
        print("=" * 60)
        
        overall_accuracy = (correct_cells / total_cells * 100) if total_cells > 0 else 0
        overall_validation = (validated_cells / total_cells * 100) if total_cells > 0 else 0
        
        print(f"\n总准确率: {correct_cells}/{total_cells} ({overall_accuracy:.1f}%)")
        print(f"总验证通过率: {validated_cells}/{total_cells} ({overall_validation:.1f}%)")
        
        if overall_accuracy >= 85:
            print("\n✅ 识别效果很好！可以集成到主程序")
        elif overall_accuracy >= 70:
            print("\n⚠️  识别效果一般，建议继续标注更多数据")
        else:
            print("\n❌ 识别效果不佳，需要更多标注数据或调整方法")


def main():
    """主函数"""
    tester = CustomOCRTester()
    tester.test_on_labeled_data()


if __name__ == "__main__":
    main()
